import React, { useState, useEffect } from 'react'
import {
  Zap, Play, Square, BarChart3, TrendingUp, Shield, RefreshCw,
  DollarSign, Target, Repeat, Clock, CheckCircle, AlertTriangle, Rocket
} from 'lucide-react'
import {
  fetchStrategies, startAutoTrader, stopAutoTrader, fetchAutoTraderStatus,
  fetchAutoTraderPerformance, fetchAutoTraderGems, compoundProfits
} from '../services/api'
import { useApp } from '../context/AppContext'

const AutoTrader = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [strategies, setStrategies] = useState([])
  const [status, setStatus] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [gems, setGems] = useState([])
  const [selectedStrategy, setSelectedStrategy] = useState('')
  const [investAmount, setInvestAmount] = useState('1000')
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [stratRes, statusRes, perfRes, gemRes] = await Promise.all([
        fetchStrategies().catch(() => null),
        fetchAutoTraderStatus().catch(() => null),
        fetchAutoTraderPerformance().catch(() => null),
        fetchAutoTraderGems().catch(() => null)
      ])

      const stratData = stratRes?.data?.data || stratRes?.data?.strategies || stratRes?.data || []
      setStrategies(Array.isArray(stratData) ? stratData : [])
      setStatus(statusRes?.data?.data || statusRes?.data || null)
      setPerformance(perfRes?.data?.data || perfRes?.data || null)
      
      const gemData = gemRes?.data?.data || gemRes?.data?.gems || gemRes?.data || []
      setGems(Array.isArray(gemData) ? gemData : [])
    } catch (e) {
      console.error('Auto-trader load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  // ⚡ Auto-refresh every 15s
  useEffect(() => {
    const iv = setInterval(loadData, 15000)
    return () => clearInterval(iv)
  }, [])

  const handleStart = async () => {
    if (!selectedStrategy) { addNotification('Select a strategy first', 'error'); return }
    if (!investAmount || parseFloat(investAmount) < 100) { addNotification('Min investment ₹100', 'error'); return }
    
    setStarting(true)
    hapticFeedback('impact')
    try {
      await startAutoTrader(selectedStrategy, parseFloat(investAmount))
      addNotification('🚀 Auto-Trader started!', 'success')
      hapticFeedback('success')
      loadData()
    } catch (e) {
      addNotification('Failed to start: ' + (e.response?.data?.detail || e.message), 'error')
      hapticFeedback('error')
    } finally {
      setStarting(false)
    }
  }

  const handleStop = async () => {
    hapticFeedback('impact')
    try {
      await stopAutoTrader()
      addNotification('Auto-Trader stopped', 'info')
      loadData()
    } catch (e) {
      addNotification('Failed to stop', 'error')
    }
  }

  const handleCompound = async () => {
    hapticFeedback('impact')
    try {
      await compoundProfits()
      addNotification('Profits compounded! 🎯', 'success')
      loadData()
    } catch (e) {
      addNotification('Compound failed', 'error')
    }
  }

  const isRunning = status?.is_running || status?.active || status?.status === 'running'

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-40 rounded-2xl" />
        <div className="skeleton h-24 rounded-xl" />
        {[1,2].map(i => <div key={i} className="skeleton h-20 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Paper Mode Banner */}
      <div className="mb-3 p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-2">
        <AlertTriangle size={16} className="text-amber-400 shrink-0" />
        <span className="text-xs text-amber-300">Paper Mode — Connect exchange API keys in Settings for live trading</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <Zap size={22} className="text-amber-400" />
            <span>Auto-Trader Bot</span>
          </h1>
          <p className="text-slate-400 text-sm">AI-powered automated trading</p>
        </div>
        <button onClick={loadData} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Status Banner */}
      <div className={`rounded-2xl p-5 mb-5 ${
        isRunning
          ? 'bg-gradient-to-r from-emerald-600 to-teal-600 shadow-lg shadow-emerald-500/20'
          : 'bg-gradient-to-r from-slate-700 to-slate-800 border border-slate-600'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-emerald-300 animate-pulse' : 'bg-slate-500'}`} />
            <span className="font-bold text-lg">{isRunning ? 'BOT IS RUNNING' : 'BOT STOPPED'}</span>
          </div>
          {isRunning && (
            <button onClick={handleStop}
              className="bg-red-500/20 hover:bg-red-500/30 text-red-300 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center space-x-1">
              <Square size={14} />
              <span>Stop</span>
            </button>
          )}
        </div>
        {status && (
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <p className="text-xs opacity-70">Strategy</p>
              <p className="font-medium">{status.strategy || status.current_strategy || '---'}</p>
            </div>
            <div>
              <p className="text-xs opacity-70">Invested</p>
              <p className="font-medium">₹{(status.invested || 0).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs opacity-70">P&L</p>
              <p className={`font-medium ${(status.pnl || 0) >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
                {(status.pnl || 0) >= 0 ? '+' : ''}₹{(status.pnl || 0).toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Start Bot (if not running) */}
      {!isRunning && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5 animate-fade-up">
          <h3 className="font-bold mb-3 flex items-center space-x-2">
            <Rocket size={18} className="text-amber-400" />
            <span>Launch Auto-Trader</span>
          </h3>
          
          {/* Strategy Selection */}
          <p className="text-xs text-slate-400 mb-2">Select Strategy</p>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {strategies.length > 0 ? strategies.map((s, i) => {
              const name = typeof s === 'string' ? s : s.name || s.strategy
              return (
                <button key={i} onClick={() => setSelectedStrategy(name)}
                  className={`p-3 rounded-lg text-sm text-left transition-all ${
                    selectedStrategy === name
                      ? 'bg-blue-600 text-white border border-blue-500'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:border-blue-500/50'
                  }`}>
                  <p className="font-medium">{name}</p>
                  {typeof s === 'object' && s.description && (
                    <p className="text-[10px] mt-0.5 opacity-70">{s.description}</p>
                  )}
                </button>
              )
            }) : (
              <>
                {['Conservative', 'Balanced', 'Aggressive', 'Gem Hunter'].map(s => (
                  <button key={s} onClick={() => setSelectedStrategy(s)}
                    className={`p-3 rounded-lg text-sm transition-all ${
                      selectedStrategy === s
                        ? 'bg-blue-600 text-white border border-blue-500'
                        : 'bg-slate-700 text-slate-300 border border-slate-600'
                    }`}>{s}</button>
                ))}
              </>
            )}
          </div>

          {/* Investment Amount */}
          <p className="text-xs text-slate-400 mb-2">Investment Amount</p>
          <div className="grid grid-cols-4 gap-2 mb-3">
            {['500', '1000', '5000', '10000'].map(a => (
              <button key={a} onClick={() => setInvestAmount(a)}
                className={`py-2 rounded-lg text-sm font-medium ${
                  investAmount === a ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
                }`}>₹{parseInt(a).toLocaleString()}</button>
            ))}
          </div>
          <input type="number" value={investAmount} onChange={e => setInvestAmount(e.target.value)}
            placeholder="Custom amount"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-4 focus:ring-2 focus:ring-blue-500 outline-none" />

          <button onClick={handleStart} disabled={starting || !selectedStrategy}
            className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white py-3.5 rounded-xl font-bold text-sm 
            disabled:opacity-40 hover:from-amber-400 hover:to-orange-400 transition-all active:scale-95 shadow-lg shadow-amber-500/20">
            {starting ? '🔄 Starting...' : '🚀 Start Auto-Trader'}
          </button>
        </div>
      )}

      {/* Compound Button */}
      {isRunning && (
        <button onClick={handleCompound}
          className="w-full bg-slate-800 border border-slate-700 py-3 rounded-xl mb-5 font-medium text-sm flex items-center justify-center space-x-2 hover:bg-slate-700">
          <Repeat size={16} className="text-blue-400" />
          <span>Compound Profits</span>
        </button>
      )}

      {/* Performance */}
      {performance && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5">
          <h3 className="font-bold mb-3 flex items-center space-x-2">
            <BarChart3 size={18} className="text-blue-400" />
            <span>Performance Report</span>
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-slate-700/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Total Trades</p>
              <p className="text-lg font-bold">{performance.total_trades || performance.trades || 0}</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Win Rate</p>
              <p className="text-lg font-bold text-emerald-400">{(performance.win_rate || performance.winRate || 0).toFixed(1)}%</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Total P&L</p>
              <p className={`text-lg font-bold ${(performance.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                ₹{(performance.total_pnl || performance.pnl || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">ROI</p>
              <p className={`text-lg font-bold ${(performance.roi || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {(performance.roi || 0).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bot Gem Picks */}
      {gems.length > 0 && (
        <div>
          <h3 className="font-bold mb-3 flex items-center space-x-2">
            <Target size={18} className="text-purple-400" />
            <span>Bot's Gem Picks</span>
          </h3>
          <div className="space-y-2">
            {gems.slice(0, 5).map((g, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">{g.symbol || g.name}</p>
                  <p className="text-xs text-slate-400">{g.reason || g.signal || ''}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">₹{(g.price || 0).toLocaleString()}</p>
                  <p className={`text-xs ${(g.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(g.change || 0) >= 0 ? '+' : ''}{(g.change || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default AutoTrader
