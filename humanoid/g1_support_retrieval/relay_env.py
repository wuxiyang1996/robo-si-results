"""Genesis scene for the H1 stool-relay variant; no controller or oracle import.

Pose writes occur only in reset.  Runtime actions never auto-reset the scene.
The original five-family environment and its object arrays remain unchanged.
"""

from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

import genesis as gs
import numpy as np
import torch

from . import task_spec as T
from .cabinets import collider_mjcf
from .genesis_env import G1SupportRetrievalGenesis, G1_XML
from .relay_spec import (CABINET_ID, CONTROL_DT, EXTRA_SIZES, PHYSICS, PHYSICS_DT,
                         RelayConfig, RelayObject, build_relay_metadata, sample_episode)


def _np(value):
    return value.detach().cpu().numpy() if hasattr(value, "detach") else np.asarray(value)


def _geom_ids(entity):
    return [int(geom.idx) for geom in entity.geoms]


def _bind_surfaces(env):
    """Expose actual collider IDs, not the cabinet's merged link identity."""
    meta = env.relay_metadata
    cabinet_index = T.CABINET_VARIANTS.index(meta["cabinet_id"])
    cabinet = env.cabinets[cabinet_index][1]
    geometry = _geom_ids(cabinet)
    expected = T.CABINET_META[meta["cabinet_id"]]["colliders"]
    if len(geometry) != len(expected):
        raise ValueError("cabinet collider count changed; cannot safely identify the relay board")
    env.relay_cabinet_geom_ids = geometry
    env.relay_surface_geom_ids = {
        surface["id"]: [geometry[index] for index in surface["collider_indices"]]
        for surface in meta["relay_surfaces"]
    }
    env.relay_cabinet_surfaces = {surface["id"]: cabinet for surface in meta["relay_surfaces"]}
    ground = getattr(env, "relay_ground", None)
    if ground is None:
        # The unchanged reference environment adds its Plane before any entity.
        ground = env.scene.entities[0]
    env.relay_ground = ground
    env.relay_floor_geom_ids = _geom_ids(ground)


