/**
 * 🔗 JARVIS Deep Link Router
 * ═══════════════════════════════
 * - Handle jarvis://trading/BTCUSDT style deep links
 * - Share links: https://jarvis.app/signal/123
 * - Capacitor App URL listener for Android intent
 * - Web fallback with hash routes
 * - Auto-navigate to correct page with params
 */

class DeepLinkRouter {
  constructor() {
    this.routes = new Map()
    this.pendingLink = null
    this._init()
  }

  _init() {
    // Web: handle hash-based deep links on load
    if (typeof window !== 'undefined') {
      const hash = window.location.hash
      if (hash && hash.startsWith('#/')) {
        this.pendingLink = hash.replace('#', '')
      }

      // Handle web share target
      const params = new URLSearchParams(window.location.search)
      const sharedUrl = params.get('url') || params.get('text')
      if (sharedUrl) {
        this.pendingLink = this._parseShareUrl(sharedUrl)
      }
    }
  }

  /**
   * Register a deep link route handler
   * @param {string} pattern - e.g., '/signal/:id' or '/trade/:symbol'
   * @param {Function} handler - receives { params, navigate }
   */
  register(pattern, handler) {
    this.routes.set(pattern, handler)
  }

  /**
   * Initialize with React Router navigate function
   * Must be called inside a Router context
   */
  activate(navigate) {
    // Process any pending deep link
    if (this.pendingLink) {
      this._resolve(this.pendingLink, navigate)
      this.pendingLink = null
    }

    // Listen for Capacitor app URL events
    this._listenCapacitor(navigate)

    // Listen for custom events (from push notifications)
    window.addEventListener('jarvis-deeplink', (e) => {
      if (e.detail?.url) {
        this._resolve(e.detail.url, navigate)
      }
    })
  }

  async _listenCapacitor(navigate) {
    try {
      const { App } = await import('@capacitor/app').catch(() => ({}))
      if (App?.addListener) {
        App.addListener('appUrlOpen', (event) => {
          const url = event.url
          console.log('[DeepLink] Capacitor URL:', url)
          this._resolve(this._parseCapacitorUrl(url), navigate)
        })
      }
    } catch (e) {
      // Not in Capacitor — web only
    }
  }

  _resolve(path, navigate) {
    if (!path) return

    // Direct routes
    const directRoutes = {
      '/trading': '/trading',
      '/chat': '/chat',
      '/signals': '/trading',
      '/wallet': '/wallet',
      '/settings': '/settings',
      '/paper-trading': '/paper-trading',
      '/pnl': '/pnl-journal',
      '/watchlist': '/watchlist',
      '/alerts': '/smart-alerts',
      '/depth': '/depth-chart',
      '/tax': '/tax-calculator',
      '/scanner': '/gems',
    }

    // Check direct routes first
    for (const [pattern, route] of Object.entries(directRoutes)) {
      if (path.startsWith(pattern)) {
        navigate(route)
        return
      }
    }

    // Parameterized routes
    if (path.startsWith('/trade/')) {
      const symbol = path.split('/')[2]
      navigate('/trading', { state: { symbol } })
      return
    }

    if (path.startsWith('/signal/')) {
      const signalId = path.split('/')[2]
      navigate('/trading', { state: { signalId } })
      return
    }

    if (path.startsWith('/chart/')) {
      const symbol = path.split('/')[2]
      navigate('/candle-indicators', { state: { symbol } })
      return
    }

    // Check custom registered routes
    for (const [pattern, handler] of this.routes) {
      const match = this._matchPattern(pattern, path)
      if (match) {
        handler({ params: match, navigate })
        return
      }
    }

    // Fallback: navigate to path as-is
    navigate(path)
  }

  _parseCapacitorUrl(url) {
    // jarvis://trading/BTCUSDT → /trading/BTCUSDT
    // https://jarvis.app/signal/123 → /signal/123
    try {
      const parsed = new URL(url)
      return parsed.pathname || parsed.hash?.replace('#', '') || '/'
    } catch {
      return url.replace(/^jarvis:\/\//, '/')
    }
  }

  _parseShareUrl(url) {
    try {
      const parsed = new URL(url)
      if (parsed.hostname.includes('jarvis')) {
        return parsed.pathname
      }
    } catch {}
    return null
  }

  _matchPattern(pattern, path) {
    const patternParts = pattern.split('/')
    const pathParts = path.split('/')
    if (patternParts.length !== pathParts.length) return null

    const params = {}
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) {
        params[patternParts[i].slice(1)] = pathParts[i]
      } else if (patternParts[i] !== pathParts[i]) {
        return null
      }
    }
    return params
  }

  /**
   * Generate a shareable deep link URL
   */
  createLink(path, params = {}) {
    const base = 'https://jarvis.app'
    const query = Object.keys(params).length ? '?' + new URLSearchParams(params).toString() : ''
    return `${base}${path}${query}`
  }

  /**
   * Share a deep link via Web Share API
   */
  async share(title, path, params = {}) {
    const url = this.createLink(path, params)
    if (navigator.share) {
      await navigator.share({ title, text: `Check this on JARVIS AI: ${title}`, url })
    } else {
      await navigator.clipboard.writeText(url)
    }
  }
}

const deepLink = new DeepLinkRouter()
export default deepLink
