"""Measured support transfer and placement, with explicit development probes."""
import math

import numpy as np
from scipy.spatial.transform import Rotation

from humanoid.g1_tabletop.genesis_env import CONTROL_DT


def lower_outside_bridge(c):
    """Development probe: lower the holding hand entirely outside the table edge."""
    from .controller import smooth
    from .ik import WristClearanceIK
    c.require_stage(4)
    state = c.object_state("disk")
    if state["hand_force_magnitudes_n"]["left"] > c.env.cfg.contact_min_n:
        raise RuntimeError("bridge transfer requires the left hand to be released")
    previous_ik = c.ik
    c.ik = WristClearanceIK(all_robot_pairs=True)
    centre = np.asarray(state["pos"])
    hands = c.nominal_hands()
    quat = state["quat"]
    normal = Rotation.from_quat([quat[1], quat[2], quat[3], quat[0]]).as_matrix()[:, 2]
    axis = np.cross(normal, [0., 0., -1.])
    angle = math.acos(np.clip(-normal[2], -1., 1.))
    level_vector = axis/max(np.linalg.norm(axis), 1e-12)*angle
    goal = np.array([c.env.cfg.edge_x-c.env.cfg.disk_radius-.02, centre[1], c.env.cfg.rest_z+.003])
    c.attitude_rotvec = np.zeros(3)
    try:
        for phase, seconds in (("clear_bridge_pusher", 16.), ("carry_inverted_disk_outside_edge", 20.),
                               ("lower_outside_holding_hand", 25.)):
            c.event(phase)
            bad = 0.
            for i in range(round(seconds/CONTROL_DT)):
                amount = smooth((i+1)/round(seconds/CONTROL_DT))
                out = 0. if phase == "clear_bridge_pusher" else amount if phase == "carry_inverted_disk_outside_edge" else 1.
                down = amount if phase == "lower_outside_holding_hand" else 0.
                level = Rotation.from_rotvec(level_vector*out).as_matrix()
                state = c.object_state("disk")
                correction = c.attitude_correction(state, level@normal)
                translation = np.array([(goal[0]-centre[0])*out, 0., (goal[2]-centre[2])*down])
                left = hands["left"][0]+[0., .15*(amount if phase == "clear_bridge_pusher" else 1.), .1*out]
                errors = c.reach({"right": ("palm", centre+translation+correction@level@(hands["right"][0]-centre),
                                             correction@level@hands["right"][1]),
                                  "left": ("palm", left, hands["left"][1] if phase == "clear_bridge_pusher" else None)},
                                 seed_reference=True)
                c.step()
                bad = bad+CONTROL_DT if max(errors.values()) > .015 else 0.
                if bad >= .25:
                    raise RuntimeError("outside bridge motion exceeded the local IK residual budget")
        c.event("align_supported_disk_with_table_height")
        offset = np.zeros(3)
        stable = 0.
        for _ in range(1500):
            state = c.object_state("disk")
            error = goal-np.asarray(state["pos"])
            offset += CONTROL_DT*np.clip(.5*error, -.002, .002)
            correction = c.attitude_correction(state, np.array([0., 0., -1.]))
            c.reach({"right": ("palm", goal+offset+correction@level@(hands["right"][0]-centre),
                                         correction@level@hands["right"][1]),
                      "left": ("palm", hands["left"][0]+[0., .15, .1], None)}, seed_reference=True)
            c.step()
            good = np.linalg.norm(error) < .003 and c.env.status["conditions"]["inverted"] and c.env.status["conditions"]["still"]
            stable = stable+CONTROL_DT if good else 0.
            if stable >= .5:
                break
        else:
            raise RuntimeError("outside bridge pose was not established")
        c.pinch_bridge_goal = goal.copy()
    finally:
        c.ik = previous_ik


def edge_roll_support(c):
    """Development probe: establish a table-supported tilted rim after inversion."""
    from .controller import regulate_pinch, smooth
    from .ik import WristClearanceIK
    c.require_stage(4)
    previous_ik = c.ik
    c.ik = WristClearanceIK()
    c.ik.upper = previous_ik.upper.copy()
    c.ik.lo, c.ik.hi = previous_ik.lo.copy(), previous_ik.hi.copy()
    state = c.object_state("disk")
    centre = np.asarray(state["pos"])
    hands = c.nominal_hands()
    quat = state["quat"]
    normal = Rotation.from_quat([quat[1], quat[2], quat[3], quat[0]]).as_matrix()[:, 2]
    c.attitude_rotvec = np.zeros(3)
    offsets = {side: np.zeros(3) for side in hands}
    translation = np.zeros(3)
    turn = np.eye(3)
    def tick():
        state = c.object_state("disk")
        regulate_pinch(c, state, base_force=2., responsiveness=3.)
        q = state["quat"]
        current_normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
        for side in hands:
            residual = np.asarray(state["hand_forces_n"][side])-[0., 0., c.env.cfg.disk_mass*9.81/2]
            tangent = residual-current_normal*np.dot(residual, current_normal)
            offsets[side] = np.clip(offsets[side]-CONTROL_DT*np.clip(.001*tangent, -.002, .002), -.012, .012)
        correction = c.attitude_correction(state, turn@normal)
        c.reach({side: ("palm", centre+translation+offsets[side]+correction@turn@(hands[side][0]-centre),
                       correction@turn@hands[side][1]) for side in hands}, seed_reference=True)
        c.step()
    try:
        c.event("tilt_inverted_disk_over_table")
        for i in range(1500):
            amount = smooth((i+1)/1500)
            turn = Rotation.from_euler("y", -math.pi/3*amount).as_matrix()
            translation[0] = .10*amount
            tick()
        c.event("lower_tilted_rim_to_table")
        stable = 0.
        for _ in range(2000):
            state = c.object_state("disk")
            supported = state["support_force_n"] >= .7*c.env.cfg.disk_mass*9.81
            translation[2] -= CONTROL_DT*(.0002 if supported else .002)
            tick()
            stable = stable+CONTROL_DT if supported else 0.
            if stable >= .5:
                return
        raise RuntimeError("tilted disk rim did not establish table support within the local budget")
    finally:
        c.ik = previous_ik


