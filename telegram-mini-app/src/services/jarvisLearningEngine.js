/**
 * 🧠 JARVIS LEARNING ENGINE — Adaptive Pattern Recognition
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like how JARVIS learns Tony's preferences over time:
 * - Tracks which pages user visits most → suggests them
 * - Records trading patterns (buy/sell timing, asset preferences)
 * - Learns voice command frequency → auto-suggests favorites
 * - Adapts to user's active hours → smarter alerts
 * - Builds "User DNA" profile for personalized experience
 * 
 * "I noticed you tend to check SOL every morning, Sir. It's up 3% today."
 */

const STORAGE_KEY = 'jarvis_learned_patterns'

let patterns = {
  pageVisits: {},      // { pageName: { count, lastVisit, avgDuration } }
  assetWatchlist: {},   // { symbol: { views, trades, lastSeen } }
  activeHours: new Array(24).fill(0), // Activity per hour
  activeDays: new Array(7).fill(0),   // Activity per day of week
  commandUsage: {},    // { command: count }
  tradingStyle: {
    avgHoldTime: 0,
    preferredTimeframe: '1h',
    riskLevel: 'moderate', // conservative, moderate, aggressive
    favoriteAction: 'buy', // buy, sell, swap
    totalTrades: 0,
  },
  sessions: {
    total: 0,
    avgDuration: 0,
    longestStreak: 0,
    currentStreak: 0,
    lastSession: 0,
  },
  preferences: {
    favoritePages: [],
    favoriteAssets: [],
    preferredSuitMode: 'MARK_50',
    alertPreference: 'minimal', // minimal, balanced, detailed
  },
  milestones: [],
}

function init() {
  _restore()
  _trackSession()
  _setupListeners()
  console.log(`[Learning Engine] 🧠 Loaded ${_countPatterns()} patterns`)
}

function _restore() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      patterns = { ...patterns, ...parsed }
    }
  } catch {}
}

function _save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(patterns))
  } catch {}
}

function _setupListeners() {
  // Track page visits
  window.addEventListener('jarvis-navigate', (e) => {
    const page = e.detail?.page || 'unknown'
    trackPageVisit(page)
  })

  // Track voice commands
  window.addEventListener('jarvis-command-executed', (e) => {
    const cmd = e.detail?.command || 'unknown'
    trackCommand(cmd)
  })

  // Track trades
  window.addEventListener('jarvis-trade', (e) => {
    const { symbol, action, amount } = e.detail || {}
    trackTrade(symbol, action, amount)
  })

  // Track hourly activity
  _trackActiveHour()
}

function _trackSession() {
  const now = Date.now()
  const lastSession = patterns.sessions.lastSession
  const dayMs = 86400000

  patterns.sessions.total++
  patterns.sessions.lastSession = now

  // Streak tracking
  if (lastSession && (now - lastSession) < dayMs * 1.5) {
    patterns.sessions.currentStreak++
    if (patterns.sessions.currentStreak > patterns.sessions.longestStreak) {
      patterns.sessions.longestStreak = patterns.sessions.currentStreak
    }
  } else {
    patterns.sessions.currentStreak = 1
  }

  // Check for milestones
  _checkMilestones()
  _save()
}

function _trackActiveHour() {
  const hour = new Date().getHours()
  const day = new Date().getDay()
  patterns.activeHours[hour]++
  patterns.activeDays[day]++
  _save()
}

// ═══════ Tracking Functions ═══════

function trackPageVisit(page) {
  if (!patterns.pageVisits[page]) {
    patterns.pageVisits[page] = { count: 0, lastVisit: 0, totalTime: 0 }
  }
  patterns.pageVisits[page].count++
  patterns.pageVisits[page].lastVisit = Date.now()
  
  _trackActiveHour()
  _updateFavorites()
  _save()
}

function trackCommand(command) {
  if (!patterns.commandUsage[command]) {
    patterns.commandUsage[command] = 0
  }
  patterns.commandUsage[command]++
  _save()
}

function trackAssetView(symbol) {
  if (!symbol) return
  symbol = symbol.toUpperCase()
  if (!patterns.assetWatchlist[symbol]) {
    patterns.assetWatchlist[symbol] = { views: 0, trades: 0, lastSeen: 0 }
  }
  patterns.assetWatchlist[symbol].views++
  patterns.assetWatchlist[symbol].lastSeen = Date.now()
  _updateFavorites()
  _save()
}

function trackTrade(symbol, action, amount) {
  if (!symbol) return
  symbol = symbol.toUpperCase()
  if (!patterns.assetWatchlist[symbol]) {
    patterns.assetWatchlist[symbol] = { views: 0, trades: 0, lastSeen: 0 }
  }
  patterns.assetWatchlist[symbol].trades++
  patterns.assetWatchlist[symbol].lastSeen = Date.now()
  patterns.tradingStyle.totalTrades++

  // Determine risk level based on trading frequency
  if (patterns.tradingStyle.totalTrades > 50) {
    patterns.tradingStyle.riskLevel = 'aggressive'
  } else if (patterns.tradingStyle.totalTrades > 20) {
    patterns.tradingStyle.riskLevel = 'moderate'
  }

  _checkMilestones()
  _save()
}

