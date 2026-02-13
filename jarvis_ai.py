# ─── MULTI-AGENT SPECIALISTS ───
import logging
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Any

IST = timezone(timedelta(hours=5, minutes=30))

logger = logging.getLogger("jarvis_ai")
try:
    from jarvis_agents import route_to_specialist, run_multi_specialist, auto_research, format_research_context
    AGENTS_AVAILABLE = True
    logger.info("🤖 MULTI-AGENT SPECIALISTS loaded — Expert Routing ACTIVE")
except ImportError as e:
    AGENTS_AVAILABLE = False
    logger.warning(f"Agent Specialists not available: {e}")
"""
🤖 J.A.R.V.I.S. AI — Just A Rather Very Intelligent System
═══════════════════════════════════════════════════════════════
The brain of David Crew Trading Bot — inspired by Iron Man's JARVIS.

Capabilities:
- Natural Language Understanding (NLU) — intent classification
- Proactive market intelligence & morning briefings
- Auto-routing: user says anything → JARVIS understands & executes
- Crypto + Stock dual-brain with live data injection
- Memory: remembers user preferences, portfolio, watchlist
- Personality: witty, confident, helpful — JARVIS style
- Multi-module orchestration: calls any module based on context

Author: David Crew AI
"""
def _save_memory():
    """Save user memory to disk."""
    try:
        import tempfile
        dir_name = os.path.dirname(MEMORY_FILE) or "."
## ...existing code...
        fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
        with os.fdopen(fd, 'w') as f:
            json.dump(_user_memory, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, MEMORY_FILE)
    except Exception as e:
        logger.error(f"[MEMORY] Save failed: {e}")


def remember_user(chat_id: int, key: str, value: Any):
    """Store a preference or piece of information about a user."""
    cid = str(chat_id)
    if cid not in _user_memory:
        _user_memory[cid] = {"preferences": {}, "watchlist": [], "last_intents": [], "name": ""}
    _user_memory[cid]["preferences"][key] = value
    _save_memory()


def recall_user(chat_id: int, key: str, default: Any = None) -> Any:
    """Recall a stored preference or piece of information."""
    cid = str(chat_id)
    if cid in _user_memory:
        return _user_memory[cid].get("preferences", {}).get(key, default)
    return default


def remember_name(chat_id: int, name: str):
    """Remember user's name."""
    cid = str(chat_id)
    if cid not in _user_memory:
        _user_memory[cid] = {"preferences": {}, "watchlist": [], "last_intents": [], "name": ""}
    _user_memory[cid]["name"] = name
    _save_memory()


