"""A new MuJoCo execution of original joint references; no success is transferred across engines."""
import argparse,hashlib,json,shutil,traceback
from pathlib import Path
import numpy as np
from .run import Attempt,write
class ReferenceAttempt(Attempt):
 def command(self):
  for a,j in enumerate(self.actj):
   name=self.m.joint(int(j)).name;qi=self.m.jnt_qposadr[j];vi=self.m.jnt_dofadr[j]
   kp,kd=(2.4,.25) if 'hand' in name else (14.,1.5) if 'wrist' in name else (40.,5.) if any(k in name for k in ['shoulder','elbow']) else (150.,8.) if 'waist' in name else (160.,6.) if 'knee' in name else (100.,5.)
   effort=max(abs(self.m.actuator_ctrlrange[a]));self.d.ctrl[a]=np.clip(kp*(self.qref[qi]-self.d.qpos[qi])-kd*self.d.qvel[vi],-effort,effort)
 def execute(self):
  source=self.args.reference;initial=json.loads((source/'initial_state.json').read_text());z=np.load(source/'trajectory.npz');mapping=json.loads((source/'high-low-trajectory.json').read_text())
  if len(initial['joint_names'])!=len(self.actj):raise ValueError('Actuator identity mismatch')
  self.plan['high_level']=list(dict.fromkeys(row['high_level'] for row in mapping));self.plan['low_level']=[{k:row[k] for k in ['id','phase','high_level','action']} for row in mapping]
  self.plan['strategy']='Execute frozen original expert joint references as a NEW physical candidate under the extension scene and scorer. This is a reference program, not online replanning or a transferred success claim.'
  self.plan['reference_source']={'run':source.name,'trajectory_sha256':hashlib.sha256((source/'trajectory.npz').read_bytes()).hexdigest(),'original_engine':'Genesis','execution_engine':'MuJoCo','extension_generated_start_unchanged':True,'pd':'original stiffness/damping schedule, bounded torques, no added gravity force'}
  write(self.out/'plan.json',self.plan)
  for name in ['trajectory.npz','initial_state.json','high-low-trajectory.json']:shutil.copyfile(source/name,self.out/('reference-'+name))
  shutil.copyfile(__file__,self.out/'reference_candidate.py')
  names=initial['joint_names'];qids=np.array([self.m.jnt_qposadr[self.joints[n]] for n in names]);phase_for={i:row['phase'] for row in mapping for i in range(*row['command_slice'])}
  for i,target in enumerate(z['targets']):
   phase=phase_for[i]
   if not self.events or phase!=self.phase:
    if self.events:self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
    self.phase=phase;self.events.append({'phase':phase,'start_s':float(self.d.time),'record_start':len(self.records)})
   self.qref[qids]=target;self.step()
  if self.events:self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def finish(self,error):
  super().finish(error);summary=json.loads((self.out/'summary.json').read_text())
  for name in ['reference_candidate.py','reference-trajectory.npz','reference-initial_state.json','reference-high-low-trajectory.json']:
   if (self.out/name).exists():summary['source_hashes'][name]=hashlib.sha256((self.out/name).read_bytes()).hexdigest()
  summary['controller']='recorded original references, executed anew under MuJoCo extension protocol';write(self.out/'summary.json',summary)
def main():
 p=argparse.ArgumentParser();p.add_argument('--setting',default='DF-04-G',choices=['DF-04-G']);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,default=Path('df_family/runs/DF-01-G-a02'));p.add_argument('--tuning',type=Path,default=Path('df_family/tuning/reference-candidate.json'));a=p.parse_args();run=ReferenceAttempt(a);error=None
 try:run.execute()
 except Exception as exc:error=str(exc);(a.output/'error.txt').write_text(traceback.format_exc())
 finally:run.finish(error)
 return 0 if run.success and error is None else 1
if __name__=='__main__':raise SystemExit(main())
