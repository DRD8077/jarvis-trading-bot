/**
 * 🔒 JARVIS SECURITY PROTOCOL — Intruder Detection & App Protection
 * ═══════════════════════════════════════════════════════════════════════
 * 
 * Like JARVIS detecting intruders in Tony's mansion:
 * - Failed login attempt detection
 * - App tampering detection
 * - Session anomaly detection
 * - Unusual usage pattern alerts
 * - Screen capture detection (visibility change)
 * - Device change detection
 * - Auto-lock on suspicious activity
 * - Security event logging
 */

let securityLog = []
let failedAttempts = 0
let deviceFingerprint = null
let isLocked = false
let suspiciousActivity = 0

const MAX_FAILED_ATTEMPTS = 5
const LOCK_DURATION = 5 * 60 * 1000 // 5 minutes

/**
 * Initialize security module
 */
function init() {
  // Generate device fingerprint
  deviceFingerprint = generateFingerprint()

  // Check if fingerprint changed (possible device theft)
  try {
    const savedFP = localStorage.getItem('jarvis_device_fp')
    if (savedFP && savedFP !== deviceFingerprint) {
      logEvent('DEVICE_CHANGE', 'Device fingerprint has changed — possible unauthorized access')
      suspiciousActivity += 3
      // Silent — no speech on device change (triggers on first install and app updates)
      console.warn('[JARVIS Security] Device fingerprint changed')
    }
    localStorage.setItem('jarvis_device_fp', deviceFingerprint)
  } catch {}

  // Detect screen capture / tab switch (possible screen recording)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      logEvent('SCREEN_HIDDEN', 'App went to background')
    } else {
      logEvent('SCREEN_VISIBLE', 'App came back to foreground')
    }
  })

  // Detect DevTools opening (debugging attempt) — v32: reduced frequency, no speech trigger
  let devToolsOpen = false
  const devToolsCheck = setInterval(() => {
    const threshold = 100
    const widthThreshold = window.outerWidth - window.innerWidth > threshold
    const heightThreshold = window.outerHeight - window.innerHeight > threshold
    
    if (widthThreshold || heightThreshold) {
      if (!devToolsOpen) {
        devToolsOpen = true
        logEvent('DEVTOOLS_OPEN', 'Developer tools detected')
        // v32: NO suspicious activity increment — prevents false lockouts on Android
      }
    } else {
      devToolsOpen = false
    }
  }, 30000) // v32: Check every 30s instead of 5s

  // Detect rapid clicking (brute force attempt)
  let clickBuffer = []
  document.addEventListener('click', () => {
    clickBuffer.push(Date.now())
    clickBuffer = clickBuffer.filter(t => Date.now() - t < 2000)
    if (clickBuffer.length > 20) {
      logEvent('RAPID_CLICK', 'Rapid clicking detected — possible bot/brute force')
      suspiciousActivity += 1
      clickBuffer = []
    }
  }, { passive: true })

  // Check for suspicious activity threshold — v32: higher threshold, no auto-speech
  setInterval(() => {
    if (suspiciousActivity >= 10 && !isLocked) {
      lockApp('Multiple suspicious activities detected')
    }
    // Decay suspicious activity over time (faster decay)
    if (suspiciousActivity > 0) suspiciousActivity -= 0.5
  }, 60000) // v32: Check every 60s instead of 30s

  // Restore security log
  try {
    const saved = localStorage.getItem('jarvis_security_log')
    if (saved) securityLog = JSON.parse(saved).slice(-50)
  } catch {}

  // Check if currently locked
  try {
    const lockData = JSON.parse(localStorage.getItem('jarvis_security_lock'))
    if (lockData && lockData.until > Date.now()) {
      isLocked = true
      setTimeout(() => unlock(), lockData.until - Date.now())
    }
  } catch {}

  console.log('[JARVIS Security] 🔒 Security Protocol ONLINE')

  return { cleanup: () => clearInterval(devToolsCheck) }
}

/**
 * Generate a simple device fingerprint
 */
function generateFingerprint() {
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 'unknown',
  ]
  // Simple hash
  let hash = 0
  const str = components.join('|')
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return 'FP-' + Math.abs(hash).toString(36)
}

/**
 * Log a security event
 */
