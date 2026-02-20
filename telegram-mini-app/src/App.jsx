import React, { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AppProvider, useApp } from './context/AppContext'
import Navigation from './components/Navigation'
import LiveTicker from './components/LiveTicker'
import InstallPrompt from './components/InstallPrompt'
import LoginScreen from './components/LoginScreen'
import ErrorBoundary from './components/ErrorBoundary'
import ConnectionStatus from './components/ConnectionStatus'
import backgroundAlerts from './services/backgroundAlerts'
import offlineCache from './services/offlineCache'
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
  const { isLoggedIn, authLoading, handleLogin } = useApp()

  useEffect(() => {
    console.log('[JARVIS] App loaded — standalone mode')
    // Start background price alert engine
    backgroundAlerts.start(15000)
    // Pre-cache essentials for offline mode
    import('./services/api').then(api => {
      offlineCache.preCacheEssentials(api).catch(() => {})
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

  // Gate: Show login screen if not authenticated
  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <Router>
      <div className="min-h-screen bg-slate-900">
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
              </Routes>
            </main>
          </Suspense>
        </ErrorBoundary>
        <Navigation />
        <InstallPrompt />
      </div>
    </Router>
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
