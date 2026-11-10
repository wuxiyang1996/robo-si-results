"""Render the proposed Sokoban design and update its existing evidence pages.

Accept a repository or hosted src root. Existing evidence sections are retained.
The two Markdown design documents are the editable content sources.
"""
from pathlib import Path
import argparse
from html import escape
import hashlib
import json

from bs4 import BeautifulSoup
import markdown


CSS = """
.sokoban-design {padding-block:32px}
.sokoban-design h2 {scroll-margin-top:130px;margin-top:36px}
.sokoban-design h3 {margin-top:24px}
.sokoban-design p,.sokoban-design li,.sokoban-design td {overflow-wrap:anywhere}
.sokoban-design .table-scroll {max-width:100%;overflow-x:auto;margin:20px 0}
.sokoban-design table {width:100%;border-collapse:collapse;font-size:14px}
.sokoban-design th,.sokoban-design td {padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);min-width:120px}
.sokoban-design th {background:var(--panel)}
.sokoban-design .design-flow {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:0;list-style:none;margin:24px 0}
.sokoban-design .design-flow li {padding:16px;border:1px solid var(--line);background:var(--card);border-radius:10px}
.sokoban-design .design-flow span {display:block;color:var(--accent);font:12px var(--mono);margin-bottom:6px}
.sokoban-design .design-note {padding:18px;border-left:3px solid var(--accent);background:var(--panel);margin:20px 0}
.sokoban-design .design-nav {line-height:2.2;margin-bottom:22px}
@media(max-width:700px){.sokoban-design .design-flow{grid-template-columns:repeat(2,minmax(0,1fr))}.sokoban-design th,.sokoban-design td{min-width:110px}}
@media print{.nav,.skip-link,.design-nav{display:none}.sokoban-design .table-scroll{overflow:visible}body{background:white;color:black}}
"""


def fragment(text):
    return BeautifulSoup(text, 'html.parser')


def set_html(element, text):
    element.clear()
    element.append(fragment(text))


def wrap_tables(soup):
    for table in soup.select('table'):
        if 'table-scroll' not in table.parent.get('class', []):
            wrapper = soup.new_tag('div', attrs={'class': 'table-scroll', 'tabindex': '0', 'role': 'region',
                                                        'aria-label': '可横向滚动的数据表 / Scrollable data table'})
            table.wrap(wrapper)


