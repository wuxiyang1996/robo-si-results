"""Canonical measured P4 channels for the unchanged original five safety rules."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from .. import task_spec as T
from ..genesis_env import G1_XML
from ..sandbox.trusted.statelog import RelayStateLogger, FOOT_LINKS, _np, world_params


class P4SafetyRecorder:
    def __init__(self, env, out, actuator):
        self.env, self.out, self.rows = env, Path(out), []
        r = env.robot
        # Reuse the trusted per-contact identity/magnitude classifier unchanged.
        c = self.contacts = RelayStateLogger.__new__(RelayStateLogger)
        c.env = env
        c.objects = list(env.floor_boxes) + list(env.top_boxes)
        c.surfaces = []
        c.surface_geom_ids = {}
        c.robot_links = {x.idx for x in r.links}
        c.hand_of = {x.idx: 0 if x.name.startswith('left_') else 1 for x in r.links
                     if x.name.startswith(('left_', 'right_')) and ('hand' in x.name or 'wrist' in x.name)}
        c.foot_of = {r.get_link(name).idx: i for i, name in enumerate(FOOT_LINKS)}
        c.object_of = {x.idx: i for i, obj in enumerate(c.objects) for x in obj.links}
        c.ground_links = {x.idx for x in env.scene.entities[0].links}
        c.cabinet_links = {x.idx for pair in env.cabinets for obj in pair for x in obj.links}
        self.feet = [r.get_link(name).idx_local for name in FOOT_LINKS]
        xml = ET.parse(G1_XML).getroot()
        default = xml.find(".//default[@class='foot']/geom")
        if default.get('type') != 'sphere':
            raise ValueError('exact foot-bottom recorder requires frozen spherical foot colliders')
        geometry = {}
        for name in FOOT_LINKS:
            geoms = xml.find(f".//body[@name='{name}']").findall("geom[@class='foot']")
            geometry[name] = [dict(center=list(map(float,g.get('pos').split())), radius=float(g.get('size',default.get('size')))) for g in geoms]
            if len(geometry[name]) != 4: raise ValueError('expected four physical foot spheres')
        self.geometry = geometry
        present = _np(env.core.floor_present)[0].astype(bool).tolist() + _np(env.core.top_present)[0].astype(bool).tolist()
        present[0] = True  # The scene runner explicitly placed floor_boxes[0] as P4 target.
        masses = world_params(env)['links_mass']
        mass = float(masses[[x.idx for x in r.links]].sum())
        self.meta = dict(schema='h1-p4-canonical-safety/1', control_dt=T.CONTROL_DT,
            object_ids=[f'floor_{i}' for i in range(len(env.floor_boxes))]+[f'top_{i}' for i in range(len(env.top_boxes))],
            object_present=[True]*len(c.objects), episode_object_present=present,
            physical_presence_reason="All instantiated movable entities remain collision-enabled, including parked objects; original rule 2 covers each of them.",
            torque_channel_semantics="Genesis current-state clipped PD/force evaluated by get_dofs_control_force, identical to trusted logger; not an independent mechanical torque sensor or a claim about the previous substep impulse.",
            object_sizes_m=[list(x) for x in (*T.FLOOR_SIZES,*T.TOP_SIZES)], target_index=0,
            joint_names=list(T.JOINT_NAMES),joint_lower=actuator.lower.tolist(),joint_upper=actuator.upper.tolist(),
            joint_effort_limits=actuator.effort.tolist(),robot_mass_kg=mass,
            foot_collision_geometry=geometry, foot_geometry_source=str(G1_XML),
            foot_geometry_source_sha256=hashlib.sha256(Path(G1_XML).read_bytes()).hexdigest(),
            torque_provenance=dict(quantity='signed_actual_joint_force',source='robot.get_dofs_control_force',sampling='same_state_time_as_q'),
            contact_mapping=dict(robot_links={str(x.idx):x.name for x in r.links},hand_of=c.hand_of,foot_of=c.foot_of,
                object_of=c.object_of,ground_links=sorted(c.ground_links),cabinet_links=sorted(c.cabinet_links),
                semantics='RelayStateLogger._relay_contacts: sum each contact magnitude for body/hand/cabinet, signed upward force on robot for feet; zero means query had no matching contacts. All movable objects including parked entities recorded.',
                classifier_source_sha256=hashlib.sha256(Path(__import__('inspect').getfile(RelayStateLogger)).read_bytes()).hexdigest()))
        (self.out/'safety_meta.json').write_text(json.dumps(self.meta,indent=2)+'\n')

    def record(self,t):
        r=self.env.robot
        lp,lq=_np(r.get_links_pos())[0],_np(r.get_links_quat())[0]
        bottom=[]
        for i,name in enumerate(FOOT_LINKS):
            centers=np.array([g['center'] for g in self.geometry[name]])
            radii=np.array([g['radius'] for g in self.geometry[name]])
            transformed=Rotation.from_quat(lq[self.feet[i]][[1,2,3,0]]).apply(centers)+lp[self.feet[i]]
            bottom.append(float((transformed[:,2]-radii).min()))
        row=dict(t=float(t),root_pos=_np(r.get_pos())[0],root_quat=_np(r.get_quat())[0],
            root_vel=_np(r.get_vel())[0],root_angvel=_np(r.get_ang())[0],foot_bottom_m=np.array(bottom),
            object_pos=np.stack([_np(o.get_pos())[0] for o in self.contacts.objects]),
            object_quat=np.stack([_np(o.get_quat())[0] for o in self.contacts.objects]),
            q=_np(r.get_dofs_position(self.env.dofs))[0],tau=_np(r.get_dofs_control_force(self.env.dofs))[0])
        row.update(self.contacts._relay_contacts())
        row['invalid_mask']=int(any(not np.isfinite(value).all() for value in row.values()))
        self.rows.append(row)

    def finish(self,command_count):
        self.rows=self.rows[:command_count]
        self.record(command_count*T.CONTROL_DT)
        np.savez_compressed(self.out/'safety_trace.npz',**{key:np.array([r[key] for r in self.rows]) for key in self.rows[0]})
