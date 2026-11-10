"""Genesis scene with dynamic hand mappings and audited tool-mediated contacts."""
import json
import math
from pathlib import Path
import numpy as np
import torch
import genesis as gs
from .contracts import contract, config
from .assets import build
from humanoid.g1_tabletop_hanoi.task_spec import Evaluator


def array(v):return v.detach().cpu().numpy() if hasattr(v,'detach') else np.asarray(v)


class ToolEvaluator(Evaluator):
    """Reuse legal Hanoi rules; manipulation evidence may traverse a held tool.

    Raw observations retain direct and mediated contact separately. Any tool
    contact prevents release, including a tool not currently held by a robot.
    """
    def _read_states(self,states):
        adapted={name:dict(value) for name,value in states.items()}
        for name in self.cfg.object_names:
            adapted[name]['hand_contact']=bool(states[name]['hand_contact'] or states[name].get('tool_chain_contact'))
            adapted[name]['robot_contact']=bool(states[name]['robot_contact'] or states[name].get('any_tool_contact'))
        return super()._read_states(adapted)


class Environment:
    def __init__(self,task,out,backend='gpu',seed=0):
        self.contract=contract(task);self.cfg=config(task);self.out=Path(out)
        self.model_path,self.metadata=build(task,self.out/'assets')
        gs.init(backend=gs.gpu if backend=='gpu' else gs.cpu,precision='64',
                seed=seed,logging_level='warning',use_deterministic_algorithms=True)
        self.scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.005,substeps=1),
            rigid_options=gs.options.RigidOptions(enable_self_collision=True,enable_neutral_collision=True,
                enable_torsional_friction=True,friction_cone=gs.friction_cone.elliptic,impratio=100.,max_collision_pairs=2048),
            show_viewer=False)
        self.entity=self.scene.add_entity(gs.morphs.MJCF(file=str(self.model_path)))
        self.camera=self.scene.add_camera(res=(800,600),pos=(1.5,-1.6,1.7),lookat=(.35,0,.82),fov=47,GUI=False)
        self.scene.build()
        self.names=self.metadata['robot_joints']
        self.dofs=[self.entity.get_joint(n).dofs_idx_local[0] for n in self.names]
        limits=self.metadata['limits']
        def vector(key):return np.array([limits[n][key] for n in self.names])
        self.lo,self.hi,self.effort,self.kp,self.kd,self.velocity=[vector(x) for x in ['lower','upper','effort','kp','kd','velocity']]
        for name in self.metadata['mimic_followers']:
            i=self.names.index(name);self.kp[i]=self.kd[i]=self.effort[i]=0
        q=np.clip(np.zeros(len(self.names)),self.lo,self.hi)
        values=dict(left_hip_pitch_joint=-.10,right_hip_pitch_joint=-.10,
                    left_knee_joint=.30,right_knee_joint=.30,left_ankle_pitch_joint=-.20,right_ankle_pitch_joint=-.20,
                    left_shoulder_pitch_joint=-1.1,right_shoulder_pitch_joint=-1.1,
                    left_shoulder_roll_joint=.4,right_shoulder_roll_joint=-.4,
                    left_elbow_joint=.8,right_elbow_joint=.8)
        for n,v in values.items():q[self.names.index(n)]=v
        for i,n in enumerate(self.names):
            if '_parallel_slide_' in n:q[i]=.035
        self.entity.set_dofs_position(q,self.dofs,zero_velocity=True)
        self.entity.set_dofs_kp(np.zeros(len(q)),self.dofs);self.entity.set_dofs_kv(np.zeros(len(q)),self.dofs)
        self.entity.set_dofs_force_range(-self.effort,self.effort,self.dofs)
        self.links={l.idx:l.name for l in self.entity.links}
        self.byname={l.name:l for l in self.entity.links}
        self.measured=list(self.cfg.object_names)+['T1_tongs','T2_fork']
        self.indices=[self.byname[n].idx for n in self.measured]
        self.robot_links={i for i,n in self.links.items() if not n.startswith(('disk_','T1_','T2_','pad_','rod_')) and n not in ['world','ground','table']}
        self.hand_links={i for i,n in self.links.items() if '_hand_' in n or '_parallel_' in n or n.startswith(('L_','R_')) or 'wrist_yaw_link' in n}
        self.q0=q.copy();self.target=q.copy();self.steps=0;self.last_tau=np.zeros_like(q)
        self.evaluator=ToolEvaluator(self.cfg);self.status=self.evaluator.status()
        self.last_contacts=[];self.observer=None;self.violations=[]
        self.model_info=dict(backend=backend,seed=seed,precision=64,physics_dt=.005,control_dt=.02,
                             scene_sha256=self.metadata['scene_sha256'],hand_joints=len(q),
                             self_collision=True,tool_attachments=False,physics='Genesis')

    def owner(self,index):
        name=self.links[index]
        if name.startswith('T1_'):return 'T1_tongs'
        if name.startswith('T2_'):return 'T2_fork'
        return name

    def state(self):
        solver=self.scene.rigid_solver
        poses={k:array(getattr(solver,method)(self.indices,**kw)) for k,method,kw in [
            ('pos','get_links_pos',{'relative':True}),('quat','get_links_quat',{'relative':True}),
            ('linear_velocity','get_links_vel',{'relative':True}),('angular_velocity','get_links_ang',{})]}
        contacts=self.entity.get_contacts()
        la,lb,fa=[array(contacts[k]) for k in ['link_a','link_b','force_a']]
        held=set();self.last_contacts=[]
        for a,b,f in zip(la,lb,fa):
            a,b=int(a),int(b);oa,ob=self.owner(a),self.owner(b);norm=float(np.linalg.norm(f))
            self.last_contacts.append(dict(a=self.links[a],b=self.links[b],owner_a=oa,owner_b=ob,force_a=f.tolist()))
            if norm>.05:
                if a in self.hand_links and ob.startswith(('T1_','T2_')):held.add(ob)
                if b in self.hand_links and oa.startswith(('T1_','T2_')):held.add(oa)
        result={}
        for i,name in enumerate(self.measured):
            robot_force=hand_force=tool_force=0.;support={};chain=[]
            for a,b,f in zip(la,lb,fa):
                a,b=int(a),int(b);oa,ob=self.owner(a),self.owner(b)
                if oa==name and ob!=name:other,force,owner=b,f,ob
                elif ob==name and oa!=name:other,force,owner=a,-f,oa
                else:continue
                norm=float(np.linalg.norm(force))
                if other in self.robot_links:
                    robot_force+=norm
                    if other in self.hand_links:hand_force+=norm
                else:support[owner]=support.get(owner,0.)+float(force[2])
                if owner.startswith(('T1_','T2_')):
                    tool_force+=norm
                    if owner in held and norm>.05:chain.append(owner)
            result[name]={k:poses[k][i].tolist() for k in poses}
            result[name].update(hand_contact=bool(hand_force>.05),robot_contact=bool(robot_force>.05),
                                hand_force_n=hand_force,robot_force_n=robot_force,
                                tool_chain_contact=bool(chain),held_tools=sorted(set(chain)),
                                any_tool_contact=bool(tool_force>.05),support_forces={k:max(0.,v) for k,v in support.items()})
        return result

    def install_guards(self):
        def deny(name):
            def f(*a,**k):
                self.violations.append(dict(step=self.steps,method=name));raise RuntimeError('Forbidden runtime state write: '+name)
            return f
        for obj,names in [(self.entity,['set_pos','set_quat','set_dofs_position','set_dofs_velocity','set_qpos','set_mass','set_friction','set_dofs_kp','set_dofs_kv','set_dofs_force_range']),
                          (self.scene,['reset','set_state','add_entity']),
                          (self.scene.rigid_solver,['set_state','add_weld_constraint','delete_weld_constraint'])]:
            for name in names:
                if hasattr(obj,name):setattr(obj,name,deny(name))

    def step(self,target):
        q=np.asarray(target,dtype=float)
        if q.shape!=self.target.shape or not np.isfinite(q).all():raise ValueError('Invalid target')
        if (q<self.lo-1e-8).any() or (q>self.hi+1e-8).any():raise ValueError('Target outside joint limits')
        if self.status['terminated']:raise RuntimeError('Task terminated: '+self.status['reason'])
        self.target+=np.clip(q-self.target,-self.velocity*.02,self.velocity*.02)
        for _ in range(4):
            actual=array(self.entity.get_dofs_position(self.dofs));vel=array(self.entity.get_dofs_velocity(self.dofs))
            self.last_tau=np.clip(self.kp*(self.target-actual)-self.kd*vel,-self.effort,self.effort)
            self.entity.control_dofs_force(self.last_tau,self.dofs);self.scene.step();self.steps+=1
            state=self.state();self.status=self.evaluator.update(state,.005)
            if self.observer:self.observer(state)
            if self.status['terminated']:break
        return state

    def render(self):return self.camera.render()[0]
    def close(self):self.scene.destroy()
