/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  JARVIS BACKEND API CLIENT — Real Server Connection              ║
 * ║  Connects to the JARVIS FastAPI Server with JWT Auth             ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

// ═══════════════════════════════════════════════════════════════
//  SERVER URL DETECTION
// ═══════════════════════════════════════════════════════════════

function getServerURL() {
  // Use the SAME server detection as apiBase.js
  // 1. VITE env override (same var as apiBase)
  if (import.meta.env.VITE_SERVER_URL) {
    return import.meta.env.VITE_SERVER_URL
  }
  if (import.meta.env.VITE_JARVIS_SERVER) {
    return import.meta.env.VITE_JARVIS_SERVER
  }
  // 2. Runtime config
  if (window?.__JARVIS_CONFIG__?.serverUrl) {
    return window.__JARVIS_CONFIG__.serverUrl
  }
  // 3. Same-origin (dev mode)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return `http://localhost:8000`
  }
  // 4. Native APK — hardcoded codespace URL (matches apiBase.js)
  if (window?.Capacitor?.isNativePlatform?.() || window.location.protocol === 'capacitor:') {
    return 'https://super-duper-funicular-gp99q655qw6cprr-8000.app.github.dev'
  }
  // 5. Fallback — same origin
  return window.location.origin
}

const SERVER_URL = getServerURL()

console.log(`[JARVIS Backend] Server: ${SERVER_URL}`)

// ═══════════════════════════════════════════════════════════════
//  TOKEN MANAGEMENT
// ═══════════════════════════════════════════════════════════════

const TOKEN_KEY = 'jarvis_access_token'
const REFRESH_KEY = 'jarvis_refresh_token'
const USER_KEY = 'jarvis_user'

function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}

function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

function setTokens(access, refresh) {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

function setStoredUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// ═══════════════════════════════════════════════════════════════
//  FETCH WRAPPER with Auth & Retry
// ═══════════════════════════════════════════════════════════════

let _isRefreshing = false
let _refreshPromise = null

async function jarvisFetch(path, options = {}) {
  const url = `${SERVER_URL}${path}`
  const token = getAccessToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    // Token expired — try refresh
    if (response.status === 401 && getRefreshToken()) {
      const newTokens = await refreshTokens()
      if (newTokens) {
        headers['Authorization'] = `Bearer ${newTokens.access_token}`
        return fetch(url, { ...options, headers })
      }
    }

    return response
  } catch (error) {
    console.error(`[JARVIS API] ${path} failed:`, error.message)
    throw error
  }
}

