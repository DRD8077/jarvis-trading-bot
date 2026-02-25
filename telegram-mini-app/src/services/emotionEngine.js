/**
 * 🧠 JARVIS Emotion Engine — Advanced Emotion Analysis & Response
 * ═══════════════════════════════════════════════════════════════
 * 
 * Higher-level emotion engine that uses CameraEngine's face/emotion
 * detection to provide contextual JARVIS responses. Tracks:
 * - Emotion history & patterns
 * - Mood trends over time
 * - Contextual responses ("You seem tired, sir")
 * - Comfort actions (play music, adjust lights, etc.)
 * 
 * Works on Desktop (full camera), Android (front camera), Web (WebRTC).
 * No server needed — runs entirely in browser/Electron.
 */

import cameraEngine from './cameraEngine'

class EmotionEngine {
  constructor() {
    this.currentEmotion = null
    this.emotionHistory = []
    this.moodScore = 50 // 0=very sad, 100=very happy
    this.isActive = false
    this.callbacks = {
      onEmotionChange: null,
      onMoodShift: null,
      onGreeting: null,
      onComfort: null,
    }
    this._lastEmotion = null
    this._emotionStreak = 0
    this._lastGreetingTime = 0
    this._sessionStartTime = Date.now()
    this._presenceState = 'unknown' // present, away, returning
    this._lastPresenceChange = 0

    // JARVIS personality responses
    this._responses = {
      happy: [
        "You seem to be in good spirits, sir. Shall I play some music to match?",
        "Excellent mood detected. All systems performing optimally.",
        "I notice you're smiling. Glad to see it, sir.",
        "Your positive energy is noted. Perhaps a good time to review opportunities?",
      ],
      sad: [
        "Sir, I detect some distress. Is there anything I can help with?",
        "You seem a bit down. Would you like me to play something uplifting?",
        "I'm here if you need anything, sir. Shall I adjust the ambiance?",
        "Detected melancholy. Remember sir, even Stark has off days.",
      ],
      angry: [
        "Sir, elevated stress detected. Perhaps take a moment?",
        "I notice some tension. Shall I dim the lights and play calming music?",
        "Frustration detected. Want me to handle something for you?",
      ],
      surprised: [
        "Something unexpected? I'm monitoring all channels, sir.",
        "Surprise detected. Everything alright?",
        "I see that caught you off guard. Need me to investigate?",
      ],
      neutral: [
        "All systems nominal, sir.",
        "Standing by for your instructions.",
        "Ready when you are, sir.",
      ],
      fearful: [
        "Sir, I detect some anxiety. Everything is secure, I assure you.",
        "No threats detected on any systems. You're safe, sir.",
        "I'm monitoring all channels. Nothing to worry about.",
      ],
      tired: [
        "You appear fatigued, sir. Perhaps it's time for a break?",
        "Long session detected. I'd recommend some rest.",
        "Eye strain detected. Shall I enable night mode?",
      ],
      returning: [
        "Welcome back, sir. I've kept everything running in your absence.",
        "Ah, you've returned. All systems remained stable.",
        "Good to see you again, sir. Missed you. Systems all green.",
      ],
      greeting_morning: [
        "Good morning, sir. Ready to conquer the day?",
        "Morning. I've prepared your briefing. Markets are live.",
        "Rise and shine, sir. All systems online.",
      ],
      greeting_afternoon: [
        "Good afternoon, sir. How may I assist?",
        "Afternoon. Hope the day is treating you well.",
      ],
      greeting_evening: [
        "Good evening, sir. Shall I dim the interface?",
        "Evening already. Time flies when you're building empires.",
      ],
    }
  }

  /**
   * Initialize the Emotion Engine
   */
  async init(options = {}) {
    this.callbacks.onEmotionChange = options.onEmotionChange || null
    this.callbacks.onMoodShift = options.onMoodShift || null
    this.callbacks.onGreeting = options.onGreeting || null
    this.callbacks.onComfort = options.onComfort || null

    // Initialize camera engine with our callbacks
    await cameraEngine.init({
      onFaceDetected: (faces) => this._handleFaceDetected(faces),
      onEmotionDetected: (emotion) => this._handleEmotionDetected(emotion),
      onProximityChange: (proximity) => this._handleProximityChange(proximity),
    })

    this.isActive = true
    console.log('[EmotionEngine] Initialized — Iron Man emotion AI ready')
    return true
  }

