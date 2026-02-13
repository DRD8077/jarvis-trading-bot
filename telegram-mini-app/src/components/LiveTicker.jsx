import React, { useState, useEffect, useRef } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const defaultTickers = [
  { symbol: 'BTC', price: 0, change: 0 },
  { symbol: 'ETH', price: 0, change: 0 },
  { symbol: 'SOL', price: 0, change: 0 },
  { symbol: 'BNB', price: 0, change: 0 },
  { symbol: 'XRP', price: 0, change: 0 },
  { symbol: 'NIFTY', price: 0, change: 0 },
]

const LiveTicker = () => {
  const [tickers, setTickers] = useState(defaultTickers)
  const scrollRef = useRef(null)

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple&vs_currencies=usd&include_24hr_change=true')
        if (res.ok) {
          const d = await res.json()
          setTickers(prev => {
            const updated = [...prev]
            const map = {
              BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana',
              BNB: 'binancecoin', XRP: 'ripple'
            }
            updated.forEach(t => {
              const id = map[t.symbol]
              if (id && d[id]) {
                t.price = d[id].usd || 0
                t.change = d[id].usd_24h_change || 0
              }
            })
            return [...updated]
          })
        }
      } catch (e) { /* silent */ }
    }

    fetchPrices()
    const interval = setInterval(fetchPrices, 30000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll animation
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    let pos = 0
    const speed = 0.5
    const animate = () => {
      pos += speed
      if (pos >= el.scrollWidth / 2) pos = 0
      el.scrollLeft = pos
      requestAnimationFrame(animate)
    }
    const anim = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(anim)
  }, [tickers])

  const formatPrice = (p) => {
    if (p >= 1000) return p.toLocaleString(undefined, { maximumFractionDigits: 0 })
    if (p >= 1) return p.toFixed(2)
    return p.toFixed(4)
  }

  return (
    <div className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700/50 overflow-hidden">
      <div ref={scrollRef} className="flex items-center space-x-4 py-1.5 px-2 overflow-hidden whitespace-nowrap"
        style={{ scrollBehavior: 'auto' }}>
        {/* Double the tickers for seamless scroll */}
        {[...tickers, ...tickers].map((t, i) => (
          <div key={i} className="flex items-center space-x-1.5 shrink-0">
            <span className="text-[10px] text-slate-400 font-medium">{t.symbol}</span>
            <span className="text-[10px] font-bold text-white">${formatPrice(t.price)}</span>
            <span className={`text-[10px] font-medium flex items-center ${
              t.change > 0 ? 'text-emerald-400' : t.change < 0 ? 'text-red-400' : 'text-slate-500'
            }`}>
              {t.change > 0 ? <TrendingUp size={8} /> : t.change < 0 ? <TrendingDown size={8} /> : <Minus size={8} />}
              {Math.abs(t.change).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LiveTicker
