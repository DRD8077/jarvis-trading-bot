import React, { useState, useEffect } from 'react'
import { Download, X, Smartphone, Zap, Shield, Wifi } from 'lucide-react'

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [show, setShow] = useState(false)
  const [installed, setInstalled] = useState(false)

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
      setInstalled(true)
      return
    }

    const handler = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      // Show prompt after 5 seconds
      setTimeout(() => setShow(true), 5000)
    }

    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', () => { setInstalled(true); setShow(false) })

    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') setInstalled(true)
    setDeferredPrompt(null)
    setShow(false)
  }

  if (installed || !show) return null

  return (
    <div className="fixed bottom-20 left-3 right-3 z-[9998] animate-slide-up">
      <div className="bg-gradient-to-r from-blue-600/95 to-purple-600/95 backdrop-blur-xl rounded-2xl p-4 shadow-2xl border border-white/10">
        <button onClick={() => setShow(false)} className="absolute top-3 right-3 text-white/60 hover:text-white">
          <X size={18} />
        </button>
        
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center flex-shrink-0">
            <Smartphone size={24} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-white font-bold text-sm">Install JARVIS App</h3>
            <p className="text-white/70 text-xs mt-0.5">Get native app experience — No download needed!</p>
            <div className="flex items-center gap-3 mt-2 text-[10px] text-white/50">
              <span className="flex items-center gap-1"><Zap size={10} />Instant</span>
              <span className="flex items-center gap-1"><Shield size={10} />Secure</span>
              <span className="flex items-center gap-1"><Wifi size={10} />Live Updates</span>
            </div>
          </div>
        </div>
        
        <button 
          onClick={handleInstall}
          className="w-full mt-3 py-2.5 bg-white text-blue-700 rounded-xl font-bold text-sm flex items-center justify-center gap-2 active:scale-95 transition-transform"
        >
          <Download size={16} /> Install Now — Free
        </button>
      </div>
    </div>
  )
}
