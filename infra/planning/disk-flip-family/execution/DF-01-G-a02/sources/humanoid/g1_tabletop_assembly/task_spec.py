"""Contact-based task definition; all dimensions are metres and seconds.

The required order is support the hinged fixture with the brace, seat and
release the sleeve, then seat and release the cap. Rectangular through-holes
physically prevent a 90-degree insertion. Geometry creation belongs to the
simulator adapter; this module never edits simulation state or attaches parts.

Feed trusted measurements at every physics step. State-sequence tests validate
these scoring rules, not the physical feasibility of a robot controller.
Support measurements are named upward contact-force sums in newtons; generic
contact flags cannot substitute for the required physical load path.
"""

from copy import deepcopy
from dataclasses import dataclass
from math import cos, isfinite, radians, sqrt
from typing import Optional

_MIN_SUPPORT_FORCE_N = .05


def _vector(value, length):
    if len(value) != length:
        raise ValueError(f"expected {length} coordinates")
    result = tuple(float(v) for v in value)
    if not all(isfinite(v) for v in result):
        raise ValueError("non-finite coordinates")
    return result


def _norm(vector):
    return sqrt(sum(v * v for v in vector))


def _rotation(quaternion):
    w, x, y, z = _vector(quaternion, 4)
    length = _norm((w, x, y, z))
    if length < 1e-12:
        raise ValueError("zero quaternion")
    w, x, y, z = (v / length for v in (w, x, y, z))
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def _local(point, origin, rotation):
    difference = tuple(point[i] - origin[i] for i in range(3))
    return tuple(sum(rotation[j][i] * difference[j] for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class TaskConfig:
    table_height: float = .74
    table_center: tuple = (.55, 0.)
    table_size: tuple = (.70, 1.15, .05)
    max_episode_seconds: float = 120.
    control_dt: float = .02
    object_names: tuple = ("brace", "sleeve", "cap")
    measurement_names: tuple = ("brace", "sleeve", "cap", "fixture")
    fixture_pivot_xy: tuple = (.46, 0.)
    fixture_pivot_height: float = .075
    fixture_size: tuple = (.36, .20, .025)
    fixture_initial_pitch: float = .28
    post_offset: tuple = (.04, 0.)
    post_size: tuple = (.036, .024)
    post_height: float = .12
    brace_size: tuple = (.07, .18, .0625)
    brace_goal_xy: tuple = (.59, 0.)
    sleeve_outer_size: tuple = (.12, .10)
    sleeve_inner_size: tuple = (.044, .032)
    sleeve_height: float = .045
    cap_outer_size: tuple = (.10, .08)
    cap_inner_size: tuple = (.044, .032)
    cap_height: float = .025
    brace_stable_seconds: float = .5
    sleeve_stable_seconds: float = .5
    final_hold_seconds: float = 2.
    support_loss_grace_seconds: float = .10
    linear_speed_max: float = .025
    angular_speed_max: float = .15
    height_tolerance: float = .004
    # None derives the tolerance from the hole-to-post clearance (__post_init__).
    xy_tolerance: Optional[float] = None
    part_contact_allowance: float = .001
    max_part_tilt_degrees: float = 5.
    max_fixture_tilt_degrees: float = 3.
    drop_distance: float = .12

    def __post_init__(self):
        positive = (
            "table_height", "max_episode_seconds", "control_dt", "fixture_pivot_height",
            "post_height", "sleeve_height", "cap_height", "brace_stable_seconds",
            "sleeve_stable_seconds", "final_hold_seconds", "support_loss_grace_seconds",
            "linear_speed_max", "angular_speed_max", "height_tolerance", "part_contact_allowance",
            "max_part_tilt_degrees", "max_fixture_tilt_degrees", "drop_distance",
        )
        if any(not isfinite(getattr(self, field)) or getattr(self, field) <= 0 for field in positive):
            raise ValueError("task dimensions, time limits and tolerances must be positive and finite")
        for field, length in (
            ("table_center", 2), ("table_size", 3), ("fixture_pivot_xy", 2),
            ("fixture_size", 3), ("post_offset", 2), ("post_size", 2),
            ("brace_size", 3), ("brace_goal_xy", 2),
            ("sleeve_outer_size", 2), ("sleeve_inner_size", 2),
            ("cap_outer_size", 2), ("cap_inner_size", 2),
        ):
            values = _vector(getattr(self, field), length)
            if ("size" in field) and any(v <= 0 for v in values):
                raise ValueError(f"{field} must be positive")
        for name in ("sleeve", "cap"):
            outer = getattr(self, f"{name}_outer_size")
            inner = getattr(self, f"{name}_inner_size")
            if any(not self.post_size[i] < inner[i] < outer[i] for i in range(2)):
                raise ValueError("each through-hole must fit the post and have solid surrounding walls")
        # A seated part can rest anywhere within the hole-to-post clearance, so
        # the check asks whether it is on the post, not how centred it is.
        # Recorded configurations keep their explicit legacy value on replay.
        if self.xy_tolerance is None:
            clearance = max((getattr(self, f"{name}_inner_size")[i] - self.post_size[i]) / 2
                            for name in ("sleeve", "cap") for i in range(2))
            object.__setattr__(self, "xy_tolerance", clearance + self.part_contact_allowance)
        if not isfinite(self.xy_tolerance) or self.xy_tolerance <= 0:
            raise ValueError("xy_tolerance must be positive and finite")
        if self.sleeve_height + self.cap_height >= self.post_height:
            raise ValueError("the locating post must engage both assembled pieces")
        if abs(self.fixture_center[2] - self.fixture_size[2] / 2
               - self.table_height - self.brace_size[2]) > 1e-9:
            raise ValueError("brace height must support the horizontal fixture")
        if not isfinite(self.fixture_initial_pitch):
            raise ValueError("fixture_initial_pitch must be finite")
        if self.object_names != ("brace", "sleeve", "cap"):
            raise ValueError("object_names must be brace, sleeve, cap")
        if self.measurement_names != ("brace", "sleeve", "cap", "fixture"):
            raise ValueError("measurement_names must also include fixture")

    @property
    def fixture_center(self):
        return (*self.fixture_pivot_xy, self.table_height + self.fixture_pivot_height)

    @property
    def base_top(self):
        return self.fixture_center[2] + self.fixture_size[2] / 2

    @property
    def base_center(self):
        return tuple(self.fixture_pivot_xy[i] + self.post_offset[i] for i in range(2))

    @property
    def post_top(self):
        return self.base_top + self.post_height

    @property
    def brace_goal(self):
        return (*self.brace_goal_xy, self.table_height + self.brace_size[2] / 2)

    @property
    def sleeve_goal(self):
        return (*self.base_center, self.base_top + self.sleeve_height / 2)

    @property
    def cap_goal(self):
        return (*self.base_center, self.base_top + self.sleeve_height + self.cap_height / 2)

    def scene_objects(self):
        return scene_objects(self)


def scene_objects(cfg=None):
    """Descriptors for real collision geometry, including open rectangular rings.

    The adapter builds ``tilting_fixture`` as an unactuated y-axis hinge with
    the platform and post on one rigid link. ``square_ring`` is a single rigid
    body composed of four wall boxes, leaving its centre open.
    """
    cfg = cfg or TaskConfig()
    return [
        {
            "name": "fixture", "kind": "tilting_fixture", "pos": cfg.fixture_center,
            "size": cfg.fixture_size, "post_size": (*cfg.post_size, cfg.post_height),
            "post_offset": (*cfg.post_offset, (cfg.fixture_size[2] + cfg.post_height) / 2),
            "initial_pitch": cfg.fixture_initial_pitch,
            "color": (.40, .44, .49, 1.), "fixed": False,
        },
        {
            "name": "brace", "kind": "box",
            "pos": (.43, .40, cfg.table_height + cfg.brace_size[2] / 2),
            "size": cfg.brace_size, "mass": .35,
            "color": (.95, .66, .10, 1.), "fixed": False,
        },
        {
            "name": "sleeve", "kind": "square_ring",
            "pos": (.43, .25, cfg.table_height + cfg.sleeve_height / 2 + .002),
            "outer_size": cfg.sleeve_outer_size, "inner_size": cfg.sleeve_inner_size,
            "height": cfg.sleeve_height, "mass": .20,
            "color": (.12, .52, .89, 1.), "fixed": False,
        },
        {
            "name": "cap", "kind": "square_ring",
            "pos": (.43, -.25, cfg.table_height + cfg.cap_height / 2 + .002),
            "outer_size": cfg.cap_outer_size, "inner_size": cfg.cap_inner_size,
            "height": cfg.cap_height, "mass": .12,
            "color": (.90, .30, .16, 1.), "fixed": False,
        },
    ]


class Evaluator:
    """Read-only, terminal-latching evaluator for trusted physics measurements."""

    def __init__(self, cfg=None):
        self.cfg = cfg or TaskConfig()
        self.reset()

    def reset(self):
        self.elapsed = 0.
        self.stage = 0
        self.brace_dwell = 0.
        self.sleeve_dwell = 0.
        self.final_dwell = 0.
        self.support_lost_dwell = 0.
        self.previous_brace = False
        self.previous_sleeve = False
        self.previous_final = False
        self.success = False
        self.failed = False
        self.reason = "in_progress"
        self.conditions = {"brace_supported": False, "sleeve_seated": False, "cap_seated": False}
        self._terminal = None
        return self._result()

    def _result(self):
        if self.success:
            progress = 1.
        elif self.stage == 0:
            progress = .25 * min(1., self.brace_dwell / self.cfg.brace_stable_seconds)
        elif self.stage == 1:
            progress = .25 + .25 * min(1., self.sleeve_dwell / self.cfg.sleeve_stable_seconds)
        else:
            progress = .5 + .5 * min(1., self.final_dwell / self.cfg.final_hold_seconds)
        return {
            "success": self.success, "failed": self.failed,
            "terminated": self.success or self.failed, "reason": self.reason,
            "score": int(self.success), "progress": progress, "stage": self.stage,
            "stage_name": ("support_fixture", "insert_sleeve", "insert_cap", "complete")[self.stage],
            "elapsed_seconds": self.elapsed,
            "brace_stable_seconds": self.brace_dwell,
            "sleeve_stable_seconds": self.sleeve_dwell,
            "final_hold_seconds": self.final_dwell,
            "conditions": dict(self.conditions),
        }

    def _finish(self, reason, success=False):
        self.success = success
        self.failed = not success
        self.reason = reason
        if success:
            self.stage = 3
        self._terminal = self._result()
        return deepcopy(self._terminal)

    @staticmethod
    def _read_state(raw, brace=False):
        result = {
            "pos": _vector(raw["pos"], 3),
            "rotation": _rotation(raw["quat"]),
            "linear_velocity": _vector(raw["linear_velocity"], 3),
            "angular_velocity": _vector(raw["angular_velocity"], 3),
        }
        flags = ("hand_contact", "robot_contact", "support_contact")
        if brace:
            flags += ("fixture_contact",)
        for flag in flags:
            if not isinstance(raw[flag], bool):
                raise ValueError(f"{flag} must be a trusted boolean contact measurement")
            result[flag] = raw[flag]
        forces = raw["support_forces"]
        if not isinstance(forces, dict) or not all(isinstance(name, str) for name in forces):
            raise ValueError("support_forces must map object names to upward contact forces")
        result["support_forces"] = {}
        for name, value in forces.items():
            force = float(value)
            if isinstance(value, bool) or not isfinite(force):
                raise ValueError("support forces must be finite measurements in newtons")
            result["support_forces"][name] = force
        if brace:
            load = raw["fixture_load_n"]
            result["fixture_load_n"] = float(load)
            if isinstance(load, bool) or not isfinite(result["fixture_load_n"]):
                raise ValueError("fixture_load_n must be a finite force measurement")
        return result

    def _slow_released(self, state):
        return (
            not state["hand_contact"] and not state["robot_contact"]
            and _norm(state["linear_velocity"]) <= self.cfg.linear_speed_max
            and _norm(state["angular_velocity"]) <= self.cfg.angular_speed_max
        )

    def _brace_supported(self, brace, fixture):
        cfg = self.cfg
        tolerances = (.012, .020, cfg.height_tolerance)
        aligned_brace = (
            abs(brace["rotation"][0][0]) >= cos(radians(cfg.max_part_tilt_degrees))
            and abs(brace["rotation"][1][1]) >= cos(radians(cfg.max_part_tilt_degrees))
            and brace["rotation"][2][2] >= cos(radians(cfg.max_part_tilt_degrees))
        )
        horizontal_fixture = all(
            fixture["rotation"][i][i] >= cos(radians(cfg.max_fixture_tilt_degrees)) for i in range(3)
        )
        return (
            all(abs(brace["pos"][i] - cfg.brace_goal[i]) <= tolerances[i] for i in range(3))
            and all(abs(fixture["pos"][i] - cfg.fixture_center[i]) <= cfg.height_tolerance for i in range(3))
            and aligned_brace and horizontal_fixture
            and brace["support_contact"] and brace["fixture_contact"]
            and brace["support_forces"].get("table", 0.) > _MIN_SUPPORT_FORCE_N
            and brace["fixture_load_n"] > _MIN_SUPPORT_FORCE_N
            and fixture["support_forces"].get("brace", 0.) > _MIN_SUPPORT_FORCE_N
            and self._slow_released(brace) and self._slow_released(fixture)
        )

    def _on_post(self, state, name, fixture):
        """Detect insertion before checking release, seating, or task order."""
        cfg = self.cfg
        local = _local(state["pos"], fixture["pos"], fixture["rotation"])
        inner = getattr(cfg, f"{name}_inner_size")
        outer = getattr(cfg, f"{name}_outer_size")
        height = getattr(cfg, f"{name}_height")
        # A conservative world-to-fixture vertical bound also detects a tilted
        # piece entering the post before it is level enough to score.
        relative_z = [
            sum(fixture["rotation"][j][2] * state["rotation"][j][i] for j in range(3))
            for i in range(3)
        ]
        half_height = sum(abs(relative_z[i]) * (outer + (height,))[i] / 2 for i in range(3))
        post_bottom = cfg.fixture_size[2] / 2
        return (
            all(abs(local[i] - cfg.post_offset[i]) < inner[i] / 2 for i in range(2))
            and local[2] - half_height < post_bottom + cfg.post_height - .002
            and local[2] + half_height > post_bottom + .002
        )

    def _seated(self, state, name, fixture):
        cfg = self.cfg
        height = getattr(cfg, f"{name}_height")
        inner = getattr(cfg, f"{name}_inner_size")
        local = _local(state["pos"], fixture["pos"], fixture["rotation"])
        expected_z = cfg.fixture_size[2] / 2 + height / 2
        if name == "cap":
            expected_z += cfg.sleeve_height
        if not (
            all(abs(local[i] - cfg.post_offset[i]) <= cfg.xy_tolerance for i in range(2))
            and abs(local[2] - expected_z) <= cfg.height_tolerance
            and state["rotation"][2][2] >= cos(radians(cfg.max_part_tilt_degrees))
            and state["support_contact"] and self._slow_released(state)
            and state["support_forces"].get(
                "fixture" if name == "sleeve" else "sleeve", 0.) > _MIN_SUPPORT_FORCE_N
        ):
            return False
        # Check both faces of the hole against all four post corners. This uses
        # the actual rectangular cross-section, so a 90-degree yaw cannot pass
        # merely because its centre and height happen to match the target.
        for z in (local[2] - height / 2, local[2] + height / 2):
            for xsign in (-1, 1):
                for ysign in (-1, 1):
                    corner = (
                        cfg.post_offset[0] + xsign * cfg.post_size[0] / 2,
                        cfg.post_offset[1] + ysign * cfg.post_size[1] / 2, z,
                    )
                    world = tuple(
                        fixture["pos"][i] + sum(fixture["rotation"][i][j] * corner[j] for j in range(3))
                        for i in range(3)
                    )
                    in_piece = _local(world, state["pos"], state["rotation"])
                    if any(abs(in_piece[i]) > inner[i] / 2 + 1e-6 for i in range(2)):
                        return False
        return True

    def update(self, states, dt):
        if self._terminal is not None:
            return deepcopy(self._terminal)
        try:
            dt = float(dt)
            if not isfinite(dt) or dt <= 0 or dt > self.cfg.control_dt * 1.01:
                return self._finish("invalid_sample_interval")
            current = {
                name: self._read_state(states[name], brace=name == "brace")
                for name in self.cfg.measurement_names
            }
        except (ValueError, TypeError, KeyError, OverflowError):
            return self._finish("invalid_state")
        self.elapsed += dt
        if any(current[name]["pos"][2] < self.cfg.table_height - self.cfg.drop_distance
               for name in self.cfg.object_names):
            return self._finish("object_dropped")
        if self.elapsed + 1e-9 >= self.cfg.max_episode_seconds:
            return self._finish("timeout")

        brace, sleeve, cap, fixture = (current[name] for name in self.cfg.measurement_names)
        brace_ok = self._brace_supported(brace, fixture)
        sleeve_ok = self._seated(sleeve, "sleeve", fixture)
        cap_ok = self._seated(cap, "cap", fixture)
        self.conditions = {"brace_supported": brace_ok, "sleeve_seated": sleeve_ok, "cap_seated": cap_ok}

        # Evaluate order using the stage at the start of this sample: a single
        # frame cannot finish a prerequisite and insert the next part together.
        if self.stage < 1 and self._on_post(sleeve, "sleeve", fixture):
            return self._finish("sleeve_before_brace")
        if self.stage < 2 and self._on_post(cap, "cap", fixture):
            return self._finish("cap_before_sleeve")

        if self.stage >= 1:
            self.support_lost_dwell = 0. if brace_ok else self.support_lost_dwell + dt
            if self.support_lost_dwell + 1e-9 >= self.cfg.support_loss_grace_seconds:
                return self._finish("fixture_support_lost")

        if self.stage == 0:
            self.brace_dwell = self.brace_dwell + dt if brace_ok and self.previous_brace else 0.
            self.previous_brace = brace_ok
            if self.brace_dwell + 1e-9 >= self.cfg.brace_stable_seconds:
                self.stage = 1
        elif self.stage == 1:
            qualifies = brace_ok and sleeve_ok
            self.sleeve_dwell = self.sleeve_dwell + dt if qualifies and self.previous_sleeve else 0.
            self.previous_sleeve = qualifies
            if self.sleeve_dwell + 1e-9 >= self.cfg.sleeve_stable_seconds:
                self.stage = 2
        else:
            qualifies = brace_ok and sleeve_ok and cap_ok
            self.final_dwell = self.final_dwell + dt if qualifies and self.previous_final else 0.
            self.previous_final = qualifies
            if self.final_dwell + 1e-9 >= self.cfg.final_hold_seconds:
                return self._finish("assembled_and_released", success=True)
        return self._result()
