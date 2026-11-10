"""Plan and screen disk instances without generating an execution trajectory."""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import random

from infra.oracle import Budget, Check, assess, fingerprint, screen_chain, write_batch
from humanoid.g1_tabletop_disk_flip.task_spec import TaskConfig

TASK_ID = "g1_tabletop_disk_flip"


def make_instance(cfg=None, seed=0, sample_id=None):
    return dict(task_id=TASK_ID, task_version="0.1", seed=seed,
                sample_id=sample_id or f"disk-{seed}",
                robot="G1_Dex3_fixed_pelvis", physics_profile="tabletop_genesis_400hz_float64",
                config=asdict(cfg or TaskConfig()))


def config_from_instance(instance):
    for key, expected in (("task_id", TASK_ID), ("task_version", "0.1"),
                          ("robot", "G1_Dex3_fixed_pelvis"),
                          ("physics_profile", "tabletop_genesis_400hz_float64")):
        if instance.get(key) != expected:
            raise ValueError(f"unsupported {key}")
    values = dict(instance["config"])
    for name, value in dict(friction_model="pyramidal", collision_detector="mpr",
                            disk_collision_shape="cylinder", post_flip_handoff="bimanual").items():
        values.setdefault(name, value)
    for key in ("table_center", "table_size", "start_xy", "goal_xy", "object_names"):
        if key in values:
            values[key] = tuple(values[key])
    return TaskConfig(**values)


def build_plan(cfg):
    c = cfg
    lifted = [c.edge_x-.03, c.start_xy[1], c.table_height+c.disk_radius+.04]
    limits = dict(disk_linear_speed_max_m_s=c.linear_speed_max,
                  disk_angular_speed_max_rad_s=c.angular_speed_max,
                  robot_contact_force_max_n=c.robot_force_max_n,
                  table_contact_force_max_n=c.table_force_max_n,
                  joint_target_speed_max_rad_s=c.joint_target_speed_max)
    states = dict(
        edge=dict(disk_center=list(c.edge_center), face="orange_up", support="table",
                  overhang_m=[c.overhang_min, c.overhang_max]),
        clamped=dict(disk_center=list(c.edge_center), support="table_and_both_hands",
                     contact_mode="two_independent_face_pinches", stable_s=c.grasp_hold_seconds),
        lifted=dict(disk_center=lifted, support="both_hands", face="orange_up"),
        inverted=dict(disk_center=lifted, support="both_hands", face="blue_up"),
        outside_bridge=dict(disk_center=[c.edge_x-c.disk_radius-.02, c.start_xy[1], c.rest_z+.003],
                            face="blue_up", support="right_hand_outside_table_edge"),
        table_transfer=dict(disk_center=[c.edge_x+.025, c.start_xy[1], c.rest_z],
                            face="blue_up", support="table_and_lower_finger_pads"),
        released=dict(disk_center=[*c.goal_xy, c.rest_z], face="blue_up", support="table",
                      whole_disk_on_table=True, no_robot_contact=True, stable_s=c.final_hold_seconds))
    steps = []
    contracts = (
        ("slide", "gentle_slide_to_edge", ["upright_on_table"], ["edge_supported"], "edge"),
        ("clamp", "two_independent_edge_pinches", ["edge_supported"], ["bimanual_clamp"], "clamped"),
        ("lift", "bimanual_lift_clear", ["bimanual_clamp"], ["clear_of_table"], "lifted"),
        ("turn", "bimanual_half_turn", ["bimanual_clamp", "clear_of_table"], ["inverted"], "inverted"),
        ("place", "edge_setdown_withdraw_slide_release", ["bimanual_clamp", "inverted"],
         ["inverted_released_in_goal"], "released"),
    )
    for id_, skill, requires, ensures, key_state in contracts:
        steps.append(dict(id=id_, skill=skill, requires=requires, ensures=ensures,
            key_state=key_state, constraints=dict(limits),
            applicability=dict(validation="unvalidated", evidence=[],
                requested=dict(disk_mass_kg=c.disk_mass, disk_radius_m=c.disk_radius,
                               disk_height_m=c.disk_height, table_height_m=c.table_height,
                               target_disk_position_m=list(states[key_state]["disk_center"]),
                               horizontal_reach_m=math.hypot(*states[key_state]["disk_center"][:2]),
                               support_edge_x_m=c.edge_x, table_size_m=list(c.table_size),
                               required_support=states[key_state]["support"],
                               required_face=states[key_state].get("face", "orange_up"),
                               contact_mode=states[key_state].get("contact_mode", "skill_defined"),
                               arm_stiffness_scale=c.arm_stiffness_scale,
                               friction_model=c.friction_model,
                               collision_detector=c.collision_detector,
                               disk_collision_shape=c.disk_collision_shape,
                               post_flip_handoff=c.post_flip_handoff),
                validated_ranges=None)))
        if id_ == "place" and c.post_flip_handoff == "gentle_placement":
            steps[-1]["subgoals"] = ["outside_bridge", "table_transfer", "released"]
            steps[-1]["constraints"]["placement_handoff"] = c.post_flip_handoff
    return dict(initial_facts=["upright_on_table"], goal_facts=["inverted_released_in_goal"],
                steps=steps, key_states=states, constraints=limits,
                execution=dict(mode="rolling_local_planning", horizon_control_steps=1,
                               precomputed_full_trajectory_required=False),
                limitations=["Nominal key states are constraints, not commanded object poses",
                             "No disk manipulation skill has a validated applicability envelope"])


