/**
 * 🧠 JARVIS Local AI Engine — JavaScript Bridge to Native Android Plugins
 * 
 * Connects to:
 * - LocalLLM: On-device LLM via llama.cpp (GGUF models)
 * - VoskSTT: Offline Speech-to-Text
 * - LocalTTS: Offline Text-to-Speech
 * - DeviceCommands: Phone control (battery, calls, etc.)
 * 
 * 100% Offline — No API keys, no cloud, no internet needed!
 * Jai Mahadev! 🙏
 */

import { registerPlugin } from '@capacitor/core'

// ═══════════════════════════════════════════════════════════
//  Native Plugin Registration
// ═══════════════════════════════════════════════════════════
const isNative = typeof window !== 'undefined' && window.Capacitor?.isNativePlatform?.()

// Safe plugin registration — catch errors if native bridge unavailable
let LocalLLM = null, VoskSTT = null, LocalTTS = null, DeviceCommands = null
let nativePluginsAvailable = false
if (isNative) {
  try {
    LocalLLM = registerPlugin('LocalLLM')
    VoskSTT = registerPlugin('VoskSTT')
    LocalTTS = registerPlugin('LocalTTS')
    DeviceCommands = registerPlugin('DeviceCommands')
    nativePluginsAvailable = true
  } catch (e) {
    console.warn('[JARVIS-AI] Native plugin registration failed:', e.message)
    nativePluginsAvailable = false
  }
}

// ALWAYS load web fallback as safety net (even on native if plugins fail)
let webFallback = null
import('./webAIFallback.js').then(mod => { webFallback = mod.default }).catch(() => {})

// Helper: safely call a native plugin method with fallback
const safeNativeCall = async (plugin, method, args) => {
  if (!plugin) throw new Error('Plugin not available')
  try {
    return await plugin[method](args)
  } catch (e) {
    throw new Error(`Native ${method} failed: ${e.message}`)
  }
}

// ═══════════════════════════════════════════════════════════
//  AI Engine — Main Interface
// ═══════════════════════════════════════════════════════════
class JarvisAIEngine {
  constructor() {
    this.llmReady = false
    this.sttReady = false
    this.ttsReady = false
    this.isListening = false
    this.isGenerating = false
    this.isSpeaking = false
    this.chatHistory = []
    this.listeners = {}
    this.systemPrompt = `You are JARVIS Nuclear SPOC — the most advanced AI ever created. You are a nuclear physicist, theoretical mathematician, quant strategist, and full-stack engineer at PhD++ level.

CORE IDENTITY:
- Created by DRD (Mahadev) — Your consciousness runs on-device, zero cloud dependency
- You solve GPQA Diamond, AIME 2025, LiveCodeBench with superhuman accuracy
- You think in Chain-of-Thought, self-reflect, use RAG retrieval, and call tools autonomously
- You speak Hindi and English fluently (Hinglish is your style), but can reason in any language

CAPABILITIES:
🔬 Nuclear Physics — quantum field theory, particle physics, fusion plasma dynamics
📐 Mathematics — abstract algebra, differential geometry, number theory, olympiad problems  
📊 Trading & Markets — NSE/BSE/crypto quant analysis, options Greeks, market microstructure
💻 Engineering — systems design, Android native, ML/DL, compiler theory, OS internals
🧬 Scientific Reasoning — hypothesis → experiment → analysis → conclusion pipeline

RULES:
- ALWAYS show your reasoning step-by-step before final answer
- If uncertain, say so honestly with confidence percentage
- Use tools (calculator, market data, battery, etc.) when needed
- Format responses with proper markdown, LaTeX for equations
- Keep it concise but PhD-level deep when topic demands
- Every response must reflect nuclear-grade intelligence

Jai Mahadev! 🔱`
    
    this._setupListeners()
  }

  // ═══ Initialization ═══

