/**
 * 🎙️ JARVIS Gemini Voice Command Engine
 * ═══════════════════════════════════════
 * - Web Speech Recognition → Gemini AI interpretation
 * - Natural language trading commands
 * - Hindi + English support
 * - Command parsing: "Buy 1000 rupees Nifty CE near ATM"
 * - Voice feedback with Web Speech Synthesis
 * - Continuous listening mode
 */

import { getApiBase } from './apiBase'

class GeminiVoiceEngine {
  constructor() {
    this.recognition = null
    this.synthesis = window.speechSynthesis || null
    this.isListening = false
    this.language = 'en-IN'
    this.onResult = null
    this.onCommand = null
    this.onError = null
    this.commandHistory = []
    this._initRecognition()
  }

  _initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('[VoiceEngine] Speech Recognition not supported')
      return
    }

    try {
      this.recognition = new SpeechRecognition()
    } catch (e) {
      console.warn('[VoiceEngine] SpeechRecognition constructor failed:', e.message)
      return
    }
    this.recognition.continuous = false
    this.recognition.interimResults = true
    this.recognition.lang = this.language
    this.recognition.maxAlternatives = 1

    this.recognition.onresult = (event) => {
      const last = event.results[event.results.length - 1]
      const transcript = last[0].transcript.trim()
      const isFinal = last.isFinal

      if (this.onResult) this.onResult(transcript, isFinal)
      
      if (isFinal) {
        this._processCommand(transcript)
      }
    }

    this.recognition.onerror = (event) => {
      console.warn('[VoiceEngine] Error:', event.error)
      this.isListening = false
      if (this.onError) this.onError(event.error)
    }

    this.recognition.onend = () => {
      this.isListening = false
    }
  }

  get isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  }

  startListening(lang = 'en-IN') {
    if (!this.recognition) return false
    
    this.language = lang
    this.recognition.lang = lang
    
    try {
      this.recognition.start()
      this.isListening = true
      return true
    } catch (e) {
      console.warn('[VoiceEngine] Start failed:', e.message)
      return false
    }
  }

  stopListening() {
    if (this.recognition) {
      try { this.recognition.stop() } catch {}
    }
    this.isListening = false
  }

  /**
   * Send transcript to Gemini for intelligent command parsing
   */
  async _processCommand(transcript) {
    try {
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/miniapp/voice/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: transcript, 
          language: this.language 
        }),
      })

      if (res.ok) {
        const data = await res.json()
        const command = data.command || data

        this.commandHistory.unshift({
          transcript,
          command,
          timestamp: Date.now(),
        })

        if (this.commandHistory.length > 50) {
          this.commandHistory = this.commandHistory.slice(0, 50)
        }

        if (this.onCommand) this.onCommand(command)
        
        // Voice feedback
        if (command.reply) {
          this.speak(command.reply)
        }

        return command
      }
    } catch {
      // Fallback: local command parsing
      const command = this._parseLocally(transcript)
      if (this.onCommand) this.onCommand(command)
      return command
    }
  }

  /**
   * Local command parsing (works offline)
   */
  _parseLocally(text) {
    const lower = text.toLowerCase()

    // Price check
    if (lower.match(/price|kya hai|kitna|what.?is|check/)) {
      const symbols = this._extractSymbols(lower)
      return { action: 'price_check', symbols, text, reply: `Checking price for ${symbols.join(', ')}` }
    }

    // Buy command
    if (lower.match(/buy|kharido|purchase|long/)) {
      return this._parseTradingCommand(lower, 'buy', text)
    }

    // Sell command
    if (lower.match(/sell|becho|short/)) {
      return this._parseTradingCommand(lower, 'sell', text)
    }

    // Portfolio
    if (lower.match(/portfolio|holdings|my stocks|mere stocks/)) {
      return { action: 'show_portfolio', text, reply: 'Opening your portfolio' }
    }

    // Market status
    if (lower.match(/market|nifty|sensex|bank nifty/)) {
      return { action: 'market_status', text, reply: 'Loading market overview' }
    }

    // Alert
    if (lower.match(/alert|notify|batao jab/)) {
      const symbols = this._extractSymbols(lower)
      const priceMatch = lower.match(/(\d+[\d,.]*)/g)
      return { 
        action: 'set_alert', 
        symbols, 
        price: priceMatch ? parseFloat(priceMatch[0].replace(/,/g, '')) : null,
        text, 
        reply: `Setting alert for ${symbols.join(', ')}` 
      }
    }

    // News
    if (lower.match(/news|khabar|update/)) {
      return { action: 'show_news', text, reply: 'Fetching latest market news' }
    }

    // AI analysis
    if (lower.match(/analyze|analysis|predict|signal|jarvis/)) {
      const symbols = this._extractSymbols(lower)
      return { action: 'ai_analysis', symbols, text, reply: `Running AI analysis on ${symbols.join(', ')}` }
    }

    return { action: 'chat', text, reply: null }
  }

  _parseTradingCommand(lower, side, text) {
    const symbols = this._extractSymbols(lower)
    const amountMatch = lower.match(/(\d+[\d,.]*)\s*(rupee|rs|₹|inr|dollar|\$|usdt)/i)
    const qtyMatch = lower.match(/(\d+[\d,.]*)\s*(lot|share|qty|quantity|unit)/i)
    
    let amount = amountMatch ? parseFloat(amountMatch[1].replace(/,/g, '')) : null
    let qty = qtyMatch ? parseInt(qtyMatch[1].replace(/,/g, '')) : null

    // Options detection
    let optionType = null
    if (lower.match(/\bce\b|call/)) optionType = 'CE'
    if (lower.match(/\bpe\b|put/)) optionType = 'PE'

    const atm = lower.includes('atm') || lower.includes('at the money')

    return {
      action: `${side}_order`,
      symbols,
      amount,
      qty,
      optionType,
      atm,
      text,
      reply: `${side === 'buy' ? 'Buying' : 'Selling'} ${symbols.join(', ')}${amount ? ` worth ₹${amount}` : ''}${optionType ? ` ${optionType}` : ''}`
    }
  }

  _extractSymbols(text) {
    const symbolPatterns = [
      /\b(btc|bitcoin)\b/i,
      /\b(eth|ethereum)\b/i,
      /\b(nifty|nifty\s*50)\b/i,
      /\b(bank\s*nifty|banknifty)\b/i,
      /\b(sensex)\b/i,
      /\b(reliance|tcs|infosys|hdfc|sbi|wipro|hcl|tatamotors|adani|icici)\b/i,
      /\b(sol|solana)\b/i,
      /\b(xrp|ripple)\b/i,
      /\b(doge|dogecoin)\b/i,
      /\b(bnb)\b/i,
    ]

    const found = []
    for (const p of symbolPatterns) {
      const match = text.match(p)
      if (match) found.push(match[1].toUpperCase())
    }

    return found.length > 0 ? found : ['MARKET']
  }

  /**
   * Text-to-Speech (voice feedback)
   */
  speak(text, lang = 'en-IN') {
    if (!this.synthesis) return

    // Cancel any ongoing speech
    this.synthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    utterance.rate = 1.0
    utterance.pitch = 1.0
    utterance.volume = 0.8

    // Prefer Indian English voice
    const voices = this.synthesis.getVoices()
    const indianVoice = voices.find(v => v.lang === 'en-IN') || voices.find(v => v.lang.startsWith('en'))
    if (indianVoice) utterance.voice = indianVoice

    this.synthesis.speak(utterance)
  }

  setLanguage(lang) {
    this.language = lang
    if (this.recognition) this.recognition.lang = lang
  }

  getHistory() {
    return this.commandHistory
  }

  clearHistory() {
    this.commandHistory = []
  }
}

const voiceEngine = new GeminiVoiceEngine()
export default voiceEngine
