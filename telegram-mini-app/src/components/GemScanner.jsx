import React, { useState, useEffect, useCallback } from 'react'
import {
  Gem, Search, Shield, AlertTriangle, TrendingUp, ExternalLink,
  RefreshCw, Flame, Star, ChevronDown, CheckCircle, XCircle,
  ArrowUpRight, ArrowDownRight, BarChart3, Droplets, Zap
} from 'lucide-react'
import { fetchGems, fetchRugCheck } from '../services/api'
import { useApp } from '../context/AppContext'

const GemScanner = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [gems, setGems] = useState([])
  const [loading, setLoading] = useState(true)
  const [rugCheckAddress, setRugCheckAddress] = useState('')
  const [rugResult, setRugResult] = useState(null)
  const [checking, setChecking] = useState(false)
  const [filter, setFilter] = useState('all')
  const [stats, setStats] = useState({ total: 0, trending: 0, new: 0, dips: 0 })
  const [lastUpdate, setLastUpdate] = useState(null)

  const loadGems = useCallback(async (activeFilter) => {
    const f = activeFilter || filter
    setLoading(true)
    try {
      const res = await fetchGems(f)
      const d = res.data || {}
      const gemList = d.gems || d.data || []
      setGems(Array.isArray(gemList) ? gemList : [])
      if (d.stats) setStats(d.stats)
      setLastUpdate(new Date().toLocaleTimeString('en-IN'))
    } catch (e) {
      console.error('Gems load error:', e)
      addNotification?.('Failed to load gems', 'error')
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { loadGems('all') }, [])

  const handleFilterChange = (f) => {
    setFilter(f)
    hapticFeedback?.('impact')
    loadGems(f)
  }

  const handleRugCheck = async () => {
    if (!rugCheckAddress) { addNotification('Enter token address', 'error'); return }
    setChecking(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchRugCheck(rugCheckAddress)
      setRugResult(res.data?.data || res.data || {})
      hapticFeedback?.('success')
    } catch (e) {
      addNotification('Rug check failed', 'error')
      hapticFeedback?.('error')
    } finally {
      setChecking(false)
    }
  }

  const formatPrice = (p) => {
    const n = Number(p)
    if (!n) return '$0'
    if (n < 0.0001) return '$' + n.toExponential(2)
    if (n < 0.01) return '$' + n.toFixed(6)
    if (n < 1) return '$' + n.toFixed(4)
    if (n < 1000) return '$' + n.toFixed(2)
    return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }

  const formatNum = (n) => {
    const v = Number(n)
    if (!v) return '--'
    if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B'
    if (v >= 1e6) return '$' + (v / 1e6).toFixed(2) + 'M'
    if (v >= 1e3) return '$' + (v / 1e3).toFixed(1) + 'K'
    return '$' + v.toFixed(0)
  }

  const getChange = (g) => Number(g.change_24h || g.change || g.priceChange24h || 0)
  const getPrice = (g) => Number(g.price_usd || g.price || g.priceUsd || 0)
  const getVolume = (g) => Number(g.volume_24h || g.volume || 0)
  const getLiquidity = (g) => Number(g.liquidity_usd || g.liquidity || 0)
  const getMcap = (g) => Number(g.market_cap || g.mcap || g.marketCap || 0)
  const getScore = (g) => Number(g.gem_score || g.score || 0)

  const getScoreColor = (s) => s >= 80 ? 'text-emerald-400' : s >= 60 ? 'text-yellow-400' : s >= 40 ? 'text-orange-400' : 'text-red-400'
  const getScoreBg = (s) => s >= 80 ? 'bg-emerald-500/20 border-emerald-500/30' : s >= 60 ? 'bg-yellow-500/20 border-yellow-500/30' : s >= 40 ? 'bg-orange-500/20 border-orange-500/30' : 'bg-red-500/20 border-red-500/30'

  const getRiskColor = (risk) => {
    const r = (risk || '').toLowerCase()
    if (r.includes('low') || r.includes('safe')) return 'text-emerald-400'
    if (r.includes('medium') || r.includes('moderate')) return 'text-yellow-400'
    return 'text-red-400'
  }
  const getRiskBg = (risk) => {
    const r = (risk || '').toLowerCase()
    if (r.includes('low') || r.includes('safe')) return 'bg-emerald-500/20'
    if (r.includes('medium') || r.includes('moderate')) return 'bg-yellow-500/20'
    return 'bg-red-500/20'
  }

  const filters = [
    { id: 'all', label: 'All Gems', count: stats.total },
    { id: 'trending', label: '\uD83D\uDD25 Trending', count: stats.trending },
    { id: 'new', label: '\u2728 New', count: stats.new },
    { id: 'dips', label: '\uD83D\uDCC9 Buy Dips', count: stats.dips },
  ]

  if (loading && gems.length === 0) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="flex items-center space-x-2 mb-4">
          <Gem size={22} className="text-pink-400 animate-pulse" />
          <span className="text-lg font-bold text-white">Scanning Gems...</span>
        </div>
        {[1,2,3,4,5].map(i => (
          <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-slate-700 rounded-full" />
              <div className="flex-1"><div className="h-4 bg-slate-700 rounded w-24 mb-1" /><div className="h-3 bg-slate-700 rounded w-16" /></div>
              <div><div className="h-4 bg-slate-700 rounded w-16 mb-1" /><div className="h-3 bg-slate-700 rounded w-12 ml-auto" /></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <Gem size={22} className="text-pink-400" />
            <span>Gem Scanner</span>
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">LIVE</span>
          </h1>
          <p className="text-slate-400 text-xs mt-0.5">
            DexScreener + PumpFun {lastUpdate && <span>• {lastUpdate}</span>}
          </p>
        </div>
        <button onClick={() => loadGems(filter)} disabled={loading}
          className="p-2.5 bg-slate-800 rounded-full border border-slate-700 active:scale-95 transition-transform">
          <RefreshCw size={16} className={'text-blue-400 ' + (loading ? 'animate-spin' : '')} />
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {filters.map(f => (
          <div key={f.id} className="bg-slate-800/50 rounded-lg p-2 text-center">
            <p className="text-[10px] text-slate-400">{f.label.split(' ')[0]}</p>
            <p className="text-sm font-bold">{f.count || 0}</p>
          </div>
        ))}
      </div>

      {/* Rug Check */}
      <div className="bg-slate-800 rounded-xl p-3 border border-slate-700 mb-4">
        <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
          <Shield size={14} className="text-amber-400" />
          <span>Rug Pull Detector</span>
        </h3>
        <div className="flex space-x-2">
          <input type="text" value={rugCheckAddress} onChange={e => setRugCheckAddress(e.target.value)}
            placeholder="Token address or name..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
          <button onClick={handleRugCheck} disabled={checking}
            className="bg-amber-600 hover:bg-amber-500 text-white px-4 rounded-lg text-sm font-medium disabled:opacity-50 active:scale-95 transition-transform">
            {checking ? '...' : 'Check'}
          </button>
        </div>
        {rugResult && (
          <div className="mt-3 bg-slate-700/50 rounded-lg p-3 animate-fade-up">
            <div className="flex items-center justify-between mb-2">
              <p className="font-medium text-sm">{rugResult.name || rugResult.symbol || rugCheckAddress}</p>
              <span className={'text-xs font-medium px-2 py-0.5 rounded-full ' + getRiskBg(rugResult.risk) + ' ' + getRiskColor(rugResult.risk)}>
                {rugResult.risk || rugResult.risk_level || 'Unknown'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-slate-400">Score: </span><span className="font-medium">{rugResult.score || '--'}/100</span></div>
              <div><span className="text-slate-400">Liquidity: </span><span className="font-medium">${(rugResult.liquidity || 0).toLocaleString()}</span></div>
              {rugResult.holders && <div><span className="text-slate-400">Holders: </span><span>{rugResult.holders}</span></div>}
              {rugResult.top_holder_percent && <div><span className="text-slate-400">Top Holder: </span><span>{rugResult.top_holder_percent}%</span></div>}
            </div>
            {(rugResult.warnings || rugResult.flags) && (
              <div className="mt-2 space-y-1">
                {(rugResult.warnings || rugResult.flags || []).map((w, i) => (
                  <p key={i} className="text-xs text-amber-400 flex items-center space-x-1">
                    <AlertTriangle size={10} /><span>{typeof w === 'string' ? w : w.message || w.flag}</span>
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Filter Bar */}
      <div className="flex space-x-2 mb-4 overflow-x-auto scrollbar-hide">
        {filters.map(f => (
          <button key={f.id} onClick={() => handleFilterChange(f.id)}
            className={'px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap flex items-center space-x-1 active:scale-95 transition-all ' + (
              filter === f.id
                ? 'bg-pink-600 text-white shadow-lg shadow-pink-500/20'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            )}>
            <span>{f.label}</span>
            {f.count > 0 && <span className="text-[10px] opacity-70">({f.count})</span>}
          </button>
        ))}
      </div>

      {/* Loading overlay for filter switch */}
      {loading && gems.length > 0 && (
        <div className="flex items-center justify-center py-2 mb-2">
          <RefreshCw size={14} className="animate-spin text-pink-400 mr-2" />
          <span className="text-xs text-slate-400">Refreshing...</span>
        </div>
      )}

      {/* Gems List */}
      <div className="space-y-2">
        {gems.length === 0 ? (
          <div className="text-center py-12">
            <Gem size={48} className="mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400 text-sm">No gems found for this filter</p>
            <button onClick={() => handleFilterChange('all')} className="mt-3 text-xs text-pink-400 underline">
              Show All Gems
            </button>
          </div>
        ) : (
          gems.map((g, i) => {
            const price = getPrice(g)
            const change = getChange(g)
            const vol = getVolume(g)
            const liq = getLiquidity(g)
            const mcap = getMcap(g)
            const score = getScore(g)

            return (
              <div key={(g.symbol || g.name || '') + '-' + i}
                className="bg-slate-800 rounded-xl p-3 border border-slate-700 animate-fade-up active:scale-[0.99] transition-transform"
                style={{ animationDelay: i * 20 + 'ms' }}>

                {/* Top Row: Token + Price */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className={'w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold border ' + (
                      change >= 0
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-red-500/10 border-red-500/30 text-red-400'
                    )}>
                      {(g.symbol || g.name || '??').substring(0, 3).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center space-x-1.5">
                        <p className="font-bold text-sm">{g.symbol || g.name}</p>
                        {(g._tag === 'trending' || g._tag === 'pumpfun' || g._tag === 'cg_trending') ? (
                          <span className="text-[9px] bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded-full">{'\uD83D\uDD25'} HOT</span>
                        ) : (g._tag === 'new' || g._tag === 'pumpfun_new') ? (
                          <span className="text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded-full">{'\u2728'} NEW</span>
                        ) : g._tag === 'dip' ? (
                          <span className="text-[9px] bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded-full">{'\uD83D\uDCC9'} DIP</span>
                        ) : null}
                      </div>
                      <p className="text-[10px] text-slate-400">
                        {g.chain || g.network || ''}{g.dex ? ' \u2022 ' + g.dex : ''}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{formatPrice(price)}</p>
                    <div className={'flex items-center justify-end space-x-0.5 text-xs font-medium ' + (change >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                      {change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                      <span>{change >= 0 ? '+' : ''}{change.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>

                {/* Gem Score + Buy/Sell */}
                {score > 0 && (
                  <div className="flex items-center space-x-2 mb-2">
                    <div className={'px-2 py-0.5 rounded-full text-[10px] font-bold border ' + getScoreBg(score) + ' ' + getScoreColor(score)}>
                      {'\u2B50'} GEM {score}/100
                    </div>
                    {g.buy_sell_ratio && (
                      <span className={'text-[10px] px-1.5 py-0.5 rounded-full ' + (
                        Number(g.buy_sell_ratio) >= 1.5 ? 'bg-emerald-500/15 text-emerald-400' :
                        Number(g.buy_sell_ratio) >= 1 ? 'bg-emerald-500/10 text-emerald-300' :
                        'bg-red-500/10 text-red-400'
                      )}>
                        {Number(g.buy_sell_ratio) >= 1 ? '\uD83D\uDFE2' : '\uD83D\uDD34'} B/S: {Number(g.buy_sell_ratio).toFixed(2)}
                      </span>
                    )}
                    {g.dip_score > 0 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/15 text-purple-400">
                        Dip: {g.dip_score}
                      </span>
                    )}
                  </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-1.5 text-[10px]">
                  {vol > 0 && (
                    <div className="bg-slate-700/50 rounded-lg p-1.5 text-center">
                      <p className="text-slate-500 flex items-center justify-center space-x-0.5">
                        <BarChart3 size={9} /><span>Volume</span>
                      </p>
                      <p className="font-bold text-xs">{formatNum(vol)}</p>
                    </div>
                  )}
                  {liq > 0 && (
                    <div className="bg-slate-700/50 rounded-lg p-1.5 text-center">
                      <p className="text-slate-500 flex items-center justify-center space-x-0.5">
                        <Droplets size={9} /><span>Liquidity</span>
                      </p>
                      <p className="font-bold text-xs">{formatNum(liq)}</p>
                    </div>
                  )}
                  {mcap > 0 && (
                    <div className="bg-slate-700/50 rounded-lg p-1.5 text-center">
                      <p className="text-slate-500 flex items-center justify-center space-x-0.5">
                        <Zap size={9} /><span>MCap</span>
                      </p>
                      <p className="font-bold text-xs">{formatNum(mcap)}</p>
                    </div>
                  )}
                </div>

                {/* Multi-timeframe changes */}
                {(g.change_5m || g.change_1h || g.change_6h) && (
                  <div className="flex space-x-2 mt-2">
                    {g.change_5m != null && (
                      <span className={'text-[9px] px-1.5 py-0.5 rounded ' + (Number(g.change_5m) >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400')}>
                        5m: {Number(g.change_5m) >= 0 ? '+' : ''}{Number(g.change_5m).toFixed(1)}%
                      </span>
                    )}
                    {g.change_1h != null && (
                      <span className={'text-[9px] px-1.5 py-0.5 rounded ' + (Number(g.change_1h) >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400')}>
                        1h: {Number(g.change_1h) >= 0 ? '+' : ''}{Number(g.change_1h).toFixed(1)}%
                      </span>
                    )}
                    {g.change_6h != null && (
                      <span className={'text-[9px] px-1.5 py-0.5 rounded ' + (Number(g.change_6h) >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400')}>
                        6h: {Number(g.change_6h) >= 0 ? '+' : ''}{Number(g.change_6h).toFixed(1)}%
                      </span>
                    )}
                  </div>
                )}

                {/* Buys/Sells */}
                {(g.buys_24h || g.sells_24h) && (
                  <div className="flex items-center space-x-3 mt-2 text-[10px]">
                    <span className="text-emerald-400">{'\uD83D\uDFE2'} {g.buys_24h || 0} buys</span>
                    <span className="text-red-400">{'\uD83D\uDD34'} {g.sells_24h || 0} sells</span>
                  </div>
                )}

                {g.reason && <p className="text-[10px] text-slate-400 mt-1.5">{g.reason}</p>}

                {g.url && (
                  <a href={g.url} target="_blank" rel="noopener noreferrer"
                    className="text-[10px] text-blue-400 flex items-center space-x-1 mt-1.5 hover:underline">
                    <ExternalLink size={9} /><span>View Chart</span>
                  </a>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer count */}
      {gems.length > 0 && (
        <p className="text-center text-[10px] text-slate-500 mt-4">
          Showing {gems.length} gems {'\u2022'} {filter === 'all' ? 'All Sources' : filter.toUpperCase()}
        </p>
      )}
    </div>
  )
}

export default GemScanner