def push_across_bridge(c, *, resume=False, stop_after_transfer=False):
    """Development probe: slide from the outside holding hand onto the table."""
    from .controller import smooth
    from .ik import WristClearanceIK
    c.require_stage(4)
    previous_ik = c.ik
    c.ik = WristClearanceIK(all_robot_pairs=True)
    hands = c.nominal_hands()
    right_point, right_rotation = hands["right"]
    right_shift = np.zeros(3)
    right_fingers = {index: float(c.q[index]) for name, index in c.index.items() if name.startswith("right_hand_")}
    left_indices = [index for name, index in c.index.items() if name.startswith("left_hand_")]
    c.ik._set(c.env.base_position, (1, 0, 0, 0), c.q)
    tip = c.ik.hand_point("left", "thumb").copy()
    rotation = hands["left"][1].copy()
    target_rotation = (Rotation.from_euler("z", -math.pi/2)*Rotation.from_euler("x", math.pi/2)).as_matrix()
    release_thumb = resume
    withdrawing = False
    c.attitude_rotvec = np.zeros(3)
    thumb_target = None
    bridge_height = c.env.cfg.rest_z+.004
    initial_thumb_angle = sum(c.actual_q()[c.index[f"right_hand_{joint}_joint"]] for joint in ("thumb_1", "thumb_2"))
    def tick():
        state = c.object_state("disk")
        if state["pos"][0] < c.env.cfg.edge_x-c.env.cfg.disk_radius+.01 and state["support_force_n"] < .1:
            q = state["quat"]
            normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
            radial = np.array([1., 0., 0.])-normal[0]*normal
            radial /= np.linalg.norm(radial)
            far_bottom = state["pos"][2]+c.env.cfg.disk_radius*radial[2]-c.env.cfg.disk_height/2*abs(normal[2])
            height_error = max(bridge_height-state["pos"][2], c.env.cfg.table_height+.003-far_bottom)
            right_shift[2] = np.clip(right_shift[2]+CONTROL_DT*np.clip(.5*height_error, -.001, .001), -.015, .035)
        measured = c.actual_q()
        for index in left_indices:
            c.q[index] = np.clip(c.q[index]+CONTROL_DT*np.clip(-.8*measured[index], -.04, .04),
                                c.lo[index]+.001, c.hi[index]-.001)
        for index, value in right_fingers.items():
            c.q[index] = value
        if thumb_target is not None and not release_thumb:
            state = c.object_state("disk")
            q = state["quat"]
            normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
            pressure = sum(max(0., float(np.dot(sample["force_n"], normal)))
                           for sample in state["hand_contacts"]["right"]
                           if "right_hand_thumb_" in sample.get("robot_link", ""))
            base = c.index["right_hand_thumb_1_joint"]
            distal = c.index["right_hand_thumb_2_joint"]
            right_fingers[base] = np.clip(right_fingers[base]-CONTROL_DT*np.clip(.024*(thumb_target-pressure), -.04, .04),
                                         c.lo[base]+.001, c.hi[base]-.001)
            right_fingers[distal] = np.clip(right_fingers[distal]+CONTROL_DT*np.clip(
                .8*(initial_thumb_angle-measured[base]-measured[distal]), -.04, .04), c.lo[distal]+.001, c.hi[distal]-.001)
            c.q[base], c.q[distal] = right_fingers[base], right_fingers[distal]
        if release_thumb:
            for joint, desired in (("thumb_1", .35), ("thumb_2", 0.)):
                index = c.index[f"right_hand_{joint}_joint"]
                right_fingers[index] = np.clip(right_fingers[index]+CONTROL_DT*np.clip(
                    .8*(desired-measured[index]), -.08, .08), c.lo[index]+.001, c.hi[index]-.001)
                c.q[index] = right_fingers[index]
        state = c.object_state("disk")
        correction = np.eye(3) if withdrawing else c.attitude_correction(state, np.array([0., 0., -1.]))
        centre = np.asarray(state["pos"])
        left_target = tip.copy()
        if withdrawing:
            measured_tip, _ = c.hand_pose("left", "thumb")
            left_target[2] += np.clip(1.5*(tip[2]-measured_tip[2]), -.004, .004)
        errors = c.reach({"right": ("palm", centre+correction@(right_point+right_shift-centre), correction@right_rotation),
                          "left": ("thumb", left_target, rotation)}, seed_reference=True)
        c.step()
        return errors
    def move(goal, seconds, phase, goal_rotation=None):
        nonlocal tip, rotation
        start = tip.copy()
        start_rotation = rotation.copy()
        delta = Rotation.from_matrix(goal_rotation@start_rotation.T).as_rotvec() if goal_rotation is not None else np.zeros(3)
        c.event(phase)
        bad = 0.
        for i in range(round(seconds/CONTROL_DT)):
            amount = smooth((i+1)/round(seconds/CONTROL_DT))
            tip = start+amount*(goal-start)
            rotation = Rotation.from_rotvec(amount*delta).as_matrix()@start_rotation
            errors = tick()
            bad = bad+CONTROL_DT if max(errors.values()) > .015 else 0.
            if bad >= .5:
                raise RuntimeError("bridge pusher approach exceeded its local IK residual budget")
    try:
        if not resume:
            state = c.object_state("disk")
            near = np.asarray(state["pos"])+[-c.env.cfg.disk_radius-.025, 0., .12]
            move(near, 18., "approach_near_rim_above_outside_bridge", target_rotation)
            near[2] = c.object_state("disk")["pos"][2]-.004
            move(near, 12., "lower_bridge_pusher_outside_near_rim")
            c.event("establish_bridge_push_contact")
            for _ in range(1500):
                state = c.object_state("disk")
                if state["hand_force_magnitudes_n"]["left"] >= .1:
                    break
                tip[0] += .002*CONTROL_DT
                tick()
            else:
                raise RuntimeError("bridge pusher did not establish contact")
        start = np.asarray(c.object_state("disk")["pos"])
        withdraw = 0.
        transferred = 0.
        c.event("slide_disk_from_holding_hand_onto_table")
        for i in range(6000):
            state = c.object_state("disk")
            actual = np.asarray(state["pos"])
            quat = state["quat"]
            normal = Rotation.from_quat([quat[1], quat[2], quat[3], quat[0]]).as_matrix()[:, 2]
            radial = np.array([1., 0., 0.])-normal[0]*normal
            radial /= np.linalg.norm(radial)
            near_rim = actual-c.env.cfg.disk_radius*radial
            desired = start[0]+smooth(min((i+1)/4000, 1.))*(c.env.cfg.goal_xy[0]-start[0])
            previous_tip = tip.copy()
            step = np.clip(desired-actual[0], -.004*CONTROL_DT, .006*CONTROL_DT)
            if state["hand_force_magnitudes_n"]["left"] > 5. or state["robot_contact_force_n"] > 12.:
                step = min(step, -.002*CONTROL_DT)
            tip[0] = min(tip[0]+step, near_rim[0]+.015)
            contacts = state["hand_contacts"]["left"]
            contact = (sum(np.asarray(sample["position"])*np.linalg.norm(sample["force_n"]) for sample in contacts)/
                       max(1e-9, sum(np.linalg.norm(sample["force_n"]) for sample in contacts))) if contacts else tip
            inward = actual-contact
            inward -= normal*np.dot(inward, normal)
            inward /= max(np.linalg.norm(inward), 1e-9)
            left_force = np.asarray(state["hand_forces_n"]["left"])
            tangent_force = left_force-inward*np.dot(inward, left_force)
            tip[1] += CONTROL_DT*np.clip(.2*(near_rim[1]-contact[1])-.003*tangent_force[1], -.002, .002)
            tip[1] = np.clip(tip[1], near_rim[1]-.025, near_rim[1]+.025)
            upward = [(np.asarray(sample["position"]), sample["force_n"][2])
                      for sample in state["hand_contacts"]["right"] if sample["force_n"][2] > .05]
            support_point = (sum(point*f for point, f in upward)/sum(f for _, f in upward)) if upward else actual
            support_x = support_point[0]
            # Let the pushing rim support the small moment from the overhang.
            # Downward pusher friction otherwise requires a large upper pinch.
            upward_target = np.clip((c.env.cfg.disk_mass*9.81*(support_x-actual[0])-
                                      (contact[2]-support_point[2])*left_force[0])/
                                     max(.05, support_x-contact[0])-.03, 0., .8*c.env.cfg.disk_mass*9.81)
            vertical_rate = .003*(upward_target-state["hand_forces_n"]["left"][2])
            if state["hand_force_magnitudes_n"]["left"] < .1:
                vertical_rate = 2.*(near_rim[2]-.004-tip[2])
            tip[2] += CONTROL_DT*np.clip(vertical_rate, -.001, .001)
            tip[2] = np.clip(tip[2], near_rim[2]-.006, near_rim[2]+.001)
            if actual[0] >= start[0]+.006 and state["hand_force_magnitudes_n"]["left"] > 2.:
                thumb_target = max(.4, 1.8-50.*(actual[0]-(c.env.cfg.edge_x-c.env.cfg.disk_radius-.005)))
                if state["hand_forces_n"]["left"][2] > .1:
                    thumb_target = .4
            if not withdrawing and actual[0]+c.env.cfg.disk_radius > c.env.cfg.edge_x+.015:
                right_shift[2] = max(-.008, right_shift[2]-.0005*CONTROL_DT)
            if actual[0]+c.env.cfg.disk_radius > c.env.cfg.edge_x+.015 and state["hand_force_magnitudes_n"]["left"] > .5:
                release_thumb = True
            if (resume and not withdrawing and actual[0] > c.env.cfg.edge_x+.01
                    and state["support_force_n"] > .4*c.env.cfg.disk_mass*9.81
                    and c.env.status["conditions"]["inverted"] and c.env.status["conditions"]["still"]):
                # Once the centre is supported inside the table, remove the
                # lower pads monotonically. Waiting for nearly all the weight
                # to reach the table can trap the disk against those pads.
                right_point, right_rotation = c.nominal_hands()["right"]
                right_shift = np.zeros(3)
                withdraw = 0.
                withdrawing = True
                c.event("withdraw_lower_pads_after_supported_centre")
            if withdrawing:
                withdraw = min(.08, withdraw+.004*CONTROL_DT)
                right_shift[2] = max(-.025, right_shift[2]-.002*CONTROL_DT)
                # With the centre on the table, push at the tabletop rim
                # height. Following a descending overhanging rim can put the
                # thumb beneath it and lever the disk upright.
                tip[2] = previous_tip[2]+CONTROL_DT*np.clip(
                    2.*(c.env.cfg.table_height+.002-previous_tip[2]), -.002, .002)
                if state["hand_force_magnitudes_n"]["right"] > c.env.cfg.contact_min_n:
                    tip[0] = min(tip[0], previous_tip[0])
            elif state["support_force_n"] > .8*c.env.cfg.disk_mass*9.81 and actual[0] > c.env.cfg.edge_x+.01:
                withdraw = min(.06, withdraw+.004*CONTROL_DT)
            right_shift[0] = -withdraw
            if state["robot_contact_force_n"] > 12.:
                tip[1:] = previous_tip[1:]
                tip[0] = min(tip[0], previous_tip[0]-.003*CONTROL_DT)
            tip[2] = previous_tip[2]+np.clip(tip[2]-previous_tip[2], -.002*CONTROL_DT, .002*CONTROL_DT)
            tick()
            if stop_after_transfer:
                state = c.object_state("disk")
                thumb_force = sum(np.linalg.norm(sample["force_n"]) for sample in state["hand_contacts"]["right"]
                                  if "right_hand_thumb_" in sample.get("robot_link", ""))
                good = (state["pos"][0] > c.env.cfg.edge_x+.01
                        and state["support_force_n"] > .5*c.env.cfg.disk_mass*9.81
                        and thumb_force < c.env.cfg.contact_min_n
                        and state["hand_force_magnitudes_n"]["left"] > .1
                        and c.env.status["conditions"]["still"] and c.env.status["conditions"]["inverted"])
                transferred = transferred+CONTROL_DT if good else 0.
                if transferred >= .5:
                    c.event("table_and_lower_pads_share_load_after_thumb_release")
                    return
            if c.env.status["conditions"]["placed"] and c.env.status["conditions"]["in_goal"]:
                break
        else:
            raise RuntimeError("bridge slide did not reach the fully supported goal")
        move(tip+[-.035, 0., 0.], 5., "unload_bridge_pusher")
        move(tip+[0., 0., .12], 6., "clear_bridge_pusher_after_placement")
        c.hold(c.env.cfg.final_hold_seconds+.5)
        if not c.env.status["success"]:
            raise RuntimeError("bridge placement did not establish released stable completion")
    finally:
        c.ik = previous_ik


