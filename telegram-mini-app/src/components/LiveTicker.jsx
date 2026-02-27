import React, { useState, useEffect, useRef } from 'react'
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from 'lucide-react'
import { fetchTicker } from '../services/api'
import binanceFeed from '../services/binanceFeed'

// Top crypto symbols to show in ticker
const TICKER_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'SHIBUSDT']
const DISPLAY_NAMES = { BTCUSDT: 'BTC', ETHUSDT: 'ETH', BNBUSDT: 'BNB', SOLUSDT: 'SOL', XRPUSDT: 'XRP', DOGEUSDT: 'DOGE', ADAUSDT: 'ADA', AVAXUSDT: 'AVAX', DOTUSDT: 'DOT', MATICUSDT: 'MATIC', LINKUSDT: 'LINK', SHIBUSDT: 'SHIB' }

const LiveTicker = () => {
  const [tickers, setTickers] = useState([])
  const scrollRef = useRef(null)
  const binanceReady = useRef(false)

  // PRIMARY: Binance WebSocket — real-time, no backend needed
  useEffect(() => {
    const unsubs = TICKER_SYMBOLS.map(sym =>
      binanceFeed.subscribe(sym, (data) => {
        binanceReady.current = true
        setTickers(prev => {
          const idx = prev.findIndex(t => t.symbol === DISPLAY_NAMES[sym] || t.symbol === sym)
          const entry = {
            symbol: DISPLAY_NAMES[sym] || sym.replace('USDT', ''),
            price: data.price,
            priceUsd: data.price,
            change: data.change24h,
            isInr: false
          }
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = entry
            return next
          }
          return [...prev, entry]
        })
      })
    )
    return () => unsubs.forEach(u => u())
  }, [])

  // FALLBACK: Backend API only if Binance WS hasn't delivered data in 5s
  useEffect(() => {
    const fallbackTimer = setTimeout(async () => {
      if (binanceReady.current) return // Binance already working
      try {
        const data = await fetchTicker()
        const raw = data?.ticker || data?.data?.ticker || []
        if (raw.length > 0) {
          setTickers(raw.map(t => ({
            symbol: t.symbol || '???',
            price: t.price_inr || t.price_usd || 0,
            priceUsd: t.price_usd || 0,
            change: t.change_24h || 0,
            isInr: !!(t.price_inr && t.price_inr > 1)
          })))
        }
      } catch {}
    }, 5000)
    return () => clearTimeout(fallbackTimer)
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
