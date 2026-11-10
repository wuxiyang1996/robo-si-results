#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
cd /fs/gamma-projects/vlm-robot/robo-si
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m df_family.compact_evidence "df_family/runs/$1"
