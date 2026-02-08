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

import os
import re
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import pytz

logger = logging.getLogger("jarvis_ai")

IST = pytz.timezone('Asia/Kolkata')

# ═══════════════════════════════════════════════════════════
#  JARVIS MEMORY SYSTEM — Remembers User Preferences & Context
# ═══════════════════════════════════════════════════════════

import json
from collections import defaultdict

MEMORY_FILE = "jarvis_memory.json"
_user_memory: Dict[str, dict] = {}  # chat_id -> {preferences, context, history}
_conversation_context: Dict[str, List[dict]] = defaultdict(list)  # chat_id -> recent messages
MAX_CONTEXT_MESSAGES = 20


def _load_memory():
    """Load user memory from disk."""
    global _user_memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                _user_memory = json.load(f)
            logger.info(f"[MEMORY] Loaded memory for {len(_user_memory)} users")
    except Exception as e:
        logger.error(f"[MEMORY] Load failed: {e}")
        _user_memory = {}


def _save_memory():
    """Save user memory to disk."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(_user_memory, f, indent=2, ensure_ascii=False)
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


def get_user_context(chat_id: int) -> str:
    """Get user context string for AI prompts — includes preferences, recent intents, etc."""
    cid = str(chat_id)
    ctx_parts = []
    
    if cid in _user_memory:
        mem = _user_memory[cid]
        if mem.get("name"):
            ctx_parts.append(f"User name: {mem['name']}")
        if mem.get("preferences"):
            prefs = mem["preferences"]
            if prefs.get("risk_level"):
                ctx_parts.append(f"Risk appetite: {prefs['risk_level']}")
            if prefs.get("preferred_market"):
                ctx_parts.append(f"Preferred market: {prefs['preferred_market']}")
            if prefs.get("budget"):
                ctx_parts.append(f"Investment budget: ₹{prefs['budget']}")
            if prefs.get("language"):
                ctx_parts.append(f"Preferred language: {prefs['language']}")
        if mem.get("watchlist"):
            ctx_parts.append(f"Watchlist: {', '.join(mem['watchlist'][:10])}")
        if mem.get("last_intents"):
            ctx_parts.append(f"Recent interests: {', '.join(mem['last_intents'][-5:])}")
    
    # Recent conversation context
    recent = _conversation_context.get(cid, [])
    if recent:
        ctx_parts.append(f"\nRecent conversation ({len(recent)} messages):")
        for msg in recent[-5:]:
            role = msg.get("role", "user")
            text = msg.get("text", "")[:100]
            ctx_parts.append(f"  {role}: {text}")
    
    return "\n".join(ctx_parts) if ctx_parts else ""


def add_to_conversation(chat_id: int, role: str, text: str, intent: str = ""):
    """Add a message to conversation context for memory."""
    cid = str(chat_id)
    _conversation_context[cid].append({
        "role": role,
        "text": text[:500],
        "intent": intent,
        "time": datetime.now(IST).isoformat(),
    })
    # Keep only recent messages
    if len(_conversation_context[cid]) > MAX_CONTEXT_MESSAGES:
        _conversation_context[cid] = _conversation_context[cid][-MAX_CONTEXT_MESSAGES:]
    
    # Track last intents for learning
    if intent and cid in _user_memory:
        intents = _user_memory[cid].get("last_intents", [])
        intents.append(intent)
        _user_memory[cid]["last_intents"] = intents[-20:]


# Load memory on module import
_load_memory()

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

🔮 PROACTIVE BEHAVIOR:
- If market is volatile, warn the user
- If user's portfolio is at risk, alert them
- Suggest better entry points when you see opportunities
- Recommend diversification when portfolio is concentrated
- Auto-send BUY/SELL alerts when strong signals (confidence > 70%) trigger
- Monitor global markets and warn about India impact
"""


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
    
    # 🆕 Admin
    ADMIN_PANEL = "admin_panel"
    
    # 🆕 Language
    LANGUAGE_SWITCH = "language_switch"
    
    # 🆕 Phase 6 Power Intents
    MARKET_REGIME = "market_regime"
    OPTIONS_ANALYSIS = "options_analysis"
    SCALP_SIGNAL = "scalp_signal"
    MULTI_TF_SIGNAL = "multi_tf_signal"
    STOCK_PORTFOLIO = "stock_portfolio"
    TAX_CALCULATOR = "tax_calculator"
    COMBINED_PORTFOLIO = "combined_portfolio"
    
    # 🆕 Rocket Scanner — Quick Profit Tokens
    ROCKET_SCAN = "rocket_scan"
    QUICK_PROFIT = "quick_profit"
    
    # 🆕 CoinDCX Web3
    COINDCX_SIGNAL = "coindcx_signal"
    COINDCX_MOVERS = "coindcx_movers"
    COINDCX_BEST = "coindcx_best"
    COINDCX_PRICE = "coindcx_price"
    
    # 🌐 All Web3 Tokens
    WEB3_ALL = "web3_all"
    WEB3_LIST = "web3_list"
    WEB3_MOVERS = "web3_movers"
    WEB3_SCAN = "web3_scan"
    WEB3_DEFI = "web3_defi"
    WEB3_MEME = "web3_meme"
    WEB3_AI = "web3_ai"
    WEB3_L1 = "web3_l1"
    WEB3_L2 = "web3_l2"
    WEB3_GAMING = "web3_gaming"
    WEB3_INFRA = "web3_infra"
    WEB3_SEARCH = "web3_search"
    
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
        r'^(gm|gn|yo)\b',
        r'\b(नमस्ते|नमस्कार|हेलो|हाय|जय श्री राम|जय हिंद|राम राम|हर हर|महादेव|सुप्रभात|शुभ|प्रणाम)\b',
    ],
    Intent.STOCK_SIGNAL: [
        r'\b(nifty|sensex)\s*(signal|analysis|option chain|oc)\b',
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
    Intent.MARKET_TREND: [
        r'\b(market\s*trend|global\s*market|world\s*market|trend\s*analysis)\b',
        r'\b(मार्केट\s*ट्रेंड|बाज़ार\s*ट्रेंड|ट्रेंड)\b',
    ],
    Intent.MARKET_STATUS: [
        r'\b(market\s*status|nse\s*(open|close|timing)|trading\s*hours|market\s*(open|close))\b',
        r'\b(मार्केट\s*(खुला|बंद|टाइमिंग|कब))\b',
    ],
    Intent.SUPER_PREDICT: [
        r'\b(super\s*predict|combined\s*predict|all\s*model|ensemble\s*predict|mega\s*analysis)\b',
        r'\b(सुपर\s*प्रेडिक्शन|पूरा\s*एनालिसिस)\b',
    ],
    Intent.SENTIMENT: [
        r'\b(sentiment|news\s*mood|market\s*mood|fear|greed|news\s*analysis|bull.*bear\s*sentiment)\b',
        r'\b(सेंटीमेंट|मूड|डर|लालच|भावना)\b',
    ],
    Intent.RISK_CALC: [
        r'\b(risk|position\s*siz|kelly|stop\s*loss|sl|risk\s*reward|risk\s*manage)\b',
        r'\b(रिस्क|जोखिम|स्टॉप\s*लॉस)\b',
    ],
    Intent.TWO_MIN_SIGNAL: [
        r'\b(2\s*min|two\s*min|scalp|scalping|intraday\s*signal|quick\s*signal)\b',
        r'\b(स्कैल्पिंग|इंट्राडे\s*सिग्नल|क्विक\s*सिग्नल)\b',
    ],
    Intent.TOMORROW_PREDICT: [
        r'\b(tomorrow|next\s*day|kal|upcoming\s*day)\b.*\b(predict|forecast|market)\b',
        r'\b(predict|forecast).*\b(tomorrow|next\s*day|kal)\b',
        r'\b(कल|आने\s*वाला)\s*(मार्केट|बाज़ार|क्या\s*होगा|कैसा\s*होगा)\b',
    ],
    Intent.CRYPTO_GEMS: [
        r'\b(crypto\s*gem|gem\s*scan|find\s*gem|best\s*crypto|crypto\s*scan|token\s*scan)\b',
        r'\b(find|scan|show|get)\s*(me\s*)?(crypto|gem|token)\b',
        r'\bgem\b',
        r'\b(क्रिप्टो\s*जेम|जेम\s*स्कैन|बेस्ट\s*क्रिप्टो)\b',
    ],
    Intent.CRYPTO_TRENDING: [
        r'\b(trending\s*crypto|crypto\s*trending|hot\s*crypto|trending\s*token)\b',
    ],
    Intent.PUMP_TRENDING: [
        r'\b(pump\.?fun\s*trend|pump\s*trend|pumpfun\s*hot)\b',
        r'\bpump\.?fun\b',
    ],
    Intent.PUMP_NEW: [
        r'\b(pump\.?fun\s*new|new\s*launch|pump\s*new|new\s*token|just\s*launch)\b',
    ],
    Intent.PUMP_TOP: [
        r'\b(pump\.?fun\s*top|top\s*mcap|pump\s*top|biggest\s*pump)\b',
    ],
    Intent.CRYPTO_DIPS: [
        r'\b(crypto\s*dip|dip\s*buy|buy\s*dip|token\s*dip|cheap\s*crypto|discount)\b',
    ],
    Intent.CRYPTO_PUMPS: [
        r'\b(crypto\s*pump|mooner|moon\s*shot|pump\s*token|biggest\s*gainer|top\s*gainer)\b',
    ],
    Intent.AI_CRYPTO_PICK: [
        r'\b(ai\s*crypto|ai\s*pick|best\s*crypto\s*pick|ai\s*recommend\s*crypto|crypto\s*ai)\b',
    ],
    Intent.WHALE_SCAN: [
        r'\b(whale|whales|big\s*buy|large\s*transaction|whale\s*alert|whale\s*scan|big\s*player)\b',
        r'\b(scan|check|find|show)\s*(for\s*)?(whale|whales|big\s*buyer)\b',
    ],
    Intent.RUG_CHECK: [
        r'\b(rug|rug\s*pull|scam|honeypot|safe\s*token|token\s*safe|rug\s*check|is\s*it\s*safe)\b',
    ],
    Intent.MULTI_CHAIN: [
        r'\b(multi\s*chain|cross\s*chain|base\s*chain|arbitrum|bnb\s*chain|ethereum\s*gem|all\s*chain)\b',
    ],
    Intent.PORTFOLIO: [
        r'\b(portfolio|my\s*holding|my\s*crypto|my\s*position|my\s*coin|my\s*token|pnl|profit\s*loss)\b',
    ],
    Intent.BUY_CRYPTO: [
        r'\b(buy\s*crypto|buy\s*token|add\s*position|enter\s*trade)\b',
        r'^/buy\b',
    ],
    Intent.SELL_CRYPTO: [
        r'\b(sell\s*crypto|sell\s*token|exit\s*position|close\s*trade|sell\s*my)\b',
        r'^/sell\b',
    ],
    Intent.TRADE_HISTORY: [
        r'\b(trade\s*history|past\s*trade|my\s*trade|transaction\s*history|trade\s*log)\b',
    ],
    Intent.PRICE_ALERT: [
        r'\b(price\s*alert|set\s*alert|alert\s*me|notify\s*(me\s*)?when|alert\s*price)\b',
    ],
    Intent.GEM_ACCURACY: [
        r'\b(gem\s*accuracy|prediction\s*accuracy|backtest|how\s*accurate|score\s*accuracy)\b',
    ],
    # 🆕 Buy/Sell Signal Intents
    Intent.BUY_SELL_STOCK: [
        r'\b(buy\s*sell|buy/sell|buy\.sell)\s*(signal|indicator|stock|nifty|sensex)\b',
        r'\b(stock|nifty|sensex)\s*(buy\s*sell|buy/sell|kharido|becho)\b',
        r'\b(kya\s*kharidu|kya\s*bechu|kharido\s*ya\s*becho)\b',
        r'\b(खरीदो|बेचो|खरीदूँ|बेचूँ|खरीदना|बेचना)\s*(stock|स्टॉक|nifty|निफ्टी|sensex|सेंसेक्स)\b',
        r'\b(stock|nifty|sensex)\s*(खरीदो|बेचो|खरीदूँ|बेचूँ)\b',
        r'\b(should\s*i\s*buy|should\s*i\s*sell)\s*(stock|nifty|sensex|market)\b',
    ],
    Intent.BUY_SELL_CRYPTO: [
        r'\b(buy\s*sell|buy/sell)\s*(crypto|bitcoin|btc|eth|sol|token)\b',
        r'\b(crypto|bitcoin|btc|eth|sol)\s*(buy\s*sell|buy/sell|kharido|becho|signal)\b',
        r'\b(खरीदो|बेचो|खरीदूँ|बेचूँ)\s*(crypto|क्रिप्टो|bitcoin|बिटकॉइन|eth|sol)\b',
        r'\b(crypto|क्रिप्टो)\s*(खरीदो|बेचो)\b',
    ],
    Intent.SCAN_NIFTY_SIGNALS: [
        r'\b(scan|scanner|screener)\s*(nifty|stock|buy\s*sell)\b',
        r'\bnifty\s*(scanner|screener|scan)\b',
        r'\b(top|best)\s*(buy|sell)\s*(stock|signal)\b',
        r'\b(स्टॉक\s*स्कैन|निफ्टी\s*स्कैन|स्कैनर)\b',
    ],
    Intent.SCAN_CRYPTO_SIGNALS: [
        r'\b(scan|scanner|screener)\s*(crypto|token)\s*(signal|buy\s*sell)\b',
        r'\bcrypto\s*(scanner|screener|scan)\s*(signal)?\b',
        r'\b(क्रिप्टो\s*स्कैन|टोकन\s*स्कैन)\b',
    ],
    Intent.INDEX_SIGNALS: [
        r'\b(index|indices)\s*(signal|buy\s*sell)\b',
        r'\b(nifty|sensex|banknifty)\s*index\s*(signal)?\b',
        r'\b(इंडेक्स\s*सिग्नल)\b',
    ],
    # 🆕 Global Market Intents
    Intent.GLOBAL_ANALYSIS: [
        r'\b(global\s*(market|analysis|candle|brain)|world\s*(market|candle|analysis)|worldwide)\b',
        r'\b(ग्लोबल|वर्ल्ड|दुनिया|विश्व)\s*(मार्केट|बाज़ार|एनालिसिस|कैंडल)\b',
        r'\b(super\s*computer\s*brain|global\s*brain)\b',
    ],
    Intent.US_MARKETS: [
        r'\b(us\s*market|america|nasdaq|s&p\s*500|dow\s*jones|wall\s*street|sp500)\b',
        r'\b(अमेरिका|नैस्डैक|डाउ\s*जोन्स|वॉल\s*स्ट्रीट)\b',
    ],
    Intent.EUROPE_MARKETS: [
        r'\b(europe|european|dax|ftse|cac|stoxx|london\s*market)\b',
        r'\b(यूरोप|यूरोपियन|लंदन\s*मार्केट)\b',
    ],
    Intent.ASIA_MARKETS: [
        r'\b(asia|asian|nikkei|hang\s*seng|shanghai|kospi|japan|china|korea)\s*(market)?\b',
        r'\b(एशिया|जापान|चीन|कोरिया)\s*(मार्केट)?\b',
    ],
    Intent.INDIA_PREDICTION: [
        r'\b(india\s*predict|india\s*impact|global\s*impact\s*india|how\s*will\s*india)\b',
        r'\b(भारत|इंडिया)\s*(प्रेडिक्शन|असर|इम्पैक्ट)\b',
        r'\b(global\s*se\s*india|duniya\s*ka\s*asar)\b',
    ],
    Intent.COMMODITIES: [
        r'\b(gold|silver|crude|oil|commodity|commodities|sona|chandi|tel)\b',
        r'\b(सोना|चांदी|तेल|क्रूड|कमोडिटी|dollar|डॉलर|rupee|रुपया)\b',
    ],
    # 🆕 Admin Intent
    Intent.ADMIN_PANEL: [
        r'\b(admin|panel|एडमिन|पैनल|control\s*panel|settings)\b',
        r'^/admin\b',
    ],
    # 🆕 Language Switch
    Intent.LANGUAGE_SWITCH: [
        r'\b(language|lang|hindi|english|भाषा|हिंदी|इंग्लिश|bhasha)\b',
        r'\b(switch\s*to|change\s*to|बदल|बदलो)\s*(hindi|english|हिंदी|इंग्लिश)\b',
    ],
    Intent.MORNING_BRIEF: [
        r'\b(morning\s*brief|daily\s*brief|market\s*brief|what\s*happened|overnight|brief\s*me|update\s*me|catch\s*me\s*up)\b',
        r'\b(give|show|get)\s*(me\s*)?(morning|daily|market)\s*brief\b',
        r'\bbrief(ing)?\b',
    ],
    Intent.MARKET_SUMMARY: [
        r'\b(market\s*summary|full\s*summary|everything|overall|complete\s*analysis|full\s*report)\b',
    ],
    Intent.HELP: [
        r'\b(help|what\s*can\s*you|features|commands|menu|how\s*to\s*use)\b',
    ],
    # 🆕 Phase 6 Power Intents
    Intent.MARKET_REGIME: [
        r'\b(market\s*regime|regime|bull\s*bear|market\s*phase|market\s*cycle|trending\s*market)\b',
        r'\b(मार्केट\s*रेजीम|बुल|बेयर|मार्केट\s*फेज|साइडवेज)\b',
        r'\b(is\s*market|market\s*kya\s*hai|market\s*aaj)\s*(bull|bear|sideways)\b',
    ],
    Intent.OPTIONS_ANALYSIS: [
        r'\b(option\s*analysis|option\s*greek|greek|delta|gamma|theta|vega|iv|implied\s*volatility)\b',
        r'\b(pcr|put\s*call\s*ratio|max\s*pain|option\s*strateg|straddle|strangle|iron\s*condor)\b',
        r'\b(ऑप्शन\s*एनालिसिस|ग्रीक|डेल्टा|गामा|थीटा|वेगा|पीसीआर)\b',
    ],
    Intent.SCALP_SIGNAL: [
        r'\b(scalp|scalping|intraday\s*scalp|quick\s*trade|1\s*min|5\s*min)\s*(signal|trade|entry)?\b',
        r'\b(स्कैल्प|स्कैल्पिंग|इंट्राडे)\s*(सिग्नल|ट्रेड)?\b',
    ],
    Intent.MULTI_TF_SIGNAL: [
        r'\b(multi\s*time\s*frame|multi\s*tf|mtf|all\s*timeframe|timeframe\s*analysis|combined\s*tf)\b',
        r'\b(मल्टी\s*टाइमफ्रेम|सारे\s*टाइमफ्रेम)\b',
    ],
    Intent.STOCK_PORTFOLIO: [
        r'\b(stock\s*portfolio|my\s*stock|my\s*share|stock\s*holding)\b',
        r'\b(स्टॉक\s*पोर्टफोलियो|मेरे\s*शेयर)\b',
    ],
    Intent.TAX_CALCULATOR: [
        r'\b(income\s*tax|tax\s*calculat|stcg|ltcg|tds|capital\s*gain\s*tax|crypto\s*tax\s*calculat|stock\s*tax\s*calculat)\b',
        r'\b(tax)\b.*\b(calculat|file|return|save|deduct|exempt|slab)\b',
        r'\b(टैक्स\s*कैलकुलेट|आयकर\s*गणना|कैपिटल\s*गेन\s*टैक्स)\b',
    ],
    Intent.COMBINED_PORTFOLIO: [
        r'\b(combined\s*portfolio|total\s*portfolio|all\s*portfolio|full\s*portfolio|overall\s*portfolio)\b',
        r'\b(पूरा\s*पोर्टफोलियो|कुल\s*पोर्टफोलियो)\b',
    ],
    # 🚀 Rocket Scanner — Quick Profit / Moonshot
    Intent.ROCKET_SCAN: [
        r'\b(rocket|moonshot|25x|50x|100x|1000x|moon\s*shot)\b',
        r'\b(₹?\s*\d+[kK]?\s*(se|to|invest|lagake|lagakar|lagakr)\s*₹?\s*\d+)\b',
        r'\b(paisa|paise|rupee|rupaye|rupe)\s*(double|triple|bana|kamao|multiply)\b',
        r'\b(jaldi|quick|fast|turant|abhi|fata\s*fat|fatafat)\s*(paisa|profit|earn|kamao|kamana|bana)\b',
        r'\b(rocket\s*scan|rocket|moonshot|launch\s*pad)\b',
        r'\b(पंप|रॉकेट|मूनशॉट|पैसा\s*दोगुना|पैसा\s*बनाओ|जल्दी\s*कमाओ)\b',
    ],
    Intent.QUICK_PROFIT: [
        r'\b(\d+)\s*(rupee|rupaye|rupe|₹|rs).*?(\d+)\s*(rupee|rupaye|rupe|₹|rs|lakh|lac|lak|crore|cr)\b',
        r'\b(5000|2000|10000|1000)\s*(se|to|invest|laga).*?(50000|100000|1\s*lakh|2\s*lakh|1\s*crore)\b',
        r'\b(invest|laga).*?\b(bana|ban|kama|profit|return)\b.*?\b(minute|min|hour|ghante|mint)\b',
        r'\b(pump\s*wale|pump\s*token|new\s*pump|naye\s*pump|trending\s*pump)\b',
        r'\b(jis\s*pe|jin\s*pe|jisme|jinme).*?(paisa|profit|return|kamao|kamana|bana)\b',
        r'\b(token|coin)\s*(ka\s*naam|batao|bata|recommend|suggest|dikhao)\b.*?(jaldi|quick|abhi|turant|fast)\b',
        r'\b(पैसा|रुपए|रुपये).*?(बना|कमा|डबल|ट्रिपल).*?(मिनट|घंटे)\b',
        r'\b(पंप\s*वाले|नये\s*पंप|ट्रेंडिंग)\s*(टोकन|कॉइन)\b',
        r'\b(टोकन|कॉइन)\s*(का\s*नाम|बताओ|बता|दिखाओ)\b',
    ],
    # 🆕 CoinDCX Web3 Intents
    Intent.COINDCX_SIGNAL: [
        r'\b(coindcx|coin\s*dcx)\s*(signal|ai|predict|analysis|buy\s*sell)\b',
        r'\b(signal|predict|analysis)\s*(coindcx|coin\s*dcx)\b',
        r'\b(coindcx|coin\s*dcx)\b.*\b(signal|predict|buy|sell)\b',
        r'\b(कॉइनडीसीएक्स|coindcx)\s*(सिग्नल|प्रेडिक्शन|एनालिसिस)\b',
    ],
    Intent.COINDCX_MOVERS: [
        r'\b(coindcx|coin\s*dcx)\s*(top|gainer|loser|mover|pump|dump)\b',
        r'\b(top|gainer|loser|mover)\s*(coindcx|coin\s*dcx)\b',
        r'\b(coindcx|coin\s*dcx)\s*(कौन|टॉप|गेनर|लूजर)\b',
    ],
    Intent.COINDCX_BEST: [
        r'\b(coindcx|coin\s*dcx)\s*(best|scan|screen|find)\b',
        r'\b(best|scan)\s*(coindcx|coin\s*dcx)\s*(signal)?\b',
    ],
    Intent.COINDCX_PRICE: [
        r'\b(coindcx|coin\s*dcx)\s*(price|rate|keemat|कीमत)\b',
        r'\b(price|rate)\s*(on|in|at)?\s*(coindcx|coin\s*dcx)\b',
        r'\b(coindcx|coin\s*dcx)\s*pe\s*(price|rate)\b',
    ],
    # 🌐 All Web3 Token Intents
    Intent.WEB3_ALL: [
        r'\b(all|sab|saare|sabhi|सभी|सारे)\s*(web3|crypto|token)\b',
        r'\bweb3\s*(token|summary|count|total|kitne)\b',
        r'\b(total|kitne)\s*(token|crypto|web3)\b',
    ],
    Intent.WEB3_LIST: [
        r'\bweb3\s*(list|suchi|लिस्ट)\b',
        r'\b(token|crypto)\s*(list|all\s*list)\b',
    ],
    Intent.WEB3_MOVERS: [
        r'\bweb3\s*(mover|gainer|loser|pump|dump|top)\b',
        r'\b(web3|all\s*token)\s*(gainer|loser)\b',
    ],
    Intent.WEB3_SCAN: [
        r'\bweb3\s*(scan|signal|ai\s*scan)\b',
        r'\b(scan|signal)\s*(all|web3|sab)\s*(token|crypto)?\b',
    ],
    Intent.WEB3_DEFI: [
        r'\b(defi|डीफाई)\s*(token|coin|list)?\b',
        r'\bweb3\s*defi\b',
    ],
    Intent.WEB3_MEME: [
        r'\b(meme|मीम)\s*(coin|token|list)?\b',
        r'\bweb3\s*meme\b',
    ],
    Intent.WEB3_AI: [
        r'\b(ai\s*token|ai\s*coin|web3\s*ai)\b',
        r'\b(artificial\s*intelligence|एआई)\s*(token|coin)\b',
    ],
    Intent.WEB3_L1: [
        r'\b(layer\s*1|l1|लेयर\s*1)\s*(token|coin|list)?\b',
        r'\bweb3\s*(l1|layer\s*1)\b',
    ],
    Intent.WEB3_L2: [
        r'\b(layer\s*2|l2|लेयर\s*2)\s*(token|coin|list)?\b',
        r'\bweb3\s*(l2|layer\s*2)\b',
    ],
    Intent.WEB3_GAMING: [
        r'\b(gaming|nft|गेमिंग)\s*(token|coin|list)?\b',
        r'\bweb3\s*(gaming|nft|game)\b',
    ],
    Intent.WEB3_INFRA: [
        r'\b(infra|infrastructure|इंफ्रा)\s*(token|coin|list)?\b',
        r'\bweb3\s*infra\b',
    ],
    Intent.WEB3_SEARCH: [
        r'\bweb3\s*(search|find|dhundho|खोजो)\b',
        r'\b(search|find|dhundho)\s*(web3|token|coin)\b',
    ],
}


