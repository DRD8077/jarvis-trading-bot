/**
 * 🎯 JARVIS HUD OVERLAY — Iron Man Heads-Up Display
 * ═══════════════════════════════════════════════════
 * 
 * Floating Iron Man-style status bar always visible on screen:
 * - Arc reactor pulse animation (blue glow)
 * - Voice wave animation when JARVIS speaks
 * - System status indicators (brain, scanner, market)
 * - Emergency mode (turns red on crashes)
 * - Tap to talk to JARVIS
 * - Expandable mini-panel with quick stats
 */

import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, Activity, Zap, Shield, AlertTriangle, Mic, Volume2, ChevronUp, ChevronDown, Wifi, WifiOff, Brain, Eye } from 'lucide-react'

const JarvisHUD = () => {
  const navigate = useNavigate()
  const [isExpanded, setIsExpanded] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isEmergency, setIsEmergency] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [brainActive, setBrainActive] = useState(false)
  const [lastAlert, setLastAlert] = useState('')
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
      setLastAlert(e.detail?.symbol ? `${e.detail.symbol} CRASH!` : 'EMERGENCY!')
      setTimeout(() => { setIsEmergency(false); setPulseColor('cyan') }, 30000)
    }
    const onBrainScan = () => {
      setBrainActive(true)
      setTimeout(() => setBrainActive(false), 5000)
    }
    const onOnline = () => setIsOnline(true)
    const onOffline = () => setIsOnline(false)

    window.addEventListener('jarvis-speak', onSpeak)
    window.addEventListener('jarvis-emergency', onEmergency)
    window.addEventListener('jarvis-brain-scan', onBrainScan)
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)

    // Start brain status check
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
      clearInterval(brainCheck)
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
              <span className={`text-[9px] font-bold tracking-widest ${isEmergency ? 'text-red-400' : 'text-cyan-400'}`}>
                J.A.R.V.I.S
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
            {/* Brain status */}
            <div className={`flex items-center gap-0.5 ${brainActive ? 'text-purple-400' : 'text-slate-500'}`}>
              <Brain size={10} className={brainActive ? 'animate-pulse' : ''} />
              <span className="text-[8px]">{brainActive ? 'SCAN' : 'IDLE'}</span>
            </div>
            
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

        {/* Expanded Panel */}
        {isExpanded && (
          <div className={`mt-1 p-2 rounded-xl backdrop-blur-xl border transition-all duration-300 ${
            isEmergency 
              ? 'bg-red-950/80 border-red-500/40' 
              : 'bg-slate-950/80 border-cyan-500/15'
          }`}>
            {/* System Status Grid */}
            <div className="grid grid-cols-4 gap-1.5 mb-2">
              {[
                { label: 'VOICE', active: true, icon: Volume2, color: 'cyan' },
                { label: 'BRAIN', active: systemStatus.brain, icon: Brain, color: 'purple' },
                { label: 'SCAN', active: systemStatus.scanner, icon: Eye, color: 'emerald' },
                { label: 'GUARD', active: true, icon: Shield, color: 'blue' },
              ].map((sys, i) => (
                <div key={i} className={`flex flex-col items-center p-1 rounded-lg ${
                  sys.active ? `bg-${sys.color}-500/10 border border-${sys.color}-500/20` : 'bg-slate-800/50 border border-slate-700/30'
                }`}>
                  <sys.icon size={12} className={sys.active ? `text-${sys.color}-400` : 'text-slate-500'} />
                  <span className={`text-[7px] font-bold mt-0.5 ${sys.active ? `text-${sys.color}-400` : 'text-slate-500'}`}>
                    {sys.label}
                  </span>
                  <span className={`text-[6px] ${sys.active ? 'text-emerald-400' : 'text-red-400'}`}>
                    {sys.active ? 'ONLINE' : 'OFFLINE'}
                  </span>
                </div>
              ))}
            </div>

            {/* Quick Actions */}
            <div className="flex gap-1.5">
              <button 
                onClick={handleForcesScan}
                className="flex-1 py-1 rounded-lg bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Zap size={10} /> FORCE SCAN
              </button>
              <button 
                onClick={handleTapToTalk}
                className="flex-1 py-1 rounded-lg bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-[9px] font-medium flex items-center justify-center gap-1"
              >
                <Mic size={10} /> TALK TO JARVIS
              </button>
            </div>

            {/* Last Alert */}
            {lastAlert && (
              <div className="mt-1.5 px-2 py-1 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <span className="text-[8px] text-yellow-400">Last Alert: {lastAlert}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default JarvisHUD
