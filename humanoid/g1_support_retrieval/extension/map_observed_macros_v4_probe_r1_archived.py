"""Post-execution measured P4 macro explanation, never a replacement skill verdict.

Developed after 8034839 outcome and failed leaf predicates were inspected.
Keep command-label leaves and their failures intact. Group touching/pushing/release
as one observed transport macro; do not claim the original Touch exit contract.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from .verify_skill_refinement import (read,write,sha,check,combine,segment_checks,
    key_state,hand_contact,released,grounded,double_support,foot_forces,CONTRACT)

DEFINITION={
    "schema":"h1-p4-observed-macro-definition/1",
    "version":"2026-10-27.post-execution.v1",
    "timing":"Defined after 8034839 outcome, original leaf failures and actuator violation were inspected. Post-execution description, not prospectively declared skill acceptance.",
    "scope":"Observed effects of this continuous physical trace only. Does not validate arbitrary skill starts, independent low-level leaf contracts, actuator compliance, sensor-only execution, or formal admission.",
    "transport":"Adjacent Touch+Push+Retreat interval: both raw hand contacts occur, target progresses toward D on ground with two feet planted, exits released and target speed <.02 m/s. No claim of simultaneous raw contact at nominal Touch exit.",
    "reposition":"PlannedSteps and following intermediate ReturnHands: measured bilateral unloaded swings, supported landing and forward displacement, hands released, real following Touch establishes executed contact reachability. Final ReturnHands instead joins final release macro.",
    "release":"Final ReturnHands/Retreat/ClearHands/Hold/Recenter/StandUp/Hold: preserve individual measured physical checks; recenter is nonphysical bookkeeping, final geometric goal separated from strict actuator verdict.",
    "preservation":"Every original command interval, raw boundary and leaf fail/unknown is referenced without relabeling its success. No command or physics state is changed.",
}


def freeze_contract(out, profile_path):
    out=Path(out)
    if out.exists():raise FileExistsError('Never overwrite a frozen macro contract')
    # These predicates were developed on v2. They may be declared for FUTURE v3
    # executions, but never retroactively described as predeclared for v2.
    profile=read(profile_path)
    value=dict(schema='h1-p4-prospective-macro-contract/1',frozen_at_utc=datetime.now(timezone.utc).isoformat(),task_id='H1S-07.P4',origin='Rules developed after v2 outcomes; prospectively declared only for later run IDs started after this freeze.',reviewer_source_sha256=sha(__file__),profile_sha256=sha(profile_path),profile_snapshot=read(profile_path),definition=DEFINITION,definition_role_override='Prospective executable macro skill contract for future matching-profile runs; old leaf predicates retained as diagnostic, not exact leaf-boundary acceptance.',thresholds=CONTRACT['thresholds'],plan=[{'high_level':'H1','macro':'observed_approach'}, {'high_level':'H2/H3','repeat':profile['controller']['cycles'],'sequence':['observed_ground_transport','observed_foot_reposition']},{'high_level':'H4','macro':'observed_release_and_stand'}],success='All measured macro effects, complete command/shared-boundary coverage, original 1 mrad actuator compliance and strict native goal/identity verdict. Original fine-grained leaf statuses remain separately visible. No human or formal admission claim.')
    repo=Path(__file__).resolve().parents[3]
    sources=['humanoid/g1_support_retrieval/solution/carry_box/plan_carry.py','humanoid/g1_support_retrieval/solution/underhand_lift/hand_model.py','humanoid/g1_support_retrieval/solution/underhand_lift/phases.py','humanoid/g1_support_retrieval/extension/verify_p4.py','humanoid/g1_support_retrieval/extension/safety_recording.py','humanoid/g1_support_retrieval/sandbox/trusted/statelog.py','humanoid/g1_support_retrieval/extension/run_p4.py','humanoid/g1_support_retrieval/solution/push_box/run_push.py','humanoid/g1_support_retrieval/extension/verify_skill_refinement.py','humanoid/g1_support_retrieval/extension/verify_p4_safety.py','humanoid/g1_support_retrieval/sandbox/trusted/relay_safety.py','humanoid/g1_support_retrieval/sandbox/trusted/relay_safety_rules.py','infra/sandbox/monitors.py']
    value['source_bindings']={f:sha(repo/f) for f in sources}
    value['diagnostic_only']=bool(profile.get('diagnostic_only',False))
    value['success']+=' Original shared five-rule safety review must be complete with no events; missing fields mean unknown.'
    write(out,value);return value


def build(run, semantic_path, contract_path=None):
    run=Path(run); semantic_path=Path(semantic_path)
    sem=read(semantic_path);trace=read(run/'execution/trace.json');profile=read(run/'profile.json')
    q=np.load(run/'execution/joint_trace.npz',allow_pickle=False)['measured']
    binding=None
    if contract_path:
        binding=read(contract_path)
        receipt=read(run/'refinement_contract_binding.json')
        if receipt.get('contract_sha256')!=sha(contract_path) or receipt.get('before_first_physics') is not True or datetime.fromisoformat(receipt['bound_at_utc'])<datetime.fromisoformat(binding['frozen_at_utc']):raise ValueError('Missing pre-physics contract binding receipt')
        for source,digest in binding['source_bindings'].items():
            if sha(run/'source_snapshot'/source)!=digest:raise ValueError('Frozen macro source binding mismatch:'+source)
        if binding['reviewer_source_sha256']!=sha(__file__) or binding['profile_snapshot']!=profile or binding['definition']!=DEFINITION or binding['thresholds']!=CONTRACT['thresholds']:raise ValueError('Frozen macro source/profile/rules mismatch')
    segments=sem['segments']; th=CONTRACT['thresholds']; macros=[]; i=0
    while i<len(segments):
        starti=i;s=segments[i];kind=s['skill']
        if kind=='touch':
            expected=['touch','push','retreat']
            if [a['skill'] for a in segments[i:i+3]]!=expected:raise ValueError('Unexpected transport macro sequence; no inferred missing phases')
            i+=3;typ='observed_ground_transport';hl='H2_ground_supported_transport'
        elif kind=='planned_steps':
            i+=1;typ='observed_foot_reposition';hl='H3_reposition_for_next_contact'
            if i+1<len(segments) and segments[i]['skill']=='return_hands' and segments[i+1]['skill']=='touch':i+=1
        elif kind=='return_hands':
            if any(a['skill'] in ('touch','push','planned_steps') for a in segments[i:]):raise ValueError('Unrecognized final-release context')
            i=len(segments);typ='observed_release_and_stand';hl='H4_release_and_stabilize_delivery'
        elif kind=='approach':i+=1;typ='observed_approach';hl='H1_observe_and_establish_push_posture'
        else:raise ValueError('Unexpected top-level phase '+kind)
        group=segments[starti:i];start=group[0]['range_half_open'][0];stop=group[-1]['range_half_open'][1];rows=trace[start:stop+1];checks=[]
        if typ=='observed_ground_transport':
            checks=segment_checks('push',rows,profile,th)
            checks.append(check('raw_bilateral_contact_occurs_within_macro',lambda:all(any(hand_contact(r,side,th) for r in rows) for side in ('left','right'))))
            checks.append(check('released_at_macro_exit',lambda:released(rows[-1],th)))
        elif typ=='observed_foot_reposition':
            checks=segment_checks('planned_steps',rows,profile,th)
            if group[-1]['skill']=='return_hands':checks.extend(group[-1]['checks'])
        else:
            checks=[dict(c,source_original_segment=a['id']) for a in group if a['credit_as_physical_skill'] for c in a['checks']]
        leaves=[a for a in sem['low_level_action_segments'] if start<=a['range_half_open'][0] and a['range_half_open'][1]<=stop]
        witnesses={}
        if typ=='observed_ground_transport':
            witnesses['first_raw_hand_contact_state_index']={side:next((start+j for j,r in enumerate(rows) if hand_contact(r,side,th)),None) for side in ('left','right')}
            witnesses['target_displacement_m']=(np.array(rows[-1]['box'])-np.array(rows[0]['box'])).tolist()
            witnesses['exit_target_speed_m_s']=rows[-1]['box_speed']
        if typ=='observed_foot_reposition':
            witnesses['feet_displacement_m']=(np.array(rows[-1]['feet_meas'])-np.array(rows[0]['feet_meas'])).tolist()
            witnesses['first_measured_unloaded_swing_state_index']={side:next((start+j for j,r in enumerate(rows) if r['feet_meas'][leg][2]-rows[0]['feet_meas'][leg][2]>th['foot_lift_above_initial_m'] and foot_forces(r)[leg]<=th['ground_contact_N'] and foot_forces(r)[1-leg]>th['ground_contact_N']),None) for leg,side in enumerate(('left','right'))}
        macros.append(dict(id=f'M{len(macros)+1:02d}',observed_macro=typ,high_level_id=hl,original_segment_ids=[a['id'] for a in group],range_half_open=[start,stop],command_range_half_open=[start,stop],time_s=[rows[0]['time'],rows[-1]['time']],entry=key_state(rows[0],q[start]),exit=key_state(rows[-1],q[stop]),checks=checks,measured_effect_status=combine(checks),witnesses=witnesses,original_leaf_ids=[a['id'] for a in leaves],original_leaf_failures_and_unknown=[dict(id=a['id'],status=a['status'],credit_as_physical_skill=a.get('credit_as_physical_skill',True),checks=[c for c in a['checks'] if c['status']!='passed']) for a in leaves if a['status']!='passed']))
    transitions=[dict(from_macro=a['id'],to_macro=b['id'],shared_state_index=a['range_half_open'][1],identical_measured_boundary=a['exit']==b['entry']) for a,b in zip(macros,macros[1:])]
    out=dict(schema='h1-p4-post-execution-observed-macro-mapping/1',definition=DEFINITION,definition_source_sha256=sha(__file__),source_semantic_report=str(semantic_path),source_semantic_sha256=sha(semantic_path),original_semantic_complete=sem['semantic_refinement_complete'],original_leaf_counts=sem['low_level_action_counts'],strict_actuator_check=sem['actuator_coverage_check'],terminal_goal=sem['terminal_goal_recomputation'],macros=macros,transitions=transitions,all_macro_effects_measured=all(m['measured_effect_status']=='passed' for m in macros),command_coverage_complete=bool(macros) and macros[0]['range_half_open'][0]==0 and macros[-1]['range_half_open'][1]==len(trace)-1 and all(t['identical_measured_boundary'] for t in transitions),compliant_complete_refinement=False,formal_admission=False,human_review='not_signed')
    out['interpretation']='Measured macro effects are a retrospective explanation. The original leaf failures/unknown and strict actuator violations remain; this artifact cannot upgrade the run to witnessed_full or claim the original skill decomposition passed.'
    if binding:
        out['prospective_contract']={'path':str(contract_path),'sha256':sha(contract_path),'frozen_at_utc':binding['frozen_at_utc'],'scope':binding['definition_role_override'],'origin':binding['origin']}
        expected=['observed_approach']+['observed_ground_transport','observed_foot_reposition']*profile['controller']['cycles']+['observed_release_and_stand']
        out['declared_macro_sequence_matches']=[m['observed_macro'] for m in macros]==expected
        from .verify_p4_safety import review as safety_review
        out['original_shared_safety_review']=safety_review(run)
        out['prospectively_declared_macro_refinement_complete']=bool(not profile.get('diagnostic_only',False) and not binding.get('diagnostic_only',False) and out['original_shared_safety_review']['safety_passed'] and out['all_macro_effects_measured'] and out['command_coverage_complete'] and out['declared_macro_sequence_matches'] and sem['actuator_coverage_check']['status']=='passed' and sem['terminal_goal_recomputation']['task_success'] and sem['runtime_identity_verdict'] and sem['runtime_identity_verdict'].get('task_success') is True and sem['runtime_identity_verdict'].get('evidence_status')=='witnessed_full')
        out['interpretation']='These macro rules originate in v2 post-execution analysis and are bound here to a separate frozen contract for a later matching-profile run. Fine-grained leaf failures remain diagnostic and are not called passed. Strict actuator/goal/identity and original five safety rules remain necessary.'
    return out


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path,nargs='?');ap.add_argument('--semantic',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--contract',type=Path);ap.add_argument('--freeze-profile',type=Path);args=ap.parse_args()
    if args.freeze_profile:
        if not args.out:ap.error('--out required for freeze')
        freeze_contract(args.out,args.freeze_profile);print(args.out);return
    if not args.run or not args.semantic:ap.error('run and --semantic required')
    out=build(args.run,args.semantic,args.contract);write(args.out or args.run/'observed_macro_mapping.json',out);print({k:out[k] for k in ['all_macro_effects_measured','command_coverage_complete','compliant_complete_refinement','original_leaf_counts']})
if __name__=='__main__':main()
