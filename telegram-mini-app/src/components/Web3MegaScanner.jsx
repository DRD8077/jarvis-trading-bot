import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Rocket, Flame, TrendingUp, TrendingDown, Search, RefreshCw, ExternalLink,
  Shield, AlertTriangle, Zap, Star, Globe, BarChart3, ArrowUpRight, ArrowDownRight,
  ChevronRight, Eye, Filter, Clock, Gem, Target, CircleDollarSign
} from 'lucide-react'
import {
  fetchDexTrending, fetchDexNewPairs, fetchPumpfunTrending, fetchPumpfunNew,
  fetchWeb3Rockets, fetchWeb3Launches, fetchDextoolsHot, fetchDextoolsSearch,
  fetchBirdeyeTrending, fetchCoindcxMegaScan, fetchGems, fetchRugCheck
} from '../services/api'
import { useApp } from '../context/AppContext'

const TABS = [
  { id: 'dex', label: 'DexScreener', icon: Globe, color: 'text-green-400' },
  { id: 'pump', label: 'Pump.fun', icon: Rocket, color: 'text-pink-400' },
  { id: 'dextools', label: 'DexTools', icon: Flame, color: 'text-orange-400' },
  { id: 'birdeye', label: 'Birdeye', icon: Eye, color: 'text-cyan-400' },
  { id: 'rockets', label: 'Rockets', icon: Zap, color: 'text-yellow-400' },
  { id: 'gems', label: 'AI Gems', icon: Gem, color: 'text-purple-400' },
  { id: 'coindcx', label: 'CoinDCX', icon: CircleDollarSign, color: 'text-blue-400' },
]

const CHAIN_OPTIONS = ['all', 'ethereum', 'solana', 'bsc', 'base', 'arbitrum', 'polygon', 'avalanche']

const formatPrice = (p) => {
  if (!p || p === 0) return '$0'
  if (p < 0.00001) return `$${p.toExponential(2)}`
  if (p < 0.01) return `$${p.toFixed(6)}`
  if (p < 1) return `$${p.toFixed(4)}`
  if (p < 1000) return `$${p.toFixed(2)}`
  return `$${(p/1000).toFixed(1)}K`
}

const formatVol = (v) => {
  if (!v) return '-'
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${(v/1e3).toFixed(1)}K`
  return `$${v.toFixed(0)}`
}

const formatMcap = (m) => {
  if (!m) return '-'
  if (m >= 1e12) return `$${(m/1e12).toFixed(1)}T`
  if (m >= 1e9) return `$${(m/1e9).toFixed(1)}B`
  if (m >= 1e6) return `$${(m/1e6).toFixed(1)}M`
  if (m >= 1e3) return `$${(m/1e3).toFixed(1)}K`
  return `$${m.toFixed(0)}`
}

const ChangeTag = ({ val }) => {
  const v = parseFloat(val || 0)
  const isPos = v >= 0
  return (
    <span className={`inline-flex items-center text-xs font-bold ${isPos ? 'text-green-400' : 'text-red-400'}`}>
      {isPos ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
      {Math.abs(v).toFixed(1)}%
    </span>
  )
}

const TokenCard = ({ token, onRugCheck }) => {
  const change = token.change24h || token.priceChange24h || token.change_24h || token.price_change_percentage_24h || 0
  const price = token.price || token.priceUsd || token.current_price || 0
  const vol = token.volume || token.volume24h || token.total_volume || 0
  const mcap = token.marketCap || token.market_cap || token.fdv || 0
  const liq = token.liquidity || token.liquidityUsd || 0
  const chain = token.chain || token.chainId || token.network || ''
  const addr = token.address || token.pairAddress || token.contract || ''

  return (
    <div className="bg-slate-800/70 border border-slate-700/40 rounded-xl p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          {token.image && <img src={token.image} alt="" className="w-6 h-6 rounded-full" onError={e => e.target.style.display='none'} />}
          <div className="min-w-0">
            <p className="text-sm font-bold text-white truncate">{token.symbol || token.name || '???'}</p>
            <p className="text-[10px] text-slate-500 truncate">{token.name || token.baseToken?.name || chain}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-white">{formatPrice(parseFloat(price))}</p>
          <ChangeTag val={change} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-[10px]">
        <div><span className="text-slate-500">Vol 24h</span><br /><span className="text-slate-300 font-semibold">{formatVol(parseFloat(vol))}</span></div>
        <div><span className="text-slate-500">MCap</span><br /><span className="text-slate-300 font-semibold">{formatMcap(parseFloat(mcap))}</span></div>
        <div><span className="text-slate-500">Liq</span><br /><span className="text-slate-300 font-semibold">{formatVol(parseFloat(liq))}</span></div>
      </div>

      {chain && <span className="inline-block text-[9px] bg-slate-700/60 text-slate-400 px-2 py-0.5 rounded-full">{chain}</span>}

      <div className="flex gap-2">
        {addr && (
          <>
            <button onClick={() => onRugCheck(addr)} className="flex-1 text-[10px] bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg py-1.5 font-semibold flex items-center justify-center gap-1">
              <Shield size={10} /> Rug Check
            </button>
            <a href={`https://dexscreener.com/search?q=${addr}`} target="_blank" rel="noopener noreferrer" className="flex-1 text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg py-1.5 font-semibold flex items-center justify-center gap-1">
              <ExternalLink size={10} /> Chart
            </a>
          </>
        )}
      </div>

      {/* Dip Alert */}
      {parseFloat(change) <= -5 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1 flex items-center gap-1">
          <Target size={11} className="text-red-400" />
          <span className="text-[10px] text-red-300 font-semibold">🔥 DIP ALERT: {Math.abs(parseFloat(change)).toFixed(1)}% DOWN — Gem opportunity?</span>
        </div>
      )}
    </div>
  )
}

