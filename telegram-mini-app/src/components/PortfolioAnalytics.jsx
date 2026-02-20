import React, { useState, useEffect } from 'react'
import {
  PieChart, LineChart, TrendingUp, TrendingDown, DollarSign,
  RefreshCw, Plus, ArrowUpRight, ArrowDownLeft, BarChart3,
  Calculator, Wallet, Target, ShieldCheck, Percent, Download, FileText
} from 'lucide-react'
import { PieChart as RechartsP, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import {
  fetchCombinedPortfolio, fetchPortfolioPnl, fetchPortfolioTax,
  addPortfolioHolding, sellPortfolioHolding
} from '../services/api'
import { useApp } from '../context/AppContext'
import exportEngine from '../services/exportEngine'

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16']

const PortfolioAnalytics = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const userId = String(user?.id || '')
  const [portfolio, setPortfolio] = useState(null)
  const [pnl, setPnl] = useState(null)
  const [tax, setTax] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [showAdd, setShowAdd] = useState(false)
  const [addForm, setAddForm] = useState({ symbol: '', quantity: '', price: '', exchange: 'crypto' })

  const load = async () => {
    setLoading(true)
    try {
      const [portRes, pnlRes, taxRes] = await Promise.all([
        fetchCombinedPortfolio(userId).catch(() => null),
        fetchPortfolioPnl(userId).catch(() => null),
        fetchPortfolioTax(userId).catch(() => null)
      ])
      setPortfolio(portRes?.data?.data || portRes?.data || null)
      setPnl(pnlRes?.data?.data || pnlRes?.data || null)
      setTax(taxRes?.data?.data || taxRes?.data || null)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  // ⚡ Auto-refresh portfolio every 20s
  useEffect(() => {
    const iv = setInterval(load, 20000)
    return () => clearInterval(iv)
  }, [])

  const handleAdd = async () => {
    if (!addForm.symbol || !addForm.quantity) { addNotification('Fill symbol & quantity', 'error'); return }
    hapticFeedback('impact')
    try {
      await addPortfolioHolding({ user_id: userId, symbol: addForm.symbol, quantity: parseFloat(addForm.quantity), price: parseFloat(addForm.price) || 0, exchange: addForm.exchange })
      addNotification(`Added ${addForm.symbol} to portfolio!`, 'success')
      hapticFeedback('success')
      setShowAdd(false)
      setAddForm({ symbol: '', quantity: '', price: '', exchange: 'crypto' })
      load()
    } catch (e) { addNotification('Failed to add', 'error') }
  }

  const totalValue = portfolio?.total_value || 0
  const totalPnl = portfolio?.total_pnl || pnl?.total_pnl || 0
  const totalPnlPct = portfolio?.total_pnl_pct || pnl?.total_pnl_pct || 0
  const holdings = portfolio?.holdings || portfolio?.assets || []
  const pnlHistory = pnl?.history || pnl?.daily || []

  // Prepare chart data
  const pieData = holdings.slice(0, 8).map((h, i) => ({
    name: h.symbol || h.name || `Asset ${i}`,
    value: h.value || h.current_value || 1
  }))

  const areaData = pnlHistory.map(d => ({
    date: d.date || d.day || '',
    pnl: d.pnl || d.cumulative || d.value || 0
  }))

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      <div className="skeleton h-36 rounded-2xl" />
      <div className="skeleton h-48 rounded-2xl" />
      {[1,2,3].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-violet-500 to-purple-500 rounded-lg flex items-center justify-center">
              <PieChart size={16} />
            </div>
            <span>Portfolio</span>
          </h1>
          <p className="text-slate-400 text-sm">Cross-asset analytics</p>
        </div>
        <div className="flex items-center space-x-2">
          <button onClick={() => {
            exportEngine.exportPortfolio(holdings)
            hapticFeedback('success')
            addNotification('Portfolio CSV downloading...', 'success')
          }} className="p-2 bg-emerald-600 rounded-full" title="Export CSV">
            <Download size={16} />
          </button>
          <button onClick={() => {
            const report = exportEngine.generatePnLSummary(holdings, [])
            exportEngine.exportPDF(report)
            hapticFeedback('success')
          }} className="p-2 bg-blue-600 rounded-full" title="PDF Report">
            <FileText size={16} />
          </button>
          <button onClick={() => setShowAdd(!showAdd)} className="p-2 bg-violet-600 rounded-full">
            <Plus size={18} />
          </button>
          <button onClick={load} className="p-2 bg-slate-800 rounded-full">
            <RefreshCw size={18} className="text-violet-400" />
          </button>
        </div>
      </div>

      {/* Value Card */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl p-5 mb-4 shadow-lg shadow-violet-500/20">
        <p className="text-xs text-purple-200 mb-1">Total Portfolio Value</p>
        <p className="text-3xl font-bold mb-2">${totalValue.toLocaleString()}</p>
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-bold ${
            totalPnl >= 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
          }`}>
            {totalPnl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            <span>{totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)}</span>
            <span>({totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%)</span>
          </div>
        </div>
      </div>

      {/* Add Asset Form */}
      {showAdd && (
        <div className="bg-slate-800 border border-violet-500/30 rounded-xl p-4 mb-4 space-y-3">
          <h3 className="font-bold text-sm">Add Asset</h3>
          <div className="flex space-x-2">
            {['crypto', 'stocks', 'defi'].map(e => (
              <button key={e} onClick={() => setAddForm(p => ({ ...p, exchange: e }))}
                className={`flex-1 py-1.5 rounded-lg text-xs capitalize ${
                  addForm.exchange === e ? 'bg-violet-600' : 'bg-slate-700'
                }`}>{e}</button>
            ))}
          </div>
          <input value={addForm.symbol} onChange={e => setAddForm(p => ({ ...p, symbol: e.target.value }))}
            placeholder="Symbol (BTC, ETH, NIFTY...)" className="w-full bg-slate-700 rounded-lg px-3 py-2 text-sm outline-none" />
          <div className="grid grid-cols-2 gap-2">
            <input value={addForm.quantity} onChange={e => setAddForm(p => ({ ...p, quantity: e.target.value }))}
              placeholder="Quantity" type="number" className="bg-slate-700 rounded-lg px-3 py-2 text-sm outline-none" />
            <input value={addForm.price} onChange={e => setAddForm(p => ({ ...p, price: e.target.value }))}
              placeholder="Buy Price" type="number" className="bg-slate-700 rounded-lg px-3 py-2 text-sm outline-none" />
          </div>
          <button onClick={handleAdd} className="w-full bg-violet-600 py-2.5 rounded-lg text-sm font-bold">Add to Portfolio</button>
        </div>
      )}

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-4">
        {['overview', 'holdings', 'pnl', 'tax'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`flex-1 py-2 rounded-lg text-xs font-medium capitalize transition-all ${
              activeTab === t ? 'bg-violet-600 text-white' : 'text-slate-400'
            }`}>{t}</button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Pie Chart */}
          {pieData.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="font-bold text-sm mb-2">Allocation</h3>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsP>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                      paddingAngle={2} dataKey="value">
                      {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </RechartsP>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {pieData.map((d, i) => (
                  <div key={i} className="flex items-center space-x-1">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-[10px] text-slate-400">{d.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* P&L Graph */}
          {areaData.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="font-bold text-sm mb-2">P&L Curve</h3>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={areaData}>
                    <defs>
                      <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 9, fill: '#64748b' }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="pnl" stroke="#8b5cf6" fill="url(#pnlGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* HOLDINGS TAB */}
      {activeTab === 'holdings' && (
        <div className="space-y-2">
          {holdings.length === 0 ? (
            <div className="text-center py-12">
              <Wallet size={40} className="mx-auto text-slate-600 mb-2" />
              <p className="text-slate-500 text-sm">No holdings yet. Tap + to add.</p>
            </div>
          ) : holdings.map((h, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" 
                    style={{ backgroundColor: COLORS[i % COLORS.length] + '30', color: COLORS[i % COLORS.length] }}>
                    {(h.symbol || '?')[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{h.symbol || h.name}</p>
                    <p className="text-[10px] text-slate-500">{h.quantity || 0} × ${h.current_price || h.price || 0}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">${(h.value || h.current_value || 0).toFixed(2)}</p>
                  <p className={`text-[10px] font-medium ${(h.pnl || h.pnl_pct || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(h.pnl || h.pnl_pct || 0) >= 0 ? '+' : ''}{(h.pnl_pct || h.pnl || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PNL TAB */}
      {activeTab === 'pnl' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
              <p className="text-[10px] text-emerald-400">Realized P&L</p>
              <p className="text-lg font-bold text-emerald-400">${(pnl?.realized || 0).toFixed(2)}</p>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-center">
              <p className="text-[10px] text-blue-400">Unrealized P&L</p>
              <p className="text-lg font-bold text-blue-400">${(pnl?.unrealized || 0).toFixed(2)}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-slate-800 rounded-xl p-3 text-center">
              <p className="text-[10px] text-slate-500">Best Trade</p>
              <p className="text-xs font-bold text-emerald-400">{pnl?.best_trade || '--'}</p>
            </div>
            <div className="bg-slate-800 rounded-xl p-3 text-center">
              <p className="text-[10px] text-slate-500">Worst Trade</p>
              <p className="text-xs font-bold text-red-400">{pnl?.worst_trade || '--'}</p>
            </div>
            <div className="bg-slate-800 rounded-xl p-3 text-center">
              <p className="text-[10px] text-slate-500">Max Drawdown</p>
              <p className="text-xs font-bold text-amber-400">{pnl?.max_drawdown || '--'}%</p>
            </div>
          </div>
        </div>
      )}

      {/* TAX TAB */}
      {activeTab === 'tax' && (
        <div className="space-y-3">
          {!tax ? (
            <p className="text-center text-slate-500 py-12 text-sm">Tax data not available</p>
          ) : (
            <>
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                <h3 className="font-bold text-sm mb-3 flex items-center space-x-2">
                  <Calculator size={16} className="text-amber-400" />
                  <span>Tax Summary (Estimated)</span>
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-400">Short-term gains</span><span className="font-medium">${tax.short_term || 0}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Long-term gains</span><span className="font-medium">${tax.long_term || 0}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Est. tax liability</span><span className="font-bold text-amber-400">${tax.estimated_tax || 0}</span></div>
                </div>
              </div>
              <p className="text-[10px] text-slate-600 text-center">* Estimates only. Consult a tax professional.</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default PortfolioAnalytics