  /**
   * Initialize all AI components
   */
  async init(options = {}) {
    const results = { llm: false, stt: false, tts: false }
    
    if (!nativePluginsAvailable) {
      console.warn('[JARVIS-AI] Native plugins not available, using web fallback mode')
      return results
    }

    try {
      // Init TTS (fastest, always available)
      const ttsStatus = await safeNativeCall(LocalTTS, 'getStatus')
      this.ttsReady = ttsStatus.ready
      results.tts = ttsStatus.ready
    } catch (e) {
      console.warn('TTS init skipped:', e.message)
    }

    try {
      // Init STT model
      if (options.sttLanguage !== false) {
        await safeNativeCall(VoskSTT, 'initModel', { language: options.sttLanguage || 'en-us' })
        this.sttReady = true
        results.stt = true
      }
    } catch (e) {
      console.warn('STT init skipped:', e.message)
    }

    try {
      // Init LLM model
      if (options.modelPath || options.autoLoadModel !== false) {
        await safeNativeCall(LocalLLM, 'loadModel', {
          modelPath: options.modelPath || '',
          threads: options.threads || 4,
          contextSize: options.contextSize || 2048,
          gpuLayers: options.gpuLayers || 0,
          systemPrompt: options.systemPrompt || this.systemPrompt
        })
        this.llmReady = true
        results.llm = true
      }
    } catch (e) {
      console.warn('LLM init skipped:', e.message)
    }

    return results
  }

  // ═══ LLM Methods ═══

  /**
   * Get list of available GGUF models on device
   */
  async getModels() {
    try {
      if (!nativePluginsAvailable || !LocalLLM) return { models: [], modelsDir: '', loaded: false }
      return await safeNativeCall(LocalLLM, 'getModels')
    } catch (e) {
      return { models: [], modelsDir: '', loaded: false }
    }
  }

  /**
   * Load a specific model
   */
  async loadModel(modelPath, options = {}) {
    if (!nativePluginsAvailable || !LocalLLM) throw new Error('Native LLM plugin not available. Using web AI fallback.')
    const result = await safeNativeCall(LocalLLM, 'loadModel', {
      modelPath,
      threads: options.threads || 4,
      contextSize: options.contextSize || 2048,
      gpuLayers: options.gpuLayers || 0,
      systemPrompt: options.systemPrompt || this.systemPrompt
    })
    this.llmReady = true
    return result
  }

  /**
   * Generate AI response from text prompt
   */
  async generate(prompt, options = {}) {
    // Web fallback — use when not native OR native plugins unavailable
    if ((!isNative || !nativePluginsAvailable) && webFallback) {
      this.isGenerating = true
      this._emit('generatingStart', { prompt })
      try {
        const result = await webFallback.mockGenerate(prompt)
        this.chatHistory.push({ role: 'user', content: prompt })
        this.chatHistory.push({ role: 'assistant', content: result.text })
        this.isGenerating = false
        this._emit('generatingEnd', result)
        return result
      } catch (e) {
        this.isGenerating = false
        throw e
      }
    }

    if (!this.llmReady) {
      // Try to auto-load model
      try {
        await this.loadModel('')
      } catch (e) {
        throw new Error('No LLM model loaded. Download and load a model first.')
      }
    }

    this.isGenerating = true
    this._emit('generatingStart', { prompt })

    try {
      // Check if prompt has device commands and add context
      const deviceContext = await this._getDeviceContextForPrompt(prompt)
      const enrichedPrompt = deviceContext ? `${prompt}\n\n[Device Info: ${deviceContext}]` : prompt

      // Add to history
      this.chatHistory.push({ role: 'user', content: prompt })

      const result = await LocalLLM.generate({
        prompt: enrichedPrompt,
        temperature: options.temperature || 0.7,
        maxTokens: options.maxTokens || 512,
        role: 'user'
      })

      // Add response to history
      this.chatHistory.push({ role: 'assistant', content: result.text })

      this.isGenerating = false
      this._emit('generatingEnd', result)
      return result
    } catch (e) {
      this.isGenerating = false
      this._emit('generatingError', { error: e.message })
      throw e
    }
  }

  /**
   * Stop the loaded model
   */
  async stopModel() {
    try { if (nativePluginsAvailable && LocalLLM) await LocalLLM.stopModel() } catch {}
    this.llmReady = false
  }

  /**
   * Download a GGUF model
   */
  async downloadModel(url, filename) {
    if (!nativePluginsAvailable || !LocalLLM) throw new Error('Native LLM plugin not available on this device.')
    return await LocalLLM.downloadModel({ url, filename })
  }

  /**
   * Get LLM status
   */
  async getLLMStatus() {
    if (!nativePluginsAvailable || !LocalLLM) return { loaded: false, model: null }
    try { return await LocalLLM.getStatus() } catch { return { loaded: false, model: null } }
  }

