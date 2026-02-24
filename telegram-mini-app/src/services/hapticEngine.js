/**
 * 📳 JARVIS Haptic Feedback Engine
 * ═══════════════════════════════════
 * - Different vibration patterns per event type
 * - Capacitor Haptics for native Android
 * - Web Vibration API fallback
 * - User-configurable intensity
 * - Silent mode support
 */

const PATTERNS = {
  // Quick tap for UI interactions
  impact: [10],
  light: [5],
  medium: [15],
  heavy: [25],
  
  // Trading events
  buy: [20, 50, 20],        // Quick double-tap
  sell: [30, 40, 30],       // Stronger double-tap
  profit: [10, 30, 10, 30, 10, 30, 100], // Victory crescendo
  loss: [50, 100, 50],      // Warning buzz
  
  // Alerts
  alert: [20, 50, 20, 50, 20, 50, 20], // Attention-grabbing
  notification: [10, 50, 10],   // Gentle nudge
  success: [10, 30, 50],        // Ascending happiness
  error: [100, 50, 100],        // Double buzz warning
  
  // Navigation
  tabSwitch: [5],
  longPress: [5, 30, 50],
  swipe: [8],
  
  // Special
  whaleAlert: [50, 50, 50, 50, 200], // WHALE spotted!
  priceTarget: [10, 20, 10, 20, 10, 20, 150], // Price target hit
  countdown: [10, 200, 10, 200, 10, 200, 100], // 3-2-1 GO!
}

class HapticEngine {
  constructor() {
    this.enabled = localStorage.getItem('jarvis_haptics') !== 'false'
    this.intensity = parseFloat(localStorage.getItem('jarvis_haptic_intensity') || '1.0')
    this.nativeAvailable = false
    this._checkNative()
  }

  async _checkNative() {
    try {
      const { Haptics } = await import('@capacitor/haptics').catch(() => ({}))
      if (Haptics?.vibrate) {
        this.nativeAvailable = true
        this._native = Haptics
      }
    } catch {
      // Web only
    }
  }

  /**
   * Trigger haptic feedback
   * @param {string} type - Pattern name from PATTERNS
   */
  trigger(type) {
    if (!this.enabled) return

    const pattern = PATTERNS[type] || PATTERNS.impact
    
    // Scale by intensity
    const scaled = pattern.map(v => Math.round(v * this.intensity))

    // Try native first (Capacitor)
    if (this.nativeAvailable && this._native) {
      try {
        if (type === 'impact' || type === 'light') {
          this._native.impact({ style: 'LIGHT' })
        } else if (type === 'heavy' || type === 'error') {
          this._native.impact({ style: 'HEAVY' })
        } else {
          this._native.vibrate({ duration: scaled.reduce((s, v) => s + v, 0) })
        }
        return
      } catch {
        // Fall through to web API
      }
    }

    // Web Vibration API fallback
    if (navigator.vibrate) {
      navigator.vibrate(scaled)
    }
  }

  /**
   * Enable/disable haptics
   */
  setEnabled(enabled) {
    this.enabled = enabled
    localStorage.setItem('jarvis_haptics', String(enabled))
  }

  /**
   * Set intensity (0.0 - 2.0)
   */
  setIntensity(intensity) {
    this.intensity = Math.max(0, Math.min(2, intensity))
    localStorage.setItem('jarvis_haptic_intensity', String(this.intensity))
  }

  /**
   * Test all patterns
   */
  async testAll() {
    const types = Object.keys(PATTERNS)
    for (const type of types) {
      this.trigger(type)
      await new Promise(r => setTimeout(r, 800))
    }
  }

  /**
   * Get available patterns
   */
  getPatterns() {
    return Object.keys(PATTERNS)
  }
}

const haptics = new HapticEngine()
export default haptics
