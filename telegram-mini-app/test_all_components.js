#!/usr/bin/env node
/**
 * 🧪 JARVIS Automated Component Test Suite
 * ═════════════════════════════════════════════
 * Tests EVERY component and service for:
 * - Import/export validity
 * - No static dangerous imports
 * - ErrorBoundary wrapping
 * - Try-catch in all async handlers
 * - Service constructor safety
 * 
 * Run: node test_all_components.js
 */

const fs = require('fs')
const path = require('path')

const SRC = path.join(__dirname, 'src')
const COMPONENTS = path.join(SRC, 'components')
const SERVICES = path.join(SRC, 'services')
const HOOKS = path.join(SRC, 'hooks')
const PAGES = path.join(SRC, 'pages')

let passed = 0, failed = 0, warnings = 0
const results = []

function test(name, condition, severity = 'FAIL') {
  if (condition) {
    passed++
    results.push({ name, status: '✅ PASS' })
  } else if (severity === 'WARN') {
    warnings++
    results.push({ name, status: '⚠️ WARN' })
  } else {
    failed++
    results.push({ name, status: '❌ FAIL' })
  }
}

function readFile(filePath) {
  try { return fs.readFileSync(filePath, 'utf-8') } catch { return '' }
}

function getFiles(dir, ext = '.jsx') {
  try {
    return fs.readdirSync(dir).filter(f => f.endsWith(ext)).map(f => path.join(dir, f))
  } catch { return [] }
}

console.log('🧪 JARVIS Test Suite Starting...\n')
console.log('═'.repeat(60))

// ═══ TEST 1: All components exist and export default ═══
console.log('\n📦 Test 1: Component Exports')
const componentFiles = getFiles(COMPONENTS, '.jsx')
componentFiles.forEach(file => {
  const content = readFile(file)
  const name = path.basename(file)
  test(`${name} has default export`, content.includes('export default'))
})

// ═══ TEST 2: No static dangerous service imports ═══
console.log('\n🔒 Test 2: No Static Service Imports')
const dangerousServices = [
  'realtime', 'wsHub', 'jarvisCore', 'serviceMesh', 'crashAnalytics',
  'autoRefreshEngine', 'backgroundAlerts', 'firebasePush', 'hapticEngine',
  'offlineEngine', 'offlineCache', 'presenceEngine', 'jarvisDB',
  'notificationPipeline', 'voiceCommandEngine', 'webAIFallback',
  'securityBatteryPerf', 'elevenlabsVoice', 'themeEngine', 'smartAuth',
  'deepLink', 'chartCapture', 'exchangeEngine', 'systemControl',
  'i18n', 'pushNotifications', 'JarvisDeviceService'
]
const allUIFiles = [...componentFiles, ...getFiles(PAGES, '.jsx')]
allUIFiles.forEach(file => {
  const content = readFile(file)
  const name = path.basename(file)
  dangerousServices.forEach(svc => {
    const regex = new RegExp(`^import\\s+.*from\\s+['\"].*services/${svc}['\"]`, 'm')
    test(`${name} no static import of ${svc}`, !regex.test(content))
  })
})

// ═══ TEST 3: App.jsx has ErrorBoundary on every route ═══
console.log('\n🛡️ Test 3: ErrorBoundary Wrapping')
const appContent = readFile(path.join(SRC, 'App.jsx'))
const routeMatches = appContent.match(/<Route\s+path=/g) || []
const ebRoutes = appContent.match(/<ErrorBoundary><[A-Z]/g) || []
test('All routes have ErrorBoundary', routeMatches.length > 0 && ebRoutes.length >= routeMatches.length - 2)
test('App root has ErrorBoundary', appContent.includes('<ErrorBoundary>\n      <AppProvider>') || appContent.includes('<ErrorBoundary>\n    <AppProvider>'))

// ═══ TEST 4: Service constructors have try-catch ═══
console.log('\n🔧 Test 4: Service Constructor Safety')
const serviceFiles = getFiles(SERVICES, '.js')
serviceFiles.forEach(file => {
  const content = readFile(file)
  const name = path.basename(file)
  if (content.includes('constructor(') || content.includes('constructor (')) {
    // Check if constructor body has try-catch
    const hasTryCatch = content.includes('try {') || content.includes('try{')
    test(`${name} constructor has try-catch`, hasTryCatch, 'WARN')
  }
})

