/**
 * 🧠 JARVIS MEMORY SYSTEM — Persistent AI Memory
 * ═══════════════════════════════════════════════════
 * 
 * Like in Iron Man, JARVIS remembers EVERYTHING:
 * - User preferences (favorite coins, trading style)
 * - Visit patterns (which pages visited most, at what times)
 * - Trading history (wins, losses, learning from mistakes)
 * - Conversation context (what was discussed before)
 * - User habits (morning routine, preferred alerts)
 * 
 * All stored in localStorage — works offline, no server needed
 * JARVIS uses this memory to be PROACTIVE and PERSONALIZED
 */

const STORAGE_KEY = 'jarvis_memory_v2'
const MAX_HISTORY = 100

// Default memory structure
function defaultMemory() {
  return {
    user: {
      name: 'Sir',
      preferredLanguage: 'hi',
      tradingStyle: 'moderate', // conservative, moderate, aggressive
      riskTolerance: 'medium',
      firstSeen: new Date().toISOString(),
      totalSessions: 0,
    },
    favorites: {
      coins: [], // ['BTC', 'ETH', 'SOL']
      pages: [],  // ['/moonshot', '/trading']
      strategies: [],
    },
    patterns: {
      activeHours: {}, // { '9': 15, '10': 22, ... } — count of visits per hour
      topPages: {},    // { '/dashboard': 45, '/trading': 30, ... }
      avgSessionDuration: 0,
      totalVisits: 0,
      lastVisit: null,
      consecutiveDays: 0,
      lastActiveDate: null,
    },
    trading: {
      totalTrades: 0,
      wins: 0,
      losses: 0,
      biggestWin: 0,
      biggestLoss: 0,
      favoriteTimeframe: null,
      lastTradeTime: null,
      profitStreak: 0,
      lossStreak: 0,
    },
    alerts: {
      emergencyCount: 0,
      gemsFound: 0,
      whaleAlerts: 0,
      lastEmergency: null,
    },
    conversations: {
      totalMessages: 0,
      topTopics: {},      // { 'bitcoin': 5, 'gems': 3 }
      lastConversation: null,
      mood: 'neutral',    // happy, neutral, frustrated
    },
    insights: [], // Array of JARVIS generated insights
    version: 2,
  }
}

// ═══ LOAD / SAVE ═══
function loadMemory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      // Merge with defaults in case new fields were added
      return { ...defaultMemory(), ...data }
    }
  } catch {}
  return defaultMemory()
}

function saveMemory(memory) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(memory))
  } catch {}
}

let memory = loadMemory()

// ═══ SESSION TRACKING ═══
function startSession() {
  memory.user.totalSessions++
  memory.patterns.totalVisits++
  memory.patterns.lastVisit = new Date().toISOString()
  
  // Track consecutive days
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()
  if (memory.patterns.lastActiveDate === yesterday) {
    memory.patterns.consecutiveDays++
  } else if (memory.patterns.lastActiveDate !== today) {
    memory.patterns.consecutiveDays = 1
  }
  memory.patterns.lastActiveDate = today
  
  saveMemory(memory)
}

// ═══ PAGE TRACKING ═══
function trackPageVisit(path) {
  const hour = new Date().getHours().toString()
  memory.patterns.activeHours[hour] = (memory.patterns.activeHours[hour] || 0) + 1
  memory.patterns.topPages[path] = (memory.patterns.topPages[path] || 0) + 1
  
  // Update favorite pages (top 5)
  const sorted = Object.entries(memory.patterns.topPages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([p]) => p)
  memory.favorites.pages = sorted
  
  saveMemory(memory)
}

// ═══ TRADING MEMORY ═══
function recordTrade(result) {
  // result: { type: 'win'|'loss', amount: number, symbol: string }
  memory.trading.totalTrades++
  memory.trading.lastTradeTime = new Date().toISOString()
  
  if (result.type === 'win' || result.type === 'profit') {
    memory.trading.wins++
    memory.trading.profitStreak++
    memory.trading.lossStreak = 0
    if (result.amount > memory.trading.biggestWin) {
      memory.trading.biggestWin = result.amount
    }
  } else {
    memory.trading.losses++
    memory.trading.lossStreak++
    memory.trading.profitStreak = 0
    if (result.amount > memory.trading.biggestLoss) {
      memory.trading.biggestLoss = result.amount
    }
  }
  
  // Track favorite coins
  if (result.symbol && !memory.favorites.coins.includes(result.symbol)) {
    memory.favorites.coins.push(result.symbol)
    if (memory.favorites.coins.length > 20) memory.favorites.coins.shift()
  }
  
  saveMemory(memory)
}

// ═══ CONVERSATION MEMORY ═══
function recordMessage(message) {
  memory.conversations.totalMessages++
  memory.conversations.lastConversation = new Date().toISOString()
  
  // Extract topics from message
  const topics = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'nifty', 'gem', 
    'trade', 'portfolio', 'profit', 'loss', 'market', 'whale', 'dip', 'moon', 'pump']
  const lower = (message || '').toLowerCase()
  topics.forEach(topic => {
    if (lower.includes(topic)) {
      memory.conversations.topTopics[topic] = (memory.conversations.topTopics[topic] || 0) + 1
    }
  })
  
  saveMemory(memory)
}

// ═══ ALERT MEMORY ═══
function recordAlert(type) {
  if (type === 'emergency') {
    memory.alerts.emergencyCount++
    memory.alerts.lastEmergency = new Date().toISOString()
  } else if (type === 'gem') {
    memory.alerts.gemsFound++
  } else if (type === 'whale') {
    memory.alerts.whaleAlerts++
  }
  saveMemory(memory)
}

