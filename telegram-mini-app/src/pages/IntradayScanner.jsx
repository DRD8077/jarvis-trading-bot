import React, { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Zap, TrendingUp, BarChart3, Activity, RefreshCw, Target, Volume2, Flame, Clock, ArrowUpRight, ArrowDownRight, AlertTriangle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchIntradayScan, fetchIntradayBreakouts, fetchIntradayVolume, fetchIntradayMomentum, fetchScreenerOversold, fetchScreenerOverbought, fetchScreenerVolumeSpike, fetchScreenerGapUps, fetchScreenerMomentum, fetchScreener52wHigh, fetchScreenerBullish, fetchScreenerRun } from '../services/api'

const tabs = [
  { id: 'scan', label: 'Full Scan', icon: Zap },
  { id: 'breakout', label: 'Breakouts', icon: TrendingUp },
  { id: 'volume', label: 'Volume', icon: BarChart3 },
  { id: 'momentum', label: 'Momentum', icon: Flame },
  { id: 'screener', label: 'Screener', icon: Target },
]

export default function IntradayScanner() {
  const nav = useNavigate()
  const [tab, setTab] = useState('scan')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})
  const [screenerType, setScreenerType] = useState('oversold')
  const [customQuery, setCustomQuery] = useState('')

  const screenerTypes = [
    { id: 'oversold', label: 'RSI Oversold', color: 'text-green-400', fn: fetchScreenerOversold },
    { id: 'overbought', label: 'RSI Overbought', color: 'text-red-400', fn: fetchScreenerOverbought },
    { id: 'volume', label: 'Volume Spike', color: 'text-yellow-400', fn: fetchScreenerVolumeSpike },
    { id: 'gaps', label: 'Gap Up', color: 'text-cyan-400', fn: fetchScreenerGapUps },
    { id: 'momentum', label: 'Top Momentum', color: 'text-purple-400', fn: fetchScreenerMomentum },
    { id: '52high', label: '52W High', color: 'text-orange-400', fn: fetchScreener52wHigh },
    { id: 'bullish', label: 'Strong Bull', color: 'text-emerald-400', fn: fetchScreenerBullish },
  ]

  const load = useCallback(async (key, fn) => {
    setLoading(p => ({ ...p, [key]: true }))
    try {
      const r = await fn()
      setData(p => ({ ...p, [key]: r.data?.data || r.data || {} }))
    } catch (e) {
      console.warn(key, e.message)
    }
    setLoading(p => ({ ...p, [key]: false }))
  }, [])

  useEffect(() => {
    if (tab === 'scan') load('scan', fetchIntradayScan)
    else if (tab === 'breakout') load('breakout', fetchIntradayBreakouts)
    else if (tab === 'volume') load('volume', fetchIntradayVolume)
    else if (tab === 'momentum') load('momentum', fetchIntradayMomentum)
  }, [tab, load])

  const loadScreener = (type) => {
    setScreenerType(type)
    const st = screenerTypes.find(s => s.id === type)
    if (st?.fn) load(`screener_${type}`, st.fn)
  }

  const runCustom = () => {
    if (customQuery.trim()) load('screener_custom', () => fetchScreenerRun(customQuery))
  }

  const renderStockCard = (stock, i) => {
    if (typeof stock === 'string') {
      return (
        <div key={i} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
          <p className="text-sm text-gray-300">{stock}</p>
        </div>
      )
    }
    const sym = stock.symbol || stock.name || stock.stock || `Stock ${i+1}`
    const price = stock.price || stock.ltp || stock.close || stock.current_price
    const change = stock.change || stock.change_pct || stock.pct_change || stock.returns
    const signal = stock.signal || stock.action || stock.recommendation || stock.type
    const score = stock.score || stock.strength || stock.confidence
    const vol = stock.volume || stock.vol
    const isUp = change > 0

    return (
      <div key={i} className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/40 hover:border-cyan-500/30 transition-all">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-white font-bold text-sm">{sym}</span>
            {signal && (
              <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${signal.toLowerCase().includes('buy') || signal.toLowerCase().includes('bull') ? 'bg-green-500/20 text-green-400' : signal.toLowerCase().includes('sell') || signal.toLowerCase().includes('bear') ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                {signal}
              </span>
            )}
          </div>
          {price && <span className="text-white font-mono text-sm">₹{parseFloat(price).toFixed(2)}</span>}
        </div>
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            {change !== undefined && (
              <span className={`flex items-center text-xs font-mono ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                {isUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {typeof change === 'number' ? `${change > 0 ? '+' : ''}${change.toFixed(2)}%` : change}
              </span>
            )}
            {vol && <span className="text-xs text-gray-500">Vol: {typeof vol === 'number' ? vol.toLocaleString() : vol}</span>}
          </div>
          {score !== undefined && (
            <div className="flex items-center gap-1">
              <div className="w-12 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full" style={{ width: `${Math.min(100, typeof score === 'number' ? score : parseFloat(score) || 50)}%` }} />
              </div>
              <span className="text-xs text-gray-400">{typeof score === 'number' ? score.toFixed(0) : score}</span>
            </div>
          )}
        </div>
        {stock.reason && <p className="text-xs text-gray-500 mt-1 truncate">{stock.reason}</p>}
        {stock.entry && <p className="text-xs text-cyan-400 mt-1">Entry: ₹{stock.entry} | SL: ₹{stock.sl} | T: ₹{stock.target}</p>}
      </div>
    )
  }

  const renderList = (items) => {
    if (!items) return <p className="text-gray-500 text-center py-8">No data yet — tap refresh</p>
    const arr = Array.isArray(items) ? items : typeof items === 'object' ? (items.stocks || items.results || items.data || items.scan || items.breakouts || items.volume_spikes || items.momentum || items.result || Object.values(items).flat().filter(Array.isArray).flat() || [items]) : [items]
    if (typeof arr === 'string') return <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50"><pre className="text-xs text-gray-300 whitespace-pre-wrap">{arr}</pre></div>
    if (!Array.isArray(arr) || arr.length === 0) {
      // Try to render object as key-value
      if (typeof items === 'object') {
        return Object.entries(items).map(([k, v]) => (
          <div key={k} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 mb-2">
            <span className="text-xs text-cyan-400 uppercase">{k.replace(/_/g, ' ')}</span>
            <pre className="text-xs text-gray-300 mt-1 whitespace-pre-wrap">{typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v)}</pre>
          </div>
        ))
      }
      return <p className="text-gray-500 text-center py-8">No results found</p>
    }
    return <div className="space-y-2">{arr.map((s, i) => renderStockCard(s, i))}</div>
  }

  const Tab = tabs.find(t => t.id === tab)

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-950 to-black text-white pb-24">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur-md border-b border-gray-800/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => nav(-1)} className="p-1"><ArrowLeft size={20} className="text-gray-400" /></button>
          <div>
            <h1 className="text-lg font-bold flex items-center gap-2">
              <Zap size={18} className="text-yellow-400" />
              Intraday Scanner
            </h1>
            <p className="text-xs text-gray-500">NIFTY 50 Real-Time Stock Scanner</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-3 overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-gray-800/50 text-gray-400 border border-gray-700/30'
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="px-4 py-2">
        {/* Full Scan */}
        {tab === 'scan' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-cyan-400 flex items-center gap-2"><Activity size={14} /> Complete Scan</h2>
              <button onClick={() => load('scan', fetchIntradayScan)} className="p-1.5 bg-gray-800 rounded-lg hover:bg-gray-700">
                <RefreshCw size={14} className={`text-gray-400 ${loading.scan ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl p-3 border border-cyan-500/20 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock size={14} className="text-cyan-400" />
                <span className="text-xs text-gray-400">Scans 50 NIFTY stocks for breakouts, volume spikes & momentum signals</span>
              </div>
              <p className="text-xs text-gray-500">Uses multi-thread parallel scanning with technical analysis</p>
            </div>
            {loading.scan ? (
              <div className="flex flex-col items-center py-12">
                <div className="w-12 h-12 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                <p className="text-xs text-gray-500 mt-3">Scanning 50 stocks...</p>
              </div>
            ) : renderList(data.scan)}
          </div>
        )}

        {/* Breakouts */}
        {tab === 'breakout' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-green-400 flex items-center gap-2"><TrendingUp size={14} /> Breakout Stocks</h2>
              <button onClick={() => load('breakout', fetchIntradayBreakouts)} className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.breakout ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="bg-green-500/10 rounded-xl p-3 border border-green-500/20 mb-4">
              <p className="text-xs text-gray-400">Stocks breaking above resistance / previous highs with strong volume confirmation</p>
            </div>
            {loading.breakout ? <Loader /> : renderList(data.breakout)}
          </div>
        )}

        {/* Volume */}
        {tab === 'volume' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-yellow-400 flex items-center gap-2"><BarChart3 size={14} /> Volume Surges</h2>
              <button onClick={() => load('volume', fetchIntradayVolume)} className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.volume ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="bg-yellow-500/10 rounded-xl p-3 border border-yellow-500/20 mb-4">
              <p className="text-xs text-gray-400">Stocks with unusual volume (2x+ average) — smart money activity detected</p>
            </div>
            {loading.volume ? <Loader /> : renderList(data.volume)}
          </div>
        )}

        {/* Momentum */}
        {tab === 'momentum' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-purple-400 flex items-center gap-2"><Flame size={14} /> Momentum Leaders</h2>
              <button onClick={() => load('momentum', fetchIntradayMomentum)} className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.momentum ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="bg-purple-500/10 rounded-xl p-3 border border-purple-500/20 mb-4">
              <p className="text-xs text-gray-400">Strongest momentum stocks based on RSI + MACD + ADX + Price Action</p>
            </div>
            {loading.momentum ? <Loader /> : renderList(data.momentum)}
          </div>
        )}

        {/* Screener */}
        {tab === 'screener' && (
          <div>
            <h2 className="text-sm font-bold text-orange-400 flex items-center gap-2 mb-3"><Target size={14} /> Stock Screener Pro</h2>
            
            {/* Custom Query */}
            <div className="bg-gray-800/50 rounded-xl p-3 border border-gray-700/40 mb-4">
              <p className="text-xs text-gray-400 mb-2">Natural Language Query</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customQuery}
                  onChange={e => setCustomQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && runCustom()}
                  placeholder="e.g. RSI below 30 and volume > 2x"
                  className="flex-1 bg-gray-900/50 border border-gray-700/50 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-cyan-500/50 outline-none"
                />
                <button onClick={runCustom} className="px-3 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-500/30">
                  Scan
                </button>
              </div>
            </div>

            {/* Pre-built Screeners */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              {screenerTypes.map(s => (
                <button
                  key={s.id}
                  onClick={() => loadScreener(s.id)}
                  className={`p-2.5 rounded-lg text-xs font-medium border transition-all ${
                    screenerType === s.id ? 'bg-gray-700/60 border-cyan-500/40 text-white' : 'bg-gray-800/40 border-gray-700/30 text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <span className={s.color}>{s.label}</span>
                </button>
              ))}
            </div>

            {/* Screener Results */}
            {loading[`screener_${screenerType}`] || loading.screener_custom ? (
              <Loader />
            ) : (
              renderList(data[`screener_${screenerType}`] || data.screener_custom)
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Loader() {
  return (
    <div className="flex flex-col items-center py-12">
      <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
      <p className="text-xs text-gray-500 mt-3">Loading...</p>
    </div>
  )
}
