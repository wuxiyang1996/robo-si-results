"""Read-only per-task progress ledger, including failed attempts and live jobs."""
from pathlib import Path
import argparse
import json
from datetime import datetime,timezone
from .contracts import TASKS,FAMILY,contract


def collect():
    tasks=[]
    for task in TASKS:
        row=dict(**contract(task),attempts=[],expert_success=False,high_low_plan_available=True,
                 physical_feasibility='not_established',trajectory_available=False,video_available=False)
        for folder in sorted((FAMILY/'runs').glob(task+'-*')):
            result=folder/'result.json';heartbeat=folder/'heartbeat.json'
            if not heartbeat.exists():continue
            value=json.loads((result if result.exists() else heartbeat).read_text())
            attempt=dict(path=str(folder.relative_to(FAMILY)),finished=result.exists(),
                         **{k:value[k] for k in ['reason','state','physics_steps','simulation_seconds','video_frames','task_success','move_count'] if k in value})
            row['attempts'].append(attempt)
            row['trajectory_available']|=(folder/'trajectory.npz').exists()
            row['video_available']|=(folder/'video.mp4').exists() and value.get('video_frames',0)>0
            if value.get('task_success'):
                row['expert_success']=True;row['physical_feasibility']='one_full_reference_pending_independent_replay'
        tasks.append(row)
    return dict(schema='hanoi-family-progress/1',updated_utc=datetime.now(timezone.utc).isoformat(),
                task_count=len(tasks),successful_tasks=sum(x['expert_success'] for x in tasks),tasks=tasks)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args();r=collect()
    if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))