TEXT = {
    'zh': {
        'lang': 'zh-CN', 'other': 'en', 'other_label': 'English',
        'title': 'Sokoban：从局部观察到全局建图',
        'lead': '多机器人构建一致、可更新的全局地图，并通过物理推箱清路抵达目标。重点比较有通信与无显式通信；工具可由 agent 按需构建。',
        'home': '任务首页', 'evidence': '现有 L1 证据', 'doc': '完整任务设计', 'download': '下载设计文档',
        'status': '设计更新 · 2026-10-28 · 新增物理运行 0',
        'scope': 'L1 保留开发图见证；L2/L3、建图评测和通信对照待实现与验证。task_success=null，formal_admission=false。',
        'summary_title': '任务设计：建图、执行、通信',
        'flow': ['局部 RGB 与本体感知', '构建与更新全局地图', '规划与物理推箱', '合法到达各自目标'],
        'cards': [('地图是否正确', '覆盖、通路判断与动态更新'), ('任务是否完成', '合法推箱、稳定驻留与恢复'), ('通信是否有益', '同实例、同预算的配对对照')],
        'levels': '<tr><td>SK-L1</td><td>固定开发图 · 双 G1</td><td>局部探索、建图与物理执行</td></tr><tr><td>SK-L2</td><td>未见拓扑 · 双 G1</td><td>全局一致性、信息融合与重规划</td></tr><tr><td>SK-L3</td><td>相同地图 · 能力变化</td><td>身体约束下的可达性与分工</td></tr>',
        'heads': ['难度', '配置', '考察能力'],
        'experiment': 'C+ 开启受限显式消息，C− 关闭消息接口；两组保留相同传感器、工具权限和预算。C− 仍能看到同伴动作，因此不等于完全没有信息交换。',
        'tools': '允许 agent 独立或借助通信编写建图、地图融合、规划程序和消息协议。实体工具不必需，自建软件工具也不强制；不按工具数量或代码长度加分。',
        'roadmap': '实施顺序：冻结合同 → L1 认证 → L2 实例 → 建图评测 → 通信对照 → 工具分析 → 能力扩展。',
        'closeout_title': '证据与设计状态',
        'closeout': '现有开发图参考包已交付；本页新增的是任务设计与实施清单。新等级、建图指标与对照实验尚待实现，物理有效性及正式准入继续单独记录。',
        'native_title': '现有 L1 配置与观察',
        'reference_note': '最新任务设计以全局建图、通信对照和可选自主工具构建为主线。本文保留历史参考执行及其证据范围。',
        'print_label': '可使用浏览器打印或保存 PDF',
    },
    'en': {
        'lang': 'en', 'other': 'zh', 'other_label': '中文',
        'title': 'Sokoban: From Local Views to a Global Map',
        'lead': 'Multiple robots build a consistent, updatable global map and clear routes through physical pushing. Compare explicit communication with no explicit messages; agents may build tools when useful.',
        'home': 'Tasks', 'evidence': 'Existing L1 evidence', 'doc': 'Full task design', 'download': 'Download design document',
        'status': 'Design update · 2026-10-28 · 0 new physics runs',
        'scope': 'L1 retains its development-map witness. L2/L3, mapping evaluation and communication comparisons await implementation and validation. task_success=null; formal_admission=false.',
        'summary_title': 'Task design: mapping, execution and communication',
        'flow': ['Local RGB and proprioception', 'Build and update a global map', 'Plan and physically push crates', 'Reach own goals legally'],
        'cards': [('Is the map correct?', 'Coverage, traversability and updates'), ('Is the task completed?', 'Legal pushing, stable dwell and recovery'), ('Does communication help?', 'Matched instances and budgets')],
        'levels': '<tr><td>SK-L1</td><td>Fixed development map · two G1s</td><td>Local exploration, mapping and physical execution</td></tr><tr><td>SK-L2</td><td>Unseen topology · two G1s</td><td>Global consistency, fusion and replanning</td></tr><tr><td>SK-L3</td><td>Matched map · changed capabilities</td><td>Embodiment-dependent reachability and roles</td></tr>',
        'heads': ['Level', 'Configuration', 'Capability'],
        'experiment': 'C+ enables bounded explicit messages; C− disables the message API. Keep sensors, tool permissions and budgets identical. C− can still observe peer motion, so it does not eliminate all information exchange.',
        'tools': 'Agents may independently or collaboratively write mapping, fusion and planning programs or messaging protocols. Neither physical tools nor self-built software are mandatory. Tool count and code length earn no direct credit.',
        'roadmap': 'Sequence: freeze contracts → certify L1 → build L2 instances → evaluate mapping → compare communication → analyze tools → extend capabilities.',
        'closeout_title': 'Evidence and design status',
        'closeout': 'The existing development-map reference packet has been delivered. This update adds a task design and implementation list. New levels, map metrics and comparisons remain planned; physical validity and formal admission are recorded separately.',
        'native_title': 'Existing L1 configuration and observations',
        'reference_note': 'The current task design focuses on global mapping, communication comparisons and optional self-built tools. This document retains the historical reference execution and its evidence scope.',
        'print_label': 'Use browser print to save a PDF',
    },
}


def render_design(root, language):
    t = TEXT[language]
    source = 'design.md' if language == 'zh' else 'design.en.md'
    raw = (root/'infra/planning/sokoban'/source).read_text('utf8')
    doc = fragment(markdown.markdown(raw, extensions=['tables', 'fenced_code']))
    doc.h1.decompose()
    links = []
    for index, heading in enumerate(doc.select('h2'), 1):
        heading['id'] = f'design-{index}'
        links.append(f'<a href="#design-{index}">{escape(heading.get_text())}</a>')
    # The document is served two directories above its Markdown source.
    for a in doc.select('a[href]'):
        if a['href'].startswith('../../'):
            a['href'] = a['href'][6:]
    wrap_tables(doc)
    page = f'''<!doctype html>
<html lang="{t['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="description" content="{escape(t['lead'], quote=True)}">
<title>{escape(t['title'])} · Task design</title><link rel="stylesheet" href="contribute.css"><style>{CSS}</style></head>
<body><a class="skip-link" href="#main">{'跳到正文' if language == 'zh' else 'Skip to content'}</a>
<header class="nav"><div class="wrap"><a class="brand" href="contribute-{language}.html">Embodied Terminal-Bench</a><nav><a href="task-sokoban-{language}.html">{t['evidence']}</a></nav><a class="lang" href="task-sokoban-design-{t['other']}.html">{t['other_label']}</a></div></header>
<main id="main"><div class="hero"><div class="wrap"><p class="eyebrow">{t['status']}</p><h1>{escape(t['title'])}</h1><p class="lead">{escape(t['lead'])}</p><p><a class="btn primary" href="planning/sokoban/{source}" download>{t['download']}</a></p><p class="muted">{t['print_label']}</p></div></div>
<article class="sokoban-design"><div class="wrap"><nav class="design-nav" aria-label="{'文档目录' if language == 'zh' else 'Document contents'}">{' · '.join(links)}</nav>{doc}</div></article></main>
<footer><div class="wrap">Embodied Terminal-Bench · Sokoban · 2026-10-28</div></footer></body></html>'''
    (root/f'infra/task-sokoban-design-{language}.html').write_text(page, 'utf8')


