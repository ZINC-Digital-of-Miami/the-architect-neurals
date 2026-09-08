/* Shared reading controls. Reading places stay in this browser; no network or analytics. */
(() => {
  'use strict';
  document.documentElement.classList.add('ui-ready');
  const menuButton = document.querySelector('[data-ui-menu]');
  const navigation = document.getElementById('site-navigation');
  const dropdowns = [...document.querySelectorAll('[data-ui-dropdown]')];
  const dialog = document.getElementById('contents-dialog');
  const contentsButton = document.querySelector('[data-ui-contents]');
  const main = document.getElementById('main-content');
  const status = document.querySelector('[data-ui-status]');
  const saveButton = document.querySelector('[data-ui-save]');
  const resumeButton = document.querySelector('[data-ui-resume]');
  const progress = document.getElementById('reading-progress');
  const topProgress = document.getElementById('progress');
  const currentLabel = document.getElementById('whereami');
  const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  let statusTimer;
  let frame = 0;
  let positions = [];
  let current = null;
  let measurementFrame = 0;
  const storageKey = `architecture:reading:${location.pathname}`;

  function announce(message) {
    if (!status) return;
    clearTimeout(statusTimer);
    status.textContent = message;
    statusTimer = setTimeout(() => { status.textContent = ''; }, 6000);
  }

  function closeDropdowns(except) {
    dropdowns.forEach(button => {
      if (button === except) return;
      button.setAttribute('aria-expanded', 'false');
      button.closest('.navgroup').classList.remove('open');
      document.getElementById(button.getAttribute('aria-controls')).hidden = true;
    });
  }

  function setMenu(open) {
    if (!menuButton || !navigation) return;
    menuButton.setAttribute('aria-expanded', String(open));
    navigation.classList.toggle('is-open', open);
    if (!open) closeDropdowns();
  }

  menuButton?.addEventListener('click', () => {
    setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
  });
  dropdowns.forEach(button => button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    closeDropdowns(button);
    button.setAttribute('aria-expanded', String(open));
    button.closest('.navgroup').classList.toggle('open', open);
    document.getElementById(button.getAttribute('aria-controls')).hidden = !open;
  }));
  document.addEventListener('click', event => {
    if (!event.target.closest('.topnav')) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || dialog?.open) return;
    const openDropdown = dropdowns.find(button => button.getAttribute('aria-expanded') === 'true');
    if (openDropdown) {
      closeDropdowns();
      openDropdown.focus();
    } else if (menuButton?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menuButton.focus();
    }
  });
  navigation?.addEventListener('focusout', event => {
    if (event.relatedTarget && !navigation.contains(event.relatedTarget)
        && event.relatedTarget !== menuButton) setMenu(false);
  });
  matchMedia('(min-width: 1101px)').addEventListener('change', () => setMenu(false));

  contentsButton?.addEventListener('click', () => {
    setMenu(false);
    if (!dialog.open) dialog.showModal();
  });
  document.querySelector('[data-ui-close-contents]')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right
        || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog?.addEventListener('close', () => contentsButton?.focus({preventScroll: true}));

  function targetFromHash(hash) {
    try { return document.getElementById(decodeURIComponent(hash.replace(/^#/, ''))); }
    catch { return null; }
  }
  function reveal(target, updateUrl = false) {
    target?.dispatchEvent(new CustomEvent('architecture:reveal-section', {bubbles: true, detail: {updateUrl}}));
    for (let parent = target?.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') parent.open = true;
    }
  }
  function scrollToTarget(target, behavior = 'auto') {
    if (target.id === 'top') scrollTo({top: 0, behavior});
    else target.scrollIntoView({behavior, block: 'start'});
  }
  function focusTarget(target) {
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({preventScroll: true});
  }
  document.addEventListener('click', event => {
    const anchor = event.target.closest('a[href]');
    if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey
        || event.ctrlKey || event.shiftKey || event.altKey || anchor.target === '_blank') return;
    const url = new URL(anchor.href, location.href);
    if (anchor.closest('.topnav')) setMenu(false);
    if (url.origin !== location.origin || url.pathname !== location.pathname || !url.hash) return;
    const target = targetFromHash(url.hash);
    if (!target) return;
    event.preventDefault();
    reveal(target);
    if (dialog?.open) dialog.close();
    history.pushState(null, '', url.hash);
    requestAnimationFrame(() => {
      focusTarget(target);
      scrollToTarget(target, reducedMotion() ? 'auto' : 'smooth');
      measure();
    });
  });
  addEventListener('hashchange', () => {
    const target = targetFromHash(location.hash);
    if (target) { reveal(target); requestAnimationFrame(() => scrollToTarget(target)); }
  });

  function sectionTitle(element) {
    const heading = element.matches('h1,h2,h3,h4') ? element : element.querySelector('h1,h2,h3,h4,.kicker,.deck-label');
    return (heading?.textContent || element.id.replaceAll('-', ' ')).trim();
  }
  function measure() {
    if (!main) return;
    const candidates = main.querySelectorAll('h1[id],h2[id],h3[id],h4[id],section[id],header.cover[id]');
    positions = [...candidates].filter(element => element.getClientRects().length).map(element => ({
      element, top: element.getBoundingClientRect().top + scrollY, title: sectionTitle(element)
    })).sort((a, b) => a.top - b.top);
    update();
  }
  function scheduleMeasure() {
    if (measurementFrame) return;
    measurementFrame = requestAnimationFrame(() => { measurementFrame = 0; measure(); });
  }
  function update() {
    const total = Math.max(0, document.documentElement.scrollHeight - innerHeight);
    const percent = total ? Math.min(100, Math.max(0, scrollY / total * 100)) : 100;
    if (progress) progress.value = percent;
    if (topProgress) topProgress.style.width = `${percent}%`;
    const readingLine = scrollY + Math.min(180, innerHeight * .25);
    let selected = positions[0] || null;
    for (const position of positions) {
      if (position.top > readingLine) break;
      selected = position;
    }
    if (!selected || current?.element === selected.element) return;
    current = selected;
    if (currentLabel) currentLabel.textContent = selected.title;
    document.querySelectorAll('.sidebar-links a[href]').forEach(anchor => {
      const url = new URL(anchor.href, location.href);
      const active = url.pathname === location.pathname && url.hash === `#${selected.element.id}`;
      anchor.classList.toggle('on', active);
      if (active) {
        anchor.setAttribute('aria-current', 'location');
        const part = anchor.closest('details');
        if (part) part.open = true;
      } else anchor.removeAttribute('aria-current');
    });
  }
  addEventListener('scroll', () => {
    if (frame) return;
    frame = requestAnimationFrame(() => { frame = 0; update(); });
  }, {passive: true});
  addEventListener('resize', scheduleMeasure, {passive: true});
  main?.addEventListener('toggle', scheduleMeasure, true);
  if (main && 'ResizeObserver' in window) new ResizeObserver(scheduleMeasure).observe(main);
  document.fonts?.ready.then(scheduleMeasure);

  function savedPlace() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      return saved?.version === 1 && typeof saved.id === 'string' && Number.isFinite(saved.offset) ? saved : null;
    } catch { return null; }
  }
  saveButton?.addEventListener('click', () => {
    const element = current?.element || main;
    if (!element) return;
    const offset = scrollY - (element.getBoundingClientRect().top + scrollY);
    try {
      localStorage.setItem(storageKey, JSON.stringify({version: 1, id: element.id, offset}));
      if (resumeButton) resumeButton.hidden = false;
      announce('Reading place saved on this device.');
    } catch { announce('This browser could not save your reading place.'); }
  });
  resumeButton?.addEventListener('click', () => {
    const saved = savedPlace();
    const target = saved && document.getElementById(saved.id);
    if (!target) { announce('The saved section is no longer available on this page.'); return; }
    reveal(target, true);
    requestAnimationFrame(() => {
      focusTarget(target);
      const top = Math.max(0, target.getBoundingClientRect().top + scrollY + saved.offset);
      scrollTo({top, behavior: reducedMotion() ? 'auto' : 'smooth'});
      announce('Returned to your saved reading place.');
    });
  });
  if (resumeButton) resumeButton.hidden = !savedPlace();
  if (location.hash) {
    const target = targetFromHash(location.hash);
    if (target) { reveal(target); requestAnimationFrame(() => scrollToTarget(target)); }
  }
  measure();
})();