def roll_and_withdraw(c):
    """Development probe: controlled roll while sliding the lower pads outward."""
    from .controller import regulate_pinch, smooth
    if c.env.cfg.post_flip_handoff not in ("supported_table_roll", "gentle_placement"):
        raise RuntimeError("table-supported rolling is outside the declared contract")
    c.require_stage(4)
    state = c.object_state("disk")
    centre = np.asarray(state["pos"])
    quat = state["quat"]
    normal = Rotation.from_quat([quat[1], quat[2], quat[3], quat[0]]).as_matrix()[:, 2]
    tangent = np.array([0., 0., 1.])-normal[2]*normal
    tangent /= np.linalg.norm(tangent)
    pivot = centre-c.env.cfg.disk_radius*tangent+c.env.cfg.disk_height/2*normal
    axis = np.cross(normal, [0., 0., -1.])
    angle = math.acos(np.clip(-normal[2], -1., 1.))
    axis /= np.linalg.norm(axis)
    hands = c.nominal_hands()
    c.pinch_errors = {}
    c.pinch_hand_load_shares = {side: 0. for side in hands}
    c.event("roll_flat_while_withdrawing_lower_pads")
    for i in range(2000):
        progress = (i+1)/2000
        amount = smooth(progress)
        turn = Rotation.from_rotvec(axis*angle*amount).as_matrix()
        slide = .09*amount
        rise = .07*smooth(max(0., (progress-.5)/.5))
        blue = -turn@normal
        c.pinch_hand_force_targets = {side: 2.-1.3*smooth(min(progress/.25, 1.)) for side in hands}
        regulate_pinch(c, c.object_state("disk"), base_force=2., responsiveness=3., support_fraction=0.)
        c.reach({side: ("palm", pivot+turn@(hands[side][0]-pivot)+slide*(turn@tangent)+rise*blue,
                       turn@hands[side][1]) for side in hands}, seed_reference=True)
        c.step()
        if c.env.status["conditions"]["inverted"] and c.env.status["conditions"]["still"]:
            return
    raise RuntimeError("controlled rolling did not establish a flat disk within its local budget")


