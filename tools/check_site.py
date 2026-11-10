"""Validate the actual deploy artifact, task coverage, media identity and links."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
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
        self.family_tiles=[];self.family_filters=[];self.family_galleries=[];self.paused_families=[];self.current_family_tile=None;self.current_task_card=None;self.details=[]
        self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag in ('a','link') and a.get('href'):self.links.append(a['href'])
        if tag in ('img','script') and a.get('src'):self.links.append(a['src'])
        if tag=='video':self.videos.append(a)
        if a.get('data-timeline'):self.timelines.append(a['data-timeline'])
        if tag=='img':self.images.append(a)
        if tag=='a' and 'data-family-card' in a:
            self.current_family_tile={**a,'images':[]};self.family_tiles.append(self.current_family_tile)
        if tag=='img' and self.current_family_tile is not None:self.current_family_tile['images'].append(a)
        if tag=='button' and 'data-family-filter' in a:self.family_filters.append(a)
        if 'data-family-gallery' in a:self.family_galleries.append(a)
        if 'data-paused-family' in a:self.paused_families.append(a)
        if tag=='figure' and a.get('data-record'):self.figures.append(a['data-record'])
        if tag=='article' and 'task-card' in a.get('class','').split():
            self.current_task_card={**a,'text':[]};self.cards.append(self.current_task_card)
        if tag=='details':self.details.append(a)
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href')
        if tag=='h1':self.headings.append(tag)
        if tag in ('script','style'):self.ignored+=1
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag=='a':self.current_family_tile=None
        if tag=='article':self.current_task_card=None
        if tag in ('script','style'):self.ignored=max(0,self.ignored-1)
    def handle_data(self,data):
        if not self.ignored:
            self.text.append(data)
            if self.current_task_card is not None:self.current_task_card['text'].append(data)

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
        for k in ('title_zh','title_en','description_zh','description_en','goal_zh','goal_en'):
            require(bool(t.get(k,'')),f'{rid}: empty {k}')
            require('???' not in t.get(k,'') and '\ufffd' not in t.get(k,''),f'{rid}: damaged text in {k}')
        require(bool(re.search(r'[\u4e00-\u9fff]',t.get('description_zh',''))),f'{rid}: missing Chinese description')
        require(len(t.get('description_zh',''))>=30,f'{rid}: insufficient task description')
        require(bool(t.get('scope_zh'))==bool(t.get('scope_en')),f'{rid}: demonstrated scope must be bilingual when present')
        require(bool(re.search(r'[\u4e00-\u9fff]',t.get('goal_zh',''))),f'{rid}: missing Chinese goal')
        conditions_zh=t.get('conditions_zh');conditions_en=t.get('conditions_en')
        valid_conditions=isinstance(conditions_zh,list) and isinstance(conditions_en,list) and bool(conditions_zh) and len(conditions_zh)==len(conditions_en)
        require(valid_conditions,f'{rid}: scene constraints need matching nonempty bilingual arrays')
        if valid_conditions:
            require(all(isinstance(x,str) and x.strip() and '???' not in x and '\ufffd' not in x for x in conditions_zh+conditions_en),f'{rid}: empty or damaged constraint')
        require(bool(t.get('robots')),f'{rid}: missing robot filter labels')
        require(bool(t.get('tags')),f'{rid}: missing task keywords')
        require(all(tag in config['tag_labels'] for tag in t.get('tags',[])),f'{rid}: task keyword is outside the shared bilingual vocabulary')
        if records[rid].get('accepted_exit'):
            require(any(x in t.get('goal_zh','')+t.get('scope_zh','') for x in ('退出','停止','不可行')),f'{rid}: displayed safe-exit goal omitted')
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
        require(not any(x in text for x in ['最终交付 Nyx','研究提案 · v6','相对 v5 的变化','任务说明正在整理','任务条件与原始记录','任务标识与原始记录','任务链接']),f'{rel}: legacy version clutter or record-link label remains')
        require(not any('task-details' in d.get('class','').split() for d in doc.details),f'{rel}: task details still hide the former record-link panel')
        require('???' not in text and '\ufffd' not in text,f'{rel}: damaged displayed text')
        for image in doc.images:
            require('alt' in image,f'{rel}: image missing alt attribute')
            if 'poster' in image.get('class','').split():
                require(bool(image.get('alt')),f'{rel}: video poster missing a task description')
        require(len(doc.figures)==len(doc.videos),f'{rel}: video players have missing recording identifiers')
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
            require(url.netloc!='robo-si-review.wuxiyang.chatgpt.site',f'{rel}: current page links to the retired parallel site')
            if url.netloc!='wuxiyang1996.github.io' or not url.path.startswith(PREFIX):continue
            path=unquote(url.path[len(PREFIX):])
            if not path or path.endswith('/'):path+='index.html'
            require(not path.startswith('archive/') and path!='archive.html',f'{rel}: current page still links to an archive')
            target=root/path
            references+=1
            require(target.is_file(),f'{rel}: missing local target {path}')
            if path.endswith('.html'):require(path in build['active_pages'],f'{rel}: current navigation points to an old HTML route: {path}')
            if url.fragment and target.is_file() and path.endswith('.html'):
                if path not in docs:docs[path]=Document(target)
                require(unquote(url.fragment) in docs[path].ids,f'{rel}: missing anchor {path}#{url.fragment}')
    family_categories={fid:c['id'] for c in index['categories'] for fid in c['families']}
    recorded_families={r['family'] for r in records.values()}
    category_ids={c['id'] for c in index['categories']}
    def check_family_tiles(rel,expected):
        doc=docs[rel];ids=[tile.get('data-family-card') for tile in doc.family_tiles]
        require(set(ids)==set(expected) and len(ids)==len(expected),f'{rel}: family thumbnails must cover each recorded family exactly once')
        for tile in doc.family_tiles:
            fid=tile.get('data-family-card');rid=tile.get('data-preview-record');record=records.get(rid)
            require('family-tile' in tile.get('class','').split(),f'{rel}: family thumbnail is missing its card class')
            require(tile.get('href')==PREFIX+'tasks/families/'+str(fid)+'.html',f'{rel}: thumbnail must link directly to its family videos')
            require(tile.get('data-family-category')==family_categories.get(fid),f'{rel}: wrong thumbnail category for {fid}')
            require(rid==catalog['family_representatives'].get(fid) and record is not None,f'{rel}: wrong representative recording for {fid}')
            images=tile['images']
            require(len(images)==1,f'{rel}: expected one thumbnail image for {fid}')
            if record and len(images)==1:
                require(record['family']==fid and images[0].get('src')==record['poster_url'],f'{rel}: thumbnail does not match the verified family representative')
        return doc
    for rel in ('index.html','tasks/index.html'):
        doc=check_family_tiles(rel,recorded_families)
        require(not doc.videos,f'{rel}: family entry gallery should use linked thumbnails, not inline players')
        require(len(doc.family_galleries)==1 and doc.family_galleries[0].get('data-default-category')=='access',f'{rel}: missing shared category gallery')
        filters=[f.get('data-family-filter') for f in doc.family_filters]
        require(set(filters)==category_ids|{'all'} and len(filters)==7,f'{rel}: expected all and six category filter buttons')
        require(all(f.get('type')=='button' and f.get('aria-pressed') in ('true','false') for f in doc.family_filters),f'{rel}: category filters need native button semantics and pressed state')
        require(sum(f.get('aria-pressed')=='true' for f in doc.family_filters)==1,f'{rel}: exactly one category filter should be selected')
        require(len(doc.paused_families)==1 and doc.paused_families[0].get('data-paused-family')=='F3' and doc.paused_families[0].get('data-family-category')=='deformable',f'{rel}: paused F3 must remain separate from video thumbnails')
    for category in index['categories']:
        rel='tasks/categories/'+category['id']+'.html'
        if len(category['families'])>1:
            doc=check_family_tiles(rel,recorded_families.intersection(category['families']))
            require(not doc.videos and not doc.family_filters,f'{rel}: category should link to family videos without duplicate filters or players')
    dynamic=next(c for c in index['categories'] if c['id']=='dynamic')
    require(dynamic['demo']=='TT-R-G-U' and catalog['family_representatives'].get('TT')=='TT-R-G-U','Incorrect arm-versus-humanoid demonstration.')
    seen=Counter()
    for fid in index['families']:
        doc=docs['tasks/families/'+fid+'.html']
        seen.update(c['id'] for c in doc.cards)
        expected={rid for rid,r in records.items() if r['family']==fid}
        require(set(doc.figures)==expected and len(doc.figures)==len(expected),f'{fid}: family video players must preserve every recording exactly once')
        for card in doc.cards:
            task=index['tasks'].get(card['id'],{});displayed=' '.join(card['text'])
            require(task.get('goal_zh','') in displayed,f'{card["id"]}: goal is not shown on the current task card')
            for condition in task.get('conditions_zh',[]):require(condition in displayed,f'{card["id"]}: a scene constraint is not shown')
            require(task.get('scope_zh','') in displayed,f'{card["id"]}: demonstrated scope is not shown')
    require(set(seen)==set(records) and all(n==1 for n in seen.values()),'Family galleries must include every recording exactly once.')
    page_sources=json.loads((REPO/'site/content/pages.json').read_text(encoding='utf-8'))
    require('archive.html' not in build['active_pages'],'The archive must not remain a current content page.')
    for name in ('research','guide'):
        source=page_sources[name];generated=(root/(name+'.html')).read_text(encoding='utf-8')
        for section in source['sections']:
            for block in section.get('blocks',[]):
                kind=block.get('type')
                require(kind in ('code','table','list','note','paragraph'),f'{name}: unknown document block type {kind}')
                if kind=='code':
                    require(bool(block.get('text','').strip()),f'{name}: empty code example')
                    require('<pre><code>'+escape(block.get('text',''))+'</code></pre>' in generated,f'{name}: code example is missing or not HTML-escaped')
                elif kind=='list':
                    require(bool(block.get('items_zh')) and len(block.get('items_zh',[]))==len(block.get('items_en',[])),f'{name}: bilingual list length mismatch')
                elif kind=='table':
                    columns=len(block.get('columns_zh',[]))
                    require(columns>0 and columns==len(block.get('columns_en',[])),f'{name}: bilingual table column mismatch')
                    require(bool(block.get('rows_zh')) and len(block.get('rows_zh',[]))==len(block.get('rows_en',[])),f'{name}: bilingual table row mismatch')
                    require(all(len(row)==columns for row in block.get('rows_zh',[])+block.get('rows_en',[])),f'{name}: inconsistent table row width')
                elif kind in ('note','paragraph'):
                    require(bool(block.get('text_zh')) and bool(block.get('text_en')),f'{name}: missing bilingual block text')
    require('download' in docs['guide.html'].ids,'The usage guide must retain its download anchor.')
    routes=json.loads((root/'data/legacy-routes.json').read_text(encoding='utf-8'))
    require(build.get('archived_html')==0,'Archived HTML content must not be published.')
    require(build.get('legacy_redirects')==len(routes),'Legacy redirect count does not match its manifest.')
    active=set(build['active_pages'])
    for path,route in routes.items():
        target=route.get('target','');parts=urlsplit(target)
        target_path=parts.path or 'index.html'
        if target_path.endswith('/'):target_path+='index.html'
        require(not parts.scheme and not parts.netloc and not parts.query and not parts.fragment and target_path in active,f'{path}: redirect target is not a current page')
        stub=root/path
        require(stub.is_file(),f'{path}: missing legacy redirect')
        if not stub.is_file():continue
        doc=Document(stub);raw=stub.read_text(encoding='utf-8')
        require(doc.canonical==BASE+target,f'{path}: redirect canonical differs from its current target')
        require(doc.links==[BASE+target,PREFIX+target],f'{path}: redirect retains links beyond its current destination')
        require(doc.meta.get('robots')=='noindex,follow',f'{path}: redirect must not be indexed')
        require(not doc.videos and not doc.images and not doc.cards and not doc.timelines and len(raw)<12000,f'{path}: legacy redirect contains old content or media')
        require('location.replace(' in raw and 'aliases=' in raw,f'{path}: redirect does not preserve task aliases')
        for old_id,new_id in route.get('aliases',{}).items():
            require(isinstance(old_id,str) and bool(old_id),f'{path}: invalid task alias')
            require(new_id in records,f'{path}: alias points to unknown recording {new_id}')
            require(target_path in docs and new_id in docs[target_path].ids,f'{path}: alias target is absent from its current page')
    for path in ('archive-m4-20261104.html','archive/pages/archive-m4-20261104.html'):
        route=routes.get(path,{})
        require(route.get('target')=='tasks/families/M4.html',f'{path}: M4 old route must open the current M4 family')
        require(route.get('aliases',{}).get('M4-01')=='M4-01',f'{path}: M4-01 alias is not preserved')
    published_html={p.relative_to(root).as_posix() for p in root.rglob('*.html')}
    require(published_html==active|set(routes),'Published HTML includes unregistered old content or missing current routes.')
    for obsolete in ('data/archive-files.json','data/archive-build.json','assets/archive','archive/assets'):
        require(not (root/obsolete).exists(),f'Obsolete archive asset remains: {obsolete}')
    require(not list(root.rglob('*.mp4')),'Historical video binaries were accidentally included in the Pages artifact.')
    files=[p for p in root.rglob('*') if p.is_file()]
    require(len(files)<1500,'Pages artifact contains excessive files.')
    require(sum(p.stat().st_size for p in files)<15*1024*1024,'Pages artifact exceeds the focused current-site footprint.')
    report={'passed':not errors,'errors':errors,'unique_recordings':len(records),'task_families':len(families),'categories':len(index['categories']),'active_pages':len(build['active_pages']),'local_links_checked':references,'archived_html':build.get('archived_html'),'legacy_redirects_checked':len(routes),'media_manifest_unchanged':(root/'data/video-gallery.json').read_bytes()==(REPO/'data/video-gallery.json').read_bytes(),'browser_visual_qa':'separately recorded; not inferred from static checks'}
    (root/'data/site-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)

if __name__=='__main__':main()