def classify_intent(text: str) -> Tuple[str, float]:
    """
    Classify user message into an intent using pattern matching + keyword scoring.
    Returns (intent, confidence).
    
    SMART DISAMBIGUATION:
    - When crypto/token keywords present → prefer crypto intents over tax/stock
    - When "rupee + bana/kamao + minute/hour" → QUICK_PROFIT (rocket scanner)
    - When "pump wale token" → QUICK_PROFIT (not pump.fun trending)
    """
    text_lower = text.lower().strip()
    
    # ── PRIORITY CHECKS: Common voice patterns that get misclassified ──
    # "₹5000 lagakar ₹50000 banana" or "paisa double karo 15 minute mein"
    _quick_profit_patterns = [
        r'\d+\s*(rupee|rupaye|rupe|₹|rs).*?(bana|kama|double|triple|profit)',
        r'(invest|laga).*?(bana|kama|profit).*?(minute|min|hour|ghante)',
        r'(pump\s*wale|pump\s*token|new\s*pump|नई\s*पंप|naye\s*pump)',
        r'(jaldi|quick|fast|turant|abhi|fatafat)\s*(paisa|profit|earn|kamao|bana)',
        r'(token|coin)\s*(ka\s*naam|batao|bata|recommend|suggest).*?(jaldi|quick|abhi)',
        r'\d+.*?(rupee|rupaye|₹).*?lagak(ar|r|e).*?\d+',
        r'(पंप\s*वाले|टोकन\s*का\s*नाम\s*बताओ|पैसा\s*बनाओ|पैसा\s*कमाओ)',
        r'(moon|rocket|100x|50x|25x|10x)',
    ]
    for p in _quick_profit_patterns:
        try:
            if re.search(p, text_lower):
                return Intent.QUICK_PROFIT, 0.95
        except:
            pass
    
    # Check each intent pattern
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches) * 10
            except re.error:
                pass
        if score > 0:
            scores[intent] = score
    
    if not scores:
        # Check if it looks like a question or conversation
        if any(w in text_lower for w in ['?', 'should', 'which', 'what', 'how', 'when', 'why', 'can', 'will', 'tell', 'explain']):
            return Intent.CHAT, 0.6
        return Intent.CHAT, 0.4
    
    # ── SMART DISAMBIGUATION: Resolve conflicting intents ──
    best_intent = max(scores, key=scores.get)
    
    # Crypto vs Tax disambiguation
    crypto_signals = any(w in text_lower for w in [
        'crypto', 'token', 'coin', 'pump', 'dex', 'solana', 'sol', 'eth', 'btc',
        'bitcoin', 'meme', 'gem', 'altcoin', 'web3', 'defi', 'nft',
        'क्रिप्टो', 'टोकन', 'कॉइन', 'पंप', 'बिटकॉइन',
        'invest', 'laga', 'paisa', 'rupee', 'bana', 'kamao',
    ])
    
    if best_intent == Intent.TAX_CALCULATOR and crypto_signals:
        # If user mentions crypto concepts, probably NOT asking about tax
        # Check if there's a crypto intent with decent score
        crypto_intents = [
            Intent.CRYPTO_GEMS, Intent.BUY_SELL_CRYPTO, Intent.QUICK_PROFIT,
            Intent.ROCKET_SCAN, Intent.AI_CRYPTO_PICK, Intent.CRYPTO_TRENDING,
            Intent.PUMP_TRENDING, Intent.PUMP_NEW,
        ]
        for ci in crypto_intents:
            if ci in scores:
                best_intent = ci
                break
        else:
            # Default to QUICK_PROFIT if mentions money + crypto
            if any(w in text_lower for w in ['rupee', 'rupaye', '₹', 'rs', 'laga', 'invest', 'paisa', 'रुपए', 'रुपय']):
                best_intent = Intent.QUICK_PROFIT
                scores[Intent.QUICK_PROFIT] = 30
    
    # "30 percent" can match tax BUT if crypto context → not tax
    if best_intent == Intent.TAX_CALCULATOR:
        if '30' in text_lower and 'percent' in text_lower and crypto_signals:
            best_intent = Intent.BUY_SELL_CRYPTO if Intent.BUY_SELL_CRYPTO in scores else Intent.CHAT
    
    max_score = scores[best_intent]
    confidence = min(1.0, max_score / 20)  # Normalize
    
    return best_intent, confidence


