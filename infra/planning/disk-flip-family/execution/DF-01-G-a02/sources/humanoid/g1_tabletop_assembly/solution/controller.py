"""Measured-state IK controller; every motion goes through joint targets."""
import math

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from humanoid.g1_support_retrieval.oracle.upper_ik import UpperBodyIK
from humanoid.g1_tabletop.genesis_env import JOINT_NAMES, JOINT_LIMITS, CONTROL_DT


class EpisodeFailed(RuntimeError):
    pass


class Controller:
    def __init__(self, env, on_step=None, gravity_compensation=True):
        self.env = env
        self.ik = UpperBodyIK()
        self.q = np.asarray(env.observe()["joint_position"], dtype=float)
        self.initial_q = self.q.copy()
        self.kp = env.kp.cpu().numpy()
        self.effort = env.effort.cpu().numpy()
        self.lo, self.hi = np.asarray(JOINT_LIMITS).T
        self.index = {name: i for i, name in enumerate(JOINT_NAMES)}
        self.gravity_compensation = gravity_compensation
        self.phase = "initial"
        self.steps = 0
        self.on_step = on_step
        self.joint_feedback = {}
        self.last_observation = env.observe()
        self.events = []

    @property
    def q_ref(self):
        return self.q

    @q_ref.setter
    def q_ref(self, value):
        self.q = np.asarray(value, dtype=float).copy()

    def actual_q(self):
        return self.env.robot.get_dofs_position(self.env.dofs).cpu().numpy().astype(float)

    def hand_pose(self, side, kind="palm"):
        self.ik._set(self.env.base_position, (1, 0, 0, 0), self.actual_q())
        return (self.ik.hand_point(side, kind).copy(),
                self.ik.d.xmat[self.ik.wrist[side]].reshape(3, 3).copy())

    def object_state(self, name):
        return self.env.state()[name]

    def palms(self, measured=True):
        q = self.actual_q() if measured else self.q
        self.ik._set(self.env.base_position, (1, 0, 0, 0), q)
        return {side: self.ik.hand_point(side, "palm").copy()
                for side in ("left", "right")}

    def move(self, tasks, seconds=3., phase="reach", rate=1.):
        self.event(phase)
        self.move_hands(tasks, seconds=seconds, rate=rate)
        return True

    def event(self, phase, **metadata):
        self.phase = phase
        self.events.append(dict(phase=phase, time=self.env.physics_steps*.005, **metadata))

    def gravity_offset(self):
        self.ik._set(self.env.base_position, (1, 0, 0, 0), self.actual_q())
        self.ik.d.qvel[:] = 0
        mujoco.mj_forward(self.ik.m, self.ik.d)
        torque = self.ik.d.qfrc_bias[self.ik.dadr].copy()
        # The mounted pelvis carries the body; only waist, arms and hands need
        # compensation. The commanded references remain inside hardware limits.
        torque[:12] = 0.
        return np.clip(torque, -.8*self.effort, .8*self.effort)/self.kp

    def step(self, q=None):
        if self.env.status["terminated"]:
            if self.env.status["failed"]:
                raise EpisodeFailed(self.env.status["reason"])
            return self.last_observation
        if q is not None:
            self.q = np.asarray(q, dtype=float).copy()
        for feedback in tuple(self.joint_feedback.values()):
            feedback(self)
        target = self.q.copy()
        if self.gravity_compensation:
            target += self.gravity_offset()
        target = np.clip(target, self.lo+1e-5, self.hi-1e-5)
        obs, reward, done, info = self.env.step_targets(target)
        self.steps += 1
        self.last_observation = obs
        if self.on_step is not None:
            self.on_step(target.copy(), obs, reward, info, self.phase)
        if done and info["failed"]:
            raise EpisodeFailed(info["reason"])
        return obs

    def reach(self, tasks, rate=.8, feedback=0., iters=10):
        """Update nominal references for {side: (kind, world_pos, wrist_R)}."""
        goals = {}
        for side, (kind, pos, rot) in tasks.items():
            pos = np.asarray(pos, dtype=float)
            if feedback:
                measured, _ = self.hand_pose(side, kind)
                pos = pos + np.clip(feedback*(pos-measured), -.012, .012)
            goals[side] = (kind, pos, rot)
        solution, errors = self.ik.solve(
            self.env.base_position, (1, 0, 0, 0), self.q, goals,
            iters=iters, damping=.015, w_rot=.35, max_step=.10)
        active = self.ik.upper
        self.q[active] += np.clip(solution[active]-self.q[active],
                                  -rate*CONTROL_DT, rate*CONTROL_DT)
        return errors

    def move_hands(self, tasks, seconds=2., rate=.8, feedback=.25, settle=0.):
        starts = {side: self.hand_pose(side, task[0]) for side, task in tasks.items()}
        orientations = {}
        for side, (_, _, rot) in tasks.items():
            if rot is not None:
                orientations[side] = Slerp([0., 1.], Rotation.from_matrix(
                    np.stack([starts[side][1], np.asarray(rot)])))
        count = max(1, math.ceil(seconds/CONTROL_DT))
        errors = {}
        for i in range(count):
            fraction = (i+1)/count
            fraction = fraction**3*(10.-15.*fraction+6.*fraction**2)
            current = {}
            for side, (kind, pos, rot) in tasks.items():
                start = starts[side][0]
                current[side] = (kind, start+fraction*(np.asarray(pos)-start),
                                 orientations[side](fraction).as_matrix() if rot is not None else None)
            errors = self.reach(current, rate=rate, feedback=feedback)
            self.step()
            if self.env.status["success"]:
                return errors
        for _ in range(math.ceil(settle/CONTROL_DT)):
            errors = self.reach(tasks, rate=rate, feedback=feedback)
            self.step()
        return errors

    def move_hand(self, side, pos, rot=None, seconds=2., **kwargs):
        return self.move_hands({side: ("palm", np.asarray(pos), rot)}, seconds=seconds, **kwargs)

    def move_joints(self, target, seconds=1.):
        start = self.q.copy()
        target = np.asarray(target, dtype=float)
        count = max(1, math.ceil(seconds/CONTROL_DT))
        for i in range(count):
            fraction = (i+1)/count
            fraction = fraction**3*(10.-15.*fraction+6.*fraction**2)
            self.step(start+fraction*(target-start))

    def hold(self, seconds, tasks=None):
        for _ in range(math.ceil(seconds/CONTROL_DT)):
            if tasks:
                self.reach(tasks, feedback=.25)
            self.step()
            if self.env.status["success"]:
                break

    def ready(self):
        """Lift behind the table edge before extending the hands over it."""
        self.event("raise_hands_before_table")
        self.hold(.5)
        tasks = {side: ("palm", np.array([.03, sign*.26, 1.06]), np.eye(3))
                 for side, sign in (("left", 1.), ("right", -1.))}
        self.move_hands(tasks, seconds=4., settle=.5)
        return tasks

    def hand_preset(self, side, mode="open", seconds=.5):
        flex, distal, t1, t2 = {
            "open": (0., 0., 0., 0.),
            "squeeze": (.6, 0., -1.047, 1.),
            "press": (0., 0., -1.047, 1.),
            "pinch": (.7, .4, 0., .05),
            "hook": (1.57, 0., -1.04, 0.),
        }[mode]
        sign = -1. if side == "left" else 1.
        target = self.q.copy()
        for finger in ("index", "middle"):
            target[self.index[f"{side}_hand_{finger}_0_joint"]] = sign*flex
            target[self.index[f"{side}_hand_{finger}_1_joint"]] = sign*distal
        target[self.index[f"{side}_hand_thumb_0_joint"]] = 1.04 if mode == "hook" else 0.
        target[self.index[f"{side}_hand_thumb_1_joint"]] = sign*t1
        target[self.index[f"{side}_hand_thumb_2_joint"]] = -sign*t2
        target = np.clip(target, self.lo, self.hi)
        if seconds:
            self.move_joints(target, seconds)
        else:
            self.q = target

    def contacts(self, name):
        entity = self.env.objects[name]
        raw = entity.get_contacts(with_entity=self.env.robot)
        ids = {link.idx: link.name for link in self.env.robot.links}
        arrays = {key: value.cpu().numpy() for key, value in raw.items()}
        rows = []
        for i in range(len(arrays["link_a"])):
            for suffix in ("a", "b"):
                body = ids.get(int(arrays[f"link_{suffix}"][i]))
                if body:
                    rows.append(dict(link=body, position=arrays["position"][i].tolist(),
                                     force=arrays[f"force_{suffix}"][i].tolist()))
        return rows
