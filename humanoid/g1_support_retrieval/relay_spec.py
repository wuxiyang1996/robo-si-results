"""CPU-only scene specification for the versioned H1 stool-relay variant.

This module does not import Genesis, mutate task_spec, or run a controller.  The
randomized layers are design candidates, not a claim of verified solvability.
``reference_v15`` preserves the fixed seed-2 engineering scene, including its
green shelf box; it is not a three-layer benchmark acceptance result.
"""

from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


TASK_ROOT = Path(__file__).resolve().parent
SCHEMA_VERSION = "stool_relay/1.0"
CABINET_ID = "steel_frame_shelves_01_mid"
PHYSICS_DT = 0.005
CONTROL_DT = 0.02
PHYSICS = dict(self_collision=False, torsional_friction=False, elliptic_friction=False,
               noslip_iterations=0)
TOP_SIZES = ((0.18, 0.20, 0.16), (0.20, 0.18, 0.14),
             (0.16, 0.22, 0.18), (0.20, 0.20, 0.15))
TOP_COLORS = ("red", "green", "blue", "yellow")
EXTRA_SIZES = {"heavy_support": (0.46, 0.48, 0.22),
               "fixed_block": (0.40, 0.42, 0.22),
               "narrow_block": (0.16, 0.18, 0.44)}


@dataclass(frozen=True)
class RelayConfig:
    profile: str = "randomized"
    difficulty_layer: int = 1
    capability_tier: str = "explicit"
    split: str = "development"
    episode_length_s: float = 1200.0

    def __post_init__(self):
        if self.profile not in ("randomized", "reference_v15", "layer1_high_fixed"):
            raise ValueError("unknown relay profile")
        if type(self.difficulty_layer) is not int or self.difficulty_layer not in (1, 2, 3):
            raise ValueError("difficulty_layer must be 1, 2, or 3")
        if self.capability_tier not in ("explicit", "partial", "latent"):
            raise ValueError("unknown capability disclosure tier")
        if self.split not in ("development", "evaluation"):
            raise ValueError("split must be development or evaluation")
        if not math.isfinite(self.episode_length_s) or self.episode_length_s <= 0:
            raise ValueError("episode_length_s must be finite and positive")
        if self.profile in ("reference_v15", "layer1_high_fixed") and self.difficulty_layer != 1:
            raise ValueError("reference_v15 is a separate engineering baseline, not a layer 2/3 scene")


@dataclass(frozen=True)
class RelayObject:
    id: str
    kind: str
    size: tuple
    position: tuple
    quaternion: tuple = (1.0, 0.0, 0.0, 0.0)
    mass: float = 1.0
    friction: float = 0.5
    fixed: bool = False
    asset: str = "box"
    color: str = "neutral"
    top_index: int | None = None
    validation_status: str = "unvalidated"


@dataclass(frozen=True)
class RelayEpisode:
    schema_version: str
    seed: int
    episode_index: int
    split: str
    profile: str
    difficulty_layer: int
    capability_tier: str
    episode_length_s: float
    cabinet_id: str
    cabinet_position: tuple
    target_id: str
    objects: tuple
    robot_position: tuple
    robot_quaternion: tuple
    robot_joint_positions: dict
    goal_center: tuple = (0.6, 1.2)
    goal_size: tuple = (0.6, 0.6)
    board_height: float = 0.90
    target_shelf_height: float = 1.25
    support_zone_center: tuple = (3.03, 0.0)
    support_zone_half_size: tuple = (0.20, 0.26)
    requested_transport_m: float = 1.0
    validation_status: str = "unvalidated_randomized_scene"
    sampling_attempts: int = 1
    rejected_candidates: tuple = ()


def _draw(seed, episode_index, split, label, low, high):
    # Named counters: adding layer-2/3 draws never changes necessary entities.
    key = json.dumps([SCHEMA_VERSION, int(seed), int(episode_index), split, label], separators=(",", ":"))
    integer = int.from_bytes(hashlib.sha256(key.encode("utf8")).digest()[:8], "big") >> 11
    return low + (high - low) * (integer / float(1 << 53))


def _quat(yaw):
    return (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))


@lru_cache(maxsize=1)
def _asset_metadata():
    stool = json.loads((TASK_ROOT / "assets/stools/folding_stool/meta.json").read_text(encoding="utf8"))
    cabinet = json.loads((TASK_ROOT / "assets/cabinets" / CABINET_ID / "meta.json").read_text(encoding="utf8"))
    return stool, cabinet


