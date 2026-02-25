/**
 * 🖥️ JARVIS AI Desktop — Main Electron Process v8.0
 * ═══════════════════════════════════════════════════
 * 
 * Windows/Mac/Linux desktop app for JARVIS AI Trading.
 * Features:
 * - System tray with quick actions
 * - Global hotkeys (Ctrl+Shift+J to open JARVIS)
 * - Proximity detection (Bluetooth/WiFi)
 * - System control (open apps, run commands, file access)
 * - Always-on-top mode
 * - Native notifications
 * - Auto-start on boot
 * - Hardware acceleration for charts
 * - Volume Control (system-level)
 * - Brightness Management
 * - WhatsApp Automation
 * - Music Playback (YouTube, Spotify)
 * - News Updates
 * - PC Power Control (shutdown, restart, sleep, lock)
 * - Windows Management (minimize, maximize, switch)
 * - Full System Automation
 * - Operating System specs reporting
 */

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, 
        Notification, shell, screen, nativeTheme, powerMonitor, 
        desktopCapturer, session } = require('electron')
const path = require('path')
const fs = require('fs')
const { exec, execSync, spawn } = require('child_process')
const os = require('os')

let mainWindow = null
let tray = null
let isQuitting = false

// Single instance lock — MUST be before any app event handlers
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
  process.exit(0)
}

// ═══════════════════════════════════
// APP CONFIGURATION
// ═══════════════════════════════════

const isDev = process.argv.includes('--dev')

// Determine webapp path with fallbacks
function getWebAppPath() {
  if (isDev) return 'http://localhost:5173'
  
  // Try multiple paths for packaged app
  const candidates = [
    path.join(process.resourcesPath || '', 'webapp', 'index.html'),
    path.join(__dirname, '..', 'webapp', 'index.html'),
    path.join(__dirname, 'webapp', 'index.html'),
    path.join(__dirname, 'dist', 'index.html'),
  ]
  
  for (const p of candidates) {
    if (fs.existsSync(p)) return `file://${p}`
  }
  
  // Fallback to hosted version
  return 'https://super-duper-funicular-gp99q655qw6cprr-8000.app.github.dev'
}

const WEBAPP_PATH = getWebAppPath()

const iconFile = path.join(__dirname, 'assets', 'icon.png')
const APP_CONFIG = {
  width: 1280,
  height: 800,
  minWidth: 400,
  minHeight: 600,
  title: 'JARVIS AI Trading — Iron Man Edition',
  icon: fs.existsSync(iconFile) ? iconFile : undefined,
}

// ═══════════════════════════════════
// WINDOW CREATION
// ═══════════════════════════════════

function createMainWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: APP_CONFIG.width,
    height: APP_CONFIG.height,
    minWidth: APP_CONFIG.minWidth,
    minHeight: APP_CONFIG.minHeight,
    title: APP_CONFIG.title,
    icon: APP_CONFIG.icon,
    backgroundColor: '#0a0e1a',
    show: false,
    frame: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: !isDev,
      spellcheck: false,
      enableBlinkFeatures: 'CSSColorSchemeUARendering',
      backgroundThrottling: false, // Keep running in background
    }
  })

  // ═══ CAMERA PERMISSION — Auto-grant for JARVIS ═══
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowed = ['media', 'mediaKeySystem', 'notifications', 'fullscreen', 'clipboard-read', 'clipboard-sanitized-write']
    if (allowed.includes(permission)) {
      callback(true)
    } else {
      callback(false)
    }
  })

  // Also handle permission check
  session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
    const allowed = ['media', 'mediaKeySystem', 'notifications', 'fullscreen', 'clipboard-read', 'clipboard-sanitized-write']
    return allowed.includes(permission)
  })

  // Load the app
  mainWindow.loadURL(WEBAPP_PATH)

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    console.log('[JARVIS Desktop] Window ready')

    // Send system info to renderer
    mainWindow.webContents.send('system-info', getSystemInfo())
  })

  // Handle close → minimize to tray
  mainWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault()
      mainWindow.hide()
      return false
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  }
}

