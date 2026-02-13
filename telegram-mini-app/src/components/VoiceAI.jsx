import React, { useState, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Loader, Send, Sparkles } from 'lucide-react'
import { voiceGenerate, voiceTranscribe } from '../services/api'
import { useApp } from '../context/AppContext'

const VoiceAI = ({ onTranscript }) => {
  const { addNotification, hapticFeedback } = useApp()
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [ttsText, setTtsText] = useState('')
  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  // Start voice recording
  const startListening = async () => {
    hapticFeedback('impact')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
        await transcribeAudio(blob)
      }

      mediaRecorder.start()
      setListening(true)
      addNotification('🎤 Listening...', 'info')
    } catch (e) {
      addNotification('Microphone access denied', 'error')
      hapticFeedback('error')
    }
  }

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    setListening(false)
    hapticFeedback('impact')
  }

  const transcribeAudio = async (blob) => {
    setGenerating(true)
    try {
      const formData = new FormData()
      formData.append('audio', blob, 'recording.webm')
      const res = await voiceTranscribe(formData)
      const text = res?.data?.data?.text || res?.data?.text || ''
      setTranscript(text)
      if (onTranscript) onTranscript(text)
      addNotification('Transcription complete!', 'success')
    } catch (e) {
      addNotification('Transcription failed', 'error')
    } finally { setGenerating(false) }
  }

  const handleSpeak = async (text) => {
    if (!text) return
    setSpeaking(true)
    hapticFeedback('impact')
    try {
      const res = await voiceGenerate(text)
      const audioUrl = res?.data?.data?.audio_url || res?.data?.audio_url
      if (audioUrl && audioRef.current) {
        audioRef.current.src = audioUrl
        audioRef.current.play()
        audioRef.current.onended = () => setSpeaking(false)
      } else {
        setSpeaking(false)
      }
    } catch (e) {
      addNotification('Voice generation failed', 'error')
      setSpeaking(false)
    }
  }

  return (
    <div className="space-y-3">
      <audio ref={audioRef} className="hidden" />

      {/* Mic Button */}
      <div className="flex items-center justify-center">
        <button onClick={listening ? stopListening : startListening}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all active:scale-90 shadow-lg ${
            listening
              ? 'bg-red-500 shadow-red-500/30 animate-pulse'
              : 'bg-gradient-to-br from-violet-600 to-purple-600 shadow-violet-500/30'
          }`}>
          {generating ? <Loader size={24} className="animate-spin" /> :
           listening ? <MicOff size={24} /> : <Mic size={24} />}
        </button>
      </div>

      <p className="text-center text-[10px] text-slate-500">
        {listening ? 'Tap to stop recording...' :
         generating ? 'Transcribing...' :
         'Tap to speak to JARVIS'}
      </p>

      {/* Transcript */}
      {transcript && (
        <div className="bg-slate-800 border border-violet-500/20 rounded-xl p-3">
          <p className="text-[10px] text-violet-400 mb-1">You said:</p>
          <p className="text-sm">{transcript}</p>
        </div>
      )}

      {/* TTS Input */}
      <div className="flex items-center space-x-2">
        <input value={ttsText} onChange={e => setTtsText(e.target.value)}
          placeholder="Type text for JARVIS to speak..."
          className="flex-1 bg-slate-800 rounded-xl px-3 py-2 text-sm outline-none border border-slate-700 focus:border-violet-500" />
        <button onClick={() => handleSpeak(ttsText)} disabled={speaking || !ttsText}
          className="p-2.5 bg-violet-600 rounded-xl disabled:opacity-50 active:scale-90">
          {speaking ? <Volume2 size={16} className="animate-pulse" /> : <Sparkles size={16} />}
        </button>
      </div>
    </div>
  )
}

export default VoiceAI
