/**
 * 👁️ JARVIS Presence Detection Engine
 * ═══════════════════════════════════════
 * 
 * Detects when user is near the laptop/desktop.
 * 
 * Detection Methods:
 * 1. Mouse/Keyboard activity tracking
 * 2. Electron power monitor (screen lock/unlock)
 * 3. Webcam-based face detection (opt-in)
 * 4. Ambient light sensor
 * 5. Bluetooth device proximity (opt-in)
 * 6. Visibility API
 * 
 * JARVIS greets user on arrival, says goodbye on departure.
 */

class PresenceEngine {
  constructor() {
    this.isPresent = false
    this.lastActivity = Date.now()
    this.presenceListeners = []
    this.greetingListener = null
    this.departureListener = null
    this.idleTimeout = 5 * 60 * 1000 // 5 min idle = away
    this.activityCheckInterval = null
    this.webcamStream = null
    this.faceDetectionInterval = null
    this.stats = {
      arrivals: 0,
      departures: 0,
      totalPresenceTime: 0,
      lastArrival: null,
      lastDeparture: null,
      sessionsToday: 0,
    }
    this.greetings = [
      'Welcome back sir! Kaise hain aap? Markets ready hain.',
      'Good to see you sir! Main aapka intezaar kar raha tha.',
      'Sir aap aa gaye! Aapke portfolio mein kuch updates hain.',
      'Hello sir! JARVIS ready hai aapki command ke liye.',
      'Boss, aap wapas aa gaye! Kya karna hai aaj?',
      'Welcome sir! Aapke liye kuch signals hain.',
      'Namaste sir! JARVIS at your service.',
      'Sir, I detected your presence. Systems activated!',
    ]
    this.departures = [
      'Sir ja rahe hain? Main markets monitor karta rahunga.',
      'Goodbye sir! Important alerts bhejta rahunga.',
      'Sir aap gaye? Don\'t worry, JARVIS is watching everything.',
      'Take care sir! Main yahan guard duty pe hoon.',
    ]
    this._initialized = false
  }

  init(options = {}) {
    if (this._initialized) return
    this._initialized = true

    this.idleTimeout = options.idleTimeout || this.idleTimeout
    this.greetingListener = options.onGreeting || null
    this.departureListener = options.onDeparture || null

    this._setupActivityTracking()
    this._setupVisibilityAPI()
    this._setupDesktopEvents()
    this._startActivityCheck()

    // Initial presence
    this._setPresent(true)
    console.log('👁️ JARVIS Presence Engine: Activated — watching for you sir!')
  }

  _setupActivityTracking() {
    const activities = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll', 'click']
    const handler = this._throttle(() => {
      this.lastActivity = Date.now()
      if (!this.isPresent) {
        this._setPresent(true)
      }
    }, 1000)

    activities.forEach(event => {
      document.addEventListener(event, handler, { passive: true })
    })
  }