def update_task(root, language):
    t = TEXT[language]
    path = root/f'infra/task-sokoban-{language}.html'
    soup = fragment(path.read_text('utf8'))
    soup.title.string = t['title']+' · robo-si'
    soup.select_one('meta[name="description"]')['content'] = t['lead']
    if not soup.select_one('#sokoban-design-style'):
        style = soup.new_tag('style', attrs={'id': 'sokoban-design-style'})
        style.string = CSS
        soup.head.append(style)
    hero = soup.select_one('.hero')
    hero.h1.string = t['title']
    hero.select_one('.eyebrow').string = t['status']
    hero.select_one('.lead').string = t['lead']
    evidence_line = hero.select_one('.lead').find_next_sibling('p')
    evidence_line.string = t['scope']
    old_cards = hero.select_one('.cards')
    # Keep historical witness numbers with the witness, not the proposed design.
    if not soup.select_one('#witness-cards'):
        old_cards['id'] = 'witness-cards'
        soup.select_one('#witness h2').insert_after(old_cards.extract())
    elif old_cards:
        old_cards.decompose()
    cards = '<div class="cards">'+''.join(f'<div class="card"><h3>{escape(a)}</h3><p>{escape(b)}</p></div>' for a, b in t['cards'])+'</div>'
    hero.select_one('.wrap').append(fragment(cards))
    closeout = soup.select_one('#reference-closeout')
    closeout.h2.string = t['closeout_title']
    closeout.select_one('p').string = t['closeout']
    hero.insert_after(closeout.extract())
    soup.select_one('#task h2').string = t['native_title']
    source = 'design.md' if language == 'zh' else 'design.en.md'
    section = f'''<section class="sokoban-design" id="task-design"><div class="wrap"><h2>{t['summary_title']}</h2>
<ol class="design-flow">{''.join(f'<li><span>0{i}</span>{escape(x)}</li>' for i,x in enumerate(t['flow'],1))}</ol>
<table><thead><tr>{''.join('<th scope="col">'+x+'</th>' for x in t['heads'])}</tr></thead><tbody>{t['levels']}</tbody></table>
<p>{t['experiment']}</p><p>{t['tools']}</p><p class="design-note">{t['roadmap']}</p>
<p><a class="btn primary" href="task-sokoban-design-{language}.html">{t['doc']}</a> · <a href="planning/sokoban/{source}" download>{t['download']}</a> · <a href="#witness">{t['evidence']}</a></p></div></section>'''
    if soup.select_one('#task-design'):
        soup.select_one('#task-design').decompose()
    new_section = fragment(section)
    wrap_tables(new_section)
    hero.insert_after(new_section)
    top_link = soup.select_one('#main > p.wrap a')
    if top_link:
        top_link['href'] = '#task-design'
        top_link.string = t['doc']
    path.write_text(str(soup), 'utf8')


def update_reference(root):
    path = root/'infra/reference-designs/Sokoban.md'
    text = path.read_bytes().decode('utf8')
    marker = '<!-- sokoban-current-design -->'
    if marker not in text:
        newline = '\r\n' if '\r\n' in text else '\n'
        line, rest = text.split(newline, 1)
        text = line+newline+newline+marker+newline+'> 当前任务设计：[从局部观察到全局建图](../planning/sokoban/design.md)。以全局建图、通信对照和可选自主工具构建为主线；下文保留历史参考执行与证据范围。'+newline+rest
        path.write_bytes(text.encode('utf8'))
    path = root/'infra/reference-designs/Sokoban.html'
    text = path.read_bytes().decode('utf8')
    if 'id="current-sokoban-design"' not in text:
        text = text.replace('</h1>', '</h1><p id="current-sokoban-design">当前任务设计：<a href="../task-sokoban-design-zh.html">从局部观察到全局建图</a>。全局建图、通信对照与可选自主工具构建；下文保留历史参考执行与证据范围。</p>', 1)
        path.write_bytes(text.encode('utf8'))


def update_coverage(root):
    path = root/'infra/task-detail-coverage.json'
    raw = path.read_bytes().decode('utf8')
    newline = '\r\n' if '\r\n' in raw else '\n'
    data = json.loads(raw)
    for row in data['rows']:
        if row['task'] != 'Sokoban':
            continue
        row['sha256'] = hashlib.sha256((root/'infra'/row['page']).read_bytes()).hexdigest()
        for source in row['sources']:
            if source['path'] == 'infra/reference-designs/Sokoban.md':
                source['sha256'] = hashlib.sha256((root/source['path']).read_bytes()).hexdigest()
        row['design_update'] = {'date': '2026-10-28', 'scope': 'mapping-first task design; historical evidence retained',
                                'new_physics_runs': 0, 'new_browser_validation': False}
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').replace('\n', newline).encode('utf8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    for language in TEXT:
        render_design(args.root, language)
        update_task(args.root, language)
    update_reference(args.root)
    update_coverage(args.root)


if __name__ == '__main__':
    main()
