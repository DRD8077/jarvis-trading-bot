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
 * Uses Capacitor native plugins on Android, Web Speech API on desktop.
 * Natural language command parsing.
 * Hindi TTS responses.
 */

// Safe Capacitor import — won't crash if not available
let Capacitor = { isNativePlatform: () => false, Plugins: {} }
try {
  if (typeof window !== 'undefined' && window.Capacitor) {
    Capacitor = window.Capacitor
  }
} catch(e) {
  // Not in Capacitor environment
}

let SpeechRecognitionPlugin = null
let TextToSpeechPlugin = null

// Lazy-load Capacitor plugins
async function loadCapPlugins() {
  try {
    if (Capacitor.isNativePlatform()) {
      const srMod = await import('@capacitor-community/speech-recognition')
      SpeechRecognitionPlugin = srMod.SpeechRecognition
      const ttsMod = await import('@capacitor-community/text-to-speech')
      TextToSpeechPlugin = ttsMod.TextToSpeech
    }
  } catch (e) {
    console.warn('[JarvisVoice] Capacitor plugins not available:', e.message)
  }
}

class JarvisVoiceEngine {
  constructor() {
    this.recognition = null
    this.synthesis = null
    this.isListening = false
    this.wakeWord = 'jarvis'
    this.language = 'hi-IN'
    this.commands = new Map()
    this.onCommand = null
    this.onTranscript = null
    this.onStateChange = null
    this.conversationHistory = []
    this.personality = 'jarvis'
    this._isNative = false
    this._initialized = false
    this._listeners = {}

    this._registerDefaultCommands()
  }

  on(event, handler) {
    this._listeners[event] = handler
  }

  _notifyStateChange(state) {
    if (this._listeners['stateChange']) this._listeners['stateChange'](state)
    if (this.onStateChange) this.onStateChange(state)
  }

  _notifyResult(text, isFinal) {
    if (this._listeners['result']) this._listeners['result']({ text, isFinal })
    if (this.onTranscript) this.onTranscript(text, isFinal)
  }

  // ═══════════════════════════════════
  // SPEECH RECOGNITION
  // ═══════════════════════════════════

  async init() {
    if (this._initialized) return true
    
    await loadCapPlugins()
    this._isNative = Capacitor.isNativePlatform() && !!SpeechRecognitionPlugin

    if (this._isNative) {
      // Native Android/iOS — use Capacitor plugin
      try {
        const permResult = await SpeechRecognitionPlugin.requestPermissions()
        console.log('[JarvisVoice] Native permissions:', permResult)
        
        // Listen for partial results
        SpeechRecognitionPlugin.addListener('partialResults', (data) => {
          const text = data.matches?.[0] || ''
          if (text) this._notifyResult(text, false)
        })
        
        this._initialized = true
        console.log('[JarvisVoice] Initialized — Native Capacitor (Hindi + English)')
        return true
      } catch (e) {
        console.warn('[JarvisVoice] Native init failed, falling back to Web API:', e)
        this._isNative = false
      }
    }

    // Fallback: Web Speech API (desktop/browsers)
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionAPI) {
      console.warn('[JarvisVoice] Speech recognition not supported')
      this._initialized = true
      return false
    }

    this.recognition = new SpeechRecognitionAPI()
    this.recognition.continuous = true
    this.recognition.interimResults = true
    this.recognition.lang = this.language
    this.recognition.maxAlternatives = 3

    this.recognition.onresult = (event) => this._handleResult(event)
    this.recognition.onerror = (event) => this._handleError(event)
    this.recognition.onend = () => {
      if (this.isListening) {
        setTimeout(() => {
          try { this.recognition.start() } catch {}
        }, 500)
      }
    }

