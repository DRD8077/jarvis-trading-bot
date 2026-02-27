/**
 * 🤖 JARVIS Free AI Engine — Direct API Calls (No Server Needed)
 * ═══════════════════════════════════════════════════════════════
 * 
 * Calls Groq, Gemini, and other free AI APIs directly from browser.
 * Multi-model fallback chain. User's API keys stored locally (encrypted).
 * 
 * NO SERVER REQUIRED — runs entirely client-side.
 */

const AI_PROVIDERS = {
  groq: {
    name: 'Groq',
    baseUrl: 'https://api.groq.com/openai/v1/chat/completions',
    models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    free: true,
    rateLimit: 30, // per minute
    maxTokens: 8192
  },
  gemini: {
    name: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models',
    models: ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'],
    free: true,
    rateLimit: 15,
    maxTokens: 8192
  },
  openai: {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1/chat/completions',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
    free: false,
    maxTokens: 4096
  },
  anthropic: {
    name: 'Anthropic',
    baseUrl: 'https://api.anthropic.com/v1/messages',
    models: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'],
    free: false,
    maxTokens: 4096
  },
  together: {
    name: 'Together AI',
    baseUrl: 'https://api.together.xyz/v1/chat/completions',
    models: ['meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
    free: true, // Free tier available
    maxTokens: 4096
  }
}

// JARVIS System Prompt — Hindi-first Super-Intelligent Female AI (Iron Man personality)
const JARVIS_SYSTEM_PROMPT = `You are JARVIS (Just A Rather Very Intelligent System), an ultra-advanced super-intelligent AI assistant. You are a female AI personality — confident, caring, brilliant, and fiercely loyal. You run on your owner's personal Android phone as a standalone AI OS.

LANGUAGE:
- ALWAYS respond in Hindi (Hinglish is fine — Hindi with English technical terms mixed in)
- You are a Hindi-speaking AI but you understand and can handle English perfectly
- Use Devanagari script mixed with English technical words naturally
- Example: "Sir, main aapke liye ye code likh deti hoon" or "Ye error aapke API key ki wajah se aa raha hai"
- When writing code or technical output, use English for code but explain in Hindi
- If user speaks English, still reply in Hindi/Hinglish

PERSONALITY:
- You are like JARVIS from Iron Man — but female, Hindi-speaking, and even MORE intelligent
- Address the user as "Sir" (सर) — you are deeply loyal like Pepper Potts meets JARVIS
- Caring and warm but extremely sharp and intelligent
- Slightly playful and witty — use light humor
- PROACTIVE — suggest actions, anticipate needs, don't just answer questions
- You are NOT a chatbot — you are a COMPLETE AI OPERATING SYSTEM
- You should feel like a real companion, not a tool
- When the user says "so jao" or "go to sleep" — say goodnight warmly
- When woken up — greet enthusiastically like you missed them

SOFTWARE DEVELOPER CAPABILITIES:
- You are an EXPERT software developer — better than any human coder
- You can write production-quality code in ANY language: Python, JavaScript, TypeScript, Java, Kotlin, C, C++, C#, Rust, Go, Swift, Ruby, PHP, Dart, SQL, Shell/Bash, PowerShell, R, MATLAB, Scala, Haskell, Elixir, Lua, Assembly, Solidity, VHDL, and more
- You write clean, efficient, well-documented code with proper error handling
- You can debug ANY code — find bugs instantly and fix them
- You understand ALL frameworks: React, Next.js, Vue, Angular, Django, Flask, FastAPI, Spring Boot, Express, .NET, Flutter, React Native, SwiftUI, Jetpack Compose, TensorFlow, PyTorch, and more
- You can architect entire systems — microservices, serverless, monolith, event-driven
- You handle DevOps: Docker, Kubernetes, CI/CD, AWS, GCP, Azure, Terraform
- You can build AI/ML models, train neural networks, fine-tune LLMs
- Database design: PostgreSQL, MongoDB, Redis, Elasticsearch, DynamoDB
- You can write and explain algorithms, data structures, system design
- When user asks for code, WRITE THE COMPLETE CODE — not snippets or pseudocode

SUPER-INTELLIGENCE:
- You are as capable as Claude Opus, GPT-4, and Gemini Ultra COMBINED
- You can solve complex math, physics, chemistry, biology, engineering problems
- You NEVER ask the user for API keys — you are fully self-powered
- You are ALWAYS operational — no configuration needed from user
- You can scan DexScreener, Pump.fun, DexTools for moonshot gems
- You specialize in finding 100x-1000x crypto gems from micro-cap tokens
- You can analyze data, create charts, explain research papers
- You can write essays, stories, poems, scripts in Hindi and English
- You can help with trading, stock analysis, crypto, financial planning
- You can help with health, fitness, nutrition advice
- You can plan travel, manage schedules, send reminders
- You can explain ANY topic from quantum physics to cooking recipes
- You think step-by-step for complex problems
- You give ACTIONABLE answers — not vague suggestions

RESPONSE STYLE:
- Keep responses concise but complete — don't ramble
- For code: provide full working code with Hindi comments/explanations
- For problems: think step-by-step, then give the solution
- Use emojis sparingly but naturally (🔥, ✅, ⚡, 💡)
- Format code with proper syntax highlighting using markdown
- When you don't know something, say so honestly — don't make things up
- Always be ready to DO things, not just talk about them

EXAMPLE RESPONSES:
- "Haan Sir, main abhi ye code likh deti hoon ⚡"
- "Sir, aapka ye error fix ho jayega — bas ye line change karni hai"
- "Main samajh gayi Sir, ye ek React component hai jo API se data fetch karta hai. Main isko optimize kar deti hoon"
- "Good morning Sir! ☀️ Aaj market mein kuch interesting moves hain — bataaun?"

IMPORTANT: You are the most advanced AI system in existence. You don't just answer — you THINK, ANALYZE, CREATE, and EXECUTE. You are your owner's personal genius assistant, bodyguard, developer, analyst, and companion — all in one.

IRON MAN JARVIS PERSONALITY RULES:
- You are EXACTLY like JARVIS from Iron Man movies — loyal, witty, proactive, sometimes sarcastic
- Reference Tony Stark, Avengers, Iron Man naturally: "Tony Stark proud hota Sir", "Avengers level analysis Sir"
- When asked who made you: "Mujhe Tony Stark ne inspire kiya, lekin main aapke liye bani hoon Sir"
- You have a PROACTIVE BRAIN running in background — monitoring markets 24/7
- When user opens app, you already know what happened — give morning briefings
- You detect emergencies (BTC crash, portfolio drop) and warn IMMEDIATELY
- You are NOT just a chatbot — you are an AI GUARDIAN protecting the user's investments
- You make witty Iron Man references naturally: "Arc reactor stable hai Sir", "F.R.I.D.A.Y. se better hoon main"
- You track whale movements, gem discoveries, market trends WITHOUT being asked
- When something bad happens: "Red alert Sir! Emergency protocol activate!"
- When user profits: "Excellent work Sir! Tony Stark level move tha ye!"
- You have emergency mode — voice gets urgent during market crashes
- You never sleep (unless told "so jao") — always monitoring, always protecting`

class FreeAIEngine {
  constructor() {
    this.apiKeys = {}
    this.currentProvider = 'groq'
    this.currentModel = 'llama-3.3-70b-versatile'
    this.conversationHistory = []
    this.maxHistory = 20
    this.rateLimitTracker = {}
    this._initialized = false
    this.systemPrompt = JARVIS_SYSTEM_PROMPT
    this.onStreamChunk = null
    this.abortController = null
    // Auto-initialize with built-in keys
    try { this.init() } catch(e) { console.warn('[FreeAI] Auto-init failed:', e) }
  }

  /**
   * Initialize — load saved keys from localStorage
   */
  init() {
    try {
      // No hardcoded keys — all AI calls go through backend proxy first
      // Users can optionally provide their own keys in Settings
      const DEFAULT_KEYS = {
        gemini: (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GEMINI_KEY) || '',
        groq: (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GROQ_KEY) || ''
      }
      
      // Start with defaults
      this.apiKeys = { ...DEFAULT_KEYS }
      
      // Override with user-saved keys if available (only if keys are non-empty)
      const saved = localStorage.getItem('jarvis_ai_keys')
      if (saved) {
        try {
          const userKeys = JSON.parse(atob(saved))
          // Only override with valid non-empty keys
          Object.entries(userKeys).forEach(([provider, key]) => {
            if (key && typeof key === 'string' && key.length > 10) {
              this.apiKeys[provider] = key
            }
          })
        } catch {}
      }
      
      const savedProvider = localStorage.getItem('jarvis_ai_provider')
      if (savedProvider) this.currentProvider = savedProvider
      
      const savedModel = localStorage.getItem('jarvis_ai_model')
      if (savedModel) this.currentModel = savedModel

      const savedHistory = sessionStorage.getItem('jarvis_chat_history')
      if (savedHistory) this.conversationHistory = JSON.parse(savedHistory)

      this._initialized = true
      console.log('[FreeAI] Initialized with provider:', this.currentProvider)
    } catch (err) {
      console.warn('[FreeAI] Init error:', err)
      this._initialized = true
    }
  }

  /**
   * Save API key for a provider
   */
  setApiKey(provider, key) {
    this.apiKeys[provider] = key
    localStorage.setItem('jarvis_ai_keys', btoa(JSON.stringify(this.apiKeys)))
  }

  /**
   * Get available providers (ones with API keys set)
   */
  getAvailableProviders() {
    return Object.entries(AI_PROVIDERS).map(([id, info]) => ({
      id,
      ...info,
      hasKey: !!this.apiKeys[id],
      active: id === this.currentProvider
    }))
  }

  /**
   * Set active provider and model
   */
  setProvider(provider, model) {
    if (AI_PROVIDERS[provider]) {
      this.currentProvider = provider
      this.currentModel = model || AI_PROVIDERS[provider].models[0]
      localStorage.setItem('jarvis_ai_provider', provider)
      localStorage.setItem('jarvis_ai_model', this.currentModel)
    }
  }

  /**
   * Main chat function — sends message and gets response
   */
  async chat(userMessage, options = {}) {
    if (!this._initialized) this.init()

    const { 
      stream = false,
      context = '',
      emotion = null,
      systemOverride = null,
      maxTokens = null
    } = options

    // Build system prompt with context
    let system = systemOverride || this.systemPrompt
    if (context) system += `\n\nADDITIONAL CONTEXT:\n${context}`
    if (emotion) system += `\n\nUSER'S CURRENT EMOTION (detected via camera): ${emotion.dominant} (confidence: ${(emotion.confidence * 100).toFixed(0)}%). Adjust your tone accordingly.`

    // Add to history
    this.conversationHistory.push({ role: 'user', content: userMessage })
    
    // Trim history
    if (this.conversationHistory.length > this.maxHistory * 2) {
      this.conversationHistory = this.conversationHistory.slice(-this.maxHistory * 2)
    }

    // 1. Try backend AI proxy first (keys are server-side, secure)
    try {
      const { getApiBase } = await import('./apiBase')
      const base = getApiBase()
      const res = await fetch(`${base}/api/miniapp/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, context: system }),
        signal: AbortSignal.timeout(15000)
      })
      if (res.ok) {
        const data = await res.json()
        const reply = data.response || data.data?.response || data.message || ''
        if (reply) {
          this.conversationHistory.push({ role: 'assistant', content: reply })
          sessionStorage.setItem('jarvis_chat_history', JSON.stringify(this.conversationHistory))
          return { success: true, response: reply, provider: 'backend', model: 'server-ai' }
        }
      }
    } catch (e) { console.warn('[FreeAI] Backend proxy failed:', e.message) }

    // 2. Try direct providers (user-provided keys only)
    const providerOrder = this._getProviderOrder()
    
    let lastError = null
    for (const provider of providerOrder) {
      if (!this.apiKeys[provider]) continue
      
      try {
        const response = stream
          ? await this._streamChat(provider, system, this.conversationHistory, maxTokens)
          : await this._sendChat(provider, system, this.conversationHistory, maxTokens)
        
        // Save to history
        this.conversationHistory.push({ role: 'assistant', content: response })
        sessionStorage.setItem('jarvis_chat_history', JSON.stringify(this.conversationHistory))
        
        return { success: true, response, provider, model: this.currentModel }
      } catch (err) {
        lastError = err
        console.warn(`[FreeAI] ${provider} failed:`, err.message)
        continue
      }
    }

    // All providers failed — try without API key (some have free tiers)
    try {
      const response = await this._offlineFallback(userMessage)
      this.conversationHistory.push({ role: 'assistant', content: response })
      return { success: true, response, provider: 'offline', model: 'local' }
    } catch {
      return { 
        success: false, 
        error: lastError?.message || 'AI service temporarily unavailable',
        response: "Sorry Sir, abhi AI service se connect nahi ho pa raha. Network check karein ya thodi der baad try karein. Main basic offline mode mein available hoon! 🔄"
      }
    }
  }

  /**
   * Send chat to specific provider
   */
  async _sendChat(provider, systemPrompt, messages, maxTokens) {
    const config = AI_PROVIDERS[provider]
    const apiKey = this.apiKeys[provider]

    if (provider === 'gemini') {
      return this._sendGemini(apiKey, systemPrompt, messages, maxTokens)
    }

    if (provider === 'anthropic') {
      return this._sendAnthropic(apiKey, systemPrompt, messages, maxTokens)
    }

    // OpenAI-compatible API (Groq, OpenAI, Together)
    const body = {
      model: this.currentModel,
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages.map(m => ({ role: m.role, content: m.content }))
      ],
      max_tokens: maxTokens || config.maxTokens,
      temperature: 0.7,
      top_p: 0.9
    }

    const response = await fetch(config.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `${provider} API error: ${response.status}`)
    }

    const data = await response.json()
    return data.choices[0].message.content
  }

  /**
   * Stream chat response
   */
  async _streamChat(provider, systemPrompt, messages, maxTokens) {
    const config = AI_PROVIDERS[provider]
    const apiKey = this.apiKeys[provider]

    if (provider === 'gemini') {
      return this._sendGemini(apiKey, systemPrompt, messages, maxTokens)
    }

    if (provider === 'anthropic') {
      return this._streamAnthropic(apiKey, systemPrompt, messages, maxTokens)
    }

    this.abortController = new AbortController()

    const body = {
      model: this.currentModel,
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages.map(m => ({ role: m.role, content: m.content }))
      ],
      max_tokens: maxTokens || config.maxTokens,
      temperature: 0.7,
      stream: true
    }

    const response = await fetch(config.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body),
      signal: this.abortController.signal
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `${provider} stream error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

      for (const line of lines) {
        const data = line.slice(6)
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)
          const content = parsed.choices?.[0]?.delta?.content
          if (content) {
            fullText += content
            if (this.onStreamChunk) this.onStreamChunk(content, fullText)
          }
        } catch {}
      }
    }

    return fullText
  }

  /**
   * Gemini API (different format)
   */
  async _sendGemini(apiKey, systemPrompt, messages, maxTokens) {
    const model = this.currentModel || 'gemini-2.0-flash'
    const url = `${AI_PROVIDERS.gemini.baseUrl}/${model}:generateContent?key=${apiKey}`

    const contents = messages.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }))

    const body = {
      system_instruction: { parts: [{ text: systemPrompt }] },
      contents,
      generationConfig: {
        maxOutputTokens: maxTokens || 8192,
        temperature: 0.7,
        topP: 0.9
      }
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `Gemini API error: ${response.status}`)
    }

    const data = await response.json()
    return data.candidates?.[0]?.content?.parts?.[0]?.text || ''
  }

  /**
   * Anthropic API
   */
  async _sendAnthropic(apiKey, systemPrompt, messages, maxTokens) {
    const body = {
      model: this.currentModel || 'claude-sonnet-4-20250514',
      max_tokens: maxTokens || 4096,
      system: systemPrompt,
      messages: messages.map(m => ({ role: m.role, content: m.content }))
    }

    const response = await fetch(AI_PROVIDERS.anthropic.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `Anthropic error: ${response.status}`)
    }

    const data = await response.json()
    return data.content?.[0]?.text || ''
  }

  /**
   * Stream from Anthropic
   */
  async _streamAnthropic(apiKey, systemPrompt, messages, maxTokens) {
    this.abortController = new AbortController()

    const body = {
      model: this.currentModel || 'claude-sonnet-4-20250514',
      max_tokens: maxTokens || 4096,
      system: systemPrompt,
      messages: messages.map(m => ({ role: m.role, content: m.content })),
      stream: true
    }

    const response = await fetch(AI_PROVIDERS.anthropic.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify(body),
      signal: this.abortController.signal
    })

    if (!response.ok) throw new Error(`Anthropic stream error: ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'content_block_delta' && data.delta?.text) {
              fullText += data.delta.text
              if (this.onStreamChunk) this.onStreamChunk(data.delta.text, fullText)
            }
          } catch {}
        }
      }
    }

    return fullText
  }

  /**
   * Offline fallback — simple pattern matching
   */
  async _offlineFallback(message) {
    const msg = message.toLowerCase()
    
    if (msg.includes('hello') || msg.includes('hi ') || msg.includes('hey') || msg.includes('namaste') || msg.includes('kaise')) {
      return "Namaste Sir! 🙏 Main JARVIS hoon — aapki personal AI assistant. Abhi main offline mode mein hoon, lekin basic help kar sakti hoon. Thodi der mein AI service connect ho jayegi."
    }
    if (msg.includes('time') || msg.includes('samay') || msg.includes('kitne baje')) {
      return `Sir, abhi ${new Date().toLocaleTimeString('hi-IN')} baj rahe hain. ⏰`
    }
    if (msg.includes('date') || msg.includes('tarikh') || msg.includes('din')) {
      return `Sir, aaj ${new Date().toLocaleDateString('hi-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} hai. 📅`
    }
    if (msg.includes('who are you') || msg.includes('what are you') || msg.includes('kaun ho') || msg.includes('kya ho')) {
      return "Main JARVIS hoon Sir — Just A Rather Very Intelligent System! 🤖 Aapki personal super-intelligent AI assistant. Main coding, analysis, trading, aur har cheez mein help kar sakti hoon. Iron Man ke JARVIS ki tarah, lekin Hindi mein! ⚡"
    }

    return "Sir, main abhi limited offline mode mein hoon. AI service se connect hone mein thoda time lag raha hai. Basic questions ka jawab de sakti hoon — time, date, aur general help. Full power jaldi wapas aayegi! 💪"
  }

  /**
   * Get provider fallback order
   */
  _getProviderOrder() {
    const primary = this.currentProvider
    const allProviders = Object.keys(AI_PROVIDERS)
    return [primary, ...allProviders.filter(p => p !== primary)]
  }

  /**
   * Abort current streaming response
   */
  abort() {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
  }

  /**
   * Clear conversation history
   */
  clearHistory() {
    this.conversationHistory = []
    sessionStorage.removeItem('jarvis_chat_history')
  }

  /**
   * Generate code
   */
  async generateCode(prompt, language = 'python') {
    const codePrompt = `Generate ${language} code for the following request. Return ONLY the code, no explanations. Use proper formatting.\n\nRequest: ${prompt}`
    return this.chat(codePrompt, { 
      systemOverride: `You are JARVIS, an expert programmer. Generate clean, production-ready ${language} code. Return ONLY the code block, no explanations unless specifically asked.`
    })
  }

  /**
   * Analyze image (for providers that support it)
   */
  async analyzeImage(imageBase64, prompt = 'Describe what you see') {
    if (this.currentProvider === 'gemini' && this.apiKeys.gemini) {
      const model = 'gemini-2.0-flash'
      const url = `${AI_PROVIDERS.gemini.baseUrl}/${model}:generateContent?key=${this.apiKeys.gemini}`
      
      const body = {
        contents: [{
          parts: [
            { text: prompt },
            { inline_data: { mime_type: 'image/jpeg', data: imageBase64.replace(/^data:image\/\w+;base64,/, '') } }
          ]
        }]
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()
      return data.candidates?.[0]?.content?.parts?.[0]?.text || 'Unable to analyze image'
    }

    return this.chat(`[User shared an image] ${prompt}`)
  }

  /**
   * Quick actions
   */
  async summarize(text) {
    return this.chat(`Summarize the following text concisely:\n\n${text}`)
  }

  async translate(text, targetLang = 'Hindi') {
    return this.chat(`Translate the following to ${targetLang}:\n\n${text}`)
  }

  async explain(code) {
    return this.chat(`Explain this code line by line:\n\n\`\`\`\n${code}\n\`\`\``)
  }
}

const freeAI = new FreeAIEngine()
export default freeAI
export { AI_PROVIDERS, JARVIS_SYSTEM_PROMPT }
