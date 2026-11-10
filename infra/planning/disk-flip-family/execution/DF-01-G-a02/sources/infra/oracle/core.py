"""Evidence-scoped oracle support. Screening never claims global solvability.

No simulator, sandbox, container, or full trajectory generator is required.
Adapters supply necessary-condition checks and proposed high-level skill chains.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import time


STATUSES = ('full_success_evidence', 'screening_passed', 'undetermined', 'check_failed')
CATEGORIES = ('reachability', 'collision', 'support', 'skill_chain')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass
class Check:
    name: str
    category: str
    outcome: str
    reason: str
    scope: str = 'candidate'
    evidence: list = None
    constraints: dict = None

    def __post_init__(self):
        if self.category not in CATEGORIES or self.outcome not in ('pass', 'fail', 'unknown'):
            raise ValueError('Unknown check category or outcome')
        if self.scope not in ('instance', 'candidate') or not self.reason:
            raise ValueError('A check needs its scope and reason')
        self.evidence = self.evidence or []


class Budget:
    """Cooperative check budget; expensive adapters must also bound their own work."""
    def __init__(self, max_checks=1000, seconds=10., clock=time.monotonic):
        if not isinstance(max_checks, int) or max_checks < 0 or not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Finite nonnegative budgets required')
        self.max_checks, self.seconds, self.clock = max_checks, seconds, clock
        self.started, self.used, self.exhausted = clock(), 0, False

    def run(self, name, category, callback, scope='candidate'):
        if self.used >= self.max_checks or self.clock()-self.started >= self.seconds:
            self.exhausted = True
            return Check(name, category, 'unknown', 'budget_exhausted', scope)
        self.used += 1
        try:
            check = callback()
            if not isinstance(check, Check):
                raise TypeError('Checker must return Check')
        except Exception as error:
            return Check(name, category, 'unknown', 'checker_error: '+repr(error), scope)
        if self.clock()-self.started > self.seconds:
            self.exhausted = True
            return Check(name, category, 'unknown', 'budget_exhausted_after_check', scope)
        return check

    def record(self):
        return dict(max_checks=self.max_checks, max_seconds=self.seconds, used_checks=self.used,
                    elapsed_seconds=self.clock()-self.started, exhausted=self.exhausted)


def verified_artifacts(refs, root):
    """Fail closed on missing/changed artifacts; paths remain within evidence root."""
    if not isinstance(refs, (list, tuple)) or not refs or root is None:
        return False
    root = Path(root).resolve()
    for ref in refs:
        try:
            if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
                return False
            if Path(ref['path']).is_absolute():
                return False
            path = (root/ref['path']).resolve()
            path.relative_to(root)
            if not path.is_file() or len(ref['sha256']) != 64:
                return False
            with path.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != ref['sha256']:
                    return False
        except (KeyError, TypeError, ValueError, OSError):
            return False
    return True


def in_domain(value, constraint):
    """An interval needs explicit joint-domain evidence; sample extrema are not bounds."""
    if 'equals' in constraint:
        return fingerprint(value) == fingerprint(constraint['equals'])
    if 'one_of' in constraint:
        return any(fingerprint(value) == fingerprint(v) for v in constraint['one_of'])
    if set(constraint) >= {'min', 'max', 'unit'}:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return False
        return constraint['min'] <= value <= constraint['max']
    raise ValueError('Domain needs equals, one_of, or min/max/unit')


def screen_chain(plan, skills, initial_state, budget, evidence_root=None):
    """Check declared skill applicability and postcondition/precondition handoffs.

    Missing validation or an out-of-domain skill is unknown, never task-impossible.
    Contract facts are symbolic conditions, not a substitute for collision physics.
    """
    if not plan:
        return [Check('skill_chain', 'skill_chain', 'unknown', 'no_candidate_plan')]
    facts = dict(initial_state)
    checks = []
    for index, step in enumerate(plan):
        name = f'skill_{index}_{step.get("skill", "missing")}'
        def check_step():
            skill = skills.get(step.get('skill'))
            if not skill:
                return Check(name, 'skill_chain', 'unknown', 'unregistered_skill')
            params = step.get('parameters', {})
            matching = []
            for domain in skill.get('domains', []):
                if not domain.get('parameters') or domain.get('validation_kind') not in ('observed_case', 'validated_joint_domain'):
                    continue
                if domain['validation_kind'] == 'observed_case' and any(set(c) != {'equals'} for c in domain['parameters'].values()):
                    continue  # Single observations never establish intervals or a Cartesian product.
                if all(k in params and in_domain(params[k], condition) for k, condition in domain['parameters'].items()):
                    matching.append(domain)
            certified = next((d for d in matching if verified_artifacts(d.get('evidence'), evidence_root)), None)
            if certified is None:
                return Check(name, 'skill_chain', 'unknown', 'outside_evidenced_domain_or_missing_evidence')
            if not all(k in certified for k in ('requires','provides')):
                return Check(name, 'skill_chain', 'unknown', 'missing_evidenced_transition_contract')
            if any(fingerprint(step.get(k, {})) != fingerprint(certified[k]) for k in ('requires','provides')):
                return Check(name, 'skill_chain', 'fail', 'candidate_changes_evidenced_transition')
            for key, value in certified['requires'].items():
                if key not in facts:
                    return Check(name, 'skill_chain', 'unknown', 'missing_precondition: '+key)
                if fingerprint(facts[key]) != fingerprint(value):
                    return Check(name, 'skill_chain', 'fail', 'incompatible_handoff: '+key)
            return Check(name, 'skill_chain', 'pass', 'declared_domain_and_handoff_checked', evidence=certified['evidence'],
                         constraints={k:certified.get(k) for k in ('validation_kind','parameters','requires','provides','scope')})
        checked = budget.run(name, 'skill_chain', check_step)
        checks.append(checked)
        if checked.outcome == 'pass':
            facts.update(step.get('provides', {}))
        else:
            # Never propagate optimistic postconditions past an unverified step.
            for key in step.get('provides', {}):
                facts.pop(key, None)
    return checks


def verified_execution(execution, digest, evidence_root):
    if not isinstance(execution, dict) or not verified_artifacts([execution.get('witness', {})], evidence_root):
        return False
    try:
        witness = json.loads((Path(evidence_root)/execution['witness']['path']).read_text())
        if not isinstance(witness, dict):
            return False
        return bool(witness.get('schema') == 'oracle-execution-witness/1'
                    and witness.get('instance_sha256') == digest
                    and isinstance(witness.get('scope'), str) and witness['scope'].strip()
                    and witness.get('completed') is True and witness.get('verification_passed') is True
                    and verified_artifacts(witness.get('artifacts'), evidence_root))
    except (OSError, ValueError, KeyError):
        return False


def assess(instance, plan, key_states, checks, budget, execution=None, evidence_root=None):
    """Four exclusive statuses, with independent screening and execution dimensions."""
    digest = fingerprint(instance)
    instance_failed = any(c.outcome == 'fail' and c.scope == 'instance' for c in checks)
    covered = all(any(c.category == cat for c in checks) for cat in CATEGORIES)
    screening = 'check_failed' if instance_failed else 'screening_passed' if covered and checks and all(c.outcome == 'pass' for c in checks) else 'undetermined'
    full = verified_execution(execution, digest, evidence_root)
    # A necessary-condition failure conflicting with a success claim needs review.
    conflict = full and instance_failed
    status = 'undetermined' if conflict else 'full_success_evidence' if full else screening
    success_scope = None
    if full:
        success_scope = json.loads((Path(evidence_root)/execution['witness']['path']).read_text())['scope']
    return dict(schema='oracle-assessment/1', instance=instance, instance_sha256=digest,
                status=status, screening_status=screening, evidence_conflict=conflict,
                success_scope=success_scope,
                high_level_plan=plan, key_states=key_states,
                checks=[asdict(c) for c in checks], budget=budget.record(), execution_evidence=execution,
                global_solvability_proven=False, formal_admission=False,
                limitations=['Screening covers only recorded conditions; it is not a complete solution.',
                             'Candidate failure, missing skill evidence and budget exhaustion do not prove impossibility.'])


def write_batch(path, records, source, expected_sample_ids, sampling_manifest=None):
    """Retain every draw, including failures and unknowns; never filter a benchmark."""
    if source not in ('self_generated', 'benchmark_prescribed'):
        raise ValueError('Declare the sampling source')
    records, expected = list(records), list(expected_sample_ids)
    if any(r.get('status') not in STATUSES for r in records):
        raise ValueError('Every record needs one of the four instance statuses')
    actual = [r['instance']['sample_id'] for r in records]
    if len(set(expected)) != len(expected) or actual != expected:
        raise ValueError('Every sampled instance must be retained once, in sampling order')
    counts = {status:sum(r['status'] == status for r in records) for status in STATUSES}
    data = dict(schema='oracle-batch/1', source=source, sampled_ids=expected,
                denominator=len(expected), status_counts=counts, records=records,
                sampling_manifest=sampling_manifest, filtered_out_ids=[], screening_is_not_execution_success=True)
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return data


class RollingPlanner:
    """Generate only the next bounded control chunk from fresh measured state."""
    def __init__(self, horizon=10):
        if not isinstance(horizon, int) or horizon < 1:
            raise ValueError('Positive integer horizon required')
        self.horizon, self.replans = horizon, 0

    def next_chunk(self, measured_state, subgoal, local_planner):
        import copy
        from itertools import islice
        measured_hash = fingerprint(measured_state)
        # Planner receives a horizon, and even an unbounded generator is truncated.
        actions = list(islice(iter(local_planner(copy.deepcopy(measured_state), subgoal, self.horizon)), self.horizon))
        self.replans += 1
        return dict(measured_state_sha256=measured_hash, subgoal=subgoal,
                    horizon=self.horizon, actions=actions, replan_index=self.replans)
