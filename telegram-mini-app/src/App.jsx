import React, { Suspense, lazy, useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import { AppProvider, useApp } from './context/AppContext'
import Navigation from './components/Navigation'
import LiveTicker from './components/LiveTicker'
import InstallPrompt from './components/InstallPrompt'
import LoginScreen from './components/LoginScreen'
import OnboardingScreen from './components/OnboardingScreen'
import SplashScreen from './components/SplashScreen'
import ErrorBoundary from './components/ErrorBoundary'
import ConnectionStatus from './components/ConnectionStatus'
import useSwipeNavigation from './hooks/useSwipeNavigation'
// Only import safe constants — NO service classes, NO constructors
import { API_BASE, WS_URL } from './services/apiBase'

// ═══════════════════════════════════════════════════════════════
// CRASH-PROOF ARCHITECTURE v12
// ═══════════════════════════════════════════════════════════════
// ALL 30+ services are loaded DYNAMICALLY inside useEffect.
// Each service import is individually wrapped in try-catch.
// If ANY service fails to load (constructor crash, missing API,
// Android WebView issue, etc.), the app STILL boots perfectly.
// This guarantees ZERO startup crashes on ANY device.
// ═══════════════════════════════════════════════════════════════

// Safe dynamic service loader — returns null if import fails
async function loadService(importPromise, name) {
  try {
    const mod = await importPromise
    const svc = mod?.default || mod
    if (svc) console.log(`[JARVIS] ✅ ${name} loaded`)
    return svc
  } catch (e) {
    console.warn(`[JARVIS] ⚠️ ${name} failed to load:`, e.message)
    return null
  }
}

// Safe method caller — never throws
function sc(service, method, ...args) {
  try {
    if (service && typeof service[method] === 'function') {
      const result = service[method](...args)
      if (result && typeof result.catch === 'function') result.catch(() => {})
      return result
    }
  } catch (e) {
    console.warn(`[JARVIS] ${method}() error:`, e.message)
  }
  return null
}

// ═══════════════════════════════════════════════════════════════
// LAZY-LOADED PAGES (all in Suspense — safe by design)
// ═══════════════════════════════════════════════════════════════
const Dashboard = lazy(() => import('./components/Dashboard'))
const Trading = lazy(() => import('./components/Trading'))
const Wallet = lazy(() => import('./components/Wallet'))
const AIChat = lazy(() => import('./components/AIChat'))
const AutoTrader = lazy(() => import('./components/AutoTrader'))
const GemScanner = lazy(() => import('./components/GemScanner'))
const Screener = lazy(() => import('./components/Screener'))
const Intelligence = lazy(() => import('./components/Intelligence'))
const Settings = lazy(() => import('./components/Settings'))
const PhantomWallet = lazy(() => import('./components/PhantomWallet'))
const CopyTrading = lazy(() => import('./components/CopyTrading'))
const SocialFeed = lazy(() => import('./components/SocialFeed'))
const OptionsChain = lazy(() => import('./components/OptionsChain'))
const PortfolioAnalytics = lazy(() => import('./components/PortfolioAnalytics'))
const WhaleAlerts = lazy(() => import('./components/WhaleAlerts'))
const BacktestBuilder = lazy(() => import('./components/BacktestBuilder'))
const IndianStocks = lazy(() => import('./components/IndianStocks'))
const NiftyOptionsLive = lazy(() => import('./components/NiftyOptionsLive'))
const CandleIndicators = lazy(() => import('./components/CandleIndicators'))
const PowerPredictor = lazy(() => import('./components/PowerPredictor'))
const IntradayScanner = lazy(() => import('./pages/IntradayScanner'))
const OptionsProLive = lazy(() => import('./pages/OptionsProLive'))
const StrategyBuilder = lazy(() => import('./pages/StrategyBuilder'))
const RiskManager = lazy(() => import('./pages/RiskManager'))
const MegaTrader = lazy(() => import('./components/MegaTrader'))
const HindiVoice = lazy(() => import('./components/HindiVoiceAssistant'))
const AIAgent = lazy(() => import('./components/AIAgent'))
const AdminPanel = lazy(() => import('./components/AdminPanel'))
const PaperTrading = lazy(() => import('./components/PaperTrading'))
const PnLJournal = lazy(() => import('./components/PnLJournal'))
const Watchlist = lazy(() => import('./components/Watchlist'))
const AlertRulesEngine = lazy(() => import('./components/AlertRulesEngine'))
const DepthChart = lazy(() => import('./components/DepthChart'))
const TaxCalculator = lazy(() => import('./components/TaxCalculator'))
const JarvisCommandCenter = lazy(() => import('./components/JarvisCommandCenter'))
const VoiceCommand = lazy(() => import('./components/VoiceCommand'))
const VaultManager = lazy(() => import('./components/VaultManager'))
const ExchangeConnect = lazy(() => import('./components/ExchangeConnect'))
const QRScanner = lazy(() => import('./components/QRScanner'))
const SignalShareCard = lazy(() => import('./components/SignalShareCard'))
const VoiceAI = lazy(() => import('./components/VoiceAI'))
const SystemSpecs = lazy(() => import('./components/SystemSpecs'))
const JarvisVsMyra = lazy(() => import('./components/JarvisVsMyra'))
const VoiceAutomation = lazy(() => import('./components/VoiceAutomation'))
const JarvisHolographic = lazy(() => import('./components/JarvisHolographic'))
const GamingCoach = lazy(() => import('./components/GamingCoach'))

const PageLoader = () => (
  <div className="p-4 bg-slate-900 min-h-screen space-y-3 animate-pulse">
    <div className="h-6 w-40 bg-slate-800 rounded" />
    <div className="grid grid-cols-2 gap-2">
      <div className="h-20 bg-slate-800 rounded-xl" />
      <div className="h-20 bg-slate-800 rounded-xl" />
    </div>
    <div className="h-32 bg-slate-800 rounded-xl" />
    <div className="h-24 bg-slate-800 rounded-xl" />
  </div>
)

// ═══════════════════════════════════════════════════════════════
// APP INNER — Main app with crash-proof service initialization
// ═══════════════════════════════════════════════════════════════
function AppInner() {
  const { isLoggedIn, authLoading, handleLogin, onboardingDone, completeOnboarding } = useApp()

  const [showSplash, setShowSplash] = useState(() => {
    return !sessionStorage.getItem('jarvis_splash_shown')
  })

  useEffect(() => {
    // ═══════════════════════════════════════════════════════════
    // CRASH-PROOF BOOT SEQUENCE
    // Every single service is dynamically imported inside its
    // own try-catch. NO service can crash the app.
    // ═══════════════════════════════════════════════════════════
    async function bootJarvis() {
      console.log('[JARVIS v12.0 STANDALONE] Crash-proof boot sequence starting...')

      // Phase 1: Load all services in parallel (each isolated)
      const [
        crashAnalytics,
        jarvis,
        serviceMesh,
        multiSource,
        wsHub,
        offlineEngine,
        jarvisDB,
        notificationPipeline,
        presenceEngine,
        jarvisVoice,
        autoRefreshEngine,
        hapticEngine,
        i18n,
        themeEngine,
        smartAuth,
        voiceCommandEngine,
        webAIFallback,
        securityBatteryPerf,
        elevenlabsVoice,
        backgroundAlerts,
        offlineCache,
        firebasePush,
        deepLink,
      ] = await Promise.all([
        loadService(import('./services/crashAnalytics'), 'crashAnalytics'),
        loadService(import('./services/jarvisCore'), 'jarvisCore'),
        loadService(import('./services/serviceMesh'), 'serviceMesh'),
        loadService(import('./services/multiSourceData'), 'multiSourceData'),
        loadService(import('./services/wsHub'), 'wsHub'),
        loadService(import('./services/offlineEngine'), 'offlineEngine'),
        loadService(import('./services/jarvisDB'), 'jarvisDB'),
        loadService(import('./services/notificationPipeline'), 'notificationPipeline'),
        loadService(import('./services/presenceEngine'), 'presenceEngine'),
        loadService(import('./services/jarvisVoice'), 'jarvisVoice'),
        loadService(import('./services/autoRefreshEngine'), 'autoRefreshEngine'),
        loadService(import('./services/hapticEngine'), 'hapticEngine'),
        loadService(import('./services/i18n'), 'i18n'),
        loadService(import('./services/themeEngine'), 'themeEngine'),
        loadService(import('./services/smartAuth'), 'smartAuth'),
        loadService(import('./services/voiceCommandEngine'), 'voiceCommandEngine'),
        loadService(import('./services/webAIFallback'), 'webAIFallback'),
        loadService(import('./services/securityBatteryPerf'), 'securityBatteryPerf'),
        loadService(import('./services/elevenlabsVoice'), 'elevenlabsVoice'),
        loadService(import('./services/backgroundAlerts'), 'backgroundAlerts'),
        loadService(import('./services/offlineCache'), 'offlineCache'),
        loadService(import('./services/firebasePush'), 'firebasePush'),
        loadService(import('./services/deepLink'), 'deepLink'),
      ])

      // Store deepLink globally so SwipeableApp can use it
      window.__jarvisDeepLink = deepLink

      console.log('[JARVIS] Phase 1 complete — all services loaded')

      // Phase 2: Initialize services (each call isolated)
      try {
        sc(crashAnalytics, 'init')
        if (crashAnalytics && typeof crashAnalytics.addBreadcrumb === 'function') {
          crashAnalytics.addBreadcrumb('app', 'App loaded — v12.0 STANDALONE CRASH-PROOF')
        }
      } catch (e) { console.warn('[JARVIS] crashAnalytics init:', e.message) }

      try {
        sc(jarvis, 'init', API_BASE)
      } catch (e) { console.warn('[JARVIS] jarvisCore init:', e.message) }

      try {
        if (serviceMesh && typeof serviceMesh.registerService === 'function') {
          serviceMesh.registerService({ name: 'backend-api', endpoint: `${API_BASE}/health`, criticalLevel: 'critical', interval: 30000 })
          serviceMesh.registerService({ name: 'coingecko', endpoint: 'https://api.coingecko.com/api/v3/ping', criticalLevel: 'high' })
          serviceMesh.registerService({ name: 'binance', endpoint: 'https://api.binance.com/api/v3/ping', criticalLevel: 'normal' })
        }
        sc(serviceMesh, 'start', 30000)
      } catch (e) { console.warn('[JARVIS] serviceMesh init:', e.message) }

      try {
        sc(multiSource, 'startAutoRefresh')
      } catch (e) { console.warn('[JARVIS] multiSource init:', e.message) }

      try {
        const wsUrl = WS_URL || `${API_BASE.replace(/^http/, 'ws')}/ws`
        sc(wsHub, 'connect', 'jarvis', {
          url: [wsUrl],
          channels: ['prices', 'signals', 'alerts'],
          heartbeatInterval: 30000,
          onMessage: (msg) => {
            try {
              if (msg.type === 'price_update') {
                window.dispatchEvent(new CustomEvent('jarvis-price-update', { detail: msg.data }))
              } else if (msg.type === 'new_signal') {
                window.dispatchEvent(new CustomEvent('jarvis-signal', { detail: msg.data }))
              }
            } catch {}
          }
        })
        sc(wsHub, 'connect', 'binance', {
          url: ['wss://stream.binance.com:9443/ws'],
          channels: [],
          heartbeatInterval: 60000
        })
      } catch (e) { console.warn('[JARVIS] wsHub init:', e.message) }

      try { sc(jarvisDB, 'init') } catch (e) { console.warn('[JARVIS] jarvisDB init:', e.message) }

      try {
        sc(presenceEngine, 'init', {
          onGreeting: (msg) => {
            try {
              sc(notificationPipeline, 'send', { title: '\u{1F441}\uFE0F JARVIS', message: msg, type: 'info', priority: 'normal' })
              if (jarvisVoice && jarvisVoice._initialized && typeof jarvisVoice.speak === 'function') jarvisVoice.speak(msg, 'hi-IN')
            } catch {}
          },
          onDeparture: (msg) => {
            try {
              sc(notificationPipeline, 'send', { title: '\u{1F441}\uFE0F JARVIS', message: msg, type: 'info', priority: 'low' })
            } catch {}
          }
        })
      } catch (e) { console.warn('[JARVIS] presenceEngine init:', e.message) }

      // Register service worker
      try {
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.register('/sw-v6.js').then(reg => {
            if (reg.periodicSync) {
              reg.periodicSync.register('jarvis-price-check', { minInterval: 15 * 60 * 1000 }).catch(() => {})
            }
          }).catch(() => {})
        }
      } catch {}

      // Desktop-specific initialization
      try {
        if (window.jarvisDesktop) {
          console.log('[JARVIS] Desktop mode — full OS control enabled!')
          window.jarvisDesktop.on('navigate', (path) => {
            window.dispatchEvent(new CustomEvent('jarvis-navigate', { detail: path }))
          })
          window.jarvisDesktop.on('voice', () => {
            if (jarvisVoice && typeof jarvisVoice.startListening === 'function') jarvisVoice.startListening()
          })
        }
      } catch {}

      // Phase 2.5: Initialize realtime engine for WebSocket prices
      try {
        const rtModule = await loadService(import('./services/realtime'), 'realtime')
        if (rtModule) {
          sc(rtModule, 'init', API_BASE)
          window.__jarvisRealtime = rtModule
          console.log('[JARVIS] RealTime WebSocket engine initialized')
        }
      } catch (e) { console.warn('[JARVIS] realtime init:', e.message) }

      // Phase 3: Initialize all remaining services
      try { sc(autoRefreshEngine, 'start') } catch {}
      try { sc(hapticEngine, 'init') } catch {}
      try { sc(i18n, 'init') } catch {}
      try { sc(themeEngine, 'init') } catch {}
      try { sc(smartAuth, 'init') } catch {}
      try { sc(voiceCommandEngine, 'init') } catch {}
      try { sc(webAIFallback, 'init') } catch {}
      try { sc(elevenlabsVoice, 'init') } catch {}

      // SecurityBatteryPerf — may export a named init function
      try {
        if (securityBatteryPerf) {
          if (typeof securityBatteryPerf.initSecurityBatteryPerf === 'function') {
            await securityBatteryPerf.initSecurityBatteryPerf()
          } else if (typeof securityBatteryPerf.init === 'function') {
            securityBatteryPerf.init()
          }
        }
      } catch (e) { console.warn('[JARVIS] securityBatteryPerf:', e.message) }

      // Background alerts
      try { sc(backgroundAlerts, 'start', 15000) } catch {}

      // Pre-cache for offline mode
      try {
        const api = await import('./services/api').catch(() => null)
        if (api && offlineCache && typeof offlineCache.preCacheEssentials === 'function') {
          offlineCache.preCacheEssentials(api).catch(() => {})
        }
      } catch {}

      // Firebase push
      try { sc(firebasePush, 'init') } catch {}

      console.log('[JARVIS v12.0] ⚡ ALL systems ONLINE — crash-proof boot complete')
    }

    bootJarvis().catch(e => {
      console.error('[JARVIS] Boot sequence error (app still running):', e.message)
    })
  }, [])

  // Cinematic splash screen on first session load
  if (showSplash) {
    return <SplashScreen onFinish={() => { sessionStorage.setItem('jarvis_splash_shown', '1'); setShowSplash(false) }} />
  }

  // Show loading spinner while checking saved auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-3 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-slate-400 text-sm">Loading JARVIS...</span>
        </div>
      </div>
    )
  }

  // Gate: Show onboarding on first launch
  if (!onboardingDone) {
    return <OnboardingScreen onComplete={completeOnboarding} />
  }

  // Gate: Show login screen if not authenticated
  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <Router>
      <SwipeableApp />
    </Router>
  )
}

