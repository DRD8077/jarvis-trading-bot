#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  🖥️ JARVIS AI — Windows EXE Installer Builder v10.0
#  ═══════════════════════════════════════════════════════════════════════════════
#  Builds a complete Windows EXE installer that includes:
#    ✅ Electron desktop app (full laptop control)
#    ✅ Python backend (bundled via PyInstaller)
#    ✅ React frontend (pre-built)
#    ✅ All AI engines, trading modules, desktop control
#    ✅ NSIS installer with desktop shortcut
#    ✅ System tray, hotkeys, auto-start
#
#  Usage: ./build_exe_installer.sh [--win|--linux|--all]
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║     🖥️  JARVIS AI — Desktop EXE/Installer Builder v10.0            ║"
echo "║     Complete Laptop Control + AI Trading + Voice Assistant           ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TARGET="${1:---win}"
VERSION=$(python3 -c "import json; print(json.load(open('version.json'))['version'])" 2>/dev/null || echo "10.0.0")
BUILD_NUM=$(python3 -c "import json; print(json.load(open('version.json'))['build'])" 2>/dev/null || echo "1")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "  📌 Version: $VERSION (Build #$BUILD_NUM)"
echo "  🎯 Target:  $TARGET"
echo "  ⏰ Time:    $TIMESTAMP"
echo ""

# ═══════════════════════════════════════════
# STEP 1: Pre-flight Checks
# ═══════════════════════════════════════════
echo "━━━ Step 1/7: Pre-flight Checks ━━━"

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "  ❌ Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
    sudo apt-get install -y nodejs 2>/dev/null
fi
echo "  ✅ Node.js: $(node --version)"

# Check npm
if ! command -v npm &>/dev/null; then
    echo "  ❌ npm not found"
    exit 1
fi
echo "  ✅ npm: $(npm --version)"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  ❌ Python 3 not found"
    exit 1
fi
echo "  ✅ Python: $(python3 --version)"

# Check pip
if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    echo "  ❌ pip not found"
    exit 1
fi
echo "  ✅ pip available"
echo ""

# ═══════════════════════════════════════════
# STEP 2: Bundle Python Backend with PyInstaller
# ═══════════════════════════════════════════
echo "━━━ Step 2/7: Bundle Python Backend ━━━"

# Activate venv if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "  ✅ Virtual environment activated"
fi

# Install PyInstaller
pip install pyinstaller 2>/dev/null || pip3 install pyinstaller 2>/dev/null
echo "  ✅ PyInstaller ready"

# Create a launcher script that PyInstaller will bundle
cat > _jarvis_launcher.py << 'PYEOF'
"""
JARVIS AI Backend Launcher — Bundled for Desktop EXE
Starts the FastAPI server with all AI engines embedded.
"""
import os
import sys
import json
import signal
import logging

# Set up paths for bundled mode
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.environ['PYTHONPATH'] = BASE_DIR
os.environ['APP_MODE'] = 'desktop'
os.environ['PORT'] = os.environ.get('PORT', '8000')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("jarvis-desktop")

def main():
    logger.info("🖥️ JARVIS Desktop Backend starting...")
    logger.info(f"   Base directory: {BASE_DIR}")
    logger.info(f"   Port: {os.environ['PORT']}")
    
    try:
        import uvicorn
        # Try standalone server first (no Telegram dependency)
        try:
            from jarvis_standalone_server import app
            logger.info("   Using standalone server (no Telegram)")
        except ImportError:
            from jarvis_server import app
            logger.info("   Using main server")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=int(os.environ['PORT']),
            log_level="info",
            workers=1,
            timeout_keep_alive=30
        )
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
PYEOF

echo "  ✅ Launcher script created"

# Collect all Python modules to include
PYTHON_MODULES=""
for pyfile in *.py; do
    module=$(basename "$pyfile" .py)
    if [ "$module" != "_jarvis_launcher" ] && [ "$module" != "setup" ]; then
        PYTHON_MODULES="$PYTHON_MODULES --hidden-import=$module"
    fi
