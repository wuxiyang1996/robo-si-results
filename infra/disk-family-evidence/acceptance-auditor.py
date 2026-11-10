"""Fail-closed qualification of retained, reproducible simulation witnesses."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .verify import verify
from .cases import get


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def video_evidence(e,summary):
    """Decode both complete videos and bind frame counts to physics timestamps."""
    import imageio_ffmpeg
    times=np.asarray(json.loads((e/'video_frame_times.json').read_text())['simulation_times'])
    timing=(len(times)>1 and times[0]==0 and abs(times[-1]-summary['sim_time'])<1e-9
        and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.100000001
        and np.allclose(times/.0025,np.round(times/.0025),atol=1e-7,rtol=0))
    videos={}
    for name in ('video.mp4','overhead.mp4'):
        frames,seconds=imageio_ffmpeg.count_frames_and_secs(str(e/name))
        videos[name]=dict(frames=frames,seconds=seconds,sha256=sha(e/name),passed=frames==len(times))
    return dict(passed=bool(timing and all(v['passed'] for v in videos.values())),timestamp_count=len(times),timestamp_sha256=sha(e/'video_frame_times.json'),videos=videos)


def qualify(runs):
    contract_path=Path(__file__).with_name('acceptance-contract.json')
    contract=json.loads(contract_path.read_text());records=[]
    for case in contract['tasks']:
        valid=[];replays=[];rejected=[]
        for attempt in sorted((Path(runs)/case).glob('*')):
            e=attempt/'evidence'
            if not (e/'verification.json').exists():continue
            summary=json.loads((e/'summary.json').read_text())
            if not summary.get('success'):continue
            # Historical witnesses remain valid history, but cannot substitute
            # for the newly predeclared complete-input replay package.
            with np.load(e/'trajectory.npz') as z:
                complete_inputs='requested_targets' in z and 'wheel_commands' in z
            if not complete_inputs:continue
            audit=verify(e)
            sources=summary['source_hashes']
            integrity=all((attempt/'workspace'/p).is_file() and sha(attempt/'workspace'/p)==h for p,h in sources.items())
            config=summary['config'];lim=contract['unchanged_physical_limits']
            limits_ok=(config['heading_tolerance']<=np.deg2rad(lim['heading_error_degrees'])+1e-12
                and config['center_radius']<=lim['maximum_center_displacement_m']
                and config['final_center_error']<=lim['final_center_displacement_m']
                and config['settle_duration']>=lim['released_stable_seconds']
                and config['time_limit']<=lim['time_limit_seconds']
                and config['contact_force_max']<=lim['contact_force_N']
                and config['tilt_max']<=np.deg2rad(lim['tilt_degrees'])+1e-12
                and config['linear_speed_max']<=lim['linear_speed_m_per_s']
                and config['angular_speed_max']<=lim['angular_speed_rad_per_s'])
            video=all((e/n).is_file() and (e/n).stat().st_size>0 for n in ('video.mp4','overhead.mp4','video_frame_times.json','contacts.jsonl.gz','plan.json'))
            video_check=video_evidence(e,summary) if video else {'passed':False}
            expected=get(case)
            case_matches=all(summary['configuration'][k]==expected[k] for k in ('body','task','materials','scene'))
            normal_reset=summary.get('start')=='normal_reset' and summary.get('state_splicing') is False
            passed=audit['passed'] and integrity and limits_ok and video_check['passed'] and case_matches and normal_reset
            row=dict(attempt=attempt.name,summary_sha256=sha(e/'summary.json'),trajectory_sha256=sha(e/'trajectory.npz'),source_integrity=integrity,limits_unchanged=limits_ok,evidence_present=video,independent_audit=audit['passed'],sim_time=summary['sim_time'])
            row.update(video_audit=video_check,task_configuration_matches=case_matches,normal_reset=normal_reset,deterministic_algorithms=summary.get('deterministic_algorithms',False))
            if not passed:rejected.append(row);continue
            row['source_fingerprint']=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
            row['configuration_fingerprint']=hashlib.sha256(json.dumps(summary['configuration'],sort_keys=True).encode()).hexdigest()
            if summary.get('replay_source'):
                row['replay_source']=summary['replay_source'];row['replay_check']=summary['replay_check'];replays.append(row)
            else:valid.append(row)
        accepted=None
        for primary in sorted(valid,key=lambda r:not r['deterministic_algorithms']):
            repeats=[r for r in valid if r['source_fingerprint']==primary['source_fingerprint'] and r['configuration_fingerprint']==primary['configuration_fingerprint']]
            linked=[r for r in replays if r['source_fingerprint']==primary['source_fingerprint'] and r['replay_source']['trajectory_sha256']==primary['trajectory_sha256'] and r['replay_source']['summary_sha256']==primary['summary_sha256']]
            if len(repeats)>=2 and linked:
                accepted=dict(primary=primary['attempt'],normal_runs=[r['attempt'] for r in repeats],replays=[r['attempt'] for r in linked]);break
        records.append(dict(case_id=case,passed=accepted is not None,accepted=accepted,valid_normal=valid,valid_replays=replays,rejected_successes=rejected))
    return dict(schema='dr-acceptance-result/1',contract_sha256=sha(contract_path),auditor_sha256=sha(Path(__file__)),passed=all(r['passed'] for r in records),tasks=records,scope=contract['scope'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,default=Path(__file__).with_name('runs'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=qualify(a.runs);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for r in result['tasks']:print(r['case_id'],r['passed'],r['accepted'])
    raise SystemExit(0 if result['passed'] else 2)
