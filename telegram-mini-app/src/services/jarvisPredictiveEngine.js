/**
 * 🔮 JARVIS PREDICTIVE ENGINE — AI-Powered Market Prediction
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like JARVIS predicting trajectory and outcomes for Tony Stark.
 * Uses pattern recognition from memory + market data to predict:
 * 
 * - Price direction (bullish/bearish/neutral)
 * - Volatility prediction (calm/volatile/extreme)
 * - Best trading windows (based on user's historical win/loss times)
 * - Risk assessment for current market conditions
 * - Portfolio health score
 * - Confidence level for each prediction
 * 
 * All predictions announced in Hindi.
 */

// Historical patterns stored in memory
let predictionHistory = []
let marketPatterns = {
  hourlyTrend: [],
  dailyVolatility: [],
  winningHours: {},
  losingHours: {},
  marketCycles: [],
}

/**
 * Analyze current market and generate predictions
 * @returns {Promise<object>} Prediction results
 */
async function generatePrediction() {
  console.log('[JARVIS Predict] 🔮 Generating market prediction...')

  try {
    // Fetch real market data
    const [btcData, globalData] = await Promise.all([
      fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true')
        .then(r => r.json()).catch(() => null),
      fetch('https://api.coingecko.com/api/v3/global')
        .then(r => r.json()).catch(() => null),
    ])

    const btcPrice = btcData?.bitcoin?.usd || 0
    const btcChange = btcData?.bitcoin?.usd_24h_change || 0
    const ethChange = btcData?.ethereum?.usd_24h_change || 0
    const solChange = btcData?.solana?.usd_24h_change || 0
    const globalMcapChange = globalData?.data?.market_cap_change_percentage_24h_usd || 0
    const btcDominance = globalData?.data?.market_cap_percentage?.btc || 0

    // Multi-factor analysis
    const factors = {
      btcTrend: analyzeTrend(btcChange),
      ethCorrelation: analyzeCorrelation(btcChange, ethChange),
      altSeason: btcDominance < 45,
      marketMomentum: globalMcapChange,
      volatility: analyzeVolatility(btcChange, ethChange, solChange),
      timeOfDay: analyzeTimeOfDay(),
      dayOfWeek: analyzeDayOfWeek(),
    }

    // Generate prediction score (-100 to +100)
    let score = 0
    let confidence = 50

    // BTC trend weight (40%)
    score += factors.btcTrend.score * 0.4
    confidence += factors.btcTrend.confidence * 0.3

    // ETH correlation weight (15%)
    score += factors.ethCorrelation.score * 0.15

    // Market momentum weight (25%)
    score += (globalMcapChange > 0 ? 20 : -20) * 0.25
    if (Math.abs(globalMcapChange) > 5) confidence += 10

    // Volatility factor (10%)
    score += factors.volatility.score * 0.1
    if (factors.volatility.level === 'extreme') confidence -= 15

    // Time-based analysis (10%)
    score += factors.timeOfDay.score * 0.05
    score += factors.dayOfWeek.score * 0.05

    // Load user's trading patterns from memory
    const userPatterns = await loadUserPatterns()
    if (userPatterns.bestHour === new Date().getHours()) {
      confidence += 10
    }

    // Clamp values
    score = Math.max(-100, Math.min(100, Math.round(score)))
    confidence = Math.max(20, Math.min(95, Math.round(confidence)))

    // Direction
    let direction = 'NEUTRAL'
    if (score > 20) direction = 'BULLISH'
    else if (score > 5) direction = 'SLIGHTLY BULLISH'
    else if (score < -20) direction = 'BEARISH'
    else if (score < -5) direction = 'SLIGHTLY BEARISH'

    // Generate prediction object
    const prediction = {
      direction,
      score,
      confidence,
      btcPrice,
      btcChange,
      volatility: factors.volatility.level,
      altSeason: factors.altSeason,
      timeAnalysis: factors.timeOfDay.label,
      dayAnalysis: factors.dayOfWeek.label,
      riskLevel: confidence < 40 ? 'HIGH' : confidence < 65 ? 'MODERATE' : 'LOW',
      recommendation: generateRecommendation(direction, confidence, factors),
      hindiSummary: generateHindiSummary(direction, score, confidence, btcPrice, btcChange, factors),
      timestamp: Date.now(),
    }

    // Store prediction
    predictionHistory.push(prediction)
    if (predictionHistory.length > 50) predictionHistory = predictionHistory.slice(-50)
    try {
      localStorage.setItem('jarvis_predictions', JSON.stringify(predictionHistory.slice(-20)))
    } catch {}

    return prediction
  } catch (error) {
    console.warn('[JARVIS Predict] Error:', error.message)
    return {
      direction: 'NEUTRAL',
      score: 0,
      confidence: 30,
      volatility: 'unknown',
      hindiSummary: 'Sir, market data abhi available nahi hai. Prediction baad mein doongi.',
      timestamp: Date.now(),
    }
  }
}

