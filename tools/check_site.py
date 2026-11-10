"""Validate the actual deploy artifact, task coverage, media identity and links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
from collections import Counter
import argparse
import hashlib
import json
import re

REPO=Path(__file__).resolve().parents[1]
PREFIX='/robo-si-results/'
BASE='https://wuxiyang1996.github.io'+PREFIX

class Document(HTMLParser):
    def __init__(self,path):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.links=[];self.videos=[];self.figures=[];self.cards=[];self.images=[];self.headings=[];self.text=[];self.meta={};self.timelines=[];self.canonical=None;self.ignored=0
        self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag in ('a','link') and a.get('href'):self.links.append(a['href'])
        if tag in ('img','script') and a.get('src'):self.links.append(a['src'])
        if tag=='video':self.videos.append(a)
        if a.get('data-timeline'):self.timelines.append(a['data-timeline'])
        if tag=='img':self.images.append(a)
        if tag=='figure' and a.get('data-record'):self.figures.append(a['data-record'])
        if tag=='article' and 'task-card' in a.get('class','').split():self.cards.append(a)
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href')
        if tag=='h1':self.headings.append(tag)
        if tag in ('script','style'):self.ignored+=1
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.ignored=max(0,self.ignored-1)
    def handle_data(self,data):
        if not self.ignored:self.text.append(data)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=REPO/'dist');args=ap.parse_args()
    root=args.root.resolve();errors=[]
    def require(ok,message):
        if not ok:errors.append(message)
    build=json.loads((root/'data/site-build.json').read_text(encoding='utf-8'))
    config=json.loads((REPO/'site/content/site.json').read_text(encoding='utf-8'))
    index=json.loads((root/'data/task-index.json').read_text(encoding='utf-8'))
    catalog=json.loads((REPO/'data/video-gallery.json').read_text(encoding='utf-8'))
    records={r['record_id']:r for r in catalog['records']}
    require(build['editorial_complete'],'Build contains preview-only incomplete content.')
    require(len(index['tasks'])==len(records)==246,'Expected 246 task records.')
    require(set(index['tasks'])==set(records),'Editorial record IDs differ from original recordings.')
    require(len(index['families'])==30 and len(index['categories'])==6,'Expected 30 families and six categories.')
    require('???' not in json.dumps(index,ensure_ascii=False),'Damaged text appears in the site content index.')
    families=[f for c in index['categories'] for f in c['families']]
    require(set(families)==set(index['families']) and len(families)==30,'Each family must appear in exactly one primary category.')
    require((root/'data/video-gallery.json').read_bytes()==(REPO/'data/video-gallery.json').read_bytes(),'Original media manifest changed in the build.')
    require(all(r['speed']==8 and r['nyx_receipt_verified'] and r['full_decode_verified'] for r in records.values()),'Unverified media in the catalog.')
    descriptions=[]
    for rid,t in index['tasks'].items():
        for k in ('title_zh','title_en','description_zh','description_en'):
            require(bool(t.get(k,'')),f'{rid}: empty {k}')
            require('???' not in t.get(k,'') and '\ufffd' not in t.get(k,''),f'{rid}: damaged text in {k}')
        require(bool(re.search(r'[\u4e00-\u9fff]',t.get('description_zh',''))),f'{rid}: missing Chinese description')
        require(len(t.get('description_zh',''))>=30,f'{rid}: insufficient task description')
        require(bool(t.get('robots')),f'{rid}: missing robot filter labels')
        require(bool(t.get('tags')),f'{rid}: missing task keywords')
        require(all(tag in config['tag_labels'] for tag in t.get('tags',[])),f'{rid}: task keyword is outside the shared bilingual vocabulary')
        if records[rid].get('accepted_exit'):
            require(any(x in t['description_zh']+t.get('scope_zh','') for x in ('退出','停止','不可行')),f'{rid}: safe-exit goal omitted')
        descriptions.append(t['description_zh'])
    require(len(descriptions)==len(set(descriptions)),'Descriptions must be case-specific, not duplicated.')
    docs={};references=0
    for rel in build['active_pages']:
        path=root/rel;require(path.is_file(),f'Missing active page {rel}')
        if not path.exists():continue
        doc=Document(path);docs[rel]=doc
        require(len(doc.headings)==1,f'{rel}: expected exactly one h1')
        require(len(doc.ids)==len(set(doc.ids)),f'{rel}: duplicate HTML IDs')
        require(bool(doc.canonical),f'{rel}: no canonical URL')
        require(bool(doc.meta.get('description')),f'{rel}: no description')
        require(bool(doc.meta.get('keywords')),f'{rel}: no keywords')
        require(bool(doc.meta.get('og:image')),f'{rel}: no sharing poster')
        text=' '.join(doc.text)
        require(not any(x in text for x in ['最终交付 Nyx','研究提案 · v6','相对 v5 的变化','任务说明正在整理']),f'{rel}: legacy version clutter or placeholder remains')
        require('???' not in text and '\ufffd' not in text,f'{rel}: damaged displayed text')
        for image in doc.images:require(bool(image.get('alt')),f'{rel}: image missing alt')
        for figure,video in zip(doc.figures,doc.videos):
            r=records.get(figure)
            require(r is not None,f'{rel}: unknown video {figure}')
            if r:
                require(video.get('data-video-src')==r['video_url'] and video.get('poster')==r['poster_url'],f'{rel}: altered video or poster for {figure}')
            require('autoplay' not in video and video.get('preload')=='none',f'{rel}: video eagerly loaded or autoplaying')
            require(video.get('tabindex')=='-1',f'{rel}: hidden video can receive keyboard focus')
    for rel,doc in list(docs.items()):
        for value in doc.links:
            url=urlsplit(urljoin(BASE+rel,value))
            if url.netloc!='wuxiyang1996.github.io' or not url.path.startswith(PREFIX):continue
            path=unquote(url.path[len(PREFIX):])
            if not path or path.endswith('/'):path+='index.html'
            target=root/path
            references+=1
            require(target.is_file(),f'{rel}: missing local target {path}')
            if url.fragment and target.is_file() and path.endswith('.html'):
                if path not in docs:docs[path]=Document(target)
                require(unquote(url.fragment) in docs[path].ids,f'{rel}: missing anchor {path}#{url.fragment}')
    home=docs['index.html']
    require(len(home.figures)==6,'Homepage must have six category demonstrations.')
    dynamic=next(c for c in index['categories'] if c['id']=='dynamic')
    require(dynamic['demo']=='TT-R-G-U' and 'TT-R-G-U' in home.figures,'Incorrect arm-versus-humanoid demonstration.')
    seen=Counter()
    for fid in index['families']:
        doc=docs['tasks/families/'+fid+'.html']
        seen.update(c['id'] for c in doc.cards)
    require(set(seen)==set(records) and all(n==1 for n in seen.values()),'Family galleries must include every recording exactly once.')
    archive=json.loads((root/'data/archive-files.json').read_text(encoding='utf-8'))
    require(archive['baseline_commit']==build['archive_commit'],'Archive baseline mismatch.')
    timeline_count=0
    for path in archive['original_html_sha256']:
        require((root/'archive/pages'/path).is_file(),f'Missing archived page {path}')
        archived=Document(root/'archive/pages'/path)
        for timeline in archived.timelines:
            timeline_count+=1
            raw_prefix='https://raw.githubusercontent.com/wuxiyang1996/robo-si-results/'+archive['baseline_commit']+'/'
            require(timeline.startswith(raw_prefix),f'{path}: archive timeline still uses a broken relative path')
            if timeline.startswith(raw_prefix):require(unquote(timeline[len(raw_prefix):]) in archive['files'],f'{path}: archive timeline source missing')
    require(not list(root.rglob('*.mp4')),'Historical video binaries were accidentally included in the Pages artifact.')
    files=[p for p in root.rglob('*') if p.is_file()]
    require(len(files)<1500,'Pages artifact contains excessive files.')
    require(sum(p.stat().st_size for p in files)<50*1024*1024,'Pages artifact exceeds the planned footprint.')
    report={'passed':not errors,'errors':errors,'unique_recordings':len(records),'task_families':len(families),'categories':len(index['categories']),'active_pages':len(build['active_pages']),'local_links_checked':references,'archived_html':len(archive['original_html_sha256']),'archive_timelines_checked':timeline_count,'media_manifest_unchanged':(root/'data/video-gallery.json').read_bytes()==(REPO/'data/video-gallery.json').read_bytes(),'historical_unresolved_links':len(archive['historical_unresolved_links']),'browser_visual_qa':'separately recorded; not inferred from static checks'}
    (root/'data/site-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)

if __name__=='__main__':main()
