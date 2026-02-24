/**
 * 🔐 JARVIS Encrypted Vault
 * ══════════════════════════
 * 
 * AES-256-GCM encrypted storage for sensitive data.
 * API keys, passwords, exchange secrets — all encrypted at rest.
 * Uses Web Crypto API (native browser, zero dependencies).
 * Optional biometric unlock integration.
 */

const VAULT_STORE = 'jarvis_vault'
const VAULT_KEY_NAME = 'jarvis_vault_key'
const SALT_LENGTH = 16
const IV_LENGTH = 12

class EncryptedVault {
  constructor() {
    this.masterKey = null
    this.unlocked = false
    this.cache = new Map()
  }

  // ═══════════════════════════════════
  // KEY DERIVATION
  // ═══════════════════════════════════

  async _deriveKey(password, salt) {
    const enc = new TextEncoder()
    const keyMaterial = await crypto.subtle.importKey(
      'raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']
    )
    return crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    )
  }

  async _getOrCreateMasterKey() {
    // Try to load existing key from IndexedDB
    const stored = await this._idbGet(VAULT_KEY_NAME)
    if (stored) {
      return crypto.subtle.importKey('jwk', stored, 'AES-GCM', true, ['encrypt', 'decrypt'])
    }

    // Generate new master key
    const key = await crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']
    )

    // Export and store
    const exported = await crypto.subtle.exportKey('jwk', key)
    await this._idbSet(VAULT_KEY_NAME, exported)
    return key
  }

  // ═══════════════════════════════════
  // ENCRYPT / DECRYPT
  // ═══════════════════════════════════

  async encrypt(plaintext) {
    if (!this.masterKey) throw new Error('Vault is locked')
    const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH))
    const enc = new TextEncoder()
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv }, this.masterKey, enc.encode(plaintext)
    )
    // Combine IV + ciphertext
    const combined = new Uint8Array(iv.length + ciphertext.byteLength)
    combined.set(iv, 0)
    combined.set(new Uint8Array(ciphertext), iv.length)
    return btoa(String.fromCharCode(...combined))
  }

  async decrypt(cipherB64) {
    if (!this.masterKey) throw new Error('Vault is locked')
    const combined = Uint8Array.from(atob(cipherB64), c => c.charCodeAt(0))
    const iv = combined.slice(0, IV_LENGTH)
    const ciphertext = combined.slice(IV_LENGTH)
    const dec = new TextDecoder()
    const plaintext = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv }, this.masterKey, ciphertext
    )
    return dec.decode(plaintext)
  }

  // ═══════════════════════════════════
  // VAULT OPERATIONS
  // ═══════════════════════════════════

  async unlock(pin = null) {
    try {
      if (pin) {
        // PIN-based unlock
        const salt = await this._idbGet('vault_salt') || crypto.getRandomValues(new Uint8Array(SALT_LENGTH))
        if (!(await this._idbGet('vault_salt'))) {
          await this._idbSet('vault_salt', salt)
        }
        this.masterKey = await this._deriveKey(pin, salt)
      } else {
        // Auto-unlock using stored key
        this.masterKey = await this._getOrCreateMasterKey()
      }
      this.unlocked = true
      console.log('[Vault] Unlocked successfully')
      return true
    } catch (e) {
      console.error('[Vault] Unlock failed:', e.message)
      return false
    }
  }

  lock() {
    this.masterKey = null
    this.unlocked = false
    this.cache.clear()
    console.log('[Vault] Locked')
  }

  async store(key, value) {
    const plaintext = typeof value === 'object' ? JSON.stringify(value) : String(value)
    const encrypted = await this.encrypt(plaintext)
    await this._idbSet(`vault_${key}`, encrypted)
    this.cache.set(key, value)
    return true
  }

  async retrieve(key) {
    if (this.cache.has(key)) return this.cache.get(key)
    const encrypted = await this._idbGet(`vault_${key}`)
    if (!encrypted) return null
    try {
      const plaintext = await this.decrypt(encrypted)
      // Try to parse as JSON
      try { 
        const parsed = JSON.parse(plaintext)
        this.cache.set(key, parsed)
        return parsed
      } catch {
        this.cache.set(key, plaintext)
        return plaintext
      }
    } catch {
      return null
    }
  }

  async remove(key) {
    await this._idbDelete(`vault_${key}`)
    this.cache.delete(key)
  }

  async listKeys() {
    const allKeys = await this._idbAllKeys()
    return allKeys.filter(k => k.startsWith('vault_') && k !== 'vault_salt')
      .map(k => k.replace('vault_', ''))
  }

  // ═══════════════════════════════════
  // SECURE API KEY MANAGEMENT
  // ═══════════════════════════════════

  async storeAPIKey(service, apiKey, apiSecret = null) {
    await this.store(`apikey_${service}`, { key: apiKey, secret: apiSecret, stored_at: Date.now() })
  }

  async getAPIKey(service) {
    return await this.retrieve(`apikey_${service}`)
  }

  async storeExchangeCredentials(exchange, credentials) {
    await this.store(`exchange_${exchange}`, {
      ...credentials,
      stored_at: Date.now()
    })
  }

  async getExchangeCredentials(exchange) {
    return await this.retrieve(`exchange_${exchange}`)
  }

  // ═══════════════════════════════════
  // IndexedDB Helper
  // ═══════════════════════════════════

  _openDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(VAULT_STORE, 1)
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains('vault')) {
          req.result.createObjectStore('vault')
        }
      }
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
  }

  async _idbSet(key, value) {
    const db = await this._openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readwrite')
      tx.objectStore('vault').put(value, key)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  async _idbGet(key) {
    const db = await this._openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readonly')
      const req = tx.objectStore('vault').get(key)
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
  }

  async _idbDelete(key) {
    const db = await this._openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readwrite')
      tx.objectStore('vault').delete(key)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  async _idbAllKeys() {
    const db = await this._openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readonly')
      const req = tx.objectStore('vault').getAllKeys()
      req.onsuccess = () => resolve(req.result || [])
      req.onerror = () => reject(req.error)
    })
  }

  // ═══════════════════════════════════
  // STATUS
  // ═══════════════════════════════════

  isUnlocked() { return this.unlocked }

  async getStatus() {
    const keys = await this.listKeys()
    return {
      unlocked: this.unlocked,
      storedKeys: keys.length,
      cachedKeys: this.cache.size,
      keys: keys
    }
  }
}

const encryptedVault = new EncryptedVault()
export default encryptedVault
export { EncryptedVault }
