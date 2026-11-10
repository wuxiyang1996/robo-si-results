"""Check the Pages gallery and retain an explicit report of historical dead links."""
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from collections import Counter
import argparse
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://wuxiyang1996.github.io/robo-si-results/'
PREFIX = '/robo-si-results/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-build', type=Path, required=True)
    ap.add_argument('--report', type=Path, default=ROOT / 'data/gallery-validation.json')
    args = ap.parse_args()
    source = args.source_build.resolve()
    errors = []
    catalog = json.loads((ROOT / 'data/video-gallery.json').read_text(encoding='utf-8'))
    records = catalog['records']
    by_id = {r['record_id']: r for r in records}
    if len(records) != 246 or len(by_id) != 246:
        errors.append('The catalog must contain 246 unique records.')
    categories = sorted((ROOT / 'infra/categories').glob('*.html'))
    families = sorted((ROOT / 'infra/families').glob('*.html'))
    if len(categories) != 6 or len(families) != 30:
        errors.append('Expected six category and thirty family pages.')
    seen = Counter()
    for path in families:
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        for card in soup.select('.record-card'):
            key = card.get('id')
            seen[key] += 1
            record = by_id.get(key)
            video = card.select_one('video')
            if record is None or video is None:
                errors.append(f'{path.name}: missing record or video for {key}')
                continue
            if video.get('data-video-src') != record['video_url']:
                errors.append(f'{key}: video URL differs from catalog')
            if video.get('poster') != record['poster_url']:
                errors.append(f'{key}: poster URL differs from catalog')
            if record.get('speed') != 8:
                errors.append(f'{key}: speed is not 8x')
            if not card.select_one('.task-summary') or not card.select_one('.task-summary').get_text(strip=True):
                errors.append(f'{key}: missing visible summary')
    if set(seen) != set(by_id) or any(v != 1 for v in seen.values()):
        errors.append('Family pages must contain every record exactly once.')
    homepage = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    if len(homepage.select('video')) != 6:
        errors.append('Homepage must contain six representative videos.')
    evidence_count = 0
    for path in source.rglob('*.json'):
        relative = path.relative_to(source)
        if len(relative.parts) < 2 or relative.parts[0].startswith('.'):
            continue
        evidence_count += 1
        target = ROOT / relative
        if not target.is_file() or sha(target) != sha(path):
            errors.append(f'Evidence JSON changed or absent: {relative.as_posix()}')
    publication = json.loads((ROOT / 'data/gallery-publication.json').read_text(encoding='utf-8'))
    for relative, expected in publication['legacy_html_sha256'].items():
        if sha(ROOT / relative) != expected:
            errors.append(f'Historical HTML changed: {relative}')
    tracked = subprocess.run(['git', 'ls-tree', '--name-only', 'HEAD'], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    archive_map = {entry['original']: entry['archive'] for entry in publication.get('legacy_family_archives', [])}
    historical = list(archive_map) if archive_map else [p for p in tracked if p.endswith('.html') and p != 'index.html']
    archived_paths = [archive_map.get(p, p) for p in historical]
    # Git's clean filters account for Windows core.autocrlf checkouts. The raw
    # worktree-byte comparison to the import baseline above remains separate.
    baseline_commit = publication.get('legacy_baseline_commit', 'HEAD')
    original_ids = subprocess.run(['git', 'rev-parse'] + [baseline_commit + ':' + p for p in historical],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    current_ids = subprocess.run(['git', 'hash-object'] + archived_paths, cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.splitlines()
    raw_ids = subprocess.run(['git', 'hash-object', '--no-filters'] + archived_paths, cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.splitlines()
    for relative, original, current, raw in zip(historical, original_ids, current_ids, raw_ids):
        if (original != raw if archive_map else original not in (current, raw)):
            errors.append(f'Git-tracked historical page changed: {relative}')
    baseline_count = len(historical)
    for entry in publication.get('legacy_family_archives', []):
        if sha(ROOT / entry['archive']) != entry['sha256']:
            errors.append(f'Archive bytes changed: {entry["archive"]}')
        redirect = BeautifulSoup((ROOT / entry['original']).read_text(encoding='utf-8'), 'html.parser')
        if redirect.html.get('data-gallery-redirect') != entry['family']:
            errors.append(f'Missing current-gallery redirect: {entry["original"]}')
    for record in records:
        source_path = Path(urlsplit(record['source_page']).path).name
        if archive_map and source_path not in archive_map.values():
            errors.append(f'Historical source must point to an archive: {record["record_id"]}')
    primary = set(categories + families + [ROOT / 'index.html', ROOT / 'infra/contribute-zh.html',
                ROOT / 'infra/guide-zh.html', ROOT / 'infra/results-zh.html'])
    all_pages = list((ROOT / 'infra').rglob('*.html')) + list((ROOT / 'doc').rglob('*.html')) + [ROOT / 'index.html'] + [ROOT / p for p in archive_map]
    historical_missing = []
    anchor_warnings = []
    id_cache = {}
    reference_count = 0
    for path in all_pages:
        relative = path.relative_to(ROOT).as_posix()
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        for node in soup.select('[href],[src],[poster],[data-video-src]'):
            for key in ('href', 'src', 'poster', 'data-video-src'):
                value = node.get(key)
                if not value:
                    continue
                url = urlsplit(urljoin(BASE + relative, value))
                if url.netloc != 'wuxiyang1996.github.io':
                    continue
                reference_count += 1
                if not url.path.startswith(PREFIX):
                    errors.append(f'{relative}: URL escapes project prefix: {value}')
                    continue
                target = ROOT / unquote(url.path[len(PREFIX):])
                if target.is_dir():
                    target /= 'index.html'
                if not target.is_file():
                    item = {'page': relative, 'url': value}
                    if path in primary:
                        errors.append(f'{relative}: missing gallery target: {value}')
                    else:
                        historical_missing.append(item)
                    continue
                if url.fragment and target.suffix == '.html':
                    if target not in id_cache:
                        ts = BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')
                        id_cache[target] = {x.get('id') for x in ts.select('[id]')} | {x.get('name') for x in ts.select('[name]')}
                    if unquote(url.fragment) not in id_cache[target]:
                        anchor_warnings.append({'page': relative, 'url': value,
                                                'note': 'Static check; compatibility redirects may handle this anchor.'})
    report = {'schema': 'github-pages-gallery-check/1', 'passed': not errors,
              'unique_records': len(by_id), 'category_pages': len(categories),
              'family_pages': len(families), 'reference_count': reference_count,
              'evidence_json_verified_byte_for_byte': evidence_count,
              'historical_family_archives_verified_against_git': baseline_count,
              'legacy_family_urls_redirecting_to_current_gallery': len(archive_map),
              'errors': errors, 'historical_missing_links': historical_missing,
              'static_anchor_warnings': anchor_warnings, 'browser_visual_qa': 'not_performed'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('historical_missing_links', 'static_anchor_warnings')}, ensure_ascii=False))
    print(json.dumps({'historical_missing_links': len(historical_missing), 'static_anchor_warnings': len(anchor_warnings)}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
