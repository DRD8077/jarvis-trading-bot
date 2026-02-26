import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Loader, Send, Sparkles, Heart, SmilePlus, Globe, Brain } from 'lucide-react'
import { useApp } from '../context/AppContext'

/**
 * 🎙️💕 JARVIS Hindi Voice Assistant — Super Sweet & Smiling Voice
 * 
 * Features:
 * - Hindi voice input & output
 * - Sweet, always smiling personality
 * - Mood detection & empathetic responses
 * - Gemini deep understanding
 * - Owner/User aware
 * - Real-time conversation
 */

import { API_BASE, SERVER_BASE } from '../services/apiBase'

const VOICE_BASE = (SERVER_BASE || '') + '/api/voice'
const GEMINI_BASE = (SERVER_BASE || '') + '/api/gemini'

const MOOD_EMOJIS = {
  happy: '😊',
  sad: '🤗',
  confused: '💡',
  excited: '🎉',
  anxious: '🌸',
  neutral: '😊',
}

const SWEET_PLACEHOLDERS = [
  'JARVIS se Hindi mein baat karo... 💕',
  'Kuch bhi poochiye, main hoon na! 😊',
  'Market ki baat karo ya bas hello bolo! 🌟',
  'Boliye, main sun rahi hoon... 🎤',
]

