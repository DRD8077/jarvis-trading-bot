const CACHE_NAME = 'jarvis-v1';
const STATIC_ASSETS = [
  '/miniapp',
  '/miniapp/index.html'
];

// Install — cache shell
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch — Network first, fallback to cache (always fresh data)
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  
  // API calls — always network, never cache
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Static assets (JS/CSS) — cache first for speed
  if (e.request.destination === 'script' || e.request.destination === 'style' || url.pathname.match(/\.(js|css|woff2?|png|jpg|svg)$/)) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const fetchPromise = fetch(e.request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
          }
          return response;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // HTML pages — network first (always latest)
  e.respondWith(
    fetch(e.request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        return response;
      })
      .catch(() => caches.match(e.request) || caches.match('/miniapp'))
  );
});
