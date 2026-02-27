import React, { useState, useEffect } from 'react'
import {
  Wallet, Plus, Minus, History, CreditCard, ArrowUpRight, ArrowDownLeft,
  RefreshCw, QrCode, Copy, CheckCircle, AlertCircle, Clock
} from 'lucide-react'
import { fetchWallet, requestDeposit, verifyDeposit, requestWithdraw } from '../services/api'
import { useApp } from '../context/AppContext'

// ═══ Client-side UPI QR Generator (no backend needed) ═══
function generateUPIQR(amount, upiId = 'jarvis@ybl', name = 'JARVIS Trading') {
  const upiUrl = `upi://pay?pa=${encodeURIComponent(upiId)}&pn=${encodeURIComponent(name)}&am=${amount}&cu=INR&tn=${encodeURIComponent('JARVIS Deposit')}`
  // Use Google Charts QR API as fallback (works without any library)
  const qrUrl = `https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=${encodeURIComponent(upiUrl)}&choe=UTF-8`
  return { qr_url: qrUrl, upi_id: upiId, upi_link: upiUrl }
}

const WalletPage = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const [walletData, setWalletData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('overview') // overview, deposit, withdraw
  const [depositAmount, setDepositAmount] = useState('')
  const [depositQR, setDepositQR] = useState(null)
  const [utrInput, setUtrInput] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawMethod, setWithdrawMethod] = useState('upi')
  const [phantomAddress, setPhantomAddress] = useState('')
  const [withdrawUpiId, setWithdrawUpiId] = useState('')
  const [processing, setProcessing] = useState(false)

  const loadWallet = async () => {
    setLoading(true)
    try {
      const res = await fetchWallet()
      setWalletData(res.data?.data || res.data || {})
    } catch (e) {
      console.error('Wallet load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWallet()
    // Auto-refresh wallet every 15 seconds for real-time balance
    const iv = setInterval(() => {
      fetchWallet().then(res => {
        const d = res.data?.data || res.data || {}
        if (d) setWalletData(d)
      }).catch(() => {})
    }, 15000)
    return () => clearInterval(iv)
  }, [])

  const handleDeposit = async () => {
    if (!depositAmount || parseFloat(depositAmount) < 1) {
      addNotification('Minimum deposit is ₹1', 'error'); return
    }
    setProcessing(true)
    try {
      const res = await requestDeposit(parseFloat(depositAmount))
      setDepositQR(res.data?.data || res.data || {})
      hapticFeedback('success')
      addNotification('QR generated! Scan to pay', 'success')
    } catch (e) {
      // Backend unavailable — generate QR client-side
      try {
        const qrData = generateUPIQR(parseFloat(depositAmount))
        setDepositQR(qrData)
        hapticFeedback('success')
        addNotification('UPI QR generated! Scan karke pay karein 💳', 'success')
      } catch (e2) {
        addNotification('QR generation failed', 'error')
      }
    } finally {
      setProcessing(false)
    }
  }

  const handleVerifyDeposit = async () => {
    if (!utrInput) { addNotification('Enter UTR number', 'error'); return }
    setProcessing(true)
    try {
      await verifyDeposit(utrInput, parseFloat(depositAmount))
      addNotification('Deposit verification submitted!', 'success')
      hapticFeedback('success')
      setActiveView('overview')
      loadWallet()
    } catch (e) {
      addNotification('Verification failed', 'error')
    } finally {
      setProcessing(false)
    }
  }

  const handleWithdraw = async () => {
    if (!withdrawAmount || parseFloat(withdrawAmount) < 1) {
      addNotification('Minimum withdrawal is ₹1', 'error'); return
    }
    if (withdrawMethod === 'phantom' && (!phantomAddress || phantomAddress.length < 32)) {
      addNotification('Please enter a valid Phantom wallet address', 'error'); return
    }
    if (withdrawMethod === 'upi' && !withdrawUpiId) {
      addNotification('Please enter your UPI ID', 'error'); return
    }
    setProcessing(true)
    try {
      await requestWithdraw(parseFloat(withdrawAmount), withdrawMethod, withdrawMethod === 'phantom' ? phantomAddress : withdrawUpiId)
      const dest = withdrawMethod === 'phantom' ? 'Phantom wallet' : 'UPI'
      addNotification(`Withdrawal to ${dest} submitted!`, 'success')
      hapticFeedback('success')
      setActiveView('overview')
      loadWallet()
    } catch (e) {
      addNotification('Withdrawal failed: ' + (e.response?.data?.detail || e.message), 'error')
    } finally {
      setProcessing(false)
    }
  }

  const balance = walletData?.balance || walletData?.portfolio?.balance || 0
  const portfolio = walletData?.portfolio || {}
  const transactions = walletData?.transactions || []
  const tax = walletData?.tax || {}

  if (loading) {
    return (
      <div className="p-4 space-y-4 bg-slate-900 min-h-screen">
        <div className="skeleton h-36 rounded-2xl" />
        <div className="grid grid-cols-2 gap-3"><div className="skeleton h-14" /><div className="skeleton h-14" /></div>
        {[1,2,3].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Wallet</h1>
        <button onClick={loadWallet} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Balance Card */}
      <div className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-5 shadow-lg shadow-emerald-500/20 mb-5">
        <p className="text-emerald-100 text-sm">Available Balance</p>
        <p className="text-3xl font-bold mt-1">₹{balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
        {portfolio.invested && (
          <div className="flex items-center mt-3 space-x-4 text-sm">
            <div>
              <span className="text-emerald-200">Invested: </span>
              <span className="font-medium">₹{(portfolio.invested || 0).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-emerald-200">P&L: </span>
              <span className={`font-medium ${(portfolio.pnl || 0) >= 0 ? 'text-white' : 'text-red-200'}`}>
                {(portfolio.pnl || 0) >= 0 ? '+' : ''}₹{(portfolio.pnl || 0).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <button onClick={() => setActiveView(activeView === 'deposit' ? 'overview' : 'deposit')}
          className={`py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 transition-all ${
            activeView === 'deposit' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 border border-slate-700'
          }`}>
          <ArrowDownLeft size={18} />
          <span>Deposit</span>
        </button>
        <button onClick={() => setActiveView(activeView === 'withdraw' ? 'overview' : 'withdraw')}
          className={`py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 transition-all ${
            activeView === 'withdraw' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 border border-slate-700'
          }`}>
          <ArrowUpRight size={18} />
          <span>Withdraw</span>
        </button>
      </div>

      {/* DEPOSIT VIEW */}
      {activeView === 'deposit' && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5 animate-fade-up">
          <h3 className="font-bold mb-3">Deposit via UPI</h3>
          
          {!depositQR ? (
            <>
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[100, 500, 1000].map(amt => (
                  <button key={amt} onClick={() => setDepositAmount(amt.toString())}
                    className={`py-2 rounded-lg text-sm font-medium transition-all ${
                      depositAmount === amt.toString()
                        ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}>₹{amt.toLocaleString()}</button>
                ))}
              </div>
              <input type="number" value={depositAmount} onChange={e => setDepositAmount(e.target.value)}
                placeholder="Enter amount (min ₹1)"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-3 focus:ring-2 focus:ring-blue-500 outline-none" />
              <button onClick={handleDeposit} disabled={processing}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors">
                {processing ? 'Generating QR...' : 'Generate UPI QR'}
              </button>
            </>
          ) : (
            <div className="text-center">
              {depositQR.qr_url && (
                <img src={depositQR.qr_url} alt="UPI QR" className="mx-auto w-48 h-48 rounded-lg mb-3" />
              )}
              {depositQR.upi_id && (
                <div className="bg-slate-700 rounded-lg p-3 mb-3">
                  <p className="text-xs text-slate-400">UPI ID</p>
                  <p className="font-mono text-sm">{depositQR.upi_id}</p>
                </div>
              )}
              <p className="text-sm text-slate-400 mb-3">Pay ₹{depositAmount} and enter UTR below</p>
              <input type="text" value={utrInput} onChange={e => setUtrInput(e.target.value)}
                placeholder="Enter UTR / Transaction ID"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-3 focus:ring-2 focus:ring-blue-500 outline-none" />
              <button onClick={handleVerifyDeposit} disabled={processing}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-semibold text-sm disabled:opacity-50">
                {processing ? 'Verifying...' : 'Verify Payment'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* WITHDRAW VIEW — UPI / Bank / Phantom */}
      {activeView === 'withdraw' && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5 animate-fade-up">
          <h3 className="font-bold mb-3">Withdraw Funds</h3>

          {/* Method Toggle */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              { key: 'upi', label: 'UPI', icon: '💳' },
              { key: 'bank', label: 'Bank', icon: '🏦' },
              { key: 'phantom', label: 'Phantom', icon: '👻' },
            ].map(m => (
              <button key={m.key} onClick={() => setWithdrawMethod(m.key)}
                className={`py-2.5 rounded-lg text-sm font-semibold transition-all ${
                  withdrawMethod === m.key
                    ? m.key === 'phantom' ? 'bg-purple-600 text-white' : 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}>
                {m.icon} {m.label}
              </button>
            ))}
          </div>

          {/* UPI Withdraw */}
          {withdrawMethod === 'upi' && (
            <input type="text" value={withdrawUpiId} onChange={e => setWithdrawUpiId(e.target.value)}
              placeholder="Enter your UPI ID (e.g. name@upi)"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-3 focus:ring-2 focus:ring-blue-500 outline-none" />
          )}

          {/* Bank Withdraw */}
          {withdrawMethod === 'bank' && (
            <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-3 mb-3">
              <p className="text-xs text-yellow-300">🏦 Bank transfers take 1-3 business days. Contact admin via bot for bank withdrawal.</p>
            </div>
          )}

          {/* Phantom Wallet */}
          {withdrawMethod === 'phantom' && (
            <>
              <div className="bg-purple-600/20 border border-purple-500/30 rounded-lg p-3 mb-3">
                <p className="text-xs text-purple-300">👻 Withdrawals sent directly to your Phantom (Solana) wallet</p>
              </div>
              <input type="text" value={phantomAddress} onChange={e => setPhantomAddress(e.target.value)}
                placeholder="Enter your Phantom wallet address..."
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-3 focus:ring-2 focus:ring-purple-500 outline-none font-mono" />
            </>
          )}

          <input type="number" value={withdrawAmount} onChange={e => setWithdrawAmount(e.target.value)}
            placeholder="Enter amount (min ₹1)"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm mb-3 focus:ring-2 focus:ring-blue-500 outline-none" />
          <p className="text-xs text-slate-400 mb-3">Available: ₹{balance.toLocaleString()}</p>
          <button onClick={handleWithdraw} disabled={processing || withdrawMethod === 'bank'}
            className={`w-full py-3 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors ${
              withdrawMethod === 'phantom' ? 'bg-purple-600 hover:bg-purple-500 text-white' : 'bg-blue-600 hover:bg-blue-500 text-white'
            }`}>
            {processing ? 'Processing...' : withdrawMethod === 'phantom' ? '👻 Withdraw to Phantom' : withdrawMethod === 'upi' ? '💳 Withdraw to UPI' : '🏦 Contact Admin for Bank'}
          </button>
        </div>
      )}

      {/* Tax Summary */}
      {tax.total_tax !== undefined && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-5">
          <h3 className="font-bold mb-2">Tax Summary (30% Crypto)</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-slate-400">Total Gains:</span> <span className="font-medium">₹{(tax.total_gains || 0).toLocaleString()}</span></div>
            <div><span className="text-slate-400">Tax Liability:</span> <span className="font-medium text-red-400">₹{(tax.total_tax || 0).toLocaleString()}</span></div>
          </div>
        </div>
      )}

      {/* Transaction History */}
      <div>
        <h3 className="font-bold mb-3 flex items-center space-x-2">
          <History size={18} className="text-slate-400" />
          <span>Recent Transactions</span>
        </h3>
        <div className="space-y-2">
          {transactions.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-8">No transactions yet</p>
          ) : (
            transactions.slice(0, 15).map((tx, i) => (
              <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                    (tx.type || '').includes('deposit') || (tx.amount || 0) > 0 ? 'bg-emerald-500/20' :
                    (tx.type || '').includes('withdraw') ? 'bg-orange-500/20' : 'bg-blue-500/20'
                  }`}>
                    {(tx.type || '').includes('deposit') || (tx.amount || 0) > 0
                      ? <ArrowDownLeft size={16} className="text-emerald-400" />
                      : <ArrowUpRight size={16} className="text-orange-400" />
                    }
                  </div>
                  <div>
                    <p className="text-sm font-medium">{tx.description || tx.type || 'Transaction'}</p>
                    <p className="text-xs text-slate-500">{tx.date || tx.time || ''}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${(tx.amount || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(tx.amount || 0) >= 0 ? '+' : ''}₹{Math.abs(tx.amount || 0).toLocaleString()}
                  </p>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                    (tx.status || '').includes('complete') ? 'bg-emerald-500/20 text-emerald-400' :
                    (tx.status || '').includes('pending') ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-600 text-slate-300'
                  }`}>{tx.status || ''}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default WalletPage
