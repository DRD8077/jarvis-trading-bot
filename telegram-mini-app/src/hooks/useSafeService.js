import { useState, useEffect, useRef } from 'react'

/**
 * 🛡️ JARVIS Safe Service Hook
 * ═══════════════════════════════
 * Dynamically imports a service module with full crash isolation.
 * If the service constructor crashes, the component still renders.
 * 
 * Usage:
 *   const myService = useSafeService(() => import('../services/myService'))
 *   // myService is null until loaded, then the default export
 *   if (myService) myService.doSomething()
 */
export function useSafeService(importFn) {
  const [service, setService] = useState(null)
  const loaded = useRef(false)

  useEffect(() => {
    if (loaded.current) return
    loaded.current = true
    
    importFn()
      .then(mod => {
        setService(mod?.default || mod)
      })
      .catch(e => {
        console.warn('[JARVIS] Service load failed:', e.message)
      })
  }, [])

  return service
}

/**
 * Load multiple services at once
 * Usage:
 *   const { realtime, autoRefresh } = useSafeServices({
 *     realtime: () => import('../services/realtime'),
 *     autoRefresh: () => import('../services/autoRefreshEngine'),
 *   })
 */
export function useSafeServices(importMap) {
  const [services, setServices] = useState({})
  const loaded = useRef(false)

  useEffect(() => {
    if (loaded.current) return
    loaded.current = true

    const entries = Object.entries(importMap)
    Promise.all(
      entries.map(([name, importFn]) =>
        importFn()
          .then(mod => [name, mod?.default || mod])
          .catch(e => {
            console.warn(`[JARVIS] ${name} load failed:`, e.message)
            return [name, null]
          })
      )
    ).then(results => {
      setServices(Object.fromEntries(results))
    })
  }, [])

  return services
}

/**
 * Safely call a method on a service (never throws)
 */
export function safeCall(service, method, ...args) {
  try {
    if (service && typeof service[method] === 'function') {
      const result = service[method](...args)
      if (result && typeof result.catch === 'function') result.catch(() => {})
      return result
    }
  } catch (e) {
    console.warn(`[JARVIS] ${method}() error:`, e.message)
  }
  return null
}

export default { useSafeService, useSafeServices, safeCall }
