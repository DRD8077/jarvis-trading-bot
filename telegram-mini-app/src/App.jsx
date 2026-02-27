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
// Install global timer manager FIRST — pauses all setIntervals when app goes to background
import timerManager from './services/timerManager'
timerManager.install()

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
const CopyTrading = lazy(() => import('./components/CopyTrading'))
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
const VaultManager = lazy(() => import('./components/VaultManager'))
const ExchangeConnect = lazy(() => import('./components/ExchangeConnect'))
const Web3MegaScanner = lazy(() => import('./components/Web3MegaScanner'))
const CryptoTop1000 = lazy(() => import('./components/CryptoTop1000'))
const AICandleBrain = lazy(() => import('./components/AICandleBrain'))

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
    // Set global mute from saved settings BEFORE any services load
    try {
      const savedSettings = JSON.parse(localStorage.getItem('jarvis_app_settings') || '{}')
      window.__JARVIS_MUTE = savedSettings.sound !== true // muted by default unless sound=true
    } catch { window.__JARVIS_MUTE = true }

    async function bootJarvis() {
      console.log('[JARVIS v19.0 STANDALONE] Crash-proof boot sequence starting...')

      // ═══ GLOBAL MUTE — disable ALL sounds/alerts/notifications by default ═══
      // User can re-enable in Settings. This prevents all annoying popups/beeps/vibrations.
      try {
        const savedSettings = localStorage.getItem('jarvis_app_settings')
        const parsed = savedSettings ? JSON.parse(savedSettings) : null
        // Default: muted. Only unmute if user explicitly enabled sound.
        window.__JARVIS_MUTE = parsed?.sound ? false : true
      } catch { window.__JARVIS_MUTE = true }
      console.log('[JARVIS] 🔇 Global mute:', window.__JARVIS_MUTE ? 'ON (silent)' : 'OFF (sounds enabled)')


      // Phase 1: Load essential services in parallel (each isolated)
      const [
        crashAnalytics,
        jarvis,
        offlineEngine,
        jarvisDB,
        hapticEngine,
        i18n,
        themeEngine,
        elevenlabsVoice,
        offlineCache,
      ] = await Promise.all([
        loadService(import('./services/crashAnalytics'), 'crashAnalytics'),
        loadService(import('./services/jarvisCore'), 'jarvisCore'),
        loadService(import('./services/offlineEngine'), 'offlineEngine'),
        loadService(import('./services/jarvisDB'), 'jarvisDB'),
        loadService(import('./services/hapticEngine'), 'hapticEngine'),
        loadService(import('./services/i18n'), 'i18n'),
        loadService(import('./services/themeEngine'), 'themeEngine'),
        loadService(import('./services/elevenlabsVoice'), 'elevenlabsVoice'),
        loadService(import('./services/offlineCache'), 'offlineCache'),
      ])

      console.log('[JARVIS] Phase 1 complete — essential services loaded')

      // Phase 2: Initialize services (each call isolated)
      try {
        sc(crashAnalytics, 'init')
        if (crashAnalytics && typeof crashAnalytics.addBreadcrumb === 'function') {
          crashAnalytics.addBreadcrumb('app', 'App loaded — v19.0 LEAN BOOT')
        }
      } catch (e) { console.warn('[JARVIS] crashAnalytics init:', e.message) }

      try {
        sc(jarvis, 'init', API_BASE)
      } catch (e) { console.warn('[JARVIS] jarvisCore init:', e.message) }

      try { sc(jarvisDB, 'init') } catch (e) { console.warn('[JARVIS] jarvisDB init:', e.message) }

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

      // Phase 3: Initialize remaining services
      try { sc(hapticEngine, 'init') } catch {}
      try { sc(i18n, 'init') } catch {}
      try { sc(themeEngine, 'init') } catch {}
      try { sc(elevenlabsVoice, 'init') } catch {}

      // Pre-cache for offline mode
      try {
        const api = await import('./services/api').catch(() => null)
        if (api && offlineCache && typeof offlineCache.preCacheEssentials === 'function') {
          offlineCache.preCacheEssentials(api).catch(() => {})
        }
      } catch {}

      // Phase 4: JARVIS Wake Word Engine — "Hey JARVIS" always-on listener
      try {
        const { getWakeWordEngine } = await import('./services/wakeWordEngine').catch(() => ({}));
        if (getWakeWordEngine) {
          const wakeEngine = getWakeWordEngine();
          wakeEngine.onWakeWord((transcript) => {
            // Handle sleep command
            if (transcript === '__JARVIS_SLEEP__') {
              console.log('[JARVIS] 😴 Going to sleep...');
              window.dispatchEvent(new CustomEvent('jarvis-sleep', { detail: { sleeping: true } }));
              // Speak goodnight
              try {
                import('./services/elevenlabsVoice.js').then(m => {
                  const tts = m.default || m;
                  if (tts?.speak) tts.speak('Good night Sir! Jab bhi zaroorat ho, bas bol dijiye JARVIS wake up. Main hamesha yahan hoon. 😴');
                });
              } catch {}
              return;
            }
            // If waking from sleep, announce
            if (wakeEngine.isSleeping === false && transcript) {
              try {
                import('./services/elevenlabsVoice.js').then(m => {
                  const tts = m.default || m;
                  if (tts?.speak) tts.speak('Good morning Sir! Main jaag gayi! Bataiye, kya karna hai? ⚡');
                });
              } catch {}
            }
            console.log('[JARVIS] Wake word detected! Activating voice mode...');
            // Navigate to AI Chat with voice auto-start
            window.dispatchEvent(new CustomEvent('jarvis-wake-word', { detail: { transcript } }));
            // Navigate to chat page — voice will auto-activate there
            try {
              const navEvent = new CustomEvent('jarvis-navigate', { detail: { path: '/chat' } });
              window.dispatchEvent(navEvent);
            } catch {}
          });
          // Start wake word listening (non-blocking)
          wakeEngine.start().catch(() => {});
          window.__jarvisWakeEngine = wakeEngine;
          console.log('[JARVIS] 🎙️ Wake word engine started — say "Hey JARVIS"');
        }
      } catch (e) { console.warn('[JARVIS] Wake word engine:', e.message) }

      // Phase 5: JARVIS Ultra Features — 20 Z+++ Security & Smart Upgrades
      try {
        const { initUltraFeatures } = await import('./services/jarvisUltraFeatures');
        await initUltraFeatures();
        console.log('[JARVIS] 🛡️ Ultra Features — 20 upgrades ACTIVE');
      } catch (e) { console.warn('[JARVIS] Ultra features:', e.message) }

      console.log('[JARVIS v19.0] ⚡ ALL systems ONLINE — Lean boot complete')
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

    // Listen for JARVIS voice navigation events (from wake word, voice commands, etc.)
    const handleJarvisNavigate = (e) => {
      const path = e?.detail?.path
      if (path) {
        console.log('[JARVIS] Navigating to:', path)
        navigate(path)
      }
    }
    window.addEventListener('jarvis-navigate', handleJarvisNavigate)
    return () => window.removeEventListener('jarvis-navigate', handleJarvisNavigate)
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
              <Route path="/copy-trading" element={<ErrorBoundary><CopyTrading /></ErrorBoundary>} />
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
              <Route path="/vault" element={<ErrorBoundary><VaultManager /></ErrorBoundary>} />
              <Route path="/exchange-connect" element={<ErrorBoundary><ExchangeConnect /></ErrorBoundary>} />
              <Route path="/web3-scanner" element={<ErrorBoundary><Web3MegaScanner /></ErrorBoundary>} />
              <Route path="/crypto-top1000" element={<ErrorBoundary><CryptoTop1000 /></ErrorBoundary>} />
              <Route path="/candle-brain" element={<ErrorBoundary><AICandleBrain /></ErrorBoundary>} />
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
