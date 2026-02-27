/**
 * 💛 JARVIS EMOTIONAL INTELLIGENCE — Mood Detection & Adaptive Personality
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * In Iron Man, JARVIS adapts his tone based on Tony's mood:
 * - When Tony is stressed → JARVIS is calm and supportive
 * - When Tony is excited → JARVIS matches energy
 * - When Tony is in danger → JARVIS becomes urgent
 * - When Tony jokes → JARVIS responds with dry wit
 * 
 * This engine tracks:
 * - Interaction speed (frantic = stressed, slow = calm)
 * - Trading patterns (losing streak = frustrated, winning = happy)
 * - Time patterns (late night = tired, morning = fresh)
 * - Touch patterns (aggressive tapping = frustrated)
 * - Voice tone keywords (angry words, happy words, etc.)
 * 
 * Then adjusts JARVIS's responses accordingly.
 */

const MOODS = {
  CALM: { id: 'calm', label: 'Calm', emoji: '😌', color: '#3b82f6', voiceTone: 'normal', responseStyle: 'standard' },
  HAPPY: { id: 'happy', label: 'Happy', emoji: '😊', color: '#22c55e', voiceTone: 'upbeat', responseStyle: 'enthusiastic' },
  EXCITED: { id: 'excited', label: 'Excited', emoji: '🤩', color: '#f59e0b', voiceTone: 'energetic', responseStyle: 'matching-energy' },
  STRESSED: { id: 'stressed', label: 'Stressed', emoji: '😰', color: '#ef4444', voiceTone: 'calm-reassuring', responseStyle: 'supportive' },
  FRUSTRATED: { id: 'frustrated', label: 'Frustrated', emoji: '😤', color: '#dc2626', voiceTone: 'patient', responseStyle: 'helpful' },
  TIRED: { id: 'tired', label: 'Tired', emoji: '😴', color: '#8b5cf6', voiceTone: 'gentle', responseStyle: 'brief' },
  FOCUSED: { id: 'focused', label: 'Focused', emoji: '🎯', color: '#06b6d4', voiceTone: 'minimal', responseStyle: 'concise' },
  ANXIOUS: { id: 'anxious', label: 'Anxious', emoji: '😟', color: '#f97316', voiceTone: 'steady', responseStyle: 'reassuring' },
}

// State
let currentMood = MOODS.CALM
let moodHistory = []
let interactionMetrics = {
  tapFrequency: [], // timestamps of taps
  pageChanges: [], // timestamps of navigation
  messagesPerMinute: 0,
  lastInteraction: Date.now(),
  consecutiveLosses: 0,
  consecutiveWins: 0,
  sessionStart: Date.now(),
}

// Keywords that indicate mood
const MOOD_KEYWORDS = {
  happy: ['great', 'awesome', 'amazing', 'profit', 'win', 'made money', 'kamaya', 'maza', 'accha', 'badiya', 'zabardast', 'fantastic'],
  stressed: ['crash', 'loss', 'stop loss', 'emergency', 'help', 'down', 'red', 'neeche', 'gir', 'mar', 'barbad', 'halp'],
  frustrated: ['stupid', 'why', 'kyu', 'not working', 'nahi', 'wrong', 'waste', 'bakwas', 'kharab', 'useless', 'again'],
  excited: ['moon', 'pump', 'rocket', '100x', 'lambo', 'rich', 'millionaire', 'upar', 'chal gaya', 'green'],
  anxious: ['risky', 'careful', 'sure', 'confirm', 'risk', 'safe', 'darr', 'khatarnak', 'dangerous'],
  tired: ['tired', 'thak', 'soja', 'sleep', 'neend', 'late', 'boring', 'bas'],
}

/**
 * Detect mood from a text message
 */
function detectMoodFromText(text) {
  if (!text) return null
  const lower = text.toLowerCase()

  for (const [mood, keywords] of Object.entries(MOOD_KEYWORDS)) {
    for (const kw of keywords) {
      if (lower.includes(kw)) {
        return mood
      }
    }
  }
  return null
}

/**
 * Detect mood from interaction patterns
 */
