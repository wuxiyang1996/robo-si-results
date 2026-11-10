"""Checkpoint-initialized diagnostics only. These are never full task witnesses."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
import mujoco
from .run import Attempt,write
from .reference_interface import JointReferenceInterface
class Probe(Attempt):
 def __init__(self,args):
  if args.checkpoint_json and args.checkpoint_json.name=='final-state.json':
   diagnosis=args.checkpoint_json.parent/'diagnostic.json'
   if diagnosis.exists():
    failure=json.loads(diagnosis.read_text()).get('failure')
    physical_failures={'disk_linear_speed','disk_angular_speed','robot_contact_load','table_contact_load','local_damage_proxy','disk_dropped','disk_ground_contact','robot_table_collision','robot_self_collision','nonfinite_physics','uncontrolled_contact_loss'}
    reason=failure.removeprefix('RuntimeError: ') if isinstance(failure,str) else failure
    if reason in physical_failures:raise ValueError(f'Checkpoint is the final state of a physical failure ({failure}); choose a saved valid earlier checkpoint')
  self.out=args.output;self.out.mkdir(parents=True,exist_ok=False)
  source=args.run;meta=json.loads((source/'model-binding.json').read_text());self.body=meta['body'];self.profile=meta['object_profile'];self.tuning=json.loads((source/'plan.json').read_text())['controller_tuning']
  if args.tuning:self.tuning.update(json.loads(args.tuning.read_text()))
  self.m=mujoco.MjModel.from_xml_path(str(source/'scene.xml'));self.d=mujoco.MjData(self.m);self.ikm=mujoco.MjModel.from_xml_path(str(source/'scene.xml'));self.ik=mujoco.MjData(self.ikm)
  for g in range(self.ikm.ngeom):
   if 'wrist' in self.ikm.body(int(self.ikm.geom_bodyid[g])).name and self.ikm.geom_contype[g]:self.ikm.geom_margin[g]=.004
  i=None
  if not args.checkpoint_json:
   z=np.load(source/'trajectory.npz');assert args.time<=float(z['time'][-1])+1e-9,'Requested checkpoint exceeds recorded trajectory';i=min(np.searchsorted(z['time'],args.time-1e-8),len(z['time'])-1);self.d.qpos[:]=z['qpos'][i];self.d.qvel[:]=z['qvel'][i];self.d.ctrl[:]=z['ctrl'][i];self.d.time=float(z['time'][i]);self.qref=z['reference'][i].copy();self.last_ref=self.qref.copy();mujoco.mj_forward(self.m,self.d)
  if args.checkpoint_json:
   checkpoint=json.loads(args.checkpoint_json.read_text());self.d.qpos[:]=checkpoint['qpos'];self.d.qvel[:]=checkpoint['qvel'];self.qref=np.array(checkpoint['reference']);self.last_ref=self.qref.copy();self.d.time=checkpoint['time'];mujoco.mj_forward(self.m,self.d)
  self.obj=self.m.body('disk').id;self.objj=self.m.joint('disk_free').id;self.objq=self.m.jnt_qposadr[self.objj];self.objv=self.m.jnt_dofadr[self.objj];self.table=self.m.geom('table').id;self.ground=self.m.geom('ground').id;self.joints={self.m.joint(j).name:j for j in range(self.m.njnt) if j!=self.objj};self.actj=self.m.actuator_trnid[:,0];self.mode='position' if self.body=='S' else 'torque';self.action_interface=JointReferenceInterface(self.m,self.qref,self.body)
  if args.physics_dt:self.m.opt.timestep=args.physics_dt
  self.phase='place';self.dt=float(self.m.opt.timestep);self.events=[];self.records=[];self.trace=(self.out/'trace.jsonl').open('w');self.tick=0;self.frames=0;self.peaks={k:0. for k in ['speed','angular','robot','table','local','self_contact','robot_table']};self.hold=self.unsupported=0.;self.success=False;self.seen_lift=bool(self.d.xpos[self.obj,2]>.99);self.seen_flip=bool(self.d.xmat[self.obj].reshape(3,3)[2,2]<-.99);self.deep_grasp=self.pressure_control=True;self.sg3_lock_time=10.;self.start=time.monotonic()
  if args.checkpoint_json:
   if 'ctrl' in checkpoint:self.d.ctrl[:]=checkpoint['ctrl']
   else:self.command()  # Reconstruct bounded actuator controls before measuring checkpoint contacts.
   if 'act' in checkpoint:self.d.act[:]=checkpoint['act']
   if 'qacc_warmstart' in checkpoint:self.d.qacc_warmstart[:]=checkpoint['qacc_warmstart']
   mujoco.mj_forward(self.m,self.d)
  if self.body=='G':
   keys=[(s,f) for s in ['left','right'] for f in ['thumb','index','middle']];self.six_touched={k:False for k in keys};self.six_points={};self.six_errors={}
   stream=(source/'trace.jsonl').open() if (source/'trace.jsonl').exists() else gzip.open(source/'trace.jsonl.gz','rt')
   for line in stream:
    row=json.loads(line)
    if row['time']>self.d.time:break
    self.seen_lift |= row.get('seen_lift',False);self.seen_flip |= row.get('seen_flip',False)
    for c in row['contacts']:
     for k in keys:
      if c['body'].startswith(k[0]+'_hand_'+k[1]) and (1 if k[1]=='thumb' else -1)*np.dot(c['force_on_disk_world'],row['disk_normal'])>.1:self.six_touched[k]=True
   normal=self.d.xmat[self.obj].reshape(3,3)[:,2];self.filtered_force_targets=np.array([sum(max(0.,(1 if k[1]=='thumb' else -1)*np.dot(c['force_on_disk_world'],normal)) for c in self.contacts()[-1] if c['body'].startswith(k[0]+'_hand_'+k[1])) for k in keys])
  if self.body=='F':
   # This latch means 'has ever touched', not 'currently touching'. Recover it
   # from the recorded prefix so a checkpoint does not reopen a loaded thumb
   # while another contact is momentarily absent.
   self.inspire_touched={side:{face:False for face in ['thumb','fingers']} for side in ['L','R']}
   stream=(source/'trace.jsonl').open() if (source/'trace.jsonl').exists() else gzip.open(source/'trace.jsonl.gz','rt')
   with stream:
    for line in stream:
     row=json.loads(line)
     if row['time']>self.d.time:break
     n=np.asarray(row['disk_normal'])
     for side in ['L','R']:
      for face in ['thumb','fingers']:
       parts=['thumb'] if face=='thumb' else self.tuning.get('inspire_fingers',['index'])
       load=sum(c['force_n'] for c in row['contacts'] if any(c['body'].startswith(side+'_'+part+'_') for part in parts))
       self.inspire_touched[side][face] |= bool(load>.1)
     if all(v for values in self.inspire_touched.values() for v in values.values()):break
  source_hashes={}
  for name in ['run.py','stage_probe.py','model.py','reference_interface.py','wrench.py']:
   raw=Path(__file__).with_name(name).read_bytes();(self.out/name).write_bytes(raw);source_hashes[name]=hashlib.sha256(raw).hexdigest()
  write(self.out/'scope.json',dict(source_hashes=source_hashes,scope='checkpoint-initialized local diagnosis; not a full execution or acceptance witness',source=str(source),source_trajectory_sha256=hashlib.sha256((source/'trajectory.npz').read_bytes()).hexdigest() if (source/'trajectory.npz').exists() else None,requested_time=args.time,source_step=int(i) if i is not None else None,source_time=float(self.d.time),controller_tuning=self.tuning,controller_touch_history=getattr(self,'inspire_touched',None),action=args.action,physics_dt=self.dt,checkpoint_override=str(args.checkpoint_json) if args.checkpoint_json else None,checkpoint_sha256=hashlib.sha256(args.checkpoint_json.read_bytes()).hexdigest() if args.checkpoint_json else None))
 def step(self):
  super().step()
  if self.tick%250==0:
   folder=self.out/'checkpoints';folder.mkdir(exist_ok=True)
   write(folder/f't{self.d.time:.4f}.json',dict(time=float(self.d.time),qpos=self.d.qpos.tolist(),qvel=self.d.qvel.tolist(),reference=self.qref.tolist(),ctrl=self.d.ctrl.tolist(),act=self.d.act.tolist(),qacc_warmstart=self.d.qacc_warmstart.tolist(),scope='Valid diagnostic checkpoint only; not a full execution'))
 def render(self,name=None):pass
 def finish_probe(self,error):
  period=round(.02/self.dt);complete=len(self.records)//period;rows=[self.records[(i+1)*period-1] for i in range(complete)]
  if rows:
   np.savez_compressed(self.out/'command-references.npz',time=np.array([r[0] for r in rows]),reference=np.array([r[4] for r in rows]),phase=np.array([r[5] for r in rows]));write(self.out/'command-references.json',dict(scope='Commands proposed by a checkpoint-initialized diagnostic; not a full task witness or accepted policy',commands=complete,physics_hz=round(1/self.dt),control_hz=50,packet_sha256=hashlib.sha256((self.out/'command-references.npz').read_bytes()).hexdigest(),physical_failure=error))
  write(self.out/'final-state.json',dict(time=float(self.d.time),qpos=self.d.qpos.tolist(),qvel=self.d.qvel.tolist(),reference=self.qref.tolist(),ctrl=self.d.ctrl.tolist(),act=self.d.act.tolist(),qacc_warmstart=self.d.qacc_warmstart.tolist()));self.trace.close();write(self.out/'diagnostic.json',dict(scope='stage diagnosis only',controller_tuning_at_end=self.tuning,failure=error,time=float(self.d.time),peaks=self.peaks,terminal_at_checkpoint_continuation=bool(self.success),wall_seconds=time.monotonic()-self.start));print((self.out/'diagnostic.json').read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--time',type=float,required=True);p.add_argument('--physics-dt',type=float);p.add_argument('--checkpoint-json',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--tuning',type=Path);p.add_argument('--action',choices=['sg3_release','sg3_release_withdraw','sg3_finish','sg3_push','sg3_acquire_lift','dex3_finish','dex3_posttransfer','dex3_push','dex3_shift_push','dex3_align'],required=True);args=p.parse_args();a=Probe(args);error=None
 try:
  if args.action=='sg3_release':a.release_sg3_on_table()
  elif args.action=='sg3_release_withdraw':a.release_sg3_on_table();a.withdraw_sg3()
  elif args.action=='sg3_finish':a.finish_sg3_edge()
  elif args.action=='sg3_push':a.pressure_control=False;a.finish_sg3_push()
  elif args.action=='sg3_acquire_lift':
   a.sg3_lock_time=0.;a.establish_sg3_grasp();p,R=a.nominal_hand_pose('right');a.move('lift',{'right':(p+[0,0,.16],R)},seconds=40)
  elif args.action=='dex3_align':a.align_inverted_grasp()
  elif args.action=='dex3_shift_push':
   a.handoff_progress=1.;a.open_hands={'left'};p,R=a.nominal_hand_pose('right');delta=np.array([a.tuning['bridge_edge_x'],0,.870])-a.d.xpos[a.obj];a.move('place',{'right':(p+delta,R),'left':a.nominal_hand_pose('left')},seconds=10);a.finish_dex3_push_from_bridge()
  elif args.action=='dex3_push':
   a.handoff_progress=1.;a.open_hands={'left'};a.finish_dex3_push_from_bridge()
  elif args.action=='dex3_posttransfer':
   a.handoff_progress=1.;a.open_hands={'left'};a.finish_dex3_bridge_after_transfer()
  else:a.finish_dex3_bridge()
 except Exception as e:error=str(e)
 finally:a.finish_probe(error)
if __name__=='__main__':main()
