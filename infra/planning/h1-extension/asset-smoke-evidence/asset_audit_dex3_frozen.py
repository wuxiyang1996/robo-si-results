"""Static official-asset audit and bounded passive Genesis GPU loading probes.

No manipulation controller or task-success evaluator is provided. Smoke outcomes
are asset-load/finite-state observations only and never count as H1 task success.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import socket
import time
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_asset(path):
    path=Path(path).resolve()
    root=ET.parse(path).getroot()
    refs=[]
    compiler=root.find("compiler")
    meshdir=compiler.get("meshdir", "") if compiler is not None else ""
    for node in root.iter():
        value=node.get("filename") if node.tag=="mesh" and root.tag=="robot" else node.get("file") if node.tag in ("mesh","include","texture","hfield") else None
        if not value:
            continue
        if value.startswith("package://"):
            resolved=None
        elif value.startswith("file://"):
            resolved=Path(value[7:]).resolve()
        else:
            resolved=(path.parent/(meshdir if node.tag=="mesh" and root.tag=="mujoco" else "")/value).resolve()
        exists=resolved is not None and resolved.is_file()
        refs.append({"kind":node.tag,"reference":value,"resolved":str(resolved) if resolved else None,"exists":exists,"sha256":sha(resolved) if exists else None})
    masses=[]
    for node in root.findall(".//inertial/mass"):
        masses.append(float(node.get("value")))
    joints=[{"name":j.get("name"),"type":j.get("type"),"limit":dict(j.find("limit").attrib) if j.find("limit") is not None else None,"mimic":dict(j.find("mimic").attrib) if j.find("mimic") is not None else None} for j in root.findall("joint")]
    return {"schema":"h1-official-asset-static-audit/1","file":str(path),"sha256":sha(path),"format":root.tag,"model_name":root.get("name",root.get("model")),"links":len(root.findall("link")),"joints":joints,"declared_mass_sum_kg":sum(masses) if masses else None,"mass_values_finite_positive":bool(masses) and all(math.isfinite(m) and m>0 for m in masses),"references":refs,"missing_references":[r for r in refs if not r["exists"]],"physical_validation":False,"task_success":None}


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")


def smoke(plan_path, model_id, out):
    import numpy as np
    plan=json.loads(Path(plan_path).read_text())
    model=next(m for m in plan["models"] if m["id"]==model_id)
    if plan["simulation_seconds"]>2 or plan["wall_seconds"]>1200 or plan["gpu_count"]!=1:
        raise ValueError("Smoke budget must remain 1 GPU, <=2 simulated seconds/model and <=20 min wall/model")
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    write(out/"predeclared-plan.json",plan)
    audit=inspect_asset(model["file"]);write(out/"static-audit.json",audit)
    result={"schema":"h1-asset-gpu-smoke/1","model_id":model_id,"task_success":None,"counts_as_H1_task_run":False,"controller":"none; passive default joint pose","formal_admission":False,"status":"preflight","simulated_seconds":0.0,"physics_steps":0,"origin_file_sha256":audit["sha256"],"plan_sha256":sha(plan_path),"source_sha256":sha(__file__)}
    if audit["sha256"]!=model["sha256"] or audit["missing_references"]:
        result.update(status="blocked_asset_references_or_identity")
        write(out/"result.json",result)
        return result
    start=time.monotonic();rows=[]
    try:
        import torch
        import genesis as gs
        if not torch.cuda.is_available():
            raise RuntimeError("Allocated CUDA GPU required")
        write(out/"environment.json",{"hostname":socket.gethostname(),"slurm_job_id":os.environ.get("SLURM_JOB_ID"),"slurm_array_task_id":os.environ.get("SLURM_ARRAY_TASK_ID"),"device":torch.cuda.get_device_name(0),"packages":{p:importlib.metadata.version(p) for p in ("genesis-world","torch","numpy")}})
        gs.init(backend=gs.gpu,logging_level="warning",seed=0)
        dt=plan["physics_dt"]
        scene=gs.Scene(sim_options=gs.options.SimOptions(dt=dt,substeps=1),rigid_options=gs.options.RigidOptions(enable_self_collision=True,enable_collision=True),show_viewer=False)
        scene.add_entity(gs.morphs.Plane())
        robot=scene.add_entity(gs.morphs.URDF(file=model["file"],fixed=False,pos=tuple(model["spawn_xyz"])))
        scene.build()
        result.update(status="loaded",load_wall_seconds=time.monotonic()-start,n_dofs=robot.n_dofs,n_qs=robot.n_qs)
        def array(x):
            return x.detach().cpu().numpy() if hasattr(x,"detach") else np.asarray(x)
        steps=int(round(plan["simulation_seconds"]/dt))
        for step in range(steps+1):
            state={"step":step,"time":step*dt,"root_pos":array(robot.get_pos()).tolist(),"root_quat":array(robot.get_quat()).tolist(),"qpos":array(robot.get_qpos()).tolist(),"qvel":array(robot.get_dofs_velocity()).tolist(),"root_velocity":array(robot.get_vel()).tolist(),"root_angular_velocity":array(robot.get_ang()).tolist()}
            if not all(np.isfinite(np.asarray(v)).all() for v in state.values()):
                raise ValueError("Nonfinite passive physical state")
            rows.append(state)
            result["physics_steps"]=step;result["simulated_seconds"]=step*dt
            if step==steps:
                break
            if time.monotonic()-start>plan["wall_seconds"]-20:
                result["status"]="wall_budget_exhausted";break
            scene.step()
        if result["physics_steps"]==steps:
            result["status"]="passive_finite_rollout_completed"
        if rows:
            result["initial_root_pos"]=rows[0]["root_pos"]
            result["final_root_pos"]=rows[-1]["root_pos"]
            result["final_root_speed_mps"]=float(np.linalg.norm(rows[-1]["root_velocity"]))
            result["final_root_angular_speed_radps"]=float(np.linalg.norm(rows[-1]["root_angular_velocity"]))
        result["stable_pose_claimed"]=False
        result["limitations"]=["Default joint pose; no stabilizing, locomotion or manipulation controller","Passive finite rollout is not balance, load-bearing, grasping or task feasibility validation","Candidate variant selection is not a frozen H1 embodiment decision","Genesis importer collision/inertia warnings remain part of the probe log"]
    except Exception as exc:
        result.update(status="load_or_rollout_error",error={"type":type(exc).__name__,"message":str(exc)})
    finally:
        with (out/"states.jsonl").open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row,allow_nan=False)+"\n")
        result["wall_seconds"]=time.monotonic()-start
        result["state_log_sha256"]=sha(out/"states.jsonl")
        result["source_unchanged"]=result["source_sha256"]==sha(__file__)
        result["asset_unchanged"]=result["origin_file_sha256"]==sha(model["file"])
        write(out/"result.json",result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("inspect");a.add_argument("file",type=Path);a.add_argument("--out",type=Path,required=True)
    b=sub.add_parser("smoke");b.add_argument("--plan",type=Path,required=True);b.add_argument("--model",required=True);b.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="inspect":
        result=inspect_asset(args.file);args.out.parent.mkdir(parents=True,exist_ok=True);write(args.out,result)
    else:
        result=smoke(args.plan,args.model,args.out)
    print(json.dumps({"output":str(args.out),"status":result.get("status","static_audit_only"),"task_success":None}))
    return 0 if not result.get("error") and not result.get("missing_references") else 2

if __name__=="__main__":
    raise SystemExit(main())