class RelayEnv(G1SupportRetrievalGenesis):
    def __init__(self, num_envs=1, *, relay_config=None, seed=0, sensors=None,
                 camera=True, show_viewer=False):
        if num_envs != 1:
            raise ValueError("stool_relay currently supports one sealed scene per worker")
        if T.SIM_DT != PHYSICS_DT or T.CONTROL_DT != CONTROL_DT or T.DECIMATION != 4:
            raise ValueError("base timing no longer matches the frozen stool-relay physics contract")
        self.relay_config = (RelayConfig() if relay_config is None else
                             RelayConfig(**relay_config) if isinstance(relay_config, dict) else relay_config)
        if not isinstance(self.relay_config, RelayConfig):
            raise TypeError("relay_config must be RelayConfig or a matching dictionary")
        self.relay_seed = seed
        self._relay_episode_index = -1
        self._relay_sensors = sensors
        self._relay_done = False
        # All layers share one physical topology. Reset can park/unpark extras
        # without rebuilding cameras or changing solver dimensions.
        self.relay_episode = sample_episode(seed, 0, self.relay_config)
        cfg = T.TaskConfig(episode_length_s=self.relay_config.episode_length_s,
            family_weights=(0., 1., 0., 0., 0.), floor_boxes=False,
            strength_range=(1., 1.), payload_range=(0., 0.), start_jitter_xy=0., start_jitter_yaw=0.)
        super().__init__(1, cfg=cfg, seed=seed, camera=camera, show_viewer=show_viewer, **PHYSICS)

    def _build(self, show_viewer, camera):
        # Deliberately explicit construction: no process-global Scene monkey patch.
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=PHYSICS_DT, substeps=1),
            rigid_options=gs.options.RigidOptions(enable_self_collision=False,
                enable_torsional_friction=False, noslip_iterations=0,
                friction_cone=gs.friction_cone.pyramidal, batch_dofs_info=True, batch_links_info=True),
            vis_options=gs.options.VisOptions(rendered_envs_idx=[0]),
            viewer_options=gs.options.ViewerOptions(camera_pos=(-1., -3.5, 3.), camera_lookat=(2., 0., .8)),
            show_viewer=show_viewer)
        def add(name, morph, **kwargs):
            return self.scene.add_entity(morph, name="relay_" + name, **kwargs)
        rigid = lambda friction: gs.materials.Rigid(friction=friction)
        color = lambda rgb: gs.surfaces.Default(color=tuple(rgb))
        self.relay_ground = add("ground", gs.morphs.Plane(), material=rigid(.1))
        (x0, x1), (y0, y1), thickness, height = T.ROOM_X, T.ROOM_Y, T.WALL_THICKNESS, T.WALL_HEIGHT
        walls = (((thickness, y1-y0+2*thickness, height), (x0-thickness/2, 0., height/2)),
                 ((thickness, y1-y0+2*thickness, height), (x1+thickness/2, 0., height/2)),
                 ((x1-x0, thickness, height), ((x0+x1)/2, y0-thickness/2, height/2)),
                 ((x1-x0, thickness, height), ((x0+x1)/2, y1+thickness/2, height/2)))
        for index, (size, pos) in enumerate(walls):
            add(f"wall_{index}", gs.morphs.Box(size=size, pos=pos, fixed=True),
                material=rigid(.5), surface=color((.85, .85, .82)))
        self.cabinets = []
        for index, variant in enumerate(T.CABINET_VARIANTS):
            pos = (T.CABINET_X_FRONT, 0., T.CABINET_PARK_Z - 5.*index)
            visual = add(f"cabinet_{index}_visual", gs.morphs.Mesh(
                file=str(T.CABINET_DIR / variant / "visual.obj"), pos=pos, fixed=True,
                collision=False, batch_fixed_verts=True))
            collision = add(f"cabinet_{index}_collision", gs.morphs.MJCF(
                file=str(collider_mjcf(variant)), pos=pos, visualization=False, batch_fixed_verts=True))
            self.cabinets.append((visual, collision))
        add("goal", gs.morphs.Box(size=(*T.GOAL_SIZE, .002), pos=(*T.GOAL_CENTER, .001),
                                  fixed=True, collision=False), surface=color((.2, .8, .3)))
        self.top_boxes = [add(f"top_{i}", gs.morphs.Box(size=size, pos=(-3., -1.+.5*i, size[2]/2)),
            material=rigid(.5), surface=color(rgb)) for i, (size, rgb) in enumerate(zip(T.TOP_SIZES, T.TOP_COLORS))]
        self.floor_boxes = [add(f"floor_{i}", gs.morphs.Box(size=size, pos=(-4., -1.+.8*i, size[2]/2)),
            material=rigid(.5), surface=color(rgb)) for i, (size, rgb) in enumerate(zip(T.FLOOR_SIZES, T.FLOOR_COLORS))]
        stool_asset = Path(__file__).parent / "assets/stools/folding_stool/stool.urdf"
        self.stool = add("stool", gs.morphs.URDF(file=str(stool_asset), pos=(-4., 2.5, .11049)), material=rigid(.5))
        self._relay_extras = {}
        for index, (name, size) in enumerate(EXTRA_SIZES.items()):
            self._relay_extras[name] = add(name, gs.morphs.Box(size=size, pos=(-6.-index, 0., size[2]/2),
                fixed=name == "fixed_block", batch_fixed_verts=True), material=rigid(.5), surface=color((.55, .45, .34)))
        self.robot = add("robot", gs.morphs.MJCF(file=str(G1_XML), pos=(*T.ROBOT_START, T.ROBOT_BASE_HEIGHT)))
        self.cam = self.scene.add_camera(res=(1280, 720), pos=(-.8, -2.9, 2.9),
            lookat=(2.5, 0., 1.05), fov=36, GUI=False) if camera else None
        if self._relay_sensors is not None:
            self._relay_sensors.add_cameras(self.scene)
        self.scene.build(n_envs=1, env_spacing=(8., 8.))

    def _init_buffers(self):
        super()._init_buffers()
        # Base task specifies generous arm/hand effort values; this variant uses
        # the unchanged hardware MJCF ratings, as the physical reference did.
        ratings = {joint.get("name"): float(joint.get("actuatorfrcrange").split()[1])
                   for joint in ET.parse(G1_XML).getroot().iter("joint") if joint.get("actuatorfrcrange")}
        physical = torch.tensor([min(float(self.p["effort"][i]), ratings.get(name, float(self.p["effort"][i])))
                                 for i, name in enumerate(T.JOINT_NAMES)], device=self.device)
        self.p["effort"] = physical
        self.effort[:] = physical
        self.robot.set_dofs_force_range(-physical, physical, self.dofs)

    def reset(self, env_ids=None, *, relay_config=None, seed=None, episode_index=None):
        if env_ids is not None:
            ids = np.asarray(_np(env_ids)).reshape(-1)
            if len(ids) == 0:
                return self.obs
            if ids.tolist() != [0]:
                raise ValueError("RelayEnv only has environment 0")
        config = self.relay_config if relay_config is None else (
            RelayConfig(**relay_config) if isinstance(relay_config, dict) else relay_config)
        next_seed = self.relay_seed if seed is None else seed
        index = self._relay_episode_index + 1 if episode_index is None else episode_index
        episode = sample_episode(next_seed, index, config)  # validate before any state mutation
        self.relay_config, self.relay_seed, self._relay_episode_index = config, next_seed, index
        self.relay_episode = episode
        dev, core = self.device, self.core
        tensor = lambda values: torch.as_tensor(values, dtype=torch.float32, device=dev)[None]
        ids = torch.tensor([0], device=dev, dtype=torch.long)
        core.cfg = replace(core.cfg, episode_length_s=config.episode_length_s)
        core.max_steps = int(round(config.episode_length_s / CONTROL_DT))
        self.max_episode_length = core.max_steps
        # Initialize all legacy core buffers and parked objects from the same
        # original seed-2 TaskCore sample, then apply this variant's generator.
        # Reference objects therefore retain the exact original float32 masses.
        core.seed = 2
        core.episode_index[:] = 0
        super().reset(ids)
        for i, parts in enumerate(self.cabinets):
            pos = episode.cabinet_position if T.CABINET_VARIANTS[i] == episode.cabinet_id else (3.3, 0., -20.)
            for entity in parts:
                entity.set_pos(tensor(pos), envs_idx=ids)
        if config.profile != "reference_v15":
            for i, entity in enumerate(self.top_boxes):
                entity.set_pos(tensor((-3., -.9 + .6*i, T.TOP_SIZES[i][2]/2)), envs_idx=ids, zero_velocity=True)
        for i, entity in enumerate(self._relay_extras.values()):
            entity.set_pos(tensor((-6.-i, 0., .3)), envs_idx=ids, zero_velocity=True)
        self.relay_entities = {}
        core.top_present[:] = False
        core.floor_present[:] = False
        for obj in episode.objects:
            entity = (self.stool if obj.id == "stool" else self.top_boxes[obj.top_index]
                      if obj.top_index is not None else self._relay_extras[obj.id])
            entity.set_pos(tensor(obj.position), envs_idx=ids, zero_velocity=True)
            entity.set_quat(tensor(obj.quaternion), envs_idx=ids, zero_velocity=True)
            if not obj.fixed:
                entity.set_mass(torch.tensor([obj.mass], device=dev), envs_idx=ids)
            entity.set_friction_ratio(torch.tensor([[obj.friction/.5]], device=dev), envs_idx=ids)
            self.relay_entities[obj.id] = entity
            if obj.top_index is not None:
                core.top_present[0, obj.top_index] = True
        target = next(obj for obj in episode.objects if obj.id == episode.target_id)
        core.target[0] = target.top_index
        core.cabinet[0] = T.CABINET_VARIANTS.index(episode.cabinet_id)
        core.levels[0] = core.cab_levels[core.cabinet[0]]
        core.shelf_height[0] = episode.target_shelf_height
        core.target_start_z[0] = target.position[2]
        core.tier[0] = T.TIERS.index(config.capability_tier)
        core.goal[:] = torch.as_tensor(episode.goal_center, dtype=torch.float32, device=dev)
        q = tensor([episode.robot_joint_positions[name] for name in T.JOINT_NAMES])
        self.robot.set_pos(tensor(episode.robot_position), envs_idx=ids, zero_velocity=True)
        self.robot.set_quat(tensor(episode.robot_quaternion), envs_idx=ids, zero_velocity=True)
        self.robot.set_dofs_position(q, self.dofs, envs_idx=ids, zero_velocity=True)
        self.target[:] = q
        self.relay_metadata = build_relay_metadata(episode)
        _bind_surfaces(self)
        self._relay_done = False
        self.obs[:] = core.observe(self.state())
        return self.obs

    def step(self, actions):
        """Legacy position-action convenience API; success belongs to the trusted verifier.

        The sandbox uses its LowCmd executor instead. Neither path uses the old
        center-in-goal condition to reset or end a relay episode prematurely.
        """
        if self._relay_done:
            raise RuntimeError("relay episode is over; terminal state is preserved until explicit reset")
        actions = torch.as_tensor(actions, device=self.device, dtype=torch.float32)
        if tuple(actions.shape) != (1, T.ACTION_DIM) or not bool(torch.isfinite(actions).all()):
            raise ValueError(f"expected finite actions of shape (1, {T.ACTION_DIM})")
        actions = actions.clamp(-T.ACTION_CLIP, T.ACTION_CLIP)
        target = (self.default_q + T.ACTION_SCALE * actions[:, :T.NUM_JOINTS]).clamp(self.q_lo, self.q_hi)
        self.apply_targets(target)
        state = self.state()
        reward, _, _, info = self.core.step(state, actions)
        reference_fall = getattr(self, '_reference_fall_state', None)
        if reference_fall is not None:
            # Sealed native reference: exact recorded control rows, using the
            # same supported-lean semantics as the LowCmd sandbox and scorer.
            fallen = torch.tensor([reference_fall()], device=self.device, dtype=torch.bool)
        else:
            pelvis_up = 1. - 2. * (state.root_quat[:, 1].square() + state.root_quat[:, 2].square())
            fallen = (state.root_pos[:, 2] < self.core.cfg.fall_height) | (pelvis_up < self.core.cfg.fall_tilt_cos)
        timeout = self.core.step_count >= self.core.max_steps
        done = fallen | info["declared"] | timeout
        info["preliminary_goal"] = info.pop("success")
        info["success"] = torch.zeros_like(done)
        info["fallen"] = fallen
        self.obs[:] = self.core.observe(state)
        self._relay_done = bool(done[0])
        return self.obs, reward, done, {**info, "time_outs": timeout, "task_variant": "stool_relay"}


