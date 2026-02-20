import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Error Boundary to catch React rendering errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('[JARVIS] React Error:', error, errorInfo)
    // Also show in our global overlay
    if (window.__jarvisShowError) {
      window.__jarvisShowError(
        'React Error: ' + (error?.message || error),
        errorInfo?.componentStack?.split('\n')[1] || '',
        0, 0, error
      )
    }
  }
  render() {
    if (this.state.hasError) {
      return React.createElement('div', {
        style: { padding: 20, background: '#0a0e1a', color: '#f1f5f9', minHeight: '100vh', fontFamily: 'monospace' }
      },
        React.createElement('h2', { style: { color: '#ef4444' } }, '⚠️ JARVIS App Error'),
        React.createElement('p', { style: { color: '#fbbf24', fontSize: 14 } },
          String(this.state.error?.message || this.state.error || 'Unknown error')
        ),
        this.state.errorInfo && React.createElement('pre', {
          style: { color: '#94a3b8', fontSize: 11, overflow: 'auto', maxHeight: 300, background: '#1e293b', padding: 12, borderRadius: 8 }
        }, this.state.errorInfo.componentStack),
        React.createElement('button', {
          onClick: () => window.location.reload(),
          style: { background: '#3b82f6', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: 8, marginTop: 12, cursor: 'pointer' }
        }, '🔄 Reload')
      )
    }
    return this.props.children
  }
}

// Init with error catching
try {
  console.log('[JARVIS] main.jsx — starting React app...')
  console.log('[JARVIS] location:', window.location.href)
  console.log('[JARVIS] Capacitor:', typeof window.Capacitor, window.Capacitor?.getPlatform?.())

  const rootEl = document.getElementById('root')
  if (!rootEl) {
    throw new Error('Root element #root not found in DOM')
  }

  ReactDOM.createRoot(rootEl).render(
    React.createElement(ErrorBoundary, null,
      React.createElement(App)
    )
  )

  console.log('[JARVIS] React render called successfully')
} catch (err) {
  console.error('[JARVIS] FATAL startup error:', err)
  if (window.__jarvisShowError) {
    window.__jarvisShowError(
      'FATAL: ' + (err?.message || err),
      err?.fileName || 'main.jsx',
      err?.lineNumber || 0, 0, err
    )
  }
  // Fallback: write error directly to root
  const root = document.getElementById('root')
  if (root) {
    root.innerHTML = '<div style="padding:20px;color:#ef4444;font-family:monospace"><h2>JARVIS Startup Failed</h2><p>' +
      String(err?.message || err) + '</p><pre style="color:#94a3b8;font-size:11px;overflow:auto">' +
      String(err?.stack || '') + '</pre><button onclick="location.reload()" style="background:#3b82f6;color:#fff;border:none;padding:10px 20px;border-radius:8px;margin-top:12px">Reload</button></div>'
  }
}
