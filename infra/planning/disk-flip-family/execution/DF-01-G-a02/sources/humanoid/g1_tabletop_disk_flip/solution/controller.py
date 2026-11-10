"""Slow joint-only oracle for slide, opposing-face clamp, flip and release.

Validation records define its observed operating points. Planned waypoints alone
are not feasibility evidence; measured contact guards stop failed execution.
"""
import math

import numpy as np
import mujoco
from scipy.spatial.transform import Rotation

from humanoid.g1_tabletop_assembly.solution.controller import Controller
from humanoid.g1_tabletop.genesis_env import CONTROL_DT
from infra.oracle import RollingPlanner


def smooth(t):
    t = np.clip(t, 0., 1.)
    return t**3*(10.-15.*t+6.*t*t)


class GentleController(Controller):
    def ready(self):
        self.configure_grasp_ik()
        self.event("settle_raised_separated_hands")
        self.hold(.5)

    def configure_grasp_ik(self):
        # Stay on the ordinary elbow/shoulder branch instead of folding an arm
        # through the torso to satisfy a Cartesian goal.
        for name, low, high in (("waist_pitch_joint", -.3, .5), ("waist_roll_joint", -.25, .25),
                ("waist_yaw_joint", -.7, .7), ("left_shoulder_roll_joint", -.1, 1.8),
                ("right_shoulder_roll_joint", -1.8, .1), ("left_elbow_joint", .05, 2.5),
                ("right_elbow_joint", .05, 2.5)):
            self.ik.set_limit(name, low, high)

    def nominal_hands(self):
        """Keep the steady PD compression when starting the next local motion."""
        self.ik._set(self.env.base_position, (1, 0, 0, 0), self.q)
        return {side: (self.ik.hand_point(side, "palm").copy(),
                       self.ik.d.xmat[self.ik.wrist[side]].reshape(3, 3).copy())
                for side in ("left", "right")}

    def attitude_correction(self, state, desired_normal):
        q = state["quat"]
        normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
        error = np.cross(normal, desired_normal)
        correction = 2.*error
        magnitude = np.linalg.norm(correction)
        if magnitude > .16:
            correction *= .16/magnitude
        previous = getattr(self, "attitude_rotvec", np.zeros(3))
        change = (CONTROL_DT/(.25+CONTROL_DT))*(correction-previous)
        speed = np.linalg.norm(change)/CONTROL_DT
        if speed > .08:
            change *= .08/speed
        self.attitude_rotvec = previous+change
        return Rotation.from_rotvec(self.attitude_rotvec).as_matrix()

    def select_approach_branch(self, tasks, handoffs=(), trials=32, seed_hints=()):
        """Bounded key-state search; a candidate is not an execution witness."""
        measured = self.actual_q()
        rng = np.random.default_rng(19)
        candidates = []
        for trial in range(trials):
            seed = measured.copy()
            if trial:
                seed[self.ik.upper] = self.initial_q[self.ik.upper]
            if trial > 1:
                seed[self.ik.upper] = np.clip(seed[self.ik.upper]+rng.normal(0., 1.2, len(self.ik.upper)),
                                            self.ik.lo, self.ik.hi)
            if trial < len(seed_hints):
                seed[self.ik.upper] = np.asarray(seed_hints[trial])[self.ik.upper]
            q, errors = self.ik.solve(self.env.base_position, (1, 0, 0, 0), seed, tasks,
                                      iters=120, damping=.015, w_rot=.35)
            if max(errors.values()) > .008:
                continue
            # Check all self-contact, including shoulders against the torso.
            mujoco.mj_forward(self.ik.m, self.ik.d)
            bad = any(contact.dist < -.001 for contact in self.ik.d.contact)
            probe = q.copy()
            for handoff in handoffs:
                if bad:
                    break
                probe, residual = self.ik.solve(self.env.base_position, (1, 0, 0, 0), probe, handoff,
                                               iters=100, damping=.015, w_rot=.35)
                mujoco.mj_forward(self.ik.m, self.ik.d)
                bad = max(residual.values()) > .008 or any(contact.dist < -.001 for contact in self.ik.d.contact)
            if not bad:
                candidates.append((np.linalg.norm(q[self.ik.upper]-measured[self.ik.upper]), q))
        if not candidates:
            raise RuntimeError("approach key-state IK search exhausted without a usable candidate")
        _, solution = min(candidates, key=lambda item: item[0])
        target = self.q.copy()
        target[self.ik.upper] = solution[self.ik.upper]
        self.event("reconfigure_for_bimanual_approach", candidates=len(candidates), trials=trials,
                   collision_scope="approach_and_handoff_robot_self_collision_only")
        # This is a local joint motion, executed under the physics evaluator.
        # The key-state check does not certify the swept physical motion.
        seconds = max(12., float(np.max(np.abs(target-self.q)))*1.875/.25)
        self.move_joints(target, seconds=seconds)
        self.move_hands(tasks, seconds=4.)

    def event(self, phase, **metadata):
        self.phase = phase
        self.events.append(dict(phase=phase, time=self.env.physics_steps*self.env.sim_dt, **metadata))

    def move_hands(self, tasks, seconds=4., **kwargs):
        kwargs["rate"] = min(kwargs.get("rate", .35), .35)
        return super().move_hands(tasks, seconds=seconds, **kwargs)

    def reach(self, tasks, rate=.35, **kwargs):
        if not hasattr(self, "local_planner"):
            self.local_planner = RollingPlanner(horizon=1)
        measured = self.env.observe()
        self.last_hand_goals = {side: dict(kind=kind, position=np.asarray(position).tolist())
                                for side, (kind, position, rotation) in tasks.items()}
        errors = {}
        def local_plan(state, goal, horizon):
            # Solve from measured joints, but slew the persistent reference.
            # Resetting the reference to measured joints every tick removes the
            # steady PD error needed to overcome model/friction discrepancies.
            goals = {}
            for side, (kind, position, rotation) in tasks.items():
                position = np.array(position, dtype=float, copy=True)
                feedback = kwargs.get("feedback", 0.)
                if feedback:
                    actual, _ = self.hand_pose(side, kind)
                    position += np.clip(feedback*(position-actual), -.004, .004)
                goals[side] = (kind, position, rotation)
            seed = self.q.copy() if kwargs.get("seed_reference", False) else np.asarray(state["joint_position"])
            if getattr(self.ik, "uses_measured_finger_geometry", False):
                finger_indices = [index for name, index in self.index.items() if "_hand_" in name]
                seed[finger_indices] = np.asarray(state["joint_position"])[finger_indices]
            solution, residual = self.ik.solve(self.env.base_position, (1, 0, 0, 0), seed,
                goals, iters=kwargs.get("iters", 12),
                damping=.015, w_rot=.35, max_step=.10)
            errors.update(residual)
            active = self.ik.upper
            self.q[active] += np.clip(solution[active]-self.q[active],
                                      -min(rate, .35)*CONTROL_DT, min(rate, .35)*CONTROL_DT)
            yield self.q.tolist()
        chunk = self.local_planner.next_chunk(measured, {"hands": list(tasks)}, local_plan)
        self.q = np.asarray(chunk["actions"][0])
        self.last_ik_errors = dict(errors)
        return errors

    def require_stage(self, stage):
        if self.env.status.get("stage", 0) < stage:
            raise RuntimeError(f"physical stage {stage} not established: {self.env.status}")


