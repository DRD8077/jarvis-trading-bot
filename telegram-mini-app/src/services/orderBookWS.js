/**
 * 📊 JARVIS Multi-Exchange Order Book WebSocket
 * ═══════════════════════════════════════════════
 * - Live depth data from Binance + CoinDCX
 * - Real-time bid/ask visualization
 * - Aggregated order book
 * - Spread indicator
 * - Large order detection (whale walls)
 * - Auto-reconnect
 */

class OrderBookWebSocket {
  constructor() {
    this.connections = {}
    this.orderBooks = {}
    this.onUpdate = null
    this.onWhaleWall = null
    this.reconnectAttempts = {}
    this.maxReconnects = 10
  }

  /**
   * Subscribe to order book for a symbol
   * @param {string} symbol - e.g., 'BTCUSDT'
   * @param {string} exchange - 'binance' | 'coindcx'
   */
  subscribe(symbol, exchange = 'binance') {
    const key = `${exchange}_${symbol}`
    if (this.connections[key]) return // Already connected

    this.orderBooks[key] = { bids: [], asks: [], spread: 0, lastUpdate: 0 }
    this.reconnectAttempts[key] = 0

    switch (exchange) {
      case 'binance':
        this._connectBinance(symbol, key)
        break
      case 'coindcx':
        this._connectCoinDCX(symbol, key)
        break
      default:
        this._connectBinance(symbol, key)
    }
  }

  unsubscribe(symbol, exchange = 'binance') {
    const key = `${exchange}_${symbol}`
    if (this.connections[key]) {
      this.connections[key].close()
      delete this.connections[key]
      delete this.orderBooks[key]
    }
  }

  unsubscribeAll() {
    for (const key of Object.keys(this.connections)) {
      this.connections[key].close()
    }
    this.connections = {}
    this.orderBooks = {}
  }

