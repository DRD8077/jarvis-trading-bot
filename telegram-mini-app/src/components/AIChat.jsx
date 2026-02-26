import React, { useState, useRef, useEffect, useCallback, memo } from 'react'
import {
  Send, Bot, User, Sparkles, Loader2, Trash2, ChevronDown, Copy, Check,
  Search, TrendingUp, Shield, Zap, Brain, Globe, Plus, Settings2,
  ChevronRight, MessageSquare, Cpu, ArrowUp, StopCircle, RotateCcw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { sendChat, clearChat as clearChatApi, fetchChatHistory, fetchChatModels, streamChat } from '../services/api'
import { useApp } from '../context/AppContext'

// ═══ Markdown Renderer (GPT-like) ═══
const MarkdownMessage = memo(({ content }) => (
  <ReactMarkdown
    components={{
      p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed text-[13.5px]">{children}</p>,
      strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
      em: ({ children }) => <em className="text-blue-300/90">{children}</em>,
      ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1 text-[13px]">{children}</ul>,
      ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1 text-[13px]">{children}</ol>,
      li: ({ children }) => <li className="leading-relaxed">{children}</li>,
      h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2 mt-3 border-b border-slate-700/50 pb-1">{children}</h1>,
      h2: ({ children }) => <h2 className="text-base font-bold text-white mb-2 mt-2.5">{children}</h2>,
      h3: ({ children }) => <h3 className="text-sm font-bold text-white/90 mb-1.5 mt-2">{children}</h3>,
      code: ({ inline, className, children }) => {
        if (inline) return <code className="bg-slate-800 text-emerald-400 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
        const lang = (className || '').replace('language-', '')
        return (
          <div className="my-3 rounded-xl overflow-hidden border border-slate-700/50 bg-slate-950">
            <div className="flex items-center justify-between bg-slate-800/80 px-4 py-2 border-b border-slate-700/40">
              <span className="text-[10px] text-slate-400 font-mono uppercase">{lang || 'code'}</span>
              <button onClick={() => navigator.clipboard?.writeText(String(children))} className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1 transition-colors">
                <Copy size={10} /> Copy
              </button>
            </div>
            <pre className="p-4 overflow-x-auto text-xs font-mono text-slate-300 leading-relaxed"><code>{children}</code></pre>
          </div>
        )
      },
      blockquote: ({ children }) => <blockquote className="border-l-3 border-blue-500 pl-4 my-3 text-slate-300 bg-blue-500/5 py-2 rounded-r-lg">{children}</blockquote>,
      a: ({ href, children }) => <a href={href} target="_blank" rel="noopener" className="text-blue-400 underline decoration-blue-400/30 hover:decoration-blue-400 transition-all">{children}</a>,
      hr: () => <hr className="border-slate-700/50 my-4" />,
      table: ({ children }) => <div className="overflow-x-auto my-3 rounded-lg border border-slate-700/50"><table className="min-w-full text-xs">{children}</table></div>,
      thead: ({ children }) => <thead className="bg-slate-800/60">{children}</thead>,
      th: ({ children }) => <th className="px-3 py-2 text-left text-blue-300 font-semibold text-xs border-b border-slate-700">{children}</th>,
      td: ({ children }) => <td className="px-3 py-2 border-b border-slate-800/50 text-[12px]">{children}</td>,
    }}
  >{content}</ReactMarkdown>
))

// ═══ Thinking animation ═══
const ThinkingDots = () => (
  <div className="flex items-start gap-3 px-4 py-3">
    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
      <Sparkles size={13} className="text-white" />
    </div>
    <div className="flex items-center gap-1.5 pt-2">
      <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse" />
      <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
      <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
    </div>
  </div>
)

// ═══ Suggested prompts (like ChatGPT) ═══
const suggestions = [
  { icon: '📊', title: 'Market Overview', sub: 'NIFTY, BTC, global view', prompt: 'Give me a complete market overview — NIFTY 50, Bank NIFTY, Bitcoin, Ethereum, Fear & Greed index, and overall sentiment analysis' },
  { icon: '🔍', title: 'Gem Tokens', sub: '10x potential crypto gems', prompt: 'Find me top 5 hidden gem crypto tokens with 10x potential. Include market cap, liquidity, risk score, and why each is promising' },
  { icon: '📈', title: 'Trading Signals', sub: 'BUY/SELL with entry & SL', prompt: 'Give me your top 5 real-time BUY/SELL trading signals for both crypto and Indian stocks. Include entry price, stop-loss, target, and confidence level' },
  { icon: '🧠', title: 'AI Prediction', sub: '7-day price forecast', prompt: 'Predict NIFTY 50, Bitcoin, and Ethereum prices for the next 7 days. Include confidence levels, key support/resistance levels, and scenarios' },
  { icon: '💻', title: 'Code Banao', sub: 'code generate & run karo', prompt: 'Python mein ek crypto price tracker banao jo har 10 second mein BTC aur ETH ka price dikhaye with color coding' },
  { icon: '🚀', title: 'GitHub Clone', sub: 'repo install & run karo', prompt: 'Clone https://github.com/ccxt/ccxt and show me how to use it to get live crypto prices from Binance' },
  { icon: '🇮🇳', title: 'Hindi Baat Karo', sub: 'Hindi/Hinglish mein baat', prompt: 'NIFTY 50 ka aaj ka analysis do Hindi mein — kahan support hai, kahan resistance, aur kal kya prediction hai?' },
  { icon: '🪂', title: 'Airdrop Scan', sub: 'free crypto dhundho', prompt: 'Mere wallet mein koi naye airdrops aaye hain? Saare free tokens scan karo aur batao kaunse claim karne chahiye' },
]

// ═══ Model Selector ═══
const ModelSelector = ({ models, selected, onSelect, show, onToggle }) => {
  if (!show) return null
  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-slate-800 border border-slate-700/60 rounded-xl shadow-2xl shadow-black/40 z-50 overflow-hidden animate-fade-up">
      <div className="px-3 py-2 border-b border-slate-700/50">
        <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">Select AI Model</span>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {models.map(m => (
          <button key={m.id} onClick={() => { onSelect(m.id); onToggle(false) }}
            disabled={!m.available}
            className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-all ${
              m.id === selected ? 'bg-blue-600/20 text-blue-300' : m.available ? 'hover:bg-slate-700/50 text-slate-300' : 'opacity-30 cursor-not-allowed'
            }`}>
            <Cpu size={14} className={m.id === selected ? 'text-blue-400' : 'text-slate-500'} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{m.name}</p>
              <p className="text-[10px] text-slate-500 truncate">{m.desc}</p>
            </div>
            {m.id === selected && <Check size={14} className="text-blue-400" />}
          </button>
        ))}
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═══════════════════════════════════════════════════════════
const AIChat = () => {
  const { user, hapticFeedback } = useApp()
  const userId = String(user?.id || '0')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [streamText, setStreamText] = useState('')
  const [showScrollBtn, setShowScrollBtn] = useState(false)
  const [copiedIdx, setCopiedIdx] = useState(null)
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('jarvis-auto')
  const [showModelPicker, setShowModelPicker] = useState(false)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(false)

  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
  }, [])

  useEffect(() => { scrollToBottom(false) }, [messages, streamText])

  useEffect(() => {
    const el = chatContainerRef.current
    if (!el) return
    const onScroll = () => setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 200)
    el.addEventListener('scroll', onScroll)
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  // Load models + history on mount
  useEffect(() => {
    fetchChatModels().then(r => {
      const m = r.data?.models || []
      if (m.length) setModels(m)
    }).catch(() => {})

    fetchChatHistory(userId).then(r => {
      const hist = r.data?.data?.messages || r.data?.messages || []
      if (hist.length > 0) setMessages(hist)
    }).catch(() => {})
  }, [])

  const modelLabel = models.find(m => m.id === selectedModel)?.name || 'JARVIS Auto'

  // ═══ Send with Streaming ═══
  const handleSend = async (text = null) => {
    const msg = text || input.trim()
    if (!msg || loading || streaming) return

    hapticFeedback?.('impact')
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setStreaming(true)
    setStreamText('')
    abortRef.current = false

    // Resize textarea back
    if (inputRef.current) inputRef.current.style.height = 'auto'

    let fullReply = ''
    try {
      await streamChat(
        msg, userId, selectedModel,
        (chunk) => {
          if (abortRef.current) return
          fullReply += chunk
          setStreamText(fullReply)
        },
        () => {
          // Done
          if (fullReply) {
            setMessages(prev => [...prev, { role: 'assistant', content: fullReply, model: selectedModel }])
          }
          setStreamText('')
          setStreaming(false)
          hapticFeedback?.('success')
        },
        (error) => {
          // Error — fallback to non-streaming
          console.warn('Stream error, falling back:', error)
          setStreamText('')
          setStreaming(false)
          fallbackChat(msg)
        }
      )
    } catch (e) {
      setStreamText('')
      setStreaming(false)
      fallbackChat(msg)
    }
  }

  const fallbackChat = async (msg) => {
    setLoading(true)
    try {
      const res = await sendChat(msg, `User: ${user?.first_name}, ID: ${userId}`, userId)
      const reply = res.data?.data?.reply || res.data?.reply || res.data?.response || 'Error processing request.'
      setMessages(prev => [...prev, { role: 'assistant', content: reply, model: selectedModel }])
      hapticFeedback?.('success')
    } catch (e) {
      // Backend failed — use freeAI (client-side AI with embedded keys)
      try {
        const { default: freeAI } = await import('../services/freeAI')
        if (!freeAI._initialized) freeAI.init()
        const result = await freeAI.chat(msg, { streaming: false })
        const reply = result?.text || result?.response || result || 'JARVIS is thinking...'
        setMessages(prev => [...prev, { role: 'assistant', content: typeof reply === 'string' ? reply : JSON.stringify(reply), model: 'freeAI' }])
        hapticFeedback?.('success')
      } catch (e2) {
        setMessages(prev => [...prev, { role: 'assistant', content: `**Error:** ${e.message}. Offline AI also failed: ${e2.message}` }])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleStop = () => { abortRef.current = true; setStreaming(false); setStreamText('') }

  const handleNewChat = async () => {
    hapticFeedback?.('impact')
    try { await clearChatApi(userId) } catch {}
    setMessages([])
    setStreamText('')
  }

  const handleRegenerate = () => {
    const lastUser = [...messages].reverse().find(m => m.role === 'user')
    if (lastUser) {
      setMessages(prev => prev.slice(0, -1)) // Remove last assistant msg
      handleSend(lastUser.content)
    }
  }

  const copyMessage = (text, idx) => {
    navigator.clipboard?.writeText(text)
    setCopiedIdx(idx)
    hapticFeedback?.('light')
    setTimeout(() => setCopiedIdx(null), 2000)
  }

  const isNewChat = messages.length === 0 && !streamText

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0f] text-white">
      {/* ═══ TOP BAR ═══ */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-[#0a0a0f]/95 backdrop-blur-xl sticky top-0 z-10">
        <button onClick={handleNewChat} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-white/5 transition-all active:scale-95" title="New chat">
          <Plus size={16} className="text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">New</span>
        </button>
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-md bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={10} />
          </div>
          <span className="text-sm font-semibold tracking-tight">JARVIS</span>
        </div>
        <div className="w-16" /> {/* spacer for balance */}
      </div>

      {/* ═══ MESSAGES AREA ═══ */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto scrollbar-hide">
        
        {/* ═══ EMPTY STATE (like ChatGPT) ═══ */}
        {isNewChat && (
          <div className="flex flex-col items-center justify-center min-h-[70vh] px-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/20">
              <Bot size={28} className="text-white" />
            </div>
            <h2 className="text-xl font-bold mb-1">JARVIS AI</h2>
            <p className="text-slate-500 text-xs mb-8">Tumhara personal AI trading intelligence — Hindi/English</p>
            
            <div className="w-full max-w-md grid grid-cols-2 gap-2.5" style={{maxHeight:'45vh',overflowY:'auto'}}>
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => handleSend(s.prompt)}
                  className="text-left p-3 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.06] hover:border-white/10 transition-all active:scale-[0.98] group">
                  <span className="text-lg mb-1 block">{s.icon}</span>
                  <p className="text-xs font-medium text-slate-300 group-hover:text-white transition-colors">{s.title}</p>
                  <p className="text-[10px] text-slate-600 mt-0.5">{s.sub}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ═══ MESSAGES ═══ */}
        {!isNewChat && (
          <div className="max-w-2xl mx-auto px-4 py-4 space-y-1">
            {messages.map((msg, i) => (
              <div key={i} className="group">
                {msg.role === 'user' ? (
                  // USER MESSAGE
                  <div className="flex justify-end py-2">
                    <div className="max-w-[80%] bg-blue-600 rounded-2xl rounded-br-md px-4 py-2.5 shadow-lg shadow-blue-600/10">
                      <p className="text-[13.5px] whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  </div>
                ) : (
                  // ASSISTANT MESSAGE
                  <div className="py-3">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Sparkles size={12} />
                      </div>
                      <div className="flex-1 min-w-0 text-slate-200">
                        <MarkdownMessage content={msg.content} />
                        {/* Action buttons */}
                        <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => copyMessage(msg.content, i)} className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-white px-1.5 py-1 rounded transition-colors">
                            {copiedIdx === i ? <><Check size={10} className="text-emerald-400" /> <span className="text-emerald-400">Copied</span></> : <><Copy size={10} /> Copy</>}
                          </button>
                          {i === messages.length - 1 && msg.role === 'assistant' && (
                            <button onClick={handleRegenerate} className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-white px-1.5 py-1 rounded transition-colors">
                              <RotateCcw size={10} /> Regenerate
                            </button>
                          )}
                          {msg.model && <span className="text-[9px] text-slate-600 ml-auto">{models.find(m => m.id === msg.model)?.name || msg.model}</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* ═══ STREAMING IN-PROGRESS ═══ */}
            {streaming && streamText && (
              <div className="py-3">
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5 animate-pulse">
                    <Sparkles size={12} />
                  </div>
                  <div className="flex-1 min-w-0 text-slate-200">
                    <MarkdownMessage content={streamText + '▊'} />
                  </div>
                </div>
              </div>
            )}
            
            {/* Thinking indicator */}
            {(streaming && !streamText) && <ThinkingDots />}
            {loading && <ThinkingDots />}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Scroll to bottom */}
      {showScrollBtn && (
        <div className="flex justify-center -mt-8 relative z-10">
          <button onClick={() => scrollToBottom()} className="p-1.5 bg-slate-800 rounded-full shadow-lg border border-slate-700 hover:bg-slate-700 transition-colors">
            <ChevronDown size={16} />
          </button>
        </div>
      )}

      {/* ═══ INPUT BAR ═══ */}
      <div className="px-3 pt-2 pb-2 bg-[#0a0a0f]" style={{ paddingBottom: 'calc(75px + env(safe-area-inset-bottom, 0px))' }}>
        <div className="max-w-2xl mx-auto relative">
          {/* Model selector popover */}
          <ModelSelector models={models} selected={selectedModel} onSelect={setSelectedModel} show={showModelPicker} onToggle={setShowModelPicker} />
          
          <div className="bg-white/[0.05] border border-white/[0.08] rounded-2xl focus-within:border-white/15 transition-colors">
            {/* Textarea */}
            <textarea ref={inputRef} value={input}
              onChange={e => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px' }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder="JARVIS se pucho... / Ask JARVIS anything..."
              rows={1}
              className="w-full bg-transparent px-4 pt-3 pb-1 text-sm resize-none outline-none placeholder-slate-600 scrollbar-hide"
              style={{ maxHeight: '150px' }}
              disabled={loading || streaming} />
            
            {/* Bottom row: model selector + send */}
            <div className="flex items-center justify-between px-3 pb-2.5">
              <button onClick={() => setShowModelPicker(!showModelPicker)}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-white/5 transition-colors text-slate-500 hover:text-slate-300">
                <Cpu size={12} />
                <span className="text-[10px] font-medium">{modelLabel}</span>
                <ChevronRight size={10} className={`transition-transform ${showModelPicker ? 'rotate-90' : ''}`} />
              </button>
              
              <div className="flex items-center gap-1.5">
                {streaming ? (
                  <button onClick={handleStop} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/15 transition-colors" title="Stop">
                    <StopCircle size={16} className="text-white" />
                  </button>
                ) : (
                  <button onClick={() => handleSend()} disabled={!input.trim() || loading}
                    className={`p-1.5 rounded-lg transition-all ${
                      input.trim() ? 'bg-white text-black hover:bg-slate-200' : 'bg-white/10 text-slate-600'
                    }`}>
                    <ArrowUp size={16} />
                  </button>
                )}
              </div>
            </div>
          </div>
          
          <p className="text-[9px] text-slate-600 text-center mt-1.5">JARVIS can make mistakes. Verify important trading decisions independently.</p>
        </div>
      </div>
    </div>
  )
}

export default AIChat
