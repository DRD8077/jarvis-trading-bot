import React, { useState, useCallback } from 'react'
import { ArrowLeft, ShieldCheck, Calculator, Target, TrendingUp, PieChart, AlertTriangle, DollarSign, RefreshCw, Percent, BarChart3, Scale } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchKellyCriterion, fetchPositionSize, fetchInvestmentPlan, fetchRiskReward, fetchMarketNews, fetchStockNews } from '../services/api'

export default function RiskManager() {
  const nav = useNavigate()
  const [tab, setTab] = useState('position')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})

  // Position Size Inputs
  const [capital, setCapital] = useState(100000)
  const [riskPct, setRiskPct] = useState(2)
  const [entry, setEntry] = useState(100)
  const [sl, setSl] = useState(95)

  // Risk-Reward Inputs
  const [rrEntry, setRrEntry] = useState(100)
  const [rrSl, setRrSl] = useState(95)
  const [rrTarget, setRrTarget] = useState(115)

  // Investment Capital
  const [investCapital, setInvestCapital] = useState(50000)

  // News
  const [newsSymbol, setNewsSymbol] = useState('')

  const load = useCallback(async (key, fn) => {
    setLoading(p => ({ ...p, [key]: true }))
    try {
      const r = await fn()
      setData(p => ({ ...p, [key]: r.data?.data || r.data || {} }))
    } catch (e) { console.warn(key, e.message) }
    setLoading(p => ({ ...p, [key]: false }))
  }, [])

  const tabs = [
    { id: 'position', label: 'Position Size', icon: Calculator },
    { id: 'risk-reward', label: 'Risk:Reward', icon: Scale },
    { id: 'kelly', label: 'Kelly Criterion', icon: Percent },
    { id: 'invest', label: 'Investment Plan', icon: PieChart },
    { id: 'news', label: 'Market News', icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-950 to-black text-white pb-24">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur-md border-b border-gray-800/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => nav(-1)} className="p-1"><ArrowLeft size={20} className="text-gray-400" /></button>
          <div>
            <h1 className="text-lg font-bold flex items-center gap-2">
              <ShieldCheck size={18} className="text-green-400" />
              Risk Manager
            </h1>
            <p className="text-xs text-gray-500">Position Sizing, Kelly, Risk:Reward & News</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-3 overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-gray-800/50 text-gray-400 border border-gray-700/30'
            }`}>
            <t.icon size={14} />{t.label}
          </button>
        ))}
      </div>

      <div className="px-4 py-2 space-y-3">
        {/* POSITION SIZE CALCULATOR */}
        {tab === 'position' && (
          <div>
            <div className="bg-gradient-to-r from-green-500/10 to-cyan-500/10 rounded-xl p-4 border border-green-500/20 mb-4">
              <h3 className="text-sm font-bold text-green-400 mb-1">Position Size Calculator</h3>
              <p className="text-xs text-gray-500">Never risk more than you can afford. Calculate exact quantity based on your risk tolerance.</p>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <InputField label="Capital (₹)" value={capital} onChange={setCapital} icon={DollarSign} />
              <InputField label="Risk %" value={riskPct} onChange={setRiskPct} icon={AlertTriangle} step="0.5" />
              <InputField label="Entry Price" value={entry} onChange={setEntry} icon={TrendingUp} />
              <InputField label="Stop Loss" value={sl} onChange={setSl} icon={Target} />
            </div>

            <button
              onClick={() => load('position', () => fetchPositionSize(capital, riskPct, entry, sl))}
              className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl text-sm font-bold"
            >
              {loading.position ? 'Calculating...' : 'CALCULATE POSITION SIZE'}
            </button>

            {data.position && (
              <div className="mt-4 space-y-2">
                <ResultCard obj={data.position} color="green" />
                {/* Quick preview */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/40">
                  <div className="grid grid-cols-2 gap-3">
                    <QuickStat label="Risk Amount" value={`₹${(capital * riskPct / 100).toLocaleString()}`} color="red" />
                    <QuickStat label="Per Share Risk" value={`₹${(entry - sl).toFixed(2)}`} color="orange" />
                    <QuickStat label="Max Qty" value={Math.floor((capital * riskPct / 100) / (entry - sl))} color="green" />
                    <QuickStat label="Position Value" value={`₹${(Math.floor((capital * riskPct / 100) / (entry - sl)) * entry).toLocaleString()}`} color="cyan" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* RISK:REWARD CALCULATOR */}
        {tab === 'risk-reward' && (
          <div>
            <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-xl p-4 border border-yellow-500/20 mb-4">
              <h3 className="text-sm font-bold text-yellow-400 mb-1">Risk:Reward Ratio</h3>
              <p className="text-xs text-gray-500">Never take a trade below 1:2 risk-reward. Calculate before you enter.</p>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4">
              <InputField label="Entry" value={rrEntry} onChange={setRrEntry} icon={TrendingUp} />
              <InputField label="Stop Loss" value={rrSl} onChange={setRrSl} icon={Target} />
              <InputField label="Target" value={rrTarget} onChange={setRrTarget} icon={DollarSign} />
            </div>

            <button
              onClick={() => load('rr', () => fetchRiskReward(rrEntry, rrSl, rrTarget))}
              className="w-full py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl text-sm font-bold"
            >
              {loading.rr ? 'Calculating...' : 'CALCULATE RISK:REWARD'}
            </button>

            {data.rr ? (
              <ResultCard obj={data.rr} color="yellow" />
            ) : (
              /* Client-side quick calc */
              <div className="mt-4 bg-gray-800/50 rounded-xl p-4 border border-gray-700/40">
                <div className="grid grid-cols-3 gap-3">
                  <QuickStat label="Risk" value={`₹${(rrEntry - rrSl).toFixed(2)}`} color="red" />
                  <QuickStat label="Reward" value={`₹${(rrTarget - rrEntry).toFixed(2)}`} color="green" />
                  <QuickStat
                    label="Ratio"
                    value={`1:${((rrTarget - rrEntry) / (rrEntry - rrSl)).toFixed(2)}`}
                    color={((rrTarget - rrEntry) / (rrEntry - rrSl)) >= 2 ? 'green' : 'red'}
                  />
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>SL: ₹{rrSl}</span>
                    <span>Entry: ₹{rrEntry}</span>
                    <span>TP: ₹{rrTarget}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden flex">
                    <div className="bg-red-500 h-full" style={{ width: `${((rrEntry - rrSl) / (rrTarget - rrSl)) * 100}%` }} />
                    <div className="bg-green-500 h-full flex-1" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* KELLY CRITERION */}
        {tab === 'kelly' && (
          <div>
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-4 border border-purple-500/20 mb-4">
              <h3 className="text-sm font-bold text-purple-400 mb-1">Kelly Criterion</h3>
              <p className="text-xs text-gray-500">Mathematically optimal bet size based on your ACTUAL trade history. Maximize growth, minimize risk of ruin.</p>
            </div>

            <button
              onClick={() => load('kelly', fetchKellyCriterion)}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl text-sm font-bold"
            >
              {loading.kelly ? 'Analyzing Trades...' : 'CALCULATE KELLY FROM TRADE HISTORY'}
            </button>

            {data.kelly && <ResultCard obj={data.kelly} color="purple" />}

            {/* Kelly Explainer */}
            <div className="mt-4 bg-gray-800/50 rounded-xl p-4 border border-gray-700/40">
              <h4 className="text-xs font-bold text-gray-400 mb-2">HOW KELLY WORKS</h4>
              <div className="space-y-2 text-xs text-gray-500">
                <p><span className="text-purple-400 font-bold">f* = (bp - q) / b</span></p>
                <p>b = average win / average loss</p>
                <p>p = win rate, q = 1 - p</p>
                <p className="text-yellow-400">Use Half-Kelly (f*/2) for safety — full Kelly is too aggressive.</p>
              </div>
            </div>
          </div>
        )}

        {/* INVESTMENT PLAN */}
        {tab === 'invest' && (
          <div>
            <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-xl p-4 border border-cyan-500/20 mb-4">
              <h3 className="text-sm font-bold text-cyan-400 mb-1">Smart Investment Plan</h3>
              <p className="text-xs text-gray-500">AI-generated allocation plan based on your capital — diversified across sectors, risk levels.</p>
            </div>

            <div className="mb-4">
              <InputField label="Total Capital (₹)" value={investCapital} onChange={setInvestCapital} icon={DollarSign} />
            </div>

            <button
              onClick={() => load('invest', () => fetchInvestmentPlan(investCapital))}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl text-sm font-bold"
            >
              {loading.invest ? 'Building Plan...' : 'GENERATE INVESTMENT PLAN'}
            </button>

            {data.invest && <ResultCard obj={data.invest} color="cyan" />}
          </div>
        )}

        {/* MARKET NEWS */}
        {tab === 'news' && (
          <div>
            <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-xl p-4 border border-orange-500/20 mb-4">
              <h3 className="text-sm font-bold text-orange-400 mb-1">Market News with Sentiment</h3>
              <p className="text-xs text-gray-500">AI-analyzed breaking news with bullish/bearish sentiment classification.</p>
            </div>

            <div className="flex gap-2 mb-4">
              <button onClick={() => load('news', fetchMarketNews)}
                className="flex-1 py-2.5 bg-orange-500/20 rounded-lg text-xs font-bold text-orange-400 border border-orange-500/30">
                {loading.news ? '...' : 'Market News'}
              </button>
              <div className="flex-1 flex gap-1">
                <input type="text" value={newsSymbol} onChange={e => setNewsSymbol(e.target.value)}
                  placeholder="RELIANCE" className="flex-1 bg-gray-900/60 border border-gray-700/50 rounded-lg px-2 py-2 text-xs text-white placeholder-gray-600 outline-none" />
                <button onClick={() => newsSymbol && load('stockNews', () => fetchStockNews(newsSymbol))}
                  className="px-3 py-2 bg-cyan-500/20 rounded-lg text-xs font-bold text-cyan-400 border border-cyan-500/30">Go</button>
              </div>
            </div>

            {loading.news || loading.stockNews ? <Loader /> : (
              <>
                {data.news && <RenderNews items={data.news} />}
                {data.stockNews && <RenderNews items={data.stockNews} />}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function InputField({ label, value, onChange, icon: Icon, step = '1' }) {
  return (
    <div>
      <label className="text-xs text-gray-500 flex items-center gap-1 mb-1">
        {Icon && <Icon size={10} />} {label}
      </label>
      <input
        type="number"
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value) || 0)}
        className="w-full bg-gray-900/60 border border-gray-700/50 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-green-500/50"
      />
    </div>
  )
}

function QuickStat({ label, value, color }) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-lg font-bold text-${color}-400`}>{value}</p>
    </div>
  )
}

