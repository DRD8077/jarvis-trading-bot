import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Settings, Bot, Send, Globe, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import jarvisVoice from '../services/jarvisVoice'
import systemControl from '../services/systemControl'

const VoiceCommand = () => {
  const navigate = useNavigate()
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [conversation, setConversation] = useState([])
  const [language, setLanguage] = useState('hi-IN')
  const [textInput, setTextInput] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    if (!jarvisVoice._initialized) {
      jarvisVoice.init()
    }

    jarvisVoice.on('result', async ({ text, isFinal }) => {
      setTranscript(text)
      if (isFinal && text.trim()) {
        await handleCommand(text.trim())
        setTranscript('')
      }
    })

    jarvisVoice.on('stateChange', (state) => {
      setIsListening(state === 'listening')
      setIsSpeaking(state === 'speaking')
    })

    return () => {
      jarvisVoice.stopListening()
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation])

  const handleCommand = async (text) => {
    setConversation(prev => [...prev, { role: 'user', text, time: new Date() }])

    // Try system control first
    const sysResult = await systemControl.executeNaturalCommand(text)
    if (sysResult) {
      const reply = sysResult.response
      setConversation(prev => [...prev, { role: 'jarvis', text: reply, time: new Date() }])
      jarvisVoice.speak(reply, language)
      return
    }

    // Try voice command handler
    const result = await jarvisVoice.handleCommand(text)
    if (result) {
      setConversation(prev => [...prev, { role: 'jarvis', text: result.response, time: new Date() }])
      jarvisVoice.speak(result.response, language)
    } else {
      const fallback = language === 'hi-IN'
        ? `Sir, "${text}" ke baare mein main soch raha hoon... Abhi ye feature develop ho raha hai.`
        : `Sir, I'm thinking about "${text}"... This feature is being enhanced.`
      setConversation(prev => [...prev, { role: 'jarvis', text: fallback, time: new Date() }])
      jarvisVoice.speak(fallback, language)
    }
  }

  const toggleListening = () => {
    if (isListening) {
      jarvisVoice.stopListening()
    } else {
      jarvisVoice.startListening(language)
    }
  }

  const handleTextSubmit = async (e) => {
    e.preventDefault()
    if (!textInput.trim()) return
    await handleCommand(textInput.trim())
    setTextInput('')
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white flex flex-col">
      {/* Header */}
      <div className="p-4 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-slate-400 hover:text-white">
            <ArrowLeft size={20} />
          </button>
          <Bot className="text-cyan-400" size={24} />
          <div>
            <h1 className="font-bold text-lg">JARVIS Voice</h1>
            <p className="text-xs text-slate-400">
              {isListening ? '🔴 Listening...' : isSpeaking ? '🔵 Speaking...' : '⚪ Ready'}
            </p>
          </div>
        </div>
        <button
          onClick={() => setLanguage(l => l === 'hi-IN' ? 'en-IN' : 'hi-IN')}
          className="flex items-center gap-1 px-3 py-1 rounded-full bg-slate-800 text-xs"
        >
          <Globe size={14} />
          {language === 'hi-IN' ? 'हिंदी' : 'English'}
        </button>
      </div>

      {/* Conversation */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {conversation.length === 0 && (
          <div className="text-center py-12 space-y-4">
            <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Bot size={40} />
            </div>
            <h2 className="text-xl font-bold">JARVIS Voice Assistant</h2>
            <p className="text-slate-400 text-sm max-w-xs mx-auto">
              {language === 'hi-IN'
                ? 'Mujhse Hindi ya English mein baat karo. Main aapki har command samajhta hoon!'
                : 'Talk to me in Hindi or English. I understand all your commands!'}
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-xs mx-auto text-xs">
              {[
                '"Bitcoin price kya hai?"',
                '"Open Chrome"',
                '"Portfolio dikhao"',
                '"Buy BTC 100 dollars"',
                '"Market kaisa hai?"',
                '"Battery kitna hai?"',
              ].map((cmd, i) => (
                <button
                  key={i}
                  onClick={() => handleCommand(cmd.replace(/"/g, ''))}
                  className="px-3 py-2 bg-slate-800 rounded-lg text-slate-300 hover:bg-slate-700"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        )}

        {conversation.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] px-4 py-3 rounded-2xl ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-sm'
                : 'bg-slate-800 text-slate-200 rounded-bl-sm'
            }`}>
              {msg.role === 'jarvis' && <span className="text-cyan-400 text-xs font-bold block mb-1">🤖 JARVIS</span>}
              <p className="text-sm">{msg.text}</p>
              <p className="text-[10px] opacity-50 mt-1">
                {msg.time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {transcript && (
          <div className="flex justify-end">
            <div className="max-w-[80%] px-4 py-3 rounded-2xl bg-blue-600/50 text-white/70 rounded-br-sm">
              <p className="text-sm italic">{transcript}...</p>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <form onSubmit={handleTextSubmit} className="flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={language === 'hi-IN' ? 'Type ya bolo...' : 'Type or speak...'}
            className="flex-1 bg-slate-800 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <button type="submit" className="bg-cyan-600 p-3 rounded-xl hover:bg-cyan-500">
            <Send size={18} />
          </button>
        </form>

        <div className="flex items-center justify-center">
          <button
            onClick={toggleListening}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
              isListening
                ? 'bg-red-500 animate-pulse shadow-lg shadow-red-500/50'
                : 'bg-gradient-to-br from-cyan-500 to-blue-600 hover:shadow-lg hover:shadow-cyan-500/50'
            }`}
          >
            {isListening ? <MicOff size={28} /> : <Mic size={28} />}
          </button>
        </div>

        {isListening && (
          <p className="text-center text-xs text-red-400 animate-pulse">
            {language === 'hi-IN' ? '🎤 Sun raha hoon... Boliye sir!' : '🎤 Listening... Speak sir!'}
          </p>
        )}
      </div>
    </div>
  )
}

export default VoiceCommand
