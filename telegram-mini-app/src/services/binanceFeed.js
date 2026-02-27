/**
 * 🔥 JARVIS Binance Real-Time Price Feed
 * ═══════════════════════════════════════
 * Connects DIRECTLY to Binance WebSocket for real-time crypto prices.
 * No backend needed — pure browser-to-Binance connection.
 * 
 * Uses combined stream: wss://stream.binance.com:9443/stream
 * Subscribes to mini-ticker for ALL trading pairs or specific ones.
 * 
 * Usage:
 *   import binanceFeed from './binanceFeed'
 *   const unsub = binanceFeed.subscribe('BTCUSDT', (price) => { ... })
 *   // later: unsub()
 */

const BINANCE_WS = 'wss://stream.binance.com:9443/ws'
const BINANCE_STREAM = 'wss://stream.binance.com:9443/stream'
const RECONNECT_DELAYS = [1000, 2000, 5000, 10000, 30000]

class BinanceFeed {
  constructor() {
    this.ws = null
    this.subscribers = new Map()       // symbol → Set<callback>
    this.allTickerSubs = new Set()     // callbacks for ALL tickers
    this.prices = new Map()            // symbol → { price, change24h, volume, high, low, ts }
    this.reconnectAttempt = 0
    this.reconnectTimer = null
    this.connected = false
    this._paused = false
    
    // Auto-connect when first subscriber is added
    // Listen for visibility
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          this._pause()
        } else {
          this._resume()
        }
      })
    }
  }

  /**
   * Subscribe to price updates for a specific symbol
   * @param {string} symbol - e.g. 'BTCUSDT'
   * @param {Function} callback - ({price, change24h, volume, high, low, ts}) => void
   * @returns {Function} unsubscribe
   */
  subscribe(symbol, callback) {
    const sym = symbol.toUpperCase()
    if (!this.subscribers.has(sym)) {
      this.subscribers.set(sym, new Set())
    }
    this.subscribers.get(sym).add(callback)
    
    // Deliver cached price immediately
    const cached = this.prices.get(sym)
    if (cached) {
      try { callback(cached) } catch {}
    }
    
    // Connect if not connected
    if (!this.connected && !this._paused) {
      this._connect()
    }
    
    return () => {
      const subs = this.subscribers.get(sym)
      if (subs) {
        subs.delete(callback)
        if (subs.size === 0) this.subscribers.delete(sym)
      }
      // Disconnect if no subscribers left
      if (this.subscribers.size === 0 && this.allTickerSubs.size === 0) {
        this._disconnect()
      }
    }
  }

  /**
   * Subscribe to ALL ticker updates (24hr mini ticker for all symbols)
   * @param {Function} callback - (Map<symbol, priceData>) => void, called every ~1s with full map
   * @returns {Function} unsubscribe
   */
  subscribeAll(callback) {
    this.allTickerSubs.add(callback)
    
    // Deliver cached immediately
    if (this.prices.size > 0) {
      try { callback(this.prices) } catch {}
    }
    
    if (!this.connected && !this._paused) {
      this._connect()
    }
    
    return () => {
      this.allTickerSubs.delete(callback)
      if (this.subscribers.size === 0 && this.allTickerSubs.size === 0) {
        this._disconnect()
      }
    }
  }

  /**
   * Get cached price for a symbol
   */
  getPrice(symbol) {
    return this.prices.get(symbol.toUpperCase()) || null
  }

  /**
   * Get all cached prices
   */
  getAllPrices() {
    return this.prices
  }

  // ─── Internal Connection ────────────────────────────────────
  _connect() {
    if (this.ws) return
    
    try {
      // Use !miniTicker@arr for ALL symbols (efficient single stream)
      const url = `${BINANCE_WS}/!miniTicker@arr`
      this.ws = new WebSocket(url)
      
      this.ws.onopen = () => {
        console.log('[BinanceFeed] ⚡ Connected — real-time prices active')
        this.connected = true
        this.reconnectAttempt = 0
      }
      
      this.ws.onmessage = (evt) => {
        try {
          const tickers = JSON.parse(evt.data)
          this._processTickers(tickers)
        } catch {}
      }
      
      this.ws.onclose = () => {
        this.connected = false
        this.ws = null
        if (!this._paused && (this.subscribers.size > 0 || this.allTickerSubs.size > 0)) {
          this._scheduleReconnect()
        }
      }
      
      this.ws.onerror = () => {
        // Will trigger onclose
      }
    } catch (e) {
      console.warn('[BinanceFeed] Connection failed:', e.message)
      this._scheduleReconnect()
    }
  }
  
  _disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connected = false
  }
  
  _scheduleReconnect() {
    if (this.reconnectTimer) return
    const delay = RECONNECT_DELAYS[Math.min(this.reconnectAttempt, RECONNECT_DELAYS.length - 1)]
    this.reconnectAttempt++
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      if (!this._paused) this._connect()
    }, delay)
  }
  
  _pause() {
    this._paused = true
    this._disconnect()
    console.log('[BinanceFeed] ⏸️ Paused (app in background)')
  }
  
  _resume() {
    this._paused = false
    if (this.subscribers.size > 0 || this.allTickerSubs.size > 0) {
      console.log('[BinanceFeed] ▶️ Resuming...')
      this._connect()
    }
  }

  // ─── Process Ticker Data ────────────────────────────────────
  _processTickers(tickers) {
    if (!Array.isArray(tickers)) return
    
    let hasSubscriberUpdates = false
    
    for (const t of tickers) {
      // Binance mini ticker format:
      // e: event type, s: symbol, c: close price, o: open, h: high, l: low, v: volume, q: quote volume
      const symbol = t.s
      const price = parseFloat(t.c)
      const open = parseFloat(t.o)
      const change24h = open > 0 ? ((price - open) / open * 100) : 0
      
      const data = {
        symbol,
        price,
        open,
        high: parseFloat(t.h),
        low: parseFloat(t.l),
        volume: parseFloat(t.v),
        quoteVolume: parseFloat(t.q),
        change24h: Math.round(change24h * 100) / 100,
        ts: Date.now(),
      }
      
      this.prices.set(symbol, data)
      
      // Notify symbol-specific subscribers
      const subs = this.subscribers.get(symbol)
      if (subs && subs.size > 0) {
        hasSubscriberUpdates = true
        for (const cb of subs) {
          try { cb(data) } catch {}
        }
      }
    }
    
    // Notify all-ticker subscribers (throttled - only if we have them)
    if (this.allTickerSubs.size > 0) {
      for (const cb of this.allTickerSubs) {
        try { cb(this.prices) } catch {}
      }
    }
  }

  // ─── Top Movers ─────────────────────────────────────────────
  /**
   * Get top gainers/losers from cached data
   * @param {number} count - how many to return
   * @returns {{ gainers: Array, losers: Array }}
   */
  getTopMovers(count = 10) {
    const usdt = Array.from(this.prices.values())
      .filter(p => p.symbol.endsWith('USDT') && p.volume > 0)
      .sort((a, b) => b.change24h - a.change24h)
    
    return {
      gainers: usdt.slice(0, count),
      losers: usdt.slice(-count).reverse(),
    }
  }

  getStats() {
    return {
      connected: this.connected,
      symbolCount: this.prices.size,
      subscriberCount: this.subscribers.size,
      allTickerSubs: this.allTickerSubs.size,
      paused: this._paused,
    }
  }
}

const binanceFeed = new BinanceFeed()
export default binanceFeed
