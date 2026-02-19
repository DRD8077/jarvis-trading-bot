import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AppContext = createContext(null)

export const useApp = () => useContext(AppContext)

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [theme, setTheme] = useState('light')
  const [notifications, setNotifications] = useState([])
  const [isOnline, setIsOnline] = useState(true)

  const tg = window.Telegram?.WebApp

  useEffect(() => {
    // Initialize Telegram WebApp
    if (tg) {
      tg.ready()
      tg.expand()
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user)
      }
      tg.setHeaderColor('#0a0e1a')
      tg.setBackgroundColor('#0a0e1a')
    } else {
      // APK / Browser fallback — generate a persistent device ID
      let deviceId = localStorage.getItem('jarvis_device_id')
      if (!deviceId) {
        deviceId = String(Math.floor(100000000 + Math.random() * 900000000))
        localStorage.setItem('jarvis_device_id', deviceId)
      }
      setUser({ id: Number(deviceId), first_name: 'JARVIS User', last_name: '', username: 'jarvis_user' })
    }

    // Online/offline detection
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const addNotification = useCallback((msg, type = 'info') => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, msg, type }])
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 4000)
  }, [])

  const hapticFeedback = useCallback((type = 'impact') => {
    if (tg?.HapticFeedback) {
      if (type === 'impact') tg.HapticFeedback.impactOccurred('medium')
      else if (type === 'success') tg.HapticFeedback.notificationOccurred('success')
      else if (type === 'error') tg.HapticFeedback.notificationOccurred('error')
    }
  }, [])

  return (
    <AppContext.Provider value={{
      user, theme, setTheme, notifications, addNotification,
      isOnline, hapticFeedback, tg
    }}>
      {children}
      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-[9999] space-y-2">
        {notifications.map(n => (
          <div key={n.id} className={`px-4 py-2 rounded-lg text-sm font-medium text-white shadow-lg animate-slide-in ${
            n.type === 'success' ? 'bg-emerald-500' : n.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
          }`}>
            {n.msg}
          </div>
        ))}
      </div>
    </AppContext.Provider>
  )
}
