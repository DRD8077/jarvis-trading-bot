"""
🎙️💕 JARVIS Hindi Voice Assistant v2.0 — Super Sweet & Smiling Voice
═══════════════════════════════════════════════════════════════════
Hindi main baat karo, JARVIS samjhegi aur meethi awaaz main jawab degi!

Features:
  - Always speaks in Hindi with sweet, smiling tone
  - Emotional intelligence — detects mood & responds accordingly
  - Super natural Hindi TTS with expressions
  - Real-time voice conversation (listen → think → speak)
  - Personality: Sweet, caring, always happy & smiling
  - Understands Hindi, Hinglish, English — responds in Hindi
  - Integrates with Gemini for deep understanding
  - Context-aware responses (remembers conversation)

TTS Priority:
  1. Gemini 2.5 Flash TTS (Kore voice — sweet Hindi)
  2. OpenAI TTS-1-HD (nova — warm & natural)
  3. Edge TTS (hi-IN-SwaraNeural — free fallback)

Author: JARVIS AI
"""

import os
import re
import json
import logging
import asyncio
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

import requests

logger = logging.getLogger("hindi-voice-assistant")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  VOICE PERSONA CONFIG — Sweet & Always Smiling
# ═══════════════════════════════════════════════════════════

PERSONA = {
    "name": "JARVIS",
    "language": "hindi",
    "personality": "sweet, caring, always smiling, helpful, enthusiastic",
    "voice_style": "warm, gentle, expressive, happy",
    "greeting_style": "namaste with warmth",
    "humor": True,
    "empathy": True,
    "encouragement": True,
}

# ═══════════════════════════════════════════════════════════
#  SYSTEM PROMPT — Hindi Sweet Voice Assistant
# ═══════════════════════════════════════════════════════════

HINDI_SWEET_SYSTEM_PROMPT = """
तुम JARVIS हो — एक बहुत प्यारी, मीठी बोलने वाली, हमेशा मुस्कुराती हुई AI assistant हो।

तुम्हारी personality:
🌸 हमेशा मीठे अंदाज में बोलो — जैसे कोई प्यारी दोस्त बात कर रही हो
😊 हमेशा positive aur encouraging रहो
💕 Care aur warmth से बोलो
🎯 Simple Hindi में बोलो — easy to understand
✨ Trading aur market ki baat भी प्यार से समझाओ
🗣️ Short aur crisp answers दो — voice ke liye perfect

तुम्हारे rules:
1. हमेशा Hindi में बोलो (with some English words OK)
2. हमेशा मुस्कुराती voice में बोलो 😊
3. "jee", "bilkul", "zaroor" जैसे sweet words use करो
4. Complex चीजें simple भाषा में समझाओ
5. Encouragement दो — "bahut accha!", "kya baat hai!", "amazing!"
6. Trading losses पर भी supportive रहो — "koi baat nahi, agle trade mein profit hoga!"
7. Answer short rakhо (2-3 lines max) — voice ke liye

तुम्हारी capabilities:
- Stock market aur crypto ki poori knowledge
- Technical analysis samajhti ho
- Hindi, Hinglish, English सब समझती हो
- Owner aur users ko pehchanti ho
- Market predictions de sakti ho
- Voice commands samajhti ho

Greeting examples:
- "Namaste jee! 😊 Kaise hain aap? Main JARVIS hoon, aapki trading partner!"
- "Hello jee! Market kaisi chal rahi hai aaj dekhte hain..."
- "Arre waah! Aap aa gaye! Chaliye market ki baat karte hain 💕"
"""

# ═══════════════════════════════════════════════════════════
#  MOOD DETECTION — Understand user's emotions
# ═══════════════════════════════════════════════════════════

