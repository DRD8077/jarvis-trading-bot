/**
 * 🔧 JARVIS DIAGNOSTICS PAGE — Full System Diagnostic UI
 * ═══════════════════════════════════════════════════════════════
 * 
 * "JARVIS, run a diagnostic"
 * Beautiful Iron Man style system check display
 */

import React, { useState, useEffect } from 'react'

export default function JarvisDiagnosticsPage() {
  const [report, setReport] = useState(null)
  const [running, setRunning] = useState(false)
  const [scanPhase, setScanPhase] = useState(0)
  const [userDNA, setUserDNA] = useState(null)

  const runDiag = async () => {
    setRunning(true)
    setScanPhase(0)

    // Animate scan phases
    const phases = ['Initializing...', 'Checking Core...', 'Scanning Defense...', 'Testing AI...', 'Power Check...', 'Network Scan...', 'Hardware Check...', 'Compiling Report...']
    for (let i = 0; i < phases.length; i++) {
      setScanPhase(i)
      await new Promise(r => setTimeout(r, 400))
    }

    try {
      const mod = await import('../services/jarvisDiagnostics.js')
      const result = await mod.default.runDiagnostic()
      setReport(result)
    } catch (e) {
      console.error('[Diagnostics] Error:', e)
    }

    // Load user DNA
    try {
      const leMod = await import('../services/jarvisLearningEngine.js')
      setUserDNA(leMod.default.getUserDNA())
    } catch {}

    setRunning(false)
  }

  useEffect(() => {
    // Load last report
    try {
      const saved = localStorage.getItem('jarvis_last_diagnostic')
      if (saved) setReport(JSON.parse(saved))
    } catch {}
  }, [])

  const statusColor = (s) => {
    if (s === 'ONLINE' || s === 'NOMINAL') return '#00ff88'
    if (s === 'STANDBY' || s === 'LEARNING' || s === 'EMPTY') return '#00d4ff'
    if (s === 'DEGRADED' || s === 'LOW' || s === 'UNINITIALIZED') return '#ffaa00'
    if (s === 'OFFLINE' || s === 'UNAVAILABLE') return '#ff6644'
    if (s === 'ERROR' || s === 'CRITICAL') return '#ff4444'
    return '#888'
  }

  const statusIcon = (s) => {
    if (s === 'ONLINE' || s === 'NOMINAL') return '●'
    if (s === 'STANDBY' || s === 'LEARNING' || s === 'EMPTY') return '◐'
    if (s === 'DEGRADED' || s === 'LOW') return '◑'
    if (s === 'OFFLINE' || s === 'UNAVAILABLE') return '○'
    if (s === 'ERROR' || s === 'CRITICAL') return '✗'
    return '?'
  }

  const phases = ['Initializing...', 'Checking Core...', 'Scanning Defense...', 'Testing AI...', 'Power Check...', 'Network Scan...', 'Hardware Check...', 'Compiling Report...']

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.icon}>🔧</span>
        <h2 style={styles.title}>SYSTEM DIAGNOSTICS</h2>
      </div>
      <p style={styles.subtitle}>Full JARVIS Self-Diagnostic</p>

      {/* Run Button */}
      <button
        onClick={runDiag}
        disabled={running}
        style={{
          ...styles.runBtn,
          opacity: running ? 0.5 : 1,
          boxShadow: running ? 'none' : '0 0 20px #00d4ff44',
        }}
      >
        {running ? '⟳ SCANNING...' : '▶ RUN DIAGNOSTIC'}
      </button>

      {/* Scan Animation */}
      {running && (
        <div style={styles.scanArea}>
          <div style={styles.scanLine} />
          {phases.map((phase, i) => (
            <div key={i} style={{
              ...styles.scanPhase,
              color: i < scanPhase ? '#00ff88' : i === scanPhase ? '#00d4ff' : '#333',
            }}>
              {i < scanPhase ? '✓' : i === scanPhase ? '⟳' : '○'} {phase}
            </div>
          ))}
        </div>
      )}

      {/* Report */}
      {report && !running && (
        <>
          {/* Overall Status */}
          <div style={{
            ...styles.overallBox,
            borderColor: report.overallStatus === 'NOMINAL' ? '#00ff88' : report.overallStatus === 'DEGRADED' ? '#ffaa00' : '#ff4444',
            boxShadow: `0 0 20px ${report.overallStatus === 'NOMINAL' ? '#00ff8833' : '#ff444433'}`,
          }}>
            <div style={styles.overallHeader}>
              <span style={{...styles.overallStatus, color: statusColor(report.overallStatus)}}>
                {report.overallStatus}
              </span>
              <span style={styles.overallHealth}>{report.healthPercent}%</span>
            </div>
            <div style={styles.overallStats}>
              <span style={{color:'#00ff88'}}>✓ {report.online} Online</span>
              <span style={{color:'#ffaa00'}}>◑ {report.degraded} Degraded</span>
              <span style={{color:'#ff4444'}}>✗ {report.offline + report.errors} Issues</span>
            </div>
            <div style={styles.overallMeta}>
              Scan: {report.duration}ms | {report.total} subsystems | {new Date(report.timestamp).toLocaleString()}
            </div>
          </div>

          {/* Systems by Category */}
          {['CORE', 'DEFENSE', 'AI', 'POWER', 'DISPLAY', 'NETWORK', 'HARDWARE'].map(cat => {
            const systems = Object.values(report.results).filter(r => r.category === cat)
            if (systems.length === 0) return null
            return (
              <div key={cat} style={styles.category}>
                <h3 style={styles.catTitle}>{cat}</h3>
                {systems.map((sys, i) => (
                  <div key={i} style={styles.systemRow}>
                    <span style={{color: statusColor(sys.status), marginRight:'8px', fontFamily:'monospace'}}>
                      {statusIcon(sys.status)}
                    </span>
                    <span style={styles.sysName}>{sys.name}</span>
                    <span style={{...styles.sysStatus, color: statusColor(sys.status)}}>
                      {sys.status}
                    </span>
                    <div style={styles.sysDetails}>{sys.details}</div>
                  </div>
                ))}
              </div>
            )
          })}

          {/* User DNA */}
          {userDNA && (
            <div style={styles.dnaSection}>
              <h3 style={styles.catTitle}>👤 USER DNA</h3>
              <div style={styles.dnaGrid}>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Sessions</span>
                  <span style={styles.dnaValue}>{userDNA.totalSessions}</span>
                </div>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Streak</span>
                  <span style={styles.dnaValue}>{userDNA.currentStreak} days</span>
                </div>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Best Streak</span>
                  <span style={styles.dnaValue}>{userDNA.longestStreak} days</span>
                </div>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Risk Level</span>
                  <span style={{...styles.dnaValue, color: userDNA.riskLevel === 'aggressive' ? '#ff4444' : userDNA.riskLevel === 'moderate' ? '#ffaa00' : '#00ff88'}}>
                    {userDNA.riskLevel?.toUpperCase()}
                  </span>
                </div>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Peak Hour</span>
                  <span style={styles.dnaValue}>{userDNA.peakHour}:00</span>
                </div>
                <div style={styles.dnaStat}>
                  <span style={styles.dnaLabel}>Peak Day</span>
                  <span style={styles.dnaValue}>{userDNA.peakDay}</span>
                </div>
              </div>
              {userDNA.favoriteAssets?.length > 0 && (
                <div style={styles.dnaRow}>
                  <span style={styles.dnaLabel}>Fav Assets:</span>
                  <span style={styles.dnaValue}>{userDNA.favoriteAssets.join(', ')}</span>
                </div>
              )}
              {userDNA.milestones?.length > 0 && (
                <div style={styles.milestones}>
                  <span style={styles.dnaLabel}>Milestones:</span>
                  <div style={styles.milestoneList}>
                    {userDNA.milestones.map((m, i) => (
                      <span key={i} style={styles.milestone}>{m.label}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
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
  icon: { fontSize: '28px' },
  title: {
    margin: 0,
    fontSize: '20px',
    color: '#00d4ff',
    textShadow: '0 0 10px #00d4ff44',
    letterSpacing: '2px',
  },
  subtitle: {
    margin: '0 0 16px 38px',
    fontSize: '11px',
    color: '#666',
    letterSpacing: '1px',
  },
  runBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #0d2137, #1e3a5f)',
    color: '#00d4ff',
    border: '1px solid #00d4ff44',
    borderRadius: '10px',
    fontSize: '16px',
    fontWeight: 'bold',
    fontFamily: "'Courier New', monospace",
    cursor: 'pointer',
    letterSpacing: '2px',
    marginBottom: '16px',
  },
  scanArea: {
    padding: '16px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #1e3a5f',
    marginBottom: '16px',
    position: 'relative',
    overflow: 'hidden',
  },
  scanLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '2px',
    background: 'linear-gradient(90deg, transparent, #00d4ff, transparent)',
    animation: 'scan 2s infinite',
  },
  scanPhase: {
    padding: '4px 0',
    fontSize: '13px',
    transition: 'color 0.3s ease',
  },
  overallBox: {
    padding: '16px',
    background: '#0d1117',
    borderRadius: '12px',
    border: '2px solid',
    marginBottom: '16px',
  },
  overallHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  overallStatus: {
    fontSize: '24px',
    fontWeight: 'bold',
    letterSpacing: '3px',
  },
  overallHealth: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#00d4ff',
  },
  overallStats: {
    display: 'flex',
    gap: '16px',
    fontSize: '13px',
    marginBottom: '8px',
  },
  overallMeta: {
    fontSize: '10px',
    color: '#666',
  },
  category: {
    marginBottom: '12px',
    padding: '12px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #1e3a5f',
  },
  catTitle: {
    margin: '0 0 8px 0',
    fontSize: '12px',
    color: '#666',
    letterSpacing: '2px',
    borderBottom: '1px solid #1e3a5f',
    paddingBottom: '4px',
  },
  systemRow: {
    display: 'grid',
    gridTemplateColumns: '20px 1fr auto',
    gridTemplateRows: 'auto auto',
    gap: '2px 4px',
    padding: '6px 0',
    borderBottom: '1px solid #111827',
  },
  sysName: {
    fontSize: '13px',
    color: '#ccc',
  },
  sysStatus: {
    fontSize: '11px',
    fontWeight: 'bold',
    textAlign: 'right',
  },
  sysDetails: {
    gridColumn: '2 / 4',
    fontSize: '10px',
    color: '#666',
  },
  dnaSection: {
    marginBottom: '12px',
    padding: '12px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #1e4d2b',
  },
  dnaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
    marginBottom: '8px',
  },
  dnaStat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '2px',
  },
  dnaLabel: {
    fontSize: '9px',
    color: '#666',
    letterSpacing: '1px',
  },
  dnaValue: {
    fontSize: '14px',
    color: '#00d4ff',
    fontWeight: 'bold',
  },
  dnaRow: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    fontSize: '12px',
    marginBottom: '4px',
  },
  milestones: {
    marginTop: '8px',
  },
  milestoneList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginTop: '4px',
  },
  milestone: {
    padding: '4px 8px',
    background: '#1e4d2b',
    borderRadius: '6px',
    fontSize: '11px',
    color: '#00ff88',
  },
}
