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
"$python_bin" "$1/entry.py" "$1" "$2" "$3"
run_exit=$?
if [ -f "$3/trajectory.npz" ]; then
 "$python_bin" -m df_family.verify "$3"
 verify_exit=$?
 if [ "$verify_exit" -ne 0 ]; then exit "$verify_exit"; fi
fi
exit "$run_exit"
