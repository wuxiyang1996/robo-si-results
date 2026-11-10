#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --constraint=Zen
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
cd /fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
"$python_bin" - "$1" <<'CHECK'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);s=json.loads((root/'summary.json').read_text());v=json.loads((root/'verification.json').read_text())
assert s['task_success'] and v['task_success'] and v['replay_matches'],'Baseline has no verified complete witness; supplemental acceptance was not started'
CHECK
if ! "$python_bin" - "$1" <<'REUSE'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);read=lambda n:json.loads((root/n).read_text())
try:
 r=read('reference-replay-verification.json');m=read('trajectory-reference.json')
 assert r['all_physics_state_and_control_array_hashes_match'] and r['actual_sha256']==m['full_array_sha256']
 for key,name in [('reference_packet_sha256','trajectory-reference.npz'),('reference_metadata_sha256','trajectory-reference.json'),('scene_sha256','scene.xml'),('initial_state_sha256','initial_state.json')]:assert r[key]==hashlib.sha256((root/name).read_bytes()).hexdigest()
 assert m['source_trajectory_npz_sha256']==hashlib.sha256((root/'trajectory.npz').read_bytes()).hexdigest()
except (AssertionError,KeyError,FileNotFoundError,json.JSONDecodeError):raise SystemExit(1)
print('Reusing exact replay proof bound to current packet, metadata, scene, initial state and native trajectory')
REUSE
then
 "$python_bin" -m df_family.compact_evidence "$1"
fi
"$python_bin" -m df_family.portable_extension_expert "$1" --output "$2"
