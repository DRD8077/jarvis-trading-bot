import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  User, Bell, Shield, Globe, Moon, Sun, Volume2, Activity, ChevronRight,
  Zap, Gem, Search, Brain, Bot, TrendingUp, Wallet, Gift, BarChart3, LogOut,
  Fingerprint, Wifi, WifiOff, Download, Mic, Database, Trash2
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import pushNotifications from '../services/pushNotifications'
import biometricAuth from '../services/biometricAuth'
import offlineCache from '../services/offlineCache'
import backgroundAlerts from '../services/backgroundAlerts'

const Settings = () => {
  const { user, hapticFeedback } = useApp()
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

  useEffect(() => {
    setPushEnabled(typeof Notification !== 'undefined' && Notification.permission === 'granted')
    offlineCache.getCacheStats().then(setCacheStats)
    setAlertCount(backgroundAlerts.getActiveAlerts().length)
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
        <p className="text-xs text-slate-500 mt-1">v4.0.0 • 10 Power Features • PWA + APK</p>
        <p className="text-[10px] text-slate-600 mt-1">Push • Biometric • Offline • Charts • Voice • Alerts • Export • OrderBook</p>
        <p className="text-[10px] text-slate-600 mt-1">© 2024-2026 JARVIS AI</p>
      </div>
    </div>
  )
}

export default Settings
