import React, { useState, useEffect, useCallback, useRef } from 'react'
import jarvisCore from '../services/jarvisCore'
import jarvisPersonality from '../services/jarvisPersonality'
import jarvisBrain from '../services/jarvisBrain'
import offlineEngine from '../services/offlineEngine'
import crashAnalytics from '../services/crashAnalytics'
import { API_BASE } from '../services/apiBase'

/**
 * 🤖 JARVIS Iron Man Command Center
 * ═══════════════════════════════════
 * 
 * The main AI interface — looks and feels like
 * Tony Stark's JARVIS holographic display.
 * 
 * Features:
 * - AI chat with personality
 * - System health HUD
 * - Real-time signal feed
 * - Voice activation ready
 * - Autonomous brain status
 * - Zero-dependency status indicator
 */

const JarvisCommandCenter = () => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [systemHealth, setSystemHealth] = useState(null)
  const [signals, setSignals] = useState([])
  const [isInitialized, setIsInitialized] = useState(false)
  const [activeTab, setActiveTab] = useState('chat') // chat, brain, health, signals
  const [brainStats, setBrainStats] = useState(null)
  const chatRef = useRef(null)

  // Initialize JARVIS Core
  useEffect(() => {
    let mounted = true

    const boot = async () => {
      try {
        await jarvisCore.init(API_BASE)
        if (!mounted) return
        setIsInitialized(true)

        // Boot greeting
        const greeting = jarvisPersonality.getGreeting()
        setMessages([{ role: 'jarvis', text: greeting, ts: Date.now() }])

        // Start autonomous brain monitoring
        jarvisBrain.startMonitoring(() => jarvisCore.getAllPrices(), 15000)

        // Periodic health updates
        const healthTimer = setInterval(() => {
          if (mounted) {
            setSystemHealth(jarvisCore.getSystemHealth())
            setBrainStats(jarvisBrain.getStats())
            setSignals(jarvisBrain.getLatestSignals(5))
          }
        }, 5000)

        // Initial health check
        setSystemHealth(jarvisCore.getSystemHealth())

        return () => clearInterval(healthTimer)
      } catch (e) {
        console.error('[JARVIS CC] Boot error:', e)
        setMessages([{ role: 'jarvis', text: jarvisPersonality.getErrorMessage(e.message), ts: Date.now() }])
        setIsInitialized(true)
      }
    }

    boot()
    return () => { mounted = false }
  }, [])

  // Auto-scroll chat
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages])

  const sendMessage = useCallback(async () => {
    const msg = input.trim()
    if (!msg || isThinking) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg, ts: Date.now() }])
    setIsThinking(true)

    try {
      // Special commands
      if (msg.toLowerCase() === 'status' || msg.toLowerCase() === 'health') {
        const health = jarvisCore.getSystemHealth()
        const statusMsg = `🤖 JARVIS System Status:\n\n` +
          `Overall: ${health.overall?.toUpperCase()} (${health.score}%)\n` +
          `Uptime: ${health.uptimeFormatted}\n` +
          `AI Provider: ${health.ai?.current || 'initializing'}\n` +
          `Data Pipeline: ${health.pipeline?.score ?? '--'}% healthy\n` +
          `Version: v${health.version} ${health.codename}\n\n` +
          Object.entries(health.modules || {}).map(([k, v]) => `${v.status === 'healthy' ? '🟢' : v.status === 'degraded' ? '🟡' : '🔴'} ${k}: ${v.status}`).join('\n')

        setMessages(prev => [...prev, { role: 'jarvis', text: statusMsg, ts: Date.now() }])
        setIsThinking(false)
        return
      }

      if (msg.toLowerCase() === 'quote') {
        setMessages(prev => [...prev, { role: 'jarvis', text: jarvisPersonality.getIronManQuote(), ts: Date.now() }])
        setIsThinking(false)
        return
      }

      if (msg.toLowerCase().startsWith('signals')) {
        const sigs = jarvisBrain.getLatestSignals(5)
        const sigMsg = sigs.length > 0 ?
          `📊 Latest JARVIS Signals:\n\n${sigs.map(s => `${s.signal === 'BUY' ? '🟢' : s.signal === 'SELL' ? '🔴' : '🟡'} ${s.symbol?.toUpperCase()} — ${s.signal} (${s.confidence}%)\n   ${s.reason}`).join('\n\n')}` :
          'No signals yet. The autonomous brain needs a few cycles to analyze patterns.'

        setMessages(prev => [...prev, { role: 'jarvis', text: sigMsg, ts: Date.now() }])
        setIsThinking(false)
        return
      }

      // Regular AI chat — uses failover chain
      const response = await jarvisCore.ask(msg)
      const jarvisReply = response.text || 'I processed your request but couldn\'t generate a response. Try rephrasing.'
      const providerNote = response.provider && response.provider !== 'backend' ?
        `\n\n_[via ${response.provider}${response.isOffline ? ' — offline mode' : ''}]_` : ''

      // Add personality comment
      let personalNote = ''
      if (msg.toLowerCase().includes('buy') || msg.toLowerCase().includes('sell') || msg.toLowerCase().includes('signal')) {
        personalNote = '\n\n' + jarvisPersonality.commentOnSignal({ action: msg.toLowerCase().includes('buy') ? 'BUY' : msg.toLowerCase().includes('sell') ? 'SELL' : 'HOLD', confidence: 70, symbol: 'Market' })
      }

      setMessages(prev => [...prev, { role: 'jarvis', text: jarvisReply + personalNote + providerNote, ts: Date.now() }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'jarvis', text: jarvisPersonality.getErrorMessage(e.message), ts: Date.now() }])
    }

    setIsThinking(false)
  }, [input, isThinking])

  const renderHealthHUD = () => {
    if (!systemHealth) return null
    const h = systemHealth

    return (
      <div className="space-y-3">
        {/* Overall Status Arc */}
        <div className="bg-gradient-to-br from-blue-900/50 to-purple-900/50 border border-blue-500/30 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-cyan-400">JARVIS CORE v{h.version}</h3>
            <span className="text-xs text-blue-300 font-mono">{h.codename}</span>
          </div>
          <div className="flex items-center space-x-4 mb-4">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="#1e293b" strokeWidth="3" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke={h.score >= 80 ? '#22c55e' : h.score >= 50 ? '#eab308' : '#ef4444'}
                  strokeWidth="3" strokeDasharray={`${h.score || 0}, 100`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-bold text-white">{h.score ?? '--'}%</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-300">Overall: <span className={`font-bold ${h.overall === 'healthy' ? 'text-emerald-400' : h.overall === 'degraded' ? 'text-yellow-400' : 'text-red-400'}`}>{h.overall?.toUpperCase()}</span></p>
              <p className="text-xs text-slate-400 mt-1">Uptime: {h.uptimeFormatted}</p>
              <p className="text-xs text-slate-400">AI: {h.ai?.current || 'initializing'}</p>
            </div>
          </div>

          {/* Module Status Grid */}
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(h.modules || {}).map(([name, mod]) => (
              <div key={name} className="bg-slate-800/60 rounded-lg p-2 flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${mod.status === 'healthy' ? 'bg-emerald-400' : mod.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'}`} />
                <span className="text-xs text-slate-300 truncate">{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Providers */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-cyan-400 mb-2">AI Failover Chain</h4>
          <div className="space-y-1.5">
            {(h.ai?.providers || []).map((p, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${p.status === 'ok' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                  <span className={`text-xs ${h.ai?.current === p.name ? 'text-cyan-400 font-bold' : 'text-slate-400'}`}>{p.name}</span>
                </div>
                <span className="text-[10px] text-slate-500">
                  {h.ai?.current === p.name ? '⚡ ACTIVE' : p.status === 'ok' ? 'standby' : `${p.fails} fails`}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Data Pipeline */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-cyan-400 mb-2">Data Pipeline</h4>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400">Health Score</span>
            <span className="text-xs font-bold text-emerald-400">{h.pipeline?.score ?? '--'}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div className="bg-gradient-to-r from-cyan-500 to-emerald-500 h-1.5 rounded-full transition-all"
              style={{ width: `${h.pipeline?.score ?? 0}%` }} />
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-slate-500">
            <span>Healthy: {h.pipeline?.healthy ?? 0}</span>
            <span>Cached: {h.pipeline?.cached ?? 0}</span>
            <span>Down: {h.pipeline?.failing ?? 0}</span>
          </div>
        </div>

        {/* Storage */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-cyan-400 mb-2">Offline Storage</h4>
          {(() => {
            const stats = offlineEngine.getStorageStats()
            return (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-slate-400">Items:</span> <span className="text-white">{stats.jarvisItems}</span></div>
                <div><span className="text-slate-400">Size:</span> <span className="text-white">{stats.totalSizeKB} KB</span></div>
                <div><span className="text-slate-400">Queue:</span> <span className="text-white">{stats.queueSize}</span></div>
                <div><span className="text-slate-400">Network:</span> <span className={`font-bold ${stats.isOnline ? 'text-emerald-400' : 'text-red-400'}`}>{stats.isOnline ? 'Online' : 'Offline'}</span></div>
              </div>
            )
          })()}
        </div>
      </div>
    )
  }

  const renderBrainTab = () => {
    const stats = brainStats || jarvisBrain.getStats()

    return (
      <div className="space-y-3">
        <div className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 border border-purple-500/30 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-purple-400">🧠 Autonomous Brain</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${stats.isRunning ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
              {stats.isRunning ? 'ACTIVE' : 'STOPPED'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-slate-800/50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-cyan-400">{stats.totalSignals}</p>
              <p className="text-[10px] text-slate-400">Total Signals</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-purple-400">{stats.confidenceThreshold}%</p>
              <p className="text-[10px] text-slate-400">Min Confidence</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-amber-400">{stats.mode}</p>
              <p className="text-[10px] text-slate-400">Decision Mode</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-emerald-400">{stats.activePositions}</p>
              <p className="text-[10px] text-slate-400">Active Positions</p>
            </div>
          </div>

          {/* Mode Selector */}
          <div className="mb-3">
            <p className="text-xs text-slate-400 mb-2">Decision Mode</p>
            <div className="flex space-x-2">
              {['OBSERVER', 'ADVISOR', 'AUTONOMOUS'].map(mode => (
                <button key={mode} onClick={() => { jarvisBrain.mode = mode; setBrainStats({ ...stats, mode }) }}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                    stats.mode === mode
                      ? mode === 'AUTONOMOUS' ? 'bg-red-600 text-white ring-2 ring-red-400/50' :
                        mode === 'ADVISOR' ? 'bg-blue-600 text-white ring-2 ring-blue-400/50' :
                        'bg-slate-600 text-white ring-2 ring-slate-400/50'
                      : 'bg-slate-700 text-slate-400'
                  }`}>
                  {mode === 'AUTONOMOUS' ? '🦾' : mode === 'ADVISOR' ? '🧠' : '👁️'} {mode}
                </button>
              ))}
            </div>
          </div>

          {stats.mode === 'AUTONOMOUS' && (
            <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-3 text-center">
              <p className="text-xs text-red-400 font-bold">⚠️ IRON MAN MODE ACTIVE</p>
              <p className="text-[10px] text-red-300/70">JARVIS is making autonomous trading decisions</p>
            </div>
          )}
        </div>

        {/* Latest Signals */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-purple-400 mb-3">Latest Brain Signals</h4>
          {signals.length > 0 ? (
            <div className="space-y-2">
              {signals.map((s, i) => (
                <div key={i} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2.5">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${s.signal === 'BUY' ? 'bg-emerald-400' : s.signal === 'SELL' ? 'bg-red-400' : 'bg-yellow-400'}`} />
                    <div>
                      <span className="text-xs font-bold text-white">{s.symbol?.toUpperCase()}</span>
                      <p className="text-[10px] text-slate-400 truncate max-w-[200px]">{s.reason}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-bold ${s.signal === 'BUY' ? 'text-emerald-400' : s.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>{s.signal}</span>
                    <p className="text-[10px] text-slate-400">{s.confidence}%</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-4">Brain is analyzing patterns... Signals will appear here.</p>
          )}
        </div>
      </div>
    )
  }

  const renderSignals = () => (
    <div className="space-y-3">
      <div className="bg-gradient-to-br from-emerald-900/30 to-blue-900/30 border border-emerald-500/20 rounded-2xl p-5">
        <h3 className="text-lg font-bold text-emerald-400 mb-2">📡 Live Signal Feed</h3>
        <p className="text-xs text-slate-400 mb-4">Multi-source AI analysis running continuously</p>

        {signals.length > 0 ? signals.map((s, i) => (
          <div key={i} className="bg-slate-800/70 rounded-xl p-4 mb-2 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className={`text-lg ${s.signal === 'BUY' ? '🟢' : s.signal === 'SELL' ? '🔴' : '🟡'}`}></span>
                <span className="text-base font-bold text-white">{s.symbol?.toUpperCase()}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${s.signal === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : s.signal === 'SELL' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {s.signal}
                </span>
                <span className="text-xs text-slate-400">{s.confidence}%</span>
              </div>
            </div>
            <p className="text-xs text-slate-300">{s.reason}</p>
            {s.indicators && (
              <div className="flex flex-wrap gap-1 mt-2">
                {s.indicators.rsi && <span className="px-1.5 py-0.5 bg-slate-700 rounded text-[10px] text-slate-400">RSI: {s.indicators.rsi.toFixed(0)}</span>}
                {s.indicators.macd && <span className="px-1.5 py-0.5 bg-slate-700 rounded text-[10px] text-slate-400">MACD: {s.indicators.macd > 0 ? '+' : ''}{s.indicators.macd.toFixed(2)}</span>}
              </div>
            )}
            <p className="text-[10px] text-slate-500 mt-1">
              {jarvisPersonality.commentOnSignal(s)}
            </p>
          </div>
        )) : (
          <div className="text-center py-8">
            <p className="text-4xl mb-2">🔍</p>
            <p className="text-sm text-slate-400">JARVIS Brain is analyzing markets...</p>
            <p className="text-xs text-slate-500 mt-1">Signals appear when confidence exceeds {jarvisBrain.confidenceThreshold}%</p>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-24">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900/50 via-purple-900/30 to-blue-900/50 border-b border-cyan-500/20 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <span className="text-lg">🤖</span>
            </div>
            <div>
              <h1 className="text-base font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">J.A.R.V.I.S.</h1>
              <p className="text-[10px] text-slate-400">
                {isInitialized ? (navigator.onLine ? '🟢 All systems online' : '🟡 Offline mode') : '⏳ Booting...'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-1.5">
            {systemHealth && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                (systemHealth.score ?? 0) >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                (systemHealth.score ?? 0) >= 50 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {systemHealth.score ?? '--'}%
              </span>
            )}
          </div>
        </div>

        {/* Tab Nav */}
        <div className="flex space-x-1 mt-3">
          {[
            { id: 'chat', label: '💬 Chat', color: 'cyan' },
            { id: 'brain', label: '🧠 Brain', color: 'purple' },
            { id: 'signals', label: '📡 Signals', color: 'emerald' },
            { id: 'health', label: '❤️ Health', color: 'blue' },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === tab.id
                  ? `bg-${tab.color}-500/20 text-${tab.color}-400 border border-${tab.color}-500/30`
                  : 'text-slate-500 hover:text-slate-300'
              }`}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'health' && renderHealthHUD()}
        {activeTab === 'brain' && renderBrainTab()}
        {activeTab === 'signals' && renderSignals()}

        {activeTab === 'chat' && (
          <>
            {/* Chat Messages */}
            <div ref={chatRef} className="space-y-3 mb-4 max-h-[calc(100vh-260px)] overflow-y-auto">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl p-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-sm'
                  }`}>
                    {msg.role === 'jarvis' && (
                      <span className="text-[10px] text-cyan-400 font-bold block mb-1">JARVIS</span>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                    <span className="text-[10px] text-slate-500 mt-1 block text-right">
                      {new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}

              {isThinking && (
                <div className="flex justify-start">
                  <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm p-3">
                    <span className="text-[10px] text-cyan-400 font-bold block mb-1">JARVIS</span>
                    <div className="flex space-x-1.5">
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex space-x-2 mb-3 overflow-x-auto pb-1">
              {['status', 'signals', 'quote', 'analyze BTC', 'market overview', 'portfolio advice'].map(cmd => (
                <button key={cmd} onClick={() => { setInput(cmd); }}
                  className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-400 hover:text-cyan-400 hover:border-cyan-500/30 whitespace-nowrap transition-all">
                  {cmd}
                </button>
              ))}
            </div>

            {/* Input */}
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Ask JARVIS anything..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none"
              />
              <button onClick={sendMessage} disabled={isThinking || !input.trim()}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-4 py-3 rounded-xl font-bold text-sm disabled:opacity-50 transition-all active:scale-95 shadow-lg shadow-cyan-500/20">
                {isThinking ? '...' : '→'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default JarvisCommandCenter
