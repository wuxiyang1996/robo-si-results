"""Post-execution measured P4 macro explanation, never a replacement skill verdict.

Developed after 8034839 outcome and failed leaf predicates were inspected.
Keep command-label leaves and their failures intact. Group touching/pushing/release
as one observed transport macro; do not claim the original Touch exit contract.
"""
from __future__ import annotations
import argparse
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


def build(run, semantic_path):
    run=Path(run); semantic_path=Path(semantic_path)
    sem=read(semantic_path);trace=read(run/'execution/trace.json');profile=read(run/'profile.json')
    q=np.load(run/'execution/joint_trace.npz',allow_pickle=False)['measured']
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
    return out


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path);ap.add_argument('--semantic',type=Path,required=True);ap.add_argument('--out',type=Path);args=ap.parse_args();out=build(args.run,args.semantic);write(args.out or args.run/'observed_macro_mapping.json',out);print({k:out[k] for k in ['all_macro_effects_measured','command_coverage_complete','compliant_complete_refinement','original_leaf_counts']})
if __name__=='__main__':main()
