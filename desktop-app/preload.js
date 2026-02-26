/**
 * 🔐 JARVIS Desktop — Preload Script v8.0
 * ════════════════════════════════════════
 * 
 * Secure bridge between Electron main process and renderer.
 * Exposes safe APIs via contextBridge.
 * Full OS control: Volume, Brightness, Power, Apps, WhatsApp, Music, News
 */

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('jarvisDesktop', {
  // ═══ Platform Info ═══
  isDesktop: true,
  isJarvisOS: true,
  platform: process.platform,
  version: '16.0.0',

  // ═══ System ═══
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getOsSpecs: () => ipcRenderer.invoke('get-os-specs'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  getDiskSpace: () => ipcRenderer.invoke('get-disk-space'),

  // ═══ Code Execution Engine ═══
  executeCode: (code, language, options) => ipcRenderer.invoke('execute-code', code, language, options),

  // ═══ Screen Capture ═══
  captureScreen: () => ipcRenderer.invoke('capture-screen'),
  captureWindow: (title) => ipcRenderer.invoke('capture-window', title),

  // ═══ Process Management ═══
  listProcesses: () => ipcRenderer.invoke('list-processes'),

  // ═══ Network Info ═══
  getWifiInfo: () => ipcRenderer.invoke('get-wifi-info'),
  getBatteryInfo: () => ipcRenderer.invoke('get-battery-info'),

  // ═══ URL Opening ═══
  openUrl: (url) => ipcRenderer.invoke('open-url', url),

  // ═══ System ═══
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getOsSpecs: () => ipcRenderer.invoke('get-os-specs'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  getDiskSpace: () => ipcRenderer.invoke('get-disk-space'),

  // ═══ Window Controls ═══
  minimize: () => ipcRenderer.invoke('minimize'),
  maximize: () => ipcRenderer.invoke('maximize'),
  close: () => ipcRenderer.invoke('close'),
  setAlwaysOnTop: (value) => ipcRenderer.invoke('set-always-on-top', value),
  toggleFullscreen: () => ipcRenderer.invoke('toggle-fullscreen'),
  getWindowState: () => ipcRenderer.invoke('get-window-state'),

  // ═══ File System ═══
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  writeFile: (path, content) => ipcRenderer.invoke('write-file', path, content),
  listDirectory: (path) => ipcRenderer.invoke('list-directory', path),
  createFolder: (path) => ipcRenderer.invoke('create-folder', path),
  deleteFile: (path) => ipcRenderer.invoke('delete-file', path),
  moveFile: (src, dest) => ipcRenderer.invoke('move-file', src, dest),

  // ═══ Shell ═══
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  openPath: (path) => ipcRenderer.invoke('open-path', path),
  runCommand: (cmd) => ipcRenderer.invoke('run-command', cmd),

  // ═══ Volume Control ═══
  volumeUp: () => ipcRenderer.invoke('volume-up'),
  volumeDown: () => ipcRenderer.invoke('volume-down'),
  volumeMute: () => ipcRenderer.invoke('volume-mute'),
  volumeSet: (level) => ipcRenderer.invoke('volume-set', level),

  // ═══ Brightness Control ═══
  brightnessUp: () => ipcRenderer.invoke('brightness-up'),
  brightnessDown: () => ipcRenderer.invoke('brightness-down'),
  brightnessSet: (level) => ipcRenderer.invoke('brightness-set', level),

  // ═══ PC Power Control ═══
  pcShutdown: () => ipcRenderer.invoke('pc-shutdown'),
  pcRestart: () => ipcRenderer.invoke('pc-restart'),
  pcSleep: () => ipcRenderer.invoke('pc-sleep'),
  pcLock: () => ipcRenderer.invoke('pc-lock'),
  pcLogoff: () => ipcRenderer.invoke('pc-logoff'),

  // ═══ Window Management ═══
  minimizeAll: () => ipcRenderer.invoke('window-minimize-all'),
  switchWindow: () => ipcRenderer.invoke('window-switch'),

  // ═══ App Management ═══
  openApp: (name) => ipcRenderer.invoke('open-app', name),
  closeApp: (name) => ipcRenderer.invoke('close-app', name),

  // ═══ WhatsApp Automation ═══
  whatsappSend: (phone, msg) => ipcRenderer.invoke('whatsapp-send', phone, msg),
  whatsappOpen: () => ipcRenderer.invoke('whatsapp-open'),

  // ═══ Music Playback ═══
  playYouTube: (query) => ipcRenderer.invoke('play-youtube', query),
  playSpotify: (query) => ipcRenderer.invoke('play-spotify', query),
  mediaControl: (action) => ipcRenderer.invoke('media-control', action),

  // ═══ News ═══
  openNews: (category) => ipcRenderer.invoke('open-news', category),

  // ═══ Clipboard ═══
  clipboardWrite: (text) => ipcRenderer.invoke('clipboard-write', text),
  clipboardRead: () => ipcRenderer.invoke('clipboard-read'),

  // ═══ Notifications ═══
  showNotification: (opts) => ipcRenderer.invoke('show-notification', opts),

  // ═══ Event Listeners ═══
  on: (channel, callback) => {
    const validChannels = ['navigate', 'toggle-voice', 'system-suspend', 'system-resume', 
      'screen-locked', 'screen-unlocked', 'power-status', 'system-info', 'refresh-data']
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (e, data) => callback(data))
    }
  },
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

console.log('[JARVIS Desktop v16.0] Preload script loaded — Full OS Control + JARVIS OS Shell APIs available')