  /**
   * Start camera-based emotion detection
   */
  async startDetection(videoElement) {
    if (!videoElement) {
      console.warn('[EmotionEngine] No video element provided')
      return { success: false, error: 'No video element' }
    }
    const result = await cameraEngine.startCamera(videoElement)
    if (result.success) {
      console.log('[EmotionEngine] Camera emotion detection active')
    }
    return result
  }

  /**
   * Stop camera detection
   */
  stopDetection() {
    cameraEngine.stopCamera()
    console.log('[EmotionEngine] Detection stopped')
  }

  /**
   * Handle face detected from camera
   */
  _handleFaceDetected(faces) {
    if (faces.length > 0 && this._presenceState === 'away') {
      this._presenceState = 'returning'
      this._lastPresenceChange = Date.now()
      // User just came back
      const timeSinceStart = Date.now() - this._sessionStartTime
      if (timeSinceStart > 60000) { // Only greet if away for > 1 min
        this._triggerResponse('returning')
      }
      setTimeout(() => {
        this._presenceState = 'present'
      }, 5000)
    } else if (faces.length > 0 && this._presenceState !== 'present') {
      this._presenceState = 'present'
      this._lastPresenceChange = Date.now()
    }
  }

  /**
   * Handle emotion detected from camera
   */
  _handleEmotionDetected(emotion) {
    if (!emotion || !emotion.dominant) return

    this.currentEmotion = emotion

    // Track emotion history (keep last 100 entries)
    this.emotionHistory.push({
      emotion: emotion.dominant,
      confidence: emotion.confidence,
      timestamp: Date.now(),
    })
    if (this.emotionHistory.length > 100) {
      this.emotionHistory.shift()
    }

    // Update mood score
    this._updateMoodScore(emotion.dominant)

    // Check for emotion change
    if (emotion.dominant !== this._lastEmotion) {
      this._emotionStreak = 1
      this._lastEmotion = emotion.dominant

      // Trigger callback
      if (this.callbacks.onEmotionChange) {
        this.callbacks.onEmotionChange(emotion)
      }
    } else {
      this._emotionStreak++
    }

    // If same emotion persists for 10+ detections, trigger comfort response
    if (this._emotionStreak >= 10 && ['sad', 'angry', 'fearful'].includes(emotion.dominant)) {
      this._triggerResponse(emotion.dominant)
      this._emotionStreak = 0 // Reset to avoid spamming
    }

    // Happy streak — positive reinforcement
    if (this._emotionStreak >= 15 && emotion.dominant === 'happy') {
      this._triggerResponse('happy')
      this._emotionStreak = 0
    }
  }

  /**
   * Handle proximity change
   */
  _handleProximityChange(proximity) {
    if (proximity === 'away') {
      this._presenceState = 'away'
      this._lastPresenceChange = Date.now()
    } else if (proximity === 'very-near') {
      // User is very close to screen — maybe reading something important
    }
  }

  /**
   * Update internal mood score based on detected emotion
   */
  _updateMoodScore(emotion) {
    const moodDeltas = {
      happy: +2,
      neutral: 0,
      surprised: +1,
      sad: -3,
      angry: -4,
      fearful: -2,
      disgusted: -2,
    }

    const delta = moodDeltas[emotion] || 0
    const oldScore = this.moodScore
    this.moodScore = Math.max(0, Math.min(100, this.moodScore + delta))

    // Mood shifted significantly
    const oldCategory = this._getMoodCategory(oldScore)
    const newCategory = this._getMoodCategory(this.moodScore)

    if (oldCategory !== newCategory && this.callbacks.onMoodShift) {
      this.callbacks.onMoodShift({
        from: oldCategory,
        to: newCategory,
        score: this.moodScore,
      })
    }
  }

  /**
   * Get mood category from score
   */
  _getMoodCategory(score) {
    if (score >= 75) return 'great'
    if (score >= 50) return 'good'
    if (score >= 25) return 'low'
    return 'critical'
  }

