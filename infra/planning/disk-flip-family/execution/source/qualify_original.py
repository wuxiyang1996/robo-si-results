"""Predeclared nominal repetitions of the frozen original, separate from development."""
import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;REPO=BASE.parent;SNAPSHOT=BASE/'snapshots/original-v1';COHORT=BASE/'qualification/DF-01-G/cohort-v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text()) if p.exists() else {}
def check(manifest):
 for relative,want in manifest['source_hashes'].items():assert digest(SNAPSHOT/relative)==want,relative
 for relative,want in manifest['robot_asset_hashes'].items():assert digest(SNAPSHOT/relative)==want,relative
 assert digest(BASE/'original-plan.json')==manifest['plan_sha256']
def main():
 global SNAPSHOT,COHORT
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run','replay','report']);parser.add_argument('--repeat',type=int,choices=[1,2,3]);parser.add_argument('--cohort',default='cohort-v1');parser.add_argument('--snapshot',default='original-v1');parser.add_argument('--baseline',default='DF-01-G-a02');parser.add_argument('--replay-output',type=Path);args=parser.parse_args();assert args.cohort.startswith('cohort-v') and args.cohort.removeprefix('cohort-v').isdigit();COHORT=BASE/'qualification/DF-01-G'/args.cohort;path=COHORT/'manifest.json'
 if args.action=='freeze':SNAPSHOT=BASE/'snapshots'/args.snapshot
 else:SNAPSHOT=BASE/'snapshots'/read(path).get('snapshot','original-v1')
 if args.action=='freeze':
  assert not path.exists(),'Never replace a frozen cohort';COHORT.mkdir(parents=True,exist_ok=True)
  baseline=read(BASE/'runs'/args.baseline/'summary.json');assets=read(BASE/'runs'/args.baseline/'asset_hashes.json');assert baseline.get('full_task_success');sources={k:digest(SNAPSHOT/k) for k in baseline['sources_sha256']};relative='humanoid/g1_tabletop_disk_flip/solution/hierarchy.py';sources[relative]=digest(SNAPSHOT/relative)
  manifest=dict(snapshot=args.snapshot,baseline=args.baseline,schema='disk-flip-qualification-cohort/1',setting='DF-01-G',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Three fresh nominal runs of frozen original fixed-base Genesis expert; not randomized robustness or formal admission',seed=0,backend='cpu',source_hashes=sources,robot_asset_hashes={k:v for k,v in assets.items() if not k.startswith('generated_disk/')},plan_sha256=digest(BASE/'original-plan.json'),expected_config=baseline['config'],expected_physics=baseline['physics'],runtime_versions=baseline['runtime_versions'],repetitions=[dict(id=f'repeat-{i:02}',seed=0) for i in [1,2,3]],independent_replay_of='repeat-01',replace_failed_repetition=False,other_gates='pending; this cohort does not supply human review, second-person reproduction or process isolation')
  check(manifest);path.write_text(json.dumps(manifest,indent=2)+'\n');print(path);return
 manifest=read(path);check(manifest)
 if args.action in ['run','replay']:
  assert args.repeat is not None
  source=COHORT/f'repeat-{args.repeat:02}';out=source if args.action=='run' else args.replay_output or COHORT/f'repeat-{args.repeat:02}-replay';assert not out.exists(),out
  command=[sys.executable,'-m','humanoid.g1_tabletop_disk_flip.solution.run','--output',str(out),'--backend','cpu','--seed','0','--video']
  if args.action=='replay':command+=['--replay',str(source/'trajectory.npz')]
  result=subprocess.run(command,cwd=SNAPSHOT);check(manifest)
  if args.action=='run' and (out/'summary.json').exists():subprocess.run([sys.executable,'-m','df_family.verify_original',str(out)],cwd=REPO,check=True)
  if args.action=='replay' and (out/'summary.json').exists():
   replay=read(out/'summary.json');verification=read(source/'verification.json');verification.update(independent_physics_replay=bool(replay.get('independent_action_replay_verified')),independent_replay_checks=replay.get('replay_checks',{}),independent_replay_run=str(out));(source/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
  raise SystemExit(result.returncode)
 rows=[]
 for entry in manifest['repetitions']:
  folder=COHORT/entry['id'];s=read(folder/'summary.json');v=read(folder/'verification.json')
  assets=read(folder/'asset_hashes.json')
  checks=dict(complete=bool(s.get('full_task_success') and s.get('error') is None),high_low_coverage=v.get('high_low_trajectory_coverage') is True,config=s.get('config')==manifest['expected_config'],physics=s.get('physics')==manifest['expected_physics'],runtime=s.get('runtime_versions')==manifest['runtime_versions'],source_hashes=bool(s) and all(s.get('sources_sha256',{}).get(k)==value for k,value in manifest['source_hashes'].items() if not k.endswith('/hierarchy.py')),robot_assets=bool(assets) and all(assets.get(k)==value for k,value in manifest['robot_asset_hashes'].items()))
  passed=all(checks.values())
  rows.append(dict(id=entry['id'],status='passed' if passed else 'failed' if s else 'pending',full_success=passed,checks=checks,failure=s.get('error'),independent_replay=v.get('independent_physics_replay') is True))
 replay_path=read(COHORT/'repeat-01/verification.json').get('independent_replay_run');replay_summary=read(Path(replay_path)/'summary.json') if replay_path else read(COHORT/'repeat-01-replay/summary.json')
 result=dict(replay_status='passed' if rows[0]['independent_replay'] else 'failed' if replay_summary else 'pending',replay_checks=replay_summary.get('replay_checks'),setting='DF-01-G',cohort=args.cohort,manifest_sha256=digest(path),repetitions=rows,repetition_gate=all(r['full_success'] for r in rows),replay_gate=rows[0]['independent_replay'],formally_admitted=False,external_review='pending')
 (COHORT/'status.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
