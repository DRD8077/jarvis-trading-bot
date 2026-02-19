// JARVIS Trading — Bulletproof Service Worker v5
// Makes the old APK work even when Codespace is OFF
// Strategy: Cache everything on first load, use Railway as fallback origin

const CACHE_NAME = 'jarvis-v5';
const RAILWAY = 'https://jarvis-trading-production.up.railway.app';

// ─── INSTALL: Precache shell + fetch Railway version as backup ───
self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    try { await cache.addAll(['/miniapp', '/miniapp/index.html']); } catch(e) {}
    try {
      const html = await fetch(RAILWAY + '/miniapp');
      if (html.ok) await cache.put('__railway_shell__', html.clone());
    } catch(e) {}
  })());
  self.skipWaiting();
});

// ─── ACTIVATE: Clean old caches, take control immediately ───
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

// ─── FETCH: Smart multi-origin routing ───
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // ── API CALLS: Always go to Railway (24/7 server) ──
  if (url.pathname.startsWith('/api/')) {
    e.respondWith((async () => {
      const railwayUrl = RAILWAY + url.pathname + url.search;
      try {
        return await fetch(railwayUrl, { mode: 'cors' });
      } catch(err) {
        try { return await fetch(e.request); } catch(e2) {
          return new Response(JSON.stringify({error:'offline'}), {
            status: 503, headers: {'Content-Type':'application/json'}
          });
        }
      }
    })());
    return;
  }

  // ── STATIC ASSETS: Cache-first → Original → Railway fallback ──
  if (url.pathname.startsWith('/miniapp/assets/') || 
      url.pathname.match(/\.(js|css|woff2?|png|jpg|svg|ico)$/)) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(e.request);
      if (cached) {
        fetch(e.request).then(r => { if(r && r.ok) cache.put(e.request, r); }).catch(()=>{});
        return cached;
      }
      try {
        const resp = await fetch(e.request);
        if (resp.ok) { cache.put(e.request, resp.clone()); return resp; }
      } catch(e1) {}
      try {
        const resp = await fetch(RAILWAY + url.pathname + url.search);
        if (resp.ok) { cache.put(e.request, resp.clone()); return resp; }
      } catch(e2) {}
      return new Response('', {status: 404});
    })());
    return;
  }

  // ── HTML / NAVIGATION: Network → Cache → Railway ──
  e.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      const resp = await fetch(e.request);
      if (resp.ok) { cache.put(e.request, resp.clone()); return resp; }
    } catch(e1) {}
    const cached = await cache.match(e.request);
    if (cached) return cached;
    const shell = await cache.match('/miniapp');
    if (shell) return shell;
    const railwayShell = await cache.match('__railway_shell__');
    if (railwayShell) return railwayShell;
    try {
      const resp = await fetch(RAILWAY + '/miniapp');
      if (resp.ok) { cache.put('__railway_shell__', resp.clone()); return resp; }
    } catch(e3) {}
    return new Response('<h1>JARVIS Offline</h1>', {status: 503, headers: {'Content-Type':'text/html'}});
  })());
});

// ─── PREFETCH: Cache all assets when told to ───
self.addEventListener('message', (e) => {
  if (e.data === 'PREFETCH_ALL') {
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const htmlResp = await cache.match('/miniapp') || await fetch('/miniapp');
        const html = await htmlResp.clone().text();
        const regex = /\/miniapp\/assets\/[^"'\s)]+/g;
        let match;
        while ((match = regex.exec(html)) !== null) {
          if (!(await cache.match(match[0]))) {
            try { const r = await fetch(match[0]); if(r.ok) await cache.put(match[0], r); } 
            catch(e1) { try { const r = await fetch(RAILWAY+match[0]); if(r.ok) await cache.put(match[0], r); } catch(e2){} }
          }
        }
      } catch(e) {}
    })();
  }
});
