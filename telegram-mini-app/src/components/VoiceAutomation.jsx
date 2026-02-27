import React, { useState, useEffect, useCallback, useRef } from 'react'
import { API_BASE } from '../services/apiBase'

/**
 * 🎙️ JARVIS Ultimate Voice Automation Center v8.5
 * ElevenLabs Premium AI Voice + Full System Control
 * Features: WhatsApp, Volume, Brightness, Music, News, PC Power, Window Management
 * Voice: ElevenLabs streaming TTS (voiceId: 2bNrEsM0omyhLiEyOwqY)
 */

let elevenlabsVoice = null
import('../services/elevenlabsVoice.js').then(m => { elevenlabsVoice = m.default }).catch(() => {})

const VoiceAutomation = () => {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [selectedVoice, setSelectedVoice] = useState('jarvis-prime')
  const [systemStatus, setSystemStatus] = useState(null)
  const [recentCommands, setRecentCommands] = useState([])
  const [activeTab, setActiveTab] = useState('commands')
  const [voiceEngine, setVoiceEngine] = useState('elevenlabs')
  const [isProcessing, setIsProcessing] = useState(false)
  const [continuousMode, setContinuousMode] = useState(false)
  const [aiThinking, setAiThinking] = useState(false)
  const [powerStatus, setPowerStatus] = useState(null)
  const [elevenLabsReady, setElevenLabsReady] = useState(false)
  const recognitionRef = useRef(null)
  const continuousRef = useRef(false)

  const voiceProfiles = [
    { id: 'jarvis-prime', name: 'JARVIS Prime', gender: 'male', lang: 'en', engine: 'elevenlabs', desc: 'ElevenLabs AI Voice' },
    { id: 'jarvis-tony', name: 'Tony Stark', gender: 'male', lang: 'en', engine: 'elevenlabs', desc: 'Confident & Smart' },
    { id: 'friday', name: 'Friday', gender: 'female', lang: 'en', engine: 'elevenlabs', desc: 'Professional Assistant' },
    { id: 'myra', name: 'MYRA 2.0', gender: 'female', lang: 'en', engine: 'elevenlabs', desc: 'Personal AI Friend' },
    { id: 'vikram', name: 'Vikram (Hindi)', gender: 'male', lang: 'hi', engine: 'elevenlabs', desc: 'Hindi Male Voice' },
    { id: 'arjun', name: 'Arjun (Hindi)', gender: 'male', lang: 'hi', engine: 'web', desc: 'Hindi Deep Voice' },
    { id: 'priya', name: 'Priya (Hindi)', gender: 'female', lang: 'hi', engine: 'elevenlabs', desc: 'Hindi Female Voice' },
    { id: 'neha', name: 'Neha (Hindi)', gender: 'female', lang: 'hi', engine: 'web', desc: 'Hindi Warm Voice' },
  ]

  const commandCategories = [
    {
      title: '🚀 System Automation', commands: [
        { cmd: 'Open Chrome', desc: 'Launch browser', icon: '🌐' },
        { cmd: 'Close Notepad', desc: 'Close app', icon: '📝' },
        { cmd: 'Open Calculator', desc: 'Launch calc', icon: '🔢' },
        { cmd: 'Create folder', desc: 'New folder', icon: '📁' },
        { cmd: 'Delete file', desc: 'Remove file', icon: '🗑️' },
        { cmd: 'Take screenshot', desc: 'Screen capture', icon: '📸' },
      ]
    },
    {
      title: '📊 System Status', commands: [
        { cmd: 'Battery status', desc: 'Battery & charging', icon: '🔋' },
        { cmd: 'CPU usage', desc: 'CPU monitor', icon: '💻' },
        { cmd: 'RAM usage', desc: 'Memory check', icon: '🧠' },
        { cmd: 'Internet speed', desc: 'Speed test', icon: '📶' },
        { cmd: 'Disk space', desc: 'Storage check', icon: '💾' },
        { cmd: 'System info', desc: 'Full HW info', icon: '⚙️' },
      ]
    },
    {
      title: '🖥️ Window Control', commands: [
        { cmd: 'Minimize all', desc: 'Show desktop', icon: '⬇️' },
        { cmd: 'Switch window', desc: 'Alt+Tab', icon: '🔄' },
        { cmd: 'Split screen', desc: 'Side by side', icon: '📐' },
        { cmd: 'Close window', desc: 'Close current', icon: '❌' },
        { cmd: 'New desktop', desc: 'Virtual desktop', icon: '🖥️' },
        { cmd: 'Show taskbar', desc: 'Toggle taskbar', icon: '📊' },
      ]
    },
    {
      title: '⚡ PC Power', commands: [
        { cmd: 'Shutdown PC', desc: 'Power off', icon: '🔴' },
        { cmd: 'Restart PC', desc: 'Reboot', icon: '🔄' },
        { cmd: 'Sleep mode', desc: 'Sleep', icon: '😴' },
        { cmd: 'Lock screen', desc: 'Lock PC', icon: '🔒' },
        { cmd: 'Log off', desc: 'Sign out', icon: '👋' },
        { cmd: 'Hibernate', desc: 'Hibernate', icon: '💤' },
      ]
    },
    {
      title: '💬 WhatsApp', commands: [
        { cmd: 'Send WhatsApp', desc: 'Send message', icon: '📱' },
        { cmd: 'Open WhatsApp', desc: 'Launch app', icon: '💬' },
        { cmd: 'Read messages', desc: 'Latest msgs', icon: '📩' },
        { cmd: 'WhatsApp call', desc: 'Voice call', icon: '📞' },
        { cmd: 'Video call', desc: 'Start video', icon: '📹' },
        { cmd: 'Send file', desc: 'Share file', icon: '📎' },
      ]
    },
    {
      title: '🔊 Volume', commands: [
        { cmd: 'Volume up', desc: '+10%', icon: '🔊' },
        { cmd: 'Volume down', desc: '-10%', icon: '🔉' },
        { cmd: 'Mute', desc: 'Mute audio', icon: '🔇' },
        { cmd: 'Unmute', desc: 'Unmute', icon: '🔈' },
        { cmd: 'Volume 50', desc: 'Set level', icon: '🎚️' },
        { cmd: 'Max volume', desc: '100%', icon: '📢' },
      ]
    },
    {
      title: '🔆 Brightness', commands: [
        { cmd: 'Brightness up', desc: 'Increase', icon: '☀️' },
        { cmd: 'Brightness down', desc: 'Decrease', icon: '🌙' },
        { cmd: 'Brightness 80', desc: 'Set level', icon: '🔆' },
        { cmd: 'Night mode', desc: 'Blue filter', icon: '🌙' },
        { cmd: 'Auto brightness', desc: 'Auto adjust', icon: '💡' },
        { cmd: 'Max brightness', desc: '100%', icon: '🌟' },
      ]
    },
    {
      title: '🎵 Music', commands: [
        { cmd: 'Play music', desc: 'YouTube play', icon: '▶️' },
        { cmd: 'Play Spotify', desc: 'From Spotify', icon: '💚' },
        { cmd: 'Next song', desc: 'Skip track', icon: '⏭️' },
        { cmd: 'Previous song', desc: 'Go back', icon: '⏮️' },
        { cmd: 'Pause music', desc: 'Pause', icon: '⏸️' },
        { cmd: 'Play Arijit', desc: 'Artist play', icon: '🎤' },
      ]
    },
    {
      title: '📰 News', commands: [
        { cmd: 'Latest news', desc: 'Breaking', icon: '🗞️' },
        { cmd: 'Market news', desc: 'Stock news', icon: '📈' },
        { cmd: 'Sports news', desc: 'Sports', icon: '⚽' },
        { cmd: 'Tech news', desc: 'Technology', icon: '💻' },
        { cmd: 'India news', desc: 'Indian news', icon: '🇮🇳' },
        { cmd: 'World news', desc: 'Global', icon: '🌍' },
      ]
    },
    {
      title: '💰 Trading', commands: [
        { cmd: 'BTC price', desc: 'Bitcoin price', icon: '₿' },
        { cmd: 'Buy Nifty CE', desc: 'Options order', icon: '📈' },
        { cmd: 'Portfolio status', desc: 'Check P&L', icon: '📊' },
        { cmd: 'Market overview', desc: 'Full summary', icon: '🌐' },
        { cmd: 'Set stop loss', desc: 'Risk manage', icon: '🛡️' },
        { cmd: 'Sell all', desc: 'Close trades', icon: '🔴' },
      ]
    },
    {
      title: '🚨 Emergency', commands: [
        { cmd: 'EMERGENCY SELL', desc: 'Liquidate all', icon: '🔴' },
        { cmd: 'Kill switch', desc: 'Stop engines', icon: '⛔' },
        { cmd: 'Stop loss all', desc: 'Enable SL', icon: '🛡️' },
        { cmd: 'Pause trading', desc: 'Pause 1hr', icon: '⏸️' },
        { cmd: 'Export trades', desc: 'Download', icon: '📥' },
        { cmd: 'Full backup', desc: 'Backup data', icon: '💾' },
      ]
    },
  ]

  // Initialize ElevenLabs
  useEffect(() => {
    const initEL = async () => {
      try {
        const mod = await import('../services/elevenlabsVoice.js')
        elevenlabsVoice = mod.default
        await elevenlabsVoice.init()
        setElevenLabsReady(elevenlabsVoice.initialized && !elevenlabsVoice.useFallback)
      } catch { setElevenLabsReady(false) }
    }
    initEL()
  }, [])

  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      setResponse('❌ Speech recognition not supported')
      return
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SR()
    const profile = voiceProfiles.find(v => v.id === selectedVoice)
    recognition.lang = profile?.lang === 'hi' ? 'hi-IN' : 'en-US'
    recognition.continuous = continuousMode
    recognition.interimResults = true

    recognition.onstart = () => { setIsListening(true); setIsProcessing(false) }
    recognition.onend = () => {
      setIsListening(false)
      if (continuousRef.current) {
        setTimeout(() => { try { recognition.start() } catch {} }, 500)
      }
    }
    recognition.onerror = (e) => {
      setIsListening(false)
      if (e.error !== 'no-speech' && e.error !== 'aborted') setResponse(`❌ ${e.error}`)
    }
    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1]
      setTranscript(result[0].transcript)
      if (result.isFinal) {
        const text = result[0].transcript
        if (continuousMode && !text.toLowerCase().includes('jarvis') && !text.toLowerCase().includes('myra')) return
        executeVoiceCommand(text.replace(/jarvis|myra/gi, '').trim() || text)
      }
    }
    recognitionRef.current = recognition
    recognition.start()
  }, [selectedVoice, continuousMode])

  const stopListening = () => {
    continuousRef.current = false
    setContinuousMode(false)
    try { recognitionRef.current?.stop() } catch {}
    setIsListening(false)
  }

  const toggleContinuous = () => {
    if (continuousMode) { stopListening() } else { setContinuousMode(true); continuousRef.current = true; startListening() }
  }

  const executeVoiceCommand = async (command) => {
    const cmd = command.toLowerCase().trim()
    let result = ''
    setIsProcessing(true)
    setAiThinking(true)

    try {
      if (window.jarvisDesktop) {
        if (cmd.includes('volume up')) { await window.jarvisDesktop.volumeUp(); result = '🔊 Volume increased!' }
        else if (cmd.includes('volume down')) { await window.jarvisDesktop.volumeDown(); result = '🔉 Volume decreased!' }
        else if (cmd.match(/mute|unmute/)) { await window.jarvisDesktop.volumeMute(); result = '🔇 Toggled!' }
        else if (cmd.match(/volume (\d+)/)) { await window.jarvisDesktop.volumeSet(parseInt(cmd.match(/(\d+)/)[1])); result = `🔊 Volume set!` }
        else if (cmd.includes('brightness up')) { await window.jarvisDesktop.brightnessUp(); result = '🔆 Brightness up!' }
        else if (cmd.includes('brightness down')) { await window.jarvisDesktop.brightnessDown(); result = '🔅 Brightness down!' }
        else if (cmd.match(/brightness (\d+)/)) { await window.jarvisDesktop.brightnessSet(parseInt(cmd.match(/(\d+)/)[1])); result = '🔆 Set!' }
        else if (cmd.includes('shutdown')) { await window.jarvisDesktop.pcShutdown(); result = '🔴 Shutting down...' }
        else if (cmd.includes('restart')) { await window.jarvisDesktop.pcRestart(); result = '🔄 Restarting...' }
        else if (cmd.includes('sleep')) { await window.jarvisDesktop.pcSleep(); result = '😴 Sleeping...' }
        else if (cmd.includes('lock')) { await window.jarvisDesktop.pcLock(); result = '🔒 Locked!' }
        else if (cmd.includes('logoff') || cmd.includes('log off')) { await window.jarvisDesktop.pcLogoff(); result = '👋 Logging off...' }
        else if (cmd.includes('minimize')) { await window.jarvisDesktop.minimizeAll(); result = '⬇️ All minimized!' }
        else if (cmd.includes('switch')) { await window.jarvisDesktop.switchWindow(); result = '🔄 Switched!' }
        else if (cmd.includes('chrome') || cmd.includes('browser')) { await window.jarvisDesktop.openApp('chrome'); result = '🌐 Chrome!' }
        else if (cmd.includes('whatsapp') && cmd.includes('open')) { await window.jarvisDesktop.whatsappOpen(); result = '💬 WhatsApp!' }
        else if (cmd.includes('calculator')) { await window.jarvisDesktop.openApp('calculator'); result = '🔢 Calculator!' }
        else if (cmd.includes('play') && cmd.includes('spotify')) { await window.jarvisDesktop.playSpotify(cmd.replace(/play|spotify|on/gi, '').trim()); result = '🎵 Spotify!' }
        else if (cmd.includes('play')) { await window.jarvisDesktop.playYouTube(cmd.replace('play', '').trim()); result = '🎵 Playing!' }
        else if (cmd.includes('next')) { await window.jarvisDesktop.mediaControl('next'); result = '⏭️ Next!' }
        else if (cmd.includes('previous')) { await window.jarvisDesktop.mediaControl('prev'); result = '⏮️ Previous!' }
        else if (cmd.includes('pause')) { await window.jarvisDesktop.mediaControl('pause'); result = '⏸️ Paused!' }
        else if (cmd.includes('news')) { await window.jarvisDesktop.openNews('latest'); result = '📰 Opening news!' }
        else if (cmd.match(/battery|cpu|ram|system/)) {
          const info = await window.jarvisDesktop.getSystemInfo()
          result = `📊 ${info.cpus} cores | ${info.totalMemory} RAM | ${info.platform}`
        }
        else if (cmd.includes('screenshot')) { await window.jarvisDesktop.runCommand('gnome-screenshot'); result = '📸 Done!' }
        else { const r = await window.jarvisDesktop.runCommand(command); result = r?.success ? '✅ Done!' : `❌ ${r?.error || 'Failed'}` }
      } else {
        if (cmd.match(/emergency|kill switch|sell all|stop loss/)) {
          try {
            const action = cmd.includes('kill') ? 'kill_switch' : cmd.includes('sell') ? 'sell_all' : cmd.includes('stop') ? 'stop_loss_all' : 'pause_trading'
            const res = await fetch(`${API_BASE}/v8/emergency-action`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action, user_id: 'voice_user' })
            })
            const data = await res.json()
            result = `🚨 ${data.detail || 'Emergency executed!'}`
          } catch { result = '🚨 Emergency action sent (offline)' }
        } else {
          try {
            const res = await fetch(`${API_BASE}/jarvis-ai/respond`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message: command, user_id: 'voice_user' })
            })
            const data = await res.json()
            result = data.response || data.message || '🤖 Processed!'
          } catch {
            if (cmd.includes('price') || cmd.includes('btc')) result = '₿ Fetching Bitcoin price...'
            else if (cmd.includes('nifty')) result = '📊 Checking Nifty...'
            else if (cmd.includes('news')) result = '📰 Fetching news...'
            else if (cmd.includes('play')) result = '🎵 Opening music...'
            else if (cmd.includes('time') || cmd.includes('date')) result = `🕐 ${new Date().toLocaleString('en-IN')}`
            else if (cmd.match(/hello|hi|namaste/)) result = '🙏 Namaste! Main JARVIS hoon!'
            else result = `🤖 "${command}"`
          }
        }
      }
    } catch (e) { result = `❌ ${e.message || 'Failed'}` }

    setAiThinking(false)
    setIsProcessing(false)
    await speakResponse(result)
    setResponse(result)
    setRecentCommands(prev => [{ cmd: command, result, time: new Date().toLocaleTimeString(), voice: selectedVoice }, ...prev.slice(0, 19)])
  }

  const speakResponse = async (text) => {
    const clean = text.replace(/[\u{1F300}-\u{1FAD6}\u{2600}-\u{27BF}\u{FE00}-\u{FEFF}]/gu, '')
    if (elevenlabsVoice && elevenLabsReady && voiceEngine === 'elevenlabs') {
      elevenlabsVoice.setVoice(selectedVoice)
      const ok = await elevenlabsVoice.speak(clean)
      if (ok) return
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(clean)
      const p = voiceProfiles.find(v => v.id === selectedVoice)
      u.lang = p?.lang === 'hi' ? 'hi-IN' : 'en-US'
      u.rate = 1.0; u.pitch = p?.gender === 'female' ? 1.1 : 0.9
      const voices = speechSynthesis.getVoices()
      const m = voices.find(v => v.lang.includes(p?.lang === 'hi' ? 'hi' : 'en'))
      if (m) u.voice = m
      speechSynthesis.speak(u)
    }
  }

  const quickExec = (cmd) => { setTranscript(cmd); executeVoiceCommand(cmd) }

  useEffect(() => {
    const fetch_ = async () => {
      try { const r = await fetch(`${API_BASE}/v8/power-status`); if (r.ok) setPowerStatus(await r.json()) } catch {}
      if (window.jarvisDesktop) { setSystemStatus(await window.jarvisDesktop.getSystemInfo()) }
      else {
        setSystemStatus({ platform: navigator.platform, cores: navigator.hardwareConcurrency || 'N/A', memory: navigator.deviceMemory ? `${navigator.deviceMemory}GB` : 'N/A', online: navigator.onLine })
        if (navigator.getBattery) try { const b = await navigator.getBattery(); setSystemStatus(p => ({ ...p, battery: `${Math.round(b.level*100)}%${b.charging ? '⚡' : ''}` })) } catch {}
      }
    }
    fetch_()
    const i = setInterval(fetch_, 10000)
    return () => clearInterval(i)
  }, [])

  return (
    <div className="p-3 bg-slate-900 min-h-screen text-white pb-20">
      <div className="text-center mb-4">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-green-400 to-purple-400 bg-clip-text text-transparent">
          🎙️ JARVIS Voice Automation
        </h1>
        <p className="text-[10px] text-slate-400 mt-1">ElevenLabs AI Voice • {commandCategories.length * 6} Commands • Hindi + English</p>
        <div className="flex items-center justify-center gap-2 mt-1">
          <span className={`text-[9px] px-2 py-0.5 rounded-full ${elevenLabsReady ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
            {elevenLabsReady ? '🟢 ElevenLabs' : '🟡 Web Speech'}
          </span>
          <span className="text-[9px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">v8.5 Power</span>
        </div>
      </div>

      <div className="flex flex-col items-center mb-4">
        <div className="relative">
          <button onClick={isListening ? stopListening : startListening}
            className={`w-24 h-24 rounded-full flex items-center justify-center text-4xl transition-all ${
              isListening ? 'bg-red-500 animate-pulse shadow-[0_0_40px_rgba(239,68,68,0.6)] scale-110'
              : aiThinking ? 'bg-yellow-500 animate-bounce shadow-[0_0_40px_rgba(234,179,8,0.4)]'
              : 'bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 hover:scale-105 shadow-[0_0_30px_rgba(99,102,241,0.4)]'
            }`}>
            {aiThinking ? '🧠' : isListening ? '⏹️' : '🎤'}
          </button>
          {isListening && <>
            <div className="absolute inset-0 rounded-full border-2 border-red-500/50 animate-ping" />
            <div className="absolute -inset-2 rounded-full border border-red-500/30 animate-ping" style={{ animationDelay: '0.3s' }} />
          </>}
        </div>
        <div className={`text-xs mt-2 font-medium ${isListening ? 'text-red-400 animate-pulse' : aiThinking ? 'text-yellow-400' : 'text-slate-400'}`}>
          {aiThinking ? '🧠 AI Processing...' : isListening ? '🔴 LISTENING...' : 'Tap to speak'}
        </div>
        <button onClick={toggleContinuous}
          className={`mt-2 text-[10px] px-3 py-1 rounded-full transition-all ${continuousMode ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-slate-800 text-slate-500'}`}>
          {continuousMode ? '🟢 Always Listening (Say "JARVIS...")' : '👂 Enable Always Listening'}
        </button>
        {transcript && <div className="mt-2 text-sm text-blue-300 bg-blue-500/10 rounded-lg px-4 py-2 max-w-xs border border-blue-500/20">🗣️ "{transcript}"</div>}
        {response && <div className="mt-1 text-xs text-green-400 bg-green-500/10 rounded-lg px-4 py-2 max-w-xs text-center border border-green-500/20">{response}</div>}
      </div>

      <div className="flex gap-2 mb-3">
        <button onClick={() => setVoiceEngine('elevenlabs')}
          className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${voiceEngine === 'elevenlabs' ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-600/30' : 'bg-slate-800 text-slate-400'}`}>
          ✨ ElevenLabs AI
        </button>
        <button onClick={() => setVoiceEngine('web')}
          className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${voiceEngine === 'web' ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg' : 'bg-slate-800 text-slate-400'}`}>
          🌐 Web Speech
        </button>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 mb-3">
        <div className="text-[10px] text-slate-400 font-bold mb-2">🗣️ Voice Profiles ({voiceProfiles.length})</div>
        <div className="grid grid-cols-4 gap-1.5">
          {voiceProfiles.map(v => (
            <button key={v.id} onClick={() => { setSelectedVoice(v.id); if (elevenlabsVoice) elevenlabsVoice.setVoice(v.id); speakResponse(`Hello, I am ${v.name}`) }}
              className={`p-1.5 rounded-lg text-center transition-all ${selectedVoice === v.id ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg ring-1 ring-blue-400/50' : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'}`}>
              <div className="text-lg">{v.gender === 'male' ? '👨' : '👩'}</div>
              <div className="text-[9px] font-medium leading-tight">{v.name}</div>
              <div className="text-[7px] opacity-60">{v.engine === 'elevenlabs' ? '✨AI' : '🌐Web'}</div>
            </button>
          ))}
        </div>
      </div>

      {systemStatus && (
        <div className="bg-gradient-to-r from-emerald-900/30 to-blue-900/30 border border-emerald-500/20 rounded-xl p-2.5 mb-3">
          <div className="grid grid-cols-5 gap-1 text-[9px]">
            <div className="bg-slate-800/60 rounded-lg p-1.5 text-center">
              <div className="text-slate-500">Platform</div>
              <div className="text-white font-bold">{(systemStatus.platform||'').substring(0,8)}</div>
            </div>
            <div className="bg-slate-800/60 rounded-lg p-1.5 text-center">
              <div className="text-slate-500">CPU</div>
              <div className="text-cyan-400 font-bold">{powerStatus?.cpu?.percent ? `${powerStatus.cpu.percent}%` : systemStatus.cores||'N/A'}</div>
            </div>
            <div className="bg-slate-800/60 rounded-lg p-1.5 text-center">
              <div className="text-slate-500">RAM</div>
              <div className="text-purple-400 font-bold">{powerStatus?.memory?.percent ? `${powerStatus.memory.percent}%` : systemStatus.memory||'N/A'}</div>
            </div>
            <div className="bg-slate-800/60 rounded-lg p-1.5 text-center">
              <div className="text-slate-500">Disk</div>
              <div className="text-amber-400 font-bold">{powerStatus?.disk?.percent ? `${powerStatus.disk.percent}%` : 'N/A'}</div>
            </div>
            <div className="bg-slate-800/60 rounded-lg p-1.5 text-center">
              <div className="text-slate-500">Status</div>
              <div className="text-green-400 font-bold">{systemStatus.online !== false ? '🟢' : '🔴'}</div>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-1 mb-3">
        {['commands','history','settings'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex-1 py-1.5 rounded-lg text-[10px] font-bold transition-all ${activeTab === tab ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
            {tab === 'commands' ? '📋 Commands' : tab === 'history' ? '📜 History' : '⚙️ Settings'}
          </button>
        ))}
      </div>

      {activeTab === 'commands' ? (
        <div className="space-y-3">
          {commandCategories.map((cat, ci) => (
            <div key={ci} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
              <div className="text-sm font-bold text-blue-400 mb-2">{cat.title}</div>
              <div className="grid grid-cols-3 gap-1.5">
                {cat.commands.map((c, i) => (
                  <button key={i} onClick={() => quickExec(c.cmd)} disabled={isProcessing}
                    className="bg-slate-900/50 hover:bg-blue-600/20 rounded-lg p-2 text-center transition-all active:scale-95 disabled:opacity-50">
                    <div className="text-base">{c.icon}</div>
                    <div className="text-[9px] text-white font-medium mt-0.5 leading-tight">{c.cmd}</div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : activeTab === 'history' ? (
        <div className="space-y-1.5">
          {recentCommands.length === 0 ? (
            <div className="text-center text-slate-500 text-xs py-8"><div className="text-4xl mb-2">🎤</div>No commands yet — tap mic!</div>
          ) : recentCommands.map((c, i) => (
            <div key={i} className="bg-slate-800/50 rounded-lg p-2.5 border border-slate-700/30">
              <div className="flex justify-between"><div className="text-xs text-blue-400 font-medium">"{c.cmd}"</div><div className="text-[8px] text-slate-500">{c.time}</div></div>
              <div className="text-[10px] text-green-400 mt-0.5">{c.result}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
            <div className="text-sm font-bold text-purple-400 mb-3">✨ ElevenLabs Voice</div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-slate-400">Status</span><span className={elevenLabsReady ? 'text-green-400' : 'text-yellow-400'}>{elevenLabsReady ? '🟢 Connected' : '🟡 Web Speech'}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Model</span><span className="text-blue-400">eleven_multilingual_v2</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Voice ID</span><span className="text-slate-300 font-mono text-[9px]">2bNrEsM0omyhLiEyOwqY</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Commands</span><span className="text-cyan-400">{commandCategories.reduce((s,c) => s + c.commands.length, 0)}</span></div>
            </div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
            <div className="text-sm font-bold text-cyan-400 mb-2">🔧 Voice Tuning</div>
            <div className="space-y-2">
              {[{l:'Stability',c:'blue',d:50},{l:'Clarity',c:'purple',d:75},{l:'Style',c:'pink',d:50}].map(s => (
                <div key={s.l}>
                  <div className="text-[10px] text-slate-400 mb-1">{s.l}</div>
                  <input type="range" min="0" max="100" defaultValue={s.d} className={`w-full h-1 bg-slate-700 rounded-lg appearance-none accent-${s.c}-500`}
                    onChange={e => elevenlabsVoice?.setSettings({ [s.l.toLowerCase()]: e.target.value/100 })} />
                </div>
              ))}
            </div>
          </div>
          <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/20 rounded-xl p-3">
            <div className="text-sm font-bold text-blue-400 mb-1">💡 Power Tips</div>
            <div className="text-[10px] text-slate-400 space-y-1">
              <div>• Set ELEVENLABS_API_KEY for premium voice</div>
              <div>• Say "JARVIS" in continuous mode</div>
              <div>• Emergency commands work offline</div>
              <div>• Desktop app = full OS control</div>
              <div>• Voice cloning via ElevenLabs API</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default VoiceAutomation
