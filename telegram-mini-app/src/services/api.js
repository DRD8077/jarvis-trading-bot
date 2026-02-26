import axios from 'axios'
import { API_BASE } from './apiBase'

// Realtime init moved to App.jsx bootJarvis() — NOT at module scope
// This prevents WebSocket crashes when components import api.js

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// User data auto-inject from Gmail auth
api.interceptors.request.use((config) => {
  try {
    const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || 'null')
    if (savedUser) {
      config.params = {
        ...config.params,
        user_id: savedUser.id,
        username: savedUser.name || savedUser.email || 'user'
      }
      const token = localStorage.getItem('jarvis_gmail_token')
      if (token) config.headers['Authorization'] = `Bearer ${token}`
    }
  } catch(e) {}
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => { console.warn(`API [${err.config?.url}]:`, err.message); return Promise.reject(err) }
)

// ═══ DASHBOARD ═══
export const fetchDashboard = () => api.get('/dashboard')
export const fetchHealth = () => api.get('/health')
export const fetchTicker = () => api.get('/ticker')
export const fetchFastPrice = (symbol) => api.get(`/price/${symbol}`)

// ═══ MARKETS ═══
export const fetchMarkets = () => api.get('/markets')
export const fetchSentiment = () => api.get('/sentiment/analysis')
export const fetchNews = (category = 'all') => api.get('/news', { params: { category } })
export const fetchTopMovers = () => api.get('/markets')

// ═══ SIGNALS & ANALYSIS ═══
export const fetchSignals = () => api.get('/signals')
export const fetchAnalysis = (symbol) => api.get('/analyze', { params: { symbol } })
export const fetchTechnicalAnalysis = (symbol) => api.get('/analysis/technical', { params: { symbol } })
export const fetchCandleAnalysis = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchPredictions = () => api.get('/predictions')

// ═══ GEM SCANNER ═══
export const fetchGems = (filter = 'all') => api.get('/gems', { params: { filter } })
export const fetchRugCheck = (address) => api.get('/rug-check', { params: { address } })
export const fetchSearch = (q) => api.get('/search', { params: { q } })
export const fetchToken = (address) => api.get(`/token/${address}`)

// ═══ DEX & PUMP ═══
export const fetchDexTrending = () => api.get('/dex/trending')
export const fetchDexNewPairs = () => api.get('/dex/new-pairs')
export const fetchPumpfunTrending = () => api.get('/pumpfun/trending')
export const fetchPumpfunNew = () => api.get('/pumpfun/new')

// ═══ AI CHAT ═══
export const sendChat = (message, context = '', userId = null) => {
  const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || '{}')
  const uid = userId || savedUser?.id || '0'
  return api.post('/chat', { message, context, user_id: String(uid) })
}
export const clearChat = (userId) => api.post('/chat/clear', { user_id: userId })
export const fetchChatHistory = (userId) => api.get('/chat/history', { params: { user_id: userId } })
export const fetchChatModels = () => api.get('/chat/models')

// ═══ CODE ENGINE ═══
export const executeCode = (prompt, userId) => api.post('/code/execute', { prompt, user_id: userId }, { timeout: 120000 })
export const cloneGithub = (url, userId, runCmd = '') => api.post('/code/github', { url, user_id: userId, run_cmd: runCmd }, { timeout: 120000 })
export const runCode = (code, language = 'python') => api.post('/code/run', { code, language }, { timeout: 60000 })