function trackSuitMode(mode) {
  patterns.preferences.preferredSuitMode = mode
  _save()
}

// ═══════ Intelligence / Suggestions ═══════

function _updateFavorites() {
  // Top 5 pages
  patterns.preferences.favoritePages = Object.entries(patterns.pageVisits)
    .sort(([,a], [,b]) => b.count - a.count)
    .slice(0, 5)
    .map(([page]) => page)

  // Top 5 assets
  patterns.preferences.favoriteAssets = Object.entries(patterns.assetWatchlist)
    .sort(([,a], [,b]) => (b.views + b.trades * 3) - (a.views + a.trades * 3))
    .slice(0, 5)
    .map(([symbol]) => symbol)
}

function getSuggestion() {
  const hour = new Date().getHours()
  const suggestions = []

  // Suggest most visited page if not already there
  if (patterns.preferences.favoritePages.length > 0) {
    suggestions.push(`Sir, aapka favorite page "${patterns.preferences.favoritePages[0]}" hai. Wahan chalein?`)
  }

  // Suggest favorite asset
  if (patterns.preferences.favoriteAssets.length > 0) {
    const fav = patterns.preferences.favoriteAssets[0]
    suggestions.push(`${fav} aapka most watched asset hai. Uska price check karein?`)
  }

  // Time-based suggestion
  const peakHour = patterns.activeHours.indexOf(Math.max(...patterns.activeHours))
  if (Math.abs(hour - peakHour) <= 1) {
    suggestions.push('Yeh aapka peak trading time hai. Market scan karun?')
  }

  // Streak encouragement
  if (patterns.sessions.currentStreak >= 3) {
    suggestions.push(`${patterns.sessions.currentStreak} din ki streak hai Sir! Keep going!`)
  }

  return suggestions[Math.floor(Math.random() * suggestions.length)] || null
}

function getUserDNA() {
  return {
    totalSessions: patterns.sessions.total,
    currentStreak: patterns.sessions.currentStreak,
    longestStreak: patterns.sessions.longestStreak,
    favoritePages: patterns.preferences.favoritePages,
    favoriteAssets: patterns.preferences.favoriteAssets,
    tradingStyle: patterns.tradingStyle,
    peakHour: patterns.activeHours.indexOf(Math.max(...patterns.activeHours)),
    peakDay: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][patterns.activeDays.indexOf(Math.max(...patterns.activeDays))],
    topCommands: Object.entries(patterns.commandUsage).sort(([,a], [,b]) => b - a).slice(0, 5),
    riskLevel: patterns.tradingStyle.riskLevel,
    milestones: patterns.milestones,
    suitMode: patterns.preferences.preferredSuitMode,
  }
}

function _checkMilestones() {
  const ms = patterns.milestones
  const checks = [
    { id: 'first_session', condition: patterns.sessions.total >= 1, label: 'First Boot 🚀' },
    { id: 'streak_3', condition: patterns.sessions.currentStreak >= 3, label: '3-Day Streak 🔥' },
    { id: 'streak_7', condition: patterns.sessions.currentStreak >= 7, label: 'Week Warrior ⚡' },
    { id: 'streak_30', condition: patterns.sessions.currentStreak >= 30, label: 'Iron Will 🏆' },
    { id: 'trades_10', condition: patterns.tradingStyle.totalTrades >= 10, label: '10 Trades 📈' },
    { id: 'trades_50', condition: patterns.tradingStyle.totalTrades >= 50, label: '50 Trades 💰' },
    { id: 'trades_100', condition: patterns.tradingStyle.totalTrades >= 100, label: 'Century 🎯' },
    { id: 'commands_50', condition: Object.values(patterns.commandUsage).reduce((a,b)=>a+b, 0) >= 50, label: 'Voice Master 🎤' },
    { id: 'pages_all', condition: Object.keys(patterns.pageVisits).length >= 15, label: 'Explorer 🗺️' },
  ]

  checks.forEach(({ id, condition, label }) => {
    if (condition && !ms.find(m => m.id === id)) {
      ms.push({ id, label, unlockedAt: Date.now() })
      // v33: Silent milestone — no speech on boot (was causing unwanted alerts)
      console.log(`[JARVIS Learning] Milestone unlocked: ${label}`)
    }
  })
}

function _countPatterns() {
  return Object.keys(patterns.pageVisits).length +
    Object.keys(patterns.assetWatchlist).length +
    Object.keys(patterns.commandUsage).length +
    patterns.milestones.length
}

function getPatterns() { return { ...patterns } }

const jarvisLearningEngine = {
  init, trackPageVisit, trackCommand, trackAssetView,
  trackTrade, trackSuitMode, getSuggestion, getUserDNA,
  getPatterns,
}

export default jarvisLearningEngine
export { trackPageVisit, trackCommand, trackAssetView, trackTrade, getSuggestion, getUserDNA }
