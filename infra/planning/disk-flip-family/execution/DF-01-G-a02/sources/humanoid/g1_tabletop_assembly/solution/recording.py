"""Audited, action-aligned assembly traces and independent physics replay.

Importing this module needs NumPy, not Genesis or torch. A trace contains the
initial observation separately, followed by one *post-step* observation for
each 43-dimensional absolute joint target (radians). Ordinary steps are 20 ms;
the final step can be shorter if the evaluator terminates inside its four
5 ms physics ticks.

Typical use::

    with EpisodeAudit(env) as audit:
        with Recorder(output_dir, env, audit=audit) as recorder:
            obs, reward, done, status = recorder.step(target_q)

Alternatively call ``record(obs, target_q, status, reward)`` immediately after
``env.step_targets(target_q)``. Context-manager exit persists partial episodes
after an exception. This is a development audit, not a hostile-code sandbox:
the controller may read object truth and use inverse kinematics.
"""

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np

from humanoid.g1_tabletop_assembly.task_spec import TaskConfig


SCHEMA_VERSION = 1
SIM_DT = .005
CONTROL_DT = .02
NUM_JOINTS = 43
REPO = Path(__file__).resolve().parents[3]
SOURCE_FILES = (
    "humanoid/g1_tabletop_assembly/task_spec.py",
    "humanoid/g1_tabletop_assembly/genesis_env.py",
    "humanoid/g1_tabletop/genesis_env.py",
    "humanoid/g1_tabletop/assets.py",
    "humanoid/g1_box_stair_transport/robot.py",
    "humanoid/g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml",
    "humanoid/g1_tabletop_assembly/solution/recording.py",
)


def _plain(value):
    """Copy tensors/NumPy/dataclasses into finite, JSON-serializable values."""
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _json(value):
    return json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, allow_nan=False)


def _copy(value):
    return json.loads(_json(value))


def config_hash(config):
    return hashlib.sha256(_json(config).encode("utf-8")).hexdigest()


def source_hashes(extra_paths=()):
    result = {}
    paths = [REPO / name for name in SOURCE_FILES]
    paths.extend(Path(path).resolve() for path in extra_paths)
    for path in paths:
        try:
            name = path.relative_to(REPO).as_posix()
        except ValueError:
            name = str(path)
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(_json(value) + "\n", encoding="utf-8")
    temporary.replace(path)