// Streaming chat — SSE
export const streamChat = async (message, userId, modelId = 'jarvis-auto', onChunk, onDone, onError) => {
  const baseUrl = api.defaults.baseURL || '/api/miniapp'
  try {
    const res = await fetch(`${baseUrl}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_id: userId, model: modelId })
    })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const d = JSON.parse(line.slice(6))
            if (d.chunk) onChunk?.(d.chunk)
            if (d.done) onDone?.()
            if (d.error) onError?.(d.error)
          } catch {}
        }
      }
    }
    onDone?.()
  } catch (e) {
    onError?.(e.message)
  }
}

// ═══ WALLET & PHANTOM ═══
export const fetchWallet = () => api.get('/wallet')
export const phantomConnect = (userId, walletAddress) => api.post('/wallet/connect-phantom', { user_id: userId, wallet_address: walletAddress })
export const phantomDisconnect = (userId) => api.post('/wallet/disconnect-phantom', { user_id: userId })
export const fetchPhantomBalance = (userId) => api.get('/wallet/phantom-balance', { params: { user_id: userId } })
export const fetchWalletTokens = (userId) => api.get('/wallet/tokens', { params: { user_id: userId } })
export const fetchWalletBalance = (userId) => api.get('/wallet/balance', { params: { user_id: userId } })

// ═══ PAYMENTS (Deposit / Withdraw) ═══
export const requestDeposit = (amount, method = 'upi') => api.post('/deposit', { amount, method })
export const verifyDeposit = (utr, amount) => api.post('/deposit/verify', { utr, amount })
export const requestWithdraw = (amount, method = 'upi') => api.post('/withdraw', { amount, method })
export const fetchTransactions = (userId) => api.get('/transactions', { params: { user_id: userId } })

// ═══ AUTO-TRADER ═══
export const fetchStrategies = () => api.get('/auto-trader/strategies')
export const startAutoTrader = (strategy, amount) => api.post('/auto-trader/start', { strategy, amount })
export const stopAutoTrader = () => api.post('/auto-trader/stop')
export const fetchAutoTraderStatus = () => api.get('/auto-trader/status')
export const fetchAutoTraderPerformance = () => api.get('/auto-trader/performance')
export const compoundProfits = () => api.post('/auto-trader/compound')
export const fetchAutoTraderGems = () => api.get('/auto-trader/gems')

// ═══ INDIA / NIFTY ═══
export const fetchIndiaDashboard = () => api.get('/india/dashboard')
export const fetchNiftyDashboard = () => api.get('/india/dashboard')
export const fetchIndiaIndices = () => api.get('/india/indices')
export const fetchVix = () => api.get('/india/vix')
export const fetchFiiDii = () => api.get('/india/fii-dii')
export const fetchPcr = (index) => api.get('/india/pcr', { params: { index } })
export const fetchSectors = () => api.get('/india/sectors')
export const fetchGiftNifty = () => api.get('/india/gift-nifty')
export const fetchIndiaSuperAnalysis = (query, budget) => api.get('/india/super-analysis', { params: { query, budget } })
export const fetchIndiaPrediction = (index) => api.get('/india/prediction', { params: { index } })
export const fetchMlPrediction = (symbol) => api.get('/india/ml-prediction', { params: { symbol } })
export const fetchIndiaNews = (limit = 20) => api.get('/india/news', { params: { limit } })
export const fetchIndiaCombinedDashboard = () => api.get('/india/dashboard')
export const fetchMarketStatus = () => api.get('/india/dashboard')
export const fetchPivots = (index) => api.get('/india/dashboard')
export const fetchOiBuildup = (index) => api.get('/india/dashboard')
export const fetchNiftySuperAnalysis = (index) => api.get('/india/super-analysis', { params: { query: index } })
export const fetchIndiaSnapshot = () => api.get('/india/indices')
export const fetchPowerPredict = (index) => api.get('/india/prediction', { params: { index } })
export const fetchMarketRegime = (symbol) => api.get('/regime', { params: { symbol } })
export const fetchIndia2minSignal = (symbol, name) => api.get('/india/prediction', { params: { index: name } })
export const fetchOiSuperSignal = (symbol) => api.get('/options/signal', { params: { symbol } })
export const fetchGlobalIndiaImpact = () => api.get('/global/india-impact')
export const fetchIndiaHolidays = () => api.get('/india/dashboard')
export const fetchInvestmentCalc = (symbol, name, investment) => api.get('/india/super-analysis', { params: { query: name, budget: investment } })
export const fetchAiMarketVerdict = () => api.get('/india/ai-verdict')
export const fetchAiDashboard = () => api.get('/india/dashboard')

// ═══ OPTIONS ═══
export const fetchOptionChain = (symbol, expiry) => api.get('/options/chain', { params: { symbol, expiry } })
export const fetchOptionsAnalysis = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchOptionsSignal = (symbol) => api.get('/options/signal', { params: { symbol } })
export const fetchOptionsTraps = (symbol) => api.get('/options/traps', { params: { symbol } })
export const fetchBudgetPlays = (symbol, budget) => api.get('/options/budget-plays', { params: { symbol, budget } })
export const fetchOptionStrategy = (symbol, outlook, budget) => api.get('/options/strategy', { params: { symbol, outlook, budget } })
export const fetchOptionIV = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchMorningPicks = () => api.get('/options/budget-plays')
export const fetchOptionPositions = () => api.get('/wallet')

// ═══ INTELLIGENCE ═══
export const fetchIntelligence = () => api.get('/intelligence')
export const fetchTopPicks = () => api.get('/intelligence/top-picks')
export const fetchWatchlist = (userId) => api.get('/intelligence/watchlist', { params: { user_id: userId } })

// ═══ RISK / REGIME / CORRELATION ═══
export const fetchRisk = (params) => api.get('/risk/position-size', { params })
export const fetchPositionSize = (capital, riskPct, entry, sl) => api.get('/risk/position-size', { params: { capital, risk_pct: riskPct, entry, sl } })
export const fetchInvestmentPlan = (capital) => api.get('/risk/plan', { params: { capital } })
export const fetchRegime = (symbol) => api.get('/regime', { params: { symbol } })
export const fetchCorrelation = (symbol) => api.get('/correlation', { params: { symbol } })

// ═══ GLOBAL ═══
export const fetchGlobalMarkets = () => api.get('/global/markets')
export const fetchGlobalAnalysis = () => api.get('/global/analysis')
export const fetchGlobalIndiaImpactDirect = () => api.get('/global/india-impact')

// ═══ AIRDROPS ═══
export const fetchAirdrops = () => api.get('/airdrops')
export const fetchNewAirdrops = () => api.get('/airdrops/new')

// ═══ FUTURES ═══
export const fetchFutures = () => api.get('/futures/dashboard')

// ═══ SCREENER ═══
export const fetchScreener = (filters) => api.get('/screener/full', { params: filters })

// ═══ COPY TRADING & SOCIAL ═══
export const fetchCopyTradingSignals = () => api.get('/signals')
export const fetchCopyTradingLeaderboard = () => api.get('/auto-trader/performance')
export const fetchSocialFeed = (limit = 20, offset = 0) => fetch(`${API_BASE.replace('/miniapp', '')}/api/social/feed?limit=${limit}&offset=${offset}`).then(r => r.json()).catch(() => ({ signals: [] }))
export const shareSignal = (data) => fetch(`${API_BASE.replace('/miniapp', '')}/api/social/share`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json())
export const likeSignal = (signalId, userId) => fetch(`${API_BASE.replace('/miniapp', '')}/api/social/like/${signalId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId }) }).then(r => r.json())
export const fetchLeaderboard = (limit = 20) => fetch(`${API_BASE.replace('/miniapp', '')}/api/social/leaderboard?limit=${limit}`).then(r => r.json()).catch(() => ({ leaders: [] }))
export const followTrader = (traderId, userId) => fetch(`${API_BASE.replace('/miniapp', '')}/api/social/follow/${traderId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId }) }).then(r => r.json())

// ═══ WHALE ═══
export const fetchWhaleAlert = (token) => api.get('/whale/token', { params: { address: token } })
export const fetchWhaleScan = () => api.get('/whale/scan')
export const fetchWhaleOnchain = (mint) => api.get('/whale/onchain', { params: { mint } })

// ═══ PORTFOLIO ═══
export const fetchCombinedPortfolio = (userId) => api.get('/wallet', { params: { user_id: userId } })
export const fetchPortfolioPnl = (userId) => api.get('/auto-trader/performance', { params: { user_id: userId } })
export const addPortfolioHolding = (data) => api.post('/auto-trader/start', data)
export const sellPortfolioHolding = (data) => api.post('/auto-trader/stop', data)
export const sellPosition = (symbol, qty) => api.post('/auto-trader/stop', { symbol, quantity: qty })
export const sellAll = () => api.post('/auto-trader/stop')

// ═══ BACKTEST ═══
export const runBacktest = (strategy) => api.post('/auto-trader/start', { strategy, mode: 'backtest' })

// ═══ PHANTOM ═══
export const phantomConnectLink = (userId) => api.post('/wallet/connect-phantom', { user_id: userId })
export const phantomScan = (userId) => api.get('/wallet/phantom-balance', { params: { user_id: userId } })
export const phantomDashboard = (userId) => api.get('/wallet/phantom-balance', { params: { user_id: userId } })
export const solanaBalance = (wallet) => api.get('/solana/balance', { params: { wallet } })
export const solanaTransactions = (wallet) => api.get('/solana/transactions', { params: { wallet } })

export default api

// ═══ INTRADAY SCANNER (maps to signals/screener endpoints) ═══
export const fetchIntradayScan = (params) => api.get('/intraday/scan', { params })
export const fetchIntradayBreakouts = () => api.get('/intraday/breakouts')
export const fetchIntradayVolume = () => api.get('/intraday/volume')
export const fetchIntradayMomentum = () => api.get('/intraday/momentum')
export const fetchScreenerOversold = () => api.get('/screener/filter', { params: { type: 'oversold' } })
export const fetchScreenerOverbought = () => api.get('/screener/filter', { params: { type: 'overbought' } })
export const fetchScreenerVolumeSpike = () => api.get('/screener/filter', { params: { type: 'volume' } })
export const fetchScreenerGapUps = () => api.get('/screener/filter', { params: { type: 'gap_up' } })
export const fetchScreenerMomentum = () => api.get('/screener/filter', { params: { type: 'momentum' } })
export const fetchScreener52wHigh = () => api.get('/screener/filter', { params: { type: '52w_high' } })
export const fetchScreenerBullish = () => api.get('/screener/filter', { params: { type: 'bullish' } })
export const fetchScreenerRun = (filters) => api.get('/screener/filter', { params: filters })

// ═══ OPTIONS PRO LIVE ═══
export const fetchStrikePrice = (symbol) => api.get('/options/strike', { params: { symbol } })
export const fetchNearbyOptions = (symbol) => api.get('/options/nearby', { params: { symbol } })
export const fetchChainSummary = (symbol) => api.get('/options/chain-summary', { params: { symbol } })
export const fetchFuturesDashboard = () => api.get('/futures/dashboard')
export const fetchFuturesBasis = (symbol) => api.get('/futures/dashboard', { params: { symbol } })
export const fetchFuturesStraddle = (symbol) => api.get('/futures/dashboard', { params: { symbol } })
export const fetchFuturesOiDist = (symbol) => api.get('/futures/dashboard', { params: { symbol } })
export const fetchFuturesMaxPain = (symbol) => api.get('/futures/dashboard', { params: { symbol } })
export const fetchCorrelationsScan = () => api.get('/correlation', { params: { symbol: 'NIFTY' } })
export const fetchCorrelationInsight = (symbol) => api.get('/correlation', { params: { symbol } })

// ═══ STRATEGY BUILDER ═══
export const fetchStrategyRecommend = (symbol, outlook, budget) => api.get('/options/strategy', { params: { symbol, outlook, budget } })
export const fetchStraddle = (symbol) => api.get('/options/strategy', { params: { symbol, outlook: 'straddle' } })
export const fetchStrangle = (symbol) => api.get('/options/strategy', { params: { symbol, outlook: 'strangle' } })
export const fetchBullSpread = (symbol, budget) => api.get('/options/strategy', { params: { symbol, outlook: 'bullish', budget } })
export const fetchBearSpread = (symbol, budget) => api.get('/options/strategy', { params: { symbol, outlook: 'bearish', budget } })
export const fetchIronCondor = (symbol, budget) => api.get('/options/strategy', { params: { symbol, outlook: 'iron_condor', budget } })
export const fetchIvAnalysis = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchGreeks = (symbol) => api.get('/options/greeks', { params: { symbol } })

// ═══ RISK MANAGER EXTRAS ═══
export const fetchKellyCriterion = (winRate, avgWin, avgLoss) => api.get('/risk/position-size', { params: { win_rate: winRate, avg_win: avgWin, avg_loss: avgLoss, type: 'kelly' } })
export const fetchRiskReward = (entry, sl, tp) => api.get('/risk/position-size', { params: { entry, sl, target: tp } })
export const fetchMarketNews = (category) => api.get('/news', { params: { category } })
export const fetchStockNews = (symbol) => api.get('/news', { params: { category: symbol } })

// ═══ NIFTY OPTIONS LIVE ═══
export const fetchNseLiveChain = (symbol, expiry) => api.get('/options/chain', { params: { symbol, expiry } })
export const fetchNseLiveSpot = (symbol) => api.get('/india/vix', { params: { symbol } })
export const fetchNseAtmOtm = (symbol) => api.get('/options/atm-otm', { params: { symbol } })
export const fetchOiTraps = (symbol) => api.get('/options/traps', { params: { symbol } })
export const fetchOiBudgetPlays = (symbol, budget) => api.get('/options/budget-plays', { params: { symbol, budget } })
export const fetchOiChange = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchOtmAtmAnalysis = (symbol) => api.get('/options/atm-otm', { params: { symbol } })
export const fetchRapidMomentum = (symbol) => api.get('/india/prediction', { params: { index: symbol } })

// ═══ CANDLE INDICATORS ═══
export const fetchCandlePatterns = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchCandleIndicators = (symbol) => api.get('/analysis/technical', { params: { symbol } })

// ═══ TRADING EXTRAS ═══
export const fetchCandlePatternsOld = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchUltraPredict = (symbol) => api.get('/ultra/predict', { params: { symbol } })

// ═══ OPTIONS CHAIN EXTRAS ═══
export const fetchBudgetPicks = (symbol, budget) => api.get('/options/budget-plays', { params: { symbol, budget } })

// ═══ PHANTOM EXTRAS ═══
export const solanaAirdrops = (wallet) => api.get('/airdrops', { params: { wallet } })

// ═══ PORTFOLIO EXTRAS ═══
export const fetchPortfolioTax = (userId) => api.get('/auto-trader/performance', { params: { user_id: userId, type: 'tax' } })

// ═══ POWER PREDICTOR EXTRAS ═══
export const fetchMlPredict = (symbol) => api.get('/ml/predict', { params: { symbol } })

// ═══ WEB3 ROCKETS ═══
export const fetchWeb3Rockets = () => api.get('/web3/rockets')
export const fetchWeb3Launches = () => api.get('/web3/new-launches')

// ═══ SOLANA ═══
export const fetchSolanaBalance = (wallet) => api.get('/solana/balance', { params: { wallet } })
export const fetchSolanaTokens = (wallet) => api.get('/solana/tokens', { params: { wallet } })
export const fetchSolanaTransactions = (wallet) => api.get('/solana/transactions', { params: { wallet } })

// ═══ INR PRICES ═══
export const fetchInrPrices = () => api.get('/inr/prices')
export const fetchInrGainers = () => api.get('/inr/gainers')
export const fetchInrLosers = () => api.get('/inr/losers')

// ═══ PNL JOURNAL ═══
export const fetchPnlDaily = (userId) => api.get('/pnl/daily', { params: { user_id: userId } })
export const fetchPnlWeekly = (userId) => api.get('/pnl/weekly', { params: { user_id: userId } })
export const fetchPnlMonthly = (userId) => api.get('/pnl/monthly', { params: { user_id: userId } })
export const logTrade = (data) => api.post('/pnl/log', data)
export const closeTrade = (data) => api.post('/pnl/close', data)

// ═══ CHARTS ═══
export const fetchChart = (symbol, timeframe = '1d') => api.get('/chart', { params: { symbol, timeframe } })

// ═══ BRIEFING / SUPER BRAIN ═══
export const fetchBriefing = () => api.get('/briefing')
export const fetchMarketIntel = () => api.get('/market-intel')

// ═══ MARKET BRAIN ═══
export const fetchMarketBrainAnalysis = (query) => api.get('/market-brain/analyze', { params: { query } })

// ═══ ULTRA AI ═══
export const fetchUltraHealth = (symbol) => api.get('/ultra/health', { params: { symbol } })

// ═══ COINDCX MEGA ═══
export const fetchCoindcxMegaScan = () => api.get('/coindcx/scan')

// ═══ DEXTOOLS ═══
export const fetchDextoolsHot = () => api.get('/dextools/hot')
export const fetchDextoolsSearch = (q) => api.get('/dextools/search', { params: { q } })

// ═══ GLOBAL ═══
export const fetchGlobalIndiaPrediction = () => api.get('/global/india-impact')

// ═══ LIVE INDEX ═══
export const fetchLivePrice = (symbol) => api.get('/live/price', { params: { symbol } })
export const fetchLive2minSignal = (symbol) => api.get('/live/2min-signal', { params: { symbol } })
export const fetchLiveInvestment = (symbol, amount) => api.get('/live/investment', { params: { symbol, amount } })

// ═══ MEMORY ═══
export const rememberData = (userId, key, value) => api.post('/memory/remember', { user_id: userId, key, value })
export const recallData = (userId, key) => api.get('/memory/recall', { params: { user_id: userId, key } })

// ═══ ANGELONE ═══
export const fetchAngeloneLtp = (symbol) => api.get('/angelone/ltp', { params: { symbol } })
export const fetchAngelonePositions = () => api.get('/angelone/positions')

// ═══ AI VERDICT ═══
export const fetchAiVerdict = () => api.get('/india/ai-verdict')

// ═══ VOICE AI ═══
export const voiceGenerate = (text) => api.post('/voice/generate', { text })
export const voiceTranscribe = (audioData) => api.post('/chat', { message: audioData, context: 'transcribe' })

// ═══ 🎙️ HINDI VOICE ASSISTANT ═══
const VOICE_BASE_URL = API_BASE.replace('/miniapp', '') + '/api/voice'
const GEMINI_BASE_URL = API_BASE.replace('/miniapp', '') + '/api/gemini'
const AUTH_BASE_URL = API_BASE.replace('/miniapp', '') + '/api/auth'
const INTEL_BASE_URL = API_BASE.replace('/miniapp', '') + '/api/intelligence'
const OTA_BASE_URL = API_BASE.replace('/miniapp', '') + '/api/ota'

export const voiceHindiChat = (message, userId, userName, isOwner) => {
  const fd = new FormData()
  fd.append('message', message)
  fd.append('user_id', userId || '0')
  fd.append('user_name', userName || '')
  fd.append('is_owner', isOwner ? 'true' : 'false')
  return fetch(`${VOICE_BASE_URL}/chat`, { method: 'POST', body: fd }).then(r => r.json())
}
export const voiceSpeak = (text) => {
  const fd = new FormData()
  fd.append('text', text)
  return fetch(`${VOICE_BASE_URL}/speak`, { method: 'POST', body: fd }).then(r => r.blob())
}
export const voiceTranscribeHindi = (audioBlob) => {
  const fd = new FormData()
  fd.append('audio', audioBlob, 'recording.webm')
  return fetch(`${VOICE_BASE_URL}/transcribe`, { method: 'POST', body: fd }).then(r => r.json())
}

// ═══ 🧠 GEMINI BRIDGE ═══
export const geminiChat = (message, userId) => fetch(`${GEMINI_BASE_URL}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, user_id: userId }) }).then(r => r.json())
export const geminiAnalyze = (query) => fetch(`${GEMINI_BASE_URL}/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) }).then(r => r.json())
export const geminiIntent = (message) => fetch(`${GEMINI_BASE_URL}/intent`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }) }).then(r => r.json())
export const geminiConfig = () => fetch(`${GEMINI_BASE_URL}/config`).then(r => r.json())

// ═══ 🔐 SMART AUTH ═══
export const authLogin = (chatId, firstName, lastName, username, isOwner) => fetch(`${AUTH_BASE_URL}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chatId, first_name: firstName, last_name: lastName, username, is_owner: isOwner }) }).then(r => r.json())
export const authRegister = (chatId, firstName, lastName, username) => fetch(`${AUTH_BASE_URL}/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chatId, first_name: firstName, last_name: lastName, username }) }).then(r => r.json())
export const authVerify = (token) => fetch(`${AUTH_BASE_URL}/verify`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) }).then(r => r.json())
export const authProfile = (userId) => fetch(`${AUTH_BASE_URL}/profile/${userId}`).then(r => r.json())

// ═══ 🧠 SUPER INTELLIGENCE ═══
export const fetchSuperChat = (message, userId) => fetch(`${INTEL_BASE_URL}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, user_id: userId }) }).then(r => r.json())
export const fetchProactiveInsights = (userId) => fetch(`${INTEL_BASE_URL}/insights?user_id=${userId}`).then(r => r.json())
export const fetchAccuracy = () => fetch(`${INTEL_BASE_URL}/accuracy`).then(r => r.json())
export const fetchMarketContext = () => fetch(`${INTEL_BASE_URL}/context`).then(r => r.json())
export const learnPreference = (userId, key, value) => fetch(`${INTEL_BASE_URL}/learn`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId, key, value }) }).then(r => r.json())

