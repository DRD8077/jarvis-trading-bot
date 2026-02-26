import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import gmailAuth from '../services/gmailAuth'
import themeEngine from '../services/themeEngine'

const AppContext = createContext(null)

export const useApp = () => useContext(AppContext)

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [theme, setTheme] = useState(themeEngine.getTheme())
  const [notifications, setNotifications] = useState([])
  const [isOnline, setIsOnline] = useState(true)
  const [onboardingDone, setOnboardingDone] = useState(
    localStorage.getItem('jarvis_onboarding_done') === 'true'
  )
  const [paperTradingMode, setPaperTradingMode] = useState(
    localStorage.getItem('jarvis_paper_mode') === 'true'
  )

  // Theme change handler
  const changeTheme = useCallback((themeId) => {
    themeEngine.setTheme(themeId)
    setTheme(themeId)
  }, [])

  const toggleTheme = useCallback(() => {
    const next = themeEngine.toggle()
    setTheme(next)
    return next
  }, [])

  const completeOnboarding = useCallback(() => {
    localStorage.setItem('jarvis_onboarding_done', 'true')
    setOnboardingDone(true)
  }, [])

  const togglePaperTrading = useCallback(() => {
    setPaperTradingMode(prev => {
      const next = !prev
      localStorage.setItem('jarvis_paper_mode', String(next))
      return next
    })
  }, [])

  useEffect(() => {
    // Check for saved Gmail/manual login (defensive: fallback if method missing)
    const savedUser = typeof gmailAuth.getCurrentUser === 'function'
      ? gmailAuth.getCurrentUser()
      : gmailAuth.getUser?.() || gmailAuth.user || null

    if (savedUser) {
      setUser(savedUser)
      setIsLoggedIn(true)
      setIsAdmin(savedUser.isAdmin || false)
    }
    // else: not logged in, show LoginScreen

    setAuthLoading(false)

    // Listen for auth changes (login/logout from gmailAuth)
    const unsubscribe = gmailAuth.onAuthChange((authUser) => {
      if (authUser) {
        setUser(authUser)
        setIsLoggedIn(true)
        setIsAdmin(authUser.isAdmin || false)
      } else {
        setUser(null)
        setIsLoggedIn(false)
        setIsAdmin(false)
      }
    })

    // Online/offline detection
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      unsubscribe()
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const handleLogin = useCallback((loggedInUser) => {
    setUser(loggedInUser)
    setIsLoggedIn(true)
    setIsAdmin(loggedInUser.isAdmin || false)
  }, [])

  const handleLogout = useCallback(() => {
    gmailAuth.logout()
    setUser(null)
    setIsLoggedIn(false)
    setIsAdmin(false)
  }, [])

  const addNotification = useCallback((msg, type = 'info') => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, msg, type }])
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 4000)
  }, [])

  const hapticFeedback = useCallback((type = 'impact') => {
    // Native vibration for haptic feedback
    if (window.navigator?.vibrate) {
      if (type === 'impact') window.navigator.vibrate(20)
      else if (type === 'success') window.navigator.vibrate([10, 30, 10])
      else if (type === 'error') window.navigator.vibrate([50, 20, 50])
    }
  }, [])

  return (
    <AppContext.Provider value={{
      user, isLoggedIn, isAdmin, authLoading,
      handleLogin, handleLogout,
      theme, setTheme: changeTheme, toggleTheme, notifications, addNotification,
      isOnline, hapticFeedback,
      onboardingDone, completeOnboarding,
      paperTradingMode, togglePaperTrading
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
