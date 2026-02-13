import React, { useState, useEffect } from 'react'
import {
  Wallet, Link2, Unlink, Scan, RefreshCw, Copy, CheckCircle,
  ExternalLink, Shield, Zap, AlertTriangle, TrendingUp, TrendingDown,
  Globe, Coins, ArrowUpRight, ArrowDownLeft, Eye, Lock
} from 'lucide-react'
import {
  phantomConnectLink, phantomConnect, phantomDisconnect, phantomScan,
  phantomDashboard, solanaBalance, solanaTransactions, solanaAirdrops
} from '../services/api'
import { useApp } from '../context/AppContext'

const PhantomWallet = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const userId = String(user?.id || '')
  const [walletAddress, setWalletAddress] = useState('')
  const [addressInput, setAddressInput] = useState('')
  const [connected, setConnected] = useState(false)
  const [scanResult, setScanResult] = useState(null)
  const [balance, setBalance] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [airdrops, setAirdrops] = useState([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [activeTab, setActiveTab] = useState('tokens')
  const [copied, setCopied] = useState(false)

  const loadWallet = async () => {
    setLoading(true)
    try {
      const dashRes = await phantomDashboard(userId).catch(() => null)
      const data = dashRes?.data?.data || dashRes?.data || {}
      if (data.address || data.wallet_address) {
        setWalletAddress(data.address || data.wallet_address || '')
        setConnected(true)
        await loadBalance(data.address || data.wallet_address)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadBalance = async (addr) => {
    try {
      const [balRes, txRes] = await Promise.all([
        solanaBalance(addr).catch(() => null),
        solanaTransactions(addr, 15).catch(() => null)
      ])
      setBalance(balRes?.data?.data || null)
      setTransactions(txRes?.data?.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  // Auto-detect Phantom browser extension
  const autoConnectPhantom = async () => {
    try {
      const provider = window.solana || window.phantom?.solana
      if (provider?.isPhantom && !connected) {
        const resp = await provider.connect({ onlyIfTrusted: true })
        const addr = resp.publicKey.toString()
        if (addr) {
          setAddressInput(addr)
          await phantomConnect(userId, addr)
          setWalletAddress(addr)
          setConnected(true)
          await loadBalance(addr)
          addNotification('🔗 Phantom auto-connected!', 'success')
        }
      }
    } catch (e) {
      // User hasn't previously approved — that's OK
      console.log('Phantom auto-connect skipped:', e.message)
    }
  }

  useEffect(() => { 
    loadWallet().then(() => {
      if (!connected) autoConnectPhantom()
    })
  }, [])

  const handleConnect = async () => {
    // Try Phantom browser extension first
    const provider = window.solana || window.phantom?.solana
    if (provider?.isPhantom) {
      setConnecting(true)
      hapticFeedback('impact')
      try {
        const resp = await provider.connect()
        const addr = resp.publicKey.toString()
        await phantomConnect(userId, addr)
        setWalletAddress(addr)
        setConnected(true)
        addNotification('🔗 Phantom connected via extension!', 'success')
        hapticFeedback('success')
        await loadBalance(addr)
        return
      } catch (e) {
        // Extension declined, fall through to manual
      } finally {
        setConnecting(false)
      }
    }
    
    // Fall back to manual address entry
    if (!addressInput || addressInput.length < 32) {
      addNotification('Enter valid Solana wallet address', 'error'); return
    }
    setConnecting(true)
    hapticFeedback('impact')
    try {
      await phantomConnect(userId, addressInput)
      setWalletAddress(addressInput)
      setConnected(true)
      addNotification('🔗 Wallet connected!', 'success')
      hapticFeedback('success')
      await loadBalance(addressInput)
    } catch (e) {
      addNotification('Connection failed: ' + e.message, 'error')
      hapticFeedback('error')
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    hapticFeedback('impact')
    try {
      await phantomDisconnect(userId)
      setWalletAddress('')
      setConnected(false)
      setScanResult(null)
      setBalance(null)
      addNotification('Wallet disconnected', 'info')
    } catch (e) {
      addNotification('Disconnect failed', 'error')
    }
  }

  const handleScan = async () => {
    setScanning(true)
    hapticFeedback('impact')
    try {
      const res = await phantomScan(userId)
      setScanResult(res.data?.data || res.data || {})
      addNotification('Wallet scanned! AI predictions ready', 'success')
      hapticFeedback('success')
    } catch (e) {
      addNotification('Scan failed', 'error')
    } finally {
      setScanning(false)
    }
  }

  const handleScanAirdrops = async () => {
    if (!walletAddress) return
    hapticFeedback('impact')
    try {
      const res = await solanaAirdrops(walletAddress)
      setAirdrops(res.data?.data || [])
      addNotification(`Found ${(res.data?.data || []).length} claimable airdrops`, 'success')
    } catch (e) {
      addNotification('Airdrop scan failed', 'error')
    }
  }

  const copyAddress = () => {
    navigator.clipboard.writeText(walletAddress)
    setCopied(true)
    hapticFeedback('success')
    setTimeout(() => setCopied(false), 2000)
  }

  const tokens = scanResult?.tokens || balance?.tokens || []
  const totalValue = scanResult?.total_value || balance?.total_value || 0
  const solBal = balance?.sol_balance || scanResult?.sol_balance || 0

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-36 rounded-2xl" />
        <div className="skeleton h-32 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
              <Globe size={16} />
            </div>
            <span>Phantom Wallet</span>
          </h1>
          <p className="text-slate-400 text-sm">Solana • SPL Tokens • Auto-Trade</p>
        </div>
        {connected && (
          <button onClick={() => loadBalance(walletAddress)} className="p-2 bg-slate-800 rounded-full">
            <RefreshCw size={18} className="text-blue-400" />
          </button>
        )}
      </div>

      {/* Not Connected */}
      {!connected && (
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-purple-600/30 to-blue-600/30 border border-purple-500/20 rounded-2xl p-6 text-center">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg shadow-purple-500/30">
              <Globe size={36} />
            </div>
            <h2 className="text-xl font-bold mb-2">Connect Your Phantom Wallet</h2>
            <p className="text-slate-400 text-sm mb-4">
              Link your Solana wallet for AI-powered auto trading, token scanning, and portfolio tracking
            </p>
            <div className="flex items-center space-x-2 bg-slate-800 rounded-xl p-1 mb-4">
              <input type="text" value={addressInput} onChange={e => setAddressInput(e.target.value)}
                placeholder="Paste your Solana wallet address..."
                className="flex-1 bg-transparent px-3 py-2.5 text-sm outline-none placeholder-slate-500" />
            </div>
            <button onClick={handleConnect} disabled={connecting}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3.5 rounded-xl font-bold text-sm 
              hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 active:scale-95 transition-all shadow-lg shadow-purple-500/20">
              {connecting ? '🔄 Connecting...' : '🔗 Connect Wallet'}
            </button>
          </div>

          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="font-bold text-sm mb-3 flex items-center space-x-2">
              <Shield size={16} className="text-emerald-400" />
              <span>Security Features</span>
            </h3>
            <div className="space-y-2 text-xs text-slate-400">
              <div className="flex items-center space-x-2"><Lock size={12} className="text-blue-400" /><span>HMAC encrypted wallet storage</span></div>
              <div className="flex items-center space-x-2"><Shield size={12} className="text-emerald-400" /><span>Rate limiting (15 req/60s)</span></div>
              <div className="flex items-center space-x-2"><Eye size={12} className="text-purple-400" /><span>Read-only access — no private keys</span></div>
              <div className="flex items-center space-x-2"><Zap size={12} className="text-amber-400" /><span>AI-powered token predictions</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Connected */}
      {connected && (
        <div className="space-y-4">
          {/* Wallet Card */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-5 shadow-lg shadow-purple-500/20">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-sm font-medium">Connected</span>
              </div>
              <button onClick={handleDisconnect} className="text-xs bg-white/10 px-2 py-1 rounded-lg flex items-center space-x-1">
                <Unlink size={10} /><span>Disconnect</span>
              </button>
            </div>
            <div className="flex items-center space-x-2 mb-3">
              <p className="text-sm font-mono truncate flex-1">{walletAddress}</p>
              <button onClick={copyAddress} className="p-1.5 bg-white/10 rounded-lg">
                {copied ? <CheckCircle size={14} className="text-emerald-300" /> : <Copy size={14} />}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-purple-200">SOL Balance</p>
                <p className="text-xl font-bold">{solBal.toFixed(4)} SOL</p>
              </div>
              <div>
                <p className="text-xs text-purple-200">Total Value</p>
                <p className="text-xl font-bold">${totalValue.toLocaleString()}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-3 gap-2">
            <button onClick={handleScan} disabled={scanning}
              className="bg-gradient-to-br from-purple-500 to-blue-500 p-3 rounded-xl flex flex-col items-center space-y-1
              disabled:opacity-50 active:scale-95 transition-transform">
              <Scan size={20} />
              <span className="text-[10px] font-medium">{scanning ? 'Scanning...' : 'AI Scan'}</span>
            </button>
            <button onClick={handleScanAirdrops}
              className="bg-gradient-to-br from-amber-500 to-orange-500 p-3 rounded-xl flex flex-col items-center space-y-1 active:scale-95">
              <Coins size={20} />
              <span className="text-[10px] font-medium">Airdrops</span>
            </button>
            <a href={`https://solscan.io/account/${walletAddress}`} target="_blank" rel="noopener noreferrer"
              className="bg-slate-800 border border-slate-700 p-3 rounded-xl flex flex-col items-center space-y-1">
              <ExternalLink size={20} className="text-blue-400" />
              <span className="text-[10px] font-medium text-slate-300">Solscan</span>
            </a>
          </div>

          {/* Tab Bar */}
          <div className="flex space-x-1 bg-slate-800 rounded-xl p-1">
            {['tokens', 'transactions', 'airdrops'].map(t => (
              <button key={t} onClick={() => setActiveTab(t)}
                className={`flex-1 py-2 rounded-lg text-xs font-medium capitalize transition-all ${
                  activeTab === t ? 'bg-purple-600 text-white' : 'text-slate-400'
                }`}>{t}</button>
            ))}
          </div>

          {/* TOKENS TAB */}
          {activeTab === 'tokens' && (
            <div className="space-y-2">
              {tokens.length === 0 ? (
                <div className="text-center py-8">
                  <Coins size={40} className="mx-auto text-slate-600 mb-2" />
                  <p className="text-slate-500 text-sm">Tap "AI Scan" to load tokens with predictions</p>
                </div>
              ) : tokens.map((t, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-[10px] font-bold">
                        {(t.symbol || '?').substring(0, 3)}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{t.symbol || t.name || 'Unknown'}</p>
                        <p className="text-[10px] text-slate-500">{t.balance?.toFixed(4) || 0} tokens</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold">${(t.value || t.usd_value || 0).toFixed(2)}</p>
                      {t.price && <p className="text-[10px] text-slate-400">${t.price.toFixed(6)}</p>}
                    </div>
                  </div>
                  {/* AI Prediction */}
                  {t.prediction && (
                    <div className={`mt-2 p-2 rounded-lg text-xs ${
                      (t.prediction.signal || '').toLowerCase().includes('buy') || (t.prediction.direction || '').toLowerCase() === 'up'
                        ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                    }`}>
                      <span className="font-medium">AI: </span>
                      {t.prediction.signal || t.prediction.direction || ''} •
                      Confidence: {t.prediction.confidence || '--'}%
                      {t.prediction.reason && <span> • {t.prediction.reason}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* TRANSACTIONS TAB */}
          {activeTab === 'transactions' && (
            <div className="space-y-2">
              {transactions.length === 0 ? (
                <p className="text-center text-slate-500 py-8 text-sm">No recent transactions</p>
              ) : transactions.map((tx, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      (tx.type || '').includes('receive') || (tx.direction || '') === 'in'
                        ? 'bg-emerald-500/20' : 'bg-red-500/20'
                    }`}>
                      {(tx.type || '').includes('receive') || (tx.direction || '') === 'in'
                        ? <ArrowDownLeft size={14} className="text-emerald-400" />
                        : <ArrowUpRight size={14} className="text-red-400" />
                      }
                    </div>
                    <div>
                      <p className="text-sm font-medium truncate max-w-[180px]">{tx.signature?.substring(0, 16) || tx.type || '...'}</p>
                      <p className="text-[10px] text-slate-500">{tx.time || tx.blockTime || ''}</p>
                    </div>
                  </div>
                  {tx.amount && (
                    <p className={`text-sm font-bold ${(tx.amount || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {tx.amount >= 0 ? '+' : ''}{tx.amount} SOL
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* AIRDROPS TAB */}
          {activeTab === 'airdrops' && (
            <div className="space-y-2">
              {airdrops.length === 0 ? (
                <div className="text-center py-8">
                  <Coins size={40} className="mx-auto text-slate-600 mb-2" />
                  <p className="text-slate-500 text-sm">Tap "Airdrops" button to scan</p>
                </div>
              ) : airdrops.map((a, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">{a.symbol || a.name || 'Token'}</p>
                      <p className="text-xs text-slate-400">{a.amount || 0} tokens</p>
                    </div>
                    {a.claim_link && (
                      <a href={a.claim_link} target="_blank" rel="noopener noreferrer"
                        className="bg-amber-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium">
                        Claim
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default PhantomWallet