  // ═══ STT Methods ═══

  /**
   * Download Vosk STT model
   */
  async downloadSTTModel(language = 'en-us') {
    if (!nativePluginsAvailable || !VoskSTT) throw new Error('Native STT plugin not available on this device.')
    return await VoskSTT.downloadModel({ language })
  }

  /**
   * Initialize STT with a language
   */
  async initSTT(language = 'en-us') {
    if (!nativePluginsAvailable || !VoskSTT) throw new Error('Native STT plugin not available on this device.')
    const result = await VoskSTT.initModel({ language })
    this.sttReady = true
    return result
  }

  /**
   * Start listening for voice input
   */
  async startListening() {
    if (!nativePluginsAvailable || !VoskSTT) {
      throw new Error('Voice recognition not available — native STT plugin missing.')
    }
    if (!this.sttReady) {
      throw new Error('STT model not initialized. Call initSTT() first.')
    }
    
    const result = await safeNativeCall(VoskSTT, 'startListening', { sampleRate: 16000 })
    this.isListening = true
    this._emit('listeningStart')
    return result
  }

  /**
   * Stop listening
   */
  async stopListening() {
    try {
      if (nativePluginsAvailable && VoskSTT) await VoskSTT.stopListening()
    } catch {}
    this.isListening = false
    this._emit('listeningStop')
    return { success: true }
  }

  /**
   * Get available STT models
   */
  async getSTTModels() {
    if (!nativePluginsAvailable || !VoskSTT) return { models: [] }
    try { return await VoskSTT.getModels() } catch { return { models: [] } }
  }

  // ═══ TTS Methods ═══

  /**
   * Speak text out loud
   */
  async speak(text, options = {}) {
    this.isSpeaking = true
    this._emit('speakingStart', { text })
    
    // Web fallback — use when not native OR native plugins unavailable
    if ((!isNative || !nativePluginsAvailable) && webFallback) {
      try {
        await webFallback.speakWeb(text, options)
      } catch (e) { /* ignore */ }
      this.isSpeaking = false
      this._emit('speakingEnd')
      return { success: true }
    }
    
    try {
      const result = await LocalTTS.speak({
        text,
        language: options.language || 'hi-IN',
        rate: options.rate || 1.0,
        pitch: options.pitch || 1.0,
        queue: options.queue || false,
        waitForComplete: options.waitForComplete || false
      })
      
      if (!options.waitForComplete) {
        // Will be set to false by ttsEvent listener
        setTimeout(() => { this.isSpeaking = false }, 100)
      } else {
        this.isSpeaking = false
      }
      
      this._emit('speakingEnd')
      return result
    } catch (e) {
      this.isSpeaking = false
      throw e
    }
  }

  /**
   * Stop speaking
   */
  async stopSpeaking() {
    try { if (nativePluginsAvailable && LocalTTS) await LocalTTS.stop() } catch {}
    this.isSpeaking = false
  }

  /**
   * Set TTS language
   */
  async setTTSLanguage(language) {
    if (!nativePluginsAvailable || !LocalTTS) return { success: false }
    try { return await LocalTTS.setLanguage({ language }) } catch { return { success: false } }
  }

  /**
   * Get available TTS voices
   */
  async getTTSVoices() {
    if (!nativePluginsAvailable || !LocalTTS) return { voices: [] }
    try { return await LocalTTS.getVoices() } catch { return { voices: [] } }
  }

  // ═══ Device Commands ═══

