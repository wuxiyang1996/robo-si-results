"""Single-scene tabletop environment: real contacts, capped joint torques.

The pelvis is bolted to a stand. Objects are never attached to the hands or
repositioned during an episode. This development API exposes ground truth;
it is not an isolated benchmark sandbox.
"""
from pathlib import Path
import hashlib
import math
import xml.etree.ElementTree as ET

import numpy as np
import torch
import genesis as gs

from humanoid.g1_box_stair_transport.robot import JOINT_NAMES, JOINT_LIMITS
from .assets import write_object_urdf

HERE = Path(__file__).resolve().parent
G1_XML = HERE.parent / "g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml"
SIM_DT = 0.005
CONTROL_DT = 0.02
ACTION_SCALE = 0.25


def anchored_robot_xml():
    """Cache an anchored derivative; preserve the upstream robot and license."""
    import os
    import tempfile

    source = G1_XML.read_bytes()
    digest = hashlib.sha256(b"anchor-v2" + source + str(G1_XML).encode()).hexdigest()[:12]
    target = HERE / "assets/generated" / f"g1_anchored_{digest}.xml"
    if target.exists():
        return target
    root = ET.fromstring(source)
    root.find("compiler").set("meshdir", str(G1_XML.parent / "assets"))
    # A fixed MJCF root keeps its authored transform; the morph adds its own.
    # Put the robot origin at zero before placing the stand at base_position.
    root.find("worldbody/body").set("pos", "0 0 0")
    for body in root.iter("body"):
        for joint in list(body):
            if joint.tag == "freejoint":
                body.remove(joint)
    keyframe = root.find("keyframe")
    if keyframe is not None:
        root.remove(keyframe)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            ET.ElementTree(root).write(handle, encoding="utf-8", xml_declaration=True)
        try:
            os.replace(temporary, target)
        except (FileExistsError, PermissionError):
            # Windows may deny replacing a concurrently opened winner's file.
            # Every writer publishes the same immutable asset atomically.
            if not target.is_file():
                raise
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def actuator_parameters():
    """Explicit PD with torque caps read from the actual G1 MJCF actuators."""
    root = ET.parse(G1_XML).getroot()
    limits = {}
    for joint in root.iter("joint"):
        bounds = joint.get("actuatorfrcrange", "").split()
        if len(bounds) == 2:
            limits[joint.attrib["name"]] = max(abs(float(v)) for v in bounds)
    if set(JOINT_NAMES) - limits.keys():
        raise ValueError("G1 XML must supply an effort range for every driven joint")
    kp, kd = [], []
    for name in JOINT_NAMES:
        p, d = (100., 5.)
        if "knee" in name:
            p, d = 160., 6.
        elif "waist" in name:
            p, d = 150., 8.
        elif "wrist" in name:
            p, d = 35., 1.5
        elif "hand" in name:
            p, d = 6., .25
        kp.append(p)
        kd.append(d)
    return kp, kd, [limits[name] for name in JOINT_NAMES]


