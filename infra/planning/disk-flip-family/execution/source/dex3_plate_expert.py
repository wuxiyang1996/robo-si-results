"""Nominal P2 prefix followed by measured support transfer and rim pushing.

Only robot joint references are changed. Object state belongs to the simulator.
"""
import types
import numpy as np
from scipy.spatial.transform import Rotation

def smooth(x):return x**3*(10-15*x+6*x*x)

def segment(a,phase,seconds,callback):
 a.phase=phase;a.events.append(dict(phase=phase,start_s=float(a.d.time),record_start=len(a.records)))
 count=round(seconds/.02)
 for i in range(count):callback(i,count)
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))

def finish_from_prefix(a):
 if a.args.setting=='DF-03-G':return finish_p3_from_prefix(a)
 if a.args.setting!='DF-02-G':raise ValueError('This nominal expert is only configured for DF-02-G and DF-03-G')
 a.pressure_control=False;a.phase='place';a.events.append(dict(phase='place',start_s=float(a.d.time),record_start=len(a.records)));stable=0.
 for i in range(2500):
  if i>=250:
   for part,want in [('thumb_1',.3),('thumb_2',0.),('index_0',-.02),('index_1',-.02),('middle_0',-.02),('middle_1',-.02)]:
    name='left_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,a.qref[qi]+.02*np.clip(.3*(want-a.qref[qi]),-.015,.015))
  a.step();load=sum(c['force_n'] for c in a.contacts()[-1] if c['body'].startswith('left_hand_'));stable=stable+.02 if load<.05 else 0.
  if stable>=2:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 if stable<2:raise RuntimeError('left_hand_not_released')
 a.handoff_progress=1.;a.tuning.update(bridge_allow_reverse_right_elbow=True,bridge_transport_feedback=False)
 left=a.nominal_hand_pose('left')
 def servo(goal,yaw_delta=0):
  centre=a.d.xpos[a.obj].copy();normal=a.d.xmat[a.obj].reshape(3,3)[:,2];omega=np.clip(.8*np.cross(normal,[0.,0.,-1.]),-.06,.06);rot=Rotation.from_rotvec(.02*omega).as_matrix()@Rotation.from_euler('z',yaw_delta).as_matrix();p,R=a.nominal_hand_pose('right');translation=.02*np.clip(.6*(goal-centre),-.004,.004)
  a.apply_goals({'right':(centre+translation+rot@(p-centre),rot@R),'left':left})
 a.freeze_right_arm=True;a.move('place',{'right':a.nominal_hand_pose('right'),'left':(left[0]+[0,.14,0],None)},seconds=16);a.freeze_right_arm=False;left=a.nominal_hand_pose('left');centre=a.d.xpos[a.obj].copy()
 segment(a,'place',15,lambda i,n:servo(centre));centre=a.d.xpos[a.obj].copy();segment(a,'place',40,lambda i,n:servo(centre,-np.pi/3*(smooth((i+1)/n)-smooth(i/n))))
 target=a.qref.copy();a.joint_set(target,'right_hand_index_0_joint',1.1);a.joint_set(target,'right_hand_index_1_joint',.5);a.move('place',target=target,seconds=10)
 centre=a.d.xpos[a.obj].copy();goal=np.array([.29,0,.89]);segment(a,'place',30,lambda i,n:servo(centre+smooth((i+1)/n)*(goal-centre)))
 goal=np.array([.29,0,.866]);stable=0.;a.phase='place';a.events.append(dict(phase='place',start_s=float(a.d.time),record_start=len(a.records)))
 for _ in range(1250):
  servo(goal);stable=stable+.02 if a.contacts()[1]>.15 and a.d.xmat[a.obj].reshape(3,3)[2,2]<-.99 else 0.
  if stable>=.5:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 p,R=a.nominal_hand_pose('right');p=p.copy();stable=0.;touch=False;a.phase='place';a.events.append(dict(phase='place',start_s=float(a.d.time),record_start=len(a.records)))
 for _ in range(2000):
  if a.contacts()[1]>.10:touch=True
  if not touch:p[2]-=.001*.02
  a.apply_goals({'right':(p,R)});stable=stable+.02 if touch and a.contacts()[1]>.05 else 0.
  if stable>=.5:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 if stable<.5:raise RuntimeError('edge_table_support_not_established')
 return index_tail(a)

