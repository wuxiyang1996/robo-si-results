"""Build the research site, galleries and explicit historical redirects.

Uses only the Python standard library. Editorial content is separate from the
immutable recording manifest; a normal build refuses incomplete task copy.
"""
from pathlib import Path
from html import escape
from urllib.parse import quote, urlsplit
from collections import Counter
import argparse
import hashlib
import json
import shutil
import subprocess
from archive_site import build_archive

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'site'
OUT = ROOT / 'dist'
CONFIG = json.loads((SOURCE / 'content/site.json').read_text(encoding='utf-8'))
CATALOG = json.loads((ROOT / 'data/video-gallery.json').read_text(encoding='utf-8'))
RECORDS = {r['record_id']: r for r in CATALOG['records']}
PREFIX = CONFIG['base_path']
BASE = CONFIG['base_url']
FAMILIES = {}
TASKS = {}
PAGES = {}
ACTIVE = []
COUNTS = Counter(r['family'] for r in RECORDS.values())
BY_CATEGORY = {f: c for c in CONFIG['categories'] for f in c['families']}

def e(value): return escape(str(value), quote=True)
def tr(zh, en, tag='span', extra=''):
    return f'<{tag} data-zh="{e(zh)}" data-en="{e(en)}" {extra}>{escape(zh)}</{tag}>'
def local(path): return PREFIX + path.lstrip('/')
def link(path, zh, en, cls='text-link'):
    return f'<a class="{cls}" data-local href="{e(local(path))}">{tr(zh,en)}</a>'
def external(url, zh, en, cls='text-link'):
    return f'<a class="{cls}" href="{e(url)}">{tr(zh,en)}</a>'
def family_url(fid): return 'tasks/families/' + fid + '.html'
def category_url(cid): return 'tasks/categories/' + cid + '.html'

def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

def header(active):
    nav = [('research.html','研究问题','Research','research'),('tasks/','任务图集','Tasks','tasks'),('guide.html','使用与下载','Get started','guide')]
    items = ''.join(f'<a data-local href="{local(path)}"'+(' aria-current="page"' if key==active else '')+'>'+tr(zh,en)+'</a>' for path,zh,en,key in nav)
    return f'''<a class="skip-link" href="#main">{tr('跳到正文','Skip to content')}</a>
    <header class="site-nav"><div class="wrap nav-inner"><a class="brand" data-local href="{PREFIX}">Embodied Terminal-Bench<small>ROBO-SI</small></a>
    <nav class="main-nav" aria-label="主导航 / Main navigation">{items}<a href="https://github.com/wuxiyang1996/robo-si-results">GitHub ↗</a></nav>
    <button class="language-toggle" id="language-toggle" type="button" lang="en" aria-label="Switch to English">English</button></div></header>'''

def footer():
    return f'''<footer class="footer"><div class="wrap footer-inner"><div><p class="footer-brand">Embodied Terminal-Bench</p><p>{tr('物理工具使用、能力判断与机器人编程','Physical tool use, capability awareness and robot programming')}</p></div>
    <div class="footer-links">{link('research.html','研究问题','Research','')}{link('guide.html','使用与下载','Get started','')}{link('archive.html','历史与证据','Archive & evidence','')}<a href="https://github.com/wuxiyang1996/robo-si-results">GitHub</a></div></div></footer>'''

