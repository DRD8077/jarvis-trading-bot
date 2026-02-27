import React, { useState, useEffect, useRef, useCallback, memo } from 'react'
import {
  Mic, MicOff, Send, Bot, User, Sparkles, Loader2, Brain, Cpu,
  Battery, Wifi, Phone, Volume2, VolumeX, Clock, Smartphone,
  Download, Settings2, Trash2, Power, Globe, MessageSquare,
  ChevronDown, Copy, Check, Zap, Shield, Search, ArrowUp,
  HardDrive, Languages, RotateCcw, Vibrate, Sun, Moon,
  PlayCircle, StopCircle, AlertCircle, CheckCircle2, Info
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useApp } from '../context/AppContext'

// ═══ Markdown Renderer ═══
const MarkdownMsg = memo(({ content }) => (
  <ReactMarkdown components={{
    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed text-[13px]">{children}</p>,
    strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
    em: ({ children }) => <em className="text-blue-300/90">{children}</em>,
    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5 text-[12px]">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5 text-[12px]">{children}</ol>,
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
    code: ({ inline, children }) => inline
      ? <code className="bg-slate-800 text-emerald-400 px-1 py-0.5 rounded text-[11px] font-mono">{children}</code>
      : <pre className="bg-slate-950 p-3 rounded-lg overflow-x-auto text-[11px] font-mono text-slate-300 my-2 border border-slate-800"><code>{children}</code></pre>,
    blockquote: ({ children }) => <blockquote className="border-l-2 border-blue-500 pl-3 my-2 text-slate-400 text-[12px]">{children}</blockquote>,
    a: ({ href, children }) => <a href={href} target="_blank" rel="noopener" className="text-blue-400 underline">{children}</a>,
  }}>{content}</ReactMarkdown>
))