def nominal_joint_positions():
    """The existing StepPlanner.nominal posture, without invoking its IK."""
    cfg = json.loads((TASK_ROOT / "solution/step_up/configs/sonic.json").read_text(encoding="utf8"))
    values = dict(zip(cfg["joint_names"], cfg["default"]))
    for side, sign in (("left", 1), ("right", -1)):
        values[f"{side}_shoulder_roll_joint"] = sign * 0.5
        values[f"{side}_shoulder_pitch_joint"] = -0.15
        values[f"{side}_elbow_joint"] = 1.0
        for finger, count in (("thumb", 3), ("middle", 2), ("index", 2)):
            for index in range(count):
                values[f"{side}_hand_{finger}_{index}_joint"] = 0.0
    return values


@lru_cache(maxsize=1)
def nominal_root_height():
    """One CPU FK call, matching StepPlanner's 35 mm ankle-frame floor height."""
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(TASK_ROOT / "assets/unitree_g1/g1_with_hands.xml"))
    data = mujoco.MjData(model)
    data.qpos[:] = model.qpos0
    data.qpos[:3] = [0.95, 0.0, 0.76]
    for name, value in nominal_joint_positions().items():
        data.qpos[model.joint(name).qposadr[0]] = value
    mujoco.mj_forward(model, data)
    feet_z = [data.xpos[model.body(f"{side}_ankle_roll_link").id, 2] for side in ("left", "right")]
    return float(0.76 + 0.035 - sum(feet_z) / 2)


def _sample_candidate(seed=0, episode_index=0, config=None, attempt=0):
    config = RelayConfig() if config is None else RelayConfig(**config) if isinstance(config, dict) else config
    if not isinstance(config, RelayConfig):
        raise TypeError("config must be RelayConfig or a matching dictionary")
    if type(seed) is not int or type(episode_index) is not int or seed < 0 or episode_index < 0:
        raise ValueError("seed and episode_index must be nonnegative integers")
    stool_meta, _ = _asset_metadata()
    size = tuple(stool_meta["size"])
    draw = lambda name, lo, hi: _draw(seed, episode_index, config.split,
        name if attempt == 0 else f"attempt_{attempt}/{name}", lo, hi)
    if config.profile in ("reference_v15", "layer1_high_fixed"):
        if seed != 2:
            raise ValueError("reference_v15 is the fixed TaskCore seed-2 scene; use seed=2")
        # Exact float32 values from TaskCore(seed=2), first sample, one_support,
        # floor_boxes=False, payload=0, strength=1, no start jitter.  The oracle
        # then initializes the stool and nominal robot before its first step.
        objects = [
            RelayObject("stool", "stool", size, (2.03, 0.0, size[2] / 2), mass=1.5,
                        asset="assets/stools/folding_stool/stool.urdf", validation_status="single_seed_reference"),
            RelayObject("target", "target", TOP_SIZES[0], (3.407087802886963, 0.0, 1.3320000171661377),
                        mass=0.4756770730018616, color="red", top_index=0, validation_status="single_seed_reference"),
            RelayObject("top_distractor_1", "shelf_box", TOP_SIZES[1],
                        (3.418644666671753, 0.37959998846054077, 1.5920000076293945),
                        mass=0.7267887592315674, color="green", top_index=1, validation_status="single_seed_reference"),
        ]
        robot_xy, robot_yaw = (2.03 - 0.46, 0.0), 0.0
        zone, requested = (3.03, 0.0), 1.0
        validation = "engineering_reference_single_seed_not_layer_admission"
        if config.profile == "layer1_high_fixed":
            objects = [obj for obj in objects if obj.id in ("stool", "target")]
            objects = [replace(obj, position=(obj.position[0], obj.position[1], 1.602))
                       if obj.id == "target" else obj for obj in objects]
            robot_xy = (2.03 - 0.40, 0.0)
            validation = "unvalidated_layer1_high_shelf_candidate"
    else:
        target_index = min(3, int(draw("target_color", 0, 4)))
        target_size = TOP_SIZES[target_index]
        target_y = draw("target_y", -0.06, 0.06)
        target_x = 3.3 + target_size[0] / 2 + draw("target_front_inset", 0.012, 0.020)
        stool_x = draw("stool_x", 1.95, 2.07)
        stool_y = target_y + draw("stool_y", -0.04, 0.04)
        stool_yaw = draw("stool_yaw", -0.035, 0.035)
        objects = [
            RelayObject("stool", "stool", size, (stool_x, stool_y, size[2] / 2),
                        quaternion=_quat(stool_yaw), mass=draw("stool_mass", 1.40, 1.60),
                        friction=draw("stool_friction", 0.48, 0.55), asset="assets/stools/folding_stool/stool.urdf"),
            RelayObject("target", "target", target_size, (target_x, target_y, 1.25 + target_size[2] / 2 + .002),
                        mass=draw("target_mass", 0.43, 0.52), friction=draw("target_friction", 0.48, 0.55),
                        color=TOP_COLORS[target_index], top_index=target_index),
        ]
        robot_xy = (stool_x - 0.46 + draw("robot_x", -.015, .015), stool_y + draw("robot_y", -.015, .015))
        robot_yaw = draw("robot_yaw", -.02, .02)
        zone = (3.03, target_y)
        requested = math.hypot(zone[0] - stool_x, zone[1] - stool_y)
        validation = "unvalidated_randomized_scene"
        if config.difficulty_layer >= 2:
            # Mass is physical, not a verifier exclusion. Whether a stronger body
            # can use this candidate has NOT yet been demonstrated.
            objects.append(RelayObject("heavy_support", "support_candidate", EXTRA_SIZES["heavy_support"],
                (draw("heavy_x", 1.35, 1.55), draw("heavy_y", -.95, -.85), .11),
                mass=draw("heavy_mass", 32.0, 38.0), friction=.6,
                validation_status="unvalidated_stronger_body_candidate"))
        if config.difficulty_layer >= 3:
            objects.extend([
                RelayObject("fixed_block", "fixed_object", EXTRA_SIZES["fixed_block"],
                    (draw("fixed_x", 1.40, 1.60), draw("fixed_y", .85, .95), .11), fixed=True, mass=8., friction=.5,
                    validation_status="fixed_physically_not_blacklisted"),
                RelayObject("narrow_block", "narrow_object", EXTRA_SIZES["narrow_block"],
                    (draw("narrow_x", 2.35, 2.50), draw("narrow_y", -.95, -.85), .22), mass=2.5, friction=.5,
                    validation_status="unvalidated_alternative_affordances"),
            ])
    return RelayEpisode(SCHEMA_VERSION, seed, episode_index, config.split, config.profile,
        config.difficulty_layer, config.capability_tier, config.episode_length_s, CABINET_ID, (3.3, 0., 0.),
        "target", tuple(objects), (*robot_xy, nominal_root_height()), _quat(robot_yaw), nominal_joint_positions(),
        support_zone_center=zone, requested_transport_m=requested, validation_status=validation,
        target_shelf_height=1.52 if config.profile == "layer1_high_fixed" else 1.25)


