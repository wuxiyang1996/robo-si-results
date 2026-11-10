"""Deterministic, simulator-independent collision assets for G1 tabletop tasks.

``write_object_urdf(spec, output_dir)`` accepts ``ring``, ``square_ring`` and
``tilting_fixture`` kinds. Lengths are metres, masses kilograms, and colors RGB
or RGBA in [0, 1]. Object ``pos`` and ``initial_pitch`` belong to the environment
and never become a world transform in an asset.

A round ring is a regular 24-sided annulus, decomposed into nonoverlapping
convex trapezoidal prisms. ``radius`` is the maximum outer radius and
``inner_radius`` is the minimum hole radius (the inner polygon's apothem).
Inertias use the actual polygon geometry, rather than a filled cylinder.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET


RING_SEGMENTS = 24


def _positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return value


def _vector(values, count, name, positive=False):
    try:
        values = tuple(float(v) for v in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must have {count} finite entries") from exc
    if len(values) != count or not all(math.isfinite(v) for v in values):
        raise ValueError(f"{name} must have {count} finite entries")
    if positive and any(v <= 0 for v in values):
        raise ValueError(f"{name} must have positive entries")
    return values


def _fmt(value):
    return format(float(value), ".15g")


def _xyz(values):
    return " ".join(_fmt(v) for v in values)


def _atomic_text(path, text):
    """Content-addressed output is safe to share between concurrent builders."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _inertial(link, mass, center, tensor):
    item = ET.SubElement(link, "inertial")
    ET.SubElement(item, "origin", xyz=_xyz(center), rpy="0 0 0")
    ET.SubElement(item, "mass", value=_fmt(mass))
    ET.SubElement(
        item, "inertia",
        **{name: _fmt(tensor[i][j]) for name, i, j in (
            ("ixx", 0, 0), ("ixy", 0, 1), ("ixz", 0, 2),
            ("iyy", 1, 1), ("iyz", 1, 2), ("izz", 2, 2)
        )}
    )


def _geometry(link, name, shape, attributes, color, center=(0, 0, 0), yaw=0):
    for tag in ("collision", "visual"):
        item = ET.SubElement(link, tag, name=f"{name}_{tag}")
        ET.SubElement(item, "origin", xyz=_xyz(center), rpy=_xyz((0, 0, yaw)))
        ET.SubElement(ET.SubElement(item, "geometry"), shape, **attributes)
        if tag == "visual":
            ET.SubElement(
                ET.SubElement(item, "material", name=f"{name}_material"),
                "color", rgba=_xyz(color)
            )


def _box_inertia(size, mass):
    x, y, z = size
    return [
        [mass * (y*y + z*z) / 12, 0.0, 0.0],
        [0.0, mass * (x*x + z*z) / 12, 0.0],
        [0.0, 0.0, mass * (x*x + y*y) / 12],
    ]


def _compound_inertia(boxes):
    """Exact inertia of disjoint boxes: [(size, center, mass), ...]."""
    mass = sum(item[2] for item in boxes)
    center = tuple(sum(c[i] * m for _, c, m in boxes) / mass for i in range(3))
    tensor = [[0.0] * 3 for _ in range(3)]
    for size, position, part_mass in boxes:
        own = _box_inertia(size, part_mass)
        delta = [position[i] - center[i] for i in range(3)]
        squared = sum(d*d for d in delta)
        for i in range(3):
            for j in range(3):
                tensor[i][j] += own[i][j] + part_mass * (
                    (squared if i == j else 0.0) - delta[i] * delta[j]
                )
    return mass, center, tensor


def _polygon_integrals(radius):
    points = [
        (radius * math.cos(2 * math.pi * i / RING_SEGMENTS),
         radius * math.sin(2 * math.pi * i / RING_SEGMENTS))
        for i in range(RING_SEGMENTS)
    ]
    area, ix, iy = 0.0, 0.0, 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        cross = x0 * y1 - x1 * y0
        area += cross / 2
        ix += cross * (y0*y0 + y0*y1 + y1*y1) / 12
        iy += cross * (x0*x0 + x0*x1 + x1*x1) / 12
    return area, ix, iy