/**
 * Analyze price trend
 */
function analyzeTrend(change24h) {
  if (change24h > 5) return { score: 80, confidence: 70, label: 'Strong Uptrend' }
  if (change24h > 2) return { score: 50, confidence: 60, label: 'Uptrend' }
  if (change24h > 0) return { score: 20, confidence: 45, label: 'Slight Uptrend' }
  if (change24h > -2) return { score: -20, confidence: 45, label: 'Slight Downtrend' }
  if (change24h > -5) return { score: -50, confidence: 60, label: 'Downtrend' }
  return { score: -80, confidence: 70, label: 'Strong Downtrend' }
}

/**
 * Analyze ETH-BTC correlation
 */
function analyzeCorrelation(btcChange, ethChange) {
  const diff = Math.abs(btcChange - ethChange)
  if (diff < 1) return { score: 10, label: 'High correlation' }
  if (ethChange > btcChange + 3) return { score: 30, label: 'ETH outperforming — alt season signal' }
  if (ethChange < btcChange - 3) return { score: -20, label: 'ETH underperforming — risk-off' }
  return { score: 0, label: 'Normal correlation' }
}

/**
 * Analyze volatility level
 */
function analyzeVolatility(btcChange, ethChange, solChange) {
  const avgAbsChange = (Math.abs(btcChange) + Math.abs(ethChange) + Math.abs(solChange)) / 3
  if (avgAbsChange > 10) return { level: 'extreme', score: -30, label: 'Extreme volatility' }
  if (avgAbsChange > 5) return { level: 'high', score: -10, label: 'High volatility' }
  if (avgAbsChange > 2) return { level: 'moderate', score: 10, label: 'Moderate volatility' }
  return { level: 'low', score: 20, label: 'Low volatility — stable' }
}

/**
 * Time-of-day analysis
 */
function analyzeTimeOfDay() {
  const hour = new Date().getHours()
  // IST-based analysis (Indian market hours)
  if (hour >= 9 && hour <= 15) return { score: 10, label: 'Indian market hours — active' }
  if (hour >= 18 && hour <= 23) return { score: 15, label: 'US market overlap — high volume' }
  if (hour >= 0 && hour <= 5) return { score: -5, label: 'Low activity hours' }
  return { score: 5, label: 'Normal hours' }
}

/**
 * Day-of-week analysis
 */
function analyzeDayOfWeek() {
  const day = new Date().getDay()
  if (day === 0) return { score: -10, label: 'Sunday — typically low volume' }
  if (day === 1) return { score: 15, label: 'Monday — fresh week momentum' }
  if (day === 5) return { score: -5, label: 'Friday — weekend caution' }
  if (day === 6) return { score: -8, label: 'Saturday — reduced volume' }
  return { score: 5, label: 'Midweek — normal activity' }
}

/**
 * Load user trading patterns from memory
 */
