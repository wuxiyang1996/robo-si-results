"""Free-base native grasp/lift/release gate for the unchanged H3 parcel."""
import argparse,gzip,hashlib,json,os,time,traceback
from pathlib import Path
import numpy as np
from .embodiments import stretch4 as M

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--width',type=float,default=.18);a=ap.parse_args()
 out=a.out;out.mkdir(parents=True,exist_ok=False);asset,receipt=M.build(out/'assets','rollers')
 for name,p in [('probe-source.py',Path(__file__)),('binding-source.py',Path(M.__file__))]:(out/name).write_bytes(p.read_bytes())
 from .embodiments.stretch4_driver import StretchDriver
 from .embodiments import stretch4_driver
 (out/'driver-source.py').write_bytes(Path(stretch4_driver.__file__).read_bytes())
 # At zero yaw, the original SG4 grasp midpoint is about y=-.086 m.
 stages=[('settle',2.,0.,0.,0.),('raise_open',4.,.608,0.,.5),('approach',4.,.608,.0875,.5),('squeeze',2.,.608,.0875,.35),('lift',3.,.758,.0875,.35),('hold_airborne',3.,.758,.0875,.35),('lower',3.,.608,.0875,.35),('release',2.,.608,.0875,.5),('withdraw',3.,.608,0.,.5),('table_dwell',2.,.608,0.,.5)]
 plan=dict(schema='h3-parcel-grasp-probe/1',configuration_dependencies=['H3-03','H3-04','H3-05'],scope='single-robot grasp feasibility only; no doorway or complete-task claim',parcel_size=[.20,a.width,.16],parcel_mass=.4,table_height=.7,phases=stages,physics_dt=.005,airborne_dwell_required_s=2.,released_dwell_required_s=1.5,task_success=None,slurm_job_id=os.getenv('SLURM_JOB_ID'))
 (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 scene=None;writer=None;trace=None;result={**plan,'status':'started'};started=time.monotonic()
 try:
  import genesis as gs
  import imageio.v2 as imageio
  gs.init(backend=gs.gpu,seed=0,logging_level='warning')
  scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.005),rigid_options=gs.options.RigidOptions(enable_self_collision=True,batch_dofs_info=True,batch_links_info=True),show_viewer=False)
  floor=scene.add_entity(gs.morphs.Plane(),material=gs.materials.Rigid(friction=.6))
  table=scene.add_entity(gs.morphs.Box(size=(.42,.42,.7),pos=(.8,-.086,.35),fixed=True),material=gs.materials.Rigid(friction=.6),surface=gs.surfaces.Default(color=(.65,.45,.25)))
  box=scene.add_entity(gs.morphs.Box(size=plan['parcel_size'],pos=(.8,-.086,.783)),material=gs.materials.Rigid(rho=.4/np.prod(plan['parcel_size']),friction=.7),surface=gs.surfaces.Default(color=(.8,.25,.1)))
  robot=scene.add_entity(gs.morphs.URDF(file=str(asset),pos=(0,0,.005),fixed=False,merge_fixed_links=False),material=gs.materials.Rigid(friction=.6))
  cam=scene.add_camera(res=(800,600),pos=(2.7,-3.2,2.3),lookat=(.4,0,.75),GUI=False)
  scene.build(n_envs=1);driver=StretchDriver(robot,gs.device)
  # Upstream gripper uses rubber friction 1.8; apply before stepping and record.
  pads=[l.idx_local for l in robot.links if 'gripper_finger' in l.name]
  import torch
  robot.set_friction_ratio(torch.full((1,len(pads)),3.),links_idx_local=pads)
  writer=imageio.get_writer(str(out/'motion.mp4'),fps=10,codec='libx264',quality=7,macro_block_size=1)
  trace=gzip.open(out/'states.jsonl.gz','wt');owners={l.idx:l.name for l in robot.links};t=0.;air=0.;max_air=0.;released=0.;max_released=0.;events=[];boundaries=[]
  def arr(v):return v.detach().cpu().numpy()[0]
  def force(a,b):
   c=a.get_contacts(with_entity=b);return float(torch.where(c['valid_mask'],c['force_a'].norm(dim=-1),0.).sum().cpu())
  for phase,dur,lift,arm,grip in stages:
   goal=np.array([lift,arm,0.,0.,0.,grip,grip]);begin=t
   for i in range(round(dur/.005)):
    if i%4==0:cmd=driver.apply(goal)
    scene.step();t=round(t+.005,6)
    pos=arr(box.get_pos());vel=arr(box.get_vel());quat=arr(box.get_quat());robotpos=arr(robot.get_pos())
    contacts={k:arr(v) for k,v in robot.get_contacts(with_entity=box).items()};finger=[0.,0.]
    for j in np.flatnonzero(contacts['valid_mask']):
     for side in ['a','b']:
      link=owners.get(int(contacts['link_'+side][j]),'')
      if 'gripper_finger' in link:finger[0 if 'left' in link else 1]+=float(np.linalg.norm(contacts['force_'+side][j]))
    support=force(box,table);graspforce=force(box,robot)
    airborne=bool(pos[2]>.84 and support<.5 and min(finger)>.5 and np.linalg.norm(vel)<.15)
    air=air+.005 if airborne else 0.;max_air=max(max_air,air)
    releaseok=bool(max_air>=2 and abs(pos[2]-.78)<.02 and np.linalg.norm(vel)<.05 and graspforce<.2 and support>2. and abs(pos[0]-.8)<.1 and abs(pos[1]+.086)<.1)
    released=released+.005 if releaseok else 0.;max_released=max(max_released,released)
    if air>=2. and not any(e['event']=='airborne_dwell' for e in events):events.append(dict(t=t,event='airborne_dwell'))
    if released>=1.5 and not any(e['event']=='released_table_dwell' for e in events):events.append(dict(t=t,event='released_table_dwell'))
    row=dict(t=t,phase=phase,parcel_pos=pos.tolist(),parcel_quat=quat.tolist(),parcel_vel=vel.tolist(),table_contact_N=support,finger_contacts_N=finger,robot_parcel_contact_N=graspforce,robot_pos=robotpos.tolist(),robot_quat=arr(robot.get_quat()).tolist(),joint_positions=arr(robot.get_dofs_position()).tolist(),command=cmd,airborne=airborne,airborne_dwell_s=air,released_dwell_s=released)
    trace.write(json.dumps(row,allow_nan=False)+'\n')
    if round(t/.005)%20==0:writer.append_data(cam.render()[0])
    if pos[2]<.6 or abs(pos[0]-.8)>.3 or abs(pos[1]+.086)>.3:raise RuntimeError('parcel dropped or pushed out of the manipulation area')
   boundaries.append(dict(phase=phase,start_s=begin,end_s=t,parcel_pos=pos.tolist(),finger_contacts_N=finger,table_contact_N=support));print(json.dumps(boundaries[-1]),flush=True)
  result.update(status='grasp_probe_completed',probe_success=bool(max_air>=2. and max_released>=1.5),physics_feasibility='passed_local_screen' if max_air>=2. and max_released>=1.5 else 'check_failed')
 except Exception as exc:
  result.update(status='grasp_probe_failed',probe_success=False,error=str(exc),traceback=traceback.format_exc(),physics_feasibility='check_failed');print(result['traceback'],flush=True)
 finally:
  if trace:trace.close()
  if writer:writer.close()
  if scene:scene.destroy()
  result.update(wall_seconds=time.monotonic()-started,seconds=locals().get('t',0),events=locals().get('events',[]),phase_boundaries=locals().get('boundaries',[]),max_airborne_dwell_s=locals().get('max_air',0),max_released_dwell_s=locals().get('max_released',0),task_success=None,hardware_calibrated=False)
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');(out/'files.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='files.json'},indent=2)+'\n')
 if not result.get('probe_success'):raise SystemExit(1)
if __name__=='__main__':main()
