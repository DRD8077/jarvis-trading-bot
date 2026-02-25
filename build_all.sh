#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  🚀 JARVIS AI — MASTER BUILD SCRIPT v10.0
#  ═══════════════════════════════════════════════════════════════════════════════
#  Build EVERYTHING: Windows EXE + Android APK + Linux AppImage
#
#  Usage:
#    ./build_all.sh              — Build EXE + APK (both)
#    ./build_all.sh --exe        — Build Windows EXE only
#    ./build_all.sh --apk        — Build Android APK only
#    ./build_all.sh --linux      — Build Linux AppImage only
#    ./build_all.sh --portable   — Create portable ZIP (no build tools needed)
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VERSION=$(python3 -c "import json; print(json.load(open('version.json'))['version'])" 2>/dev/null || echo "10.0.0")

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                         ║"
echo "║        ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗     █████╗ ██╗           ║"
echo "║        ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██╔══██╗██║           ║"
echo "║        ██║███████║██████╔╝██║   ██║██║███████╗    ███████║██║           ║"
echo "║   ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██╔══██║██║           ║"
echo "║   ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ██║  ██║██║           ║"
echo "║    ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝           ║"
echo "║                                                                         ║"
echo "║              🤖 Master Build System v10.0                               ║"
echo "║              Build EXE + APK — Full Laptop & Phone Control              ║"
echo "║              Version: $VERSION                                             ║"
echo "║                                                                         ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

TARGET="${1:---all}"
mkdir -p dist

# ═══════════════════════════════════
# PORTABLE ZIP (always create this)
# ═══════════════════════════════════
create_portable() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📦 Creating Portable ZIP Package..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    PORTABLE_DIR="dist/JARVIS-AI-v${VERSION}-portable"
    rm -rf "$PORTABLE_DIR"
    mkdir -p "$PORTABLE_DIR"
    
    echo "  📋 Copying project files..."
    
    # Copy all Python files
    cp *.py "$PORTABLE_DIR/" 2>/dev/null || true
    
    # Copy shell scripts & batch files
    cp *.sh "$PORTABLE_DIR/" 2>/dev/null || true
    cp *.bat "$PORTABLE_DIR/" 2>/dev/null || true
    
    # Copy configs
    cp requirements.txt "$PORTABLE_DIR/"
    cp version.json "$PORTABLE_DIR/" 2>/dev/null || true
    cp pyproject.toml "$PORTABLE_DIR/" 2>/dev/null || true
    [ -f ".env.example" ] && cp .env.example "$PORTABLE_DIR/"
    [ -f ".env" ] && echo "  ⚠️ Skipping .env (contains secrets)"
    
    # Copy JSON configs (without sensitive data)
    for f in jarvis_features.json jarvis_airdrops.json; do
        [ -f "$f" ] && cp "$f" "$PORTABLE_DIR/"
    done
    
    # Copy desktop app
    mkdir -p "$PORTABLE_DIR/desktop-app"
    cp desktop-app/main.js "$PORTABLE_DIR/desktop-app/" 2>/dev/null || true
    cp desktop-app/preload.js "$PORTABLE_DIR/desktop-app/" 2>/dev/null || true
    cp desktop-app/backendManager.js "$PORTABLE_DIR/desktop-app/" 2>/dev/null || true
    cp desktop-app/package.json "$PORTABLE_DIR/desktop-app/" 2>/dev/null || true
    [ -d "desktop-app/assets" ] && cp -r desktop-app/assets "$PORTABLE_DIR/desktop-app/"
    
    # Copy frontend source
    if [ -d "telegram-mini-app/src" ]; then
        mkdir -p "$PORTABLE_DIR/telegram-mini-app"
        cp -r telegram-mini-app/src "$PORTABLE_DIR/telegram-mini-app/"
        cp telegram-mini-app/package.json "$PORTABLE_DIR/telegram-mini-app/" 2>/dev/null || true
        cp telegram-mini-app/vite.config.* "$PORTABLE_DIR/telegram-mini-app/" 2>/dev/null || true
        cp telegram-mini-app/index.html "$PORTABLE_DIR/telegram-mini-app/" 2>/dev/null || true
        cp telegram-mini-app/capacitor.config.* "$PORTABLE_DIR/telegram-mini-app/" 2>/dev/null || true
        [ -d "telegram-mini-app/dist" ] && cp -r telegram-mini-app/dist "$PORTABLE_DIR/telegram-mini-app/"
    fi
    
    # Copy templates & static
    [ -d "templates" ] && cp -r templates "$PORTABLE_DIR/"
    [ -d "static" ] && cp -r static "$PORTABLE_DIR/"
    [ -d "models" ] && cp -r models "$PORTABLE_DIR/"
    [ -d "data" ] && cp -r data "$PORTABLE_DIR/"
    
    # Create README for portable package
    cat > "$PORTABLE_DIR/INSTALL_README.md" << 'READMEEOF'
# 🤖 JARVIS AI — Portable Installation Guide

## Windows Setup (EXE)

