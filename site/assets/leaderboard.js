/* All task rows are server rendered; filtering progressively enhances the table. */
(() => {
  'use strict';
  const rows = [...document.querySelectorAll('[data-lb-row]')];
  if (!rows.length) return;
  const search = document.getElementById('lb-search');
  const family = document.getElementById('lb-family');
  const status = document.getElementById('lb-status');
  const count = document.getElementById('lb-count');
  function restore() {
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    for (const [key, control] of [['family', family], ['status', status]]) {
      const value = params.get(key) || '';
      control.value = [...control.options].some(o => o.value === value) ? value : '';
    }
  }
  function filter(write = false) {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach(row => {
      row.hidden = (family.value && row.dataset.family !== family.value) ||
        (status.value && row.dataset.status !== status.value) ||
        (query && !row.dataset.search.includes(query));
      if (!row.hidden) visible++;
    });
    count.dataset.zh = `显示 ${visible} / ${rows.length} 项任务`;
    count.dataset.en = `Showing ${visible} / ${rows.length} tasks`;
    count.textContent = document.documentElement.lang === 'en' ? count.dataset.en : count.dataset.zh;
    document.getElementById('lb-empty').hidden = visible > 0;
    if (write) {
      const url = new URL(location.href);
      for (const [key, value] of [['q', search.value], ['family', family.value], ['status', status.value]]) {
        value ? url.searchParams.set(key, value) : url.searchParams.delete(key);
      }
      history.replaceState(null, '', url);
    }
  }
  search.addEventListener('input', () => filter(true));
  family.addEventListener('change', () => filter(true));
  status.addEventListener('change', () => filter(true));
  document.getElementById('lb-clear').addEventListener('click', () => {
    search.value = ''; family.value = ''; status.value = ''; filter(true);
  });
  window.addEventListener('popstate', () => { restore(); filter(); });
  restore(); filter();
})();