def slide(c):
    """Push the far rim with a straight thumb, avoiding downward table loading."""
    cfg = c.env.cfg
    face = Rotation.from_euler("x", math.pi/2).as_matrix()
    c.ready()
    for side in ("left", "right"):
        c.hand_preset(side, "open", seconds=2.)
    disk = np.asarray(c.object_state("disk")["pos"])
    tip = disk+[cfg.disk_radius+.025, 0., .10]
    c.move({"left": ("thumb", tip.copy(), face)}, seconds=8., phase="approach_far_rim")
    tip[2] = cfg.table_height+.002
    c.move({"left": ("thumb", tip.copy(), face)}, seconds=8., phase="lower_outside_far_rim")
    c.event("gentle_rim_contact")
    for _ in range(1000):
        state = c.object_state("disk")
        if state["hand_force_magnitudes_n"]["left"] >= .10:
            break
        tip[0] -= .002*CONTROL_DT
        c.reach({"left": ("thumb", tip.copy(), face)}, feedback=1.5)
        c.step()
    else:
        raise RuntimeError("rim contact was not established")
    c.event("slide_to_near_edge")
    start = np.asarray(c.object_state("disk")["pos"])
    for i in range(2500):
        state = c.object_state("disk")
        actual = np.asarray(state["pos"])
        desired_x = start[0]+smooth((i+1)/1800)*(cfg.edge_center[0]-start[0])
        tip[0] += np.clip(desired_x-actual[0], -.010*CONTROL_DT, .010*CONTROL_DT)
        tip[0] = max(tip[0], actual[0]+cfg.disk_radius-.002)
        # Track the disk laterally. A fixed-Y pusher amplifies any sideways
        # displacement because the contact normal then points away from centre.
        lateral = actual[1]+2.*(actual[1]-cfg.start_xy[1])
        tip[1] += np.clip(lateral-tip[1], -.004*CONTROL_DT, .004*CONTROL_DT)
        # The thumb remains near the mid-height of the rim; it never presses
        # through the top face to manufacture tangential friction.
        tip[2] = cfg.table_height+.002
        c.reach({"left": ("thumb", tip.copy(), face)}, feedback=1.5)
        c.step()
        if c.env.status["stage"] >= 1 and actual[0] <= cfg.edge_center[0]+.001:
            return
    c.require_stage(1)


def clamp(c):
    cfg = c.env.cfg
    faces = {s: Rotation.from_euler("z", angle, degrees=True).as_matrix()
                 @ Rotation.from_euler("x", math.pi/2).as_matrix()
             for s, angle in (("left", -25), ("right", 25))}
    c.event("clear_pusher_before_clamp")
    tip, rot = c.hand_pose("left", "thumb")
    c.move_hands({"left": ("thumb", tip+[0., 0., .12], rot)}, seconds=6.)
    c.configure_grasp_ik()
    for side in ("left", "right"):
        c.hand_preset(side, "open", seconds=2.)
    # Bend the contacting fingers while keeping the palms vertically separated.
    # Fold unused fingers away so they cannot move the resultant support point
    # sideways, which would roll the disk as table support disappears.
    fingers = c.q.copy()
    for side, sign, active in (("left", -1., "index"), ("right", 1., "middle")):
        for finger in ("index", "middle"):
            fingers[c.index[f"{side}_hand_{finger}_0_joint"]] = 0. if finger == active else sign*1.4
            fingers[c.index[f"{side}_hand_{finger}_1_joint"]] = sign*.35 if finger == active else 0.
    c.move_joints(fingers, seconds=6.)
    disk = np.asarray(c.object_state("disk")["pos"])
    top = np.array([cfg.edge_x-.135, disk[1]+.070, cfg.rest_z+.065])
    lower = np.array([cfg.edge_x-.115, disk[1]-.070, cfg.rest_z-.065])
    c.event("approach_exposed_rim")
    search = {"left": ("palm", top.copy(), faces["left"]),
              "right": ("palm", lower.copy(), faces["right"])}
    closed = {"left": ("palm", top+[0., 0., -.037], faces["left"]),
              "right": ("palm", lower+[0., 0., .037], faces["right"])}
    c.select_approach_branch({"left": ("palm", top+[0., .12, .12], faces["left"]),
                             "right": ("palm", lower+[0., -.15, 0.], faces["right"])},
                             handoffs=(search, closed))
    c.move_hands(search, seconds=8.)
    c.event("opposing_face_clamp")
    contacted = {"left": False, "right": False}
    alignment = {side: np.zeros(3) for side in contacted}
    for _ in range(3500):
        state = c.object_state("disk")
        if state["hand_forces_n"]["left"][2] > .15 or state["hand_forces_n"]["right"][2] < -.15:
            raise RuntimeError("contact search touched the wrong disk face")
        for side, point, direction in (("left", top, -1.), ("right", lower, 1.)):
            actual, _ = c.hand_pose(side)
            # Soft arms have a steady lateral tracking error under gravity and
            # contact. Integrate only tangent directions; the normal direction
            # remains force-controlled. Corrections are slow and bounded.
            alignment[side][:2] += np.clip(.2*(point[:2]-actual[:2]), -.002, .002)*CONTROL_DT
            alignment[side][:2] = np.clip(alignment[side][:2], -.05, .05)
            force = state["hand_force_magnitudes_n"][side]
            contacted[side] = contacted[side] or force > .15
            target = (4.5 if side == "left" else 5.7) if all(contacted.values()) else .3
            velocity = (.0015 if not contacted[side] else
                        np.clip((target-force)*.001, -.001, .0007))
            point[2] += direction*velocity*CONTROL_DT
        c.reach({"left": ("palm", top+alignment["left"], faces["left"]),
                 "right": ("palm", lower+alignment["right"], faces["right"])}, feedback=.5)
        c.step()
        forces = state["hand_force_magnitudes_n"]
        if (c.env.status["stage"] >= 2 and min(forces.values()) >= 3.
                and forces["right"]-forces["left"] >= .8):
            c.grip_targets = {"left": top.copy(), "right": lower.copy()}
            return
    raise RuntimeError("load-bearing bimanual preload not established within the local budget")


