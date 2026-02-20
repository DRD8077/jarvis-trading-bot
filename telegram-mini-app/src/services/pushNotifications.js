/**
 * 🔔 JARVIS Push Notification Engine
 * ════════════════════════════════════
 * - Firebase Cloud Messaging for native push (when available)
 * - Web Push API fallback for browser/PWA
 * - In-app notification manager
 * - Price alert triggers
 * - Whale alert notifications
 * - Signal notifications
 * - Persistent notification preferences in localStorage
 */

const VAPID_PUBLIC_KEY = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkOs-qy02tEMeHrlGG1e9tzQ4E4gHV-Lk5yA3VifIo'

class PushNotificationEngine {
  constructor() {
    this.permission = 'default'
    this.subscription = null
    this.listeners = new Map()
    this.alerts = JSON.parse(localStorage.getItem('jarvis_price_alerts') || '[]')
    this.preferences = JSON.parse(localStorage.getItem('jarvis_notif_prefs') || JSON.stringify({
      priceAlerts: true,
      whaleAlerts: true,
      signals: true,
      tradeUpdates: true,
      news: false,
      sound: true,
      vibrate: true
    }))
    this._init()
  }

  async _init() {
    if (typeof window === 'undefined') return
    this.permission = Notification?.permission || 'default'
    
    // Register service worker for push
    if ('serviceWorker' in navigator) {
      try {
        const reg = await navigator.serviceWorker.ready
        this.swRegistration = reg
      } catch {}
    }
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if (!('Notification' in window)) {
      return { granted: false, reason: 'Notifications not supported' }
    }
    
    try {
      const result = await Notification.requestPermission()
      this.permission = result
      if (result === 'granted') {
        await this._subscribePush()
        return { granted: true }
      }
      return { granted: false, reason: result }
    } catch (e) {
      return { granted: false, reason: e.message }
    }
  }

  /**
   * Subscribe to Web Push
   */
  async _subscribePush() {
    if (!this.swRegistration) return null
    try {
      const sub = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this._urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      })
      this.subscription = sub
      // Send subscription to server
      await this._sendSubscriptionToServer(sub)
      return sub
    } catch (e) {
      console.warn('[Push] Subscribe failed:', e.message)
      return null
    }
  }

  async _sendSubscriptionToServer(sub) {
    try {
      const user = JSON.parse(localStorage.getItem('jarvis_gmail_user') || '{}')
      await fetch('/api/miniapp/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscription: sub.toJSON(),
          user_id: user?.id || '0',
          preferences: this.preferences
        })
      })
    } catch {}
  }

  /**
   * Show local notification (works without FCM)
   */
  async showNotification(title, body, options = {}) {
    if (this.permission !== 'granted') {
      // Fallback: in-app toast
      this._emitInApp(title, body, options)
      return
    }

    const notifOptions = {
      body,
      icon: '/miniapp/icons/icon-192.png',
      badge: '/miniapp/icons/icon-72.png',
      tag: options.tag || 'jarvis-' + Date.now(),
      vibrate: this.preferences.vibrate ? [200, 100, 200] : undefined,
      silent: !this.preferences.sound,
      data: options.data || {},
      actions: options.actions || [],
      requireInteraction: options.persistent || false,
      ...options
    }

    try {
      if (this.swRegistration) {
        await this.swRegistration.showNotification(title, notifOptions)
      } else {
        new Notification(title, notifOptions)
      }
    } catch {
      this._emitInApp(title, body, options)
    }
  }

  // ═══ Price Alerts ═══

  addPriceAlert(symbol, targetPrice, direction = 'above', label = '') {
    const alert = {
      id: Date.now().toString(36),
      symbol,
      targetPrice: parseFloat(targetPrice),
      direction, // 'above' | 'below'
      label: label || `${symbol} ${direction} ₹${targetPrice}`,
      active: true,
      createdAt: new Date().toISOString(),
      triggered: false
    }
    this.alerts.push(alert)
    this._saveAlerts()
    return alert
  }

  removePriceAlert(alertId) {
    this.alerts = this.alerts.filter(a => a.id !== alertId)
    this._saveAlerts()
  }

  getActiveAlerts() {
    return this.alerts.filter(a => a.active && !a.triggered)
  }

  /**
   * Check prices against alerts (called by auto-refresh engine)
   */
  checkPriceAlerts(priceMap) {
    if (!this.preferences.priceAlerts) return
    
    for (const alert of this.alerts) {
      if (!alert.active || alert.triggered) continue
      
      const currentPrice = priceMap[alert.symbol]
      if (!currentPrice) continue

      const triggered = alert.direction === 'above'
        ? currentPrice >= alert.targetPrice
        : currentPrice <= alert.targetPrice

      if (triggered) {
        alert.triggered = true
        alert.triggeredAt = new Date().toISOString()
        alert.triggeredPrice = currentPrice
        
        this.showNotification(
          `🎯 Price Alert: ${alert.symbol}`,
          `${alert.symbol} is now ₹${currentPrice.toLocaleString('en-IN')} (target: ${alert.direction} ₹${alert.targetPrice.toLocaleString('en-IN')})`,
          { tag: `price-${alert.id}`, data: { type: 'price_alert', alert } }
        )
        
        // Vibrate for urgency
        if (navigator.vibrate && this.preferences.vibrate) {
          navigator.vibrate([300, 100, 300, 100, 300])
        }
      }
    }
    this._saveAlerts()
  }

  // ═══ Whale Alert ═══

  notifyWhaleAlert(whale) {
    if (!this.preferences.whaleAlerts) return
    this.showNotification(
      `🐋 Whale Alert: ${whale.token || 'Unknown'}`,
      `${whale.type === 'buy' ? '🟢 BUY' : '🔴 SELL'} — $${(whale.amount || 0).toLocaleString()} on ${whale.exchange || 'DEX'}`,
      { tag: `whale-${Date.now()}`, data: { type: 'whale', whale } }
    )
  }

  // ═══ Signal Notification ═══

  notifySignal(signal) {
    if (!this.preferences.signals) return
    this.showNotification(
      `📊 ${signal.action?.toUpperCase() || 'SIGNAL'}: ${signal.symbol}`,
      `${signal.summary || signal.reason || 'New trading signal'} — Confidence: ${signal.confidence || 'N/A'}%`,
      { tag: `signal-${signal.symbol}-${Date.now()}`, data: { type: 'signal', signal } }
    )
  }

  // ═══ Preferences ═══

  updatePreferences(newPrefs) {
    this.preferences = { ...this.preferences, ...newPrefs }
    localStorage.setItem('jarvis_notif_prefs', JSON.stringify(this.preferences))
    if (this.subscription) this._sendSubscriptionToServer(this.subscription)
  }

  getPreferences() {
    return { ...this.preferences }
  }

  // ═══ In-App Events ═══

  onNotification(callback) {
    const id = Date.now()
    this.listeners.set(id, callback)
    return () => this.listeners.delete(id)
  }

  _emitInApp(title, body, options = {}) {
    for (const cb of this.listeners.values()) {
      try { cb({ title, body, ...options }) } catch {}
    }
  }

  // ═══ Utilities ═══

  _saveAlerts() {
    localStorage.setItem('jarvis_price_alerts', JSON.stringify(this.alerts))
  }

  _urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawData = atob(base64)
    return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)))
  }

  getStatus() {
    return {
      permission: this.permission,
      subscribed: !!this.subscription,
      activeAlerts: this.getActiveAlerts().length,
      totalAlerts: this.alerts.length,
      preferences: this.preferences
    }
  }
}

const pushNotifications = new PushNotificationEngine()
export default pushNotifications
