"""Preserve palm concavities instead of replacing a thumb socket with one convex hull."""
from pathlib import Path
import hashlib,json,time
import numpy as np,trimesh,coacd
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=ROOT.parent/'robo-si-local-tests/h1-implementation-20261027/asset-cache/unitree_ros/robots/g1_description/meshes'
 out=ROOT/'df_family/assets/inspire-palms-v2';out.mkdir(exist_ok=True)
 manifest={'schema':'inspire-palm-collision/2','threshold_m':.001,'max_convex_hull':64,'real_metric':True,'seed':0,'mass_and_inertia':'Unchanged official URDF inertials','pairs_disabled':[],'parts':{}}
 for side in ['L','R']:
  name=side+'_hand_base_link';path=source/(name+'.STL');mesh=trimesh.load(path,force='mesh');start=time.monotonic()
  parts=coacd.run_coacd(coacd.Mesh(np.asarray(mesh.vertices),np.asarray(mesh.faces)),threshold=.001,max_convex_hull=64,real_metric=True,preprocess_mode='auto',resolution=5000,mcts_iterations=100,mcts_nodes=20,mcts_max_depth=3,seed=0)
  paths=[]
  for i,(v,f) in enumerate(parts):
   dest=out/f'{name}-{i:02}.obj';trimesh.Trimesh(v,f,process=False).export(dest);paths.append({'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
  manifest['parts'][name]={'original_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_volume_m3':abs(float(mesh.volume)),'single_hull_volume_m3':float(mesh.convex_hull.volume),'parts_volume_sum_m3':sum(abs(float(trimesh.Trimesh(v,f).volume)) for v,f in parts),'files':paths,'seconds':time.monotonic()-start}
  print(json.dumps({'name':name,'parts':len(parts),'seconds':time.monotonic()-start}),flush=True)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