def index_tail(a):
 a.freeze_right_arm=True;a.pressure_control=False;a.active_tool='index_push';a.tuning.update(plan_world_contacts=True,bridge_allow_reverse_elbow=True,bridge_allow_cross_shoulder=True,incremental_ik_tolerance=1e-5,ik_right_hand_weight=10.,bridge_allow_reverse_right_elbow=True,wrist_clearance=False);a.incremental_motion=True
 row={'body_offset':[.04809672682411692,.005287920635738453,.003970664934028173],'euler':[120,75,30]};offset=np.array(row['body_offset']);R=Rotation.from_euler('xyz',row['euler'],degrees=True).as_matrix();w=a.m.body('left_wrist_yaw_link').id;b=a.m.body('left_hand_index_1_link').id
 p0,R0=a.nominal_hand_pose('left');a.move('place',{'left':(np.array([.31,.20,1.10]),None)},seconds=10)
 target=a.qref.copy()
 for f,values in [('index',[0,0]),('middle',[-1.5,-1.5]),('thumb',[-1.0472,-.610865,1.16355])]:
  for j,v in enumerate(values):a.joint_set(target,f'left_hand_{f}_{j}_joint',v)
 a.move('place',target=target,seconds=6)
 original=a.hand_pose
 def pose(self,side,data=None):
  if side!='left':return original(side,data)
  d=data or self.d;return d.xpos[b]+d.xmat[b].reshape(3,3)@offset,d.xmat[w].reshape(3,3)
 a.hand_pose=types.MethodType(pose,a);a.hand_defs=lambda:{'left':(b,offset),'right':(a.m.body('right_wrist_yaw_link').id,np.array([.08382,-.00406,0]))}
 a.freeze_right_arm=False;disk=a.d.xpos[a.obj].copy();above=disk+[-.105,0,.035];held=a.nominal_hand_pose('right');a.tuning['plan_avoid_left_object']=True
 for g in range(a.ikm.ngeom):
  if a.ikm.body(int(a.ikm.geom_bodyid[g])).name.startswith('left_') and a.ikm.geom_contype[g]:a.ikm.geom_margin[g]=.003
 a.move('slide_goal',{'left':(above,R),'right':held},seconds=20);a.move('slide_goal',{'left':(disk+[-.105,0,(.003+.1*a.d.xmat[a.obj].reshape(3,3)[0,2])/a.d.xmat[a.obj].reshape(3,3)[2,2]],R),'right':held},seconds=12);a.tuning['plan_avoid_left_object']=False
 tip,_=a.nominal_hand_pose('left');rightp,rightR=a.nominal_hand_pose('right');anchor=rightp.copy();thumb_angle=sum(a.d.qpos[a.m.jnt_qposadr[a.joints['right_hand_'+part+'_joint']]] for part in ['thumb_1','thumb_2']);released=False
 a.phase='slide_goal';a.events.append(dict(phase=a.phase,start_s=float(a.d.time),record_start=len(a.records)))
 for i in range(5000):
  disk=a.d.xpos[a.obj].copy();robot,table,local,rt,selfc,cs=a.contacts();lf=sum((np.array(c['force_on_disk_world']) for c in cs if c['body'].startswith('left_hand_')),start=np.zeros(3));rl=sum(c['force_n'] for c in cs if c['body'].startswith('right_hand_'))
  if disk[0]>.36 and table>.6:released=True
  tip[0]+=.02*np.clip(.004*(2.4-lf[0]),-.003,.006);tip[0]=min(tip[0],disk[0]-np.sqrt(max(.0025,.1**2-(tip[1]-disk[1])**2))+.008)
  tip[1]+=.02*np.clip((.25*(-disk[1]) if released and rl<.05 else 1.5*(disk[1]-tip[1])),-.004,.004);normal=a.d.xmat[a.obj].reshape(3,3)[:,2];rim_z=disk[2]+(.003-normal[0]*(tip[0]-disk[0])-normal[1]*(tip[1]-disk[1]))/normal[2];tip[2]+=.02*np.clip(1.5*(rim_z-tip[2]),-.004,.004)
  if local>2.8 and a.profile=='P3':tip[0]-=.004*.02
  if released:
   for part,want in [('thumb_1',.35),('thumb_2',0.)]:
    n='right_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[n]];a.joint_set(a.qref,n,a.qref[qi]+.02*np.clip(.8*(want-a.d.qpos[qi]),-.08,.08))
   a.freeze_right_arm=False;rightp[0]=max(anchor[0]-.08,rightp[0]-.003*.02);rightp[2]=max(anchor[2]-.025,rightp[2]-.001*.02)
  else:
   rightp[0]=anchor[0]+min(.03,max(0.,disk[0]-.31)*.6)
   pressure=sum(max(0.,-c['force_on_disk_world'][2]) for c in cs if c['body'].startswith('right_hand_thumb_'));qi=a.m.jnt_qposadr[a.joints['right_hand_thumb_1_joint']];qi2=a.m.jnt_qposadr[a.joints['right_hand_thumb_2_joint']];a.joint_set(a.qref,'right_hand_thumb_1_joint',a.qref[qi]-.02*np.clip(.024*(.9-pressure),-.04,.04));a.joint_set(a.qref,'right_hand_thumb_2_joint',a.qref[qi2]+.02*np.clip(.8*(thumb_angle-a.d.qpos[qi]-a.d.qpos[qi2]),-.04,.04))
  for part in ['index_0','index_1']:
   name='left_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,np.clip(a.qref[qi]-.02*2.*a.d.qpos[qi],-.3,.3))
  R=Rotation.from_euler('xyz',[120,75-15*smooth(np.clip((disk[0]-.37)/.06,0,1)),30],degrees=True).as_matrix();a.apply_goals({'left':(tip,R),'right':(rightp,rightR)})
  if disk[0]>=.39 and rl<.05:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 push_into_goal(a)

