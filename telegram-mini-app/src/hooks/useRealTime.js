/**
 * ⚡ useRealTime — React Hook for Live Data
 * ═══════════════════════════════════════════
 * Connects any component to the real-time engine
 * Auto-subscribes on mount, auto-unsubscribes on unmount
 * Smart refresh, WebSocket-first, polling fallback
 */
import { useState, useEffect, useRef, useCallback } from 'react'
// Dynamic import — do NOT import realtime at module scope
let _realtimeCache = null
async function getRealtime() {
  if (_realtimeCache) return _realtimeCache
  try {
    const mod = await import('../services/realtime')
    _realtimeCache = mod?.default || mod
    return _realtimeCache
  } catch (e) {
    console.warn('[useRealTime] realtime load failed:', e.message)
    return null
  }
}

/**
 * Hook to subscribe to real-time data channel
 * @param {string} channel - Data channel name (e.g., 'dashboard', 'indian_stocks')
 * @param {Function} fetcher - API function to call () => Promise<AxiosResponse>
 * @param {object} opts
 * @param {number} opts.interval - Polling interval in ms (default: 10000)
 * @param {boolean} opts.enabled - Whether to auto-fetch (default: true)
 * @param {Function} opts.transform - Transform data before setting state
 * @param {*} opts.initialData - Initial data before first fetch
 */
export function useRealTime(channel, fetcher, opts = {}) {
  const {
    interval = 10000,
    enabled = true,
    transform = null,
    initialData = null
  } = opts

  const [data, setData] = useState(initialData)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [error, setError] = useState(null)
  const mountedRef = useRef(true)
  const firstLoadRef = useRef(true)

  const handleData = useCallback((rawData, ts) => {
    if (!mountedRef.current) return
    try {
      const processed = transform ? transform(rawData) : rawData
      setData(processed)
      setLastUpdate(ts || new Date().toISOString())
      setError(null)
      if (firstLoadRef.current) {
        setLoading(false)
        firstLoadRef.current = false
      }
    } catch (e) {
      setError(e.message)
    }
  }, [transform])

  // Manual refresh function
  const refresh = useCallback(async () => {
    if (!fetcher) return
    try {
      const result = await fetcher()
      const rawData = result?.data?.data || result?.data || result
      handleData(rawData, new Date().toISOString())
    } catch (e) {
      if (mountedRef.current) {
        setError(e.message)
      }
    }
  }, [fetcher, handleData])

  useEffect(() => {
    mountedRef.current = true
    firstLoadRef.current = true
    setLoading(true)

    if (!enabled || !fetcher) {
      setLoading(false)
      return
    }

    let unsub = () => {}
    getRealtime().then(rt => {
      if (!rt || typeof rt.subscribe !== 'function' || !mountedRef.current) return
      unsub = rt.subscribe(channel, handleData, {
        interval,
        fetcher
      })
    }).catch(() => {})

    return () => {
      mountedRef.current = false
      unsub()
    }
  }, [channel, enabled, interval]) // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, lastUpdate, error, refresh }
}

/**
 * Hook for ticker/price data (uses WebSocket when available)
 */
export function useTickerData() {
  const [tickers, setTickers] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let unsubTicker = () => {}
    let unsubStatus = () => {}
    getRealtime().then(rt => {
      if (!rt || typeof rt.subscribe !== 'function') return
      unsubTicker = rt.subscribe('ticker', (data) => {
        if (Array.isArray(data)) setTickers(data)
      })
      unsubStatus = rt.subscribe('_status', (status) => {
        setConnected(status.connected)
      })
    }).catch(() => {})

    return () => { unsubTicker(); unsubStatus() }
  }, [])

  return { tickers, connected }
}

/**
 * Hook for auto-refreshing any API endpoint
 * Simpler than useRealTime — just wraps setInterval with smart refresh
 * @param {Function} fetcher - () => Promise<AxiosResponse>
 * @param {number} intervalMs - Refresh interval (default: 10000 = 10s)
 * @param {Array} deps - Additional dependencies
 */
export function useAutoRefresh(fetcher, intervalMs = 10000, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const mountedRef = useRef(true)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const result = await fetcherRef.current()
      if (mountedRef.current) {
        const d = result?.data?.data || result?.data || result
        setData(d)
        setLastUpdate(new Date().toLocaleTimeString('en-IN'))
        setLoading(false)
        setRefreshing(false)
      }
    } catch (e) {
      if (mountedRef.current) {
        setLoading(false)
        setRefreshing(false)
      }
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    load(false)
    const iv = setInterval(() => load(true), intervalMs)
    return () => {
      mountedRef.current = false
      clearInterval(iv)
    }
  }, [intervalMs, ...deps]) // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, refreshing, lastUpdate, refresh: () => load(true) }
}

export default useRealTime