def lift(c):
    c.configure_grasp_ik()
    cfg = c.env.cfg
    disk = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    lifted = disk.copy()
    lifted[0] += .04
    lifted[2] = cfg.table_height+cfg.disk_radius+cfg.clearance+.035
    c.event("lift_clear_of_table")
    squeeze = {"left": 0., "right": 0.}
    for i in range(550):
        translation = smooth(min((i+1)/500, 1.))*(lifted-disk)
        # First clear the thin rim, then bring the grasp forward of the torso.
        translation[0] = .04*smooth(np.clip((i+1-200)/300, 0., 1.))
        state = c.object_state("disk")
        correction = c.attitude_correction(state, np.array([0., 0., 1.]))
        for side in squeeze:
            target = 4.5 if side == "left" else 5.7
            squeeze[side] += np.clip((target-state["hand_force_magnitudes_n"][side])*.0005,
                                     -.001, .001)*CONTROL_DT
        c.reach({side: ("palm", disk+translation+correction@(hands[side][0]-disk+[0., 0.,
                     (-1. if side == "left" else 1.)*squeeze[side]]), correction@hands[side][1]) for side in hands}, feedback=.25)
        c.step()
        if c.env.status["stage"] >= 3:
            return
    c.require_stage(3)


def pinch_loads(state, cfg):
    q = state["quat"]
    normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    centre = np.asarray(state["pos"])
    loads = {side: {"top": 0., "bottom": 0.} for side in ("left", "right")}
    for side, contacts in state["hand_contacts"].items():
        for contact in contacts:
            height = np.dot(np.asarray(contact["position"])-centre, normal)
            offset = np.asarray(contact["position"])-centre
            if abs(height) > cfg.disk_height/2+.002 or np.linalg.norm(offset-height*normal) > cfg.disk_radius+.002:
                continue
            force = np.dot(contact["force_n"], normal)
            if height > cfg.disk_height*.2:
                loads[side]["top"] += max(0., -force)
            elif height < -cfg.disk_height*.2:
                loads[side]["bottom"] += max(0., force)
    return loads


def pinch_group_targets(c, state, base_force, support_fraction=1.):
    """Allocate each finger's normal load from measured contact lever arms."""
    from .grasp_wrench import allocate_normal_forces
    q = state["quat"]
    rotation = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    normal, centre = rotation[:, 2], np.asarray(state["pos"])
    keys = [(s, f) for s in ("left", "right") for f in ("thumb", "index", "middle")]
    loads = {key: 0. for key in keys}
    points = {key: np.zeros(3) for key in keys}
    tangent_torque = np.zeros(3)
    for side, samples in state["hand_contacts"].items():
        palm, hand_rotation = c.hand_pose(side)
        thumb_face = getattr(c, "pinch_thumb_faces", {}).get(side, -1)
        for sample in samples:
            point, force = np.asarray(sample["position"]), np.asarray(sample["force_n"])
            offset = point-centre
            height = float(offset@normal)
            if (abs(height) > c.env.cfg.disk_height/2+.002
                    or np.linalg.norm(offset-height*normal) > c.env.cfg.disk_radius+.002):
                continue
            if -thumb_face*height > c.env.cfg.disk_height*.2:
                finger = "index" if (hand_rotation.T@(point-palm))[2] > 0 else "middle"
                load = max(0., thumb_face*float(force@normal))
            elif thumb_face*height > c.env.cfg.disk_height*.2:
                finger, load = "thumb", max(0., -thumb_face*float(force@normal))
            else:
                continue
            key = (side, finger)
            loads[key] += load
            points[key] += load*(rotation.T@offset)
            tangent_torque += np.cross(offset, force-(force@normal)*normal)
    cache = getattr(c, "pinch_group_points", {})
    for key in keys:
        if loads[key] > .01:
            cache[key] = points[key]/loads[key]
    c.pinch_group_points = cache
    if len(cache) < 6 or base_force < .5:
        return loads, None
    if getattr(c, "pinch_hand_force_targets", None) is not None:
        # Regrasp candidate: unload the moving pinch while the other holds.
        # This deliberately does not claim the quasi-static wrench certificate.
        targets = {key: 0. for key in keys}
        active = getattr(c, "pinch_active_groups", set(keys))
        for side, base in c.pinch_hand_force_targets.items():
            share = getattr(c, "pinch_hand_load_shares", {}).get(side, .5)
            thumb_force_sign = -getattr(c, "pinch_thumb_faces", {}).get(side, -1)
            delta = c.env.cfg.disk_mass*9.81*normal[2]*support_fraction*share/(2*thumb_force_sign)
            targets[(side, "thumb")] = max(0., base+delta)
            fingers = [f for f in ("index", "middle") if (side, f) in active]
            for finger in fingers:
                targets[(side, finger)] = max(0., base-delta)/len(fingers)
        c.wrench_targets = targets
        return loads, targets
    c.wrench_ticks = getattr(c, "wrench_ticks", 0)+1
    if not hasattr(c, "wrench_targets") or c.wrench_ticks % 10 == 0:
        if any(value != -1 for value in getattr(c, "pinch_thumb_faces", {}).values()):
            raise RuntimeError("mixed-face handoff requires its explicit per-hand force targets")
        weight = c.env.cfg.disk_mass*9.81*support_fraction
        delta = weight*normal[2]/4
        bias = getattr(c, "pinch_preload_bias", {})
        reference = np.array([value for side in ("left", "right")
                              for value in (base_force+bias.get(side, 0.)+delta,
                                            (base_force+bias.get(side, 0.)-delta)/2,
                                            (base_force+bias.get(side, 0.)-delta)/2)])
        locations = np.array([centre+rotation@cache[key] for key in keys])
        allocated = None
        for total in (4*base_force, min(4*base_force+2., 12.), 12.):
            allocated = allocate_normal_forces(locations, centre, normal, weight, reference, total,
                                               tangent_torque=tangent_torque, minimum=.15,
                                               active_mask=None if not hasattr(c, "pinch_active_groups") else
                                                   [key in c.pinch_active_groups for key in keys])
            if allocated is not None:
                break
        if allocated is None:
            raise RuntimeError("measured pinch geometry has no bounded normal-wrench allocation in the local model")
        c.wrench_targets = dict(zip(keys, allocated))
        if c.wrench_ticks % 50 == 0:
            c.events.append(dict(phase="normal_wrench_allocation", control_phase=c.phase,
                time=c.env.physics_steps*c.env.sim_dt,
                measured={"/".join(k): float(v) for k, v in loads.items()},
                targets={"/".join(k): float(v) for k, v in c.wrench_targets.items()}))
    return loads, c.wrench_targets