const Web3MegaScanner = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [activeTab, setActiveTab] = useState('dex')
  const [tokens, setTokens] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [chain, setChain] = useState('all')
  const [rugResult, setRugResult] = useState(null)
  const [rugChecking, setRugChecking] = useState(false)
  const [rugAddr, setRugAddr] = useState('')
  const [stats, setStats] = useState({ total: 0, dips: 0, rockets: 0 })
  const refreshRef = useRef(null)

  const loadData = useCallback(async (tab) => {
    const t = tab || activeTab
    setLoading(true)
    try {
      let data = []

      switch (t) {
        case 'dex': {
          const [trending, newPairs] = await Promise.all([
            fetchDexTrending().catch(() => ({ data: {} })),
            fetchDexNewPairs().catch(() => ({ data: {} }))
          ])
          const trendList = trending.data?.pairs || trending.data?.data?.pairs || trending.data?.data || []
          const newList = newPairs.data?.pairs || newPairs.data?.data?.pairs || newPairs.data?.data || []
          data = [...(Array.isArray(trendList) ? trendList : []), ...(Array.isArray(newList) ? newList : [])]

          // If backend fails, fetch directly from DexScreener public API
          if (data.length === 0) {
            try {
              const res = await fetch('https://api.dexscreener.com/latest/dex/tokens/SOL,ETH,BNB')
              if (res.ok) {
                const json = await res.json()
                data = (json.pairs || []).slice(0, 50).map(p => ({
                  symbol: p.baseToken?.symbol || '?',
                  name: p.baseToken?.name || '',
                  price: p.priceUsd,
                  change24h: p.priceChange?.h24 || 0,
                  volume: p.volume?.h24 || 0,
                  liquidity: p.liquidity?.usd || 0,
                  marketCap: p.fdv || 0,
                  chain: p.chainId,
                  address: p.pairAddress,
                  image: p.info?.imageUrl || '',
                }))
              }
            } catch {}
          }
          break
        }

        case 'pump': {
          const [trending, newest] = await Promise.all([
            fetchPumpfunTrending().catch(() => ({ data: {} })),
            fetchPumpfunNew().catch(() => ({ data: {} }))
          ])
          const tList = trending.data?.tokens || trending.data?.data?.tokens || trending.data?.data || []
          const nList = newest.data?.tokens || newest.data?.data?.tokens || newest.data?.data || []
          data = [...(Array.isArray(tList) ? tList : []), ...(Array.isArray(nList) ? nList : [])]

          // Fallback: fetch from pump.fun API directly
          if (data.length === 0) {
            try {
              const res = await fetch('https://frontend-api.pump.fun/coins?offset=0&limit=50&sort=last_trade_timestamp&order=DESC&includeNsfw=false')
              if (res.ok) {
                const json = await res.json()
                data = (json || []).map(c => ({
                  symbol: c.symbol || '?',
                  name: c.name || '',
                  price: c.usd_market_cap ? c.usd_market_cap / (c.total_supply || 1e9) : 0,
                  marketCap: c.usd_market_cap || 0,
                  chain: 'solana',
                  address: c.mint || '',
                  image: c.image_uri || '',
                  change24h: 0,
                  volume: c.usd_market_cap || 0,
                }))
              }
            } catch {}
          }
          break
        }

        case 'dextools': {
          const res = await fetchDextoolsHot().catch(() => ({ data: {} }))
          data = res.data?.pairs || res.data?.data?.pairs || res.data?.data || []
          if (!Array.isArray(data)) data = []

          // Fallback: fetch DexScreener boosted tokens (alternative source)
          if (data.length === 0) {
            try {
              const r = await fetch('https://api.dexscreener.com/token-boosts/latest/v1')
              if (r.ok) {
                const json = await r.json()
                data = (json || []).slice(0, 50).map(t => ({
                  symbol: t.tokenAddress?.slice(0, 8) || '?',
                  name: t.description || '',
                  chain: t.chainId || '',
                  address: t.tokenAddress || '',
                  price: 0,
                  change24h: 0,
                  volume: t.amount || 0,
                }))
              }
            } catch {}
          }
          break
        }

        case 'birdeye': {
          const res = await fetchBirdeyeTrending().catch(() => ({ tokens: [] }))
          data = res.tokens || res.data?.tokens || res.data?.data?.tokens || []
          if (!Array.isArray(data)) data = []

          // Fallback: use DexScreener Solana trending
          if (data.length === 0) {
            try {
              const r = await fetch('https://api.dexscreener.com/latest/dex/tokens/SOL')
              if (r.ok) {
                const json = await r.json()
                data = (json.pairs || []).slice(0, 50).map(p => ({
                  symbol: p.baseToken?.symbol || '?',
                  name: p.baseToken?.name || '',
                  price: p.priceUsd,
                  change24h: p.priceChange?.h24 || 0,
                  volume: p.volume?.h24 || 0,
                  liquidity: p.liquidity?.usd || 0,
                  chain: 'solana',
                  address: p.pairAddress,
                  image: p.info?.imageUrl || '',
                }))
              }
            } catch {}
          }
          break
        }

        case 'rockets': {
          const [rockets, launches] = await Promise.all([
            fetchWeb3Rockets().catch(() => ({ data: {} })),
            fetchWeb3Launches().catch(() => ({ data: {} }))
          ])
          const rList = rockets.data?.rockets || rockets.data?.data?.rockets || rockets.data?.data || []
          const lList = launches.data?.launches || launches.data?.data?.launches || launches.data?.data || []
          data = [...(Array.isArray(rList) ? rList : []), ...(Array.isArray(lList) ? lList : [])]
          break
        }

        case 'gems': {
          const res = await fetchGems('dips').catch(() => ({ data: {} }))
          data = res.data?.gems || res.data?.data?.gems || res.data?.data || []
          if (!Array.isArray(data)) data = []

          // Also directly scan CoinGecko for big dippers 
          try {
            const r = await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h')
            if (r.ok) {
              const coins = await r.json()
              const dippers = coins.filter(c => (c.price_change_percentage_24h || 0) <= -5).map(c => ({
                symbol: c.symbol?.toUpperCase() || '?',
                name: c.name || '',
                price: c.current_price || 0,
                change24h: c.price_change_percentage_24h || 0,
                volume: c.total_volume || 0,
                marketCap: c.market_cap || 0,
                image: c.image || '',
                chain: 'multi',
                address: c.id || '',
              }))
              data = [...dippers, ...data]
            }
          } catch {}
          break
        }

        case 'coindcx': {
          const res = await fetchCoindcxMegaScan().catch(() => ({ data: {} }))
          data = res.data?.coins || res.data?.data?.coins || res.data?.data || []
          if (!Array.isArray(data)) data = []
          break
        }
      }

      // Calculate stats
      const dipCount = data.filter(t => parseFloat(t.change24h || t.priceChange24h || t.change_24h || 0) <= -5).length
      const rocketCount = data.filter(t => parseFloat(t.change24h || t.priceChange24h || t.change_24h || 0) >= 20).length
      setStats({ total: data.length, dips: dipCount, rockets: rocketCount })
      setTokens(data)
      setLastUpdate(new Date().toLocaleTimeString('en-IN'))
      // JARVIS voice — announce scan results
      try {
        if (rocketCount > 0 || dipCount > 0) {
          window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: `Sir, Web3 scan complete! ${data.length} tokens scanned. ${rocketCount} rockets mil rahe hain 20 percent plus, aur ${dipCount} dip pe hain. ${rocketCount > 3 ? 'Bahut opportunities hain Sir!' : 'Check kariye!'}`, priority: 'normal' } }))
        }
      } catch {}
    } catch (e) {
      console.error(`[Web3Scanner] ${t} error:`, e)
      addNotification?.(`Failed to load ${t} data`, 'error')
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => { loadData() }, [activeTab])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    refreshRef.current = setInterval(() => loadData(), 5000)
    return () => clearInterval(refreshRef.current)
  }, [loadData])

  const handleTabChange = (id) => {
    setActiveTab(id)
    hapticFeedback?.('impact')
    setSearchQuery('')
  }

  const doRugCheck = async (address) => {
    if (!address) return
    setRugAddr(address)
    setRugChecking(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchRugCheck(address)
      setRugResult(res.data?.data || res.data || {})
      hapticFeedback?.('success')
    } catch {
      addNotification?.('Rug check failed', 'error')
    } finally {
      setRugChecking(false)
    }
  }

  // Filter tokens
  const filtered = tokens.filter(t => {
    const sym = (t.symbol || t.name || '').toLowerCase()
    const matchSearch = !searchQuery || sym.includes(searchQuery.toLowerCase())
    const matchChain = chain === 'all' || (t.chain || t.chainId || '').toLowerCase().includes(chain)
    return matchSearch && matchChain
  })

  return (
    <div className="p-3 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Rocket size={20} className="text-purple-400" />
            Web3 Mega Scanner
          </h1>
          <p className="text-[10px] text-slate-500">
            {lastUpdate ? `Updated ${lastUpdate}` : 'Loading...'} • {stats.total} tokens • {stats.dips} dips • {stats.rockets} 🚀
          </p>
        </div>
        <button onClick={() => { hapticFeedback?.('impact'); loadData() }} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={16} className={`text-blue-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 overflow-x-auto scrollbar-hide mb-3 pb-1">
        {TABS.map(t => {
          const Icon = t.icon
          return (
            <button key={t.id} onClick={() => handleTabChange(t.id)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold whitespace-nowrap transition-all
                ${activeTab === t.id ? 'bg-slate-700 border border-slate-600 text-white' : 'bg-slate-800/50 text-slate-500'}`}>
              <Icon size={12} className={activeTab === t.id ? t.color : ''} />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Search + Chain Filter */}
      <div className="flex gap-2 mb-3">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search tokens..."
            className="w-full bg-slate-800/50 border border-slate-700/30 rounded-xl pl-8 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-purple-500/50" />
        </div>
        <select value={chain} onChange={e => setChain(e.target.value)}
          className="bg-slate-800/50 border border-slate-700/30 rounded-xl px-2 py-2 text-xs text-white outline-none">
          {CHAIN_OPTIONS.map(c => <option key={c} value={c}>{c === 'all' ? '🌐 All' : c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
        </select>
      </div>

      {/* Dip Alert Banner */}
      {stats.dips > 0 && (
        <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-xl p-2.5 mb-3 flex items-center gap-2">
          <Target size={16} className="text-red-400 shrink-0" />
          <div>
            <p className="text-xs font-bold text-red-300">🔥 {stats.dips} tokens at -5% or deeper!</p>
            <p className="text-[10px] text-slate-400">AI scanning for recovery potential...</p>
          </div>
        </div>
      )}

      {/* Rug Check Result */}
      {rugResult && (
        <div className={`border rounded-xl p-3 mb-3 ${rugResult.safe || rugResult.is_safe ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1.5">
              {(rugResult.safe || rugResult.is_safe) ? <Shield size={14} className="text-green-400" /> : <AlertTriangle size={14} className="text-red-400" />}
              <span className="text-xs font-bold">{(rugResult.safe || rugResult.is_safe) ? '✅ SAFE' : '⚠️ RISKY'}</span>
            </div>
            <button onClick={() => setRugResult(null)} className="text-slate-500 text-xs">✕</button>
          </div>
          <p className="text-[10px] text-slate-400 break-all">{rugAddr}</p>
          {rugResult.score && <p className="text-[10px] text-slate-300 mt-1">Safety Score: {rugResult.score}/100</p>}
          {rugResult.risks && rugResult.risks.length > 0 && (
            <div className="mt-1 space-y-0.5">
              {rugResult.risks.map((r, i) => <p key={i} className="text-[10px] text-red-300">⚠️ {r}</p>)}
            </div>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && tokens.length === 0 && (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="bg-slate-800/50 rounded-xl h-28 animate-pulse" />
          ))}
        </div>
      )}

      {/* Token List */}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12">
          <Rocket size={40} className="mx-auto text-slate-700 mb-3" />
          <p className="text-slate-500 text-sm">No tokens found</p>
          <p className="text-slate-600 text-xs mt-1">Try a different tab or clear filters</p>
        </div>
      )}

      <div className="space-y-2">
        {filtered.slice(0, 50).map((token, i) => (
          <TokenCard key={`${token.symbol || token.address || i}-${i}`} token={token} onRugCheck={doRugCheck} />
        ))}
      </div>

      {filtered.length > 50 && (
        <p className="text-center text-slate-500 text-xs mt-3">Showing 50 of {filtered.length} tokens</p>
      )}
    </div>
  )
}

export default Web3MegaScanner
