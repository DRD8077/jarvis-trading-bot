/**
 * 🖥️ JARVIS AI Desktop — Main Electron Process
 * ═══════════════════════════════════════════════
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
 */

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, 
        Notification, shell, screen, nativeTheme, powerMonitor } = require('electron')
const path = require('path')
const fs = require('fs')

let mainWindow = null
let tray = null
let isQuitting = false

// ═══════════════════════════════════
// APP CONFIGURATION
// ═══════════════════════════════════

const isDev = process.argv.includes('--dev')
const WEBAPP_PATH = isDev
  ? 'http://localhost:5173'
  : `file://${path.join(process.resourcesPath, 'webapp', 'index.html')}`

const APP_CONFIG = {
  width: 1280,
  height: 800,
  minWidth: 400,
  minHeight: 600,
  title: 'JARVIS AI Trading — Iron Man Edition',
  icon: path.join(__dirname, 'assets', 'icon.png'),
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
  const iconPath = path.join(__dirname, 'assets', 'tray-icon.png')
  
  // Create a default icon if not exists
  if (!fs.existsSync(iconPath)) {
    // Use app icon fallback
    tray = new Tray(APP_CONFIG.icon || path.join(__dirname, 'assets', 'icon.png'))
  } else {
    tray = new Tray(iconPath)
  }

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
    const { exec } = require('child_process')
    return new Promise((resolve) => {
      exec(command, { timeout: 30000 }, (error, stdout, stderr) => {
        resolve({ success: !error, stdout, stderr, error: error?.message })
      })
    })
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

  console.log('[JARVIS Desktop] IPC handlers registered')
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
// APP LIFECYCLE
// ═══════════════════════════════════

app.whenReady().then(() => {
  console.log('[JARVIS Desktop v6.0] Iron Man Edition starting...')

  createMainWindow()
  createTray()
  registerGlobalShortcuts()
  setupIPC()
  setupPowerMonitoring()

  // Auto-start on boot (user can disable in settings)
  // setupAutoStart()

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
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

// Single instance lock — prevent multiple JARVIS instances
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.show()
      mainWindow.focus()
    }
  })
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('[JARVIS Desktop] Uncaught error:', error)
})

console.log('[JARVIS Desktop] Main process loaded')