def regulate_pinch(c, state, searching=False, preload=True, base_force=2.0, responsiveness=1., proportional_gain=.04,
                   support_fraction=1.):
    loads = pinch_loads(state, c.env.cfg)
    for side, thumb_face in getattr(c, "pinch_thumb_faces", {}).items():
        if thumb_face == 1:
            loads[side]["top"], loads[side]["bottom"] = loads[side]["bottom"], loads[side]["top"]
    group_loads, group_targets = pinch_group_targets(c, state, base_force, support_fraction)
    touched = getattr(c, "pinch_touched", {s: {f: False for f in ("top", "bottom")}
                                         for s in loads})
    for side in loads:
        for face in loads[side]:
            touched[side][face] |= loads[side][face] > .10
    c.pinch_touched = touched
    all_ready = all(all(faces.values()) for faces in touched.values())
    q = state["quat"]
    vertical = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[2, 2]
    measured_joints = c.actual_q()
    for side, sign in (("left", -1.), ("right", 1.)):
        frozen = getattr(c, "pinch_frozen_hand_references", {}).get(side)
        if frozen is not None:
            for name, value in frozen.items():
                c.q[c.index[name]] = value
            continue
        ready = all(touched[side].values()) if getattr(c, "pinch_independent_readiness", False) else all_ready
        manual = getattr(c, "pinch_free_hand_targets", {}).get(side)
        if manual is not None or side in getattr(c, "pinch_open_hands", set()):
            # Once the other hand takes the load, retract the distal pads too.
            # Keeping the thumb pad parallel while opening its proximal joint
            # reaches a zero-Jacobian pose and can press it back into the disk.
            profile = manual.items() if manual is not None else (("thumb_1", -sign*.3), ("thumb_2", 0.),
                                   ("index_0", sign*.02), ("index_1", sign*.02),
                                   ("middle_0", sign*.02), ("middle_1", sign*.02))
            for joint, desired in profile:
                index = c.index[f"{side}_hand_{joint}_joint"]
                c.q[index] = np.clip(c.q[index]+CONTROL_DT*np.clip(
                    .8*(desired-measured_joints[index]), -.08, .08), c.lo[index]+.001, c.hi[index]-.001)
            continue
        for joint, desired in (("index_1", sign*.5), ("middle_1", sign*.5)):
            index = c.index[f"{side}_hand_{joint}_joint"]
            c.q[index] = np.clip(c.q[index]+np.clip(.5*(desired-measured_joints[index]), -.02, .02)*CONTROL_DT,
                                 c.lo[index]+.001, c.hi[index]-.001)
        thumb_base = c.index[f"{side}_hand_thumb_1_joint"]
        thumb_tip = c.index[f"{side}_hand_thumb_2_joint"]
        # Keep the distal thumb pad horizontal in the hand frame while its
        # proximal joint raises it. Curling only the tip meets the circular rim
        # first and produces an unwanted horizontal push.
        distal_control = side in getattr(c, "pinch_distal_thumb_control", set())
        if distal_control:
            c.q[thumb_base] = np.clip(c.q[thumb_base]+CONTROL_DT*np.clip(
                .8*(-sign*.25-measured_joints[thumb_base]), -.04, .04),
                c.lo[thumb_base]+.001, c.hi[thumb_base]-.001)
        else:
            angle_error = -sign*math.pi/2-measured_joints[thumb_base]-measured_joints[thumb_tip]
            c.q[thumb_tip] = np.clip(c.q[thumb_tip]+np.clip(.8*angle_error, -.04, .04)*CONTROL_DT,
                                    c.lo[thumb_tip]+.001, c.hi[thumb_tip]-.001)
        for face in ("top", "bottom"):
            target = (base_force+(.3 if face == "bottom" else -.3)*vertical*support_fraction if preload else .5) if ready else .20
            if ready and group_targets is not None and face == "bottom":
                target = group_targets[(side, "thumb")]
            key = (side, face)
            if not hasattr(c, "pinch_errors"):
                c.pinch_errors = {}
            previous = c.pinch_errors.get(key, target-loads[side][face])
            filtered = previous+CONTROL_DT/(.1+CONTROL_DT)*(target-loads[side][face]-previous)
            c.pinch_errors[key] = filtered
            velocity = ((.025 if face == "bottom" else .02) if searching and not touched[side][face] else
                        responsiveness*np.clip(.008*(target-loads[side][face]), -.015, .015))
            velocity += proportional_gain*(filtered-previous)/CONTROL_DT
            velocity = np.clip(velocity, -.15, .15)
            overload = max(0., state["robot_contact_force_n"]-15.)
            if overload:
                velocity = min(velocity, -responsiveness*min(.015, .008*overload))
            if face == "top":
                for finger in ("index", "middle"):
                    finger_velocity = velocity
                    if ready and group_targets is not None:
                        error = group_targets[(side, finger)]-group_loads[(side, finger)]
                        key = (side, finger)
                        previous = c.pinch_errors.get(key, error)
                        filtered = previous+CONTROL_DT/(.1+CONTROL_DT)*(error-previous)
                        c.pinch_errors[key] = filtered
                        finger_velocity = responsiveness*np.clip(.008*error, -.015, .015)
                        finger_velocity += proportional_gain*(filtered-previous)/CONTROL_DT
                        finger_velocity = np.clip(finger_velocity, -.15, .15)
                        if overload:
                            finger_velocity = min(finger_velocity, -responsiveness*min(.015, .008*overload))
                    index = c.index[f"{side}_hand_{finger}_0_joint"]
                    c.q[index] = np.clip(c.q[index]+sign*finger_velocity*CONTROL_DT,
                                         c.lo[index]+.01, c.hi[index]-.01)
            else:
                index = thumb_tip if distal_control else thumb_base
                c.q[index] = np.clip(c.q[index]-sign*velocity*CONTROL_DT,
                                     c.lo[index]+.01, c.hi[index]-.01)
    return loads


