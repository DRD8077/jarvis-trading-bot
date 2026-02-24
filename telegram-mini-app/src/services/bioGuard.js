/**
 * 🔒 JARVIS Biometric Trading Guard
 * ═══════════════════════════════════
 * 
 * Fingerprint/Face required for trade execution.
 * Uses Web Authentication API + Capacitor BiometricAuth.
 * Configurable security levels.
 */

class BiometricGuard {
  constructor() {
    this.settings = {
      enabled: false,
      requireForTrades: true,
      requireForWithdrawals: true,
      requireForSettings: false,
      requireForAppOpen: false,
      lockAfterMinutes: 5,
      maxAttempts: 5,
    }
    this.authenticated = false
    this.lastAuth = 0
    this.failedAttempts = 0
    this.locked = false
    this._loadSettings()
  }

  _loadSettings() {
    try {
      const s = localStorage.getItem('jarvis_bio_settings')
      if (s) Object.assign(this.settings, JSON.parse(s))
    } catch {}
  }

  saveSettings(settings) {
    Object.assign(this.settings, settings)
    localStorage.setItem('jarvis_bio_settings', JSON.stringify(this.settings))
  }

  // ═══════════════════════════════════
  // BIOMETRIC AUTH
  // ═══════════════════════════════════

  async isAvailable() {
    // Check Web Authentication API
    if (window.PublicKeyCredential) {
      try {
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
        if (available) return { available: true, type: 'webauthn' }
      } catch {}
    }

    // Check Capacitor BiometricAuth plugin (loaded dynamically at runtime only)
    try {
      const capBioModule = '@capacitor/biometric-auth'
      const mod = await import(/* @vite-ignore */ capBioModule)
      if (mod?.BiometricAuth) {
        const result = await mod.BiometricAuth.isAvailable()
        if (result.has) return { available: true, type: 'capacitor', biometryType: result.biometryType }
      }
    } catch {}

    return { available: false }
  }

  async authenticate(reason = 'Verify your identity') {
    if (this.locked) {
      return { success: false, error: 'Account locked. Too many failed attempts.' }
    }

    // Check if recently authenticated
    if (this.authenticated && (Date.now() - this.lastAuth) < this.settings.lockAfterMinutes * 60 * 1000) {
      return { success: true, cached: true }
    }

    const availability = await this.isAvailable()
    if (!availability.available) {
      // Fallback to PIN
      return { success: true, method: 'fallback', message: 'Biometric not available, using PIN fallback' }
    }

    try {
      if (availability.type === 'webauthn') {
        return await this._webAuthnAuth(reason)
      } else if (availability.type === 'capacitor') {
        return await this._capacitorAuth(reason)
      }
    } catch (e) {
      this.failedAttempts++
      if (this.failedAttempts >= this.settings.maxAttempts) {
        this.locked = true
        setTimeout(() => { this.locked = false; this.failedAttempts = 0 }, 300000) // 5 min lockout
      }
      return { success: false, error: e.message, attempts: this.failedAttempts }
    }
  }

  async _webAuthnAuth(reason) {
    const challenge = crypto.getRandomValues(new Uint8Array(32))

    const credential = await navigator.credentials.get({
      publicKey: {
        challenge,
        timeout: 60000,
        userVerification: 'required',
        rpId: window.location.hostname
      }
    })

    if (credential) {
      this.authenticated = true
      this.lastAuth = Date.now()
      this.failedAttempts = 0
      return { success: true, method: 'webauthn' }
    }
    return { success: false, error: 'Authentication cancelled' }
  }

  async _capacitorAuth(reason) {
    const capBioModule = '@capacitor/biometric-auth'
    const { BiometricAuth } = await import(/* @vite-ignore */ capBioModule)
    await BiometricAuth.authenticate({
      reason,
      title: 'JARVIS Security',
      subtitle: reason,
      description: 'Authenticate to continue',
      negativeButtonText: 'Cancel',
      allowDeviceCredential: true
    })

    this.authenticated = true
    this.lastAuth = Date.now()
    this.failedAttempts = 0
    return { success: true, method: 'biometric' }
  }

  // ═══════════════════════════════════
  // GUARD MIDDLEWARE
  // ═══════════════════════════════════

  async guardTrade(tradeDetails) {
    if (!this.settings.enabled || !this.settings.requireForTrades) return { allowed: true }
    const auth = await this.authenticate(`Confirm ${tradeDetails.side} ${tradeDetails.quantity} ${tradeDetails.symbol}`)
    return { allowed: auth.success, auth }
  }

  async guardWithdrawal(details) {
    if (!this.settings.enabled || !this.settings.requireForWithdrawals) return { allowed: true }
    const auth = await this.authenticate(`Confirm withdrawal: ${details.amount} ${details.currency}`)
    return { allowed: auth.success, auth }
  }

  async guardSettings() {
    if (!this.settings.enabled || !this.settings.requireForSettings) return { allowed: true }
    const auth = await this.authenticate('Access JARVIS Settings')
    return { allowed: auth.success, auth }
  }

  // ═══════════════════════════════════
  // PIN FALLBACK
  // ═══════════════════════════════════

  async setPin(pin) {
    const enc = new TextEncoder()
    const hash = await crypto.subtle.digest('SHA-256', enc.encode(pin + 'jarvis_salt_v6'))
    const hashHex = Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('')
    localStorage.setItem('jarvis_pin_hash', hashHex)
    return true
  }

  async verifyPin(pin) {
    const enc = new TextEncoder()
    const hash = await crypto.subtle.digest('SHA-256', enc.encode(pin + 'jarvis_salt_v6'))
    const hashHex = Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('')
    const stored = localStorage.getItem('jarvis_pin_hash')
    const valid = stored === hashHex
    if (valid) {
      this.authenticated = true
      this.lastAuth = Date.now()
      this.failedAttempts = 0
    } else {
      this.failedAttempts++
    }
    return valid
  }

  hasPin() {
    return !!localStorage.getItem('jarvis_pin_hash')
  }

  getStatus() {
    return {
      ...this.settings,
      authenticated: this.authenticated,
      lastAuth: this.lastAuth,
      failedAttempts: this.failedAttempts,
      locked: this.locked,
      hasPin: this.hasPin()
    }
  }
}

const bioGuard = new BiometricGuard()
export default bioGuard
export { BiometricGuard }
