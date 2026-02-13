import React, { useState, useEffect } from 'react'
import {
  Search, Filter, TrendingUp, TrendingDown, BarChart3, RefreshCw,
  SlidersHorizontal, Star, ArrowUpDown
} from 'lucide-react'
import { fetchScreener, fetchFutures } from '../services/api'
import { useApp } from '../context/AppContext'

const Screener = () => {
  const { addNotification, hapticFeedback } = useApp()
  const [results, setResults] = useState([])
  const [futures, setFutures] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('screener') // screener, futures
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    market: 'all', // all, crypto, indian
    signal: 'all', // all, buy, sell
    sortBy: 'change', // change, volume, price
  })

  const loadData = async () => {
    setLoading(true)
    try {
      const [scrRes, futRes] = await Promise.all([
        fetchScreener({ market: filters.market }).catch(() => null),
        fetchFutures().catch(() => null)
      ])
      
      const scrData = scrRes?.data?.data || scrRes?.data?.results || scrRes?.data || []
      setResults(Array.isArray(scrData) ? scrData : [])
      setFutures(futRes?.data?.data || futRes?.data || null)
    } catch (e) {
      console.error('Screener load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const filteredResults = results.filter(r => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (!(r.symbol || r.name || '').toLowerCase().includes(q)) return false
    }
    if (filters.signal !== 'all') {
      const sig = (r.signal || r.type || '').toLowerCase()
      if (!sig.includes(filters.signal)) return false
    }
    return true
  }).sort((a, b) => {
    if (filters.sortBy === 'change') return Math.abs(b.change || b.change_percent || 0) - Math.abs(a.change || a.change_percent || 0)
    if (filters.sortBy === 'volume') return (b.volume || 0) - (a.volume || 0)
    if (filters.sortBy === 'price') return (b.price || b.last_price || 0) - (a.price || a.last_price || 0)
    return 0
  })

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <Search size={22} className="text-teal-400" />
            <span>Screener</span>
          </h1>
          <p className="text-slate-400 text-sm">Stocks, Crypto & Futures scanner</p>
        </div>
        <button onClick={loadData} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-blue-400" />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex space-x-1 bg-slate-800 rounded-xl p-1 mb-4">
        {['screener', 'futures'].map(t => (
          <button key={t} onClick={() => { setActiveTab(t); hapticFeedback('impact') }}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all capitalize ${
              activeTab === t ? 'bg-teal-600 text-white' : 'text-slate-400'
            }`}>{t}</button>
        ))}
      </div>

      {/* SCREENER TAB */}
      {activeTab === 'screener' && (
        <>
          {/* Search Bar */}
          <div className="relative mb-3">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search symbol or name..."
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-teal-500 outline-none" />
          </div>

          {/* Filters */}
          <div className="flex space-x-2 mb-4 overflow-x-auto scrollbar-hide">
            {[
              { key: 'market', options: [{ v: 'all', l: 'All' }, { v: 'crypto', l: 'Crypto' }, { v: 'indian', l: 'Indian' }] },
              { key: 'signal', options: [{ v: 'all', l: 'All' }, { v: 'buy', l: '🟢 Buy' }, { v: 'sell', l: '🔴 Sell' }] },
            ].map(fg => (
              <div key={fg.key} className="flex space-x-1">
                {fg.options.map(o => (
                  <button key={o.v} onClick={() => setFilters(p => ({ ...p, [fg.key]: o.v }))}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${
                      filters[fg.key] === o.v ? 'bg-teal-600 text-white' : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>{o.l}</button>
                ))}
              </div>
            ))}
            <button onClick={() => setFilters(p => ({
              ...p,
              sortBy: p.sortBy === 'change' ? 'volume' : p.sortBy === 'volume' ? 'price' : 'change'
            }))} className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700 flex items-center space-x-1">
              <ArrowUpDown size={10} />
              <span>Sort: {filters.sortBy}</span>
            </button>
          </div>

          {/* Results */}
          {loading ? (
            <div className="space-y-2">
              {[1,2,3,4,5].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredResults.length === 0 ? (
                <p className="text-center text-slate-400 py-12">No results found</p>
              ) : (
                filteredResults.slice(0, 50).map((r, i) => (
                  <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center text-xs font-bold">
                        {(r.symbol || r.name || '?').substring(0, 3)}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{r.symbol || r.name}</p>
                        <div className="flex items-center space-x-2">
                          {r.signal && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                              (r.signal || '').toLowerCase().includes('buy')
                                ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                            }`}>{r.signal}</span>
                          )}
                          <span className="text-[10px] text-slate-500">{r.exchange || r.market || ''}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold">₹{(r.price || r.last_price || r.ltp || 0).toLocaleString()}</p>
                      <p className={`text-xs font-medium ${(r.change || r.change_percent || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {(r.change || r.change_percent || 0) >= 0 ? '+' : ''}{(r.change || r.change_percent || 0).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}

      {/* FUTURES TAB */}
      {activeTab === 'futures' && (
        <div className="space-y-4">
          {!futures ? (
            <div className="text-center py-12">
              <BarChart3 size={48} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">Loading futures data...</p>
            </div>
          ) : (
            <>
              {/* VIX Info */}
              {(futures.vix || futures.india_vix) && (
                <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-xl p-4 shadow-lg">
                  <p className="text-violet-200 text-xs">India VIX (Fear Index)</p>
                  <p className="text-2xl font-bold">{(futures.vix || futures.india_vix || 0).toFixed(2)}</p>
                  <p className="text-xs text-violet-200 mt-1">
                    {(futures.vix || futures.india_vix || 0) > 20 ? '⚠️ High volatility' : '✅ Low volatility'}
                  </p>
                </div>
              )}

              {/* Futures Data */}
              {(futures.data || futures.futures || []).map((f, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-3 border border-slate-700 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-sm">{f.symbol || f.name}</p>
                    <p className="text-xs text-slate-400">{f.expiry || f.expDate || ''}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">₹{(f.price || f.ltp || 0).toLocaleString()}</p>
                    <p className={`text-xs ${(f.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {(f.change || 0) >= 0 ? '+' : ''}{(f.change || 0).toFixed(2)}%
                    </p>
                  </div>
                </div>
              ))}

              {/* OI Data */}
              {futures.oi_analysis && (
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <h3 className="font-bold text-sm mb-2">Open Interest Analysis</h3>
                  <p className="text-xs text-slate-400">{JSON.stringify(futures.oi_analysis).substring(0, 200)}...</p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default Screener
