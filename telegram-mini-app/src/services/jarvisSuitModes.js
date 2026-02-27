/**
 * 🦾 JARVIS SUIT MODES — Iron Man Combat/Stealth/Recon Modes
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like Tony Stark switching between suits:
 * 
 * STEALTH MODE (Mark XV Sneaky):
 * - Minimal voice, no proactive alerts, dark silent mode
 * - For when you want to quietly monitor without distractions
 * 
 * COMBAT MODE (Mark XLIV Hulkbuster):
 * - Aggressive trading alerts, every micro-movement announced
 * - Maximum voice, fastest scan intervals, zero delay alerts
 * 
 * RECON MODE (Mark XVII Heartbreaker):
 * - Scanning focus — finds gems, analyzes data, no trading
 * - JARVIS focuses on research and intelligence gathering
 * 
 * GUARDIAN MODE (Mark XXV Striker):
 * - Portfolio protection — monitors stops, warns about losses
 * - Risk-first approach, JARVIS warns before every action
 * 
 * AUTOPILOT MODE (Mark XLII):
 * - JARVIS handles everything — auto-scan, auto-trade, auto-alert
 * - Minimal user intervention needed
 */

const SUIT_MODES = {
  standard: {
    id: 'standard',
    name: 'Standard',
    subtitle: 'Mark III — Balanced',
    icon: '🦾',
    color: '#3b82f6',
    description: 'Default balanced mode. JARVIS speaks normally, scans regularly.',
    voiceLevel: 'normal',      // low, normal, high, maximum
    scanInterval: 5,           // minutes
    alertThreshold: 'medium',  // low, medium, high, extreme
    autoTrade: false,
    proactiveAlerts: true,
    soundEffects: true,
  },
  stealth: {
    id: 'stealth',
    name: 'Stealth',
    subtitle: 'Mark XV — Sneaky',
    icon: '🥷',
    color: '#64748b',
    description: 'Silent mode. No voice, no sounds. Just visual alerts. Pure stealth.',
    voiceLevel: 'off',
    scanInterval: 15,
    alertThreshold: 'extreme', // only critical alerts
    autoTrade: false,
    proactiveAlerts: false,
    soundEffects: false,
  },
  combat: {
    id: 'combat',
    name: 'Combat',
    subtitle: 'Mark XLIV — Hulkbuster',
    icon: '⚔️',
    color: '#ef4444',
    description: 'Maximum aggression! Every movement announced. Fastest scans. Full power!',
    voiceLevel: 'maximum',
    scanInterval: 1,
    alertThreshold: 'low',  // alert on everything
    autoTrade: false,
    proactiveAlerts: true,
    soundEffects: true,
  },
  recon: {
    id: 'recon',
    name: 'Recon',
    subtitle: 'Mark XVII — Heartbreaker',
    icon: '🔍',
    color: '#8b5cf6',
    description: 'Intelligence gathering. JARVIS focuses on finding gems and analysis.',
    voiceLevel: 'normal',
    scanInterval: 3,
    alertThreshold: 'medium',
    autoTrade: false,
    proactiveAlerts: true,
    soundEffects: true,
  },
  guardian: {
    id: 'guardian',
    name: 'Guardian',
    subtitle: 'Mark XXV — Striker',
    icon: '🛡️',
    color: '#22c55e',
    description: 'Portfolio protection. Warns before losses. Risk-first approach.',
    voiceLevel: 'high',
    scanInterval: 2,
    alertThreshold: 'medium',
    autoTrade: false,
    proactiveAlerts: true,
    soundEffects: true,
  },
  autopilot: {
    id: 'autopilot',
    name: 'Autopilot',
    subtitle: 'Mark XLII — Full Auto',
    icon: '🤖',
    color: '#06b6d4',
    description: 'JARVIS handles everything. Auto-scan, auto-alert, maximum AI assistance.',
    voiceLevel: 'high',
    scanInterval: 2,
    alertThreshold: 'low',
    autoTrade: true,
    proactiveAlerts: true,
    soundEffects: true,
  },
}

const STORAGE_KEY = 'jarvis_suit_mode'
let currentMode = 'standard'

// Load saved mode
try {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && SUIT_MODES[saved]) currentMode = saved
} catch {}

function setMode(modeId) {
  if (!SUIT_MODES[modeId]) return false
  currentMode = modeId
  try { localStorage.setItem(STORAGE_KEY, modeId) } catch {}
  
  const mode = SUIT_MODES[modeId]
  
  // Apply voice level
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('jarvis-mode-change', { detail: mode }))
  }
  
  // Announce mode change
  const announcements = {
    standard: 'Standard mode activated Sir. Balanced operations. Sab systems normal.',
    stealth: 'Stealth mode engaged Sir. Going silent. Sirf critical alerts milenge.',
    combat: 'COMBAT MODE ACTIVATED! Full power Sir! Maximum aggression. Har movement pe alert milega!',
    recon: 'Recon mode Sir. Intelligence gathering focus. Gems aur analysis pe dhyan hai.',
    guardian: 'Guardian mode active Sir. Portfolio protection priority. Risk warnings maximum.',
    autopilot: 'Autopilot engaged Sir. Main sab handle karungi. Aap relax kariye. JARVIS in control.',
  }
  
  if (mode.voiceLevel !== 'off') {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: announcements[modeId] || `${mode.name} mode activated.`, priority: 'high' }
    }))
  }
  
  // Apply scan interval to proactive brain
  try {
    const brain = window.__jarvisProactiveBrain
    if (brain) {
      // Restart with new interval
      brain.stop?.()
      brain.start?.()
    }
  } catch {}
  
  // Apply sound effects setting
  try {
    import('./jarvisSoundFX.js').then(m => {
      const sfx = m.default || m
      if (sfx?.setEnabled) sfx.setEnabled(mode.soundEffects)
    })
  } catch {}
  
  return true
}

function getMode() {
  return SUIT_MODES[currentMode] || SUIT_MODES.standard
}

function getModeId() {
  return currentMode
}

function getAllModes() {
  return Object.values(SUIT_MODES)
}

function shouldSpeak() {
  return getMode().voiceLevel !== 'off'
}

function shouldAlert(severity = 'medium') {
  const thresholds = { low: 1, medium: 2, high: 3, extreme: 4 }
  const current = thresholds[getMode().alertThreshold] || 2
  const severityLevel = thresholds[severity] || 2
  return severityLevel >= current
}

function getScanInterval() {
  return (getMode().scanInterval || 5) * 60 * 1000
}

const jarvisSuitModes = {
  setMode,
  getMode,
  getModeId,
  getAllModes,
  shouldSpeak,
  shouldAlert,
  getScanInterval,
  SUIT_MODES,
}

export default jarvisSuitModes
export { setMode, getMode, getModeId, getAllModes, shouldSpeak, shouldAlert }
