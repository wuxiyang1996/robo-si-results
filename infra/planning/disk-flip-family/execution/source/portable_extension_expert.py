"""Package a verified extension expert with portable scene assets and commands."""
import argparse,hashlib,json,shutil
from pathlib import Path
from .portable_bundle import build,FIELDS
BASE=Path(__file__).resolve().parent
ENTRY='''import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import mujoco,numpy as np
from frozen_expert import run
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
manifest=json.loads((ROOT/'expert-manifest.json').read_text())
for name,h in manifest['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
scene=ROOT/manifest['run']/'scene.xml'
def portable_scene(body,profile,out,**kwargs):
 binding=json.loads((scene.parent/'model-binding.json').read_text());assert body==binding['body'] and profile==binding['object_profile']
 assert abs(kwargs['physics_dt']-binding['physics_dt'])<1e-12
 tree=ET.parse(scene)
 for element in tree.getroot().findall('.//asset/*'):
  for key,value in list(element.attrib.items()):
   if key.startswith('file'):element.set(key,str((scene.parent/value).resolve()))
 target=out/'scene.xml';tree.write(target,encoding='unicode');model=mujoco.MjModel.from_xml_path(str(target));original=mujoco.MjModel.from_xml_path(str(scene))
 for key in manifest['compiled_fields']:assert np.array_equal(getattr(model,key),getattr(original,key)),key
 tuning=json.loads((ROOT/'tuning.json').read_text())
 if tuning.get('reference_prefix_file'):
  metadata=out/Path(tuning['reference_prefix_file']).with_suffix('.json').name
  prefix=json.loads(metadata.read_text());assert prefix['scene_sha256']==manifest['baseline_scene_sha256']
  prefix['original_scene_sha256']=prefix['scene_sha256'];prefix['scene_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
  prefix['relocation']='Asset paths only; compiled physics arrays checked by portable loader'
  metadata.write_text(json.dumps(prefix,indent=2)+'\\n')
 (out/'model-binding.json').write_text(json.dumps(binding,indent=2)+'\\n')
 (out/'portable-initialization.json').write_text(json.dumps(dict(adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),compiled_physics_arrays_identical=True,source_manifest_sha256=hashlib.sha256((ROOT/'expert-manifest.json').read_bytes()).hexdigest()),indent=2)+'\\n')
 return model,mujoco.MjData(model),binding
run.build_scene=portable_scene
sys.argv=['frozen-expert','--setting',manifest['setting'],'--tuning',str(ROOT/'tuning.json'),'--output',str(a.output.resolve())]
raise SystemExit(run.main())
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run=a.run.resolve();out=a.output.resolve();v=json.loads((run/'verification.json').read_text());s=json.loads((run/'summary.json').read_text());assert v['task_success'] and v['replay_matches']
 build([run],out);pkg=out/'frozen_expert';pkg.mkdir();(pkg/'__init__.py').write_text('')
 for name in [n for n in s['source_hashes'] if n not in ['plan.json','scene.xml']]:
  assert Path(name).name==name
  assert hashlib.sha256((run/name).read_bytes()).hexdigest()==s['source_hashes'][name];shutil.copyfile(run/name,pkg/name)
 for name in ['verify.py','compact_evidence.py']:shutil.copyfile(BASE/name,out/name)
 for name in ['summary.json','verification.json','segments.json','high-low-trajectory.json','trajectory-reference.npz','trajectory-reference.json','reference-replay-verification.json']:
  shutil.copyfile(run/name,out/run.name/name)
 plan=json.loads((run/'plan.json').read_text());(out/'tuning.json').write_text(json.dumps(plan['controller_tuning'],indent=2)+'\n');(out/'run_expert.py').write_text(ENTRY)
 (out/'REPRODUCE.md').write_text(f'''# {s['setting']} portable expert

This package contains the frozen privileged expert and identical portable physics
assets. It does not claim hardware performance, human signoff or second-person
reproduction. The scene loader only rewrites asset paths during initialization;
it checks compiled arrays before fresh execution. Source, tuning and assets are
bound by `expert-manifest.json`.

Use Python 3.12, MuJoCo 3.14.0, NumPy, SciPy, imageio, imageio-ffmpeg and matplotlib.
Run from this extracted directory. Use a fresh output path and at least 10 GB free.

```bash
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
python run_expert.py --output fresh-execution
python verify.py fresh-execution
python compact_evidence.py --replay {run.name}
```

The first command executes the frozen expert from a fresh initialized scene.
See the archived summary and plan for its policy scope: a fixed nominal reference
prefix, when present, is explicitly not a generalizing closed-loop policy. The last
command independently reconstructs all physics states and actuator controls from
the compact held-reference packet and compares exact array SHA-256 hashes.
Original run metadata retains historical source paths for provenance; portable
scene asset references resolve entirely within this extracted package.
''')
 files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
 m=dict(schema='disk-flip-portable-extension-expert/1',setting=s['setting'],run=run.name,baseline_scene_sha256=hashlib.sha256((run/'scene.xml').read_bytes()).hexdigest(),files=files,compiled_fields=FIELDS,baseline_verification_sha256=hashlib.sha256((run/'verification.json').read_bytes()).hexdigest(),scope='Portable nominal privileged expert. Fresh relocated execution must pass before portable acceptance; no external signoff.')
 (out/'expert-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(bundle=str(out),files=len(files))))
if __name__=='__main__':main()
