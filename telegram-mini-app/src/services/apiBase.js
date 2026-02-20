/**
 * 🌐 JARVIS API Base URL — Smart Auto-Detection
 * ════════════════════════════════════════════════════
 * Priority order:
 * 1. VITE_API_BASE env variable (dev/build override)
 * 2. Same-origin relative path (fastest, zero CORS)
 * 3. Fallback → relative path (works when served from same server)
 *
 * NOTE: The APK bundles the full UI locally. API calls use relative
 * paths so the Capacitor server or any proxy can route them.
 */

export function isNativeApp() {
  return typeof window !== 'undefined' && 
    (window.Capacitor?.isNativePlatform?.() || 
     window.location.protocol === 'file:' ||
     (window.location.hostname === 'localhost' && !window.location.port))
}

const LIVE_SERVER = 'https://jarvis-trading-production.up.railway.app'

function detectServerBase() {
  // 1. Env override (set during build via VITE_API_BASE)
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE.replace('/api/miniapp', '')
  }
  // 2. Running inside APK → use live Railway server
  if (isNativeApp()) {
    return LIVE_SERVER
  }
  // 3. Same-origin (browser) → relative path
  return ''
}

export function getServerBase() {
  return detectServerBase()
}

export function getApiBase() {
  const base = detectServerBase()
  return base ? `${base}/api/miniapp` : '/api/miniapp'
}

export const API_BASE = getApiBase()
export const SERVER_BASE = getServerBase()

export default { API_BASE, SERVER_BASE, getApiBase, getServerBase, isNativeApp }
