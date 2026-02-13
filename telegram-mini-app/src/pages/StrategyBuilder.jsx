import React, { useState, useCallback } from 'react'
import { ArrowLeft, Puzzle, RefreshCw, TrendingUp, TrendingDown, Minimize2, Maximize2, Shield, Zap, Calculator, BarChart3, Target } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchStrategyRecommend, fetchStraddle, fetchStrangle, fetchBullSpread, fetchBearSpread, fetchIronCondor, fetchIvAnalysis, fetchGreeks } from '../services/api'

const strategies = [
  { id: 'recommend', label: 'AI Recommend', icon: Zap, color: 'cyan', desc: 'AI picks the best strategy for current market', fn: (sym) => fetchStrategyRecommend(sym) },
  { id: 'straddle', label: 'Straddle', icon: Maximize2, color: 'purple', desc: 'ATM CE + PE — profit from big moves', fn: (sym) => fetchStraddle(sym) },
  { id: 'strangle', label: 'Strangle', icon: Minimize2, color: 'blue', desc: 'OTM CE + PE — cheaper, wider breakevens', fn: (sym) => fetchStrangle(sym) },
  { id: 'bull', label: 'Bull Call Spread', icon: TrendingUp, color: 'green', desc: 'Buy lower CE, sell higher CE — limited risk bullish', fn: (sym) => fetchBullSpread(sym) },
  { id: 'bear', label: 'Bear Put Spread', icon: TrendingDown, color: 'red', desc: 'Buy higher PE, sell lower PE — limited risk bearish', fn: (sym) => fetchBearSpread(sym) },
  { id: 'condor', label: 'Iron Condor', icon: Shield, color: 'orange', desc: 'Sell OTM strangle, buy wider protection — rangebound', fn: (sym) => fetchIronCondor(sym) },
]

