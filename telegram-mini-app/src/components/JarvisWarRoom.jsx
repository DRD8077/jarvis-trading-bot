/**
 * 🏟️ JARVIS WAR ROOM — Multi-Market Tactical Display
 * ═══════════════════════════════════════════════════════════════
 * 
 * Like Tony Stark's holographic war room with multiple screens:
 * - BTC, ETH, SOL, BNB, XRP all on one screen
 * - Live price tickers with mini sparklines
 * - Market dominance chart
 * - Fear & Greed Index
 * - Global market cap
 * - Top gainers / losers
 * - DeFi TVL
 */

import React, { useState, useEffect, useCallback } from 'react'

const TRACKED_COINS = [
  { id: 'bitcoin', symbol: 'BTC', color: '#F7931A' },
  { id: 'ethereum', symbol: 'ETH', color: '#627EEA' },
  { id: 'solana', symbol: 'SOL', color: '#14F195' },
  { id: 'binancecoin', symbol: 'BNB', color: '#F3BA2F' },
  { id: 'ripple', symbol: 'XRP', color: '#00AAE4' },
  { id: 'cardano', symbol: 'ADA', color: '#0033AD' },
  { id: 'dogecoin', symbol: 'DOGE', color: '#C2A633' },
  { id: 'avalanche-2', symbol: 'AVAX', color: '#E84142' },
]

