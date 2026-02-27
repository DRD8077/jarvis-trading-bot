/**
 * 🦾 JARVIS VOICE COMPANION — Iron Man Style Always-Speaking AI
 * ══════════════════════════════════════════════════════════════
 * 
 * This is the BRAIN of JARVIS voice. Unlike basic TTS, this service
 * makes JARVIS behave like Tony Stark's AI — proactive, conversational,
 * always speaking, reacting to everything happening in the app.
 * 
 * JARVIS speaks:
 * - On app boot → greets you
 * - On page navigation → announces where you are
 * - On finding gems → alerts you about opportunities
 * - On trades → announces buy/sell with P&L
 * - On market changes → warns about big moves
 * - On errors → explains what went wrong
 * - When asked → full conversational AI in Hindi
 * - Proactively → gives tips, reminders, insights
 * 
 * Language: Hindi (Hinglish — Hindi + English technical terms)
 * Personality: Iron Man JARVIS — loyal, sharp, witty, proactive
 */

let voiceEngine = null
let speaking = false
let speechQueue = []
let initialized = false

// ═══ JARVIS PAGE ANNOUNCEMENTS — what JARVIS says on each page ═══
const PAGE_GREETINGS = {
  '/': 'Sir, Dashboard ready hai. Market ka overview dekh rahe hain. Koi specific analysis chahiye toh bolo.',
  '/chat': 'Haan Sir, bataiye! Main sun rahi hoon. Kuch bhi poochiye — market, gems, code, kuch bhi.',
  '/moonshot': 'Sir, MoonShot Hunter active hai. DexScreener aur Pump.fun se gems scan ho rahe hain. Jo token minus 5 percent pe hai, woh dikhega yahan.',
  '/auto-sniper': 'Sir, AI Auto Sniper ready hai. Start karna hai toh bolo — main automatically gems dhundhke trade karungi.',
  '/trading': 'Trading page pe hain Sir. Real-time charts aur signals ready hain.',
  '/wallet': 'Sir, aapka wallet open hai. Balance aur transactions yahan dikhenge.',
  '/gems': 'Gem Scanner active, Sir. Hidden gems dhundh rahi hoon with high potential.',
  '/auto-trader': 'Auto Trader panel, Sir. Paper mode mein safe practice kar sakte hain.',
  '/mega-trader': 'MEGA Trader, Sir! Ye hamara most powerful AI trading system hai.',
  '/indian-stocks': 'Indian Stocks dashboard, Sir. NIFTY, Bank NIFTY, aur top stocks ka analysis.',
  '/nifty-options': 'NIFTY Options Live, Sir. Options chain data real-time mein aa raha hai.',
  '/intelligence': 'Intelligence hub, Sir. Market ka deep analysis yahan milega.',
  '/screener': 'Screener active, Sir. Criteria set karke stocks aur crypto filter karo.',
  '/copy-trading': 'Copy Trading, Sir. Top traders ko follow karke unke trades copy kar sakte ho.',
  '/paper-trading': 'Paper Trading mode, Sir. Ye safe practice zone hai — koi real paisa nahi lagta.',
  '/watchlist': 'Aapki Watchlist, Sir. Favourite tokens aur stocks yahan tracked hain.',
  '/portfolio': 'Portfolio Analytics, Sir. Aapke investments ka complete analysis.',
  '/web3-scanner': 'Web3 Scanner active, Sir. DexScreener, DexTools, Pump.fun sab scan ho rahe hain.',
  '/crypto-top1000': 'Top 1000 Crypto, Sir. Real-time prices aur rankings.',
  '/settings': 'Settings page, Sir. App ka configuration yahan change kar sakte ho.',
  '/voice': 'Voice Assistant mode, Sir. Main sun rahi hoon — bolo kya karna hai!',
  '/ai-agent': 'AI Agent mode, Sir. Main kuch bhi kar sakti hoon — code, research, analysis.',
  '/candle-brain': 'AI Candle Brain, Sir. Chart patterns ka AI analysis chalu hai.',
  '/backtest': 'Backtesting, Sir. Past data pe strategy test kar sakte ho.',
  '/whales': 'Whale Alerts, Sir. Badi transactions track ho rahi hain.',
  '/vault': 'Secure Vault, Sir. Aapke passwords aur credentials safe hain yahan.',
  '/exchange-connect': 'Exchange Connect, Sir. Binance ya CoinDCX connect karna hai toh yahan se karo.',
  '/pnl-journal': 'P&L Journal, Sir. Trading history aur profit loss ka record.',
  '/depth-chart': 'Depth Chart, Sir. Order book ka visual representation.',
  '/smart-alerts': 'Smart Alerts, Sir. Custom price alerts set karo.',
  '/tax-calculator': 'Tax Calculator, Sir. Crypto tax calculate karna hai?',
  '/power-predictor': 'Power Predictor, Sir. AI prediction engine ready hai.',
}