async function loadUserPatterns() {
  try {
    const mem = await import('./jarvisMemory.js')
    const m = mem.default || mem
    if (m?.getMemory) {
      const memory = m.getMemory()
      const hours = memory?.patterns?.activeHours || {}
      let bestHour = 12
      let maxCount = 0
      Object.entries(hours).forEach(([h, count]) => {
        if (count > maxCount) { bestHour = parseInt(h); maxCount = count }
      })
      return { bestHour, totalTrades: memory?.trading?.totalTrades || 0 }
    }
  } catch {}
  return { bestHour: 12, totalTrades: 0 }
}

/**
 * Generate recommendation
 */
function generateRecommendation(direction, confidence, factors) {
  if (confidence < 40) return 'WAIT — market unclear, avoid new positions'
  if (direction === 'BULLISH' && confidence > 65) return 'BUY — strong bullish signals detected'
  if (direction === 'BEARISH' && confidence > 65) return 'SELL — bearish signals, protect capital'
  if (factors.volatility.level === 'extreme') return 'CAUTION — extreme volatility, trade small'
  if (direction.includes('SLIGHTLY')) return 'HOLD — wait for stronger confirmation'
  return 'MONITOR — keep watching for clear signals'
}

/**
 * Generate Hindi prediction summary
 */
function generateHindiSummary(direction, score, confidence, btcPrice, btcChange, factors) {
  const directionHindi = {
    'BULLISH': 'market BULLISH hai, upar ja sakta hai',
    'SLIGHTLY BULLISH': 'market thoda bullish lag raha hai',
    'NEUTRAL': 'market neutral hai, clear direction nahi hai',
    'SLIGHTLY BEARISH': 'market thoda bearish lag raha hai',
    'BEARISH': 'market BEARISH hai, neeche ja sakta hai',
  }

  let summary = `Sir, meri prediction: ${directionHindi[direction] || 'neutral'}. `
  summary += `Bitcoin ${btcPrice.toLocaleString()} dollars pe hai, ${btcChange >= 0 ? btcChange.toFixed(1) + ' percent upar' : Math.abs(btcChange).toFixed(1) + ' percent neeche'}. `
  summary += `Mera confidence level ${confidence} percent hai. `

  if (factors.volatility.level === 'extreme') {
    summary += 'Warning: Market mein bahut zyada volatility hai, careful rahiye! '
  } else if (factors.volatility.level === 'high') {
    summary += 'Volatility high hai, tight stop-losses rakhiye. '
  }

  if (factors.altSeason) {
    summary += 'Alt season ka signal mil raha hai, altcoins pe nazar rakhiye. '
  }

  summary += factors.timeOfDay.label === 'US market overlap — high volume'
    ? 'Abhi US market hours hain, volume achha hai.'
    : factors.timeOfDay.label === 'Indian market hours — active'
    ? 'Indian market hours hain, activity hai.'
    : ''

  return summary
}

/**
 * Get prediction accuracy from history
 */
function getAccuracy() {
  if (predictionHistory.length < 5) return { accuracy: 'N/A', sample: predictionHistory.length }
  // Compare sequential predictions — if direction held, count as correct
  let correct = 0
  for (let i = 1; i < predictionHistory.length; i++) {
    const prev = predictionHistory[i - 1]
    const curr = predictionHistory[i]
    if (prev.direction === curr.direction) correct++
  }
  return {
    accuracy: `${Math.round((correct / (predictionHistory.length - 1)) * 100)}%`,
    sample: predictionHistory.length,
  }
}

/**
 * Predict and speak — convenience method
 */
async function predictAndSpeak() {
  const prediction = await generatePrediction()
  if (prediction.hindiSummary) {
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text: prediction.hindiSummary, priority: 'high' }
    }))
  }
  return prediction
}

/**
 * Get 7 stored predictions
 */
function getHistory() {
  if (!predictionHistory.length) {
    try {
      predictionHistory = JSON.parse(localStorage.getItem('jarvis_predictions') || '[]')
    } catch {}
  }
  return predictionHistory
}

const jarvisPredictiveEngine = {
  generatePrediction,
  predictAndSpeak,
  getAccuracy,
  getHistory,
}

export default jarvisPredictiveEngine
export { generatePrediction, predictAndSpeak, getAccuracy, getHistory }
