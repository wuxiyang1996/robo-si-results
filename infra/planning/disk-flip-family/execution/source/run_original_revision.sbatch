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
repo=/fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
out="$repo/df_family/runs/DF-01-G-$1"
test ! -e "$out"
cd "$repo/df_family/snapshots/original-expert-v2"
"$python_bin" -m humanoid.g1_tabletop_disk_flip.solution.run --output "$out" --backend cpu --seed 0 --video
lscpu --json > "$out/runtime-machine.json"
cd "$repo"
"$python_bin" -m df_family.verify_original "$out"
cd "$repo/df_family/snapshots/original-expert-v2"
"$python_bin" -m humanoid.g1_tabletop_disk_flip.solution.run --output "$out-replay" --backend cpu --seed 0 --video --replay "$out/trajectory.npz"
lscpu --json > "$out-replay/runtime-machine.json"
cd "$repo"
"$python_bin" - "$out" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);v=json.loads((p/'verification.json').read_text());s=json.loads(Path(str(p)+'-replay/summary.json').read_text());v.update(independent_physics_replay=bool(s['independent_action_replay_verified']),independent_replay_checks=s['replay_checks'],independent_replay_run=str(p)+'-replay');(p/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
PY