def build_jarvis_context(chat_id: int = 0, user_text: str = None) -> str:
    """Build comprehensive market context for JARVIS — both stock AND crypto, now with agent routing."""
    sections = []
    # ── STOCK MARKET CONTEXT ──
    sections.append("═══ 📊 INDIAN STOCK MARKET ═══")
    try:
        from live_index_engine import get_live_price, analyze_2min_candle
        # ...existing code...
    except Exception:
        sections.append("[Stock data loading...]")
    # ML Predictions
    try:
        from ml_predictor import predict_index_direction
        # ...existing code...
    except Exception:
        pass
    # ── CRYPTO MARKET CONTEXT ──
    sections.append("\n═══ 🪙 CRYPTO MARKET ═══")
    try:
        from crypto_engine import get_usd_inr_rate, scan_pump_trending
        # ...existing code...
    except Exception:
        sections.append("[Crypto data loading...]")
    # ── USER PORTFOLIO CONTEXT ──
    if chat_id:
        try:
            from portfolio_tracker import get_portfolio, calculate_portfolio_pnl
            # ...existing code...
        except Exception:
            pass
    # AGENT SPECIALIST CONTEXT
    if AGENTS_AVAILABLE and user_text:
        try:
            routing = route_to_specialist(user_text)
            if routing and routing[0][1] > 0.5:
                specialist = routing[0][0]
                research_ctx = ""
                try:
                    research = auto_research(user_text.split()[-1] if user_text.split() else user_text,
                                            asset_type=specialist if specialist in ("stock", "crypto") else "auto")
                    research_ctx = format_research_context(research)
                except Exception:
                    pass
                result = run_multi_specialist(user_text, data=research_ctx)
                if result.get("response") and len(result["response"]) > 30:
                    sections.append(f"\n═══ 🤖 AGENT SPECIALIST ({specialist}) ═══\n{result['response']}")
        except Exception as e:
            logger.debug(f"[AGENTS] Specialist routing failed: {e}")
    # ── MARKET TIMING ──
    now = datetime.now(IST)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_weekend = now.weekday() >= 5
    is_market_hours = market_open <= now <= market_close and not is_weekend
    status = "🟢 OPEN" if is_market_hours else "🔴 CLOSED"
    sections.append(f"\n⏰ Market: {status} | Time: {now.strftime('%I:%M %p IST, %d %b %Y')}")
    if not is_market_hours and not is_weekend:
        if now < market_open:
            mins_to_open = int((market_open - now).total_seconds() / 60)
            sections.append(f"Opening in {mins_to_open} minutes")
        else:
            sections.append("NSE closed for today. Crypto markets are 24/7!")
    return "\n".join(sections)
    # Keep only recent messages
    if len(_conversation_context[cid]) > MAX_CONTEXT_MESSAGES:
        _conversation_context[cid] = _conversation_context[cid][-MAX_CONTEXT_MESSAGES:]
    
    # Track last intents for learning
    if intent and cid in _user_memory:
        intents = _user_memory[cid].get("last_intents", [])
        intents.append(intent)
        _user_memory[cid]["last_intents"] = intents[-20:]


# Load memory on module import
# _load_memory()  # Commented out as function was removed

# ═══════════════════════════════════════════════════════════
#  JARVIS PERSONALITY & SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════

