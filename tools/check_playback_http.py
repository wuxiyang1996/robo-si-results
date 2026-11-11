"""Check deployed video byte ranges after publication, without downloading videos.

    python tools/check_playback_http.py --cache-bust \
        --output .site-preview/live-playback-http.json

Only transient connection failures receive one retry. HTTP responses and media
validation failures are recorded immediately, so a second response cannot hide
an incorrect MIME type, range, or published file size.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlencode
from urllib.request import Request, urlopen
import argparse
import errno
import http.client
import json
import os
import re
import socket
import ssl
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = 'https://wuxiyang1996.github.io/robo-si-results/'
SUFFIX_IDS = ('H1S-01', 'H1S-03', 'TT-R-G-U')
RANGE_BYTES = 1024


def transient_connection_error(error):
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, ssl.SSLCertVerificationError):
        return False
    if isinstance(reason, socket.gaierror):
        return reason.errno == socket.EAI_AGAIN
    if isinstance(reason, (TimeoutError, ConnectionError,
                           http.client.RemoteDisconnected, http.client.IncompleteRead)):
        return True
    return isinstance(reason, OSError) and (
        reason.errno in {errno.ETIMEDOUT, errno.ECONNRESET, errno.ECONNABORTED,
                         errno.ECONNREFUSED, errno.ENETUNREACH, errno.EHOSTUNREACH}
        or getattr(reason, 'winerror', None) in {10050, 10051, 10053, 10054, 10060, 10061, 10065}
    )


def response_result(status, headers, body, expected_bytes, suffix):
    """Keep only the response fields needed to diagnose public video delivery."""
    content_type = headers.get('Content-Type', '').strip()
    content_range = headers.get('Content-Range', '').strip()
    disposition = headers.get('Content-Disposition', '').strip()
    attachment = disposition.split(';', 1)[0].strip().lower() == 'attachment'
    parsed = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', content_range, re.IGNORECASE)
    bounds = tuple(map(int, parsed.groups())) if parsed else None
    expected_bounds = ((expected_bytes - RANGE_BYTES, expected_bytes - 1, expected_bytes)
                       if suffix else (0, RANGE_BYTES - 1, expected_bytes))
    checks = {
        'partial_content': status == 206,
        'video_content_type': content_type.split(';', 1)[0].strip().lower() == 'video/mp4',
        'range_matches_manifest': bounds == expected_bounds,
        'body_1024_bytes': len(body) == RANGE_BYTES,
        'inline_disposition': not attachment,
    }
    return {
        'ok': all(checks.values()), 'status': status,
        'content_type': content_type,
        'content_range': content_range,
        'attachment_disposition': attachment,
        'body_bytes_read': len(body),
        'checks': checks,
        'errors': [name for name, passed in checks.items() if not passed],
    }


def check_record(record, base_url, timeout, suffix=False, cache_token=None):
    requested_range = 'bytes=-1024' if suffix else 'bytes=0-1023'
    url = urljoin(base_url, record['video_path'])
    if cache_token:
        url += '?' + urlencode({'playback_check': cache_token})
    result = {
        'record_id': record['record_id'], 'video_path': record['video_path'],
        'expected_bytes': record['bytes'], 'requested_range': requested_range,
    }
    started = time.monotonic()
    for attempt in (1, 2):
        try:
            request = Request(url, headers={
                'User-Agent': 'robo-si-playback-check/1',
                'Range': requested_range,
                'Accept': 'video/mp4',
                'Accept-Encoding': 'identity',
            })
            try:
                response = urlopen(request, timeout=timeout)
            except HTTPError as error:
                # HTTP failures are responses, not transient connection retries.
                response = error
            with response:
                # One extra byte detects a server ignoring the requested range.
                body = response.read(RANGE_BYTES + 1)
                checked = response_result(response.status, response.headers, body,
                                          record['bytes'], suffix)
            result.update(checked)
            break
        except (URLError, OSError, http.client.HTTPException) as error:
            transient = transient_connection_error(error)
            if attempt == 1 and transient:
                time.sleep(.3)
                continue
            # Exception messages can include redirect URLs; retain only type.
            result.update(ok=False, status=None, errors=['connection_failure'],
                          error_type=type(error).__name__, transient=transient)
            break
    result['attempts'] = attempt
    result['elapsed_s'] = round(time.monotonic() - started, 3)
    return result


def read_records(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    records = manifest['records']
    identifiers = set()
    for record in records:
        rid = record['record_id']
        if not isinstance(rid, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', rid):
            raise ValueError('Invalid record ID in playback manifest')
        if rid in identifiers:
            raise ValueError('Duplicate record ID in playback manifest: ' + rid)
        identifiers.add(rid)
        name = record['video_path']
        path = PurePosixPath(name)
        if (path.is_absolute() or path.as_posix() != name or '..' in path.parts
                or not name.startswith('media/videos/')
                or not all(re.fullmatch(r'[A-Za-z0-9_.-]+', part) for part in path.parts)):
            raise ValueError('Invalid video path in playback manifest: ' + rid)
        if type(record['bytes']) is not int or record['bytes'] < RANGE_BYTES:
            raise ValueError('Invalid video byte count in playback manifest: ' + rid)
    if not records or not set(SUFFIX_IDS).issubset(identifiers):
        raise ValueError('Playback manifest lacks records required for suffix checks')
    return records


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'site/content/playback_media.json')
    parser.add_argument('--base-url', default=PUBLIC_BASE)
    parser.add_argument('--output', type=Path, default=ROOT / '.site-preview/live-playback-http.json')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--timeout', type=float, default=20, help='Seconds per HTTP connection/read')
    parser.add_argument('--cache-bust', action='store_true', help='Append one fresh public query value to this run')
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 6 or not 0 < args.timeout <= 120:
        parser.error('Use 1–6 workers and a timeout greater than zero and at most 120 seconds')
    parsed = urlsplit(args.base_url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not args.base_url.endswith('/')):
        parser.error('--base-url must be an HTTPS directory URL without credentials or query parameters')
    try:
        records = read_records(args.manifest)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'ok': False, 'error': 'Invalid or missing playback manifest'}))
        return 2
    started = time.monotonic()
    token = uuid.uuid4().hex if args.cache_bust else None
    prefix_results, suffix_results = {}, {}
    jobs = [(record, False) for record in records]
    jobs += [(record, True) for record in records if record['record_id'] in SUFFIX_IDS]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(check_record, record, args.base_url, args.timeout, suffix, token):
                   (record['record_id'], suffix) for record, suffix in jobs}
        for future in as_completed(pending):
            rid, suffix = pending[future]
            (suffix_results if suffix else prefix_results)[rid] = future.result()
    prefix = [prefix_results[record['record_id']] for record in records]
    suffix = [suffix_results[rid] for rid in SUFFIX_IDS]
    all_results = prefix + suffix
    failures = [f"{item['record_id']}:{item['requested_range']}" for item in all_results if not item['ok']]
    summary = {
        'ok': not failures, 'videos': len(prefix),
        'prefix_passed': sum(item['ok'] for item in prefix),
        'suffix_passed': sum(item['ok'] for item in suffix),
        'suffix_checks': len(suffix),
        'retried_requests': sum(item['attempts'] > 1 for item in all_results),
        'failed_requests': len(failures),
        'elapsed_s': round(time.monotonic() - started, 3),
    }
    report = {
        'schema': 'robo-si-live-playback-http/1',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'public_base': args.base_url, 'cache_bust': args.cache_bust,
        'summary': summary, 'records': prefix, 'suffix_checks': suffix,
    }
    write_report(args.output, report)
    print(json.dumps({**summary, 'failed': failures[:10]}, ensure_ascii=False))
    return 0 if summary['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
