import { useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

// Main tab order for swipe navigation
const TAB_ORDER = ['/', '/trading', '/ai-agent', '/chat']

export default function useSwipeNavigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const touchRef = useRef({ startX: 0, startY: 0, startTime: 0 })

  const onTouchStart = useCallback((e) => {
    const touch = e.touches[0]
    touchRef.current = {
      startX: touch.clientX,
      startY: touch.clientY,
      startTime: Date.now()
    }
  }, [])

  const onTouchEnd = useCallback((e) => {
    const touch = e.changedTouches[0]
    const { startX, startY, startTime } = touchRef.current
    const deltaX = touch.clientX - startX
    const deltaY = touch.clientY - startY
    const elapsed = Date.now() - startTime

    // Must be a fast horizontal swipe (>80px, <400ms, more horizontal than vertical)
    if (Math.abs(deltaX) < 80 || elapsed > 400 || Math.abs(deltaY) > Math.abs(deltaX) * 0.7) {
      return
    }

    const currentIndex = TAB_ORDER.indexOf(location.pathname)
    if (currentIndex === -1) return // Not on a main tab — don't swipe

    const direction = deltaX > 0 ? -1 : 1 // swipe left = next, swipe right = prev
    const nextIndex = currentIndex + direction

    if (nextIndex >= 0 && nextIndex < TAB_ORDER.length) {
      // Add transition class for animation
      const main = document.querySelector('main')
      if (main) {
        main.classList.add(direction > 0 ? 'page-transition-enter' : 'page-transition-exit')
        setTimeout(() => {
          main.classList.remove('page-transition-enter', 'page-transition-exit')
        }, 300)
      }
      navigate(TAB_ORDER[nextIndex])
    }
  }, [navigate, location.pathname])

  return { onTouchStart, onTouchEnd }
}
