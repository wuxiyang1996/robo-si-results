"""Validate published result semantics, CSV exports and evidence closure."""
import csv
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Rows(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.rows = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and 'data-lb-row' in attrs:
            self.rows.append(attrs)


def main():
    source = json.loads((ROOT/'site/content/leaderboard.json').read_text(encoding='utf-8'))
    public = json.loads((ROOT/'dist/data/leaderboard.json').read_text(encoding='utf-8'))
    assert source == public
    tasks = public['tasks']
    summary = public['summary']
    counts = Counter(t['status'] for t in tasks)
    assert counts == summary['case_status_counts']
    assert len(tasks) == len({t['case'] for t in tasks}) == summary['benchmark']['cases'] == 246
    assert len({t['family'] for t in tasks}) == 29
    assert sum(t['local_scope'] for t in tasks) == summary['scope']['current_local'] == 99
    assert sum(t['valid'] for t in tasks) == summary['valid_evaluation_cases'] == 30
    assert sorted(t['case'] for t in tasks if t['success']) == sorted(summary['verified_success_cases'])
    assert sum(t['success'] is False for t in tasks) == 28
    assert summary['aggregate_246_success_rate'] is None and summary['official_efe_run'] is False
    assert sum(t['standard_ready'] + t['privileged_ready'] for t in tasks) == 492
    with (ROOT/'dist/data/leaderboard-tasks.csv').open(encoding='utf-8-sig', newline='') as handle:
        exported = list(csv.DictReader(handle))
    assert len(exported) == 246
    by_case = {row['case']: row for row in exported}
    evidence_files = set()
    for task in tasks:
        row = by_case[task['case']]
        assert row['status'] == task['status']
        assert row['family'] == task['family']
        if not task['valid']:
            assert task['success'] is None and task['native_score'] is None and task['evidence'] is None
            assert row['native_score'] == '' and row['success'] == ''
        else:
            proof = task['evidence']
            assert proof['success'] is task['success']
            assert proof['runtime_verified'] and proof['submission_unchanged']
            assert public['source_checksums'][proof['bundle_path']] == proof['result_sha256']
            path = ROOT/'dist/data/leaderboard-evidence'/(task['case']+'.json')
            assert json.loads(path.read_text()) == proof
            evidence_files.add(path.name)
    assert {p.name for p in (ROOT/'dist/data/leaderboard-evidence').iterdir()} == evidence_files
    html = (ROOT/'dist/leaderboard.html').read_text(encoding='utf-8')
    rows = Rows(html).rows
    assert len(rows) == 246
    assert {r['data-case'] for r in rows} == set(by_case)
    assert Counter(r['data-status'] for r in rows) == counts
    assert all(r['data-family'] == by_case[r['data-case']]['family'] for r in rows)
    assert '/robo-si-results/leaderboard.html' in (ROOT/'dist/index.html').read_text(encoding='utf-8')
    assert '/robo-si-results/leaderboard.html' in (ROOT/'dist/sitemap.xml').read_text()
    print(json.dumps({'passed': True, 'tasks': 246, 'valid_scores': 30, 'successes': 2,
                      'unscored_preserved_as_null': 216, 'evidence_digests': len(evidence_files)}))


if __name__ == '__main__':
    main()
