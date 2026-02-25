/**
 * 🦾 JARVIS Holographic Interface — Iron Man Edition
 * ═══════════════════════════════════════════════════
 * 
 * Complete Iron Man movie-style JARVIS interface with:
 * - Arc Reactor animated face
 * - Voice waveform visualization
 * - Camera feed + emotion detection
 * - AI chat with streaming
 * - Code editor & execution
 * - System controls panel
 * - Holographic HUD design
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import './JarvisHolographic.css'
import freeAI from '../services/freeAI'
import cameraEngine from '../services/cameraEngine'
import codeEngine from '../services/codeExecutionEngine'

// ═══════════════════════════════════
// MAIN JARVIS HOLOGRAPHIC COMPONENT
// ═══════════════════════════════════

export default function JarvisHolographic() {
  // ── State ──
  const [messages, setMessages] = useState([
    { role: 'jarvis', content: "Good day, Sir. I am JARVIS — Just A Rather Very Intelligent System. All systems are online. How may I assist you today?" }
  ])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [activePanel, setActivePanel] = useState('chat') // chat, code, controls, settings
  const [cameraActive, setCameraActive] = useState(false)
  const [emotion, setEmotion] = useState(null)
  const [proximity, setProximity] = useState('unknown')
  const [faces, setFaces] = useState([])
  const [codeText, setCodeText] = useState('// Write your code here\nconsole.log("Hello from JARVIS!")')
  const [codeLang, setCodeLang] = useState('javascript')
  const [codeOutput, setCodeOutput] = useState(null)
  const [codeRunning, setCodeRunning] = useState(false)
  const [streamText, setStreamText] = useState('')
  const [systemTime, setSystemTime] = useState(new Date())
  const [aiProvider, setAiProvider] = useState('groq')
  const [showSettings, setShowSettings] = useState(false)
  const [apiKeyInput, setApiKeyInput] = useState('')
  const [reactorMinimized, setReactorMinimized] = useState(false)

  // ── Refs ──
  const chatRef = useRef(null)
  const videoRef = useRef(null)
  const inputRef = useRef(null)
  const recognitionRef = useRef(null)
  const synthRef = useRef(window.speechSynthesis)

  // ── Initialize ──
  useEffect(() => {
    freeAI.init()
    
    // Update time every second
    const timer = setInterval(() => setSystemTime(new Date()), 1000)
    
    // Initialize speech recognition
    initSpeechRecognition()
    
    // Keyboard shortcut
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'J') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    
    return () => {
      clearInterval(timer)
      window.removeEventListener('keydown', handleKeyDown)
      cameraEngine.stopCamera()
    }
  }, [])

  // Auto-scroll chat
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages, streamText])

  // ── Speech Recognition ──
  const initSpeechRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join('')
      
      setInput(transcript)
      
      if (event.results[0].isFinal) {
        setIsListening(false)
        handleSend(transcript)
      }
    }

    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)
    
    recognitionRef.current = recognition
  }, [])

  // ── Toggle Voice ──
  const toggleVoice = () => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
    } else {
      try {
        recognitionRef.current?.start()
        setIsListening(true)
      } catch {}
    }
  }

  // ── Speak Response ──
  const speak = (text) => {
    if (!synthRef.current) return
    synthRef.current.cancel()
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    utterance.pitch = 0.9
    utterance.volume = 0.8
    
    // Try to find a British English voice
    const voices = synthRef.current.getVoices()
    const britishVoice = voices.find(v => v.lang.includes('en-GB')) || 
                         voices.find(v => v.lang.includes('en-US')) ||
                         voices[0]
    if (britishVoice) utterance.voice = britishVoice
    
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    
    synthRef.current.speak(utterance)
  }

  // ── Send Message ──
  const handleSend = async (overrideText) => {
    const text = overrideText || input.trim()
    if (!text || isThinking) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setIsThinking(true)
    setStreamText('')
    setReactorMinimized(true)

    // Check for system commands
    const commandResult = await handleSystemCommand(text)
    if (commandResult) {
      setMessages(prev => [...prev, { role: 'jarvis', content: commandResult }])
      speak(commandResult)
      setIsThinking(false)
      return
    }

    // Stream callback
    freeAI.onStreamChunk = (chunk, full) => {
      setStreamText(full)
    }

    const result = await freeAI.chat(text, { 
      stream: true,
      emotion,
      context: proximity !== 'away' ? `User is ${proximity} to the device.` : ''
    })

    setStreamText('')
    setMessages(prev => [...prev, { 
      role: 'jarvis', 
      content: result.response,
      provider: result.provider 
    }])
    
    // Speak the response (first 200 chars for long responses)
    const speakText = result.response.length > 200 
      ? result.response.substring(0, 200) + '...' 
      : result.response
    speak(speakText.replace(/```[\s\S]*?```/g, 'code block').replace(/[*_#`]/g, ''))
    
    setIsThinking(false)
  }

  // ── System Commands ──
  const handleSystemCommand = async (text) => {
    const cmd = text.toLowerCase()
    const isDesktop = !!window.jarvisDesktop

    // Volume commands
    if (cmd.includes('volume up') || cmd.includes('increase volume')) {
      if (isDesktop) { await window.jarvisDesktop.volumeUp(); return "Volume increased, Sir." }
      return "Volume control requires desktop mode, Sir."
    }
    if (cmd.includes('volume down') || cmd.includes('decrease volume') || cmd.includes('lower volume')) {
      if (isDesktop) { await window.jarvisDesktop.volumeDown(); return "Volume decreased, Sir." }
    }
    if (cmd.includes('mute')) {
      if (isDesktop) { await window.jarvisDesktop.volumeMute(); return "Audio muted, Sir." }
    }

    // App commands
    if (cmd.match(/open (chrome|browser)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('chrome'); return "Opening Chrome, Sir." }
    }
    if (cmd.match(/open (vscode|vs code|code editor)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('vscode'); return "Opening VS Code, Sir." }
    }
    if (cmd.match(/open (whatsapp)/)) {
      if (isDesktop) { await window.jarvisDesktop.whatsappOpen(); return "Opening WhatsApp, Sir." }
    }
    if (cmd.match(/open (spotify|music)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('spotify'); return "Opening Spotify, Sir." }
    }
    if (cmd.match(/open (terminal|cmd)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('terminal'); return "Opening Terminal, Sir." }
    }
    if (cmd.match(/open (calculator)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('calculator'); return "Opening Calculator, Sir." }
    }
    if (cmd.match(/open (file|explorer|files)/)) {
      if (isDesktop) { await window.jarvisDesktop.openApp('explorer'); return "Opening File Explorer, Sir." }
    }

    // Power commands
    if (cmd.includes('lock') && (cmd.includes('screen') || cmd.includes('computer') || cmd.includes('pc'))) {
      if (isDesktop) { await window.jarvisDesktop.pcLock(); return "Locking the system now, Sir." }
    }
    if (cmd.includes('sleep') && (cmd.includes('computer') || cmd.includes('pc') || cmd.includes('system'))) {
      if (isDesktop) { await window.jarvisDesktop.pcSleep(); return "Putting the system to sleep, Sir." }
    }
    if (cmd.includes('shutdown') || cmd.includes('shut down')) {
      if (isDesktop) { await window.jarvisDesktop.pcShutdown(); return "Initiating shutdown sequence, Sir. You have 5 seconds." }
    }
    if (cmd.includes('restart') && (cmd.includes('computer') || cmd.includes('pc') || cmd.includes('system'))) {
      if (isDesktop) { await window.jarvisDesktop.pcRestart(); return "Restarting the system, Sir." }
    }

    // Brightness
    if (cmd.includes('brightness up') || cmd.includes('brighter')) {
      if (isDesktop) { await window.jarvisDesktop.brightnessUp(); return "Brightness increased, Sir." }
    }
    if (cmd.includes('brightness down') || cmd.includes('dimmer') || cmd.includes('dim')) {
      if (isDesktop) { await window.jarvisDesktop.brightnessDown(); return "Brightness decreased, Sir." }
    }

    // Music
    if (cmd.match(/play (.+) on youtube/)) {
      const query = cmd.match(/play (.+) on youtube/)[1]
      if (isDesktop) { await window.jarvisDesktop.playYouTube(query); return `Searching YouTube for "${query}", Sir.` }
      else { window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`); return `Opening YouTube search for "${query}", Sir.` }
    }

    // WhatsApp message
    if (cmd.match(/send whatsapp to (\d+) (.+)/)) {
      const match = cmd.match(/send whatsapp to (\d+) (.+)/)
      if (isDesktop) { await window.jarvisDesktop.whatsappSend(match[1], match[2]); return `Opening WhatsApp to send message to ${match[1]}, Sir.` }
    }

    // System info
    if (cmd.includes('system info') || cmd.includes('system specs') || cmd.includes('computer info')) {
      if (isDesktop) {
        const info = await window.jarvisDesktop.getSystemInfo()
        return `System Report:\n• Platform: ${info.platform}\n• CPU: ${info.cpus} cores\n• Memory: ${info.totalMemory} (${info.freeMemory} free)\n• Uptime: ${info.uptime}\n• Electron: v${info.electronVersion}`
      }
    }

    // Camera
    if (cmd.includes('camera on') || cmd.includes('turn on camera') || cmd.includes('see me') || cmd.includes('look at me')) {
      toggleCamera()
      return cameraActive ? "Disabling camera feed, Sir." : "Activating camera feed. I can see you now, Sir."
    }

    // Time
    if (cmd.includes('what time') || cmd === 'time') {
      return `The current time is ${new Date().toLocaleTimeString()}, Sir.`
    }
    if (cmd.includes('what date') || cmd === 'date' || cmd.includes('what day')) {
      return `Today is ${new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}, Sir.`
    }

    // Code execution
    if (cmd.startsWith('run ') || cmd.startsWith('execute ')) {
      setActivePanel('code')
      return null // Let AI handle complex code requests
    }

    // Not a system command — let AI handle it
    return null
  }

  // ── Camera Toggle ──
  const toggleCamera = async () => {
    if (cameraActive) {
      cameraEngine.stopCamera()
      setCameraActive(false)
      setFaces([])
      setEmotion(null)
      setProximity('unknown')
    } else {
      if (videoRef.current) {
        cameraEngine.init({
          onFaceDetected: (detected) => setFaces(detected),
          onEmotionDetected: (emo) => setEmotion(emo),
          onProximityChange: (prox) => {
            setProximity(prox)
            if (prox === 'near' || prox === 'very-near') {
              // Greet when user approaches
              const greetings = [
                "Welcome back, Sir.",
                "Good to see you, Sir. All systems operational.",
                "I detect your presence, Sir. How may I help?"
              ]
              const greet = greetings[Math.floor(Math.random() * greetings.length)]
              speak(greet)
            }
          }
        })
        const result = await cameraEngine.startCamera(videoRef.current)
        setCameraActive(result.success)
      }
    }
  }

  // ── Run Code ──
  const runCode = async () => {
    setCodeRunning(true)
    setCodeOutput(null)
    const result = await codeEngine.execute(codeText, codeLang)
    setCodeOutput(result)
    setCodeRunning(false)
  }

  // ── Save API Key ──
  const saveApiKey = () => {
    if (apiKeyInput.trim()) {
      freeAI.setApiKey(aiProvider, apiKeyInput.trim())
      freeAI.setProvider(aiProvider)
      setApiKeyInput('')
      setShowSettings(false)
      setMessages(prev => [...prev, { 
        role: 'jarvis', 
        content: `${aiProvider.charAt(0).toUpperCase() + aiProvider.slice(1)} API key configured successfully, Sir. I'm now fully operational with ${aiProvider} as my AI backbone.` 
      }])
    }
  }

  // ── Key Press ──
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Quick Actions ──
  const quickActions = [
    { label: '💻 System Info', action: () => handleSend('show me system info') },
    { label: '📷 Camera', action: toggleCamera },
    { label: '⚡ Code', action: () => { setActivePanel('code'); setReactorMinimized(true) } },
    { label: '🔊 Volume +', action: () => handleSend('volume up') },
    { label: '🔇 Mute', action: () => handleSend('mute') },
    { label: '🌐 Chrome', action: () => handleSend('open chrome') },
    { label: '🎵 Spotify', action: () => handleSend('open spotify') },
    { label: '⚙️ Settings', action: () => setShowSettings(!showSettings) },
  ]

  // ═══════════════════════════════════
  // RENDER
  // ═══════════════════════════════════

  return (
    <div className="jarvis-holographic">
      {/* Background Effects */}
      <div className="holo-grid" />
      <div className="scan-lines" />
      <div className="scan-bar" />
      
      {/* Corner Decorations */}
      <div className="corner-deco top-left" />
      <div className="corner-deco top-right" />
      <div className="corner-deco bottom-left" />
      <div className="corner-deco bottom-right" />

      {/* ── Status Bar ── */}
      <div className="jarvis-status-bar">
        <div className="status-left">
          <span className="holo-text" style={{ fontSize: '13px', fontWeight: 600, letterSpacing: '4px' }}>
            J.A.R.V.I.S.
          </span>
          <div className="status-indicator">
            <div className="live-dot" />
            <span>ONLINE</span>
          </div>
        </div>
        <div className="status-right">
          <span style={{ color: 'rgba(0, 212, 255, 0.5)' }}>
            {systemTime.toLocaleTimeString('en-US', { hour12: false })}
          </span>
          <span style={{ color: 'rgba(0, 212, 255, 0.3)', fontSize: '9px' }}>
            {systemTime.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
          {emotion && (
            <div className="status-indicator">
              <span>{emotion.dominant === 'happy' ? '😊' : emotion.dominant === 'sad' ? '😢' : emotion.dominant === 'angry' ? '😠' : emotion.dominant === 'surprised' ? '😮' : '😐'}</span>
              <span>{emotion.dominant}</span>
            </div>
          )}
          {proximity !== 'unknown' && proximity !== 'away' && (
            <div className="status-indicator">
              <div className="live-dot" />
              <span>USER {proximity.toUpperCase()}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Arc Reactor (JARVIS Face) ── */}
      <div className={`arc-reactor-container ${reactorMinimized ? 'minimized' : ''}`}
        onClick={() => setReactorMinimized(!reactorMinimized)}
        style={{ cursor: 'pointer' }}
      >
        <div className="arc-reactor">
          <div className="arc-ring arc-ring-5" />
          <div className="arc-ring arc-ring-4" />
          <div className="arc-ring arc-ring-3" />
          <div className="arc-ring arc-ring-2" />
          <div className="arc-ring arc-ring-1" />
          <div className={`arc-core ${isSpeaking ? 'speaking' : ''}`} />
        </div>
        
        {/* Voice Waveform */}
        <div className={`voice-waveform ${isSpeaking || isListening ? '' : 'idle'}`}>
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="wave-bar" 
              style={{ 
                height: isSpeaking || isListening 
                  ? `${Math.random() * 32 + 4}px` 
                  : '4px',
                animationDuration: `${0.3 + Math.random() * 0.4}s`
              }} 
            />
          ))}
        </div>

        {!reactorMinimized && (
          <div className="jarvis-title holo-text">
            {isThinking ? 'PROCESSING...' : isSpeaking ? 'SPEAKING...' : isListening ? 'LISTENING...' : 'READY'}
          </div>
        )}
      </div>

      {/* ── Camera Feed ── */}
      {cameraActive && (
        <div className="camera-feed-panel hud-panel fade-in">
          <div className="hud-panel-header">
            <div className="dot" />
            <span>VISUAL FEED</span>
            <button onClick={toggleCamera} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer', fontSize: '14px' }}>✕</button>
          </div>
          <div style={{ position: 'relative' }}>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', borderRadius: '4px' }} />
            <div className="camera-overlay">
              {faces.map((face, i) => (
                <div key={i} className="face-box" style={{
                  left: `${(face.x / 640) * 100}%`,
                  top: `${(face.y / 480) * 100}%`,
                  width: `${(face.width / 640) * 100}%`,
                  height: `${(face.height / 480) * 100}%`
                }}>
                  {emotion && <div className="face-label">{emotion.dominant} {(emotion.confidence * 100).toFixed(0)}%</div>}
                </div>
              ))}
            </div>
          </div>
          {emotion && (
            <div className="emotion-display">
              {Object.entries(emotion.all || {}).map(([name, value]) => (
                <div key={name} className="emotion-bar">
                  <span style={{ width: '52px', fontSize: '9px', textTransform: 'uppercase' }}>{name}</span>
                  <div className="bar-track">
                    <div className={`bar-fill ${name}`} style={{ width: `${value * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Hidden video element for camera */}
      {!cameraActive && <video ref={videoRef} style={{ display: 'none' }} />}

      {/* ── Code Editor Panel ── */}
      {activePanel === 'code' && (
        <div className="code-panel slide-up">
          <div className="hud-panel" style={{ padding: 0, display: 'flex', flexDirection: 'column', maxHeight: 'calc(100vh - 160px)' }}>
            <div className="code-toolbar">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="hud-panel-header" style={{ margin: 0 }}>
                  <div className="dot" />
                  <span>CODE ENGINE</span>
                </div>
                <select value={codeLang} onChange={(e) => setCodeLang(e.target.value)}>
                  {codeEngine.getSupportedLanguages().map(l => (
                    <option key={l.id} value={l.id}>{l.icon} {l.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button className="run-btn" onClick={runCode} disabled={codeRunning}>
                  {codeRunning ? '⏳ Running...' : '▶ Run'}
                </button>
                <button className="run-btn" onClick={() => setActivePanel('chat')} style={{ color: '#ff6666', borderColor: 'rgba(255,100,100,0.3)' }}>
                  ✕
                </button>
              </div>
            </div>
            <textarea
              className="code-editor"
              value={codeText}
              onChange={(e) => setCodeText(e.target.value)}
              spellCheck={false}
              placeholder="Write your code here..."
            />
            {codeOutput && (
              <div className={`code-output ${codeOutput.success ? '' : 'error'}`}>
                <div style={{ fontSize: '9px', color: 'rgba(0,212,255,0.5)', marginBottom: '4px', letterSpacing: '1px' }}>
                  OUTPUT ({codeOutput.elapsed}) {codeOutput.success ? '✓' : '✗'}
                </div>
                {codeOutput.output || codeOutput.error || 'No output'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── System Controls Panel ── */}
      {activePanel === 'controls' && (
        <div className="code-panel slide-up">
          <div className="hud-panel">
            <div className="hud-panel-header">
              <div className="dot" />
              <span>SYSTEM CONTROL</span>
              <button onClick={() => setActivePanel('chat')} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer' }}>✕</button>
            </div>
            <div className="system-controls-grid">
              {[
                { icon: '🔊', label: 'Vol +', action: () => window.jarvisDesktop?.volumeUp() },
                { icon: '🔉', label: 'Vol -', action: () => window.jarvisDesktop?.volumeDown() },
                { icon: '🔇', label: 'Mute', action: () => window.jarvisDesktop?.volumeMute() },
                { icon: '☀️', label: 'Bright +', action: () => window.jarvisDesktop?.brightnessUp() },
                { icon: '🌙', label: 'Bright -', action: () => window.jarvisDesktop?.brightnessDown() },
                { icon: '🔒', label: 'Lock', action: () => window.jarvisDesktop?.pcLock() },
                { icon: '💤', label: 'Sleep', action: () => window.jarvisDesktop?.pcSleep() },
                { icon: '🔄', label: 'Restart', action: () => window.jarvisDesktop?.pcRestart() },
                { icon: '⏏️', label: 'Logoff', action: () => window.jarvisDesktop?.pcLogoff() },
                { icon: '🌐', label: 'Chrome', action: () => window.jarvisDesktop?.openApp('chrome') },
                { icon: '💻', label: 'VS Code', action: () => window.jarvisDesktop?.openApp('vscode') },
                { icon: '📂', label: 'Files', action: () => window.jarvisDesktop?.openApp('explorer') },
                { icon: '📱', label: 'WhatsApp', action: () => window.jarvisDesktop?.whatsappOpen() },
                { icon: '🎵', label: 'Spotify', action: () => window.jarvisDesktop?.openApp('spotify') },
                { icon: '⏯️', label: 'Play/Pause', action: () => window.jarvisDesktop?.mediaControl('play') },
                { icon: '⏭️', label: 'Next', action: () => window.jarvisDesktop?.mediaControl('next') },
                { icon: '⏮️', label: 'Previous', action: () => window.jarvisDesktop?.mediaControl('previous') },
                { icon: '📷', label: 'Camera', action: toggleCamera },
              ].map((ctrl, i) => (
                <button key={i} className="sys-ctrl-btn" onClick={ctrl.action}>
                  <span className="icon">{ctrl.icon}</span>
                  <span>{ctrl.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Settings Panel ── */}
      {showSettings && (
        <div className="code-panel slide-up" style={{ zIndex: 100 }}>
          <div className="hud-panel">
            <div className="hud-panel-header">
              <div className="dot" />
              <span>AI CONFIGURATION</span>
              <button onClick={() => setShowSettings(false)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer' }}>✕</button>
            </div>
            
            <div style={{ fontSize: '11px', color: 'rgba(0,212,255,0.6)', marginBottom: '12px' }}>
              Configure your free AI API key. No server needed — calls go directly from your device.
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {Object.entries({
                  groq: '⚡ Groq (FREE)',
                  gemini: '🔮 Gemini (FREE)',
                  together: '🤝 Together (FREE)',
                  openai: '🧠 OpenAI',
                  anthropic: '🎭 Anthropic'
                }).map(([key, label]) => (
                  <button
                    key={key}
                    className={`quick-action-chip ${aiProvider === key ? 'active' : ''}`}
                    onClick={() => setAiProvider(key)}
                    style={aiProvider === key ? { background: 'rgba(0,212,255,0.2)', borderColor: '#00d4ff' } : {}}
                  >
                    {label} {freeAI.apiKeys[key] ? '✓' : ''}
                  </button>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '6px' }}>
                <input
                  type="password"
                  className="chat-input"
                  placeholder={`Enter ${aiProvider} API key...`}
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  style={{ borderRadius: '8px' }}
                />
                <button className="run-btn" onClick={saveApiKey}>Save</button>
              </div>

              <div style={{ fontSize: '10px', color: 'rgba(0,212,255,0.4)' }}>
                {aiProvider === 'groq' && '→ Get free key at console.groq.com'}
                {aiProvider === 'gemini' && '→ Get free key at aistudio.google.com/apikey'}
                {aiProvider === 'together' && '→ Get free key at api.together.xyz'}
                {aiProvider === 'openai' && '→ Get key at platform.openai.com (paid)'}
                {aiProvider === 'anthropic' && '→ Get key at console.anthropic.com (paid)'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Navigation Buttons ── */}
      <div className="jarvis-nav-overlay">
        {[
          { id: 'chat', icon: '💬', label: 'Chat' },
          { id: 'code', icon: '⚡', label: 'Code' },
          { id: 'controls', icon: '🎮', label: 'Controls' },
        ].map(nav => (
          <button
            key={nav.id}
            className={`jarvis-nav-btn ${activePanel === nav.id ? 'active' : ''}`}
            onClick={() => { setActivePanel(nav.id); setReactorMinimized(nav.id !== 'chat') }}
          >
            {nav.icon} {nav.label}
          </button>
        ))}
      </div>

      {/* ── Quick Actions ── */}
      <div style={{ position: 'absolute', top: '50px', left: '50%', transform: 'translateX(-50%)', zIndex: 20, display: reactorMinimized ? 'block' : 'none' }}>
        <div className="quick-actions" style={{ maxWidth: '90vw' }}>
          {quickActions.map((qa, i) => (
            <button key={i} className="quick-action-chip" onClick={qa.action}>
              {qa.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Chat Interface ── */}
      <div className={`jarvis-chat-container ${reactorMinimized ? 'expanded' : ''}`}>
        <div className="chat-messages" ref={chatRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role === 'user' ? 'user' : 'jarvis'}`}>
              {msg.role === 'jarvis' && <div className="jarvis-label">J.A.R.V.I.S.</div>}
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              {msg.provider && msg.provider !== 'offline' && (
                <div style={{ fontSize: '9px', color: 'rgba(0,212,255,0.3)', marginTop: '4px', textAlign: 'right' }}>
                  via {msg.provider}
                </div>
              )}
            </div>
          ))}
          
          {/* Streaming text */}
          {streamText && (
            <div className="chat-message jarvis">
              <div className="jarvis-label">J.A.R.V.I.S.</div>
              <div style={{ whiteSpace: 'pre-wrap' }}>{streamText}</div>
            </div>
          )}
          
          {/* Thinking indicator */}
          {isThinking && !streamText && (
            <div className="chat-message jarvis">
              <div className="jarvis-label">J.A.R.V.I.S.</div>
              <div className="thinking-dots">
                <span /><span /><span />
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="chat-input-bar">
          <button className={`chat-btn ${isListening ? 'active' : ''}`} onClick={toggleVoice} title="Voice input">
            🎤
          </button>
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder={isListening ? 'Listening...' : 'Ask JARVIS anything...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isThinking}
          />
          <button className="chat-btn" onClick={() => handleSend()} disabled={isThinking || !input.trim()}>
            {isThinking ? '⏳' : '➤'}
          </button>
          <button className="chat-btn" onClick={() => setShowSettings(!showSettings)} title="Settings">
            ⚙️
          </button>
        </div>
      </div>
    </div>
  )
}
