/**
 * 🎙️ ElevenLabs Premium Voice Engine
 * ════════════════════════════════════
 * Ultra-realistic AI voice for JARVIS
 * Uses ElevenLabs Text-to-Speech API
 * Voice ID: 2bNrEsM0omyhLiEyOwqY
 * 
 * Features:
 * - Streaming TTS with WebSocket
 * - Multiple voice profiles
 * - Emotion control (stability, similarity_boost)
 * - Auto-fallback to Web Speech API
 * - Voice activity detection
 * - Conversation mode with ElevenLabs Agents
 */

import { getApiBase } from './apiBase'

class ElevenLabsVoiceEngine {
  constructor() {
    // API key loaded from localStorage (user-provided) or empty (uses backend proxy)
    this.apiKey = localStorage.getItem('jarvis_elevenlabs_key') || ''
    this.defaultVoiceId = 'ThT5KcBeYPX3keUQqHPh' // Priya — sweet Hindi female voice
    this.wsUrl = 'wss://api.elevenlabs.io/v1/text-to-speech'
    this.isPlaying = false
    this.audioContext = null
    this.audioQueue = []
    this.currentSource = null
    this.initialized = false
    this.useFallback = false
    
    // Voice settings — tuned for sweet female voice
    this.settings = {
      stability: 0.55,
      similarity_boost: 0.8,
      style: 0.6,
      use_speaker_boost: true
    }

    // Voice library — ElevenLabs voices
    this.voices = {
      'jarvis-prime': { id: '2bNrEsM0omyhLiEyOwqY', name: 'JARVIS Prime', lang: 'en' },
      'jarvis-tony':  { id: 'pNInz6obpgDQGcFmaJgB', name: 'Tony Stark', lang: 'en' },
      'friday':       { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Friday', lang: 'en' },
      'myra':         { id: '21m00Tcm4TlvDq8ikWAM', name: 'MYRA (Rachel)', lang: 'en' },
      'vikram':       { id: 'yoZ06aMxZJJ28mfd3POQ', name: 'Vikram (Hindi)', lang: 'hi' },
      'priya':        { id: 'ThT5KcBeYPX3keUQqHPh', name: 'Priya (Hindi)', lang: 'hi' },
      'arjun':        { id: 'VR6AewLTigWG4xSOukaG', name: 'Arjun', lang: 'hi' },
      'neha':         { id: 'pFZP5JQG7iQjIQuC4Bku', name: 'Neha', lang: 'hi' }
    }

    this.activeVoice = 'priya'
    this.onStateChange = null
    this.onError = null
  }

  /**
   * Initialize the engine — try ElevenLabs, fallback to Web Speech
   */
  async init(apiKey = null) {
    try {
      // Use hardcoded key, or try local storage / backend
      this.apiKey = apiKey || this.apiKey || localStorage.getItem('elevenlabs_api_key') || null

      if (!this.apiKey) {
        // Try fetching from backend
        try {
          const apiBase = getApiBase()
          const res = await fetch(`${apiBase}/api/miniapp/config/elevenlabs`)
          if (res.ok) {
            const data = await res.json()
            this.apiKey = data.api_key || null
            this.defaultVoiceId = data.voice_id || this.defaultVoiceId
            if (data.available && !this.apiKey) {
              this._useServerTTS = true
              this._serverBase = apiBase
            }
          }
        } catch {}
      }

      // Initialize AudioContext
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
      
      if (this.apiKey) {
        // Verify API key with a lightweight call
        const testRes = await fetch('https://api.elevenlabs.io/v1/voices', {
          headers: { 'xi-api-key': this.apiKey }
        })
        if (testRes.ok) {
          const voiceData = await testRes.json()
          console.log(`[ElevenLabs] Connected — ${voiceData.voices?.length || 0} voices available`)
          this.initialized = true
          this.useFallback = false
        } else {
          console.warn('[ElevenLabs] Invalid API key, using fallback')
          this.useFallback = true
          this.initialized = true
        }
      } else {
        console.log('[ElevenLabs] No API key — using Web Speech fallback')
        this.useFallback = true
        this.initialized = true
      }

      return true
    } catch (e) {
      console.warn('[ElevenLabs] Init failed:', e.message)
      this.useFallback = true
      this.initialized = true
      return true // Still works with fallback
    }
  }

  /**
   * Set API key
   */
  setApiKey(key) {
    this.apiKey = key
    localStorage.setItem('elevenlabs_api_key', key)
    this.useFallback = false
    console.log('[ElevenLabs] API key set')
  }

  /**
   * Select active voice profile
   */
  setVoice(profileName) {
    if (this.voices[profileName]) {
      this.activeVoice = profileName
      console.log(`[ElevenLabs] Voice: ${this.voices[profileName].name}`)
    }
  }

  /**
   * Adjust voice settings
   */
  setSettings({ stability, similarity_boost, style, use_speaker_boost }) {
    if (stability !== undefined) this.settings.stability = Math.max(0, Math.min(1, stability))
    if (similarity_boost !== undefined) this.settings.similarity_boost = Math.max(0, Math.min(1, similarity_boost))
    if (style !== undefined) this.settings.style = Math.max(0, Math.min(1, style))
    if (use_speaker_boost !== undefined) this.settings.use_speaker_boost = use_speaker_boost
  }

  /**
   * PRIMARY: Speak text using ElevenLabs or fallback
   */
  async speak(text, options = {}) {
    if (!text || !this.initialized) return false

    const voiceProfile = options.voice ? this.voices[options.voice] : this.voices[this.activeVoice]
    const voiceId = voiceProfile?.id || this.defaultVoiceId

    // Notify state
    this.isPlaying = true
    if (this.onStateChange) this.onStateChange('speaking')

    // Server-side TTS (ElevenLabs key on backend, not exposed to client)
    if (this._useServerTTS) {
      return this._speakServerSide(text, voiceId, options)
    }

    if (!this.useFallback && this.apiKey) {
      return this._speakElevenLabs(text, voiceId, options)
    } else {
      return this._speakWebSpeech(text, voiceProfile?.lang || 'en')
    }
  }

  /**
   * Server-side ElevenLabs TTS (key stays on backend)
   */
  async _speakServerSide(text, voiceId, options = {}) {
    try {
      const res = await fetch(`${this._serverBase}/api/miniapp/voice/elevenlabs/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice_id: voiceId,
          stability: options.stability || this.settings.stability,
          similarity_boost: options.similarity_boost || this.settings.similarity_boost,
          style: options.style || this.settings.style
        })
      })

      if (res.ok && res.headers.get('content-type')?.includes('audio')) {
        const audioBuffer = await res.arrayBuffer()
        await this._playAudioBuffer(audioBuffer)
        return true
      }

      // Fallback
      console.warn('[ElevenLabs] Server TTS failed, using Web Speech')
      return this._speakWebSpeech(text, 'en')
    } catch (e) {
      console.warn('[ElevenLabs] Server error:', e.message)
      return this._speakWebSpeech(text, 'en')
    }
  }

  /**
   * ElevenLabs TTS via REST API
   */
  async _speakElevenLabs(text, voiceId, options = {}) {
    try {
      const model = options.model || 'eleven_multilingual_v2'
      const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': this.apiKey,
          'Accept': 'audio/mpeg'
        },
        body: JSON.stringify({
          text: text,
          model_id: model,
          voice_settings: {
            stability: options.stability || this.settings.stability,
            similarity_boost: options.similarity_boost || this.settings.similarity_boost,
            style: options.style || this.settings.style,
            use_speaker_boost: this.settings.use_speaker_boost
          }
        })
      })

      if (!res.ok) {
        console.warn(`[ElevenLabs] TTS failed (${res.status}), using fallback`)
        return this._speakWebSpeech(text, 'en')
      }

      const audioBuffer = await res.arrayBuffer()
      await this._playAudioBuffer(audioBuffer)
      return true
    } catch (e) {
      console.warn('[ElevenLabs] TTS error:', e.message)
      return this._speakWebSpeech(text, 'en')
    }
  }

  /**
   * ElevenLabs Streaming TTS via WebSocket (ultra-low latency)
   */
  async speakStreaming(text, options = {}) {
    if (!this.apiKey || this.useFallback) {
      return this.speak(text, options)
    }

    const voiceProfile = options.voice ? this.voices[options.voice] : this.voices[this.activeVoice]
    const voiceId = voiceProfile?.id || this.defaultVoiceId
    const model = options.model || 'eleven_multilingual_v2'

    return new Promise((resolve, reject) => {
      try {
        const ws = new WebSocket(
          `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${model}`
        )

        const audioChunks = []

        ws.onopen = () => {
          // Send BOS (beginning of stream) message
          ws.send(JSON.stringify({
            text: ' ',
            voice_settings: {
              stability: this.settings.stability,
              similarity_boost: this.settings.similarity_boost,
              style: this.settings.style
            },
            xi_api_key: this.apiKey
          }))

          // Send text in chunks for streaming
          const chunks = text.match(/.{1,250}[.!?,\s]|.+$/g) || [text]
          chunks.forEach(chunk => {
            ws.send(JSON.stringify({ text: chunk }))
          })

          // Send EOS (end of stream)
          ws.send(JSON.stringify({ text: '' }))
        }

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          if (data.audio) {
            // Decode base64 audio chunk
            const audioBytes = Uint8Array.from(atob(data.audio), c => c.charCodeAt(0))
            audioChunks.push(audioBytes)
          }
        }

        ws.onclose = async () => {
          if (audioChunks.length > 0) {
            const totalLength = audioChunks.reduce((sum, chunk) => sum + chunk.length, 0)
            const combined = new Uint8Array(totalLength)
            let offset = 0
            audioChunks.forEach(chunk => {
              combined.set(chunk, offset)
              offset += chunk.length
            })
            await this._playAudioBuffer(combined.buffer)
          }
          this.isPlaying = false
          if (this.onStateChange) this.onStateChange('idle')
          resolve(true)
        }

        ws.onerror = (err) => {
          console.warn('[ElevenLabs] WS error:', err)
          this.speak(text, options).then(resolve).catch(reject)
        }
      } catch (e) {
        this.speak(text, options).then(resolve).catch(reject)
      }
    })
  }

  /**
   * Play audio buffer through AudioContext
   */
  async _playAudioBuffer(buffer) {
    try {
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      // Stop any current playback
      this.stop()

      const audioBuffer = await this.audioContext.decodeAudioData(buffer.slice(0))
      const source = this.audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(this.audioContext.destination)
      
      source.onended = () => {
        this.isPlaying = false
        this.currentSource = null
        if (this.onStateChange) this.onStateChange('idle')
      }

      this.currentSource = source
      source.start()
      return true
    } catch (e) {
      console.warn('[ElevenLabs] Audio playback error:', e.message)
      this.isPlaying = false
      return false
    }
  }

  /**
   * Fallback: Web Speech API TTS
   */
  _speakWebSpeech(text, lang = 'en') {
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        this.isPlaying = false
        resolve(false)
        return
      }

      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US'
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      // Try to find a good voice
      const voices = window.speechSynthesis.getVoices()
      const langCode = lang === 'hi' ? 'hi' : 'en'
      const matchVoice = voices.find(v => v.lang.includes(langCode))
      if (matchVoice) utterance.voice = matchVoice

      utterance.onend = () => {
        this.isPlaying = false
        if (this.onStateChange) this.onStateChange('idle')
        resolve(true)
      }
      utterance.onerror = () => {
        this.isPlaying = false
        resolve(false)
      }

      window.speechSynthesis.speak(utterance)
    })
  }

  /**
   * Stop current playback
   */
  stop() {
    if (this.currentSource) {
      try { this.currentSource.stop() } catch {}
      this.currentSource = null
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    this.isPlaying = false
    if (this.onStateChange) this.onStateChange('idle')
  }

  /**
   * Get available voices from ElevenLabs
   */
  async getAvailableVoices() {
    if (!this.apiKey) return Object.values(this.voices)

    try {
      const res = await fetch('https://api.elevenlabs.io/v1/voices', {
        headers: { 'xi-api-key': this.apiKey }
      })
      if (res.ok) {
        const data = await res.json()
        return data.voices || []
      }
    } catch {}
    return Object.values(this.voices)
  }

  /**
   * Get usage/subscription info
   */
  async getUsageInfo() {
    if (!this.apiKey) return null

    try {
      const res = await fetch('https://api.elevenlabs.io/v1/user/subscription', {
        headers: { 'xi-api-key': this.apiKey }
      })
      if (res.ok) return await res.json()
    } catch {}
    return null
  }

  /**
   * ElevenLabs Conversational AI Agent (voice agent mode)
   */
  async startConversation(agentId = null) {
    if (!this.apiKey) {
      console.warn('[ElevenLabs] API key needed for conversation mode')
      return null
    }

    // This connects to ElevenLabs conversational agent
    const ws = new WebSocket(
      `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=${agentId || 'default'}`
    )

    return {
      ws,
      sendAudio: (audioData) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(audioData)
        }
      },
      end: () => ws.close()
    }
  }

  /**
   * Voice cloning — upload audio to create custom voice
   */
  async cloneVoice(name, audioFiles, description = '') {
    if (!this.apiKey) return null

    try {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('description', description)
      audioFiles.forEach(file => formData.append('files', file))

      const res = await fetch('https://api.elevenlabs.io/v1/voices/add', {
        method: 'POST',
        headers: { 'xi-api-key': this.apiKey },
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        console.log(`[ElevenLabs] Voice cloned: ${data.voice_id}`)
        return data
      }
    } catch (e) {
      console.warn('[ElevenLabs] Clone failed:', e.message)
    }
    return null
  }

  /**
   * Get current state
   */
  getState() {
    return {
      initialized: this.initialized,
      hasApiKey: !!this.apiKey,
      useFallback: this.useFallback,
      isPlaying: this.isPlaying,
      activeVoice: this.activeVoice,
      voiceName: this.voices[this.activeVoice]?.name || 'Unknown',
      settings: { ...this.settings }
    }
  }
}

const elevenlabsVoice = new ElevenLabsVoiceEngine()
export default elevenlabsVoice
