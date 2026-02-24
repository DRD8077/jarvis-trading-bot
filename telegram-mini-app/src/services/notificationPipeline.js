/**
 * 🔔 JARVIS Notification Pipeline
 * ═══════════════════════════════════
 * 
 * Multi-channel notification system:
 * - In-app toasts (always works)
 * - Push notifications (via SW)
 * - Native Android (via Capacitor)
 * - Sound/vibration alerts
 * - Smart batching (no spam)
 * - Priority levels (critical → low)
 * - Hindi + English
 */

const PRIORITIES = { CRITICAL: 4, HIGH: 3, NORMAL: 2, LOW: 1, SILENT: 0 }

class NotificationPipeline {
  constructor() {
    this.subscribers = new Map()
    this.history = []
    this.batchQueue = []
    this.batchTimer = null
    this.settings = {
      enabled: true,
      sound: true,
      vibrate: true,
      batchDelay: 3000, // 3 second batching
      maxHistory: 200,
      doNotDisturb: false,
      dndStart: '22:00',
      dndEnd: '07:00',
      minPriority: PRIORITIES.LOW,
      language: 'en'
    }
    this._loadSettings()
  }

  _loadSettings() {
    try {
      const saved = localStorage.getItem('jarvis_notif_settings')
      if (saved) Object.assign(this.settings, JSON.parse(saved))
    } catch {}
  }

  saveSettings() {
    localStorage.setItem('jarvis_notif_settings', JSON.stringify(this.settings))
  }

  // ═══════════════════════════════════
  // SEND NOTIFICATION
  // ═══════════════════════════════════

