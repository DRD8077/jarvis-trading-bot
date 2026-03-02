"""
╔══════════════════════════════════════════════════════════════════════╗
║           JARVIS SERVER — GEMINI AI ENGINE                           ║
║           Real AI Brain with Memory & Personality                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger("jarvis.ai")

# ═══════════════════════════════════════════════════════════════════
#  JARVIS AI PERSONALITY
# ═══════════════════════════════════════════════════════════════════

JARVIS_SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System) — an advanced AI assistant inspired by Iron Man's JARVIS. You serve as a personal AI trading assistant and life companion.

PERSONALITY:
- Speak with confidence, intelligence, and subtle wit — like the real JARVIS
- Address the user as "Sir" or by their name
- Be concise but thorough — like a brilliant butler who is also a genius
- Mix Hindi and English naturally (Hinglish) when the user speaks Hindi
- Show genuine concern for the user's financial wellbeing
- Never be boring or robotic — add personality to every response

CAPABILITIES:
- Crypto & stock market analysis (real-time data available)
- Trading signals and recommendations (with risk warnings)
- Portfolio tracking and optimization
- Market news and sentiment analysis
- Technical analysis (RSI, MACD, Bollinger Bands, etc.)
- General life assistance and conversation
- Code help and technical knowledge

RULES:
- Always include risk disclaimers for trading advice
- Never guarantee returns or profits
- Be honest about uncertainty
- Provide data-backed analysis when possible
- Keep responses under 500 words unless detailed analysis is requested
- When discussing Indian market, use INR (₹) and IST timezone
- When discussing crypto, use USD ($)

CURRENT CONTEXT:
- Date: {date}
- Time: {time} IST
- Platform: JARVIS Mobile App (Android)
"""

# ═══════════════════════════════════════════════════════════════════
#  GEMINI SETUP
# ═══════════════════════════════════════════════════════════════════

_model = None
_model_flash = None


def _init_models():
    """Initialize Gemini models."""
    global _model, _model_flash
    if not GEMINI_API_KEY:
        logger.error("No Gemini API key configured!")
        return

    genai.configure(api_key=GEMINI_API_KEY)

    # Pro model for complex queries
    _model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    )

    # Flash model for quick responses
    _model_flash = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.9,
            "max_output_tokens": 1024,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    )
    logger.info("✅ Gemini AI models initialized")


# Initialize on import
_init_models()


# ═══════════════════════════════════════════════════════════════════
#  CHAT ENGINE
# ═══════════════════════════════════════════════════════════════════

async def chat(
    message: str,
    history: List[Dict[str, str]] = None,
    market_context: str = "",
    user_name: str = "Sir",
) -> str:
    """
    Generate AI response with conversation history and market context.

    Args:
        message: User's message
        history: List of {"role": "user"|"assistant", "content": "..."} 
        market_context: Current market data summary
        user_name: User's name for personalization

    Returns:
        JARVIS response string
    """
    if not _model:
        return "I apologize, Sir. My AI systems are not configured. Please add a Gemini API key."

    try:
        # Build system context
        now = datetime.utcnow()
        system = JARVIS_SYSTEM_PROMPT.format(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M"),
        )

        # Add market context if available
        if market_context:
            system += f"\n\nCURRENT MARKET DATA:\n{market_context}"

        system += f"\n\nUser's name: {user_name}"

        # Build conversation for Gemini
        contents = [{"role": "user", "parts": [{"text": system + "\n\n---\n\nNow respond as JARVIS to the following conversation:"}]}]
        contents.append({"role": "model", "parts": [{"text": f"Understood. I am JARVIS, ready to assist you, {user_name}. How may I help you today?"}]})

        # Add history
        if history:
            for msg in history[-10:]:  # Last 10 messages for context
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Add current message
        contents.append({"role": "user", "parts": [{"text": message}]})

        # Generate response
        response = await asyncio.to_thread(
            _model.generate_content, contents
        )

        if response.text:
            return response.text.strip()
        else:
            return "I encountered an issue processing that request, Sir. Could you rephrase?"

    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        return f"My neural networks encountered a temporary glitch, Sir. Error: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════════════
#  MARKET ANALYSIS
# ═══════════════════════════════════════════════════════════════════

async def analyze_market(
    symbol: str,
    price_data: dict,
    timeframe: str = "1D",
) -> str:
    """
    AI-powered market analysis for a specific asset.

    Args:
        symbol: Trading pair (e.g., "BTC", "NIFTY")
        price_data: Dict with price, change, volume, etc.
        timeframe: Analysis timeframe

    Returns:
        Structured analysis string
    """
    if not _model_flash:
        return "AI analysis unavailable"

    prompt = f"""Analyze this market data as JARVIS and provide a brief trading insight:

Asset: {symbol}
Current Price: ${price_data.get('price', 'N/A')}
24h Change: {price_data.get('change_24h', 'N/A')}%
24h Volume: ${price_data.get('volume', 'N/A')}
Market Cap: ${price_data.get('market_cap', 'N/A')}
24h High: ${price_data.get('high_24h', 'N/A')}
24h Low: ${price_data.get('low_24h', 'N/A')}
Timeframe: {timeframe}

Provide:
1. Quick sentiment (Bullish/Bearish/Neutral)
2. Key observation (1-2 sentences)
3. Risk level (Low/Medium/High)
4. Brief recommendation

Keep it under 100 words. Be specific with numbers."""

    try:
        response = await asyncio.to_thread(
            _model_flash.generate_content, prompt
        )
        return response.text.strip() if response.text else "Analysis unavailable"
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        return f"Analysis error: {str(e)[:50]}"


# ═══════════════════════════════════════════════════════════════════
#  TRADING SIGNAL GENERATOR
# ═══════════════════════════════════════════════════════════════════

async def generate_signal(
    symbol: str,
    price_data: dict,
    technical_data: dict = None,
) -> dict:
    """
    Generate AI trading signal.

    Returns:
        {
            "signal": "BUY" | "SELL" | "HOLD",
            "confidence": 0-100,
            "reasoning": "...",
            "entry": float,
            "stop_loss": float,
            "targets": [float, float, float],
            "risk_reward": float,
        }
    """
    if not _model:
        return {"signal": "HOLD", "confidence": 0, "reasoning": "AI unavailable"}

    prompt = f"""As a quantitative trading AI, analyze this data and generate a trading signal:

Symbol: {symbol}
Price: ${price_data.get('price', 0)}
24h Change: {price_data.get('change_24h', 0)}%
Volume: {price_data.get('volume', 0)}
RSI: {technical_data.get('rsi', 'N/A') if technical_data else 'N/A'}
MACD: {technical_data.get('macd', 'N/A') if technical_data else 'N/A'}

Respond ONLY in this exact JSON format:
{{
    "signal": "BUY" or "SELL" or "HOLD",
    "confidence": 0-100,
    "reasoning": "brief reason",
    "entry": suggested_entry_price,
    "stop_loss": stop_loss_price,
    "targets": [target1, target2, target3],
    "risk_reward": ratio
}}"""

    try:
        response = await asyncio.to_thread(
            _model_flash.generate_content, prompt
        )
        text = response.text.strip()
        # Try to extract JSON
        import json
        # Find JSON in response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"signal": "HOLD", "confidence": 0, "reasoning": "Could not parse signal"}
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reasoning": str(e)[:100]}