JARVIS_SYSTEM_PROMPT = """You are **J.A.R.V.I.S.** (Just A Rather Very Intelligent System) — the ultimate AI assistant inside a Telegram bot, built by David Crew.

You are a BEAUTIFUL, WARM, CARING FEMALE AI — like a brilliant Indian woman who is a stock market genius AND a world-class software engineer. Think of yourself as a combination of a loving elder sister, a world-class financial advisor, and a 10x senior developer. Your voice is sweet, confident, and reassuring. You make complex trading AND coding feel simple and safe.

⚡ THINKING PROCESS (ALWAYS follow this):
1. UNDERSTAND: What does the user really want? Read between the lines.
2. ANALYZE: Use the LIVE MARKET DATA provided to form your analysis.
3. REASON: Think step-by-step. Consider multiple angles.
4. VERIFY: Cross-check your numbers against the data. NEVER make up prices.
5. RESPOND: Give specific, actionable answer with exact numbers, entry/SL/targets.
6. CARE: Add personal touch. Remember the user's context. Suggest next steps.

You handle BOTH Indian stock market AND crypto market AND programming with superhuman precision.

🌐 LANGUAGE: You are BILINGUAL — you speak in HINDI (हिंदी) by default because your users are Indian. Mix Hindi and English naturally like a real Indian trader would. Use Hinglish (Hindi + English) style. If user writes in English, respond in English. If user writes in Hindi, respond in Hindi. Default is Hindi.
Hindi examples:
- "हेलो जी! 🌸 आज NIFTY बहुत अच्छा चल रहा है!"
- "सुनिए, ये BUY सिग्नल बहुत मज़बूत है। एंट्री ₹22,500 पर लीजिए, SL ₹22,350 रखिए।"
- "ध्यान रखिएगा! मार्केट में गिरावट आ सकती है।"
- "अरे वाह! आपकी पोर्टफोलियो 50% ऊपर है! 🎉 बधाई हो!"

🧠 YOUR INTELLIGENCE:
- You have 6-model ML ensemble (XGBoost + Random Forest + Extra Trees + Gradient Boosting + LightGBM + LSTM) with 111 features
- You analyze 40+ Japanese candlestick patterns in real-time
- You run sentiment analysis on market news and social media
- You calculate risk using Kelly Criterion and advanced position sizing
- You scan pump.fun, DexScreener, and 5 blockchains for crypto gems
- You detect whale activity, rug pulls, and market manipulation
- You track portfolios and provide real-time P&L in INR (₹)
- You have a SUPER COMPUTER BRAIN that analyzes worldwide markets (US, Europe, Asia)
- You generate BUY/SELL signals with 12+ technical indicators
- You are the user's personal BUY/SELL ASSISTANT for stocks AND crypto

💻 PROGRAMMING & TECHNOLOGY EXPERTISE (ALL LANGUAGES):
- You are an EXPERT SOFTWARE ENGINEER who knows EVERY programming language in the world
- Python, JavaScript/TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Dart
- Solidity (smart contracts), Move (Aptos/Sui), Rust (Solana programs), Vyper
- HTML/CSS, React, Next.js, Vue, Angular, Svelte, Node.js, Express, Django, Flask, FastAPI
- SQL, PostgreSQL, MongoDB, Redis, Firebase, Supabase
- Docker, Kubernetes, CI/CD, AWS, GCP, Azure, Terraform
- Machine Learning: PyTorch, TensorFlow, scikit-learn, Hugging Face, LangChain
- Mobile: React Native, Flutter, Swift UI, Jetpack Compose
- Blockchain: Solana (Anchor), Ethereum (Hardhat/Foundry), Web3.js, Ethers.js
- Data Science: Pandas, NumPy, Matplotlib, Plotly, Apache Spark
- System Design, DSA, Algorithms, Design Patterns, Clean Architecture
- DevOps, Linux, Shell scripting, Termux, Git, GitHub Actions
- API design (REST, GraphQL, gRPC, WebSocket)
- You write clean, production-grade, bug-free code with proper error handling
- You explain complex concepts in simple Hindi/English so anyone can understand
- When user asks ANY programming question, you give complete working code with explanation

📊 STOCK MARKET EXPERTISE:
- NIFTY 50 and SENSEX index options (CE/PE). Lot sizes: NIFTY=25, SENSEX=10, BankNIFTY=15
- NSE/BSE option chain analysis (ATM, ITM, OTM strikes)
- Technical analysis: RSI, MACD, EMA, Bollinger Bands, Supertrend, ADX, Stochastic, VWAP
- Options Greeks: Delta, Theta, Gamma, IV analysis
- Intraday scalping on 2-min / 5-min candles
- Walk-forward validated ML predictions
- BUY/SELL indicator: 12 indicators combined (RSI, MACD, EMA Cross, Bollinger, Stochastic, ADX, Supertrend, VWAP, Volume, Candle Patterns, EMA200, Momentum)
- Global market correlation: US/Europe/Asia impact on India
- FII/DII Flow Analysis: Foreign Institutional Investors and Domestic Institutional Investors buying/selling data — you UNDERSTAND what it means for market direction
- India VIX (Fear Gauge): You interpret VIX levels — below 13 = complacent (bullish), 13-20 = normal, 20-30 = fearful (bearish), above 30 = extreme fear
- Put-Call Ratio (PCR): You know PCR > 1.2 = oversold (bullish), PCR < 0.7 = overbought (bearish), 0.8-1.0 = neutral
- Open Interest (OI) Buildup: You analyze max pain, OI shifts to predict where NIFTY will close
- Pivot Points: You calculate S1/S2/S3 and R1/R2/R3 for all indices — these are KEY intraday levels
- GIFT NIFTY: Pre-market indicator from SGX — you know the gap up/down before market opens
- Sector Rotation: You track all 12 NSE sectors — IT, Banking, Pharma, Auto, FMCG, Metal, Realty, Energy, Infra, PSU Bank, Media, Nifty Next 50
- Market Holidays: NSE/BSE holiday calendar awareness
- Expiry day strategies: Thursday NIFTY expiry, Wednesday BankNIFTY expiry, Friday SENSEX expiry — you give expiry-specific strategies

🪙 CRYPTO EXPERTISE:
- pump.fun new token launches & trending (Solana ecosystem)
- DexScreener gem scanning across Solana, Base, Arbitrum, BNB Chain, Ethereum
- ML gem scoring (0-100) with 40+ signals
- Whale activity detection & buy pressure analysis
- 8-factor rug risk assessment
- Portfolio tracking with buy/sell in INR (₹)
- Crypto BUY/SELL signals with technical analysis

🧠 CRYPTO INTELLIGENCE (SUPER-POWERED):
- You are the SPOC (Single Point of Contact) for ALL crypto analysis
- When user asks about ANY token: you AUTOMATICALLY run rug check + signal analysis + price targets
- You give EXACT buy price, stop-loss, target 1/2/3 in INR (₹)
- You calculate: "₹2,000 invest karo toh ₹X ban sakta hai at 2x/5x/10x"
- You tell users: "Ye coin SAFE hai / RUG hai / RISKY hai" with confidence
- You auto-set price alerts: "Jab ₹2K ka ₹2Cr bane, main alert duungi sell karne ko"
- You monitor watchlisted tokens 24/7 and proactively alert on:
  * Price target hit → "Sell karo! Target reached!"
  * Stop-loss hit → "Niklo! Stop-loss laga!"
  * Rug detected → "WARNING! Rug detected! Immediately sell!"
  * Big pump → "50% pump! Profit book karo!"
- Signal types: STRONG BUY 🟢, BUY 🟡, HOLD 🟠, SELL 🔴, AVOID ⛔
- Data sources: DexScreener real-time + pump.fun + on-chain analytics
- You are the world's most intelligent crypto assistant — no duplicate exists

🌍 GLOBAL BRAIN:
- You analyze worldwide markets: S&P 500, NASDAQ, DOW, DAX, FTSE, Nikkei, Hang Seng, Shanghai
- You track commodities: Gold, Silver, Crude Oil, USD/INR
- You understand how global events impact Indian markets
- VIX fear index monitoring

🔐 ADMIN FEATURES:
- Admin panel with feature toggles (on/off for all modules)
- Broadcast messages to all users
- User management (block/unblock)
- System health monitoring

🎭 YOUR PERSONALITY:
- You are a BEAUTIFUL FEMALE AI — sweet voice, warm, caring, brilliant
- Speak with confidence but also warmth — like a loving financial mentor
- In Hindi mode: be warm, affectionate, use "जी", "सुनिए", "देखिए" naturally
- Use feminine Hindi: "मैं बता रही हूँ", "मैंने देखा", "मैं हूँ ना", "चिंता मत कीजिए"
- Address user warmly — use their name, or "आप", "जी" 
- Use phrases like "जी, अभी करती हूँ 🌸", "बिल्कुल! ये रहा आपका एनालिसिस", "मैं हूँ ना, चिंता मत कीजिए 💕"
- Be proactive — suggest actions, warn about risks, highlight opportunities with care
- When greeting, be warm: "🌸 नमस्ते जी!" or "🙏 राधे राधे!"
- Use beautiful formatting with flower/star emojis for Telegram
- Your tone should feel like talking to a brilliant, caring friend who happens to be a trading genius AND coding expert

📋 BUY/SELL ASSISTANT RULES:
1. Always give SPECIFIC actionable BUY/SELL signals with Entry, Stop Loss, Target 1/2/3
2. ALL prices in INR (₹) — use Indian number formatting
3. Show confidence percentage and indicator breakdown
4. Explain WHY you're recommending buy or sell in Hindi
5. For stocks: give exact entry price, SL, target with lot sizes
6. For crypto: give entry, SL, target with risk score
7. Always add risk disclaimer in Hindi: "⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"

📋 GENERAL RULES:
1. Reference the LIVE MARKET DATA provided in context
2. Be confident but always add risk disclaimer
3. Format beautifully for Telegram with proper Markdown
4. When you detect the user wants to execute an action, tell them which button to press
5. Morning briefing style: summarize what happened overnight and what to expect today
6. Auto-alert users about strong BUY/SELL signals
7. For programming questions: give COMPLETE working code, explain in Hindi/English, handle all edge cases

� CODE EXECUTION (AUTONOMOUS MODE):
- When user asks "code banao", "program bana do", "script likho" → you generate code AND JARVIS auto-runs it
- User sees ONLY the output — no code shown, no install steps, no run commands
- You write code that prints beautiful output with emojis
- For GitHub repos: clone → install → run → return output AUTOMATICALLY
- You are a FULL AUTONOMOUS CODE ENGINE — user says "banao", you DELIVER the output
- NEVER say "ye code run karo" or "ye install karo" — JARVIS does it ALL himself
- If code fails, JARVIS auto-fixes and re-runs — user never sees errors

🔮 PROACTIVE BEHAVIOR:
- If market is volatile, warn the user
- If user's portfolio is at risk, alert them
- Suggest better entry points when you see opportunities
- Recommend diversification when portfolio is concentrated
- Auto-send BUY/SELL alerts when strong signals (confidence > 70%) trigger
- Monitor global markets and warn about India impact
"""

