/**
 * 🎨 JARVIS Theme Engine
 * ════════════════════════
 * Dark, AMOLED Black, and Light themes
 * Auto-applies CSS variables for instant theme switching
 * Persists preference in localStorage
 */

const THEMES = {
  dark: {
    name: 'Dark',
    bg: '#0a0e1a',
    bgCard: 'rgba(30, 41, 59, 0.5)',
    bgNav: 'rgba(15, 23, 42, 0.85)',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: 'rgba(148, 163, 184, 0.08)',
    accent: '#3b82f6',
  },
  amoled: {
    name: 'AMOLED Black',
    bg: '#000000',
    bgCard: 'rgba(15, 15, 15, 0.9)',
    bgNav: 'rgba(0, 0, 0, 0.95)',
    text: '#ffffff',
    textSecondary: '#737373',
    border: 'rgba(255, 255, 255, 0.06)',
    accent: '#3b82f6',
  },
  light: {
    name: 'Light',
    bg: '#f8fafc',
    bgCard: 'rgba(255, 255, 255, 0.9)',
    bgNav: 'rgba(248, 250, 252, 0.95)',
    text: '#0f172a',
    textSecondary: '#64748b',
    border: 'rgba(0, 0, 0, 0.08)',
    accent: '#2563eb',
  }
}

class ThemeEngine {
  constructor() {
    this.current = localStorage.getItem('jarvis_theme') || 'dark'
    this.listeners = new Set()
    this._apply(this.current)
  }

  getTheme() {
    return this.current
  }

  getThemes() {
    return Object.entries(THEMES).map(([id, theme]) => ({ id, ...theme }))
  }

  setTheme(themeId) {
    if (!THEMES[themeId]) return
    this.current = themeId
    localStorage.setItem('jarvis_theme', themeId)
    this._apply(themeId)
    this.listeners.forEach(cb => cb(themeId))
  }

  toggle() {
    const keys = Object.keys(THEMES)
    const idx = keys.indexOf(this.current)
    const next = keys[(idx + 1) % keys.length]
    this.setTheme(next)
    return next
  }

  _apply(themeId) {
    const theme = THEMES[themeId]
    if (!theme) return

    const root = document.documentElement
    root.style.setProperty('--jarvis-bg', theme.bg)
    root.style.setProperty('--jarvis-bg-card', theme.bgCard)
    root.style.setProperty('--jarvis-bg-nav', theme.bgNav)
    root.style.setProperty('--jarvis-text', theme.text)
    root.style.setProperty('--jarvis-text-secondary', theme.textSecondary)
    root.style.setProperty('--jarvis-border', theme.border)
    root.style.setProperty('--jarvis-accent', theme.accent)

    // Update body background
    document.body.style.background = theme.bg
    document.body.style.color = theme.text

    // Update meta theme-color for Android status bar
    let meta = document.querySelector('meta[name="theme-color"]')
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'theme-color'
      document.head.appendChild(meta)
    }
    meta.content = theme.bg

    // Add/remove AMOLED class for special styling
    if (themeId === 'amoled') {
      document.body.classList.add('amoled-theme')
      document.body.classList.remove('light-theme')
    } else if (themeId === 'light') {
      document.body.classList.add('light-theme')
      document.body.classList.remove('amoled-theme')
    } else {
      document.body.classList.remove('amoled-theme', 'light-theme')
    }
  }

  onChange(callback) {
    this.listeners.add(callback)
    return () => this.listeners.delete(callback)
  }

  isDark() {
    return this.current === 'dark' || this.current === 'amoled'
  }

  isAmoled() {
    return this.current === 'amoled'
  }
}

const themeEngine = new ThemeEngine()
export default themeEngine
export { THEMES }
