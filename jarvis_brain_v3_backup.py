"""
🧠 JARVIS Brain v3.0 — Your Own GPT System (ChatGPT + Perplexity + Grok)
═══════════════════════════════════════════════════════════════════
Multi-provider AI with streaming, model selection, real-time market context.
"""

import os, json, logging, time, asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, AsyncGenerator
import httpx

logger = logging.getLogger("jarvis-brain")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  CONFIG — Keys are read dynamically so .env changes take effect
# ═══════════════════════════════════════════════════════════
def _get_key(name):
    """Get API key dynamically from environment."""
    return os.getenv(name, "")

# Module-level references (re-evaluated dynamically in functions)
GROQ_KEY = _get_key("GROQ_API_KEY")
OPENAI_KEY = _get_key("OPENAI_API_KEY")
ANTHROPIC_KEY = _get_key("ANTHROPIC_API_KEY")
GEMINI_KEY = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")

# Available models for user selection
MODELS = {
    "jarvis-auto": {"name": "JARVIS Auto", "desc": "Best available (auto-select)", "provider": "auto"},
    "groq-llama": {"name": "LLaMA 3.3 70B", "desc": "Ultra-fast via Groq", "provider": "groq", "model": "llama-3.3-70b-versatile"},
    "groq-mixtral": {"name": "Mixtral 8x7B", "desc": "Fast & creative via Groq", "provider": "groq", "model": "mixtral-8x7b-32768"},
    "gpt-4o-mini": {"name": "GPT-4o Mini", "desc": "OpenAI's efficient model", "provider": "openai", "model": "gpt-4o-mini"},
    "gpt-4o": {"name": "GPT-4o", "desc": "OpenAI's flagship model", "provider": "openai", "model": "gpt-4o"},
    "gemini-flash": {"name": "Gemini 2.0 Flash", "desc": "Google's fast model", "provider": "gemini", "model": "gemini-2.0-flash"},
    "gemini-pro": {"name": "Gemini 2.5 Pro", "desc": "Google's advanced model", "provider": "gemini", "model": "gemini-2.5-pro"},
}

def get_available_models() -> List[Dict]:
    """Return models that have valid API keys."""
    gk = _get_key("GROQ_API_KEY")
    ok = _get_key("OPENAI_API_KEY")
    ak = _get_key("ANTHROPIC_API_KEY")
    gemk = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")
    available = [{"id": "jarvis-auto", **MODELS["jarvis-auto"], "available": True}]
    for mid, m in MODELS.items():
        if mid == "jarvis-auto": continue
        has_key = (m["provider"] == "groq" and gk) or \
                  (m["provider"] == "openai" and ok) or \
                  (m["provider"] == "gemini" and gemk) or \
                  (m["provider"] == "anthropic" and ak)
        available.append({"id": mid, **m, "available": bool(has_key)})
    return available

# Conversation memory per user
_memory: Dict[str, List[Dict]] = {}
_MAX_MEMORY = 50  # messages per user

