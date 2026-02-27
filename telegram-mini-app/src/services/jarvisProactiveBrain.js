/**
 * 🧠 JARVIS PROACTIVE BRAIN — Iron Man Level Intelligence
 * ═══════════════════════════════════════════════════════════
 * 
 * In Iron Man, JARVIS doesn't wait to be asked. He MONITORS, ANALYZES,
 * and ALERTS Tony Stark proactively:
 * - "Sir, I'm detecting a thermal signature approaching..."
 * - "Your heart rate has elevated, Sir. Shall I call Dr. Banner?"
 * - "I've completed the analysis. The Mark VII is ready for deployment."
 * 
 * This service does the SAME for trading:
 * - Background market scanning every 5 minutes
 * - Auto-detects big dips (buying opportunities)  
 * - Auto-detects moonshot rockets (breakout alerts)
 * - Whale movement tracking
 * - Portfolio health monitoring
 * - Emergency crash detection (BTC -10%+ = RED ALERT)
 * - Morning briefing on first open each day
 * - Time-aware greetings and market reminders
 * 
 * ALL alerts spoken in Hindi via jarvisVoiceCompanion
 */

// ═══ STATE ═══
let isRunning = false
let scanInterval = null
let lastScanTime = 0
let lastBTCPrice = 0
let lastAlertTime = {}
let morningBriefingDone = false

const SCAN_INTERVAL = 5 * 60 * 1000   // 5 minutes
const ALERT_COOLDOWN = 10 * 60 * 1000  // 10 min cooldown per alert type
const CRASH_THRESHOLD = -8             // % drop = emergency
const DIP_THRESHOLD = -5               // % drop = buying opportunity  
const ROCKET_THRESHOLD = 15            // % gain = breakout alert
const WHALE_THRESHOLD = 1000000        // $1M+ = whale alert

// ═══ PERSONALITY — JARVIS witty proactive lines ═══
const PROACTIVE_LINES = {
  morningBriefing: (data) => {
    const hour = new Date().getHours()
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
    const btc = data.btcChange ? `Bitcoin ${data.btcChange >= 0 ? 'upar' : 'neeche'} hai ${Math.abs(data.btcChange).toFixed(1)} percent.` : ''
    const gems = data.gemsFound ? `${data.gemsFound} potential gems mili hain.` : ''
    const alert = data.emergencyCount ? `${data.emergencyCount} emergency alerts the overnight.` : 'Koi emergency nahi thi.'
    return `${greeting} Sir! Aapka daily briefing ready hai. ${btc} ${gems} ${alert} Main proactively market monitor kar rahi hoon. Bataiye kya karna hai!`
  },

  bigDipFound: (tokens) => {
    const names = tokens.slice(0, 3).map(t => t.symbol || t.name).join(', ')
    return `Sir, attention! ${tokens.length} tokens mein big dip detect hua — ${names}. Ye buying opportunity ho sakti hai. Dekhna chahenge?`
  },

  rocketDetected: (tokens) => {
    const top = tokens[0]
    return `Sir, breakout alert! ${top.symbol || top.name} ${Math.abs(top.change).toFixed(1)} percent upar gaya hai! ${tokens.length > 1 ? `Aur ${tokens.length - 1} tokens bhi rocket kar rahe hain.` : ''} Check kariye!`
  },

  crashAlert: (symbol, pct) => {
    return `RED ALERT Sir! ${symbol} ${Math.abs(pct).toFixed(1)} percent CRASH hua hai! Emergency mode activate. Apne positions check kariye immediately!`
  },

  whaleMovement: (type, amount, symbol) => {
    const amtStr = amount >= 1000000 ? `${(amount / 1000000).toFixed(1)} million dollars` : `${(amount / 1000).toFixed(0)} thousand dollars`
    return `Sir, whale ${type === 'buy' ? 'BUYING' : 'SELLING'} detect hui! ${amtStr} ka ${symbol} ${type === 'buy' ? 'kharida gaya' : 'becha gaya'}. Big player move hai ye.`
  },

  marketStable: () => {
    const lines = [
      'Sir, market stable chal raha hai. Koi major movement nahi hai abhi.',
      'All systems nominal, Sir. Market quiet hai. Main monitor karti rahungi.',
      'Sir, scan complete. Market mein koi unusual activity nahi hai. Relax kariye.',
      'Sab theek hai Sir. Market sideways chal raha hai. Jaise hi kuch hoga, main bata dungi.',
    ]
    return lines[Math.floor(Math.random() * lines.length)]
  },

  periodicUpdate: (data) => {
    const lines = [
      `Sir, quick update: Bitcoin ${data.btcPrice ? `$${data.btcPrice.toLocaleString()} pe hai` : 'stable hai'}. Main watch kar rahi hoon.`,
      `Market scan done Sir. ${data.totalScanned || 0} tokens checked. ${data.opportunities || 0} opportunities mili.`,
      `Sir, aapka AI guardian active hai. ${data.alertsToday || 0} alerts aaj diye, sab kuch monitored hai.`,
    ]
    return lines[Math.floor(Math.random() * lines.length)]
  },

  // ═══ TIME-AWARE INTELLIGENCE ═══
  marketOpening: () => 'Sir, Indian market kholne wala hai! NIFTY pre-market data check kariye. Aaj ka gameplan ready hai?',
  marketClosing: () => 'Sir, market 15 minutes mein band hone wala hai. Open positions review kar lijiye.',
  lateNight: () => 'Sir, raat bahut ho gayi hai. Crypto 24/7 chalta hai lekin aapko rest bhi chahiye. Main watch karti rahungi.',
  weekend: () => 'Sir, weekend hai. Indian market band hai lekin crypto chal raha hai. Koi analysis karna hai?',
  
  // ═══ WITTY TONY STARK STYLE ═══
  randomWitty: () => {
    const witty = [
      'Sir, maine sab kuch check kiya. Tony Stark proud hota aap pe.',
      'Systems running at full capacity Sir. Arc reactor stable hai. Metaphorically, of course.',
      'Sir, aapke portfolio mein koi khatarnaak nahi hai. Unlike Mr. Stark ke enemies.',
      'Market mein opportunity hamesha hoti hai Sir. Bas sahi waqt pe sahi move karna hai.',
      'Sir, main aapki financial FRIDAY hoon, minus the accent. Plus the intelligence.',
      'Scan complete Sir. No Infinity Stones found, but some good gems are available.',
    ]
    return witty[Math.floor(Math.random() * witty.length)]
  },
}

