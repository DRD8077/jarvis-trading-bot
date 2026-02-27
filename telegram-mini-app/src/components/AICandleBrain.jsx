import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  BarChart3, TrendingUp, TrendingDown, Globe, RefreshCw, Target, Zap,
  ArrowUpRight, ArrowDownRight, Activity, Eye, ChevronRight, Brain
} from 'lucide-react'
import { fetchCandleAnalysis, fetchTechnicalAnalysis } from '../services/api'
import { getApiBase } from '../services/apiBase'
import { useApp } from '../context/AppContext'

const TABS = [
  { id: 'global', label: 'Global', icon: Globe },
  { id: 'india', label: 'India', icon: Target },
  { id: 'us', label: 'US', icon: Activity },
  { id: 'asia', label: 'Asia', icon: Eye },
  { id: 'patterns', label: 'Patterns', icon: BarChart3 },
]

const SYMBOLS = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'TATAMOTORS', 'WIPRO']

const SignalBadge = ({ signal }) => {
  if (!signal) return null
  const s = signal.toUpperCase()
  const isUp = s.includes('BUY') || s.includes('BULL') || s.includes('UP')
  const isDown = s.includes('SELL') || s.includes('BEAR') || s.includes('DOWN') || s.includes('CRASH')
  const color = isUp ? 'bg-green-500/20 text-green-400 border-green-500/30' :
    isDown ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
  return <span className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border ${color}`}>{signal}</span>
}

const AICandleBrain = () => {
  const { hapticFeedback } = useApp()
  const [activeTab, setActiveTab] = useState('global')
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [globalData, setGlobalData] = useState(null)
  const [indiaData, setIndiaData] = useState(null)
  const [usData, setUsData] = useState(null)
  const [asiaData, setAsiaData] = useState(null)
  const [patterns, setPatterns] = useState([])
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY')
  const [symbolAnalysis, setSymbolAnalysis] = useState(null)
  const refreshRef = useRef(null)
  const base = getApiBase()

  const loadGlobalCandles = useCallback(async () => {
    setLoading(true)
    try {
      const [allRes, usRes, asiaRes] = await Promise.all([
        fetch(`${base}/api/miniapp/global-candle/all`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`${base}/api/miniapp/global-candle/us`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`${base}/api/miniapp/global-candle/asia`).then(r => r.ok ? r.json() : null).catch(() => null),
      ])
      setGlobalData(allRes?.data || allRes || null)
      setUsData(usRes?.data || usRes || null)
      setAsiaData(asiaRes?.data || asiaRes || null)
      setLastUpdate(new Date().toLocaleTimeString('en-IN'))
    } catch (e) {
      console.error('[CandleBrain] global load error:', e)
    } finally {
      setLoading(false)
    }
  }, [base])

  const loadIndiaCandles = useCallback(async () => {
    setLoading(true)
    try {
      const [predRes, candleRes] = await Promise.all([
        fetch(`${base}/api/miniapp/india/prediction`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetchCandleAnalysis('NIFTY').then(r => r.data).catch(() => null),
      ])
      setIndiaData({ prediction: predRes?.data || predRes, candles: candleRes?.data || candleRes })
      setLastUpdate(new Date().toLocaleTimeString('en-IN'))
    } catch (e) {
      console.error('[CandleBrain] India load error:', e)
    } finally {
      setLoading(false)
    }
  }, [base])

  const loadPatterns = useCallback(async (sym) => {
    setLoading(true)
    try {
      const [candleRes, techRes] = await Promise.all([
        fetchCandleAnalysis(sym).then(r => r.data).catch(() => null),
        fetchTechnicalAnalysis(sym).then(r => r.data).catch(() => null),
      ])
      const cd = candleRes?.data || candleRes || {}
      const td = techRes?.data || techRes || {}
      setSymbolAnalysis({ candles: cd, technical: td })

      // Fetch multi-timeframe patterns
      try {
        const mtfRes = await fetch(`${base}/api/miniapp/candle/multi-timeframe?symbol=${sym}`)
        if (mtfRes.ok) {
          const mtf = await mtfRes.json()
          setPatterns(mtf.data?.patterns || mtf.patterns || [])
        }
      } catch {}

      setLastUpdate(new Date().toLocaleTimeString('en-IN'))
    } catch (e) {
      console.error('[CandleBrain] patterns error:', e)
    } finally {
      setLoading(false)
    }
  }, [base])

  useEffect(() => {
    if (activeTab === 'global' || activeTab === 'us' || activeTab === 'asia') loadGlobalCandles()
    else if (activeTab === 'india') loadIndiaCandles()
    else if (activeTab === 'patterns') loadPatterns(selectedSymbol)
  }, [activeTab, selectedSymbol])

  // Auto-refresh every 10 seconds
  useEffect(() => {
    refreshRef.current = setInterval(() => {
      if (activeTab === 'global' || activeTab === 'us' || activeTab === 'asia') loadGlobalCandles()
      else if (activeTab === 'india') loadIndiaCandles()
      else loadPatterns(selectedSymbol)
    }, 10000)
    return () => clearInterval(refreshRef.current)
  }, [activeTab, selectedSymbol])

  const renderDataSection = (title, data) => {
    if (!data) return <p className="text-slate-500 text-sm text-center py-8">Loading {title}...</p>

    const items = Array.isArray(data) ? data :
      data.markets || data.indices || data.stocks || data.analysis || data.candles || []

    if (typeof data === 'object' && !Array.isArray(data) && !items.length) {
      // Render key-value pairs
      return (
        <div className="space-y-2">
          {Object.entries(data).filter(([k]) => !['error', 'status', 'timestamp'].includes(k)).map(([key, val]) => (
            <div key={key} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3">
              <p className="text-xs text-slate-400 capitalize mb-1">{key.replace(/_/g, ' ')}</p>
              {typeof val === 'object' && val !== null ? (
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(val).slice(0, 10).map(([k2, v2]) => (
                    <div key={k2}>
                      <span className="text-[10px] text-slate-500">{k2.replace(/_/g, ' ')}</span>
                      <p className="text-xs font-semibold text-white">
                        {typeof v2 === 'number' ? v2.toFixed(2) : String(v2)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm font-bold text-white">{typeof val === 'number' ? val.toFixed(2) : String(val)}</p>
              )}
            </div>
          ))}
        </div>
      )
    }

    if (Array.isArray(items) && items.length > 0) {
      return (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-white">{item.name || item.symbol || item.market || `#${i+1}`}</span>
                {item.signal && <SignalBadge signal={item.signal} />}
                {item.direction && <SignalBadge signal={item.direction} />}
              </div>
              <div className="grid grid-cols-3 gap-2 text-[10px]">
                {item.price && <div><span className="text-slate-500">Price</span><br /><span className="text-white font-semibold">{parseFloat(item.price).toLocaleString()}</span></div>}
                {item.change !== undefined && <div><span className="text-slate-500">Change</span><br /><span className={parseFloat(item.change) >= 0 ? 'text-green-400' : 'text-red-400'}>{parseFloat(item.change).toFixed(2)}%</span></div>}
                {item.confidence !== undefined && <div><span className="text-slate-500">Confidence</span><br /><span className="text-yellow-400 font-semibold">{item.confidence}%</span></div>}
                {item.pattern && <div className="col-span-3"><span className="text-slate-500">Pattern</span><br /><span className="text-purple-400 font-semibold">{item.pattern}</span></div>}
                {item.timeframe && <div><span className="text-slate-500">TF</span><br /><span className="text-cyan-400">{item.timeframe}</span></div>}
                {item.score !== undefined && <div><span className="text-slate-500">Score</span><br /><span className="text-yellow-400">{item.score}/100</span></div>}
              </div>
            </div>
          ))}
        </div>
      )
    }

    return <p className="text-slate-500 text-sm text-center py-8">No data available for {title}</p>
  }

  return (
    <div className="p-3 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Brain size={20} className="text-purple-400" />
            AI Candle Brain
          </h1>
          <p className="text-[10px] text-slate-500">
            Global candle analysis & pattern detection • {lastUpdate || 'Loading...'}
          </p>
        </div>
        <button onClick={() => {
          hapticFeedback?.('impact')
          if (activeTab === 'patterns') loadPatterns(selectedSymbol)
          else if (activeTab === 'india') loadIndiaCandles()
          else loadGlobalCandles()
        }} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={16} className={`text-blue-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 overflow-x-auto scrollbar-hide mb-4 pb-1">
        {TABS.map(t => {
          const Icon = t.icon
          return (
            <button key={t.id} onClick={() => { setActiveTab(t.id); hapticFeedback?.('impact') }}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all
                ${activeTab === t.id ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300' : 'bg-slate-800/50 text-slate-500'}`}>
              <Icon size={13} />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      {activeTab === 'global' && (
        <div>
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1"><Globe size={14} className="text-green-400" /> Global Markets Analysis</h2>
          {renderDataSection('Global Markets', globalData)}
        </div>
      )}

      {activeTab === 'india' && (
        <div>
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1"><Target size={14} className="text-orange-400" /> India Market Prediction</h2>
          {indiaData?.prediction && (
            <div className="bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border border-orange-500/20 rounded-xl p-3 mb-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">AI Verdict</span>
                {indiaData.prediction.direction && <SignalBadge signal={indiaData.prediction.direction} />}
                {indiaData.prediction.verdict && <SignalBadge signal={indiaData.prediction.verdict} />}
              </div>
              {indiaData.prediction.confidence && (
                <p className="text-sm font-bold text-white mt-1">Confidence: {indiaData.prediction.confidence}%</p>
              )}
              {indiaData.prediction.summary && (
                <p className="text-[10px] text-slate-400 mt-1">{indiaData.prediction.summary}</p>
              )}
            </div>
          )}
          {renderDataSection('India Candles', indiaData?.candles)}
        </div>
      )}

      {activeTab === 'us' && (
        <div>
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1"><Activity size={14} className="text-blue-400" /> US Markets Analysis</h2>
          {renderDataSection('US Markets', usData)}
        </div>
      )}

      {activeTab === 'asia' && (
        <div>
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1"><Eye size={14} className="text-cyan-400" /> Asian Markets Analysis</h2>
          {renderDataSection('Asian Markets', asiaData)}
        </div>
      )}

      {activeTab === 'patterns' && (
        <div>
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1"><BarChart3 size={14} className="text-purple-400" /> Candle Pattern Analysis</h2>
          
          {/* Symbol selector */}
          <div className="flex gap-1 overflow-x-auto scrollbar-hide mb-3 pb-1">
            {SYMBOLS.map(s => (
              <button key={s} onClick={() => { setSelectedSymbol(s); hapticFeedback?.('impact') }}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold whitespace-nowrap
                  ${selectedSymbol === s ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300' : 'bg-slate-800/50 text-slate-500'}`}>
                {s}
              </button>
            ))}
          </div>

          {symbolAnalysis && (
            <>
              {/* Technical Summary */}
              {symbolAnalysis.technical && (
                <div className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3 mb-3">
                  <p className="text-xs font-bold mb-2">Technical Analysis — {selectedSymbol}</p>
                  {renderDataSection('Technical', symbolAnalysis.technical)}
                </div>
              )}

              {/* Candle Patterns */}
              {symbolAnalysis.candles && (
                <div className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3 mb-3">
                  <p className="text-xs font-bold mb-2">Detected Patterns</p>
                  {renderDataSection('Candles', symbolAnalysis.candles)}
                </div>
              )}
            </>
          )}

          {/* Multi-Timeframe Patterns */}
          {patterns.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-bold">Multi-Timeframe Patterns</p>
              {patterns.map((p, i) => (
                <div key={i} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{p.pattern || p.name || `Pattern #${i+1}`}</span>
                    <SignalBadge signal={p.signal || p.direction || p.type || 'NEUTRAL'} />
                  </div>
                  {p.timeframe && <p className="text-[10px] text-slate-400 mt-0.5">Timeframe: {p.timeframe}</p>}
                  {p.confidence && <p className="text-[10px] text-yellow-400">Confidence: {p.confidence}%</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AICandleBrain