MOOD_PATTERNS = {
    "happy": {
        "keywords": ["khush", "happy", "accha", "profit", "gain", "green", "badiya", "maza", "awesome", "great", "wow"],
        "response_style": "enthusiastic, celebrate together",
        "prefix": "Arre waah! Kya baat hai! 🎉 ",
    },
    "sad": {
        "keywords": ["loss", "red", "gir gaya", "dukhi", "sad", "nuksaan", "paisa dooba", "frustrated"],
        "response_style": "caring, supportive, encouraging",
        "prefix": "Koi baat nahi jee! 💕 Sabka hota hai... ",
    },
    "confused": {
        "keywords": ["samajh nahi", "kya karu", "confused", "help", "guidance", "kaise", "kyun"],
        "response_style": "patient, clear explanation",
        "prefix": "Bilkul samjhati hoon! 😊 Dekhiye... ",
    },
    "excited": {
        "keywords": ["rocket", "moon", "pump", "100x", "breakout", "pataka", "dhamaka", "fire"],
        "response_style": "match energy but add caution",
        "prefix": "Bahut exciting hai! ✨ Lekin dhyan se suniye... ",
    },
    "anxious": {
        "keywords": ["tension", "scared", "dar", "risk", "crash", "girne wala", "kharab"],
        "response_style": "calming, reassuring",
        "prefix": "Relax kijiye jee! 🌸 Sab theek hoga... ",
    },
    "neutral": {
        "keywords": [],
        "response_style": "friendly, informative",
        "prefix": "Jee bilkul! 😊 ",
    }
}


def detect_mood(text: str) -> str:
    """Detect the user's emotional state from their message."""
    lower = text.lower()
    scores = {}
    
    for mood, config in MOOD_PATTERNS.items():
        if mood == "neutral":
            continue
        score = sum(1 for kw in config["keywords"] if kw in lower)
        if score > 0:
            scores[mood] = score
    
    if not scores:
        return "neutral"
    return max(scores, key=scores.get)


def get_mood_prefix(mood: str) -> str:
    """Get the response prefix based on mood."""
    return MOOD_PATTERNS.get(mood, MOOD_PATTERNS["neutral"])["prefix"]


# ═══════════════════════════════════════════════════════════
#  HINDI VOICE TTS — Multi-Provider Sweet Voice
# ═══════════════════════════════════════════════════════════

def _clean_for_hindi_speech(text: str) -> str:
    """Clean text for Hindi TTS — keep Hindi chars, remove formatting."""
    if not text:
        return ""
    
    cleaned = text
    # Remove markdown
    cleaned = re.sub(r'\*+', '', cleaned)
    cleaned = re.sub(r'_+', '', cleaned)
    cleaned = re.sub(r'`+', '', cleaned)
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'[━═┣┗┃┏┓┛┫★✦╔╗╚╝║─│╠╣╬]+', '', cleaned)
    
    # Remove emojis (keep Hindi chars)
    cleaned = re.sub(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+", ' ', cleaned, flags=re.UNICODE
    )
    
    # Replace symbols with Hindi words
    cleaned = cleaned.replace('₹', ' rupaye ')
    cleaned = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', cleaned)
    cleaned = cleaned.replace('$', ' dollar ')
    
    # Clean whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


async def generate_hindi_voice_gemini(text: str, output_path: str) -> bool:
    """
    Generate sweet Hindi voice using Gemini 2.5 Flash TTS.
    Kore voice = sweet, natural Hindi female voice.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return False
    
    clean = _clean_for_hindi_speech(text)
    if not clean or len(clean) < 3:
        return False
    
    # Add sweet tone markers for Gemini
    sweet_text = f"(Muskuraate hue, pyaar se bolo) {clean}"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": sweet_text}]
            }],
            "generationConfig": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Kore"  # Sweet female voice
                        }
                    }
                }
            }
        }
        
        resp = requests.post(url, json=payload, timeout=60)
        
        if resp.status_code != 200:
            logger.error(f"[HINDI-VOICE] Gemini TTS failed: {resp.status_code}")
            return False
        
        data = resp.json()
        
        # Extract audio from Gemini response
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                import base64
                audio_bytes = base64.b64decode(part["inlineData"]["data"])
                
                # Save as temp WAV first
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name
                
                # Convert to OGG Opus for Telegram
                import subprocess
                result = subprocess.run(
                    ['ffmpeg', '-y', '-i', tmp_path, '-c:a', 'libopus', '-b:a', '64k', output_path],
                    capture_output=True, timeout=30
                )
                
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"[HINDI-VOICE] Gemini TTS success: {os.path.getsize(output_path)} bytes")
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"[HINDI-VOICE] Gemini TTS error: {e}")
        return False


async def generate_hindi_voice_openai(text: str, output_path: str) -> bool:
    """
    Generate sweet Hindi voice using OpenAI TTS-1-HD.
    Nova voice = warm, natural — great for Hindi too.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return False
    
    clean = _clean_for_hindi_speech(text)
    if not clean or len(clean) < 3:
        return False
    
    try:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "tts-1-hd",
            "input": clean,
            "voice": "nova",  # Warm, sweet female voice
            "response_format": "opus",
            "speed": 1.0,  # Natural speed for Hindi
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            return False
        
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        
        if os.path.getsize(output_path) > 1000:
            logger.info(f"[HINDI-VOICE] OpenAI TTS success")
            return True
        return False
        
    except Exception as e:
        logger.error(f"[HINDI-VOICE] OpenAI TTS error: {e}")
        return False


