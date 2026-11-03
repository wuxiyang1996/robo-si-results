(function () {
  var root = document.documentElement;
  function setLang(l) {
    root.setAttribute('data-lang', l);
    root.setAttribute('lang', l === 'zh' ? 'zh-CN' : 'en');
    try { localStorage.setItem('robo-si-lang', l); } catch (e) {}
    document.querySelectorAll('option[data-' + l + ']').forEach(function (o) { o.textContent = o.getAttribute('data-' + l); });
  }
  var saved = null;
  document.addEventListener('DOMContentLoaded', function () { setLang(root.getAttribute('data-lang')); });
  try { saved = localStorage.getItem('robo-si-lang'); } catch (e) {}
  setLang(saved || ((navigator.language || '').toLowerCase().indexOf('zh') === 0 ? 'zh' : 'en'));
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-set-lang]');
    if (b) setLang(b.getAttribute('data-set-lang'));
  });

  // Play muted videos while they are on screen.
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var v = en.target;
        if (en.isIntersecting && en.intersectionRatio > 0.55) { v.play().catch(function () {}); }
        else if (!v.paused) { v.pause(); }
      });
    }, { threshold: [0, 0.55, 1] });
    document.querySelectorAll('video[data-auto]').forEach(function (v) { io.observe(v); });
  }

  // Case table filters on the overview page.
  var table = document.getElementById('cases');
  if (table) {
    var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
    var fFam = document.getElementById('f-fam'), fEmb = document.getElementById('f-emb'),
        fExit = document.getElementById('f-exit'), fq = document.getElementById('f-q'),
        count = document.getElementById('f-count');
    var apply = function () {
      var fam = fFam.value, emb = fEmb.value, ex = fExit.value, q = fq.value.trim().toLowerCase(), n = 0;
      rows.forEach(function (r) {
        var ok = (!fam || r.dataset.fam === fam) && (!emb || r.dataset.emb.split('|').indexOf(emb) >= 0) &&
                 (!ex || r.dataset.exit === ex) && (!q || r.textContent.toLowerCase().indexOf(q) >= 0);
        r.style.display = ok ? '' : 'none';
        if (ok) n++;
      });
      count.textContent = n + ' / ' + rows.length;
    };
    [fFam, fEmb, fExit].forEach(function (s) { s.addEventListener('change', apply); });
    fq.addEventListener('input', apply);
    apply();
  }
})();
