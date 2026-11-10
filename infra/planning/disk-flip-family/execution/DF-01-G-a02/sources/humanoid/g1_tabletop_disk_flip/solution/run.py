"""Record representative joint-only candidates, prefixes and fresh-scene replays."""
import argparse
from dataclasses import asdict
import hashlib
import json
import linecache
import platform
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import traceback

import numpy as np


def read_config(values, *, legacy_defaults=False):
    from humanoid.g1_tabletop_disk_flip.task_spec import TaskConfig
    values = dict(values)
    if legacy_defaults:
        # Recorded configurations predating these fields used the original
        # contact and handoff models, regardless of the current scene defaults.
        for name, value in dict(friction_model="pyramidal", collision_detector="mpr",
                                disk_collision_shape="cylinder", post_flip_handoff="bimanual").items():
            values.setdefault(name, value)
    for name in ("table_center", "table_size", "start_xy", "goal_xy", "object_names"):
        if name in values:
            values[name] = tuple(values[name])
    return TaskConfig(**values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu", "gpu"), default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--skill", choices=("slide", "pinch", "pinch_lift", "pinch_turn",
                                          "pinch_and_lift", "pinch_through_turn", "slide_through_turn",
                                          "pinch_complete", "pinch_place"))
    parser.add_argument("--prefix", type=Path, help="execute recorded joint commands from the default reset first")
    parser.add_argument("--replay", type=Path, help="independent fresh-scene replay of trajectory.npz")
    args = parser.parse_args()
    if args.replay and (args.skill or args.prefix or args.config):
        parser.error("--replay reads the frozen configuration; cannot combine with skill, prefix or config")
    original = None
    if args.replay:
        original = json.loads((args.replay.parent / "summary.json").read_text())
        cfg = read_config(original["config"], legacy_defaults=True)
        args.seed = original["physics"]["seed"]
    elif args.config:
        cfg = read_config(json.loads(args.config.read_text()))
    else:
        from humanoid.g1_tabletop_disk_flip.task_spec import TaskConfig
        cfg = TaskConfig()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[3]
    relative_sources = [
        "humanoid/g1_tabletop_disk_flip/task_spec.py", "humanoid/g1_tabletop_disk_flip/assets.py",
        "humanoid/g1_tabletop_disk_flip/solution/controller.py", "humanoid/g1_tabletop_disk_flip/solution/run.py",
        "humanoid/g1_tabletop_disk_flip/solution/audit.py",
        "humanoid/g1_tabletop_disk_flip/solution/grasp_wrench.py",
        "humanoid/g1_tabletop_disk_flip/solution/placement.py",
        "humanoid/g1_tabletop_disk_flip/solution/ik.py",
        "humanoid/g1_tabletop_disk_flip/solution/oracle.py", "humanoid/g1_tabletop/genesis_env.py",
        "humanoid/g1_tabletop/assets.py", "humanoid/g1_tabletop_assembly/task_spec.py",
        "humanoid/g1_tabletop_assembly/solution/controller.py", "humanoid/g1_box_stair_transport/robot.py",
        "humanoid/g1_tabletop_assembly/solution/recording.py",
        "humanoid/g1_support_retrieval/oracle/upper_ik.py", "infra/oracle/core.py", "infra/oracle/__init__.py",
        "humanoid/g1_support_retrieval/task_spec.py",
        "humanoid/g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml",
    ]
    source_hashes = {}
    for relative in relative_sources:
        data = (root / relative).read_bytes()
        source_hashes[relative] = hashlib.sha256(data).hexdigest()
        target = args.output / "sources" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        # Tracebacks must show the captured source even if another development
        # run edits the working tree while this simulation is executing.
        if relative.endswith(".py"):
            linecache.cache[str(root / relative)] = (len(data), None, data.decode().splitlines(keepends=True), str(root / relative))
    runtime_versions = {"python": platform.python_version()}
    for package in ("genesis-world", "torch", "numpy", "mujoco", "scipy"):
        try:
            runtime_versions[package] = version(package)
        except PackageNotFoundError:
            runtime_versions[package] = "not_installed"
    asset_root = root / "humanoid/g1_support_retrieval/assets/unitree_g1/assets"
    asset_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(asset_root.iterdir()) if path.is_file()}
    # Preserve the generated collision geometry, not only the robot meshes.
    # Canonical relative mesh references make this bundle portable across paths.
    import xml.etree.ElementTree as ET
    from ..assets import write_disk_urdf
    disk_spec = next(spec for spec in cfg.scene_objects() if spec["name"] == "disk")
    disk_asset = write_disk_urdf(disk_spec, root / "humanoid/g1_tabletop/assets/generated")
    generated = args.output / "generated_disk"
    generated.mkdir()
    disk_xml = ET.parse(disk_asset).getroot()
    for mesh in disk_xml.findall(".//mesh"):
        path = Path(mesh.attrib["filename"])
        data = path.read_bytes()
        (generated / path.name).write_bytes(data)
        asset_hashes["generated_disk/"+path.name] = hashlib.sha256(data).hexdigest()
        mesh.set("filename", path.name)
    data = (ET.tostring(disk_xml, encoding="unicode")+"\n").encode()
    (generated / "disk.urdf").write_bytes(data)
    asset_hashes["generated_disk/disk.urdf"] = hashlib.sha256(data).hexdigest()
    (args.output / "asset_hashes.json").write_text(json.dumps(asset_hashes, indent=2)+"\n")
    from humanoid.g1_tabletop.genesis_env import G1TabletopGenesis
    from . import controller
    env = G1TabletopGenesis("disk_flip", cfg=cfg, backend=args.backend, seed=args.seed, camera=args.video)
    targets, times, error, writer, c = [], [], None, None, None
    replay_checks = {}
    self_contact_pairs = {}
    environment_contact_pairs = {}
    world_links = {link.idx: env.link_owners.get(link.idx, f"scene_entity_{i}/{link.name}")
                   for i, entity in enumerate(env.scene.entities) if entity is not env.robot
                   for link in entity.links}
    robot_links = {link.idx: link.name for link in env.robot.links}
    from .audit import DiskEpisodeAudit
    audit = DiskEpisodeAudit(env)
    try:
        audit.__enter__()
        (args.output / "initial_state.json").write_text(json.dumps(audit.initial_observation, indent=2)+"\n")
        from .oracle import make_instance, screen_instance
        plan = screen_instance(make_instance(env.cfg, args.seed))
        (args.output / "oracle_plan.json").write_text(json.dumps(plan, indent=2)+"\n")
        if args.video:
            import imageio.v2 as imageio
            writer = imageio.get_writer(args.output / "video.mp4", fps=10, macro_block_size=1)
            writer.append_data(env.render())
            imageio.imwrite(args.output / "initial.png", env.render())
        with (args.output / "trace.jsonl").open("w") as trace:
            def record(target, observation, reward, status, phase):
                targets.append(env.target.detach().cpu().numpy().copy())
                times.append(observation["time"])
                contact = {key: value.detach().cpu().numpy() for key, value in env.robot.get_contacts().items()}
                forces = {}
                environment_forces = {}
                for index in range(len(contact["link_a"])):
                    a, b = int(contact["link_a"][index]), int(contact["link_b"][index])
                    if a in robot_links and b in robot_links:
                        pair = " / ".join(sorted((robot_links[a], robot_links[b])))
                        forces[pair] = forces.get(pair, 0.)+float(np.linalg.norm(contact["force_a"][index]))
                    elif a in robot_links or b in robot_links:
                        robot_link, other = (a, b) if a in robot_links else (b, a)
                        pair = robot_links[robot_link]+" / "+world_links.get(other, f"link_{other}")
                        environment_forces[pair] = environment_forces.get(pair, 0.)+float(np.linalg.norm(contact["force_a"][index]))
                for pair, force in environment_forces.items():
                    if force > .1:
                        stats = environment_contact_pairs.setdefault(pair, dict(peak_force_n=0., observed_control_samples=0))
                        if force > stats["peak_force_n"]:
                            stats.update(peak_force_n=force, peak_time_s=observation["time"], peak_phase=phase)
                        stats["observed_control_samples"] += 1
                for pair, force in forces.items():
                    if force > .1:
                        stats = self_contact_pairs.setdefault(pair, dict(peak_force_n=0., observed_control_samples=0))
                        stats["peak_force_n"] = max(stats["peak_force_n"], force)
                        stats["observed_control_samples"] += 1
                trace.write(json.dumps(dict(time=observation["time"], phase=phase,
                    status=status, objects=observation["objects"],
                    hand_goals=getattr(c, "last_hand_goals", None),
                    ik_errors_m=getattr(c, "last_ik_errors", None),
                    hands={side: {kind: c.hand_pose(side, kind)[0].tolist() for kind in ("palm", "thumb")}
                           for side in ("left", "right")}, joint_position=observation["joint_position"]))+"\n")
                if len(targets) % 200 == 0:
                    print(json.dumps(dict(time=times[-1], phase=phase, stage=status["stage"],
                        disk=observation["objects"]["disk"]["pos"])), flush=True)
                    trace.flush()
                if writer is not None and len(targets) % 5 == 0:
                    writer.append_data(env.render())
            c = controller.GentleController(env, on_step=record)
            def play(path, phase):
                archive = np.load(path, allow_pickle=False)
                commands = archive["targets"]
                if commands.ndim != 2 or commands.shape[1] != 43 or not np.isfinite(commands).all():
                    raise ValueError("invalid recorded joint commands")
                for target in commands:
                    observation, reward, done, status = env.step_targets(target)
                    record(target, observation, reward, status, phase)
                    if done:
                        break
                c.q = env.target.detach().cpu().numpy().astype(float)-c.gravity_offset()
                c.last_observation = env.observe()
                return commands
            if args.replay:
                commands = play(args.replay, "action_replay")
                replay_checks = dict(original_success=original["full_task_success"],
                    replay_success=env.status["success"], all_commands_executed=len(targets) == len(commands),
                    duration_matches=abs(times[-1]-original["status"]["elapsed"]) <= .020001,
                    final_pose_matches=np.allclose(env.state()["disk"]["pos"], original["final_objects"]["disk"]["pos"], atol=.002))
                replay_checks["orientation_matches"] = bool(abs(np.dot(
                    env.state()["disk"]["quat"], original["final_objects"]["disk"]["quat"])) >= .99999)
                replay_checks["physics_metadata_matches"] = env.physics_metadata == original["physics"]
                replay_checks["runtime_versions_match"] = runtime_versions == original.get("runtime_versions")
                original_assets = args.replay.parent / "asset_hashes.json"
                replay_checks["robot_assets_match"] = original_assets.is_file() and json.loads(original_assets.read_text()) == asset_hashes
                physics_sources = [path for path in relative_sources if "/solution/" not in path and not path.startswith("infra/")]
                replay_checks["physics_sources_match"] = all(source_hashes[path] == original["sources_sha256"].get(path)
                                                             for path in physics_sources)
                replay_checks["no_forbidden_state_writes"] = not audit.violations
            else:
                if args.prefix:
                    prefix_summary = json.loads((args.prefix.parent / "summary.json").read_text())
                    if read_config(prefix_summary["config"], legacy_defaults=True) != cfg:
                        raise ValueError("prefix and current physical configuration differ")
                    play(args.prefix, "recorded_prefix")
                if args.skill:
                    getattr(controller, args.skill)(c)
                else:
                    controller.run(c)
    except Exception:
        error = traceback.format_exc()
    finally:
        try:
            if writer is not None:
                writer.append_data(env.render())
                writer.close()
                import imageio.v2 as imageio
                imageio.imwrite(args.output / "final.png", env.render())
            np.savez_compressed(args.output / "trajectory.npz", targets=np.asarray(targets), time=np.asarray(times))
            torque_peaks = env.max_applied_torque.detach().cpu().numpy()
            torque_limits = env.effort.detach().cpu().numpy()
            recorded = np.vstack([env.default_q.detach().cpu().numpy(), np.asarray(targets).reshape(-1, 43)])
            target_speed_peak = float(np.max(np.abs(np.diff(recorded, axis=0)))) / cfg.control_dt if targets else 0.
            actuator_checks = dict(
                effort_limits_passed=bool(np.all(torque_peaks <= torque_limits+1e-6)),
                target_speed_limit_passed=target_speed_peak <= cfg.joint_target_speed_max+1e-5,
                target_speed_peak_rad_s=target_speed_peak,
                applied_torque_peak_nm=torque_peaks.tolist(), effort_limit_nm=torque_limits.tolist())
            summary = dict(task="g1_tabletop_disk_flip", controller="action_replay" if args.replay else "privileged_candidate",
                purpose="representative_validation_only", planning_mode="rolling_local_planning",
                skill_probe=args.skill, prefix=str(args.prefix) if args.prefix else None,
                horizon_control_steps=1, oracle_plan="oracle_plan.json", config=asdict(env.cfg),
                physics=env.physics_metadata, full_task_success=bool(env.status["success"] and not audit.violations
                    and audit.fresh_default_reset and error is None and actuator_checks["effort_limits_passed"]
                    and actuator_checks["target_speed_limit_passed"]), status=env.status,
                error=error, control_steps=len(targets), events=c.events if c else [], final_objects=env.state(),
                integrity_audit=audit.report(),
                robot_pose_setters_during_policy=any(v["method"].startswith("robot.") for v in audit.violations),
                object_pose_setters_during_policy=bool(audit.violations),
                independent_action_replay_verified=bool(replay_checks) and all(replay_checks.values()) and error is None,
                replay_checks=replay_checks, sources_sha256=source_hashes)
            summary["runtime_versions"] = runtime_versions
            summary["actuator_checks"] = actuator_checks
            summary["success_scope"] = "declared_configuration_fixed_pelvis_privileged_development"
            summary["robot_self_contact_observations"] = dict(sampling_hz=50, threshold_n=.1,
                scope="control-boundary observations only; not substep collision certification", pairs=self_contact_pairs)
            summary["robot_environment_contact_observations"] = dict(sampling_hz=50, threshold_n=.1,
                scope="control-boundary observations only; not substep collision certification", pairs=environment_contact_pairs)
            (args.output / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
            print(json.dumps(dict(success=summary["full_task_success"], status=env.status, error=error)), flush=True)
        finally:
            audit.__exit__(None, None, None)
            env.close()
    probe_ok = args.skill and error is None and not env.status["failed"]
    return 0 if probe_ok or summary["full_task_success"] and error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
