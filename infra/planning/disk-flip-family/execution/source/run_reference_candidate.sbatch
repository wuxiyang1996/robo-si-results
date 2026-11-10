#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
cd /fs/gamma-projects/vlm-robot/robo-si
set +e
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m df_family.reference_candidate --setting "$1" --output "df_family/runs/$1-$2" "${@:3}"

run_exit=$?
if [ -f "df_family/runs/$1-$2/trajectory.npz" ]; then
 /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m df_family.verify "df_family/runs/$1-$2"
fi
exit "$run_exit"
