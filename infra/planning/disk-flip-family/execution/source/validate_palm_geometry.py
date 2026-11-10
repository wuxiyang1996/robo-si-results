from pathlib import Path
import json,numpy as np,mujoco
from .model import build_scene
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'df_family/runs/DF-02-F-a11';old=mujoco.MjModel.from_xml_path(str(p/'scene.xml'))
new,d,binding=build_scene('F','P2',ROOT/'df_family/acceptance/palm-model-probe',collision_profile='inspire-palms-v2')
assert old.nq==new.nq and old.nbody==new.nbody
inertial={n:float(np.max(np.abs(getattr(old,n)-getattr(new,n)))) for n in ['body_mass','body_ipos','body_inertia']}
assert max(inertial.values())<1e-12
z=np.load(p/'trajectory.npz');d.qpos[:]=z['qpos'][-1];d.qvel[:]=z['qvel'][-1];d.ctrl[:]=z['ctrl'][-1];mujoco.mj_forward(new,d)
pairs=[]
for c in d.contact:
 names=[new.body(new.geom_bodyid[g]).name for g in c.geom]
 if set(names)=={'R_hand_base_link','R_thumb_proximal'}:pairs.append({'distance_m':float(c.dist),'position':c.pos.tolist()})
r={'schema':'palm-collision-regression/1','inertial_max_differences':inertial,'original_offending_contacts':3,'decomposed_contacts_at_same_pose':pairs,'collision_pairs_disabled':False,'convex_parts':128,'scope':'Same formerly failing configuration; physical runs must restart and requalify with this geometry version'}
(ROOT/'df_family/acceptance/palm-collision-regression.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
