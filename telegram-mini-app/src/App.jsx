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
import backgroundAlerts from './services/backgroundAlerts'
import offlineCache from './services/offlineCache'
import firebasePush from './services/firebasePush'
import crashAnalytics from './services/crashAnalytics'
import deepLink from './services/deepLink'
import useSwipeNavigation from './hooks/useSwipeNavigation'
// v6.0 IRON MAN: Self-sufficient JARVIS core services
import jarvis from './services/jarvisCore'
import serviceMesh from './services/serviceMesh'
import multiSource from './services/multiSourceData'
import wsHub from './services/wsHub'
import offlineEngine from './services/offlineEngine'
import { API_BASE } from './services/apiBase'
// Direct server connection — no Telegram dependency

// Lazy load pages for performance
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
// NEW: Pro features
const PaperTrading = lazy(() => import('./components/PaperTrading'))
const PnLJournal = lazy(() => import('./components/PnLJournal'))
// v5.1: Super power features
const Watchlist = lazy(() => import('./components/Watchlist'))
const AlertRulesEngine = lazy(() => import('./components/AlertRulesEngine'))
const DepthChart = lazy(() => import('./components/DepthChart'))
const TaxCalculator = lazy(() => import('./components/TaxCalculator'))
// v6.0 IRON MAN: JARVIS Command Center
const JarvisCommandCenter = lazy(() => import('./components/JarvisCommandCenter'))

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

// Inner app that can use context hooks
function AppInner() {
  const { isLoggedIn, authLoading, handleLogin, onboardingDone, completeOnboarding } = useApp()

  const [showSplash, setShowSplash] = useState(() => {
    return !sessionStorage.getItem('jarvis_splash_shown')
  })

  useEffect(() => {
    console.log('[JARVIS v6.0 IRON MAN] Booting autonomous systems...')
    // Initialize crash analytics
    crashAnalytics.init()
    crashAnalytics.addBreadcrumb('app', 'App loaded — v6.0 IRON MAN')
    // === v6.0: Initialize JARVIS Core ===
    jarvis.init(API_BASE)
    // Start self-healing service mesh
    serviceMesh.registerService({ name: 'backend-api', endpoint: `${API_BASE}/health`, criticalLevel: 'critical', interval: 30000 })
    serviceMesh.registerService({ name: 'coingecko', endpoint: 'https://api.coingecko.com/api/v3/ping', criticalLevel: 'high' })
    serviceMesh.registerService({ name: 'binance', endpoint: 'https://api.binance.com/api/v3/ping', criticalLevel: 'normal' })
    serviceMesh.start(30000)
    // Start multi-source data aggregator
    multiSource.startAutoRefresh()
    // Connect WebSocket hub
    wsHub.connect([`${API_BASE.replace('http', 'ws')}/ws`, 'wss://stream.binance.com:9443/ws'])
    // Initialize offline engine
    offlineEngine.init()
    console.log('[JARVIS v6.0] All autonomous systems ONLINE ⚡')
    // Start background price alert engine
    backgroundAlerts.start(15000)
    // Pre-cache essentials for offline mode
    import('./services/api').then(api => {
      offlineCache.preCacheEssentials(api).catch(() => {})
    }).catch(() => {})
    // Initialize Firebase push notifications
    firebasePush.init().then(token => {
      if (token) console.log('[JARVIS] Firebase push ready')
    }).catch(() => {})
    // Register for periodic background sync (where supported)
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.ready.then(reg => {
        if (reg.periodicSync) {
          reg.periodicSync.register('jarvis-price-check', { minInterval: 15 * 60 * 1000 }).catch(() => {})
        }
      })
    }
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

  // Activate deep link router
  useEffect(() => {
    deepLink.activate(navigate)
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
