import React, { useState, useEffect } from 'react'
import {
  Gem, Search, Shield, AlertTriangle, TrendingUp, ExternalLink,
  RefreshCw, Flame, Star, ChevronDown, CheckCircle, XCircle
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
  const [filter, setFilter] = useState('all') // all, safe, trending, new

  const loadGems = async () => {
    setLoading(true)
    try {
      const res = await fetchGems()
      const data = res.data?.data || res.data?.gems || res.data || []
      setGems(Array.isArray(data) ? data : 
        [...(data.dexscreener || []), ...(data.trending || []), ...(data.coindcx_dips || [])])
    } catch (e) {
      console.error('Gems load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadGems() }, [])

  const handleRugCheck = async () => {
    if (!rugCheckAddress) { addNotification('Enter token address', 'error'); return }
    setChecking(true)
    hapticFeedback('impact')
    try {
      const res = await fetchRugCheck(rugCheckAddress)
      setRugResult(res.data?.data || res.data || {})
      hapticFeedback('success')
    } catch (e) {
      addNotification('Rug check failed', 'error')
      hapticFeedback('error')
    } finally {
      setChecking(false)
    }
  }

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

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-14 rounded-xl" />
        {[1,2,3,4].map(i => <div key={i} className="skeleton h-24 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <Gem size={22} className="text-pink-400" />
            <span>Gem Scanner</span>
          </h1>
          <p className="text-slate-400 text-sm">DexScreener + CoinDCX + Web3 tokens</p>
        </div>
        <button onClick={loadGems} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Rug Check */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5">
        <h3 className="font-bold text-sm mb-2 flex items-center space-x-2">
          <Shield size={16} className="text-amber-400" />
          <span>Rug Pull Detector</span>
        </h3>
        <div className="flex space-x-2">
          <input type="text" value={rugCheckAddress} onChange={e => setRugCheckAddress(e.target.value)}
            placeholder="Enter token address or name..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
          <button onClick={handleRugCheck} disabled={checking}
            className="bg-amber-600 hover:bg-amber-500 text-white px-4 rounded-lg text-sm font-medium disabled:opacity-50">
            {checking ? '...' : 'Check'}
          </button>
        </div>

        {/* Rug Check Result */}
        {rugResult && (
          <div className="mt-3 bg-slate-700/50 rounded-lg p-3 animate-fade-up">
            <div className="flex items-center justify-between mb-2">
              <p className="font-medium text-sm">{rugResult.name || rugResult.symbol || rugCheckAddress}</p>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getRiskBg(rugResult.risk)} ${getRiskColor(rugResult.risk)}`}>
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
        {[
          { id: 'all', label: 'All Gems' },
          { id: 'trending', label: '🔥 Trending' },
          { id: 'new', label: '✨ New' },
          { id: 'dips', label: '📉 Buy Dips' },
        ].map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${
              filter === f.id ? 'bg-pink-600 text-white' : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}>{f.label}</button>
        ))}
      </div>

      {/* Gems List */}
      <div className="space-y-2">
        {gems.length === 0 ? (
          <div className="text-center py-12">
            <Gem size={48} className="mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400">Scanning for gems...</p>
          </div>
        ) : (
          gems.map((g, i) => (
            <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700 animate-fade-up"
              style={{ animationDelay: `${i * 30}ms` }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full 
                    flex items-center justify-center text-xs font-bold border border-pink-500/20">
                    {(g.symbol || g.name || '??').substring(0, 3).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-bold text-sm">{g.symbol || g.name}</p>
                    <p className="text-xs text-slate-400">{g.chain || g.network || g.exchange || ''}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">${(g.price || g.priceUsd || 0).toLocaleString(undefined, { maximumFractionDigits: 6 })}</p>
                  <p className={`text-xs font-medium ${(g.change || g.priceChange24h || g.change_24h || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(g.change || g.priceChange24h || g.change_24h || 0) >= 0 ? '+' : ''}
                    {(g.change || g.priceChange24h || g.change_24h || 0).toFixed(2)}%
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs mb-2">
                {g.volume && (
                  <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                    <p className="text-slate-400">Volume</p>
                    <p className="font-medium">${(g.volume || 0).toLocaleString()}</p>
                  </div>
                )}
                {g.liquidity && (
                  <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                    <p className="text-slate-400">Liquidity</p>
                    <p className="font-medium">${(g.liquidity || 0).toLocaleString()}</p>
                  </div>
                )}
                {g.mcap && (
                  <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                    <p className="text-slate-400">MCap</p>
                    <p className="font-medium">${(g.mcap || g.marketCap || 0).toLocaleString()}</p>
                  </div>
                )}
              </div>

              {g.reason && <p className="text-xs text-slate-400 mb-2">{g.reason}</p>}
              
              {g.url && (
                <a href={g.url} target="_blank" rel="noopener noreferrer"
                  className="text-xs text-blue-400 flex items-center space-x-1 hover:underline">
                  <ExternalLink size={10} /><span>View on DexScreener</span>
                </a>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default GemScanner
