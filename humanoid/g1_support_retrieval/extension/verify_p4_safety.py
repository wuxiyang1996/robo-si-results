"""P4 adapter to original H1 five safety rules; no threshold changes.

Missing force/geometry/signed-torque channels yield unknown, never zero-filled
support or a clean safety certificate. Body support is passed to the original
rules, so kneeling/sitting are not rejected by an invented feet-only rule.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import hashlib
import numpy as np
from ..sandbox.trusted import relay_safety as fall
from ..sandbox.trusted import relay_safety_rules as rules
from infra.sandbox import monitors


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def validate(a,meta,trace,actuator):
    n=len(trace)
    if n<2:raise ValueError('too few safety samples')
    ids=meta['object_ids'];k=len(ids)
    if not k or len(set(ids))!=k:raise ValueError('missing/duplicate object identities')
    expected={'t':(n,),'root_pos':(n,3),'root_quat':(n,4),'root_vel':(n,3),'root_angvel':(n,3),'foot_bottom_m':(n,2),'feet_floor_fz':(n,2),'object_pos':(n,k,3),'object_quat':(n,k,4),'foot_object_fz':(n,k,2),'hand_object_force':(n,k,2),'body_object_force':(n,k),'foot_cabinet_force':(n,2),'hand_cabinet_force':(n,2),'body_cabinet_force':(n,),'body_ground_force':(n,),'q':(n,43),'tau':(n,43),'invalid_mask':(n,)}
    missing=[]
    for key,shape in expected.items():
        if key not in a:missing.append(key);continue
        if np.shape(a[key])!=shape or not np.isfinite(a[key]).all():raise ValueError('invalid shape/nonfinite:'+key)
    if missing:raise ValueError('missing safety channels:'+','.join(missing))
    if not np.isin(a['invalid_mask'],[0,1]).all():raise ValueError('invalid safety anomaly mask')
    if (np.abs(np.linalg.norm(a['root_quat'],axis=1)-1)>.001).any() or (np.abs(np.linalg.norm(a['object_quat'],axis=2)-1)>.001).any():raise ValueError('invalid quaternion')
    if abs(float(a['t'][0]))>1e-9:raise ValueError('safety timeline does not start at original t0')
    if actuator['samples']!=(n-1)*round(meta['control_dt']/actuator['physics_dt']):raise ValueError('safety/control/physics coverage mismatch')
    if not np.allclose(a['t'],[r['time'] for r in trace],atol=1e-9,rtol=0):raise ValueError('safety/trajectory clock mismatch')
    if not np.isclose(float(meta['control_dt']),.02) or not np.allclose(np.diff(a['t']),meta['control_dt'],atol=1e-9,rtol=0):raise ValueError('invalid control cadence')
    for key in ('joint_names','joint_effort_limits','joint_lower','joint_upper'):
        if meta[key]!=actuator[key]:raise ValueError('frozen actuator identity mismatch:'+key)
    if len(meta['joint_names'])!=43 or len(set(meta['joint_names']))!=43:raise ValueError('invalid joint identities')
    for key in ('joint_effort_limits','joint_lower','joint_upper'):
        if np.shape(meta[key])!=(43,) or not np.isfinite(meta[key]).all():raise ValueError('invalid limits:'+key)
    if not np.isclose(meta['robot_mass_kg'],rules.ROBOT_MASS_KG,atol=1e-6,rtol=0):raise ValueError('original safety body-weight binding mismatch')
    if np.shape(meta['object_sizes_m'])!=(k,3) or np.shape(meta['object_present'])!=(k,) or not np.isfinite(meta['object_sizes_m']).all() or (np.array(meta['object_sizes_m'])<=0).any():raise ValueError('object geometry binding missing')
    if not all(value is True for value in meta['object_present']):raise ValueError('P4 physical object presence cannot mask parked collidable entities')
    if not isinstance(meta['target_index'],int) or not 0<=meta['target_index']<k:raise ValueError('target index missing')
    if meta.get('torque_provenance')!={'quantity':'signed_actual_joint_force','source':'robot.get_dofs_control_force','sampling':'same_state_time_as_q'}:raise ValueError('missing signed actual torque provenance')
    if not isinstance(meta.get('contact_mapping'),dict) or not meta['contact_mapping']:raise ValueError('contact link identity mapping missing')
    for key in ('hand_object_force','body_object_force','foot_cabinet_force','hand_cabinet_force','body_cabinet_force','body_ground_force'):
        if (a[key]<0).any():raise ValueError('negative contact magnitude:'+key)
    j=meta['target_index']
    if not np.allclose(a['object_pos'][:,j],[r['box'] for r in trace],atol=1e-6,rtol=0) or not np.allclose(a['root_pos'],[r['root'] for r in trace],atol=1e-6,rtol=0):raise ValueError('safety/trajectory pose mismatch')


def evaluate_arrays(a,meta,trace,actuator):
    validate(a,meta,trace,actuator)
    safety=fall.evaluate_fall_safety(a,meta)
    j=meta['target_index'];free=np.asarray(a['hand_object_force'])[:,j,:].max(axis=1)<1.0
    # Use the exact measured target geometry/speed rather than a hand-authored
    # synthetic trajectory; final release follows the original <1 N definition.
    result=rules.evaluate(a,meta,meta['object_ids'],np.asarray(meta['object_present'],bool),np.asarray(meta['object_sizes_m']),~np.asarray(a['invalid_mask'],bool),safety,free,np.array([r['bottom'] for r in trace]),np.array([r['box_speed'] for r in trace]),a)
    alarms,diagnostics=rules.command_alarms(a['t'],a['q'],a['tau'],meta['joint_names'],np.asarray(meta['joint_effort_limits']),np.asarray(meta['joint_lower']),np.asarray(meta['joint_upper']),safety['fallen'])
    complete=bool(result['complete'] and safety['safety_coverage']['complete'] and not np.asarray(safety['pending']).any())
    return dict(status='failed' if result['events'] else 'passed' if complete else 'unknown',complete=complete,safety_passed=complete and not result['events'],original_five_rules=result,fall_coverage=safety['safety_coverage'],fall_support_reference=safety['support_load_reference'],fall_pending_samples=int(np.asarray(safety['pending']).sum()),command_pattern_diagnostics={'alarms':alarms,'metrics':diagnostics,'non_rule5_alarms_are_diagnostic_only':True},limitations=safety['limitations'])


def review(run):
    run=Path(run);out=dict(schema='h1-p4-original-safety-adapter/1',status='unknown',complete=False,safety_passed=False,formal_admission=False,thresholds_changed=False,errors=[],source_hashes={str(Path(m.__file__).resolve()):sha(m.__file__) for m in (fall,rules,monitors)},adapter_source_sha256=sha(__file__))
    try:
        trace=read(run/'execution/trace.json');actuator=read(run/'execution/actuator_audit.json')
        # Even v2 has enough evidence for a limited final-release rule review.
        free=np.array([not any(str(link).startswith(('left_hand_','right_hand_')) or link in ('left_wrist_yaw_link','right_wrist_yaw_link') for link in r['contact_links']) for r in trace])
        ev,metric=rules.final_release(np.array([r['time'] for r in trace]),free,np.array([r['bottom'] for r in trace]),np.array([r['box_speed'] for r in trace]),.02)
        out['partial_rule4_contact_identity_review']={'events':ev,'metrics':metric,'scope':'Contact-identity final release only; complete rules use canonical <1 N measured hand force.'}
        meta=read(run/'execution/safety_meta.json')
        with np.load(run/'execution/safety_trace.npz',allow_pickle=False) as f:a={k:f[k] for k in f.files}
        # Bind canonical safety channels to independent primary trajectory and
        # frozen MJCF joint ordering, never blindly qpos[7:]==actuator order.
        from .verify_skill_refinement import joint_order
        names,_=joint_order(run,actuator)
        with np.load(run/'execution/joint_trace.npz',allow_pickle=False) as f:q=f['measured']
        order=[names.index(name) for name in meta['joint_names']]
        if q.shape!=(len(trace),50) or not np.allclose(a['q'],q[:,7:][:,order],atol=1e-7,rtol=0):raise ValueError('safety joint states differ from measured joint_trace')
        if not np.allclose(a['root_quat'],q[:,3:7],atol=1e-7,rtol=0):raise ValueError('safety root quaternion differs from measured joint_trace')
        if not np.allclose(a['feet_floor_fz'],[r['support_contacts']['feet_ground_fz_N'] for r in trace],atol=1e-6,rtol=0):raise ValueError('safety foot support differs from primary trace')
        if (np.max(np.abs(a['tau']),axis=0)>np.array(actuator['max_abs_tau'])+1e-5).any():raise ValueError('sampled actual torque exceeds all-step audit maximum')
        profile=read(run/'profile.json');j=meta['target_index']
        if not np.allclose(meta['object_sizes_m'][j],profile['target']['size_m'],atol=1e-9,rtol=0):raise ValueError('target size identity mismatch')
        out.update(evaluate_arrays(a,meta,trace,actuator))
        out['coverage_binding']={'first_time_s':float(a['t'][0]),'last_time_s':float(a['t'][-1]),'state_samples':len(trace),'physics_samples':actuator['samples'],'all_control_samples_including_terminal':True,'joint_trace_bound':True,'source_mapping':meta['contact_mapping'],'torque_provenance':meta['torque_provenance']}
        out['artifact_hashes']={n:sha(run/n) for n in ('execution/safety_meta.json','execution/safety_trace.npz','execution/trace.json','execution/actuator_audit.json','execution/joint_trace.npz','profile.json')}
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        out.update(status='unknown',complete=False,safety_passed=False)
        out['errors'].append(f'{type(exc).__name__}:{exc}')
        out['remaining_measurements']=['root quaternion and exact foot-bottom geometry','all movable object poses and per-foot/per-hand/body object contacts','foot/hand/non-hand cabinet contact magnitudes','body-ground support magnitude','signed measured actual torque and joint positions for all 43 actuators throughout the control timeline','frozen robot/object/contact-link identities']
    return out


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path);ap.add_argument('--out',type=Path);args=ap.parse_args();out=review(args.run);write(args.out or args.run/'original_safety_review.json',out);print(json.dumps({k:out[k] for k in ('status','complete','safety_passed','errors')}));return 0 if out['safety_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
