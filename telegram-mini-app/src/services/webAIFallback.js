/**
 * 🌐 Web/APK Fallback for JARVIS AI Engine v2.0
 * 
 * When native LLM plugins aren't available (browser or APK without compiled plugins),
 * this provides REAL AI responses by calling the server's Gemini API,
 * plus browser-native Speech API for STT/TTS.
 * 
 * Priority:
 * 1. Server Gemini API (real AI responses via Railway backend)
 * 2. Browser Web Speech API for STT/TTS
 * 3. Device mock commands (battery, network from browser APIs)
 */

import { API_BASE, SERVER_BASE, isNativeApp } from './apiBase'

class WebAIFallback {
  constructor() {
    this.isNative = typeof window !== 'undefined' && window.Capacitor?.isNativePlatform()
    this.recognition = null
    this.synth = window.speechSynthesis || null
    this.chatHistory = []
    this.serverConnected = false
    // Don't fire fetch at import time — check lazily on first use
  }

  async _checkServerConnection() {
    try {
      const base = SERVER_BASE || ''
      const res = await fetch(`${base}/health`, { timeout: 5000 })
      this.serverConnected = res.ok
      console.log(`[JARVIS] Server connection: ${this.serverConnected ? '✅ Connected' : '❌ Offline'}`)
    } catch {
      this.serverConnected = false
      console.log('[JARVIS] Server connection: ❌ Offline (will retry on chat)')
    }
  }

  get isWeb() {
    return !this.isNative
  }

  // ═══ STT (Web Speech API fallback) ═══

