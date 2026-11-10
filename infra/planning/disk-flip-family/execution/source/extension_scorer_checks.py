"""Counterexamples against the exact archived extension scorer method.

Synthetic observations test predicates and timers, not dynamic feasibility.
"""
import argparse,ast,hashlib,json,types
from pathlib import Path
import numpy as np

def run(source):
 tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Attempt');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='assess');module=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
 def velocity(m,d,kind,obj,result,local):result[:]=d.velocity
 namespace={'np':np,'mujoco':types.SimpleNamespace(mj_objectVelocity=velocity,mjtObj=types.SimpleNamespace(mjOBJ_BODY=1))};exec(compile(module,str(source),'exec'),namespace);assess=namespace['assess'];rows=[]
 def fixture(**kw):
  x=types.SimpleNamespace(m=None,obj=0,profile=kw.get('profile','P1'),phase=kw.get('phase','release'),dt=.0005,hold=0.,unsupported=0.,success=False,seen_lift=False,seen_flip=False,peaks={k:0. for k in ['speed','angular','robot','table','local','robot_table','self_contact']})
  angle=np.deg2rad(kw.get('angle',0.));R=np.array([[np.cos(angle),0,np.sin(angle)],[0,-1,0],[np.sin(angle),0,-np.cos(angle)]])
  x.d=types.SimpleNamespace(xpos=np.array([kw.get('position',[.5,0,.866])],dtype=float),xmat=np.array([R.flatten()]),qpos=np.zeros(7),qvel=np.zeros(6),time=0.,velocity=np.array([kw.get('angular',0.),0,0,kw.get('speed',0.),0,0]))
  x.contacts=lambda:(kw.get('robot',0.),kw.get('table',1.1772),kw.get('local',0.),kw.get('robot_table',0.),kw.get('self_contact',0.),[])
  return x
 def check(name,expected_success=False,expected_error=None,steps=4002,**kw):
  a=fixture(**kw);error=None
  if kw.get('nonfinite'):a.d.qpos[0]=float('nan')
  try:
   for _ in range(steps):a.d.time+=a.dt;assess(a)
  except RuntimeError as e:error=str(e)
  passed=bool(a.success)==expected_success and error==expected_error
  rows.append(dict(case=name,passed=passed,observed_success=bool(a.success),observed_error=error));assert passed,rows[-1]
 check('inverted_released_stable_positive_control',True)
 check('supported_turnover_does_not_require_lift',True,phase='turn')
 for phase in ['settle','close','turn','place','release']:
  check('stage_label_cannot_complete_'+phase,angle=180.,phase=phase)
 check('inverted_outside_goal',position=[.6,0,.866]);check('inverted_overhang',position=[.42,0,.866]);check('orientation_outside_tolerance',angle=8.1)
 check('orientation_inside_tolerance',True,angle=7.9);check('still_held_by_hand',robot=.051);check('moving_at_goal',speed=.016);check('spinning_at_goal',angular=.081)
 check('insufficient_terminal_dwell',steps=3998);check('contact_loss',expected_error='uncontrolled_contact_loss',table=0.)
 for key,value,error in [('speed',.121,'disk_linear_speed'),('angular',.651,'disk_angular_speed'),('robot',18.01,'robot_contact_load'),('table',8.01,'table_contact_load'),('local',18.01,'local_damage_proxy'),('robot_table',20.01,'robot_table_collision'),('self_contact',20.01,'robot_self_collision')]:check('reject_'+error,expected_error=error,**{key:value})
 check('p3_local_load_cap',expected_error='local_damage_proxy',profile='P3',local=4.01);check('p2_does_not_apply_p3_cap',True,profile='P2',local=4.01)
 check('dropped',expected_error='disk_dropped',position=[.5,0,.83]);check('nonfinite',expected_error='nonfinite_physics',nonfinite=True)
 a=fixture()
 for _ in range(3998):assess(a)
 a.contacts=lambda:(.1,1.1772,.1,0,0,[]);assess(a);a.contacts=lambda:(0,1.1772,0,0,0,[])
 for _ in range(100):assess(a)
 assert not a.success and a.hold<.1;rows.append(dict(case='contact_resets_terminal_timer',passed=True))
 return dict(schema='disk-flip-frozen-extension-scorer-checks/1',passed=all(r['passed'] for r in rows),checks=rows,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Synthetic predicate/timer counterexamples executed against archived assess() source. Not a physical execution or feasibility witness.')
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(r['checks']),a.output)
if __name__=='__main__':main()
