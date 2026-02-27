import React, { useState, useEffect } from 'react'
import {
  BarChart3, TrendingUp, TrendingDown, Activity, RefreshCw,
  Globe, Layers, Target, Shield, Zap, ArrowUpRight, ArrowDownLeft,
  Eye, AlertTriangle, DollarSign, Percent, Building2, LineChart,
  Flame, BookOpen, PieChart, Users, Clock, Brain, Crosshair,
  Radio, Timer, ChevronRight, Gauge, Wifi
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import {
  fetchIndiaCombinedDashboard,
  fetchIndiaSuperAnalysis, fetchNiftySuperAnalysis, fetchIndiaSnapshot,
  fetchPowerPredict, fetchMarketRegime, fetchIndia2minSignal,
  fetchOiSuperSignal, fetchGlobalIndiaImpact, fetchIndiaHolidays,
  fetchInvestmentCalc, fetchAiMarketVerdict, fetchAiDashboard
} from '../services/api'
import { useApp } from '../context/AppContext'

const IndianStocks = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [dashboard, setDashboard] = useState(null)
  const [fiiDii, setFiiDii] = useState(null)
  const [vix, setVix] = useState(null)
  const [pcr, setPcr] = useState(null)
  const [pivots, setPivots] = useState(null)
  const [gift, setGift] = useState(null)
  const [sectors, setSectors] = useState([])
  const [oi, setOi] = useState(null)
  const [marketStatus, setMarketStatus] = useState(null)
  const [regime, setRegime] = useState(null)
  const [powerPred, setPowerPred] = useState(null)
  const [signal2min, setSignal2min] = useState(null)
  const [oiSuper, setOiSuper] = useState(null)
  const [globalImpact, setGlobalImpact] = useState(null)
  const [snapshot, setSnapshot] = useState(null)
  const [investCalc, setInvestCalc] = useState(null)
  const [superAnalysis, setSuperAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [analysisSymbol, setAnalysisSymbol] = useState('RELIANCE')
  const [investAmount, setInvestAmount] = useState('2000')
  const [selectedIndex, setSelectedIndex] = useState('NIFTY')
  const [loadingPower, setLoadingPower] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [aiVerdict, setAiVerdict] = useState(null)
  const [loadingVerdict, setLoadingVerdict] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      // ONE single API call instead of 10 separate calls = 10x faster!
      const res = await fetchIndiaCombinedDashboard(selectedIndex).catch(() => null)
      const d = res?.data?.data || {}
      setDashboard(d.dashboard || null)
      setFiiDii(d.fii_dii || null)
      setVix(d.vix || null)
      setPcr(d.pcr || null)
      setPivots(d.pivots || null)
      setGift(d.gift || null)
      setSectors(d.sectors || [])
      setOi(d.oi || null)
      setMarketStatus(d.market_status || null)
      setSnapshot(d.snapshot || null)
      // JARVIS voice — announce Indian market summary
      try {
        const nifty = d.dashboard?.nifty50 || d.snapshot?.nifty
        const change = nifty?.change || nifty?.pChange || 0
        window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: `Sir, Indian market update. ${nifty ? `Nifty ${change >= 0 ? 'upar' : 'neeche'} hai, ${Math.abs(change).toFixed(1)} points ${change >= 0 ? 'gain' : 'loss'}.` : 'Market data loaded.'} ${d.fii_dii ? (d.fii_dii.fii_net > 0 ? 'FII buying kar rahe hain, positive signal!' : 'FII selling kar rahe hain, cautious rahiye.') : ''}`, priority: 'low' } }))
      } catch {}
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadPowerPrediction = async () => {
    setLoadingPower(true)
    hapticFeedback?.('impact')
    try {
      const [predRes, regRes, oiRes, globalRes] = await Promise.all([
        fetchPowerPredict(selectedIndex).catch(() => null),
        fetchMarketRegime().catch(() => null),
        fetchOiSuperSignal(selectedIndex).catch(() => null),
        fetchGlobalIndiaImpact().catch(() => null)
      ])
      setPowerPred(predRes?.data?.data || predRes?.data || null)
      setRegime(regRes?.data?.data || regRes?.data || null)
      setOiSuper(oiRes?.data?.data || oiRes?.data || null)
      setGlobalImpact(globalRes?.data?.data || globalRes?.data || null)
      addNotification?.('AI Prediction ready!', 'success')
      hapticFeedback?.('success')
    } catch (e) { console.error(e) }
    finally { setLoadingPower(false) }
  }

  const load2minSignal = async () => {
    hapticFeedback?.('impact')
    try {
      const symMap = { NIFTY: '^NSEI', SENSEX: '^BSESN', BANKNIFTY: '^NSEBANK' }
      const res = await fetchIndia2minSignal(symMap[selectedIndex] || '^NSEI', selectedIndex)
      setSignal2min(res?.data?.data || res?.data || null)
      addNotification?.('2-min signal updated!', 'success')
    } catch (e) { console.error(e) }
  }

  const loadInvestCalc = async () => {
    hapticFeedback?.('impact')
    try {
      const symMap = { NIFTY: '^NSEI', SENSEX: '^BSESN', BANKNIFTY: '^NSEBANK' }
      const res = await fetchInvestmentCalc(symMap[selectedIndex] || '^NSEI', selectedIndex, parseFloat(investAmount) || 2000)
      setInvestCalc(res?.data?.data || res?.data || null)
    } catch (e) { console.error(e) }
  }

  const loadSuperAnalysis = async (sym) => {
    setAnalysisSymbol(sym)
    setLoadingAnalysis(true)
    try {
      const res = await fetchIndiaSuperAnalysis(sym, parseFloat(investAmount) || 2000)
      setSuperAnalysis(res?.data?.data || res?.data || null)
      addNotification?.('Analysis ready for ' + sym, 'success')
      hapticFeedback?.('success')
    } catch (e) { console.error(e) }
    finally { setLoadingAnalysis(false) }
  }

  useEffect(() => { load() }, [selectedIndex])

  // ⚡ Auto-refresh every 10s for live market data
  useEffect(() => {
    const iv = setInterval(() => {
      // Silent refresh — no loading spinner
      (async () => {
        try {
          const res = await fetchIndiaCombinedDashboard(selectedIndex).catch(() => null)
          const d = res?.data?.data || {}
          if (d.dashboard) setDashboard(d.dashboard)
          if (d.fii_dii) setFiiDii(d.fii_dii)
          if (d.vix) setVix(d.vix)
          if (d.pcr) setPcr(d.pcr)
          if (d.pivots) setPivots(d.pivots)
          if (d.gift) setGift(d.gift)
          if (d.sectors?.length) setSectors(d.sectors)
          if (d.oi) setOi(d.oi)
          if (d.market_status) setMarketStatus(d.market_status)
          if (d.snapshot) setSnapshot(d.snapshot)
        } catch (e) { /* silent */ }
      })()
    }, 10000)
    return () => clearInterval(iv)
  }, [selectedIndex])

  const isOpen = marketStatus?.is_open || false
  const niftyValue = snapshot?.nifty?.price || dashboard?.nifty || 0
  const niftyChange = snapshot?.nifty?.change_pct || dashboard?.nifty_change || 0
  const sensexValue = snapshot?.sensex?.price || dashboard?.sensex || 0
  const sensexChange = snapshot?.sensex?.change_pct || dashboard?.sensex_change || 0
  const bankNifty = dashboard?.banknifty || 0
  const bankNiftyChange = dashboard?.banknifty_change || 0
  const vixValue = vix?.current || vix?.value || vix?.vix || 0
  const pcrValue = pcr?.pcr || pcr?.value || 0
  const giftValue = gift?.price || gift?.value || gift?.gift_nifty || 0
  const giftChange = gift?.change || gift?.gap || 0

  const tabs = [
    { key: 'dashboard', label: 'Live' },
    { key: 'predict', label: 'AI Predict' },
    { key: 'fii', label: 'FII/DII' },
    { key: 'sectors', label: 'Sectors' },
    { key: 'invest', label: 'Invest' },
    { key: 'analysis', label: 'Stock' },
  ]

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-3">
      <div className="skeleton h-8 w-48 bg-slate-800 rounded animate-pulse" />
      <div className="grid grid-cols-2 gap-2">{[1,2].map(i => <div key={i} className="h-20 bg-slate-800 rounded-xl animate-pulse" />)}</div>
      {[1,2,3].map(i => <div key={i} className="h-24 bg-slate-800 rounded-xl animate-pulse" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <span className="text-2xl">&#x1F1EE;&#x1F1F3;</span>
            <span>Indian Markets</span>
          </h1>
          <div className="flex items-center space-x-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${isOpen ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
            <span className="text-slate-400">{isOpen ? 'Market Open' : 'Closed'}</span>
            {marketStatus?.is_expiry_day && <span className="text-amber-400 font-bold">EXPIRY DAY</span>}
          </div>
        </div>
        <button onClick={load} className="p-2 bg-slate-800 rounded-full"><RefreshCw size={18} className="text-orange-400" /></button>
      </div>

      {/* Index Selector */}
      <div className="flex space-x-2 mb-3">
        {['NIFTY', 'SENSEX', 'BANKNIFTY'].map(idx => (
          <button key={idx} onClick={() => setSelectedIndex(idx)}
            className={`flex-1 py-1.5 rounded-xl text-[10px] font-bold transition-all ${
              selectedIndex === idx ? 'bg-orange-600 text-white shadow-lg shadow-orange-500/20' : 'bg-slate-800 text-slate-400'
            }`}>{idx}</button>
        ))}
      </div>

      {/* Index Cards */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: 'NIFTY 50', val: niftyValue, chg: niftyChange, grad: 'from-blue-600 to-blue-700' },
          { label: 'SENSEX', val: sensexValue, chg: sensexChange, grad: 'from-purple-600 to-purple-700' },
          { label: 'BANK NIFTY', val: bankNifty, chg: bankNiftyChange, grad: 'from-emerald-600 to-emerald-700' }
        ].map((c, i) => (
          <div key={i} className={`bg-gradient-to-br ${c.grad} rounded-xl p-2.5`}>
            <p className="text-[9px] opacity-70">{c.label}</p>
            <p className="text-sm font-bold">{c.val ? c.val.toLocaleString() : '--'}</p>
            <p className={`text-[10px] font-medium ${(c.chg||0) >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
              {(c.chg||0) >= 0 ? '+' : ''}{(c.chg||0).toFixed(2)}%
            </p>
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-5 gap-1.5 mb-3">
        {[
          { label: 'VIX', val: vixValue ? Number(vixValue).toFixed(1) : '--', color: vixValue > 18 ? 'text-red-400' : 'text-emerald-400' },
          { label: 'PCR', val: typeof pcrValue === 'number' ? pcrValue.toFixed(2) : '--', color: pcrValue > 1 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'GIFT', val: giftValue ? Number(giftValue).toLocaleString() : '--', color: 'text-blue-400' },
          { label: 'Gap', val: giftChange ? (giftChange >= 0 ? '+' : '') + Number(giftChange).toFixed(0) : '--', color: giftChange >= 0 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'DTE', val: marketStatus?.days_to_expiry || '--', color: 'text-amber-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-800 rounded-lg p-1.5 text-center">
            <p className="text-[8px] text-slate-500">{s.label}</p>
            <p className={`text-[10px] font-bold ${s.color}`}>{s.val}</p>
          </div>
        ))}
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-3 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => {
            setActiveTab(t.key)
            if (t.key === 'predict' && !powerPred) loadPowerPrediction()
          }}
            className={`flex-1 shrink-0 py-1.5 rounded-lg text-[9px] font-medium transition-all whitespace-nowrap px-1.5 ${
              activeTab === t.key ? 'bg-orange-600 text-white' : 'text-slate-400'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* DASHBOARD TAB */}
      {activeTab === 'dashboard' && (
        <div className="space-y-3">
          <button onClick={load2minSignal}
            className="w-full bg-gradient-to-r from-amber-600 to-orange-600 rounded-xl p-3 flex items-center justify-between active:scale-[0.98] transition-transform shadow-lg shadow-orange-500/20">
            <div className="flex items-center space-x-2">
              <Timer size={18} />
              <div className="text-left">
                <p className="text-xs font-bold">2-Min Scalping Signal</p>
                <p className="text-[10px] opacity-80">RSI(7) + EMA(9/21) + Volume Surge</p>
              </div>
            </div>
            <ChevronRight size={16} />
          </button>

          {signal2min && (
            <div className={`rounded-xl p-3 border ${
              (signal2min.signal || signal2min.direction || '').toLowerCase().includes('bull') || (signal2min.direction || '').includes('UP')
                ? 'bg-emerald-500/10 border-emerald-500/20' : (signal2min.signal || '').toLowerCase().includes('bear')
                ? 'bg-red-500/10 border-red-500/20' : 'bg-blue-500/10 border-blue-500/20'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm">{signal2min.signal || signal2min.direction || 'NEUTRAL'}</span>
                {signal2min.strength && <span className="text-xs text-amber-400">Strength: {signal2min.strength}/10</span>}
              </div>
              <div className="grid grid-cols-4 gap-1 text-[10px]">
                {signal2min.rsi && <div className="bg-slate-800 rounded p-1 text-center"><p className="text-slate-500">RSI(7)</p><p className="font-bold">{Number(signal2min.rsi).toFixed(1)}</p></div>}
                {signal2min.ema_signal && <div className="bg-slate-800 rounded p-1 text-center"><p className="text-slate-500">EMA</p><p className="font-bold">{signal2min.ema_signal}</p></div>}
                {signal2min.momentum && <div className="bg-slate-800 rounded p-1 text-center"><p className="text-slate-500">Mom.</p><p className="font-bold">{signal2min.momentum}</p></div>}
                {signal2min.volume_surge !== undefined && <div className="bg-slate-800 rounded p-1 text-center"><p className="text-slate-500">Vol</p><p className={`font-bold ${signal2min.volume_surge ? 'text-amber-400' : ''}`}>{signal2min.volume_surge ? 'SURGE' : 'Normal'}</p></div>}
              </div>
              {signal2min.reason && <p className="text-[10px] text-slate-400 mt-1">{signal2min.reason}</p>}
            </div>
          )}

          {/* JARVIS AI SUPER VERDICT */}
          <button onClick={async () => {
            setLoadingVerdict(true)
            hapticFeedback?.('impact')
            try {
              const r = await fetchAiMarketVerdict()
              const d = r.data?.data || r.data || {}
              // Build formatted verdict from dashboard data
              const pred = d.prediction || {}
              const regime = d.regime || {}
              const fii = d.fii_dii || {}
              const vix = d.vix || {}
              const pcr = d.pcr || {}
              const nifty = d.nifty || {}
              const banknifty = d.banknifty || {}
              setAiVerdict({
                direction: pred.direction || 'N/A',
                action: pred.action || 'N/A',
                confidence: pred.confidence || pred.calibrated_confidence || 0,
                spot: pred.spot || nifty.ltp || 0,
                regime: regime.regime_display || regime.regime || 'N/A',
                regime_strategy: regime.strategy_hi || regime.strategy || '',
                fii_net: fii.fii_net, dii_net: fii.dii_net, fii_signal: fii.signal || '',
                vix_val: vix.vix, vix_trend: vix.trend || '', vix_fear: vix.fear_level || '',
                vix_tip: vix.interpretation || '',
                pcr_val: pcr.pcr_value || pcr.pcr, pcr_signal: pcr.signal || pcr.interpretation || '',
                bull_score: pred.bull_score || regime.bull_score || 0,
                bear_score: pred.bear_score || regime.bear_score || 0,
                nifty_change: nifty.change_pct || nifty.pct_change || 0,
                banknifty_ltp: banknifty.ltp || 0,
                banknifty_change: banknifty.change_pct || banknifty.pct_change || 0,
                _formatted: true
              })
            } catch (e) { console.warn(e) }
            setLoadingVerdict(false)
          }}
            className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 rounded-xl p-3 flex items-center justify-between active:scale-[0.98] transition-transform shadow-lg shadow-purple-500/20">
            <div className="flex items-center space-x-2">
              <Brain size={18} className={loadingVerdict ? 'animate-pulse' : ''} />
              <div className="text-left">
                <p className="text-xs font-bold">JARVIS AI Super Verdict</p>
                <p className="text-[10px] opacity-80">Groq AI analyzes ALL data → Expert trading advice</p>
              </div>
            </div>
            {loadingVerdict ? <RefreshCw size={16} className="animate-spin" /> : <ChevronRight size={16} />}
          </button>
          {aiVerdict && (
            <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-4 space-y-3">
              <div className="flex items-center space-x-2 mb-1">
                <Brain size={14} className="text-purple-400" />
                <span className="text-xs font-bold text-purple-400">AI EXPERT VERDICT</span>
              </div>

              {aiVerdict._formatted ? (
                <>
                  {/* Direction & Action */}
                  <div className={`rounded-lg p-3 text-center ${
                    (aiVerdict.direction || '').toLowerCase().includes('bull') ? 'bg-emerald-500/15 border border-emerald-500/30' :
                    (aiVerdict.direction || '').toLowerCase().includes('bear') ? 'bg-red-500/15 border border-red-500/30' :
                    'bg-yellow-500/15 border border-yellow-500/30'
                  }`}>
                    <p className="text-lg font-black">{aiVerdict.direction}</p>
                    <p className={`text-sm font-bold mt-1 ${
                      (aiVerdict.action || '').includes('CE') ? 'text-emerald-400' :
                      (aiVerdict.action || '').includes('PE') ? 'text-red-400' : 'text-yellow-400'
                    }`}>📌 {aiVerdict.action}</p>
                    <p className="text-[10px] text-slate-400 mt-1">Confidence: {Number(aiVerdict.confidence).toFixed(1)}%</p>
                  </div>

                  {/* Spot + Indices */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-800 rounded-lg p-2 text-center">
                      <p className="text-slate-400 text-[10px]">NIFTY</p>
                      <p className="font-bold text-sm">{Number(aiVerdict.spot).toFixed(0)}</p>
                      <p className={`text-[10px] font-medium ${aiVerdict.nifty_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {aiVerdict.nifty_change >= 0 ? '+' : ''}{Number(aiVerdict.nifty_change).toFixed(2)}%
                      </p>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-2 text-center">
                      <p className="text-slate-400 text-[10px]">BANKNIFTY</p>
                      <p className="font-bold text-sm">{Number(aiVerdict.banknifty_ltp).toFixed(0)}</p>
                      <p className={`text-[10px] font-medium ${aiVerdict.banknifty_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {aiVerdict.banknifty_change >= 0 ? '+' : ''}{Number(aiVerdict.banknifty_change).toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {/* Market Regime */}
                  <div className="bg-slate-800 rounded-lg p-2">
                    <p className="text-[10px] text-slate-400 mb-1">MARKET REGIME</p>
                    <p className="font-bold text-sm">{aiVerdict.regime}</p>
                    {aiVerdict.regime_strategy && <p className="text-[10px] text-slate-400 mt-1">💡 {aiVerdict.regime_strategy}</p>}
                  </div>

                  {/* Bull vs Bear Score */}
                  <div className="bg-slate-800 rounded-lg p-2">
                    <p className="text-[10px] text-slate-400 mb-1">BULL vs BEAR</p>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-slate-700 rounded-full h-3 overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" 
                          style={{ width: `${Math.min(100, Math.max(0, aiVerdict.bull_score))}%` }} />
                      </div>
                      <span className="text-[10px] text-emerald-400 font-bold w-12 text-right">{Number(aiVerdict.bull_score).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="flex-1 bg-slate-700 rounded-full h-3 overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full" 
                          style={{ width: `${Math.min(100, Math.max(0, aiVerdict.bear_score))}%` }} />
                      </div>
                      <span className="text-[10px] text-red-400 font-bold w-12 text-right">{Number(aiVerdict.bear_score).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* FII/DII */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-800 rounded-lg p-2 text-center">
                      <p className="text-slate-400 text-[10px]">FII NET</p>
                      <p className={`font-bold ${aiVerdict.fii_net >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        ₹{Number(aiVerdict.fii_net || 0).toFixed(0)} Cr
                      </p>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-2 text-center">
                      <p className="text-slate-400 text-[10px]">DII NET</p>
                      <p className={`font-bold ${aiVerdict.dii_net >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        ₹{Number(aiVerdict.dii_net || 0).toFixed(0)} Cr
                      </p>
                    </div>
                  </div>
                  {aiVerdict.fii_signal && <p className="text-[10px] text-center text-slate-400">{aiVerdict.fii_signal}</p>}

                  {/* VIX */}
                  <div className="bg-slate-800 rounded-lg p-2">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] text-slate-400">VIX (INDIA)</p>
                      <span className="text-[10px]">{aiVerdict.vix_fear}</span>
                    </div>
                    <p className="font-bold text-sm">{Number(aiVerdict.vix_val || 0).toFixed(2)}</p>
                    <p className="text-[10px] text-slate-400">{aiVerdict.vix_trend}</p>
                    {aiVerdict.vix_tip && <p className="text-[10px] text-amber-400 mt-1">💡 {aiVerdict.vix_tip}</p>}
                  </div>

                  {/* PCR */}
                  {aiVerdict.pcr_val && (
                    <div className="bg-slate-800 rounded-lg p-2">
                      <p className="text-[10px] text-slate-400">PUT-CALL RATIO (PCR)</p>
                      <p className="font-bold text-sm">{Number(aiVerdict.pcr_val).toFixed(2)}</p>
                      {aiVerdict.pcr_signal && <p className="text-[10px] text-slate-400">{aiVerdict.pcr_signal}</p>}
                    </div>
                  )}
                </>
              ) : (
                <pre className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">{typeof aiVerdict === 'string' ? aiVerdict : JSON.stringify(aiVerdict, null, 2)}</pre>
              )}
            </div>
          )}

          {pivots && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                <Target size={12} className="text-blue-400" /><span>{selectedIndex} Pivot Points</span>
              </h3>
              <div className="grid grid-cols-3 gap-1.5 text-[10px] text-center">
                <div className="space-y-1">
                  <p className="text-red-400 font-bold text-[9px]">SUPPORT</p>
                  {['s1','s2','s3'].map(k => pivots[k] && <p key={k} className="bg-red-500/10 rounded p-1">{k.toUpperCase()}: {pivots[k]}</p>)}
                </div>
                <div className="space-y-1">
                  <p className="text-blue-400 font-bold text-[9px]">PIVOT</p>
                  <p className="bg-blue-500/10 rounded p-1 text-base font-bold">{pivots.pivot || pivots.pp || '--'}</p>
                  {pivots.cpr_high && <p className="bg-blue-500/5 rounded p-1">CPR: {pivots.cpr_high}-{pivots.cpr_low}</p>}
                </div>
                <div className="space-y-1">
                  <p className="text-emerald-400 font-bold text-[9px]">RESISTANCE</p>
                  {['r1','r2','r3'].map(k => pivots[k] && <p key={k} className="bg-emerald-500/10 rounded p-1">{k.toUpperCase()}: {pivots[k]}</p>)}
                </div>
              </div>
            </div>
          )}

          {oi && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                <Layers size={12} className="text-purple-400" /><span>OI Buildup</span>
              </h3>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="space-y-1">
                  <p className="text-emerald-400 font-semibold text-[9px]">LONG BUILDUP</p>
                  {(oi.long_buildup || []).slice(0, 4).map((s, i) => (
                    <div key={i} className="flex justify-between bg-emerald-500/5 rounded p-1">
                      <span>{typeof s === 'string' ? s : s.symbol || s.strike}</span>
                      <span className="text-emerald-400">{s.change || ''}</span>
                    </div>
                  ))}
                </div>
                <div className="space-y-1">
                  <p className="text-red-400 font-semibold text-[9px]">SHORT BUILDUP</p>
                  {(oi.short_buildup || []).slice(0, 4).map((s, i) => (
                    <div key={i} className="flex justify-between bg-red-500/5 rounded p-1">
                      <span>{typeof s === 'string' ? s : s.symbol || s.strike}</span>
                      <span className="text-red-400">{s.change || ''}</span>
                    </div>
                  ))}
                </div>
              </div>
              {oi.max_pain && <p className="text-[10px] text-amber-400 mt-2 text-center">Max Pain: {Number(oi.max_pain).toLocaleString()}</p>}
            </div>
          )}
        </div>
      )}

      {/* AI PREDICT TAB */}
      {activeTab === 'predict' && (
        <div className="space-y-3">
          <button onClick={loadPowerPrediction} disabled={loadingPower}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4 text-center active:scale-[0.98] transition-transform shadow-lg shadow-purple-500/20 disabled:opacity-50">
            <Brain size={24} className="mx-auto mb-1" />
            <p className="font-bold text-sm">{loadingPower ? 'Analyzing 10 signals...' : 'Run Power Prediction'}</p>
            <p className="text-[10px] opacity-70">ML + TA + Candles + FII + VIX + PCR + Pivots + GIFT + News + Global</p>
          </button>

          {powerPred && (
            <div className={`rounded-xl p-4 border-2 ${
              (powerPred.verdict || powerPred.direction || '').toLowerCase().includes('bull')
                ? 'bg-emerald-500/10 border-emerald-500/30' : (powerPred.verdict || powerPred.direction || '').toLowerCase().includes('bear')
                ? 'bg-red-500/10 border-red-500/30' : 'bg-blue-500/10 border-blue-500/30'
            }`}>
              <div className="text-center mb-3">
                <p className="text-2xl font-bold">{powerPred.verdict || powerPred.direction || 'NEUTRAL'}</p>
                {powerPred.confidence && (
                  <div className="mt-2">
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-slate-400">Confidence</span>
                      <span className="font-bold">{powerPred.confidence}%</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${
                        powerPred.confidence > 70 ? 'bg-emerald-500' : powerPred.confidence > 50 ? 'bg-amber-500' : 'bg-red-500'
                      }`} style={{ width: `${powerPred.confidence}%` }} />
                    </div>
                  </div>
                )}
              </div>

              {powerPred.signals && (
                <div className="space-y-1">
                  <p className="text-[10px] text-slate-400 font-bold">SIGNALS BREAKDOWN:</p>
                  {Object.entries(powerPred.signals).map(([key, sig]) => {
                    const isBull = typeof sig === 'string' ? sig.toLowerCase().includes('bull') : (sig?.direction || '').toLowerCase().includes('bull')
                    const label = typeof sig === 'string' ? sig : sig?.signal || sig?.direction || sig?.value || JSON.stringify(sig)
                    return (
                      <div key={key} className="flex items-center justify-between bg-slate-800 rounded-lg p-1.5 text-[10px]">
                        <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className={`font-bold ${isBull ? 'text-emerald-400' : 'text-red-400'}`}>
                          {String(label).substring(0, 30)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}

              {powerPred.target && <p className="text-xs text-emerald-400 mt-2">Target: {powerPred.target}</p>}
              {powerPred.stop_loss && <p className="text-xs text-red-400">Stop Loss: {powerPred.stop_loss}</p>}
            </div>
          )}

          {regime && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                <Gauge size={12} className="text-blue-400" /><span>Market Regime</span>
              </h3>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm font-bold px-2 py-0.5 rounded-lg ${
                  (regime.regime || '').toLowerCase().includes('bull') ? 'bg-emerald-500/20 text-emerald-400' :
                  (regime.regime || '').toLowerCase().includes('bear') ? 'bg-red-500/20 text-red-400' :
                  'bg-blue-500/20 text-blue-400'
                }`}>{regime.regime || 'Unknown'}</span>
                {regime.confidence && <span className="text-xs text-slate-400">{regime.confidence}% confidence</span>}
              </div>
              {regime.trading_params && (
                <div className="grid grid-cols-3 gap-1 text-[10px]">
                  {regime.trading_params.position_size && <div className="bg-slate-700 rounded p-1 text-center"><p className="text-slate-500">Position</p><p>{regime.trading_params.position_size}%</p></div>}
                  {regime.trading_params.sl_multiplier && <div className="bg-slate-700 rounded p-1 text-center"><p className="text-slate-500">SL Multi</p><p>{regime.trading_params.sl_multiplier}x</p></div>}
                  {regime.trading_params.strategy && <div className="bg-slate-700 rounded p-1 text-center"><p className="text-slate-500">Strategy</p><p className="truncate">{regime.trading_params.strategy}</p></div>}
                </div>
              )}
            </div>
          )}

          {oiSuper && (
            <div className="bg-slate-800 border border-amber-500/20 rounded-xl p-3">
              <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                <AlertTriangle size={12} className="text-amber-400" /><span>OI Super Signal</span>
              </h3>
              {oiSuper.direction && <p className={`text-sm font-bold ${(oiSuper.direction || '').includes('BULL') ? 'text-emerald-400' : 'text-red-400'}`}>{oiSuper.direction}</p>}
              {oiSuper.traps && Array.isArray(oiSuper.traps) && oiSuper.traps.length > 0 && (
                <div className="mt-1 space-y-0.5">{oiSuper.traps.map((t, i) => <p key={i} className="text-[10px] text-amber-400">Warning: {typeof t === 'string' ? t : t.name || JSON.stringify(t)}</p>)}</div>
              )}
              {oiSuper.max_pain && <p className="text-[10px] text-slate-400 mt-1">Max Pain: {oiSuper.max_pain}</p>}
            </div>
          )}

          {globalImpact && (
            <div className="bg-slate-800 border border-blue-500/20 rounded-xl p-3">
              <h3 className="font-bold text-xs mb-2 flex items-center space-x-2">
                <Globe size={12} className="text-blue-400" /><span>Global Impact on India</span>
              </h3>
              {typeof globalImpact === 'string' ? (
                <p className="text-xs text-slate-300">{globalImpact}</p>
              ) : (
                <>
                  {globalImpact.prediction && <p className="text-sm font-bold">{globalImpact.prediction}</p>}
                  {globalImpact.factors && Object.entries(globalImpact.factors).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] mt-0.5">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span>{String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* FII/DII TAB */}
      {activeTab === 'fii' && (
        <div className="space-y-3">
          {!fiiDii ? <p className="text-center text-slate-500 py-12 text-sm">FII/DII data loading...</p> : (
            <>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'FII', icon: Globe, color: 'blue', buy: fiiDii.fii_buy, sell: fiiDii.fii_sell, net: fiiDii.fii_net },
                  { label: 'DII', icon: Building2, color: 'orange', buy: fiiDii.dii_buy, sell: fiiDii.dii_sell, net: fiiDii.dii_net }
                ].map((item, i) => (
                  <div key={i} className={`rounded-xl p-3 border ${(item.net||0) >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <div className="flex items-center space-x-1 mb-1">
                      <item.icon size={14} />
                      <p className="font-bold text-sm">{item.label}</p>
                    </div>
                    <p className="text-[10px] text-slate-400">Buy: {(item.buy||0).toLocaleString()} Cr</p>
                    <p className="text-[10px] text-slate-400">Sell: {(item.sell||0).toLocaleString()} Cr</p>
                    <p className={`text-sm font-bold mt-1 ${(item.net||0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      Net: {(item.net||0).toLocaleString()} Cr
                    </p>
                  </div>
                ))}
              </div>
              {(fiiDii.history || []).length > 0 && (
                <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                  <h3 className="text-xs font-bold mb-2">FII/DII Flow Trend</h3>
                  <div className="h-36">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={(fiiDii.history || []).slice(-7)}>
                        <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#64748b' }} />
                        <YAxis tick={{ fontSize: 8, fill: '#64748b' }} />
                        <Tooltip />
                        <Bar dataKey="fii_net" fill="#3b82f6" name="FII" />
                        <Bar dataKey="dii_net" fill="#f59e0b" name="DII" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
              {fiiDii.interpretation && <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-2.5"><p className="text-[10px] text-blue-300">{fiiDii.interpretation}</p></div>}
            </>
          )}
        </div>
      )}

      {/* SECTORS TAB */}
      {activeTab === 'sectors' && (
        <div className="space-y-2">
          {sectors.length === 0 ? <p className="text-center text-slate-500 py-12 text-sm">Loading sectors...</p> :
            sectors.map((s, i) => {
              const ch = s.change || s.change_pct || 0
              return (
                <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-2.5 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] ${ch >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                      {ch >= 0 ? <TrendingUp size={12} className="text-emerald-400" /> : <TrendingDown size={12} className="text-red-400" />}
                    </div>
                    <div>
                      <p className="font-semibold text-xs">{s.name || s.sector}</p>
                      {s.top_stock && <p className="text-[9px] text-slate-500">Top: {s.top_stock}</p>}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-xs font-bold ${ch >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{ch >= 0 ? '+' : ''}{Number(ch).toFixed(2)}%</p>
                    {s.change_1w !== undefined && <p className="text-[9px] text-slate-500">1W: {Number(s.change_1w).toFixed(1)}%</p>}
                  </div>
                </div>
              )
            })
          }
        </div>
      )}

      {/* INVEST TAB */}
      {activeTab === 'invest' && (
        <div className="space-y-3">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
            <h3 className="font-bold text-xs mb-2">Investment Calculator</h3>
            <p className="text-[10px] text-slate-400 mb-2">Enter amount - AI finds best options plays</p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 flex items-center bg-slate-700 rounded-xl px-3 py-2">
                <span className="text-slate-400 text-sm mr-1">Rs</span>
                <input type="number" value={investAmount} onChange={e => setInvestAmount(e.target.value)}
                  placeholder="2000" className="flex-1 bg-transparent text-sm outline-none" />
              </div>
              <button onClick={loadInvestCalc}
                className="bg-orange-600 px-4 py-2 rounded-xl text-xs font-bold active:scale-95">Calculate</button>
            </div>
          </div>

          {investCalc && (
            <div className="space-y-2">
              {(investCalc.options || investCalc.best_options || []).map((opt, i) => (
                <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs">{opt.name || opt.description || 'Option ' + (i + 1)}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                      (opt.type || '').toUpperCase() === 'CE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{opt.type || 'CE'}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-[10px]">
                    <div><p className="text-slate-500">Strike</p><p>{opt.strike || '--'}</p></div>
                    <div><p className="text-slate-500">Premium</p><p>Rs {opt.premium || opt.ltp || '--'}</p></div>
                    <div><p className="text-slate-500">Lots</p><p>{opt.lots || opt.quantity || '--'}</p></div>
                  </div>
                  {opt.profit_scenarios && (
                    <div className="mt-1 grid grid-cols-3 gap-1 text-[9px]">
                      {Object.entries(opt.profit_scenarios).slice(0, 3).map(([k, v]) => (
                        <div key={k} className="bg-slate-700 rounded p-1 text-center">
                          <p className="text-slate-500">{k}</p>
                          <p className={parseFloat(v) >= 0 ? 'text-emerald-400' : 'text-red-400'}>Rs {v}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STOCK ANALYSIS TAB */}
      {activeTab === 'analysis' && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <input value={analysisSymbol} onChange={e => setAnalysisSymbol(e.target.value.toUpperCase())}
              placeholder="RELIANCE, TCS, INFY..."
              className="flex-1 bg-slate-800 rounded-xl px-3 py-2 text-sm outline-none border border-slate-700 focus:border-orange-500 uppercase" />
            <button onClick={() => loadSuperAnalysis(analysisSymbol)} disabled={loadingAnalysis}
              className="bg-orange-600 px-4 py-2 rounded-xl text-xs font-bold disabled:opacity-50">
              {loadingAnalysis ? '...' : 'Analyze'}
            </button>
          </div>
          <div className="flex space-x-1.5 overflow-x-auto pb-1">
            {['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'ITC', 'SBIN', 'BHARTIARTL', 'LT', 'TATAMOTORS'].map(s => (
              <button key={s} onClick={() => loadSuperAnalysis(s)}
                className="shrink-0 px-2.5 py-1 bg-slate-800 rounded-full text-[9px] font-medium text-slate-400 active:bg-orange-600 active:text-white">{s}</button>
            ))}
          </div>

          {superAnalysis && (
            <div className="space-y-2">
              <div className="bg-gradient-to-br from-orange-500/20 to-amber-500/20 border border-orange-500/20 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold">{superAnalysis.symbol || analysisSymbol}</h3>
                  {superAnalysis.signal && (
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      (superAnalysis.signal || '').toLowerCase().includes('buy') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{superAnalysis.signal}</span>
                  )}
                </div>
                {superAnalysis.price && <p className="text-lg font-bold">Rs {Number(superAnalysis.price).toLocaleString()}</p>}
                <div className="grid grid-cols-3 gap-1.5 text-[10px] mt-2">
                  {superAnalysis.target && <div><p className="text-slate-500">Target</p><p className="text-emerald-400 font-bold">Rs {superAnalysis.target}</p></div>}
                  {superAnalysis.stop_loss && <div><p className="text-slate-500">Stop Loss</p><p className="text-red-400 font-bold">Rs {superAnalysis.stop_loss}</p></div>}
                  {superAnalysis.confidence && <div><p className="text-slate-500">Confidence</p><p className="text-blue-400 font-bold">{superAnalysis.confidence}%</p></div>}
                </div>
                {superAnalysis.analysis && <p className="text-[10px] text-slate-300 mt-2 leading-relaxed">{superAnalysis.analysis}</p>}
              </div>
              {superAnalysis.option_recommendation && (
                <div className="bg-slate-800 border border-amber-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-1">Option Recommendation</h3>
                  <p className="text-[10px] text-slate-300">{typeof superAnalysis.option_recommendation === 'string' ? superAnalysis.option_recommendation : JSON.stringify(superAnalysis.option_recommendation)}</p>
                </div>
              )}
              {superAnalysis.indicators && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-1">Technical Indicators</h3>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    {Object.entries(superAnalysis.indicators).slice(0, 12).map(([k, v]) => (
                      <div key={k} className="flex justify-between bg-slate-700/50 rounded p-1">
                        <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                        <span className="font-medium">{typeof v === 'number' ? v.toFixed(2) : String(v).substring(0, 15)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IndianStocks