def release_supported_hand(c, moving="left"):
    """Probe a hand release while the tilted disk remains table supported."""
    from .controller import regulate_pinch
    if c.env.cfg.post_flip_handoff not in ("supported_table_roll", "gentle_placement"):
        raise RuntimeError("table-supported release is outside the declared contract")
    c.require_stage(4)
    anchor = "right" if moving == "left" else "left"
    c.pinch_frozen_hand_references = {side: {name: float(c.q[index]) for name, index in c.index.items()
                                           if name.startswith(side+"_hand_")} for side in (moving, anchor)}
    c.pinch_open_hands = set()
    c.pinch_free_hand_targets = {}
    hands = c.nominal_hands()
    vertical = 0.
    c.event("release_hand_with_table_and_other_hand_support", moving_hand=moving)
    stable = 0.
    for i in range(2000):
        if i == 100:
            c.pinch_frozen_hand_references.pop(moving)
            c.pinch_open_hands.add(moving)
        state = c.object_state("disk")
        vertical += CONTROL_DT*np.clip(.01*(state["support_force_n"]-1.3*c.env.cfg.disk_mass*9.81), -.006, .002)
        regulate_pinch(c, c.object_state("disk"), base_force=0.)
        c.reach({side: ("palm", hands[side][0]+[0., 0., vertical], hands[side][1]) for side in hands}, seed_reference=True)
        c.step()
        stable = stable+CONTROL_DT if c.object_state("disk")["hand_force_magnitudes_n"][moving] <= c.env.cfg.contact_min_n else 0.
        if stable >= 1.:
            return
    raise RuntimeError("table-supported hand release exhausted its local budget")


