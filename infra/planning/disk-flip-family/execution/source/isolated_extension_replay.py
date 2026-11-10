"""Complete process-separated recorded policy; not an online closed-loop expert.

The child can send joint references only. The parent owns dynamics, actuator
limits and scoring. Every physics array must match a separately verified run.
"""
import argparse, ast, hashlib, inspect, json, subprocess, sys
from pathlib import Path
import mujoco
import numpy as np
from .run import Attempt
from .reference_interface import JointReferenceInterface, ActionRejected

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen_methods_match(source):
 tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Attempt')
 for name in ['command','assess','contacts']:
  node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
  import textwrap
  current=ast.parse(textwrap.dedent(inspect.getsource(getattr(Attempt,name)))).body[0]
  assert ast.dump(node)==ast.dump(current),f'Frozen physical method changed: {name}'

def child(packet):
 z=np.load(packet);initial=json.loads(sys.stdin.readline());action=initial['action'];names=initial['joint_qpos_addresses']
 for kind in ['object_pose','model_edit','stage_write','unknown_joint','nonfinite','slew','partial']:
  probe=json.loads(json.dumps(action));key=next(iter(probe['targets']))
  if kind=='object_pose':probe['object_pose']=[.5,0,.866]
  elif kind=='model_edit':probe['friction']=100
  elif kind=='stage_write':probe['success']=True
  elif kind=='unknown_joint':probe['targets']['disk_free']=0
  elif kind=='nonfinite':probe['targets'][key]=float('nan')
  elif kind=='slew':probe['targets'][key]+=10
  else:probe['targets'].pop(key)
  print(json.dumps(probe),flush=True);assert json.loads(sys.stdin.readline())=={'rejected':True}
 for ref in z['reference']:
  print(json.dumps({'type':'joint_reference','targets':{name:float(ref[i]) for name,i in names.items()}}),flush=True)
  assert json.loads(sys.stdin.readline())=={'accepted':True}
 return 0

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path);p.add_argument('--child',action='store_true');args=p.parse_args();root=args.run.resolve()
 if args.child:return child(root/'trajectory-reference.npz')
 assert args.output and not args.output.exists();args.output.mkdir(parents=True)
 read=lambda name:json.loads((root/name).read_text())
 verification=read('verification.json');meta=read('trajectory-reference.json');exact=read('reference-replay-verification.json');summary=read('summary.json')
 assert verification['task_success'] and verification['replay_matches'] and exact['all_physics_state_and_control_array_hashes_match']
 assert all(sha(root/n)==h for n,h in summary['source_hashes'].items());frozen_methods_match(root/'run.py')
 a=Attempt.__new__(Attempt);a.m=mujoco.MjModel.from_xml_path(str(root/'scene.xml'));a.d=mujoco.MjData(a.m);init=read('initial_state.json');a.d.qpos[:]=init['qpos'];a.d.qvel[:]=init['qvel'];mujoco.mj_forward(a.m,a.d)
 a.body=summary['binding']['body'];a.profile=summary['binding']['object_profile'];a.obj=a.m.body('disk').id;a.table=a.m.geom('table').id;a.ground=a.m.geom('ground').id;a.dt=float(a.m.opt.timestep);a.qref=a.d.qpos.copy();a.joints={a.m.joint(j).name:j for j in range(a.m.njnt) if a.m.joint(j).name!='disk_free'};a.actj=a.m.actuator_trnid[:,0];a.mode='position' if a.body=='S' else 'torque';a.tuning=meta['controller_tuning'];a.phase='settle';a.peaks={k:0. for k in ['speed','angular','robot','table','local','self_contact','robot_table']};a.hold=a.unsupported=0.;a.success=a.seen_lift=a.seen_flip=False
 gateway=JointReferenceInterface(a.m,a.qref,a.body);packet=np.load(root/'trajectory-reference.npz');hashes={k:hashlib.sha256() for k in ['qpos','qvel','ctrl']};transport=hashlib.sha256();cases=[];step=count=0;error=None
 with (args.output/'policy-stderr.log').open('w') as errors:
  process=subprocess.Popen([sys.executable,'-u','-m','df_family.isolated_extension_replay',str(root),'--child'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
  def send(data):process.stdin.write(json.dumps(data)+'\n');process.stdin.flush()
  send(dict(action=gateway.encode(a.qref),joint_qpos_addresses={n:int(a.m.jnt_qposadr[j]) for n,j in gateway.joints.items()}))
  try:
   for kind in ['object_pose','model_edit','stage_write','unknown_joint','nonfinite','slew','partial']:
    before=(a.d.qpos.copy(),a.d.qvel.copy(),gateway.reference.copy(),a.d.time);rejected=False
    try:gateway.accept(json.loads(process.stdout.readline(65536)))
    except ActionRejected:rejected=True
    unchanged=np.array_equal(before[0],a.d.qpos) and np.array_equal(before[1],a.d.qvel) and np.array_equal(before[2],gateway.reference) and before[3]==a.d.time
    cases.append(dict(case=kind,rejected=rejected,physics_and_reference_unchanged=bool(unchanged)));assert rejected and unchanged;send({'rejected':True})
   for end,phase in zip(packet['physics_step'],packet['phase']):
    line=process.stdout.readline(65536);a.qref=gateway.accept(json.loads(line));transport.update(line.encode());a.phase=str(phase)
    if a.body=='S':a.command()
    while step<int(end):
     if a.body!='S':a.command()
     mujoco.mj_step(a.m,a.d);a.assess()
     for key,h in hashes.items():h.update(np.ascontiguousarray(getattr(a.d,key)).tobytes())
     step+=1
    count+=1;send({'accepted':True})
    if count%1000==0:print(json.dumps(dict(commands=count,simulated_seconds=float(a.d.time))),flush=True)
  except Exception as e:error=repr(e)
  finally:
   process.stdin.close()
   try:process.wait(timeout=15)
   except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
 actual={k:h.hexdigest() for k,h in hashes.items()};same=actual==meta['full_array_sha256'];passed=not error and process.returncode==0 and bool(a.success) and same and count==len(packet['reference'])
 report=dict(schema='disk-flip-isolated-recorded-policy/1',setting=summary['setting'],passed=passed,complete_isolated_execution=passed,policy_is_closed_loop=False,separate_python_process=True,shared_simulator_memory=False,commands_from_child=count,physics_steps=step,simulated_seconds=float(a.d.time),task_success=bool(a.success),negative_cases=cases,negative_cases_passed=len(cases)==7 and all(x['rejected'] and x['physics_and_reference_unchanged'] for x in cases),all_physics_state_and_control_array_hashes_match=same,actual_sha256=actual,baseline_verification_sha256=sha(root/'verification.json'),reference_packet_sha256=sha(root/'trajectory-reference.npz'),scene_sha256=sha(root/'scene.xml'),transport_sha256=transport.hexdigest(),adapter_sha256=sha(Path(__file__)),policy_exit_code=process.returncode,error=error,scope='Complete fresh execution through the process boundary using a recorded reference policy. Parent owns dynamics and scoring. Exact array equality binds the existing independently verified trajectory/video and high-low mapping. Not a closed-loop child expert, OS sandbox, public-agent result or external signoff.')
 (args.output/'adapter.py').write_bytes(Path(__file__).read_bytes());(args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
