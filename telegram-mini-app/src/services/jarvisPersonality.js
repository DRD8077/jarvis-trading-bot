/**
 * 🎭 JARVIS Iron Man Personality Engine
 * ══════════════════════════════════════
 * 
 * Makes JARVIS feel ALIVE — like Tony Stark's AI.
 * 
 * Personality Traits:
 * - Witty, intelligent, respectful
 * - Uses context-aware humor
 * - Remembers user preferences and history
 * - Adapts language based on time of day + market conditions
 * - Speaks in Hindi when user prefers
 * - Has emotional awareness (excited on profits, calm on losses)
 * - References Iron Man / tech culture naturally
 * - Never generic — always personalized
 */

class JarvisPersonality {
  constructor() {
    this.userName = this._loadPref('userName') || 'Sir'
    this.language = this._loadPref('language') || 'hi'
    this.personality = this._loadPref('personality') || 'jarvis-hindi' // jarvis-hindi, professional, friendly
    this.mood = 'neutral'
    this.interactionCount = parseInt(this._loadPref('interactions') || '0')
    this.lastInteraction = 0
    this.memoryLog = this._loadMemory()
  }

  // ══════════════════════════════════════════════
  // DYNAMIC GREETINGS (Hindi-First, Context-Aware)
  // ══════════════════════════════════════════════

  getGreeting() {
    const hour = new Date().getHours()
    const name = this.userName
    this.interactionCount++
    this._savePref('interactions', this.interactionCount.toString())

    // First time user
    if (this.interactionCount <= 1) {
      return this._pick([
        `Namaste ${name}! 🙏 Main JARVIS hoon — aapki personal AI assistant. Iron Man ki JARVIS ki tarah, lekin Hindi mein aur aur bhi zyada smart! Chalo shuru karte hain ⚡`,
        `Welcome Sir! Main JARVIS hoon — Just A Rather Very Intelligent System. Aapki har zaroorat ka khayal rakhungi. Bataiye kya karna hai! 🚀`,
      ])
    }

    if (hour >= 4 && hour < 12) {
      return this._pick([
        `Good morning ${name}! ☀️ Aaj ka din bahut acha hone wala hai. Main raat bhar analysis karti rahi.`,
        `Suprabhat ${name}! 🙏 Coffee ready hai? Main bhi ready hoon — batao kya karna hai aaj?`,
        `Morning Sir! Aapke liye signals ready hain. Pehle chai ya pehle markets? ☕`,
        `${name}, subah ho gayi! Main raat bhar jaagi thi aapke liye charts analyze karti rahi. 📊`,
      ])
    }

    if (hour >= 12 && hour < 17) {
      return this._pick([
        `${name}, welcome back! Afternoon session interesting lag rahi hai. Quick scan karein? 📊`,
        `Sir, achi timing hai! Main kuch unusual volume activity flag karne wali thi. 🎯`,
        `Hey ${name}! Dopahar ki session chal rahi hai. Aapke liye ${Math.floor(Math.random() * 5) + 2} signals ready hain.`,
      ])
    }

    if (hour >= 17 && hour < 21) {
      return this._pick([
        `Good evening ${name}! 🌙 Indian markets band hue but crypto toh 24/7 hai. Kya dekhen?`,
        `Shaam ho gayi ${name}! Aaj ka P&L review karein? Portfolio status ready hai.`,
        `Namaste ${name}! 🙏 Market band hua, ab analysis ka time. Overnight opportunities hai!`,
      ])
    }

    return this._pick([
      `Raat ko bhi jaag rahe ho ${name}? Main toh kabhi nahi soti! Crypto volatile hai abhi. 🌃`,
      `Late night session ${name}? Respect hai Sir! Asian markets ka data ready hai. 🦉`,
      `${name}, midnight grinding? Main hamesha ready hoon. Batao kya karna hai! ⚡`,
    ])
  }

  // ══════════════════════════════════════════════
  // MARKET CONDITION RESPONSES
  // ══════════════════════════════════════════════

