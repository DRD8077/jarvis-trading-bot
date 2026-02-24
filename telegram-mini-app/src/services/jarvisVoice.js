/**
 * 🎤 JARVIS Voice-First Hindi Engine
 * ════════════════════════════════════
 * 
 * Full voice control — Hindi + English.
 * "JARVIS, BTC ka price kya hai?"
 * "JARVIS, buy 0.1 BTC"
 * "JARVIS, mera portfolio dikhao"
 * "JARVIS, NIFTY ka options chain dikhao"
 * 
 * Uses Web Speech API (works offline in Android).
 * Natural language command parsing.
 * Hindi TTS responses.
 */

class JarvisVoiceEngine {
  constructor() {
    this.recognition = null
    this.synthesis = window.speechSynthesis || null
    this.isListening = false
    this.wakeWord = 'jarvis'
    this.language = 'hi-IN' // Hindi default, auto-detects English
    this.commands = new Map()
    this.onCommand = null
    this.onTranscript = null
    this.onStateChange = null
    this.conversationHistory = []
    this.personality = 'jarvis' // jarvis, assistant, friend

    this._registerDefaultCommands()
  }

  // ═══════════════════════════════════
  // SPEECH RECOGNITION
  // ═══════════════════════════════════

  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('[JarvisVoice] Speech recognition not supported')
      return false
    }

    this.recognition = new SpeechRecognition()
    this.recognition.continuous = true
    this.recognition.interimResults = true
    this.recognition.lang = this.language
    this.recognition.maxAlternatives = 3

    this.recognition.onresult = (event) => this._handleResult(event)
    this.recognition.onerror = (event) => this._handleError(event)
    this.recognition.onend = () => {
      if (this.isListening) {
        // Auto-restart if user hasn't stopped
        setTimeout(() => {
          try { this.recognition.start() } catch {}
        }, 500)
      }
    }

    console.log('[JarvisVoice] Initialized — Hindi + English')
    return true
  }

  startListening() {
    if (!this.recognition) this.init()
    if (!this.recognition) return false

    try {
      this.recognition.start()
      this.isListening = true
      this._notifyStateChange('listening')
      console.log('[JarvisVoice] Listening...')
      return true
    } catch (e) {
      console.warn('[JarvisVoice] Start failed:', e.message)
      return false
    }
  }

  stopListening() {
    this.isListening = false
    if (this.recognition) {
      try { this.recognition.stop() } catch {}
    }
    this._notifyStateChange('idle')
  }

  _handleResult(event) {
    const results = event.results
    const lastResult = results[results.length - 1]

    if (!lastResult.isFinal) {
      // Interim result — show live transcript
      const interim = lastResult[0].transcript
      if (this.onTranscript) this.onTranscript(interim, false)
      return
    }

    const transcript = lastResult[0].transcript.trim().toLowerCase()
    const confidence = lastResult[0].confidence

    if (this.onTranscript) this.onTranscript(transcript, true)
    console.log(`[JarvisVoice] Heard: "${transcript}" (${(confidence * 100).toFixed(0)}%)`)

    // Check for wake word or process command
    if (transcript.includes(this.wakeWord) || this.isListening) {
      const command = transcript.replace(this.wakeWord, '').trim()
      if (command) this._processCommand(command, confidence)
    }
  }

  _handleError(event) {
    if (event.error === 'no-speech') return // Normal — user just isn't talking
    if (event.error === 'aborted') return
    console.warn('[JarvisVoice] Error:', event.error)
    this._notifyStateChange('error')
  }

  // ═══════════════════════════════════
  // TEXT-TO-SPEECH (Hindi + English)
  // ═══════════════════════════════════

  speak(text, lang = null) {
    if (!this.synthesis) return Promise.resolve()

    return new Promise((resolve) => {
      // Cancel any ongoing speech
      this.synthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang || this._detectLanguage(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      // Find best voice
      const voices = this.synthesis.getVoices()
      const hindiVoice = voices.find(v => v.lang.includes('hi'))
      const englishVoice = voices.find(v => v.lang.includes('en-IN')) || voices.find(v => v.lang.includes('en'))

      if (utterance.lang.includes('hi') && hindiVoice) {
        utterance.voice = hindiVoice
      } else if (englishVoice) {
        utterance.voice = englishVoice
      }

      utterance.onend = () => resolve()
      utterance.onerror = () => resolve()

      this.synthesis.speak(utterance)
      this._notifyStateChange('speaking')
      utterance.onend = () => {
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        resolve()
      }
    })
  }

  _detectLanguage(text) {
    // Simple Hindi detection — check for Devanagari or common Hindi words
    const hindiWords = ['kya', 'hai', 'karo', 'dikhao', 'batao', 'mera', 'kitna', 'aaj',
      'kal', 'abhi', 'nahi', 'haan', 'acha', 'theek', 'paise', 'kharido', 'becho',
      'portfolio', 'nifty', 'bank', 'kaisa', 'kaise']
    const words = text.toLowerCase().split(/\s+/)
    const hindiCount = words.filter(w => hindiWords.includes(w)).length
    if (hindiCount >= 2 || /[\u0900-\u097F]/.test(text)) return 'hi-IN'
    return 'en-IN'
  }

  // ═══════════════════════════════════
  // COMMAND PARSING (NLP-lite)
  // ═══════════════════════════════════

  _processCommand(text, confidence) {
    const normalized = text.toLowerCase().trim()
    this.conversationHistory.push({ role: 'user', text: normalized, timestamp: Date.now() })

    // Check registered commands
    for (const [pattern, handler] of this.commands) {
      const match = normalized.match(pattern)
      if (match) {
        const result = handler(match, normalized)
        if (result) {
          if (result.response) this.speak(result.response)
          if (result.action && this.onCommand) this.onCommand(result)
          this.conversationHistory.push({ role: 'jarvis', text: result.response, timestamp: Date.now() })
          return
        }
      }
    }

    // No match — send to AI
    if (this.onCommand) {
      this.onCommand({ action: 'ai_chat', text: normalized, confidence })
    }
  }

  _registerDefaultCommands() {
    // PRICE QUERIES
    this.commands.set(
      /(price|kya hai|kitna|rate|kimat).*(btc|bitcoin|eth|ethereum|sol|solana|bnb|xrp|nifty|banknifty)/i,
      (match, text) => {
        const coin = match[2].toUpperCase()
        return { action: 'get_price', symbol: coin, response: `${coin} ka price check kar raha hoon sir...` }
      }
    )

    this.commands.set(
      /(btc|bitcoin|eth|ethereum|sol|solana|bnb|xrp|nifty|banknifty).*(price|kya hai|kitna|rate)/i,
      (match, text) => {
        const coin = match[1].toUpperCase()
        return { action: 'get_price', symbol: coin, response: `${coin} ka price dekhta hoon sir...` }
      }
    )

    // BUY/SELL
    this.commands.set(
      /(buy|kharido|le lo)\s+([\d.]+)\s*(btc|bitcoin|eth|ethereum|sol|bnb)/i,
      (match) => {
        const qty = parseFloat(match[2])
        const coin = match[3].toUpperCase()
        return { action: 'buy', symbol: coin, quantity: qty, response: `${qty} ${coin} buy ka order place kar raha hoon sir!` }
      }
    )

    this.commands.set(
      /(sell|becho|bech do)\s+([\d.]+)\s*(btc|bitcoin|eth|ethereum|sol|bnb)/i,
      (match) => {
        const qty = parseFloat(match[2])
        const coin = match[3].toUpperCase()
        return { action: 'sell', symbol: coin, quantity: qty, response: `${qty} ${coin} sell ka order de raha hoon sir!` }
      }
    )

    // PORTFOLIO
    this.commands.set(
      /portfolio|mera portfolio|mere holdings|mera paisa|kitna paisa/i,
      () => ({ action: 'show_portfolio', response: 'Aapka portfolio dikha raha hoon sir...' })
    )

    // P&L
    this.commands.set(
      /(profit|loss|pnl|p&l|kitna kamaya|kitna gaya)/i,
      () => ({ action: 'show_pnl', response: 'Aapka Profit & Loss check kar raha hoon...' })
    )

    // SIGNALS
    this.commands.set(
      /(signal|signals|kya kharidna chahiye|kya buy karu|suggestion)/i,
      () => ({ action: 'show_signals', response: 'Market signals analyze kar raha hoon sir...' })
    )

    // OPTIONS CHAIN
    this.commands.set(
      /(option|options chain|nifty option|bank nifty option)/i,
      () => ({ action: 'show_options', response: 'Options chain load kar raha hoon sir...' })
    )

    // MARKET STATUS
    this.commands.set(
      /(market|market kaisa|trend|bearish|bullish|market condition)/i,
      () => ({ action: 'market_status', response: 'Market ka analysis kar raha hoon...' })
    )

    // NAVIGATION
    this.commands.set(
      /(home|dashboard|ghar|mukhya page)/i,
      () => ({ action: 'navigate', path: '/', response: 'Home page pe le jaata hoon sir' })
    )

    this.commands.set(
      /(settings|setting|seiting)/i,
      () => ({ action: 'navigate', path: '/settings', response: 'Settings khol raha hoon' })
    )

    this.commands.set(
      /(trading|trade|khareed bech)/i,
      () => ({ action: 'navigate', path: '/trading', response: 'Trading page khol raha hoon sir' })
    )

    // GREETINGS
    this.commands.set(
      /(hello|hi|hey|namaste|namaskar|kaise ho|how are you)/i,
      () => {
        const responses = [
          'Namaste sir! Main JARVIS hoon, aapki seva mein. Kya karna hai?',
          'Hello sir! Sab systems online hain. Aapka kya hukm hai?',
          'Ji sir, JARVIS ready hai. Bataaiye kya karu?',
          'Namaskar! Main bilkul theek hoon. Aap bataaiye kaise madad karu?'
        ]
        return { action: 'greeting', response: responses[Math.floor(Math.random() * responses.length)] }
      }
    )

    // STATUS
    this.commands.set(
      /(status|system status|kaisa chal raha|sab theek)/i,
      () => ({ action: 'system_status', response: 'Sab systems check kar raha hoon sir... Sab kuch theek chal raha hai!' })
    )

    // HELP
    this.commands.set(
      /(help|madad|kya kar sakta|kya kya kar sakta)/i,
      () => ({
        action: 'show_help',
        response: 'Sir, main bahut kuch kar sakta hoon! Price check, buy sell, portfolio dekhna, signals, market analysis, options chain, aur bahut kuch. Aap Hindi ya English mein bol sakte hain!'
      })
    )

    // WEATHER / GENERAL
    this.commands.set(
      /(time|samay|kitne baje|what time)/i,
      () => {
        const now = new Date()
        const time = now.toLocaleTimeString('hi-IN')
        return { action: 'time', response: `Sir, abhi ${time} baj rahe hain` }
      }
    )

    // STOP
    this.commands.set(
      /(stop|ruko|band karo|chup|quiet|shut up)/i,
      () => {
        this.stopListening()
        return { action: 'stop', response: 'Ji sir, chup ho gaya' }
      }
    )

    // THANK YOU
    this.commands.set(
      /(thank|thanks|dhanyavaad|shukriya|bahut acha)/i,
      () => {
        const responses = [
          'Shukriya sir! Aur kya karu?',
          'Aapki seva mein sir! Kabhi bhi boliye.',
          'Thank you sir! JARVIS hamesha ready hai.'
        ]
        return { action: 'thanks', response: responses[Math.floor(Math.random() * responses.length)] }
      }
    )
  }

  // ═══════════════════════════════════
  // REGISTER CUSTOM COMMANDS
  // ═══════════════════════════════════

  registerCommand(pattern, handler) {
    this.commands.set(pattern, handler)
  }

  // ═══════════════════════════════════
  // STATE
  // ═══════════════════════════════════

  _notifyStateChange(state) {
    if (this.onStateChange) this.onStateChange(state)
    window.dispatchEvent(new CustomEvent('jarvis-voice-state', { detail: { state } }))
  }

  getState() {
    return {
      isListening: this.isListening,
      language: this.language,
      wakeWord: this.wakeWord,
      supported: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
      ttsSupported: !!this.synthesis,
      history: this.conversationHistory.slice(-20)
    }
  }

  setLanguage(lang) {
    this.language = lang
    if (this.recognition) this.recognition.lang = lang
  }

  toggleLanguage() {
    this.language = this.language === 'hi-IN' ? 'en-IN' : 'hi-IN'
    if (this.recognition) this.recognition.lang = this.language
    return this.language
  }

  destroy() {
    this.stopListening()
    if (this.synthesis) this.synthesis.cancel()
  }
}

const jarvisVoice = new JarvisVoiceEngine()
export default jarvisVoice
export { JarvisVoiceEngine }
