import React, { useState, useEffect } from 'react'
import {
  RefreshCw, TrendingUp, TrendingDown, Brain, Zap,
  AlertTriangle, Shield, Gauge, Globe, Activity,
  Target, BarChart3, Eye, Radio, Layers,
  ArrowUpRight, ArrowDownLeft, Clock, Flame
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie } from 'recharts'
import {
  fetchPowerPredict, fetchMlPredict, fetchMarketRegime,
  fetchGlobalAnalysis, fetchGlobalIndiaImpact
} from '../services/api'
import { useApp } from '../context/AppContext'

const PowerPredictor = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [powerPred, setPowerPred] = useState(null)
  const [mlPred, setMlPred] = useState(null)
  const [regime, setRegime] = useState(null)
  const [globalAnalysis, setGlobalAnalysis] = useState(null)
  const [globalImpact, setGlobalImpact] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('power')
  const [selectedIndex, setSelectedIndex] = useState('NIFTY')

  const symbolMap = { NIFTY: '^NSEI', SENSEX: '^BSESN', BANKNIFTY: '^NSEBANK' }

  const loadPower = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const [predRes, regRes] = await Promise.all([
        fetchPowerPredict(selectedIndex).catch(() => null),
        fetchMarketRegime().catch(() => null)
      ])
      setPowerPred(predRes?.data?.data || predRes?.data || null)
      setRegime(regRes?.data?.data || regRes?.data || null)
      addNotification?.('Power prediction ready!', 'success')
      hapticFeedback?.('success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadMl = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const res = await fetchMlPredict(symbolMap[selectedIndex] || '^NSEI', selectedIndex)
      setMlPred(res?.data?.data || res?.data || null)
      addNotification?.('ML prediction ready!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadGlobal = async () => {
    setLoading(true)
    hapticFeedback?.('impact')
    try {
      const [gRes, impactRes] = await Promise.all([
        fetchGlobalAnalysis().catch(() => null),
        fetchGlobalIndiaImpact().catch(() => null)
      ])
      setGlobalAnalysis(gRes?.data?.data || gRes?.data || null)
      setGlobalImpact(impactRes?.data?.data || impactRes?.data || null)
      addNotification?.('Global analysis ready!', 'success')
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    if (activeTab === 'power') loadPower()
    else if (activeTab === 'ml') loadMl()
    else if (activeTab === 'global') loadGlobal()
  }, [selectedIndex])

  const tabs = [
    { key: 'power', label: '10-Signal AI' },
    { key: 'ml', label: 'ML Ensemble' },
    { key: 'regime', label: 'Regime' },
    { key: 'global', label: 'Global' },
  ]

  const verdictColor = (v) => {
    if (!v) return 'text-slate-400'
    const vl = v.toLowerCase()
    if (vl.includes('strong') && vl.includes('bull')) return 'text-emerald-300'
    if (vl.includes('bull') || vl.includes('buy') || vl.includes('up')) return 'text-emerald-400'
    if (vl.includes('strong') && vl.includes('bear')) return 'text-red-300'
    if (vl.includes('bear') || vl.includes('sell') || vl.includes('down')) return 'text-red-400'
    return 'text-amber-400'
  }

  const verdictBg = (v) => {
    if (!v) return 'from-slate-600/20 to-slate-700/20'
    const vl = v.toLowerCase()
    if (vl.includes('bull') || vl.includes('buy') || vl.includes('up')) return 'from-emerald-600/20 to-emerald-700/10'
    if (vl.includes('bear') || vl.includes('sell') || vl.includes('down')) return 'from-red-600/20 to-red-700/10'
    return 'from-amber-600/20 to-amber-700/10'
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold flex items-center space-x-2">
            <Brain size={20} className="text-purple-400" />
            <span>Power Predictor</span>
          </h1>
          <p className="text-[10px] text-slate-400">10-Signal AI + 6-Model ML + LSTM + SHAP + Global</p>
        </div>
        <button onClick={() => {
          if (activeTab === 'power') loadPower()
          else if (activeTab === 'ml') loadMl()
          else loadGlobal()
        }} className="p-2 bg-slate-800 rounded-full"><RefreshCw size={16} className="text-purple-400" /></button>
      </div>

      {/* Index Selector */}
      <div className="flex space-x-2 mb-3">
        {['NIFTY', 'SENSEX', 'BANKNIFTY'].map(idx => (
          <button key={idx} onClick={() => setSelectedIndex(idx)}
            className={`flex-1 py-1.5 rounded-xl text-[10px] font-bold transition-all ${
              selectedIndex === idx ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{idx}</button>
        ))}
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-3">
        {tabs.map(t => (
          <button key={t.key} onClick={() => {
            setActiveTab(t.key)
            if (t.key === 'power' && !powerPred) loadPower()
            else if (t.key === 'ml' && !mlPred) loadMl()
            else if (t.key === 'global' && !globalAnalysis) loadGlobal()
          }}
            className={`flex-1 py-1.5 rounded-lg text-[9px] font-medium ${
              activeTab === t.key ? 'bg-purple-600 text-white' : 'text-slate-400'
            }`}>{t.label}</button>
        ))}
      </div>

      {loading && (
        <div className="text-center py-12">
          <Brain size={32} className="mx-auto text-purple-400 animate-pulse" />
          <p className="text-sm text-slate-400 mt-2">AI analyzing {selectedIndex}...</p>
          <p className="text-[10px] text-slate-500">Running 10 signal engines</p>
        </div>
      )}

      {/* POWER TAB - 10 Signal Prediction */}
      {activeTab === 'power' && !loading && (
        <div className="space-y-3">
          {powerPred ? (
            <>
              {/* Main Verdict */}
              <div className={`bg-gradient-to-br ${verdictBg(powerPred.verdict || powerPred.direction)} rounded-xl p-4 text-center border border-slate-700`}>
                <p className="text-[10px] text-slate-400 mb-1">10-SIGNAL ULTRA PREDICTION</p>
                <p className={`text-3xl font-bold ${verdictColor(powerPred.verdict || powerPred.direction)}`}>
                  {powerPred.verdict || powerPred.direction || 'NEUTRAL'}
                </p>
                {powerPred.confidence && (
                  <div className="mt-3 max-w-xs mx-auto">
                    <div className="flex justify-between text-[10px] mb-1">
                      <span className="text-slate-400">AI Confidence</span>
                      <span className="font-bold">{powerPred.confidence}%</span>
                    </div>
                    <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${
                        powerPred.confidence > 75 ? 'bg-emerald-500' : powerPred.confidence > 50 ? 'bg-amber-500' : 'bg-red-500'
                      }`} style={{ width: `${powerPred.confidence}%` }} />
                    </div>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-2 mt-3 text-[10px]">
                  {powerPred.target && <div><p className="text-slate-500">Target</p><p className="text-emerald-400 font-bold">{powerPred.target}</p></div>}
                  {powerPred.stop_loss && <div><p className="text-slate-500">Stop Loss</p><p className="text-red-400 font-bold">{powerPred.stop_loss}</p></div>}
                  {powerPred.risk_reward && <div><p className="text-slate-500">R:R</p><p className="text-amber-400 font-bold">{powerPred.risk_reward}</p></div>}
                </div>
              </div>

              {/* Signals Breakdown */}
              {powerPred.signals && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">10 Signal Breakdown</h3>
                  <div className="space-y-1.5">
                    {Object.entries(powerPred.signals).map(([key, sig]) => {
                      const sigStr = typeof sig === 'string' ? sig : sig?.signal || sig?.direction || sig?.value || JSON.stringify(sig)
                      const isBull = sigStr.toLowerCase().includes('bull') || sigStr.toLowerCase().includes('buy') || sigStr.toLowerCase().includes('up')
                      const weight = typeof sig === 'object' ? sig?.weight : null
                      return (
                        <div key={key} className="flex items-center justify-between bg-slate-700/30 rounded-lg p-2">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${isBull ? 'bg-emerald-400' : 'bg-red-400'}`} />
                            <span className="text-[10px] text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`text-[10px] font-bold ${isBull ? 'text-emerald-400' : 'text-red-400'}`}>
                              {String(sigStr).substring(0, 25)}
                            </span>
                            {weight && <span className="text-[8px] text-slate-500">{weight}x</span>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {powerPred.analysis && (
                <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-1">AI Analysis</h3>
                  <p className="text-[10px] text-slate-300 leading-relaxed">{typeof powerPred.analysis === 'string' ? powerPred.analysis : JSON.stringify(powerPred.analysis)}</p>
                </div>
              )}
            </>
          ) : !loading && (
            <button onClick={loadPower}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-6 text-center active:scale-[0.98]">
              <Brain size={40} className="mx-auto mb-2" />
              <p className="font-bold">Run 10-Signal Prediction</p>
              <p className="text-[10px] opacity-70 mt-1">ML + Technical + FII + VIX + PCR + Candles + Pivots + GIFT + News + Global</p>
            </button>
          )}
        </div>
      )}

      {/* ML TAB - 6-Model Ensemble */}
      {activeTab === 'ml' && !loading && (
        <div className="space-y-3">
          {mlPred ? (
            <>
              {/* ML Verdict */}
              <div className={`bg-gradient-to-br ${verdictBg(mlPred.prediction || mlPred.direction)} rounded-xl p-4 text-center border border-slate-700`}>
                <p className="text-[10px] text-slate-400 mb-1">6-MODEL ML ENSEMBLE + LSTM</p>
                <p className={`text-3xl font-bold ${verdictColor(mlPred.prediction || mlPred.direction)}`}>
                  {mlPred.prediction || mlPred.direction || 'NEUTRAL'}
                </p>
                {mlPred.probability !== undefined && (
                  <p className="text-sm text-slate-300 mt-1">Probability: {typeof mlPred.probability === 'number' ? (mlPred.probability * 100).toFixed(1) : mlPred.probability}%</p>
                )}
                {mlPred.predicted_range && (
                  <p className="text-xs text-blue-400 mt-1">Range: {typeof mlPred.predicted_range === 'string' ? mlPred.predicted_range : JSON.stringify(mlPred.predicted_range)}</p>
                )}
              </div>

              {/* Individual Model Results */}
              {mlPred.models && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">Individual Model Votes</h3>
                  <div className="space-y-1.5">
                    {(Array.isArray(mlPred.models) ? mlPred.models : Object.entries(mlPred.models).map(([k, v]) => ({ name: k, ...(typeof v === 'object' ? v : { prediction: v }) }))).map((m, i) => {
                      const modelName = m.name || m.model || 'Model ' + (i + 1)
                      const pred = m.prediction || m.direction || m.vote || '--'
                      const conf = m.confidence || m.probability || m.accuracy
                      const isBull = String(pred).toLowerCase().includes('bull') || String(pred).toLowerCase().includes('up') || String(pred).toLowerCase().includes('buy')
                      return (
                        <div key={i} className="flex items-center justify-between bg-slate-700/30 rounded-lg p-2">
                          <span className="text-[10px] text-slate-400 capitalize">{String(modelName).replace(/_/g, ' ')}</span>
                          <div className="flex items-center space-x-2">
                            <span className={`text-[10px] font-bold ${isBull ? 'text-emerald-400' : 'text-red-400'}`}>{String(pred).substring(0, 15)}</span>
                            {conf && <span className="text-[8px] text-slate-500">{typeof conf === 'number' ? (conf > 1 ? conf.toFixed(0) + '%' : (conf * 100).toFixed(0) + '%') : conf}</span>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* SHAP Feature Importance */}
              {mlPred.feature_importance && (
                <div className="bg-slate-800 border border-blue-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">SHAP Feature Importance</h3>
                  <div className="space-y-1">
                    {(Array.isArray(mlPred.feature_importance) ? mlPred.feature_importance : Object.entries(mlPred.feature_importance).map(([k, v]) => ({ feature: k, importance: v }))).slice(0, 10).map((f, i) => {
                      const fname = f.feature || f.name || 'Feature ' + (i + 1)
                      const imp = typeof f.importance === 'number' ? f.importance : typeof f.value === 'number' ? f.value : 0
                      const maxImp = Math.max(...(Array.isArray(mlPred.feature_importance) ? mlPred.feature_importance : Object.values(mlPred.feature_importance)).map(x => Math.abs(typeof x === 'number' ? x : x?.importance || x?.value || 0)))
                      const pct = maxImp > 0 ? (Math.abs(imp) / maxImp) * 100 : 50
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-[9px] mb-0.5">
                            <span className="text-slate-400 capitalize">{String(fname).replace(/_/g, ' ')}</span>
                            <span className="font-medium">{typeof imp === 'number' ? imp.toFixed(4) : imp}</span>
                          </div>
                          <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, pct)}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {mlPred.summary && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3">
                  <p className="text-[10px] text-blue-300">{typeof mlPred.summary === 'string' ? mlPred.summary : JSON.stringify(mlPred.summary)}</p>
                </div>
              )}

              {/* Fallback for unknown structures */}
              {!mlPred.models && !mlPred.feature_importance && typeof mlPred === 'object' && (
                <div className="bg-slate-800 rounded-xl p-3 space-y-1">
                  {Object.entries(mlPred).filter(([k]) => !['prediction','direction','probability','predicted_range','summary'].includes(k)).slice(0, 15).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{typeof v === 'object' ? JSON.stringify(v).substring(0, 40) : String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : !loading && (
            <button onClick={loadMl}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl p-6 text-center active:scale-[0.98]">
              <Activity size={40} className="mx-auto mb-2" />
              <p className="font-bold">Run ML Ensemble</p>
              <p className="text-[10px] opacity-70 mt-1">RandomForest + XGBoost + LightGBM + GradBoost + ExtraTrees + LSTM</p>
            </button>
          )}
        </div>
      )}

      {/* REGIME TAB */}
      {activeTab === 'regime' && !loading && (
        <div className="space-y-3">
          {regime ? (
            <>
              <div className={`bg-gradient-to-br ${verdictBg(regime.regime)} rounded-xl p-4 text-center border border-slate-700`}>
                <p className="text-[10px] text-slate-400 mb-1">8-COMPONENT MARKET REGIME</p>
                <p className={`text-2xl font-bold ${verdictColor(regime.regime)}`}>
                  {regime.regime || 'UNKNOWN'}
                </p>
                {regime.confidence && <p className="text-xs text-slate-300 mt-1">{regime.confidence}% confidence</p>}
                {regime.description && <p className="text-[10px] text-slate-400 mt-2">{regime.description}</p>}
              </div>

              {/* Regime Components */}
              {regime.components && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">Regime Components</h3>
                  <div className="space-y-1">
                    {(Array.isArray(regime.components) ? regime.components : Object.entries(regime.components).map(([k, v]) => ({ name: k, value: v }))).slice(0, 8).map((c, i) => {
                      const cName = c.name || c.component || 'Component ' + (i + 1)
                      const cVal = c.value || c.signal || c.score || '--'
                      return (
                        <div key={i} className="flex justify-between items-center bg-slate-700/30 rounded-lg p-2 text-[10px]">
                          <span className="text-slate-400 capitalize">{String(cName).replace(/_/g, ' ')}</span>
                          <span className={`font-bold ${verdictColor(String(cVal))}`}>{String(cVal).substring(0, 30)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Trading Parameters */}
              {regime.trading_params && (
                <div className="bg-slate-800 border border-amber-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">Regime-Adapted Trading Params</h3>
                  <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                    {Object.entries(regime.trading_params).slice(0, 8).map(([k, v]) => (
                      <div key={k} className="bg-slate-700/50 rounded p-1.5">
                        <p className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}</p>
                        <p className="font-bold">{typeof v === 'number' ? v.toFixed(2) : String(v).substring(0, 20)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {regime.recommendation && (
                <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-1">Regime Strategy</h3>
                  <p className="text-[10px] text-slate-300">{typeof regime.recommendation === 'string' ? regime.recommendation : JSON.stringify(regime.recommendation)}</p>
                </div>
              )}

              {/* Fallback */}
              {!regime.components && !regime.trading_params && typeof regime === 'object' && (
                <div className="bg-slate-800 rounded-xl p-3 space-y-1">
                  {Object.entries(regime).filter(([k]) => !['regime','confidence','description','recommendation'].includes(k)).slice(0, 12).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{typeof v === 'object' ? JSON.stringify(v).substring(0, 40) : String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : !loading && (
            <button onClick={loadPower}
              className="w-full bg-gradient-to-r from-amber-600 to-orange-600 rounded-xl p-6 text-center active:scale-[0.98]">
              <Gauge size={40} className="mx-auto mb-2" />
              <p className="font-bold">Detect Market Regime</p>
              <p className="text-[10px] opacity-70 mt-1">8 regimes: Strong Bull to Strong Bear + Volatile/Accumulation/Distribution</p>
            </button>
          )}
        </div>
      )}

      {/* GLOBAL TAB */}
      {activeTab === 'global' && !loading && (
        <div className="space-y-3">
          {globalImpact ? (
            <>
              <div className={`bg-gradient-to-br ${verdictBg(globalImpact.prediction || globalImpact.verdict)} rounded-xl p-4 text-center border border-slate-700`}>
                <p className="text-[10px] text-slate-400 mb-1">GLOBAL MARKETS IMPACT ON INDIA</p>
                <p className={`text-2xl font-bold ${verdictColor(globalImpact.prediction || globalImpact.verdict)}`}>
                  {globalImpact.prediction || globalImpact.verdict || 'NEUTRAL'}
                </p>
                {globalImpact.impact_score && <p className="text-xs text-slate-300 mt-1">Impact Score: {globalImpact.impact_score}/10</p>}
              </div>

              {/* Global Markets */}
              {globalImpact.markets && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">Global Markets</h3>
                  <div className="space-y-1">
                    {(Array.isArray(globalImpact.markets) ? globalImpact.markets : Object.entries(globalImpact.markets).map(([k, v]) => ({ name: k, ...(typeof v === 'object' ? v : { change: v }) }))).slice(0, 12).map((m, i) => {
                      const mChange = m.change || m.change_pct || 0
                      return (
                        <div key={i} className="flex items-center justify-between bg-slate-700/30 rounded-lg p-1.5 text-[10px]">
                          <span className="text-slate-400">{m.name || m.market || 'Market'}</span>
                          <span className={`font-bold ${Number(mChange) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {Number(mChange) >= 0 ? '+' : ''}{typeof mChange === 'number' ? mChange.toFixed(2) : mChange}%
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {globalImpact.factors && (
                <div className="bg-slate-800 border border-blue-500/20 rounded-xl p-3">
                  <h3 className="font-bold text-xs mb-2">Impact Factors</h3>
                  {Object.entries(globalImpact.factors).slice(0, 8).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}

              {globalImpact.analysis && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3">
                  <p className="text-[10px] text-blue-300">{typeof globalImpact.analysis === 'string' ? globalImpact.analysis : JSON.stringify(globalImpact.analysis)}</p>
                </div>
              )}

              {/* Fallback */}
              {!globalImpact.markets && !globalImpact.factors && typeof globalImpact === 'object' && (
                <div className="bg-slate-800 rounded-xl p-3 space-y-1">
                  {Object.entries(globalImpact).filter(([k]) => !['prediction','verdict','impact_score','analysis'].includes(k)).slice(0, 15).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px] py-0.5 border-b border-slate-700 last:border-0">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{typeof v === 'object' ? JSON.stringify(v).substring(0, 40) : String(v).substring(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : !loading && (
            <button onClick={loadGlobal}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-center active:scale-[0.98]">
              <Globe size={40} className="mx-auto mb-2" />
              <p className="font-bold">Analyze Global Impact</p>
              <p className="text-[10px] opacity-70 mt-1">22 global markets + 5 commodities impact on India</p>
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default PowerPredictor
