"""Apply verified H1 media receipts to the gallery; keep the prior public pins."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--media-dir', type=Path, required=True)
    ap.add_argument('--release-base', required=True)
    ap.add_argument('--review', type=Path, required=True)
    args = ap.parse_args()
    review = json.loads(args.review.read_text(encoding='utf-8'))
    catalog_path = ROOT/'data/video-gallery.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    by_id = {r['record_id']:r for r in catalog['records']}
    replacements = {}
    for item in review['cases']:
        case = item['case']
        receipt = json.loads((args.media_dir/(case+'.json')).read_text(encoding='utf-8'))
        assert receipt['verification']['passed'] and item['visual_review_passed']
        record = by_id[case]
        record.setdefault('previous_public_media', {
            k: record[k] for k in ('video_url','poster_url','source_8x_sha256',
                                   'web_sha256','poster_sha256','nyx_receipt_sha256')})
        for key, ext in [('video_url','mp4'),('poster_url','jpg')]:
            url = args.release_base.rstrip('/')+'/'+case+'.'+ext
            replacements[record[key]] = url
            record[key] = url
        before = receipt['input_metadata']; after = receipt['output_metadata']
        record.update(source_8x_sha256=receipt['source_sha256'],
            source_8x_duration_s=before['duration_s'],source_8x_frames=before['frames'],
            web_sha256=receipt['output_sha256'],poster_sha256=receipt['poster_sha256'],
            web_frames=after['frames'],web_duration_s=after['duration_s'],
            web_fps=after['fps'],web_resolution=after['resolution'],
            all_presentation_timestamps_preserved=True,full_decode_verified=True,
            nyx_receipt_verified=True,nyx_audited_video_sha256=receipt['source_sha256'],
            nyx_receipt_sha256=receipt['nyx_receipt_sha256'],
            asset_review_status='fine_grained_assets_rerendered_visually_reviewed',
            nyx_render_completed_at_utc=datetime.fromtimestamp(
                Path(receipt['render_path'],'full-fixed.mp4').stat().st_mtime, timezone.utc).isoformat(),
            completion_time_evidence='new render file completion mtime; not a signed timestamp',
            latest_scope='New reviewed H1 fine-grained display render; original physical record and camera retained.',
            fine_grained_update=item)
    for folder in [ROOT/'infra', ROOT/'doc']:
        for path in folder.rglob('*.html'):
            text = path.read_text(encoding='utf-8')
            for old,new in replacements.items(): text=text.replace(old,new)
            path.write_text(text,encoding='utf-8')
    h1 = ROOT/'infra/families/H1.html'
    soup = BeautifulSoup(h1.read_text(encoding='utf-8'),'html.parser')
    for item in review['cases']:
        figure = soup.select_one('figure[data-record="'+item['case']+'"]')
        card = figure.find_parent('article')
        caption = figure.select_one('figcaption [data-zh]')
        caption['data-zh']='精细素材更新 · Nyx · 8×'
        caption['data-en']='Detailed assets · Nyx · 8×'
        caption.string=caption['data-zh']
        note=soup.new_tag('p',attrs={'class':'asset-update-note','data-zh':item['note_zh'],'data-en':item['note_en']})
        note.string=item['note_zh']
        old_note=card.select_one('.asset-update-note')
        if old_note:old_note.replace_with(note)
        else:card.select_one('.record-details').append(note)
    h1.write_text(str(soup),encoding='utf-8')
    catalog['fine_grained_h1_update']=review
    catalog.setdefault('baseline_nyx_asset_audit',catalog['nyx_asset_audit'])
    catalog['nyx_asset_audit']={
        'all_verified':True,'records':len(catalog['records']),
        'fine_grained_h1_revision_records':len(review['cases']),
        'baseline_audit_sha256':catalog['baseline_nyx_asset_audit']['audit_sha256'],
        'scope':'Baseline source verification plus the separately reviewed H1 detailed-asset revision; per-record metadata is authoritative.'}
    catalog['remote_media']['supplemental_release_base']=args.release_base
    catalog['previous_manifest_url']=catalog['remote_manifest_url']
    catalog['remote_manifest_url']=args.release_base.rstrip('/')+'/video-gallery.json'
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/h1-fine-grained-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
    # Root is the generated home, not a stale separate copy.
    (ROOT/'index.html').write_bytes((ROOT/'infra/contribute-zh.html').read_bytes())
    print(json.dumps({'updated_records':len(review['cases']),'total_records':len(by_id)}))

if __name__ == '__main__': main()