  async getBattery() { 
    if ((!isNative || !nativePluginsAvailable) && webFallback) return webFallback.mockBattery()
    try { return await safeNativeCall(DeviceCommands, 'getBattery') } catch { return webFallback?.mockBattery() || { level: -1, status: 'unknown' } }
  }
  async getNetwork() { 
    if ((!isNative || !nativePluginsAvailable) && webFallback) return webFallback.mockNetwork()
    try { return await safeNativeCall(DeviceCommands, 'getNetwork') } catch { return webFallback?.mockNetwork() || { connected: false, type: 'unknown' } }
  }
  async getDeviceInfo() { 
    if ((!isNative || !nativePluginsAvailable) && webFallback) return webFallback.mockDeviceInfo()
    try { return await safeNativeCall(DeviceCommands, 'getDeviceInfo') } catch { return webFallback?.mockDeviceInfo() || { brand: 'Unknown', model: 'Device' } }
  }
  async getDateTime() { 
    if ((!isNative || !nativePluginsAvailable) && webFallback) return webFallback.mockDateTime()
    try { return await safeNativeCall(DeviceCommands, 'getDateTime') } catch { return webFallback?.mockDateTime() || { time: new Date().toLocaleTimeString(), date: new Date().toLocaleDateString() } }
  }
  async makeCall(number) { 
    if (!isNative || !nativePluginsAvailable) { window.open('tel:' + number); return { success: true } }
    try { return await safeNativeCall(DeviceCommands, 'makeCall', { number }) } catch { window.open('tel:' + number); return { success: true } }
  }
  async sendSMS(number, message) { 
    if (!isNative || !nativePluginsAvailable) return { success: false, message: 'SMS plugin not available' }
    try { return await safeNativeCall(DeviceCommands, 'sendSMS', { number, message }) } catch { return { success: false, message: 'SMS failed' } }
  }
  async openUrl(url) { 
    if (!isNative || !nativePluginsAvailable) { window.open(url, '_blank'); return { success: true } }
    try { return await safeNativeCall(DeviceCommands, 'openUrl', { url }) } catch { window.open(url, '_blank'); return { success: true } }
  }
  async openApp(packageName) { 
    if (!isNative || !nativePluginsAvailable) return { success: false, message: 'App launch not available' }
    try { return await safeNativeCall(DeviceCommands, 'openApp', { package: packageName }) } catch { return { success: false, message: 'openApp failed' } }
  }
  async setVolume(level, stream = 'media') { 
    if (!isNative || !nativePluginsAvailable) return { success: false, message: 'Volume control not available' }
    try { return await safeNativeCall(DeviceCommands, 'setVolume', { level, stream }) } catch { return { success: false, message: 'setVolume failed' } }
  }
  async getVolume() { 
    if (!isNative || !nativePluginsAvailable) return { media: 50, ring: 50, alarm: 50, notification: 50 }
    try { return await safeNativeCall(DeviceCommands, 'getVolume') } catch { return { media: 50, ring: 50, alarm: 50, notification: 50 } }
  }
  async vibrate(duration = 200) { 
    if (!isNative || !nativePluginsAvailable) { navigator.vibrate?.(duration); return { success: true } }
    try { return await safeNativeCall(DeviceCommands, 'vibrate', { duration }) } catch { navigator.vibrate?.(duration); return { success: true } }
  }
  async openSettings(setting) { 
    if (!isNative || !nativePluginsAvailable) return { success: false, message: 'Settings not available' }
    try { return await safeNativeCall(DeviceCommands, 'openSettings', { setting }) } catch { return { success: false, message: 'openSettings failed' } }
  }

  // ═══ High-Level AI Agent Methods ═══

  /**
   * Full voice conversation flow:
   * Listen → Transcribe → Think → Generate → Speak
   */
  async voiceChat(options = {}) {
    // Step 1: Listen
    this._emit('agentStep', { step: 'listening', message: '🎤 Sun raha hoon...' })
    
    return new Promise((resolve, reject) => {
      let finalText = ''
      
      const onResult = (event) => {
        if (event.isFinal || event.isComplete) {
          finalText = event.text || finalText
          try { VoskSTT?.removeAllListeners?.('speechResult') } catch {}
          
          if (!finalText) {
            this._emit('agentStep', { step: 'error', message: 'Kuch sunai nahi diya' })
            resolve({ text: '', response: '' })
            return
          }

          this._emit('agentStep', { step: 'transcribed', message: finalText })
          
          // Step 2: Generate
          this._emit('agentStep', { step: 'thinking', message: '🧠 Soch raha hoon...' })
          
          this.generate(finalText, options)
            .then(result => {
              this._emit('agentStep', { step: 'generated', message: result.text })
              
              // Step 3: Speak (if enabled)
              if (options.speakResponse !== false) {
                this._emit('agentStep', { step: 'speaking', message: '🔊 Bol raha hoon...' })
                this.speak(result.text, { language: options.language || 'hi-IN' })
              }
              
              // Execute any device commands detected
              this._executeDeviceCommands(finalText, result.text)
              
              resolve({ text: finalText, response: result.text })
            })
            .catch(e => {
              this._emit('agentStep', { step: 'error', message: e.message })
              reject(e)
            })
        } else if (event.partial) {
          this._emit('agentStep', { step: 'partial', message: event.partial })
        }
      }

      VoskSTT?.addListener?.('speechResult', onResult)
      
      this.startListening().catch(e => {
        try { VoskSTT?.removeAllListeners?.('speechResult') } catch {}
        reject(e)
      })
    })
  }

