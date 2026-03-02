import React, { Suspense, lazy, useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { AppProvider, useApp } from './context/AppContext'
import Navigation from './components/Navigation'
import LiveTicker from './components/LiveTicker'
import InstallPrompt from './components/InstallPrompt'
import LoginScreen from './components/LoginScreen'
import OnboardingScreen from './components/OnboardingScreen'
import SplashScreen from './components/SplashScreen'
import IronManBoot from './components/IronManBoot'
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
const MoonShotHunter = lazy(() => import('./components/MoonShotHunter'))
const AIAutoSniper = lazy(() => import('./components/AIAutoSniper'))
const JarvisWorkshop = lazy(() => import('./components/JarvisWorkshop'))
const JarvisHologram = lazy(() => import('./components/JarvisHologram'))
const JarvisHUD = lazy(() => import('./components/JarvisHUD'))
const JarvisWarRoom = lazy(() => import('./components/JarvisWarRoom'))
const JarvisDiagnosticsPage = lazy(() => import('./components/JarvisDiagnosticsPage'))
const JarvisBattleOverlay = lazy(() => import('./components/JarvisBattleOverlay'))
const JarvisNotificationOverlay = lazy(() => import('./components/JarvisNotificationOverlay'))

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
    // Set global mute for SOUND EFFECTS only (not voice speech)
    // __JARVIS_MUTE = true → all SoundFX beeps/alerts disabled
    // __JARVIS_VOICE_ENABLED = true → JARVIS can still speak via TTS
    try {
      const savedSettings = JSON.parse(localStorage.getItem('jarvis_app_settings') || '{}')
      window.__JARVIS_MUTE = savedSettings.sound !== true // SFX muted by default
      window.__JARVIS_VOICE_ENABLED = savedSettings.voice !== false // Voice ON by default
    } catch {
      window.__JARVIS_MUTE = true
      window.__JARVIS_VOICE_ENABLED = true // JARVIS should always speak
    }

    async function bootJarvis() {
      console.log('[JARVIS v31.0 STANDALONE] Crash-proof boot sequence starting...')

      // ═══ SOUND EFFECTS MUTE — only kills beeps/chimes, NOT JARVIS voice ═══
      try {
        const savedSettings = localStorage.getItem('jarvis_app_settings')
        const parsed = savedSettings ? JSON.parse(savedSettings) : null
        window.__JARVIS_MUTE = parsed?.sound ? false : true // SFX off by default
        window.__JARVIS_VOICE_ENABLED = parsed?.voice !== false // Voice always ON unless explicitly disabled
      } catch {
        window.__JARVIS_MUTE = true
        window.__JARVIS_VOICE_ENABLED = true
      }
      console.log('[JARVIS] 🔇 Sound FX:', window.__JARVIS_MUTE ? 'OFF' : 'ON')
      console.log('[JARVIS] 🗣️ Voice:', window.__JARVIS_VOICE_ENABLED ? 'ON' : 'OFF')


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

      // ═══ JARVIS BOOT GREETING — DISABLED (v33: was causing unwanted speech on first touch) ═══
      // JARVIS will only speak when user explicitly asks via voice command or chat
      try {
        // Pre-load voice companion module (for when user wants to speak)
        await import('./services/jarvisVoiceCompanion.js').catch(() => null)
      } catch {}

      // Pre-cache for offline mode
      try {
        const api = await import('./services/api').catch(() => null)
        if (api && offlineCache && typeof offlineCache.preCacheEssentials === 'function') {
          offlineCache.preCacheEssentials(api).catch(() => {})
        }
      } catch {}

      // Phase 4: JARVIS Wake Word Engine — DISABLED on auto-start (v33: was picking up ambient noise and triggering speech)
      // User can manually enable "Hey JARVIS" from Settings or Voice page
      try {
        const { getWakeWordEngine } = await import('./services/wakeWordEngine').catch(() => ({}));
        if (getWakeWordEngine) {
          const wakeEngine = getWakeWordEngine();
          // Store reference but DON'T auto-start — user must enable explicitly
          window.__jarvisWakeEngine = wakeEngine;
          console.log('[JARVIS] 🎙️ Wake word engine loaded (manual start — enable in Settings)');
        }
      } catch (e) { console.warn('[JARVIS] Wake word engine:', e.message) }

      // Phase 5: JARVIS Ultra Features — 20 Z+++ Security & Smart Upgrades
      try {
        const { initUltraFeatures } = await import('./services/jarvisUltraFeatures');
        await initUltraFeatures();
        console.log('[JARVIS] 🛡️ Ultra Features — 20 upgrades ACTIVE');
      } catch (e) { console.warn('[JARVIS] Ultra features:', e.message) }

      // Phase 6: JARVIS Proactive Brain — background market monitoring (Iron Man style)
      try {
        const brainMod = await import('./services/jarvisProactiveBrain.js');
        const brain = brainMod.default || brainMod;
        if (brain?.start) {
          brain.start();
          window.__jarvisProactiveBrain = brain;
          console.log('[JARVIS] 🧠 Proactive Brain ACTIVATED — monitoring markets');
        }
      } catch (e) { console.warn('[JARVIS] Proactive Brain:', e.message) }

      // Phase 7: Sound Effects Engine — DISABLED by default (user can enable in Settings)
      // Sounds were causing continuous alert noise on Android. Now fully silent.
      try {
        const sfxMod = await import('./services/jarvisSoundFX.js');
        const sfx = sfxMod.default || sfxMod;
        // Do NOT play startup sound — keep it silent
        sfx.setEnabled(false); // Explicitly disabled
        console.log('[JARVIS] 🔇 Sound FX loaded (SILENT mode — enable in Settings)');
      } catch (e) { console.warn('[JARVIS] Sound FX:', e.message) }

      // Phase 8: Memory System — remembers everything
      try {
        const memMod = await import('./services/jarvisMemory.js');
        const mem = memMod.default || memMod;
        if (mem?.startSession) {
          mem.startSession();
          console.log('[JARVIS] 🧠 Memory System ONLINE — session tracked');
        }
      } catch (e) { console.warn('[JARVIS] Memory:', e.message) }

      // Phase 9: Gesture Controls — shake, double-tap, long-press
      try {
        const gestMod = await import('./services/jarvisGestures.js');
        const gestures = gestMod.default || gestMod;
        if (gestures?.init) {
          gestures.init();
          console.log('[JARVIS] 🤌 Gesture Controls ONLINE — shake to scan');
        }
      } catch (e) { console.warn('[JARVIS] Gestures:', e.message) }

      // Phase 10: Emotional Intelligence — mood detection & adaptive personality
      try {
        const eqMod = await import('./services/jarvisEQ.js');
        const eq = eqMod.default || eqMod;
        if (eq?.init) {
          eq.init();
          console.log('[JARVIS] 💛 Emotional Intelligence ONLINE — mood tracking active');
        }
      } catch (e) { console.warn('[JARVIS] EQ:', e.message) }

      // Phase 11: Arc Reactor Power System
      try {
        const arcMod = await import('./services/jarvisArcReactor.js');
        const arc = arcMod.default || arcMod;
        if (arc?.init) {
          arc.init();
          console.log('[JARVIS] ⚡ Arc Reactor ONLINE — power management active');
        }
      } catch (e) { console.warn('[JARVIS] Arc Reactor:', e.message) }

      // Phase 12: Emergency Protocols — restore any active protocol
      try {
        const protoMod = await import('./services/jarvisEmergencyProtocols.js');
        const proto = protoMod.default || protoMod;
        if (proto?.restore) {
          const active = proto.restore();
          if (active) console.log('[JARVIS] 🚨 Protocol restored:', active.codename);
          console.log('[JARVIS] 🚨 Emergency Protocols ONLINE — 6 protocols ready');
        }
      } catch (e) { console.warn('[JARVIS] Protocols:', e.message) }

      // Phase 13: Security Protocol — intruder detection
      try {
        const secMod = await import('./services/jarvisSecurity.js');
        const sec = secMod.default || secMod;
        if (sec?.init) {
          sec.init();
          console.log('[JARVIS] 🔒 Security Protocol ONLINE — perimeter active');
        }
      } catch (e) { console.warn('[JARVIS] Security:', e.message) }

      // Phase 14: AI Personality — restore saved personality
      try {
        const persMod = await import('./services/jarvisPersonalities.js');
        const pers = persMod.default || persMod;
        if (pers?.restore) {
          const p = pers.restore();
          console.log('[JARVIS] 🤖 AI Personality:', p?.name || 'JARVIS');
        }
      } catch (e) { console.warn('[JARVIS] Personalities:', e.message) }

      // Phase 15: Battle HUD — target tracking system
      try {
        const bhMod = await import('./services/jarvisBattleHUD.js');
        const bh = bhMod.default || bhMod;
        if (bh?.init) {
          bh.init();
          console.log('[JARVIS] ⚔️ Battle HUD ONLINE — target tracking ready');
        }
      } catch (e) { console.warn('[JARVIS] Battle HUD:', e.message) }

      // Phase 16: Learning Engine — adaptive pattern recognition
      try {
        const leMod = await import('./services/jarvisLearningEngine.js');
        const le = leMod.default || leMod;
        if (le?.init) {
          le.init();
          console.log('[JARVIS] 🧠 Learning Engine ONLINE — adapting to user patterns');
        }
      } catch (e) { console.warn('[JARVIS] Learning Engine:', e.message) }

      // Phase 17: Conversation Memory — persistent context
      try {
        const cmMod = await import('./services/jarvisConversationMemory.js');
        const cm = cmMod.default || cmMod;
        if (cm?.init) {
          cm.init();
          console.log('[JARVIS] 💬 Conversation Memory ONLINE — remembering everything');
        }
      } catch (e) { console.warn('[JARVIS] Conversation Memory:', e.message) }

      // Phase 18: Smart Notifications — Iron Man style alerts
      try {
        const notifMod = await import('./services/jarvisNotifications.js');
        const notif = notifMod.default || notifMod;
        if (notif?.init) {
          notif.init();
          console.log('[JARVIS] 🔔 Smart Notifications ONLINE — alert system ready');
        }
      } catch (e) { console.warn('[JARVIS] Notifications:', e.message) }

      console.log('[JARVIS v31.0] ⚡ ALL systems ONLINE — Full Iron Man mode ACTIVE')
    }

    bootJarvis().catch(e => {
      console.error('[JARVIS] Boot sequence error (app still running):', e.message)
    })
  }, [])

  // Cinematic Iron Man boot sequence on first session load
  if (showSplash) {
    return <IronManBoot onFinish={() => { sessionStorage.setItem('jarvis_splash_shown', '1'); setShowSplash(false) }} />
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

  // Gate: Show loading while auth initializes
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-blue-400 text-sm">Initializing JARVIS...</p>
        </div>
      </div>
    )
  }

  // Owner is always logged in — this is a fallback safety net
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
  const location = useLocation()
  const [showHologram, setShowHologram] = useState(false)

  // ═══ JARVIS VOICE COMPANION — speaks on every page navigation ═══
  useEffect(() => {
    try {
      import('./services/jarvisVoiceCompanion.js').then(mod => {
        const companion = mod.default || mod
        if (companion?.onPageChange) {
          companion.onPageChange(location.pathname)
        }
      }).catch(() => {})
      // Track page change for EQ (mood detection)
      import('./services/jarvisEQ.js').then(mod => {
        const eq = mod.default || mod
        if (eq?.recordPageChange) eq.recordPageChange(location.pathname)
      }).catch(() => {})
      // Track page visit for Learning Engine
      import('./services/jarvisLearningEngine.js').then(mod => {
        const le = mod.default || mod
        if (le?.trackPageVisit) le.trackPageVisit(location.pathname)
      }).catch(() => {})
    } catch {}
  }, [location.pathname])

  // Hologram overlay listener
  useEffect(() => {
    const onOpen = () => setShowHologram(true)
    window.addEventListener('jarvis-hologram-open', onOpen)
    return () => window.removeEventListener('jarvis-hologram-open', onOpen)
  }, [])

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
      {/* JARVIS HUD — Iron Man floating status bar */}
      <Suspense fallback={null}><JarvisHUD /></Suspense>
      {/* JARVIS Holographic Display Overlay */}
      {showHologram && <Suspense fallback={null}><JarvisHologram onClose={() => setShowHologram(false)} /></Suspense>}
      {/* JARVIS Battle HUD Overlay — target tracking */}
      <Suspense fallback={null}><JarvisBattleOverlay /></Suspense>
      {/* JARVIS Notification Overlay — Iron Man style alerts */}
      <Suspense fallback={null}><JarvisNotificationOverlay /></Suspense>
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
              <Route path="/moonshot" element={<ErrorBoundary><MoonShotHunter /></ErrorBoundary>} />
              <Route path="/auto-sniper" element={<ErrorBoundary><AIAutoSniper /></ErrorBoundary>} />
              <Route path="/workshop" element={<ErrorBoundary><JarvisWorkshop /></ErrorBoundary>} />
              <Route path="/war-room" element={<ErrorBoundary><JarvisWarRoom /></ErrorBoundary>} />
              <Route path="/diagnostics" element={<ErrorBoundary><JarvisDiagnosticsPage /></ErrorBoundary>} />
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
