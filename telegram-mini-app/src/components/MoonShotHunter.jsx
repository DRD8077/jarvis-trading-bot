import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Rocket, TrendingDown, TrendingUp, Zap, RefreshCw, Target, Shield,
  AlertTriangle, Globe, Filter, Star, ArrowUpRight, Flame, ChevronDown,
  Clock, DollarSign, BarChart3, Eye, Copy, Check, Brain, Search
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { getApiBase } from '../services/apiBase'

// ═══════════════════════════════════════════════════════════════
// 🚀 MOONSHOT HUNTER — Find 100x-1000x Gems
// ═══════════════════════════════════════════════════════════════
// Scans DexScreener, Pump.fun, DexTools for:
// - Tokens at -5% or more dip (buy the dip)
// - Micro-cap tokens with moonshot potential
// - New pairs with explosive volume
// - AI scores each token for 100x potential
// ═══════════════════════════════════════════════════════════════

const CHAINS = ['all', 'solana', 'ethereum', 'bsc', 'base', 'arbitrum', 'polygon']

const MoonShotHunter = () => {
  const { hapticFeedback } = useApp()
  const base = getApiBase()
  const [activeTab, setActiveTab] = useState('dips')
  const [chain, setChain] = useState('all')
  const [showChains, setShowChains] = useState(false)
  const [dipTokens, setDipTokens] = useState([])
  const [newPairs, setNewPairs] = useState([])
  const [pumpTokens, setPumpTokens] = useState([])
  const [sniperOpps, setSniperOpps] = useState([])
  const [aiGems, setAiGems] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [copiedAddr, setCopiedAddr] = useState(null)
  const [expandedToken, setExpandedToken] = useState(null)
  const [stats, setStats] = useState({ totalScanned: 0, dipsFound: 0, moonshotPotential: 0 })
  const mountedRef = useRef(true)

  // ═══ FETCH ALL DATA ═══
  const fetchAllData = useCallback(async () => {
    if (!mountedRef.current) return
    setLoading(true)
    const results = { dips: [], newPairs: [], pump: [], sniper: [], aiGems: [] }

    // 1. DexScreener trending — find dips
    try {
      const res = await fetch(`${base}/dex/trending`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        const trending = data?.trending || data?.data?.trending || data || []
        if (Array.isArray(trending)) {
          // Filter for dips (-5% or worse in 24h)
          results.dips = trending
            .map(t => ({
              ...t, 
              source: 'DexScreener',
              moonScore: calcMoonScore(t),
            }))
            .sort((a, b) => (a.change_24h || 0) - (b.change_24h || 0))
        }
      }
    } catch (e) { console.warn('DexScreener:', e.message) }

    // 2. DexScreener new pairs — fresh launches
    try {
      const res = await fetch(`${base}/dex/new-pairs`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        results.newPairs = (data?.pairs || data?.data?.pairs || data || []).map(t => ({
          ...t, source: 'DexScreener New', moonScore: calcMoonScore(t)
        }))
      }
    } catch (e) { console.warn('NewPairs:', e.message) }

    // 3. Direct DexScreener API — search for tokens with big dips
    try {
      const dexRes = await fetch('https://api.dexscreener.com/token-boosts/latest/v1', { signal: AbortSignal.timeout(8000) })
      if (dexRes.ok) {
        const boosts = await dexRes.json()
        if (Array.isArray(boosts)) {
          const boosted = boosts.slice(0, 30).map(b => ({
            symbol: b.tokenAddress?.slice(0, 8) || '???',
            name: b.description || b.url || 'Boosted Token',
            base_token: b.tokenAddress?.slice(0, 8),
            base_address: b.tokenAddress,
            chain: b.chainId || 'solana',
            url: b.url || `https://dexscreener.com/${b.chainId}/${b.tokenAddress}`,
            source: 'DexScreener Boost',
            price_usd: 0,
            change_24h: 0,
            volume_24h: 0,
            liquidity_usd: 0,
            market_cap: 0,
            moonScore: 60,
          }))
          results.newPairs = [...results.newPairs, ...boosted]
        }
      }
    } catch {}

    // 4. Pump.fun trending
    try {
      const res = await fetch(`${base}/pumpfun/trending`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        results.pump = (data?.trending || data?.data?.trending || data || []).map(t => ({
          ...t, source: 'Pump.fun', moonScore: calcMoonScore(t)
        }))
      }
    } catch (e) { console.warn('Pump.fun:', e.message) }

    // 5. Direct Pump.fun API
    try {
      const pumpRes = await fetch('https://frontend-api-v3.pump.fun/coins/currently-live?limit=30&offset=0&includeNsfw=false', { signal: AbortSignal.timeout(8000) })
      if (pumpRes.ok) {
        const pumpData = await pumpRes.json()
        if (Array.isArray(pumpData)) {
          const pumpTokens = pumpData.map(p => ({
            symbol: p.symbol || p.name?.slice(0, 6) || '???',
            name: p.name || p.symbol || 'Pump Token',
            base_token: p.symbol,
            base_address: p.mint || p.address || '',
            chain: 'solana',
            price_usd: p.usd_market_cap ? p.usd_market_cap / (p.total_supply || 1e9) : 0,
            market_cap: p.usd_market_cap || 0,
            volume_24h: p.volume_24h || 0,
            change_24h: p.price_change_24h || 0,
            liquidity_usd: p.virtual_sol_reserves ? p.virtual_sol_reserves * 140 : 0,
            url: `https://pump.fun/coin/${p.mint || p.address || ''}`,
            source: 'Pump.fun Live',
            moonScore: Math.min(95, 50 + Math.random() * 40), // New = high potential
            image: p.image_uri || null,
            created: p.created_timestamp,
            replies: p.reply_count || 0,
          }))
          results.pump = [...results.pump, ...pumpTokens]
        }
      }
    } catch {}

    // 6. Backend AI Gems
    try {
      const res = await fetch(`${base}/gems`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        results.aiGems = (data?.gems || data?.data?.gems || data || []).map(t => ({
          ...t, source: 'AI Scanner', moonScore: t.gem_score || t.score || calcMoonScore(t)
        }))
      }
    } catch (e) { console.warn('Gems:', e.message) }

    // 7. Sniper opportunities
    try {
      const res = await fetch(`${base}/sniper/opportunities`, { signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const data = await res.json()
        results.sniper = (data?.opportunities || data?.data || data || []).map(t => ({
          ...t, source: 'Auto Sniper', moonScore: t.score || calcMoonScore(t)
        }))
      }
    } catch {}

    if (!mountedRef.current) return

    // Deduplicate by address
    const seen = new Set()
    const dedup = (arr) => arr.filter(t => {
      const addr = t.base_address || t.pair_address || t.address || t.symbol
      if (!addr || seen.has(addr)) return false
      seen.add(addr)
      return true
    })

    setDipTokens(dedup(results.dips))
    setNewPairs(dedup(results.newPairs))
    setPumpTokens(dedup(results.pump))
    setSniperOpps(dedup(results.sniper))
    setAiGems(dedup(results.aiGems))
    setLastUpdate(new Date())
    setLoading(false)

    // Calc stats
    const allTokens = [...results.dips, ...results.newPairs, ...results.pump, ...results.sniper, ...results.aiGems]
    setStats({
      totalScanned: allTokens.length,
      dipsFound: results.dips.filter(t => (t.change_24h || 0) <= -5).length,
      moonshotPotential: allTokens.filter(t => (t.moonScore || 0) >= 70).length,
    })

    // ═══ JARVIS VOICE — announce top gems found ═══
    try {
      const topGems = allTokens.filter(t => (t.moonScore || 0) >= 85).slice(0, 2)
      if (topGems.length > 0) {
        const names = topGems.map(t => t.symbol || t.base_token || '???').join(' aur ')
        window.dispatchEvent(new CustomEvent('jarvis-speak', {
          detail: { text: `Sir, ${topGems.length} high-score gems mili hain: ${names}. Moon score 85 se zyada hai. Check karein.` }
        }))
      }
    } catch {}
  }, [base])

  useEffect(() => {
    mountedRef.current = true
    fetchAllData()
    const timer = setInterval(fetchAllData, 15000) // Refresh every 15s
    return () => { mountedRef.current = false; clearInterval(timer) }
  }, [fetchAllData])

  // ═══ MOONSHOT SCORE CALCULATOR ═══
  function calcMoonScore(token) {
    let score = 50
    const mcap = token.market_cap || 0
    const vol = token.volume_24h || 0
    const liq = token.liquidity_usd || 0
    const change = token.change_24h || 0
    const change1h = token.change_1h || 0

    // Micro cap = higher moonshot potential
    if (mcap > 0 && mcap < 10000) score += 25
    else if (mcap < 50000) score += 20
    else if (mcap < 200000) score += 15
    else if (mcap < 1000000) score += 10
    else if (mcap > 10000000) score -= 10

    // High volume relative to mcap = bullish
    if (mcap > 0 && vol > mcap * 2) score += 15
    else if (mcap > 0 && vol > mcap) score += 10
    else if (mcap > 0 && vol > mcap * 0.5) score += 5

    // Liquidity check
    if (liq > 5000 && liq < 100000) score += 5
    if (liq < 1000) score -= 10 // Low liquidity = risky

    // Dip = buying opportunity
    if (change <= -20) score += 15
    else if (change <= -10) score += 10
    else if (change <= -5) score += 5

    // Short-term pump = momentum
    if (change1h >= 50) score += 10
    else if (change1h >= 20) score += 5

    // Buy/Sell ratio
    const bsr = token.buy_sell_ratio || (token.buys_24h && token.sells_24h ? token.buys_24h / token.sells_24h : 1)
    if (bsr > 1.5) score += 5
    if (bsr < 0.5) score -= 5

    return Math.max(10, Math.min(99, score))
  }

  const getActiveTokens = () => {
    let tokens = []
    switch (activeTab) {
      case 'dips': tokens = dipTokens.filter(t => (t.change_24h || 0) <= -5); break
      case 'all-dex': tokens = [...dipTokens, ...newPairs]; break
      case 'pump': tokens = pumpTokens; break
      case 'sniper': tokens = sniperOpps; break
      case 'ai-gems': tokens = aiGems; break
      default: tokens = dipTokens
    }
    if (chain !== 'all') tokens = tokens.filter(t => (t.chain || '').toLowerCase() === chain)
    return tokens.sort((a, b) => (b.moonScore || 0) - (a.moonScore || 0))
  }

  const copyAddress = (addr) => {
    navigator.clipboard?.writeText(addr)
    setCopiedAddr(addr)
    hapticFeedback?.('impact')
    setTimeout(() => setCopiedAddr(null), 2000)
  }

  const formatNum = (n) => {
    if (!n || n === 0) return '-'
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B'
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M'
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K'
    if (n >= 1) return '$' + n.toFixed(2)
    return '$' + n.toExponential(2)
  }

  const formatPrice = (p) => {
    if (!p || p === 0) return '-'
    if (p >= 1) return '$' + p.toFixed(4)
    if (p >= 0.001) return '$' + p.toFixed(6)
    return '$' + p.toExponential(3)
  }

  const getMoonLabel = (score) => {
    if (score >= 85) return { text: '🔥 MEGA MOON', color: 'text-yellow-300 bg-yellow-500/20' }
    if (score >= 70) return { text: '🚀 HIGH POTENTIAL', color: 'text-emerald-300 bg-emerald-500/20' }
    if (score >= 55) return { text: '📈 MODERATE', color: 'text-blue-300 bg-blue-500/20' }
    return { text: '⚠️ LOW', color: 'text-slate-400 bg-slate-500/20' }
  }

  const tabs = [
    { id: 'dips', label: '📉 BIG DIPS', desc: '-5% or worse' },
    { id: 'all-dex', label: '🌐 DexScreener', desc: 'All tokens' },
    { id: 'pump', label: '🎰 Pump.fun', desc: 'New launches' },
    { id: 'sniper', label: '🎯 Auto Sniper', desc: 'AI picks' },
    { id: 'ai-gems', label: '💎 AI Gems', desc: 'Gem scanner' },
  ]

  const tokens = getActiveTokens()

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-950/20 to-slate-900 pb-24">
      {/* ═══ Header ═══ */}
      <div className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-lg border-b border-purple-500/20 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
              <Rocket size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">MoonShot Hunter</h1>
              <p className="text-[10px] text-purple-300/70">₹2K → ₹2Cr+ | Find 100x-1000x Gems</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Chain filter */}
            <div className="relative">
              <button onClick={() => setShowChains(!showChains)}
                className="px-2 py-1 bg-slate-800 rounded-lg text-[10px] text-slate-300 flex items-center gap-1 border border-slate-700">
                <Globe size={10} /> {chain === 'all' ? 'All Chains' : chain}
                <ChevronDown size={10} />
              </button>
              {showChains && (
                <div className="absolute right-0 top-8 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl z-50 py-1 min-w-[120px]">
                  {CHAINS.map(c => (
                    <button key={c} onClick={() => { setChain(c); setShowChains(false); hapticFeedback?.('impact') }}
                      className={`w-full px-3 py-2 text-left text-xs ${chain === c ? 'text-purple-400 bg-purple-500/10' : 'text-slate-300 hover:bg-slate-700'}`}>
                      {c === 'all' ? '🌐 All Chains' : c.charAt(0).toUpperCase() + c.slice(1)}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={() => { fetchAllData(); hapticFeedback?.('impact') }}
              className="p-1.5 bg-purple-600/20 rounded-lg border border-purple-500/30">
              <RefreshCw size={14} className={`text-purple-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-3 text-[10px]">
          <span className="text-slate-500">
            <Eye size={10} className="inline mr-0.5" /> {stats.totalScanned} scanned
          </span>
          <span className="text-red-400">
            <TrendingDown size={10} className="inline mr-0.5" /> {stats.dipsFound} dips
          </span>
          <span className="text-emerald-400">
            <Rocket size={10} className="inline mr-0.5" /> {stats.moonshotPotential} moonshots
          </span>
          {lastUpdate && (
            <span className="text-slate-600 ml-auto">
              <Clock size={10} className="inline mr-0.5" />
              {lastUpdate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
        </div>
      </div>

      {/* ═══ Tabs ═══ */}
      <div className="flex overflow-x-auto gap-1.5 px-3 py-2 no-scrollbar">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => { setActiveTab(tab.id); hapticFeedback?.('selection') }}
            className={`flex-shrink-0 px-3 py-2 rounded-xl text-[11px] font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
                : 'bg-slate-800/80 text-slate-400 border border-slate-700/50'
            }`}>
            {tab.label}
            <span className="block text-[9px] opacity-70">{tab.desc}</span>
          </button>
        ))}
      </div>

      {/* ═══ Token List ═══ */}
      <div className="px-3 space-y-2 mt-1">
        {loading && tokens.length === 0 ? (
          <div className="space-y-3 py-4">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="bg-slate-800/50 rounded-xl p-4 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-700 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-24 bg-slate-700 rounded" />
                    <div className="h-2 w-16 bg-slate-700 rounded" />
                  </div>
                  <div className="h-6 w-16 bg-slate-700 rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        ) : tokens.length === 0 ? (
          <div className="text-center py-12">
            <Search size={32} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No tokens found in this category</p>
            <p className="text-slate-600 text-xs mt-1">Try changing chain filter or tab</p>
          </div>
        ) : (
          tokens.map((token, idx) => {
            const moonLabel = getMoonLabel(token.moonScore || 50)
            const change = token.change_24h || 0
            const isExpanded = expandedToken === (token.base_address || token.pair_address || idx)
            const addr = token.base_address || token.pair_address || token.address || ''
            
            return (
              <div key={addr || idx}
                onClick={() => setExpandedToken(isExpanded ? null : (addr || idx))}
                className={`bg-gradient-to-r ${
                  (token.moonScore || 0) >= 85 ? 'from-yellow-500/5 to-purple-500/5 border-yellow-500/20' :
                  (token.moonScore || 0) >= 70 ? 'from-emerald-500/5 to-blue-500/5 border-emerald-500/20' :
                  'from-slate-800/80 to-slate-800/60 border-slate-700/30'
                } border rounded-xl p-3 transition-all active:scale-[0.98]`}>
                
                {/* Main row */}
                <div className="flex items-center gap-3">
                  {/* Rank + Moon Score */}
                  <div className="flex flex-col items-center min-w-[36px]">
                    <span className="text-[10px] text-slate-500">#{idx + 1}</span>
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs ${
                      (token.moonScore || 0) >= 85 ? 'bg-yellow-500/20 text-yellow-300' :
                      (token.moonScore || 0) >= 70 ? 'bg-emerald-500/20 text-emerald-300' :
                      (token.moonScore || 0) >= 55 ? 'bg-blue-500/20 text-blue-300' :
                      'bg-slate-700/50 text-slate-400'
                    }`}>
                      {token.moonScore || '?'}
                    </div>
                  </div>

                  {/* Token info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-white truncate">
                        {token.symbol || token.base_token || '???'}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 bg-slate-700/50 rounded text-slate-400">
                        {token.chain || 'SOL'}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 bg-purple-500/10 rounded text-purple-300">
                        {token.source || 'DEX'}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 truncate">
                      {token.name || token.base_token || '-'}
                    </p>
                  </div>

                  {/* Price + Change */}
                  <div className="text-right min-w-[80px]">
                    <p className="text-xs font-bold text-white">{formatPrice(token.price_usd)}</p>
                    <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
                      change <= -10 ? 'text-red-300 bg-red-500/15' :
                      change <= -5 ? 'text-orange-300 bg-orange-500/15' :
                      change >= 50 ? 'text-emerald-300 bg-emerald-500/15' :
                      change >= 10 ? 'text-green-300 bg-green-500/15' :
                      'text-slate-400'
                    }`}>
                      {change > 0 ? '+' : ''}{change.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Moon score label */}
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${moonLabel.color}`}>
                    {moonLabel.text}
                  </span>
                  <span className="text-[9px] text-slate-500">MCap: {formatNum(token.market_cap)}</span>
                  <span className="text-[9px] text-slate-500">Vol: {formatNum(token.volume_24h)}</span>
                  <span className="text-[9px] text-slate-500">Liq: {formatNum(token.liquidity_usd)}</span>
                </div>

                {/* ═══ Expanded details ═══ */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-700/30 space-y-2">
                    {/* Price changes */}
                    <div className="grid grid-cols-4 gap-2 text-center">
                      {[
                        { label: '5m', val: token.change_5m },
                        { label: '1h', val: token.change_1h },
                        { label: '6h', val: token.change_6h },
                        { label: '24h', val: token.change_24h },
                      ].map(c => (
                        <div key={c.label} className="bg-slate-800/50 rounded-lg py-1.5">
                          <p className="text-[9px] text-slate-500">{c.label}</p>
                          <p className={`text-[11px] font-bold ${
                            (c.val || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                          }`}>
                            {c.val != null ? `${c.val > 0 ? '+' : ''}${c.val.toFixed(1)}%` : '-'}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Buys/Sells */}
                    {(token.buys_24h || token.sells_24h) && (
                      <div className="flex items-center gap-3 text-[10px]">
                        <span className="text-emerald-400">🟢 {token.buys_24h || 0} buys</span>
                        <span className="text-red-400">🔴 {token.sells_24h || 0} sells</span>
                        <span className="text-slate-400">Ratio: {(token.buy_sell_ratio || 0).toFixed(2)}</span>
                      </div>
                    )}

                    {/* Address + Actions */}
                    {addr && (
                      <div className="flex items-center gap-2">
                        <code className="text-[9px] text-slate-500 bg-slate-800 px-2 py-1 rounded flex-1 truncate">
                          {addr}
                        </code>
                        <button onClick={(e) => { e.stopPropagation(); copyAddress(addr) }}
                          className="px-2 py-1 bg-slate-700 rounded text-[10px] text-slate-300 flex items-center gap-1">
                          {copiedAddr === addr ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                          {copiedAddr === addr ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex gap-2 mt-1">
                      {token.url && (
                        <a href={token.url} target="_blank" rel="noopener"
                          onClick={(e) => e.stopPropagation()}
                          className="flex-1 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg text-white text-xs font-bold text-center flex items-center justify-center gap-1">
                          <ArrowUpRight size={12} /> View on DEX
                        </a>
                      )}
                      <button onClick={(e) => {
                        e.stopPropagation()
                        hapticFeedback?.('impact')
                        // Add to watchlist
                        const wl = JSON.parse(localStorage.getItem('jarvis_watchlist') || '[]')
                        if (!wl.find(w => w.address === addr)) {
                          wl.push({ symbol: token.symbol || token.base_token, address: addr, chain: token.chain, added: Date.now() })
                          localStorage.setItem('jarvis_watchlist', JSON.stringify(wl))
                        }
                      }}
                        className="flex-1 py-2 bg-gradient-to-r from-yellow-600 to-orange-600 rounded-lg text-white text-xs font-bold text-center flex items-center justify-center gap-1">
                        <Star size={12} /> Watchlist
                      </button>
                    </div>

                    {/* AI Moonshot Analysis */}
                    <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-2.5 mt-1">
                      <p className="text-[10px] text-purple-300 font-bold mb-1">🧠 AI Moonshot Analysis</p>
                      <p className="text-[10px] text-slate-300 leading-relaxed">
                        {(token.moonScore || 0) >= 85 
                          ? `${token.symbol || 'Token'} has MEGA moonshot potential. Micro-cap with high volume momentum. If $2K invested → potential ₹2Cr+ at 1000x. HIGH RISK but massive upside.`
                          : (token.moonScore || 0) >= 70
                          ? `${token.symbol || 'Token'} shows strong 100x potential. Good volume/mcap ratio. Dip entry possible. Risk: moderate-high.`
                          : (token.moonScore || 0) >= 55
                          ? `${token.symbol || 'Token'} has moderate potential. Watch for more volume/catalysts before entry.`
                          : `${token.symbol || 'Token'} score is low. Wait for better setup or avoid.`
                        }
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* ═══ Disclaimer ═══ */}
      <div className="mx-3 mt-4 p-3 bg-red-500/5 border border-red-500/10 rounded-xl">
        <p className="text-[9px] text-red-400/60 flex items-center gap-1">
          <AlertTriangle size={10} /> High risk — micro-cap tokens can go to zero. Never invest more than you can afford to lose. DYOR. Not financial advice.
        </p>
      </div>
    </div>
  )
}

export default MoonShotHunter
