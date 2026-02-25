/**
 * 📱 JARVIS Personal Assistant Mode — Android PA Engine
 * ═══════════════════════════════════════════════════════
 * 
 * Personal Assistant capabilities for Android:
 * - WhatsApp message handling
 * - Call management (answer/reject/make calls)
 * - Video call avatar (JARVIS responds on behalf)
 * - Contact access
 * - Notification management
 * - SMS handling
 * - Calendar/reminders
 * 
 * Uses Capacitor native plugins on Android,
 * graceful web fallbacks on desktop/browser.
 */

class JarvisPA {
  constructor() {
    this.isAndroid = typeof Capacitor !== 'undefined' && Capacitor.getPlatform() === 'android'
    this.isDesktop = !!window.jarvisDesktop
    this.isCapacitor = typeof Capacitor !== 'undefined'
    this.contacts = []
    this.notifications = []
    this.callHistory = []
    this.paActive = false
    this.onIncomingCall = null
    this.onIncomingMessage = null
    this.onNotification = null
  }

  /**
   * Initialize PA mode
   */
  async init(options = {}) {
    this.onIncomingCall = options.onIncomingCall || null
    this.onIncomingMessage = options.onIncomingMessage || null
    this.onNotification = options.onNotification || null

    if (this.isAndroid) {
      await this._initAndroidPA()
    }

    console.log('[JarvisPA] Personal Assistant initialized', {
      platform: this.isAndroid ? 'Android' : this.isDesktop ? 'Desktop' : 'Web',
      capabilities: this.getCapabilities()
    })

    return true
  }

  /**
   * Initialize Android-specific PA features
   */
  async _initAndroidPA() {
    try {
      // Request necessary permissions
      if (window.DeviceCommands) {
        // Notification listener permission
        await window.DeviceCommands.requestPermission({ permission: 'NOTIFICATION_LISTENER' }).catch(() => {})
        // Phone permissions
        await window.DeviceCommands.requestPermission({ permission: 'CALL_PHONE' }).catch(() => {})
        await window.DeviceCommands.requestPermission({ permission: 'READ_CONTACTS' }).catch(() => {})
        await window.DeviceCommands.requestPermission({ permission: 'READ_SMS' }).catch(() => {})
      }
    } catch (err) {
      console.warn('[JarvisPA] Android init error:', err)
    }
  }

  /**
   * Get PA capabilities for current platform
   */
  getCapabilities() {
    if (this.isAndroid) {
      return {
        whatsapp: true,
        calls: true,
        videoCalls: true,
        sms: true,
        contacts: true,
        notifications: true,
        calendar: true,
        camera: true,
        files: true,
        apps: true,
        tts: true,
        stt: true
      }
    }

    if (this.isDesktop) {
      return {
        whatsapp: true, // via WhatsApp Web
        calls: false,
        videoCalls: false,
        sms: false,
        contacts: false,
        notifications: true,
        calendar: false,
        camera: true,
        files: true,
        apps: true,
        tts: true,
        stt: true
      }
    }

    // Web
    return {
      whatsapp: true, // via WhatsApp Web API link
      calls: false,
      videoCalls: false,
      sms: false,
      contacts: false,
      notifications: true,
      calendar: false,
      camera: true,
      files: false,
      apps: false,
      tts: true,
      stt: true
    }
  }

  // ═══════════════════════════════════
  // WHATSAPP
  // ═══════════════════════════════════

  /**
   * Send WhatsApp message
   */
  async sendWhatsApp(phone, message) {
    const cleanPhone = phone.replace(/[^0-9+]/g, '')
    
    if (this.isAndroid && window.DeviceCommands) {
      try {
        // Direct WhatsApp intent on Android
        await window.DeviceCommands.sendWhatsApp({ phone: cleanPhone, message })
        return { success: true, message: `WhatsApp message sent to ${cleanPhone}` }
      } catch {
        // Fallback to URL scheme
      }
    }
    
    if (this.isDesktop) {
      await window.jarvisDesktop.whatsappSend(cleanPhone, message)
      return { success: true, message: `Opening WhatsApp for ${cleanPhone}` }
    }

    // Web fallback
    window.open(`https://api.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(message)}`)
    return { success: true, message: `Opening WhatsApp Web for ${cleanPhone}` }
  }

  /**
   * Open WhatsApp
   */
  async openWhatsApp() {
    if (this.isAndroid && window.DeviceCommands) {
      await window.DeviceCommands.openApp({ packageName: 'com.whatsapp' }).catch(() => {})
    } else if (this.isDesktop) {
      await window.jarvisDesktop.whatsappOpen()
    } else {
      window.open('https://web.whatsapp.com')
    }
    return { success: true }
  }

  // ═══════════════════════════════════
  // CALLS
  // ═══════════════════════════════════

  /**
   * Make a phone call (Android only)
   */
  async makeCall(phone) {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.makeCall({ phone })
        return { success: true, message: `Calling ${phone}...` }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    
    // Fallback: tel: protocol
    window.open(`tel:${phone}`)
    return { success: true, message: `Initiating call to ${phone}` }
  }

  /**
   * Answer incoming call (Android only)
   */
  async answerCall() {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.answerCall()
        return { success: true, message: 'Call answered' }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    return { success: false, error: 'Call answering requires Android' }
  }

  /**
   * End/reject call (Android only)
   */
  async endCall() {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.endCall()
        return { success: true, message: 'Call ended' }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    return { success: false, error: 'Call management requires Android' }
  }

  // ═══════════════════════════════════
  // CONTACTS
  // ═══════════════════════════════════