def push_into_goal(a):
 a.freeze_right_arm=False;a.freeze_right_wrist=True;held=a.nominal_hand_pose('right')
 a.tuning.update(bridge_allow_reverse_left_elbow=False,bridge_allow_reverse_right_elbow=True,bridge_allow_cross_shoulder=True,wrist_clearance=False)
 b=a.m.body('left_hand_index_1_link').id;w=a.m.body('left_wrist_yaw_link').id;offset=np.array([.05123901347380861,.004372218838549904,.004683740261029003]);original=a.hand_pose

 def pose(self,side,data=None):
  if side!='left':return original(side,data)
  d=data or self.d;return d.xpos[b]+d.xmat[b].reshape(3,3)@offset,d.xmat[w].reshape(3,3)
 a.hand_pose=types.MethodType(pose,a);a.hand_defs=lambda:{'right':held,'left':(b,offset),'right':(a.m.body('right_wrist_yaw_link').id,np.array([.08382,-.00406,0]))}
 disk=a.d.xpos[a.obj].copy();direction=np.array([1.,0.,0.]);phi=np.arctan2(direction[1],direction[0]);R=Rotation.from_euler('z',phi).as_matrix()@Rotation.from_euler('xyz',[120,60,30],degrees=True).as_matrix();tip,R0=a.nominal_hand_pose('left')
 a.move('slide_goal',{'right':held,'left':(tip+[-.03,0,0],R0)},seconds=4)
 a.move('slide_goal',{'right':held,'left':(tip+[-.03,0,.02],R0)},seconds=3)
 behind=disk-.11*direction;behind[2]=.88;a.move('slide_goal',{'right':held,'left':(behind,R)},seconds=8);behind[2]=.8635;a.move('slide_goal',{'right':held,'left':(behind,R)},seconds=5)
 tip,_=a.nominal_hand_pose('left');a.phase='slide_goal';a.events.append(dict(phase='slide_goal',start_s=float(a.d.time),record_start=len(a.records)))
 for i in range(1500):
  disk=a.d.xpos[a.obj].copy();force=sum((np.array(c['force_on_disk_world']) for c in a.contacts()[-1] if c['body'].startswith('left_hand_')),start=np.zeros(3));tip+=.02*np.clip(.004*(2.-force@direction),-.003,.006)*direction;tip[1]+=.02*np.clip(1.5*(disk[1]-tip[1]),-.004,.004);tip[2]+=.02*np.clip(1.5*(.8635-tip[2]),-.003,.003);a.apply_goals({'right':held,'left':(tip,R)})
  if disk[0]>=.49 and np.linalg.norm(disk[:2]-[.50,0])<.044:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records));a.move('release',{'right':held,'left':(tip-.025*direction,R)},seconds=4);a.move('release',{'right':held,'left':(tip-.025*direction+[0,0,.06],R)},seconds=4);a.move('release',seconds=2.5)
 if not a.success:raise RuntimeError('terminal_goal_not_established')

