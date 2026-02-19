#!/bin/bash
# ══════════════════════════════════════════════
#  🚀 JARVIS Complete Startup Script
#  Starts: FastAPI Server + Telegram Bot
# ══════════════════════════════════════════════

cd /workspaces/codespaces-blank

# Load environment
set -a
source .env 2>/dev/null
set +a

# Auto-detect codespace URL
if [ -n "$CODESPACE_NAME" ]; then
    DOMAIN="${CODESPACE_NAME}-8000.app.github.dev"
    export MINI_APP_URL="https://${DOMAIN}"
    export WEBAPP_URL="https://${DOMAIN}/miniapp"
    echo "🌐 Codespace URL: https://${DOMAIN}"
fi

echo "══════════════════════════════════════════════"
echo "  🤖 JARVIS AI Trading Platform"
echo "══════════════════════════════════════════════"
echo "  📱 Mini App:  ${MINI_APP_URL}/miniapp"
echo "  🔌 API:       ${MINI_APP_URL}/api/miniapp/health"
echo "  🤖 Bot:       @David_crew_bot"
echo "══════════════════════════════════════════════"

# Kill existing processes
echo "🔄 Cleaning up old processes..."
pkill -f "uvicorn server:app" 2>/dev/null
pkill -f "telegram_mini_app_bot" 2>/dev/null
sleep 2

# Make port public
if [ -n "$CODESPACE_NAME" ]; then
    echo "🔓 Setting port 8000 to public..."
    gh codespace ports visibility 8000:public -c "$CODESPACE_NAME" 2>/dev/null &
fi

# Start FastAPI Server
echo "🚀 Starting FastAPI server on port 8000..."
python -m uvicorn server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

# Wait for server to be ready
echo "⏳ Waiting for server..."
for i in {1..15}; do
    if curl -s -o /dev/null http://localhost:8000/api/miniapp/health 2>/dev/null; then
        echo "   ✅ Server ready!"
        break
    fi
    sleep 1
done

# Start Telegram Bot
echo "🤖 Starting Telegram bot..."
python telegram_mini_app_bot.py &
BOT_PID=$!
echo "   Bot PID: $BOT_PID"
sleep 2

# Set bot menu button
echo "📱 Setting bot menu button..."
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setChatMenuButton" \
    -H "Content-Type: application/json" \
    -d "{\"menu_button\":{\"type\":\"web_app\",\"text\":\"🚀 JARVIS\",\"web_app\":{\"url\":\"${MINI_APP_URL}/miniapp\"}}}" > /dev/null 2>&1

echo ""
echo "══════════════════════════════════════════════"
echo "  ✅ JARVIS is LIVE!"
echo "══════════════════════════════════════════════"
echo "  🌐 Open: ${MINI_APP_URL}/miniapp"
echo "  🤖 Bot:  https://t.me/David_crew_bot"
echo "  📊 API:  ${MINI_APP_URL}/api/miniapp/health"
echo "  🔑 Admin: ${MINI_APP_URL}/admin"
echo "══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for processes
wait