// ═══ 🔄 OTA UPDATES ═══
export const otaCheck = (currentVersion) => fetch(`${OTA_BASE_URL}/check?current_version=${currentVersion}`).then(r => r.json())
export const otaDownload = (version) => fetch(`${OTA_BASE_URL}/download/${version}`).then(r => r.blob())

// ═══ 🔥 MEGA AI TRADER — Nuclear Autonomous Trading ═══
export const fetchMegaTraderStatus = (userId) => api.get('/mega-trader/status', { params: { user_id: userId } })
export const createMegaWallet = (userId) => api.post('/mega-trader/create-wallet', { user_id: userId })
export const enableMegaTrader = (userId) => api.post('/mega-trader/enable', { user_id: userId })
export const disableMegaTrader = (userId) => api.post('/mega-trader/disable', { user_id: userId })
export const fetchMegaPortfolio = (userId) => api.get('/mega-trader/portfolio', { params: { user_id: userId } })
export const fetchMegaScan = () => api.get('/mega-trader/scan')
export const megaBuy = (userId, mint, solAmount) => api.post('/mega-trader/buy', { user_id: userId, mint, sol_amount: solAmount })
export const megaSell = (userId, mint, sellPct = 100) => api.post('/mega-trader/sell', { user_id: userId, mint, sell_pct: sellPct })
export const megaTransfer = (userId, destination, solAmount) => api.post('/mega-trader/transfer', { user_id: userId, destination, sol_amount: solAmount })
export const fetchMegaTransfers = (userId) => api.get('/mega-trader/transfers', { params: { user_id: userId } })
export const megaRugCheck = (mint, chain = 'solana') => api.get('/mega-trader/rug-check', { params: { mint, chain } })

