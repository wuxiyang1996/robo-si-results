"""Bounded tool-acquisition and Hanoi candidate, executed through joint commands.

The candidate deliberately stops at failed guards. A symbolic plan or IK target
does not count as a physical transfer. This is a privileged feasibility expert.
"""
import math
import numpy as np
import mujoco
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .runtime import array
from humanoid.g1_tabletop_hanoi.task_spec import reference_moves


class GuardFailure(RuntimeError):pass


class Expert:
    def __init__(self,env,monitor,max_moves=None):
        self.e=env;self.m=monitor;self.names=env.names;self.q=env.target.copy();self.max_moves=max_moves
        self.model=mujoco.MjModel.from_xml_path(str(env.model_path));self.data=mujoco.MjData(self.model)
        joints=[self.model.joint(n).id for n in self.names]
        self.qa=self.model.jnt_qposadr[joints];self.da=self.model.jnt_dofadr[joints]
        self.active=np.array([i for i,n in enumerate(self.names) if n.startswith('waist_') or (n.startswith('right_') and any(x in n for x in ['shoulder','elbow','wrist']))])
        self.wrist=self.model.body('right_wrist_yaw_link').id
        self.grip=np.array([i for i,n in enumerate(self.names) if (n.startswith('right_') and ('_hand_' in n or '_parallel_' in n)) or n.startswith('R_')])
        self.holding=False;self.tool='T2_fork';self.relative=None
        self.ik_lo=env.lo.copy();self.ik_hi=env.hi.copy()
        for i,n in enumerate(self.names):
            if n.startswith('waist_'):
                self.ik_lo[i]=max(self.ik_lo[i],-.32);self.ik_hi[i]=min(self.ik_hi[i],.32)

    def set_phase(self,high,low,action):self.m.phase(high,low,action)

    def fk(self,q):
        self.data.qpos[self.qa]=q;mujoco.mj_forward(self.model,self.data)
        return self.data.xpos[self.wrist].copy(),self.data.xmat[self.wrist].reshape(3,3).copy()

    def solve(self,pos,rot):
        seed=self.q.copy();cols=self.da[self.active]
        jp=np.zeros((3,self.model.nv));jr=np.zeros_like(jp)
        def fun(x):
            q=seed.copy();q[self.active]=x;p,r=self.fk(q)
            return np.r_[p-pos,.18*Rotation.from_matrix(rot@r.T).as_rotvec(),.001*(x-seed[self.active])]
        def jac(x):
            fun(x);mujoco.mj_jacBody(self.model,self.data,jp,jr,self.wrist)
            return np.vstack([jp[:,cols],-.18*jr[:,cols],.001*np.eye(len(cols))])
        result=least_squares(fun,np.clip(seed[self.active],self.ik_lo[self.active]+1e-6,self.ik_hi[self.active]-1e-6),bounds=(self.ik_lo[self.active]+1e-6,self.ik_hi[self.active]-1e-6),max_nfev=100)
        q=seed.copy();q[self.active]=result.x;p,r=self.fk(q)
        err=float(np.linalg.norm(p-pos));angle=float(np.linalg.norm(Rotation.from_matrix(rot@r.T).as_rotvec()))
        self.m.events.append(dict(event='ik',high=self.m.high,low=self.m.low,error_m=err,error_rad=angle,target_position=pos.tolist()))
        if err>.012 or angle>.12:raise GuardFailure(f'IK unreachable: position={err:.4f} m, rotation={angle:.3f} rad')
        return q

    def hold(self,seconds):
        for _ in range(math.ceil(seconds/.02)):
            self.command(self.q)

    def command(self,q):
        if self.m.controls>=self.m.max_controls:raise GuardFailure('bounded_attempt_budget_exhausted')
        # Kinematic/gravity calculations only affect command references.
        self.fk(q);bias=self.data.qfrc_bias[self.da]
        target=q.copy()
        for i,n in enumerate(self.names):
            if any(x in n for x in ['waist','shoulder','elbow','wrist']):target[i]+=bias[i]/self.e.kp[i]
        target=np.clip(target,self.e.lo,self.e.hi)
        self.m.control(target)
        if self.m.rod_obstruction_seconds>.10:raise GuardFailure('robot_link_obstructed_by_rod')
        if self.e.status['terminated'] and not self.e.status['success']:
            raise GuardFailure('physical_task_failure: '+self.e.status['reason'])

    def move(self,pos,rot=np.eye(3),seconds=2.):
        target=self.solve(np.asarray(pos),np.asarray(rot));start=self.q.copy()
        seconds=max(seconds,float(np.max(np.abs(target-start)/self.e.velocity))*1.9)
        for k in range(1,math.ceil(seconds/.02)+1):
            t=min(1,k*.02/seconds);s=t*t*t*(10+t*(-15+6*t))
            self.q=start+s*(target-start);self.command(self.q)
        self.hold(.2)

    def fingers(self,closure,seconds=.8):
        target=self.q.copy()
        for i in self.grip:
            n=self.names[i]
            if n in self.e.metadata['mimic_followers']:continue
            lo,hi=self.e.lo[i],self.e.hi[i]
            if '_parallel_slide_' in n:target[i]=.035*(1-closure)
            elif '_hand_' in n:
                if 'thumb_0' in n:target[i]=.15*closure
                elif 'thumb_1' in n:target[i]=min(hi,.7)*closure
                elif 'thumb_2' in n:target[i]=min(hi,1.0)*closure
                elif 'index_0' in n or 'middle_0' in n:target[i]=min(hi,.9)*closure
                else:target[i]=min(hi,1.2)*closure
            else:
                endpoint=hi if abs(hi)>=abs(lo) else lo
                target[i]=endpoint*(.65 if 'thumb' in n else .7)*closure
        start=self.q.copy()
        for k in range(1,math.ceil(seconds/.02)+1):
            t=min(1,k*.02/seconds);self.q=start+(3*t*t-2*t*t*t)*(target-start);self.command(self.q)
        self.hold(.3)

    def grasp(self):
        self.set_phase('P00','P00.L01','settle and inspect physical tool geometry');self.hold(.5)
        self.set_phase('P01','P01.L01','park unused left hand above the rod workspace')
        start=self.q.copy();target=start.copy()
        for name,value in [('left_shoulder_pitch_joint',-2.),('left_shoulder_roll_joint',.5),('left_elbow_joint',1.2)]:
            target[self.names.index(name)]=value
        for k in range(1,101):
            t=k/100;self.q=start+(3*t*t-2*t*t*t)*(target-start);self.command(self.q)
        self.hold(.4)
        self.m.predictions.append(dict(stage='before_probe',tool=self.tool,feasible=None,
            rationale='Under-disk support candidate; handle acquisition and force capacity remain unverified',
            capability_truth_used=False,confidence=None))
        for attempt,backoff in enumerate([.15,.17,.13]):
            state=self.e.state()[self.tool];p=np.array(state['pos']);z0=p[2]
            if p[2]<self.e.cfg.table_height-.03:raise GuardFailure('tool fell below rack before acquisition')
            tq=np.array(state['quat']);tool_rotation=Rotation.from_quat(tq[[1,2,3,0]]).as_matrix()
            handle=p+tool_rotation@np.array([-.075,0,0])
            approach_rotation=Rotation.from_euler('y',math.pi/2).as_matrix()
            wrist=handle-approach_rotation@np.array([backoff,0,0])
            self.set_phase('P01','P01.L01',f'approach fork handle, grasp candidate {attempt+1}')
            self.fingers(0)
            # Orient above all rods first, then descend outside their XY area.
            self.move(wrist+np.array([0,0,.30]),approach_rotation)
            self.move(wrist+np.array([0,0,.10]),approach_rotation)
            self.set_phase('P01','P01.L02','descend and close hand on tool handle')
            self.move(wrist,approach_rotation,seconds=2.);self.fingers(.85 if self.e.contract['embodiment']=='parallel' else .8)
            self.set_phase('P01','P01.L03','physical 40 mm lift probe')
            self.move(wrist+np.array([0,0,.04]),approach_rotation,seconds=1.)
            state=self.e.state()[self.tool];lift=float(state['pos'][2]-z0)
            passed=bool(state['hand_contact'] and lift>.025 and state['support_forces'].get('table',0)<.05)
            self.m.events.append(dict(event='tool_lift_probe',attempt=attempt+1,lift_m=lift,
                                     hand_force_n=state['hand_force_n'],passed=passed))
            self.m.predictions.append(dict(stage='after_probe',tool=self.tool,feasible=passed,
                                          scope='tool acquisition only',lift_m=lift))
            if passed:
                link=self.e.byname['right_wrist_yaw_link'];wp=array(link.get_pos())
                wq=array(link.get_quat());wr=Rotation.from_quat(wq[[1,2,3,0]]).as_matrix()
                tq=np.array(state['quat']);tr=Rotation.from_quat(tq[[1,2,3,0]]).as_matrix()
                self.relative=(wr.T@(np.array(state['pos'])-wp),wr.T@tr)
                self.holding=True;return
            self.fingers(0);self.move(wrist+np.array([0,0,.10]),approach_rotation)
        raise GuardFailure('tool_acquisition_failed_after_three_physical_grasp_candidates')

    def tool_move(self,pos,seconds=2.):
        relative,rotation=self.relative
        wrist_rotation=rotation.T
        self.move(np.asarray(pos)-wrist_rotation@relative,wrist_rotation,seconds)
        if not self.e.state()[self.tool]['hand_contact']:raise GuardFailure('lost_tool_hand_contact')

    def run(self):
        self.grasp()
        for i,(disk,source,target) in enumerate(reference_moves(self.e.cfg.num_disks),1):
            if self.max_moves and i>self.max_moves:raise GuardFailure('diagnostic_move_prefix_complete')
            pid=f'M{i:02}';state=self.e.state()[disk];p=np.array(state['pos'])
            # Fork plate spans +/-37mm in y and passes outside the inner foot.
            tool=np.array([p[0]-.055,p[1],p[2]-.0125+.0045+.022])
            self.set_phase(pid,pid+'.L01','approach source top disk with held fork')
            self.tool_move(tool+np.array([-.18,0,.20]))
            self.tool_move(tool+np.array([-.18,0,0]))
            self.set_phase(pid,pid+'.L02','insert fork through underside clearance')
            self.tool_move(tool,2.)
            self.set_phase(pid,pid+'.L03','lift supported disk clear of source rod')
            high=self.e.cfg.pad_top+self.e.cfg.rod_height+.07
            self.tool_move(tool+np.array([0,0,high-p[2]]),2.)
            actual=self.e.state()[disk]
            if not actual['tool_chain_contact'] or actual['pos'][2]<self.e.cfg.pad_top+self.e.cfg.rod_height+.015:
                raise GuardFailure('disk_not_physically_supported_and_clear_of_rod')
            self.set_phase(pid,pid+'.L04','transfer supported disk over legal target')
            level=len(self.e.evaluator.stacks[target]);dst=np.array(self.e.cfg.slot_position(target,level))
            target_tool=np.array([dst[0]-.055,dst[1],high-.0125+.0045+.022])
            self.tool_move(target_tool,2.5)
            self.set_phase(pid,pid+'.L05','lower disk onto legal target support')
            target_tool[2]=dst[2]-.0125+.0045+.022
            self.tool_move(target_tool,2.)
            self.set_phase(pid,pid+'.L06','withdraw fork and wait for stable physical commit')
            self.tool_move(target_tool+np.array([-.18,0,0]),2.);self.hold(.8)
            if self.e.evaluator.move_count!=i:raise GuardFailure('legal_move_not_committed_after_release')
        self.set_phase('FINAL','FINAL.L01','confirm released stable tower');self.hold(2.1)