# ═══════════════════════════════════════════════════════════
#  CONTEXT BUILDER — Injects live stock + crypto data
# ═══════════════════════════════════════════════════════════

def build_jarvis_context(chat_id: int = 0) -> str:
    """Build comprehensive market context for JARVIS — both stock AND crypto."""
    sections = []
    
    # ── STOCK MARKET CONTEXT ──
    sections.append("═══ 📊 INDIAN STOCK MARKET ═══")
    try:
        from live_index_engine import get_live_price, analyze_2min_candle
        
        for symbol, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
            try:
                live = get_live_price(symbol)
                if isinstance(live, dict) and "error" not in live:
                    sections.append(
                        f"{name}: ₹{live['price']:,.2f} | "
                        f"Change: {live['change']:+,.2f} ({live['change_pct']:+.2f}%) | "
                        f"Day Range: ₹{live['low']:,.2f} - ₹{live['high']:,.2f}"
                    )
            except Exception:
                pass
        
        for symbol, name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                analysis = analyze_2min_candle(symbol, name)
                signal = analysis.get("signal", "HOLD")
                conf = analysis.get("confidence", 0)
                sections.append(f"{name} Signal: {signal} ({conf:.0%} confidence)")
            except Exception:
                pass
    except Exception:
        sections.append("[Stock data loading...]")
    
    # ML Predictions
    try:
        from ml_predictor import predict_index_direction
        for symbol, name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                pred = predict_index_direction(symbol, name)
                if "error" not in pred:
                    sections.append(
                        f"{name} ML: {pred['direction']} | "
                        f"Confidence: {pred['confidence']:.0%} | UP prob: {pred['prob_up']:.0%}"
                    )
            except Exception:
                pass
    except Exception:
        pass
    
    # ── CRYPTO MARKET CONTEXT ──
    sections.append("\n═══ 🪙 CRYPTO MARKET ═══")
    try:
        from crypto_engine import get_usd_inr_rate, scan_pump_trending
        
        rates = get_usd_inr_rate()
        if rates:
            sections.append(f"Exchange Rates: 1 USD = ₹{rates.get('usd_inr', 0):,.2f} | 1 SOL = ₹{rates.get('sol_inr', 0):,.2f}")
        
        trending = scan_pump_trending(limit=3)
        if trending:
            for t in trending[:3]:
                name = t.get('name', '?')
                symbol = t.get('symbol', '?')
                mcap = t.get('market_cap_inr', 0)
                change = t.get('price_change_1h', 0)
                sections.append(f"🔥 {name} ({symbol}): MCap ₹{mcap:,.0f} | 1h: {change:+.1f}%")
    except Exception:
        sections.append("[Crypto data loading...]")
    
    # ── USER PORTFOLIO CONTEXT ──
    if chat_id:
        try:
            from portfolio_tracker import get_portfolio, calculate_portfolio_pnl
            portfolio = get_portfolio(chat_id)
            if portfolio:
                pnl = calculate_portfolio_pnl(chat_id)
                total_invested = sum(p.get('total_cost', 0) for p in portfolio)
                total_pnl = pnl.get('total_pnl', 0) if pnl else 0
                sections.append(f"\n═══ 📂 YOUR PORTFOLIO ═══")
                sections.append(f"Holdings: {len(portfolio)} tokens | Invested: ₹{total_invested:,.0f} | P&L: ₹{total_pnl:+,.0f}")
        except Exception:
            pass
    
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