def _vector(value, size, name):
    array = np.asarray(_plain(value), dtype=np.float64)
    if array.shape != (size,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must contain {size} finite numbers")
    return array


def _quaternion_error(first, second):
    first = _vector(first, 4, "quaternion")
    second = _vector(second, 4, "quaternion")
    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator < 1e-12:
        raise ValueError("zero quaternion")
    similarity = abs(float(np.dot(first, second) / denominator))
    return 2 * math.acos(min(1., similarity))


class EpisodeAudit:
    """Reset once, then reject direct pose writes on every scene entity.

    Construction does not reset. Entering the context resets before installing
    guards. The original methods are restored on exit, including error paths.
    A caught forbidden-write exception still permanently invalidates the run.
    """

    ENTITY_METHODS = (
        "set_pos", "set_quat", "set_qpos", "set_dofs_position",
        "set_dofs_velocity", "set_vverts",
    )

    def __init__(self, env):
        self.env = env
        self.active = False
        self.fresh_default_reset = False
        self.initial_observation = None
        self.violations = []
        self._originals = []
        self.guarded_methods = []

    def _guard(self, owner, method, label):
        if not hasattr(owner, method):
            return
        original = getattr(owner, method)
        namespace = getattr(owner, "__dict__", {})
        own_attribute = method in namespace

        def forbidden(*args, **kwargs):
            event = {"method": f"{label}.{method}",
                     "physics_steps": int(getattr(self.env, "physics_steps", -1))}
            self.violations.append(event)
            raise RuntimeError(f"direct state write prohibited after reset: {event['method']}")

        setattr(owner, method, forbidden)
        self._originals.append((owner, method, original, own_attribute))
        self.guarded_methods.append(f"{label}.{method}")

    def __enter__(self):
        if self.active or self.initial_observation is not None:
            raise RuntimeError("EpisodeAudit is single-use")
        if config_hash(self.env.cfg) != config_hash(TaskConfig()):
            raise ValueError("expert recording requires the default assembly TaskConfig")
        initial = _copy(self.env.reset())
        if self.env.physics_steps != 0 or abs(float(initial["time"])) > 1e-12:
            raise ValueError("fresh reset must start at physics step/time zero")
        _vector(initial["joint_position"], NUM_JOINTS, "initial joint position")
        if len(initial["joint_names"]) != NUM_JOINTS:
            raise ValueError("the default G1 trace must have 43 joint names")
        if not np.allclose(initial["joint_position"], _plain(self.env.default_q),
                           rtol=0, atol=1e-6):
            raise ValueError("reset joint positions differ from the default posture")
        if not np.allclose(initial["joint_velocity"], 0., rtol=0, atol=1e-6):
            raise ValueError("reset joint velocities must be zero")
        specs = {item["name"]: item for item in self.env.cfg.scene_objects()}
        for name in self.env.cfg.measurement_names:
            actual = initial["objects"][name]
            if not np.allclose(actual["pos"], specs[name]["pos"], rtol=0, atol=1e-5):
                raise ValueError(f"reset {name} position differs from the default scene")
            angle = self.env.cfg.fixture_initial_pitch if name == "fixture" else 0.
            expected = [math.cos(angle / 2), 0., math.sin(angle / 2), 0.]
            if _quaternion_error(actual["quat"], expected) > 1e-5:
                raise ValueError(f"reset {name} orientation differs from the default scene")
            for field in ("linear_velocity", "angular_velocity"):
                if not np.allclose(actual[field], 0., rtol=0, atol=1e-6):
                    raise ValueError(f"reset {name} {field} must be zero")
        self.initial_observation = initial
        self.fresh_default_reset = True
        try:
            entities = {"robot": self.env.robot, **self.env.objects}
            # Include fixed table/ground/decorative bodies if the adapter exposes
            # them through the scene; moving those would also change physics.
            for index, entity in enumerate(getattr(self.env.scene, "entities", ())):
                if all(entity is not known for known in entities.values()):
                    entities[f"scene_entity_{index}"] = entity
            for label, entity in entities.items():
                for method in self.ENTITY_METHODS:
                    self._guard(entity, method, label)
            self._guard(self.env.scene, "reset", "scene")
            self._guard(self.env.scene, "set_state", "scene")
            self._guard(self.env, "reset", "env")
            self.active = True
            return self
        except BaseException:
            self._restore()
            raise

    def _restore(self):
        for owner, method, original, own_attribute in reversed(self._originals):
            if own_attribute:
                setattr(owner, method, original)
            else:
                delattr(owner, method)
        self._originals.clear()
        self.active = False

    def __exit__(self, exc_type, exc_value, traceback):
        self._restore()
        return False

    def report(self):
        return {
            "fresh_default_reset": self.fresh_default_reset,
            "forbidden_state_write_attempts": deepcopy(self.violations),
            "object_pose_setters_used_after_reset": bool(self.violations),
            "guarded_methods": list(self.guarded_methods),
            "scope": "development API audit; not a hostile-code sandbox",
        }


class Recorder:
    """Write ``trace.jsonl``, ``trajectory.npz``, and ``summary.json``.

    ``record`` accepts the result of exactly one immediately preceding control
    step. It checks the applied target, observation clock, joint order, and
    environment status. Initial state is never mislabelled as an action result.
    """

    def __init__(self, output_dir, env, *, audit, metadata=None, source_paths=()):
        if audit.env is not env or not audit.active:
            raise ValueError("Recorder requires the active EpisodeAudit for this environment")
        if env.physics_steps != 0:
            raise ValueError("create Recorder immediately after the audited default reset")
        self.directory = Path(output_dir)
        self.directory.mkdir(parents=True, exist_ok=True)
        if any((self.directory / name).exists()
               for name in ("trace.jsonl", "trajectory.npz", "summary.json")):
            raise FileExistsError(f"refusing to overwrite an existing trace: {self.directory}")
        self.env, self.audit = env, audit
        self.initial_observation = _copy(audit.initial_observation)
        self.joint_names = list(self.initial_observation["joint_names"])
        self.object_names = list(env.cfg.measurement_names)
        self.records = []
        self.finished = False
        self.summary = None
        self.metadata = {
            "schema_version": SCHEMA_VERSION,
            "task": "g1_tabletop_assembly",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "base_mode": "fixed_pelvis",
            "observation_mode": "privileged_development",
            "config": _copy(env.cfg),
            "config_sha256": config_hash(env.cfg),
            "source_sha256": source_hashes(source_paths),
            "joint_names": self.joint_names,
            "object_names": self.object_names,
            "action_spec": {
                "field": "target_q", "shape": [NUM_JOINTS], "units": "radians",
                "meaning": "absolute joint position targets in joint_names order",
                "api": "env.step_targets(target_q)",
                "physics_hz": 200, "nominal_control_hz": 50,
                "physics_steps_per_control": 4,
                "terminal_control_step_may_be_shorter": True,
                "normalized_action": "(target_q - default_q) / 0.25",
                "default_q": _plain(env.default_q),
                "joint_lower_limits": _plain(env.lo),
                "joint_upper_limits": _plain(env.hi),
                "torque_limits_nm": _plain(env.effort),
            },
            "controller_metadata": _copy(metadata or {}),
        }
        self._stream = (self.directory / "trace.jsonl").open("x", encoding="utf-8")
        self._stream.write(_json({"kind": "initial", "metadata": self.metadata,
                                 "observation": self.initial_observation,
                                 "status": _plain(env.status)}) + "\n")
        self._stream.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        error = f"{exc_type.__name__}: {exc_value}" if exc_type else None
        self.finish(error=error)
        return False

    def step(self, target_q, physics_evidence=None):
        """Apply one target and immediately record the corresponding result."""
        observation, reward, done, status = self.env.step_targets(target_q)
        self.record(observation, target_q, status, reward, physics_evidence)
        return observation, reward, done, status

    def record(self, observation, target_q, status, reward, physics_evidence=None):
        if self.finished or not self.audit.active:
            raise RuntimeError("recording requires an active, unfinished audited episode")
        target = _vector(target_q, NUM_JOINTS, "target_q")
        if not np.allclose(target, _plain(self.env.target), rtol=0, atol=2e-7):
            raise ValueError("target_q differs from the action actually applied by the environment")
        observation, status = _copy(observation), _copy(status)
        if observation["joint_names"] != self.joint_names:
            raise ValueError("joint order changed during the episode")
        if status != _copy(self.env.status):
            raise ValueError("record status must be the environment's current evaluator result")
        for field in ("joint_position", "joint_velocity"):
            _vector(observation[field], NUM_JOINTS, field)
        for name in self.object_names:
            for field, size in (("pos", 3), ("quat", 4), ("linear_velocity", 3),
                                ("angular_velocity", 3)):
                _vector(observation["objects"][name][field], size, f"{name}.{field}")
        previous_time = (self.records[-1]["time_end"] if self.records else
                         float(self.initial_observation["time"]))
        time_end = float(observation["time"])
        delta = time_end - previous_time
        ticks = round(delta / SIM_DT)
        if (not 1 <= ticks <= 4 or abs(delta - ticks * SIM_DT) > 1e-8
                or (ticks != 4 and not status.get("terminated"))):
            raise ValueError("record exactly one 20 ms control step; only terminal steps may be shorter")
        if abs(time_end - self.env.physics_steps * SIM_DT) > 1e-8:
            raise ValueError("post-step observation clock differs from the environment")
        if not math.isfinite(float(reward)):
            raise ValueError("reward must be finite")
        evidence = {
            "physics_steps": int(self.env.physics_steps),
            "max_applied_torque_nm": _plain(self.env.max_applied_torque),
        }
        if physics_evidence is not None:
            evidence["controller"] = _copy(physics_evidence)
        row = {
            "kind": "transition", "index": len(self.records),
            "time_start": previous_time, "time_end": time_end,
            "physics_ticks": ticks, "target_q": target.tolist(),
            "observation": observation, "reward": float(reward),
            "status": status, "physics_evidence": evidence,
        }
        encoded = _json(row)
        self.records.append(row)
        self._stream.write(encoded + "\n")
        self._stream.flush()

    def _save_npz(self):
        observations = [row["observation"] for row in self.records]
        count, objects = len(self.records), len(self.object_names)

        def object_vectors(fields):
            width = sum(size for _, size in fields)
            return np.asarray([
                [[number for field, _ in fields for number in obs["objects"][name][field]]
                 for name in self.object_names] for obs in observations],
                dtype=np.float64).reshape(count, objects, width)

        arrays = {
            "schema_version": np.asarray(SCHEMA_VERSION),
            "joint_names": np.asarray(self.joint_names),
            "object_names": np.asarray(self.object_names),
            "metadata_json": np.asarray(_json(self.metadata)),
            "initial_observation_json": np.asarray(_json(self.initial_observation)),
            "time_start": np.asarray([row["time_start"] for row in self.records]),
            "time": np.asarray([row["time_end"] for row in self.records]),
            "physics_ticks": np.asarray([row["physics_ticks"] for row in self.records], dtype=np.int32),
            "target_q": np.asarray([row["target_q"] for row in self.records],
                                   dtype=np.float64).reshape(count, NUM_JOINTS),
            "joint_position": np.asarray([obs["joint_position"] for obs in observations],
                                         dtype=np.float64).reshape(count, NUM_JOINTS),
            "joint_velocity": np.asarray([obs["joint_velocity"] for obs in observations],
                                         dtype=np.float64).reshape(count, NUM_JOINTS),
            "object_pose": object_vectors((("pos", 3), ("quat", 4))),
            "object_velocity": object_vectors((("linear_velocity", 3), ("angular_velocity", 3))),
            "reward": np.asarray([row["reward"] for row in self.records]),
            "stage": np.asarray([row["status"].get("stage", 0) for row in self.records], dtype=np.int32),
            "status_json": np.asarray([_json(row["status"]) for row in self.records], dtype=np.str_),
            "object_states_json": np.asarray([_json(obs["objects"]) for obs in observations], dtype=np.str_),
            "physics_evidence_json": np.asarray([_json(row["physics_evidence"]) for row in self.records],
                                                dtype=np.str_),
        }
        temporary = self.directory / "trajectory.npz.tmp"
        with temporary.open("wb") as handle:
            np.savez_compressed(handle, **arrays)
        temporary.replace(self.directory / "trajectory.npz")

    def finish(self, error=None):
        """Persist a final or partial trace; only actual final evaluator success counts."""
        if self.finished:
            return self.summary
        self.finished = True
        final_status = _copy(self.env.status)
        evaluator_status = _copy(self.env.evaluator._result())
        aligned = bool(self.records and self.records[-1]["status"] == final_status
                       and self.records[-1]["physics_evidence"]["physics_steps"] == self.env.physics_steps)
        success = bool(error is None and aligned and final_status.get("success")
                       and evaluator_status.get("success") and final_status.get("terminated")
                       and not final_status.get("failed")
                       and self.audit.fresh_default_reset and not self.audit.violations)
        self.summary = {
            **self.metadata,
            "full_task_success": success,
            "trajectory_kind": "successful_expert" if success else "partial_attempt",
            "recording_complete": error is None and aligned,
            "episode_terminated": bool(final_status.get("terminated")),
            "incomplete": not success,
            "error": error,
            "control_steps": len(self.records),
            "physics_steps": int(self.env.physics_steps),
            "duration_seconds": self.env.physics_steps * SIM_DT,
            "final_status": final_status,
            "evaluator_final_status": evaluator_status,
            "initial_objects": self.initial_observation["objects"],
            "final_objects": _copy(self.env.state()),
            "max_applied_torque_nm": _plain(self.env.max_applied_torque),
            "audit": self.audit.report(),
            "stage_transitions": _stage_transitions([row["status"].get("stage", 0)
                                                    for row in self.records]),
            "files": {"trajectory": "trajectory.npz", "trace": "trace.jsonl"},
        }
        try:
            self._save_npz()
        except BaseException as exc:
            self.summary.update(full_task_success=False, recording_complete=False,
                                incomplete=True, save_error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            try:
                _write_json(self.directory / "summary.json", self.summary)
            finally:
                self._stream.close()
        return self.summary


def _stage_transitions(stages):
    transitions = [0]
    for stage in stages:
        if int(stage) != transitions[-1]:
            transitions.append(int(stage))
    return transitions


def _load_trace(trace_path):
    path = Path(trace_path)
    if path.is_dir():
        path = path / "trajectory.npz"
    if path.suffix == ".json" and path.name == "summary.json":
        path = path.parent / "trajectory.npz"
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        if not rows or rows[0].get("kind") != "initial":
            raise ValueError("JSONL trace must start with its separate initial observation")
        transitions = [row for row in rows[1:] if row.get("kind") == "transition"]
        return {
            "metadata": rows[0]["metadata"],
            "initial": rows[0]["observation"],
            "targets": np.asarray([row["target_q"] for row in transitions],
                                  dtype=float).reshape(-1, NUM_JOINTS),
            "stages": [row["status"].get("stage", 0) for row in transitions],
            "final_status": transitions[-1]["status"] if transitions else rows[0]["status"],
            "final_objects": (transitions[-1]["observation"] if transitions else
                              rows[0]["observation"])["objects"],
        }
    with np.load(path, allow_pickle=False) as data:
        count = len(data["target_q"])
        initial = json.loads(str(data["initial_observation_json"]))
        return {
            "metadata": json.loads(str(data["metadata_json"])),
            "initial": initial,
            "targets": np.array(data["target_q"], dtype=np.float64),
            "stages": data["stage"].tolist(),
            "final_status": json.loads(str(data["status_json"][-1])) if count else {},
            "final_objects": (json.loads(str(data["object_states_json"][-1])) if count else
                              initial["objects"]),
        }


def replay(trace_path, backend="cpu", output_dir=None, *,
           position_tolerance=1e-4, rotation_tolerance=1e-3, env_factory=None):
    """Re-simulate saved targets from a default reset, never restore saved poses.

    ``env_factory`` is only a dependency-injection hook for plain unit tests.
    Normal execution imports and creates the Genesis assembly adapter here.
    A replay is verified only if its evaluator succeeds, source/config hashes
    match, its stage sequence matches, and final object poses agree.
    """
    trace = _load_trace(trace_path)
    targets = trace["targets"]
    if targets.ndim != 2 or targets.shape[1] != NUM_JOINTS or not np.isfinite(targets).all():
        raise ValueError("trace targets must have shape (steps, 43) and be finite")
    if trace["metadata"]["config_sha256"] != config_hash(TaskConfig()):
        raise ValueError("replay requires a trace recorded with default assembly configuration")
    if position_tolerance <= 0 or rotation_tolerance <= 0:
        raise ValueError("replay tolerances must be positive")
    if env_factory is None:
        from humanoid.g1_tabletop_assembly.genesis_env import G1TabletopAssemblyGenesis
        env_factory = G1TabletopAssemblyGenesis
    env = env_factory(backend=backend)
    report = {
        "trace_path": str(Path(trace_path).resolve()), "backend": backend,
        "action_only_replay": True, "replay_verified": False,
        "full_task_success": False, "expected_control_steps": len(targets),
        "position_tolerance_m": position_tolerance,
        "rotation_tolerance_rad": rotation_tolerance,
    }
    audit = EpisodeAudit(env)
    records, error, recorder = [], None, None
    try:
        with audit:
            if trace["metadata"]["joint_names"] != audit.initial_observation["joint_names"]:
                raise ValueError("trace joint order differs from this environment")
            if output_dir is not None:
                recorder = Recorder(output_dir, env, audit=audit,
                                    metadata={"controller": "action_only_replay",
                                              "source_trace": report["trace_path"]})
            for target in targets:
                observation, reward, done, status = env.step_targets(target)
                if recorder is not None:
                    recorder.record(observation, target, status, reward)
                records.append(status)
                if done:
                    break
            final_objects = _copy(env.state())
            errors = {}
            for name, expected in trace["final_objects"].items():
                actual = final_objects[name]
                errors[name] = {
                    "position_m": float(np.linalg.norm(np.asarray(actual["pos"]) - expected["pos"])),
                    "rotation_rad": _quaternion_error(actual["quat"], expected["quat"]),
                }
            current_sources = source_hashes()
            expected_sources = trace["metadata"]["source_sha256"]
            source_match = all(expected_sources.get(name) == digest
                               for name, digest in current_sources.items())
            stage_match = [row.get("stage", 0) for row in records] == trace["stages"]
            success_match = bool(env.status.get("success")) == bool(trace["final_status"].get("success"))
            object_match = all(item["position_m"] <= position_tolerance
                               and item["rotation_rad"] <= rotation_tolerance
                               for item in errors.values())
            success = bool(env.status.get("success") and env.evaluator._result().get("success")
                           and env.status.get("terminated") and not env.status.get("failed")
                           and len(records) == len(targets) and len(targets)
                           and not audit.violations)
            report.update(
                full_task_success=success,
                replay_verified=bool(success and source_match and stage_match
                                     and success_match and object_match),
                control_steps=len(records), final_status=_copy(env.status),
                source_hashes_match=source_match, stages_match=stage_match,
                success_matches=success_match, final_objects_match=object_match,
                stage_transitions=_stage_transitions([row.get("stage", 0) for row in records]),
                final_object_errors=errors, final_objects=final_objects,
            )
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        report.update(error=error, full_task_success=False, replay_verified=False,
                      control_steps=len(records))
        raise
    finally:
        try:
            if recorder is not None:
                recorder.finish(error=error)
            report["audit"] = audit.report()
            if output_dir is not None:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                _write_json(Path(output_dir) / "replay_report.json", report)
        finally:
            env.close()
    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Replay assembly absolute joint targets from a fresh reset")
    parser.add_argument("trace", type=Path)
    parser.add_argument("--backend", choices=("cpu", "gpu"), default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.trace, backend=args.backend, output_dir=args.output)
    print(_json(report), flush=True)
    return 0 if report["replay_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
