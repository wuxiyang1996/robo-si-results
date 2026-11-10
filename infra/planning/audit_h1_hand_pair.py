"""Reproduce the static, official G1 rev1 body comparison; no physics claim."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PIN = '7919cba47a3f68888f3b084945b0ffbf3bb3763a'
MODELS = {
    'dex3': 'g1_29dof_with_hand_rev_1_0.urdf',
    'inspire_dfq': 'g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf',
}


def structural(node):
    return (node.tag, sorted(node.attrib.items()), (node.text or '').strip(),
            [structural(child) for child in node])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT.parents[2] /
        'robo-si-local-tests/h1-implementation-20261027/asset-cache/unitree_ros')
    args = parser.parse_args()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.cache, text=True).strip()
    if head != PIN:
        raise SystemExit(f'Pinned repository mismatch: {head}')
    models, roots = {}, {}
    for key, name in MODELS.items():
        path = args.cache / 'robots/g1_description' / name
        relative = str(path.relative_to(args.cache))
        raw = path.read_bytes()
        pinned = subprocess.check_output(['git', 'show', f'{PIN}:{relative}'], cwd=args.cache)
        if raw != pinned:
            raise SystemExit(f'Modified pinned model: {relative}')
        root = ET.fromstring(raw)
        roots[key] = root
        joints = [j for j in root.findall('joint') if j.get('type') != 'fixed']
        mimic = [j for j in joints if j.find('mimic') is not None]
        meshes = {}
        for mesh in root.findall('.//mesh'):
            uri = mesh.get('filename')
            local = path.parent / uri.removeprefix('package://g1_description/')
            if not local.is_file():
                raise SystemExit(f'Missing mesh: {uri}')
            meshes[uri] = hashlib.sha256(local.read_bytes()).hexdigest()
        models[key] = dict(path=relative, sha256=hashlib.sha256(raw).hexdigest(),
            movable_joint_count=len(joints), mimic_joint_count=len(mimic),
            non_mimic_joint_count=len(joints)-len(mimic),
            mimic=[dict(name=j.get('name'), **j.find('mimic').attrib) for j in mimic],
            mesh_sha256=meshes)
    comparisons = {}
    for comparison in ('joint', 'fixed_joint', 'link'):
        tag = 'joint' if comparison == 'fixed_joint' else comparison
        elements = [{e.get('name'): e for e in root.findall(tag)
                     if tag != 'joint' or (e.get('type') == 'fixed') == (comparison == 'fixed_joint')}
                    for root in roots.values()]
        common = sorted(set(elements[0]) & set(elements[1]))
        equal = [name for name in common if structural(elements[0][name]) == structural(elements[1][name])]
        comparisons[comparison] = dict(common_names=common, structurally_identical_names=equal,
            different_names=sorted(set(common)-set(equal)),
            variant_only_names={key:sorted(set(part)-set(common)) for key,part in zip(MODELS,elements)})
    same = (len(comparisons['joint']['common_names']) == 29 and
            len(comparisons['fixed_joint']['common_names']) == 7 and
            len(comparisons['link']['common_names']) == 37 and
            all(not value['different_names'] for value in comparisons.values()))
    result = dict(schema='h1-official-g1-matched-body-static-audit/1',
        generated_utc=datetime.now(timezone.utc).isoformat(),
        repository='https://github.com/unitreerobotics/unitree_ros', commit=PIN,
        method='Recursive XML tag, sorted attributes, stripped text, ordered children; mesh content hashes. Common movable and fixed joints and common links.',
        models=models, comparisons=comparisons, shared_body_structurally_identical=same,
        task_success=None, physics_executed_by_this_audit=False,
        limitations=[
            'Structural equality does not establish contact dynamics, controller compatibility, motor independence, or stable grasping.',
            'Inspire mimic joints need an explicit Genesis coupling and actuation audit; raw joint count is not active motor count.',
            'The existing H1 Menagerie-based G1 runtime is a separate legacy embodiment; its evidence does not transfer to these official rev1 models.',
            'Matched-hand task comparisons must freeze the same world, body settings, seed, sensing and scoring, then validate each end effector independently.',
        ])
    (ROOT/'h1-extension/g1-matched-body-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(shared_body_structurally_identical=same,
        common_movable_joints=len(comparisons['joint']['common_names']),
        common_links=len(comparisons['link']['common_names']),
        models={k:{n:v[n] for n in ('movable_joint_count','mimic_joint_count','non_mimic_joint_count')} for k,v in models.items()})))
    if not same:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
