/**
 * 🧠 JARVIS Offline AI Engine (llama.cpp Bridge)
 * ════════════════════════════════════════════════
 * Native plugin bridge for on-device LLM inference
 * Uses Capacitor plugin to communicate with llama.cpp
 * Works in airplane mode — "Hey JARVIS" even offline!
 * Falls back to WebLLM when native not available
 */

class OfflineAIEngine {
  constructor() {
    this.isNative = false
    this.isReady = false
    this.isLoading = false
    this.currentModel = null
    this.modelInfo = null
    this.listeners = new Map()
  }

  /**
   * Initialize the offline AI engine
   * Checks native capabilities first, then web fallback
   */
  async init() {
    if (this.isReady) return true

    // Check if running in Capacitor native
    if (window.Capacitor?.isNativePlatform?.()) {
      try {
        const { LocalLLM } = await import('@capacitor/core').then(m => m.Plugins).catch(() => ({}))
        if (LocalLLM) {
          const status = await LocalLLM.getStatus()
          this.isNative = true
          this.isReady = status.ready || false
          this.currentModel = status.model || null
          this.modelInfo = status
          console.log('[OfflineAI] Native LLM available:', status)
          return true
        }
      } catch (e) {
        console.warn('[OfflineAI] Native LLM not available:', e)
      }
    }

    // Web fallback: check WebGPU/WASM support
    try {
      const hasWebGPU = 'gpu' in navigator
      const hasWASM = typeof WebAssembly === 'object'
      console.log(`[OfflineAI] Web fallback — WebGPU: ${hasWebGPU}, WASM: ${hasWASM}`)
      this.isReady = hasWASM // WASM is minimum requirement
      return this.isReady
    } catch {
      return false
    }
  }

  /**
   * Download and load a GGUF model
   * @param {string} modelName - e.g. 'tinyllama-1.1b'
   * @param {function} onProgress - progress callback (0-100)
   */
  async loadModel(modelName = 'auto', onProgress = null) {
    this.isLoading = true
    this._emit('loading', { model: modelName })

    try {
      if (this.isNative) {
        const { LocalLLM } = await import('@capacitor/core').then(m => m.Plugins)
        const result = await LocalLLM.loadModel({
          model: modelName,
          onProgress: (p) => {
            onProgress?.(p.progress)
            this._emit('progress', p)
          }
        })
        this.currentModel = result.model
        this.isReady = true
        this.isLoading = false
        this._emit('ready', { model: result.model })
        return true
      }

      // Web fallback: use lightweight WASM model
      console.log('[OfflineAI] Web model loading not implemented yet')
      this.isLoading = false
      return false
    } catch (e) {
      this.isLoading = false
      this._emit('error', { message: e.message })
      console.error('[OfflineAI] Model load failed:', e)
      return false
    }
  }

  /**
   * Chat with the offline AI model
   * @param {string} message - User message
   * @param {object} options - temperature, maxTokens, etc.
   * @returns {AsyncGenerator<string>} - Streaming response chunks
   */
  async *chat(message, options = {}) {
    if (!this.isReady) {
      yield 'Offline AI not ready. Please download a model first.'
      return
    }

    const defaults = {
      temperature: 0.7,
      maxTokens: 512,
      systemPrompt: 'You are JARVIS, a helpful AI trading assistant. You speak Hindi and English. You help with trading, crypto, Indian stocks, and general knowledge. Be concise and helpful.',
      ...options
    }

    try {
      if (this.isNative) {
        const { LocalLLM } = await import('@capacitor/core').then(m => m.Plugins)
        
        // Native streaming inference
        const stream = await LocalLLM.chatStream({
          message,
          system: defaults.systemPrompt,
          temperature: defaults.temperature,
          maxTokens: defaults.maxTokens
        })

        for await (const chunk of stream) {
          yield chunk.text || chunk.token || ''
        }
        return
      }

      // Web fallback: simple response
      yield `[Offline mode] Main samajh gaya: "${message}". Abhi offline AI model download karein Settings mein jaake.`
    } catch (e) {
      yield `Error: ${e.message}`
    }
  }

  /**
   * Simple non-streaming chat
   */
  async chatSync(message, options = {}) {
    let response = ''
    for await (const chunk of this.chat(message, options)) {
      response += chunk
    }
    return response
  }

  /**
   * Get list of available/downloaded models
   */
  async getModels() {
    const models = [
      {
        id: 'tinyllama-1.1b',
        name: 'TinyLlama 1.1B',
        size: '670 MB',
        quality: 'Good',
        speed: 'Fast',
        minRam: '3 GB',
        downloaded: false,
        recommended: true,
        description: 'Fast, good for basic queries'
      },
      {
        id: 'llama-3.2-1b',
        name: 'Llama 3.2 1B',
        size: '700 MB',
        quality: 'Very Good',
        speed: 'Fast',
        minRam: '3 GB',
        downloaded: false,
        recommended: true,
        description: 'Best balance of speed and quality'
      },
      {
        id: 'phi-3-mini',
        name: 'Phi-3 Mini',
        size: '2.3 GB',
        quality: 'Excellent',
        speed: 'Medium',
        minRam: '6 GB',
        downloaded: false,
        description: 'High quality but needs more RAM'
      }
    ]

    if (this.isNative) {
      try {
        const { LocalLLM } = await import('@capacitor/core').then(m => m.Plugins)
        const result = await LocalLLM.getDownloadedModels()
        const downloaded = result.models || []
        models.forEach(m => {
          m.downloaded = downloaded.some(d => d.id === m.id || d.name === m.name)
        })
      } catch {}
    }

    return models
  }

  /**
   * Delete a downloaded model
   */
  async deleteModel(modelId) {
    if (this.isNative) {
      try {
        const { LocalLLM } = await import('@capacitor/core').then(m => m.Plugins)
        await LocalLLM.deleteModel({ model: modelId })
        if (this.currentModel === modelId) {
          this.currentModel = null
          this.isReady = false
        }
        return true
      } catch { return false }
    }
    return false
  }

  /**
   * Get device capabilities for AI
   */
  async getDeviceInfo() {
    const info = {
      platform: window.Capacitor?.getPlatform?.() || 'web',
      hasWebGPU: 'gpu' in navigator,
      hasWASM: typeof WebAssembly === 'object',
      ram: navigator.deviceMemory || 'unknown',
      cores: navigator.hardwareConcurrency || 4,
      isNative: this.isNative,
      currentModel: this.currentModel,
      isReady: this.isReady,
    }
    return info
  }

  // Event emitter
  _emit(event, data) {
    this.listeners.forEach((cb, id) => {
      if (id.startsWith(event)) cb(data)
    })
  }

  on(event, callback) {
    const id = `${event}_${Date.now()}`
    this.listeners.set(id, callback)
    return () => this.listeners.delete(id)
  }
}

const offlineAI = new OfflineAIEngine()
export default offlineAI
