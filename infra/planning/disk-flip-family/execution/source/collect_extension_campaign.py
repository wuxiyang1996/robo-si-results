"""Collect completed checks and publish verified evidence; never invent external signoff."""
import argparse,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
from .publish_evidence import publish
BASE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text()) if p.exists() else {}
def command(module,*args):subprocess.run([sys.executable,'-m','df_family.'+module,*map(str,args)],check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--setting',required=True);p.add_argument('--cohort',required=True);p.add_argument('--baseline',required=True);a=p.parse_args();name=a.baseline
 command('qualify_extension','report','--setting',a.setting,'--cohort',a.cohort)
 root=BASE/'runs'/name;bundle=BASE/'acceptance'/('portable-'+name);fresh=BASE/'portable-validation'/(name+'-fresh');validation=read(fresh/'portable-validation.json');manifest=bundle/'expert-manifest.json'
 if validation.get('passed') is True:
  m=read(manifest);assert validation['bundle_manifest_sha256']==hashlib.sha256(manifest.read_bytes()).hexdigest()
  assert all(hashlib.sha256((bundle/n).read_bytes()).hexdigest()==h for n,h in m['files'].items())
  archive=bundle.with_suffix('.tar.gz')
  with tarfile.open(archive,'w:gz') as tar:tar.add(bundle,arcname=bundle.name)
  download=publish(archive,name+'-portable-expert');download['bundle_manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest();download['scope']='Fresh relocated nominal expert and independent replay verified; no second-person claim'
  (BASE/'acceptance'/f'portable-{a.setting}-download.json').write_text(json.dumps(download,indent=2)+'\n')
 command('extension_scorer_checks',root/'run.py','--output',BASE/'acceptance'/('extension-scorer-'+name+'.json'))
 command('isolated_action_probe',root,'--output',BASE/'acceptance'/('isolated-boundary-'+name+'.json'))
 command('extension_acceptance','--setting',a.setting,'--baseline',name,'--scorer',BASE/'acceptance'/('extension-scorer-'+name+'.json'),'--boundary',BASE/'acceptance'/('isolated-boundary-'+name+'.json'),'--isolated',BASE/'isolated'/(name+'-recorded')/'report.json','--portable',fresh/'portable-validation.json','--bundle',bundle)
 if read(root/'reference-replay-verification.json').get('all_physics_state_and_control_array_hashes_match') is True:
  command('publish_run_evidence',name)
  selection=BASE/'acceptance/public-selection-development.json';selected=read(selection);selected=[name if x.startswith(a.setting+'-') else x for x in selected];selection.write_text(json.dumps(selected,indent=2)+'\n')
 command('acceptance_status');command('monitor');command('export_report','--selection',BASE/'acceptance/public-selection-development.json')
if __name__=='__main__':main()