def finish_p3_from_prefix(a):
 a.pressure_control=False;a.phase='place';a.events.append(dict(phase='place',start_s=float(a.d.time),record_start=len(a.records)));stable=0.;initial=a.qref.copy()
 for i in range(2500):
  if i<250:
   for part,delta in [('thumb_1',-.02),('middle_0',.12)]:
    name='right_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,initial[qi]+smooth((i+1)/250)*delta)
  if i>=250:
   for part,want in [('thumb_1',.3),('thumb_2',0.),('index_0',-.02),('index_1',-.02),('middle_0',-.02),('middle_1',-.02)]:
    name='left_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,a.qref[qi]+.02*np.clip(.3*(want-a.qref[qi]),-.015,.015))
  if i>500:
   a.incremental_motion=True;a.tuning['incremental_ik_tolerance']=1e-5;normal=a.d.xmat[a.obj].reshape(3,3)[:,2];centre=a.d.xpos[a.obj].copy();rot=Rotation.from_rotvec(.02*np.clip(.7*np.cross(normal,[0.,0.,-1.]),-.06,.06)).as_matrix();p,R=a.nominal_hand_pose('right');a.apply_goals({'right':(centre+rot@(p-centre),rot@R),'left':a.nominal_hand_pose('left')})
  else:a.step()
  load=sum(c['force_n'] for c in a.contacts()[-1] if c['body'].startswith('left_hand_'));stable=stable+.02 if load<.05 else 0.
  if stable>=35:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 if stable<35:raise RuntimeError('left_hand_not_released')
 return finish_p3_after_handoff(a)

