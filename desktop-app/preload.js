/**
 * 🔐 JARVIS Desktop — Preload Script
 * ═══════════════════════════════════
 * 
 * Secure bridge between Electron main process and renderer.
 * Exposes safe APIs via contextBridge.
 */

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('jarvisDesktop', {
  // ═══ Platform Info ═══
  isDesktop: true,
  platform: process.platform,

  // ═══ System ═══
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),

  // ═══ Window Controls ═══
  minimize: () => ipcRenderer.invoke('minimize'),
  maximize: () => ipcRenderer.invoke('maximize'),
  close: () => ipcRenderer.invoke('close'),
  setAlwaysOnTop: (value) => ipcRenderer.invoke('set-always-on-top', value),

  // ═══ File System ═══
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  writeFile: (path, content) => ipcRenderer.invoke('write-file', path, content),
  listDirectory: (path) => ipcRenderer.invoke('list-directory', path),

  // ═══ Shell ═══
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  openPath: (path) => ipcRenderer.invoke('open-path', path),
  runCommand: (cmd) => ipcRenderer.invoke('run-command', cmd),

  // ═══ Clipboard ═══
  clipboardWrite: (text) => ipcRenderer.invoke('clipboard-write', text),
  clipboardRead: () => ipcRenderer.invoke('clipboard-read'),

  // ═══ Notifications ═══
  showNotification: (opts) => ipcRenderer.invoke('show-notification', opts),

  // ═══ Event Listeners ═══
  onNavigate: (callback) => ipcRenderer.on('navigate', (e, path) => callback(path)),
  onToggleVoice: (callback) => ipcRenderer.on('toggle-voice', () => callback()),
  onSystemSuspend: (callback) => ipcRenderer.on('system-suspend', () => callback()),
  onSystemResume: (callback) => ipcRenderer.on('system-resume', () => callback()),
  onScreenLocked: (callback) => ipcRenderer.on('screen-locked', () => callback()),
  onScreenUnlocked: (callback) => ipcRenderer.on('screen-unlocked', () => callback()),
  onPowerStatus: (callback) => ipcRenderer.on('power-status', (e, data) => callback(data)),
  onSystemInfo: (callback) => ipcRenderer.on('system-info', (e, data) => callback(data)),
  onRefreshData: (callback) => ipcRenderer.on('refresh-data', () => callback()),

  // ═══ Remove Listeners ═══
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
})

console.log('[JARVIS Desktop] Preload script loaded — Desktop APIs available')
