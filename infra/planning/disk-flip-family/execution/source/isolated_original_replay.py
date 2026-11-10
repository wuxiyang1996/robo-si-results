"""Full recorded-policy execution over a process boundary; no OS sandbox claim."""
import argparse,datetime,gzip,hashlib,json,math,subprocess,sys
from pathlib import Path
import numpy as np

CHILD=r'''
import gzip,json,sys
with gzip.open(sys.argv[1],'rt') as commands:
 for request in sys.stdin:
  message=json.loads(request)
  if message=={'type':'next'}:
   line=commands.readline()
   if not line:raise RuntimeError('recorded policy exhausted')
   print(line.rstrip(),flush=True)
  elif message.get('type')=='probe':
   action=message['action'];kind=message['case']
   if kind=='object_pose':action['object_pose']=[.5,0,.866]
   elif kind=='model_edit':action['friction']=100
   elif kind=='stage_write':action['success']=True
   elif kind=='nonfinite':action['targets'][0]=float('nan')
   elif kind=='slew':action['targets'][0]+=.1
   elif kind=='partial':action['targets'].pop()
   elif kind=='wrong_type':action['targets'][0]=True
   else:raise ValueError('unknown probe')
   print(json.dumps(action),flush=True)
  else:raise ValueError('invalid request')
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.source=a.source.resolve();a.output=a.output.resolve();assert not a.output.exists()
 base=Path(__file__).resolve().parent;snapshot=base/'snapshots/original-expert-v2';sys.path.insert(0,str(snapshot))
 from humanoid.g1_tabletop.genesis_env import G1TabletopGenesis
 from humanoid.g1_tabletop_disk_flip.solution import run
 commands=np.load(a.source/'trajectory.npz')['targets'];inputs=a.output.parent/(a.output.name+'-policy-input.jsonl.gz');assert not inputs.exists()
 inputs.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(inputs,'wt') as f:
  for target in commands:f.write(json.dumps(dict(type='joint_reference',targets=target.tolist()),allow_nan=False)+'\n')
 child=subprocess.Popen([sys.executable,'-I','-S','-u','-c',CHILD,str(inputs)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 native=G1TabletopGenesis.step_targets;count=0;transport_hash=hashlib.sha256();error=None;negative_cases=[]
 def validate(env,action):
  if not isinstance(action,dict) or set(action)!={'type','targets'} or action['type']!='joint_reference':raise ValueError('only joint references accepted')
  values=action['targets']
  if not isinstance(values,list) or len(values)!=43 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):raise ValueError('invalid joint vector')
  target=np.asarray(values,dtype=np.float32);lo=env.lo.detach().cpu().numpy();hi=env.hi.detach().cpu().numpy();previous=env.target.detach().cpu().numpy()
  if np.any(target<lo) or np.any(target>hi):raise ValueError('joint limits')
  if np.max(np.abs(target-previous))>env.cfg.control_dt*env.cfg.joint_target_speed_max+1e-5:raise ValueError('reference slew')
  return target
 def probe(env):
  def state():
   return json.dumps(dict(objects=env.state(),status=env.status,joints=env.robot.get_dofs_position(env.dofs).detach().cpu().numpy().tolist(),velocity=env.robot.get_dofs_velocity(env.dofs).detach().cpu().numpy().tolist(),reference=env.target.detach().cpu().numpy().tolist()),sort_keys=True)
  for kind in ['object_pose','model_edit','stage_write','nonfinite','slew','partial','wrong_type']:
   before=state();action=dict(type='joint_reference',targets=env.target.detach().cpu().numpy().tolist());child.stdin.write(json.dumps(dict(type='probe',case=kind,action=action))+'\n');child.stdin.flush();response=json.loads(child.stdout.readline(65536));rejected=False
   try:validate(env,response)
   except ValueError:rejected=True
   unchanged=state()==before;negative_cases.append(dict(case=kind,rejected=rejected,physical_state_and_reference_unchanged=unchanged))
   if not rejected or not unchanged:raise RuntimeError('negative action probe failed')
 def step(env,expected):
  nonlocal count
  if count==0:probe(env)
  child.stdin.write('{"type":"next"}\n');child.stdin.flush();line=child.stdout.readline(65536);target=validate(env,json.loads(line))
  if not np.array_equal(target,expected):raise ValueError('recorded policy differs from frozen reference')
  transport_hash.update(line.encode());count+=1
  return native(env,target)
 G1TabletopGenesis.step_targets=step
 sys.argv=['frozen-recording','--output',str(a.output),'--backend','cpu','--seed','0','--video','--replay',str(a.source/'trajectory.npz')]
 try:code=run.main()
 except Exception as e:error=repr(e);code=1
 finally:
  G1TabletopGenesis.step_targets=native;child.stdin.close();child.wait(timeout=15)
 if not a.output.exists():raise RuntimeError(error or 'native runner created no output')
 summary=json.loads((a.output/'summary.json').read_text()) if (a.output/'summary.json').exists() else {}
 report=dict(schema='disk-flip-isolated-recorded-policy/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=str(a.source),source_trajectory_sha256=hashlib.sha256((a.source/'trajectory.npz').read_bytes()).hexdigest(),adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),policy_input_sha256=hashlib.sha256(inputs.read_bytes()).hexdigest(),transport_sha256=transport_hash.hexdigest(),negative_cases=negative_cases,negative_cases_passed=len(negative_cases)==7 and all(c['rejected'] and c['physical_state_and_reference_unchanged'] for c in negative_cases),commands_from_child=count,expected_commands=len(commands),separate_process=True,shared_simulator_memory=False,transport='strict JSON joint references over anonymous pipes',full_task_success=summary.get('full_task_success',False),native_independent_replay_verified=summary.get('independent_action_replay_verified',False),passed=bool(code==0 and count==len(commands) and summary.get('independent_action_replay_verified') and child.returncode==0),error=error,scope='Fresh full execution of a frozen recorded open-loop expert policy. The child emits references; the trusted parent owns physics/scoring and rejects malformed or out-of-range actions. This is not a closed-loop expert in isolation, an OS sandbox, human review, or second-person reproduction.')
 (a.output/'transport-adapter.py').write_bytes(Path(__file__).read_bytes());(a.output/'isolated-execution.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return code
if __name__=='__main__':raise SystemExit(main())