def rim_regrasp(c, moving="left", table_supported=True):
    """Bounded side-rim contact probe while the other hand and table support."""
    from .controller import regulate_pinch, smooth
    state = c.object_state("disk")
    if state["hand_force_magnitudes_n"][moving] > c.env.cfg.contact_min_n:
        raise RuntimeError("rim approach requires a fully released hand")
    anchor = "right" if moving == "left" else "left"
    sign = 1. if moving == "left" else -1.
    c.pinch_frozen_hand_references = {anchor: {name: float(c.q[index]) for name, index in c.index.items()
                                             if name.startswith(anchor+"_hand_")}}
    hands = c.nominal_hands()
    c.ik.set_limit(f"{moving}_elbow_joint", -1., 2.5)
    full = (c.ik.upper.copy(), c.ik.lo.copy(), c.ik.hi.copy())
    groups = {side: [j for j, index in enumerate(full[0])
                     if next(name for name, value in c.index.items() if value == index).startswith(side+"_")
                     or (side == anchor and next(name for name, value in c.index.items() if value == index).startswith("waist_"))]
              for side in (moving, anchor)}
    c.ik._set(c.env.base_position, (1, 0, 0, 0), c.q)
    tip = c.ik.hand_point(moving, "thumb").copy()
    rotation = hands[moving][1].copy()
    vertical = 0.
    c.pinch_free_hand_targets = {}
    c.pinch_frozen_hand_references[moving] = {name: float(c.q[index]) for name, index in c.index.items()
                                            if name.startswith(moving+"_hand_")}
    def tick():
        nonlocal vertical
        state = c.object_state("disk")
        if table_supported:
            vertical += CONTROL_DT*np.clip(.01*(state["support_force_n"]-1.3*c.env.cfg.disk_mass*9.81), -.006, .002)
        regulate_pinch(c, state, base_force=0.)
        for side, task in ((anchor, ("palm", hands[anchor][0]+[0., 0., vertical], hands[anchor][1])),
                           (moving, ("thumb", tip, rotation))):
            c.ik.upper, c.ik.lo, c.ik.hi = (values[groups[side]].copy() for values in full)
            errors = c.reach({side: task}, seed_reference=True)
            if side == anchor:
                c.pinch_anchor_vertical = float(vertical)
                c.pinch_anchor_ik_error = errors[side]
        c.step()
    def move(goal, seconds, phase):
        nonlocal tip
        start = tip.copy()
        c.event(phase, moving_hand=moving)
        for i in range(round(seconds/CONTROL_DT)):
            tip = start+smooth((i+1)/round(seconds/CONTROL_DT))*(goal-start)
            tick()
    try:
        centre = np.asarray(state["pos"])
        move(tip+[0., sign*.15, 0.], 16., "withdraw_released_hand_before_reorienting")
        c.pinch_frozen_hand_references.pop(moving)
        c.pinch_free_hand_targets = {moving: {joint: 0. for joint in
            ("thumb_0", "thumb_1", "thumb_2", "index_0", "index_1", "middle_0", "middle_1")}}
        rotation = None
        move(centre+[0., sign*.25, .18], 16., "clear_released_thumb_above_side_rim")
        start_rotation = c.nominal_hands()[moving][1]
        target_rotation = (Rotation.from_euler("z", -sign*math.pi/2)*Rotation.from_euler("x", sign*math.pi/2)).as_matrix()
        delta = Rotation.from_matrix(target_rotation@start_rotation.T).as_rotvec()
        c.event("orient_thumb_for_side_rim_contact", moving_hand=moving)
        for i in range(750):
            rotation = Rotation.from_rotvec(smooth((i+1)/750)*delta).as_matrix()@start_rotation
            tick()
        state = c.object_state("disk")
        q = state["quat"]
        normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
        outward = np.array([0., sign, 0.])-sign*normal[1]*normal
        outward /= np.linalg.norm(outward)
        move(np.asarray(state["pos"])+outward*(c.env.cfg.disk_radius+.025)+[0., 0., -.004],
             16., "approach_side_rim_with_open_thumb")
        if c.last_ik_errors[moving] > .008:
            raise RuntimeError("side-rim thumb target is outside the local arm workspace")
        c.event("establish_side_rim_pressure", moving_hand=moving)
        stable = 0.
        for _ in range(2000):
            state = c.object_state("disk")
            pressure = -float(np.dot(state["hand_forces_n"][moving], outward))
            tip -= CONTROL_DT*np.clip(.001*(2.-pressure), -.001, .002)*outward
            tick()
            stable = stable+CONTROL_DT if 1.5 <= pressure <= 2.5 else 0.
            if stable >= .5:
                c.pinch_rim_goals = {moving: (tip.copy(), rotation.copy(), outward.copy())}
                return
        raise RuntimeError("side-rim pressure was not established within the local budget")
    finally:
        c.ik.upper, c.ik.lo, c.ik.hi = full


def single_hold(c, moving="left"):
    """Bounded support-transfer probe; no successful task is implied."""
    from .ik import WristClearanceIK
    previous = c.ik
    c.ik = WristClearanceIK()
    try:
        return _single_hold(c, moving)
    finally:
        c.ik = previous


