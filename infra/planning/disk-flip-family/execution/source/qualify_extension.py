"""Frozen nominal extension repetitions; checkpoint diagnostics never qualify."""
import argparse, datetime, hashlib, importlib.metadata, json, shutil, subprocess, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
CACHE=BASE.parent.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache'
CODE=['run.py','model.py','wrench.py','reference_interface.py']
def read(p):return json.loads(p.read_text()) if p.exists() else {}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def check(root,m):
 for n,h in m['source_hashes'].items():assert sha(root/'frozen_expert'/n)==h,n
 for n,h in m['verification_sources'].items():assert sha(root/'frozen_verification'/n)==h,n
 for n,h in m['asset_hashes'].items():assert sha(Path(n))==h,n
 assert sha(root/'tuning.json')==m['tuning_sha256']
 assert sha(root/'entry.py')==m['entry_sha256']
 assert {k:importlib.metadata.version(k) for k in m['runtime']}==m['runtime']
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run','report']);p.add_argument('--setting',required=True);p.add_argument('--cohort',default='cohort-v1');p.add_argument('--baseline',type=Path);p.add_argument('--repeat',type=int,choices=[1,2,3]);a=p.parse_args()
 assert a.setting in ['DF-02-G','DF-02-F','DF-03-G','DF-04-G','DF-04-S'];assert a.cohort.startswith('cohort-v') and a.cohort[8:].isdigit()
 root=BASE/'qualification'/a.setting/a.cohort;manifest=root/'manifest.json'
 if a.action=='freeze':
  assert not root.exists();source=a.baseline.resolve();summary=read(source/'summary.json');v=read(source/'verification.json');assert summary.get('task_success') and v.get('task_success') and v.get('replay_matches');assert summary['setting']==a.setting
  root.mkdir(parents=True);package=root/'frozen_expert';package.mkdir();(package/'__init__.py').write_text('')
  source_files=CODE+[n for n in summary['source_hashes'] if n not in CODE+['plan.json','scene.xml']]
  for n in source_files:
   assert Path(n).name==n
   assert sha(source/n)==summary['source_hashes'][n];shutil.copyfile(source/n,package/n)
  validation=root/'frozen_verification';validation.mkdir();(validation/'__init__.py').write_text('')
  for n in ['verify.py','compact_evidence.py']:shutil.copyfile(BASE/n,validation/n)
  plan=read(source/'plan.json');(root/'tuning.json').write_text(json.dumps(plan['controller_tuning'],indent=2)+'\n')
  from .portable_bundle import build
  build([source],root/'portable-scene');assets=read(root/'portable-scene/manifest.json')['files'];hashes={x['source']:x['sha256'] for x in assets.values()};hashes[summary['binding']['source']]=summary['binding']['source_sha256']
  entry="""from pathlib import Path
import sys
from frozen_expert import model,run
model.CACHE=Path(sys.argv[1]);model.OUT=Path(sys.argv[2])
sys.argv=['frozen-expert','--setting',sys.argv[3],'--tuning',sys.argv[4],'--output',sys.argv[5]]
raise SystemExit(run.main())
""";(root/'entry.py').write_text(entry)
  m=dict(schema='disk-flip-extension-qualification/1',setting=a.setting,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline=str(source),baseline_summary_sha256=sha(source/'summary.json'),baseline_verification_sha256=sha(source/'verification.json'),source_hashes={n:sha(package/n) for n in source_files},verification_sources={n:sha(validation/n) for n in ['verify.py','compact_evidence.py']},asset_hashes=hashes,tuning_sha256=sha(root/'tuning.json'),entry_sha256=sha(root/'entry.py'),cache=str(CACHE),generated_asset_directory=str(BASE/'assets'),runtime={n:importlib.metadata.version(n) for n in ['mujoco','numpy','scipy','imageio']},expected_plan=plan,expected_scene_sha256=sha(source/'scene.xml'),repetitions=[dict(id=f'repeat-{i:02}') for i in [1,2,3]],replace_failed_repetition=False,scope='Fresh nominal fixed-base executions of frozen extension sources, same assets/physics/limits. No random-start robustness, public-agent score or external signoff.')
  check(root,m);manifest.write_text(json.dumps(m,indent=2)+'\n');print(manifest);return
 m=read(manifest);check(root,m)
 if a.action=='run':
  assert a.repeat;out=root/f'repeat-{a.repeat:02}';assert not out.exists()
  result=subprocess.run([sys.executable,str(root/'entry.py'),m['cache'],m['generated_asset_directory'],a.setting,str(root/'tuning.json'),str(out)],cwd=root);check(root,m)
  if (out/'summary.json').exists():
   subprocess.run([sys.executable,'-m','frozen_verification.verify',str(out)],cwd=root,check=True)
   if a.repeat==1:subprocess.run([sys.executable,'-m','frozen_verification.compact_evidence',str(out)],cwd=root,check=True)
  raise SystemExit(result.returncode)
 rows=[]
 for rep in m['repetitions']:
  out=root/rep['id'];s=read(out/'summary.json');v=read(out/'verification.json');checks=dict(complete=s.get('task_success') is True,independent_replay=v.get('task_success') is True and v.get('replay_matches') is True,high_low=v.get('continuous_high_low_trajectory_coverage') is True,source_hashes=all(s.get('source_hashes',{}).get(n)==h for n,h in m['source_hashes'].items()),same_scene=s.get('source_hashes',{}).get('scene.xml')==m['expected_scene_sha256'],same_plan=read(out/'plan.json')==m['expected_plan'])
  execution_checks=all(checks[k] for k in ['complete','source_hashes','same_scene','same_plan'])
  status='passed' if all(checks.values()) else 'awaiting_independent_verification' if execution_checks and not v else 'failed' if s else 'pending'
  rows.append(dict(id=rep['id'],status=status,full_success=all(checks.values()),execution_passed=execution_checks,verification_pending=bool(execution_checks and not v),checks=checks,failure=s.get('failure')))
 compact=read(root/'repeat-01/reference-replay-verification.json');replay=compact.get('all_physics_state_and_control_array_hashes_match') is True and rows[0]['checks']['independent_replay']
 report=dict(setting=a.setting,cohort=a.cohort,manifest_sha256=sha(manifest),repetitions=rows,repetition_gate=all(r['full_success'] for r in rows),replay_gate=replay,replay_status='passed' if replay else 'pending',formally_admitted=False,external_review='pending');(root/'status.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
