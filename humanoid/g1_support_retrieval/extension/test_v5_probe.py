"""Synthetic v5 diagnostic reader gates; macro predicates tested separately."""
import json,unittest
from unittest.mock import patch
from .test_v4_probe import V4ProbeTests
from .verify_v5_probe import evaluate

class V5ProbeTests(unittest.TestCase):
    def setUp(self):
        V4ProbeTests.setUp(self)
        self.patch=patch('humanoid.g1_support_retrieval.extension.map_observed_macros.build',return_value={'all_macro_effects_measured':True,'command_coverage_complete':True,'declared_macro_sequence_matches':True,'prospectively_declared_macro_refinement_complete':False,'macros':[]})
        self.mock=self.patch.start()
        old='humanoid/g1_support_retrieval/extension/v4-probe-acceptance.json';new=old.replace('v4','v5')
        self.wr('source_snapshot/'+new,json.loads((self.p/'source_snapshot'/old).read_text()))
        (self.p/'frozen_documents/v5-probe-acceptance.json').write_bytes((self.p/'source_snapshot'/new).read_bytes())
        contract=json.loads((self.p/'refinement-contract.json').read_text());contract['frozen_documents']=[{'path':new,'sha256':self.sha(self.p/'source_snapshot'/new)}];self.wr('refinement-contract.json',contract)
        self.wr('refinement_contract_binding.json',{'before_first_physics':True,'contract_sha256':self.sha(self.p/'refinement-contract.json')})
        self.wr('execution/command_trace.json',[{'joint_position_target':[0.]*43}]*4)
        self.trace[1]['phase']='settle_release';self.trace[2]['phase']='hold_both';self.wr('execution/trace.json',self.trace)
        safety=json.loads((self.p/'original_safety_independent.json').read_text());safety['artifact_hashes']['execution/trace.json']=self.sha(self.p/'execution/trace.json');self.wr('original_safety_independent.json',safety)
        self.wr('skill_refinement-v5-probe.json',{'artifact_hashes':{f:self.sha(self.p/f) for f in ['profile.json','execution/trace.json','execution/command_trace.json','execution/joint_trace.npz','execution/actuator_audit.json','execution/result.json']}})
    def save(self):V4ProbeTests.save(self)
    def tearDown(self):self.patch.stop();self.tmp.cleanup()
    def test_clean_diagnostic_stays_not_full(self):
        out=evaluate(self.p);self.assertTrue(out['diagnostic_accepted'],out);self.assertFalse(out['full_witness'])
    def test_macro_effect_failure_not_hidden_by_native_goal(self):
        self.mock.return_value['all_macro_effects_measured']=False
        self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_stale_semantic_input_is_rejected(self):
        self.wr('execution/result.json',{'status':'plan_completed','changed':True})
        self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_incomplete_commands_fail(self):
        self.data=self.data[:-1];self.save();self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_bad_safety_or_native_full_never_pass(self):
        self.wr('outcome.json',{'task_success':True,'evidence_status':'witnessed_full','errors':[]})
        self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_terminal_reference_change_rejected(self):
        commands=json.loads((self.p/'execution/command_trace.json').read_text());commands[-1]['joint_position_target'][0]=.1;self.wr('execution/command_trace.json',commands)
        self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
    def test_terminal_finger_reference_neutral_rejected(self):
        self.data[-1,4]=0;self.save();self.assertFalse(evaluate(self.p)['diagnostic_accepted'])
if __name__=='__main__':unittest.main()