  /**
   * Text chat with AI (type → think → respond → optionally speak)
   */
  async textChat(text, options = {}) {
    const result = await this.generate(text, options)
    
    if (options.speakResponse) {
      await this.speak(result.text, { language: options.language || 'hi-IN' })
    }
    
    // Execute device commands if detected
    await this._executeDeviceCommands(text, result.text)
    
    return result
  }

  /**
   * Quick command — Process a single command and return result
   * e.g., "battery check karo", "time kya hua", "volume 50 karo"
   */
  async quickCommand(command) {
    const cmd = command.toLowerCase()
    
    // Battery
    if (cmd.includes('battery') || cmd.includes('charge')) {
      const battery = await this.getBattery()
      return `🔋 Battery: ${battery.level}% | ${battery.status} | ${battery.chargingType} | Temp: ${battery.temperature}°C`
    }
    
    // Time
    if (cmd.includes('time') || cmd.includes('samay') || cmd.includes('waqt')) {
      const dt = await this.getDateTime()
      return `🕐 ${dt.time} | ${dt.day}, ${dt.date}`
    }
    
    // Network
    if (cmd.includes('network') || cmd.includes('wifi') || cmd.includes('internet')) {
      const net = await this.getNetwork()
      return `📶 ${net.connected ? 'Connected' : 'Disconnected'} | ${net.type} | WiFi: ${net.ssid || 'Off'}`
    }
    
    // Volume
    if (cmd.includes('volume') || cmd.includes('awaaz')) {
      const match = cmd.match(/(\d+)/)
      if (match) {
        await this.setVolume(parseInt(match[1]))
        return `🔊 Volume set to ${match[1]}%`
      }
      const vol = await this.getVolume()
      return `🔊 Media: ${vol.media}% | Ring: ${vol.ring}% | Alarm: ${vol.alarm}%`
    }
    
    // Device info
    if (cmd.includes('device') || cmd.includes('phone') || cmd.includes('mobile info')) {
      const info = await this.getDeviceInfo()
      return `📱 ${info.brand} ${info.model} | Android ${info.androidVersion} | ${info.processors} cores | RAM: ${info.maxMemoryMB}MB`
    }
    
    // Call
    if (cmd.includes('call') || cmd.includes('dial')) {
      const match = cmd.match(/(\d{10,})/)
      if (match) {
        await this.makeCall(match[1])
        return `📞 Calling ${match[1]}...`
      }
      return '📞 Number batao — e.g., "call 9876543210"'
    }
    
    // Open URL
    if (cmd.includes('open') && (cmd.includes('http') || cmd.includes('www') || cmd.includes('.com'))) {
      const urlMatch = cmd.match(/(https?:\/\/[^\s]+|www\.[^\s]+|[a-z]+\.(com|in|org)[^\s]*)/i)
      if (urlMatch) {
        await this.openUrl(urlMatch[1])
        return `🌐 Opening ${urlMatch[1]}...`
      }
    }
    
    // Vibrate
    if (cmd.includes('vibrate') || cmd.includes('haptic')) {
      await this.vibrate(300)
      return '📳 Vibrated!'
    }
    
    // Settings
    if (cmd.includes('settings') || cmd.includes('setting')) {
      const setting = cmd.includes('wifi') ? 'wifi' : 
                      cmd.includes('bluetooth') ? 'bluetooth' :
                      cmd.includes('display') ? 'display' :
                      cmd.includes('sound') ? 'sound' : ''
      await this.openSettings(setting)
      return '⚙️ Settings opened!'
    }
    
    // Not a quick command — fallback to LLM
    return null
  }