  /**
   * Get contacts (Android only)
   */
  async getContacts() {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        const result = await window.DeviceCommands.getContacts()
        this.contacts = result.contacts || []
        return { success: true, contacts: this.contacts }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    return { success: false, error: 'Contact access requires Android', contacts: [] }
  }

  /**
   * Find contact by name
   */
  async findContact(name) {
    if (this.contacts.length === 0) {
      await this.getContacts()
    }
    
    const query = name.toLowerCase()
    const matches = this.contacts.filter(c => 
      (c.name || '').toLowerCase().includes(query) ||
      (c.phone || '').includes(query)
    )
    
    return matches
  }

  // ═══════════════════════════════════
  // SMS
  // ═══════════════════════════════════

  /**
   * Send SMS (Android only)
   */
  async sendSMS(phone, message) {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.sendSMS({ phone, message })
        return { success: true, message: `SMS sent to ${phone}` }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    
    // Fallback
    window.open(`sms:${phone}?body=${encodeURIComponent(message)}`)
    return { success: true, message: `Opening SMS for ${phone}` }
  }

  // ═══════════════════════════════════
  // NOTIFICATIONS
  // ═══════════════════════════════════

  /**
   * Show notification
   */
  async showNotification(title, body, options = {}) {
    if (this.isDesktop) {
      await window.jarvisDesktop.showNotification({ title, body, ...options })
      return { success: true }
    }

    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body, icon: '/icon-192.png', ...options })
        return { success: true }
      } else if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission()
        if (permission === 'granted') {
          new Notification(title, { body, icon: '/icon-192.png', ...options })
          return { success: true }
        }
      }
    }

    return { success: false, error: 'Notifications not available' }
  }

  // ═══════════════════════════════════
  // VIDEO CALL PA MODE
  // ═══════════════════════════════════

  /**
   * Start PA video call mode
   * JARVIS takes over camera feed with AI avatar
   * Responds to callers on behalf of user
   */
  async startPAMode(options = {}) {
    this.paActive = true
    
    const config = {
      greeting: options.greeting || "Hello, I'm JARVIS, the AI assistant. The user is currently unavailable. How may I help you?",
      autoAnswer: options.autoAnswer !== false,
      recordCalls: options.recordCalls || false,
      forwardTo: options.forwardTo || null,
      language: options.language || 'en-US'
    }

    // On Android, set up call interception
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.registerCallListener({
          onIncoming: async (callInfo) => {
            if (this.paActive && config.autoAnswer) {
              // Answer the call
              await this.answerCall()
              
              // Speak greeting
              if (window.LocalTTS) {
                await window.LocalTTS.speak({ text: config.greeting, lang: config.language })
              } else {
                this._webSpeak(config.greeting)
              }

              // Listen for caller's response
              if (window.VoskSTT) {
                const response = await window.VoskSTT.listen({ timeout: 15000 })
                if (this.onIncomingCall) {
                  this.onIncomingCall({ ...callInfo, callerMessage: response.text })
                }
              }
            }
          }
        })
        
        console.log('[JarvisPA] PA mode active — JARVIS will answer calls')
      } catch (err) {
        console.warn('[JarvisPA] Call listener setup failed:', err)
      }
    }

    return { success: true, message: 'PA mode activated. JARVIS will handle calls and messages.' }
  }

  /**
   * Stop PA mode
   */
  async stopPAMode() {
    this.paActive = false
    
    if (this.isAndroid && window.DeviceCommands) {
      await window.DeviceCommands.unregisterCallListener().catch(() => {})
    }

    return { success: true, message: 'PA mode deactivated.' }
  }

  /**
   * Web speech synthesis fallback
   */
  _webSpeak(text) {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    utterance.pitch = 0.9
    const voices = speechSynthesis.getVoices()
    const voice = voices.find(v => v.lang.includes('en-GB')) || voices[0]
    if (voice) utterance.voice = voice
    speechSynthesis.speak(utterance)
  }

  // ═══════════════════════════════════
  // REMINDERS / CALENDAR
  // ═══════════════════════════════════

  /**
   * Set a reminder
   */
  async setReminder(title, timeMs) {
    const delay = timeMs - Date.now()
    if (delay <= 0) {
      return { success: false, error: 'Reminder time is in the past' }
    }

    setTimeout(() => {
      this.showNotification('⏰ JARVIS Reminder', title)
      this._webSpeak(`Reminder, Sir: ${title}`)
    }, delay)

    const time = new Date(timeMs).toLocaleTimeString()
    return { success: true, message: `Reminder set for ${time}: "${title}"` }
  }

  // ═══════════════════════════════════
  // APP CONTROL (Android)
  // ═══════════════════════════════════

  /**
   * Open any Android app
   */
  async openApp(packageName) {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        await window.DeviceCommands.openApp({ packageName })
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    return { success: false, error: 'App control requires Android' }
  }

  /**
   * Get installed apps list (Android)
   */
  async getInstalledApps() {
    if (this.isAndroid && window.DeviceCommands) {
      try {
        const result = await window.DeviceCommands.getInstalledApps()
        return { success: true, apps: result.apps || [] }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
    return { success: false, error: 'Requires Android' }
  }

  /**
   * Get PA status
   */
  getStatus() {
    return {
      active: this.paActive,
      platform: this.isAndroid ? 'android' : this.isDesktop ? 'desktop' : 'web',
      capabilities: this.getCapabilities(),
      contactsLoaded: this.contacts.length
    }
  }
}

const jarvisPA = new JarvisPA()
export default jarvisPA