  /**
   * Trigger a contextual JARVIS response
   */
  _triggerResponse(type) {
    const now = Date.now()
    // Don't respond more than once per 30 seconds
    if (now - this._lastGreetingTime < 30000) return
    this._lastGreetingTime = now

    const responses = this._responses[type]
    if (!responses || responses.length === 0) return

    const message = responses[Math.floor(Math.random() * responses.length)]

    // Fire appropriate callback
    if (['sad', 'angry', 'fearful', 'tired'].includes(type) && this.callbacks.onComfort) {
      this.callbacks.onComfort({ type, message, moodScore: this.moodScore })
    } else if (['returning', 'greeting_morning', 'greeting_afternoon', 'greeting_evening'].includes(type) && this.callbacks.onGreeting) {
      this.callbacks.onGreeting({ type, message })
    } else if (this.callbacks.onEmotionChange) {
      this.callbacks.onEmotionChange({ dominant: type, message, confidence: 0.8, all: {} })
    }

    console.log(`[EmotionEngine] Response (${type}): ${message}`)
  }

  /**
   * Get time-based greeting
   */
  getTimeGreeting() {
    const hour = new Date().getHours()
    if (hour >= 5 && hour < 12) return this._randomResponse('greeting_morning')
    if (hour >= 12 && hour < 17) return this._randomResponse('greeting_afternoon')
    return this._randomResponse('greeting_evening')
  }

  /**
   * Get a random response for an emotion type
   */
  _randomResponse(type) {
    const responses = this._responses[type]
    if (!responses || responses.length === 0) return ''
    return responses[Math.floor(Math.random() * responses.length)]
  }

  /**
   * Get comfort action suggestions based on current mood
   */
  getComfortSuggestions() {
    const suggestions = []
    
    if (this.moodScore < 25) {
      suggestions.push(
        { action: 'play_music', label: 'Play uplifting music', icon: '🎵' },
        { action: 'dim_lights', label: 'Adjust brightness', icon: '💡' },
        { action: 'take_break', label: 'Suggest a break', icon: '☕' },
        { action: 'show_memes', label: 'Show something funny', icon: '😄' },
      )
    } else if (this.moodScore < 50) {
      suggestions.push(
        { action: 'play_music', label: 'Background music', icon: '🎵' },
        { action: 'motivational', label: 'Motivational quote', icon: '💪' },
      )
    }

    return suggestions
  }

  /**
   * Get emotion analytics
   */
  getAnalytics() {
    if (this.emotionHistory.length === 0) {
      return { dominantOverall: 'neutral', distribution: {}, moodScore: this.moodScore, sessionDuration: 0 }
    }

    // Count emotion occurrences
    const counts = {}
    this.emotionHistory.forEach(e => {
      counts[e.emotion] = (counts[e.emotion] || 0) + 1
    })

    // Get distribution percentages
    const total = this.emotionHistory.length
    const distribution = {}
    Object.entries(counts).forEach(([k, v]) => {
      distribution[k] = Math.round((v / total) * 100)
    })

    // Dominant emotion overall
    const dominantOverall = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral'

    return {
      dominantOverall,
      distribution,
      moodScore: this.moodScore,
      moodCategory: this._getMoodCategory(this.moodScore),
      totalDetections: total,
      sessionDuration: Math.round((Date.now() - this._sessionStartTime) / 60000), // minutes
      currentEmotion: this.currentEmotion?.dominant || 'unknown',
      presenceState: this._presenceState,
    }
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      active: this.isActive,
      cameraActive: cameraEngine.isActive,
      currentEmotion: this.currentEmotion,
      moodScore: this.moodScore,
      moodCategory: this._getMoodCategory(this.moodScore),
      presence: this._presenceState,
      detectionsCount: this.emotionHistory.length,
    }
  }

  /**
   * Manually trigger a greeting (useful on app start)
   */
  triggerGreeting() {
    const greeting = this.getTimeGreeting()
    if (this.callbacks.onGreeting) {
      const hour = new Date().getHours()
      const type = hour >= 5 && hour < 12 ? 'greeting_morning' : hour >= 12 && hour < 17 ? 'greeting_afternoon' : 'greeting_evening'
      this.callbacks.onGreeting({ type, message: greeting })
    }
    return greeting
  }

  /**
   * Shutdown
   */
  destroy() {
    this.stopDetection()
    this.isActive = false
    this.emotionHistory = []
    console.log('[EmotionEngine] Destroyed')
  }
}

const emotionEngine = new EmotionEngine()
export default emotionEngine
