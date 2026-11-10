"""Strict joint-reference boundary; actions cannot carry simulation state or model edits."""
import math
import numpy as np
import mujoco
class ActionRejected(ValueError):pass
class JointReferenceInterface:
 def __init__(self,model,initial_reference,body):
  self.model=model;self.body=body;self.reference=np.asarray(initial_reference,dtype=float).copy();self.joints={}
  for a in range(model.nu):
   if model.actuator_trntype[a]==mujoco.mjtTrn.mjTRN_JOINT:
    j=int(model.actuator_trnid[a,0]);self.joints[model.joint(j).name]=j
  if body=='S':
   for i in range(4):
    name=f'joint_arm_l{i}';self.joints[name]=model.joint(name).id
 def encode(self,reference):
  return {'type':'joint_reference','targets':{n:float(reference[self.model.jnt_qposadr[j]]) for n,j in self.joints.items()}}
 def accept(self,action,dt=.02):
  if not isinstance(action,dict) or set(action)!={'type','targets'} or action['type']!='joint_reference':raise ActionRejected('Only joint_reference targets are accepted')
  targets=action['targets']
  if not isinstance(targets,dict) or set(targets)!=set(self.joints):raise ActionRejected('Targets must contain exactly the declared actuated joints')
  candidate=self.reference.copy()
  for name,j in self.joints.items():
   value=targets[name]
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ActionRejected('Joint target must be a finite number')
   qi=self.model.jnt_qposadr[j]
   if self.model.jnt_limited[j] and not self.model.jnt_range[j,0]-1e-9<=value<=self.model.jnt_range[j,1]+1e-9:raise ActionRejected('Joint limit exceeded')
   rate=.05 if self.model.jnt_type[j]==mujoco.mjtJoint.mjJNT_SLIDE else .5
   if abs(value-self.reference[qi])>rate*dt+1e-8:raise ActionRejected('Reference slew limit exceeded')
   candidate[qi]=value
  # Commit only after every field passes; rejected actions have no partial effects.
  self.reference=candidate
  return candidate.copy()
