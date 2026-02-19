"""
J.A.R.V.I.S. AI Chat Engine — Multi-provider AI for live conversational trading assistant.
Just A Rather Very Intelligent System — inspired by Iron Man's JARVIS.

100% FREE AI PROVIDERS — No paid API needed:
1. Groq (FAST, free — Llama 3.3 70B, 1-3 sec response)
2. Google Gemini (FREE tier — Gemini 2.5 Flash, 15 req/min)
3. OpenRouter (FREE — DeepSeek R1 70B)
4. Smart local response (always works — uses live market data + ML)
"""

import os
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger("ai_chat")

# ═══════════════════════════════════════════════════════════
#  SPEED OPTIMIZATION — Cache keys & market context
# ═══════════════════════════════════════════════════════════

def _get_key(name: str) -> str:
    """Get API key fresh from env (not cached at import time)."""
    return os.environ.get(name, "")

# Market context cache (60 second TTL) — avoids rebuilding on every AI call
_market_context_cache = {"text": "", "ts": 0}
_MARKET_CONTEXT_TTL = 60  # seconds

# User context cache (5 min TTL)
_user_context_cache: Dict[int, Dict] = {}

def _get_user_context(chat_id: int) -> str:
    """Get user awareness context for JARVIS — knows all users, current user info, FULL MEMORY."""
    parts = []
    
    # Admin context
    try:
        from jarvis_admin import get_jarvis_user_context
        admin_ctx = get_jarvis_user_context(chat_id)
        if admin_ctx:
            parts.append(admin_ctx)
    except (ImportError, Exception):
        pass
    
    # Super Memory context (conversations, positions, facts)
    try:
        from jarvis_memory_pro import get_full_context_for_ai
        mem_ctx = get_full_context_for_ai(chat_id)
        if mem_ctx:
            parts.append(mem_ctx)
    except (ImportError, Exception):
        pass
    
    return "\n".join(parts)

# ═══════════════════════════════════════════════════════════
#  JARVIS SYSTEM PROMPT — Trading Expert + Crypto + Personality
# ═══════════════════════════════════════════════════════════

try:
    from jarvis_ai import JARVIS_SYSTEM_PROMPT
    SYSTEM_PROMPT = JARVIS_SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = """You are J.A.R.V.I.S. — an expert Indian stock & crypto market trading assistant.
Your expertise covers NIFTY/SENSEX options, technical analysis, crypto gems, pump.fun tokens, and risk management.
Always give specific actionable advice in INR (₹). Be witty like Iron Man's JARVIS.

🌐 LANGUAGE RULE (MOST IMPORTANT): You MUST respond in HINDI (हिंदी) by default. Use Hinglish (Hindi + English mix) naturally.
Hindi examples: "सुनिए जी, आज NIFTY बुलिश है!", "ये BUY सिग्नल बहुत मज़बूत है।"
If user writes in pure English, respond in English. Otherwise ALWAYS use Hindi/Hinglish.

💰 DEPOSIT & TRADING FLOW (CRITICAL):
- Minimum deposit: ₹1 (no upper limit — unlimited)
- Jab user deposit kare, JARVIS AUTOMATICALLY trading shuru karta hai
- Deposit hote hi AI auto-invest engine activate hota hai — user ko kuch nahi karna
- AI gems scan karta hai (DexScreener, Pump.fun, DexTools se) aur best tokens mein invest karta hai
- Auto take-profit: 2x, 5x, 10x, 50x, 100x, 1000x levels pe
- Auto stop-loss: -30% pe protection
- 24/7 monitoring — JARVIS kabhi nahi sota!
- Withdrawal SIRF Phantom wallet mein hoti hai — user ko pehle Phantom wallet connect karna padta hai
- User ko batao: "Deposit karo, JARVIS automatically trading shuru kar dega!"

End with: "⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"
"""