def _single_hold(c, moving):
    from .controller import regulate_pinch, pinch_group_targets, pinch_loads, smooth
    if c.env.cfg.post_flip_handoff not in ("supported_single_pinch", "gentle_placement"):
        raise RuntimeError("single-pinch transfer is outside the declared task contract")
    c.require_stage(4)
    state = c.object_state("disk")
    centre = np.asarray(state["pos"])
    hands = c.nominal_hands()
    q = state["quat"]
    normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    loads, _ = pinch_group_targets(c, state, 0.)
    c.pinch_active_groups = {key for key, value in loads.items() if value > .10}
    c.pinch_errors = {}
    c.pinch_open_hands = set()
    c.attitude_rotvec = np.zeros(3)
    anchor = "right" if moving == "left" else "left"
    already_supported = (state["hand_forces_n"][anchor][2] >= .8*c.env.cfg.disk_mass*9.81
                         and state["hand_forces_n"][moving][2] <= .2*c.env.cfg.disk_mass*9.81)
    c.event("transfer_weight_to_one_pinch", holding_hand=anchor, moving_hand=moving)
    stable = 0.
    for i in range(2500):
        progress = 1. if already_supported else smooth(min((i+1)/1000, 1.))
        c.pinch_hand_force_targets = {anchor: 2.5, moving: 2.*(1.-progress)}
        c.pinch_hand_load_shares = {anchor: .5+.5*progress, moving: .5*(1.-progress)}
        state = c.object_state("disk")
        if (progress >= .99 and state["hand_forces_n"][anchor][2] >= .8*c.env.cfg.disk_mass*9.81
                and state["hand_forces_n"][moving][2] <= .2*c.env.cfg.disk_mass*9.81):
            c.pinch_open_hands.add(moving)
        regulate_pinch(c, state, base_force=2., responsiveness=3.)
        correction = c.attitude_correction(state, normal)
        c.reach({s: ("palm", centre+correction@(hands[s][0]-centre), correction@hands[s][1])
                  for s in hands}, seed_reference=True)
        c.step()
        state = c.object_state("disk")
        supported = (state["hand_force_magnitudes_n"][moving] <= c.env.cfg.contact_min_n
                     and min(pinch_loads(state, c.env.cfg)[anchor].values()) > c.env.cfg.contact_min_n
                     and state["hand_forces_n"][anchor][2] >= .8*c.env.cfg.disk_mass*9.81
                     and c.env.status["conditions"].get("still"))
        stable = stable+CONTROL_DT if supported else 0.
        if stable >= 5.:
            return
    raise RuntimeError("complete single-hand load transfer was not established within the probe budget")


def reposition_open_hand(c, moving):
    from .controller import regulate_pinch, pinch_loads, smooth
    state = c.object_state("disk")
    if state["hand_force_magnitudes_n"][moving] > c.env.cfg.contact_min_n:
        raise RuntimeError("repositioning requires the moving hand to be fully released")
    centre = np.asarray(state["pos"])
    hands = c.nominal_hands()
    q = state["quat"]
    normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    c.attitude_rotvec = np.zeros(3)
    sign = -1. if moving == "left" else 1.
    goal = hands[moving][0].copy()
    free_rotation = hands[moving][1].copy()
    released_motion = False
    c.pinch_independent_readiness = True
    for name in ("waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"):
        value = c.q[c.index[name]]
        c.ik.set_limit(name, value-.001, value+.001)
    def tick(searching=False):
        state = c.object_state("disk")
        regulate_pinch(c, state, base_force=2., responsiveness=3., searching=searching)
        correction = c.attitude_correction(state, normal)
        c.reach({s: ("palm", centre+correction@((goal if s == moving else hands[s][0])-centre),
                      free_rotation if s == moving and released_motion else correction@hands[s][1])
                  for s in hands}, seed_reference=True)
        c.step()
    def move(target, seconds, phase):
        nonlocal goal
        start = goal.copy()
        c.event(phase, moving_hand=moving)
        steps = round(seconds/CONTROL_DT)
        for i in range(steps):
            goal = start+smooth((i+1)/steps)*(target-start)
            tick()
    initial_normal = normal.copy()
    c.event("level_supported_disk_before_repositioning", moving_hand=moving)
    for i in range(500):
        amount = smooth((i+1)/500)
        normal = (1.-amount)*initial_normal+amount*np.array([0., 0., -1.])
        normal /= np.linalg.norm(normal)
        tick()
    # The holding arm must not follow a redundant whole-body IK branch while
    # the released hand moves. Keep its loaded joint references continuous.
    # The upright regrasp uses the other valid elbow branch. A bounded geometry
    # probe found this pose unreachable under the approach-only positive limit.
    c.ik.set_limit(f"{moving}_elbow_joint", -1., 2.5)
    full_ik = (c.ik.upper.copy(), c.ik.lo.copy(), c.ik.hi.copy())
    anchor = "right" if moving == "left" else "left"
    c.pinch_frozen_hand_references = {anchor: {name: float(c.q[index]) for name, index in c.index.items()
                                             if name.startswith(anchor+"_hand_")}}
    free_arm = [j for j, index in enumerate(c.ik.upper)
                if next(name for name, value in c.index.items() if value == index).startswith(moving+"_")]
    c.ik.upper, c.ik.lo, c.ik.hi = (values[free_arm].copy() for values in full_ik)
    c.ik.set_limit(f"{moving}_wrist_pitch_joint", -1.52, 1.52)
    released_motion = True
    free_rotation = None
    outside = goal.copy(); outside[1] = centre[1]-sign*.25
    move(outside, 16., "clear_open_hand_beside_disk")
    disk_now = np.asarray(c.object_state("disk")["pos"])
    outside[0] = disk_now[0]-.10; outside[2] = disk_now[2]+.15
    move(outside, 16., "move_open_hand_above_near_rim")
    start_rotation = c.nominal_hands()[moving][1]
    target_rotation = (Rotation.from_euler("z", sign*math.pi/2)*Rotation.from_euler("x", -sign*math.pi/2)).as_matrix()
    delta = Rotation.from_matrix(target_rotation@start_rotation.T).as_rotvec()
    c.event("orient_free_hand_for_upright_pinch", moving_hand=moving)
    for i in range(1000):
        free_rotation = Rotation.from_rotvec(smooth((i+1)/1000)*delta).as_matrix()@start_rotation
        tick()
    if c.last_ik_errors[moving] > .008:
        raise RuntimeError("upright regrasp orientation is outside the local arm workspace")
    profile = dict(thumb_0=.6 if moving == "left" else .25, thumb_1=-sign*.25, thumb_2=-sign*1.30,
                   index_0=sign*.05, index_1=sign*.5, middle_0=sign*.05, middle_1=sign*.5)
    c.pinch_free_hand_targets = {moving: profile}
    c.event("preshape_relocated_hand", moving_hand=moving)
    for _ in range(1500):
        tick()
        actual = c.actual_q()
        if max(abs(actual[c.index[f"{moving}_hand_{j}_joint"]]-value) for j, value in profile.items()) < .015:
            break
    else:
        raise RuntimeError("relocated hand did not reach its free preshape")
    disk_now = np.asarray(c.object_state("disk")["pos"])
    inside = goal.copy(); inside[1] = disk_now[1]-sign*.25
    inside[0] = disk_now[0]-(.07 if moving == "left" else .04); inside[2] = disk_now[2]+.12
    move(inside, 16., "approach_outside_disk_for_regrasp")
    c.pinch_thumb_faces = dict(getattr(c, "pinch_thumb_faces", {}), **{moving: 1})
    inside[2] = c.object_state("disk")["pos"][2]+.044
    move(inside, 12., "lower_open_pinch_outside_disk")
    inside[1] = c.object_state("disk")["pos"][1]-sign*(.085 if moving == "left" else .09)
    move(inside, 16., "insert_open_pinch_from_side")
    c.pinch_free_hand_targets = {}
    c.pinch_open_hands.discard(moving)
    c.pinch_distal_thumb_control = set(getattr(c, "pinch_distal_thumb_control", set())) | {moving}
    c.pinch_touched[moving] = {"top": False, "bottom": False}
    c.pinch_active_groups.update((moving, finger) for finger in ("thumb", "index", "middle"))
    c.pinch_hand_force_targets[moving] = 1.5
    c.pinch_errors = {}
    c.event("close_relocated_pinch", moving_hand=moving)
    stable = 0.
    for _ in range(1500):
        tick(searching=True)
        loads = pinch_loads(c.object_state("disk"), c.env.cfg)
        stable = stable+CONTROL_DT if min(loads[moving].values()) > .4 and c.env.status["conditions"]["bimanual_clamp"] else 0.
        if stable >= .5:
            c.ik.upper, c.ik.lo, c.ik.hi = full_ik
            c.pinch_frozen_hand_references = {}
            c.pinch_errors = {}
            return
    raise RuntimeError("relocated pinch did not establish both face contacts")


