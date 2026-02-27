import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Target, Play, Pause, RefreshCw, Shield, AlertTriangle, Zap,
  TrendingUp, TrendingDown, Settings2, DollarSign, Clock, Globe,
  Brain, Rocket, BarChart3, ArrowUpRight, ChevronDown, Eye, Volume2
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { getApiBase } from '../services/apiBase'

// ═══════════════════════════════════════════════════════════════
// 🤖 AI AUTO SNIPER — JARVIS Finds & Trades Gems Automatically
// ═══════════════════════════════════════════════════════════════
// - Scans DexScreener, Pump.fun every 15s
// - AI scores each token for moonshot potential
// - Auto-snipes tokens matching your criteria
// - Paper mode by default (no real money until exchange connected)
// - Stop-loss + take-profit automation
// ═══════════════════════════════════════════════════════════════

const AIAutoSniper = () => {
  const { hapticFeedback } = useApp()
  const base = getApiBase()
  const [isActive, setIsActive] = useState(false)
  const [mode, setMode] = useState('paper') // paper or live
  const [config, setConfig] = useState({
    maxBudget: 2000,           // ₹2000 per trade
    minMoonScore: 70,          // Min AI score to buy
    maxPositions: 5,           // Max concurrent positions
    stopLoss: -15,             // -15% stop loss
    takeProfit: 100,           // +100% take profit (2x)
    targetChains: ['solana', 'bsc', 'ethereum'],
    minLiquidity: 1000,        // Min $1K liquidity
    maxMarketCap: 500000,      // Max $500K mcap (micro-cap only)
    autoBuyDips: true,         // Buy tokens at -5% or more
    dipThreshold: -5,          // Min dip to trigger buy
  })
  const [showConfig, setShowConfig] = useState(false)
  const [positions, setPositions] = useState([])
  const [tradeHistory, setTradeHistory] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [stats, setStats] = useState({
    totalScanned: 0, totalBought: 0, totalSold: 0,
    totalPnl: 0, winRate: 0, bestTrade: 0,
  })
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const mountedRef = useRef(true)
  const scanTimerRef = useRef(null)

  const addLog = useCallback((msg, type = 'info') => {
    const entry = { msg, type, ts: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }
    setLogs(prev => [entry, ...prev].slice(0, 50))
  }, [])

  // ═══ SCAN FOR OPPORTUNITIES ═══
  const scanMarket = useCallback(async () => {
    if (!mountedRef.current) return
    setLoading(true)
    addLog('🔍 Scanning DexScreener + Pump.fun + backend...', 'scan')

    const allTokens = []

    // 1. DexScreener trending
    try {
      const res = await fetch(`${base}/dex/trending`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        const trending = data?.trending || []
        allTokens.push(...trending.map(t => ({ ...t, source: 'DexScreener' })))
        addLog(`📊 DexScreener: ${trending.length} tokens`, 'data')
      }
    } catch {}

    // 2. Direct DexScreener API
    try {
      const res = await fetch('https://api.dexscreener.com/token-boosts/latest/v1', { signal: AbortSignal.timeout(8000) })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          allTokens.push(...data.slice(0, 20).map(b => ({
            symbol: b.tokenAddress?.slice(0, 8),
            base_address: b.tokenAddress,
            chain: b.chainId || 'solana',
            source: 'DexBoost',
            price_usd: 0, change_24h: 0, volume_24h: 0, liquidity_usd: 0, market_cap: 0,
          })))
        }
      }
    } catch {}

    // 3. Pump.fun live
    try {
      const res = await fetch('https://frontend-api-v3.pump.fun/coins/currently-live?limit=20&offset=0&includeNsfw=false', { signal: AbortSignal.timeout(8000) })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          allTokens.push(...data.map(p => ({
            symbol: p.symbol || p.name?.slice(0, 6),
            name: p.name,
            base_address: p.mint || p.address,
            chain: 'solana',
            price_usd: p.usd_market_cap ? p.usd_market_cap / (p.total_supply || 1e9) : 0,
            market_cap: p.usd_market_cap || 0,
            volume_24h: p.volume_24h || 0,
            change_24h: p.price_change_24h || 0,
            liquidity_usd: p.virtual_sol_reserves ? p.virtual_sol_reserves * 140 : 0,
            source: 'Pump.fun',
          })))
          addLog(`🎰 Pump.fun: ${data.length} live tokens`, 'data')
        }
      }
    } catch {}

    // 4. Backend gems
    try {
      const res = await fetch(`${base}/gems`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        const gems = data?.gems || data?.data?.gems || []
        allTokens.push(...gems.map(t => ({ ...t, source: 'AI Gems' })))
        addLog(`💎 AI Gems: ${gems.length} found`, 'data')
      }
    } catch {}

    // 5. Backend sniper
    try {
      const res = await fetch(`${base}/sniper/opportunities`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        const opps = data?.opportunities || []
        allTokens.push(...opps.map(t => ({ ...t, source: 'Sniper' })))
      }
    } catch {}

    // Score and filter
    const scored = allTokens.map(t => ({
      ...t,
      moonScore: calcMoonScore(t),
    })).filter(t => {
      const mcap = t.market_cap || 0
      const liq = t.liquidity_usd || 0
      const ch = (t.chain || '').toLowerCase()
      // Apply filters
      if (config.targetChains.length > 0 && !config.targetChains.includes(ch) && ch !== '') return true // keep if unknown chain
      if (mcap > config.maxMarketCap && mcap > 0) return false
      if (liq < config.minLiquidity && liq > 0) return false
      return true
    }).sort((a, b) => (b.moonScore || 0) - (a.moonScore || 0))

    if (!mountedRef.current) return

    setOpportunities(scored.slice(0, 30))
    setStats(prev => ({ ...prev, totalScanned: prev.totalScanned + allTokens.length }))
    setLoading(false)

    // AUTO-BUY logic (paper mode)
    if (isActive && mode === 'paper') {
      const eligible = scored.filter(t => {
        if ((t.moonScore || 0) < config.minMoonScore) return false
        if (positions.length >= config.maxPositions) return false
        if (config.autoBuyDips && (t.change_24h || 0) > config.dipThreshold) return false
        // Don't buy same token twice
        const addr = t.base_address || t.pair_address || ''
        if (positions.find(p => p.address === addr)) return false
        return true
      })

      for (const token of eligible.slice(0, 1)) { // Buy max 1 per scan
        const pos = {
          symbol: token.symbol || token.base_token || '???',
          address: token.base_address || token.pair_address || '',
          chain: token.chain || 'unknown',
          entryPrice: token.price_usd || 0,
          currentPrice: token.price_usd || 0,
          amount: config.maxBudget,
          moonScore: token.moonScore,
          pnl: 0,
          pnlPercent: 0,
          buyTime: Date.now(),
          source: token.source,
          status: 'open',
        }
        setPositions(prev => [...prev, pos])
        setStats(prev => ({ ...prev, totalBought: prev.totalBought + 1 }))
        addLog(`🟢 AUTO-BUY: ${pos.symbol} @ ${formatPrice(pos.entryPrice)} | Score: ${pos.moonScore} | ₹${config.maxBudget}`, 'buy')
        hapticFeedback?.('success')
        // ═══ JARVIS VOICE — announce buy ═══
        try {
          window.dispatchEvent(new CustomEvent('jarvis-speak', {
            detail: { text: `Sir, ${pos.symbol} kharida! Score ${pos.moonScore}, amount ${config.maxBudget} rupaye. Moon potential hai!`, priority: 'high' }
          }))
        } catch {}
      }
    }

    addLog(`✅ Scan complete: ${scored.length} tokens scored, ${scored.filter(t => t.moonScore >= 70).length} moonshots`, 'success')
  }, [base, config, isActive, mode, positions, addLog, hapticFeedback])

  // ═══ SIMULATE PRICE UPDATES (paper mode) ═══
  useEffect(() => {
    if (positions.length === 0) return
    const timer = setInterval(() => {
      setPositions(prev => prev.map(p => {
        if (p.status !== 'open') return p
        // Simulate price movement (±5% per tick for micro-caps)
        const change = (Math.random() - 0.45) * 0.1 // Slight upward bias for moonshots
        const newPrice = p.currentPrice * (1 + change)
        const pnlPercent = ((newPrice - p.entryPrice) / p.entryPrice) * 100
        const pnl = (pnlPercent / 100) * p.amount

        // Auto stop-loss / take-profit
        if (pnlPercent <= config.stopLoss) {
          addLog(`🔴 STOP-LOSS: ${p.symbol} @ ${pnlPercent.toFixed(1)}% | Lost ₹${Math.abs(pnl).toFixed(0)}`, 'sell')
          hapticFeedback?.('error')
          // ═══ JARVIS VOICE — announce stop loss ═══
          try {
            window.dispatchEvent(new CustomEvent('jarvis-speak', {
              detail: { text: `Warning Sir! ${p.symbol} pe stop loss trigger hua. ${Math.abs(pnl).toFixed(0)} rupaye ka loss. Position close ho gayi.`, priority: 'high' }
            }))
          } catch {}
          setStats(prev => ({ ...prev, totalSold: prev.totalSold + 1, totalPnl: prev.totalPnl + pnl }))
          setTradeHistory(prev => [{ ...p, exitPrice: newPrice, pnl, pnlPercent, exitTime: Date.now(), reason: 'Stop Loss' }, ...prev])
          return { ...p, currentPrice: newPrice, pnl, pnlPercent, status: 'closed-sl' }
        }
        if (pnlPercent >= config.takeProfit) {
          addLog(`🟢 TAKE-PROFIT: ${p.symbol} @ +${pnlPercent.toFixed(1)}% | Profit ₹${pnl.toFixed(0)}`, 'sell')
          hapticFeedback?.('success')
          // ═══ JARVIS VOICE — announce take profit ═══
          try {
            window.dispatchEvent(new CustomEvent('jarvis-speak', {
              detail: { text: `Congratulations Sir! ${p.symbol} pe target hit! ${pnl.toFixed(0)} rupaye ka profit! Bohot badhiya trade!`, priority: 'high' }
            }))
          } catch {}
          setStats(prev => ({ ...prev, totalSold: prev.totalSold + 1, totalPnl: prev.totalPnl + pnl }))
          setTradeHistory(prev => [{ ...p, exitPrice: newPrice, pnl, pnlPercent, exitTime: Date.now(), reason: 'Take Profit' }, ...prev])
          return { ...p, currentPrice: newPrice, pnl, pnlPercent, status: 'closed-tp' }
        }

        return { ...p, currentPrice: newPrice, pnl, pnlPercent }
      }))
    }, 3000)
    return () => clearInterval(timer)
  }, [positions.length, config.stopLoss, config.takeProfit, addLog, hapticFeedback])

  // ═══ AUTO-SCAN TIMER ═══
  useEffect(() => {
    mountedRef.current = true
    scanMarket() // Initial scan
    if (isActive) {
      scanTimerRef.current = setInterval(scanMarket, 15000)
    }
    return () => {
      mountedRef.current = false
      if (scanTimerRef.current) clearInterval(scanTimerRef.current)
    }
  }, [isActive]) // eslint-disable-line

  // Calculate win rate
  useEffect(() => {
    const closed = tradeHistory.length
    if (closed > 0) {
      const wins = tradeHistory.filter(t => t.pnl > 0).length
      const best = Math.max(0, ...tradeHistory.map(t => t.pnlPercent || 0))
      setStats(prev => ({ ...prev, winRate: (wins / closed * 100), bestTrade: best }))
    }
  }, [tradeHistory])

  function calcMoonScore(token) {
    let score = 50
    const mcap = token.market_cap || 0
    const vol = token.volume_24h || 0
    const change = token.change_24h || 0
    if (mcap > 0 && mcap < 10000) score += 25
    else if (mcap < 50000) score += 20
    else if (mcap < 200000) score += 15
    else if (mcap < 1000000) score += 10
    if (mcap > 0 && vol > mcap * 2) score += 15
    else if (mcap > 0 && vol > mcap) score += 10
    if (change <= -20) score += 15
    else if (change <= -10) score += 10
    else if (change <= -5) score += 5
    const bsr = token.buy_sell_ratio || 1
    if (bsr > 1.5) score += 5
    return Math.max(10, Math.min(99, score))
  }

  const formatPrice = (p) => {
    if (!p) return '-'
    if (p >= 1) return '$' + p.toFixed(4)
    if (p >= 0.001) return '$' + p.toFixed(6)
    return '$' + p.toExponential(3)
  }

  const formatNum = (n) => {
    if (!n) return '-'
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M'
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K'
    return '$' + n.toFixed(0)
  }

  const openPositions = positions.filter(p => p.status === 'open')
  const totalOpenPnl = openPositions.reduce((sum, p) => sum + (p.pnl || 0), 0)

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-purple-950/20 pb-24">
      {/* ═══ Header ═══ */}
      <div className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-lg border-b border-cyan-500/20 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-lg ${
              isActive ? 'bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-emerald-500/30 animate-pulse' 
                       : 'bg-gradient-to-br from-slate-600 to-slate-700'
            }`}>
              <Target size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">AI Auto Sniper</h1>
              <p className="text-[10px] text-cyan-300/70">
                {mode === 'paper' ? '📝 Paper Mode' : '💰 LIVE Mode'} • {isActive ? '🟢 Active' : '⏸️ Paused'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { setShowConfig(!showConfig); hapticFeedback?.('impact') }}
              className="p-1.5 bg-slate-800 rounded-lg border border-slate-700">
              <Settings2 size={14} className="text-slate-400" />
            </button>
            <button onClick={() => {
              setIsActive(!isActive)
              hapticFeedback?.('impact')
              addLog(isActive ? '⏸️ Sniper PAUSED' : '🟢 Sniper ACTIVATED — hunting gems...', isActive ? 'info' : 'success')
            }}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1 ${
                isActive 
                  ? 'bg-red-600 text-white shadow-lg shadow-red-500/30' 
                  : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/30'
              }`}>
              {isActive ? <><Pause size={12} /> STOP</> : <><Play size={12} /> START</>}
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="bg-slate-800/50 rounded-lg py-1.5">
            <p className="text-[9px] text-slate-500">Scanned</p>
            <p className="text-[11px] font-bold text-white">{stats.totalScanned}</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg py-1.5">
            <p className="text-[9px] text-slate-500">Bought</p>
            <p className="text-[11px] font-bold text-emerald-400">{stats.totalBought}</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg py-1.5">
            <p className="text-[9px] text-slate-500">Win Rate</p>
            <p className="text-[11px] font-bold text-cyan-400">{stats.winRate.toFixed(0)}%</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg py-1.5">
            <p className="text-[9px] text-slate-500">Total P&L</p>
            <p className={`text-[11px] font-bold ${stats.totalPnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              ₹{stats.totalPnl.toFixed(0)}
            </p>
          </div>
        </div>
      </div>

      {/* ═══ Config Panel ═══ */}
      {showConfig && (
        <div className="mx-3 mt-2 bg-slate-800 border border-slate-700 rounded-xl p-3 space-y-3">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <Settings2 size={12} /> Sniper Configuration
          </h3>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-slate-400">Budget per trade (₹)</label>
              <input type="number" value={config.maxBudget}
                onChange={e => setConfig(prev => ({ ...prev, maxBudget: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Min Moon Score</label>
              <input type="number" value={config.minMoonScore} min={30} max={95}
                onChange={e => setConfig(prev => ({ ...prev, minMoonScore: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Stop Loss (%)</label>
              <input type="number" value={config.stopLoss} max={0}
                onChange={e => setConfig(prev => ({ ...prev, stopLoss: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Take Profit (%)</label>
              <input type="number" value={config.takeProfit} min={10}
                onChange={e => setConfig(prev => ({ ...prev, takeProfit: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Max Positions</label>
              <input type="number" value={config.maxPositions} min={1} max={20}
                onChange={e => setConfig(prev => ({ ...prev, maxPositions: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Dip Threshold (%)</label>
              <input type="number" value={config.dipThreshold} max={0}
                onChange={e => setConfig(prev => ({ ...prev, dipThreshold: Number(e.target.value) }))}
                className="w-full bg-slate-700 rounded-lg px-2 py-1.5 text-xs text-white mt-0.5" />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-[10px] text-slate-400">Auto-Buy Dips</label>
            <button onClick={() => setConfig(prev => ({ ...prev, autoBuyDips: !prev.autoBuyDips }))}
              className={`w-10 h-5 rounded-full transition-all ${config.autoBuyDips ? 'bg-emerald-500' : 'bg-slate-600'}`}>
              <div className={`w-4 h-4 bg-white rounded-full transition-transform ${config.autoBuyDips ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-700">
            <span className="text-[10px] text-red-400 flex items-center gap-1">
              <AlertTriangle size={10} /> Paper mode — no real money
            </span>
          </div>
        </div>
      )}

      {/* ═══ Open Positions ═══ */}
      {openPositions.length > 0 && (
        <div className="mx-3 mt-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
              <BarChart3 size={12} className="text-cyan-400" /> Open Positions ({openPositions.length})
            </h3>
            <span className={`text-xs font-bold ${totalOpenPnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              P&L: ₹{totalOpenPnl.toFixed(0)}
            </span>
          </div>
          <div className="space-y-1.5">
            {openPositions.map((p, i) => (
              <div key={i} className={`flex items-center gap-3 p-2.5 rounded-xl border ${
                (p.pnlPercent || 0) >= 0 ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
              }`}>
                <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-xs font-bold text-white">
                  {(p.moonScore || 0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-white">{p.symbol}</span>
                    <span className="text-[8px] px-1 py-0.5 bg-slate-700/50 rounded text-slate-400">{p.chain}</span>
                    <span className="text-[8px] text-slate-500">{p.source}</span>
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Entry: {formatPrice(p.entryPrice)} → Now: {formatPrice(p.currentPrice)}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-xs font-bold ${(p.pnlPercent || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(p.pnlPercent || 0) >= 0 ? '+' : ''}{(p.pnlPercent || 0).toFixed(1)}%
                  </p>
                  <p className={`text-[10px] ${(p.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    ₹{(p.pnl || 0).toFixed(0)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Top Opportunities ═══ */}
      <div className="mx-3 mt-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
            <Rocket size={12} className="text-purple-400" /> Top Opportunities
          </h3>
          <button onClick={() => { scanMarket(); hapticFeedback?.('impact') }}
            className="text-[10px] text-cyan-400 flex items-center gap-1">
            <RefreshCw size={10} className={loading ? 'animate-spin' : ''} /> Scan Now
          </button>
        </div>
        <div className="space-y-1.5">
          {opportunities.slice(0, 10).map((t, i) => (
            <div key={i} className={`flex items-center gap-2.5 p-2.5 rounded-xl border ${
              (t.moonScore || 0) >= 85 ? 'bg-yellow-500/5 border-yellow-500/20' :
              (t.moonScore || 0) >= 70 ? 'bg-emerald-500/5 border-emerald-500/20' :
              'bg-slate-800/50 border-slate-700/30'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold ${
                (t.moonScore || 0) >= 85 ? 'bg-yellow-500/20 text-yellow-300' :
                (t.moonScore || 0) >= 70 ? 'bg-emerald-500/20 text-emerald-300' :
                'bg-slate-700 text-slate-400'
              }`}>
                {t.moonScore || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold text-white truncate">{t.symbol || t.base_token || '???'}</span>
                  <span className="text-[8px] text-slate-500">{t.chain || '-'}</span>
                  <span className="text-[8px] text-purple-400">{t.source}</span>
                </div>
                <p className="text-[9px] text-slate-500">MCap: {formatNum(t.market_cap)} • Vol: {formatNum(t.volume_24h)}</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold text-white">{formatPrice(t.price_usd)}</p>
                <span className={`text-[10px] font-bold ${(t.change_24h || 0) <= -5 ? 'text-red-400' : (t.change_24h || 0) >= 10 ? 'text-emerald-400' : 'text-slate-400'}`}>
                  {(t.change_24h || 0) > 0 ? '+' : ''}{(t.change_24h || 0).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══ Trade History ═══ */}
      {tradeHistory.length > 0 && (
        <div className="mx-3 mt-3">
          <h3 className="text-xs font-bold text-white mb-2 flex items-center gap-1.5">
            <Clock size={12} className="text-slate-400" /> Trade History
          </h3>
          <div className="space-y-1">
            {tradeHistory.slice(0, 10).map((t, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg text-[10px]">
                <span className={`font-bold ${t.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {t.pnl >= 0 ? '🟢' : '🔴'} {t.symbol}
                </span>
                <span className="text-slate-500">→ {t.reason}</span>
                <span className={`ml-auto font-bold ${t.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {t.pnl >= 0 ? '+' : ''}₹{t.pnl.toFixed(0)} ({t.pnlPercent >= 0 ? '+' : ''}{t.pnlPercent.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Live Logs ═══ */}
      <div className="mx-3 mt-3">
        <h3 className="text-xs font-bold text-white mb-2 flex items-center gap-1.5">
          <Eye size={12} className="text-slate-400" /> Live Scanner Log
        </h3>
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-2 max-h-40 overflow-y-auto font-mono">
          {logs.length === 0 ? (
            <p className="text-[10px] text-slate-600 text-center py-3">Press START to begin scanning...</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className={`text-[9px] py-0.5 ${
                log.type === 'buy' ? 'text-emerald-400' :
                log.type === 'sell' ? 'text-red-400' :
                log.type === 'success' ? 'text-cyan-400' :
                log.type === 'data' ? 'text-blue-400' :
                'text-slate-400'
              }`}>
                <span className="text-slate-600">[{log.ts}]</span> {log.msg}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ═══ Disclaimer ═══ */}
      <div className="mx-3 mt-3 p-2.5 bg-red-500/5 border border-red-500/10 rounded-xl">
        <p className="text-[9px] text-red-400/60 flex items-center gap-1">
          <AlertTriangle size={10} /> Paper mode only — no real money is used. Connect exchange in Settings for live trading. Micro-cap tokens are extremely risky.
        </p>
      </div>
    </div>
  )
}

export default AIAutoSniper
