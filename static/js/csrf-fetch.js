(function () {
  const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);
  const originalFetch = window.fetch.bind(window);

  function readCookie(name) {
    const prefix = `${name}=`;
    return document.cookie
      .split(';')
      .map((value) => value.trim())
      .find((value) => value.startsWith(prefix))
      ?.slice(prefix.length) || '';
  }

  function csrfToken() {
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    return metaToken && metaToken !== 'NOTPROVIDED' ? metaToken : readCookie('csrftoken');
  }

  function isSameOrigin(input) {
    const url = typeof input === 'string' ? input : input?.url || '';
    if (!url || url.startsWith('/')) return true;
    try {
      return new URL(url, window.location.href).origin === window.location.origin;
    } catch {
      return false;
    }
  }

  function requestMethod(input, init) {
    return (init?.method || input?.method || 'GET').toUpperCase();
  }

  window.fetch = function csrfFetch(input, init = {}) {
    const method = requestMethod(input, init);
    if (SAFE_METHODS.has(method) || !isSameOrigin(input)) {
      return originalFetch(input, init);
    }

    const token = csrfToken();
    if (!token) {
      return originalFetch(input, init);
    }

    const headers = new Headers(init.headers || input?.headers || {});
    if (!headers.has('X-CSRFToken')) {
      headers.set('X-CSRFToken', token);
    }

    return originalFetch(input, { ...init, headers });
  };
})();
