"""Bounded Stretch 4 servo adapter; only motors advance the free-root body."""
import math
import numpy as np
import torch
from . import stretch4 as M

class StretchDriver:
 def __init__(self,robot,device):
  self.robot=robot;self.device=device;self.names=M.POSITION+M.WHEELS
  self.dofs={n:robot.get_joint(n).dofs_idx_local[0] for n in self.names+M.ARMS[1:]}
  for n,v in M.PARAMS.items():
   robot.set_dofs_kp([v['kp']],[self.dofs[n]]);robot.set_dofs_kv([v['kv']],[self.dofs[n]])
   robot.set_dofs_force_range([-v['force']],[v['force']],[self.dofs[n]])
  for n in M.ARMS[1:]:
   robot.set_dofs_kp([0.],[self.dofs[n]]);robot.set_dofs_kv([0.],[self.dofs[n]]);robot.set_dofs_force_range([0.],[0.],[self.dofs[n]])
  self.target=robot.get_dofs_position([self.dofs[n] for n in M.POSITION])[0].detach().cpu().numpy().copy()
  self.last={}
 def apply(self,goal=None,twist=(0,0,0),dt=.02):
  goal=self.target.copy() if goal is None else np.asarray(goal,dtype=float)
  if goal.shape!=(len(M.POSITION),) or not np.isfinite(goal).all() or not np.isfinite(twist).all():raise ValueError('invalid Stretch command')
  bounds=np.array([M.PARAMS[n]['range'] for n in M.POSITION]);goal=goal.clip(bounds[:,0],bounds[:,1])
  rate=np.array([M.PARAMS[n]['velocity'] for n in M.POSITION])*dt
  self.target+=np.clip(goal-self.target,-rate,rate)
  vx,vy,w=np.asarray(twist).clip([-.2,-.2,-.4],[.2,.2,.4])
  wheels=np.array([(math.cos(a)*vx+math.sin(a)*vy+.174*w)/M.WHEEL_RADIUS for a in [2*math.pi/3,-2*math.pi/3,0]]).clip(-6,6)
  self.robot.control_dofs_position(torch.as_tensor(self.target[None],device=self.device,dtype=torch.float32),[self.dofs[n] for n in M.POSITION])
  self.robot.control_dofs_velocity(torch.as_tensor(wheels[None],device=self.device,dtype=torch.float32),[self.dofs[n] for n in M.WHEELS])
  self.last=dict(position_targets=self.target.tolist(),wheel_velocity_targets=wheels.tolist(),body_twist=[float(vx),float(vy),float(w)])
  return self.last