def unload_thumb(c, side, direction):
    """Separate a rim pusher with a continuous loaded-arm reference."""
    cfg = c.env.cfg
    # Unload the rim normal before lifting the pusher; lifting a still-loaded
    # thumb can drag the disk upward when static friction holds correctly.
    # Preserve the existing arm reference at the transition. Replacing it by
    # measured arm angles abruptly discards the loaded PD deflection.
    reference = c.actual_q()
    reference[c.ik.upper] = c.q[c.ik.upper]
    c.ik._set(c.env.base_position, (1, 0, 0, 0), reference)
    tip = c.ik.hand_point(side, "thumb").copy()
    rotation = c.ik.d.xmat[c.ik.wrist[side]].reshape(3, 3).copy()
    c.event("unload_rim_pusher", hand=side)
    for i in range(250):
        c.reach({side: ("thumb", tip+[direction*.035*smooth((i+1)/250), 0., 0.], rotation)}, feedback=0.)
        c.step()
    if c.object_state("disk")["hand_force_magnitudes_n"][side] > cfg.contact_min_n:
        raise RuntimeError("rim pusher remains loaded after the withdrawal budget")
    c.hold(.5)


def pinch(c):
    """Candidate: each hand pinches both faces at the exposed edge."""
    cfg = c.env.cfg
    unload_thumb(c, "left", 1.)
    tip, rotation = c.hand_pose("left", "thumb")
    c.move({"left": ("thumb", tip+[0., 0., .12], rotation)}, seconds=6., phase="clear_rim_pusher")
    c.configure_grasp_ik()
    c.event("retract_above_and_beside_disk")
    c.move_hands({side: ("palm", np.array([.25, sign*.30, cfg.table_height+.19]),
                         c.hand_pose(side)[1])
                  for side, sign in (("left", 1.), ("right", -1.))}, seconds=10.)
    c.ik.set_limit("left_wrist_roll_joint", .7, 1.95)
    c.ik.set_limit("right_wrist_roll_joint", -1.95, -.7)
    fingers = c.q.copy()
    for side, sign in (("left", -1.), ("right", 1.)):
        for finger in ("index", "middle"):
            fingers[c.index[f"{side}_hand_{finger}_0_joint"]] = sign*.05
            fingers[c.index[f"{side}_hand_{finger}_1_joint"]] = sign*.50
        # Abduct the thumb toward the disk centre, so the lower contact can
        # support its weight without a large cantilever moment at the rim.
        fingers[c.index[f"{side}_hand_thumb_0_joint"]] = .6 if side == "left" else .25
        fingers[c.index[f"{side}_hand_thumb_1_joint"]] = 0.
        fingers[c.index[f"{side}_hand_thumb_2_joint"]] = -sign*math.pi/2
    c.move_joints(fingers, seconds=6.)
    disk = np.asarray(c.object_state("disk")["pos"])
    rotations = {side: Rotation.from_euler("z", sign*math.pi/2).as_matrix()
                     @ Rotation.from_euler("x", -sign*math.pi/2).as_matrix()
                 for side, sign in (("left", -1.), ("right", 1.))}
    # Stagger the two finger pairs in X so their tips can interleave. This
    # brings both thumbs under the faces instead of onto the circular rim.
    # A slightly lower palm keeps the proximal thumb away from its straight
    # configuration, where normal displacement has a near-zero Jacobian.
    poses = {side: np.array([cfg.edge_x-offset, disk[1]+sign*.09, cfg.rest_z+.044])
             for side, sign, offset in (("left", 1., .055), ("right", -1., .026))}
    tasks = {s: ("palm", poses[s], rotations[s]) for s in poses}
    # Insert from outside the front edge. A lateral approach exceeds the arm
    # workspace and an approach from above would put the thumb on the top face.
    approach = {s: ("palm", poses[s]+[-.10, sign*.06, 0.], rotations[s])
                for s, sign in (("left", 1.), ("right", -1.))}
    hint = c.q.copy()
    for name, value in (("waist_yaw", 0.), ("waist_roll", 0.), ("waist_pitch", .3)):
        hint[c.index[name+"_joint"]] = value
    for side, sign in (("left", 1.), ("right", -1.)):
        for joint, value in (("shoulder_pitch", -.14), ("shoulder_roll", sign*.82),
                             ("shoulder_yaw", sign*.42), ("elbow", .15),
                             ("wrist_roll", sign*1.19), ("wrist_pitch", -1.45), ("wrist_yaw", sign*.32)):
            hint[c.index[f"{side}_{joint}_joint"]] = value
    c.select_approach_branch(approach, trials=48, seed_hints=(hint,))
    c.event("calibrate_free_finger_preshape")
    finger_indices = [index for name, index in c.index.items() if "hand_" in name]
    settled = 0.
    for _ in range(500):
        measured = c.actual_q()
        error = fingers[finger_indices]-measured[finger_indices]
        c.q[finger_indices] = np.clip(c.q[finger_indices]+np.clip(.8*error, -.04, .04)*CONTROL_DT,
                                      c.lo[finger_indices]+.001, c.hi[finger_indices]-.001)
        c.reach(approach, feedback=.25)
        c.step()
        settled = settled+CONTROL_DT if np.max(np.abs(error)) < .008 else 0.
        if settled >= .25:
            break
    else:
        raise RuntimeError("free-finger preshape did not settle within its calibration budget")
    narrow = {s: ("palm", poses[s]+[-.10, 0., 0.], rotations[s]) for s in poses}
    c.move_hands(narrow, seconds=6.)
    c.move_hands(tasks, seconds=12.)
    c.event("close_two_independent_edge_pinches")
    alignment_time = 0.
    preload_dwell = 0.
    tracked_drift = np.zeros(3)
    for _ in range(2500):
        state = c.object_state("disk")
        loads = regulate_pinch(c, state, searching=True)
        if all(all(faces.values()) for faces in c.pinch_touched.values()):
            alignment_time += CONTROL_DT
        drift = np.asarray(state["pos"])-disk
        drift[2] = 0.
        if abs(drift[0]) > .006 or abs(drift[1]) > .02:
            raise RuntimeError("disk drift exhausted the exposed-thumb clearance budget")
        tracked_drift += np.clip(drift-tracked_drift, -.002*CONTROL_DT, .002*CONTROL_DT)
        c.reach({s: ("palm", poses[s]+tracked_drift, rotations[s]) for s in poses}, feedback=.5)
        c.step()
        loaded = (c.env.status["stage"] >= 2 and hasattr(c, "wrench_targets")
                  and state["robot_contact_force_n"] < 13.
                  and min(v for faces in loads.values() for v in faces.values()) > .8
                  and sum(f[2] for f in state["hand_forces_n"].values()) > .4*cfg.disk_mass*9.81)
        preload_dwell = preload_dwell+CONTROL_DT if loaded else 0.
        if preload_dwell >= .5:
            return
    raise RuntimeError("two load-bearing edge pinches were not established within the local budget")


