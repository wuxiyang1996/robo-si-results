#!/bin/bash
#SBATCH --job-name=hanoi-campaign
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --array=1-10%3
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/hanoi_family/job-logs/%A_%a.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV
printf -v hanoi_task 'Hanoi-%02d' "$SLURM_ARRAY_TASK_ID"
hanoi_controls=6000
if [ "$SLURM_ARRAY_TASK_ID" -eq 7 ]; then hanoi_controls=14000; fi
if [ "$SLURM_ARRAY_TASK_ID" -eq 8 ]; then hanoi_controls=24000; fi
exec /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B -m hanoi_family.run \
  --task "$hanoi_task" --out "hanoi_family/runs/${hanoi_task}-expert-a04" --backend cpu --max-controls "$hanoi_controls"
