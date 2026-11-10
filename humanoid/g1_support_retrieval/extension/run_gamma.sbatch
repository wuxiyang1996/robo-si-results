#!/bin/bash
#SBATCH --job-name=h1-p4-development
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=humanoid/g1_support_retrieval/extension/validation/job-logs/%x-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
export PYTHONPATH="${H1_EXTENSION_DEPS:-/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-extension-deps}${PYTHONPATH:+:$PYTHONPATH}"
export PYOPENGL_PLATFORM=egl PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
python_bin=${H1_EXTENSION_PYTHON:-/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python}
if [[ -n "${H1_REPEAT_FROM:-}" ]]; then
  "$python_bin" -m humanoid.g1_support_retrieval.extension.repeat_frozen --baseline "$H1_REPEAT_FROM" --out "humanoid/g1_support_retrieval/extension/validation/attempt-${SLURM_JOB_ID}"
else
  contract_args=()
  if [[ -n "${H1_REFINEMENT_CONTRACT:-}" ]]; then
    contract_args=(--refinement-contract "$H1_REFINEMENT_CONTRACT")
  fi
  "$python_bin" -m humanoid.g1_support_retrieval.extension.run_p4 "${contract_args[@]}" --profile "${H1_EXTENSION_PROFILE:-humanoid/g1_support_retrieval/extension/p4-development.json}" --out "humanoid/g1_support_retrieval/extension/validation/attempt-${SLURM_JOB_ID}"
fi

attempt_dir="${SLURM_SUBMIT_DIR}/humanoid/g1_support_retrieval/extension/validation/attempt-${SLURM_JOB_ID}"
(
  cd "$attempt_dir/source_snapshot"
  "$python_bin" -m humanoid.g1_support_retrieval.extension.verify_p4 "$attempt_dir" || true
  "$python_bin" -m humanoid.g1_support_retrieval.extension.verify_p4_safety "$attempt_dir" || true
)
