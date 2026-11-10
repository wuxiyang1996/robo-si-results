"""Read-only evidence ledger: development progress never implies formal admission."""
import argparse,datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SETTINGS=['DF-01-G','DF-02-G','DF-02-F','DF-03-G','DF-04-G','DF-04-S']
def read(path):
 try:return json.loads(path.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return {}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'acceptance/status.json');args=parser.parse_args()
 plan=read(ROOT/'acceptance/plan-v1.json');runs=[]
 videos={r['run']:r for r in read(ROOT/'acceptance/release-video-validation.json').get('videos',[])}
 for path in sorted((ROOT/'runs').glob('DF-*')):
  if not path.is_dir() or 'replay' in path.name:continue
  setting=next((s for s in SETTINGS if path.name.startswith(s+'-')),None)
  if setting is None:continue
  summary=read(path/'summary.json');verification=read(path/'verification.json')
  if not summary:continue
  original=setting=='DF-01-G'
  if original:
   success=bool(summary.get('status',{}).get('success',False) if isinstance(summary.get('status'),dict) else summary.get('success',False))
   # The original has its own independent verifier; keep that report separate.
   success=bool(success and summary.get('full_task_success',False) and verification.get('fresh_complete_execution',False) and verification.get('independent_physics_replay') is True)
  else:success=bool(summary.get('task_success') is True and verification.get('task_success') is True and verification.get('replay_matches') is True and verification.get('source_hashes_match') is True)
  video=videos.get(path.name,{});video_path=path/'video.mp4'
  video_valid=bool(video.get('full_decode_passed') is True and video_path.exists() and hashlib.sha256(video_path.read_bytes()).hexdigest()==video.get('sha256')) if success else False
  coverage=verification.get('high_low_trajectory_coverage' if original else 'continuous_high_low_trajectory_coverage') is True
  physics=verification.get('original_scorer_unchanged') is True if original else verification.get('source_hashes_match') is True and verification.get('actuator_limits_passed') is True
  runs.append(dict(run=path.name,setting=setting,scope='development',complete_physical_witness=success,high_low_coverage_verified=coverage,physics_and_sources_verified=physics,full_video_decode_verified=video_valid,
   simulated_seconds=summary.get('simulated_seconds',summary.get('status',{}).get('elapsed') if isinstance(summary.get('status'),dict) else None),failure=summary.get('failure',summary.get('error')),
   control_replay_matches=verification.get('independent_physics_replay') if original else verification.get('replay_matches'),seen_lift=summary.get('seen_lift'),seen_flip=summary.get('seen_flip'),source_hashes=summary.get('source_hashes',{})))
 settings=[]
 for setting in SETTINGS:
  candidates=[r for r in runs if r['setting']==setting]
  cohorts=sorted((ROOT/'qualification'/setting).glob('cohort-v*'),key=lambda p:int(p.name.removeprefix('cohort-v')));cohort=cohorts[-1] if cohorts else ROOT/'qualification'/setting/'cohort-v1';qualification=read(cohort/'status.json');started=(cohort/'manifest.json').exists()
  witness=any(r['complete_physical_witness'] for r in candidates)
  gates={name:dict(status='pending',evidence=[]) for name in plan['required_automatic_gates']}
  def mark(name,status,evidence):gates[name]=dict(status=status,evidence=evidence)
  if witness:
   mark('complete_generated_start_to_goal_success','passed',[r['run'] for r in candidates if r['complete_physical_witness']])
   for name,field in [('high_low_and_trajectory_mapping_coverage','high_low_coverage_verified'),('same_limits_and_physics_as_task','physics_and_sources_verified'),('videos_and_contact_transition_review_material','full_video_decode_verified')]:
    evidence=[r['run'] for r in candidates if r['complete_physical_witness'] and r[field]]
    if evidence:mark(name,'passed',evidence)
  if qualification.get('repetition_gate'):mark('repetition_cohort','passed',[str(cohort.relative_to(ROOT)/'status.json')])
  if qualification.get('replay_gate'):mark('independent_scorer_and_control_replay','passed',[str(cohort.relative_to(ROOT)/'status.json')])
  if setting=='DF-01-G':
   checks=read(ROOT/'acceptance/original-frozen-scorer-checks.json')
   if checks.get('passed'):mark('no_op_and_stage_counterexamples','passed',['acceptance/original-frozen-scorer-checks.json'])
   isolated=read(ROOT/'acceptance/original-isolated-closed-loop.json')
   if isolated.get('passed') and isolated.get('negative_cases_passed') and isolated.get('full_task_success'):
    mark('integrity_and_illegal_action_probes','passed',['acceptance/original-isolated-closed-loop.json'])
   elif witness:mark('integrity_and_illegal_action_probes','partial',['Run integrity audits passed; bound closed-loop rejection report pending'])
   if isolated.get('passed') and isolated.get('policy_is_closed_loop'):
    mark('isolated_action_interface_execution','passed' if isolated.get('independent_physics_replay') is True and isolated.get('high_low_trajectory_coverage') is True else 'partial',['acceptance/original-isolated-closed-loop.json'])
   portable=read(ROOT/'acceptance/original-portable-download.json');validation=read(ROOT/'acceptance/original-portable-validation.json')
   if portable.get('sha256') and portable.get('url') and validation.get('passed') and portable.get('bundled_source_matches_fresh_validation'):
    mark('portable_assets_and_reproducible_commands','passed',['acceptance/original-portable-download.json','acceptance/original-portable-validation.json'])
  else:
   body=setting[-1];probe=read(ROOT/f'acceptance/isolated-boundary-{body}.json')
   if probe.get('passed'):
    mark('integrity_and_illegal_action_probes','partial',[f'acceptance/isolated-boundary-{body}.json','Boundary probes passed; a successful complete task is still required'])
    mark('no_op_and_stage_counterexamples','partial',[f'acceptance/isolated-boundary-{body}.json','Physical no-op passed; stage counterexamples pending'])
   supplement=read(ROOT/f'acceptance/extension-validation-{setting}.json')
   if supplement.get('baseline') in [r['run'] for r in candidates if r['complete_physical_witness']]:
    for name,passed in supplement.get('checks',{}).items():
     if passed and name in gates:mark(name,'passed',[f'acceptance/extension-validation-{setting}.json',*supplement.get('evidence',{}).values()])
  all_automatic=all(g['status']=='passed' for g in gates.values())
  settings.append(dict(setting=setting,development_attempts=len(candidates),complete_witnesses=[r['run'] for r in candidates if r['complete_physical_witness']],
   qualification_cohort=cohort.name if started else 'not_started',qualification_history=[read(c/'status.json') for c in cohorts],qualification_progress=qualification if started else None,required_fresh_repeats=plan['qualification_cohort']['fresh_runs_per_setting'],
   automatic_gates=gates,automatic_acceptance='passed' if all_automatic else 'pending',human_video_signoff='pending',second_person_reproduction='pending',formally_admitted=False))
 report=dict(schema='disk-flip-acceptance-status/1',generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  scope='Six declared settings; all listed runs are development unless a separately frozen qualification manifest says otherwise',
  settings=settings,runs=runs,formally_admitted=False,
  note='This ledger cannot create human signoff or independent-person reproduction. Partial skills and matching replays of failed executions do not count as complete witnesses.')
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'completed_development_records':len(runs),'formal_admission':False,'report':str(args.output)}))
if __name__=='__main__':main()
