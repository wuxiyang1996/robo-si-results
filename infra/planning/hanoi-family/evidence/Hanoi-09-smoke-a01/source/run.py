"""Record a continuous physical attempt, including failures and partial evidence."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import numpy as np
from .contracts import TASKS, FAMILY, contract, plan, config


def plain(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x


def write(path,data):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(plain(data),ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)


def hashes():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FAMILY.glob('*.py')}


class Monitor:
    def __init__(self,e,out,max_controls):
        from humanoid.g1_support_retrieval.solution.step_up.video import VideoWriter
        self.e=e;self.out=out;self.max_controls=max_controls;self.controls=0
        self.high='P00';self.low='P00.L01';self.events=[];self.predictions=[]
        self.segments=[];self.actions=[];self.q=[];self.qd=[];self.times=[]
        self.physics=gzip.open(out/'physics.jsonl.gz','wt');self.lowfile=open(out/'low_plan.jsonl','w')
        self.video=VideoWriter(out/'video.mp4',fps=5);self.frames=0;self.next_frame=0.;self.start=time.monotonic()
        self.tool_chain_steps=0;self.e.observer=self.observe
        self.last_state=None;self.last_phase=None
        self.peak_torque=np.zeros(len(e.names));self.max_limit_error=0.
        write(out/'limits.json',dict(names=e.names,lower=e.lo,upper=e.hi,effort=e.effort,velocity=e.velocity))

    def phase(self,high,low,action):
        self.high,self.low=high,low
        if self.segments:self.segments[-1]['physics_end_exclusive']=self.e.steps
        entry=dict(high_id=high,low_id=low,action=action,physics_start=self.e.steps,
                   physics_end_exclusive=None,control_start=self.controls)
        self.segments.append(entry);self.lowfile.write(json.dumps(entry)+'\n');self.lowfile.flush()

    def observe(self,state):
        self.last_state=state
        self.peak_torque=np.maximum(self.peak_torque,np.abs(self.e.last_tau))
        self.tool_chain_steps+=int(any(state[n]['tool_chain_contact'] for n in self.e.cfg.object_names))
        self.physics.write(json.dumps(plain(dict(physics_step=self.e.steps,time=self.e.steps*.005,
            high=self.high,low=self.low,objects=state,contacts=self.e.last_contacts,
            torque=self.e.last_tau,status=self.e.status)),allow_nan=False,separators=(',',':'))+'\n')

    def control(self,target):
        from .runtime import array
        start=self.e.steps;state=self.e.step(target);self.controls+=1
        q=array(self.e.entity.get_dofs_position(self.e.dofs));qd=array(self.e.entity.get_dofs_velocity(self.e.dofs))
        self.actions.append(dict(index=self.controls-1,high=self.high,low=self.low,
                                 physics_start=start,physics_end_exclusive=self.e.steps,target=self.e.target.copy()))
        self.q.append(q);self.qd.append(qd);self.times.append(self.e.steps*.005)
        self.max_limit_error=max(self.max_limit_error,float(np.max(np.maximum(self.e.lo-q,q-self.e.hi))))
        now=self.e.steps*.005
        if now+1e-9>=self.next_frame:
            frame=self.e.render();self.video.append_data(frame);self.frames+=1;self.next_frame=now+.2
            if self.frames==1:
                import imageio.v3 as iio
                iio.imwrite(self.out/'initial.png',frame)
        if self.controls%10==0:
            self.physics.flush()
            write(self.out/'heartbeat.json',dict(state='running',high=self.high,low=self.low,physics_steps=self.e.steps,
                simulation_seconds=now,wall_seconds=time.monotonic()-self.start,controls=self.controls,video_frames=self.frames,
                move_count=self.e.status['move_count']))
        return state

    def finish(self,reason):
        if self.segments:self.segments[-1]['physics_end_exclusive']=self.e.steps
        self.physics.close();self.lowfile.close();self.video.close()
        write(self.out/'executed-plan.json',dict(schema='hanoi-executed-plan/1',segments=self.segments,
              only_executed_ranges=True,physics_index_convention='commands/segments: zero-based start inclusive and end exclusive; physics records: 1-based completed-step number'))
        write(self.out/'events.json',self.events);write(self.out/'predictions.json',self.predictions)
        with gzip.open(self.out/'actions.jsonl.gz','wt') as f:
            for action in self.actions:f.write(json.dumps(plain(action),allow_nan=False)+'\n')
        np.savez_compressed(self.out/'trajectory.npz',q=np.asarray(self.q),qd=np.asarray(self.qd),
                            target=np.asarray([x['target'] for x in self.actions]),time=self.times,joint_names=self.e.names)
        report=dict(schema='hanoi-attempt/1',task_id=self.e.contract['task_id'],task_success=bool(self.e.status['success']),
            formal_admission=False,reason=reason,physical_status=self.e.status,continuous_from_initial_state=True,
            expert_scope='privileged feasibility candidate; not an isolated agent or self-modeling score',
            tool_chain_physics_steps=self.tool_chain_steps,physics_steps=self.e.steps,controls=self.controls,
            simulation_seconds=self.e.steps*.005,wall_seconds=time.monotonic()-self.start,
            video_frames=self.frames,video_seconds=self.frames/5,video_speed=1,
            runtime_state_write_attempts=self.e.violations,max_joint_limit_error=self.max_limit_error,
            torque_caps_respected=bool((self.peak_torque<=self.e.effort+1e-9).all()),
            independent_replay=False,boundary_calibrated=False,
            artifacts=['high_low_plan.json','executed-plan.json','trajectory.npz','physics.jsonl.gz','actions.jsonl.gz','video.mp4'])
        write(self.out/'result.json',report);write(self.out/'heartbeat.json',dict(state='finished',**report))
        return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',choices=list(TASKS),required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--backend',choices=['gpu','cpu'],default='gpu')
    p.add_argument('--mode',choices=['smoke','expert'],default='expert');p.add_argument('--max-controls',type=int,default=2500)
    p.add_argument('--max-moves',type=int);p.add_argument('--seed',type=int,default=0)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    write(a.out/'task.json',contract(a.task));write(a.out/'scene-config.json',asdict(config(a.task)))
    write(a.out/'high_low_plan.json',plan(a.task));before=hashes();write(a.out/'source-hashes.json',before)
    write(a.out/'heartbeat.json',dict(state='building_scene',task_id=a.task,pid=os.getpid(),host=os.uname().nodename))
    env=monitor=None;reason=None;result=None
    try:
        from .runtime import Environment
        env=Environment(a.task,a.out,a.backend,a.seed)
        write(a.out/'environment.json',env.model_info);monitor=Monitor(env,a.out,a.max_controls)
        write(a.out/'initial-state.json',env.state());env.install_guards()
        from .controller import Expert
        expert=Expert(env,monitor,a.max_moves)
        if a.mode=='smoke':
            expert.set_phase('P00','P00.L01','bounded scene/contact smoke, not task execution');expert.hold(2.)
            reason='scene_smoke_only'
        else:expert.run();reason='task_completed' if env.status['success'] else 'candidate_returned_without_success'
    except Exception as exc:
        reason=f'{type(exc).__name__}: {exc}'
        (a.out/'error.txt').write_text(traceback.format_exc())
    finally:
        try:
            if monitor:result=monitor.finish(reason)
            else:
                result=dict(task_id=a.task,task_success=False,reason=reason,physics_steps=0,
                            video_frames=0,status='setup_failed',independent_replay=False)
                write(a.out/'result.json',result);write(a.out/'heartbeat.json',dict(state='setup_failed',**result))
            after=hashes();write(a.out/'source-check.json',dict(before=before,after=after,source_unchanged=before==after))
        finally:
            if env:env.close()
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result and (result.get('task_success') or reason=='scene_smoke_only') else 2


if __name__=='__main__':raise SystemExit(main())
