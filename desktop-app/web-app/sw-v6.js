/**
 * 🛡️ JARVIS Advanced Service Worker
 * ═══════════════════════════════════
 * 
 * Military-grade caching strategies:
 * - Cache-First for static assets (JS, CSS, images)
 * - Network-First for API calls (with cache fallback)
 * - Stale-While-Revalidate for market data
 * - Background Sync for offline trades
 * - Push notification handling
 * - Periodic price checks
 */

const CACHE_NAME = 'jarvis-v6-cache'
const API_CACHE = 'jarvis-api-cache'
const DATA_CACHE = 'jarvis-data-cache'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
]

// ═══════════════════════════════════
// INSTALL — Cache critical assets
// ═══════════════════════════════════
self.addEventListener('install', (event) => {
  console.log('[JARVIS SW] Installing v6.0...')
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        console.log('[JARVIS SW] Some assets failed to cache, continuing...')
      })
    }).then(() => self.skipWaiting())
  )
})

// ═══════════════════════════════════
// ACTIVATE — Clean old caches
// ═══════════════════════════════════
self.addEventListener('activate', (event) => {
  console.log('[JARVIS SW] Activating v6.0...')
  event.waitUntil(
    caches.keys().then(names => {
      return Promise.all(
        names.filter(n => n !== CACHE_NAME && n !== API_CACHE && n !== DATA_CACHE)
          .map(n => caches.delete(n))
      )
    }).then(() => self.clients.claim())
  )
})

// ═══════════════════════════════════
// FETCH — Smart caching strategies
// ═══════════════════════════════════
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // Skip non-GET requests
  if (event.request.method !== 'GET') return

  // Skip WebSocket and chrome-extension requests
  if (url.protocol === 'ws:' || url.protocol === 'wss:' || url.protocol === 'chrome-extension:') return

  // Strategy 1: Cache-First for static assets
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(event.request, CACHE_NAME))
    return
  }

  // Strategy 2: Stale-While-Revalidate for price/market data
  if (isMarketData(url)) {
    event.respondWith(staleWhileRevalidate(event.request, DATA_CACHE, 30000))
    return
  }

  // Strategy 3: Network-First for API calls
  if (isAPICall(url)) {
    event.respondWith(networkFirst(event.request, API_CACHE, 10000))
    return
  }

  // Default: Network with cache fallback
  event.respondWith(networkFirst(event.request, CACHE_NAME, 5000))
})

// ═══════════════════════════════════
// CACHING STRATEGIES
// ═══════════════════════════════════

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request)
  if (cached) return cached

  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    return response
  } catch {
    return new Response('Offline', { status: 503 })
  }
}

async function networkFirst(request, cacheName, timeout = 5000) {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeout)

    const response = await fetch(request, { signal: controller.signal })
    clearTimeout(timer)

    if (response.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    return response
  } catch {
    const cached = await caches.match(request)
    if (cached) return cached
    return new Response(JSON.stringify({ error: 'offline', cached: false }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

async function staleWhileRevalidate(request, cacheName, maxAge = 30000) {
  const cache = await caches.open(cacheName)
  const cached = await cache.match(request)

  // Return cached immediately, then update in background
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone())
    }
    return response
  }).catch(() => null)

  if (cached) {
    // Check if stale
    const cachedDate = cached.headers.get('sw-cached-at')
    const age = cachedDate ? Date.now() - parseInt(cachedDate) : Infinity
    if (age < maxAge) {
      return cached
    }
  }

  // If no cache or too stale, wait for network
  const networkResponse = await fetchPromise
  if (networkResponse) return networkResponse
  if (cached) return cached

  return new Response(JSON.stringify({ error: 'offline' }), {
    status: 503, headers: { 'Content-Type': 'application/json' }
  })
}

// ═══════════════════════════════════
// URL CLASSIFIERS
// ═══════════════════════════════════

function isStaticAsset(url) {
  return url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|ico|woff2?|ttf|eot)$/) ||
    url.pathname.startsWith('/assets/')
}

function isMarketData(url) {
  return url.hostname.includes('coingecko') ||
    url.hostname.includes('binance') ||
    url.hostname.includes('coincap') ||
    url.hostname.includes('dexscreener') ||
    url.pathname.includes('/ticker') ||
    url.pathname.includes('/market') ||
    url.pathname.includes('/price')
}

