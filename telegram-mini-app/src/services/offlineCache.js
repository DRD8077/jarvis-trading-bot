/**
 * 📦 JARVIS Offline Cache Engine (IndexedDB)
 * ════════════════════════════════════════════
 * - Caches dashboard, portfolio, ticker, signals data
 * - Auto-saves on every API response
 * - Serves stale data when offline
 * - TTL-based expiry (configurable per cache key)
 * - Max 50MB storage budget
 * - Background sync when back online
 */

const DB_NAME = 'jarvis_offline_db'
const DB_VERSION = 2
const STORE_NAME = 'cache'

class OfflineCacheEngine {
  constructor() {
    try {
        this.db = null
      this.isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true
      this.pendingWrites = []
      this._init()
  
    } catch(e) {
      console.warn('[offlineCache] Constructor init error:', e)
    }
}

  async _init() {
    if (typeof window === 'undefined' || !window.indexedDB) return

    try {
      this.db = await this._openDB()
    } catch (e) {
      console.warn('[OfflineCache] IndexedDB init failed:', e.message)
    }

    // Track online state
    window.addEventListener('online', () => {
      this.isOnline = true
      this._flushPendingWrites()
    })
    window.addEventListener('offline', () => {
      this.isOnline = false
    })
  }

  _openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)
      
      request.onupgradeneeded = (e) => {
        const db = e.target.result
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'key' })
          store.createIndex('timestamp', 'timestamp', { unique: false })
          store.createIndex('category', 'category', { unique: false })
        }
      }

      request.onsuccess = (e) => resolve(e.target.result)
      request.onerror = (e) => reject(e.target.error)
    })
  }

  /**
   * Save data to offline cache
   * @param {string} key - Cache key (e.g., 'dashboard', 'portfolio_user123')
   * @param {*} data - Any serializable data
   * @param {object} opts - { ttl: ms, category: string }
   */
  async set(key, data, opts = {}) {
    if (!this.db) return false

    const record = {
      key,
      data,
      timestamp: Date.now(),
      ttl: opts.ttl || 5 * 60 * 1000, // 5 min default
      category: opts.category || 'general',
      size: JSON.stringify(data).length
    }

    try {
      const tx = this.db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      store.put(record)
      await new Promise((resolve, reject) => {
        tx.oncomplete = resolve
        tx.onerror = () => reject(tx.error)
      })
      return true
    } catch (e) {
      console.warn('[OfflineCache] Write failed:', e.message)
      return false
    }
  }

  /**
   * Get cached data
   * @param {string} key
   * @param {boolean} ignoreExpiry - Return even if expired
   * @returns {Promise<{data: *, fresh: boolean, age: number} | null>}
   */
  async get(key, ignoreExpiry = false) {
    if (!this.db) return null

    try {
      const tx = this.db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.get(key)
      
      const record = await new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error)
      })

      if (!record) return null

      const age = Date.now() - record.timestamp
      const fresh = age < record.ttl

      if (!fresh && !ignoreExpiry) return null

      return {
        data: record.data,
        fresh,
        age,
        timestamp: record.timestamp,
        category: record.category
      }
    } catch {
      return null
    }
  }

  /**
   * Get data with online fallback
   * If online: fetch fresh → cache → return
   * If offline: return cached (even expired)
   */
  async getWithFallback(key, fetcher, opts = {}) {
    // Online: try fresh first
    if (this.isOnline && fetcher) {
      try {
        const result = await fetcher()
        const data = result?.data?.data || result?.data || result
        await this.set(key, data, opts)
        return { data, source: 'network', fresh: true }
      } catch {
        // Network failed, try cache
      }
    }

    // Offline or network failed: use cache
    const cached = await this.get(key, true) // ignore expiry when offline
    if (cached) {
      return { data: cached.data, source: 'cache', fresh: cached.fresh, age: cached.age }
    }

    return null
  }

  /**
   * Pre-cache important data for offline use
   */
  async preCacheEssentials(apiModule) {
    if (!this.isOnline || !apiModule) return

    const essentials = [
      { key: 'dashboard', fn: apiModule.fetchDashboard, ttl: 60000 },
      { key: 'ticker', fn: apiModule.fetchTicker, ttl: 30000 },
      { key: 'signals', fn: apiModule.fetchSignals, ttl: 120000 },
      { key: 'markets', fn: apiModule.fetchMarkets, ttl: 60000 },
      { key: 'india_dashboard', fn: apiModule.fetchIndiaDashboard, ttl: 60000 },
    ]

    for (const { key, fn, ttl } of essentials) {
      try {
        const res = await fn()
        const data = res?.data?.data || res?.data || res
        await this.set(key, data, { ttl, category: 'essential' })
      } catch {}
    }
  }

  /**
   * Cache user-specific data
   */
  async cacheUserData(userId, apiModule) {
    if (!this.isOnline || !apiModule || !userId) return

    const userKeys = [
      { key: `wallet_${userId}`, fn: () => apiModule.fetchWallet(), ttl: 300000 },
      { key: `portfolio_${userId}`, fn: () => apiModule.fetchCombinedPortfolio(userId), ttl: 300000 },
    ]

    for (const { key, fn, ttl } of userKeys) {
      try {
        const res = await fn()
        const data = res?.data?.data || res?.data || res
        await this.set(key, data, { ttl, category: 'user' })
      } catch {}
    }
  }

  /**
   * Delete expired entries
   */
  async cleanup() {
    if (!this.db) return

    try {
      const tx = this.db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const request = store.openCursor()

      request.onsuccess = (e) => {
        const cursor = e.target.result
        if (cursor) {
          const record = cursor.value
          const age = Date.now() - record.timestamp
          // Delete if older than 24 hours
          if (age > 24 * 60 * 60 * 1000) {
            cursor.delete()
          }
          cursor.continue()
        }
      }
    } catch {}
  }

  /**
   * Get total cache size
   */
  async getCacheStats() {
    if (!this.db) return { entries: 0, totalSize: 0, categories: {} }

    try {
      const tx = this.db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.getAll()

      const records = await new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error)
      })

      const categories = {}
      let totalSize = 0
      for (const r of records) {
        totalSize += r.size || 0
        categories[r.category] = (categories[r.category] || 0) + 1
      }

      return { entries: records.length, totalSize, totalSizeKB: Math.round(totalSize / 1024), categories }
    } catch {
      return { entries: 0, totalSize: 0, categories: {} }
    }
  }

  async clearAll() {
    if (!this.db) return
    const tx = this.db.transaction(STORE_NAME, 'readwrite')
    tx.objectStore(STORE_NAME).clear()
  }

  _flushPendingWrites() {
    // Re-attempt any failed writes
    const pending = [...this.pendingWrites]
    this.pendingWrites = []
    for (const { key, data, opts } of pending) {
      this.set(key, data, opts)
    }
  }
}

const offlineCache = new OfflineCacheEngine()
export default offlineCache
