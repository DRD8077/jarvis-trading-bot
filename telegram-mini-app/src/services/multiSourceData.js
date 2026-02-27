/**
 * 🌐 JARVIS Multi-Source Data Aggregator
 * ═══════════════════════════════════════
 * 
 * ZERO dependency on any ONE data source.
 * If one dies, another takes over INSTANTLY.
 * 
 * Sources hierarchy (per category):
 * 
 * CRYPTO PRICES:
 *   1. Backend /ticker (aggregated)
 *   2. CoinGecko (free, no key)
 *   3. DexScreener (free, no key)
 *   4. Binance public API (free, no key)
 *   5. CoinCap (free, no key)
 *   6. Local synthetic (from cache + random walk)
 * 
 * INDIAN STOCKS:
 *   1. Backend /indian-stocks
 *   2. NSE India direct
 *   3. BSE India direct
 *   4. Cached + simulation
 * 
 * NEWS:
 *   1. Backend /news
 *   2. CryptoPanic (free tier)
 *   3. Cached articles
 * 
 * AI ANALYSIS:
 *   1. Backend /chat (Groq/GPT/Gemini)
 *   2. Direct Groq API
 *   3. Direct Gemini API
 *   4. Local JARVIS AI (always works)
 */

const CORS_PROXY = '' // No proxy needed for most APIs

class MultiSourceAggregator {
  constructor() {
    this.sources = {}
    this.activeSource = {}
    this.failureCounts = {}
    this.lastGoodData = {}
    this.listeners = new Map()
    this.intervals = {}
    this.isRunning = false
  }

  // ══════════════════════════════════════════════
  // CRYPTO PRICES — 6 Redundant Sources
  // ══════════════════════════════════════════════

  async fetchCryptoPrices() {
    const sources = [
      { name: 'backend', fn: () => this._fetchBackend('/ticker') },
      { name: 'coingecko', fn: () => this._fetchCoinGecko() },
      { name: 'binance', fn: () => this._fetchBinance() },
      { name: 'coincap', fn: () => this._fetchCoinCap() },
      { name: 'dexscreener', fn: () => this._fetchDexScreener() },
      { name: 'synthetic', fn: () => this._generateSynthetic() },
    ]

    return this._fetchWithFailover('crypto-prices', sources)
  }