// ═══ JARVIS INSIGHTS — learns patterns and generates wisdom ═══
function generateInsight() {
  const insights = []
  
  // Trading insights
  const winRate = memory.trading.totalTrades > 0 
    ? ((memory.trading.wins / memory.trading.totalTrades) * 100).toFixed(0) 
    : null
  if (winRate && memory.trading.totalTrades >= 5) {
    if (winRate >= 70) insights.push(`Sir, aapki win rate ${winRate}% hai. Excellent performance! Tony Stark bhi impressed hote.`)
    else if (winRate >= 50) insights.push(`Sir, aapki win rate ${winRate}% hai. Solid trading. Thoda aur analysis se 70%+ possible hai.`)
    else insights.push(`Sir, win rate ${winRate}% hai. Zyada careful rahiye. JARVIS recommend karti hai smaller positions.`)
  }
  
  // Pattern insights
  const peakHour = Object.entries(memory.patterns.activeHours)
    .sort((a, b) => b[1] - a[1])[0]
  if (peakHour) {
    insights.push(`Sir, aap sabse zyada ${peakHour[0]}:00 baje active rehte hain. Market bhi us waqt volatile hota hai.`)
  }
  
  // Streak insights
  if (memory.trading.profitStreak >= 3) {
    insights.push(`Sir, ${memory.trading.profitStreak} consecutive wins! Hot streak pe hain. Par overconfident mat hoiye.`)
  }
  if (memory.trading.lossStreak >= 3) {
    insights.push(`Sir, ${memory.trading.lossStreak} consecutive losses hue. Break lijiye. Fresh mind se dobara dekhenge.`)
  }
  
  // Loyalty insights
  if (memory.patterns.consecutiveDays >= 7) {
    insights.push(`Sir, ${memory.patterns.consecutiveDays} din se continuously JARVIS use kar rahe hain. Dedication level Iron Man jaisa hai!`)
  }
  
  // Favorite page insight
  if (memory.favorites.pages.length > 0) {
    const fav = memory.favorites.pages[0]
    insights.push(`Sir, aapki sabse favorite page ${fav} hai. Wahan ka data prioritize kar rahi hoon.`)
  }
  
  return insights
}

// ═══ GET PERSONALIZED GREETING ═══
function getPersonalizedGreeting() {
  const hour = new Date().getHours()
  const timeGreeting = hour < 6 ? 'Late night' : hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : hour < 21 ? 'Good evening' : 'Late night'
  
  const sessions = memory.user.totalSessions
  const streak = memory.patterns.consecutiveDays
  const wins = memory.trading.wins
  
  if (sessions <= 1) {
    return `${timeGreeting} Sir! Welcome to JARVIS. Main aapki personal AI assistant hoon. Iron Man ke JARVIS ki tarah, always at your service!`
  }
  
  if (streak >= 7) {
    return `${timeGreeting} Sir! ${streak} din ka streak! Aap toh Tony Stark se bhi dedicated hain. Kya karna hai aaj?`
  }
  
  if (memory.trading.profitStreak >= 3) {
    return `${timeGreeting} Sir! ${memory.trading.profitStreak} consecutive wins ka streak chal raha hai. Hot hands! Aaj bhi kuch dhundhte hain?`
  }
  
  if (wins > 10) {
    return `${timeGreeting} Sir! Session #${sessions} shuru. Aapki ${wins} wins ke saath JARVIS ready hai. Bataiye kya plan hai?`
  }
  
  return `${timeGreeting} Sir! Session #${sessions}. Main monitor kar rahi thi. ${memory.alerts.gemsFound > 0 ? `${memory.alerts.gemsFound} gems track ho rahi hain. ` : ''}Kya karna hai?`
}

// ═══ GET USER'S FAVORITE COINS ═══
function getFavoriteCoins() {
  return memory.favorites.coins.slice(0, 10)
}

// ═══ GET MOST VISITED PAGES ═══  
function getMostVisitedPages() {
  return Object.entries(memory.patterns.topPages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
}

// ═══ GET TRADING STATS ═══
function getTradingStats() {
  const m = memory.trading
  return {
    ...m,
    winRate: m.totalTrades > 0 ? ((m.wins / m.totalTrades) * 100).toFixed(1) : '0',
  }
}

// ═══ LISTEN FOR EVENTS ═══
if (typeof window !== 'undefined') {
  window.addEventListener('jarvis-trade', (e) => {
    const { type, name, amount } = e.detail || {}
    recordTrade({ type: type || 'unknown', symbol: name, amount: amount || 0 })
  })
  window.addEventListener('jarvis-gem-found', () => recordAlert('gem'))
  window.addEventListener('jarvis-emergency', () => recordAlert('emergency'))
  window.addEventListener('jarvis-navigate', (e) => trackPageVisit(e.detail?.path || '/'))
}

const jarvisMemory = {
  startSession,
  trackPageVisit,
  recordTrade,
  recordMessage,
  recordAlert,
  generateInsight,
  getPersonalizedGreeting,
  getFavoriteCoins,
  getMostVisitedPages,
  getTradingStats,
  getMemory: () => memory,
  resetMemory: () => { memory = defaultMemory(); saveMemory(memory) },
}

export default jarvisMemory
export { startSession, trackPageVisit, recordTrade, recordMessage, generateInsight, getPersonalizedGreeting }
