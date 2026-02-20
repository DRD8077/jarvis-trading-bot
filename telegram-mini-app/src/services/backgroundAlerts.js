/**
 * 🔔 JARVIS Background Price Alert Engine
 * ═════════════════════════════════════════
 * - Runs via Web Worker / Visibility API
 * - Checks prices even when app is backgrounded
 * - Triggers push notifications on alert conditions
 * - Multiple alert types: above, below, % change
 * - Persists alerts in localStorage
 * - Connects to push notification engine
 */

import { getApiBase } from './apiBase'

class BackgroundAlertEngine {
  constructor() {
    this.alerts = this._loadAlerts()
    this.worker = null
    this.checkInterval = null
    this.isRunning = false
    this.lastPrices = {}
    this.onAlertTriggered = null
  }

  _loadAlerts() {
    try {
      return JSON.parse(localStorage.getItem('jarvis_price_alerts') || '[]')
    } catch { return [] }
  }

  _saveAlerts() {
    localStorage.setItem('jarvis_price_alerts', JSON.stringify(this.alerts))
  }

  /**
   * Add a price alert
   * @param {string} symbol - e.g., 'BTCUSDT'
   * @param {string} condition - 'above' | 'below' | 'pct_change'
   * @param {number} value - target price or % change
   * @param {object} opts - { repeat: bool, note: string }
   */
  addAlert(symbol, condition, value, opts = {}) {
    const alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      symbol: symbol.toUpperCase(),
      condition,
      value: parseFloat(value),
      repeat: opts.repeat || false,
      note: opts.note || '',
      createdAt: Date.now(),
      triggered: false,
      triggeredAt: null,
      basePrice: this.lastPrices[symbol.toUpperCase()] || null,
    }

    this.alerts.push(alert)
    this._saveAlerts()
    
    if (!this.isRunning) this.start()
    
    return alert
  }

  removeAlert(alertId) {
    this.alerts = this.alerts.filter(a => a.id !== alertId)
    this._saveAlerts()
  }

  getAlerts(symbol = null) {
    if (symbol) return this.alerts.filter(a => a.symbol === symbol.toUpperCase())
    return [...this.alerts]
  }

  getActiveAlerts() {
    return this.alerts.filter(a => !a.triggered || a.repeat)
  }

  /**
   * Start background checking
   */
  start(intervalMs = 15000) {
    if (this.isRunning) return
    this.isRunning = true

    // Regular interval check
    this.checkInterval = setInterval(() => this._checkAlerts(), intervalMs)

    // Also check on visibility change (when user returns to app)
    document.addEventListener('visibilitychange', this._onVisibilityChange)

    // Immediate first check
    this._checkAlerts()

    console.log('[BackgroundAlerts] Started with', this.alerts.length, 'alerts')
  }

  stop() {
    this.isRunning = false
    if (this.checkInterval) clearInterval(this.checkInterval)
    document.removeEventListener('visibilitychange', this._onVisibilityChange)
  }

  _onVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      // Check immediately when app becomes visible
      this._checkAlerts()
    }
  }

  async _checkAlerts() {
    const activeAlerts = this.getActiveAlerts()
    if (activeAlerts.length === 0) return

    // Get unique symbols
    const symbols = [...new Set(activeAlerts.map(a => a.symbol))]

    try {
      // Fetch current prices
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/miniapp/ticker`)
      if (!res.ok) return

      const data = await res.json()
      const prices = {}

      // Parse ticker data
      if (data.data) {
        if (Array.isArray(data.data)) {
          for (const item of data.data) {
            const sym = (item.symbol || item.s || '').toUpperCase()
            prices[sym] = parseFloat(item.price || item.c || item.last || 0)
          }
        } else if (typeof data.data === 'object') {
          for (const [key, val] of Object.entries(data.data)) {
            prices[key.toUpperCase()] = parseFloat(val?.price || val?.c || val || 0)
          }
        }
      }

      // Also try BTC/ETH specific
      if (!prices['BTCUSDT'] && data.data?.btc) {
        prices['BTCUSDT'] = parseFloat(data.data.btc)
      }
      if (!prices['ETHUSDT'] && data.data?.eth) {
        prices['ETHUSDT'] = parseFloat(data.data.eth)
      }

      this.lastPrices = { ...this.lastPrices, ...prices }

      // Check each alert
      for (const alert of activeAlerts) {
        const currentPrice = prices[alert.symbol]
        if (!currentPrice) continue

        let triggered = false
        let message = ''

        switch (alert.condition) {
          case 'above':
            if (currentPrice >= alert.value) {
              triggered = true
              message = `🚀 ${alert.symbol} is above $${alert.value.toLocaleString()} — Now: $${currentPrice.toLocaleString()}`
            }
            break

          case 'below':
            if (currentPrice <= alert.value) {
              triggered = true
              message = `📉 ${alert.symbol} dropped below $${alert.value.toLocaleString()} — Now: $${currentPrice.toLocaleString()}`
            }
            break

          case 'pct_change':
            if (alert.basePrice) {
              const pctChange = ((currentPrice - alert.basePrice) / alert.basePrice) * 100
              if (Math.abs(pctChange) >= Math.abs(alert.value)) {
                triggered = true
                message = `📊 ${alert.symbol} moved ${pctChange > 0 ? '+' : ''}${pctChange.toFixed(2)}% — Now: $${currentPrice.toLocaleString()}`
              }
            }
            break
        }

        if (triggered && !alert.triggered) {
          alert.triggered = true
          alert.triggeredAt = Date.now()

          if (alert.repeat) {
            // Reset for repeat alerts
            alert.triggered = false
            alert.basePrice = currentPrice
          }

          this._saveAlerts()

          // Show notification
          this._notify(alert, message)

          if (this.onAlertTriggered) {
            this.onAlertTriggered(alert, message, currentPrice)
          }
        }
      }
    } catch (e) {
      // Silent fail - will retry next interval
    }
  }

  _notify(alert, message) {
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('JARVIS Price Alert', {
        body: message,
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        tag: alert.id,
        vibrate: [200, 100, 200],
        data: { symbol: alert.symbol, alertId: alert.id },
      })
    }

    // In-app toast
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('jarvis-alert', { detail: { alert, message } })
      window.dispatchEvent(event)
    }
  }

  /**
   * Quick alert helpers
   */
  alertAbove(symbol, price, note = '') {
    return this.addAlert(symbol, 'above', price, { note })
  }

  alertBelow(symbol, price, note = '') {
    return this.addAlert(symbol, 'below', price, { note })
  }

  alertOnChange(symbol, pctChange, note = '') {
    return this.addAlert(symbol, 'pct_change', pctChange, { repeat: true, note })
  }

  /**
   * Get current price for a symbol
   */
  getLastPrice(symbol) {
    return this.lastPrices[symbol?.toUpperCase()] || null
  }
}

const backgroundAlerts = new BackgroundAlertEngine()
export default backgroundAlerts
