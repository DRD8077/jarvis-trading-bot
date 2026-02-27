/**
 * 🚨 JARVIS EMERGENCY PROTOCOLS — Iron Man Movie-Accurate Crisis Response
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Like in the Iron Man movies:
 * - "House Party Protocol" — deploy ALL suits (activate all scanners + defenses)
 * - "Veronica Protocol" — deploy Hulkbuster (maximum defense mode)
 * - "Clean Slate Protocol" — close all positions (emergency exit)
 * - "Lullaby Protocol" — gradual de-risk (soft stop-loss mode)
 * - "Avengers Protocol" — alert all channels (push + voice + visual)
 * - "Mark 42 Protocol" — autonomous trading (full auto-pilot)
 * 
 * Each protocol triggers a coordinated sequence of automated actions.
 */

const PROTOCOLS = {
  // ═══ HOUSE PARTY — Deploy ALL defenses (Iron Man 3) ═══
  'house-party': {
    name: 'House Party Protocol',
    codename: 'HOUSE PARTY',
    icon: '🎉',
    color: '#f59e0b',
    description: 'Deploy all Iron Legion — activate every scanner and defense system',
    hindiAnnouncement: 'Sir, House Party Protocol activated! Saare suits deploy ho rahe hain. Har scanner, har defense system ONLINE!',
    actions: ['activate-all-scanners', 'enable-all-alerts', 'force-brain-scan', 'max-threat-monitor', 'enable-whale-watch'],
    suitMode: 'combat',
    duration: 30 * 60 * 1000, // 30 minutes
  },

  // ═══ VERONICA — Maximum defense (Age of Ultron) ═══
  'veronica': {
    name: 'Veronica Protocol',
    codename: 'VERONICA',
    icon: '🛡️',
    color: '#ef4444',
    description: 'Deploy Hulkbuster — maximum portfolio defense, all stop-losses activated',
    hindiAnnouncement: 'Sir, Veronica Protocol! Hulkbuster deployed! Sabhi stop-losses activate, portfolio ko maximum protection diya ja raha hai!',
    actions: ['tighten-stop-losses', 'enable-guardian-mode', 'hedge-positions', 'emergency-alerts-only'],
    suitMode: 'guardian',
    duration: 60 * 60 * 1000, // 1 hour
  },

  // ═══ CLEAN SLATE — Emergency exit (Iron Man 3) ═══
  'clean-slate': {
    name: 'Clean Slate Protocol',
    codename: 'CLEAN SLATE',
    icon: '💥',
    color: '#dc2626',
    description: 'Self-destruct all positions — emergency close everything',
    hindiAnnouncement: 'Sir, CLEAN SLATE PROTOCOL! Ye bahut bada decision hai. Saari positions close ho rahi hain. Emergency exit!',
    actions: ['close-all-positions', 'cancel-pending-orders', 'disable-auto-trade', 'notify-emergency'],
    suitMode: 'standard',
    duration: 0, // Immediate, no duration
    requiresConfirmation: true,
  },

  // ═══ LULLABY — Gradual de-risk (Age of Ultron) ═══
  'lullaby': {
    name: 'Lullaby Protocol',
    codename: 'LULLABY',
    icon: '🌙',
    color: '#8b5cf6',
    description: 'Gradual de-risk — tighten stops, reduce exposure slowly',
    hindiAnnouncement: 'Sir, Lullaby Protocol. Hulk ko sula rahe hain. Positions gradually reduce ho rahi hain, risk kam ho raha hai.',
    actions: ['gradual-stop-tighten', 'reduce-position-sizes', 'lower-risk-tolerance', 'enable-trailing-stops'],
    suitMode: 'guardian',
    duration: 2 * 60 * 60 * 1000, // 2 hours
  },

  // ═══ AVENGERS — Maximum alert mode ═══
  'avengers': {
    name: 'Avengers Protocol',
    codename: 'AVENGERS ASSEMBLE',
    icon: '⚡',
    color: '#3b82f6',
    description: 'Alert ALL channels — voice, visual, push, vibrate — maximum awareness',
    hindiAnnouncement: 'Sir, Avengers Assemble! Saare alert channels activate! Voice, visual, push notifications, vibration — sab ON!',
    actions: ['enable-all-notifications', 'enable-voice-alerts', 'enable-vibration', 'max-scan-frequency', 'enable-emergency-sounds'],
    suitMode: 'combat',
    duration: 60 * 60 * 1000, // 1 hour
  },

  // ═══ MARK 42 — Autonomous mode (Iron Man 3) ═══
  'mark-42': {
    name: 'Mark 42 Protocol',
    codename: 'MARK 42',
    icon: '🤖',
    color: '#06b6d4',
    description: 'Full autonomous trading — JARVIS handles everything',
    hindiAnnouncement: 'Sir, Mark 42 Protocol! Autonomous mode engaged. Main khud sab handle karungi. Aap aaram kariye!',
    actions: ['enable-auto-trade', 'enable-auto-stop-loss', 'enable-auto-take-profit', 'full-brain-scan'],
    suitMode: 'autopilot',
    duration: 4 * 60 * 60 * 1000, // 4 hours
  },

  // ═══ FRIDAY — Backup AI mode ═══
  'friday': {
    name: 'FRIDAY Protocol',
    codename: 'FRIDAY BACKUP',
    icon: '🔄',
    color: '#22c55e',
    description: 'Switch to FRIDAY personality — more cautious, risk-averse approach',
    hindiAnnouncement: 'Sir, Friday Protocol activated. Main FRIDAY mode mein switch ho rahi hoon. Zyada cautious approach.',
    actions: ['switch-personality-friday', 'conservative-trading', 'extra-confirmation'],
    suitMode: 'guardian',
    duration: 0, // Permanent until changed
  },
}