def pinch_lift(c):
    c.configure_grasp_ik()
    c.ik.set_limit("left_wrist_roll_joint", -1.95, 1.95)
    c.ik.set_limit("right_wrist_roll_joint", -1.95, 1.95)
    centre = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    goal = np.array([c.env.cfg.edge_x-.03, centre[1], c.env.cfg.table_height+c.env.cfg.disk_radius+.04])
    c.event("lift_with_two_edge_pinches")
    for i in range(850):
        translation = smooth(min((i+1)/750, 1.))*(goal-centre)
        state = c.object_state("disk")
        regulate_pinch(c, state, base_force=2.+.5*smooth(min((i+1)/400, 1.)))
        correction = c.attitude_correction(state, np.array([0., 0., 1.]))
        c.reach({s: ("palm", centre+translation+correction@(hands[s][0]-centre),
                     correction@hands[s][1]) for s in hands}, feedback=0.)
        c.step()
        if c.env.status["stage"] >= 3 and c.env.status["conditions"].get("still"):
            return
    c.require_stage(3)


def pinch_turn(c):
    c.configure_grasp_ik()
    c.ik.set_limit("left_wrist_roll_joint", -1.95, 1.95)
    c.ik.set_limit("right_wrist_roll_joint", -1.95, 1.95)
    # Keep the pitch joint away from the housing contact near +/- pi/2.
    c.ik.set_limit("right_wrist_pitch_joint", -1.575, 1.575)
    from .ik import WristClearanceIK
    previous_ik = c.ik
    c.ik = WristClearanceIK()
    c.ik.upper = previous_ik.upper.copy()
    c.ik.lo, c.ik.hi = previous_ik.lo.copy(), previous_ik.hi.copy()
    centre = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    q = c.object_state("disk")["quat"]
    normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    vertical_correction = 0.
    tangent_offsets = {side: np.zeros(3) for side in hands}
    pressure_fallback = False
    c.event("turn_with_two_edge_pinches")
    try:
        for i in range(3250):
            turn = Rotation.from_euler("y", math.pi*smooth(min((i+1)/3000, 1.))).as_matrix()
            state = c.object_state("disk")
            disk_q = state["quat"]
            disk_normal = Rotation.from_quat([disk_q[1], disk_q[2], disk_q[3], disk_q[0]]).as_matrix()[:, 2]
            try:
                regulate_pinch(c, state, base_force=2.5, responsiveness=3.)
            except RuntimeError as error:
                # The normal-only wrench model can become infeasible just
                # before horizontal inversion although measured pinches still
                # carry the disk. Use the same bounded pressure feedback as
                # the settling skill, within this narrow measured condition.
                if (str(error) != "measured pinch geometry has no bounded normal-wrench allocation in the local model"
                        or i < 2400 or disk_normal[2] > -math.cos(math.radians(15.))
                        or not c.env.status["conditions"]["bimanual_clamp"]):
                    raise
                c.pinch_hand_force_targets = {side: 2.5 for side in hands}
                c.pinch_hand_load_shares = {side: .5 for side in hands}
                c.pinch_errors = {}
                pressure_fallback = True
                c.event("use_measured_pressure_feedback_near_inversion")
                regulate_pinch(c, state, base_force=2.5, responsiveness=3.)
            for side in hands:
                residual = np.asarray(state["hand_forces_n"][side])-[0., 0., c.env.cfg.disk_mass*9.81/2]
                tangent = residual-disk_normal*np.dot(residual, disk_normal)
                tangent_offsets[side] = np.clip(tangent_offsets[side]-CONTROL_DT*np.clip(.001*tangent, -.002, .002), -.012, .012)
            vertical_correction = float(np.clip(vertical_correction+CONTROL_DT*np.clip(
                .5*(centre[2]+.01-state["pos"][2]), -.001, .003), 0., .06))
            correction = c.attitude_correction(state, turn@normal)
            c.reach({s: ("palm", centre+[0., 0., vertical_correction]+tangent_offsets[s]+correction@turn@(hands[s][0]-centre),
                         correction@turn@hands[s][1]) for s in hands}, feedback=0., seed_reference=True)
            c.step()
            if c.env.status["stage"] >= 4:
                return
        c.require_stage(4)
    finally:
        c.ik = previous_ik
        if pressure_fallback:
            del c.pinch_hand_force_targets
            del c.pinch_hand_load_shares


def pinch_and_lift(c):
    """Bounded development probe; only evaluator completion can score success."""
    pinch(c)
    pinch_lift(c)


def pinch_through_turn(c):
    pinch_and_lift(c)
    pinch_turn(c)


def slide_through_turn(c):
    """Fresh-reset representative validation of the first four stages only."""
    slide(c)
    pinch_through_turn(c)
    c.event("settle_after_bimanual_inversion")
    hold_pinch(c, 10.)


