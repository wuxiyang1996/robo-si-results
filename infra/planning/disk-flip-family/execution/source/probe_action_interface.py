"""Adversarial payload checks against the real imported model and reference boundary."""
import argparse,copy,json
from pathlib import Path
import mujoco,numpy as np
from .reference_interface import JointReferenceInterface,ActionRejected

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();m=mujoco.MjModel.from_xml_path(str(a.run/'scene.xml'));init=json.loads((a.run/'initial_state.json').read_text());body=json.loads((a.run/'model-binding.json').read_text())['body'];api=JointReferenceInterface(m,init['qpos'],body);valid=api.encode(api.reference);api.accept(valid);name=next(n for n,j in api.joints.items() if m.jnt_limited[j]);cases={}
 for kind in ['object_pose','model_edit','unknown_joint','nan','joint_limit','slew_limit','partial_commit']:
  payload=copy.deepcopy(valid)
  if kind=='object_pose':payload['qpos']=init['qpos']
  elif kind=='model_edit':payload['physics_dt']=1.
  elif kind=='unknown_joint':payload['targets']['disk_free']=0.
  elif kind=='nan':payload['targets'][name]=float('nan')
  elif kind=='joint_limit':payload['targets'][name]=float(m.jnt_range[api.joints[name],1])+1.
  elif kind=='slew_limit':payload['targets'][name]+=.03
  else:
   names=list(payload['targets']);payload['targets'][names[0]]+=.0001;payload['targets'][names[-1]]=float('inf')
  before=api.reference.copy()
  try:api.accept(payload);rejected=False
  except ActionRejected:rejected=True
  cases[kind]={'rejected':rejected,'state_unchanged':bool(np.array_equal(api.reference,before))}
 assert all(r['rejected'] and r['state_unchanged'] for r in cases.values())
 report={'schema':'disk-flip-action-interface-probes/1','model':str(a.run/'scene.xml'),'body':body,'valid_noop_accepted':True,'negative_cases':cases,'scope':'Action parser and atomic reference state only; not a physics success, process isolation or whole-task integrity certificate'}
 out=Path(__file__).resolve().parent/'acceptance'/f'action-interface-{body}.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
