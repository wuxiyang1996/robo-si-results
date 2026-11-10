#!/bin/bash
#SBATCH --job-name=h1-original-gpu
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/baseline-%j.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027
export PYTHONPATH=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-extension-deps
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B baseline_runner.py "gamma-fixed-${SLURM_JOB_ID}"
