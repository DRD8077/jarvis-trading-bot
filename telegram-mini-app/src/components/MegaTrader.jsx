import React, { useState, useEffect, useCallback } from 'react'
import {
  Zap, Play, Square, BarChart3, TrendingUp, Shield, RefreshCw,
  DollarSign, Target, Rocket, Wallet, ArrowUpRight, ArrowDownRight,
  AlertTriangle, CheckCircle, Copy, ExternalLink, Send, Eye, EyeOff,
  Clock, Activity, Search, ShieldCheck, Bot, Flame, X
} from 'lucide-react'
import {
  fetchMegaTraderStatus, createMegaWallet, enableMegaTrader, disableMegaTrader,
  fetchMegaPortfolio, fetchMegaScan, megaBuy, megaSell, megaTransfer,
  fetchMegaTransfers, megaRugCheck
} from '../services/api'
import { useApp } from '../context/AppContext'

const MegaTrader = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [status, setStatus] = useState(null)
  const [portfolio, setPortfolio] = useState(null)
  const [scanResults, setScanResults] = useState(null)
  const [transfers, setTransfers] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showTransferModal, setShowTransferModal] = useState(false)
  const [transferDest, setTransferDest] = useState('')
  const [transferAmount, setTransferAmount] = useState('')
  const [rugCheckMint, setRugCheckMint] = useState('')
  const [rugResult, setRugResult] = useState(null)
  const [actionLoading, setActionLoading] = useState('')
  const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || '0'

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [statusRes, portfolioRes] = await Promise.all([
        fetchMegaTraderStatus(userId).catch(() => null),
        fetchMegaPortfolio(userId).catch(() => null),
      ])
      setStatus(statusRes?.data || null)
      setPortfolio(portfolioRes?.data || null)
    } catch (e) {
      console.error('Load error:', e)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => { loadData() }, [loadData])

  // Auto-refresh every 30s
  useEffect(() => {
    const timer = setInterval(loadData, 30000)
    return () => clearInterval(timer)
  }, [loadData])

  const handleCreateWallet = async () => {
    setActionLoading('create')
    hapticFeedback('impact')
    try {
      const res = await createMegaWallet(userId)
      const data = res?.data
      if (data?.success) {
        addNotification('✅ Trading wallet created!', 'success')
        hapticFeedback('success')
        loadData()
      } else {
        addNotification(data?.error || 'Wallet creation failed', 'error')
      }
    } catch (e) {
      addNotification('Failed to create wallet', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const handleToggleTrader = async () => {
    const isEnabled = status?.auto_trade_enabled
    setActionLoading('toggle')
    hapticFeedback('impact')
    try {
      if (isEnabled) {
        await disableMegaTrader(userId)
        addNotification('⏸️ AI Trader paused', 'warning')
      } else {
        await enableMegaTrader(userId)
        addNotification('🚀 AI Trader activated!', 'success')
        hapticFeedback('success')
      }
      loadData()
    } catch (e) {
      addNotification('Toggle failed', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const handleTransfer = async () => {
    if (!transferDest || !transferAmount) {
      addNotification('Fill destination & amount', 'error')
      return
    }
    setActionLoading('transfer')
    hapticFeedback('impact')
    try {
      const res = await megaTransfer(userId, transferDest, parseFloat(transferAmount))
      const data = res?.data
      if (data?.success) {
        addNotification(`✅ Sent ${data.sol_sent} SOL → ₹${(data.inr_value || 0).toLocaleString('en-IN')}`, 'success')
        hapticFeedback('success')
        setShowTransferModal(false)
        setTransferDest('')
        setTransferAmount('')
        loadData()
      } else {
        addNotification(data?.error || 'Transfer failed', 'error')
      }
    } catch (e) {
      addNotification('Transfer error', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const handleManualSell = async (mint) => {
    setActionLoading(`sell-${mint}`)
    hapticFeedback('impact')
    try {
      const res = await megaSell(userId, mint, 100)
      if (res?.data?.success) {
        addNotification('✅ Sold successfully!', 'success')
        loadData()
      } else {
        addNotification(res?.data?.error || 'Sell failed', 'error')
      }
    } catch (e) {
      addNotification('Sell error', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const handleManualBuy = async (mint) => {
    setActionLoading(`buy-${mint}`)
    hapticFeedback('impact')
    try {
      const res = await megaBuy(userId, mint, 0.01)
      if (res?.data?.success) {
        addNotification('✅ Bought successfully!', 'success')
        loadData()
      } else {
        addNotification(res?.data?.error || 'Buy failed', 'error')
      }
    } catch (e) {
      addNotification('Buy error', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const loadScan = async () => {
    setActionLoading('scan')
    try {
      const res = await fetchMegaScan()
      setScanResults(res?.data || null)
    } catch (e) {
      console.error('Scan error:', e)
    } finally {
      setActionLoading('')
    }
  }

  const handleRugCheck = async () => {
    if (!rugCheckMint) return
    setActionLoading('rug')
    try {
      const res = await megaRugCheck(rugCheckMint)
      setRugResult(res?.data || null)
    } catch (e) {
      addNotification('Rug check failed', 'error')
    } finally {
      setActionLoading('')
    }
  }

  const copyAddress = (addr) => {
    navigator.clipboard.writeText(addr).catch(() => {})
    addNotification('📋 Address copied!', 'success')
    hapticFeedback('impact')
  }

  const formatINR = (val) => {
    if (!val && val !== 0) return '₹0'
    return '₹' + Math.abs(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })
  }

  // ── NO WALLET STATE ──
  if (!loading && status && !status.has_wallet) {
    return (
      <div style={{ padding: 16, minHeight: '100vh', background: '#0a0a0f' }}>
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>🤖🚀</div>
          <h2 style={{ color: '#fff', fontSize: 22, marginBottom: 8 }}>JARVIS MEGA AI TRADER</h2>
          <p style={{ color: '#9ca3af', fontSize: 14, marginBottom: 24, lineHeight: 1.6 }}>
            Nuclear autonomous crypto trading engine.<br />
            AI scans 7+ sources, auto-buys gems, manages positions, shows everything in ₹ INR.
          </p>
          <div style={{ background: '#111827', borderRadius: 12, padding: 16, marginBottom: 24, textAlign: 'left' }}>
            <p style={{ color: '#f59e0b', fontSize: 13, marginBottom: 8 }}>⚡ How it works:</p>
            <ul style={{ color: '#d1d5db', fontSize: 12, lineHeight: 2, paddingLeft: 16 }}>
              <li>Create trading wallet (free Solana address)</li>
              <li>Send SOL to your wallet address</li>
              <li>Enable AI Trader — JARVIS auto-trades 24/7</li>
              <li>AI scans DexScreener, PumpFun, DexTools, CoinGecko</li>
              <li>Auto rug-check before every buy (GoPlus security)</li>
              <li>Auto take-profit: 2x→5x→10x→50x→100x→1000x</li>
              <li>Smart stop-loss: -35% fixed + trailing at +50%</li>
              <li>Transfer profits to your Phantom wallet anytime</li>
              <li>₹500 → ₹5,000 → ₹50,000 → ₹5,00,000 → ₹50,00,000</li>
            </ul>
          </div>
          {!status?.sdk_installed && (
            <div style={{ background: '#7f1d1d', borderRadius: 8, padding: 12, marginBottom: 16 }}>
              <p style={{ color: '#fca5a5', fontSize: 12 }}>⚠️ Solana SDK not installed. Run: pip install solders base58</p>
            </div>
          )}
          <button
            onClick={handleCreateWallet}
            disabled={actionLoading === 'create'}
            style={{ width: '100%', padding: '14px 24px', background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#fff', border: 'none', borderRadius: 12, fontSize: 16, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
          >
            {actionLoading === 'create' ? <RefreshCw size={18} className="spin" /> : <Wallet size={18} />}
            {actionLoading === 'create' ? 'Creating...' : 'Create Trading Wallet'}
          </button>
        </div>
      </div>
    )
  }

  // ── LOADING ──
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <RefreshCw size={32} className="spin" style={{ color: '#8b5cf6' }} />
      </div>
    )
  }

  const walletAddr = status?.wallet_address || portfolio?.wallet_address || ''
  const isTrading = status?.auto_trade_enabled
  const totalInr = portfolio?.total_value_inr || 0
  const pnlInr = portfolio?.total_pnl_inr || 0
  const pnlPct = portfolio?.total_pnl_pct || 0
  const solBal = portfolio?.sol_balance || 0
  const solInr = portfolio?.sol_balance_inr || 0
  const positions = portfolio?.positions || status?.active_positions || []
  const compound = portfolio?.compound_stage || status?.compound_stage || {}
  const trades = status?.recent_trades || []
  const config = status?.config || {}

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: BarChart3 },
    { id: 'positions', label: '💰 Positions', icon: Target },
    { id: 'scan', label: '🔍 AI Scan', icon: Search },
    { id: 'safety', label: '🛡️ Rug Check', icon: ShieldCheck },
    { id: 'history', label: '📜 History', icon: Clock },
  ]

  return (
    <div style={{ padding: 12, minHeight: '100vh', background: '#0a0a0f', paddingBottom: 80 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bot size={22} style={{ color: '#8b5cf6' }} />
          <h2 style={{ color: '#fff', fontSize: 16, margin: 0, fontWeight: 700 }}>MEGA AI TRADER</h2>
          <span style={{ background: isTrading ? '#059669' : '#dc2626', color: '#fff', fontSize: 10, padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
            {isTrading ? '🟢 LIVE' : '🔴 OFF'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button onClick={loadData} style={{ background: '#1f2937', border: 'none', borderRadius: 8, padding: '6px 8px', cursor: 'pointer' }}>
            <RefreshCw size={14} style={{ color: '#9ca3af' }} />
          </button>
          <button onClick={() => setShowTransferModal(true)} style={{ background: '#1f2937', border: 'none', borderRadius: 8, padding: '6px 8px', cursor: 'pointer' }}>
            <Send size={14} style={{ color: '#8b5cf6' }} />
          </button>
        </div>
      </div>

      {/* Wallet Address */}
      {walletAddr && (
        <div onClick={() => copyAddress(walletAddr)} style={{ background: '#111827', borderRadius: 10, padding: '8px 12px', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <Wallet size={14} style={{ color: '#6b7280' }} />
          <span style={{ color: '#9ca3af', fontSize: 11, fontFamily: 'monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{walletAddr}</span>
          <Copy size={12} style={{ color: '#6b7280' }} />
        </div>
      )}

      {/* Portfolio Summary Card */}
      <div style={{ background: 'linear-gradient(135deg, #1e1b4b, #312e81)', borderRadius: 14, padding: 16, marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <div>
            <p style={{ color: '#a5b4fc', fontSize: 11, margin: 0 }}>Total Portfolio</p>
            <p style={{ color: '#fff', fontSize: 28, fontWeight: 800, margin: '4px 0' }}>{formatINR(totalInr)}</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <p style={{ color: '#a5b4fc', fontSize: 11, margin: 0 }}>P&L</p>
            <p style={{ color: pnlInr >= 0 ? '#34d399' : '#f87171', fontSize: 18, fontWeight: 700, margin: '4px 0' }}>
              {pnlInr >= 0 ? '+' : ''}{formatINR(pnlInr)}
            </p>
            <p style={{ color: pnlPct >= 0 ? '#34d399' : '#f87171', fontSize: 12, margin: 0 }}>
              {pnlPct >= 0 ? '↑' : '↓'} {Math.abs(pnlPct).toFixed(1)}%
            </p>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
          <div style={{ background: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 10px' }}>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>SOL Balance</p>
            <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, margin: '2px 0' }}>{solBal.toFixed(4)}</p>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>{formatINR(solInr)}</p>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 10px' }}>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>Positions</p>
            <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, margin: '2px 0' }}>{positions.length}</p>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>/ {config.max_positions || 10} max</p>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 10px' }}>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>Total Trades</p>
            <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, margin: '2px 0' }}>{status?.total_trades || 0}</p>
            <p style={{ color: '#a5b4fc', fontSize: 10, margin: 0 }}>all time</p>
          </div>
        </div>
      </div>

      {/* Compound Stage Progress */}
      {compound?.name && (
        <div style={{ background: '#111827', borderRadius: 10, padding: 12, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ color: '#f59e0b', fontSize: 12, fontWeight: 600 }}>🎯 {compound.name}</span>
            <span style={{ color: '#d1d5db', fontSize: 11 }}>{(compound.progress_pct || 0).toFixed(1)}%</span>
          </div>
          <div style={{ background: '#1f2937', borderRadius: 6, height: 8, overflow: 'hidden' }}>
            <div style={{ background: 'linear-gradient(90deg, #8b5cf6, #f59e0b)', height: '100%', width: `${Math.min(100, compound.progress_pct || 0)}%`, borderRadius: 6, transition: 'width 0.5s' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ color: '#6b7280', fontSize: 10 }}>{formatINR(compound.current_inr || 0)}</span>
            <span style={{ color: '#6b7280', fontSize: 10 }}>Target: {formatINR(compound.target_inr || 0)}</span>
          </div>
        </div>
      )}

      {/* Enable/Disable Button */}
      <button
        onClick={handleToggleTrader}
        disabled={actionLoading === 'toggle'}
        style={{
          width: '100%', padding: '12px', marginBottom: 12, border: 'none', borderRadius: 10,
          background: isTrading
            ? 'linear-gradient(135deg, #dc2626, #991b1b)'
            : 'linear-gradient(135deg, #059669, #047857)',
          color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8
        }}
      >
        {actionLoading === 'toggle' ? <RefreshCw size={16} className="spin" /> : isTrading ? <Square size={16} /> : <Play size={16} />}
        {isTrading ? '⏸️ Pause AI Trader' : '🚀 Start AI Trader (Auto Mode)'}
      </button>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 12, overflowX: 'auto', paddingBottom: 4 }}>
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => { setActiveTab(tab.id); if (tab.id === 'scan') loadScan() }}
            style={{
              flex: 'none', padding: '8px 12px', borderRadius: 8, border: 'none',
              background: activeTab === tab.id ? '#8b5cf6' : '#1f2937',
              color: activeTab === tab.id ? '#fff' : '#9ca3af',
              fontSize: 11, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap'
            }}>{tab.label}</button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div>
          {/* AI Config Info */}
          <div style={{ background: '#111827', borderRadius: 10, padding: 12, marginBottom: 12 }}>
            <h4 style={{ color: '#8b5cf6', fontSize: 12, margin: '0 0 8px' }}>⚙️ AI Trading Config</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {[
                ['Scan Cycle', `${(config.scan_interval || 120)}s`],
                ['Min Score', `${config.min_gem_score || 60}/100`],
                ['Max Rug Risk', `${config.max_rug_risk || 40}/100`],
                ['Trailing SL', config.trailing_stop || '+50% / 20%'],
              ].map(([label, val]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: '#1f2937', borderRadius: 6 }}>
                  <span style={{ color: '#6b7280', fontSize: 10 }}>{label}</span>
                  <span style={{ color: '#d1d5db', fontSize: 10, fontWeight: 600 }}>{val}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 8 }}>
              <p style={{ color: '#6b7280', fontSize: 10, margin: 0 }}>Take-Profit Levels:</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                {(config.take_profit_levels || ['2x','5x','10x','50x','100x','1000x','10000x']).map(tp => (
                  <span key={tp} style={{ background: '#065f46', color: '#34d399', fontSize: 9, padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>{tp}</span>
                ))}
              </div>
            </div>
          </div>

          {/* How to Fund */}
          <div style={{ background: '#111827', borderRadius: 10, padding: 12 }}>
            <h4 style={{ color: '#f59e0b', fontSize: 12, margin: '0 0 8px' }}>💰 Fund Your Wallet</h4>
            <p style={{ color: '#9ca3af', fontSize: 11, lineHeight: 1.6, margin: 0 }}>
              1. Copy your wallet address above<br />
              2. Open Phantom / Solflare app<br />
              3. Send SOL to your trading wallet<br />
              4. AI will start trading automatically!<br />
              5. Transfer profits back to Phantom anytime
            </p>
            <p style={{ color: '#6b7280', fontSize: 10, marginTop: 8 }}>
              💡 Min ₹500 worth SOL recommended. Exchange rate: ₹{(portfolio?.usd_inr_rate || 83.5).toFixed(1)}/USD
            </p>
          </div>
        </div>
      )}

      {activeTab === 'positions' && (
        <div>
          {positions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <p style={{ color: '#6b7280', fontSize: 14 }}>📭 No active positions</p>
              <p style={{ color: '#4b5563', fontSize: 12 }}>AI will auto-buy gems when criteria are met</p>
            </div>
          ) : (
            positions.map((pos, i) => {
              const pnl = pos.pnl_pct || 0
              const isProfit = pnl >= 0
              return (
                <div key={i} style={{ background: '#111827', borderRadius: 10, padding: 12, marginBottom: 8, borderLeft: `3px solid ${isProfit ? '#059669' : '#dc2626'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{pos.symbol || pos.mint?.slice(0, 8) || '?'}</span>
                      {pos.profits_taken?.length > 0 && (
                        <span style={{ background: '#065f46', color: '#34d399', fontSize: 9, padding: '1px 5px', borderRadius: 4 }}>
                          {pos.profits_taken.length} TP hit
                        </span>
                      )}
                    </div>
                    <span style={{ color: isProfit ? '#34d399' : '#f87171', fontSize: 14, fontWeight: 700 }}>
                      {pnl >= 0 ? '+' : ''}{pnl.toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                    <div>
                      <span style={{ color: '#6b7280', fontSize: 10 }}>Invested: </span>
                      <span style={{ color: '#d1d5db', fontSize: 10 }}>{formatINR(pos.invested_inr || 0)}</span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280', fontSize: 10 }}>Current: </span>
                      <span style={{ color: '#d1d5db', fontSize: 10 }}>{formatINR(pos.current_value_inr || pos.value_inr || 0)}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                    <button onClick={() => handleManualSell(pos.mint)} disabled={actionLoading === `sell-${pos.mint}`}
                      style={{ flex: 1, padding: '6px', background: '#7f1d1d', color: '#fca5a5', border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer' }}>
                      {actionLoading === `sell-${pos.mint}` ? '...' : '🔴 Sell 100%'}
                    </button>
                    <button onClick={() => { if (pos.mint) window.open(`https://solscan.io/token/${pos.mint}`, '_blank') }}
                      style={{ padding: '6px 10px', background: '#1f2937', color: '#9ca3af', border: 'none', borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>
                      <ExternalLink size={12} />
                    </button>
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      {activeTab === 'scan' && (
        <div>
          <button onClick={loadScan} disabled={actionLoading === 'scan'}
            style={{ width: '100%', padding: 10, background: '#312e81', color: '#a5b4fc', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
            {actionLoading === 'scan' ? <RefreshCw size={14} className="spin" /> : <Search size={14} />}
            {actionLoading === 'scan' ? 'Scanning 7 sources...' : '🔍 Scan All Sources Now'}
          </button>

          {scanResults && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 10 }}>
                <div style={{ background: '#111827', borderRadius: 8, padding: 8, textAlign: 'center' }}>
                  <p style={{ color: '#6b7280', fontSize: 10, margin: 0 }}>Scanned</p>
                  <p style={{ color: '#fff', fontSize: 16, fontWeight: 700, margin: 0 }}>{scanResults.total_scanned}</p>
                </div>
                <div style={{ background: '#111827', borderRadius: 8, padding: 8, textAlign: 'center' }}>
                  <p style={{ color: '#6b7280', fontSize: 10, margin: 0 }}>Passed AI</p>
                  <p style={{ color: '#34d399', fontSize: 16, fontWeight: 700, margin: 0 }}>{scanResults.passed_threshold}</p>
                </div>
                <div style={{ background: '#111827', borderRadius: 8, padding: 8, textAlign: 'center' }}>
                  <p style={{ color: '#6b7280', fontSize: 10, margin: 0 }}>Sources</p>
                  <p style={{ color: '#a5b4fc', fontSize: 16, fontWeight: 700, margin: 0 }}>{scanResults.sources?.length || 0}</p>
                </div>
              </div>

              {scanResults.top_gems?.map((gem, i) => (
                <div key={i} style={{ background: '#111827', borderRadius: 10, padding: 10, marginBottom: 6, borderLeft: `3px solid ${gem.ai_score >= 70 ? '#059669' : gem.ai_score >= 50 ? '#f59e0b' : '#dc2626'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{gem.symbol}</span>
                      <span style={{ color: '#6b7280', fontSize: 10, marginLeft: 6 }}>{gem.source}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{
                        background: gem.ai_score >= 70 ? '#065f46' : gem.ai_score >= 50 ? '#78350f' : '#7f1d1d',
                        color: gem.ai_score >= 70 ? '#34d399' : gem.ai_score >= 50 ? '#fbbf24' : '#fca5a5',
                        padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 700
                      }}>{gem.ai_score}/100</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                    <span style={{ color: '#9ca3af', fontSize: 10 }}>💰 ${gem.price_usd?.toFixed(6) || '0'}</span>
                    <span style={{ color: '#9ca3af', fontSize: 10 }}>📊 Vol: ${(gem.volume_24h || 0).toLocaleString()}</span>
                    <span style={{ color: '#9ca3af', fontSize: 10 }}>💧 Liq: ${(gem.liquidity || 0).toLocaleString()}</span>
                    {gem.price_change_1h ? <span style={{ color: gem.price_change_1h >= 0 ? '#34d399' : '#f87171', fontSize: 10 }}>1h: {gem.price_change_1h > 0 ? '+' : ''}{gem.price_change_1h.toFixed(1)}%</span> : null}
                  </div>
                  <p style={{ color: gem.ai_score >= 65 ? '#34d399' : '#fbbf24', fontSize: 10, margin: '4px 0 0' }}>{gem.ai_verdict}</p>
                  {gem.chain === 'solana' && gem.ai_score >= 65 && (
                    <button onClick={() => handleManualBuy(gem.mint)} disabled={actionLoading === `buy-${gem.mint}`}
                      style={{ marginTop: 6, padding: '5px 12px', background: '#065f46', color: '#34d399', border: 'none', borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: 'pointer' }}>
                      {actionLoading === `buy-${gem.mint}` ? '...' : '🟢 Buy 0.01 SOL'}
                    </button>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {activeTab === 'safety' && (
        <div>
          <div style={{ background: '#111827', borderRadius: 10, padding: 12, marginBottom: 12 }}>
            <h4 style={{ color: '#8b5cf6', fontSize: 12, margin: '0 0 8px' }}>🛡️ Token Rug Check</h4>
            <p style={{ color: '#6b7280', fontSize: 11, marginBottom: 8 }}>Paste any Solana token address to check for rug pull risks</p>
            <div style={{ display: 'flex', gap: 6 }}>
              <input value={rugCheckMint} onChange={e => setRugCheckMint(e.target.value)}
                placeholder="Token mint address..."
                style={{ flex: 1, padding: '8px 10px', background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#fff', fontSize: 12, outline: 'none' }} />
              <button onClick={handleRugCheck} disabled={actionLoading === 'rug'}
                style={{ padding: '8px 14px', background: '#8b5cf6', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                {actionLoading === 'rug' ? '...' : 'Check'}
              </button>
            </div>
          </div>

          {rugResult && (
            <div style={{ background: '#111827', borderRadius: 10, padding: 12, borderLeft: `3px solid ${rugResult.safe ? '#059669' : '#dc2626'}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                {rugResult.safe ? <ShieldCheck size={20} style={{ color: '#34d399' }} /> : <AlertTriangle size={20} style={{ color: '#f87171' }} />}
                <span style={{ color: rugResult.safe ? '#34d399' : '#f87171', fontSize: 16, fontWeight: 700 }}>
                  {rugResult.safe ? '✅ SAFE' : '❌ DANGEROUS'}
                </span>
                <span style={{ color: '#9ca3af', fontSize: 12, marginLeft: 'auto' }}>
                  Risk: {rugResult.risk_score}/100
                </span>
              </div>
              <div style={{ background: '#1f2937', borderRadius: 8, height: 6, overflow: 'hidden', marginBottom: 8 }}>
                <div style={{ background: rugResult.risk_score > 50 ? '#dc2626' : rugResult.risk_score > 25 ? '#f59e0b' : '#059669', height: '100%', width: `${rugResult.risk_score}%` }} />
              </div>
              {rugResult.reasons?.map((r, i) => (
                <p key={i} style={{ color: '#d1d5db', fontSize: 11, margin: '4px 0', padding: '4px 8px', background: '#1f2937', borderRadius: 4 }}>{r}</p>
              ))}
            </div>
          )}

          {/* Auto Rug Protection Info */}
          <div style={{ background: '#111827', borderRadius: 10, padding: 12, marginTop: 12 }}>
            <h4 style={{ color: '#059669', fontSize: 12, margin: '0 0 8px' }}>🛡️ AI Auto-Protection</h4>
            <ul style={{ color: '#9ca3af', fontSize: 11, lineHeight: 2, paddingLeft: 16, margin: 0 }}>
              <li>GoPlus Security API check before every buy</li>
              <li>Honeypot detection (can you sell?)</li>
              <li>Mintable token detection</li>
              <li>Owner permission abuse check</li>
              <li>High tax detection (buy/sell tax)</li>
              <li>Holder concentration analysis</li>
              <li>Liquidity adequacy check</li>
              <li>FDV/Liquidity ratio analysis</li>
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div>
          {trades.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <p style={{ color: '#6b7280', fontSize: 14 }}>📭 No trades yet</p>
              <p style={{ color: '#4b5563', fontSize: 12 }}>Fund wallet and enable AI trader to start</p>
            </div>
          ) : (
            trades.map((t, i) => (
              <div key={i} style={{ background: '#111827', borderRadius: 8, padding: 10, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: t.type === 'buy' ? '#065f46' : '#7f1d1d'
                }}>
                  {t.type === 'buy' ? <ArrowDownRight size={16} style={{ color: '#34d399' }} /> : <ArrowUpRight size={16} style={{ color: '#fca5a5' }} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{t.type === 'buy' ? '🟢 BUY' : '🔴 SELL'} {t.mint}</span>
                    <span style={{ color: '#d1d5db', fontSize: 12, fontWeight: 600 }}>{formatINR(t.inr)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                    <span style={{ color: '#6b7280', fontSize: 10 }}>{t.sol?.toFixed(4) || '0'} SOL</span>
                    <span style={{ color: '#6b7280', fontSize: 10 }}>{t.time?.slice(0, 16) || ''}</span>
                  </div>
                </div>
                {t.signature && (
                  <button onClick={() => window.open(`https://solscan.io/tx/${t.signature}`, '_blank')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}>
                    <ExternalLink size={12} style={{ color: '#6b7280' }} />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Transfer Modal */}
      {showTransferModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'flex-end', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', borderRadius: '16px 16px 0 0', padding: 20, width: '100%', maxWidth: 420 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ color: '#fff', fontSize: 16, margin: 0 }}>📤 Transfer to Phantom</h3>
              <button onClick={() => setShowTransferModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} style={{ color: '#6b7280' }} />
              </button>
            </div>
            <p style={{ color: '#9ca3af', fontSize: 12, marginBottom: 12 }}>
              Send SOL to your Phantom/Solflare wallet address. Real on-chain transfer.
            </p>
            <div style={{ marginBottom: 12 }}>
              <label style={{ color: '#6b7280', fontSize: 11, marginBottom: 4, display: 'block' }}>Destination Solana Address</label>
              <input value={transferDest} onChange={e => setTransferDest(e.target.value)}
                placeholder="Enter Solana wallet address..."
                style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ color: '#6b7280', fontSize: 11, marginBottom: 4, display: 'block' }}>Amount (SOL)</label>
              <input value={transferAmount} onChange={e => setTransferAmount(e.target.value)}
                placeholder="0.0" type="number" step="0.001"
                style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
              <p style={{ color: '#6b7280', fontSize: 10, marginTop: 4 }}>
                Available: {solBal.toFixed(4)} SOL ({formatINR(solInr)}) 
                {transferAmount && <span style={{ color: '#f59e0b' }}> → Sending {formatINR(parseFloat(transferAmount || 0) * (portfolio?.sol_price_inr || 0))}</span>}
              </p>
            </div>
            <button onClick={handleTransfer} disabled={actionLoading === 'transfer'}
              style={{ width: '100%', padding: '12px', background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              {actionLoading === 'transfer' ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
              {actionLoading === 'transfer' ? 'Transferring...' : '📤 Transfer Now'}
            </button>
          </div>
        </div>
      )}

      <style>{`.spin { animation: spin 1s linear infinite; } @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default MegaTrader