function detectMoodFromBehavior() {
  const now = Date.now()
  const sessionMinutes = (now - interactionMetrics.sessionStart) / 60000

  // Check tap frequency (last 30 seconds)
  const recentTaps = interactionMetrics.tapFrequency.filter(t => now - t < 30000).length

  // Check page change frequency (last 2 minutes)
  const recentPageChanges = interactionMetrics.pageChanges.filter(t => now - t < 120000).length

  // Late night detection (IST)
  const hour = new Date().getHours()
  const isLateNight = hour >= 0 && hour <= 5

  // Analyze patterns
  if (recentTaps > 15) return 'frustrated' // Frantic tapping
  if (recentPageChanges > 8) return 'anxious' // Jumping between pages rapidly
  if (interactionMetrics.consecutiveLosses >= 3) return 'stressed'
  if (interactionMetrics.consecutiveWins >= 3) return 'excited'
  if (isLateNight && sessionMinutes > 30) return 'tired'
  if (recentTaps < 3 && recentPageChanges <= 1) return 'focused'

  return null
}

/**
 * Update mood based on all factors
 */
function updateMood(textMood = null) {
  const behaviorMood = detectMoodFromBehavior()
  const finalMood = textMood || behaviorMood || 'calm'

  const moodMap = {
    calm: MOODS.CALM,
    happy: MOODS.HAPPY,
    excited: MOODS.EXCITED,
    stressed: MOODS.STRESSED,
    frustrated: MOODS.FRUSTRATED,
    tired: MOODS.TIRED,
    focused: MOODS.FOCUSED,
    anxious: MOODS.ANXIOUS,
  }

  const newMood = moodMap[finalMood] || MOODS.CALM

  // Only update if mood actually changed
  if (newMood.id !== currentMood.id) {
    const previousMood = currentMood
    currentMood = newMood

    moodHistory.push({
      from: previousMood.id,
      to: newMood.id,
      timestamp: Date.now(),
    })

    // Keep last 50 mood changes
    if (moodHistory.length > 50) moodHistory = moodHistory.slice(-50)

    console.log(`[JARVIS EQ] Mood changed: ${previousMood.emoji} ${previousMood.label} → ${newMood.emoji} ${newMood.label}`)

    // Dispatch mood change event
    window.dispatchEvent(new CustomEvent('jarvis-mood-change', { detail: newMood }))

    // Speak mood-specific message if significant change
    if (shouldAnnounceMoodChange(previousMood, newMood)) {
      const announcement = getMoodAnnouncement(newMood, previousMood)
      if (announcement) {
        window.dispatchEvent(new CustomEvent('jarvis-speak', {
          detail: { text: announcement, priority: 'low' }
        }))
      }
    }
  }

  return currentMood
}

/**
 * Should we announce mood change?
 */
function shouldAnnounceMoodChange(from, to) {
  // Always announce if going to stressed/frustrated/tired
  if (['stressed', 'frustrated', 'tired'].includes(to.id)) return true
  // Announce going from negative to positive
  if (['stressed', 'frustrated'].includes(from.id) && ['happy', 'excited', 'calm'].includes(to.id)) return true
  return false
}

/**
 * Get mood-specific JARVIS announcement
 */
function getMoodAnnouncement(newMood, previousMood) {
  switch (newMood.id) {
    case 'stressed':
      return 'Sir, main notice kar rahi hoon ke aap thoda stressed lag rahe hain. Deep breath lein. Market aata jaata rehta hai, aap strong hain.'
    case 'frustrated':
      return 'Sir, frustration samajh sakti hoon. Ek suggestion — thoda break lein, chai piyein. Main tab tak market watch karungi.'
    case 'tired':
      return 'Sir, bahut der se kaam kar rahe hain. Aap thak gaye lagta hain. Kya main autopilot mode activate kar doon? Aap rest kariye.'
    case 'happy':
      if (previousMood?.id === 'stressed') return 'Dekha Sir! Maine kaha tha sab theek hoga. Aap ki smile wapas aa gayi!'
      return null
    case 'excited':
      return 'Sir, bahut accha chal raha hai! Lekin yaad rakhiye — profit book karna mat bhoolna. Greed is the enemy.'
    case 'anxious':
      return 'Sir, bahut zyada pages switch kar rahe hain. Relax kariye. Main sab monitor kar rahi hoon, koi zaroori movement hogi toh bata dungi.'
    default:
      return null
  }
}