export default function StrategyBuilder() {
  const nav = useNavigate()
  const [symbol, setSymbol] = useState('NIFTY')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})
  const [active, setActive] = useState(null)
  const [ivData, setIvData] = useState(null)
  const [greeksData, setGreeksData] = useState(null)
  const [greeksInput, setGreeksInput] = useState({ spot: 25000, strike: 25000, days: 7, iv: 15, rate: 7, optType: 'CE' })
  const [showGreeks, setShowGreeks] = useState(false)

  const load = useCallback(async (key, fn) => {
    setLoading(p => ({ ...p, [key]: true }))
    try {
      const r = await fn()
      setData(p => ({ ...p, [key]: r.data?.data || r.data || {} }))
    } catch (e) { console.warn(key, e.message) }
    setLoading(p => ({ ...p, [key]: false }))
  }, [])

  const buildStrategy = (s) => {
    setActive(s.id)
    load(s.id, () => s.fn(symbol))
  }

  const loadIv = () => {
    setLoading(p => ({ ...p, iv: true }))
    fetchIvAnalysis(symbol)
      .then(r => setIvData(r.data?.data || r.data))
      .catch(e => console.warn(e))
      .finally(() => setLoading(p => ({ ...p, iv: false })))
  }

  const calcGreeks = () => {
    const { spot, strike, days, iv, rate, optType } = greeksInput
    setLoading(p => ({ ...p, greeks: true }))
    fetchGreeks(spot, strike, days, iv, rate, optType)
      .then(r => setGreeksData(r.data?.data || r.data))
      .catch(e => console.warn(e))
      .finally(() => setLoading(p => ({ ...p, greeks: false })))
  }

  const renderStrategy = (d) => {
    if (!d || typeof d !== 'object') return null
    // Handle OptionStrategy objects
    const legs = d.legs || d.strategy?.legs
    const maxProfit = d.max_profit || d.strategy?.max_profit
    const maxLoss = d.max_loss || d.strategy?.max_loss
    const breakevens = d.breakevens || d.breakeven || d.strategy?.breakevens

    return (
      <div className="space-y-3 mt-3">
        {/* Strategy Name */}
        {(d.name || d.strategy_name || d.strategy?.name) && (
          <div className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl p-3 border border-cyan-500/20">
            <h3 className="text-sm font-bold text-cyan-400">{d.name || d.strategy_name || d.strategy?.name}</h3>
            {d.reason && <p className="text-xs text-gray-400 mt-1">{d.reason}</p>}
            {d.strategy?.reason && <p className="text-xs text-gray-400 mt-1">{d.strategy.reason}</p>}
          </div>
        )}

        {/* Legs */}
        {legs && Array.isArray(legs) && (
          <div className="bg-gray-800/50 rounded-xl p-3 border border-gray-700/40">
            <h4 className="text-xs font-bold text-gray-400 mb-2">LEGS</h4>
            {legs.map((leg, i) => (
              <div key={i} className="flex justify-between items-center py-2 border-b border-gray-700/30 last:border-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded font-bold ${leg.action === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {leg.action || leg.type}
                  </span>
                  <span className="text-sm text-white">{leg.strike} {leg.option_type || leg.opt_type}</span>
                </div>
                <span className="text-sm font-mono text-gray-300">₹{leg.price || leg.premium || leg.ltp}</span>
              </div>
            ))}
          </div>
        )}

        {/* P&L Summary */}
        <div className="grid grid-cols-3 gap-2">
          {maxProfit !== undefined && (
            <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20 text-center">
              <p className="text-xs text-gray-500">Max Profit</p>
              <p className="text-sm font-bold text-green-400">₹{typeof maxProfit === 'number' ? maxProfit.toLocaleString() : maxProfit}</p>
            </div>
          )}
          {maxLoss !== undefined && (
            <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/20 text-center">
              <p className="text-xs text-gray-500">Max Loss</p>
              <p className="text-sm font-bold text-red-400">₹{typeof maxLoss === 'number' ? Math.abs(maxLoss).toLocaleString() : maxLoss}</p>
            </div>
          )}
          {breakevens && (
            <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/20 text-center">
              <p className="text-xs text-gray-500">Breakeven</p>
              <p className="text-sm font-bold text-yellow-400">
                {Array.isArray(breakevens) ? breakevens.map(b => b.toFixed(0)).join(' / ') : breakevens}
              </p>
            </div>
          )}
        </div>

        {/* Additional data fallback */}
        {!legs && <RenderObj obj={d} />}
      </div>
    )
  }

  const RenderObj = ({ obj }) => {
    if (!obj || typeof obj !== 'object') return null
    const entries = Object.entries(obj).filter(([k, v]) => v !== null && !['legs', 'status'].includes(k))
    return (
      <div className="bg-gray-800/50 rounded-xl p-3 border border-gray-700/40">
        <div className="grid grid-cols-2 gap-2">
          {entries.slice(0, 20).map(([k, v]) => (
            <div key={k} className="bg-gray-900/40 rounded-lg p-2">
              <p className="text-xs text-gray-500">{k.replace(/_/g, ' ')}</p>
              <p className="text-sm text-white font-mono truncate">
                {typeof v === 'object' ? JSON.stringify(v).slice(0, 50) : String(v)}
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
              <Puzzle size={18} className="text-purple-400" />
              Strategy Builder
            </h1>
            <p className="text-xs text-gray-500">Build & Analyze Options Strategies</p>
          </div>
        </div>
      </div>

      {/* Symbol */}
      <div className="flex gap-2 px-4 pt-3">
        {['NIFTY', 'BANKNIFTY', 'SENSEX'].map(s => (
          <button key={s} onClick={() => setSymbol(s)} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${symbol === s ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-gray-800/50 text-gray-500 border border-gray-700/30'}`}>
            {s}
          </button>
        ))}
      </div>

      <div className="px-4 py-3 space-y-3">
        {/* Strategy Cards */}
        <h2 className="text-sm font-bold text-purple-400 flex items-center gap-2"><Puzzle size={14} /> Pick a Strategy</h2>
        <div className="grid grid-cols-2 gap-2">
          {strategies.map(s => (
            <button
              key={s.id}
              onClick={() => buildStrategy(s)}
              className={`p-3 rounded-xl text-left border transition-all ${
                active === s.id ? `bg-${s.color}-500/15 border-${s.color}-500/30` : 'bg-gray-800/40 border-gray-700/30 hover:border-gray-600'
              }`}
            >
              <s.icon size={16} className={`text-${s.color}-400 mb-1`} />
              <p className="text-xs font-bold text-white">{s.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.desc}</p>
              {loading[s.id] && <div className="mt-2 w-full h-1 bg-gray-700 rounded-full overflow-hidden"><div className="h-full bg-cyan-500 rounded-full animate-pulse w-2/3" /></div>}
            </button>
          ))}
        </div>

        {/* Active Strategy Result */}
        {active && data[active] && !loading[active] && renderStrategy(data[active])}

        {/* IV Analysis */}
        <div className="mt-4">
          <button onClick={loadIv} className="w-full p-3 bg-yellow-500/10 rounded-xl border border-yellow-500/20 text-left hover:bg-yellow-500/15 transition-all">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-yellow-400" />
                <div>
                  <p className="text-xs font-bold text-yellow-400">IV Rank & Percentile</p>
                  <p className="text-xs text-gray-500">Is IV high or low? Timing for selling/buying options</p>
                </div>
              </div>
              {loading.iv ? <RefreshCw size={14} className="text-yellow-400 animate-spin" /> : <Target size={14} className="text-gray-500" />}
            </div>
          </button>
          {ivData && (
            <div className="bg-gray-800/50 rounded-xl p-3 border border-yellow-500/20 mt-2">
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ivData).filter(([_, v]) => v !== null).map(([k, v]) => (
                  <div key={k} className="bg-gray-900/40 rounded-lg p-2">
                    <p className="text-xs text-gray-500">{k.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-bold text-yellow-400">{typeof v === 'number' ? v.toFixed(2) : String(v)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Greeks Calculator */}
        <div className="mt-4">
          <button onClick={() => setShowGreeks(!showGreeks)} className="w-full p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-left hover:bg-emerald-500/15 transition-all">
            <div className="flex items-center gap-2">
              <Calculator size={16} className="text-emerald-400" />
              <div>
                <p className="text-xs font-bold text-emerald-400">Option Greeks Calculator</p>
                <p className="text-xs text-gray-500">Delta, Gamma, Theta, Vega, Rho — Black-Scholes</p>
              </div>
            </div>
          </button>

          {showGreeks && (
            <div className="bg-gray-800/50 rounded-xl p-4 border border-emerald-500/20 mt-2">
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[
                  { key: 'spot', label: 'Spot', placeholder: '25000' },
                  { key: 'strike', label: 'Strike', placeholder: '25000' },
                  { key: 'days', label: 'Days', placeholder: '7' },
                  { key: 'iv', label: 'IV %', placeholder: '15' },
                  { key: 'rate', label: 'Rate %', placeholder: '7' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="text-xs text-gray-500 block mb-1">{f.label}</label>
                    <input
                      type="number"
                      value={greeksInput[f.key]}
                      onChange={e => setGreeksInput(p => ({ ...p, [f.key]: parseFloat(e.target.value) || 0 }))}
                      placeholder={f.placeholder}
                      className="w-full bg-gray-900/60 border border-gray-700/50 rounded-lg px-2 py-1.5 text-sm text-white outline-none focus:border-emerald-500/50"
                    />
                  </div>
                ))}
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Type</label>
                  <div className="flex gap-1">
                    <button onClick={() => setGreeksInput(p => ({ ...p, optType: 'CE' }))}
                      className={`flex-1 py-1.5 rounded text-xs font-bold ${greeksInput.optType === 'CE' ? 'bg-green-500/20 text-green-400' : 'bg-gray-800 text-gray-500'}`}>CE</button>
                    <button onClick={() => setGreeksInput(p => ({ ...p, optType: 'PE' }))}
                      className={`flex-1 py-1.5 rounded text-xs font-bold ${greeksInput.optType === 'PE' ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-500'}`}>PE</button>
                  </div>
                </div>
              </div>
              <button onClick={calcGreeks} className="w-full py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg text-xs font-bold">
                {loading.greeks ? 'Calculating...' : 'CALCULATE GREEKS'}
              </button>

              {greeksData && (
                <div className="grid grid-cols-5 gap-1.5 mt-3">
                  {['delta', 'gamma', 'theta', 'vega', 'rho'].map(g => (
                    <div key={g} className="bg-gray-900/60 rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-500 uppercase">{g}</p>
                      <p className="text-sm font-bold text-emerald-400">
                        {greeksData[g] !== undefined ? (typeof greeksData[g] === 'number' ? greeksData[g].toFixed(4) : greeksData[g]) : '—'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