done

# Bundle with PyInstaller (creates dist/_jarvis_launcher/)
echo "  📦 Bundling Python backend (this takes a few minutes)..."
pyinstaller \
    --noconfirm \
    --clean \
    --name jarvis_backend \
    --distpath desktop-app/python-backend \
    --workpath build/pyinstaller \
    --specpath build \
    --onedir \
    $PYTHON_MODULES \
    --hidden-import=uvicorn \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols \
    --hidden-import=uvicorn.protocols.http \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=uvicorn.lifespan \
    --hidden-import=uvicorn.lifespan.on \
    --hidden-import=fastapi \
    --hidden-import=starlette \
    --hidden-import=pydantic \
    --hidden-import=httpx \
    --hidden-import=pandas \
    --hidden-import=numpy \
    --hidden-import=sklearn \
    --hidden-import=psutil \
    --hidden-import=jwt \
    --hidden-import=bcrypt \
    --hidden-import=redis \
    --hidden-import=edge_tts \
    --hidden-import=groq \
    --hidden-import=openai \
    --hidden-import=anthropic \
    --collect-all uvicorn \
    --collect-all fastapi \
    --collect-all starlette \
    --collect-all pydantic \
    _jarvis_launcher.py 2>&1 | tail -5

# Copy data files needed by the backend
echo "  📋 Copying data files..."
BACKEND_DIR="desktop-app/python-backend/jarvis_backend"
mkdir -p "$BACKEND_DIR"

# Copy JSON configs
for jsonfile in jarvis_api_keys.json jarvis_features.json jarvis_predictions.json \
                jarvis_memory.json version.json jarvis_airdrops.json; do
    [ -f "$jsonfile" ] && cp "$jsonfile" "$BACKEND_DIR/" 2>/dev/null
done

# Copy templates and static
[ -d "templates" ] && cp -r templates "$BACKEND_DIR/" 2>/dev/null
[ -d "static" ] && cp -r static "$BACKEND_DIR/" 2>/dev/null
[ -d "data" ] && cp -r data "$BACKEND_DIR/" 2>/dev/null
[ -d "models" ] && cp -r models "$BACKEND_DIR/" 2>/dev/null

echo "  ✅ Python backend bundled"
echo ""

# ═══════════════════════════════════════════
# STEP 3: Build React Frontend
# ═══════════════════════════════════════════
echo "━━━ Step 3/7: Build React Frontend ━━━"

FRONTEND_DIR=""
for dir in "telegram-mini-app" "frontend" "jarvis-app"; do
    if [ -d "$dir/src" ] && [ -f "$dir/package.json" ]; then
        FRONTEND_DIR="$dir"
        break
    fi
done

