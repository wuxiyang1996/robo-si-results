"""Choose a verified baseline, then submit bounded, evidence-producing checks."""
import argparse,datetime,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text()) if p.exists() else {}
def main():
 p=argparse.ArgumentParser();p.add_argument('--setting',required=True);p.add_argument('--cohort',required=True);p.add_argument('--baselines',nargs='+',required=True);a=p.parse_args()
 chosen=None
 for name in a.baselines:
  root=BASE/'runs'/name;s=read(root/'summary.json');v=read(root/'verification.json')
  if s.get('setting')==a.setting and all(x is True for x in [s.get('task_success'),v.get('task_success'),v.get('replay_matches'),v.get('source_hashes_match')]):chosen=name;break
 assert chosen,'No verified successful baseline; no qualification campaign launched'
 subprocess.run([sys.executable,'-m','df_family.qualify_extension','freeze','--setting',a.setting,'--cohort',a.cohort,'--baseline',str(BASE/'runs'/chosen)],check=True)
 jobs=[]
 def submit(label,script,*args,dependency=None):
  cmd=['sbatch','--parsable','-J',label]
  if dependency:cmd+=['--dependency',dependency,'--kill-on-invalid-dep=yes']
  result=subprocess.check_output(cmd+[str(BASE/script),*map(str,args)],text=True).strip();job=int(result.split(';')[0]);jobs.append(dict(job=job,label=label,args=list(map(str,args)),dependency=dependency));return job
 repeats=[];submissions=[]
 cohort=BASE/'qualification'/a.setting/a.cohort
 for repeat in [1,2,3]:
  job=submit(f'df-{a.setting}-q{repeat}','run_extension_qualification.sbatch',a.setting,a.cohort,repeat);repeats.append(job);submissions.append(dict(repeat=repeat,slurm_job=str(job),submitted_at=datetime.datetime.now(datetime.timezone.utc).isoformat()));(cohort/'submissions.json').write_text(json.dumps(submissions,indent=2)+'\n')
 bundle=BASE/'acceptance'/('portable-'+chosen);isolated=BASE/'isolated'/(chosen+'-recorded');fresh=BASE/'portable-validation'/(chosen+'-fresh')
 preparation=read(BASE/'acceptance/prepared-reference-jobs.json').get(chosen)
 evidence=submit('df-'+chosen+'-evidence','run_extension_evidence.sbatch',BASE/'runs'/chosen,bundle,dependency=f'afterany:{preparation}' if preparation else None)
 isolation=submit('df-'+chosen+'-isolated','run_extension_isolated.sbatch',BASE/'runs'/chosen,isolated,dependency=f'afterok:{evidence}')
 portable=submit('df-'+chosen+'-portable','run_portable_extension.sbatch',bundle,fresh,dependency=f'afterok:{evidence}')
 finalizer=submit('df-'+chosen+'-collect','run_extension_collect.sbatch',a.setting,a.cohort,chosen,dependency='afterany:'+':'.join(map(str,[*repeats,evidence,isolation,portable])))
 receipt=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),setting=a.setting,cohort=a.cohort,baseline=chosen,jobs=jobs,scope='Submitted automated checks; no passed gate or external signoff implied')
 (cohort/'campaign-jobs.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
