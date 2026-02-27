import React, { useState, useEffect } from 'react'
import {
  Activity, TrendingUp, TrendingDown, Target, Shield, Zap,
  RefreshCw, Search, ChevronUp, ChevronDown, DollarSign, BarChart3,
  Layers, AlertTriangle, Calculator, Crosshair
} from 'lucide-react'
import {
  fetchOptionChain, fetchOptionStrategy, fetchBudgetPicks,
  fetchMorningPicks, fetchOptionIV
} from '../services/api'
import { useApp } from '../context/AppContext'

const OptionsChain = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [chain, setChain] = useState(null)
  const [activeTab, setActiveTab] = useState('chain')
  const [loading, setLoading] = useState(true)
  const [symbol, setSymbol] = useState('NIFTY')
  const [expiry, setExpiry] = useState('')
  const [budgetPicks, setBudgetPicks] = useState([])
  const [morningPicks, setMorningPicks] = useState([])
  const [strategies, setStrategies] = useState(null)
  const [ivData, setIvData] = useState(null)
  const [budget, setBudget] = useState('5000')

  const loadChain = async () => {
    setLoading(true)
    try {
      const res = await fetchOptionChain(symbol, expiry || undefined)
      const data = res?.data?.data || res?.data || {}
      setChain(data)
      if (data.expiry) setExpiry(data.expiry)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadBudgetPicks = async () => {
    try {
      const res = await fetchBudgetPicks(parseInt(budget) || 5000)
      setBudgetPicks(res?.data?.data || [])
    } catch (e) { console.error(e) }
  }

  const loadMorningPicks = async () => {
    try {
      const res = await fetchMorningPicks()
      setMorningPicks(res?.data?.data || [])
    } catch (e) { console.error(e) }
  }

  const loadStrategy = async () => {
    try {
      const res = await fetchOptionStrategy(symbol, 'auto')
      setStrategies(res?.data?.data || res?.data || null)
    } catch (e) { console.error(e) }
  }

  const loadIV = async () => {
    try {
      const res = await fetchOptionIV(symbol)
      setIvData(res?.data?.data || res?.data || null)
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadChain() }, [symbol])

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const iv = setInterval(() => { loadChain() }, 10000)
    return () => clearInterval(iv)
  }, [symbol])

  const strikes = chain?.strikes || chain?.options || []
  const spotPrice = chain?.spot_price || chain?.spot || 0
  const maxPain = chain?.max_pain || 0
  const totalCallOI = chain?.total_call_oi || 0
  const totalPutOI = chain?.total_put_oi || 0
  const pcr = totalCallOI > 0 ? (totalPutOI / totalCallOI).toFixed(2) : '--'

  const tabs = [
    { key: 'chain', icon: Layers, label: 'Chain' },
    { key: 'budget', icon: DollarSign, label: 'Budget' },
    { key: 'strategy', icon: Target, label: 'Strategy' },
    { key: 'morning', icon: Zap, label: 'Morning' },
  ]

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      <div className="skeleton h-8 w-48" />
      <div className="skeleton h-24 rounded-2xl" />
      {[1,2,3,4,5].map(i => <div key={i} className="skeleton h-12 rounded-xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
              <Activity size={16} />
            </div>
            <span>Options Chain</span>
          </h1>
          <p className="text-slate-400 text-sm">Nifty / BankNifty Options</p>
        </div>
        <button onClick={loadChain} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-orange-400" />
        </button>
      </div>

      {/* Symbol Toggle */}
      <div className="flex space-x-2 mb-4">
        {['NIFTY', 'BANKNIFTY', 'FINNIFTY'].map(s => (
          <button key={s} onClick={() => setSymbol(s)}
            className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
              symbol === s ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{s}</button>
        ))}
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <div className="bg-slate-800 rounded-lg p-2 text-center">
          <p className="text-[10px] text-slate-500">Spot</p>
          <p className="text-xs font-bold text-blue-400">{spotPrice.toLocaleString()}</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-2 text-center">
          <p className="text-[10px] text-slate-500">Max Pain</p>
          <p className="text-xs font-bold text-amber-400">{maxPain.toLocaleString()}</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-2 text-center">
          <p className="text-[10px] text-slate-500">PCR</p>
          <p className={`text-xs font-bold ${parseFloat(pcr) > 1 ? 'text-emerald-400' : 'text-red-400'}`}>{pcr}</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-2 text-center">
          <p className="text-[10px] text-slate-500">Expiry</p>
          <p className="text-xs font-bold text-purple-400">{expiry || '--'}</p>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-4">
        {tabs.map(t => (
          <button key={t.key} onClick={() => {
            setActiveTab(t.key)
            if (t.key === 'budget' && budgetPicks.length === 0) loadBudgetPicks()
            if (t.key === 'strategy' && !strategies) loadStrategy()
            if (t.key === 'morning' && morningPicks.length === 0) loadMorningPicks()
          }}
            className={`flex-1 py-2 rounded-lg text-[10px] font-medium flex items-center justify-center space-x-1 transition-all ${
              activeTab === t.key ? 'bg-orange-600 text-white' : 'text-slate-400'
            }`}>
            <t.icon size={12} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* CHAIN TAB */}
      {activeTab === 'chain' && (
        <div>
          {/* Header Row */}
          <div className="grid grid-cols-7 gap-1 px-2 py-2 text-[9px] text-slate-500 font-semibold">
            <span>OI</span><span>Vol</span><span>LTP</span>
            <span className="text-center font-bold text-slate-300">Strike</span>
            <span>LTP</span><span>Vol</span><span>OI</span>
          </div>
          <div className="space-y-0.5 max-h-[50vh] overflow-y-auto">
            {strikes.length === 0 ? (
              <p className="text-center text-slate-500 py-8 text-sm">No chain data available</p>
            ) : strikes.map((s, i) => {
              const isATM = s.atm || Math.abs((s.strike || 0) - spotPrice) < 100
              return (
                <div key={i} className={`grid grid-cols-7 gap-1 px-2 py-1.5 rounded-lg text-[10px] ${
                  isATM ? 'bg-orange-500/10 border border-orange-500/30' : 'bg-slate-800/50'
                }`}>
                  <span className="text-emerald-400 font-medium">{(s.call_oi || s.CE?.oi || 0).toLocaleString()}</span>
                  <span className="text-slate-400">{(s.call_volume || s.CE?.volume || 0).toLocaleString()}</span>
                  <span className="text-emerald-300 font-medium">{(s.call_ltp || s.CE?.ltp || 0).toFixed(1)}</span>
                  <span className={`text-center font-bold ${isATM ? 'text-orange-400' : 'text-slate-200'}`}>
                    {s.strike || s.strikePrice || 0}
                  </span>
                  <span className="text-red-300 font-medium">{(s.put_ltp || s.PE?.ltp || 0).toFixed(1)}</span>
                  <span className="text-slate-400">{(s.put_volume || s.PE?.volume || 0).toLocaleString()}</span>
                  <span className="text-red-400 font-medium">{(s.put_oi || s.PE?.oi || 0).toLocaleString()}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* BUDGET TAB */}
      {activeTab === 'budget' && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <input type="number" value={budget} onChange={e => setBudget(e.target.value)}
              placeholder="Budget in ₹"
              className="flex-1 bg-slate-800 rounded-xl px-3 py-2.5 text-sm outline-none border border-slate-700 focus:border-orange-500" />
            <button onClick={loadBudgetPicks}
              className="bg-orange-600 px-4 py-2.5 rounded-xl text-sm font-bold">Find</button>
          </div>
          {budgetPicks.length === 0 ? (
            <p className="text-center text-slate-500 py-8 text-sm">Enter budget to find affordable options</p>
          ) : budgetPicks.map((p, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <div className="flex items-center justify-between mb-1">
                <p className="font-bold text-sm">{p.symbol || p.name || 'Option'}</p>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  (p.type || '').toLowerCase() === 'ce' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                }`}>{p.type || 'CE'}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div><p className="text-slate-500">Strike</p><p>{p.strike || '--'}</p></div>
                <div><p className="text-slate-500">LTP</p><p>₹{p.ltp || p.price || '--'}</p></div>
                <div><p className="text-slate-500">Cost</p><p className="text-amber-400">₹{p.cost || p.total_cost || '--'}</p></div>
              </div>
              {p.roi && <p className="text-[10px] text-emerald-400 mt-1">Potential ROI: {p.roi}%</p>}
            </div>
          ))}
        </div>
      )}

      {/* STRATEGY TAB */}
      {activeTab === 'strategy' && (
        <div className="space-y-3">
          {!strategies ? (
            <div className="text-center py-12">
              <Target size={40} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500 text-sm">AI analyzing best strategies...</p>
            </div>
          ) : (
            <>
              <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 border border-orange-500/20 rounded-xl p-4">
                <h3 className="font-bold mb-1">{strategies.name || strategies.strategy || 'AI Strategy'}</h3>
                <p className="text-sm text-slate-300 mb-2">{strategies.description || strategies.reason || ''}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-slate-500">Max Profit:</span> <span className="text-emerald-400 font-bold">{strategies.max_profit || '--'}</span></div>
                  <div><span className="text-slate-500">Max Loss:</span> <span className="text-red-400 font-bold">{strategies.max_loss || '--'}</span></div>
                  <div><span className="text-slate-500">Breakeven:</span> <span className="text-blue-400">{strategies.breakeven || '--'}</span></div>
                  <div><span className="text-slate-500">Win Prob:</span> <span className="text-amber-400">{strategies.win_probability || '--'}%</span></div>
                </div>
              </div>
              {strategies.legs && strategies.legs.map((leg, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold">{leg.action} {leg.type} {leg.strike}</span>
                    <span className="text-slate-400">₹{leg.premium || '--'}</span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* MORNING TAB */}
      {activeTab === 'morning' && (
        <div className="space-y-3">
          {morningPicks.length === 0 ? (
            <div className="text-center py-12">
              <Zap size={40} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500 text-sm">Morning picks loading...</p>
            </div>
          ) : morningPicks.map((p, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-bold text-sm">{p.symbol || p.name || 'Pick'}</p>
                  <p className="text-[10px] text-slate-500">{p.strategy || p.type || '--'}</p>
                </div>
                {p.confidence && (
                  <div className="flex items-center space-x-1">
                    <Crosshair size={12} className="text-amber-400" />
                    <span className="text-xs font-bold text-amber-400">{p.confidence}%</span>
                  </div>
                )}
              </div>
              <p className="text-xs text-slate-300">{p.reason || p.analysis || ''}</p>
              {p.entry && (
                <div className="flex items-center space-x-3 mt-2 text-[10px]">
                  <span className="text-slate-500">Entry: {p.entry}</span>
                  <span className="text-emerald-400">TP: {p.target || '--'}</span>
                  <span className="text-red-400">SL: {p.stop_loss || '--'}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default OptionsChain
