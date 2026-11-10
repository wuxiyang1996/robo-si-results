"""Freeze development code before queueing; this is not qualification or success."""
import argparse,datetime,hashlib,json,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--tuning',type=Path,required=True);a=p.parse_args();assert a.name.replace('-','').replace('_','').isalnum()
 root=BASE/'snapshots'/a.name;root.mkdir(parents=True,exist_ok=False);package=root/'expert';package.mkdir();(package/'__init__.py').write_text('')
 tuning=json.loads(a.tuning.read_text());files=['run.py','model.py','wrench.py','reference_interface.py']
 if tuning.get('prefix_completion') in ['dex3_index_bridge','dex3_plate_bridge']:files.append('dex3_plate_expert.py' if tuning['prefix_completion']=='dex3_plate_bridge' else 'dex3_expert.py')
 if tuning.get('reference_prefix_file'):
  prefix=Path(tuning['reference_prefix_file']);assert prefix.name==str(prefix);files.extend([prefix.name,prefix.with_suffix('.json').name])
 for name in files:shutil.copyfile(BASE/name,package/name)
 shutil.copyfile(a.tuning,root/'tuning.json')
 entry='''import hashlib,json,sys
from pathlib import Path
from expert import model,run
root=Path(sys.argv[1]);manifest=json.loads((root/'manifest.json').read_text())
def check():
 for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
check();model.CACHE=Path(manifest['asset_cache']);model.OUT=Path(manifest['generated_assets'])
sys.argv=['frozen-development-candidate','--setting',sys.argv[2],'--output',sys.argv[3],'--tuning',str(root/'tuning.json')]
try:code=run.main()
finally:check()
raise SystemExit(code)
'''
 (root/'entry.py').write_text(entry)
 paths=[p for p in root.rglob('*') if p.is_file()];manifest=dict(schema='disk-flip-development-snapshot/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},asset_cache=str(BASE.parent.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache'),generated_assets=str(BASE/'assets'),scope='Frozen development candidate code and tuning; no physical success or qualification claim')
 (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(root)
if __name__=='__main__':main()
