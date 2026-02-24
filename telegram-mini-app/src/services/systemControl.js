/**
 * 🖥️ JARVIS System Control Engine
 * ═══════════════════════════════════
 * 
 * Gives JARVIS control over your laptop/desktop.
 * Works on both Desktop (Electron) and Web (limited).
 * 
 * Capabilities:
 * - Open apps & URLs
 * - Read/Write files
 * - Run terminal commands
 * - System notifications
 * - Clipboard management
 * - Screen brightness/volume (where supported)
 * - Process monitoring
 */

class SystemControlEngine {
  constructor() {
    this.isDesktop = !!window.jarvisDesktop
    this.capabilities = this._detectCapabilities()
    this.commandHistory = []
  }

  _detectCapabilities() {
    const caps = {
      fileSystem: !!window.jarvisDesktop,
      shell: !!window.jarvisDesktop,
      clipboard: !!navigator.clipboard,
      notifications: 'Notification' in window,
      speech: 'speechSynthesis' in window,
      recognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
      battery: 'getBattery' in navigator,
      bluetooth: 'bluetooth' in navigator,
      geolocation: 'geolocation' in navigator,
      vibrate: 'vibrate' in navigator,
      mediaDevices: !!navigator.mediaDevices,
      share: !!navigator.share,
      wakeLock: 'wakeLock' in navigator,
      usb: 'usb' in navigator,
      serial: 'serial' in navigator,
      isDesktop: !!window.jarvisDesktop,
    }
    return caps
  }

  // ═══════════════════════════════════
  // FILE SYSTEM (Desktop only)
  // ═══════════════════════════════════

