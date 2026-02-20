/**
 * 🔐 JARVIS Smart Auth — Owner/User Recognition
 * APK understands who is owner and who are users!
 */

const AUTH_TOKEN_KEY = 'jarvis_auth_token'
const USER_DATA_KEY = 'jarvis_user_data'

class JarvisAuth {
  constructor() {
    this.token = localStorage.getItem(AUTH_TOKEN_KEY)
    this.user = JSON.parse(localStorage.getItem(USER_DATA_KEY) || 'null')
    this.isOwner = this.user?.is_owner || false
  }

  /**
   * Login — auto-detects owner vs user
   */
  async login(chatId, username = '', firstName = '') {
    try {
      // Use saved Gmail user data
      const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || 'null')

      const formData = new FormData()
      formData.append('chat_id', chatId || savedUser?.id || '0')
      formData.append('username', username || savedUser?.name || '')
      formData.append('first_name', firstName || savedUser?.name?.split(' ')[0] || '')
      formData.append('device_fp', this._getDeviceFingerprint())

      const { SERVER_BASE } = await import('./apiBase')
      const resp = await fetch(`${SERVER_BASE}/api/auth/login`, {
        method: 'POST',
        body: formData,
      })

      const data = await resp.json()

      if (data.success) {
        this.token = data.token
        this.user = data.user
        this.isOwner = data.is_owner

        localStorage.setItem(AUTH_TOKEN_KEY, data.token)
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(data.user))

        console.log(`[AUTH] Logged in as ${data.is_owner ? '👑 OWNER' : '👤 User'} — Tier: ${data.tier}`)
        return data
      }

      return { success: false, error: data.error || 'Login failed' }
    } catch (e) {
      console.error('[AUTH] Login error:', e)
      return { success: false, error: e.message }
    }
  }

  /**
   * Auto-login on app start
   */
  async autoLogin() {
    // Use saved Gmail user data
    const savedUser = JSON.parse(localStorage.getItem('jarvis_gmail_user') || 'null')

    if (savedUser?.id) {
      return this.login(String(savedUser.id), savedUser.name, savedUser.name?.split(' ')[0])
    }

    // Try saved session
    if (this.token) {
      const valid = await this.verifySession()
      if (valid) return { success: true, user: this.user, is_owner: this.isOwner }
    }

    return { success: false, error: 'No session' }
  }

  /**
   * Verify current session
   */
  async verifySession() {
    if (!this.token) return false

    try {
      const { SERVER_BASE } = await import('./apiBase')
      const resp = await fetch(`${SERVER_BASE}/api/auth/verify`, {
        headers: { 'Authorization': `Bearer ${this.token}` },
      })

      if (resp.ok) {
        const data = await resp.json()
        this.user = data.user
        this.isOwner = data.is_owner
        return true
      }
    } catch {}

    return false
  }

  /**
   * Check permission
   */
  hasPermission(permission) {
    if (this.isOwner) return true
    const perms = this.user?.permissions || {}
    return perms[permission] || false
  }

  /**
   * Get auth headers for API calls
   */
  getHeaders() {
    const headers = {}
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`
    return headers
  }

  /**
   * Logout
   */
  logout() {
    this.token = null
    this.user = null
    this.isOwner = false
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(USER_DATA_KEY)
  }

  /**
   * Device fingerprint for security
   */
  _getDeviceFingerprint() {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillText('JARVIS-FP', 2, 2)

    const data = [
      navigator.userAgent,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      navigator.language,
      navigator.platform,
      canvas.toDataURL(),
    ].join('|')

    // Simple hash
    let hash = 0
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash |= 0
    }
    return Math.abs(hash).toString(36)
  }
}

export const jarvisAuth = new JarvisAuth()
export default jarvisAuth