// ═══════════════════════════════════
// SYSTEM TRAY
// ═══════════════════════════════════

function createTray() {
  try {
    const iconPath = path.join(__dirname, 'assets', 'tray-icon.png')
    const appIcon = APP_CONFIG.icon || path.join(__dirname, 'assets', 'icon.png')
    
    // Find a valid icon path
    let validIcon = null
    if (fs.existsSync(iconPath)) validIcon = iconPath
    else if (fs.existsSync(appIcon)) validIcon = appIcon
    
    if (!validIcon) {
      console.log('[JARVIS Desktop] No tray icon found, skipping tray')
      return
    }
    
    tray = new Tray(validIcon)

  const contextMenu = Menu.buildFromTemplate([
    { label: '🤖 Open JARVIS', click: () => { mainWindow?.show(); mainWindow?.focus() } },
    { type: 'separator' },
    { label: '📊 Dashboard', click: () => navigate('/') },
    { label: '💹 Trading', click: () => navigate('/trading') },
    { label: '🧠 AI Chat', click: () => navigate('/chat') },
    { label: '🎯 Signals', click: () => navigate('/jarvis') },
    { type: 'separator' },
    { label: '🔊 Voice Mode', click: () => sendToRenderer('toggle-voice') },
    { label: '📌 Always on Top', type: 'checkbox', click: (item) => {
      mainWindow?.setAlwaysOnTop(item.checked)
    }},
    { type: 'separator' },
    { label: '⚙️ Settings', click: () => navigate('/settings') },
    { label: '❌ Quit JARVIS', click: () => {
      isQuitting = true
      app.quit()
    }}
  ])

  tray.setToolTip('JARVIS AI Trading — Iron Man Edition')
  tray.setContextMenu(contextMenu)

  tray.on('click', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide()
    } else {
      mainWindow?.show()
      mainWindow?.focus()
    }
  })

  tray.on('double-click', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })
  } catch (err) {
    console.error('[JARVIS Desktop] Tray creation failed:', err.message)
  }
}

function navigate(path) {
  mainWindow?.show()
  mainWindow?.focus()
  mainWindow?.webContents.send('navigate', path)
}

function sendToRenderer(channel, data = {}) {
  mainWindow?.webContents.send(channel, data)
}

// ═══════════════════════════════════
// GLOBAL HOTKEYS
// ═══════════════════════════════════

function registerGlobalShortcuts() {
  if (!app.isReady()) {
    console.log('[JARVIS Desktop] App not ready, skipping shortcut registration')
    return
  }
  try {
  // Ctrl+Shift+J → Toggle JARVIS
  globalShortcut.register('CommandOrControl+Shift+J', () => {
    if (mainWindow?.isVisible() && mainWindow?.isFocused()) {
      mainWindow.hide()
    } else {
      mainWindow?.show()
      mainWindow?.focus()
    }
  })

  // Ctrl+Shift+V → Voice mode
  globalShortcut.register('CommandOrControl+Shift+V', () => {
    mainWindow?.show()
    sendToRenderer('toggle-voice')
  })

  // Ctrl+Shift+T → Quick trade
  globalShortcut.register('CommandOrControl+Shift+T', () => {
    mainWindow?.show()
    navigate('/trading')
  })

  console.log('[JARVIS Desktop] Global shortcuts registered')
  } catch (err) {
    console.error('[JARVIS Desktop] Shortcut registration failed:', err.message)
  }
}

// ═══════════════════════════════════
// SYSTEM INFO
// ═══════════════════════════════════

function getSystemInfo() {
  const os = require('os')
  return {
    platform: process.platform,
    arch: process.arch,
    hostname: os.hostname(),
    username: os.userInfo().name,
    cpus: os.cpus().length,
    totalMemory: (os.totalmem() / 1073741824).toFixed(1) + ' GB',
    freeMemory: (os.freemem() / 1073741824).toFixed(1) + ' GB',
    uptime: (os.uptime() / 3600).toFixed(1) + ' hours',
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
    chromeVersion: process.versions.chrome,
  }
}

