/**
 * 📊 JARVIS Portfolio Sync Engine
 * ═══════════════════════════════════
 * 
 * Syncs portfolio from multiple sources:
 * - CoinDCX API (Indian crypto exchange)
 * - Binance API (global)
 * - Manual entry
 * - CSV import
 * All synced to local SQLite DB. Works 100% offline.
 */

import jarvisDB from './jarvisDB'
import encryptedVault from './encryptedVault'

class PortfolioSyncEngine {
  constructor() {
    this.syncInterval = null
    this.lastSync = {}
    this.exchanges = {
      coindcx: { name: 'CoinDCX', enabled: false, baseUrl: 'https://api.coindcx.com' },
      binance: { name: 'Binance', enabled: false, baseUrl: 'https://api.binance.com' },
      manual: { name: 'Manual', enabled: true }
    }
  }

  // ═══════════════════════════════════
  // EXCHANGE CONNECTIONS
  // ═══════════════════════════════════

  async connectExchange(exchange, apiKey, apiSecret) {
    await encryptedVault.storeExchangeCredentials(exchange, { apiKey, apiSecret })
    this.exchanges[exchange].enabled = true
    console.log(`[PortfolioSync] Connected to ${exchange}`)
    return true
  }

  async disconnectExchange(exchange) {
    await encryptedVault.remove(`exchange_${exchange}`)
    this.exchanges[exchange].enabled = false
  }

  async getConnectedExchanges() {
    const result = []
    for (const [id, ex] of Object.entries(this.exchanges)) {
      const creds = await encryptedVault.getExchangeCredentials(id)
      result.push({ id, ...ex, hasCredentials: !!creds })
    }
    return result
  }

  // ═══════════════════════════════════
  // SYNC FROM EXCHANGES
  // ═══════════════════════════════════

  async syncAll() {
    const results = {}

    for (const [id, ex] of Object.entries(this.exchanges)) {
      if (!ex.enabled) continue
      try {
        if (id === 'binance') results.binance = await this._syncBinance()
        else if (id === 'coindcx') results.coindcx = await this._syncCoinDCX()
      } catch (e) {
        results[id] = { error: e.message }
      }
    }

    // Always sync from local portfolio
    results.local = await this._getLocalSummary()
    this.lastSync.all = Date.now()
    return results
  }

  async _syncBinance() {
    const creds = await encryptedVault.getExchangeCredentials('binance')
    if (!creds) return { error: 'Not connected' }

    try {
      // Binance public API — no auth needed for SOME endpoints
      const res = await fetch('https://api.binance.com/api/v3/account', {
        headers: { 'X-MBX-APIKEY': creds.apiKey }
      })
      if (!res.ok) throw new Error(`Binance API ${res.status}`)
      const data = await res.json()

      let synced = 0
      for (const balance of (data.balances || [])) {
        const qty = parseFloat(balance.free) + parseFloat(balance.locked)
        if (qty > 0) {
          jarvisDB.updateHolding(`${balance.asset}/USDT`, qty, 0, 'binance', 'crypto')
          synced++
        }
      }
      this.lastSync.binance = Date.now()
      return { synced, timestamp: Date.now() }
    } catch (e) {
      return { error: e.message }
    }
  }

  async _syncCoinDCX() {
    const creds = await encryptedVault.getExchangeCredentials('coindcx')
    if (!creds) return { error: 'Not connected' }

    try {
      const res = await fetch('https://api.coindcx.com/exchange/v1/users/balances', {
        method: 'POST',
        headers: { 'X-AUTH-APIKEY': creds.apiKey }
      })
      if (!res.ok) throw new Error(`CoinDCX API ${res.status}`)
      const balances = await res.json()

      let synced = 0
      for (const b of (balances || [])) {
        const qty = parseFloat(b.balance)
        if (qty > 0) {
          jarvisDB.updateHolding(b.currency, qty, 0, 'coindcx', 'crypto')
          synced++
        }
      }
      this.lastSync.coindcx = Date.now()
      return { synced, timestamp: Date.now() }
    } catch (e) {
      return { error: e.message }
    }
  }

  async _getLocalSummary() {
    const portfolio = jarvisDB.getPortfolio()
    const value = jarvisDB.getPortfolioValue()
    return { holdings: portfolio.length, value }
  }

  // ═══════════════════════════════════
  // MANUAL OPERATIONS
  // ═══════════════════════════════════

  addManualHolding(symbol, quantity, avgPrice, type = 'crypto') {
    jarvisDB.updateHolding(symbol.toUpperCase(), quantity, avgPrice, 'manual', type)
    return true
  }

  removeHolding(symbol) {
    jarvisDB.run(`DELETE FROM portfolio WHERE symbol = ?`, [symbol])
    return true
  }

  // ═══════════════════════════════════
  // CSV IMPORT/EXPORT
  // ═══════════════════════════════════

  importCSV(csvText) {
    const lines = csvText.trim().split('\n')
    if (lines.length < 2) return { error: 'Empty CSV' }

    const headers = lines[0].toLowerCase().split(',').map(h => h.trim())
    const symbolIdx = headers.findIndex(h => h.includes('symbol') || h.includes('coin'))
    const qtyIdx = headers.findIndex(h => h.includes('quantity') || h.includes('qty') || h.includes('amount'))
    const priceIdx = headers.findIndex(h => h.includes('price') || h.includes('avg'))

    if (symbolIdx === -1 || qtyIdx === -1) return { error: 'CSV must have symbol and quantity columns' }

    let imported = 0
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(',').map(c => c.trim().replace(/"/g, ''))
      if (!cols[symbolIdx]) continue
      const symbol = cols[symbolIdx].toUpperCase()
      const qty = parseFloat(cols[qtyIdx]) || 0
      const price = priceIdx >= 0 ? (parseFloat(cols[priceIdx]) || 0) : 0
      if (qty > 0) {
        jarvisDB.updateHolding(symbol, qty, price, 'csv-import', 'crypto')
        imported++
      }
    }

    return { imported, total: lines.length - 1 }
  }

  exportCSV() {
    return jarvisDB.exportCSV('portfolio')
  }

  // ═══════════════════════════════════
  // AUTO-SYNC
  // ═══════════════════════════════════

  startAutoSync(interval = 300000) { // 5 min default
    if (this.syncInterval) return
    this.syncInterval = setInterval(() => this.syncAll(), interval)
    console.log('[PortfolioSync] Auto-sync started')
  }

  stopAutoSync() {
    if (this.syncInterval) clearInterval(this.syncInterval)
    this.syncInterval = null
  }

  getSyncStatus() {
    return {
      lastSync: this.lastSync,
      exchanges: Object.entries(this.exchanges).map(([id, ex]) => ({ id, ...ex })),
      autoSyncActive: !!this.syncInterval
    }
  }
}

const portfolioSync = new PortfolioSyncEngine()
export default portfolioSync
export { PortfolioSyncEngine }
