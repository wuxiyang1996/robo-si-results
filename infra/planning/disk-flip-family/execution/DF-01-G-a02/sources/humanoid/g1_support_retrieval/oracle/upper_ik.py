"""Damped least-squares IK for the waist and arms with the base and legs held at their
measured state (the Agile policy owns the legs). Each hand task puts a point of a hand
link at a world position and, optionally, the wrist frame at a world orientation.
MuJoCo forward kinematics and Jacobians on the same MJCF the simulators load.
"""

from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from .. import task_spec as T

XML = Path(__file__).resolve().parents[1] / "assets" / "unitree_g1" / "g1_with_hands.xml"
PALM = {"left": (0.08382, 0.00406, 0.0), "right": (0.08382, -0.00406, 0.0)}   # palm centre, wrist_yaw frame
THUMB_TIP = {"left": (-0.0038, -0.0516, -0.002), "right": (-0.0038, 0.0516, -0.002)}  # thumb_2 frame
SIDES = ("left", "right")


class UpperBodyIK:
    def __init__(self):
        self.m = mujoco.MjModel.from_xml_path(str(XML))
        self.d = mujoco.MjData(self.m)
        jid = [self.m.joint(n).id for n in T.JOINT_NAMES]
        self.qadr = np.array([self.m.jnt_qposadr[j] for j in jid])
        self.dadr = np.array([self.m.jnt_dofadr[j] for j in jid])
        self.upper = np.array([i for i, n in enumerate(T.JOINT_NAMES)
                               if n.startswith("waist") or any(k in n for k in ("shoulder", "elbow", "wrist"))])
        self.lo = self.m.jnt_range[np.array(jid)[self.upper], 0] + 0.02
        self.hi = self.m.jnt_range[np.array(jid)[self.upper], 1] - 0.02
        self.wrist = {s: self.m.body(f"{s}_wrist_yaw_link").id for s in SIDES}
        self.thumb = {s: self.m.body(f"{s}_hand_thumb_2_link").id for s in SIDES}

    def set_limit(self, name, lo, hi):
        """Range the IK may use for one joint, within the model range."""
        i = list(self.upper).index(T.JOINT_NAMES.index(name))
        j = self.m.joint(name).id
        self.lo[i], self.hi[i] = max(self.m.jnt_range[j, 0] + 0.02, lo), min(self.m.jnt_range[j, 1] - 0.02, hi)

    def limit(self, name, lo, hi):
        """Narrow the range the IK may use for one joint."""
        i = list(self.upper).index(T.JOINT_NAMES.index(name))
        self.lo[i], self.hi[i] = max(self.lo[i], lo), min(self.hi[i], hi)

    def _set(self, root_pos, root_quat_wxyz, q):
        self.d.qpos[:3] = root_pos
        self.d.qpos[3:7] = root_quat_wxyz
        self.d.qpos[self.qadr] = q
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_comPos(self.m, self.d)

    def point(self, body, local):
        return self.d.xpos[body] + self.d.xmat[body].reshape(3, 3) @ np.asarray(local)

    def hand_point(self, side, kind):
        if kind == "palm":
            return self.point(self.wrist[side], PALM[side])
        return self.point(self.thumb[side], THUMB_TIP[side])

    def solve(self, root_pos, root_quat_wxyz, q, tasks, iters=8, damping=0.03, w_rot=0.3, max_step=0.15):
        """q: all joints (JOINT_NAMES order), measured or the last reference. tasks: {side:
        (kind, position, rotation matrix or None)}, kind "palm" or "thumb". Returns new q
        (only the waist and arm joints change) and the remaining position errors per side."""
        q = np.array(q, dtype=float)
        jacp, jacr = np.zeros((3, self.m.nv)), np.zeros((3, self.m.nv))
        cols = self.dadr[self.upper]
        for _ in range(iters):
            self._set(root_pos, root_quat_wxyz, q)
            rows, errs = [], []
            for side, (kind, pos, rot) in tasks.items():
                body = self.wrist[side] if kind == "palm" else self.thumb[side]
                local = PALM[side] if kind == "palm" else THUMB_TIP[side]
                p = self.point(body, local)
                mujoco.mj_jac(self.m, self.d, jacp, jacr, p, body)
                rows.append(jacp[:, cols].copy())
                errs.append(np.asarray(pos) - p)
                if rot is not None:
                    mujoco.mj_jacBody(self.m, self.d, None, jacr, self.wrist[side])
                    cur = self.d.xmat[self.wrist[side]].reshape(3, 3)
                    rows.append(w_rot * jacr[:, cols].copy())
                    errs.append(w_rot * Rotation.from_matrix(np.asarray(rot) @ cur.T).as_rotvec())
            J, e = np.vstack(rows), np.concatenate(errs)
            dq = J.T @ np.linalg.solve(J @ J.T + damping ** 2 * np.eye(len(e)), e)
            dq = np.clip(dq, -max_step, max_step)
            q[self.upper] = np.clip(q[self.upper] + dq, self.lo, self.hi)
        self._set(root_pos, root_quat_wxyz, q)
        err = {side: float(np.linalg.norm(np.asarray(pos) - self.hand_point(side, kind)))
               for side, (kind, pos, rot) in tasks.items()}
        return q, err
