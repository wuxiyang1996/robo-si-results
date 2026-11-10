"""Support retrieval in one Genesis episode: carry the folding stool to the cabinet,
set it down, climb onto it, and retrieve the high-shelf box. The relay route places the box
on the 0.90 m board, descends empty-handed, picks the box up again, and delivers it to the goal.

    python -m humanoid.g1_support_retrieval.oracle.stool_chain --carry 1 --walk-mode planned --effort-caps physical --self-collision 0 --relay 1 --relay-dy .27 --relay-waist .35 --relay-standoff .4 --hand-position-margin .04

Expert oracle (reads the simulator state). One scene, no resets; the only pose writes are the
initial placement of the robot behind the stool and of the stool. Two actuation regimes, as a
real G1 low-level controller allows (kp/kd are per-command parameters there):
  * stiff whole-body phases (stool lift and set-down, standing up): the verified stool_carry
    controller - leg PD kp 3000 / kd 40 on IK references; stepping onto and off the stool and
    standing on it: the step_up contact QP (leg torques);
  * loaded stool walking: smooth footfall references and measured-state contact QP;
    walking after the relay pickup: Agile through the task's own env.step.
Every run records motion.mp4 and a result.json, success or not.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
SOL = HERE.parent / "solution"
for sub in ("underhand_lift", "stool_carry", "carry_climb_retrieve"):
    sys.path.insert(0, str(SOL / sub))
sys.path.insert(0, str(HERE.parents[2]))
from hand_model import UnderhandPlanner, fingers_down, SIDES  # noqa: E402
from phases import Phase, Hand, Hold, StableHold, Attach, Detach, Carry, SetServo, CheckGrip, StandUp, Engage  # noqa: E402
from run_underhand import contact_summary, smooth  # noqa: E402
from run_stool import Stool, StoolContext, Settled, HandsTo, SlideOut, SIGN, STOOL_DIR  # noqa: E402
from humanoid.g1_support_retrieval import task_spec as T  # noqa: E402
import mujoco  # noqa: E402
from step_on import StepOn, FrameWriter  # noqa: E402
from humanoid.g1_support_retrieval.solution.step_up.video import VideoWriter, recording_directory  # noqa: E402
from humanoid.g1_support_retrieval.oracle.chain_checkpoint import (  # noqa: E402
    load_chain_checkpoint, save_chain_checkpoint, sync_planner_model, restore_on_stool_continuation,
)
from humanoid.g1_support_retrieval.oracle.stool_walk import walk_planned as planned_walk  # noqa: E402

G = 9.81
STAND = 0.72                      # Agile's standing pelvis height
STAGES = ("lift", "standup", "walk", "setdown", "climb", "retrieve", "stepdown", "goal")
# The Agile policy's own standing legs (JOINT_NAMES order) with the stool-carry arms, measured
# standing 3 s: pelvis 0.716 m, pitched 0.23 rad forward, 7 cm behind the ankles (agile probe)
AGILE_LEGS = np.array([-0.82, 0.0279, -0.0747, 0.8962, -0.3082, -0.0786,
                       -0.8169, -0.0285, 0.0833, 0.9104, -0.3258, 0.0772])


def balanced_arm_reference(planner, start, upper, seconds=6.0, self_collision=True):
    """Fold the arms/waist while preserving the measured feet and body COM.

    The previous fixed-leg interpolation moved the COM 57 mm backwards after
    setdown, outside the heels. Pelvis translation and both legs must change
    with the upper body, even though neither foot takes a step.
    """
    from humanoid.g1_support_retrieval.oracle.stool_walk import fixed_root_leg_ik

    p, q = planner, np.array(start, dtype=float).copy()
    p.forward(q)
    feet = p.d.xpos[p.feet].copy()
    rotations = np.array([Rotation.from_matrix(p.d.xmat[b].reshape(3, 3)).as_rotvec()
                          for b in p.feet])
    com = p.d.subtree_com[1, :2].copy()
    root_quat = q[3:7].copy()
    root_quat /= np.linalg.norm(root_quat)
    poses, peak_effort, inactive_self_penetration = [], 0.0, 0.0
    for u in np.linspace(0.0, 1.0, 121):
        blend = u ** 3 * (10.0 - 15.0 * u + 6.0 * u * u)
        seed = q.copy()
        seed[p.qids[12:]] = start[p.qids[12:]] + (upper - start[p.qids[12:]]) * blend
        q = fixed_root_leg_ik(p, seed, feet, com, start[2], rotations, root_quat, margin=0.02)
        foot_rotation_error = max(np.linalg.norm((Rotation.from_rotvec(rotations[i]).inv()
                                  * Rotation.from_matrix(p.d.xmat[b].reshape(3, 3))).as_rotvec())
                                  for i, b in enumerate(p.feet))
        if foot_rotation_error > 0.025:
            raise ValueError(f"arm fold foot orientation error {foot_rotation_error:.4f} rad")
        tau = p.force_check(q, np.zeros(p.m.nv), np.zeros(p.m.nv), [0, 1],
                            reserve=1.0, box_support=False)
        peak_effort = max(peak_effort, float(np.max(np.abs(tau) / p.params["effort"])))
        for contact in p.d.contact:
            if contact.dist < -0.002:
                bodies = p.m.geom_bodyid[np.asarray(contact.geom)]
                internal = all(p.m.body_rootid[b] == 1 for b in bodies)
                if internal and not self_collision:
                    # Match the episode's explicit simulator option. These
                    # adjacent shoulder meshes already overlap in the measured
                    # start pose; environment contacts are always checked.
                    inactive_self_penetration = max(inactive_self_penetration, -float(contact.dist))
                    continue
                names = [p.m.body(p.m.geom_bodyid[g]).name for g in contact.geom]
                raise ValueError(f"arm fold u={u:.4f}: penetration {contact.dist:.4f} m {names}")
        poses.append(q.copy())
    poses = np.asarray(poses)
    dt = seconds / (len(poses) - 1)
    velocity = np.diff(poses[:, p.qids], axis=0) / dt
    acceleration = np.diff(velocity, axis=0) / dt
    scale = max(1.0, float(np.max(np.abs(velocity))) / 0.5,
                float(np.sqrt(np.max(np.abs(acceleration)) / 2.0)),
                float(np.max(np.linalg.norm(np.diff(poses[:, :3], axis=0), axis=1))) / dt / 0.025)
    times = np.linspace(0.0, seconds * scale, len(poses))
    return poses, times, dict(feet=feet.tolist(), com=com.tolist(),
                              max_static_effort_ratio=peak_effort,
                              self_collision_enabled=bool(self_collision),
                              inactive_self_penetration_m=inactive_self_penetration,
                              duration_seconds=float(times[-1]))


def on_stool_shoulder_reference(planner, start, seconds=3.0):
    """Prepare the original retrieval IK seed while keeping both feet and COM.

    The retracted climbing shoulders avoid the cabinet upright, but put the
    incremental arm IK in a different branch. Restore the old nominal motor
    target only after both feet support on the stool. This is a planned motion,
    not a state write; the caller executes and checks the physical transition.
    """
    from humanoid.g1_support_retrieval.oracle.stool_walk import fixed_root_leg_ik
    from humanoid.g1_support_retrieval.oracle.entry_reference import retime_entry_reference

    p = planner
    start = np.asarray(start, dtype=float).copy()
    p.forward(start)
    feet = p.d.xpos[p.feet].copy()
    rotations = np.array([Rotation.from_matrix(p.d.xmat[b].reshape(3, 3)).as_rotvec()
                          for b in p.feet])
    com = p.d.subtree_com[1, :2].copy()
    root_quat = start[3:7].copy()
    upper_start = start[p.qids[12:]].copy()
    upper_goal = upper_start.copy()
    shoulders = [T.JOINT_NAMES.index(f"{side}_shoulder_pitch_joint") for side in SIDES]
    shoulder_rolls = [T.JOINT_NAMES.index(f"{side}_shoulder_roll_joint") for side in SIDES]
    for index in shoulders:
        upper_goal[index - 12] = -0.15
    for index, goal in zip(shoulder_rolls, (0.5, -0.5)):
        upper_goal[index - 12] = goal
    poses, previous = [start.copy()], start.copy()
    for u in np.linspace(0.0, 1.0, 101)[1:]:
        blend = u ** 3 * (10.0 - 15.0 * u + 6.0 * u * u)
        seed = previous.copy()
        seed[p.qids[12:]] = upper_start + (upper_goal - upper_start) * blend
        previous = fixed_root_leg_ik(p, seed, feet, com, start[2], rotations,
                                     root_quat, margin=0.02)
        poses.append(previous.copy())
    qs, times, velocities, accelerations, timing = retime_entry_reference(
        p.m, p.vids, poses, seconds, dt=T.CONTROL_DT)
    return qs, times, velocities, accelerations, dict(
        **timing, feet=feet.tolist(), foot_rotations=rotations.tolist(),
        com=com.tolist(), shoulder_joint_indices=shoulders,
        shoulder_start_rad=start[p.qids[shoulders]].tolist(),
        shoulder_goal_rad=[-0.15, -0.15],
        shoulder_roll_joint_indices=shoulder_rolls,
        shoulder_roll_start_rad=start[p.qids[shoulder_rolls]].tolist(),
        shoulder_roll_goal_rad=[0.5, -0.5])


class Reattach(Phase):
    """After a walk under another controller: take the stool reference from the measured
    stool pose and each hand's offset from its measured MCP point (hands stay attached)."""

    name = "reattach"

    def start(self, ctx):
        pos, R = ctx.box.pos.copy(), ctx.box.R.copy()
        ctx.box_des = (pos, R)
        ctx.box_mode = "desired"
        ctx.planner.forward(ctx.measured)
        for i, side in enumerate(SIDES):
            h = ctx.hands[side]
            h.rel_mcp = R.T @ (ctx.mcp_meas[i] - pos)
            h.rel_rot = R.T @ ctx.planner.d.xmat[ctx.planner.hands[i]].reshape(3, 3)
            h.attached = True
            # A fresh physical attachment is the fixed reference for bounded
            # setdown force corrections; never rebase it onto a moving target.
            h.setdown_servo_anchor = h.rel_mcp.copy()
            h.setdown_servo_debug = None
        ctx.track = np.zeros((2, 3))

    def step(self, ctx, age):
        return "done"


class ClearStoolHands(Phase):
    """Unload the rail before attempting a sideways withdrawal."""

    name = "clear_hands"

    def start(self, ctx):
        # The loaded grip's integral correction must not become a free-hand
        # height offset. Rebase on measured hands; the normal joint-reference
        # rate limits still apply to every subsequent command.
        ctx.track[:] = 0.0
        ctx.metrics["release_start"] = dict(q=ctx.measured.tolist(), stool=ctx.box.pos.tolist(),
                                             stool_rotation=ctx.box.R.tolist())
        self.z0, self.thumb0, self.extra, self.mcp0, self.normal, self.clear_z = {}, {}, {}, {}, {}, {}
        for i, side in enumerate(SIDES):
            h = ctx.hands[side]
            h.attached, h.servo = False, None
            h.mcp = ctx.mcp_meas[i].copy()
            self.mcp0[side] = h.mcp.copy()
            self.normal[side] = ctx.face_normal(side).copy()
            h.z = self.z0[side] = float(h.mcp[2])
            # The stool has reached the floor. A free hand must not chase a
            # rising rail if incidental contact tilts it during withdrawal.
            grounded_rail_z = float(ctx.box.rail_bottom + ctx.box.size[2] / 2)
            self.clear_z[side] = min(ctx.box.edge_z(side), grounded_rail_z) - self.kw["below"]
            h.rot = Rotation.from_matrix(ctx.planner.d.xmat[ctx.planner.hands[i]].reshape(3, 3)).as_rotvec()
            self.thumb0[side], self.extra[side] = h.q.get("thumb1", 0.0), 0.0
        self.next_log = 0.0

    def step(self, ctx, age):
        duration = self.kw.get("seconds", 3.0)
        # Clear the crossed legs as well as the rail before lowering. Mesh
        # sweeps of the measured lowered pose leave only ~0 mm beneath the
        # left fingers after a 12 mm lead. The wider withdrawal gives both
        # hands a height band that tolerates the measured tracking deflection.
        lead_seconds = 4.0
        lead = smooth(age / lead_seconds)
        u = smooth((age - lead_seconds) / duration)
        measurements = {}
        clear = True
        for i, side in enumerate(SIDES):
            h = ctx.hands[side]
            _, gap = ctx.finger_metrics(side)
            force = sum(float(np.linalg.norm(ctx.contacts["groups"].get(f"{side}_{part}", np.zeros(3))))
                        for part in ("finger", "thumb", "palm"))
            tracking = abs(float(ctx.mcp_meas[i, 2]) - h.z)
            tracking_xy = float(np.linalg.norm(ctx.mcp_meas[i, :2] - h.mcp[:2]))
            # Only add a small downward search after the measured hand has
            # caught up. Do not turn an IK lag into a growing motion command.
            if age > lead_seconds + duration + 0.5 and tracking < 0.004 and tracking_xy < 0.008 and gap < 0.005:
                self.extra[side] = min(0.003, self.extra[side] + 0.001 * T.CONTROL_DT)
            goal = self.clear_z[side] - self.extra[side]
            h.mcp = self.mcp0[side] + self.normal[side] * {"left": 0.036, "right": 0.024}[side] * lead
            lead_z = self.z0[side] - 0.001 * lead
            h.z = lead_z + (goal - lead_z) * u
            # Keep the thumb above the seat until the whole hand is outside.
            # Rotating thumb1 toward -0.5 here sweeps it through the seat and
            # clamps the grounded stool against the fingers underneath.
            h.q["thumb1"] = self.thumb0[side]
            clear &= gap >= 0.005 and force < 1.0 and tracking < 0.004 and tracking_xy < 0.008
            measurements[side] = dict(mcp=ctx.mcp_meas[i].tolist(), target_z=h.z,
                                      target_xy=h.mcp[:2].tolist(), tracking_xy=tracking_xy,
                                      tracking_z=tracking, fixed_clear_z=self.clear_z[side],
                                      track=ctx.track[i].tolist(), gap=gap, force=force,
                                      support=ctx.support(side), extra=self.extra[side], fingers=dict(h.q),
                                      actual_fingers={f"{part}_{joint}": float(ctx.measured[ctx.planner.qadr(
                                          f"{side}_hand_{part}_{joint}_joint")])
                                          for part, count in (("index", 2), ("middle", 2), ("thumb", 3))
                                          for joint in range(count)})
        grounded = abs(ctx.box.bottom()) <= 0.01 and ctx.box.tilt_deg() < 3.0 and np.linalg.norm(ctx.box.vel) < 0.02
        if age >= self.next_log:
            self.next_log = age + 0.2 - 1e-6
            ctx.metrics.setdefault("release_trace", []).append(dict(
                age=round(age, 3), stool=ctx.box.pos.tolist(), tilt=ctx.box.tilt_deg(),
                stool_rotation=ctx.box.R.tolist(), robot_q=ctx.measured.tolist(),
                reference_q=ctx.qref.tolist(), feet=ctx.feet_meas.tolist(),
                hands=measurements, groups={k: v.tolist() for k, v in ctx.contacts["groups"].items()},
                links=ctx.contacts["links"]))
        if self.held(age >= lead_seconds + duration and clear and grounded, 0.3):
            return "done"
        if age > 14.0:
            return "fail:hands_not_clear_of_rail"


class WeightedCarry(Carry):
    """Carry with the planner's pelvis-pitch regularisation ramped from w[0] to w[1] (the
    whole-body IK otherwise stands up bent at the hips, a pose the walking policy would
    straighten, swinging the stool into the torso). With `mcp` = (x, z): the stool goes so that
    the mid point of both hands' control points ends at that x and height (world)."""

    name = "carry"

    def start(self, ctx):
        if "joint_step_limit" in self.kw:
            ctx.planner.reach_joint_step_limit = self.kw["joint_step_limit"]
        if "mcp" in self.kw:
            ref = ctx.box_des if ctx.box_des is not None else ctx.box_reference()
            mid = np.mean([ref[0] + ref[1] @ ctx.hands[sd].rel_mcp for sd in SIDES], axis=0)
            x, z = self.kw["mcp"]
            self.kw["offset"] = [x - mid[0], 0.0, z - mid[2]]
        self.com0 = ctx.com_cmd.copy()
        super().start(ctx)

    def step(self, ctx, age):
        w0, w1 = self.kw.get("w", (0.2, 0.2))
        u = smooth(age / self.kw.get("seconds", 5.0))
        ctx.planner.root_rotation_weights = np.array([50.0, w0 + (w1 - w0) * u, 50.0])
        if "com" in self.kw:          # centre-of-mass target (robot + carried load) relative to nominal
            ctx.com_cmd = self.com0 + (ctx.com_nominal + np.asarray(self.kw["com"]) - self.com0) * u
        return super().step(ctx, age)


class Upright(Phase):
    """Straighten up with the stool held: ramp the IK's pelvis-pitch bound and waist pitch/roll
    bounds down (the shared reach allows the pelvis 0.85 rad and the waist 0.5 rad forward, and
    with the hands 0.33 m ahead it bent at the waist and sat the pelvis back to keep the centre
    of mass: a tall, bent posture that toppled sideways in the first footfall, stepwalk-v1..v8)."""

    name = "upright"

    def start(self, ctx):
        pl = ctx.planner
        if not hasattr(pl, "_pre_upright_constraints"):
            pl._pre_upright_constraints = dict(
                root_rotation_upper=np.array(getattr(pl, "root_rotation_upper", [0.3, 0.85, 0.3]), float),
                root_rotation_lower=np.array(getattr(pl, "root_rotation_lower", [-0.3, -0.2, -0.3]), float),
                waist_lower=np.array(getattr(pl, "waist_lower", -0.2), float),
                waist_upper=np.array(getattr(pl, "waist_upper", 0.5), float),
                waist_yaw_range=pl.m.jnt_range[pl.m.joint("waist_yaw_joint").id].copy())
        self.up0 = np.array(getattr(pl, "root_rotation_upper", [0.3, 0.85, 0.3]), float)
        self.lo0 = np.array(getattr(pl, "root_rotation_lower", [-0.3, -0.2, -0.3]), float)
        self.w_lo0 = np.array(np.broadcast_to(getattr(pl, "waist_lower", -0.2), 2), float)
        self.w_hi0 = np.array(np.broadcast_to(getattr(pl, "waist_upper", 0.5), 2), float)

    def step(self, ctx, age):
        pl = ctx.planner
        u = smooth(age / self.kw.get("seconds", 6.0))
        pitch, waist = self.kw.get("pelvis_pitch", 0.2), self.kw.get("waist_pitch", 0.1)
        pl.root_rotation_upper = [self.up0[0], self.up0[1] + (pitch - self.up0[1]) * u, self.up0[2]]
        pelvis_roll = self.kw.get("pelvis_roll")
        if pelvis_roll is not None:
            pl.root_rotation_upper[0] = self.up0[0] + (pelvis_roll - self.up0[0]) * u
            pl.root_rotation_lower = self.lo0.copy()
            pl.root_rotation_lower[0] += (-pelvis_roll - self.lo0[0]) * u
        roll = self.kw.get("waist_roll", 0.05)
        pl.waist_lower = np.array([self.w_lo0[0] + (-roll - self.w_lo0[0]) * u, self.w_lo0[1] + (-waist - self.w_lo0[1]) * u])
        pl.waist_upper = np.array([self.w_hi0[0] + (roll - self.w_hi0[0]) * u, self.w_hi0[1] + (waist - self.w_hi0[1]) * u])
        yaw_id = pl.m.joint("waist_yaw_joint").id
        if not hasattr(self, "yaw0"):
            self.yaw0 = pl.m.jnt_range[yaw_id].copy()
        yaw = self.kw.get("waist_yaw", 0.05)
        pl.m.jnt_range[yaw_id] = [self.yaw0[0] + (-yaw - self.yaw0[0]) * u, self.yaw0[1] + (yaw - self.yaw0[1]) * u]
        level = True
        if pelvis_roll is not None:
            measured_roll = Rotation.from_quat(ctx.measured[[4, 5, 6, 3]]).as_euler("xyz")[0]
            level = self.held(u >= 1.0 and abs(measured_roll) < pelvis_roll + np.radians(1.0), 0.5)
        if age > self.kw.get("seconds", 6.0) + 0.5:
            if level:
                return "done"
            if age > self.kw.get("seconds", 6.0) + 4.0:
                return "fail:pelvis_not_level"


class StoolStep(Phase):
    """Legacy experimental quasi-static footfall along +x with the stool held:
    centre of mass over the stance foot (3/10 of the cycle), the swing foot lifted 4.5 cm and
    advanced `dist` (4/10), the centre of mass back to the middle (3/10). The swing foot is not
    lifted before the MEASURED centre of mass is within com_tolerance of the stance target
    (leg compliance leaves a steady offset, integrated into the command), and the mass is not
    moved back before the foot is down. The stool reference advances with the feet mid-point."""

    name = "step"

    def __init__(self, chain, side, **kw):
        super().__init__(side, **kw)
        self.chain = chain

    def start(self, ctx):
        chain = self.chain
        self.swing = 0 if self.side == "left" else 1
        self.stance = 1 - self.swing
        chain.feet[:, :2] = ctx.feet_meas[:, :2]        # plan from where the feet really are
        self.feet0 = chain.feet.copy()
        self.mid0 = self.feet0[:, :2].mean(axis=0)
        self.com0 = ctx.com_cmd.copy()
        # the centre-of-mass offset from the feet mid-point is the walk's nominal one, not re-derived
        # from the last command: footfalls landing short of the IK's (they touch down early) let the
        # world-frame command creep ahead of the real feet until the body was thrown forward
        # (stepwalk-v10, -v14: IK foot 8 cm ahead of the real one at the 5th footfall)
        if getattr(chain, "walk_offset", None) is None:
            chain.walk_offset = self.com0 - self.mid0
        self.offset = chain.walk_offset.copy()
        self.done_early = self.kw.get("goal_x") is not None and float(ctx.measured[0]) >= self.kw["goal_x"] - 0.02
        R_ref = getattr(chain, "walk_R0", None)
        if R_ref is None:
            R_ref = chain.walk_R0 = ctx.box_des[1].copy()
        self.box0 = (ctx.box_des[0].copy(), R_ref)
        self.clock = self.waited = self.landing_wait = 0.0
        self.bias = np.zeros(2)
        self.ready_time = 0.0

    def compensated(self, ctx, com_cmd):
        """The robot's own centre-of-mass target for a commanded (robot + load) one, as run_stiff."""
        chain = self.chain
        carried = float(np.clip(ctx.support("left") + ctx.support("right"), 0.0, chain.args.mass * G))
        robot_weight = float(ctx.planner.m.body_subtreemass[1]) * G
        return com_cmd - carried / robot_weight * (chain.stool.pos[:2] - com_cmd)

    def step(self, ctx, age):
        chain = self.chain
        if self.done_early:
            return "done"
        duration = self.kw.get("seconds", 8.0)
        d = self.kw["dist"]
        offset = self.offset
        # aim `inset` short of the stance foot's centre line (towards the other foot): standing tall
        # with the stool the shift overran the foot centre by 3.5 cm and toppled (stepwalk-v6)
        stance_com = self.feet0[self.stance, :2] + offset
        stance_com[1] += self.kw.get("inset", 0.0) * (1.0 if self.stance == 1 else -1.0)
        local = min(self.clock * 10 / duration, 10.0)
        error = self.compensated(ctx, stance_com) - ctx.com_meas
        velocity = chain.cpu(chain.r.get_vel())[:2]
        steady = (float(np.linalg.norm(error)) < self.kw.get("com_tolerance", 0.025)
                  and float(np.linalg.norm(velocity)) < 0.02)
        self.ready_time = self.ready_time + 0.02 if steady else 0.0
        ready = self.ready_time >= 0.20
        # landed = the swing foot carries load, not just its height: at touchdown with ~0 N the
        # support assumption flipped to both feet, the stance leg's feed-forward halved and the
        # other leg pushed on a foot that was not down, rolling the body over (stepwalk-v16)
        fz_all = chain.r.get_links_net_contact_force()[0, [chain.r.get_link(nm).idx_local for nm in T.FOOT_LINKS], 2].cpu().numpy()
        landed = float(fz_all[self.swing]) > self.kw.get("land_force", 40.0)
        self.seek = getattr(self, "seek", 0.0)
        if 6.9 < local < 7.1 and not landed:
            self.landing_wait += 0.02
            if self.landing_wait >= 4.0:
                return "fail:landing_not_loaded"
            self.seek = min(self.seek + 0.02 * 0.02, 0.03)        # foot target 2 cm/s further down, <= 3 cm
            self.bias = np.clip(self.bias + self.kw.get("com_gain", 0.015) * error, -0.04, 0.04)
        elif local < 3.0 or ready or local > 3.2:
            self.clock += 0.02
            if 3.0 <= local < 7.1:
                # closed loop on the measured centre of mass through the IK command during single
                # support: held by the stiff PD + feed-forward alone the body crept outward ~2.5 cm/s
                # once the swing foot was up (stepwalk-v17)
                self.bias = np.clip(self.bias + self.kw.get("com_gain", 0.015) * error, -0.04, 0.04)
        else:
            self.waited += 0.02
            self.bias = np.clip(self.bias + 0.004 * error, -0.03, 0.03)
            if self.waited > self.kw.get("max_wait", 6.0):
                return "fail:com_not_over_stance_foot"
        local = min(self.clock * 10 / duration, 10.0)
        feet = self.feet0.copy()
        feet[self.swing, 0] += d * smooth((local - 3) / 4)
        feet[self.swing, 2] += self.kw.get("lift", 0.045) * np.sin(np.pi * np.clip((local - 3) / 4, 0, 1)) ** 2 - self.seek
        chain.feet = feet
        if local <= 7:
            ctx.com_cmd = self.com0 + (stance_com - self.com0) * smooth(local / 3) + self.bias
        else:
            final = feet[:, :2].mean(axis=0) + offset
            ctx.com_cmd = stance_com + (final - stance_com) * smooth((local - 7) / 3) + self.bias * (1 - smooth((local - 7) / 3))
        # the stool goes forward with the feet (half a step per footfall) and sideways with the
        # commanded centre of mass: left at the centre line, the IK hung the pelvis 8 cm outside
        # the stance foot to balance it and the robot toppled sideways at lift-off (stepwalk-v3)
        # ... with the commanded centre of mass, not the feet mid-point: the pelvis trails the feet,
        # and after three footfalls the stool had gone from 0.47 to 0.60 m ahead of it, the arms
        # stretched and it pitched 32 deg into the body (stepwalk-v5)
        adv = float(ctx.com_cmd[0] - self.com0[0])
        sway = float(ctx.com_cmd[1] - self.com0[1]) * self.kw.get("sway", 1.0)
        # Carry's pitch feedback: tilt the hands against the measured stool pitch (the underhand
        # hold lets the stool pitch about the rails)
        pitch = float(np.arcsin(np.clip(-ctx.box.R[2, 0], -1, 1)))
        chain.walk_pitch_fb = float(np.clip(getattr(chain, "walk_pitch_fb", 0.0) + self.kw.get("pitch_gain", 0.02) * pitch, -0.25, 0.25))
        R_cmd = Rotation.from_rotvec([0, -chain.walk_pitch_fb, 0]).as_matrix() @ self.box0[1]
        ctx.box_des = (self.box0[0] + np.array([adv, sway, 0.0]), R_cmd)
        single = 3 < local < 7 or (local >= 7 and not landed and self.kw.get("hold_single", True))
        chain.balance = dict(support=[self.stance] if single else [0, 1])
        if int(round(chain.t / 0.02)) % 10 == 0:
            fz = fz_all
            chain.report.setdefault("walk_trace", []).append(dict(
                t=round(chain.t, 2), side=self.side, local=round(float(local), 1), waited=round(self.waited, 2),
                feet_cmd=np.round(feet, 3).tolist(), feet_meas=np.round(ctx.feet_meas, 3).tolist(),
                com_cmd=np.round(ctx.com_cmd, 3).tolist(), com_tgt=np.round(self.compensated(ctx, ctx.com_cmd), 3).tolist(),
                com_meas=np.round(ctx.com_meas, 3).tolist(), bias=np.round(self.bias, 3).tolist(),
                root=np.round(ctx.measured[:3], 3).tolist(), root_ref=np.round(chain.qref[:3], 3).tolist(),
                feet_ref=np.round(chain.ik_feet(), 3).tolist(), fz=np.round(fz, 1).tolist(),
                stool=np.round(chain.stool.pos, 3).tolist(), tilt=round(chain.stool.tilt_deg(), 1),
                bal=getattr(chain, "balance_last", None)))
        if self.clock > duration + 0.5:
            if not landed:
                return "fail:landing_not_loaded"
            chain.balance = dict(support=[0, 1])
            ctx.metrics.setdefault("step_com_wait_s", []).append(round(self.waited, 2))
            ctx.metrics.setdefault("footfalls_m", []).append(round(float(ctx.feet_meas[self.swing, 0] - self.feet0[self.swing, 0]), 4))
            return "done"
        return None


