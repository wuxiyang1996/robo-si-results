"""Bounded single-robot control probe with 200 Hz evidence and rendered video."""
import argparse,gzip,hashlib,json,math,os,time,traceback
from pathlib import Path
import numpy as np
from .embodiments import stretch4 as S


def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--no-video',action='store_true');p.add_argument('--wheel-model',choices=['raw','rollers'],default='raw');p.add_argument('--diagnostic',action='store_true');p.add_argument('--wheel-effort',type=float,default=8.);p.add_argument('--wheel-kv',type=float,default=4.);a=p.parse_args()
 if not 0<a.wheel_effort<=20 or not 0<a.wheel_kv<=50:p.error('probe wheel bounds out of range')
 for name in S.WHEELS:S.PARAMS[name].update(force=a.wheel_effort,kv=a.wheel_kv,source='predeclared author probe limit; not hardware calibrated')
 out=a.out;out.mkdir(parents=True,exist_ok=False)
 source,receipt=S.build(out/'assets',a.wheel_model)
 (out/'binding-source.py').write_bytes(Path(S.__file__).read_bytes())
 phases=[('settle',2.),('lift_and_open',4.),('extend',3.),('forward',3.),('stop_forward',2.),('lateral',3.),('stop_lateral',2.),('rotate',3.),('stop_rotate',2.),('retract_close',4.)]
 if a.diagnostic:phases=[('settle',1.),('forward',1.)]
 plan=dict(schema='h3-control-probe-plan/1',scope='H3-03/H3-04/H3-05 shared Stretch 4 control prerequisite; not task execution',physics_dt=.005,phases=phases,expected_translation_m=.45,minimum_useful_translation_m=.2,maximum_cross_axis_drift_m=.15,maximum_stopped_speed_mps=.03,task_success=None,slurm_job_id=os.getenv('SLURM_JOB_ID'))
 (out/'plan.json').write_text(json.dumps(plan,indent=2));(out/'source.py').write_bytes(Path(__file__).read_bytes())
 started=time.monotonic();scene=None;writer=None;trace=None;result={**plan,'status':'started'}
 try:
  import genesis as gs
  import torch
  import imageio.v2 as imageio
  gs.init(backend=gs.gpu,seed=0,logging_level='warning')
  scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.005),rigid_options=gs.options.RigidOptions(enable_self_collision=True,batch_dofs_info=True,batch_links_info=True),show_viewer=False)
  floor=scene.add_entity(gs.morphs.Plane(),material=gs.materials.Rigid(friction=.6))
  robot=scene.add_entity(gs.morphs.URDF(file=str(source),pos=(0,0,.005),fixed=False,merge_fixed_links=False),material=gs.materials.Rigid(friction=.6))
  cam=scene.add_camera(res=(800,600),pos=(2.7,-3.2,2.2),lookat=(0,0,.65),GUI=False) if not a.no_video else None
  scene.build(n_envs=1)
  dofs={n:robot.get_joint(n).dofs_idx_local[0] for n in [*S.POSITION,*S.WHEELS,*S.ARMS[1:]]}
  for n,v in S.PARAMS.items():
   robot.set_dofs_kp([v['kp']],[dofs[n]]);robot.set_dofs_kv([v['kv']],[dofs[n]])
   robot.set_dofs_force_range([-v['force']],[v['force']],[dofs[n]])
  for n in S.ARMS[1:]:
   robot.set_dofs_kp([0.],[dofs[n]]);robot.set_dofs_kv([0.],[dofs[n]]);robot.set_dofs_force_range([0.],[0.],[dofs[n]])
  q=np.zeros(len(S.POSITION));robot.set_dofs_position(torch.tensor(q[None],device=gs.device,dtype=gs.tc_float),[dofs[n] for n in S.POSITION],zero_velocity=True)
  if cam:writer=imageio.get_writer(str(out/'motion.mp4'),fps=10,codec='libx264',quality=7,macro_block_size=1)
  trace=gzip.open(out/'states.jsonl.gz','wt');t=0.;boundaries=[];measurements=[]
  def arr(x):return x.detach().cpu().numpy()[0].tolist()
  wheel_geometry=[]
  for link in robot.links:
   if 'wheel' in link.name:
    wheel_geometry.append(dict(name=link.name,pos=arr(link.get_pos()),quat=arr(link.get_quat()),geoms=[dict(type=str(g.type),data=np.asarray(g.data).tolist(),init_pos=np.asarray(g.init_pos).tolist()) for g in link.geoms]))
  (out/'wheel-geometry.json').write_text(json.dumps(wheel_geometry,indent=2))
  owners={l.idx:l.name for l in robot.links}
  for phase,duration in phases:
   begin=dict(phase=phase,t=t,pos=arr(robot.get_pos()));goal=q.copy()
   if phase=='lift_and_open':goal[0]=.48;goal[-2:]=.5
   if phase=='extend':goal[1]=.09
   if phase=='retract_close':goal[1]=0.;goal[-2:]=0.
   for step in range(round(duration/.005)):
    if step%4==0:
     speed=np.array([S.PARAMS[n]['velocity'] for n in S.POSITION]);q+=np.clip(goal-q,-speed*.02,speed*.02)
     v={'forward':(.15,0,0),'lateral':(0,.15,0),'rotate':(0,0,.25)}.get(phase,(0,0,0))
     angles=[2*math.pi/3,-2*math.pi/3,0]
     wheel=[(math.cos(x)*v[0]+math.sin(x)*v[1]+.174*v[2])/S.WHEEL_RADIUS for x in angles]
     robot.control_dofs_position(torch.tensor(q[None],device=gs.device,dtype=gs.tc_float),[dofs[n] for n in S.POSITION])
     robot.control_dofs_velocity(torch.tensor([wheel],device=gs.device,dtype=gs.tc_float),[dofs[n] for n in S.WHEELS])
    scene.step();t=round(t+.005,6)
    row=dict(t=t,phase=phase,root_pos=arr(robot.get_pos()),root_quat=arr(robot.get_quat()),root_vel=arr(robot.get_vel()),q=arr(robot.get_dofs_position()),qd=arr(robot.get_dofs_velocity()),targets=q.tolist(),wheel_targets=wheel)
    contacts={k:np.asarray(arr(v)) for k,v in robot.get_contacts(with_entity=floor).items()};loads={}
    for i in np.flatnonzero(contacts['valid_mask']):
     for side in ['a','b']:
      name=owners.get(int(contacts['link_'+side][i]))
      if name:loads[name]=loads.get(name,0.)+float(np.linalg.norm(contacts['force_'+side][i]))
    row['ground_contact_force_N']=loads
    row['finger_tips']={n:arr(robot.get_link(n).get_pos()) for n in ['gripper_fingertip_left_link','gripper_fingertip_right_link']}
    if not all(np.isfinite(row[k]).all() for k in ['root_pos','root_quat','root_vel','q','qd']):raise RuntimeError('nonfinite native state')
    trace.write(json.dumps(row,allow_nan=False)+'\n')
    if cam and round(t/.005)%20==0:writer.append_data(cam.render()[0])
   end=dict(phase=phase,t=t,pos=row['root_pos'],quat=row['root_quat'],speed=float(np.linalg.norm(row['root_vel'])),fingertip_center_distance=float(np.linalg.norm(np.array(list(row['finger_tips'].values()))[0]-np.array(list(row['finger_tips'].values()))[1])))
   end['displacement']=(np.array(end['pos'])-np.array(begin['pos'])).tolist();boundaries.append(dict(start=begin,end=end));print(json.dumps(end),flush=True)
   print('ground support',loads,flush=True)
  result.update(status='control_probe_completed',seconds=t,phase_boundaries=boundaries,task_success=None,physics_feasibility='undetermined',hardware_calibrated=False)
 except Exception as exc:
  result.update(status='probe_failed',error=str(exc),traceback=traceback.format_exc(),task_success=None);print(result['traceback'],flush=True)
 finally:
  if trace:trace.close()
  if writer:writer.close()
  result['wall_seconds']=time.monotonic()-started
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  if scene:scene.destroy()
  (out/'files.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='files.json'},indent=2)+'\n')
 if result['status']=='probe_failed':raise SystemExit(1)
if __name__=='__main__':main()
