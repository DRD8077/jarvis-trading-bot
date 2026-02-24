/**
 * 🎨 JARVIS Signal Share Card
 * ═════════════════════════════
 * Generate beautiful trade signal image cards
 * Share on WhatsApp, Instagram, Telegram
 * Uses HTML Canvas for image generation
 */
import React, { useRef, useState } from 'react'
import { Share2, Download, Image, X, Copy, Check } from 'lucide-react'
import { useApp } from '../context/AppContext'

const SignalShareCard = ({ signal, onClose }) => {
  const { addNotification, hapticFeedback } = useApp()
  const canvasRef = useRef(null)
  const [generating, setGenerating] = useState(false)
  const [imageUrl, setImageUrl] = useState(null)

  // Default signal if none provided
  const s = signal || {
    symbol: 'BTCUSDT',
    action: 'BUY',
    entry: 67500,
    target: 72000,
    stopLoss: 65000,
    confidence: 87,
    timeframe: '4H',
    reason: 'Bullish breakout above 67K resistance with strong volume',
  }

  const generateCard = async () => {
    setGenerating(true)
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const W = 600, H = 400
    canvas.width = W
    canvas.height = H

    // Background
    const bgGrad = ctx.createLinearGradient(0, 0, W, H)
    bgGrad.addColorStop(0, '#0a0e1a')
    bgGrad.addColorStop(0.5, '#111827')
    bgGrad.addColorStop(1, '#0a0e1a')
    ctx.fillStyle = bgGrad
    ctx.fillRect(0, 0, W, H)

    // Decorative elements
    ctx.globalAlpha = 0.1
    ctx.fillStyle = s.action === 'BUY' ? '#10b981' : '#ef4444'
    ctx.beginPath()
    ctx.arc(W * 0.8, H * 0.2, 120, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(W * 0.2, H * 0.8, 80, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = 1

    // Border
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.3)'
    ctx.lineWidth = 2
    ctx.roundRect?.(10, 10, W - 20, H - 20, 16) || ctx.rect(10, 10, W - 20, H - 20)
    ctx.stroke()

    // Header — JARVIS AI
    ctx.fillStyle = '#8b5cf6'
    ctx.font = 'bold 14px system-ui'
    ctx.fillText('🤖 JARVIS AI SIGNAL', 30, 45)

    // Timestamp
    ctx.fillStyle = '#64748b'
    ctx.font = '11px system-ui'
    ctx.textAlign = 'right'
    ctx.fillText(new Date().toLocaleString(), W - 30, 45)
    ctx.textAlign = 'left'

    // Divider
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(30, 60)
    ctx.lineTo(W - 30, 60)
    ctx.stroke()

    // Symbol + Action Badge
    ctx.fillStyle = '#f1f5f9'
    ctx.font = 'bold 32px system-ui'
    ctx.fillText(s.symbol, 30, 105)

    // Action badge
    const badgeColor = s.action === 'BUY' ? '#10b981' : '#ef4444'
    const badgeText = s.action === 'BUY' ? '🟢 BUY' : '🔴 SELL'
    ctx.fillStyle = badgeColor + '33'
    ctx.beginPath()
    const bw = ctx.measureText(badgeText).width + 24
    ctx.roundRect?.(W - bw - 30, 78, bw, 32, 8) || ctx.rect(W - bw - 30, 78, bw, 32)
    ctx.fill()
    ctx.fillStyle = badgeColor
    ctx.font = 'bold 16px system-ui'
    ctx.fillText(badgeText, W - bw - 18, 100)

    // Price levels
    const levels = [
      { label: 'Entry Price', value: `₹${s.entry.toLocaleString()}`, color: '#3b82f6' },
      { label: 'Target', value: `₹${s.target.toLocaleString()}`, color: '#10b981' },
      { label: 'Stop Loss', value: `₹${s.stopLoss.toLocaleString()}`, color: '#ef4444' },
    ]

    levels.forEach((l, i) => {
      const x = 30 + i * 185
      const y = 140

      // Background box
      ctx.fillStyle = l.color + '15'
      ctx.beginPath()
      ctx.roundRect?.(x, y, 170, 55, 8) || ctx.rect(x, y, 170, 55)
      ctx.fill()

      // Left accent
      ctx.fillStyle = l.color
      ctx.fillRect(x, y + 4, 3, 47)

      ctx.fillStyle = '#94a3b8'
      ctx.font = '10px system-ui'
      ctx.fillText(l.label, x + 12, y + 20)
      ctx.fillStyle = '#f1f5f9'
      ctx.font = 'bold 18px system-ui'
      ctx.fillText(l.value, x + 12, y + 44)
    })

    // Confidence + Timeframe
    const confY = 220
    ctx.fillStyle = '#1e293b'
    ctx.beginPath()
    ctx.roundRect?.(30, confY, W - 60, 45, 8) || ctx.rect(30, confY, W - 60, 45)
    ctx.fill()

    // Confidence bar
    ctx.fillStyle = '#3b82f620'
    ctx.beginPath()
    ctx.roundRect?.(45, confY + 12, 200, 20, 6) || ctx.rect(45, confY + 12, 200, 20)
    ctx.fill()
    
    const confGrad = ctx.createLinearGradient(45, 0, 45 + s.confidence * 2, 0)
    confGrad.addColorStop(0, '#3b82f6')
    confGrad.addColorStop(1, '#8b5cf6')
    ctx.fillStyle = confGrad
    ctx.beginPath()
    ctx.roundRect?.(45, confY + 12, s.confidence * 2, 20, 6) || ctx.rect(45, confY + 12, s.confidence * 2, 20)
    ctx.fill()

    ctx.fillStyle = '#fff'
    ctx.font = 'bold 12px system-ui'
    ctx.fillText(`${s.confidence}% Confidence`, 55, confY + 27)

    ctx.fillStyle = '#94a3b8'
    ctx.font = '12px system-ui'
    ctx.textAlign = 'right'
    ctx.fillText(`⏱ ${s.timeframe} Timeframe`, W - 45, confY + 27)
    ctx.textAlign = 'left'

    // Reason
    if (s.reason) {
      ctx.fillStyle = '#64748b'
      ctx.font = '11px system-ui'
      const maxWidth = W - 60
      const words = s.reason.split(' ')
      let line = ''
      let y = 295
      for (const word of words) {
        const test = line + word + ' '
        if (ctx.measureText(test).width > maxWidth) {
          ctx.fillText(line.trim(), 30, y)
          line = word + ' '
          y += 16
        } else {
          line = test
        }
      }
      if (line.trim()) ctx.fillText(line.trim(), 30, y)
    }

    // Footer
    ctx.fillStyle = '#334155'
    ctx.beginPath()
    ctx.roundRect?.(30, H - 50, W - 60, 35, 8) || ctx.rect(30, H - 50, W - 60, 35)
    ctx.fill()

    ctx.fillStyle = '#94a3b8'
    ctx.font = '11px system-ui'
    ctx.fillText('🤖 Generated by JARVIS AI Trading Bot', 45, H - 28)
    ctx.textAlign = 'right'
    ctx.fillStyle = '#6366f1'
    ctx.fillText('t.me/jarvisai_bot', W - 45, H - 28)
    ctx.textAlign = 'left'

    // Convert to image
    const url = canvas.toDataURL('image/png')
    setImageUrl(url)
    setGenerating(false)
  }

  // Auto-generate on mount
  React.useEffect(() => { generateCard() }, [])

  const shareImage = async () => {
    if (!imageUrl) return
    hapticFeedback('impact')

    try {
      const blob = await (await fetch(imageUrl)).blob()
      const file = new File([blob], `jarvis_signal_${s.symbol}.png`, { type: 'image/png' })

      if (navigator.share) {
        await navigator.share({
          title: `JARVIS Signal: ${s.action} ${s.symbol}`,
          text: `🤖 JARVIS AI Signal\n${s.action} ${s.symbol}\nEntry: ₹${s.entry}\nTarget: ₹${s.target}\nSL: ₹${s.stopLoss}\nConfidence: ${s.confidence}%`,
          files: [file]
        })
        addNotification('📤 Shared successfully!', 'success')
      } else {
        // Fallback: download
        downloadImage()
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        downloadImage()
      }
    }
  }

  const downloadImage = () => {
    if (!imageUrl) return
    const a = document.createElement('a')
    a.href = imageUrl
    a.download = `jarvis_signal_${s.symbol}_${Date.now()}.png`
    a.click()
    addNotification('📥 Signal card downloaded!', 'success')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div className="relative bg-slate-900 border border-slate-700 rounded-2xl p-4 w-full max-w-md animate-fade-up" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <Image size={14} className="text-blue-400" /> Signal Card
          </h3>
          <button onClick={onClose} className="p-1 bg-slate-800 rounded-full">
            <X size={14} className="text-slate-400" />
          </button>
        </div>

        {/* Canvas (hidden, for generation) */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Preview */}
        {imageUrl && (
          <img src={imageUrl} alt="Signal Card" className="w-full rounded-xl border border-slate-700 mb-3" />
        )}

        {generating && (
          <div className="h-48 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button onClick={shareImage} className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors">
            <Share2 size={14} /> Share
          </button>
          <button onClick={downloadImage} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors">
            <Download size={14} /> Download
          </button>
        </div>
      </div>
    </div>
  )
}

export default SignalShareCard