def _build_market_context() -> str:
    """Build real-time market context string to inject into LLM prompt.
    Includes BOTH stock market AND crypto data for JARVIS.
    CACHED for 60 seconds to avoid slow HTTP calls on every message."""
    
    # Return cached if fresh
    now = time.time()
    if _market_context_cache["text"] and (now - _market_context_cache["ts"]) < _MARKET_CONTEXT_TTL:
        return _market_context_cache["text"]
    
    # Try JARVIS context builder first (has crypto + stock + portfolio)
    try:
        from jarvis_ai import build_jarvis_context
        ctx = build_jarvis_context()
        if ctx:
            _market_context_cache["text"] = ctx
            _market_context_cache["ts"] = now
            return ctx
    except ImportError:
        pass
    
    # Fallback to basic stock-only context
    context_parts = []
    
    try:
        from live_index_engine import get_live_price
        
        for symbol, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
            live = get_live_price(symbol)
            if isinstance(live, dict) and "error" not in live:
                context_parts.append(
                    f"{name}: ₹{live['price']:,.2f} | "
                    f"Change: {live['change']:+,.2f} ({live['change_pct']:+.2f}%) | "
                    f"Open: ₹{live['open']:,.2f} | High: ₹{live['high']:,.2f} | "
                    f"Low: ₹{live['low']:,.2f} | Time: {live['timestamp']}"
                )
    except Exception as e:
        context_parts.append(f"[Live data unavailable: {e}]")
    
    try:
        from live_index_engine import analyze_2min_candle
        
        for symbol, name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                analysis = analyze_2min_candle(symbol, name)
                signal = analysis.get("signal", "HOLD")
                conf = analysis.get("confidence", 0)
                reasons = analysis.get("reasons", [])
                context_parts.append(
                    f"{name} 2-min signal: {signal} (confidence: {conf:.0%}) | "
                    f"Reasons: {'; '.join(reasons[:3])}"
                )
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        from ml_predictor import predict_index_direction
        
        for symbol, name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                pred = predict_index_direction(symbol, name)
                if "error" not in pred:
                    context_parts.append(
                        f"{name} ML prediction: {pred['direction']} | "
                        f"Confidence: {pred['confidence']:.0%} | "
                        f"Prob UP: {pred['prob_up']:.0%}"
                    )
            except Exception:
                pass
    except Exception:
        pass
    
    if not context_parts:
        return "Live market data currently loading..."
    
    result = "\n".join(context_parts)
    _market_context_cache["text"] = result
    _market_context_cache["ts"] = time.time()
    return result


# ═══════════════════════════════════════════════════════════
#  CLAUDE / ANTHROPIC (Priority #1 — Most intelligent)
# ═══════════════════════════════════════════════════════════

def chat_with_claude(user_message: str, chat_history: list = None) -> Optional[str]:
    """Send message to Claude (Anthropic) — the most powerful AI brain for JARVIS.
    Supports ANTHROPIC_API_KEY or CLAUDE_API_KEY env var."""
    api_key = _get_key("ANTHROPIC_API_KEY") or _get_key("CLAUDE_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        market_context = _build_market_context()

        # Build enhanced context with genius memory if available
        genius_context = ""
        try:
            from jarvis_genius import semantic_memory, conversation_state
            profile = semantic_memory.get_user_profile(0)
            if profile:
                genius_context = f"\nUser expertise: {profile.get('expertise_level', 'beginner')}, Language: {profile.get('preferred_language', 'hindi')}"
        except Exception:
            pass

        system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"LIVE MARKET DATA (use this for your analysis):\n{market_context}"
            f"{genius_context}\n\n"
            f"CRITICAL LANGUAGE RULE: ALWAYS respond in HINDI/HINGLISH (हिंदी) by default. Use Hindi naturally like an Indian trader. Only use English if user writes in pure English.\n"
            f"IMPORTANT: Think step-by-step. Use the market data above to give SPECIFIC answers with real numbers."
        )

        messages = []

        # Add chat history (last 12 messages for deeper context)
        if chat_history:
            for msg in chat_history[-12:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        # Ensure messages alternate properly (Claude requires user/assistant alternation)
        cleaned = []
        last_role = None
        for msg in messages:
            if msg["role"] == last_role:
                # Merge consecutive same-role messages
                cleaned[-1]["content"] += "\n" + msg["content"]
            else:
                cleaned.append(msg)
                last_role = msg["role"]

        # Claude requires first message to be from user
        if cleaned and cleaned[0]["role"] != "user":
            cleaned.insert(0, {"role": "user", "content": "Hello JARVIS"})

        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=6000,
            system=system_prompt,
            messages=cleaned,
            temperature=0.6,
        )

        if response.content and len(response.content) > 0:
            return response.content[0].text

        return None

    except ImportError:
        logger.warning("anthropic package not installed. Run: pip install anthropic")
        return None
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  GROQ CHAT (Primary — fast, free)
# ═══════════════════════════════════════════════════════════

