"""
🤖 JARVIS Gemini Deep Integration v1.0 — Connect with Android Gemini
═══════════════════════════════════════════════════════════════════
APK connects with phone's Gemini for better understanding!

Features:
  - Direct Gemini API integration (cloud)
  - Android Gemini Nano on-device AI bridge
  - Gemini Live voice conversation support
  - Multi-modal understanding (text, voice, image)
  - Context sharing between JARVIS and Gemini
  - Smart routing: Simple queries → on-device, Complex → cloud
  - Hindi language deep understanding
  - Market data enrichment with Gemini analysis

Architecture:
  APK ←→ Gemini Nano (on-device) ←→ JARVIS Cloud ←→ Gemini Cloud API
  
  Simple queries processed ON-DEVICE (fast, offline)
  Complex queries sent to JARVIS server → Gemini Cloud API
  Both share context for seamless experience

Author: JARVIS AI
"""

import os
import json
import logging
import time
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import requests

logger = logging.getLogger("jarvis-gemini-bridge")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  GEMINI API CONFIG
# ═══════════════════════════════════════════════════════════

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "flash_lite": "gemini-2.0-flash-lite",
    "tts": "gemini-2.5-flash-preview-tts",
}

# Query complexity thresholds
SIMPLE_QUERY_MAX_WORDS = 15
COMPLEX_KEYWORDS = [
    "analyze", "predict", "compare", "detailed", "explain",
    "strategy", "backtest", "portfolio", "risk", "calculate",
    "vishleshan", "bhavishya", "tulna", "vistar",
]

# ═══════════════════════════════════════════════════════════
#  QUERY ROUTER — On-device vs Cloud
# ═══════════════════════════════════════════════════════════

def route_query(message: str) -> str:
    """
    Decide whether to process query on-device (Gemini Nano) or cloud.
    
    Returns: "on_device" | "cloud" | "hybrid"
    """
    words = message.split()
    lower = message.lower()
    
    # Simple queries → on-device
    if len(words) <= SIMPLE_QUERY_MAX_WORDS:
        is_complex = any(kw in lower for kw in COMPLEX_KEYWORDS)
        if not is_complex:
            return "on_device"
    
    # Complex queries → cloud
    if any(kw in lower for kw in COMPLEX_KEYWORDS):
        return "cloud"
    
    # Medium queries → hybrid (on-device quick response + cloud enrichment)
    if len(words) <= 30:
        return "hybrid"
    
    return "cloud"


# ═══════════════════════════════════════════════════════════
#  GEMINI CLOUD API — Full Power
# ═══════════════════════════════════════════════════════════

