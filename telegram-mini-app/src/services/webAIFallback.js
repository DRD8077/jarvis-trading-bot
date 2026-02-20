/**
 * 🌐 Web Fallback for JARVIS AI Engine
 * 
 * When running in browser (not in Capacitor native app),
 * this provides mock/fallback implementations for:
 * - Web Speech API for STT (browser built-in)
 * - Web Speech Synthesis for TTS (browser built-in)
 * - Mock device commands
 * 
 * This allows development & testing without an Android device.
 */

class WebAIFallback {
  constructor() {
    this.isNative = typeof window !== 'undefined' && window.Capacitor?.isNativePlatform()
    this.recognition = null
    this.synth = window.speechSynthesis || null
    this.chatHistory = []
  }

  /**
   * Check if we're in native or web mode
   */
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

  // ═══ Mock LLM (simple pattern-based responses for testing) ═══

  async mockGenerate(prompt) {
    const p = prompt.toLowerCase()
    
    // Simple keyword responses for testing
    const responses = {
      'hello|hi|hey|namaste|namaskar': 'Namaste! 🙏 Main JARVIS hoon. Kaise madad kar sakta hoon? (Note: Yeh web mode hai — phone pe full AI chalega)',
      'battery': `🔋 Battery Info:\n${JSON.stringify(await this.mockBattery(), null, 2)}\n\n*Web mode mein real battery API use ho raha hai*`,
      'time|samay|waqt': `🕐 ${new Date().toLocaleString('hi-IN')}\n\n*Phone pe zyada accurate hoga with timezone*`,
      'network|wifi|internet': `📶 Online: ${navigator.onLine ? 'Yes ✅' : 'No ❌'}\n\n*Phone pe full WiFi/cellular details milenge*`,
      'device|phone': `📱 Browser: ${navigator.userAgent.substring(0, 50)}...\nCores: ${navigator.hardwareConcurrency}\n\n*Phone pe full device info milega*`,
      'joke|mazak': '😄 Ek programmer ne apni maa se kaha: "Maa, mujhe ek girlfriend chahiye." Maa boli: "Beta, pehle bugs to fix kar le!" 😂',
      'market|nifty|bitcoin|btc': '📊 Market data ke liye internet chahiye. Offline mode mein saved data use hoga.\n\nTip: Phone pe JARVIS AI Agent install karo — trading features bhi milenge! 🚀',
    }
    
    for (const [patterns, response] of Object.entries(responses)) {
      if (new RegExp(patterns, 'i').test(p)) {
        return { text: response, model: 'web-mock', tokensUsed: 0 }
      }
    }
    
    return {
      text: `🌐 **Web Mode Response**\n\nAapne kaha: "${prompt}"\n\nYeh web/browser mode hai — basic responses hi milenge.\n\n📱 **Full AI ke liye:**\n1. APK build karo: \`bash build_apk_ai_agent.sh\`\n2. Phone pe install karo\n3. LLM model download karo\n4. Phir offline AI full power se chalega! 🧠\n\n*Jai Mahadev! 🙏*`,
      model: 'web-mock',
      tokensUsed: 0
    }
  }
}

const webFallback = new WebAIFallback()
export default webFallback
