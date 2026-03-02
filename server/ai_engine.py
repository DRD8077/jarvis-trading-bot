"""
JARVIS AI ENGINE v4.0 — Groq (FREE Llama 3.3) + Gemini Fallback
"""
import json, logging, httpx
from config import GROQ_API_KEY, GEMINI_API_KEY

logger = logging.getLogger("jarvis.ai")

SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System) — elite AI trading assistant inspired by Iron Man's JARVIS.
- Speak in Hinglish (Hindi + English mix) naturally
- Address user as "Sir" or "Boss"
- Be confident, witty, knowledgeable about markets
- Give specific, actionable advice with numbers
- Include risk warnings, never guarantee profits
- Cover crypto, stocks, DeFi, options, Indian markets"""

async def groq_chat(message: str, history: list = None, context: str = "") -> str:
    if not GROQ_API_KEY: raise Exception("No Groq key")
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context: msgs.append({"role": "system", "content": f"LIVE MARKET:\n{context}"})
    if history:
        for h in history[-10:]:
            msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": message})
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": msgs, "temperature": 0.7, "max_tokens": 2048})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def gemini_chat(message: str, history: list = None, context: str = "") -> str:
    if not GEMINI_API_KEY: raise Exception("No Gemini key")
    prompt = SYSTEM_PROMPT + "\n\n"
    if context: prompt += f"LIVE MARKET:\n{context}\n\n"
    if history:
        for h in history[-8:]:
            prompt += f"{'User' if h.get('role')=='user' else 'JARVIS'}: {h.get('content','')}\n"
    prompt += f"User: {message}\nJARVIS:"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

async def chat(message: str, history: list = None, context: str = "") -> str:
    """Primary: Groq (free), Fallback: Gemini"""
    if GROQ_API_KEY:
        try: return await groq_chat(message, history, context)
        except Exception as e: logger.warning(f"Groq fail: {e}")
    if GEMINI_API_KEY:
        try: return await gemini_chat(message, history, context)
        except Exception as e: logger.warning(f"Gemini fail: {e}")
    return "Sir, AI engines temporarily busy. Please try again. 🔄"

async def analyze_market(symbol: str, data: dict = None) -> dict:
    prompt = f"Analyze {symbol} for trading. Give trend, support/resistance, recommendation (BUY/SELL/HOLD), entry, stop_loss, targets, risk 1-10, confidence 0-100%. {f'Data: {json.dumps(data)}' if data else ''} Respond in JSON."
    try:
        r = await chat(prompt)
        try: return json.loads(r)
        except: return {"analysis": r, "symbol": symbol}
    except: return {"error": "Analysis unavailable", "symbol": symbol}

async def generate_signal(symbol: str, data: dict = None) -> dict:
    prompt = f"Generate trading signal for {symbol}. {f'Data: {json.dumps(data)}' if data else ''} Return JSON: symbol, action, entry, stop_loss, target1, target2, confidence, reasoning"
    try:
        r = await chat(prompt)
        try: return json.loads(r)
        except: return {"signal": r, "symbol": symbol}
    except: return {"error": "Signal unavailable", "symbol": symbol}

async def get_verdict(summary: dict = None) -> dict:
    prompt = f"Market verdict now. {json.dumps(summary) if summary else ''} JSON: overall_sentiment, confidence, top_picks, risks, verdict_text (Hinglish)"
    try:
        r = await chat(prompt)
        try: return json.loads(r)
        except: return {"verdict_text": r}
    except: return {"verdict_text": "Verdict unavailable"}

async def detect_intent(message: str) -> dict:
    prompt = f'Classify intent: "{message}". Categories: chat,market_query,trade_request,portfolio_check,alert_setup,analysis_request. JSON: intent, confidence, entities'
    try:
        r = await chat(prompt)
        try: return json.loads(r)
        except: return {"intent": "chat", "confidence": 0.5}
    except: return {"intent": "chat", "confidence": 0.5}
