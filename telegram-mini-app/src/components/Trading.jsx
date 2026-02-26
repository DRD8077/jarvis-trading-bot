import React, { useState, useEffect, lazy, Suspense } from 'react'
import {
  TrendingUp, TrendingDown, BarChart3, Target, Zap, RefreshCw,
  ChevronDown, AlertTriangle, Eye, Clock
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { fetchSignals, fetchMarkets, fetchCandlePatternsOld as fetchCandlePatterns, fetchUltraPredict, sellPosition } from '../services/api'
import { useApp } from '../context/AppContext'

const TradingViewChart = lazy(() => import('../services/TradingViewChart'))

const Trading = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [activeTab, setActiveTab] = useState('signals')
  const [signals, setSignals] = useState([])
  const [markets, setMarkets] = useState([])
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSignal, setSelectedSignal] = useState(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [sigRes, mktRes, predRes] = await Promise.all([
        fetchSignals().catch(() => null),
        fetchMarkets().catch(() => null),
        fetchUltraPredict('BTC,ETH,SOL,NIFTY').catch(() => null)
      ])
      
      const sigData = sigRes?.data?.data || sigRes?.data?.signals || sigRes?.data || []
      setSignals(Array.isArray(sigData) ? sigData : [])
      
      const mktData = mktRes?.data?.data || mktRes?.data?.markets || mktRes?.data || []
      setMarkets(Array.isArray(mktData) ? mktData : 
        mktData?.crypto ? [...(mktData.crypto || []), ...(mktData.indian || [])] : [])
      
      const predData = predRes?.data?.data || predRes?.data?.predictions || predRes?.data || []
      setPredictions(Array.isArray(predData) ? predData : [])
    } catch (e) {
      console.error('Trading load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  // ⚡ Auto-refresh signals & markets every 15s
  useEffect(() => {
    const iv = setInterval(async () => {
      try {
        const [sigRes, mktRes] = await Promise.all([
          fetchSignals().catch(() => null),
          fetchMarkets().catch(() => null)
        ])
        const sigData = sigRes?.data?.data || sigRes?.data?.signals || sigRes?.data || []
        if (Array.isArray(sigData) && sigData.length) setSignals(sigData)
        const mktData = mktRes?.data?.data || mktRes?.data?.markets || mktRes?.data || []
        if (Array.isArray(mktData) && mktData.length) setMarkets(mktData)
        else if (mktData?.crypto) setMarkets([...(mktData.crypto || []), ...(mktData.indian || [])])
      } catch (e) { /* silent */ }
    }, 15000)
    return () => clearInterval(iv)
  }, [])

  // Listen for real-time signal updates from WebSocket
  useEffect(() => {
    const handleSignal = (e) => {
      try {
        const signal = e.detail
        if (!signal) return
        setSignals(prev => [signal, ...prev.slice(0, 19)])
        addNotification(`New AI Signal: ${signal.signal || signal.type} ${signal.symbol}`, 'info')
      } catch {}
    }
    window.addEventListener('jarvis-signal', handleSignal)
    return () => window.removeEventListener('jarvis-signal', handleSignal)
  }, [])

  const handleExecuteTrade = async (signal) => {
    hapticFeedback('impact')
    addNotification(`Executing ${signal.signal || signal.type} on ${signal.symbol}...`, 'info')
    try {
      const action = (signal.signal || signal.type || '').toUpperCase()
      if (action === 'SELL') {
        const res = await sellPosition(signal.symbol, signal.quantity || 1)
        addNotification(`SELL order executed for ${signal.symbol} ✅`, 'success')
      } else {
        // BUY — route through auto-trader
        const { startAutoTrader } = await import('../services/api')
        const res = await startAutoTrader(
          signal.strategy || 'ai_signal',
          signal.amount || signal.price || 100
        )
        addNotification(`BUY order placed for ${signal.symbol} at ${signal.entry || signal.price || 'market'} ✅`, 'success')
      }
      hapticFeedback('success')
    } catch (e) {
      addNotification('Trade failed: ' + (e?.response?.data?.detail || e.message), 'error')
      hapticFeedback('error')
    }
  }

  const tabs = [
    { id: 'signals', label: 'AI Signals', icon: Zap },
    { id: 'chart', label: 'Charts', icon: BarChart3 },
    { id: 'markets', label: 'Markets', icon: TrendingUp },
    { id: 'predict', label: 'Predictions', icon: Target },
  ]

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-12 w-full rounded-xl" />
        {[1,2,3].map(i => <div key={i} className="skeleton h-36 w-full rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold">Trading</h1>
          <p className="text-slate-400 text-sm">AI-powered signals & market data</p>
        </div>
        <button onClick={loadData} className="p-2 bg-slate-800 rounded-full hover:bg-slate-700">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-5">
        {tabs.map(t => {
          const Icon = t.icon
          return (
            <button key={t.id} onClick={() => { setActiveTab(t.id); hapticFeedback('impact') }}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === t.id ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'
              }`}>
              <Icon size={16} />
              <span>{t.label}</span>
            </button>
          )
        })}
      </div>

      {/* CHART TAB */}
      {activeTab === 'chart' && (
        <div className="space-y-3">
          <Suspense fallback={<div className="h-[400px] bg-slate-800 rounded-xl animate-pulse flex items-center justify-center text-slate-500 text-sm">Loading chart...</div>}>
            <TradingViewChart symbol="BTCUSDT" height={350} />
          </Suspense>
          <div className="grid grid-cols-2 gap-2">
            {['ETHUSDT', 'SOLUSDT'].map(sym => (
              <Suspense key={sym} fallback={<div className="h-[200px] bg-slate-800 rounded-xl animate-pulse" />}>
                <TradingViewChart symbol={sym} height={200} />
              </Suspense>
            ))}
          </div>
        </div>
      )}

      {/* SIGNALS TAB */}
      {activeTab === 'signals' && (
        <div className="space-y-3">
          {signals.length === 0 ? (
            <div className="text-center py-12">
              <Zap size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">No active signals right now</p>
              <p className="text-slate-500 text-sm">Check back soon — AI is scanning...</p>
            </div>
          ) : (
            signals.map((s, i) => {
              const isBuy = (s.signal || s.type || '').toUpperCase().includes('BUY')
              return (
                <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700 animate-fade-up"
                  style={{ animationDelay: `${i * 50}ms` }}>
                  {/* Signal Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        isBuy ? 'bg-emerald-500/20' : 'bg-red-500/20'
                      }`}>
                        {isBuy ? <TrendingUp size={22} className="text-emerald-400" /> : <TrendingDown size={22} className="text-red-400" />}
                      </div>
                      <div>
                        <p className="font-bold text-base">{s.symbol || s.name}</p>
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            isBuy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                          }`}>{s.signal || s.type}</span>
                          {s.timeframe && <span className="text-xs text-slate-500">{s.timeframe}</span>}
                        </div>
                      </div>
                    </div>
                    {/* Confidence Badge */}
                    <div className="text-right">
                      <p className="text-xs text-slate-400">Confidence</p>
                      <p className={`text-lg font-bold ${
                        (s.confidence || s.score || 0) > 70 ? 'text-emerald-400' :
                        (s.confidence || s.score || 0) > 50 ? 'text-yellow-400' : 'text-red-400'
                      }`}>{s.confidence || s.score || '--'}%</p>
                    </div>
                  </div>

                  {/* Price Grid */}
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="bg-slate-700/50 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-slate-400 uppercase">Entry</p>
                      <p className="text-sm font-bold">₹{(s.price || s.entry || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-emerald-500/10 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-emerald-400 uppercase">Target</p>
                      <p className="text-sm font-bold text-emerald-400">₹{(s.target || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-red-500/10 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-red-400 uppercase">Stop Loss</p>
                      <p className="text-sm font-bold text-red-400">₹{(s.stoploss || s.stop_loss || 0).toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Reason */}
                  {(s.reason || s.analysis) && (
                    <p className="text-xs text-slate-400 mb-3 line-clamp-2">{s.reason || s.analysis}</p>
                  )}

                  {/* Execute Button */}
                  <button onClick={() => handleExecuteTrade(s)}
                    className={`w-full py-3 rounded-xl font-bold text-sm transition-all active:scale-95 ${
                      isBuy 
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-white shadow-lg shadow-emerald-500/20' 
                        : 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 text-white shadow-lg shadow-red-500/20'
                    }`}>
                    {isBuy ? '🚀 BUY NOW' : '🔻 SELL NOW'}
                  </button>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* MARKETS TAB */}
      {activeTab === 'markets' && (
        <div className="space-y-2">
          {markets.length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">Loading markets...</p>
            </div>
          ) : (
            markets.slice(0, 30).map((m, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center text-xs font-bold">
                    {(m.symbol || m.name || '??').substring(0, 3)}
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{m.symbol || m.name}</p>
                    <p className="text-xs text-slate-400">{m.market || m.exchange || ''}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">₹{(m.price || m.last_price || m.ltp || 0).toLocaleString()}</p>
                  <p className={`text-xs font-medium ${
                    (m.change || m.change_percent || m.change_24h || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {(m.change || m.change_percent || m.change_24h || 0) >= 0 ? '+' : ''}
                    {(m.change || m.change_percent || m.change_24h || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* PREDICTIONS TAB */}
      {activeTab === 'predict' && (
        <div className="space-y-3">
          {predictions.length === 0 ? (
            <div className="text-center py-12">
              <Target size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">AI predictions are being generated...</p>
            </div>
          ) : (
            predictions.map((p, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-bold">{p.symbol || p.name}</p>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    (p.prediction || '').toLowerCase().includes('bull') || (p.direction || '').toLowerCase() === 'up'
                      ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {p.prediction || p.direction || p.signal}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-slate-400">Current</p>
                    <p className="text-sm font-semibold">₹{(p.current_price || p.price || 0).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Predicted</p>
                    <p className="text-sm font-semibold text-blue-400">₹{(p.predicted_price || p.target || 0).toLocaleString()}</p>
                  </div>
                </div>
                {p.confidence && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">AI Confidence</span>
                      <span className="font-medium">{p.confidence}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-1.5">
                      <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${p.confidence}%` }} />
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default Trading
