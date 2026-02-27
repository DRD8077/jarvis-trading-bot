/**
 * 🌀 JARVIS HOLOGRAPHIC DISPLAY — Iron Man 3D Projection UI
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like Tony Stark's holographic projections in his workshop/suit.
 * A fullscreen animated overlay with:
 * - Rotating 3D-like radar sweep
 * - Floating data particles
 * - Animated grid lines
 * - Real-time market data projection
 * - Prediction confidence arcs
 * - Can be triggered via gesture or voice command
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { X, Activity, TrendingUp, TrendingDown, Shield, AlertTriangle, Zap } from 'lucide-react'

const JarvisHologram = ({ onClose }) => {
  const canvasRef = useRef(null)
  const animFrameRef = useRef(null)
  const [marketData, setMarketData] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [phase, setPhase] = useState(0) // 0=loading, 1=scanning, 2=showing data
  const [particles, setParticles] = useState([])

  // Fetch market data
  useEffect(() => {
    async function loadData() {
      try {
        const [priceRes, globalRes] = await Promise.all([
          fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,cardano,dogecoin&vs_currencies=usd&include_24hr_change=true').then(r => r.json()),
          fetch('https://api.coingecko.com/api/v3/global').then(r => r.json()),
        ])
        setMarketData({ prices: priceRes, global: globalRes?.data })
        setPhase(1)
        setTimeout(() => setPhase(2), 2000) // Scanning animation

        // Try prediction engine
        import('../services/jarvisPredictiveEngine.js').then(m => {
          const eng = m.default || m
          if (eng?.generatePrediction) {
            eng.generatePrediction().then(p => setPrediction(p))
          }
        }).catch(() => {})
      } catch {
        setPhase(2)
      }
    }
    loadData()

    // Announce
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: 'Holographic display activated Sir. Market data project kar rahi hoon.', priority: 'high' }
    }))

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    }
  }, [])

  // Canvas animation — radar sweep + particles
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width = window.innerWidth
    const H = canvas.height = window.innerHeight
    let angle = 0
    let particleList = Array.from({ length: 60 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 0.5,
      alpha: Math.random() * 0.5 + 0.2,
    }))

    function draw() {
      ctx.clearRect(0, 0, W, H)

      // Draw grid
      ctx.strokeStyle = 'rgba(34, 211, 238, 0.06)'
      ctx.lineWidth = 0.5
      for (let x = 0; x < W; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke()
      }
      for (let y = 0; y < H; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke()
      }

      // Draw radar sweep from center
      const cx = W / 2, cy = H * 0.4
      angle += 0.02

      // Radar circles
      for (let r = 30; r <= 150; r += 40) {
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(34, 211, 238, ${0.15 - r * 0.0005})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }

      // Radar sweep line
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(cx + Math.cos(angle) * 150, cy + Math.sin(angle) * 150)
      ctx.strokeStyle = 'rgba(34, 211, 238, 0.6)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Sweep gradient trail
      const gradient = ctx.createConicalGradient
        ? null // Not supported everywhere
        : null
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.arc(cx, cy, 150, angle - 0.5, angle, false)
      ctx.closePath()
      ctx.fillStyle = 'rgba(34, 211, 238, 0.05)'
      ctx.fill()

      // Draw floating particles
      particleList.forEach(p => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0) p.x = W
        if (p.x > W) p.x = 0
        if (p.y < 0) p.y = H
        if (p.y > H) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(34, 211, 238, ${p.alpha})`
        ctx.fill()
      })

      // Connection lines between nearby particles
      for (let i = 0; i < particleList.length; i++) {
        for (let j = i + 1; j < particleList.length; j++) {
          const dx = particleList[i].x - particleList[j].x
          const dy = particleList[i].y - particleList[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 100) {
            ctx.beginPath()
            ctx.moveTo(particleList[i].x, particleList[i].y)
            ctx.lineTo(particleList[j].x, particleList[j].y)
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.1 * (1 - dist / 100)})`
            ctx.lineWidth = 0.3
            ctx.stroke()
          }
        }
      }

      // HUD bracket corners
      const bSize = 20, bPad = 20
      ctx.strokeStyle = 'rgba(34, 211, 238, 0.3)'
      ctx.lineWidth = 1.5
      // Top-left
      ctx.beginPath(); ctx.moveTo(bPad, bPad + bSize); ctx.lineTo(bPad, bPad); ctx.lineTo(bPad + bSize, bPad); ctx.stroke()
      // Top-right
      ctx.beginPath(); ctx.moveTo(W - bPad - bSize, bPad); ctx.lineTo(W - bPad, bPad); ctx.lineTo(W - bPad, bPad + bSize); ctx.stroke()
      // Bottom-left
      ctx.beginPath(); ctx.moveTo(bPad, H - bPad - bSize); ctx.lineTo(bPad, H - bPad); ctx.lineTo(bPad + bSize, H - bPad); ctx.stroke()
      // Bottom-right
      ctx.beginPath(); ctx.moveTo(W - bPad - bSize, H - bPad); ctx.lineTo(W - bPad, H - bPad); ctx.lineTo(W - bPad, H - bPad - bSize); ctx.stroke()

      animFrameRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current) }
  }, [])

  const coins = marketData?.prices ? [
    { name: 'BTC', price: marketData.prices.bitcoin?.usd, change: marketData.prices.bitcoin?.usd_24h_change },
    { name: 'ETH', price: marketData.prices.ethereum?.usd, change: marketData.prices.ethereum?.usd_24h_change },
    { name: 'SOL', price: marketData.prices.solana?.usd, change: marketData.prices.solana?.usd_24h_change },
    { name: 'ADA', price: marketData.prices.cardano?.usd, change: marketData.prices.cardano?.usd_24h_change },
    { name: 'DOGE', price: marketData.prices.dogecoin?.usd, change: marketData.prices.dogecoin?.usd_24h_change },
  ] : []

  const globalMcap = marketData?.global?.total_market_cap?.usd
  const globalChange = marketData?.global?.market_cap_change_percentage_24h_usd

  return (
    <div className="fixed inset-0 z-[99999] bg-black/95 flex flex-col items-center overflow-hidden" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      {/* Canvas background */}
      <canvas ref={canvasRef} className="absolute inset-0" />

      {/* Close button */}
      <button onClick={onClose} className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
        <X size={16} />
      </button>

      {/* Title */}
      <div className="relative z-10 mt-8 text-center">
        <div className="text-[10px] tracking-[0.3em] text-cyan-500/60 font-mono">JARVIS HOLOGRAPHIC DISPLAY</div>
        <div className="text-2xl font-bold text-cyan-400 tracking-widest mt-1" style={{ textShadow: '0 0 20px rgba(34,211,238,0.5)' }}>
          MARKET PROJECTION
        </div>
      </div>

      {/* Phase 0-1: Scanning animation */}
      {phase < 2 && (
        <div className="relative z-10 flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto border border-cyan-500/30 rounded-full flex items-center justify-center animate-pulse">
              <Activity size={32} className="text-cyan-400 animate-spin" style={{ animationDuration: '3s' }} />
            </div>
            <div className="text-cyan-400 text-sm mt-4 font-mono animate-pulse">
              {phase === 0 ? 'Initializing holographic matrix...' : 'Scanning market vectors...'}
            </div>
          </div>
        </div>
      )}

      {/* Phase 2: Data display */}
      {phase === 2 && (
        <div className="relative z-10 flex-1 w-full px-4 mt-6 overflow-y-auto pb-20">
          {/* Global Market Cap */}
          {globalMcap && (
            <div className="text-center mb-4">
              <div className="text-[9px] text-cyan-500/60 tracking-widest font-mono">GLOBAL MARKET CAP</div>
              <div className="text-xl font-bold text-white font-mono">
                ${(globalMcap / 1e12).toFixed(2)}T
              </div>
              <div className={`text-xs font-mono ${globalChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {globalChange >= 0 ? '▲' : '▼'} {Math.abs(globalChange || 0).toFixed(2)}% (24h)
              </div>
            </div>
          )}

          {/* Coin Cards — holographic style */}
          <div className="space-y-2 mb-4">
            {coins.map((coin, i) => (
              <div key={coin.name}
                className="flex items-center justify-between px-4 py-2.5 rounded-xl border border-cyan-500/10 bg-cyan-950/20 backdrop-blur-sm"
                style={{ animationDelay: `${i * 0.1}s`, animation: 'fadeIn 0.5s forwards', opacity: 0 }}
              >
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 6px rgba(34,211,238,0.6)' }} />
                  <span className="text-cyan-300 font-bold text-sm font-mono">{coin.name}</span>
                </div>
                <span className="text-white font-mono text-sm">
                  ${coin.price?.toLocaleString(undefined, { maximumFractionDigits: coin.price < 1 ? 4 : 2 }) || '—'}
                </span>
                <span className={`text-xs font-mono ${(coin.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(coin.change || 0) >= 0 ? '+' : ''}{(coin.change || 0).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>

          {/* Prediction Display */}
          {prediction && (
            <div className="mt-4 p-3 rounded-xl border border-cyan-500/15 bg-cyan-950/30">
              <div className="text-[9px] tracking-widest text-cyan-500/60 font-mono mb-2">AI PREDICTION ENGINE</div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {prediction.score > 0 ? <TrendingUp className="text-emerald-400" size={18} /> : <TrendingDown className="text-red-400" size={18} />}
                  <span className={`text-lg font-bold ${prediction.score > 0 ? 'text-emerald-400' : prediction.score < 0 ? 'text-red-400' : 'text-yellow-400'}`}>
                    {prediction.direction}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 font-mono">Confidence</div>
                  <div className="text-sm font-bold text-cyan-400">{prediction.confidence}%</div>
                </div>
              </div>
              {/* Confidence bar */}
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${prediction.confidence > 65 ? 'bg-emerald-400' : prediction.confidence > 40 ? 'bg-yellow-400' : 'bg-red-400'}`}
                  style={{ width: `${prediction.confidence}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                Volatility: <span className={prediction.volatility === 'extreme' ? 'text-red-400' : prediction.volatility === 'high' ? 'text-orange-400' : 'text-emerald-400'}>
                  {prediction.volatility?.toUpperCase() || 'N/A'}
                </span>
                {' • '}Risk: <span className={prediction.riskLevel === 'HIGH' ? 'text-red-400' : prediction.riskLevel === 'MODERATE' ? 'text-yellow-400' : 'text-emerald-400'}>
                  {prediction.riskLevel || 'N/A'}
                </span>
              </div>
              {prediction.recommendation && (
                <div className="mt-2 text-[10px] text-cyan-300/80 font-mono">
                  ▸ {prediction.recommendation}
                </div>
              )}
            </div>
          )}

          {/* Threat Assessment */}
          <div className="mt-3 flex items-center justify-between px-3 py-2 rounded-xl border border-cyan-500/10 bg-cyan-950/15">
            <div className="flex items-center gap-1.5">
              <Shield size={14} className="text-emerald-400" />
              <span className="text-[10px] text-slate-400 font-mono">THREAT LEVEL</span>
            </div>
            <span className="text-[10px] font-bold text-emerald-400 font-mono">
              {prediction?.riskLevel === 'HIGH' ? '🔴 HIGH' : prediction?.riskLevel === 'MODERATE' ? '🟡 MODERATE' : '🟢 LOW'}
            </span>
          </div>

          {/* Timestamp */}
          <div className="mt-4 text-center text-[8px] text-cyan-500/40 font-mono">
            PROJECTED AT {new Date().toLocaleTimeString()} • TAP ANYWHERE TO CLOSE
          </div>
        </div>
      )}

      {/* Fadeout animation styles */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

export default JarvisHologram