    this.synthesis = window.speechSynthesis || null
    this._initialized = true
    console.log('[JarvisVoice] Initialized — Web Speech API (Hindi + English)')
    return true
  }

  async startListening(lang) {
    if (!this._initialized) await this.init()
    if (lang) this.language = lang

    if (this._isNative) {
      try {
        await SpeechRecognitionPlugin.start({
          language: this.language,
          maxResults: 3,
          partialResults: true,
          popup: false
        })
        this.isListening = true
        this._notifyStateChange('listening')
        
        // Listen for final results
        SpeechRecognitionPlugin.addListener('listeningState', (state) => {
          if (state.status === 'stopped' && this.isListening) {
            // Auto-restart
            setTimeout(() => this.startListening(this.language), 500)
          }
        })
        
        // Get results
        const resultHandler = async (data) => {
          const text = data.matches?.[0] || ''
          if (text) {
            this._notifyResult(text, true)
            await this.handleCommand(text.trim())
          }
        }
        SpeechRecognitionPlugin.addListener('results', resultHandler)
        
        console.log('[JarvisVoice] Native listening...')
        return true
      } catch (e) {
        console.warn('[JarvisVoice] Native start failed:', e)
        return false
      }
    }

    // Web Speech API fallback
    if (!this.recognition) {
      this.init()
    }
    
    if (this.recognition) {
      try {
        this.recognition.lang = this.language
        this.recognition.start()
        this.isListening = true
        this._notifyStateChange('listening')
        console.log('[JarvisVoice] Listening via Web Speech API...')
        return true
      } catch (e) {
        console.warn('[JarvisVoice] Web Speech API failed:', e.message)
      }
    }
    
    // MediaRecorder + Server Whisper fallback (Android WebView)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      const chunks = []
      
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunks, { type: 'audio/webm' })
        if (blob.size < 1000) return
        
        try {
          const { getServerBase } = await import('./apiBase')
          const base = getServerBase()
          const fd = new FormData()
          fd.append('audio', blob, 'recording.webm')
          const res = await fetch(`${base}/api/voice/transcribe`, { method: 'POST', body: fd })
          const data = await res.json()
          const text = data?.text?.trim()
          if (text) {
            this._notifyResult(text, true)
            await this.handleCommand(text)
          }
        } catch (e) {
          console.warn('[JarvisVoice] Server transcription failed:', e)
        }
        this.isListening = false
        this._notifyStateChange('idle')
      }
      
      recorder.start()
      this._mediaRecorder = recorder
      this.isListening = true
      this._notifyStateChange('listening')
      
      // Auto-stop after 15 seconds
      setTimeout(() => {
        if (this._mediaRecorder?.state === 'recording') this._mediaRecorder.stop()
      }, 15000)
      
      console.log('[JarvisVoice] Listening via MediaRecorder + Whisper...')
      return true
    } catch (e) {
      console.warn('[JarvisVoice] All STT methods failed:', e)
      return false
    }
  }

  async stopListening() {
    this.isListening = false
    
    if (this._isNative) {
      try {
        await SpeechRecognitionPlugin.stop()
        await SpeechRecognitionPlugin.removeAllListeners()
      } catch {}
    }
    
    if (this.recognition) {
      try { this.recognition.stop() } catch {}
    }
    
    // Stop MediaRecorder (triggers onstop → transcription)
    if (this._mediaRecorder?.state === 'recording') {
      try { this._mediaRecorder.stop() } catch {}
    }
    this._mediaRecorder = null
    
    this._notifyStateChange('idle')
  }

  _handleResult(event) {
    const results = event.results
    const lastResult = results[results.length - 1]

    if (!lastResult.isFinal) {
      const interim = lastResult[0].transcript
      this._notifyResult(interim, false)
      return
    }

    const transcript = lastResult[0].transcript.trim().toLowerCase()
    const confidence = lastResult[0].confidence

    this._notifyResult(transcript, true)
    console.log(`[JarvisVoice] Heard: "${transcript}" (${(confidence * 100).toFixed(0)}%)`)

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
  // Uses ElevenLabs → Native → Web Speech
  // ═══════════════════════════════════

  async speak(text, lang = null) {
    // v32: Respect mute/voice settings — NEVER bypass
    if (window.__JARVIS_MUTE || window.__JARVIS_VOICE_ENABLED === false) return;
    
    const detectedLang = lang || this._detectLanguage(text)
    
    // 1. Try ElevenLabs first (sweet Priya voice)
    try {
      const { default: elevenlabsVoice } = await import('./elevenlabsVoice')
      if (elevenlabsVoice && elevenlabsVoice.initialized && typeof elevenlabsVoice.speak === 'function') {
        this._notifyStateChange('speaking')
        await elevenlabsVoice.speak(text, { voice: 'priya' })
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        return
      }
    } catch (e) {
      console.warn('[JarvisVoice] ElevenLabs failed, trying server TTS:', e.message)
    }
    
    // 1.5. Try server-side edge-tts (high quality, always available)
    try {
      const { getServerBase } = await import('./apiBase')
      const base = getServerBase()
      const fd = new FormData()
      const cleanText = text.replace(/```[\s\S]*?```/g, '').replace(/[#*_~>|]/g, '').slice(0, 500)
      fd.append('text', cleanText)
      fd.append('voice', detectedLang.includes('hi') ? 'hi-IN-SwaraNeural' : 'en-US-JennyNeural')
      const res = await fetch(`${base}/api/voice/speak`, { method: 'POST', body: fd })
      if (res.ok && res.headers.get('content-type')?.includes('audio')) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        this._notifyStateChange('speaking')
        await new Promise((resolve) => {
          const audio = new Audio(url)
          audio.onended = () => { URL.revokeObjectURL(url); resolve() }
          audio.onerror = () => { URL.revokeObjectURL(url); resolve() }
          audio.play().catch(() => resolve())
        })
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        return
      }
    } catch (e) {
      console.warn('[JarvisVoice] Server TTS failed, trying native:', e.message)
    }
    
    // 2. Try native TTS
    if (this._isNative && TextToSpeechPlugin) {
      try {
        this._notifyStateChange('speaking')
        await TextToSpeechPlugin.speak({
          text,
          lang: detectedLang,
          rate: 1.0,
          pitch: 1.0,
          volume: 1.0,
          category: 'playback'
        })
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        return
      } catch (e) {
        console.warn('[JarvisVoice] Native TTS failed, using web fallback:', e)
      }
    }

    // Web Speech API fallback
    if (!this.synthesis) {
      this.synthesis = window.speechSynthesis || null
    }
    if (!this.synthesis) return

    return new Promise((resolve) => {
      this.synthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = detectedLang
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      const voices = this.synthesis.getVoices()
      const hindiVoice = voices.find(v => v.lang.includes('hi'))
      const englishVoice = voices.find(v => v.lang.includes('en-IN')) || voices.find(v => v.lang.includes('en'))

      if (utterance.lang.includes('hi') && hindiVoice) {
        utterance.voice = hindiVoice
      } else if (englishVoice) {
        utterance.voice = englishVoice
      }

      this._notifyStateChange('speaking')
      utterance.onend = () => {
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        resolve()
      }
      utterance.onerror = () => {
        this._notifyStateChange(this.isListening ? 'listening' : 'idle')
        resolve()
      }

      this.synthesis.speak(utterance)
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

  getState() {
    return {
      isListening: this.isListening,
      language: this.language,
      wakeWord: this.wakeWord,
      supported: this._isNative || !!(window.SpeechRecognition || window.webkitSpeechRecognition),
      ttsSupported: this._isNative || !!this.synthesis,
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

  async destroy() {
    await this.stopListening()
    if (this.synthesis) this.synthesis.cancel()
    if (this._isNative && SpeechRecognitionPlugin) {
      try { await SpeechRecognitionPlugin.removeAllListeners() } catch {}
    }
  }
}

const jarvisVoice = new JarvisVoiceEngine()
export default jarvisVoice
export { JarvisVoiceEngine }
