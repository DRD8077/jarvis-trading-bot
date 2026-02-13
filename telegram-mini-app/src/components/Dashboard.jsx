import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  TrendingUp, TrendingDown, Wallet, Activity, Bot, Zap, Search,
  Shield, BarChart3, Gem, Radio, Brain, ChevronRight, RefreshCw, Flame
} from 'lucide-react'
import { fetchDashboard, fetchNews, fetchSentiment } from '../services/api'
import { useApp } from '../context/AppContext'

const Dashboard = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [news, setNews] = useState([])
  const [sentiment, setSentiment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async (silent = false) => {
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
      if (silent) { hapticFeedback('success'); addNotification('Data refreshed', 'success') }
    } catch (e) {
      console.error('Dashboard load error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const quickActions = [
    { icon: Bot, label: 'AI Chat', color: 'from-blue-500 to-cyan-500', path: '/chat' },
    { icon: Zap, label: 'Auto Trade', color: 'from-amber-500 to-orange-500', path: '/auto-trader' },
    { icon: Gem, label: 'Gem Scanner', color: 'from-pink-500 to-rose-500', path: '/gems' },
    { icon: Search, label: 'Screener', color: 'from-emerald-500 to-teal-500', path: '/screener' },
    { icon: BarChart3, label: 'Signals', color: 'from-violet-500 to-purple-500', path: '/trading' },
    { icon: Brain, label: 'Intelligence', color: 'from-indigo-500 to-blue-500', path: '/intelligence' },
  ]

  const dashData = data?.data || data || {}
  const portfolio = dashData.portfolio || {}
  const signals = dashData.signals || []
  const movers = dashData.top_movers || dashData.movers || {}
  const regime = dashData.regime || dashData.market_regime || {}

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-32 w-full rounded-2xl" />
        <div className="grid grid-cols-2 gap-3">
          <div className="skeleton h-20" /><div className="skeleton h-20" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton h-20" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 space-y-5 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Hey, {user?.first_name || 'Trader'} 👋</h1>
          <p className="text-slate-400 text-sm">Your AI Trading Command Center</p>
        </div>
        <button onClick={() => loadData(true)} className="p-2 rounded-full bg-slate-800 hover:bg-slate-700">
          <RefreshCw size={18} className={`text-blue-400 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Portfolio Card */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-5 shadow-lg shadow-blue-500/20">
        <p className="text-blue-100 text-sm mb-1">Total Portfolio Value</p>
        <p className="text-3xl font-bold">
          ₹{(portfolio.total_value || portfolio.totalValue || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </p>
        <div className="flex items-center mt-2 space-x-4">
          <div className="flex items-center space-x-1">
            {(portfolio.pnl_percent || 0) >= 0 
              ? <TrendingUp size={14} className="text-emerald-300" />
              : <TrendingDown size={14} className="text-red-300" />
            }
            <span className={`text-sm font-medium ${(portfolio.pnl_percent || 0) >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
              {(portfolio.pnl_percent || 0) >= 0 ? '+' : ''}{(portfolio.pnl_percent || 0).toFixed(2)}%
            </span>
          </div>
          <span className="text-blue-200 text-xs">24h change</span>
        </div>
        <div className="flex mt-3 space-x-3">
          <button onClick={() => navigate('/wallet')} className="flex-1 bg-white/20 hover:bg-white/30 rounded-lg py-2 text-sm font-medium text-center transition-colors">
            Deposit
          </button>
          <button onClick={() => navigate('/trading')} className="flex-1 bg-white/20 hover:bg-white/30 rounded-lg py-2 text-sm font-medium text-center transition-colors">
            Trade Now
          </button>
        </div>
      </div>

      {/* Market Regime & Sentiment */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-xs mb-1">Market Regime</p>
          <p className={`text-lg font-bold ${
            (regime.regime || '').toLowerCase().includes('bull') ? 'text-emerald-400' :
            (regime.regime || '').toLowerCase().includes('bear') ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {regime.regime || regime.status || '---'}
          </p>
          <p className="text-slate-500 text-xs mt-1 truncate">{regime.signal || regime.description || ''}</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-xs mb-1">Fear & Greed</p>
          <p className={`text-lg font-bold ${
            (sentiment?.score || sentiment?.data?.score || 50) > 60 ? 'text-emerald-400' :
            (sentiment?.score || sentiment?.data?.score || 50) < 40 ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {sentiment?.score || sentiment?.data?.score || '--'}/100
          </p>
          <p className="text-slate-500 text-xs mt-1">{sentiment?.label || sentiment?.data?.label || ''}</p>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h3>
        <div className="grid grid-cols-3 gap-3">
          {quickActions.map((a, i) => {
            const Icon = a.icon
            return (
              <button key={i} onClick={() => { hapticFeedback('impact'); navigate(a.path) }}
                className={`bg-gradient-to-br ${a.color} p-3 rounded-xl flex flex-col items-center space-y-1.5 
                shadow-lg hover:scale-[1.02] active:scale-95 transition-transform`}>
                <Icon size={22} className="text-white" />
                <span className="text-xs font-medium text-white/90">{a.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Active Signals */}
      {signals.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Live Signals</h3>
            <button onClick={() => navigate('/trading')} className="text-blue-400 text-xs flex items-center">
              View All <ChevronRight size={14} />
            </button>
          </div>
          <div className="space-y-2">
            {signals.slice(0, 3).map((s, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    (s.signal || s.type || '').toUpperCase().includes('BUY') ? 'bg-emerald-500/20' : 'bg-red-500/20'
                  }`}>
                    {(s.signal || s.type || '').toUpperCase().includes('BUY')
                      ? <TrendingUp size={18} className="text-emerald-400" />
                      : <TrendingDown size={18} className="text-red-400" />
                    }
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{s.symbol || s.name}</p>
                    <p className="text-xs text-slate-400">{s.signal || s.type} • {s.confidence || s.strength || '--'}%</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">₹{(s.price || s.entry || 0).toLocaleString()}</p>
                  {s.target && <p className="text-xs text-emerald-400">T: ₹{s.target.toLocaleString()}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Movers */}
      {(movers.gainers || movers.losers) && (
        <div>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            <Flame size={14} className="inline text-orange-400 mr-1" /> Top Movers
          </h3>
          <div className="flex space-x-3 overflow-x-auto pb-2 scrollbar-hide">
            {[...(movers.gainers || []).slice(0, 3), ...(movers.losers || []).slice(0, 2)].map((m, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 min-w-[140px] flex-shrink-0">
                <p className="font-semibold text-sm truncate">{m.symbol || m.name}</p>
                <p className="text-xs text-slate-400">₹{(m.price || m.last_price || 0).toLocaleString()}</p>
                <p className={`text-sm font-bold mt-1 ${(m.change || m.change_percent || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(m.change || m.change_percent || 0) >= 0 ? '+' : ''}{(m.change || m.change_percent || 0).toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Breaking News */}
      {news.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            <Radio size={14} className="inline text-red-400 mr-1 animate-pulse" /> Breaking News
          </h3>
          <div className="space-y-2">
            {news.slice(0, 4).map((n, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                <p className="text-sm font-medium">{n.title || n.headline || n}</p>
                {n.source && <p className="text-xs text-slate-500 mt-1">{n.source} • {n.time || ''}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI CTA */}
      <div onClick={() => navigate('/chat')}
        className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-5 cursor-pointer hover:shadow-lg hover:shadow-indigo-500/20 transition-shadow">
        <div className="flex items-center space-x-3">
          <Bot size={32} className="text-white" />
          <div>
            <p className="font-bold text-lg">Ask JARVIS AI Anything</p>
            <p className="text-indigo-200 text-sm">Market analysis, trade ideas, predictions & more</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
