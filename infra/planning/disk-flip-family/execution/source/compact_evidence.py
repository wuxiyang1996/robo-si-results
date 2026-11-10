"""Public replay packet: 50 Hz held references reconstruct every recorded physics-step state/control."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np,mujoco

def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def command(m,d,qref,body,tuning=None):
 tuning=tuning or {}
 if body!='S':
  for a in range(m.nu):
   j=m.actuator_trnid[a,0];name=m.joint(int(j)).name;qi=m.jnt_qposadr[j];vi=m.jnt_dofadr[j];finger='hand' in name or name.startswith(('L_','R_'));kp,kd=(tuning.get('finger_servo_kp',6.),tuning.get('finger_servo_kd',.25)) if finger else (40.,3.) if 'wrist' in name else (150.,8.);
   if tuning.get('soft_servo',False):kp,kd=(2.4,.25) if finger else (14.,1.5) if 'wrist' in name else (40.,5.) if any(k in name for k in ['shoulder','elbow']) else (150.,8.)
   if finger:
    for stage in tuning.get('finger_servo_schedule',[]):
     if round(d.time/m.opt.timestep)>=stage['start_step']:kp,kd=stage['kp'],stage['kd']
   effort=max(abs(m.actuator_ctrlrange[a]));d.ctrl[a]=np.clip(kp*(qref[qi]-d.qpos[qi])-kd*d.qvel[vi]+d.qfrc_bias[vi],-effort,effort)
 else:
  targets={'left_wheel_vel':0,'right_wheel_vel':0,'arm':sum(qref[m.jnt_qposadr[m.joint(f'joint_arm_l{i}').id]] for i in range(4))}
  for a in range(m.nu):
   n=m.actuator(a).name;v=targets[n] if n in targets else qref[m.jnt_qposadr[m.actuator_trnid[a,0]]];d.ctrl[a]=np.clip(v,*m.actuator_ctrlrange[a])

def replay(folder):
 z=np.load(folder/'trajectory-reference.npz');m=mujoco.MjModel.from_xml_path(str(folder/'scene.xml'));d=mujoco.MjData(m);initial=json.loads((folder/'initial_state.json').read_text());d.qpos[:]=initial['qpos'];d.qvel[:]=initial['qvel'];mujoco.mj_forward(m,d);meta=json.loads((folder/'trajectory-reference.json').read_text());hashes={k:hashlib.sha256() for k in ['qpos','qvel','ctrl']};step=0
 for count,(end,ref) in enumerate(zip(z['physics_step'],z['reference']),1):
  if meta['body']=='S':command(m,d,ref,meta['body'],meta.get('controller_tuning'))
  while step<int(end):
   if meta['body']!='S':command(m,d,ref,meta['body'],meta.get('controller_tuning'))
   mujoco.mj_step(m,d)
   for k in hashes:hashes[k].update(np.ascontiguousarray(getattr(d,k)).tobytes())
   step+=1
  if count%1000==0:print(json.dumps(dict(replay_commands=count,physics_steps=step,simulated_seconds=float(d.time))),flush=True)
 actual={k:h.hexdigest() for k,h in hashes.items()};result={'physics_steps':step,'all_physics_state_and_control_array_hashes_match':actual==meta['full_array_sha256'],'physics_hz':round(1/float(m.opt.timestep)),'actual_sha256':actual,'scope':'exact reconstruction from held joint references; no qpos/qvel writes after initialization'}
 result.update(reference_packet_sha256=hashlib.sha256((folder/'trajectory-reference.npz').read_bytes()).hexdigest(),reference_metadata_sha256=hashlib.sha256((folder/'trajectory-reference.json').read_bytes()).hexdigest(),scene_sha256=hashlib.sha256((folder/'scene.xml').read_bytes()).hexdigest(),initial_state_sha256=hashlib.sha256((folder/'initial_state.json').read_bytes()).hexdigest())
 if result['physics_hz']==400:result['all_400hz_state_and_control_array_hashes_match']=result['all_physics_state_and_control_array_hashes_match']
 (folder/'reference-replay-verification.json').write_text(json.dumps(result,indent=2)+'\n');assert result['all_physics_state_and_control_array_hashes_match'],result;return result

def prepare(run):
 z={k:v for k,v in np.load(run/'trajectory.npz').items()};m=mujoco.MjModel.from_xml_path(str(run/'scene.xml'));q=m.jnt_qposadr[m.joint('disk_free').id];v=m.jnt_dofadr[m.joint('disk_free').id];n=len(z['time']);period=round(.02/float(m.opt.timestep));idx=np.unique(np.r_[np.arange(period-1,n,period),n-1]);prev=0
 for end in idx:
  assert np.all(z['reference'][prev:end+1]==z['reference'][end]);prev=end+1
 np.savez_compressed(run/'trajectory-reference.npz',physics_step=idx+1,time=z['time'][idx],reference=z['reference'][idx],object_qpos=z['qpos'][idx,q:q+7],object_qvel=z['qvel'][idx,v:v+6],phase=z['phase'][idx])
 meta={'controller_tuning':json.loads((run/'plan.json').read_text()).get('controller_tuning',{}),'format':'held-reference-replay/1','physics_hz':round(1/float(m.opt.timestep)),'control_hz':50,'body':json.loads((run/'model-binding.json').read_text())['body'],'physics_steps':n,'full_array_sha256':{k:sha(z[k]) for k in ['qpos','qvel','ctrl']},'source_trajectory_npz_sha256':hashlib.sha256((run/'trajectory.npz').read_bytes()).hexdigest(),'replay':'python compact_evidence.py --replay PATH_TO_RUN','requirements':'MuJoCo 3.14.0, NumPy, same official meshes, scene.xml and initial_state.json. Remap external mesh paths when needed.','storage':'References stored once per control interval; partial final interval retained. Object states shown at control endpoints; full physics-step states/controls are deterministically reconstructed and checked by array SHA-256.'}
 (run/'trajectory-reference.json').write_text(json.dumps(meta,indent=2)+'\n');result=replay(run);print(run.name,result['all_physics_state_and_control_array_hashes_match'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',nargs='?',type=Path);p.add_argument('--replay',type=Path);a=p.parse_args();print(replay(a.replay)) if a.replay else prepare(a.run)
