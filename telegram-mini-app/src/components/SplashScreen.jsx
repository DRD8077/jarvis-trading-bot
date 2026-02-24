/**
 * 🌊 JARVIS Animated Splash Screen
 * ═══════════════════════════════════
 * - Cinematic app launch animation
 * - JARVIS logo pulse + particle effects
 * - Loading progress bar with status text
 * - Auto-dismiss after boot sequence
 */
import React, { useState, useEffect, useRef } from 'react'
import { Bot, Zap, Shield, Wifi } from 'lucide-react'

const BOOT_STEPS = [
  { text: 'Initializing JARVIS...', icon: Bot, duration: 400 },
  { text: 'Loading AI Engine...', icon: Zap, duration: 500 },
  { text: 'Connecting Markets...', icon: Wifi, duration: 400 },
  { text: 'Security Check...', icon: Shield, duration: 300 },
  { text: 'Ready! 🚀', icon: Zap, duration: 200 },
]

const SplashScreen = ({ onFinish }) => {
  const [step, setStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [fadeOut, setFadeOut] = useState(false)
  const canvasRef = useRef(null)

  // Particle animation
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      r: Math.random() * 2 + 0.5,
      alpha: Math.random() * 0.5 + 0.2,
    }))

    let raf
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach(p => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(59, 130, 246, ${p.alpha})`
        ctx.fill()
      })
      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(59,130,246,${0.15 * (1 - dist / 120)})`
            ctx.stroke()
          }
        }
      }
      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(raf)
  }, [])

  // Boot sequence
  useEffect(() => {
    let total = 0
    const totalDuration = BOOT_STEPS.reduce((sum, s) => sum + s.duration, 0)
    
    BOOT_STEPS.forEach((s, i) => {
      total += s.duration
      const elapsed = total
      setTimeout(() => {
        setStep(i)
        setProgress(Math.round((elapsed / totalDuration) * 100))
      }, elapsed)
    })

    setTimeout(() => {
      setProgress(100)
      setFadeOut(true)
      setTimeout(() => onFinish?.(), 500)
    }, totalDuration + 300)
  }, [onFinish])

  const Icon = BOOT_STEPS[step]?.icon || Bot

  return (
    <div className={`fixed inset-0 z-[9999] bg-[#050810] flex flex-col items-center justify-center transition-opacity duration-500 ${fadeOut ? 'opacity-0' : 'opacity-100'}`}>
      <canvas ref={canvasRef} className="absolute inset-0" />
      
      <div className="relative z-10 flex flex-col items-center">
        {/* Logo */}
        <div className="relative mb-8">
          <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 flex items-center justify-center shadow-2xl shadow-blue-500/30 animate-pulse">
            <Bot size={48} className="text-white" />
          </div>
          {/* Orbiting ring */}
          <div className="absolute inset-[-12px] rounded-full border border-blue-500/20 animate-spin" style={{ animationDuration: '8s' }}>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-cyan-400 rounded-full" />
          </div>
          <div className="absolute inset-[-24px] rounded-full border border-purple-500/10 animate-spin" style={{ animationDuration: '12s', animationDirection: 'reverse' }}>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-1.5 h-1.5 bg-purple-400 rounded-full" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-black text-white mb-1 tracking-wider">
          JARVIS <span className="text-blue-400">AI</span>
        </h1>
        <p className="text-slate-500 text-xs mb-10 tracking-widest uppercase">Trading Intelligence</p>

        {/* Boot status */}
        <div className="flex items-center space-x-2 mb-4">
          <Icon size={14} className="text-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs font-mono">{BOOT_STEPS[step]?.text}</span>
        </div>

        {/* Progress bar */}
        <div className="w-56 h-1 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-slate-600 text-[10px] font-mono mt-2">{progress}%</span>
      </div>

      {/* Bottom branding */}
      <div className="absolute bottom-8 text-center">
        <p className="text-slate-700 text-[10px]">v5.0 • Mahadev Tech</p>
      </div>
    </div>
  )
}

export default SplashScreen