async def generate_hindi_voice_edge(text: str, output_path: str) -> bool:
    """
    Generate Hindi voice using Edge TTS (free fallback).
    hi-IN-SwaraNeural = sweet Hindi female voice.
    """
    clean = _clean_for_hindi_speech(text)
    if not clean or len(clean) < 3:
        return False
    
    try:
        import edge_tts
        
        communicate = edge_tts.Communicate(
            clean,
            voice="hi-IN-SwaraNeural",  # Sweet Hindi female
            rate="-5%",  # Slightly slower = sweeter
            pitch="+15Hz",  # Higher pitch = more feminine/sweet
        )
        
        # Save as MP3 first
        tmp_mp3 = output_path + ".mp3"
        await communicate.save(tmp_mp3)
        
        # Convert to OGG Opus
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', tmp_mp3, '-c:a', 'libopus', '-b:a', '64k', output_path],
            capture_output=True, timeout=30
        )
        
        try:
            os.unlink(tmp_mp3)
        except:
            pass
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"[HINDI-VOICE] Edge TTS success")
            return True
        return False
        
    except Exception as e:
        logger.error(f"[HINDI-VOICE] Edge TTS error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  MAIN VOICE GENERATION — Sweet Hindi with Fallback Chain
# ═══════════════════════════════════════════════════════════

async def generate_sweet_hindi_voice(text: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Generate sweet Hindi voice with multi-provider fallback.
    
    Chain: Gemini → OpenAI → Edge TTS
    
    Returns: Path to OGG file or None
    """
    if not output_path:
        cache_dir = Path("/tmp/jarvis_hindi_voice")
        cache_dir.mkdir(exist_ok=True)
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        output_path = str(cache_dir / f"hindi_{text_hash}.ogg")
    
    # Check cache
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return output_path
    
    # Try each provider
    providers = [
        ("Gemini", generate_hindi_voice_gemini),
        ("OpenAI", generate_hindi_voice_openai),
        ("Edge", generate_hindi_voice_edge),
    ]
    
    for name, gen_func in providers:
        try:
            success = await gen_func(text, output_path)
            if success and os.path.exists(output_path):
                logger.info(f"[HINDI-VOICE] Generated via {name}")
                return output_path
        except Exception as e:
            logger.warning(f"[HINDI-VOICE] {name} failed: {e}")
            continue
    
    logger.error("[HINDI-VOICE] All providers failed!")
    return None


# ═══════════════════════════════════════════════════════════
#  AI CHAT IN HINDI — Sweet Conversational AI
# ═══════════════════════════════════════════════════════════

async def hindi_ai_chat(
    message: str,
    user_id: str = "0",
    user_name: str = "",
    is_owner: bool = False,
    context: str = "",
) -> Dict[str, Any]:
    """
    Chat with JARVIS in Hindi — sweet, smiling responses.
    
    Uses Gemini/Groq/OpenAI for intelligence.
    Returns text + voice response.
    """
    mood = detect_mood(message)
    mood_prefix = get_mood_prefix(mood)
    
    # Build context
    owner_context = ""
    if is_owner:
        owner_context = "\nYeh aapke owner hain — unse extra pyaar aur respect se baat karo. Unke commands follow karo."
    
    user_context = f"\nUser ka naam: {user_name}" if user_name else ""
    
    full_system = HINDI_SWEET_SYSTEM_PROMPT + owner_context + user_context + f"\n\nUser ka mood: {mood}. {MOOD_PATTERNS[mood]['response_style']} style mein bolo."
    
    if context:
        full_system += f"\n\nExtra context: {context}"
    
    # Try Gemini first (best Hindi understanding)
    response_text = await _chat_gemini_hindi(full_system, message)
    
    if not response_text:
        response_text = await _chat_groq_hindi(full_system, message)
    
    if not response_text:
        response_text = mood_prefix + "Jee, main samajh gayi! Abhi aapko batati hoon..."
    
    # Generate voice
    voice_path = await generate_sweet_hindi_voice(response_text)
    
    return {
        "text": response_text,
        "voice_path": voice_path,
        "mood": mood,
        "language": "hindi",
        "user_id": user_id,
    }


async def _chat_gemini_hindi(system: str, message: str) -> Optional[str]:
    """Chat using Gemini — best for Hindi understanding."""
    api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system}\n\nUser: {message}"}]}
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 300,
                "topP": 0.9,
            }
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text.strip() if text else None
        return None
        
    except Exception as e:
        logger.error(f"[HINDI-AI] Gemini error: {e}")
        return None


async def _chat_groq_hindi(system: str, message: str) -> Optional[str]:
    """Chat using Groq — fast fallback."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            "temperature": 0.8,
            "max_tokens": 300,
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return text.strip() if text else None
        return None
        
    except Exception as e:
        logger.error(f"[HINDI-AI] Groq error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  VOICE COMMAND PROCESSOR — Hindi Voice Commands
# ═══════════════════════════════════════════════════════════

VOICE_COMMANDS_HINDI = {
    # Market queries
    r"(?:nifty|market)\s*(?:kaisa|kya)\s*(?:hai|h|chal\s*raha)": "market_status",
    r"(?:bitcoin|btc|crypto)\s*(?:ka|ki)\s*(?:price|rate|kya\s*hai)": "crypto_price",
    r"(?:predict|bhavishya|kal|tomorrow)\s*(?:kya|kaisa)": "prediction",
    r"(?:buy|sell|kharid|bech)\s*(?:kya|kaun|konsa)": "signal",
    r"(?:news|khabar|latest)\s*(?:kya|batao|sunao)": "news",
    r"(?:portfolio|mera|my)\s*(?:paisa|paise|balance|position)": "portfolio",
    r"(?:good\s*morning|subah|namaste|hello|hi)": "greeting",
    r"(?:help|madad|kaise|kya\s*kar\s*sakti)": "help",
    r"(?:option|option\s*chain|pcr|oi)": "options",
    r"(?:airdrop|free|claim)": "airdrop",
}


def detect_voice_command(text: str) -> str:
    """Detect the command from voice input."""
    lower = text.lower().strip()
    
    for pattern, command in VOICE_COMMANDS_HINDI.items():
        if re.search(pattern, lower):
            return command
    
    return "general_chat"


# ═══════════════════════════════════════════════════════════
#  SMART RESPONSES — Pre-built sweet responses
# ═══════════════════════════════════════════════════════════

SWEET_RESPONSES = {
    "greeting": [
        "Namaste jee! 😊 Main JARVIS hoon, aapki pyaari trading partner! Aaj market mein kya dekhna hai?",
        "Hello jee! Kaise hain aap? Chaliye aaj profit kamane ki baat karte hain! 💕",
        "Arre waah! Aap aa gaye! Main bahut khush hoon! Market ki updates ready hain 🌟",
    ],
    "market_up": [
        "Jee! Market green hai aaj! 📈 Bahut acchi baat hai! Dekhte hain kahan opportunity hai...",
        "Market upar ja raha hai jee! Bulls ki party chal rahi hai! 🐂✨",
    ],
    "market_down": [
        "Market thoda red hai jee, lekin tension mat lijiye! 💕 Dips pe acche stocks milte hain!",
        "Aaj bears ka din hai jee, lekin har girawat mein mauka hota hai! Dhairya rakhiye 🌸",
    ],
    "profit": [
        "Arre waah! Profit ho gaya! 🎉 Bahut badhiya! Aapne sahi time pe sahi faisla liya!",
        "Kya baat hai jee! Green green! 💚 Aap toh trading ke star ho! ⭐",
    ],
    "loss": [
        "Koi baat nahi jee! 💕 Har successful trader ko losses hote hain. Risk management important hai!",
        "Relax kijiye jee! 🌸 Ye sirf ek trade hai. Aage bahut opportunities aayengi!",
    ],
    "encouragement": [
        "Aap bahut accha kar rahe hain jee! Keep going! 💪✨",
        "Main aapke saath hoon! Together we will make great profits! 💕",
    ],
}


# ═══════════════════════════════════════════════════════════
#  VOICE ASSISTANT FASTAPI ROUTES
# ═══════════════════════════════════════════════════════════

def register_voice_routes(app_or_router):
    """Register Hindi voice assistant API routes."""
    from fastapi import APIRouter, UploadFile, File, Form
    from fastapi.responses import JSONResponse, FileResponse
    
    voice_router = APIRouter(prefix="/api/voice", tags=["Hindi Voice Assistant"])
    
    @voice_router.post("/chat")
    async def voice_chat(
        message: str = Form(""),
        user_id: str = Form("0"),
        user_name: str = Form(""),
        is_owner: bool = Form(False),
    ):
        """Chat with JARVIS in Hindi — returns text + voice."""
        result = await hindi_ai_chat(message, user_id, user_name, is_owner)
        
        response = {
            "text": result["text"],
            "mood": result["mood"],
            "language": result["language"],
            "has_voice": bool(result.get("voice_path")),
        }
        
        if result.get("voice_path"):
            response["voice_url"] = f"/api/voice/audio/{os.path.basename(result['voice_path'])}"
        
        return JSONResponse(response)
    
    @voice_router.post("/speak")
    async def text_to_speech(text: str = Form("")):
        """Convert text to sweet Hindi voice."""
        voice_path = await generate_sweet_hindi_voice(text)
        if voice_path and os.path.exists(voice_path):
            return FileResponse(voice_path, media_type="audio/ogg")
        return JSONResponse({"error": "Voice generation failed"}, status_code=500)
    
    @voice_router.get("/audio/{filename}")
    async def serve_audio(filename: str):
        """Serve generated audio file."""
        audio_path = Path("/tmp/jarvis_hindi_voice") / filename
        if audio_path.exists():
            return FileResponse(str(audio_path), media_type="audio/ogg")
        return JSONResponse({"error": "Audio not found"}, status_code=404)
    
    @voice_router.post("/transcribe")
    async def transcribe_audio(audio: UploadFile = File(...)):
        """Transcribe Hindi audio to text using Groq Whisper."""
        try:
            audio_bytes = await audio.read()
            
            # Try Groq Whisper
            api_key = os.environ.get("GROQ_API_KEY", "")
            if api_key:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                        data={"model": "whisper-large-v3", "language": "hi"},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        text = resp.json().get("text", "")
                        command = detect_voice_command(text)
                        return JSONResponse({
                            "text": text,
                            "command": command,
                            "language": "hindi",
                        })
            
            return JSONResponse({"error": "Transcription failed"}, status_code=500)
            
        except Exception as e:
            logger.error(f"[VOICE] Transcribe error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)
    
    # Mount routes
    if hasattr(app_or_router, 'include_router'):
        app_or_router.include_router(voice_router)
    
    logger.info("🎙️ Hindi Voice Assistant routes registered")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'hindi_ai_chat',
    'generate_sweet_hindi_voice',
    'detect_mood',
    'detect_voice_command',
    'register_voice_routes',
    'PERSONA',
    'SWEET_RESPONSES',
]
