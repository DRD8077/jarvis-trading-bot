/**
 * 🎨 JARVIS Onboarding Screen — Beautiful 3-Slide Intro
 * ═══════════════════════════════════════════════════════════
 * Shows on first app launch before login:
 * Slide 1: Meet JARVIS AI
 * Slide 2: Trade Smarter
 * Slide 3: Voice Control
 * Then → Login Screen
 */
import React, { useState, useRef, useEffect } from 'react'
import { Bot, TrendingUp, Mic, ArrowRight, ChevronRight, Sparkles } from 'lucide-react'

const slides = [
  {
    icon: Bot,
    emoji: '🤖',
    title: 'Meet JARVIS AI',
    subtitle: 'Your Personal AI Trading Assistant',
    description: 'Powered by 25+ AI engines — GPT, Gemini, real-time market data, and deep learning models working together for you.',
    color: 'from-blue-500 via-purple-500 to-pink-500',
    bgGlow: 'bg-blue-600/20',
    features: ['Real-time Market Analysis', 'Hindi & English Support', 'Works 24/7 for You'],
  },
  {
    icon: TrendingUp,
    emoji: '📈',
    title: 'Trade Smarter',
    subtitle: 'AI-Powered Signals & Auto-Trading',
    description: 'Get BUY/SELL signals for Crypto, Indian Stocks, NIFTY Options — with stop-loss, targets & confidence levels.',
    color: 'from-emerald-500 via-teal-500 to-cyan-500',
    bgGlow: 'bg-emerald-600/20',
    features: ['Auto-Trading Bot', 'Copy Top Traders', 'Paper Trading Mode'],
  },
  {
    icon: Mic,
    emoji: '🎙️',
    title: 'Voice Control',
    subtitle: '"Hey JARVIS, NIFTY ka price batao"',
    description: 'Control everything with your voice — in Hindi or English. Works offline too! Just speak and JARVIS obeys.',
    color: 'from-orange-500 via-red-500 to-pink-500',
    bgGlow: 'bg-orange-600/20',
    features: ['Hindi Voice Commands', 'Offline Voice AI', 'Hands-Free Trading'],
  },
]

const OnboardingScreen = ({ onComplete }) => {
  const [current, setCurrent] = useState(0)
  const [direction, setDirection] = useState(0) // -1 left, 1 right
  const [touching, setTouching] = useState(false)
  const touchStartX = useRef(0)
  const touchDeltaX = useRef(0)
  const containerRef = useRef(null)

  const goNext = () => {
    if (current < slides.length - 1) {
      setDirection(1)
      setCurrent(c => c + 1)
    } else {
      localStorage.setItem('jarvis_onboarding_done', 'true')
      onComplete()
    }
  }

  const goPrev = () => {
    if (current > 0) {
      setDirection(-1)
      setCurrent(c => c - 1)
    }
  }

  const skip = () => {
    localStorage.setItem('jarvis_onboarding_done', 'true')
    onComplete()
  }

  // Touch swipe handlers
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX
    touchDeltaX.current = 0
    setTouching(true)
  }

  const handleTouchMove = (e) => {
    touchDeltaX.current = e.touches[0].clientX - touchStartX.current
  }

  const handleTouchEnd = () => {
    setTouching(false)
    if (touchDeltaX.current < -50) goNext()
    else if (touchDeltaX.current > 50) goPrev()
  }

  const slide = slides[current]
  const Icon = slide.icon
  const isLast = current === slides.length - 1

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-[#0a0e1a] flex flex-col items-center justify-between p-6 text-white overflow-hidden relative"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-1/4 left-1/4 w-80 h-80 ${slide.bgGlow} rounded-full blur-[100px] animate-pulse transition-all duration-1000`} />
        <div className={`absolute bottom-1/3 right-1/4 w-60 h-60 ${slide.bgGlow} rounded-full blur-[80px] animate-pulse transition-all duration-1000`} style={{ animationDelay: '1s' }} />
      </div>

      {/* Skip button */}
      <div className="w-full flex justify-end relative z-10 pt-2">
        <button onClick={skip} className="text-slate-500 text-sm px-3 py-1 rounded-lg hover:text-white hover:bg-white/5 transition-all">
          Skip
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 max-w-sm w-full" key={current}>
        {/* Animated Icon */}
        <div className={`w-28 h-28 rounded-[2rem] bg-gradient-to-br ${slide.color} flex items-center justify-center mb-8 shadow-2xl animate-float`}
          style={{ boxShadow: `0 20px 60px rgba(99, 102, 241, 0.3)` }}>
          <span className="text-5xl">{slide.emoji}</span>
        </div>

        {/* Title */}
        <h1 className={`text-3xl font-extrabold bg-gradient-to-r ${slide.color} bg-clip-text text-transparent mb-2 text-center animate-fade-up`}>
          {slide.title}
        </h1>
        <p className="text-slate-400 text-center text-sm mb-6 animate-fade-up" style={{ animationDelay: '0.1s' }}>
          {slide.subtitle}
        </p>

        {/* Description */}
        <p className="text-slate-300 text-center text-[13px] leading-relaxed mb-8 animate-fade-up" style={{ animationDelay: '0.2s' }}>
          {slide.description}
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2 animate-fade-up" style={{ animationDelay: '0.3s' }}>
          {slide.features.map((f, i) => (
            <div key={i} className={`px-3 py-1.5 rounded-full bg-gradient-to-r ${slide.color} bg-opacity-10 border border-white/10 text-xs font-medium text-white/90`}
              style={{ background: 'rgba(255,255,255,0.05)' }}>
              <Sparkles size={10} className="inline mr-1 opacity-60" />
              {f}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom section: dots + button */}
      <div className="w-full max-w-sm relative z-10 pb-4">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-6">
          {slides.map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all duration-500 ${
                i === current ? 'w-8 bg-gradient-to-r ' + slide.color : 'w-2 bg-slate-700'
              }`}
            />
          ))}
        </div>

        {/* CTA Button */}
        <button
          onClick={goNext}
          className={`w-full py-4 rounded-2xl bg-gradient-to-r ${slide.color} text-white font-bold text-lg flex items-center justify-center gap-2 shadow-2xl active:scale-[0.98] transition-transform`}
          style={{ boxShadow: '0 10px 40px rgba(99, 102, 241, 0.3)' }}
        >
          {isLast ? (
            <>
              <Sparkles size={20} />
              <span>Get Started</span>
              <ArrowRight size={20} />
            </>
          ) : (
            <>
              <span>Next</span>
              <ChevronRight size={20} />
            </>
          )}
        </button>

        {/* Swipe hint */}
        <p className="text-slate-600 text-[10px] text-center mt-3">
          ← Swipe to navigate →
        </p>
      </div>
    </div>
  )
}

export default OnboardingScreen
