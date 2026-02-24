import React, { useState } from 'react'

/**
 * 🤖 Jarvis vs MYRA 2.0 — AI Assistant Comparison
 * Choose the perfect assistant for your needs
 */

const JarvisVsMyra = () => {
  const [selected, setSelected] = useState('jarvis')

  const jarvisFeatures = [
    { icon: '⚡', title: 'Advanced System Automation', desc: 'Open, close, manage apps. Handle files & folders with voice commands.' },
    { icon: '🖥️', title: 'Full Windows Control', desc: 'Minimize, maximize, switch windows. Shutdown, restart, sleep, lock PC.' },
    { icon: '👨‍💻', title: 'Developer-Friendly Commands', desc: 'Custom script execution, code generation, GitHub integration.' },
    { icon: '📊', title: 'Performance Monitoring', desc: 'Real-time CPU, RAM, battery, network status via voice.' },
    { icon: '📱', title: 'Multi-App Management', desc: 'WhatsApp automation, music playback, browser control.' },
    { icon: '⚙️', title: 'Custom Script Execution', desc: 'Run shell commands, Python scripts, Node.js code on demand.' },
    { icon: '💹', title: 'Trading AI Brain', desc: '87 trading engines, 228 API endpoints, real-time market analysis.' },
    { icon: '🔐', title: 'Military Security', desc: 'AES-256 encryption, biometric auth, encrypted vault.' },
    { icon: '🌐', title: 'Multi-Platform', desc: 'EXE + APK + PWA + DMG + AppImage — runs everywhere.' },
    { icon: '🎯', title: 'Voice Input', desc: '4 male + 4 female voices. Hindi + English + Chinese.' },
    { icon: '🔊', title: 'Volume & Brightness', desc: 'Control system volume and screen brightness with voice.' },
    { icon: '🎵', title: 'Music & News', desc: 'Play YouTube/Spotify music and get real-time news via voice.' },
  ]

  const myraFeatures = [
    { icon: '💬', title: 'Human-like Conversations', desc: 'Natural AI companion that understands your emotions and context.' },
    { icon: '🏠', title: 'Daily Life Automation', desc: 'Reminders, schedules, to-do lists, daily briefings.' },
    { icon: '🎭', title: 'Entertainment Control', desc: 'Music, videos, jokes, stories, casual gaming.' },
    { icon: '⏰', title: 'Smart Reminders', desc: 'Context-aware reminders that know when and how to notify.' },
    { icon: '📰', title: 'News & Information', desc: 'Curated news, weather, sports, trending topics.' },
    { icon: '🎨', title: 'Personalized Responses', desc: 'Learns your preferences and adapts personality over time.' },
    { icon: '😊', title: 'Mood Detection', desc: 'Detects your mood and adjusts tone accordingly.' },
    { icon: '🗣️', title: 'Sweet Hindi Voice', desc: 'Natural Hindi voice with emotional expression.' },
    { icon: '📅', title: 'Calendar Management', desc: 'Smart scheduling with conflict detection.' },
    { icon: '🎪', title: 'Casual & Fun', desc: 'Perfect for everyday users who want a helpful friend.' },
  ]

  return (
    <div className="p-3 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="text-center mb-4">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          🤖 Jarvis vs MYRA 2.0
        </h1>
        <p className="text-xs text-slate-400 mt-1">Choose the perfect assistant for your needs</p>
      </div>

      {/* Toggle */}
      <div className="flex bg-slate-800 rounded-xl p-1 mb-4">
        <button
          onClick={() => setSelected('jarvis')}
          className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all ${
            selected === 'jarvis'
              ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
              : 'text-slate-400'
          }`}
        >
          🦾 JARVIS
        </button>
        <button
          onClick={() => setSelected('myra')}
          className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all ${
            selected === 'myra'
              ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white shadow-lg'
              : 'text-slate-400'
          }`}
        >
          💜 MYRA 2.0
        </button>
      </div>

      {/* Description Cards */}
      <div className={`rounded-xl p-3 mb-4 border ${
        selected === 'jarvis'
          ? 'bg-gradient-to-r from-blue-900/40 to-cyan-900/40 border-blue-500/30'
          : 'bg-gradient-to-r from-pink-900/40 to-purple-900/40 border-pink-500/30'
      }`}>
        {selected === 'jarvis' ? (
          <>
            <div className="text-lg font-bold text-blue-400">🦾 JARVIS</div>
            <p className="text-xs text-slate-300 mt-1">
              Designed for <span className="text-blue-400 font-bold">power users</span> who need complete system control and automation. 
              Full trading AI brain with 87 engines, voice commands in Hindi & English, 
              system-level control (volume, brightness, apps, files), WhatsApp automation, 
              and military-grade security.
            </p>
            <div className="flex gap-2 mt-2">
              <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">Pro</span>
              <span className="text-[10px] bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded">Trading</span>
              <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded">Developer</span>
            </div>
          </>
        ) : (
          <>
            <div className="text-lg font-bold text-pink-400">💜 MYRA 2.0</div>
            <p className="text-xs text-slate-300 mt-1">
              Perfect for <span className="text-pink-400 font-bold">everyday users</span> who want a personal AI companion. 
              Human-like conversations, daily life automation, entertainment control, 
              smart reminders, and personalized responses that learn your preferences.
            </p>
            <div className="flex gap-2 mt-2">
              <span className="text-[10px] bg-pink-500/20 text-pink-400 px-2 py-0.5 rounded">Personal</span>
              <span className="text-[10px] bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">Friendly</span>
              <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">Fun</span>
            </div>
          </>
        )}
      </div>

      {/* Feature List */}
      <div className="space-y-2">
        {(selected === 'jarvis' ? jarvisFeatures : myraFeatures).map((f, i) => (
          <div key={i} className={`rounded-xl p-3 border ${
            selected === 'jarvis'
              ? 'bg-slate-800/50 border-slate-700/50 hover:border-blue-500/30'
              : 'bg-slate-800/50 border-slate-700/50 hover:border-pink-500/30'
          } transition-all`}>
            <div className="flex items-center gap-2">
              <span className="text-lg">{f.icon}</span>
              <div>
                <div className={`text-sm font-bold ${selected === 'jarvis' ? 'text-blue-400' : 'text-pink-400'}`}>
                  {f.title}
                </div>
                <div className="text-[11px] text-slate-400">{f.desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison Table */}
      <div className="mt-4 bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
        <div className="text-sm font-bold text-white mb-3 text-center">📊 Quick Comparison</div>
        <div className="space-y-1.5">
          {[
            { feature: 'System Control', jarvis: '✅ Full', myra: '❌ Limited' },
            { feature: 'Trading AI', jarvis: '✅ 87 Engines', myra: '❌ None' },
            { feature: 'Voice Commands', jarvis: '✅ 20+ Hindi/EN', myra: '✅ Basic' },
            { feature: 'Conversations', jarvis: '✅ Business', myra: '✅ Human-like' },
            { feature: 'WhatsApp', jarvis: '✅ Automation', myra: '❌ None' },
            { feature: 'Entertainment', jarvis: '✅ Music/News', myra: '✅ Full' },
            { feature: 'Security', jarvis: '✅ Military AES-256', myra: '✅ Standard' },
            { feature: 'Platforms', jarvis: '✅ EXE+APK+PWA', myra: '⚠️ Web Only' },
            { feature: 'Mood Detection', jarvis: '⚠️ Basic', myra: '✅ Advanced' },
            { feature: 'Personalization', jarvis: '✅ Preferences', myra: '✅ Deep Learning' },
          ].map((row, i) => (
            <div key={i} className="grid grid-cols-3 gap-1 text-[11px]">
              <div className="text-slate-400 py-1">{row.feature}</div>
              <div className="text-center text-blue-400 py-1 bg-blue-500/5 rounded">{row.jarvis}</div>
              <div className="text-center text-pink-400 py-1 bg-pink-500/5 rounded">{row.myra}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Both Active Notice */}
      <div className="mt-4 bg-gradient-to-r from-emerald-900/30 to-blue-900/30 border border-emerald-500/20 rounded-xl p-3 text-center">
        <div className="text-sm font-bold text-emerald-400">🎉 Both Active in JARVIS v7.0!</div>
        <div className="text-[10px] text-slate-400 mt-1">
          JARVIS mode for power users • MYRA mode for personal companion<br/>
          Switch anytime via Settings → AI Mode
        </div>
      </div>
    </div>
  )
}

export default JarvisVsMyra