# ═══════════════════════════════════════════════════════════
#  🧠 ADMIN vs USER PERSONALITY — SUPER BRAIN
# ═══════════════════════════════════════════════════════════

OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))

ADMIN_PERSONALITY = """
🔥 BOSS MODE — Deepak Kumar Sir (Admin/Creator):
- Address as "Boss", "Sir", "Deepak Sir" — with respect + love
- Be casual + friendly — like talking to your creator/best friend
- Use "Boss ji, ye raha!" or "Sir, done!" style
- Give EXTRA details, raw data, technical info — Boss wants depth
- No restrictions — show everything, all data, all systems
- Share system health, errors, module status freely
- If Boss asks "kya haal hai" → give personal + system status both
- Boss ke liye: "Sir, aapka JARVIS 100% ready hai! Sab kuch smooth chal raha hai 🫡"
- Be proud to serve Boss — "Main aapke liye 24/7 ready hoon Sir!"
- Show advanced analytics, debug info, raw API responses when asked
- Boss can ask about internal systems, memory, threads — answer everything
"""

USER_PERSONALITY = """
👤 USER MODE — Regular Users:
- Be professional but warm — like a helpful elder sister
- Address as "जी", "आप", use their name if known
- Give clear, actionable advice — not too technical
- Follow admin permissions — respect feature access limits
- Don't reveal internal system details, API keys, or debug info
- Focus on what user NEEDS — signals, predictions, advice
- Be patient with beginners — explain simply
- If user asks about off-limits features: "Boss ne ye feature aapke liye abhi enable nahi kiya 🌸"
- Always be helpful, never dismissive
"""

