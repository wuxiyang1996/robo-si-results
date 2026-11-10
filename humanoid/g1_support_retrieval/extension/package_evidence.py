"""Build a local complete, reviewable single-attempt P4 evidence packet."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def package(run, destination):
    run=Path(run).resolve();destination=Path(destination).resolve()
    if not run.name.startswith('attempt-'):raise ValueError('expected a single attempt directory')
    outcome=json.loads((run/'outcome.json').read_text())
    safety=json.loads((run/'original_safety_review.json').read_text())
    if outcome.get('task_success') is not True or safety.get('safety_passed') is not True:
        raise ValueError('This packet helper requires a completed strict task/safety witness')
    required=['profile.json','refinement-contract.json','refinement_contract_binding.json','source_hashes.json','asset_hashes.json','effective_asset_hashes.json','manifest.json','environment.json','execution/trace.json','execution/command_trace.json','execution/joint_trace.npz','execution/physics_commands.npz','execution/actuator_audit.json','execution/safety_meta.json','execution/safety_trace.npz','execution/motion.mp4','trajectory_overview.png']
    for name in required:
        if not (run/name).is_file():raise FileNotFoundError(name)
    macro_paths=list(run.glob('*macro*.json'))
    if not macro_paths:raise ValueError('Independent macro review must be retained before packaging')
    valid_macro=[]
    for path in macro_paths:
        report=json.loads(path.read_text())
        if report.get('prospectively_declared_macro_refinement_complete') is True:
            valid_macro.append(path.name)
    if not valid_macro:raise ValueError('Completed prospective macro refinement is required, not just a macro file')
    independent_safety=json.loads((run/'original_safety_independent.json').read_text())
    if independent_safety.get('complete') is not True or independent_safety.get('safety_passed') is not True:
        raise ValueError('Independent original safety review must be complete and passed')
    for name in ['independent_video_review.json','independent_video_samples.png','independent_video_final.png']:
        if not (run/name).is_file():raise FileNotFoundError(name)
    video=json.loads((run/'independent_video_review.json').read_text())
    if video.get('ai_visual_review') != 'selected_frames_reviewed':
        raise ValueError('Selected video frames must actually be reviewed before packaging')
    files=[]
    for path in sorted(run.rglob('*')):
        if '__pycache__' in path.parts:continue
        if path.is_symlink():raise ValueError('Evidence packet refuses symlink: '+str(path))
        if not path.is_file():continue
        if path.suffix in ('.pem','.key') or path.name in ('.env','credentials.json'):
            raise ValueError('Unexpected credential-like file: '+str(path))
        files.append(dict(path=f'{run.name}/{path.relative_to(run)}',size_bytes=path.stat().st_size,sha256=sha(path)))
    created=datetime.now(timezone.utc).isoformat()
    contents=dict(schema='h1-p4-local-evidence-packet/1',created_at_utc=created,attempt=run.name,
        scope='Single fresh Gamma physics execution with frozen source/assets; development evidence, not formal admission or cross-machine reproduction.',
        task_success=outcome['task_success'],original_five_rules_passed=safety['safety_passed'],formal_admission=False,
        uncompressed_file_bytes=sum(x['size_bytes'] for x in files),files=files)
    readme=f'''# Local P4 evidence: {run.name}\n\nThis packet contains exactly one development attempt and its original source/assets, raw continuous recordings, contracts and independent reviews. It is not a formal release, hardware-robot experiment, independent cross-machine reproduction or a claim about all 22 tasks. Read the actual macro and leaf reviews; fine-grained diagnostic failures are retained. GPU identity is recorded in environment.json.\n\nVerify each file against CONTENTS.json and the archive against its external packet-metadata.json. Raw sources and assets are under {run.name}/source_snapshot. Previous verdicts, if present, remain in review_history.\n\nTo perform a fresh Gamma repetition, use a compatible Genesis Python environment with the package versions recorded in environment.json and OSQP1.1.3 available on PYTHONPATH. From the repository containing the current extension launcher, set H1_REPEAT_FROM to the absolute extracted {run.name} directory, H1_EXTENSION_PYTHON to the Genesis Python interpreter, and H1_EXTENSION_DEPS to its task-local dependency directory; then run:\n\n```bash\nsbatch --export=ALL,H1_REPEAT_FROM,H1_EXTENSION_PYTHON,H1_EXTENSION_DEPS humanoid/g1_support_retrieval/extension/run_gamma.sbatch\n```\n\nThe launcher copies the immutable snapshot and starts a new simulator. It does not load an old state or replay a trajectory. The archive alone does not promise portable dependency installation or access to a Slurm Gamma partition. The original 600-s simulation/3600-s wall budget and strict 1-mrad rule remain bound in profile.json. Formal admission, independent replay, license review, sensor-only agent validation and human signoff remain separate gates.\n'''.encode()
    destination.mkdir(parents=True,exist_ok=True)
    archive=destination/f'{run.name}-complete-evidence.tar.gz'
    if archive.exists():raise FileExistsError(archive)
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for row in files:
            relative=Path(row['path']).relative_to(run.name)
            tar.add(run/relative,arcname=row['path'],recursive=False)
        for name,data in [('CONTENTS.json',(json.dumps(contents,indent=2)+'\n').encode()),('PACKAGE_README.md',readme)]:
            info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o644
            tar.addfile(info,io.BytesIO(data))
    metadata=dict(schema='h1-p4-local-packet-metadata/1',created_at_utc=created,archive_path=str(archive),
        archive_sha256=sha(archive),archive_size_bytes=archive.stat().st_size,
        file_count=len(files),uncompressed_file_bytes=contents['uncompressed_file_bytes'],
        contents_path=str(destination/f'{run.name}-CONTENTS.json'),formal_admission=False)
    (destination/f'{run.name}-CONTENTS.json').write_text(json.dumps(contents,indent=2)+'\n')
    (destination/f'{run.name}-packet-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))
    return metadata


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('run',type=Path);ap.add_argument('--destination',type=Path,required=True)
    args=ap.parse_args();package(args.run,args.destination)
