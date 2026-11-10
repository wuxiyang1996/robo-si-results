"""Pinned Stretch 4 SE4/francis/SG4 binding for measured Genesis probes.

The wheel meshes retain URDF contact geometry in revision 1. This does NOT
implement the official MuJoCo anisotropic omniwheel contact model. Mobility is
an empirical gate, never inferred from successful import or wheel rotation.
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

CACHE=Path('/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027')
SOURCE=CACHE/'asset-generated/stretch4/SE4_francis_sg4.urdf'
SOURCE_SHA='e3a2668fb2138d895146789feb7a5e2fcae4c5e768cb107516c2c4d03dba5b65'
URDF_COMMIT='3ce2c9511d3857447cd7df2bb25f48cf8afa196e'
MJCF_COMMIT='0b20cf4fb5faf514ac40581582f9b64aa8f96e50'
WHEELS=['wheel_0_joint','wheel_1_joint','wheel_2_joint']
ARMS=['arm_l1_joint','arm_l2_joint','arm_l3_joint','arm_l4_joint']
FINGERS=['gripper_finger_left_joint','gripper_finger_right_joint']
POSITION=['lift_joint','arm_l1_joint','wrist_yaw_joint','wrist_pitch_joint','wrist_roll_joint',*FINGERS]
# Limits are frozen before stepping. Uncalibrated values are explicitly marked.
PARAMS={
 'lift_joint':dict(kp=8000.,kv=200.,force=200.,velocity=.2,range=[0.,1.2],source='official stretch4_mujoco defaults lift_stretch4; probe speed capped at .2 m/s'),
 'arm_l1_joint':dict(kp=40000.,kv=1920.,force=700.,velocity=.05,range=[0.,.13],source='single master with 3 mimic followers; virtual-work mapping from official tendon: F_master=4*175 N, kp_master=16*2500, kv_master=16*120'),
 'wrist_yaw_joint':dict(kp=400.,kv=4.3,force=20.,velocity=.5,range=[-1.135,4.276],source='URDF effort 20 Nm; MJCF gains'),
 'wrist_pitch_joint':dict(kp=400.,kv=3.5,force=20.,velocity=.5,range=[-1.135,4.276],source='URDF effort 20 Nm; MJCF gains'),
 'wrist_roll_joint':dict(kp=250.,kv=1.2,force=20.,velocity=.5,range=[-4.276,1.135],source='URDF effort 20 Nm; MJCF gains'),
 **{n:dict(kp=500.,kv=20.,force=20.,velocity=.5,range=[0.,.5],source='URDF effort 20 Nm (below MJCF 30 Nm); MJCF gains; separate drives as upstream') for n in FINGERS},
 **{n:dict(kp=0.,kv=4.,force=8.,velocity=6.,range=None,source='author-declared conservative probe bound, NOT a verified hardware torque; raw URDF wheel joint has no limit') for n in WHEELS}}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(out, wheel_model='raw'):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Stretch 4 source hash changed')
 root=ET.parse(SOURCE).getroot();joints={j.get('name'):j for j in root.findall('joint')}
 for name in ARMS[1:]:ET.SubElement(joints[name],'mimic',joint=ARMS[0],multiplier='1',offset='0')
 changes=['Add three telescope mimic equalities matching the official MuJoCo equality chain']
 if wheel_model=='rollers':
  import math
  import numpy as np
  # Explicit passive rolling contacts; no base force, pose or velocity injection.
  # Preserve each wheel's total mass, COM and inertia at the zero configuration.
  links={l.get('name'):l for l in root.findall('link')}
  for wheel in range(3):
   name=f'wheel_{wheel}_link';link=links[name];inert=link.find('inertial');mass=float(inert.find('mass').get('value'))
   com=np.fromstring(inert.find('origin').get('xyz'),sep=' ');I=inert.find('inertia')
   tensor=np.array([[float(I.get('i'+a+b if a<=b else 'i'+b+a)) for b in 'xyz'] for a in 'xyz'])
   def shift(c):return (c@c)*np.eye(3)-np.outer(c,c)
   nr=16;rm=.02;rr=.012;radius=.060;hubmass=mass-nr*rm;hubcom=mass*com/hubmass
   total=tensor+mass*shift(com);rollerI=2/5*rm*rr**2*np.eye(3)
   for k in range(nr):
    theta=2*math.pi*k/nr;pos=np.array([radius*math.cos(theta),radius*math.sin(theta),0.]);total-=rollerI+rm*shift(pos)
    child=f'wheel_{wheel}_roller_{k}';l=ET.SubElement(root,'link',name=child)
    ii=ET.SubElement(l,'inertial');ET.SubElement(ii,'mass',value=str(rm));ET.SubElement(ii,'inertia',ixx=str(rollerI[0,0]),iyy=str(rollerI[1,1]),izz=str(rollerI[2,2]),ixy='0',ixz='0',iyz='0')
    for typ in ['collision']:
     g=ET.SubElement(ET.SubElement(l,typ),'geometry');ET.SubElement(g,'sphere',radius=str(rr))
    j=ET.SubElement(root,'joint',name=child+'_joint',type='continuous');ET.SubElement(j,'parent',link=name);ET.SubElement(j,'child',link=child)
    ET.SubElement(j,'origin',xyz=' '.join(map(str,pos)),rpy='0 0 0');ET.SubElement(j,'axis',xyz=f'{-math.sin(theta)} {math.cos(theta)} 0');ET.SubElement(j,'dynamics',damping='0.0001',friction='0.00001')
   hubI=total-hubmass*shift(hubcom)
   if np.linalg.eigvalsh(hubI).min()<=0:raise ValueError('invalid derived wheel inertia')
   inert.find('mass').set('value',str(hubmass));inert.find('origin').set('xyz',' '.join(map(str,hubcom)))
   for ai,a in enumerate('xyz'):
    for bi,b in enumerate('xyz'):
     if ai<=bi:I.set('i'+a+b,str(hubI[ai,bi]))
   for col in list(link.findall('collision')):link.remove(col)
   geom=ET.SubElement(ET.SubElement(link,'collision'),'geometry');ET.SubElement(geom,'cylinder',radius='.054',length='.018')
  changes.append('Replace three rigid wheel collision meshes with radius .054 m hubs and 16 passive spherical rollers per wheel (roller radius .012 m, center radius .060 m, mass .02 kg); preserve aggregate wheel mass, COM and rest inertia. Original visuals retained. This is an explicit approximate contact model, not hardware validation.')
 elif wheel_model!='raw':raise ValueError('wheel_model')
 dest=out/'stretch4_telescope_coupled.urdf';ET.ElementTree(root).write(dest,encoding='utf-8',xml_declaration=True)
 receipt=dict(schema='h3-stretch4-binding/1',source_sha256=SOURCE_SHA,urdf_commit=URDF_COMMIT,mjcf_commit=MJCF_COMMIT,derived_sha256=sha(dest),
  changes=changes,wheel_model=wheel_model,
  actuators=PARAMS,root_fixed=False,gravity_compensation=False,hardware_calibrated=False,
  limitations=['Wheel contact model must be measured; explicit rollers are an approximation, not the official MuJoCo anisotropic contact model','Wheel torque bound is an author probe bound','Genesis neutral-pose contact filtering must be audited'],
  meshes={m.get('filename'):sha(m.get('filename')) for m in root.findall('.//mesh')})
 (out/'binding.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return dest,receipt
