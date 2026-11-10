"""Audit complete or partial recorded attempts without upgrading their status."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import numpy as np


def verify(folder):
    folder=Path(folder);result=json.loads((folder/'result.json').read_text());checks={}
    if not result.get('physics_steps'):
        return dict(task_id=result['task_id'],scope='setup failure',task_success=False,checks={},artifacts={})
    lim=json.loads((folder/'limits.json').read_text());traj=np.load(folder/'trajectory.npz')
    with gzip.open(folder/'actions.jsonl.gz','rt') as f:actions=[json.loads(x) for x in f]
    mapping=json.loads((folder/'executed-plan.json').read_text())['segments']
    checks['action_count']=len(actions)==result['controls']==len(traj['q'])==len(traj['target'])
    checks['continuous_commands']=bool(actions) and actions[0]['physics_start']==0 and all(
        a['physics_end_exclusive']==b['physics_start'] for a,b in zip(actions,actions[1:])) and actions[-1]['physics_end_exclusive']==result['physics_steps']
    checks['finite_trajectory']=all(np.isfinite(traj[k]).all() for k in ['q','qd','target','time'])
    checks['target_limits']=bool((traj['target']>=np.asarray(lim['lower'])-1e-8).all() and (traj['target']<=np.asarray(lim['upper'])+1e-8).all())
    checks['recorded_targets_match']=np.array_equal(traj['target'],np.asarray([a['target'] for a in actions]))
    checks['phase_mapping']=all(any(s['high_id']==a['high'] and s['low_id']==a['low'] and
        s['physics_start']<=a['physics_start'] and s['physics_end_exclusive']>=a['physics_end_exclusive'] for s in mapping) for a in actions)
    count=0;torque_ok=True
    with gzip.open(folder/'physics.jsonl.gz','rt') as f:
        for line in f:
            s=json.loads(line);count+=1
            if s['physics_step']!=count:torque_ok=False
            if not (np.abs(np.asarray(s['torque']))<=np.asarray(lim['effort'])+1e-8).all():torque_ok=False
    checks['physics_steps_and_torque_caps']=count==result['physics_steps'] and torque_ok
    checks['no_runtime_state_write_attempts']=not result['runtime_state_write_attempts']
    checks['source_unchanged']=json.loads((folder/'source-check.json').read_text())['source_unchanged']
    checks['video_exists']=(folder/'video.mp4').is_file() and result['video_frames']>0
    artifacts={}
    for name in result['artifacts']+['result.json','source-hashes.json','source-check.json','environment.json','limits.json']:
        p=folder/name;artifacts[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    return dict(schema='hanoi-attempt-audit/1',task_id=result['task_id'],
                scope='record continuity and declared constraints; not independent physical replay',
                audit_passed=all(checks.values()),task_success=bool(result['task_success']),
                independent_replay=False,checks=checks,artifacts=artifacts)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args();r=verify(a.folder)
    (a.folder/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