def finish_p3_after_handoff(a):
 a.handoff_progress=1.;a.tuning.update(bridge_allow_reverse_right_elbow=True,bridge_transport_feedback=False,incremental_ik_tolerance=1e-5);a.incremental_motion=True;left=a.nominal_hand_pose('left')
 def servo(goal,yaw_delta=0):
  centre=a.d.xpos[a.obj].copy();normal=a.d.xmat[a.obj].reshape(3,3)[:,2];rot=Rotation.from_rotvec(.02*np.clip(.8*np.cross(normal,[0.,0.,-1.]),-.06,.06)).as_matrix()@Rotation.from_euler('z',yaw_delta).as_matrix();p,R=a.nominal_hand_pose('right');translation=.02*np.clip(.6*(goal-centre),-.004,.004);a.apply_goals({'right':(centre+translation+rot@(p-centre),rot@R),'left':left})
 left0=left;centre=a.d.xpos[a.obj].copy()
 def clear_left(i,n):
  nonlocal left
  left=(left0[0]+smooth((i+1)/n)*np.array([0,.14,0]),None);servo(centre)
 segment(a,'place',16,clear_left);left=a.nominal_hand_pose('left');centre=a.d.xpos[a.obj].copy();segment(a,'place',15,lambda i,n:servo(centre));centre=a.d.xpos[a.obj].copy();segment(a,'place',40,lambda i,n:servo(centre,-np.pi/3*(smooth((i+1)/n)-smooth(i/n))))
 target=a.qref.copy();a.joint_set(target,'right_hand_index_0_joint',1.1);a.joint_set(target,'right_hand_index_1_joint',.5);a.move('place',target=target,seconds=10)
 centre=a.d.xpos[a.obj].copy();goal=np.array([.29,0,.89]);segment(a,'place',30,lambda i,n:servo(centre+smooth((i+1)/n)*(goal-centre)));segment(a,'place',1,lambda i,n:servo(np.array([.29,0,.866])))
 a.tuning['plan_world_contacts']=True;target=a.qref.copy()
 for side,sign,fingers in [('left',-1,['index','middle']),('right',1,['index'])]:
  for finger in fingers:
   for j in [0,1]:a.joint_set(target,f'{side}_hand_{finger}_{j}_joint',sign*1.5)
 a.move('place',target=target,seconds=6);goal=np.array([.29,0,.8656]);stable=0.;a.phase='place';a.events.append(dict(phase='place',start_s=float(a.d.time),record_start=len(a.records)))
 for i in range(2000):
  centre=a.d.xpos[a.obj].copy();normal=a.d.xmat[a.obj].reshape(3,3)[:,2];rot=Rotation.from_rotvec(.02*np.clip(.8*np.cross(normal,[0.,0.,-1.]),-.06,.06)).as_matrix();p,R=a.nominal_hand_pose('right');delta=.02*np.clip(.6*(goal-centre),-.003,.003);a.apply_goals({'right':(centre+delta+rot@(p-centre),rot@R)})
  stable=stable+.02 if a.contacts()[1]>.15 and normal[2]<-.99 else 0.
  if stable>=.5:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 if stable<.5:raise RuntimeError('table_support_not_established')
 return index_tail_p3(a)