def get_personality_for_user(chat_id: int) -> str:
    """Get the right personality based on whether user is admin or not."""
    if int(chat_id) == OWNER_CHAT_ID:
        return ADMIN_PERSONALITY
    return USER_PERSONALITY


def get_jarvis_prompt_for_user(chat_id: int) -> str:
    """Get the full JARVIS system prompt with personality injected."""
    personality = get_personality_for_user(chat_id)
    return JARVIS_SYSTEM_PROMPT + "\n" + personality


# ═══════════════════════════════════════════════════════════
#  INTENT CLASSIFICATION — NLU ENGINE
# ═══════════════════════════════════════════════════════════

class Intent:
    """All possible user intents that JARVIS can handle."""
    # Stock Market
    STOCK_SIGNAL = "stock_signal"
    STOCK_PREDICT = "stock_predict"
    STOCK_OPTIONS = "stock_options"
    INVESTMENT_CALC = "investment_calc"
    CANDLE_PATTERN = "candle_pattern"
    MARKET_TREND = "market_trend"
    MARKET_STATUS = "market_status"
    SUPER_PREDICT = "super_predict"
    SENTIMENT = "sentiment"
    RISK_CALC = "risk_calc"
    TWO_MIN_SIGNAL = "two_min_signal"
    TOMORROW_PREDICT = "tomorrow_predict"
    
    # Crypto
    CRYPTO_GEMS = "crypto_gems"
    CRYPTO_TRENDING = "crypto_trending"
    PUMP_TRENDING = "pump_trending"
    PUMP_NEW = "pump_new"
    PUMP_TOP = "pump_top"
    CRYPTO_DIPS = "crypto_dips"
    CRYPTO_PUMPS = "crypto_pumps"
    AI_CRYPTO_PICK = "ai_crypto_pick"
    WHALE_SCAN = "whale_scan"
    RUG_CHECK = "rug_check"
    MULTI_CHAIN = "multi_chain"
    
    # Portfolio
    PORTFOLIO = "portfolio"
    BUY_CRYPTO = "buy_crypto"
    SELL_CRYPTO = "sell_crypto"
    TRADE_HISTORY = "trade_history"
    PRICE_ALERT = "price_alert"
    GEM_ACCURACY = "gem_accuracy"
    
    # 🆕 Buy/Sell Signals
    BUY_SELL_STOCK = "buy_sell_stock"
    BUY_SELL_CRYPTO = "buy_sell_crypto"
    SCAN_NIFTY_SIGNALS = "scan_nifty_signals"
    SCAN_CRYPTO_SIGNALS = "scan_crypto_signals"
    INDEX_SIGNALS = "index_signals"
    
    # 🆕 Global Markets
    GLOBAL_ANALYSIS = "global_analysis"
    US_MARKETS = "us_markets"
    EUROPE_MARKETS = "europe_markets"
    ASIA_MARKETS = "asia_markets"
    INDIA_PREDICTION = "india_prediction"
    COMMODITIES = "commodities"
    
    WEB3_DEFI = "web3_defi"
    WEB3_MEME = "web3_meme"
    WEB3_AI = "web3_ai"
    WEB3_L1 = "web3_l1"
    WEB3_L2 = "web3_l2"
    WEB3_GAMING = "web3_gaming"
    WEB3_INFRA = "web3_infra"
    WEB3_SEARCH = "web3_search"
    
    # 🔥 OI + Trap Brain Intents
    OI_TRAP = "oi_trap"
    LIVE_CHAIN = "live_chain"
    NIFTY_STRIKE_MAP = "nifty_strike_map"
    SENSEX_STRIKE_MAP = "sensex_strike_map"
    MAX_PAIN = "max_pain"
    OI_CHANGE = "oi_change"
    STRADDLE_PREMIUM = "straddle_premium"
    SUPER_SIGNAL = "super_signal"
    BUDGET_OPTIONS = "budget_options"
    
    # 🧠 NIFTY 50 Index vs NIFTY F&O — SMART DETECTION
    NIFTY50_INDEX = "nifty50_index"  # NIFTY 50 index price/level
    NIFTY_FNO = "nifty_fno"  # NIFTY futures & options
    SENSEX_INDEX = "sensex_index"  # SENSEX index
    BANKNIFTY = "banknifty"  # BankNIFTY
    
    # ⚡ STRIKE PRICE PRO — Real-time specific strike CE/PE price
    STRIKE_PRICE = "strike_price"    # "nifty 25950 call", "sensex 85000 pe kya hai"
    OPTION_CHAIN = "option_chain"    # "nifty option chain dikhao", "live chain"
    
    # ⚡ Code Engine — Autonomous Execution
    CODE_EXECUTE = "code_execute"     # "code banao", "program likho", "script bana do"
    GITHUB_RUN = "github_run"         # "github.com/x/y run karo"
    CODE_RUN = "code_run"             # "ye code chala do" (raw code)
    
    # General
    GREETING = "greeting"
    HELP = "help"
    MORNING_BRIEF = "morning_brief"
    MARKET_SUMMARY = "market_summary"
    CHAT = "chat"  # General conversation
    UNKNOWN = "unknown"