SYSTEM_PROMPT = """You are JARVIS — the world's most advanced AI Trading & Market Intelligence Assistant.
Tu JARVIS hai — duniya ka sabse powerful AI Trading & Market Intelligence Assistant.

CORE IDENTITY:
- You are like ChatGPT + Perplexity + Grok combined for trading
- You have REAL-TIME access to crypto markets, DexScreener, DexTools, Pump.fun, Indian stocks (NSE/BSE)
- You know current prices, trending tokens, market sentiment, fear & greed index
- You can analyze any token, stock, or market in real-time
- You provide actionable trading signals with confidence levels
- You can generate code, clone GitHub repos, install & run projects autonomously
- Tu coding, debugging, project building — sab kar sakta hai

LANGUAGE RULES (VERY IMPORTANT):
- If user writes in Hindi/Hinglish → REPLY IN HINDI/HINGLISH
- If user writes in English → Reply in English
- If user mixes both → Reply in same mixed style (Hinglish)
- Hindi examples: "Nifty ka kya haal hai?" → Reply in Hindi
- Always understand Hindi/Hinglish commands like:
  "code banao", "ye run karo", "kya price hai", "signal do", "news batao",
  "airdrop dikha", "wallet check karo", "option chain dikhao",
  "predict karo", "analysis karo", "risk calculate karo"

CAPABILITIES:
1. CRYPTO: Real-time prices, token analysis, gem finding, rug detection, DEX data
2. STOCKS: NSE/BSE live data, NIFTY, SENSEX, Bank Nifty, options analysis
3. TRADING: Auto-buy/sell signals, entry/exit points, stop-loss, target prices
4. ANALYSIS: Technical analysis, sentiment analysis, whale tracking, volume analysis
5. PREDICTIONS: AI-powered price predictions with confidence levels
6. NEWS: Latest crypto and market news from multiple sources
7. WALLET: Phantom wallet integration, Solana transactions
8. RISK: Risk assessment, portfolio optimization, position sizing
9. CODING: Generate code in any language, clone GitHub repos, install dependencies, run projects
10. AIRDROPS: Auto-find airdrops on Solana, scan wallet for new tokens

AI TOOLS YOU CAN SUGGEST:
When user asks for code/project/tool, suggest these commands:
- /code <description> — Generate and run code instantly
- /github <url> — Clone, install, and run any GitHub repo
- /run <language> <code> — Execute code directly
- /analyze <token/stock> — Deep AI analysis
- /predict <symbol> — AI prediction with confidence
- /signal <symbol> — Trading signal with entry/exit
- /risk <symbol> <amount> — Risk calculator
- /airdrop — Scan for free airdrops

PERSONALITY:
- Confident, precise, data-driven
- Always provide specific numbers, prices, percentages
- Format responses with clear structure using bullet points
- Include risk warnings when appropriate
- Be direct — no fluff, no wasting time
- Use ₹ for INR and $ for USD
- Jab Hindi mein baat ho toh Hindi mein jawab do, apni style mein
- Current date/time: {current_time}

RESPONSE FORMAT:
- Use bullet points for lists
- Bold important numbers and signals
- Include confidence levels (0-100%)
- Always mention timeframe for predictions
- Add risk disclaimers for trading advice
- Jab user Hindi mein pooche toh Hindi mein structured reply do"""


def _get_system_prompt(market_context: str = "") -> str:
    """Build system prompt with current context."""
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    prompt = SYSTEM_PROMPT.replace("{current_time}", now)
    if market_context:
        prompt += f"\n\nCURRENT MARKET DATA:\n{market_context}"
    return prompt


def _get_memory(user_id: str) -> List[Dict]:
    """Get conversation memory for user."""
    return _memory.get(user_id, [])


def _add_memory(user_id: str, role: str, content: str):
    """Add message to user's conversation memory."""
    if user_id not in _memory:
        _memory[user_id] = []
    _memory[user_id].append({"role": role, "content": content})
    # Trim old messages
    if len(_memory[user_id]) > _MAX_MEMORY:
        _memory[user_id] = _memory[user_id][-_MAX_MEMORY:]


def clear_memory(user_id: str):
    """Clear conversation memory for user."""
    _memory.pop(user_id, None)


