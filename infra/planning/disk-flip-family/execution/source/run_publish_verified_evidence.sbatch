#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1
cd /fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
"$python_bin" -m df_family.publish_run_evidence "$@"
"$python_bin" -m df_family.acceptance_status
