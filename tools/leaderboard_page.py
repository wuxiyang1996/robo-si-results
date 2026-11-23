"""Render the audited leaderboard using the site's shared shell and translations."""
import csv
import io
import json
from collections import Counter

STATUS = {
    'verified_success': ('确认成功', 'Verified success'),
    'valid_evaluation_unsuccessful': ('有效评分 · 未成功', 'Valid evaluation · unsuccessful'),
    'evaluation_invalid': ('评测无有效成绩', 'Invalid evaluation'),
    'solver_attempted_no_valid_evaluation': ('尝试启动 · 无有效评分', 'Launch attempted · no valid score'),
    'preflight_failed': ('预检失败', 'Preflight failed'),
    'frozen_source_mismatch': ('冻结源码不匹配', 'Frozen source mismatch'),
    'evaluated_elsewhere_per_user': ('外部评测 · 未收录', 'External evaluation · not collected'),
    'excluded_per_user_20261115': ('按要求排除', 'Excluded by request'),
    'outside_original_astra_192': ('原计划外', 'Outside original plan'),
}


def render_leaderboard(site):
    tr, e, link = site.tr, site.e, site.link
    data = json.loads((site.SOURCE/'content/leaderboard.json').read_text(encoding='utf-8'))
    tasks, summary = data['tasks'], data['summary']
    assert len(tasks) == len({t['case'] for t in tasks}) == 246
    assert set(t['case'] for t in tasks) == set(site.RECORDS)
    assert dict(Counter(t['status'] for t in tasks)) == summary['case_status_counts']
    assert sum(t['valid'] for t in tasks) == 30 and sum(t['success'] is True for t in tasks) == 2
    site.write('data/leaderboard.json', json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    fields = ['case','family','local_scope','status','valid','success','native_score','snapshot','attempts','standard_ready','privileged_ready']
    csv_file = io.StringIO(newline='')
    writer = csv.DictWriter(csv_file, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(tasks)
    site.write('data/leaderboard-tasks.csv', '\ufeff'+csv_file.getvalue())

    def table(headers, rows, name):
        return f'<div class="lb-table-scroll" role="region" aria-label="{e(name)}" tabindex="0"><table class="lb-table"><thead><tr>'+''.join('<th scope="col">'+tr(*h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

    def cell(text): return '<td>'+text+'</td>'
    metrics = [(246,'任务总数','Benchmark tasks'),(29,'任务族','Task families'),(30,'Astra 有效评分','Valid Astra evaluations'),(2,'Astra 确认成功','Verified Astra successes')]
    stats = '<div class="lb-stats">'+''.join(f'<div><strong>{n}</strong>'+tr(zh,en)+'</div>' for n,zh,en in metrics)+'</div>'
    hero = '<section class="page-hero"><div class="wrap"><p class="eyebrow">RESULTS &amp; LEADERBOARD</p>'+tr('排行榜与评测结果','Leaderboard & evaluation results','h1')+tr('完整 246 项任务的参考记录、沙箱就绪状态与 Astra 实测结果。每个数字都可追溯到对应任务。','Reference records, sandbox readiness and observed Astra results across all 246 tasks. Every count is traceable to individual tasks.','p','class="lead"')+'<p class="lb-meta">'+tr('更新：2026-11-23 · 评测记录截至 2026-11-15 10:42 EST','Updated: 2026-11-23 · Run records through Nov 15, 2026, 10:42 EST')+'</p>'+stats+'</div></section>'
    row = '<tr><td><strong>Astra</strong><small>Codex · xhigh · Privileged</small></td>'+cell('99 / 246')+cell('30')+cell('<strong class="lb-success">2</strong>')+cell('28')+cell(tr('— 未完整评测','— Incomplete evaluation'))+cell(tr('探索性记录','Exploratory results'))+'</tr>'
    ranking = '<section class="section lb-section"><div class="wrap"><div class="section-head"><div><p class="eyebrow">MODEL RESULTS</p>'+tr('模型结果','Model results','h2')+'</div><a class="button" href="#task-results">'+tr('查看逐项结果','View task results')+'</a></div>'+table([('模型／设置','Model / setup'),('本机范围','Local scope'),('有效评分','Valid scores'),('确认成功','Successes'),('有效未成功','Unsuccessful'),('246 项成功率','246-task success rate'),('评测性质','Run type')],[row],'模型结果 / Model results')+'<div class="lb-note">'+tr('当前没有可正式排名的完整运行。Astra 包含多候选、重试、开发中断和中途策略补评测；不是官方 EFE 榜单运行。2 / 30 仅描述已获得有效评分的任务，不能代表整个基准的模型成功率。','No complete run is currently eligible for a formal ranking. Astra includes multiple candidates, retries, interrupted development and snapshot evaluations; this is not an official EFE run. The 2 / 30 count describes only tasks with valid evaluations, not benchmark-wide model performance.','p')+tr('每项累计开发上限为 4 小时；18 项中途策略补评测中，15 项有效但未成功，3 项无有效成绩。这些策略尚未完成开发，不能视为全部用满预算后的结果。','The cumulative development cap is 4 hours per task. Of 18 snapshot evaluations, 15 are valid but unsuccessful and 3 have no valid score. Those policies were still under development and do not represent completed full-budget trials.','p')+'</div></div></section>'
    coverage = '<section class="section lb-section"><div class="wrap"><p class="eyebrow">BENCHMARK COVERAGE</p>'+tr('完整任务覆盖','Complete task coverage','h2')+'<div class="lb-coverage"><article><h3>'+tr('参考专家交付','Reference expert delivery')+'</h3><strong>246 / 246</strong>'+tr('29 个任务族；每项均关联既有参考演示。参考记录保留正确退出与有限验收范围，属于特权状态专家交付。','29 task families, each linked to an existing reference demonstration. Reference records retain correct-exit and limited-acceptance scopes and come from privileged-state experts.','p')+link('tasks/','浏览参考演示','Browse reference demonstrations','')+'</article><article><h3>'+tr('沙箱就绪检查','Sandbox readiness')+'</h3><strong>492 / 492</strong>'+tr('Standard 246 / 246；Privileged 246 / 246。检查输入、动作、原生评分和重置／独立评测接口，就绪通过不等于模型成功。','Standard 246 / 246; Privileged 246 / 246. Checks cover inputs, actions, native grading and reset / independent evaluation interfaces. Readiness does not imply model success.','p')+'</article></div></div></section>'
    family_rows = []
    for family in sorted({t['family'] for t in tasks}):
        subset = [t for t in tasks if t['family'] == family]
        title = site.FAMILIES[family]
        family_rows.append('<tr><th scope="row">'+link(site.family_url(family),family,family,'')+'<small>'+tr(title['title_zh'],title['title_en'])+'</small></th>'+''.join(cell(str(v)) for v in [len(subset),sum(t['local_scope'] for t in subset),sum(t['valid'] for t in subset),sum(t['success'] is True for t in subset),sum(t['success'] is False for t in subset)])+'</tr>')
    families = '<section class="section lb-section"><div class="wrap"><details class="lb-families"><summary>'+tr('查看 29 个任务族的汇总','Explore all 29 task families')+'</summary>'+table([('任务族','Family'),('任务数','Tasks'),('本机范围','Local scope'),('有效评分','Valid scores'),('确认成功','Successes'),('有效未成功','Unsuccessful')],family_rows,'任务族汇总 / Family summary')+'</details></div></section>'
    counts = Counter(t['status'] for t in tasks)
    options = '<option value="" data-zh="全部状态" data-en="All statuses">全部状态</option>'+''.join(f'<option value="{s}" data-zh="{e(zh)} ({counts[s]})" data-en="{e(en)} ({counts[s]})">{e(zh)} ({counts[s]})</option>' for s,(zh,en) in STATUS.items())
    family_options = '<option value="" data-zh="全部任务族" data-en="All families">全部任务族</option>'+''.join(f'<option>{e(f)}</option>' for f in sorted({t['family'] for t in tasks}))
    task_rows = []
    for t in tasks:
        rid = t['case']; task = site.TASKS[rid]
        tone = 'success' if t['success'] else ('scored' if t['valid'] else 'missing')
        score = '—' if t['native_score'] is None else f"{t['native_score']:g}"
        badge = f'<span class="lb-status lb-{tone}">'+tr(*STATUS[t['status']])+'</span>'
        if t['snapshot']: badge += '<small>'+tr('含中途策略补评测','Includes snapshot evaluation')+'</small>'
        proof = ''
        if t['evidence']:
            proof_path = 'data/leaderboard-evidence/'+rid+'.json'
            site.write(proof_path,json.dumps(t['evidence'],ensure_ascii=False,indent=2)+'\n')
            proof = link(proof_path,'评分记录摘要','Evaluation digest','')
        else: proof = tr('— 无有效成绩','— No valid score')
        task_rows.append(f'<tr data-lb-row data-case="{e(rid)}" data-family="{e(t["family"])}" data-status="{e(t["status"])}" data-search="{e((rid+" "+task["title_zh"]+" "+task["title_en"]).lower())}"><th scope="row">'+link(site.family_url(t['family'])+'#'+rid,rid,rid,'')+'<small>'+tr(task['title_zh'],task['title_en'])+'</small></th>'+cell(e(t['family']))+cell(badge)+cell(score)+cell(tr('两模式就绪','Both modes ready'))+cell(link(site.family_url(t['family'])+'#'+rid,'参考演示','Reference demo','')+'<small>'+proof+'</small>')+'</tr>')
    filters = '<div class="lb-filters"><div><label for="lb-search">'+tr('搜索任务','Search tasks')+'</label><input id="lb-search" type="search" data-placeholder-zh="任务 ID 或任务名称" data-placeholder-en="Task ID or title" placeholder="任务 ID 或任务名称"></div><div><label for="lb-family">'+tr('任务族','Family')+f'</label><select id="lb-family">{family_options}</select></div><div><label for="lb-status">'+tr('Astra 状态','Astra status')+f'</label><select id="lb-status">{options}</select></div><button id="lb-clear" type="button">'+tr('清除筛选','Clear filters')+'</button></div>'
    details = '<section class="section lb-section" id="task-results"><div class="wrap"><div class="section-head"><div><p class="eyebrow">TASK-BY-TASK RESULTS</p>'+tr('246 项任务明细','All 246 task results','h2')+'</div>'+link('data/leaderboard-tasks.csv','下载 CSV','Download CSV','')+'</div>'+tr('原生 score 保留各任务的评分尺度，不跨任务求平均。无有效评分显示为「—」，不计作零分。参考演示来自既有专家记录，不是 Astra 运行录像。','Native scores retain each task’s grading scale and are not averaged across tasks. Missing or invalid scores appear as “—”, not zero. Reference demos are existing expert records, not Astra rollout videos.','p')+filters+'<p id="lb-count" role="status" aria-live="polite" data-zh="显示 246 / 246 项任务" data-en="Showing 246 / 246 tasks">显示 246 / 246 项任务</p>'+table([('任务','Task'),('任务族','Family'),('Astra 结果','Astra result'),('原生 score','Native score'),('沙箱','Sandbox'),('查看记录','Explore')],task_rows,'逐项评测结果 / Task results')+'<p id="lb-empty" hidden>'+tr('没有匹配结果，请调整筛选条件。','No matching tasks. Try different filters.')+'</p></div></section>'
    methods = '<section class="section lb-section" id="methodology"><div class="wrap lb-method"><p class="eyebrow">SOURCES &amp; COUNTING</p>'+tr('数据来源与统计口径','Sources & counting policy','h2')+'<ul>'+tr('本机 Astra 范围 99 项；用户说明在其他机器评测、此处未核验的 48 项；按要求排除的 45 项；原始 Astra 192 项计划外的 54 项。合计 246 项。','99 tasks in the local Astra scope; 48 reported evaluated elsewhere without locally verified results; 45 excluded by request; and 54 outside the original 192-task plan. Total: 246.','li')+tr('按不同任务计数：优先采用独立评分确认的成功，否则采用最近一次有效评分；预检、探针和无效评测不算有效失败。所有候选的历史尝试不会被当成独立任务。','Count unique tasks: prefer an independently verified success, otherwise the most recent valid evaluation. Preflight checks, probes and invalid evaluations are not scored failures. Historical candidate attempts are not separate tasks.','li')+tr('数据来自 astra_246_20261123 结果包。网页数据保留源文件 SHA-256 与包内证据路径；评分摘要只摘取核验字段，完整原始证据保留在本地结果包。未重新运行模型或仿真。','Imported from the astra_246_20261123 result bundle. Web data retains source SHA-256 hashes and bundle-relative evidence paths. Evaluation digests contain selected verification fields; full original evidence remains in the local bundle. No model or simulation was rerun.','li')+'</ul><div class="hero-actions">'+link('data/leaderboard.json','下载完整排行榜 JSON','Download leaderboard JSON','button')+link('data/video-gallery.json','参考记录清单','Reference record manifest','')+'</div></div></section>'
    assets = f'<link rel="stylesheet" href="{site.asset("assets/leaderboard.css")}"><script defer src="{site.asset("assets/leaderboard.js")}"></script>'
    site.page('leaderboard.html','排行榜与评测结果','Leaderboard & evaluation results','246 项任务、29 个任务族的参考记录、沙箱就绪与 Astra 实测结果。',assets+hero+ranking+coverage+families+details+methods,active='leaderboard')