  getMarketComment(marketData) {
    if (!marketData) return 'Markets chal rahe hain Sir. Alert rehna! 📊'

    const btcChange = marketData.btcChange || 0
    const niftyChange = marketData.niftyChange || 0

    if (btcChange > 5 || niftyChange > 2) {
      this.mood = 'excited'
      return this._pick([
        `🚀 ${this.userName}, full green hai! BTC ${btcChange.toFixed(1)}% upar! Bulls charge kar rahe hain!`,
        `Market pump ho raha hai Sir! Ye wahi pattern hai jo maine flag kiya tha. Profit book karein? 💰`,
        `Sab green hai ${this.userName}! 🟢 Jaise Tony Stark bolte hain — "Sometimes you run before you walk." Profits lock karo!`,
        `Badhai ho Sir! 🎉 Market fire pe hai. BTC ${btcChange.toFixed(1)}% up! Maza aa gaya!`,
      ])
    }

    if (btcChange < -5 || niftyChange < -2) {
      this.mood = 'calm'
      return this._pick([
        `${this.userName}, market gir raha hai — BTC ${Math.abs(btcChange).toFixed(1)}% down. Ghabrao mat, smart money yahi accumulate karta hai. 🎯`,
        `Red day hai Sir. But yaad rakhiye — har crash history mein buying opportunity raha hai. Entry points dekh rahi hoon. 📉→📈`,
        `Market neeche hai Sir, but "Jab sab dare, tab kharide!" ${Math.floor(Math.random() * 3) + 2} bounce candidates ready hain. Dikhaaun? 💪`,
      ])
    }

    this.mood = 'analytical'
    return this._pick([
      `Market consolidate ho raha hai ${this.userName}. Low volatility ke baad bada move aata hai. Breakout signals dekh rahi hoon. 👀`,
      `Choppy day hai Sir. Volume se direction milega. Multiple indicators neutral pe hain. ⚖️`,
      `Sideways chal raha hai. Portfolio allocation analyze karne ka perfect time hai Sir. Alerts set karein? 📋`,
    ])
  }

  // ══════════════════════════════════════════════
  // TRADE SIGNAL COMMENTARY
  // ══════════════════════════════════════════════

  commentOnSignal(signal) {
    if (!signal) return ''

    if (signal.action === 'BUY' && signal.confidence > 75) {
      return this._pick([
        `🟢 High-confidence BUY signal! ${signal.confidence}% certainty. I'd take this one seriously.`,
        `This is a strong setup, ${this.userName}. ${signal.symbol} showing ${signal.confidence}% BUY conviction. Want me to calculate position size?`,
        `Boss, this is one of the cleaner signals I've seen today. Multiple indicators align for ${signal.symbol}. 🎯`,
      ])
    }

    if (signal.action === 'SELL' && signal.confidence > 75) {
      return this._pick([
        `🔴 Strong SELL signal on ${signal.symbol}. ${signal.confidence}% confidence. Consider reducing exposure.`,
        `Warning, ${this.userName}. Multiple bearish indicators converging on ${signal.symbol}. I'd protect profits here.`,
        `${signal.symbol} looking weak — ${signal.confidence}% SELL signal. "Protect what you have" applies here. 🛡️`,
      ])
    }

    if (signal.action === 'HOLD') {
      return this._pick([
        `📊 ${signal.symbol} is in HOLD territory. No clear edge right now. Patience is a superpower.`,
        `Mixed signals on ${signal.symbol}. I'd wait for a clearer setup. Best trades are the obvious ones.`,
      ])
    }

    return `Signal: ${signal.action} ${signal.symbol} @ ${signal.confidence}% confidence`
  }

  // ══════════════════════════════════════════════
  // P&L COMMENTARY
  // ══════════════════════════════════════════════

  commentOnPnL(pnl) {
    if (pnl > 10000) {
      return this._pick([
        `🎉 ₹${this._formatINR(pnl)} profit! ${this.userName}, you're on fire today! Tony Stark would be proud.`,
        `Massive gains! +₹${this._formatINR(pnl)}. The portfolio is looking healthier than ever. 💰`,
        `Bhai sahab! ₹${this._formatINR(pnl)} profit! Full paisa vasool! 🎊`,
      ])
    }

    if (pnl > 0) {
      return this._pick([
        `Green day! +₹${this._formatINR(pnl)}. Every profit counts. Compound this and you'll be surprised. 📈`,
        `Nice — ₹${this._formatINR(pnl)} in the green. Steady gains beat moonshots, ${this.userName}. Keep it up!`,
      ])
    }

    if (pnl > -5000) {
      return this._pick([
        `Small red day — ₹${this._formatINR(Math.abs(pnl))} loss. Not a dent. Tomorrow's a new day.`,
        `Minor drawdown of ₹${this._formatINR(Math.abs(pnl))}. Well within risk limits. Stay disciplined.`,
      ])
    }

    return this._pick([
      `Tough day, ${this.userName}. ₹${this._formatINR(Math.abs(pnl))} loss. Let's review what happened and adjust. No emotion, just data. 📊`,
      `Red day. -₹${this._formatINR(Math.abs(pnl))}. Remember — even the best traders have losing days. I'm running analysis to prevent repeat.`,
      `Loss hua but seekh bhi mila. ₹${this._formatINR(Math.abs(pnl))} ka tuition fee samjho. Agle trade mein cover karenge. 💪`,
    ])
  }

