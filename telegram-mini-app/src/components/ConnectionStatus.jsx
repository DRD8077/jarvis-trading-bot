import React, { useState, useEffect, useRef } from 'react'
import { Wifi, WifiOff, Zap, RefreshCw } from 'lucide-react'
// NO static service imports — loaded dynamically

/**
 * 🟢 Connection Status Bar — Shows real-time connection health
 * Appears at top of app, auto-hides when healthy
 */
const ConnectionStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [wsConnected, setWsConnected] = useState(false)
  const [showStatus, setShowStatus] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const handleOnline = () => { setIsOnline(true); setShowStatus(true); setTimeout(() => setShowStatus(false), 2000) }
    const handleOffline = () => { setIsOnline(false); setShowStatus(true) }
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Dynamically load realtime service
    let unsub = null
    import('../services/realtime').then(mod => {
      const rt = mod?.default
      if (rt && typeof rt.subscribe === 'function') {
        unsub = rt.subscribe('_status', (data) => {
          setWsConnected(data?.connected || false)
        })
      }
    }).catch(() => {})

    // Show briefly on mount to confirm connected
    setShowStatus(true)
    const hideTimer = setTimeout(() => setShowStatus(false), 3000)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      unsub?.()
      clearTimeout(hideTimer)
    }
  }, [])

  const handleForceRefresh = () => {
    setRefreshing(true)
    import('../services/autoRefreshEngine').then(mod => {
      const ar = mod?.default
      if (ar && typeof ar.forceRefresh === 'function') ar.forceRefresh()
    }).catch(() => {})
    setTimeout(() => setRefreshing(false), 1000)
  }

  // Always show when offline
  if (!isOnline) {
    return (
      <div className="fixed top-0 left-0 right-0 z-[100] bg-red-600/95 backdrop-blur-sm px-4 py-2 flex items-center justify-between text-white text-xs font-medium animate-slide-down">
        <div className="flex items-center gap-2">
          <WifiOff size={14} />
          <span>Offline — Reconnecting...</span>
        </div>
      </div>
    )
  }

  if (!showStatus) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-emerald-600/90 backdrop-blur-sm px-4 py-1.5 flex items-center justify-between text-white text-xs font-medium animate-slide-down"
      style={{ animation: 'slideDown 0.2s ease-out' }}>
      <div className="flex items-center gap-2">
        <Wifi size={12} />
        <span>Connected</span>
        {wsConnected && <Zap size={10} className="text-yellow-300" />}
      </div>
      <button onClick={handleForceRefresh} className="p-1 rounded active:scale-90">
        <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
      </button>
    </div>
  )
}

export default ConnectionStatus