def screen_instance(instance, *, budget_s=1., evidence_root=None):
    budget = Budget(max_checks=32, seconds=budget_s)
    try:
        c = config_from_instance(instance)
    except (KeyError, TypeError, ValueError) as exc:
        return assess(instance, [], {}, [Check("task_configuration", "support", "fail",
            "sample violates the task configuration contract: "+str(exc), scope="instance")], budget)
    plan = build_plan(c)
    # Skill identities and their joint operating conditions are explicit. None
    # has certified domains yet: successful no-op and scoring tests are not
    # manipulation skill evidence and cannot establish an applicability range.
    chain = [dict(id=step["id"], skill=step["skill"],
                  requires={fact: True for fact in step["requires"]},
                  provides={fact: True for fact in step["ensures"]},
                  parameters=dict(step["applicability"]["requested"],
                                  robot=instance["robot"], physics_profile=instance["physics_profile"],
                                  task_version=instance["task_version"], task_config=asdict(c),
                                  physics_seed=instance["seed"]),
                  constraints=step["constraints"], key_state=step["key_state"],
                  subgoals=step.get("subgoals", [step["key_state"]]))
             for step in plan["steps"]]
    skills = {step["skill"]: dict(domains=[], validation="unvalidated") for step in chain}
    checks = []
    catalog = None
    observed_case = None
    if evidence_root is not None:
        def check_evidence():
            nonlocal catalog, observed_case
            from .evidence import load_catalog
            candidate = load_catalog(evidence_root)
            matched = next((case for case in candidate["cases"]
                            if fingerprint(case["config"]) == fingerprint(asdict(c))
                            and case["seed"] == instance["seed"]), None)
            if matched is None:
                return Check("observed_operating_point", "skill_chain", "unknown",
                             "outside_observed_configuration_and_seed; no interval is inferred")
            catalog, observed_case = candidate, matched
            return Check("observed_operating_point", "skill_chain", "pass",
                         "exact_operating_point_with_execution_replay_and_matching_model_runtime",
                         evidence=matched["evidence"])
        checked = budget.run("observed_operating_point", "skill_chain", check_evidence)
        checks.append(checked)
        if checked.outcome == "pass":
            skills = {step["skill"]: catalog["skills"].get(step["skill"], skills[step["skill"]]) for step in chain}
        else:
            catalog = observed_case = None
    def analytic(name, category, condition, reason, scope="candidate"):
        checks.append(budget.run(name, category, lambda:
            Check(name, category, "pass" if condition else "fail", reason, scope), scope))
    def unresolved(name, category, reason):
        def check():
            if observed_case is not None:
                return Check(name, category, "pass",
                    "observed_in_complete_execution_and_independent_replay_at_exact_parameters; "
                    "not_a_continuous_domain_or_substep_collision_certificate",
                    evidence=observed_case["evidence"])
            return Check(name, category, "unknown", reason)
        checks.append(budget.run(name, category, check))
    analytic("edge_support", "support", c.edge_center[0] > c.edge_x,
             "disk centre remains inside the near support edge")
    analytic("static_weight", "support", c.disk_mass*9.81 <= c.table_force_max_n,
             f"resting weight {c.disk_mass*9.81:.6g} N must fit table-force limit {c.table_force_max_n} N", "instance")
    analytic("lift_force", "support", c.disk_mass*9.81 <= c.robot_force_max_n,
             f"lifting weight {c.disk_mass*9.81:.6g} N must fit robot-contact limit {c.robot_force_max_n} N", "instance")
    analytic("disk_turn_clearance", "collision",
             plan["key_states"]["lifted"]["disk_center"][2]-math.hypot(c.disk_radius, c.disk_height/2)
             > c.table_height+c.clearance,
             "nominal disk swept volume clears tabletop; whole-robot collision remains unchecked")
    unresolved("bimanual_reachability", "reachability",
               "joint-limit and orientation-constrained IK for both hands is not validated")
    unresolved("robot_swept_collision", "collision",
               "whole-robot paths and underhand entry/withdrawal require collision checks")
    unresolved("grasp_wrench_support", "support",
               "measured contact lever arms, per-finger preload and frictional support are unvalidated; "
               "the runtime normal-wrench model alone is not a friction-closure certificate")
    unresolved("physical_handoffs", "skill_chain",
               "slide-to-clamp and flipped-edge-to-release transitions need bounded contact probes")
    checks.extend(screen_chain(chain, skills, {"upright_on_table": True}, budget, evidence_root=evidence_root))
    execution = catalog.get("executions", {}).get(fingerprint(instance)) if catalog is not None else None
    report = assess(instance, chain, plan["key_states"], checks, budget,
                    execution=execution, evidence_root=evidence_root)
    report.update(skill_catalog=skills, constraints=plan["constraints"],
                  execution_contract=plan["execution"], trajectory=None)
    report["limitations"].extend(plan["limitations"] if observed_case is None else [
        "Skill evidence covers only the exact recorded configuration and physics seed",
        "Human video review and formal admission are separate from automated execution evidence"])
    return report