class StoolRobot:
    """oracle.Robot's interface for the arms while the contact QP holds the legs: lets the
    floor-tested oracle.retrieve run unchanged on the stool."""

    def __init__(self, chain, cont, q_stand):
        from humanoid.g1_support_retrieval.oracle.upper_ik import UpperBodyIK
        self.chain, self.cont, self.env = chain, cont, chain.env
        self.video = None
        self.ik = UpperBodyIK()
        # Waist yaw and roll nearly locked: the stool stands square in front of the target, and
        # with the fingers turned up the IK's waist yaw/roll flipped sign every few steps with
        # growing amplitude, rocking the box out of the hands (chain-dev-v8: +-0.13 rad)
        for name, lo, hi in (("waist_yaw_joint", -0.05, 0.05), ("waist_roll_joint", -0.05, 0.05),
                             ("waist_pitch_joint", -0.1, 0.3)):
            self.ik.limit(name, lo, hi)
        self.links = {l.idx: l.name for l in self.env.robot.links}
        self.s = self.env.state()
        self.q_ref = self.joints().copy()
        self.hands = {"left": "open", "right": "open"}
        self.steps, self.done, self.info = 0, False, {}
        self.q_stand = q_stand
        self.box_contacts = []
        self.waist_velocity = np.zeros(3)
        self.previous_reference = q_stand.copy()
        # the IK works from the reference base pose the QP holds, not the measured one: solving
        # from the measured (swaying) base, the waist chased the sway and the sway grew
        # (chain-dev-v8/v9: waist yaw, roll, then pitch flipping sign every 0.24 s)
        w = cont.world_pose(q_stand)
        self.ref_pos, self.ref_quat = w[:3].copy(), w[3:7].copy()
        self.ref_legs = q_stand[cont.p.qids[:12]].copy()

    @property
    def pos(self):
        return self.s.root_pos[0].cpu().numpy()

    @property
    def quat(self):
        return self.s.root_quat[0].cpu().numpy()

    @property
    def yaw(self):
        return float(T.yaw_of(self.s.root_quat)[0])

    def joints(self):
        return self.s.joint_pos[0].cpu().numpy().astype(float)

    def box_state(self, k):
        box = self.env.top_boxes[k]
        return box.get_pos()[0].cpu().numpy(), box.get_quat()[0].cpu().numpy()

    def hand_forces(self, k):
        from humanoid.g1_support_retrieval.oracle.oracle import Robot
        return Robot.hand_forces(self, k)

    def hold_legs(self, on=True):
        self.stance_log = "contact QP on the stool"

    def reach(self, tasks, rate=0.6, iters=6):
        """oracle.Robot.reach, from the reference base pose and legs (see __init__)."""
        from humanoid.g1_support_retrieval.oracle.oracle import hand_preset
        rate = rate * self.chain.args.arm_rate_scale
        q = self.q_ref.copy()
        q[:12] = self.ref_legs
        for side, mode in self.hands.items():
            if mode is not None:
                q = hand_preset(q, side, mode)
        sol, _ = self.ik.solve(self.ref_pos, self.ref_quat, q, tasks, iters=iters)
        up = self.ik.upper
        waist_start = self.q_ref[12:15].copy()
        self.q_ref[up] += np.clip(sol[up] - self.q_ref[up], -rate * T.CONTROL_DT, rate * T.CONTROL_DT)
        # Abrupt waist reversals accelerate the whole torso while standing on
        # the stool. Keep this motion smooth even when the arm IK changes branch.
        error = sol[12:15] - waist_start
        acceleration = np.clip(16.0 * error - 8.0 * self.waist_velocity,
                               -self.chain.args.stool_waist_accel, self.chain.args.stool_waist_accel)
        self.waist_velocity = np.clip(self.waist_velocity + acceleration * T.CONTROL_DT,
                                      -self.chain.args.stool_waist_rate, self.chain.args.stool_waist_rate)
        self.q_ref[12:15] = waist_start + self.waist_velocity * T.CONTROL_DT
        # Path advancement must use the commanded pose after rate limits and
        # physical joint margins, rather than the unconstrained IK solution.
        commanded = self.target()
        commanded[:12] = self.ref_legs
        self.ik._set(self.ref_pos, self.ref_quat, commanded)
        return {side: float(np.linalg.norm(np.asarray(pos) - self.ik.hand_point(side, kind)))
                for side, (kind, pos, rot) in tasks.items()}

    def target(self):
        from humanoid.g1_support_retrieval.oracle.oracle import hand_preset
        q = self.q_ref.copy()
        for side, mode in self.hands.items():
            if mode is not None:
                q = hand_preset(q, side, mode)
        limits, margins = self.chain.physical_joint_limits, self.chain.position_margins
        return np.clip(q, limits[:, 0] + margins, limits[:, 1] - margins)

    def step(self, *a, **kw):
        cont = self.cont
        ref = self.q_stand.copy()
        ref[cont.p.qids[12:]] = self.target()[12:]
        vref = np.zeros(cont.p.m.nv)
        mujoco.mj_differentiatePos(cont.p.m, vref, T.CONTROL_DT, self.previous_reference, ref)
        self.previous_reference = ref.copy()
        # Contact sensing is part of control, independent of diagnostic logging.
        self.hand_forces(self.chain.k)
        contacts = list(self.box_contacts)
        contacts.extend((name, point, force) for name, _, force, point in self.chain.hand_env_contacts(self))
        # the measured contact wrench enters the QP low-pass filtered and bounded: the step when the
        # palms first touch the box made a QP frame infeasible and the robot lost its stance on the
        # stool (chain-relay-v2, chain-dev-v26)
        raw = cont.external_from(contacts) if contacts else np.zeros(cont.p.m.nv)
        self.ext = raw if getattr(self, "ext", None) is None else 0.85 * self.ext + 0.15 * raw
        ext = np.clip(self.ext, -40.0, 40.0)
        try:
            cont.tick(ref, vref, [0, 1], "on_stool", "qp", external=ext)
        except ValueError as exc:
            self.done, self.info = True, {"error": str(exc)}
            return False
        # Holds and direct reference interpolation also pass here. Keep the
        # filter state equal to the reference velocity actually sent to the QP.
        self.waist_velocity = vref[cont.p.vids[12:15]].copy()
        self.steps += 1
        self.s = self.env.state()
        self.chain.t = cont.t
        if self.steps % 10 == 0:
            self.chain.report.setdefault("on_stool_reference", []).append(dict(
                t=round(cont.t, 3), waist_ref=ref[cont.p.qids[12:15]].tolist(),
                waist_velocity=vref[cont.p.vids[12:15]].tolist(), waist_measured=self.joints()[12:15].tolist(),
                external_base=ext[:6].tolist()))
        return True


