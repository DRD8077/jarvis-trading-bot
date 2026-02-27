/**
 * 🦾 IRON MAN CINEMATIC BOOT SEQUENCE
 * ═════════════════════════════════════
 * 
 * Exactly like when Tony Stark puts on the suit:
 * - Dark screen → Arc reactor ignites
 * - HUD lines sweep across screen
 * - System checks appear one by one with scan lines
 * - "All systems nominal" → JARVIS speaks
 * - Hexagonal grid overlay fades in then out
 * - Final: JARVIS logo + "At your service, Sir"
 */

import React, { useState, useEffect, useCallback } from 'react'

const BOOT_SYSTEMS = [
  { id: 'core', label: 'Neural Core', sub: 'AI Engine v15.0', icon: '🧠', delay: 0 },
  { id: 'voice', label: 'Voice Matrix', sub: 'Hindi TTS Active', icon: '🎙️', delay: 200 },
  { id: 'scanner', label: 'Market Scanner', sub: 'DexScreener + CoinGecko', icon: '📡', delay: 400 },
  { id: 'brain', label: 'Proactive Brain', sub: 'Background Monitor', icon: '⚡', delay: 600 },
  { id: 'guard', label: 'Security Shield', sub: 'Encryption Active', icon: '🛡️', delay: 800 },
  { id: 'trade', label: 'Trading Engine', sub: 'Auto-Sniper Ready', icon: '🎯', delay: 1000 },
  { id: 'gem', label: 'Gem Hunter', sub: 'MoonShot + Pump.fun', icon: '💎', delay: 1200 },
  { id: 'hud', label: 'HUD Interface', sub: 'Holographic Display', icon: '🔮', delay: 1400 },
]

