"""Import a verified result bundle; publish only explicit, portable result fields.

Usage: python tools/import_leaderboard.py PATH_TO_astra_246_BUNDLE
The original bundle is read-only. No model or simulation is run.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bundle', type=Path)
    args = ap.parse_args()
    bundle = args.bundle.resolve()
    checksums = dict((name, sha) for sha, name in
                     (line.split('  ', 1) for line in (bundle/'SHA256SUMS').read_text().splitlines()))
    used = {}

    def read(name):
        path = (bundle/name).resolve()
        assert path.is_relative_to(bundle)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert checksums[name] == digest, name
        used[name] = digest
        return raw.decode('utf-8-sig')

    summary = json.loads(read('summary.json'))
    rows = list(csv.DictReader(read('tables/tasks_246.csv').splitlines()))
    readiness = list(csv.DictReader(read('tables/readiness_492.csv').splitlines()))
    attempts = {r['result_path']: r for r in csv.DictReader(read('tables/astra_attempts.csv').splitlines())}
    gallery = json.loads((ROOT/'data/video-gallery.json').read_text(encoding='utf-8'))
    records = {r['record_id']: r for r in gallery['records']}
    assert len(rows) == len({r['case'] for r in rows}) == 246
    assert set(records) == {r['case'] for r in rows}
    assert len({r['family'] for r in rows}) == 29
    assert len(readiness) == len({(r['case'], r['mode']) for r in readiness}) == 492
    assert all(r['readiness_verified'] == 'True' for r in readiness)
    assert dict(Counter(r['astra_status'] for r in rows)) == summary['case_status_counts']
    tasks = []
    for row in rows:
        valid = row['has_valid_evaluation'] == 'True'
        success = row['verified_success'] == 'True' if valid else None
        proof = None
        if valid:
            attempt = attempts[row['selected_result_path']]
            assert attempt['probe_only'] == 'False' and attempt['valid_independent_evaluation'] == 'True'
            result = json.loads(read(row['selected_result_path']))
            proof = {'result_sha256': used[row['selected_result_path']],
                     'bundle_path': row['selected_result_path'],
                     'runtime_verified': result.get('runtime_verified'),
                     'success': result.get('success'),
                     'submission_unchanged': result.get('submission_unchanged'),
                     'submission_sha256': result.get('submission_sha256')}
            assert proof['runtime_verified'] is True and proof['submission_unchanged'] is True
            assert proof['success'] is success
        tasks.append({'case': row['case'], 'family': row['family'],
                      'local_scope': row['local_astra_scope'] == 'True',
                      'status': row['astra_status'], 'valid': valid, 'success': success,
                      'native_score': float(row['selected_native_score']) if valid and row['selected_native_score'] else None,
                      'snapshot': row['has_snapshot_evaluation'] == 'True',
                      'attempts': int(row['nonprobe_attempts']),
                      'standard_ready': row['standard_ready'] == 'True',
                      'privileged_ready': row['privileged_ready'] == 'True',
                      'evidence': proof})
    assert sum(t['valid'] for t in tasks) == summary['valid_evaluation_cases'] == 30
    assert sum(t['local_scope'] for t in tasks) == 99
    assert sorted(t['case'] for t in tasks if t['success']) == sorted(summary['verified_success_cases'])
    assert all(t['standard_ready'] and t['privileged_ready'] for t in tasks)
    out = ROOT/'site/content/leaderboard.json'
    out.write_text(json.dumps({'schema': 'robo-si-leaderboard/1', 'updated': '2026-11-23',
                              'run_end': '2026-11-15 10:42:48 EST',
                              'summary': summary, 'tasks': tasks,
                              'source_checksums': used}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'tasks': len(tasks), 'valid': 30, 'success': 2, 'verified_sources': len(used)}))


if __name__ == '__main__':
    main()