export default function JarvisWarRoom() {
  const [coins, setCoins] = useState([])
  const [globalData, setGlobalData] = useState(null)
  const [fearGreed, setFearGreed] = useState(null)
  const [topGainers, setTopGainers] = useState([])
  const [topLosers, setTopLosers] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      // Fetch coin prices
      const ids = TRACKED_COINS.map(c => c.id).join(',')
      const [priceRes, globalRes, trendRes] = await Promise.allSettled([
        fetch(`https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${ids}&order=market_cap_desc&sparkline=false&price_change_percentage=1h,24h,7d`),
        fetch('https://api.coingecko.com/api/v3/global'),
        fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&sparkline=false&price_change_percentage=24h'),
      ])

      if (priceRes.status === 'fulfilled' && priceRes.value.ok) {
        const data = await priceRes.value.json()
        setCoins(data)
      }

      if (globalRes.status === 'fulfilled' && globalRes.value.ok) {
        const data = await globalRes.value.json()
        setGlobalData(data.data)
      }

      if (trendRes.status === 'fulfilled' && trendRes.value.ok) {
        const data = await trendRes.value.json()
        const sorted = data.sort((a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0))
        setTopGainers(sorted.slice(0, 5))
        setTopLosers(sorted.slice(-5).reverse())
      }

      // Fear & Greed (alternative API)
      try {
        const fgRes = await fetch('https://api.alternative.me/fng/?limit=1')
        if (fgRes.ok) {
          const fgData = await fgRes.json()
          setFearGreed(fgData.data?.[0])
        }
      } catch {}

      setLastUpdate(new Date())
      setLoading(false)
    } catch (e) {
      console.warn('[War Room] Fetch error:', e)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Update every 30s
    return () => clearInterval(interval)
  }, [fetchData])

  const formatNum = (n) => {
    if(!n) return '—'
    if (n >= 1e12) return `$${(n/1e12).toFixed(2)}T`
    if (n >= 1e9) return `$${(n/1e9).toFixed(2)}B`
    if (n >= 1e6) return `$${(n/1e6).toFixed(2)}M`
    return `$${n.toLocaleString()}`
  }

  const fgColor = (val) => {
    val = parseInt(val)
    if (val <= 25) return '#ff4444'
    if (val <= 45) return '#ff8844'
    if (val <= 55) return '#ffaa00'
    if (val <= 75) return '#88cc44'
    return '#44ff44'
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.headerIcon}>🏟️</span>
          <h2 style={styles.title}>WAR ROOM</h2>
        </div>
        <div style={styles.loading}>
          <div style={styles.scanLine}></div>
          <p style={{color:'#00d4ff'}}>INITIALIZING TACTICAL DISPLAY...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.headerIcon}>🏟️</span>
        <h2 style={styles.title}>JARVIS WAR ROOM</h2>
        <span style={styles.liveIndicator}>● LIVE</span>
      </div>
      <p style={styles.subtitle}>Multi-Market Tactical Display</p>

      {/* Global Stats Bar */}
      <div style={styles.globalBar}>
        <div style={styles.globalStat}>
          <span style={styles.globalLabel}>MARKET CAP</span>
          <span style={styles.globalValue}>{formatNum(globalData?.total_market_cap?.usd)}</span>
        </div>
        <div style={styles.globalStat}>
          <span style={styles.globalLabel}>24H VOL</span>
          <span style={styles.globalValue}>{formatNum(globalData?.total_volume?.usd)}</span>
        </div>
        <div style={styles.globalStat}>
          <span style={styles.globalLabel}>BTC DOM</span>
          <span style={styles.globalValue}>{globalData?.market_cap_percentage?.btc?.toFixed(1) || '—'}%</span>
        </div>
        {fearGreed && (
          <div style={styles.globalStat}>
            <span style={styles.globalLabel}>FEAR/GREED</span>
            <span style={{...styles.globalValue, color: fgColor(fearGreed.value)}}>
              {fearGreed.value} — {fearGreed.value_classification}
            </span>
          </div>
        )}
      </div>

      {/* Main Coin Grid */}
      <div style={styles.coinGrid}>
        {coins.map(coin => {
          const tracked = TRACKED_COINS.find(t => t.id === coin.id)
          const change = coin.price_change_percentage_24h || 0
          const isUp = change >= 0
          return (
            <div key={coin.id} style={{
              ...styles.coinCard,
              borderColor: tracked?.color || '#333',
              boxShadow: `0 0 15px ${tracked?.color || '#333'}33`,
            }}>
              <div style={styles.coinHeader}>
                <span style={{...styles.coinSymbol, color: tracked?.color}}>{tracked?.symbol || coin.symbol?.toUpperCase()}</span>
                <span style={{...styles.coinChange, color: isUp ? '#00ff88' : '#ff4444'}}>
                  {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                </span>
              </div>
              <div style={styles.coinPrice}>
                ${coin.current_price?.toLocaleString(undefined, {maximumFractionDigits: 2})}
              </div>
              <div style={styles.coinMeta}>
                <span>MCap: {formatNum(coin.market_cap)}</span>
              </div>
              {/* Mini bar showing 24h change */}
              <div style={styles.miniBarBg}>
                <div style={{
                  ...styles.miniBar,
                  width: `${Math.min(Math.abs(change) * 5, 100)}%`,
                  background: isUp ? '#00ff8866' : '#ff444466',
                }}/>
              </div>
            </div>
          )
        })}
      </div>

      {/* Top Gainers & Losers */}
      <div style={styles.glGrid}>
        <div style={styles.glSection}>
          <h3 style={{...styles.glTitle, color: '#00ff88'}}>🚀 TOP GAINERS</h3>
          {topGainers.map((c, i) => (
            <div key={c.id} style={styles.glRow}>
              <span style={styles.glRank}>#{i+1}</span>
              <span style={styles.glName}>{c.symbol?.toUpperCase()}</span>
              <span style={{...styles.glChange, color: '#00ff88'}}>
                +{(c.price_change_percentage_24h || 0).toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
        <div style={styles.glSection}>
          <h3 style={{...styles.glTitle, color: '#ff4444'}}>💀 TOP LOSERS</h3>
          {topLosers.map((c, i) => (
            <div key={c.id} style={styles.glRow}>
              <span style={styles.glRank}>#{i+1}</span>
              <span style={styles.glName}>{c.symbol?.toUpperCase()}</span>
              <span style={{...styles.glChange, color: '#ff4444'}}>
                {(c.price_change_percentage_24h || 0).toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Last Update */}
      <div style={styles.footer}>
        <span>Last scan: {lastUpdate?.toLocaleTimeString() || '—'}</span>
        <button onClick={fetchData} style={styles.refreshBtn}>⟳ REFRESH</button>
      </div>
    </div>
  )
}

const styles = {
  container: {
    padding: '16px',
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0a0a0a 0%, #0d1117 50%, #0a0a0a 100%)',
    color: '#e0e0e0',
    fontFamily: "'Courier New', monospace",
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '4px',
  },
  headerIcon: { fontSize: '28px' },
  title: {
    margin: 0,
    fontSize: '20px',
    color: '#00d4ff',
    textShadow: '0 0 10px #00d4ff44',
    letterSpacing: '2px',
    flex: 1,
  },
  liveIndicator: {
    color: '#ff4444',
    fontSize: '12px',
    animation: 'blink 1s infinite',
  },
  subtitle: {
    margin: '0 0 16px 38px',
    fontSize: '11px',
    color: '#666',
    letterSpacing: '1px',
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '60vh',
    gap: '20px',
  },
  scanLine: {
    width: '200px',
    height: '2px',
    background: 'linear-gradient(90deg, transparent, #00d4ff, transparent)',
    animation: 'scan 2s infinite',
  },
  globalBar: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '8px',
    marginBottom: '16px',
    padding: '12px',
    background: '#111827',
    borderRadius: '10px',
    border: '1px solid #1e3a5f',
  },
  globalStat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '2px',
  },
  globalLabel: {
    fontSize: '9px',
    color: '#666',
    letterSpacing: '1px',
  },
  globalValue: {
    fontSize: '13px',
    color: '#00d4ff',
    fontWeight: 'bold',
  },
  coinGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '10px',
    marginBottom: '16px',
  },
  coinCard: {
    padding: '12px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #333',
    position: 'relative',
    overflow: 'hidden',
  },
  coinHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  coinSymbol: {
    fontSize: '16px',
    fontWeight: 'bold',
  },
  coinChange: {
    fontSize: '12px',
    fontWeight: 'bold',
  },
  coinPrice: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: '4px',
  },
  coinMeta: {
    fontSize: '10px',
    color: '#666',
  },
  miniBarBg: {
    width: '100%',
    height: '3px',
    background: '#1a1a2e',
    borderRadius: '2px',
    marginTop: '6px',
    overflow: 'hidden',
  },
  miniBar: {
    height: '100%',
    borderRadius: '2px',
    transition: 'width 0.5s ease',
  },
  glGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '10px',
    marginBottom: '16px',
  },
  glSection: {
    padding: '10px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #1e3a5f',
  },
  glTitle: {
    margin: '0 0 8px 0',
    fontSize: '12px',
    letterSpacing: '1px',
  },
  glRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '4px 0',
    fontSize: '12px',
    borderBottom: '1px solid #1a1a2e',
  },
  glRank: { color: '#666', width: '24px' },
  glName: { flex: 1, color: '#ccc', fontWeight: 'bold' },
  glChange: { fontWeight: 'bold' },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    fontSize: '11px',
    color: '#666',
  },
  refreshBtn: {
    background: '#1e3a5f',
    color: '#00d4ff',
    border: 'none',
    borderRadius: '6px',
    padding: '6px 14px',
    fontSize: '12px',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
  },
}
