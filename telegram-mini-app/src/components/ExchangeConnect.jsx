import React, { useState, useEffect, useRef } from 'react'
import { Radio, Link2, Unlink, RefreshCw, ArrowLeft, Check, AlertCircle, Wallet } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const ExchangeConnect = () => {
  const navigate = useNavigate()
  const portfolioSyncRef = useRef(null)
  const exchangeEngineRef = useRef(null)
  const [exchanges, setExchanges] = useState([])
  const [showConnect, setShowConnect] = useState(null)
  const [credentials, setCredentials] = useState({ apiKey: '', apiSecret: '' })
  const [syncing, setSyncing] = useState(false)
  const [portfolio, setPortfolio] = useState(null)
  const [error, setError] = useState('')

  const availableExchanges = [
    { id: 'binance', name: 'Binance', logo: '🟡', color: 'from-yellow-500 to-amber-600', desc: 'World\'s largest crypto exchange' },
    { id: 'coindcx', name: 'CoinDCX', logo: '🔵', color: 'from-blue-500 to-cyan-600', desc: 'India\'s largest exchange' },
    { id: 'paper', name: 'Paper Trading', logo: '📝', color: 'from-purple-500 to-indigo-600', desc: 'Practice with virtual money' },
  ]

  useEffect(() => {
    import('../services/portfolioSync').then(m => { portfolioSyncRef.current = m?.default || m }).catch(() => {})
    import('../services/exchangeEngine').then(m => { exchangeEngineRef.current = m?.default || m }).catch(() => {})
    loadExchanges()
  }, [])

  const loadExchanges = () => {
    const connected = []
    availableExchanges.forEach(ex => {
      const saved = localStorage.getItem(`jarvis_exchange_${ex.id}`)
      if (saved) {
        connected.push({ ...ex, connected: true, connectedAt: JSON.parse(saved).connectedAt })
      }
    })
    setExchanges(connected)
  }

  const handleConnect = async (exchangeId) => {
    if (exchangeId === 'paper') {
      localStorage.setItem(`jarvis_exchange_paper`, JSON.stringify({ connectedAt: Date.now() }))
      exchangeEngineRef.current?.setActiveExchange?.('paper')
      setShowConnect(null)
      loadExchanges()
      return
    }

    if (!credentials.apiKey || !credentials.apiSecret) {
      setError('API Key and Secret required')
      return
    }

    try {
      if (portfolioSyncRef.current) await portfolioSyncRef.current.connectExchange(exchangeId, credentials)
      localStorage.setItem(`jarvis_exchange_${exchangeId}`, JSON.stringify({ connectedAt: Date.now() }))
      exchangeEngineRef.current?.setActiveExchange?.(exchangeId)
      setCredentials({ apiKey: '', apiSecret: '' })
      setShowConnect(null)
      setError('')
      loadExchanges()
    } catch (e) {
      setError(e.message || 'Connection failed')
    }
  }

  const handleDisconnect = (exchangeId) => {
    portfolioSyncRef.current?.disconnectExchange?.(exchangeId)
    localStorage.removeItem(`jarvis_exchange_${exchangeId}`)
    loadExchanges()
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      const data = portfolioSyncRef.current ? await portfolioSyncRef.current.syncAll() : null
      setPortfolio(data)
    } catch (e) {
      setError('Sync failed: ' + (e.message || 'Unknown error'))
    }
    setSyncing(false)
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white p-4 pb-24">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="text-slate-400">
          <ArrowLeft size={20} />
        </button>
        <Radio className="text-blue-400" size={24} />
        <div>
          <h1 className="font-bold text-lg">Exchange Connect</h1>
          <p className="text-xs text-slate-400">{exchanges.length} connected</p>
        </div>
      </div>

      {/* Exchange Cards */}
      <div className="space-y-3">
        {availableExchanges.map(ex => {
          const connected = exchanges.find(e => e.id === ex.id)
          return (
            <div key={ex.id} className="bg-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{ex.logo}</span>
                  <div>
                    <h3 className="font-bold">{ex.name}</h3>
                    <p className="text-xs text-slate-400">{ex.desc}</p>
                  </div>
                </div>
                {connected ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-green-400 flex items-center gap-1">
                      <Check size={12} /> Connected
                    </span>
                    <button
                      onClick={() => handleDisconnect(ex.id)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg"
                    >
                      <Unlink size={16} />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowConnect(ex.id)}
                    className={`px-4 py-2 rounded-lg bg-gradient-to-r ${ex.color} font-bold text-sm flex items-center gap-1`}
                  >
                    <Link2 size={14} /> Connect
                  </button>
                )}
              </div>

              {/* Connect Form */}
              {showConnect === ex.id && ex.id !== 'paper' && (
                <div className="mt-4 space-y-3 pt-4 border-t border-slate-700">
                  <input
                    value={credentials.apiKey}
                    onChange={e => setCredentials(prev => ({ ...prev, apiKey: e.target.value }))}
                    placeholder="API Key"
                    className="w-full bg-slate-900 rounded-lg px-3 py-2 text-sm outline-none"
                  />
                  <input
                    value={credentials.apiSecret}
                    onChange={e => setCredentials(prev => ({ ...prev, apiSecret: e.target.value }))}
                    placeholder="API Secret"
                    type="password"
                    className="w-full bg-slate-900 rounded-lg px-3 py-2 text-sm outline-none"
                  />
                  {error && (
                    <p className="text-red-400 text-xs flex items-center gap-1">
                      <AlertCircle size={12} /> {error}
                    </p>
                  )}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleConnect(ex.id)}
                      className={`flex-1 py-2 rounded-lg bg-gradient-to-r ${ex.color} font-bold text-sm`}
                    >
                      Connect
                    </button>
                    <button
                      onClick={() => { setShowConnect(null); setError('') }}
                      className="flex-1 py-2 rounded-lg bg-slate-700 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-500">
                    🔐 Credentials are AES-256-GCM encrypted and stored locally. Never sent to any server.
                  </p>
                </div>
              )}

              {showConnect === ex.id && ex.id === 'paper' && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <p className="text-sm text-slate-400 mb-3">Paper trading uses virtual ₹10,00,000. No real money involved.</p>
                  <button
                    onClick={() => handleConnect('paper')}
                    className="w-full py-2 rounded-lg bg-gradient-to-r from-purple-500 to-indigo-600 font-bold text-sm"
                  >
                    Start Paper Trading
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Sync Button */}
      {exchanges.length > 0 && (
        <button
          onClick={handleSync}
          disabled={syncing}
          className="w-full mt-6 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-bold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
          {syncing ? 'Syncing...' : 'Sync All Portfolios'}
        </button>
      )}

      {/* Portfolio Summary */}
      {portfolio && (
        <div className="mt-4 bg-slate-800 rounded-xl p-4 space-y-2">
          <h3 className="font-bold flex items-center gap-2"><Wallet size={16} /> Portfolio Summary</h3>
          <p className="text-xs text-slate-400">{JSON.stringify(portfolio).substring(0, 200)}...</p>
        </div>
      )}
    </div>
  )
}

export default ExchangeConnect
