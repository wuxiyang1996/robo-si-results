"""Bounded normal-force allocation for six measured pinch contact groups.

This local quasi-static model is a control aid, not a friction-cone certificate
or a proof that a sampled task can be executed.
"""
from itertools import combinations, product

import numpy as np


SIGNS = np.array([1., -1., -1., 1., -1., -1.])  # thumb, index, middle, per hand


def allocate_normal_forces(points, centre, normal, weight, reference, total,
                           tangent_torque=None, minimum=.10, maximum=4.0, active_mask=None):
    points, centre, normal, reference = map(np.asarray, (points, centre, normal, reference))
    if (points.shape != (6, 3) or centre.shape != (3,) or normal.shape != (3,)
            or reference.shape != (6,) or not np.isfinite(points).all()
            or not np.isfinite(centre).all() or not np.isfinite(normal).all()
            or not np.isfinite(reference).all() or not np.isfinite([weight, total, minimum, maximum]).all()
            or weight < 0 or not 0 <= minimum < maximum or abs(np.linalg.norm(normal)-1.) > 1e-5):
        raise ValueError("invalid normal-wrench inputs")
    tangent_torque = np.zeros(3) if tangent_torque is None else np.asarray(tangent_torque)
    if tangent_torque.shape != (3,) or not np.isfinite(tangent_torque).all():
        raise ValueError("invalid tangent torque")
    active_mask = np.ones(6, dtype=bool) if active_mask is None else np.asarray(active_mask, dtype=bool)
    if active_mask.shape != (6,):
        raise ValueError("invalid active contact mask")
    available = np.flatnonzero(active_mask).tolist()
    axis = np.eye(3)[np.argmin(np.abs(normal))]
    u = np.cross(normal, axis)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    torques = np.cross(points-centre, SIGNS[:, None]*normal)
    # Scale moments to a 0.1 m lever arm for numerical conditioning.
    a = np.vstack((SIGNS, torques@u/.1, torques@v/.1, np.ones(6)))
    b = np.array([weight*normal[2], -tangent_torque@u/.1, -tangent_torque@v/.1, total])
    if len(available) < 4 or np.linalg.matrix_rank(a[:, available], tol=1e-8) < 4:
        return None
    best = None
    # Four independent equalities leave two free dimensions. The closest
    # feasible allocation has zero, one or two independent active bounds.
    for count in range(len(available)-4+1):
        for active_tuple in combinations(available, count):
            active = list(active_tuple)
            free = [i for i in available if i not in active]
            af = a[:, free]
            for bounds in product((minimum, maximum), repeat=count):
                result = reference.astype(float, copy=True)
                result[~active_mask] = 0.
                result[active] = bounds
                residual = b-a[:, active]@result[active]-af@reference[free]
                result[free] += af.T@np.linalg.lstsq(af@af.T, residual, rcond=1e-10)[0]
                if (np.max(np.abs(a@result-b)) > 1e-6 or np.min(result[active_mask]) < minimum-1e-7
                        or np.max(result) > maximum+1e-7):
                    continue
                cost = float(np.sum((result-reference)**2))
                if best is None or cost < best[0]:
                    best = (cost, result)
    return None if best is None else best[1]
