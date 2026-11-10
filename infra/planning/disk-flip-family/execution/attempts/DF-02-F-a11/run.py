"""Continuous joint-actuated expert attempts with predeclared plans and 400 Hz records."""
import argparse,hashlib,json,os,time,traceback
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from .model import build_scene

PROFILES={'DF-02-G':('G','P2'),'DF-02-F':('F','P2'),'DF-03-G':('G','P3'),'DF-04-G':('G','P1'),'DF-04-S':('S','P1')}
ACTIONS=[('settle','prepare','Stabilize the fixed body and supported plate'),('preshape','prepare','Open and orient fingers'),('orient_clear','prepare','Orient hands above and outside the disk'),('pregrasp','grasp','Approach the exposed rim from outside the table'),('insert','grasp','Insert opposing contacts around the rim'),('close','grasp','Close under measured contact loads'),('lift','lift','Raise the plate while maintaining actual grasp'),('turn','turn','Rotate the grasp through 180 degrees with clearance'),('place','place','Transfer support to the table'),('release','place','Open, withdraw and verify stable release')]

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def smooth(x):return x**3*(10-15*x+6*x*x)

class Attempt:
 def __init__(self,args):
  self.args=args;self.out=args.output;self.out.mkdir(parents=True,exist_ok=False);self.body,self.profile=PROFILES[args.setting]
  self.tuning=json.loads(args.tuning.read_text()) if getattr(args,'tuning',None) else {}
  self.plan={'controller_tuning':self.tuning,'setting':args.setting,'created_before_execution':True,'high_level':['prepare','grasp','lift','turn','place'],'low_level':[dict(id=f'L{i+1:02}',phase=p,high_level=h,action=a) for i,(p,h,a) in enumerate(ACTIONS)],'goal':{'xy':[.50,0],'position_tolerance_m':.045,'normal_z_max':-float(np.cos(np.deg2rad(8))),'release_hold_s':2},'world':{'start_xy':[.40,0],'table_height_m':.86,'table_edge_x_m':.35,'initial_overhang_m':.05,'base_motion':False},'limits':{'linear_speed_m_s':.12,'angular_speed_rad_s':.65,'robot_contact_sum_n':18,'table_contact_sum_n':8,'local_contact_body_n':4 if self.profile=='P3' else None},'engine':'MuJoCo extension development; original Genesis evidence is separate','policy':'joint targets through effort-limited actuators; no object pose/velocity/force writes or attachment'}
  if self.body=='S' and self.tuning.get('supported_turn',False):
   self.plan['strategy']='far-rim-supported tilt, vertical lift, vertical-axis half-turn, supported setdown, release and push to goal'
   self.plan['low_level'].append(dict(id='L11',phase='slide_goal',high_level='place',action='Push the released inverted disk fully into the goal region'))
  write(self.out/'plan.json',self.plan)
  for name in ['run.py','model.py']:(self.out/name).write_bytes(Path(__file__).with_name(name).read_bytes())
  self.m,self.d,self.binding=build_scene(self.body,self.profile,self.out)
  self.ikm=mujoco.MjModel.from_xml_path(str(self.out/'scene.xml'));self.ik=mujoco.MjData(self.ikm)
  for g in range(self.ikm.ngeom):
   if 'wrist' in self.ikm.body(int(self.ikm.geom_bodyid[g])).name and self.ikm.geom_contype[g]:self.ikm.geom_margin[g]=.004
  self.obj=self.m.body('disk').id;self.objj=self.m.joint('disk_free').id;self.objq=self.m.jnt_qposadr[self.objj];self.objv=self.m.jnt_dofadr[self.objj]
  self.table=self.m.geom('table').id;self.ground=self.m.geom('ground').id
  self.actj=self.m.actuator_trnid[:,0].copy();self.mode='torque' if self.body!='S' else 'position'
  self.joints={self.m.joint(j).name:j for j in range(self.m.njnt) if j!=self.objj}
  self.qref=self.d.qpos.copy();self.phase='settle';self.events=[];self.records=[];self.trace=(self.out/'trace.jsonl').open('w');self.failed=None;self.success=False;self.seen_lift=False;self.seen_flip=False;self.hold=0.;self.unsupported=0.;self.peaks={k:0. for k in ['speed','angular','robot','table','local','self_contact','robot_table']};self.frames=0
  self.start=time.monotonic();self.dt=float(self.m.opt.timestep);self.ctrl_dt=.02;self.tick=0;self.initialized=False
  self.initialize()
  self.qref=self.d.qpos.copy();self.last_ref=self.qref.copy();mujoco.mj_forward(self.m,self.d)
  self.initial=self.d.qpos.copy();write(self.out/'initial_state.json',{'qpos':self.d.qpos.tolist(),'qvel':self.d.qvel.tolist(),'disk_pos':self.d.xpos[self.obj].tolist()})
  self.renderer=mujoco.Renderer(self.m,height=720,width=960)
  import imageio.v2 as imageio
  self.writer=imageio.get_writer(self.out/'video.mp4',fps=10,macro_block_size=1)
  self.camera=mujoco.MjvCamera();self.camera.lookat[:]=[.35,0,.90];self.camera.distance=1.8;self.camera.azimuth=135;self.camera.elevation=-25
  self.imageio=imageio;self.render('initial.png');self.initialized=True
 def joint_set(self,target,name,value):
  if name in self.joints:
   j=self.joints[name];target[self.m.jnt_qposadr[j]]=np.clip(value,*self.m.jnt_range[j]) if self.m.jnt_limited[j] else value
 def initialize(self):
  # Scene initialization only; no position setters are used after this block.
  if self.body in ['G','F']:
   for side,sign in [('left',1),('right',-1)]:
    for part,v in [('hip_pitch',-.1),('knee',.3),('ankle_pitch',-.2),('shoulder_pitch',-1.1),('shoulder_roll',sign*.4),('elbow',.8)]:self.joint_set(self.d.qpos,f'{side}_{part}_joint',v)
  if self.body=='F':
    for side in ['L','R']:
     self.joint_set(self.d.qpos,f'{side}_thumb_proximal_yaw_joint',self.tuning.get('inspire_thumb_yaw',1.05))
     self.joint_set(self.d.qpos,f'{side}_thumb_proximal_pitch_joint',.15)
  else:
   self.joint_set(self.d.qpos,'joint_lift',.98)
   self.joint_set(self.d.qpos,'joint_wrist_yaw',0)
   self.joint_set(self.d.qpos,'joint_gripper_slide',.025)
 def preshape(self,close=0):
  q=self.qref.copy()
  if self.body=='G':
   for side,sign in [('left',-1),('right',1)]:
    for f in ['index','middle']:
     self.joint_set(q,f'{side}_hand_{f}_0_joint',sign*(.05+.5*close));self.joint_set(q,f'{side}_hand_{f}_1_joint',sign*.50)
    self.joint_set(q,f'{side}_hand_thumb_0_joint',self.tuning.get('left_thumb_yaw',.6) if side=='left' else self.tuning.get('right_thumb_yaw',.25))
    self.joint_set(q,f'{side}_hand_thumb_1_joint',0)
    self.joint_set(q,f'{side}_hand_thumb_2_joint',-sign*(1.57+.15*close))
  elif self.body=='F':
   for side in ['L','R']:
    self.joint_set(q,f'{side}_thumb_proximal_yaw_joint',self.tuning.get('inspire_thumb_yaw',1.05))
    self.joint_set(q,f'{side}_thumb_proximal_pitch_joint',.15+.4*close)
    for f in ['index','middle','ring','pinky']:self.joint_set(q,f'{side}_{f}_proximal_joint',.10+1.15*close)
  else:self.joint_set(q,'joint_gripper_slide',.025-.045*close)
  return q
 def hand_defs(self):
  if self.body=='S':return {'right':(self.m.body('link_grasp_center').id,np.zeros(3))}
  return {s:(self.m.body(f'{s}_wrist_yaw_link').id,np.array([.08382,.00406 if s=='left' else -.00406,0])) for s in ['left','right']}
 def hand_pose(self,side,data=None):
  d=data or self.d;b,offset=self.hand_defs()[side];R=d.xmat[b].reshape(3,3);return d.xpos[b]+R@offset,R
 def solve(self,goals,seed=None):
  self.ik.qpos[:]=self.d.qpos if seed is None else seed
  names=[n for n in self.joints if any(k in n for k in ['shoulder','elbow','wrist','waist'])] if self.body!='S' else ['joint_lift','joint_arm_l0','joint_arm_l1','joint_arm_l2','joint_arm_l3','joint_wrist_yaw','joint_wrist_pitch','joint_wrist_roll']
  js=[self.joints[n] for n in names if n in self.joints];qids=np.array([self.m.jnt_qposadr[j] for j in js]);vids=np.array([self.m.jnt_dofadr[j] for j in js]);lo=self.m.jnt_range[js,0].copy();hi=self.m.jnt_range[js,1].copy()
  for k,j in enumerate(js):
   n=self.m.joint(j).name
   if 'elbow' in n:lo[k]=max(lo[k],.05)
   if n=='left_shoulder_roll_joint':lo[k]=max(lo[k],-.10)
   if n=='right_shoulder_roll_joint':hi[k]=min(hi[k],.10)
   if n=='left_wrist_roll_joint' and self.phase not in ['turn','place','release']:lo[k]=.7
   if n=='right_wrist_roll_joint' and self.phase not in ['turn','place','release']:hi[k]=-.7
   if n=='waist_roll_joint':lo[k],hi[k]=-.25,.25
   if n=='waist_pitch_joint':lo[k],hi[k]=-.3,.5
  for _ in range(70):
   mujoco.mj_forward(self.ikm,self.ik);rows=[];errs=[]
   for side,(p,R) in goals.items():
    b,offset=self.hand_defs()[side];now,rot=self.hand_pose(side,self.ik);jp=np.zeros((3,self.m.nv));jr=jp.copy();mujoco.mj_jac(self.ikm,self.ik,jp,jr,now,b)
    rows.append(jp[:,vids]);errs.append(np.asarray(p)-now)
    if R is not None:rows.append(.15*jr[:,vids]);errs.append(.15*Rotation.from_matrix(R@rot.T).as_rotvec())
   for contact in self.ik.contact:
    ba,bb=[int(self.m.geom_bodyid[g]) for g in contact.geom]
    if ba<=0 or bb<=0 or self.obj in [ba,bb] or contact.dist>=.002:continue
    ja=np.zeros((3,self.m.nv));jb=ja.copy();mujoco.mj_jac(self.ikm,self.ik,ja,None,contact.pos,ba);mujoco.mj_jac(self.ikm,self.ik,jb,None,contact.pos,bb)
    rows.append((4.*(contact.frame[:3]@(jb[:,vids]-ja[:,vids])))[None,:]);errs.append(np.array([4.*(.002-contact.dist)]))
   J=np.vstack(rows);e=np.concatenate(errs);dq=J.T@np.linalg.solve(J@J.T+.001*np.eye(len(e)),e)
   self.ik.qpos[qids]=np.clip(self.ik.qpos[qids]+np.clip(dq,-.12,.12),lo,hi)
   if self.body=='S':
    vals=[self.ik.qpos[self.m.jnt_qposadr[self.joints[f'joint_arm_l{i}']]] for i in range(4)]
    for i in range(4):self.ik.qpos[self.m.jnt_qposadr[self.joints[f'joint_arm_l{i}']]]=np.mean(vals)
   if np.max(np.abs(e))<.001:break
  mujoco.mj_forward(self.ikm,self.ik)
  errors={s:float(np.linalg.norm(np.asarray(p)-self.hand_pose(s,self.ik)[0])) for s,(p,R) in goals.items()}
  return self.ik.qpos.copy(),errors
 def contacts(self):
  robot=table=local=rt=selfc=0.;bybody={};pairs=[];support=0.
  for i in range(self.d.ncon):
   c=self.d.contact[i];g1,g2=c.geom;bs=[int(self.m.geom_bodyid[g]) for g in [g1,g2]];f=np.zeros(6);mujoco.mj_contactForce(self.m,self.d,i,f);mag=float(np.linalg.norm(f[:3]));normal=float(f[0])
   if self.obj in bs:
    other=g2 if bs[0]==self.obj else g1;bid=int(self.m.geom_bodyid[other]);name=self.m.body(bid).name
    if other==self.table:table+=mag;support+=max(0.,normal)
    elif other==self.ground:raise RuntimeError('disk_ground_contact')
    elif bid!=self.obj:
     robot+=mag;bybody[name]=bybody.get(name,0)+mag
    if mag>.001:pairs.append({'body':name,'force_n':mag,'normal_n':normal,'position':c.pos.tolist(),'force_on_disk_world':((1 if bs[1]==self.obj else -1)*c.frame.reshape(3,3).T@f[:3]).tolist()})
   elif self.table in [g1,g2]:rt+=mag
   elif all(b>0 for b in bs):selfc+=mag
  local=max(bybody.values(),default=0)
  return robot,table,local,rt,selfc,pairs
 def assess(self):
  pos=self.d.xpos[self.obj].copy();normal=self.d.xmat[self.obj].reshape(3,3)[:,2];v=np.zeros(6);mujoco.mj_objectVelocity(self.m,self.d,mujoco.mjtObj.mjOBJ_BODY,self.obj,v,0)
  speed=float(np.linalg.norm(v[3:]));ang=float(np.linalg.norm(v[:3]));robot,table,local,rt,selfc,pairs=self.contacts()
  for k,val in [('speed',speed),('angular',ang),('robot',robot),('table',table),('local',local),('self_contact',selfc),('robot_table',rt)]:self.peaks[k]=max(self.peaks[k],val)
  if not np.isfinite(self.d.qpos).all() or not np.isfinite(self.d.qvel).all():raise RuntimeError('nonfinite_physics')
  for value,limit,reason in [(speed,.12,'disk_linear_speed'),(ang,.65,'disk_angular_speed'),(robot,18,'robot_contact_load'),(table,8,'table_contact_load'),(local,4 if self.profile=='P3' else 18,'local_damage_proxy')]:
   if value>limit+1e-6:raise RuntimeError(reason)
  if pos[2]<.835:raise RuntimeError('disk_dropped')
  if rt>20:raise RuntimeError('robot_table_collision')
  if selfc>20:raise RuntimeError('robot_self_collision')
  self.seen_lift |= bool(pos[2]>.99 and robot>.05)
  self.seen_flip |= bool(normal[2]<-.99)
  if table<.05 and robot<.05:self.unsupported+=self.dt
  else:self.unsupported=0
  if self.unsupported>.10:raise RuntimeError('uncontrolled_contact_loss')
  whole=bool(abs(pos[0]-.7)+.1<=.35 and abs(pos[1])+.1<=.575)
  terminal=bool(self.seen_flip and normal[2]<-np.cos(np.deg2rad(8)) and whole and np.linalg.norm(pos[:2]-[.5,0])<=.045 and table>.05 and robot<.05 and speed<.015 and ang<.08)
  self.hold=self.hold+self.dt if terminal else 0.;self.success=self.hold>=2
  return dict(time=float(self.d.time),phase=self.phase,disk_pos=pos.tolist(),disk_normal=normal.tolist(),speed=speed,angular=ang,robot_force=robot,table_force=table,local_force=local,robot_table_force=rt,self_contact_force=selfc,contacts=pairs,seen_lift=self.seen_lift,seen_flip=self.seen_flip,terminal_conditions=terminal,success=self.success)
 def pinch_loads(self):
  loads={s:{f:0. for f in ['top','bottom']} for s in ['left','right']}
  normal=self.d.xmat[self.obj].reshape(3,3)[:,2]
  for c in self.contacts()[-1]:
   for side in loads:
    if c['body'].startswith(side+'_hand'):
     face='bottom' if 'thumb' in c['body'] else 'top'
     loads[side][face]+=abs(float(np.dot(c['force_on_disk_world'],normal)))
  return loads
 def regulate_pinch(self):
  loads=self.pinch_loads();normal=self.d.xmat[self.obj].reshape(3,3)[2,2]
  if not hasattr(self,'pinch_touched'):
   self.pinch_touched={s:{f:False for f in ['top','bottom']} for s in loads};self.pinch_errors={}
  for side in loads:
   for face in loads[side]:self.pinch_touched[side][face] |= loads[side][face]>.1
  ready=all(all(x.values()) for x in self.pinch_touched.values())
  for side,sign in [('left',-1),('right',1)]:
   def actual(part):return self.d.qpos[self.m.jnt_qposadr[self.joints[f'{side}_hand_{part}_joint']]]
   def increment(part,velocity):
    n=f'{side}_hand_{part}_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*velocity)
   increment('thumb_2',np.clip(.8*(-sign*np.pi/2-actual('thumb_1')-actual('thumb_2')),-.04,.04))
   for f in ['index','middle']:increment(f+'_1',np.clip(.5*(sign*.5-actual(f+'_1')),-.02,.02))
   for face in ['top','bottom']:
    target=(self.tuning.get('dex3_load_n',1.5)+(.3 if face=='bottom' else -.3)*normal) if ready else .2
    key=(side,face);error=target-loads[side][face];previous=self.pinch_errors.get(key,error);filtered=previous+.02/.12*(error-previous);self.pinch_errors[key]=filtered
    velocity=(.025 if face=='bottom' else .02) if not self.pinch_touched[side][face] else np.clip(.008*error,-.015,.015)
    velocity=np.clip(velocity+.04*(filtered-previous)/.02,-.10,.10)
    if self.contacts()[0]>self.tuning.get('dex3_soft_total_n',12):velocity=min(velocity,-.04)
    if face=='bottom':increment('thumb_1',-sign*velocity)
    else:
     for f in ['index','middle']:increment(f+'_0',sign*velocity)
  return loads
 def regulate_inspire(self):
  loads={'thumb':0.,'fingers':0.}
  for c in self.contacts()[-1]:
   if c['body'].startswith('R_'):loads['thumb' if 'thumb' in c['body'] else 'fingers']+=c['force_n']
  if not hasattr(self,'inspire_touched'):self.inspire_touched={k:False for k in loads}
  for k,v in loads.items():self.inspire_touched[k] |= v>.1
  ready=all(self.inspire_touched.values())
  fingers=['index'] if self.tuning.get('inspire_index_only',False) else ['index','middle','ring','pinky']
  for face,names in [('thumb',['thumb_proximal_pitch']),('fingers',[f+'_proximal' for f in fingers])]:
   target=(self.tuning.get('inspire_thumb_n',2.8) if face=='thumb' else self.tuning.get('inspire_fingers_n',2.2)) if ready else .2
   speed=(.015 if face=='thumb' else .007) if not self.inspire_touched[face] else np.clip(.006*(target-loads[face]),-.025,.015)
   if self.contacts()[0]>11:speed=min(speed,-.02)
   for name in names:
    n='R_'+name+'_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*speed)
 def regulate_sg3(self):
  force=self.contacts()[0];qi=self.m.jnt_qposadr[self.joints['joint_gripper_slide']]
  target=self.tuning.get('sg3_load_n',6.)
  velocity=np.clip(.0005*(force-target),-.003,.006)
  self.joint_set(self.qref,'joint_gripper_slide',self.qref[qi]+.02*velocity)
 def command(self):
  if self.mode=='torque':
   for a,j in enumerate(self.actj):
    name=self.m.joint(int(j)).name;qi=self.m.jnt_qposadr[j];vi=self.m.jnt_dofadr[j]
    finger='hand' in name or name.startswith(('L_','R_'));kp,kd=(6.,.25) if finger else (40.,3.) if 'wrist' in name else (150.,8.)
    effort=max(abs(self.m.actuator_ctrlrange[a]));self.d.ctrl[a]=np.clip(kp*(self.qref[qi]-self.d.qpos[qi])-kd*self.d.qvel[vi]+self.d.qfrc_bias[vi],-effort,effort)
  else:
   targets={'left_wheel_vel':0,'right_wheel_vel':0,'arm':sum(self.qref[self.m.jnt_qposadr[self.joints[f'joint_arm_l{i}']]] for i in range(4))}
   for a in range(self.m.nu):
    n=self.m.actuator(a).name
    if n in targets:v=targets[n]
    else:
     j=self.m.actuator_trnid[a,0];v=self.qref[self.m.jnt_qposadr[j]]
    self.d.ctrl[a]=np.clip(v,*self.m.actuator_ctrlrange[a])
 def render(self,name=None):
  self.renderer.update_scene(self.d,camera=self.camera);im=self.renderer.render();self.writer.append_data(im);self.frames+=1
  if name:self.imageio.imwrite(self.out/name,im)
 def step(self):
  if getattr(self,'pressure_control',False):
   if self.body=='G':self.regulate_pinch()
   elif self.body=='S':self.regulate_sg3()
   elif self.body=='F':self.regulate_inspire()
  # References slewed at 0.5 rad/s; prismatic references at 0.05 m/s.
  for n,j in self.joints.items():
   qi=self.m.jnt_qposadr[j];rate=.05 if self.m.jnt_type[j]==mujoco.mjtJoint.mjJNT_SLIDE else .5
   self.qref[qi]=self.last_ref[qi]+np.clip(self.qref[qi]-self.last_ref[qi],-rate*.02,rate*.02)
  self.last_ref=self.qref.copy()
  for _ in range(8):
   self.command();mujoco.mj_step(self.m,self.d);self.records.append((self.d.time,self.d.qpos.copy(),self.d.qvel.copy(),self.d.ctrl.copy(),self.qref.copy(),self.phase));row=self.assess()
  self.tick+=1;self.trace.write(json.dumps(row)+'\n')
  if self.tick%5==0:self.render()
  if self.tick%100==0:self.trace.flush();print(json.dumps({k:row[k] for k in ['time','phase','disk_pos','robot_force','table_force']}),flush=True)
 def move(self,phase,goals=None,seconds=4,target=None):
  self.phase=phase;self.events.append({'phase':phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  start={s:self.hand_pose(s) for s in goals} if goals else None;q0=self.qref.copy()
  for i in range(round(seconds/.02)):
   u=smooth((i+1)/round(seconds/.02))
   if goals:
    current={}
    for s,(p,R) in goals.items():
     p0,R0=start[s];rot=Rotation.from_rotvec(u*Rotation.from_matrix(R@R0.T).as_rotvec()).as_matrix()@R0 if R is not None else None
     current[s]=(p0+u*(p-p0),rot)
    solution,err=self.solve(current,seed=self.qref)
    for n,j in self.joints.items():
     if any(k in n for k in ['shoulder','elbow','wrist','waist']) or self.body=='S' and any(k in n for k in ['joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   elif target is not None:self.qref=q0+u*(target-q0)
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if goals:
   residual={s:float(np.linalg.norm(p-self.hand_pose(s)[0])) for s,(p,R) in goals.items()};self.events[-1]['position_errors_m']=residual
   if max(residual.values())>.025:raise RuntimeError('grasp_pose_not_reached:'+str(residual))
 def execute(self):
  self.move('settle',seconds=2);self.move('preshape',target=self.preshape(),seconds=4)
  disk=self.d.xpos[self.obj].copy()
  if self.body=='S':
   # First candidate: near-edge pinch with the finger closing axis vertical.
   _,R=self.hand_pose('right');R=Rotation.from_euler('x',np.pi/2).as_matrix()@R
   goals={'right':(disk+[self.tuning.get('sg3_grasp_x',-.085),0,0],R)}
  else:
   goals={s:(disk+[-.10 if s=='left' else -.07,sign*(.15 if self.body=='F' else self.tuning.get('grasp_y',.09)),.044],Rotation.from_euler('z',-sign*np.pi/2).as_matrix()@Rotation.from_euler('x',sign*np.pi/2).as_matrix()) for s,sign in [('left',1),('right',-1)]}
  pre={s:(p+[-.12,(.06 if s=='left' else -.06) if self.body!='S' else 0,.015],R) for s,(p,R) in goals.items()}
  high={s:(p+[-.12,(.16 if s=='left' else -.16) if self.body!='S' else 0,.16 if self.body!='S' else .18],R) for s,(p,R) in goals.items()}
  if self.body!='S':
   pre={s:(np.array([.22,sign*(.24 if self.body=='F' else .18),.93]),goals[s][1]) for s,sign in [('left',1),('right',-1)]}
   seed=self.qref.copy()
   for side,sign in [('left',1),('right',-1)]:
    for part,v in [('shoulder_pitch',-.14),('shoulder_roll',sign*.82),('shoulder_yaw',sign*.42),('elbow',.15),('wrist_roll',sign*1.19),('wrist_pitch',-1.45),('wrist_yaw',sign*.32)]:self.joint_set(seed,f'{side}_{part}_joint',v)
   self.joint_set(seed,'waist_pitch_joint',.3)
   candidate,errors=self.solve(pre,seed)
   write(self.out/'pregrasp-ik.json',{'errors_m':errors,'candidate_qpos':candidate.tolist(),'scope':'key pose only; not physical feasibility'})
   if max(errors.values())>.01:raise RuntimeError('no_pregrasp_key_pose')
   target=self.qref.copy()
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist']):target[self.m.jnt_qposadr[j]]=candidate[self.m.jnt_qposadr[j]]
   self.move('orient_clear',target=target,seconds=16)
   self.move('pregrasp',pre,seconds=4)
  else:
   candidate,errors=self.solve(high)
   write(self.out/'pregrasp-ik.json',{'errors_m':errors,'candidate_qpos':candidate.tolist(),'scope':'key pose only; not physical feasibility'})
   if max(errors.values())>.01:raise RuntimeError('no_pregrasp_key_pose')
   target=self.qref.copy()
   for n,j in self.joints.items():
    if any(k in n for k in ['wrist','joint_arm','joint_lift']):target[self.m.jnt_qposadr[j]]=candidate[self.m.jnt_qposadr[j]]
   self.move('orient_clear',target=target,seconds=12)
   self.move('pregrasp',pre,seconds=14)
  if self.body=='F':
   p,R=goals['right'];R=Rotation.from_euler('z',self.tuning.get('inspire_hand_yaw',0.)) .as_matrix()@R;goals={'right':(p+np.array(self.tuning.get('inspire_offset',[.025,.02,0.])),R)}
  if self.profile in ['P2','P3'] and self.body=='G':goals={s:(p+[-.02,0,.008],R) for s,(p,R) in goals.items()}
  self.move('insert',goals,seconds=20)
  if self.body=='G':
   self.pressure_control=True;self.move('close',seconds=self.tuning.get('dex3_close_s',40))
   if not all(v>self.tuning.get('dex3_min_face_n',.8) for faces in self.pinch_loads().values() for v in faces.values()):raise RuntimeError('opposing_grasp_loads_not_established')
  elif self.body=='S':
   self.pressure_control=True;self.move('close',seconds=22)
  else:
   self.pressure_control=True;self.move('close',seconds=self.tuning.get('inspire_close_s',55))
  if self.contacts()[0]<.10:raise RuntimeError('no_measured_grasp_contact')
  if self.body=='S' and self.tuning.get('supported_turn',False):return self.execute_sg3_supported()
  lift={s:(self.hand_pose(s)[0]+[0,0,.16],self.hand_pose(s)[1]) for s in goals}
  self.move('lift',lift,seconds=40)
  if self.d.xpos[self.obj][2]<.99:raise RuntimeError('lift_without_object')
  centre=self.d.xpos[self.obj].copy();poses={s:self.hand_pose(s) for s in goals}
  self.phase='turn';self.events.append({'phase':'turn','start_s':float(self.d.time),'record_start':len(self.records)})
  for i in range(3000):
   R=Rotation.from_euler('x' if self.body=='S' else 'y',(-1 if self.body=='S' else 1)*np.pi*smooth((i+1)/3000)).as_matrix();targets={s:(centre+R@(p-centre),R@rot) for s,(p,rot) in poses.items()}
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  delta=np.array([.5,0,.866])-self.d.xpos[self.obj]
  self.move('place',{s:(self.hand_pose(s)[0]+delta,self.hand_pose(s)[1]) for s in goals},seconds=15)
  self.pressure_control=False
  self.move('release',target=self.preshape(close=0),seconds=5)
  self.move('release',{s:(self.hand_pose(s)[0]+[-.08,0,.08],self.hand_pose(s)[1]) for s in goals},seconds=8)
  self.move('release',seconds=3)
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def rotate_grasp(self,phase,axis,angle,pivot,seconds):
  self.phase=phase;self.events.append({'phase':phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  poses={'right':self.hand_pose('right')};steps=round(seconds/.02)
  for i in range(steps):
   R=Rotation.from_euler(axis,angle*smooth((i+1)/steps)).as_matrix()
   targets={s:(pivot+R@(p-pivot),R@rot) for s,(p,rot) in poses.items()}
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['wrist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
 def execute_sg3_supported(self):
  # Hold the far rim on the table while rotating the gripped near rim upward.
  pivot=self.d.xpos[self.obj]+np.array([.10,0,-.006])
  self.rotate_grasp('lift','y',np.pi/2,pivot,65)
  self.move('lift',{'right':(self.hand_pose('right')[0]+[0,0,.025],self.hand_pose('right')[1])},seconds=12)
  self.rotate_grasp('turn','z',np.pi,self.d.xpos[self.obj].copy(),65)
  self.move('place',{'right':(self.hand_pose('right')[0]-[0,0,.025],self.hand_pose('right')[1])},seconds=12)
  pivot=self.d.xpos[self.obj]+np.array([0,0,-.10])
  self.rotate_grasp('place','y',-np.pi/2,pivot,65)
  self.pressure_control=False
  self.move('release',target=self.preshape(close=0),seconds=8)
  self.move('release',{'right':(self.hand_pose('right')[0]+[-.08,0,.07],self.hand_pose('right')[1])},seconds=12)
  self.move('slide_goal',target=self.preshape(close=1),seconds=8)
  disk=self.d.xpos[self.obj].copy();R=self.hand_pose('right')[1]
  self.move('slide_goal',{'right':(disk+[-.14,0,.002],R)},seconds=15)
  self.phase='slide_goal';self.events.append({'phase':'slide_goal','start_s':float(self.d.time),'record_start':len(self.records)})
  pos=self.hand_pose('right')[0].copy()
  for i in range(4500):
   if self.d.xpos[self.obj][0]>=.49:break
   pos[0]+=.002*.02
   solution,_=self.solve({'right':(pos,R)},seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['wrist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.move('release',{'right':(self.hand_pose('right')[0]+[-.06,0,.06],R)},seconds=12)
  self.move('release',seconds=3)
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def finish(self,error):
  self.trace.close();self.render('final.png');self.writer.close();self.renderer.close()
  if self.events and 'end_s' not in self.events[-1]:self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records),interrupted=True)
  write(self.out/'segments.json',self.events)
  if self.records:
   t,q,v,u,refs,phases=zip(*self.records);np.savez_compressed(self.out/'trajectory.npz',time=t,qpos=q,qvel=v,ctrl=u,reference=refs,phase=phases)
  summary={'setting':self.args.setting,'task_success':bool(self.success and not error),'status':'full_witness_candidate' if self.success and not error else 'failed_attempt','failure':error,'simulated_seconds':float(self.d.time),'wall_seconds':time.monotonic()-self.start,'physics_hz':400,'trace_hz':50,'video_fps':10,'physics_records':len(self.records),'video_frames':self.frames,'peaks':self.peaks,'seen_lift':self.seen_lift,'seen_flip':self.seen_flip,'independent_verification':'pending','binding':self.binding,'policy_state_writes':0,'object_attachment':False,'source_hashes':{n:hashlib.sha256((self.out/n).read_bytes()).hexdigest() for n in ['run.py','model.py','plan.json','scene.xml']},'limitations':['Privileged development expert; no public-agent score','MuJoCo extension protocol; original Genesis evidence is separate','No comparison success inferred from a failed or single-body attempt']}
  write(self.out/'summary.json',summary);print(json.dumps(summary),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--tuning',type=Path);p.add_argument('--setting',choices=list(PROFILES),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();attempt=Attempt(a);error=None
 try:attempt.execute()
 except Exception as e:error=str(e);(a.output/'error.txt').write_text(traceback.format_exc())
 finally:attempt.finish(error)
 return 0 if attempt.success and not error else 1
if __name__=='__main__':raise SystemExit(main())
