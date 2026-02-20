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

function detectServerBase() {
  // 1. Env override (set during build via VITE_API_BASE)
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE.replace('/api/miniapp', '')
  }
  // 2. For native app, use the configured server URL from Capacitor
  if (isNativeApp() && window.Capacitor?.getServerUrl) {
    try {
      const serverUrl = window.Capacitor.getServerUrl()
      if (serverUrl && !serverUrl.startsWith('file:')) {
        return serverUrl
      }
    } catch (_) { /* ignore */ }
  }
  // 3. Relative path — works when UI & API are on same origin
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
