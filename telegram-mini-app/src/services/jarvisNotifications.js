/**
 * 🔔 JARVIS SMART NOTIFICATIONS — Iron Man Style Alerts
 * ═══════════════════════════════════════════════════════════════
 * 
 * On-screen alerts styled like Iron Man's suit warnings:
 * - Glowing border animations (red=danger, gold=info, green=success)
 * - Priority-based stacking (emergency on top)
 * - Auto-dismiss timers
 * - Sound integration
 * - Hindi/English messages
 * - Action buttons
 * 
 * Uses CustomEvents so any component can trigger without imports.
 */

const QUEUE_KEY = 'jarvis_notification_queue'
let notificationStack = []
let notifId = 0

const PRIORITIES = { low: 1, normal: 2, high: 3, emergency: 4 }
const DISPLAY_TIMES = { low: 4000, normal: 6000, high: 8000, emergency: 12000 }

function init() {
  // Listen for notification events from anywhere
  window.addEventListener('jarvis-notify', (e) => {
    show(e.detail)
  })

  // Listen for specific alert types
  window.addEventListener('jarvis-gem-found', (e) => {
    show({
      title: '💎 GEM DETECTED',
      message: `${e.detail?.symbol || 'Unknown'} — new gem found!`,
      priority: 'high',
      type: 'success',
    })
  })

  window.addEventListener('jarvis-trade', (e) => {
    const d = e.detail || {}
    show({
      title: '📊 TRADE EXECUTED',
      message: `${d.action?.toUpperCase() || 'TRADE'} ${d.symbol || ''} @ ${d.price || ''}`,
      priority: 'high',
      type: 'info',
    })
  })

  window.addEventListener('jarvis-emergency', (e) => {
    show({
      title: '🚨 EMERGENCY',
      message: e.detail?.message || 'Emergency protocol activated',
      priority: 'emergency',
      type: 'danger',
    })
  })

  window.addEventListener('jarvis-market-alert', (e) => {
    show({
      title: '⚡ MARKET ALERT',
      message: e.detail?.text || 'Market movement detected',
      priority: 'normal',
      type: 'warning',
    })
  })

  console.log('[Notifications] 🔔 Smart notifications initialized')
}

/**
 * Show a notification
 * @param {Object} opts - { title, message, priority, type, action, duration }
 * priority: 'low' | 'normal' | 'high' | 'emergency'
 * type: 'info' | 'success' | 'warning' | 'danger'
 */
function show(opts = {}) {
  const notification = {
    id: ++notifId,
    title: opts.title || 'JARVIS',
    message: opts.message || '',
    priority: opts.priority || 'normal',
    type: opts.type || 'info',
    action: opts.action || null, // { label, callback } or { label, navigate }
    timestamp: Date.now(),
    duration: opts.duration || DISPLAY_TIMES[opts.priority] || 6000,
    dismissed: false,
  }

  notificationStack.push(notification)

  // Sort by priority (emergency first)
  notificationStack.sort((a, b) => PRIORITIES[b.priority] - PRIORITIES[a.priority])

  // Keep max 5 active
  if (notificationStack.length > 5) {
    notificationStack = notificationStack.slice(0, 5)
  }

  // Dispatch update to UI
  _dispatchUpdate()

  // Auto-dismiss
  setTimeout(() => {
    dismiss(notification.id)
  }, notification.duration)

  return notification.id
}

function dismiss(id) {
  notificationStack = notificationStack.filter(n => n.id !== id)
  _dispatchUpdate()
}

function dismissAll() {
  notificationStack = []
  _dispatchUpdate()
}

function getActive() {
  return [...notificationStack]
}

function _dispatchUpdate() {
  window.dispatchEvent(new CustomEvent('jarvis-notification-update', {
    detail: { notifications: [...notificationStack] }
  }))
}

const jarvisNotifications = { init, show, dismiss, dismissAll, getActive }
export default jarvisNotifications
export { show as showNotification, dismiss, dismissAll, getActive }