### Quick Start:
1. Install [Python 3.11+](https://www.python.org/downloads/) (**check "Add to PATH"**)
2. Install [Node.js 18+](https://nodejs.org/)
3. Double-click `setup_windows.bat` to install dependencies
4. Double-click `start_jarvis_desktop.bat` to run JARVIS!

### Build Windows Installer (EXE):
```bash
bash build_exe_installer.sh --win
```
The installer will be in `desktop-app/release/JARVIS-AI-v10.0.0-Setup.exe`

## Android Setup (APK)

### Quick Install:
1. Transfer any pre-built `.apk` file to your phone
2. On phone: Settings → Security → Allow "Install Unknown Apps"
3. Tap the APK to install
4. Open JARVIS AI — done!

### Build APK from Source:
```bash
bash build_apk_full.sh --debug    # Debug APK
bash build_apk_full.sh --release  # Signed release APK
```

## What JARVIS Can Do

### On Laptop (Windows/Mac/Linux):
- 🗣️ Voice commands (ask anything)
- 📂 Open/close any application
- 🔊 Volume & brightness control
- 💻 Shutdown, restart, sleep, lock PC
- 📸 Take screenshots
- 📝 Execute code (Python, JS, etc.)
- 📁 File management (search, read, write)
- 📋 Clipboard control
- 🌐 Open any website
- 💬 WhatsApp automation
- 🎵 Play music (YouTube, Spotify)
- 📊 Stock/crypto trading signals
- 🧠 AI chat with multiple providers
- ⌨️ Global hotkey: Ctrl+Shift+J

### On Phone (Android):
- 🗣️ Voice commands
- 📷 Camera access
- 📂 File manager
- 📍 Location tracking
- 🔔 Push notifications
- 🔐 Biometric login
- 📞 Make calls, send SMS
- 📊 Trading signals
- 🧠 AI chat
- 🔊 Auto-start on boot
- 📱 Background service

## API Keys

Add your AI provider keys to `.env`:
```env
GROQ_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

At least ONE AI key is needed for chat to work.
READMEEOF

    # Create zip
    cd dist
    zip -r "JARVIS-AI-v${VERSION}-portable.zip" "JARVIS-AI-v${VERSION}-portable" -x "*/node_modules/*" "*/.git/*" "*/__pycache__/*" "*/\.venv/*" 2>/dev/null
    cd "$SCRIPT_DIR"
    
    ZIPSIZE=$(du -sh "dist/JARVIS-AI-v${VERSION}-portable.zip" 2>/dev/null | cut -f1)
    echo "  ✅ Portable ZIP: dist/JARVIS-AI-v${VERSION}-portable.zip ($ZIPSIZE)"
    echo ""
}

# ═══════════════════════════════════
# BUILD TARGETS
# ═══════════════════════════════════
case "$TARGET" in
    --exe|--win)
        echo "  🖥️ Building Windows EXE..."
        bash build_exe_installer.sh --win
        create_portable
        ;;
    --apk|--android)
        echo "  📱 Building Android APK..."
        bash build_apk_full.sh --debug
        ;;
    --linux)
        echo "  🐧 Building Linux AppImage..."
        bash build_exe_installer.sh --linux
        create_portable
        ;;
    --portable)
        create_portable
        ;;
    --all|*)
        echo "  🚀 Building EVERYTHING..."
        echo ""
        
        # Build portable first (always works)
        create_portable
        
        # Build EXE (may need Wine on Linux)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  🖥️ Building Desktop App..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        bash build_exe_installer.sh --linux 2>&1 || echo "  ⚠️ Desktop build had issues (non-fatal)"
        
        # Build APK
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  📱 Building Android APK..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        bash build_apk_full.sh --debug 2>&1 || echo "  ⚠️ APK build had issues (non-fatal)"
        ;;
esac

# ═══════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    🎉 JARVIS AI — Build Complete!                       ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                         ║"
echo "║  📁 All artifacts in: dist/                                             ║"
echo "║                                                                         ║"

# List all artifacts
if [ -d "dist" ]; then
    for f in dist/JARVIS-AI-*; do
        if [ -f "$f" ]; then
            SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
            NAME=$(basename "$f")
            printf "║  %-60s %10s ║\n" "  $NAME" "$SIZE"
        fi
    done
    
    # Check desktop-app/release too
    if [ -d "desktop-app/release" ]; then
        for f in desktop-app/release/JARVIS*; do
            if [ -f "$f" ]; then
                SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
                NAME=$(basename "$f")
                printf "║  %-60s %10s ║\n" "  $NAME" "$SIZE"
            fi
        done
    fi
fi

echo "║                                                                         ║"
echo "║  📋 Installation:                                                       ║"
echo "║    Windows: Run setup_windows.bat → start_jarvis_desktop.bat            ║"
echo "║    Android: Transfer APK to phone → Install → Open JARVIS AI           ║"
echo "║    Linux:   chmod +x *.AppImage → ./JARVIS*.AppImage                    ║"
echo "║    Portable: Unzip → setup → start                                     ║"
echo "║                                                                         ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
