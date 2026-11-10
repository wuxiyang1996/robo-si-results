#!/bin/bash
#SBATCH --partition=gamma
#SBATCH --account=gamma
#SBATCH --qos=default
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=/fs/gamma-projects/vlm-robot/robo-si/df_family/job-logs/%x-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONNOUSERSITE=1
cd /fs/gamma-projects/vlm-robot/robo-si
python_bin=/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python
"$python_bin" -m df_family.qualify_extension freeze --setting "$1" --cohort "$2" --baseline "$3"
"$python_bin" - "$1" "$2" <<'PY'
import datetime,json,subprocess,sys
from pathlib import Path
setting,cohort=sys.argv[1:];path=Path('df_family/qualification')/setting/cohort/'submissions.json';records=[]
for repeat in [1,2,3]:
 job=subprocess.check_output(['sbatch','--parsable','-J',f'df-{setting}-q{repeat}','df_family/run_extension_qualification.sbatch',setting,cohort,str(repeat)],text=True).strip()
 records.append(dict(repeat=repeat,slurm_job=job,submitted_at=datetime.datetime.now(datetime.timezone.utc).isoformat()));path.write_text(json.dumps(records,indent=2)+'\n');print(records[-1],flush=True)
PY
"$python_bin" -m df_family.qualify_extension report --setting "$1" --cohort "$2"