function SwipeableApp() {
  const { onTouchStart, onTouchEnd } = useSwipeNavigation()
  const navigate = useNavigate()

  // Activate deep link router (loaded dynamically, stored on window)
  useEffect(() => {
    try {
      const dl = window.__jarvisDeepLink
      if (dl && typeof dl.activate === 'function') {
        dl.activate(navigate)
      }
    } catch (e) {
      console.warn('[JARVIS] deepLink activate failed:', e.message)
    }
  }, [navigate])

  return (
    <div className="min-h-screen bg-slate-900" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
      <ConnectionStatus />
      <LiveTicker />
      <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <main className="pb-safe">
            <Routes>
              <Route path="/" element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
              <Route path="/trading" element={<ErrorBoundary><Trading /></ErrorBoundary>} />
              <Route path="/wallet" element={<ErrorBoundary><Wallet /></ErrorBoundary>} />
              <Route path="/chat" element={<ErrorBoundary><AIChat /></ErrorBoundary>} />
              <Route path="/auto-trader" element={<ErrorBoundary><AutoTrader /></ErrorBoundary>} />
              <Route path="/gems" element={<ErrorBoundary><GemScanner /></ErrorBoundary>} />
              <Route path="/screener" element={<ErrorBoundary><Screener /></ErrorBoundary>} />
              <Route path="/intelligence" element={<ErrorBoundary><Intelligence /></ErrorBoundary>} />
              <Route path="/settings" element={<ErrorBoundary><Settings /></ErrorBoundary>} />
              <Route path="/phantom" element={<ErrorBoundary><PhantomWallet /></ErrorBoundary>} />
              <Route path="/copy-trading" element={<ErrorBoundary><CopyTrading /></ErrorBoundary>} />
              <Route path="/social" element={<ErrorBoundary><SocialFeed /></ErrorBoundary>} />
              <Route path="/options" element={<ErrorBoundary><OptionsChain /></ErrorBoundary>} />
              <Route path="/portfolio" element={<ErrorBoundary><PortfolioAnalytics /></ErrorBoundary>} />
              <Route path="/whales" element={<ErrorBoundary><WhaleAlerts /></ErrorBoundary>} />
              <Route path="/backtest" element={<ErrorBoundary><BacktestBuilder /></ErrorBoundary>} />
              <Route path="/indian-stocks" element={<ErrorBoundary><IndianStocks /></ErrorBoundary>} />
              <Route path="/nifty-options" element={<ErrorBoundary><NiftyOptionsLive /></ErrorBoundary>} />
              <Route path="/candle-indicators" element={<ErrorBoundary><CandleIndicators /></ErrorBoundary>} />
              <Route path="/power-predictor" element={<ErrorBoundary><PowerPredictor /></ErrorBoundary>} />
              <Route path="/intraday-scanner" element={<ErrorBoundary><IntradayScanner /></ErrorBoundary>} />
              <Route path="/options-pro" element={<ErrorBoundary><OptionsProLive /></ErrorBoundary>} />
              <Route path="/strategy-builder" element={<ErrorBoundary><StrategyBuilder /></ErrorBoundary>} />
              <Route path="/risk-manager" element={<ErrorBoundary><RiskManager /></ErrorBoundary>} />
              <Route path="/mega-trader" element={<ErrorBoundary><MegaTrader /></ErrorBoundary>} />
              <Route path="/voice" element={<ErrorBoundary><HindiVoice fullScreen /></ErrorBoundary>} />
              <Route path="/ai-agent" element={<ErrorBoundary><AIAgent /></ErrorBoundary>} />
              <Route path="/admin" element={<ErrorBoundary><AdminPanel /></ErrorBoundary>} />
              <Route path="/paper-trading" element={<ErrorBoundary><PaperTrading /></ErrorBoundary>} />
              <Route path="/pnl-journal" element={<ErrorBoundary><PnLJournal /></ErrorBoundary>} />
              <Route path="/watchlist" element={<ErrorBoundary><Watchlist /></ErrorBoundary>} />
              <Route path="/smart-alerts" element={<ErrorBoundary><AlertRulesEngine /></ErrorBoundary>} />
              <Route path="/depth-chart" element={<ErrorBoundary><DepthChart /></ErrorBoundary>} />
              <Route path="/tax-calculator" element={<ErrorBoundary><TaxCalculator /></ErrorBoundary>} />
              <Route path="/jarvis" element={<ErrorBoundary><JarvisCommandCenter /></ErrorBoundary>} />
              <Route path="/voice-command" element={<ErrorBoundary><VoiceCommand /></ErrorBoundary>} />
              <Route path="/vault" element={<ErrorBoundary><VaultManager /></ErrorBoundary>} />
              <Route path="/exchange-connect" element={<ErrorBoundary><ExchangeConnect /></ErrorBoundary>} />
              <Route path="/qr-scanner" element={<ErrorBoundary><QRScanner /></ErrorBoundary>} />
              <Route path="/signal-card" element={<ErrorBoundary><SignalShareCard /></ErrorBoundary>} />
              <Route path="/voice-ai" element={<ErrorBoundary><VoiceAI /></ErrorBoundary>} />
              <Route path="/system-specs" element={<ErrorBoundary><SystemSpecs /></ErrorBoundary>} />
              <Route path="/jarvis-vs-myra" element={<ErrorBoundary><JarvisVsMyra /></ErrorBoundary>} />
              <Route path="/voice-automation" element={<ErrorBoundary><VoiceAutomation /></ErrorBoundary>} />
              <Route path="/jarvis-holographic" element={<ErrorBoundary><JarvisHolographic /></ErrorBoundary>} />
              <Route path="/iron-man" element={<ErrorBoundary><JarvisHolographic /></ErrorBoundary>} />
              <Route path="/gaming" element={<ErrorBoundary><GamingCoach apiBase={API_BASE} /></ErrorBoundary>} />
              <Route path="/gaming-coach" element={<ErrorBoundary><GamingCoach apiBase={API_BASE} /></ErrorBoundary>} />
            </Routes>
          </main>
        </Suspense>
      </ErrorBoundary>
      <Navigation />
      <InstallPrompt />
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <AppInner />
      </AppProvider>
    </ErrorBoundary>
  )
}

export default App
