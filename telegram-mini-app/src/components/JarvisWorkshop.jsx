/**
 * 🔧 JARVIS WORKSHOP — Tony Stark's Lab: Strategy Builder & AI Analysis
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Like Tony's workshop in the Iron Man movies where he builds suits
 * with JARVIS helping analyze, test, and optimize.
 * 
 * This is the user's "lab" where they can:
 * - Build custom trading strategies with AI assistance
 * - Run simulations with voice feedback
 * - View JARVIS's diagnostic reports
 * - See prediction history & accuracy
 * - Manage emergency protocols
 * - Choose AI personality
 * - Review threat assessments
 * - Arc reactor power management
 */

import React, { useState, useEffect } from 'react'
import { Wrench, Beaker, Brain, Shield, Zap, Bot, TrendingUp, AlertTriangle, Battery, ChevronRight, Play, BarChart3, History, Settings, Cpu, Sparkles } from 'lucide-react'

const JarvisWorkshop = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [arcPower, setArcPower] = useState(100)
  const [prediction, setPrediction] = useState(null)
  const [personality, setPersonality] = useState(null)
  const [protocols, setProtocols] = useState(null)
  const [activeProtocol, setActiveProtocol] = useState(null)
  const [predictionHistory, setPredictionHistory] = useState([])
  const [mood, setMood] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load all subsystems
    loadSystems()

    // Announce
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Welcome to the Workshop Sir. Tony Stark ka lab. Yahan aap apni strategies build kar sakte hain, systems manage kar sakte hain.', priority: 'high' }
    }))

    // Listen for power updates
    const onPower = (e) => setArcPower(e.detail?.level || 100)
    window.addEventListener('jarvis-power-update', onPower)
    return () => window.removeEventListener('jarvis-power-update', onPower)
  }, [])

  async function loadSystems() {
    try {
      // Arc Reactor
      const arc = await import('../services/jarvisArcReactor.js').catch(() => null)
      if (arc?.default?.getStatus) setArcPower(arc.default.getStatus().level)

      // Personality
      const pers = await import('../services/jarvisPersonalities.js').catch(() => null)
      if (pers?.default?.getPersonality) setPersonality(pers.default.getPersonality())

      // Protocols
      const proto = await import('../services/jarvisEmergencyProtocols.js').catch(() => null)
      if (proto?.default) {
        setProtocols(proto.default.getProtocols())
        setActiveProtocol(proto.default.getActiveProtocol())
      }

      // Predictions
      const pred = await import('../services/jarvisPredictiveEngine.js').catch(() => null)
      if (pred?.default?.getHistory) setPredictionHistory(pred.default.getHistory())

      // Mood
      const eq = await import('../services/jarvisEQ.js').catch(() => null)
      if (eq?.default?.getCurrentMood) setMood(eq.default.getCurrentMood())
    } catch {}
  }

  async function runPrediction() {
    setLoading(true)
    try {
      const pred = await import('../services/jarvisPredictiveEngine.js')
      const engine = pred.default || pred
      const result = await engine.predictAndSpeak()
      setPrediction(result)
      setPredictionHistory(engine.getHistory())
    } catch { }
    setLoading(false)
  }

  async function activateProtocol(id) {
    try {
      const proto = await import('../services/jarvisEmergencyProtocols.js')
      const engine = proto.default || proto
      engine.activateProtocol(id)
      setActiveProtocol(engine.getActiveProtocol())
    } catch { }
  }

  async function switchAI(id) {
    try {
      const pers = await import('../services/jarvisPersonalities.js')
      const engine = pers.default || pers
      const result = engine.switchPersonality(id)
      setPersonality(result)
    } catch { }
  }

  async function rechargeReactor() {
    try {
      const arc = await import('../services/jarvisArcReactor.js')
      const engine = arc.default || arc
      engine.recharge(30)
      setArcPower(engine.getPowerLevel())
    } catch { }
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Cpu },
    { id: 'predict', label: 'Predict', icon: Brain },
    { id: 'protocols', label: 'Protocols', icon: Shield },
    { id: 'ai', label: 'AI Select', icon: Bot },
    { id: 'reactor', label: 'Reactor', icon: Zap },
  ]

  return (
    <div className="min-h-screen bg-[#0a0e1a] pt-14 pb-24 px-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-xl bg-cyan-500/20 flex items-center justify-center">
          <Wrench size={18} className="text-cyan-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">JARVIS Workshop</h1>
          <p className="text-[10px] text-cyan-500/60 tracking-wider font-mono">TONY STARK'S LAB • MARK XXIX</p>
        </div>
      </div>

      {/* Arc Reactor Status Bar */}
      <div className="mb-4 p-2 rounded-xl bg-slate-900/80 border border-cyan-500/10">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider">ARC REACTOR POWER</span>
          <span className={`text-xs font-bold font-mono ${arcPower > 60 ? 'text-cyan-400' : arcPower > 30 ? 'text-yellow-400' : 'text-red-400'}`}>
            {arcPower}%
          </span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${arcPower > 60 ? 'bg-cyan-400' : arcPower > 30 ? 'bg-yellow-400' : 'bg-red-400'}`}
            style={{ width: `${arcPower}%`, boxShadow: `0 0 8px ${arcPower > 60 ? 'rgba(34,211,238,0.5)' : arcPower > 30 ? 'rgba(245,158,11,0.5)' : 'rgba(239,68,68,0.5)'}` }}
          />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[10px] font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-800/50 text-slate-400 border border-slate-700/20'
            }`}
          >
            <tab.icon size={12} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-3">
          {/* System Status Grid */}
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'AI Personality', value: personality?.name || 'JARVIS', color: personality?.color || '#22d3ee', icon: Bot },
              { label: 'Mood Detection', value: mood?.label || 'Calm', color: mood?.color || '#3b82f6', icon: Sparkles },
              { label: 'Arc Reactor', value: `${arcPower}%`, color: arcPower > 60 ? '#22d3ee' : arcPower > 30 ? '#f59e0b' : '#ef4444', icon: Zap },
              { label: 'Protocol', value: activeProtocol?.codename || 'None', color: activeProtocol?.color || '#64748b', icon: Shield },
            ].map((item, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/20">
                <div className="flex items-center gap-1.5 mb-1">
                  <item.icon size={12} style={{ color: item.color }} />
                  <span className="text-[9px] text-slate-500 font-mono">{item.label}</span>
                </div>
                <span className="text-sm font-bold" style={{ color: item.color }}>{item.value}</span>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="space-y-2">
            <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider">QUICK ACTIONS</span>
            {[
              { label: 'Run Market Prediction', desc: 'AI-powered market forecast', action: runPrediction, icon: Brain, color: '#8b5cf6' },
              { label: 'Open Hologram Display', desc: 'Holographic market projection', action: () => window.dispatchEvent(new CustomEvent('jarvis-hologram-open')), icon: Beaker, color: '#22d3ee' },
              { label: 'Force Brain Scan', desc: 'Emergency market scan', action: () => window.dispatchEvent(new CustomEvent('jarvis-brain-scan')), icon: BarChart3, color: '#22c55e' },
              { label: 'Recharge Arc Reactor', desc: 'Boost power by 30%', action: rechargeReactor, icon: Battery, color: '#f59e0b' },
            ].map((action, i) => (
              <button
                key={i}
                onClick={action.action}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-700/20 text-left hover:border-cyan-500/20 transition-all"
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: action.color + '20' }}>
                  <action.icon size={16} style={{ color: action.color }} />
                </div>
                <div className="flex-1">
                  <span className="text-sm font-medium text-white">{action.label}</span>
                  <span className="text-[10px] text-slate-500 block">{action.desc}</span>
                </div>
                <ChevronRight size={14} className="text-slate-600" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* PREDICTION TAB */}
      {activeTab === 'predict' && (
        <div className="space-y-3">
          <button
            onClick={runPrediction}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-purple-500/20 border border-purple-500/30 text-purple-300 font-medium flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin" />
            ) : (
              <Brain size={16} />
            )}
            {loading ? 'Analyzing market...' : 'Generate AI Prediction'}
          </button>

          {prediction && (
            <div className="p-3 rounded-xl bg-slate-900/80 border border-cyan-500/10 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {prediction.score > 0 ? <TrendingUp className="text-emerald-400" size={18} /> : <AlertTriangle className="text-red-400" size={18} />}
                  <span className={`text-lg font-bold ${prediction.score > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {prediction.direction}
                  </span>
                </div>
                <span className="text-cyan-400 font-bold">{prediction.confidence}%</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${prediction.confidence > 65 ? 'bg-emerald-400' : 'bg-yellow-400'}`} style={{ width: `${prediction.confidence}%` }} />
              </div>
              {prediction.recommendation && (
                <p className="text-[10px] text-slate-400 font-mono">▸ {prediction.recommendation}</p>
              )}
            </div>
          )}

          {/* History */}
          {predictionHistory.length > 0 && (
            <div>
              <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider flex items-center gap-1 mb-2"><History size={10} /> PREDICTION HISTORY</span>
              <div className="space-y-1">
                {predictionHistory.slice(-5).reverse().map((p, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-slate-900/40 border border-slate-800/30">
                    <span className={`text-[10px] font-bold ${p.score > 0 ? 'text-emerald-400' : p.score < 0 ? 'text-red-400' : 'text-yellow-400'}`}>
                      {p.direction}
                    </span>
                    <span className="text-[9px] text-slate-500 font-mono">{p.confidence}% conf</span>
                    <span className="text-[8px] text-slate-600">{new Date(p.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* PROTOCOLS TAB */}
      {activeTab === 'protocols' && protocols && (
        <div className="space-y-2">
          <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider">EMERGENCY PROTOCOLS</span>
          {Object.entries(protocols).map(([id, proto]) => (
            <button
              key={id}
              onClick={() => activateProtocol(id)}
              className={`w-full text-left p-3 rounded-xl border transition-all ${
                activeProtocol?.id === id
                  ? 'bg-opacity-20 border-opacity-40'
                  : 'bg-slate-900/60 border-slate-700/20'
              }`}
              style={activeProtocol?.id === id ? { backgroundColor: proto.color + '20', borderColor: proto.color + '60' } : {}}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{proto.icon}</span>
                <span className="text-sm font-bold text-white">{proto.codename}</span>
                {activeProtocol?.id === id && <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold">ACTIVE</span>}
              </div>
              <p className="text-[10px] text-slate-400">{proto.description}</p>
              {proto.duration > 0 && (
                <span className="text-[8px] text-slate-600 font-mono">Duration: {proto.duration / 60000} min</span>
              )}
            </button>
          ))}

          {activeProtocol && (
            <button
              onClick={async () => {
                const proto = await import('../services/jarvisEmergencyProtocols.js')
                const engine = proto.default || proto
                engine.deactivateProtocol()
                setActiveProtocol(null)
              }}
              className="w-full py-2 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 text-sm font-medium"
            >
              Deactivate Protocol
            </button>
          )}
        </div>
      )}

      {/* AI PERSONALITY TAB */}
      {activeTab === 'ai' && (
        <div className="space-y-2">
          <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider">SELECT AI PERSONALITY</span>
          {['jarvis', 'friday', 'edith', 'karen'].map(id => {
            const p = { jarvis: { name: 'J.A.R.V.I.S', icon: '🤖', color: '#22d3ee', desc: 'Witty, loyal, sarcastic — the original' },
              friday: { name: 'F.R.I.D.A.Y', icon: '🟢', color: '#22c55e', desc: 'Professional, crisp, no-nonsense' },
              edith: { name: 'E.D.I.T.H', icon: '🕶️', color: '#f59e0b', desc: 'Protective, warm, safety-first' },
              karen: { name: 'K.A.R.E.N', icon: '🕷️', color: '#ef4444', desc: 'Friendly, educational, supportive' },
            }[id]
            const isActive = personality?.id === id
            return (
              <button
                key={id}
                onClick={() => switchAI(id)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  isActive ? 'border-opacity-40' : 'bg-slate-900/60 border-slate-700/20'
                }`}
                style={isActive ? { backgroundColor: p.color + '20', borderColor: p.color + '60' } : {}}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-lg">{p.icon}</span>
                  <span className="text-sm font-bold" style={{ color: isActive ? p.color : '#fff' }}>{p.name}</span>
                  {isActive && <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold">ACTIVE</span>}
                </div>
                <p className="text-[10px] text-slate-400 ml-8">{p.desc}</p>
              </button>
            )
          })}
        </div>
      )}

      {/* ARC REACTOR TAB */}
      {activeTab === 'reactor' && (
        <div className="space-y-4">
          {/* Big Arc Reactor Visual */}
          <div className="flex flex-col items-center py-6">
            <div className="relative w-32 h-32">
              {/* Outer ring */}
              <div className="absolute inset-0 rounded-full border-2 animate-spin"
                style={{
                  borderColor: arcPower > 60 ? 'rgba(34,211,238,0.3)' : arcPower > 30 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)',
                  animationDuration: '10s'
                }}
              />
              {/* Inner glow */}
              <div className="absolute inset-4 rounded-full flex items-center justify-center"
                style={{
                  background: `radial-gradient(circle, ${arcPower > 60 ? 'rgba(34,211,238,0.4)' : arcPower > 30 ? 'rgba(245,158,11,0.4)' : 'rgba(239,68,68,0.4)'} 0%, transparent 70%)`,
                  boxShadow: `0 0 40px ${arcPower > 60 ? 'rgba(34,211,238,0.3)' : arcPower > 30 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'}`,
                }}
              >
                <span className="text-3xl font-bold font-mono" style={{ color: arcPower > 60 ? '#22d3ee' : arcPower > 30 ? '#f59e0b' : '#ef4444' }}>
                  {arcPower}%
                </span>
              </div>
              {/* Orbiting dots */}
              {[0, 1, 2, 3].map(i => (
                <div key={i}
                  className="absolute w-2 h-2 rounded-full animate-spin"
                  style={{
                    backgroundColor: arcPower > 60 ? '#22d3ee' : arcPower > 30 ? '#f59e0b' : '#ef4444',
                    top: '50%', left: '50%',
                    transform: `rotate(${i * 90}deg) translateX(60px)`,
                    animationDuration: '4s',
                    boxShadow: `0 0 6px ${arcPower > 60 ? '#22d3ee' : arcPower > 30 ? '#f59e0b' : '#ef4444'}`,
                  }}
                />
              ))}
            </div>
            <span className={`text-sm font-bold mt-3 ${arcPower > 60 ? 'text-cyan-400' : arcPower > 30 ? 'text-yellow-400' : 'text-red-400'}`}>
              {arcPower > 80 ? 'OPTIMAL' : arcPower > 50 ? 'NOMINAL' : arcPower > 25 ? 'LOW POWER' : 'CRITICAL'}
            </span>
          </div>

          {/* Recharge Button */}
          <button
            onClick={rechargeReactor}
            className="w-full py-3 rounded-xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 font-medium flex items-center justify-center gap-2"
          >
            <Zap size={16} /> Recharge Arc Reactor (+30%)
          </button>

          {/* Power Costs Info */}
          <div>
            <span className="text-[9px] text-cyan-500/60 font-mono tracking-wider">POWER CONSUMPTION</span>
            <div className="mt-1 space-y-1">
              {[
                { label: 'Voice Module', cost: 3 },
                { label: 'Gem Scan', cost: 8 },
                { label: 'Brain Scan', cost: 10 },
                { label: 'Prediction', cost: 12 },
                { label: 'Trade Execution', cost: 15 },
                { label: 'Hologram', cost: 20 },
                { label: 'Emergency Protocol', cost: 25 },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between px-2 py-1 rounded-lg bg-slate-900/40">
                  <span className="text-[10px] text-slate-400">{item.label}</span>
                  <span className="text-[10px] font-bold text-cyan-400 font-mono">{item.cost}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default JarvisWorkshop
