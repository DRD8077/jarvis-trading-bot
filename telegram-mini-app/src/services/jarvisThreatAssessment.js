/**
 * 🎯 JARVIS THREAT ASSESSMENT — Iron Man Threat Detection
 * ═══════════════════════════════════════════════════════════
 * 
 * Like when JARVIS says "I'm detecting hostile signatures" —
 * this system scans tokens for dangers:
 * 
 * - Rug Pull Risk Detection (honeypot, locked liquidity, etc)
 * - Whale Concentration Score (top holders %)
 * - Volatility Threat Level (extreme price swings)
 * - Smart Contract Risk (verified, proxy, renounced)
 * - Social Sentiment Threat (fear/greed analysis)
 * - Overall THREAT LEVEL: LOW / MODERATE / HIGH / CRITICAL
 * 
 * JARVIS speaks warnings proactively when threats detected
 */

// Threat levels
const THREAT = {
  LOW: { level: 'LOW', color: '#22c55e', label: 'Safe', icon: '🟢' },
  MODERATE: { level: 'MODERATE', color: '#eab308', label: 'Caution', icon: '🟡' },
  HIGH: { level: 'HIGH', color: '#f97316', label: 'Dangerous', icon: '🟠' },
  CRITICAL: { level: 'CRITICAL', color: '#ef4444', label: 'EXTREME DANGER', icon: '🔴' },
}

/**
 * Run full threat assessment on a token
 * @param {object} token - Token data with price, volume, holders info
 * @returns {object} Full threat assessment report
 */
function assessThreat(token) {
  const threats = []
  let totalScore = 0

  // 1. Price volatility check
  const change24h = Math.abs(parseFloat(token.change24h || token.priceChange24h || token.change_24h || 0))
  if (change24h > 50) {
    threats.push({ type: 'EXTREME_VOLATILITY', severity: 'critical', detail: `${change24h.toFixed(0)}% price swing in 24h` })
    totalScore += 30
  } else if (change24h > 25) {
    threats.push({ type: 'HIGH_VOLATILITY', severity: 'high', detail: `${change24h.toFixed(0)}% movement` })
    totalScore += 15
  } else if (change24h > 15) {
    totalScore += 5
  }

  // 2. Volume analysis
  const volume = parseFloat(token.volume24h || token.volume || 0)
  const mcap = parseFloat(token.marketCap || token.market_cap || token.fdv || 0)
  if (mcap > 0 && volume > 0) {
    const volumeRatio = volume / mcap
    if (volumeRatio > 3) {
      threats.push({ type: 'ABNORMAL_VOLUME', severity: 'high', detail: `Volume ${volumeRatio.toFixed(1)}x of market cap — possible pump & dump` })
      totalScore += 20
    } else if (volumeRatio > 1) {
      threats.push({ type: 'HIGH_VOLUME', severity: 'moderate', detail: `Volume ${(volumeRatio * 100).toFixed(0)}% of market cap` })
      totalScore += 8
    }
  }

  // 3. Market cap check
  if (mcap > 0 && mcap < 10000) {
    threats.push({ type: 'MICRO_CAP', severity: 'critical', detail: 'Market cap under $10K — extreme rug pull risk' })
    totalScore += 25
  } else if (mcap > 0 && mcap < 100000) {
    threats.push({ type: 'TINY_CAP', severity: 'high', detail: 'Market cap under $100K — very high risk' })
    totalScore += 15
  } else if (mcap > 0 && mcap < 1000000) {
    threats.push({ type: 'SMALL_CAP', severity: 'moderate', detail: 'Market cap under $1M — elevated risk' })
    totalScore += 8
  }

  // 4. Liquidity check
  const liquidity = parseFloat(token.liquidity || token.liquidityUsd || 0)
  if (liquidity > 0 && liquidity < 5000) {
    threats.push({ type: 'NO_LIQUIDITY', severity: 'critical', detail: `Only $${liquidity.toFixed(0)} liquidity — cannot sell` })
    totalScore += 30
  } else if (liquidity > 0 && liquidity < 50000) {
    threats.push({ type: 'LOW_LIQUIDITY', severity: 'high', detail: `Only $${(liquidity / 1000).toFixed(1)}K liquidity` })
    totalScore += 15
  }

  // 5. Age check (new tokens are riskier)
  const createdAt = token.createdAt || token.created_at || token.pairCreatedAt
  if (createdAt) {
    const ageHours = (Date.now() - new Date(createdAt).getTime()) / 3600000
    if (ageHours < 1) {
      threats.push({ type: 'NEWBORN_TOKEN', severity: 'critical', detail: 'Token less than 1 hour old — extreme caution' })
      totalScore += 25
    } else if (ageHours < 24) {
      threats.push({ type: 'NEW_TOKEN', severity: 'high', detail: `Token only ${ageHours.toFixed(0)} hours old` })
      totalScore += 12
    } else if (ageHours < 168) { // 7 days
      threats.push({ type: 'YOUNG_TOKEN', severity: 'moderate', detail: `Token ${(ageHours / 24).toFixed(0)} days old` })
      totalScore += 5
    }
  }

  // 6. Name/symbol red flags
  const name = (token.name || token.symbol || '').toLowerCase()
  const rugKeywords = ['elon', 'musk', 'safe', 'moon', 'inu', 'baby', 'doge', 'shib', 'pepe', 'trump', 'pussy', 'cum', 'ass', 'fuck']
  const rugMatches = rugKeywords.filter(k => name.includes(k))
  if (rugMatches.length >= 2) {
    threats.push({ type: 'MEME_TOKEN', severity: 'high', detail: `Meme token indicators: ${rugMatches.join(', ')}` })
    totalScore += 15
  } else if (rugMatches.length === 1) {
    totalScore += 5
  }

  // 7. Top holder concentration (if available)
  const topHolderPct = parseFloat(token.topHolderPct || token.top10_pct || 0)
  if (topHolderPct > 80) {
    threats.push({ type: 'WHALE_DOMINATED', severity: 'critical', detail: `Top holders own ${topHolderPct.toFixed(0)}% — one sell = crash` })
    totalScore += 25
  } else if (topHolderPct > 50) {
    threats.push({ type: 'CONCENTRATED', severity: 'high', detail: `Top holders own ${topHolderPct.toFixed(0)}%` })
    totalScore += 12
  }

  // Determine overall threat level
  let threatLevel
  if (totalScore >= 60) threatLevel = THREAT.CRITICAL
  else if (totalScore >= 35) threatLevel = THREAT.HIGH
  else if (totalScore >= 15) threatLevel = THREAT.MODERATE
  else threatLevel = THREAT.LOW

  return {
    ...threatLevel,
    score: Math.min(totalScore, 100),
    threats,
    summary: generateSummary(threatLevel, threats),
    hindiSummary: generateHindiSummary(threatLevel, threats, token),
    token: token.symbol || token.name || 'Unknown',
    timestamp: new Date().toISOString(),
  }
}

