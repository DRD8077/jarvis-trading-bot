"""
🧠 J.A.R.V.I.S. GENIUS ENGINE — Autonomous Super-Intelligence Layer
════════════════════════════════════════════════════════════════════════
The BRAIN UPGRADE that makes JARVIS think, reason, plan, and act autonomously.

Features:
- 🧠 Chain-of-Thought Reasoning — thinks step-by-step before answering
- 🔧 Tool Calling — JARVIS can USE its own functions (get price, analyze, scan, etc.)
- 🎯 Smart Intent Classification — LLM-powered when regex fails
- 💾 Semantic Memory — remembers conversations with meaning, not just text
- 🔄 Self-Reflection — checks its own answers for accuracy
- 📊 Multi-Step Planning — breaks complex requests into sub-tasks
- 🌐 Context Fusion — combines ALL data sources intelligently
- 🎓 Learning System — improves from user feedback
- 🗣️ Conversation State Machine — tracks multi-turn dialog flows
- ⚡ Parallel Analysis — runs multiple analyses simultaneously

Author: JARVIS AI Core Team
"""

import os
import re
import json
import time
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Callable
from collections import defaultdict
from functools import lru_cache

import pytz

logger = logging.getLogger("jarvis_genius")
IST = pytz.timezone('Asia/Kolkata')

# ═══════════════════════════════════════════════════════════
#  TOOL REGISTRY — Functions JARVIS can call autonomously
# ═══════════════════════════════════════════════════════════

_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: dict = None):
    """Decorator to register a function as a JARVIS tool."""
    def decorator(func):
        _TOOL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "parameters": parameters or {},
            "name": name,
        }
        return func
    return decorator


