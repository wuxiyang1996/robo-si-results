"""Editorial research layout and progressively enhanced architecture diagrams."""
from html import escape


def render_research(p, interactive, tr, link, external, categories):
    sections = {s['id']: s for s in p['sections']}

    def paragraphs(zh, en, cls=''):
        zparts, eparts = zh.split('\n\n'), en.split('\n\n')
        assert len(zparts) == len(eparts), 'Research paragraphs must be bilingual'
        return ''.join(tr(z, e, 'p', f'class="{cls}"' if cls else '') for z, e in zip(zparts, eparts))

    def body(sid):
        s = sections[sid]
        return paragraphs(s['body_zh'], s['body_en'])

    def anchor(sid, zh, en, cls=''):
        return f'<a href="#{sid}" class="{cls}">'+tr(zh, en)+'</a>'

    def resources(sid):
        return '<div class="resource-links">'+''.join(external(a['url'], a['label_zh'], a['label_en']) for a in sections[sid].get('links', []))+'</div>'

    def heading(sid, number, zh=None, en=None):
        s = sections[sid]
        return '<p class="section-kicker">'+number+'</p>'+tr(zh or s['title_zh'], en or s['title_en'], 'h2')

    overview = ''
    for number, sid, zh, en, detail_zh, detail_en in [
        ('01', 'problem', '我们研究什么', 'The questions', '编程、物理试验与能力自建模', 'Programming, experiments, and self-modeling'),
        ('02', 'tracks', '怎样比较方法', 'The experiments', '回合内求解、冻结复用与轻训练', 'Solving, frozen reuse, and light training'),
        ('03', 'agent-interface', '沙盒如何运行', 'Inside the sandbox', '从传感器观测到独立评分', 'From sensor observations to independent scoring'),
    ]:
        overview += f'<a href="#{sid}"><span class="overview-number">{number}</span><span class="overview-copy">'+tr(zh, en, 'strong')+tr(detail_zh, detail_en, 'small')+'</span><span aria-hidden="true">↗</span></a>'
    result = '<section class="research-hero"><div class="wrap research-hero-grid"><div><p class="eyebrow">RESEARCH / EMBODIED TERMINAL-BENCH</p>'+tr(p['title_zh'], p['title_en'], 'h1')+tr(p['lead_zh'], p['lead_en'], 'p', 'class="lead"')+'</div><nav class="research-overview" aria-label="研究页概览 / Research overview">'+overview+'</nav></div></section>'

    toc_items = [('problem','研究问题','Questions'), ('task-design','任务设计','Task design'), ('tracks','评测路线','Evaluation tracks'), ('agent-interface','沙盒架构','Sandbox'), ('scoring-and-acceptance','评分与验收','Scoring'), ('budgets-and-evaluation','预算与对照','Budgets & controls'), ('reuse-and-evidence','方法复用','Reuse')]
    toc = '<aside class="research-toc" aria-label="页内目录 / On this page">'+tr('阅读导览','ON THIS PAGE','p')+''.join(anchor(sid,zh,en) for sid,zh,en in toc_items)+'</aside>'
    result += '<div class="wrap research-layout">'+toc+'<div class="research-body">'

    result += '<section class="research-section" id="problem">'+heading('problem','01 / QUESTIONS')+body('problem')+'<div class="research-question-grid">'
    question_summaries = [
        ('rq1', '写程序', 'Programming', '循环、分支和调试，能否让机器人更好地完成长任务并从失败中恢复？', 'Can loops, branches, and debugging help a robot complete long tasks and recover from failure?', '有效成功率 · 恢复能力 · 交互成本', 'Valid success · Recovery · Interaction cost'),
        ('rq2', '做试验', 'Experimentation', '机器人能否先提出预测，再用有目的的物理探测修正自己的判断？', 'Can a robot make predictions, then revise them through purposeful physical probes?', '预测校准 · 探测效率 · 最终结果', 'Calibration · Probe efficiency · Outcome'),
        ('rq3', '认识身体', 'Self-modeling', '当可达范围、夹爪或力量改变时，学到的能力边界能否帮助它换一种办法？', 'When reach, grip, or strength changes, can learned capability limits help it find another approach?', '跨身体迁移 · 路线选择 · 能力边界', 'Body transfer · Route choice · Capability limits'),
    ]
    for i,(sid,zh,en,sz,se,mz,me) in enumerate(question_summaries,1):
        result += f'<article class="research-question" id="{sid}"><p class="section-kicker">RQ{i}</p>'+tr(zh,en,'h3')+tr(sz,se,'p','class="question-method"')+tr(mz,me,'p','class="question-measures"')+'<details class="research-details"><summary>'+tr('实验如何比较','Experimental comparisons')+'</summary>'+body(sid)+'</details></article>'
    result += '</div></section>'

    result += '<section class="research-section" id="task-design">'+heading('task-design','02 / TASK DESIGN','同一个目标，不同身体，不同办法','One goal. Different bodies. Different approaches.')
    result += tr('每项任务给出目标、初始场景和公开约束。agent 自己发现工具的用途，选择行动，并用试验检查可行性。','Each task specifies the goal, initial scene, and public constraints. The agent discovers tool uses, chooses actions, and tests feasibility.','p','class="section-intro"')
    result += '<div class="research-category-links">'+''.join(link('tasks/categories/'+c['id']+'.html',c['title_zh'],c['title_en'],'') for c in categories)+'</div>'
    result += '<div class="research-design-grid">'
    for i,zh,en,z,e in [
        (1,'必要工具','Necessary tools','场景中只提供完成任务所需的工具。','The scene contains only the tools needed for the task.'),
        (2,'加入身体差异','Add body-dependent choices','加入另一种身体能用、当前身体用不了的工具。','Add tools that another body can use, but the current body cannot.'),
        (3,'再加入干扰物','Then add distractors','加入需要通过观察和试验辨别的干扰物。','Add distractors that observation and experiments can distinguish.'),
    ]:
        result += '<div class="design-step"><span class="design-number">0'+str(i)+'</span>'+tr(zh,en,'h3')+tr(z,e,'p')+'</div>'
    result += '</div>'+tr('三层使用同一种子逐步叠加，比较工具选择随身体和场景发生的变化。','The three layers build on the same seed, allowing comparisons of tool selection across bodies and scenes.','p','class="research-caption"')+'<details class="research-details"><summary>'+tr('任务条件与随机化','Task conditions and randomization')+'</summary>'+body('task-design')+'</details></section>'

    result += '<section class="research-section" id="tracks">'+heading('tracks','03 / EVALUATION TRACKS','三条路线，比较不同的学习方式','Three tracks, three ways to improve')+tr('选择一条路线，查看它允许改变什么，以及怎样进行公平比较。','Choose a track to see what can change and how the comparison is controlled.','p','class="section-intro"')
    result += '<div class="track-explorer" data-track-explorer><div class="track-tabs" data-track-tablist aria-label="评测路线 / Evaluation tracks">'
    for t in interactive['tracks']:
        tid=escape(t['id'],quote=True)
        result += f'<button type="button" class="track-tab" id="track-tab-{tid}" data-track-tab="{tid}" aria-controls="track-panel-{tid}"><span class="track-letter">{tid}</span>'+tr(t['label_zh'],t['label_en'],'strong')+tr(t['summary_zh'],t['summary_en'],'span','class="track-summary"')+'</button>'
    result += '</div>'
    for t in interactive['tracks']:
        tid=escape(t['id'],quote=True)
        result += f'<section class="track-panel" id="track-panel-{tid}" data-track-panel="{tid}" aria-labelledby="track-tab-{tid}"><div class="track-field-grid">'
        for f in t['fields']:
            result += '<div class="track-field">'+tr(f['label_zh'],f['label_en'],'small')+tr(f['text_zh'],f['text_en'],'p')+'</div>'
        result += '</div><div class="track-detail">'+''.join(tr(z,e,'p') for z,e in zip(t['paragraphs_zh'],t['paragraphs_en']))+'</div></section>'
    result += '</div></section>'

    result += '<section class="research-section" id="agent-interface">'+heading('agent-interface','04 / INSIDE THE SANDBOX','一次回合，在沙盒里怎样运行？','What happens inside one episode?')+tr('点击流程中的部件，查看它的职责、输入和输出；也可以沿着下面的步骤走一遍。','Select a component to explore its role, inputs, and outputs, or follow the steps below.','p','class="section-intro"')
    components={c['id']:c for c in interactive['components']}
    def part(cid):
        c=components[cid];i=list(components).index(cid)+1
        return f'<button type="button" class="sandbox-part" id="sandbox-part-{cid}" data-sandbox-part="{cid}" aria-controls="sandbox-panel-{cid}"><span class="part-number">0{i}</span>'+tr(c['label_zh'],c['label_en'],'strong')+tr(c['summary_zh'],c['summary_en'],'small')+'</button>'
    result += '<div class="sandbox-explorer" data-sandbox-explorer><div class="sandbox-layout"><div class="sandbox-map" id="sandbox-map" aria-label="沙盒运行流程 / Sandbox flow">'
    result += '<div class="sandbox-lane task-lane">'+part('task')+'</div>'
    result += '<p class="flow-label">↓ '+tr('公开目标、身体规格与预算','Public goal, body specifications, and budget')+'</p>'
    result += '<div class="sandbox-lane agent-lane">'+tr('AGENT 工作区','AGENT WORKSPACE','p','class="lane-label"')+part('agent')+'</div>'
    result += '<p class="flow-label">↓ '+tr('动作指令','Action commands')+' <span aria-hidden="true">·</span> ↑ '+tr('传感器反馈','Sensor feedback')+'</p>'
    result += '<div class="sandbox-lane world-lane">'+tr('可信环境 · 观测与行动循环','TRUSTED ENVIRONMENT · OBSERVE & ACT','p','class="lane-label"')+'<div class="sandbox-cycle">'+part('executor')+part('physics')+part('sensors')+'</div><p class="flow-label">'+tr('执行指令 → 推进物理 → 生成观测 → 返回 agent','Execute → advance physics → observe → return to agent')+'</p></div>'
    result += '<p class="flow-label">↓ '+tr('每一步留下物理证据','Capture physical evidence at every step')+'</p>'
    result += '<div class="sandbox-lane evidence-lane">'+tr('环境侧 · 全程记录 → 回合后评分','ENVIRONMENT SIDE · RECORD THROUGHOUT → SCORE AFTER THE EPISODE','p','class="lane-label"')+'<div class="sandbox-evidence">'+part('record')+part('scorer')+'</div></div></div><div class="sandbox-detail">'
    for c in interactive['components']:
        cid=c['id']
        result += f'<section id="sandbox-panel-{cid}" data-sandbox-panel="{cid}" aria-labelledby="sandbox-part-{cid}">'+anchor('sandbox-map','↑ 返回流程，选择其他部件','↑ Back to the diagram','sandbox-back')+tr('部件 '+str(list(components).index(cid)+1)+' / 7','COMPONENT '+str(list(components).index(cid)+1)+' / 7','p','class="section-kicker"')+tr(c['label_zh'],c['label_en'],'h3')+tr(c['role_zh'],c['role_en'],'p')+'<div class="sandbox-io"><div>'+tr('接收什么','INPUT','h4')+tr(c['input_zh'],c['input_en'],'p')+'</div><div>'+tr('交出什么','OUTPUT','h4')+tr(c['output_zh'],c['output_en'],'p')+'</div></div><div class="sandbox-boundary">'+tr('怎样分工','RESPONSIBILITY','h4')+tr(c['boundary_zh'],c['boundary_en'],'p')+'</div><div class="sandbox-example">'+tr('以斜坡取物为例','EXAMPLE · RETRIEVAL WITH A RAMP','h4')+tr(c['example_zh'],c['example_en'],'p')+'</div></section>'
    result += '</div></div><div class="sandbox-walkthrough"><div class="sandbox-walkthrough-heading">'+tr('沿着一次回合走一遍','Walk through an episode','h3')+tr('以斜坡取物说明数据如何流动。','Follow the data through a ramp-retrieval example.','p')+'</div><ol data-sandbox-walkthrough>'
    for i,s in enumerate(interactive['steps']):
        result += f'<li><button type="button" data-sandbox-step="{i}" data-component="{s["component"]}"><span aria-hidden="true">{i+1:02}</span>'+tr(s['title_zh'],s['title_en'])+'</button>'+tr(s['text_zh'],s['text_en'],'p','class="walkthrough-copy"')+'</li>'
    result += '</ol><div class="sandbox-step-controls"><button type="button" data-sandbox-prev>'+tr('← 上一步','← Previous')+'</button><span data-sandbox-step-count aria-live="polite">1 / 7</span><button type="button" data-sandbox-next>'+tr('下一步 →','Next →')+'</button></div></div></div>'
    result += '<details class="research-details"><summary>'+tr('接口与观测约定','Interfaces and observation rules')+'</summary>'+body('agent-interface')+'</details>'+resources('agent-interface')+'</section>'

    result += '<div class="research-two-column">'
    for sid,number,zh,en in [('scoring-and-acceptance','05 / SCORING','用物理记录判断进度','Score progress from physical records'),('budgets-and-evaluation','06 / EXPERIMENTS','把预算和对照放在一起','Make budgets and controls explicit')]:
        result += f'<section class="research-section" id="{sid}">'+heading(sid,number,zh,en)+body(sid)+'</section>'
    result += '</div><section class="research-section research-closing" id="reuse-and-evidence">'+heading('reuse-and-evidence','07 / REUSE')+body('reuse-and-evidence')+resources('reuse-and-evidence')+'</section></div></div>'
    return result