def metadata_for_reference(env):
    """Bind an already initialized oracle scene for trusted recording, with no pose writes.

    This is a separate engineering profile. It does not reclassify its extra
    green shelf box as a necessary layer-1 object or claim randomized admission.
    """
    if getattr(getattr(env, "relay_config", None), "profile", None) == "layer1_high_fixed":
        episode = env.relay_episode
        objects = tuple(replace(obj,
            position=tuple(map(float, _np(env.relay_entities[obj.id].get_pos())[0])),
            quaternion=tuple(map(float, _np(env.relay_entities[obj.id].get_quat())[0])),
            mass=float(_np(env.relay_entities[obj.id].get_links_mass()).sum())) for obj in episode.objects)
        episode = replace(episode, objects=objects,
            robot_position=tuple(map(float, _np(env.robot.get_pos())[0])),
            robot_quaternion=tuple(map(float, _np(env.robot.get_quat())[0])),
            robot_joint_positions=dict(zip(T.JOINT_NAMES, map(float, _np(env.robot.get_dofs_position(env.dofs))[0]))))
        env.relay_metadata = build_relay_metadata(episode)
        env.relay_metadata["reference_binding"] = "actual_initial_state_read_only"
        _bind_surfaces(env)
        return env.relay_metadata
    if not hasattr(env, "stool"):
        raise ValueError("reference environment has no physical stool")
    for key, expected in PHYSICS.items():
        if getattr(env, key, None) != expected:
            raise ValueError(f"reference_v15 requires {key}={expected!r}")
    if int(env.core.seed) != 2:
        raise ValueError("reference_v15 requires original TaskCore seed 2")
    episode = sample_episode(2, 0, RelayConfig(profile="reference_v15"))
    cabinet = T.CABINET_VARIANTS[int(env.core.cabinet[0])]
    if cabinet != CABINET_ID:
        raise ValueError("reference_v15 requires its actual steel-frame mid cabinet")
    target_index = int(env.core.target[0])
    if target_index != 0:
        raise ValueError("reference_v15 requires its original red target")
    spec = {obj.id: obj for obj in episode.objects}
    entities, objects = {"stool": env.stool}, []
    def actual(obj, entity):
        return replace(obj, position=tuple(map(float, _np(entity.get_pos())[0])),
                       quaternion=tuple(map(float, _np(entity.get_quat())[0])),
                       mass=float(_np(entity.get_links_mass()).sum()))
    objects.append(actual(spec["stool"], env.stool))
    for group, boxes, sizes in (("top", env.top_boxes, T.TOP_SIZES), ("floor", env.floor_boxes, T.FLOOR_SIZES)):
        for index, entity in enumerate(boxes):
            position = _np(entity.get_pos())[0]
            if not (T.ROOM_X[0] <= position[0] <= T.ROOM_X[1] and T.ROOM_Y[0] <= position[1] <= T.ROOM_Y[1]):
                continue
            name = "target" if group == "top" and index == target_index else f"{group}_distractor_{index}"
            color = T.TOP_COLOR_NAMES[index] if group == "top" else "neutral"
            obj = RelayObject(name, "target" if name == "target" else "shelf_box" if group == "top" else "floor_object",
                              tuple(sizes[index]), tuple(position), color=color,
                              top_index=index if group == "top" else None, validation_status="engineering_reference")
            entities[name] = entity
            objects.append(actual(obj, entity))
    if "target" not in entities:
        raise ValueError("the actual reference target is not in the room")
    robot = env.robot
    episode = replace(episode, objects=tuple(objects),
        robot_position=tuple(map(float, _np(robot.get_pos())[0])),
        robot_quaternion=tuple(map(float, _np(robot.get_quat())[0])),
        robot_joint_positions=dict(zip(T.JOINT_NAMES, map(float, _np(robot.get_dofs_position(env.dofs))[0]))))
    env.relay_episode, env.relay_entities = episode, entities
    env.relay_metadata = build_relay_metadata(episode)
    env.relay_metadata["reference_binding"] = "actual_initial_state_read_only"
    _bind_surfaces(env)
    return env.relay_metadata
