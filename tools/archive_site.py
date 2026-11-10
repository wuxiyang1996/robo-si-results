"""Render historical HTML without deploying the historical video/evidence tree.

Original tracked files remain unchanged. Every relocated file points to a fixed
Git commit, and the full mapping is shipped with the site for reproducibility.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit, quote
import hashlib
import json
import re
import subprocess


def build_archive(root, output, commit, base_url, prefix):
    tracked = subprocess.check_output(
        ['git', 'ls-tree', '-r', '-z', '--name-only', commit], cwd=root
    ).decode('utf-8').rstrip('\0').split('\0')
    files = set(tracked)
    directories = {str(parent) for path in tracked for parent in PurePosixPath(path).parents if str(parent) != '.'}
    raw = f'https://raw.githubusercontent.com/wuxiyang1996/robo-si-results/{commit}/'
    blob = f'https://github.com/wuxiyang1996/robo-si-results/blob/{commit}/'
    html_paths = sorted(p for p in tracked if p.endswith('.html'))
    assets = {}
    original_hashes = {}
    missing = set()

    def raw_url(path):
        return raw + quote(path, safe='/')

    def local_path(value, source):
        if not value or value.startswith(('#', 'data:', 'mailto:', 'tel:', 'javascript:')):
            return None
        absolute = urljoin(base_url + source, unescape(value))
        u = urlsplit(absolute)
        if u.netloc == urlsplit(base_url).netloc and u.path.startswith(prefix):
            path = u.path[len(prefix):]
        elif u.netloc == 'robo-si-review.wuxiyang.chatgpt.site':
            path = u.path.lstrip('/')
        else:
            return None
        if not path:
            path = 'index.html'
        if path not in files and path + '.html' in files:
            path += '.html'
        suffix = ('?' + u.query if u.query else '') + ('#' + u.fragment if u.fragment else '')
        return path, suffix

    def asset(path):
        if path in assets:
            return assets[path]
        name = hashlib.sha256(path.encode()).hexdigest()[:12] + '-' + PurePosixPath(path).name
        relative = 'archive/assets/' + name
        assets[path] = relative
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Sources are intentionally frozen at commit, including historical CSS/JS.
        data = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=root)
        if path.endswith('.css'):
            text = data.decode('utf-8', errors='replace')
            def css_url(match):
                value = match.group(1).strip(' \t\r\n\"\'')
                pair = local_path(value, path)
                return 'url("' + (raw_url(pair[0]) + pair[1] if pair else value) + '")'
            data = re.sub(r'url\(([^)]+)\)', css_url, text).encode('utf-8')
        target.write_bytes(data)
        return relative

    def rewrite(value, source):
        pair = local_path(value, source)
        if not pair:
            return value
        path, suffix = pair
        if path.rstrip('/') in directories:
            return f'https://github.com/wuxiyang1996/robo-si-results/tree/{commit}/' + quote(path.rstrip('/'), safe='/') + suffix
        if path not in files:
            missing.add((source, path))
            return value
        if path.endswith('.html'):
            return prefix + 'archive/pages/' + path + suffix
        if path.endswith(('.css', '.js')):
            return prefix + asset(path) + suffix
        return raw_url(path) + suffix

    class ArchiveHTML(HTMLParser):
        def __init__(self, source):
            super().__init__(convert_charrefs=False)
            self.source = source
            self.parts = []

        def tag(self, tag, attrs, closed=False):
            attrs = [(k, rewrite(v, self.source) if k in ('href', 'src', 'poster', 'data-src', 'data-timeline', 'data-video-src') and v else v)
                     for k, v in attrs]
            self.parts.append('<' + tag + ''.join(' ' + k + ('' if v is None else '="' + escape(v, quote=True) + '"')
                                                   for k, v in attrs) + ('/>' if closed else '>'))
            if tag == 'head':
                self.parts.append('<meta name="robots" content="noindex,follow">')
            if tag == 'body':
                self.parts.append('<div style="background:#efe3de;color:#642627;padding:12px 24px;font:14px/1.6 system-ui;position:relative;z-index:30">历史资料 / Archived material · <a style="color:inherit;text-decoration:underline" href="' + prefix + '">当前项目首页 / Current project</a> · <a style="color:inherit;text-decoration:underline" href="' + blob + quote(self.source, safe='/') + '">原始文件 / Original source</a></div>')

        def handle_starttag(self, tag, attrs): self.tag(tag, attrs)
        def handle_startendtag(self, tag, attrs): self.tag(tag, attrs, True)
        def handle_endtag(self, tag): self.parts.append('</' + tag + '>')
        def handle_data(self, data): self.parts.append(data)
        def handle_comment(self, data): self.parts.append('<!--' + data + '-->')
        def handle_decl(self, decl): self.parts.append('<!' + decl + '>')
        def handle_entityref(self, name): self.parts.append('&' + name + ';')
        def handle_charref(self, name): self.parts.append('&#' + name + ';')
        def handle_pi(self, data): self.parts.append('<?' + data + '>')

    for path in html_paths:
        data = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=root)
        original_hashes[path] = hashlib.sha256(data).hexdigest()
        parser = ArchiveHTML(path)
        parser.feed(data.decode('utf-8', errors='replace'))
        target = output / 'archive/pages' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join(parser.parts), encoding='utf-8')
    mapping = {p: {'raw': raw_url(p), 'source': blob + quote(p, safe='/'),
                   **({'page': prefix + 'archive/pages/' + p} if p.endswith('.html') else {})}
               for p in tracked if not p.startswith('.')}
    report = {'baseline_commit': commit, 'files': mapping, 'original_html_sha256': original_hashes,
              'historical_unresolved_links': [{'page': p, 'target': t} for p, t in sorted(missing)],
              'note': 'Historical source files remain in Git. HTML is served under archive/pages; binary and machine-readable evidence links use the immutable raw URL. Old raw HTTP paths are not a stable API.'}
    target = output / 'data/archive-files.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return html_paths, report