// ═══ JARVIS PROACTIVE PHRASES ═══
const PROACTIVE_PHRASES = {
  gemFound: (name, score) => `Sir, attention! ${name} mil gaya score ${score}. Ye moonshot potential hai. Dekhna chahenge?`,
  bigDip: (name, pct) => `Sir, ${name} ${Math.abs(pct).toFixed(1)} percent neeche gaya hai. Dip buying opportunity ho sakti hai.`,
  trade: (type, name, amount) => `${type === 'buy' ? 'KHARIDA' : 'BECHA'}, Sir! ${name} mein ${amount} rupaye ka trade execute hua.`,
  stopLoss: (name, loss) => `Warning Sir! ${name} pe stop loss trigger hua. ${loss} rupaye ka loss. Position close ho gayi.`,
  takeProfit: (name, profit) => `Congratulations Sir! ${name} pe target hit! ${profit} rupaye ka profit! Position close.`,
  marketAlert: (msg) => `Market Alert, Sir! ${msg}`,
  error: (msg) => `Sir, ek issue aa gaya. ${msg}. Main fix karne ki koshish karungi.`,
  offline: () => 'Sir, internet connection lost ho gaya hai. Offline mode mein kaam kar rahi hoon.',
  online: () => 'Sir, internet wapas aa gaya! Saari services reconnect ho rahi hain.',
  welcome: () => 'Namaste Sir! JARVIS online hai. All systems operational. DexScreener, Pump.fun scan ready. Bataiye kya karna hai!',
  goodnight: () => 'Good night Sir! Jab bhi zaroorat ho, bas bolo JARVIS wake up. Main hamesha yahan hoon.',
  wakeUp: () => 'Good morning Sir! Main jaag gayi! Saare systems check kar liye — sab theek hai. Bataiye, kya karna hai?',
}

// ═══ Initialize voice engine ═══
async function initVoice() {
  if (initialized) return
  try {
    const mod = await import('./elevenlabsVoice.js')
    voiceEngine = mod.default || mod
    if (voiceEngine && !voiceEngine.initialized) {
      await voiceEngine.init().catch(() => {})
    }
    initialized = true
    console.log('[JARVIS Voice Companion] Initialized — Iron Man mode active')
  } catch (e) {
    console.warn('[JARVIS Voice Companion] Init error:', e.message)
    initialized = true // Mark as initialized even on error to prevent retry loops
  }
}

// ═══ SPEAK — queued, no overlap ═══
async function speak(text, priority = 'normal') {
  if (!text) return

  // Initialize on first call
  if (!initialized) await initVoice()

  // High priority interrupts current speech
  if (priority === 'high' && speaking) {
    try { voiceEngine?.stop?.() } catch {}
    speaking = false
    speechQueue = [] // Clear queue for high priority
  }

  // If already speaking, queue it (max 3 in queue)
  if (speaking) {
    if (speechQueue.length < 3) {
      speechQueue.push(text)
    }
    return
  }

  speaking = true

  try {
    if (voiceEngine?.speak) {
      await voiceEngine.speak(text)
    } else if (typeof window !== 'undefined' && window.speechSynthesis) {
      await new Promise((resolve) => {
        window.speechSynthesis.cancel()
        const u = new SpeechSynthesisUtterance(text.slice(0, 500))
        u.lang = 'hi-IN'
        u.rate = 1.05
        u.pitch = 1.0
        u.volume = 1.0
        // Find Hindi voice
        const voices = window.speechSynthesis.getVoices()
        const hiVoice = voices.find(v => v.lang.includes('hi'))
        if (hiVoice) u.voice = hiVoice
        u.onend = resolve
        u.onerror = resolve
        window.speechSynthesis.speak(u)
      })
    }
  } catch (e) {
    console.warn('[JARVIS Voice] Speak error:', e.message)
  }

  speaking = false

  // Process queue
  if (speechQueue.length > 0) {
    const next = speechQueue.shift()
    speak(next)
  }
}

