"""New Gamma execution receipt around untouched frozen H1 source."""
import datetime, hashlib, importlib.metadata, json, os, pathlib, socket, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'baseline-packet'))
from reproduce import command
name = sys.argv[1]
workspace, output, argv, _ = command('fixed-native', None, name)
receipt_dir = ROOT/'baseline-runs'/name
receipt_dir.mkdir(parents=True, exist_ok=False)
def write(name, data):
 (receipt_dir/name).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
import torch
assert torch.cuda.is_available(), 'GPU required; no CPU fallback'
write('predeclared-scope.json', {'task_id':'H1S-01', 'profile':'reference_v15','seed':2,'source':'verified original fixed C371/C373 packet', 'archive_sha256':'300630ebf965ef40e6b8c16c231dfe7671fd84dabd70684b842b4138f6d03e03', 'robot_self_collision':False,'privileged_reference':True,'max_wall_seconds':3540,'max_sim_seconds':1200,'original_scoring_unchanged':True,'controller_parameters':{'crouch':.38,'lift_root':.02,'stool_waist_pitch_upper':.47,'set_ahead':.47},'formal_admission':False,'new_execution':True,'argv':argv,'cwd':str(workspace),'output':str(output)})
write('environment.json',{'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'python':sys.version,'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,'packages':{p:importlib.metadata.version(p) for p in ('genesis-world','numpy','scipy','torch','mujoco','osqp','onnxruntime')}})
start=time.monotonic();status='started';rc=None
write('started.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
try:
 rc=subprocess.call(argv,cwd=workspace,timeout=3540)
 status='process_complete'
except subprocess.TimeoutExpired:
 status='wall_budget_exhausted'
finally:
 verdict_path=output/'trusted_recording/verdict.json'
 verdict=json.loads(verdict_path.read_text()) if verdict_path.exists() else None
 write('result.json',{'status':status,'exit_code':rc,'wall_seconds':time.monotonic()-start,'new_physics_success':bool(verdict and verdict.get('success') is True and verdict.get('chain_complete') is True and verdict.get('integrity',{}).get('void') is False),'original_verdict':verdict,'output':str(output)})
raise SystemExit(rc if rc is not None else 124)
