#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  🤖 JARVIS COMPLETE SETUP + FOREVER RUN — Termux (Android)      ║
# ║  ONE COMMAND DOES EVERYTHING:                                    ║
# ║    bash jarvis_forever.sh                                        ║
# ║                                                                  ║
# ║  ✅ Auto-installs packages                                       ║
# ║  ✅ Auto-clones repo                                             ║
# ║  ✅ Auto-creates .env with all keys                              ║
# ║  ✅ Auto-installs Python dependencies                            ║
# ║  ✅ Runs bot FOREVER with auto-restart                           ║
# ╚══════════════════════════════════════════════════════════════════╝
#
#  STOP BOT:  touch /tmp/jarvis_stop
#

set -o pipefail

# ═══ CONFIG ═══
DOWNLOAD_URL="https://files.catbox.moe/sikjiv.gz"
PROJECT_DIR="$HOME/jarvis"
BOT_SCRIPT="telegram_bot.py"
LOG_FILE="jarvis_bot.log"
PID_FILE="jarvis_bot.pid"
STOP_FILE="/tmp/jarvis_stop"
MAX_RESTARTS=9999
RESTART_DELAY=5
HEALTH_CHECK_INTERVAL=30

# ═══ COLORS ═══
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🤖 J.A.R.V.I.S. — COMPLETE AUTO-SETUP + FOREVER MODE   ║"
echo "║  Trading Bot + Crypto + AI + Programming Expert           ║"
echo "║  Powered by Claude AI + Groq + OpenAI + Gemini            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Remove old stop signal
rm -f "$STOP_FILE"

# ═══════════════════════════════════════════════════════════
#  STEP 1: AUTO-INSTALL SYSTEM PACKAGES (Termux)
# ═══════════════════════════════════════════════════════════

install_if_missing() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${YELLOW}📦 Installing $1...${NC}"
        if command -v pkg &>/dev/null; then
            pkg install -y "$2" 2>/dev/null
        elif command -v apt &>/dev/null; then
            apt install -y "$2" 2>/dev/null
        fi
    fi
}

echo -e "${CYAN}═══ STEP 1: System Packages ═══${NC}"
install_if_missing "python3" "python"
install_if_missing "pip" "python-pip"
install_if_missing "git" "git"
install_if_missing "curl" "curl"

# Check Python
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo -e "${RED}❌ Python not found! Run manually: pkg install python${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $($PYTHON --version)${NC}"

# ═══════════════════════════════════════════════════════════
#  STEP 2: CLONE/UPDATE REPO
# ═══════════════════════════════════════════════════════════

echo -e "${CYAN}═══ STEP 2: Project Code ═══${NC}"

# If we're already inside the project directory with bot script, skip download
if [ -f "$BOT_SCRIPT" ]; then
    echo -e "${GREEN}✅ Already in project directory${NC}"
elif [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/$BOT_SCRIPT" ]; then
    echo -e "${GREEN}✅ Project exists at $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}📥 Downloading JARVIS project...${NC}"
    mkdir -p "$PROJECT_DIR"
    curl -sL "$DOWNLOAD_URL" -o /tmp/jarvis-dl.tar.gz
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Download failed! Check internet connection.${NC}"
        exit 1
    fi
    tar xzf /tmp/jarvis-dl.tar.gz -C "$PROJECT_DIR"
    rm -f /tmp/jarvis-dl.tar.gz
    cd "$PROJECT_DIR"
    echo -e "${GREEN}✅ Project downloaded to $PROJECT_DIR${NC}"
fi

# ═══════════════════════════════════════════════════════════
#  STEP 3: CREATE .env (YOUR API KEYS)
# ═══════════════════════════════════════════════════════════

echo -e "${CYAN}═══ STEP 3: Environment Setup ═══${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}🔑 .env not found! Creating template...${NC}"
    echo -e "${RED}⚠️ APNE API KEYS DALO — template create ho raha hai${NC}"
    cat > .env << 'ENVEOF'
# ═══ REQUIRED — Yeh dono ZARURI hain ═══
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TEST_CHAT_ID=YOUR_CHAT_ID_HERE
OWNER_CHAT_ID=YOUR_CHAT_ID_HERE
ADMIN_CHAT_ID=YOUR_CHAT_ID_HERE

# ═══ AI PROVIDERS (at least 1 dalo) ═══
ANTHROPIC_API_KEY=
GROQ_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# ═══ CRYPTO (optional) ═══
COINDCX_API_KEY=
OWNER_SOLANA_WALLET=
OWNER_PHANTOM_USERNAME=

# ═══ OTHER ═══
WEBHOOK_URL=http://localhost:8000
WATCHLIST=NIFTY,SENSEX
ENVEOF
    echo -e "${GREEN}✅ .env template created${NC}"
    echo -e "${RED}❗ IMPORTANT: Edit .env with your keys: nano .env${NC}"
    echo -e "${YELLOW}   Then run this script again.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

# Load env vars
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs 2>/dev/null)
echo -e "${GREEN}✅ Environment variables loaded${NC}"

# ═══════════════════════════════════════════════════════════
#  STEP 4: INSTALL PYTHON DEPENDENCIES
# ═══════════════════════════════════════════════════════════

echo -e "${CYAN}═══ STEP 4: Python Dependencies ═══${NC}"

