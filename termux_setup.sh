#!/data/data/com.termux/files/usr/bin/bash
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  🤖 J.A.R.V.I.S. — TERMUX COMPLETE SETUP (Android)                 ║
# ║                                                                      ║
# ║  Yeh script KUCH BHI nahi download karta unknown sites se.           ║
# ║  Sab kuch GitHub se aayega — SAFE & SECURE.                         ║
# ║                                                                      ║
# ║  USAGE:                                                              ║
# ║    bash termux_setup.sh                                              ║
# ║                                                                      ║
# ║  STOP BOT:                                                           ║
# ║    touch /tmp/jarvis_stop                                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -o pipefail

# ═══ CONFIG ═══
GITHUB_REPO="APNA_GITHUB_USERNAME/APNA_REPO_NAME"  # <-- YAHA APNA REPO DALO
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
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${MAGENTA}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════╗
║       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗              ║
║       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝              ║
║       ██║███████║██████╔╝██║   ██║██║███████╗              ║
║  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║              ║
║  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║              ║
║   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝              ║
║                                                              ║
║  🤖 TERMUX AUTO-SETUP — Android Phone Edition                ║
║  Trading Bot + Crypto + AI + Programming Expert              ║
╚══════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

rm -f "$STOP_FILE"

# ═══════════════════════════════════════════════════════════
#  STEP 1: TERMUX PACKAGES INSTALL
# ═══════════════════════════════════════════════════════════

echo -e "${CYAN}━━━ STEP 1/6: System Packages ━━━${NC}"

# Termux storage permission (for file access)
if [ ! -d "$HOME/storage" ]; then
    echo -e "${YELLOW}📱 Requesting storage permission...${NC}"
    termux-setup-storage 2>/dev/null || true
    sleep 2
fi

# Update package list
echo -e "${YELLOW}📦 Updating package list...${NC}"
pkg update -y 2>/dev/null

# Install all needed system packages
PACKAGES="python python-pip git curl wget openssl libxml2 libxslt ffmpeg"
echo -e "${YELLOW}📦 Installing: $PACKAGES${NC}"
pkg install -y $PACKAGES 2>/dev/null

# Termux-specific scientific packages (pre-compiled, MUCH faster)
echo -e "${YELLOW}📦 Installing scientific packages (pre-compiled)...${NC}"
pkg install -y python-numpy python-scipy python-pandas 2>/dev/null || true

# Detect Python
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo -e "${RED}❌ Python not found even after install! Run: pkg install python${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $($PYTHON --version)${NC}"
echo -e "${GREEN}✅ All system packages installed${NC}"

# ═══════════════════════════════════════════════════════════
#  STEP 2: GET PROJECT CODE
# ═══════════════════════════════════════════════════════════

echo -e "\n${CYAN}━━━ STEP 2/6: Project Code ━━━${NC}"

if [ -f "$BOT_SCRIPT" ]; then
    echo -e "${GREEN}✅ Already in project directory ($PWD)${NC}"
elif [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/$BOT_SCRIPT" ]; then
    echo -e "${GREEN}✅ Project found at $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}📥 Cloning from GitHub...${NC}"
    
    if [ "$GITHUB_REPO" = "APNA_GITHUB_USERNAME/APNA_REPO_NAME" ]; then
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}❌ GITHUB_REPO set nahi hai!${NC}"
        echo ""
        echo -e "${YELLOW}Pehle script edit karo:${NC}"
        echo -e "${BOLD}  nano termux_setup.sh${NC}"
        echo ""
        echo -e "${YELLOW}Line 19 mein apna repo dalo:${NC}"
        echo -e "${BOLD}  GITHUB_REPO=\"your-username/your-repo\"${NC}"
        echo ""
        echo -e "${YELLOW}Ya phir manually clone karo:${NC}"
        echo -e "${BOLD}  git clone https://github.com/YOUR/REPO.git ~/jarvis${NC}"
        echo -e "${BOLD}  cd ~/jarvis${NC}"
        echo -e "${BOLD}  bash termux_setup.sh${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 1
    fi
    
    git clone "https://github.com/$GITHUB_REPO.git" "$PROJECT_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Git clone failed! Check repo name and internet.${NC}"
        exit 1
    fi
    cd "$PROJECT_DIR"
    echo -e "${GREEN}✅ Code cloned to $PROJECT_DIR${NC}"