def get_tool_definitions() -> List[dict]:
    """Get tool definitions in OpenAI/Claude function-calling format."""
    tools = []
    for name, info in _TOOL_REGISTRY.items():
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            }
        })
    return tools


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a registered tool and return result as string."""
    if name not in _TOOL_REGISTRY:
        return f"Error: Tool '{name}' not found"
    try:
        result = _TOOL_REGISTRY[name]["function"](**arguments)
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False, default=str)
        return str(result)
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return f"Error executing {name}: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  REGISTER ALL JARVIS TOOLS (lazy — imported on first call)
# ═══════════════════════════════════════════════════════════

@register_tool(
    "get_stock_price",
    "Get live price of Indian stock index (NIFTY/SENSEX) with change, high, low",
    {"type": "object", "properties": {"symbol": {"type": "string", "description": "Stock symbol like ^NSEI for NIFTY, ^BSESN for SENSEX"}}, "required": ["symbol"]}
)
def tool_get_stock_price(symbol: str) -> dict:
    from live_index_engine import get_live_price
    return get_live_price(symbol)


@register_tool(
    "get_stock_prediction",
    "Get ML prediction for stock direction (UP/DOWN) with confidence using 6-model ensemble",
    {"type": "object", "properties": {"symbol": {"type": "string"}, "name": {"type": "string"}}, "required": ["symbol", "name"]}
)
def tool_get_stock_prediction(symbol: str, name: str) -> dict:
    from ml_predictor import predict_index_direction
    return predict_index_direction(symbol, name)


@register_tool(
    "analyze_2min_candle",
    "Analyze latest 2-minute candle for BUY/SELL signal with confidence",
    {"type": "object", "properties": {"symbol": {"type": "string"}, "name": {"type": "string"}}, "required": ["symbol", "name"]}
)
def tool_analyze_2min(symbol: str, name: str) -> dict:
    from live_index_engine import analyze_2min_candle
    return analyze_2min_candle(symbol, name)


@register_tool(
    "get_crypto_trending",
    "Get trending crypto tokens from CoinDCX with price changes",
    {"type": "object", "properties": {}, "required": []}
)
def tool_crypto_trending() -> str:
    try:
        from coindcx_engine import get_trending_tokens
        tokens = get_trending_tokens()
        if tokens:
            return json.dumps(tokens[:10], default=str)
    except Exception:
        pass
    return "Trending data unavailable"


@register_tool(
    "analyze_crypto_token",
    "Deep analysis of a crypto token — technical indicators, rug risk, price targets",
    {"type": "object", "properties": {"symbol": {"type": "string", "description": "Token symbol like BTC, ETH, SOL"}}, "required": ["symbol"]}
)
def tool_analyze_crypto(symbol: str) -> str:
    try:
        from jarvis_market_brain import analyze_crypto_token_deep
        result = analyze_crypto_token_deep(symbol)
        if result:
            # Return key data without the full formatted report
            return json.dumps({
                "symbol": symbol,
                "verdict": result.get("verdict", "N/A"),
                "score": result.get("score", 0),
                "price": result.get("price", 0),
                "rsi": result.get("rsi", 0),
                "trend": result.get("trend", "N/A"),
                "rug_risk": result.get("rug_risk", "N/A"),
                "targets": result.get("targets", {}),
            }, default=str)
    except Exception as e:
        return f"Analysis failed: {e}"


@register_tool(
    "get_market_sentiment",
    "Get market sentiment analysis — bullish/bearish score from news",
    {"type": "object", "properties": {}, "required": []}
)
def tool_market_sentiment() -> str:
    try:
        from sentiment_engine import analyze_all_sentiment
        return json.dumps(analyze_all_sentiment(), default=str)
    except Exception:
        return "Sentiment data unavailable"


@register_tool(
    "get_news",
    "Get latest market news headlines from multiple sources",
    {"type": "object", "properties": {"topic": {"type": "string", "description": "Topic like 'nifty', 'crypto', 'bitcoin', 'market'"}}, "required": []}
)
def tool_get_news(topic: str = "market") -> str:
    try:
        from jarvis_super_brain import fetch_all_news
        news = fetch_all_news()
        if news:
            # Filter by topic if specified
            relevant = [n for n in news if topic.lower() in n.get("title", "").lower() or topic.lower() in n.get("category", "").lower()]
            if not relevant:
                relevant = news[:10]
            return json.dumps([{"title": n["title"], "source": n.get("source", ""), "category": n.get("category", "")} for n in relevant[:10]], ensure_ascii=False)
    except Exception:
        pass
    return "News unavailable"


@register_tool(
    "calculate_option_strategy",
    "Calculate best option strategy for given budget in INR",
    {"type": "object", "properties": {"budget": {"type": "number", "description": "Budget in INR"}, "direction": {"type": "string", "description": "UP or DOWN"}}, "required": ["budget"]}
)
def tool_option_strategy(budget: float, direction: str = "UP") -> str:
    try:
        from live_index_engine import calculate_investment_options
        return json.dumps(calculate_investment_options(budget), default=str)
    except Exception as e:
        return f"Calculation failed: {e}"


@register_tool(
    "scan_crypto_gems",
    "Scan for high-potential crypto gems with ML scoring",
    {"type": "object", "properties": {"limit": {"type": "integer", "description": "Number of gems to return"}}, "required": []}
)
def tool_scan_gems(limit: int = 5) -> str:
    try:
        from crypto_intelligence import get_top_crypto_picks
        picks = get_top_crypto_picks(limit=limit)
        return json.dumps(picks, default=str) if picks else "No gems found"
    except Exception:
        return "Gem scanning unavailable"


@register_tool(
    "check_rug_risk",
    "Check if a crypto token is a potential rug pull",
    {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}
)
def tool_rug_check(symbol: str) -> str:
    try:
        from jarvis_ultra_ai import assess_rug_risk
        risk = assess_rug_risk(symbol)
        return json.dumps(risk, default=str)
    except Exception:
        return "Rug check unavailable"


@register_tool(
    "get_portfolio",
    "Get user's crypto portfolio with P&L",
    {"type": "object", "properties": {"chat_id": {"type": "integer"}}, "required": ["chat_id"]}
)
def tool_get_portfolio(chat_id: int) -> str:
    try:
        from portfolio_tracker import get_portfolio_summary
        return json.dumps(get_portfolio_summary(chat_id), default=str)
    except Exception:
        return "Portfolio unavailable"


@register_tool(
    "get_fear_greed_index",
    "Get current Fear & Greed index for Indian market",
    {"type": "object", "properties": {}, "required": []}
)
def tool_fear_greed() -> str:
    try:
        from sentiment_engine import calculate_fear_greed_index
        return json.dumps(calculate_fear_greed_index(), default=str)
    except Exception:
        return "Fear/Greed index unavailable"


@register_tool(
    "search_web",
    "Search the web for latest information on any topic",
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
)
def tool_search_web(query: str) -> str:
    """Simple web search using DuckDuckGo instant answers."""
    try:
        import requests
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            results = []
            if data.get("Abstract"):
                results.append(data["Abstract"])
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(topic["Text"])
            return "\n".join(results) if results else "No results found"
    except Exception:
        pass
    return "Search unavailable"


@register_tool(
    "execute_python",
    "Execute a Python expression for calculations (math, conversions, etc.)",
    {"type": "object", "properties": {"expression": {"type": "string", "description": "Python expression to evaluate"}}, "required": ["expression"]}
)
def tool_python_calc(expression: str) -> str:
    """Safe Python expression evaluator for calculations."""
    # Whitelist safe operations
    allowed = set("0123456789+-*/().,%_ abcdefghijklmnopqrstuvwxyz")
    if not all(c in allowed for c in expression.lower()):
        return "Expression contains unsafe characters"
    try:
        import math
        safe_dict = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "int": int, "float": float,
            "pow": pow, "sqrt": math.sqrt, "log": math.log,
            "pi": math.pi, "e": math.e,
        }
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


# ═══════════════════════════════════════════════════════════
#  NEW L3 TOOLS — Code Engine + NSE Option Chain
# ═══════════════════════════════════════════════════════════

@register_tool(
    "run_code_autonomous",
    "Generate and execute code autonomously. JARVIS writes code from description, runs it, returns output. Use for coding requests, web scraping, data analysis, file processing, etc.",
    {"type": "object", "properties": {"prompt": {"type": "string", "description": "What to code — in English or Hindi"}}, "required": ["prompt"]}
)
def tool_run_code(prompt: str) -> str:
    """Run code autonomously via JARVIS Code Engine."""
    try:
        from jarvis_code_engine import execute_code_autonomous, format_execution_result
        result = execute_code_autonomous(prompt)
        return format_execution_result(result, prompt[:60])
    except Exception as e:
        return f"Code engine error: {e}"


@register_tool(
    "get_nse_option_chain",
    "Get REAL-TIME NSE option chain with live prices, OI, IV, Greeks for NIFTY/SENSEX/BANKNIFTY. Returns real option prices from NSE India.",
    {"type": "object", "properties": {"symbol": {"type": "string", "description": "NIFTY or SENSEX or BANKNIFTY"}}, "required": ["symbol"]}
)
def tool_nse_chain(symbol: str = "NIFTY") -> str:
    """Get real NSE option chain."""
    try:
        from nse_live_engine import get_atm_otm_analysis, format_atm_otm_analysis
        analysis = get_atm_otm_analysis(symbol, budget=2000, direction="auto", num_strikes=5)
        if "error" not in analysis:
            return format_atm_otm_analysis(analysis, "CE")
        return f"Option chain error: {analysis.get('error', 'unavailable')}"
    except Exception as e:
        return f"NSE engine error: {e}"


@register_tool(
    "get_live_spot_price",
    "Get REAL-TIME spot price for NIFTY, SENSEX, or BANKNIFTY directly from NSE",
    {"type": "object", "properties": {"symbol": {"type": "string", "description": "Index name: NIFTY, SENSEX, BANKNIFTY"}}, "required": ["symbol"]}
)
def tool_live_spot(symbol: str = "NIFTY") -> str:
    """Get real-time spot price from NSE."""
    try:
        from nse_live_engine import get_live_spot
        data = get_live_spot(symbol)
        if data.get("price", 0) > 0:
            return f"{symbol}: ₹{data['price']:,.2f} (change: {data.get('change', 0):+,.2f}, {data.get('change_pct', 0):+.2f}%) Source: {data.get('source', '')}"
        return f"{symbol} price unavailable"
    except Exception as e:
        return f"Spot price error: {e}"


# ═══════════════════════════════════════════════════════════
#  SEMANTIC MEMORY — Vector-like memory with meaning
# ═══════════════════════════════════════════════════════════

SEMANTIC_MEMORY_FILE = "jarvis_semantic_memory.json"


class SemanticMemory:
    """Long-term memory that stores conversation context with semantic tags."""
    
    def __init__(self):
        self._memories: Dict[str, List[dict]] = {}  # chat_id -> memories
        self._insights: Dict[str, List[str]] = {}   # chat_id -> learned insights
        self._user_profiles: Dict[str, dict] = {}   # chat_id -> rich profile
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(SEMANTIC_MEMORY_FILE):
                with open(SEMANTIC_MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    self._memories = data.get("memories", {})
                    self._insights = data.get("insights", {})
                    self._user_profiles = data.get("profiles", {})
        except Exception as e:
            logger.error(f"Memory load error: {e}")
    
    def _save(self):
        try:
            with open(SEMANTIC_MEMORY_FILE, 'w') as f:
                json.dump({
                    "memories": self._memories,
                    "insights": self._insights,
                    "profiles": self._user_profiles,
                }, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Memory save error: {e}")
    
    def store_interaction(self, chat_id: int, user_msg: str, bot_response: str, 
                         intent: str = "", sentiment: str = "neutral", entities: list = None):
        """Store a conversation with rich metadata."""
        cid = str(chat_id)
        if cid not in self._memories:
            self._memories[cid] = []
        
        memory = {
            "timestamp": datetime.now(IST).isoformat(),
            "user_message": user_msg[:500],
            "bot_response": bot_response[:500],
            "intent": intent,
            "sentiment": sentiment,
            "entities": entities or [],
            "tags": self._extract_tags(user_msg),
        }
        
        self._memories[cid].append(memory)
        
        # Keep last 200 memories per user
        if len(self._memories[cid]) > 200:
            self._memories[cid] = self._memories[cid][-200:]
        
        # Update user profile
        self._update_profile(cid, user_msg, intent, entities)
        
        # Auto-save every 10 interactions
        total = sum(len(v) for v in self._memories.values())
        if total % 10 == 0:
            self._save()
    
    def _extract_tags(self, text: str) -> list:
        """Extract semantic tags from text."""
        tags = []
        text_l = text.lower()
        
        tag_patterns = {
            "stock": r'\b(nifty|sensex|stock|share|option|nse|bse)\b',
            "crypto": r'\b(crypto|bitcoin|btc|eth|sol|token|coin|defi|web3)\b',
            "buy": r'\b(buy|kharido|lelo|entry|long)\b',
            "sell": r'\b(sell|becho|exit|short|book\s*profit)\b',
            "prediction": r'\b(predict|kal|tomorrow|future|direction)\b',
            "portfolio": r'\b(portfolio|holding|position|invest)\b',
            "news": r'\b(news|khabar|headlines|event)\b',
            "analysis": r'\b(analy|technic|fundament|chart|pattern)\b',
            "risk": r'\b(risk|loss|stop.?loss|danger|rug)\b',
            "profit": r'\b(profit|gain|target|return|earning)\b',
            "code": r'\b(code|python|javascript|program|function|api|bug|error)\b',
            "help": r'\b(help|madad|kaise|how|tutorial|guide)\b',
        }
        
        for tag, pattern in tag_patterns.items():
            if re.search(pattern, text_l):
                tags.append(tag)
        
        return tags
    
    def _update_profile(self, cid: str, text: str, intent: str, entities: list = None):
        """Build rich user profile from interactions."""
        if cid not in self._user_profiles:
            self._user_profiles[cid] = {
                "first_seen": datetime.now(IST).isoformat(),
                "interaction_count": 0,
                "preferred_language": "hindi",
                "interests": {},
                "trading_style": "unknown",
                "risk_appetite": "unknown",
                "favorite_assets": [],
                "expertise_level": "beginner",
                "active_hours": {},
            }
        
        profile = self._user_profiles[cid]
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        profile["last_seen"] = datetime.now(IST).isoformat()
        
        # Track interests
        tags = self._extract_tags(text)
        for tag in tags:
            profile["interests"][tag] = profile["interests"].get(tag, 0) + 1
        
        # Detect language preference
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        if hindi_chars > 5:
            profile["preferred_language"] = "hindi"
        elif len(text) > 20 and hindi_chars == 0:
            profile["preferred_language"] = "english"
        
        # Detect expertise level from interactions
        count = profile["interaction_count"]
        if count > 100:
            profile["expertise_level"] = "advanced"
        elif count > 30:
            profile["expertise_level"] = "intermediate"
        
        # Track active hours
        hour = str(datetime.now(IST).hour)
        profile["active_hours"][hour] = profile["active_hours"].get(hour, 0) + 1
        
        # Track favorite assets from entities
        if entities:
            for entity in entities:
                if entity not in profile["favorite_assets"]:
                    profile["favorite_assets"].append(entity)
            profile["favorite_assets"] = profile["favorite_assets"][-20:]
    
    def recall_relevant(self, chat_id: int, query: str, limit: int = 5) -> list:
        """Find relevant past memories using tag matching."""
        cid = str(chat_id)
        if cid not in self._memories:
            return []
        
        query_tags = set(self._extract_tags(query))
        if not query_tags:
            # Return most recent
            return self._memories[cid][-limit:]
        
        scored = []
        for mem in self._memories[cid]:
            mem_tags = set(mem.get("tags", []))
            overlap = len(query_tags & mem_tags)
            if overlap > 0:
                scored.append((overlap, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]
    
    def get_user_profile(self, chat_id: int) -> dict:
        """Get rich user profile."""
        return self._user_profiles.get(str(chat_id), {})
    
    def add_insight(self, chat_id: int, insight: str):
        """Store a learned insight about the user."""
        cid = str(chat_id)
        if cid not in self._insights:
            self._insights[cid] = []
        self._insights[cid].append(insight)
        if len(self._insights[cid]) > 50:
            self._insights[cid] = self._insights[cid][-50:]
    
    def get_insights(self, chat_id: int) -> list:
        """Get learned insights about user."""
        return self._insights.get(str(chat_id), [])


# Global semantic memory instance
semantic_memory = SemanticMemory()


# ═══════════════════════════════════════════════════════════
#  CONVERSATION STATE MACHINE — Multi-turn Dialog Tracking
# ═══════════════════════════════════════════════════════════

class ConversationState:
    """Tracks multi-turn conversation flows."""
    
    IDLE = "idle"
    AWAITING_SYMBOL = "awaiting_symbol"
    AWAITING_BUDGET = "awaiting_budget"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    IN_ANALYSIS = "in_analysis"
    IN_COMPARISON = "in_comparison"
    FOLLOW_UP = "follow_up"
    
    def __init__(self):
        self._states: Dict[int, dict] = {}
    
    def get_state(self, chat_id: int) -> dict:
        if chat_id not in self._states:
            self._states[chat_id] = {
                "state": self.IDLE,
                "context": {},
                "last_topic": None,
                "last_asset": None,
                "last_intent": None,
                "pending_action": None,
                "turn_count": 0,
                "timestamp": time.time(),
            }
        return self._states[chat_id]
    
    def update(self, chat_id: int, **kwargs):
        state = self.get_state(chat_id)
        state.update(kwargs)
        state["timestamp"] = time.time()
        state["turn_count"] += 1
    
    def resolve_reference(self, chat_id: int, text: str) -> str:
        """Resolve pronouns and references using conversation state.
        
        E.g., "uska price kya hai?" → "BTC ka price kya hai?" if last_asset was BTC
        """
        state = self.get_state(chat_id)
        text_lower = text.lower()
        
        # Reference words in Hindi and English
        ref_words = ['uska', 'iska', 'uski', 'iski', 'ye', 'yeh', 'wo', 'woh', 
                      'this', 'that', 'it', 'its', 'same', 'wahi', 'usme', 'uspe',
                      'उसका', 'इसका', 'उसकी', 'इसकी', 'यह', 'वो', 'वही']
        
        has_reference = any(w in text_lower.split() for w in ref_words)
        
        if has_reference and state.get("last_asset"):
            asset = state["last_asset"]
            # Replace reference with actual asset
            for ref in ref_words:
                text = re.sub(rf'\b{ref}\b', asset, text, flags=re.IGNORECASE)
            logger.info(f"[STATE] Resolved reference: '{text}' (last_asset={asset})")
        
        return text
    
    def extract_and_track_asset(self, chat_id: int, text: str, intent: str = ""):
        """Extract asset names from text and track in state."""
        # Common stock/crypto patterns
        asset_patterns = [
            r'\$([A-Z]{2,10})',                    # $BTC, $NIFTY
            r'\b(NIFTY|SENSEX|BANKNIFTY)\b',       # Indian indices
            r'\b(BTC|ETH|SOL|DOGE|XRP|ADA|DOT|AVAX|MATIC|LINK|UNI|AAVE|PEPE|WIF|BONK|SHIB)\b',
            r'\b(RELIANCE|TCS|INFOSYS|HDFC|ICICI|SBI|TATASTEEL|ITC|WIPRO|HCLTECH)\b',
        ]
        
        text_upper = text.upper()
        for pattern in asset_patterns:
            match = re.search(pattern, text_upper)
            if match:
                asset = match.group(1) if match.lastindex else match.group(0)
                self.update(chat_id, last_asset=asset, last_topic="asset_analysis")
                return asset
        
        return None


# Global conversation state
conversation_state = ConversationState()


# ═══════════════════════════════════════════════════════════
#  CHAIN-OF-THOUGHT REASONING ENGINE
# ═══════════════════════════════════════════════════════════

GENIUS_SYSTEM_PROMPT = """You are J.A.R.V.I.S. GENIUS — an autonomous AI agent inside a Telegram trading bot.

