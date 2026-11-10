"""Fresh Gamma development reference for H1S-07.P4; no replay or checkpoint."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REPO = TASK.parents[1]
sys.path.insert(0, str(REPO))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=HERE / "p4-development.json")
    parser.add_argument("--refinement-contract", type=Path)
    parser.add_argument("--execute-frozen", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.execute_frozen:
        return execute(out)
    out.mkdir(parents=True, exist_ok=False)
    profile = json.loads(args.profile.read_text())
    write(out / "profile.json", profile)
    expert_source = (REPO / profile["expert_plan_path"]).resolve() if profile.get("expert_plan_path") else HERE / "expert-plan.json"
    expert_source.relative_to(REPO)
    shutil.copyfile(expert_source, out / "expert-plan.json")
    versions = {}
    for package in ("genesis-world", "torch", "mujoco", "scipy", "numpy", "osqp"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    write(out / "environment.json", dict(host=socket.gethostname(), python=sys.version,
          platform=platform.platform(), slurm_job_id=os.environ.get("SLURM_JOB_ID"),
          slurm_partition=os.environ.get("SLURM_JOB_PARTITION"), versions=versions,
          gpu=subprocess.run(["nvidia-smi", "--query-gpu=name,uuid,driver_version", "--format=csv"],
                             text=True, capture_output=True).stdout))
    hashes = {}
    for base in (TASK / "solution", TASK / "extension", TASK / "sandbox" / "trusted", REPO / "infra" / "sandbox"):
        for path in base.rglob("*.py"):
            if "validation" in path.parts or "runs" in path.parts:
                continue
            rel = path.relative_to(REPO)
            target = out / "source_snapshot" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            hashes[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in [TASK / n for n in ("genesis_env.py", "task_spec.py", "cabinets.py")]:
        rel = path.relative_to(REPO)
        target = out / "source_snapshot" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    write(out / "source_hashes.json", hashes)
    from humanoid.g1_support_retrieval import task_spec as frozen_spec
    from humanoid.g1_support_retrieval.cabinets import collider_mjcf
    for variant in frozen_spec.CABINET_VARIANTS:
        collider_mjcf(variant)  # Materialize deterministic effective colliders before hashing.
    asset_hashes = {}
    for path in (TASK / "assets").rglob("*"):
        if path.is_file():
            asset_hashes[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    write(out / "asset_hashes.json", asset_hashes)
    snapshot = out / "source_snapshot"
    shutil.copytree(TASK / "assets", snapshot / TASK.relative_to(REPO) / "assets")
    config = TASK / "solution/step_up/configs/sonic.json"
    frozen_config = snapshot / config.relative_to(REPO)
    frozen_config.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config, frozen_config)
    hashes[str(config.relative_to(REPO))] = hashlib.sha256(config.read_bytes()).hexdigest()
    if args.refinement_contract:
        contract_source = args.refinement_contract.resolve()
        contract_bytes = contract_source.read_bytes()
        contract = json.loads(contract_bytes)
        contract_digest = hashlib.sha256(contract_bytes).hexdigest()
        if contract["profile_snapshot"] != profile:
            raise ValueError("prospective contract/profile mismatch before execution")
        if contract["profile_sha256"] != hashlib.sha256(args.profile.read_bytes()).hexdigest():
            raise ValueError("prospective profile source hash mismatch")
        for name, digest in contract["source_bindings"].items():
            if hashes.get(name) != digest:
                raise ValueError("prospective source binding mismatch: " + name)
        for document in contract.get("frozen_documents", []):
            source_document = (REPO / document["path"]).resolve()
            relative_document = source_document.relative_to(REPO)
            raw = source_document.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != document["sha256"]:
                raise ValueError("prospective document hash mismatch: " + str(relative_document))
            if source_document == expert_source.resolve() and hashlib.sha256((out/"expert-plan.json").read_bytes()).hexdigest()!=digest:
                raise ValueError("archived expert plan differs from frozen document")
            document_copy = out / "frozen_documents" / relative_document.name
            document_copy.parent.mkdir(parents=True,exist_ok=True)
            document_copy.write_bytes(raw)
            archived_document = snapshot / relative_document
            archived_document.parent.mkdir(parents=True,exist_ok=True)
            archived_document.write_bytes(raw)
            hashes[str(relative_document)] = digest
        (out / "refinement-contract.json").write_bytes(contract_bytes)
        write(out / "refinement_contract_binding.json", dict(contract_sha256=contract_digest,
            bound_at_utc=datetime.now(timezone.utc).isoformat(), before_first_physics=True,
            source_bindings_checked=True, profile_snapshot_checked=True))
    write(out / "source_hashes.json", hashes)
    frozen_entry = snapshot / Path(__file__).resolve().relative_to(REPO)
    write(out / "execution_identity.json", dict(executed_source_root=str(snapshot),
        entrypoint=str(frozen_entry), frozen_source_execution=True,
        asset_copy_mode="independent copy, pre/post hash checked"))
    child = subprocess.Popen([sys.executable, str(frozen_entry), "--execute-frozen", "--out", str(out)], cwd=snapshot)
    execution_wall = max(1., profile["budget"]["wall_seconds_per_attempt"] - (time.monotonic()-started) - 90.)
    try:
        return child.wait(timeout=execution_wall)
    except subprocess.TimeoutExpired:
        write(out / "wall_stop.json", dict(reason="predeclared wall budget; reserve 90 seconds for evidence flush",
            elapsed_wall_s=time.monotonic()-started, action="SIGINT to frozen Python worker"))
        child.send_signal(signal.SIGINT)
        try:
            return child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            write(out / "flush_incomplete.json", dict(reason="worker did not stop within 60 second flush reserve",
                partial_trace="execution/trajectory.partial.jsonl", full_witness_allowed=False))
            return 124


def execute(out):
    profile = json.loads((out / "profile.json").read_text())
    asset_hashes = json.loads((out / "asset_hashes.json").read_text())
    stamp = time.monotonic()
    status = "exception_before_execution"
    try:
        from humanoid.g1_support_retrieval import task_spec as spec
        spec.GOAL_CENTER = tuple(profile["goal"]["center_xy_m"])
        spec.GOAL_SIZE = tuple(profile["goal"]["size_xy_m"])
        from humanoid.g1_support_retrieval.solution.push_box import run_push
        ctl = profile["controller"]
        argv = ["--out", str(out / "execution"), "--planned-steps", "--cycles", str(ctl["cycles"]),
                "--stroke", str(ctl["stroke_m"]), "--mass", str(profile["target"]["mass_kg"]),
                "--size", *map(str,profile["target"]["size_m"]),
                "--box-friction", str(profile["target"]["friction"]),
                "--box-x", str(profile["target"]["initial_center_m"][0]),
                "--max-push", str(ctl["max_push_per_hand_N"]),
                "--waist-upper", str(ctl.get("waist_upper_rad",.5)),
                "--thumb-fold", str(ctl.get("thumb_fold_rad",-1.047)),
                "--elbow-upper", str(ctl.get("elbow_upper_rad",2.0944)),
                "--finger-reference-min", str(ctl.get("finger_reference_min_rad",0.0)),
                "--clear-hands-seconds", str(ctl.get("clear_hands_seconds",3.0)),
                "--stand-up-seconds", str(ctl.get("stand_up_seconds",14.0)),
                "--terminal-joint-step", str(ctl.get("terminal_joint_step_rad",0.0)),
                "--seconds", str(profile["budget"]["simulation_seconds_per_attempt"]),
                "--seed", str(profile["seed"]), "--final-approach", str(ctl["final_approach_m"]),
                "--final-mode", str(ctl.get("final_mode","stand")),
                "--final-settle-max-seconds", str(ctl.get("final_settle_max_s",8.0)),
                "--final-settle-dwell", str(ctl.get("final_settle_dwell_s",1.0)),
                "--final-hold-seconds", str(ctl["final_hold_s"]), "--video-fps", str(ctl["video_fps"]),
                "--balance-feedback", "--gravity-compensation", "--elliptic-friction", "--torsional-friction"]
        if ctl.get("measured_clear_start",False):
            argv.append("--measured-clear-start")
        write(out / "command.json", {"entrypoint": "run_push.main", "argv": argv})
        result = run_push.main(argv)
        status = result["status"]
        write(out / "effective_asset_hashes.json", {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in asset_hashes})
    except BaseException as exc:
        write(out / "exception.json", {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        traceback.print_exc()
    finally:
        write(out / "attempt.json", dict(task_id=profile["task_id"], status=status,
              wall_seconds=time.monotonic()-stamp, full_success_claimed=False,
              evidence_status="pending_independent_verification", formal_admission=False))
    if status == "exception_before_execution":
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
