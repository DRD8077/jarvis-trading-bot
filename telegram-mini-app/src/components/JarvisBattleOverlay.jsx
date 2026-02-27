/**
 * ⚔️ JARVIS BATTLE OVERLAY — Iron Man Targeting HUD Component
 * ═══════════════════════════════════════════════════════════════
 * 
 * Floating overlay showing locked targets with:
 * - Animated targeting reticle
 * - Price + distance to target
 * - Color-coded status (green=on track, yellow=danger, red=SL hit)
 * - Minimizable
 */

import React, { useState, useEffect } from 'react'

export default function JarvisBattleOverlay() {
  const [targets, setTargets] = useState([])
  const [minimized, setMinimized] = useState(true)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      const t = e.detail?.targets || []
      setTargets(t)
      if (t.length > 0) setVisible(true)
    }
    window.addEventListener('jarvis-battle-update', handler)

    // Load initial
    try {
      const saved = localStorage.getItem('jarvis_battle_targets')
      if (saved) {
        const t = JSON.parse(saved)
        if (t.length > 0) {
          setTargets(t)
          setVisible(true)
        }
      }
    } catch {}

    return () => window.removeEventListener('jarvis-battle-update', handler)
  }, [])

  if (!visible || targets.length === 0) return null

  const statusColor = (s) => {
    if (s === 'TARGET_HIT') return '#00ff88'
    if (s === 'SL_HIT') return '#ff4444'
    if (s === 'DANGER') return '#ffaa00'
    return '#00d4ff'
  }

  if (minimized) {
    return (
      <div
        onClick={() => setMinimized(false)}
        style={styles.minimized}
      >
        <span style={styles.miniIcon}>⚔️</span>
        <span style={styles.miniCount}>{targets.length}</span>
        <span style={styles.miniPulse}>●</span>
      </div>
    )
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.header}>
        <span>⚔️ BATTLE HUD — {targets.length} TARGETS</span>
        <button onClick={() => setMinimized(true)} style={styles.minBtn}>━</button>
      </div>
      
      {targets.map((t, i) => (
        <div key={t.symbol} style={{
          ...styles.targetRow,
          borderLeftColor: statusColor(t.status),
        }}>
          <div style={styles.targetHeader}>
            <span style={{color: statusColor(t.status), fontWeight:'bold', fontSize:'14px'}}>
              ◎ {t.symbol}
            </span>
            <span style={{color: statusColor(t.status), fontSize:'10px', fontWeight:'bold'}}>
              {t.status}
            </span>
          </div>
          <div style={styles.targetPrice}>
            ${t.currentPrice?.toLocaleString(undefined, {maximumFractionDigits:2})}
          </div>
          <div style={styles.targetMeta}>
            {t.targetPrice > 0 && (
              <span>Target: ${t.targetPrice.toLocaleString()} ({t.distanceToTarget > 0 ? '+' : ''}{t.distanceToTarget}%)</span>
            )}
            {t.stopLoss > 0 && (
              <span style={{color:'#ff6644'}}> | SL: ${t.stopLoss.toLocaleString()}</span>
            )}
          </div>
          <div style={{
            ...styles.changeBar,
            background: (t.change24h || 0) >= 0
              ? `linear-gradient(90deg, #00ff8833 ${Math.min(Math.abs(t.change24h)*5,100)}%, transparent 0%)`
              : `linear-gradient(90deg, #ff444433 ${Math.min(Math.abs(t.change24h)*5,100)}%, transparent 0%)`,
          }}>
            <span style={{color: (t.change24h||0)>=0?'#00ff88':'#ff4444', fontSize:'10px'}}>
              24h: {(t.change24h||0)>=0?'+':''}{(t.change24h||0).toFixed(2)}%
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

const styles = {
  minimized: {
    position: 'fixed',
    bottom: '140px',
    right: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '6px 10px',
    background: '#0d1117ee',
    borderRadius: '20px',
    border: '1px solid #00d4ff44',
    zIndex: 200,
    cursor: 'pointer',
    boxShadow: '0 0 10px #00d4ff22',
  },
  miniIcon: { fontSize: '14px' },
  miniCount: { color: '#00d4ff', fontSize: '12px', fontWeight: 'bold', fontFamily: 'monospace' },
  miniPulse: { color: '#ff4444', fontSize: '8px', animation: 'blink 1s infinite' },
  overlay: {
    position: 'fixed',
    bottom: '140px',
    right: '12px',
    width: '260px',
    maxHeight: '350px',
    background: '#0d1117ee',
    borderRadius: '12px',
    border: '1px solid #00d4ff44',
    backdropFilter: 'blur(10px)',
    zIndex: 200,
    overflow: 'auto',
    boxShadow: '0 0 20px #00d4ff22',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 10px',
    fontSize: '10px',
    color: '#00d4ff',
    fontFamily: 'monospace',
    letterSpacing: '1px',
    borderBottom: '1px solid #1e3a5f',
  },
  minBtn: {
    background: 'none',
    border: 'none',
    color: '#00d4ff',
    fontSize: '14px',
    cursor: 'pointer',
    padding: '0 4px',
  },
  targetRow: {
    padding: '8px 10px',
    borderBottom: '1px solid #111827',
    borderLeft: '3px solid',
  },
  targetHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  targetPrice: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#fff',
    fontFamily: 'monospace',
  },
  targetMeta: {
    fontSize: '10px',
    color: '#888',
    marginTop: '2px',
  },
  changeBar: {
    marginTop: '4px',
    padding: '2px 6px',
    borderRadius: '4px',
  },
}