def index_tail_p3(a):
 a.freeze_right_arm=True;a.pressure_control=False;a.active_tool='index_push';a.incremental_motion=True;a.tuning.update(plan_world_contacts=True,bridge_allow_reverse_elbow=True,bridge_allow_cross_shoulder=True,incremental_ik_tolerance=1e-5,ik_right_hand_weight=10.,bridge_allow_reverse_right_elbow=True,wrist_clearance=False)
 row={'body_offset':[.049578207575203176,.0047371800065187375,-.007176292355786335],'euler':[30,60,-60]};offset=np.array(row['body_offset']);R=Rotation.from_euler('xyz',row['euler'],degrees=True).as_matrix();w=a.m.body('left_wrist_yaw_link').id;b=a.m.body('left_hand_index_1_link').id
 original_step=a.step;thumb_angle=sum(a.d.qpos[a.m.jnt_qposadr[a.joints['right_hand_'+part+'_joint']]] for part in ['thumb_1','thumb_2'])
 def supported_step():
  pressure=sum(max(0.,-c['force_on_disk_world'][2]) for c in a.contacts()[-1] if c['body'].startswith('right_hand_thumb_'));qi=a.m.jnt_qposadr[a.joints['right_hand_thumb_1_joint']];qi2=a.m.jnt_qposadr[a.joints['right_hand_thumb_2_joint']]
  a.joint_set(a.qref,'right_hand_thumb_1_joint',a.qref[qi]-.02*np.clip(.024*(.9-pressure),-.04,.04));a.joint_set(a.qref,'right_hand_thumb_2_joint',a.qref[qi2]+.02*np.clip(.8*(thumb_angle-a.d.qpos[qi]-a.d.qpos[qi2]),-.04,.04));original_step()
 a.step=supported_step
 p0,R0=a.nominal_hand_pose('left');a.move('place',{'left':(np.array([.25,.20,1.10]),None)},seconds=10)
 target=a.qref.copy()
 for f,values in [('index',[0,0]),('middle',[-1.5,-1.5]),('thumb',[-1.0472,-.610865,1.16355])]:
  for j,v in enumerate(values):a.joint_set(target,f'left_hand_{f}_{j}_joint',v)
 a.move('place',target=target,seconds=6)
 original=a.hand_pose
 def pose(self,side,data=None):
  if side!='left':return original(side,data)
  d=data or self.d;return d.xpos[b]+d.xmat[b].reshape(3,3)@offset,d.xmat[w].reshape(3,3)
 a.hand_pose=types.MethodType(pose,a);a.hand_defs=lambda:{'left':(b,offset),'right':(a.m.body('right_wrist_yaw_link').id,np.array([.08382,-.00406,0]))}
 a.freeze_right_arm=False;a.freeze_right_wrist=True;a.tuning['bridge_allow_reverse_left_elbow']=True;disk=a.d.xpos[a.obj].copy();above=disk+[-.105,0,.035];held=a.nominal_hand_pose('right');a.tuning['plan_avoid_left_object']=True
 for g in range(a.ikm.ngeom):
  if a.ikm.body(int(a.ikm.geom_bodyid[g])).name.startswith('left_') and a.ikm.geom_contype[g]:a.ikm.geom_margin[g]=.003
 a.move('slide_goal',{'left':(above,R),'right':held},seconds=20);a.move('slide_goal',{'left':(disk+[-.105,0,-.002],R),'right':held},seconds=12);a.tuning['plan_avoid_left_object']=False
 a.step=original_step;tip,_=a.nominal_hand_pose('left');rightp,rightR=a.nominal_hand_pose('right');anchor=rightp.copy();thumb_angle=sum(a.d.qpos[a.m.jnt_qposadr[a.joints['right_hand_'+part+'_joint']]] for part in ['thumb_1','thumb_2']);released=False
 a.phase='slide_goal';a.events.append(dict(phase=a.phase,start_s=float(a.d.time),record_start=len(a.records)))
 for i in range(5000):
  disk=a.d.xpos[a.obj].copy();robot,table,local,rt,selfc,cs=a.contacts();lf=sum((np.array(c['force_on_disk_world']) for c in cs if c['body'].startswith('left_hand_')),start=np.zeros(3));rl=sum(c['force_n'] for c in cs if c['body'].startswith('right_hand_'))
  if disk[0]>.36 and table>.6:released=True
  tip[0]+=.02*np.clip(.004*(2.4-lf[0]),-.003,.006);tip[0]=min(tip[0],disk[0]-np.sqrt(max(.0025,.1**2-(tip[1]-disk[1])**2))+.008)
  tip[1]+=.02*np.clip(1.5*(disk[1]-tip[1]),-.004,.004);tip[2]+=.02*np.clip(1.5*((.863 if released and rl<.05 else disk[2]+(.003-a.d.xmat[a.obj].reshape(3,3)[0,2]*(tip[0]-disk[0])-a.d.xmat[a.obj].reshape(3,3)[1,2]*(tip[1]-disk[1]))/a.d.xmat[a.obj].reshape(3,3)[2,2])-tip[2]),-.002,.002)
  if local>2.8 and a.profile=='P3':tip[0]-=.004*.02
  if released:
   for part,want in [('thumb_1',.35),('thumb_2',0.)]:
    n='right_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[n]];a.joint_set(a.qref,n,a.qref[qi]+.02*np.clip(.8*(want-a.d.qpos[qi]),-.08,.08))
   a.freeze_right_arm=False;rightp[0]=max(anchor[0]-.08,rightp[0]-.003*.02);rightp[2]=max(anchor[2]-.025,rightp[2]-.001*.02)
  else:
   pressure=sum(max(0.,-c['force_on_disk_world'][2]) for c in cs if c['body'].startswith('right_hand_thumb_'));qi=a.m.jnt_qposadr[a.joints['right_hand_thumb_1_joint']];qi2=a.m.jnt_qposadr[a.joints['right_hand_thumb_2_joint']];a.joint_set(a.qref,'right_hand_thumb_1_joint',a.qref[qi]-.02*np.clip(.024*(.9-pressure),-.04,.04));a.joint_set(a.qref,'right_hand_thumb_2_joint',a.qref[qi2]+.02*np.clip(.8*(thumb_angle-a.d.qpos[qi]-a.d.qpos[qi2]),-.04,.04))
  for part in ['index_0','index_1']:
   name='left_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,np.clip(a.qref[qi]-.02*2.*a.d.qpos[qi],-.3,.3))
  a.apply_goals({'left':(tip,R)} if released and rl<.05 else {'left':(tip,R),'right':(rightp,rightR)})
  if disk[0]>=.389 and rl<.05:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records))
 finish_rim(a,R)

