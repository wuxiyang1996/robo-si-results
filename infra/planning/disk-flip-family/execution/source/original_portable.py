"""Package frozen original sources and robot assets with byte-preserving evidence."""
import argparse,hashlib,json,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--closed-loop',type=Path);p.add_argument('--closed-loop-replay',type=Path);p.add_argument('--recorded-policy',type=Path);p.add_argument('--portable-validation-run',type=Path);a=p.parse_args();out=a.output;assert not out.exists();out.mkdir(parents=True)
 source=BASE/'snapshots/original-expert-v2';shutil.copytree(source,out/'source',symlinks=False,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for name in ['LICENSE','README.md']:shutil.copyfile(BASE.parent/'humanoid/g1_support_retrieval/assets/unitree_g1'/name,out/('unitree-g1-'+name))
 cohort=BASE/'qualification/DF-01-G/cohort-v2';shutil.copytree(cohort,out/'qualification',symlinks=False)
 isolated=a.recorded_policy or Path('/nfshomes/wuxiyang/df-live-output/isolated/original-v2-recorded-policy-03');shutil.copytree(isolated,out/'isolated-recorded-policy',symlinks=False)
 shutil.copyfile(isolated/'transport-adapter.py',out/'isolated_original_replay.py')
 for argument,directory in [(a.closed_loop,'isolated-closed-loop'),(a.closed_loop_replay,'isolated-closed-loop-replay'),(a.portable_validation_run,'portable-fresh-execution')]:
  if argument:
   assert (argument/'summary.json').exists();shutil.copytree(argument,out/directory,symlinks=False)
 if a.closed_loop:
  shutil.copyfile(a.closed_loop/'closed-loop-adapter.py',out/'isolated_original_closed_loop.py')
 for name in ['original-frozen-scorer-checks.json','original-portable-validation.json']:
  shutil.copyfile(BASE/'acceptance'/name,out/name)
 shutil.copyfile(BASE/'original-plan.json',out/'original-plan.json')
 shutil.copyfile(BASE.parent/'tests/test_tabletop_disk_flip.py',out/'test_tabletop_disk_flip.py')
 metadata=json.loads((cohort/'manifest.json').read_text());copied=out/'source'
 checks={k:digest(copied/k)==v for k,v in {**metadata['source_hashes'],**metadata['robot_asset_hashes']}.items()};assert all(checks.values())
 assert not any(p.is_symlink() for p in out.rglob('*'))
 (out/'REPRODUCE.md').write_text('''# Original Disk Flip expert v2 reproduction

Scope: fixed pelvis, nominal generated start, Genesis CPU, privileged expert. This bundle does not qualify the other five settings and does not supply human signoff or second-person reproduction.

The source and all robot assets are included with original bytes. `qualification/manifest.json` freezes the expert, scorer, configuration, seed and runtime versions. The failed infrastructure replay folder is retained separately; the completed retry is identified in `replay-attempts.json` and the repeat-01 verification report.

Use Python 3.12 with the exact runtime package versions listed in the manifest. No installation script or credentials are included. Run from `source/`, setting `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1`:

```sh
python -m humanoid.g1_tabletop_disk_flip.solution.run --output ../fresh-expert --backend cpu --seed 0 --video
python -m humanoid.g1_tabletop_disk_flip.solution.run --output ../fresh-action-replay --backend cpu --seed 0 --video --replay ../qualification/repeat-01/trajectory.npz
```

Outputs must use new directories. Check `full_task_success`, `error`, `integrity_audit` and all `replay_checks`; a rendered video alone is not a pass. Numerical differences across hardware may affect replay; preserve failed results. The included isolated recorded-policy execution uses a separate process to emit joint references and has no shared simulator memory. The recorded-policy and online closed-loop runs are separate evidence: inspect each report. The online expert receives read-only observations over JSON, computes joint references in a child process, and leaves physics/scoring with the trusted parent. Neither adapter is an OS security sandbox.

To repeat the included online closed-loop expert, run from the bundle root, using a fresh output directory:

```sh
python isolated_original_closed_loop.py --snapshot source --output isolated-fresh
```

Replay its recorded trajectory from `source/` with the native `--replay` command above. The child is privileged: observations include simulator object poses and contact loads. These are author-side expert results, not a public-agent benchmark score. The native servo enforces the unchanged joint target speed and effort bounds.

The included frozen scorer test file can be run from the bundle root with `PYTHONPATH=source python -m unittest test_tabletop_disk_flip`; the source snapshot takes precedence over installed modules. The portable fresh execution was produced from the previous package's identical frozen source and asset bytes; `original-portable-validation.json` binds its native integrity/configuration/physics checks. Packaging additional evidence does not constitute a second-person reproduction.

All videos, trajectories, traces, source snapshots and hashes for the frozen cohort are retained. Validate the bundle with `python verify_bundle.py` before execution. Robot licensing: see `unitree-g1-LICENSE` and upstream provenance in `unitree-g1-README.md`.
''')
 (out/'verify_bundle.py').write_text('''from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'bundle-manifest.json').read_text())
for relative,record in manifest['files'].items():
 path=root/relative
 assert path.is_file() and path.stat().st_size==record['bytes'],relative
 assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],relative
print('PASS:',len(manifest['files']),'files match SHA-256')
''')
 files={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(out.rglob('*')) if p.is_file()}
 report=dict(schema='disk-flip-original-portable/1',snapshot='original-expert-v2',scope='Byte-preserving original sources, assets and cohort evidence; not whole-family admission',cohort_manifest_sha256=digest(cohort/'manifest.json'),frozen_source_and_asset_checks=checks,symlinks=False,files=files)
 (out/'bundle-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(files=len(files),bytes=sum(x['bytes'] for x in files.values()),frozen_hashes_match=all(checks.values()),output=str(out))))
if __name__=='__main__':main()
