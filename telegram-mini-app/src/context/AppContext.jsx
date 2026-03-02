import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
// NO static service imports — all loaded dynamically to prevent crashes

const AppContext = createContext(null)

export const useApp = () => useContext(AppContext)

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [theme, setTheme] = useState('dark')
  const gmailAuthRef = useRef(null)
  const themeEngineRef = useRef(null)
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
    try { if (themeEngineRef.current) { themeEngineRef.current.setTheme(themeId); setTheme(themeId) } } catch {}
  }, [])

  const toggleTheme = useCallback(() => {
    try { if (themeEngineRef.current) { const next = themeEngineRef.current.toggle(); setTheme(next); return next } } catch {}
    return theme
  }, [theme])

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
    // Dynamically load gmailAuth and themeEngine — crash-proof
    let unsubscribe = () => {}
    async function loadServices() {
      // ═══ STEP 1: Check localStorage for saved session ═══
      try {
        const savedToken = localStorage.getItem('jarvis_access_token')
        const savedUserStr = localStorage.getItem('jarvis_user') || localStorage.getItem('jarvis_gmail_user')
        if (savedToken && savedUserStr) {
          const savedUser = JSON.parse(savedUserStr)
          if (savedUser && savedUser.username) {
            console.log('[JARVIS] Restored session for:', savedUser.username)
            setUser(savedUser)
            setIsLoggedIn(true)
            setIsAdmin(savedUser.isAdmin || savedUser.role === 'admin' || false)
            setAuthLoading(false)
            // Still load theme below, but auth is done
          }
        }
      } catch (e) { console.warn('[JARVIS] session restore:', e.message) }

      // ═══ STEP 2: If no saved session, auto-login as owner ═══
      if (!user) {
        try {
          const { SERVER_BASE } = await import('../services/apiBase')
          const serverUrl = SERVER_BASE || ''
          const resp = await fetch(`${serverUrl}/api/auth/auto-login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: 'jarvis-apk' })
          })
          if (resp.ok) {
            const data = await resp.json()
            if (data.success && data.user) {
              const ownerUser = {
                id: data.user.id,
                name: data.user.username,
                username: data.user.username,
                email: data.user.email || '',
                role: data.user.role || 'admin',
                isAdmin: data.user.isAdmin || data.user.role === 'admin',
                avatar: data.user.username[0].toUpperCase(),
                isRealAuth: true,
              }
              // Save to localStorage
              localStorage.setItem('jarvis_access_token', data.access_token)
              localStorage.setItem('jarvis_refresh_token', data.refresh_token)
              localStorage.setItem('jarvis_user', JSON.stringify(ownerUser))
              localStorage.setItem('jarvis_gmail_user', JSON.stringify(ownerUser))
              localStorage.setItem('jarvis_gmail_token', data.access_token)
              
              setUser(ownerUser)
              setIsLoggedIn(true)
              setIsAdmin(true)
              console.log('[JARVIS] ✅ Owner auto-logged in as ADMIN:', ownerUser.username)
            }
          }
        } catch (e) {
          console.warn('[JARVIS] Auto-login failed (server offline?):', e.message)
          // Fallback: still try gmailAuth below
        }
      }

      // ═══ STEP 3: Legacy gmailAuth (fallback) ═══
      try {
        const gmod = await import('../services/gmailAuth').catch(() => null)
        const ga = gmod?.default || gmod
        if (ga) {
          gmailAuthRef.current = ga
          if (!user) {
            const savedUser = typeof ga.getCurrentUser === 'function'
              ? ga.getCurrentUser()
              : ga.getUser?.() || ga.user || null
            if (savedUser) {
              setUser(savedUser)
              setIsLoggedIn(true)
              setIsAdmin(savedUser.isAdmin || false)
            }
          }
          if (typeof ga.onAuthChange === 'function') {
            unsubscribe = ga.onAuthChange((authUser) => {
              if (authUser) { setUser(authUser); setIsLoggedIn(true); setIsAdmin(authUser.isAdmin || false) }
              else { setUser(null); setIsLoggedIn(false); setIsAdmin(false) }
            })
          }
        }
      } catch (e) { console.warn('[JARVIS] gmailAuth load:', e.message) }
      try {
        const tmod = await import('../services/themeEngine').catch(() => null)
        const te = tmod?.default || tmod
        if (te) {
          themeEngineRef.current = te
          setTheme(typeof te.getTheme === 'function' ? te.getTheme() : 'dark')
        }
      } catch (e) { console.warn('[JARVIS] themeEngine load:', e.message) }
      setAuthLoading(false)
    }
    loadServices()

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
    try { if (gmailAuthRef.current) gmailAuthRef.current.logout() } catch {}
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