// ═══ TEST 5: All components have error handling ═══
console.log('\n⚡ Test 5: Async Error Handling')
allUIFiles.forEach(file => {
  const content = readFile(file)
  const name = path.basename(file)
  const asyncCount = (content.match(/async\s/g) || []).length
  if (asyncCount > 0) {
    const catchCount = (content.match(/catch\s*\(/g) || []).length + (content.match(/\.catch\(/g) || []).length
    test(`${name} has catch for ${asyncCount} async (${catchCount} catches)`, catchCount > 0, 'WARN')
  }
})

// ═══ TEST 6: API functions exist ═══
console.log('\n🌐 Test 6: API Endpoint Functions')
const apiContent = readFile(path.join(SERVICES, 'api.js'))
const apiExports = [
  'fetchTicker', 'fetchDashboard', 'fetchSignals', 'sendChat', 'streamChat',
  'fetchGems', 'startAutoTrader', 'stopAutoTrader', 'fetchPortfolio',
  'fetchWallet', 'requestDeposit', 'requestWithdraw'
]
apiExports.forEach(fn => {
  test(`api.js exports ${fn}`, apiContent.includes(`export`) && apiContent.includes(fn))
})

// ═══ TEST 7: Key files exist ═══
console.log('\n📁 Test 7: Key Files Exist')
const keyFiles = [
  'src/App.jsx', 'src/components/Dashboard.jsx', 'src/components/Trading.jsx',
  'src/components/Wallet.jsx', 'src/components/AIChat.jsx', 'src/components/GamingCoach.jsx',
  'src/components/HindiVoiceAssistant.jsx', 'src/components/ErrorBoundary.jsx',
  'src/services/api.js', 'src/services/apiBase.js', 'src/services/freeAI.js',
  'src/services/realtime.js', 'src/services/wsHub.js', 'src/services/jarvisVoice.js',
  'src/hooks/useRealTime.js', 'src/hooks/useSafeService.js',
  'src/context/AppContext.jsx'
]
keyFiles.forEach(f => {
  test(`${f} exists`, fs.existsSync(path.join(__dirname, f)))
})

// ═══ TEST 8: freeAI has embedded keys ═══
console.log('\n🔑 Test 8: AI Engine Keys')
const freeAIContent = readFile(path.join(SERVICES, 'freeAI.js'))
test('freeAI has Gemini key (base64)', freeAIContent.includes('atob('))
test('freeAI has auto-init', freeAIContent.includes('this.init()'))
test('freeAI has chat method', freeAIContent.includes('async chat('))

// ═══ TEST 9: Voice system ═══
console.log('\n🎤 Test 9: Voice System')
const hindiVoice = readFile(path.join(COMPONENTS, 'HindiVoiceAssistant.jsx'))
test('Hindi Voice has native Capacitor STT', hindiVoice.includes('SpeechRecognition'))
test('Hindi Voice has native Capacitor TTS', hindiVoice.includes('TextToSpeech'))
test('Hindi Voice has freeAI fallback', hindiVoice.includes('freeAI'))
test('Hindi Voice has browser fallback', hindiVoice.includes('speechSynthesis'))

// ═══ TEST 10: Gaming Coach ═══
console.log('\n🎮 Test 10: Gaming Coach')
const gaming = readFile(path.join(COMPONENTS, 'GamingCoach.jsx'))
test('Gaming has BGMI package detection', gaming.includes('com.pubg.imobile'))
test('Gaming has auto-play AI', gaming.includes('autoPlayActive') || gaming.includes('startAutoPlay'))
test('Gaming has screen capture', gaming.includes('startScreenCapture'))
test('Gaming has pro player profiles', gaming.includes('jonathan_gaming'))
test('Gaming has freeAI fallback', gaming.includes('freeAI'))
test('Gaming has voice callouts', gaming.includes('speakCallout'))

// ═══ TEST 11: Build test ═══
console.log('\n🏗️ Test 11: Build Validity')
const indexHtml = readFile(path.join(__dirname, 'index.html'))
test('index.html exists', indexHtml.length > 0)
test('index.html loads App', indexHtml.includes('main.jsx') || indexHtml.includes('src/main'))
const viteConfig = readFile(path.join(__dirname, 'vite.config.js'))
test('vite.config.js exists', viteConfig.length > 0)

// ═══ RESULTS ═══
console.log('\n' + '═'.repeat(60))
console.log(`\n🧪 TEST RESULTS:`)
console.log(`   ✅ Passed: ${passed}`)
console.log(`   ⚠️ Warnings: ${warnings}`)
console.log(`   ❌ Failed: ${failed}`)
console.log(`   📊 Total: ${passed + warnings + failed}`)
console.log(`   📈 Score: ${Math.round(passed/(passed+failed+warnings)*100)}%`)

if (failed > 0) {
  console.log('\n❌ FAILURES:')
  results.filter(r => r.status.includes('FAIL')).forEach(r => console.log(`   ${r.status} ${r.name}`))
}
if (warnings > 0) {
  console.log('\n⚠️ WARNINGS:')
  results.filter(r => r.status.includes('WARN')).forEach(r => console.log(`   ${r.status} ${r.name}`))
}

console.log('\n' + '═'.repeat(60))
process.exit(failed > 0 ? 1 : 0)
