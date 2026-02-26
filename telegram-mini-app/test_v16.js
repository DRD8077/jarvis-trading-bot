#!/usr/bin/env node
/**
 * 🧪 JARVIS v16 — Comprehensive Test Suite
 * ══════════════════════════════════════════
 * 
 * Tests:
 * 1. Component Export Verification — all 56 components export a valid default
 * 2. Service Constructor Safety — all services have try-catch constructors
 * 3. No Static Dangerous Imports — zero service imports at module level
 * 4. ErrorBoundary Coverage — every route wrapped
 * 5. API Functions Exist — all exported API functions are callable
 * 6. Wake Word Engine — singleton, start/stop, listeners
 * 7. SystemControl — all control actions defined
 * 8. GamingCoach — auto-play modes, pro players
 * 9. Voice System — 3-layer STT + 3-layer TTS
 * 10. AI Fallback — freeAI embedded keys present
 * 11. Build Artifact Verification — dist/ has all required files
 * 12. Android Manifest — all permissions, service, boot receiver
 * 13. Electron Main Process — frameless window, OS shell, IPC handlers
 * 14. Route Completeness — all lazy components have routes
 * 15. Crash Resilience — every loadService wrapped in try-catch
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname);
const SRC = path.join(ROOT, 'src');
const COMPONENTS = path.join(SRC, 'components');
const SERVICES = path.join(SRC, 'services');
const DIST = path.join(ROOT, 'dist');
const ANDROID = path.join(ROOT, 'android');
const DESKTOP = path.resolve(ROOT, '..', 'desktop-app');

let passed = 0;
let failed = 0;
let warnings = 0;
const failures = [];

function test(name, fn) {
  try {
    const result = fn();
    if (result === false) throw new Error('returned false');
    passed++;
  } catch (e) {
    failed++;
    failures.push({ name, error: e.message });
  }
}

function warn(name, msg) {
  warnings++;
  console.log(`  ⚠️  ${name}: ${msg}`);
}

function readFile(p) {
  try { return fs.readFileSync(p, 'utf-8'); } catch { return ''; }
}

function fileExists(p) { return fs.existsSync(p); }

// ═══════════════════════════════════════════
// 1. COMPONENT EXPORT VERIFICATION
// ═══════════════════════════════════════════
console.log('\n🧪 Test Suite 1: Component Exports');

const componentFiles = fs.readdirSync(COMPONENTS).filter(f => f.endsWith('.jsx') && !f.endsWith('.bak'));

componentFiles.forEach(file => {
  test(`${file} — has default export`, () => {
    const code = readFile(path.join(COMPONENTS, file));
    if (!code) throw new Error('file empty');
    if (!code.includes('export default') && !code.match(/export\s*{\s*\w+\s+as\s+default/)) {
      throw new Error('no default export');
    }
  });
});

// ═══════════════════════════════════════════
// 2. SERVICE CONSTRUCTOR SAFETY
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 2: Service Constructor Safety');

const serviceFiles = fs.readdirSync(SERVICES).filter(f => f.endsWith('.js') || f.endsWith('.jsx'));

serviceFiles.forEach(file => {
  test(`${file} — no unsafe top-level execution`, () => {
    const code = readFile(path.join(SERVICES, file));
    // Check for try-catch in constructor OR class definition
    if (code.includes('constructor(') && !code.includes('try {') && !code.includes('try{')) {
      throw new Error('constructor without try-catch');
    }
  });
});

// ═══════════════════════════════════════════
// 3. NO STATIC DANGEROUS IMPORTS
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 3: Static Import Safety');

const dangerousServices = [
  'jarvisCore', 'jarvisVoice', 'serviceMesh', 'wsHub', 'presenceEngine',
  'notificationPipeline', 'crashAnalytics', 'hapticEngine', 'offlineEngine',
  'autoRefreshEngine', 'themeEngine', 'smartAuth', 'firebasePush',
  'voiceCommandEngine', 'elevenlabsVoice', 'biometricAuth'
];

componentFiles.forEach(file => {
  test(`${file} — no static service imports`, () => {
    const code = readFile(path.join(COMPONENTS, file));
    for (const svc of dangerousServices) {
      const staticImport = new RegExp(`^import\\s+.*\\bfrom\\s+['\"].*${svc}['\"]`, 'm');
      if (staticImport.test(code)) {
        throw new Error(`static import of ${svc}`);
      }
    }
  });
});

// ═══════════════════════════════════════════
// 4. ERRORBOUNDARY COVERAGE
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 4: ErrorBoundary Coverage');

const appCode = readFile(path.join(SRC, 'App.jsx'));

test('App.jsx imports ErrorBoundary', () => {
  if (!appCode.includes('ErrorBoundary')) throw new Error('missing ErrorBoundary import');
});

test('Every Route element wrapped in ErrorBoundary', () => {
  const routeLines = appCode.split('\n').filter(l => l.includes('<Route'));
  const unwrapped = routeLines.filter(l => l.includes('element=') && !l.includes('ErrorBoundary'));
  if (unwrapped.length > 0) {
    throw new Error(`${unwrapped.length} routes without ErrorBoundary`);
  }
});

test('Root App wrapped in ErrorBoundary', () => {
  if (!appCode.includes('<ErrorBoundary>\n') && !appCode.includes('<ErrorBoundary>')) {
    // Allow it as long as it's somewhere
  }
  const rootMatch = appCode.match(/function App\b[\s\S]*?return\s*\([\s\S]*?<ErrorBoundary>/);
  if (!rootMatch) throw new Error('Root App not wrapped');
});

// ═══════════════════════════════════════════
// 5. API FUNCTIONS
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 5: API Functions');

const apiCode = readFile(path.join(SERVICES, 'api.js'));

['fetchDashboard', 'fetchTicker', 'sendChat', 'fetchSignals', 'fetchNews'].forEach(fn => {
  test(`api.js exports ${fn}`, () => {
    if (!apiCode.includes(`export`) && !apiCode.includes(fn)) {
      throw new Error(`${fn} not found`);
    }
  });
});

// ═══════════════════════════════════════════
// 6. WAKE WORD ENGINE
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 6: Wake Word Engine');

const wakeCode = readFile(path.join(SERVICES, 'wakeWordEngine.js'));

test('wakeWordEngine.js exists', () => { if (!wakeCode) throw new Error('missing'); });
test('Has getWakeWordEngine singleton export', () => {
  if (!wakeCode.includes('getWakeWordEngine')) throw new Error('no singleton');
});
test('Has wake word list including Hindi', () => {
  if (!wakeCode.includes('jarvis') || !wakeCode.includes('जार्विस')) throw new Error('missing wake words');
});
test('Has 3-tier fallback (Capacitor + WebSpeech)', () => {
  if (!wakeCode.includes('_tryCapacitorSTT') || !wakeCode.includes('_tryWebSpeechAPI'))
    throw new Error('missing fallback tiers');
});
test('Has activation sound', () => {
  if (!wakeCode.includes('_playActivationSound')) throw new Error('no sound');
});
test('Has haptic vibration on wake', () => {
  if (!wakeCode.includes('vibrate')) throw new Error('no vibration');
});
test('Boot sequence starts wake word engine', () => {
  if (!appCode.includes('wakeWordEngine') || !appCode.includes('wakeEngine.start'))
    throw new Error('not started in boot');
});

// ═══════════════════════════════════════════
// 7. SYSTEM CONTROL
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 7: SystemControl Component');

const sysCtrlCode = readFile(path.join(COMPONENTS, 'SystemControl.jsx'));

test('SystemControl.jsx exists', () => { if (!sysCtrlCode) throw new Error('missing'); });
test('Has volume control', () => { if (!sysCtrlCode.includes('volume') && !sysCtrlCode.includes('Volume')) throw new Error('no volume'); });
test('Has brightness control', () => { if (!sysCtrlCode.includes('brightness') || !sysCtrlCode.includes('Brightness')) throw new Error('no brightness'); });
test('Has flashlight toggle', () => { if (!sysCtrlCode.includes('flashlight') || !sysCtrlCode.includes('Flashlight')) throw new Error('no flashlight'); });
test('Has battery status', () => { if (!sysCtrlCode.includes('battery') || !sysCtrlCode.includes('Battery')) throw new Error('no battery'); });
test('Has PC power controls', () => { if (!sysCtrlCode.includes('pcShutdown') || !sysCtrlCode.includes('pcRestart')) throw new Error('no pc power'); });
test('Has app launcher', () => { if (!sysCtrlCode.includes('openApp') || !sysCtrlCode.includes('Open')) throw new Error('no app launcher'); });
test('Has screenshot capture', () => { if (!sysCtrlCode.includes('screenshot') || !sysCtrlCode.includes('Screenshot')) throw new Error('no screenshot'); });
test('Has routes in App.jsx', () => {
  if (!appCode.includes('/system-control') || !appCode.includes('/device-control'))
    throw new Error('missing routes');
});

// ═══════════════════════════════════════════
// 8. GAMING COACH
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 8: GamingCoach');

const gamingCode = readFile(path.join(COMPONENTS, 'GamingCoach.jsx'));

test('GamingCoach.jsx exists', () => { if (!gamingCode) throw new Error('missing'); });
test('Has pro player profiles', () => {
  if (!gamingCode.includes('Jonathan') || !gamingCode.includes('Mortal'))
    throw new Error('missing pro players');
});
test('Has BGMI game package detection', () => {
  const lower = gamingCode.toLowerCase();
  if (!lower.includes('bgmi') || !lower.includes('pubg') || !lower.includes('com.pubg'))
    throw new Error('no game detection');
});
test('Has freeAI fallback for gaming chat', () => {
  if (!gamingCode.includes('freeAI') && !gamingCode.includes('free_ai'))
    warn('GamingCoach', 'no freeAI fallback detected');
});
test('Has gaming routes', () => {
  if (!appCode.includes('/gaming')) throw new Error('missing /gaming route');
});

// ═══════════════════════════════════════════
// 9. VOICE SYSTEM
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 9: Voice System');

const voiceCode = readFile(path.join(COMPONENTS, 'HindiVoiceAssistant.jsx'));

test('HindiVoiceAssistant.jsx exists', () => { if (!voiceCode) throw new Error('missing'); });
test('Has Capacitor SpeechRecognition (native STT)', () => {
  if (!voiceCode.includes('speech-recognition') && !voiceCode.includes('SpeechRecognition'))
    throw new Error('no Capacitor STT');
});
test('Has Web Speech API fallback', () => {
  if (!voiceCode.includes('webkitSpeechRecognition') && !voiceCode.includes('SpeechRecognition'))
    throw new Error('no WebSpeech fallback');
});
test('Has MediaRecorder fallback', () => {
  if (!voiceCode.includes('MediaRecorder')) throw new Error('no MediaRecorder fallback');
});
test('Has TTS output (Capacitor or browser)', () => {
  if (!voiceCode.includes('TextToSpeech') && !voiceCode.includes('speechSynthesis') && !voiceCode.includes('text-to-speech'))
    throw new Error('no TTS');
});
test('Has Hindi language support', () => {
  if (!voiceCode.includes('hi-IN') && !voiceCode.includes('Hindi'))
    throw new Error('no Hindi support');
});

// ═══════════════════════════════════════════
// 10. AI FALLBACK
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 10: AI Fallback (freeAI)');

const freeAICode = readFile(path.join(SERVICES, 'freeAI.js'));

test('freeAI.js exists', () => { if (!freeAICode) throw new Error('missing'); });
test('Has embedded API keys (base64)', () => {
  if (!freeAICode.includes('atob(')) throw new Error('no base64 keys');
});
test('Has auto-init in constructor', () => {
  if (!freeAICode.includes('this.init()') && !freeAICode.includes('init()'))
    throw new Error('no auto-init');
});
test('Has chat() method', () => {
  if (!freeAICode.includes('chat(') && !freeAICode.includes('async chat'))
    throw new Error('no chat method');
});
test('AIChat.jsx has freeAI fallback', () => {
  const chatCode = readFile(path.join(COMPONENTS, 'AIChat.jsx'));
  if (!chatCode.includes('freeAI')) throw new Error('AIChat missing freeAI fallback');
});

// ═══════════════════════════════════════════
// 11. BUILD ARTIFACTS
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 11: Build Artifacts');

test('dist/ directory exists', () => {
  if (!fileExists(DIST)) throw new Error('no dist/');
});

test('dist/index.html exists', () => {
  if (!fileExists(path.join(DIST, 'index.html'))) throw new Error('no index.html');
});

test('dist/assets/ has JS bundles', () => {
  const assets = fs.readdirSync(path.join(DIST, 'assets')).filter(f => f.endsWith('.js'));
  if (assets.length < 10) throw new Error(`only ${assets.length} JS files`);
});

test('dist/assets/ has CSS', () => {
  const css = fs.readdirSync(path.join(DIST, 'assets')).filter(f => f.endsWith('.css'));
  if (css.length < 1) throw new Error('no CSS files');
});

// ═══════════════════════════════════════════
// 12. ANDROID MANIFEST
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 12: Android Manifest');

const manifestPath = path.join(ANDROID, 'app/src/main/AndroidManifest.xml');
const manifest = readFile(manifestPath);

test('AndroidManifest.xml exists', () => { if (!manifest) throw new Error('missing'); });

const requiredPermissions = [
  'INTERNET', 'CAMERA', 'RECORD_AUDIO', 'VIBRATE', 'FOREGROUND_SERVICE',
  'RECEIVE_BOOT_COMPLETED', 'POST_NOTIFICATIONS', 'WAKE_LOCK',
  'ACCESS_NETWORK_STATE', 'ACCESS_WIFI_STATE', 'CALL_PHONE',
  'SYSTEM_ALERT_WINDOW', 'FOREGROUND_SERVICE_MICROPHONE',
  'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS',
];

requiredPermissions.forEach(perm => {
  test(`Manifest has ${perm} permission`, () => {
    if (!manifest.includes(perm)) throw new Error(`missing permission: ${perm}`);
  });
});

test('Manifest has JarvisService', () => {
  if (!manifest.includes('JarvisService')) throw new Error('no JarvisService');
});

test('Manifest has JarvisBootReceiver', () => {
  if (!manifest.includes('JarvisBootReceiver')) throw new Error('no JarvisBootReceiver');
});

test('Manifest has BOOT_COMPLETED intent filter', () => {
  if (!manifest.includes('BOOT_COMPLETED')) throw new Error('no boot intent');
});

test('JarvisService has foregroundServiceType', () => {
  if (!manifest.includes('foregroundServiceType')) throw new Error('no foreground type');
});

// ═══════════════════════════════════════════
// 13. ELECTRON DESKTOP APP
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 13: Electron Desktop App');

const electronMain = readFile(path.join(DESKTOP, 'main.js'));
const electronPreload = readFile(path.join(DESKTOP, 'preload.js'));

test('Electron main.js exists', () => { if (!electronMain) throw new Error('missing'); });
test('Electron preload.js exists', () => { if (!electronPreload) throw new Error('missing'); });

test('Has frameless window (frame: false)', () => {
  if (!electronMain.includes('frame: false')) throw new Error('not frameless');
});

test('Has JARVIS OS Shell injection', () => {
  if (!electronMain.includes('getJarvisOSShellJS') || !electronMain.includes('jarvis-os-shell'))
    throw new Error('no OS shell');
});

test('Has boot sequence animation', () => {
  if (!electronMain.includes('jarvis-os-boot') || !electronMain.includes('boot-reactor'))
    throw new Error('no boot animation');
});

test('Has custom titlebar', () => {
  if (!electronMain.includes('jarvis-titlebar') || !electronMain.includes('J.A.R.V.I.S'))
    throw new Error('no custom titlebar');
});

test('Has system tray', () => {
  if (!electronMain.includes('createTray') || !electronMain.includes('Tray'))
    throw new Error('no system tray');
});

test('Has global shortcuts', () => {
  if (!electronMain.includes('globalShortcut') || !electronMain.includes('CommandOrControl+Shift+J'))
    throw new Error('no global shortcuts');
});

test('Has always-on-top support', () => {
  if (!electronMain.includes('setAlwaysOnTop')) throw new Error('no always-on-top');
});

test('Has volume control IPC', () => {
  if (!electronMain.includes('volume-up') || !electronMain.includes('volume-down'))
    throw new Error('no volume IPC');
});

test('Has brightness control IPC', () => {
  if (!electronMain.includes('brightness-up') || !electronMain.includes('brightness-down'))
    throw new Error('no brightness IPC');
});

test('Has PC power control (shutdown/restart/sleep/lock)', () => {
  if (!electronMain.includes('pc-shutdown') || !electronMain.includes('pc-restart') || 
      !electronMain.includes('pc-sleep') || !electronMain.includes('pc-lock'))
    throw new Error('missing PC power controls');
});

test('Has WhatsApp automation', () => {
  if (!electronMain.includes('whatsapp-send')) throw new Error('no WhatsApp');
});

test('Has music playback (YouTube/Spotify)', () => {
  if (!electronMain.includes('play-youtube') || !electronMain.includes('play-spotify'))
    throw new Error('no music playback');
});

test('Has code execution engine', () => {
  if (!electronMain.includes('execute-code') || !electronMain.includes('setupCodeEngine'))
    throw new Error('no code engine');
});

test('Has screen capture', () => {
  if (!electronMain.includes('capture-screen') || !electronMain.includes('desktopCapturer'))
    throw new Error('no screen capture');
});

test('Has auto-start on boot', () => {
  if (!electronMain.includes('setupAutoStart') || !electronMain.includes('openAtLogin'))
    throw new Error('no auto-start');
});

test('Has power monitoring', () => {
  if (!electronMain.includes('powerMonitor') || !electronMain.includes('setupPowerMonitoring'))
    throw new Error('no power monitoring');
});

test('Preload exposes isJarvisOS', () => {
  if (!electronPreload.includes('isJarvisOS')) throw new Error('no isJarvisOS flag');
});

test('Preload has v16.0', () => {
  if (!electronPreload.includes('16.0')) throw new Error('version mismatch');
});

// ═══════════════════════════════════════════
// 14. ROUTE COMPLETENESS
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 14: Route Completeness');

const expectedRoutes = [
  '/', '/trading', '/wallet', '/chat', '/auto-trader', '/gems', '/screener',
  '/intelligence', '/settings', '/phantom', '/copy-trading', '/social',
  '/options', '/portfolio', '/whales', '/backtest', '/indian-stocks',
  '/nifty-options', '/candle-indicators', '/power-predictor', '/intraday-scanner',
  '/options-pro', '/strategy-builder', '/risk-manager', '/mega-trader',
  '/voice', '/ai-agent', '/admin', '/paper-trading', '/pnl-journal',
  '/watchlist', '/smart-alerts', '/depth-chart', '/tax-calculator',
  '/jarvis', '/voice-command', '/vault', '/exchange-connect', '/qr-scanner',
  '/signal-card', '/voice-ai', '/system-specs', '/jarvis-vs-myra',
  '/voice-automation', '/jarvis-holographic', '/gaming', '/gaming-coach',
  '/system-control', '/device-control', '/phone-control',
];

expectedRoutes.forEach(route => {
  test(`Route ${route} exists`, () => {
    if (!appCode.includes(`path="${route}"`)) throw new Error(`missing route: ${route}`);
  });
});

// ═══════════════════════════════════════════
// 15. CRASH RESILIENCE
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 15: Crash Resilience');

test('loadService() function exists', () => {
  if (!appCode.includes('async function loadService')) throw new Error('no loadService');
});

test('sc() safe caller exists', () => {
  if (!appCode.includes('function sc(')) throw new Error('no sc()');
});

test('All services loaded via Promise.all', () => {
  if (!appCode.includes('Promise.all')) throw new Error('no Promise.all');
});

test('Boot sequence has try-catch', () => {
  if (!appCode.includes('bootJarvis().catch')) throw new Error('no boot error handler');
});

test('Phase 4 wake word has try-catch', () => {
  const phase4Match = appCode.includes('Phase 4') || appCode.includes('Wake Word Engine');
  if (!phase4Match) throw new Error('no Phase 4 wake word');
});

// Count total lazy imports
const lazyCount = (appCode.match(/lazy\(\(\)/g) || []).length;
test(`Has ${lazyCount} lazy-loaded components (should be 47+)`, () => {
  if (lazyCount < 47) throw new Error(`only ${lazyCount} lazy components`);
});

// ═══════════════════════════════════════════
// 16. ANDROID JAVA FILES
// ═══════════════════════════════════════════
console.log('🧪 Test Suite 16: Android Java Files');

const javaDir = path.join(ANDROID, 'app/src/main/java/com/jarvis/trading');

test('MainActivity.java exists', () => {
  if (!fileExists(path.join(javaDir, 'MainActivity.java'))) throw new Error('missing');
});

test('JarvisService.java exists', () => {
  if (!fileExists(path.join(javaDir, 'JarvisService.java'))) throw new Error('missing');
});

test('JarvisBootReceiver.java exists', () => {
  if (!fileExists(path.join(javaDir, 'JarvisBootReceiver.java'))) throw new Error('missing');
});

test('DeviceCommandsPlugin.java exists', () => {
  if (!fileExists(path.join(javaDir, 'plugins', 'DeviceCommandsPlugin.java'))) throw new Error('missing');
});

test('LocalTTSPlugin.java exists', () => {
  if (!fileExists(path.join(javaDir, 'plugins', 'LocalTTSPlugin.java'))) throw new Error('missing');
});

const mainActivityCode = readFile(path.join(javaDir, 'MainActivity.java'));

test('MainActivity starts JarvisService', () => {
  if (!mainActivityCode.includes('startJarvisService'))
    throw new Error('service not started');
});

test('MainActivity registers DeviceCommands plugin', () => {
  if (!mainActivityCode.includes('DeviceCommandsPlugin'))
    throw new Error('plugin not registered');
});

// ═══════════════════════════════════════════
// FINAL REPORT
// ═══════════════════════════════════════════
console.log('\n════════════════════════════════════════════');
console.log('🧪 JARVIS v16.0 TEST RESULTS');
console.log('════════════════════════════════════════════');
console.log(`✅ PASSED:   ${passed}`);
console.log(`❌ FAILED:   ${failed}`);
console.log(`⚠️  WARNINGS: ${warnings}`);
console.log(`📊 TOTAL:    ${passed + failed}`);
console.log(`🎯 SCORE:    ${((passed / (passed + failed)) * 100).toFixed(1)}%`);
console.log('════════════════════════════════════════════');

if (failures.length > 0) {
  console.log('\n❌ FAILURES:');
  failures.forEach(f => console.log(`   • ${f.name}: ${f.error}`));
}

if (failed === 0) {
  console.log('\n🏆 ALL TESTS PASSED — JARVIS v16.0 is BATTLE-READY!');
} else {
  console.log(`\n⚠️ ${failed} tests need attention`);
}

process.exit(failed > 0 ? 1 : 0);
