"""Online Dex3 support transfer and index pushing after a declared nominal prefix.

All motion is issued as robot joint references. The simulator and scorer retain
ownership of the object, contact dynamics, limits and episode state.
"""
import numpy as np
from scipy.spatial.transform import Rotation
def smooth(x):return x**3*(10-15*x+6*x*x)


def segment(a,phase,seconds,callback):
 a.phase=phase;a.events.append(dict(phase=phase,start_s=float(a.d.time),record_start=len(a.records)))
 count=round(seconds/.02)
 for i in range(count):callback(i,count)
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))


def finish_from_prefix(a):
 if a.args.setting!='DF-04-G':raise ValueError('No validated prefix completion is implemented for this setting yet')
 a.tuning.update(bridge_allow_reverse_right_elbow=True,plan_world_contacts=True,incremental_ik_tolerance=1e-5)
 a.incremental_motion=True;a.pressure_control=False;a.handoff_progress=1.
 left=a.nominal_hand_pose('left')
 def servo(goal,yaw_delta=0.):
  centre=a.d.xpos[a.obj].copy();normal=a.d.xmat[a.obj].reshape(3,3)[:,2];omega=.8*np.cross(normal,[0.,0.,-1.]);norm=np.linalg.norm(omega)
  if norm>.08:omega*=.08/norm
  rot=Rotation.from_rotvec(.02*omega).as_matrix()@Rotation.from_euler('z',yaw_delta).as_matrix();p,R=a.nominal_hand_pose('right');translation=.02*np.clip(.6*(goal-centre),-.005,.005)
  a.apply_goals({'right':(centre+translation+rot@(p-centre),rot@R),'left':(left[0],None)})
 centre=a.d.xpos[a.obj].copy();segment(a,'place',40,lambda i,n:servo(centre,-np.pi/3*(smooth((i+1)/n)-smooth(i/n))))
 target=a.qref.copy()
 for side,sign,fingers in [('left',-1,['index','middle']),('right',1,['index'])]:
  for finger in fingers:
   for j in [0,1]:a.joint_set(target,f'{side}_hand_{finger}_{j}_joint',sign*1.5)
 a.move('place',target=target,seconds=6)
 centre=a.d.xpos[a.obj].copy();goal=np.array([.29,0,.8656]);segment(a,'place',55,lambda i,n:servo(centre+smooth((i+1)/n)*(goal-centre)));segment(a,'place',8,lambda i,n:servo(goal))
 return push_from_shared_support(a)


def push_from_shared_support(a):
 """Approach with a frontmost index surface, transfer load, then release."""
 a.freeze_right_arm=True;a.pressure_control=False;a.active_tool='index_bridge_prepare'
 a.tuning.update(plan_world_contacts=True,bridge_allow_cross_shoulder=True,bridge_allow_reverse_right_elbow=True,wrist_clearance=False,incremental_ik_tolerance=1e-5)
 a.incremental_motion=True
 a.move('place',{'left':(np.array([.25,.20,1.10]),None)},seconds=10)
 target=a.qref.copy()
 for finger,values in [('index',[0,0]),('middle',[-1.5,-1.5]),('thumb',[-1.0472,-.610865,1.16355])]:
  for j,value in enumerate(values):a.joint_set(target,f'left_hand_{finger}_{j}_joint',value)
 a.move('place',target=target,seconds=6)
 a.active_tool='left_index_dex3';a.tool_rotation_wrist=True;a.freeze_right_arm=False
 R=Rotation.from_euler('xyz',[120,75,30],degrees=True).as_matrix();disk=a.d.xpos[a.obj].copy();held=a.nominal_hand_pose('right')
 a.tuning['plan_avoid_left_object']=True
 for g in range(a.ikm.ngeom):
  if a.ikm.body(int(a.ikm.geom_bodyid[g])).name.startswith('left_') and a.ikm.geom_contype[g]:a.ikm.geom_margin[g]=.003
 a.move('slide_goal',{'left':(disk+[-.105,0,.035],R),'right':held},seconds=20)
 a.move('slide_goal',{'left':(disk+[-.105,0,.003],R),'right':held},seconds=12)
 a.tuning['plan_avoid_left_object']=False
 tip,_=a.nominal_hand_pose('left');rightp,rightR=a.nominal_hand_pose('right');anchor=rightp.copy()
 thumb_angle=sum(a.d.qpos[a.m.jnt_qposadr[a.joints['right_hand_'+part+'_joint']]] for part in ['thumb_1','thumb_2']);released=False
 a.phase='slide_goal';a.events.append(dict(phase=a.phase,start_s=float(a.d.time),record_start=len(a.records)))
 for _ in range(5000):
  disk=a.d.xpos[a.obj].copy();robot,table,local,rt,selfc,contacts=a.contacts()
  left_force=sum((np.array(c['force_on_disk_world']) for c in contacts if c['body'].startswith('left_hand_')),start=np.zeros(3));right_load=sum(c['force_n'] for c in contacts if c['body'].startswith('right_hand_'))
  if disk[0]>.36 and table>.6:released=True
  tip[0]+=.02*np.clip(.004*(2.4-left_force[0]),-.003,.006)
  tip[0]=min(tip[0],disk[0]-np.sqrt(max(.0025,.1**2-(tip[1]-disk[1])**2))+.008)
  tip[1]+=.02*np.clip(.12*(-disk[1]) if released and right_load<.05 else 1.5*(disk[1]-tip[1]),-.004,.004)
  tip[2]+=.02*np.clip(1.5*(disk[2]+.003-tip[2]),-.002,.002)
  if local>2.8 and a.profile=='P3':tip[0]-=.004*.02
  if released:
   for part,want in [('thumb_1',.35),('thumb_2',0.)]:
    name='right_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,a.qref[qi]+.02*np.clip(.8*(want-a.d.qpos[qi]),-.08,.08))
   rightp[0]=max(anchor[0]-.08,rightp[0]-.003*.02);rightp[2]=max(anchor[2]-.025,rightp[2]-.001*.02)
  else:
   pressure=sum(max(0.,-c['force_on_disk_world'][2]) for c in contacts if c['body'].startswith('right_hand_thumb_'))
   qi=a.m.jnt_qposadr[a.joints['right_hand_thumb_1_joint']];qi2=a.m.jnt_qposadr[a.joints['right_hand_thumb_2_joint']]
   a.joint_set(a.qref,'right_hand_thumb_1_joint',a.qref[qi]-.02*np.clip(.024*(.9-pressure),-.04,.04))
   a.joint_set(a.qref,'right_hand_thumb_2_joint',a.qref[qi2]+.02*np.clip(.8*(thumb_angle-a.d.qpos[qi]-a.d.qpos[qi2]),-.04,.04))
  a.apply_goals({'left':(tip,R),'right':(rightp,rightR)})
  if disk[0]>=.49 and right_load<.05:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 a.move('release',{'left':(tip+[-.025,0,0],R)},seconds=5)
 a.move('release',{'left':(tip+[-.025,0,.10],R)},seconds=5)
 a.move('release',seconds=3)
 if not a.success:raise RuntimeError('terminal_goal_not_established')