function ResultCard({ obj, color = 'green' }) {
  if (!obj || typeof obj !== 'object') return null
  const entries = Object.entries(obj).filter(([k, v]) => v !== null && v !== undefined && k !== 'status')
  if (!entries.length) return null
  return (
    <div className={`mt-4 bg-gray-800/50 rounded-xl p-4 border border-${color}-500/20`}>
      <div className="grid grid-cols-2 gap-2">
        {entries.slice(0, 20).map(([k, v]) => (
          <div key={k} className="bg-gray-900/40 rounded-lg p-2">
            <p className="text-xs text-gray-500">{k.replace(/_/g, ' ')}</p>
            <p className={`text-sm font-bold text-${color}-400`}>
              {typeof v === 'number' ? (v > 1000 ? `₹${v.toLocaleString()}` : v.toFixed(2)) : typeof v === 'object' ? JSON.stringify(v).slice(0, 80) : String(v)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

function RenderNews({ items }) {
  const news = items?.news || items?.result || (Array.isArray(items) ? items : [])
  if (typeof news === 'string') {
    return <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/40"><pre className="text-xs text-gray-300 whitespace-pre-wrap">{news}</pre></div>
  }
  if (!Array.isArray(news) || !news.length) {
    if (typeof items === 'object') {
      return (
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/40">
          {Object.entries(items).filter(([_, v]) => v).map(([k, v]) => (
            <div key={k} className="mb-2">
              <span className="text-xs text-orange-400 uppercase">{k.replace(/_/g, ' ')}: </span>
              <span className="text-xs text-gray-300">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
            </div>
          ))}
        </div>
      )
    }
    return <p className="text-gray-500 text-center py-4 text-sm">No news available</p>
  }
  return (
    <div className="space-y-2">
      {news.map((n, i) => (
        <div key={i} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/40">
          <div className="flex justify-between items-start mb-1">
            <h4 className="text-xs font-bold text-white flex-1">{n.title || n.headline || n.text}</h4>
            {n.sentiment && (
              <span className={`text-xs px-2 py-0.5 rounded-full ml-2 ${
                n.sentiment.toLowerCase().includes('bull') || n.sentiment.toLowerCase().includes('positive') ? 'bg-green-500/20 text-green-400' :
                n.sentiment.toLowerCase().includes('bear') || n.sentiment.toLowerCase().includes('negative') ? 'bg-red-500/20 text-red-400' :
                'bg-gray-700 text-gray-400'
              }`}>{n.sentiment}</span>
            )}
          </div>
          {n.summary && <p className="text-xs text-gray-500">{n.summary}</p>}
          {n.source && <p className="text-xs text-gray-600 mt-1">{n.source} {n.date && `· ${n.date}`}</p>}
        </div>
      ))}
    </div>
  )
}

function Loader() {
  return (
    <div className="flex flex-col items-center py-12">
      <div className="w-10 h-10 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin" />
      <p className="text-xs text-gray-500 mt-3">Loading...</p>
    </div>
  )
}
