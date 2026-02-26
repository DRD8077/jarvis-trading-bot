/**
 * 📸 JARVIS Chart Capture + Share Engine
 * ═══════════════════════════════════════
 * 
 * One-tap chart screenshot with signal overlay.
 * Shareable as image to WhatsApp/Telegram/Twitter.
 * Uses Canvas API — zero external dependencies.
 */

class ChartCaptureEngine {
  constructor() {
    try {
        this.watermark = 'JARVIS AI Trading • jarvis.trading'
  
    } catch(e) {
      console.warn('[chartCapture] Constructor init error:', e)
    }
}

  // ═══════════════════════════════════
  // CAPTURE ELEMENT AS IMAGE
  // ═══════════════════════════════════

  async captureElement(element, options = {}) {
    if (!element) throw new Error('No element provided')

    const canvas = document.createElement('canvas')
    const rect = element.getBoundingClientRect()
    const scale = options.scale || 2 // Retina quality

    canvas.width = rect.width * scale
    canvas.height = (rect.height + 60) * scale // Extra space for watermark
    const ctx = canvas.getContext('2d')
    ctx.scale(scale, scale)

    // Dark background
    ctx.fillStyle = '#0a0e1a'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Use html2canvas-like approach using SVG foreignObject
    try {
      const data = await this._elementToImage(element, rect)
      ctx.drawImage(data, 0, 0, rect.width, rect.height)
    } catch {
      // Fallback: just draw a placeholder
      ctx.fillStyle = '#1e293b'
      ctx.fillRect(10, 10, rect.width - 20, rect.height - 20)
      ctx.fillStyle = '#94a3b8'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('Chart Capture', rect.width / 2, rect.height / 2)
    }

    // Add signal overlay if provided
    if (options.signal) {
      this._drawSignalOverlay(ctx, options.signal, rect)
    }

    // Add watermark
    this._drawWatermark(ctx, rect)

    return canvas
  }

