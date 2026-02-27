/**
 * 🔔 JARVIS NOTIFICATION OVERLAY — Iron Man Style On-Screen Alerts
 * ═══════════════════════════════════════════════════════════════
 * 
 * Floating notification stack with:
 * - Glowing borders per type (red=danger, gold=warning, green=success, blue=info)
 * - Slide-in animation
 * - Auto-dismiss with progress bar
 * - Priority stacking
 */

import React, { useState, useEffect } from 'react'

export default function JarvisNotificationOverlay() {
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    const handler = (e) => {
      setNotifications(e.detail?.notifications || [])
    }
    window.addEventListener('jarvis-notification-update', handler)
    return () => window.removeEventListener('jarvis-notification-update', handler)
  }, [])

  if (notifications.length === 0) return null

  const typeColors = {
    info: { border: '#00d4ff', bg: '#00d4ff11', glow: '#00d4ff33' },
    success: { border: '#00ff88', bg: '#00ff8811', glow: '#00ff8833' },
    warning: { border: '#ffaa00', bg: '#ffaa0011', glow: '#ffaa0033' },
    danger: { border: '#ff4444', bg: '#ff444411', glow: '#ff444433' },
  }

  const dismissNotif = (id) => {
    import('../services/jarvisNotifications.js').then(m => m.default.dismiss(id))
  }

  return (
    <div style={styles.container}>
      {notifications.map((n, i) => {
        const colors = typeColors[n.type] || typeColors.info
        return (
          <div
            key={n.id}
            onClick={() => dismissNotif(n.id)}
            style={{
              ...styles.notif,
              borderColor: colors.border,
              background: colors.bg,
              boxShadow: `0 0 15px ${colors.glow}, inset 0 0 20px ${colors.glow}`,
              animationDelay: `${i * 0.1}s`,
            }}
          >
            <div style={styles.notifHeader}>
              <span style={{...styles.notifTitle, color: colors.border}}>{n.title}</span>
              <span style={styles.notifTime}>
                {new Date(n.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}
              </span>
            </div>
            {n.message && <div style={styles.notifMessage}>{n.message}</div>}
            {/* Progress bar for auto-dismiss */}
            <div style={styles.progressBg}>
              <div style={{
                ...styles.progress,
                background: colors.border,
                animation: `shrink ${n.duration || 6000}ms linear forwards`,
              }} />
            </div>
          </div>
        )
      })}
      <style>{`
        @keyframes shrink { from { width: 100%; } to { width: 0%; } }
        @keyframes slideIn { from { transform: translateX(100%); opacity:0; } to { transform: translateX(0); opacity:1; } }
      `}</style>
    </div>
  )
}

const styles = {
  container: {
    position: 'fixed',
    top: '60px',
    right: '8px',
    width: '280px',
    zIndex: 300,
    pointerEvents: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  notif: {
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid',
    backdropFilter: 'blur(10px)',
    cursor: 'pointer',
    animation: 'slideIn 0.3s ease-out forwards',
    fontFamily: "'Courier New', monospace",
  },
  notifHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  notifTitle: {
    fontSize: '11px',
    fontWeight: 'bold',
    letterSpacing: '1px',
  },
  notifTime: {
    fontSize: '9px',
    color: '#666',
  },
  notifMessage: {
    fontSize: '12px',
    color: '#ccc',
    lineHeight: '1.3',
  },
  progressBg: {
    width: '100%',
    height: '2px',
    background: '#1a1a2e',
    borderRadius: '1px',
    marginTop: '6px',
    overflow: 'hidden',
  },
  progress: {
    height: '100%',
    borderRadius: '1px',
  },
}