const IronManBoot = ({ onFinish }) => {
  const [phase, setPhase] = useState(0) // 0=dark, 1=reactor, 2=scan, 3=systems, 4=ready, 5=fadeout
  const [activeSystems, setActiveSystems] = useState([])
  const [scanLine, setScanLine] = useState(0)
  const [reactorGlow, setReactorGlow] = useState(0)
  const [statusText, setStatusText] = useState('')

  const finish = useCallback(() => {
    setPhase(5)
    setTimeout(() => onFinish?.(), 600)
  }, [onFinish])

  // Main boot sequence timeline
  useEffect(() => {
    // Phase 0: Dark (300ms)
    const t1 = setTimeout(() => {
      setPhase(1)
      setStatusText('ARC REACTOR INITIALIZING...')
    }, 300)

    // Phase 1: Reactor ignition animation (800ms)  
    const t2 = setTimeout(() => {
      setReactorGlow(100)
      setStatusText('NEURAL LINK ESTABLISHED')
    }, 600)

    // Phase 2: Scan lines sweep (start at 1100ms)
    const t3 = setTimeout(() => {
      setPhase(2)
      setStatusText('SCANNING SYSTEMS...')
    }, 1100)

    // Phase 3: Systems come online one by one
    const t4 = setTimeout(() => {
      setPhase(3)
      setStatusText('INITIALIZING SUBSYSTEMS...')
    }, 1800)

    // Activate each system
    BOOT_SYSTEMS.forEach((sys, i) => {
      setTimeout(() => {
        setActiveSystems(prev => [...prev, sys.id])
        setStatusText(`${sys.label} — ONLINE`)
      }, 2000 + sys.delay)
    })

    // Phase 4: All systems ready
    const t5 = setTimeout(() => {
      setPhase(4)
      setStatusText('ALL SYSTEMS NOMINAL')
    }, 3800)

    // Finish
    const t6 = setTimeout(finish, 4800)

    return () => {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3)
      clearTimeout(t4); clearTimeout(t5); clearTimeout(t6)
    }
  }, [finish])

  // Scan line animation
  useEffect(() => {
    if (phase < 2) return
    const iv = setInterval(() => {
      setScanLine(prev => (prev + 2) % 100)
    }, 30)
    return () => clearInterval(iv)
  }, [phase])

  return (
    <div 
      className={`fixed inset-0 z-[99999] flex flex-col items-center justify-center overflow-hidden transition-opacity duration-500 ${phase === 5 ? 'opacity-0' : 'opacity-100'}`}
      style={{ background: '#020408' }}
    >
      {/* Hexagonal grid background */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='52' viewBox='0 0 60 52' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0l30 15v22L30 52 0 37V15z' fill='none' stroke='%2300d4ff' stroke-width='0.5'/%3E%3C/svg%3E")`,
        backgroundSize: '60px 52px',
      }} />

      {/* Scan lines overlay */}
      {phase >= 2 && (
        <div className="absolute inset-0 pointer-events-none">
          <div 
            className="absolute left-0 right-0 h-[2px] transition-all"
            style={{
              top: `${scanLine}%`,
              background: 'linear-gradient(90deg, transparent, rgba(0,212,255,0.4), transparent)',
              boxShadow: '0 0 20px rgba(0,212,255,0.3)',
            }}
          />
        </div>
      )}

      {/* Corner brackets — Iron Man HUD style */}
      <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-cyan-500/40" />
      <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-cyan-500/40" />
      <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-cyan-500/40" />
      <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-cyan-500/40" />

      {/* ARC REACTOR — center piece */}
      <div className="relative mb-8">
        {/* Outer ring */}
        <div 
          className={`w-28 h-28 rounded-full border-2 flex items-center justify-center transition-all duration-1000 ${phase >= 1 ? 'border-cyan-500/60' : 'border-slate-800/30'}`}
          style={{
            boxShadow: phase >= 1 ? `0 0 ${30 + reactorGlow * 0.3}px rgba(0,212,255,${0.1 + reactorGlow * 0.003}), inset 0 0 20px rgba(0,212,255,0.1)` : 'none',
          }}
        >
          {/* Middle ring */}
          <div 
            className={`w-20 h-20 rounded-full border flex items-center justify-center transition-all duration-700 ${phase >= 1 ? 'border-cyan-400/40' : 'border-transparent'}`}
            style={{ 
              animation: phase >= 1 ? 'spin 8s linear infinite' : 'none',
            }}
          >
            {/* Inner core */}
            <div 
              className="w-10 h-10 rounded-full transition-all duration-500"
              style={{
                background: phase >= 1 
                  ? `radial-gradient(circle, ${phase === 4 ? '#22d3ee' : '#0ea5e9'} 0%, rgba(0,212,255,0.4) 40%, transparent 70%)`
                  : 'rgba(30,40,60,0.5)',
                boxShadow: phase >= 1 
                  ? `0 0 40px rgba(0,212,255,${0.3 + reactorGlow * 0.005}), 0 0 80px rgba(0,212,255,0.15)`
                  : 'none',
              }}
            />
          </div>
          {/* Rotating tick marks */}
          {phase >= 1 && [0, 45, 90, 135, 180, 225, 270, 315].map(deg => (
            <div 
              key={deg}
              className="absolute w-[1px] h-3 bg-cyan-500/40"
              style={{ 
                transform: `rotate(${deg}deg) translateY(-48px)`,
                transformOrigin: '50% 62px',
              }}
            />
          ))}
        </div>

        {/* Orbiting dots */}
        {phase >= 2 && (
          <div className="absolute inset-[-16px] rounded-full" style={{ animation: 'spin 4s linear infinite' }}>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-cyan-400 rounded-full" 
              style={{ boxShadow: '0 0 8px #22d3ee' }} />
          </div>
        )}
      </div>

      {/* JARVIS Text */}
      <div className="text-center mb-6">
        <h1 className="text-2xl font-black tracking-[0.4em] mb-1" style={{
          color: phase >= 1 ? '#22d3ee' : '#1e293b',
          textShadow: phase >= 1 ? '0 0 20px rgba(0,212,255,0.5)' : 'none',
          transition: 'all 1s',
        }}>
          J.A.R.V.I.S
        </h1>
        <p className="text-[10px] tracking-[0.3em] text-slate-600 uppercase">
          Just A Rather Very Intelligent System
        </p>
      </div>

      {/* Systems Status Grid */}
      {phase >= 3 && (
        <div className="w-72 grid grid-cols-2 gap-1.5 mb-6">
          {BOOT_SYSTEMS.map(sys => {
            const isActive = activeSystems.includes(sys.id)
            return (
              <div 
                key={sys.id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-lg border transition-all duration-300 ${
                  isActive 
                    ? 'border-cyan-500/30 bg-cyan-950/30' 
                    : 'border-slate-800/30 bg-slate-900/20'
                }`}
                style={{ 
                  opacity: isActive ? 1 : 0.3,
                  transform: isActive ? 'translateX(0)' : 'translateX(-10px)',
                  transition: 'all 0.4s ease-out',
                }}
              >
                <span className="text-sm">{sys.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className={`text-[9px] font-bold ${isActive ? 'text-cyan-400' : 'text-slate-600'}`}>
                    {sys.label}
                  </div>
                  <div className="text-[7px] text-slate-500 truncate">{sys.sub}</div>
                </div>
                <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-400' : 'bg-slate-700'}`}
                  style={{ boxShadow: isActive ? '0 0 6px #34d399' : 'none' }} />
              </div>
            )
          })}
        </div>
      )}

      {/* Status Text */}
      <div className="text-center">
        <p className="text-[11px] font-mono tracking-widest" style={{
          color: phase === 4 ? '#34d399' : '#64748b',
          textShadow: phase === 4 ? '0 0 10px rgba(52,211,153,0.5)' : 'none',
          transition: 'all 0.3s',
        }}>
          {statusText}
        </p>
        
        {/* Progress dots */}
        {phase < 4 && (
          <div className="flex justify-center gap-1 mt-3">
            {[0,1,2,3].map(i => (
              <div 
                key={i}
                className="w-1 h-1 rounded-full bg-cyan-500/50 animate-pulse"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Bottom: Version */}
      <div className="absolute bottom-6 text-center">
        <p className="text-[8px] tracking-widest text-slate-700 uppercase">
          MARK XXVIII • Iron Man Edition • v28.0
        </p>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default IronManBoot