  _connectBinance(symbol, key) {
    const wsUrl = `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@depth20@100ms`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log(`[OrderBook] Binance ${symbol} connected`)
        this.reconnectAttempts[key] = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          const bids = (data.bids || []).map(([price, qty]) => ({
            price: parseFloat(price),
            qty: parseFloat(qty),
            total: parseFloat(price) * parseFloat(qty),
          }))

          const asks = (data.asks || []).map(([price, qty]) => ({
            price: parseFloat(price),
            qty: parseFloat(qty),
            total: parseFloat(price) * parseFloat(qty),
          }))

          const bestBid = bids[0]?.price || 0
          const bestAsk = asks[0]?.price || 0
          const spread = bestAsk - bestBid
          const spreadPct = bestBid > 0 ? (spread / bestBid) * 100 : 0

          this.orderBooks[key] = {
            bids,
            asks,
            spread,
            spreadPct,
            bestBid,
            bestAsk,
            midPrice: (bestBid + bestAsk) / 2,
            lastUpdate: Date.now(),
            exchange: 'binance',
            symbol,
          }

          // Detect whale walls (large orders > 5x average)
          this._detectWhaleWalls(key, bids, asks)

          if (this.onUpdate) this.onUpdate(key, this.orderBooks[key])
        } catch {}
      }

      ws.onerror = () => {
        console.warn(`[OrderBook] Binance ${symbol} error`)
      }

      ws.onclose = () => {
        delete this.connections[key]
        this._reconnect(symbol, 'binance', key)
      }

      this.connections[key] = ws
    } catch (e) {
      console.warn('[OrderBook] Failed to connect:', e.message)
    }
  }

  _connectCoinDCX(symbol, key) {
    // CoinDCX uses Socket.IO — we'll poll their REST API as fallback
    this._pollCoinDCX(symbol, key)
  }

  async _pollCoinDCX(symbol, key) {
    const poll = async () => {
      if (!this.orderBooks[key]) return // Unsubscribed

      try {
        const res = await fetch(`https://api.coindcx.com/exchange/v1/books/depth?symbol=${symbol}`)
        if (res.ok) {
          const data = await res.json()
          
          const bids = (data.bids || []).slice(0, 20).map(b => ({
            price: parseFloat(b.price || b[0]),
            qty: parseFloat(b.quantity || b[1]),
            total: parseFloat(b.price || b[0]) * parseFloat(b.quantity || b[1]),
          }))

          const asks = (data.asks || []).slice(0, 20).map(a => ({
            price: parseFloat(a.price || a[0]),
            qty: parseFloat(a.quantity || a[1]),
            total: parseFloat(a.price || a[0]) * parseFloat(a.quantity || a[1]),
          }))

          const bestBid = bids[0]?.price || 0
          const bestAsk = asks[0]?.price || 0

          this.orderBooks[key] = {
            bids,
            asks,
            spread: bestAsk - bestBid,
            spreadPct: bestBid > 0 ? ((bestAsk - bestBid) / bestBid) * 100 : 0,
            bestBid,
            bestAsk,
            midPrice: (bestBid + bestAsk) / 2,
            lastUpdate: Date.now(),
            exchange: 'coindcx',
            symbol,
          }

          if (this.onUpdate) this.onUpdate(key, this.orderBooks[key])
        }
      } catch {}

      // Poll every 2s
      if (this.orderBooks[key]) {
        setTimeout(poll, 2000)
      }
    }

    poll()
  }

  _detectWhaleWalls(key, bids, asks) {
    const allOrders = [...bids, ...asks]
    const avgTotal = allOrders.reduce((s, o) => s + o.total, 0) / allOrders.length

    const walls = allOrders.filter(o => o.total > avgTotal * 5)
    if (walls.length > 0 && this.onWhaleWall) {
      this.onWhaleWall(key, walls)
    }
  }

  _reconnect(symbol, exchange, key) {
    if (this.reconnectAttempts[key] >= this.maxReconnects) return

    this.reconnectAttempts[key]++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts[key]), 30000)

    setTimeout(() => {
      if (this.orderBooks[key] !== undefined) { // Still subscribed
        this.subscribe(symbol, exchange)
      }
    }, delay)
  }

  /**
   * Get aggregated order book (merged from all exchanges)
   */
  getAggregated(symbol) {
    const keys = Object.keys(this.orderBooks).filter(k => k.includes(symbol))
    if (keys.length === 0) return null

    const allBids = []
    const allAsks = []

    for (const key of keys) {
      const book = this.orderBooks[key]
      allBids.push(...book.bids.map(b => ({ ...b, exchange: book.exchange })))
      allAsks.push(...book.asks.map(a => ({ ...a, exchange: book.exchange })))
    }

    allBids.sort((a, b) => b.price - a.price)
    allAsks.sort((a, b) => a.price - b.price)

    return {
      bids: allBids.slice(0, 25),
      asks: allAsks.slice(0, 25),
      bestBid: allBids[0]?.price || 0,
      bestAsk: allAsks[0]?.price || 0,
      spread: (allAsks[0]?.price || 0) - (allBids[0]?.price || 0),
    }
  }

  /**
   * Get order book visualization data (cumulative depth)
   */
  getDepthData(symbol) {
    const aggregated = this.getAggregated(symbol)
    if (!aggregated) return null

    let bidCumulative = 0
    const bidDepth = aggregated.bids.map(b => {
      bidCumulative += b.qty
      return { price: b.price, cumQty: bidCumulative }
    })

    let askCumulative = 0
    const askDepth = aggregated.asks.map(a => {
      askCumulative += a.qty
      return { price: a.price, cumQty: askCumulative }
    })

    return { bidDepth, askDepth, midPrice: (aggregated.bestBid + aggregated.bestAsk) / 2 }
  }

  getBook(symbol, exchange) {
    return this.orderBooks[`${exchange}_${symbol}`] || null
  }

  isConnected(symbol, exchange) {
    const key = `${exchange}_${symbol}`
    return this.connections[key]?.readyState === WebSocket.OPEN
  }
}

const orderBookWS = new OrderBookWebSocket()
export default orderBookWS
