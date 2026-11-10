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
cd /fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
set +e
"$python_bin" -m df_family.qualify_extension run --setting "$1" --cohort "$2" --repeat "$3"
result=$?
"$python_bin" -m df_family.qualify_extension report --setting "$1" --cohort "$2"
exit "$result"
