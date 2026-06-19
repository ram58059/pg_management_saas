(function () {
  'use strict';

  const MESSAGES = [
    'Preparing your stay...',
    'Getting your room details ready...',
    'Loading your living space...',
    'Setting things up for you...',
    'Fetching the latest information...',
    'Making your experience seamless...',
    'Almost there...',
  ];

  const NAV_KEY = 'stayi-nav';
  const SHOW_DELAY_MS = 200;

  const state = {
    pageVisible: false,
    ajaxCount: 0,
    showTimer: null,
    progressTimer: null,
    messageTimer: null,
    messageIndex: 0,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function setMessage(text) {
    const el = $('stayi-loader-message');
    if (!el) return;
    if (text) {
      el.textContent = text;
      return;
    }
    el.classList.add('is-changing');
    window.setTimeout(() => {
      el.textContent = MESSAGES[state.messageIndex % MESSAGES.length];
      state.messageIndex += 1;
      el.classList.remove('is-changing');
    }, 150);
  }

  function startMessageRotation() {
    stopMessageRotation();
    setMessage(MESSAGES[0]);
    state.messageIndex = 1;
    state.messageTimer = window.setInterval(() => setMessage(), 2500);
  }

  function stopMessageRotation() {
    if (state.messageTimer) {
      window.clearInterval(state.messageTimer);
      state.messageTimer = null;
    }
  }

  function showOverlay(message) {
    const overlay = $('stayi-loader-overlay');
    if (!overlay || state.pageVisible) return;
    state.pageVisible = true;
    overlay.classList.add('is-visible');
    overlay.setAttribute('aria-hidden', 'false');
    document.documentElement.setAttribute('aria-busy', 'true');
    if (message) {
      const el = $('stayi-loader-message');
      if (el) el.textContent = message;
      stopMessageRotation();
    } else {
      startMessageRotation();
    }
  }

  function hideOverlay() {
    const overlay = $('stayi-loader-overlay');
    if (!overlay || !state.pageVisible) return;
    state.pageVisible = false;
    overlay.classList.remove('is-visible');
    overlay.setAttribute('aria-hidden', 'true');
    document.documentElement.removeAttribute('aria-busy');
    stopMessageRotation();
  }

  function showProgress() {
    const bar = $('stayi-loader-progress');
    if (!bar || bar.classList.contains('is-visible')) return;
    bar.classList.add('is-visible');
    bar.setAttribute('aria-hidden', 'false');
  }

  function hideProgress() {
    const bar = $('stayi-loader-progress');
    if (!bar) return;
    bar.classList.remove('is-visible');
    bar.setAttribute('aria-hidden', 'true');
  }

  function clearShowTimer() {
    if (state.showTimer) {
      window.clearTimeout(state.showTimer);
      state.showTimer = null;
    }
  }

  function clearProgressTimer() {
    if (state.progressTimer) {
      window.clearTimeout(state.progressTimer);
      state.progressTimer = null;
    }
  }

  const StayiLoader = {
    show(options = {}) {
      const mode = options.mode || 'page';
      const message = options.message || null;
      const immediate = options.immediate === true;

      if (mode === 'ajax') {
        state.ajaxCount += 1;
        clearProgressTimer();
        state.progressTimer = window.setTimeout(() => {
          if (state.ajaxCount > 0) showProgress();
        }, SHOW_DELAY_MS);
        return;
      }

      clearShowTimer();
      if (immediate) {
        showOverlay(message);
        return;
      }
      state.showTimer = window.setTimeout(() => showOverlay(message), SHOW_DELAY_MS);
    },

    hide(options = {}) {
      const mode = options.mode || 'page';

      if (mode === 'ajax') {
        state.ajaxCount = Math.max(0, state.ajaxCount - 1);
        if (state.ajaxCount === 0) {
          clearProgressTimer();
          hideProgress();
        }
        return;
      }

      clearShowTimer();
      hideOverlay();
    },

    setMessage(message) {
      setMessage(message);
      stopMessageRotation();
    },

    skeletonLines(count = 3) {
      return Array.from({ length: count }, (_, index) => {
        const width = index === 0 ? '55%' : index === count - 1 ? '40%' : '75%';
        return `<div class="stayi-skeleton stayi-skeleton-line" style="width:${width}"></div>`;
      }).join('');
    },

    skeletonTableRows(columns, rows = 4) {
      return Array.from({ length: rows }, () =>
        `<tr>${Array.from({ length: columns }, () =>
          '<td class="p-4"><div class="stayi-skeleton stayi-skeleton-line"></div></td>'
        ).join('')}</tr>`
      ).join('');
    },

    skeletonCards(count = 4) {
      return Array.from({ length: count }, () =>
        `<div class="stayi-skeleton-card"><div class="stayi-skeleton stayi-skeleton-line-sm"></div><div class="stayi-skeleton stayi-skeleton-line-lg"></div><div class="stayi-skeleton stayi-skeleton-line" style="width:65%"></div></div>`
      ).join('');
    },

    wrapFetch() {
      if (window.__stayiFetchWrapped) return;
      window.__stayiFetchWrapped = true;
      const originalFetch = window.fetch.bind(window);

      window.fetch = function stayiFetch(input, init = {}) {
        const headers = new Headers(init.headers || {});
        const silent =
          init.stayiLoader === false ||
          headers.get('X-Stayi-Silent') === '1';

        if (silent) {
          return originalFetch(input, init);
        }

        const useFullOverlay = init.stayiLoader === 'full';
        StayiLoader.show({ mode: useFullOverlay ? 'page' : 'ajax' });

        return originalFetch(input, init)
          .then((response) => {
            StayiLoader.hide({ mode: useFullOverlay ? 'page' : 'ajax' });
            return response;
          })
          .catch((error) => {
            StayiLoader.hide({ mode: useFullOverlay ? 'page' : 'ajax' });
            throw error;
          });
      };
    },

    bindForms() {
      document.querySelectorAll('form').forEach((form) => {
        if (form.dataset.stayiNoLoader === 'true') return;
        if (form.dataset.stayiBound === 'true') return;
        form.dataset.stayiBound = 'true';

        form.addEventListener('submit', function onSubmit(event) {
          if (form.dataset.stayiSubmitting === 'true') {
            event.preventDefault();
            return;
          }

          if (form.dataset.stayiAjax === 'true') return;

          form.dataset.stayiSubmitting = 'true';
          const submitBtn =
            form.querySelector('[type="submit"]') ||
            form.querySelector('button:not([type="button"])');
          const loadingText =
            form.dataset.stayiLoading ||
            (submitBtn && submitBtn.dataset.stayiLoading) ||
            'Processing...';

          if (submitBtn) {
            if (!submitBtn.dataset.stayiOriginalText) {
              submitBtn.dataset.stayiOriginalText = submitBtn.innerHTML;
            }
            submitBtn.disabled = true;
            submitBtn.setAttribute('aria-busy', 'true');
            submitBtn.innerHTML = loadingText;
          }

          StayiLoader.show({
            mode: 'page',
            message: loadingText.replace(/\.\.\.$/, '...'),
          });
        });
      });
    },

    bindNavigation() {
      document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link) return;
        if (link.target === '_blank') return;
        if (link.hasAttribute('download')) return;
        if (link.dataset.stayiNoLoader === 'true') return;

        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
        if (href.startsWith('mailto:') || href.startsWith('tel:')) return;

        try {
          const url = new URL(link.href, window.location.origin);
          if (url.origin !== window.location.origin) return;
        } catch (_) {
          return;
        }

        sessionStorage.setItem(NAV_KEY, '1');
        StayiLoader.show({ mode: 'page', immediate: true });
      });
    },

    markPageReady() {
      document.documentElement.classList.remove('stayi-nav-loading');
      document.documentElement.classList.add('stayi-page-ready');
      sessionStorage.removeItem(NAV_KEY);
      StayiLoader.hide({ mode: 'page' });
    },

    init() {
      StayiLoader.wrapFetch();
      StayiLoader.bindNavigation();

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          StayiLoader.bindForms();
          window.requestAnimationFrame(() => {
            window.setTimeout(StayiLoader.markPageReady, state.reducedMotion ? 0 : 80);
          });
        });
      } else {
        StayiLoader.bindForms();
        StayiLoader.markPageReady();
      }

      window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
          StayiLoader.markPageReady();
        }
      });
    },
  };

  window.StayiLoader = StayiLoader;

  if (sessionStorage.getItem(NAV_KEY) === '1') {
    document.documentElement.classList.add('stayi-nav-loading');
  }

  StayiLoader.init();
})();
