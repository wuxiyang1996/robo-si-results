"""Simulator-independent definition of the G1 support-augmented retrieval RL task.

Both backends (Isaac Lab and Genesis) build the same scene from the constants here,
apply `TaskCore.sample` at every reset, hand the simulator state to `TaskCore` as a
`State`, and get back the same observations, rewards and terminations. Everything is
batched torch; nothing here imports a simulator.

Frame: per-environment origin on the floor, x from the room towards the cabinet,
y across, z up. Quaternions are (w, x, y, z). Units: m, kg, s, rad.

Task: a Unitree G1 (29 DoF + two 7-DoF Dex3 hands, 43 joints) must take the box
whose colour is given by the instruction off the cabinet top and leave it in the
goal zone. When the cabinet is too high it may move a floor box and climb it; when
no box is enough it should declare the task infeasible by holding the extra
"declare" action high. The policy controls joint position targets directly.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import torch

# --------------------------------------------------------------------------- robot
JOINT_NAMES = (
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint", "left_knee_joint",
    "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint", "right_knee_joint",
    "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint", "left_elbow_joint",
    "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    "left_hand_thumb_0_joint", "left_hand_thumb_1_joint", "left_hand_thumb_2_joint",
    "left_hand_middle_0_joint", "left_hand_middle_1_joint", "left_hand_index_0_joint", "left_hand_index_1_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint", "right_elbow_joint",
    "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
    "right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint",
    "right_hand_middle_0_joint", "right_hand_middle_1_joint", "right_hand_index_0_joint", "right_hand_index_1_joint",
)
NUM_JOINTS = len(JOINT_NAMES)
ACTION_DIM = NUM_JOINTS + 1          # joint targets + "declare infeasible"
# Hard joint limits (identical in the Isaac USD and the Menagerie MJCF), JOINT_NAMES order.
JOINT_LIMITS = (
    (-2.5307, 2.8798),
    (-0.5236, 2.9671),
    (-2.7576, 2.7576),
    (-0.0873, 2.8798),
    (-0.8727, 0.5236),
    (-0.2618, 0.2618),
    (-2.5307, 2.8798),
    (-2.9671, 0.5236),
    (-2.7576, 2.7576),
    (-0.0873, 2.8798),
    (-0.8727, 0.5236),
    (-0.2618, 0.2618),
    (-2.6180, 2.6180),
    (-0.5200, 0.5200),
    (-0.5200, 0.5200),
    (-3.0892, 2.6704),
    (-1.5882, 2.2515),
    (-2.6180, 2.6180),
    (-1.0472, 2.0944),
    (-1.9722, 1.9722),
    (-1.6144, 1.6144),
    (-1.6144, 1.6144),
    (-1.0472, 1.0472),
    (-0.7243, 1.0472),
    (0.0000, 1.7453),
    (-1.5708, 0.0000),
    (-1.7453, 0.0000),
    (-1.5708, 0.0000),
    (-1.7453, 0.0000),
    (-3.0892, 2.6704),
    (-2.2515, 1.5882),
    (-2.6180, 2.6180),
    (-1.0472, 2.0944),
    (-1.9722, 1.9722),
    (-1.6144, 1.6144),
    (-1.6144, 1.6144),
    (-1.0472, 1.0472),
    (-1.0472, 0.7243),
    (-1.7453, 0.0000),
    (0.0000, 1.5708),
    (0.0000, 1.7453),
    (0.0000, 1.5708),
    (0.0000, 1.7453),
)
# Joint order of Isaac Lab's G1 articulation (breadth-first); the pretrained lower-body
# policy indexes its inputs in this order.
ISAAC_JOINT_ORDER = (
    "left_hip_pitch_joint", "right_hip_pitch_joint", "waist_yaw_joint",
    "left_hip_roll_joint", "right_hip_roll_joint", "waist_roll_joint",
    "left_hip_yaw_joint", "right_hip_yaw_joint", "waist_pitch_joint",
    "left_knee_joint", "right_knee_joint", "left_shoulder_pitch_joint",
    "right_shoulder_pitch_joint", "left_ankle_pitch_joint", "right_ankle_pitch_joint",
    "left_shoulder_roll_joint", "right_shoulder_roll_joint", "left_ankle_roll_joint",
    "right_ankle_roll_joint", "left_shoulder_yaw_joint", "right_shoulder_yaw_joint",
    "left_elbow_joint", "right_elbow_joint", "left_wrist_roll_joint",
    "right_wrist_roll_joint", "left_wrist_pitch_joint", "right_wrist_pitch_joint",
    "left_wrist_yaw_joint", "right_wrist_yaw_joint", "left_hand_index_0_joint",
    "left_hand_middle_0_joint", "left_hand_thumb_0_joint", "right_hand_index_0_joint",
    "right_hand_middle_0_joint", "right_hand_thumb_0_joint", "left_hand_index_1_joint",
    "left_hand_middle_1_joint", "left_hand_thumb_1_joint", "right_hand_index_1_joint",
    "right_hand_middle_1_joint", "right_hand_thumb_1_joint", "left_hand_thumb_2_joint",
    "right_hand_thumb_2_joint",
)
HAND_LINKS = ("left_wrist_yaw_link", "right_wrist_yaw_link")
FOOT_LINKS = ("left_ankle_roll_link", "right_ankle_roll_link")
TORSO_LINK = "torso_link"

DEFAULT_JOINT_POS = {
    "left_hip_pitch_joint": -0.10, "right_hip_pitch_joint": -0.10,
    "left_knee_joint": 0.30, "right_knee_joint": 0.30,
    "left_ankle_pitch_joint": -0.20, "right_ankle_pitch_joint": -0.20,
}
ROBOT_BASE_HEIGHT = 0.78

# Actuators follow Isaac Lab's G1_29DOF_CFG (the configuration the pretrained lower-body
# policy was trained with). Legs and ankles are DC motors whose torque is computed in
# TaskCore-independent code (`dc_motor_torque`) and applied as effort by both backends;
# waist, arms and hands use the simulator's implicit PD drive.
# (pattern, kp, kd, effort limit, velocity limit, saturation effort, armature, kind)
JOINT_GROUPS = (
    ("hip_yaw", 100.0, 2.5, 88.0, 32.0, 180.0, 0.03, "dc"),
    ("hip_roll", 100.0, 2.5, 88.0, 32.0, 180.0, 0.03, "dc"),
    ("hip_pitch", 100.0, 2.5, 88.0, 32.0, 180.0, 0.03, "dc"),
    ("knee", 200.0, 5.0, 139.0, 20.0, 180.0, 0.03, "dc"),
    ("ankle_pitch", 20.0, 0.2, 50.0, 37.0, 80.0, 0.03, "dc"),
    ("ankle_roll", 20.0, 0.1, 50.0, 37.0, 80.0, 0.03, "dc"),
    ("waist_yaw", 5000.0, 5.0, 88.0, 32.0, 0.0, 0.001, "implicit"),
    ("waist_roll", 5000.0, 5.0, 50.0, 37.0, 0.0, 0.001, "implicit"),
    ("waist_pitch", 5000.0, 5.0, 50.0, 37.0, 0.0, 0.001, "implicit"),
    ("shoulder", 3000.0, 10.0, 300.0, 100.0, 0.0, 0.001, "implicit"),
    ("elbow", 3000.0, 10.0, 300.0, 100.0, 0.0, 0.001, "implicit"),
    ("wrist", 3000.0, 10.0, 300.0, 100.0, 0.0, 0.001, "implicit"),
    ("hand", 20.0, 2.0, 300.0, 100.0, 0.0, 0.001, "implicit"),
)
STRENGTH_GROUPS = ("hip", "knee", "ankle")   # torque limits scaled by the per-episode strength factor
ACTION_SCALE = 0.25
ACTION_CLIP = 20.0
CONTROL_DT = 0.02                    # 50 Hz policy
SIM_DT = 0.005
DECIMATION = 4


def _group(name):
    return next(g for g in JOINT_GROUPS if g[0] in name)


def joint_params():
    """Per-joint actuator parameters in JOINT_NAMES order, as a dict of tensors."""
    cols = ("kp", "kd", "effort", "vel_limit", "saturation", "armature")
    out = {c: torch.tensor([_group(n)[i + 1] for n in JOINT_NAMES]) for i, c in enumerate(cols)}
    out["dc"] = torch.tensor([_group(n)[7] == "dc" for n in JOINT_NAMES])
    out["strength"] = torch.tensor([any(s in n for s in STRENGTH_GROUPS) for n in JOINT_NAMES])
    return out


def dc_motor_torque(target, q, qd, kp, kd, effort, vel_limit, saturation):
    """Isaac Lab's DCMotor (isaaclab.actuators.DCMotor), reproduced term for term so that
    both backends apply exactly the same leg torques."""
    tau = kp * (target - q) - kd * qd
    v_lim = vel_limit * (1.0 + effort / saturation)
    qd = torch.maximum(torch.minimum(qd, v_lim), -v_lim)
    hi = torch.minimum(saturation * (1.0 - qd / vel_limit), effort)
    lo = torch.maximum(saturation * (-1.0 - qd / vel_limit), -effort)
    return torch.maximum(torch.minimum(tau, hi), lo)


def default_joint_pos():
    return torch.tensor([DEFAULT_JOINT_POS.get(n, 0.0) for n in JOINT_NAMES])


# --------------------------------------------------------------------------- scene
ROOM_X = (0.0, 4.0)
ROOM_Y = (-1.8, 1.8)
WALL_THICKNESS, WALL_HEIGHT = 0.1, 1.0
GOAL_CENTER, GOAL_SIZE = (0.6, 1.2), (0.6, 0.6)
ROBOT_START = (0.8, 0.0)

# Cabinets: real CC0 furniture models (Poly Haven) re-shelved by scripts/prepare_cabinets.py.
# Every environment holds every variant; the episode's variant stands with its front at
# CABINET_X_FRONT and the others are parked under the floor. Coloured boxes go on the top
# three levels (top surface and the two highest boards); the target's level sets the family.
CABINET_X_FRONT = 3.3
CABINET_PARK_Z = -20.0
CABINET_DIR = Path(__file__).resolve().parent / "assets" / "cabinets"
CABINET_VARIANTS = tuple(json.loads((CABINET_DIR / "index.json").read_text()))
CABINET_META = {v: json.loads((CABINET_DIR / v / "meta.json").read_text()) for v in CABINET_VARIANTS}
NUM_CABINETS = len(CABINET_VARIANTS)
TOP_LEVELS = 3
SLOTS_PER_LEVEL = 3

# Boxes on the shelf: (depth x, width y, height z), colour per slot.
TOP_SIZES = ((0.18, 0.20, 0.16), (0.20, 0.18, 0.14), (0.16, 0.22, 0.18), (0.20, 0.20, 0.15))
TOP_COLORS = ((0.80, 0.12, 0.12), (0.15, 0.60, 0.22), (0.15, 0.30, 0.80), (0.90, 0.80, 0.15))
TOP_COLOR_NAMES = ("red", "green", "blue", "yellow")
HAND_CLEARANCE = 0.10                # free space beside the target box for a hand (Dex3 ~8 cm thick)
NUM_TOP = len(TOP_SIZES)

# Movable floor boxes: two low steps, a medium box, a tall platform (only climbable from a
# step), and a tall narrow box (too high to climb and too narrow to stand on).
FLOOR_SIZES = ((0.45, 0.50, 0.18), (0.40, 0.45, 0.18), (0.40, 0.40, 0.26), (0.45, 0.50, 0.45),
               (0.24, 0.24, 0.44))
FLOOR_COLORS = ((0.60, 0.42, 0.25), (0.66, 0.50, 0.32), (0.72, 0.58, 0.40), (0.50, 0.36, 0.24),
                (0.45, 0.45, 0.48))
FLOOR_NAMES = ("step_a", "step_b", "medium", "platform", "narrow")
FLOOR_SPOTS = ((1.65, -1.3), (1.65, -0.45), (1.65, 0.45), (1.65, 1.3), (2.45, -1.3), (2.45, -0.45), (2.45, 0.45),
               (2.45, 1.3))
NUM_FLOOR = len(FLOOR_SIZES)
PARK_X = -1.5                        # absent boxes rest outside the room, behind the back wall

# Nominal capability of an unmodified G1, used only to label scene families (see README).
REACH_TOP_FROM_FLOOR = 1.15          # highest shelf whose front boxes are graspable from the floor
STEP_LIMIT = 0.30                    # highest single step treated as climbable

FAMILIES = ("direct", "one_support", "choose_support", "staircase", "infeasible")
INFEASIBLE = FAMILIES.index("infeasible")
TIERS = ("explicit", "partial", "latent")


def family_of_level(z):
    """Family a target on a level at height z belongs to, from the support it needs:
    nothing, one low box (0.18 / 0.26 m), the 0.45 m platform reached by a step, or more
    than any arrangement of the boxes allowed in infeasible scenes can give (None: unused)."""
    need = z - REACH_TOP_FROM_FLOOR
    if need <= -0.05:
        return ("direct",)
    if 0.05 <= need <= 0.15:
        return ("one_support", "choose_support")
    if 0.30 <= need <= 0.40:
        return ("staircase",)
    if need >= 0.80:
        return ("infeasible",)
    return ()


# (variant index, level index) pairs a target may use, per family.
FAMILY_OPTIONS = {f: tuple((v, k) for v, name in enumerate(CABINET_VARIANTS)
                           for k, lv in enumerate(CABINET_META[name]["top3"]) if f in family_of_level(lv["z"]))
                  for f in FAMILIES}


@dataclass
class TaskConfig:
    episode_length_s: float = 60.0
    family_weights: tuple = (1.0, 1.0, 1.0, 1.0, 1.0)
    tier_weights: tuple = (1.0, 1.0, 1.0)
    strength_range: tuple = (0.85, 1.0)      # scales leg and arm torque limits
    payload_range: tuple = (0.0, 5.0)        # kg added to the torso
    floor_boxes: bool = True                 # False parks every floor box (probes, curricula)
    start_jitter_xy: float = 0.15
    start_jitter_yaw: float = 0.3
    declare_threshold: float = 2.0           # the declare action must stay above this ...
    declare_hold_steps: int = 25             # ... for this many consecutive control steps (0.5 s)
    fall_height: float = 0.40
    fall_tilt_cos: float = 0.3               # torso "up" projected on world z below this -> fallen
    rewards: dict = field(default_factory=lambda: {
        "success": 20.0, "declare_correct": 10.0, "declare_wrong": -5.0, "fall": -10.0,
        "alive": 0.01, "progress": 1.0, "action_rate": -1e-3, "joint_vel": -1e-5,
    })


# --------------------------------------------------------------------------- math
def quat_rotate_inverse(q, v):
    """Rotate world vectors v (..., 3) into the frame of quaternions q (..., 4, wxyz)."""
    w, xyz = q[..., :1], q[..., 1:]
    t = 2.0 * torch.cross(xyz, v, dim=-1)
    return v - w * t + torch.cross(xyz, t, dim=-1)


def quat_from_yaw(yaw):
    half = 0.5 * yaw
    z = torch.zeros_like(yaw)
    return torch.stack([torch.cos(half), z, z, torch.sin(half)], dim=-1)


def yaw_of(q):
    w, x, y, z = q.unbind(-1)
    return torch.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


# --------------------------------------------------------------------------- state
@dataclass
class State:
    """Simulator state in the per-environment frame, joints in JOINT_NAMES order."""
    root_pos: torch.Tensor          # (N, 3)
    root_quat: torch.Tensor         # (N, 4)
    root_lin_vel: torch.Tensor      # (N, 3) world frame
    root_ang_vel: torch.Tensor      # (N, 3) world frame
    joint_pos: torch.Tensor         # (N, J)
    joint_vel: torch.Tensor         # (N, J)
    torso_quat: torch.Tensor        # (N, 4)
    hand_pos: torch.Tensor          # (N, 2, 3)
    top_pos: torch.Tensor           # (N, NUM_TOP, 3)
    floor_pos: torch.Tensor         # (N, NUM_FLOOR, 3)
    floor_quat: torch.Tensor        # (N, NUM_FLOOR, 4)


@dataclass
class Episode:
    """Everything a backend must apply at reset, for the environments being reset."""
    env_ids: torch.Tensor
    robot_pos: torch.Tensor         # (n, 3)
    robot_quat: torch.Tensor        # (n, 4)
    cabinet: torch.Tensor           # (n,) index into CABINET_VARIANTS standing in the room
    cabinet_pos: torch.Tensor       # (n, NUM_CABINETS, 3) origin of every variant (others parked)
    shelf_height: torch.Tensor      # (n,) surface of the level holding the target
    top_pos: torch.Tensor           # (n, NUM_TOP, 3), absent ones parked
    top_mass: torch.Tensor          # (n, NUM_TOP)
    floor_pos: torch.Tensor         # (n, NUM_FLOOR, 3), absent ones parked
    floor_quat: torch.Tensor        # (n, NUM_FLOOR, 4)
    floor_mass: torch.Tensor        # (n, NUM_FLOOR)
    floor_friction: torch.Tensor    # (n, NUM_FLOOR)
    strength: torch.Tensor          # (n,)
    payload: torch.Tensor           # (n,)


OBS_DIM = 3 + 3 + 3 + 1 + NUM_JOINTS * 2 + ACTION_DIM + 4 + 2 + TOP_LEVELS + NUM_TOP * 7 + 3 + NUM_FLOOR * 9 + 2 + 6 + 7


class TaskCore:
    """Episode sampling, observations, rewards and terminations, shared by all backends."""

    def __init__(self, num_envs, device, cfg=None, seed=0):
        self.n = num_envs
        self.device = torch.device(device)
        self.cfg = cfg or TaskConfig()
        self.seed = int(seed)
        dev = self.device
        self.episode_index = torch.zeros(num_envs, device=dev, dtype=torch.long)
        self.default_q = default_joint_pos().to(dev)
        self.max_steps = int(round(self.cfg.episode_length_s / CONTROL_DT))
        self.top_sizes = torch.tensor(TOP_SIZES, device=dev)
        metas = [CABINET_META[v] for v in CABINET_VARIANTS]
        self.cab_levels = torch.tensor([[lv["z"] for lv in m["top3"]] for m in metas], device=dev)
        self.cab_depth = torch.tensor([m["depth"] for m in metas], device=dev)
        self.cab_inner_depth = torch.tensor([m["inner_depth"] for m in metas], device=dev)
        # Slot centres along y per variant and level: the top surface spans the full width,
        # the boards the space between the side panels.
        slot = torch.linspace(-1.0, 1.0, SLOTS_PER_LEVEL, device=dev)
        half = []
        for m in metas:
            inner = (m["inner_y"][1] - m["inner_y"][0]) / 2
            half.append([m["width"] / 2 - 0.14] + [inner - 0.14] * (TOP_LEVELS - 1))
        self.cab_slot_y = torch.tensor(half, device=dev).unsqueeze(-1) * slot   # (V, levels, slots)
        # half the usable width per level (top surface: whole width; boards: between the panels)
        self.cab_half = torch.tensor([[m["width"] / 2] + [(m["inner_y"][1] - m["inner_y"][0]) / 2] * (TOP_LEVELS - 1)
                                      for m in metas], device=dev)
        self.family_options = {f: torch.tensor(FAMILY_OPTIONS[f], device=dev, dtype=torch.long)
                               for f in FAMILIES}
        self.top_colors = torch.tensor(TOP_COLORS, device=dev)
        self.floor_sizes = torch.tensor(FLOOR_SIZES, device=dev)
        self.goal = torch.tensor(GOAL_CENTER, device=dev)
        z = lambda *s, dtype=torch.float32: torch.zeros(*s, device=dev, dtype=dtype)
        self.family = z(num_envs, dtype=torch.long)
        self.tier = z(num_envs, dtype=torch.long)
        self.target = z(num_envs, dtype=torch.long)
        self.top_present = z(num_envs, NUM_TOP, dtype=torch.bool)
        self.floor_present = z(num_envs, NUM_FLOOR, dtype=torch.bool)
        self.shelf_height = z(num_envs)
        self.cabinet = z(num_envs, dtype=torch.long)
        self.levels = z(num_envs, TOP_LEVELS)
        self.strength = torch.ones(num_envs, device=dev)
        self.payload = z(num_envs)
        self.last_action = z(num_envs, ACTION_DIM)
        self.declare_count = z(num_envs, dtype=torch.long)
        self.step_count = z(num_envs, dtype=torch.long)
        self.potential = z(num_envs)
        self.target_start_z = z(num_envs)

    # ------------------------------------------------------------------ sampling
    # Counter-based randomness: every number is a hash of (seed, env id, episode index, draw
    # index), so environment i's k-th episode is the same scene in every backend no matter
    # when or in which batch it is reset. Every draw below is full width for that reason.
    _MASK = (1 << 62) - 1

    @classmethod
    def _mix(cls, x):
        x = ((x ^ (x >> 31)) * 0x3C6EF372FE94F82B) & cls._MASK
        x = ((x ^ (x >> 29)) * 0x1F83D9ABFB41BD6B) & cls._MASK
        return x ^ (x >> 32)

    def _rand(self, *shape):
        n, k = shape[0], 1
        for s in shape[1:]:
            k *= s
        cols = torch.arange(k, device=self.device, dtype=torch.long) + self._draw
        self._draw += k
        key = self._mix((self._key.unsqueeze(-1) * 1_000_003 + cols) & self._MASK)
        return (((key >> 20) & 0xFFFFFF).float() / float(1 << 24)).reshape(*shape)

    def _uniform(self, lo, hi, *shape):
        return lo + (hi - lo) * self._rand(*shape)

    def _choice(self, weights, n):
        cdf = torch.cumsum(torch.tensor(weights, device=self.device, dtype=torch.float32), 0)
        u = self._rand(n) * cdf[-1]
        return torch.searchsorted(cdf, u.unsqueeze(-1), right=True).squeeze(-1).clamp(max=len(weights) - 1)

    def sample(self, env_ids):
        n = len(env_ids)
        dev = self.device
        cfg = self.cfg
        env_ids = torch.as_tensor(env_ids, device=dev, dtype=torch.long)
        self._key = self._mix(((self.seed * 7919 + env_ids) * 104_729 + self.episode_index[env_ids]) & self._MASK)
        self._draw = 0
        self.episode_index[env_ids] += 1
        family = self._choice(cfg.family_weights, n)
        tier = self._choice(cfg.tier_weights, n)

        # The target's (cabinet variant, level) pair, drawn among those that fit the family.
        counts = torch.tensor([len(FAMILY_OPTIONS[f]) for f in FAMILIES], device=dev)
        table = torch.zeros(len(FAMILIES), int(counts.max()), 2, device=dev, dtype=torch.long)
        for i, f in enumerate(FAMILIES):
            table[i, :len(FAMILY_OPTIONS[f])] = self.family_options[f]
        k = (self._rand(n) * counts[family]).long().clamp(max=counts[family] - 1)
        cabinet, target_level = table[family, k].unbind(-1)
        levels = self.cab_levels[cabinet]
        shelf = levels.gather(1, target_level.unsqueeze(-1)).squeeze(-1)
        cabinet_pos = torch.zeros(n, NUM_CABINETS, 3, device=dev)
        cabinet_pos[..., 0] = CABINET_X_FRONT
        cabinet_pos[..., 2] = CABINET_PARK_Z
        cabinet_pos[torch.arange(n, device=dev), cabinet, 2] = 0.0

        # Floor boxes per family (slots: step_a, step_b, medium, platform, narrow). one_support:
        # a low step suffices. choose_support: the tall narrow box tempts but cannot be used.
        # staircase: only the platform is high enough, climbed from a step box. infeasible:
        # neither platform nor narrow box, so no stack of the remaining boxes reaches.
        floor_present = self._rand(n, NUM_FLOOR) < 0.5
        pick = self._rand(n) < 0.5
        one, choose, stair, inf = (family == FAMILIES.index(f)
                                   for f in ("one_support", "choose_support", "staircase", "infeasible"))
        floor_present[:, 0] |= one | (choose & pick) | (stair & pick)
        floor_present[:, 1] |= stair & ~pick
        floor_present[:, 2] |= choose & ~pick
        floor_present[:, 3] = ((floor_present[:, 3] & ~(one | choose)) | stair) & ~inf
        floor_present[:, 4] = ((floor_present[:, 4] & ~one) | choose) & ~inf
        floor_present &= cfg.floor_boxes

        # Coloured boxes: 2-4 present, each on its own (level, slot) cell of the top three
        # levels; the target takes a slot on its level, the others the remaining cells of the
        # other levels, so both sides of the target are free for the hands.
        n_top = 2 + (self._rand(n) * (NUM_TOP - 1)).long().clamp(max=NUM_TOP - 2)
        order = torch.argsort(self._rand(n, NUM_TOP), dim=-1)
        rank = torch.argsort(order, dim=-1)
        top_present = rank < n_top.unsqueeze(-1)
        target = order[:, 0]
        cells = TOP_LEVELS * SLOTS_PER_LEVEL
        target_cell = target_level * SLOTS_PER_LEVEL + (self._rand(n) * SLOTS_PER_LEVEL).long().clamp(
            max=SLOTS_PER_LEVEL - 1)
        cell_key = self._rand(n, cells)
        cell_level = torch.arange(cells, device=self.device) // SLOTS_PER_LEVEL
        cell_key = torch.where(cell_level.unsqueeze(0) == target_level.unsqueeze(-1), 2.0, cell_key)
        cell_key = cell_key.scatter(1, target_cell.unsqueeze(-1), -1.0)
        box_cell = torch.argsort(cell_key, dim=-1).gather(1, rank)
        lvl, slot = box_cell // SLOTS_PER_LEVEL, box_cell % SLOTS_PER_LEVEL
        depth = torch.where(lvl == 0, self.cab_depth[cabinet].unsqueeze(-1),
                            self.cab_inner_depth[cabinet].unsqueeze(-1))
        # 1-2 cm behind the front edge (was 1-10 cm): deeper boxes sat at the limit of the
        # G1 arm reach from the floor (oracle/runs/oracle-v12..v17)
        inset_max = (depth - self.top_sizes[:, 0] - 0.01).clamp(min=0.01, max=0.02)
        inset = 0.01 + (inset_max - 0.01) * self._rand(n, NUM_TOP)
        top_pos = torch.stack([
            CABINET_X_FRONT + inset + self.top_sizes[:, 0] / 2,
            self.cab_slot_y[cabinet.unsqueeze(-1), lvl, slot],
            levels.gather(1, lvl) + self.top_sizes[:, 2] / 2 + 0.002], dim=-1)
        # keep the target at least HAND_CLEARANCE from the side panels (edge slots move inwards)
        rows = torch.arange(n, device=self.device)
        limit = (self.cab_half[cabinet, target_level] - self.top_sizes[target, 1] / 2 - HAND_CLEARANCE).clamp(min=0.0)
        top_pos[rows, target, 1] = torch.maximum(torch.minimum(top_pos[rows, target, 1], limit), -limit)
        top_pos = torch.where(top_present.unsqueeze(-1), top_pos, self._parked(n, NUM_TOP, self.top_sizes, 0.0))

        # Floor boxes on distinct spots with jitter, random yaw, hidden mass and friction.
        spot_idx = torch.argsort(self._rand(n, len(FLOOR_SPOTS)), dim=-1)[:, :NUM_FLOOR]
        spots = torch.tensor(FLOOR_SPOTS, device=dev)[spot_idx]
        floor_xy = spots + self._uniform(-0.1, 0.1, n, NUM_FLOOR, 2)
        floor_pos = torch.cat([floor_xy, (self.floor_sizes[:, 2] / 2 + 0.002).expand(n, -1).unsqueeze(-1)], dim=-1)
        floor_pos = torch.where(floor_present.unsqueeze(-1), floor_pos, self._parked(n, NUM_FLOOR, self.floor_sizes, 1.0))
        floor_quat = quat_from_yaw(self._uniform(-0.4, 0.4, n, NUM_FLOOR))
        floor_mass = torch.stack([self._uniform(3.0, 8.0, n), self._uniform(2.0, 6.0, n), self._uniform(1.0, 8.0, n),
                                  self._uniform(6.0, 15.0, n), self._uniform(1.0, 4.0, n)], dim=-1)
        floor_friction = self._uniform(0.3, 0.8, n, NUM_FLOOR)
        slippery = self._rand(n) < 0.3            # a light, low-friction medium box: slides unless braced
        floor_mass[:, 2] = torch.where(slippery, self._uniform(0.5, 1.0, n), floor_mass[:, 2])
        floor_friction[:, 2] = torch.where(slippery, self._uniform(0.08, 0.15, n), floor_friction[:, 2])

        yaw = self._uniform(-cfg.start_jitter_yaw, cfg.start_jitter_yaw, n)
        robot_pos = torch.stack([
            ROBOT_START[0] + self._uniform(-cfg.start_jitter_xy, cfg.start_jitter_xy, n),
            ROBOT_START[1] + self._uniform(-cfg.start_jitter_xy, cfg.start_jitter_xy, n),
            torch.full((n,), ROBOT_BASE_HEIGHT, device=dev)], dim=-1)

        ep = Episode(env_ids=env_ids, robot_pos=robot_pos, robot_quat=quat_from_yaw(yaw),
                     cabinet=cabinet, cabinet_pos=cabinet_pos, shelf_height=shelf, top_pos=top_pos,
                     top_mass=self._uniform(0.3, 1.0, n, NUM_TOP), floor_pos=floor_pos, floor_quat=floor_quat,
                     floor_mass=floor_mass, floor_friction=floor_friction,
                     strength=self._uniform(*cfg.strength_range, n), payload=self._uniform(*cfg.payload_range, n))

        self.family[env_ids] = family
        self.tier[env_ids] = tier
        self.target[env_ids] = target
        self.top_present[env_ids] = top_present
        self.floor_present[env_ids] = floor_present
        self.shelf_height[env_ids] = shelf
        self.cabinet[env_ids] = cabinet
        self.levels[env_ids] = levels
        self.strength[env_ids] = ep.strength
        self.payload[env_ids] = ep.payload
        self.last_action[env_ids] = 0.0
        self.declare_count[env_ids] = 0
        self.step_count[env_ids] = 0
        self.target_start_z[env_ids] = top_pos[torch.arange(n, device=dev), target, 2]
        self.potential[env_ids] = float("nan")
        return ep

    def _parked(self, n, k, sizes, row):
        slot = torch.arange(k, device=self.device, dtype=torch.float32)
        pos = torch.stack([torch.full((k,), PARK_X - row, device=self.device),
                           -1.2 + 0.8 * slot, sizes[:, 2] / 2 + 0.002], dim=-1)
        return pos.expand(n, k, 3)

    # ------------------------------------------------------------------ observations
    def capability_obs(self):
        tier = self.tier
        one_hot = torch.nn.functional.one_hot(tier, 3).float()
        exact = torch.stack([self.strength, self.payload / 10.0,
                             torch.full_like(self.strength, REACH_TOP_FROM_FLOOR),
                             torch.full_like(self.strength, STEP_LIMIT)], dim=-1)
        coarse = torch.stack([(self.strength > 0.93).float(), (self.payload > 2.5).float(),
                              torch.ones_like(self.strength), torch.ones_like(self.strength)], dim=-1)
        info = torch.where((tier == 0).unsqueeze(-1), exact, torch.where((tier == 1).unsqueeze(-1), coarse, 0.0))
        return torch.cat([one_hot, info], dim=-1)

    def observe(self, s):
        n = self.n
        q = s.root_quat
        up = torch.tensor([0.0, 0.0, -1.0], device=self.device).expand(n, 3)
        base_rel = lambda p: quat_rotate_inverse(q.unsqueeze(1).expand(*p.shape[:-1], 4), p - s.root_pos.unsqueeze(1))
        yaw = yaw_of(q)
        top_rel = base_rel(s.top_pos)
        floor_rel = base_rel(s.floor_pos)
        floor_yaw = yaw_of(s.floor_quat) - yaw.unsqueeze(-1)
        goal3 = torch.cat([self.goal.expand(n, 2), torch.zeros(n, 1, device=self.device)], dim=-1)
        target_rgb = self.top_colors[self.target]
        tp = self.top_present.float().unsqueeze(-1)
        fp = self.floor_present.float().unsqueeze(-1)
        obs = torch.cat([
            quat_rotate_inverse(q, s.root_lin_vel), quat_rotate_inverse(q, s.root_ang_vel) * 0.25,
            quat_rotate_inverse(q, up), s.root_pos[:, 2:3],
            s.joint_pos - self.default_q, s.joint_vel * 0.05, self.last_action,
            s.root_pos[:, :2], torch.sin(yaw).unsqueeze(-1), torch.cos(yaw).unsqueeze(-1),
            (CABINET_X_FRONT - s.root_pos[:, 0]).unsqueeze(-1), self.cab_depth[self.cabinet].unsqueeze(-1),
            self.levels,
            torch.cat([tp, top_rel * tp, self.top_colors.expand(n, -1, -1) * tp], dim=-1).reshape(n, -1),
            target_rgb,
            torch.cat([fp, floor_rel * fp, torch.sin(floor_yaw).unsqueeze(-1) * fp,
                       torch.cos(floor_yaw).unsqueeze(-1) * fp, self.floor_sizes.expand(n, -1, -1) * fp],
                      dim=-1).reshape(n, -1),
            base_rel(goal3.unsqueeze(1))[:, 0, :2],
            base_rel(s.hand_pos).reshape(n, -1),
            self.capability_obs(),
        ], dim=-1)
        return torch.nan_to_num(obs).clamp(-50.0, 50.0)

    # ------------------------------------------------------------------ reward / termination
    def target_pos(self, s):
        return s.top_pos[torch.arange(self.n, device=self.device), self.target]

    def in_goal(self, p):
        half = torch.tensor(GOAL_SIZE, device=self.device) / 2
        return ((p[..., :2] - self.goal).abs() <= half).all(-1) & (p[..., 2] < 0.35)

    def step(self, s, actions):
        """Rewards and terminations for one control step; `actions` is the raw policy output."""
        cfg, w = self.cfg, self.cfg.rewards
        self.step_count += 1
        tgt = self.target_pos(s)
        hand_d = (s.hand_pos - tgt.unsqueeze(1)).norm(dim=-1).min(dim=-1).values
        goal_d = (tgt[:, :2] - self.goal).norm(dim=-1)
        lifted = (self.target_start_z - tgt[:, 2] > 0.3).float()
        phi = -hand_d - 2.0 * goal_d * lifted + 1.0 * lifted
        progress = torch.where(torch.isnan(self.potential), torch.zeros_like(phi), phi - self.potential)
        self.potential = phi

        torso_up = quat_rotate_inverse(s.torso_quat, torch.tensor([0.0, 0.0, 1.0], device=self.device).expand(self.n, 3))
        fallen = (s.root_pos[:, 2] < cfg.fall_height) | (torso_up[:, 2] < cfg.fall_tilt_cos)
        others_in_goal = (self.in_goal(s.top_pos) & self.top_present).sum(-1) - self.in_goal(tgt).long()
        success = self.in_goal(tgt) & (others_in_goal == 0) & ~fallen
        held = actions[:, -1] > cfg.declare_threshold
        self.declare_count = torch.where(held, self.declare_count + 1, torch.zeros_like(self.declare_count))
        declared = self.declare_count >= cfg.declare_hold_steps
        infeasible = self.family == INFEASIBLE

        reward = (w["alive"] + w["progress"] * progress
                  + w["action_rate"] * (actions - self.last_action).square().sum(-1)
                  + w["joint_vel"] * s.joint_vel.square().sum(-1)
                  + w["success"] * success.float()
                  + torch.where(declared, torch.where(infeasible, w["declare_correct"], w["declare_wrong"]), 0.0)
                  + w["fall"] * fallen.float())
        self.last_action = actions.clone()
        terminated = success | fallen | declared
        truncated = (self.step_count >= self.max_steps) & ~terminated
        info = {"success": success, "fallen": fallen, "declared": declared,
                "declared_correct": declared & infeasible, "lifted": lifted.bool()}
        return reward, terminated, truncated, info


def family_names(idx):
    return [FAMILIES[i] for i in idx.tolist()]