def _ring_mesh(outer, inner, height):
    angle = math.pi / RING_SEGMENTS
    # CCW polygon, viewed from above; the bottom face reverses its winding.
    points = [
        (outer * math.cos(-angle), outer * math.sin(-angle)),
        (outer * math.cos(angle), outer * math.sin(angle)),
        (inner * math.cos(angle), inner * math.sin(angle)),
        (inner * math.cos(-angle), inner * math.sin(-angle)),
    ]
    vertices = [(x, y, z) for z in (-height/2, height/2) for x, y in points]
    faces = [(4, 3, 2, 1), (5, 6, 7, 8),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 4, 8, 7), (4, 1, 5, 8)]
    lines = ["# One closed convex prism of a 24-piece annulus."]
    lines.extend("v " + _xyz(vertex) for vertex in vertices)
    # Triangles are understood consistently by URDF mesh importers.
    for a, b, c, d in faces:
        lines.extend((f"f {a} {b} {c}", f"f {a} {c} {d}"))
    return "\n".join(lines) + "\n"


def _ring(root, cfg, folder, stem):
    outer, hole, height, mass = (
        cfg["radius"], cfg["inner_radius"], cfg["height"], cfg["mass"]
    )
    inner = hole / math.cos(math.pi / RING_SEGMENTS)
    if inner >= outer:
        raise ValueError("ring hole must fit within its 24-sided outer boundary")
    mesh = folder / f"{stem}_wedge.obj"
    _atomic_text(mesh, _ring_mesh(outer, inner, height))
    link = ET.SubElement(root, "link", name=cfg["name"])
    area0, ix0, iy0 = _polygon_integrals(outer)
    area1, ix1, iy1 = _polygon_integrals(inner)
    area, ix, iy = area0-area1, ix0-ix1, iy0-iy1
    tensor = [
        [mass * (ix/area + height*height/12), 0.0, 0.0],
        [0.0, mass * (iy/area + height*height/12), 0.0],
        [0.0, 0.0, mass * (ix+iy)/area],
    ]
    _inertial(link, mass, (0, 0, 0), tensor)
    for i in range(RING_SEGMENTS):
        _geometry(link, f"sector_{i:02d}", "mesh",
                  {"filename": mesh.as_posix(), "scale": "1 1 1"},
                  cfg["color"], yaw=2 * math.pi * i / RING_SEGMENTS)


def _square_ring(root, cfg):
    x, y = cfg["outer_size"]
    hx, hy = cfg["inner_size"]
    h, mass = cfg["height"], cfg["mass"]
    if hx >= x or hy >= y:
        raise ValueError("square_ring inner_size must be smaller than outer_size")
    # The x strips span the full y width; y strips stop at the hole's x edges.
    geometry = [
        (((x-hx)/2, y, h), (-(x+hx)/4, 0, 0)),
        (((x-hx)/2, y, h), ((x+hx)/4, 0, 0)),
        ((hx, (y-hy)/2, h), (0, -(y+hy)/4, 0)),
        ((hx, (y-hy)/2, h), (0, (y+hy)/4, 0)),
    ]
    volume = (x*y - hx*hy) * h
    boxes = [(size, center, mass * math.prod(size) / volume)
             for size, center in geometry]
    link = ET.SubElement(root, "link", name=cfg["name"])
    _inertial(link, *_compound_inertia(boxes))
    for i, (size, center) in enumerate(geometry):
        _geometry(link, f"rim_{i}", "box", {"size": _xyz(size)},
                  cfg["color"], center=center)


def _tilting_fixture(root, cfg):
    base = ET.SubElement(root, "link", name="fixture_pedestal")
    pedestal = cfg["pedestal_size"]
    pedestal_center = cfg["pedestal_offset"]
    _inertial(base, cfg["pedestal_mass"], pedestal_center,
              _box_inertia(pedestal, cfg["pedestal_mass"]))
    _geometry(base, "pedestal", "box", {"size": _xyz(pedestal)},
              cfg["color"], center=pedestal_center)
    plate = ET.SubElement(root, "link", name="fixture_plate")
    post_mass = cfg["post_mass"]
    boxes = [
        (cfg["size"], (0, 0, 0), cfg["mass"] - post_mass),
        (cfg["post_size"], cfg["post_offset"], post_mass),
    ]
    _inertial(plate, *_compound_inertia(boxes))
    _geometry(plate, "platform", "box", {"size": _xyz(cfg["size"])},
              cfg["color"])
    _geometry(plate, "post", "box", {"size": _xyz(cfg["post_size"])},
              cfg["post_color"], center=cfg["post_offset"])
    hinge = ET.SubElement(root, "joint", name="fixture_hinge", type="revolute")
    ET.SubElement(hinge, "parent", link="fixture_pedestal")
    ET.SubElement(hinge, "child", link="fixture_plate")
    ET.SubElement(hinge, "origin", xyz="0 0 0", rpy="0 0 0")
    ET.SubElement(hinge, "axis", xyz="0 1 0")
    ET.SubElement(hinge, "limit", lower="-0.04", upper="0.32",
                  effort="20", velocity="3")
    ET.SubElement(hinge, "dynamics", damping=_fmt(cfg["hinge_damping"]),
                  friction="0")