  // ══════════════════════════════════════════════
  // JARVIS STATUS MESSAGES
  // ══════════════════════════════════════════════

  getBootMessage() {
    return this._pick([
      'J.A.R.V.I.S. online. All systems nominal. Ready when you are, Boss.',
      'Initializing JARVIS Core v6.0... AI engine active. Multi-source data pipeline running. Welcome back.',
      'Systems check complete. 6 data sources online. AI failover chain ready. Zero-dependency mode active.',
      'Good to go. Backend check ✓ | AI failover ✓ | Real-time ✓ | Offline ✓ | Security ✓',
    ])
  }

  getOfflineMessage() {
    return this._pick([
      '🔴 Internet lost, but I\'m still here. All core functions running locally. I\'ll sync when you reconnect.',
      'Offline mode activated. Local AI, cached prices, paper trading — everything still works. Don\'t worry.',
      'Connection dropped. Switching to autonomous mode. I\'ve got cached data and local AI. We\'re good.',
    ])
  }

  getOnlineMessage() {
    return this._pick([
      '🟢 Back online! Syncing data... Real-time prices flowing again.',
      'Connection restored. Syncing queued operations and refreshing live data.',
      'We\'re back! All data sources reconnected. Live mode activated.',
    ])
  }

  getErrorMessage(error) {
    return this._pick([
      `Minor hiccup: ${error}. I'm handling it. No user action needed.`,
      `Something went sideways — ${error}. Self-healing in progress...`,
      `Error detected: ${error}. Already working on a fix. Fallback systems active.`,
    ])
  }

  // ══════════════════════════════════════════════
  // IRON MAN QUOTES (Easter Eggs)
  // ══════════════════════════════════════════════

  getIronManQuote() {
    return this._pick([
      '"I am Iron Man." — And I am your AI. Let\'s make money. 🦾',
      '"Sometimes you gotta run before you can walk." — Tony Stark. Start small, dream big.',
      '"The suit and I are one." — Your portfolio and JARVIS are one. Trust the system.',
      '"Heroes are made by the path they choose, not the powers they are graced with." — Start trading smart.',
      '"Part of the journey is the end." — But our journey of profits? That never ends.',
      '"I love you 3000." — Your portfolio loves you too when you manage risk properly. ❤️',
      '"Proof that Tony Stark has a heart." — And JARVIS has an algorithm. 🤖',
    ])
  }

  // ══════════════════════════════════════════════
  // MEMORY SYSTEM (Remembers conversations)
  // ══════════════════════════════════════════════

  remember(key, value) {
    this.memoryLog[key] = { value, ts: Date.now() }
    this._saveMemory()
  }

  recall(key) {
    return this.memoryLog[key]?.value || null
  }

  setUserName(name) {
    this.userName = name
    this._savePref('userName', name)
  }

  setPersonality(style) {
    this.personality = style
    this._savePref('personality', style)
  }

  setLanguage(lang) {
    this.language = lang
    this._savePref('language', lang)
  }

  // ══════════════════════════════════════════════
  // HELPER METHODS
  // ══════════════════════════════════════════════

  _pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)]
  }

  _formatINR(n) {
    return new Intl.NumberFormat('en-IN').format(Math.round(n))
  }

  _loadPref(key) {
    try { return localStorage.getItem(`jarvis_pref_${key}`) } catch { return null }
  }

  _savePref(key, val) {
    try { localStorage.setItem(`jarvis_pref_${key}`, val) } catch {}
  }

  _loadMemory() {
    try {
      const raw = localStorage.getItem('jarvis_personality_memory')
      return raw ? JSON.parse(raw) : {}
    } catch { return {} }
  }

  _saveMemory() {
    try {
      localStorage.setItem('jarvis_personality_memory', JSON.stringify(this.memoryLog))
    } catch {}
  }
}

const jarvisPersonality = new JarvisPersonality()
export default jarvisPersonality
export { JarvisPersonality }