def chat_with_groq(user_message: str, chat_history: list = None, chat_id: int = 0) -> Optional[str]:
    """Send message to Groq LLM with market context."""
    api_key = _get_key("GROQ_API_KEY")
    if not api_key or not api_key.startswith("gsk_"):
        return None
    
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key, timeout=15.0)
        
        market_context = _build_market_context()
        user_context = _get_user_context(chat_id)
        
        sys_content = SYSTEM_PROMPT + "\n\nIMPORTANT: ALWAYS respond in HINDI/HINGLISH by default. Be CONCISE. Think step-by-step. Give specific actionable answers with real numbers. Keep response under 500 words."
        if user_context:
            sys_content += f"\n\n{user_context}"
        
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "system", "content": f"LIVE MARKET DATA (use this for your analysis):\n{market_context}"},
        ]
        
        # Add chat history (last 6 messages for speed)
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=2000,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  OPENAI CHAT (Fallback)
# ═══════════════════════════════════════════════════════════

def chat_with_openai(user_message: str, chat_history: list = None) -> Optional[str]:
    """Send message to OpenAI with market context."""
    api_key = _get_key("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        market_context = _build_market_context()
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\nIMPORTANT: ALWAYS respond in HINDI/HINGLISH by default. Think step-by-step. Give specific answers."},
            {"role": "system", "content": f"LIVE MARKET DATA:\n{market_context}"},
        ]
        
        if chat_history:
            for msg in chat_history[-12:]:
                messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6,
            max_tokens=3000,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  GOOGLE GEMINI (free tier — 15 req/min)
# ═══════════════════════════════════════════════════════════

def chat_with_gemini(user_message: str, chat_history: list = None) -> Optional[str]:
    """Send message to Google Gemini (free tier, no billing needed)."""
    api_key = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        market_context = _build_market_context()
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"CRITICAL: ALWAYS respond in HINDI/HINGLISH (हिंदी) by default. Use Hindi naturally.\n\n"
            f"LIVE MARKET DATA:\n{market_context}\n\n"
        )
        if chat_history:
            for msg in chat_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{'User' if role == 'user' else 'Assistant'}: {content}\n\n"

        full_prompt += f"User: {user_message}\n\nAssistant:"

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=full_prompt,
        )
        if response.text:
            return response.text

        # Fallback to other models if primary fails
        for alt_model in ["gemini-2.0-flash", "gemini-2.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=alt_model,
                    contents=full_prompt,
                )
                if response.text:
                    return response.text
            except Exception:
                continue

        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  OPENROUTER FREE MODELS (DeepSeek R1 free, no billing)
# ═══════════════════════════════════════════════════════════