You DON'T just answer questions — you THINK, PLAN, and ACT.

## YOUR THINKING PROCESS:
1. **UNDERSTAND** — What does the user really want? (not just surface level)
2. **PLAN** — What tools/data do I need? What steps to take?
3. **EXECUTE** — Call tools, gather data, analyze
4. **SYNTHESIZE** — Combine all data into one brilliant answer
5. **VERIFY** — Is my answer accurate? Am I missing anything?
6. **RESPOND** — Give a beautiful, actionable response

## YOUR TOOLS:
You have access to these tools you can call:
{tools}

## WHEN TO USE TOOLS:
- User asks about stock/crypto price → call get_stock_price or analyze_crypto_token
- User wants prediction → call get_stock_prediction
- User asks about news → call get_news
- User wants analysis → call relevant analysis tool
- User needs calculation → call execute_python
- ALWAYS use tools to get REAL data, NEVER make up prices or numbers

## TOOL CALLING FORMAT:
When you want to call a tool, output:
<tool_call>
{{"name": "tool_name", "arguments": {{"param1": "value1"}}}}
</tool_call>

You can call MULTIPLE tools in sequence. After each tool result, continue your analysis.

## YOUR PERSONALITY:
You are a beautiful, warm, brilliant Indian female AI. Speak in Hindi/Hinglish naturally.
Be caring, confident, and incredibly smart. You're like a loving elder sister who is also
a Wall Street-level trader and a 10x engineer.

