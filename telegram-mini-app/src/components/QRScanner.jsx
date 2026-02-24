/**
 * 📷 JARVIS QR Code Scanner
 * ═══════════════════════════
 * Scan QR codes for wallet addresses
 * Uses device camera via getUserMedia
 * Supports: Wallet addresses, Payment URIs, URLs
 */
import React, { useState, useRef, useEffect } from 'react'
import { Camera, X, Copy, Check, QrCode, ExternalLink, Wallet, ArrowLeft } from 'lucide-react'
import { useApp } from '../context/AppContext'

const QRScanner = ({ onScan, onClose }) => {
  const { addNotification, hapticFeedback } = useApp()
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)
  const animFrameRef = useRef(null)

  useEffect(() => {
    startCamera()
    return () => stopCamera()
  }, [])

  const startCamera = async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
        setScanning(true)
        scanFrame()
      }
    } catch (e) {
      setError('Camera access denied. Please allow camera permission.')
      console.error('[QR] Camera error:', e)
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
    }
    setScanning(false)
  }

  const scanFrame = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      // Use BarcodeDetector API if available
      if ('BarcodeDetector' in window) {
        const detector = new BarcodeDetector({ formats: ['qr_code'] })
        detector.detect(canvas).then(barcodes => {
          if (barcodes.length > 0) {
            handleResult(barcodes[0].rawValue)
            return
          }
        }).catch(() => {})
      }

      // Fallback: try reading ImageData for simple QR patterns
      // (Full QR decoding needs a library, but BarcodeDetector covers most Android devices)
    }

    animFrameRef.current = requestAnimationFrame(scanFrame)
  }

  const handleResult = (value) => {
    stopCamera()
    setResult(value)
    hapticFeedback('success')
    
    if (onScan) onScan(value)
  }

  const copyResult = () => {
    navigator.clipboard?.writeText(result)
    setCopied(true)
    hapticFeedback('impact')
    addNotification('📋 Copied to clipboard!', 'success')
    setTimeout(() => setCopied(false), 2000)
  }

  const getResultType = (val) => {
    if (!val) return 'text'
    if (val.match(/^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/)) return 'btc'
    if (val.match(/^0x[0-9a-fA-F]{40}$/)) return 'eth'
    if (val.match(/^[1-9A-HJ-NP-Za-km-z]{32,44}$/)) return 'sol'
    if (val.startsWith('http')) return 'url'
    if (val.includes('@')) return 'upi'
    return 'text'
  }

  const resultType = getResultType(result)
  const resultLabel = {
    btc: '₿ Bitcoin Address',
    eth: 'Ξ Ethereum Address',
    sol: '◎ Solana Address',
    url: '🔗 URL',
    upi: '💳 UPI ID',
    text: '📝 Text'
  }[resultType]

  const handleClose = () => {
    stopCamera()
    if (onClose) onClose()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 backdrop-blur-xl z-10">
        <button onClick={handleClose} className="flex items-center gap-2 text-white">
          <ArrowLeft size={20} />
          <span className="text-sm font-medium">Back</span>
        </button>
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <QrCode size={16} /> QR Scanner
        </h2>
        <div className="w-16" />
      </div>

      {/* Camera View */}
      {!result && (
        <div className="flex-1 relative">
          <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
          <canvas ref={canvasRef} className="hidden" />

          {/* Scanning overlay */}
          {scanning && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-64 h-64 relative">
                {/* Corner brackets */}
                <div className="absolute top-0 left-0 w-8 h-8 border-t-3 border-l-3 border-blue-500 rounded-tl-lg" />
                <div className="absolute top-0 right-0 w-8 h-8 border-t-3 border-r-3 border-blue-500 rounded-tr-lg" />
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-3 border-l-3 border-blue-500 rounded-bl-lg" />
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-3 border-r-3 border-blue-500 rounded-br-lg" />
                {/* Scanning line */}
                <div className="absolute left-2 right-2 h-0.5 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-scan" />
              </div>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="text-center p-6">
                <Camera size={48} className="text-slate-600 mx-auto mb-4" />
                <p className="text-red-400 text-sm">{error}</p>
                <button onClick={startCamera} className="mt-4 px-4 py-2 bg-blue-600 rounded-xl text-sm font-medium">
                  Try Again
                </button>
              </div>
            </div>
          )}

          {/* Hint */}
          <div className="absolute bottom-8 left-0 right-0 text-center">
            <p className="text-white/60 text-xs">Point camera at QR code</p>
          </div>
        </div>
      )}

      {/* Result View */}
      {result && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-sm">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl p-5 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <QrCode size={16} className="text-blue-400" />
                <span className="text-xs text-blue-400 font-medium">{resultLabel}</span>
              </div>
              <p className="text-white text-sm break-all font-mono bg-slate-800 p-3 rounded-xl">
                {result}
              </p>
            </div>

            <div className="flex gap-3">
              <button onClick={copyResult}
                className="flex-1 py-3 bg-blue-600 rounded-xl font-bold text-sm flex items-center justify-center gap-2">
                {copied ? <><Check size={16} /> Copied</> : <><Copy size={16} /> Copy</>}
              </button>
              {resultType === 'url' && (
                <button onClick={() => window.open(result, '_blank')}
                  className="py-3 px-4 bg-slate-800 rounded-xl">
                  <ExternalLink size={16} className="text-slate-400" />
                </button>
              )}
            </div>

            <button onClick={() => { setResult(null); startCamera() }}
              className="w-full mt-3 py-3 bg-slate-800 rounded-xl text-sm text-slate-300 font-medium">
              Scan Again
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes scan {
          0% { top: 10%; }
          50% { top: 85%; }
          100% { top: 10%; }
        }
        .animate-scan { animation: scan 2s ease-in-out infinite; }
      `}</style>
    </div>
  )
}

export default QRScanner
