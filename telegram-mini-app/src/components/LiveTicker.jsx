import React, { useState, useEffect, useRef } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { fetchDashboard } from '../services/api'

const LiveTicker = () => {
  const [tickers, setTickers] = useState([])
  const scrollRef = useRef(null)

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const res = await fetchDashboard()
        const data = res?.data || {}
        const mt = data.market_ticker || []
        if (mt.length > 0) {
          setTickers(mt.map(t => ({
            symbol: t.symbol || '???',
            price: t.price_inr || t.price_usd || 0,
            priceUsd: t.price_usd || 0,
            change: t.change_24h || 0,
            isInr: !!(t.price_inr && t.price_inr > 1)
          })))
        }
      } catch (e) { /* silent */ }
    }
    fetchPrices()
    const interval = setInterval(fetchPrices, 20000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (!el || tickers.length === 0) return
    let pos = 0
    let animId
    const animate = () => {
      pos += 0.5
      if (pos >= el.scrollWidth / 2) pos = 0
      el.scrollLeft = pos
      animId = requestAnimationFrame(animate)
    }
    animId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animId)
  }, [tickers])

  const formatPrice = (p, isInr) => {
    const sym = isInr ? '₹' : '$'
    if (p >= 100000) return sym + (p / 100000).toFixed(2) + 'L'
    if (p >= 1000) return sym + p.toLocaleString(isInr ? 'en-IN' : undefined, { maximumFractionDigits: 0 })
    if (p >= 1) return sym + p.toFixed(2)
    if (p >= 0.01) return sym + p.toFixed(4)
    return sym + p.toExponential(2)
  }

  if (tickers.length === 0) {
    return (
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700/30 py-2 px-3">
        <div className="flex items-center space-x-3 animate-pulse">
          {[1,2,3,4,5].map(i => <div key={i} className="h-3 w-20 bg-slate-700 rounded shrink-0" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-r from-slate-900 via-slate-800/95 to-slate-900 border-b border-blue-500/10 overflow-hidden">
      <div ref={scrollRef} className="flex items-center space-x-5 py-2 px-3 overflow-hidden whitespace-nowrap"
        style={{ scrollBehavior: 'auto' }}>
        {[...tickers, ...tickers].map((t, i) => (
          <div key={i} className="flex items-center space-x-1.5 shrink-0">
            <span className="text-[11px] text-blue-300/80 font-bold tracking-wide">{t.symbol}</span>
            <span className="text-[11px] font-bold text-white">{formatPrice(t.price, t.isInr)}</span>
            <span className={`text-[10px] font-semibold flex items-center px-1 py-0.5 rounded ${
              t.change > 0 ? 'text-emerald-400 bg-emerald-500/10' : 
              t.change < 0 ? 'text-red-400 bg-red-500/10' : 'text-slate-500'
            }`}>
              {t.change > 0 ? <TrendingUp size={8} className="mr-0.5" /> : 
               t.change < 0 ? <TrendingDown size={8} className="mr-0.5" /> : <Minus size={8} className="mr-0.5" />}
              {t.change > 0 ? '+' : ''}{t.change.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LiveTicker
