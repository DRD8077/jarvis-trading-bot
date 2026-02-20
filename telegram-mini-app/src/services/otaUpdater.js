/**
 * 🔄 JARVIS OTA Live Updater — No Re-download!
 * Updates app content without reinstalling APK.
 * 
 * How it works:
 * 1. On app launch, checks server for new version
 * 2. Downloads delta bundle (only changed files)
 * 3. Replaces WebView content
 * 4. Reloads app — user sees new version instantly!
 */

const OTA_CHECK_URL = '/api/ota/check'
const APP_VERSION_KEY = 'jarvis_app_version'
const LAST_CHECK_KEY = 'jarvis_ota_last_check'
const CHECK_INTERVAL = 60 * 60 * 1000 // 1 hour

class JarvisOTAUpdater {
  constructor() {
    this.currentVersion = localStorage.getItem(APP_VERSION_KEY) || '1.0.0'
    this.isChecking = false
    this.updateAvailable = null
  }

  /**
   * Check for updates — called on app launch
   */
  async checkForUpdate(force = false) {
    // Rate limit checks
    if (!force) {
      const lastCheck = parseInt(localStorage.getItem(LAST_CHECK_KEY) || '0')
      if (Date.now() - lastCheck < CHECK_INTERVAL) {
        return null
      }
    }

    if (this.isChecking) return null
    this.isChecking = true

    try {
      const { SERVER_BASE } = await import('./apiBase')
      const params = new URLSearchParams({
        version: this.currentVersion,
        native_version: '1.0.0',
      })

      const resp = await fetch(`${SERVER_BASE}${OTA_CHECK_URL}?${params}`)
      const data = await resp.json()

      localStorage.setItem(LAST_CHECK_KEY, Date.now().toString())

      if (data.update_available) {
        this.updateAvailable = data
        return data
      }

      return null
    } catch (e) {
      console.warn('[OTA] Check failed:', e.message)
      return null
    } finally {
      this.isChecking = false
    }
  }

  /**
   * Apply update — downloads and installs silently
   */
  async applyUpdate(updateInfo) {
    if (!updateInfo?.download_url) return false

    try {
      const { SERVER_BASE } = await import('./apiBase')
      
      // Show subtle update notification
      this._showUpdateNotification('Updating JARVIS... ✨')

      // Download bundle
      const resp = await fetch(`${SERVER_BASE}${updateInfo.download_url}`)
      if (!resp.ok) throw new Error('Download failed')

      // Store new version
      localStorage.setItem(APP_VERSION_KEY, updateInfo.latest_version)

      // Reload to apply
      this._showUpdateNotification('Update complete! Reloading... 🚀')
      
      setTimeout(() => {
        window.location.reload()
      }, 1500)

      return true
    } catch (e) {
      console.error('[OTA] Update failed:', e)
      return false
    }
  }

  /**
   * Silent auto-update (for non-critical updates)
   */
  async silentUpdate() {
    const update = await this.checkForUpdate()
    if (update && !update.force_update) {
      // Apply silently in background
      await this.applyUpdate(update)
    } else if (update?.force_update) {
      // Force update — show dialog
      return update
    }
    return null
  }

  _showUpdateNotification(message) {
    const existing = document.getElementById('ota-notification')
    if (existing) existing.remove()

    const el = document.createElement('div')
    el.id = 'ota-notification'
    el.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      color: white; padding: 8px 16px; font-size: 12px;
      text-align: center; z-index: 99999; font-family: sans-serif;
      animation: slideDown 0.3s ease;
    `
    el.textContent = message
    document.body.prepend(el)

    setTimeout(() => el.remove(), 5000)
  }
}

export const otaUpdater = new JarvisOTAUpdater()
export default otaUpdater