// ═══════════════════════════════════════════════════════════
//  🚀 POWER-UP v6.0 — New Module APIs
// ═══════════════════════════════════════════════════════════
const POWER_BASE = API_BASE.replace('/miniapp', '') + '/api'

// --- SSE Real-time Signals ---
export const connectSSE = (channel = 'all', onMessage) => {
  const es = new EventSource(`${POWER_BASE}/sse/${channel}`)
  es.onmessage = (e) => { try { onMessage(JSON.parse(e.data)) } catch {} }
  es.onerror = () => { console.warn('SSE reconnecting...') }
  return es
}

// --- Task Queue ---
export const enqueueTask = (taskType, params = {}, userId = 'system') =>
  fetch(`${POWER_BASE}/tasks/enqueue`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task_type: taskType, params, user_id: userId }) }).then(r => r.json())
export const fetchTaskStatus = (taskId) => fetch(`${POWER_BASE}/tasks/${taskId}`).then(r => r.json())
export const fetchAllTasks = () => fetch(`${POWER_BASE}/tasks`).then(r => r.json())

// --- DexTools ---
export const fetchDextoolsSummary = () => fetch(`${POWER_BASE}/dextools/summary`).then(r => r.json()).catch(() => ({}))
export const fetchDextoolsHotPairs = (chain = 'ethereum') => fetch(`${POWER_BASE}/dextools/hot/${chain}`).then(r => r.json()).catch(() => ({ pairs: [] }))