# Check if key packages exist, if not install all
$PYTHON -c "import groq; import anthropic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}📦 Installing Python packages (first time takes 2-5 min)...${NC}"
    $PYTHON -m pip install --upgrade pip 2>/dev/null
    $PYTHON -m pip install -r requirements.txt 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ Some packages failed. Installing core packages individually...${NC}"
        $PYTHON -m pip install requests pandas numpy pytz python-dotenv 2>/dev/null
        $PYTHON -m pip install groq openai anthropic google-generativeai 2>/dev/null
        $PYTHON -m pip install beautifulsoup4 feedparser textblob yfinance 2>/dev/null
        $PYTHON -m pip install scikit-learn edge-tts Pillow qrcode 2>/dev/null
        $PYTHON -m pip install schedule joblib scipy nltk 2>/dev/null
    fi
    echo -e "${GREEN}✅ All Python packages installed${NC}"
else
    echo -e "${GREEN}✅ Python packages already installed${NC}"
fi

# ═══════════════════════════════════════════════════════════
#  STEP 5: VERIFY EVERYTHING
# ═══════════════════════════════════════════════════════════

echo -e "${CYAN}═══ STEP 5: Final Verification ═══${NC}"

# Check bot script exists
if [ ! -f "$BOT_SCRIPT" ]; then
    echo -e "${RED}❌ $BOT_SCRIPT not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Bot script: $BOT_SCRIPT${NC}"

# Check critical env vars
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set in .env${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Telegram Token: set${NC}"

# Check AI providers
[ -n "$ANTHROPIC_API_KEY" ] && echo -e "${GREEN}✅ Claude AI: CONNECTED 🧠${NC}" || echo -e "${YELLOW}⚠️ Claude AI: No key (add ANTHROPIC_API_KEY to .env)${NC}"
[ -n "$GROQ_API_KEY" ] && echo -e "${GREEN}✅ Groq AI: CONNECTED${NC}" || echo -e "${YELLOW}⚠️ Groq: No key${NC}"
[ -n "$OPENAI_API_KEY" ] && echo -e "${GREEN}✅ OpenAI: CONNECTED${NC}" || echo -e "${YELLOW}⚠️ OpenAI: No key${NC}"
[ -n "$GEMINI_API_KEY" ] && echo -e "${GREEN}✅ Gemini: CONNECTED${NC}" || echo -e "${YELLOW}⚠️ Gemini: No key${NC}"

# Kill old instance if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Killing old bot (PID: $OLD_PID)${NC}"
        kill "$OLD_PID" 2>/dev/null
        sleep 2
        kill -9 "$OLD_PID" 2>/dev/null
    fi
    rm -f "$PID_FILE"
fi

echo ""
echo -e "${MAGENTA}╔══════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║  🚀 SETUP COMPLETE — STARTING JARVIS 24/7    ║${NC}"
echo -e "${MAGENTA}║  Stop: touch /tmp/jarvis_stop                 ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ═══════════════════════════════════════════════════════════
#  FOREVER LOOP — Bot runs until you stop it
# ═══════════════════════════════════════════════════════════

RESTART_COUNT=0

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    # Check stop signal
    if [ -f "$STOP_FILE" ]; then
        echo -e "${YELLOW}🛑 Stop signal received. JARVIS shutting down...${NC}"
        rm -f "$STOP_FILE" "$PID_FILE"
        exit 0
    fi

    RESTART_COUNT=$((RESTART_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Starting JARVIS (attempt #$RESTART_COUNT) — $TIMESTAMP${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"

    # Start bot in background
    $PYTHON -u "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
    BOT_PID=$!
    echo "$BOT_PID" > "$PID_FILE"
    echo -e "${GREEN}✅ Bot started (PID: $BOT_PID)${NC}"

    # Monitor loop
    while true; do
        sleep $HEALTH_CHECK_INTERVAL

        # Check stop signal
        if [ -f "$STOP_FILE" ]; then
            echo -e "${YELLOW}🛑 Stop signal. Killing bot...${NC}"
            kill "$BOT_PID" 2>/dev/null
            rm -f "$STOP_FILE" "$PID_FILE"
            exit 0
        fi

        # Check if bot is alive
        if ! kill -0 "$BOT_PID" 2>/dev/null; then
            echo -e "${RED}💀 Bot crashed! Restarting in ${RESTART_DELAY}s...${NC}"
            break
        fi

        # Memory check
        if command -v ps &>/dev/null; then
            MEM=$(ps -o rss= -p "$BOT_PID" 2>/dev/null || echo "0")
            MEM_MB=$((${MEM:-0} / 1024))
            if [ "$MEM_MB" -gt 500 ]; then
                echo -e "${YELLOW}⚠️ High memory (${MEM_MB}MB). Restarting...${NC}"
                kill "$BOT_PID" 2>/dev/null
                sleep 2
                break
            fi
        fi
    done

    # Backoff for rapid crashes
    if [ $RESTART_COUNT -gt 5 ]; then
        DELAY=$((RESTART_DELAY + RESTART_COUNT))
        [ $DELAY -gt 60 ] && DELAY=60
    else
        DELAY=$RESTART_DELAY
    fi

    echo -e "${YELLOW}⏳ Waiting ${DELAY}s before restart...${NC}"
    sleep $DELAY

    # Rotate log if >10MB
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$LOG_SIZE" -gt 10485760 ]; then
            tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "$LOG_FILE"
            echo -e "${YELLOW}📄 Log rotated${NC}"
        fi
    fi
done

echo -e "${RED}❌ Max restarts reached. Manual intervention needed.${NC}"
rm -f "$PID_FILE"
exit 1
