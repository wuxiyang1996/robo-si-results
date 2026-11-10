"""Snapshot this family's declared jobs and last readable states without mutating runs."""
import datetime,json,subprocess
from pathlib import Path
BASE=Path(__file__).resolve().parent
JOBS={'DF-02-F-a40':8070133,'DF-02-G-a33':8069774,'DF-02-G-a32':8069581,'DF-03-G-a23':8069372,'DF-02-G-a31':8069253,'DF-03-G-a22':8069224,'DF-02-G-a30':8069076,'DF-03-G-a21':8069124,'DF-04-G-a27':8068004,'DF-04-G-a26':8067989,'DF-02-F-a39':8067017,'DF-02-F-a38':8066151,'DF-04-S-a28':8064776,'DF-04-S-a27':8064663,'DF-04-S-a26':8056898,'DF-04-S-a25':8056279,'DF-02-G-a29':8056287,'DF-02-F-a34':8056288,'DF-02-F-a35':8056332,'DF-02-F-a36':8056468,'DF-02-F-a37':8056637,'DF-03-G-a18':8056289,'DF-03-G-a19':8056483,'DF-03-G-a20':8056516}
def read(p):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return {}
def replay_progress(job):
 logs=list((BASE/'job-logs').glob(f'*-{job}.log'))
 if not logs:return None
 with logs[0].open('rb') as f:
  f.seek(max(0,logs[0].stat().st_size-65536));lines=f.read().decode(errors='replace').splitlines()
 for line in reversed(lines):
  try:r=json.loads(line)
  except json.JSONDecodeError:continue
  if isinstance(r,dict) and ('replay_physics_steps' in r or 'replay_commands' in r):return r
 return None
def main():
 jobs={n:(job,BASE/'runs'/n) for n,job in JOBS.items()}
 for submission in sorted((BASE/'qualification').glob('*/*/submissions.json')):
  for r in read(submission):
   path=submission.parent/f"repeat-{r['repeat']:02}"
   jobs[str(path.relative_to(BASE))]=(int(str(r['slurm_job']).split(';')[0]),path)
 states={}
 response=subprocess.run(['squeue','-h','-j',','.join(str(job) for job,_ in jobs.values()),'-o','%i|%T|%M'],capture_output=True,text=True)
 for line in response.stdout.splitlines():
  parts=line.split('|')
  if len(parts)==3:states[int(parts[0])]=dict(state=parts[1],elapsed=parts[2])
 rows=[]
 for n,(job,p) in jobs.items():
  s=read(p/'summary.json');v=read(p/'verification.json');live=read(p/'live-state.json');rows.append(dict(run=n,slurm_job=job,scheduler=states.get(job,{'state':'not_in_queue'}),output=str(p.resolve()),terminal_summary=bool(s),task_success=s.get('task_success'),failure=s.get('failure'),last_time=s.get('simulated_seconds',live.get('time')),phase=live.get('phase'),verified=v.get('replay_matches'),verified_success=v.get('task_success'),verification_progress=replay_progress(job) if not v else None))
 report=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),runs=rows,scope='Read-only job snapshot; not a background monitoring service or automatic signoff');p=BASE/'acceptance/live-jobs.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(p)
 for r in rows:print(r['run'],r['scheduler']['state'],r['last_time'],r['phase'],r['failure'],r['verified_success'])
if __name__=='__main__':main()
