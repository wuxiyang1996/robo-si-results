#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd /fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
if [ -f df_family/qualification/DF-04-S/cohort-v1/manifest.json ]; then
 "$python_bin" -m df_family.qualify_extension report --setting DF-04-S --cohort cohort-v1
fi
"$python_bin" -m df_family.extension_acceptance --setting DF-04-S --baseline DF-04-S-a26 --scorer df_family/acceptance/extension-scorer-S-a26.json --boundary df_family/acceptance/isolated-boundary-S-a26.json --isolated df_family/isolated/DF-04-S-recorded-01/report.json --portable df_family/portable-validation/S-v1-fresh/portable-validation.json --bundle df_family/acceptance/portable-S-v1
"$python_bin" -m df_family.acceptance_status
"$python_bin" -m df_family.monitor