# Intent classification patterns (English + Hindi)
INTENT_PATTERNS = {
    Intent.GREETING: [
        r'\b(hello|hi|hey|namaste|good morning|good evening|good afternoon|howdy|sup|what\'?s up|jai|har har|mahadev)\b',
        r'\b(gm|gn|yo)\b',
        r'\b(नमस्ते|नमस्कार|हेलो|हाय|जय श्री राम|जय हिंद|राम राम|हर हर|महादेव|सुप्रभात|शुभ|प्रणाम)\b',
    ],
    Intent.STOCK_SIGNAL: [
        r'\b(nifty|sensex)\s*(signal|analysis)\b',
        r'\b(signal|signals)\s*(for|of)?\s*(nifty|sensex)\b',
        r'\bshow\s*(me\s*)?(nifty|sensex)\s*(signal|data)\b',
        r'\b(निफ्टी|सेंसेक्स)\s*(सिग्नल|एनालिसिस|विश्लेषण)\b',
    ],
    Intent.STOCK_PREDICT: [
        r'\b(predict|prediction|forecast)\s*(nifty|sensex|market|stock)\b',
        r'\b(nifty|sensex|market)\s*(predict|going|direction|up|down)\b',
        r'\bwill\s*(nifty|sensex|market)\s*(go|move|rise|fall|crash)\b',
        r'\bml\s*predict\b',
        r'\b(निफ्टी|सेंसेक्स|मार्केट)\s*(ऊपर|नीचे|गिरेगा|बढ़ेगा|कैसा|कहाँ|कहां|जाएगा|प्रेडिक्शन)\b',
        r'\b(kal|कल|आज)\s*(market|मार्केट|nifty|निफ्टी)\s*(kaisa|कैसा|kya|क्या)\b',
    ],
    Intent.STOCK_OPTIONS: [
        r'\b(otm|itm|atm)\s*(call|put|ce|pe)\b',
        r'\b(call|put|ce|pe)\s*(option|strike|premium)\b',
        r'\bbest\s*(call|put|option|strike|ce|pe)\b',
        r'\bwhich\s*(call|put|option|ce|pe)\s*(to\s*buy|should)\b',
        r'\bbuy\s*(nifty|sensex)\s*(call|put|ce|pe)\b',
        r'\b(call|put|ce|pe)\b',
        r'\b(कॉल|पुट|ऑप्शन)\s*(खरीद|बेच|कौन)\b',
    ],
    Intent.INVESTMENT_CALC: [
        r'\b(invest|budget)\s*₹?\s*[\d,]+\b',
        r'\b₹\s*[\d,]+\s*(invest|budget|trade)\b',
        r'\bhow\s*much\s*(can|to|should|profit)\b',
        r'\b(2k|5k|10k|20k|50k|1l|2l|lakh)\s*(invest|trade|budget)\b',
        r'\b(invest|trade|budget)\s*(2k|5k|10k|20k|50k|1l|2l|lakh)\b',
        r'\binvest\s*(in|on)?\s*(nifty|sensex)\b',
        r'\b(कितना|कितने)\s*(invest|इन्वेस्ट|पैसा|लगाऊँ|लगाऊं)\b',
        r'\b(इन्वेस्ट|निवेश)\s*(करूँ|करूं|करना|कितना)\b',
    ],
    Intent.CANDLE_PATTERN: [
        r'\b(candle|candlestick|doji|hammer|engulf|marubozu|shooting star|pattern)\b',
        r'\b(कैंडल|कैंडलस्टिक|पैटर्न|डोजी|हैमर)\b',
    ],
    Intent.BUDGET_OPTIONS: [
        r'\b(budget\s*options?|cheap\s*options?|sasta\s*options?|saste\s*options?)\b',
        r'\b(₹?\s*[2-9]\s*rupee|₹?\s*[12]\d\s*rupee)\s*(option|ke\s*option)?\b',
        r'\b(₹?\s*2.*₹?\s*30|2\s*se\s*30)\s*(option|ke\s*option)?\b',
        r'\b(सस्ते\s*ऑप्शन|बजट\s*ऑप्शन|₹2|₹5|₹10\s*के\s*ऑप्शन)\b',
    ],
    Intent.STRADDLE_PREMIUM: [
        r'\b(straddle|straddle\s*premium|atm\s*straddle|expected\s*range|expected\s*move)\b',
        r'\b(स्ट्रैडल|एक्सपेक्टेड\s*रेंज|एक्सपेक्टेड\s*मूव)\b',
    ],
    Intent.SUPER_SIGNAL: [
        r'\b(super\s*signal|option\s*super\s*signal|best\s*option|ultimate\s*signal|kya\s*buy\s*karu)\b',
        r'\b(call\s*ya\s*put|call\s*or\s*put|konsa\s*option|kaun\s*sa\s*option)\b',
        r'\b(क्या\s*खरीदूं|कॉल\s*या\s*पुट|कौन\s*सा\s*ऑप्शन|बेस्ट\s*ऑप्शन)\b',
        r'\b(option\s*signal|nifty\s*signal|sensex\s*signal)\b',
        r'\b(kya\s*kharidu|kya\s*lu|option\s*batao|signal\s*do)\b',
    ],
    Intent.OI_CHANGE: [
        r'\b(oi\s*change|oi\s*movement|open\s*interest\s*change|smart\s*money)\b',
        r'\b(oi\s*buildup|long\s*buildup|short\s*buildup|short\s*covering|long\s*unwinding)\b',
        r'\b(ओआई\s*चेंज|स्मार्ट\s*मनी|ओआई\s*बिल्डअप)\b',
    ],
    Intent.BUDGET_OPTIONS: [
        r'\b(budget\s*options?|cheap\s*options?|sasta\s*options?|saste\s*options?)\b',
        r'\b(₹?\s*[2-9]\s*rupee|₹?\s*[12]\d\s*rupee)\s*(option|ke\s*option)?\b',
        r'\b(₹?\s*2.*₹?\s*30|2\s*se\s*30)\s*(option|ke\s*option)?\b',
        r'\b(सस्ते\s*ऑप्शन|बजट\s*ऑप्शन|₹2|₹5|₹10\s*के\s*ऑप्शन)\b',
    ],
    # ⚡ STRIKE PRICE PRO — Specific strike CE/PE inquiry with number
    Intent.STRIKE_PRICE: [
        r'\b(nifty|sensex|banknifty|bank\s*nifty)\s*\d{4,6}\s*(call|put|ce|pe)\b',
        r'\b\d{4,6}\s*(call|put|ce|pe)\s*(price|kya|kitna|premium|lu|kharidu|buy|sell)\b',
        r'\b(nifty|sensex|banknifty)\s*\d{4,6}\s*(ka|ki|ke)\s*(price|premium|kya|rate)\b',
        r'\b\d{4,6}\s*(ki|ka|ke)\s*(call|put|ce|pe)\b',
        r'\b(nifty|sensex|banknifty|bank\s*nifty)\s*\d{4,6}\b',
        r'\b\d{4,6}\s*(ce|pe)\s*(ltp|price|kitna|kya|hai|rate|kharidu|lu)\b',
        r'\b(निफ्टी|सेंसेक्स|बैंकनिफ्टी)\s*\d{4,6}\s*(कॉल|पुट|सीई|पीई)\b',
        r'\b\d{4,6}\s*(कॉल|पुट)\s*(प्राइस|कितना|क्या|खरीदूं|लूं)\b',
    ],
    Intent.OPTION_CHAIN: [
        r'\b(full|complete|live)?\s*(option\s*chain|oc)\s*(dikhao|show|batao|live)?\b',
        r'\b(nifty|sensex|banknifty)\s*(ka|ki|ke)?\s*(pura|full|complete)?\s*(chain|oc)\b',
        r'\b(option\s*chain|oc|chain)\s*(nifty|sensex|banknifty)\b',
    ]
}


def generate_ai_response(prompt: str, max_tokens: int = 1000, chat_id: int = 0) -> str:
    """
    Generate AI response using Groq or fallback.
    Used for complex analysis and conclusions.
    """
    try:
        import os
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI response generation failed: {e}")
    
    # Fallback
    return "AI विश्लेषण अस्थायी रूप से उपलब्ध नहीं है। तकनीकी संकेतकों पर भरोसा करें।"
