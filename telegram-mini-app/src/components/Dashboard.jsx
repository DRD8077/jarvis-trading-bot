import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  TrendingUp, TrendingDown, Wallet, Activity, Bot, Zap, Search,
  Shield, BarChart3, Gem, Radio, Brain, ChevronRight, RefreshCw, Flame,
  ArrowUpRight, ArrowDownRight, Sparkles, Eye, EyeOff, Globe, Rocket,
  Layers, LineChart, ScanLine, ShieldCheck, Copy
} from 'lucide-react'
import { fetchDashboard, fetchNews, fetchSentiment } from '../services/api'
import { useApp } from '../context/AppContext'
import realtime from '../services/realtime'

const Dashboard = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [news, setNews] = useState([])
  const [sentiment, setSentiment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [showBalance, setShowBalance] = useState(true)

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const [dashRes, newsRes, sentRes] = await Promise.all([
        fetchDashboard().catch(() => null),
        fetchNews().catch(() => null),
        fetchSentiment().catch(() => null)
      ])
      if (dashRes?.data) setData(dashRes.data)
      if (newsRes?.data) setNews(Array.isArray(newsRes.data) ? newsRes.data : newsRes.data?.news || [])
      if (sentRes?.data) setSentiment(sentRes.data)
      if (silent) { hapticFeedback('success'); addNotification('Data refreshed ✨', 'success') }
    } catch (e) {
      console.error('Dashboard load error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [hapticFeedback, addNotification])

  useEffect(() => { loadData() }, [loadData])

  // Real-time WebSocket for live price tickers
  useEffect(() => {
    let unsub
    try {
      unsub = realtime.subscribe('dashboard', (liveData) => {
        if (liveData?.market_ticker) {
          setData(prev => prev ? { ...prev, market_ticker: liveData.market_ticker } : prev)
        }
        if (liveData?.portfolio) {
          setData(prev => prev ? { ...prev, portfolio: { ...prev.portfolio, ...liveData.portfolio } } : prev)
        }
        if (liveData?.fear_greed) {
          setData(prev => prev ? { ...prev, fear_greed: liveData.fear_greed } : prev)
        }
      }, { pollInterval: 10000, pollUrl: '/dashboard' })
    } catch (e) {
      console.warn('[Dashboard] Realtime subscribe failed, using polling only')
    }

    return () => { if (unsub) unsub() }
  }, [])

  // Fallback auto-refresh every 15s
  useEffect(() => {
    const iv = setInterval(() => loadData(true), 15000)
    return () => clearInterval(iv)
  }, [loadData])

  const quickActions = [
    { icon: Bot, label: 'AI Chat', color: 'from-blue-500 to-cyan-400', path: '/chat', glow: 'shadow-blue-500/30' },
    { icon: Zap, label: 'Auto Trade', color: 'from-amber-500 to-orange-400', path: '/auto-trader', glow: 'shadow-amber-500/30' },
    { icon: Gem, label: 'Gems', color: 'from-pink-500 to-rose-400', path: '/gems', glow: 'shadow-pink-500/30' },
    { icon: Search, label: 'Screener', color: 'from-emerald-500 to-teal-400', path: '/screener', glow: 'shadow-emerald-500/30' },
    { icon: BarChart3, label: 'Signals', color: 'from-violet-500 to-purple-400', path: '/trading', glow: 'shadow-violet-500/30' },
    { icon: Brain, label: 'Intelligence', color: 'from-indigo-500 to-blue-400', path: '/intelligence', glow: 'shadow-indigo-500/30' },
    { icon: Rocket, label: 'MEGA AI', color: 'from-red-500 to-yellow-400', path: '/mega-trader', glow: 'shadow-red-500/30' },
    { icon: Flame, label: 'Stocks', color: 'from-orange-500 to-amber-400', path: '/indian-stocks', glow: 'shadow-orange-500/30' },
    { icon: Layers, label: 'Options', color: 'from-cyan-500 to-blue-400', path: '/nifty-options', glow: 'shadow-cyan-500/30' },
  ]

  // Extract data from API response
  const portfolio = data?.portfolio || {}
  const signals = data?.signals || []
  const movers = data?.top_movers || {}
  const regime = data?.regime || {}
  const marketTicker = data?.market_ticker || []
  const fearGreed = data?.fear_greed || data?.sentiment || {}
  const dexTrending = data?.dex_trending || []
  const pumpfun = data?.pumpfun || []
  const vix = data?.vix || {}
  const indices = data?.indices || []

  const fgScore = fearGreed?.score || fearGreed?.value || sentiment?.score || sentiment?.data?.score || regime?.fear_greed || 0
  const fgLabel = fgScore > 75 ? 'Extreme Greed' : fgScore > 60 ? 'Greed' : fgScore > 40 ? 'Neutral' : fgScore > 25 ? 'Fear' : 'Extreme Fear'
  const fgColor = fgScore > 60 ? 'text-emerald-400' : fgScore > 40 ? 'text-yellow-400' : 'text-red-400'

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-[#0a0e1a] min-h-screen">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-slate-800/50 rounded-lg animate-pulse" />
          <div className="h-8 w-8 bg-slate-800/50 rounded-full animate-pulse" />
        </div>
        <div className="h-40 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-24 bg-slate-800/40 rounded-xl animate-pulse" />
          <div className="h-24 bg-slate-800/40 rounded-xl animate-pulse" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[1,2,3,4,5,6].map(i => <div key={i} className="h-20 bg-slate-800/40 rounded-xl animate-pulse" />)}
        </div>
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-20 bg-slate-800/40 rounded-xl animate-pulse" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 space-y-5 bg-[#0a0e1a] min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Hey, {user?.first_name || 'Trader'} 👋
          </h1>
          <div className="flex items-center space-x-2 mt-0.5">
            <div className="flex items-center space-x-1">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 text-[10px] font-medium">LIVE</span>
            </div>
            <span className="text-slate-600 text-[10px]">•</span>
            <p className="text-slate-500 text-[10px]">Auto-refresh 15s</p>
          </div>
        </div>
        <button onClick={() => loadData(true)} 
          className="p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-blue-500/30 transition-all active:scale-90">
          <RefreshCw size={16} className={`text-blue-400 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Portfolio Card — Premium Glass Effect */}
      <div className="relative overflow-hidden rounded-2xl">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/90 via-purple-600/90 to-pink-600/90" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=%2220%22 height=%2220%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cpath d=%22M0 0h20v20H0z%22 fill=%22none%22/%3E%3Ccircle cx=%221%22 cy=%221%22 r=%221%22 fill=%22rgba(255,255,255,0.05)%22/%3E%3C/svg%3E')]" />
        <div className="relative p-5">
          <div className="flex items-center justify-between mb-1">
            <p className="text-white/70 text-xs font-medium tracking-wide uppercase">Portfolio Balance</p>
            <button onClick={() => setShowBalance(!showBalance)} className="text-white/60 hover:text-white/90 transition-colors">
              {showBalance ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>
          <p className="text-3xl font-bold tracking-tight">
            {showBalance ? `₹${(portfolio.balance_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '₹ •••••'}
          </p>
          <div className="flex items-center mt-2 space-x-3">
            <div className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
              (portfolio.pnl_inr || 0) >= 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
            }`}>
              {(portfolio.pnl_inr || 0) >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
              <span>{(portfolio.pnl_inr || 0) >= 0 ? '+' : ''}₹{Math.abs(portfolio.pnl_inr || 0).toLocaleString()}</span>
            </div>
            <span className="text-white/40 text-[10px]">24h P&L</span>
          </div>
          <div className="flex mt-4 space-x-3">
            <button onClick={() => navigate('/wallet')} 
              className="flex-1 bg-white/15 hover:bg-white/25 backdrop-blur-sm rounded-xl py-2.5 text-sm font-semibold text-center transition-all active:scale-95 border border-white/10">
              💳 Deposit
            </button>
            <button onClick={() => navigate('/trading')} 
              className="flex-1 bg-white/15 hover:bg-white/25 backdrop-blur-sm rounded-xl py-2.5 text-sm font-semibold text-center transition-all active:scale-95 border border-white/10">
              📈 Trade Now
            </button>
          </div>
        </div>
      </div>

      {/* Market Stats Row */}
      <div className="grid grid-cols-3 gap-2.5">
        <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-3 border border-slate-700/30">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Regime</p>
          <p className={`text-sm font-bold mt-0.5 ${
            (regime.regime || '').toLowerCase().includes('bull') || (regime.regime || '').toLowerCase().includes('greed') ? 'text-emerald-400' :
            (regime.regime || '').toLowerCase().includes('bear') || (regime.regime || '').toLowerCase().includes('fear') ? 'text-red-400' : 'text-yellow-400'
          }`}>{regime.regime || '---'}</p>
          {regime.rec && <p className="text-[9px] text-slate-500 mt-0.5 truncate">{regime.rec}</p>}
        </div>
        <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-3 border border-slate-700/30">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Fear/Greed</p>
          <p className={`text-sm font-bold mt-0.5 ${fgColor}`}>{fgScore || '--'}/100</p>
          <p className="text-[9px] text-slate-500 mt-0.5">{fgLabel}</p>
        </div>
        <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-3 border border-slate-700/30">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">VIX</p>
          <p className={`text-sm font-bold mt-0.5 ${(vix.value || regime.vix || 0) > 20 ? 'text-red-400' : 'text-emerald-400'}`}>
            {vix.value || regime.vix || '--'}
          </p>
          <p className="text-[9px] text-slate-500 mt-0.5">{(vix.value || regime.vix || 0) > 20 ? 'High Vol' : 'Low Vol'}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">⚡ Quick Actions</h3>
        <div className="grid grid-cols-3 gap-2.5">
          {quickActions.map((a, i) => {
            const Icon = a.icon
            return (
              <button key={i} onClick={() => { hapticFeedback('impact'); navigate(a.path) }}
                className={`bg-gradient-to-br ${a.color} p-3.5 rounded-xl flex flex-col items-center space-y-1.5 
                shadow-lg ${a.glow} hover:scale-[1.03] active:scale-95 transition-all duration-200`}>
                <Icon size={20} className="text-white drop-shadow-lg" />
                <span className="text-[10px] font-bold text-white/95 tracking-wide">{a.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Live Market Prices */}
      {marketTicker.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">🔴 Live Prices</h3>
            <div className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[10px] text-red-400 font-medium">LIVE</span>
            </div>
          </div>
          <div className="space-y-1.5">
            {marketTicker.slice(0, 8).map((coin, i) => (
              <div key={i} className="bg-slate-800/30 backdrop-blur-sm rounded-xl px-3.5 py-2.5 border border-slate-700/20 
                flex items-center justify-between hover:border-blue-500/20 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                    i < 3 ? 'bg-gradient-to-br from-amber-500 to-orange-500' :
                    i < 5 ? 'bg-gradient-to-br from-blue-500 to-cyan-500' : 'bg-gradient-to-br from-purple-500 to-pink-500'
                  }`}>
                    {(coin.symbol || '??').slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-sm font-bold">{coin.symbol}</p>
                    <p className="text-[10px] text-slate-500 truncate max-w-[100px]">{coin.name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">
                    {coin.price_inr > 1000 ? `₹${coin.price_inr.toLocaleString('en-IN', {maximumFractionDigits: 0})}` :
                     coin.price_inr > 1 ? `₹${coin.price_inr.toFixed(2)}` :
                     `$${coin.price_usd?.toFixed(coin.price_usd > 1 ? 2 : 6) || '0'}`}
                  </p>
                  <span className={`text-[10px] font-semibold inline-flex items-center px-1.5 py-0.5 rounded-md ${
                    (coin.change_24h || 0) >= 0 ? 'text-emerald-400 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'
                  }`}>
                    {(coin.change_24h || 0) >= 0 ? '▲' : '▼'} {Math.abs(coin.change_24h || 0).toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Signals */}
      {signals.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">⚡ AI Signals</h3>
            <button onClick={() => navigate('/trading')} className="text-blue-400 text-[10px] font-medium flex items-center hover:text-blue-300">
              View All <ChevronRight size={12} />
            </button>
          </div>
          <div className="space-y-2">
            {signals.slice(0, 4).map((s, i) => (
              <div key={i} className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-3.5 border border-slate-700/20 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                    (s.signal || s.type || '').toUpperCase().includes('BUY') ? 'bg-emerald-500/15 ring-1 ring-emerald-500/30' : 'bg-red-500/15 ring-1 ring-red-500/30'
                  }`}>
                    {(s.signal || s.type || '').toUpperCase().includes('BUY')
                      ? <TrendingUp size={16} className="text-emerald-400" />
                      : <TrendingDown size={16} className="text-red-400" />
                    }
                  </div>
                  <div>
                    <p className="font-bold text-sm">{s.symbol || s.name}</p>
                    <p className="text-[10px] text-slate-500">
                      {s.signal || s.type} • <span className="text-blue-400">{s.confidence || s.strength || '--'}%</span>
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">₹{(s.price || s.entry || 0).toLocaleString()}</p>
                  {s.target && <p className="text-[10px] text-emerald-400">🎯 ₹{s.target.toLocaleString()}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Movers */}
      {(movers.gainers?.length > 0 || movers.losers?.length > 0) && (
        <div>
          <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">
            🔥 Top Movers
          </h3>
          <div className="flex space-x-2.5 overflow-x-auto pb-2 scrollbar-hide">
            {[...(movers.gainers || []).slice(0, 4), ...(movers.losers || []).slice(0, 3)].map((m, i) => (
              <div key={i} className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-3 border border-slate-700/20 min-w-[130px] flex-shrink-0">
                <p className="font-bold text-xs truncate">{m.symbol || m.name}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  ₹{(m.price || m.last_price || m.price_inr || 0).toLocaleString()}
                </p>
                <p className={`text-sm font-bold mt-1.5 ${(m.change || m.change_percent || m.change_24h || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(m.change || m.change_percent || m.change_24h || 0) >= 0 ? '+' : ''}{(m.change || m.change_percent || m.change_24h || 0).toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trending Gems */}
      {dexTrending.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">💎 Trending Gems</h3>
            <button onClick={() => navigate('/gems')} className="text-pink-400 text-[10px] font-medium flex items-center hover:text-pink-300">
              More <ChevronRight size={12} />
            </button>
          </div>
          <div className="flex space-x-2.5 overflow-x-auto pb-2 scrollbar-hide">
            {dexTrending.slice(0, 6).map((gem, i) => (
              <div key={i} className="bg-gradient-to-br from-slate-800/50 to-slate-800/20 rounded-xl p-3 border border-slate-700/20 min-w-[140px] flex-shrink-0">
                <p className="font-bold text-xs truncate">{gem.symbol || gem.base_token}</p>
                <p className="text-[9px] text-slate-500 truncate">{gem.name}</p>
                <p className="text-xs font-bold mt-1 text-white">${gem.price_usd?.toFixed(gem.price_usd > 1 ? 2 : 6) || '0'}</p>
                <div className="flex items-center mt-1 space-x-1">
                  <span className={`text-[10px] font-semibold ${(gem.change_24h || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(gem.change_24h || 0) >= 0 ? '+' : ''}{(gem.change_24h || 0).toFixed(1)}%
                  </span>
                  {gem.gem_score && (
                    <span className="text-[9px] px-1 py-0.5 rounded bg-purple-500/20 text-purple-300">
                      ⭐{gem.gem_score}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* News */}
      {news.length > 0 && (
        <div>
          <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">
            📰 Market News
          </h3>
          <div className="space-y-2">
            {news.slice(0, 4).map((n, i) => (
              <div key={i} className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-3 border border-slate-700/20">
                <p className="text-xs font-medium leading-relaxed">{n.title || n.headline || (typeof n === 'string' ? n : '')}</p>
                {n.source && <p className="text-[10px] text-slate-500 mt-1.5">{n.source} • {n.time || ''}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI CTA */}
      <div onClick={() => navigate('/chat')}
        className="relative overflow-hidden rounded-2xl cursor-pointer group active:scale-[0.98] transition-transform">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600" />
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/0 via-white/5 to-pink-600/0 group-hover:via-white/10 transition-colors" />
        <div className="relative p-5 flex items-center space-x-4">
          <div className="w-12 h-12 bg-white/10 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/10">
            <Sparkles size={24} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-base">Ask JARVIS AI ✨</p>
            <p className="text-indigo-200/80 text-xs">Analysis • Predictions • Trade Ideas • Hindi/English</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
