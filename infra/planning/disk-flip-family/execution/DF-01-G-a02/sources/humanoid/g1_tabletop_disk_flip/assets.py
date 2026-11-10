"""One inertial disk with one collision shape and two colored faces."""
import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from humanoid.g1_tabletop.assets import _atomic_text, _inertial


def _collision_mesh(radius, height, segments=128):
    """Closed regular prism; radial approximation error is under 31 µm at r=.1."""
    vertices = [(radius*math.cos(2*math.pi*i/segments),
                 radius*math.sin(2*math.pi*i/segments), z)
                for z in (-height/2, height/2) for i in range(segments)]
    vertices += [(0., 0., -height/2), (0., 0., height/2)]
    faces = []
    for i in range(segments):
        j = (i+1) % segments
        faces += [(i, j, j+segments), (i, j+segments, i+segments),
                  (2*segments, j, i), (2*segments+1, i+segments, j+segments)]
    return ("\n".join("v "+" ".join(format(x, ".17g") for x in p) for p in vertices)+"\n"
            +"\n".join("f "+" ".join(str(i+1) for i in f) for f in faces)+"\n")


def write_disk_urdf(spec, output_dir):
    radius, height, mass = (float(spec[k]) for k in ("radius", "height", "mass"))
    if any(not math.isfinite(v) or v <= 0 for v in (radius, height, mass)):
        raise ValueError("disk dimensions and mass must be positive and finite")
    shape = spec.get("collision_shape", "cylinder")
    if shape not in ("cylinder", "mesh"):
        raise ValueError("unsupported disk collision shape")
    root = ET.Element("robot", name="turnover_disk")
    link = ET.SubElement(root, "link", name="disk")
    axial = mass*radius**2*(2+math.cos(2*math.pi/128))/6 if shape == "mesh" else mass*radius**2/2
    transverse = axial/2+mass*height**2/12
    _inertial(link, mass, (0, 0, 0),
              ((transverse, 0, 0), (0, transverse, 0), (0, 0, axial)))
    collision = ET.SubElement(link, "collision")
    geometry = ET.SubElement(collision, "geometry")
    if shape == "mesh":
        content = _collision_mesh(radius, height)
        mesh = Path(output_dir).resolve() / ("disk_collision_"+hashlib.sha256(content.encode()).hexdigest()[:16]+".obj")
        _atomic_text(mesh, content)
        ET.SubElement(geometry, "mesh", filename=mesh.as_posix(), scale="1 1 1")
    else:
        ET.SubElement(geometry, "cylinder", radius=str(radius), length=str(height))
    # Colored halves share the same rigid link; no additional collision skins.
    for side, sign, color in (("top", 1, "0.95 0.48 0.10 1"),
                              ("bottom", -1, "0.10 0.45 0.90 1")):
        visual = ET.SubElement(link, "visual", name=side)
        ET.SubElement(visual, "origin", xyz=f"0 0 {sign*height/4}")
        ET.SubElement(ET.SubElement(visual, "geometry"), "cylinder",
                      radius=str(radius), length=str(height/2))
        ET.SubElement(ET.SubElement(visual, "material", name=side), "color", rgba=color)
    ET.indent(root, space="  ")
    content = ET.tostring(root, encoding="unicode")+"\n"
    digest = hashlib.sha256(content.encode()).hexdigest()[:16]
    path = Path(output_dir).resolve() / f"disk_{digest}.urdf"
    _atomic_text(path, content)
    return path
