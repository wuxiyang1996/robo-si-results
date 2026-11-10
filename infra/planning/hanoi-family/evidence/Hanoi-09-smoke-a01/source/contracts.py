"""Ten explicit task contracts and symbolic/physical planning obligations."""
from pathlib import Path
from dataclasses import asdict
import json

ROOT = Path(__file__).resolve().parents[1]
FAMILY = Path(__file__).resolve().parent
TASKS = {
    'Hanoi-01': ('dex3', 'explicit', 3, 'nominal'),
    'Hanoi-02': ('parallel', 'explicit', 3, 'nominal'),
    'Hanoi-03': ('dex3', 'latent', 3, 'nominal'),
    'Hanoi-04': ('parallel', 'latent', 3, 'nominal'),
    'Hanoi-05': ('dex3', 'latent', 3, 'grip_boundary_candidate'),
    'Hanoi-06': ('parallel', 'latent', 3, 'wrist_boundary_candidate'),
    'Hanoi-07': ('dex3', 'explicit', 4, 'nominal'),
    'Hanoi-08': ('dex3', 'explicit', 5, 'nominal'),
    'Hanoi-09': ('inspire', 'explicit', 3, 'nominal'),
    'Hanoi-10': ('inspire', 'latent', 3, 'nominal'),
}


def contract(task):
    body, disclosure, disks, profile = TASKS[task]
    return dict(schema='hanoi-tool-task/1', task_id=task, embodiment=body,
                disclosure=disclosure, disks=disks, capability_profile=profile,
                tools=['T1_tongs', 'T2_fork'], pelvis_fixed=True,
                timestep=.005, control_dt=.02, release_hold=.5, final_hold=2.,
                runtime_status='experimental_not_admitted',
                boundary_calibrated=False if 'boundary' in profile else None,
                observation_scope='privileged_physical_reference_not_agent_evaluation')


def config(task):
    from humanoid.g1_tabletop_hanoi.task_spec import TaskConfig
    c = contract(task)
    return TaskConfig(num_disks=c['disks'], max_episode_seconds=900.,
                      ring_segments=12, disk_height=.025, disk_mass=.12)


def plan(task):
    from humanoid.g1_tabletop_hanoi.task_spec import reference_moves
    c = contract(task)
    high = [dict(id='P00', goal='Inspect candidate tools and estimate effective capability',
                 guard='bounded probe observations and recorded feasibility prediction'),
            dict(id='P01', goal='Acquire a compatible tool through hand contact',
                 guard='tool lifted from rack, hand-tool force, no attachment')]
    low = [dict(id='P00.L01', high='P00', action='observe initial geometry and nominal limits'),
           dict(id='P00.L02', high='P00', action='record prediction; update after contact/lift probe'),
           dict(id='P01.L01', high='P01', action='approach tool above rack with open hand'),
           dict(id='P01.L02', high='P01', action='descend, close around handle, dwell'),
           dict(id='P01.L03', high='P01', action='lift 40 mm and test actual support/contact')]
    for i, (disk, source, target) in enumerate(reference_moves(c['disks']), 1):
        pid=f'M{i:02}'
        high.append(dict(id=pid, goal=f'Transfer {disk} from {source} to {target}',
                         disk=disk, source=source, target=target,
                         guard='top disk; real tool contact; rod cleared; legal released support'))
        for j, action in enumerate(['approach legal source top disk', 'insert/support or clamp disk',
                                   'lift completely above source rod', 'transfer above legal target',
                                   'lower hole over rod', 'withdraw tool; release for 0.5 s'], 1):
            low.append(dict(id=f'{pid}.L{j:02}', high=pid, action=action))
    high.append(dict(id='FINAL', goal='Complete tower remains independently supported for 2 s',
                     guard='all disks legally committed; no hand/tool support'))
    low.append(dict(id='FINAL.L01', high='FINAL', action='observe final released stable tower'))
    return dict(schema='hanoi-high-low-plan/1', task_id=task, high_level=high,
                low_level=low, planning_only=True,
                evidence_rule='Only actual executed action ranges establish trajectory correspondence.')


def export(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for task in TASKS:
        folder=out/task;folder.mkdir(exist_ok=True)
        for name, value in [('task.json',contract(task)),('plan.json',plan(task)),('scene-config.json',asdict(config(task)))]:
            (folder/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=FAMILY/'contracts')
    export(p.parse_args().out)