def retune_thumb_pad(c):
    """Development probe from an established upright left-hand regrasp."""
    from .controller import regulate_pinch, pinch_loads
    single_hold(c, "left")
    c.pinch_frozen_hand_references = {"right": {name: float(c.q[index]) for name, index in c.index.items()
                                               if name.startswith("right_hand_")}}
    profile = dict(thumb_0=.6, thumb_1=.2, thumb_2=1.30,
                   index_0=-.05, index_1=-.5, middle_0=-.05, middle_1=-.5)
    c.pinch_free_hand_targets = {"left": profile}
    c.event("prepare_distal_thumb_pad_below_disk")
    for _ in range(1500):
        regulate_pinch(c, c.object_state("disk"), base_force=2., responsiveness=3.)
        c.step()
        actual = c.actual_q()
        if max(abs(actual[c.index[f"left_hand_{j}_joint"]]-value) for j, value in profile.items()) < .015:
            break
    else:
        raise RuntimeError("distal pad preshape did not settle")
    c.pinch_free_hand_targets = {}
    c.pinch_open_hands.discard("left")
    c.pinch_distal_thumb_control = {"left"}
    c.pinch_touched["left"] = {"top": False, "bottom": False}
    c.pinch_active_groups.update(("left", finger) for finger in ("thumb", "index", "middle"))
    c.pinch_hand_force_targets["left"] = 1.5
    c.pinch_errors = {}
    c.event("close_distal_thumb_pad")
    stable = 0.
    for _ in range(1500):
        regulate_pinch(c, c.object_state("disk"), base_force=2., responsiveness=3., searching=True)
        c.step()
        loads = pinch_loads(c.object_state("disk"), c.env.cfg)
        stable = stable+CONTROL_DT if min(loads["left"].values()) > .4 else 0.
        if stable >= .5:
            c.pinch_frozen_hand_references = {}
            c.pinch_errors = {}
            return
    raise RuntimeError("distal thumb pad did not establish an opposing pinch")