def page(path, title_zh, title_en, description, body, active='tasks', image=None, keywords=None):
    title_zh += ' · Embodied Terminal-Bench'
    title_en += ' · Embodied Terminal-Bench'
    canonical = BASE + ('' if path == 'index.html' else path.replace('/index.html','/'))
    poster = image or RECORDS[CONFIG['categories'][0]['demo']]['poster_url']
    words = CONFIG['keywords_zh'] + CONFIG['keywords_en'] + (keywords or [])
    indexing='<meta name="robots" content="noindex,follow">' if path in ('404.html','tasks/search.html') else ''
    text = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title data-zh="{e(title_zh)}" data-en="{e(title_en)}">{escape(title_zh)}</title><meta name="description" content="{e(description)}"><meta name="keywords" content="{e(', '.join(dict.fromkeys(words)))}">
    <meta name="theme-color" content="#faf7f3"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:site_name" content="Embodied Terminal-Bench"><meta property="og:title" content="{e(title_zh)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{e(poster)}"><meta name="twitter:card" content="summary_large_image">
    {indexing}<link rel="stylesheet" href="{local('assets/site.css')}"><script defer src="{local('assets/site.js')}"></script></head><body>
    {header(active)}<main id="main">{body}</main>{footer()}</body></html>'''
    write(path, text)
    ACTIVE.append(path)

def breadcrumbs(parts):
    items = [link('', '首页','Home','')]
    for path,zh,en in parts:
        items.append('<span aria-hidden="true">/</span>' + (link(path,zh,en,'') if path else tr(zh,en)))
    return '<nav class="wrap breadcrumbs" aria-label="当前位置 / Breadcrumb">'+''.join(items)+'</nav>'

def player(record_id):
    r = RECORDS[record_id]
    task = TASKS.get(record_id, r)
    zh,en = task['title_zh'],task['title_en']
    return f'''<figure class="player" data-record="{e(record_id)}" data-state="poster"><video controls playsinline preload="none" tabindex="-1" data-video-src="{e(r['video_url'])}" poster="{e(r['poster_url'])}" aria-label="{e(zh)}" data-label-zh="{e(zh)}" data-label-en="{e(en)}"></video>
    <button class="video-start" data-play-video type="button" aria-label="播放：{e(zh)}" data-label-zh="播放：{e(zh)}" data-label-en="Play: {e(en)}"><img class="poster" src="{e(r['poster_url'])}" alt="{e(zh)}" loading="lazy" decoding="async" width="960" height="540"><span class="play-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path fill="currentColor" d="M4 2L18 10 4 18Z"/></svg></span></button><span class="speed">8×</span>
    <p class="video-status" hidden role="status">{tr('视频暂时无法加载。','The video could not load.')} <a href="{e(r['video_url'])}">{tr('打开视频文件','Open video file')}</a></p>
    <noscript><p class="video-status"><a href="{e(r['video_url'])}">{tr('打开视频','Open video')}</a></p></noscript></figure>'''

def robots(values):
    return '<div class="robots">'+''.join('<span>'+e(x)+'</span>' for x in values)+'</div>'

def gallery_note():
    return '<p class="gallery-note">'+tr('视频展示物理仿真中的参考执行。各任务的简化条件和完成范围随录像说明，不能据此推算新 agent 的成功率。','Videos show reference executions in physics simulation. Each task states its conditions and demonstrated scope; these are not success rates for a new agent.')+'</p>'

def cta():
    return f'''<section class="bottom-cta"><div class="wrap cta-inner"><div>{tr('从一个任务开始','Start with one task','h2')}{tr('下载环境，接入 agent，再看执行记录和评分。','Download the environment, connect an agent, and inspect execution and scores.','p')}</div><div class="hero-actions">{link('guide.html','使用与下载','Get started','button')}{link('research.html','阅读研究问题','Read the research')}</div></div></section>'''

def home():
    contributions=''.join(f'<article class="contribution"><span class="number">0{i}</span><div>{tr(x["title_zh"],x["title_en"],"h2")}{tr(x["body_zh"],x["body_en"],"p")}</div></article>' for i,x in enumerate(CONFIG['contributions'],1))
    cards=[]
    for c in CONFIG['categories']:
        count=sum(COUNTS[f] for f in c['families'])
        family_count=sum(COUNTS[f]>0 for f in c['families'])
        cards.append(f'''<article class="category-card" data-category="{c['id']}">{player(c['demo'])}<div class="card-topline"><h3>{link(category_url(c['id']),c['title_zh'],c['title_en'],'')}</h3><span class="card-number">{c['number']}</span></div>{tr(c['description_zh'],c['description_en'],'p','class="card-description"')}<div class="card-footer"><span>{tr(f'{family_count} 个任务族 · {count} 段录像',f'{family_count} families · {count} recordings')}</span>{link(category_url(c['id']),'查看任务','Explore tasks')}</div>{tr(c['demo_zh'],c['demo_en'],'p','class="demo-caption"')}</article>''')
    body=f'''<section class="hero"><div class="wrap"><p class="eyebrow">CODE · EXPERIMENT · PHYSICAL ACTION</p>{tr(CONFIG['research_question_zh'],CONFIG['research_question_en'],'h1')}{tr(CONFIG['intro_zh'],CONFIG['intro_en'],'p','class="lead"')}<div class="hero-actions">{link('#categories','观看任务演示','Explore the tasks','button')}{link('research.html','阅读研究问题','Read the research')}</div></div></section>
    <div class="wrap"><div class="contributions">{contributions}</div></div><section class="section" id="categories"><div class="wrap"><div class="section-head"><div><p class="eyebrow">THE TASK GALLERY</p>{tr('六种物理难题','Six kinds of physical challenge','h2')}{tr('从一段演示进入，看看机器人要解决什么。','Start with a demonstration, then explore the problem behind it.','p')}</div>{link('tasks/','浏览全部任务','Browse all tasks')}</div><div class="gallery">{''.join(cards)}</div>{gallery_note()}</div></section>{cta()}'''
    page('index.html',CONFIG['research_question_zh'],CONFIG['research_question_en'],CONFIG['intro_zh'],body,active='home')

def family_card(fid):
    f=FAMILIES[fid]
    rid=CATALOG['family_representatives'].get(fid)
    if not rid or rid not in RECORDS: return ''
    return f'''<article class="family-card">{player(rid)}<div class="card-topline"><h2>{link(family_url(fid),f['title_zh'],f['title_en'],'')}</h2><span class="family-code">{fid}</span></div>{tr(f['intro_zh'],f['intro_en'],'p','class="card-description"')}<div class="card-footer">{robots(f['robots'])}{link(family_url(fid),f'查看 {COUNTS[fid]} 个任务',f'View {COUNTS[fid]} tasks')}</div></article>'''

def task_card(r):
    rid=r['record_id']; t=TASKS[rid]
    all_text=' '.join([rid,*r.get('public_case_ids',[]),t['title_zh'],t['title_en'],t['description_zh'],t['description_en'],*t['robots'],*t['tags'],FAMILIES[r['family']]['title_zh'],r['family']])
    scope=(tr(t.get('scope_zh',''),t.get('scope_en',''),'p','class="scope"') if t.get('scope_zh') else '')
    outcome=('<span class="outcome">'+tr('安全退出','Safe exit')+'</span>') if r.get('accepted_exit') else ''
    original=r.get('historical_source_original_url',r['source_page'])
    source_path=urlsplit(r['source_page']).path.split('/')[-1]
    fragment=urlsplit(original).fragment or rid
    original_page='archive/pages/'+source_path+'#'+quote(fragment,safe='.-')
    aliases=''.join(f'<span id="{e(alias)}"></span>' for alias in r.get('public_case_ids',[]) if alias!=rid)
    return f'''<article class="task-card" id="{e(rid)}" data-filter-card data-search="{e(all_text)}" data-robots="{e('|'.join(t['robots']))}" data-tags="{e('|'.join(t['tags']))}" data-outcome="{'exit' if r.get('accepted_exit') else 'execution'}">{aliases}{player(rid)}{tr(t['title_zh'],t['title_en'],'h2')}{tr(t['description_zh'],t['description_en'],'p','class="task-description"')}<div class="task-meta">{robots(t['robots'])}{outcome}</div>{scope}<details class="task-details"><summary>{tr('任务标识与原始记录','Task ID & original record')}</summary><p class="task-id">{e(' · '.join(r.get('public_case_ids',[rid])))}</p><div class="detail-links">{link(original_page,'任务条件与原始记录','Original task conditions')}{external(r['video_url'],'打开视频文件','Open video file')}{link(family_url(r['family'])+'#'+rid,'任务链接','Link to task')}</div></details></article>'''

def toolbar(records):
    values=[TASKS[r['record_id']] for r in records]
    rs=sorted(set(x for t in values for x in t['robots']))
    tags=sorted(set(x for t in values for x in t['tags']))
    tag_en=CONFIG['tag_labels']
    opts=lambda values:''.join(f'<option value="{e(v)}">{e(v)}</option>' for v in values)
    tagopts=''.join(f'<option value="{e(v)}" data-zh="{e(v)}" data-en="{e(tag_en.get(v,v))}">{e(v)}</option>' for v in tags)
    return f'''<div class="toolbar"><div class="search-field"><label for="task-search">{tr('查找任务','Search')}</label><input id="task-search" type="search" placeholder="任务、机器人或关键词" data-placeholder-zh="任务、机器人或关键词" data-placeholder-en="Task, robot or keyword" aria-label="查找任务 / Search tasks"></div><select id="robot-filter" aria-label="按机器人筛选 / Filter by robot"><option value="" data-zh="全部机器人" data-en="All robots">全部机器人</option>{opts(rs)}</select><select id="tag-filter" aria-label="按任务特点筛选 / Filter by task feature"><option value="" data-zh="全部任务特点" data-en="All features">全部任务特点</option>{tagopts}</select><select id="outcome-filter" aria-label="按目标类型筛选 / Filter by target type"><option value="" data-zh="全部目标" data-en="All goals">全部目标</option><option value="execution" data-zh="操作任务" data-en="Manipulation">操作任务</option><option value="exit" data-zh="安全退出" data-en="Safe exit">安全退出</option></select><button class="reset-filter" type="button" data-reset-filter>{tr('重置','Reset')}</button><span class="filter-count" id="filter-count" role="status" aria-live="polite">{len(records)} / {len(records)}</span></div>'''

def tasks_grid(records):
    return toolbar(records)+'<div class="gallery">'+''.join(task_card(r) for r in records)+'</div><div class="empty-results" id="empty-results" hidden>'+tr('没有找到符合条件的任务。试试更短的关键词，或清除筛选。','No tasks match these filters. Try a shorter search or reset the filters.')+'</div>'

def categories():
    for c in CONFIG['categories']:
        intro=breadcrumbs([('tasks/','任务图集','Tasks'),('',c['title_zh'],c['title_en'])])+f'<section class="page-hero"><div class="wrap"><p class="eyebrow">{c["number"]} / TASK CATEGORY</p>'+tr(c['title_zh'],c['title_en'],'h1')+tr(c['description_zh'],c['description_en'],'p','class="lead"')+'</div></section>'
        if len(c['families'])==1:
            fid=c['families'][0];f=FAMILIES[fid]
            content=tr(f['intro_zh'],f['intro_en'],'p','class="card-description"')+tasks_grid([r for r in RECORDS.values() if r['family']==fid])
        else:
            content='<div class="gallery">'+''.join(family_card(f) for f in c['families'] if COUNTS[f])+'</div>'
            paused=[f for f in c['families'] if not COUNTS[f]]
            if paused:
                content+='<p class="paused-note">'+tr('另有任务设计尚无完整参考录像：','Task designs without a complete reference recording: ')+' · '.join(link(family_url(f),FAMILIES[f]['title_zh'],FAMILIES[f]['title_en'],'') for f in paused)+'</p>'
        page(category_url(c['id']),c['title_zh'],c['title_en'],c['description_zh'],intro+'<section class="section" style="padding-top:0"><div class="wrap">'+content+gallery_note()+'</div></section>',image=RECORDS[c['demo']]['poster_url'],keywords=c['families'])

def families():
    for fid,f in FAMILIES.items():
        c=BY_CATEGORY[fid];records=[r for r in RECORDS.values() if r['family']==fid]
        body=breadcrumbs([('tasks/','任务图集','Tasks'),(category_url(c['id']),c['title_zh'],c['title_en']),('',f['title_zh'],f['title_en'])])
        body+='<section class="page-hero"><div class="wrap"><p class="eyebrow">'+e(fid)+' / TASK FAMILY</p>'+tr(f['title_zh'],f['title_en'],'h1')+tr(f['intro_zh'],f['intro_en'],'p','class="lead"')+robots(f['robots'])+'</div></section>'
        content=tasks_grid(records) if records else '<div class="paused-family">'+tr('任务设计保留，研究暂停','Task design retained; research paused','h2')+tr('这项任务尚无完整目标通过验证的参考录像。设计和已有记录保留在归档中，后续恢复时再补充。','There is no reference recording that verifies the complete goal. The design and existing records remain in the archive.','p')+link('archive/pages/archive-f3-20261104.html','查看任务设计与记录','Read the design and records')+'</div>'
        body+='<section class="section" style="padding-top:0"><div class="wrap">'+content+(gallery_note() if records else '')+'</div></section>'
        page(family_url(fid),f['title_zh'],f['title_en'],f['intro_zh'],body,keywords=[fid,*f['robots'],*f['tags']])

def directory():
    cards=[]
    for c in CONFIG['categories']:
        rows=''.join('<li>'+link(family_url(f),FAMILIES[f]['title_zh'],FAMILIES[f]['title_en'],'')+'</li>' for f in c['families'] if COUNTS[f])
        cards.append(f'<section class="directory-item" id="{c["id"]}"><p class="eyebrow">{c["number"]}</p><h2>{link(category_url(c["id"]),c["title_zh"],c["title_en"],"")}</h2><ul>{rows}</ul></section>')
    form=f'<form class="toolbar" action="{local("tasks/search.html")}" method="get"><div class="search-field"><label for="global-search">{tr("查找任务","Search")}</label><input id="global-search" type="search" name="q" placeholder="任务、机器人或关键词" data-placeholder-zh="任务、机器人或关键词" data-placeholder-en="Task, robot or keyword"></div><input type="hidden" name="lang" value="zh"><button class="button" type="submit">{tr("搜索全部任务","Search all tasks")}</button></form>'
    body=breadcrumbs([('','任务图集','Tasks')])+'<section class="page-hero"><div class="wrap"><p class="eyebrow">TASK GALLERY</p>'+tr('从你关心的问题开始','Find the problem you care about','h1')+tr('按物理难点浏览六类任务，也可以直接搜索机器人、工具或任务名称。','Browse six categories of physical challenge, or search for a robot, tool or task.','p','class="lead"')+'</div></section><section class="section" style="padding-top:0"><div class="wrap">'+form+'<div class="directory-grid">'+''.join(cards)+'</div>'+gallery_note()+'</div></section>'
    page('tasks/index.html','任务图集','Task gallery','按物理难点、机器人和工具浏览任务设计与参考录像。',body)
    body=breadcrumbs([('tasks/','任务图集','Tasks'),('','查找任务','Search')])+'<section class="page-hero"><div class="wrap">'+tr('查找任务','Find a task','h1')+tr('输入任务名称、机器人或关键词，进一步按任务特点筛选。','Search by task, robot or keyword, then narrow by task features.','p','class="lead"')+'</div></section><section class="section search-page" style="padding-top:0"><div class="wrap">'+tasks_grid(list(RECORDS.values()))+gallery_note()+'</div></section>'
    page('tasks/search.html','查找任务','Find a task','搜索所有任务的目标、机器人、工具与任务特点。',body)

def documents():
    for name,p in PAGES.items():
        if name not in ('research','guide','archive'):continue
        body=breadcrumbs([('',p['title_zh'],p['title_en'])])+'<section class="page-hero"><div class="wrap"><p class="eyebrow">'+{'research':'RESEARCH','guide':'GET STARTED','archive':'ARCHIVE & EVIDENCE'}[name]+'</p>'+tr(p['title_zh'],p['title_en'],'h1')+tr(p['lead_zh'],p['lead_en'],'p','class="lead"')+'</div></section>'
        toc=''.join(link('#'+s['id'],s['title_zh'],s['title_en'],'') for s in p['sections'])
        # Fragment links in this page are local to the document, not the homepage.
        toc=toc.replace('href="'+PREFIX+'#','href="#')
        sections=[]
        for s in p['sections']:
            resources=''.join(external(a['url'],a['label_zh'],a['label_en']) for a in s.get('links',[]))
            sections.append(f'<section class="document-section" id="{s["id"]}">'+tr(s['title_zh'],s['title_en'],'h2')+tr(s['body_zh'],s['body_en'],'p')+('<div class="resource-links">'+resources+'</div>' if resources else '')+'</section>')
        selected=''
        if name=='archive':
            selected='<div class="archive-notice archive-selected" id="archive-selected" hidden data-archive-base="https://github.com/wuxiyang1996/robo-si-results/blob/'+CONFIG['archive_commit']+'/">'+tr('这个链接来自历史资料，可查看当时的原始文件。','This link comes from the historical materials. The original file is available below.')+'</div>'
            sections.append('<section class="document-section" id="records">'+tr('任务与验证记录','Task and verification records','h2')+tr('任务视频保留原始参考执行的范围。此处提供媒体清单、历史页面与原始文件目录，便于核对。','Task videos retain the scope of their original reference executions. The media manifest, historical pages and file index are available for inspection.','p')+'<div class="resource-links">'+external(local('data/video-gallery.json'),'视频与证据清单','Video & evidence manifest')+external(local('data/archive-files.json'),'归档文件索引','Archive file index')+link('archive/pages/index.html','历史网站页面','Historical site pages')+'</div></section>')
        body+='<div class="wrap document-layout"><aside class="document-toc" aria-label="页内目录 / On this page">'+toc+'</aside><div class="document-body">'+selected+''.join(sections)+'</div></div>'
        page(name+'.html',p['title_zh'],p['title_en'],p['lead_zh'],body,active=name)

def redirect(path, target, aliases=None):
    aliases=aliases or {}
    lang='en' if '-en.' in path else 'zh'
    script='const target=new URL('+json.dumps(local(target))+',location.origin),aliases='+json.dumps(aliases)+';const q=new URLSearchParams(location.search);if('+json.dumps(lang)+"==='en'&&!q.has('lang'))q.set('lang','en');target.search=q;let hash=decodeURIComponent(location.hash.slice(1));if(hash)target.hash=aliases[hash]||hash;location.replace(target.pathname+target.search+target.hash);"
    write(path,f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="{BASE+target}"><title>Embodied Terminal-Bench</title></head><body><p><a href="{local(target)}">打开当前页面 / Open page</a></p><script>{script}</script></body></html>')

def legacy_redirects(paths):
    family_by_slug={f.lower():f for f in FAMILIES}
    for path in paths:
        if path in ACTIVE:continue
        stem=Path(path).stem
        if path.count('/')==0 and stem in family_by_slug:
            fid=family_by_slug[stem];target=family_url(fid)
        elif path.startswith('infra/families/') and stem in FAMILIES:
            fid=stem;target=family_url(fid)
        else:
            fid=None
            if path.startswith('infra/categories/') and stem in {c['id'] for c in CONFIG['categories']}:target=category_url(stem)
            elif path in ['infra/contribute-zh.html','infra/contribute-en.html']:target=''
            elif path in ['infra/guide-zh.html','infra/guide-en.html']:target='guide.html'
            elif path in ['doc/self-modeling-benchmark-v6-zh.html','doc/self-modeling-benchmark-v6-en.html']:target='research.html'
            elif path in ['infra/results-zh.html','infra/results-en.html']:target='archive.html'
            else:target='archive/pages/'+path
        aliases={}
        if fid:
            for r in RECORDS.values():
                if r['family']!=fid:continue
                for alias in [r['record_id'],*r.get('public_case_ids',[]),urlsplit(r.get('historical_source_original_url','')).fragment]:
                    if alias:aliases[alias]=r['record_id']
        redirect(path,target,aliases)

def not_found():
    body='<section class="hero"><div class="wrap"><p class="eyebrow">FIND A PAGE</p>'+tr('这个地址可能已归档','This address may have moved to the archive','h1')+tr('正在检查历史文件目录。你也可以从任务图集或归档入口继续。','Checking the historical file index. You can also continue from the task gallery or archive.','p','class="lead"')+'<div class="hero-actions">'+link('tasks/','任务图集','Task gallery','button')+link('archive.html','历史与证据','Archive & evidence')+'</div><p id="archive-file-link"></p></div></section>'
    script='''<script>(async()=>{const prefix='/robo-si-results/';if(!location.pathname.startsWith(prefix))return;let key;try{key=decodeURIComponent(location.pathname.slice(prefix.length))}catch{return}try{const res=await fetch(prefix+'data/archive-files.json');if(!res.ok)return;const data=await res.json();const file=data.files[key]||data.files[key+'.html'];if(!file)return;if(file.page){location.replace(file.page+location.search+location.hash);return}const el=document.getElementById('archive-file-link');const a=document.createElement('a');a.className='text-link';a.href=file.raw;a.textContent='打开原始文件 / Open original file';el.append(a);location.replace(file.raw+location.hash)}catch{}})();</script>'''
    page('404.html','查找页面','Find a page','查找任务页面和历史归档文件。',body+script,active='')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete-content',action='store_true',help='Local layout preview only; validation will reject incomplete content.')
    args=parser.parse_args()
    assert OUT.resolve()==ROOT.resolve()/'dist', 'Unexpected build target'
    OUT.mkdir(exist_ok=True)
    for path in sorted((SOURCE/'content').glob('tasks_*.json')):
        obj=json.loads(path.read_text(encoding='utf-8'))
        assert not (set(FAMILIES)&set(obj['families'])),path
        assert not (set(TASKS)&set(obj['tasks'])),path
        FAMILIES.update(obj['families']);TASKS.update(obj['tasks'])
    missing=set(RECORDS)-set(TASKS)
    missing_families=set(BY_CATEGORY)-set(FAMILIES)
    if not args.allow_incomplete_content:
        assert not missing and not missing_families, f'Missing editorial content: {sorted(missing)} / {sorted(missing_families)}'
    for fid in missing_families:FAMILIES[fid]={'title_zh':fid,'title_en':fid,'intro_zh':'任务说明正在整理。','intro_en':'Task description in progress.','robots':[],'tags':[]}
    for rid in missing:
        r=RECORDS[rid];TASKS[rid]={**r,'description_zh':'任务说明正在整理。','description_en':'Task description in progress.','robots':[],'tags':[],'scope_zh':'','scope_en':''}
    assert set(TASKS)==set(RECORDS)
    assert set(FAMILIES)==set(BY_CATEGORY)
    pages_path=SOURCE/'content/pages.json'
    if pages_path.exists():PAGES.update(json.loads(pages_path.read_text(encoding='utf-8')))
    elif args.allow_incomplete_content:
        for key,zh,en in [('research','研究问题','Research'),('guide','使用与下载','Get started'),('archive','历史与证据','Archive & evidence')]:PAGES[key]={'title_zh':zh,'title_en':en,'lead_zh':'','lead_en':'','sections':[]}
    else:raise ValueError('Missing document content')
    (OUT/'assets').mkdir(exist_ok=True)
    for source in (SOURCE/'assets').iterdir():
        if source.is_file():shutil.copyfile(source,OUT/'assets'/source.name)
    (OUT/'data').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/video-gallery.json',OUT/'data/video-gallery.json')
    browser_qa='not_performed'
    qa_path=SOURCE/'quality/browser-review.json'
    if qa_path.exists():
        qa=json.loads(qa_path.read_text(encoding='utf-8'))
        qa_current=all((ROOT/path).is_file() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value for path,value in qa['source_sha256'].items())
        browser_qa=qa['status'] if qa_current else 'source_changed_since_review'
        shutil.copyfile(qa_path,OUT/'data/browser-review.json')
    home();directory();categories();families();documents();not_found()
    signature=hashlib.sha256((ROOT/'tools/archive_site.py').read_bytes()+CONFIG['archive_commit'].encode()).hexdigest()
    cache=OUT/'data/archive-build.json'
    if cache.exists() and json.loads(cache.read_text())['signature']==signature:
        report=json.loads((OUT/'data/archive-files.json').read_text(encoding='utf-8'))
        paths=list(report['original_html_sha256'])
    else:
        paths,report=build_archive(ROOT,OUT,CONFIG['archive_commit'],BASE,PREFIX)
        write('data/archive-build.json',json.dumps({'signature':signature}))
    legacy_redirects(paths)
    public={'categories':CONFIG['categories'],'families':FAMILIES,'tasks':TASKS,'unique_recordings':len(RECORDS),'public_configurations':CATALOG['public_configurations']}
    write('data/task-index.json',json.dumps(public,ensure_ascii=False,separators=(',',':')))
    write('robots.txt','User-agent: *\nAllow: /robo-si-results/\nDisallow: /robo-si-results/archive/\nDisallow: /robo-si-results/404.html\nSitemap: '+BASE+'sitemap.xml\n')
    urls=[BASE+('' if p=='index.html' else p.replace('/index.html','/')) for p in ACTIVE if p not in ('404.html','tasks/search.html')]
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(u)+'</loc></url>' for u in urls)+'</urlset>')
    files=[p for p in OUT.rglob('*') if p.is_file()]
    summary={'editorial_complete':not missing and not missing_families,'records':len(RECORDS),'families':len(FAMILIES),'categories':len(CONFIG['categories']),'active_pages':ACTIVE,'archived_html':len(paths),'files':len(files),'bytes':sum(p.stat().st_size for p in files),'video_manifest_sha256':hashlib.sha256((OUT/'data/video-gallery.json').read_bytes()).hexdigest(),'archive_commit':CONFIG['archive_commit'],'browser_visual_qa':browser_qa}
    write('data/site-build.json',json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:summary[k] for k in ['editorial_complete','records','families','categories','archived_html','files','bytes']}))

if __name__=='__main__':main()
