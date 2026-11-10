"""Trusted per-physics-step scoring; never moves or attaches an object.

Stages require measured support and opposing hand forces. A final upside-down
pose alone cannot bypass the edge slide, grasp, clearance and controlled turn.
Limits are conservative task parameters, not calibrated damage thresholds.
"""
from copy import deepcopy
from dataclasses import dataclass, fields
from math import cos, isfinite, radians, sqrt

from humanoid.g1_tabletop_assembly.task_spec import _rotation, _vector, _norm


@dataclass(frozen=True)
class TaskConfig:
    table_height: float = .86
    table_center: tuple = (.70, 0.)
    table_size: tuple = (.70, 1.15, .05)
    disk_radius: float = .10
    disk_height: float = .012
    disk_mass: float = .12
    start_xy: tuple = (.50, 0.)
    goal_xy: tuple = (.50, 0.)
    goal_tolerance: float = .045
    overhang_min: float = .055
    overhang_max: float = .095
    control_dt: float = .02
    physics_dt: float = .0025
    friction_model: str = "elliptic"
    collision_detector: str = "gjk"
    disk_collision_shape: str = "mesh"
    post_flip_handoff: str = "gentle_placement"
    max_episode_seconds: float = 600.
    edge_hold_seconds: float = .25
    grasp_hold_seconds: float = .30
    flip_hold_seconds: float = .30
    final_hold_seconds: float = 2.
    contact_loss_grace_seconds: float = .10
    joint_target_speed_max: float = .50
    arm_stiffness_scale: float = .40
    linear_speed_max: float = .12
    angular_speed_max: float = .65
    robot_force_max_n: float = 18.
    table_force_max_n: float = 8.
    release_linear_speed: float = .015
    release_angular_speed: float = .08
    contact_min_n: float = .05
    height_tolerance: float = .004
    clearance: float = .02
    flat_tolerance_degrees: float = 8.
    object_names: tuple = ("disk",)

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, (float, int)) and (not isfinite(value) or value <= 0):
                raise ValueError(f"{field.name} must be positive and finite")
        for name, length in (("table_size", 3), ("table_center", 2),
                             ("start_xy", 2), ("goal_xy", 2)):
            _vector(getattr(self, name), length)
        if any(v <= 0 for v in self.table_size) or self.table_size[2] >= self.table_height:
            raise ValueError("invalid table dimensions")
        if not 0 < self.overhang_min < self.overhang_max < self.disk_radius:
            raise ValueError("overhang must leave the centre supported by the table")
        for xy in (self.start_xy, self.goal_xy):
            if any(abs(xy[i]-self.table_center[i])+self.disk_radius+self.goal_tolerance
                   > self.table_size[i]/2 for i in range(2)):
                raise ValueError("start and goal must leave room for the whole disk")
        if self.object_names != ("disk",):
            raise ValueError("object_names must contain only disk")
        if self.control_dt != .02 or self.flat_tolerance_degrees >= 30:
            raise ValueError("invalid sampling interval or flatness tolerance")
        if not 1 <= self.control_dt/self.physics_dt <= 20 or abs(
                self.control_dt/self.physics_dt-round(self.control_dt/self.physics_dt)) > 1e-8:
            raise ValueError("physics_dt must divide control_dt with at most 20 physics steps")
        if self.arm_stiffness_scale > 1:
            raise ValueError("gentle arm stiffness cannot exceed the shared default")
        if self.friction_model not in ("pyramidal", "elliptic"):
            raise ValueError("friction_model must be pyramidal or elliptic")
        if self.collision_detector not in ("mpr", "gjk"):
            raise ValueError("collision_detector must be mpr or gjk")
        if self.disk_collision_shape not in ("cylinder", "mesh"):
            raise ValueError("disk_collision_shape must be cylinder or mesh")
        if self.post_flip_handoff not in ("bimanual", "supported_single_pinch", "supported_table_roll", "gentle_placement"):
            raise ValueError("invalid post-flip handoff policy")

    @property
    def edge_x(self):
        return self.table_center[0]-self.table_size[0]/2

    @property
    def rest_z(self):
        return self.table_height+self.disk_height/2

    @property
    def edge_center(self):
        return (self.edge_x+self.disk_radius-(self.overhang_min+.8*(self.overhang_max-self.overhang_min)),
                self.start_xy[1], self.rest_z)

    def scene_objects(self):
        return [dict(name="disk", kind="disk", pos=(*self.start_xy, self.rest_z),
                     radius=self.disk_radius, height=self.disk_height,
                     mass=self.disk_mass, friction=.45, fixed=False, collision_shape=self.disk_collision_shape,
                     color=(.95, .48, .10, 1.))]


