import React, { useState, useEffect } from 'react'
import {
  Copy, Trophy, TrendingUp, TrendingDown, Users, Star,
  Zap, Target, Shield, ArrowRight, RefreshCw, Eye, Play, Pause
} from 'lucide-react'
import { fetchCopyTradingSignals, fetchCopyTradingLeaderboard } from '../services/api'
import { useApp } from '../context/AppContext'

const CopyTrading = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const userId = String(user?.id || '')
  const [signals, setSignals] = useState([])
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('signals')
  const [copying, setCopying] = useState({})

  const load = async () => {
    setLoading(true)
    try {
      const [sigRes, lbRes] = await Promise.all([
        fetchCopyTradingSignals(userId).catch(() => null),
        fetchCopyTradingLeaderboard().catch(() => null)
      ])
      setSignals(sigRes?.data?.data || sigRes?.data?.signals || [])
      setLeaderboard(lbRes?.data?.data || lbRes?.data?.leaderboard || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleCopy = (signal) => {
    hapticFeedback('impact')
    setCopying(p => ({ ...p, [signal.id || signal.symbol]: true }))
    addNotification(`📋 Copied ${signal.symbol} trade signal!`, 'success')
    hapticFeedback('success')
    setTimeout(() => setCopying(p => ({ ...p, [signal.id || signal.symbol]: false })), 2000)
  }

  const stats = [
    { label: 'Active Signals', value: signals.length, icon: Zap, color: 'from-blue-500 to-cyan-500' },
    { label: 'Win Rate', value: '78%', icon: Target, color: 'from-emerald-500 to-green-500' },
    { label: 'Top Traders', value: leaderboard.length, icon: Trophy, color: 'from-amber-500 to-orange-500' },
  ]

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      {[1,2,3].map(i => <div key={i} className="skeleton h-28 rounded-2xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Copy size={16} />
            </div>
            <span>Copy Trading</span>
          </h1>
          <p className="text-slate-400 text-sm">Copy JARVIS AI & top trader signals</p>
        </div>
        <button onClick={load} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {stats.map((s, i) => (
          <div key={i} className={`bg-gradient-to-br ${s.color} rounded-xl p-3 text-center`}>
            <s.icon size={18} className="mx-auto mb-1" />
            <p className="text-lg font-bold">{s.value}</p>
            <p className="text-[10px] opacity-80">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-4">
        {['signals', 'leaderboard'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`flex-1 py-2 rounded-lg text-xs font-medium capitalize transition-all ${
              activeTab === t ? 'bg-blue-600 text-white' : 'text-slate-400'
            }`}>{t === 'signals' ? '⚡ Live Signals' : '🏆 Leaderboard'}</button>
        ))}
      </div>

      {/* SIGNALS TAB */}
      {activeTab === 'signals' && (
        <div className="space-y-3">
          {signals.length === 0 ? (
            <div className="text-center py-12">
              <Zap size={40} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500">No active signals right now</p>
              <p className="text-xs text-slate-600 mt-1">JARVIS AI is analyzing markets...</p>
            </div>
          ) : signals.map((sig, i) => {
            const isBuy = (sig.side || sig.signal || '').toLowerCase().includes('buy') ||
                          (sig.side || sig.signal || '').toLowerCase().includes('long')
            return (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isBuy ? 'bg-emerald-500/20' : 'bg-red-500/20'
                    }`}>
                      {isBuy ? <TrendingUp size={16} className="text-emerald-400" /> : <TrendingDown size={16} className="text-red-400" />}
                    </div>
                    <div>
                      <p className="font-bold text-sm">{sig.symbol || sig.pair || 'N/A'}</p>
                      <p className="text-[10px] text-slate-500">{sig.exchange || sig.source || 'JARVIS AI'}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    isBuy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}>{sig.side || sig.signal || (isBuy ? 'BUY' : 'SELL')}</span>
                </div>

                <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
                  <div>
                    <p className="text-slate-500">Entry</p>
                    <p className="font-medium">{sig.entry || sig.price || '--'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Target</p>
                    <p className="font-medium text-emerald-400">{sig.target || sig.tp || '--'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Stop Loss</p>
                    <p className="font-medium text-red-400">{sig.stop_loss || sig.sl || '--'}</p>
                  </div>
                </div>

                {sig.confidence && (
                  <div className="mb-3">
                    <div className="flex justify-between text-[10px] mb-1">
                      <span className="text-slate-500">Confidence</span>
                      <span className="text-blue-400">{sig.confidence}%</span>
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                        style={{ width: `${sig.confidence}%` }} />
                    </div>
                  </div>
                )}

                <button onClick={() => handleCopy(sig)}
                  className={`w-full py-2 rounded-lg text-xs font-bold active:scale-95 transition-all ${
                    copying[sig.id || sig.symbol]
                      ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white hover:bg-blue-500'
                  }`}>
                  {copying[sig.id || sig.symbol] ? '✅ Copied!' : '📋 Copy This Trade'}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* LEADERBOARD TAB */}
      {activeTab === 'leaderboard' && (
        <div className="space-y-2">
          {leaderboard.length === 0 ? (
            <div className="text-center py-12">
              <Trophy size={40} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500">Leaderboard loading...</p>
            </div>
          ) : leaderboard.map((t, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3 flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                i === 0 ? 'bg-amber-500/20 text-amber-400' :
                i === 1 ? 'bg-slate-400/20 text-slate-300' :
                i === 2 ? 'bg-orange-500/20 text-orange-400' :
                'bg-slate-700 text-slate-400'
              }`}>#{i + 1}</div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm truncate">{t.name || t.trader || `Trader ${i + 1}`}</p>
                <div className="flex items-center space-x-2 text-[10px] text-slate-400">
                  <span>{t.total_trades || 0} trades</span>
                  <span>•</span>
                  <span className="text-emerald-400">{t.win_rate || 0}% WR</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-emerald-400">+{t.pnl || t.profit || 0}%</p>
                <p className="text-[10px] text-slate-500">{t.period || '30d'}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default CopyTrading