class ChainOn(StepOn):
    """step_on's verified stand-and-climb, then (instead of its retrieval) the oracle's shelf
    retrieval on the stool and the step down: the executed climb played backwards."""

    def __init__(self, chain):
        self.chain = chain
        self.climb = None

    def stand(self):
        # Keep the arms inward while climbing. The transported stool can finish
        # rotated: the wider posture struck the cabinet upright during single
        # support even though the stool-local reference was feasible.
        self.p.nominal_shoulder_pitch = -0.075
        self.p.nominal_shoulder_roll = 0.4
        self.p.leading_com_inset = self.chain.args.climb_com_inset
        # Loaded ankle tracking can consume the generic 20 mrad IK reserve.
        # Keep this inside the IK bounds so the whole-body pose is re-solved;
        # clipping a finished trajectory would move the supporting foot.
        self.ik_joint_margin = np.full(12, 0.02)
        self.ik_joint_margin[[4, 10]] = self.chain.args.climb_ankle_pitch_margin
        self.ik_joint_margin[[5, 11]] = self.chain.args.climb_ankle_roll_margin
        super().stand()
        self.adjust_climb_entry()

    def adjust_climb_entry(self):
        """Physically recover the verified approach footprint after transporting the stool."""
        from humanoid.g1_support_retrieval.oracle.stool_walk import fixed_root_leg_ik
        from humanoid.g1_support_retrieval.oracle.entry_reference import retime_entry_reference
        from scipy.spatial import ConvexHull

        p = self.p
        q, _ = self.state()
        root_quat = q[3:7].copy()
        upper_target = p.nominal()[p.qids[12:]].copy()
        p.forward(q)
        feet = p.d.xpos[p.feet].copy()
        # Measured successful start-at-climb footprint, in the observed stool frame.
        target = np.array([[p.box_x - 0.4613, 0.119, 0.035],
                           [p.box_x - 0.4613, -0.119, 0.035]])
        error = np.linalg.norm(feet[:, :2] - target[:, :2], axis=1)
        if error.max() < 0.012:
            return
        if error.max() > 0.16:
            raise ValueError("climb entry requires more than the bounded 16 cm foot adjustment")
        foot_ids = [self.r.get_link(name).idx_local for name in T.FOOT_LINKS]
        weight = float(p.m.body_subtreemass[1]) * G
        height = min(float(q[2]), 0.72)
        log = self.chain.report.setdefault("climb_entry", [])

        def leg_ik(seed, desired_feet, desired_com, desired_height):
            seed = seed.copy()
            # Keep the stand controller's motor targets. Re-seeding each segment
            # from load-deflected upper joints would accumulate its static error.
            seed[p.qids[12:]] = upper_target
            return fixed_root_leg_ik(p, seed, desired_feet, desired_com, desired_height,
                                     np.zeros((2, 3)), root_quat, margin=0.02)

        def measured():
            actual, velocity = self.state()
            p.forward(actual)
            return (actual, velocity, p.d.xpos[p.feet].copy(), p.d.subtree_com[1, :2].copy(),
                    self.r.get_links_net_contact_force()[0, foot_ids, 2].detach().cpu().numpy())

        def record(phase, ref, supports):
            actual, velocity, actual_feet, com, fz = measured()
            foot_velocity, bottom, support_points = [], [], []
            for side, body in enumerate(p.feet):
                jac = np.zeros((3, p.m.nv))
                mujoco.mj_jac(p.m, p.d, jac, None, actual_feet[side], body)
                foot_velocity.append((jac @ velocity).tolist())
                rotation = p.d.xmat[body].reshape(3, 3)
                corners = actual_feet[side] + p.corners @ rotation.T
                bottom.append(float(corners[:, 2].min()))
                if side in supports:
                    support_points.extend(corners[:, :2])
            hull = ConvexHull(np.asarray(support_points))
            support_margin = float(-np.max(hull.equations[:, :2] @ com + hull.equations[:, 2]))
            p.forward(ref)
            com_error = float(np.linalg.norm(com - p.d.subtree_com[1, :2]))
            foot_error = np.linalg.norm(actual_feet - p.d.xpos[p.feet], axis=1)
            item = dict(time=round(self.t, 3), phase=phase, feet=actual_feet.tolist(), fz=fz.tolist(),
                        com=com.tolist(), com_error=com_error, root_speed=float(np.linalg.norm(velocity[:3])),
                        foot_error=foot_error.tolist(), support=supports, bottom=bottom,
                        support_margin=support_margin,
                        foot_velocity=foot_velocity, root=actual[:7].tolist(), root_ref=ref[:7].tolist(),
                        feet_ref=p.d.xpos[p.feet].tolist(), measured_q=actual.tolist(),
                        measured_v=velocity.tolist(), reference_q=ref.tolist())
            log.append(item)
            return item

        def segment(phase, desired_feet, desired_com, desired_height, supports, seconds):
            start, _ = self.state()
            p.forward(start)
            start_feet = p.d.xpos[p.feet].copy()
            start_feet[:, 2] = np.where(start_feet[:, 2] < 0.045, 0.035, start_feet[:, 2])
            start_com = p.d.subtree_com[1, :2].copy()
            previous = start.copy()
            poses = [previous.copy()]
            for step in range(1, int(seconds / T.CONTROL_DT) + 1):
                u = smooth(step * T.CONTROL_DT / seconds)
                f = start_feet + (desired_feet - start_feet) * u
                ref = leg_ik(previous, f, start_com + (desired_com - start_com) * u,
                             start[2] + (desired_height - start[2]) * u)
                self.collision_check(ref)
                previous = ref
                poses.append(ref.copy())
            # A bounded Cartesian path can still jump between IK configurations.
            # Plan before moving, then bound the actual 20 ms joint and pelvis
            # differences, including the stationary gates at both ends.
            qs, times, velocities, accelerations, timing = retime_entry_reference(
                p.m, p.vids, poses, seconds, dt=T.CONTROL_DT)
            peak_effort = 0.0
            for step, ref in enumerate(qs[1:], 1):
                self.collision_check(ref)
                if step % 5 == 0 or step == len(qs) - 1:
                    tau = p.force_check(ref, velocities[step], accelerations[step - 1], supports,
                                        reserve=1.0, actuated_indices=np.arange(12))
                    peak_effort = max(peak_effort, float(np.max(np.abs(tau[:12]) / p.params["effort"][:12])))
            self.chain.report.setdefault("climb_entry_timing", []).append(dict(
                phase=phase, original_duration=seconds, peak_reference_effort_ratio=peak_effort, **timing))
            self.chain.event("climb:entry_plan", phase=phase, duration=float(times[-1]),
                             joint_speed_radps=timing["joint_speed_radps"],
                             joint_acceleration_radps2=timing["joint_acceleration_radps2"],
                             root_speed_mps=timing["root_speed_mps"],
                             root_acceleration_mps2=timing["root_acceleration_mps2"])
            for step, ref in enumerate(qs[1:], 1):
                self.tick(ref, velocities[step], supports, "entry_" + phase, "qp")
                if step % 10 == 0:
                    record(phase, ref, supports)
            return qs[-1]

        def gate(phase, ref, supports, landing=None, unload=None, swing=None, target_xy=None):
            stable = 0.0
            vref = np.zeros(p.m.nv)
            p.forward(ref)
            contact_feet = p.d.xpos[p.feet].copy()
            contact_com = p.d.subtree_com[1, :2].copy()
            # Contact compliance varies with the incoming posture. Keep the
            # measured 2 N touchdown requirement and give the slow bounded
            # search enough travel to establish it before enabling both feet.
            for step in range(250 if landing is not None else 150):
                self.tick(ref, vref, supports, "entry_" + phase, "qp")
                vref[:] = 0
                item = record(phase, ref, supports)
                load = np.asarray(item["fz"])
                # A newly touching foot is still excluded from the old single-
                # support QP. Confirm real contact and a safe measured support
                # margin before enabling both feet; tracking settles in recenter.
                balanced = item["support_margin"] > 0.005 if landing is not None else item["com_error"] < 0.012
                good = (balanced and item["root_speed"] < 0.025
                        and (load[1 - unload] > 0.75 * weight and load[unload] < 0.15 * weight
                             if unload is not None else
                             min(load[supports]) > (0.70 * weight if len(supports) == 1 else 20.0)))
                if swing is not None:
                    good = (good and item["bottom"][swing] > 0.025 and load[swing] < 0.05 * weight
                            and np.linalg.norm(item["foot_velocity"][swing]) < 0.02)
                    if target_xy is not None:
                        good = good and np.linalg.norm(np.asarray(item["feet"])[swing, :2] - target_xy) < 0.008
                if landing is not None:
                    good = (good and load[landing] > 2.0 and abs(item["feet"][landing][2] - 0.035) < 0.006
                            and abs(item["foot_velocity"][landing][2]) < 0.015
                            and np.linalg.norm(np.asarray(item["feet"])[landing, :2] - target[landing, :2]) < 0.012)
                    # Keep seeking contact until the measured load is sustained,
                    # including when an initial light touch subsequently unloads.
                    if load[landing] <= 2.0 and contact_feet[landing, 2] > 0.0305:
                        contact_feet[landing, 2] = max(0.0305, contact_feet[landing, 2] - 0.00002)
                        next_ref = leg_ik(ref, contact_feet, contact_com, height)
                        self.collision_check(next_ref)
                        mujoco.mj_differentiatePos(p.m, vref, T.CONTROL_DT, ref, next_ref)
                        ref = next_ref
                stable = stable + T.CONTROL_DT if good else 0.0
                if stable >= 0.24:
                    self.chain.t = self.t
                    self.chain.event("climb:entry_gate", phase=phase, fz=item["fz"],
                                     com_error=item["com_error"], feet=item["feet"])
                    return ref
            raise ValueError("climb entry measured gate failed: " + phase)

        self.chain.t = self.t
        # Move the foot that leaves the narrower intermediate stance first.
        # The transported footprint is asymmetric; a fixed left-first order
        # stretched the other leg nearly straight and pinned its ankle roll.
        intermediate_span = [float(np.linalg.norm(target[side, :2] - feet[1 - side, :2]))
                             for side in (0, 1)]
        first = int(np.argmin(intermediate_span))
        order = (first, 1 - first)
        self.chain.event("climb:entry_adjust", feet=feet.tolist(), target=target.tolist(),
                         foot_order=order, intermediate_span=intermediate_span)
        feet[:, 2] = 0.035
        ref = segment("center", feet, feet[:, :2].mean(axis=0) + [0.035, 0.0], height, [0, 1], 2.5)
        gate("center", ref, [0, 1])
        for swing in order:
            support = 1 - swing
            _, _, feet, _, _ = measured()
            feet[:, 2] = 0.035
            com = feet[support, :2] + [0.035, 0.0]
            ref = segment(f"transfer_{support}", feet, com, height, [0, 1], 3.0)
            gate(f"before_lift_{swing}", ref, [0, 1], unload=swing)
            raised = feet.copy()
            raised[swing, 2] = 0.075
            ref = segment(f"lift_{swing}", raised, com, height, [support], 1.5)
            gate(f"lifted_{swing}", ref, [support], swing=swing)
            raised[swing, :2] = target[swing, :2]
            ref = segment(f"back_{swing}", raised, com, height, [support], 2.0)
            gate(f"aligned_{swing}", ref, [support], swing=swing, target_xy=target[swing, :2])
            raised[swing, 2] = 0.034
            ref = segment(f"land_{swing}", raised, com, height, [support], 1.5)
            ref = gate(f"landed_{swing}", ref, [support], landing=swing)
            _, _, feet, _, _ = measured()
            feet[:, 2] = 0.035
            ref = segment(f"recenter_{swing}", feet, feet[:, :2].mean(axis=0) + [0.035, 0.0],
                          height, [0, 1], 2.5)
            gate(f"recenter_{swing}", ref, [0, 1])
        # End with the same height and neutral arms used by the original climb.
        _, _, feet, _, _ = measured()
        feet[:, 2] = 0.035
        ref = segment("stand", feet, feet[:, :2].mean(axis=0) + [0.035, 0.0],
                      float(p.nominal()[2]), [0, 1], 2.5)
        gate("ready", ref, [0, 1])
        _, _, feet, _, _ = measured()
        final_error = np.linalg.norm(feet[:, :2] - target[:, :2], axis=1)
        if final_error.max() > 0.012:
            raise ValueError("climb entry footprint did not converge")
        self.chain.t = self.t
        self.chain.event("climb:entry_ready", feet=feet.tolist(), error=final_error.tolist())

    def resume_on_stool(self, ctx, state):
        """Diagnostic continuation from verified top support, without replaying the climb."""
        restore_on_stool_continuation(self, state, ctx)
        report = dict(success=False, status="not_started", runtime_pose_writes=False,
                      object_attachment=False, diagnostic_resume=True)
        try:
            self.retrieve()
            report.update(success=True, status="retrieval_metrics_passed_video_review_required")
        except (ValueError, RuntimeError) as exc:
            report.update(status="stopped", reason=str(exc))
        finally:
            report.update(stages=self.stages, final_time=self.t, max_effort_ratio=self.max_effort,
                          max_speed_ratio=self.max_speed, max_joint_limit_overshoot=self.max_stop)
            report["actuator_checks"] = (self.max_effort <= 1.001 and self.max_speed <= 1.001
                                          and self.max_stop <= 0.001)
            report["climb_success"] = ("box_top_support_verified" in self.stages
                                         and report["actuator_checks"])
            report["success"] = bool(report["success"] and report["climb_success"])
            (self.args.out / "continuation_result.json").write_text(json.dumps(report, indent=2))
            (self.args.out / "continuation_trace.json").write_text(json.dumps(self.rows))
            np.savez(self.args.out / "continuation_joints.npz", measured=self.joints)
        return report

    def execute(self, qs, times, labels, mode="native"):
        if mode == "qp" and self.climb is None:
            # The shared step planner contains the floor and stool only. Check
            # the actual cabinet at the observed stool position/yaw before
            # executing a climb; a clear path in the stool proxy is insufficient.
            from humanoid.g1_support_retrieval.oracle.cabinet_clearance import check_cabinet_clearance
            control_times = np.arange(0, times[-1] + 0.001, T.CONTROL_DT)
            world_poses, control_phases = [], []
            for t in control_times:
                i = min(max(np.searchsorted(times, t, side="right") - 1, 0), len(times) - 2)
                a = np.clip((t - times[i]) / (times[i + 1] - times[i]), 0, 1)
                q = qs[i] * (1 - a) + qs[i + 1] * a
                q[3:7] /= np.linalg.norm(q[3:7])
                world_poses.append(self.world_pose(q))
                control_phases.append(str(labels[i]))
            clearance = check_cabinet_clearance(
                self.chain.report["scene"]["cabinet"], np.asarray(world_poses),
                minimum_clearance=0.025)
            sample = clearance["closest"]["sample_index"]
            clearance.update(reference_frame="world", control_dt=T.CONTROL_DT,
                             minimum_time_seconds=(float(control_times[sample]) if sample is not None else None),
                             minimum_phase=(control_phases[sample] if sample is not None else None),
                             stool_position=self.bp.tolist(), stool_yaw_rad=float(self.yaw))
            self.chain.report["climb_cabinet_clearance"] = clearance
            (self.chain.args.out / "climb_cabinet_clearance.json").write_text(
                json.dumps(clearance, indent=2), encoding="utf-8")
            self.chain.event("climb:clearance_checked", passed=clearance["passed"],
                             minimum_clearance_m=clearance["minimum_clearance_m"],
                             required_clearance_m=clearance["required_clearance_m"],
                             closest=clearance["closest"])
            if not clearance["passed"]:
                raise ValueError("climb reference lacks cabinet clearance")
            self.climb = (np.array(qs).copy(), np.array(times).copy(), np.array(labels).copy())
            roll = np.asarray(qs)[:, self.p.qids[[5, 11]]]
            self.chain.event("climb:start", seconds=round(float(times[-1]), 1),
                             ankle_roll_reference_min=roll.min(axis=0).tolist(),
                             ankle_roll_reference_max=roll.max(axis=0).tolist())
            mode = self.chain.args.climb_mode
            # Scope the measured-COM controller to the formal climb. Retrieval
            # and reverse descent retain their separately verified controller.
            saved_weight = getattr(self.wbc, "com_task_weight", 0.0)
            saved_diagnostics = getattr(self.wbc, "record_diagnostics", False)
            saved_contact_mode = getattr(self.wbc, "contact_stabilization", "reference")
            saved_position_guard = getattr(self.wbc, "position_guard_margin", None)
            self.wbc.com_task_weight = self.chain.args.climb_com_weight
            self.wbc.contact_stabilization = self.chain.args.climb_contact_stabilization
            self.wbc.position_guard_margin = self.chain.args.climb_position_guard
            self.wbc.record_diagnostics = True
            self.chain.event("climb:controller", com_task_weight=self.wbc.com_task_weight,
                             leading_com_inset_m=self.p.leading_com_inset,
                             ankle_pitch_reference_margin_rad=self.chain.args.climb_ankle_pitch_margin,
                             ankle_roll_reference_margin_rad=self.chain.args.climb_ankle_roll_margin,
                             contact_stabilization=self.wbc.contact_stabilization,
                             position_guard_margin_rad=self.wbc.position_guard_margin)
            try:
                with (self.chain.args.out / "climb_control_trace.jsonl").open("w", encoding="utf-8") as stream:
                    self._climb_trace_stream = stream
                    return super().execute(qs, times, labels, mode)
            finally:
                self._climb_trace_stream = None
                self.wbc.com_task_weight = saved_weight
                self.wbc.contact_stabilization = saved_contact_mode
                self.wbc.position_guard_margin = saved_position_guard
                self.wbc.record_diagnostics = saved_diagnostics
        return super().execute(qs, times, labels, mode)

    def collision_check(self, q):
        """As Continuation.collision_check, but names the colliding geoms and lets shallow
        foot-floor contact pass: the reference starts from the measured pose, whose feet sink a
        few mm into the floor (soft contact; chain-inplace-v1 stopped on -4 mm in `stand`)."""
        m, d = self.p.m, self.p.d
        self.p.forward(q)
        for c in d.contact[: d.ncon]:
            if c.dist >= -0.002:
                continue
            g = [int(c.geom[0]), int(c.geom[1])]
            names = [m.geom(i).name or m.body(m.geom_bodyid[i]).name for i in g]
            bodies = [m.body(m.geom_bodyid[i]).name for i in g]
            foot_floor = "probe_floor" in names and any("ankle" in b for b in bodies)
            if foot_floor and c.dist > -0.008:
                self.chain.report.setdefault("tolerated_foot_floor_mm", []).append(round(float(c.dist) * 1000, 1))
                continue
            # the shoulder links' meshes overlap the torso by a few mm near the adduction limit
            # (chain-inplace-v2: left_shoulder_roll_link / torso_link -4.2 mm in `stand`)
            shoulder_torso = "torso_link" in bodies and any("shoulder" in b for b in bodies)
            # (with the robot's self-collision off, the stand-up leaves the shoulder 1.6 cm in the
            # torso, chain-relay-v11: tolerate what the sim itself does not react to)
            if shoulder_torso and c.dist > (-0.006 if self.chain.args.self_collision else -0.025):
                self.chain.report.setdefault("tolerated_shoulder_torso_mm", []).append(round(float(c.dist) * 1000, 1))
                continue
            raise ValueError(f"Continuation reference collision {c.dist:.4f} m {bodies} {names}")

    def external_from(self, contacts):
        """Generalized force of measured robot contacts [(link, world point, force on robot)]."""
        p = self.p
        q, _ = self.state()
        p.forward(q)
        ext, jac = np.zeros(p.m.nv), np.zeros((3, p.m.nv))
        for name, point, force in contacts:
            try:
                body = p.m.body(name).id
            except KeyError:
                continue
            mujoco.mj_jac(p.m, p.d, jac, None, self.local_point(point), body)
            ext += jac.T @ self.rot.apply(np.asarray(force, float))
        # Only the base, legs and waist: the arms and hands are position-controlled in the
        # simulation, and the QP's 95 % torque bound on the tiny Dex3 finger joints made it
        # infeasible under a squeeze (chain-inplace-v3: stopped while pulling the box out).
        ext[p.vids[15:]] = 0.0
        return ext

    def retrieve(self):
        chain = self.chain
        chain.t = self.t
        chain.event("climb:on_stool")
        chain.report["stages"]["climb"] = "done"
        checkpoint_path = chain.args.save_on_stool_checkpoint
        if checkpoint_path is None and chain.args.save_checkpoint:
            path = chain.args.save_checkpoint
            checkpoint_path = path.with_name(path.stem + "-on-stool" + path.suffix)
        if checkpoint_path and not hasattr(chain, "_resume_on_stool"):
            chain._checkpoint_continuation = self
            try:
                save_chain_checkpoint(chain, checkpoint_path, stage="on_stool")
            except Exception as exc:
                chain.report["checkpoint_error"] = dict(type=type(exc).__name__, message=str(exc))
                chain.event("checkpoint:failed", **chain.report["checkpoint_error"])
            else:
                chain.event("checkpoint:saved", path=str(checkpoint_path), checkpoint_stage="on_stool", diagnostic_only=True)
            finally:
                del chain._checkpoint_continuation
        if chain.args.stop_after == "climb":
            return
        from humanoid.g1_support_retrieval.oracle.oracle import retrieve as oracle_retrieve
        robot = self.prepare_retrieval()
        if chain.args.skip_retrieve:              # development: step down empty-handed
            self.step_down(robot)
            return
        chain.view = "shelf"
        res = oracle_retrieve(robot, chain.k, T.TOP_SIZES[chain.k])
        chain.t = self.t
        chain.view = "stool"
        chain.report["stages"]["retrieve"] = dict(ok=res.ok, reason=res.reason,
                                                  metrics={k: v for k, v in res.metrics.items() if k != "trace"},
                                                  trace=res.metrics.get("trace"))
        chain.event("retrieve:end", ok=res.ok, reason=res.reason, error=robot.info.get("error"))
        chain.report["stages"]["retrieve"]["error"] = robot.info.get("error")
        if not res.ok:
            raise ValueError("retrieve: " + res.reason)
        self.stages.append("target_retrieved")
        if chain.args.stop_after == "retrieve":
            return
        if chain.args.relay:
            self.place_on_board(robot)
            self.stages.append("box_on_board_below")
            self.carrying = False
        self.step_down(robot)

    def prepare_retrieval_shoulders(self):
        """Execute once at the common fresh/checkpoint retrieval boundary."""
        if getattr(self, "_retrieval_shoulders_prepared", False):
            return
        p, chain = self.p, self.chain
        start, _ = self.state()
        qs, times, velocities, accelerations, timing = on_stool_shoulder_reference(p, start)
        from humanoid.g1_support_retrieval.oracle.cabinet_clearance import check_cabinet_clearance
        clearance = check_cabinet_clearance(
            chain.report["scene"]["cabinet"], np.asarray([self.world_pose(q) for q in qs]),
            minimum_clearance=0.025)
        chain.report["retrieval_shoulder_cabinet_clearance"] = clearance
        (chain.args.out / "retrieval_shoulder_cabinet_clearance.json").write_text(
            json.dumps(clearance, indent=2), encoding="utf-8")
        chain.event("retrieve:shoulder_clearance_checked", passed=clearance["passed"],
                    minimum_clearance_m=clearance["minimum_clearance_m"],
                    required_clearance_m=clearance["required_clearance_m"],
                    closest=clearance["closest"])
        if not clearance["passed"]:
            raise ValueError("retrieval shoulder reference lacks cabinet clearance")
        peak_effort = 0.0
        for step, ref in enumerate(qs[1:], 1):
            self.collision_check(ref)
            tau = p.force_check(ref, velocities[step], accelerations[step - 1], [0, 1],
                                reserve=1.0, actuated_indices=np.arange(12))
            peak_effort = max(peak_effort, float(np.max(abs(tau[:12]) / p.params["effort"][:12])))
        # Also check the final braking command before the stationary gate.
        p.force_check(qs[-1], np.zeros(p.m.nv), accelerations[-1], [0, 1],
                      reserve=1.0, actuated_indices=np.arange(12))
        record = dict(planned=timing, peak_reference_effort_ratio=peak_effort, trace=[], ok=False)
        chain.report["retrieval_shoulder_transition"] = record
        chain.event("retrieve:prepare_shoulders", duration=float(times[-1]),
                    shoulder_start_rad=timing["shoulder_start_rad"], shoulder_goal_rad=[-0.15, -0.15],
                    shoulder_roll_start_rad=timing["shoulder_roll_start_rad"],
                    shoulder_roll_goal_rad=timing["shoulder_roll_goal_rad"])
        for step, ref in enumerate(qs[1:], 1):
            self.tick(ref, velocities[step], [0, 1], "retrieval_prepare_shoulders", "qp")
        ref = qs[-1]
        foot_ids = [self.r.get_link(name).idx_local for name in T.FOOT_LINKS]
        shoulder_ids = np.asarray(timing["shoulder_joint_indices"])
        shoulder_roll_ids = np.asarray(timing["shoulder_roll_joint_indices"])
        stable = 0.0
        for _ in range(200):
            self.tick(ref, np.zeros(p.m.nv), [0, 1], "retrieval_prepare_settle", "qp")
            on_top = self.top_support()
            actual, velocity = self.state()
            p.forward(actual)
            fz = self.r.get_links_net_contact_force()[0, foot_ids, 2].detach().cpu().numpy()
            shoulder_error = max(float(np.max(abs(actual[p.qids[shoulder_ids]] + 0.15))),
                                 float(np.max(abs(actual[p.qids[shoulder_roll_ids]] - [0.5, -0.5]))))
            com_error = float(np.linalg.norm(p.d.subtree_com[1, :2] - np.asarray(timing["com"])))
            foot_error = float(np.max(np.linalg.norm(p.d.xpos[p.feet] - np.asarray(timing["feet"]), axis=1)))
            good = (on_top and min(fz) > 20.0 and shoulder_error < 0.01
                    and com_error < 0.01 and foot_error < 0.01
                    and np.linalg.norm(velocity[:3]) < 0.025
                    and np.linalg.norm(velocity[3:6]) < 0.1)
            stable = stable + T.CONTROL_DT if good else 0.0
            record["trace"].append(dict(time=round(self.t, 3), foot_fz_N=fz.tolist(),
                shoulder_pitch_rad=actual[p.qids[shoulder_ids]].tolist(),
                shoulder_roll_rad=actual[p.qids[shoulder_roll_ids]].tolist(),
                shoulder_error_rad=shoulder_error, com_error_m=com_error, foot_error_m=foot_error,
                root_speed_mps=float(np.linalg.norm(velocity[:3])),
                root_angular_speed_radps=float(np.linalg.norm(velocity[3:6])),
                stable_seconds=stable))
            if stable >= 0.5:
                record.update(ok=True, final_time=self.t, actual_q=actual.tolist())
                self._retrieval_shoulders_prepared = True
                chain.event("retrieve:shoulders_ready", shoulder_pitch_rad=actual[p.qids[shoulder_ids]].tolist(),
                            shoulder_roll_rad=actual[p.qids[shoulder_roll_ids]].tolist(),
                            com_error_m=com_error, foot_fz_N=fz.tolist())
                return
        raise ValueError("retrieval shoulder preparation did not settle")

    def prepare_retrieval(self):
        """Initialize the same first-tick controller for fresh and restored top support."""
        chain = self.chain
        existing = getattr(chain, "on_stool", None)
        if existing is not None:
            if existing.cont is not self:
                raise ValueError("retrieval controller belongs to a different continuation")
            return existing
        self.prepare_retrieval_shoulders()
        # an occasional single infeasible contact-QP frame stopped the run (chain-dev-v26, while
        # squeezing): reuse the last torques for up to 10 frames in a row
        plain_solve = self.wbc.solve
        memo = {"tau": None, "misses": 0}

        def solve(*a, **kw):
            try:
                memo["tau"], memo["misses"] = plain_solve(*a, **kw), 0
            except ValueError:
                memo["misses"] += 1
                chain.report["qp_frames_reused"] = chain.report.get("qp_frames_reused", 0) + 1
                if memo["tau"] is None or memo["misses"] > 10:
                    raise
            return memo["tau"]
        self.wbc.solve = solve
        q_stand, _ = self.state()
        robot = StoolRobot(chain, self, q_stand)
        chain.on_stool = robot
        return robot

    def tick(self, ref, vref, support, phase, *a, **kw):
        self.chain.t = self.t
        tick_start = self.t
        self.chain._audit_current_reference = ref
        self.chain._audit_current_velocity = vref
        self.chain._audit_current_phase = phase
        try:
            out = super().tick(ref, vref, support, phase, *a, **kw)
        finally:
            self.chain.t = self.t
            self.chain._audit_current_reference = None
            self.chain._audit_current_velocity = None
            self.chain._audit_current_phase = None
            stream = getattr(self, "_climb_trace_stream", None)
            debug = getattr(self.wbc, "control_debug", None)
            if stream is not None and debug is not None:
                actual, velocity = self.state()
                foot_ids = [self.r.get_link(name).idx_local for name in T.FOOT_LINKS]
                row = dict(time_start=tick_start, time_end=self.t, phase=phase, **debug,
                    position_guard=getattr(self.wbc, "position_guard_debug", None),
                    post_q=actual.tolist(), post_v=velocity.tolist(),
                    foot_force_world=self.r.get_links_net_contact_force()[0, foot_ids].detach().cpu().tolist(),
                    stool_position_world=self.cpu(self.box.get_pos()).tolist(),
                    stool_quaternion_world=self.cpu(self.box.get_quat()).tolist())
                stream.write(json.dumps(row) + "\n")
        self._tick_n = getattr(self, "_tick_n", 0) + 1
        self.chain.note_efforts(phase if phase in ("on_stool",) else ("stepdown" if phase.startswith("down_") else "climb"))
        if self._tick_n % 10 == 0:
            touch = {k: v[:2] for k, v in self.chain.robot_touches(None).items() if "ankle" not in k}
            if touch:
                self.chain.report.setdefault("climb_touches", []).append([round(self.t, 2), phase, touch])
        return out

    def torso_force(self, robot):
        return float(sum(np.linalg.norm(fc) for n, _, fc in getattr(robot, "box_contacts", []) if "torso" in n))

    def hug(self, robot):
        """Turn the held box on to the chest: both palms as one rigid grip, rotated about the grip
        axis to fingers-up 90 deg and moved so the contact centre is hug_ahead in front of and
        hug_up above the pelvis, then pressed in until the torso carries ~3 N. A two-palm squeeze
        holds through point contacts and lets the box swing about the grip axis; a box face on the
        chest stops that both ways (chain-dev-v28..v33: hands steady, box swung 38-77 deg)."""
        chain = self.chain
        from humanoid.g1_support_retrieval.oracle.oracle import CONTACT_AHEAD
        robot.ik._set(robot.ref_pos, robot.ref_quat, robot.target())
        P0 = {sd: robot.ik.hand_point(sd, "palm").copy() for sd in SIDES}
        R0 = {sd: robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3).copy() for sd in SIDES}
        c0 = np.mean([P0[sd] + R0[sd] @ np.array([CONTACT_AHEAD, 0.0, 0.0]) for sd in SIDES], axis=0)
        elev = float(np.degrees(np.arcsin(np.clip(R0["left"][2, 0], -1, 1))))
        # stay at the carry angle: the box hangs on the grip axis with its rest angle (~55 deg) just
        # below the hands' 60 deg, so gravity turns its near top edge into the chest (blocked) and
        # turning away lifts it against gravity. Turned to 90 deg, gravity pulled it off the chest
        # and it swung back down and slipped (chain-dev-v36).
        dtheta = np.radians(chain.args.hug_deg - elev)
        yaw = Rotation.from_quat(robot.ref_quat[[1, 2, 3, 0]]).as_euler("xyz")[2]
        Rz = Rotation.from_euler("z", yaw).as_matrix()
        c1 = robot.ref_pos + Rz @ np.array([chain.args.hug_ahead, 0.0, chain.args.hug_up])
        axis = Rz @ np.array([0.0, 1.0, 0.0])
        grip = {"offset": 0.0, "f": None, "press": 0.0}

        def tasks_for(a, press):
            Rd = Rotation.from_rotvec(-axis * dtheta * a).as_matrix()
            c = c0 + (c1 - c0) * a - Rz @ np.array([press, 0.0, 0.0])
            out = {}
            for sd in SIDES:
                inward = Rz @ np.array([0.0, -1.0 if sd == "left" else 1.0, 0.0])
                out[sd] = ("palm", c + Rd @ (P0[sd] - c0) + inward * grip["offset"], Rd @ R0[sd])
            return out

        def servo():
            f = robot.hand_forces(chain.k)
            mean = 0.5 * sum(abs(float(f[sd][1])) for sd in SIDES)
            grip["f"] = mean if grip["f"] is None else 0.8 * grip["f"] + 0.2 * mean
            grip["offset"] = float(np.clip(grip["offset"] + np.clip((chain.args.carry_grip - grip["f"]) * 2e-5, -4e-4, 4e-4),
                                           -0.01, 0.01))

        n = int(chain.args.hug_seconds / T.CONTROL_DT)
        for k in range(1, n + 1):
            servo()
            robot.reach(tasks_for(smooth(k / n), 0.0), rate=1.0)
            if not robot.step():
                raise ValueError("episode ended while hugging")
        # press in until the chest carries ~3 N (<= 6 cm, 3 s)
        for k in range(150):
            servo()
            if self.torso_force(robot) >= 3.0:
                break
            grip["press"] = min(grip["press"] + 0.01 * T.CONTROL_DT, 0.06)
            robot.reach(tasks_for(1.0, grip["press"]), rate=1.0)
            if not robot.step():
                raise ValueError("episode ended while hugging")
        bp, bq = robot.box_state(chain.k)
        tilt = float(np.degrees(np.arccos(np.clip(1 - 2 * (bq[1] ** 2 + bq[2] ** 2), -1, 1))))
        f = robot.hand_forces(chain.k)
        info = dict(box=np.round(bp, 3).tolist(), tilt=round(tilt, 1), press_m=round(grip["press"], 3),
                    torso_N=round(self.torso_force(robot), 1), palms_N={sd: round(abs(float(f[sd][1])), 1) for sd in SIDES})
        chain.report["stages"]["hug"] = info
        chain.event("hug", **info)
        return min(abs(float(f[sd][1])) for sd in SIDES) > 2.0

    def arm_report(self, robot):
        """Left-arm joints: (reference - measured, |control force| / effort cap) where it matters."""
        names = ["shoulder_pitch", "shoulder_roll", "shoulder_yaw", "elbow", "wrist_roll", "wrist_pitch", "wrist_yaw"]
        names = [f"{sd}_{n}" for sd in SIDES for n in names]
        idx = [T.JOINT_NAMES.index(f"{n}_joint") for n in names]
        ref = robot.target()
        meas = robot.joints()
        force = self.cpu(self.r.get_dofs_control_force([self.env.dofs[i] for i in idx]))
        cap = self.chain_caps[idx] if hasattr(self, "chain_caps") else self.chain.p["effort"].cpu().numpy()[idx]
        return {n: [round(float(ref[i] - meas[i]), 3), round(float(abs(f) / c), 2)] for n, i, f, c in zip(names, idx, force, cap)
                if abs(ref[i] - meas[i]) > 0.02 or abs(f) / c > 0.8}

    def grip_move(self, robot, P0, R0, c0, waypoints, servo_on=True):
        """Move both palms as one rigid grip: waypoints [(centre, fingers-up deg change, open m,
        seconds[, waist yaw rad])], interpolated smoothly; common-mode squeeze servo while holding.
        A given waist yaw is ramped and held by the IK (the IK's own choice of waist yaw flipped
        sign from step to step on the stool, see StoolRobot)."""
        chain = self.chain
        yaw = Rotation.from_quat(robot.ref_quat[[1, 2, 3, 0]]).as_euler("xyz")[2]
        Rz = Rotation.from_euler("z", yaw).as_matrix()
        axis = Rz @ np.array([0.0, 1.0, 0.0])
        st = getattr(self, "_grip", None) or {"offset": 0.0, "f": None, "c": c0.copy(), "deg": 0.0, "open": 0.0}
        self._grip = st
        st.setdefault("waist", None)
        for centre, deg, open_m, seconds, *waist in waypoints:
            c_a, d_a, o_a = st["c"].copy(), st["deg"], st["open"]
            w_a = st["waist"] if st["waist"] is not None else float(robot.q_ref[T.JOINT_NAMES.index("waist_yaw_joint")])
            w_b = waist[0] if waist else st["waist"]
            n = max(1, int(seconds / T.CONTROL_DT))
            for k in range(1, n + 1):
                u = smooth(k / n)
                st["c"], st["deg"], st["open"] = c_a + (np.asarray(centre) - c_a) * u, d_a + (deg - d_a) * u, o_a + (open_m - o_a) * u
                if w_b is not None:
                    st["waist"] = w_a + (w_b - w_a) * u
                    robot.ik.set_limit("waist_yaw_joint", st["waist"] - 0.01, st["waist"] + 0.01)
                if servo_on and st["open"] <= 0.0:
                    f = robot.hand_forces(chain.k)
                    mean = 0.5 * sum(abs(float(f[sd][1])) for sd in SIDES)
                    st["f"] = mean if st["f"] is None else 0.8 * st["f"] + 0.2 * mean
                    st["offset"] = float(np.clip(st["offset"] + np.clip((chain.args.carry_grip - st["f"]) * 2e-5, -4e-4, 4e-4),
                                                 -0.01, 0.01))
                Rd = Rotation.from_rotvec(-axis * np.radians(st["deg"])).as_matrix()
                tasks = {}
                for sd in SIDES:
                    inward = Rz @ np.array([0.0, -1.0 if sd == "left" else 1.0, 0.0])
                    tasks[sd] = ("palm", st["c"] + Rd @ (P0[sd] - c0) + inward * (st["offset"] - st["open"]), Rd @ R0[sd])
                err = robot.reach(tasks, rate=1.0)
                if k % 10 == 0:
                    bp, bq = robot.box_state(chain.k)
                    f = robot.hand_forces(chain.k)
                    robot.ik._set(robot.pos, robot.quat, robot.joints())
                    gap_m = float(np.linalg.norm(robot.ik.hand_point("left", "palm") - robot.ik.hand_point("right", "palm")))
                    chain.report.setdefault("place_trace", []).append(dict(
                        t=round(self.t, 2), c=np.round(st["c"], 3).tolist(), deg=round(st["deg"], 1), open=round(st["open"], 3),
                        box=np.round(bp, 3).tolist(), tilt=round(float(np.degrees(np.arccos(np.clip(1 - 2 * (bq[1] ** 2 + bq[2] ** 2), -1, 1)))), 1),
                        force={sd: round(abs(float(f[sd][1])), 1) for sd in SIDES}, palm_gap=round(gap_m, 3),
                        ik_err={sd: round(v, 3) for sd, v in err.items()},
                        arm=self.arm_report(robot),
                        other=sorted({n for n, _, fc in robot.box_contacts if "hand" not in n and np.linalg.norm(fc) > 0.5})))
                if not robot.step():
                    raise ValueError("episode ended while placing the box")

    def place_on_board(self, robot):
        """Put the held box on the board below, beside the stool (relay_dy to the side, relay_in
        behind the cabinet front), so it can be taken again from the floor: carrying it down the
        stool between two palms, the box worked loose (chain-dev-v19..v40)."""
        chain, a = self.chain, self.chain.args
        from humanoid.g1_support_retrieval.oracle.oracle import CONTACT_AHEAD
        d, w, h = T.TOP_SIZES[chain.k]
        variant = T.CABINET_VARIANTS[int(self.env.core.cabinet[0])]
        shelf = float(self.env.core.shelf_height[0])
        board = max(z for z in T.CABINET_META[variant]["levels_top_down"] if z < shelf - 0.05)
        target = np.array([T.CABINET_X_FRONT + a.relay_in, chain.y0 + a.relay_dy, board + h / 2 + 0.003])
        robot.ik._set(robot.ref_pos, robot.ref_quat, robot.target())
        P0 = {sd: robot.ik.hand_point(sd, "palm").copy() for sd in SIDES}
        R0 = {sd: robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3).copy() for sd in SIDES}
        c0 = np.mean([P0[sd] + R0[sd] @ np.array([CONTACT_AHEAD, 0.0, 0.0]) for sd in SIDES], axis=0)
        elev = float(np.degrees(np.arcsin(np.clip(R0["left"][2, 0], -1, 1))))
        out_x = min(c0[0], T.CABINET_X_FRONT - d / 2 - 0.03)
        chain.event("place:start", board=board, target=np.round(target, 3).tolist(), from_deg=round(elev, 1))
        self._grip = None
        # sideways only once the box is out over the board, arms reaching forward: moved aside close to
        # the body, the right forearm crossed the chest and the box dropped (chain-relay-v5)
        self.grip_move(robot, P0, R0, c0, [
            ((out_x, c0[1], target[2] + 0.04), -elev, 0.0, 4.0),            # level and down, outside
            ((target[0], c0[1], target[2] + 0.05), -elev, 0.0, 3.0, a.relay_waist / 2),   # in over the board
            ((target[0], target[1], target[2] + 0.05), -elev, 0.0, 3.0, a.relay_waist),   # aside, waist turned
            ((target[0], target[1], target[2] - 0.005), -elev, 0.0, 2.0),    # down on to it
            ((target[0], target[1], target[2] - 0.005), -elev, 0.0, 0.5),
        ])
        self.grip_move(robot, P0, R0, c0, [
            ((target[0], target[1], target[2] - 0.005), -elev, 0.03, 1.0),   # open the palms
            ((T.CABINET_X_FRONT - 0.18, target[1], target[2] + 0.06), -elev, 0.03, 3.0),   # hands out
        ], servo_on=False)
        for _ in range(25):
            if not robot.step():
                raise ValueError("episode ended after placing the box")
        bp, bq = robot.box_state(chain.k)
        tilt = float(np.degrees(np.arccos(np.clip(1 - 2 * (bq[1] ** 2 + bq[2] ** 2), -1, 1))))
        f = robot.hand_forces(chain.k)
        on_board = abs(bp[2] - (board + h / 2)) < 0.015 and bp[0] > T.CABINET_X_FRONT + 0.01 and tilt < 8.0
        free = max(abs(float(f[sd][1])) for sd in SIDES) < 1.0
        info = dict(box=np.round(bp, 3).tolist(), tilt=round(tilt, 1), board=board, on_board=bool(on_board), hands_free=bool(free))
        chain.report["stages"]["place"] = info
        chain.event("place:end", **info)
        if not (on_board and free):
            raise ValueError("box not left on the board below")
        chain.relay_board = board
        # Joint-space return from the shelf reaches farther forward midway
        # through the elbow rotation. Withdraw first so the fingers cannot sweep
        # through the 0.90 m board while the arms fold back.
        self.grip_move(robot, P0, R0, c0, [
            ((T.CABINET_X_FRONT - 0.34, target[1], target[2] + 0.06), -elev, 0.03, 2.5),
        ], servo_on=False)
        chain.event("place:hands_retracted", cabinet_contacts=sum(
            float(np.linalg.norm(f)) for _, other, f, _ in chain.hand_env_contacts(robot)
            if "cabinet" in other))
        # arms back to the climb's pose (3 s): from the placing pose, reaching forward and aside,
        # the step-down re-plan found the right shoulder in the torso and the reversed climb lost
        # the stance in down_land_right (chain-relay-v6)
        robot.q_ref[:] = robot.target()
        robot.hands = {sd: None for sd in SIDES}
        arms0 = robot.q_ref[12:].copy()
        arms1 = np.asarray(self.climb[0][-1])[self.p.qids[12:]]
        n = int(3.0 / T.CONTROL_DT)
        for k in range(1, n + 1):
            robot.q_ref[12:] = arms0 + (arms1 - arms0) * smooth(k / n)
            if not robot.step():
                raise ValueError("episode ended bringing the arms back")
        for _ in range(25):
            if not robot.step():
                raise ValueError("episode ended bringing the arms back")
        measured, velocity = self.state()
        ref = robot.q_stand
        drift = float(np.linalg.norm(measured[:2] - ref[:2]))
        speed = float(np.linalg.norm(velocity[:2]))
        chain.event("place:arms_returned", root_drift=drift, speed=speed)
        if drift > 0.04 or speed > 0.05:
            raise ValueError("unstable stance after returning the arms")
        robot.ik.set_limit("waist_yaw_joint", -0.05, 0.05)
        self._grip = None

    def step_down(self, robot):
        """The executed climb backwards, arms holding the box (their joint references fixed,
        the hand-box contact forces fed to the QP as external forces)."""
        chain = self.chain
        qs, times, labels = self.climb
        # Squeeze harder before stepping down: the arm references stay fixed from here on (no
        # force servo), and with ~19 N a side the box slid out of the hands when the second
        # foot came down (chain-dev-v19). Palms a few mm further in, along their normals.
        if chain.args.extra_squeeze > 0:
            robot.ik._set(robot.ref_pos, robot.ref_quat, robot.target())
            hold = {sd: (robot.ik.hand_point(sd, "palm").copy(),
                         robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3).copy()) for sd in SIDES}
            yaw_axis = Rotation.from_quat(robot.ref_quat[[1, 2, 3, 0]]).as_matrix()[:, 1]   # base left
            for i in range(50):
                a = min(1.0, (i + 1) / 40)
                tasks = {sd: ("palm", hold[sd][0] - (1 if sd == "left" else -1) * yaw_axis * chain.args.extra_squeeze * a,
                              hold[sd][1]) for sd in SIDES}
                robot.reach(tasks, rate=1.0)
                if not robot.step():
                    raise ValueError("episode ended while tightening the grip")
            f = robot.hand_forces(chain.k)
            chain.report["stages"]["tighten"] = {sd: round(abs(float(f[sd][1])), 1) for sd in SIDES}
        if chain.args.hug and not self.hug(robot):
            raise ValueError("box lost while hugging it to the chest")
        upper = robot.target()[12:]
        # Re-plan the climb with the arms as they hold the box now (the planner's IK keeps the
        # centre of mass over the support foot with this upper body), then play it backwards:
        # the executed climb with the holding arms pasted in put the CoM past the edge of the
        # left foot on the stool and the robot fell off sideways (chain-dev-v11).
        q0 = qs[0].copy()
        q0[self.p.qids[12:]] = upper
        try:
            plan = self.p.plan(initial=q0)
            for pose in plan["qpos"]:
                self.collision_check(pose)
            qs, times, labels = plan["qpos"], plan["time"], plan["phase"]
            chain.event("stepdown:replanned", seconds=round(float(times[-1]), 1))
        except ValueError as exc:
            chain.event("stepdown:replan_failed", error=str(exc)[:200])
        rq = qs[::-1].copy()
        rt = (times[-1] - times[::-1]) * chain.args.stepdown_slow
        rl = list(labels[:-1][::-1]) + ["end"]      # interval j of the reversal = original interval n-2-j
        q_now, _ = self.state()
        rq[:, self.p.qids[12:]] = upper
        start = q_now.copy()
        start[self.p.qids[12:]] = upper
        rq = np.vstack([start, rq])
        rt = np.r_[0.0, rt + 2.0]
        rl = ["blend"] + rl
        # palm targets in the frame of the reference base: re-solved every tick for the current
        # reference base, with a common-mode squeeze servo on the mean hand force (fixed arm
        # references let the grip force drift while the body moved)
        robot.ik._set(robot.ref_pos, robot.ref_quat, robot.target())
        # hands fixed in the yaw-only frame of the base: the box stays level and just translates
        # while the pelvis pitches and rolls (in the pelvis frame the hands swung the box about
        # the grip axis, where a two-palm squeeze is weakest, and it slipped out: chain-dev-v28..v31)
        frame = {"kind": "pelvis" if chain.args.hug else "yaw"}

        def yaw_frame(quat):
            if frame["kind"] == "pelvis":     # rigid with the pelvis
                return Rotation.from_quat(quat[[1, 2, 3, 0]]).as_matrix()
            return Rotation.from_euler("z", Rotation.from_quat(quat[[1, 2, 3, 0]]).as_euler("xyz")[2]).as_matrix()

        def rebase(kind):
            """Re-express the current palm targets in another frame of the reference base."""
            robot.ik._set(robot.ref_pos, robot.ref_quat, robot.target())
            frame["kind"] = kind
            Rb = yaw_frame(robot.ref_quat)
            for sd in SIDES:
                palm_rel[sd] = (Rb.T @ (robot.ik.hand_point(sd, "palm") - robot.ref_pos),
                                Rb.T @ robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3))
            squeeze["offset"] = 0.0
            squeeze["ramp"] = 1.0
            squeeze["lift_done"] = True
        Rb0 = yaw_frame(robot.ref_quat)
        palm_rel = {sd: (Rb0.T @ (robot.ik.hand_point(sd, "palm") - robot.ref_pos),
                         Rb0.T @ robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3)) for sd in SIDES}
        squeeze = {"offset": 0.0, "f": None, "ramp": 0.0}

        def hold_box(q_local):
            w = self.world_pose(q_local)
            robot.ref_pos, robot.ref_quat = w[:3].copy(), w[3:7].copy()
            robot.ref_legs = q_local[self.p.qids[:12]].copy()
            Rb = yaw_frame(robot.ref_quat)
            f = robot.hand_forces(chain.k)
            mean = 0.5 * sum(abs(float(f[sd][1])) for sd in SIDES)
            squeeze["f"] = mean if squeeze["f"] is None else 0.8 * squeeze["f"] + 0.2 * mean
            squeeze["offset"] = float(np.clip(squeeze["offset"] + np.clip((chain.args.carry_grip - squeeze["f"]) * 2e-5, -4e-4, 4e-4),
                                              -0.01, 0.01))
            if chain.args.hug:         # keep ~3 N on the chest
                squeeze["press"] = float(np.clip(squeeze.get("press", 0.0) + np.clip((3.0 - self.torso_force(robot)) * 2e-5,
                                                                                     -2e-4, 2e-4), -0.02, 0.02))
            # box higher (and a little further out) relative to the base: stepping off the stool the
            # left knee comes up above the pelvis and knocked the box out of the hands (chain-dev-v21)
            lift = np.array([chain.args.stepdown_box_out, 0.0, chain.args.stepdown_box_up]) * squeeze["ramp"]
            if chain.args.hug or squeeze.get("lift_done"):     # already included in palm_rel
                lift = np.zeros(3)
            squeeze["ramp"] = min(1.0, squeeze["ramp"] + T.CONTROL_DT / 3.0)
            tasks = {}
            for sd in SIDES:
                rel, Rrel = palm_rel[sd]
                inward = np.array([0.0, -1.0 if sd == "left" else 1.0, 0.0])
                chest = np.array([-squeeze.get("press", 0.0), 0.0, 0.0])
                tasks[sd] = ("palm", robot.ref_pos + Rb @ (rel + inward * squeeze["offset"] + lift + chest), Rb @ Rrel)
            robot.reach(tasks, rate=1.0)
            if robot.steps % 10 == 0:
                bp, bq = robot.box_state(chain.k)
                tilt = float(np.degrees(np.arccos(np.clip(1 - 2 * (bq[1] ** 2 + bq[2] ** 2), -1, 1))))
                robot.s = self.env.state()
                robot.ik._set(robot.pos, robot.quat, robot.joints())
                elev = {sd: round(float(np.degrees(np.arcsin(np.clip(robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3)[2, 0], -1, 1)))), 1)
                        for sd in SIDES}
                palm_gap = round(float(np.linalg.norm(robot.ik.hand_point("left", "palm") - robot.ik.hand_point("right", "palm"))), 3)
                chain.report.setdefault("hold_trace", []).append(
                    [round(self.t, 2), round(squeeze["f"], 1), round(squeeze["offset"], 4), *np.round(bp, 3).tolist(),
                     round(tilt, 1), *np.round(robot.ref_pos, 3).tolist(), {sd: round(abs(float(f[sd][1])), 1) for sd in SIDES},
                     elev, palm_gap, sorted({n for n, _, fc in robot.box_contacts if "hand" not in n and np.linalg.norm(fc) > 0.5}),
                     self.cpu(self.env.top_boxes[chain.k].get_ang()).round(2).tolist()])
            robot.steps += 1
            return robot.target()[12:]
        chain.event("stepdown:start", seconds=round(float(rt[-1]), 1))
        # native mode's static feed-forward (force_check) can be infeasible for a frame on one foot
        # with the box held (stopped there in chain-dev-v18): keep the last feasible torques then;
        # the stiff PD and the ankle balance feedback do the balancing
        plain_check = self.p.force_check
        last = {}

        def force_check(*a, **kw):
            try:
                last["tau"] = plain_check(*a, **kw)
            except ValueError:
                chain.report["stepdown_feedforward_reused"] = chain.report.get("stepdown_feedforward_reused", 0) + 1
                if "tau" not in last:
                    raise
            return last["tau"]
        self.p.force_check = force_check
        previous = ""
        shift = np.zeros(2)
        for t in np.arange(0, rt[-1] + 0.001, 0.02):
            i = min(max(np.searchsorted(rt, t, side="right") - 1, 0), len(rt) - 2)
            a = np.clip((t - rt[i]) / (rt[i + 1] - rt[i]), 0, 1)
            q = rq[i] * (1 - a) + rq[i + 1] * a
            q[3:7] /= np.linalg.norm(q[3:7])
            v = np.zeros(self.p.m.nv)
            mujoco.mj_differentiatePos(self.p.m, v, rt[i + 1] - rt[i], rq[i], rq[i + 1])
            phase = str(rl[i])
            support = [0, 1]
            if phase in ("lift_left", "advance_left", "land_left"):
                support = [1]
            if phase in ("lift_right", "advance_right", "land_right"):
                support = [0]
            if phase != previous:
                print("STEPDOWN", phase, round(self.t, 2), "grip", round(squeeze["f"] or 0.0, 1), flush=True)
                previous = phase
            q = q.copy()
            q[self.p.qids[12:]] = hold_box(q) if getattr(self, "carrying", True) else upper
            robot.hand_forces(chain.k)
            # Outer centre-of-mass loop: the QP tracks the configuration only, and on one foot
            # (5-6 cm wide) after the reversed weight transfer the CoM crept outward 3 cm and the
            # robot rolled over (chain-dev-v14, also without the box, -v15). Move the base
            # reference against the CoM error, so the QP's base PD pushes the CoM back.
            if len(support) == 1 and chain.args.com_gain > 0:
                qm, _ = self.state()
                self.p.forward(qm)
                com_meas = self.p.d.subtree_com[1, :2].copy()
                self.p.forward(q)
                com_ref = self.p.d.subtree_com[1, :2].copy()
                shift = np.clip(shift + 0.02 * chain.args.com_gain * (com_ref - com_meas) * 5.0, -0.04, 0.04)
            else:
                shift *= 0.98
            q = q.copy()
            q[:2] += shift
            self.tick(q, v, support, "down_" + phase, chain.args.stepdown_mode,
                      external=self.external_from(robot.box_contacts))
            if int(round(self.t / 0.02)) % 5 == 0 and phase in ("transfer_left_toe_support", "land_left", "lift_right", "advance_right"):
                qm, _ = self.state()
                self.p.forward(qm)
                com = self.p.d.subtree_com[1].copy()
                feet_w = self.p.d.xpos[self.p.feet].copy()
                fz = self.r.get_links_net_contact_force()[0, [self.r.get_link(nm).idx_local for nm in T.FOOT_LINKS], 2].cpu().numpy()
                roll = float(Rotation.from_quat(qm[[4, 5, 6, 3]]).as_euler("xyz")[0])
                ref_com = None
                self.p.forward(q)
                ref_com = self.p.d.subtree_com[1].copy()
                chain.report.setdefault("stepdown_diag", []).append(dict(
                    t=round(self.t, 2), phase=phase, support=support, foot_fz=np.round(fz, 1).tolist(),
                    com_minus_right_foot=np.round(com[:2] - feet_w[1, :2], 3).tolist(),
                    com_minus_left_foot=np.round(com[:2] - feet_w[0, :2], 3).tolist(),
                    ref_com_minus_meas=np.round(ref_com[:2] - com[:2], 3).tolist(), roll=round(roll, 3)))
        # Agile's own standing legs before the hand-over, feet where they are (stiff, 3 s): handed
        # over from the planner's nominal stance, the policy dropped the pelvis 4 cm in 0.2 s and
        # the box slid out of the hands (chain-dev-v24)
        q_now, _ = self.state()
        self.p.forward(q_now)
        feet_ref = self.p.d.xpos[self.p.feet].copy()
        feet_ref[:, 2] = 0.035
        seed = q_now.copy()
        seed[self.p.qids[:12]] = AGILE_LEGS
        try:
            q_goal = self.p.ik(seed, feet_ref, feet_ref[:, :2].mean(axis=0) + np.array([0.04, 0.0]), 0.716, np.zeros((2, 3)))
        except ValueError as exc:
            q_goal = None
            chain.event("agile_stance:ik_failed", error=str(exc)[:200])
        if q_goal is not None and getattr(self, "carrying", True):
            # the box now pitches with the pelvis: Agile's stance pitches it 0.23 rad forward, and
            # holding the box level then asks the waist for -0.23 rad (limit -0.1); the IK twisted
            # the arms and the box flew out (chain-dev-v39)
            w = self.world_pose(q_now)
            robot.ref_pos, robot.ref_quat = w[:3].copy(), w[3:7].copy()
            rebase("pelvis")
        if q_goal is not None:
            n = int(chain.args.agile_stance_seconds / 0.02)
            arms0 = upper.copy()
            arms1 = T.default_joint_pos().numpy()[12:]
            for k in range(1, n + 1):
                u = smooth(k / n)
                q = q_now + (q_goal - q_now) * u
                q[3:7] /= np.linalg.norm(q[3:7])
                if getattr(self, "carrying", True):
                    q[self.p.qids[12:]] = hold_box(q)
                else:                      # empty hands: arms back to the default pose for the walk
                    q[self.p.qids[12:]] = arms0 + (arms1 - arms0) * u
                self.tick(q, np.zeros(self.p.m.nv), [0, 1], "to_agile_stance", "native",
                          external=self.external_from(robot.box_contacts))
            chain.report["stages"]["agile_stance_legs"] = np.round(q_goal[self.p.qids[:12]], 2).tolist()
        chain.t = self.t
        f = robot.hand_forces(chain.k)
        bp, _ = robot.box_state(chain.k)
        feet = [self.cpu(self.r.get_links_pos([self.r.get_link(nm).idx_local]))[0] for nm in T.FOOT_LINKS]
        held = (min(abs(float(f[sd][1])) for sd in SIDES) > 2.0 or chain.args.skip_retrieve
                or not getattr(self, "carrying", True))
        on_floor = max(float(ft[2]) for ft in feet) < 0.12
        chain.report["stages"]["stepdown"] = dict(held=bool(held), on_floor=bool(on_floor),
                                                  feet_z=[round(float(ft[2]), 3) for ft in feet],
                                                  box=np.round(bp, 3).tolist(),
                                                  forces={sd: round(abs(float(f[sd][1])), 1) for sd in SIDES})
        chain.event("stepdown:end", held=bool(held), on_floor=bool(on_floor))
        if not (held and on_floor):
            raise ValueError("step down: " + ("box not held" if not held else "feet not on the floor"))
        self.stages.append("stepped_down_with_box")


