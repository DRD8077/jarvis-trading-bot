#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🚀 JARVIS — Start All Services
#  Starts: FastAPI Server (Admin + Mini App) + Telegram Bot
# ═══════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load env
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}✅ Loaded .env${NC}"
fi

# Build public URL
if [ -n "$CODESPACE_NAME" ] && [ -n "$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" ]; then
    PUBLIC_URL="https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
    echo -e "${BLUE}🌐 Public URL: ${PUBLIC_URL}${NC}"
    echo -e "${BLUE}🌐 Mini App:   ${PUBLIC_URL}/miniapp${NC}"
    echo -e "${BLUE}🌐 Admin:      ${PUBLIC_URL}/${NC}"
    
    # Auto-update MINI_APP_URL if it's stale
    export MINI_APP_URL="${PUBLIC_URL}/miniapp"
    export WEBHOOK_URL="${PUBLIC_URL}"
    export WEBAPP_URL="${PUBLIC_URL}/miniapp"
    
    # Make port public 
    echo -e "${YELLOW}🔓 Making port 8080 public...${NC}"
    gh codespace ports visibility 8080:public -c "$CODESPACE_NAME" 2>/dev/null || true
fi

# Kill any existing processes
echo -e "${YELLOW}🔄 Stopping old processes...${NC}"
pkill -f "uvicorn jarvis_admin" 2>/dev/null || true
pkill -f "node.*bot.js" 2>/dev/null || true
sleep 1

# ═══ Start FastAPI Server ═══
echo -e "${BLUE}🚀 Starting FastAPI server on port 8080...${NC}"
cd "$SCRIPT_DIR"
python -m uvicorn jarvis_admin:app --host 0.0.0.0 --port 8080 --log-level info &
FASTAPI_PID=$!
echo -e "${GREEN}✅ FastAPI PID: ${FASTAPI_PID}${NC}"

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for server...${NC}"
for i in {1..15}; do
    if curl -s http://localhost:8080/api/miniapp/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ FastAPI server is ready!${NC}"
        break
    fi
    sleep 1
done

# ═══ Start Node.js Bot ═══
echo -e "${BLUE}🤖 Starting Telegram Bot...${NC}"
cd "$SCRIPT_DIR/telegram-ai-app"

# Export vars for the Node bot
export BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
export WEBAPP_URL="${MINI_APP_URL}"

node bot/bot.js &
BOT_PID=$!
echo -e "${GREEN}✅ Bot PID: ${BOT_PID}${NC}"

sleep 2

# ═══ Summary ═══
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 JARVIS ALL SYSTEMS ONLINE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "  🌐 Admin Panel: ${PUBLIC_URL:-http://localhost:8080}/"
echo -e "  📱 Mini App:    ${PUBLIC_URL:-http://localhost:8080}/miniapp"
echo -e "  🔌 API Health:  ${PUBLIC_URL:-http://localhost:8080}/api/miniapp/health"
echo -e "  🤖 Bot:         @David_crew_bot"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for any process to exit
wait -n $FASTAPI_PID $BOT_PID 2>/dev/null

# Cleanup
echo -e "${RED}🛑 Shutting down...${NC}"
kill $FASTAPI_PID $BOT_PID 2>/dev/null
wait 2>/dev/null