def development_samples(count, seed, evidence_root=None):
    """Proposed design range only: no validated skill range currently exists.

    Future task adapters should preferentially sample certified skill envelopes.
    Do not silently treat these provisional ranges as a certified envelope.
    """
    rng = random.Random(seed)
    cases = []
    if evidence_root is not None:
        try:
            from .evidence import load_catalog
            cases = load_catalog(evidence_root, verify_runtime=False)["cases"]
        except (OSError, ValueError, KeyError, TypeError):
            pass  # Provisional sampling is explicitly labelled below.
    for index in range(count):
        if cases:
            case = rng.choice(cases)
            instance = make_instance(config_from_instance(case["instance"]), case["seed"], sample_id=f"draw-{index}")
            instance["sampling"] = dict(mode="development", generator_seed=seed, draw_index=index,
                range_basis="observed_configuration_points_only_no_interpolated_range", evidence_case=case["id"])
            yield instance
            continue
        cfg = TaskConfig(start_xy=(rng.uniform(.55, .62), rng.uniform(-.08, .08)),
                         disk_mass=rng.uniform(.10, .15))
        instance = make_instance(cfg, seed+index, sample_id=f"draw-{index}")
        instance["sampling"] = dict(mode="development", generator_seed=seed, draw_index=index,
                                    range_basis="provisional_design_no_validated_skill_envelope")
        yield instance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", type=Path, help="JSON list of prescribed instances; retained verbatim")
    parser.add_argument("--source", choices=("self_generated", "benchmark_prescribed"), default="self_generated")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--budget-s", type=float, default=1.)
    parser.add_argument("--evidence-root", type=Path,
                        default=Path(__file__).resolve().parents[1]/"validation/release",
                        help="optional verified operating-point bundle; missing evidence remains unknown")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.budget_s) or args.budget_s < 0 or args.count < 1:
        parser.error("nonnegative finite budget and positive count required")
    if args.source == "benchmark_prescribed" and args.instances is None:
        parser.error("benchmark screening requires the prescribed --instances; no replacement sampling")
    if args.instances:
        instances = json.loads(args.instances.read_text())
        if not isinstance(instances, list) or not all(isinstance(i, dict) for i in instances):
            parser.error("--instances must contain a JSON list of instance objects")
    else:
        instances = list(development_samples(args.count, args.seed, args.evidence_root))
    ids = [instance.get("sample_id") for instance in instances]
    if any(not isinstance(id_, str) or not id_ for id_ in ids) or len(set(ids)) != len(ids):
        parser.error("each draw requires a distinct nonempty sample_id; equal configurations are retained")
    records = [screen_instance(instance, budget_s=args.budget_s, evidence_root=args.evidence_root) for instance in instances]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = write_batch(args.output, records, args.source, ids)
    print(json.dumps(dict(output=str(args.output), counts=report["status_counts"],
                          sampled=report["denominator"], retained=len(report["records"]))))



if __name__ == "__main__":
    main()
