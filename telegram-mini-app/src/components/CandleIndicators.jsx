import React, { useState, useEffect } from 'react'
import {
  RefreshCw, TrendingUp, TrendingDown, Activity, Target,
  BarChart3, Eye, Flame, Zap, ChevronDown, LineChart,
  Clock, Layers, ArrowUpRight, ArrowDownLeft, Gauge,
  BookOpen, Filter
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart as RechartsLine, Line } from 'recharts'
import {
  fetchCandlePatterns, fetchCandleAnalysis, fetchCandleIndicators
} from '../services/api'
import { useApp } from '../context/AppContext'

const CandleIndicators = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [patterns, setPatterns] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [indicators, setIndicators] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('patterns')
  const [symbol, setSymbol] = useState('^NSEI')
  const [displayName, setDisplayName] = useState('NIFTY')
  const [timeframe, setTimeframe] = useState('1d')

  const symbolMap = {
    'NIFTY': '^NSEI', 'SENSEX': '^BSESN', 'BANKNIFTY': '^NSEBANK',
    'RELIANCE': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'INFY': 'INFY.NS',
    'HDFC': 'HDFCBANK.NS', 'ITC': 'ITC.NS', 'SBIN': 'SBIN.NS',
    'BHARTIARTL': 'BHARTIARTL.NS', 'TATAMOTORS': 'TATAMOTORS.NS',
    'LT': 'LT.NS', 'WIPRO': 'WIPRO.NS', 'ICICIBANK': 'ICICIBANK.NS'
  }

  const loadPatterns = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchCandlePatterns(symbol, timeframe)
      setPatterns(res?.data?.data || res?.data || null)
      addNotification?.('Candle patterns scanned!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadAnalysis = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchCandleAnalysis(symbol)
      setAnalysis(res?.data?.data || res?.data || null)
      addNotification?.('Full candle analysis ready!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadIndicators = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchCandleIndicators(symbol, timeframe)
      setIndicators(res?.data?.data || res?.data || null)
      addNotification?.('Indicators loaded!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const selectSymbol = (name) => {
    setDisplayName(name)
    setSymbol(symbolMap[name] || name)
  }

  useEffect(() => {
    if (activeTab === 'patterns') loadPatterns()
    else if (activeTab === 'analysis') loadAnalysis()
    else if (activeTab === 'indicators') loadIndicators()
  }, [symbol, timeframe])

  const tabs = [
    { key: 'patterns', label: '43 Patterns' },
    { key: 'analysis', label: '12-Factor Score' },
    { key: 'indicators', label: '50+ Indicators' },
  ]

  const patternTypeColor = (type) => {
    if (!type) return 'text-slate-400'
    const t = type.toLowerCase()
    if (t.includes('bull') || t.includes('buy')) return 'text-emerald-400'
    if (t.includes('bear') || t.includes('sell')) return 'text-red-400'
    return 'text-amber-400'
  }

  const patternTypeBg = (type) => {
    if (!type) return 'bg-slate-500/10 border-slate-500/20'
    const t = type.toLowerCase()
    if (t.includes('bull') || t.includes('buy')) return 'bg-emerald-500/10 border-emerald-500/20'
    if (t.includes('bear') || t.includes('sell')) return 'bg-red-500/10 border-red-500/20'
    return 'bg-amber-500/10 border-amber-500/20'
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center space-x-2">
            <BarChart3 size={20} className="text-orange-400" />
            <span>Candle & Indicators</span>
          </h1>
          <p className="text-[10px] text-slate-400">43 patterns + 50 indicators + 12-factor scoring</p>
        </div>
        <button onClick={() => {
          if (activeTab === 'patterns') loadPatterns()
          else if (activeTab === 'analysis') loadAnalysis()
          else loadIndicators()
        }} className="p-2 bg-slate-800 rounded-full"><RefreshCw size={16} className="text-orange-400" /></button>
      </div>

      {/* Symbol Selector */}
      <div className="flex space-x-1.5 overflow-x-auto pb-2 mb-2">
        {Object.keys(symbolMap).map(s => (
          <button key={s} onClick={() => selectSymbol(s)}
            className={`shrink-0 px-2.5 py-1 rounded-full text-[9px] font-medium transition-all ${
              displayName === s ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{s}</button>
        ))}
      </div>

      {/* Timeframe Selector */}
      <div className="flex space-x-1.5 mb-3">
        {['5m', '15m', '1h', '1d', '1wk'].map(tf => (
          <button key={tf} onClick={() => setTimeframe(tf)}
            className={`flex-1 py-1 rounded-lg text-[10px] font-bold ${
              timeframe === tf ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{tf.toUpperCase()}</button>
        ))}
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-3">
        {tabs.map(t => (
          <button key={t.key} onClick={() => {
            setActiveTab(t.key)
            if (t.key === 'patterns') loadPatterns()
            else if (t.key === 'analysis') loadAnalysis()
            else loadIndicators()
          }}
            className={`flex-1 py-1.5 rounded-lg text-[9px] font-medium ${
              activeTab === t.key ? 'bg-orange-600 text-white' : 'text-slate-400'
            }`}>{t.label}</button>
        ))}
      </div>

      {loading && (
        <div className="text-center py-8">
          <Activity size={24} className="mx-auto text-orange-400 animate-spin" />
          <p className="text-sm text-slate-400 mt-2">Scanning {displayName}...</p>
        </div>
      )}

      {/* PATTERNS TAB */}
      {activeTab === 'patterns' && !loading && (
        <div className="space-y-2">
          {patterns ? (
            <>
              {/* Pattern Summary */}
              {patterns.summary && (
                <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/20 rounded-xl p-3 mb-2">
                  <p className="text-xs font-bold mb-1">Pattern Summary</p>
                  <p className="text-[10px] text-slate-300">{typeof patterns.summary === 'string' ? patterns.summary : JSON.stringify(patterns.summary)}</p>
                </div>
              )}
              {patterns.total_found !== undefined && (
                <p className="text-xs text-slate-400 mb-1">{patterns.total_found} patterns detected on {displayName} ({timeframe})</p>
              )}

              {/* Pattern List */}
              {(patterns.patterns || patterns.detected || []).length > 0 ? (
                (patterns.patterns || patterns.detected || []).map((p, i) => (
                  <div key={i} className={`rounded-xl p-3 border ${patternTypeBg(p.type || p.signal || p.sentiment)}`}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        {(p.type || p.signal || '').toLowerCase().includes('bull') ? <TrendingUp size={14} className="text-emerald-400" /> : <TrendingDown size={14} className="text-red-400" />}
                        <span className="font-bold text-xs">{p.name || p.pattern || 'Pattern'}</span>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${patternTypeColor(p.type || p.signal || p.sentiment)}`}>
                        {p.type || p.signal || p.sentiment || '--'}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 text-[10px]">
                      {p.reliability !== undefined && <div><p className="text-slate-500">Reliability</p><p className="font-bold">{p.reliability}%</p></div>}
                      {p.strength !== undefined && <div><p className="text-slate-500">Strength</p><p className="font-bold">{p.strength}/10</p></div>}
                      {p.timeframe && <div><p className="text-slate-500">TF</p><p className="font-bold">{p.timeframe}</p></div>}
                    </div>
                    {p.description && <p className="text-[10px] text-slate-400 mt-1">{p.description}</p>}
                    {p.action && <p className="text-[10px] text-amber-400 mt-0.5">Action: {p.action}</p>}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <BarChart3 size={32} className="mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No patterns detected on {timeframe}</p>
                  <p className="text-[10px]">Try a different timeframe</p>
                </div>
              )}

              {/* Raw data display if structure is different */}
              {!patterns.patterns && !patterns.detected && typeof patterns === 'object' && (
                <div className="bg-slate-800 rounded-xl p-3">
                  {Object.entries(patterns).filter(([k]) => k !== 'summary' && k !== 'total_found').slice(0, 15).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className={`font-medium ${patternTypeColor(typeof v === 'string' ? v : '')}`}>{typeof v === 'object' ? JSON.stringify(v).substring(0, 30) : String(v).substring(0, 30)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : !loading && (
            <div className="text-center py-12 text-slate-500">
              <BarChart3 size={48} className="mx-auto mb-3 opacity-20" />
              <p>Select a symbol and timeframe to scan</p>
            </div>
          )}
        </div>
      )}

      {/* ANALYSIS TAB */}
      {activeTab === 'analysis' && !loading && (
        <div className="space-y-3">
          {analysis ? (
            <>
              {/* Overall Score */}
              {analysis.score !== undefined && (
                <div className="bg-gradient-to-br from-blue-600/30 to-purple-600/30 border border-blue-500/20 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-400 mb-1">12-FACTOR COMPOSITE SCORE</p>
                  <p className={`text-4xl font-bold ${
                    analysis.score > 7 ? 'text-emerald-400' : analysis.score > 4 ? 'text-amber-400' : 'text-red-400'
                  }`}>{typeof analysis.score === 'number' ? analysis.score.toFixed(1) : analysis.score}/10</p>
                  {analysis.signal && <p className={`text-sm font-bold mt-1 ${
                    (analysis.signal || '').toLowerCase().includes('buy') ? 'text-emerald-400' : 'text-red-400'
                  }`}>{analysis.signal}</p>}
                </div>
              )}

              {/* Factor Breakdown */}
              {analysis.factors && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                    <Layers size={12} className="text-blue-400" /><span>Factor Breakdown</span>
                  </h3>
                  <div className="space-y-1.5">
                    {(Array.isArray(analysis.factors) ? analysis.factors : Object.entries(analysis.factors).map(([k, v]) => ({ name: k, ...( typeof v === 'object' ? v : { value: v }) }))).slice(0, 12).map((f, i) => {
                      const fName = f.name || f.factor || 'Factor ' + (i + 1)
                      const fValue = f.score || f.value || 0
                      const fMax = f.max || 10
                      const pct = typeof fValue === 'number' ? (fValue / fMax) * 100 : 50
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-[10px] mb-0.5">
                            <span className="text-slate-400 capitalize">{String(fName).replace(/_/g, ' ')}</span>
                            <span className="font-bold">{typeof fValue === 'number' ? fValue.toFixed(1) : fValue}</span>
                          </div>
                          <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${
                              pct > 70 ? 'bg-emerald-500' : pct > 40 ? 'bg-amber-500' : 'bg-red-500'
                            }`} style={{ width: `${Math.min(100, Math.max(5, pct))}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {analysis.recommendation && (
                <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-1">AI Recommendation</h3>
                  <p className="text-[10px] text-slate-300">{typeof analysis.recommendation === 'string' ? analysis.recommendation : JSON.stringify(analysis.recommendation)}</p>
                </div>
              )}

              {/* Generic data fallback */}
              {!analysis.score && !analysis.factors && typeof analysis === 'object' && (
                <div className="bg-slate-800 rounded-xl p-3 space-y-1">
                  {Object.entries(analysis).slice(0, 20).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{typeof v === 'object' ? JSON.stringify(v).substring(0, 40) : String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : !loading && (
            <div className="text-center py-12 text-slate-500">
              <BookOpen size={48} className="mx-auto mb-3 opacity-20" />
              <p>Select a symbol for 12-factor analysis</p>
            </div>
          )}
        </div>
      )}

      {/* INDICATORS TAB */}
      {activeTab === 'indicators' && !loading && (
        <div className="space-y-3">
          {indicators ? (
            <>
              {/* Quick Stats */}
              <div className="grid grid-cols-4 gap-1.5 text-[10px]">
                {indicators.rsi !== undefined && (
                  <div className={`rounded-lg p-2 text-center ${indicators.rsi > 70 ? 'bg-red-500/10' : indicators.rsi < 30 ? 'bg-emerald-500/10' : 'bg-slate-800'}`}>
                    <p className="text-slate-500">RSI</p>
                    <p className={`font-bold text-sm ${indicators.rsi > 70 ? 'text-red-400' : indicators.rsi < 30 ? 'text-emerald-400' : 'text-slate-300'}`}>{Number(indicators.rsi).toFixed(1)}</p>
                  </div>
                )}
                {indicators.macd_signal !== undefined && (
                  <div className="bg-slate-800 rounded-lg p-2 text-center">
                    <p className="text-slate-500">MACD</p>
                    <p className={`font-bold text-sm ${(indicators.macd_signal || '').toLowerCase().includes('bull') ? 'text-emerald-400' : 'text-red-400'}`}>{indicators.macd_signal || '--'}</p>
                  </div>
                )}
                {indicators.adx !== undefined && (
                  <div className="bg-slate-800 rounded-lg p-2 text-center">
                    <p className="text-slate-500">ADX</p>
                    <p className={`font-bold text-sm ${indicators.adx > 25 ? 'text-amber-400' : 'text-slate-300'}`}>{Number(indicators.adx).toFixed(1)}</p>
                  </div>
                )}
                {indicators.supertrend !== undefined && (
                  <div className={`rounded-lg p-2 text-center ${(indicators.supertrend || '').toLowerCase().includes('up') || (indicators.supertrend || '').toLowerCase().includes('buy') ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
                    <p className="text-slate-500">SuperT</p>
                    <p className="font-bold text-sm">{String(indicators.supertrend).substring(0, 6)}</p>
                  </div>
                )}
              </div>

              {/* All Indicators Grid */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                  <Activity size={12} className="text-blue-400" /><span>All Technical Indicators ({timeframe.toUpperCase()})</span>
                </h3>
                <div className="grid grid-cols-2 gap-1">
                  {(indicators.all_indicators || Object.entries(indicators)).length > 0 && (
                    (indicators.all_indicators
                      ? Object.entries(indicators.all_indicators)
                      : Object.entries(indicators).filter(([k]) => !['history', 'chart_data', 'all_indicators'].includes(k))
                    ).slice(0, 30).map(([key, val]) => {
                      const isBullish = typeof val === 'string' && (val.toLowerCase().includes('bull') || val.toLowerCase().includes('buy') || val.toLowerCase().includes('up') || val.toLowerCase().includes('above'))
                      const isBearish = typeof val === 'string' && (val.toLowerCase().includes('bear') || val.toLowerCase().includes('sell') || val.toLowerCase().includes('down') || val.toLowerCase().includes('below'))
                      return (
                        <div key={key} className="flex justify-between items-center bg-slate-700/30 rounded py-1 px-1.5 text-[9px]">
                          <span className="text-slate-400 capitalize truncate mr-1" style={{maxWidth: '55%'}}>{key.replace(/_/g, ' ')}</span>
                          <span className={`font-medium truncate ${isBullish ? 'text-emerald-400' : isBearish ? 'text-red-400' : 'text-slate-300'}`} style={{maxWidth: '45%'}}>
                            {typeof val === 'number' ? val.toFixed(2) : typeof val === 'object' ? JSON.stringify(val).substring(0, 15) : String(val).substring(0, 15)}
                          </span>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* Chart Data */}
              {(indicators.history || indicators.chart_data || []).length > 0 && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="text-xs font-bold mb-2">Price + RSI Chart</h3>
                  <div className="h-32">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={(indicators.history || indicators.chart_data || []).slice(-30)}>
                        <XAxis dataKey="date" tick={{ fontSize: 7, fill: '#64748b' }} />
                        <YAxis tick={{ fontSize: 7, fill: '#64748b' }} />
                        <Tooltip />
                        <Area type="monotone" dataKey="close" stroke="#3b82f6" fill="#3b82f620" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {indicators.signal && (
                <div className={`rounded-xl p-3 text-center border ${
                  (indicators.signal || '').toLowerCase().includes('buy') ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'
                }`}>
                  <p className="text-xs text-slate-400">Overall Signal</p>
                  <p className={`text-lg font-bold ${
                    (indicators.signal || '').toLowerCase().includes('buy') ? 'text-emerald-400' : 'text-red-400'
                  }`}>{indicators.signal}</p>
                </div>
              )}
            </>
          ) : !loading && (
            <div className="text-center py-12 text-slate-500">
              <LineChart size={48} className="mx-auto mb-3 opacity-20" />
              <p>Select a symbol for indicator analysis</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CandleIndicators
