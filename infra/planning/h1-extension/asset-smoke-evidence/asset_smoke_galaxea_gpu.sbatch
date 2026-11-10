#!/bin/bash
#SBATCH --job-name=h1-galaxea-asset-smoke
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/asset-smoke-galaxea-%j.log
set -euo pipefail
cd /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
set +e
timeout 1170 /fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -B asset_audit_frozen.py smoke --plan asset-smoke-galaxea-plan.json --model galaxea_r1_v2_1_0 --out "asset-smoke-runs/${SLURM_JOB_ID}_galaxea"
probe_rc=$?
set -e
printf '%s\n' "$probe_rc" > "asset-smoke-exit-${SLURM_JOB_ID}_galaxea.txt"
exit "$probe_rc"
