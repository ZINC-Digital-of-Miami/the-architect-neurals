(() => {
  'use strict';
  const params = new URLSearchParams(location.search);
  const search = document.getElementById('topic-search');
  const rows = [...document.querySelectorAll('[data-topic-record]')];
  if (search) {
    const categoryButtons = [...document.querySelectorAll('[data-category]')];
    const statusButtons = [...document.querySelectorAll('[data-status-filter]')];
    let category = categoryButtons.some(b => b.dataset.category === params.get('category')) ? params.get('category') : 'all';
    let status = statusButtons.some(b => b.dataset.statusFilter === params.get('status')) ? params.get('status') : 'all';
    search.value = params.get('q') || '';
    function filter(replace = true) {
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      rows.forEach(row => {
        const matches = (!query || row.dataset.search.includes(query)) &&
          (category === 'all' || row.dataset.categories.split(' ').includes(category)) &&
          (status === 'all' || row.dataset.status === status);
        row.hidden = !matches;
        if (matches) visible++;
      });
      categoryButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.category === category)));
      statusButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.statusFilter === status)));
      document.getElementById('topic-results').textContent = `${visible} ${visible === 1 ? 'topic' : 'topics'}`;
      document.getElementById('topic-empty').hidden = visible !== 0;
      if (replace) {
        const url = new URL(location.href);
        [['q', query], ['category', category === 'all' ? '' : category], ['status', status === 'all' ? '' : status]].forEach(([key, value]) => value ? url.searchParams.set(key, value) : url.searchParams.delete(key));
        history.replaceState(null, '', url);
      }
    }
    search.addEventListener('input', () => filter());
    categoryButtons.forEach(b => b.addEventListener('click', () => { category = b.dataset.category; filter(); }));
    statusButtons.forEach(b => b.addEventListener('click', () => { status = b.dataset.statusFilter; filter(); }));
    filter(false);
  }
  const tabs = [...document.querySelectorAll('[data-view-tab]')];
  const views = [...document.querySelectorAll('[data-view]')];
  if (tabs.length) {
    tabs[0].parentElement.setAttribute('role', 'tablist');
    tabs.forEach(tab => {
      tab.id = `tab-${tab.dataset.viewTab}`;
      tab.setAttribute('role', 'tab');
      const panel = views.find(view => view.dataset.view === tab.dataset.viewTab);
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tab.id);
      panel.tabIndex = 0;
    });
    function select(id, updateUrl = false, focus = false) {
      if (!tabs.some(tab => tab.dataset.viewTab === id)) id = 'overview';
      tabs.forEach(tab => {
        const active = tab.dataset.viewTab === id;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
        if (active && focus) tab.focus();
      });
      views.forEach(view => { view.hidden = view.dataset.view !== id; });
      if (updateUrl) {
        const url = new URL(location.href);
        url.searchParams.set('view', id);
        url.hash = '';
        history.pushState(null, '', url);
      }
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(tab.dataset.viewTab, true));
      tab.addEventListener('keydown', event => {
        const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length :
          event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length :
          event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1;
        if (next >= 0) { event.preventDefault(); select(tabs[next].dataset.viewTab, true, true); }
      });
    });
    document.addEventListener('architecture:reveal-section', event => {
      const panel = event.target.closest?.('[data-view]');
      if (panel) select(panel.dataset.view, event.detail?.updateUrl === true);
    });
    function locationView() {
      let target = null;
      try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (_) { /* malformed external fragment */ }
      return target?.closest('[data-view]')?.dataset.view || new URLSearchParams(location.search).get('view');
    }
    addEventListener('popstate', () => select(locationView()));
    addEventListener('hashchange', () => select(locationView()));
    select(locationView());
  }
})();