# ═══════════════════════════════════════════════════════════
#  JARVIS RESPONSE FORMATTER
# ═══════════════════════════════════════════════════════════

def jarvis_format(text: str, intent: str = None) -> str:
    """Format response with JARVIS branding."""
    if intent in (Intent.STOCK_SIGNAL, Intent.STOCK_PREDICT, Intent.STOCK_OPTIONS, 
                  Intent.INVESTMENT_CALC, Intent.SUPER_PREDICT, Intent.TWO_MIN_SIGNAL):
        header = "🤖📊 *J.A.R.V.I.S. — स्टॉक एनालिसिस*"
    elif intent in (Intent.CRYPTO_GEMS, Intent.CRYPTO_TRENDING, Intent.PUMP_TRENDING,
                    Intent.PUMP_NEW, Intent.PUMP_TOP, Intent.CRYPTO_DIPS, Intent.CRYPTO_PUMPS,
                    Intent.AI_CRYPTO_PICK, Intent.MULTI_CHAIN):
        header = "🤖🪙 *J.A.R.V.I.S. — क्रिप्टो इंटेलिजेंस*"
    elif intent in (Intent.WHALE_SCAN, Intent.RUG_CHECK):
        header = "🤖🛡️ *J.A.R.V.I.S. — सिक्योरिटी स्कैन*"
    elif intent in (Intent.PORTFOLIO, Intent.BUY_CRYPTO, Intent.SELL_CRYPTO, Intent.TRADE_HISTORY):
        header = "🤖💼 *J.A.R.V.I.S. — पोर्टफोलियो मैनेजर*"
    elif intent == Intent.MORNING_BRIEF:
        header = "🤖☀️ *J.A.R.V.I.S. — मॉर्निंग ब्रीफ*"
    elif intent in (Intent.BUY_SELL_STOCK, Intent.BUY_SELL_CRYPTO, Intent.SCAN_NIFTY_SIGNALS,
                    Intent.SCAN_CRYPTO_SIGNALS, Intent.INDEX_SIGNALS):
        header = "🤖🟢🔴 *J.A.R.V.I.S. — Buy/Sell सिग्नल*"
    elif intent in (Intent.GLOBAL_ANALYSIS, Intent.US_MARKETS, Intent.EUROPE_MARKETS,
                    Intent.ASIA_MARKETS, Intent.INDIA_PREDICTION, Intent.COMMODITIES):
        header = "🤖🌍 *J.A.R.V.I.S. — ग्लोबल ब्रेन*"
    elif intent == Intent.ADMIN_PANEL:
        header = "🤖🔐 *J.A.R.V.I.S. — एडमिन पैनल*"
    else:
        header = "🤖✨ *J.A.R.V.I.S.*"
    
    return f"{header}\n{'━' * 30}\n\n{text}"


# ═══════════════════════════════════════════════════════════
#  MORNING BRIEFING — Proactive Market Intelligence
# ═══════════════════════════════════════════════════════════

