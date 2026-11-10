"""Build immutable scene assets; all bodies move only through physics at runtime.

E2 is an explicitly parameterized simulated gripper, not a claimed commercial
robot. E3 grafts the licensed Inspire hand subtrees onto the same G1 wrists.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation

from .contracts import ROOT, FAMILY, contract, config

G1 = ROOT/'humanoid/g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml'
INSPIRE = ROOT.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache/unitree_ros/robots/g1_description/g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf'


def fmt(v):return ' '.join(format(float(x),'.12g') for x in v)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def box(parent,name,size,pos=(0,0,0),mass=.01,color=(.6,.6,.6,1),**kw):
    return ET.SubElement(parent,'geom',name=name,type='box',size=fmt(np.asarray(size)/2),
                         pos=fmt(pos),mass=str(mass),rgba=fmt(color),friction='.7 .005 .0001',condim='4',**kw)


def replace_hand(root, side, embodiment, metadata):
    wrist=root.find(f'.//body[@name="{side}_wrist_yaw_link"]')
    assert wrist is not None
    old_joints={j.get('name') for b in wrist.findall('body') for j in b.iter('joint')}
    for child in list(wrist):
        if child.tag=='body' or (child.tag=='geom' and '_hand_' in child.get('mesh','')):
            wrist.remove(child)
    # Retain the authored wrist assembly inertia conservatively. Record this
    # adapter limitation rather than claiming a calibrated hardware mass model.
    metadata['wrist_inertia_policy']='original wrist assembly inertia retained; replacement hand mass added; hardware mass calibration pending'
    for section in ['actuator','contact','equality']:
        element=root.find(section)
        if element is not None:
            for child in list(element):
                if any(v in old_joints for v in child.attrib.values()):element.remove(child)
    if embodiment=='parallel':
        body=ET.SubElement(wrist,'body',name=f'{side}_parallel_palm',pos='.045 0 0')
        box(body,f'{side}_gripper_palm',(.06,.10,.06),(.03,0,0),.22,(.2,.3,.45,1))
        for sign in [-1,1]:
            finger=ET.SubElement(body,'body',name=f'{side}_parallel_finger_{sign}',pos=fmt((.06,sign*.012,0)))
            ET.SubElement(finger,'joint',name=f'{side}_parallel_slide_{sign}',type='slide',axis=fmt((0,sign,0)),range='0 .035',actuatorfrcrange='-25 25',damping='1',armature='.002')
            box(finger,f'{side}_finger_pad_{sign}',(.07,.012,.06),(.035,0,0),.055,(.15,.15,.18,1))
        return
    source=ET.parse(INSPIRE).getroot()
    links={x.get('name'):x for x in source.findall('link')}
    children={}
    for joint in source.findall('joint'):
        children.setdefault(joint.find('parent').get('link'),[]).append(joint)
    asset=root.find('asset');equal=root.find('equality')
    if equal is None:equal=ET.SubElement(root,'equality')
    def transform(node):
        origin=node.find('origin')
        if origin is None:return {'pos':'0 0 0'}
        rpy=list(map(float,origin.get('rpy','0 0 0').split()))
        quat=Rotation.from_euler('xyz',rpy).as_quat()[[3,0,1,2]]
        return dict(pos=origin.get('xyz','0 0 0'),quat=fmt(quat))
    def add_child(parent,joint):
        lname=joint.find('child').get('link');link=links[lname]
        body=ET.SubElement(parent,'body',name=lname,**transform(joint))
        inertial=link.find('inertial')
        if inertial is not None:
            inertia=inertial.find('inertia')
            # URDF inertia is expressed in the inertial frame. Rotate it into
            # the body frame before using MJCF fullinertia.
            a=inertia.attrib
            matrix=np.array([[float(a['ixx']),float(a['ixy']),float(a['ixz'])],
                             [float(a['ixy']),float(a['iyy']),float(a['iyz'])],
                             [float(a['ixz']),float(a['iyz']),float(a['izz'])]])
            tr=transform(inertial);q=np.array(list(map(float,tr.pop('quat','1 0 0 0').split())))
            rot=Rotation.from_quat(q[[1,2,3,0]]).as_matrix();matrix=rot@matrix@rot.T
            ET.SubElement(body,'inertial',mass=inertial.find('mass').get('value'),pos=tr['pos'],
                fullinertia=fmt([matrix[0,0],matrix[1,1],matrix[2,2],matrix[0,1],matrix[0,2],matrix[1,2]]))
        if joint.get('type')!='fixed':
            lim=joint.find('limit');eff=float(lim.get('effort'))
            ET.SubElement(body,'joint',name=joint.get('name'),type='hinge',axis=joint.find('axis').get('xyz'),
                          range=f"{lim.get('lower')} {lim.get('upper')}",actuatorfrcrange=f'{-eff} {eff}',damping='.05')
            mimic=joint.find('mimic')
            if mimic is not None:
                ET.SubElement(equal,'joint',joint1=joint.get('name'),joint2=mimic.get('joint'),
                              polycoef=f"{mimic.get('offset','0')} {mimic.get('multiplier','1')} 0 0 0")
                metadata['mimic_followers'].append(joint.get('name'))
        for tag in ['visual','collision']:
            for index,g in enumerate(link.findall(tag)):
                mesh=g.find('geometry/mesh')
                if mesh is None:raise ValueError('Unsupported Inspire primitive')
                path=(INSPIRE.parent/mesh.get('filename')).resolve();assert path.is_file(),path
                meshname=f'{lname}_{tag}_{index}'
                ET.SubElement(asset,'mesh',name=meshname,file=str(path),scale=mesh.get('scale','1 1 1'))
                ET.SubElement(body,'geom',name=meshname,type='mesh',mesh=meshname,
                              contype='1' if tag=='collision' else '0',conaffinity='1' if tag=='collision' else '0',
                              rgba='.65 .68 .72 1',**transform(g))
                metadata['mesh_hashes'][str(path)]=sha(path)
        for nxt in children.get(lname,[]):add_child(body,nxt)
    for joint in children[f'{side}_wrist_yaw_link']:
        if joint.find('child').get('link').startswith(('L_','R_')):add_child(wrist,joint)


def ring(root,world,name,pos,radius,cfg,out):
    from humanoid.g1_tabletop.assets import _ring_mesh
    body=ET.SubElement(world,'body',name=name,pos=fmt(pos));ET.SubElement(body,'freejoint',name=name+'_free')
    # Raised inner foot leaves a real 9 mm underside approach gap at the rim.
    for label,outer,inner,height,z in [('plate',radius,cfg.disk_inner_radius,.016,.0045),
                                     ('foot',min(radius-.005,.032),cfg.disk_inner_radius,.009,-.008)]:
        mesh=out/f'{name}_{label}.obj';mesh.write_text(_ring_mesh(outer,inner,height,12))
        meshname=f'{name}_{label}'
        ET.SubElement(root.find('asset'),'mesh',name=meshname,file=str(mesh))
        for j in range(12):
            ET.SubElement(body,'geom',name=f'{meshname}_{j}',type='mesh',mesh=meshname,
                          pos=fmt((0,0,z)),quat=fmt((math.cos(j*math.pi/12),0,0,math.sin(j*math.pi/12))),
                          mass=str(cfg.disk_mass*(.8 if label=='plate' else .2)/12),
                          rgba=fmt((*cfg.disk_colors[int(name.split('_')[1])],1)),
                          friction=f'{cfg.disk_friction} .005 .0001',condim='4')


def build(task,out):
    import mujoco
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    c=contract(task);cfg=config(task);root=ET.parse(G1).getroot()
    metadata=dict(task=c,source_model=str(G1),source_model_sha256=sha(G1),
                  mimic_followers=[],mesh_hashes={},runtime_state_writes=False,
                  tool_attachment_constraints=False,body_calibration='experimental')
    root.find('compiler').set('meshdir',str(G1.parent/'assets'))
    world=root.find('worldbody');robot=world.find('body');robot.set('pos','0 0 .79')
    for element in list(world):
        if element is not robot:world.remove(element)
    for body in robot.iter('body'):
        for j in list(body):
            if j.tag=='freejoint':body.remove(j)
    for tag in ['keyframe','sensor']:
        for node in list(root.findall(tag)):root.remove(node)
    if c['embodiment']!='dex3':
        for side in ['left','right']:replace_hand(root,side,c['embodiment'],metadata)
    joint_nodes=list(robot.iter('joint'));names=[j.get('name') for j in joint_nodes]
    # Rebuild actuators after swapping hands. Mimic followers stay passive.
    for a in list(root.findall('actuator')):root.remove(a)
    actuators=ET.SubElement(root,'actuator')
    limits={};velocities={}
    for j in joint_nodes:
        name=j.get('name');bounds=list(map(float,j.get('range').split()))
        force=max(map(abs,map(float,j.get('actuatorfrcrange').split())))
        hand=('_hand_' in name or '_parallel_' in name or name.startswith(('L_','R_')))
        if c['capability_profile']=='grip_boundary_candidate' and hand:force*=.25
        if c['capability_profile']=='wrist_boundary_candidate' and 'wrist' in name:force*=.35
        limits[name]=dict(lower=bounds[0],upper=bounds[1],effort=force,
                          kp=800. if '_parallel_slide_' in name else 6. if hand else 35. if 'wrist' in name else 150. if 'waist' in name else 160. if 'knee' in name else 100.,
                          kd=8. if '_parallel_slide_' in name else .25 if hand else 1.5 if 'wrist' in name else 5.,
                          velocity=.06 if j.get('type')=='slide' else 1.2)
        if name not in metadata['mimic_followers']:
            ET.SubElement(actuators,'motor',name=name+'_motor',joint=name,gear='1',forcelimited='true',forcerange=f'{-force} {force}')
    metadata['robot_joints']=names;metadata['limits']=limits
    ground=ET.SubElement(world,'body',name='ground',pos='0 0 -.01')
    box(ground,'ground_geom',(5,5,.02),mass=0,color=(.25,.28,.30,1))
    table=ET.SubElement(world,'body',name='table',pos=fmt((*cfg.table_center,cfg.table_height-cfg.table_size[2]/2)))
    box(table,'table_geom',cfg.table_size,mass=0,color=(.60,.48,.34,1))
    for peg,(x,y) in cfg.peg_positions.items():
        pad=ET.SubElement(world,'body',name='pad_'+peg,pos=fmt((x,y,cfg.table_height+cfg.pad_thickness/2)))
        box(pad,'pad_geom_'+peg,(.21,.21,cfg.pad_thickness),mass=0,color=(.3,.65,.4,1) if peg=='C' else (.55,.6,.65,1))
        rod=ET.SubElement(world,'body',name='rod_'+peg,pos=fmt((x,y,cfg.pad_top+cfg.rod_height/2)))
        ET.SubElement(rod,'geom',name='rod_geom_'+peg,type='cylinder',size=fmt((cfg.rod_radius,cfg.rod_height/2)),rgba='.7 .73 .77 1')
    for name,pos in cfg.initial_positions().items():
        ring(root,world,name,pos,cfg.disk_radii[cfg.object_names.index(name)],cfg,out)
    fork=ET.SubElement(world,'body',name='T2_fork',pos='.42 -.40 .775');ET.SubElement(fork,'freejoint',name='T2_free')
    box(fork,'T2_handle',(.05,.026,.06),(-.075,0,0),.06,(.15,.35,.8,1))
    box(fork,'T2_crossbar',(.025,.086,.008),(-.037,0,-.020),.025,(.2,.45,.8,1))
    for sign in [-1,1]:box(fork,f'T2_prong_{sign}',(.14,.012,.004),(.045,sign*.037,-.022),.025,(.65,.7,.75,1))
    tongs=ET.SubElement(world,'body',name='T1_tongs',pos='.42 .40 .775');ET.SubElement(tongs,'freejoint',name='T1_free')
    box(tongs,'T1_handle',(.05,.026,.06),(-.075,0,0),.06,(.8,.35,.15,1))
    box(tongs,'T1_spine',(.06,.035,.012),(-.035,0,-.015),.03,(.75,.45,.2,1))
    for sign in [-1,1]:
        jaw=ET.SubElement(tongs,'body',name=f'T1_jaw_{sign}',pos=fmt((-.015,sign*.02,-.015)))
        ET.SubElement(jaw,'joint',name=f'T1_hinge_{sign}',type='hinge',axis=fmt((0,0,sign)),range='0 .7',stiffness='.15',springref='.45',damping='.02')
        box(jaw,f'T1_bar_{sign}',(.14,.008,.012),(.065,sign*.008,0),.035,(.8,.45,.2,1))
    # Geom-level attribution is retained for independent contact-chain audits.
    for g in world.findall('geom'):g.set('friction','.7 .005 .0001')
    path=out/'scene.xml';ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
    model=mujoco.MjModel.from_xml_path(str(path))
    metadata.update(scene_sha256=sha(path),nq=model.nq,nv=model.nv,
                    source_inspire_sha256=sha(INSPIRE) if c['embodiment']=='inspire' else None,
                    tools_initial={'T1_tongs':[.42,.40,.775],'T2_fork':[.42,-.40,.775]},
                    disk_geometry='12-segment annulus; 16mm plate over 9mm inner support foot',
                    E2_parameters='synthetic parallel gripper; two independent 35mm slides, 25N each; no commercial calibration')
    (out/'model.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return path,metadata


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();path,meta=build(a.task,a.out);print(json.dumps({'path':str(path),'nq':meta['nq'],'joints':len(meta['robot_joints'])}))
