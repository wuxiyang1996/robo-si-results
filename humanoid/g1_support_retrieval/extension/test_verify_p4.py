"""Negative controls for evidence validation; these are not physics runs."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from humanoid.g1_support_retrieval.extension.verify_p4 import evaluate, mapping, physical_command_errors

class P4EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((Path(__file__).parent/"p4-development.json").read_text())
        self.result = {"status":"plan_completed", "box_size":[.45,.50,.18], "box_mass_kg":5., "box_floor_friction":.5,"object_attachment":False,"runtime_pose_writes":False,"applied_root_wrench":False}
        self.trace = []
        for i in range(201):
            x = 2.3 + .36*min(i/50, 1)
            self.trace.append(dict(time=i*.02, phase="Push_both" if i<50 else "Hold_both",
                box=[x,0,.09], box_quat=[1,0,0,0], box_speed=.36 if i<50 else 0,
                box_angular_speed=0, tilt_deg=0, root_linear_velocity=[0,0,0],
                root_angular_velocity=[0,0,0], forces={}, contact_links=[], body_contact_N=0,
                support_contacts=dict(target_ground_fz_N=49.05,feet_ground_fz_N=[200,200],body_ground_force_N=0)))
        self.commands = [dict(time=i*.02,joint_position_target=[0]*43,leg_position_target=[0]*12,reference_velocity=[0]*43,leg_torque=None) for i in range(200)]
        self.joints = np.zeros((201,50))
        self.actuator = dict(samples=800,max_position_overshoot=0,max_speed_ratio=.5,max_effort_ratio=.5)
    def check(self):
        return evaluate(self.profile,self.result,self.trace,self.commands,self.joints,self.actuator)
    def test_diagnostic_cannot_be_complete_even_if_goal_met(self):
        self.profile["diagnostic_only"] = True
        result = self.check()
        self.assertTrue(result["physical_goal_met"])
        self.assertFalse(result["task_success"])
        self.assertIn("diagnostic_or_partial_start_never_full_witness",result["errors"])
    def test_partial_start_cannot_be_complete(self):
        self.profile["debug_start"] = "old late trajectory"
        self.assertFalse(self.check()["task_success"])
    def test_complete_legal_delivery(self):
        self.assertTrue(self.check()["task_success"])
    def test_center_inside_but_corner_outside(self):
        for row in self.trace[50:]: row["box"][0] = 2.9
        self.assertFalse(self.check()["task_success"])
    def test_missing_endpoint_rejected(self):
        self.trace.pop()
        self.assertIn("state_command_coverage_mismatch",self.check()["errors"])
    def test_no_independent_support_rejected(self):
        for row in self.trace[50:]: row["support_contacts"]["target_ground_fz_N"] = 0
        self.assertFalse(self.check()["task_success"])
    def test_still_held_rejected(self):
        for row in self.trace[50:]: row["forces"] = {"left_palm":[2,0,0]}
        self.assertFalse(self.check()["task_success"])
    def test_falling_robot_rejected(self):
        for row in self.trace[50:]: row["root_angular_velocity"]=[.2,0,0]
        self.assertFalse(self.check()["task_success"])
    def test_dwell_reset_on_one_bad_frame(self):
        self.trace[-10]["box_speed"] = .1
        self.assertFalse(self.check()["task_success"])
    def test_actuator_violation_rejected(self):
        self.actuator["max_effort_ratio"] = 1.2
        self.assertIn("actuator_max_effort_ratio",self.check()["errors"])
    def test_missing_physics_sample_rejected(self):
        self.actuator["samples"] -= 1
        self.assertIn("physics_actuator_coverage_mismatch",self.check()["errors"])
    def test_cancelled_contact_force_does_not_prove_release(self):
        for row in self.trace[50:]: row["contact_links"]=["left_hand_index_2_link"]
        self.assertFalse(self.check()["task_success"])
    def test_legitimate_goal_does_not_require_expert_sequence(self):
        self.result["status"] = "alternative_legal_route_complete"
        self.assertTrue(self.check()["task_success"])
    def test_wrong_mass_binding_rejected(self):
        self.result["box_mass_kg"] = 1
        self.assertFalse(self.check()["task_success"])
    def test_nonfinite_command_rejected(self):
        self.commands[0]["joint_position_target"]=[float("nan")]*43
        self.assertFalse(self.check()["task_success"])
    def test_wrong_joint_shape_rejected(self):
        self.joints = np.zeros((201,1))
        self.assertFalse(self.check()["task_success"])
    def test_pose_write_flag_rejected(self):
        self.result["runtime_pose_writes"]=True
        self.assertFalse(self.check()["task_success"])
    def test_safe_nonhand_push_is_not_hidden_task_failure(self):
        self.trace[10]["body_contact_N"]=20
        self.assertTrue(self.check()["task_success"])
    def test_nonfoot_support_is_not_hidden_route_failure(self):
        for row in self.trace[50:]:
            row["support_contacts"]["body_ground_force_N"]=400
            row["support_contacts"]["feet_ground_fz_N"]=[0,0]
        self.assertTrue(self.check()["task_success"])
        self.assertFalse(self.check()["terminal_reference_standing"])
    def test_published_one_milliradian_tolerance_is_preserved(self):
        self.actuator["max_position_overshoot"]=.0011
        self.assertFalse(self.check()["task_success"])
        self.assertTrue(self.check()["physical_goal_met"])
    def test_mapping_covers_all_measured_intervals(self):
        mapped = mapping(self.trace,self.commands)["segments"]
        self.assertEqual(mapped[0]["start_state_index"],0)
        self.assertEqual(mapped[-1]["end_state_index"],200)
        self.assertTrue(all(a["end_state_index"]==b["start_state_index"] for a,b in zip(mapped,mapped[1:])))

class ExactCommandTests(unittest.TestCase):
    def setUp(self):
        self.names=[f"joint_{i}" for i in range(43)]
        self.columns=["time","leg_force_mode"]+["position_target:"+n for n in self.names]+["applied_leg_force:"+n for n in self.names[:12]]+["leg_force_lower:"+n for n in self.names[:12]]+["leg_force_upper:"+n for n in self.names[:12]]
        self.data=np.zeros((4,81)); self.data[:,0]=np.arange(4)*.005
        self.data[:,1]=1; self.data[:,57:69]=-10; self.data[:,69:81]=10
    def check(self): return physical_command_errors(self.data,self.columns,self.names,1)
    def test_valid_exact_command(self): self.assertEqual(self.check(),[])
    def test_force_above_bound(self):
        self.data[1,45]=11
        self.assertIn("applied_command_force_exceeds_bounds",self.check())
    def test_inverted_bound(self):
        self.data[1,57]=20
        self.assertIn("inverted_command_force_bounds",self.check())
    def test_invalid_mode(self):
        self.data[1,1]=2
        self.assertIn("invalid_leg_control_mode",self.check())
    def test_reordered_columns(self):
        self.columns[2],self.columns[3]=self.columns[3],self.columns[2]
        self.assertIn("physics_command_column_mismatch",self.check())
    def test_missing_physics_command(self):
        self.data=self.data[:-1]
        self.assertIn("exact_physics_command_coverage_mismatch",self.check())

if __name__ == "__main__": unittest.main()
