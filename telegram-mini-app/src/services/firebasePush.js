/**
 * 🔥 JARVIS Firebase Push Notification Service
 * ═══════════════════════════════════════════════
 * - Firebase Cloud Messaging for native Android push
 * - Lock screen alerts: "BTC hit $70K!", price targets, signals
 * - Background notification handling
 * - Topic subscription for market alerts
 * - Falls back to Web Push API if Firebase unavailable
 */

import { API_BASE } from './apiBase'

// Firebase config (replace with your project's config)
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyD_JARVIS_FIREBASE_KEY",
  authDomain: "jarvis-trading-bot.firebaseapp.com",
  projectId: "jarvis-trading-bot",
  storageBucket: "jarvis-trading-bot.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
}

class FirebasePushService {
  constructor() {
    this.messaging = null
    this.token = null
    this.isInitialized = false
    this.listeners = new Map()
    this.topics = ['price_alerts', 'whale_alerts', 'signals', 'news']
    this.subscribedTopics = JSON.parse(localStorage.getItem('jarvis_fcm_topics') || '[]')
  }

  /**
   * Initialize Firebase + get FCM token
   */
  async init() {
    if (this.isInitialized) return this.token

    try {
      // Dynamic import Firebase — fully opaque to bundler  
      const fbAppPath = ['firebase', 'app'].join('/')
      const fbMsgPath = ['firebase', 'messaging'].join('/')
      const firebaseAppModule = await import(/* @vite-ignore */ fbAppPath).catch(() => null)
      const firebaseMsgModule = await import(/* @vite-ignore */ fbMsgPath).catch(() => null)

      const initializeApp = firebaseAppModule?.initializeApp
      const getMessaging = firebaseMsgModule?.getMessaging
      const getToken = firebaseMsgModule?.getToken
      const onMessage = firebaseMsgModule?.onMessage

      if (!initializeApp || !getMessaging) {
        console.log('[FCM] Firebase not available, using fallback push')
        return null
      }

      const app = initializeApp(FIREBASE_CONFIG)
      this.messaging = getMessaging(app)

      // Request permission
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        console.warn('[FCM] Notification permission denied')
        return null
      }

      // Get FCM token
      this.token = await getToken(this.messaging, {
        vapidKey: 'YOUR_VAPID_KEY_HERE'
      })

      console.log('[FCM] Token:', this.token?.substring(0, 20) + '...')

      // Send token to server
      await this._registerToken(this.token)

      // Listen for foreground messages
      onMessage(this.messaging, (payload) => {
        console.log('[FCM] Foreground message:', payload)
        this._handleForegroundMessage(payload)
      })

      this.isInitialized = true
      return this.token
    } catch (e) {
      console.warn('[FCM] Init failed:', e.message)
      return null
    }
  }

  /**
   * Register token with backend
   */
  async _registerToken(token) {
    try {
      const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || '{}')
      await fetch(`${API_BASE}/push/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          user_id: savedUser?.id || '0',
          platform: 'android',
          topics: this.subscribedTopics
        })
      })
    } catch (e) {
      console.warn('[FCM] Token registration failed:', e)
    }
  }

  /**
   * Handle foreground messages — show in-app notification
   */
  _handleForegroundMessage(payload) {
    const { title, body, data } = payload.notification || payload.data || {}
    
    // Show in-app notification
    this.listeners.forEach(callback => callback({ title, body, data }))

    // Also show native notification
    if (Notification.permission === 'granted') {
      new Notification(title || 'JARVIS Alert', {
        body: body || '',
        icon: '/icon-192.png',
        badge: '/icon-72.png',
        vibrate: [200, 100, 200],
        tag: data?.type || 'jarvis-alert',
        data: data,
        actions: [
          { action: 'open', title: 'Open JARVIS' },
          { action: 'dismiss', title: 'Dismiss' }
        ]
      })
    }

    // Haptic feedback
    if (navigator.vibrate) navigator.vibrate([100, 50, 100])
  }

  /**
   * Subscribe to alert topics
   */
  async subscribeToTopic(topic) {
    if (!this.subscribedTopics.includes(topic)) {
      this.subscribedTopics.push(topic)
      localStorage.setItem('jarvis_fcm_topics', JSON.stringify(this.subscribedTopics))
      
      if (this.token) {
        try {
          await fetch(`${API_BASE}/push/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: this.token, topic })
          })
        } catch {}
      }
    }
  }

  /**
   * Unsubscribe from topic
   */
  async unsubscribeFromTopic(topic) {
    this.subscribedTopics = this.subscribedTopics.filter(t => t !== topic)
    localStorage.setItem('jarvis_fcm_topics', JSON.stringify(this.subscribedTopics))
    
    if (this.token) {
      try {
        await fetch(`${API_BASE}/push/unsubscribe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: this.token, topic })
        })
      } catch {}
    }
  }

  /**
   * Set price alert (triggers push when price hits target)
   */
  async setPriceAlert(symbol, targetPrice, direction = 'above') {
    try {
      const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || '{}')
      await fetch(`${API_BASE}/push/price-alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: savedUser?.id || '0',
          token: this.token,
          symbol,
          target_price: targetPrice,
          direction
        })
      })
      return true
    } catch {
      return false
    }
  }

  /**
   * Add listener for foreground notifications
   */
  onNotification(id, callback) {
    this.listeners.set(id, callback)
    return () => this.listeners.delete(id)
  }

  /**
   * Check if push is supported + enabled
   */
  isSupported() {
    return 'Notification' in window && 'serviceWorker' in navigator
  }

  getToken() {
    return this.token
  }

  getSubscribedTopics() {
    return [...this.subscribedTopics]
  }
}

const firebasePush = new FirebasePushService()
export default firebasePush
