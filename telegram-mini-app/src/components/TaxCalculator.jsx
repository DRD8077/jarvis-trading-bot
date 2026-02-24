/**
 * 💰 JARVIS Tax Calculator — Capital Gains for Indian Traders
 * ═══════════════════════════════════════════════════════════════
 * - Auto-import from paper trading & P&L journal
 * - STCG (15%) + LTCG (10% above ₹1L) calculation
 * - Crypto tax (30% flat) for VDA assets
 * - F&O profit (business income / slab rate)
 * - Generate tax report PDF-style
 * - Financial year selector
 * - Section 44AD presumptive taxation
 */
import React, { useState, useEffect, useMemo } from 'react'
import { 
  Calculator, FileText, Download, IndianRupee, TrendingUp, Calendar,
  PieChart, AlertTriangle, ChevronDown, Info
} from 'lucide-react'

const TAX_SLABS_NEW = [
  { limit: 300000, rate: 0 },
  { limit: 700000, rate: 5 },
  { limit: 1000000, rate: 10 },
  { limit: 1200000, rate: 15 },
  { limit: 1500000, rate: 20 },
  { limit: Infinity, rate: 30 },
]

const TaxCalculator = () => {
  const [fy, setFy] = useState('2025-26')
  const [trades, setTrades] = useState([])
  const [manualEntry, setManualEntry] = useState({
    type: 'equity_stcg', // equity_stcg, equity_ltcg, crypto, fno
    buyValue: '',
    sellValue: '',
    description: '',
  })
  const [showAdd, setShowAdd] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [otherIncome, setOtherIncome] = useState('')

  // Load from paper trading history
  useEffect(() => {
    try {
      const paperData = JSON.parse(localStorage.getItem('jarvis_paper_trading') || '{}')
      const tradeHistory = paperData.history || []
      const pnlData = JSON.parse(localStorage.getItem('jarvis_pnl_journal') || '[]')
      
      const imported = [...tradeHistory, ...pnlData]
        .filter(t => t.pnl !== undefined)
        .map(t => ({
          id: t.id || Date.now() + Math.random(),
          type: t.asset?.includes('BTC') || t.asset?.includes('ETH') || t.asset?.includes('SOL') ? 'crypto' :
                t.type === 'fno' ? 'fno' : 'equity_stcg',
          description: `${t.asset || t.symbol || 'Trade'} ${t.action || ''}`,
          buyValue: t.buyPrice || t.entryPrice || 0,
          sellValue: t.sellPrice || t.exitPrice || 0,
          profit: t.pnl || 0,
          date: t.time || t.date || new Date().toISOString(),
        }))
      
      const saved = JSON.parse(localStorage.getItem('jarvis_tax_trades') || '[]')
      setTrades([...saved, ...imported].filter((t, i, arr) => 
        arr.findIndex(x => x.id === t.id) === i
      ))
    } catch (e) {
      setTrades(JSON.parse(localStorage.getItem('jarvis_tax_trades') || '[]'))
    }
  }, [])

  // Save trades
  useEffect(() => {
    localStorage.setItem('jarvis_tax_trades', JSON.stringify(trades))
  }, [trades])

  // Calculate taxes
  const taxSummary = useMemo(() => {
    const grouped = {
      equity_stcg: { profit: 0, loss: 0, trades: 0 },
      equity_ltcg: { profit: 0, loss: 0, trades: 0 },
      crypto: { profit: 0, loss: 0, trades: 0 },
      fno: { profit: 0, loss: 0, trades: 0 },
    }

    trades.forEach(t => {
      const cat = grouped[t.type] || grouped.equity_stcg
      const pnl = t.profit || (parseFloat(t.sellValue) - parseFloat(t.buyValue)) || 0
      if (pnl >= 0) cat.profit += pnl
      else cat.loss += Math.abs(pnl)
      cat.trades++
    })

    // STCG: 15% on net equity short-term gains
    const stcgNet = Math.max(0, grouped.equity_stcg.profit - grouped.equity_stcg.loss)
    const stcgTax = stcgNet * 0.15

    // LTCG: 10% on gains above ₹1 lakh
    const ltcgNet = Math.max(0, grouped.equity_ltcg.profit - grouped.equity_ltcg.loss)
    const ltcgExempt = Math.min(ltcgNet, 100000)
    const ltcgTaxable = Math.max(0, ltcgNet - 100000)
    const ltcgTax = ltcgTaxable * 0.10

    // Crypto VDA: 30% flat, no loss offset, no deductions
    const cryptoProfit = grouped.crypto.profit // Loss cannot be offset
    const cryptoTax = cryptoProfit * 0.30
    const cryptoTds = cryptoProfit * 0.01 // 1% TDS on crypto

    // F&O: Treated as business income, taxed at slab rate
    const fnoNet = grouped.fno.profit - grouped.fno.loss
    const fnoTax = fnoNet > 0 ? calculateSlabTax(fnoNet + parseFloat(otherIncome || 0)) : 0

    const totalTax = stcgTax + ltcgTax + cryptoTax + fnoTax
    const totalProfit = stcgNet + ltcgNet + cryptoProfit + Math.max(0, fnoNet)
    const totalLoss = grouped.equity_stcg.loss + grouped.equity_ltcg.loss + grouped.crypto.loss + grouped.fno.loss
    const effectiveRate = totalProfit > 0 ? (totalTax / totalProfit * 100) : 0

    // Turnover for F&O (for audit purpose check)
    const fnoTurnover = grouped.fno.profit + grouped.fno.loss
    const needsAudit = fnoTurnover > 100000000 // ₹10Cr

    return {
      grouped,
      stcgNet, stcgTax,
      ltcgNet, ltcgTaxable, ltcgTax, ltcgExempt,
      cryptoProfit, cryptoTax, cryptoTds,
      fnoNet, fnoTax,
      totalTax, totalProfit, totalLoss,
      effectiveRate, fnoTurnover, needsAudit,
      totalTrades: trades.length,
    }
  }, [trades, otherIncome])

  function calculateSlabTax(income) {
    let remaining = income
    let tax = 0
    let prevLimit = 0
    for (const slab of TAX_SLABS_NEW) {
      const taxable = Math.min(remaining, slab.limit - prevLimit)
      if (taxable <= 0) break
      tax += taxable * (slab.rate / 100)
      remaining -= taxable
      prevLimit = slab.limit
    }
    return tax
  }

  const addTrade = () => {
    if (!manualEntry.buyValue || !manualEntry.sellValue) return
    const buy = parseFloat(manualEntry.buyValue)
    const sell = parseFloat(manualEntry.sellValue)
    setTrades(prev => [...prev, {
      id: Date.now(),
      type: manualEntry.type,
      description: manualEntry.description || manualEntry.type.replace('_', ' ').toUpperCase(),
      buyValue: buy,
      sellValue: sell,
      profit: sell - buy,
      date: new Date().toISOString(),
    }])
    setManualEntry({ type: 'equity_stcg', buyValue: '', sellValue: '', description: '' })
    setShowAdd(false)
  }

  const deleteTrade = (id) => {
    setTrades(prev => prev.filter(t => t.id !== id))
  }

  const exportReport = () => {
    const lines = [
      `JARVIS Tax Report — FY ${fy}`,
      `Generated: ${new Date().toLocaleDateString()}`,
      '',
      `Total Trades: ${taxSummary.totalTrades}`,
      `Total Profit: ₹${taxSummary.totalProfit.toLocaleString()}`,
      `Total Loss: ₹${taxSummary.totalLoss.toLocaleString()}`,
      '',
      '=== EQUITY (Short-Term) ===',
      `Net Gain: ₹${taxSummary.stcgNet.toLocaleString()}`,
      `Tax @ 15%: ₹${taxSummary.stcgTax.toLocaleString()}`,
      '',
      '=== EQUITY (Long-Term) ===',
      `Net Gain: ₹${taxSummary.ltcgNet.toLocaleString()}`,
      `Exempt (up to ₹1L): ₹${taxSummary.ltcgExempt.toLocaleString()}`,
      `Tax @ 10%: ₹${taxSummary.ltcgTax.toLocaleString()}`,
      '',
      '=== CRYPTO / VDA ===',
      `Profit: ₹${taxSummary.cryptoProfit.toLocaleString()}`,
      `Tax @ 30%: ₹${taxSummary.cryptoTax.toLocaleString()}`,
      `TDS @ 1%: ₹${taxSummary.cryptoTds.toLocaleString()}`,
      '',
      '=== F&O (Business Income) ===',
      `Net P&L: ₹${taxSummary.fnoNet.toLocaleString()}`,
      `Tax (slab): ₹${taxSummary.fnoTax.toLocaleString()}`,
      `Turnover: ₹${taxSummary.fnoTurnover.toLocaleString()}`,
      taxSummary.needsAudit ? '⚠️ AUDIT REQUIRED (turnover > ₹10Cr)' : '',
      '',
      `════════════════════════════`,
      `TOTAL TAX: ₹${taxSummary.totalTax.toLocaleString()}`,
      `Effective Rate: ${taxSummary.effectiveRate.toFixed(1)}%`,
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `jarvis_tax_report_${fy}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const fmt = (n) => `₹${Math.abs(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white p-4 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold">💰 Tax Calculator</h1>
          <p className="text-slate-500 text-xs">Indian trading tax estimation</p>
        </div>
        <select value={fy} onChange={e => setFy(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs">
          <option value="2025-26">FY 2025-26</option>
          <option value="2024-25">FY 2024-25</option>
          <option value="2023-24">FY 2023-24</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gradient-to-br from-emerald-900/30 to-emerald-800/10 border border-emerald-500/20 rounded-xl p-4">
          <p className="text-[10px] text-emerald-400/70">Total Profit</p>
          <p className="text-lg font-bold text-emerald-400">{fmt(taxSummary.totalProfit)}</p>
          <p className="text-[10px] text-slate-500">{taxSummary.totalTrades} trades</p>
        </div>
        <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-500/20 rounded-xl p-4">
          <p className="text-[10px] text-red-400/70">Total Tax</p>
          <p className="text-lg font-bold text-red-400">{fmt(taxSummary.totalTax)}</p>
          <p className="text-[10px] text-slate-500">Eff. rate: {taxSummary.effectiveRate.toFixed(1)}%</p>
        </div>
      </div>

      {/* Tax Breakdown */}
      <div className="space-y-2 mb-4">
        {[
          { label: 'Equity STCG (15%)', profit: taxSummary.stcgNet, tax: taxSummary.stcgTax, color: 'blue', info: 'Short-term: held < 1 year' },
          { label: 'Equity LTCG (10%)', profit: taxSummary.ltcgNet, tax: taxSummary.ltcgTax, color: 'purple', info: `₹${(taxSummary.ltcgExempt/1000).toFixed(0)}K exempt` },
          { label: 'Crypto VDA (30%)', profit: taxSummary.cryptoProfit, tax: taxSummary.cryptoTax, color: 'amber', info: 'No loss offset allowed' },
          { label: 'F&O (Slab Rate)', profit: Math.max(0, taxSummary.fnoNet), tax: taxSummary.fnoTax, color: 'cyan', info: 'Business income' },
        ].map(item => (
          <div key={item.label} className={`bg-slate-800/50 border border-slate-700/50 rounded-xl p-3`}>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-${item.color}-400 text-sm font-medium`}>{item.label}</span>
              <span className="text-red-400 text-sm font-bold">-{fmt(item.tax)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 text-xs">Profit: {fmt(item.profit)}</span>
              <span className="text-slate-600 text-[10px]">{item.info}</span>
            </div>
          </div>
        ))}
      </div>

      {taxSummary.needsAudit && (
        <div className="flex items-start space-x-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl mb-4">
          <AlertTriangle size={16} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-amber-400 text-sm font-medium">Tax Audit Required</p>
            <p className="text-xs text-amber-400/70">F&O turnover exceeds ₹10Cr. Section 44AB audit is mandatory.</p>
          </div>
        </div>
      )}

      {/* Other income for slab calc */}
      <div className="mb-4">
        <label className="text-xs text-slate-500">Other Income (for F&O slab calculation)</label>
        <input type="number" value={otherIncome} onChange={e => setOtherIncome(e.target.value)}
          placeholder="₹ Salary, rental, etc."
          className="w-full mt-1 p-3 bg-slate-800 border border-slate-700 rounded-xl text-sm focus:border-blue-500 outline-none" />
      </div>

      {/* Actions */}
      <div className="flex space-x-2 mb-6">
        <button onClick={() => setShowAdd(true)}
          className="flex-1 py-3 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400 text-sm font-medium flex items-center justify-center space-x-2">
          <Calculator size={16} />
          <span>Add Trade</span>
        </button>
        <button onClick={exportReport}
          className="flex-1 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm font-medium flex items-center justify-center space-x-2">
          <Download size={16} />
          <span>Export Report</span>
        </button>
      </div>

      {/* Trade List */}
      <h3 className="text-sm font-bold mb-2 text-slate-400">Recent Trades ({trades.length})</h3>
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {trades.slice(-20).reverse().map(t => (
          <div key={t.id} className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg text-xs">
            <div className="flex-1">
              <span className="font-medium">{t.description}</span>
              <span className={`ml-2 px-1.5 py-0.5 rounded text-[9px] ${
                t.type === 'crypto' ? 'bg-amber-500/10 text-amber-400' :
                t.type === 'fno' ? 'bg-cyan-500/10 text-cyan-400' :
                t.type === 'equity_ltcg' ? 'bg-purple-500/10 text-purple-400' :
                'bg-blue-500/10 text-blue-400'
              }`}>{t.type.replace('_', ' ').toUpperCase()}</span>
            </div>
            <span className={`font-mono ${t.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {t.profit >= 0 ? '+' : ''}{fmt(t.profit)}
            </span>
          </div>
        ))}
        {trades.length === 0 && (
          <p className="text-center text-slate-600 text-xs py-8">No trades recorded. Add manually or they'll import from Paper Trading.</p>
        )}
      </div>

      {/* Add Trade Modal */}
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowAdd(false)} />
          <div className="relative bg-slate-900 w-full rounded-t-3xl p-4">
            <h3 className="font-bold text-lg mb-4">Add Trade</h3>
            <div className="space-y-3">
              <select value={manualEntry.type} onChange={e => setManualEntry({...manualEntry, type: e.target.value})}
                className="w-full p-3 bg-slate-800 border border-slate-700 rounded-xl text-sm">
                <option value="equity_stcg">Equity STCG (short-term)</option>
                <option value="equity_ltcg">Equity LTCG (long-term)</option>
                <option value="crypto">Crypto / VDA</option>
                <option value="fno">F&O / Derivatives</option>
              </select>
              <input type="text" value={manualEntry.description} onChange={e => setManualEntry({...manualEntry, description: e.target.value})}
                placeholder="Description (e.g., RELIANCE buy/sell)" className="w-full p-3 bg-slate-800 border border-slate-700 rounded-xl text-sm outline-none" />
              <div className="grid grid-cols-2 gap-2">
                <input type="number" value={manualEntry.buyValue} onChange={e => setManualEntry({...manualEntry, buyValue: e.target.value})}
                  placeholder="Buy value ₹" className="p-3 bg-slate-800 border border-slate-700 rounded-xl text-sm outline-none" />
                <input type="number" value={manualEntry.sellValue} onChange={e => setManualEntry({...manualEntry, sellValue: e.target.value})}
                  placeholder="Sell value ₹" className="p-3 bg-slate-800 border border-slate-700 rounded-xl text-sm outline-none" />
              </div>
              <button onClick={addTrade} className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl font-bold text-sm">
                Add Trade
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-6 p-3 bg-slate-800/30 rounded-xl">
        <p className="text-[10px] text-slate-600 flex items-start space-x-1">
          <Info size={12} className="flex-shrink-0 mt-0.5" />
          <span>This is an estimation tool only. Actual tax liability may differ. Consult a CA for filing.
          Tax rates as per Indian Income Tax Act. STCG on equity: 15%, LTCG: 10% above ₹1L, Crypto VDA: 30% flat, F&O: slab rate.</span>
        </p>
      </div>
    </div>
  )
}

export default TaxCalculator