if [ -n "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        echo "  📦 Installing frontend dependencies..."
        npm install 2>&1 | tail -3
    fi
    
    # Inject desktop mode config
    cat > src/desktop-config.js << 'JSEOF'
// Auto-generated desktop configuration
window.JARVIS_DESKTOP = true;
window.JARVIS_VERSION = '10.0.0';
window.JARVIS_MODE = 'desktop';
window.API_BASE = 'http://127.0.0.1:8000';
window.WS_BASE = 'ws://127.0.0.1:8000/ws';
JSEOF
    
    # Build
    echo "  🔨 Building frontend..."
    npm run build 2>&1 | tail -3
    
    cd "$SCRIPT_DIR"
    echo "  ✅ Frontend built: $FRONTEND_DIR/dist"
else
    echo "  ⚠️ No frontend found — using hosted version"
fi
echo ""

# ═══════════════════════════════════════════
# STEP 4: Update Electron App Configuration
# ═══════════════════════════════════════════
echo "━━━ Step 4/7: Configure Electron App ━━━"

cd desktop-app

# Install Electron dependencies
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing Electron dependencies..."
    npm install 2>&1 | tail -3
fi

# Update package.json version
node -e "
const pkg = require('./package.json');
pkg.version = '$VERSION';
pkg.build.extraResources = pkg.build.extraResources || [];

// Add Python backend to resources
const hasBackend = pkg.build.extraResources.some(r => 
    typeof r === 'object' && r.to === 'python-backend'
);
if (!hasBackend) {
    pkg.build.extraResources.push({
        from: 'python-backend/jarvis_backend',
        to: 'python-backend',
        filter: ['**/*']
    });
}

require('fs').writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('  ✅ package.json updated to v$VERSION');
"

cd "$SCRIPT_DIR"
echo ""

# ═══════════════════════════════════════════
# STEP 5: Create Enhanced Electron Main with Backend Auto-Start
# ═══════════════════════════════════════════
echo "━━━ Step 5/7: Enhance Electron Backend Integration ━━━"

# Create a backend manager module for Electron
cat > desktop-app/backendManager.js << 'BMEOF'
/**
 * 🔧 JARVIS Backend Manager — Auto-starts Python server
 * Manages the embedded Python FastAPI backend process.
 */
const { spawn, execSync } = require('child_process')
const path = require('path')
const fs = require('fs')
const os = require('os')
const http = require('http')

let backendProcess = null
let isRunning = false

function getBackendPath() {
    // In packaged app
    const candidates = [
        path.join(process.resourcesPath || '', 'python-backend', 'jarvis_backend'),
        path.join(process.resourcesPath || '', 'python-backend', 'jarvis_backend.exe'),
        path.join(__dirname, 'python-backend', 'jarvis_backend', 'jarvis_backend'),
        path.join(__dirname, 'python-backend', 'jarvis_backend', 'jarvis_backend.exe'),
        path.join(__dirname, '..', 'python-backend', 'jarvis_backend'),
    ]
    
    for (const p of candidates) {
        if (fs.existsSync(p)) return p
    }
    
    // Fallback: run directly with python
    return null
}

function checkServerHealth() {
    return new Promise((resolve) => {
        const req = http.get('http://127.0.0.1:8000/health', { timeout: 2000 }, (res) => {
            resolve(res.statusCode === 200)
        })
        req.on('error', () => resolve(false))
        req.on('timeout', () => { req.destroy(); resolve(false) })
    })
}

async function startBackend() {
    if (isRunning) return true
    
    // Check if server already running
    const alreadyUp = await checkServerHealth()
    if (alreadyUp) {
        console.log('[Backend] Server already running on port 8000')
        isRunning = true
        return true
    }
    
    const backendPath = getBackendPath()
    
    if (backendPath) {
        console.log(`[Backend] Starting bundled backend: ${backendPath}`)
        backendProcess = spawn(backendPath, [], {
            cwd: path.dirname(backendPath),
            env: { ...process.env, PORT: '8000', APP_MODE: 'desktop' },
            stdio: ['pipe', 'pipe', 'pipe'],
            detached: false,
            windowsHide: true,
        })
        
        backendProcess.stdout.on('data', (d) => console.log(`[Backend] ${d.toString().trim()}`))
        backendProcess.stderr.on('data', (d) => console.error(`[Backend] ${d.toString().trim()}`))
        backendProcess.on('exit', (code) => {
            console.log(`[Backend] Process exited with code ${code}`)
            isRunning = false
        })
    } else {
        // Try running with system Python
        console.log('[Backend] No bundled backend, trying system Python...')
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
        const serverScript = path.join(__dirname, '..', 'jarvis_standalone_server.py')
        
        if (fs.existsSync(serverScript)) {
            backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'jarvis_standalone_server:app',
                '--host', '127.0.0.1', '--port', '8000'], {
                cwd: path.join(__dirname, '..'),
                env: { ...process.env, PORT: '8000', APP_MODE: 'desktop' },
                stdio: ['pipe', 'pipe', 'pipe'],
                detached: false,
                windowsHide: true,
            })
            
            backendProcess.stdout.on('data', (d) => console.log(`[Backend] ${d.toString().trim()}`))
            backendProcess.stderr.on('data', (d) => console.error(`[Backend] ${d.toString().trim()}`))
            backendProcess.on('exit', (code) => {
                console.log(`[Backend] Process exited with code ${code}`)
                isRunning = false
            })
        } else {
            console.log('[Backend] No server found — running in frontend-only mode')
            return false
        }
    }
    
    // Wait for server to be ready
    for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 1000))
        const ready = await checkServerHealth()
        if (ready) {
            console.log('[Backend] ✅ Server ready!')
            isRunning = true
            return true
        }
    }
    
    console.log('[Backend] ⚠️ Server did not start in time')
    return false
}

