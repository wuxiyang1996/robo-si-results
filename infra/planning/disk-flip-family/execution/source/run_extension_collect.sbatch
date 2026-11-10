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
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m df_family.collect_extension_campaign --setting "$1" --cohort "$2" --baseline "$3"