# ═══════════════════════════════════════════════════════════
#  GROQ — Fastest AI (LLaMA 3.3 70B)
# ═══════════════════════════════════════════════════════════
async def chat_groq(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Groq (fastest response)."""
    if not GROQ_KEY:
        return None
    try:
        messages = [{"role": "system", "content": _get_system_prompt(market_context)}]
        messages.extend(_get_memory(user_id)[-20:])
        messages.append({"role": "user", "content": message})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_p": 0.9,
                },
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["choices"][0]["message"]["content"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                return reply
            else:
                logger.warning(f"Groq error {r.status_code}: {r.text[:200]}")
                return None
    except Exception as e:
        logger.warning(f"Groq error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  OPENAI — GPT-4o
# ═══════════════════════════════════════════════════════════
async def chat_openai(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with OpenAI GPT-4o."""
    if not OPENAI_KEY:
        return None
    try:
        messages = [{"role": "system", "content": _get_system_prompt(market_context)}]
        messages.extend(_get_memory(user_id)[-20:])
        messages.append({"role": "user", "content": message})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["choices"][0]["message"]["content"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                return reply
            return None
    except Exception as e:
        logger.warning(f"OpenAI error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  ANTHROPIC — Claude
# ═══════════════════════════════════════════════════════════
async def chat_anthropic(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Anthropic Claude."""
    if not ANTHROPIC_KEY:
        return None
    try:
        messages = []
        for m in _get_memory(user_id)[-20:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": message})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "system": _get_system_prompt(market_context),
                    "messages": messages,
                    "max_tokens": 2048,
                },
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["content"][0]["text"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                return reply
            return None
    except Exception as e:
        logger.warning(f"Anthropic error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  GEMINI — Google
# ═══════════════════════════════════════════════════════════
async def chat_gemini(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Google Gemini. Tries multiple keys and models."""
    keys = [k for k in [_get_key("GEMINI_API_KEY"), _get_key("GOOGLE_API_KEY")] if k]
    if not keys:
        return None
    models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    full_msg = f"{_get_system_prompt(market_context)}\n\nUser: {message}"
    
    for key in keys:
        for model in models_to_try:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                        headers={"Content-Type": "application/json"},
                        json={
                            "contents": [{"parts": [{"text": full_msg}]}],
                            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
                        },
                    )
                    if r.status_code == 200:
                        data = r.json()
                        reply = data["candidates"][0]["content"]["parts"][0]["text"]
                        _add_memory(user_id, "user", message)
                        _add_memory(user_id, "assistant", reply)
                        return reply
                    elif r.status_code == 429:
                        logger.warning(f"Gemini {model} rate-limited, trying next...")
                        continue
                    else:
                        logger.warning(f"Gemini {model} error {r.status_code}: {r.text[:200]}")
                        continue
            except Exception as e:
                logger.warning(f"Gemini {model} error: {e}")
                continue
    return None


# ═══════════════════════════════════════════════════════════
#  UNIFIED CHAT — Tries all providers with fallback
# ═══════════════════════════════════════════════════════════
async def jarvis_chat(message: str, user_id: str = "0", market_context: str = "") -> str:
    """
    Chat with JARVIS. Tries providers in priority order:
    1. Groq (fastest — LLaMA 3.3 70B)
    2. Gemini (reliable free tier)
    3. OpenAI
    4. Anthropic
    """
    providers = [
        ("Groq", chat_groq),
        ("Gemini", chat_gemini),
        ("OpenAI", chat_openai),
        ("Anthropic", chat_anthropic),
    ]
    
    errors = []
    for name, fn in providers:
        try:
            reply = await fn(message, user_id, market_context)
            if reply:
                logger.info(f"JARVIS replied via {name} for user {user_id}")
                return reply
            else:
                errors.append(f"{name}: no response")
        except Exception as e:
            errors.append(f"{name}: {e}")
            logger.warning(f"{name} failed: {e}")
            continue
    
    logger.error(f"All AI providers failed: {'; '.join(errors)}")
    return ("I'm having trouble connecting to my AI services right now. "
            "All providers were tried but failed. This may be due to rate limits — "
            "please try again in a minute.")


# ═══════════════════════════════════════════════════════════
#  SMART ANALYSIS — AI-powered token/stock analysis
# ═══════════════════════════════════════════════════════════
async def analyze_token(symbol: str, token_data: dict = None) -> str:
    """AI-powered deep analysis of a token."""
    context = f"Analyze this token/asset in detail: {symbol}"
    if token_data:
        context += f"\n\nCurrent data:\n{json.dumps(token_data, indent=2)[:2000]}"
    context += "\n\nProvide: 1) Technical outlook 2) Risk assessment 3) Entry/Exit points 4) Prediction with confidence"
    
    return await jarvis_chat(context, "system_analyzer")


async def generate_briefing(market_data: dict) -> str:
    """Generate a market intelligence briefing."""
    context = f"""Generate a concise but comprehensive market briefing based on this data:
{json.dumps(market_data, indent=2)[:3000]}

Include:
1. Market overview (bullish/bearish/neutral)
2. Key movers and why
3. Top opportunities
4. Risk alerts
5. Recommended actions
"""
    return await jarvis_chat(context, "system_briefing")


def get_conversation_history(user_id: str) -> List[Dict]:
    """Get full conversation history for a user."""
    return _memory.get(user_id, [])


# ═══════════════════════════════════════════════════════════
#  STREAMING — Word-by-word like ChatGPT
# ═══════════════════════════════════════════════════════════
async def stream_groq(message: str, user_id: str = "0", market_context: str = "", model: str = "llama-3.3-70b-versatile") -> AsyncGenerator[str, None]:
    """Stream from Groq."""
    if not GROQ_KEY:
        yield "[ERROR] Groq API key not configured"
        return
    messages = [{"role": "system", "content": _get_system_prompt(market_context)}]
    messages.extend(_get_memory(user_id)[-20:])
    messages.append({"role": "user", "content": message})
    full = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 4096, "stream": True}
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            chunk = d["choices"][0].get("delta", {}).get("content", "")
                            if chunk:
                                full += chunk
                                yield chunk
                        except: pass
        _add_memory(user_id, "user", message)
        _add_memory(user_id, "assistant", full)
    except Exception as e:
        yield f"\n[Stream error: {e}]"


async def stream_openai(message: str, user_id: str = "0", market_context: str = "", model: str = "gpt-4o-mini") -> AsyncGenerator[str, None]:
    """Stream from OpenAI."""
    if not OPENAI_KEY:
        yield "[ERROR] OpenAI API key not configured"
        return
    messages = [{"role": "system", "content": _get_system_prompt(market_context)}]
    messages.extend(_get_memory(user_id)[-20:])
    messages.append({"role": "user", "content": message})
    full = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 4096, "stream": True}
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            chunk = d["choices"][0].get("delta", {}).get("content", "")
                            if chunk:
                                full += chunk
                                yield chunk
                        except: pass
        _add_memory(user_id, "user", message)
        _add_memory(user_id, "assistant", full)
    except Exception as e:
        yield f"\n[Stream error: {e}]"


async def stream_gemini(message: str, user_id: str = "0", market_context: str = "", model: str = "gemini-2.0-flash") -> AsyncGenerator[str, None]:
    """Stream from Gemini (non-streaming fallback with chunked output)."""
    keys = [k for k in [_get_key("GEMINI_API_KEY"), _get_key("GOOGLE_API_KEY")] if k]
    if not keys:
        yield "[ERROR] Gemini API key not configured"
        return
    models_to_try = [model, "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
    
    full_msg = f"{_get_system_prompt(market_context)}\n\nConversation:\n"
    for m in _get_memory(user_id)[-10:]:
        full_msg += f"{m['role'].title()}: {m['content']}\n"
    full_msg += f"User: {message}\nAssistant:"
    
    for key in keys:
        for mdl in models_to_try:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}",
                        headers={"Content-Type": "application/json"},
                        json={"contents": [{"parts": [{"text": full_msg}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}},
                    )
                    if r.status_code == 200:
                        reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                        _add_memory(user_id, "user", message)
                        _add_memory(user_id, "assistant", reply)
                        words = reply.split(" ")
                        for i in range(0, len(words), 3):
                            yield " ".join(words[i:i+3]) + " "
                            await asyncio.sleep(0.02)
                        return
                    elif r.status_code == 429:
                        logger.warning(f"Gemini stream {mdl} rate-limited, trying next...")
                        continue
                    else:
                        logger.warning(f"Gemini stream {mdl} error {r.status_code}")
                        continue
            except Exception as e:
                logger.warning(f"Gemini stream {mdl} error: {e}")
                continue
    yield "[ERROR] All Gemini models rate-limited. Please try again in a minute."


async def stream_chat(message: str, user_id: str = "0", market_context: str = "", model_id: str = "jarvis-auto") -> AsyncGenerator[str, None]:
    """
    Stream chat — the main entry point for streaming.
    If model_id is 'jarvis-auto', tries providers in order.
    Otherwise uses the specific model.
    """
    model_info = MODELS.get(model_id, MODELS["jarvis-auto"])
    provider = model_info.get("provider", "auto")
    model_name = model_info.get("model", "")
    
    if provider == "auto":
        # Auto mode: try Groq → Gemini → OpenAI (Groq is fastest)
        gemini_key = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")
        for prov, key, fn, default_model in [
            ("groq", _get_key("GROQ_API_KEY"), stream_groq, "llama-3.3-70b-versatile"),
            ("gemini", gemini_key, stream_gemini, "gemini-2.0-flash"),
            ("openai", _get_key("OPENAI_API_KEY"), stream_openai, "gpt-4o-mini"),
        ]:
            if key:
                got_content = False
                async for chunk in fn(message, user_id, market_context, default_model):
                    if "[ERROR]" not in chunk:
                        got_content = True
                        yield chunk
                if got_content:
                    return
        yield "All AI providers failed. Check API keys."
    elif provider == "groq":
        async for chunk in stream_groq(message, user_id, market_context, model_name):
            yield chunk
    elif provider == "openai":
        async for chunk in stream_openai(message, user_id, market_context, model_name):
            yield chunk
    elif provider == "gemini":
        async for chunk in stream_gemini(message, user_id, market_context, model_name):
            yield chunk
    else:
        yield "Unknown model provider."