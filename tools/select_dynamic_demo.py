"""Select an existing verified G1/UR10e rally for the two representative slots."""
from pathlib import Path
import copy,json
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
CASE='TT-R-G-U'
catalog_path=ROOT/'data/video-gallery.json'
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
record=next(r for r in catalog['records'] if r['record_id']==CASE)
assert record['speed']==8 and record['nyx_receipt_verified'] and record['full_decode_verified']
source=BeautifulSoup((ROOT/'infra/families/TT.html').read_text(encoding='utf-8'),'html.parser')
figure=source.select_one('figure[data-record="'+CASE+'"]')
assert figure and figure.select_one('video')['data-video-src']==record['video_url']
previous=catalog['category_demos']['dynamic']
for relative in ['index.html','infra/contribute-zh.html','infra/categories/dynamic.html']:
    path=ROOT/relative
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    target=soup.select_one('figure[data-record="'+previous+'"]') or soup.select_one('figure[data-record="'+CASE+'"]')
    assert target,relative
    card=target.find_parent('article')
    target.replace_with(copy.deepcopy(figure))
    label=card.select_one('.demo-description [data-zh]')
    if label:
        label['data-zh']=record['title_zh'];label['data-en']=record['title_en'];label.string=record['title_zh']
    path.write_text(str(soup),encoding='utf-8')
catalog['category_demos']['dynamic']=CASE
catalog['family_representatives']['TT']=CASE
catalog.setdefault('frozen_media_manifest_url',catalog['remote_manifest_url'])
catalog['remote_manifest_url']='https://wuxiyang1996.github.io/robo-si-results/data/video-gallery.json'
catalog['representative_selection_update']={
    'date':'2026-11-10','category':'dynamic','family':'TT','record_id':CASE,
    'reason':'G1 humanoid and UR10e arm are both clearly visible in the existing verified Nyx 8x rally.',
    'media_unchanged':True}
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'category':'dynamic','family':'TT','record_id':CASE,'media_changed':False}))