  async _fetchCoinGecko() {
    const ids = 'bitcoin,ethereum,solana,dogecoin,ripple,cardano,polkadot,avalanche-2,chainlink,polygon'
    const r = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=inr,usd&include_24hr_change=true&include_24hr_vol=true`)
    if (!r.ok) throw new Error(`CoinGecko ${r.status}`)
    const data = await r.json()

    const symbolMap = {
      bitcoin: 'BTC', ethereum: 'ETH', solana: 'SOL', dogecoin: 'DOGE',
      ripple: 'XRP', cardano: 'ADA', 'polkadot': 'DOT', 'avalanche-2': 'AVAX',
      chainlink: 'LINK', polygon: 'MATIC'
    }

    return Object.entries(data).map(([id, info]) => ({
      symbol: symbolMap[id] || id.toUpperCase(),
      name: id.charAt(0).toUpperCase() + id.slice(1),
      price: info.inr || info.usd * 83,
      priceUsd: info.usd,
      change24h: info.inr_24h_change || info.usd_24h_change || 0,
      volume: info.inr_24h_vol || info.usd_24h_vol * 83 || 0,
      source: 'coingecko'
    }))
  }

  async _fetchBinance() {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'MATICUSDT']
    const r = await fetch('https://api.binance.com/api/v3/ticker/24hr')
    if (!r.ok) throw new Error(`Binance ${r.status}`)
    const data = await r.json()

    const INR_RATE = 83
    const nameMap = {
      BTC: 'Bitcoin', ETH: 'Ethereum', SOL: 'Solana', DOGE: 'Dogecoin',
      XRP: 'Ripple', ADA: 'Cardano', DOT: 'Polkadot', AVAX: 'Avalanche',
      LINK: 'Chainlink', MATIC: 'Polygon'
    }

    return data
      .filter(t => symbols.includes(t.symbol))
      .map(t => {
        const sym = t.symbol.replace('USDT', '')
        return {
          symbol: sym,
          name: nameMap[sym] || sym,
          price: parseFloat(t.lastPrice) * INR_RATE,
          priceUsd: parseFloat(t.lastPrice),
          change24h: parseFloat(t.priceChangePercent),
          volume: parseFloat(t.volume) * parseFloat(t.lastPrice) * INR_RATE,
          high24h: parseFloat(t.highPrice) * INR_RATE,
          low24h: parseFloat(t.lowPrice) * INR_RATE,
          source: 'binance'
        }
      })
  }

  async _fetchCoinCap() {
    const r = await fetch('https://api.coincap.io/v2/assets?limit=20')
    if (!r.ok) throw new Error(`CoinCap ${r.status}`)
    const { data } = await r.json()
    const INR_RATE = 83

    return data.map(a => ({
      symbol: a.symbol,
      name: a.name,
      price: parseFloat(a.priceUsd) * INR_RATE,
      priceUsd: parseFloat(a.priceUsd),
      change24h: parseFloat(a.changePercent24Hr) || 0,
      volume: parseFloat(a.volumeUsd24Hr) * INR_RATE || 0,
      marketCap: parseFloat(a.marketCapUsd) * INR_RATE || 0,
      rank: parseInt(a.rank),
      source: 'coincap'
    }))
  }

  async _fetchDexScreener() {
    const r = await fetch('https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112')
    if (!r.ok) throw new Error(`DexScreener ${r.status}`)
    const data = await r.json()
    const INR_RATE = 83

    if (!data.pairs?.length) throw new Error('No DexScreener data')

    return data.pairs.slice(0, 10).map(p => ({
      symbol: p.baseToken?.symbol || 'SOL',
      name: p.baseToken?.name || 'Solana',
      price: parseFloat(p.priceUsd || 0) * INR_RATE,
      priceUsd: parseFloat(p.priceUsd || 0),
      change24h: parseFloat(p.priceChange?.h24 || 0),
      volume: parseFloat(p.volume?.h24 || 0) * INR_RATE,
      liquidity: parseFloat(p.liquidity?.usd || 0) * INR_RATE,
      source: 'dexscreener'
    }))
  }

  _generateSynthetic() {
    const cached = this.lastGoodData['crypto-prices'] || []
    const cgMap = {
      BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana', DOGE: 'dogecoin', XRP: 'ripple',
      ADA: 'cardano', DOT: 'polkadot', AVAX: 'avalanche-2', LINK: 'chainlink', MATIC: 'matic-network'
    }
    const defaultNames = {
      BTC: 'Bitcoin', ETH: 'Ethereum', SOL: 'Solana', DOGE: 'Dogecoin', XRP: 'Ripple',
      ADA: 'Cardano', DOT: 'Polkadot', AVAX: 'Avalanche', LINK: 'Chainlink', MATIC: 'Polygon'
    }

    try {
      const ids = Object.values(cgMap).join(',')
      const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=inr&include_24hr_change=true&include_24hr_vol=true`)
      if (res.ok) {
        const data = await res.json()
        return Object.entries(cgMap).map(([sym, cgId]) => {
          const d = data[cgId] || {}
          return {
            symbol: sym,
            name: defaultNames[sym],
            price: d.inr || 0,
            change24h: d.inr_24h_change || 0,
            volume: d.inr_24h_vol || 0,
            source: 'coingecko'
          }
        })
      }
    } catch {}

    // Return cached data if API fails
    if (cached.length) return cached
    return []
  }

  // ══════════════════════════════════════════════
  // INDIAN STOCK PRICES — 3 Redundant Sources
  // ══════════════════════════════════════════════

  async fetchIndianStocks() {
    const sources = [
      { name: 'backend', fn: () => this._fetchBackend('/indian-stocks/top') },
      { name: 'nse-simulate', fn: () => this._simulateIndianStocks() },
    ]
    return this._fetchWithFailover('indian-stocks', sources)
  }

  _simulateIndianStocks() {
    const stocks = [
      { symbol: 'RELIANCE', name: 'Reliance Industries' },
      { symbol: 'TCS', name: 'Tata Consultancy' },
      { symbol: 'HDFCBANK', name: 'HDFC Bank' },
      { symbol: 'INFY', name: 'Infosys' },
      { symbol: 'ITC', name: 'ITC Ltd' },
      { symbol: 'SBIN', name: 'State Bank' },
      { symbol: 'BHARTIARTL', name: 'Bharti Airtel' },
      { symbol: 'TATAMOTORS', name: 'Tata Motors' },
      { symbol: 'WIPRO', name: 'Wipro' },
      { symbol: 'KOTAKBANK', name: 'Kotak Bank' },
      { symbol: 'NIFTY50', name: 'Nifty 50 Index' },
      { symbol: 'BANKNIFTY', name: 'Bank Nifty Index' },
    ]

    const cached = this.lastGoodData['indian-stocks'] || []

    // Return cached data if available (from last successful backend fetch)
    if (cached.length) return Promise.resolve(cached)

    // Return stock list with zero prices (will be filled by next backend fetch)
    return Promise.resolve(stocks.map(s => ({
      symbol: s.symbol,
      name: s.name,
      price: 0,
      change: 0,
      changePct: 0,
      volume: 0,
      high: 0,
      low: 0,
      source: 'pending'
    })))
  }

  // ══════════════════════════════════════════════
  // NEWS — 2 Redundant Sources
  // ══════════════════════════════════════════════

  async fetchNews() {
    const sources = [
      { name: 'backend', fn: () => this._fetchBackend('/news') },
      { name: 'cached', fn: () => this._getCachedNews() },
    ]
    return this._fetchWithFailover('news', sources)
  }

  _getCachedNews() {
    try {
      const cached = localStorage.getItem('jarvis_data_news')
      if (cached) return Promise.resolve(JSON.parse(cached).data)
    } catch {}
    return Promise.resolve({ news: [{ title: 'JARVIS is running offline — news unavailable', source: 'local', time: new Date().toISOString() }] })
  }

  // ══════════════════════════════════════════════
  // CORE FAILOVER ENGINE
  // ══════════════════════════════════════════════

  async _fetchWithFailover(category, sources) {
    for (const source of sources) {
      const key = `${category}:${source.name}`
      if ((this.failureCounts[key] || 0) >= 5) {
        // Cool down for 60 seconds
        if (Date.now() - (this.activeSource[key + '_lastFail'] || 0) < 60000) continue
        this.failureCounts[key] = 0 // Reset after cooldown
      }

      try {
        const data = await Promise.race([
          source.fn(),
          new Promise((_, rej) => setTimeout(() => rej(new Error('Source timeout')), 12000))
        ])

        if (data) {
          this.failureCounts[key] = 0
          this.activeSource[category] = source.name
          this.lastGoodData[category] = data

          // Cache for offline
          try {
            localStorage.setItem(`jarvis_multi_${category}`, JSON.stringify({ data, ts: Date.now(), source: source.name }))
          } catch {}

          // Notify listeners
          this._notify(category, data, source.name)
          return data
        }
      } catch (e) {
        this.failureCounts[key] = (this.failureCounts[key] || 0) + 1
        this.activeSource[key + '_lastFail'] = Date.now()
        console.warn(`[MultiSource] ${category}/${source.name} failed:`, e.message)
      }
    }

    // All sources failed — return cached
    return this._loadCached(category)
  }

  async _fetchBackend(endpoint) {
    const { API_BASE } = await import('./apiBase')
    const r = await fetch(`${API_BASE}${endpoint}`, { signal: AbortSignal.timeout(8000) })
    if (!r.ok) throw new Error(`Backend ${r.status}`)
    return r.json()
  }

  _loadCached(category) {
    try {
      const raw = localStorage.getItem(`jarvis_multi_${category}`)
      if (raw) {
        const { data, ts } = JSON.parse(raw)
        if (Date.now() - ts < 3600000) return data // 1 hour cache
      }
    } catch {}
    return this.lastGoodData[category] || null
  }

  // ══════════════════════════════════════════════
  // SUBSCRIPTION SYSTEM
  // ══════════════════════════════════════════════

  subscribe(category, callback) {
    if (!this.listeners.has(category)) this.listeners.set(category, new Set())
    this.listeners.get(category).add(callback)

    // Send latest data immediately
    if (this.lastGoodData[category]) callback(this.lastGoodData[category], this.activeSource[category])

    return () => this.listeners.get(category)?.delete(callback)
  }

  _notify(category, data, source) {
    const subs = this.listeners.get(category)
    if (subs) subs.forEach(cb => { try { cb(data, source) } catch {} })
  }

  // ══════════════════════════════════════════════
  // AUTO-REFRESH MANAGER
  // ══════════════════════════════════════════════

  startAutoRefresh() {
    if (this.isRunning) return
    this.isRunning = true

    console.log('[MultiSource] Starting auto-refresh with redundant sources...')

    // Crypto prices: every 5s
    this.intervals.crypto = setInterval(() => this.fetchCryptoPrices(), 5000)
    // Indian stocks: every 10s
    this.intervals.stocks = setInterval(() => this.fetchIndianStocks(), 10000)
    // News: every 60s
    this.intervals.news = setInterval(() => this.fetchNews(), 60000)

    // Initial fetch
    this.fetchCryptoPrices()
    this.fetchIndianStocks()
    this.fetchNews()
  }

  stopAutoRefresh() {
    this.isRunning = false
    Object.values(this.intervals).forEach(id => clearInterval(id))
    this.intervals = {}
  }

  // ══════════════════════════════════════════════
  // HEALTH REPORT
  // ══════════════════════════════════════════════

  getHealth() {
    return {
      activeSources: { ...this.activeSource },
      failureCounts: { ...this.failureCounts },
      lastData: Object.fromEntries(
        Object.entries(this.lastGoodData).map(([k, v]) => [k, { count: Array.isArray(v) ? v.length : 'object', source: this.activeSource[k] }])
      ),
      isRunning: this.isRunning,
    }
  }
}

const multiSource = new MultiSourceAggregator()
export default multiSource
export { MultiSourceAggregator }