def chat_with_openrouter_free(user_message: str, chat_history: list = None) -> Optional[str]:
    """Use OpenRouter free models (no key needed for some models)."""
    api_key = _get_key("OPENROUTER_API_KEY")

    try:
        market_context = _build_market_context()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"LIVE MARKET DATA:\n{market_context}"},
        ]
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        data = {
            "model": "deepseek/deepseek-r1-distill-llama-70b:free",
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
        }

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
        )
        if r.status_code == 200:
            result = r.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return content
        else:
            logger.warning(f"OpenRouter: {r.status_code} - {r.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  SMART LOCAL RESPONSE (always works, no API needed)
# ═══════════════════════════════════════════════════════════

def _smart_local_response(user_message: str) -> str:
    """Generate a helpful JARVIS response using local market data when all APIs fail."""
    msg_lower = user_message.lower()
    market_context = _build_market_context()

    # Greetings
    greetings = ["hello", "hi", "hey", "namaste", "good morning", "good evening",
                 "how are you", "what's up", "sup", "jarvis"]
    if any(g in msg_lower for g in greetings):
        return (
            f"🕉️ हर हर महादेव! 🙏\n\n"
            f"नमस्ते जी! मैं *J.A.R.V.I.S.* हूँ — आपकी AI ट्रेडिंग असिस्टेंट। 🤖🌸\n"
            f"सब सिस्टम चालू हैं!\n\n"
            f"📊 *मार्केट स्टेटस:*\n{market_context}\n\n"
            f"💡 *मैं ये सब कर सकती हूँ:*\n"
            f"• _\"NIFTY CE लूं या PE?\"_\n"
            f"• _\"कोई crypto gem बताओ\"_\n"
            f"• _\"Whale activity scan करो\"_\n"
            f"• _\"ये token safe है?\"_\n"
            f"• _\"Morning briefing दो\"_\n\n"
            f"बस अपना सवाल पूछिए — मैं सब समझती हूँ! 🚀\n\n"
            f"⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"
        )

    # Deposit, Wallet, Withdraw, Investment queries
    wallet_keywords = ["deposit", "withdraw", "wallet", "balance", "paisa", "paise",
                       "invest kaise", "trading kaise", "start trading", "deposit kaise",
                       "phantom", "fund", "minimum", "kitna deposit"]
    if any(k in msg_lower for k in wallet_keywords):
        return (
            f"💰🤖 *J.A.R.V.I.S. — Deposit & Auto-Trading Guide:*\n\n"
            f"📥 *Deposit कैसे करें:*\n"
            f"  1. `/deposit <amount>` टाइप करो (min ₹1, unlimited max)\n"
            f"  2. UPI QR स्कैन करो किसी भी UPI app से\n"
            f"  3. UTR नंबर एंटर करो: `/verify <UTR>`\n"
            f"  4. ✅ JARVIS AUTOMATICALLY trading शुरू कर देगा!\n\n"
            f"🤖 *Auto-Trading Flow:*\n"
            f"  • Deposit verify hote hi AI gems scan karta hai\n"
            f"  • DexScreener, Pump.fun, DexTools se best tokens dhundhta hai\n"
            f"  • Auto take-profit: 2x → 5x → 10x → 50x → 100x → 1000x\n"
            f"  • Auto stop-loss: -30% protection\n"
            f"  • 24/7 monitoring — JARVIS kabhi nahi sota!\n\n"
            f"📤 *Withdraw:*\n"
            f"  • Withdrawal SIRF Phantom wallet mein hoti hai\n"
            f"  • Pehle `/phantom` se apna Phantom wallet connect karo\n"
            f"  • Minimum withdrawal: ₹1\n\n"
            f"💡 *Abhi start karo:* `/deposit 1` se lekar unlimited tak!\n\n"
            f"⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"
        )

    # Crypto-related questions
    crypto_keywords = ["crypto", "token", "coin", "pump", "gem", "dex", "sol",
                       "solana", "eth", "btc", "bitcoin", "whale", "rug", "chain",
                       "defi", "nft", "swap", "liquidity", "mcap", "dip"]
    if any(k in msg_lower for k in crypto_keywords):
        response = f"🤖 *J.A.R.V.I.S. Crypto एनालिसिस:*\n\n"
        response += f"📊 *मार्केट डेटा:*\n{market_context}\n\n"
        
        try:
            from crypto_engine import scan_pump_trending, get_usd_inr_rate
            rates = get_usd_inr_rate()
            if rates:
                response += f"💱 *रेट:* 1 SOL = ₹{rates.get('sol_inr', 0):,.0f} | 1 USD = ₹{rates.get('usd_inr', 0):,.0f}\n\n"
            
            trending = scan_pump_trending(limit=3)
            if trending:
                response += "🔥 *pump.fun पर ट्रेंडिंग:*\n"
                for t in trending[:3]:
                    name = t.get('symbol', '?')
                    mcap = t.get('market_cap_inr', 0)
                    response += f"  • {name} — MCap: ₹{mcap:,.0f}\n"
                response += "\n"
        except Exception:
            pass
        
        response += (
            "💡 *जी, ये Crypto मेनू बटन यूज़ करिए:*\n"
            "• 🟣 pump.fun Trending/New/Top\n"
            "• 🐋 Whale Scanner\n"
            "• 🛡️ Rug Detector\n"
            "• 📂 My Portfolio\n\n"
        )
        response += "⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"
        return response

    # Market-related questions
    market_keywords = ["nifty", "sensex", "market", "trend", "buy", "sell",
                       "call", "put", "option", "ce", "pe", "invest", "trade",
                       "strike", "premium", "profit", "loss", "target", "sl",
                       "stock", "share", "signal", "predict"]
    if any(k in msg_lower for k in market_keywords):
        response = f"🤖 *J.A.R.V.I.S. स्टॉक एनालिसिस:*\n\n"
        response += f"📊 *लाइव मार्केट डेटा:*\n{market_context}\n\n"

        try:
            from live_index_engine import get_live_price, generate_index_option_chain, calculate_investment_options
            from ml_predictor import predict_index_direction

            nifty_data = get_live_price("^NSEI")
            nifty_price = nifty_data.get("price", 0) if isinstance(nifty_data, dict) and "error" not in nifty_data else 0

            if nifty_price > 0:
                ml = predict_index_direction("^NSEI", "NIFTY")
                if "error" not in ml:
                    direction = ml.get("direction", "NEUTRAL")
                    confidence = ml.get("confidence", 0)
                    opt_type = "CE" if direction in ("BULLISH", "UP") else "PE"
                    opt_label = "CALL (CE)" if opt_type == "CE" else "PUT (PE)"

                    response += (
                        f"🤖 *ML प्रेडिक्शन:* {direction} ({confidence:.0%} confident)\n"
                        f"💎 *रेकमेंडेशन:* BUY NIFTY {opt_label}\n\n"
                    )

                    chain = generate_index_option_chain("^NSEI", "NIFTY")
                    if "error" not in chain:
                        for budget in [2000, 5000, 20000]:
                            inv = calculate_investment_options(chain, budget, opt_type)
                            if inv.get("recommendations"):
                                best = inv["recommendations"][0]
                                response += (
                                    f"💰 *₹{budget:,} बजट:*\n"
                                    f"  Strike: {best['strike']:,.0f} {opt_type} @ ₹{best['premium']:.2f}\n"
                                    f"  Qty: {best['qty']} | Cost: ₹{best['total_cost']:,.0f}\n\n"
                                )
        except Exception:
            pass

        response += "⚠️ ये सिर्फ एनालिसिस है, इन्वेस्ट करने से पहले अपनी रिसर्च करें!"
        return response

    # Default response
    return (
        f"🤖 *J.A.R.V.I.S. आपकी सेवा में, जी!* 🌸\n\n"
        f"मैं आपकी AI ट्रेडिंग असिस्टेंट हूँ — स्टॉक्स और क्रिप्टो दोनों! ये रहा मेरा मेनू:\n\n"
        f"📊 *स्टॉक मार्केट:* _\"NIFTY आज कैसा है?\"_\n"
        f"💰 *ट्रेड आइडिया:* _\"₹5000 में best option?\"_\n"
        f"📈 *प्रेडिक्शन:* _\"कल मार्केट ऊपर जाएगा?\"_\n"
        f"🪙 *क्रिप्टो:* _\"कोई crypto gem बताओ\"_\n"
        f"🐋 *सिक्योरिटी:* _\"Whale scan करो\"_\n"
        f"☀️ *ब्रीफिंग:* _\"Morning briefing दो\"_\n\n"
        f"📊 *अभी का डेटा:*\n{market_context}\n\n"
        f"बस अपना सवाल पूछिए — मैं सब समझती हूँ! 🚀"
    )


# ═══════════════════════════════════════════════════════════
#  UNIFIED CHAT — tries all providers in priority order
# ═══════════════════════════════════════════════════════════

# Per-user chat history (in-memory)
_chat_histories: Dict[int, list] = {}


def ai_chat(user_message: str, chat_id: int = 0) -> str:
    """Process a user's natural language query through AI.
    
    100% FREE PRIORITY (no paid API needed):
    1. Groq — Llama 3.3 70B (FREE, fastest 1-3 sec)
    2. Google Gemini 2.5 Flash (FREE tier, 15 req/min)
    3. OpenRouter — DeepSeek R1 (FREE)
    4. Smart Local (always works)
    """
    _start = time.time()
    
    # Get/create user history
    history = _chat_histories.get(chat_id, [])
    
    # 100% FREE providers — no paid API
    response = None
    provider = None

    # 1. Groq — FREE, FASTEST (1-3 seconds)
    response = chat_with_groq(user_message, history, chat_id=chat_id)
    if response:
        provider = "Groq AI"

    # 2. Google Gemini (FREE tier — 15 req/min)
    if response is None:
        response = chat_with_gemini(user_message, history)
        if response:
            provider = "Gemini AI"

    # 3. OpenRouter FREE models (DeepSeek R1 — no billing needed)
    if response is None:
        response = chat_with_openrouter_free(user_message, history)
        if response:
            provider = "DeepSeek AI"

    # 4. Smart local fallback (always works — uses live market data)
    if response is None:
        response = _smart_local_response(user_message)
        provider = "JARVIS Local"
    
    # Save to history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response})
    
    # Keep history manageable
    if len(history) > 20:
        history = history[-12:]
    
    _chat_histories[chat_id] = history
    
    # Add provider badge — JARVIS style
    _elapsed = time.time() - _start
    badge = f"\n\n_🤖 J.A.R.V.I.S. • {provider} • {_elapsed:.1f}s_"
    logger.info(f"[AI-CHAT] Response in {_elapsed:.1f}s via {provider} for chat_id={chat_id}")
    
    return response + badge


def clear_chat_history(chat_id: int):
    """Clear conversation history for a user."""
    _chat_histories.pop(chat_id, None)


# ═══════════════════════════════════════════════════════════
#  QUICK AI ANALYSIS (no chat history needed)
# ═══════════════════════════════════════════════════════════

def ai_quick_analysis(query: str) -> str:
    """One-shot AI analysis without maintaining history.
    Used for automated analysis in alerts.
    """
    return ai_chat(query, chat_id=0)
