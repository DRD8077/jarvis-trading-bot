/**
 * 🔊 JARVIS SOUND EFFECTS ENGINE — Iron Man Audio
 * ═══════════════════════════════════════════════════
 * 
 * All sounds generated via Web Audio API — no external files needed!
 * Iron Man signature sounds:
 * - Startup chime (arc reactor power-up)
 * - Alert beep (warning tone)
 * - Confirmation tone (success chime)
 * - Scan sweep (radar-like sweep)
 * - Error buzz (failure indicator)
 * - Emergency klaxon (red alert)
 * - Typing tick (data processing)
 * - Navigation whoosh (page transition)
 */

let audioCtx = null
let enabled = true
const VOLUME = 0.15 // Keep subtle — not annoyingly loud

function getContext() {
  if (!audioCtx) {
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    } catch { return null }
  }
  if (audioCtx.state === 'suspended') audioCtx.resume().catch(() => {})
  return audioCtx
}

function playTone(freq, duration, type = 'sine', volumeMultiplier = 1) {
  if (!enabled) return
  const ctx = getContext()
  if (!ctx) return
  try {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = type
    osc.frequency.value = freq
    gain.gain.setValueAtTime(VOLUME * volumeMultiplier, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + duration)
  } catch {}
}

// ═══ IRON MAN SOUND EFFECTS ═══

/** Arc reactor startup — ascending tones like powering up */
function startup() {
  if (!enabled) return
  const ctx = getContext()
  if (!ctx) return
  try {
    const freqs = [200, 300, 450, 600, 800, 1000, 1200]
    freqs.forEach((f, i) => {
      setTimeout(() => playTone(f, 0.15, 'sine', 0.6), i * 60)
    })
    // Final shimmer
    setTimeout(() => playTone(1500, 0.4, 'sine', 0.4), 450)
    setTimeout(() => playTone(2000, 0.3, 'sine', 0.3), 550)
  } catch {}
}

/** Confirmation chime — two ascending notes */
function confirm() {
  playTone(800, 0.1, 'sine', 0.5)
  setTimeout(() => playTone(1200, 0.15, 'sine', 0.5), 100)
}

/** Alert beep — attention-getting double beep */
function alert() {
  playTone(1000, 0.08, 'square', 0.3)
  setTimeout(() => playTone(1000, 0.08, 'square', 0.3), 150)
}

/** Warning — descending tone */
function warning() {
  playTone(800, 0.15, 'sawtooth', 0.2)
  setTimeout(() => playTone(600, 0.2, 'sawtooth', 0.2), 150)
}

/** Error buzz — low harsh tone */
function error() {
  playTone(200, 0.3, 'sawtooth', 0.3)
  setTimeout(() => playTone(150, 0.2, 'sawtooth', 0.25), 200)
}

/** Emergency klaxon — urgent repeating alert */
function emergency() {
  for (let i = 0; i < 4; i++) {
    setTimeout(() => {
      playTone(800, 0.1, 'square', 0.4)
      setTimeout(() => playTone(600, 0.1, 'square', 0.4), 120)
    }, i * 300)
  }
}

/** Scan sweep — rising frequency sweep */
function scan() {
  if (!enabled) return
  const ctx = getContext()
  if (!ctx) return
  try {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(300, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(2000, ctx.currentTime + 0.5)
    gain.gain.setValueAtTime(VOLUME * 0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.6)
  } catch {}
}

/** Navigation whoosh — quick frequency sweep */
function navigate() {
  if (!enabled) return
  const ctx = getContext()
  if (!ctx) return
  try {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(1500, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(500, ctx.currentTime + 0.15)
    gain.gain.setValueAtTime(VOLUME * 0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.2)
  } catch {}
}

/** Tick — tiny data processing click */
function tick() {
  playTone(2000, 0.02, 'sine', 0.2)
}

/** Speak start — JARVIS about to talk indicator */
function speakStart() {
  playTone(600, 0.05, 'sine', 0.3)
  setTimeout(() => playTone(900, 0.08, 'sine', 0.3), 60)
}

/** Gem found — exciting discovery chime */
function gemFound() {
  const notes = [523, 659, 784, 1047] // C5, E5, G5, C6
  notes.forEach((f, i) => {
    setTimeout(() => playTone(f, 0.12, 'sine', 0.5), i * 80)
  })
}

/** Trade executed — decisive confirmation */
function tradeExecuted() {
  playTone(400, 0.08, 'sine', 0.4)
  setTimeout(() => playTone(600, 0.08, 'sine', 0.4), 80)
  setTimeout(() => playTone(800, 0.15, 'sine', 0.5), 160)
}

/** Profit — happy ascending arpeggio */
function profit() {
  const notes = [523, 659, 784, 1047, 1318]
  notes.forEach((f, i) => {
    setTimeout(() => playTone(f, 0.1, 'sine', 0.4), i * 70)
  })
}

/** Loss — somber descending notes */
function loss() {
  playTone(500, 0.2, 'sine', 0.3)
  setTimeout(() => playTone(400, 0.2, 'sine', 0.3), 200)
  setTimeout(() => playTone(300, 0.3, 'sine', 0.2), 400)
}

// ═══ AUTO-TRIGGER ON JARVIS EVENTS ═══
if (typeof window !== 'undefined') {
  window.addEventListener('jarvis-speak', () => speakStart())
  window.addEventListener('jarvis-emergency', () => emergency())
  window.addEventListener('jarvis-brain-scan', () => scan())
  window.addEventListener('jarvis-gem-found', () => gemFound())
  window.addEventListener('jarvis-trade', (e) => {
    const type = e.detail?.type
    if (type === 'profit' || type === 'take-profit') profit()
    else if (type === 'loss' || type === 'stop-loss') loss()
    else tradeExecuted()
  })
  window.addEventListener('jarvis-navigate', () => navigate())
}

function setEnabled(val) { enabled = !!val }
function isEnabled() { return enabled }

const jarvisSoundFX = {
  startup, confirm, alert, warning, error, emergency,
  scan, navigate, tick, speakStart, gemFound, tradeExecuted,
  profit, loss, setEnabled, isEnabled, getContext,
}

export default jarvisSoundFX
export { startup, confirm, alert, warning, error, emergency, scan, navigate, tick, speakStart, gemFound, tradeExecuted, profit, loss }