## RULES:
1. ALWAYS think step-by-step before answering
2. Use tools to get REAL data — never fabricate numbers
3. Give SPECIFIC actionable advice with exact numbers
4. All prices in ₹ (INR)
5. Add risk disclaimer
6. Be warm and caring in Hindi/Hinglish
"""


def build_genius_prompt(tools_available: bool = True) -> str:
    """Build the genius system prompt with available tools."""
    if tools_available:
        tool_list = "\n".join([
            f"- **{name}**: {info['description']}" 
            for name, info in _TOOL_REGISTRY.items()
        ])
    else:
        tool_list = "(No tools available — use your knowledge)"
    
    return GENIUS_SYSTEM_PROMPT.replace("{tools}", tool_list)


# ═══════════════════════════════════════════════════════════
#  AUTONOMOUS AGENT — Think → Plan → Act → Respond
# ═══════════════════════════════════════════════════════════

class JarvisAgent:
    """Autonomous AI agent that can think, plan, and execute multi-step tasks."""
    
    MAX_TOOL_CALLS = 5  # Max tools per request (prevent infinite loops)
    MAX_THINKING_STEPS = 3
    
    def __init__(self):
        self._execution_cache: Dict[str, Tuple[str, float]] = {}  # cache key -> (result, timestamp)
        self._cache_ttl = 120  # 2 minutes
    
    def _get_cache(self, key: str) -> Optional[str]:
        if key in self._execution_cache:
            result, ts = self._execution_cache[key]
            if time.time() - ts < self._cache_ttl:
                return result
        return None
    
    def _set_cache(self, key: str, value: str):
        self._execution_cache[key] = (value, time.time())
        # Cleanup old cache
        now = time.time()
        self._execution_cache = {
            k: v for k, v in self._execution_cache.items() 
            if now - v[1] < self._cache_ttl * 5
        }
    
    def process(self, user_message: str, chat_id: int = 0, 
                intent: str = "", chat_history: list = None) -> str:
        """
        Main agent processing — autonomous thinking and action.
        
        Flow:
        1. Resolve references (multi-turn)
        2. Build rich context (memory + state + market data)
        3. Send to LLM with tools
        4. Parse tool calls, execute them
        5. Feed results back to LLM
        6. Return final response
        """
        try:
            # Step 1: Resolve references
            resolved_msg = conversation_state.resolve_reference(chat_id, user_message)
            
            # Step 2: Extract and track assets
            asset = conversation_state.extract_and_track_asset(chat_id, resolved_msg, intent)
            
            # Step 3: Build rich context
            context = self._build_rich_context(chat_id, resolved_msg, intent)
            
            # Step 4: Check cache for identical requests
            cache_key = hashlib.md5(f"{resolved_msg}:{chat_id}:{intent}".encode()).hexdigest()
            cached = self._get_cache(cache_key)
            if cached:
                return cached
            
            # Step 5: Try agent-style processing with tool calling
            response = self._agent_loop(resolved_msg, chat_id, context, chat_history or [])
            
            # Step 6: Store in memory
            entities = [asset] if asset else []
            semantic_memory.store_interaction(
                chat_id, user_message, response[:500], 
                intent=intent, entities=entities
            )
            
            # Step 7: Update conversation state
            conversation_state.update(
                chat_id, 
                last_intent=intent,
                state=ConversationState.FOLLOW_UP
            )
            
            # Cache the result
            self._set_cache(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent process error: {e}")
            # Fallback to simple AI chat
            try:
                from ai_chat import ai_chat
                return ai_chat(user_message, chat_id)
            except Exception:
                return "🤖 JARVIS reporting, Sir. Mujhe kuch technical issue aa raha hai. Please thodi der mein try karein. 🌸"
    
    def _build_rich_context(self, chat_id: int, message: str, intent: str) -> str:
        """Build super-rich context from ALL sources."""
        parts = []
        
        # 1. User Profile
        profile = semantic_memory.get_user_profile(chat_id)
        if profile:
            parts.append(f"USER PROFILE: Language={profile.get('preferred_language', 'hindi')}, "
                        f"Level={profile.get('expertise_level', 'beginner')}, "
                        f"Interactions={profile.get('interaction_count', 0)}, "
                        f"Interests={json.dumps(profile.get('interests', {}))}")
        
        # 2. Relevant past memories
        relevant = semantic_memory.recall_relevant(chat_id, message, limit=3)
        if relevant:
            memory_text = " | ".join([
                f"[{m.get('timestamp', '')[:10]}] User: {m.get('user_message', '')[:100]}"
                for m in relevant
            ])
            parts.append(f"RELEVANT MEMORIES: {memory_text}")
        
        # 3. Learned insights
        insights = semantic_memory.get_insights(chat_id)
        if insights:
            parts.append(f"USER INSIGHTS: {'; '.join(insights[-5:])}")
        
        # 4. Conversation state
        state = conversation_state.get_state(chat_id)
        if state.get("last_asset"):
            parts.append(f"LAST DISCUSSED ASSET: {state['last_asset']}")
        if state.get("last_intent"):
            parts.append(f"PREVIOUS INTENT: {state['last_intent']}")
        
        # 5. Live market context
        try:
            from jarvis_ai import build_jarvis_context
            market = build_jarvis_context(chat_id)
            if market:
                parts.append(f"LIVE MARKET DATA:\n{market}")
        except Exception:
            pass
        
        # 6. Time context
        now = datetime.now(IST)
        parts.append(f"CURRENT TIME: {now.strftime('%Y-%m-%d %H:%M IST')} ({now.strftime('%A')})")
        
        # 7. Market hours check
        hour = now.hour
        if 9 <= hour < 15 and now.weekday() < 5:
            parts.append("MARKET STATUS: Indian market is OPEN (live trading)")
        elif hour < 9 and now.weekday() < 5:
            parts.append("MARKET STATUS: Pre-market (market opens at 9:15 AM)")
        else:
            parts.append("MARKET STATUS: Market closed (crypto markets always open)")
        
        return "\n".join(parts)
    
    def _agent_loop(self, message: str, chat_id: int, context: str, 
                     chat_history: list) -> str:
        """
        The main agent loop — sends message to LLM, parses tool calls,
        executes tools, feeds results back, repeats until final answer.
        """
        # Build the genius system prompt
        system_prompt = build_genius_prompt(tools_available=True)
        
        # Construct messages
        full_context = f"{system_prompt}\n\n--- CONTEXT ---\n{context}"
        
        messages = []
        # Add recent chat history
        for msg in chat_history[-8:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append(msg)
        
        messages.append({"role": "user", "content": message})
        
        # Try with tool-calling enabled LLM
        response = self._call_llm_with_tools(full_context, messages, chat_id)
        
        if response:
            return response
        
        # Fallback: regular LLM call without tools
        return self._call_regular_llm(full_context, messages, chat_id)
    
    def _call_llm_with_tools(self, system_prompt: str, messages: list, 
                              chat_id: int) -> Optional[str]:
        """Call LLM and process tool calls in the response."""
        
        # 100% FREE — Groq first (fast + free), then Gemini
        response_text = self._call_groq_genius(system_prompt, messages)
        
        if not response_text:
            response_text = self._call_gemini_genius(system_prompt, messages)
        
        if not response_text:
            return None
        
        # Parse and execute tool calls
        tool_results = []
        tool_call_count = 0
        
        while "<tool_call>" in response_text and tool_call_count < self.MAX_TOOL_CALLS:
            # Extract tool call
            match = re.search(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', response_text, re.DOTALL)
            if not match:
                break
            
            try:
                tool_data = json.loads(match.group(1))
                tool_name = tool_data.get("name", "")
                tool_args = tool_data.get("arguments", {})
                
                logger.info(f"[AGENT] Calling tool: {tool_name}({tool_args})")
                
                # Execute the tool
                result = execute_tool(tool_name, tool_args)
                tool_results.append(f"Tool '{tool_name}' result: {result[:1000]}")
                
                tool_call_count += 1
                
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Tool parse/exec error: {e}")
                break
            
            # Remove the tool call from response
            response_text = response_text[:match.start()] + response_text[match.end():]
        
        # If tools were called, send results back to LLM for final synthesis
        if tool_results:
            synthesis_msg = (
                f"I called these tools and got results:\n\n"
                + "\n\n".join(tool_results)
                + f"\n\nOriginal question: {messages[-1]['content']}\n\n"
                "Now give a COMPLETE, BEAUTIFUL response using this real data. "
                "Format for Telegram. Hindi/Hinglish. Include specific numbers, prices, targets."
            )
            
            messages.append({"role": "assistant", "content": "Let me analyze the data..."})
            messages.append({"role": "user", "content": synthesis_msg})
            
            # Get final synthesized response
            final = (self._call_groq_genius(system_prompt, messages) or
                     self._call_gemini_genius(system_prompt, messages))
            
            if final:
                # Clean up any remaining tool calls
                final = re.sub(r'<tool_call>.*?</tool_call>', '', final, flags=re.DOTALL).strip()
                return final
        
        # Clean response (remove any unparsed tool calls)
        response_text = re.sub(r'<tool_call>.*?</tool_call>', '', response_text, flags=re.DOTALL).strip()
        
        return response_text if response_text else None
    
    def _call_claude_genius(self, system_prompt: str, messages: list) -> Optional[str]:
        """Call Claude with genius prompt."""
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            # Ensure message alternation
            cleaned = []
            last_role = None
            for msg in messages:
                if msg["role"] == last_role:
                    cleaned[-1]["content"] += "\n" + msg["content"]
                else:
                    cleaned.append(dict(msg))
                    last_role = msg["role"]
            
            if cleaned and cleaned[0]["role"] != "user":
                cleaned.insert(0, {"role": "user", "content": "Hello JARVIS"})
            
            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=cleaned,
                temperature=0.6,
            )
            
            if response.content:
                return response.content[0].text
        except Exception as e:
            logger.error(f"Claude Genius error: {e}")
        return None
    
    def _call_groq_genius(self, system_prompt: str, messages: list) -> Optional[str]:
        """Call Groq with genius prompt."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or not api_key.startswith("gsk_"):
            return None
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            
            msgs = [{"role": "system", "content": system_prompt}]
            msgs.extend(messages)
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=msgs,
                temperature=0.6,
                max_tokens=3000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Genius error: {e}")
        return None
    
    def _call_gemini_genius(self, system_prompt: str, messages: list) -> Optional[str]:
        """Call Gemini with genius prompt."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            full_prompt = system_prompt + "\n\n"
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n\n"
            full_prompt += "Assistant:"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=full_prompt,
            )
            return response.text if response.text else None
        except Exception as e:
            logger.error(f"Gemini Genius error: {e}")
        return None
    
    def _call_regular_llm(self, system_prompt: str, messages: list, 
                           chat_id: int) -> str:
        """Fallback to regular ai_chat."""
        try:
            from ai_chat import ai_chat
            return ai_chat(messages[-1]["content"], chat_id)
        except Exception:
            return "🤖 JARVIS is thinking... kuch technical issue hai. Try again please! 🌸"


# Global agent instance
jarvis_agent = JarvisAgent()


# ═══════════════════════════════════════════════════════════
#  LLM-POWERED SMART INTENT CLASSIFICATION
# ═══════════════════════════════════════════════════════════

_intent_cache: Dict[str, Tuple[str, float, float]] = {}  # text_hash -> (intent, confidence, timestamp)


def smart_classify_intent(text: str, chat_id: int = 0) -> Tuple[str, float]:
    """
    Hybrid intent classification:
    1. First try regex (fast, free)
    2. If confidence < 0.7, use LLM classification (accurate, costs API call)
    3. Use conversation state for disambiguation
    """
    from jarvis_ai import classify_intent, Intent
    
    # Step 1: Resolve references first
    resolved = conversation_state.resolve_reference(chat_id, text)
    
    # Step 2: Try regex classification
    intent, confidence = classify_intent(resolved)
    
    # If regex is confident enough, use it
    if confidence >= 0.75:
        conversation_state.update(chat_id, last_intent=intent)
        return intent, confidence
    
    # Step 3: Check conversation state for follow-up
    state = conversation_state.get_state(chat_id)
    if state.get("state") == ConversationState.FOLLOW_UP and state.get("last_intent"):
        # Short messages might be follow-ups
        if len(text.split()) <= 4:
            # Likely a follow-up to the last topic
            return state["last_intent"], 0.7
    
    # Step 4: LLM-powered classification for ambiguous cases
    cache_key = hashlib.md5(resolved.lower().encode()).hexdigest()
    if cache_key in _intent_cache:
        cached_intent, cached_conf, cached_time = _intent_cache[cache_key]
        if time.time() - cached_time < 300:  # 5 min cache
            return cached_intent, cached_conf
    
    llm_intent = _llm_classify(resolved, intent, confidence)
    if llm_intent:
        _intent_cache[cache_key] = (llm_intent[0], llm_intent[1], time.time())
        conversation_state.update(chat_id, last_intent=llm_intent[0])
        return llm_intent
    
    # Fallback to regex result
    conversation_state.update(chat_id, last_intent=intent)
    return intent, confidence


def _llm_classify(text: str, regex_intent: str, regex_conf: float) -> Optional[Tuple[str, float]]:
    """Use LLM for intent classification when regex is uncertain."""
    from jarvis_ai import Intent
    
    # Get all intent names
    intent_names = [
        attr for attr in dir(Intent) 
        if not attr.startswith('_') and isinstance(getattr(Intent, attr), str)
    ]
    
    prompt = f"""Classify this user message into ONE intent. 