  async readFile(path) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.readFile(path)
    }
    // Web fallback: File System Access API
    if (window.showOpenFilePicker) {
      try {
        const [handle] = await window.showOpenFilePicker()
        const file = await handle.getFile()
        const text = await file.text()
        return { success: true, data: text }
      } catch (e) {
        return { success: false, error: e.message }
      }
    }
    return { success: false, error: 'File system not available' }
  }

  async writeFile(path, content) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.writeFile(path, content)
    }
    // Web fallback
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker()
        const writable = await handle.createWritable()
        await writable.write(content)
        await writable.close()
        return { success: true }
      } catch (e) {
        return { success: false, error: e.message }
      }
    }
    return { success: false, error: 'File system not available' }
  }

  async listDirectory(path) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.listDirectory(path)
    }
    return { success: false, error: 'Desktop only feature' }
  }

  // ═══════════════════════════════════
  // SHELL / COMMANDS (Desktop only)
  // ═══════════════════════════════════

  async runCommand(command) {
    this.commandHistory.push({ command, timestamp: Date.now() })
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.runCommand(command)
    }
    return { success: false, error: 'Desktop only feature. Install JARVIS Desktop for full system control.' }
  }

  async openApp(appName) {
    const appMap = {
      'chrome': { win: 'start chrome', mac: 'open -a "Google Chrome"', linux: 'google-chrome' },
      'firefox': { win: 'start firefox', mac: 'open -a Firefox', linux: 'firefox' },
      'notepad': { win: 'start notepad', mac: 'open -a TextEdit', linux: 'gedit' },
      'calculator': { win: 'start calc', mac: 'open -a Calculator', linux: 'gnome-calculator' },
      'terminal': { win: 'start cmd', mac: 'open -a Terminal', linux: 'gnome-terminal' },
      'explorer': { win: 'start explorer', mac: 'open .', linux: 'nautilus .' },
      'vscode': { win: 'code', mac: 'code', linux: 'code' },
    }

    const app = appMap[appName.toLowerCase()]
    if (!app) {
      // Try direct command
      return this.runCommand(appName)
    }

    const platform = this._getPlatform()
    return this.runCommand(app[platform] || app.linux)
  }

  async openURL(url) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.openExternal(url)
    }
    window.open(url, '_blank')
    return { success: true }
  }

  async openFolder(path) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.openPath(path)
    }
    return { success: false, error: 'Desktop only' }
  }

  // ═══════════════════════════════════
  // CLIPBOARD
  // ═══════════════════════════════════

  async copyToClipboard(text) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.clipboardWrite(text)
    }
    try {
      await navigator.clipboard.writeText(text)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.message }
    }
  }

  async readClipboard() {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.clipboardRead()
    }
    try {
      return await navigator.clipboard.readText()
    } catch (e) {
      return ''
    }
  }

  // ═══════════════════════════════════
  // NOTIFICATIONS
  // ═══════════════════════════════════

  async notify(title, body, options = {}) {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.showNotification({ title, body, ...options })
    }
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/icons/icon-192.png', ...options })
      return { success: true }
    }
    return { success: false }
  }

  // ═══════════════════════════════════
  // SCREEN / POWER
  // ═══════════════════════════════════

  async keepScreenOn() {
    if ('wakeLock' in navigator) {
      try {
        const lock = await navigator.wakeLock.request('screen')
        return { success: true, lock }
      } catch (e) {
        return { success: false, error: e.message }
      }
    }
    return { success: false, error: 'Wake Lock not supported' }
  }

  async getBatteryInfo() {
    if ('getBattery' in navigator) {
      try {
        const battery = await navigator.getBattery()
        return {
          level: Math.round(battery.level * 100),
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        }
      } catch {
        return null
      }
    }
    return null
  }

  // ═══════════════════════════════════
  // SYSTEM INFO
  // ═══════════════════════════════════

  async getSystemInfo() {
    if (window.jarvisDesktop) {
      return window.jarvisDesktop.getSystemInfo()
    }
    return {
      platform: navigator.platform,
      userAgent: navigator.userAgent,
      language: navigator.language,
      onLine: navigator.onLine,
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory,
      maxTouchPoints: navigator.maxTouchPoints,
      isDesktop: false
    }
  }

  // ═══════════════════════════════════
  // NATURAL LANGUAGE COMMAND PARSER
  // ═══════════════════════════════════

  async executeNaturalCommand(text) {
    const cmd = text.toLowerCase().trim()

    // Open app commands
    const openMatch = cmd.match(/(?:open|kholo|start|chalu karo)\s+(.+)/i)
    if (openMatch) {
      const target = openMatch[1].trim()
      // Check if URL
      if (target.includes('.com') || target.includes('.in') || target.includes('http')) {
        const url = target.startsWith('http') ? target : `https://${target}`
        await this.openURL(url)
        return { action: 'open_url', target: url, response: `${target} khol raha hoon sir!` }
      }
      await this.openApp(target)
      return { action: 'open_app', target, response: `${target} start kar raha hoon sir!` }
    }

    // Copy/clipboard
    if (cmd.includes('copy') || cmd.includes('clipboard')) {
      const content = await this.readClipboard()
      return { action: 'clipboard', content, response: `Clipboard mein hai sir: "${content?.substring(0, 50)}..."` }
    }

    // Battery
    if (cmd.includes('battery') || cmd.includes('charge') || cmd.includes('kitna charge')) {
      const battery = await this.getBatteryInfo()
      if (battery) {
        return { action: 'battery', data: battery, response: `Sir, battery ${battery.level}% hai${battery.charging ? ', aur charge ho raha hai' : ''}` }
      }
      return { action: 'battery', response: 'Battery info available nahi hai sir' }
    }

    // System info
    if (cmd.includes('system') || cmd.includes('computer') || cmd.includes('laptop')) {
      const info = await this.getSystemInfo()
      return { action: 'system_info', data: info, response: `Sir, aapka system: ${info.platform || info.hostname}, ${info.cpus || info.hardwareConcurrency} cores, ${info.totalMemory || info.deviceMemory + 'GB'} RAM` }
    }

    // Run command (advanced)
    if (cmd.startsWith('run ') || cmd.startsWith('execute ') || cmd.startsWith('terminal ')) {
      const command = cmd.replace(/^(run|execute|terminal)\s+/i, '')
      const result = await this.runCommand(command)
      return { action: 'command', result, response: result.success ? `Command executed sir: ${result.stdout?.substring(0, 100)}` : `Error sir: ${result.error}` }
    }

    return null
  }

  _getPlatform() {
    if (window.jarvisDesktop?.platform === 'win32') return 'win'
    if (window.jarvisDesktop?.platform === 'darwin') return 'mac'
    if (navigator.platform?.includes('Win')) return 'win'
    if (navigator.platform?.includes('Mac')) return 'mac'
    return 'linux'
  }

  getCapabilities() {
    return this.capabilities
  }
}

const systemControl = new SystemControlEngine()
export default systemControl
export { SystemControlEngine }
