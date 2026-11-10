"""Compare imported convex contacts with the original Inspire triangle surfaces."""
from pathlib import Path
import json,hashlib
import numpy as np,mujoco,trimesh
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'df_family/runs/DF-02-F-a11';m=mujoco.MjModel.from_xml_path(str(p/'scene.xml'));d=mujoco.MjData(m);z=np.load(p/'trajectory.npz');d.qpos[:]=z['qpos'][-1];d.qvel[:]=z['qvel'][-1];d.ctrl[:]=z['ctrl'][-1];mujoco.mj_forward(m,d)
 source=ROOT.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache/unitree_ros/robots/g1_description/meshes'
 names={'R_hand_base_link':'R_hand_base_link.STL','R_thumb_proximal':'Link12_R.STL'}
 meshes={n:trimesh.load(source/f,force='mesh') for n,f in names.items()};rows=[]
 for i,c in enumerate(d.contact):
  bodies=[m.body(m.geom_bodyid[g]).name for g in c.geom]
  if set(bodies)!=set(names):continue
  distances={}
  for n,mesh in meshes.items():
   b=m.body(n).id;local=d.xmat[b].reshape(3,3).T@(c.pos-d.xpos[b]);_,dist,_=trimesh.proximity.closest_point(mesh,[local]);distances[n]=float(dist[0])
  force=np.zeros(6);mujoco.mj_contactForce(m,d,i,force)
  rows.append(dict(convex_contact_penetration_m=-float(c.dist),force_n=float(np.linalg.norm(force[:3])),distance_to_original_triangle_surface_m=distances,world_point=c.pos.tolist()))
 report={'schema':'collision-surface-audit/1','source_attempt':p.name,'scope':'Sampled offending contacts, not a global collision-free certificate','source_hashes':{f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in names.values()},'contacts':rows,'documentation':'https://mujoco.readthedocs.io/en/stable/computation.html#convex-decomposition'}
 out=ROOT/'df_family/acceptance/inspire-collision-audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
