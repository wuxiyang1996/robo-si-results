"""Extract unaltered video frames and a contact sheet with source-bound timing."""
import argparse
import hashlib
import json
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path);args=ap.parse_args();run=args.run
    trace=json.loads((run/'execution/trace.json').read_text())
    commands=json.loads((run/'execution/command_trace.json').read_text())
    profile=json.loads((run/'profile.json').read_text());fps=profile['controller']['video_fps']
    times=[0.];next_frame=0.
    for cmd in commands:
        if cmd['time']>=next_frame:
            times.append(cmd['time']+.02);next_frame+=1./fps
    times.append(len(commands)*.02)
    video=run/'execution/motion.mp4';reader=imageio.get_reader(video);actual_count=reader.count_frames()
    if actual_count!=len(times):raise ValueError(f'Video/state frame mapping mismatch: video={actual_count}, expected={len(times)}')
    groups=[];start=0
    while start<len(commands):
        stop=start+1
        while stop<len(commands) and trace[stop]['phase']==trace[start]['phase']:stop+=1
        if trace[start]['phase'].startswith(('push','planned_steps')):
            groups.append((trace[start]['time']+trace[stop]['time'])/2)
        start=stop
    chosen=[0.]+groups+[times[-1]]
    selected=[min(range(len(times)),key=lambda k:abs(times[k]-t)) for t in chosen]
    fig,axes=plt.subplots((len(selected)+1)//2,2,figsize=(16,2.7*((len(selected)+1)//2)),layout='constrained')
    records=[]
    for ax,index in zip(np.ravel(axes),selected):
        frame=reader.get_data(index);t=times[index];state=min(range(len(trace)),key=lambda k:abs(trace[k]['time']-t))
        ax.imshow(frame);ax.axis('off');ax.set_title(f'frame {index}; physics t={t:.2f}s; {trace[state]["phase"]}',fontsize=10)
        records.append(dict(frame_index=index,physics_time_s=t,nearest_state_index=state,phase=trace[state]['phase']))
    for ax in np.ravel(axes)[len(selected):]:ax.axis('off')
    fig.savefig(run/'independent_video_samples.png',dpi=140);plt.close(fig)
    imageio.imwrite(run/'independent_video_final.png',reader.get_data(actual_count-1));meta=reader.get_meta_data();reader.close()
    report=dict(schema='h1-p4-video-sampling/1',video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),frame_count=actual_count,
        frame_mapping_verified=True,video_fps=meta['fps'],video_size=list(meta['size']),
        frame_time_semantics='Frozen writer: initial t0, post-control state t+.02 at scheduled frame, final fresh state. Encoded display time differs slightly; physics times here are reconstructed and frame-count checked.',
        selected_frames=records,ai_visual_review='pending',human_review='pending',
        scope='Selected-frame visual consistency only. No visual inference of 1mrad limits, complete safety or trajectory continuity; numerical state audits remain authoritative.',
        artifacts=['independent_video_final.png','independent_video_samples.png'])
    (run/'independent_video_review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('frame_count','frame_mapping_verified','ai_visual_review')}))


if __name__=='__main__':main()
