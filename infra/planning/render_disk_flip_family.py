"""Render the approved compact Disk Flip design; no physics or scorer changes."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import markdown
from bs4 import BeautifulSoup

IMPLEMENTATION = None
SUMMARY = {
    'zh': '4 个 task variants、3 种 embodiment、6 个选定 settings，使用 3 类盘体（2 套主要几何）。含 1 个原始配置和 5 个待验证配置；本次新增物理执行 0。',
    'en': '4 task variants, 3 embodiments and 6 selected settings, using 3 object profiles (2 main geometries). One original configuration and five unverified configurations; no new physics runs.',
}
BODIES = {'G': 'G1 + Dex3', 'F': 'G1 + Inspire five-finger hand', 'S': 'Stretch 3 + specified gripper'}
ROWS = [
    ('DF-01-G', 'DF-01', 'P1', 'G', '原版轻柔翻圆盘', 'Original gentle disk flip', '推到桌边、双手夹持翻面、放回并释放；保留原协议。', 'Push to the edge, flip under bimanual grasp, place and release; preserve the original protocol.'),
    ('DF-02-G', 'DF-02', 'P2', 'G', '带沿浅盘：三指抓取适配', 'Rimmed plate: three-finger grasp adaptation', '根据盘沿净空与手指几何，选择夹沿、托底或上下夹持。', 'Choose rim pinching, underside support or opposing-face grasp from rim clearance and finger geometry.'),
    ('DF-02-F', 'DF-02', 'P2', 'F', '带沿浅盘：五指抓取适配', 'Rimmed plate: five-finger grasp adaptation', '与 DF-02-G 同场景，只更换手及必要控制映射；检验抓取策略是否改变。', 'Same world as DF-02-G; change only the hand and required control mapping, testing whether grasp strategy changes.'),
    ('DF-03-G', 'DF-03', 'P3', 'G', '受力敏感浅盘翻面', 'Contact-load-limited plate flip', '在抗滑与局部载荷限制之间选择安全抓法，必要时分担载荷或利用桌面。', 'Balance slip resistance and local load limits; distribute load or use table support when needed.'),
    ('DF-04-G', 'DF-04', 'P1', 'G', '自主翻面：双臂配置', 'Open-strategy flip: dual-arm configuration', '自主选择单／双手抓持、重抓与支撑交接，不强制沿用原版动作顺序。', 'Choose one/two-hand grasp, regrasp and support transfer without the original mandatory sequence.'),
    ('DF-04-S', 'DF-04', 'P1', 'S', '自主翻面：单臂配置', 'Open-strategy flip: single-arm configuration', '与 DF-04-G 同物体、同桌面；按单臂与腕部能力选择完整翻面及释放策略。', 'Same object and table as DF-04-G; adapt the complete flip and release to one arm and its wrist.'),
]
PLATES = [
    ('P1', '标准实心圆盘', 'Standard solid disk', '直径 200 mm、厚 12 mm、质量 120 g；两面平整、质量均匀。', '200 mm diameter, 12 mm thick, 120 g; flat faces and uniform mass.', 'DF-01 / DF-04'),
    ('P2', '带盘沿浅盘', 'Rimmed shallow plate', '浅凹盘面、薄外沿、底部支撑圈；明确盘沿下方净空与倒扣支撑面。开发几何为外径 200 mm、总高 20 mm、120 g；14 mm 沿下净空，正放／倒扣静态支撑探针已通过。', 'Shallow concavity, thin rim and underside support ring; specify under-rim clearance and inverted support. Development geometry: 200 mm diameter, 20 mm total height, 120 g, 14 mm under-rim clearance. Upright/inverted static support probes passed.', 'DF-02'),
    ('P3', '受力敏感浅盘', 'Contact-load-sensitive shallow plate', '复用 P2 几何，增加局部接触载荷限制；首版固定摩擦与质量，保留安全可行抓法。刚体损伤代理，不模拟真实破碎。', 'Reuse P2 geometry with local contact-load limits. Initially fix friction and mass and retain a feasible safe grasp. Rigid-body damage proxy, not physical fracture.', 'DF-03'),
]


def table(headers, rows):
    return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---'] * len(headers)) + '|\n' + '\n'.join('| ' + ' | '.join(map(str, r)) + ' |' for r in rows) + '\n'


def block(text, name, content, before=None):
    start, end = f'<!-- {name}:start -->', f'<!-- {name}:end -->'
    new = start + '\n' + content + '\n' + end
    if start in text:
        return re.sub(re.escape(start) + '.*?' + re.escape(end), lambda _: new, text, flags=re.S)
    if before:
        assert text.count(before) == 1, before
        return text.replace(before, new + '\n' + before, 1)
    return text.rstrip() + '\n\n' + new + '\n'


def html(md, base):
    soup = BeautifulSoup(markdown.markdown(md, extensions=['tables']), 'html.parser')
    for a in soup.select('a[href]'):
        if not a['href'].startswith('#'):a['href'] = urljoin(base, a['href'])
    for node in soup.select('[src], [poster]'):
        for attr in ['src','poster']:
            if node.has_attr(attr):node[attr]=urljoin(base,node[attr])
    for t in soup.select('table'):
        t.wrap(soup.new_tag('div', attrs={'class': 'table-wrap', 'style': 'overflow-x:auto'}))
    return str(soup)


def document(lang):
    zh = lang == 'zh'
    name, detail = (4, 6) if zh else (5, 7)
    title = 'Disk Flip 任务族：精简任务清单与盘体设计' if zh else 'Disk Flip family: compact task list and object design'
    s = f'# {title}\n\n2026-10-29 · {SUMMARY[lang]}\n\n'
    s += ('独立操作问题计作 variant；setting 指任务＋身体＋场景的选定配置。参数取值、信息公开条件、消融及 seed 不另计任务，不铺满笛卡尔积。\n\n' if zh else 'A variant is an independent manipulation problem. A setting is a selected task/body/scene configuration. Parameter values, disclosure, ablations and seeds are not additional tasks; do not expand a Cartesian product.\n\n')
    s += ('## 任务清单\n\n' if zh else '## Task list\n\n')
    s += table(['Setting ID', 'Variant', '盘体' if zh else 'Object', 'Embodiment', '任务与核心考察' if zh else 'Task and mechanism', '状态' if zh else 'Status'], [[r[0], r[1], r[2], BODIES[r[3]], r[name] + '：' + r[detail], ('原声明范围参考' if zh else 'Historical scope only') if r[1] == 'DF-01' else ('待验证' if zh else 'Unverified')] for r in ROWS])
    s += '\n' + ('## 盘体设计\n\n' if zh else '## Object design\n\n')
    s += table(['ID', '盘体' if zh else 'Object', '结构与物性' if zh else 'Geometry and properties', '任务' if zh else 'Tasks'], [[p[0], p[1 if zh else 2], p[3 if zh else 4], p[5]] for p in PLATES])
    if zh:
        s += '''
需要冻结：盘径、盘体与盘沿厚度、盘沿宽度和下方净空、凹面深度、支撑圈尺寸、质量／质心／惯性、盘—手与盘—桌摩擦，以及适用的局部载荷限值。P2/P3 不沿用平圆盘的高度或接触判据，必须验证倒扣后稳定支撑和完整撤手。接触网格必须保留盘沿、凹面和可插入间隙，不能用填平凹面的碰撞体代替。

## 协议与配对

- 共同目标：目标面朝上，完整放入目标区域，释放后稳定；全过程满足公开安全约束。
- DF-01 保留原版双手夹持、动作顺序、评分器与阈值。6/6 完整执行和 2/2 回放只属于固定骨盆、双 Dex3、两个声明初始配置；正式准入仍为 false。
- DF-02～04 使用独立扩展协议，接受所有满足目标和公开约束的合法策略；明确允许重抓、桌面支撑和受控交接。具体容差、接触丢失、速度、载荷与稳定保持阈值须在实现前公开冻结；禁止依靠终态掩盖跌落或超限。
- DF-02-G/F 保持同一 G1 身体和相同基座约束，只更换手及必要映射。先验证实际抓持差异，不预设五指更强；若同一策略即可覆盖两者，取消额外手型配置。
- DF-04-G/S 保持物体、桌面、目标和扩展评分一致，分别设置经过验证的起始站位；执行中基座固定。必须先建立 Stretch 的完整翻面与释放见证。单臂筛查失败不等于物理不可行。
- DF-03 的损伤代理使用明确的局部载荷指标，不能以相互抵消后的接触合力代替夹持挤压力。阈值必须保留安全可行解，不能把视觉材质当成真实脆性。

## 范围与验证状态

三种 embodiment 为 G1＋Dex3、G1＋Inspire 五指手、Stretch 3＋指定夹爪。复用现有任务族的 Stretch 3 资产；夹爪与控制接口须绑定具体资产。A3、双臂轮式和 Stretch 4 暂不另列。

椭圆／方盘、摩擦／质量／质心变化、已知／未知参数和主动探测消融均暂作任务内配置或储备，不新增主任务。探测允许使用的传感器需单独声明，跨身体成功本身不等于已证明 self-modeling。

当前登记为 4 个 variants、6 个 settings（1 个原始＋5 个扩展）、3 类盘体、2 套主要几何。新增物理执行 0，未验证扩展不得继承原成绩。不修改原 14 项基准目录数量、原控制器、评分器、证据或正式准入状态。

[原任务与参考证据](/infra/task-disk-flip-zh.html#task) · [任务族总览](/infra/task-families-zh.html#disk-flip-family) · [English](README-en.md) · [结构化清单](task-design.json)
'''
    else:
        s += '''
Freeze diameter, body/rim thickness, rim width and underside clearance, concavity, support-ring geometry, mass/COM/inertia, hand–object and table–object friction, and applicable local load limits. P2/P3 need stable inverted support and complete withdrawal; do not reuse the flat disk's height/contact predicates. Collision geometry must preserve the rim, cavity and insertion gaps rather than filling them.

## Protocols and paired comparisons

- Shared goal: target face up, fully in the goal region, released and stable, with public safety constraints satisfied throughout.
- DF-01 freezes the original bimanual requirement, sequence, scorer and limits. Its 6/6 executions and 2/2 replays cover only the fixed-pelvis dual-Dex3 reference and two declared initial configurations. Formal admission remains false.
- DF-02–04 use a separate extension protocol accepting every strategy satisfying the goal and public constraints, including regrasp, table support and controlled transfer. Freeze tolerances, contact-loss rules, speed/load limits and dwell times before implementation. Terminal pose cannot excuse a drop or a limit violation.
- DF-02-G/F use the same G1 body/base constraints, changing only the hand and necessary control mapping. Verify actual grasp differences rather than assuming five fingers are superior; remove the extra hand configuration if the same strategy covers both.
- DF-04-G/S share the object, table, goal and extension scorer, with separately validated initial placements and fixed bases during execution. First establish a complete Stretch flip-and-release witness. Failed single-arm screening does not prove impossibility.
- DF-03 uses an explicit local-load damage proxy. A net force that cancels opposing contacts is not a squeeze-load measure. Preserve a safe feasible grasp; visual materials do not establish physical fragility.

## Scope and validation

The three embodiments are G1 + Dex3, G1 + Inspire five-finger hand, and Stretch 3 + a specified gripper. Reuse the existing families' Stretch 3 assets; bind the gripper and control interface to concrete assets. A3, dual-arm wheeled bodies and Stretch 4 are not additional entries.

Elliptical/rectangular shapes, friction/mass/COM changes, known/unknown parameters and active-probing ablations remain within-task configurations or reserves. Declare available sensors separately; cross-body success alone does not establish self-modeling.

Registration: 4 variants, 6 settings (one original plus five extensions), 3 object profiles and 2 main geometries. No new physics runs. New settings do not inherit historical scores. The original 14-task inventory count, controller, scorer, evidence and admission state are unchanged.

[Original task and reference evidence](/infra/task-disk-flip-en.html#task) · [Family overview](/infra/task-families-en.html#disk-flip-family) · [中文](README.md) · [Structured design](task-design.json)
'''
    if IMPLEMENTATION:
        s=s.replace('新增物理执行 0，', f'已实现并实际运行全部 6 个配置的候选专家；完整见证 {IMPLEMENTATION["settings_with_full_witness"]}/6，')
        s=s.replace('No new physics runs.', f'Candidate experts have been executed for all six settings; {IMPLEMENTATION["settings_with_full_witness"]} settings have a complete witness.')
        s=s.replace('原声明范围参考', '新执行＋独立回放通过').replace('Historical scope only', 'Fresh execution + replay passed')
        s=s.replace('| 待验证 |', '| 已运行；尚无完整见证 |').replace('| Unverified |', '| Executed; no full witness |')
        for actual in IMPLEMENTATION['selected']:
            if actual['success']:
                label = '完整见证＋独立回放通过；验收另列' if zh else 'Complete witness + replay passed; acceptance tracked separately'
                s = '\n'.join(re.sub(r'\| (?:已运行；尚无完整见证|Executed; no full witness) \|$', '| ' + label + ' |', line) if line.startswith('| ' + actual['setting'] + ' |') else line for line in s.split('\n'))
        s += '\n' + ('[逐项专家实现、计划、轨迹与视频](IMPLEMENTATION.md) · [执行台账](implementation.json)\n' if zh else '[Per-setting experts, plans, trajectories and videos](IMPLEMENTATION-en.md) · [Run ledger](implementation.json)\n')
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    root = parser.parse_args().root
    infra = root / 'infra'
    planning = infra / 'planning'
    out = planning / 'disk-flip-family'
    out.mkdir(parents=True, exist_ok=True)
    global IMPLEMENTATION
    if (out/'implementation.json').exists():
        IMPLEMENTATION=json.loads((out/'implementation.json').read_text())
        witness=IMPLEMENTATION['settings_with_full_witness']
        SUMMARY['zh']=f'4 个 task variants、3 种 embodiment、6 个选定 settings，使用 3 类盘体（2 套主要几何）。6 个配置均有候选专家与物理执行；{witness} 个完整成功见证，{6-witness} 个仍待完成。'
        SUMMARY['en']=f'4 task variants, 3 embodiments and 6 selected settings, using 3 object profiles (2 main geometries). All six have candidate experts and physics executions; {witness} complete witnesses, {6-witness} still unresolved.'
    changed = []
    def write(p, value):
        p.write_text(value, encoding='utf-8')
        changed.append(str(p.relative_to(root)))
    data = {'schema': 'disk-flip-family/1.0', 'updated': '2026-10-29', 'status': 'design_registration', 'author_only': True, 'agent_bundle_allowed': False,
            'variant_count': 4, 'embodiment_count': 3, 'setting_count': 6, 'object_profile_count': 3, 'geometry_count': 2,
            'original_setting_count': 1, 'unverified_setting_count': 5, 'new_simulation_runs': 0,
            'changes_existing_14_task_inventory': False, 'embodiments': BODIES,
            'counting': 'independent operation variants; selected task/body/scene settings; no Cartesian product',
            'objects': [{'id': p[0], 'name': {'zh': p[1], 'en': p[2]}, 'design': {'zh': p[3], 'en': p[4]}, 'status': 'historical_scope_only' if p[0] == 'P1' else 'design_unverified'} for p in PLATES],
            'settings': [{'id': r[0], 'variant': r[1], 'object': r[2], 'embodiment': r[3], 'name': {'zh': r[4], 'en': r[5]}, 'mechanism': {'zh': r[6], 'en': r[7]}, 'status': 'historical_scope_only' if r[1] == 'DF-01' else 'planned_unverified', 'protocol': 'original_frozen' if r[1] == 'DF-01' else 'open_strategy_extension', 'new_witness': None} for r in ROWS]}
    if IMPLEMENTATION:
        data.update(unverified_setting_count=6-IMPLEMENTATION['settings_with_full_witness'],extension_setting_count=5,status='implementation_in_progress',new_simulation_runs=IMPLEMENTATION['physical_attempts'],implementation='implementation.json',complete_witness_settings=IMPLEMENTATION['settings_with_full_witness'])
        for row in data['settings']:
            actual=next(x for x in IMPLEMENTATION['selected'] if x['setting']==row['id'])
            row.update(status='fresh_witness_verified' if actual['success'] else 'implemented_failed_attempt',evidence=actual['evidence'],new_witness=actual['run'] if actual['success'] else None)
        for obj in data['objects']:obj['prototype_support_probe']='execution/plate-design/support-probes.json'
    write(out / 'task-design.json', json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    for lang in ('zh', 'en'):
        zh = lang == 'zh'
        filename = 'README.md' if zh else 'README-en.md'
        doc = document(lang)
        write(out / filename, doc)
        body = html(doc.replace('# ', '## ', 1), f'/infra/planning/disk-flip-family/{filename}')
        section = '<section class="tinted" id="disk-flip-family"><div class="wrap">' + body + '</div></section>'
        page = infra / f'task-disk-flip-{lang}.html'
        write(page, block(page.read_text(), 'disk-flip-family', section, '<section id="task">'))
        if IMPLEMENTATION:
            impl_name='IMPLEMENTATION.md' if zh else 'IMPLEMENTATION-en.md'
            implementation_body=html((out/impl_name).read_text().replace('# ', '## ', 1), f'/infra/planning/disk-flip-family/{impl_name}')
            write(page,block(page.read_text(),'disk-flip-implementation','<section id="disk-flip-implementation"><div class="wrap">'+implementation_body+'</div></section>','<!-- disk-flip-family:start -->'))
        text = page.read_text()
        jump = '<p class="wrap"><a href="#disk-flip-family">' + ('新任务族：4 个 variants · 6 个配置与盘体设计' if zh else 'New family: 4 variants · 6 settings and object design') + '</a></p>'
        if IMPLEMENTATION:jump += '<p class="wrap"><a href="#disk-flip-implementation">'+('专家实现进展：计划 · 轨迹 · 物理验证 · 视频' if zh else 'Expert implementation: plans · trajectories · physics · video')+'</a></p>'
        write(page, block(text, 'disk-flip-family-jump', jump, '<div class="hero">'))
        overview = ('## Disk Flip 任务族\n\n' if zh else '## Disk Flip family\n\n') + SUMMARY[lang] + f'\n\n[Task list / 任务与盘体设计](/infra/task-disk-flip-{lang}.html#disk-flip-family) · [Markdown](disk-flip-family/{filename}) · [JSON](disk-flip-family/task-design.json)\n'
        md = planning / ('task-families.md' if zh else 'task-families-en.md')
        write(md, block(md.read_text(), 'disk-flip-family-overview', overview))
        p = infra / f'task-families-{lang}.html'
        write(p, block(p.read_text(), 'disk-flip-family-overview', '<section id="disk-flip-family"><div class="wrap">' + html(overview, '/infra/planning/task-families.md') + '</div></section>', '</main>'))
        p = infra / f'contribute-{lang}.html'
        text = p.read_text()
        match = re.search(r'<article\b[^>]*\bid="disk-flip".*?</article>', text, re.S)
        assert match, p
        content = f'<details><summary>{"任务族：4 variants · 6 settings" if zh else "Family: 4 variants · 6 settings"}</summary><p>{SUMMARY[lang]}</p><a href="/infra/task-disk-flip-{lang}.html#disk-flip-family">{"任务与盘体设计" if zh else "Tasks and object design"}</a></details>'
        card = block(match.group(), 'disk-flip-family-card', content, '</article>')
        write(p, text[:match.start()] + card + text[match.end():])
    p = planning / 'task-families.json'
    registry = json.loads(p.read_text())
    registry['disk_flip_family'] = {'updated': '2026-10-29', 'variant_count': 4, 'setting_count': 6, 'embodiment_count': 3, 'object_profile_count': 3, 'status': 'design_registration', 'new_simulation_runs': 0, 'design': 'disk-flip-family/task-design.json', 'documentation': {'zh': 'disk-flip-family/README.md', 'en': 'disk-flip-family/README-en.md'}}
    if IMPLEMENTATION:registry['disk_flip_family'].update(status='implementation_in_progress',new_simulation_runs=IMPLEMENTATION['physical_attempts'],complete_witness_settings=IMPLEMENTATION['settings_with_full_witness'],implementation='disk-flip-family/implementation.json')
    write(p, json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    p = infra / 'task-catalog.json'
    catalog = json.loads(p.read_text())
    entry = next(e for e in catalog['entries'] if e['id'] == 'DiskFlip')
    entry['family_extension'] = {'family': 'DF', 'as_of': '2026-10-29', 'status': 'design', 'counted': 4, 'original_count': 1, 'extension_count': 3, 'counting': 'independent_manipulation_problem', 'planned_body_configuration_count': 6, 'embodiment_count': 3, 'object_profile_count': 3, 'summary': SUMMARY, 'page': {lang: f'/infra/task-disk-flip-{lang}.html#disk-flip-family' for lang in ('zh', 'en')}, 'design': '/infra/planning/disk-flip-family/README.md', 'task_ids': ['DF-01', 'DF-02', 'DF-03', 'DF-04']}
    if IMPLEMENTATION:entry['family_extension'].update(status='implementation_in_progress',complete_witness_settings=IMPLEMENTATION['settings_with_full_witness'],implementation='/infra/planning/disk-flip-family/implementation.json')
    write(p, json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    for p in (planning / 'README.md', root / 'humanoid/g1_tabletop_disk_flip/README.md'):
        if p.exists():
            prefix = 'disk-flip-family/' if p.parent == planning else '../../infra/planning/disk-flip-family/'
            write(p, block(p.read_text(), 'disk-flip-family-index', '## Disk Flip family · 2026-10-29\n\n' + SUMMARY['zh'] + f'\n\n[中文设计]({prefix}README.md) · [English design]({prefix}README-en.md) · [JSON]({prefix}task-design.json)\n\nOriginal evidence and admission remain scoped to DF-01-G.'))
    print(json.dumps({'changed_paths': sorted(set(changed)), 'variants': 4, 'settings': 6, 'new_simulation_runs': IMPLEMENTATION['physical_attempts'] if IMPLEMENTATION else 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