const HindiVoiceAssistant = ({ onTranscript, onResponse, fullScreen = false }) => {
  const { addNotification, hapticFeedback } = useApp()
  const jarvisAuthRef = useRef(null)
  const [isOwner, setIsOwner] = useState(false)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState(null)
  const [chatHistory, setChatHistory] = useState([])
  const [textInput, setTextInput] = useState('')
  const [mood, setMood] = useState('neutral')
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [placeholder] = useState(SWEET_PLACEHOLDERS[Math.floor(Math.random() * SWEET_PLACEHOLDERS.length)])
  
  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const chatEndRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  // Load smartAuth service dynamically
  useEffect(() => {
    import('../services/smartAuth').then(m => {
      jarvisAuthRef.current = m?.default || m
      if (jarvisAuthRef.current?.isOwner) setIsOwner(true)
    }).catch(() => {})
  }, [])

  // Start voice recording — uses native Capacitor on Android, browser fallback on web
  const startListening = async () => {
    hapticFeedback?.('impact')
    try {
      // Try native Capacitor speech recognition first (works on Android APK)
      const { Capacitor } = await import('@capacitor/core').catch(() => ({}))
      if (Capacitor?.isNativePlatform?.()) {
        try {
          const { SpeechRecognition } = await import('@capacitor-community/speech-recognition')
          const perm = await SpeechRecognition.requestPermissions()
          if (perm?.speechRecognition === 'granted') {
            setListening(true)
            const result = await SpeechRecognition.start({
              language: 'hi-IN',
              maxResults: 1,
              prompt: 'JARVIS sun raha hai...',
              partialResults: false,
              popup: true,
            })
            setListening(false)
            const text = result?.matches?.[0] || ''
            if (text) {
              setTranscript(text)
              if (onTranscript) onTranscript(text)
              await getAIResponse(text)
            } else {
              addNotification?.('Sunai nahi diya, dubara boliye! 😊', 'info')
            }
            return
          }
        } catch (nativeErr) {
          console.warn('[Voice] Native STT failed, trying browser:', nativeErr)
        }
      }

      // Try browser Web Speech API (works on Chrome, Edge)
      if (window.webkitSpeechRecognition || window.SpeechRecognition) {
        const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition
        const recognition = new SpeechRecognitionAPI()
        recognition.lang = 'hi-IN'
        recognition.continuous = false
        recognition.interimResults = false
        
        recognition.onresult = (event) => {
          const text = event.results[0]?.[0]?.transcript || ''
          setListening(false)
          if (text) {
            setTranscript(text)
            if (onTranscript) onTranscript(text)
            getAIResponse(text)
          }
        }
        recognition.onerror = () => setListening(false)
        recognition.onend = () => setListening(false)
        
        recognition.start()
        setListening(true)
        return
      }

      // Fallback: MediaRecorder (send audio to server for transcription)
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 } 
      })
      const mediaRecorder = new MediaRecorder(stream, { 
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
          ? 'audio/webm;codecs=opus' : 'audio/webm' 
      })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
        await processVoiceInput(blob)
      }

      mediaRecorder.start()
      setListening(true)
    } catch (e) {
      addNotification?.('🎤 Mic access chahiye! Settings mein allow kijiye', 'error')
      hapticFeedback?.('error')
    }
  }

  const stopListening = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    setListening(false)
    hapticFeedback?.('impact')
  }

  // Process voice input — transcribe & get AI response
  const processVoiceInput = async (audioBlob) => {
    setThinking(true)
    
    try {
      // Step 1: Transcribe
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      
      const transcribeResp = await fetch(`${VOICE_BASE}/transcribe`, {
        method: 'POST',
        body: formData,
      })
      
      const transcribeData = await transcribeResp.json()
      const text = transcribeData?.text || ''
      
      if (!text) {
        addNotification?.('Sunai nahi diya, dubara boliye! 😊', 'info')
        setThinking(false)
        return
      }
      
      setTranscript(text)
      if (onTranscript) onTranscript(text)
      
      // Step 2: Get AI response
      await getAIResponse(text)
      
    } catch (e) {
      addNotification?.('Voice processing mein dikkat! 😅', 'error')
    } finally {
      setThinking(false)
    }
  }

  // Get AI response — Hindi, sweet, smiling
  const getAIResponse = useCallback(async (message) => {
    if (!message.trim()) return
    
    setThinking(true)
    
    // Add user message to history
    const userMsg = { role: 'user', text: message, time: new Date() }
    setChatHistory(prev => [...prev, userMsg])
    
    try {
      const formData = new FormData()
      formData.append('message', message)
      formData.append('user_id', jarvisAuthRef.current?.user?.chat_id || '0')
      formData.append('user_name', jarvisAuthRef.current?.user?.first_name || '')
      formData.append('is_owner', jarvisAuthRef.current?.isOwner ? 'true' : 'false')
      
      const resp = await fetch(`${VOICE_BASE}/chat`, {
        method: 'POST',
        body: formData,
      })
      
      const data = await resp.json()
      
      setMood(data.mood || 'neutral')
      setResponse(data)
      
      // Add AI response to history
      const aiMsg = { 
        role: 'assistant', 
        text: data.text, 
        mood: data.mood,
        time: new Date(),
        hasVoice: data.has_voice,
        voiceUrl: data.voice_url,
      }
      setChatHistory(prev => [...prev, aiMsg])
      
      if (onResponse) onResponse(data)
      
      // Auto-play voice if enabled
      if (voiceEnabled) {
        // Try server voice first
        if (data.voice_url && audioRef.current) {
          const baseUrl = API_BASE.replace('/api/miniapp', '')
          audioRef.current.src = `${baseUrl}${data.voice_url}`
          setSpeaking(true)
          audioRef.current.play().catch(() => {
            // Server audio failed — use native/browser TTS
            speakWithTTS(data.text)
          })
          audioRef.current.onended = () => setSpeaking(false)
        } else {
          // No server voice URL — use native/browser TTS
          speakWithTTS(data.text)
        }
      }
      
    } catch (e) {
      // Backend failed — try freeAI as fallback
      try {
        const { default: freeAI } = await import('../services/freeAI')
        if (!freeAI._initialized) freeAI.init()
        const result = await freeAI.chat(
          `You are JARVIS, a Hindi-speaking sweet AI assistant. Reply in Hinglish with emojis. User said: ${message}`
        )
        const replyText = result?.text || result?.response || (typeof result === 'string' ? result : 'Main soch raha hoon...')
        const aiMsg = { role: 'assistant', text: replyText, mood: 'happy', time: new Date() }
        setChatHistory(prev => [...prev, aiMsg])
        // Use native/browser TTS since server is down
        if (voiceEnabled) {
          await speakWithTTS(replyText)
        }
      } catch (e2) {
        const errorMsg = { 
          role: 'assistant', 
          text: 'Arre sorry jee! Thodi der mein try kijiye 😊💕', 
          mood: 'neutral',
          time: new Date() 
        }
        setChatHistory(prev => [...prev, errorMsg])
      }
    } finally {
      setThinking(false)
    }
  }, [voiceEnabled, onResponse])

  // Native/Browser TTS — uses ElevenLabs first, then fallback
  const speakWithTTS = async (text) => {
    if (!text) return
    setSpeaking(true)
    try {
      // Try ElevenLabs first (sweet Priya voice)
      try {
        const { default: elevenlabsVoice } = await import('../services/elevenlabsVoice')
        if (elevenlabsVoice && elevenlabsVoice.initialized) {
          await elevenlabsVoice.speak(text.substring(0, 500), { voice: 'priya' })
          setSpeaking(false)
          return
        }
      } catch {}
      
      // Try Capacitor native TTS (best quality on Android)
      const { Capacitor } = await import('@capacitor/core').catch(() => ({}))
      if (Capacitor?.isNativePlatform?.()) {
        try {
          const { TextToSpeech } = await import('@capacitor-community/text-to-speech')
          await TextToSpeech.speak({
            text: text.substring(0, 500),
            lang: 'hi-IN',
            rate: 0.95,
            pitch: 1.1,
            volume: 1.0,
            category: 'playback',
          })
          setSpeaking(false)
          return
        } catch {}
      }
      // Fallback: browser speechSynthesis
      if (window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(text.substring(0, 500))
        utterance.lang = 'hi-IN'
        utterance.rate = 0.95
        utterance.pitch = 1.1
        utterance.onend = () => setSpeaking(false)
        utterance.onerror = () => setSpeaking(false)
        window.speechSynthesis.speak(utterance)
      } else {
        setSpeaking(false)
      }
    } catch {
      setSpeaking(false)
    }
  }

  // Handle text submit
  const handleTextSubmit = async (e) => {
    e?.preventDefault()
    if (!textInput.trim()) return
    
    const msg = textInput
    setTextInput('')
    await getAIResponse(msg)
  }

  // Speak a specific text (tap-to-speak on messages)
  const speakText = async (text) => {
    if (!text) return
    setSpeaking(true)
    hapticFeedback?.('impact')
    
    try {
      // Try server voice first
      const formData = new FormData()
      formData.append('text', text)
      
      const resp = await fetch(`${VOICE_BASE}/speak`, {
        method: 'POST',
        body: formData,
      })
      
      if (resp.ok && audioRef.current) {
        const blob = await resp.blob()
        const url = URL.createObjectURL(blob)
        audioRef.current.src = url
        audioRef.current.play()
        audioRef.current.onended = () => {
          setSpeaking(false)
          URL.revokeObjectURL(url)
        }
      } else {
        // Server failed — use native/browser TTS
        await speakWithTTS(text)
      }
    } catch {
      // Server unreachable — use native/browser TTS
      await speakWithTTS(text)
    }
  }

  return (
    <div className={`flex flex-col ${fullScreen ? 'h-full' : 'space-y-3'}`}>
      <audio ref={audioRef} className="hidden" />
      
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-violet-600 flex items-center justify-center">
            <Heart size={14} className="text-white" />
          </div>
          <div>
            <p className="text-xs font-bold text-white">JARVIS Voice {MOOD_EMOJIS[mood]}</p>
            <p className="text-[9px] text-slate-500">Hindi Sweet Assistant • Always Smiling</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={`p-1.5 rounded-lg ${voiceEnabled ? 'bg-violet-600/20 text-violet-400' : 'bg-slate-800 text-slate-500'}`}
          >
            {voiceEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
          </button>
          {isOwner && (
            <span className="text-[9px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full font-bold">
              👑 OWNER
            </span>
          )}
        </div>
      </div>

      {/* Chat History */}
      <div className={`flex-1 overflow-y-auto space-y-2 ${fullScreen ? 'px-1' : ''}`} 
           style={{ maxHeight: fullScreen ? 'calc(100vh - 280px)' : '300px' }}>
        
        {chatHistory.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-pink-500/20 to-violet-600/20 flex items-center justify-center mb-3">
              <SmilePlus size={28} className="text-pink-400" />
            </div>
            <p className="text-sm font-medium text-slate-300">Namaste! Main JARVIS hoon 😊</p>
            <p className="text-xs text-slate-500 mt-1">Hindi mein baat karo, voice ya text — dono chalega! 💕</p>
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              {['Market kaisa hai?', 'Nifty predict karo', 'Good morning!', 'Best stocks batao'].map(q => (
                <button key={q}
                  onClick={() => { setTextInput(q); getAIResponse(q); }}
                  className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded-full hover:border-violet-500 hover:text-violet-400 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatHistory.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-3 py-2 ${
              msg.role === 'user' 
                ? 'bg-violet-600/80 text-white rounded-br-sm' 
                : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-sm'
            }`}>
              {msg.role === 'assistant' && msg.mood && (
                <span className="text-[9px] text-pink-400 font-medium">
                  JARVIS {MOOD_EMOJIS[msg.mood] || '😊'}
                </span>
              )}
              <p className="text-[13px] leading-relaxed">{msg.text}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-[8px] opacity-50">
                  {msg.time ? new Date(msg.time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
                {msg.role === 'assistant' && (
                  <button 
                    onClick={() => speakText(msg.text)}
                    className="text-violet-400 hover:text-violet-300"
                  >
                    <Volume2 size={10} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {thinking && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '400ms' }} />
                </div>
                <span className="text-[10px] text-slate-500">Soch rahi hoon... 🤔</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </div>

      {/* Mic Button */}
      <div className="flex items-center justify-center py-3">
        <button 
          onClick={listening ? stopListening : startListening}
          disabled={thinking}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all active:scale-90 shadow-lg ${
            listening
              ? 'bg-red-500 shadow-red-500/30 animate-pulse'
              : speaking
              ? 'bg-pink-500 shadow-pink-500/30 animate-pulse'
              : 'bg-gradient-to-br from-pink-500 to-violet-600 shadow-violet-500/30 hover:shadow-violet-500/50'
          } disabled:opacity-50`}
        >
          {thinking ? <Loader size={24} className="animate-spin text-white" /> :
           listening ? <MicOff size={24} className="text-white" /> :
           speaking ? <Volume2 size={24} className="text-white animate-pulse" /> :
           <Mic size={24} className="text-white" />}
        </button>
      </div>
      
      <p className="text-center text-[9px] text-slate-600">
        {listening ? '🎤 Sun rahi hoon... Bol dijiye!' :
         speaking ? '🔊 Bol rahi hoon... 💕' :
         thinking ? '🤔 Soch rahi hoon...' :
         '🎙️ Tap karke boliye ya niche type kariye'}
      </p>

      {/* Text Input */}
      <form onSubmit={handleTextSubmit} className="flex items-center gap-2 mt-1">
        <input 
          value={textInput} 
          onChange={e => setTextInput(e.target.value)}
          placeholder={placeholder}
          disabled={thinking}
          className="flex-1 bg-slate-800 rounded-xl px-3 py-2.5 text-sm outline-none border border-slate-700 focus:border-pink-500 transition-colors placeholder-slate-600"
        />
        <button 
          type="submit"
          disabled={thinking || !textInput.trim()}
          className="p-2.5 bg-gradient-to-br from-pink-500 to-violet-600 rounded-xl disabled:opacity-50 active:scale-90 transition-transform"
        >
          {thinking ? <Loader size={16} className="animate-spin text-white" /> : <Send size={16} className="text-white" />}
        </button>
      </form>
    </div>
  )
}

export default HindiVoiceAssistant