class G1TabletopGenesis:
    def __init__(self, task="hanoi", cfg=None, backend="cpu", camera=False,
                 show_viewer=False, seed=0):
        if task == "hanoi":
            from humanoid.g1_tabletop_hanoi.task_spec import TaskConfig, Evaluator
        elif task == "assembly":
            from humanoid.g1_tabletop_assembly.task_spec import TaskConfig, Evaluator
        elif task == "disk_flip":
            from humanoid.g1_tabletop_disk_flip.task_spec import TaskConfig, Evaluator
        else:
            raise ValueError("task must be 'hanoi', 'assembly' or 'disk_flip'")
        if backend not in ("cpu", "gpu"):
            raise ValueError("backend must be 'cpu' or 'gpu'")
        self.task, self.cfg = task, cfg or TaskConfig()
        self.evaluator = Evaluator(self.cfg)
        self.sim_dt = getattr(self.cfg, "physics_dt", SIM_DT)
        if not math.isclose(self.cfg.control_dt, CONTROL_DT):
            raise ValueError("this backend requires control_dt=0.02")
        if not gs._initialized:
            gs.init(backend=gs.cpu if backend == "cpu" else gs.gpu,
                    seed=int(seed), logging_level="warning",
                    **({"precision": "64"} if task == "disk_flip" else {}))
        if task == "disk_flip" and gs.np_float != np.float64:
            raise RuntimeError("disk contacts require 64-bit Genesis; use a fresh process")
        self.device = gs.device
        self.num_actions = len(JOINT_NAMES)
        self.base_position = (0., 0., .79)
        eye, lookat = (1.9, -2.1, 1.9), (.3, 0., .8)
        elliptic_contact = task in ("hanoi", "disk_flip") and self.cfg.friction_model == "elliptic"
        rigid_options = gs.options.RigidOptions(
            enable_self_collision=True, enable_neutral_collision=True,
            enable_torsional_friction=(self.cfg.enable_torsional_friction
                                      if task == "hanoi" else False),
            friction_cone=(gs.friction_cone.elliptic if elliptic_contact
                           else gs.friction_cone.pyramidal),
            impratio=100. if elliptic_contact else None,
            use_gjk_collision=(self.cfg.collision_detector == "gjk" if task == "disk_flip" else None),
            max_collision_pairs=1024 if task == "hanoi" else 150)
        # Capture resolved engine defaults, not just task configuration, so a
        # later replay can distinguish a new physical environment version.
        self.physics_metadata = dict(
            scene_step_seconds=self.sim_dt, integration_substeps=1,
            integration_step_seconds=self.sim_dt, evaluator_step_seconds=self.sim_dt,
            control_step_seconds=CONTROL_DT, backend=backend, seed=int(seed),
            precision_bits=np.dtype(gs.np_float).itemsize*8,
            rigid_options={key: value if value is None or isinstance(value, (bool, int, float, str))
                           else str(value)
                           for key, value in rigid_options.model_dump().items()})
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.sim_dt, substeps=1),
            rigid_options=rigid_options,
            viewer_options=gs.options.ViewerOptions(camera_pos=eye, camera_lookat=lookat),
            show_viewer=show_viewer)
        add = self.scene.add_entity
        self.ground = add(gs.morphs.Plane(), material=gs.materials.Rigid(friction=.8),
                          surface=gs.surfaces.Default(color=(.22, .25, .29)))
        c = self.cfg
        self.table = add(gs.morphs.Box(
            size=c.table_size,
            pos=(*c.table_center, c.table_height-c.table_size[2]/2), fixed=True),
            material=gs.materials.Rigid(friction=.7),
            surface=gs.surfaces.Default(color=(.70, .62, .48)))
        for x in (-1, 1):
            for y in (-1, 1):
                add(gs.morphs.Box(size=(.045, .045, c.table_height-c.table_size[2]),
                    pos=(c.table_center[0]+x*(c.table_size[0]/2-.045),
                         c.table_center[1]+y*(c.table_size[1]/2-.045),
                         (c.table_height-c.table_size[2])/2), fixed=True),
                    surface=gs.surfaces.Default(color=(.18, .22, .27)))
        # Visible rear support identifies the fixed-base manipulation setup.
        add(gs.morphs.Box(size=(.08, .10, .72), pos=(-.14, 0., .36), fixed=True),
            surface=gs.surfaces.Default(color=(.30, .32, .35)))
        self.robot = add(gs.morphs.MJCF(
            file=str(anchored_robot_xml()), pos=self.base_position))
        self.objects, self.specs = {}, {}
        for spec in c.scene_objects():
            name, kind = spec["name"], spec["kind"]
            fixed = bool(spec.get("fixed", False))
            if kind == "box":
                morph = gs.morphs.Box(size=spec["size"], pos=spec["pos"], fixed=fixed)
                volume = math.prod(spec["size"])
            elif kind == "cylinder":
                morph = gs.morphs.Cylinder(radius=spec["radius"], height=spec["height"],
                                           pos=spec["pos"], fixed=fixed)
                volume = math.pi*spec["radius"]**2*spec["height"]
            elif kind == "disk":
                from humanoid.g1_tabletop_disk_flip.assets import write_disk_urdf
                asset = write_disk_urdf(spec, HERE / "assets/generated")
                morph = gs.morphs.URDF(file=str(asset), pos=spec["pos"], fixed=False,
                                       convexify=True, decimate=False)
                volume = math.pi*spec["radius"]**2*spec["height"]
            else:
                asset = write_object_urdf(spec, HERE / "assets/generated")
                morph = gs.morphs.URDF(
                    file=str(asset), pos=spec["pos"], fixed=(kind == "tilting_fixture" or fixed),
                    convexify=True, decimate=False, merge_fixed_links=True)
                if kind == "ring":
                    volume = math.pi*(spec["radius"]**2-spec["inner_radius"]**2)*spec["height"]
                elif kind == "square_ring":
                    volume = (math.prod(spec["outer_size"])-math.prod(spec["inner_size"]))*spec["height"]
                else:
                    volume = math.prod(spec["size"])+math.prod(spec["post_size"])
            self.objects[name] = add(
                morph, material=gs.materials.Rigid(
                    rho=float(spec.get("mass", 1.2 if kind == "tilting_fixture" else .2))/volume,
                    **({"friction_torsional": .005} if task == "hanoi" and kind == "ring" else {}),
                    friction=float(spec.get("friction", .7))),
                surface=gs.surfaces.Default(**({} if kind == "disk" else
                                             {"color": tuple(spec["color"])})))
            self.specs[name] = spec
        self.cam = self.scene.add_camera(res=(1280, 900), pos=eye, lookat=lookat,
                                          fov=43, GUI=False) if camera else None
        self.scene.build()
        self.dofs = [self.robot.get_joint(n).dofs_idx_local[0] for n in JOINT_NAMES]
        self.robot_ids = {link.idx for link in self.robot.links}
        self.robot_link_names = {link.idx: link.name for link in self.robot.links}
        self.hand_ids = {link.idx for link in self.robot.links
                         if "hand" in link.name or "wrist_yaw_link" in link.name}
        self.hand_sides = {link.idx: side for side in ("left", "right")
                           for link in self.robot.links
                           if link.idx in self.hand_ids and link.name.startswith(side+"_")}
        self.link_owners = {link.idx: name for name, entity in self.objects.items()
                            for link in entity.links}
        self.link_owners.update({link.idx: "table" for link in self.table.links})
        self.link_owners.update({link.idx: "ground" for link in self.ground.links})
        self.measure_links = {
            name: (entity.get_link("fixture_plate") if self.specs[name]["kind"] == "tilting_fixture"
                   else entity.links[0]) for name, entity in self.objects.items()}
        self.fixture_ids = {
            link.idx for name, entity in self.objects.items()
            if self.specs[name]["kind"] == "tilting_fixture"
            for link in entity.links if link.name == "fixture_plate"}
        kp, kd, effort = actuator_parameters()
        if task == "disk_flip":
            kp = [value*self.cfg.arm_stiffness_scale
                  if any(part in name for part in ("shoulder", "elbow", "wrist", "hand"))
                  else value for name, value in zip(JOINT_NAMES, kp)]
            # Retain damping and physical effort bounds while softening contact.
            self.physics_metadata["arm_stiffness_scale"] = self.cfg.arm_stiffness_scale
        tensor = lambda value: torch.tensor(value, dtype=torch.float32, device=self.device)
        self.kp, self.kd, self.effort = map(tensor, (kp, kd, effort))
        self.lo, self.hi = tensor(JOINT_LIMITS).unbind(-1)
        self.default_q = torch.zeros(self.num_actions, device=self.device)
        posture = dict(left_hip_pitch_joint=-.10, right_hip_pitch_joint=-.10,
                       left_knee_joint=.30, right_knee_joint=.30,
                       left_ankle_pitch_joint=-.20, right_ankle_pitch_joint=-.20,
                       left_shoulder_pitch_joint=.25, right_shoulder_pitch_joint=.25,
                       left_shoulder_roll_joint=.20, right_shoulder_roll_joint=-.20,
                       left_elbow_joint=.80, right_elbow_joint=.80)
        if self.task == "disk_flip":
            # Begin with separated, raised hands. The shared low-hand posture
            # puts open thumbs against the hips before the first policy step.
            posture.update(left_shoulder_pitch_joint=-1.1, right_shoulder_pitch_joint=-1.1,
                           left_shoulder_roll_joint=.4, right_shoulder_roll_joint=-.4)
        for name, value in posture.items():
            self.default_q[JOINT_NAMES.index(name)] = value
        self.robot.set_dofs_kp(torch.zeros(self.num_actions), self.dofs)
        self.robot.set_dofs_kv(torch.zeros(self.num_actions), self.dofs)
        self.robot.set_dofs_force_range(-self.effort.cpu(), self.effort.cpu(), self.dofs)
        self.robot.set_dofs_armature(torch.full((self.num_actions,), .02), self.dofs)
        self.reset()

    @staticmethod
    def _array(value):
        return value.detach().cpu().numpy()

    def reset(self):
        self.scene.reset()
        self.robot.set_dofs_position(self.default_q, self.dofs, zero_velocity=True)
        actual_base = self._array(self.robot.get_link("pelvis").get_pos())
        if not np.allclose(actual_base, self.base_position, atol=1e-5):
            raise RuntimeError(f"unexpected anchored pelvis position: {actual_base}")
        for name, spec in self.specs.items():
            if spec["kind"] == "tilting_fixture":
                ent = self.objects[name]
                joint = ent.get_joint("fixture_hinge").dofs_idx_local
                ent.set_dofs_position([spec.get("initial_pitch", .28)], joint, zero_velocity=True)
                ent.set_dofs_kp([0.], joint)
                ent.set_dofs_kv([0.], joint)
                ent.set_dofs_damping([.06], joint)
        self.target = self.default_q.clone()
        self.previous_action = torch.zeros_like(self.target)
        self.physics_steps = 0
        self.max_applied_torque = torch.zeros_like(self.target)
        self.evaluator.reset()
        self.status = dict(success=False, failed=False, terminated=False, score=0.,
                           reason="", progress=0.)
        return self.observe()

    def state(self):
        result = {}
        names = getattr(self.cfg, "measurement_names", self.cfg.object_names)
        for name in names:
            entity = self.objects[name]
            link = self.measure_links[name]
            own_ids = {link.idx} if self.specs[name]["kind"] == "tilting_fixture" else {
                item.idx for item in entity.links}
            support_force, robot_force, hand_force, fixture_force, fixture_load = 0., 0., 0., 0., 0.
            support_forces = {}
            hand_forces = {side: np.zeros(3) for side in ("left", "right")}
            hand_magnitudes = {side: 0. for side in hand_forces}
            hand_positions = {side: np.zeros(3) for side in hand_forces}
            hand_contacts = {side: [] for side in hand_forces}
            contact_forces = {}
            contacts = entity.get_contacts()
            a, b = self._array(contacts["link_a"]), self._array(contacts["link_b"])
            fa, fb = self._array(contacts["force_a"]), self._array(contacts["force_b"])
            positions = self._array(contacts["position"]) if self.task == "disk_flip" else None
            for index in range(len(a)):
                if int(a[index]) in own_ids:
                    other, force = int(b[index]), fa[index]
                elif int(b[index]) in own_ids:
                    other, force = int(a[index]), fb[index]
                else:
                    continue
                magnitude = float(np.linalg.norm(force))
                if other in self.robot_ids:
                    robot_force += magnitude
                    if other in self.hand_ids:
                        hand_force += magnitude
                        if positions is not None:
                            side = self.hand_sides[other]
                            hand_forces[side] += force
                            hand_magnitudes[side] += magnitude
                            hand_positions[side] += magnitude * positions[index]
                            hand_contacts[side].append(dict(position=positions[index].tolist(),
                                                           force_n=force.tolist(),
                                                           robot_link=self.robot_link_names[other]))
                elif other not in own_ids:
                    owner = self.link_owners.get(other, "other")
                    support_forces[owner] = support_forces.get(owner, 0.) + float(force[2])
                    contact_forces[owner] = contact_forces.get(owner, 0.) + magnitude
                if other in self.fixture_ids and other not in own_ids:
                    fixture_force += magnitude
                    fixture_load -= float(force[2])
            support_forces = {owner: max(0., force) for owner, force in support_forces.items()}
            support_force = sum(support_forces.values())
            result[name] = dict(
                pos=self._array(link.get_pos()).tolist(),
                quat=self._array(link.get_quat()).tolist(),
                linear_velocity=self._array(link.get_vel()).tolist(),
                angular_velocity=self._array(link.get_ang()).tolist(),
                hand_contact=bool(hand_force > .05), robot_contact=bool(robot_force > .05),
                support_contact=bool(support_force > .05), support_forces=support_forces,
                fixture_contact=bool(fixture_force > .05), support_force_n=support_force,
                robot_contact_force_n=robot_force, fixture_contact_force_n=fixture_force,
                fixture_load_n=max(0., fixture_load))
            if self.task == "disk_flip":
                result[name].update(
                    hand_forces_n={s: f.tolist() for s, f in hand_forces.items()},
                    hand_force_magnitudes_n=hand_magnitudes,
                    hand_contacts=hand_contacts,
                    hand_contact_positions={s: (hand_positions[s]/hand_magnitudes[s]).tolist()
                                            if hand_magnitudes[s] > .05 else None
                                            for s in hand_forces},
                    contact_forces_n=contact_forces)
        return result

    def observe(self):
        return dict(joint_names=list(JOINT_NAMES),
                    joint_position=self._array(self.robot.get_dofs_position(self.dofs)).tolist(),
                    joint_velocity=self._array(self.robot.get_dofs_velocity(self.dofs)).tolist(),
                    objects=self.state(), time=self.physics_steps*self.sim_dt,
                    observation_mode="privileged_development")

    def step_targets(self, target):
        """43 absolute joint angles in radians; finite and in-range, with no pose API."""
        target = torch.as_tensor(target, dtype=torch.float32, device=self.device)
        if target.shape != (self.num_actions,) or not torch.isfinite(target).all():
            raise ValueError(f"target must contain {self.num_actions} finite joint angles")
        if ((target < self.lo) | (target > self.hi)).any():
            raise ValueError("joint target outside G1 joint limits")
        if self.status["terminated"]:
            raise RuntimeError("episode terminated; call reset()")
        if self.task == "disk_flip":
            # Bound every action channel, including absolute target replay.
            delta = self.cfg.joint_target_speed_max * CONTROL_DT
            target = self.target + torch.clamp(target-self.target, -delta, delta)
        self.target = target.clone()
        for _ in range(round(CONTROL_DT/self.sim_dt)):
            q = self.robot.get_dofs_position(self.dofs)
            qd = self.robot.get_dofs_velocity(self.dofs)
            torque = torch.clamp(self.kp*(self.target-q)-self.kd*qd,
                                 min=-self.effort, max=self.effort)
            self.max_applied_torque = torch.maximum(self.max_applied_torque, torque.abs())
            self.robot.control_dofs_force(torque, self.dofs)
            self.scene.step()
            self.physics_steps += 1
            self.status = self.evaluator.update(self.state(), self.sim_dt)
            if self.status["terminated"]:
                break
        action = (target-self.default_q)/ACTION_SCALE
        reward = (float(self.status["success"])-float(self.status["failed"])
                  - .001*float(torch.mean((action-self.previous_action)**2)))
        self.previous_action = action.clone()
        return self.observe(), reward, self.status["terminated"], dict(self.status)

    def step(self, action):
        """Normalized offsets: q_target = default_q + 0.25 * action."""
        action = torch.as_tensor(action, dtype=torch.float32, device=self.device)
        if action.shape != (self.num_actions,) or not torch.isfinite(action).all():
            raise ValueError(f"action must contain {self.num_actions} finite values")
        return self.step_targets(torch.clamp(self.default_q+ACTION_SCALE*action,
                                            min=self.lo, max=self.hi))

    def render(self):
        if self.cam is None:
            raise RuntimeError("construct with camera=True to render")
        return self.cam.render()[0]

    def close(self):
        self.scene.destroy()