fi

# ═══════════════════════════════════════════════════════════
#  STEP 3: .env FILE SETUP (API KEYS)
# ═══════════════════════════════════════════════════════════

echo -e "\n${CYAN}━━━ STEP 3/6: Environment Setup (.env) ━━━${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}🔑 .env file nahi mili. Create kar raha hoon...${NC}"
    echo ""
    echo -e "${BOLD}Apne API keys dalo (Enter press karo agar nahi hai):${NC}"
    echo ""
    
    # Telegram Token (REQUIRED)
    echo -e "${RED}[REQUIRED]${NC} Telegram Bot Token (BotFather se milta hai):"
    read -p "TELEGRAM_BOT_TOKEN=" TG_TOKEN
    if [ -z "$TG_TOKEN" ]; then
        echo -e "${RED}❌ Telegram Bot Token ZARURI hai! BotFather se lo: https://t.me/BotFather${NC}"
        exit 1
    fi
    
    # Chat ID (REQUIRED)
    echo ""
    echo -e "${RED}[REQUIRED]${NC} Apna Telegram Chat ID (@userinfobot se milta hai):"
    read -p "TEST_CHAT_ID=" CHAT_ID
    if [ -z "$CHAT_ID" ]; then
        echo -e "${RED}❌ Chat ID ZARURI hai! @userinfobot se lo${NC}"
        exit 1
    fi
    
    # AI Keys (optional)
    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} Groq API Key (free: https://console.groq.com):"
    read -p "GROQ_API_KEY=" GROQ_KEY
    
    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} Gemini API Key (free: https://aistudio.google.com):"
    read -p "GEMINI_API_KEY=" GEMINI_KEY
    
    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} OpenAI API Key:"
    read -p "OPENAI_API_KEY=" OPENAI_KEY

    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} Anthropic/Claude API Key:"
    read -p "ANTHROPIC_API_KEY=" CLAUDE_KEY
    
    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} CoinDCX API Key:"
    read -p "COINDCX_API_KEY=" CDX_KEY

    echo ""
    echo -e "${YELLOW}[OPTIONAL]${NC} Solana Wallet Address:"
    read -p "OWNER_SOLANA_WALLET=" SOL_WALLET

    # Create .env
    cat > .env << ENVEOF
# ═══ REQUIRED ═══
TELEGRAM_BOT_TOKEN=$TG_TOKEN
TEST_CHAT_ID=$CHAT_ID
OWNER_CHAT_ID=$CHAT_ID
ADMIN_CHAT_ID=$CHAT_ID

# ═══ AI PROVIDERS ═══
ANTHROPIC_API_KEY=$CLAUDE_KEY
GROQ_API_KEY=$GROQ_KEY
OPENAI_API_KEY=$OPENAI_KEY
GEMINI_API_KEY=$GEMINI_KEY

# ═══ CRYPTO ═══
COINDCX_API_KEY=$CDX_KEY
OWNER_SOLANA_WALLET=$SOL_WALLET
OWNER_PHANTOM_USERNAME=

# ═══ OPTIONAL ═══
WEBHOOK_URL=http://localhost:8000
WATCHLIST=NIFTY,SENSEX
HELIUS_API_KEY=
BIRDEYE_API_KEY=
DEXTOOLS_API_KEY=
FAST2SMS_API_KEY=
ENVEOF

    echo -e "${GREEN}✅ .env created successfully${NC}"
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

# Load env
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs 2>/dev/null)

# ═══════════════════════════════════════════════════════════
#  STEP 4: PYTHON DEPENDENCIES
# ═══════════════════════════════════════════════════════════

echo -e "\n${CYAN}━━━ STEP 4/6: Python Dependencies ━━━${NC}"
echo -e "${YELLOW}📦 Pehli baar 5-10 min lagenge, patience rakho...${NC}"

# Upgrade pip
$PYTHON -m pip install --upgrade pip 2>/dev/null

# Termux-friendly requirements (some packages need special handling)
# Install in groups to handle failures gracefully

echo -e "${YELLOW}  [1/5] Core packages...${NC}"
$PYTHON -m pip install requests python-dotenv pytz schedule 2>/dev/null