function logEvent(type, description) {
  const event = {
    type,
    description,
    timestamp: Date.now(),
    time: new Date().toLocaleString(),
  }
  securityLog.push(event)
  if (securityLog.length > 100) securityLog = securityLog.slice(-100)

  console.log(`[JARVIS Security] ${type}: ${description}`)

  // Save
  try {
    localStorage.setItem('jarvis_security_log', JSON.stringify(securityLog.slice(-50)))
  } catch {}

  // Dispatch event
  window.dispatchEvent(new CustomEvent('jarvis-security-event', { detail: event }))
}

/**
 * Record a failed login attempt
 */
function recordFailedLogin() {
  failedAttempts++
  logEvent('FAILED_LOGIN', `Failed login attempt #${failedAttempts}`)

  if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
    lockApp('Too many failed login attempts')
  } else if (failedAttempts >= 3) {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: `Warning Sir, ${failedAttempts} failed login attempts detected. ${MAX_FAILED_ATTEMPTS - failedAttempts} attempts remaining before lockout.`, priority: 'critical' }
    }))
  }
}

/**
 * Reset failed login counter (on successful login)
 */
function resetFailedLogins() {
  failedAttempts = 0
  logEvent('LOGIN_SUCCESS', 'Successful authentication')
}

/**
 * Lock the app
 */
function lockApp(reason) {
  isLocked = true
  const until = Date.now() + LOCK_DURATION
  logEvent('APP_LOCKED', `App locked: ${reason}`)

  try {
    localStorage.setItem('jarvis_security_lock', JSON.stringify({ until, reason }))
  } catch {}

  // v32: Silent lock — visual only, no speech (prevents sound loop)
  console.warn('[JARVIS Security] APP LOCKED:', reason)

  window.dispatchEvent(new CustomEvent('jarvis-security-lock', { detail: { locked: true, reason, until } }))

  // Auto-unlock after duration
  setTimeout(() => unlock(), LOCK_DURATION)
}

/**
 * Unlock the app
 */
function unlock() {
  isLocked = false
  failedAttempts = 0
  suspiciousActivity = 0
  logEvent('APP_UNLOCKED', 'App unlocked — normal operations resumed')

  try { localStorage.removeItem('jarvis_security_lock') } catch {}

  // v32: Silent unlock — no speech
  console.log('[JARVIS Security] App unlocked')
  window.dispatchEvent(new CustomEvent('jarvis-security-lock', { detail: { locked: false } }))
}

/**
 * Get security status
 */
function getStatus() {
  return {
    locked: isLocked,
    failedAttempts,
    suspiciousActivity: Math.round(suspiciousActivity),
    deviceFingerprint,
    securityLevel: suspiciousActivity >= 3 ? 'HIGH_ALERT' : suspiciousActivity >= 1 ? 'ELEVATED' : 'NORMAL',
    logCount: securityLog.length,
  }
}

/**
 * Get security log
 */
function getLog() {
  return securityLog
}

/**
 * Check if app is locked
 */
function isAppLocked() {
  return isLocked
}

/**
 * Run security diagnostic
 */
function runDiagnostic() {
  const results = {
    deviceFingerprint: !!deviceFingerprint,
    localStorage: (() => { try { localStorage.setItem('test', '1'); localStorage.removeItem('test'); return true } catch { return false } })(),
    online: navigator.onLine,
    secureContext: window.isSecureContext,
    cookiesEnabled: navigator.cookieEnabled,
    failedAttempts,
    suspiciousEvents: securityLog.filter(e => ['FAILED_LOGIN', 'RAPID_CLICK', 'DEVTOOLS_OPEN', 'DEVICE_CHANGE'].includes(e.type)).length,
  }

  logEvent('DIAGNOSTIC', 'Security diagnostic completed')

  // Announce results
  const issues = Object.entries(results).filter(([, v]) => v === false).map(([k]) => k)
  if (issues.length > 0) {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: `Sir, security diagnostic complete. ${issues.length} issues found: ${issues.join(', ')}. Investigate karna chahiye.`, priority: 'high' }
    }))
  } else {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Sir, security diagnostic complete. All systems secure. Koi threat nahi mila.', priority: 'high' }
    }))
  }

  return results
}

const jarvisSecurity = {
  init,
  logEvent,
  recordFailedLogin,
  resetFailedLogins,
  lockApp,
  unlock,
  getStatus,
  getLog,
  isAppLocked,
  runDiagnostic,
}

export default jarvisSecurity
export { init, logEvent, getStatus, getLog, isAppLocked, runDiagnostic }