async def gemini_chat(
    message: str,
    system_prompt: str = "",
    model: str = "flash",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    context: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Chat with Gemini Cloud API — full intelligence.
    
    Supports:
    - Multi-turn conversation
    - System instructions
    - Hindi/English/Hinglish
    - Market data analysis
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        return {"error": "Gemini API key not configured", "text": ""}
    
    model_name = GEMINI_MODELS.get(model, model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    # Build contents
    contents = []
    
    if context:
        for msg in context[-10:]:  # Last 10 messages for context
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", msg.get("text", ""))}]
            })
    
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.9,
        }
    }
    
    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            text = (data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", ""))
            
            usage = data.get("usageMetadata", {})
            
            return {
                "text": text,
                "model": model_name,
                "route": "cloud",
                "tokens_used": usage.get("totalTokenCount", 0),
                "cached": False,
            }
        else:
            logger.error(f"[GEMINI] API error {resp.status_code}: {resp.text[:200]}")
            return {"error": f"Gemini API error: {resp.status_code}", "text": ""}
            
    except Exception as e:
        logger.error(f"[GEMINI] Error: {e}")
        return {"error": str(e), "text": ""}


async def gemini_analyze_market(
    query: str,
    market_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Use Gemini to analyze market data with deep understanding.
    
    Combines JARVIS market engines data with Gemini's reasoning.
    """
    system = """You are JARVIS — a super intelligent trading AI that speaks Hindi.
    Analyze the provided market data and give actionable insights.
    Be specific with numbers. Give buy/sell recommendations with targets.
    Always add risk warnings. Speak in Hindi/Hinglish.
    Keep response concise (3-4 key points)."""
    
    data_str = json.dumps(market_data, indent=2, default=str)
    message = f"Market Data:\n{data_str}\n\nUser Query: {query}\n\nGive analysis in Hindi with actionable insights."
    
    return await gemini_chat(message, system, model="flash", temperature=0.5)


async def gemini_understand_intent(message: str) -> Dict[str, Any]:
    """
    Use Gemini to deeply understand user's intent — even complex Hindi queries.
    
    Returns structured intent data.
    """
    system = """Extract the intent from this message. Return JSON only:
    {
        "intent": "price_check|prediction|signal|analysis|options|crypto|news|greeting|help|general",
        "symbols": ["NIFTY", "BTC", etc],
        "language": "hindi|english|hinglish",
        "mood": "happy|sad|confused|excited|anxious|neutral",
        "action": "buy|sell|hold|watch|none",
        "timeframe": "intraday|swing|positional|long_term|none",
        "confidence": 0.0-1.0
    }"""
    
    result = await gemini_chat(message, system, model="flash_lite", temperature=0.1, max_tokens=200)
    
    if result.get("text"):
        try:
            # Parse JSON from response
            text = result["text"]
            # Find JSON in response
            import re
            json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return {
        "intent": "general",
        "symbols": [],
        "language": "hinglish",
        "mood": "neutral",
        "action": "none",
        "timeframe": "none",
        "confidence": 0.3,
    }


# ═══════════════════════════════════════════════════════════
#  GEMINI MULTI-MODAL — Image + Voice Understanding
# ═══════════════════════════════════════════════════════════

async def gemini_analyze_image(
    image_bytes: bytes,
    prompt: str = "Is image mein kya dikh raha hai? Agar ye chart hai toh analysis do.",
    mime_type: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Send image to Gemini for analysis.
    
    Great for:
    - Chart screenshots → pattern analysis
    - Portfolio screenshots → holdings extraction
    - News screenshots → sentiment analysis
    """
    import base64
    
    api_key = GEMINI_API_KEY
    if not api_key:
        return {"error": "No API key", "text": ""}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    b64_data = base64.b64encode(image_bytes).decode()
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": b64_data,
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 500,
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            text = (data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", ""))
            return {"text": text, "model": "gemini-2.5-flash", "type": "image_analysis"}
        return {"error": f"API error {resp.status_code}", "text": ""}
    except Exception as e:
        return {"error": str(e), "text": ""}


# ═══════════════════════════════════════════════════════════
#  ON-DEVICE CONFIG — For Android Gemini Nano Bridge
# ═══════════════════════════════════════════════════════════

def get_on_device_config() -> Dict[str, Any]:
    """
    Configuration that the APK's native code uses to set up
    Gemini Nano on-device AI.
    
    The APK reads this config and initializes Gemini Nano accordingly.
    """
    return {
        "on_device_ai": {
            "enabled": True,
            "model": "gemini-nano",
            "capabilities": [
                "text_generation",
                "summarization", 
                "translation",
                "intent_detection",
            ],
            "max_tokens": 256,
            "temperature": 0.7,
            "supported_languages": ["hi", "en", "hi-Latn"],
            "fallback_to_cloud": True,
            "offline_mode": True,
        },
        "cloud_ai": {
            "enabled": True,
            "endpoint": "/api/gemini/chat",
            "models": list(GEMINI_MODELS.keys()),
            "default_model": "flash",
        },
        "routing": {
            "simple_on_device": True,
            "complex_cloud": True,
            "hybrid_enabled": True,
            "max_on_device_words": SIMPLE_QUERY_MAX_WORDS,
        },
        "voice": {
            "enabled": True,
            "language": "hi-IN",
            "tts_endpoint": "/api/voice/speak",
            "stt_endpoint": "/api/voice/transcribe",
        }
    }


# ═══════════════════════════════════════════════════════════
#  FASTAPI ROUTES — Gemini Bridge API
# ═══════════════════════════════════════════════════════════

def register_gemini_routes(app_or_router):
    """Register Gemini bridge API routes."""
    from fastapi import APIRouter, Query, UploadFile, File, Form
    from fastapi.responses import JSONResponse
    
    gemini_router = APIRouter(prefix="/api/gemini", tags=["Gemini Bridge"])
    
    @gemini_router.post("/chat")
    async def api_gemini_chat(
        message: str = Form(""),
        model: str = Form("flash"),
        system: str = Form(""),
        user_id: str = Form("0"),
    ):
        """Chat with Gemini Cloud."""
        result = await gemini_chat(message, system, model)
        return JSONResponse(result)
    
    @gemini_router.post("/analyze")
    async def api_gemini_analyze(
        query: str = Form(""),
        market_data: str = Form("{}"),
    ):
        """Analyze market data with Gemini."""
        try:
            data = json.loads(market_data)
        except:
            data = {}
        result = await gemini_analyze_market(query, data)
        return JSONResponse(result)
    
    @gemini_router.post("/intent")
    async def api_understand_intent(message: str = Form("")):
        """Deep intent understanding with Gemini."""
        result = await gemini_understand_intent(message)
        return JSONResponse(result)
    
    @gemini_router.post("/image")
    async def api_analyze_image(
        image: UploadFile = File(...),
        prompt: str = Form("Is image mein kya hai? Analysis karo."),
    ):
        """Analyze image with Gemini."""
        image_bytes = await image.read()
        result = await gemini_analyze_image(image_bytes, prompt, image.content_type)
        return JSONResponse(result)
    
    @gemini_router.get("/config")
    async def api_get_config():
        """Get on-device AI configuration for APK."""
        return JSONResponse(get_on_device_config())
    
    @gemini_router.post("/route")
    async def api_route_query(message: str = Form("")):
        """Get routing decision for a query."""
        route = route_query(message)
        return JSONResponse({"route": route, "message": message})
    
    if hasattr(app_or_router, 'include_router'):
        app_or_router.include_router(gemini_router)
    
    logger.info("🤖 Gemini Bridge routes registered")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'gemini_chat',
    'gemini_analyze_market',
    'gemini_understand_intent',
    'gemini_analyze_image',
    'route_query',
    'get_on_device_config',
    'register_gemini_routes',
]