class Chain:
    def __init__(self, args):
        self.args = args
        self.meta = json.loads((STOOL_DIR / "meta.json").read_text())
        self.stool = Stool(self.meta)
        self.L, self.W, self.H = self.stool.size
        self.report = dict(stages={}, events=[], status="not_started")
        self.t = 0.0
        self.max_effort = self.max_speed = 0.0

    # ------------------------------------------------------------------ scene
    def build(self):
        import genesis as gs
        from humanoid.g1_support_retrieval.genesis_env import G1SupportRetrievalGenesis
        args, H = self.args, self.H

        class StoolScene(G1SupportRetrievalGenesis):
            def reset(scene_self, env_ids=None):
                # A reference demonstration is one physical episode. Preserve
                # terminal state for release/settling evidence instead of the
                # training environment's automatic pose reset.
                if getattr(scene_self, "chain_preserve_terminal", False):
                    return scene_self.obs
                return super().reset(env_ids)

            def _build(scene_self, show_viewer, camera):
                original = gs.Scene.build
                original_add = gs.Scene.add_entity

                def add_entity(scene, *a, **kw):
                    # Genesis includes entity names in its physics-description
                    # digest. Default names contain random UUIDs and cannot be
                    # recreated by a second process, although the physics agrees.
                    kw.setdefault("name", f"g1_chain_entity_{len(scene.entities):03d}")
                    return original_add(scene, *a, **kw)

                def build(scene, *a, **kw):
                    scene_self.stool = scene.add_entity(
                        gs.morphs.URDF(file=str(STOOL_DIR / "stool.urdf"), pos=(-4.0, 2.5, H / 2)),
                        material=gs.materials.Rigid(friction=args.friction))
                    return original(scene, *a, **kw)

                gs.Scene.build = build
                gs.Scene.add_entity = add_entity
                try:
                    super()._build(show_viewer, camera)
                finally:
                    gs.Scene.build = original
                    gs.Scene.add_entity = original_add

        weights = tuple(1.0 if f == "one_support" else 0.0 for f in T.FAMILIES)
        # torsional friction: a two-palm squeeze holds the box through point contacts whose normals
        # are the grip axis; without torsional friction nothing resists spinning about it and the box
        # swung like a pendulum on the grip axis and slipped out (chain-dev-v33: hands steady at 60 deg,
        # box 38-77 deg); real finger pads have contact area
        self.env = env = StoolScene(1, seed=args.seed, camera=True, self_collision=bool(args.self_collision),
                                    torsional_friction=bool(args.torsional_friction),
                                    elliptic_friction=bool(args.elliptic_friction), cfg=T.TaskConfig(
            family_weights=weights, floor_boxes=False, payload_range=(0, 0), strength_range=(1, 1),
            start_jitter_xy=0, start_jitter_yaw=0, episode_length_s=5000.0))
        self.r, self.dev = env.robot, env.device
        env.chain_preserve_terminal = True
        self.report["automatic_reset_disabled"] = True
        core = env.core
        self.k = int(core.target[0])
        s = env.state()
        self.target0 = s.top_pos[0, self.k].cpu().numpy()
        self.y0 = float(self.target0[1])
        self.drop_x = args.drop_x
        self.stool_x0 = self.drop_x - args.carry
        info = dict(family=T.FAMILIES[int(core.family[0])], cabinet=T.CABINET_VARIANTS[int(core.cabinet[0])],
                    target=self.k, target_pos=np.round(self.target0, 3).tolist(), target_size=T.TOP_SIZES[self.k],
                    shelf=float(core.shelf_height[0]), stool_start=[self.stool_x0, self.y0], stool_drop=[self.drop_x, self.y0])
        self.report["scene"] = info
        print("SCENE", json.dumps(info), flush=True)
        self.p = {k: v.to(self.dev) for k, v in T.joint_params().items()}

    def tensor(self, x):
        return torch.as_tensor(np.asarray(x), dtype=torch.float32, device=self.dev)[None]

    @staticmethod
    def cpu(x):
        return x[0].detach().cpu().numpy()

    # ------------------------------------------------------------------ gains
    def stiff_gains(self):
        r, env, p = self.r, self.env, self.p
        r.set_dofs_kp(torch.where(p["dc"], 0.0, p["kp"]), env.dofs)
        r.set_dofs_kv(torch.where(p["dc"], 0.0, p["kd"]), env.dofs)
        r.set_dofs_kp(torch.full((12,), self.args.leg_kp, device=self.dev), env.dofs[:12])
        r.set_dofs_kv(torch.full((12,), self.args.leg_kd, device=self.dev), env.dofs[:12])
        if getattr(self, "active_stage", "") in ("lift", "standup", "setdown"):
            # The 5000 N m/rad waist position servo otherwise retains only
            # 5 N m s/rad damping in loaded crouching transitions.
            # Damp lift and setdown transients while keeping the rated torque cap.
            pitch = T.JOINT_NAMES.index("waist_pitch_joint")
            r.set_dofs_kv(torch.tensor([40.0], device=self.dev), [env.dofs[pitch]])
        r.set_dofs_force_range(-p["effort"], p["effort"], env.dofs)

    def task_gains(self):
        """Back to the task's actuation: the env drives the DC-motor legs by torque itself."""
        r, env, p = self.r, self.env, self.p
        r.set_dofs_kp(torch.where(p["dc"], 0.0, p["kp"]), env.dofs)
        r.set_dofs_kv(torch.where(p["dc"], 0.0, p["kd"]), env.dofs)
        r.set_dofs_force_range(-p["effort"], p["effort"], env.dofs)

    # ------------------------------------------------------------------ video
    def frame(self):
        if getattr(self, "view", "stool") == "room":
            self.env.cam.set_pose(pos=(-0.8, -2.9, 2.9), lookat=(2.0, 0.4, 0.6), up=(0, 0, 1))
        elif getattr(self, "view", "stool") == "shelf2":    # the floor retrieval from the board below
            bp = self.cpu(self.env.top_boxes[self.k].get_pos())
            self.env.cam.set_pose(pos=(bp[0] - 1.25, bp[1] + 0.9, bp[2] + 0.5), lookat=(bp[0] - 0.25, bp[1], bp[2] - 0.1), up=(0, 0, 1))
        elif getattr(self, "view", "stool") == "side2":     # the floor retrieval, from the side
            bp = self.cpu(self.env.top_boxes[self.k].get_pos())
            self.env.cam.set_pose(pos=(bp[0] - 1.7, bp[1] - 1.0, 0.95), lookat=(bp[0] - 0.45, bp[1] + 0.2, 0.6), up=(0, 0, 1))
        elif getattr(self, "view", "stool") == "shelf":     # the retrieval on the stool, close up
            tx, tz = float(self.target0[0]), float(self.target0[2])
            self.env.cam.set_pose(pos=(tx - 1.0, self.y0 + 1.1, tz + 0.35), lookat=(tx - 0.2, self.y0, tz - 0.1), up=(0, 0, 1))
        else:
            x = 0.5 * (self.stool_x0 + T.CABINET_X_FRONT) - 0.3
            self.env.cam.set_pose(pos=(x - 0.6, self.y0 + 2.6, 1.7), lookat=(x + 0.1, self.y0, 0.75), up=(0, 0, 1))
        return self.env.render()[:, :, :3]

    def record(self):
        if self.t >= getattr(self, "_next_audit_sample", 0.0):
            self._next_audit_sample = self.t + 0.20 - 1e-6
            self.update_stool()
            self.report.setdefault("transport_trace", []).append(dict(
                t=round(self.t, 3), stage=getattr(self, "active_stage", "initial"),
                stool=self.stool.pos.tolist(), stool_bottom=float(self.stool.bottom()),
                tilt=float(self.stool.tilt_deg())))
        if self.t >= self.next_frame:
            self.writer.append_data(self.frame())
            self.next_frame += 0.04

    def event(self, name, **kw):
        e = dict(time=round(self.t, 2), stage=name, **kw)
        self.report["events"].append(e)
        with (self.args.out / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(e, default=float) + "\n")
        print("EVENT", json.dumps(e, default=float), flush=True)

    def install_actuator_monitor(self):
        """Observe every physics step, including controllers that call env.step internally."""
        self._audit_effort = torch.zeros(T.NUM_JOINTS, device=self.dev)
        self._audit_speed = torch.zeros(T.NUM_JOINTS, device=self.dev)
        self._audit_stop = torch.zeros(T.NUM_JOINTS, device=self.dev)
        self._audit_position_min = torch.full((T.NUM_JOINTS,), float("inf"), device=self.dev)
        self._audit_position_max = torch.full((T.NUM_JOINTS,), -float("inf"), device=self.dev)
        self._audit_limit_peaks = {}
        ratings = torch.as_tensor(self.physical_effort, device=self.dev, dtype=torch.float32)
        limits = torch.as_tensor(self.physical_joint_limits, device=self.dev, dtype=torch.float32)
        speeds = torch.as_tensor(self.planner.params["vel_limit"], device=self.dev, dtype=torch.float32)
        original = self.env.scene.step

        def monitored(*args, **kwargs):
            result = original(*args, **kwargs)
            force = self.r.get_dofs_control_force(self.env.dofs)[0].abs()
            velocity = self.r.get_dofs_velocity(self.env.dofs)[0].abs()
            position = self.r.get_dofs_position(self.env.dofs)[0]
            self._audit_position_min = torch.minimum(self._audit_position_min, position)
            self._audit_position_max = torch.maximum(self._audit_position_max, position)
            self._audit_effort = torch.maximum(self._audit_effort, force / ratings)
            self._audit_speed = torch.maximum(self._audit_speed, velocity / speeds)
            stop = torch.maximum(limits[:, 0] - position, position - limits[:, 1])
            increasing = (stop > 0.001) & (stop > self._audit_stop)
            if bool(increasing.any()):
                audit_ref = getattr(self, "_audit_current_reference", None)
                audit_ref = self.qref if audit_ref is None else audit_ref
                audit_phase = (getattr(self, "_audit_current_phase", None)
                               or getattr(self, "active_stiff_phase", None))
                measured_q = self.qref.copy()
                measured_q[:3] = self.cpu(self.r.get_pos())
                measured_q[3:7] = self.cpu(self.r.get_quat())
                measured_q[self.planner.qids] = position.detach().cpu().numpy()
                state = self.env.state()
                measured_v = np.zeros(self.planner.m.nv)
                measured_v[:3] = self.cpu(state.root_lin_vel)
                measured_v[3:6] = Rotation.from_quat(measured_q[[4, 5, 6, 3]]).inv().apply(
                    self.cpu(state.root_ang_vel))
                measured_v[self.planner.vids] = self.cpu(state.joint_vel)
                for index in increasing.nonzero().flatten().cpu().tolist():
                    name = T.JOINT_NAMES[index]
                    sample = dict(time=self.t, physics_tick=getattr(self, "_physics_ticks", 0) + 1,
                                  phase=audit_phase,
                                  position=float(position[index]), speed=float(velocity[index]),
                                  reference=(float(audit_ref[self.planner.qids[index]])
                                             if audit_phase else None),
                                  effort=float(force[index]), effort_limit=float(ratings[index]),
                                  overshoot=float(stop[index]))
                    if name not in self._audit_limit_peaks:
                        self.event("actuators:limit_exceeded", joint=name, **{k: v for k, v in sample.items() if k != "time"})
                    audit_velocity = getattr(self, "_audit_current_velocity", None)
                    sample.update(measured_q=measured_q.tolist(), reference_q=audit_ref.tolist(),
                                  measured_generalized_velocity=measured_v.tolist(),
                                  reference_generalized_velocity=(audit_velocity.tolist()
                                                                  if audit_velocity is not None else None))
                    self._audit_limit_peaks[name] = sample
            self._audit_stop = torch.maximum(self._audit_stop, stop)
            self._physics_ticks = getattr(self, "_physics_ticks", 0) + 1
            if self._physics_ticks % 20 == 0 and (self.args.out / "STOP").exists():
                raise RuntimeError("stopped_by_request_file")
            return result

        self.env.scene.step = monitored
        self.report["actuator_monitor_scope"] = "full_episode"

    def install_position_target_limits(self):
        """Keep position targets inside physical stops; do not alter model limits."""
        margin = self.args.position_margin
        bounds = self.physical_joint_limits
        margins = np.array([max(margin, self.args.hand_position_margin) if "hand" in name else margin
                            for name in T.JOINT_NAMES])
        self.position_margins = margins
        count = max(int(i) for i in self.env.dofs) + 1
        lower = torch.full((count,), -float("inf"), device=self.dev)
        upper = torch.full((count,), float("inf"), device=self.dev)
        ids = torch.as_tensor(self.env.dofs, device=self.dev, dtype=torch.long)
        lower[ids] = torch.as_tensor(bounds[:, 0] + margins, device=self.dev, dtype=torch.float32)
        upper[ids] = torch.as_tensor(bounds[:, 1] - margins, device=self.dev, dtype=torch.float32)
        original = self.r.control_dofs_position

        def bounded(position, dofs_idx_local=None, envs_idx=None):
            target = torch.as_tensor(position, device=self.dev, dtype=torch.float32)
            indices = slice(None) if dofs_idx_local is None else dofs_idx_local
            target = torch.maximum(lower[indices], torch.minimum(upper[indices], target))
            return original(target, dofs_idx_local=dofs_idx_local, envs_idx=envs_idx)

        self.r.control_dofs_position = bounded
        self.report["position_target_margin_rad"] = margin
        self.report["hand_position_target_margin_rad"] = self.args.hand_position_margin

    def actuator_report(self):
        peaks = dict(max_effort_ratio=float(self._audit_effort.max()),
                     max_speed_ratio=float(self._audit_speed.max()),
                     max_joint_limit_overshoot=float(self._audit_stop.max()))
        peaks["actuator_checks"] = (peaks["max_effort_ratio"] <= 1.001
                                    and peaks["max_speed_ratio"] <= 1.001
                                    and peaks["max_joint_limit_overshoot"] <= 0.001)
        peaks["joint_limit_overshoots"] = {
            T.JOINT_NAMES[i]: float(value) for i, value in enumerate(self._audit_stop.cpu().tolist())
            if value > 0.001}
        peaks["joint_limit_peak_samples"] = dict(self._audit_limit_peaks)
        peaks["joint_position_extrema"] = {
            name: dict(measured_min=float(low), measured_max=float(high),
                       lower=float(bounds[0]), upper=float(bounds[1]))
            for name, low, high, bounds in zip(T.JOINT_NAMES, self._audit_position_min.cpu().tolist(),
                                               self._audit_position_max.cpu().tolist(), self.physical_joint_limits)}
        return peaks

    # ------------------------------------------------------------------ stiff controller
    def init_stiff(self):
        """Planner, approach references and stiff-controller state for the stool lift (as
        stool_carry/run_stool.py, with the stool on the line y = y0 of the target)."""
        args, stool, meta = self.args, self.stool, self.meta
        L, W, H = self.L, self.W, self.H
        probe = np.array([L, 2 * (stool.rail_y[0] - 0.05), H])
        planner = UnderhandPlanner(probe, self.stool_x0, args.mass)
        self.physical_joint_limits = planner.m.jnt_range[planner.jids].copy()
        self.physical_effort = np.minimum(planner.params["effort"],
                                         planner.m.jnt_actfrcrange[planner.jids, 1]).copy()
        if args.model_torso_mass > 0:
            torso = planner.m.body("torso_link").id
            self.report["model_torso_mass"] = dict(before=float(planner.m.body_mass[torso]), after=args.model_torso_mass)
            planner.m.body_mass[torso] = args.model_torso_mass
            mujoco.mj_setConst(planner.m, planner.d)
        planner.root_lower, planner.root_upper = [-5.0, -5.0, 0.30], [5.0, 5.0, 1.2]
        # The loaded initial lift can deflect the waist about 0.021 rad beyond
        # its IK target. Reserve room below the physical 0.52 rad stop before
        # planning the approach, as in setdown; actuator limits stay unchanged.
        planner.waist_upper = np.array([0.5, 0.47])
        planner.place_box([self.stool_x0, self.y0, H / 2])
        self.planner = planner
        if args.model_torso_mass <= 0:
            sync_planner_model(self)
        self.upright = np.array([fingers_down(np.radians(args.hand_pitch))] * 2)
        mcp_z = meta["outer_rail"]["bottom_z"] - args.below_rail
        q0 = planner.nominal()
        q0[0] = self.stool_x0 - args.gap
        q0[1] = self.y0
        planner.forward(q0)
        self.feet = planner.d.xpos[planner.feet].copy()
        com0 = planner.d.subtree_com[1, :2].copy()
        self.hand_cmd = {s: dict(flex=1.57, distal=0.0, thumb0=0.0, thumb1=args.thumb_up, thumb2=0.0) for s in SIDES}
        probe_q = q0.copy()
        for s in SIDES:
            planner.set_hand(probe_q, s, **self.hand_cmd[s])
        planner.forward(probe_q)
        reach_in = {}
        for i, s in enumerate(SIDES):
            R = planner.d.xmat[planner.hands[i]].reshape(3, 3)
            R_up = Rotation.from_rotvec(self.upright[i]).as_matrix()
            mcp = planner.palms()[i]
            pts = np.vstack([planner.body_points(f"{s}_hand_{f}_{k}_link") for f in ("index", "middle") for k in (0, 1)]
                            + [planner.body_points(f"{s}_hand_thumb_{k}_link") for k in (1, 2)])
            world = ((pts - mcp) @ R) @ R_up.T
            reach_in[s] = float((-SIGN[s] * world[:, 1]).max())
        out = {s: reach_in[s] + args.out_clear for s in SIDES}

        def mcp_target(side, extra, z):
            return np.array([self.stool_x0 + args.hand_x_offset, self.y0 + SIGN[side] * (stool.slat_end + out[side] + extra), z])

        keyframes = [(np.array([mcp_target(s, 0.03, mcp_z + 0.12) for s in SIDES]), 30),
                     (np.array([mcp_target(s, 0.0, mcp_z) for s in SIDES]), 20)]
        q = q0.copy()
        start_hand = {s: dict(flex=0.0, distal=0.0, thumb0=0.0, thumb1=0.0, thumb2=0.0) for s in SIDES}
        planner.forward(q)
        prev = planner.palms().copy()
        rot0 = np.array([Rotation.from_matrix(planner.d.xmat[b].reshape(3, 3)).as_rotvec() for b in planner.hands])
        h0 = q[2]
        refs = [q.copy()]
        total, k_global = sum(n for _, n in keyframes), 0
        for target, n in keyframes:
            for i in range(1, n + 1):
                k_global += 1
                u, g = smooth(i / n), smooth(k_global / total)
                for s in SIDES:
                    planner.set_hand(q, s, **{kk: start_hand[s][kk] + (self.hand_cmd[s][kk] - start_hand[s][kk]) * g
                                              for kk in self.hand_cmd[s]})
                for _ in range(4):
                    try:
                        q, _ = planner.reach(q, self.feet, prev + (target - prev) * u, com0 + np.array([args.com_shift, 0]) * g,
                                             h0 + (args.crouch - h0) * g, rotations=rot0 * (1 - g) + self.upright * g)
                    except ValueError:
                        q = planner.d.qpos.copy()
                    bad = [tuple(map(int, c.geom)) for c in planner.d.contact[: planner.d.ncon] if c.dist < -0.002]
                    if not bad:
                        break
                    for pair in bad:
                        if pair not in planner.clearance_pairs:
                            planner.clearance_pairs.append(pair)
                refs.append(q.copy())
            prev = target
        self.refs = np.array(refs)
        planner.forward(self.refs[-1])
        self.report["approach_mcp_error_m"] = float(np.linalg.norm(planner.palms() - keyframes[-1][0], axis=1).max())
        edge = np.diff(self.refs[:, planner.qids], axis=0) / 0.1
        scale = max(1.0, float(abs(edge).max() / 0.5), float(np.sqrt(abs(np.diff(edge, axis=0) / 0.1).max() / 2)))
        self.ref_times = np.arange(len(self.refs)) * 0.1 * scale
        ctx = StoolContext(planner, stool, args.mass, stool.size)
        ctx.upright = self.upright
        ctx.root_h = self.refs[-1, 2]
        ctx.com_cmd = com0 + np.array([args.com_shift, 0])
        ctx.com_nominal = com0.copy()
        ctx.metrics["stool_start"] = [self.stool_x0, self.y0, H / 2]
        self.ctx = ctx
        self.qref = self.refs[0].copy()
        self.body_q = np.array([planner.qids[i] for i in range(T.NUM_JOINTS) if "hand" not in T.JOINT_NAMES[i]])
        self.hand_adr = {s: [planner.m.jnt_qposadr[j] for j in range(planner.m.njnt)
                             if planner.m.joint(j).name.startswith(s + "_hand")] for s in SIDES}
        self.mapping = {link.idx: planner.m.body(link.name).id for link in self.r.links
                        if link.name in [planner.m.body(i).name for i in range(planner.m.nbody)]}
        # physical effort caps (min of the task's and the G1 model's ratings), as stool_carry: the
        # task allows 300 N m on arms and hands, and a 5 mm extra squeeze then pressed the box with
        # ~200 N a side (stool-demo-v1); the Dex3 fingers are rated 1.4-2.45 N m, wrists 5-25 N m
        if self.args.effort_caps == "physical":
            self.p["effort"] = torch.as_tensor(planner.params["effort"], device=self.dev, dtype=torch.float32)
        self.report["effort_caps"] = ("physical (min of task and G1 model actuator ranges)" if self.args.effort_caps == "physical"
                                      else "task (task_spec: 300 N m on arms and hands)")

    def place_initial(self):
        """The only pose writes: robot standing behind the stool, stool on the floor."""
        r = self.r
        q = self.refs[0]
        r.set_pos(self.tensor(q[:3]), zero_velocity=True)
        r.set_quat(self.tensor(q[3:7]), zero_velocity=True)
        r.set_dofs_position(self.tensor(q[self.planner.qids]), self.env.dofs, zero_velocity=True)
        self.env.stool.set_pos(self.tensor([self.stool_x0, self.y0, self.H / 2]), zero_velocity=True)
        self.env.stool.set_quat(self.tensor([1, 0, 0, 0]), zero_velocity=True)
        if abs(self.args.mass - self.meta["mass_kg"]) > 1e-6:
            self.env.stool.set_mass(self.args.mass)

    def measured_q(self):
        s = self.env.state()
        q = self.qref.copy()
        q[:3] = self.cpu(s.root_pos)
        q[3:7] = self.cpu(s.root_quat)
        q[self.planner.qids] = self.cpu(s.joint_pos)
        return q, s

    def update_stool(self):
        st = self.env.stool
        self.stool.update(self.cpu(st.get_pos()), self.cpu(st.get_quat()), self.cpu(st.get_vel()))

    def stiff_step(self, leg_target, upper_target):
        r, env, p = self.r, self.env, self.p
        bal = getattr(self, "balance", None)
        if bal is not None:
            # carry_walk's balance feedback: ankle pitch/roll target offsets from the base pose and
            # velocity error against the reference (bounded corrective torque through the PD)
            measured, st = self.measured_q()
            qref = self.qref
            angles = (Rotation.from_quat(qref[[4, 5, 6, 3]]).inv() * Rotation.from_quat(measured[[4, 5, 6, 3]])).as_rotvec()
            pos_error = measured[:3] - qref[:3]
            vel = self.cpu(st.root_lin_vel)
            omega = self.cpu(st.root_ang_vel)
            pitch = (450 * pos_error[0] + 80 * vel[0] + 80 * angles[1] + 12 * omega[1]) * self.args.bal_sign[1]
            roll = (-450 * pos_error[1] - 80 * vel[1] + 80 * angles[0] + 12 * omega[0]) * self.args.bal_sign[0]
            weights = np.array([0.5, 0.5])
            if len(bal["support"]) == 1:
                weights[:] = 0.0
                weights[bal["support"][0]] = 1.0
            leg_target = np.array(leg_target, dtype=float).copy()
            if self.args.walk_gravcomp:
                try:
                    ext = self._contacts["generalized"] if getattr(self, "_contacts", None) else None
                    self._ff = self.planner.force_check(qref, np.zeros(self.planner.m.nv), np.zeros(self.planner.m.nv),
                                                        list(bal["support"]), reserve=1.0, external=ext,
                                                        actuated_indices=np.arange(12), box_support=False)
                except ValueError:
                    self.report["walk_ff_infeasible"] = self.report.get("walk_ff_infeasible", 0) + 1
                if getattr(self, "_ff", None) is not None:
                    leg_target += self._ff[:12] / self.args.leg_kp
            # the ankle can only realise a roll/pitch torque the foot supports (~ weight x half the
            # foot width, ~10 N m): carry_walk's 0.03 rad clip (90 N m at kp 3000) rolled the stance
            # foot over its edge in the first footfall (stepwalk-v11)
            clip = self.args.bal_clip
            for leg in range(2):
                leg_target[leg * 6 + 4] += float(np.clip(weights[leg] * pitch / self.args.leg_kp, -clip, clip))
                leg_target[leg * 6 + 5] += float(np.clip(weights[leg] * roll / self.args.leg_kp, -clip, clip))
            jr = self.planner.m.jnt_range[self.planner.jids[:12]]
            leg_target = np.clip(leg_target, jr[:, 0], jr[:, 1])
            self.balance_last = [round(float(pitch), 1), round(float(roll), 1), np.round(pos_error[:2], 3).tolist(), np.round(angles[:2], 3).tolist()]
        for _ in range(4):
            qd = r.get_dofs_velocity(env.dofs)
            upper = torch.minimum(p["effort"][:12], p["saturation"][:12] * (1 - qd[:, :12] / p["vel_limit"][:12]))
            lower = torch.maximum(-p["effort"][:12], p["saturation"][:12] * (-1 - qd[:, :12] / p["vel_limit"][:12]))
            r.set_dofs_force_range(lower[0], upper[0], env.dofs[:12])
            r.control_dofs_position(self.tensor(leg_target), env.dofs[:12])
            r.control_dofs_position(self.tensor(upper_target), env.dofs[12:])
            env.scene.step()
            self.max_effort = max(self.max_effort, float((r.get_dofs_control_force(env.dofs).abs() / p["effort"]).max()))
            self.max_speed = max(self.max_speed, float((r.get_dofs_velocity(env.dofs).abs() / p["vel_limit"]).max()))
        self.t += 0.02
        self.record()

    def setdown_thumb_observation(self, measured, state, contacts):
        """Measured stop/force evidence for the isolated setdown relief experiment."""
        planner, ctx = self.planner, self.ctx
        velocity = self.cpu(state.joint_vel)
        effort = self.cpu(self.r.get_dofs_control_force(self.env.dofs))
        hands = {}
        for side in SIDES:
            index = T.JOINT_NAMES.index(f"{side}_hand_thumb_1_joint")
            direction = -1.0 if side == "left" else 1.0
            actual = float(measured[planner.qids[index]])
            lower, upper = self.physical_joint_limits[index]
            raw_target = float(self.qref[planner.qids[index]])
            clipped = float(np.clip(raw_target, lower+self.position_margins[index],
                                    upper-self.position_margins[index]))
            ext = float(contacts["generalized"][planner.vids[index]])
            force = contacts["groups"].get(side+"_thumb", np.zeros(3))
            reach, below = ctx.finger_metrics(side)
            hands[side] = dict(actual_rad=actual, raw_target_rad=raw_target,
                clipped_position_target_rad=clipped, lower_rad=float(lower), upper_rad=float(upper),
                margin_rad=float(actual-lower if direction < 0 else upper-actual),
                velocity_radps=float(velocity[index]), outward_speed_radps=float(direction*velocity[index]),
                applied_torque_Nm=float(effort[index]), external_torque_Nm=ext,
                outward_torque_Nm=direction*ext, contact_force_N=force.tolist(),
                contact_N=float(np.linalg.norm(force)), finger_support_N=float(ctx.support(side)),
                finger_reach_m=float(reach), finger_below_rail_m=float(below))
        knee_force = {side: np.zeros(3) for side in SIDES}
        raw = self.r.get_contacts(with_entity=self.env.stool)
        raw = {key: value.detach().cpu().numpy() for key, value in raw.items()}
        if raw["link_a"].ndim == 2:
            raw = {key: value[0] for key, value in raw.items()}
        for ci in range(len(raw["link_a"])):
            if "valid_mask" in raw and not raw["valid_mask"][ci]:
                continue
            for suffix in ("a", "b"):
                body = self.mapping.get(int(raw["link_"+suffix][ci]))
                if body is None:
                    continue
                name = planner.m.body(body).name
                for side in SIDES:
                    if name == side+"_knee_link":
                        knee_force[side] += raw["force_"+suffix][ci]
        return hands, {side: force.tolist() for side, force in knee_force.items()}

    def run_stiff(self, plan, label, approach=False, timeout=240.0):
        """The stool_carry control loop: IK references from the phase targets, executed by
        stiff joint position control. Returns "done" or a failure string."""
        args, ctx, planner, stool = self.args, self.ctx, self.planner, self.stool
        current, start, i = None, 0.0, 0
        t0 = self.t
        body_time = 0.0
        thumb_guard = None
        if label == "setdown" and getattr(args, "setdown_thumb_guard", 0):
            from humanoid.g1_support_retrieval.oracle.thumb_guard import ThumbContactGuard
            thumb_guard = ThumbContactGuard(args.min_reach)
        self.stiff_gains()
        while self.t - t0 < timeout:
            measured, s = self.measured_q()
            self.update_stool()
            if thumb_guard is not None:
                # contact_summary's Jacobian must use this measured pose, not
                # the preceding IK reference, for a joint external torque.
                planner.forward(measured)
            contacts = ctx.measure(measured, contact_summary(self.r, self.env.stool, self.mapping, planner))
            planner.forward(measured)
            ctx.feet_meas = planner.d.xpos[planner.feet].copy()
            ctx.com_meas = planner.d.subtree_com[1, :2].copy()
            self._contacts = contacts
            guard_result, guard_row = None, None
            if thumb_guard is not None and current is not None and current.name == "carry":
                hands, knee_forces = self.setdown_thumb_observation(measured, s, contacts)
                guard_result = thumb_guard.update(self.t, hands, stool_vz=float(stool.vel[2]),
                    stool_tilt_deg=float(stool.tilt_deg()), grounded=bool(stool.bottom() < .015))
                guard_row = dict(time=self.t, phase=current.name, phase_age=self.t-start,
                    hands=hands, knee_contact_force_N=knee_forces, **guard_result)
                if guard_result["triggered"] or guard_result["recovered"] or guard_result["failure"]:
                    self.event("setdown:thumb_guard", **guard_result)
                if guard_result["failure"]:
                    self.report.setdefault("setdown_thumb_guard_trace", []).append(guard_row)
                    with (self.args.out / "setdown_thumb_guard_trace.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(guard_row)+"\n")
                    return "thumb_guard:"+guard_result["failure"]
            if (label == "standup" or (label == "setdown" and
                    (current is None or current.name in ("reattach", "carry")) and
                    int(round(self.t / T.CONTROL_DT)) % 5 == 0)):
                # Preserve loaded transition evidence. Logging does not change
                # references or simulator state.
                raw = self.env.stool.get_contacts()
                raw = {key: value[0].detach().cpu().numpy() for key, value in raw.items()}
                names = {link.idx: link.name for link in self.env.scene.rigid_solver.links}
                stool_contacts = []
                for ci in np.flatnonzero(raw["valid_mask"]):
                    force = raw["force_a"][ci]
                    if np.linalg.norm(force) >= 0.2:
                        stool_contacts.append(dict(
                            links=[names.get(int(raw[key][ci]), str(raw[key][ci])) for key in ("link_a", "link_b")],
                            force_a=force.tolist(), point=raw["position"][ci].tolist()))
                row = dict(time=self.t, phase=current.name if current else None,
                           phase_progress=getattr(current, "progress", None),
                           phase_age=self.t - start, measured_q=measured.tolist(), reference_q=self.qref.tolist(),
                           stool=stool.pos.tolist(), stool_rotation=stool.R.tolist(), stool_velocity=stool.vel.tolist(),
                           stool_target=([ctx.box_des[0].tolist(), ctx.box_des[1].tolist()] if ctx.box_des is not None else None),
                           mcp=ctx.mcp_meas.tolist(), track=ctx.track.tolist(), feet=ctx.feet_meas.tolist(),
                           com=ctx.com_meas.tolist(), root_target=ctx.root_h, com_target=ctx.com_cmd.tolist(),
                           effort=self.cpu(self.r.get_dofs_control_force(self.env.dofs)).tolist(),
                           groups={key: value.tolist() for key, value in contacts["groups"].items()},
                           contacts=stool_contacts,
                           hands={side: dict(rel_mcp=hand.rel_mcp.tolist(), rel_rot=hand.rel_rot.tolist(),
                                             fingers=dict(hand.q), servo=hand.servo, attached=hand.attached,
                                             servo_guard=getattr(hand, "setdown_servo_debug", None))
                                  for side, hand in ctx.hands.items()})
                trace_name = "standup_trace" if label == "standup" else "setdown_descent_trace"
                self.report.setdefault(trace_name, []).append(row)
                with (self.args.out / (trace_name + ".jsonl")).open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row) + "\n")
            body_n = float(sum(np.linalg.norm(v) for kk, v in contacts["groups"].items() if kk.endswith("_body")))
            self.report["max_body_contact_N"] = max(self.report.get("max_body_contact_N", 0.0), body_n)
            body_time = body_time + 0.02 if body_n > 10.0 else 0.0
            if body_time > 1.0:
                return "body_contact_with_stool"
            tt = self.t - t0
            if approach and tt < self.ref_times[-1]:
                a = min(np.searchsorted(self.ref_times, tt, side="right") - 1, len(self.ref_times) - 2)
                u = (tt - self.ref_times[a]) / (self.ref_times[a + 1] - self.ref_times[a])
                self.qref = self.refs[a] * (1 - u) + self.refs[a + 1] * u
                self.qref[3:7] /= np.linalg.norm(self.qref[3:7])
            else:
                if ctx.hands is None:
                    ctx.hands = {side: Hand(side, ctx.mcp_meas[j].copy(), self.hand_cmd[side]) for j, side in enumerate(SIDES)}
                    ctx.track = np.zeros((2, 3))
                    ctx.qref = self.qref
                if current is None:
                    if i >= len(plan):
                        self.active_stiff_phase = None
                        return "done"
                    current, start = plan[i], self.t
                    self.active_stiff_phase = current.name
                    self.event(f"{label}:{current.name}")
                    current.start(ctx)
                ctx.qref = self.qref
                if guard_result is not None and guard_result["paused"]:
                    # Freeze both the trajectory clock and Carry's pitch-force
                    # integrator; holding age alone would still rotate the hands.
                    start += T.CONTROL_DT
                    result = None
                else:
                    result = current.step(ctx, self.t - start)
                if result == "done":
                    if getattr(self, "_physics_ticks", 0):
                        checks = self.actuator_report()
                        self.report.setdefault("stiff_phase_actuator_checks", []).append(
                            dict(time=self.t, stage=label, phase=current.name, **checks))
                        self.event("actuators:stiff_phase_end", completed_stage=label,
                                   phase=current.name, **{key: checks[key] for key in
                                   ("actuator_checks", "max_effort_ratio", "max_speed_ratio", "max_joint_limit_overshoot")})
                    i, current = i + 1, None
                elif result:
                    return f"{current.name}:{result}"
                targets, rotations = [], []
                for side in SIDES:
                    h = ctx.hands[side]
                    n = ctx.face_normal(side)
                    step = 0.0
                    if h.servo:
                        part, force = h.servo[:2]
                        f = ctx.normal(side, part) if part else ctx.total_normal(side)
                        step = 0.0004 if (f < 0.3 and h.approach) else float(np.clip((force - f) * args.servo_gain, -0.0004, 0.0004))
                        if len(h.servo) > 2 and h.servo[2] == "max":
                            step = min(0.0, step)
                    excess = ctx.total_normal(side) - args.max_squeeze
                    if excess > 0:
                        step -= min(0.002, 0.0004 + 0.0001 * excess)
                    if h.attached:
                        if label == "setdown" and hasattr(h, "setdown_servo_anchor"):
                            # An excess-force correction used to add up to 2 mm
                            # every tick, outrunning the arm and withdrawing the
                            # finger support while lowering continued. Bound the
                            # total correction and do not integrate farther ahead
                            # of the actual hand in that correction's direction.
                            requested_step = step
                            step = float(np.clip(step, -0.0001, 0.0001))
                            pos, rotation = ctx.box_reference()
                            outward = rotation[:, 1] * SIGN[side]
                            target = pos + rotation @ h.rel_mcp
                            normal_error = float((target - ctx.mcp_meas[SIDES.index(side)]) @ outward)
                            blocked = ((step < 0.0 and normal_error > 0.002)
                                       or (step > 0.0 and normal_error < -0.002))
                            if blocked:
                                step = 0.0
                            before = h.rel_mcp.copy()
                            h.rel_mcp -= np.array([0.0, SIGN[side], 0.0]) * step
                            anchor = h.setdown_servo_anchor
                            h.rel_mcp[1] = np.clip(h.rel_mcp[1], anchor[1] - 0.01, anchor[1] + 0.01)
                            if thumb_guard is not None:
                                before_offset = float((before[1]-anchor[1])*SIGN[side])
                                proposed_offset = float((h.rel_mcp[1]-anchor[1])*SIGN[side])
                                protected_offset = thumb_guard.constrain_offset(side, proposed_offset,
                                    before_offset, normal_error)
                                h.rel_mcp[1] = anchor[1]+SIGN[side]*protected_offset
                            h.setdown_servo_debug = dict(
                                requested_step_m=float(requested_step),
                                applied_step_m=float((before[1] - h.rel_mcp[1]) * SIGN[side]),
                                normal_target_error_m=normal_error, tracking_blocked=bool(blocked),
                                outward_offset_m=float((h.rel_mcp[1] - anchor[1]) * SIGN[side]))
                        else:
                            h.rel_mcp -= np.array([0.0, SIGN[side], 0.0]) * step
                        mcp, rot = ctx.attached_target(side)
                    else:
                        h.mcp -= n * step
                        h.mcp[2] = h.z
                        mcp, rot = h.mcp, Rotation.from_matrix(ctx.hand_rotation(side)).as_rotvec()
                    targets.append(mcp)
                    rotations.append(rot)
                mcp_cmd, rot_cmd = np.array(targets), np.array(rotations)
                ctx.targets = mcp_cmd
                free = np.array([[0.0, 0.0, 1.0] if ctx.hands[sd].attached else [1.0, 1.0, 1.0] for sd in SIDES])
                if guard_result is None or not guard_result["paused"]:
                    ctx.track = np.clip(ctx.track + free * np.clip(args.track_gain * (mcp_cmd - ctx.mcp_meas), -0.0005, 0.0005),
                                        -0.03, 0.03)
                mcp_cmd = mcp_cmd + ctx.track
                carried = float(np.clip(ctx.support("left") + ctx.support("right"), 0.0, args.mass * G))
                robot_weight = float(planner.m.body_subtreemass[1]) * G
                com_target = ctx.com_cmd - carried / robot_weight * (stool.pos[:2] - ctx.com_cmd)
                try:
                    qnext, _ = planner.reach(self.qref, self.feet, mcp_cmd, com_target, ctx.root_h, rotations=rot_cmd)
                except ValueError as exc:
                    qnext = planner.d.qpos.copy()
                    if "palms" not in str(exc):
                        return "online_" + str(exc)
                qref = self.qref
                delta = float(abs(qnext[self.body_q] - qref[self.body_q]).max())
                alpha = min(1.0, 0.6 * 0.02 / max(delta, 1e-9), 0.003 / max(1e-9, float(np.linalg.norm(qnext[:3] - qref[:3]))))
                new = qref.copy()
                new[:3] = qref[:3] + (qnext[:3] - qref[:3]) * alpha
                rq, rn = Rotation.from_quat(qref[[4, 5, 6, 3]]), Rotation.from_quat(qnext[[4, 5, 6, 3]])
                new[3:7] = (rq * Rotation.from_rotvec(alpha * (rq.inv() * rn).as_rotvec())).as_quat()[[3, 0, 1, 2]]
                new[self.body_q] = qref[self.body_q] + (qnext[self.body_q] - qref[self.body_q]) * alpha
                for side in SIDES:
                    goal = new.copy()
                    planner.set_hand(goal, side, **ctx.hands[side].q)
                    adr = self.hand_adr[side]
                    new[adr] = qref[adr] + np.clip(goal[adr] - qref[adr], -0.012, 0.012)
                self.qref = new
            if guard_row is not None:
                guard_row["reference_updates"] = {side: dict(
                    rel_mcp=ctx.hands[side].rel_mcp.tolist(),
                    servo_guard=getattr(ctx.hands[side], "setdown_servo_debug", None)) for side in SIDES}
                self.report.setdefault("setdown_thumb_guard_trace", []).append(guard_row)
                with (self.args.out / "setdown_thumb_guard_trace.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(guard_row)+"\n")
            self.stiff_step(self.qref[planner.qids[:12]].copy(), self.qref[planner.qids[12:]])
            if int(round(self.t / 0.02)) % 50 == 0:
                print("STATE", round(self.t, 2), label, "stool", np.round(stool.pos, 3).tolist(), "tilt", round(stool.tilt_deg(), 1),
                      "bottom", round(stool.bottom(), 3), "sup", {k: round(ctx.support(k), 1) for k in SIDES},
                      "root", np.round(measured[:3], 3).tolist(), flush=True)
            err = float(np.linalg.norm((Rotation.from_quat(self.qref[[4, 5, 6, 3]]).inv()
                                        * Rotation.from_quat(measured[[4, 5, 6, 3]])).as_rotvec()))
            if err > 0.6 or measured[2] < 0.2:
                return "loss_of_posture"
        return "timeout"

    # ------------------------------------------------------------------ stages
    def lift_and_stand(self):
        a = self.args
        f = a.insert_force
        lift = [
            Engage("both", contacts=[("left", None, f), ("right", None, f)]),
            SetServo("both", servo={"left": None, "right": (None, f)}, seconds=0.3),
            CheckGrip("both", reach=a.min_reach, support=0.0, seconds=0.5),
            Attach("both", freeze=True),
            Carry("both", offset=[0, 0, a.lift], root=a.lift_root, seconds=7.0, pitch_gain=0.02),
            CheckGrip("both", reach=a.min_reach, support=0.3, seconds=0.5),
            StableHold("both", seconds=2.0, clearance=a.lift * 0.6, tilt=8.0, speed=0.05),
        ]
        status = self.run_stiff(lift, "lift", approach=True)
        self.report["stages"]["lift"] = dict(status=status, metrics={k: v for k, v in self.ctx.metrics.items() if k.startswith("hold")})
        if status != "done":
            return status
        if a.save_checkpoint and not a.resume_checkpoint:
            checkpoint_path = a.save_checkpoint.with_name(a.save_checkpoint.stem + "-lift" + a.save_checkpoint.suffix)
            try:
                save_chain_checkpoint(self, checkpoint_path, stage="lift")
            except Exception as exc:
                self.report["checkpoint_error"] = dict(type=type(exc).__name__, message=str(exc))
                self.event("checkpoint:failed", **self.report["checkpoint_error"])
            else:
                self.event("checkpoint:saved", path=str(checkpoint_path), checkpoint_stage="lift", diagnostic_only=True)
        if a.stop_after == "lift":
            return status
        return self.stand_loaded()

    def stand_loaded(self):
        """Stand from the completed physical lift, including checkpoint restores."""
        a = self.args
        # Stand up with the stool: straight up past the knees, then in front of the chest with the
        # pelvis upright. Upright, the fingers-down hands reach 0.30-0.35 m ahead at 0.85-1.0 m
        # (upper-body IK); the body is 0.06-0.08 m deep above 0.7 m but the knees reach 0.17-0.26 m
        # forward lower down, so the hands go 0.33 m ahead of the feet at 0.95 m: offline the pelvis
        # stays upright (pitch 0.01, waist 0.05), the stool 0.35 m ahead with its bottom at 0.77 m
        # (chain-v1: held 0.27 m ahead with the bottom at 0.55 m it jammed on the thighs).
        planner = self.planner
        nom = planner.nominal()
        planner.forward(nom)
        nom_off = float(planner.d.xpos[planner.feet][:, 0].mean() - nom[0])
        pelvis_end = float(self.feet[:, 0].mean() - nom_off)
        rise = 0.5 * (STAND - self.ctx.root_h)
        # Raising the stool straight up with its long forward lever overloaded
        # the waist before the torso could straighten. Bring it closer first,
        # keeping the pelvis low; retain the original final hand destination.
        compact_dz = min(0.08, max(0.0, a.stand_up_dz[0]))
        compact = WeightedCarry("both", offset=[-0.06, 0, compact_dz], root=0.0,
                                seconds=4.0, pitch_gain=0.02, w=(0.2, 0.2))
        compact.name = "compact_lift"
        stand = [
            compact,
            CheckGrip("both", reach=a.min_reach, support=0.3, seconds=0.5),
            WeightedCarry("both", offset=[0, 0, a.stand_up_dz[0] - compact_dz], root=rise,
                          seconds=8.0, pitch_gain=0.02, w=(0.2, 5.0)),
            # ... and the centre of mass (with the stool) back over the standing one: the lift keeps it
            # 4 cm forward (com_shift), and handed over like that the walking policy ran away
            # forward at up to 0.75 m/s (chain-v3, chain-v4)
            WeightedCarry("both", mcp=(pelvis_end + a.carry_ahead, a.carry_mcp_z), root=rise, seconds=16.0,
                          pitch_gain=0.02, w=(5.0, 50.0), com=[a.carry_com, 0.0], joint_step_limit=0.012),
        ] + ([Upright("both", seconds=6.0, pelvis_pitch=a.upright_pelvis, waist_pitch=a.upright_waist,
                     pelvis_roll=0.01)] if a.upright else []) + [
            StableHold("both", seconds=2.0, clearance=0.5, tilt=10.0, speed=0.05),
        ]
        previous_step_limit = getattr(planner, "reach_joint_step_limit", None)
        try:
            status = self.run_stiff(stand, "standup")
        finally:
            if previous_step_limit is None:
                planner.__dict__.pop("reach_joint_step_limit", None)
            else:
                planner.reach_joint_step_limit = previous_step_limit
        self.update_stool()
        measured, _ = self.measured_q()
        self.report["stages"]["standup"] = dict(status=status, stool=np.round(self.stool.pos, 3).tolist(),
                                                bottom=round(self.stool.bottom(), 3), root=np.round(measured[:3], 3).tolist())
        return status

    def lift_in_place(self):
        """stool_carry/run_stool.py's verified plan, unchanged: lift, hold 3 s, set down where
        it was, hands out, stand up."""
        a = self.args
        f = a.insert_force
        plan = [
            Engage("both", contacts=[("left", None, f), ("right", None, f)]),
            SetServo("both", servo={"left": None, "right": (None, f)}, seconds=0.3),
            CheckGrip("both", reach=a.min_reach, support=0.0, seconds=0.5),
            Attach("both", freeze=True),
            Carry("both", offset=[0, 0, a.lift], root=a.lift_root, seconds=7.0, pitch_gain=0.02),
            CheckGrip("both", reach=a.min_reach, support=0.3, seconds=0.5),
            StableHold("both", seconds=3.0, clearance=a.lift * 0.6, tilt=8.0, speed=0.05),
            Carry("both", offset=[0, 0, -a.lift], root=-a.lift_root, seconds=7.0, pitch_gain=0.02),
            Detach("both"),
            Settled("both", seconds=1.0),
            HandsTo("both", below=a.below_rail, seconds=2.0),
            SlideOut("both", dist=a.retreat, seconds=3.0),
            Hold("both", seconds=1.0),
            StandUp("both", seconds=14.0),
            Hold("both", seconds=1.0),
        ]
        status = self.run_stiff(plan, "stool", approach=True)
        if status == "done":
            # arms back to the approach pose the climb was verified from (--start-at climb starts
            # there): after the stand-up they hang low in front and the climb lost its posture on
            # one foot with an upper-body joint at 4x its rating (chain-relay-v12)
            qids = self.planner.qids
            start, goal = self.qref.copy(), self.qref.copy()
            goal[qids[12:]] = self.refs[0][qids[12:]]
            n = int(2.0 / 0.02)
            for k in range(1, n + 1):
                q = start + (goal - start) * smooth(k / n)
                self.stiff_step(q[qids[:12]], q[qids[12:]])
            self.qref = goal
            for _ in range(25):
                self.stiff_step(goal[qids[:12]], goal[qids[12:]])
            self.event("stool:arms_to_climb_pose")
        sp = self.cpu(self.env.stool.get_pos())
        self.report["stages"]["stool"] = dict(
            status=status, stool=np.round(sp, 3).tolist(),
            metrics={k: v for k, v in self.ctx.metrics.items() if k.startswith(("hold", "placed", "stable"))})
        return status

    def walk_steps(self):
        """Carry the stool to the cabinet with planned footfalls (StepWalk), the hands attached."""
        a = self.args
        measured, _ = self.measured_q()
        goal_x = self.drop_x - a.set_ahead
        distance = float(goal_x - measured[0])
        pitch = float(Rotation.from_quat(measured[[4, 5, 6, 3]]).as_euler("xyz")[1])
        waist = measured[self.planner.qids[12:15]]
        self.event("walk:start", goal_x=round(goal_x, 3), distance=round(distance, 3), mode="steps",
                   pelvis_pitch=round(pitch, 3), waist=np.round(waist, 3).tolist())
        if distance > 0.03:
            n = int(np.ceil(distance / (a.step_length / 2)))
            n += n % 2
            d = 2 * distance / n
            self.event("walk:plan", footfalls=n, step=round(d, 3))
            plan = []
            self.walk_offset = None
            # footfalls until the pelvis reaches goal_x (short landings take more steps), 2 n at most
            for k in range(2 * n):
                plan.append(StoolStep(self, "right" if k % 2 == 0 else "left", dist=d, seconds=a.step_seconds, lift=a.step_lift,
                                      sway=a.step_sway, inset=a.step_inset, goal_x=goal_x, com_tolerance=a.step_com_tol,
                                      com_gain=a.step_com_gain))
            plan.append(StableHold("both", seconds=2.0, clearance=0.5, tilt=10.0, speed=0.05))
            self._ff = None
            self.walk_R0, self.walk_pitch_fb = None, 0.0
            status = self.run_stiff(plan, "walk", timeout=900.0)
        else:
            status = "done"
        self.balance = None
        self.update_stool()
        measured, _ = self.measured_q()
        info = dict(status=status, goal_x=round(goal_x, 3), pelvis=np.round(measured[:3], 3).tolist(),
                    stool=np.round(self.stool.pos, 3).tolist(), stool_tilt=round(self.stool.tilt_deg(), 1),
                    stool_bottom=round(self.stool.bottom(), 3), feet=np.round(self.feet, 3).tolist())
        self.report["stages"]["walk"] = info
        self.event("walk:end", **info)
        return status

    def walk_planned(self):
        return planned_walk(self)

    def to_agile_stance(self, seconds=4.0):
        """Joint-space move (stiff) to a pose with Agile's standing legs, feet where they are, and
        the hands where they hold the stool now (arms and waist re-solved by the IK)."""
        planner, ctx = self.planner, self.ctx
        measured, _ = self.measured_q()
        planner.forward(measured)
        targets = np.array([ctx.attached_target(sd)[0] for sd in SIDES])
        rots = np.array([ctx.attached_target(sd)[1] for sd in SIDES])
        saved = (planner.m.jnt_range.copy(), getattr(planner, "com_position_weight", 500),
                 getattr(planner, "root_height_weight", 100), np.array(planner.root_rotation_weights, float))
        legs = np.asarray(planner.jids[:12])
        try:
            planner.m.jnt_range[legs, 0] = AGILE_LEGS - 0.01
            planner.m.jnt_range[legs, 1] = AGILE_LEGS + 0.01
            planner.com_position_weight = 0.0          # legs and feet fix the base; CoM follows
            planner.root_height_weight = 0.0
            planner.root_rotation_weights = np.array([50.0, 0.0, 50.0])
            seed = self.qref.copy()
            seed[planner.qids[:12]] = AGILE_LEGS
            goal = seed
            for _ in range(4):
                try:
                    goal, err = planner.reach(goal, self.feet, targets, ctx.com_cmd, 0.716, rotations=rots)
                    break
                except ValueError as exc:
                    goal, err = planner.d.qpos.copy(), str(exc)
        finally:
            planner.m.jnt_range[:] = saved[0]
            planner.com_position_weight, planner.root_height_weight, planner.root_rotation_weights = saved[1], saved[2], saved[3]
        planner.forward(goal)
        hand_err = float(np.linalg.norm(planner.palms() - targets, axis=1).max())
        pitch = float(Rotation.from_quat(goal[[4, 5, 6, 3]]).as_euler("xyz")[1])
        self.event("to_agile_stance", hand_err=round(hand_err, 3), pelvis=np.round(goal[:3], 3).tolist(), pitch=round(pitch, 3))
        start = self.qref.copy()
        n = int(seconds / 0.02)
        self.stiff_gains()
        for k in range(1, n + 1):
            u = smooth(k / n)
            q = start + (goal - start) * u
            self.stiff_step(q[planner.qids[:12]], q[planner.qids[12:]])
        self.qref = goal.copy()
        for _ in range(25):
            self.stiff_step(goal[planner.qids[:12]], goal[planner.qids[12:]])
        self.update_stool()
        measured, _ = self.measured_q()
        info = dict(hand_err=round(hand_err, 3), pelvis=np.round(measured[:3], 3).tolist(),
                    stool_bottom=round(self.stool.bottom(), 3), stool_tilt=round(self.stool.tilt_deg(), 1))
        self.report["stages"]["agile_stance"] = info
        return "done" if self.stool.bottom() > 0.5 and self.stool.tilt_deg() < 10.0 else "stool_slipped"

    def walk(self):
        """Agile walk with the stool held, arms on their last stiff references. Straight and
        slow: with the general navigator (up to 0.5 m/s) the walk ran 0.26 m past its goal and
        put the stool into the cabinet (chain-v2); Agile stops from 0.2-0.25 m/s within a few
        cm. Stops early on a cabinet guard; the set-down then places the stool at drop_x."""
        from humanoid.g1_support_retrieval.oracle.oracle import Robot, hold
        a = self.args
        self.task_gains()
        robot = Robot(self.env, video=None)
        robot.q_ref = self.qref[self.planner.qids].copy()
        robot.hands = {"left": None, "right": None}
        robot.mask_upper = a.mask_upper
        self.robot = robot
        self._hook_robot(robot)
        stool = self.env.stool
        ahead = float(self.cpu(stool.get_pos())[0] - robot.pos[0])
        goal_x = self.drop_x - a.set_ahead
        guard = T.CABINET_X_FRONT - 0.08 - self.meta["footprint"][0] / 2      # max stool centre x
        self.event("walk:start", ahead=round(ahead, 3), goal_x=round(goal_x, 3), guard=round(guard, 3))
        ok = hold(robot, 2.0)
        self.report["walk_settle"] = dict(base=np.round(robot.pos, 3).tolist(), yaw=round(robot.yaw, 3))
        t0, why = self.t, "reached"
        trace = []
        while ok:
            x, y, yaw = robot.pos[0], robot.pos[1], robot.yaw
            sx = float(self.cpu(stool.get_pos())[0])
            if goal_x - x <= a.walk_lead:
                break
            if sx >= guard:
                why = "cabinet_guard"
                break
            if float(robot.base_velocity()[0]) > a.walk_speed + 0.2:
                why = "runaway_guard"      # chain-v3: commanded 0.25 m/s, ran up to 0.75 m/s
                break
            if self.t - t0 > 20.0:
                why = "timeout"
                break
            # base-frame command: forward, lateral back onto y0, keep facing +x
            c, s_ = np.cos(yaw), np.sin(yaw)
            ey = self.y0 - y
            vy_b = float(np.clip(1.0 * (-s_ * 0.0 + c * ey), -0.1, 0.1))
            wz = float(np.clip(-2.0 * yaw, -0.4, 0.4))
            ok = robot.step((a.walk_speed, vy_b, wz))
            if int(round(self.t / 0.02)) % 10 == 0:
                trace.append([round(self.t, 2), round(float(x), 3), round(float(y), 3), round(float(yaw), 3), round(sx, 3)])
        # stop and stand until still (<= 4 s), guard still on
        still = 0
        for _ in range(200):
            if not ok:
                break
            ok = robot.step((0.0, 0.0, 0.0))
            v = robot.base_velocity()
            still = still + 1 if float(np.linalg.norm(v[:2])) < 0.03 else 0
            if still >= 25:
                break
        ok = ok and hold(robot, 0.5)
        sp, sq = self.cpu(stool.get_pos()), self.cpu(stool.get_quat())
        tilt = float(np.degrees(np.arccos(np.clip(1 - 2 * (sq[1] ** 2 + sq[2] ** 2), -1, 1))))
        held = sp[2] - self.H / 2 > 0.25 and tilt < 15.0
        self.report["stages"]["walk"] = dict(ok=bool(ok), held=bool(held), stop=why, goal_x=round(goal_x, 3),
                                             overshoot=round(float(robot.pos[0] - goal_x), 3), task=robot.info,
                                             stool=np.round(sp, 3).tolist(), tilt=round(tilt, 1),
                                             base=np.round(robot.pos, 3).tolist(), yaw=round(robot.yaw, 3), trace=trace)
        self.event("walk:end", **{k: v for k, v in self.report["stages"]["walk"].items() if k not in ("task", "trace")})
        return "done" if ok and held else ("stool_dropped" if not held else "walk_failed")

    def hand_env_contacts(self, robot):
        """[(robot link, other link, force on the robot, world point)] for arm/hand links touching
        the cabinet or the stool."""
        c = self.r.get_contacts()
        c = {key: v[0].detach().cpu().numpy() if hasattr(v[0], "detach") else v for key, v in c.items()}
        names = {l.idx: l.name for l in self.env.scene.rigid_solver.links}
        own = {l.idx for l in self.r.links}
        out = []
        for i in np.flatnonzero(c["valid_mask"]):
            a, b = int(c["link_a"][i]), int(c["link_b"][i])
            if (a in own) == (b in own):
                continue
            mine, other, suffix = (a, b, "a") if a in own else (b, a, "b")
            name, oname = names.get(mine, ""), names.get(other, "")
            if not any(k in name for k in ("hand", "wrist", "elbow", "shoulder")) or "box" in oname:
                continue
            out.append((name, oname, c["force_" + suffix][i].copy(), c["position"][i].copy()))
        return out

    def ik_feet(self):
        """Foot positions of the IK reference (where the IK thinks the feet are)."""
        self.planner.forward(self.qref)
        return self.planner.d.xpos[self.planner.feet].copy()

    def note_efforts(self, stage):
        """Peak |applied torque| / physical rating per joint and stage (report['effort_by_joint'])."""
        if not hasattr(self, "_phys_effort"):
            m = self.planner.m
            self._phys_effort = self.physical_effort.copy()
        f = self.cpu(self.r.get_dofs_control_force(self.env.dofs))
        f = f[0] if f.ndim == 2 else f
        ratio = np.abs(f) / self._phys_effort
        table = self.report.setdefault("effort_by_joint", {}).setdefault(stage, {})
        for i in np.flatnonzero(ratio > 1.0):
            n = T.JOINT_NAMES[i].replace("_joint", "")
            if float(ratio[i]) > (table.get(n) or [0.0])[0]:
                table[n] = [round(float(ratio[i]), 2), round(self.t, 2), getattr(self, "effort_note", "")]

    def robot_touches(self, robot, min_force=2.0):
        """Robot links touching anything but the floor (diagnostics): {link: [other, N]}."""
        c = self.r.get_contacts()
        c = {key: v[0].detach().cpu().numpy() if hasattr(v[0], "detach") else v for key, v in c.items()}
        names = {l.idx: l.name for l in self.env.scene.rigid_solver.links}
        own = {l.idx for l in self.r.links}
        out = {}
        for i in np.flatnonzero(c["valid_mask"]):
            a, b = int(c["link_a"][i]), int(c["link_b"][i])
            if a in own and b in own:
                na, nb = names.get(a, ""), names.get(b, "")
                if not ({"torso_link", "pelvis"} & {na, nb} and ("shoulder" in na + nb or "elbow" in na + nb or "wrist" in na + nb)):
                    continue
            mine, other = (a, b) if a in own else (b, a)
            f = float(np.linalg.norm(c["force_a"][i]))
            oname = names.get(other, str(other))
            if f < min_force or "plane" in oname or "floor" in oname.lower():
                continue
            key = names.get(mine, str(mine))
            if f >= out.get(key, ["", 0.0])[1]:
                out[key] = [oname, round(f, 1), np.round(c["position"][i], 3).tolist()]
        return out

    def _hook_robot(self, robot):
        """Record the env.step phases into the same video and clock."""
        chain = self
        step = robot.step

        def stepped(*a, **kw):
            out = step(*a, **kw)
            chain.note_efforts("relay_agile")
            chain.t += T.CONTROL_DT
            chain.record()
            return out
        robot.step = stepped

    def standing_state(self):
        """Measured double-support posture; a stationary stool is insufficient."""
        from scipy.spatial import ConvexHull, QhullError

        q, state = self.measured_q()
        p = self.planner
        p.forward(q)
        feet = p.d.xpos[p.feet].copy()
        com = p.d.subtree_com[1].copy()
        corners = getattr(p, "support_corners", (p.corners, p.corners))
        points, bottom = [], []
        for side, body in enumerate(p.feet):
            rotation = p.d.xmat[body].reshape(3, 3)
            sole = feet[side] + np.asarray(corners[side]) @ rotation.T
            points.extend(sole[:, :2])
            bottom.append(float(sole[:, 2].min()))
        try:
            hull = ConvexHull(np.asarray(points))
            margin = float(-np.max(hull.equations[:, :2] @ com[:2] + hull.equations[:, 2]))
        except QhullError:
            margin = -1.0
        foot_ids = [self.r.get_link(name).idx_local for name in T.FOOT_LINKS]
        fz = self.r.get_links_net_contact_force()[0, foot_ids, 2].detach().cpu().numpy()
        rotation = Rotation.from_quat(q[[4, 5, 6, 3]]).as_matrix()
        tilt = float(np.degrees(np.arccos(np.clip(rotation[2, 2], -1.0, 1.0))))
        speed = float(np.linalg.norm(self.cpu(state.root_lin_vel)))
        angular = float(np.linalg.norm(self.cpu(state.root_ang_vel)))
        good = (q[2] >= 0.55 and tilt <= 25.0 and speed <= 0.03 and angular <= 0.1
                and bool(np.all(fz > 20.0)) and max(abs(z) for z in bottom) <= 0.015
                and margin >= 0.005)
        return dict(ok=bool(good), root_height_m=float(q[2]), pelvis_tilt_deg=tilt,
                    root_speed_mps=speed, root_angular_speed_radps=angular,
                    foot_fz_N=fz.tolist(), foot_bottom_m=bottom, support_margin_m=margin,
                    com=com.tolist(), root=q[:7].tolist(), feet=feet.tolist())

    def balanced_arms_to_climb_pose(self):
        """Physical double-support transition with a measured stable endpoint."""
        p = self.planner
        initial = self.standing_state()
        info = dict(initial=initial, trace=[], status="planning")
        self.report["setdown_arm_transition"] = info
        if not initial["ok"]:
            info["status"] = "initial_robot_not_stable"
            return info["status"]
        start, _ = self.measured_q()
        upper = np.clip(self.refs[0][p.qids[12:]],
                        self.physical_joint_limits[12:, 0] + self.position_margins[12:],
                        self.physical_joint_limits[12:, 1] - self.position_margins[12:])
        try:
            poses, times, plan = balanced_arm_reference(p, start, upper,
                                                       self_collision=bool(self.args.self_collision))
        except ValueError as exc:
            info.update(status="arm_fold_plan_failed", reason=str(exc))
            return info["status"]
        info["plan"] = plan
        np.savez(self.args.out / "setdown_arm_reference.npz", qpos=poses, time=times)
        self.active_stiff_phase = "arms_to_climb_pose"
        self.event("setdown:arms_to_climb_pose_start", **plan)
        self.qref = start.copy()
        t0, stable, unsafe = self.t, 0.0, 0.0
        status = "arm_fold_not_stable"
        for k in range(int(np.ceil((times[-1] + 4.0) / T.CONTROL_DT))):
            age = min(self.t - t0 + T.CONTROL_DT, float(times[-1]))
            i = min(max(int(np.searchsorted(times, age, side="right")) - 1, 0), len(times) - 2)
            a = (age - times[i]) / (times[i + 1] - times[i])
            self.qref = poses[i] + (poses[i + 1] - poses[i]) * a
            self.qref[3:7] /= np.linalg.norm(self.qref[3:7])
            self.stiff_step(self.qref[p.qids[:12]], self.qref[p.qids[12:]])
            state = self.standing_state()
            if k % 5 == 0:
                measured, _ = self.measured_q()
                info["trace"].append(dict(time=self.t, age=self.t - t0, **state,
                                          measured_q=measured.tolist(), reference_q=self.qref.tolist()))
            supported = (state["root_height_m"] >= 0.55 and state["pelvis_tilt_deg"] <= 25.0
                         and state["support_margin_m"] >= 0.005
                         and min(state["foot_fz_N"]) > 20.0
                         and max(abs(z) for z in state["foot_bottom_m"]) <= 0.015)
            unsafe = 0.0 if supported else unsafe + T.CONTROL_DT
            if unsafe >= 0.12:
                status = "arm_fold_support_lost"
                break
            done = self.t - t0 >= times[-1]
            stable = stable + T.CONTROL_DT if done and state["ok"] else 0.0
            if stable >= 0.5:
                status = "done"
                break
        info.update(status=status, final=state, stable_seconds=round(stable, 3))
        self.ctx.qref = self.qref.copy()
        self.active_stiff_phase = None
        self.event("setdown:arms_to_climb_pose", status=status, robot=state)
        return status

    def setdown(self, resume_lowered=False, resume_released=False):
        """Back to the stiff controller where the walk ended: crouch, put the stool down ~0.58 m
        ahead of the pelvis, unload the hands, settle the stool, withdraw and stand up.

        A lowered-stool diagnostic resume skips descent initialization. That
        checkpoint represents completed lowering, not verified stable placement.
        A released-stool resume also skips unloading and rising; the arm
        transition and final stable hand-off gate still must complete.
        """
        a, ctx, planner = self.args, self.ctx, self.planner
        status = "done"
        if not (resume_lowered or resume_released):
            saved = getattr(planner, "_pre_upright_constraints", None)
            if saved is not None:
                planner.root_rotation_upper = saved["root_rotation_upper"].copy()
                planner.root_rotation_lower = np.array(saved.get("root_rotation_lower", [-0.3, -0.2, -0.3]), float)
                planner.waist_lower = saved["waist_lower"].copy()
                planner.waist_upper = saved["waist_upper"].copy()
                planner.m.jnt_range[planner.m.joint("waist_yaw_joint").id] = saved["waist_yaw_range"]
            else:
                # Older diagnostic checkpoints predate the saved reach constraints.
                planner.root_rotation_upper = [0.3, 1.4, 0.3]
                planner.root_rotation_lower = [-0.3, -0.2, -0.3]
                planner.waist_lower, planner.waist_upper = -0.2, 0.5
                planner.m.jnt_range[planner.m.joint("waist_yaw_joint").id] = self.physical_joint_limits[12]
            # Loaded crouch/standing transitions deflect the waist beyond its IK
            # reference: the repeated setdown reached 0.52235 rad at a 0.52 stop.
            # Leave planning room for this deflection; physical limits stay intact.
            planner.waist_upper = np.minimum(planner.waist_upper, [0.5, 0.47])
            measured, _ = self.measured_q()
            self.qref = measured.copy()
            planner.forward(measured)
            self.feet = planner.d.xpos[planner.feet].copy()
            feet_mid = self.feet[:, :2].mean(axis=0)
            ctx.com_cmd = feet_mid + np.array([a.com_shift, 0.0])
            ctx.com_nominal = feet_mid.copy()
            ctx.root_h = float(measured[2])
            self.update_stool()
            bottom = self.stool.bottom()
            # Recover the ground-grasp crouch, not the higher post-lift posture.
            # Lower the pelvis early: splitting this drop equally left the waist
            # supporting >50 N m while the stool passed through waist height.
            root_drop = ctx.root_h - a.crouch
            first_drop, last_drop = 0.75 * root_drop, 0.25 * root_drop
            self.report["setdown_plan"] = dict(root_start=ctx.root_h, root_goal=a.crouch,
                                               first_root_drop=first_drop, last_root_drop=last_drop,
                                               com_shift_start=a.com_shift, com_shift_lowering=0.08,
                                               com_shift_phase="second_carry")
            out = float(self.drop_x - self.stool.pos[0])          # put it down at drop_x (world)
            lateral = float(self.y0 - self.stool.pos[1])
            ctx.metrics["setdown_reach_out_m"] = out
            mid = bottom - a.stand_up_dz[0]
            head = [
                Reattach("both"),
                WeightedCarry("both", offset=[out, lateral, -mid], root=-first_drop,
                              seconds=8.0, pitch_gain=0.02, w=(50.0, 5.0)),
                # Only move the combined COM forward once the initial crouch is
                # established. Earlier motion led IK into a knee/stool collision.
                WeightedCarry("both", offset=[0, 0, -(bottom - mid)], root=-last_drop, com=[0.08, 0.0],
                              seconds=8.0, pitch_gain=0.02, w=(5.0, 0.2)),
                Detach("both"),
            ]
            ctx.metrics["stool_start"] = self.stool.pos.tolist()
            status = self.run_stiff(head, "setdown")
            if status == "done":
                # This return boundary includes the final Detach control tick.
                # Saving and resuming here both precede the tail's first measure.
                # Hands may still carry the stool; no settling claim is made.
                self.report["stages"]["stool_lowered"] = dict(
                    status="done", time=self.t, stool=self.stool.pos.tolist(),
                    root_target=ctx.root_h, com_target=ctx.com_cmd.tolist())
                if a.save_checkpoint:
                    path = a.save_checkpoint
                    checkpoint_path = path.with_name(path.stem + "-stool-lowered" + path.suffix)
                    try:
                        save_chain_checkpoint(self, checkpoint_path, stage="stool_lowered")
                    except Exception as exc:
                        self.report["checkpoint_error"] = dict(type=type(exc).__name__, message=str(exc))
                        self.event("checkpoint:failed", **self.report["checkpoint_error"])
                    else:
                        self.event("checkpoint:saved", path=str(checkpoint_path),
                                   checkpoint_stage="stool_lowered", diagnostic_only=True)
        if status == "done" and not resume_released:
            # A lowered-stool resume preserves every restored reference and
            # context field until the normal ClearStoolHands.start rebase.
            tail = [
                ClearStoolHands("both", below=a.below_rail, seconds=3.0),
                Settled("both", seconds=1.0),
                SlideOut("both", dist=a.retreat, seconds=3.0),
                Hold("both", seconds=1.0),
                StandUp("both", seconds=14.0),
                Hold("both", seconds=1.0),
            ]
            status = self.run_stiff(tail, "setdown")
            if status == "done":
                # Save the completed release/standing phase before changing
                # upper posture. This is not the final hand-off acceptance.
                self.report["stages"]["stool_released"] = dict(
                    status="done", time=self.t, stool=self.stool.pos.tolist(),
                    root_target=ctx.root_h, com_target=ctx.com_cmd.tolist())
                if a.save_checkpoint:
                    path = a.save_checkpoint
                    checkpoint_path = path.with_name(path.stem + "-stool-released" + path.suffix)
                    try:
                        save_chain_checkpoint(self, checkpoint_path, stage="stool_released")
                    except Exception as exc:
                        self.report["checkpoint_error"] = dict(type=type(exc).__name__, message=str(exc))
                        self.event("checkpoint:failed", **self.report["checkpoint_error"])
                    else:
                        self.event("checkpoint:saved", path=str(checkpoint_path),
                                   checkpoint_stage="stool_released", diagnostic_only=True)
        if status == "done":
            status = self.balanced_arms_to_climb_pose()
        final_state = dict(ok=False)
        if status == "done":
            stable = 0.0
            for _ in range(100):
                self.stiff_step(self.qref[planner.qids[:12]], self.qref[planner.qids[12:]])
                self.update_stool()
                measured, _ = self.measured_q()
                planner.forward(measured)
                contacts = contact_summary(self.r, self.env.stool, self.mapping, planner)
                hand_force = sum(float(np.linalg.norm(force)) for name, force in contacts["groups"].items()
                                 if name.endswith(("_thumb", "_finger", "_palm")))
                bottom, tilt = self.stool.bottom(), self.stool.tilt_deg()
                speed = float(np.linalg.norm(self.stool.vel))
                angular_speed = float(np.linalg.norm(self.cpu(self.env.stool.get_ang())))
                drop_error = float(np.linalg.norm(self.stool.pos[:2] - [self.drop_x, self.y0]))
                object_good = (abs(bottom) <= 0.015 and tilt <= 10.0 and speed <= 0.03
                               and angular_speed <= 0.1 and hand_force < 1.0 and drop_error <= 0.04)
                robot_state = self.standing_state()
                good = object_good and robot_state["ok"]
                stable = stable + T.CONTROL_DT if good else 0.0
                final_state = dict(ok=stable >= 0.5, time=self.t, stool=self.stool.pos.tolist(),
                                   bottom=bottom, tilt=tilt, speed=speed, angular_speed=angular_speed,
                                   hand_force_N=hand_force, stable_seconds=round(stable, 3),
                                   object_ok=bool(object_good), robot_ok=robot_state["ok"], robot=robot_state)
                if final_state["ok"]:
                    break
            self.event("setdown:final_settled", **{key: value for key, value in final_state.items() if key != "time"})
            if not final_state["ok"]:
                status = "final_robot_or_stool_not_settled"
        sp = self.cpu(self.env.stool.get_pos())
        self.report["stages"]["setdown"] = dict(status=status, stool=np.round(sp, 3).tolist(),
                                                stool_vs_drop=round(float(np.linalg.norm(sp[:2] - [self.drop_x, self.y0])), 3),
                                                final_state=final_state,
                                                release_start=ctx.metrics.get("release_start"),
                                                release_trace=ctx.metrics.get("release_trace", []),
                                                metrics={k: v for k, v in ctx.metrics.items() if k.startswith("placed")})
        # Continuation configures its leg gains only. Restore this temporary
        # upper-body gain before saving the hand-off or entering the climb.
        pitch = T.JOINT_NAMES.index("waist_pitch_joint")
        self.r.set_dofs_kv(self.p["kd"][pitch:pitch + 1], [self.env.dofs[pitch]])
        return status

    def climb_retrieve_stepdown(self):
        """Stand on the stool (verified step_on), take the box, step down with it."""
        cont = ChainOn(self)
        context = dict(env=self.env, planner=self.planner, args=self.args, writer=FrameWriter(self.writer, self.frame),
                       time=self.t + 0.02, qref=self.qref.copy(), box=self.env.stool, tensor=self.tensor, cpu=self.cpu)
        rep = (cont.resume_on_stool(context, self._resume_on_stool) if hasattr(self, "_resume_on_stool")
               else cont(context))
        self.t = cont.t
        # Both controllers write the same 25 fps stream. Continue the existing
        # frame clock instead of catching up old deadlines at every control tick.
        self.next_frame = cont.next_frame
        self.report["stages"]["continuation"] = {k: v for k, v in rep.items() if k in (
            "success", "climb_success", "status", "reason", "stages", "max_effort_ratio", "max_speed_ratio", "max_joint_limit_overshoot", "actuator_checks")}
        self.max_effort = max(self.max_effort, rep.get("max_effort_ratio", 0.0))
        self.max_speed = max(self.max_speed, rep.get("max_speed_ratio", 0.0))
        want = {"climb": "box_top_support_verified", "retrieve": "target_retrieved"}.get(self.args.stop_after,
                                                                                         "stepped_down_with_box")
        if not rep.get("actuator_checks", False):
            return "actuator_checks_failed"
        return "done" if want in rep.get("stages", []) else str(rep.get("reason", rep.get("status", "failed")))

    def settle_delivered(self, robot):
        """Observe the released box on the floor after task termination, without reset."""
        stable = 0.0
        box = self.env.top_boxes[self.k]
        half_size = np.asarray(T.TOP_SIZES[self.k]) / 2
        local_corners = np.array([[x, y, z] for x in (-half_size[0], half_size[0])
                                  for y in (-half_size[1], half_size[1])
                                  for z in (-half_size[2], half_size[2])])
        info = dict(ok=False, stable_seconds=0.0)
        for _ in range(100):
            # Robot.step normally stops refreshing its cached state at task
            # termination. Keep it current while the unchanged controller holds.
            robot.s = self.env.state()
            robot.step()
            state = self.env.state()
            position = self.cpu(box.get_pos())
            quat = self.cpu(box.get_quat())
            rotation = Rotation.from_quat(quat[[1, 2, 3, 0]]).as_matrix()
            bottom = float((local_corners @ rotation.T + position)[:, 2].min())
            tilt = float(np.degrees(np.arccos(np.clip(rotation[2, 2], -1.0, 1.0))))
            speed = float(np.linalg.norm(self.cpu(box.get_vel())))
            angular_speed = float(np.linalg.norm(self.cpu(box.get_ang())))
            forces = robot.hand_forces(self.k)
            hand_force = max(float(np.linalg.norm(forces[side])) for side in SIDES)
            # A released box may settle on any face. Its lowest measured corner,
            # rather than its initial upright half-height, determines floor contact.
            on_floor = abs(bottom) < 0.015
            good = (bool(self.env.core.in_goal(self.env.core.target_pos(state))[0])
                    and robot.info.get("success", False) and on_floor
                    and speed < 0.03 and angular_speed < 0.10 and hand_force < 1.0)
            stable = stable + T.CONTROL_DT if good else 0.0
            info = dict(ok=stable >= 0.5, stable_seconds=round(stable, 3),
                        box=position.tolist(), bottom=bottom, tilt=tilt, speed=speed,
                        angular_speed=angular_speed, hand_force_N=hand_force,
                        goal_center=self.env.core.goal.detach().cpu().tolist(), goal_size=list(T.GOAL_SIZE))
            if info["ok"]:
                break
        self.event("goal:settled", **info)
        return info

    def place_at_goal(self, robot):
        """Align the measured box over the goal, lower it, and finish withdrawing both hands."""
        from humanoid.g1_support_retrieval.oracle.oracle import Result, hand_preset, box_corners

        robot.hold_legs()
        robot.s = self.env.state()
        if robot.info.get("fallen", False):
            return Result(False, "fell while settling at the goal")
        box = self.env.top_boxes[self.k]
        center0, quat0 = robot.box_state(self.k)
        center0 = center0.astype(float)
        box_rotation = Rotation.from_quat(quat0[[1, 2, 3, 0]]).as_matrix()
        yaw = float(np.arctan2(box_rotation[1, 0], box_rotation[0, 0]))
        level_rotation = Rotation.from_euler("z", yaw).as_matrix()
        turn = Rotation.from_matrix(level_rotation @ box_rotation.T).as_rotvec()
        q = robot.q_ref.copy()
        q[:12] = robot.joints()[:12]
        for side in SIDES:
            q = hand_preset(q, side, "squeeze")
        q = np.clip(q, self.physical_joint_limits[:, 0] + self.position_margins,
                    self.physical_joint_limits[:, 1] - self.position_margins)
        robot.ik._set(robot.pos, robot.quat, q)
        palms = {side: robot.ik.hand_point(side, "palm").copy() for side in SIDES}
        rotations = {side: robot.ik.d.xmat[robot.ik.wrist[side]].reshape(3, 3).copy() for side in SIDES}
        lateral = palms["left"] - palms["right"]
        lateral /= np.linalg.norm(lateral)
        goal_xy = self.env.core.goal.detach().cpu().numpy().astype(float)
        # The locomotion arrival tolerance can leave the pelvis 8 cm farther
        # away. Keep this low pose inside the measured arm workspace there.
        release_height = 0.74
        current = center0.copy()
        angle, offset, filtered_force = 0.0, 0.0, None
        trace = self.report.setdefault("goal_place_trace", [])
        self.event("goal:place_start", box=center0.tolist(), goal=goal_xy.tolist())

        def tick(center, fraction, opening=0.0, squeeze=True, phase="lower"):
            nonlocal offset, filtered_force
            robot.s = self.env.state()
            rotation = Rotation.from_rotvec(turn * fraction).as_matrix()
            axis = rotation @ lateral
            forces = robot.hand_forces(self.k)  # Also updates external wrenches for the stance QP.
            mean_force = 0.5 * sum(abs(float(np.dot(forces[side], axis))) for side in SIDES)
            filtered_force = mean_force if filtered_force is None else 0.8 * filtered_force + 0.2 * mean_force
            if squeeze:
                offset = float(np.clip(offset + np.clip((18.0 - filtered_force) * 2e-5, -2e-4, 2e-4), -0.012, 0.012))
            tasks = {side: ("palm", center + rotation @ (palms[side] - center0)
                            + (-axis if side == "left" else axis) * (offset - opening),
                            rotation @ rotations[side]) for side in SIDES}
            robot.reach(tasks, rate=0.6, iters=8)
            robot.q_ref[:] = np.clip(robot.q_ref, self.physical_joint_limits[:, 0] + self.position_margins,
                                     self.physical_joint_limits[:, 1] - self.position_margins)
            robot.step()
            # Terminal success is an observation, not an instruction to leave one hand in the box.
            robot.s = self.env.state()
            bp, bq = robot.box_state(self.k)
            robot.ik._set(robot.pos, robot.quat, robot.joints())
            error = max(float(np.linalg.norm(robot.ik.hand_point(side, "palm") - tasks[side][1])) for side in SIDES)
            speed = float(np.linalg.norm(self.cpu(box.get_vel())))
            angular_speed = float(np.linalg.norm(self.cpu(box.get_ang())))
            bottom = float(box_corners(bp, bq, T.TOP_SIZES[self.k])[:, 2].min())
            if robot.steps % 10 == 0:
                trace.append(dict(t=round(self.t, 3), phase=phase, target=center.tolist(), box=bp.tolist(),
                                  bottom=bottom, speed=speed, angular_speed=angular_speed, palm_error=error,
                                  squeeze=filtered_force, opening=opening, root=robot.pos.tolist()))
            if robot.info.get("fallen", False):
                raise ValueError("fell during goal placement")
            return bp, error, speed, angular_speed

        def withdraw(reason=""):
            # Complete this trajectory even after the task's first success tick.
            for i in range(100):
                opening = 0.075 * smooth(min(1.0, (i + 1) * T.CONTROL_DT / 1.2))
                tick(current, angle, opening, squeeze=False, phase="release")
            self.event("goal:hands_withdrawn", box=robot.box_state(self.k)[0].tolist(),
                       hand_force_N=max(float(np.linalg.norm(f)) for f in robot.hand_forces(self.k).values()))
            return Result(True, reason)

        try:
            # First remove the carried tilt while keeping the contact centre high; then lower.
            for phase, target, fraction, seconds in (
                ("align_level", np.r_[goal_xy, max(0.86, center0[2] - 0.08)], 1.0, 5.0),
                ("lower", np.r_[goal_xy, release_height], 1.0, 5.0),
            ):
                start, angle0 = current.copy(), angle
                progress = 0.0
                for _ in range(int((seconds * 2 + 3) / T.CONTROL_DT)):
                    u = smooth(min(1.0, progress / seconds))
                    current = start + (target - start) * u
                    angle = angle0 + (fraction - angle0) * u
                    bp, error, _, _ = tick(current, angle, phase=phase)
                    if bp[2] < current[2] - 0.12:
                        self.event("goal:contact_lost", phase=phase, box=bp.tolist())
                        # This is not a success verdict: the caller still checks
                        # the actual settled box, no hand force and goal bounds.
                        return withdraw("box lost grip while lowering; settling checked separately")
                    if error < 0.03:
                        progress += T.CONTROL_DT
                    if progress >= seconds and np.linalg.norm(bp - target) < 0.04:
                        break
                else:
                    return Result(False, f"goal {phase} did not track", dict(box=bp.tolist(), palm_error=error))
                self.event("goal:place_phase", phase=phase, box=bp.tolist(), palm_error=error)
            # Correct residual grasp offset with a bounded, slow common translation.
            stable = 0.0
            nominal = current.copy()
            for _ in range(200):
                bp, error, speed, angular_speed = tick(current, angle, phase="settle_grip")
                delta = np.r_[goal_xy, release_height] - bp
                current += np.clip(delta * 0.04, -0.0004, 0.0004)
                current = np.clip(current, nominal - 0.04, nominal + 0.04)
                good = np.linalg.norm(delta[:2]) < 0.025 and abs(delta[2]) < 0.04 and speed < 0.03 and angular_speed < 0.15
                stable = stable + T.CONTROL_DT if good else 0.0
                if stable >= 0.3:
                    break
            else:
                return Result(False, "goal box did not settle before release", dict(box=bp.tolist(), speed=speed))
            self.event("goal:release_start", box=bp.tolist(), speed=speed, angular_speed=angular_speed)
            return withdraw()
        except ValueError as exc:
            return Result(False, str(exc))

    def relay_goal(self):
        """Walk round the stool, take the box off the board below from the floor (M1's retrieval),
        carry it to the goal zone and let it drop there."""
        from humanoid.g1_support_retrieval.oracle.oracle import Robot, navigate, release, hold, GOAL_POSE, retrieve
        from humanoid.g1_support_retrieval.oracle.navigation import Grid, stance_near
        self.view = "room"
        self.task_gains()
        robot = Robot(self.env, video=None)
        robot.blend_legs = (torch.as_tensor(robot.joints()[robot.agile.leg_idx.cpu().numpy()], device=self.dev,
                                            dtype=torch.float32).unsqueeze(0), 0, 25)
        self._hook_robot(robot)
        if not hold(robot, 1.5):
            return "fell_after_step_down"
        sp, sq = self.cpu(self.env.stool.get_pos()), self.cpu(self.env.stool.get_quat())
        stool = [(sp[:2], self.meta["footprint"][:2], float(Rotation.from_quat(sq[[1, 2, 3, 0]]).as_euler("xyz")[2]))]
        s = robot.s
        grid = Grid(self.env.core, s.floor_pos[0].cpu().numpy(), T.yaw_of(s.floor_quat[0]).cpu().numpy(), extra=stool)
        bp, _ = robot.box_state(self.k)
        # nearest free spot in front of the box, 2 cm steps (stance_near's 8 cm steps stood the robot
        # 0.16-0.24 m off the box; offline IK reaches it from ~0.22 m, not further)
        stance = None
        for dy in sorted(np.arange(-0.30, 0.301, 0.02), key=abs):
            goal = np.array([T.CABINET_X_FRONT - 0.42, bp[1] + dy])
            # 3 cm spare sideways: 1.7 cm off the stool's inflated footprint the walk did not
            # get there in 30 s (relay-dev-v3)
            if all(grid.free(goal + np.array([0.0, e])) for e in (-0.03, 0.0, 0.03)):
                try:
                    grid.route(robot.pos[:2], goal, 0.0)
                except ValueError:
                    continue
                stance = goal
                break
        if stance is None:
            stance = stance_near(grid, robot.pos[:2], bp[1])
        if stance is None:
            return "no_stance_beside_the_stool"
        # aimed 6 cm past the 0.35 m retrieval standoff: the walk stops ~6 cm short (relay-dev-v1: 0.41 m),
        # and with the box beside the stance the arms reach it from 0.35 m, not from 0.41 m (offline IK:
        # 1 cm vs 3-7 cm palm error)
        closer = np.array([T.CABINET_X_FRONT - self.args.relay_standoff, stance[1]])
        # facing the box (not the cabinet): stood 0.2 m beside it facing straight, the left arm had to
        # cross the chest, jammed against the torso and threw the robot over (relay-dev-v13..v17)
        face = float(np.arctan2(bp[1] - closer[1], bp[0] - closer[0])) if self.args.relay_face else 0.0
        r = navigate(robot, stance, face, extend=closer, extra=stool)
        feet_now = [self.cpu(self.r.get_links_pos([self.r.get_link(nm).idx_local]))[0] for nm in T.FOOT_LINKS]
        sp_now = self.cpu(self.env.stool.get_pos())
        self.event("relay:at_board", ok=r.ok, reason=r.reason, metrics=r.metrics, stance=np.round(stance, 3).tolist(),
                   pos=np.round(robot.pos, 3).tolist(), feet=np.round(feet_now, 3).tolist(), stool=np.round(sp_now, 3).tolist(),
                   stool_yaw=round(float(stool[0][2]), 3), stool_box=np.round(stool[0][1], 3).tolist())
        if not r.ok:
            return "walk_to_board_failed"
        if self.args.relay_face:
            # navigate settles the position only (arrived with a 0.39 rad yaw error, relay-dev-v27):
            # turn in place until the heading is within 0.05 rad, <= 6 s
            turned = False
            for _ in range(int(6.0 / T.CONTROL_DT)):
                err = float(np.remainder(face - robot.yaw + np.pi, 2 * np.pi) - np.pi)
                if abs(err) < 0.05:
                    turned = True
                    break
                if not robot.step((0.0, 0.0, float(np.clip(1.5 * err, -0.5, 0.5)))):
                    return "fell_turning_to_the_box"
            self.event("relay:faced", turned=turned, yaw=round(float(robot.yaw), 3), target=round(face, 3))
        self.view = self.args.relay_view
        # feet, base and stool contacts while retrieving (diagnostics)
        step0 = robot.step
        stool_links = None

        def logged(*a, **kw):
            out = step0(*a, **kw)
            gs_ = getattr(robot, "glide_state", None)
            self.effort_note = "reach" if gs_ else ("held" if robot.legs is not None else "walk")
            if robot.steps % 10 == 0:
                ft = [self.cpu(self.r.get_links_pos([self.r.get_link(nm).idx_local]))[0] for nm in T.FOOT_LINKS]
                fz = self.r.get_links_net_contact_force()[0, [self.r.get_link(nm).idx_local for nm in T.FOOT_LINKS], 2].cpu().numpy()
                # commanded vs measured palms and arm joints
                robot.ik._set(robot.pos, robot.quat, robot.q_ref)
                palm_ref = {sd: robot.ik.hand_point(sd, "palm").copy() for sd in SIDES}
                robot.ik._set(robot.pos, robot.quat, robot.joints())
                palm_meas = {sd: robot.ik.hand_point(sd, "palm").copy() for sd in SIDES}
                dq = robot.joints() - robot.q_ref
                arms = {sd: {n.replace(f"{sd}_", "").replace("_joint", ""): round(float(dq[i]), 2)
                             for i, n in enumerate(T.JOINT_NAMES) if n.startswith(sd) and "hand" not in n and abs(dq[i]) > 0.05}
                        for sd in SIDES}
                self.report.setdefault("relay_feet", []).append(dict(
                    t=round(self.t, 2), legs_held=robot.legs is not None, base=np.round(robot.pos, 3).tolist(),
                    palm_err={sd: np.round(palm_meas[sd] - palm_ref[sd], 3).tolist() for sd in SIDES},
                    palm=np.round(palm_meas["left"], 3).tolist(), arm_lag=arms, waist=np.round(robot.joints()[12:15], 2).tolist(),
                    glide=getattr(robot, "glide_state", None), yaw=round(float(robot.yaw), 3),
                    left_ref=np.round(robot.q_ref[[i for i, n in enumerate(T.JOINT_NAMES) if n.startswith("left") and "hand" not in n and not any(k in n for k in ("hip", "knee", "ankle"))]], 2).tolist(),
                    left_meas=np.round(robot.joints()[[i for i, n in enumerate(T.JOINT_NAMES) if n.startswith("left") and "hand" not in n and not any(k in n for k in ("hip", "knee", "ankle"))]], 2).tolist(),
                    feet=np.round(ft, 3).tolist(), fz=np.round(fz, 1).tolist(),
                    qp_fallbacks=getattr(robot, "qp_fallbacks", None), touch=self.robot_touches(robot),
                    stool=np.round(self.cpu(self.env.stool.get_pos()), 3).tolist()))
            return out
        robot.step = logged
        if self.args.relay_cabinet_ext:
            # hand-cabinet contacts enter the stance QP too (M1 feeds it the box contacts only): a
            # 40 N finger push on the side post, unknown to the QP, tipped the robot on to one foot
            # (relay-dev-v25..v28)
            plain_forces = robot.hand_forces

            def forces_with_cabinet(k):
                out = plain_forces(k)
                for name, other, f, point in self.hand_env_contacts(robot):
                    robot.box_contacts.append((name, point, f))
                return out
            robot.hand_forces = forces_with_cabinet
        robot.ik.set_limit("waist_yaw_joint", -self.args.relay_waist_yaw, self.args.relay_waist_yaw)
        if self.args.relay_arm_limits:
            # the box on the 0.90 m board is low and close (0.32 m ahead, 0.26 m up): raising the hand
            # there the IK swung the upper arm back and flexed the elbow, pressing the upper arm into
            # the torso (kN self-contact, relay-dev-v21/v22); keep the arms swinging forward instead
            for sd in SIDES:
                robot.ik.set_limit(f"{sd}_shoulder_pitch_joint", -3.0, 0.0)
                robot.ik.set_limit(f"{sd}_elbow_joint", -0.2, 2.0)
        res = retrieve(robot, self.k, T.TOP_SIZES[self.k], rise_first=bool(self.args.relay_rise))
        robot.step = step0
        self.view = "room"
        self.report["stages"]["floor_retrieve"] = dict(ok=res.ok, reason=res.reason,
                                                       metrics={k: v for k, v in res.metrics.items() if k != "trace"},
                                                       trace=res.metrics.get("trace"))
        self.event("relay:retrieved", ok=res.ok, reason=res.reason)
        if not res.ok:
            return "floor_retrieve_failed"
        r = navigate(robot, GOAL_POSE[0], GOAL_POSE[1], timeout=40.0, extra=stool)
        f = robot.hand_forces(self.k)
        held = min(abs(float(f[sd][1])) for sd in SIDES) > 2.0
        rel = self.place_at_goal(robot) if (r.ok and held) else None
        settled = self.settle_delivered(robot) if rel is not None and rel.ok else dict(ok=False)
        self.report["stages"]["goal"] = dict(walk=dict(ok=r.ok, reason=r.reason, metrics=r.metrics), held_at_goal=bool(held),
                                             release=None if rel is None else dict(ok=rel.ok, reason=rel.reason),
                                             settled=settled, task=robot.info)
        self.event("goal:end", task=robot.info)
        return "done" if robot.info.get("success") and settled["ok"] else ("box_dropped" if not held else "not_settled_in_goal")

    def goal(self):
        """Agile with the box held: walk to the goal zone and let the box drop there."""
        from humanoid.g1_support_retrieval.oracle.oracle import Robot, navigate, release, hold, GOAL_POSE
        self.view = "room"
        self.task_gains()
        held_by = self.on_stool
        robot = Robot(self.env, video=None)
        robot.q_ref = held_by.q_ref.copy()
        robot.hands = dict(held_by.hands)
        robot.carry = getattr(held_by, "carry", {})
        # the same IK (waist limits) as on the stool: the walking robot's own IK caps the waist
        # pitch at 0.2, the holding pose has 0.3, and re-solving there moved the palms off the box
        # right after the hand-over (chain-dev-v25)
        robot.ik = held_by.ik
        # Squeeze servo while walking, palm targets fixed in the measured pelvis frame (so the IK
        # does not chase the gait's sway): with fixed arm references and the physical effort caps
        # the box slid out as the walk started (chain-dev-v22).
        from humanoid.g1_support_retrieval.oracle.oracle import hand_preset
        q_t = robot.q_ref.copy()
        for sd, mode in robot.hands.items():
            if mode is not None:
                q_t = hand_preset(q_t, sd, mode)
        robot.ik._set(robot.pos, robot.quat, q_t)
        # rigid with the pelvis: Agile walks with the pelvis pitched ~0.23 rad forward, and keeping the
        # box level would need the waist beyond its -0.1 rad limit (see to_agile_stance in step_down)
        Rb0 = Rotation.from_quat(robot.quat[[1, 2, 3, 0]]).as_matrix()
        palm_rel = {sd: (Rb0.T @ (robot.ik.hand_point(sd, "palm") - robot.pos),
                         Rb0.T @ robot.ik.d.xmat[robot.ik.wrist[sd]].reshape(3, 3)) for sd in SIDES}
        servo = {"on": True, "offset": 0.0, "f": None}
        plain_step = robot.step

        def step_with_grip(*a, **kw):
            if servo["on"]:
                f = robot.hand_forces(self.k)
                mean = 0.5 * sum(abs(float(f[sd][1])) for sd in SIDES)
                servo["f"] = mean if servo["f"] is None else 0.8 * servo["f"] + 0.2 * mean
                servo["offset"] = float(np.clip(servo["offset"] + np.clip((self.args.carry_grip - servo["f"]) * 2e-5, -4e-4, 4e-4), -0.01, 0.01))
                Rb = Rotation.from_quat(robot.quat[[1, 2, 3, 0]]).as_matrix()
                tasks = {}
                for sd in SIDES:
                    rel, Rrel = palm_rel[sd]
                    inward = np.array([0.0, -1.0 if sd == "left" else 1.0, 0.0])
                    tasks[sd] = ("palm", robot.pos + Rb @ (rel + inward * servo["offset"]), Rb @ Rrel)
                robot.reach(tasks, rate=1.0)
                if robot.steps % 10 == 0:
                    bp, _ = robot.box_state(self.k)
                    self.report.setdefault("walk_trace", []).append(
                        [round(self.t, 2), *np.round(robot.pos, 3).tolist(), round(robot.yaw, 3), round(servo["f"], 1),
                         round(servo["offset"], 4), *np.round(bp, 3).tolist(), np.round(robot.joints()[:12], 2).tolist()])
            return plain_step(*a, **kw)
        robot.step = step_with_grip
        robot.blend_legs = (torch.as_tensor(robot.joints()[robot.agile.leg_idx.cpu().numpy()], device=self.dev,
                                            dtype=torch.float32).unsqueeze(0), 0, 25)     # 0.5 s hand-over
        self._hook_robot(robot)
        ok = hold(robot, 1.0)
        r = navigate(robot, GOAL_POSE[0], GOAL_POSE[1], timeout=40.0) if ok else None
        f = robot.hand_forces(self.k)
        held = min(abs(float(f[sd][1])) for sd in SIDES) > 2.0
        servo["on"] = False                       # let go at the goal
        self.report["stages"]["walk_grip_N"] = round(servo["f"] or 0.0, 1)
        rel = release(robot, self.k) if (r is not None and r.ok and held) else None
        settled = self.settle_delivered(robot) if rel is not None and rel.ok else dict(ok=False)
        self.report["stages"]["goal"] = dict(walk=None if r is None else dict(ok=r.ok, reason=r.reason, metrics=r.metrics),
                                             held_at_goal=bool(held),
                                             release=None if rel is None else dict(ok=rel.ok, reason=rel.reason),
                                             settled=settled, task=robot.info)
        self.event("goal:end", task=robot.info)
        return "done" if robot.info.get("success") and settled["ok"] else ("box_dropped" if not held else "not_settled_in_goal")

    # ------------------------------------------------------------------ run
    def run(self):
        a = self.args
        self.build()
        self.init_stiff()
        self.place_initial()
        resumed = None
        if a.resume_checkpoint:
            resumed = load_chain_checkpoint(self, a.resume_checkpoint)
            self.report["diagnostic_resume"] = str(a.resume_checkpoint)
            self.report["automatic_reset_disabled"] = bool(self.env.chain_preserve_terminal)
        self.install_position_target_limits()
        self.install_actuator_monitor()
        self.r.set_dofs_force_range(-self.p["effort"], self.p["effort"], self.env.dofs)
        self.writer = VideoWriter(a.out / "motion.mp4", fps=25)
        self.next_frame = self.t
        stamp = time.perf_counter()
        status = "not_started"
        try:
            self.writer.append_data(self.frame())
            last = {"lift": "standup", "retrieve": "climb", "stepdown": "climb", "": "goal"}.get(a.stop_after, a.stop_after)
            goal_fn = self.relay_goal if a.relay else self.goal
            stages = (("standup", self.lift_and_stand), ("agile_stance", self.to_agile_stance), ("walk", self.walk),
                      ("setdown", self.setdown),
                      ("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
            if a.carry > 0 and a.walk_mode in ("steps", "planned"):
                stages = (("standup", self.lift_and_stand),
                          ("walk", self.walk_planned if a.walk_mode == "planned" else self.walk_steps), ("setdown", self.setdown),
                          ("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
            if a.resume_checkpoint:
                if resumed["stage"] == "on_stool":
                    stages = (("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
                elif a.carry <= 0:
                    raise ValueError("Checkpoint resume requires carry > 0")
                elif resumed["stage"] == "lift":
                    stages = (("standup", self.stand_loaded),) + stages[1:]
                elif resumed["stage"] == "stool_lowered":
                    # Keep the setdown stage label (including its waist gains),
                    # but skip every lowering/reattach initialization operation.
                    stages = (("setdown", lambda: self.setdown(resume_lowered=True)),
                              ("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
                elif resumed["stage"] == "stool_released":
                    stages = (("setdown", lambda: self.setdown(resume_released=True)),
                              ("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
                else:
                    names = [name for name, _ in stages]
                    stages = stages[names.index(resumed["stage"]) + 1:]
            if a.carry <= 0 and not a.resume_checkpoint:  # the stool already stands where it is needed
                stages = (("stool", self.lift_in_place), ("climb", self.climb_retrieve_stepdown), ("goal", goal_fn))
                last = {"lift": "stool", "standup": "stool", "walk": "stool", "setdown": "stool"}.get(last, last)
                if a.start_at == "climb":     # development: start standing behind the placed stool
                    stages = stages[1:]
                if a.start_at == "relay":     # development: box already on the board below
                    d, w, h = T.TOP_SIZES[self.k]
                    box = self.env.top_boxes[self.k]
                    box.set_pos(self.tensor([a.relay_box[0], a.relay_box[1], 0.90 + h / 2 + 0.002]), zero_velocity=True)
                    box.set_quat(self.tensor([1, 0, 0, 0]), zero_velocity=True)
                    stages = stages[2:]
            for name, fn in stages:
                self.active_stage = name
                status = fn()
                # Preserve the observed prefix before a later phase can fail.
                # The final report still audits every physics tick of the run.
                prefix_checks = self.actuator_report()
                self.report.setdefault("actuator_prefix_checks", {})[name] = prefix_checks
                self.event("actuators:stage_end", completed_stage=name,
                           **{key: prefix_checks[key] for key in
                              ("actuator_checks", "max_effort_ratio", "max_speed_ratio", "max_joint_limit_overshoot")})
                if status != "done":
                    status = f"{name}:{status}"
                    break
                if (name in ("standup", "walk", "setdown") and a.save_checkpoint
                        and not (name == "standup" and a.stop_after == "lift")):
                    checkpoint_path = a.save_checkpoint if name == "standup" else a.save_checkpoint.with_name(
                        a.save_checkpoint.stem + "-" + name + a.save_checkpoint.suffix)
                    try:
                        save_chain_checkpoint(self, checkpoint_path, stage=name)
                    except Exception as exc:
                        # Recording a replay is optional. An I/O/serialization
                        # failure must not discard a stable physical episode.
                        self.report["checkpoint_error"] = dict(type=type(exc).__name__, message=str(exc))
                        self.event("checkpoint:failed", **self.report["checkpoint_error"])
                    else:
                        self.event("checkpoint:saved", path=str(checkpoint_path), diagnostic_only=True)
                if name == last:
                    status = "success" if name == "goal" else f"stopped_after_{a.stop_after}"
                    break
        except Exception as exc:
            status = f"error:{type(exc).__name__}:{exc}"
            self.report["exception"] = dict(type=type(exc).__name__, message=str(exc))
            raise
        finally:
            try:
                terminal_q, _ = self.measured_q()
                self.report["terminal_robot_q"] = terminal_q.tolist()
                self.report["terminal_reference_q"] = self.qref.tolist()
                self.report["terminal_controller_phase"] = getattr(self, "active_stiff_phase", None)
                self.report["terminal_stool"] = dict(
                    position=self.cpu(self.env.stool.get_pos()).tolist(),
                    quaternion=self.cpu(self.env.stool.get_quat()).tolist(),
                    velocity=self.cpu(self.env.stool.get_vel()).tolist(),
                    angular_velocity=self.cpu(self.env.stool.get_ang()).tolist())
                # A requested stop raises inside the physics loop. Preserve the
                # release evidence even when setdown() cannot write its result.
                if self.active_stage == "setdown":
                    self.report["setdown_debug"] = dict(
                        release_start=self.ctx.metrics.get("release_start"),
                        release_trace=self.ctx.metrics.get("release_trace", []))
            except Exception as exc:
                self.report["terminal_state_recording_error"] = str(exc)
            try:
                self.writer.append_data(self.frame())
            finally:
                self.writer.close()
            checks = self.actuator_report()
            if status == "success" and not checks["actuator_checks"]:
                status = "actuator_checks_failed"
            self.report.update(status=status, sim_seconds=round(self.t, 2), wall_seconds=round(time.perf_counter() - stamp, 1),
                               **checks,
                               object_attachment=False, runtime_pose_writes="initial placement only")
            (a.out / "result.json").write_text(json.dumps(self.report, indent=2, default=float))
            print("RESULT", json.dumps({k: self.report[k] for k in ("status", "stages", "sim_seconds", "wall_seconds")}, default=float),
                  flush=True)
        return self.report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=HERE / "runs/stool-chain")
    ap.add_argument("--seed", type=int, default=2, help="task seed: one_support, central target on the 1.25 m level")
    ap.add_argument("--drop-x", type=float, default=3.03, help="stool centre where it is put down (pelvis ~0.40 m from the cabinet on it)")
    ap.add_argument("--carry", type=float, default=1.0, help="distance the stool is carried, m (0: verified lift/set-down in place)")
    ap.add_argument("--set-ahead", type=float, default=0.47,
                    help="stool centre ahead of the standing pelvis when set down (stool-v3: 0.46-0.48; 0.58 crouched)")
    ap.add_argument("--carry-ahead", type=float, default=0.33, help="hands (MCP) ahead of the standing pelvis while walking")
    ap.add_argument("--carry-mcp-z", type=float, default=0.95, help="hands (MCP) height while walking")
    ap.add_argument("--stand-up-dz", type=float, nargs=1, default=[0.30], help="first, straight-up part of the stand-up")
    ap.add_argument("--mask-upper", type=int, default=0, help="hide the arm pose from the Agile policy (1/0)")
    ap.add_argument("--walk-speed", type=float, default=0.25)
    ap.add_argument("--walk-mode", default="planned", choices=("planned", "steps", "agile"),
                    help="planned: smooth references/contact QP; steps/agile: historical diagnostic controllers")
    ap.add_argument("--planned-max-steps", type=int, default=0, help="diagnostic footfall limit (0: continue to goal)")
    ap.add_argument("--planned-com-tol", type=float, default=0.012)
    ap.add_argument("--planned-speed-tol", type=float, default=0.02)
    ap.add_argument("--position-margin", type=float, default=0.01,
                    help="position targets stay this far inside physical joint stops, rad")
    ap.add_argument("--hand-position-margin", type=float, default=0.04,
                    help="finger position targets allow extra room for contact deflection, rad")
    ap.add_argument("--setdown-thumb-guard", type=int, choices=(0, 1), default=1,
                    help="experimental isolated setdown thumb-load relief; 0 retains baseline control")
    ap.add_argument("--save-checkpoint", type=Path, default=None,
                    help="save lift, standup, walk, stool-lowered, stool-released (before final arm/stance hand-off), setdown and on-stool diagnostic states")
    ap.add_argument("--save-on-stool-checkpoint", type=Path, default=None,
                    help="save verified top support before the first retrieval tick; also derived from --save-checkpoint")
    ap.add_argument("--resume-checkpoint", type=Path, default=None,
                    help="diagnostic only: resume a saved boundary; stool-lowered resumes unloading, stool-released resumes the final arm/stance hand-off")
    ap.add_argument("--step-length", type=float, default=0.12, help="swing-foot advance per cycle, m")
    ap.add_argument("--step-seconds", type=float, default=8.0, help="seconds per cycle")
    ap.add_argument("--step-lift", type=float, default=0.045, help="swing-foot height, m")
    ap.add_argument("--step-com-gain", type=float, default=0.015, help="per-tick integral gain of the single-support CoM correction")
    ap.add_argument("--step-com-tol", type=float, default=0.01, help="measured-CoM gate before lifting the swing foot, m (push_box: 0.025)")
    ap.add_argument("--bal-sign", type=float, nargs=2, default=[1.0, 1.0], help="sign of the ankle roll / pitch balance terms")
    ap.add_argument("--bal-clip", type=float, default=0.004, help="ankle balance-feedback target offset limit, rad")
    ap.add_argument("--elliptic-friction", type=int, default=0, help="Genesis elliptic friction cone (1/0; the verified push/carry runs used it)")
    ap.add_argument("--upright", type=int, default=1, help="straighten the trunk after the stand-up before walking (1/0)")
    ap.add_argument("--upright-pelvis", type=float, default=0.2, help="pelvis pitch bound while upright, rad")
    ap.add_argument("--upright-waist", type=float, default=0.1, help="waist pitch bound while upright, rad")
    ap.add_argument("--step-inset", type=float, default=0.0,
                    help="legacy steps mode: lateral stance inset, m; planned mode reads actual collision geometry")
    ap.add_argument("--model-torso-mass", type=float, default=0.0,
                    help="diagnostic lift-planner mass override, kg; 0 synchronizes the full runtime model. "
                         "Planned walking always synchronizes the actual simulator inertials")
    ap.add_argument("--step-sway", type=float, default=1.0, help="stool follows the lateral centre-of-mass shift by this fraction")
    ap.add_argument("--walk-gravcomp", type=int, default=1, help="leg gravity-compensation feed-forward while stepping (1/0)")
    ap.add_argument("--skip-retrieve", action="store_true", help="development: step down without the box")
    ap.add_argument("--extra-squeeze", type=float, default=0.0, help="palms this much further in before stepping down, m")
    ap.add_argument("--stepdown-box-up", type=float, default=0.12, help="box this much higher vs the base while stepping down")
    ap.add_argument("--stepdown-box-out", type=float, default=0.03, help="... and this much further out")
    # off by default: shifting the base reference also moves the QP's foot targets (chain-dev-v16)
    ap.add_argument("--com-gain", type=float, default=0.0, help="outer CoM loop on one foot while stepping down (0: off)")
    ap.add_argument("--stepdown-mode", default="native", choices=("native", "qp"),
                    help="native: stiff PD + static torques + ankle balance feedback; qp: contact QP torques")
    ap.add_argument("--stepdown-slow", type=float, default=1.5, help="step-down duration vs the planned climb")
    ap.add_argument("--carry-grip", type=float, default=18.0, help="mean palm force kept while stepping down and walking, N")
    ap.add_argument("--torsional-friction", type=int, default=0, help="Genesis torsional friction at contacts (1/0)")
    ap.add_argument("--hug", type=int, default=0, help="hug the box to the chest before stepping down (1/0)")
    ap.add_argument("--relay", type=int, default=1, help="put the box on the board below, step down, take it from the floor")
    ap.add_argument("--relay-dy", type=float, default=0.22, help="box placed this far to the left of the stool line")
    ap.add_argument("--relay-waist", type=float, default=0.0,
                    help="waist yaw (rad) while placing the box beside the stool: with the waist held "
                         "straight the arms reached 0.20 m aside at most (chain-relay-v8)")
    ap.add_argument("--relay-in", type=float, default=0.08, help="box centre this far behind the cabinet front")
    ap.add_argument("--climb-mode", default="qp", choices=("qp", "native"), help="controller for the climb onto the stool")
    ap.add_argument("--climb-com-weight", type=float, default=0.0,
                    help="optional measured XY COM acceleration cost during formal climb")
    ap.add_argument("--climb-com-inset", type=float, default=0.0,
                    help="metres to move the leading-foot single-support COM target inward")
    ap.add_argument("--climb-ankle-roll-margin", type=float, default=0.02,
                    help="ankle roll IK reserve during climb planning, radians")
    ap.add_argument("--climb-ankle-pitch-margin", type=float, default=0.02,
                    help="ankle pitch IK reserve during climb planning, radians")
    ap.add_argument("--climb-contact-stabilization", choices=("reference", "velocity"), default="reference",
                    help="formal climb contact acceleration stabilization")
    ap.add_argument("--climb-position-guard", type=float, default=None,
                    help="optional predicted leg position margin during formal climb, radians")
    ap.add_argument("--hug-ahead", type=float, default=0.20, help="grip centre ahead of the pelvis when hugging")
    ap.add_argument("--hug-deg", type=float, default=60.0, help="fingers-up angle of the hands when hugging")
    ap.add_argument("--hug-up", type=float, default=0.30, help="grip centre above the pelvis when hugging")
    ap.add_argument("--hug-seconds", type=float, default=4.0)
    ap.add_argument("--effort-caps", default="physical", choices=("physical", "task"),
                    help="joint effort caps: G1 model ratings, or the task's (300 N m on arms and hands)")
    ap.add_argument("--agile-stance-seconds", type=float, default=5.0, help="move to Agile's stance before the hand-over")
    ap.add_argument("--arm-rate-scale", type=float, default=1.0, help="arm reference rate on the stool vs the floor")
    ap.add_argument("--stool-waist-rate", type=float, default=0.35, help="maximum waist reference speed on the stool, rad/s")
    ap.add_argument("--stool-waist-accel", type=float, default=0.8, help="maximum waist reference acceleration on the stool, rad/s^2")
    ap.add_argument("--carry-com", type=float, default=-0.01, help="CoM (with the stool) vs the nominal standing CoM, x")
    ap.add_argument("--walk-lead", type=float, default=0.06, help="stop commanding this far before the goal")
    ap.add_argument("--stop-after", default="", choices=("",) + STAGES)
    ap.add_argument("--relay-standoff", type=float, default=0.29, help="walk goal off the cabinet for the floor retrieval")
    ap.add_argument("--relay-view", default="shelf2", choices=("shelf2", "side2"), help="camera for the floor retrieval")
    ap.add_argument("--relay-face", type=int, default=0, help="stance facing the box instead of the cabinet (1/0)")
    ap.add_argument("--self-collision", type=int, default=1,
                    help="robot self-collision (1/0). The task env runs without it; stool_carry was verified with it")
    ap.add_argument("--relay-cabinet-ext", type=int, default=0, help="feed hand-cabinet contact forces to the stance QP (1/0)")
    ap.add_argument("--relay-arm-limits", type=int, default=0, help="shoulder pitch <= 0, elbow >= -0.2 while retrieving from the floor")
    ap.add_argument("--relay-rise", type=int, default=0,
                    help="back/up/in approach points before the reach (1/0): from the default pose they led the IK "
                         "into an elbow-hyperextended branch with the upper arm inside the torso (relay-dev-v12..v20)")
    ap.add_argument("--relay-waist-yaw", type=float, default=0.25, help="IK waist yaw limit for the floor retrieval")
    ap.add_argument("--relay-box", type=float, nargs=2, default=[3.396, 0.202],
                    help="development (--start-at relay): box x y on the board below")
    ap.add_argument("--start-at", default="", choices=("", "climb", "relay"),
                    help="development only (with --carry 0): start standing behind the placed stool")
    # stool_carry's verified settings
    ap.add_argument("--mass", type=float, default=1.5)
    ap.add_argument("--friction", type=float, default=0.5)
    ap.add_argument("--gap", type=float, default=0.46)
    ap.add_argument("--below-rail", type=float, default=0.02)
    ap.add_argument("--out-clear", type=float, default=0.015)
    ap.add_argument("--hand-x-offset", type=float, default=0.0)
    ap.add_argument("--hand-pitch", type=float, default=90.0)
    ap.add_argument("--thumb-up", type=float, default=0.72)
    ap.add_argument("--com-shift", type=float, default=0.04)
    ap.add_argument("--crouch", type=float, default=0.42)
    ap.add_argument("--insert-force", type=float, default=3.0)
    ap.add_argument("--min-reach", type=float, default=0.03)
    ap.add_argument("--lift", type=float, default=0.10)
    ap.add_argument("--lift-root", type=float, default=0.06)
    ap.add_argument("--retreat", type=float, default=0.12)
    ap.add_argument("--max-squeeze", type=float, default=30.0)
    ap.add_argument("--leg-kp", type=float, default=3000.0)
    ap.add_argument("--leg-kd", type=float, default=40.0)
    ap.add_argument("--servo-gain", type=float, default=4e-5)
    ap.add_argument("--track-gain", type=float, default=0.02)
    args = ap.parse_args(argv)
    if not np.isfinite(args.climb_com_weight) or args.climb_com_weight < 0:
        ap.error("--climb-com-weight must be finite and nonnegative")
    if not np.isfinite(args.climb_com_inset) or not 0 <= args.climb_com_inset <= 0.03:
        ap.error("--climb-com-inset must be between 0 and 0.03 metres")
    if not np.isfinite(args.climb_ankle_roll_margin) or not 0.02 <= args.climb_ankle_roll_margin <= 0.1:
        ap.error("--climb-ankle-roll-margin must be between 0.02 and 0.1 radians")
    if not np.isfinite(args.climb_ankle_pitch_margin) or not 0.02 <= args.climb_ankle_pitch_margin <= 0.1:
        ap.error("--climb-ankle-pitch-margin must be between 0.02 and 0.1 radians")
    if args.climb_position_guard is not None and (not np.isfinite(args.climb_position_guard)
                                                or not 0 <= args.climb_position_guard <= 0.05):
        ap.error("--climb-position-guard must be between 0 and 0.05 radians")
    args.out = recording_directory(args.out)
    src = args.out / "sources"
    src.mkdir()
    shutil.copy2(Path(__file__), src / Path(__file__).name)
    for module in ("stool_walk.py", "entry_reference.py", "cabinet_clearance.py", "chain_checkpoint.py", "audit_chain.py", "thumb_guard.py"):
        if (HERE / module).exists():
            shutil.copy2(HERE / module, src / module)
    task_dir = HERE.parent
    for relative in ("solution/carry_box/plan_carry.py", "solution/underhand_lift/step_on.py",
                     "solution/carry_climb_retrieve/continuation.py", "solution/step_up/contact_wbc.py",
                     "solution/step_up/constrained_step.py", "solution/step_up/math_utils.py",
                     "solution/step_up/configs/sonic.json", "solution/carry_walk/plan_walk.py",
                     "solution/underhand_lift/phases.py", "solution/underhand_lift/hand_model.py",
                     "solution/underhand_lift/run_underhand.py", "solution/stool_carry/run_stool.py",
                     "solution/push_box/run_push.py", "oracle/oracle.py", "oracle/navigation.py",
                     "task_spec.py", "genesis_env.py", "cabinets.py"):
        target = src / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(task_dir / relative, target)
    (args.out / "config.json").write_text(json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}, indent=2))
    (args.out / "planning.json").write_text(json.dumps(dict(box_size=list(json.loads((STOOL_DIR / "meta.json").read_text())["size"]),
                                                            box_mass_kg=args.mass, support="folding_stool")))
    return Chain(args).run()


if __name__ == "__main__":
    main()