// ═══ PAGE NAVIGATION ANNOUNCEMENTS ═══
let lastPage = ''
function onPageChange(path) {
  if (path === lastPage) return
  lastPage = path
  
  const greeting = PAGE_GREETINGS[path]
  if (greeting) {
    // Small delay to let page render
    setTimeout(() => speak(greeting), 500)
  }
}

// ═══ PROACTIVE ALERTS ═══
function announceGem(name, score) {
  if (score >= 80) speak(PROACTIVE_PHRASES.gemFound(name, score), 'high')
}

function announceDip(name, pct) {
  if (pct <= -5) speak(PROACTIVE_PHRASES.bigDip(name, pct))
}

function announceTrade(type, name, amount) {
  speak(PROACTIVE_PHRASES.trade(type, name, amount), 'high')
}

function announceStopLoss(name, loss) {
  speak(PROACTIVE_PHRASES.stopLoss(name, Math.abs(loss)), 'high')
}

function announceTakeProfit(name, profit) {
  speak(PROACTIVE_PHRASES.takeProfit(name, profit), 'high')
}

function announceMarketAlert(msg) {
  speak(PROACTIVE_PHRASES.marketAlert(msg), 'high')
}

function announceError(msg) {
  speak(PROACTIVE_PHRASES.error(msg))
}

function announceWelcome() {
  speak(PROACTIVE_PHRASES.welcome(), 'high')
}

function announceGoodnight() {
  speak(PROACTIVE_PHRASES.goodnight())
}

function announceWakeUp() {
  speak(PROACTIVE_PHRASES.wakeUp(), 'high')
}

// ═══ NETWORK STATUS ═══
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    setTimeout(() => speak(PROACTIVE_PHRASES.online()), 1000)
  })
  window.addEventListener('offline', () => {
    speak(PROACTIVE_PHRASES.offline(), 'high')
  })
}

// ═══ GLOBAL EVENT LISTENERS — any component can trigger JARVIS voice ═══
if (typeof window !== 'undefined') {
  // Any component can dispatch: window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: '...' } }))
  window.addEventListener('jarvis-speak', (e) => {
    const text = e.detail?.text
    const priority = e.detail?.priority || 'normal'
    if (text) speak(text, priority)
  })

  // Gem found event
  window.addEventListener('jarvis-gem-found', (e) => {
    const { name, score } = e.detail || {}
    if (name && score) announceGem(name, score)
  })

  // Trade executed event
  window.addEventListener('jarvis-trade', (e) => {
    const { type, name, amount } = e.detail || {}
    if (type && name) announceTrade(type, name, amount || 0)
  })

  // Market alert event
  window.addEventListener('jarvis-market-alert', (e) => {
    const { message } = e.detail || {}
    if (message) announceMarketAlert(message)
  })
}

// ═══ EXPORT ═══
const jarvisVoiceCompanion = {
  speak,
  onPageChange,
  announceGem,
  announceDip,
  announceTrade,
  announceStopLoss,
  announceTakeProfit,
  announceMarketAlert,
  announceError,
  announceWelcome,
  announceGoodnight,
  announceWakeUp,
  initVoice,
  PAGE_GREETINGS,
  PROACTIVE_PHRASES,
}

export default jarvisVoiceCompanion
export { speak, onPageChange, announceGem, announceDip, announceTrade, announceStopLoss, announceTakeProfit, announceMarketAlert, announceError, announceWelcome }