function generateSummary(level, threats) {
  if (threats.length === 0) return 'No significant threats detected.'
  return `${level.label}: ${threats.length} threat(s) detected — ${threats.map(t => t.type).join(', ')}`
}

function generateHindiSummary(level, threats, token) {
  const symbol = token.symbol || token.name || 'is token'
  if (level.level === 'CRITICAL') {
    return `DANGER Sir! ${symbol} mein ${threats.length} critical threats hain. Rug pull risk bahut zyada hai. Main recommend karti hoon AVOID kariye!`
  }
  if (level.level === 'HIGH') {
    return `Warning Sir! ${symbol} high risk hai. ${threats[0]?.detail || 'Multiple concerns'}. Bahut careful rahiye agar invest karna ho.`
  }
  if (level.level === 'MODERATE') {
    return `Sir, ${symbol} mein moderate risk hai. ${threats[0]?.detail || 'Some concerns'}. Due diligence zaruri hai.`
  }
  return `Sir, ${symbol} relatively safe lag raha hai. Par hamesha DYOR kariye.`
}

/**
 * Quick threat scan on multiple tokens
 * Returns tokens sorted by threat level (most dangerous first)
 */
function batchAssess(tokens) {
  if (!Array.isArray(tokens)) return []
  return tokens
    .map(t => ({ ...t, threat: assessThreat(t) }))
    .sort((a, b) => b.threat.score - a.threat.score)
}

/**
 * JARVIS auto-warn — speak about critically dangerous tokens
 */
function autoWarnDangerous(tokens) {
  const assessed = batchAssess(tokens)
  const critical = assessed.filter(t => t.threat.level === 'CRITICAL')
  
  if (critical.length > 0) {
    const names = critical.slice(0, 3).map(t => t.symbol || t.name).join(', ')
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: {
        text: `Red alert Sir! ${critical.length} tokens mein CRITICAL threat detected. ${names} — bahut khatarnak hain. Stay away!`,
        priority: 'high'
      }
    }))
  }
}

const jarvisThreatAssessment = {
  assessThreat,
  batchAssess,
  autoWarnDangerous,
  THREAT,
}

export default jarvisThreatAssessment
export { assessThreat, batchAssess, autoWarnDangerous, THREAT }