// --- Birdeye (Solana DEX Intel) ---
export const fetchBirdeyeSummary = () => fetch(`${POWER_BASE}/birdeye/summary`).then(r => r.json()).catch(() => ({}))
export const fetchBirdeyeTrending = () => fetch(`${POWER_BASE}/birdeye/trending`).then(r => r.json()).catch(() => ({ tokens: [] }))

// --- Notifications ---
export const subscribePush = (chatId, prefs) =>
  fetch(`${POWER_BASE}/notifications/subscribe`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chatId, preferences: prefs }) }).then(r => r.json())
export const unsubscribePush = (chatId) =>
  fetch(`${POWER_BASE}/notifications/unsubscribe`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chatId }) }).then(r => r.json())

// --- JWT Auth v2 ---
export const jwtRegister = (username, password, chatId) =>
  fetch(`${POWER_BASE}/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, chat_id: chatId }) }).then(r => r.json())
export const jwtLogin = (username, password) =>
  fetch(`${POWER_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }).then(r => r.json())
export const jwtRefresh = (refreshToken) =>
  fetch(`${POWER_BASE}/auth/refresh`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) }).then(r => r.json())

// --- System Metrics / Admin ---
export const fetchSystemOverview = () => fetch(`${POWER_BASE}/system/overview`).then(r => r.json()).catch(() => ({}))
export const fetchSystemMetrics = () => fetch(`${POWER_BASE}/metrics`).then(r => r.json()).catch(() => ({}))
export const fetchAdminApiKeys = () => fetch(`${POWER_BASE}/admin/api-keys`).then(r => r.json()).catch(() => ({ keys: [] }))
export const setAdminApiKey = (keyName, keyValue) =>
  fetch(`${POWER_BASE}/admin/api-keys`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key_name: keyName, key_value: keyValue }) }).then(r => r.json())
export const fetchAdminErrors = () => fetch(`${POWER_BASE}/admin/errors`).then(r => r.json()).catch(() => ({}))
export const fetchEngineHealth = () => fetch(`${POWER_BASE}/admin/engine-health`).then(r => r.json()).catch(() => ({ engines: {} }))