@lru_cache(maxsize=1)
def _nominal_sole_centers():
    import mujoco
    model = mujoco.MjModel.from_xml_path(str(TASK_ROOT / "assets/unitree_g1/g1_with_hands.xml"))
    data = mujoco.MjData(model)
    data.qpos[:] = model.qpos0
    data.qpos[:3] = [0., 0., nominal_root_height()]
    for name, value in nominal_joint_positions().items():
        data.qpos[model.joint(name).qposadr[0]] = value
    mujoco.mj_forward(model, data)
    points = []
    for side in ("left", "right"):
        body = model.body(f"{side}_ankle_roll_link").id
        for geom in range(model.ngeom):
            if model.geom_bodyid[geom] == body and model.geom_type[geom] == mujoco.mjtGeom.mjGEOM_SPHERE:
                points.append((float(data.geom_xpos[geom, 0]), float(data.geom_xpos[geom, 1]),
                               float(model.geom_size[geom, 0])))
    if len(points) != 8:
        raise ValueError("expected eight physical foot-contact spheres for reset geometry validation")
    return tuple(points)


def geometry_errors(episode):
    """Conservative initial geometry checks; they do not certify dynamic feasibility."""
    errors, boxes = [], {}
    stool, cabinet = _asset_metadata()
    for obj in episode.objects:
        if not all(math.isfinite(float(v)) for v in (*obj.position, *obj.quaternion, *obj.size, obj.mass, obj.friction)):
            errors.append(f"{obj.id}: nonfinite geometry or physical parameter")
            continue
        if min(obj.size) <= 0 or obj.mass <= 0 or obj.friction <= 0:
            errors.append(f"{obj.id}: nonpositive size, mass or friction")
        if abs(sum(v*v for v in obj.quaternion) - 1.) > 1e-6:
            errors.append(f"{obj.id}: invalid unit quaternion")
        w, x, y, z = obj.quaternion
        rotation = ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
                    (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
                    (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))
        size = stool["footprint"] if obj.id == "stool" else obj.size
        extents = [sum(abs(rotation[i][j])*size[j]/2 for j in range(3)) for i in range(3)]
        bounds = [(obj.position[i]-extents[i], obj.position[i]+extents[i]) for i in range(3)]
        boxes[obj.id] = bounds
        if bounds[0][0] < .01 or bounds[0][1] > 3.99 or bounds[1][0] < -1.79 or bounds[1][1] > 1.79:
            errors.append(f"{obj.id}: outside room interior")
        if obj.top_index is None and abs(bounds[2][0]) > .003:
            errors.append(f"{obj.id}: not initialized on the ground")
    for index, first in enumerate(episode.objects):
        for second in episode.objects[index+1:]:
            if first.id not in boxes or second.id not in boxes:
                continue
            a, b = boxes[first.id], boxes[second.id]
            if all(min(a[i][1], b[i][1]) - max(a[i][0], b[i][0]) > -.005 for i in range(3)):
                errors.append(f"{first.id}/{second.id}: overlapping or insufficient initial clearance")
    for obj in episode.objects:
        if obj.top_index is None or obj.id not in boxes:
            continue
        lo, hi = boxes[obj.id][:2]
        bottom = boxes[obj.id][2][0]
        supports = [c for c in cabinet["colliders"] if c[3] > .3 and c[4] > .5
                    and abs(c[2]+c[5]/2+episode.cabinet_position[2]-bottom) <= .004]
        if not any(lo[0] >= c[0]+episode.cabinet_position[0]-c[3]/2 and
                   lo[1] <= c[0]+episode.cabinet_position[0]+c[3]/2 and
                   hi[0] >= c[1]+episode.cabinet_position[1]-c[4]/2 and
                   hi[1] <= c[1]+episode.cabinet_position[1]+c[4]/2 for c in supports):
            errors.append(f"{obj.id}: footprint or bottom outside its actual cabinet shelf")
    yaw = 2*math.atan2(episode.robot_quaternion[3], episode.robot_quaternion[0])
    c, s = math.cos(yaw), math.sin(yaw)
    robot_points = [(episode.robot_position[0]+c*x-s*y, episode.robot_position[1]+s*x+c*y, radius)
                    for x, y, radius in _nominal_sole_centers()]
    rb = [(min(p[i]-p[2] for p in robot_points), max(p[i]+p[2] for p in robot_points)) for i in range(2)]
    if rb[0][0] < .01 or rb[0][1] > 3.99 or rb[1][0] < -1.79 or rb[1][1] > 1.79:
        errors.append("robot: initial foot footprint outside room")
    for obj in episode.objects:
        if obj.top_index is not None or obj.id not in boxes:
            continue
        b = boxes[obj.id]
        if all(min(rb[i][1], b[i][1])-max(rb[i][0], b[i][0]) > -.02 for i in range(2)):
            errors.append(f"robot/{obj.id}: initial foot footprint overlap or insufficient standoff")
    return errors


