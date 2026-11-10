#!/bin/bash
#SBATCH --job-name=hanoi-tools
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:30:00
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV
exec /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B -m hanoi_family.run "$@"
