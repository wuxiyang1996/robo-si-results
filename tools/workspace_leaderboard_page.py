"""Render the complete Astra result inventory with explicit score denominators."""
import csv
import io
import json
from collections import Counter

STATUS={
    'verified_success':('确认成功','Verified success'),
    'valid_unsuccessful':('有效评分 · 未成功','Valid score · unsuccessful'),
    'invalid_evaluation':('评测无效 · 待重评','Invalid evaluation · awaiting regrade'),
    'no_submission':('缺少提交 · 待补跑','No submission · awaiting retry'),
    'no_valid_evaluation':('无有效评分 · 待补跑','No valid score · awaiting retry'),
}


def render_leaderboard(site):
    tr,e,link=site.tr,site.e,site.link
    data=json.loads((site.SOURCE/'content/leaderboard.json').read_text(encoding='utf-8'))
    tasks,s=data['tasks'],data['summary']
    assert len(tasks)==len({t['case'] for t in tasks})==246
    assert {t['case'] for t in tasks}==set(site.RECORDS)
    assert dict(Counter(t['status'] for t in tasks))==s['case_status_counts']
    site.write('data/leaderboard.json',json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    fields=['case','family','status','valid','success','native_score','stage_score','campaign','effort','regrade','snapshot','attempts','standard_ready','privileged_ready']
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(tasks)
    site.write('data/leaderboard-tasks.csv','\ufeff'+output.getvalue())

    def table(headers,rows,name):
        return f'<div class="lb-table-scroll" role="region" aria-label="{e(name)}" tabindex="0"><table class="lb-table"><thead><tr>'+''.join('<th scope="col">'+tr(*h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
    def td(value):return '<td>'+str(value)+'</td>'
    def number(value):return '—' if value is None else f'{value:g}'
    def section(content,attr=''):
        return '<section class="section lb-section" '+attr+'><div class="wrap">'+content+'</div></section>'

    stats=[(246,'完整任务范围','Complete task scope'),(s['valid'],'有效独立评分','Valid evaluations'),(s['success'],'确认成功','Verified successes'),(s['pending'],'待补有效成绩','Scores to complete')]
    hero='<section class="page-hero"><div class="wrap"><p class="eyebrow">RESULTS &amp; LEADERBOARD</p>'
    hero+=tr('Astra · 完整任务评分','Astra · full task results','h1')
    hero+=tr('汇总工作区与已归档远端结果，逐项核对 246 个任务的成功状态、原生分数和阶段分。','All retained workspace and archived remote results, reconciled across 246 tasks with success status, native scores and stage scores.','p','class="lead"')
    hero+='<p class="lb-meta">'+tr('数据核验：'+data['updated']+' · 29 个任务族','Data audited: '+data['updated']+' · 29 task families')+'</p>'
    hero+='<div class="lb-stats">'+''.join(f'<div><strong>{n}</strong>'+tr(zh,en)+'</div>' for n,zh,en in stats)+'</div></div></section>'

    fraction=100*s['verified_success_fraction_all_tasks']
    rate_label=tr('已确认成功占比','Verified success fraction') if s['pending'] else tr('任务成功率','Task success rate')
    score_mean=f"{s['stage_score_mean_valid']:.2f}" if s['stage_score_mean_valid'] is not None else '—'
    model_row='<tr><th scope="row">Astra<small>Codex · Privileged · high / xhigh</small></th>'
    model_row+=td(str(s['valid'])+' / 246')+td(s['success'])+td(s['unsuccessful'])
    model_row+=td(f'{fraction:.2f}%<small>'+rate_label+f' · {s["success"]} / 246</small>')
    model_row+=td(score_mean+' / 100<small>'+tr(f'{s["stage_score_count"]} 项有阶段分',f'{s["stage_score_count"]} tasks with stage scores')+'</small>')+td(s['pending'])+'</tr>'
    model='<div class="section-head"><div><p class="eyebrow">MODEL RESULTS</p>'+tr('评分汇总','Score summary','h2')+'</div><a class="button" href="#task-results">'+tr('查看全部任务','View all tasks')+'</a></div>'
    model+=table([('模型／设置','Model / setup'),('有效评分覆盖','Valid score coverage'),('确认成功','Successes'),('有效未成功','Unsuccessful'),('全部 246 项','All 246 tasks'),('已评分阶段均分','Mean available stage score'),('待补成绩','Pending')],[model_row],'Astra 评分 / Astra results')
    pending_zh=f'还有 {s["pending"]} 项等待有效成绩。已确认成功占比以全部 246 项为分母，表示当前已证实的下界；完整运行成功率在评测补齐后给出。'
    pending_en=f'{s["pending"]} tasks still await valid scores. The verified success fraction uses all 246 tasks as its denominator and is a confirmed lower bound; the complete-run rate becomes available after evaluation is complete.'
    if not s['pending']:
        pending_zh='246 项均有有效独立评分，成功率以全部任务为分母。'
        pending_en='All 246 tasks have valid independent evaluations; the success rate uses every task.'
    model+='<div class="lb-note">'+tr(pending_zh,pending_en,'p')
    model+=tr(f'阶段均分只包含有原生阶段分的 {s["stage_score_count"]} 项；缺失成绩不填零。不同任务的原生 score 保留原始尺度，统一阶段分单列为 0–100。',f'The stage mean includes only the {s["stage_score_count"]} tasks with native stage scores; missing values are not zero-filled. Native scores retain task-specific scales, while stage scores use a separate 0–100 scale.','p')+'</div>'

    families=[]
    for family in sorted({t['family'] for t in tasks}):
        group=[t for t in tasks if t['family']==family];scores=[t['stage_score'] for t in group if t['stage_score'] is not None]
        title=site.FAMILIES[family]
        row='<tr><th scope="row">'+link(site.family_url(family),family,family,'')+'<small>'+tr(title['title_zh'],title['title_en'])+'</small></th>'
        row+=''.join(td(x) for x in [len(group),sum(t['valid'] for t in group),sum(t['success'] is True for t in group),sum(not t['valid'] for t in group)])
        families.append(row+td(f'{sum(scores)/len(scores):.2f} ({len(scores)})' if scores else '—')+'</tr>')
    family_section='<details class="lb-families"><summary>'+tr('29 个任务族：覆盖、成功与阶段分','29 families: coverage, successes and stage scores')+'</summary>'
    family_section+=table([('任务族','Family'),('任务数','Tasks'),('有效评分','Valid scores'),('成功','Successes'),('待补','Pending'),('阶段均分（项数）','Stage mean (tasks)')],families,'任务族评分 / Family scores')+'</details>'

    counts=Counter(t['status'] for t in tasks)
    options='<option value="" data-zh="全部状态" data-en="All statuses">全部状态</option>'
    options+=''.join(f'<option value="{state}" data-zh="{e(zh)} ({counts[state]})" data-en="{e(en)} ({counts[state]})">{e(zh)} ({counts[state]})</option>' for state,(zh,en) in STATUS.items() if counts[state])
    family_options='<option value="" data-zh="全部任务族" data-en="All families">全部任务族</option>'+''.join('<option>'+e(f)+'</option>' for f in sorted({t['family'] for t in tasks}))
    filters='<div class="lb-filters"><div><label for="lb-search">'+tr('搜索任务','Search tasks')+'</label><input id="lb-search" type="search" data-placeholder-zh="任务 ID 或任务名称" data-placeholder-en="Task ID or title" placeholder="任务 ID 或任务名称"></div>'
    filters+='<div><label for="lb-family">'+tr('任务族','Family')+'</label><select id="lb-family">'+family_options+'</select></div><div><label for="lb-status">'+tr('结果状态','Result status')+'</label><select id="lb-status">'+options+'</select></div><button id="lb-clear" type="button">'+tr('清除筛选','Clear filters')+'</button></div>'
    rows=[]
    for task in tasks:
        rid=task['case'];copy=site.TASKS[rid]
        tone='success' if task['success'] else 'scored' if task['valid'] else 'missing'
        status=f'<span class="lb-status lb-{tone}">'+tr(*STATUS[task['status']])+'</span><small>'+e(task['effort'])
        if task['regrade']:status+=' · '+tr('冻结策略重评','Frozen-policy regrade')
        if task['snapshot']:status+=' · '+tr('策略快照','Policy snapshot')
        status+='</small>'
        proof='—'
        if task['evidence']:
            path='data/leaderboard-evidence/'+rid+'.json'
            site.write(path,json.dumps(task['evidence'],ensure_ascii=False,indent=2)+'\n')
            proof=link(path,'评分与阶段证据','Scores & stage evidence','')
        search=e((rid+' '+copy['title_zh']+' '+copy['title_en']).lower())
        row=f'<tr data-lb-row data-case="{e(rid)}" data-family="{e(task["family"])}" data-status="{e(task["status"])}" data-search="{search}"><th scope="row">'
        row+=link(site.family_url(task['family'])+'#'+rid,rid,rid,'')+'<small>'+tr(copy['title_zh'],copy['title_en'])+'</small></th>'
        row+=td(task['family'])+td(status)+td(number(task['native_score']))+td(number(task['stage_score']))
        rows.append(row+td(proof+'<small>'+link(site.family_url(task['family'])+'#'+rid,'参考演示','Reference demo','')+'</small>')+'</tr>')
    detail='<div class="section-head"><div><p class="eyebrow">ALL 246 TASKS</p>'+tr('逐项成绩与证据','Task scores & evidence','h2')+'</div>'+link('data/leaderboard-tasks.csv','下载完整 CSV','Download full CSV','')+'</div>'
    detail+=tr('每项列出原生分数和阶段分；「—」表示尚无对应的有效成绩。参考演示来自既有专家记录，模型结果以评分证据为准。','Each task lists native and stage scores; “—” means a corresponding valid score is unavailable. Reference demonstrations are expert records; model results come from evaluation evidence.','p')+filters
    detail+='<p id="lb-count" role="status" aria-live="polite" data-zh="显示 246 / 246 项任务" data-en="Showing 246 / 246 tasks">显示 246 / 246 项任务</p>'
    detail+=table([('任务','Task'),('任务族','Family'),('Astra 结果','Astra result'),('原生 score','Native score'),('阶段分 / 100','Stage / 100'),('证据','Evidence')],rows,'逐项成绩 / Task scores')
    detail+='<p id="lb-empty" hidden>'+tr('没有匹配结果，请调整筛选条件。','No matching tasks. Try different filters.')+'</p>'

    methodology=[
        ('读取工作区后续 Astra 批次、历史修复重评及 astra_246_20261123 远端结果包。按唯一任务归并：优先独立评分确认的成功，否则采用有效评分；优先完整提交，再取较新记录。','Includes subsequent local Astra campaigns, historical repair evaluations and the astra_246_20261123 remote bundle. Deduplicate by task: prefer independently verified success, otherwise a valid evaluation; prefer complete submissions, then newer evidence.'),
        ('这是包含重试、不同提供者和 high／xhigh 设置的探索性汇总，不是固定预算、单次运行的正式模型排名。新修复尝试单独记录，不覆盖原运行或重置其历史预算。','This is an exploratory aggregate across retries, providers and high / xhigh settings, not a fixed-budget, single-pass model ranking. New repair attempts are recorded separately without overwriting original runs or resetting their historical budgets.'),
        ('有效评分要求独立物理评测、原生 verifier 未判 void、冻结提交未改变。无效评测和缺少提交保持待补；阶段分只采纳原生评分器已有的 0–100 分，不从成败标签推算。','A valid score requires independent physical evaluation, a non-void native verdict and an unchanged frozen submission. Invalid evaluations and missing submissions remain pending. Stage scores come from the native 0–100 grader and are not inferred from success labels.'),
        ('246 项参考演示与 Standard／Privileged 共 492 项沙箱就绪检查均已收录，不作为 Astra 成绩。公开证据摘要保留原始结果与原生评分文件的 SHA-256；完整源记录保留在工作区。','All 246 reference demonstrations and 492 Standard / Privileged readiness checks are retained separately from Astra scores. Public evidence digests retain SHA-256 hashes of the original result and native verdict; complete source records remain in the workspace.')]
    method='<div class="lb-method"><p class="eyebrow">SOURCES &amp; COUNTING</p>'+tr('统计口径与完整性','Counting policy & completeness','h2')+'<ul>'+''.join(tr(zh,en,'li') for zh,en in methodology)+'</ul><div class="hero-actions">'
    method+=link('data/leaderboard.json','下载完整评分 JSON','Download full results JSON','button')+link('data/video-gallery.json','参考记录清单','Reference manifest','')+'</div></div>'
    assets=f'<link rel="stylesheet" href="{site.asset("assets/leaderboard.css")}"><script defer src="{site.asset("assets/leaderboard.js")}"></script>'
    site.page('leaderboard.html','Astra 完整任务评分','Astra full task results','246 项 Astra 任务的原生评分、阶段分、完整覆盖与评测证据。',assets+hero+section(model)+section(family_section)+section(detail,'id="task-results"')+section(method,'id="methodology"'),active='leaderboard')