  async startWebSTT(onResult, onPartial) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      throw new Error('Speech Recognition not supported in this browser')
    }

    this.recognition = new SpeechRecognition()
    this.recognition.continuous = true
    this.recognition.interimResults = true
    this.recognition.lang = 'hi-IN' // Hindi default, also understands English

    this.recognition.onresult = (event) => {
      let finalText = ''
      let interimText = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalText += transcript + ' '
        } else {
          interimText += transcript
        }
      }
      
      if (interimText && onPartial) onPartial(interimText)
      if (finalText && onResult) onResult(finalText.trim())
    }

    this.recognition.onerror = (event) => {
      console.warn('Web STT error:', event.error)
    }

    this.recognition.start()
  }

  stopWebSTT() {
    if (this.recognition) {
      this.recognition.stop()
      this.recognition = null
    }
  }

  // ═══ TTS (Web Speech Synthesis fallback) ═══

  async speakWeb(text, options = {}) {
    // v32: Respect mute/voice settings — NEVER bypass
    if (window.__JARVIS_MUTE || window.__JARVIS_VOICE_ENABLED === false) return;
    if (!this.synth) return

    // Cancel current speech
    this.synth.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = options.language || 'hi-IN'
    utterance.rate = options.rate || 1.0
    utterance.pitch = options.pitch || 1.0
    
    // Try to find Hindi voice
    const voices = this.synth.getVoices()
    const hindiVoice = voices.find(v => v.lang.includes('hi'))
    const indianEnglishVoice = voices.find(v => v.lang.includes('en-IN'))
    
    if (options.language?.includes('hi') && hindiVoice) {
      utterance.voice = hindiVoice
    } else if (indianEnglishVoice) {
      utterance.voice = indianEnglishVoice
    }

    return new Promise((resolve) => {
      utterance.onend = resolve
      this.synth.speak(utterance)
    })
  }

  stopWebTTS() {
    if (this.synth) this.synth.cancel()
  }

  // ═══ Mock Device Commands (for web testing) ═══

  async mockBattery() {
    // Try real Battery API
    if (navigator.getBattery) {
      const battery = await navigator.getBattery()
      return {
        level: Math.round(battery.level * 100),
        isCharging: battery.charging,
        chargingType: battery.charging ? 'USB' : 'None',
        temperature: 28.5,
        status: battery.charging ? 'Charging' : 'Discharging'
      }
    }
    return { level: 75, isCharging: false, chargingType: 'None', temperature: 30, status: 'Discharging' }
  }

  async mockNetwork() {
    return {
      connected: navigator.onLine,
      type: navigator.connection?.type || 'WiFi',
      wifiEnabled: true,
      ssid: 'Unknown (Web mode)'
    }
  }

  async mockDeviceInfo() {
    return {
      brand: 'Web Browser',
      model: navigator.userAgent.split('(')[1]?.split(')')[0] || 'Unknown',
      androidVersion: 'N/A (Web)',
      processors: navigator.hardwareConcurrency || 4,
      maxMemoryMB: 'N/A'
    }
  }

  async mockDateTime() {
    const now = new Date()
    return {
      date: now.toLocaleDateString('hi-IN', { day: '2-digit', month: 'long', year: 'numeric' }),
      time: now.toLocaleTimeString('hi-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),
      day: now.toLocaleDateString('hi-IN', { weekday: 'long' }),
      full: now.toLocaleString('hi-IN'),
      timestamp: now.getTime()
    }
  }

  // ═══ AI Generation (uses SERVER Gemini API — real AI responses!) ═══

  async mockGenerate(prompt) {
    // ALWAYS try the server's Gemini API first (real AI!)
    try {
      const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || '{}')
      const userId = savedUser?.id || '0'
      const apiBase = API_BASE || '/api/miniapp'
      
      console.log(`[JARVIS] Sending to Gemini via: ${apiBase}/chat`)
      
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: prompt, 
          user_id: String(userId),
          context: 'mobile_app'
        })
      })

      if (res.ok) {
        const data = await res.json()
        const text = data.response || data.reply || data.message || data.text || 'No response from server'
        this.serverConnected = true
        
        this.chatHistory.push({ role: 'user', content: prompt })
        this.chatHistory.push({ role: 'assistant', content: text })
        
        return { 
          text, 
          model: data.model || 'gemini-server', 
          tokensUsed: data.tokens_used || 0,
          source: 'server-gemini'
        }
      }
    } catch (e) {
      console.warn('[JARVIS] Server Gemini API failed:', e.message, '— trying offline fallback')
      this.serverConnected = false
    }

    // Offline fallback — basic pattern responses when server unreachable
    return this._offlineFallback(prompt)
  }

  // Offline pattern-based responses (last resort when no internet)
  _offlineFallback(prompt) {
    const p = prompt.toLowerCase()
    
    const responses = {
      'hello|hi|hey|namaste|namaskar': 'Namaste! 🙏 Main JARVIS hoon. Abhi server se connect nahi ho pa raha — internet check karo.',
      'battery': `🔋 Battery Info:\n${navigator.getBattery ? 'Browser Battery API available' : 'Not available'}\n\n⚠️ Full battery info ke liye server connection chahiye.`,
      'time|samay|waqt': `🕐 ${new Date().toLocaleString('hi-IN')}`,
      'network|wifi|internet': `📶 Online: ${navigator.onLine ? 'Haan ✅' : 'Nahi ❌'}\nServer: ${this.serverConnected ? 'Connected ✅' : 'Disconnected ❌'}`,
    }
    
    for (const [patterns, response] of Object.entries(responses)) {
      if (new RegExp(patterns, 'i').test(p)) {
        return { text: response, model: 'offline-fallback', tokensUsed: 0, source: 'offline' }
      }
    }
    
    return {
      text: `⚠️ **Offline Mode**\n\nServer se connect nahi ho pa raha.\n\n**Fix karne ke liye:**\n1. Internet/WiFi on karo 📶\n2. App restart karo 🔄\n3. Server: ${SERVER_BASE || 'Not configured'}\n\nJab internet aayega, Gemini AI full power se chalega! 🧠✨`,
      model: 'offline-fallback',
      tokensUsed: 0,
      source: 'offline'
    }
  }
}

const webFallback = new WebAIFallback()
export default webFallback