function stopBackend() {
    if (backendProcess) {
        console.log('[Backend] Stopping server...')
        if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t'])
        } else {
            backendProcess.kill('SIGTERM')
        }
        backendProcess = null
        isRunning = false
    }
}

function getStatus() {
    return { running: isRunning, pid: backendProcess?.pid || null }
}

module.exports = { startBackend, stopBackend, getStatus, checkServerHealth }
BMEOF

echo "  ✅ Backend manager created"
echo ""

# ═══════════════════════════════════════════
# STEP 6: Build Electron App
# ═══════════════════════════════════════════
echo "━━━ Step 6/7: Build Electron App ━━━"

cd desktop-app

# Install electron-builder globally if needed
npm list electron-builder 2>/dev/null || npm install electron-builder 2>/dev/null

echo "  🔨 Building Electron app..."

case "$TARGET" in
    --win)
        echo "  📦 Building Windows EXE + NSIS installer..."
        npx electron-builder --win --publish never 2>&1 | tail -10
        ;;
    --linux)
        echo "  📦 Building Linux AppImage + deb..."
        npx electron-builder --linux --publish never 2>&1 | tail -10
        ;;
    --mac)
        echo "  📦 Building Mac DMG..."
        npx electron-builder --mac --publish never 2>&1 | tail -10
        ;;
    --all)
        echo "  📦 Building for all platforms..."
        npx electron-builder --win --linux --publish never 2>&1 | tail -10
        ;;
    *)
        echo "  📦 Building for current platform..."
        npx electron-builder --publish never 2>&1 | tail -10
        ;;
esac

cd "$SCRIPT_DIR"
echo ""

# ═══════════════════════════════════════════
# STEP 7: Final Report
# ═══════════════════════════════════════════
echo "━━━ Step 7/7: Build Report ━━━"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                   🖥️ JARVIS Desktop Build Complete!                ║"
echo "╠═══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                     ║"

# List built artifacts
if [ -d "desktop-app/release" ]; then
    echo "║  📁 Built Artifacts:                                                ║"
    for f in desktop-app/release/*; do
        if [ -f "$f" ]; then
            SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
            NAME=$(basename "$f")
            printf "║    %-55s %8s ║\n" "$NAME" "$SIZE"
        fi
    done
fi

echo "║                                                                     ║"
echo "║  🚀 What JARVIS Desktop Can Do:                                     ║"
echo "║    • Open/close any app (Chrome, VSCode, WhatsApp...)               ║"
echo "║    • Volume & brightness control                                     ║"
echo "║    • Shutdown, restart, sleep, lock PC                              ║"
echo "║    • Execute code (Python, JS, more)                                ║"
echo "║    • File management (read, write, search)                          ║"
echo "║    • Take screenshots                                               ║"
echo "║    • AI chat with multiple providers                                 ║"
echo "║    • Stock & crypto trading signals                                  ║"
echo "║    • Voice commands                                                  ║"
echo "║    • System tray + global hotkeys (Ctrl+Shift+J)                    ║"
echo "║    • WhatsApp automation                                             ║"
echo "║    • YouTube/Spotify music playback                                  ║"
echo "║    • Auto-start on boot                                              ║"
echo "║                                                                     ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📋 Install: Run the JARVIS-AI-v${VERSION}-Setup.exe on your Windows laptop"
echo "  🔑 Hotkey: Ctrl+Shift+J to summon JARVIS anytime"
echo ""
