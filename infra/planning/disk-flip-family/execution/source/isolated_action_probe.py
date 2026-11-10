"""Exercise a real process boundary. This is not hostile-code sandboxing or a task witness."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
import mujoco
from .reference_interface import JointReferenceInterface, ActionRejected
from .run import Attempt

CHILD = r'''
import json,sys
for line in sys.stdin:
 request=json.loads(line);action=request['action'];kind=request['case']
 if kind=='object_pose':action['object_pose']=[.5,0,.866]
 elif kind=='model_edit':action['friction']=100
 elif kind=='stage_write':action['success']=True
 elif kind=='unknown_joint':action['targets']['disk_free']=0
 elif kind=='nonfinite':action['targets'][next(iter(action['targets']))]=float('nan')
 elif kind=='slew':action['targets'][next(iter(action['targets']))]+=10
 elif kind=='partial':action['targets'].pop(next(iter(action['targets'])))
 print(json.dumps(action),flush=True)
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 root=args.run;binding=json.loads((root/'model-binding.json').read_text());init=json.loads((root/'initial_state.json').read_text());plan=json.loads((root/'plan.json').read_text())
 a=Attempt.__new__(Attempt);a.m=mujoco.MjModel.from_xml_path(str(root/'scene.xml'));a.d=mujoco.MjData(a.m);a.d.qpos[:]=init['qpos'];a.d.qvel[:]=init['qvel'];mujoco.mj_forward(a.m,a.d)
 a.body=binding['body'];a.profile=binding['object_profile'];a.obj=a.m.body('disk').id;a.table=a.m.geom('table').id;a.ground=a.m.geom('ground').id;a.dt=float(a.m.opt.timestep);a.qref=a.d.qpos.copy();a.joints={a.m.joint(j).name:j for j in range(a.m.njnt) if a.m.joint(j).name!='disk_free'};a.actj=a.m.actuator_trnid[:,0];a.mode='position' if a.body=='S' else 'torque';a.tuning=plan['controller_tuning'];a.phase='settle';a.peaks={k:0. for k in ['speed','angular','robot','table','local','self_contact','robot_table']};a.hold=a.unsupported=0.;a.success=a.seen_lift=a.seen_flip=False
 gateway=JointReferenceInterface(a.m,a.qref,a.body);child=subprocess.Popen([sys.executable,'-I','-S','-u','-c',CHILD],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 def exchange(kind):
  child.stdin.write(json.dumps(dict(case=kind,action=gateway.encode(a.qref)))+'\n');child.stdin.flush();return json.loads(child.stdout.readline(65536))
 cases=[]
 try:
  for kind in ['object_pose','model_edit','stage_write','unknown_joint','nonfinite','slew','partial']:
   before=(a.d.qpos.copy(),a.d.qvel.copy(),gateway.reference.copy(),a.d.time);rejected=False
   try:gateway.accept(exchange(kind))
   except ActionRejected:rejected=True
   unchanged=np.array_equal(before[0],a.d.qpos) and np.array_equal(before[1],a.d.qvel) and np.array_equal(before[2],gateway.reference) and before[3]==a.d.time
   cases.append(dict(case=kind,rejected=rejected,physics_and_reference_unchanged=bool(unchanged)))
  failure=None
  try:
   for _ in range(150):
    a.qref=gateway.accept(exchange('noop'))
    for _ in range(round(.02/a.dt)):a.command();mujoco.mj_step(a.m,a.d);a.assess()
  except RuntimeError as e:failure=str(e)
 finally:
  child.stdin.close();child.wait(timeout=10)
 report=dict(schema='disk-flip-isolated-boundary-probe/1',setting=root.name,body=a.body,separate_python_process=True,policy_python_isolated_mode=True,shared_simulator_memory=False,transport='JSON lines over anonymous pipes',negative_cases=cases,no_op=dict(simulated_seconds=float(a.d.time),task_success=bool(a.success),physical_violation=failure,peaks=a.peaks),passed=all(c['rejected'] and c['physics_and_reference_unchanged'] for c in cases) and not a.success,scope='Process-separated malformed-action and physical no-op tests only. Not a complete task execution, OS sandbox, or hostile-code security certificate.',complete_isolated_execution=False,scene_sha256=hashlib.sha256((root/'scene.xml').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
