/**
 * 📊 JARVIS P&L Journal with Charts
 * ════════════════════════════════════
 * Track every trade, show daily/weekly profit graphs
 * Beautiful charts with Chart.js
 * Export to CSV, share on WhatsApp
 */
import React, { useState, useEffect, useMemo } from 'react'
import {
  TrendingUp, TrendingDown, Calendar, BarChart3, PieChart, Download,
  Share2, Filter, ChevronDown, ArrowUpRight, ArrowDownRight, Target,
  DollarSign, Activity, Clock, Trophy, Flame, Plus, X
} from 'lucide-react'
import { useApp } from '../context/AppContext'

const STORAGE_KEY = 'jarvis_pnl_journal'

const loadJournal = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}

const saveJournal = (j) => localStorage.setItem(STORAGE_KEY, JSON.stringify(j))

const PnLJournal = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const [trades, setTrades] = useState(loadJournal)
  const [timeframe, setTimeframe] = useState('week') // day, week, month, all
  const [showAdd, setShowAdd] = useState(false)
  const [newTrade, setNewTrade] = useState({
    symbol: '', type: 'BUY', entry: '', exit: '', quantity: '', date: new Date().toISOString().split('T')[0], notes: ''
  })

  // Also load from paper trading history
  useEffect(() => {
    try {
      const paperState = JSON.parse(localStorage.getItem('jarvis_paper_trading') || '{}')
      if (paperState.history?.length && trades.length === 0) {
        const imported = paperState.history.map(h => ({
          id: h.id,
          symbol: h.symbol,
          type: h.type,
          entry: h.entryPrice,
          exit: h.exitPrice,
          quantity: h.quantity,
          pnl: h.pnl,
          date: h.closedAt?.split('T')[0] || new Date().toISOString().split('T')[0],
          notes: 'Paper trade',
          source: 'paper'
        }))
        setTrades(imported)
        saveJournal(imported)
      }
    } catch {}
  }, [])

  // Add trade
  const addTrade = () => {
    const entry = parseFloat(newTrade.entry)
    const exit = parseFloat(newTrade.exit)
    const qty = parseFloat(newTrade.quantity)
    if (!newTrade.symbol || !entry || !exit || !qty) {
      addNotification('Fill all fields!', 'error')
      return
    }
    const pnl = newTrade.type === 'BUY' ? (exit - entry) * qty : (entry - exit) * qty
    const trade = {
      id: Date.now(),
      ...newTrade,
      entry, exit, quantity: qty, pnl,
      source: 'manual'
    }
    const updated = [trade, ...trades]
    setTrades(updated)
    saveJournal(updated)
    setShowAdd(false)
    setNewTrade({ symbol: '', type: 'BUY', entry: '', exit: '', quantity: '', date: new Date().toISOString().split('T')[0], notes: '' })
    hapticFeedback('success')
    addNotification(`Trade logged: ${newTrade.symbol} ${pnl >= 0 ? '✅ Profit' : '❌ Loss'}: ₹${pnl.toFixed(2)}`, pnl >= 0 ? 'success' : 'error')
  }

  // Delete trade
  const deleteTrade = (id) => {
    const updated = trades.filter(t => t.id !== id)
    setTrades(updated)
    saveJournal(updated)
    hapticFeedback('impact')
  }

  // Filter by timeframe
  const filteredTrades = useMemo(() => {
    const now = new Date()
    return trades.filter(t => {
      if (timeframe === 'all') return true
      const tradeDate = new Date(t.date)
      const diffDays = (now - tradeDate) / (1000 * 60 * 60 * 24)
      if (timeframe === 'day') return diffDays <= 1
      if (timeframe === 'week') return diffDays <= 7
      if (timeframe === 'month') return diffDays <= 30
      return true
    })
  }, [trades, timeframe])

  // Stats
  const stats = useMemo(() => {
    const wins = filteredTrades.filter(t => t.pnl > 0)
    const losses = filteredTrades.filter(t => t.pnl <= 0)
    const totalPnL = filteredTrades.reduce((s, t) => s + (t.pnl || 0), 0)
    const avgWin = wins.length ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0
    const avgLoss = losses.length ? losses.reduce((s, t) => s + Math.abs(t.pnl), 0) / losses.length : 0
    const winRate = filteredTrades.length ? ((wins.length / filteredTrades.length) * 100) : 0
    const bestTrade = filteredTrades.length ? Math.max(...filteredTrades.map(t => t.pnl)) : 0
    const worstTrade = filteredTrades.length ? Math.min(...filteredTrades.map(t => t.pnl)) : 0

    return { totalPnL, wins: wins.length, losses: losses.length, winRate, avgWin, avgLoss, bestTrade, worstTrade, total: filteredTrades.length }
  }, [filteredTrades])

  // Daily P&L for chart
  const dailyPnL = useMemo(() => {
    const grouped = {}
    filteredTrades.forEach(t => {
      const day = t.date || 'Unknown'
      grouped[day] = (grouped[day] || 0) + (t.pnl || 0)
    })
    return Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)).map(([date, pnl]) => ({ date, pnl }))
  }, [filteredTrades])

  // Cumulative P&L
  const cumulativePnL = useMemo(() => {
    let cumulative = 0
    return dailyPnL.map(d => {
      cumulative += d.pnl
      return { date: d.date, pnl: d.pnl, cumulative }
    })
  }, [dailyPnL])

  // Export to CSV
  const exportCSV = () => {
    const header = 'Date,Symbol,Type,Entry,Exit,Qty,P&L,Notes\n'
    const rows = trades.map(t =>
      `${t.date},${t.symbol},${t.type},${t.entry},${t.exit},${t.quantity},${t.pnl?.toFixed(2)},${t.notes || ''}`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `jarvis_pnl_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    addNotification('📥 CSV exported!', 'success')
  }

  // Share summary
  const shareSummary = () => {
    const text = `📊 JARVIS Trading Journal\n` +
      `━━━━━━━━━━━━━━━━━\n` +
      `💰 Total P&L: ₹${stats.totalPnL.toFixed(2)}\n` +
      `🎯 Win Rate: ${stats.winRate.toFixed(1)}%\n` +
      `✅ Wins: ${stats.wins} | ❌ Losses: ${stats.losses}\n` +
      `📈 Best: ₹${stats.bestTrade.toFixed(2)}\n` +
      `📉 Worst: ₹${stats.worstTrade.toFixed(2)}\n` +
      `\n🤖 Powered by JARVIS AI Trading`

    if (navigator.share) {
      navigator.share({ title: 'JARVIS P&L', text })
    } else {
      navigator.clipboard?.writeText(text)
      addNotification('📋 Summary copied!', 'success')
    }
  }

  // Simple bar chart component
  const maxPnL = Math.max(...dailyPnL.map(d => Math.abs(d.pnl)), 1)

  return (
    <div className="p-4 pb-24 bg-[#0a0e1a] min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold">📊 P&L Journal</h1>
          <p className="text-slate-500 text-xs">Track every trade, visualize your growth</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportCSV} className="p-2 bg-slate-800 rounded-xl hover:bg-slate-700">
            <Download size={16} className="text-slate-400" />
          </button>
          <button onClick={shareSummary} className="p-2 bg-slate-800 rounded-xl hover:bg-slate-700">
            <Share2 size={16} className="text-slate-400" />
          </button>
          <button onClick={() => setShowAdd(true)} className="p-2 bg-blue-600 rounded-xl hover:bg-blue-700">
            <Plus size={16} className="text-white" />
          </button>
        </div>
      </div>

      {/* P&L Summary Card */}
      <div className="bg-gradient-to-br from-slate-800/50 to-slate-800/30 border border-slate-700/30 rounded-2xl p-5 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-slate-400 text-xs">Total P&L</p>
            <h2 className={`text-2xl font-bold ${stats.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {stats.totalPnL >= 0 ? '+' : ''}₹{stats.totalPnL.toFixed(2)}
            </h2>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stats.totalPnL >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
            {stats.totalPnL >= 0 ? <TrendingUp size={24} className="text-emerald-400" /> : <TrendingDown size={24} className="text-red-400" />}
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <p className="text-[10px] text-slate-500">Win Rate</p>
            <p className="text-sm font-bold text-blue-400">{stats.winRate.toFixed(1)}%</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-slate-500">Wins</p>
            <p className="text-sm font-bold text-emerald-400">{stats.wins}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-slate-500">Losses</p>
            <p className="text-sm font-bold text-red-400">{stats.losses}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-slate-500">Total</p>
            <p className="text-sm font-bold text-white">{stats.total}</p>
          </div>
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="flex gap-1 bg-slate-800/50 rounded-xl p-1 mb-4">
        {['day', 'week', 'month', 'all'].map(tf => (
          <button key={tf} onClick={() => setTimeframe(tf)}
            className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all capitalize ${
              timeframe === tf ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}>
            {tf}
          </button>
        ))}
      </div>

      {/* P&L Chart (simple bars) */}
      {dailyPnL.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/30 rounded-2xl p-4 mb-4">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <BarChart3 size={14} className="text-blue-400" /> Daily P&L
          </h3>
          <div className="flex items-end gap-1 h-32">
            {dailyPnL.slice(-14).map((d, i) => {
              const height = Math.max((Math.abs(d.pnl) / maxPnL) * 100, 4)
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-end">
                  <div
                    className={`w-full rounded-t-sm transition-all ${d.pnl >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}
                    style={{ height: `${height}%`, minHeight: 4 }}
                  />
                  <p className="text-[7px] text-slate-600 mt-1 truncate w-full text-center">
                    {d.date.split('-').slice(1).join('/')}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Cumulative P&L Line */}
      {cumulativePnL.length > 1 && (
        <div className="bg-slate-800/50 border border-slate-700/30 rounded-2xl p-4 mb-4">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Activity size={14} className="text-purple-400" /> Cumulative P&L
          </h3>
          <div className="h-20 flex items-end gap-1">
            {cumulativePnL.slice(-20).map((d, i, arr) => {
              const maxCum = Math.max(...arr.map(x => Math.abs(x.cumulative)), 1)
              const normalized = (d.cumulative / maxCum) * 50 + 50
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-end" style={{ height: '80px' }}>
                  <div
                    className={`w-full rounded-sm ${d.cumulative >= 0 ? 'bg-purple-500/60' : 'bg-red-500/60'}`}
                    style={{ height: `${Math.max(normalized, 4)}%` }}
                  />
                </div>
              )
            })}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[8px] text-slate-600">{cumulativePnL[0]?.date}</span>
            <span className={`text-xs font-bold ${cumulativePnL[cumulativePnL.length - 1]?.cumulative >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              ₹{cumulativePnL[cumulativePnL.length - 1]?.cumulative?.toFixed(0) || 0}
            </span>
          </div>
        </div>
      )}

      {/* Trade List */}
      <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
        <Clock size={14} className="text-slate-400" /> Recent Trades
      </h3>
      <div className="space-y-2">
        {filteredTrades.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 size={40} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No trades yet</p>
            <p className="text-slate-600 text-xs mt-1">Add trades manually or use Paper Trading mode</p>
          </div>
        ) : filteredTrades.slice(0, 50).map(trade => (
          <div key={trade.id} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3 group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${trade.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {trade.type}
                </span>
                <span className="text-sm font-semibold">{trade.symbol}</span>
                <span className="text-[10px] text-slate-500">×{trade.quantity}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {trade.pnl >= 0 ? '+' : ''}₹{trade.pnl?.toFixed(2)}
                </span>
                <button onClick={() => deleteTrade(trade.id)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all">
                  <X size={12} className="text-red-400" />
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
              <span>₹{trade.entry} → ₹{trade.exit}</span>
              <span>{trade.date}</span>
            </div>
            {trade.notes && <p className="text-[10px] text-slate-600 mt-1 italic">{trade.notes}</p>}
          </div>
        ))}
      </div>

      {/* Add Trade Modal */}
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-end" onClick={() => setShowAdd(false)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <div className="relative bg-slate-900 border-t border-slate-700 rounded-t-3xl w-full max-w-lg p-5 animate-slide-up" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">📝 Log Trade</h3>
              <button onClick={() => setShowAdd(false)} className="p-1.5 bg-slate-800 rounded-full">
                <X size={16} className="text-slate-400" />
              </button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input placeholder="Symbol (e.g. BTC)" value={newTrade.symbol} onChange={e => setNewTrade(p => ({ ...p, symbol: e.target.value.toUpperCase() }))}
                  className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" />
                <select value={newTrade.type} onChange={e => setNewTrade(p => ({ ...p, type: e.target.value }))}
                  className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none">
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <input type="number" placeholder="Entry ₹" value={newTrade.entry} onChange={e => setNewTrade(p => ({ ...p, entry: e.target.value }))}
                  className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" />
                <input type="number" placeholder="Exit ₹" value={newTrade.exit} onChange={e => setNewTrade(p => ({ ...p, exit: e.target.value }))}
                  className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" />
                <input type="number" placeholder="Qty" value={newTrade.quantity} onChange={e => setNewTrade(p => ({ ...p, quantity: e.target.value }))}
                  className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500" />
              </div>
              <input type="date" value={newTrade.date} onChange={e => setNewTrade(p => ({ ...p, date: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none" />
              <input placeholder="Notes (optional)" value={newTrade.notes} onChange={e => setNewTrade(p => ({ ...p, notes: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white outline-none" />
              <button onClick={addTrade} className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold transition-colors">
                Log Trade
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PnLJournal
