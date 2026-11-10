"""Independent measurement of frozen v4-probe-acceptance.json; never full success.

The acceptance document is frozen before execution. This reader implements those
conditions; elbow reference ceiling is checked throughout, and the mirrored
finger interior reference is checked from ClearHands through final opening/hold.
The 1e-6 comparison tolerance only represents float32 command encoding (same
numeric epsilon as the frozen macro); hardware/safety tolerances are unchanged.
"""
from pathlib import Path
import argparse,ast,hashlib,json
import numpy as np


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def evaluate(run):
    run=Path(run);out=dict(schema='h1-p4-v4-independent-diagnostic-acceptance/1',diagnostic_only=True,task_success=False,full_witness=False,formal_admission=False,human_review='not_signed',diagnostic_accepted=False,checks=[],errors=[],reviewer_sha256=sha(__file__),implementation_scope='Independent reader of pre-execution frozen acceptance document; no physical/task threshold changes. Initial neutral finger reference is outside terminal opening scope.')
    def check(name,value,metrics=None):out['checks'].append(dict(predicate=name,passed=bool(value),metrics=metrics or {}))
    try:
        profile=read(run/'profile.json');outcome=read(run/'outcome.json');result=read(run/'execution/result.json');trace=read(run/'execution/trace.json');commands=read(run/'execution/command_trace.json');audit=read(run/'execution/actuator_audit.json');contract=read(run/'refinement-contract.json');receipt=read(run/'refinement_contract_binding.json');n=len(commands);dec=round(profile['budget']['control_dt_s']/profile['budget']['physics_dt_s']);eps=contract['thresholds']['joint_difference_epsilon_rad']
        if profile!=contract.get('profile_snapshot') or eps!=1e-6 or profile['controller']['elbow_upper_rad']!=2.0 or profile['controller']['finger_reference_min_rad']!=.06:raise ValueError('Frozen profile or numerical diagnostic criteria changed')
        docs=[d for d in contract.get('frozen_documents',[]) if Path(d['path']).name=='v4-probe-acceptance.json']
        if len(docs)!=1:raise ValueError('Exactly one frozen diagnostic acceptance document required')
        document=docs[0];acceptance=read(run/'frozen_documents/v4-probe-acceptance.json');out['frozen_acceptance_sha256']=document['sha256'];out['acceptance']=acceptance
        check('acceptance_document_identity',sha(run/'frozen_documents/v4-probe-acceptance.json')==document['sha256'] and sha(run/'source_snapshot'/document['path'])==document['sha256'])
        check('diagnostic_not_native_full',profile.get('diagnostic_only') is True and profile.get('full_task_witness_allowed') is False and outcome.get('task_success') is False and outcome.get('evidence_status')!='witnessed_full')
        check('contract_bound_before_first_physics',receipt.get('before_first_physics') is True and receipt['contract_sha256']==sha(run/'refinement-contract.json'))
        check('controller_finished_original_start_plan',result.get('status')=='plan_completed' and not any(profile.get(k) for k in ['resume_from','checkpoint','debug_start','diagnostic_start_state','partial_start']))
        source=read(run/'source_hashes.json');assets=read(run/'asset_hashes.json');effective=read(run/'effective_asset_hashes.json');bad=[]
        for mapping in (source,assets):
            bad.extend(f for f,h in mapping.items() if not (run/'source_snapshot'/f).exists() or sha(run/'source_snapshot'/f)!=h)
        bad.extend(f for f,h in contract.get('source_bindings',{}).items() if not (run/'source_snapshot'/f).exists() or sha(run/'source_snapshot'/f)!=h)
        check('source_and_asset_identity',not bad and assets==effective,{'mismatched':bad,'asset_pre_post_equal':assets==effective})
        check('all_physics_actuator_constraints',audit['samples']==n*dec and audit['max_position_overshoot']<=.001 and audit['max_speed_ratio']<=1.001 and audit['max_effort_ratio']<=1.001,{'samples':audit['samples'],'max_position_overshoot_rad':audit['max_position_overshoot'],'position_tolerance_rad':.001,'max_speed_ratio':audit['max_speed_ratio'],'max_effort_ratio':audit['max_effort_ratio']})
        safety=read(run/'original_safety_independent.json')
        required_safety_inputs=['execution/safety_meta.json','execution/safety_trace.npz','execution/trace.json','execution/actuator_audit.json','execution/joint_trace.npz','profile.json']
        hashes=safety.get('artifact_hashes',{})
        check('independent_safety_matches_current_inputs',all(f in hashes and (run/f).exists() and sha(run/f)==hashes[f] for f in required_safety_inputs))
        check('original_five_safety_rules',safety['complete'] and safety['safety_passed'] and not safety['errors'],{'events':safety.get('original_five_rules',{}).get('events',[]),'status':safety['status']})
        check('complete_control_timeline',len(trace)==n+1 and abs(trace[0]['time'])<1e-9 and np.allclose([r['time'] for r in trace],np.arange(n+1)*profile['budget']['control_dt_s'],atol=1e-9,rtol=0))
        phases=['clear_hands','stand_up'];control_indices=[i for i,r in enumerate(trace[:-1]) if any(r['phase'].startswith(p) for p in phases)];indices=sorted(set(control_indices+[i+1 for i in control_indices]))
        for i in indices:
            feet=trace[i]['support_contacts']['feet_ground_fz_N']
            if not isinstance(feet,list) or len(feet)!=2 or any(type(v) not in (int,float) or not np.isfinite(v) for v in feet):raise ValueError('Missing/nonfinite two-foot support measurement')
        badfeet=[i for i in indices if max(trace[i]['support_contacts']['feet_ground_fz_N'])<=1.0]
        check('clear_and_stand_sampled_foot_support',bool(indices) and not badfeet,{'samples_checked':len(indices),'failed_indices':badfeet,'failed_times_s':[trace[i]['time'] for i in badfeet],'criterion':'at least one measured floor foot force >1 N each control state'})
        with np.load(run/'execution/physics_commands.npz',allow_pickle=False) as f:data=f['data'];cols=list(f['columns'])
        check('complete_exact_physics_command_coverage',data.shape==(n*dec,81) and np.isfinite(data).all())
        jointnames=audit['joint_names'];pos=np.stack([data[:,cols.index('position_target:'+name)] for name in jointnames],axis=1)
        elbows={name:float(pos[:,jointnames.index(name)].max()) for name in ('left_elbow_joint','right_elbow_joint')}
        check('actual_elbow_command_ceiling',max(elbows.values())<=profile['controller']['elbow_upper_rad']+eps,{'maximum_reference_rad':elbows,'ceiling_rad':profile['controller']['elbow_upper_rad'],'float_encoding_tolerance_rad':eps})
        starts=[i for i,r in enumerate(trace[:-1]) if r['phase'].startswith('clear_hands') and (i==0 or not trace[i-1]['phase'].startswith('clear_hands'))]
        if not starts:raise ValueError('ClearHands terminal opening interval absent')
        start=starts[-1];tree=ast.parse((run/'source_snapshot/humanoid/g1_support_retrieval/solution/underhand_lift/hand_model.py').read_text());sign=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FLEX_SIGN' for t in node.targets));fingers={}
        for side in ('left','right'):
            for finger in ('index','middle'):
                for part in (0,1):
                    name=f'{side}_hand_{finger}_{part}_joint';fingers[name]=float((pos[start*dec:,jointnames.index(name)]*sign[side]).min())
        check('terminal_opening_finger_interior_reference',min(fingers.values())>=profile['controller']['finger_reference_min_rad']-eps,{'minimum_inward_reference_rad':fingers,'floor_rad':profile['controller']['finger_reference_min_rad'],'float_encoding_tolerance_rad':eps,'command_range_half_open':[start,n],'scope':'ClearHands through final StandUp/hold, initial neutral pose not included'})
        expected={'diagnostic_or_partial_start_never_full_witness','final_released_stable_dwell_too_short'};other=[e for e in outcome.get('errors',[]) if e not in expected]
        check('no_other_native_integrity_failures',not other,{'expected_diagnostic_or_unreached_D_errors':[e for e in outcome.get('errors',[]) if e in expected],'unexpected_errors':other})
        out['physical_goal_met_diagnostic_only']=outcome.get('physical_goal_met');out['diagnostic_accepted']=all(c['passed'] for c in out['checks'])
        out['input_hashes']={f:sha(run/f) for f in ['profile.json','refinement-contract.json','refinement_contract_binding.json','frozen_documents/v4-probe-acceptance.json','execution/trace.json','execution/command_trace.json','execution/physics_commands.npz','execution/actuator_audit.json','execution/result.json','original_safety_independent.json','outcome.json']}
    except (OSError,KeyError,ValueError,TypeError,IndexError,StopIteration) as exc:out['errors'].append(f'{type(exc).__name__}:{exc}');out['diagnostic_accepted']=False
    return out


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path);ap.add_argument('--out',type=Path);args=ap.parse_args();out=evaluate(args.run);write(args.out or args.run/'diagnostic_acceptance.json',out);print({k:out[k] for k in ['diagnostic_accepted','full_witness','errors']});return 0 if out['diagnostic_accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