def finish_rim(a,R):
 disk=a.d.xpos[a.obj].copy();tip,_=a.nominal_hand_pose('left');tip[0]=disk[0]-.108;a.move('slide_goal',{'left':(tip,R)},seconds=4)
 disk=a.d.xpos[a.obj].copy();normal=a.d.xmat[a.obj].reshape(3,3)[:,2];tip[0]=disk[0]-.108;tip[1]=disk[1];tip[2]=disk[2]+(.003+.1*normal[0])/normal[2];a.move('slide_goal',{'left':(tip,R)},seconds=4)
 tip,_=a.nominal_hand_pose('left');a.phase='slide_goal';a.events.append(dict(phase='slide_goal',start_s=float(a.d.time),record_start=len(a.records)))
 for i in range(2000):
  disk=a.d.xpos[a.obj].copy();robot,table,local,rt,selfc,cs=a.contacts();force=sum((np.array(c['force_on_disk_world']) for c in cs if c['body'].startswith('left_hand_')),start=np.zeros(3));normal=a.d.xmat[a.obj].reshape(3,3)[:,2]
  tip[0]+=.02*np.clip(.004*(2.4-force[0]),-.003,.006);tip[0]=min(tip[0],disk[0]-np.sqrt(max(.0025,.1**2-(tip[1]-disk[1])**2))+.008);tip[1]+=.02*np.clip(1.5*(disk[1]-tip[1]),-.004,.004);rim_z=disk[2]+(.003-normal[0]*(tip[0]-disk[0])-normal[1]*(tip[1]-disk[1]))/normal[2];tip[2]+=.02*np.clip(1.5*(rim_z-tip[2]),-.002,.002)
  if local>2.8:tip[0]-=.004*.02
  for part in ['index_0','index_1']:
   name='left_hand_'+part+'_joint';qi=a.m.jnt_qposadr[a.joints[name]];a.joint_set(a.qref,name,np.clip(a.qref[qi]-.02*2.*a.d.qpos[qi],-.3,.3))
  a.apply_goals({'left':(tip,R)})
  if disk[0]>=.49:break
 a.events[-1].update(end_s=float(a.d.time),record_end=len(a.records));a.move('release',{'left':(tip+[-.025,0,0],R)},seconds=5);a.move('release',{'left':(tip+[-.025,0,.10],R)},seconds=5);a.move('release',seconds=3)
 if not a.success:raise RuntimeError('terminal_goal_not_established')
