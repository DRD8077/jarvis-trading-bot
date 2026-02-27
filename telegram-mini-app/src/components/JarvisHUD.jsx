/**
 * 🎯 JARVIS HUD OVERLAY — Iron Man Heads-Up Display v2
 * ═══════════════════════════════════════════════════════
 * 
 * - Arc reactor pulse animation
 * - Voice wave animation when speaking
 * - System status indicators
 * - Suit mode display + quick switch
 * - Ambient data stream ticker
 * - Threat level indicator
 * - Memory-based stats (win rate, streak)
 * - Emergency mode (red)
 */

import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, Activity, Zap, Shield, AlertTriangle, Mic, Volume2, ChevronUp, ChevronDown, Wifi, WifiOff, Brain, Eye, Swords, Search, ShieldCheck, Cpu } from 'lucide-react'

const JarvisHUD = () => {
  const navigate = useNavigate()
  const [isExpanded, setIsExpanded] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isEmergency, setIsEmergency] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [brainActive, setBrainActive] = useState(false)
  const [lastAlert, setLastAlert] = useState('')
  const [currentMode, setCurrentMode] = useState('standard')
  const [modeColor, setModeColor] = useState('#3b82f6')
  const [dataStream, setDataStream] = useState([])
  const [tradingStats, setTradingStats] = useState({ wins: 0, winRate: '0', streak: 0 })
  const [threatLevel, setThreatLevel] = useState('LOW')
  const [arcPower, setArcPower] = useState(100)
  const [aiName, setAiName] = useState('J.A.R.V.I.S')
  const [aiColor, setAiColor] = useState('#22d3ee')
  const [userMood, setUserMood] = useState(null)
  const [activeProtocol, setActiveProtocol] = useState(null)
  const [systemStatus, setSystemStatus] = useState({
    voice: true,
    brain: false,
    scanner: true,
    market: true,
  })
  const [pulseColor, setPulseColor] = useState('cyan')
  const hudRef = useRef(null)

  useEffect(() => {
    // Listen for JARVIS events
    const onSpeak = () => { setIsSpeaking(true); setTimeout(() => setIsSpeaking(false), 3000) }
    const onEmergency = (e) => {
      setIsEmergency(true)
      setPulseColor('red')
      setThreatLevel('CRITICAL')
      setLastAlert(e.detail?.symbol ? `${e.detail.symbol} CRASH!` : 'EMERGENCY!')
      setTimeout(() => { setIsEmergency(false); setPulseColor('cyan'); setThreatLevel('LOW') }, 30000)
    }
    const onBrainScan = () => {
      setBrainActive(true)
      setTimeout(() => setBrainActive(false), 5000)
    }
    const onOnline = () => setIsOnline(true)
    const onOffline = () => setIsOnline(false)
    const onModeChange = (e) => {
      const mode = e.detail
      if (mode?.id) setCurrentMode(mode.id)
      if (mode?.color) setModeColor(mode.color)
    }
    const onHudToggle = () => setIsExpanded(prev => !prev)

    window.addEventListener('jarvis-speak', onSpeak)
    window.addEventListener('jarvis-emergency', onEmergency)
    window.addEventListener('jarvis-brain-scan', onBrainScan)
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    window.addEventListener('jarvis-mode-change', onModeChange)
    window.addEventListener('jarvis-hud-toggle', onHudToggle)

    // Listen for new v29 systems
    const onPowerUpdate = (e) => setArcPower(e.detail?.level || 100)
    const onPersonalityChange = (e) => {
      if (e.detail?.name) setAiName(e.detail.name)
      if (e.detail?.color) setAiColor(e.detail.color)
    }
    const onMoodChange = (e) => setUserMood(e.detail)
    const onProtocolActive = (e) => setActiveProtocol(e.detail)
    const onProtocolDeactive = () => setActiveProtocol(null)

    window.addEventListener('jarvis-power-update', onPowerUpdate)
    window.addEventListener('jarvis-personality-change', onPersonalityChange)
    window.addEventListener('jarvis-mood-change', onMoodChange)
    window.addEventListener('jarvis-protocol-activated', onProtocolActive)
    window.addEventListener('jarvis-protocol-deactivated', onProtocolDeactive)

    // Load memory stats
    import('../services/jarvisMemory.js').then(m => {
      const mem = m.default || m
      if (mem?.getTradingStats) {
        const stats = mem.getTradingStats()
        setTradingStats({ wins: stats.wins || 0, winRate: stats.winRate || '0', streak: stats.profitStreak || 0 })
      }
    }).catch(() => {})

    // Load current suit mode
    import('../services/jarvisSuitModes.js').then(m => {
      const modes = m.default || m
      if (modes?.getMode) {
        const mode = modes.getMode()
        setCurrentMode(mode.id)
        setModeColor(mode.color)
      }
    }).catch(() => {})

    // Load AI personality
    import('../services/jarvisPersonalities.js').then(m => {
      const pers = m.default || m
      if (pers?.getPersonality) {
        const p = pers.getPersonality()
        setAiName(p.name)
        setAiColor(p.color)
      }
    }).catch(() => {})

    // Load arc reactor power
    import('../services/jarvisArcReactor.js').then(m => {
      const arc = m.default || m
      if (arc?.getPowerLevel) setArcPower(arc.getPowerLevel())
    }).catch(() => {})

    // Ambient data stream — scrolling mini-ticker
    const streamInterval = setInterval(() => {
      const items = [
        'BTC scanning...', 'ETH monitoring...', 'SOL tracking...', 'Gems: hunting...',
        'Whales: watching...', 'DexScreener: live', 'Brain: active', 'Shield: on',
        'Nifty: tracking', 'Portfolio: guarded', 'Threats: scanning', 'Voice: ready'
      ]
      setDataStream(prev => {
        const next = [...prev, items[Math.floor(Math.random() * items.length)]]
        return next.slice(-3) // Keep last 3
      })
    }, 4000)

    // Brain status check
    const brainCheck = setInterval(() => {
      const brainRunning = !!window.__jarvisProactiveBrain
      setSystemStatus(prev => ({ ...prev, brain: brainRunning }))
    }, 10000)

    return () => {
      window.removeEventListener('jarvis-speak', onSpeak)
      window.removeEventListener('jarvis-emergency', onEmergency)
      window.removeEventListener('jarvis-brain-scan', onBrainScan)
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
      window.removeEventListener('jarvis-mode-change', onModeChange)
      window.removeEventListener('jarvis-hud-toggle', onHudToggle)
      window.removeEventListener('jarvis-power-update', onPowerUpdate)
      window.removeEventListener('jarvis-personality-change', onPersonalityChange)
      window.removeEventListener('jarvis-mood-change', onMoodChange)
      window.removeEventListener('jarvis-protocol-activated', onProtocolActive)
      window.removeEventListener('jarvis-protocol-deactivated', onProtocolDeactive)
      clearInterval(brainCheck)
      clearInterval(streamInterval)
    }
  }, [])

  const handleTapToTalk = () => {
    // Navigate to voice/chat
    navigate('/chat')
    window.dispatchEvent(new CustomEvent('jarvis-speak', { 
      detail: { text: 'Haan Sir, bataiye! Main sun rahi hoon.', priority: 'high' } 
    }))
  }

  const handleForcesScan = () => {
    window.dispatchEvent(new CustomEvent('jarvis-speak', { 
      detail: { text: 'Sir, emergency scan shuru kar rahi hoon. Sab check hoga.', priority: 'high' } 
    }))
    // Trigger brain scan
    import('../services/jarvisProactiveBrain.js').then(m => {
      const brain = m.default || m
      if (brain?.scanNow) brain.scanNow()
    }).catch(() => {})
  }

  const arcReactorColor = isEmergency ? '#ef4444' : isSpeaking ? '#22d3ee' : '#3b82f6'
  const glowIntensity = isSpeaking ? '0 0 20px' : '0 0 10px'

  return (
    <div 
      ref={hudRef}
      className="fixed top-0 left-0 right-0 z-[9999] pointer-events-none"
      style={{ userSelect: 'none' }}
    >
      {/* Main HUD Bar */}
      <div className="pointer-events-auto mx-2 mt-1">
        <div 
          className={`flex items-center justify-between px-2 py-1 rounded-xl backdrop-blur-xl border transition-all duration-500 ${
            isEmergency 
              ? 'bg-red-950/80 border-red-500/60 shadow-lg shadow-red-500/20' 
              : 'bg-slate-950/70 border-cyan-500/20 shadow-lg shadow-cyan-500/5'
          }`}
        >
          {/* Left: Arc Reactor + JARVIS label */}
          <div className="flex items-center gap-1.5" onClick={handleTapToTalk}>
            {/* Arc Reactor */}
            <div className="relative">
              <div 
                className="w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300"
                style={{
                  background: `radial-gradient(circle, ${arcReactorColor}40 0%, transparent 70%)`,
                  boxShadow: `${glowIntensity} ${arcReactorColor}`,
                }}
              >
                <div 
                  className="w-3 h-3 rounded-full animate-pulse"
                  style={{ 
                    background: arcReactorColor,
                    boxShadow: `0 0 8px ${arcReactorColor}, 0 0 16px ${arcReactorColor}40`
                  }}
                />
              </div>
              {/* Speaking wave rings */}
              {isSpeaking && (
                <>
                  <div className="absolute inset-0 rounded-full border border-cyan-400/40 animate-ping" />
                  <div className="absolute -inset-1 rounded-full border border-cyan-400/20 animate-ping" style={{ animationDelay: '0.3s' }} />
                </>
              )}
            </div>
            <div className="flex flex-col">
              <span className={`text-[9px] font-bold tracking-widest`} style={{ color: aiColor }}>
                {aiName}
              </span>
              {isSpeaking && (
                <div className="flex gap-[1px]">
                  {[1,2,3,4,5].map(i => (
                    <div key={i} className="w-[2px] bg-cyan-400 rounded-full animate-pulse" 
                      style={{ height: `${3 + Math.random() * 6}px`, animationDelay: `${i * 0.1}s` }} 
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Center: Status indicators */}
          <div className="flex items-center gap-2">
            {/* Arc Reactor Power */}
            <div className={`flex items-center gap-0.5 ${arcPower > 60 ? 'text-cyan-400' : arcPower > 30 ? 'text-yellow-400' : 'text-red-400'}`}>
              <Zap size={9} />
              <span className="text-[7px] font-bold font-mono">{arcPower}%</span>
            </div>

            {/* Brain status */}
            <div className={`flex items-center gap-0.5 ${brainActive ? 'text-purple-400' : 'text-slate-500'}`}>
              <Brain size={10} className={brainActive ? 'animate-pulse' : ''} />
            </div>
            
            {/* Mood indicator */}
            {userMood && (
              <span className="text-[8px]" title={userMood.label}>{userMood.emoji}</span>
            )}

            {/* Active protocol badge */}
            {activeProtocol && (
              <span className="text-[6px] px-1 py-0.5 rounded font-bold animate-pulse" style={{ backgroundColor: activeProtocol.color + '30', color: activeProtocol.color }}>
                {activeProtocol.icon}
              </span>
            )}

            {/* Online status */}
            <div className={`flex items-center gap-0.5 ${isOnline ? 'text-emerald-400' : 'text-red-400'}`}>
              {isOnline ? <Wifi size={10} /> : <WifiOff size={10} />}
            </div>

            {/* Emergency badge */}
            {isEmergency && (
              <div className="flex items-center gap-0.5 text-red-400 animate-pulse">
                <AlertTriangle size={10} />
                <span className="text-[8px] font-bold">ALERT</span>
              </div>
            )}

            {/* Shield (security) */}
            <Shield size={10} className="text-emerald-500/60" />
          </div>

          {/* Right: Quick actions */}
          <div className="flex items-center gap-1.5">
            {/* Mic - tap to talk */}
            <button 
              onClick={handleTapToTalk}
              className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                isListening ? 'bg-red-500/30 text-red-400' : 'bg-cyan-500/10 text-cyan-400'
              }`}
            >
              <Mic size={11} />
            </button>

            {/* Expand button */}
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="w-5 h-5 rounded-full flex items-center justify-center bg-slate-800/50 text-slate-400"
            >
              {isExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
          </div>
        </div>

        {/* Expanded Panel — Iron Man Full HUD */}
        {isExpanded && (
          <div className={`mt-1 p-2 rounded-xl backdrop-blur-xl border transition-all duration-300 ${
            isEmergency 
              ? 'bg-red-950/80 border-red-500/40' 
              : 'bg-slate-950/80 border-cyan-500/15'
          }`}>
            {/* Suit Mode Banner */}
            <div className="flex items-center justify-between mb-2 px-1">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-bold tracking-wider" style={{ color: modeColor }}>
                  {currentMode.toUpperCase()} MODE
                </span>
                <span className="text-[7px] text-slate-500">
                  {currentMode === 'standard' ? 'Mark III' : currentMode === 'combat' ? 'Hulkbuster' : currentMode === 'stealth' ? 'Sneaky' : currentMode === 'recon' ? 'Heartbreaker' : currentMode === 'guardian' ? 'Striker' : 'Full Auto'}
                </span>
              </div>
              {/* Threat Level */}
              <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[7px] font-bold ${
                threatLevel === 'CRITICAL' ? 'bg-red-500/20 text-red-400 animate-pulse' :
                threatLevel === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                threatLevel === 'MODERATE' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-emerald-500/20 text-emerald-400'
              }`}>
                <div className={`w-1.5 h-1.5 rounded-full ${
                  threatLevel === 'CRITICAL' ? 'bg-red-500' : threatLevel === 'HIGH' ? 'bg-orange-500' : threatLevel === 'MODERATE' ? 'bg-yellow-500' : 'bg-emerald-500'
                }`} />
                THREAT: {threatLevel}
              </div>
            </div>

            {/* System Status Grid */}
            <div className="grid grid-cols-4 gap-1.5 mb-2">
              {[
                { label: 'VOICE', active: true, icon: Volume2, color: 'cyan' },
                { label: 'BRAIN', active: systemStatus.brain, icon: Brain, color: 'purple' },
                { label: 'SCAN', active: systemStatus.scanner, icon: Eye, color: 'emerald' },
                { label: 'GUARD', active: true, icon: Shield, color: 'blue' },
              ].map((sys, i) => (
                <div key={i} className={`flex flex-col items-center p-1 rounded-lg border ${
                  sys.active ? 'bg-slate-800/50 border-slate-600/30' : 'bg-slate-900/50 border-slate-800/30'
                }`}>
                  <sys.icon size={12} className={sys.active ? `text-${sys.color}-400` : 'text-slate-600'} />
                  <span className={`text-[7px] font-bold mt-0.5 ${sys.active ? 'text-slate-300' : 'text-slate-600'}`}>
                    {sys.label}
                  </span>
                  <span className={`text-[6px] ${sys.active ? 'text-emerald-400' : 'text-red-400'}`}>
                    {sys.active ? '●' : '○'}
                  </span>
                </div>
              ))}
            </div>

            {/* Trading Stats from Memory */}
            {tradingStats.wins > 0 && (
              <div className="flex items-center justify-between px-2 py-1 mb-2 rounded-lg bg-slate-800/40 border border-slate-700/20">
                <span className="text-[8px] text-slate-400">Win Rate</span>
                <span className={`text-[9px] font-bold ${parseFloat(tradingStats.winRate) >= 50 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {tradingStats.winRate}%
                </span>
                <span className="text-[8px] text-slate-400">Wins</span>
                <span className="text-[9px] font-bold text-cyan-400">{tradingStats.wins}</span>
                {tradingStats.streak > 0 && (
                  <>
                    <span className="text-[8px] text-slate-400">Streak</span>
                    <span className="text-[9px] font-bold text-yellow-400">🔥{tradingStats.streak}</span>
                  </>
                )}
              </div>
            )}

            {/* Suit Mode Quick Switch */}
            <div className="flex gap-1 mb-2 overflow-x-auto pb-1">
              {[
                { id: 'standard', icon: '🦾', label: 'STD', color: '#3b82f6' },
                { id: 'combat', icon: '⚔️', label: 'CMB', color: '#ef4444' },
                { id: 'stealth', icon: '🥷', label: 'STL', color: '#64748b' },
                { id: 'recon', icon: '🔍', label: 'RCN', color: '#8b5cf6' },
                { id: 'guardian', icon: '🛡️', label: 'GRD', color: '#22c55e' },
                { id: 'autopilot', icon: '🤖', label: 'AUTO', color: '#06b6d4' },
              ].map(mode => (
                <button
                  key={mode.id}
                  onClick={() => {
                    import('../services/jarvisSuitModes.js').then(m => {
                      const modes = m.default || m
                      if (modes?.setMode) modes.setMode(mode.id)
                    }).catch(() => {})
                    setCurrentMode(mode.id)
                    setModeColor(mode.color)
                  }}
                  className={`flex flex-col items-center px-2 py-1 rounded-lg border text-[7px] transition-all ${
                    currentMode === mode.id 
                      ? 'border-opacity-60 bg-opacity-20 scale-105' 
                      : 'border-slate-700/20 bg-slate-800/30'
                  }`}
                  style={{
                    borderColor: currentMode === mode.id ? mode.color : undefined,
                    backgroundColor: currentMode === mode.id ? mode.color + '20' : undefined,
                  }}
                >
                  <span className="text-sm">{mode.icon}</span>
                  <span className="font-bold" style={{ color: currentMode === mode.id ? mode.color : '#64748b' }}>
                    {mode.label}
                  </span>
                </button>
              ))}
            </div>

            {/* Quick Actions */}
            <div className="flex gap-1.5 mb-1.5">
              <button 
                onClick={handleForcesScan}
                className="flex-1 py-1 rounded-lg bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Zap size={10} /> SCAN
              </button>
              <button 
                onClick={handleTapToTalk}
                className="flex-1 py-1 rounded-lg bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Mic size={10} /> TALK
              </button>
              <button 
                onClick={() => window.dispatchEvent(new CustomEvent('jarvis-hologram-open'))}
                className="flex-1 py-1 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Eye size={10} /> HOLO
              </button>
              <button 
                onClick={() => navigate('/workshop')}
                className="flex-1 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Cpu size={10} /> LAB
              </button>
            </div>

            {/* Ambient Data Stream */}
            {dataStream.length > 0 && (
              <div className="mt-1.5 overflow-hidden h-3">
                <div className="flex gap-3 animate-scroll-left">
                  {dataStream.map((item, i) => (
                    <span key={i} className="text-[7px] text-cyan-600/50 whitespace-nowrap font-mono">
                      ▸ {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Last Alert */}
            {lastAlert && (
              <div className="mt-1.5 px-2 py-1 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <span className="text-[8px] text-yellow-400">⚡ {lastAlert}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default JarvisHUD