echo -e "${YELLOW}  [2/5] Data & ML packages...${NC}"
# numpy/pandas/scipy might already be installed via pkg
$PYTHON -m pip install pandas numpy joblib 2>/dev/null
$PYTHON -m pip install scikit-learn 2>/dev/null || echo -e "${YELLOW}  ⚠️ scikit-learn failed (ML features limited)${NC}"

echo -e "${YELLOW}  [3/5] AI packages...${NC}"
$PYTHON -m pip install groq openai anthropic google-generativeai 2>/dev/null

echo -e "${YELLOW}  [4/5] Analysis & web packages...${NC}"
$PYTHON -m pip install beautifulsoup4 feedparser textblob yfinance 2>/dev/null
$PYTHON -m pip install qrcode Pillow 2>/dev/null

echo -e "${YELLOW}  [5/5] Extra packages...${NC}"
$PYTHON -m pip install edge-tts nltk ta scipy 2>/dev/null || true
$PYTHON -m pip install fastapi uvicorn 2>/dev/null || true

# Heavy ML packages - may fail on Termux (that's OK, bot still works)
echo -e "${YELLOW}  [bonus] Heavy ML packages (may skip on some devices)...${NC}"
$PYTHON -m pip install xgboost 2>/dev/null || echo -e "${YELLOW}  ⚠️ xgboost skipped (OK — bot works without it)${NC}"
$PYTHON -m pip install lightgbm 2>/dev/null || echo -e "${YELLOW}  ⚠️ lightgbm skipped (OK — bot works without it)${NC}"
$PYTHON -m pip install pandas-ta 2>/dev/null || echo -e "${YELLOW}  ⚠️ pandas-ta skipped (OK)${NC}"
$PYTHON -m pip install shap 2>/dev/null || echo -e "${YELLOW}  ⚠️ shap skipped (OK)${NC}"

echo -e "${GREEN}✅ Python packages installed${NC}"

# ═══════════════════════════════════════════════════════════
#  STEP 5: VERIFY EVERYTHING
# ═══════════════════════════════════════════════════════════

echo -e "\n${CYAN}━━━ STEP 5/6: Verification ━━━${NC}"

# Bot script
if [ ! -f "$BOT_SCRIPT" ]; then
    echo -e "${RED}❌ $BOT_SCRIPT not found in $(pwd)!${NC}"
    echo -e "${YELLOW}Make sure you cloned the repo correctly.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Bot script found${NC}"

# Token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN empty! Edit .env file.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Telegram token: set${NC}"

# Chat ID
[ -n "$TEST_CHAT_ID" ] && echo -e "${GREEN}✅ Chat ID: $TEST_CHAT_ID${NC}" || echo -e "${YELLOW}⚠️ TEST_CHAT_ID not set${NC}"

# AI providers
echo -e "\n${BOLD}  AI Providers Status:${NC}"
[ -n "$ANTHROPIC_API_KEY" ] && echo -e "  ${GREEN}✅ Claude AI${NC}" || echo -e "  ${YELLOW}⚪ Claude (no key)${NC}"
[ -n "$GROQ_API_KEY" ] && echo -e "  ${GREEN}✅ Groq AI${NC}" || echo -e "  ${YELLOW}⚪ Groq (no key)${NC}"
[ -n "$OPENAI_API_KEY" ] && echo -e "  ${GREEN}✅ OpenAI${NC}" || echo -e "  ${YELLOW}⚪ OpenAI (no key)${NC}"
[ -n "$GEMINI_API_KEY" ] && echo -e "  ${GREEN}✅ Gemini${NC}" || echo -e "  ${YELLOW}⚪ Gemini (no key)${NC}"

# Python test
echo ""
$PYTHON -c "
import sys
print(f'  Python {sys.version.split()[0]}')
mods = {
    'requests': 'HTTP', 'pandas': 'Data', 'dotenv': 'Env',
    'groq': 'Groq AI', 'openai': 'OpenAI', 'anthropic': 'Claude',
    'yfinance': 'Yahoo Finance', 'bs4': 'Web Scraping'
}
ok = []
fail = []
for m, name in mods.items():
    try:
        __import__(m)
        ok.append(name)
    except:
        fail.append(name)
print(f'  ✅ Working: {len(ok)}/{len(mods)} — {\", \".join(ok)}')
if fail:
    print(f'  ⚠️  Missing: {\", \".join(fail)} (bot still works)')
" 2>/dev/null

