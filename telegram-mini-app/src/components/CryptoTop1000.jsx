import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  TrendingUp, TrendingDown, Search, RefreshCw, ArrowUpRight, ArrowDownRight,
  BarChart3, Flame, Star, Filter, ChevronRight, Target, Zap, Globe
} from 'lucide-react'
import { useApp } from '../context/AppContext'

const PAGES_TO_LOAD = 5 // 5 pages × 250 = top 1250 coins
const PER_PAGE = 250

const formatNum = (n) => {
  if (!n) return '-'
  if (n >= 1e12) return `$${(n/1e12).toFixed(2)}T`
  if (n >= 1e9) return `$${(n/1e9).toFixed(2)}B`
  if (n >= 1e6) return `$${(n/1e6).toFixed(2)}M`
  if (n >= 1e3) return `$${(n/1e3).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

const formatPrice = (p) => {
  if (!p) return '$0'
  if (p < 0.00001) return `$${p.toExponential(2)}`
  if (p < 0.01) return `$${p.toFixed(6)}`
  if (p < 1) return `$${p.toFixed(4)}`
  if (p < 10000) return `$${p.toFixed(2)}`
  return `$${p.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

const SORT_OPTIONS = [
  { id: 'market_cap_desc', label: 'Market Cap ↓' },
  { id: 'volume_desc', label: 'Volume ↓' },
  { id: 'price_change_desc', label: 'Gainers 🚀' },
  { id: 'price_change_asc', label: 'Losers 📉' },
]

const CryptoTop1000 = () => {
  const { hapticFeedback } = useApp()
  const [coins, setCoins] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('market_cap_desc')
  const [lastUpdate, setLastUpdate] = useState(null)
  const [showDipsOnly, setShowDipsOnly] = useState(false)
  const [globalData, setGlobalData] = useState(null)
  const refreshRef = useRef(null)

  const loadCoins = useCallback(async () => {
    setLoading(true)
    try {
      // Fetch top 1000+ coins from CoinGecko (free, no auth)
      const allCoins = []
      const pagePromises = []
      for (let page = 1; page <= PAGES_TO_LOAD; page++) {
        pagePromises.push(
          fetch(`https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=${PER_PAGE}&page=${page}&sparkline=false&price_change_percentage=1h%2C24h%2C7d`)
            .then(r => r.ok ? r.json() : [])
            .catch(() => [])
        )
      }
      const pages = await Promise.all(pagePromises)
      pages.forEach(p => { if (Array.isArray(p)) allCoins.push(...p) })

      setCoins(allCoins)
      setLastUpdate(new Date().toLocaleTimeString('en-IN'))

      // Also fetch global market data
      try {
        const gRes = await fetch('https://api.coingecko.com/api/v3/global')
        if (gRes.ok) {
          const gData = await gRes.json()
          setGlobalData(gData.data)
        }
      } catch {}
    } catch (e) {
      console.error('[Top1000] Load error:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadCoins() }, [])

  // Auto-refresh every 8 seconds
  useEffect(() => {
    refreshRef.current = setInterval(loadCoins, 8000)
    return () => clearInterval(refreshRef.current)
  }, [loadCoins])

  // Sort & filter
  const processed = React.useMemo(() => {
    let list = [...coins]

    // Search filter
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(c => c.symbol?.toLowerCase().includes(q) || c.name?.toLowerCase().includes(q))
    }

    // Dips filter
    if (showDipsOnly) {
      list = list.filter(c => (c.price_change_percentage_24h || 0) <= -5)
    }

    // Sort
    switch (sortBy) {
      case 'volume_desc': list.sort((a, b) => (b.total_volume || 0) - (a.total_volume || 0)); break
      case 'price_change_desc': list.sort((a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0)); break
      case 'price_change_asc': list.sort((a, b) => (a.price_change_percentage_24h || 0) - (b.price_change_percentage_24h || 0)); break
      default: break // already by market cap
    }

    return list
  }, [coins, search, sortBy, showDipsOnly])

  const dipCount = coins.filter(c => (c.price_change_percentage_24h || 0) <= -5).length
  const rocketCount = coins.filter(c => (c.price_change_percentage_24h || 0) >= 10).length

  return (
    <div className="p-3 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Globe size={20} className="text-blue-400" />
            Top {coins.length} Crypto Live
          </h1>
          <p className="text-[10px] text-slate-500">
            {lastUpdate ? `Updated ${lastUpdate}` : 'Loading...'} • Auto-refresh 8s
          </p>
        </div>
        <button onClick={() => { hapticFeedback?.('impact'); loadCoins() }} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={16} className={`text-blue-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Global Stats */}
      {globalData && (
        <div className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-2.5 mb-3">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-[9px] text-slate-500">Total MCap</p>
              <p className="text-xs font-bold text-white">{formatNum(globalData.total_market_cap?.usd)}</p>
            </div>
            <div>
              <p className="text-[9px] text-slate-500">24h Volume</p>
              <p className="text-xs font-bold text-white">{formatNum(globalData.total_volume?.usd)}</p>
            </div>
            <div>
              <p className="text-[9px] text-slate-500">BTC Dom</p>
              <p className="text-xs font-bold text-yellow-400">{(globalData.market_cap_percentage?.btc || 0).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="flex gap-2 mb-3">
        <div className="flex-1 bg-red-500/10 border border-red-500/20 rounded-xl p-2 text-center">
          <button onClick={() => { setShowDipsOnly(!showDipsOnly); hapticFeedback?.('impact') }} className="w-full">
            <p className="text-lg font-bold text-red-400">{dipCount}</p>
            <p className="text-[9px] text-red-300">{showDipsOnly ? '🔍 Showing Dips' : 'Dips ≤ -5%'}</p>
          </button>
        </div>
        <div className="flex-1 bg-green-500/10 border border-green-500/20 rounded-xl p-2 text-center">
          <p className="text-lg font-bold text-green-400">{rocketCount}</p>
          <p className="text-[9px] text-green-300">Rockets ≥ +10%</p>
        </div>
        <div className="flex-1 bg-blue-500/10 border border-blue-500/20 rounded-xl p-2 text-center">
          <p className="text-lg font-bold text-blue-400">{coins.length}</p>
          <p className="text-[9px] text-blue-300">Total Coins</p>
        </div>
      </div>

      {/* Search + Sort */}
      <div className="flex gap-2 mb-3">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search BTC, ETH, SOL..."
            className="w-full bg-slate-800/50 border border-slate-700/30 rounded-xl pl-8 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-blue-500/50" />
        </div>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)}
          className="bg-slate-800/50 border border-slate-700/30 rounded-xl px-2 py-2 text-xs text-white outline-none">
          {SORT_OPTIONS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
      </div>

      {/* Loading */}
      {loading && coins.length === 0 && (
        <div className="space-y-1">
          {Array.from({ length: 10 }, (_, i) => (
            <div key={i} className="bg-slate-800/50 rounded-xl h-14 animate-pulse" />
          ))}
        </div>
      )}

      {/* Coin List */}
      <div className="space-y-1">
        {processed.slice(0, 200).map((coin, i) => {
          const change24h = coin.price_change_percentage_24h || 0
          const change1h = coin.price_change_percentage_1h_in_currency || 0
          const change7d = coin.price_change_percentage_7d_in_currency || 0
          const isPos = change24h >= 0
          const isDip = change24h <= -5
          const isRocket = change24h >= 10

          return (
            <div key={coin.id} className={`flex items-center justify-between p-2.5 rounded-xl border transition-all
              ${isDip ? 'bg-red-500/5 border-red-500/20' : isRocket ? 'bg-green-500/5 border-green-500/20' : 'bg-slate-800/50 border-slate-700/20'}`}>
              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                <span className="text-[10px] text-slate-600 w-5 text-right">{coin.market_cap_rank || i + 1}</span>
                {coin.image && <img src={coin.image} alt="" className="w-6 h-6 rounded-full" onError={e => e.target.style.display='none'} />}
                <div className="min-w-0">
                  <p className="text-xs font-bold truncate">{coin.symbol?.toUpperCase()}</p>
                  <p className="text-[9px] text-slate-500 truncate">{coin.name}</p>
                </div>
              </div>

              <div className="text-right ml-2">
                <p className="text-xs font-bold">{formatPrice(coin.current_price)}</p>
                <div className="flex items-center justify-end gap-1">
                  <span className={`text-[10px] font-bold flex items-center ${isPos ? 'text-green-400' : 'text-red-400'}`}>
                    {isPos ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                    {Math.abs(change24h).toFixed(1)}%
                  </span>
                  {isDip && <span className="text-[8px]">🔥</span>}
                  {isRocket && <span className="text-[8px]">🚀</span>}
                </div>
              </div>

              <div className="text-right ml-3 hidden sm:block">
                <p className="text-[10px] text-slate-400">{formatNum(coin.total_volume)}</p>
                <p className="text-[10px] text-slate-500">{formatNum(coin.market_cap)}</p>
              </div>
            </div>
          )
        })}
      </div>

      {processed.length > 200 && (
        <p className="text-center text-slate-500 text-xs mt-3">Showing 200 of {processed.length} coins</p>
      )}
    </div>
  )
}

export default CryptoTop1000
