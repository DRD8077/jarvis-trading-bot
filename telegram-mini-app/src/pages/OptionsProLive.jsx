import React, { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Crosshair, RefreshCw, TrendingUp, TrendingDown, Eye, BarChart3, Target, Activity, Shield, DollarSign, Layers, ChevronDown } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchStrikePrice, fetchNearbyOptions, fetchChainSummary, fetchFuturesDashboard, fetchFuturesBasis, fetchFuturesStraddle, fetchFuturesOiDist, fetchFuturesMaxPain, fetchCorrelationsScan, fetchCorrelationInsight } from '../services/api'

const tabs = [
  { id: 'strike', label: 'Strike Lookup', icon: Crosshair },
  { id: 'chain', label: 'Chain Summary', icon: Layers },
  { id: 'fno', label: 'F&O Brain', icon: BarChart3 },
  { id: 'correlations', label: 'Correlations', icon: Activity },
]

export default function OptionsProLive() {
  const nav = useNavigate()
  const [tab, setTab] = useState('strike')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})
  const [symbol, setSymbol] = useState('NIFTY')
  const [strike, setStrike] = useState('')
  const [optType, setOptType] = useState('CE')

  const load = useCallback(async (key, fn) => {
    setLoading(p => ({ ...p, [key]: true }))
    try {
      const r = await fn()
      setData(p => ({ ...p, [key]: r.data?.data || r.data || {} }))
    } catch (e) { console.warn(key, e.message) }
    setLoading(p => ({ ...p, [key]: false }))
  }, [])

  useEffect(() => {
    if (tab === 'chain') {
      load('chain', () => fetchChainSummary(symbol))
      load('nearby', () => fetchNearbyOptions(symbol, 10))
    } else if (tab === 'fno') {
      load('fno', () => fetchFuturesDashboard(symbol))
    } else if (tab === 'correlations') {
      load('corr', fetchCorrelationsScan)
    }
  }, [tab, symbol, load])

  // ⚡ Auto-refresh active tab every 10s
  useEffect(() => {
    const iv = setInterval(() => {
      if (tab === 'chain') {
        load('chain', () => fetchChainSummary(symbol))
      } else if (tab === 'fno') {
        load('fno', () => fetchFuturesDashboard(symbol))
      } else if (tab === 'correlations') {
        load('corr', fetchCorrelationsScan)
      }
    }, 10000)
    return () => clearInterval(iv)
  }, [tab, symbol, load])

  const lookupStrike = () => {
    if (!strike) return
    load('strike', () => fetchStrikePrice(symbol, parseInt(strike), optType))
  }

  const RenderKV = ({ obj, title, color = 'cyan' }) => {
    if (!obj || typeof obj !== 'object') return null
    const entries = Object.entries(obj).filter(([_, v]) => v !== null && v !== undefined && v !== '')
    if (!entries.length) return null
    return (
      <div className={`bg-gray-800/50 rounded-xl p-4 border border-${color}-500/20 mb-3`}>
        {title && <h3 className={`text-sm font-bold text-${color}-400 mb-3`}>{title}</h3>}
        <div className="grid grid-cols-2 gap-2">
          {entries.map(([k, v]) => (
            <div key={k} className="bg-gray-900/40 rounded-lg p-2">
              <p className="text-xs text-gray-500 mb-0.5">{k.replace(/_/g, ' ').toUpperCase()}</p>
              <p className={`text-sm font-mono ${typeof v === 'number' && v > 0 ? 'text-green-400' : typeof v === 'number' && v < 0 ? 'text-red-400' : 'text-white'}`}>
                {typeof v === 'object' ? JSON.stringify(v) : typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(v)}
              </p>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-950 to-black text-white pb-24">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur-md border-b border-gray-800/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => nav(-1)} className="p-1"><ArrowLeft size={20} className="text-gray-400" /></button>
          <div>
            <h1 className="text-lg font-bold flex items-center gap-2">
              <Crosshair size={18} className="text-red-400" />
              Options Pro Live
            </h1>
            <p className="text-xs text-gray-500">Strike Intelligence + F&O Brain + Correlations</p>
          </div>
        </div>
      </div>

      {/* Symbol Selector */}
      <div className="flex gap-2 px-4 pt-3">
        {['NIFTY', 'BANKNIFTY', 'SENSEX'].map(s => (
          <button key={s} onClick={() => setSymbol(s)} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${symbol === s ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-800/50 text-gray-500 border border-gray-700/30'}`}>
            {s}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-3 overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-800/50 text-gray-400 border border-gray-700/30'
            }`}>
            <t.icon size={14} />{t.label}
          </button>
        ))}
      </div>

      <div className="px-4 py-2">
        {/* Strike Lookup */}
        {tab === 'strike' && (
          <div>
            <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 rounded-xl p-4 border border-red-500/20 mb-4">
              <h3 className="text-sm font-bold text-red-400 mb-3">Strike Price Lookup</h3>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Strike</label>
                  <input type="number" value={strike} onChange={e => setStrike(e.target.value)}
                    placeholder="25000" className="w-full bg-gray-900/60 border border-gray-700/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-red-500/50" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Type</label>
                  <div className="flex gap-1">
                    <button onClick={() => setOptType('CE')} className={`flex-1 py-2 rounded-lg text-xs font-bold ${optType === 'CE' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-gray-800 text-gray-500'}`}>CE</button>
                    <button onClick={() => setOptType('PE')} className={`flex-1 py-2 rounded-lg text-xs font-bold ${optType === 'PE' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-800 text-gray-500'}`}>PE</button>
                  </div>
                </div>
                <div className="flex items-end">
                  <button onClick={lookupStrike} className="w-full py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg text-xs font-bold">
                    LOOKUP
                  </button>
                </div>
              </div>
            </div>

            {loading.strike ? <Loader /> : data.strike && (
              <div>
                {/* Main Strike Card */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/40 mb-3">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <span className="text-xs text-gray-500">{symbol} {strike} {optType}</span>
                      <h3 className="text-2xl font-bold text-white">₹{data.strike.ltp || data.strike.price || '—'}</h3>
                    </div>
                    {data.strike.recommendation && (
                      <span className={`text-xs px-3 py-1 rounded-full font-bold ${data.strike.recommendation?.toLowerCase().includes('buy') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {data.strike.recommendation}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {data.strike.iv && <Stat label="IV" value={`${data.strike.iv}%`} color="yellow" />}
                    {data.strike.oi && <Stat label="OI" value={data.strike.oi.toLocaleString()} color="cyan" />}
                    {data.strike.volume && <Stat label="Volume" value={data.strike.volume.toLocaleString()} color="purple" />}
                    {data.strike.moneyness && <Stat label="Moneyness" value={data.strike.moneyness} color="orange" />}
                    {data.strike.confidence && <Stat label="Confidence" value={`${data.strike.confidence}%`} color="green" />}
                    {data.strike.risk_reward && <Stat label="Risk:Reward" value={data.strike.risk_reward} color="red" />}
                  </div>
                </div>

                {/* Trade Levels */}
                {(data.strike.entry || data.strike.sl || data.strike.target1) && (
                  <div className="bg-gradient-to-r from-green-500/10 to-cyan-500/10 rounded-xl p-4 border border-green-500/20 mb-3">
                    <h4 className="text-xs font-bold text-green-400 mb-2">AI TRADE LEVELS</h4>
                    <div className="grid grid-cols-4 gap-2">
                      <Stat label="Entry" value={`₹${data.strike.entry}`} color="cyan" />
                      <Stat label="SL" value={`₹${data.strike.sl}`} color="red" />
                      <Stat label="Target 1" value={`₹${data.strike.target1}`} color="green" />
                      <Stat label="Target 2" value={`₹${data.strike.target2}`} color="emerald" />
                    </div>
                  </div>
                )}

                {/* PCR / Max Pain */}
                <div className="grid grid-cols-2 gap-2">
                  {data.strike.pcr && (
                    <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/40">
                      <p className="text-xs text-gray-500">PCR</p>
                      <p className="text-lg font-bold text-cyan-400">{data.strike.pcr}</p>
                    </div>
                  )}
                  {data.strike.max_pain && (
                    <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/40">
                      <p className="text-xs text-gray-500">Max Pain</p>
                      <p className="text-lg font-bold text-orange-400">{data.strike.max_pain}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chain Summary */}
        {tab === 'chain' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-cyan-400">Chain Summary — {symbol}</h2>
              <button onClick={() => { load('chain', () => fetchChainSummary(symbol)); load('nearby', () => fetchNearbyOptions(symbol, 10)) }}
                className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.chain ? 'animate-spin' : ''}`} />
              </button>
            </div>
            {loading.chain ? <Loader /> : (
              <>
                <RenderKV obj={data.chain} title="Option Chain Intelligence" color="cyan" />
                {data.nearby && <RenderKV obj={data.nearby} title="Nearby Strikes (ATM ± 10)" color="purple" />}
              </>
            )}
          </div>
        )}

        {/* F&O Brain */}
        {tab === 'fno' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-yellow-400">F&O Intelligence — {symbol}</h2>
              <button onClick={() => load('fno', () => fetchFuturesDashboard(symbol))} className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.fno ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {loading.fno ? <Loader /> : <RenderKV obj={data.fno?.dashboard || data.fno} title="Futures Dashboard" color="yellow" />}

            {/* Quick F&O Buttons */}
            <div className="grid grid-cols-2 gap-2 mt-3">
              {[
                { label: 'Futures Basis', fn: () => load('basis', () => fetchFuturesBasis(symbol)), key: 'basis', color: 'green' },
                { label: 'ATM Straddle', fn: () => load('straddle', () => fetchFuturesStraddle(symbol)), key: 'straddle', color: 'purple' },
                { label: 'OI Distribution', fn: () => load('oidist', () => fetchFuturesOiDist(symbol)), key: 'oidist', color: 'orange' },
                { label: 'Max Pain', fn: () => load('maxpain', () => fetchFuturesMaxPain(symbol)), key: 'maxpain', color: 'red' },
              ].map(b => (
                <button key={b.key} onClick={b.fn} className={`p-3 bg-${b.color}-500/10 rounded-lg border border-${b.color}-500/20 text-xs font-medium text-${b.color}-400 hover:bg-${b.color}-500/20 transition-all`}>
                  {loading[b.key] ? '...' : b.label}
                </button>
              ))}
            </div>

            {/* F&O Sub-results */}
            {data.basis && <RenderKV obj={data.basis} title="Futures Basis Analysis" color="green" />}
            {data.straddle && <RenderKV obj={data.straddle} title="ATM Straddle Premium" color="purple" />}
            {data.oidist && <RenderKV obj={data.oidist} title="OI Distribution" color="orange" />}
            {data.maxpain && <RenderKV obj={data.maxpain} title="Max Pain Analysis" color="red" />}
          </div>
        )}

        {/* Correlations */}
        {tab === 'correlations' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-emerald-400">Cross-Asset Correlations</h2>
              <button onClick={() => load('corr', fetchCorrelationsScan)} className="p-1.5 bg-gray-800 rounded-lg">
                <RefreshCw size={14} className={`text-gray-400 ${loading.corr ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="bg-emerald-500/10 rounded-xl p-3 border border-emerald-500/20 mb-4">
              <p className="text-xs text-gray-400">NIFTY vs S&P500, Gold, Crude, DXY, BTC — correlation matrix with divergence alerts</p>
            </div>
            {loading.corr ? <Loader /> : <RenderKV obj={data.corr} title="Correlation Matrix" color="emerald" />}

            {/* Individual insights */}
            <div className="grid grid-cols-3 gap-2 mt-3">
              {['NIFTY', 'BANKNIFTY', 'SENSEX'].map(s => (
                <button key={s} onClick={() => load(`corr_${s}`, () => fetchCorrelationInsight(s))}
                  className="p-2 bg-gray-800/50 rounded-lg border border-gray-700/30 text-xs text-gray-400 hover:text-emerald-400">
                  {s}
                </button>
              ))}
            </div>
            {['NIFTY', 'BANKNIFTY', 'SENSEX'].map(s => data[`corr_${s}`] && (
              <div key={s} className="mt-2">
                <RenderKV obj={data[`corr_${s}`]?.insight || data[`corr_${s}`]} title={`${s} Correlation`} color="emerald" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div className="bg-gray-900/40 rounded-lg p-2 text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-sm font-bold text-${color}-400`}>{value || '—'}</p>
    </div>
  )
}

function Loader() {
  return (
    <div className="flex flex-col items-center py-12">
      <div className="w-10 h-10 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
      <p className="text-xs text-gray-500 mt-3">Loading...</p>
    </div>
  )
}