def hold_pinch(c, seconds):
    """Keep contact-force feedback active while the inverted disk settles."""
    state = c.object_state("disk")
    centre = np.asarray(state["pos"])
    hands = c.nominal_hands()
    quat = state["quat"]
    normal = Rotation.from_quat([quat[1], quat[2], quat[3], quat[0]]).as_matrix()[:, 2]
    offsets = {side: np.zeros(3) for side in hands}
    c.attitude_rotvec = np.zeros(3)
    for i in range(round(seconds/CONTROL_DT)):
        state = c.object_state("disk")
        c.pinch_hand_force_targets = {side: 2.5-.5*smooth(min((i+1)/200, 1.)) for side in hands}
        c.pinch_hand_load_shares = {side: .5 for side in hands}
        regulate_pinch(c, state, base_force=2.5-.5*smooth(min((i+1)/200, 1.)), responsiveness=3.)
        for side in hands:
            residual = np.asarray(state["hand_forces_n"][side])-[0., 0., c.env.cfg.disk_mass*9.81/2]
            tangent = residual-normal*np.dot(residual, normal)
            offsets[side] = np.clip(offsets[side]-CONTROL_DT*np.clip(.001*tangent, -.002, .002), -.012, .012)
        correction = c.attitude_correction(state, normal)
        c.reach({side: ("palm", centre+offsets[side]+correction@(hands[side][0]-centre),
                       correction@hands[side][1]) for side in hands}, seed_reference=True)
        c.step()
    del c.pinch_hand_force_targets
    del c.pinch_hand_load_shares


def pinch_complete(c):
    from .placement import place as place_pinched_disk
    pinch_through_turn(c)
    place_pinched_disk(c)


def pinch_place(c):
    from .placement import place as place_pinched_disk
    place_pinched_disk(c)


def pinch_single_hold_probe(c):
    from .placement import single_hold
    single_hold(c)


def pinch_left_regrasp_probe(c):
    from .placement import reposition_open_hand
    reposition_open_hand(c, "left")


def pinch_right_transfer_probe(c):
    from .placement import single_hold
    single_hold(c, "right")


def pinch_right_regrasp_probe(c):
    from .placement import reposition_open_hand
    reposition_open_hand(c, "right")


def pinch_pad_regrip_probe(c):
    from .placement import retune_thumb_pad
    retune_thumb_pad(c)


def pinch_edge_roll_probe(c):
    from .placement import edge_roll_support
    edge_roll_support(c)


def pinch_table_release_probe(c):
    from .placement import release_supported_hand
    release_supported_hand(c)


def pinch_rim_regrasp_probe(c):
    from .placement import rim_regrasp
    rim_regrasp(c)


def pinch_air_rim_probe(c):
    from .placement import rim_regrasp
    rim_regrasp(c, table_supported=False)


def pinch_roll_withdraw_probe(c):
    from .placement import roll_and_withdraw
    roll_and_withdraw(c)


def pinch_bridge_probe(c):
    from .placement import lower_outside_bridge
    lower_outside_bridge(c)


def pinch_bridge_push_probe(c):
    from .placement import push_across_bridge
    push_across_bridge(c)


def pinch_bridge_transfer_probe(c):
    from .placement import push_across_bridge
    push_across_bridge(c, stop_after_transfer=True)


def pinch_bridge_resume_probe(c):
    from .placement import push_across_bridge
    push_across_bridge(c, resume=True)


def pinch_hold_probe(c):
    """Development-only static posture check, never a full-task witness."""
    c.event("hold_loaded_finger_and_arm_targets")
    c.hold(10.)


def pinch_support_probe(c):
    """Development-only contact geometry diagnostic at the edge."""
    for i in range(100):
        if i % 5 == 0:
            samples = c.env.objects["disk"].get_contacts()
            robot_samples = c.env.robot.get_contacts()
            c.event("inspect_supported_rim_contacts",
                    disk_contacts={k: v.detach().cpu().numpy().tolist() for k, v in samples.items()},
                    robot_contacts={k: v.detach().cpu().numpy().tolist() for k, v in robot_samples.items()})
        c.step()


def pinch_contact_probe(c):
    samples = c.env.objects["disk"].get_contacts()
    c.event("inspect_contact_link_identity",
            contacts={key: value.detach().cpu().numpy().tolist() for key, value in samples.items()},
            robot_links={str(link.idx): link.name for link in c.env.robot.links})


def pinch_geometry_probe(c):
    """Read-only development check of collision meshes against visual scale."""
    entity = c.env.objects["disk"]
    c.event("collision_geometry_diagnostic", disk_aabb=entity.get_AABB().cpu().numpy().tolist(),
        geometries=[dict(link=g.link.name, index=g.idx, kind=str(g.type), convex=g.is_convex,
                         data=g.data.tolist(), minimum=np.min(g.mesh.verts, axis=0).tolist(),
                         maximum=np.max(g.mesh.verts, axis=0).tolist())
                    for g in [*entity.geoms, *[g for g in c.env.robot.geoms if "thumb" in g.link.name]]])


def pinch_thumb_rebalance(c):
    """Slide loaded thumb pads inward using bounded joint feedback."""
    c.event("rebalance_loaded_thumb_contacts")
    indices = [c.index[f"{side}_hand_thumb_0_joint"] for side in ("left", "right")]
    starts = c.actual_q()[indices]
    for i in range(500):
        state = c.object_state("disk")
        regulate_pinch(c, state, base_force=2.5)
        desired = starts+.45*smooth(min((i+1)/200, 1.))
        c.q[indices] += np.clip(.8*(desired-c.actual_q()[indices]), -.15, .15)*CONTROL_DT
        c.q[indices] = np.clip(c.q[indices], c.lo[indices]+.001, c.hi[indices]-.001)
        c.step()


def turn_over(c):
    c.configure_grasp_ik()
    c.ik.set_limit("waist_roll_joint", -.5, .5)
    c.ik.set_limit("waist_pitch_joint", -.3, .5)
    c.ik.set_limit("waist_yaw_joint", -1., 1.)
    q = c.object_state("disk")["quat"]
    initial_normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    c.attitude_rotvec = np.zeros(3)
    lifted = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    offsets = {side: hands[side][0]-lifted for side in hands}
    rotations = {side: hands[side][1] for side in hands}
    c.event("slow_bimanual_half_turn")
    # Minimum-jerk half-turn: peak angular reference speed is 0.37 rad/s.
    squeeze = {"left": 0., "right": 0.}
    for i in range(950):
        angle = -math.pi*smooth(min((i+1)/800, 1.))
        turn = Rotation.from_euler("x", angle).as_matrix()
        state = c.object_state("disk")
        correction = c.attitude_correction(state, turn@initial_normal)
        for side in squeeze:
            target = 5.1+(-1. if side == "left" else 1.)*.6*math.cos(angle)
            squeeze[side] += np.clip((target-state["hand_force_magnitudes_n"][side])*.0005,
                                     -.001, .001)*CONTROL_DT
        c.reach({s: ("palm", lifted+correction@turn@(offsets[s]+[0., 0.,
                    (-1. if s == "left" else 1.)*squeeze[s]]), correction@turn@rotations[s]) for s in offsets},
                feedback=.1)
        c.step()
        if c.env.status["stage"] >= 4:
            break
    c.require_stage(4)


