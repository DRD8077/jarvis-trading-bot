import React, { useState, useEffect } from 'react'
import {
  Fish, AlertTriangle, TrendingUp, TrendingDown, RefreshCw,
  Activity, Eye, ArrowUpRight, ArrowDownLeft, Clock, Waves,
  Filter, Zap
} from 'lucide-react'
import { fetchWhaleAlert, fetchWhaleScan, fetchWhaleOnchain } from '../services/api'
import { useApp } from '../context/AppContext'

const WhaleAlerts = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [alerts, setAlerts] = useState([])
  const [scanResult, setScanResult] = useState(null)
  const [onchain, setOnchain] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('alerts')
  const [filter, setFilter] = useState('all')

  const load = async () => {
    setLoading(true)
    try {
      const [alertRes, scanRes, onchainRes] = await Promise.all([
        fetchWhaleAlert().catch(() => null),
        fetchWhaleScan().catch(() => null),
        fetchWhaleOnchain().catch(() => null)
      ])
      const alertList = alertRes?.data?.data || alertRes?.data?.alerts || []
      setAlerts(alertList)
      setScanResult(scanRes?.data?.data || scanRes?.data || null)
      setOnchain(onchainRes?.data?.data || onchainRes?.data?.transactions || [])
      // JARVIS voice — announce whale activity
      if (alertList.length > 0) {
        try {
          const bigAlert = alertList[0]
          const amount = bigAlert?.amount || bigAlert?.value || ''
          const symbol = bigAlert?.symbol || bigAlert?.currency || 'crypto'
          window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: `Sir, whale alert! ${alertList.length} bade transactions detect hue. ${symbol} mein ${amount ? amount + ' ka' : 'bada'} movement hai. Dhyan rakhiye!`, priority: 'normal' } }))
        } catch {}
      }
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  // ⚡ Auto-refresh whale alerts every 15s
  useEffect(() => {
    const iv = setInterval(load, 15000)
    return () => clearInterval(iv)
  }, [])

  const filteredAlerts = filter === 'all' ? alerts :
    alerts.filter(a => (a.type || a.direction || '').toLowerCase().includes(filter))

  const formatAmount = (n) => {
    if (!n) return '--'
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
    return `$${n.toFixed(0)}`
  }

  const tabs = [
    { key: 'alerts', label: '🐋 Alerts', icon: Fish },
    { key: 'onchain', label: '⛓️ On-Chain', icon: Activity },
    { key: 'scan', label: '🔍 Scanner', icon: Eye },
  ]

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      {[1,2,3,4].map(i => <div key={i} className="skeleton h-20 rounded-xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
              <Waves size={16} />
            </div>
            <span>Whale Alerts</span>
          </h1>
          <p className="text-slate-400 text-sm">Track big money moves</p>
        </div>
        <button onClick={load} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-cyan-400" />
        </button>
      </div>

      {/* Stats */}
      {scanResult && (
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
            <p className="text-[10px] text-emerald-400">Buying</p>
            <p className="text-sm font-bold text-emerald-400">{formatAmount(scanResult.total_buying || 0)}</p>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center">
            <p className="text-[10px] text-red-400">Selling</p>
            <p className="text-sm font-bold text-red-400">{formatAmount(scanResult.total_selling || 0)}</p>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-center">
            <p className="text-[10px] text-blue-400">Net Flow</p>
            <p className={`text-sm font-bold ${(scanResult.net_flow || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {formatAmount(scanResult.net_flow || 0)}
            </p>
          </div>
        </div>
      )}

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-4">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
              activeTab === t.key ? 'bg-cyan-600 text-white' : 'text-slate-400'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* ALERTS TAB */}
      {activeTab === 'alerts' && (
        <div className="space-y-3">
          {/* Filter Pills */}
          <div className="flex space-x-2 overflow-x-auto pb-1">
            {['all', 'buy', 'sell', 'transfer'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`shrink-0 px-3 py-1 rounded-full text-[10px] font-medium capitalize ${
                  filter === f ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}>{f}</button>
            ))}
          </div>

          {filteredAlerts.length === 0 ? (
            <div className="text-center py-12">
              <Fish size={48} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500">No whale alerts detected</p>
              <p className="text-xs text-slate-600">Monitoring blockchain for large transactions...</p>
            </div>
          ) : filteredAlerts.map((a, i) => {
            const isBuy = (a.type || a.direction || '').toLowerCase().includes('buy') ||
                         (a.type || a.direction || '').toLowerCase().includes('accumul')
            return (
              <div key={i} className={`bg-slate-800 border rounded-xl p-3 ${
                isBuy ? 'border-emerald-500/20' : 'border-red-500/20'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                      isBuy ? 'bg-emerald-500/20' : 'bg-red-500/20'
                    }`}>
                      {isBuy ? <ArrowDownLeft size={16} className="text-emerald-400" /> : <ArrowUpRight size={16} className="text-red-400" />}
                    </div>
                    <div>
                      <p className="font-bold text-sm">{a.symbol || a.coin || a.asset || '???'}</p>
                      <div className="flex items-center space-x-1 text-[10px] text-slate-500">
                        <Clock size={8} />
                        <span>{a.time || a.timestamp || 'Just now'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{formatAmount(a.amount || a.value || 0)}</p>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      isBuy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{a.type || a.direction || (isBuy ? 'BUY' : 'SELL')}</span>
                  </div>
                </div>
                {(a.from || a.to) && (
                  <div className="text-[10px] text-slate-500 flex items-center space-x-1">
                    <span className="truncate max-w-[120px]">{a.from || 'Unknown'}</span>
                    <span>→</span>
                    <span className="truncate max-w-[120px]">{a.to || 'Unknown'}</span>
                  </div>
                )}
                {a.impact && (
                  <p className="text-[10px] mt-1 text-cyan-400">💡 {a.impact}</p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ON-CHAIN TAB */}
      {activeTab === 'onchain' && (
        <div className="space-y-2">
          {onchain.length === 0 ? (
            <p className="text-center text-slate-500 py-12 text-sm">No on-chain data available</p>
          ) : onchain.map((tx, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity size={14} className="text-cyan-400" />
                <div>
                  <p className="text-sm font-medium">{tx.type || tx.action || 'Transfer'}</p>
                  <p className="text-[10px] text-slate-500">{tx.blockchain || tx.chain || 'Multi-chain'}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold">{formatAmount(tx.amount || tx.value || 0)}</p>
                <p className="text-[10px] text-slate-500">{tx.time || ''}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SCANNER TAB */}
      {activeTab === 'scan' && (
        <div className="space-y-3">
          {!scanResult ? (
            <p className="text-center text-slate-500 py-12 text-sm">Scanner running...</p>
          ) : (
            <>
              {(scanResult.top_accumulation || []).length > 0 && (
                <div className="bg-slate-800 border border-emerald-500/20 rounded-xl p-4">
                  <h3 className="font-bold text-sm mb-3 flex items-center space-x-2">
                    <TrendingUp size={14} className="text-emerald-400" />
                    <span className="text-emerald-400">Top Accumulation</span>
                  </h3>
                  {scanResult.top_accumulation.map((t, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0 text-sm">
                      <span className="font-medium">{t.symbol || t.coin || `#${i+1}`}</span>
                      <span className="text-emerald-400 font-bold">{formatAmount(t.amount || 0)}</span>
                    </div>
                  ))}
                </div>
              )}
              {(scanResult.top_distribution || []).length > 0 && (
                <div className="bg-slate-800 border border-red-500/20 rounded-xl p-4">
                  <h3 className="font-bold text-sm mb-3 flex items-center space-x-2">
                    <TrendingDown size={14} className="text-red-400" />
                    <span className="text-red-400">Top Distribution</span>
                  </h3>
                  {scanResult.top_distribution.map((t, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0 text-sm">
                      <span className="font-medium">{t.symbol || t.coin || `#${i+1}`}</span>
                      <span className="text-red-400 font-bold">{formatAmount(t.amount || 0)}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default WhaleAlerts
