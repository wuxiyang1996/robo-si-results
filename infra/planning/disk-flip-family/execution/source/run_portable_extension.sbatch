#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
cd "$1"
"$python_bin" run_expert.py --output "$2"
"$python_bin" verify.py "$2"
"$python_bin" - "$2" <<'PY'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1]);v=json.loads((out/'verification.json').read_text());s=json.loads((out/'summary.json').read_text());assert s['task_success'] and v['task_success'] and v['replay_matches']
manifest=Path('expert-manifest.json');m=json.loads(manifest.read_text());assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in m['files'].items())
report=dict(passed=True,setting=m['setting'],scope='Fresh relocated portable frozen-expert execution and independent control replay; same-author automated test, not second-person reproduction',bundle_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),summary_sha256=hashlib.sha256((out/'summary.json').read_bytes()).hexdigest(),verification_sha256=hashlib.sha256((out/'verification.json').read_bytes()).hexdigest(),compiled_physics_arrays_identical=json.loads((out/'portable-initialization.json').read_text())['compiled_physics_arrays_identical'])
(out/'portable-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
PY
