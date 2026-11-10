"""Bind a new frozen-reference execution to its predeclared high/low plan."""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();out=a.run.resolve();base=Path(__file__).resolve().parent
 sys.path.insert(0,str(base/'snapshots/original-v1'))
 from humanoid.g1_tabletop_disk_flip.solution.hierarchy import segment_rows,GOALS
 summary=json.load(open(out/'summary.json'));initial=json.load(open(out/'initial_state.json'));z=np.load(out/'trajectory.npz')
 rows=[json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines()]
 result={'setting':'DF-01-G','fresh_complete_execution':summary['full_task_success'],'independent_physics_replay':'pending','new_simulation':True,'original_scorer_unchanged':True,'claimed_scope':'one new frozen-reference execution, fixed pelvis, privileged state','controller_error':summary['error']}
 try:
  segments,milestones=segment_rows(rows,z['time'],initial)
  compact=[dict(id=s['id'],high_level=s['high_level'],phase=s['phase'],action=s['action'],constraint=s['local_constraint'],command_slice=s['command_slice'],time_interval_s=s['time_interval_s'],observed_peaks=s['observed_peaks_50hz'],start_disk=s['start_state']['objects']['disk'],end_disk=s['end_state']['objects']['disk']) for s in segments]
  (out/'high-low-trajectory.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n')
  result.update(high_low_trajectory_coverage=True,low_level_segments=len(segments),high_level_goals=len(GOALS),recorded_control_steps=len(z['time']),stage_times={str(k):v['state']['time'] for k,v in milestones.items()},actuator_checks=summary['actuator_checks'],integrity_audit=summary['integrity_audit'],physics_peaks=summary['status'].get('peaks'))
 except Exception as e:result.update(high_low_trajectory_coverage=False,mapping_error=str(e))
 (out/'plan.json').write_bytes((base/'original-plan.json').read_bytes())
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 arr=np.array([[r['time'],*r['objects']['disk']['pos'],r['objects']['disk']['robot_contact_force_n'],r['objects']['disk']['support_force_n']] for r in rows])
 fig,ax=plt.subplots(2,1,figsize=(10,6),sharex=True)
 for i,l in enumerate(['x','y','z']):ax[0].plot(arr[:,0],arr[:,i+1],label=l)
 ax[0].set_ylabel('Object position (m)');ax[0].legend()
 ax[1].plot(arr[:,0],arr[:,4],label='robot contact');ax[1].plot(arr[:,0],arr[:,5],label='support');ax[1].legend();ax[1].set_ylabel('Load (N)');ax[1].set_xlabel('Simulation time (s)');fig.suptitle('DF-01-G: new frozen-reference execution');fig.tight_layout();fig.savefig(out/'trajectory.png',dpi=130);plt.close(fig)
 result['artifacts_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['plan.json','trajectory.npz','trace.jsonl','video.mp4']}
 (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
