"""G1 actuator specification copied from H1; no cabinet asset dependency."""
import torch

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
ACTION_DIM = NUM_JOINTS             # H6 has no infeasibility declaration action
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


