"""Independent measured-state P4 goal verifier and three-level trajectory map.

It accepts any legal complete route: reference phase names never enter the
success predicate. Missing logs fail closed; a motion video is not state evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import shutil
from pathlib import Path
import numpy as np


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def corners(position, quaternion, size):
    w, x, y, z = quaternion
    rotation = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                         [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                         [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    points = np.array(list(itertools.product((-1., 1.), repeat=3))) * np.asarray(size)/2
    return points @ rotation.T + position


def high_level(phase):
    if phase == "approach":
        return "H1_observe_and_establish_push_posture"
    if phase.startswith(("touch", "push")):
        return "H2_ground_supported_transport"
    if phase.startswith(("planned", "step", "return", "set_root")):
        return "H3_reposition_for_next_contact"
    return "H4_release_and_stabilize_delivery"


def evaluate(profile, result, trace, commands, joints, actuator):
    errors = []
    if len(trace) < 2 or len(commands) != len(trace)-1:
        errors.append("state_command_coverage_mismatch")
    if len(joints) != len(trace):
        errors.append("joint_state_coverage_mismatch")
    times = np.array([row["time"] for row in trace], dtype=float)
    if not len(times) or not np.isfinite(times).all() or abs(times[0]) > 1e-9 or not np.allclose(np.diff(times), .02, rtol=0, atol=1e-8):
        errors.append("non_contiguous_state_time")
    if joints.shape != (len(trace), 50):
        errors.append("joint_state_shape_mismatch")
    for key in ("object_attachment", "runtime_pose_writes", "applied_root_wrench"):
        if result.get(key) is not False:
            errors.append("forbidden_integrity_flag:"+key)
    for cmd in commands:
        for key, expected in (("joint_position_target",43),("leg_position_target",12),("reference_velocity",43)):
            values=np.asarray(cmd.get(key, []), dtype=float)
            if values.shape != (expected,) or not np.isfinite(values).all():
                errors.append("invalid_command:"+key)
        if cmd.get("leg_torque") is not None:
            values=np.asarray(cmd["leg_torque"], dtype=float)
            if values.shape != (12,) or not np.isfinite(values).all():
                errors.append("invalid_command:leg_torque")
    if not np.isfinite(joints).all():
        errors.append("nonfinite_joint_state")
    if len(commands) and (len(commands) != len(times)-1 or not np.allclose([c["time"] for c in commands], times[:-1], rtol=0, atol=1e-8)):
        errors.append("command_time_mismatch")
    if actuator.get("samples") != len(commands)*4:
        errors.append("physics_actuator_coverage_mismatch")
    for key, limit in (("max_position_overshoot", .001), ("max_speed_ratio", 1.001), ("max_effort_ratio", 1.001)):
        if key not in actuator or not np.isfinite(actuator[key]) or actuator[key] > limit:
            errors.append("actuator_"+key)
    for recorded, expected in (("box_size", profile["target"]["size_m"]), ("box_mass_kg", profile["target"]["mass_kg"]), ("box_floor_friction", profile["target"]["friction"])):
        if recorded not in result or not np.allclose(result[recorded], expected, rtol=0, atol=1e-8):
            errors.append("scene_binding_mismatch:"+recorded)
    goal = profile["goal"]
    center, size = np.asarray(goal["center_xy_m"]), np.asarray(goal["size_xy_m"])
    lo, hi = center-size/2, center+size/2
    target_size = profile["target"]["size_m"]
    stable, in_goal = [], []
    max_bottom = 0.
    initial_position_ok = bool(trace and np.allclose(trace[0]["box"], profile["target"]["initial_center_m"], atol=1e-5))
    if not initial_position_ok:
        errors.append("initial_target_does_not_match_profile")
    for row in trace:
        position, quaternion = np.asarray(row["box"]), np.asarray(row["box_quat"])
        if not np.isfinite(position).all() or not np.isfinite(quaternion).all() or abs(np.linalg.norm(quaternion)-1) > 1e-3:
            errors.append("invalid_target_pose")
            stable.append(False); in_goal.append(False); continue
        pts = corners(position, quaternion, target_size)
        inside = bool((pts[:, :2] >= lo-1e-5).all() and (pts[:, :2] <= hi+1e-5).all())
        in_goal.append(inside)
        bottom = float(pts[:, 2].min())
        max_bottom = max(max_bottom, abs(bottom))
        support = row["support_contacts"]
        released = not row["contact_links"] and all(np.linalg.norm(f) <= .5 for f in row["forces"].values())
        target_ok = (row["box_speed"] <= goal["max_linear_speed_m_s"] and
                     row["box_angular_speed"] <= goal["max_angular_speed_rad_s"] and
                     row["tilt_deg"] <= goal["max_tilt_deg"] and
                     abs(bottom) <= goal["max_ground_gap_m"] and
                     support["target_ground_fz_N"] >= .8*profile["target"]["mass_kg"]*9.81)
        robot_ok = (np.linalg.norm(row["root_linear_velocity"]) <= .03 and
                    np.linalg.norm(row["root_angular_velocity"]) <= .05)
        stable.append(bool(inside and released and target_ok and robot_ok))
    if in_goal and in_goal[0]:
        errors.append("target_starts_in_delivery_zone")
    if max_bottom > goal["max_ground_gap_m"]:
        errors.append("heavy_target_lost_ground_support_or_penetrated_floor")
    dwell_start = len(stable)
    for i in range(len(stable)-1, -1, -1):
        if not stable[i]:
            break
        dwell_start = i
    dwell = float(times[-1]-times[dwell_start]) if dwell_start < len(times) else 0.
    if times.size and times[-1] > profile["budget"]["simulation_seconds_per_attempt"]:
        errors.append("simulation_budget_exceeded")
    if dwell+1e-9 < goal["hold_s"]:
        errors.append("final_released_stable_dwell_too_short")
    return dict(schema="h1-p4-measured-outcome/1", task_id=profile["task_id"],
                controller_status=result["status"],
                physical_goal_met=bool(dwell+1e-9>=goal["hold_s"]),
                position_tolerance_rad=.001,
                position_tolerance_source="humanoid/g1_support_retrieval/sandbox/trusted/relay_scoring.py:POSITION_TOLERANCE; TASK_CARD.md:18",
                task_success=not errors, evidence_status="witnessed_full" if not errors else "unknown",
                formal_admission=False, privileged=True, errors=sorted(set(errors)),
                measured_final_dwell_s=dwell, measured_simulation_s=float(times[-1]) if len(times) else 0,
                state_samples=len(trace), command_samples=len(commands), physics_samples=actuator.get("samples"),
                final_target_entirely_in_D=bool(in_goal[-1]) if in_goal else False,
                max_absolute_target_bottom_m=max_bottom,
                max_nonhand_target_contact_N=max((row["body_contact_N"] for row in trace),default=0),
                max_nonfoot_ground_contact_N=max((row["support_contacts"]["body_ground_force_N"] for row in trace),default=0),
                terminal_reference_standing=bool(trace and min(trace[-1]["support_contacts"]["feet_ground_fz_N"])>1 and trace[-1]["support_contacts"]["body_ground_force_N"]<1),
                robot_stability_scope="Measured base velocities; no hidden hand-only or foot-only contact requirement. Actual standing/support contacts are separate reference diagnostics.",
                cannot_lift_claim="Only excluded by declared 2 kg lifted-payload rule; physical impossibility is not claimed.")


def mapping(trace, commands):
    segments = []
    start = 0
    while start < len(commands):
        phase = trace[start]["phase"]
        end = start+1
        while end < len(commands) and trace[end]["phase"] == phase:
            end += 1
        sid = f"L{len(segments)+1:03d}"
        high_id=high_level(phase.lower())
        if phase.lower().startswith("retreat") and end<len(commands) and trace[end]["phase"].lower().startswith("planned"):
            high_id="H2_ground_supported_transport"
        segments.append(dict(id=sid, high_level_id=high_id, phase=phase,
            start_state_index=start, end_state_index=end, command_range_half_open=[start, end],
            start_s=trace[start]["time"], end_s=trace[end]["time"],
            measured_trajectory="execution/joint_trace.npz:measured",
            commands="execution/command_trace.json", physical_state="execution/trace.json"))
        start = end
    sequence=[]
    for segment in segments:
        if sequence and sequence[-1]["id"]==segment["high_level_id"]:
            sequence[-1]["low_level_ids"].append(segment["id"])
            sequence[-1]["end_state_index"]=segment["end_state_index"]
        else:
            sequence.append(dict(id=segment["high_level_id"],low_level_ids=[segment["id"]],
                start_state_index=segment["start_state_index"],end_state_index=segment["end_state_index"]))
    return dict(schema="h1-high-low-trajectory-mapping/1", generated_from="actual continuous execution phase transitions",
                scope="privileged finite expert; no replayed checkpoint stitching; semantic review separate", segments=segments,
                high_level_plan=sequence)


def physical_command_errors(data, columns, joint_names, command_count):
    expected = (["time", "leg_force_mode"] + ["position_target:"+n for n in joint_names] +
        ["applied_leg_force:"+n for n in joint_names[:12]] +
        ["leg_force_lower:"+n for n in joint_names[:12]] +
        ["leg_force_upper:"+n for n in joint_names[:12]])
    if len(joint_names)!=43 or list(columns)!=expected:
        return ["physics_command_column_mismatch"]
    if data.shape != (4*command_count,81) or not np.isfinite(data).all() or not np.allclose(data[:,0],np.arange(len(data))*.005,rtol=0,atol=1e-8):
        return ["exact_physics_command_coverage_mismatch"]
    errors=[]
    if not np.isin(data[:,1],[0,1]).all(): errors.append("invalid_leg_control_mode")
    lower,upper=data[:,57:69],data[:,69:81]
    if not (lower<=upper).all(): errors.append("inverted_command_force_bounds")
    selected=data[:,1]==1
    force=data[selected,45:57]
    if not ((force>=lower[selected]-1e-5)&(force<=upper[selected]+1e-5)).all():
        errors.append("applied_command_force_exceeds_bounds")
    return errors


def verify(directory):
    directory = Path(directory)
    old_outcome=directory/"outcome.json"
    if old_outcome.is_file():
        old_hash=hashlib.sha256(old_outcome.read_bytes()).hexdigest()
        history=directory/"review_history"/old_hash
        history.mkdir(parents=True,exist_ok=True)
        for name in ("outcome.json","verification_source.py","manifest.json"):
            if (directory/name).is_file(): shutil.copyfile(directory/name,history/name)
    checker_copy=directory/"verification_source.py"
    if Path(__file__).resolve()!=checker_copy.resolve():
        shutil.copyfile(__file__,checker_copy)
    try:
        profile, result = read(directory/"profile.json"), read(directory/"execution/result.json")
        trace, commands = read(directory/"execution/trace.json"), read(directory/"execution/command_trace.json")
        joint_archive = np.load(directory/"execution/joint_trace.npz", allow_pickle=False)
        joints = joint_archive["measured"]
        actuator=read(directory/"execution/actuator_audit.json")
        outcome = evaluate(profile, result, trace, commands, joints, actuator)
        trajectory_time=joint_archive["time"]
        if trajectory_time.shape!=(len(trace),) or not np.allclose(trajectory_time,[r["time"] for r in trace],rtol=0,atol=1e-8) or joint_archive["joint_names"].tolist()!=actuator["joint_names"]:
            outcome.update(task_success=False,evidence_status="unknown")
            outcome["errors"].append("joint_archive_time_or_identity_mismatch")
        if result.get("recorder_version") != "p4_aligned_state_exact_substep_commands_v2":
            outcome.update(task_success=False, evidence_status="unknown")
            outcome["errors"].append("legacy_recorder_mixed_angular_velocity_timestamp")
        else:
            physical = np.load(directory/"execution/physics_commands.npz", allow_pickle=False)
            physical_errors=physical_command_errors(physical["data"],physical["columns"].tolist(),joint_archive["joint_names"].tolist(),len(commands))
            if physical_errors:
                outcome.update(task_success=False, evidence_status="unknown")
                outcome["errors"].extend(physical_errors)
        if len(trace) == len(commands)+1:
            write(directory/"plan_mapping.json", mapping(trace, commands))
        changed = []
        source_hashes = read(directory/"source_hashes.json")
        critical = ["humanoid/g1_support_retrieval/solution/push_box/run_push.py",
                    "humanoid/g1_support_retrieval/extension/run_p4.py",
                    "humanoid/g1_support_retrieval/extension/verify_p4.py",
                    "humanoid/g1_support_retrieval/sandbox/trusted/statelog.py",
                    "humanoid/g1_support_retrieval/task_spec.py",
                    "humanoid/g1_support_retrieval/genesis_env.py"]
        changed.extend(name for name in critical if name not in source_hashes)
        for name, digest in source_hashes.items():
            archived = directory/"source_snapshot"/name
            if not archived.is_file() or hashlib.sha256(archived.read_bytes()).hexdigest()!=digest:
                changed.append(name)
        identity = read(directory/"execution_identity.json")
        if identity.get("frozen_source_execution") is not True:
            outcome.update(task_success=False, evidence_status="unknown")
            outcome["errors"].append("execution_not_bound_to_frozen_source")
        asset_start = read(directory/"asset_hashes.json")
        asset_end = read(directory/"effective_asset_hashes.json")
        for name, digest in asset_start.items():
            asset = directory/"source_snapshot"/name
            if not asset.is_file() or hashlib.sha256(asset.read_bytes()).hexdigest()!=digest:
                changed.append(name)
        physical_world=np.load(directory/"execution/world_params.npz",allow_pickle=False)
        if set(physical_world.files)!={"links_mass","geoms_friction_ratio"} or any(not np.isfinite(physical_world[k]).all() or (physical_world[k]<0).any() for k in physical_world.files):
            outcome.update(task_success=False,evidence_status="unknown")
            outcome["errors"].append("invalid_effective_world_parameters")
        # Frozen G1 scene build order: plane1 + walls4 + six(visual,collider)12 + goal1 + topboxes4.
        # Every preceding entity has one link; the first floor box is global link22.
        target_mass=float(physical_world["links_mass"][22])
        outcome["physical_target_mass_kg"]=target_mass
        outcome["target_mass_link_binding"]="frozen G1 native scene global link22; creation order in genesis_env.py"
        if abs(target_mass-profile["target"]["mass_kg"])>1e-6:
            outcome.update(task_success=False,evidence_status="unknown")
            outcome["errors"].append("physical_target_mass_mismatch")
        environment = read(directory/"environment.json")
        attempt = read(directory/"attempt.json")
        if not asset_start or asset_start != asset_end:
            outcome.update(task_success=False, evidence_status="unknown")
            outcome["errors"].append("effective_asset_manifest_mismatch")
        if not environment.get("gpu") or environment.get("slurm_partition") != "gamma" or attempt.get("task_id") != profile["task_id"]:
            outcome.update(task_success=False, evidence_status="unknown")
            outcome["errors"].append("run_identity_mismatch")
        outcome["verification_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        outcome["video_recorded"] = (directory/"execution/motion.mp4").is_file()
        outcome["human_video_review"] = "pending"
        outcome["release_ready"] = False
        outcome["three_level_mapping_scope"] = "observed phase-to-control/trajectory mapping; semantic skill entry/effect and transition review pending"
        if changed:
            outcome.update(task_success=False, evidence_status="unknown")
            outcome["errors"].append("source_snapshot_hash_mismatch")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        outcome = dict(schema="h1-p4-measured-outcome/1", task_id="H1S-07.P4", task_success=False,
            evidence_status="unknown", formal_admission=False,
            errors=[f"missing_or_invalid_evidence:{type(exc).__name__}:{exc}"])
    write(directory/"outcome.json", outcome)
    names = ["refinement-contract.json", "refinement-identity.json", "trajectory_overview.png", "execution/trajectory.partial.jsonl", "repeat_launcher_identity.json", "wall_stop.json", "verification_source.py", "execution_identity.json", "expert-plan.json", "effective_asset_hashes.json", "execution/world_params.npz", "profile.json", "environment.json", "source_hashes.json", "asset_hashes.json", "attempt.json", "command.json",
             "plan_mapping.json", "outcome.json", "execution/trace.json", "execution/command_trace.json",
             "execution/result.json", "execution/joint_trace.npz", "execution/physics_commands.npz", "execution/actuator_audit.json", "execution/motion.mp4"]
    write(directory/"manifest.json", {name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
                                       for name in names if (directory/name).is_file()})
    return outcome


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["task_success"] else 1)