/**
 * Record a tap/touch interaction
 */
function recordTap() {
  interactionMetrics.tapFrequency.push(Date.now())
  // Keep last 100
  if (interactionMetrics.tapFrequency.length > 100) {
    interactionMetrics.tapFrequency = interactionMetrics.tapFrequency.slice(-100)
  }
  interactionMetrics.lastInteraction = Date.now()
}

/**
 * Record a page navigation
 */
function recordPageChange(path) {
  interactionMetrics.pageChanges.push(Date.now())
  if (interactionMetrics.pageChanges.length > 50) {
    interactionMetrics.pageChanges = interactionMetrics.pageChanges.slice(-50)
  }
  // Auto-update mood every few page changes
  if (interactionMetrics.pageChanges.length % 5 === 0) {
    updateMood()
  }
}

/**
 * Record trade outcome
 */
function recordTradeOutcome(isWin) {
  if (isWin) {
    interactionMetrics.consecutiveWins++
    interactionMetrics.consecutiveLosses = 0
  } else {
    interactionMetrics.consecutiveLosses++
    interactionMetrics.consecutiveWins = 0
  }
  updateMood()
}

/**
 * Process a user message to detect mood
 */
function processMessage(text) {
  const textMood = detectMoodFromText(text)
  if (textMood) {
    updateMood(textMood)
  }
}

/**
 * Get response style modifier based on current mood
 */
function getResponseModifier() {
  switch (currentMood.id) {
    case 'stressed':
      return { prefix: 'Sir, relax kariye. ', tone: 'calm and reassuring', speed: 0.9, extraPatience: true }
    case 'frustrated':
      return { prefix: 'Sir, main samajhti hoon. ', tone: 'patient and helpful', speed: 0.85, extraPatience: true }
    case 'tired':
      return { prefix: '', tone: 'gentle and brief', speed: 0.8, keepItShort: true }
    case 'excited':
      return { prefix: 'Absolutely Sir! ', tone: 'enthusiastic', speed: 1.1, matchEnergy: true }
    case 'happy':
      return { prefix: '', tone: 'warm and friendly', speed: 1.0, positive: true }
    case 'anxious':
      return { prefix: 'Sir, don\'t worry. ', tone: 'steady and confident', speed: 0.9, reassure: true }
    case 'focused':
      return { prefix: '', tone: 'concise', speed: 1.0, minimal: true }
    default:
      return { prefix: '', tone: 'normal', speed: 1.0 }
  }
}

/**
 * Get current mood
 */
function getCurrentMood() {
  return currentMood
}

/**
 * Get mood history
 */
function getMoodHistory() {
  return moodHistory
}

/**
 * Initialize EQ event listeners
 */
function init() {
  // Track taps globally
  document.addEventListener('touchstart', recordTap, { passive: true })
  document.addEventListener('click', recordTap, { passive: true })

  // Listen for trade events
  window.addEventListener('jarvis-trade', (e) => {
    if (e.detail?.profit !== undefined) {
      recordTradeOutcome(e.detail.profit > 0)
    }
  })

  // Listen for messages
  window.addEventListener('jarvis-user-message', (e) => {
    if (e.detail?.text) processMessage(e.detail.text)
  })

  // Periodic mood check
  setInterval(() => updateMood(), 60000) // Every minute

  console.log('[JARVIS EQ] 💛 Emotional Intelligence ONLINE')
}

const jarvisEQ = {
  init,
  getCurrentMood,
  getMoodHistory,
  updateMood,
  processMessage,
  recordPageChange,
  recordTradeOutcome,
  getResponseModifier,
  detectMoodFromText,
  MOODS,
}

export default jarvisEQ
export { init, getCurrentMood, updateMood, processMessage, getResponseModifier }