async function refreshTokens() {
  if (_isRefreshing) return _refreshPromise

  _isRefreshing = true
  _refreshPromise = (async () => {
    try {
      const resp = await fetch(`${SERVER_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: getRefreshToken() }),
      })

      if (!resp.ok) {
        clearTokens()
        return null
      }

      const data = await resp.json()
      setTokens(data.access_token, data.refresh_token)
      return data
    } catch {
      clearTokens()
      return null
    } finally {
      _isRefreshing = false
      _refreshPromise = null
    }
  })()

  return _refreshPromise
}

async function apiGet(path, params = {}) {
  const searchParams = new URLSearchParams()
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null) searchParams.set(key, val)
  }
  const query = searchParams.toString()
  const fullPath = query ? `${path}?${query}` : path
  const resp = await jarvisFetch(fullPath)
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return resp.json()
}

async function apiPost(path, body = {}) {
  const resp = await jarvisFetch(path, {
    method: 'POST',
    body: JSON.stringify(body),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return resp.json()
}

async function apiDelete(path) {
  const resp = await jarvisFetch(path, { method: 'DELETE' })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return resp.json()
}


// ═══════════════════════════════════════════════════════════════
//  AUTH API
// ═══════════════════════════════════════════════════════════════

export const JarvisAuth = {
  async register(username, password, email = null) {
    const data = await apiPost('/api/auth/register', { username, password, email })
    setTokens(data.access_token, data.refresh_token)
    setStoredUser(data.user)
    return data
  },

  async login(username, password) {
    const data = await apiPost('/api/auth/login', { username, password })
    setTokens(data.access_token, data.refresh_token)
    setStoredUser(data.user)
    return data
  },

  async logout() {
    try {
      await apiPost('/api/auth/logout')
    } catch { /* ignore */ }
    clearTokens()
  },

  async getMe() {
    return apiGet('/api/auth/me')
  },

  async changePassword(oldPassword, newPassword) {
    const result = await apiPost('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
    clearTokens()
    return result
  },

  isLoggedIn() {
    return !!getAccessToken()
  },

  getUser() {
    return getStoredUser()
  },
}


// ═══════════════════════════════════════════════════════════════
//  AI CHAT API
// ═══════════════════════════════════════════════════════════════

export const JarvisAI = {
  async chat(message, context = '') {
    return apiPost('/api/ai/chat', { message, context })
  },

  async analyze(symbol) {
    return apiPost(`/api/ai/analyze/${encodeURIComponent(symbol)}`)
  },

  async getSignal(symbol) {
    return apiPost(`/api/ai/signal/${encodeURIComponent(symbol)}`)
  },

  async getChatHistory(limit = 50) {
    return apiGet('/api/ai/history', { limit })
  },
}


// ═══════════════════════════════════════════════════════════════
//  MARKET DATA API
// ═══════════════════════════════════════════════════════════════

export const JarvisMarket = {
  async getTopCryptos(limit = 100, currency = 'usd') {
    return apiGet('/api/market/top', { limit, currency })
  },

  async getPrice(coinId) {
    return apiGet(`/api/market/price/${encodeURIComponent(coinId)}`)
  },

  async search(query) {
    return apiGet('/api/market/search', { q: query })
  },

  async getTrending() {
    return apiGet('/api/market/trending')
  },

  async getGlobal() {
    return apiGet('/api/market/global')
  },

  async getFearGreed() {
    return apiGet('/api/market/fear-greed')
  },

  async getPriceHistory(coinId, days = 30, currency = 'usd') {
    return apiGet(`/api/market/history/${encodeURIComponent(coinId)}`, { days, currency })
  },

  async getBinanceTicker(symbol) {
    return apiGet(`/api/market/ticker/${encodeURIComponent(symbol)}`)
  },

  async getKlines(symbol, interval = '1h', limit = 100) {
    return apiGet(`/api/market/klines/${encodeURIComponent(symbol)}`, { interval, limit })
  },

  async getWhales() {
    return apiGet('/api/market/whales')
  },

  async searchDex(query) {
    return apiGet('/api/market/dex/search', { q: query })
  },

  async getNewDexPairs(chain = 'solana') {
    return apiGet('/api/market/dex/new', { chain })
  },
}


// ═══════════════════════════════════════════════════════════════
//  PORTFOLIO API
// ═══════════════════════════════════════════════════════════════

export const JarvisPortfolio = {
  async getPortfolios() {
    return apiGet('/api/portfolio')
  },

  async addHolding(symbol, quantity, avgBuyPrice, assetType = 'crypto', chain = null) {
    return apiPost('/api/portfolio/holding', {
      symbol,
      quantity,
      avg_buy_price: avgBuyPrice,
      asset_type: assetType,
      chain,
    })
  },

  async removeHolding(holdingId) {
    return apiDelete(`/api/portfolio/holding/${holdingId}`)
  },

  async recordTrade(symbol, side, quantity, price, notes = '') {
    return apiPost('/api/portfolio/trade', {
      symbol, side, quantity, price, notes,
    })
  },

  async getTrades(limit = 50) {
    return apiGet('/api/portfolio/trades', { limit })
  },
}


// ═══════════════════════════════════════════════════════════════
//  ALERTS API
// ═══════════════════════════════════════════════════════════════

export const JarvisAlerts = {
  async getAlerts() {
    return apiGet('/api/alerts')
  },

  async createAlert(symbol, condition, targetPrice) {
    return apiPost('/api/alerts', {
      symbol,
      condition,
      target_price: targetPrice,
    })
  },

  async deleteAlert(alertId) {
    return apiDelete(`/api/alerts/${alertId}`)
  },
}


// ═══════════════════════════════════════════════════════════════
//  SERVER STATUS
// ═══════════════════════════════════════════════════════════════

export const JarvisServer = {
  async health() {
    return apiGet('/health')
  },

  async status() {
    return apiGet('/api/status')
  },

  getServerURL() {
    return SERVER_URL
  },
}


// ═══════════════════════════════════════════════════════════════
//  DEFAULT EXPORT
// ═══════════════════════════════════════════════════════════════

const JarvisBackend = {
  auth: JarvisAuth,
  ai: JarvisAI,
  market: JarvisMarket,
  portfolio: JarvisPortfolio,
  alerts: JarvisAlerts,
  server: JarvisServer,
}

export default JarvisBackend
