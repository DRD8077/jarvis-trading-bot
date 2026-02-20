import React, { useState, useEffect } from 'react'
import {
  Brain, Globe, TrendingUp, Zap, Eye, RefreshCw, ChevronRight,
  Shield, BarChart3, Newspaper, Gift, Target, AlertCircle
} from 'lucide-react'
import { fetchIntelligence, fetchPredictions, fetchAirdrops, fetchRisk } from '../services/api'
import { useApp } from '../context/AppContext'

const Intelligence = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [intel, setIntel] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [airdrops, setAirdrops] = useState([])
  const [riskCalc, setRiskCalc] = useState(null)
  const [activeTab, setActiveTab] = useState('intel')
  const [loading, setLoading] = useState(true)

  // Risk calculator inputs
  const [riskParams, setRiskParams] = useState({
    capital: '10000', entry: '', stoploss: '', risk_percent: '2'
  })

  const loadData = async () => {
    setLoading(true)
    try {
      const [intRes, predRes, airRes] = await Promise.all([
        fetchIntelligence().catch(() => null),
        fetchPredictions().catch(() => null),
        fetchAirdrops().catch(() => null)
      ])
      setIntel(intRes?.data?.data || intRes?.data || null)
      
      const predData = predRes?.data?.data || predRes?.data?.predictions || predRes?.data || []
      setPredictions(Array.isArray(predData) ? predData : [])
      
      const airData = airRes?.data?.data || airRes?.data?.airdrops || airRes?.data || []
      setAirdrops(Array.isArray(airData) ? airData : [])
    } catch (e) {
      console.error('Intelligence load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  // ⚡ Auto-refresh intelligence every 20s
  useEffect(() => {
    const iv = setInterval(loadData, 20000)
    return () => clearInterval(iv)
  }, [])

  const doRiskCalc = async () => {
    hapticFeedback('impact')
    try {
      const res = await fetchRisk(riskParams)
      setRiskCalc(res.data?.data || res.data || {})
    } catch (e) {
      addNotification('Risk calc failed', 'error')
    }
  }

  const tabs = [
    { id: 'intel', label: 'Intelligence', icon: Brain },
    { id: 'predict', label: 'Accuracy', icon: Target },
    { id: 'airdrops', label: 'Airdrops', icon: Gift },
    { id: 'risk', label: 'Risk Calc', icon: Shield },
  ]

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-12 rounded-xl" />
        {[1,2,3].map(i => <div key={i} className="skeleton h-32 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <Brain size={22} className="text-indigo-400" />
            <span>Intelligence Hub</span>
          </h1>
          <p className="text-slate-400 text-sm">AI-powered market intelligence</p>
        </div>
        <button onClick={loadData} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-5 overflow-x-auto scrollbar-hide">
        {tabs.map(t => {
          const Icon = t.icon
          return (
            <button key={t.id} onClick={() => { setActiveTab(t.id); hapticFeedback('impact') }}
              className={`flex-1 flex items-center justify-center space-x-1 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap px-2 ${
                activeTab === t.id ? 'bg-indigo-600 text-white' : 'text-slate-400'
              }`}>
              <Icon size={14} />
              <span>{t.label}</span>
            </button>
          )
        })}
      </div>

      {/* INTELLIGENCE TAB */}
      {activeTab === 'intel' && (
        <div className="space-y-4">
          {!intel ? (
            <div className="text-center py-12">
              <Brain size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">Loading market intelligence...</p>
            </div>
          ) : (
            <>
              {/* Briefing */}
              {intel.briefing && (
                <div className="bg-gradient-to-br from-indigo-600/30 to-purple-600/30 border border-indigo-500/30 rounded-xl p-4">
                  <h3 className="font-bold text-sm mb-2 text-indigo-300">Market Briefing</h3>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{intel.briefing}</p>
                </div>
              )}

              {/* Key Levels */}
              {intel.key_levels && (
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <h3 className="font-bold text-sm mb-3">Key Levels</h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(intel.key_levels).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                        <span className="font-medium">{typeof v === 'number' ? v.toLocaleString() : JSON.stringify(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Insights */}
              {(intel.insights || intel.analysis || intel.summary) && (
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <h3 className="font-bold text-sm mb-2">AI Analysis</h3>
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {intel.insights || intel.analysis || intel.summary}
                  </p>
                </div>
              )}

              {/* Raw data fallback */}
              {!intel.briefing && !intel.insights && (
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <h3 className="font-bold text-sm mb-2">Market Intelligence</h3>
                  <pre className="text-xs text-slate-400 overflow-auto max-h-96 whitespace-pre-wrap">
                    {JSON.stringify(intel, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* PREDICTIONS ACCURACY TAB */}
      {activeTab === 'predict' && (
        <div className="space-y-3">
          {predictions.length === 0 ? (
            <div className="text-center py-12">
              <Target size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">No prediction history yet</p>
            </div>
          ) : (
            predictions.map((p, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-bold text-sm">{p.symbol || p.name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    p.correct ? 'bg-emerald-500/20 text-emerald-400' : p.correct === false ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {p.correct ? '✅ Correct' : p.correct === false ? '❌ Wrong' : '⏳ Pending'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div><span className="text-slate-400">Predicted: </span><span>{p.prediction || p.direction}</span></div>
                  <div><span className="text-slate-400">Target: </span><span>₹{(p.target || 0).toLocaleString()}</span></div>
                  <div><span className="text-slate-400">Actual: </span><span>₹{(p.actual || 0).toLocaleString()}</span></div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* AIRDROPS TAB */}
      {activeTab === 'airdrops' && (
        <div className="space-y-3">
          {airdrops.length === 0 ? (
            <div className="text-center py-12">
              <Gift size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">No upcoming airdrops found</p>
            </div>
          ) : (
            airdrops.map((a, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-bold text-sm">{a.name || a.project}</p>
                  <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full">
                    {a.status || a.type || 'Upcoming'}
                  </span>
                </div>
                {a.description && <p className="text-xs text-slate-400 mb-2">{a.description}</p>}
                <div className="flex items-center space-x-4 text-xs text-slate-500">
                  {a.date && <span>📅 {a.date}</span>}
                  {a.value && <span>💰 {a.value}</span>}
                  {a.chain && <span>⛓ {a.chain}</span>}
                </div>
                {a.link && (
                  <a href={a.link} target="_blank" rel="noopener noreferrer"
                    className="mt-2 text-xs text-blue-400 flex items-center space-x-1">
                    <Globe size={10} /><span>Participate</span>
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* RISK CALCULATOR TAB */}
      {activeTab === 'risk' && (
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="font-bold text-sm mb-3 flex items-center space-x-2">
              <Shield size={16} className="text-amber-400" />
              <span>Position Size Calculator</span>
            </h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Capital (₹)</label>
                <input type="number" value={riskParams.capital}
                  onChange={e => setRiskParams(p => ({ ...p, capital: e.target.value }))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Risk %</label>
                <input type="number" value={riskParams.risk_percent}
                  onChange={e => setRiskParams(p => ({ ...p, risk_percent: e.target.value }))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Entry Price</label>
                <input type="number" value={riskParams.entry}
                  onChange={e => setRiskParams(p => ({ ...p, entry: e.target.value }))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Stop Loss</label>
                <input type="number" value={riskParams.stoploss}
                  onChange={e => setRiskParams(p => ({ ...p, stoploss: e.target.value }))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <button onClick={doRiskCalc}
              className="w-full bg-amber-600 hover:bg-amber-500 text-white py-3 rounded-xl font-semibold text-sm transition-colors">
              Calculate Position Size
            </button>
          </div>

          {riskCalc && (
            <div className="bg-slate-800 rounded-xl p-4 border border-amber-500/30 animate-fade-up">
              <h3 className="font-bold text-sm mb-3 text-amber-400">Result</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {Object.entries(riskCalc).map(([k, v]) => (
                  <div key={k} className="bg-slate-700/50 rounded-lg p-2.5">
                    <p className="text-[10px] text-slate-400 uppercase">{k.replace(/_/g, ' ')}</p>
                    <p className="font-bold">{typeof v === 'number' ? v.toLocaleString() : v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Intelligence
