import React, { useState } from 'react'
import {
  FlaskConical, Play, BarChart3, TrendingUp, TrendingDown, Target,
  Clock, Shield, Zap, RefreshCw, Settings, ChevronRight
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, BarChart, Bar } from 'recharts'
import { runBacktest } from '../services/api'
import { useApp } from '../context/AppContext'

const BacktestBuilder = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [strategy, setStrategy] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [period, setPeriod] = useState('6m')

  const presets = [
    { label: '🔥 RSI Oversold Buy', strategy: 'Buy when RSI < 30, sell when RSI > 70 on BTC 4h' },
    { label: '📈 Golden Cross', strategy: 'Buy when 50 EMA crosses above 200 EMA on ETH daily' },
    { label: '🐋 Whale Follow', strategy: 'Buy when whale accumulation detected, sell after 20% profit on SOL' },
    { label: '📊 MACD Crossover', strategy: 'Buy on MACD bullish crossover with volume confirmation on NIFTY' },
    { label: '🎯 Mean Reversion', strategy: 'Buy when price touches lower Bollinger Band, sell at middle band on BANKNIFTY' },
    { label: '⚡ Breakout', strategy: 'Buy on 20-day high breakout with volume > 2x average on BTC daily' },
  ]

  const handleRun = async () => {
    if (!strategy.trim()) { addNotification('Enter a strategy to backtest', 'error'); return }
    setLoading(true)
    hapticFeedback('impact')
    try {
      const res = await runBacktest(strategy, period)
      setResult(res?.data?.data || res?.data || null)
      addNotification('✅ Backtest complete!', 'success')
      hapticFeedback('success')
    } catch (e) {
      addNotification('Backtest failed: ' + (e.response?.data?.detail || e.message), 'error')
      hapticFeedback('error')
    } finally { setLoading(false) }
  }

  const equityCurve = result?.equity_curve || result?.history || []
  const trades = result?.trades || []

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center">
              <FlaskConical size={16} />
            </div>
            <span>Backtest Builder</span>
          </h1>
          <p className="text-slate-400 text-sm">AI-powered strategy testing</p>
        </div>
      </div>

      {/* Strategy Input */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-4">
        <label className="text-xs text-slate-400 mb-2 block">Describe your strategy in plain English:</label>
        <textarea value={strategy} onChange={e => setStrategy(e.target.value)}
          placeholder="e.g., Buy BTC when RSI drops below 30 on the 4-hour chart, sell when it reaches 70. Use 10% of portfolio per trade with a 5% stop loss..."
          rows={3}
          className="w-full bg-slate-700 rounded-xl px-3 py-2.5 text-sm outline-none resize-none border border-slate-600 focus:border-emerald-500 placeholder-slate-500" />

        <div className="flex items-center space-x-2 mt-3">
          <div className="flex space-x-1 flex-1">
            {['1m', '3m', '6m', '1y', '2y'].map(p => (
              <button key={p} onClick={() => setPeriod(p)}
                className={`flex-1 py-1.5 rounded-lg text-[10px] font-bold transition-all ${
                  period === p ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-400'
                }`}>{p}</button>
            ))}
          </div>
          <button onClick={handleRun} disabled={loading}
            className="bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-2 rounded-xl font-bold text-sm
            disabled:opacity-50 active:scale-95 transition-all flex items-center space-x-1 shadow-lg shadow-emerald-500/20">
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            <span>{loading ? 'Running...' : 'Run'}</span>
          </button>
        </div>
      </div>

      {/* Preset Strategies */}
      {!result && (
        <div className="mb-4">
          <h3 className="text-sm font-bold mb-2 text-slate-300">Quick Presets</h3>
          <div className="grid grid-cols-2 gap-2">
            {presets.map((p, i) => (
              <button key={i} onClick={() => setStrategy(p.strategy)}
                className="bg-slate-800 border border-slate-700 rounded-xl p-3 text-left active:scale-95 transition-transform hover:border-emerald-500/30">
                <p className="text-xs">{p.label}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-2">
            <div className={`rounded-xl p-3 text-center border ${
              (result.total_return || 0) >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'
            }`}>
              <p className="text-[10px] text-slate-400">Total Return</p>
              <p className={`text-xl font-bold ${(result.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {(result.total_return || 0) >= 0 ? '+' : ''}{(result.total_return || 0).toFixed(2)}%
              </p>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-center">
              <p className="text-[10px] text-slate-400">Win Rate</p>
              <p className="text-xl font-bold text-blue-400">{(result.win_rate || 0).toFixed(1)}%</p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-2">
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <p className="text-[10px] text-slate-500">Trades</p>
              <p className="text-xs font-bold">{result.total_trades || 0}</p>
            </div>
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <p className="text-[10px] text-slate-500">Sharpe</p>
              <p className="text-xs font-bold text-purple-400">{(result.sharpe_ratio || 0).toFixed(2)}</p>
            </div>
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <p className="text-[10px] text-slate-500">Max DD</p>
              <p className="text-xs font-bold text-red-400">{(result.max_drawdown || 0).toFixed(1)}%</p>
            </div>
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <p className="text-[10px] text-slate-500">Profit F.</p>
              <p className="text-xs font-bold text-amber-400">{(result.profit_factor || 0).toFixed(2)}</p>
            </div>
          </div>

          {/* Equity Curve */}
          {equityCurve.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="text-sm font-bold mb-2">Equity Curve</h3>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={equityCurve}>
                    <defs>
                      <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 9, fill: '#64748b' }} />
                    <Tooltip />
                    <Area type="monotone" dataKey={equityCurve[0]?.equity !== undefined ? 'equity' : 'value'}
                      stroke="#10b981" fill="url(#eqGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Trade Log */}
          {trades.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="text-sm font-bold mb-2">Recent Trades ({trades.length})</h3>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {trades.slice(0, 20).map((t, i) => {
                  const isWin = (t.pnl || t.profit || 0) >= 0
                  return (
                    <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-700/50 last:border-0 text-xs">
                      <div className="flex items-center space-x-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${isWin ? 'bg-emerald-400' : 'bg-red-400'}`} />
                        <span className="font-medium">{t.side || t.type || 'Trade'}</span>
                        <span className="text-slate-500">{t.date || ''}</span>
                      </div>
                      <span className={isWin ? 'text-emerald-400' : 'text-red-400'}>
                        {isWin ? '+' : ''}{(t.pnl || t.profit || 0).toFixed(2)}%
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* AI Analysis */}
          {result.analysis && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
              <h3 className="text-sm font-bold mb-1 flex items-center space-x-2">
                <Zap size={14} className="text-emerald-400" />
                <span className="text-emerald-400">AI Analysis</span>
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">{result.analysis}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default BacktestBuilder
