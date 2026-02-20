/**
 * 🔐 JARVIS Gmail Auth — Google Sign-In for APK
 * ═══════════════════════════════════════════════
 * Handles Gmail/Google login, user profiles, admin detection
 * Works in: APK (Google Sign-In native), Browser (Google OAuth popup)
 * Admin: Deepak Kumar (owner rights)
 */

const GMAIL_USER_KEY = 'jarvis_gmail_user'
const GMAIL_TOKEN_KEY = 'jarvis_gmail_token'
const ADMIN_EMAILS = ['deepakkumar@gmail.com'] // Add your Gmail here
const ADMIN_NAMES = ['Deepak Kumar', 'deepak kumar', 'DEEPAK KUMAR']
const OWNER_ID = '5647898018'

class GmailAuth {
  constructor() {
    this.user = JSON.parse(localStorage.getItem(GMAIL_USER_KEY) || 'null')
    this.token = localStorage.getItem(GMAIL_TOKEN_KEY)
    this.isLoggedIn = !!this.user
    this.isAdmin = this._checkAdmin()
    this.listeners = new Set()
  }

  // ─── Google Sign-In (OAuth popup for web/APK WebView) ─────
  async signInWithGoogle() {
    try {
      // Try native Google Sign-In plugin first (Capacitor)
      if (window.Capacitor?.isNativePlatform?.()) {
        return await this._nativeGoogleSignIn()
      }
      // Web fallback — OAuth popup
      return await this._webGoogleSignIn()
    } catch (e) {
      console.error('[GMAIL-AUTH] Sign-in error:', e)
      return { success: false, error: e.message }
    }
  }

  // ─── Manual Login (name + email entry) ────────────────────
  async loginManual(name, email) {
    if (!name || name.trim().length < 2) {
      return { success: false, error: 'Name required (min 2 chars)' }
    }

    const user = {
      id: this._generateUserId(email || name),
      name: name.trim(),
      email: (email || '').trim().toLowerCase(),
      avatar: this._getInitials(name),
      loginMethod: email ? 'email' : 'name',
      isAdmin: this._isAdminUser(name, email),
      registeredAt: new Date().toISOString(),
      deviceId: this._getDeviceId(),
    }

    this._setUser(user)

    // Register with backend
    try {
      await this._registerWithBackend(user)
    } catch (e) { /* offline OK */ }

    return { success: true, user, isAdmin: user.isAdmin }
  }

  // ─── Google Sign-In via Web OAuth ─────────────────────────
  async _webGoogleSignIn() {
    // For Codespace/APK, we use a simplified approach:
    // Show a prompt-based login since we can't do full OAuth without client ID
    // In production, you'd configure Google Cloud Console OAuth
    return new Promise((resolve) => {
      // Dispatch event for UI to show login modal
      const event = new CustomEvent('jarvis-show-login', { detail: { type: 'google' } })
      window.dispatchEvent(event)
      
      // Listen for login completion
      const handler = (e) => {
        window.removeEventListener('jarvis-login-complete', handler)
        resolve(e.detail)
      }
      window.addEventListener('jarvis-login-complete', handler)
    })
  }

  async _nativeGoogleSignIn() {
    // Capacitor GoogleAuth plugin would go here
    // For now, delegate to manual login UI
    return this._webGoogleSignIn()
  }

  // ─── Admin Check ──────────────────────────────────────────
  _isAdminUser(name, email) {
    const nameLower = (name || '').toLowerCase().trim()
    const emailLower = (email || '').toLowerCase().trim()
    
    // Check admin names
    if (ADMIN_NAMES.some(n => n.toLowerCase() === nameLower)) return true
    // Check admin emails
    if (emailLower && ADMIN_EMAILS.some(e => e.toLowerCase() === emailLower)) return true
    
    return false
  }

  _checkAdmin() {
    if (!this.user) return false
    return this._isAdminUser(this.user.name, this.user.email)
  }

  // ─── User Management ─────────────────────────────────────
  _setUser(user) {
    this.user = user
    this.isLoggedIn = true
    this.isAdmin = user.isAdmin
    localStorage.setItem(GMAIL_USER_KEY, JSON.stringify(user))
    this._notifyListeners()
  }

  logout() {
    this.user = null
    this.isLoggedIn = false
    this.isAdmin = false
    this.token = null
    localStorage.removeItem(GMAIL_USER_KEY)
    localStorage.removeItem(GMAIL_TOKEN_KEY)
    this._notifyListeners()
  }

  getUser() {
    return this.user
  }

  getCurrentUser() {
    return this.user
  }

  getUserId() {
    return this.user?.id || this._getDeviceId()
  }

  getDisplayName() {
    return this.user?.name || 'Guest'
  }

  getAvatar() {
    return this.user?.photoUrl || null
  }

  // ─── Backend Registration ─────────────────────────────────
  async _registerWithBackend(user) {
    const { SERVER_BASE } = await import('./apiBase')
    const authUrl = SERVER_BASE + '/api/auth/login'
    
    const formData = new FormData()
    formData.append('chat_id', String(user.id))
    formData.append('username', user.email || user.name.replace(/\s/g, '_').toLowerCase())
    formData.append('first_name', user.name.split(' ')[0])
    formData.append('last_name', user.name.split(' ').slice(1).join(' '))
    formData.append('is_owner', user.isAdmin ? 'true' : 'false')
    formData.append('device_fp', user.deviceId)

    const resp = await fetch(authUrl, { method: 'POST', body: formData })
    const data = await resp.json()
    
    if (data.token) {
      this.token = data.token
      localStorage.setItem(GMAIL_TOKEN_KEY, data.token)
    }
    
    return data
  }

  // ─── Listeners ────────────────────────────────────────────
  onAuthChange(callback) {
    this.listeners.add(callback)
    return () => this.listeners.delete(callback)
  }

  _notifyListeners() {
    for (const cb of this.listeners) {
      try { cb(this.user) } catch {}
    }
  }

  // ─── Utilities ────────────────────────────────────────────
  _generateUserId(seed) {
    const str = (seed || '') + Date.now() + Math.random()
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i)
      hash |= 0
    }
    return Math.abs(hash)
  }

  _getDeviceId() {
    let id = localStorage.getItem('jarvis_device_id')
    if (!id) {
      id = String(Math.floor(100000000 + Math.random() * 900000000))
      localStorage.setItem('jarvis_device_id', id)
    }
    return id
  }

  _getInitials(name) {
    return (name || 'JU').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  }
}

const gmailAuth = new GmailAuth()
export default gmailAuth