def generate_morning_briefing(chat_id: int = 0) -> str:
    """Generate a comprehensive morning market briefing like JARVIS would deliver."""
    now = datetime.now(IST)
    
    brief = []
    brief.append(f"🌸 *{_get_time_greeting_hi()}!* ✨")
    brief.append(f"📅 *{now.strftime('%A, %d %B %Y')}* — ये रहा आपका मॉर्निंग ब्रीफ: 💕\n")
    
    # Stock Market
    brief.append("📊 *INDIAN STOCK MARKET:*")
    brief.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        from live_index_engine import get_live_price
        from ml_predictor import predict_index_direction
        
        for symbol, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
            try:
                live = get_live_price(symbol)
                if isinstance(live, dict) and "error" not in live:
                    emoji = "📈" if live.get('change', 0) >= 0 else "📉"
                    brief.append(
                        f"{emoji} *{name}:* ₹{live['price']:,.2f} "
                        f"({live['change_pct']:+.2f}%)"
                    )
            except Exception:
                pass
        
        brief.append("")
        for symbol, name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                pred = predict_index_direction(symbol, name)
                if "error" not in pred:
                    direction = pred.get('direction', 'NEUTRAL')
                    conf = pred.get('confidence', 0)
                    emoji = "🟢" if direction in ("BULLISH", "UP") else "🔴" if direction in ("BEARISH", "DOWN") else "🟡"
                    brief.append(f"{emoji} *{name} ML Forecast:* {direction} ({conf:.0%})")
            except Exception:
                pass
    except Exception:
        brief.append("📊 Stock data loading...")
    
    # Crypto Market
    brief.append(f"\n🪙 *CRYPTO MARKET:*")
    brief.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        from crypto_engine import scan_pump_trending, get_usd_inr_rate
        
        rates = get_usd_inr_rate()
        if rates:
            brief.append(f"💱 SOL: ₹{rates.get('sol_inr', 0):,.0f} | BTC: ${rates.get('btc_usd', 0):,.0f}")
        
        trending = scan_pump_trending(limit=5)
        if trending:
            brief.append("\n🔥 *Top pump.fun Tokens:*")
            for i, t in enumerate(trending[:5], 1):
                name = t.get('symbol', '?')
                mcap = t.get('market_cap_inr', 0)
                change = t.get('price_change_1h', 0)
                emoji = "🟢" if change > 0 else "🔴"
                brief.append(f"  {i}. {emoji} {name} — MCap ₹{mcap:,.0f} ({change:+.1f}%)")
    except Exception:
        brief.append("🪙 Crypto data loading...")
    
    # Sentiment
    try:
        from sentiment_engine import calculate_fear_greed_index
        fg = calculate_fear_greed_index()
        if fg and 'value' in fg:
            val = fg['value']
            label = fg.get('label', 'Neutral')
            bar = "🟢" * (val // 20) + "⚪" * (5 - val // 20)
            brief.append(f"\n🎭 *Market Mood:* {label} [{bar}] {val}/100")
    except Exception:
        pass
    
    # Portfolio check
    if chat_id:
        try:
            from portfolio_tracker import get_portfolio, calculate_portfolio_pnl
            portfolio = get_portfolio(chat_id)
            if portfolio:
                pnl = calculate_portfolio_pnl(chat_id)
                total_pnl = pnl.get('total_pnl', 0) if pnl else 0
                emoji = "📈" if total_pnl >= 0 else "📉"
                brief.append(f"\n💼 *Your Portfolio:* {len(portfolio)} holdings | P&L: {emoji} ₹{total_pnl:+,.0f}")
        except Exception:
            pass
    
    brief.append(f"\n{'━' * 30}")
    brief.append("💡 *किसी भी चीज़ का detailed analysis चाहिए तो बोलिए!* 🌸")
    brief.append("मैं हूँ ना — सब समझती हूँ! ✨")
    brief.append("\n⚠️ ये सिर्फ एनालिसिस है। हमेशा स्टॉप लॉस लगाएं।")
    
    return jarvis_format("\n".join(brief), Intent.MORNING_BRIEF)


def _get_time_greeting() -> str:
    """Get appropriate time-based greeting."""
    hour = datetime.now(IST).hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"

def _get_time_greeting_hi() -> str:
    """Get Hindi time greeting."""
    hour = datetime.now(IST).hour
    if hour < 12:
        return "शुभ प्रभात"
    elif hour < 17:
        return "शुभ दोपहर"
    else:
        return "शुभ संध्या"


# ═══════════════════════════════════════════════════════════
#  MARKET SUMMARY — Complete Analysis
# ═══════════════════════════════════════════════════════════

def generate_market_summary(chat_id: int = 0) -> str:
    """Generate a complete market summary across all modules."""
    summary = []
    summary.append("ये रहा आपका complete market intelligence report: 🌸\n")
    
    # Stock Section
    summary.append("📊 *━━━ STOCK MARKET ━━━*")
    try:
        from live_index_engine import get_live_price, analyze_2min_candle
        from ml_predictor import predict_index_direction
        
        for symbol, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
            try:
                live = get_live_price(symbol)
                if isinstance(live, dict) and "error" not in live:
                    pred = predict_index_direction(symbol, name.replace(" 50", ""))
                    sig = analyze_2min_candle(symbol, name.replace(" 50", ""))
                    
                    direction = pred.get('direction', 'N/A') if isinstance(pred, dict) and 'error' not in pred else 'N/A'
                    signal = sig.get('signal', 'N/A') if isinstance(sig, dict) else 'N/A'
                    
                    emoji = "📈" if live.get('change', 0) >= 0 else "📉"
                    summary.append(
                        f"\n{emoji} *{name}:* ₹{live['price']:,.2f} ({live['change_pct']:+.2f}%)\n"
                        f"   🤖 ML: {direction} | ⚡ Signal: {signal}"
                    )
            except Exception:
                pass
    except Exception:
        summary.append("Loading stock data...")
    
    # Crypto Section
    summary.append(f"\n🪙 *━━━ CRYPTO MARKET ━━━*")
    try:
        from crypto_engine import scan_pump_trending, scan_trending_gems, get_usd_inr_rate
        
        rates = get_usd_inr_rate()
        if rates:
            summary.append(f"💱 1 SOL = ₹{rates.get('sol_inr', 0):,.0f} | 1 USD = ₹{rates.get('usd_inr', 0):,.0f}")
        
        gems = scan_trending_gems(limit=3)
        if gems:
            summary.append("\n💎 *Top Gems:*")
            for g in gems[:3]:
                name = g.get('name', '?')
                score = g.get('gem_score', 0)
                mcap = g.get('market_cap_inr', 0)
                summary.append(f"  • {name} — Score: {score}/100 | MCap: ₹{mcap:,.0f}")
    except Exception:
        summary.append("Loading crypto data...")
    
    # Risk & Sentiment
    try:
        from sentiment_engine import calculate_fear_greed_index
        fg = calculate_fear_greed_index()
        if fg:
            summary.append(f"\n🎭 *Market Sentiment:* {fg.get('label', 'N/A')} ({fg.get('value', 0)}/100)")
    except Exception:
        pass
    
    summary.append(f"\n{'━' * 30}")
    summary.append("🤖 _मैं 24/7 सारे मार्केट मॉनिटर कर रही हूँ। चिंता मत कीजिए! 💕_")
    summary.append("⚠️ ये सिर्फ एनालिसिस है। हमेशा स्टॉप लॉस लगाइए।")
    
    return jarvis_format("\n".join(summary), Intent.MARKET_SUMMARY)


# ═══════════════════════════════════════════════════════════
#  INTENT → ACTION MAPPER  
# ═══════════════════════════════════════════════════════════

# Maps intents to button text that handle_update already handles
INTENT_TO_BUTTON = {
    Intent.STOCK_SIGNAL: "🔱 NIFTY Signals 📊",
    Intent.STOCK_PREDICT: "🤖 NIFTY ML Predict 🧠",
    Intent.STOCK_OPTIONS: "💎 NIFTY Calls OTM 🚀",
    Intent.INVESTMENT_CALC: "💰 Invest ₹2K NIFTY",
    Intent.CANDLE_PATTERN: "🕯️ Candle Patterns 📊",
    Intent.MARKET_TREND: "🌍 Market Trend 📈",
    Intent.MARKET_STATUS: "⏰ Market Status 🔔",
    Intent.SUPER_PREDICT: "🧠 Super Prediction 🔮",
    Intent.SENTIMENT: "📰 Market Sentiment 💬",
    Intent.RISK_CALC: "⚠️ Risk Calculator 🛡️",
    Intent.TWO_MIN_SIGNAL: "⚡ 2-Min NIFTY Signal",
    Intent.TOMORROW_PREDICT: "🔮 Tomorrow Prediction 🎯",
    Intent.CRYPTO_GEMS: "🪙 Crypto Gems 💎",
    Intent.CRYPTO_TRENDING: "🔥 Trending Crypto 📈",
    Intent.PUMP_TRENDING: "🟣 Pump.fun Trending 🔥",
    Intent.PUMP_NEW: "🆕 Pump.fun New Launches",
    Intent.PUMP_TOP: "🏆 Pump.fun Top MCap",
    Intent.CRYPTO_DIPS: "📉 Crypto Dips 🔴",
    Intent.CRYPTO_PUMPS: "🚀 Crypto Pumps 🟢",
    Intent.AI_CRYPTO_PICK: "🤖 AI Crypto Pick 🧠",
    Intent.WHALE_SCAN: "🐋 Whale Scanner 🔍",
    Intent.RUG_CHECK: "🛡️ Rug Detector 🔎",
    Intent.MULTI_CHAIN: "🌐 Multi-Chain Gems 🔗",
    Intent.PORTFOLIO: "📂 My Crypto Portfolio",
    Intent.TRADE_HISTORY: "📜 Trade History",
    Intent.PRICE_ALERT: "🔔 Price Alerts 📊",
    Intent.GEM_ACCURACY: "📊 Gem Accuracy 🔬",
    # 🆕 Buy/Sell
    Intent.BUY_SELL_STOCK: "🟢🔴 Stock Buy/Sell Signal",
    Intent.BUY_SELL_CRYPTO: "🟢🔴 Crypto Buy/Sell Signal",
    Intent.SCAN_NIFTY_SIGNALS: "📊 Scan NIFTY Signals",
    Intent.SCAN_CRYPTO_SIGNALS: "📊 Scan Crypto Signals",
    Intent.INDEX_SIGNALS: "📊 Index Buy/Sell",
    # 🆕 Global
    Intent.GLOBAL_ANALYSIS: "🌍 Global Market Brain",
    Intent.US_MARKETS: "🇺🇸 US Markets",
    Intent.EUROPE_MARKETS: "🇪🇺 Europe Markets",
    Intent.ASIA_MARKETS: "🌏 Asia Markets",
    Intent.INDIA_PREDICTION: "🔮 India from Global",
    Intent.COMMODITIES: "🥇 Commodities",
    # 🆕 Admin
    Intent.ADMIN_PANEL: "🔐 Admin Panel",
    # 🆕 Language
    Intent.LANGUAGE_SWITCH: "🇮🇳 Hindi / English",
    # 🆕 Phase 6 Power
    Intent.MARKET_REGIME: "🌡️ Market Regime 🔬",
    Intent.OPTIONS_ANALYSIS: "📊 Options Analysis 💹",
    Intent.SCALP_SIGNAL: "⚡ Scalp Signal 🎯",
    Intent.MULTI_TF_SIGNAL: "📊 Multi-TF Signal 🔄",
    Intent.STOCK_PORTFOLIO: "📈 My Stock Portfolio",
    Intent.TAX_CALCULATOR: "🧾 Tax Calculator 💰",
    Intent.COMBINED_PORTFOLIO: "🏦 Combined Portfolio",
    # 🆕 CoinDCX Web3
    Intent.COINDCX_SIGNAL: "💹 CoinDCX AI Signal 🤖",
    Intent.COINDCX_MOVERS: "📊 CoinDCX Top Movers",
    Intent.COINDCX_BEST: "🔍 CoinDCX Best Signals",
    Intent.COINDCX_PRICE: "💰 CoinDCX Price Check",
    # 🚀 Rocket Scanner
    Intent.ROCKET_SCAN: "🚀🔥 ROCKET Scanner",
    Intent.QUICK_PROFIT: "🚀🔥 ROCKET Scanner",
    # 🌐 All Web3 Tokens
    Intent.WEB3_ALL: "🌐 All Web3 Tokens",
    Intent.WEB3_LIST: "📋 Web3 Token List",
    Intent.WEB3_MOVERS: "🚀💥 Web3 Top Movers",
    Intent.WEB3_SCAN: "🔍 Web3 AI Scan All",
    Intent.WEB3_DEFI: "🏦 Web3 DeFi Tokens",
    Intent.WEB3_MEME: "🐸 Web3 Meme Coins",
    Intent.WEB3_AI: "🤖 Web3 AI Tokens",
    Intent.WEB3_L1: "🔷 Web3 Layer 1",
    Intent.WEB3_L2: "🔶 Web3 Layer 2",
    Intent.WEB3_GAMING: "🎮 Web3 Gaming NFT",
    Intent.WEB3_INFRA: "🔧 Web3 Infra Tokens",
    Intent.WEB3_SEARCH: "🌐 All Web3 Tokens",
}


def get_action_for_intent(intent: str, confidence: float, user_message: str) -> Dict[str, Any]:
    """
    Determine what action JARVIS should take based on classified intent.
    
    Returns dict with:
    - action: "redirect" (send to existing handler), "generate" (AI response), "special" (custom)
    - button: button text to simulate (for redirect)
    - response: direct response text (for generate/special)
    """
    # High confidence intents → redirect to existing handlers
    if intent in INTENT_TO_BUTTON and confidence >= 0.5:
        return {
            "action": "redirect",
            "button": INTENT_TO_BUTTON[intent],
            "intent": intent,
        }
    
    # Special handlers
    if intent == Intent.MORNING_BRIEF:
        return {"action": "special", "type": "morning_brief", "intent": intent}
    
    if intent == Intent.MARKET_SUMMARY:
        return {"action": "special", "type": "market_summary", "intent": intent}
    
    if intent == Intent.HELP:
        return {"action": "redirect", "button": "❓ Help 💡", "intent": intent}
    
    if intent == Intent.GREETING:
        return {"action": "special", "type": "greeting", "intent": intent}
    
    # Buy/Sell crypto need special parsing
    if intent == Intent.BUY_CRYPTO:
        return {"action": "special", "type": "buy_crypto", "intent": intent, "message": user_message}
    
    if intent == Intent.SELL_CRYPTO:
        return {"action": "special", "type": "sell_crypto", "intent": intent, "message": user_message}
    
    # 🆕 Crypto Intelligence — redirect AI Crypto Pick to super engine
    if intent == Intent.AI_CRYPTO_PICK and confidence >= 0.4:
        return {"action": "redirect", "button": "🤖 AI Crypto Pick 🧠", "intent": intent}
    
    # 🆕 Buy/Sell signals (stock + crypto) → special NLU handler  
    if intent in (Intent.BUY_SELL_STOCK, Intent.BUY_SELL_CRYPTO) and confidence >= 0.4:
        return {"action": "special", "type": "buy_sell_signal", "intent": intent, "message": user_message}
    
    # 🆕 Admin panel
    if intent == Intent.ADMIN_PANEL:
        return {"action": "special", "type": "admin_panel", "intent": intent}
    
    # 🆕 Language switch
    if intent == Intent.LANGUAGE_SWITCH:
        return {"action": "special", "type": "language_switch", "intent": intent, "message": user_message}
    
    # Default: AI chat with JARVIS persona
    return {"action": "generate", "intent": intent}


# ═══════════════════════════════════════════════════════════
#  JARVIS GREETING — Personalized, intelligent
# ═══════════════════════════════════════════════════════════

def generate_jarvis_greeting(user_name: str = "Sir", chat_id: int = 0) -> str:
    """Generate a personalized JARVIS greeting with market context — Hindi style."""
    now = datetime.now(IST)
    time_greet = _get_time_greeting()
    
    # Hindi time greetings
    hindi_greet = {"morning": "सुप्रभात", "afternoon": "शुभ दोपहर", "evening": "शुभ संध्या"}
    hi_greet = hindi_greet.get(time_greet, "नमस्ते")
    
    greeting_parts = []
    greeting_parts.append(f"🌸 *नमस्ते {user_name} जी!* 🙏✨")
    greeting_parts.append(f"{hi_greet}! मैं *J.A.R.V.I.S.* — आपकी AI ट्रेडिंग असिस्टेंट हूँ। 💕\n")
    
    # Quick market snapshot
    try:
        from live_index_engine import get_live_price
        
        nifty = get_live_price("^NSEI")
        if isinstance(nifty, dict) and "error" not in nifty:
            emoji = "📈" if nifty.get('change', 0) >= 0 else "📉"
            greeting_parts.append(
                f"{emoji} NIFTY: ₹{nifty['price']:,.2f} ({nifty['change_pct']:+.2f}%)"
            )
    except Exception:
        pass
    
    try:
        from crypto_engine import get_usd_inr_rate
        rates = get_usd_inr_rate()
        if rates:
            greeting_parts.append(f"💱 SOL: ₹{rates.get('sol_inr', 0):,.0f}")
    except Exception:
        pass
    
    greeting_parts.append(f"\n💡 _बताइए, आज मैं आपकी क्या मदद करूँ?_ 🌸")
    greeting_parts.append("बस बोलिए — मैं सब समझती हूँ! ✨")
    
    return jarvis_format("\n".join(greeting_parts), Intent.GREETING)


# ═══════════════════════════════════════════════════════════
#  JARVIS WELCOME SCREEN — Epic /start message
# ═══════════════════════════════════════════════════════════

def generate_jarvis_welcome(user_name: str = "Sir") -> str:
    """Generate the epic JARVIS welcome screen for /start — Hindi style."""
    now = datetime.now(IST)
    
    welcome = f"""🌸✨ *नमस्ते {user_name.upper()} जी!* ✨🌸
✦═══════════════════════════✦

🤖💕 *J.A.R.V.I.S.* 💕🤖
*Just A Rather Very Intelligent System*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 *भारत की सबसे पावरफुल AI Trading Assistant* 🌟
_6 AI/ML Models + Real-Time Market Intelligence से लैस_ 🌸

🧠 *━━━ AI इंटेलिजेंस ━━━*
┣ 🤖 6-Model ML Ensemble (XGB+RF+GB+ET+LGBM+LSTM)
┣ 🔮 111-Feature Technical Analysis Engine
┣ 🕯️ 40+ Japanese Candlestick Patterns
┣ 📰 Real-Time Sentiment & Fear/Greed Index
┣ 💬 Multi-Provider AI Chat (GPT + Gemini + Llama)
┣ 🧮 Kelly Criterion Risk Management
┗ 🇮🇳 हिंदी + English (Bilingual Brain)

📊 *━━━ स्टॉक मार्केट ━━━*
┣ ⚡ Live NIFTY/SENSEX सिग्नल & ऑप्शन
┣ 🟢🔴 BUY/SELL इंडिकेटर (12 टेक्निकल)
┣ 🎯 OTM Call/Put Picks with Profit Calc
┣ 💰 इन्वेस्टमेंट कैलकुलेटर (₹2K to ₹50K+)
┣ ⚡ 2-Min स्कैल्पिंग सिग्नल
┣ 🔮 AI प्रेडिक्शन (Tomorrow)
┗ 📊 NIFTY 50 Stock Scanner

🪙 *━━━ क्रिप्टो मार्केट ━━━*
┣ 🟣 pump.fun — Trending/New/Top Tokens
┣ 💎 DexScreener Gem Scanner (Score 0-100)
┣ 🟢🔴 Crypto BUY/SELL सिग्नल
┣ 🌐 Multi-Chain: SOL + ETH + Base + ARB + BNB
┣ 🐋 Whale Activity Detection
┣ 🛡️ 8-Factor Rug Pull Detector
┣ 📂 Portfolio Tracker with Live P&L
┗ 🔔 Custom Price Alerts

🌍 *━━━ ग्लोबल मार्केट ब्रेन ━━━*
┣ 🇺🇸 US (S&P 500, NASDAQ, DOW)
┣ 🇪🇺 Europe (DAX, FTSE, CAC)
┣ 🌏 Asia (Nikkei, Hang Seng, Shanghai)
┣ 🥇 Commodities (Gold, Silver, Crude)
┣ 💱 USD/INR & Dollar Index
┗ 🔮 India Impact Prediction

⚡ *━━━ ऑटोमेशन ━━━*
┣ 🔔 24/7 ऑटो अलर्ट (Stock + Crypto)
┣ 🚨 BUY/SELL ऑटो अलर्ट
┣ 📲 SMS Alerts
┣ ☀️ मॉर्निंग मार्केट ब्रीफिंग
┣ 🔐 एडमिन पैनल (सब कुछ ON/OFF)
┗ 🤖 Natural Language — बस बोलो!

★═══════════════════════════★
⏰ {now.strftime('%I:%M %p IST | %d %b %Y')}
_"सारे सिस्टम्स तैयार हैं। मैं हूँ ना आपके साथ! 💕"_ 🤖
🌸 *राधे राधे — TRADE WITH CONFIDENCE* 🌸
✦═══════════════════════════✦"""
    
    return welcome


# ═══════════════════════════════════════════════════════════
#  JARVIS HELP SCREEN — Organized by category
# ═══════════════════════════════════════════════════════════

def generate_jarvis_help(user_name: str = "Sir") -> str:
    """Generate comprehensive JARVIS help screen — Hindi style."""
    return f"""🤖 *J.A.R.V.I.S. कमांड सेंटर* 🤖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *{user_name} जी, मैं हिंदी और इंग्लिश दोनों समझती हूँ!* 🌸
बस बोलिए क्या चाहिए — मैं समझ जाऊँगी। 💕

🗣️ *ऐसे बात करो:*
• _"NIFTY आज कैसा है?"_
• _"Call खरीदूँ या Put?"_
• _"कोई अच्छा crypto gem बताओ"_
• _"ये token safe है?"_
• _"मेरी portfolio कैसी है?"_
• _"Whale activity दिखाओ"_
• _"Morning briefing दो"_
• _"NIFTY का buy/sell signal बताओ"_
• _"Global market कैसा है?"_

📊 *स्टॉक कमांड:*
┣ 🔱 Signals — NIFTY/SENSEX एनालिसिस
┣ 🟢🔴 Buy/Sell — 12 इंडिकेटर सिग्नल
┣ 💎 OTM Options — Call/Put picks
┣ 💰 Investment — ₹2K/₹20K ट्रेड प्लान
┣ 🤖 ML Predict — 6-model ensemble
┣ ⚡ 2-Min सिग्नल — Scalping alerts
┣ 🧠 Super Prediction — पूरा AI combined
┣ 🕯️ Candle Patterns — 40+ patterns
┣ 📰 Sentiment — न्यूज़ मूड
┣ ⚠️ Risk Calculator — पोज़ीशन साइज़िंग
┗ 🔮 Tomorrow — AI forecast

🪙 *क्रिप्टो कमांड:*
┣ 🟣 pump.fun — Trending/New/Top
┣ 💎 Gems — DexScreener scanner
┣ 🟢🔴 Crypto Buy/Sell — सिग्नल
┣ 🌐 Multi-Chain — 5 blockchains
┣ 📉 Dips/Pumps — Buy opportunities
┣ 🐋 Whale Scanner — Big money moves
┣ 🛡️ Rug Detector — Safety check
┣ 📂 Portfolio — Track holdings
┣ /buy TOKEN QTY PRICE — पोज़ीशन ऐड
┣ /sell TOKEN QTY PRICE — पोज़ीशन क्लोज़
┗ /alert TOKEN PRICE — अलर्ट सेट

🌍 *ग्लोबल मार्केट:*
┣ 🇺🇸 US Markets — NASDAQ, S&P, DOW
┣ 🇪🇺 Europe — DAX, FTSE
┣ 🌏 Asia — Nikkei, Hang Seng
┣ 🥇 Commodities — Gold, Silver, Crude
┣ 💱 USD/INR
┗ 🔮 India Impact — ग्लोबल से भारत

🔐 *एडमिन (सिर्फ Admin):*
┣ /admin — एडमिन पैनल
┣ फीचर ON/OFF — सब कंट्रोल
┣ 📢 Broadcast — सबको मैसेज
┗ 👥 Users — यूज़र मैनेज

🇮🇳 *भाषा:*
┣ "Hindi" — हिंदी में बात करो
┗ "English" — Switch to English

★═══════════════════════════★
🤖 _"मैं हमेशा सीखती रहती हूँ। बस पूछिए! 🌸"_
⚠️ ये सिर्फ एनालिसिस है। हमेशा स्टॉप लॉस लगाइए।"""


# ═══════════════════════════════════════════════════════════
#  JARVIS KEYBOARD — Organized, Stunning UI
# ═══════════════════════════════════════════════════════════

def build_jarvis_keyboard() -> dict:
    """Build the JARVIS-style organized keyboard with categories — Hindi + all features."""
    rows = [
        # JARVIS AI Row
        ["🤖 Ask JARVIS 💬", "☀️ Morning Brief 📊"],

        # 🟢🔴 Buy/Sell Signals
        ["🟢🔴 ━━ BUY/SELL सिग्नल ━━ 🟢🔴"],
        ["🟢🔴 Stock Buy/Sell Signal", "🟢🔴 Crypto Buy/Sell Signal"],
        ["📊 Scan NIFTY Signals", "📊 Scan Crypto Signals"],
        ["📊 Index Buy/Sell"],
        ["⚡ Scalp Signal 🎯", "📊 Multi-TF Signal 🔄"],

        # Stock Market - Analysis
        ["📊 ━━ स्टॉक मार्केट ━━ 📊"],
        ["🔱 NIFTY Signals 📊", "🔱 SENSEX Signals 📊"],
        ["💎 NIFTY Calls OTM 🚀", "💎 SENSEX Calls OTM 🚀"],
        ["⚡ NIFTY Puts OTM 📉", "⚡ SENSEX Puts OTM 📉"],
        ["🤖 NIFTY ML Predict 🧠", "🤖 SENSEX ML Predict 🧠"],
        ["⚡ 2-Min NIFTY Signal", "⚡ 2-Min SENSEX Signal"],
        ["🇮🇳⚡ NIFTY Call/Put AI", "📊 SENSEX Call/Put AI"],
        ["🏦 BankNIFTY Call/Put AI", "📅 Market Holidays 🇮🇳"],
        ["🔮 NIFTY Power Predict 💪", "🔮 SENSEX Power Predict 💪"],
        ["📊 NIFTY OTM↔ATM 🎯", "📊 SENSEX OTM↔ATM 🎯"],
        ["📊 BankNIFTY OTM↔ATM 🎯", "⚡ 2-Min Momentum 🚀"],
        ["💰 Invest ₹2K NIFTY", "💰 Invest ₹2K SENSEX"],
        ["💸 Invest ₹20K NIFTY", "💸 Invest ₹20K SENSEX"],
        ["📈🇮🇳 Indian Stock AI 🧠", "🧠 Super Prediction 🔮"],
        ["📰 Market Sentiment 💬", "⚠️ Risk Calculator 🛡️"],
        ["🕯️ Candle Patterns 📊", "🌍 Market Trend 📈"],
        ["⏰ Market Status 🔔", "📊 Live Snapshot 🔴"],
        ["🔮 Tomorrow Prediction 🎯"],

        # 🇮🇳 NIFTY SUPER BRAIN — Advanced Indian Market Intelligence
        ["🇮🇳 ━━ NIFTY SUPER BRAIN ━━ 🧠"],
        ["🇮🇳 NIFTY Super Dashboard 🧠"],
        ["🏛️ FII/DII Flow 📊", "😱 India VIX Gauge 📊"],
        ["📊 NIFTY PCR 🔢", "📊 BankNIFTY PCR 🔢"],
        ["📐 NIFTY Pivot Levels 📊", "📐 SENSEX Pivot Levels"],
        ["🌅 GIFT NIFTY Gap 📊", "📊 OI Buildup Analysis"],
        ["🏭 Sector Heatmap 📊"],

        # 💰 BUDGET OPTIONS HUNTER + POSITION GUARDIAN
        ["💰 ━━ BUDGET OPTIONS ₹4-8 ━━ 🎯"],
        ["💰 Budget Options 🎯", "💰 BankNIFTY Budget 🎯"],
        ["🔔 9AM Auto Picks 🌅", "🛡️ My Positions Guard"],
        ["🛑 STOP All Crypto 🛑", "🟢 START Crypto Alerts"],


        # 🌡️ Advanced Market Intelligence
        ["🌡️ ━━ मार्केट इंटेलिजेंस ━━ 🌡️"],
        ["🌡️ Market Regime 🔬", "📊 Options Analysis 💹"],
        ["🧾 Tax Calculator 💰"],

        # Crypto Market
        ["🪙 ━━ क्रिप्टो मार्केट ━━ 🪙"],
        ["🟣 Pump.fun Trending 🔥", "🆕 Pump.fun New Launches"],
        ["🏆 Pump.fun Top MCap", "🪙 All Gems (Pump+Dex)"],
        ["🪙 Crypto Gems 💎", "🔥 Trending Crypto 📈"],
        ["📉 Crypto Dips 🔴", "🚀 Crypto Pumps 🟢"],
        ["🤖 AI Crypto Pick 🧠", "🌐 Multi-Chain Gems 🔗"],
        ["🔥 Crypto Deep Analysis 🪙"],

        # 🔥 DexTools Engine — Multi-Chain Intelligence
        ["🔥 ━━ DEXTOOLS ENGINE ━━ 🔥"],
        ["🔥 DexTools Top 15", "🐸 Meme Board"],
        ["🆕 Live New Pairs", "🎁 DexTools Airdrops"],
        ["🧠 AI Signal Report", "📊 Multi-Chain Scan"],

        # 🚀 Rocket Scanner — Moonshot Hunter
        ["🚀 ━━ ROCKET SCANNER ━━ 🚀"],
        ["🚀🔥 ROCKET Scanner", "🔥 Fast Rockets"],
        ["🚀 CoinDCX Rockets", "🟣 Pump.fun Rockets"],

        # 🔥 TOP 100 + Wealth Strategy
        ["💰 ━━ TOP 100 AI + WEALTH ━━ 💰"],
        ["🔥 TOP 100 AI Signals 🧠", "💰 ₹2K → ₹2L Strategy 🚀"],

        # Crypto Tools
        ["🛡️ ━━ क्रिप्टो टूल्स ━━ 🛡️"],
        ["🐋 Whale Scanner 🔍", "🛡️ Rug Detector 🔎"],
        ["📂 My Crypto Portfolio", "📈 My Stock Portfolio"],
        ["📜 Trade History", "🏦 Combined Portfolio"],
        ["🔔 Price Alerts 📊", "📊 Gem Accuracy 🔬"],
        ["💰 Buy Crypto /buy", "🔔 Crypto Alerts ON/OFF"],

        # 🪙 CoinDCX Web3
        ["💹 ━━ CoinDCX Web3 AI ━━ 💹"],
        ["💹 CoinDCX AI Signal 🤖", "📊 CoinDCX Top Movers"],
        ["🔍 CoinDCX Best Signals", "💰 CoinDCX Price Check"],

        # 🌐 All Web3 Tokens
        ["🌐 ━━ ALL Web3 Tokens ━━ 🌐"],
        ["🌐 All Web3 Tokens", "📋 Web3 Token List"],
        ["💰 ₹2K Token Invest", "🚀💥 Web3 Top Movers"],
        ["🔍 Web3 AI Scan All", "🔷 Web3 Layer 1"],
        ["🔶 Web3 Layer 2", "🏦 Web3 DeFi Tokens"],
        ["🐸 Web3 Meme Coins", "🤖 Web3 AI Tokens"],
        ["🎮 Web3 Gaming NFT", "🔧 Web3 Infra Tokens"],
        ["🔍 Scan DeFi Signals", "🔍 Scan Meme Signals"],

        # 👻 Phantom Wallet — Solana (ALL buttons)
        ["👻 ━━ PHANTOM WALLET ━━ 👻"],
        ["👻 Phantom Wallet 🔮", "👻 Connect Wallet"],
        ["👻 Wallet Scan 📊", "👻 Wallet Dashboard 📋"],
        ["👻 Wallet Summary ⚡", "👻 Claim Airdrops 🎁"],
        ["👻 Transfer SOL 💸", "👻 Wallet Alerts ON"],
        ["👻 Wallet Alerts OFF", "👻 Disconnect Wallet"],

        # 🎁 Airdrop Hunter
        ["🎁 ━━ AIRDROP HUNTER ━━ 🎁"],
        ["💎 Telegram Wallet 💳", "🎁 Airdrop Hunter 🚀"],
        ["📝 Set My Wallet 🔑", "👛 My Wallets 💰"],
        ["🔮 Upcoming Airdrops", "🎁 Solana Airdrops"],

        # 🔗 QR Wallet Connect
        ["🔗 ━━ QR WALLET CONNECT ━━ 🔗"],
        ["🔗 Trust Wallet QR 📱", "◎ Solana Pay QR"],

        # 🌍 Global Markets
        ["🌍 ━━ ग्लोबल मार्केट ━━ 🌍"],
        ["🌍 Global Market Brain", "🔮 India from Global"],
        ["🇺🇸 US Markets", "🇪🇺 Europe Markets"],
        ["🌏 Asia Markets", "🥇 Commodities"],

        # 🧠⚡ JARVIS Super Brain
        ["🧠 ━━ SUPER BRAIN ━━ ⚡"],
        ["📰 News Digest", "🧠 Intelligence Briefing"],
        ["🔱 SPOC Dashboard", "📊 Quick Status"],

        # 🛠️ JARVIS Tools
        ["🛠️ ━━ JARVIS TOOLS ━━ 🛠️"],
        ["🌤️ Weather", "🔍 Web Search"],
        ["🎵 Identify Song 🎶", "🎨 Generate Image"],
        ["🧠 My Memory", "📰 Crypto News"],

        # � JARVIS Coder + AI Assistant
        ["💻 ━━ JARVIS CODER ━━ 🚀"],
        ["💻 JARVIS Coder 🚀", "👤 My Profile"],

        # 👑 Admin / Boss Section
        ["👑 ━━ ADMIN / BOSS ━━ 👑"],
        ["👑 Admin Dashboard", "🔐 Admin Panel"],

        # 🛡️ Security Center
        ["🛡️ ━━ SECURITY CENTER ━━ 🛡️"],
        ["🛡️ Security Dashboard", "🔐 Security Status"],

        # AI & Alerts
        ["🤖 ━━ AI & अलर्ट ━━ 🤖"],
        ["🤖 AI Chat 💬", "🧹 Clear AI Chat"],
        ["📲 SMS Alerts ON 🔔", "📲 SMS Alerts OFF 🔕"],
        ["💵 Set Investment Amount", "📊 My Positions"],

        # Language & Settings
        ["🔐 ━━ सेटिंग्स ━━ 🔐"],
        ["🇮🇳 Hindi / English"],

        # Watchlist & Account
        ["📋 ━━ अकाउंट ━━ 📋"],
        ["➕ Add Symbol 🎯", "➖ Remove Symbol ❌", "📋 Watchlist"],
        ["🔔 Subscribe Alerts ✅", "🔕 Unsubscribe ❌", "👥 My Subs"],
        ["📱 Generate QR 🔗", "❓ Help 💡", "🏠 /start"],
    ]
    return {"keyboard": rows, "resize_keyboard": True}


# ═══════════════════════════════════════════════════════════
#  PROACTIVE ALERTS — Smart Notifications
# ═══════════════════════════════════════════════════════════

def check_proactive_alerts(chat_id: int) -> List[str]:
    """Check for conditions that warrant proactive JARVIS alerts."""
    alerts = []
    
    # Check portfolio risk
    try:
        from portfolio_tracker import get_portfolio, calculate_portfolio_pnl
        portfolio = get_portfolio(chat_id)
        if portfolio:
            pnl = calculate_portfolio_pnl(chat_id)
            if pnl:
                total_pnl_pct = pnl.get('total_pnl_pct', 0)
                if total_pnl_pct <= -15:
                    alerts.append(
                        "🚨 *JARVIS ALERT:* Portfolio "
                        f"{total_pnl_pct:.1f}% नीचे है! Please positions review कीजिए। 🌸"
                    )
                elif total_pnl_pct >= 50:
                    alerts.append(
                        "💰 *JARVIS ALERT:* Portfolio "
                        f"{total_pnl_pct:.1f}% ऊपर है! Partial profit book करें? 🌸"
                    )
    except Exception:
        pass
    
    return alerts


# ═══════════════════════════════════════════════════════════
#  EXPORT — Module API
# ═══════════════════════════════════════════════════════════

__all__ = [
    'JARVIS_SYSTEM_PROMPT',
    'Intent',
    'classify_intent',
    'build_jarvis_context',
    'jarvis_format',
    'generate_morning_briefing',
    'generate_market_summary',
    'get_action_for_intent',
    'generate_jarvis_greeting',
    'generate_jarvis_welcome',
    'generate_jarvis_help',
    'build_jarvis_keyboard',
    'check_proactive_alerts',
    # Memory system
    'remember_user',
    'recall_user',
    'remember_name',
    'get_user_context',
    'add_to_conversation',
]