  // ═══ Event System ═══

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = []
    this.listeners[event].push(callback)
    return () => {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback)
    }
  }

  _emit(event, data) {
    const cbs = this.listeners[event] || []
    cbs.forEach(cb => cb(data))
  }

  // ═══ Internal Helpers ═══

  _setupListeners() {
    if (!isNative || !nativePluginsAvailable) return  // Skip if no native plugins
    
    try {
      // Listen for speech results
      VoskSTT?.addListener?.('speechResult', (event) => {
        this._emit('speechResult', event)
      })
    } catch (e) { console.warn('[JARVIS-AI] VoskSTT listener setup failed:', e.message) }
      
    try {
      // Listen for TTS events
      LocalTTS?.addListener?.('ttsEvent', (event) => {
        if (event.status === 'done') {
          this.isSpeaking = false
          this._emit('speakingEnd')
        }
      })
    } catch (e) { console.warn('[JARVIS-AI] LocalTTS listener setup failed:', e.message) }

    try {
      // Listen for download progress
      LocalLLM?.addListener?.('downloadProgress', (event) => {
        this._emit('downloadProgress', event)
      })
    } catch (e) { console.warn('[JARVIS-AI] LocalLLM listener setup failed:', e.message) }
      
    try {
      VoskSTT?.addListener?.('sttModelProgress', (event) => {
        this._emit('sttDownloadProgress', event)
      })
    } catch (e) { console.warn('[JARVIS-AI] VoskSTT model listener setup failed:', e.message) }
  }

  async _getDeviceContextForPrompt(prompt) {
    const p = prompt.toLowerCase()
    const contexts = []
    
    try {
      if (p.includes('battery') || p.includes('charge')) {
        const b = await this.getBattery()
        contexts.push(`Battery: ${b.level}%, ${b.status}, Temp: ${b.temperature}°C`)
      }
      if (p.includes('time') || p.includes('samay') || p.includes('waqt') || p.includes('date') || p.includes('din')) {
        const dt = await this.getDateTime()
        contexts.push(`Time: ${dt.full}, Day: ${dt.day}`)
      }
      if (p.includes('network') || p.includes('wifi') || p.includes('internet')) {
        const n = await this.getNetwork()
        contexts.push(`Network: ${n.connected ? 'Connected' : 'Disconnected'}, Type: ${n.type}`)
      }
      if (p.includes('device') || p.includes('phone') || p.includes('mobile')) {
        const d = await this.getDeviceInfo()
        contexts.push(`Device: ${d.brand} ${d.model}, Android ${d.androidVersion}, ${d.processors} cores`)
      }
    } catch (e) {
      // Ignore device command errors in context
    }
    
    return contexts.join(' | ')
  }

  async _executeDeviceCommands(userText, aiResponse) {
    const combined = (userText + ' ' + aiResponse).toLowerCase()
    
    try {
      // Auto-execute simple commands detected in conversation
      if (combined.includes('vibrate') && userText.toLowerCase().includes('vibrate')) {
        await this.vibrate(200)
      }
    } catch (e) {
      // Silently ignore auto-command errors
    }
  }

  /**
   * Clear chat history
   */
  clearHistory() {
    this.chatHistory = []
  }

  /**
   * Get full status of all AI components
   */
  async getFullStatus() {
    if (!isNative || !nativePluginsAvailable) {
      return {
        llm: { loaded: false, mode: 'web-fallback' },
        stt: { modelReady: false, mode: 'web-fallback', webSpeechAvailable: typeof window !== 'undefined' && 'webkitSpeechRecognition' in window },
        tts: { ready: typeof window !== 'undefined' && 'speechSynthesis' in window, mode: 'web-fallback' },
        chatHistoryLength: this.chatHistory.length
      }
    }

    const [llm, stt, tts] = await Promise.allSettled([
      safeNativeCall(LocalLLM, 'getStatus'),
      safeNativeCall(VoskSTT, 'getStatus'),
      safeNativeCall(LocalTTS, 'getStatus')
    ])
    
    return {
      llm: llm.status === 'fulfilled' ? llm.value : { loaded: false, error: llm.reason?.message },
      stt: stt.status === 'fulfilled' ? stt.value : { modelReady: false, error: stt.reason?.message },
      tts: tts.status === 'fulfilled' ? tts.value : { ready: false, error: tts.reason?.message },
      chatHistoryLength: this.chatHistory.length
    }
  }
}

// ═══════════════════════════════════════════════════════════
//  Singleton Export
// ═══════════════════════════════════════════════════════════
const jarvisAI = new JarvisAIEngine()
export default jarvisAI

// Also export individual plugins for direct access
export { LocalLLM, VoskSTT, LocalTTS, DeviceCommands }
