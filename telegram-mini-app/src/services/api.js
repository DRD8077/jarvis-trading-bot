import axios from 'axios'

// Base API — connects to JARVIS backend v6
const API_BASE = import.meta.env.VITE_API_BASE || '/api/miniapp'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// Telegram user data auto-inject
api.interceptors.request.use((config) => {
  const tg = window.Telegram?.WebApp
  if (tg?.initData) config.headers['X-Telegram-Init-Data'] = tg.initData
  if (tg?.initDataUnsafe?.user) {
    config.params = {
      ...config.params,
      user_id: tg.initDataUnsafe.user.id,
      username: tg.initDataUnsafe.user.username
    }
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => { console.warn(`API [${err.config?.url}]:`, err.message); return Promise.reject(err) }
)

// ═══ DASHBOARD ═══
export const fetchDashboard = () => api.get('/dashboard')
export const fetchHealth = () => api.get('/health')

// ═══ MARKETS ═══
export const fetchMarkets = () => api.get('/markets')
export const fetchSentiment = () => api.get('/sentiment')
export const fetchNews = (category = 'all') => api.get('/news', { params: { category } })
export const fetchTopMovers = () => api.get('/markets')

// ═══ SIGNALS & ANALYSIS ═══
export const fetchSignals = () => api.get('/signals')
export const fetchAnalysis = (symbol) => api.get('/analyze', { params: { symbol } })
export const fetchTechnicalAnalysis = (symbol) => api.get('/analysis/technical', { params: { symbol } })
export const fetchCandleAnalysis = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchPredictions = () => api.get('/predictions')

// ═══ GEM SCANNER ═══
export const fetchGems = () => api.get('/gems')
export const fetchRugCheck = (address) => api.get('/rug-check', { params: { address } })
export const fetchSearch = (q) => api.get('/search', { params: { q } })
export const fetchToken = (address) => api.get(`/token/${address}`)

// ═══ DEX & PUMP ═══
export const fetchDexTrending = () => api.get('/dex/trending')
export const fetchDexNewPairs = () => api.get('/dex/new-pairs')
export const fetchPumpfunTrending = () => api.get('/pumpfun/trending')
export const fetchPumpfunNew = () => api.get('/pumpfun/new')

// ═══ AI CHAT ═══
export const sendChat = (message, context = '') => api.post('/chat', { message, context })
export const clearChat = (userId) => api.post('/chat/clear', { user_id: userId })
export const fetchChatHistory = (userId) => api.get('/chat/history', { params: { user_id: userId } })
export const fetchChatModels = () => api.get('/chat/models')

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
export const fetchGlobalIndiaImpact = () => api.get('/global/markets')
export const fetchIndiaHolidays = () => api.get('/india/dashboard')
export const fetchInvestmentCalc = (symbol, name, investment) => api.get('/india/super-analysis', { params: { query: name, budget: investment } })
export const fetchAiMarketVerdict = () => api.get('/india/dashboard')
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
export const fetchGlobalAnalysis = () => api.get('/global/markets')
export const fetchGlobalIndiaImpactDirect = () => api.get('/global/markets')

// ═══ AIRDROPS ═══
export const fetchAirdrops = () => api.get('/airdrops')
export const fetchNewAirdrops = () => api.get('/airdrops/new')

// ═══ FUTURES ═══
export const fetchFutures = () => api.get('/futures')

// ═══ SCREENER ═══
export const fetchScreener = (filters) => api.get('/signals', { params: filters })

// ═══ COPY TRADING & SOCIAL ═══
export const fetchCopyTradingSignals = () => api.get('/signals')
export const fetchCopyTradingLeaderboard = () => api.get('/auto-trader/performance')
export const fetchSocialFeed = () => api.get('/news')

// ═══ WHALE ═══
export const fetchWhaleAlert = (token) => api.get('/intelligence', { params: { token } })
export const fetchWhaleScan = () => api.get('/intelligence/top-picks')
export const fetchWhaleOnchain = (mint) => api.get('/intelligence', { params: { mint } })

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
export const solanaBalance = (wallet) => api.get('/wallet/phantom-balance', { params: { wallet } })
export const solanaTransactions = (wallet) => api.get('/transactions', { params: { wallet } })

export default api

// ═══ INTRADAY SCANNER (maps to signals/screener endpoints) ═══
export const fetchIntradayScan = (params) => api.get('/signals', { params: { ...params, type: 'intraday' } })
export const fetchIntradayBreakouts = () => api.get('/signals', { params: { type: 'breakout' } })
export const fetchIntradayVolume = () => api.get('/signals', { params: { type: 'volume' } })
export const fetchIntradayMomentum = () => api.get('/signals', { params: { type: 'momentum' } })
export const fetchScreenerOversold = () => api.get('/signals', { params: { filter: 'oversold' } })
export const fetchScreenerOverbought = () => api.get('/signals', { params: { filter: 'overbought' } })
export const fetchScreenerVolumeSpike = () => api.get('/signals', { params: { filter: 'volume_spike' } })
export const fetchScreenerGapUps = () => api.get('/signals', { params: { filter: 'gap_up' } })
export const fetchScreenerMomentum = () => api.get('/signals', { params: { filter: 'momentum' } })
export const fetchScreener52wHigh = () => api.get('/signals', { params: { filter: '52w_high' } })
export const fetchScreenerBullish = () => api.get('/signals', { params: { filter: 'bullish' } })
export const fetchScreenerRun = (filters) => api.get('/signals', { params: filters })

// ═══ OPTIONS PRO LIVE ═══
export const fetchStrikePrice = (symbol) => api.get('/options/chain', { params: { symbol } })
export const fetchNearbyOptions = (symbol) => api.get('/options/chain', { params: { symbol, nearby: true } })
export const fetchChainSummary = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchFuturesDashboard = () => api.get('/futures')
export const fetchFuturesBasis = (symbol) => api.get('/futures', { params: { symbol, type: 'basis' } })
export const fetchFuturesStraddle = (symbol) => api.get('/futures', { params: { symbol, type: 'straddle' } })
export const fetchFuturesOiDist = (symbol) => api.get('/futures', { params: { symbol, type: 'oi_dist' } })
export const fetchFuturesMaxPain = (symbol) => api.get('/options/analysis', { params: { symbol } })
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
export const fetchGreeks = (symbol) => api.get('/options/analysis', { params: { symbol } })

// ═══ RISK MANAGER EXTRAS ═══
export const fetchKellyCriterion = (winRate, avgWin, avgLoss) => api.get('/risk/position-size', { params: { win_rate: winRate, avg_win: avgWin, avg_loss: avgLoss, type: 'kelly' } })
export const fetchRiskReward = (entry, sl, tp) => api.get('/risk/position-size', { params: { entry, sl, target: tp } })
export const fetchMarketNews = (category) => api.get('/news', { params: { category } })
export const fetchStockNews = (symbol) => api.get('/news', { params: { category: symbol } })

// ═══ NIFTY OPTIONS LIVE ═══
export const fetchNseLiveChain = (symbol, expiry) => api.get('/options/chain', { params: { symbol, expiry } })
export const fetchNseLiveSpot = (symbol) => api.get('/india/vix', { params: { symbol } })
export const fetchNseAtmOtm = (symbol) => api.get('/options/chain', { params: { symbol, type: 'atm_otm' } })
export const fetchOiTraps = (symbol) => api.get('/options/traps', { params: { symbol } })
export const fetchOiBudgetPlays = (symbol, budget) => api.get('/options/budget-plays', { params: { symbol, budget } })
export const fetchOiChange = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchOtmAtmAnalysis = (symbol) => api.get('/options/analysis', { params: { symbol } })
export const fetchRapidMomentum = (symbol) => api.get('/india/prediction', { params: { index: symbol } })

// ═══ CANDLE INDICATORS ═══
export const fetchCandlePatterns = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchCandleIndicators = (symbol) => api.get('/analysis/technical', { params: { symbol } })

// ═══ TRADING EXTRAS ═══
export const fetchCandlePatternsOld = (symbol) => api.get('/analysis/candles', { params: { symbol } })
export const fetchUltraPredict = (symbol) => api.get('/predictions', { params: { symbol } })

// ═══ OPTIONS CHAIN EXTRAS ═══
export const fetchBudgetPicks = (symbol, budget) => api.get('/options/budget-plays', { params: { symbol, budget } })

// ═══ PHANTOM EXTRAS ═══
export const solanaAirdrops = (wallet) => api.get('/airdrops', { params: { wallet } })

// ═══ PORTFOLIO EXTRAS ═══
export const fetchPortfolioTax = (userId) => api.get('/auto-trader/performance', { params: { user_id: userId, type: 'tax' } })

// ═══ POWER PREDICTOR EXTRAS ═══
export const fetchMlPredict = (symbol) => api.get('/india/ml-prediction', { params: { symbol } })

// ═══ VOICE AI ═══
export const voiceGenerate = (text) => api.post('/chat', { message: text, context: 'voice' })
export const voiceTranscribe = (audioData) => api.post('/chat', { message: audioData, context: 'transcribe' })
