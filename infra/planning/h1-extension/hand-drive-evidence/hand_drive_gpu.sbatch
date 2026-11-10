#!/bin/bash
#SBATCH --job-name=h1-hand-drive-isolated
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --array=0-1%1
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/hand-drive-fixtures-r2/job-%A_%a.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/hand-drive-fixtures-r2
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
model_ids=(dex3 inspire)
model_id="${model_ids[$SLURM_ARRAY_TASK_ID]}"
timeout 1170 /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B hand_drive_probe_frozen.py run "${model_id}/plan.json" "runs/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${model_id}"