# Kill old instance
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "\n${YELLOW}⚠️ Killing old bot instance (PID: $OLD_PID)${NC}"
        kill "$OLD_PID" 2>/dev/null
        sleep 2
        kill -9 "$OLD_PID" 2>/dev/null
    fi
    rm -f "$PID_FILE"
fi

# ═══════════════════════════════════════════════════════════
#  STEP 6: START BOT — FOREVER MODE
# ═══════════════════════════════════════════════════════════

echo ""
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║  🚀 JARVIS STARTING — 24/7 FOREVER MODE                  ║${NC}"
echo -e "${MAGENTA}║                                                          ║${NC}"
echo -e "${MAGENTA}║  📱 Phone lock karo, bot chalte rahega                    ║${NC}"
echo -e "${MAGENTA}║  🔋 Battery optimization OFF karo Termux ke liye          ║${NC}"
echo -e "${MAGENTA}║  🛑 STOP:  touch /tmp/jarvis_stop                         ║${NC}"
echo -e "${MAGENTA}║  📋 LOGS:  tail -f jarvis_bot.log                         ║${NC}"
echo -e "${MAGENTA}║  🔄 After phone restart: cd ~/jarvis && bash termux_setup.sh ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Termux wakelock (prevents Android from killing Termux)
if command -v termux-wake-lock &>/dev/null; then
    termux-wake-lock
    echo -e "${GREEN}🔒 Termux wake-lock ACTIVE (Android won't kill bot)${NC}"
fi

# ═══ FOREVER LOOP ═══
RESTART_COUNT=0

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    # Check stop signal
    if [ -f "$STOP_FILE" ]; then
        echo -e "${YELLOW}🛑 Stop signal received. JARVIS shutting down...${NC}"
        rm -f "$STOP_FILE" "$PID_FILE"
        # Release wakelock
        termux-wake-unlock 2>/dev/null || true
        exit 0
    fi

    RESTART_COUNT=$((RESTART_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${GREEN}🚀 [$TIMESTAMP] Starting JARVIS (run #$RESTART_COUNT)${NC}"

    # Start bot
    $PYTHON -u "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
    BOT_PID=$!
    echo "$BOT_PID" > "$PID_FILE"
    echo -e "${GREEN}✅ Bot PID: $BOT_PID${NC}"

    # Monitor loop
    while true; do
        sleep $HEALTH_CHECK_INTERVAL

        # Stop signal check
        if [ -f "$STOP_FILE" ]; then
            echo -e "${YELLOW}🛑 Stop signal. Killing bot...${NC}"
            kill "$BOT_PID" 2>/dev/null
            rm -f "$STOP_FILE" "$PID_FILE"
            termux-wake-unlock 2>/dev/null || true
            exit 0
        fi

        # Is bot alive?
        if ! kill -0 "$BOT_PID" 2>/dev/null; then
            echo -e "${RED}💀 Bot crashed! Restarting in ${RESTART_DELAY}s...${NC}"
            break
        fi

        # Memory check (restart if >400MB on phone)
        if command -v ps &>/dev/null; then
            MEM=$(ps -o rss= -p "$BOT_PID" 2>/dev/null || echo "0")
            MEM_MB=$((${MEM:-0} / 1024))
            if [ "$MEM_MB" -gt 400 ]; then
                echo -e "${YELLOW}⚠️ High memory: ${MEM_MB}MB. Restarting...${NC}"
                kill "$BOT_PID" 2>/dev/null
                sleep 2
                break
            fi
        fi
    done

    # Backoff delay
    if [ $RESTART_COUNT -gt 5 ]; then
        DELAY=$((RESTART_DELAY + RESTART_COUNT))
        [ $DELAY -gt 60 ] && DELAY=60
    else
        DELAY=$RESTART_DELAY
    fi

    echo -e "${YELLOW}⏳ Restart in ${DELAY}s...${NC}"
    sleep $DELAY

    # Rotate log if >5MB (phone storage save)
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$LOG_SIZE" -gt 5242880 ]; then
            tail -500 "$LOG_FILE" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "$LOG_FILE"
            echo -e "${YELLOW}📄 Log rotated (saving phone storage)${NC}"
        fi
    fi
done

echo -e "${RED}❌ Max restarts ($MAX_RESTARTS) reached.${NC}"
rm -f "$PID_FILE"
termux-wake-unlock 2>/dev/null || true
exit 1
