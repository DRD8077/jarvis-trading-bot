import React, { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import Navigation from './components/Navigation'
import LiveTicker from './components/LiveTicker'
import InstallPrompt from './components/InstallPrompt'
import otaUpdater from './services/otaUpdater'
import jarvisAuth from './services/smartAuth'

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

function App() {
  // 🔄 OTA Silent Update + 🔐 Auto-Login on mount
  useEffect(() => {
    otaUpdater.silentUpdate()
    jarvisAuth.autoLogin().catch(() => {})
  }, [])

  return (
    <AppProvider>
      <Router basename="/miniapp">
        <div className="min-h-screen bg-slate-900">
          <LiveTicker />
          <Suspense fallback={<PageLoader />}>
            <main className="pb-safe">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/trading" element={<Trading />} />
                <Route path="/wallet" element={<Wallet />} />
                <Route path="/chat" element={<AIChat />} />
                <Route path="/auto-trader" element={<AutoTrader />} />
                <Route path="/gems" element={<GemScanner />} />
                <Route path="/screener" element={<Screener />} />
                <Route path="/intelligence" element={<Intelligence />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/phantom" element={<PhantomWallet />} />
                <Route path="/copy-trading" element={<CopyTrading />} />
                <Route path="/social" element={<SocialFeed />} />
                <Route path="/options" element={<OptionsChain />} />
                <Route path="/portfolio" element={<PortfolioAnalytics />} />
                <Route path="/whales" element={<WhaleAlerts />} />
                <Route path="/backtest" element={<BacktestBuilder />} />
                <Route path="/indian-stocks" element={<IndianStocks />} />
                <Route path="/nifty-options" element={<NiftyOptionsLive />} />
                <Route path="/candle-indicators" element={<CandleIndicators />} />
                <Route path="/power-predictor" element={<PowerPredictor />} />
                <Route path="/intraday-scanner" element={<IntradayScanner />} />
                <Route path="/options-pro" element={<OptionsProLive />} />
                <Route path="/strategy-builder" element={<StrategyBuilder />} />
                <Route path="/risk-manager" element={<RiskManager />} />
                <Route path="/mega-trader" element={<MegaTrader />} />
                <Route path="/voice" element={<HindiVoice fullScreen />} />
              </Routes>
            </main>
          </Suspense>
          <Navigation />
          <InstallPrompt />
        </div>
      </Router>
    </AppProvider>
  )
}

export default App
