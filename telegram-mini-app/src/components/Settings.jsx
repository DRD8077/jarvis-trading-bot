import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  User, Bell, Shield, Globe, Moon, Sun, Volume2, Activity, ChevronRight,
  Zap, Gem, Search, Brain, Bot, TrendingUp, Wallet, Gift, BarChart3, LogOut,
  Fingerprint, Wifi, WifiOff, Download, Mic, Database, Trash2, QrCode,
  Palette, Monitor, Smartphone, Languages, Vibrate, HeartPulse
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import pushNotifications from '../services/pushNotifications'
import biometricAuth from '../services/biometricAuth'
import offlineCache from '../services/offlineCache'
import backgroundAlerts from '../services/backgroundAlerts'
import themeEngine from '../services/themeEngine'
import i18n, { LANGUAGES } from '../services/i18n'
import haptics from '../services/hapticEngine'
import crashAnalytics from '../services/crashAnalytics'

const Settings = () => {
  const { user, hapticFeedback, theme, setTheme, paperTradingMode, togglePaperTrading } = useApp()
  const navigate = useNavigate()
  const [settings, setSettings] = useState({
    notifications: true,
    sound: true,
    darkMode: true,
    language: 'en',
    riskLevel: 'medium'
  })
  const [biometricEnabled, setBiometricEnabled] = useState(biometricAuth.isEnabled())
  const [pushEnabled, setPushEnabled] = useState(false)
  const [cacheStats, setCacheStats] = useState(null)
  const [alertCount, setAlertCount] = useState(0)
  const [currentLang, setCurrentLang] = useState(i18n.getLanguage())
  const [hapticsEnabled, setHapticsEnabled] = useState(haptics.isEnabled())
  const [appHealth, setAppHealth] = useState(null)

  useEffect(() => {
    setPushEnabled(typeof Notification !== 'undefined' && Notification.permission === 'granted')
    offlineCache.getCacheStats().then(setCacheStats)
    setAlertCount(backgroundAlerts.getActiveAlerts().length)
    try { setAppHealth(crashAnalytics.getSummary()) } catch(e) {}
  }, [])

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    hapticFeedback('impact')
  }

  const togglePush = async () => {
    if (!pushEnabled) {
      const ok = await pushNotifications.requestPermission()
      setPushEnabled(ok)
    }
  }

  const toggleBiometric = async () => {
    if (biometricEnabled) {
      biometricAuth.disable()
      setBiometricEnabled(false)
    } else {
      const ok = await biometricAuth.enable()
      setBiometricEnabled(ok)
    }
    hapticFeedback('impact')
  }

  const clearCache = async () => {
    await offlineCache.clearAll()
    setCacheStats(await offlineCache.getCacheStats())
    hapticFeedback('success')
  }

  const allPages = [
    { icon: TrendingUp, label: 'Trading & Signals', path: '/trading', color: 'text-violet-400' },
    { icon: Bot, label: 'AI Chat Assistant', path: '/chat', color: 'text-blue-400' },
    { icon: Wallet, label: 'Wallet & Payments', path: '/wallet', color: 'text-emerald-400' },
    { icon: Zap, label: 'Auto-Trader Bot', path: '/auto-trader', color: 'text-amber-400' },
    { icon: Gem, label: 'Gem Scanner', path: '/gems', color: 'text-pink-400' },
    { icon: Search, label: 'Screener & Futures', path: '/screener', color: 'text-teal-400' },
    { icon: Brain, label: 'Intelligence Hub', path: '/intelligence', color: 'text-indigo-400' },
    { icon: Mic, label: 'Voice Assistant', path: '/voice', color: 'text-rose-400' },
  ]

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Profile */}
      <div className="bg-gradient-to-br from-blue-600/30 to-purple-600/30 border border-blue-500/20 rounded-2xl p-5 mb-5">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-2xl font-bold">
            {(user?.first_name || 'U')[0]}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold">{user?.first_name} {user?.last_name || ''}</h2>
            <p className="text-slate-400 text-sm">@{user?.username || 'user'}</p>
            <p className="text-xs text-slate-500">ID: {user?.id}</p>
          </div>
        </div>
      </div>

      {/* Quick Nav - All Pages */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">All Features</h3>
        <div className="bg-slate-800 rounded-xl border border-slate-700 divide-y divide-slate-700">
          {allPages.map((p, i) => {
            const Icon = p.icon
            return (
              <button key={i} onClick={() => navigate(p.path)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/50 transition-colors">
                <div className="flex items-center space-x-3">
                  <Icon size={18} className={p.color} />
                  <span className="text-sm font-medium">{p.label}</span>
                </div>
                <ChevronRight size={16} className="text-slate-500" />
              </button>
            )
          })}
        </div>
      </div>

      {/* Settings */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Preferences</h3>
        <div className="space-y-2">
          {/* Notifications */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bell size={18} className="text-slate-400" />
              <div>
                <p className="text-sm font-medium">Trade Notifications</p>
                <p className="text-xs text-slate-500">Signals & alerts</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={settings.notifications}
                onChange={e => updateSetting('notifications', e.target.checked)} />
              <div className="w-11 h-6 bg-slate-700 peer-checked:bg-blue-600 rounded-full
                after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          {/* Sound */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Volume2 size={18} className="text-slate-400" />
              <div>
                <p className="text-sm font-medium">Sound Effects</p>
                <p className="text-xs text-slate-500">Haptic & audio feedback</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={settings.sound}
                onChange={e => updateSetting('sound', e.target.checked)} />
              <div className="w-11 h-6 bg-slate-700 peer-checked:bg-blue-600 rounded-full
                after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          {/* Risk Level */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <Shield size={18} className="text-slate-400" />
              <div>
                <p className="text-sm font-medium">Risk Level</p>
                <p className="text-xs text-slate-500">Auto-trader risk tolerance</p>
              </div>
            </div>
            <div className="flex space-x-2">
              {[
                { v: 'low', l: 'Conservative', c: 'emerald' },
                { v: 'medium', l: 'Balanced', c: 'amber' },
                { v: 'high', l: 'Aggressive', c: 'red' }
              ].map(r => (
                <button key={r.v} onClick={() => updateSetting('riskLevel', r.v)}
                  className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                    settings.riskLevel === r.v
                      ? `bg-${r.c}-600 text-white`
                      : 'bg-slate-700 text-slate-400'
                  }`}>{r.l}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 🎨 Appearance */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Appearance</h3>
        <div className="space-y-2">
          {/* Theme Toggle */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <Palette size={18} className="text-purple-400" />
              <div>
                <p className="text-sm font-medium">Theme</p>
                <p className="text-xs text-slate-500">Dark, AMOLED Black, or Light</p>
              </div>
            </div>
            <div className="flex space-x-2">
              {[
                { id: 'dark', label: '🌙 Dark', color: 'blue' },
                { id: 'amoled', label: '⬛ AMOLED', color: 'purple' },
                { id: 'light', label: '☀️ Light', color: 'amber' }
              ].map(t => (
                <button key={t.id} onClick={() => { setTheme(t.id); hapticFeedback('impact') }}
                  className={`flex-1 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    theme === t.id ? `bg-${t.color}-600 text-white ring-2 ring-${t.color}-400/50` : 'bg-slate-700 text-slate-400'
                  }`}>{t.label}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 🌐 Language & Haptics */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Language & Feedback</h3>
        <div className="space-y-2">
          {/* Language Selector */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <Languages size={18} className="text-cyan-400" />
              <div>
                <p className="text-sm font-medium">Language / भाषा</p>
                <p className="text-xs text-slate-500">App interface language</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map(lang => (
                <button key={lang.code} onClick={() => { i18n.setLanguage(lang.code); setCurrentLang(lang.code); hapticFeedback('impact') }}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    currentLang === lang.code ? 'bg-cyan-600 text-white ring-2 ring-cyan-400/50' : 'bg-slate-700 text-slate-400'
                  }`}>{lang.flag} {lang.nativeName}</button>
              ))}
            </div>
          </div>

          {/* Haptic Feedback */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Vibrate size={18} className="text-pink-400" />
              <div>
                <p className="text-sm font-medium">Haptic Feedback</p>
                <p className="text-xs text-slate-500">{hapticsEnabled ? 'Vibration patterns active' : 'Vibrations disabled'}</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={hapticsEnabled}
                onChange={e => { haptics.setEnabled(e.target.checked); setHapticsEnabled(e.target.checked); haptics.trigger('success') }} />
              <div className="w-11 h-6 bg-slate-700 peer-checked:bg-pink-600 rounded-full
                after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          {/* App Health Score */}
          {appHealth && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center space-x-3 mb-3">
                <HeartPulse size={18} className={appHealth.healthScore >= 80 ? 'text-emerald-400' : appHealth.healthScore >= 50 ? 'text-amber-400' : 'text-red-400'} />
                <div>
                  <p className="text-sm font-medium">App Health Score</p>
                  <p className="text-xs text-slate-500">Performance & stability diagnostics</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${
                    appHealth.healthScore >= 80 ? 'bg-emerald-500' : appHealth.healthScore >= 50 ? 'bg-amber-500' : 'bg-red-500'
                  }`} style={{ width: `${appHealth.healthScore}%` }} />
                </div>
                <span className={`text-sm font-bold ${
                  appHealth.healthScore >= 80 ? 'text-emerald-400' : appHealth.healthScore >= 50 ? 'text-amber-400' : 'text-red-400'
                }`}>{appHealth.healthScore}/100</span>
              </div>
              <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400">FPS</p>
                  <p className="text-white font-bold">{appHealth.fps || '--'}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400">Errors</p>
                  <p className="text-white font-bold">{appHealth.errorCount || 0}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400">Memory</p>
                  <p className="text-white font-bold">{appHealth.memoryMB ? `${appHealth.memoryMB}MB` : '--'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 📝 Trading Mode */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Trading Mode</h3>
        <div className="space-y-2">
          {/* Paper Trading Toggle */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Monitor size={18} className="text-amber-400" />
              <div>
                <p className="text-sm font-medium">Paper Trading Mode</p>
                <p className="text-xs text-slate-500">{paperTradingMode ? 'Practice mode — fake ₹10L' : 'Using real trades'}</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={paperTradingMode} onChange={togglePaperTrading} />
              <div className="w-11 h-6 bg-slate-700 peer-checked:bg-amber-600 rounded-full
                after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          {/* Quick links */}
          <button onClick={() => navigate('/paper-trading')}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between hover:bg-slate-700/50 transition-colors">
            <div className="flex items-center space-x-3">
              <Smartphone size={18} className="text-emerald-400" />
              <span className="text-sm font-medium">Paper Trading Desk</span>
            </div>
            <ChevronRight size={16} className="text-slate-500" />
          </button>
          <button onClick={() => navigate('/pnl-journal')}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between hover:bg-slate-700/50 transition-colors">
            <div className="flex items-center space-x-3">
              <BarChart3 size={18} className="text-blue-400" />
              <span className="text-sm font-medium">P&L Journal</span>
            </div>
            <ChevronRight size={16} className="text-slate-500" />
          </button>
        </div>
      </div>

      {/* 🔐 Security & Notifications */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Security & Notifications</h3>
        <div className="space-y-2">
          {/* Push Notifications */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bell size={18} className="text-blue-400" />
              <div>
                <p className="text-sm font-medium">Push Notifications</p>
                <p className="text-xs text-slate-500">{pushEnabled ? 'Enabled — price alerts active' : 'Tap to enable'}</p>
              </div>
            </div>
            <button onClick={togglePush}
              className={`px-3 py-1 rounded-lg text-xs font-medium ${pushEnabled ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white'}`}>
              {pushEnabled ? '✓ ON' : 'Enable'}
            </button>
          </div>

          {/* Biometric Auth */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Fingerprint size={18} className="text-purple-400" />
              <div>
                <p className="text-sm font-medium">Biometric Lock</p>
                <p className="text-xs text-slate-500">{biometricEnabled ? 'Fingerprint/Face ID active' : 'Protect with biometrics'}</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={biometricEnabled} onChange={toggleBiometric} />
              <div className="w-11 h-6 bg-slate-700 peer-checked:bg-purple-600 rounded-full
                after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          {/* Background Alerts */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Zap size={18} className="text-amber-400" />
              <div>
                <p className="text-sm font-medium">Background Price Alerts</p>
                <p className="text-xs text-slate-500">{alertCount} active alert{alertCount !== 1 ? 's' : ''}</p>
              </div>
            </div>
            <span className="text-xs text-emerald-400 font-medium">Running</span>
          </div>
        </div>
      </div>

      {/* 📦 Data & Storage */}
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Data & Storage</h3>
        <div className="space-y-2">
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <Database size={18} className="text-cyan-400" />
                <div>
                  <p className="text-sm font-medium">Offline Cache</p>
                  <p className="text-xs text-slate-500">
                    {cacheStats ? `${cacheStats.entries} items • ${cacheStats.totalSizeKB || 0} KB` : 'Calculating...'}
                  </p>
                </div>
              </div>
              <button onClick={clearCache} className="p-2 rounded-lg bg-slate-700 hover:bg-red-600/30 transition-colors">
                <Trash2 size={14} className="text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Backend Status */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5">
        <h3 className="text-sm font-medium mb-2 flex items-center space-x-2">
          <Activity size={16} className="text-emerald-400" />
          <span>System Status</span>
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full" />
            <span>27 Backend Modules</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full" />
            <span>32 API Endpoints</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full" />
            <span>Multi-AI (Groq+GPT)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full" />
            <span>ML Pipeline Active</span>
          </div>
        </div>
      </div>

      {/* App Info */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-800/50 rounded-xl p-4 border border-slate-700 text-center">
        <p className="gradient-text text-lg font-bold">JARVIS AI Trading Platform</p>
        <p className="text-xs text-slate-500 mt-1">v6.0.0 IRON MAN • 35+ Features • Zero-Dependency AI • PWA + APK</p>
        <p className="text-[10px] text-slate-600 mt-1">Push • Biometric • Offline AI • TradingView • Voice • Paper Trading • P&L Journal</p>
        <p className="text-[10px] text-slate-600 mt-1">Watchlist • Smart Alerts • Depth Chart • Tax Calculator • Deep Links</p>
        <p className="text-[10px] text-slate-600 mt-1">Multi-Language • Haptics • Crash Analytics • Splash Screen • Swipe Nav</p>
        <p className="text-[10px] text-slate-600 mt-1">© 2024-2026 JARVIS AI • Jai Mahadev! 🙏</p>
      </div>
    </div>
  )
}

export default Settings
