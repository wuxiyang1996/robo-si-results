#!/bin/bash
#SBATCH --job-name=h1-dex3-asset-smoke
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/asset-smoke-dex3-%j.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
set +e
timeout 1170 /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B asset_audit_dex3_frozen.py smoke --plan asset-smoke-dex3-plan.json --model g1_rev1_Dex3 --out "asset-smoke-runs/${SLURM_JOB_ID}_dex3"
probe_rc=$?
set -e
printf '%s\n' "$probe_rc" > "asset-smoke-exit-${SLURM_JOB_ID}_dex3.txt"
exit "$probe_rc"
