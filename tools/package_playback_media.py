"""Package verified browser derivatives and write their public delivery manifest."""
from pathlib import Path
import argparse
import json
import zipfile
from playback_media import sha256, MEDIA_BUDGET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / '.cache/browser-media')
    parser.add_argument('--bundle-url', required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'site/content/playback_media.json')
    args = parser.parse_args()
    source = args.input.resolve()
    catalog_path = ROOT / 'data/video-gallery.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    originals = {r['record_id']: r for r in catalog['records']}
    manifest = json.loads((source / 'playback-media.json').read_text(encoding='utf-8'))
    records = manifest['records']
    assert len(records) == len(originals) and {r['record_id'] for r in records} == set(originals), 'Incomplete browser media'
    assert manifest['source_manifest_sha256'] == sha256(catalog_path), 'Original manifest changed'
    entries = []
    for item in records:
        rid = item['record_id']
        assert item['source_sha256'] == originals[rid]['source_8x_sha256'], rid
        assert item['faststart'] and item['full_decode_verified'], rid
        assert item['codec'] == 'h264' and item['pix_fmt'] == 'yuv420p', rid
        assert abs(item['duration_s'] - item['source_duration_s']) <= 1 / item['fps'] + .005, rid
        for kind, folder, suffix in [('video', 'videos', 'mp4'), ('poster', 'posters', 'jpg')]:
            name = f'media/{folder}/{rid}.{suffix}'
            assert item[kind + '_path'] == name, rid
            path = (source / name).resolve()
            assert path.is_relative_to(source) and path.is_file(), name
            assert sha256(path) == item[kind + '_sha256'], name
            entries.append((path, name))
    total = sum(path.stat().st_size for path, _ in entries)
    assert total < MEDIA_BUDGET, 'Browser media exceeds the Pages budget'
    assert args.bundle_url.startswith('https://github.com/wuxiyang1996/robo-si-review-assets/releases/download/'), 'Unexpected bundle host'
    archive = args.archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation keeps an already published bundle immutable.
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_STORED) as bundle:
        for path, name in entries:
            bundle.write(path, name)
    manifest['bundle'] = {'url': args.bundle_url, 'sha256': sha256(archive), 'bytes': archive.stat().st_size}
    manifest['summary'] = {'recordings': len(records), 'files': len(entries), 'media_bytes': total,
                           '1080p': sum(r['height'] == 1080 for r in records),
                           '720p': sum(r['height'] == 720 for r in records)}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'bundle': manifest['bundle'], 'summary': manifest['summary']}))


if __name__ == '__main__':
    main()
