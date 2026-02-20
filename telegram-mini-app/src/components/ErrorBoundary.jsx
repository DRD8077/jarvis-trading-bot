import React from 'react'
import { RefreshCw, AlertTriangle, Home } from 'lucide-react'

/**
 * 🛡️ Global Error Boundary — Catches ANY React crash
 * Instead of white screen, shows a recovery UI
 */
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
    console.error('[JARVIS ErrorBoundary]', error, errorInfo)
    
    // Auto-recover after 5 seconds for transient errors
    if (this.props.autoRecover !== false) {
      setTimeout(() => {
        this.setState({ hasError: false, error: null, errorInfo: null })
      }, 5000)
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    if (typeof window !== 'undefined') {
      window.location.hash = '#/'
      window.location.reload()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-6">
          <div className="max-w-sm w-full text-center space-y-6">
            <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto">
              <AlertTriangle size={32} className="text-red-400" />
            </div>
            <div>
              <h2 className="text-white font-bold text-lg mb-2">Something went wrong</h2>
              <p className="text-slate-400 text-sm">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <button onClick={this.handleRetry} 
                className="flex items-center justify-center gap-2 w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-all active:scale-95">
                <RefreshCw size={18} />
                Try Again
              </button>
              <button onClick={this.handleGoHome}
                className="flex items-center justify-center gap-2 w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium transition-all active:scale-95">
                <Home size={18} />
                Go Home
              </button>
            </div>
            <p className="text-slate-600 text-xs">Auto-recovering in 5s...</p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
