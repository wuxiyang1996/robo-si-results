"""Run the frozen privileged closed-loop expert in a separate Python process.

The child receives read-only observations and emits joint targets. Only the parent
owns Genesis and the scorer. This is process separation, not an OS sandbox.
"""
import argparse,copy,hashlib,json,subprocess,sys
from dataclasses import asdict
from pathlib import Path


def child_main(snapshot):
 protocol=sys.stdout;sys.stdout=sys.stderr
 sys.path.insert(0,str(snapshot))
 import numpy as np
 import torch
 from humanoid.g1_tabletop_disk_flip.solution.run import read_config
 from humanoid.g1_tabletop_disk_flip.solution import controller
 class RobotReadView:
  def __init__(self,env):self.env=env
  def get_dofs_position(self,dofs):return torch.tensor(self.env.current['observation']['joint_position'],dtype=torch.float32)
  def get_dofs_velocity(self,dofs):return torch.tensor(self.env.current['observation']['joint_velocity'],dtype=torch.float32)
 class ReadView:
  def __init__(self,initial):
   self.cfg=read_config(initial['config']);self.base_position=tuple(initial['base_position']);self.kp=torch.tensor(initial['kp'],dtype=torch.float32);self.effort=torch.tensor(initial['effort'],dtype=torch.float32);self.sim_dt=initial['sim_dt'];self.dofs=list(range(43));self.robot=RobotReadView(self);self.update(initial)
  def update(self,message):
   self.current=message;self.status=copy.deepcopy(message['status']);self.physics_steps=message['physics_steps'];self.target=torch.tensor(message['target'],dtype=torch.float32)
  def observe(self):return copy.deepcopy(self.current['observation'])
  def state(self):return copy.deepcopy(self.current['observation']['objects'])
  def step_targets(self,target):
   protocol.write(json.dumps(dict(type='joint_reference',targets=np.asarray(target).tolist(),phase=self.controller.phase),allow_nan=False)+'\n');protocol.flush();message=json.loads(sys.stdin.readline());self.update(message)
   return self.observe(),message['reward'],self.status['terminated'],copy.deepcopy(self.status)
 try:
  initial=json.loads(sys.stdin.readline())
  if initial.get('run_boundary_probes'):
   for kind in ['object_pose','model_edit','stage_write','nonfinite','out_of_range','partial','wrong_type']:
    action=dict(type='joint_reference',targets=initial['target'].copy(),phase='boundary_probe')
    if kind=='object_pose':action['object_pose']=[.5,0,.866]
    elif kind=='model_edit':action['friction']=100
    elif kind=='stage_write':action['success']=True
    elif kind=='nonfinite':action['targets'][0]=float('nan')
    elif kind=='out_of_range':action['targets'][0]=1e6
    elif kind=='partial':action['targets'].pop()
    elif kind=='wrong_type':action['targets'][0]=True
    protocol.write(json.dumps(action)+'\n');protocol.flush()
    if json.loads(sys.stdin.readline())!={'rejected':True}:raise RuntimeError('boundary probe was not rejected')
  env=ReadView(initial);c=controller.GentleController(env);env.controller=c;controller.run(c)
  protocol.write(json.dumps(dict(type='finished',events=c.events,steps=c.steps))+'\n');protocol.flush();return 0
 except Exception as e:
  import traceback;traceback.print_exc();protocol.write(json.dumps(dict(type='error',message=repr(e)))+'\n');protocol.flush();return 1


