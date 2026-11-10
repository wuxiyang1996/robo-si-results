"""Synthetic diagnostic-gate fixtures only; never physical witnesses."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,json,unittest
import numpy as np
from .verify_v4_probe import evaluate


class V4ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.p=Path(self.tmp.name);(self.p/'execution').mkdir();(self.p/'frozen_documents').mkdir();(self.p/'source_snapshot/humanoid/g1_support_retrieval/solution/underhand_lift').mkdir(parents=True)
        def wr(name,x):
            f=self.p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(x))
        self.wr=wr;self.sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
        self.names=['left_elbow_joint','right_elbow_joint']+[f'{s}_hand_{f}_{j}_joint' for s in ['left','right'] for f in ['index','middle'] for j in [0,1]]+[f'joint_{j}' for j in range(33)]
        profile={'diagnostic_only':True,'full_task_witness_allowed':False,'budget':{'control_dt_s':.02,'physics_dt_s':.005},'controller':{'elbow_upper_rad':2.,'finger_reference_min_rad':.06}};wr('profile.json',profile)
        doc='humanoid/g1_support_retrieval/extension/v4-probe-acceptance.json';wr('source_snapshot/'+doc,{'conditions':['synthetic fixture only'],'frozen_before_launch':True});(self.p/'frozen_documents/v4-probe-acceptance.json').write_bytes((self.p/'source_snapshot'/doc).read_bytes());contract={'profile_snapshot':profile,'thresholds':{'joint_difference_epsilon_rad':1e-6},'frozen_documents':[{'path':doc,'sha256':self.sha(self.p/'source_snapshot'/doc)}]};wr('refinement-contract.json',contract);wr('refinement_contract_binding.json',{'before_first_physics':True,'contract_sha256':self.sha(self.p/'refinement-contract.json')})
        hand='humanoid/g1_support_retrieval/solution/underhand_lift/hand_model.py';(self.p/'source_snapshot'/hand).write_text('FLEX_SIGN={"left":-1.,"right":1.}\n');wr('source_hashes.json',{hand:self.sha(self.p/'source_snapshot'/hand)});wr('source_snapshot/asset.json',{'synthetic':True});assets={'asset.json':self.sha(self.p/'source_snapshot/asset.json')};wr('asset_hashes.json',assets);wr('effective_asset_hashes.json',assets)
        wr('outcome.json',{'task_success':False,'evidence_status':'diagnostic_only','physical_goal_met':False,'errors':['diagnostic_or_partial_start_never_full_witness','final_released_stable_dwell_too_short']});wr('execution/result.json',{'status':'plan_completed'});self.trace=[{'time':i*.02,'phase':p,'support_contacts':{'feet_ground_fz_N':[100,100]}} for i,p in enumerate(['approach','clear_hands_both','stand_up_both','hold_both','terminal'])];wr('execution/trace.json',self.trace);wr('execution/command_trace.json',[{}]*4);wr('execution/actuator_audit.json',{'samples':16,'max_position_overshoot':.0005,'max_speed_ratio':.1,'max_effort_ratio':1.,'joint_names':self.names});wr('original_safety_independent.json',{'complete':True,'safety_passed':True,'errors':[],'status':'passed','original_five_rules':{'events':[]}})
        self.data=np.zeros((16,81));self.cols=['time','mode']+['position_target:'+n for n in self.names]+[f'other_{i}' for i in range(36)];self.data[:,2:4]=1.
        for j,name in enumerate(self.names):
            if '_hand_' in name:self.data[:,2+j]=-.06 if name.startswith('left') else .06
        self.save()
        for name in ['execution/safety_meta.json','execution/safety_trace.npz','execution/joint_trace.npz']:wr(name,{'synthetic':True})
        safety=json.loads((self.p/'original_safety_independent.json').read_text());safety['artifact_hashes']={name:self.sha(self.p/name) for name in ['execution/safety_meta.json','execution/safety_trace.npz','execution/trace.json','execution/actuator_audit.json','execution/joint_trace.npz','profile.json']};wr('original_safety_independent.json',safety)
    def tearDown(self):self.tmp.cleanup()
    def save(self):np.savez(self.p/'execution/physics_commands.npz',data=self.data,columns=np.array(self.cols))
    def test_clean_diagnostic_pass_never_full(self):
        x=evaluate(self.p);self.assertTrue(x['diagnostic_accepted']);self.assertFalse(x['full_witness']);self.assertFalse(x['task_success'])
    def test_elbow_ceiling_covers_initial_and_terminal_commands(self):
        self.data[0,2]=2.1;self.save();self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_finger_margin_checks_entire_clear_interval_not_last_row(self):
        self.data[4,4]=0;self.save();self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_initial_neutral_is_not_terminal_opening(self):
        self.data[:4,4:12]=0;self.save();self.assertTrue(evaluate(self.p)['diagnostic_accepted'])
    def test_missing_foot_load_at_shared_exit_rejected(self):
        self.trace[3]['support_contacts']['feet_ground_fz_N']=[0,0];self.wr('execution/trace.json',self.trace);self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_nonfinite_support_fails_closed(self):
        self.trace[1]['support_contacts']['feet_ground_fz_N']=[float('nan'),100.];self.wr('execution/trace.json',self.trace);x=evaluate(self.p);self.assertFalse(x['diagnostic_accepted']);self.assertTrue(x['errors'])
    def test_stale_safety_report_rejected(self):
        self.wr('execution/safety_meta.json',{'modified':True});self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_modified_profile_cannot_raise_ceiling(self):
        profile=json.loads((self.p/'profile.json').read_text());profile['controller']['elbow_upper_rad']=2.1;self.wr('profile.json',profile);self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_native_full_flag_cannot_pass_diagnostic(self):
        self.wr('outcome.json',{'task_success':True,'evidence_status':'witnessed_full','errors':[]});self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
if __name__=='__main__':unittest.main()