class Evaluator:
    stages = ("slide_to_edge", "clamp_with_both_hands", "lift_clear",
              "turn_over", "place_and_release", "complete")

    def __init__(self, cfg=None):
        self.cfg = cfg or TaskConfig()
        self.reset()

    def reset(self):
        self.elapsed = self.hold = self.lost_contact = 0.
        self.stage = 0
        self.success = self.failed = False
        self.reason = ""
        self.started = False
        self.conditions = {}
        self.peaks = dict(linear_speed_m_s=0., angular_speed_rad_s=0.,
                          robot_force_n=0., table_force_n=0.)

    def status(self):
        return deepcopy(dict(success=self.success, failed=self.failed,
            terminated=self.success or self.failed, score=float(self.success),
            reason=self.reason, stage=self.stage, phase=self.stages[self.stage],
            progress=self.stage/5, elapsed=self.elapsed, stable_seconds=self.hold,
            conditions=self.conditions, peaks=self.peaks))

    def fail(self, reason):
        self.failed, self.reason = True, reason
        return self.status()

    def update(self, state, dt):
        if self.success or self.failed:
            return self.status()
        c = self.cfg
        try:
            dt = float(dt)
            if not isfinite(dt) or not 0 < dt <= c.control_dt+1e-9:
                raise ValueError("invalid sampling interval")
            s = state["disk"]
            p = _vector(s["pos"], 3)
            rotation = _rotation(s["quat"])
            normal = tuple(row[2] for row in rotation)
            speed = _norm(_vector(s["linear_velocity"], 3))
            angular = _norm(_vector(s["angular_velocity"], 3))
            forces = {side: _vector(s["hand_forces_n"][side], 3) for side in ("left", "right")}
            magnitudes = {side: float(s["hand_force_magnitudes_n"][side]) for side in forces}
            contact_positions = s["hand_contact_positions"]
            robot = float(s["robot_contact_force_n"])
            supports = {k: float(v) for k, v in s["support_forces"].items()}
            contacts = {k: float(v) for k, v in s["contact_forces_n"].items()}
            scalars = [robot, *magnitudes.values(), *supports.values(), *contacts.values()]
            if any(not isfinite(v) or v < 0 for v in scalars):
                raise ValueError("invalid force measurement")
            if sum(magnitudes.values()) > robot+1e-4:
                raise ValueError("inconsistent robot force")
            points = {}
            for side in forces:
                if _norm(forces[side]) > magnitudes[side]+1e-4:
                    raise ValueError("inconsistent hand force")
                raw_point = contact_positions[side]
                points[side] = (_vector(raw_point, 3)
                                if magnitudes[side] > c.contact_min_n else None)
            patches = {}
            if "hand_contacts" in s:
                for side in forces:
                    patches[side] = [(_vector(item["position"], 3), _vector(item["force_n"], 3))
                                     for item in s["hand_contacts"][side]]
                    if (abs(sum(_norm(f) for _, f in patches[side])-magnitudes[side]) > 1e-4
                            or any(abs(sum(f[i] for _, f in patches[side])-forces[side][i]) > 1e-4
                                   for i in range(3))):
                        raise ValueError("inconsistent contact patches")
            table = contacts.get("table", 0.)
            support = supports.get("table", 0.)
            if support > table+1e-4:
                raise ValueError("inconsistent table force")
        except (KeyError, TypeError, ValueError, OverflowError):
            return self.fail("invalid_measurements")
        self.elapsed += dt
        if not self.started:
            self.started = True
            if (_norm(tuple(p[i]-(*c.start_xy, c.rest_z)[i] for i in range(3))) > .02
                    or normal[2] < .99):
                return self.fail("invalid_initial_state")
        for key, value in zip(self.peaks, (speed, angular, robot, table)):
            self.peaks[key] = max(self.peaks[key], value)
        for actual, limit, reason in (
                (speed, c.linear_speed_max, "disk_moved_too_fast"),
                (angular, c.angular_speed_max, "disk_turned_too_fast"),
                (robot, c.robot_force_max_n, "excessive_grip_or_push_force"),
                (table, c.table_force_max_n, "excessive_table_impact")):
            if actual > limit:
                return self.fail(reason)
        if p[2] < c.table_height-.025 or contacts.get("ground", 0.) > c.contact_min_n:
            return self.fail("disk_dropped")
        if self.elapsed >= c.max_episode_seconds:
            return self.fail("timeout")
        upright = normal[2] >= cos(radians(c.flat_tolerance_degrees))
        inverted = normal[2] <= -cos(radians(c.flat_tolerance_degrees))
        resting = abs(p[2]-c.rest_z) <= c.height_tolerance and support > c.contact_min_n
        overhang = c.edge_x-(p[0]-c.disk_radius)
        edge = (resting and upright and c.overhang_min <= overhang <= c.overhang_max
                and abs(p[1]-c.start_xy[1]) <= .04)
        # Opposite faces, inward forces and opposed net forces establish a
        # two-hand clamp. Two touch flags or same-side pushes are insufficient.
        clamp = False
        if all(points.values()):
            heights = {side: sum((points[side][i]-p[i])*normal[i] for i in range(3))
                       for side in forces}
            inward = all(sum(forces[side][i]*normal[i] for i in range(3))*heights[side]
                         < -c.contact_min_n*c.disk_height*.2 for side in forces)
            opposition = sum(forces["left"][i]*forces["right"][i] for i in range(3))
            on_disk = all(sum((points[side][i]-p[i])**2 for i in range(3))
                          - heights[side]**2 <= (c.disk_radius+.002)**2 for side in points)
            clamp = (heights["left"]*heights["right"] < -(c.disk_height*.2)**2
                     and on_disk
                     and all(abs(h) <= c.disk_height/2+.002 for h in heights.values())
                     and inward and opposition < -.5*_norm(forces["left"])*_norm(forces["right"]))
        # Each hand may instead pinch the exposed rim between its own thumb
        # and fingers. Net hand forces then need not oppose: both hands can
        # carry weight. Require measured inward load on BOTH disk faces in
        # EACH hand; two same-face touches cannot satisfy this alternative.
        pinches = {}
        for side, samples in patches.items():
            loads = {-1: 0., 1: 0.}
            for point, force in samples:
                height = sum((point[i]-p[i])*normal[i] for i in range(3))
                radial = sqrt(max(0., sum((point[i]-p[i])**2 for i in range(3))-height**2))
                if abs(height) > c.disk_height/2+.002 or radial > c.disk_radius+.002:
                    continue
                for face in (-1, 1):
                    if face*height > c.disk_height*.2:
                        loads[face] += max(0., -face*sum(force[i]*normal[i] for i in range(3)))
            pinches[side] = min(loads.values()) > c.contact_min_n
        clamp = clamp or (len(pinches) == 2 and all(pinches.values()))
        clear = p[2] >= c.table_height+c.disk_radius+c.clearance and table <= c.contact_min_n
        whole_disk_on_table = all(abs(p[i]-c.table_center[i])+c.disk_radius
                                  <= c.table_size[i]/2 for i in range(2))
        placed = resting and inverted and whole_disk_on_table
        released = robot <= c.contact_min_n
        still = speed <= c.release_linear_speed and angular <= c.release_angular_speed
        # During recontact the incoming hand can already share the weight
        # before closing its second face. Require an actual remaining pinch
        # and enough combined upward support throughout this handoff.
        single_support = (c.post_flip_handoff == "supported_single_pinch" and inverted and still
                          and any(pinches.values())
                          and sum(force[2] for force in forces.values()) >= .8*c.disk_mass*9.81)
        extent = c.disk_radius*sqrt(max(0., 1-normal[2]**2))+c.disk_height/2*abs(normal[2])
        table_handoff = (c.post_flip_handoff == "supported_table_roll" and normal[2] < 0.
                         and (support >= .7*c.disk_mass*9.81
                              or (support > c.contact_min_n and still and any(pinches.values())))
                         and support+sum(force[2] for force in forces.values()) >= .8*c.disk_mass*9.81
                         and sum(magnitudes.values()) > c.contact_min_n
                         and abs(p[2]-extent-c.table_height) <= c.height_tolerance)
        in_goal = _norm(tuple(p[i]-c.goal_xy[i] for i in range(2))) <= c.goal_tolerance
        self.conditions = dict(at_edge=edge, bimanual_clamp=clamp, clear=clear,
                               inverted=inverted, placed=placed, released=released,
                               still=still, in_goal=in_goal, single_pinch_support=single_support,
                               table_supported_handoff=table_handoff)
        if self.stage < 2 and (not upright or p[2] > c.rest_z+.015):
            return self.fail("lift_or_turn_before_edge_clamp")
        if self.stage == 2 and not upright:
            return self.fail("turn_before_clearance")
        if (self.stage in (2, 3, 4)
                and not (self.stage == 4 and (c.post_flip_handoff == "gentle_placement" or (resting and inverted)))):
            holding = clamp or (self.stage == 4 and (single_support or table_handoff))
            self.lost_contact = 0. if holding else self.lost_contact+dt
            if self.lost_contact >= c.contact_loss_grace_seconds-1e-9:
                return self.fail("lost_support_during_placement" if self.stage == 4 and
                                 c.post_flip_handoff == "supported_table_roll" else "lost_bimanual_clamp")
        else:
            self.lost_contact = 0.
        # During rotation the entire swept disk must stay above the tabletop.
        if self.stage == 3 and (p[2]-extent < c.table_height+c.clearance/2 or table > c.contact_min_n):
            return self.fail("turn_without_table_clearance")
        valid, duration = (
            (edge and still and robot > c.contact_min_n, c.edge_hold_seconds),
            (edge and clamp and still, c.grasp_hold_seconds),
            (clear and clamp and upright, c.grasp_hold_seconds),
            (clear and clamp and inverted and still, c.flip_hold_seconds),
            (placed and in_goal and released and still, c.final_hold_seconds),
        )[self.stage]
        self.hold = self.hold+dt if valid else 0.
        if self.hold >= duration-1e-9:
            self.stage += 1
            self.hold = 0.
            if self.stage == 5:
                self.success = True
        return self.status()