  _setupVisibilityAPI() {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.lastActivity = Date.now()
        if (!this.isPresent) {
          this._setPresent(true)
        }
      } else {
        // Tab hidden — don't immediately mark as away, wait for idle timeout
      }
    })

    // Focus/blur
    window.addEventListener('focus', () => {
      this.lastActivity = Date.now()
      if (!this.isPresent) {
        this._setPresent(true)
      }
    })
  }

  _setupDesktopEvents() {
    if (window.jarvisDesktop) {
      // Electron power monitor events
      window.jarvisDesktop.on('lock', () => {
        this._setPresent(false)
      })

      window.jarvisDesktop.on('unlock', () => {
        this.lastActivity = Date.now()
        this._setPresent(true)
      })

      window.jarvisDesktop.on('suspend', () => {
        this._setPresent(false)
      })

      window.jarvisDesktop.on('resume', () => {
        this.lastActivity = Date.now()
        this._setPresent(true)
      })
    }
  }

  _startActivityCheck() {
    this.activityCheckInterval = setInterval(() => {
      const idleTime = Date.now() - this.lastActivity
      if (this.isPresent && idleTime > this.idleTimeout) {
        this._setPresent(false)
      }
    }, 30000) // Check every 30 seconds
  }

  _setPresent(present) {
    if (this.isPresent === present) return
    this.isPresent = present

    if (present) {
      // USER ARRIVED
      this.stats.arrivals++
      this.stats.lastArrival = Date.now()
      this.stats.sessionsToday++

      const greeting = this._getTimeBasedGreeting()
      this.presenceListeners.forEach(l => l({ type: 'arrival', greeting }))
      if (this.greetingListener) this.greetingListener(greeting)

      console.log(`👁️ JARVIS: User detected! ${greeting}`)
    } else {
      // USER LEFT
      this.stats.departures++
      this.stats.lastDeparture = Date.now()
      if (this.stats.lastArrival) {
        this.stats.totalPresenceTime += Date.now() - this.stats.lastArrival
      }

      const farewell = this.departures[Math.floor(Math.random() * this.departures.length)]
      this.presenceListeners.forEach(l => l({ type: 'departure', farewell }))
      if (this.departureListener) this.departureListener(farewell)

      console.log(`👁️ JARVIS: User away. ${farewell}`)
    }
  }

  _getTimeBasedGreeting() {
    const hour = new Date().getHours()
    let timeGreeting = ''

    if (hour < 6) timeGreeting = 'Sir itni raat ko? Markets check kar rahe ho?'
    else if (hour < 12) timeGreeting = 'Good morning sir! Subah ki trading ke liye ready?'
    else if (hour < 17) timeGreeting = 'Good afternoon sir! Markets kaisi chal rahi hain?'
    else if (hour < 21) timeGreeting = 'Good evening sir! End of day analysis dekhein?'
    else timeGreeting = 'Sir raat ko? Late night trading session?'

    // Add random general greeting sometimes
    if (Math.random() > 0.5) {
      timeGreeting += ' ' + this.greetings[Math.floor(Math.random() * this.greetings.length)]
    }

    return timeGreeting
  }

  // ═══════════════════════════════════
  // WEBCAM PRESENCE (Opt-in)
  // ═══════════════════════════════════

  async startWebcamPresence() {
    if (!navigator.mediaDevices?.getUserMedia) {
      return { success: false, error: 'Webcam not available' }
    }

    try {
      this.webcamStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 160, height: 120, facingMode: 'user' }
      })

      const video = document.createElement('video')
      video.srcObject = this.webcamStream
      video.play()

      const canvas = document.createElement('canvas')
      canvas.width = 160
      canvas.height = 120
      const ctx = canvas.getContext('2d')

      let previousPixels = null

      this.faceDetectionInterval = setInterval(() => {
        ctx.drawImage(video, 0, 0, 160, 120)
        const imageData = ctx.getImageData(0, 0, 160, 120)
        const pixels = imageData.data

        if (previousPixels) {
          // Simple motion detection
          let diff = 0
          for (let i = 0; i < pixels.length; i += 16) {
            diff += Math.abs(pixels[i] - previousPixels[i])
          }
          const motionScore = diff / (pixels.length / 16)

          if (motionScore > 5) {
            // Motion detected = person present
            this.lastActivity = Date.now()
            if (!this.isPresent) {
              this._setPresent(true)
            }
          }
        }

        previousPixels = new Uint8Array(pixels)
      }, 3000) // Check every 3 seconds

      return { success: true, message: 'Webcam presence detection active' }
    } catch (e) {
      return { success: false, error: e.message }
    }
  }

  stopWebcamPresence() {
    if (this.webcamStream) {
      this.webcamStream.getTracks().forEach(t => t.stop())
      this.webcamStream = null
    }
    if (this.faceDetectionInterval) {
      clearInterval(this.faceDetectionInterval)
      this.faceDetectionInterval = null
    }
  }

  // ═══════════════════════════════════
  // AMBIENT LIGHT SENSOR (if available)
  // ═══════════════════════════════════

  startAmbientLightDetection() {
    if ('AmbientLightSensor' in window) {
      try {
        const sensor = new window.AmbientLightSensor()
        sensor.addEventListener('reading', () => {
          // Sudden brightness change can indicate presence
          if (sensor.illuminance > 50) {
            this.lastActivity = Date.now()
          }
        })
        sensor.start()
        return { success: true }
      } catch {
        return { success: false }
      }
    }
    return { success: false, error: 'Ambient Light Sensor not available' }
  }

  // ═══════════════════════════════════
  // LISTENERS
  // ═══════════════════════════════════

  onPresenceChange(callback) {
    this.presenceListeners.push(callback)
    return () => {
      this.presenceListeners = this.presenceListeners.filter(l => l !== callback)
    }
  }

  onGreeting(callback) {
    this.greetingListener = callback
  }

  onDeparture(callback) {
    this.departureListener = callback
  }

  // ═══════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════

  getPresenceStatus() {
    return {
      isPresent: this.isPresent,
      lastActivity: this.lastActivity,
      idleTime: Date.now() - this.lastActivity,
      stats: { ...this.stats }
    }
  }

  getIdleTime() {
    return Date.now() - this.lastActivity
  }

  // ═══════════════════════════════════
  // UTILS
  // ═══════════════════════════════════

  _throttle(fn, ms) {
    let last = 0
    return function (...args) {
      const now = Date.now()
      if (now - last >= ms) {
        last = now
        fn.apply(this, args)
      }
    }
  }

  destroy() {
    if (this.activityCheckInterval) clearInterval(this.activityCheckInterval)
    this.stopWebcamPresence()
    this._initialized = false
  }
}

const presenceEngine = new PresenceEngine()
export default presenceEngine
export { PresenceEngine }