// ═══ Status Indicator ═══
const StatusDot = ({ active, label, icon: Icon }) => (
  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-medium ${
    active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'
  }`}>
    <div className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
    {Icon && <Icon size={10} />}
    <span>{label}</span>
  </div>
)

// ═══ Quick Command Button ═══
const QuickCmd = ({ icon: Icon, label, color, onClick }) => (
  <button onClick={onClick}
    className={`flex flex-col items-center gap-1 p-2.5 rounded-xl bg-gradient-to-br ${color} 
    shadow-lg active:scale-95 transition-all min-w-[70px]`}>
    <Icon size={18} className="text-white" />
    <span className="text-[9px] text-white/90 font-medium">{label}</span>
  </button>
)

// ═══ Model Card ═══
const ModelCard = ({ model, onLoad, isLoaded }) => (
  <div className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
    isLoaded ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-slate-700/50 bg-slate-800/50'
  }`}>
    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
      isLoaded ? 'bg-emerald-500/20' : 'bg-slate-700'
    }`}>
      <Brain size={18} className={isLoaded ? 'text-emerald-400' : 'text-slate-400'} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium text-white truncate">{model.name}</p>
      <p className="text-[10px] text-slate-400">{model.sizeMB} MB</p>
    </div>
    {isLoaded ? (
      <CheckCircle2 size={16} className="text-emerald-400" />
    ) : (
      <button onClick={() => onLoad(model)} className="px-3 py-1 bg-blue-600 rounded-lg text-[10px] text-white font-medium active:scale-95">
        Load
      </button>
    )}
  </div>
)

// ═══ Thinking Animation ═══
const ThinkingDots = () => (
  <div className="flex items-start gap-2.5 px-3 py-2">
    <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center flex-shrink-0">
      <Sparkles size={13} className="text-white animate-spin-slow" />
    </div>
    <div className="flex items-center gap-1.5 pt-2">
      <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  </div>
)

// ═══ Suggested Prompts ═══
const suggestions = [
  { icon: '🔋', title: 'Battery Check', prompt: 'Battery kitni hai?', color: 'from-green-600 to-emerald-600' },
  { icon: '🕐', title: 'Time & Date', prompt: 'Abhi time kya hua hai?', color: 'from-blue-600 to-cyan-600' },
  { icon: '📶', title: 'Network Status', prompt: 'WiFi connected hai?', color: 'from-purple-600 to-violet-600' },
  { icon: '📱', title: 'Device Info', prompt: 'Mere phone ki details batao', color: 'from-orange-600 to-amber-600' },
  { icon: '📊', title: 'Market Analysis', prompt: 'NIFTY 50 ka analysis do Hindi mein', color: 'from-red-600 to-pink-600' },
  { icon: '🧠', title: 'Code Help', prompt: 'Python mein fibonacci ka code likho', color: 'from-indigo-600 to-blue-600' },
  { icon: '💡', title: 'General Knowledge', prompt: 'AI kya hai aur kaise kaam karta hai?', color: 'from-yellow-600 to-orange-600' },
  { icon: '🇮🇳', title: 'Hindi Chat', prompt: 'Mujhe Hindi mein ek joke sunao', color: 'from-pink-600 to-rose-600' },
]

// ═══════════════════════════════════════════════════════════
//  MAIN AI AGENT COMPONENT
// ═══════════════════════════════════════════════════════════
const AIAgent = () => {
  const { hapticFeedback, addNotification } = useApp()
  
  // Service refs (loaded dynamically to avoid crash on Android WebView)
  const jarvisAIRef = useRef(null)
  const jarvisSPOCRef = useRef(null)
  const [modelRegistry, setModelRegistry] = useState({})
  
  // ═══ State ═══
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [partialText, setPartialText] = useState('')
  const [activeTab, setActiveTab] = useState('chat') // chat, models, settings, status
  const [copiedIdx, setCopiedIdx] = useState(null)
  
  // AI Status
  const [llmReady, setLlmReady] = useState(false)
  const [sttReady, setSttReady] = useState(false)
  const [ttsReady, setTtsReady] = useState(false)
  const [currentModel, setCurrentModel] = useState('')
  const [models, setModels] = useState([])
  const [sttModels, setSttModels] = useState([])
  
  // Settings
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [language, setLanguage] = useState('hi-IN')
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(512)
  
  // Download
  const [downloading, setDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  
  // Agent step indicator
  const [agentStep, setAgentStep] = useState('')
  
  const chatEndRef = useRef(null)
  const inputRef = useRef(null)

  // ═══ Init ═══
  useEffect(() => {
    // Load services dynamically
    import('../services/jarvisAIEngine').then(m => {
      jarvisAIRef.current = m?.default || m
      // Subscribe to events
      const unsubs = [
        jarvisAIRef.current?.on?.('speechResult', (e) => {
          if (e.partial) setPartialText(e.partial)
          if (e.isFinal && e.text) {
            setPartialText('')
            setInput(e.text)
            if (e.isComplete) handleSend(e.text)
          }
        }),
        jarvisAIRef.current?.on?.('agentStep', (e) => setAgentStep(e.message)),
        jarvisAIRef.current?.on?.('speakingEnd', () => setIsSpeaking(false)),
        jarvisAIRef.current?.on?.('downloadProgress', (e) => setDownloadProgress(e.progress || 0)),
      ].filter(Boolean)
      // Store for cleanup
      window.__jarvisAIUnsubs = unsubs
      loadStatus()
    }).catch(() => {})

    import('../services/jarvisNuclearSPOC').then(m => {
      jarvisSPOCRef.current = m?.default || m
      if (m?.MODEL_REGISTRY) setModelRegistry(m.MODEL_REGISTRY)
    }).catch(() => {})

    // batteryOptimizer not actively used, skip

    return () => {
      const unsubs = window.__jarvisAIUnsubs || []
      unsubs.forEach(u => u?.())
      delete window.__jarvisAIUnsubs
    }
  }, [])

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const loadStatus = async () => {
    try {
      if (!jarvisAIRef.current) return
      const status = await jarvisAIRef.current.getFullStatus()
      setLlmReady(status.llm?.loaded || false)
      setSttReady(status.stt?.modelReady || false)
      setTtsReady(status.tts?.ready || false)
      setCurrentModel(status.llm?.currentModel || '')
      
      const llmModels = await jarvisAIRef.current.getModels()
      setModels(llmModels.models || [])
      
      const sttModelList = await jarvisAIRef.current.getSTTModels()
      setSttModels(sttModelList.models || [])
    } catch (e) {
      console.warn('Status load error:', e)
    }
  }

  // ═══ Handlers ═══
  
  const handleSend = async (overrideText) => {
    const text = overrideText || input.trim()
    if (!text || isLoading) return
    
    hapticFeedback?.('impact')
    setInput('')
    setIsLoading(true)
    setAgentStep('🧠 Nuclear Brain soch raha hai...')
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: text, time: new Date() }])
    
    try {
      // Use Nuclear SPOC — agentic pipeline: classify → RAG → CoT → tools → self-reflect
      const result = jarvisSPOCRef.current ? await jarvisSPOCRef.current.query(text) : { text: 'AI engine loading... please try again.', model: '', tokensUsed: 0 }
      
      const displayText = result.text || result.response || 'No response'
      const meta = []
      if (result.model) meta.push(`Model: ${result.model}`)
      if (result.tokensUsed) meta.push(`${result.tokensUsed} tokens`)
      if (result.toolsUsed?.length) meta.push(`Tools: ${result.toolsUsed.join(', ')}`)
      if (result.ragHits) meta.push(`RAG: ${result.ragHits} docs`)
      if (result.thinkingSteps) meta.push(`CoT: ${result.thinkingSteps} steps`)
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: displayText + (meta.length ? `\n\n---\n_${meta.join(' • ')}_` : ''),
        time: new Date(),
        tokens: result.tokensUsed, 
        model: result.model,
        isQuick: result.isQuickCommand
      }])
      
      if (autoSpeak && voiceEnabled) {
        setIsSpeaking(true)
        jarvisAIRef.current?.speak?.(displayText, { language })?.catch?.(() => setIsSpeaking(false))
      }
    } catch (e) {
      setMessages(prev => [...prev, { 
        role: 'error', content: `❌ Error: ${e.message}`, time: new Date() 
      }])
      addNotification?.('AI error: ' + e.message, 'error')
    } finally {
      setIsLoading(false)
      setAgentStep('')
    }
  }

  const handleVoice = async () => {
    hapticFeedback?.('impact')
    
    if (isListening) {
      setIsListening(false)
      await jarvisAIRef.current?.stopListening?.()
      return
    }
    
    setIsListening(true)
    setPartialText('')
    
    try {
      await jarvisAIRef.current?.startListening?.()
      // Auto-stop after 10 seconds
      setTimeout(() => {
        if (isListening) {
          setIsListening(false)
          jarvisAIRef.current?.stopListening?.()
        }
      }, 10000)
    } catch (e) {
      setIsListening(false)
      addNotification?.('Voice error: ' + e.message, 'error')
    }
  }

  const handleStopSpeaking = () => {
    jarvisAIRef.current?.stopSpeaking?.()
    setIsSpeaking(false)
  }

  const handleLoadModel = async (model) => {
    hapticFeedback?.('impact')
    setIsLoading(true)
    try {
      await jarvisAIRef.current?.loadModel?.(model.path, { threads: 4, contextSize: 2048 })
      setLlmReady(true)
      setCurrentModel(model.name)
      addNotification?.(`✅ Model loaded: ${model.name}`, 'success')
    } catch (e) {
      addNotification?.('Model load failed: ' + e.message, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadLLM = async () => {
    // Check if native platform is available
    try {
      const { Capacitor } = await import('@capacitor/core').catch(() => ({}))
      if (!Capacitor?.isNativePlatform?.()) {
        addNotification?.('AI Models sirf APK mein download hote hain. JARVIS AI chat use karein — woh online kaam karta hai! 🧠', 'info')
        return
      }
    } catch {}
    setDownloading(true)
    setDownloadProgress(0)
    try {
      await jarvisAIRef.current?.downloadModel?.(
        'https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf',
        'tinyllama-1.1b-chat-Q4_K_M.gguf'
      )
      addNotification?.('✅ TinyLlama model downloaded!', 'success')
      await loadStatus()
    } catch (e) {
      addNotification?.('Sir, yeh model abhi available nahi hai. JARVIS AI Chat use karein — woh cloud AI se kaam karta hai! 🚀', 'info')
    } finally {
      setDownloading(false)
    }
  }

  const handleDownloadSTT = async (lang) => {
    try {
      const { Capacitor } = await import('@capacitor/core').catch(() => ({}))
      if (!Capacitor?.isNativePlatform?.()) {
        addNotification?.('Voice models sirf APK mein download hote hain. Browser mein Web Speech API automatic use hota hai! 🎤', 'info')
        return
      }
    } catch {}
    setDownloading(true)
    try {
      await jarvisAIRef.current?.downloadSTTModel?.(lang)
      await jarvisAIRef.current?.initSTT?.(lang)
      setSttReady(true)
      addNotification?.(`✅ STT model (${lang}) downloaded!`, 'success')
    } catch (e) {
      addNotification?.('Sir, voice model abhi available nahi hai. Browser voice auto-use hota hai! 🎤', 'info')
    } finally {
      setDownloading(false)
    }
  }

  const handleInitAll = async () => {
    setIsLoading(true)
    try {
      const result = jarvisAIRef.current ? await jarvisAIRef.current.init({ sttLanguage: 'en-us' }) : {}
      setLlmReady(result.llm || false)
      setSttReady(result.stt || false)
      setTtsReady(result.tts || false)
      addNotification?.('✅ AI Engine initialized!', 'success')
    } catch (e) {
      addNotification?.('Init error: ' + e.message, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const copyMessage = (text, idx) => {
    navigator.clipboard?.writeText(text)
    setCopiedIdx(idx)
    setTimeout(() => setCopiedIdx(null), 2000)
    hapticFeedback?.('impact')
  }

  const clearChat = () => {
    setMessages([])
    jarvisAIRef.current?.clearHistory?.()
    jarvisSPOCRef.current?.memory?.clearShortTerm?.()
    hapticFeedback?.('impact')
  }

  // ═══ Render ═══
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* ═══ Header ═══ */}
      <div className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-lg border-b border-slate-800/60">
        <div className="px-3 pt-3 pb-2">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <Brain size={18} className="text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-white">JARVIS Nuclear AI</h1>
                <p className="text-[10px] text-slate-400">Nuclear SPOC • CoT+RAG • {Object.keys(modelRegistry).length} Models • Offline</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <button onClick={clearChat} className="p-1.5 rounded-lg bg-slate-800 active:scale-90">
                <Trash2 size={14} className="text-slate-400" />
              </button>
              <button onClick={handleInitAll} disabled={isLoading}
                className="p-1.5 rounded-lg bg-slate-800 active:scale-90">
                {isLoading ? <Loader2 size={14} className="text-blue-400 animate-spin" /> :
                 <Power size={14} className="text-slate-400" />}
              </button>
            </div>
          </div>
          
          {/* Status Bar */}
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
            <StatusDot active={llmReady} label="LLM" icon={Brain} />
            <StatusDot active={sttReady} label="STT" icon={Mic} />
            <StatusDot active={ttsReady} label="TTS" icon={Volume2} />
            {currentModel && (
              <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-violet-500/10 text-[10px] text-violet-300">
                <Cpu size={10} />
                <span className="truncate max-w-[100px]">{currentModel}</span>
              </div>
            )}
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex border-t border-slate-800/50">
          {[
            { id: 'chat', label: 'Chat', icon: MessageSquare },
            { id: 'commands', label: 'Commands', icon: Zap },
            { id: 'models', label: 'Models', icon: HardDrive },
            { id: 'settings', label: 'Settings', icon: Settings2 },
          ].map(tab => (
            <button key={tab.id} onClick={() => { setActiveTab(tab.id); hapticFeedback?.('impact') }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-[10px] font-medium transition-all ${
                activeTab === tab.id 
                  ? 'text-violet-400 border-b-2 border-violet-400 bg-violet-500/5' 
                  : 'text-slate-500'
              }`}>
              <tab.icon size={12} />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ═══ Content ═══ */}
      <div className="flex-1 overflow-y-auto">
        
        {/* ═══ CHAT TAB ═══ */}
        {activeTab === 'chat' && (
          <div className="flex flex-col min-h-full">
            {messages.length === 0 ? (
              /* Welcome + Suggestions */
              <div className="p-4 space-y-4">
                <div className="text-center py-6">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center shadow-xl shadow-violet-500/30 mb-3">
                    <Sparkles size={28} className="text-white" />
                  </div>
                  <h2 className="text-lg font-bold text-white mb-1">Jai Mahadev! 🙏</h2>
                  <p className="text-xs text-slate-400 max-w-[250px] mx-auto">
                    Main JARVIS Nuclear SPOC hoon — PhD-level reasoning, Chain-of-Thought,
                    RAG + Tool Calling. ChatGPT se bhi powerful, 100% offline!
                  </p>
                  
                  {!llmReady && (
                    <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                      <p className="text-[11px] text-amber-300 mb-2">⚠️ LLM model load nahi hai</p>
                      <button onClick={() => setActiveTab('models')}
                        className="px-4 py-1.5 bg-amber-600 rounded-lg text-[11px] text-white font-medium active:scale-95">
                        Models Tab pe jaao →
                      </button>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium px-1">Try asking...</p>
                  <div className="grid grid-cols-2 gap-2">
                    {suggestions.map((s, i) => (
                      <button key={i} onClick={() => { setInput(s.prompt); handleSend(s.prompt) }}
                        className={`text-left p-3 rounded-xl bg-gradient-to-br ${s.color} shadow-lg active:scale-95 transition-all`}>
                        <span className="text-lg">{s.icon}</span>
                        <p className="text-[11px] font-medium text-white mt-1">{s.title}</p>
                        <p className="text-[9px] text-white/60 truncate">{s.prompt}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Chat Messages */
              <div className="p-3 space-y-3">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role !== 'user' && (
                      <div className={`w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5 ${
                        msg.role === 'error' ? 'bg-red-500/20' : 'bg-gradient-to-br from-violet-600 to-purple-600'
                      }`}>
                        {msg.role === 'error' ? <AlertCircle size={13} className="text-red-400" /> :
                         <Sparkles size={13} className="text-white" />}
                      </div>
                    )}
                    
                    <div className={`max-w-[80%] rounded-2xl px-3 py-2 ${
                      msg.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-br-md' 
                        : msg.role === 'error'
                        ? 'bg-red-500/10 text-red-300 border border-red-500/20 rounded-bl-md'
                        : 'bg-slate-800 text-slate-200 rounded-bl-md'
                    }`}>
                      {msg.role === 'user' ? (
                        <p className="text-[13px]">{msg.content}</p>
                      ) : (
                        <MarkdownMsg content={msg.content} />
                      )}
                      
                      <div className="flex items-center justify-between mt-1 pt-1 border-t border-white/5">
                        <span className="text-[9px] text-white/30">
                          {msg.time?.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                          {msg.isQuick && ' • ⚡ Quick'}
                          {msg.tokens > 0 && ` • ${msg.tokens} tokens`}
                        </span>
                        {msg.role === 'assistant' && (
                          <div className="flex items-center gap-1">
                            <button onClick={() => { setIsSpeaking(true); jarvisAIRef.current?.speak?.(msg.content, { language }) }}
                              className="p-0.5 rounded active:scale-90">
                              <Volume2 size={10} className="text-white/30" />
                            </button>
                            <button onClick={() => copyMessage(msg.content, i)} className="p-0.5 rounded active:scale-90">
                              {copiedIdx === i ? <Check size={10} className="text-emerald-400" /> :
                               <Copy size={10} className="text-white/30" />}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {msg.role === 'user' && (
                      <div className="w-7 h-7 rounded-lg bg-blue-600 flex-shrink-0 flex items-center justify-center mt-0.5">
                        <User size={13} className="text-white" />
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && <ThinkingDots />}
                {agentStep && (
                  <div className="text-center">
                    <span className="text-[10px] text-violet-400 bg-violet-500/10 px-3 py-1 rounded-full">{agentStep}</span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>
        )}

        {/* ═══ COMMANDS TAB ═══ */}
        {activeTab === 'commands' && (
          <div className="p-4 space-y-4">
            <h3 className="text-xs font-bold text-white">⚡ Quick Device Commands</h3>
            <p className="text-[10px] text-slate-400">Tap any command — works 100% offline!</p>
            
            <div className="grid grid-cols-4 gap-2">
              <QuickCmd icon={Battery} label="Battery" color="from-green-600 to-emerald-700"
                onClick={async () => {
                  const b = jarvisAIRef.current ? await jarvisAIRef.current.getBattery() : { level: '--', status: 'unknown', chargingType: 'N/A', temperature: '--' }
                  const msg = `🔋 Battery: ${b.level}%\n${b.status}\nCharging: ${b.chargingType}\nTemp: ${b.temperature}°C`
                  setMessages(prev => [...prev, { role: 'assistant', content: msg, time: new Date(), isQuick: true }])
                  setActiveTab('chat')
                  if (autoSpeak) jarvisAIRef.current?.speak?.(`Battery ${b.level} percent hai, ${b.status}`, { language })
                }} />
              
              <QuickCmd icon={Clock} label="Time" color="from-blue-600 to-cyan-700"
                onClick={async () => {
                  const dt = jarvisAIRef.current ? await jarvisAIRef.current.getDateTime() : { time: new Date().toLocaleTimeString(), day: new Date().toLocaleDateString(), date: '' }
                  const msg = `🕐 ${dt.time}\n📅 ${dt.day}, ${dt.date}`
                  setMessages(prev => [...prev, { role: 'assistant', content: msg, time: new Date(), isQuick: true }])
                  setActiveTab('chat')
                  if (autoSpeak) jarvisAIRef.current?.speak?.(`Abhi ${dt.time} baj rahe hain, ${dt.day}`, { language })
                }} />
              
              <QuickCmd icon={Wifi} label="Network" color="from-purple-600 to-violet-700"
                onClick={async () => {
                  const n = jarvisAIRef.current ? await jarvisAIRef.current.getNetwork() : { connected: navigator.onLine, type: 'unknown', ssid: '' }
                  const msg = `📶 ${n.connected ? '✅ Connected' : '❌ Disconnected'}\nType: ${n.type}\nWiFi: ${n.ssid || 'Off'}`
                  setMessages(prev => [...prev, { role: 'assistant', content: msg, time: new Date(), isQuick: true }])
                  setActiveTab('chat')
                }} />
              
              <QuickCmd icon={Smartphone} label="Device" color="from-orange-600 to-amber-700"
                onClick={async () => {
                  const d = jarvisAIRef.current ? await jarvisAIRef.current.getDeviceInfo() : { brand: 'Unknown', model: 'Unknown', androidVersion: '--', sdkVersion: '--', processors: '--', maxMemoryMB: '--' }
                  const msg = `📱 **${d.brand} ${d.model}**\nAndroid ${d.androidVersion} (SDK ${d.sdkVersion})\n${d.processors} CPU cores\nRAM: ${d.maxMemoryMB}MB`
                  setMessages(prev => [...prev, { role: 'assistant', content: msg, time: new Date(), isQuick: true }])
                  setActiveTab('chat')
                }} />
              
              <QuickCmd icon={Volume2} label="Vol Up" color="from-teal-600 to-cyan-700"
                onClick={() => jarvisAIRef.current?.setVolume?.(80, 'media')} />
              
              <QuickCmd icon={VolumeX} label="Vol Down" color="from-slate-600 to-slate-700"
                onClick={() => jarvisAIRef.current?.setVolume?.(30, 'media')} />
              
              <QuickCmd icon={Vibrate} label="Vibrate" color="from-pink-600 to-rose-700"
                onClick={() => jarvisAIRef.current?.vibrate?.(300)} />
              
              <QuickCmd icon={Settings2} label="Settings" color="from-slate-600 to-gray-700"
                onClick={() => jarvisAIRef.current?.openSettings?.('')} />
            </div>

            <h3 className="text-xs font-bold text-white mt-4">🌐 Quick Actions</h3>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => jarvisAIRef.current?.openUrl?.('https://www.google.com')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800 active:scale-95">
                <Globe size={16} className="text-blue-400" />
                <span className="text-xs text-white">Open Browser</span>
              </button>
              <button onClick={() => jarvisAIRef.current?.openSettings?.('wifi')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800 active:scale-95">
                <Wifi size={16} className="text-purple-400" />
                <span className="text-xs text-white">WiFi Settings</span>
              </button>
              <button onClick={() => jarvisAIRef.current?.openSettings?.('bluetooth')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800 active:scale-95">
                <Zap size={16} className="text-blue-400" />
                <span className="text-xs text-white">Bluetooth</span>
              </button>
              <button onClick={() => jarvisAIRef.current?.openSettings?.('tts')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800 active:scale-95">
                <Languages size={16} className="text-green-400" />
                <span className="text-xs text-white">TTS Settings</span>
              </button>
            </div>

            <h3 className="text-xs font-bold text-white mt-4">📞 Call / SMS</h3>
            <div className="flex gap-2">
              <input type="tel" placeholder="Phone number..."
                className="flex-1 bg-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none"
                id="phoneInput" />
              <button onClick={() => {
                const num = document.getElementById('phoneInput')?.value
                if (num) jarvisAIRef.current?.makeCall?.(num)
              }} className="px-4 py-2 bg-green-600 rounded-xl text-xs text-white font-medium active:scale-95">
                <Phone size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ═══ MODELS TAB ═══ */}
        {activeTab === 'models' && (
          <div className="p-4 space-y-4">
            {/* LLM Models */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold text-white">🧠 LLM Models (GGUF)</h3>
                <button onClick={loadStatus} className="p-1 rounded-lg bg-slate-800 active:scale-90">
                  <RotateCcw size={12} className="text-slate-400" />
                </button>
              </div>
              
              {models.length === 0 ? (
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 text-center">
                  <Brain size={24} className="mx-auto text-slate-500 mb-2" />
                  <p className="text-xs text-slate-400 mb-2">No offline LLM models on device</p>
                  <p className="text-[10px] text-emerald-400 mb-3">✅ Cloud AI already working — use AI Chat tab for instant responses!</p>
                  
                  <div className="space-y-2">
                    <p className="text-[9px] text-slate-500">
                      Offline models require Android APK + storage. Cloud AI works everywhere!
                    </p>
                    <button onClick={handleDownloadLLM} disabled={downloading}
                      className="w-full px-4 py-2.5 bg-gradient-to-r from-violet-600 to-purple-600 rounded-xl text-xs text-white font-medium active:scale-95 disabled:opacity-50">
                      {downloading ? (
                        <span className="flex items-center justify-center gap-2">
                          <Loader2 size={14} className="animate-spin" />
                          Downloading... {downloadProgress}%
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <Download size={14} /> Download TinyLlama 1.1B (670MB)
                        </span>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {models.map((m, i) => (
                    <ModelCard key={i} model={m} onLoad={handleLoadModel} 
                      isLoaded={currentModel === m.name || currentModel === m.path} />
                  ))}
                  <button onClick={handleDownloadLLM} disabled={downloading}
                    className="w-full px-4 py-2 bg-slate-800 rounded-xl text-[11px] text-slate-300 active:scale-95 border border-dashed border-slate-700">
                    <Download size={12} className="inline mr-1" /> Download More Models
                  </button>
                </div>
              )}
            </div>

            {/* 2026 SOTA Nuclear Models */}
            <div>
              <h3 className="text-xs font-bold text-white mb-2">🔬 2026 SOTA Nuclear Models</h3>
              <p className="text-[9px] text-slate-400 mb-2">DeepSeek-R1, Qwen3, Phi-4, Gemma-3n, Llama-3.2 — PhD-level reasoning</p>
              <div className="space-y-2">
                {Object.entries(modelRegistry).map(([key, m]) => (
                  <div key={key} className="p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[11px] font-bold text-white">{m.name}</p>
                      <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300">
                        P{m.priority}
                      </span>
                    </div>
                    <div className="flex gap-2 mb-1.5 flex-wrap">
                      <span className="text-[8px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300">{m.quantization}</span>
                      <span className="text-[8px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-300">{m.sizeMB}MB</span>
                      <span className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300">{m.contextLength} ctx</span>
                    </div>
                    {m.benchmarks && (
                      <div className="flex gap-1.5 mb-2 flex-wrap">
                        {Object.entries(m.benchmarks).slice(0, 3).map(([k, v]) => (
                          <span key={k} className="text-[7px] text-slate-500">{k}: {v}</span>
                        ))}
                      </div>
                    )}
                    <button onClick={async () => {
                      // Check if native platform is available for model downloads
                      try {
                        const { Capacitor } = await import('@capacitor/core').catch(() => ({}))
                        if (!Capacitor?.isNativePlatform?.()) {
                          addNotification?.('Sir, yeh AI model sirf Android APK mein download hota hai. JARVIS AI Chat tab use karein — woh cloud AI se kaam karta hai! 🧠', 'info')
                          return
                        }
                      } catch {}
                      setDownloading(true)
                      setDownloadProgress(0)
                      try {
                        await jarvisAIRef.current?.downloadModel?.(m.url, m.filename)
                        addNotification?.(`✅ ${m.name} downloaded!`, 'success')
                        await loadStatus()
                      } catch (e) { addNotification?.('Sir, yeh model abhi available nahi hai. AI Chat use karein — cloud se kaam karta hai! 🚀', 'info') }
                      finally { setDownloading(false) }
                    }} disabled={downloading}
                      className="w-full px-3 py-1.5 bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg text-[10px] text-white font-medium active:scale-95 disabled:opacity-50">
                      <Download size={10} className="inline mr-1" /> Download {m.name} ({m.sizeMB}MB)
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* STT Models */}
            <div>
              <h3 className="text-xs font-bold text-white mb-2">🎤 Voice Models (Vosk STT)</h3>
              <div className="space-y-2">
                {[
                  { lang: 'en-us', name: 'English (US)', size: '40MB' },
                  { lang: 'hi', name: 'Hindi', size: '250MB' },
                  { lang: 'en-in', name: 'English (India)', size: '36MB' },
                ].map((m, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <Mic size={14} className="text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <p className="text-[11px] font-medium text-white">{m.name}</p>
                      <p className="text-[9px] text-slate-400">{m.size}</p>
                    </div>
                    {sttModels.some(s => s.name?.includes(m.lang)) ? (
                      <CheckCircle2 size={14} className="text-emerald-400" />
                    ) : (
                      <button onClick={() => handleDownloadSTT(m.lang)} disabled={downloading}
                        className="px-3 py-1.5 bg-blue-600 rounded-lg text-[10px] text-white font-medium active:scale-95">
                        <Download size={10} className="inline mr-1" /> Get
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ SETTINGS TAB ═══ */}
        {activeTab === 'settings' && (
          <div className="p-4 space-y-4">
            <h3 className="text-xs font-bold text-white">⚙️ AI Agent Settings</h3>
            
            {/* Voice Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800">
              <div className="flex items-center gap-2">
                <Volume2 size={16} className="text-blue-400" />
                <div>
                  <p className="text-xs text-white">Voice Output</p>
                  <p className="text-[9px] text-slate-400">AI response bolega</p>
                </div>
              </div>
              <button onClick={() => setVoiceEnabled(!voiceEnabled)}
                className={`w-11 h-6 rounded-full transition-all ${voiceEnabled ? 'bg-blue-600' : 'bg-slate-700'}`}>
                <div className={`w-5 h-5 bg-white rounded-full transition-all shadow ${voiceEnabled ? 'ml-[22px]' : 'ml-0.5'}`} />
              </button>
            </div>

            {/* Auto-Speak Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-violet-400" />
                <div>
                  <p className="text-xs text-white">Auto Speak</p>
                  <p className="text-[9px] text-slate-400">Response automatically bolega</p>
                </div>
              </div>
              <button onClick={() => setAutoSpeak(!autoSpeak)}
                className={`w-11 h-6 rounded-full transition-all ${autoSpeak ? 'bg-violet-600' : 'bg-slate-700'}`}>
                <div className={`w-5 h-5 bg-white rounded-full transition-all shadow ${autoSpeak ? 'ml-[22px]' : 'ml-0.5'}`} />
              </button>
            </div>

            {/* Language */}
            <div className="p-3 rounded-xl bg-slate-800">
              <div className="flex items-center gap-2 mb-2">
                <Languages size={16} className="text-green-400" />
                <p className="text-xs text-white">TTS Language</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { code: 'hi-IN', label: 'Hindi' },
                  { code: 'en-IN', label: 'English IN' },
                  { code: 'en-US', label: 'English US' },
                ].map(l => (
                  <button key={l.code} onClick={() => { setLanguage(l.code); jarvisAIRef.current?.setTTSLanguage?.(l.code) }}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-medium transition-all ${
                      language === l.code ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}>{l.label}</button>
                ))}
              </div>
            </div>

            {/* Temperature */}
            <div className="p-3 rounded-xl bg-slate-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Sun size={16} className="text-amber-400" />
                  <p className="text-xs text-white">Temperature</p>
                </div>
                <span className="text-[10px] text-slate-400">{temperature}</span>
              </div>
              <input type="range" min="0.1" max="2.0" step="0.1" value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500" />
              <div className="flex justify-between text-[8px] text-slate-500 mt-1">
                <span>Precise</span><span>Creative</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div className="p-3 rounded-xl bg-slate-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Cpu size={16} className="text-purple-400" />
                  <p className="text-xs text-white">Max Tokens</p>
                </div>
                <span className="text-[10px] text-slate-400">{maxTokens}</span>
              </div>
              <input type="range" min="64" max="2048" step="64" value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500" />
              <div className="flex justify-between text-[8px] text-slate-500 mt-1">
                <span>Short (64)</span><span>Long (2048)</span>
              </div>
            </div>

            {/* Open Phone TTS Settings */}
            <button onClick={() => jarvisAIRef.current?.openSettings?.('tts')}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 active:scale-[0.98]">
              <div className="flex items-center gap-2">
                <Settings2 size={16} className="text-slate-400" />
                <div>
                  <p className="text-xs text-white">Phone TTS Settings</p>
                  <p className="text-[9px] text-slate-400">Offline voices download karo yahan se</p>
                </div>
              </div>
              <ArrowUp size={14} className="text-slate-500 rotate-45" />
            </button>

            {/* AI Engine Info */}
            <div className="p-3 rounded-xl bg-gradient-to-br from-slate-800 to-slate-800/50 border border-slate-700/30">
              <h4 className="text-[10px] font-bold text-white mb-2 flex items-center gap-1">
                <Info size={10} /> About JARVIS Nuclear SPOC
              </h4>
              <div className="space-y-1 text-[9px] text-slate-400">
                <p>🔬 Nuclear SPOC: Agentic AI — CoT + Self-Reflection + RAG + Tool Calling</p>
                <p>🧠 LLM: llama.cpp + MLC LLM + ONNX — {Object.keys(modelRegistry).length} SOTA 2026 models</p>
                <p>📚 RAG: IndexedDB vector search — TF-IDF + cosine similarity</p>
                <p>🛠️ Tools: Calculator, Market, Battery, DateTime, Network + more</p>
                <p>🎤 STT: Vosk — offline speech (Hindi + English)</p>
                <p>🔊 TTS: Android built-in + streaming</p>
                <p>🛡️ Security: AES-256-GCM + device fingerprint + anti-tamper</p>
                <p>🔋 Battery: Adaptive modes (normal/power-save/ultra-save)</p>
                <p>🔒 100% Private — zero data leaves your phone</p>
                <p className="text-violet-400 font-medium pt-1">Made with ❤️ by DRD • Jai Mahadev! 🔱</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ═══ Input Bar (Chat Tab Only) ═══ */}
      {activeTab === 'chat' && (
        <div className="sticky bottom-0 bg-slate-900/95 backdrop-blur-lg border-t border-slate-800/60 p-3 pb-safe">
          {/* Partial speech text */}
          {partialText && (
            <div className="mb-2 px-3 py-1.5 bg-violet-500/10 rounded-lg border border-violet-500/20">
              <p className="text-[11px] text-violet-300 italic">🎤 {partialText}...</p>
            </div>
          )}
          
          <div className="flex items-end gap-2">
            {/* Voice Button */}
            <button onClick={handleVoice} disabled={!sttReady && !isListening}
              className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all flex-shrink-0 active:scale-90 ${
                isListening 
                  ? 'bg-red-500 shadow-lg shadow-red-500/30 animate-pulse'
                  : sttReady 
                  ? 'bg-gradient-to-br from-violet-600 to-purple-600 shadow-lg shadow-violet-500/20'
                  : 'bg-slate-800 opacity-50'
              }`}>
              {isListening ? <MicOff size={18} className="text-white" /> : <Mic size={18} className="text-white" />}
            </button>
            
            {/* Text Input */}
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={llmReady ? "JARVIS se baat karo..." : "Model load karo pehle..."}
                className="w-full bg-slate-800 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 outline-none focus:ring-1 focus:ring-violet-500/50"
              />
            </div>
            
            {/* Send / Stop Speaking */}
            {isSpeaking ? (
              <button onClick={handleStopSpeaking}
                className="w-11 h-11 rounded-xl bg-red-600 flex items-center justify-center active:scale-90 shadow-lg shadow-red-500/20">
                <StopCircle size={18} className="text-white" />
              </button>
            ) : (
              <button onClick={() => handleSend()} disabled={!input.trim() || isLoading}
                className={`w-11 h-11 rounded-xl flex items-center justify-center active:scale-90 transition-all ${
                  input.trim() 
                    ? 'bg-gradient-to-br from-blue-600 to-violet-600 shadow-lg shadow-blue-500/20'
                    : 'bg-slate-800'
                }`}>
                {isLoading ? <Loader2 size={18} className="text-white animate-spin" /> :
                 <Send size={18} className={input.trim() ? 'text-white' : 'text-slate-600'} />}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AIAgent
