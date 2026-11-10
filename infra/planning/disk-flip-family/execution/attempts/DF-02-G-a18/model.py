"""Official body imports and physical plate geometry for extension probes.

MuJoCo is used for new extension development; the original remains Genesis.
This change of engine is explicit and does not transfer original scores.
"""
from pathlib import Path
import copy, hashlib, json, math, re, tempfile, xml.etree.ElementTree as ET
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache'
OUT=Path(__file__).resolve().parent/'assets'

def build_robot(body,collision_profile="original"):
    OUT.mkdir(exist_ok=True)
    record={'body':body,'simulation_engine':'MuJoCo','base':'fixed during episode'}
    if body in ('G','F'):
        name='g1_29dof_with_hand_rev_1_0.urdf' if body=='G' else 'g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf'
        source=CACHE/'unitree_ros/robots/g1_description'/name
        tree=ET.parse(source).getroot()
        for mesh in tree.findall('.//mesh'):
            filename=mesh.get('filename').removeprefix('package://g1_description/')
            mesh.set('filename',str((source.parent/filename).resolve()))
        mj=tree.find('mujoco')
        if mj is None:mj=ET.SubElement(tree,'mujoco')
        comp=mj.find('compiler')
        if comp is None:comp=ET.SubElement(mj,'compiler')
        comp.attrib.update(discardvisual='false',fusestatic='false',balanceinertia='false')
        with tempfile.TemporaryDirectory(prefix=f'df-{body}-') as temporary:
            tmp=Path(temporary)/f'{body}.urdf';ET.ElementTree(tree).write(tmp)
            model=mujoco.MjModel.from_xml_path(str(tmp));path=Path(temporary)/f'{body}-import.xml';mujoco.mj_saveLastXML(str(path),model)
            xml=ET.parse(path).getroot()
        world=xml.find('worldbody')
        root=world.find('body');root.set('pos','0 0 0.79')
        act=ET.SubElement(xml,'actuator');eq=ET.SubElement(xml,'equality')
        limits={}
        for joint in tree.findall('joint'):
            if joint.get('type')=='fixed':continue
            n=joint.get('name');lim=joint.find('limit');limits[n]=dict(lim.attrib)
            original=next(x for x in xml.findall('.//joint') if x.get('name')==n)
            original.set('damping','0.1' if ('hand' in n or n.startswith(('L_','R_'))) else '1')
            original.set('armature','0.001' if ('hand' in n or n.startswith(('L_','R_'))) else '0.02')
            if joint.find('mimic') is not None:
                m=joint.find('mimic');ET.SubElement(eq,'joint',joint1=n,joint2=m.get('joint'),polycoef=f"{m.get('offset','0')} {m.get('multiplier','1')} 0 0 0")
            else:
                effort=float(lim.get('effort'));ET.SubElement(act,'motor',name=n,joint=n,ctrlrange=f'{-effort} {effort}',ctrllimited='true')
        for node in list(xml.findall('keyframe')):xml.remove(node)
        contact=ET.SubElement(xml,'contact')
        for side in ['left','right']:ET.SubElement(contact,'exclude',body1='pelvis_contour_link',body2=side+'_hip_pitch_link')
        if collision_profile=='inspire-palms-v2':
            if body!='F':raise ValueError('Inspire collision profile requires F embodiment')
            directory=OUT/'inspire-palms-v2';manifest=json.loads((directory/'manifest.json').read_text())
            for name,part_record in manifest['parts'].items():
                b=world.find(f".//body[@name='{name}']")
                original=[g for g in b.findall('geom') if g.get('mesh')==name and g.get('contype','1')!='0']
                if len(original)!=1:raise RuntimeError('Unexpected palm collision geometry')
                original=original[0];b.remove(original)
                for i,row in enumerate(part_record['files']):
                    meshname=f'{name}_convex_{i:02}';file=directory/row['file']
                    if hashlib.sha256(file.read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Convex asset changed')
                    ET.SubElement(xml.find('asset'),'mesh',name=meshname,file=str(file.resolve()))
                    geom=copy.deepcopy(original);geom.set('mesh',meshname);geom.set('name',meshname);b.append(geom)
            record['collision_geometry_version']=collision_profile
            record['collision_decomposition']=manifest
            record['collision_geometry_rationale']='Original triangle palm socket is replaced by a single convex hull in the naive import; decompose instead of excluding palm-thumb contacts. See inspire-collision-audit.json.'
        elif collision_profile!='original':raise ValueError('Unknown collision profile')
        record['collision_exclusions']=['fixed pelvis contour vs adjacent left/right hip pitch (URDF visual shell overlap)']
        record['actuator_limits']=limits
        record['adaptations']=['fixed base at z=.79','bounded torque PD; URDF efforts and limits','URDF mimic joint equality; no object coupling','joint damping and armature declared in model']
    else:
        source=CACHE/'stretch_mujoco/stretch_mujoco/models/stretch.xml'
        xml=ET.parse(source).getroot();xml.find('compiler').set('assetdir',str(source.parent/'assets'))
        # MuJoCo 3.14 rejects zero-volume decorative meshes from the official model.
        shell_meshes={g.get('mesh') for g in xml.findall('.//geom') if g.get('shellinertia')=='true'}
        shell_meshes.add('base_link_6')
        for mesh in xml.findall('./asset/mesh'):
            if (mesh.get('name') or Path(mesh.get('file','')).stem) in shell_meshes:mesh.set('inertia','shell')
        for g in xml.findall('.//geom'):g.attrib.pop('shellinertia',None)
        world=xml.find('worldbody');base=world.find("body[@name='base_link']")
        if base is None:base=world.find('body')
        base.set('pos','-0.22 0.02 0');base.set('euler','0 0 1.5707963267948966');base.attrib.pop('quat',None)
        for j in list(base):
            if j.tag=='freejoint' or j.tag=='joint' and j.get('type')=='free':base.remove(j)
        for k in list(xml.findall('keyframe')):xml.remove(k)
        record['adaptations']=['fixed base at declared placement','original tendon, finger mimic equality and collision exclusions','original position actuators; explicit effort caps applied at runtime','MuJoCo 3.14 compatibility: visual mesh shellinertia moved to mesh inertia=shell']
    record['source']=str(source);record['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    return xml,record

def add_plate(world,profile):
    # 0.12 kg in all first candidates; no mass scaling to ease a failed attempt.
    foot=-.006 if profile=='P1' else -.014
    obj=ET.SubElement(world,'body',name='disk',pos=f'.40 0 {0.86-foot}')
    ET.SubElement(obj,'freejoint',name='disk_free')
    parts=[]
    def geom(name,kind,size,pos,rgba,**kw):
        node=ET.SubElement(obj,'geom',name=name,type=kind,size=size,pos=pos,rgba=rgba,friction='.7 .005 .0001',condim='4',density='1000',**kw);parts.append(node);return node
    if profile=='P1':
        geom('disk_body','cylinder','.1 .006','0 0 0','.95 .48 .10 1')
    else:
        geom('plate_floor','cylinder','.077 .002','0 0 -.006','.95 .48 .10 1')
        # Separate convex sector meshes retain the concavity and rim underside.
        assets=[]
        for label,r0,r1,z0,z1 in [('wall',.074,.080,-.008,.006),('rim',.079,.1,0,.006),('foot',.053,.060,-.014,-.008)]:
            for k in range(32):
                a,b=2*math.pi*k/32,2*math.pi*(k+1)/32
                verts=[(r*math.cos(t),r*math.sin(t),z) for z in [z0,z1] for r,t in [(r0,a),(r1,a),(r1,b),(r0,b)]]
                name=f'{label}_{k}';assets.append((name,verts));geom(name,'mesh','1','0 0 0','.95 .48 .10 1',mesh=name)
        # Explicit uniform material density fixes total mass while retaining geometry-derived COM/inertia.
        volume=math.pi*.077**2*.004+sum(math.sin(2*math.pi/32)*16*(r1*r1-r0*r0)*(z1-z0) for r0,r1,z0,z1 in [(.074,.080,-.008,.006),(.079,.1,0,.006),(.053,.060,-.014,-.008)])
        for g in parts:g.set('density',str(.12/volume))
        return obj,assets,foot
    parts[0].set('mass','.12')
    return obj,[],foot

def build_scene(body,profile,out,collision_profile="original"):
    xml,record=build_robot(body,collision_profile)
    opt=xml.find('option')
    if opt is None:opt=ET.SubElement(xml,'option')
    opt.set('timestep','.0025');opt.set('integrator','implicitfast');opt.set('cone','elliptic');opt.set('gravity','0 0 -9.81')
    visual=xml.find('visual')
    if visual is None:visual=ET.SubElement(xml,'visual')
    ET.SubElement(visual,'global',offwidth='960',offheight='720')
    asset=xml.find('asset')
    if asset is None:asset=ET.SubElement(xml,'asset')
    world=xml.find('worldbody')
    ET.SubElement(world,'light',pos='0 -1 3',dir='0 0 -1')
    ET.SubElement(world,'geom',name='ground',type='plane',size='3 3 .1',rgba='.22 .25 .29 1')
    ET.SubElement(world,'geom',name='table',type='box',size='.35 .575 .025',pos='.7 0 .835',rgba='.70 .62 .48 1',friction='.7 .005 .0001')
    obj,meshes,foot=add_plate(world,profile)
    for name,verts in meshes:ET.SubElement(asset,'mesh',name=name,vertex=' '.join(str(v) for p in verts for v in p))
    # Bottom face marker is visual only.
    ET.SubElement(obj,'geom',name='blue_face',type='cylinder',size='.05 .0001',pos=f'0 0 {foot-.00015}',rgba='.10 .45 .90 1',contype='0',conaffinity='0',mass='0',group='2')
    if body=='S':
        effort_caps={'left_wheel_vel':4.,'right_wheel_vel':4.,'lift':70.,'arm':56.,'wrist_yaw':1.9,'wrist_pitch':10.6,'wrist_roll':4.1,'gripper':80.,'head_pan':1.5,'head_tilt':1.9}
        for actuator in xml.find('actuator'):
            cap=effort_caps[actuator.get('name')];actuator.set('forcerange',f'{-cap} {cap}');actuator.set('forcelimited','true')
        record['effort_caps']=effort_caps
    out.mkdir(parents=True,exist_ok=True);path=out/'scene.xml';ET.ElementTree(xml).write(path,encoding='unicode')
    for retry in range(30):
        try:
            model=mujoco.MjModel.from_xml_path(str(path));break
        except ValueError as exc:
            found=re.search(r'mesh volume is too small: ([^ .]+)',str(exc))
            if body!='S' or not found:raise
            name=found.group(1)
            mesh=next(x for x in asset.findall('mesh') if (x.get('name') or Path(x.get('file','')).stem)==name)
            mesh.set('inertia','shell');record.setdefault('degenerate_mesh_shell_inertia',[]).append(name)
            ET.ElementTree(xml).write(path,encoding='unicode')
    else:raise RuntimeError('mesh compatibility repair exhausted')
    data=mujoco.MjData(model)
    record.update(object_profile=profile,geometry='solid cylinder' if profile=='P1' else 'convex sector decomposition; gaps retained',physics_dt=.0025,object_mass=float(model.body_mass[model.body('disk').id]),object_com=model.body_ipos[model.body('disk').id].tolist(),mujoco=mujoco.__version__)
    (out/'model-binding.json').write_text(json.dumps(record,indent=2)+'\n')
    return model,data,record