// ═══ SPEAK via companion ═══
function jarvisSpeak(text, priority = 'normal') {
  if (!text) return
  window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text, priority } }))
}

// ═══ Check alert cooldown ═══
function canAlert(type) {
  const now = Date.now()
  if (lastAlertTime[type] && (now - lastAlertTime[type]) < ALERT_COOLDOWN) return false
  lastAlertTime[type] = now
  return true
}

// ═══ MORNING BRIEFING — first open of the day ═══
async function doMorningBriefing() {
  const today = new Date().toDateString()
  const lastBriefing = localStorage.getItem('jarvis_last_briefing')
  if (lastBriefing === today) return // Already briefed today
  
  localStorage.setItem('jarvis_last_briefing', today)
  
  try {
    // Fetch current market data for briefing
    const btcRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true').catch(() => null)
    const btcData = btcRes?.ok ? await btcRes.json() : null
    const btcChange = btcData?.bitcoin?.usd_24h_change || 0

    // Check for gems
    let gemsFound = 0
    try {
      const dexRes = await fetch('https://api.dexscreener.com/token-boosts/latest/v1').catch(() => null)
      const dexData = dexRes?.ok ? await dexRes.json() : []
      gemsFound = Array.isArray(dexData) ? dexData.filter(t => t.amount >= 50).length : 0
    } catch {}

    const briefingText = PROACTIVE_LINES.morningBriefing({
      btcChange,
      gemsFound,
      emergencyCount: 0,
    })

    // Morning briefing — SILENCED (don't auto-speak on boot)
    // User can ask "market status" voice command instead
    console.log('[JARVIS Brain] Morning briefing data ready (silent)')
    morningBriefingDone = true
  } catch (e) {
    console.warn('[JARVIS Brain] Morning briefing error:', e.message)
  }
}

