/**
 * 💬 JARVIS CONVERSATION MEMORY — Persistent AI Context
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like how JARVIS remembers what Tony said hours/days ago:
 * - Stores conversation snippets with timestamps
 * - References past conversations when relevant
 * - Builds context over multiple sessions
 * - "Sir, you mentioned wanting to buy SOL yesterday at $170. It's now $165."
 * - Sentiment tracking across conversations
 * - Searchable memory bank
 */

const STORAGE_KEY = 'jarvis_conversations'
const MAX_CONVERSATIONS = 200

let conversations = []
let sessionConversations = []
let activeTopics = new Set()

function init() {
  _restore()
  sessionConversations = []
  console.log(`[Conversation Memory] 💬 ${conversations.length} memories loaded`)
}

function _restore() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) conversations = JSON.parse(saved)
  } catch {
    conversations = []
  }
}

function _save() {
  try {
    // Keep only last MAX_CONVERSATIONS
    if (conversations.length > MAX_CONVERSATIONS) {
      conversations = conversations.slice(-MAX_CONVERSATIONS)
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  } catch {}
}

/**
 * Store a user message
 */
function rememberUserSaid(message, context = {}) {
  if (!message || message.length < 3) return

  const entry = {
    type: 'user',
    message: message.substring(0, 500),
    timestamp: Date.now(),
    topics: _extractTopics(message),
    sentiment: _analyzeSentiment(message),
    context,
  }

  conversations.push(entry)
  sessionConversations.push(entry)
  entry.topics.forEach(t => activeTopics.add(t))
  _save()
  return entry
}

/**
 * Store a JARVIS response
 */
function rememberJarvisSaid(message, context = {}) {
  if (!message || message.length < 3) return

  const entry = {
    type: 'jarvis',
    message: message.substring(0, 500),
    timestamp: Date.now(),
    topics: _extractTopics(message),
    context,
  }

  conversations.push(entry)
  sessionConversations.push(entry)
  _save()
  return entry
}

/**
 * Store a specific fact/decision 
 */
function rememberFact(fact, category = 'general') {
  const entry = {
    type: 'fact',
    message: fact,
    category,
    timestamp: Date.now(),
    topics: _extractTopics(fact),
  }
  conversations.push(entry)
  _save()
  return entry
}

/**
 * Search memory for relevant past conversations
 */
function recall(query, limit = 5) {
  if (!query) return []
  const queryLower = query.toLowerCase()
  const queryWords = queryLower.split(/\s+/).filter(w => w.length > 2)

  return conversations
    .filter(c => {
      const msgLower = c.message.toLowerCase()
      return queryWords.some(w => msgLower.includes(w)) ||
        (c.topics && c.topics.some(t => queryLower.includes(t)))
    })
    .sort((a, b) => {
      // Score by relevance (word matches) + recency
      const scoreA = queryWords.filter(w => a.message.toLowerCase().includes(w)).length + 
        (1 / (Date.now() - a.timestamp + 1)) * 1000000
      const scoreB = queryWords.filter(w => b.message.toLowerCase().includes(w)).length +
        (1 / (Date.now() - b.timestamp + 1)) * 1000000
      return scoreB - scoreA
    })
    .slice(0, limit)
}

/**
 * Get context for AI chat — provides relevant past conversations
 */
function getContextForChat(currentMessage) {
  const relevant = recall(currentMessage, 5)
  if (relevant.length === 0) return ''

  const context = relevant.map(c => {
    const ago = _timeAgo(c.timestamp)
    const who = c.type === 'user' ? 'User' : c.type === 'jarvis' ? 'JARVIS' : 'Fact'
    return `[${ago}] ${who}: ${c.message}`
  }).join('\n')

  return `\n--- JARVIS Memory (relevant past conversations) ---\n${context}\n--- End Memory ---\n`
}

/**
 * Get today's conversation summary
 */
function getTodaySummary() {
  const today = new Date().setHours(0, 0, 0, 0)
  const todayConvs = conversations.filter(c => c.timestamp >= today)
  
  if (todayConvs.length === 0) return 'Aaj koi conversation nahi hui hai Sir.'

  const userMessages = todayConvs.filter(c => c.type === 'user').length
  const topics = [...new Set(todayConvs.flatMap(c => c.topics || []))]

  return `Sir, aaj ${userMessages} messages hue hain. Topics: ${topics.join(', ') || 'general'}.`
}

/**
 * Get all active topics this session
 */
function getActiveTopics() {
  return [...activeTopics]
}

/**
 * Memory stats
 */
function getStats() {
  return {
    totalMemories: conversations.length,
    sessionMessages: sessionConversations.length,
    userMessages: conversations.filter(c => c.type === 'user').length,
    jarvisMessages: conversations.filter(c => c.type === 'jarvis').length,
    facts: conversations.filter(c => c.type === 'fact').length,
    topics: [...new Set(conversations.flatMap(c => c.topics || []))],
    oldestMemory: conversations.length > 0 ? _timeAgo(conversations[0].timestamp) : 'none',
    activeTopics: [...activeTopics],
  }
}

/**
 * Smart response — checks if user asked something similar before
 */
function getDejaVu(message) {
  const similar = recall(message, 3)
  const userSimilar = similar.filter(s => s.type === 'user')
  
  if (userSimilar.length > 0) {
    const last = userSimilar[0]
    const ago = _timeAgo(last.timestamp)
    // Find JARVIS response right after
    const idx = conversations.indexOf(last)
    const nextJarvis = conversations.slice(idx + 1, idx + 3).find(c => c.type === 'jarvis')
    
    return {
      found: true,
      previousMessage: last.message,
      timeAgo: ago,
      previousResponse: nextJarvis?.message || null,
    }
  }
  return { found: false }
}

// ═══════ Internal Helpers ═══════

function _extractTopics(text) {
  const topics = []
  const lower = text.toLowerCase()

  // Crypto symbols
  const cryptos = ['btc', 'eth', 'sol', 'bnb', 'xrp', 'ada', 'doge', 'avax', 'dot', 'matic', 'link', 'uni', 'shib', 'ltc', 'pepe', 'bonk', 'wif', 'floki', 'sui', 'apt', 'arb', 'near', 'inj']
  cryptos.forEach(c => { if (lower.includes(c)) topics.push(c) })

  // Trading terms
  const terms = ['buy', 'sell', 'trade', 'price', 'profit', 'loss', 'target', 'stop loss', 'market', 'pump', 'dump', 'moon', 'crash', 'bullish', 'bearish', 'dip']
  terms.forEach(t => { if (lower.includes(t)) topics.push(t) })

  // Features 
  const features = ['scan', 'predict', 'portfolio', 'wallet', 'news', 'alert']
  features.forEach(f => { if (lower.includes(f)) topics.push(f) })

  return [...new Set(topics)]
}

function _analyzeSentiment(text) {
  const lower = text.toLowerCase()
  const positive = ['good', 'great', 'profit', 'moon', 'pump', 'bullish', 'nice', 'amazing', 'accha', 'badhiya', 'mast']
  const negative = ['bad', 'loss', 'crash', 'dump', 'bearish', 'scam', 'rug', 'kharab', 'bura']

  const posCount = positive.filter(w => lower.includes(w)).length
  const negCount = negative.filter(w => lower.includes(w)).length

  if (posCount > negCount) return 'positive'
  if (negCount > posCount) return 'negative'
  return 'neutral'
}

function _timeAgo(timestamp) {
  const diff = Date.now() - timestamp
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function clearAll() {
  conversations = []
  sessionConversations = []
  activeTopics.clear()
  localStorage.removeItem(STORAGE_KEY)
}

const jarvisConversationMemory = {
  init, rememberUserSaid, rememberJarvisSaid, rememberFact,
  recall, getContextForChat, getTodaySummary, getActiveTopics,
  getStats, getDejaVu, clearAll,
}

export default jarvisConversationMemory
export { rememberUserSaid, rememberJarvisSaid, recall, getContextForChat, getStats, getDejaVu }
