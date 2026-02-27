/**
 * 📝 JARVIS Paper Trading Mode
 * ═══════════════════════════════
 * Practice trading with fake ₹10,00,000 balance + real prices
 * Zero risk — perfect for new users
 * Real-time P&L tracking, trade history, leaderboard
 */
import React, { useState, useEffect, useCallback } from 'react'
import {
  TrendingUp, TrendingDown, Wallet, Target, Shield, Zap, RefreshCw,
  ArrowUpRight, ArrowDownRight, DollarSign, BarChart3, History, Trophy,
  AlertTriangle, ChevronDown, ChevronUp, X, Plus, Minus, Check
} from 'lucide-react'
import { fetchDashboard, fetchFastPrice } from '../services/api'
import { useApp } from '../context/AppContext'

const INITIAL_BALANCE = 1000000 // ₹10,00,000
const STORAGE_KEY = 'jarvis_paper_trading'

// Load saved state
const loadState = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (saved) return saved
  } catch {}
  return {
    balance: INITIAL_BALANCE,
    positions: [],
    history: [],
    totalPnL: 0,
    winCount: 0,
    lossCount: 0,
    startDate: new Date().toISOString(),
  }
}

const saveState = (state) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

const PaperTrading = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const [state, setState] = useState(loadState)
  const [prices, setPrices] = useState({})
  const [priceChanges, setPriceChanges] = useState({})
  const [loading, setLoading] = useState(true)
  const [showOrder, setShowOrder] = useState(false)
  const [orderType, setOrderType] = useState('BUY')
  const [selectedAsset, setSelectedAsset] = useState('BTCUSDT')
  const [quantity, setQuantity] = useState('')
  const [activeTab, setActiveTab] = useState('trade') // trade, positions, history
  const [searchQuery, setSearchQuery] = useState('')

  const assets = [
    { symbol: 'BTCUSDT', name: 'Bitcoin', emoji: '₿', category: 'crypto' },
    { symbol: 'ETHUSDT', name: 'Ethereum', emoji: 'Ξ', category: 'crypto' },
    { symbol: 'SOLUSDT', name: 'Solana', emoji: '◎', category: 'crypto' },
    { symbol: 'BNBUSDT', name: 'BNB', emoji: '🔶', category: 'crypto' },
    { symbol: 'XRPUSDT', name: 'XRP', emoji: '💧', category: 'crypto' },
    { symbol: 'NIFTY50', name: 'NIFTY 50', emoji: '🇮🇳', category: 'indian' },
    { symbol: 'BANKNIFTY', name: 'Bank NIFTY', emoji: '🏦', category: 'indian' },
    { symbol: 'RELIANCE', name: 'Reliance', emoji: '🛢️', category: 'indian' },
    { symbol: 'TCS', name: 'TCS', emoji: '💻', category: 'indian' },
    { symbol: 'INFY', name: 'Infosys', emoji: '🖥️', category: 'indian' },
  ]

  // Load prices
  const loadPrices = useCallback(async () => {
    try {
      const dashRes = await fetchDashboard().catch(() => null)
      const ticker = dashRes?.data?.market_ticker || []
      const newPrices = { ...prices }

      const newChanges = {}
      ticker.forEach(t => {
        if (t.symbol) {
          newPrices[t.symbol] = parseFloat(t.price || t.last_price || 0)
          if (t.change_24h !== undefined || t.price_change_percent !== undefined) {
            newChanges[t.symbol] = parseFloat(t.change_24h || t.price_change_percent || 0)
          }
        }
      })

      // For any missing crypto prices, fetch from CoinGecko
      const cgMap = { BTCUSDT: 'bitcoin', ETHUSDT: 'ethereum', SOLUSDT: 'solana', BNBUSDT: 'binancecoin', XRPUSDT: 'ripple' }
      const missing = Object.keys(cgMap).filter(s => !newPrices[s])
      if (missing.length) {
        try {
          const ids = missing.map(s => cgMap[s]).join(',')
          const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`)
          if (res.ok) {
            const data = await res.json()
            missing.forEach(sym => {
              const d = data[cgMap[sym]]
              if (d?.usd) {
                newPrices[sym] = d.usd
                newChanges[sym] = d.usd_24h_change || 0
              }
            })
          }
        } catch {}
      }

      // For any missing Indian indices/stocks, fetch from backend
      const indianSyms = ['NIFTY50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY']
      const missingIndian = indianSyms.filter(s => !newPrices[s])
      if (missingIndian.length) {
        try {
          const { getApiBase } = await import('../services/apiBase')
          const base = getApiBase()
          const res = await fetch(`${base}/api/miniapp/india/dashboard`)
          if (res.ok) {
            const data = await res.json()
            const indices = data.data?.indices || data.indices || []
            const stocks = data.data?.stocks || data.stocks || data.data?.top_stocks || []
            indices.forEach(i => {
              const name = (i.name || i.symbol || '').toUpperCase()
              if (name.includes('NIFTY 50') || name.includes('NIFTY50')) newPrices.NIFTY50 = i.last || i.ltp || i.value || 0
              if (name.includes('BANK') && name.includes('NIFTY')) newPrices.BANKNIFTY = i.last || i.ltp || i.value || 0
            })
            stocks.forEach(s => {
              const sym = (s.symbol || s.name || '').replace('.NS', '').replace('.BO', '').toUpperCase()
              if (indianSyms.includes(sym)) {
                newPrices[sym] = s.ltp || s.price || s.last_price || 0
                newChanges[sym] = s.change_pct || s.change_percent || 0
              }
            })
          }
        } catch {}
      }

      setPriceChanges(prev => ({ ...prev, ...newChanges }))
      setPrices(newPrices)
      setLoading(false)
    } catch { setLoading(false) }
  }, [])

  useEffect(() => { loadPrices() }, [loadPrices])
  useEffect(() => {
    const iv = setInterval(loadPrices, 5000)
    return () => clearInterval(iv)
  }, [loadPrices])

  // Save state whenever it changes
  useEffect(() => { saveState(state) }, [state])

  // Calculate unrealized P&L
  const unrealizedPnL = state.positions.reduce((sum, pos) => {
    const currentPrice = prices[pos.symbol] || pos.entryPrice
    const pnl = pos.type === 'BUY'
      ? (currentPrice - pos.entryPrice) * pos.quantity
      : (pos.entryPrice - currentPrice) * pos.quantity
    return sum + pnl
  }, 0)

  const totalValue = state.balance + unrealizedPnL
  const overallReturn = ((totalValue - INITIAL_BALANCE) / INITIAL_BALANCE * 100)

  // Place order
  const placeOrder = () => {
    const qty = parseFloat(quantity)
    const price = prices[selectedAsset]
    if (!qty || qty <= 0 || !price) {
      addNotification('Invalid quantity!', 'error')
      return
    }

    const cost = qty * price
    if (orderType === 'BUY' && cost > state.balance) {
      addNotification('Insufficient balance!', 'error')
      return
    }

    const trade = {
      id: Date.now(),
      symbol: selectedAsset,
      type: orderType,
      quantity: qty,
      entryPrice: price,
      timestamp: new Date().toISOString(),
    }

    setState(prev => ({
      ...prev,
      balance: orderType === 'BUY' ? prev.balance - cost : prev.balance + cost,
      positions: [...prev.positions, trade],
    }))

    hapticFeedback('success')
    addNotification(`📝 Paper ${orderType}: ${qty} ${selectedAsset} @ ₹${price.toLocaleString()}`, 'success')
    setShowOrder(false)
    setQuantity('')
  }

  // Close position
  const closePosition = (pos) => {
    const currentPrice = prices[pos.symbol] || pos.entryPrice
    const pnl = pos.type === 'BUY'
      ? (currentPrice - pos.entryPrice) * pos.quantity
      : (pos.entryPrice - currentPrice) * pos.quantity
    const proceeds = pos.type === 'BUY' ? currentPrice * pos.quantity : pos.entryPrice * pos.quantity + pnl

    const historyEntry = {
      ...pos,
      exitPrice: currentPrice,
      pnl,
      closedAt: new Date().toISOString(),
    }

    setState(prev => ({
      ...prev,
      balance: prev.balance + proceeds,
      positions: prev.positions.filter(p => p.id !== pos.id),
      history: [historyEntry, ...prev.history],
      totalPnL: prev.totalPnL + pnl,
      winCount: pnl > 0 ? prev.winCount + 1 : prev.winCount,
      lossCount: pnl <= 0 ? prev.lossCount + 1 : prev.lossCount,
    }))

    hapticFeedback(pnl > 0 ? 'success' : 'error')
    addNotification(
      pnl > 0
        ? `✅ Closed ${pos.symbol} — Profit: ₹${pnl.toFixed(2)}`
        : `❌ Closed ${pos.symbol} — Loss: ₹${Math.abs(pnl).toFixed(2)}`,
      pnl > 0 ? 'success' : 'error'
    )
  }

  // Reset account
  const resetAccount = () => {
    const fresh = {
      balance: INITIAL_BALANCE,
      positions: [],
      history: [],
      totalPnL: 0,
      winCount: 0,
      lossCount: 0,
      startDate: new Date().toISOString(),
    }
    setState(fresh)
    saveState(fresh)
    addNotification('🔄 Paper trading account reset!', 'success')
    hapticFeedback('impact')
  }

  const winRate = (state.winCount + state.lossCount) > 0
    ? ((state.winCount / (state.winCount + state.lossCount)) * 100).toFixed(1)
    : '0.0'

  const filteredAssets = assets.filter(a =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      {[1,2,3,4].map(i => <div key={i} className="skeleton h-28 rounded-2xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-[#0a0e1a] min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold">📝 Paper Trading</h1>
            <span className="text-[9px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full font-medium">PRACTICE MODE</span>
          </div>
          <p className="text-slate-500 text-xs mt-0.5">Real prices, fake money — zero risk!</p>
        </div>
        <button onClick={resetAccount} className="p-2 bg-slate-800 rounded-xl hover:bg-slate-700 transition-colors">
          <RefreshCw size={16} className="text-slate-400" />
        </button>
      </div>

      {/* Portfolio Card */}
      <div className="bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-pink-600/20 border border-blue-500/20 rounded-2xl p-5 mb-4">
        <p className="text-slate-400 text-xs mb-1">Paper Portfolio Value</p>
        <h2 className="text-2xl font-bold mb-1">₹{totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</h2>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1 text-sm font-semibold ${overallReturn >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {overallReturn >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {overallReturn >= 0 ? '+' : ''}{overallReturn.toFixed(2)}%
          </span>
          <span className="text-slate-500 text-xs">
            Cash: ₹{state.balance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-slate-800/50 rounded-xl p-3 text-center border border-slate-700/30">
          <p className="text-[10px] text-slate-500">Total P&L</p>
          <p className={`text-sm font-bold ${state.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {state.totalPnL >= 0 ? '+' : ''}₹{state.totalPnL.toFixed(0)}
          </p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-3 text-center border border-slate-700/30">
          <p className="text-[10px] text-slate-500">Win Rate</p>
          <p className="text-sm font-bold text-blue-400">{winRate}%</p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-3 text-center border border-slate-700/30">
          <p className="text-[10px] text-slate-500">Trades</p>
          <p className="text-sm font-bold text-white">{state.winCount + state.lossCount}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-800/50 rounded-xl p-1 mb-4">
        {[
          { id: 'trade', label: 'Trade', icon: TrendingUp },
          { id: 'positions', label: `Positions (${state.positions.length})`, icon: Target },
          { id: 'history', label: 'History', icon: History },
        ].map(tab => {
          const Icon = tab.icon
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}>
              <Icon size={12} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Trade Tab */}
      {activeTab === 'trade' && (
        <div className="space-y-2">
          {/* Search */}
          <input
            type="text"
            placeholder="Search assets..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800/50 border border-slate-700/30 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500/50"
          />

          {filteredAssets.map(asset => {
            const price = prices[asset.symbol] || 0
            const change = priceChanges[asset.symbol] || 0
            return (
              <div key={asset.symbol} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{asset.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold">{asset.symbol}</p>
                    <p className="text-[10px] text-slate-500">{asset.name}</p>
                  </div>
                </div>
                <div className="text-right flex items-center gap-3">
                  <div>
                    <p className="text-sm font-bold">₹{price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                    <p className={`text-[10px] ${change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => { setSelectedAsset(asset.symbol); setOrderType('BUY'); setShowOrder(true) }}
                      className="px-2.5 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg text-[10px] font-bold hover:bg-emerald-500/30">
                      BUY
                    </button>
                    <button onClick={() => { setSelectedAsset(asset.symbol); setOrderType('SELL'); setShowOrder(true) }}
                      className="px-2.5 py-1.5 bg-red-500/20 text-red-400 rounded-lg text-[10px] font-bold hover:bg-red-500/30">
                      SELL
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Positions Tab */}
      {activeTab === 'positions' && (
        <div className="space-y-2">
          {state.positions.length === 0 ? (
            <div className="text-center py-12">
              <Target size={40} className="text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No open positions</p>
              <p className="text-slate-600 text-xs mt-1">Start trading to see your positions here</p>
            </div>
          ) : state.positions.map(pos => {
            const currentPrice = prices[pos.symbol] || pos.entryPrice
            const pnl = pos.type === 'BUY'
              ? (currentPrice - pos.entryPrice) * pos.quantity
              : (pos.entryPrice - currentPrice) * pos.quantity
            const pnlPercent = ((pnl / (pos.entryPrice * pos.quantity)) * 100)

            return (
              <div key={pos.id} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${pos.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                      {pos.type}
                    </span>
                    <span className="text-sm font-semibold">{pos.symbol}</span>
                    <span className="text-[10px] text-slate-500">×{pos.quantity}</span>
                  </div>
                  <button onClick={() => closePosition(pos)}
                    className="px-2.5 py-1 bg-slate-700 text-white rounded-lg text-[10px] font-medium hover:bg-slate-600">
                    Close
                  </button>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-500">Entry: </span>
                    <span className="text-white">₹{pos.entryPrice.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Current: </span>
                    <span className="text-white">₹{currentPrice.toLocaleString()}</span>
                  </div>
                  <div className={pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                    {pnl >= 0 ? '+' : ''}₹{pnl.toFixed(2)} ({pnlPercent.toFixed(2)}%)
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-2">
          {state.history.length === 0 ? (
            <div className="text-center py-12">
              <History size={40} className="text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No trade history yet</p>
              <p className="text-slate-600 text-xs mt-1">Closed trades will appear here</p>
            </div>
          ) : state.history.map((trade, i) => (
            <div key={i} className="bg-slate-800/50 border border-slate-700/30 rounded-xl p-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${trade.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    {trade.type}
                  </span>
                  <span className="text-sm font-semibold">{trade.symbol}</span>
                </div>
                <span className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {trade.pnl >= 0 ? '+' : ''}₹{trade.pnl.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span>₹{trade.entryPrice.toLocaleString()} → ₹{trade.exitPrice.toLocaleString()}</span>
                <span>{new Date(trade.closedAt).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Order Modal */}
      {showOrder && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={() => setShowOrder(false)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <div className="relative bg-slate-900 border-t border-slate-700 rounded-t-3xl w-full max-w-lg p-5 animate-slide-up" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">
                {orderType === 'BUY' ? '🟢' : '🔴'} {orderType} {selectedAsset}
              </h3>
              <button onClick={() => setShowOrder(false)} className="p-1.5 bg-slate-800 rounded-full">
                <X size={16} className="text-slate-400" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Current Price</label>
                <p className="text-xl font-bold">₹{(prices[selectedAsset] || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
              </div>

              <div>
                <label className="text-xs text-slate-400 mb-1 block">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={e => setQuantity(e.target.value)}
                  placeholder="Enter quantity..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500"
                />
              </div>

              {quantity && prices[selectedAsset] && (
                <div className="bg-slate-800/50 rounded-xl p-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Total Value</span>
                    <span className="font-bold">₹{(parseFloat(quantity) * prices[selectedAsset]).toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Available</span>
                    <span>₹{state.balance.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                  </div>
                </div>
              )}

              <button onClick={placeOrder}
                className={`w-full py-3.5 rounded-xl font-bold text-white transition-all active:scale-[0.98] ${
                  orderType === 'BUY' ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-red-500 hover:bg-red-600'
                }`}>
                {orderType} {selectedAsset}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PaperTrading
