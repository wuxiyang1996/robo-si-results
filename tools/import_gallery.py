"""Import the reviewed static gallery into the GitHub Pages project site.

Run with --source-build PATH --catalog PATH. Historical flat family pages and
their media remain intact. All imported root URLs receive the project prefix.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import html
import subprocess
from urllib.parse import urlsplit, urlunsplit, unquote
from bs4 import BeautifulSoup

PREFIX = '/robo-si-results'
SITE = 'https://wuxiyang1996.github.io' + PREFIX
ROOT = Path(__file__).resolve().parents[1]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


WEB_ROOTS = 'infra|doc|media|humanoid|multi_robot|single_arm|benchmarks|controllers|disk_family|m4_family|solvers'


def web_url(value):
    if value.startswith('https://robo-si-review.wuxiyang.chatgpt.site/'):
        return SITE + value.split('.site', 1)[1]
    if value.startswith('/') and not value.startswith('//') and not value.startswith(PREFIX + '/'):
        return PREFIX + value
    return value


def routing_script(text):
    return re.sub(r'(["\'`])/(?=(?:' + WEB_ROOTS + r')(?:/|["\'`]))',
                  lambda m: m[1] + PREFIX + '/', text)


def adapt(text, suffix):
    if suffix in ('.js', '.mjs'):
        return routing_script(text)
    if suffix == '.css':
        return re.sub(r'(url\(["\']?)(/[^)"\']+)',
                      lambda m: m[1] + web_url(m[2]), text)
    if suffix != '.html':
        return text
    # Only URL attributes and routing scripts change. Evidence snippets stay exact.
    text = re.sub(r'((?:href|src|poster|action|data-video-src)=["\'])([^"\']+)',
                  lambda m: m[1] + web_url(m[2]), text)
    text = re.sub(r'(content=["\']\s*\d+;\s*url=)([^"\']+)',
                  lambda m: m[1] + web_url(m[2]), text, flags=re.I)
    text = re.sub(r'(<script\b[^>]*>)([\s\S]*?)(</script>)',
                  lambda m: m[1] + routing_script(m[2]) + m[3], text)
    return text


def repair_known_document_links(text, relative):
    # These source files were absent from the static export. Point to inspected
    # existing pages/source files without substituting a different physical record.
    active = {'infra/task-h1-zh.html', 'infra/task-h1-en.html',
              'infra/task-hanoi-zh.html', 'infra/task-hanoi-en.html',
              'infra/hanoi-design-zh.html', 'infra/reference-designs/Sokoban.html'}
    if relative not in active:
        return text
    soup = BeautifulSoup(text, 'html.parser')
    for anchor in soup.select('a[href]'):
        url = anchor['href']
        if url in (PREFIX + '/infra/hanoi-progress-zh.html', SITE + '/infra/hanoi-progress-zh.html'):
            anchor['href'] = PREFIX + '/archive-hanoi-20261104.html'
            anchor.string = ('Accepted configurations and reference videos (historical results)'
                             if relative.endswith('-en.html') else '已验收配置与参考录像（历史结果页）')
        elif url == PREFIX + '/infra/sokoban-release/mapping.json':
            anchor['href'] = 'https://github.com/wuxiyang1996/robo-si/blob/main/infra/sokoban-release/mapping.json'
            anchor.string = anchor.get_text() + '（GitHub 源文件，需仓库权限）'
        elif url == '../humanoid/g1_support_retrieval/task_spec.py':
            anchor['href'] = 'https://github.com/wuxiyang1996/robo-si/blob/main/humanoid/g1_support_retrieval/task_spec.py'
            anchor.string = anchor.get_text() + ' (GitHub; repository access required)'
        elif url == '../humanoid/g1_support_retrieval/sandbox/agent_sdk':
            anchor['href'] = 'https://github.com/wuxiyang1996/robo-si/tree/main/humanoid/g1_support_retrieval/sandbox/agent_sdk'
            anchor.string = anchor.get_text() + ' (GitHub; repository access required)'
    return str(soup)


def archive_families(source, catalog, baseline_commit):
    previous_path = ROOT / 'data/gallery-publication.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {}
    previous_pins = {x['archive']: x['sha256'] for x in previous.get('legacy_family_archives', [])}
    archives = []
    mapping = {}
    for family_page in sorted((source / 'infra/families').glob('*.html')):
        family = family_page.stem
        original = ROOT / (family.lower() + '.html')
        archive = ROOT / ('archive-' + family.lower() + '-20261104.html')
        if not archive.exists():
            assert 'data-gallery-redirect' not in original.read_text(encoding='utf-8'), original
            original_blob = subprocess.run(['git', 'show', baseline_commit + ':' + original.name],
                                           cwd=ROOT, capture_output=True, check=True).stdout
            archive.write_bytes(original_blob)
        if archive.name in previous_pins:
            assert digest(archive) == previous_pins[archive.name], archive
        archives.append({'family': family, 'original': original.name,
                         'archive': archive.name, 'sha256': digest(archive)})
        mapping[original.name] = archive.name
    replacements = {}
    for record in catalog['records']:
        old = record['source_page']
        url = urlsplit(old)
        filename = Path(url.path).name
        if url.netloc == 'wuxiyang1996.github.io' and filename in mapping:
            new = urlunsplit((url.scheme, url.netloc, PREFIX + '/' + mapping[filename], url.query, url.fragment))
            replacements[old] = new
            record['historical_source_original_url'] = old
            record['source_page'] = new
    return archives, replacements


def write_family_redirects(archives, catalog):
    for entry in archives:
        family = entry['family']
        aliases = {}
        for record in catalog['records']:
            if record['family'] != family:
                continue
            for alias in [record['record_id']] + record.get('public_case_ids', []):
                aliases[alias] = record['record_id']
            fragment = unquote(urlsplit(record.get('historical_source_original_url', record['source_page'])).fragment)
            if fragment:
                aliases[fragment] = record['record_id']
        target = PREFIX + '/infra/families/' + family + '.html'
        archive = PREFIX + '/' + entry['archive']
        script = ('const aliases=' + json.dumps(aliases) + ',target=new URL(' + json.dumps(target) + ',location.origin);'
                  'target.search=location.search;let fragment=location.hash.slice(1);try{fragment=decodeURIComponent(fragment)}catch{}'
                  'if(fragment)target.hash=aliases[fragment]||fragment;location.replace(target.pathname+target.search+target.hash);')
        text = ('<!doctype html><html lang="zh-CN" data-gallery-redirect="' + html.escape(family) + '">'
                '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>' + html.escape(family) + ' · 当前任务录像</title><link rel="canonical" href="' + SITE + '/infra/families/' + family + '.html"></head>'
                '<body><p><a href="' + target + '">打开当前 Nyx 8× 任务录像 / Current task videos</a></p>'
                '<p><a href="' + archive + '">2026-11-04 历史结果原页 / Archived original results</a></p>'
                '<script>' + script + '</script></body></html>')
        (ROOT / entry['original']).write_text(text, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-build', type=Path, required=True)
    ap.add_argument('--catalog', type=Path, required=True)
    args = ap.parse_args()
    source = args.source_build.resolve()
    assert (source / 'infra/families/H1.html').is_file()
    old_audit_path = ROOT / 'data/gallery-publication.json'
    old_audit = json.loads(old_audit_path.read_text(encoding='utf-8')) if old_audit_path.exists() else {}
    baseline_commit = old_audit.get('legacy_baseline_commit') or subprocess.run(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    archives, historical_replacements = archive_families(source, catalog, baseline_commit)
    original = ROOT / 'archive-accepted-20261104.html'
    if not original.exists():
        shutil.copyfile(ROOT / 'index.html', original)
    redirected = {x['original'] for x in archives}
    legacy = {p.name: digest(p) for p in ROOT.glob('*.html')
              if p.name != 'index.html' and p.name not in redirected}
    imported = []
    for folder in source.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        for p in folder.rglob('*'):
            if not p.is_file():
                continue
            relative = p.relative_to(source)
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() in ('.html', '.css', '.js', '.mjs'):
                text = adapt(p.read_text(encoding='utf-8'), p.suffix.lower())
                if p.suffix.lower() == '.html':
                    text = repair_known_document_links(text, relative.as_posix())
                target.write_text(text, encoding='utf-8')
            else:
                shutil.copyfile(p, target)
            imported.append(relative.as_posix())
    catalog['publication_url'] = SITE + '/'
    target = ROOT / 'data/video-gallery.json'
    target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest_url = catalog['remote_manifest_url']
    for relative in imported:
        path = ROOT / relative
        if path.suffix == '.html':
            text = path.read_text(encoding='utf-8').replace(manifest_url, PREFIX + '/data/video-gallery.json')
            for old, new in historical_replacements.items():
                text = text.replace(old, new)
            path.write_text(text, encoding='utf-8')
    # Keep a task summary visible even when detailed evidence is collapsed.
    for path in (ROOT / 'infra/families').glob('*.html'):
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        for card in soup.select('.record-card'):
            details = card.select_one('.record-details')
            scope = details.select_one('p[data-zh]') if details else None
            if scope is None:
                continue
            summary = soup.new_tag('p', attrs={'class': 'task-summary'})
            for lang in ('zh', 'en'):
                value = scope.get('data-' + lang, '')
                first = re.split(r'(?<=[。！？])|(?<=[.!?])\s+', value, maxsplit=1)[0]
                summary['data-' + lang] = first or value
            summary.string = summary['data-zh']
            details.insert_before(summary)
        path.write_text(str(soup), encoding='utf-8')
    # Render the gallery directly at the public root; no extra redirect on entry.
    home = (ROOT / 'infra/contribute-zh.html').read_text(encoding='utf-8')
    (ROOT / 'index.html').write_text(home, encoding='utf-8')
    write_family_redirects(archives, catalog)
    assert all(digest(ROOT / name) == pin for name, pin in legacy.items())
    audit = {'schema': 'github-pages-gallery-import/1', 'site': SITE + '/',
             'project_base': PREFIX, 'imported_files': len(imported),
             'legacy_html_sha256': legacy, 'unique_records': len(catalog['records']),
             'legacy_family_archives': archives, 'legacy_baseline_commit': baseline_commit,
             'archive_byte_policy': 'exact_original_git_blob',
             'legacy_preserved': True}
    (ROOT / 'data/gallery-publication.json').write_text(
        json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('legacy_html_sha256', 'legacy_family_archives')}))


if __name__ == '__main__':
    main()
