"""Repeat an immutable P4 execution source/profile/assets in a fresh process."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time
import signal
from datetime import datetime, timezone


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def main():
    started=time.monotonic()
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    baseline=args.baseline.resolve(); out=args.out.resolve()
    source=baseline/"source_snapshot"
    for filename in ("source_hashes.json","asset_hashes.json"):
        hashes=json.loads((baseline/filename).read_text())
        if not hashes: raise ValueError("empty frozen manifest")
        for name,digest in hashes.items():
            if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:
                raise ValueError("frozen identity mismatch: "+name)
    out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(source,out/"source_snapshot",ignore=shutil.ignore_patterns("__pycache__"))
    for filename in ("profile.json","expert-plan.json","source_hashes.json","asset_hashes.json"):
        shutil.copyfile(baseline/filename,out/filename)
    if (baseline/"refinement-contract.json").is_file():
        contract_bytes=(baseline/"refinement-contract.json").read_bytes()
        contract=json.loads(contract_bytes)
        if contract["profile_snapshot"]!=json.loads((out/"profile.json").read_text()):
            raise ValueError("frozen repeat contract/profile mismatch")
        for name,digest in contract["source_bindings"].items():
            if hashlib.sha256((out/"source_snapshot"/name).read_bytes()).hexdigest()!=digest:
                raise ValueError("frozen repeat contract/source mismatch: "+name)
        (out/"refinement-contract.json").write_bytes(contract_bytes)
        write(out/"refinement_contract_binding.json",dict(contract_sha256=hashlib.sha256(contract_bytes).hexdigest(),
            bound_at_utc=datetime.now(timezone.utc).isoformat(),before_first_physics=True,
            source_bindings_checked=True,profile_snapshot_checked=True,repeat_of=str(baseline)))
    if (baseline/"frozen_documents").is_dir():
        shutil.copytree(baseline/"frozen_documents",out/"frozen_documents")
    versions={}
    for package in ("genesis-world","torch","mujoco","scipy","numpy","osqp"):
        versions[package]=importlib.metadata.version(package)
    write(out/"environment.json",dict(host=socket.gethostname(),python=sys.version,platform=platform.platform(),
        slurm_job_id=os.environ.get("SLURM_JOB_ID"),slurm_partition=os.environ.get("SLURM_JOB_PARTITION"),
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),versions=versions,
        gpu=subprocess.run(["nvidia-smi","--query-gpu=name,uuid,driver_version","--format=csv"],text=True,capture_output=True).stdout))
    snapshot=out/"source_snapshot"
    entry=snapshot/"humanoid/g1_support_retrieval/extension/run_p4.py"
    write(out/"execution_identity.json",dict(executed_source_root=str(snapshot),entrypoint=str(entry),
        frozen_source_execution=True,asset_copy_mode="independent identical frozen copy",
        repeat_of=str(baseline),source_profile_asset_identity_equal=True))
    write(out/"repeat_launcher_identity.json",dict(sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="external provenance setup only; all physics/controller Python executes frozen source"))
    child=subprocess.Popen([sys.executable,str(entry),"--execute-frozen","--out",str(out)],cwd=snapshot)
    profile=json.loads((out/"profile.json").read_text())
    budget=max(1.,profile["budget"]["wall_seconds_per_attempt"]-(time.monotonic()-started)-90.)
    try:
        return child.wait(timeout=budget)
    except subprocess.TimeoutExpired:
        write(out/"wall_stop.json",dict(reason="predeclared wall budget with 90 second finalization reserve",elapsed_wall_s=time.monotonic()-started))
        child.send_signal(signal.SIGINT)
        try:
            return child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            child.kill();child.wait()
            write(out/"flush_incomplete.json",dict(full_witness_allowed=False,reason="worker exceeded evidence flush reserve"))
            return 124

if __name__=="__main__": raise SystemExit(main())
