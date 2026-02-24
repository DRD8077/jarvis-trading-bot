import React, { useState, useEffect, useCallback } from 'react'
import { API_BASE } from '../services/apiBase'

/**
 * 🎙️ JARVIS Voice Automation Center
 * Full system automation via voice commands
 * Features: WhatsApp, Volume, Brightness, Music, News, PC Power, Window Management
 */

const VoiceAutomation = () => {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [selectedVoice, setSelectedVoice] = useState('male-1')
  const [systemStatus, setSystemStatus] = useState(null)
  const [recentCommands, setRecentCommands] = useState([])
  const [activeTab, setActiveTab] = useState('commands')

  const voiceProfiles = [
    { id: 'male-1', name: 'JARVIS (Tony)', gender: 'male', lang: 'en' },
    { id: 'male-2', name: 'Friday', gender: 'male', lang: 'en' },
    { id: 'male-3', name: 'Vikram (Hindi)', gender: 'male', lang: 'hi' },
    { id: 'male-4', name: 'Arjun (Hindi)', gender: 'male', lang: 'hi' },
    { id: 'female-1', name: 'MYRA', gender: 'female', lang: 'en' },
    { id: 'female-2', name: 'Alexa', gender: 'female', lang: 'en' },
    { id: 'female-3', name: 'Priya (Hindi)', gender: 'female', lang: 'hi' },
    { id: 'female-4', name: 'Neha (Hindi)', gender: 'female', lang: 'hi' },
  ]

  const commandCategories = [
    {
      title: '🚀 Full System Automation',
      commands: [
        { cmd: 'Open Chrome', desc: 'Launch Google Chrome browser' },
        { cmd: 'Close Notepad', desc: 'Close Notepad application' },
        { cmd: 'Open Calculator', desc: 'Launch system calculator' },
        { cmd: 'Create folder Projects', desc: 'Create new folder on desktop' },
        { cmd: 'Delete file temp.txt', desc: 'Delete a specific file' },
        { cmd: 'Move file to Documents', desc: 'Move files between folders' },
      ]
    },
    {
      title: '📊 System Status Check',
      commands: [
        { cmd: 'Battery status', desc: 'Check current battery level & charging' },
        { cmd: 'CPU usage', desc: 'Monitor real-time CPU utilization' },
        { cmd: 'RAM usage', desc: 'Check memory usage and available RAM' },
        { cmd: 'Internet status', desc: 'Check connection speed and status' },
        { cmd: 'Disk space', desc: 'Check available storage space' },
        { cmd: 'System info', desc: 'Full system hardware information' },
      ]
    },
    {
      title: '🖥️ Windows Management',
      commands: [
        { cmd: 'Minimize window', desc: 'Minimize current active window' },
        { cmd: 'Maximize window', desc: 'Maximize current window to full screen' },
        { cmd: 'Switch window', desc: 'Switch between open windows (Alt+Tab)' },
        { cmd: 'Close window', desc: 'Close the current active window' },
        { cmd: 'Split screen', desc: 'Arrange windows side by side' },
        { cmd: 'Show desktop', desc: 'Minimize all windows to show desktop' },
      ]
    },
    {
      title: '⚡ PC Power Control',
      commands: [
        { cmd: 'Shutdown PC', desc: 'Shutdown computer immediately' },
        { cmd: 'Restart PC', desc: 'Restart the computer' },
        { cmd: 'Sleep mode', desc: 'Put computer to sleep' },
        { cmd: 'Lock PC', desc: 'Lock the screen instantly' },
        { cmd: 'Log off', desc: 'Sign out of current user' },
        { cmd: 'Hibernate', desc: 'Hibernate the system' },
      ]
    },
    {
      title: '💬 WhatsApp Automation',
      commands: [
        { cmd: 'Send WhatsApp to Mom', desc: 'Send message to contact via WhatsApp' },
        { cmd: 'Send file on WhatsApp', desc: 'Share files through WhatsApp' },
        { cmd: 'Open WhatsApp', desc: 'Launch WhatsApp application' },
        { cmd: 'Read last WhatsApp', desc: 'Read latest unread messages' },
        { cmd: 'WhatsApp call Rohit', desc: 'Make WhatsApp voice call' },
        { cmd: 'WhatsApp video call', desc: 'Start WhatsApp video call' },
      ]
    },
    {
      title: '🔊 Volume Control',
      commands: [
        { cmd: 'Volume up', desc: 'Increase system volume by 10%' },
        { cmd: 'Volume down', desc: 'Decrease system volume by 10%' },
        { cmd: 'Mute', desc: 'Mute the system audio' },
        { cmd: 'Unmute', desc: 'Unmute the system audio' },
        { cmd: 'Set volume 50', desc: 'Set volume to specific level' },
        { cmd: 'Max volume', desc: 'Set volume to 100%' },
      ]
    },
    {
      title: '🔆 Brightness Management',
      commands: [
        { cmd: 'Brightness up', desc: 'Increase screen brightness' },
        { cmd: 'Brightness down', desc: 'Decrease screen brightness' },
        { cmd: 'Set brightness 80', desc: 'Set brightness to specific level' },
        { cmd: 'Night mode', desc: 'Enable blue light filter' },
        { cmd: 'Auto brightness', desc: 'Enable auto brightness adjustment' },
        { cmd: 'Max brightness', desc: 'Set brightness to 100%' },
      ]
    },
    {
      title: '🎵 Music Playback',
      commands: [
        { cmd: 'Play music', desc: 'Play music from YouTube' },
        { cmd: 'Play on Spotify', desc: 'Play from Spotify library' },
        { cmd: 'Next song', desc: 'Skip to next track' },
        { cmd: 'Previous song', desc: 'Go back to previous track' },
        { cmd: 'Pause music', desc: 'Pause current playback' },
        { cmd: 'Play Arijit Singh', desc: 'Play specific artist songs' },
      ]
    },
    {
      title: '📰 News Updates',
      commands: [
        { cmd: 'Latest news', desc: 'Get real-time breaking news' },
        { cmd: 'Market news', desc: 'Stock market & crypto news' },
        { cmd: 'Sports news', desc: 'Latest sports headlines' },
        { cmd: 'Tech news', desc: 'Technology and startup news' },
        { cmd: 'India news', desc: 'Indian news headlines' },
        { cmd: 'World news', desc: 'International news updates' },
      ]
    },
  ]

  // Voice recognition
  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      setResponse('Speech recognition not supported in this browser')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = selectedVoice.includes('hindi') || selectedVoice.includes('3') || selectedVoice.includes('4') ? 'hi-IN' : 'en-US'
    recognition.continuous = false
    recognition.interimResults = true

    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)
    recognition.onerror = () => setIsListening(false)

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript
      setTranscript(text)
      if (event.results[0].isFinal) {
        executeVoiceCommand(text)
      }
    }

    recognition.start()
  }, [selectedVoice])

  const executeVoiceCommand = async (command) => {
    const cmd = command.toLowerCase()
    let result = ''

    // System commands via desktop bridge
    if (window.jarvisDesktop) {
      if (cmd.includes('shutdown') || cmd.includes('shut down')) {
        const r = await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'shutdown /s /t 5' : 'shutdown -h now')
        result = '⚡ Shutting down PC in 5 seconds...'
      } else if (cmd.includes('restart') || cmd.includes('reboot')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'shutdown /r /t 5' : 'reboot')
        result = '🔄 Restarting PC in 5 seconds...'
      } else if (cmd.includes('sleep')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0' : 'systemctl suspend')
        result = '😴 PC going to sleep...'
      } else if (cmd.includes('lock')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'rundll32.exe user32.dll,LockWorkStation' : 'loginctl lock-session')
        result = '🔒 PC locked!'
      } else if (cmd.includes('volume up')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32'
          ? 'powershell "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"'
          : 'amixer set Master 10%+')
        result = '🔊 Volume increased!'
      } else if (cmd.includes('volume down')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32'
          ? 'powershell "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"'
          : 'amixer set Master 10%-')
        result = '🔉 Volume decreased!'
      } else if (cmd.includes('mute')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32'
          ? 'powershell "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"'
          : 'amixer set Master toggle')
        result = '🔇 Audio muted!'
      } else if (cmd.includes('brightness up')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32'
          ? 'powershell "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)"'
          : 'xrandr --output $(xrandr | grep " connected" | cut -f1 -d " ") --brightness 1.0')
        result = '🔆 Brightness increased!'
      } else if (cmd.includes('brightness down')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32'
          ? 'powershell "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)"'
          : 'xrandr --output $(xrandr | grep " connected" | cut -f1 -d " ") --brightness 0.6')
        result = '🔅 Brightness decreased!'
      } else if (cmd.includes('open chrome') || cmd.includes('open browser')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'start chrome' : 'google-chrome &')
        result = '🌐 Opening Chrome...'
      } else if (cmd.includes('open whatsapp')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'start whatsapp:' : 'xdg-open https://web.whatsapp.com')
        result = '💬 Opening WhatsApp...'
      } else if (cmd.includes('open calculator')) {
        await window.jarvisDesktop.runCommand(process.platform === 'win32' ? 'calc' : 'gnome-calculator &')
        result = '🔢 Opening Calculator...'
      } else if (cmd.includes('minimize')) {
        await window.jarvisDesktop.minimize()
        result = '⬇️ Window minimized!'
      } else if (cmd.includes('maximize')) {
        await window.jarvisDesktop.maximize()
        result = '⬆️ Window maximized!'
      } else if (cmd.includes('battery') || cmd.includes('power status')) {
        const r = await window.jarvisDesktop.getSystemInfo()
        result = `🔋 System: ${r.cpus} CPUs, ${r.totalMemory} RAM, ${r.freeMemory} free, Uptime: ${r.uptime}`
      } else if (cmd.includes('cpu') || cmd.includes('ram') || cmd.includes('system status')) {
        const r = await window.jarvisDesktop.getSystemInfo()
        result = `📊 CPU: ${r.cpus} cores | RAM: ${r.totalMemory} (${r.freeMemory} free) | Platform: ${r.platform} | Uptime: ${r.uptime}`
      } else {
        // Generic command execution
        const r = await window.jarvisDesktop.runCommand(command)
        result = r.success ? (r.stdout || '✅ Command executed!') : `❌ Error: ${r.error}`
      }
    } else {
      // Browser/Mobile mode — use API
      try {
        const res = await fetch(`${API_BASE}/api/miniapp/jarvis-ai/respond`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: command, user_id: 'voice_user' })
        })
        const data = await res.json()
        result = data.response || data.message || '🤖 Command processed via AI'
      } catch {
        // Offline voice response
        if (cmd.includes('news')) result = '📰 Fetching latest news...'
        else if (cmd.includes('music') || cmd.includes('play')) result = '🎵 Opening music player...'
        else if (cmd.includes('weather')) result = '🌤️ Checking weather...'
        else result = `🤖 Voice command received: "${command}"`
      }
    }

    // Speak the response
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(result.replace(/[🎵📰⚡🔊🔉🔇🔆🔅🌐💬🔢⬇️⬆️🔋📊🤖✅❌🔄😴🔒🖥️]/g, ''))
      const voices = speechSynthesis.getVoices()
      const profile = voiceProfiles.find(v => v.id === selectedVoice)
      if (profile) {
        const matchVoice = voices.find(v =>
          (profile.lang === 'hi' ? v.lang.includes('hi') : v.lang.includes('en')) &&
          (profile.gender === 'female' ? v.name.toLowerCase().includes('female') || v.name.includes('Zira') || v.name.includes('Samantha') : true)
        )
        if (matchVoice) utterance.voice = matchVoice
      }
      utterance.rate = 1.0
      utterance.pitch = 1.0
      speechSynthesis.speak(utterance)
    }

    setResponse(result)
    setRecentCommands(prev => [{ cmd: command, result, time: new Date().toLocaleTimeString() }, ...prev.slice(0, 9)])
  }

  // Quick command execution
  const quickExec = (cmd) => {
    setTranscript(cmd)
    executeVoiceCommand(cmd)
  }

  // Fetch system status
  useEffect(() => {
    const fetchStatus = async () => {
      if (window.jarvisDesktop) {
        const info = await window.jarvisDesktop.getSystemInfo()
        setSystemStatus(info)
      } else {
        setSystemStatus({
          platform: navigator.platform,
          cores: navigator.hardwareConcurrency || 'N/A',
          memory: navigator.deviceMemory ? `${navigator.deviceMemory} GB` : 'N/A',
          online: navigator.onLine,
        })
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-3 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="text-center mb-4">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-green-400 to-purple-400 bg-clip-text text-transparent">
          🎙️ Voice Automation
        </h1>
        <p className="text-xs text-slate-400 mt-1">Full System Control via Voice — Hindi + English</p>
      </div>

      {/* Voice Button */}
      <div className="flex flex-col items-center mb-4">
        <button
          onClick={startListening}
          className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl transition-all ${
            isListening
              ? 'bg-red-500 animate-pulse shadow-lg shadow-red-500/50 scale-110'
              : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:scale-105 shadow-lg shadow-blue-600/30'
          }`}
        >
          {isListening ? '⏹️' : '🎤'}
        </button>
        <div className={`text-xs mt-2 ${isListening ? 'text-red-400 animate-pulse' : 'text-slate-400'}`}>
          {isListening ? '🔴 Listening...' : 'Tap to speak'}
        </div>
        {transcript && (
          <div className="mt-2 text-sm text-blue-300 bg-blue-500/10 rounded-lg px-3 py-1">
            "{transcript}"
          </div>
        )}
        {response && (
          <div className="mt-1 text-xs text-green-400 bg-green-500/10 rounded-lg px-3 py-1 max-w-xs text-center">
            {response}
          </div>
        )}
      </div>

      {/* Voice Profile Selector */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 mb-4">
        <div className="text-xs text-slate-400 font-bold mb-2">🗣️ Voice Profile (4 Male + 4 Female)</div>
        <div className="grid grid-cols-4 gap-1.5">
          {voiceProfiles.map(v => (
            <button
              key={v.id}
              onClick={() => setSelectedVoice(v.id)}
              className={`p-1.5 rounded-lg text-[10px] text-center transition-all ${
                selectedVoice === v.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {v.gender === 'male' ? '👨' : '👩'} {v.name}
            </button>
          ))}
        </div>
      </div>

      {/* System Status */}
      {systemStatus && (
        <div className="bg-gradient-to-r from-emerald-900/30 to-blue-900/30 border border-emerald-500/20 rounded-xl p-3 mb-4">
          <div className="text-xs text-emerald-400 font-bold mb-1">📊 Live System Status</div>
          <div className="grid grid-cols-4 gap-1.5 text-[10px]">
            <div className="bg-slate-800/50 rounded p-1.5 text-center">
              <div className="text-slate-400">Platform</div>
              <div className="text-white font-medium">{systemStatus.platform}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-1.5 text-center">
              <div className="text-slate-400">CPU</div>
              <div className="text-white font-medium">{systemStatus.cores || systemStatus.cpus}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-1.5 text-center">
              <div className="text-slate-400">RAM</div>
              <div className="text-white font-medium">{systemStatus.memory || systemStatus.totalMemory}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-1.5 text-center">
              <div className="text-slate-400">Status</div>
              <div className="text-green-400 font-medium">{systemStatus.online !== false ? '🟢' : '🔴'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1.5 mb-3">
        <button onClick={() => setActiveTab('commands')} className={`flex-1 py-1.5 rounded-lg text-xs font-medium ${activeTab === 'commands' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
          📋 Commands
        </button>
        <button onClick={() => setActiveTab('history')} className={`flex-1 py-1.5 rounded-lg text-xs font-medium ${activeTab === 'history' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
          📜 History
        </button>
      </div>

      {activeTab === 'commands' ? (
        /* Command Categories */
        <div className="space-y-3">
          {commandCategories.map((cat, ci) => (
            <div key={ci} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
              <div className="text-sm font-bold text-blue-400 mb-2">{cat.title}</div>
              <div className="grid grid-cols-2 gap-1.5">
                {cat.commands.map((c, i) => (
                  <button
                    key={i}
                    onClick={() => quickExec(c.cmd)}
                    className="bg-slate-900/50 hover:bg-slate-700/50 rounded-lg p-2 text-left transition-all group"
                  >
                    <div className="text-[11px] text-white font-medium group-hover:text-blue-400">{c.cmd}</div>
                    <div className="text-[9px] text-slate-500">{c.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Command History */
        <div className="space-y-1.5">
          {recentCommands.length === 0 ? (
            <div className="text-center text-slate-500 text-xs py-8">No commands yet — start speaking!</div>
          ) : (
            recentCommands.map((c, i) => (
              <div key={i} className="bg-slate-800/50 rounded-lg p-2">
                <div className="flex justify-between items-center">
                  <div className="text-xs text-blue-400 font-medium">"{c.cmd}"</div>
                  <div className="text-[9px] text-slate-500">{c.time}</div>
                </div>
                <div className="text-[10px] text-green-400 mt-0.5">{c.result}</div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default VoiceAutomation
