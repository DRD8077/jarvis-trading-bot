/**
 * 🔐 JARVIS Login Screen — Gmail / Email / Name Login
 * ═══════════════════════════════════════════════════════
 * Beautiful login screen with Google-style auth
 * Shows on first APK launch, remembers user after login
 */
import React, { useState, useEffect } from 'react'
import { Mail, User, Shield, Sparkles, Bot, ArrowRight, Eye, EyeOff, LogOut, Crown } from 'lucide-react'
import gmailAuth from '../services/gmailAuth'

const LoginScreen = ({ onLogin }) => {
  const [step, setStep] = useState('welcome') // welcome, login, profile
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showEmail, setShowEmail] = useState(false)

  const handleLogin = async () => {
    if (!name.trim() || name.trim().length < 2) {
      setError('Please enter your name (at least 2 characters)')
      return
    }
    setLoading(true)
    setError('')

    try {
      const result = await gmailAuth.loginManual(name.trim(), email.trim())
      if (result.success) {
        onLogin(result.user)
      } else {
        setError(result.error || 'Login failed')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleLogin()
  }

  if (step === 'welcome') {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex flex-col items-center justify-center p-6 text-white">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-purple-600/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/2 w-32 h-32 bg-cyan-600/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative z-10 flex flex-col items-center max-w-sm w-full">
          {/* Logo */}
          <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center mb-6 shadow-2xl shadow-blue-500/30">
            <Bot size={48} className="text-white" />
          </div>

          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
            JARVIS AI
          </h1>
          <p className="text-slate-400 text-center mb-2">
            Your Personal AI Trading Assistant
          </p>
          <div className="flex items-center space-x-2 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 text-xs font-medium">25 AI Engines Active</span>
          </div>

          {/* Features */}
          <div className="grid grid-cols-2 gap-3 w-full mb-8">
            {[
              { icon: '📈', label: 'Live Trading' },
              { icon: '🤖', label: 'AI Signals' },
              { icon: '🇮🇳', label: 'Indian Stocks' },
              { icon: '🔮', label: 'Predictions' },
              { icon: '💎', label: 'Gem Scanner' },
              { icon: '🎙️', label: 'Voice AI' },
            ].map((f, i) => (
              <div key={i} className="bg-slate-800/50 rounded-xl p-3 flex items-center space-x-2 border border-slate-700/30">
                <span className="text-lg">{f.icon}</span>
                <span className="text-xs text-slate-300 font-medium">{f.label}</span>
              </div>
            ))}
          </div>

          {/* Get Started Button */}
          <button
            onClick={() => setStep('login')}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white font-bold text-lg flex items-center justify-center space-x-2 shadow-2xl shadow-purple-500/30 active:scale-[0.98] transition-transform"
          >
            <Sparkles size={20} />
            <span>Get Started</span>
            <ArrowRight size={20} />
          </button>

          <p className="text-slate-600 text-[10px] mt-4 text-center">
            By continuing, you agree to our Terms of Service
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] flex flex-col items-center justify-center p-6 text-white">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/3 left-1/3 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 right-1/3 w-48 h-48 bg-purple-600/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-blue-500/20">
            <Shield size={32} className="text-white" />
          </div>
          <h2 className="text-2xl font-bold mb-1">Sign In</h2>
          <p className="text-slate-400 text-sm">Enter your details to continue</p>
        </div>

        {/* Login Form */}
        <div className="space-y-4">
          {/* Name Input */}
          <div>
            <label className="text-xs text-slate-400 font-medium mb-1.5 block">Your Name *</label>
            <div className="relative">
              <User size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); setError('') }}
                onKeyPress={handleKeyPress}
                placeholder="e.g., Deepak Kumar"
                className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-slate-800/80 border border-slate-700/50 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all"
                autoFocus
              />
            </div>
          </div>

          {/* Email Input (Optional) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs text-slate-400 font-medium">Email / Gmail</label>
              <button onClick={() => setShowEmail(!showEmail)} className="text-[10px] text-blue-400">
                {showEmail ? 'Hide' : 'Optional'}
              </button>
            </div>
            {(showEmail || email) && (
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError('') }}
                  onKeyPress={handleKeyPress}
                  placeholder="your.email@gmail.com"
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-slate-800/80 border border-slate-700/50 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all"
                />
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Sign In Button */}
          <button
            onClick={handleLogin}
            disabled={loading || !name.trim()}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white font-bold flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl shadow-purple-500/20 active:scale-[0.98] transition-transform"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Shield size={18} />
                <span>Sign In to JARVIS</span>
              </>
            )}
          </button>

          {/* Admin Detection Hint */}
          {name.toLowerCase().includes('deepak') && (
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2 flex items-center space-x-2">
              <Crown size={14} className="text-amber-400" />
              <span className="text-amber-300 text-xs">Admin privileges will be granted</span>
            </div>
          )}
        </div>

        {/* Back */}
        <button onClick={() => setStep('welcome')} className="w-full text-center mt-6 text-slate-500 text-xs">
          ← Back to Welcome
        </button>
      </div>
    </div>
  )
}

// ─── User Profile Badge (for header) ─────────────────────────
export const UserBadge = ({ user, onLogout }) => {
  if (!user) return null

  return (
    <div className="flex items-center space-x-2">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
        user.isAdmin ? 'bg-gradient-to-br from-amber-500 to-orange-500' : 'bg-gradient-to-br from-blue-500 to-purple-500'
      }`}>
        {user.avatar || user.name?.[0] || 'J'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-1">
          <span className="text-xs font-medium text-white truncate">{user.name}</span>
          {user.isAdmin && <Crown size={10} className="text-amber-400 shrink-0" />}
        </div>
        {user.email && <span className="text-[10px] text-slate-500 truncate block">{user.email}</span>}
      </div>
    </div>
  )
}

export default LoginScreen
