#!/bin/bash
#SBATCH --job-name=h1-asset-smoke
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --array=0-1%1
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/asset-smoke-%A_%a.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
models=(a3_t3d0 stretch4_francis_sg4)
set +e
timeout 1170 /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B asset_audit_frozen.py smoke --plan asset-smoke-plan.json --model "${models[$SLURM_ARRAY_TASK_ID]}" --out "asset-smoke-runs/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
probe_rc=$?
set -e
printf '%s\n' "$probe_rc" > "asset-smoke-exit-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt"
exit "$probe_rc"
