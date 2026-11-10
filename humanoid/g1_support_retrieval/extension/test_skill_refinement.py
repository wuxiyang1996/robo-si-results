"""Independent semantic counterexamples. Synthetic fixtures, never physics witnesses."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from .verify_skill_refinement import CONTRACT, combine, segment_checks, key_state, internal_step_checks, internal_step_segments, actuator_check


class SkillRefinementTests(unittest.TestCase):
    def setUp(self):
        self.profile=json.loads((Path(__file__).parent/'p4-development.json').read_text())
        self.thresholds=CONTRACT['thresholds']
        self.a=dict(phase='sample',time=1.,box=[2.3,0,.09],box_quat=[1,0,0,0],bottom=0.,box_speed=0.,body_contact_N=0.,support_contacts=dict(target_ground_fz_N=49.05,feet_ground_fz_N=[200,200],body_ground_force_N=0.),push_normal=dict(left=2.,right=2.),forces={},contact_links=[],mcp_meas=[[2.,.15,.12],[2.,-.15,.12]],mcp_cmd=[[2.,.15,.12],[2.,-.15,.12]],feet_meas=[[1.6,.12,.035],[1.6,-.12,.035]],root=[1.6,0,.46],root_linear_velocity=[0,0,0],root_angular_velocity=[0,0,0])
        self.b=copy.deepcopy(self.a);self.b['time']=1.02

    def state(self,skill,rows=None,**kwargs):
        return combine(segment_checks(skill,rows or [self.a,self.b],self.profile,self.thresholds,**kwargs))

    def contact(self,row):
        row.update(forces={'left_palm':[-2,0,0],'right_palm':[-2,0,0]},contact_links=['left_wrist_yaw_link','right_wrist_yaw_link'])

    def test_original_one_milliradian_limit_is_enforced(self):
        a=dict(samples=4,max_position_overshoot=.001,max_speed_ratio=1.,max_effort_ratio=1.)
        self.assertEqual(actuator_check(a,1,self.profile,self.thresholds)['status'],'passed')
        a['max_position_overshoot']=.004584531784
        self.assertEqual(actuator_check(a,1,self.profile,self.thresholds)['status'],'failed')

    def test_contact_needs_raw_force_and_identity_not_filtered_residue(self):
        self.assertEqual(self.state('touch'),'failed')
        for r in (self.a,self.b):self.contact(r)
        self.assertEqual(self.state('touch'),'passed')
        for r in (self.a,self.b):r['contact_links']=['left_ankle_roll_link','right_ankle_roll_link']
        self.assertEqual(self.state('touch'),'failed')

    def test_push_phase_label_without_actual_progress_fails(self):
        for r in (self.a,self.b):self.contact(r);r['phase']='push_both'
        self.assertEqual(self.state('push'),'failed')
        self.b['box'][0]+=.1
        self.assertEqual(self.state('push'),'passed')

    def test_retreat_net_cancellation_does_not_prove_release(self):
        self.b['contact_links']=['left_hand_index_2_link']
        self.b['forces']={'left_finger':[0,0,0]}
        self.assertEqual(self.state('retreat'),'failed')

    def test_foot_drag_is_not_two_footfalls(self):
        self.b['feet_meas'][0][0]+=.12;self.b['feet_meas'][1][0]+=.12
        self.assertEqual(self.state('planned_steps'),'failed')

    def test_observed_swings_with_opposite_support_and_landing(self):
        rows=[copy.deepcopy(self.a) for _ in range(5)]
        for i,r in enumerate(rows):r['time']=1+i*.02
        rows[1]['feet_meas'][0]=[1.66,.12,.085];rows[1]['support_contacts']['feet_ground_fz_N']=[0,400]
        for r in rows[2:]:r['feet_meas'][0][0]=1.72
        rows[3]['feet_meas'][1]=[1.66,-.12,.085];rows[3]['support_contacts']['feet_ground_fz_N']=[400,0]
        rows[4]['feet_meas'][1][0]=1.72
        self.assertEqual(self.state('planned_steps',rows),'passed')

    def test_final_return_does_not_require_unused_future_touch(self):
        self.assertEqual(self.state('return_hands'),'unknown')
        self.assertEqual(self.state('return_hands',final_return=True),'passed')
        self.b['mcp_meas'][0][0]=2.2
        self.assertEqual(self.state('return_hands',final_return=True),'failed')

    def test_missing_support_is_unknown_with_other_contact_evidence(self):
        for r in (self.a,self.b):self.contact(r)
        del self.b['support_contacts']
        self.assertEqual(self.state('touch'),'unknown')

    def test_terminal_inherited_mcp_is_not_new_measurement(self):
        self.b['phase']='terminal'
        self.assertEqual(self.state('return_hands',final_return=True),'unknown')
        self.assertEqual(self.state('hold'),'passed')
        self.assertIn('mcp_meas',key_state(self.b,[0]*50)['field_provenance']['inherited_not_fresh_terminal_measurements'])


    def test_transfer_is_verified_by_measured_support_and_next_lift(self):
        end=copy.deepcopy(self.b);end['time']=1.04
        end['feet_meas'][0][2]+=.05;end['support_contacts']['feet_ground_fz_N']=[0,400]
        checks=internal_step_checks('transfer_right',[self.a,self.b],self.thresholds,'lift_left',[self.b,end])
        self.assertEqual(combine(checks),'passed')
        self.assertTrue(any(c['status']=='unknown' and c.get('required_for_this_run') is False for c in checks))
        no_lift=internal_step_checks('transfer_right',[self.a,self.b],self.thresholds,'lift_left',[self.b,self.b])
        self.assertEqual(combine(no_lift),'failed')

    def test_internal_actions_use_observed_labels_and_shared_indices(self):
        rows=[copy.deepcopy(self.a) for _ in range(5)]
        for i,r in enumerate(rows):
            r['time']=1+i*.02;r['step_label']=['transfer_right','transfer_right','lift_left','lift_left',None][i]
        rows[-1]['feet_meas'][0][2]+=.05;rows[-1]['support_contacts']['feet_ground_fz_N']=[0,400]
        segments=internal_step_segments(rows,np.zeros((5,50)),0,4,'L004','H3',.02,np.ones(43),self.thresholds)
        self.assertEqual([s['range_half_open'] for s in segments],[[0,2],[2,4]])
        self.assertEqual(segments[0]['exit'],segments[1]['entry'])

    def test_settle_requires_measured_full_second_not_phase_label(self):
        rows=[copy.deepcopy(self.a) for _ in range(61)]
        for i,r in enumerate(rows):r.update(time=1.+i*.02,box_angular_speed=0.)
        self.assertEqual(self.state('settle_release',rows),'passed')
        rows[-20]['root_linear_velocity']=[.031,0,0]
        self.assertEqual(self.state('settle_release',rows),'failed')

    def test_settle_never_waives_transient_support_or_release(self):
        rows=[copy.deepcopy(self.a) for _ in range(61)]
        for i,r in enumerate(rows):r.update(time=1.+i*.02,box_angular_speed=0.)
        rows[2]['support_contacts']['feet_ground_fz_N']=[0,0]
        self.assertEqual(self.state('settle_release',rows),'failed')
        rows[2]['support_contacts']['feet_ground_fz_N']=[200,200]
        rows[2]['contact_links']=['left_hand_index_2_link']
        self.assertEqual(self.state('settle_release',rows),'failed')
        rows[2]['contact_links']=[]
        del rows[-1]['box_angular_speed']
        self.assertEqual(self.state('settle_release',rows),'unknown')

    def test_crouch_macro_topology_does_not_invent_last_footfall(self):
        from .map_observed_macros import declared_sequence
        self.profile['controller'].update(cycles=3,final_mode='crouch_hold')
        self.assertEqual(declared_sequence(self.profile),['observed_approach','observed_ground_transport','observed_foot_reposition','observed_ground_transport','observed_foot_reposition','observed_ground_transport','declared_release_and_crouch_hold'])
        self.profile['controller']['cycles']=1
        self.assertEqual(declared_sequence(self.profile),['observed_approach','observed_ground_transport','declared_release_and_crouch_hold'])

if __name__=='__main__':unittest.main()
