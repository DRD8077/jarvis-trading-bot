/**
 * ⚔️ JARVIS BATTLE HUD — Iron Man Targeting & Market Overlay
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like Iron Man's HUD in combat:
 * - Target lock on specific coins/stocks (price tracking)
 * - Support/Resistance levels displayed
 * - Buy/Sell zones with color coding
 * - Distance to target (how far from your entry/exit)
 * - Threat level per target
 * - Auto-updates every 10 seconds
 * 
 * "Sir, I've locked onto BTC. Target: $105,000. Current distance: 2.3%"
 */

let targets = []
let updateInterval = null
let isActive = false

/**
 * Add a target to track (like Iron Man locking onto an enemy)
 */
function lockTarget(symbol, entryPrice, targetPrice, stopLoss) {
  const existing = targets.find(t => t.symbol === symbol)
  if (existing) {
    // Update existing target
    existing.entryPrice = entryPrice || existing.entryPrice
    existing.targetPrice = targetPrice || existing.targetPrice
    existing.stopLoss = stopLoss || existing.stopLoss
    existing.updatedAt = Date.now()
  } else {
    targets.push({
      symbol: symbol.toUpperCase(),
      entryPrice: entryPrice || 0,
      targetPrice: targetPrice || 0,
      stopLoss: stopLoss || 0,
      currentPrice: 0,
      change24h: 0,
      distanceToTarget: 0,
      distanceToSL: 0,
      status: 'TRACKING', // TRACKING, TARGET_HIT, SL_HIT, DANGER
      lockedAt: Date.now(),
      updatedAt: Date.now(),
    })
  }

  // Save to localStorage
  _save()

  // Start updates if not running
  if (!updateInterval) _startUpdates()

  window.dispatchEvent(new CustomEvent('jarvis-battle-update', { detail: { targets } }))
  return targets
}

/**
 * Remove a target
 */
function unlockTarget(symbol) {
  targets = targets.filter(t => t.symbol !== symbol.toUpperCase())
  _save()
  window.dispatchEvent(new CustomEvent('jarvis-battle-update', { detail: { targets } }))
}

/**
 * Get all locked targets
 */
function getTargets() {
  return [...targets]
}

/**
 * Update all target prices from CoinGecko
 */
async function updatePrices() {
  if (targets.length === 0) return

  try {
    // Map common symbols to CoinGecko IDs
    const symbolMap = {
      'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
      'BNB': 'binancecoin', 'XRP': 'ripple', 'ADA': 'cardano',
      'DOGE': 'dogecoin', 'AVAX': 'avalanche-2', 'DOT': 'polkadot',
      'MATIC': 'matic-network', 'LINK': 'chainlink', 'UNI': 'uniswap',
      'SHIB': 'shiba-inu', 'LTC': 'litecoin', 'ATOM': 'cosmos',
      'NEAR': 'near', 'APT': 'aptos', 'ARB': 'arbitrum', 'OP': 'optimism',
      'SUI': 'sui', 'SEI': 'sei-network', 'INJ': 'injective-protocol',
      'TIA': 'celestia', 'JUP': 'jupiter-exchange-solana', 'WIF': 'dogwifcoin',
      'PEPE': 'pepe', 'BONK': 'bonk', 'FLOKI': 'floki',
    }

    const ids = targets.map(t => symbolMap[t.symbol] || t.symbol.toLowerCase()).filter(Boolean)
    if (ids.length === 0) return

    const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids.join(',')}&vs_currencies=usd&include_24hr_change=true`)
    if (!res.ok) return
    const data = await res.json()

    targets.forEach(t => {
      const id = symbolMap[t.symbol] || t.symbol.toLowerCase()
      const priceData = data[id]
      if (priceData) {
        t.currentPrice = priceData.usd || 0
        t.change24h = priceData.usd_24h_change || 0

        // Calculate distances
        if (t.targetPrice > 0 && t.currentPrice > 0) {
          t.distanceToTarget = ((t.targetPrice - t.currentPrice) / t.currentPrice * 100).toFixed(2)
        }
        if (t.stopLoss > 0 && t.currentPrice > 0) {
          t.distanceToSL = ((t.currentPrice - t.stopLoss) / t.currentPrice * 100).toFixed(2)
        }

        // Status checks
        if (t.targetPrice > 0 && t.currentPrice >= t.targetPrice) {
          t.status = 'TARGET_HIT'
        } else if (t.stopLoss > 0 && t.currentPrice <= t.stopLoss) {
          t.status = 'SL_HIT'
        } else if (t.distanceToSL < 2) {
          t.status = 'DANGER'
        } else {
          t.status = 'TRACKING'
        }

        t.updatedAt = Date.now()
      }
    })

    _save()
    window.dispatchEvent(new CustomEvent('jarvis-battle-update', { detail: { targets } }))

    // Alert on target hit or SL hit
    const hits = targets.filter(t => t.status === 'TARGET_HIT' || t.status === 'SL_HIT')
    hits.forEach(t => {
      if (t.status === 'TARGET_HIT') {
        window.dispatchEvent(new CustomEvent('jarvis-speak', {
          detail: { text: `Sir, TARGET HIT! ${t.symbol} ne ${t.targetPrice} dollar touch kar liya! Position close karna chahenge?`, priority: 'high' }
        }))
      } else if (t.status === 'SL_HIT') {
        window.dispatchEvent(new CustomEvent('jarvis-speak', {
          detail: { text: `WARNING Sir! ${t.symbol} ne stop loss ${t.stopLoss} dollar hit kiya! Emergency action needed!`, priority: 'high' }
        }))
      }
    })

  } catch (e) {
    console.warn('[Battle HUD] Price update error:', e.message)
  }
}

/**
 * Get battle summary for voice
 */
function getBattleSummary() {
  if (targets.length === 0) return 'Sir, koi target lock nahi hai abhi. Kisi coin ko track karna hai toh bataiye.'

  const summaries = targets.map(t => {
    const dir = t.change24h >= 0 ? 'upar' : 'neeche'
    return `${t.symbol}: ${t.currentPrice.toLocaleString()} dollar, ${Math.abs(t.change24h).toFixed(1)}% ${dir}. Target se ${Math.abs(t.distanceToTarget)}% door.`
  })

  return `Sir, ${targets.length} targets locked hain. ${summaries.join(' ')}` 
}

function _startUpdates() {
  updatePrices() // Initial fetch
  updateInterval = setInterval(updatePrices, 15000) // Every 15 seconds
  isActive = true
}

function _save() {
  try {
    localStorage.setItem('jarvis_battle_targets', JSON.stringify(targets))
  } catch {}
}

function _restore() {
  try {
    const saved = localStorage.getItem('jarvis_battle_targets')
    if (saved) {
      targets = JSON.parse(saved)
      if (targets.length > 0) _startUpdates()
    }
  } catch {}
}

function init() {
  _restore()
  console.log(`[Battle HUD] ⚔️ ${targets.length} targets loaded`)
}

function destroy() {
  if (updateInterval) clearInterval(updateInterval)
  updateInterval = null
  isActive = false
}

const jarvisBattleHUD = {
  lockTarget, unlockTarget, getTargets, updatePrices,
  getBattleSummary, init, destroy, isActive: () => isActive,
}

export default jarvisBattleHUD
export { lockTarget, unlockTarget, getTargets, updatePrices, getBattleSummary }
