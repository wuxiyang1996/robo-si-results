"""Import evidence-audited Astra results without publishing private logs."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]

def source_id(path):
    name=str(path).replace('\\','/')
    for prefix,label in [('D:/rsi_vla/','workspace/'),('C:/rsi_efe/','runtime/')]:
        if name.startswith(prefix):return label+name[len(prefix):]
    raise ValueError('Unrecognized evidence root')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('audit',type=Path);args=ap.parse_args()
    data=json.loads(args.audit.read_text(encoding='utf-8'))
    astra=data['models']['Astra'];tasks=[];sources={}
    for item in astra['tasks']:
        row=item['selected'];assert row is not None
        valid=row['valid'];proof=None
        for path_key,sha_key in [('result_path','result_sha256'),('native_verdict_path','native_verdict_sha256')]:
            path,sha=row.get(path_key),row.get(sha_key)
            if path and sha:
                assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
                sources[source_id(path)]=sha
        if valid:
            proof={'case':item['case'],'campaign':row['campaign'],'model':row['model_id'],'reasoning_effort':row['effort'],
                   'runtime_verified':True,'success':row['success'],'submission_unchanged':True,
                   'native_score':row['native_score'],'stage_score':row['stage_score'],
                   'score_scale':row['score_scale'],'stage_scoring_version':row.get('stage_scoring_version'),
                   'stage_details':row['stage_details'],'result_source':source_id(row['result_path']),
                   'result_sha256':row['result_sha256'],'native_verdict_source':source_id(row['native_verdict_path']),
                   'native_verdict_sha256':row['native_verdict_sha256'],'snapshot':row['snapshot'],'regrade':row['repair']}
        tasks.append({'case':item['case'],'family':item['family'],'local_scope':not row['campaign'].startswith('remote-'),
                      'status':row['status'],'valid':valid,'success':row['success'] if valid else None,
                      'native_score':row['native_score'] if valid else None,'stage_score':row['stage_score'] if valid else None,
                      'score_scale':row['score_scale'] if valid else None,'snapshot':row['snapshot'],
                      'attempts':item['attempt_count'],'standard_ready':True,'privileged_ready':True,
                      'campaign':row['campaign'],'effort':row['effort'],'regrade':row['repair'],'evidence':proof})
    assert len(tasks)==len({t['case'] for t in tasks})==246
    score_tasks=[t for t in tasks if t['valid'] and isinstance(t['stage_score'],(int,float))]
    assert all(0<=t['stage_score']<=100 for t in score_tasks)
    total=len(tasks);valid=sum(t['valid'] for t in tasks);success=sum(t['success'] is True for t in tasks)
    summary={'benchmark':{'cases':total,'families':29,'standard_ready':246,'privileged_ready':246,'case_modes_ready':492},
             'model':'Astra','mode':'privileged','settings':dict(Counter(t['effort'] for t in tasks)),
             'covered':total,'valid':valid,'success':success,'unsuccessful':sum(t['success'] is False for t in tasks),
             'pending':total-valid,'verified_success_fraction_all_tasks':success/total,
             'success_rate_valid':success/valid if valid else None,
             'aggregate_246_success_rate':success/total if valid==total else None,
             'case_status_counts':dict(Counter(t['status'] for t in tasks)),
             'stage_score_count':len(score_tasks),'stage_score_sum':sum(t['stage_score'] for t in score_tasks),
             'stage_score_mean_valid':sum(t['stage_score'] for t in score_tasks)/len(score_tasks) if score_tasks else None,
             'stage_score_mean_all_tasks':sum(t['stage_score'] for t in score_tasks)/total if len(score_tasks)==total else None,
             'official_efe_run':False,
             'counting_policy':'Unique tasks. Prefer verified success, otherwise valid evaluation; prefer non-snapshot then most recent. Exploratory aggregate across settings and retries.'}
    output={'schema':'robo-si-leaderboard/2','updated':data['updated_at'][:10],'audited_at':data['updated_at'],
            'summary':summary,'tasks':tasks,'source_checksums':sources,'scope':'Astra only; all retained workspace campaigns and imported remote results',
            'source_audit_sha256':hashlib.sha256(args.audit.read_bytes()).hexdigest()}
    (ROOT/'site/content/leaderboard.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
