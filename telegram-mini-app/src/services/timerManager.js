/**
 * JARVIS Global Timer Manager
 * 
 * Pauses ALL setInterval timers when the app goes to background.
 * Resumes them when the app returns to foreground.
 * This saves battery, prevents failed API calls, and avoids rate limits.
 * 
 * Usage: Replace `setInterval(fn, ms)` with `timerManager.addInterval(fn, ms, 'label')`
 *        Or just include this — it monkey-patches window.setInterval globally.
 */

class TimerManager {
  constructor() {
    this._timers = new Map()  // id → { fn, ms, label, paused }
    this._paused = false
    this._nextId = 1

    // Listen for visibility changes
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          this.pauseAll()
        } else {
          this.resumeAll()
        }
      })

      // Also handle Capacitor App plugin background/foreground
      this._setupCapacitorListeners()
    }
  }

  async _setupCapacitorListeners() {
    try {
      const { App } = await import('@capacitor/app')
      App.addListener('appStateChange', ({ isActive }) => {
        if (isActive) {
          this.resumeAll()
        } else {
          this.pauseAll()
        }
      })
    } catch {}
  }

  pauseAll() {
    if (this._paused) return
    this._paused = true
    console.log(`[TimerManager] ⏸️ Pausing ${this._timers.size} timers (app in background)`)
    
    this._timers.forEach((timer, id) => {
      if (timer.nativeId) {
        clearInterval(timer.nativeId)
        timer.nativeId = null
        timer.paused = true
      }
    })
  }

  resumeAll() {
    if (!this._paused) return
    this._paused = false
    console.log(`[TimerManager] ▶️ Resuming ${this._timers.size} timers (app in foreground)`)
    
    this._timers.forEach((timer, id) => {
      if (timer.paused) {
        timer.nativeId = this._rawSetInterval(timer.fn, timer.ms)
        timer.paused = false
      }
    })
  }

  /**
   * Monkey-patch window.setInterval and window.clearInterval
   * so ALL existing code automatically benefits from pause/resume
   */
  install() {
    if (typeof window === 'undefined') return
    
    const self = this
    this._rawSetInterval = window.setInterval.bind(window)
    this._rawClearInterval = window.clearInterval.bind(window)

    // Override setInterval
    window.setInterval = function(fn, ms, ...args) {
      const id = self._nextId++
      const wrappedFn = () => fn(...args)
      
      const nativeId = self._paused ? null : self._rawSetInterval(wrappedFn, ms)
      
      self._timers.set(id, {
        fn: wrappedFn,
        ms,
        nativeId,
        paused: self._paused,
      })

      return id
    }

    // Override clearInterval
    window.clearInterval = function(id) {
      const timer = self._timers.get(id)
      if (timer) {
        if (timer.nativeId) self._rawClearInterval(timer.nativeId)
        self._timers.delete(id)
      } else {
        // Might be a raw interval ID from before monkey-patching
        self._rawClearInterval(id)
      }
    }

    console.log('[TimerManager] ✅ Installed — all setIntervals will pause in background')
  }

  getStats() {
    return {
      total: this._timers.size,
      paused: this._paused,
      active: [...this._timers.values()].filter(t => !t.paused).length,
    }
  }
}

const timerManager = new TimerManager()
export default timerManager
