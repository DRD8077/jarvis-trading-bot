#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🚀 JARVIS AI Trading Platform — Standalone Launcher
#  No Telegram. No Mini App. Pure standalone.
# ═══════════════════════════════════════════════════════════════
set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🚀 JARVIS AI Trading Platform — Standalone Mode        ║"
echo "╚═══════════════════════════════════════════════════════════╝"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ═══ Load environment ═══
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null)
    echo "  ✅ Loaded .env"
fi

# ═══ Set defaults ═══
export PORT="${PORT:-8000}"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
export APP_MODE="standalone"

# ═══ Check Python ═══
if ! command -v python3 &>/dev/null; then
    echo "  ❌ Python 3 not found"
    exit 1
fi

# ═══ Install Python dependencies if needed ═══
if [ ! -d ".venv" ] && [ ! -f ".deps_installed" ]; then
    echo "  📦 Installing Python dependencies..."
    pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt 2>/dev/null
    touch .deps_installed
    echo "  ✅ Dependencies installed"
fi

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "  ✅ Virtual environment activated"
fi

# ═══ Build frontend if needed ═══
FRONTEND_DIR=""
for dir in "frontend" "jarvis-app" "telegram-mini-app"; do
    if [ -d "$dir/src" ] && [ -f "$dir/package.json" ]; then
        FRONTEND_DIR="$dir"
        break
    fi
done

if [ -n "$FRONTEND_DIR" ]; then
    if [ ! -d "$FRONTEND_DIR/dist" ] || [ "$1" = "--rebuild" ]; then
        echo "  📦 Building frontend from $FRONTEND_DIR..."
        cd "$FRONTEND_DIR"
        
        # Install node dependencies
        if [ ! -d "node_modules" ]; then
            npm install 2>/dev/null || echo "  ⚠️ npm install had errors (non-fatal)"
        fi
        
        # Build
        npm run build 2>/dev/null || echo "  ⚠️ Frontend build had errors"
        cd "$SCRIPT_DIR"
        echo "  ✅ Frontend built"
    else
        echo "  ✅ Frontend already built ($FRONTEND_DIR/dist exists)"
    fi
fi

# ═══ Create data directory ═══
mkdir -p data

# ═══ Display startup info ═══
echo ""
echo "  🌐 Server: http://0.0.0.0:${PORT}"
echo "  📱 App:    http://0.0.0.0:${PORT}/app"
echo "  📚 Docs:   http://0.0.0.0:${PORT}/docs"
echo "  ❤️  Health: http://0.0.0.0:${PORT}/health"
echo "  🔌 WS:     ws://0.0.0.0:${PORT}/ws"
echo ""

# ═══ Start JARVIS Standalone Server ═══
echo "  🚀 Starting JARVIS server..."
exec python3 -m uvicorn jarvis_standalone_server:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --log-level info \
    --timeout-keep-alive 30