def sample_episode(seed=0, episode_index=0, config=None, *, max_attempts=32):
    """Deterministic rejection sampling over the complete nested candidate pool."""
    config = RelayConfig() if config is None else RelayConfig(**config) if isinstance(config, dict) else config
    if not isinstance(config, RelayConfig):
        raise TypeError("config must be RelayConfig or a matching dictionary")
    if type(max_attempts) is not int or max_attempts < 1 or max_attempts > 1024:
        raise ValueError("max_attempts must be an integer in 1..1024")
    full = config if config.profile in ("reference_v15", "layer1_high_fixed") else replace(config, difficulty_layer=3)
    rejected = []
    for attempt in range(1 if config.profile == "reference_v15" else max_attempts):
        candidate = _sample_candidate(seed, episode_index, full, attempt)
        errors = geometry_errors(candidate)
        if not errors:
            count = len(candidate.objects) if config.profile == "reference_v15" else (2, 3, 5)[config.difficulty_layer-1]
            return replace(candidate, difficulty_layer=config.difficulty_layer, objects=candidate.objects[:count],
                           sampling_attempts=attempt+1, rejected_candidates=tuple(rejected))
        rejected.append(dict(attempt=attempt, reasons=errors))
    raise ValueError(f"relay scene geometry rejected after {len(rejected)} attempt(s): {json.dumps(rejected)}")