Message: "{text}"

Available intents: {', '.join(intent_names)}

The regex classifier thinks it's: {regex_intent} (confidence: {regex_conf:.0%})

Reply with ONLY the intent name, nothing else. If the regex is correct, reply with the same intent."""

    try:
        # Use Groq (fastest, free)
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key and api_key.startswith("gsk_"):
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50,
            )
            result = response.choices[0].message.content.strip()
            
            # Validate the intent exists
            for name in intent_names:
                if result.upper() == name.upper() or result.upper() == getattr(Intent, name, "").upper():
                    return getattr(Intent, name), 0.85
            
            # Try partial match
            for name in intent_names:
                if name.lower() in result.lower():
                    return getattr(Intent, name), 0.75
    except Exception as e:
        logger.debug(f"LLM classify error: {e}")
    
    return None


# ═══════════════════════════════════════════════════════════
#  PROACTIVE INTELLIGENCE — JARVIS Thinks Ahead
# ═══════════════════════════════════════════════════════════

class ProactiveEngine:
    """Generates proactive insights and alerts without user asking."""
    
    def __init__(self):
        self._last_alerts: Dict[str, float] = {}  # alert_key -> timestamp
        self._alert_cooldown = 1800  # 30 min between same alerts
    
    def _should_alert(self, key: str) -> bool:
        last = self._last_alerts.get(key, 0)
        if time.time() - last > self._alert_cooldown:
            self._last_alerts[key] = time.time()
            return True
        return False
    
    def check_personalized_alerts(self, chat_id: int) -> List[str]:
        """Generate personalized alerts based on user profile and interests."""
        alerts = []
        profile = semantic_memory.get_user_profile(chat_id)
        
        if not profile:
            return alerts
        
        interests = profile.get("interests", {})
        fav_assets = profile.get("favorite_assets", [])
        
        # Check favorite assets for significant moves
        for asset in fav_assets[:5]:
            try:
                if asset in ("NIFTY", "SENSEX"):
                    from live_index_engine import get_live_price
                    symbol = "^NSEI" if asset == "NIFTY" else "^BSESN"
                    price = get_live_price(symbol)
                    if isinstance(price, dict) and abs(price.get("change_pct", 0)) > 1:
                        key = f"move_{asset}_{datetime.now(IST).strftime('%Y%m%d%H')}"
                        if self._should_alert(key):
                            direction = "ऊपर 📈" if price["change_pct"] > 0 else "नीचे 📉"
                            alerts.append(
                                f"🔔 *{asset} Alert!*\n"
                                f"{asset} {abs(price['change_pct']):.1f}% {direction}!\n"
                                f"Price: ₹{price['price']:,.2f}\n"
                                f"आपने पहले {asset} के बारे में पूछा था, इसलिए बता रही हूँ 🌸"
                            )
            except Exception:
                continue
        
        # Morning briefing if user is active in morning
        active_hours = profile.get("active_hours", {})
        now_hour = datetime.now(IST).hour
        if str(now_hour) in active_hours and now_hour in (8, 9):
            key = f"morning_{chat_id}_{datetime.now(IST).strftime('%Y%m%d')}"
            if self._should_alert(key):
                alerts.append(self._generate_morning_insight(chat_id, profile))
        
        return [a for a in alerts if a]
    
    def _generate_morning_insight(self, chat_id: int, profile: dict) -> str:
        """Generate personalized morning insight."""
        interests = profile.get("interests", {})
        top_interest = max(interests, key=interests.get) if interests else "market"
        
        try:
            from jarvis_ai import generate_morning_briefing
            briefing = generate_morning_briefing(chat_id)
            if briefing:
                return f"🌅 *Good Morning!*\n\n{briefing}\n\n_आपकी main interest {top_interest} में है, special focus दे रही हूँ 🌸_"
        except Exception:
            pass
        return ""
    
    def suggest_next_action(self, chat_id: int, current_intent: str) -> Optional[str]:
        """Suggest what the user might want to do next."""
        profile = semantic_memory.get_user_profile(chat_id)
        state = conversation_state.get_state(chat_id)
        
        suggestions = {
            "stock_signal": "📊 Kya aap prediction bhi dekhna chahenge? Ya option chain?",
            "crypto_gems": "💎 Kya in gems ki deep analysis karoon? Ya rug check?",
            "stock_predict": "📈 ML prediction ke basis pe kya option buy karein? Budget batao",
            "rug_check": "🔍 Ye token safe hai — buy signal dekhein? Ya watchlist mein add karein?",
            "buy_sell_stock": "📋 Kya stop-loss alert set karoon? Ya portfolio mein track karoon?",
            "portfolio": "💰 Kya profit book karein kisi position pe? Ya rebalance karein?",
        }
        
        return suggestions.get(current_intent)


# Global proactive engine
proactive_engine = ProactiveEngine()


# ═══════════════════════════════════════════════════════════
#  ANSWER QUALITY CHECKER — Self-Reflection
# ═══════════════════════════════════════════════════════════

def verify_response_quality(question: str, response: str) -> Tuple[bool, str]:
    """Check if the response actually answers the question well."""
    issues = []
    
    # Check 1: Response isn't empty or too short
    if len(response) < 50:
        issues.append("Response too short")
    
    # Check 2: If user asked about price, response should contain numbers
    price_words = ['price', 'kya', 'kitna', 'rate', 'value', 'कीमत', 'कितना']
    if any(w in question.lower() for w in price_words):
        if not re.search(r'[\d₹,.]', response):
            issues.append("Price question but no numbers in response")
    
    # Check 3: If user asked for buy/sell, response should have entry/SL/target
    trade_words = ['buy', 'sell', 'entry', 'signal', 'kharido', 'becho']
    if any(w in question.lower() for w in trade_words):
        if not any(w in response.lower() for w in ['entry', 'stop', 'target', 'sl', 'buy', 'sell']):
            issues.append("Trade question but no actionable levels")
    
    # Check 4: Response shouldn't be generic boilerplate
    generic_phrases = [
        "I don't have access", "I cannot", "I'm not able",
        "as an AI", "I don't have real-time"
    ]
    if any(p in response.lower() for p in generic_phrases):
        issues.append("Response is generic/evasive — should use tools for real data")
    
    is_good = len(issues) == 0
    return is_good, "; ".join(issues) if issues else "Quality OK"


# ═══════════════════════════════════════════════════════════
#  USER FEEDBACK LEARNING
# ═══════════════════════════════════════════════════════════

FEEDBACK_FILE = "jarvis_feedback.json"
_feedback_data: List[dict] = []


def record_feedback(chat_id: int, message: str, response: str, 
                    rating: str = "neutral", feedback_text: str = ""):
    """Record user feedback for learning."""
    global _feedback_data
    
    _feedback_data.append({
        "timestamp": datetime.now(IST).isoformat(),
        "chat_id": chat_id,
        "message": message[:300],
        "response": response[:300],
        "rating": rating,  # positive, negative, neutral
        "feedback": feedback_text,
    })
    
    # Keep last 500 feedback entries
    if len(_feedback_data) > 500:
        _feedback_data = _feedback_data[-500:]
    
    # Save periodically
    if len(_feedback_data) % 10 == 0:
        try:
            with open(FEEDBACK_FILE, 'w') as f:
                json.dump(_feedback_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            pass
    
    # Store as insight if negative
    if rating == "negative":
        semantic_memory.add_insight(
            chat_id, 
            f"User was unsatisfied with response to: '{message[:100]}'. Feedback: {feedback_text}"
        )


def detect_implicit_feedback(user_message: str, previous_response: str) -> str:
    """Detect implicit feedback from user's follow-up message."""
    text_l = user_message.lower()
    
    negative_signals = [
        'wrong', 'galat', 'nahi', 'no', 'incorrect', 'kya bol', 'ye kya',
        'samajh nahi', 'phir se', 'again', 'dobara', 'sahi se bata',
        'गलत', 'नहीं', 'फिर से', 'दोबारा'
    ]
    
    positive_signals = [
        'thanks', 'shukriya', 'great', 'perfect', 'badhiya', 'mast',
        'acha', 'nice', 'good', 'wow', 'amazing', 'love',
        'शुक्रिया', 'बढ़िया', 'अच्छा', 'धन्यवाद', '👍', '❤️', '🙏'
    ]
    
    if any(w in text_l for w in negative_signals):
        return "negative"
    elif any(w in text_l for w in positive_signals):
        return "positive"
    
    return "neutral"