// Active protocol state
let activeProtocol = null
let protocolTimer = null
let protocolHistory = []

/**
 * Activate an emergency protocol
 * @param {string} protocolId - Protocol key
 * @param {boolean} skipConfirmation - Force activate without confirmation
 * @returns {{ success: boolean, protocol: object }}
 */
function activateProtocol(protocolId, skipConfirmation = false) {
  const protocol = PROTOCOLS[protocolId]
  if (!protocol) {
    console.warn('[JARVIS Protocols] Unknown protocol:', protocolId)
    return { success: false, error: 'Unknown protocol' }
  }

  // Check if requires confirmation
  if (protocol.requiresConfirmation && !skipConfirmation) {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: `Sir, ${protocol.codename} Protocol bahut extreme hai. Kya aap sure hain? Fir se boliye "Confirm ${protocol.codename}" to activate.`, priority: 'critical' }
    }))
    window.__pendingProtocol = protocolId
    return { success: false, needsConfirmation: true, protocol }
  }

  // Clear any existing protocol timer
  if (protocolTimer) {
    clearTimeout(protocolTimer)
    protocolTimer = null
  }

  console.log(`[JARVIS Protocols] 🚨 ACTIVATING: ${protocol.codename}`)

  // Set active protocol
  activeProtocol = { ...protocol, id: protocolId, activatedAt: Date.now() }

  // Record in history
  protocolHistory.push({
    id: protocolId,
    name: protocol.codename,
    activatedAt: Date.now(),
  })

  // Save to localStorage
  try {
    localStorage.setItem('jarvis_active_protocol', JSON.stringify(activeProtocol))
    localStorage.setItem('jarvis_protocol_history', JSON.stringify(protocolHistory.slice(-20)))
  } catch {}

  // Announce
  window.dispatchEvent(new CustomEvent('jarvis-speak', {
    detail: { text: protocol.hindiAnnouncement, priority: 'critical' }
  }))

  // Dispatch visual event
  window.dispatchEvent(new CustomEvent('jarvis-protocol-activated', { detail: activeProtocol }))

  // Emergency visual if critical protocol
  if (['clean-slate', 'veronica', 'house-party'].includes(protocolId)) {
    window.dispatchEvent(new CustomEvent('jarvis-emergency', { detail: { symbol: protocol.codename, protocol: true } }))
  }

  // Execute actions
  executeProtocolActions(protocol.actions)

  // Switch suit mode
  if (protocol.suitMode) {
    import('./jarvisSuitModes.js').then(m => {
      const modes = m.default || m
      if (modes?.setMode) modes.setMode(protocol.suitMode)
    }).catch(() => {})
  }

  // Play sound
  import('./jarvisSoundFX.js').then(m => {
    const sfx = m.default || m
    if (sfx?.emergency) sfx.emergency()
  }).catch(() => {})

  // Set auto-deactivate timer
  if (protocol.duration > 0) {
    protocolTimer = setTimeout(() => {
      deactivateProtocol()
    }, protocol.duration)

    // Announce halfway
    setTimeout(() => {
      if (activeProtocol?.id === protocolId) {
        window.dispatchEvent(new CustomEvent('jarvis-speak', {
          detail: { text: `Sir, ${protocol.codename} Protocol ka aadha time ho gaya. ${Math.round(protocol.duration / 60000 / 2)} minute baaki hain.`, priority: 'high' }
        }))
      }
    }, protocol.duration / 2)
  }

  return { success: true, protocol: activeProtocol }
}

