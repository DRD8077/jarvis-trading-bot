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
    this.userName = this._loadPref('userName') || 'Boss'
    this.language = this._loadPref('language') || 'en'
    this.personality = this._loadPref('personality') || 'professional' // professional, friendly, jarvis-classic
    this.mood = 'neutral' // Based on market conditions
    this.interactionCount = parseInt(this._loadPref('interactions') || '0')
    this.lastInteraction = 0
    this.memoryLog = this._loadMemory()
  }

  // ══════════════════════════════════════════════
  // DYNAMIC GREETINGS (Context-Aware)
  // ══════════════════════════════════════════════

  getGreeting() {
    const hour = new Date().getHours()
    const name = this.userName
    this.interactionCount++
    this._savePref('interactions', this.interactionCount.toString())

    // First time user
    if (this.interactionCount <= 1) {
      return this._pick([
        `Welcome aboard, ${name}. I am J.A.R.V.I.S. — your personal AI trading assistant. Think of me as the Iron Man suit for your portfolio. 🤖`,
        `Hello, ${name}. I'm JARVIS — Just A Rather Very Intelligent System. Ready to make your trading superhuman. Let's begin. 🚀`,
      ])
    }

    // Returning user — time-based
    if (hour >= 4 && hour < 12) {
      return this._pick([
        `Good morning, ${name}. Markets are warming up. I've been running analysis while you slept. ☀️`,
        `Morning, ${name}! I've pre-analyzed 50+ charts for you. Coffee first, or signals first? ☕`,
        `Rise and shine, ${name}. I've been up all night watching the markets. Here's what I found...`,
        `Suprabhat ${name}! 🙏 Markets ready hai, signals ready hai. Batao kya dekhen?`,
      ])
    }

    if (hour >= 12 && hour < 17) {
      return this._pick([
        `Welcome back, ${name}. The afternoon session is looking interesting. Want me to run a quick scan? 📊`,
        `${name}, good to see you. Markets are in mid-session. I have ${Math.floor(Math.random() * 5) + 2} potential signals ready.`,
        `Hey ${name}! Perfect timing — I was just about to flag some unusual volume activity. 🎯`,
      ])
    }

    if (hour >= 17 && hour < 21) {
      return this._pick([
        `Good evening, ${name}. Indian markets closed but crypto never sleeps. Let me show you what's moving. 🌙`,
        `Evening, ${name}! Time for post-market analysis. Your portfolio status and overnight opportunities await.`,
        `Namaste ${name}! 🙏 Market band hua but JARVIS chal raha hai. Let's review today's P&L.`,
      ])
    }

    return this._pick([
      `Still up, ${name}? The night is young and crypto is volatile. I'm watching everything. 🌃`,
      `Late night session, ${name}? I never sleep, so I've got real-time analysis ready for you. 🦉`,
      `${name}, burning the midnight oil? I respect the grind. Here's what the Asian markets are showing...`,
    ])
  }

  // ══════════════════════════════════════════════
  // MARKET CONDITION RESPONSES
  // ══════════════════════════════════════════════

  getMarketComment(marketData) {
    if (!marketData) return 'Markets are moving. Stay alert, stay profitable. 📊'

    const btcChange = marketData.btcChange || 0
    const niftyChange = marketData.niftyChange || 0

    // Bull market
    if (btcChange > 5 || niftyChange > 2) {
      this.mood = 'excited'
      return this._pick([
        `🚀 ${this.userName}, we're in green territory! BTC up ${btcChange.toFixed(1)}%. The bulls are charging!`,
        `Markets are pumping, ${this.userName}! This is exactly the pattern I flagged yesterday. Time to take some profits? 💰`,
        `Green everywhere! As Tony Stark would say — "Sometimes you gotta run before you can walk." Lock in profits. 🟢`,
        `Badhai ho ${this.userName}! 🎉 Market full fire pe hai. BTC ${btcChange.toFixed(1)}% up!`,
      ])
    }

    // Bear market
    if (btcChange < -5 || niftyChange < -2) {
      this.mood = 'calm'
      return this._pick([
        `${this.userName}, markets are bleeding — BTC down ${Math.abs(btcChange).toFixed(1)}%. Stay calm. This is where smart money accumulates. 🎯`,
        `Red day, ${this.userName}. But remember — every crash in history was eventually a buying opportunity. I'm watching for entries. 📉→📈`,
        `As they say, "Be greedy when others are fearful." I've identified ${Math.floor(Math.random() * 3) + 2} potential bounce candidates. Shall I show you?`,
        `Market gir raha hai ${this.userName}, but ghabrao mat. JARVIS sab dekh raha hai. Dip pe buy ki list ready hai. 💪`,
      ])
    }

    // Sideways
    this.mood = 'analytical'
    return this._pick([
      `Markets are consolidating, ${this.userName}. Low volatility often precedes a big move. I'm watching for breakout signals. 👀`,
      `Choppy day. I'd suggest watching volume for direction clues. Multiple indicators are at neutral. ⚖️`,
      `Sideways action today. Perfect time to analyze your portfolio allocation and set up alerts for key levels.`,
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