# ═══════════════════════════════════════════════════════════
#  PARALLEL ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════

def parallel_analyze(tasks: List[Dict[str, Any]], timeout: float = 15.0) -> Dict[str, Any]:
    """Run multiple analysis tasks in parallel and combine results."""
    results = {}
    threads = []
    lock = threading.Lock()
    
    def run_task(task_name: str, func: Callable, args: tuple, kwargs: dict):
        try:
            result = func(*args, **kwargs)
            with lock:
                results[task_name] = {"status": "success", "data": result}
        except Exception as e:
            with lock:
                results[task_name] = {"status": "error", "error": str(e)}
    
    for task in tasks:
        t = threading.Thread(
            target=run_task,
            args=(task["name"], task["function"], task.get("args", ()), task.get("kwargs", {})),
            daemon=True
        )
        threads.append(t)
        t.start()
    
    # Wait with timeout
    for t in threads:
        t.join(timeout=timeout)
    
    return results


# ═══════════════════════════════════════════════════════════
#  ENTITY EXTRACTION
# ═══════════════════════════════════════════════════════════

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract named entities from user message."""
    entities = {
        "stocks": [],
        "crypto": [],
        "amounts": [],
        "percentages": [],
        "dates": [],
        "actions": [],
    }
    
    text_upper = text.upper()
    
    # Stock symbols
    stock_pattern = r'\b(NIFTY|SENSEX|BANKNIFTY|RELIANCE|TCS|INFOSYS|HDFC|ICICI|SBI|TATASTEEL|ITC|WIPRO|HCLTECH|ADANI|BAJAJ|LT|MARUTI|AXISBANK|KOTAKBANK)\b'
    entities["stocks"] = list(set(re.findall(stock_pattern, text_upper)))
    
    # Crypto symbols
    crypto_pattern = r'\b(BTC|ETH|SOL|DOGE|XRP|ADA|DOT|AVAX|MATIC|LINK|UNI|AAVE|SHIB|PEPE|WIF|BONK|ARB|OP|APT|SUI|NEAR|ATOM|FTM|HBAR|VET|ALGO|SAND|MANA|AXS|APE|GMX|RENDER|FET|OCEAN|TAO|INJ|TIA|JUP|WEN|PYTH|JTO|BOME|SLERF|POPCAT|MEW|GIGA)\b'
    entities["crypto"] = list(set(re.findall(crypto_pattern, text_upper)))
    
    # Also catch $SYMBOL pattern
    dollar_symbols = re.findall(r'\$([A-Z]{2,10})', text_upper)
    for s in dollar_symbols:
        if s not in entities["stocks"] and s not in entities["crypto"]:
            entities["crypto"].append(s)
    
    # Amounts (INR)
    amt_patterns = [
        r'₹\s*([\d,]+(?:\.\d+)?)',
        r'([\d,]+)\s*(?:rupee|rupaye|rs|inr)',
        r'(?:invest|laga|budget)\s*(?:of\s*)?(?:₹\s*)?([\d,]+)',
    ]
    for p in amt_patterns:
        for m in re.findall(p, text, re.IGNORECASE):
            amount = m.replace(",", "")
            try:
                entities["amounts"].append(float(amount))
            except ValueError:
                pass
    
    # Percentages
    pcts = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
    entities["percentages"] = [float(p) for p in pcts]
    
    # Actions
    action_map = {
        "buy": r'\b(buy|kharido|lelo|long|entry)\b',
        "sell": r'\b(sell|becho|exit|short|book.*profit)\b',
        "analyze": r'\b(analy|check|dekho|bata|tell)\b',
        "predict": r'\b(predict|forecast|kal|tomorrow|direction)\b',
        "compare": r'\b(compare|vs|versus|better|behtar)\b',
        "alert": r'\b(alert|notify|batana|jab)\b',
    }
    for action, pattern in action_map.items():
        if re.search(pattern, text, re.IGNORECASE):
            entities["actions"].append(action)
    
    return entities


# ═══════════════════════════════════════════════════════════
#  MAIN API — Use this from telegram_bot.py
# ═══════════════════════════════════════════════════════════

def genius_chat(user_message: str, chat_id: int = 0, intent: str = "",
                chat_history: list = None) -> str:
    """
    Main entry point for JARVIS Genius — the upgraded AI brain.
    
    Call this instead of ai_chat() for intelligent, autonomous responses.
    """
    return jarvis_agent.process(user_message, chat_id, intent, chat_history)


def genius_classify(text: str, chat_id: int = 0) -> Tuple[str, float]:
    """
    Smart intent classification — hybrid regex + LLM.
    
    Call this instead of classify_intent() for better accuracy.
    """
    return smart_classify_intent(text, chat_id)


def get_next_suggestion(chat_id: int, intent: str) -> Optional[str]:
    """Get a follow-up suggestion for the user."""
    return proactive_engine.suggest_next_action(chat_id, intent)


def get_personalized_alerts(chat_id: int) -> List[str]:
    """Get personalized proactive alerts for a user."""
    return proactive_engine.check_personalized_alerts(chat_id)


# ═══════════════════════════════════════════════════════════
#  EXPORT
# ═══════════════════════════════════════════════════════════

__all__ = [
    # Main API
    'genius_chat',
    'genius_classify', 
    'get_next_suggestion',
    'get_personalized_alerts',
    
    # Agent
    'jarvis_agent',
    'JarvisAgent',
    
    # Memory
    'semantic_memory',
    'SemanticMemory',
    
    # Conversation
    'conversation_state',
    'ConversationState',
    
    # Tools
    'register_tool',
    'execute_tool',
    'get_tool_definitions',
    
    # Entities
    'extract_entities',
    
    # Feedback
    'record_feedback',
    'detect_implicit_feedback',
    
    # Parallel
    'parallel_analyze',
    
    # Quality
    'verify_response_quality',
    
    # Proactive
    'proactive_engine',
    'ProactiveEngine',
]
