"""Static support probes and a dimensioned cross section; not a flip witness."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,mujoco
from .model import add_plate

def main():
 out=Path('df_family/plate-design');out.mkdir(exist_ok=True);results=[]
 for profile in ['P1','P2']:
  for inverted in [False,True]:
   root=ET.Element('mujoco');ET.SubElement(root,'option',timestep='.0025',integrator='implicitfast',gravity='0 0 -9.81');asset=ET.SubElement(root,'asset');world=ET.SubElement(root,'worldbody');ET.SubElement(world,'geom',name='table',type='box',size='.35 .575 .025',pos='.7 0 .835',friction='.7 .005 .0001')
   obj,meshes,foot=add_plate(world,profile);obj.set('pos',f'.5 0 {(.866 if inverted else .86-foot)+.002}')
   if inverted:obj.set('quat','0 1 0 0')
   for name,verts in meshes:ET.SubElement(asset,'mesh',name=name,vertex=' '.join(str(v) for p in verts for v in p))
   path=out/f'{profile}-{ "inverted" if inverted else "upright"}.xml';ET.ElementTree(root).write(path,encoding='unicode');m=mujoco.MjModel.from_xml_path(str(path));d=mujoco.MjData(m);bid=m.body('disk').id;records=[]
   for i in range(2000):
    mujoco.mj_step(m,d);load=0
    for k in range(d.ncon):
     force=np.zeros(6);mujoco.mj_contactForce(m,d,k,force);load+=np.linalg.norm(force[:3])
    records.append([d.time,*d.xpos[bid],*d.xmat[bid].reshape(3,3)[:,2],*d.qvel,load])
   arr=np.array(records);np.savez_compressed(path.with_suffix('.npz'),data=arr)
   final=arr[-800:];passed=bool(np.max(np.linalg.norm(final[:,7:13],axis=1))<1e-3 and np.max(np.linalg.norm(final[:,1:3]-[.5,0],axis=1))<1e-3 and np.min(np.abs(final[:,6]))>.999 and np.all(final[:,-1]>.1))
   results.append(dict(profile=profile,inverted=inverted,passed=passed,simulation_s=5,final_hold_s=2,final_pos=d.xpos[bid].tolist(),mass_kg=float(m.body_mass[bid]),com_local_m=m.body_ipos[bid].tolist(),principal_inertia_kg_m2=m.body_inertia[bid].tolist(),final_support_n=float(arr[-1,-1]),scope='ungrasped static tabletop support only; no flip or release witness'))
 (out/'support-probes.json').write_text(json.dumps(results,indent=2)+'\n')
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 from matplotlib.patches import Rectangle
 fig,axes=plt.subplots(2,1,figsize=(10,5));axes[0].add_patch(Rectangle((-100,-6),200,12,color='#ed963f'));axes[0].set_title('P1: solid disk · diameter 200 mm · height 12 mm · 120 g')
 axes[1].add_patch(Rectangle((-77,-8),154,4,color='#ed963f'))
 for sign in [-1,1]:
  for r0,r1,z0,z1 in [(74,80,-8,6),(79,100,0,6),(53,60,-14,-8)]:axes[1].add_patch(Rectangle((r0 if sign==1 else -r1,z0),r1-r0,z1-z0,color='#ed963f'))
 axes[1].set_title('P2 / P3: compound shallow plate · 200 × 20 mm · 120 g')
 axes[1].annotate('10 mm cavity',xy=(0,-4),xytext=(-20,12),arrowprops=dict(arrowstyle='->'))
 axes[1].annotate('14 mm under-rim clearance',xy=(90,0),xytext=(10,-29),arrowprops=dict(arrowstyle='->'))
 for ax,foot in zip(axes,[-6,-14]):
  ax.axhline(foot,color='#777',ls='--',label='upright support plane');ax.set_xlim(-115,115);ax.set_ylim(-35,24);ax.set_aspect('equal');ax.set_xlabel('Radial cross section (mm)');ax.set_ylabel('Height (mm)');ax.legend(loc='upper right',fontsize=8)
 fig.tight_layout();fig.savefig(out/'plate-cross-section.png',dpi=150);plt.close(fig);print(json.dumps(results))
if __name__=='__main__':main()
