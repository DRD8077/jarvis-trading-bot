#!/bin/bash
# ═══════════════════════════════════════
#  🚀 JARVIS Trading Platform — Starter
# ═══════════════════════════════════════
echo "═══════════════════════════════════════"
echo "  🚀 Starting JARVIS Trading Platform  "
echo "═══════════════════════════════════════"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "  📝 Loaded .env file"
fi

# Set domain URLs
DOMAIN="${DOMAIN:-davidcrewai.shop}"
export WEBAPP_URL="${WEBAPP_URL:-https://${DOMAIN}/miniapp}"
export MINI_APP_URL="${MINI_APP_URL:-https://${DOMAIN}/miniapp}"
echo "  🌐 WEBAPP_URL=$WEBAPP_URL"

# Build frontend if needed
if [ ! -d "telegram-mini-app/dist" ]; then
    echo "  📦 Building frontend..."
    cd telegram-mini-app && npm install && npm run build && cd ..
fi

# Start Telegram bot in background
echo "  📱 Starting Telegram bot..."
if [ -d "telegram-ai-app" ]; then
    (cd telegram-ai-app && node bot/bot.js) &
    BOT_PID=$!
    echo "  📱 Bot PID: $BOT_PID"
else
    echo "  ⚠️ telegram-ai-app not found, skipping bot"
    BOT_PID=""
fi

# Start FastAPI server (foreground) — unified jarvis_server.py via uvicorn
echo "  🌐 Starting JARVIS server on port ${PORT:-8000}..."
cd /app
uvicorn jarvis_server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info

# Cleanup
[ -n "$BOT_PID" ] && kill $BOT_PID 2>/dev/null
