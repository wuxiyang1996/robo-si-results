"""Build the research site, galleries and explicit historical redirects.

Uses only the Python standard library. Editorial content is separate from the
immutable recording manifest; a normal build refuses incomplete task copy.
"""
from pathlib import Path
from html import escape
from urllib.parse import urlsplit
from collections import Counter
import argparse
import hashlib
import json
import shutil
import subprocess
import re

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
FACETS = {}
DIMENSIONS = ('embodiment', 'tools', 'task', 'difficulty')
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
    <div class="footer-links">{link('research.html','研究问题','Research','')}{link('tasks/','任务图集','Task gallery','')}{link('guide.html','使用与下载','Get started','')}<a href="https://github.com/wuxiyang1996/robo-si-results">GitHub</a></div></div></footer>'''

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

def facet_values(records, dimension):
    return list(dict.fromkeys(v for r in records for v in FACETS['records'][r['record_id']][dimension]))

def facet_controls(records, family=False):
    fields=[]
    for dimension in DIMENSIONS:
        spec=FACETS['dimensions'][dimension]
        present=facet_values(records,dimension)
        values=list(spec['values']) if dimension=='difficulty' else present
        counts=Counter(v for r in records for v in FACETS['records'][r['record_id']][dimension])
        options='<option value="" data-zh="全部" data-en="All">全部</option>'
        for value in values:
            item=spec['values'][value]; n=counts[value]
            options+=f'<option value="{e(value)}" data-zh="{e(item["label_zh"])} ({n})" data-en="{e(item["label_en"])} ({n})">{e(item["label_zh"])} ({n})</option>'
        control_id=('family-' if family else '')+dimension+'-filter'
        attr=f'data-facet-filter="{dimension}"' if family else ''
        fields.append(f'<div class="facet-field"><label for="{control_id}">'+tr(spec['label_zh'],spec['label_en'])+f'</label><select id="{control_id}" {attr}>{options}</select></div>')
    return '<div class="facet-controls">'+''.join(fields)+'</div>'

def facet_guide():
    return '<details class="facet-guide"><summary>'+tr('标签与难度怎么读','About the tags and difficulty')+'</summary>'+tr('Embodiment 是执行任务的机器人；Tools 是场景里的物理工具；Task 描述要完成的操作。标签用于浏览研究任务。','Embodiment identifies the robots; Tools lists physical tools in the scene; Task describes the operation. These tags organize the research gallery.','p')+tr('难度按同一种子的场景逐层叠加：第 1 层只有必要工具；第 2 层加入当前身体用不了、其他身体能用的工具；第 3 层再加入可通过试验排除的干扰项。','Difficulty uses cumulative scenes with the same seed: layer 1 contains only necessary tools; layer 2 adds tools usable by another body but not the current one; layer 3 adds distractors that experiments can rule out.','p')+tr('“待分层”表示当前记录尚未验证这套分层条件。任务编号或执行接口中的 L1–L3、录像长短和专家成功均不作为难度依据；这些浏览标签不会提供给被评测 agent。','“Not classified” means the required scene-layer evidence has not been established. L1–L3 in task IDs or execution APIs, video duration and expert success do not determine difficulty. These browsing labels are not given to evaluated agents.','p')+'</details>'

def facet_summary(records):
    rows=[]
    for dimension in ('tools','task','difficulty'):
        spec=FACETS['dimensions'][dimension];values=facet_values(records,dimension)
        shown=values[:2]
        labels=' · '.join(spec['values'][v]['label_zh'] for v in shown)
        english=' · '.join(spec['values'][v]['label_en'] for v in shown)
        if len(values)>2:labels+=f' +{len(values)-2}';english+=f' +{len(values)-2}'
        rows.append('<div>'+tr(spec['label_zh'],spec['label_en'],'span','class="facet-caption"')+tr(labels,english)+'</div>')
    return '<div class="family-facet-summary">'+''.join(rows)+'</div>'

def task_facet_tags(rid):
    record=FACETS['records'][rid];rows=[]
    for dimension in DIMENSIONS:
        spec=FACETS['dimensions'][dimension];chips=[]
        for value in record[dimension]:
            item=spec['values'][value]
            chips.append(f'<button type="button" class="facet-chip" data-set-facet="{dimension}" data-facet-value="{e(value)}">'+tr(item['label_zh'],item['label_en'])+'</button>')
        rows.append(f'<div class="facet-row" data-facet-dimension="{dimension}">'+tr(spec['label_zh'],spec['label_en'],'dt')+'<dd>'+''.join(chips)+'</dd></div>')
    note=tr(record['difficulty_note_zh'],record['difficulty_note_en'],'p','class="facet-note"') if record['difficulty']!=['unclassified'] else ''
    return '<dl class="task-facets">'+''.join(rows)+'</dl>'+note

def gallery_note():
    return '<p class="gallery-note">'+tr('视频展示物理仿真中的参考执行。各任务的简化条件和完成范围随录像说明，不能据此推算新 agent 的成功率。','Videos show reference executions in physics simulation. Each task states its conditions and demonstrated scope; these are not success rates for a new agent.')+'</p>'

def cta():
    return f'''<section class="bottom-cta"><div class="wrap cta-inner"><div>{tr('从一个任务开始','Start with one task','h2')}{tr('下载环境，接入 agent，再看执行记录和评分。','Download the environment, connect an agent, and inspect execution and scores.','p')}</div><div class="hero-actions">{link('guide.html','使用与下载','Get started','button')}{link('research.html','阅读研究问题','Read the research')}</div></div></section>'''

def home():
    contributions=''.join(f'<article class="contribution"><span class="number">0{i}</span><div>{tr(x["title_zh"],x["title_en"],"h2")}{tr(x["body_zh"],x["body_en"],"p")}</div></article>' for i,x in enumerate(CONFIG['contributions'],1))
    body=f'''<section class="hero"><div class="wrap"><p class="eyebrow">CODE · EXPERIMENT · PHYSICAL ACTION</p>{tr(CONFIG['research_question_zh'],CONFIG['research_question_en'],'h1')}{tr(CONFIG['intro_zh'],CONFIG['intro_en'],'p','class="lead"')}<div class="hero-actions">{link('#categories','观看任务演示','Explore the tasks','button')}{link('research.html','阅读研究问题','Read the research')}</div></div></section>
    <div class="wrap"><div class="contributions">{contributions}</div></div><section class="section" id="categories"><div class="wrap"><div class="section-head"><div><p class="eyebrow">THE TASK GALLERY</p>{tr('任务图集','Task gallery','h2')}{tr('选一个类别，点击小图查看这个任务族的全部视频。','Choose a category, then open a thumbnail to explore the family’s videos.','p')}</div>{link('tasks/search.html','查找具体任务','Find a specific task')}</div>{family_gallery()}{gallery_note()}</div></section>{cta()}'''
    page('index.html',CONFIG['research_question_zh'],CONFIG['research_question_en'],CONFIG['intro_zh'],body,active='home')

def family_card(fid):
    f=FAMILIES[fid]
    rid=CATALOG['family_representatives'].get(fid)
    if not rid or rid not in RECORDS: return ''
    r=RECORDS[rid];c=BY_CATEGORY[fid]
    tags=facet_summary([record for record in RECORDS.values() if record['family']==fid])
    return f'''<a class="family-tile" data-local data-family-card="{fid}" data-family-category="{c['id']}" data-preview-record="{e(rid)}" href="{local(family_url(fid))}"><div class="family-thumbnail"><img src="{e(r['poster_url'])}" alt="" loading="lazy" decoding="async" width="960" height="540"><span class="thumbnail-action" aria-hidden="true"><svg viewBox="0 0 20 20"><path fill="currentColor" d="M4 2L18 10 4 18Z"/></svg></span><span class="speed">8×</span></div><div class="family-tile-body"><div class="family-tile-meta"><span class="family-code">{fid}</span>{tr(f'{COUNTS[fid]} 段视频',f'{COUNTS[fid]} video'+('s' if COUNTS[fid]!=1 else ''))}</div>{tr(f['title_zh'],f['title_en'],'h3')}{tags}<div class="family-tile-bottom">{robots(f['robots'])}<span class="family-arrow" aria-hidden="true">↗</span></div></div></a>'''

def family_gallery():
    buttons=[];captions=[];paused=[]
    for c in CONFIG['categories']:
        count=sum(COUNTS[f]>0 for f in c['families'])
        buttons.append(f'<button class="gallery-tag" id="{c["id"]}" type="button" data-family-filter="{c["id"]}" aria-pressed="false" aria-controls="family-grid">'+tr(c['title_zh'],c['title_en'])+f'<span class="tag-count" aria-hidden="true">{count}</span></button>')
        captions.append(f'<p data-category-caption="{c["id"]}" hidden>'+tr(c['description_zh'],c['description_en'])+'</p>')
        for fid in c['families']:
            if not COUNTS[fid]:
                paused.append(f'<p class="paused-note" data-paused-family="{fid}" data-family-category="{c["id"]}">'+link(family_url(fid),FAMILIES[fid]['title_zh'],FAMILIES[fid]['title_en'],'')+' — '+tr('研究暂停，暂无完整参考录像。','Research paused; no complete reference recording.')+'</p>')
    buttons.append('<button class="gallery-tag" type="button" data-family-filter="all" aria-pressed="true" aria-controls="family-grid">'+tr('全部','All')+'<span class="tag-count" aria-hidden="true">29</span></button>')
    records=list(RECORDS.values())
    data=json.dumps([{'family':r['family'],**{d:FACETS['records'][r['record_id']][d] for d in DIMENSIONS}} for r in records],ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    filters='<div class="facet-toolbar">'+facet_controls(records,True)+'<button type="button" class="reset-filter" data-reset-facets>'+tr('清除标签','Clear tags')+'</button></div>'+facet_guide()
    empty='<div class="empty-results" data-family-empty hidden>'+tr('没有匹配的任务。试试其他标签组合，或选择全部类别。','No matching tasks. Try another tag combination or choose all categories.')+'</div>'
    return '<div class="family-browser" data-family-gallery data-default-category="access"><div class="gallery-tags" role="group" aria-label="任务类别 / Task categories">'+''.join(buttons)+'</div>'+filters+'<div class="gallery-context">'+''.join(captions)+'<p data-category-caption="all">'+tr('从取物、搬运到装配和协作，浏览所有任务族。','Explore all families, from retrieval and transport to assembly and collaboration.')+'</p><span class="family-result-count" data-family-count role="status" aria-live="polite">'+tr('29 个任务族 · 246 个任务','29 families · 246 tasks')+'</span></div><div class="family-grid" id="family-grid">'+''.join(family_card(f) for c in CONFIG['categories'] for f in c['families'] if COUNTS[f])+ '</div>'+empty+''.join(paused)+f'<script type="application/json" data-facet-records>{data}</script></div>'

def task_card(r):
    rid=r['record_id']; t=TASKS[rid]
    is_exit=r.get('accepted_exit') or 'safe-exit' in FACETS['records'][rid]['task']
    all_text=' '.join([rid,*r.get('public_case_ids',[]),t['title_zh'],t['title_en'],t['description_zh'],t['description_en'],t.get('goal_zh',''),t.get('goal_en',''),*t.get('conditions_zh',[]),*t.get('conditions_en',[]),*t['robots'],*t['tags'],FAMILIES[r['family']]['title_zh'],r['family']])
    scope=('<div class="task-scope">'+tr('录像范围','Demonstrated scope','h3')+tr(t.get('scope_zh',''),t.get('scope_en',''),'p')+'</div>' if t.get('scope_zh') else '')
    outcome=('<span class="outcome">'+tr('安全退出','Safe exit')+'</span>') if is_exit else ''
    goal=tr(t.get('goal_zh',t['description_zh']),t.get('goal_en',t['description_en']),'p')
    conditions='<ul>'+''.join(tr(zh,en,'li') for zh,en in zip(t.get('conditions_zh',[]),t.get('conditions_en',[])))+'</ul>'
    brief='<div class="task-brief"><div>'+tr('任务目标','Goal','h3')+goal+'</div><div>'+tr('场景与约束','Scene & constraints','h3')+conditions+'</div></div>'
    aliases=''.join(f'<span id="{e(alias)}"></span>' for alias in r.get('public_case_ids',[]) if alias!=rid)
    facets=FACETS['records'][rid]
    attributes=' '.join(f'data-{d}="{e("|".join(facets[d]))}"' for d in DIMENSIONS)
    all_text+=' '+' '.join(FACETS['dimensions'][d]['values'][v][lang] for d in DIMENSIONS for v in facets[d] for lang in ('label_zh','label_en'))
    return f'''<article class="task-card" id="{e(rid)}" data-filter-card data-search="{e(all_text)}" {attributes} data-outcome="{'exit' if is_exit else 'execution'}">{aliases}{player(rid)}<p class="task-card-id">{e(' · '.join(r.get('public_case_ids',[rid])))}</p>{tr(t['title_zh'],t['title_en'],'h2')}{outcome}{task_facet_tags(rid)}{brief}{scope}</article>'''

def toolbar(records):
    return f'''<div class="toolbar task-toolbar"><div class="search-field"><label for="task-search">{tr('查找任务','Search')}</label><input id="task-search" type="search" placeholder="任务、机器人或关键词" data-placeholder-zh="任务、机器人或关键词" data-placeholder-en="Task, robot or keyword" aria-label="查找任务 / Search tasks"></div><select id="outcome-filter" aria-label="按目标类型筛选 / Filter by target type"><option value="" data-zh="全部目标" data-en="All goals">全部目标</option><option value="execution" data-zh="操作任务" data-en="Manipulation">操作任务</option><option value="exit" data-zh="安全退出" data-en="Safe exit">安全退出</option></select><button class="reset-filter" type="button" data-reset-filter>{tr('重置','Reset')}</button><span class="filter-count" id="filter-count" role="status" aria-live="polite">{len(records)} / {len(records)}</span>{facet_controls(records)}</div>{facet_guide()}'''

def tasks_grid(records):
    return toolbar(records)+'<div class="gallery">'+''.join(task_card(r) for r in records)+'</div><div class="empty-results" id="empty-results" hidden>'+tr('没有找到符合条件的任务。试试更短的关键词，或清除筛选。','No tasks match these filters. Try a shorter search or reset the filters.')+'</div>'

def categories():
    for c in CONFIG['categories']:
        intro=breadcrumbs([('tasks/','任务图集','Tasks'),('',c['title_zh'],c['title_en'])])+f'<section class="page-hero"><div class="wrap"><p class="eyebrow">{c["number"]} / TASK CATEGORY</p>'+tr(c['title_zh'],c['title_en'],'h1')+tr(c['description_zh'],c['description_en'],'p','class="lead"')+'</div></section>'
        if len(c['families'])==1:
            fid=c['families'][0];f=FAMILIES[fid]
            content=tr(f['intro_zh'],f['intro_en'],'p','class="card-description"')+tasks_grid([r for r in RECORDS.values() if r['family']==fid])
        else:
            content='<div class="family-grid">'+''.join(family_card(f) for f in c['families'] if COUNTS[f])+'</div>'
            paused=[f for f in c['families'] if not COUNTS[f]]
            if paused:
                content+='<p class="paused-note">'+tr('另有任务设计尚无完整参考录像：','Task designs without a complete reference recording: ')+' · '.join(link(family_url(f),FAMILIES[f]['title_zh'],FAMILIES[f]['title_en'],'') for f in paused)+'</p>'
        page(category_url(c['id']),c['title_zh'],c['title_en'],c['description_zh'],intro+'<section class="section" style="padding-top:0"><div class="wrap">'+content+gallery_note()+'</div></section>',image=RECORDS[c['demo']]['poster_url'],keywords=c['families'])

def families():
    for fid,f in FAMILIES.items():
        c=BY_CATEGORY[fid];records=[r for r in RECORDS.values() if r['family']==fid]
        body=breadcrumbs([('tasks/','任务图集','Tasks'),(category_url(c['id']),c['title_zh'],c['title_en']),('',f['title_zh'],f['title_en'])])
        body+='<section class="page-hero"><div class="wrap"><p class="eyebrow">'+e(fid)+' / TASK FAMILY</p>'+tr(f['title_zh'],f['title_en'],'h1')+tr(f['intro_zh'],f['intro_en'],'p','class="lead"')+robots(f['robots'])+'</div></section>'
        content=tasks_grid(records) if records else '<div class="paused-family">'+tr('研究暂停，暂无完整参考录像','Research paused; no complete reference recording','h2')+tr('完整穿衣目标尚未通过实测验证，因此这里不展示成功视频。恢复研究后，需要重新完成场景、执行与评分验证。','The complete dressing goal has not passed physical verification, so no success video is shown. Resuming this work requires scene, execution and scoring checks.','p')+'</div>'
        body+='<section class="section" style="padding-top:0"><div class="wrap">'+content+(gallery_note() if records else '')+'</div></section>'
        page(family_url(fid),f['title_zh'],f['title_en'],f['intro_zh'],body,keywords=[fid,*f['robots'],*f['tags']])

def directory():
    form=f'<form class="toolbar" action="{local("tasks/search.html")}" method="get"><div class="search-field"><label for="global-search">{tr("查找任务","Search")}</label><input id="global-search" type="search" name="q" placeholder="任务、机器人或关键词" data-placeholder-zh="任务、机器人或关键词" data-placeholder-en="Task, robot or keyword"></div><input type="hidden" name="lang" value="zh"><button class="button" type="submit">{tr("搜索全部任务","Search all tasks")}</button></form>'
    body=breadcrumbs([('','任务图集','Tasks')])+'<section class="page-hero"><div class="wrap"><p class="eyebrow">TASK GALLERY</p>'+tr('从你关心的问题开始','Find the problem you care about','h1')+tr('选一个类别，点击小图查看这个任务族的全部视频。','Choose a category, then open a thumbnail to explore the family’s videos.','p','class="lead"')+'</div></section><section class="section" style="padding-top:0"><div class="wrap">'+family_gallery()+form+gallery_note()+'</div></section>'
    page('tasks/index.html','任务图集','Task gallery','按物理难点、机器人和工具浏览任务设计与参考录像。',body)
    body=breadcrumbs([('tasks/','任务图集','Tasks'),('','查找任务','Search')])+'<section class="page-hero"><div class="wrap">'+tr('查找任务','Find a task','h1')+tr('输入任务名称、机器人或关键词，进一步按任务特点筛选。','Search by task, robot or keyword, then narrow by task features.','p','class="lead"')+'</div></section><section class="section search-page" style="padding-top:0"><div class="wrap">'+tasks_grid(list(RECORDS.values()))+gallery_note()+'</div></section>'
    page('tasks/search.html','查找任务','Find a task','搜索所有任务的目标、机器人、工具与任务特点。',body)

def document_block(block):
    kind=block['type']
    if kind=='code':
        return '<div class="code-example"><div class="code-heading"><span>'+e(block.get('language',''))+'</span><button type="button" data-copy-code>'+tr('复制命令','Copy commands')+'</button></div><pre><code>'+escape(block['text'])+'</code></pre><span class="copy-status" role="status" aria-live="polite"></span></div>'
    if kind=='list':
        return '<ul class="document-list">'+''.join(tr(zh,en,'li') for zh,en in zip(block['items_zh'],block['items_en']))+'</ul>'
    if kind=='table':
        head=''.join(tr(zh,en,'th','scope="col"') for zh,en in zip(block['columns_zh'],block['columns_en']))
        rows=''.join('<tr>'+''.join(tr(zh,en,'td') for zh,en in zip(zrow,erow))+'</tr>' for zrow,erow in zip(block['rows_zh'],block['rows_en']))
        return '<div class="table-scroll" role="region" tabindex="0" aria-label="说明表 / Reference table"><table class="document-table"><thead><tr>'+head+'</tr></thead><tbody>'+rows+'</tbody></table></div>'
    if kind=='note':
        return '<aside class="document-note">'+tr(block['text_zh'],block['text_en'],'p')+'</aside>'
    if kind=='paragraph':
        return tr(block['text_zh'],block['text_en'],'p')
    raise ValueError('Unknown document block: '+kind)

def documents():
    for name,p in PAGES.items():
        if name not in ('research','guide'):continue
        body=breadcrumbs([('',p['title_zh'],p['title_en'])])+'<section class="page-hero"><div class="wrap"><p class="eyebrow">'+{'research':'RESEARCH','guide':'GET STARTED'}[name]+'</p>'+tr(p['title_zh'],p['title_en'],'h1')+tr(p['lead_zh'],p['lead_en'],'p','class="lead"')+'</div></section>'
        toc=''.join(link('#'+s['id'],s['title_zh'],s['title_en'],'') for s in p['sections'])
        # Fragment links in this page are local to the document, not the homepage.
        toc=toc.replace('href="'+PREFIX+'#','href="#')
        sections=[]
        for s in p['sections']:
            resources=''.join(external(a['url'],a['label_zh'],a['label_en']) for a in s.get('links',[]))
            sections.append(f'<section class="document-section" id="{s["id"]}">'+tr(s['title_zh'],s['title_en'],'h2')+tr(s.get('body_zh',''),s.get('body_en',''),'p')+''.join(document_block(b) for b in s.get('blocks',[]))+('<div class="resource-links">'+resources+'</div>' if resources else '')+'</section>')
        body+='<div class="wrap document-layout"><aside class="document-toc" aria-label="页内目录 / On this page">'+toc+'</aside><div class="document-body">'+''.join(sections)+'</div></div>'
        page(name+'.html',p['title_zh'],p['title_en'],p['lead_zh'],body,active=name)

def redirect(path, target, aliases=None):
    aliases=aliases or {}
    lang='en' if '-en.' in path else 'zh'
    script='const target=new URL('+json.dumps(local(target))+',location.origin),aliases='+json.dumps(aliases)+';const q=new URLSearchParams(location.search);if('+json.dumps(lang)+"==='en'&&!q.has('lang'))q.set('lang','en');target.search=q;let hash=location.hash.slice(1);try{hash=decodeURIComponent(hash)}catch{}if(hash)target.hash=aliases[hash]||hash;location.replace(target.pathname+target.search+target.hash);"
    write(path,f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="{BASE+target}"><title>Embodied Terminal-Bench</title></head><body><p><a href="{local(target)}">打开当前页面 / Open page</a></p><script>{script}</script></body></html>')

def legacy_redirects(paths):
    family_by_slug={f.lower():f for f in FAMILIES}
    source_families={}
    for r in RECORDS.values():
        for key in ('source_page','historical_source_original_url'):
            stem=Path(urlsplit(r.get(key,'')).path).stem.lower()
            if stem:source_families.setdefault(stem,set()).add(r['family'])
    routes={}
    for path in sorted(set(paths)|{'archive.html'}):
        stem=Path(path).stem.lower()
        fid=family_by_slug.get(stem)
        if not fid and len(source_families.get(stem,[]))==1:fid=next(iter(source_families[stem]))
        if not fid:
            match=re.fullmatch(r'(?:archive-|task-)([a-z0-9]+)(?:-(?:\d{8}|zh|en))?',stem)
            if match:fid=family_by_slug.get(match.group(1))
        if fid:target=family_url(fid)
        else:
            if path.startswith('infra/categories/') and stem in {c['id'] for c in CONFIG['categories']}:target=category_url(stem)
            elif 'self-modeling' in stem or any(x in stem for x in ('task-design','protocol','verifier','acceptance','glossary')):target='research.html'
            elif path.startswith('infra/') and not any(x in stem for x in ('contribute','result','status')):target='guide.html'
            elif 'guide' in stem or 'download' in stem:target='guide.html'
            elif stem=='index':target=''
            else:target='tasks/'
        aliases={}
        if fid:
            for r in RECORDS.values():
                if r['family']!=fid:continue
                for alias in [r['record_id'],*r.get('public_case_ids',[]),urlsplit(r.get('historical_source_original_url','')).fragment]:
                    if alias:aliases[alias]=r['record_id']
        for old_path in (path,'archive/pages/'+path):
            if old_path in ACTIVE:continue
            routes[old_path]={'target':target,'aliases':aliases}
            redirect(old_path,target,aliases)
    write('data/legacy-routes.json',json.dumps(routes,ensure_ascii=False,separators=(',',':')))
    return routes

def not_found():
    body='<section class="hero"><div class="wrap"><p class="eyebrow">FIND A PAGE</p>'+tr('这个页面已整理到新的位置','This page has moved','h1')+tr('正在查找对应页面，也可以直接浏览任务或打开使用指南。','Looking for the current page. You can also browse tasks or open the guide.','p','class="lead"')+'<div class="hero-actions">'+link('tasks/','任务图集','Task gallery','button')+link('guide.html','使用与下载','Get started')+'</div></div></section>'
    script='''<script>(async()=>{const prefix='/robo-si-results/';if(!location.pathname.startsWith(prefix))return;let key;try{key=decodeURIComponent(location.pathname.slice(prefix.length))}catch{return}try{const res=await fetch(prefix+'data/legacy-routes.json');if(!res.ok)return;const routes=await res.json();const route=routes[key]||routes[key+'.html'];if(!route)return;const target=new URL(prefix+route.target,location.origin);target.search=location.search;let hash=location.hash.slice(1);try{hash=decodeURIComponent(hash)}catch{}if(hash)target.hash=route.aliases[hash]||hash;location.replace(target.pathname+target.search+target.hash)}catch{}})();</script>'''
    page('404.html','查找页面','Find a page','查找当前任务页面和使用指南。',body+script,active='')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete-content',action='store_true',help='Local layout preview only; validation will reject incomplete content.')
    args=parser.parse_args()
    assert OUT.resolve()==ROOT.resolve()/'dist', 'Unexpected build target'
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
    FACETS.update(json.loads((SOURCE/'content/task_facets.json').read_text(encoding='utf-8')))
    assert set(FACETS['records'])==set(RECORDS), 'Task facets must cover every recording'
    assert set(FACETS['dimensions'])==set(DIMENSIONS), 'Expected four independent tag dimensions'
    for rid,entry in FACETS['records'].items():
        for dimension in DIMENSIONS:
            assert entry.get(dimension) and len(entry[dimension])==len(set(entry[dimension])), (rid,dimension)
            assert all(value in FACETS['dimensions'][dimension]['values'] for value in entry[dimension]), (rid,dimension)
        assert len(entry['difficulty'])==1 and entry.get('difficulty_note_zh') and entry.get('difficulty_note_en'), rid
    pages_path=SOURCE/'content/pages.json'
    if pages_path.exists():PAGES.update(json.loads(pages_path.read_text(encoding='utf-8')))
    elif args.allow_incomplete_content:
        for key,zh,en in [('research','研究问题','Research'),('guide','使用与下载','Get started')]:PAGES[key]={'title_zh':zh,'title_en':en,'lead_zh':'','lead_en':'','sections':[]}
    else:raise ValueError('Missing document content')
    # Only remove this repository's generated deploy directory, never sources.
    if OUT.exists():shutil.rmtree(OUT.resolve())
    OUT.mkdir()
    (OUT/'assets').mkdir(exist_ok=True)
    for source in (SOURCE/'assets').iterdir():
        if source.is_file():shutil.copyfile(source,OUT/'assets'/source.name)
    (OUT/'data').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/video-gallery.json',OUT/'data/video-gallery.json')
    shutil.copyfile(SOURCE/'content/task_facets.json',OUT/'data/task-facets.json')
    browser_qa='not_performed'
    qa_path=SOURCE/'quality/browser-review.json'
    if qa_path.exists():
        qa=json.loads(qa_path.read_text(encoding='utf-8'))
        def reviewed_hash(path):
            data=path.read_bytes()
            if qa.get('source_hash_format')=='sha256-utf8-lf':data=data.replace(b'\r\n',b'\n')
            return hashlib.sha256(data).hexdigest()
        qa_current=all((ROOT/path).is_file() and reviewed_hash(ROOT/path)==value for path,value in qa['source_sha256'].items())
        browser_qa=qa['status'] if qa_current else 'source_changed_since_review'
        shutil.copyfile(qa_path,OUT/'data/browser-review.json')
    home();directory();categories();families();documents();not_found()
    tracked=subprocess.check_output(['git','ls-tree','-r','-z','--name-only',CONFIG['archive_commit']],cwd=ROOT).decode('utf-8').rstrip('\0').split('\0')
    routes=legacy_redirects([p for p in tracked if p.endswith('.html')])
    public={'categories':CONFIG['categories'],'families':FAMILIES,'tasks':TASKS,'facets':FACETS,'unique_recordings':len(RECORDS),'public_configurations':CATALOG['public_configurations']}
    write('data/task-index.json',json.dumps(public,ensure_ascii=False,separators=(',',':')))
    write('robots.txt','User-agent: *\nAllow: /robo-si-results/\nDisallow: /robo-si-results/archive/\nDisallow: /robo-si-results/404.html\nSitemap: '+BASE+'sitemap.xml\n')
    urls=[BASE+('' if p=='index.html' else p.replace('/index.html','/')) for p in ACTIVE if p not in ('404.html','tasks/search.html')]
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(u)+'</loc></url>' for u in urls)+'</urlset>')
    files=[p for p in OUT.rglob('*') if p.is_file()]
    summary={'editorial_complete':not missing and not missing_families,'records':len(RECORDS),'families':len(FAMILIES),'categories':len(CONFIG['categories']),'active_pages':ACTIVE,'archived_html':0,'legacy_redirects':len(routes),'files':len(files),'bytes':sum(p.stat().st_size for p in files),'video_manifest_sha256':hashlib.sha256((OUT/'data/video-gallery.json').read_bytes()).hexdigest(),'browser_visual_qa':browser_qa}
    write('data/site-build.json',json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:summary[k] for k in ['editorial_complete','records','families','categories','archived_html','files','bytes']}))

if __name__=='__main__':main()