def place(c):
    cfg = c.env.cfg
    disk = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    offsets = {side: hands[side][0]-disk for side in hands}
    rotations = {side: hands[side][1] for side in hands}
    # The underhand remains outside the edge while the supported disk touches
    # down; it must withdraw before the inverted disk slides fully onto the table.
    edge_place = np.array([cfg.edge_center[0], cfg.start_xy[1], cfg.rest_z-.001])
    c.event("lower_inverted_disk_at_edge")
    squeeze = {"left": 0., "right": 0.}
    for i in range(600):
        centre = disk+smooth((i+1)/600)*(edge_place-disk)
        state = c.object_state("disk")
        for side in squeeze:
            target = 5.7 if side == "left" else 4.5
            squeeze[side] += np.clip((target-state["hand_force_magnitudes_n"][side])*.0005,
                                     -.001, .001)*CONTROL_DT
        c.reach({s: ("palm", centre+offsets[s]+[0., 0.,
                    (1. if s == "left" else -1.)*squeeze[s]], rotations[s]) for s in offsets}, feedback=.1)
        c.step()
    c.hold(.3)
    if c.object_state("disk")["support_forces"].get("table", 0.) < cfg.disk_mass*9.81*.7:
        raise RuntimeError("table has not taken the disk load; refusing underhand withdrawal")
    c.event("withdraw_lower_hand_outside_edge")
    bottom, bottom_rot = c.hand_pose("left")
    upper, upper_rot = c.hand_pose("right")
    bottom[2] -= .03
    c.move_hands({"left": ("palm", bottom.copy(), bottom_rot),
                  "right": ("palm", upper, upper_rot)}, seconds=3.)
    bottom[0] -= .10
    c.move_hands({"left": ("palm", bottom, bottom_rot),
                  "right": ("palm", upper, upper_rot)}, seconds=6.)
    c.move({"right": ("palm", upper+[0., 0., .12], upper_rot)},
           seconds=6., phase="clear_upper_hand_for_rim_push")
    return_disk_to_goal(c)


def return_disk_to_goal(c):
    cfg = c.env.cfg
    c.hand_preset("right", "open", seconds=2.)
    face = Rotation.from_euler("x", -math.pi/2).as_matrix()
    start = np.asarray(c.object_state("disk")["pos"])
    tip = start+[-cfg.disk_radius-.025, 0., .12]
    c.move({"right": ("thumb", tip.copy(), face)}, seconds=6., phase="approach_near_rim")
    tip[2] = cfg.table_height+.002
    c.move({"right": ("thumb", tip.copy(), face)}, seconds=6., phase="lower_outside_near_rim")
    c.event("gentle_return_rim_contact")
    for _ in range(1000):
        if c.object_state("disk")["hand_force_magnitudes_n"]["right"] >= .1:
            break
        tip[0] += .002*CONTROL_DT
        c.reach({"right": ("thumb", tip.copy(), face)}, feedback=1.5)
        c.step()
    else:
        raise RuntimeError("near-rim contact was not established for return slide")
    c.event("slide_inverted_disk_onto_table")
    start = np.asarray(c.object_state("disk")["pos"])
    for i in range(2500):
        state = c.object_state("disk")
        actual = np.asarray(state["pos"])
        desired_x = start[0]+smooth((i+1)/1800)*(cfg.goal_xy[0]-start[0])
        tip[0] += np.clip(desired_x-actual[0], -.010*CONTROL_DT, .010*CONTROL_DT)
        tip[0] = min(tip[0], actual[0]-cfg.disk_radius+.002)
        lateral = actual[1]+2.*(actual[1]-cfg.goal_xy[1])
        tip[1] += np.clip(lateral-tip[1], -.004*CONTROL_DT, .004*CONTROL_DT)
        c.reach({"right": ("thumb", tip.copy(), face)}, feedback=1.5)
        c.step()
        if i >= 1800 and c.env.status["conditions"].get("placed") and c.env.status["conditions"].get("in_goal"):
            break
    if not c.env.status["conditions"].get("placed") or not c.env.status["conditions"].get("in_goal"):
        raise RuntimeError("inverted disk did not reach the supported goal")
    unload_thumb(c, "right", -1.)
    tip, face = c.hand_pose("right", "thumb")
    c.move({"right": ("thumb", tip+[0., 0., .12], face)},
           seconds=6., phase="release_gently")
    c.hold(cfg.final_hold_seconds+.5)
    if not c.env.status["success"]:
        raise RuntimeError("released stable completion not established")


SKILLS = {"gentle_slide_to_edge": slide, "two_independent_edge_pinches": pinch,
          "bimanual_lift_clear": pinch_lift, "bimanual_half_turn": pinch_turn,
          "edge_setdown_withdraw_slide_release": pinch_place}


def run(c):
    """Choose the next skill from measured progress; plan joint targets online.

    Only a declared representative execution invokes this function. The offline
    oracle emits key states and screening results without running any skill.
    Every skill constructs its local targets from the current measured state;
    reach()/step() solves and executes one control step at a time. Failed local
    execution remains a failed attempt, not proof that the instance is impossible.
    """
    from .oracle import build_plan
    plan = build_plan(c.env.cfg)
    while not c.env.status["terminated"]:
        stage = c.env.status.get("stage", 0)
        step = plan["steps"][stage]
        c.event("select_skill", skill=step["skill"], key_state=step["key_state"],
                horizon_control_steps=1)
        SKILLS[step["skill"]](c)
        if c.env.status.get("stage", 0) <= stage and not c.env.status["terminated"]:
            raise RuntimeError("skill did not establish its measured postcondition")
    if not c.env.status["success"]:
        raise RuntimeError("representative execution failed: "+c.env.status["reason"])
