/**
 * ⚡ JARVIS ARC REACTOR — Power Level & Energy System
 * ═══════════════════════════════════════════════════════
 * 
 * Like Tony Stark's Arc Reactor powering the suit:
 * - Power level = how hard JARVIS is working (0-100%)
 * - Increases when scanning, analyzing, trading
 * - Drains slowly during idle
 * - Overload warning when processing too much
 * - Affects HUD color and animation speed
 * - Visual indicator always on screen
 * 
 * Powers:
 * - Voice module: 5% per speak
 * - Brain scan: 15% per scan
 * - Trade execution: 20%
 * - Hologram projection: 25%
 * - Emergency protocol: 30%
 * - Each page navigation: 2%
 * - Background monitoring: 1% per minute
 */

let powerLevel = 100 // Starts fully charged
let maxPower = 100
let drainRate = 0.5 // % per minute idle drain
let rechargeRate = 2 // % per minute passive recharge
let isOverloaded = false
let powerHistory = []
let drainInterval = null

// Power costs for actions
const POWER_COSTS = {
  speak: 3,
  scan: 10,
  trade: 15,
  hologram: 20,
  protocol: 25,
  navigate: 1,
  alert: 5,
  prediction: 12,
  gemScan: 8,
  backgroundMonitor: 0.5,
}

/**
 * Initialize the arc reactor
 */
function init() {
  // Restore power level
  try {
    const saved = localStorage.getItem('jarvis_arc_power')
    if (saved) {
      const parsed = JSON.parse(saved)
      // Time-based recharge while away
      const minutesAway = (Date.now() - (parsed.timestamp || 0)) / 60000
      powerLevel = Math.min(maxPower, (parsed.level || 50) + minutesAway * rechargeRate)
    }
  } catch {}

  // Passive power management — recharge over time
  drainInterval = setInterval(() => {
    // Slow recharge when idle
    if (powerLevel < maxPower) {
      powerLevel = Math.min(maxPower, powerLevel + rechargeRate / 60)
    }

    // Save periodically
    try {
      localStorage.setItem('jarvis_arc_power', JSON.stringify({ level: powerLevel, timestamp: Date.now() }))
    } catch {}

    // Power history
    powerHistory.push({ level: powerLevel, time: Date.now() })
    if (powerHistory.length > 60) powerHistory = powerHistory.slice(-60) // Keep 1 hour

    // Dispatch power update
    window.dispatchEvent(new CustomEvent('jarvis-power-update', { detail: { level: powerLevel, max: maxPower, overloaded: isOverloaded } }))
  }, 10000) // Every 10 seconds

  // Listen for power-consuming events
  window.addEventListener('jarvis-speak', () => consumePower('speak'))
  window.addEventListener('jarvis-brain-scan', () => consumePower('scan'))
  window.addEventListener('jarvis-trade', () => consumePower('trade'))
  window.addEventListener('jarvis-emergency', () => consumePower('protocol'))
  window.addEventListener('jarvis-navigate', () => consumePower('navigate'))
  window.addEventListener('jarvis-gem-found', () => consumePower('gemScan'))

  console.log(`[JARVIS Arc Reactor] ⚡ Power: ${Math.round(powerLevel)}%`)
  return powerLevel
}

/**
 * Consume power for an action
 */
function consumePower(action) {
  const cost = POWER_COSTS[action] || 1
  powerLevel = Math.max(0, powerLevel - cost)

  // Check overload (below 10%)
  if (powerLevel < 10 && !isOverloaded) {
    isOverloaded = true
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Sir, Arc Reactor power critical! Sirf 10 percent power bachi hai. Non-essential systems shutdown ho rahe hain.', priority: 'critical' }
    }))
    window.dispatchEvent(new CustomEvent('jarvis-power-critical'))
  } else if (powerLevel >= 20 && isOverloaded) {
    isOverloaded = false
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Arc Reactor power restored Sir. Systems normalizing.', priority: 'high' }
    }))
  }

  // Low power warning at 25%
  if (powerLevel < 25 && powerLevel >= 24) {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Sir, power level 25 percent. Energy conservation mode recommended.', priority: 'medium' }
    }))
  }

  window.dispatchEvent(new CustomEvent('jarvis-power-update', {
    detail: { level: powerLevel, max: maxPower, overloaded: isOverloaded, action, cost }
  }))
}

/**
 * Recharge power (manual boost)
 */
function recharge(amount = 30) {
  powerLevel = Math.min(maxPower, powerLevel + amount)
  window.dispatchEvent(new CustomEvent('jarvis-speak', {
    detail: { text: `Arc Reactor recharged! Power level ab ${Math.round(powerLevel)} percent hai Sir.`, priority: 'high' }
  }))
  window.dispatchEvent(new CustomEvent('jarvis-power-update', { detail: { level: powerLevel, max: maxPower, overloaded: isOverloaded } }))
}

/**
 * Get current power level
 */
function getPowerLevel() {
  return Math.round(powerLevel)
}

/**
 * Get power status object
 */
function getStatus() {
  return {
    level: Math.round(powerLevel),
    max: maxPower,
    overloaded: isOverloaded,
    color: powerLevel > 60 ? '#22d3ee' : powerLevel > 30 ? '#f59e0b' : '#ef4444',
    label: powerLevel > 80 ? 'OPTIMAL' : powerLevel > 50 ? 'NOMINAL' : powerLevel > 25 ? 'LOW' : powerLevel > 10 ? 'CRITICAL' : 'EMERGENCY',
    history: powerHistory,
  }
}

/**
 * Check if we have enough power for an action
 */
function canPerform(action) {
  const cost = POWER_COSTS[action] || 1
  return powerLevel >= cost
}

/**
 * Cleanup
 */
function destroy() {
  if (drainInterval) clearInterval(drainInterval)
}

const jarvisArcReactor = {
  init,
  consumePower,
  recharge,
  getPowerLevel,
  getStatus,
  canPerform,
  destroy,
  POWER_COSTS,
}

export default jarvisArcReactor
export { init, consumePower, recharge, getPowerLevel, getStatus, canPerform }