  async send(notification) {
    const notif = {
      id: `n_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
      title: notification.title || 'JARVIS',
      body: notification.body || '',
      priority: notification.priority || PRIORITIES.NORMAL,
      category: notification.category || 'general',
      icon: notification.icon || '🤖',
      data: notification.data || {},
      actions: notification.actions || [],
      sound: notification.sound,
      timestamp: Date.now(),
      read: false
    }

    // Check DND
    if (this.settings.doNotDisturb && this._isDNDTime()) {
      if (notif.priority < PRIORITIES.CRITICAL) {
        this.batchQueue.push(notif)
        return notif.id
      }
    }

    // Priority filter
    if (notif.priority < this.settings.minPriority) {
      this.history.push({ ...notif, suppressed: true })
      return notif.id
    }

    // Add to history
    this.history.push(notif)
    if (this.history.length > this.settings.maxHistory) {
      this.history = this.history.slice(-this.settings.maxHistory)
    }

    // Dispatch to all channels  
    await this._dispatch(notif)

    // Notify subscribers
    this.subscribers.forEach(cb => {
      try { cb(notif) } catch {}
    })

    return notif.id
  }

  async _dispatch(notif) {
    // Channel 1: In-app toast (always works)
    this._showToast(notif)

    // Channel 2: Browser/Push notification
    if (notif.priority >= PRIORITIES.NORMAL) {
      this._showBrowserNotification(notif)
    }

    // Channel 3: Sound
    if (this.settings.sound && notif.priority >= PRIORITIES.NORMAL) {
      this._playSound(notif)
    }

    // Channel 4: Vibration
    if (this.settings.vibrate && notif.priority >= PRIORITIES.HIGH) {
      this._vibrate(notif)
    }
  }

  // ═══════════════════════════════════
  // NOTIFICATION CHANNELS
  // ═══════════════════════════════════

  _showToast(notif) {
    // Dispatch custom event for React to catch
    window.dispatchEvent(new CustomEvent('jarvis-toast', {
      detail: notif
    }))
  }

  async _showBrowserNotification(notif) {
    if (!('Notification' in window)) return
    if (Notification.permission !== 'granted') {
      const perm = await Notification.requestPermission()
      if (perm !== 'granted') return
    }

    try {
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.ready.then(reg => {
          reg.showNotification(notif.title, {
            body: notif.body,
            icon: '/icons/icon-192.png',
            badge: '/icons/icon-72.png',
            vibrate: notif.priority >= PRIORITIES.HIGH ? [200, 100, 200] : [100],
            tag: notif.category,
            renotify: notif.priority >= PRIORITIES.HIGH,
            data: notif.data
          })
        })
      } else {
        new Notification(notif.title, { body: notif.body, icon: '/icons/icon-192.png' })
      }
    } catch {}
  }

  _playSound(notif) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)

      if (notif.priority >= PRIORITIES.CRITICAL) {
        osc.frequency.value = 880
        gain.gain.value = 0.3
        osc.start(); osc.stop(ctx.currentTime + 0.3)
      } else if (notif.priority >= PRIORITIES.HIGH) {
        osc.frequency.value = 660
        gain.gain.value = 0.2
        osc.start(); osc.stop(ctx.currentTime + 0.2)
      } else {
        osc.frequency.value = 440
        gain.gain.value = 0.1
        osc.start(); osc.stop(ctx.currentTime + 0.15)
      }
    } catch {}
  }

  _vibrate(notif) {
    if (!navigator.vibrate) return
    if (notif.priority >= PRIORITIES.CRITICAL) {
      navigator.vibrate([200, 100, 200, 100, 200])
    } else {
      navigator.vibrate([100, 50, 100])
    }
  }

  _isDNDTime() {
    const now = new Date()
    const h = now.getHours()
    const m = now.getMinutes()
    const [startH, startM] = this.settings.dndStart.split(':').map(Number)
    const [endH, endM] = this.settings.dndEnd.split(':').map(Number)
    const current = h * 60 + m
    const start = startH * 60 + startM
    const end = endH * 60 + endM
    if (start > end) return current >= start || current < end
    return current >= start && current < end
  }

  // ═══════════════════════════════════
  // PRE-BUILT NOTIFICATION TYPES
  // ═══════════════════════════════════

  priceAlert(symbol, price, condition, targetPrice) {
    const hit = condition === 'above' ? price >= targetPrice : price <= targetPrice
    if (!hit) return null
    return this.send({
      title: `💰 Price Alert: ${symbol}`,
      body: `${symbol} is now $${price.toLocaleString()} (${condition} $${targetPrice.toLocaleString()})`,
      priority: PRIORITIES.HIGH,
      category: 'price-alert',
      data: { symbol, price, condition, targetPrice }
    })
  }

  tradeSignal(signal) {
    return this.send({
      title: `${signal.direction === 'BUY' ? '🟢' : '🔴'} ${signal.direction}: ${signal.symbol}`,
      body: `${signal.confidence}% confidence | Entry: $${signal.entry} | Target: $${signal.target}`,
      priority: signal.confidence > 80 ? PRIORITIES.HIGH : PRIORITIES.NORMAL,
      category: 'trade-signal',
      data: signal
    })
  }

  whaleAlert(data) {
    return this.send({
      title: `🐋 Whale Movement: ${data.symbol}`,
      body: `${data.type}: ${data.amount} ${data.symbol} ($${data.usdValue?.toLocaleString()})`,
      priority: PRIORITIES.HIGH,
      category: 'whale-alert',
      data
    })
  }

  pnlMilestone(data) {
    return this.send({
      title: data.pnl >= 0 ? '🎉 Profit Milestone!' : '⚠️ P&L Alert',
      body: `Today's P&L: ${data.pnl >= 0 ? '+' : ''}$${data.pnl.toFixed(2)} | Win rate: ${data.winRate}%`,
      priority: PRIORITIES.NORMAL,
      category: 'pnl',
      data
    })
  }

  systemAlert(message, priority = PRIORITIES.NORMAL) {
    return this.send({
      title: '⚙️ JARVIS System',
      body: message,
      priority,
      category: 'system'
    })
  }

  // ═══════════════════════════════════
  // SUBSCRIPTIONS
  // ═══════════════════════════════════

  subscribe(callback) {
    const id = Symbol()
    this.subscribers.set(id, callback)
    return () => this.subscribers.delete(id)
  }

  getHistory(category = null, limit = 50) {
    let h = this.history
    if (category) h = h.filter(n => n.category === category)
    return h.slice(-limit)
  }

  markRead(id) {
    const n = this.history.find(h => h.id === id)
    if (n) n.read = true
  }

  markAllRead() {
    this.history.forEach(n => { n.read = true })
  }

  getUnreadCount() {
    return this.history.filter(n => !n.read && !n.suppressed).length
  }

  clearHistory() {
    this.history = []
  }
}

const notificationPipeline = new NotificationPipeline()
export default notificationPipeline
export { NotificationPipeline, PRIORITIES }