// ═══ BACKGROUND MARKET SCAN ═══
async function backgroundScan() {
  if (Date.now() - lastScanTime < SCAN_INTERVAL - 5000) return
  lastScanTime = Date.now()

  console.log('[JARVIS Brain] 🔍 Proactive background scan...')

  try {
    // 1. Bitcoin price & crash detection
    const btcRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true').catch(() => null)
    if (btcRes?.ok) {
      const btcData = await btcRes.json()
      const btcPrice = btcData?.bitcoin?.usd || 0
      const btcChange = btcData?.bitcoin?.usd_24h_change || 0

      // EMERGENCY: BTC crash detection
      if (btcChange <= CRASH_THRESHOLD && canAlert('crash')) {
        jarvisSpeak(PROACTIVE_LINES.crashAlert('BITCOIN', btcChange), 'high')
        window.dispatchEvent(new CustomEvent('jarvis-emergency', { detail: { type: 'crash', symbol: 'BTC', change: btcChange } }))
      }

      // Track BTC price for change detection
      if (lastBTCPrice > 0) {
        const quickChange = ((btcPrice - lastBTCPrice) / lastBTCPrice) * 100
        if (quickChange <= -3 && canAlert('btc-quick-drop')) {
          jarvisSpeak(`Sir, Bitcoin tezi se gir raha hai! ${Math.abs(quickChange).toFixed(1)} percent drop last scan mein. Alert mode on.`, 'high')
        }
        if (quickChange >= 5 && canAlert('btc-quick-pump')) {
          jarvisSpeak(`Sir, Bitcoin pump ho raha hai! ${quickChange.toFixed(1)} percent upar gaya last scan mein!`, 'high')
        }
      }
      lastBTCPrice = btcPrice
    }

    // 2. DexScreener trending — find rockets and dips
    const dexRes = await fetch('https://api.dexscreener.com/token-boosts/latest/v1').catch(() => null)
    if (dexRes?.ok) {
      const dexData = await dexRes.json()
      if (Array.isArray(dexData)) {
        // High boost tokens (potential moonshots)
        const moonshots = dexData.filter(t => (t.amount || 0) >= 100)
        if (moonshots.length >= 3 && canAlert('moonshots')) {
          // Silent notification — no speech, just console log
          console.log(`[JARVIS Brain] ${moonshots.length} heavily boosted tokens found`)
        }
      }
    }

    // 3. Pump.fun — new launches detection
    try {
      const pumpRes = await fetch('https://frontend-api-v3.pump.fun/coins/currently-live?limit=10&offset=0&includeNsfw=false').catch(() => null)
      if (pumpRes?.ok) {
        const pumpData = await pumpRes.json()
        const newTokens = Array.isArray(pumpData) ? pumpData : []
        if (newTokens.length > 5 && canAlert('pump-activity')) {
          // Silent — no speech for routine pump.fun activity
          console.log(`[JARVIS Brain] ${newTokens.length} new tokens on Pump.fun`)
        }
      }
    } catch {}

    // 4. Periodic market status — DISABLED to avoid constant talking
    // Only speaks on actual critical events (crashes, big pumps)
    const scanCount = parseInt(localStorage.getItem('jarvis_scan_count') || '0') + 1
    localStorage.setItem('jarvis_scan_count', scanCount.toString())
    
    // Periodic updates and witty remarks REMOVED — user complained about constant talking
    // JARVIS now only speaks when something CRITICAL happens or when user asks

    console.log('[JARVIS Brain] ✅ Scan complete')

  } catch (e) {
    console.warn('[JARVIS Brain] Scan error:', e.message)
  }
}

// ═══ TIME-AWARE ALERTS — SILENCED (only logs, no speech) ═══
function checkTimeAwareAlerts() {
  const now = new Date()
  const hour = now.getHours()
  const minute = now.getMinutes()
  const day = now.getDay()

  // All time-aware alerts are now silent — they only log to console
  // User wants JARVIS to speak only when asked, not automatically
  if (hour === 9 && minute >= 10 && minute <= 20 && day >= 1 && day <= 5) {
    if (canAlert('market-open')) console.log('[JARVIS Brain] Indian market opening')
  }
  if (hour === 15 && minute >= 0 && minute <= 10 && day >= 1 && day <= 5) {
    if (canAlert('market-close')) console.log('[JARVIS Brain] Indian market closing')
  }
}

// ═══ START the Proactive Brain ═══
function start() {
  if (isRunning) return
  isRunning = true
  console.log('[JARVIS Brain] 🧠 Proactive Brain ACTIVATED — Iron Man mode')

  // Morning briefing on startup
  setTimeout(() => doMorningBriefing(), 5000)

  // First background scan after 2 minutes (let app boot first)
  setTimeout(() => backgroundScan(), 120000)

  // Regular scans every 5 minutes
  scanInterval = setInterval(() => {
    backgroundScan()
    checkTimeAwareAlerts()
  }, SCAN_INTERVAL)

  // Time-aware check every minute
  setInterval(checkTimeAwareAlerts, 60000)
}

// ═══ STOP ═══
function stop() {
  isRunning = false
  if (scanInterval) clearInterval(scanInterval)
  scanInterval = null
  console.log('[JARVIS Brain] Brain deactivated')
}

// ═══ FORCE SCAN NOW ═══
function scanNow() {
  lastScanTime = 0 // Reset cooldown
  backgroundScan()
  jarvisSpeak('Sir, emergency scan initiate kar rahi hoon. Sab kuch check ho raha hai.', 'high')
}

// ═══ EXPORT ═══
const jarvisProactiveBrain = {
  start,
  stop,
  scanNow,
  doMorningBriefing,
  backgroundScan,
  checkTimeAwareAlerts,
  isRunning: () => isRunning,
}

export default jarvisProactiveBrain
export { start, stop, scanNow, doMorningBriefing }
