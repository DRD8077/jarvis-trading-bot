/**
 * 🌐 JARVIS API Base URL — Smart Auto-Detection v2.0
 * ════════════════════════════════════════════════════
 * 
 * APK MODE (Native):
 *   UI loads locally from bundled dist/ folder
 *   API calls go to Railway production server
 *   Gemini AI, signals, trading — all via live backend
 *
 * BROWSER MODE:
 *   Relative paths (same-origin, zero CORS)
 *
 * Priority:
 * 1. VITE_API_BASE env override
 * 2. Native APK → Railway live server (for Gemini + all APIs)
 * 3. Same-origin relative path (browser)
 */

export function isNativeApp() {
  if (typeof window === 'undefined') return false
  // Capacitor native platform detection
  if (window.Capacitor?.isNativePlatform?.()) return true
  // file:// protocol (local WebView)
  if (window.location.protocol === 'file:') return true
  // Capacitor serves from localhost without port or capacitor://
  if (window.location.protocol === 'capacitor:') return true
  if (window.location.hostname === 'localhost' && !window.location.port) return true
  return false
}

const LIVE_SERVER = 'https://jarvis-trading-production.up.railway.app'

function detectServerBase() {
  // 1. Build-time env override
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE.replace('/api/miniapp', '')
  }
  // 2. Native APK → always use live Railway server for ALL API calls
  if (isNativeApp()) {
    console.log('[JARVIS] Native APK detected → API base:', LIVE_SERVER)
    return LIVE_SERVER
  }
  // 3. Browser → same-origin relative
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

// Log connection info on startup
if (typeof window !== 'undefined') {
  console.log(`[JARVIS] API Base: ${API_BASE}`)
  console.log(`[JARVIS] Server Base: ${SERVER_BASE}`)
  console.log(`[JARVIS] Native App: ${isNativeApp()}`)
}

export default { API_BASE, SERVER_BASE, getApiBase, getServerBase, isNativeApp, LIVE_SERVER }
