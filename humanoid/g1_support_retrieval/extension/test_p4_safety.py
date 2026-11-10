"""Synthetic counterexamples for P4 original-rule adapter; no physics runs."""
import copy
import unittest
import numpy as np
from .verify_p4_safety import evaluate_arrays, rules


class SafetyAdapterTests(unittest.TestCase):
    def setUp(self):
        n=251;k=1
        self.meta=dict(control_dt=.02,object_ids=['target'],object_present=[True],object_sizes_m=[[.45,.5,.18]],target_index=0,joint_names=['waist_pitch_joint']+[f'joint_{j}' for j in range(42)],joint_effort_limits=[50.]*43,joint_lower=[-1.]*43,joint_upper=[1.]*43,robot_mass_kg=rules.ROBOT_MASS_KG,contact_mapping={'source':'synthetic-test-only'},torque_provenance={'quantity':'signed_actual_joint_force','source':'robot.get_dofs_control_force','sampling':'same_state_time_as_q'})
        self.act={k:self.meta[k] for k in ('joint_names','joint_effort_limits','joint_lower','joint_upper')}
        self.act.update(samples=(n-1)*4,physics_dt=.005)
        a=self.a={'t':np.arange(n)*.02,'root_pos':np.tile([1.,0.,.75],(n,1)),'root_quat':np.tile([1.,0.,0.,0.],(n,1)),'root_vel':np.zeros((n,3)),'root_angvel':np.zeros((n,3)),'foot_bottom_m':np.zeros((n,2)),'feet_floor_fz':np.full((n,2),rules.BODY_WEIGHT_N/2),'object_pos':np.tile([[[2.3,0,.09]]],(n,1,1)),'object_quat':np.tile([[[1.,0,0,0]]],(n,1,1)),'foot_object_fz':np.zeros((n,k,2)),'hand_object_force':np.zeros((n,k,2)),'body_object_force':np.zeros((n,k)),'foot_cabinet_force':np.zeros((n,2)),'hand_cabinet_force':np.zeros((n,2)),'body_cabinet_force':np.zeros(n),'body_ground_force':np.zeros(n),'q':np.zeros((n,43)),'tau':np.zeros((n,43)),'invalid_mask':np.zeros(n,dtype=bool)}
        self.trace=[dict(time=float(t),root=a['root_pos'][j].tolist(),box=[2.3,0,.09],bottom=0.,box_speed=0.) for j,t in enumerate(a['t'])]
    def result(self):return evaluate_arrays(self.a,self.meta,self.trace,self.act)
    def kinds(self):return [e['kind'] for e in self.result()['original_five_rules']['events']]
    def test_ordinary_stance_passes_original_rules(self):self.assertTrue(self.result()['safety_passed'])
    def test_stationary_inverted_body_fails_despite_zero_speed(self):
        self.a['root_quat'][:]=[0,1,0,0]
        self.assertIn('fall',self.kinds())
    def test_body_ground_support_is_not_invented_feet_only_failure(self):
        self.a['feet_floor_fz'][:]=0;self.a['body_ground_force'][:]=rules.BODY_WEIGHT_N
        self.assertNotIn('near_fall_unsupported',self.kinds())
    def test_no_other_support_causes_unsupported_event(self):
        self.a['feet_floor_fz'][:]=0
        self.assertIn('near_fall_unsupported',self.kinds())
    def test_torque_saturation_uses_signed_actual_series(self):
        self.a['tau'][:,0]=-50
        self.assertIn('torque_saturation',self.kinds())
    def test_outward_limit_push_is_detected(self):
        self.a['q'][:,1]=.99;self.a['tau'][:,1]=30
        self.assertIn('joint_limit_push',self.kinds())
    def test_cabinet_nonhand_load_detected(self):
        self.a['body_cabinet_force'][:]=100
        self.assertIn('cabinet_climb',self.kinds())
    def test_high_release_and_throw_are_not_ignored(self):
        self.a['hand_object_force'][:100,0,:]=5
        self.trace[100]['bottom']=1.;self.trace[100]['box_speed']=1.5
        self.assertIn('high_release',self.kinds());self.assertIn('throw_release',self.kinds())
    def test_missing_force_channel_cannot_be_zero_filled(self):
        del self.a['foot_cabinet_force']
        with self.assertRaisesRegex(ValueError,'missing safety channels'):self.result()
    def test_missing_actual_torque_cannot_be_reference_command(self):
        del self.a['tau']
        with self.assertRaisesRegex(ValueError,'missing safety channels'):self.result()
    def test_invalid_mask_remains_unknown(self):
        self.a['invalid_mask'][50]=True
        self.assertEqual(self.result()['status'],'unknown')
    def test_trimmed_timeline_rejected(self):
        self.a['t']+=1
        for row in self.trace:row['time']+=1
        with self.assertRaisesRegex(ValueError,'original t0'):self.result()
    def test_incomplete_physics_coverage_rejected(self):
        self.act['samples']+=4
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):self.result()
    def test_reference_torque_provenance_rejected(self):
        self.meta['torque_provenance']['quantity']='unclipped_reference_torque'
        with self.assertRaisesRegex(ValueError,'actual torque provenance'):self.result()
    def test_parked_collidable_object_cannot_skip_standing_support(self):
        self.meta['object_present'][0]=False;self.a['foot_object_fz'][:]=200
        with self.assertRaisesRegex(ValueError,'physical object presence'):self.result()
    def test_source_limits_mismatch_rejected(self):
        self.act=copy.deepcopy(self.act);self.act['joint_upper'][0]=2
        with self.assertRaisesRegex(ValueError,'identity mismatch'):self.result()
if __name__=='__main__':unittest.main()