// ═══════════════════════════════════
// IPC HANDLERS (Renderer ↔ Main)
// ═══════════════════════════════════

function setupIPC() {
  // System info
  ipcMain.handle('get-system-info', () => getSystemInfo())

  // ═══ OPERATING SYSTEM SPECS ═══
  ipcMain.handle('get-os-specs', () => ({
    platform: process.platform,
    arch: process.arch,
    release: os.release(),
    hostname: os.hostname(),
    username: os.userInfo().name,
    homedir: os.homedir(),
    tmpdir: os.tmpdir(),
    cpus: os.cpus(),
    cpuCount: os.cpus().length,
    cpuModel: os.cpus()[0]?.model || 'Unknown',
    totalMemory: os.totalmem(),
    freeMemory: os.freemem(),
    usedMemory: os.totalmem() - os.freemem(),
    memoryUsagePercent: ((1 - os.freemem() / os.totalmem()) * 100).toFixed(1),
    uptime: os.uptime(),
    loadAvg: os.loadavg(),
    networkInterfaces: os.networkInterfaces(),
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
    chromeVersion: process.versions.chrome,
    v8Version: process.versions.v8,
  }))

  // File operations
  ipcMain.handle('read-file', async (event, filePath) => {
    try {
      return { success: true, data: fs.readFileSync(filePath, 'utf-8') }
    } catch (e) {
      return { success: false, error: e.message }
    }
  })

  ipcMain.handle('write-file', async (event, filePath, content) => {
    try {
      fs.writeFileSync(filePath, content, 'utf-8')
      return { success: true }
    } catch (e) {
      return { success: false, error: e.message }
    }
  })

  ipcMain.handle('list-directory', async (event, dirPath) => {
    try {
      const items = fs.readdirSync(dirPath, { withFileTypes: true })
      return {
        success: true,
        items: items.map(i => ({ name: i.name, isDirectory: i.isDirectory(), isFile: i.isFile() }))
      }
    } catch (e) {
      return { success: false, error: e.message }
    }
  })

  // Open external
  ipcMain.handle('open-external', (event, url) => shell.openExternal(url))
  ipcMain.handle('open-path', (event, p) => shell.openPath(p))

  // Run command
  ipcMain.handle('run-command', async (event, command) => {
    return new Promise((resolve) => {
      exec(command, { timeout: 30000 }, (error, stdout, stderr) => {
        resolve({ success: !error, stdout, stderr, error: error?.message })
      })
    })
  })

  // ═══ VOLUME CONTROL ═══
  ipcMain.handle('volume-up', async () => {
    try {
      if (process.platform === 'win32') {
        exec('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"')
      } else if (process.platform === 'darwin') {
        exec('osascript -e "set volume output volume ((output volume of (get volume settings)) + 10)"')
      } else {
        exec('amixer set Master 10%+')
      }
      return { success: true, message: 'Volume increased' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('volume-down', async () => {
    try {
      if (process.platform === 'win32') {
        exec('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"')
      } else if (process.platform === 'darwin') {
        exec('osascript -e "set volume output volume ((output volume of (get volume settings)) - 10)"')
      } else {
        exec('amixer set Master 10%-')
      }
      return { success: true, message: 'Volume decreased' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('volume-mute', async () => {
    try {
      if (process.platform === 'win32') {
        exec('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
      } else if (process.platform === 'darwin') {
        exec('osascript -e "set volume with output muted"')
      } else {
        exec('amixer set Master toggle')
      }
      return { success: true, message: 'Volume toggled mute' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('volume-set', async (event, level) => {
    try {
      if (process.platform === 'win32') {
        exec(`powershell -c "$wshShell = New-Object -ComObject WScript.Shell; (New-Object -ComObject WScript.Shell).SendKeys([char]173); Start-Sleep -Milliseconds 100; nircmd.exe setsysvolume ${Math.round(level * 655.35)}"`)
      } else if (process.platform === 'darwin') {
        exec(`osascript -e "set volume output volume ${level}"`)
      } else {
        exec(`amixer set Master ${level}%`)
      }
      return { success: true, message: `Volume set to ${level}%` }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ BRIGHTNESS CONTROL ═══
  ipcMain.handle('brightness-up', async () => {
    try {
      if (process.platform === 'win32') {
        exec('powershell -c "$cur = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; $new = [math]::min(100, $cur + 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, $new)"')
      } else if (process.platform === 'darwin') {
        exec('osascript -e "tell application \\"System Events\\" to key code 144"')
      } else {
        exec('xrandr --output $(xrandr | grep " connected" | head -1 | cut -f1 -d " ") --brightness 1.0')
      }
      return { success: true, message: 'Brightness increased' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('brightness-down', async () => {
    try {
      if (process.platform === 'win32') {
        exec('powershell -c "$cur = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; $new = [math]::max(10, $cur - 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, $new)"')
      } else if (process.platform === 'darwin') {
        exec('osascript -e "tell application \\"System Events\\" to key code 145"')
      } else {
        exec('xrandr --output $(xrandr | grep " connected" | head -1 | cut -f1 -d " ") --brightness 0.6')
      }
      return { success: true, message: 'Brightness decreased' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('brightness-set', async (event, level) => {
    try {
      if (process.platform === 'win32') {
        exec(`powershell -c "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, ${level})"`)
      } else if (process.platform === 'darwin') {
        exec(`osascript -e "tell application \\"System Preferences\\" to set brightness of display to ${level / 100}"`)
      } else {
        exec(`xrandr --output $(xrandr | grep " connected" | head -1 | cut -f1 -d " ") --brightness ${level / 100}`)
      }
      return { success: true, message: `Brightness set to ${level}%` }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ PC POWER CONTROL ═══
  ipcMain.handle('pc-shutdown', async () => {
    try {
      if (process.platform === 'win32') exec('shutdown /s /t 5')
      else if (process.platform === 'darwin') exec('osascript -e \'tell app "System Events" to shut down\'')
      else exec('shutdown -h now')
      return { success: true, message: 'Shutting down in 5 seconds...' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('pc-restart', async () => {
    try {
      if (process.platform === 'win32') exec('shutdown /r /t 5')
      else if (process.platform === 'darwin') exec('osascript -e \'tell app "System Events" to restart\'')
      else exec('reboot')
      return { success: true, message: 'Restarting in 5 seconds...' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('pc-sleep', async () => {
    try {
      if (process.platform === 'win32') exec('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
      else if (process.platform === 'darwin') exec('pmset sleepnow')
      else exec('systemctl suspend')
      return { success: true, message: 'Going to sleep...' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('pc-lock', async () => {
    try {
      if (process.platform === 'win32') exec('rundll32.exe user32.dll,LockWorkStation')
      else if (process.platform === 'darwin') exec('pmset displaysleepnow')
      else exec('loginctl lock-session')
      return { success: true, message: 'PC locked!' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('pc-logoff', async () => {
    try {
      if (process.platform === 'win32') exec('shutdown /l')
      else if (process.platform === 'darwin') exec('osascript -e \'tell app "System Events" to log out\'')
      else exec('loginctl terminate-user $USER')
      return { success: true, message: 'Logging off...' }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ WINDOW MANAGEMENT ═══
  ipcMain.handle('window-minimize-all', async () => {
    try {
      if (process.platform === 'win32') exec('powershell -c "(New-Object -ComObject Shell.Application).MinimizeAll()"')
      else if (process.platform === 'darwin') exec('osascript -e \'tell application "System Events" to key code 103 using {command down, option down}\'')
      else exec('wmctrl -k on')
      return { success: true, message: 'All windows minimized' }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('window-switch', async () => {
    try {
      if (process.platform === 'win32') exec('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys(\'%{TAB}\')"')
      else if (process.platform === 'darwin') exec('osascript -e \'tell application "System Events" to key code 48 using {command down}\'')
      return { success: true, message: 'Switching windows' }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ APP MANAGEMENT ═══
  ipcMain.handle('open-app', async (event, appName) => {
    try {
      const appMap = {
        'chrome': process.platform === 'win32' ? 'start chrome' : process.platform === 'darwin' ? 'open -a "Google Chrome"' : 'google-chrome &',
        'firefox': process.platform === 'win32' ? 'start firefox' : process.platform === 'darwin' ? 'open -a Firefox' : 'firefox &',
        'notepad': process.platform === 'win32' ? 'notepad' : 'gedit &',
        'calculator': process.platform === 'win32' ? 'calc' : process.platform === 'darwin' ? 'open -a Calculator' : 'gnome-calculator &',
        'terminal': process.platform === 'win32' ? 'start cmd' : process.platform === 'darwin' ? 'open -a Terminal' : 'gnome-terminal &',
        'explorer': process.platform === 'win32' ? 'explorer' : process.platform === 'darwin' ? 'open .' : 'nautilus . &',
        'vscode': process.platform === 'win32' ? 'code' : 'code &',
        'whatsapp': process.platform === 'win32' ? 'start whatsapp:' : 'xdg-open https://web.whatsapp.com &',
        'spotify': process.platform === 'win32' ? 'start spotify:' : process.platform === 'darwin' ? 'open -a Spotify' : 'spotify &',
      }
      const cmd = appMap[appName.toLowerCase()] || (process.platform === 'win32' ? `start ${appName}` : `${appName} &`)
      exec(cmd)
      return { success: true, message: `Opening ${appName}...` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('close-app', async (event, appName) => {
    try {
      if (process.platform === 'win32') exec(`taskkill /IM ${appName}.exe /F`)
      else exec(`pkill -f ${appName}`)
      return { success: true, message: `Closed ${appName}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ WHATSAPP AUTOMATION ═══
  ipcMain.handle('whatsapp-send', async (event, phone, message) => {
    try {
      const url = `https://api.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(message)}`
      shell.openExternal(url)
      return { success: true, message: `Opening WhatsApp for ${phone}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('whatsapp-open', async () => {
    try {
      if (process.platform === 'win32') exec('start whatsapp:')
      else shell.openExternal('https://web.whatsapp.com')
      return { success: true, message: 'Opening WhatsApp...' }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ MUSIC PLAYBACK ═══
  ipcMain.handle('play-youtube', async (event, query) => {
    try {
      const url = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
      shell.openExternal(url)
      return { success: true, message: `Searching YouTube: ${query}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('play-spotify', async (event, query) => {
    try {
      const url = `https://open.spotify.com/search/${encodeURIComponent(query)}`
      shell.openExternal(url)
      return { success: true, message: `Searching Spotify: ${query}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('media-control', async (event, action) => {
    try {
      if (process.platform === 'win32') {
        const keyMap = { play: 179, pause: 179, next: 176, previous: 177, stop: 178 }
        exec(`powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]${keyMap[action] || 179})"`)
      } else if (process.platform === 'darwin') {
        const keyMap = { play: 'play', pause: 'pause', next: 'next track', previous: 'previous track' }
        exec(`osascript -e 'tell application "System Events" to ${keyMap[action] || "play"}'`)
      } else {
        exec(`dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.${action === 'play' || action === 'pause' ? 'PlayPause' : action === 'next' ? 'Next' : 'Previous'}`)
      }
      return { success: true, message: `Media: ${action}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  // ═══ NEWS ═══
  ipcMain.handle('open-news', async (event, category) => {
    try {
      const urls = {
        'latest': 'https://news.google.com',
        'market': 'https://www.moneycontrol.com/news/',
        'sports': 'https://sports.ndtv.com',
        'tech': 'https://techcrunch.com',
        'india': 'https://www.ndtv.com',
        'world': 'https://www.bbc.com/news/world',
        'crypto': 'https://cointelegraph.com',
      }
      shell.openExternal(urls[category] || urls['latest'])
      return { success: true, message: `Opening ${category} news...` }
    } catch (e) { return { success: false, error: e.message } }
  })

  // Window controls
  ipcMain.handle('minimize', () => mainWindow?.minimize())
  ipcMain.handle('maximize', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize()
    else mainWindow?.maximize()
  })
  ipcMain.handle('close', () => mainWindow?.hide())
  ipcMain.handle('set-always-on-top', (event, value) => mainWindow?.setAlwaysOnTop(value))

  // Notifications
  ipcMain.handle('show-notification', (event, opts) => {
    const notif = new Notification({
      title: opts.title || 'JARVIS',
      body: opts.body || '',
      icon: APP_CONFIG.icon,
      silent: opts.silent || false,
    })
    notif.show()
    notif.on('click', () => {
      mainWindow?.show()
      mainWindow?.focus()
    })
  })

  // Clipboard
  ipcMain.handle('clipboard-write', (event, text) => {
    const { clipboard } = require('electron')
    clipboard.writeText(text)
  })

  ipcMain.handle('clipboard-read', () => {
    const { clipboard } = require('electron')
    return clipboard.readText()
  })

  // App control
  ipcMain.handle('get-app-path', () => app.getPath('userData'))
  ipcMain.handle('get-version', () => app.getVersion())

  // ═══ FILE MANAGEMENT ═══
  ipcMain.handle('create-folder', async (event, folderPath) => {
    try {
      fs.mkdirSync(folderPath, { recursive: true })
      return { success: true, message: `Folder created: ${folderPath}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('delete-file', async (event, filePath) => {
    try {
      fs.unlinkSync(filePath)
      return { success: true, message: `File deleted: ${filePath}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('move-file', async (event, src, dest) => {
    try {
      fs.renameSync(src, dest)
      return { success: true, message: `Moved: ${src} → ${dest}` }
    } catch (e) { return { success: false, error: e.message } }
  })

  ipcMain.handle('get-disk-space', async () => {
    try {
      if (process.platform === 'win32') {
        const result = execSync('wmic logicaldisk get size,freespace,caption', { encoding: 'utf-8' })
        return { success: true, data: result }
      } else {
        const result = execSync('df -h /', { encoding: 'utf-8' })
        return { success: true, data: result }
      }
    } catch (e) { return { success: false, error: e.message } }
  })

  console.log('[JARVIS Desktop v10.0] All IPC handlers registered — Full OS Control + Code Engine + Camera Active!')
}

// ═══════════════════════════════════
// CODE EXECUTION ENGINE (IPC)
// ═══════════════════════════════════

function setupCodeEngine() {
  // Execute code in any language
  ipcMain.handle('execute-code', async (event, code, language, options = {}) => {
    const timeout = options.timeout || 30000
    
    const langMap = {
      'python': { ext: '.py', cmd: 'python3' },
      'javascript': { ext: '.js', cmd: 'node' },
      'typescript': { ext: '.ts', cmd: 'npx ts-node' },
      'ruby': { ext: '.rb', cmd: 'ruby' },
      'go': { ext: '.go', cmd: 'go run' },
      'rust': { ext: '.rs', cmd: null }, // Special handling
      'java': { ext: '.java', cmd: null }, // Special handling
      'c': { ext: '.c', cmd: null },
      'cpp': { ext: '.cpp', cmd: null },
      'shell': { ext: '.sh', cmd: 'bash' },
      'bash': { ext: '.sh', cmd: 'bash' },
      'powershell': { ext: '.ps1', cmd: 'powershell -File' },
    }

    const lang = langMap[language.toLowerCase()]
    if (!lang) {
      // Try direct execution
      return new Promise((resolve) => {
        exec(code, { timeout }, (error, stdout, stderr) => {
          resolve({ success: !error, stdout, stderr, error: error?.message })
        })
      })
    }

    const tmpFile = path.join(os.tmpdir(), `jarvis_exec_${Date.now()}${lang.ext}`)
    
    try {
      fs.writeFileSync(tmpFile, code, 'utf-8')

      let cmd
      if (language === 'rust') {
        const outFile = tmpFile.replace('.rs', '')
        cmd = `rustc "${tmpFile}" -o "${outFile}" && "${outFile}"`
      } else if (language === 'java') {
        const className = code.match(/class\s+(\w+)/)?.[1] || 'JarvisExec'
        const dir = path.dirname(tmpFile)
        const jFile = path.join(dir, `${className}.java`)
        fs.renameSync(tmpFile, jFile)
        cmd = `cd "${dir}" && javac "${className}.java" && java "${className}"`
      } else if (language === 'c') {
        const outFile = tmpFile.replace('.c', '')
        cmd = `gcc "${tmpFile}" -o "${outFile}" && "${outFile}"`
      } else if (language === 'cpp') {
        const outFile = tmpFile.replace('.cpp', '')
        cmd = `g++ "${tmpFile}" -o "${outFile}" && "${outFile}"`
      } else {
        cmd = `${lang.cmd} "${tmpFile}"`
      }

      return new Promise((resolve) => {
        exec(cmd, { timeout, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
          // Cleanup
          try { fs.unlinkSync(tmpFile) } catch {}
          resolve({ success: !error, stdout, stderr, error: error?.message })
        })
      })
    } catch (err) {
      try { fs.unlinkSync(tmpFile) } catch {}
      return { success: false, error: err.message }
    }
  })

  // Screen capture
  ipcMain.handle('capture-screen', async () => {
    try {
      const sources = await desktopCapturer.getSources({ 
        types: ['screen'], 
        thumbnailSize: { width: 1920, height: 1080 } 
      })
      if (sources.length > 0) {
        const thumbnail = sources[0].thumbnail.toDataURL()
        return { success: true, image: thumbnail }
      }
      return { success: false, error: 'No screen found' }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  // Take screenshot of specific window
  ipcMain.handle('capture-window', async (event, windowTitle) => {
    try {
      const sources = await desktopCapturer.getSources({ 
        types: ['window'], 
        thumbnailSize: { width: 1280, height: 720 } 
      })
      const target = windowTitle 
        ? sources.find(s => s.name.toLowerCase().includes(windowTitle.toLowerCase()))
        : sources[0]
      if (target) {
        return { success: true, image: target.thumbnail.toDataURL(), name: target.name }
      }
      return { success: false, error: 'Window not found' }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  // List running processes
  ipcMain.handle('list-processes', async () => {
    return new Promise((resolve) => {
      const cmd = process.platform === 'win32' 
        ? 'tasklist /FO CSV /NH' 
        : 'ps aux --sort=-%mem | head -20'
      exec(cmd, { timeout: 5000 }, (error, stdout) => {
        resolve({ success: !error, data: stdout })
      })
    })
  })

  // Open URL in default browser
  ipcMain.handle('open-url', (event, url) => {
    shell.openExternal(url)
    return { success: true }
  })

  // Get Wi-Fi info
  ipcMain.handle('get-wifi-info', async () => {
    return new Promise((resolve) => {
      const cmd = process.platform === 'win32'
        ? 'netsh wlan show interfaces'
        : process.platform === 'darwin'
        ? '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I'
        : 'iwconfig 2>/dev/null || nmcli device wifi show'
      exec(cmd, { timeout: 5000 }, (error, stdout) => {
        resolve({ success: !error, data: stdout })
      })
    })
  })

  // Get battery info
  ipcMain.handle('get-battery-info', async () => {
    return new Promise((resolve) => {
      const cmd = process.platform === 'win32'
        ? 'WMIC PATH Win32_Battery Get EstimatedChargeRemaining,BatteryStatus'
        : process.platform === 'darwin'
        ? 'pmset -g batt'
        : 'cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo "No battery"'
      exec(cmd, { timeout: 5000 }, (error, stdout) => {
        resolve({ success: !error, data: stdout })
      })
    })
  })

  console.log('[JARVIS Desktop v10.0] Code Engine + Screen Capture active!')
}

// ═══════════════════════════════════
// POWER MONITORING
// ═══════════════════════════════════

function setupPowerMonitoring() {
  powerMonitor.on('suspend', () => {
    console.log('[JARVIS Desktop] System suspending...')
    sendToRenderer('system-suspend')
  })

  powerMonitor.on('resume', () => {
    console.log('[JARVIS Desktop] System resumed!')
    sendToRenderer('system-resume')
    // Force refresh data
    sendToRenderer('refresh-data')
  })

  powerMonitor.on('on-ac', () => sendToRenderer('power-status', { onBattery: false }))
  powerMonitor.on('on-battery', () => sendToRenderer('power-status', { onBattery: true }))

  powerMonitor.on('lock-screen', () => {
    console.log('[JARVIS Desktop] Screen locked')
    sendToRenderer('screen-locked')
  })

  powerMonitor.on('unlock-screen', () => {
    console.log('[JARVIS Desktop] Screen unlocked — Welcome back sir!')
    sendToRenderer('screen-unlocked')
    mainWindow?.show()
  })
}

// ═══════════════════════════════════
// AUTO-START ON BOOT
// ═══════════════════════════════════

function setupAutoStart() {
  const loginSettings = {
    openAtLogin: true,
    openAsHidden: true,
    path: process.execPath,
    args: ['--hidden']
  }

  if (process.platform !== 'linux') {
    app.setLoginItemSettings(loginSettings)
  }
}

// ═══════════════════════════════════
// BACKEND MANAGER
// ═══════════════════════════════════

let backendManager = null
try {
  backendManager = require('./backendManager')
} catch (e) {
  console.log('[JARVIS Desktop] Backend manager not found, running frontend-only mode')
}

// ═══════════════════════════════════
// APP LIFECYCLE
// ═══════════════════════════════════

app.whenReady().then(async () => {
  console.log('[JARVIS Desktop v10.0] ULTIMATE Iron Man Edition starting — Full OS Control + Code Engine + Camera!')

  // Start Python backend first
  if (backendManager) {
    console.log('[JARVIS Desktop] Starting Python AI backend...')
    const backendReady = await backendManager.startBackend()
    if (backendReady) {
      console.log('[JARVIS Desktop] ✅ Python backend running on port 8000')
    } else {
      console.log('[JARVIS Desktop] ⚠️ Backend not available — using remote/hosted mode')
    }
  }

  createMainWindow()
  createTray()
  registerGlobalShortcuts()
  setupIPC()
  setupCodeEngine()
  setupPowerMonitoring()

  // Backend status IPC
  ipcMain.handle('backend-status', () => backendManager?.getStatus() || { running: false })
  ipcMain.handle('backend-restart', async () => {
    if (backendManager) {
      backendManager.stopBackend()
      await new Promise(r => setTimeout(r, 2000))
      return await backendManager.startBackend()
    }
    return false
  })

  // Auto-start on boot
  setupAutoStart()

  // If started with --hidden flag, don't show window
  if (process.argv.includes('--hidden')) {
    mainWindow?.hide()
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
    else mainWindow?.show()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Don't quit — keep tray icon
  }
})

app.on('before-quit', () => {
  isQuitting = true
  // Stop Python backend on quit
  if (backendManager) backendManager.stopBackend()
})

app.on('will-quit', () => {
  try {
    if (app.isReady()) globalShortcut.unregisterAll()
  } catch (e) { /* ignore */ }
  // Ensure backend is stopped
  if (backendManager) backendManager.stopBackend()
})

// Second instance handler (lock acquired at top of file)
app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show()
    mainWindow.focus()
  }
})

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('[JARVIS Desktop] Uncaught error:', error)
})

console.log('[JARVIS Desktop] Main process loaded')
