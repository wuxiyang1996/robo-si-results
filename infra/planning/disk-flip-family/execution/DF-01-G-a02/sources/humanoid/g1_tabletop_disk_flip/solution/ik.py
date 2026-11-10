"""Bimanual IK with wrist-housing clearance on a separate planning model.

This is a local robot-geometry constraint, not a collision certificate for the
scene or a replacement for physical contact checks.
"""
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from humanoid.g1_support_retrieval.oracle.upper_ik import UpperBodyIK, PALM, THUMB_TIP


class WristClearanceIK(UpperBodyIK):
    def __init__(self, all_robot_pairs=False):
        super().__init__()
        self.wrist_pairs = {frozenset(self.m.body(f"{side}_wrist_{joint}_link").id
                                     for joint in ("roll", "yaw")) for side in ("left", "right")}
        bodies = set().union(*self.wrist_pairs)
        self.collision_pairs = ({frozenset((a, b)) for a in range(1, self.m.nbody)
                                 for b in range(a+1, self.m.nbody)} if all_robot_pairs else self.wrist_pairs)
        self.uses_measured_finger_geometry = all_robot_pairs
        # Margins only activate distance queries in this MuJoCo planning copy.
        # The Genesis robot geometry, friction and collision response are unchanged.
        for geom, body in enumerate(self.m.geom_bodyid):
            if body in bodies or (all_robot_pairs and self.m.geom_contype[geom]):
                self.m.geom_margin[geom] = .001

    def solve(self, root_pos, root_quat_wxyz, q, tasks, iters=12, damping=.015,
              w_rot=.35, max_step=.10):
        q = np.array(q, dtype=float, copy=True)
        cols = self.dadr[self.upper]
        jacp, jacr = np.zeros((3, self.m.nv)), np.zeros((3, self.m.nv))
        jac_other = np.zeros((3, self.m.nv))
        for _ in range(iters):
            self._set(root_pos, root_quat_wxyz, q)
            mujoco.mj_collision(self.m, self.d)
            rows, residuals = [], []
            for side, (kind, position, rotation) in tasks.items():
                body = self.wrist[side] if kind == "palm" else self.thumb[side]
                point = self.point(body, PALM[side] if kind == "palm" else THUMB_TIP[side])
                mujoco.mj_jac(self.m, self.d, jacp, jacr, point, body)
                rows.append(jacp[:, cols].copy())
                residuals.append(np.asarray(position)-point)
                if rotation is not None:
                    mujoco.mj_jacBody(self.m, self.d, None, jacr, self.wrist[side])
                    current = self.d.xmat[self.wrist[side]].reshape(3, 3)
                    rows.append(w_rot*jacr[:, cols].copy())
                    residuals.append(w_rot*Rotation.from_matrix(np.asarray(rotation)@current.T).as_rotvec())
            for contact in self.d.contact:
                a, b = self.m.geom_bodyid[[contact.geom1, contact.geom2]]
                if frozenset((a, b)) not in self.collision_pairs or contact.dist >= .001:
                    continue
                mujoco.mj_jac(self.m, self.d, jacp, None, contact.pos, a)
                mujoco.mj_jac(self.m, self.d, jac_other, None, contact.pos, b)
                normal = contact.frame[:3]
                rows.append(4.*(normal@(jac_other[:, cols]-jacp[:, cols]))[None, :])
                residuals.append(np.array([4.*(.001-contact.dist)]))
            jacobian, error = np.vstack(rows), np.concatenate(residuals)
            delta = jacobian.T@np.linalg.solve(jacobian@jacobian.T+damping**2*np.eye(len(error)), error)
            q[self.upper] = np.clip(q[self.upper]+np.clip(delta, -max_step, max_step), self.lo, self.hi)
        self._set(root_pos, root_quat_wxyz, q)
        errors = {side: float(np.linalg.norm(np.asarray(position)-self.hand_point(side, kind)))
                  for side, (kind, position, rotation) in tasks.items()}
        return q, errors