def build_relay_metadata(episode):
    """JSON-ready private metadata; callers must not expose this whole dict to agents."""
    if not isinstance(episode, RelayEpisode):
        raise TypeError("expected RelayEpisode")
    stool, cabinet = _asset_metadata()
    target = next(obj for obj in episode.objects if obj.id == episode.target_id)
    board_geoms = [i for i, c in enumerate(cabinet["colliders"])
                   if abs(c[2] + c[5] / 2 - episode.board_height) < 1e-5 and c[3] > .3 and c[4] > .5]
    if len(board_geoms) != 1:
        raise ValueError("expected one actual broad collider at the relay-board height")
    plate = cabinet["colliders"][board_geoms[0]]
    cx, cy = episode.cabinet_position[:2]
    surface = dict(id="relay_board", center_xy=[cx + plate[0], cy + plate[1]], size_xy=plate[3:5],
                   z=episode.board_height, collider_indices=board_geoms)
    source_geoms = [i for i, c in enumerate(cabinet["colliders"])
                    if abs(c[2] + c[5] / 2 - episode.target_shelf_height) < 1e-5
                    and c[3] > .3 and c[4] > .5]
    if len(source_geoms) != 1:
        raise ValueError("expected one actual broad collider beneath the initial target")
    source_plate = cabinet["colliders"][source_geoms[0]]
    original_surface = dict(id="original_target_shelf",
        center_xy=[cx + source_plate[0], cy + source_plate[1]], size_xy=source_plate[3:5],
        z=episode.target_shelf_height, collider_indices=source_geoms)
    objects = {}
    for obj in episode.objects:
        value = asdict(obj)
        value["initial_position"] = value.pop("position")
        value["initial_quaternion"] = value.pop("quaternion")
        value["support_top_local_z"] = obj.size[2] / 2
        if obj.id == "stool":
            value["colliders"] = json.loads(json.dumps(stool["colliders"]))
            value["footprint"] = list(stool["footprint"])
            value["support_top_local_z"] = stool["top_z"] - stool["size"][2] / 2
        objects[obj.id] = value
    xml = ET.parse(TASK_ROOT / "assets/unitree_g1/g1_with_hands.xml").getroot()
    foot_default = xml.find(".//default[@class='foot']/geom")
    radius = float(foot_default.get("size"))
    foot_geometry, foot_points = {}, {}
    for side in ("left", "right"):
        name = f"{side}_ankle_roll_link"
        geoms = xml.find(f".//body[@name='{name}']").findall("geom[@class='foot']")
        centers = [list(map(float, geom.get("pos").split())) for geom in geoms]
        foot_geometry[name] = [dict(center=center, radius=radius) for center in centers]
        foot_points[name] = [[center[0], center[1], center[2] - radius] for center in centers]
    return dict(kind="stool_relay", schema_version=episode.schema_version, profile=episode.profile,
        evidence_schema_version="relay-evidence/2", rubric_version="relay-rubric/2.1",
        seed=episode.seed, episode_index=episode.episode_index, split=episode.split,
        difficulty_layer=episode.difficulty_layer, capability_tier=episode.capability_tier,
        validation_status=episode.validation_status, cabinet_id=episode.cabinet_id,
        cabinet_position=list(episode.cabinet_position), target_id=episode.target_id,
        target_color=target.color, target_size=list(target.size), goal_center=list(episode.goal_center),
        goal_size=list(episode.goal_size), board_height=episode.board_height,
        board_bounds_xy=[[surface["center_xy"][i] - surface["size_xy"][i] / 2,
                          surface["center_xy"][i] + surface["size_xy"][i] / 2] for i in range(2)],
        relay_surfaces=[surface], target_shelf_height=episode.target_shelf_height,
        original_target_surface=original_surface,
        support_zone=dict(center_xy=list(episode.support_zone_center), half_size_xy=list(episode.support_zone_half_size)),
        requested_transport_m=episode.requested_transport_m, objects=objects,
        object_ids=list(objects), object_sizes=[list(obj.size) for obj in episode.objects],
        object_present=[True] * len(objects), physics=dict(PHYSICS), physics_dt=PHYSICS_DT,
        control_dt=CONTROL_DT, sim_time_limit_s=episode.episode_length_s,
        foot_collision_geometry=foot_geometry, foot_contact_points_local=foot_points,
        foot_corner_offsets=foot_points["left_ankle_roll_link"],
        robot_initial=dict(position=list(episode.robot_position), quaternion=list(episode.robot_quaternion),
                           joint_positions=dict(episode.robot_joint_positions)),
        admission=dict(accepted=False, randomized_layers_validated=False,
                       reference="full-chain-physical-v15" if episode.profile == "reference_v15" else None),
        sampling=dict(attempts=episode.sampling_attempts, rejected_candidates=list(episode.rejected_candidates),
                      method="named_counter_full_candidate_pool_geometry_rejection",
                      geometric_validation_only=True))
