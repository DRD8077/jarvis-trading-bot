/**
 * 📊 JARVIS Crash Analytics & Performance Monitor
 * ══════════════════════════════════════════════════
 * - Catch all JS errors + unhandled rejections
 * - Track page load times, API response times
 * - Memory usage monitoring
 * - FPS counter for UI smoothness
 * - Session recording (breadcrumbs)
 * - Send crash reports to server
 * - User-facing stability score
 */

const MAX_BREADCRUMBS = 50
const MAX_ERRORS = 100
const REPORT_INTERVAL = 60000 // 1 min batch

class CrashAnalytics {
  constructor() {
    this.errors = []
    this.breadcrumbs = []
    this.metrics = {
      pageLoads: [],
      apiCalls: [],
      fps: 60,
      memoryUsage: 0,
      sessionStart: Date.now(),
      crashes: 0,
      anrCount: 0, // App Not Responding
    }
    this.isInitialized = false
  }

  init() {
    if (this.isInitialized || typeof window === 'undefined') return
    this.isInitialized = true

    // Global error handler
    window.addEventListener('error', (event) => {
      this._captureError({
        type: 'error',
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        col: event.colno,
        stack: event.error?.stack,
        timestamp: Date.now(),
      })
    })

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this._captureError({
        type: 'unhandledrejection',
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        timestamp: Date.now(),
      })
    })

    // Navigation tracking
    const origPush = history.pushState
    history.pushState = (...args) => {
      this.addBreadcrumb('navigation', `→ ${args[2] || 'unknown'}`)
      origPush.apply(history, args)
    }

    // FPS monitoring
    this._startFPSMonitor()

    // Memory monitoring
    this._startMemoryMonitor()

    // ANR detection (main thread block > 5s)
    this._startANRDetector()

    // Performance observer for page loads
    if ('PerformanceObserver' in window) {
      try {
        const navObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach(entry => {
            this.metrics.pageLoads.push({
              name: entry.name,
              duration: entry.duration,
              timestamp: Date.now(),
            })
          })
        })
        navObserver.observe({ type: 'navigation', buffered: true })

        // Long task detection
        const ltObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach(entry => {
            if (entry.duration > 100) {
              this.addBreadcrumb('performance', `Long task: ${entry.duration.toFixed(0)}ms`)
            }
          })
        })
        ltObserver.observe({ type: 'longtask', buffered: true })
      } catch (e) {
        // PerformanceObserver may not support all entry types
      }
    }

    // Periodic report
    setInterval(() => this._sendReport(), REPORT_INTERVAL)

    console.log('[Analytics] Crash analytics initialized')
  }

  /**
   * Add a breadcrumb for tracking user actions
   */
  addBreadcrumb(category, message, data = null) {
    this.breadcrumbs.push({
      category,
      message,
      data,
      timestamp: Date.now(),
    })
    if (this.breadcrumbs.length > MAX_BREADCRUMBS) {
      this.breadcrumbs.shift()
    }
  }

  /**
   * Track an API call timing
   */
  trackAPI(endpoint, duration, status) {
    this.metrics.apiCalls.push({
      endpoint,
      duration,
      status,
      timestamp: Date.now(),
    })
    // Keep last 200
    if (this.metrics.apiCalls.length > 200) {
      this.metrics.apiCalls = this.metrics.apiCalls.slice(-200)
    }
  }

  /**
   * Get health score (0-100)
   */
  getHealthScore() {
    let score = 100

    // Deduct for errors
    const recentErrors = this.errors.filter(e => Date.now() - e.timestamp < 300000).length
    score -= recentErrors * 10

    // Deduct for low FPS
    if (this.metrics.fps < 30) score -= 20
    else if (this.metrics.fps < 50) score -= 10

    // Deduct for high memory
    if (this.metrics.memoryUsage > 80) score -= 15
    else if (this.metrics.memoryUsage > 60) score -= 5

    // Deduct for slow API calls
    const recentAPIs = this.metrics.apiCalls.filter(a => Date.now() - a.timestamp < 60000)
    const slowAPIs = recentAPIs.filter(a => a.duration > 3000).length
    score -= slowAPIs * 5

    // Deduct for ANR
    score -= this.metrics.anrCount * 15

    return Math.max(0, Math.min(100, score))
  }

  /**
   * Get performance summary for Settings page
   */
  getSummary() {
    const now = Date.now()
    const sessionDuration = now - this.metrics.sessionStart
    const recentAPIs = this.metrics.apiCalls.filter(a => now - a.timestamp < 300000)
    const avgAPITime = recentAPIs.length > 0 ?
      recentAPIs.reduce((s, a) => s + a.duration, 0) / recentAPIs.length : 0

    return {
      healthScore: this.getHealthScore(),
      fps: this.metrics.fps,
      memoryUsage: this.metrics.memoryUsage,
      sessionDuration: Math.floor(sessionDuration / 60000),
      totalErrors: this.errors.length,
      totalAPICalls: this.metrics.apiCalls.length,
      avgAPITime: Math.round(avgAPITime),
      crashes: this.metrics.crashes,
      anrCount: this.metrics.anrCount,
    }
  }

  _captureError(error) {
    this.errors.push(error)
    this.metrics.crashes++
    if (this.errors.length > MAX_ERRORS) {
      this.errors.shift()
    }
    console.warn('[Analytics] Error captured:', error.message)
  }

  _startFPSMonitor() {
    let frames = 0
    let lastCheck = performance.now()

    const tick = () => {
      frames++
      const now = performance.now()
      if (now - lastCheck >= 1000) {
        this.metrics.fps = Math.round(frames * 1000 / (now - lastCheck))
        frames = 0
        lastCheck = now
      }
      requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }

  _startMemoryMonitor() {
    setInterval(() => {
      if (performance.memory) {
        const used = performance.memory.usedJSHeapSize
        const total = performance.memory.jsHeapSizeLimit
        this.metrics.memoryUsage = Math.round((used / total) * 100)
      }
    }, 5000)
  }

  _startANRDetector() {
    let lastTick = Date.now()
    setInterval(() => {
      const now = Date.now()
      const delta = now - lastTick
      if (delta > 5000) {
        this.metrics.anrCount++
        this.addBreadcrumb('anr', `Main thread blocked for ${delta}ms`)
      }
      lastTick = now
    }, 1000)
  }

  async _sendReport() {
    if (this.errors.length === 0 && this.metrics.apiCalls.length === 0) return
    
    try {
      const { getApiBase } = await import('./apiBase')
      const base = getApiBase()
      
      await fetch(`${base}/analytics/crash-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          errors: this.errors.slice(-10),
          metrics: this.getSummary(),
          breadcrumbs: this.breadcrumbs.slice(-20),
          userAgent: navigator.userAgent,
          timestamp: Date.now(),
        })
      }).catch(() => {})
    } catch (e) {
      // Silent fail
    }
  }
}

const crashAnalytics = new CrashAnalytics()
export default crashAnalytics
