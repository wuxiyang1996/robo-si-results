"""Continuous joint-actuated expert attempts with predeclared plans and 400 Hz records."""
import argparse,hashlib,json,os,time,traceback
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from .model import build_scene
from .reference_interface import JointReferenceInterface

PROFILES={'DF-02-G':('G','P2'),'DF-02-F':('F','P2'),'DF-03-G':('G','P3'),'DF-04-G':('G','P1'),'DF-04-S':('S','P1')}
ACTIONS=[('settle','prepare','Stabilize the fixed body and supported plate'),('preshape','prepare','Open and orient fingers'),('orient_clear','prepare','Orient hands above and outside the disk'),('pregrasp','grasp','Approach the exposed rim from outside the table'),('insert','grasp','Insert opposing contacts around the rim'),('close','grasp','Close under measured contact loads'),('lift','lift','Raise the plate while maintaining actual grasp'),('turn','turn','Rotate the grasp through 180 degrees with clearance'),('place','place','Transfer support to the table'),('release','place','Open, withdraw and verify stable release')]

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def smooth(x):return x**3*(10-15*x+6*x*x)

class Attempt:
 def __init__(self,args):
  self.args=args;self.out=args.output;self.out.mkdir(parents=True,exist_ok=False);self.body,self.profile=PROFILES[args.setting]
  self.tuning=json.loads(args.tuning.read_text()) if getattr(args,'tuning',None) else {}
  self.plan={'controller_tuning':self.tuning,'setting':args.setting,'created_before_execution':True,'high_level':['prepare','grasp','lift','turn','place'],'low_level':[dict(id=f'L{i+1:02}',phase=p,high_level=h,action=a) for i,(p,h,a) in enumerate(ACTIONS)],'goal':{'xy':[.50,0],'position_tolerance_m':.045,'normal_z_max':-float(np.cos(np.deg2rad(8))),'release_hold_s':2},'world':{'start_xy':[.40,0],'table_height_m':.86,'table_edge_x_m':.35,'initial_overhang_m':.05,'base_motion':False},'limits':{'linear_speed_m_s':.12,'angular_speed_rad_s':.65,'robot_contact_sum_n':18,'table_contact_sum_n':8,'local_contact_body_n':4 if self.profile=='P3' else None},'engine':'MuJoCo extension development; original Genesis evidence is separate','policy':'joint targets through effort-limited actuators; no object pose/velocity/force writes or attachment'}
  if self.tuning.get('edge_regrasp',False) or self.tuning.get('prepush',False):
   self.plan['low_level'].extend([dict(id='L12',phase='edge_slide',high_level='grasp',action='Move the table-supported plate toward the edge using measured contact'),dict(id='L13',phase='regrasp_release',high_level='grasp',action='Release the table-supported plate before deeper regrasp')])
  if self.tuning.get('bridge_place',False):self.plan['low_level'].append(dict(id='L11',phase='slide_goal',high_level='place',action='Transfer support from lower fingers to the table while pushing the inverted plate into the goal'))
  if self.body=='S' and (self.tuning.get('supported_turn',False) or self.tuning.get('edge_regrasp',False)):
   self.plan['strategy']='far-rim-supported tilt, vertical lift, vertical-axis half-turn, supported setdown, release and push to goal' if self.tuning.get('supported_turn',False) else 'pull to edge, release and regrasp deeper, lift and invert, release at edge and push to goal'
   self.plan['low_level'].append(dict(id='L11',phase='slide_goal',high_level='place',action='Push the released inverted disk fully into the goal region'))
  self.plan['integration']={'physics_dt_s':self.tuning.get('physics_dt',.0025),'control_dt_s':.02,'status':'refined-step development candidate' if self.tuning.get('physics_dt',.0025)!=.0025 else 'legacy 400 Hz development'}
  write(self.out/'plan.json',self.plan)
  for name in ['run.py','model.py','wrench.py','reference_interface.py']:(self.out/name).write_bytes(Path(__file__).with_name(name).read_bytes())
  self.m,self.d,self.binding=build_scene(self.body,self.profile,self.out,collision_profile=self.tuning.get("collision_profile","original"),disk_collision_shape=self.tuning.get("disk_collision_shape","cylinder"),physics_dt=self.tuning.get("physics_dt",.0025))
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
  # Consistent initial linkage coordinates avoid an artificial equality impulse.
  for _ in range(4):
   for e in range(self.m.neq):
    if self.m.eq_type[e]!=mujoco.mjtEq.mjEQ_JOINT:continue
    j1,j2=int(self.m.eq_obj1id[e]),int(self.m.eq_obj2id[e])
    if j1<0 or j2<0:continue
    q2=float(self.d.qpos[self.m.jnt_qposadr[j2]]);coeff=self.m.eq_data[e,:5]
    self.d.qpos[self.m.jnt_qposadr[j1]]=sum(float(c)*q2**k for k,c in enumerate(coeff))
  self.qref=self.d.qpos.copy();self.last_ref=self.qref.copy();mujoco.mj_forward(self.m,self.d)
  self.action_interface=JointReferenceInterface(self.m,self.qref,self.body)
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
    for f in ['index','middle','ring','pinky']:self.joint_set(q,f'{side}_{f}_proximal_joint',self.tuning.get('inspire_unused_fold',.9) if self.tuning.get('inspire_bimanual',False) and f not in self.tuning.get('inspire_fingers',['index']) else .10+1.15*close)
  else:self.joint_set(q,'joint_gripper_slide',.025-.045*close)
  return q
 def hand_defs(self):
  if self.body=='S':return {'right':(self.m.body('link_grasp_center').id,np.zeros(3))}
  result={s:(self.m.body(f'{s}_wrist_yaw_link').id,np.array([.08382,.00406 if s=='left' else -.00406,0])) for s in ['left','right']}
  if getattr(self,'active_tool',None)=='left_thumb':result['left']=(self.m.body('left_hand_thumb_2_link').id,np.array([-.0038,-.0516,-.002]))
  if getattr(self,'active_tool',None)=='left_index':result['left']=(self.m.body('L_index_intermediate').id,np.array([.003,-.044,-.005]))
  if getattr(self,'active_tool',None)=='left_inspire_thumb':result['left']=(self.m.body('L_thumb_distal').id,np.array([.021,-.006,-.005]))
  return result
 def hand_pose(self,side,data=None):
  d=data or self.d;b,offset=self.hand_defs()[side];R=d.xmat[b].reshape(3,3);return d.xpos[b]+R@offset,R
 def nominal_hand_pose(self,side):
  self.ik.qpos[:]=self.qref
  for name,j in self.joints.items():
   if '_hand_' in name or name.startswith(('L_','R_')) or 'gripper' in name:
    qi=self.m.jnt_qposadr[j];self.ik.qpos[qi]=self.d.qpos[qi]
  mujoco.mj_forward(self.ikm,self.ik)
  p,R=self.hand_pose(side,self.ik);return p.copy(),R.copy()
 def align_grasp(self,goals):
  self.events.append({'phase':self.phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  for _ in range(400):
   targets={}
   for side,(p,R) in goals.items():
    actual,rot=self.hand_pose(side);nominal,Rnom=self.nominal_hand_pose(side)
    er=Rotation.from_matrix(R@rot.T).as_rotvec()
    targets[side]=(nominal+np.clip(.2*(p-actual),-.0003,.0003),Rotation.from_rotvec(np.clip(.15*er,-.002,.002)).as_matrix()@Rnom)
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
 def solve(self,goals,seed=None):
  if getattr(self,'active_tool',None) and hasattr(self,'tool_hold'):goals={**self.tool_hold,**goals}
  if self.phase=='slide_goal' and getattr(self,'active_tool',None)=='left_thumb' and self.tuning.get('bridge_hold_height',False) and 'right' in goals:
   if self.d.time!=getattr(self,'bridge_height_update',None):
    self.bridge_height_update=self.d.time
    if self.contacts()[1]<.1*1.1772:self.bridge_height_offset=np.clip(getattr(self,'bridge_height_offset',0.)+.02*np.clip(.5*(.870-self.d.xpos[self.obj][2]),-.003,.003),-.04,.04)
   p,R=goals['right'];goals['right']=(p+[0,0,getattr(self,'bridge_height_offset',0.)],R)
  if self.phase=='slide_goal' and getattr(self,'active_tool',None)=='left_thumb' and self.tuning.get('bridge_hold_attitude',False) and 'right' in goals:
   if self.d.time!=getattr(self,'bridge_attitude_update',None):
    self.bridge_attitude_update=self.d.time;self.bridge_attitude_matrix=self.attitude_correction(np.array([0.,0.,-1.]))
   correction=self.bridge_attitude_matrix;centre=self.d.xpos[self.obj].copy();p,R=goals['right'];goals['right']=(centre+correction@(p-centre),correction@R)
  self.ik.qpos[:]=self.d.qpos if seed is None else seed
  # Collision planning uses measured coupled finger geometry, including passive mimic joints.
  for name,j in self.joints.items():
   if '_hand_' in name or name.startswith(('L_','R_')) or 'gripper' in name:
    qi=self.m.jnt_qposadr[j];self.ik.qpos[qi]=self.d.qpos[qi]
  names=[n for n in self.joints if any(k in n for k in ['shoulder','elbow','wrist','waist'])] if self.body!='S' else ['joint_lift','joint_arm_l0','joint_arm_l1','joint_arm_l2','joint_arm_l3','joint_wrist_yaw','joint_wrist_pitch','joint_wrist_roll']
  if self.phase=='slide_goal' and getattr(self,'active_tool',None)=='left_thumb' and self.tuning.get('bridge_lock_waist',False):names=[n for n in names if 'waist' not in n]
  js=[self.joints[n] for n in names if n in self.joints];qids=np.array([self.m.jnt_qposadr[j] for j in js]);vids=np.array([self.m.jnt_dofadr[j] for j in js]);lo=self.m.jnt_range[js,0].copy();hi=self.m.jnt_range[js,1].copy()
  for k,j in enumerate(js):
   n=self.m.joint(j).name
   if 'elbow' in n:lo[k]=max(lo[k],.05)
   if n=='left_shoulder_roll_joint':lo[k]=max(lo[k],-.10)
   if n=='right_shoulder_roll_joint':hi[k]=min(hi[k],.10)
   if n=='left_wrist_roll_joint' and self.phase not in ['turn','place','release'] and not getattr(self,'active_tool',None):lo[k]=.7
   if n=='right_wrist_roll_joint' and self.phase not in ['turn','place','release'] and not getattr(self,'active_tool',None):hi[k]=-.7
   if 'wrist_pitch' in n and self.tuning.get('wrist_clearance',False):lo[k],hi[k]=max(lo[k],-1.52),min(hi[k],1.52)
   if n=='waist_roll_joint':lo[k],hi[k]=-.25,.25
   if n=='waist_pitch_joint':lo[k],hi[k]=-.3,.5
  for _ in range(70):
   mujoco.mj_forward(self.ikm,self.ik);rows=[];errs=[]
   for side,(p,R) in goals.items():
    b,offset=self.hand_defs()[side];now,rot=self.hand_pose(side,self.ik);jp=np.zeros((3,self.m.nv));jr=jp.copy();mujoco.mj_jac(self.ikm,self.ik,jp,jr,now,b)
    rows.append(jp[:,vids]);errs.append(np.asarray(p)-now)
    if R is not None:
     weight=self.tuning.get('turn_orientation_weight',.15) if self.phase in ['turn','place'] else .15
     if side=='left' and self.phase=='slide_goal' and getattr(self,'active_tool',None)=='left_thumb' and self.tuning.get('bridge_axial_push',False):
      axis=rot[:,1];projector=np.eye(3)-np.outer(axis,axis);rows.append(weight*projector@jr[:,vids]);errs.append(weight*np.cross(axis,R[:,1]))
     else:rows.append(weight*jr[:,vids]);errs.append(weight*Rotation.from_matrix(R@rot.T).as_rotvec())
   for contact in self.ik.contact:
    ba,bb=[int(self.m.geom_bodyid[g]) for g in contact.geom]
    if ba<=0 or bb<=0 or self.obj in [ba,bb] or contact.dist>=.002:continue
    ja=np.zeros((3,self.m.nv));jb=ja.copy();mujoco.mj_jac(self.ikm,self.ik,ja,None,contact.pos,ba);mujoco.mj_jac(self.ikm,self.ik,jb,None,contact.pos,bb)
    collision_weight=self.tuning.get('collision_weight',4.)
    rows.append((collision_weight*(contact.frame[:3]@(jb[:,vids]-ja[:,vids])))[None,:]);errs.append(np.array([collision_weight*(.002-contact.dist)]))
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
    target=((self.tuning.get('deep_load_n',2.5) if getattr(self,'deep_grasp',False) else self.tuning.get('dex3_load_n',1.5))+(.3 if face=='bottom' else -.3)*normal) if ready else .2
    key=(side,face);error=target-loads[side][face];previous=self.pinch_errors.get(key,error);filtered=previous+.02/.12*(error-previous);self.pinch_errors[key]=filtered
    velocity=(.025 if face=='bottom' else .02) if not self.pinch_touched[side][face] else np.clip(.008*error,-.015,.015)
    velocity=np.clip(velocity+.04*(filtered-previous)/.02,-.10,.10)
    if self.contacts()[0]>self.tuning.get('dex3_soft_total_n',12):velocity=min(velocity,-.04)
    if face=='bottom':increment('thumb_1',-sign*velocity)
    else:
     for f in ['index','middle']:increment(f+'_0',sign*velocity)
  return loads
 def regulate_six_contacts(self):
  from .wrench import allocate_normal_forces
  normal=self.d.xmat[self.obj].reshape(3,3)[:,2];rot=self.d.xmat[self.obj].reshape(3,3);centre=self.d.xipos[self.obj].copy()
  keys=[(s,f) for s in ['left','right'] for f in ['thumb','index','middle']]
  loads={k:0. for k in keys};points={k:np.zeros(3) for k in keys};tangent=np.zeros(3)
  for c in self.contacts()[-1]:
   key=next((k for k in keys if c['body'].startswith(k[0]+'_hand_'+k[1])),None)
   if key is None:continue
   force=np.array(c['force_on_disk_world']);point=np.array(c['position']);value=max(0.,(1 if key[1]=='thumb' else -1)*float(force@normal))
   loads[key]+=value;points[key]+=value*(rot.T@(point-centre));tangent+=np.cross(point-centre,force-(force@normal)*normal)
  if not hasattr(self,'six_points'):self.six_points={};self.six_errors={};self.six_touched={k:False for k in keys}
  for k in keys:
   self.six_touched[k] |= loads[k]>.1
   if loads[k]>.02:self.six_points[k]=points[k]/loads[k]
  ready=all(self.six_touched.values());base=self.tuning.get('deep_load_n',2.5);weight=float(self.m.body_mass[self.obj])*9.81
  reference=np.array([v for _ in ['left','right'] for v in [base+weight*normal[2]/4,(base-weight*normal[2]/4)/2,(base-weight*normal[2]/4)/2]])
  targets=reference if ready else np.array([.2]*6);self.wrench_feasible=False
  if hasattr(self,'handoff_progress'):
   progress=self.handoff_progress
   targets=np.array([base*(1-progress)+weight*normal[2]*(1-progress)/4,*[(base*(1-progress)-weight*normal[2]*(1-progress)/4)/2]*2,base+weight*normal[2]*(1+progress)/4,*[(base-weight*normal[2]*(1+progress)/4)/2]*2])
  if ready and len(self.six_points)==6 and not hasattr(self,'handoff_progress'):
   locations=np.array([centre+rot@self.six_points[k] for k in keys])
   for total in [4*base,12.,14.]:
    allocation=allocate_normal_forces(locations,centre,normal,weight,reference,total,tangent_torque=tangent,maximum=self.tuning.get('maximum_group_normal_n',3.5 if self.profile=='P3' else 4.),active_mask=[loads[k]>.05 for k in keys] if self.tuning.get('mask_lost_contacts',False) else None)
    if allocation is not None:targets=allocation;self.wrench_feasible=True;break
  if hasattr(self,'handoff_progress') or self.tuning.get('active_contact_fallback',False) and normal[2]<-.9:
   if not hasattr(self,'handoff_progress'):targets=reference.copy()
   for side in ['left','right']:
    available=[k for k in keys if k[0]==side and k[1]!='thumb' and loads[k]>.05]
    if available:
     total=sum(targets[keys.index((side,f))] for f in ['index','middle'])
     for f in ['index','middle']:targets[keys.index((side,f))]=total/len(available) if (side,f) in available else 0.
  if self.tuning.get('force_target_slew',False):
   previous=getattr(self,'filtered_force_targets',np.full(6,.2));targets=previous+np.clip(targets-previous,-.02,.02);self.filtered_force_targets=targets.copy()
  total_force=self.contacts()[0]
  for side,sign in [('left',-1),('right',1)]:
   if side in getattr(self,'open_hands',set()):
    for part,want in [('thumb_1',-sign*.3),('thumb_2',0.),('index_0',sign*.02),('index_1',sign*.02),('middle_0',sign*.02),('middle_1',sign*.02)]:
     n=f'{side}_hand_{part}_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*np.clip(.8*(want-self.d.qpos[qi]),-.08,.08))
    continue
   if side in getattr(self,'frozen_hands',set()):continue
   def inc(part,velocity):
    n=f'{side}_hand_{part}_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*velocity)
   def actual(part):return self.d.qpos[self.m.jnt_qposadr[self.joints[f'{side}_hand_{part}_joint']]]
   inc('thumb_2',np.clip(.8*(-sign*np.pi/2-actual('thumb_1')-actual('thumb_2')),-.04,.04))
   for finger in ['index','middle']:inc(finger+'_1',np.clip(.5*(sign*.5-actual(finger+'_1')),-.02,.02))
   for finger in ['thumb','index','middle']:
    k=(side,finger);error=targets[keys.index(k)]-loads[k];previous=self.six_errors.get(k,error);filtered=previous+.02/.12*(error-previous);self.six_errors[k]=filtered
    velocity=(.025 if finger=='thumb' else .02) if not self.six_touched[k] else np.clip(.008*error,-.015,.015)
    velocity=np.clip((3. if self.phase=='turn' and self.tuning.get('turn_feedback',False) else 1.)*velocity+.04*(filtered-previous)/.02,-.10,.10)
    if self.profile=='P3' and self.tuning.get('local_load_feedback',False):
     magnitude=sum(c['force_n'] for c in self.contacts()[-1] if c['body'].startswith(side+'_hand_'+finger))
     if magnitude>3.0:velocity=min(velocity,-min(.08,.06*(magnitude-3.0)))
    if total_force>14:velocity=min(velocity,-.04)
    inc('thumb_1' if finger=='thumb' else finger+'_0',(-sign if finger=='thumb' else sign)*velocity)
  return loads
 def regulate_inspire(self):
  for side in (['L','R'] if self.tuning.get('inspire_bimanual',False) else ['R']):
   loads={'thumb':0.,'fingers':0.}
   for c in self.contacts()[-1]:
    if c['body'].startswith(side+'_'):
     if self.tuning.get('inspire_bimanual',False) and not any(part in c['body'] for part in ['thumb','index']):continue
     loads['thumb' if 'thumb' in c['body'] else 'fingers']+=c['force_n']
   if not hasattr(self,'inspire_touched'):self.inspire_touched={}
   touched=self.inspire_touched.setdefault(side,{k:False for k in loads})
   for k,v in loads.items():touched[k] |= v>.1
   ready=all(touched.values());fingers=self.tuning.get('inspire_fingers',['index'] if self.tuning.get('inspire_index_only',False) else ['index','middle','ring','pinky'])
   for face,names in [('thumb',['thumb_proximal_pitch']),('fingers',[f+'_proximal' for f in fingers])]:
    target=(self.tuning.get('inspire_thumb_n',2.8) if face=='thumb' else self.tuning.get('inspire_fingers_n',2.2)) if ready else .2
    speed=(.015 if face=='thumb' else .007) if not touched[face] else np.clip(.006*(target-loads[face]),-.025,.015)
    if self.contacts()[0]>self.tuning.get('inspire_total_target_cap',11):speed=min(speed,-.02)
    for name in names:
     n=side+'_'+name+'_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*speed)
 def regulate_sg3(self):
  contacts=self.contacts()[-1];force=self.contacts()[0];qi=self.m.jnt_qposadr[self.joints['joint_gripper_slide']]
  desired=getattr(self,'sg3_load_override',self.tuning.get('deep_sg3_load_n',self.tuning.get('sg3_load_n',6.)) if getattr(self,'deep_grasp',False) else self.tuning.get('sg3_load_n',6.))
  if not hasattr(self,'sg3_lock_time'):self.sg3_lock_time=0.
  tips={side:sum(c['force_n'] for c in contacts if c['body']=='rubber_tip_'+side) for side in ['left','right']}
  if all(v>.05 for v in tips.values()):self.sg3_lock_time+=.02
  locked=self.sg3_lock_time>.2
  target=min(desired,.3+desired*self.sg3_lock_time/3) if locked else .15
  velocity=np.clip(.0005*(force-target),-.003,.006)
  if getattr(self,'sg3_releasing',False):velocity=max(.0005*(force-target),.0002)
  elif force<.02:velocity=-.0006 if getattr(self,'deep_grasp',False) else -.003
  self.joint_set(self.qref,'joint_gripper_slide',self.qref[qi]+.02*velocity)
  if not locked and force>.05 and self.phase=='close':
   normal=self.d.xmat[self.obj].reshape(3,3)[:,2]
   normal_force=sum(np.dot(c['force_on_disk_world'],normal) for c in contacts if c['body'].startswith('rubber_tip'))
   p,R=self.nominal_hand_pose('right');goal=p-np.clip(normal_force*.01,-.003,.003)*.02*normal
   solution,_=self.solve({'right':(goal,R)},seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['wrist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
 def command(self):
  if self.mode=='torque':
   for a,j in enumerate(self.actj):
    name=self.m.joint(int(j)).name;qi=self.m.jnt_qposadr[j];vi=self.m.jnt_dofadr[j]
    finger='hand' in name or name.startswith(('L_','R_'));kp,kd=(self.tuning.get('finger_servo_kp',6.),self.tuning.get('finger_servo_kd',.25)) if finger else (40.,3.) if 'wrist' in name else (150.,8.)
    if finger and self.body=='F' and getattr(self,'active_tool',None):kp=self.tuning.get('inspire_push_finger_kp',6.)
    if self.tuning.get('soft_servo',False):
     kp,kd=(2.4,.25) if finger else (14.,1.5) if 'wrist' in name else (40.,5.) if any(k in name for k in ['shoulder','elbow']) else (150.,8.)
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
  if self.d.time+.02>600.000001:raise RuntimeError('episode_time_limit')
  if self.body=='G' and self.phase=='close' and self.tuning.get('tangent_admittance',False) and not self.tuning.get('admittance_turn_only',False):
   _,deltas=self.tangent_admittance();targets={s:(self.nominal_hand_pose(s)[0]+delta,self.nominal_hand_pose(s)[1]) for s,delta in deltas.items()};solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
  if self.phase=='close' and hasattr(self,'close_goals'):
   drift=self.d.xpos[self.obj]-self.close_disk_origin;drift[2]=0.;self.close_drift+=np.clip(drift-self.close_drift,-.002*.02,.002*.02)
   targets={}
   for side,(p,R) in self.close_goals.items():
    actual,rot=self.hand_pose(side);nominal,Rnom=self.nominal_hand_pose(side);er=Rotation.from_matrix(R@rot.T).as_rotvec()
    targets[side]=(nominal+np.clip(.08*(p+self.close_drift-actual),-.00008,.00008),Rotation.from_rotvec(np.clip(.06*er,-.0005,.0005)).as_matrix()@Rnom)
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
  if getattr(self,'pressure_control',False):
   if self.body=='G':
    if getattr(self,'deep_grasp',False) and self.tuning.get('wrench_control',False):self.regulate_six_contacts()
    else:self.regulate_pinch()
   elif self.body=='S':self.regulate_sg3()
   elif self.body=='F':self.regulate_inspire()
  # References slewed at 0.5 rad/s; prismatic references at 0.05 m/s.
  for n,j in self.joints.items():
   qi=self.m.jnt_qposadr[j];rate=.05 if self.m.jnt_type[j]==mujoco.mjtJoint.mjJNT_SLIDE else .5
   self.qref[qi]=self.last_ref[qi]+np.clip(self.qref[qi]-self.last_ref[qi],-rate*.02,rate*.02)
  checked=self.action_interface.accept(self.action_interface.encode(self.qref))
  for j in self.action_interface.joints.values():self.qref[self.m.jnt_qposadr[j]]=checked[self.m.jnt_qposadr[j]]
  self.last_ref=self.qref.copy()
  for _ in range(round(.02/self.dt)):
   self.command();mujoco.mj_step(self.m,self.d);self.records.append((self.d.time,self.d.qpos.copy(),self.d.qvel.copy(),self.d.ctrl.copy(),self.qref.copy(),self.phase));row=self.assess()
  self.tick+=1;self.trace.write(json.dumps(row)+'\n')
  if self.tick%5==0:self.render()
  if self.tick%100==0:
   self.trace.flush();print(json.dumps({k:row[k] for k in ['time','phase','disk_pos','robot_force','table_force']}),flush=True)
   write(self.out/'live-state.json',dict(time=float(self.d.time),phase=self.phase,active_tool=getattr(self,'active_tool',None),hands={s:dict(position=self.hand_pose(s)[0].tolist(),rotation=self.hand_pose(s)[1].tolist()) for s in self.hand_defs()},qpos=self.d.qpos.tolist(),qvel=self.d.qvel.tolist(),reference=self.qref.tolist()))
 def move(self,phase,goals=None,seconds=4,target=None):
  self.phase=phase;self.events.append({'phase':phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  start={s:self.nominal_hand_pose(s) for s in goals} if goals else None;q0=self.qref.copy()
  bridge_feedback=self.body=='G' and phase=='place' and self.tuning.get('bridge_transport_feedback',False) and getattr(self,'handoff_progress',0.)>=.99 and goals and 'right' in goals
  if bridge_feedback:self.attitude_rotvec=np.zeros(3)
  for i in range(round(seconds/.02)):
   u=smooth((i+1)/round(seconds/.02))
   if goals:
    current={}
    for s,(p,R) in goals.items():
     p0,R0=start[s];rot=Rotation.from_rotvec(u*Rotation.from_matrix(R@R0.T).as_rotvec()).as_matrix()@R0 if R is not None else None
     current[s]=(p0+u*(p-p0),rot)
    if self.body=='G' and phase=='lift' and self.tuning.get('tangent_admittance',False) and not self.tuning.get('admittance_turn_only',False):
     offsets,_=self.tangent_admittance();current={s:(p+offsets[s],R) for s,(p,R) in current.items()}
    if bridge_feedback:
     correction=self.attitude_correction(np.array([0.,0.,-1.]));centre=self.d.xpos[self.obj].copy();p,R=current['right'];current['right']=(centre+correction@(p-centre),correction@R)
    solution,err=self.solve(current,seed=self.qref)
    for n,j in self.joints.items():
     if any(k in n for k in ['shoulder','elbow','wrist','waist']) or self.body=='S' and any(k in n for k in ['joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   elif target is not None:self.qref=q0+u*(target-q0)
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if goals:
   residual={s:float(np.linalg.norm(p-self.hand_pose(s)[0])) for s,(p,R) in goals.items()};self.events[-1]['position_errors_m']=residual
   if max(residual.values())>.025:raise RuntimeError('grasp_pose_not_reached:'+str(residual))
 def tangent_admittance(self):
  if getattr(self,'admittance_phase',None)!=self.phase:
   self.admittance_phase=self.phase;self.admittance_offsets={s:np.zeros(3) for s in ['left','right']}
  normal=self.d.xmat[self.obj].reshape(3,3)[:,2];previous={s:p.copy() for s,p in self.admittance_offsets.items()}
  for side in self.admittance_offsets:
   force=sum((np.array(c['force_on_disk_world']) for c in self.contacts()[-1] if c['body'].startswith(side+'_hand_')),start=np.zeros(3))
   residual=force-np.array([0.,0.,.5*1.1772]);tangent=residual-normal*np.dot(residual,normal)
   self.admittance_offsets[side]=np.clip(previous[side]-.02*np.clip(self.tuning.get('tangent_gain',.002)*tangent,-.002,.002),-.015,.015)
  return self.admittance_offsets,{s:self.admittance_offsets[s]-previous[s] for s in previous}
 def attitude_correction(self,desired):
  normal=self.d.xmat[self.obj].reshape(3,3)[:,2];correction=2*np.cross(normal,desired);length=np.linalg.norm(correction)
  if length>.16:correction*=.16/length
  previous=getattr(self,'attitude_rotvec',np.zeros(3));change=.02/.27*(correction-previous);length=np.linalg.norm(change)
  if length>.08*.02:change*=.08*.02/length
  self.attitude_rotvec=previous+change
  return Rotation.from_rotvec(self.attitude_rotvec).as_matrix()
 def execute(self):
  self.move('settle',seconds=2)
  if self.tuning.get('prepush',False):self.prepush_disk()
  if self.body=='F' and self.tuning.get('inspire_park_left',False):self.move('orient_clear',{'left':(np.array([.15,.30,1.05]),None),'right':self.nominal_hand_pose('right')},seconds=14)
  self.move('preshape',target=self.preshape(),seconds=4)
  disk=self.d.xpos[self.obj].copy()
  if self.body=='S':
   # First candidate: near-edge pinch with the finger closing axis vertical.
   _,R=self.hand_pose('right');R=Rotation.from_euler('x',np.pi/2).as_matrix()@R
   goals={'right':(disk+[self.tuning.get('sg3_grasp_x',-.085),0,0],R)}
  else:
   goals={s:(disk+[-.10 if s=='left' else -.07,sign*(.15 if self.body=='F' else self.tuning.get('grasp_y',.09)),.044],Rotation.from_euler('z',-sign*np.pi/2).as_matrix()@Rotation.from_euler('x',sign*np.pi/2).as_matrix()) for s,sign in [('left',1),('right',-1)]}
  if self.body=='G' and self.tuning.get('prepush',False):goals={side:(np.array([disk[0]-(.068 if side=='left' else .039),disk[1]+sgn*.09,disk[2]+(.044 if self.profile=='P1' else .05)]),R) for (side,(p,R)),sgn in zip(goals.items(),[1,-1])}
  if self.body=='G' and self.tuning.get('grasp_inward_yaw',0.):
   for side,sign in [('left',1),('right',-1)]:
    p,R=goals[side];p=p+[-self.tuning.get('grasp_back_offset',.005),sign*self.tuning.get('grasp_out_offset',.005),0];R=Rotation.from_euler('z',sign*self.tuning['grasp_inward_yaw']).as_matrix()@R;goals[side]=(p,R)
  pre={s:(p+[-.12,(.06 if s=='left' else -.06) if self.body!='S' else 0,.015],R) for s,(p,R) in goals.items()}
  high={s:(p+[-.12,(.16 if s=='left' else -.16) if self.body!='S' else 0,.16 if self.body!='S' else .18],R) for s,(p,R) in goals.items()}
  if self.body!='S':
   pre={s:(np.array([.22,sign*(.24 if self.body=='F' else .18),.93]),goals[s][1]) for s,sign in [('left',1),('right',-1)]}
   if self.body=='F' and self.tuning.get('inspire_park_left',False) and not self.tuning.get('inspire_bimanual',False):pre['left']=self.nominal_hand_pose('left')
   seed=self.qref.copy()
   for side,sign in [('left',1),('right',-1)]:
    if side=='left' and self.body=='F' and self.tuning.get('inspire_park_left',False) and not self.tuning.get('inspire_bimanual',False):continue
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
  if self.body=='F' and self.tuning.get('inspire_bimanual',False):
   goals={side:(np.array([.355 if side=='left' else .375,sign*.145,disk[2]+.044]),Rotation.from_euler('z',sign*-.26).as_matrix()@R) for (side,(p,R)),sign in zip(goals.items(),[1,-1])}
  elif self.body=='F':
   p,R=goals['right'];R=Rotation.from_euler('z',self.tuning.get('inspire_hand_yaw',0.)) .as_matrix()@R;goals={'right':(p+np.array(self.tuning.get('inspire_offset',[.025,.02,0.])),R)}
   if 'inspire_absolute_x' in self.tuning:goals['right'][0][0]=self.tuning['inspire_absolute_x']
  if self.profile in ['P2','P3'] and self.body=='G' and not self.tuning.get('prepush',False):goals={s:(p+[-.02,0,.008],R) for s,(p,R) in goals.items()}
  self.move('insert',goals,seconds=self.tuning.get('insert_seconds',20))
  if self.tuning.get('align_grasp',False):self.align_grasp(goals)
  if self.body=='G':
   if self.tuning.get('close_pose_feedback',False):self.close_goals=goals;self.close_disk_origin=self.d.xpos[self.obj].copy();self.close_drift=np.zeros(3)
   if self.tuning.get('prepush',False):self.deep_grasp=True
   self.pressure_control=True;self.move('close',seconds=self.tuning.get('dex3_close_s',40))
   if not self.tuning.get('edge_regrasp',False) and not all(v>self.tuning.get('dex3_min_face_n',.8) for faces in self.pinch_loads().values() for v in faces.values()):raise RuntimeError('opposing_grasp_loads_not_established')
  elif self.body=='S':
   self.pressure_control=True;self.move('close',seconds=45)
  else:
   self.pressure_control=True;self.move('close',seconds=self.tuning.get('inspire_close_s',55))
  if self.contacts()[0]<.10:raise RuntimeError('no_measured_grasp_contact')
  if self.tuning.get('edge_regrasp',False):goals=self.edge_regrasp(goals)
  if self.body=='S' and self.tuning.get('require_sg3_grasp',False):self.establish_sg3_grasp()
  if self.body=='S' and self.tuning.get('supported_turn',False):return self.execute_sg3_supported()
  lift_delta=np.array([0.,0.,.16])
  if self.body=='G' and self.tuning.get('lift_back',False):lift_delta=np.array([.32,self.d.xpos[self.obj][1],1.025])-self.d.xpos[self.obj]
  lift={s:(self.nominal_hand_pose(s)[0]+lift_delta,self.nominal_hand_pose(s)[1]) for s in goals}
  self.move('lift',lift,seconds=40)
  if self.d.xpos[self.obj][2]<.99:raise RuntimeError('lift_without_object')
  centre=self.d.xpos[self.obj].copy();poses={s:self.nominal_hand_pose(s) for s in goals}
  self.phase='turn';self.events.append({'phase':'turn','start_s':float(self.d.time),'record_start':len(self.records)})
  for i in range(3000):
   R=Rotation.from_euler('x' if self.body=='S' else 'y',(-1 if self.body=='S' else 1)*np.pi*smooth((i+1)/3000)).as_matrix()
   correction=self.attitude_correction(R@np.array([0.,0.,1.])) if self.tuning.get('turn_feedback',False) else np.eye(3)
   if self.tuning.get('turn_feedback',False):
    self.turn_height_offset=np.clip(getattr(self,'turn_height_offset',0.)+.02*np.clip(.5*(centre[2]+.01-self.d.xpos[self.obj][2]),-.001,.003),0.,.06)
   if self.tuning.get('turn_follow_xy',False):
    desired_drift=self.d.xpos[self.obj]-centre;desired_drift[2]=0.;previous=getattr(self,'turn_xy_offset',np.zeros(3));self.turn_xy_offset=np.clip(previous+np.clip(.3*(desired_drift-previous),-.003*.02,.003*.02),-.06,.06)
   targets={s:(centre+getattr(self,'turn_xy_offset',np.zeros(3))+[0,0,getattr(self,'turn_height_offset',0.)]+correction@R@(p-centre),correction@R@rot) for s,(p,rot) in poses.items()}
   if self.body=='G' and self.tuning.get('tangent_admittance',False):
    offsets,_=self.tangent_admittance();targets={s:(p+offsets[s],rot) for s,(p,rot) in targets.items()}
   if self.body=='G' and self.tuning.get('palm_clearance_feedback',False):
    if not hasattr(self,'palm_offsets'):self.palm_offsets={s:np.zeros(3) for s in targets}
    for side in targets:self.palm_offsets[side]=np.clip(self.palm_offsets[side]+self.palm_clearance_increment(side),-.025,.025)
    targets={s:(p+self.palm_offsets[s],rot) for s,(p,rot) in targets.items()}
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
   if self.body=='G' and self.tuning.get('align_inversion',False) and (i+1)*.02>=self.tuning.get('inversion_alignment_after_s',0.) and self.d.xmat[self.obj].reshape(3,3)[2,2]<self.tuning.get('inversion_alignment_switch',-.90):break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if self.body=='S' and self.tuning.get('edge_regrasp',False):return self.finish_sg3_edge()
  if self.body=='G' and self.tuning.get('align_inversion',False):self.align_inverted_grasp()
  if self.body=='G' and self.tuning.get('bridge_place',False):return self.finish_dex3_bridge()
  delta=np.array([.5,0,.866])-self.d.xpos[self.obj]
  self.move('place',{s:(self.hand_pose(s)[0]+delta,self.hand_pose(s)[1]) for s in goals},seconds=15)
  self.pressure_control=False
  self.move('release',target=self.preshape(close=0),seconds=5)
  self.move('release',{s:(self.hand_pose(s)[0]+[-.08,0,.08],self.hand_pose(s)[1]) for s in goals},seconds=8)
  self.move('release',seconds=3)
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def palm_clearance_increment(self,side):
  force=sum((np.array(c['force_on_disk_world']) for c in self.contacts()[-1] if c['body']==side+'_hand_palm_link'),start=np.zeros(3))
  return -.02*np.clip(.002*force,-.003,.003)
 def align_inverted_grasp(self):
  self.phase='turn';self.events.append({'phase':'turn','start_s':float(self.d.time),'record_start':len(self.records)})
  target_centre=self.d.xpos[self.obj].copy();stable=0.
  self.six_points={};self.six_errors={}
  normal=self.d.xmat[self.obj].reshape(3,3)[:,2]
  self.filtered_force_targets=np.array([sum(max(0.,(1 if finger=='thumb' else -1)*np.dot(c['force_on_disk_world'],normal)) for c in self.contacts()[-1] if c['body'].startswith(side+'_hand_'+finger)) for side in ['left','right'] for finger in ['thumb','index','middle']])
  for _ in range(2000):
   centre=self.d.xpos[self.obj].copy();normal=self.d.xmat[self.obj].reshape(3,3)[:,2]
   rotation=Rotation.from_rotvec(.02*np.clip(.5*np.cross(normal,[0,0,-1]),-.03,.03)).as_matrix()
   translation=.02*np.clip(.5*(target_centre-centre),-.002,.002)
   hands={s:self.nominal_hand_pose(s) for s in ['left','right']}
   self.apply_goals({s:(centre+translation+rotation@(p-centre)+(self.palm_clearance_increment(s) if self.tuning.get('palm_clearance_feedback',False) else 0),rotation@R) for s,(p,R) in hands.items()})
   stable=stable+.02 if normal[2]<-np.cos(np.deg2rad(2)) else 0.
   if stable>=.5:break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if stable<.5:raise RuntimeError('inverted_grasp_alignment_not_established')
 def prepush_disk(self):
  target=self.qref.copy()
  for n in self.joints:
   if n.startswith('left_hand_') or self.body=='F' and n.startswith('L_') and 'yaw' not in n:self.joint_set(target,n,0.)
  if self.body=='F' and self.tuning.get('inspire_index_push',False):
   for finger in ['middle','ring','pinky']:
    for part in ['proximal','intermediate']:self.joint_set(target,f'L_{finger}_{part}_joint',.6)
  self.move('edge_slide',target=target,seconds=6)
  self.tool_hold={'right':self.hand_pose('right')}
  use_index=self.body=='F' and self.tuning.get('inspire_index_push',False)
  if use_index:
   idle=(np.array([.15,-.25,1.1]),None);self.move('edge_slide',{'left':self.hand_pose('left'),'right':idle},seconds=10);self.tool_hold={'right':idle}
  self.active_tool='left_thumb' if self.body=='G' else 'left_index' if use_index else 'left_inspire_thumb'
  disk=self.d.xpos[self.obj].copy();R=Rotation.from_euler('x',np.pi/2).as_matrix() if self.body=='G' or use_index else Rotation.from_euler('z',np.pi/2).as_matrix()@Rotation.from_euler('y',np.pi/2).as_matrix()
  if use_index:R=Rotation.from_euler('y',self.tuning.get('inspire_push_pitch',0.)).as_matrix()@R
  tip=np.array([disk[0]+.125,disk[1],.90 if use_index else 1.00])
  self.move('edge_slide',{'left':(tip,R)},seconds=16)
  tip[2]=.862 if self.body=='G' else self.tuning.get('inspire_push_z',.876)
  self.move('edge_slide',{'left':(tip,R)},seconds=12);self.align_grasp({'left':(tip,R)})
  self.phase='edge_slide';self.events.append({'phase':'edge_slide','start_s':float(self.d.time),'record_start':len(self.records)})
  ref,R=self.nominal_hand_pose('left');desired=tip.copy()
  for _ in range(10000 if self.body=='F' else 4500):
   if self.d.xpos[self.obj][0]<=(self.tuning.get('inspire_edge_x',.363) if self.body=='F' else .363):break
   push_speed=self.tuning.get('inspire_push_speed',.002) if self.body=='F' else .002
   ref[0]-=push_speed*.02
   if self.body=='F':
    force=sum((np.array(c['force_on_disk_world']) for c in self.contacts()[-1] if c['body'].startswith('L_')),start=np.zeros(3))
    advance=push_speed if np.linalg.norm(force)<self.tuning.get('inspire_push_load_n',18.) else -push_speed
    desired[0]-=advance*.02;actual=self.hand_pose('left')[0];bound=push_speed*.02
    if force[2]<-.3:desired[2]+=min(push_speed,.0005)*.02
    if self.tuning.get('inspire_table_clearance',False) and self.contacts()[3]>1.:desired[2]+=.001*.02
    ref=self.nominal_hand_pose('left')[0]+[-advance*.02,0,0]+np.clip(self.tuning.get('inspire_push_feedback',.08)*(desired-actual),-bound,bound)
   solution,_=self.solve({'left':(ref,R)},seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if self.d.xpos[self.obj][0]>(self.tuning.get('inspire_edge_x',.370)+.005 if self.body=='F' else .375):raise RuntimeError('edge_push_not_established')
  if use_index and self.tuning.get('inspire_vertical_withdraw',False):
   self.move('edge_slide',{'left':(self.nominal_hand_pose('left')[0]+[0,0,.025],R)},seconds=10)
   self.move('edge_slide',{'left':(self.nominal_hand_pose('left')[0]+[-.1,0,.035],R)},seconds=12)
  else:
   self.move('edge_slide',{'left':(self.nominal_hand_pose('left')[0]+[.035,0,0],R)},seconds=6)
   self.move('edge_slide',{'left':(self.nominal_hand_pose('left')[0]+[-.1 if use_index else 0,0,.08 if use_index else .12],R)},seconds=8)
  self.active_tool=None
 def edge_regrasp(self,goals):
  self.phase='edge_slide';self.events.append({'phase':'edge_slide','start_s':float(self.d.time),'record_start':len(self.records)})
  poses={s:self.nominal_hand_pose(s) for s in goals};travel=0.
  for _ in range(4000):
   if self.d.xpos[self.obj][0]<=.363:break
   travel+=.002*.02
   targets={s:(p+[-travel,0,0],R) for s,(p,R) in poses.items()}
   solution,_=self.solve(targets,seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['shoulder','elbow','wrist','waist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.move('edge_slide',seconds=2)
  self.pressure_control=False
  if self.body=='S' and self.tuning.get('sg3_release_compensation',False):self.open_sg3_supported()
  else:self.move('regrasp_release',target=self.preshape(close=0),seconds=self.tuning.get('regrasp_release_s',8))
  self.move('pregrasp',{s:(self.nominal_hand_pose(s)[0]+[-.045,0,.03],self.nominal_hand_pose(s)[1]) for s in goals},seconds=10)
  disk=self.d.xpos[self.obj].copy()
  if abs(disk[0]-.36)>.018:raise RuntimeError('edge_regrasp_slide_position_not_established')
  if self.body=='S':
   target=self.qref.copy();self.joint_set(target,'joint_gripper_slide',.001);self.move('pregrasp',target=target,seconds=8)
   p,R=self.nominal_hand_pose('right');p[2]=disk[2]+self.tuning.get('sg3_insert_z_compensation',0.);self.move('pregrasp',{'right':(p,R)},seconds=8)
   goals={'right':(np.array([.338,disk[1],disk[2]+self.tuning.get('sg3_insert_z_compensation',0.)]),R)}
  else:
   target=self.qref.copy()
   self.joint_set(target,'left_hand_thumb_0_joint',.714);self.joint_set(target,'right_hand_thumb_0_joint',.342)
   self.move('pregrasp',target=target,seconds=5)
   goals={s:(np.array([disk[0]-(.068 if s=='left' else .039),disk[1]+(.09 if s=='left' else -.09),disk[2]+(.05 if self.profile!='P1' else .044)]),self.nominal_hand_pose(s)[1]) for s in goals}
  self.move('insert',goals,seconds=16)
  if self.body=='S' and not self.tuning.get('sg3_align_compensated',False):goals={'right':(np.array([.338,disk[1],disk[2]]),goals['right'][1])}
  self.align_grasp(goals)
  for key in ['pinch_touched','pinch_errors']:
   if hasattr(self,key):delattr(self,key)
  self.deep_grasp=True;self.sg3_lock_time=0.
  self.pressure_control=True;self.move('close',seconds=32 if self.body=='S' else 50)
  return goals
 def establish_sg3_grasp(self):
  self.phase='close';self.events.append({'phase':'close','start_s':float(self.d.time),'record_start':len(self.records)});stable=0.
  for _ in range(3000):
   loads={s:sum(c['force_n'] for c in self.contacts()[-1] if c['body']=='rubber_tip_'+s) for s in ['left','right']}
   stable=stable+.02 if min(loads.values())>1.5 else 0.
   if stable>=.5:break
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if stable<.5:raise RuntimeError('opposing_sg3_grasp_not_established')
 def apply_goals(self,goals):
  solution,_=self.solve(goals,seed=self.qref)
  for n,j in self.joints.items():
   if any(k in n for k in ['shoulder','elbow','wrist','waist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
  self.step()
 def finish_dex3_bridge(self):
  # All changes below are joint references; the table and measured contacts carry the plate.
  centre=self.d.xpos[self.obj].copy();hands={s:self.nominal_hand_pose(s) for s in ['left','right']}
  self.phase='place';self.events.append({'phase':'place','start_s':float(self.d.time),'record_start':len(self.records)})
  self.open_hands=set();stable=0.
  # The captured hand poses already include the final turn correction.
  # Start the next correction at identity so the phase boundary is continuous.
  self.attitude_rotvec=np.zeros(3)
  for i in range(1750):
   self.handoff_progress=smooth(min(1.,(i+1)/1000))
   forces={s:sum((np.array(c['force_on_disk_world']) for c in self.contacts()[-1] if c['body'].startswith(s+'_hand_')),start=np.zeros(3)) for s in hands}
   if self.handoff_progress>=.999 and forces['right'][2]>.8*1.1772 and forces['left'][2]<.25*1.1772:self.open_hands.add('left')
   correction=self.attitude_correction(np.array([0.,0.,-1.]))
   self.apply_goals({s:(centre+correction@(p-centre),correction@R) for s,(p,R) in hands.items()})
   load=sum(c['force_n'] for c in self.contacts()[-1] if c['body'].startswith('left_hand_'))
   stable=stable+.02 if 'left' in self.open_hands and load<.05 else 0.
   if stable>=.5:break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if stable<.5:raise RuntimeError('single_hand_bridge_transfer_not_established')
  return self.finish_dex3_bridge_after_transfer()
 def finish_dex3_bridge_after_transfer(self):
  edge_x=self.tuning.get('bridge_edge_x',.23)
  right=self.nominal_hand_pose('right');left=self.nominal_hand_pose('left')
  self.move('place',{'right':right,'left':(left[0]+[-.04,.15,.06],None)},seconds=12)
  delta=np.array([edge_x,0,self.d.xpos[self.obj][2]])-self.d.xpos[self.obj]
  self.move('place',{'right':(self.nominal_hand_pose('right')[0]+delta,self.nominal_hand_pose('right')[1]),'left':self.nominal_hand_pose('left')},seconds=20)
  delta=np.array([edge_x,0,.870])-self.d.xpos[self.obj]
  self.move('place',{'right':(self.nominal_hand_pose('right')[0]+delta,self.nominal_hand_pose('right')[1]),'left':self.nominal_hand_pose('left')},seconds=25)
  self.phase='place';self.events.append({'phase':'place','start_s':float(self.d.time),'record_start':len(self.records)})
  for _ in range(500):
   delta=np.clip(.15*(np.array([edge_x,0,.870])-self.d.xpos[self.obj]),-.00004,.00004)
   p,R=self.nominal_hand_pose('right');self.apply_goals({'right':(p+delta,R),'left':self.nominal_hand_pose('left')})
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  return self.finish_dex3_push_from_bridge()
 def finish_dex3_push_from_bridge(self):
  self.frozen_hands={'left','right'} if self.tuning.get('bridge_freeze_support',False) else {'left'};self.open_hands=set();self.attitude_rotvec=np.zeros(3)
  target=self.qref.copy()
  for n in self.joints:
   if n.startswith('left_hand_'):self.joint_set(target,n,-self.tuning.get('bridge_pusher_fold',0.) if any(f in n for f in ['index','middle']) else 0.)
  self.move('place',target=target,seconds=6)
  self.tool_hold={'right':self.nominal_hand_pose('right')};self.active_tool='left_thumb'
  R=Rotation.from_euler('z',-np.pi/2).as_matrix()@Rotation.from_euler('x',np.pi/2).as_matrix()
  if 'bridge_horizontal_yaw' in self.tuning:R=Rotation.from_euler('z',self.tuning['bridge_horizontal_yaw'],degrees=True).as_matrix()
  disk=self.d.xpos[self.obj].copy();tip=disk+[-self.tuning.get('bridge_push_back',.125),self.tuning.get('bridge_push_side_y',0.),.12]
  free=self.tuning.get('bridge_free_push_orientation',False)
  if self.tuning.get('bridge_side_approach',False):
   outer=disk+[-.035,.20,-.004];self.move('slide_goal',{'left':(outer,R)},seconds=12);tip[2]=disk[2]-.004
  else:self.move('slide_goal',{'left':(tip,None if free else R)},seconds=12);tip[2]=disk[2]-.004
  self.move('slide_goal',{'left':(tip,None if free else R)},seconds=10)
  if free:R=self.hand_pose('left')[1]
  self.align_grasp({'left':(tip,R)})
  self.frozen_hands={'left','right'}
  rightp,rightR=self.tool_hold['right'];rightp=rightp.copy();right_anchor=rightp.copy();tip,R=self.nominal_hand_pose('left')
  thumb_angle=sum(self.d.qpos[self.m.jnt_qposadr[self.joints['right_hand_'+part+'_joint']]] for part in ['thumb_1','thumb_2'])
  self.phase='slide_goal';self.events.append({'phase':'slide_goal','start_s':float(self.d.time),'record_start':len(self.records)})
  released=False;withdraw=False
  for _ in range(7500):
   disk=self.d.xpos[self.obj].copy();contacts=self.contacts()[-1];tableload=self.contacts()[1]
   leftforce=sum((np.array(c['force_on_disk_world']) for c in contacts if c['body'].startswith('left_hand_')),start=np.zeros(3))
   rightload=sum(c['force_n'] for c in contacts if c['body'].startswith('right_hand_'))
   if disk[0]>.365 and tableload>.4*1.1772:withdraw=True
   if disk[0]+.1>.365 and np.linalg.norm(leftforce)>.5:released=True
   if not withdraw or rightload<.05:tip[0]+=self.tuning.get('bridge_push_speed',.002)*.02
   upward=[(np.array(c['position']),c['force_on_disk_world'][2]) for c in contacts if c['body'].startswith('right_hand_') and c['force_on_disk_world'][2]>.05]
   support_x=sum(p[0]*f for p,f in upward)/sum(f for _,f in upward) if upward else disk[0]
   upward_target=np.clip(1.1772*(support_x-disk[0])/max(.05,support_x-tip[0])-.03,0.,.9)
   tip[2]+=.02*np.clip(.003*(upward_target-leftforce[2]),-.001,.001)
   tip[2]=np.clip(tip[2],disk[2]-.006,disk[2]+.001)
   if released:
    for part,want in [('thumb_1',.35),('thumb_2',0.)]:
     n='right_hand_'+part+'_joint';qi=self.m.jnt_qposadr[self.joints[n]];self.joint_set(self.qref,n,self.qref[qi]+.02*np.clip(.8*(want-self.d.qpos[qi]),-.08,.08))
   else:
    pressure=sum(max(0.,-c['force_on_disk_world'][2]) for c in contacts if c['body'].startswith('right_hand_thumb_'))
    target=.4 if leftforce[2]>.1 or disk[0]>.25 else 1.8
    qi=self.m.jnt_qposadr[self.joints['right_hand_thumb_1_joint']];self.joint_set(self.qref,'right_hand_thumb_1_joint',self.qref[qi]-.02*np.clip(.024*(target-pressure),-.04,.04))
    qi2=self.m.jnt_qposadr[self.joints['right_hand_thumb_2_joint']];self.joint_set(self.qref,'right_hand_thumb_2_joint',self.qref[qi2]+.02*np.clip(.8*(thumb_angle-self.d.qpos[qi]-self.d.qpos[qi2]),-.04,.04))
   if withdraw:
    rightp[0]=max(right_anchor[0]-.08,rightp[0]-.004*.02);rightp[2]=max(right_anchor[2]-.025,rightp[2]-.002*.02)
    tip[2]+=.02*np.clip(2*(.862-tip[2]),-.002,.002)
   elif disk[0]+.1>.365:rightp[2]=max(right_anchor[2]-.008,rightp[2]-.0005*.02)
   if self.contacts()[0]>12:tip[0]-=.003*.02
   self.tool_hold={'right':(rightp,rightR)};self.apply_goals({'left':(tip,R)})
   if disk[0]>=.49 and rightload<.05:break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.pressure_control=False
  self.move('release',{'left':(tip+[-.035,0,0],R)},seconds=6)
  self.move('release',{'left':(tip+[-.035,0,.12],R)},seconds=6)
  self.active_tool=None;self.move('release',seconds=3)
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def open_sg3_supported(self):
  self.pressure_control=False;qi=self.m.jnt_qposadr[self.joints['joint_gripper_slide']];start=float(self.qref[qi]);hand,R=self.nominal_hand_pose('right')
  def offset(value):
   self.ik.qpos[:]=self.qref;self.ik.qpos[qi]=value
   for side in ['left','right']:self.ik.qpos[self.m.jnt_qposadr[self.joints['joint_gripper_finger_'+side+'_open']]]=10*value
   mujoco.mj_forward(self.ikm,self.ik)
   return np.mean([self.ik.xpos[self.m.body('rubber_tip_'+side).id] for side in ['left','right']],axis=0)-self.hand_pose('right',self.ik)[0]
  initial=offset(start);self.phase='regrasp_release';self.events.append({'phase':self.phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  for i in range(800):
   value=start+smooth((i+1)/800)*(.025-start);delta=offset(value)-initial;delta[2]=0.
   self.joint_set(self.qref,'joint_gripper_slide',value);self.apply_goals({'right':(hand-delta,R)})
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
 def release_sg3_on_table(self):
  self.phase='place';self.events.append({'phase':self.phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  p,R=self.nominal_hand_pose('right');stable=0.
  for _ in range(1600 if self.tuning.get('sg3_level_support',False) else 800):
   loaded=self.contacts()[1]>=.85*1.1772
   normal=self.d.xmat[self.obj].reshape(3,3)[:,2]
   level=np.linalg.norm(normal[:2])<self.tuning.get('sg3_release_level_tolerance',.0008) and normal[2]<0
   if self.tuning.get('sg3_level_support',False):
    rotation=Rotation.from_rotvec(.02*np.clip(.5*np.cross(normal,[0,0,-1]),-.006,.006)).as_matrix()
    centre=self.d.xpos[self.obj].copy();p=centre+rotation@(p-centre);R=rotation@R
   supported=loaded and (level or not self.tuning.get('sg3_level_support',False))
   if not loaded:p[2]-=.0005*.02
   self.apply_goals({'right':(p,R)})
   stable=stable+.02 if supported else 0.
   if stable>=.3:break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  if stable<.3:raise RuntimeError('table_load_transfer_not_established')
  if self.tuning.get('sg3_direct_slow_release',False):
   self.pressure_control=False;self.move('release',target=self.preshape(close=0),seconds=60);return
  if self.tuning.get('sg3_release_downward',False):return self.unload_sg3_downward(p,R)
  self.phase='release';self.events.append({'phase':self.phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  initial=self.contacts()[0];self.sg3_releasing=True;released=0.
  for i in range(900):
   self.sg3_load_override=max(0.,initial*(1-min(1.,(i+1)/400)))
   if self.tuning.get('sg3_withdraw_during_release',False):
    if self.contacts()[0]<4.:p[0]-=.003*.02
    self.apply_goals({'right':(p,R)})
   else:self.step()
   released=released+.02 if self.contacts()[0]<.05 else 0.
   if released>=.3:break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.pressure_control=False;self.sg3_releasing=False
  if released<.3:raise RuntimeError('force_controlled_release_not_established')
 def unload_sg3_downward(self,p,R):
  # Bias residual contact downward so the lower pad can leave without lifting the plate.
  self.phase='release';self.events.append({'phase':self.phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  self.sg3_releasing=True;initial=self.contacts()[0];qi=self.m.jnt_qposadr[self.joints['joint_gripper_slide']];qstart=float(self.d.qpos[qi]);xstart=float(p[0]);opened=False
  for i in range(3000):
   self.sg3_load_override=max(.45,initial*(1-min(1.,(i+1)/600)))
   p[2]+=.02*np.clip(.001*(self.contacts()[1]-1.6),-.0006,.0006)
   p[0]=xstart-1.2*max(0.,self.d.qpos[qi]-qstart)
   self.apply_goals({'right':(p,R)})
   lower=sum(max(0.,c['force_on_disk_world'][2]) for c in self.contacts()[-1] if c['body'].startswith('rubber_tip'))
   if self.d.qpos[qi]>.002 and lower<.05:opened=True;break
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.pressure_control=False;self.sg3_releasing=False
  if not opened:raise RuntimeError('lower_pad_release_not_established')
  self.move('release',{'right':(self.nominal_hand_pose('right')[0]+[0,0,.006],R)},seconds=6)
  self.move('release',seconds=1)
  if self.contacts()[0]>.05:raise RuntimeError('upper_pad_release_not_established')
 def withdraw_sg3(self):
  if self.tuning.get('sg3_horizontal_withdraw',False):
   self.move('release',{'right':(self.nominal_hand_pose('right')[0]+[-.12,0,0],self.nominal_hand_pose('right')[1])},seconds=16)
   self.move('release',{'right':(self.nominal_hand_pose('right')[0]+[0,0,.07],self.nominal_hand_pose('right')[1])},seconds=6)
  else:self.move('release',{'right':(self.nominal_hand_pose('right')[0]+[-.08,0,.07],self.nominal_hand_pose('right')[1])},seconds=12)
 def finish_sg3_edge(self):
  delta=np.array([self.tuning.get('sg3_setdown_x',.363),0,.866])-self.d.xpos[self.obj]
  self.move('place',{'right':(self.nominal_hand_pose('right')[0]+delta,self.nominal_hand_pose('right')[1])},seconds=25)
  if self.tuning.get('sg3_force_release',False):self.release_sg3_on_table()
  else:
   self.pressure_control=False
   self.move('release',target=self.preshape(close=0),seconds=8)
  self.withdraw_sg3()
  return self.finish_sg3_push()
 def finish_sg3_push(self):
  self.move('slide_goal',target=self.preshape(close=1),seconds=8)
  disk=self.d.xpos[self.obj].copy();R=self.nominal_hand_pose('right')[1];push_position=disk+[-.14,0,.002]
  if self.tuning.get('sg3_pad_clearance_push',False):
   pad_geoms=[g for g in range(self.m.ngeom) if self.m.body(int(self.m.geom_bodyid[g])).name.startswith('rubber_tip_') and self.m.geom_contype[g]]
   lowest=min(self.d.geom_xpos[g,2]-(np.abs(self.d.geom_xmat[g].reshape(3,3))@self.m.geom_size[g])[2] for g in pad_geoms)
   push_position[2]=.861-(lowest-self.hand_pose('right')[0][2])+.008
  self.move('slide_goal',{'right':(push_position,R)},seconds=15)
  self.phase='slide_goal';self.events.append({'phase':'slide_goal','start_s':float(self.d.time),'record_start':len(self.records)})
  pos=self.nominal_hand_pose('right')[0].copy()
  for i in range(5500):
   if self.d.xpos[self.obj][0]>=.49:break
   pos[0]+=.002*.02
   solution,_=self.solve({'right':(pos,R)},seed=self.qref)
   for n,j in self.joints.items():
    if any(k in n for k in ['wrist','joint_arm','joint_lift']):self.qref[self.m.jnt_qposadr[j]]=solution[self.m.jnt_qposadr[j]]
   self.step()
  self.events[-1].update(end_s=float(self.d.time),record_end=len(self.records))
  self.move('release',{'right':(self.nominal_hand_pose('right')[0]+[-.06,0,.06],R)},seconds=12)
  self.move('release',seconds=3)
  if not self.success:raise RuntimeError('terminal_goal_not_established')
 def rotate_grasp(self,phase,axis,angle,pivot,seconds):
  self.phase=phase;self.events.append({'phase':phase,'start_s':float(self.d.time),'record_start':len(self.records)})
  poses={'right':self.nominal_hand_pose('right')};steps=round(seconds/.02)
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
  summary={'setting':self.args.setting,'task_success':bool(self.success and not error),'status':'full_witness_candidate' if self.success and not error else 'failed_attempt','failure':error,'simulated_seconds':float(self.d.time),'wall_seconds':time.monotonic()-self.start,'physics_hz':round(1/self.dt),'trace_hz':50,'video_fps':10,'physics_records':len(self.records),'video_frames':self.frames,'peaks':self.peaks,'seen_lift':self.seen_lift,'seen_flip':self.seen_flip,'independent_verification':'pending','binding':self.binding,'policy_state_writes':0,'object_attachment':False,'source_hashes':{n:hashlib.sha256((self.out/n).read_bytes()).hexdigest() for n in ['run.py','model.py','wrench.py','reference_interface.py','plan.json','scene.xml']},'limitations':['Privileged development expert; no public-agent score','MuJoCo extension protocol; original Genesis evidence is separate','No comparison success inferred from a failed or single-body attempt']}
  write(self.out/'summary.json',summary);print(json.dumps(summary),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--tuning',type=Path);p.add_argument('--setting',choices=list(PROFILES),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();attempt=Attempt(a);error=None
 try:attempt.execute()
 except Exception as e:error=str(e);(a.output/'error.txt').write_text(traceback.format_exc())
 finally:attempt.finish(error)
 return 0 if attempt.success and not error else 1
if __name__=='__main__':raise SystemExit(main())
