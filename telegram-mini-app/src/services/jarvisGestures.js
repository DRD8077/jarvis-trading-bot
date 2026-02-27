/**
 * 🤌 JARVIS GESTURE CONTROLS — Iron Man Hand Gestures
 * ═══════════════════════════════════════════════════════
 * 
 * Tony Stark controls holograms with gestures:
 * - SHAKE phone → Emergency market scan (like deploying suit)
 * - DOUBLE TAP (2 fingers) → Toggle JARVIS HUD expand
 * - LONG PRESS (3s) → Talk to JARVIS
 * - SWIPE DOWN from top → Force refresh data
 * 
 * Uses device accelerometer for shake detection
 * All gesture feedback announced by JARVIS voice
 */

let shakeEnabled = true
let lastShakeTime = 0
const SHAKE_THRESHOLD = 25        // Acceleration needed to trigger
const SHAKE_COOLDOWN = 10000      // 10 seconds between shakes
const DOUBLE_TAP_WINDOW = 300     // ms between taps

let lastTapTime = 0
let tapCount = 0
let tapTimer = null

// ═══ SHAKE DETECTION — Uses DeviceMotion API ═══
function initShakeDetection() {
  if (typeof window === 'undefined') return
  
  let lastX = 0, lastY = 0, lastZ = 0
  let lastMotionTime = 0

  const handleMotion = (event) => {
    if (!shakeEnabled) return
    
    const acc = event.accelerationIncludingGravity || event.acceleration
    if (!acc) return
    
    const now = Date.now()
    if (now - lastMotionTime < 100) return // Throttle to 10Hz
    lastMotionTime = now

    const { x, y, z } = acc
    const deltaX = Math.abs(x - lastX)
    const deltaY = Math.abs(y - lastY)
    const deltaZ = Math.abs(z - lastZ)
    const acceleration = deltaX + deltaY + deltaZ

    lastX = x || 0
    lastY = y || 0
    lastZ = z || 0

    if (acceleration > SHAKE_THRESHOLD) {
      if (now - lastShakeTime > SHAKE_COOLDOWN) {
        lastShakeTime = now
        onShake()
      }
    }
  }

  // Request permission on iOS
  if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
    // iOS 13+ needs permission — we'll request on first user interaction
    const requestOnce = () => {
      DeviceMotionEvent.requestPermission()
        .then(perm => {
          if (perm === 'granted') {
            window.addEventListener('devicemotion', handleMotion)
          }
        })
        .catch(() => {})
      window.removeEventListener('touchend', requestOnce)
    }
    window.addEventListener('touchend', requestOnce, { once: true })
  } else {
    window.addEventListener('devicemotion', handleMotion)
  }
  
  console.log('[JARVIS] 🤌 Gesture controls initialized — shake to scan')
}

// ═══ DOUBLE TAP DETECTION ═══
function initDoubleTap() {
  if (typeof window === 'undefined') return
  
  // Listen for double-tap on the HUD area (top of screen)
  document.addEventListener('touchend', (e) => {
    // Only trigger in top 60px of screen (HUD area)
    const touch = e.changedTouches?.[0]
    if (!touch || touch.clientY > 60) return
    
    const now = Date.now()
    if (now - lastTapTime < DOUBLE_TAP_WINDOW) {
      tapCount++
      if (tapCount >= 2) {
        tapCount = 0
        onDoubleTap()
      }
    } else {
      tapCount = 1
    }
    lastTapTime = now
    
    clearTimeout(tapTimer)
    tapTimer = setTimeout(() => { tapCount = 0 }, DOUBLE_TAP_WINDOW + 50)
  }, { passive: true })
}

// ═══ GESTURE HANDLERS ═══

function onShake() {
  console.log('[JARVIS] 📳 SHAKE detected — Emergency scan!')
  
  // Haptic feedback only — no auto-speech or brain scan (v32: prevents accidental triggers)
  try { navigator.vibrate?.([100, 50, 100]) } catch {}
  
  // Visual feedback only
  window.dispatchEvent(new CustomEvent('jarvis-gesture', { detail: { type: 'shake' } }))
}

function onDoubleTap() {
  console.log('[JARVIS] 👆👆 Double tap — Toggle HUD')
  
  try { navigator.vibrate?.(50) } catch {}
  
  // Toggle HUD expansion
  window.dispatchEvent(new CustomEvent('jarvis-hud-toggle'))
}

function onLongPress() {
  console.log('[JARVIS] ✋ Long press — Talk to JARVIS')
  
  try { navigator.vibrate?.([50, 30, 50]) } catch {}
  
  // v32: Navigate to chat only, no auto-speech
  window.dispatchEvent(new CustomEvent('jarvis-navigate', { detail: { path: '/chat' } }))
}

// ═══ INITIALIZATION ═══
function init() {
  initShakeDetection()
  initDoubleTap()
}

function setShakeEnabled(val) { shakeEnabled = !!val }

const jarvisGestures = {
  init,
  onShake,
  onDoubleTap,
  onLongPress,
  setShakeEnabled,
}

export default jarvisGestures
export { init, onShake, onDoubleTap, onLongPress }
