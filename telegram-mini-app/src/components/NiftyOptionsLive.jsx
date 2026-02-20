import React, { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw, TrendingUp, TrendingDown, Activity, Target,
  AlertTriangle, Layers, Zap, DollarSign, Eye, Shield,
  ChevronDown, ChevronUp, Filter, ArrowUpRight, ArrowDownLeft,
  Timer, Crosshair, Radio, Gauge
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  fetchNseLiveChain, fetchNseLiveSpot, fetchNseAtmOtm,
  fetchOiSuperSignal, fetchOiTraps, fetchOiBudgetPlays, fetchOiChange,
  fetchOtmAtmAnalysis, fetchRapidMomentum
} from '../services/api'
import { useApp } from '../context/AppContext'

const NiftyOptionsLive = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [chain, setChain] = useState(null)
  const [spot, setSpot] = useState(null)
  const [atmOtm, setAtmOtm] = useState(null)
  const [superSignal, setSuperSignal] = useState(null)
  const [traps, setTraps] = useState(null)
  const [budgetPlays, setBudgetPlays] = useState(null)
  const [oiChange, setOiChange] = useState(null)
  const [otmAnalysis, setOtmAnalysis] = useState(null)
  const [momentum, setMomentum] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('chain')
  const [selectedIndex, setSelectedIndex] = useState('NIFTY')
  const [maxBudget, setMaxBudget] = useState('30')
  const [loadingMomentum, setLoadingMomentum] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [chainRes, spotRes, signalRes] = await Promise.all([
        fetchNseLiveChain(selectedIndex).catch(() => null),
        fetchNseLiveSpot(selectedIndex).catch(() => null),
        fetchOiSuperSignal(selectedIndex).catch(() => null)
      ])
      setChain(chainRes?.data?.data || chainRes?.data || null)
      setSpot(spotRes?.data?.data || spotRes?.data || null)
      setSuperSignal(signalRes?.data?.data || signalRes?.data || null)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadTraps = async () => {
    hapticFeedback?.('impact')
    try {
      const [trapRes, oiRes] = await Promise.all([
        fetchOiTraps(selectedIndex).catch(() => null),
        fetchOiChange(selectedIndex).catch(() => null)
      ])
      setTraps(trapRes?.data?.data || trapRes?.data || null)
      setOiChange(oiRes?.data?.data || oiRes?.data || null)
      addNotification?.('Trap analysis loaded!', 'success')
    } catch (e) { console.error(e) }
  }

  const loadBudgetPlays = async () => {
    hapticFeedback?.('impact')
    try {
      const res = await fetchOiBudgetPlays(selectedIndex, parseFloat(maxBudget) || 30)
      setBudgetPlays(res?.data?.data || res?.data || null)
      addNotification?.('Budget plays found!', 'success')
    } catch (e) { console.error(e) }
  }

  const loadOtmAtm = async () => {
    hapticFeedback?.('impact')
    try {
      const [otmRes, atmRes] = await Promise.all([
        fetchOtmAtmAnalysis(selectedIndex).catch(() => null),
        fetchNseAtmOtm(selectedIndex).catch(() => null)
      ])
      setOtmAnalysis(otmRes?.data?.data || otmRes?.data || null)
      setAtmOtm(atmRes?.data?.data || atmRes?.data || null)
    } catch (e) { console.error(e) }
  }

  const loadMomentum = async () => {
    setLoadingMomentum(true)
    hapticFeedback?.('impact')
    try {
      const symMap = { NIFTY: '^NSEI', SENSEX: '^BSESN', BANKNIFTY: '^NSEBANK' }
      const res = await fetchRapidMomentum(symMap[selectedIndex] || '^NSEI')
      setMomentum(res?.data?.data || res?.data || null)
      addNotification?.('Rapid momentum signal ready!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoadingMomentum(false) }
  }

  useEffect(() => { load() }, [selectedIndex])

  // ⚡ Auto-refresh options chain every 10s
  useEffect(() => {
    const iv = setInterval(async () => {
      try {
        const [chainRes, spotRes, signalRes] = await Promise.all([
          fetchNseLiveChain(selectedIndex).catch(() => null),
          fetchNseLiveSpot(selectedIndex).catch(() => null),
          fetchOiSuperSignal(selectedIndex).catch(() => null)
        ])
        if (chainRes?.data) setChain(chainRes.data.data || chainRes.data)
        if (spotRes?.data) setSpot(spotRes.data.data || spotRes.data)
        if (signalRes?.data) setSuperSignal(signalRes.data.data || signalRes.data)
      } catch (e) { /* silent */ }
    }, 10000)
    return () => clearInterval(iv)
  }, [selectedIndex])

  const tabs = [
    { key: 'chain', label: 'Option Chain' },
    { key: 'traps', label: 'OI Traps' },
    { key: 'budget', label: 'Budget Plays' },
    { key: 'otm', label: 'OTM/ATM' },
    { key: 'momentum', label: 'Momentum' },
  ]

  const spotPrice = spot?.price || spot?.ltp || chain?.spot_price || 0
  const spotChange = spot?.change_pct || spot?.change || 0

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-3">
      <div className="h-8 w-48 bg-slate-800 rounded animate-pulse" />
      <div className="h-16 bg-slate-800 rounded-xl animate-pulse" />
      {[1,2,3,4].map(i => <div key={i} className="h-12 bg-slate-800 rounded-xl animate-pulse" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center space-x-2">
            <Layers size={20} className="text-orange-400" />
            <span>Live Options Chain</span>
          </h1>
          <p className="text-[10px] text-slate-400">Real-time NSE/BSE data with AI signals</p>
        </div>
        <button onClick={load} className="p-2 bg-slate-800 rounded-full"><RefreshCw size={16} className="text-orange-400" /></button>
      </div>

      {/* Index Selector */}
      <div className="flex space-x-2 mb-3">
        {['NIFTY', 'SENSEX', 'BANKNIFTY', 'FINNIFTY'].map(idx => (
          <button key={idx} onClick={() => setSelectedIndex(idx)}
            className={`flex-1 py-1.5 rounded-xl text-[10px] font-bold transition-all ${
              selectedIndex === idx ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{idx}</button>
        ))}
      </div>

      {/* Spot Price Card */}
      <div className={`bg-gradient-to-r ${spotChange >= 0 ? 'from-emerald-600/30 to-emerald-700/10' : 'from-red-600/30 to-red-700/10'} border ${spotChange >= 0 ? 'border-emerald-500/20' : 'border-red-500/20'} rounded-xl p-3 mb-3 flex items-center justify-between`}>
        <div>
          <p className="text-xs text-slate-400">{selectedIndex} Spot</p>
          <p className="text-xl font-bold">{spotPrice ? Number(spotPrice).toLocaleString() : '--'}</p>
        </div>
        <div className="text-right">
          <p className={`text-sm font-bold ${spotChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {spotChange >= 0 ? '+' : ''}{Number(spotChange).toFixed(2)}%
          </p>
          {superSignal?.direction && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
              (superSignal.direction || '').includes('BULL') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
            }`}>{superSignal.direction}</span>
          )}
        </div>
      </div>

      {/* Super Signal Mini */}
      {superSignal && (
        <div className="grid grid-cols-4 gap-1.5 mb-3 text-[10px]">
          {superSignal.pcr && <div className="bg-slate-800 rounded-lg p-1.5 text-center"><p className="text-slate-500">PCR</p><p className="font-bold">{typeof superSignal.pcr === 'number' ? superSignal.pcr.toFixed(2) : superSignal.pcr}</p></div>}
          {superSignal.max_pain && <div className="bg-slate-800 rounded-lg p-1.5 text-center"><p className="text-slate-500">Max Pain</p><p className="font-bold">{superSignal.max_pain}</p></div>}
          {superSignal.iv_rank !== undefined && <div className="bg-slate-800 rounded-lg p-1.5 text-center"><p className="text-slate-500">IV Rank</p><p className="font-bold">{typeof superSignal.iv_rank === 'number' ? superSignal.iv_rank.toFixed(0) : superSignal.iv_rank}</p></div>}
          {superSignal.confidence && <div className="bg-slate-800 rounded-lg p-1.5 text-center"><p className="text-slate-500">Conf.</p><p className="font-bold text-amber-400">{superSignal.confidence}%</p></div>}
        </div>
      )}

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-3 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => {
            setActiveTab(t.key)
            if (t.key === 'traps' && !traps) loadTraps()
            if (t.key === 'budget' && !budgetPlays) loadBudgetPlays()
            if (t.key === 'otm' && !otmAnalysis) loadOtmAtm()
            if (t.key === 'momentum' && !momentum) loadMomentum()
          }}
            className={`flex-1 shrink-0 py-1.5 rounded-lg text-[9px] font-medium whitespace-nowrap px-2 ${
              activeTab === t.key ? 'bg-orange-600 text-white' : 'text-slate-400'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* CHAIN TAB */}
      {activeTab === 'chain' && (
        <div className="space-y-2">
          {/* Chain Header */}
          <div className="grid grid-cols-7 gap-0.5 text-[8px] text-slate-500 font-bold text-center px-1">
            <span>OI</span><span>Vol</span><span>CE LTP</span><span className="text-orange-400">Strike</span><span>PE LTP</span><span>Vol</span><span>OI</span>
          </div>

          {/* Chain Rows */}
          {chain?.strikes ? (
            (Array.isArray(chain.strikes) ? chain.strikes : []).slice(0, 20).map((strike, i) => {
              const isATM = strike.is_atm || (spotPrice && Math.abs((strike.strike_price || strike.strike) - spotPrice) < 100)
              const ceOi = strike.ce_oi || strike.call_oi || 0
              const peOi = strike.pe_oi || strike.put_oi || 0
              const ceLtp = strike.ce_ltp || strike.call_ltp || 0
              const peLtp = strike.pe_ltp || strike.put_ltp || 0
              const ceVol = strike.ce_volume || strike.call_volume || 0
              const peVol = strike.pe_volume || strike.put_volume || 0
              const strikePrice = strike.strike_price || strike.strike || 0

              return (
                <div key={i} className={`grid grid-cols-7 gap-0.5 text-[9px] text-center py-1.5 px-1 rounded-lg ${
                  isATM ? 'bg-orange-500/10 border border-orange-500/20' : i % 2 === 0 ? 'bg-slate-800/50' : ''
                }`}>
                  <span className="text-emerald-400">{ceOi > 99999 ? (ceOi / 100000).toFixed(1) + 'L' : ceOi > 999 ? (ceOi / 1000).toFixed(1) + 'K' : ceOi || '--'}</span>
                  <span className="text-slate-400">{ceVol > 99999 ? (ceVol / 100000).toFixed(1) + 'L' : ceVol > 999 ? (ceVol / 1000).toFixed(1) + 'K' : ceVol || '--'}</span>
                  <span className={`font-bold ${(strike.ce_change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{ceLtp ? Number(ceLtp).toFixed(1) : '--'}</span>
                  <span className={`font-bold ${isATM ? 'text-orange-400' : 'text-slate-300'}`}>{strikePrice}</span>
                  <span className={`font-bold ${(strike.pe_change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{peLtp ? Number(peLtp).toFixed(1) : '--'}</span>
                  <span className="text-slate-400">{peVol > 99999 ? (peVol / 100000).toFixed(1) + 'L' : peVol > 999 ? (peVol / 1000).toFixed(1) + 'K' : peVol || '--'}</span>
                  <span className="text-red-400">{peOi > 99999 ? (peOi / 100000).toFixed(1) + 'L' : peOi > 999 ? (peOi / 1000).toFixed(1) + 'K' : peOi || '--'}</span>
                </div>
              )
            })
          ) : (
            <div className="text-center py-8 text-slate-500 text-sm">
              <Layers size={32} className="mx-auto mb-2 opacity-40" />
              <p>Loading option chain...</p>
              <p className="text-[10px] mt-1">Data from NSE/BSE live feed</p>
            </div>
          )}

          {/* OI Distribution Chart */}
          {chain?.strikes && Array.isArray(chain.strikes) && chain.strikes.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 mt-3">
              <h3 className="text-xs font-bold mb-2">OI Distribution</h3>
              <div className="h-28">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chain.strikes.slice(0, 15).map(s => ({
                    strike: s.strike_price || s.strike,
                    ce: s.ce_oi || s.call_oi || 0,
                    pe: -(s.pe_oi || s.put_oi || 0)
                  }))}>
                    <XAxis dataKey="strike" tick={{ fontSize: 7, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 7, fill: '#64748b' }} />
                    <Tooltip />
                    <Bar dataKey="ce" fill="#10b981" name="CE OI" />
                    <Bar dataKey="pe" fill="#ef4444" name="PE OI" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TRAPS TAB */}
      {activeTab === 'traps' && (
        <div className="space-y-3">
          <button onClick={loadTraps}
            className="w-full bg-gradient-to-r from-red-600 to-amber-600 rounded-xl p-3 flex items-center justify-between active:scale-[0.98]">
            <div className="flex items-center space-x-2">
              <AlertTriangle size={18} />
              <div className="text-left">
                <p className="text-xs font-bold">Detect OI Traps</p>
                <p className="text-[10px] opacity-80">Bull traps, Bear traps, Range traps, Max Pain</p>
              </div>
            </div>
            <ChevronDown size={16} />
          </button>

          {traps && (
            <div className="space-y-2">
              {(traps.traps || []).length > 0 ? traps.traps.map((trap, i) => (
                <div key={i} className={`rounded-xl p-3 border ${
                  (trap.type || '').toLowerCase().includes('bull') ? 'bg-red-500/10 border-red-500/20' :
                  (trap.type || '').toLowerCase().includes('bear') ? 'bg-emerald-500/10 border-emerald-500/20' :
                  'bg-amber-500/10 border-amber-500/20'
                }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs flex items-center space-x-1">
                      <AlertTriangle size={12} className="text-amber-400" />
                      <span>{trap.type || trap.name || 'Trap Detected'}</span>
                    </span>
                    {trap.severity && <span className={`text-[10px] px-1.5 rounded-full ${
                      trap.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>{trap.severity}</span>}
                  </div>
                  {trap.description && <p className="text-[10px] text-slate-300">{trap.description}</p>}
                  {trap.strike && <p className="text-[10px] text-slate-400">Strike: {trap.strike}</p>}
                  {trap.action && <p className="text-[10px] text-emerald-400 mt-0.5">Action: {trap.action}</p>}
                </div>
              )) : (
                <div className="text-center py-6 text-slate-500 text-sm">
                  <Shield size={24} className="mx-auto mb-1 opacity-40" />
                  <p>No active traps detected</p>
                </div>
              )}
            </div>
          )}

          {oiChange && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <h3 className="text-xs font-bold mb-2">OI Change Analysis</h3>
              {oiChange.summary && <p className="text-[10px] text-slate-300 mb-2">{typeof oiChange.summary === 'string' ? oiChange.summary : JSON.stringify(oiChange.summary)}</p>}
              <div className="grid grid-cols-2 gap-1 text-[10px]">
                {oiChange.ce_change !== undefined && <div className="bg-emerald-500/5 rounded p-1"><p className="text-slate-500">CE OI Change</p><p className="font-bold">{oiChange.ce_change}</p></div>}
                {oiChange.pe_change !== undefined && <div className="bg-red-500/5 rounded p-1"><p className="text-slate-500">PE OI Change</p><p className="font-bold">{oiChange.pe_change}</p></div>}
              </div>
            </div>
          )}
        </div>
      )}

      {/* BUDGET PLAYS TAB */}
      {activeTab === 'budget' && (
        <div className="space-y-3">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
            <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
              <DollarSign size={14} className="text-emerald-400" />
              <span>Budget Option Plays (Rs 2-30)</span>
            </h3>
            <div className="flex items-center space-x-2">
              <div className="flex-1 flex items-center bg-slate-700 rounded-xl px-3 py-2">
                <span className="text-slate-400 text-sm mr-1">Max Rs</span>
                <input type="number" value={maxBudget} onChange={e => setMaxBudget(e.target.value)}
                  placeholder="30" className="flex-1 bg-transparent text-sm outline-none w-12" />
              </div>
              <button onClick={loadBudgetPlays}
                className="bg-emerald-600 px-4 py-2 rounded-xl text-xs font-bold active:scale-95">Find Plays</button>
            </div>
          </div>

          {budgetPlays && (
            <div className="space-y-2">
              {(budgetPlays.plays || budgetPlays.options || []).length > 0 ? (budgetPlays.plays || budgetPlays.options || []).map((play, i) => (
                <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs">{play.name || play.description || 'Budget Play ' + (i+1)}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                      (play.type || '').toUpperCase() === 'CE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{play.type || '--'}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-1 text-[10px]">
                    <div><p className="text-slate-500">Strike</p><p>{play.strike || '--'}</p></div>
                    <div><p className="text-slate-500">LTP</p><p className="text-emerald-400 font-bold">Rs {play.ltp || play.premium || '--'}</p></div>
                    <div><p className="text-slate-500">OI</p><p>{play.oi || '--'}</p></div>
                    <div><p className="text-slate-500">Volume</p><p>{play.volume || '--'}</p></div>
                  </div>
                  {play.reason && <p className="text-[10px] text-slate-400 mt-1">{play.reason}</p>}
                  {play.risk_reward && <p className="text-[10px] text-amber-400 mt-0.5">R:R {play.risk_reward}</p>}
                </div>
              )) : (
                <div className="text-center py-6 text-slate-500 text-sm">
                  <DollarSign size={24} className="mx-auto mb-1 opacity-40" />
                  <p>No budget plays found within Rs {maxBudget}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* OTM/ATM TAB */}
      {activeTab === 'otm' && (
        <div className="space-y-3">
          <button onClick={loadOtmAtm}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-3 flex items-center justify-between active:scale-[0.98]">
            <div className="flex items-center space-x-2">
              <Crosshair size={18} />
              <div className="text-left">
                <p className="text-xs font-bold">OTM to ATM Analysis</p>
                <p className="text-[10px] opacity-80">Track options transitioning to ATM</p>
              </div>
            </div>
            <ChevronDown size={16} />
          </button>

          {atmOtm && (
            <div className="bg-slate-800 border border-blue-500/20 rounded-xl p-3">
              <h3 className="text-xs font-bold mb-2">ATM/OTM Strikes</h3>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="space-y-1">
                  <p className="text-emerald-400 font-bold text-[9px]">CALLS</p>
                  {(atmOtm.calls || []).slice(0, 5).map((c, i) => (
                    <div key={i} className="bg-emerald-500/5 rounded p-1 flex justify-between">
                      <span>{c.strike || c.strike_price}</span>
                      <span className="font-bold">Rs {c.ltp || c.premium || '--'}</span>
                    </div>
                  ))}
                </div>
                <div className="space-y-1">
                  <p className="text-red-400 font-bold text-[9px]">PUTS</p>
                  {(atmOtm.puts || []).slice(0, 5).map((p, i) => (
                    <div key={i} className="bg-red-500/5 rounded p-1 flex justify-between">
                      <span>{p.strike || p.strike_price}</span>
                      <span className="font-bold">Rs {p.ltp || p.premium || '--'}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {otmAnalysis && (
            <div className="space-y-2">
              {(otmAnalysis.transitions || otmAnalysis.otm_to_atm || []).slice(0, 6).map((t, i) => (
                <div key={i} className="bg-slate-800 border border-purple-500/20 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs">{t.strike || t.name || 'Strike ' + (i+1)}</span>
                    <span className={`text-[10px] px-1.5 rounded-full ${
                      (t.type || '').toUpperCase() === 'CE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{t.type || '--'}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-[10px]">
                    {t.probability !== undefined && <div><p className="text-slate-500">Prob</p><p className="text-amber-400 font-bold">{t.probability}%</p></div>}
                    {t.distance !== undefined && <div><p className="text-slate-500">Distance</p><p>{t.distance} pts</p></div>}
                    {t.premium !== undefined && <div><p className="text-slate-500">Premium</p><p>Rs {t.premium}</p></div>}
                  </div>
                  {t.reason && <p className="text-[10px] text-slate-400 mt-0.5">{t.reason}</p>}
                </div>
              ))}
              {(!otmAnalysis.transitions && !otmAnalysis.otm_to_atm) && (
                <div className="text-center py-6 text-slate-500 text-sm">
                  {typeof otmAnalysis === 'object' && Object.keys(otmAnalysis).length > 0 ? (
                    <div className="text-left bg-slate-800 rounded-xl p-3">
                      {Object.entries(otmAnalysis).slice(0, 8).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                          <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                          <span className="font-medium">{String(v).substring(0, 40)}</span>
                        </div>
                      ))}
                    </div>
                  ) : <p>Analyzing OTM to ATM transitions...</p>}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* MOMENTUM TAB */}
      {activeTab === 'momentum' && (
        <div className="space-y-3">
          <button onClick={loadMomentum} disabled={loadingMomentum}
            className="w-full bg-gradient-to-r from-amber-600 to-red-600 rounded-xl p-4 text-center active:scale-[0.98] disabled:opacity-50">
            <Zap size={24} className="mx-auto mb-1" />
            <p className="font-bold text-sm">{loadingMomentum ? 'Scanning momentum...' : 'Rapid 2-Min Momentum'}</p>
            <p className="text-[10px] opacity-70">RSI(7) + VWAP + Volume Spike + EMA crossovers</p>
          </button>

          {momentum && (
            <div className={`rounded-xl p-4 border-2 ${
              (momentum.signal || momentum.direction || '').toLowerCase().includes('buy') || (momentum.signal || '').toLowerCase().includes('bull')
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : (momentum.signal || momentum.direction || '').toLowerCase().includes('sell') || (momentum.signal || '').toLowerCase().includes('bear')
                ? 'bg-red-500/10 border-red-500/30' : 'bg-blue-500/10 border-blue-500/30'
            }`}>
              <div className="text-center mb-3">
                <p className="text-xl font-bold">{momentum.signal || momentum.direction || 'NEUTRAL'}</p>
                {momentum.strength && <p className="text-xs text-amber-400 mt-1">Strength: {momentum.strength}/10</p>}
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                {momentum.rsi && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">RSI (7)</p><p className="font-bold text-sm">{Number(momentum.rsi).toFixed(1)}</p></div>}
                {momentum.vwap_position && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">VWAP</p><p className="font-bold text-sm">{momentum.vwap_position}</p></div>}
                {momentum.ema_cross && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">EMA Cross</p><p className="font-bold text-sm">{momentum.ema_cross}</p></div>}
                {momentum.volume_surge !== undefined && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">Volume</p><p className={`font-bold text-sm ${momentum.volume_surge ? 'text-amber-400' : ''}`}>{momentum.volume_surge ? 'SURGE' : 'Normal'}</p></div>}
                {momentum.macd_signal && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">MACD</p><p className="font-bold text-sm">{momentum.macd_signal}</p></div>}
                {momentum.bb_position && <div className="bg-slate-800 rounded-lg p-2"><p className="text-slate-500">Bollinger</p><p className="font-bold text-sm">{momentum.bb_position}</p></div>}
              </div>
              {momentum.recommendation && <p className="text-xs text-slate-300 mt-2 text-center">{momentum.recommendation}</p>}
              {momentum.entry && <p className="text-[10px] text-emerald-400 mt-1">Entry: {momentum.entry}</p>}
              {momentum.target && <p className="text-[10px] text-blue-400">Target: {momentum.target}</p>}
              {momentum.stop_loss && <p className="text-[10px] text-red-400">SL: {momentum.stop_loss}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NiftyOptionsLive
