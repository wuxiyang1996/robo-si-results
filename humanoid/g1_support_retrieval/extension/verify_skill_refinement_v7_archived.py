"""Measured, task-specific P4 skill refinement review; never a goal scorer.

Save an immutable development audit rule revision (jobs may already be running):
  python -m humanoid.g1_support_retrieval.extension.verify_skill_refinement freeze --out CONTRACT.json
Review a run without modifying its physical verdict:
  python -m humanoid.g1_support_retrieval.extension.verify_skill_refinement review RUN --contract CONTRACT.json

Phase names only choose which declared author skill to review. Every result comes
from measured states, forces, action intervals and frozen limits, never the name or
controller's 'done' flag. Missing evidence is unknown, measured contradiction failed.
This reviewer cannot certify hidden collision-free envelopes or COM margins absent
from the recorder. A failed skill refinement never invalidates a legal task goal.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTRACT = {
    "schema": "h1-p4-measured-skill-contract/1",
    "version": "2026-10-27.v7",
    "task_id": "H1S-07.P4",
    "role": "author-side development/post-job-start measured refinement audit; not prospectively predeclared benchmark acceptance or success requirements",
    "timing_scope": "Developed after physical jobs started, with partial progress logs visible; original task D/profile/budgets remain unchanged. Revisions and hashes are retained. No claim these semantic audit rules were declared before the three runs.",
    "thresholds": {
        "touch_normal_N": 1.0,
        "ground_contact_N": 1.0,
        "hand_release_net_force_N": 0.5,
        "foot_lift_above_initial_m": 0.006,
        "numeric_position_epsilon_m": 1e-6,
        "joint_difference_epsilon_rad": 1e-6,
        "max_body_collision_N": 10.0,
    },
    "threshold_provenance": {
        "touch_normal_N": "run_push.Touch.step uses >1 N filtered contact threshold; reviewer requires current raw force and contact identity at the same threshold to avoid filter residue",
        "ground_contact_N": "P4 terminal verifier uses foot ground fz >1 N; same contact detection threshold",
        "hand_release_net_force_N": "P4 physical goal verifier; also requires zero robot-target contact links",
        "foot_lift_above_initial_m": "existing StepFoot landing tolerance 0.006 m; used to distinguish measured swing from ground-level dragging, not expected 0.05 m lift",
        "numeric_position_epsilon_m": "numerical resolution only; no nominal stroke percentage chosen from outcomes",
        "joint_difference_epsilon_rad": "floating point tolerance on necessary delta-q <= frozen velocity limit * dt",
        "max_body_collision_N": "existing expert-controller collision diagnostic threshold; author reference skill only, not a hand-only public task rule",
    },
    "predicate_definitions": {
        "touch": "Measured raw both-side contact force projected onto rear normal >1 N with matching contact links at least once each, simultaneous contact at exit, target ground contact and ground-height bound, both feet ground-supported at exit.",
        "push": "Positive measured target displacement toward declared D, real hand-target contact during transport, target continuously grounded within profile gap, foot support, endpoint target speed <=0.02 m/s as existing Push completion condition. Nominal stroke and contact cap are diagnostics, not hidden goal rules.",
        "retreat": "No target contact links and low contact force at exit; measured hand-to-box relative displacement retained. Both feet supported at entry/exit.",
        "planned_steps": "Both feet have measured forward displacement, each has an observed >6 mm rise with unloaded swing foot and supported opposite foot; endpoint has both feet grounded. Entire segment has at least one measured ground-supported foot.",
        "return_hands": "Exit has released hands and two-foot support. For a middle cycle, subsequent measured Touch in the same continuous run establishes next-contact reachability. For final release preparation, check actual MCP points behind the box rear plane and released supported posture; do not require unused future contact capability. Truncated/unknown continuation remains unknown. Measured command tracking residual remains diagnostic without an invented tolerance.",
        "approach": "Measured end posture has two-foot support and no hard body collision. Sensor target identification is not established by this privileged expert.",
        "clear_hands": "Measured upward/backward movement of both hands relative to target and no target contact at exit.",
        "stand_up": "Measured pelvis rise, end two-foot support and released hands. Whole-body collision/COM margins require separate evidence.",
        "hold": "Measured base speeds satisfy profile terminal limits and hands remain released; target terminal success separately recomputed by physical goal verifier.",
        "recenter": "Planner bookkeeping only; not credited as a separate physical skill. Shared measured boundary recorded, COM recentering not observable in current trace.",
        "planned_steps_internal_actions": "Split only observed step_label runs. Lift/advance/land/rise/lower get measured displacement and real support/contact checks. transfer/center use measured support load distribution and the next actual swing/lowering as the executed-skill witness; exact controller COM target remains an explicitly non-gating unknown because trace lacks COM. Missing labels remain unknown. Each interval keeps actual shared boundary and issued-command range.",
        "joint_continuity": "Actual full qpos joint order read from frozen MJCF, finite per-step differences bounded by frozen actuator velocity limits times control_dt; actual actuator summary covers every physics step and stays within declared limits.",
        "transitions": "Adjacent segments share the exact recorded boundary index/state/qpos; measured base velocity, support and contact topology retained. No arbitrary-start composition claim.",
        "terminal_field_provenance": "v2 terminal row inherits mcp_meas, mcp_cmd, push_normal and several controller fields from the previous control sample. These are not fresh terminal measurements. Any predicate requiring terminal MCP is unknown; original raw row is retained with field-level provenance. Root/box pose, velocity, support/contact and feet were remeasured.",
        "terminal": "Independently recompute P4 whole-target-D, release, support, stable dwell and actuator predicates through verify_p4.evaluate; preserve runtime identity verdict separately.",
    },
    "unmeasured_not_certified": ["center-of-mass/support-polygon stability margin", "all-body clearance and penetration depth", "continuous contact force between control-rate samples", "sensor-only target identification", "arbitrary-start skill applicability"],
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def freeze(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError("Never overwrite a frozen semantic contract")
    document = dict(CONTRACT, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                    reviewer_source_sha256=sha(__file__), profile_sha256=sha(HERE / "p4-development.json"), profile_snapshot=read(HERE / "p4-development.json"))
    write(path, document)
    return document


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError("Missing/nonfinite numeric measurement")
    return float(value)


def array(value, shape=None):
    v = np.asarray(value, dtype=float)
    if (shape is not None and v.shape != shape) or not np.isfinite(v).all():
        raise ValueError("Missing/nonfinite/mismatched measured array")
    return v


def check(name, predicate, metrics=None, explanation=None):
    try:
        value = predicate()
        status = "unknown" if value is None else "passed" if bool(value) else "failed"
        return dict(predicate=name, status=status, metrics={} if metrics is None else metrics(), explanation=explanation)
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        return dict(predicate=name, status="unknown", reason=f"{type(exc).__name__}: {exc}", explanation=explanation)


def combine(checks):
    states = [c["status"] for c in checks if c.get("required_for_this_run",True)]
    return "failed" if "failed" in states else "unknown" if "unknown" in states else "passed"


def phase_ranges(trace, count):
    out=[]
    start=0
    while start<count:
        phase=trace[start]["phase"]
        stop=start+1
        while stop<count and trace[stop]["phase"]==phase:
            stop+=1
        out.append((phase,start,stop))
        start=stop
    return out


def root_metrics(row):
    return dict(linear_speed_m_s=float(np.linalg.norm(array(row["root_linear_velocity"],(3,)))),
                angular_speed_rad_s=float(np.linalg.norm(array(row["root_angular_velocity"],(3,)))))


def released(row, th):
    if not isinstance(row["contact_links"], list) or not isinstance(row["forces"], dict):
        raise ValueError("Missing contact identity/force collection")
    return not row["contact_links"] and all(np.linalg.norm(array(f,(3,))) <= th["hand_release_net_force_N"] for f in row["forces"].values())


def raw_hand_normal(row, side):
    w,x,y,z=array(row["box_quat"],(4,))
    normal=-np.array([1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w)])
    forces=row["forces"]
    if not isinstance(forces,dict): raise ValueError("Missing raw contact force groups")
    return float(sum((array(forces.get(side+"_"+part,[0,0,0]),(3,)) for part in ("thumb","finger","palm")),np.zeros(3))@normal)


def hand_contact(row,side,th):
    links=row["contact_links"]
    if not isinstance(links,list): raise ValueError("Missing contact link identities")
    return any(str(name).startswith(side+"_hand_") or name==side+"_wrist_yaw_link" for name in links) and raw_hand_normal(row,side)>th["touch_normal_N"]


def foot_forces(row):
    return array(row["support_contacts"]["feet_ground_fz_N"], (2,))


def double_support(row, th):
    return bool((foot_forces(row)>th["ground_contact_N"]).all())


def grounded(row, profile, th):
    return (number(row["support_contacts"]["target_ground_fz_N"])>th["ground_contact_N"] and
            abs(number(row["bottom"]))<=profile["goal"]["max_ground_gap_m"])


def key_state(row, qpos):
    # Exact original row is retained, not a rounded/reconstructed endpoint.
    terminal = row.get("phase")=="terminal"
    return dict(raw_state=row, measured_full_qpos=np.asarray(qpos).tolist(),
                field_provenance={"raw_row_preserved": True,
                    "terminal_sample": terminal,
                    "inherited_not_fresh_terminal_measurements": ["mcp_meas","mcp_cmd","push_normal","feet_cmd","support_legs","orientation_error","leg_control","step_label"] if terminal else [],
                    "fresh_terminal_measurements": ["box","box_quat","box_speed","box_angular_speed","tilt_deg","bottom","root","root_linear_velocity","root_angular_velocity","support_contacts","contact_links","forces","body_contact_N","feet_meas"] if terminal else [],
                    "measured_full_qpos_source": "joint_trace.npz, exact same boundary index"})


def joint_order(run, actuator):
    model=run/"source_snapshot/humanoid/g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml"
    body=ET.parse(model).getroot().find("worldbody")
    names=[j.attrib["name"] for j in body.iter("joint")]
    recorded=actuator["joint_names"]
    if len(names)!=43 or len(set(names))!=43 or set(names)!=set(recorded):
        raise ValueError("Cannot bind full-qpos order to frozen hardware joint names")
    indices=[recorded.index(n) for n in names]
    return names, array(actuator["joint_velocity_limits"],(43,))[indices]


def segment_checks(kind, rows, profile, th, subsequent_touch=None, final_return=False):
    a,b=rows[0],rows[-1]
    checks=[]
    add=lambda name,fn,metrics=None,explanation=None: checks.append(check(name,fn,metrics,explanation))
    add("no_measured_reference_body_collision",lambda: all(number(r["body_contact_N"])<=th["max_body_collision_N"] and number(r["support_contacts"]["body_ground_force_N"])<=th["max_body_collision_N"] for r in rows))
    # Initial t=0 precedes contact solver evaluation and is not contact evidence.
    sensed=[r for r in rows if number(r["time"])>0]
    add("at_least_one_ground_support_throughout",lambda: bool(sensed) and all((foot_forces(r)>th["ground_contact_N"]).any() for r in sensed))
    add("target_ground_support_throughout",lambda: bool(sensed) and all(grounded(r,profile,th) for r in sensed))
    if kind in ("touch","push","retreat","return_hands","approach","clear_hands","stand_up","hold"):
        add("two_foot_exit_support",lambda: double_support(b,th))
    if kind in ("touch","push","retreat","return_hands"):
        add("two_foot_entry_support",lambda: double_support(a,th))
    if kind=="touch":
        add("both_hand_contacts_established",lambda: all(any(hand_contact(r,side,th) for r in rows) for side in ("left","right")))
        add("simultaneous_contact_at_exit",lambda: all(hand_contact(b,s,th) for s in ("left","right")),lambda:{"exit_raw_hand_normal_N":{side:raw_hand_normal(b,side) for side in ("left","right")},"filtered_controller_signal_N":b["push_normal"]})
    elif kind=="push":
        add("both_feet_planted_during_push",lambda: all(double_support(r,th) for r in rows))
        displacement=lambda: array(b["box"],(3,))[:2]-array(a["box"],(3,))[:2]
        direction=lambda: array(profile["goal"]["center_xy_m"],(2,))-array(a["box"],(3,))[:2]
        progress=lambda: float(displacement()@direction()/max(float(np.linalg.norm(direction())),1e-12))
        add("target_progress_toward_D",lambda: progress()>th["numeric_position_epsilon_m"],lambda:{"signed_progress_m":progress(),"displacement_xy_m":displacement().tolist(),"nominal_reference_stroke_m":profile["controller"]["stroke_m"]})
        add("real_hand_target_contact_observed",lambda: any(hand_contact(r,"left",th) or hand_contact(r,"right",th) for r in rows))
        add("push_settled_endpoint",lambda: number(b["box_speed"])<.02,lambda:{"box_speed_m_s":b["box_speed"]},"0.02 m/s is existing Push.step completion condition, not a new task score rule.")
        add("push_force_measured",lambda: all(np.isfinite(number(v)) for r in rows for v in r["push_normal"].values()),lambda:{"peak_raw_normal_N":max(raw_hand_normal(r,side) for r in rows for side in ("left","right")),"controller_stop_advancing_threshold_N":profile["controller"]["max_push_per_hand_N"]},"Controller threshold is not an instantaneous measured-force cap; no false hard violation inferred.")
    elif kind in ("retreat","return_hands","clear_hands","stand_up","hold"):
        add("released_at_exit",lambda: released(b,th),lambda:{"contact_links":b["contact_links"],"grouped_forces_N":b["forces"]})
        if kind=="retreat":
            add("withdrawal_measurement_available",lambda: array(b["mcp_meas"],(2,3)).shape==(2,3),lambda:{"relative_hand_displacement_m":((array(b["mcp_meas"],(2,3))-array(b["box"],(3,)))-(array(a["mcp_meas"],(2,3))-array(a["box"],(3,)))).tolist()},"Release is the effect; nominal hand withdrawal distance is not a hidden task goal.")
        if kind=="return_hands":
            if final_return:
                def rear_plane_offsets():
                    w,x,y,z=array(b["box_quat"],(4,))
                    forward=np.array([1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w)])
                    return (array(b["mcp_meas"],(2,3))-array(b["box"],(3,)))@forward + profile["target"]["size_m"][0]/2
                add("final_return_MCP_behind_box_rear_plane",lambda:bool((rear_plane_offsets()<=th["numeric_position_epsilon_m"]).all()),lambda:{"signed_MCP_rear_plane_offsets_m":rear_plane_offsets().tolist()},"Context is final release/stand preparation. Only measured MCP points and no-contact state are certified, not a full-hand collision envelope or unused future Touch ability.")
            else:
                add("next_contact_reachable_in_continuous_run",lambda: None if subsequent_touch is None else all(any(hand_contact(r,s,th) for r in subsequent_touch) for s in ("left","right")),explanation="Actual next Touch in this continuous run is the scoped reachability witness; missing continuation remains unknown.")
            add("measured_command_residual_available",lambda: array(b["mcp_cmd"],(2,3)).shape==(2,3),lambda:{"mcp_tracking_error_m":np.linalg.norm(array(b["mcp_meas"],(2,3))-array(b["mcp_cmd"],(2,3)),axis=1).tolist()},"No calibrated endpoint error threshold exists; residual availability is not a tracking-quality pass.")
        if kind=="clear_hands":
            delta=lambda: array(b["mcp_meas"],(2,3))-array(a["mcp_meas"],(2,3))
            add("hands_physically_moved_up_and_back",lambda: bool((delta()[:,2]>th["numeric_position_epsilon_m"]).all() and (delta()[:,0]<-th["numeric_position_epsilon_m"]).all()),lambda:{"world_hand_displacement_m":delta().tolist()})
        if kind=="stand_up":
            add("pelvis_physically_rose",lambda: number(b["root"][2])-number(a["root"][2])>th["numeric_position_epsilon_m"],lambda:{"pelvis_rise_m":number(b["root"][2])-number(a["root"][2])})
        if kind=="hold":
            add("robot_speed_bounds_during_hold",lambda: all(root_metrics(r)["linear_speed_m_s"]<=.03 and root_metrics(r)["angular_speed_rad_s"]<=.05 for r in rows),lambda:{"exit":root_metrics(b)},"Uses frozen P4 terminal thresholds. Intermediate Hold may be unsettled and legitimately fails this stabilization contract.")
    elif kind=="planned_steps":
        add("two_foot_entry_and_exit_support",lambda: double_support(a,th) and double_support(b,th))
        add("hands_released_during_footfalls",lambda: all(released(r,th) for r in rows))
        for leg,side in enumerate(("left","right")):
            displacement=lambda leg=leg: number(b["feet_meas"][leg][0])-number(a["feet_meas"][leg][0])
            lift_samples=lambda leg=leg:[i for i,r in enumerate(rows) if number(r["feet_meas"][leg][2])-number(a["feet_meas"][leg][2])>th["foot_lift_above_initial_m"] and foot_forces(r)[leg]<=th["ground_contact_N"] and foot_forces(r)[1-leg]>th["ground_contact_N"]]
            add(side+"_actual_forward_footfall",lambda displacement=displacement:displacement()>th["numeric_position_epsilon_m"],lambda displacement=displacement:{"forward_displacement_m":displacement(),"nominal_reference_stroke_m":profile["controller"]["stroke_m"]})
            add(side+"_unloaded_swing_and_supported_landing",lambda leg=leg,lift_samples=lift_samples:bool(lift_samples()) and foot_forces(b)[leg]>th["ground_contact_N"],lambda leg=leg,lift_samples=lift_samples:{"first_unloaded_lift_relative_index":lift_samples()[0] if lift_samples() else None,"max_lift_m":max(number(r["feet_meas"][leg][2])-number(a["feet_meas"][leg][2]) for r in rows),"exit_ground_fz_N":float(foot_forces(b)[leg])})
    elif kind=="recenter":
        add("COM_recenter_not_measured",lambda:None,explanation="Reference bookkeeping, not a separately credited physical skill; recorder lacks measured COM.")
    elif kind!="approach":
        add("unrecognized_skill_semantics",lambda:None)
    if b.get("phase")=="terminal":
        stale_mcp_checks={"withdrawal_measurement_available","measured_command_residual_available","hands_physically_moved_up_and_back","final_return_MCP_behind_box_rear_plane"}
        for predicate in checks:
            if predicate["predicate"] in stale_mcp_checks:
                predicate.update(status="unknown", reason="v2 terminal MCP is inherited from preceding pre-step row, not freshly measured; no FK reconstruction claimed")
                predicate["metrics"]={"discarded_stale_terminal_evaluation":True}
    return checks


def internal_step_checks(label, rows, th, next_label=None, next_rows=None):
    a,b=rows[0],rows[-1]
    checks=[]
    add=lambda name,fn,metrics=None,explanation=None: checks.append(check(name,fn,metrics,explanation))
    add("opposite_or_double_ground_support_throughout",lambda:all((foot_forces(r)>th["ground_contact_N"]).any() for r in rows))
    add("released_hands_throughout",lambda:all(released(r,th) for r in rows))
    if label in ("settle","rise","lower","center","transfer_left","transfer_right"):
        add("two_foot_exit_support",lambda:double_support(b,th))
    if label in ("rise","lower"):
        sign=1 if label=="rise" else -1
        add("measured_pelvis_"+label,lambda:sign*(number(b["root"][2])-number(a["root"][2]))>th["numeric_position_epsilon_m"],lambda:{"pelvis_delta_z_m":number(b["root"][2])-number(a["root"][2])})
    elif label=="settle":
        add("settled_base_velocity",lambda:root_metrics(b)["linear_speed_m_s"]<=.03 and root_metrics(b)["angular_speed_rad_s"]<=.05,lambda:root_metrics(b),"Frozen P4 stable-base thresholds; a nominal settle label alone does not prove settling.")
    elif label in ("center","transfer_left","transfer_right"):
        add("measured_load_distribution_available",lambda:True,lambda:{"entry_foot_fz_N":foot_forces(a).tolist(),"exit_foot_fz_N":foot_forces(b).tolist(),"entry_left_load_fraction":float(foot_forces(a)[0]/max(float(foot_forces(a).sum()),1e-12)),"exit_left_load_fraction":float(foot_forces(b)[0]/max(float(foot_forces(b).sum()),1e-12)),"root_displacement_m":(array(b["root"],(3,))-array(a["root"],(3,))).tolist()},"Load split and root displacement are observations, not a substitute for measured COM/support-polygon position.")
        if label.startswith("transfer_"):
            stance=0 if label=="transfer_left" else 1
            swing=1-stance
            expected="lift_right" if stance==0 else "lift_left"
            def supported_next_swing():
                if next_rows is None or next_label!=expected:return None
                return any(number(r["feet_meas"][swing][2])-number(next_rows[0]["feet_meas"][swing][2])>th["foot_lift_above_initial_m"] and foot_forces(r)[swing]<=th["ground_contact_N"] and foot_forces(r)[stance]>th["ground_contact_N"] for r in next_rows)
            add("actual_load_transfer_supports_next_swing",supported_next_swing,lambda:{"designated_stance_foot":"left" if stance==0 else "right","next_observed_step_label":next_label,"next_state_times_s":None if next_rows is None else [next_rows[0]["time"],next_rows[-1]["time"]]},"Actual opposite foot unloading/lifting with designated stance contact verifies this execution's support transition. No controller COM target is inferred from the label.")
        else:
            def supported_next_lowering():
                if next_rows is None or next_label!="lower":return None
                return all(double_support(r,th) and released(r,th) for r in next_rows) and number(next_rows[-1]["root"][2])<number(next_rows[0]["root"][2])-th["numeric_position_epsilon_m"]
            add("double_support_restored_for_next_lowering",supported_next_lowering,lambda:{"next_observed_step_label":next_label},"The concrete completed support/lowering transition is checked. Exact COM centering remains unmeasured.")
        add("exact_controller_COM_target_not_independently_measured",lambda:None,explanation="Non-gating for this executed skill: measured load/contact plus subsequent physical action supplies the scoped witness. COM/support polygon reconstruction is needed for numerical margins or future arbitrary-start applicability.")
        checks[-1]["required_for_this_run"]=False
    elif isinstance(label,str) and label.startswith(("lift_","advance_","land_")) and label.rsplit("_",1)[-1] in ("left","right"):
        side=label.rsplit("_",1)[-1];leg=0 if side=="left" else 1
        delta=lambda:array(b["feet_meas"],(2,3))[leg]-array(a["feet_meas"],(2,3))[leg]
        add("stance_foot_ground_support",lambda:all(foot_forces(r)[1-leg]>th["ground_contact_N"] for r in rows))
        if label.startswith("lift_"):
            add("actual_swing_foot_lift",lambda:delta()[2]>th["foot_lift_above_initial_m"] and foot_forces(b)[leg]<=th["ground_contact_N"],lambda:{"foot_displacement_m":delta().tolist(),"exit_swing_ground_fz_N":float(foot_forces(b)[leg])})
        elif label.startswith("advance_"):
            add("actual_unloaded_forward_swing",lambda:delta()[0]>th["numeric_position_epsilon_m"] and any(foot_forces(r)[leg]<=th["ground_contact_N"] for r in rows),lambda:{"foot_displacement_m":delta().tolist()})
        else:
            add("actual_foot_lowered_and_landed",lambda:delta()[2]<-th["numeric_position_epsilon_m"] and foot_forces(b)[leg]>th["ground_contact_N"],lambda:{"foot_displacement_m":delta().tolist(),"exit_landing_ground_fz_N":float(foot_forces(b)[leg])})
    else:
        add("missing_or_unknown_observed_step_label",lambda:None,explanation="No subaction label is fabricated for unlabelled intervals.")
    return checks


def internal_step_segments(trace, q, start, stop, parent_id, high_level_id, dt, limits, th):
    segments=[];cursor=start
    while cursor<stop:
        label=trace[cursor].get("step_label")
        end=cursor+1
        while end<stop and trace[end].get("step_label")==label:end+=1
        rows=trace[cursor:end+1]
        next_label=trace[end].get("step_label") if end<stop else None
        next_end=end+1
        while next_end<stop and trace[next_end].get("step_label")==next_label:next_end+=1
        next_rows=trace[end:next_end+1] if end<stop else None
        checks=internal_step_checks(label,rows,th,next_label,next_rows)
        checks.append(check("measured_joint_position_continuity",lambda:None if limits is None else bool((np.abs(np.diff(q[cursor:end+1,7:],axis=0))<=limits*dt+th["joint_difference_epsilon_rad"]).all())))
        segments.append(dict(id=f"{parent_id}.{len(segments)+1:02d}",parent_skill_segment=parent_id,high_level_id=high_level_id,observed_step_label=label,range_half_open=[cursor,end],boundary_state_indices=[cursor,end],command_range_half_open=[cursor,end],time_s=[trace[cursor]["time"],trace[end]["time"]],entry=key_state(trace[cursor],q[cursor]),exit=key_state(trace[end],q[end]),checks=checks,status=combine(checks),label_is_measurement=False,label_role="recorded controller intent only; semantic verdict comes from numeric measured predicates"))
        cursor=end
    return segments


def review(run, contract_path):
    run=Path(run).resolve(); contract=read(contract_path)
    if any(contract.get(k)!=v for k,v in CONTRACT.items()):
        raise ValueError("Contract differs from frozen reviewer definitions; use matching reviewer source")
    report=dict(schema="h1-p4-measured-refinement-review/1",task_id="H1S-07.P4",audit_timing=contract["timing_scope"],prospectively_predeclared_acceptance=False,status="unknown",task_success_modified=False,formal_admission=False,human_review="not_signed",contract_sha256=sha(contract_path),reviewer_sha256=sha(__file__),segments=[],transitions=[],errors=[])
    try:
        profile=read(run/"profile.json");trace=read(run/"execution/trace.json");commands=read(run/"execution/command_trace.json");actuator=read(run/"execution/actuator_audit.json");result=read(run/"execution/result.json")
        q=np.load(run/"execution/joint_trace.npz",allow_pickle=False)["measured"]
        if profile != contract.get("profile_snapshot"):
            raise ValueError("Run profile differs from frozen semantic contract profile")
        dt=profile["budget"]["control_dt_s"]
        if len(trace)!=len(commands)+1 or q.shape!=(len(trace),50) or not np.isfinite(q).all() or not np.allclose([r["time"] for r in trace],np.arange(len(trace))*dt,atol=1e-8,rtol=0):
            raise ValueError("Incomplete or discontinuous measured timeline")
        ranges=phase_ranges(trace,len(commands)); th=contract["thresholds"]
        try:
            names,limits=joint_order(run,actuator); order_error=None
        except (OSError,ValueError,KeyError,TypeError,ET.ParseError) as exc:
            names=limits=None;order_error=str(exc)
        for index,(phase,start,stop) in enumerate(ranges):
            kind=phase.rsplit("_",1)[0] if phase.endswith(("_both","_left","_right")) else phase
            rows=trace[start:stop+1]
            next_touch=None
            if kind=="return_hands" and index+1<len(ranges) and ranges[index+1][0].startswith("touch_"):
                _,ns,ne=ranges[index+1];next_touch=trace[ns:ne+1]
            final_return=kind=="return_hands" and index+1<len(ranges) and ranges[index+1][0].startswith(("retreat_","clear_hands_","hold_","recenter_","stand_up_"))
            checks=segment_checks(kind,rows,profile,th,next_touch,final_return)
            checks.append(check("measured_joint_position_continuity",lambda:None if limits is None else bool((np.abs(np.diff(q[start:stop+1,7:],axis=0))<=limits*dt+th["joint_difference_epsilon_rad"]).all()),lambda:{"maximum_measured_joint_increment_rad":float(np.abs(np.diff(q[start:stop+1,7:],axis=0)).max()),"joint_order_source":"frozen MJCF worldbody traversal","binding_error":order_error}))
            # Withdrawal after a push belongs to transport; final withdrawal to delivery.
            hl=("H1_observe_and_establish_push_posture" if kind=="approach" else "H2_ground_supported_transport" if kind in ("touch","push") or (kind=="retreat" and index+1<len(ranges) and ranges[index+1][0].startswith("planned_steps")) else "H3_reposition_for_next_contact" if kind in ("planned_steps","return_hands","step","set_root") and not final_return else "H4_release_and_stabilize_delivery")
            report["segments"].append(dict(id=f"L{index+1:03d}",phase=phase,skill=kind,high_level_id=hl,range_half_open=[start,stop],boundary_state_indices=[start,stop],time_s=[rows[0]["time"],rows[-1]["time"]],entry=key_state(rows[0],q[start]),exit=key_state(rows[-1],q[stop]),checks=checks,status=combine(checks),credit_as_physical_skill=kind!="recenter"))
        # Expand locomotion macros using only labels actually present in the trace.
        report["low_level_action_segments"]=[]
        for segment in report["segments"]:
            if segment["skill"]=="planned_steps":
                start,stop=segment["range_half_open"]
                sub=internal_step_segments(trace,q,start,stop,segment["id"],segment["high_level_id"],dt,limits,th)
                segment["internal_action_ids"]=[a["id"] for a in sub]
                report["low_level_action_segments"].extend(sub)
            else:
                report["low_level_action_segments"].append(dict(id=segment["id"],parent_skill_segment=None,high_level_id=segment["high_level_id"],observed_phase=segment["phase"],range_half_open=segment["range_half_open"],command_range_half_open=segment["range_half_open"],boundary_state_indices=segment["boundary_state_indices"],entry=segment["entry"],exit=segment["exit"],checks=segment["checks"],status=segment["status"],credit_as_physical_skill=segment["credit_as_physical_skill"]))
        report["low_level_action_transitions"]=[dict(from_action=a["id"],to_action=b["id"],shared_state_index=a["boundary_state_indices"][1],identical_measured_boundary=a["exit"]==b["entry"]) for a,b in zip(report["low_level_action_segments"],report["low_level_action_segments"][1:])]
        for left,right in zip(report["segments"],report["segments"][1:]):
            report["transitions"].append(dict(from_segment=left["id"],to_segment=right["id"],shared_state_index=left["boundary_state_indices"][1],identical_measured_boundary=left["exit"]==right["entry"],incoming_state=left["exit"],outgoing_state=right["entry"],scope="same continuous recorded state, velocities/support/contact included; arbitrary-state composition not claimed"))
        from .verify_p4 import evaluate
        goal=evaluate(profile,result,trace,commands,q,actuator)
        report["terminal_goal_recomputation"]=goal
        report["runtime_identity_verdict"]=read(run/"outcome.json") if (run/"outcome.json").exists() else None
        report["actuator_coverage_check"]=check("every_physics_step_actual_actuator_audit",lambda:actuator["samples"]==len(commands)*round(profile["budget"]["control_dt_s"]/profile["budget"]["physics_dt_s"]) and number(actuator["max_position_overshoot"])<=.02 and number(actuator["max_speed_ratio"])<=1.001 and number(actuator["max_effort_ratio"])<=1.001)
        credited=[s for s in report["segments"] if s["credit_as_physical_skill"]]
        counts={status:sum(s["status"]==status for s in credited) for status in ("passed","failed","unknown")}
        report.update(counts=counts,HL_LL=bool(credited),LL_TRAJ=bool(credited) and all(t["identical_measured_boundary"] for t in report["transitions"]),HL_TRAJ=bool(goal["task_success"]),semantic_refinement_complete=bool(credited) and all(s["status"]=="passed" for s in credited) and goal["task_success"] and report["actuator_coverage_check"]["status"]=="passed" and bool(report["runtime_identity_verdict"] and report["runtime_identity_verdict"].get("task_success") is True and report["runtime_identity_verdict"].get("evidence_status")=="witnessed_full"),unmeasured_not_certified=contract["unmeasured_not_certified"],artifact_hashes={n:sha(run/n) for n in ("profile.json","execution/trace.json","execution/command_trace.json","execution/joint_trace.npz","execution/actuator_audit.json","execution/result.json")})
        leaves=[a for a in report["low_level_action_segments"] if a.get("credit_as_physical_skill",True)]
        report["low_level_action_counts"]={status:sum(a["status"]==status for a in leaves) for status in ("passed","failed","unknown")}
        report["semantic_refinement_complete"]=report["semantic_refinement_complete"] and bool(leaves) and all(a["status"]=="passed" for a in leaves)
        report["low_level_command_coverage_complete"]=bool(leaves) and report["low_level_action_segments"][0]["range_half_open"][0]==0 and report["low_level_action_segments"][-1]["range_half_open"][1]==len(commands) and all(t["identical_measured_boundary"] for t in report["low_level_action_transitions"])
        report["status"]="measured_refinement_passed" if report["semantic_refinement_complete"] else "partial_measured_refinement"
        report["remaining_measurement_requests"]=[{"segment":s["id"],"skill":s["skill"],"predicates":[c for c in s["checks"] if c["status"]!="passed"]} for s in report["segments"] if s["status"]!="passed"]
        report["optional_unmeasured_conditions"]=[{"action":a["id"],"predicates":[c for c in a["checks"] if not c.get("required_for_this_run",True) and c["status"]!="passed"]} for a in report["low_level_action_segments"] if any(not c.get("required_for_this_run",True) and c["status"]!="passed" for c in a["checks"])]
        report["remaining_internal_action_requests"]=[{"action":a["id"],"observed_step_label":a.get("observed_step_label"),"predicates":[c for c in a["checks"] if c["status"]!="passed"]} for a in report["low_level_action_segments"] if a.get("parent_skill_segment") and a["status"]!="passed"]
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    return report


def main():
    ap=argparse.ArgumentParser(__doc__); sub=ap.add_subparsers(dest="mode",required=True)
    f=sub.add_parser("freeze");f.add_argument("--out",type=Path,required=True)
    r=sub.add_parser("review");r.add_argument("run",type=Path);r.add_argument("--contract",type=Path,required=True);r.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.mode=="freeze":freeze(args.out);print(args.out);return 0
    result=review(args.run,args.contract);out=args.out or args.run/"skill_refinement.json";write(out,result);print(json.dumps({k:result[k] for k in ("status","errors")},ensure_ascii=False));return 0 if result.get("semantic_refinement_complete") else 1

if __name__=="__main__":raise SystemExit(main())