/**
 * Execute protocol actions (simulated — triggers corresponding events)
 */
function executeProtocolActions(actions) {
  if (!actions || !actions.length) return

  actions.forEach(action => {
    console.log(`[JARVIS Protocols] Executing: ${action}`)

    switch (action) {
      case 'force-brain-scan':
      case 'full-brain-scan':
        import('./jarvisProactiveBrain.js').then(m => {
          const brain = m.default || m
          if (brain?.scanNow) brain.scanNow()
        }).catch(() => {})
        break

      case 'enable-guardian-mode':
        import('./jarvisSuitModes.js').then(m => {
          const modes = m.default || m
          if (modes?.setMode) modes.setMode('guardian')
        }).catch(() => {})
        break

      case 'activate-all-scanners':
      case 'max-scan-frequency':
        window.dispatchEvent(new CustomEvent('jarvis-brain-scan'))
        break

      case 'enable-all-notifications':
      case 'enable-all-alerts':
      case 'enable-voice-alerts':
      case 'enable-emergency-sounds':
        // v32: NEVER force-unmute — respect user's sound preferences
        console.log('[JARVIS Protocols] Sound action requested but respecting user mute settings')
        break

      case 'enable-vibration':
        try { navigator.vibrate([200, 100, 200, 100, 400]) } catch {}
        break

      case 'disable-auto-trade':
        window.__JARVIS_AUTO_TRADE_DISABLED = true
        break

      case 'enable-auto-trade':
        window.__JARVIS_AUTO_TRADE_DISABLED = false
        break

      default:
        // Log unhandled action for future implementation
        console.log(`[JARVIS Protocols] Action queued: ${action}`)
    }
  })
}

/**
 * Deactivate current protocol
 */
function deactivateProtocol() {
  if (!activeProtocol) return

  const name = activeProtocol.codename
  console.log(`[JARVIS Protocols] Deactivating: ${name}`)

  // v33: Silent deactivation — no speech (was triggering on boot when restored timer expires)
  console.log(`[JARVIS Protocols] ${name} Protocol deactivated. Normal operations resumed.`)

  // Reset to standard
  import('./jarvisSuitModes.js').then(m => {
    const modes = m.default || m
    if (modes?.setMode) modes.setMode('standard')
  }).catch(() => {})

  activeProtocol = null
  if (protocolTimer) {
    clearTimeout(protocolTimer)
    protocolTimer = null
  }

  try { localStorage.removeItem('jarvis_active_protocol') } catch {}

  window.dispatchEvent(new CustomEvent('jarvis-protocol-deactivated'))
}

/**
 * Get active protocol info
 */
function getActiveProtocol() {
  return activeProtocol
}

/**
 * Get protocol history
 */
function getProtocolHistory() {
  if (!protocolHistory.length) {
    try {
      protocolHistory = JSON.parse(localStorage.getItem('jarvis_protocol_history') || '[]')
    } catch {}
  }
  return protocolHistory
}

/**
 * Get all available protocols
 */
function getProtocols() {
  return PROTOCOLS
}

/**
 * Restore active protocol from localStorage on boot
 */
function restore() {
  try {
    const saved = JSON.parse(localStorage.getItem('jarvis_active_protocol'))
    if (saved && saved.id) {
      const elapsed = Date.now() - (saved.activatedAt || 0)
      if (saved.duration && elapsed >= saved.duration) {
        // Protocol expired
        localStorage.removeItem('jarvis_active_protocol')
        return null
      }
      activeProtocol = saved
      // Re-set timer for remaining duration
      if (saved.duration > 0) {
        const remaining = saved.duration - elapsed
        protocolTimer = setTimeout(() => deactivateProtocol(), remaining)
      }
      console.log(`[JARVIS Protocols] Restored: ${saved.codename}`)
      return saved
    }
  } catch {}
  return null
}

const jarvisEmergencyProtocols = {
  activateProtocol,
  deactivateProtocol,
  getActiveProtocol,
  getProtocols,
  getProtocolHistory,
  restore,
  executeProtocolActions,
  PROTOCOLS,
}

export default jarvisEmergencyProtocols
export { activateProtocol, deactivateProtocol, getActiveProtocol, getProtocols, restore }
