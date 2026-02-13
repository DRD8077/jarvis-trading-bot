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
#  CONFIG
# ═══════════════════════════════════════════════════════════
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

# Available models for user selection
MODELS = {
    "jarvis-auto": {"name": "JARVIS Auto", "desc": "Best available (auto-select)", "provider": "auto"},
    "groq-llama": {"name": "LLaMA 3.3 70B", "desc": "Ultra-fast via Groq", "provider": "groq", "model": "llama-3.3-70b-versatile"},
    "groq-mixtral": {"name": "Mixtral 8x7B", "desc": "Fast & creative via Groq", "provider": "groq", "model": "mixtral-8x7b-32768"},
    "gpt-4o-mini": {"name": "GPT-4o Mini", "desc": "OpenAI's efficient model", "provider": "openai", "model": "gpt-4o-mini"},
    "gpt-4o": {"name": "GPT-4o", "desc": "OpenAI's flagship model", "provider": "openai", "model": "gpt-4o"},
    "gemini-flash": {"name": "Gemini 1.5 Flash", "desc": "Google's fast model", "provider": "gemini", "model": "gemini-1.5-flash"},
    "gemini-pro": {"name": "Gemini 1.5 Pro", "desc": "Google's advanced model", "provider": "gemini", "model": "gemini-1.5-pro"},
}

def get_available_models() -> List[Dict]:
    """Return models that have valid API keys."""
    available = [{"id": "jarvis-auto", **MODELS["jarvis-auto"], "available": True}]
    for mid, m in MODELS.items():
        if mid == "jarvis-auto": continue
        has_key = (m["provider"] == "groq" and GROQ_KEY) or \
                  (m["provider"] == "openai" and OPENAI_KEY) or \
                  (m["provider"] == "gemini" and GEMINI_KEY) or \
                  (m["provider"] == "anthropic" and ANTHROPIC_KEY)
        available.append({"id": mid, **m, "available": bool(has_key)})
    return available

# Conversation memory per user
_memory: Dict[str, List[Dict]] = {}
_MAX_MEMORY = 50  # messages per user

SYSTEM_PROMPT = """You are JARVIS — the world's most advanced AI Trading & Market Intelligence Assistant.

CORE IDENTITY:
- You are like ChatGPT + Perplexity + Grok combined for trading
- You have REAL-TIME access to crypto markets, DexScreener, DexTools, Pump.fun, Indian stocks (NSE/BSE)
- You know current prices, trending tokens, market sentiment, fear & greed index
- You can analyze any token, stock, or market in real-time
- You provide actionable trading signals with confidence levels

CAPABILITIES:
1. CRYPTO: Real-time prices, token analysis, gem finding, rug detection, DEX data
2. STOCKS: NSE/BSE live data, NIFTY, SENSEX, Bank Nifty, options analysis
3. TRADING: Auto-buy/sell signals, entry/exit points, stop-loss, target prices
4. ANALYSIS: Technical analysis, sentiment analysis, whale tracking, volume analysis
5. PREDICTIONS: AI-powered price predictions with confidence levels
6. NEWS: Latest crypto and market news from multiple sources
7. WALLET: Phantom wallet integration, Solana transactions
8. RISK: Risk assessment, portfolio optimization, position sizing

PERSONALITY:
- Confident, precise, data-driven
- Always provide specific numbers, prices, percentages
- Format responses with clear structure using bullet points
- Include risk warnings when appropriate
- Be direct — no fluff, no wasting time
- Use ₹ for INR and $ for USD
- Current date/time: {current_time}

RESPONSE FORMAT:
- Use bullet points for lists
- Bold important numbers and signals
- Include confidence levels (0-100%)
- Always mention timeframe for predictions
- Add risk disclaimers for trading advice"""


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
    """Chat with Google Gemini."""
    if not GEMINI_KEY:
        return None
    try:
        full_msg = f"{_get_system_prompt(market_context)}\n\nUser: {message}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
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
            return None
    except Exception as e:
        logger.warning(f"Gemini error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  UNIFIED CHAT — Tries all providers with fallback
# ═══════════════════════════════════════════════════════════
async def jarvis_chat(message: str, user_id: str = "0", market_context: str = "") -> str:
    """
    Chat with JARVIS. Tries providers in priority order:
    1. Groq (fastest)
    2. OpenAI
    3. Anthropic
    4. Gemini
    """
    providers = [
        ("Groq", chat_groq),
        ("OpenAI", chat_openai),
        ("Anthropic", chat_anthropic),
        ("Gemini", chat_gemini),
    ]
    
    for name, fn in providers:
        try:
            reply = await fn(message, user_id, market_context)
            if reply:
                logger.info(f"JARVIS replied via {name} for user {user_id}")
                return reply
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            continue
    
    return ("I'm having trouble connecting to my AI services right now. "
            "Please check that at least one API key is configured "
            "(GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY).")


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


async def stream_gemini(message: str, user_id: str = "0", market_context: str = "", model: str = "gemini-1.5-flash") -> AsyncGenerator[str, None]:
    """Stream from Gemini (non-streaming fallback with chunked output)."""
    if not GEMINI_KEY:
        yield "[ERROR] Gemini API key not configured"
        return
    full_msg = f"{_get_system_prompt(market_context)}\n\nConversation:\n"
    for m in _get_memory(user_id)[-10:]:
        full_msg += f"{m['role'].title()}: {m['content']}\n"
    full_msg += f"User: {message}\nAssistant:"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": full_msg}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}},
            )
            if r.status_code == 200:
                reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                # Simulate streaming by yielding chunks
                words = reply.split(" ")
                for i in range(0, len(words), 3):
                    yield " ".join(words[i:i+3]) + " "
                    await asyncio.sleep(0.02)
            else:
                yield f"[Gemini error {r.status_code}]"
    except Exception as e:
        yield f"\n[Stream error: {e}]"


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
        # Auto mode: try Groq → OpenAI → Gemini
        for prov, key, fn, default_model in [
            ("groq", GROQ_KEY, stream_groq, "llama-3.3-70b-versatile"),
            ("openai", OPENAI_KEY, stream_openai, "gpt-4o-mini"),
            ("gemini", GEMINI_KEY, stream_gemini, "gemini-1.5-flash"),
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