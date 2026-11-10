"""Bounded, explicitly non-task fixed-body hand drive/mimic diagnostic.

Original assets are never edited. A derived fixture locks body joints; root is
fixed in zero gravity without a floor. Only URDF non-mimic hand drivers receive
PD commands. This cannot certify grasp contact, balance, hardware motor mapping,
or any H1 task. Prepare freezes mappings, limits, assets, code and solver source.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def is_hand(name):return '_hand_' in name or name.startswith(('L_','R_'))
def phase(step):
    if step<100:return 'neutral',0.
    if step<300:
        x=(step-100)/200;return 'ramp_out',x*x*(3-2*x)
    if step<500:return 'hold_out',1.
    if step<700:
        x=(step-500)/200;return 'ramp_return',1-x*x*(3-2*x)
    return 'hold_neutral',0.


def prepare(model,out,genesis):
    model=Path(model).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    tree=ET.parse(model);root=tree.getroot();locked=[];joints=[];references={}
    for node in root.findall('joint'):
        if node.get('type')=='fixed':continue
        name=node.get('name')
        if not is_hand(name):
            locked.append(name);node.set('type','fixed')
            for tag in ['axis','limit','dynamics']:
                for child in list(node.findall(tag)):node.remove(child)
            continue
        limit={k:float(v) for k,v in node.find('limit').attrib.items()};assert limit['lower']<=0<=limit['upper']
        mimic=node.find('mimic');joints.append(dict(name=name,type=node.get('type'),limit=limit,mimic=dict(mimic.attrib) if mimic is not None else None))
    assert len(locked)==29 and len(joints) in (14,24)
    for node in root.iter('mesh'):
        f=node.get('filename');assert not f.startswith('package://');p=(model.parent/f).resolve();assert p.is_file();references[str(p)]=sha(p);node.set('filename',str(p))
    tree.write(out/'fixture.urdf',encoding='utf-8',xml_declaration=True)
    drivers=[j for j in joints if not j['mimic']];followers=[j for j in joints if j['mimic']]
    for j in drivers:
        lo,hi=j['limit']['lower'],j['limit']['upper'];target=.04 if hi>=.04 else -.04;assert lo<=target<=hi;j['target_rad']=target
        assert 1.5*abs(target)<=j['limit']['velocity']
    for j in followers:
        m=j['mimic'];d=next(d for d in drivers if d['name']==m['joint']);a=float(m.get('multiplier',1));offset=float(m.get('offset',0));assert offset==0
        target=a*d['target_rad'];assert j['limit']['lower']<=target<=j['limit']['upper'];assert 1.5*abs(target)<=j['limit']['velocity']
    paths=['utils/urdf.py','engine/entities/rigid_entity/rigid_entity.py','engine/solvers/rigid/constraint/solver.py','engine/solvers/rigid/rigid_solver.py','engine/entities/rigid_entity/rigid_equality.py','options/solvers.py']
    plan=dict(schema='h1-fixed-body-hand-drive-probe/1',diagnostic_only=True,task_success=False,counts_as_H1_task_run=False,source_model=str(model),source_model_sha256=sha(model),fixture=str(out/'fixture.urdf'),fixture_sha256=sha(out/'fixture.urdf'),locked_body_joints=locked,transformation='29 non-hand body joints explicitly replaced by fixed joints; mesh paths made absolute; original hand joints/limits/mimic preserved',original_asset_modified=False,mesh_hashes=references,source_sha256=sha(__file__),genesis_source_hashes={str(Path(genesis)/p):sha(Path(genesis)/p) for p in paths},root_fixed=True,gravity=[0,0,0],floor=False,spawn_xyz=[0,0,1],collision=True,self_collision=True,enable_joint_limit=True,disable_constraint=False,constraint_solver='Newton',iterations=25,ls_iterations=50,sparse_solve=False,seed=0,physics_dt=.005,physics_steps=800,gpu_count=1,wall_seconds=1200,initialization='Original zero joint coordinates before first step; no pose writes or runtime resets',phases=[dict(name=phase(s)[0],first_step=s,last_step_exclusive=e) for s,e in [(0,100),(100,300),(300,500),(500,700),(700,800)]],trajectory='Cubic smoothstep 0→signed .04rad→0; driver-specific signs and URDF limits below',joint_units='rad; rad/s; N*m',driver_kp=20.,driver_kv=1.,followers_control='Zero direct control force, no position/velocity control; imported JOINT equality only',joints=joints,driver_names=[j['name'] for j in drivers],follower_names=[j['name'] for j in followers],criteria=dict(position_overshoot_rad=.001,speed_ratio=1.001,control_effort_ratio=1.001,mimic_max_residual_rad=.001,driver_final_hold_tracking_rad=.01),limitations=['Zero gravity, locked body and no floor isolate drive/coupling only','Not a grasp/contact, balance, hardware-motor or original-start task test'])
    write(out/'plan.json',plan);return plan


def run(planfile,out):
    import numpy as np
    import os,importlib.metadata,socket
    p=json.loads(Path(planfile).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=False);write(out/'plan.json',p);rows=[];start=time.monotonic()
    result=dict(schema='h1-fixed-body-hand-drive-result/1',diagnostic_only=True,task_success=False,full_witness=False,counts_as_H1_task_run=False,status='preflight',source_sha256=sha(__file__),plan_sha256=sha(planfile),physics_steps=0,probe_read_complete=False,local_response_criteria_passed=False)
    try:
        assert p['physics_steps']<=1000 and p['gpu_count']==1 and p['wall_seconds']<=1200
        assert sha(__file__)==p['source_sha256'] and sha(p['source_model'])==p['source_model_sha256'] and sha(p['fixture'])==p['fixture_sha256']
        for mapping in [p['mesh_hashes'],p['genesis_source_hashes']]:
            assert all(sha(f)==h for f,h in mapping.items())
        import torch,genesis as gs
        assert torch.cuda.is_available();gs.init(backend=gs.gpu,seed=p['seed'],logging_level='warning')
        opts=gs.options.RigidOptions(enable_collision=p['collision'],enable_self_collision=p['self_collision'],enable_joint_limit=p['enable_joint_limit'],disable_constraint=p['disable_constraint'],constraint_solver=gs.constraint_solver.Newton,iterations=p['iterations'],ls_iterations=p['ls_iterations'],sparse_solve=p['sparse_solve'])
        scene=gs.Scene(sim_options=gs.options.SimOptions(dt=p['physics_dt'],substeps=1,gravity=tuple(p['gravity'])),rigid_options=opts,show_viewer=False)
        robot=scene.add_entity(gs.morphs.URDF(file=p['fixture'],fixed=True,pos=tuple(p['spawn_xyz'])));scene.build()
        def arr(x):return x.detach().cpu().numpy() if hasattr(x,'detach') else np.asarray(x)
        names=[j['name'] for j in p['joints']];ix=[robot.get_joint(n).dof_idx_local for n in names];qx=[robot.get_joint(n).q_idx_local for n in names];di=[names.index(n) for n in p['driver_names']];fi=[names.index(n) for n in p['follower_names']];dix=[ix[i] for i in di]
        assert robot.n_dofs==len(names) and len(set(ix))==len(names);assert np.max(np.abs(arr(robot.get_qpos())[qx]))<1e-9
        eqs=[dict(name=e.name,type=str(e.type),objs=[e.eq_obj1id,e.eq_obj2id],data=arr(e.eq_data).tolist(),sol_params=arr(e.get_sol_params()).tolist()) for e in robot.equalities];assert len(eqs)==len(fi)
        expected={f"mimic_{j['name']}_to_{j['mimic']['joint']}":j for j in p['joints'] if j['mimic']}
        for e in eqs:
            j=expected[e['name']];assert abs(e['data'][1]-float(j['mimic']['multiplier']))<1e-9;assert e['objs']==[robot.get_joint(j['name']).idx,robot.get_joint(j['mimic']['joint']).idx]
        write(out/'runtime.json',dict(host=socket.gethostname(),job_id=os.environ.get('SLURM_JOB_ID'),device=torch.cuda.get_device_name(0),packages={n:importlib.metadata.version(n) for n in ['genesis-world','torch','numpy']},names=names,dof_indices=ix,qpos_indices=qx,equalities=eqs,rigid_options=robot._solver._options.model_dump(mode='json'),runtime_disable_constraint=bool(robot._solver._disable_constraint),runtime_equality_count=robot._solver.n_equalities,gravity=p['gravity'],floor=False,root_fixed=True))
        assert not robot._solver._disable_constraint and robot._solver.n_equalities==len(fi)
        effort=np.array([j['limit']['effort'] for j in p['joints']]);velocity=np.array([j['limit']['velocity'] for j in p['joints']]);lower=np.array([j['limit']['lower'] for j in p['joints']]);upper=np.array([j['limit']['upper'] for j in p['joints']]);target=np.array([p['joints'][i]['target_rad'] for i in di]);robot.set_dofs_force_range(-effort,effort,dofs_idx_local=ix);robot.set_dofs_kp(np.zeros(len(ix)),dofs_idx_local=ix);robot.set_dofs_kv(np.zeros(len(ix)),dofs_idx_local=ix);robot.set_dofs_kp(np.full(len(di),p['driver_kp']),dofs_idx_local=dix);robot.set_dofs_kv(np.full(len(di),p['driver_kv']),dofs_idx_local=dix)
        for step in range(p['physics_steps']+1):
            label,scale=phase(step);command=target*scale;robot.control_dofs_force(np.zeros(len(ix)),dofs_idx_local=ix);robot.control_dofs_position(command,dofs_idx_local=dix)
            q=arr(robot.get_qpos())[qx];v=arr(robot.get_dofs_velocity(dofs_idx_local=ix));tau=arr(robot.get_dofs_control_force(dofs_idx_local=ix));assert all(np.isfinite(x).all() for x in [q,v,tau,command]);residual={j['name']:float(q[i]-float(j['mimic'].get('multiplier',1))*q[names.index(j['mimic']['joint'])]-float(j['mimic'].get('offset',0))) for i,j in enumerate(p['joints']) if j['mimic']}
            rows.append(dict(step=step,time=step*p['physics_dt'],phase=label,driver_targets=command.tolist(),q=q.tolist(),qvel=v.tolist(),actual_control_force=tau.tolist(),mimic_residual=residual));result['physics_steps']=step
            if step==p['physics_steps']:break
            if time.monotonic()-start>p['wall_seconds']-20:raise RuntimeError('wall budget exhausted')
            scene.step()
        qs=np.array([r['q'] for r in rows]);vs=np.array([r['qvel'] for r in rows]);ts=np.array([r['actual_control_force'] for r in rows]);maxres=max([abs(x) for r in rows for x in r['mimic_residual'].values()] or [0.]);hold=qs[450:500,di];final=qs[750:801,di]
        metrics=dict(max_position_overshoot_rad=float(np.maximum(np.maximum(lower-qs,qs-upper),0).max()),max_speed_ratio=float((np.abs(vs)/velocity).max()),max_control_effort_ratio=float((np.abs(ts)/effort).max()),max_mimic_residual_rad=maxres,max_follower_direct_control_force_Nm=float(np.abs(ts[:,fi]).max()) if fi else 0.,max_driver_outward_hold_error_rad=float(np.abs(hold-target).max()),max_driver_return_hold_error_rad=float(np.abs(final).max()),per_driver_outward_mean_rad=dict(zip(p['driver_names'],hold.mean(axis=0).tolist())))
        c=p['criteria'];passed=metrics['max_position_overshoot_rad']<=c['position_overshoot_rad'] and metrics['max_speed_ratio']<=c['speed_ratio'] and metrics['max_control_effort_ratio']<=c['control_effort_ratio'] and maxres<=c['mimic_max_residual_rad'] and metrics['max_follower_direct_control_force_Nm']==0 and max(metrics['max_driver_outward_hold_error_rad'],metrics['max_driver_return_hold_error_rad'])<=c['driver_final_hold_tracking_rad']
        result.update(status='complete_local_diagnostic',probe_read_complete=True,local_response_criteria_passed=bool(passed),metrics=metrics,recorded_states=len(rows))
    except Exception as exc:result.update(status='diagnostic_error',error=dict(type=type(exc).__name__,message=str(exc)))
    finally:
        with (out/'states.jsonl').open('w') as f:
            for row in rows:f.write(json.dumps(row,allow_nan=False)+'\n')
        identity=sha(__file__)==p['source_sha256'] and sha(p['fixture'])==p['fixture_sha256'] and sha(p['source_model'])==p['source_model_sha256'] and all(sha(f)==h for mapping in [p['mesh_hashes'],p['genesis_source_hashes']] for f,h in mapping.items())
        result.update(wall_seconds=time.monotonic()-start,post_identity_intact=identity,state_sha256=sha(out/'states.jsonl'))
        result['probe_read_complete']=result['probe_read_complete'] and identity and len(rows)==p['physics_steps']+1
        result['local_response_criteria_passed']=result['local_response_criteria_passed'] and result['probe_read_complete']
        write(out/'result.json',result);write(out/'manifest.json',dict(files_sha256={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='manifest.json'},task_success=False,diagnostic_only=True))
    return result


def main():
    parser=argparse.ArgumentParser(__doc__);sub=parser.add_subparsers(dest='mode',required=True);a=sub.add_parser('prepare');a.add_argument('model');a.add_argument('out');a.add_argument('--genesis',required=True);a=sub.add_parser('run');a.add_argument('plan');a.add_argument('out');args=parser.parse_args()
    result=prepare(args.model,args.out,args.genesis) if args.mode=='prepare' else run(args.plan,args.out);print(json.dumps({k:result.get(k) for k in ['status','physics_steps','probe_read_complete','local_response_criteria_passed']}));return 0 if result.get('status')!='diagnostic_error' else 2
if __name__=='__main__':raise SystemExit(main())
