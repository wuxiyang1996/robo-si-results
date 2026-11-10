"""Independent replay of saved extension controls and high/low segment coverage."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import mujoco

def write(p,x):
 tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();out=a.run;s=json.load(open(out/'summary.json'));plan=json.load(open(out/'plan.json'));segments=json.load(open(out/'segments.json'))
 z=np.load(out/'trajectory.npz');m=mujoco.MjModel.from_xml_path(str(out/'scene.xml'));d=mujoco.MjData(m);init=json.load(open(out/'initial_state.json'));d.qpos[:]=init['qpos'];d.qvel[:]=init['qvel'];mujoco.mj_forward(m,d)
 obj=m.body('disk').id;table=m.geom('table').id;ground=m.geom('ground').id
 mismatch=0.;violations={};peaks=dict(speed=0.,angular=0.,robot=0.,table=0.,local=0.,self_contact=0.,robot_table=0.,penetration=0.);lift=flip=False;hold=unsupported=0.;curves=[];force_caps=True
 def violation(name,i):violations.setdefault(name,{'first_step':i,'time':float(d.time)})
 for i,(ctrl,q,v) in enumerate(zip(z['ctrl'],z['qpos'],z['qvel'])):
  d.ctrl[:]=ctrl;mujoco.mj_step(m,d);mismatch=max(mismatch,float(np.max(np.abs(d.qpos-q))),float(np.max(np.abs(d.qvel-v))))
  for k in range(m.nu):
   if m.actuator_forcelimited[k] and abs(d.actuator_force[k])>max(abs(m.actuator_forcerange[k]))+1e-6:force_caps=False
   if m.actuator_ctrllimited[k] and (ctrl[k]<m.actuator_ctrlrange[k,0]-1e-6 or ctrl[k]>m.actuator_ctrlrange[k,1]+1e-6):force_caps=False
  vel=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,obj,vel,0);speed=float(np.linalg.norm(vel[3:]));angular=float(np.linalg.norm(vel[:3]));robot=tab=selfc=rt=0.;bybody={}
  for k in range(d.ncon):
   c=d.contact[k];g1,g2=c.geom;b1,b2=[int(m.geom_bodyid[g]) for g in [g1,g2]];f=np.zeros(6);mujoco.mj_contactForce(m,d,k,f);mag=float(np.linalg.norm(f[:3]));peaks['penetration']=max(peaks['penetration'],-float(c.dist))
   if obj in (b1,b2):
    other=g2 if b1==obj else g1
    if other==ground:violation('disk_ground_contact',i)
    elif other==table:tab+=mag
    else:robot+=mag;b=int(m.geom_bodyid[other]);bybody[b]=bybody.get(b,0)+mag
   elif table in (g1,g2):rt+=mag
   elif b1>0 and b2>0:selfc+=mag
  local=max(bybody.values(),default=0.)
  for name,value in [('speed',speed),('angular',angular),('robot',robot),('table',tab),('local',local),('self_contact',selfc),('robot_table',rt)]:peaks[name]=max(peaks[name],value)
  for name,value,limit in [('disk_linear_speed',speed,.12),('disk_angular_speed',angular,.65),('robot_contact_load',robot,18),('table_contact_load',tab,8),('local_damage_proxy',local,4 if s['binding']['object_profile']=='P3' else 18),('robot_table_collision',rt,20),('robot_self_collision',selfc,20)]:
   if value>limit+1e-6:violation(name,i)
  pos=d.xpos[obj];normal=d.xmat[obj].reshape(3,3)[:,2]
  if pos[2]<.835:violation('disk_dropped',i)
  lift|=bool(pos[2]>.99 and robot>.05);flip|=bool(normal[2]<-.99)
  unsupported=unsupported+m.opt.timestep if tab<.05 and robot<.05 else 0.
  if unsupported>.10:violation('uncontrolled_contact_loss',i)
  goal=bool(flip and normal[2]<-np.cos(np.deg2rad(8)) and abs(pos[0]-.7)+.1<=.35 and abs(pos[1])+.1<=.575 and np.linalg.norm(pos[:2]-[.5,0])<=.045 and tab>.05 and robot<.05 and speed<.015 and angular<.08)
  hold=hold+m.opt.timestep if goal else 0.
  if i%round(.02/float(m.opt.timestep))==0:curves.append([d.time,*pos,normal[2],robot,tab,local])
  if (i+1)%round(20/float(m.opt.timestep))==0:print(json.dumps(dict(replay_physics_steps=i+1,simulated_seconds=float(d.time),max_state_difference=mismatch,violation_count=len(violations))),flush=True)
 recorded_phases=z['phase']
 phase_labels_match=bool(all(np.all(recorded_phases[segment['record_start']:segment['record_end']]==segment['phase']) for segment in segments))
 coverage=bool(phase_labels_match and segments and segments[0]['record_start']==0 and segments[-1]['record_end']==len(z['time']) and all(a['record_end']==b['record_start'] for a,b in zip(segments,segments[1:])))
 phases={x['phase']:x for x in plan['low_level']};mapping=[dict(segment=i+1,high_level=phases[x['phase']]['high_level'],low_level=phases[x['phase']]['id'],phase=x['phase'],time_interval=[x['start_s'],x['end_s']],physics_slice=[x['record_start'],x['record_end']],completed=not x.get('interrupted',False)) for i,x in enumerate(segments)]
 source_ok=all(hashlib.sha256((out/n).read_bytes()).hexdigest()==h for n,h in s['source_hashes'].items())
 matched=bool(mismatch<1e-6 and np.allclose(z['time'],np.arange(1,len(z['time'])+1)*m.opt.timestep,atol=1e-8))
 success=bool(matched and coverage and source_ok and force_caps and not violations and hold>=2 and s['task_success'])
 report=dict(setting=s['setting'],task_success=success,replay_matches=matched,max_state_difference=mismatch,source_hashes_match=source_ok,actuator_limits_passed=force_caps,continuous_high_low_trajectory_coverage=coverage,recorded_phase_labels_match=phase_labels_match,physics_peaks=peaks,violations=violations,terminal_hold_seconds=hold,seen_lift=lift,seen_flip=flip,claim='complete physical witness' if success else 'verified failed attempt; not an infeasibility proof',joint_equalities='hand/telescope internal linkage only; no object attachment')
 write(out/'verification.json',report);write(out/'high-low-trajectory.json',mapping)
 s['independent_verification']={'report':'verification.json','replay_matches':matched,'task_success':success};write(out/'summary.json',s)
 if curves:
  import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
  arr=np.array(curves);fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True)
  for j,l in enumerate(['x','y','z']):axes[0].plot(arr[:,0],arr[:,j+1],label=l)
  axes[0].set_ylabel('Object position (m)');axes[0].legend();axes[1].plot(arr[:,0],arr[:,4]);axes[1].axhline(-np.cos(np.deg2rad(8)),color='gray',ls='--');axes[1].set_ylabel('Face normal z')
  for j,l in enumerate(['robot total','table total','local body']):axes[2].plot(arr[:,0],arr[:,j+5],label=l)
  axes[2].set_ylabel('Contact load (N)');axes[2].set_xlabel('Simulation time (s)');axes[2].legend();fig.suptitle(s['setting']+' — '+('success' if success else 'failed attempt'));fig.tight_layout();fig.savefig(out/'trajectory.png',dpi=130);plt.close(fig)
 print(json.dumps(report))
if __name__=='__main__':main()
