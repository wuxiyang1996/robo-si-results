"""Copy referenced assets only and validate path-independent compiled physics identity."""
import argparse,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import mujoco,numpy as np
ROOT=Path(__file__).resolve().parent
FIELDS=['body_mass','body_ipos','body_inertia','body_pos','body_quat','jnt_pos','jnt_axis','jnt_range','dof_damping','dof_armature','geom_type','geom_size','geom_pos','geom_quat','geom_friction','geom_solref','geom_solimp','geom_contype','geom_conaffinity','mesh_vert','mesh_face','actuator_ctrlrange','actuator_forcerange','actuator_gainprm','actuator_biasprm','eq_data']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(runs,destination):
 if destination.exists():raise FileExistsError('Use a fresh bundle directory')
 destination.mkdir(parents=True);assets=destination/'assets';assets.mkdir();files={};records=[]
 for run in runs:
  scene=run/'scene.xml';tree=ET.parse(scene);xml=tree.getroot();compiler=xml.find('compiler');assetdir=Path(compiler.get('assetdir','')) if compiler is not None else Path();folder=destination/run.name;folder.mkdir()
  for element in xml.findall('.//asset/*'):
   for key,value in list(element.attrib.items()):
    if not key.startswith('file'):continue
    path=Path(value)
    if key=='file' and element.tag in ['mesh','texture','hfield'] and 'name' not in element.attrib:element.set('name',path.stem)
    if not path.is_absolute():
     specific=compiler.get('texturedir' if element.tag=='texture' else 'meshdir','') if compiler is not None else ''
     directory=Path(specific) if specific else assetdir
     path=(directory if directory.is_absolute() else scene.parent/directory)/path
    path=path.resolve();h=digest(path);name=h+path.suffix.lower();target=assets/name
    if not target.exists():shutil.copyfile(path,target)
    files[name]={'sha256':h,'bytes':target.stat().st_size,'source':str(path)};element.set(key,'../assets/'+name)
  if compiler is not None:
   for k in ['assetdir','meshdir','texturedir']:compiler.attrib.pop(k,None)
  portable=folder/'scene.xml';tree.write(portable,encoding='unicode');original=mujoco.MjModel.from_xml_path(str(scene));copied=mujoco.MjModel.from_xml_path(str(portable));checks={k:bool(np.array_equal(getattr(original,k),getattr(copied,k))) for k in FIELDS}
  assert all(checks.values()),(run,checks)
  for name in ['initial_state.json','model-binding.json','plan.json']:
   if (run/name).exists():shutil.copyfile(run/name,folder/name)
  records.append({'run':run.name,'original_scene_sha256':digest(scene),'portable_scene_sha256':digest(portable),'compiled_physics_arrays_identical':checks})
 license_root=ROOT.parent.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache'
 licenses={}
 for project in ['unitree_ros','stretch_mujoco']:
  source=license_root/project/'LICENSE';target=destination/(project+'-LICENSE');shutil.copyfile(source,target);licenses[target.name]=digest(target)
 report={'licenses':licenses,'schema':'disk-flip-portable-assets/1','scope':'Referenced robot and object assets plus path-rewritten scenes; development evidence only, no automatic acceptance','files':files,'runs':records,'total_asset_bytes':sum(x['bytes'] for x in files.values())}
 (destination/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'runs':len(records),'referenced_assets':len(files),'bytes':report['total_asset_bytes'],'all_compiled_identity_checks':True,'destination':str(destination)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('runs',type=Path,nargs='+');a=p.parse_args();build(a.runs,a.output)
