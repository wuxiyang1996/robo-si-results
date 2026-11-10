/* Progressive enhancement: the complete task catalog remains visible without JS. */
(() => {
  'use strict';
  const search = document.getElementById('task-search');
  const category = document.getElementById('category-filter');
  const state = document.getElementById('state-filter');
  const count = document.getElementById('task-count');
  const empty = document.getElementById('task-empty');
  const reset = document.getElementById('reset-filters');
  const entries = Array.from(document.querySelectorAll('.task-grid .task-entry'));
  if (!search || !category || !state || !entries.length) return;

  const zh = (document.documentElement.lang || document.body.lang || '').toLowerCase().startsWith('zh');
  const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const indexed = entries.map(entry => ({
    element: entry,
    text: normalize((entry.dataset.search || '') + ' ' + entry.textContent),
    category: entry.dataset.category || '',
    state: entry.dataset.state || ''
  }));
  const isAll = value => !value || value === 'all' || value === '*';

  function applyFilters() {
    const terms = normalize(search.value).split(' ').filter(Boolean);
    let shown = 0;
    indexed.forEach(item => {
      const matches = (isAll(category.value) || item.category === category.value)
        && (isAll(state.value) || item.state === state.value)
        && terms.every(term => item.text.includes(term));
      item.element.hidden = !matches;
      if (matches) shown += 1;
    });
    if (count) count.textContent = zh ? `显示 ${shown} / ${entries.length} 个条目` : `Showing ${shown} of ${entries.length} entries`;
    if (empty) empty.hidden = shown !== 0;
  }

  function chooseAll(select) {
    const all = Array.from(select.options).find(option => isAll(option.value));
    if (all) select.value = all.value;
    else select.selectedIndex = 0;
  }

  function clearFilters() {
    search.value = '';
    chooseAll(category);
    chooseAll(state);
    applyFilters();
  }

  function revealHash(hash, scroll) {
    if (!hash || hash === '#') return;
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    const entry = target.closest('.task-entry');
    if (entry) clearFilters();
    // Legacy anchors may sit in collapsed contribution guidance as well.
    let node = target;
    while (node && node !== document.body) {
      if (node.tagName === 'DETAILS') node.open = true;
      node = node.parentElement;
    }
    if (scroll && (entry || target.closest('details'))) {
      requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'auto' }));
    }
  }

  search.addEventListener('input', applyFilters);
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      search.value = '';
      applyFilters();
    }
  });
  category.addEventListener('change', applyFilters);
  state.addEventListener('change', applyFilters);
  if (reset) reset.addEventListener('click', () => { clearFilters(); search.focus(); });

  // Optional quick category links use the same native select and AND filters.
  document.querySelectorAll('.category-links [data-filter-category]').forEach(link => {
    link.addEventListener('click', event => {
      const value = link.dataset.filterCategory;
      if (!Array.from(category.options).some(option => option.value === value)) return;
      event.preventDefault();
      category.value = value;
      applyFilters();
      document.getElementById('tasks')?.scrollIntoView({ block: 'start', behavior: 'auto' });
    });
  });

  window.addEventListener('hashchange', () => revealHash(window.location.hash, true));
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link) return;
    let destination;
    try { destination = new URL(link.href, window.location.href); } catch (_) { return; }
    if (destination.origin === window.location.origin && destination.pathname === window.location.pathname && destination.hash) {
      // The hashchange event does not fire when clicking the current fragment again.
      revealHash(destination.hash, destination.hash === window.location.hash);
    }
  });

  applyFilters();
  revealHash(window.location.hash, true);
})();
