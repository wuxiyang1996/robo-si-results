#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=4 PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
cd /fs/gamma-projects/vlm-robot/robo-si/df_family/snapshots/original-v1
exec /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m humanoid.g1_tabletop_disk_flip.solution.run --output /fs/gamma-projects/vlm-robot/robo-si/df_family/runs/DF-01-G-a02-replay --backend cpu --video --replay /fs/gamma-projects/vlm-robot/robo-si/df_family/runs/DF-01-G-a02/trajectory.npz