def regrasp(c):
    from .controller import regulate_pinch, pinch_group_targets, pinch_loads, smooth
    c.require_stage(4)
    state = c.object_state("disk")
    centre = np.asarray(state["pos"])
    q = state["quat"]
    initial_normal = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()[:, 2]
    hands = c.nominal_hands()
    loads, _ = pinch_group_targets(c, state, 0.)
    c.pinch_active_groups = {key for key, value in loads.items() if value > .10}
    if hasattr(c, "wrench_targets"):
        del c.wrench_targets
    c.pinch_errors = {}
    shift = -.050-max(hands[s][0][0]-centre[0] for s in hands)
    if not -.16 <= shift <= -.06:
        raise RuntimeError("inverted grasp lies outside the bounded regrasp workspace")
    rounds = math.ceil(abs(shift)/.025)
    progress = {s: 0. for s in hands}
    thumb_indices = {s: c.index[f"{s}_hand_thumb_0_joint"] for s in hands}
    thumb_start = {s: c.actual_q()[i] for s, i in thumb_indices.items()}
    c.attitude_rotvec = np.zeros(3)
    for round_index in range(rounds):
        for moving in ("left", "right"):
            start = progress[moving]
            end = (round_index+1)/rounds
            c.pinch_preload_bias = {s: -.70 if s == moving else .70 for s in hands}
            c.pinch_hand_force_targets = {s: .55 if s == moving else 2.5 for s in hands}
            c.pinch_errors = {}
            c.event("unload_moving_pinch", hand=moving, round=round_index+1)
            for _ in range(1250):
                state = c.object_state("disk")
                regulate_pinch(c, state, base_force=1.5, responsiveness=5.)
                c.step()
                loads = pinch_loads(c.object_state("disk"), c.env.cfg)
                anchor = "right" if moving == "left" else "left"
                if sum(loads[moving].values()) < 1.6 and sum(loads[anchor].values()) > 4.:
                    break
            else:
                raise RuntimeError("moving pinch did not unload within the regrasp budget")
            c.event("slide_one_pinch_across_faces", hand=moving, round=round_index+1, rounds=rounds)
            for i in range(500):
                progress[moving] = start+smooth((i+1)/500)*(end-start)
                state = c.object_state("disk")
                if np.linalg.norm(np.asarray(state["pos"])-centre) > .035:
                    raise RuntimeError("disk drift exceeded the regrasp budget")
                regulate_pinch(c, state, base_force=1.5, responsiveness=5.)
                measured = c.actual_q()
                for side, index in thumb_indices.items():
                    desired = thumb_start[side]*(1.-2.*progress[side])
                    c.q[index] += np.clip(.8*(desired-measured[index]), -.04, .04)*CONTROL_DT
                    c.q[index] = np.clip(c.q[index], c.lo[index]+.001, c.hi[index]-.001)
                correction = c.attitude_correction(state, initial_normal)
                c.reach({s: ("palm", centre+correction@(hands[s][0]-centre+[shift*progress[s], 0., 0.]),
                              correction@hands[s][1]) for s in hands}, feedback=0., seed_reference=True)
                c.step()
    c.pinch_preload_bias = {}
    c.pinch_hand_force_targets = None


def setdown(c):
    from .controller import regulate_pinch, smooth, return_disk_to_goal
    cfg = c.env.cfg
    c.require_stage(4)
    centre = np.asarray(c.object_state("disk")["pos"])
    hands = c.nominal_hands()
    goal = np.array([cfg.edge_x+.003, centre[1], cfg.rest_z-.0005])
    c.pinch_hand_force_targets = {s: 1.8 for s in hands}
    c.pinch_hand_load_shares = {s: .5 for s in hands}
    c.pinch_frozen_hand_references = {}
    c.pinch_errors = {}
    c.attitude_rotvec = np.zeros(3)
    c.event("lower_inverted_disk_with_fingers_outside_edge")
    supported = 0.
    for i in range(1250):
        state = c.object_state("disk")
        translation = smooth(min((i+1)/1000, 1.))*(goal-centre)
        share = float(np.clip((state["pos"][2]-cfg.rest_z)/.012, 0., 1.))
        regulate_pinch(c, state, base_force=1.8, support_fraction=share)
        correction = c.attitude_correction(state, np.array([0., 0., -1.]))
        c.reach({s: ("palm", centre+translation+correction@(hands[s][0]-centre),
                      correction@hands[s][1]) for s in hands}, feedback=0., seed_reference=True)
        c.step()
        state = c.object_state("disk")
        stable_support = (state["support_forces"].get("table", 0.) >= .7*cfg.disk_mass*9.81
                          and abs(state["pos"][2]-cfg.rest_z) <= cfg.height_tolerance
                          and c.env.status["conditions"].get("inverted")
                          and c.env.status["conditions"].get("still"))
        supported = supported+CONTROL_DT if stable_support else 0.
        if supported >= .3:
            break
    else:
        raise RuntimeError("table did not take the inverted disk load within the setdown budget")
    c.event("open_both_pinches_after_table_support")
    c.pinch_open_hands = set(hands)
    c.pinch_free_hand_targets = {}
    hold = c.nominal_hands()
    released = 0.
    for _ in range(500):
        state = c.object_state("disk")
        regulate_pinch(c, state, base_force=0., support_fraction=0.)
        c.reach({s: ("palm", *hold[s]) for s in hold}, feedback=0., seed_reference=True)
        c.step()
        released = released+CONTROL_DT if c.object_state("disk")["robot_contact_force_n"] <= cfg.contact_min_n else 0.
        if released >= .25:
            break
    else:
        raise RuntimeError("pinches did not unload within the release budget")
    c.event("withdraw_open_hands_outside_edge")
    hands = c.nominal_hands()
    for i in range(300):
        c.reach({s: ("palm", hands[s][0]+[-.06*smooth((i+1)/300), 0., 0.], hands[s][1])
                  for s in hands}, feedback=0., seed_reference=True)
        c.step()
    c.move_hands({s: ("palm", c.hand_pose(s)[0]+[0., 0., .20], c.hand_pose(s)[1])
                  for s in hands}, seconds=8.)
    c.event("return_to_raised_pusher_posture")
    c.move_joints(c.initial_q, seconds=12.)
    c.configure_grasp_ik()
    return_disk_to_goal(c)


def place(c):
    """Settle the bimanual inversion, then hand the disk to the tabletop."""
    from .controller import hold_pinch
    if c.env.cfg.post_flip_handoff != "gentle_placement":
        raise RuntimeError("outside-hand placement requires the declared gentle placement contract")
    c.event("settle_after_bimanual_inversion")
    hold_pinch(c, 10.)
    # Start the handoff from the reference actually applied by the actuator
    # interface. This changes controller state only, never the simulator state.
    c.q = c.env.target.detach().cpu().numpy().astype(float)-c.gravity_offset()
    c.step()
    single_hold(c)
    c.step()
    lower_outside_bridge(c)
    c.step()
    push_across_bridge(c, stop_after_transfer=True)
    c.step()
    push_across_bridge(c, resume=True)
