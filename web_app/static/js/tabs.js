(function () {
  const $$ = (s) => [...document.querySelectorAll(s)];
  const pages = $$('.page'), tabs = $$('[data-tab]');
  const title = document.getElementById('pageTitle'), current = document.getElementById('menuCurrent');
  const toggle = document.getElementById('menuToggle'), wrap = document.getElementById('menuWrap');

  function setMenu(open) {
    wrap.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
  }
  toggle.addEventListener('click', () => setMenu(!wrap.classList.contains('open')));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
  document.addEventListener('click', (e) => {            // клік поза меню — згортає
    if (wrap.classList.contains('open') && !e.target.closest('.sidebar')) setMenu(false);
  });

  function showPage(name) {
    if (!pages.some((p) => p.dataset.page === name)) name = 'queues';
    pages.forEach((p) => (p.hidden = p.dataset.page !== name));
    tabs.forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle('on', on);
      if (on) {
        const label = t.querySelector('.tx').textContent;
        title.textContent = label; current.textContent = label;
      }
    });
    history.replaceState(null, '', '#' + name);
    window.scrollTo({ top: 0 });
  }
  tabs.forEach((t) => t.addEventListener('click', () => { showPage(t.dataset.tab); setMenu(false); }));

  let pcaReloaded = false;
  function showSub(name) {
    $$('.sub').forEach((s) => (s.hidden = s.dataset.sub !== name));
    $$('[data-subtab]').forEach((b) => b.classList.toggle('on', b.dataset.subtab === name));
    const frame = document.getElementById('pcaFrame');
    if (name === 'pca' && !pcaReloaded && frame && frame.src) { pcaReloaded = true; frame.src = frame.src; }
  }
  $$('[data-subtab]').forEach((b) => b.addEventListener('click', () => showSub(b.dataset.subtab)));

  showSub('metrics');
  showPage(location.hash.slice(1) || 'queues');
  window.addEventListener('hashchange', () => showPage(location.hash.slice(1)));
})();