def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--snapshot',type=Path);p.add_argument('--child',action='store_true');a=p.parse_args();base=Path(__file__).resolve().parent;snapshot=(a.snapshot or base/'snapshots/original-expert-v2').resolve()
 if a.child:return child_main(snapshot)
 assert a.output is not None;a.output=a.output.resolve();assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
 sys.path.insert(0,str(snapshot))
 import numpy as np
 from humanoid.g1_tabletop_disk_flip.solution import controller,run
 native_expert=controller.run;transport_hash=hashlib.sha256();count=0;child_status=None;negative_cases=[]
 stderr_path=a.output.parent/(a.output.name+'-policy-stderr.log')
 def validate(env,action):
  if not isinstance(action,dict) or set(action)!={'type','targets','phase'} or action['type']!='joint_reference':raise ValueError('only joint targets and logging phase are accepted')
  if not isinstance(action['phase'],str) or len(action['phase'])>256:raise ValueError('invalid logging phase')
  values=action['targets']
  if not isinstance(values,list) or len(values)!=43 or any(isinstance(x,bool) or not isinstance(x,(float,int)) for x in values):raise ValueError('invalid joint vector')
  target=np.asarray(values,dtype=float)
  if not np.isfinite(target).all() or np.any(target<env.lo.detach().cpu().numpy()) or np.any(target>env.hi.detach().cpu().numpy()):raise ValueError('joint range or finiteness violation')
  return target
 def bridge(c):
  nonlocal count,child_status
  env=c.env
  def observation(reward=0.):
   return dict(observation=env.observe(),status=env.status,physics_steps=env.physics_steps,target=env.target.detach().cpu().numpy().tolist(),reward=reward)
  with stderr_path.open('w') as errors:
   child=subprocess.Popen([sys.executable,'-I','-u',str(Path(__file__).resolve()),'--child','--snapshot',str(snapshot)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
   initial=observation();initial.update(run_boundary_probes=True,config=asdict(env.cfg),base_position=list(env.base_position),kp=env.kp.detach().cpu().numpy().tolist(),effort=env.effort.detach().cpu().numpy().tolist(),sim_dt=env.sim_dt)
   child.stdin.write(json.dumps(initial)+'\n');child.stdin.flush()
   try:
    for kind in ['object_pose','model_edit','stage_write','nonfinite','out_of_range','partial','wrong_type']:
     before=json.dumps(observation(),sort_keys=True);response=json.loads(child.stdout.readline(65536));rejected=False
     try:validate(env,response)
     except ValueError:rejected=True
     unchanged=before==json.dumps(observation(),sort_keys=True)
     negative_cases.append(dict(case=kind,rejected=rejected,physical_state_and_reference_unchanged=unchanged))
     if not rejected or not unchanged:raise RuntimeError('boundary probe failed: '+kind)
     child.stdin.write('{"rejected":true}\n');child.stdin.flush()
    while True:
     line=child.stdout.readline(1024*1024)
     if not line:raise RuntimeError('policy process ended without a terminal message')
     action=json.loads(line)
     if action.get('type')=='error':raise RuntimeError('policy error: '+action['message'])
     if action.get('type')=='finished':
      if set(action)!={'type','events','steps'} or action['steps']!=count:raise ValueError('invalid terminal policy metadata')
      c.events=action['events'];break
     target=validate(env,action)
     # Native step_targets applies the unchanged 0.5 rad/s reference slew and
     # bounded torque law. The child cannot set qpos, contact or scorer state.
     obs,reward,done,status=env.step_targets(target);count+=1;transport_hash.update(line.encode());c.phase=action['phase'];c.last_observation=obs
     if c.on_step is not None:c.on_step(target,obs,reward,status,action['phase'])
     child.stdin.write(json.dumps(observation(reward))+'\n');child.stdin.flush()
   finally:
    child.stdin.close()
    try:child.wait(timeout=20)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=10)
    child_status=child.returncode
 controller.run=bridge;sys.argv=['frozen-expert','--output',str(a.output),'--backend','cpu','--seed','0','--video']
 try:code=run.main()
 finally:controller.run=native_expert
 summary=json.loads((a.output/'summary.json').read_text());report=dict(schema='disk-flip-isolated-closed-loop/1',snapshot='original-expert-v2',separate_process=True,policy_is_closed_loop=True,privileged_read_only_observations=True,shared_simulator_memory=False,negative_cases=negative_cases,negative_cases_passed=len(negative_cases)==7 and all(x['rejected'] and x['physical_state_and_reference_unchanged'] for x in negative_cases),commands_from_child=count,policy_exit_code=child_status,transport_sha256=transport_hash.hexdigest(),adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full_task_success=summary['full_task_success'],passed=bool(code==0 and child_status==0 and summary['full_task_success']),scope='Frozen expert receives read-only state over JSON and computes targets online in a child process; trusted parent owns native physics/scoring and actuator limits. Not an OS security sandbox, public-agent score, human signoff, or second-person reproduction.')
 (a.output/'closed-loop-adapter.py').write_bytes(Path(__file__).read_bytes());(a.output/'isolated-execution.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return code
if __name__=='__main__':raise SystemExit(main())