  async _elementToImage(element, rect) {
    return new Promise((resolve, reject) => {
      const svgData = `
        <svg xmlns="http://www.w3.org/2000/svg" width="${rect.width}" height="${rect.height}">
          <foreignObject width="100%" height="100%">
            <div xmlns="http://www.w3.org/1999/xhtml">
              ${element.outerHTML}
            </div>
          </foreignObject>
        </svg>`
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('SVG render failed'))
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData)
    })
  }

  _drawSignalOverlay(ctx, signal, rect) {
    const y = rect.height - 80
    const isBuy = signal.direction === 'BUY'

    // Signal badge
    ctx.fillStyle = isBuy ? 'rgba(34, 197, 94, 0.9)' : 'rgba(239, 68, 68, 0.9)'
    ctx.beginPath()
    ctx.roundRect(10, y, 200, 70, 8)
    ctx.fill()

    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 16px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`${isBuy ? '🟢 BUY' : '🔴 SELL'} ${signal.symbol}`, 20, y + 22)

    ctx.font = '12px sans-serif'
    ctx.fillText(`Entry: $${signal.entry || 'Market'}`, 20, y + 40)
    ctx.fillText(`Target: $${signal.target || '-'} | SL: $${signal.stopLoss || '-'}`, 20, y + 55)
    ctx.fillText(`Confidence: ${signal.confidence || '-'}%`, 20, y + 68)
  }

  _drawWatermark(ctx, rect) {
    const y = rect.height + 10
    ctx.fillStyle = '#1e293b'
    ctx.fillRect(0, rect.height, rect.width, 60)

    ctx.fillStyle = '#3b82f6'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('🤖 JARVIS AI Trading', 10, y + 20)

    ctx.fillStyle = '#64748b'
    ctx.font = '10px sans-serif'
    ctx.fillText(new Date().toLocaleString(), 10, y + 38)

    ctx.textAlign = 'right'
    ctx.fillStyle = '#475569'
    ctx.fillText('JARVIS v6.0 IRON MAN', rect.width - 10, y + 20)
  }

  // ═══════════════════════════════════
  // GENERATE SIGNAL CARD IMAGE
  // ═══════════════════════════════════

  generateSignalCard(signal) {
    const canvas = document.createElement('canvas')
    const w = 400, h = 250
    canvas.width = w * 2
    canvas.height = h * 2
    const ctx = canvas.getContext('2d')
    ctx.scale(2, 2)

    const isBuy = signal.direction === 'BUY'

    // Background gradient
    const grad = ctx.createLinearGradient(0, 0, w, h)
    grad.addColorStop(0, '#0f172a')
    grad.addColorStop(1, isBuy ? '#052e16' : '#450a0a')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, w, h)

    // Border
    ctx.strokeStyle = isBuy ? '#22c55e' : '#ef4444'
    ctx.lineWidth = 2
    ctx.strokeRect(1, 1, w - 2, h - 2)

    // Header
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 24px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`${isBuy ? '🟢' : '🔴'} ${signal.direction} SIGNAL`, w / 2, 35)

    // Symbol
    ctx.font = 'bold 28px sans-serif'
    ctx.fillStyle = isBuy ? '#4ade80' : '#f87171'
    ctx.fillText(signal.symbol || 'BTC/USDT', w / 2, 70)

    // Details
    ctx.font = '16px sans-serif'
    ctx.fillStyle = '#e2e8f0'
    ctx.textAlign = 'left'

    const details = [
      ['Entry Price', `$${signal.entry || 'Market'}`],
      ['Target', `$${signal.target || '-'}`],
      ['Stop Loss', `$${signal.stopLoss || '-'}`],
      ['Confidence', `${signal.confidence || '-'}%`],
      ['Risk:Reward', signal.rr || '1:2'],
    ]

    details.forEach(([label, value], i) => {
      const y = 100 + i * 24
      ctx.fillStyle = '#94a3b8'
      ctx.fillText(label, 20, y)
      ctx.fillStyle = '#ffffff'
      ctx.textAlign = 'right'
      ctx.fillText(value, w - 20, y)
      ctx.textAlign = 'left'
    })

    // Footer
    ctx.fillStyle = '#475569'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`🤖 JARVIS AI Trading • ${new Date().toLocaleString()}`, w / 2, h - 10)

    return canvas
  }

  // ═══════════════════════════════════
  // SHARE
  // ═══════════════════════════════════

  async shareImage(canvas, title = 'JARVIS Signal') {
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    const file = new File([blob], 'jarvis-signal.png', { type: 'image/png' })

    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      try {
        await navigator.share({
          title,
          text: '🤖 JARVIS AI Trading Signal',
          files: [file]
        })
        return { shared: true, method: 'native' }
      } catch (e) {
        if (e.name === 'AbortError') return { shared: false, reason: 'cancelled' }
      }
    }

    // Fallback: download
    return this.downloadImage(canvas)
  }

  downloadImage(canvas, filename = 'jarvis-signal.png') {
    const link = document.createElement('a')
    link.download = filename
    link.href = canvas.toDataURL('image/png')
    link.click()
    return { shared: true, method: 'download' }
  }

  async shareToWhatsApp(canvas, text = '') {
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    const url = URL.createObjectURL(blob)
    window.open(`https://wa.me/?text=${encodeURIComponent(text + '\n' + url)}`, '_blank')
    return { shared: true, method: 'whatsapp' }
  }

  async shareToTelegram(canvas, text = '') {
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    const url = URL.createObjectURL(blob)
    window.open(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`, '_blank')
    return { shared: true, method: 'telegram' }
  }

  copyToClipboard(canvas) {
    canvas.toBlob(blob => {
      try {
        navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
        return { copied: true }
      } catch {
        return { copied: false }
      }
    })
  }
}

const chartCapture = new ChartCaptureEngine()
export default chartCapture
export { ChartCaptureEngine }