function isAPICall(url) {
  return url.pathname.startsWith('/api') ||
    url.pathname.startsWith('/miniapp') ||
    url.pathname.includes('/chat') ||
    url.pathname.includes('/signals')
}

// ═══════════════════════════════════
// BACKGROUND SYNC — Offline trades
// ═══════════════════════════════════
self.addEventListener('sync', (event) => {
  if (event.tag === 'jarvis-sync-trades') {
    event.waitUntil(syncOfflineTrades())
  }
  if (event.tag === 'jarvis-sync-alerts') {
    event.waitUntil(syncOfflineAlerts())
  }
})

async function syncOfflineTrades() {
  try {
    const db = await openIDB()
    const tx = db.transaction('sync_queue', 'readonly')
    const store = tx.objectStore('sync_queue')
    const pending = await idbGetAll(store)

    for (const item of pending) {
      if (item.action === 'trade') {
        await fetch('/api/trades/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.payload)
        })
      }
    }
  } catch (e) {
    console.log('[JARVIS SW] Trade sync failed, will retry:', e.message)
  }
}

async function syncOfflineAlerts() {
  console.log('[JARVIS SW] Syncing offline alerts...')
}

// ═══════════════════════════════════
// PUSH NOTIFICATIONS
// ═══════════════════════════════════
self.addEventListener('push', (event) => {
  let data = { title: 'JARVIS Alert', body: 'New notification', icon: '/icons/icon-192.png' }

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() }
    } catch {
      data.body = event.data.text()
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon || '/icons/icon-192.png',
      badge: '/icons/icon-72.png',
      vibrate: [100, 50, 100],
      data: data.data || {},
      actions: data.actions || [
        { action: 'view', title: 'View' },
        { action: 'dismiss', title: 'Dismiss' }
      ],
      tag: data.tag || 'jarvis-notification',
      renotify: true
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  const url = event.notification.data?.url || '/'

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
      const existing = clients.find(c => c.url.includes(url))
      if (existing) return existing.focus()
      return self.clients.openWindow(url)
    })
  )
})

// ═══════════════════════════════════
// PERIODIC BACKGROUND SYNC
// ═══════════════════════════════════
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'jarvis-price-check') {
    event.waitUntil(backgroundPriceCheck())
  }
})

async function backgroundPriceCheck() {
  try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd')
    const prices = await res.json()

    // Check against stored alerts
    const btcPrice = prices.bitcoin?.usd || 0
    const ethPrice = prices.ethereum?.usd || 0

    // Notify if significant movement (>5%)
    const lastBTC = parseFloat(await getCachedValue('last_btc_price') || '0')
    if (lastBTC > 0) {
      const change = Math.abs((btcPrice - lastBTC) / lastBTC * 100)
      if (change > 5) {
        self.registration.showNotification('JARVIS Price Alert', {
          body: `BTC ${btcPrice > lastBTC ? '🚀' : '📉'} $${btcPrice.toLocaleString()} (${change.toFixed(1)}% ${btcPrice > lastBTC ? 'UP' : 'DOWN'})`,
          icon: '/icons/icon-192.png',
          badge: '/icons/icon-72.png',
          vibrate: [200, 100, 200],
          tag: 'price-alert'
        })
      }
    }
    await setCachedValue('last_btc_price', String(btcPrice))
  } catch {
    // Silent fail — background check
  }
}

// ═══════════════════════════════════
// HELPER: Simple KV Cache
// ═══════════════════════════════════
function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('jarvis_sw_cache', 1)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains('kv')) db.createObjectStore('kv')
      if (!db.objectStoreNames.contains('sync_queue')) db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true })
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

function idbGetAll(store) {
  return new Promise((resolve, reject) => {
    const req = store.getAll()
    req.onsuccess = () => resolve(req.result || [])
    req.onerror = () => reject(req.error)
  })
}

async function getCachedValue(key) {
  const db = await openIDB()
  return new Promise((resolve) => {
    const tx = db.transaction('kv', 'readonly')
    const req = tx.objectStore('kv').get(key)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => resolve(null)
  })
}

async function setCachedValue(key, value) {
  const db = await openIDB()
  return new Promise((resolve) => {
    const tx = db.transaction('kv', 'readwrite')
    tx.objectStore('kv').put(value, key)
    tx.oncomplete = () => resolve()
    tx.onerror = () => resolve()
  })
}

console.log('[JARVIS SW v6.0] Service Worker loaded — Military-grade caching active')