def _configuration(spec):
    kind = spec.get("kind")
    if kind not in {"ring", "square_ring", "tilting_fixture"}:
        raise ValueError(f"Unsupported tabletop asset kind: {kind!r}")
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(spec.get("name", spec.get("id", kind))))
    if not name:
        name = kind
    color = tuple(spec.get("color", (0.65, 0.55, 0.35)))
    color = _vector(color + (1.0,) if len(color) == 3 else color, 4, "color")
    if any(c < 0 or c > 1 for c in color):
        raise ValueError("color entries must be in [0, 1]")
    cfg = dict(kind=kind, name=name, color=color,
               mass=_positive(spec.get("mass", 0.15 if kind != "tilting_fixture" else 1.2), "mass"))
    if kind in {"ring", "square_ring"}:
        cfg["height"] = _positive(spec.get("height", 0.025), "height")
    if kind == "ring":
        cfg["radius"] = _positive(spec["radius"], "radius")
        cfg["inner_radius"] = _positive(spec["inner_radius"], "inner_radius")
    elif kind == "square_ring":
        cfg["outer_size"] = _vector(spec["outer_size"], 2, "outer_size", True)
        cfg["inner_size"] = _vector(spec["inner_size"], 2, "inner_size", True)
    else:
        cfg["size"] = _vector(spec.get("size", (0.36, 0.20, 0.025)), 3, "size", True)
        cfg["post_size"] = _vector(spec.get("post_size", (0.036, 0.024, 0.12)), 3, "post_size", True)
        cfg["post_offset"] = _vector(
            spec.get("post_offset", (0.04, 0, (cfg["size"][2] + cfg["post_size"][2])/2)),
            3, "post_offset"
        )
        cfg["post_mass"] = _positive(spec.get("post_mass", 0.20 * cfg["mass"]), "post_mass")
        if cfg["post_mass"] >= cfg["mass"]:
            raise ValueError("post_mass must be smaller than the moving fixture mass")
        cfg["pedestal_mass"] = _positive(spec.get("pedestal_mass", 0.4), "pedestal_mass")
        cfg["pedestal_size"] = _vector(spec.get("pedestal_size", (0.05, 0.16, 0.06)), 3, "pedestal_size", True)
        cfg["pedestal_offset"] = _vector(spec.get("pedestal_offset", (0, 0, -0.045)), 3, "pedestal_offset")
        cfg["post_color"] = (0.72, 0.74, 0.78, 1.0)
        cfg["hinge_damping"] = _positive(spec.get("hinge_damping", 0.015), "hinge_damping")
    return cfg


def write_object_urdf(spec, output_dir) -> Path:
    """Write/reuse an asset without importing a simulator, returning its absolute path.

    ``tilting_fixture`` uses ``mass`` for the moving platform plus post, with an
    optional ``post_mass`` (default 20% of mass). Its fixed pedestal has separate
    ``pedestal_mass`` (default 0.4 kg). Load this asset with ``fixed=True`` and
    preserve the ``fixture_hinge`` revolute joint; set its initial angle in the
    environment. All other objects consist of one free rigid link.
    """
    cfg = _configuration(spec)
    folder = Path(output_dir).resolve()
    digest = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16]
    stem = f"{cfg['name']}_{digest}"
    root = ET.Element("robot", name=cfg["name"])
    if cfg["kind"] == "ring":
        _ring(root, cfg, folder, stem)
    elif cfg["kind"] == "square_ring":
        _square_ring(root, cfg)
    else:
        _tilting_fixture(root, cfg)
    ET.indent(root, space="  ")
    text = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
    path = folder / f"{stem}.urdf"
    _atomic_text(path, text)
    return path
