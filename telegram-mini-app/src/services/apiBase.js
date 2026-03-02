/**
 * 🌐 JARVIS API Base URL — Standalone Auto-Detection v3.0
 * ════════════════════════════════════════════════════════════
 * 
 * STANDALONE MODE — No Telegram, No Mini App dependency.
 * 
 * APK MODE (Capacitor Native):
 *   UI loads locally from bundled dist/ folder
 *   API calls go to configured production server
 *
 * BROWSER / PWA MODE:
 *   Same-origin relative paths (zero CORS)
 *
 * Priority:
 * 1. VITE_API_BASE env override (build-time)
 * 2. Runtime config from window.__JARVIS_CONFIG__
 * 3. Native APK → production server
 * 4. Same-origin relative path (browser)
 */

export function isNativeApp() {
  if (typeof window === 'undefined') return false
  if (window.Capacitor?.isNativePlatform?.()) return true
  if (window.location.protocol === 'file:') return true
  if (window.location.protocol === 'capacitor:') return true
  if (window.location.hostname === 'localhost' && !window.location.port) return true
  return false
}

export function isDesktopApp() {
  return typeof window !== 'undefined' && !!window.jarvisDesktop
}

// Production server URL — Codespace deployment
const LIVE_SERVER = import.meta.env.VITE_SERVER_URL 
  || window?.__JARVIS_CONFIG__?.serverUrl
  || 'https://super-duper-funicular-gp99q655qw6cprr-8000.app.github.dev'

function detectServerBase() {
  // 1. Build-time env override
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE.replace('/api/miniapp', '')
  }
  // 2. Runtime config override
  if (window?.__JARVIS_CONFIG__?.serverUrl) {
    return window.__JARVIS_CONFIG__.serverUrl
  }
  // 3. Native APK → production server
  if (isNativeApp()) {
    console.log('[JARVIS] Native APK → Server:', LIVE_SERVER)
    return LIVE_SERVER
  }
  // 4. Desktop app
  if (isDesktopApp()) {
    return window.jarvisDesktop?.serverUrl || LIVE_SERVER
  }
  // 5. Browser → same-origin
  return ''
}

export function getServerBase() {
  return detectServerBase()
}

export function getApiBase() {
  const base = detectServerBase()
  return base ? `${base}/api/miniapp` : '/api/miniapp'
}

export function getWebSocketUrl() {
  const base = detectServerBase()
  if (base) {
    return base.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws`
}

export const API_BASE = getApiBase()
export const SERVER_BASE = getServerBase()
export const WS_URL = getWebSocketUrl()

// Startup log
if (typeof window !== 'undefined') {
  console.log(`[JARVIS] Mode: ${isNativeApp() ? 'Native APK' : isDesktopApp() ? 'Desktop' : 'Browser'}`)
  console.log(`[JARVIS] API: ${API_BASE}`)
  console.log(`[JARVIS] WS:  ${WS_URL}`)
}

export default { API_BASE, SERVER_BASE, WS_URL, getApiBase, getServerBase, getWebSocketUrl, isNativeApp, isDesktopApp, LIVE_SERVER }
