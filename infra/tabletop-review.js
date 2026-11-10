if (document.documentElement.lang.startsWith("en")) {
(() => {
  const dataNode = document.getElementById('task-data');
  if (!dataNode) return;
  const task = JSON.parse(dataNode.textContent);
  const key = `robo-si-review-${task.id}-${task.version}`;
  let notes = {};
  try { notes = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) {}
  const grid = document.getElementById('video-grid');
  const e = (tag, text, cls) => { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; };
  const link = (url, text) => { const a = e('a', text); a.href = url; return a; };
  const cards = task.runs.map(run => {
    const card = e('figure', null, 'vcard');
    const video = e('video'); video.controls = true; video.preload = 'none'; video.src = run.video;
    video.setAttribute('aria-label', `${task.title} ${run.id} complete recorded-state video`);
    const caption = e('figcaption');
    const row = e('div', null, 'vrow'); row.append(e('b', run.id), e('span', 'Automatic pass', 'pill ok'));
    caption.append(row, e('p', `${Number(run.duration).toFixed(3)} s · 5 Hz recorded-state visualization`, 'muted'));
    const links = e('p'); links.append(link(run.report, 'Physical record'), document.createTextNode(' · '), link(run.scene, 'Scene input'), document.createTextNode(' · '), link(run.video, 'Original video')); caption.append(links);
    const timeline = e('details'); timeline.append(e('summary', 'After observation: automatic stage timeline'));
    const times = e('ul'); Object.entries(run.stages).forEach(([stage, seconds]) => times.append(e('li', `${stage}: ${seconds} s`))); timeline.append(times); caption.append(timeline);
    const command = e('details'); command.append(e('summary', 'Reproduction command'), e('pre', run.command.map(x => /\s/.test(x) || x.startsWith('<') ? `"${x}"` : x).join(' '))); caption.append(command);
    const review = e('details'); review.append(e('summary', 'My human observations (exportable)'));
    const label = e('label', 'Stage times, anomalies and review conclusions');
    const text = e('textarea'); text.setAttribute('aria-label', `${run.id} human review notes`); text.value = notes[run.id]?.text || ''; text.placeholder = 'Record independent observations; automatic results are not signed human acceptance.';
    text.addEventListener('input', () => { notes[run.id] = { text: text.value, updated_at: new Date().toISOString() }; try { localStorage.setItem(key, JSON.stringify(notes)); document.getElementById('notes-status').textContent = 'Notes saved in this browser. Download JSON for a backup.'; } catch (_) { document.getElementById('notes-status').textContent = 'Browser storage unavailable. Download JSON to preserve notes.'; } });
    label.append(text); review.append(label); caption.append(review); card.append(video, caption); grid.append(card); return { card, run, video };
  });
  function filter() {
    const level = document.getElementById('level-filter').value;
    const query = document.getElementById('case-search').value.trim().toLowerCase(); let count = 0;
    cards.forEach(({ card, run, video }) => { const visible = (level === 'all' || String(run.level) === level) && run.id.toLowerCase().includes(query); card.hidden = !visible; if (visible) count++; else video.pause(); });
    document.getElementById('visible-count').textContent = `Showing ${count} / ${cards.length} scenarios`;
  }
  document.getElementById('level-filter').addEventListener('change', filter);
  document.getElementById('case-search').addEventListener('input', filter);
  filter();
  document.getElementById('export-notes').addEventListener('click', () => {
    const report = { schema: 'tabletop-reviewer-notes/1', task: task.id, version: task.version, source_digest: task.source_digest, exported_at: new Date().toISOString(), notes, admission_approved: false, note: 'Reviewer notes only; signed acceptance and independent reproduction remain separate.' };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const a = link(url, ''); a.download = `${task.id}-review-notes.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    document.getElementById('notes-status').textContent = 'Notes download created; admission status is unchanged.';
  });
})();

} else {
(() => {
  const dataNode = document.getElementById('task-data');
  if (!dataNode) return;
  const task = JSON.parse(dataNode.textContent);
  const key = `robo-si-review-${task.id}-${task.version}`;
  let notes = {};
  try { notes = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) {}
  const grid = document.getElementById('video-grid');
  const e = (tag, text, cls) => { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; };
  const link = (url, text) => { const a = e('a', text); a.href = url; return a; };
  const cards = task.runs.map(run => {
    const card = e('figure', null, 'vcard');
    const video = e('video'); video.controls = true; video.preload = 'none'; video.src = run.video;
    video.setAttribute('aria-label', `${task.title} ${run.id} 完整记录状态录像`);
    const caption = e('figcaption');
    const row = e('div', null, 'vrow'); row.append(e('b', run.id), e('span', '自动通过', 'pill ok'));
    caption.append(row, e('p', `${Number(run.duration).toFixed(3)} 秒 · 5 Hz 记录状态可视化`, 'muted'));
    const links = e('p'); links.append(link(run.report, '物理记录'), document.createTextNode(' · '), link(run.scene, '场景输入'), document.createTextNode(' · '), link(run.video, '原视频')); caption.append(links);
    const timeline = e('details'); timeline.append(e('summary', '观察后展开：自动阶段时间线'));
    const times = e('ul'); Object.entries(run.stages).forEach(([stage, seconds]) => times.append(e('li', `${stage}: ${seconds} s`))); timeline.append(times); caption.append(timeline);
    const command = e('details'); command.append(e('summary', '复现命令'), e('pre', run.command.map(x => /\s/.test(x) || x.startsWith('<') ? `"${x}"` : x).join(' '))); caption.append(command);
    const review = e('details'); review.append(e('summary', '记录我的人工观察（可下载）'));
    const label = e('label', '阶段时刻、异常观察及复核结论');
    const text = e('textarea'); text.setAttribute('aria-label', `${run.id} 人工观察笔记`); text.value = notes[run.id]?.text || ''; text.placeholder = '独立记录观察，勿把自动结果直接当成人工签审。';
    text.addEventListener('input', () => { notes[run.id] = { text: text.value, updated_at: new Date().toISOString() }; try { localStorage.setItem(key, JSON.stringify(notes)); document.getElementById('notes-status').textContent = '笔记已保存在本浏览器；请下载 JSON 备份。'; } catch (_) { document.getElementById('notes-status').textContent = '浏览器存储不可用；请立即下载 JSON 保存笔记。'; } });
    label.append(text); review.append(label); caption.append(review); card.append(video, caption); grid.append(card); return { card, run, video };
  });
  function filter() {
    const level = document.getElementById('level-filter').value;
    const query = document.getElementById('case-search').value.trim().toLowerCase(); let count = 0;
    cards.forEach(({ card, run, video }) => { const visible = (level === 'all' || String(run.level) === level) && run.id.toLowerCase().includes(query); card.hidden = !visible; if (visible) count++; else video.pause(); });
    document.getElementById('visible-count').textContent = `显示 ${count} / ${cards.length} 个场景`;
  }
  document.getElementById('level-filter').addEventListener('change', filter);
  document.getElementById('case-search').addEventListener('input', filter);
  filter();
  document.getElementById('export-notes').addEventListener('click', () => {
    const report = { schema: 'tabletop-reviewer-notes/1', task: task.id, version: task.version, source_digest: task.source_digest, exported_at: new Date().toISOString(), notes, admission_approved: false, note: 'Reviewer notes only; signed acceptance and independent reproduction remain separate.' };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const a = link(url, ''); a.download = `${task.id}-review-notes.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    document.getElementById('notes-status').textContent = '已生成笔记下载；任务准入状态未改变。';
  });
})();

}
