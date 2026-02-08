"""
🎤💕 J.A.R.V.I.S. Voice Engine — Beautiful Female Hindi Voice
═══════════════════════════════════════════════════════════════
Gives JARVIS a beautiful, warm female voice using Microsoft Edge TTS.
Also handles Speech-to-Text for voice messages from users.

Voice: hi-IN-SwaraNeural (Beautiful Hindi Female)
Fallback: en-IN-NeerjaNeural (Beautiful English-Indian Female)

Author: David Crew AI
"""

import os
import re
import logging
import asyncio
import tempfile
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("voice_engine")

# ═══════════════════════════════════════════════════════════
#  VOICE CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Beautiful Hindi Female Voice (Microsoft Neural TTS)
HINDI_VOICE = "hi-IN-SwaraNeural"        # Sweet, warm Hindi female
ENGLISH_VOICE = "en-IN-NeerjaNeural"      # Beautiful Indian English female
HINDI_VOICE_ALT = "hi-IN-SwaraNeural"     # Backup

# Voice settings
VOICE_RATE = "+5%"      # Slightly faster for natural feel
VOICE_PITCH = "+2Hz"    # Slightly higher pitch for sweetness
VOICE_VOLUME = "+0%"    # Normal volume

# Cache directory for voice files
VOICE_CACHE_DIR = Path("/tmp/jarvis_voice_cache")
VOICE_CACHE_DIR.mkdir(exist_ok=True)

# Max text length for voice (Telegram voice limit ~50MB, but keep reasonable)
MAX_VOICE_TEXT_LENGTH = 2000
MAX_VOICE_DURATION_SEC = 120  # 2 minutes max

# ═══════════════════════════════════════════════════════════
#  TEXT CLEANER — Remove emojis, markdown, formatting for TTS
# ═══════════════════════════════════════════════════════════

def clean_text_for_speech(text: str) -> str:
    """
    Clean text for TTS — remove emojis, markdown, formatting symbols.
    Keep only readable text that sounds natural when spoken.
    """
    if not text:
        return ""
    
    # Remove Telegram markdown formatting
    cleaned = text
    
    # Remove bold markers
    cleaned = re.sub(r'\*+', '', cleaned)
    
    # Remove italic markers  
    cleaned = re.sub(r'_+', '', cleaned)
    
    # Remove code blocks
    cleaned = re.sub(r'`+', '', cleaned)
    
    # Remove links [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    
    # Remove decorative lines (━, ═, ┣, ┗, ★, ✦, etc.)
    cleaned = re.sub(r'[━═┣┗┃┏┓┛┫★✦╔╗╚╝║─│╠╣╬]+', '', cleaned)
    
    # Remove emojis (comprehensive emoji regex)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Misc
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols
        "\U0001FA00-\U0001FA6F"  # Chess
        "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
        "\U00002600-\U000026FF"  # Misc
        "\U0000FE00-\U0000FE0F"  # Variation selectors
        "\U0000200D"             # Zero width joiner
        "\U00002B50-\U00002B55"  # Stars
        "\U0000231A-\U0000231B"  # Watch/Hourglass
        "\U000023E9-\U000023F3"  # Play buttons
        "\U000023F8-\U000023FA"  # More controls
        "\U000025AA-\U000025FE"  # Shapes
        "\U00002934-\U00002935"  # Arrows
        "\U00003030"             # Wavy dash
        "\U0000303D"             # Part alternation
        "\U0001F004"             # Mahjong
        "\U0001F0CF"             # Joker
        "]+", flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub(' ', cleaned)
    
    # Remove special characters that don't speak well
    cleaned = re.sub(r'[#@\[\](){}<>|\\~/^]', ' ', cleaned)
    
    # Replace ₹ with "rupees" 
    cleaned = cleaned.replace('₹', ' rupees ')
    
    # Replace % with "percent"
    cleaned = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', cleaned)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Clean up multiple newlines
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    
    # Remove leading/trailing whitespace per line
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
    
    return cleaned.strip()


def detect_language(text: str) -> str:
    """Detect if text is primarily Hindi or English."""
    # Count Hindi characters (Devanagari range)
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
    
    if total_alpha == 0:
        return "hi"  # Default Hindi
    
    hindi_ratio = hindi_chars / total_alpha
    return "hi" if hindi_ratio > 0.3 else "en"


# ═══════════════════════════════════════════════════════════
#  TEXT-TO-SPEECH — Beautiful Female Voice
# ═══════════════════════════════════════════════════════════

async def _generate_voice_async(text: str, output_path: str, language: str = "auto") -> bool:
    """Generate voice audio from text using Edge TTS (async)."""
    try:
        import edge_tts
        
        # Clean text for speech
        clean_text = clean_text_for_speech(text)
        if not clean_text or len(clean_text) < 3:
            return False
        
        # Truncate if too long
        if len(clean_text) > MAX_VOICE_TEXT_LENGTH:
            clean_text = clean_text[:MAX_VOICE_TEXT_LENGTH] + "... बाकी details text में देख लीजिए।"
        
        # Detect language if auto
        if language == "auto":
            language = detect_language(clean_text)
        
        # Choose voice based on language
        voice = HINDI_VOICE if language == "hi" else ENGLISH_VOICE
        
        # Generate speech
        communicate = edge_tts.Communicate(
            clean_text, 
            voice,
            rate=VOICE_RATE,
            pitch=VOICE_PITCH,
            volume=VOICE_VOLUME
        )
        
        await communicate.save(output_path)
        
        # Verify file was created and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"[VOICE] Generated {os.path.getsize(output_path)} bytes, lang={language}, voice={voice}")
            return True
        else:
            logger.warning("[VOICE] Generated file too small or missing")
            return False
            
    except Exception as e:
        logger.error(f"[VOICE] TTS failed: {e}")
        return False


def generate_voice(text: str, language: str = "auto") -> Optional[str]:
    """
    Generate voice audio from text. Returns path to audio file or None.
    Uses caching to avoid regenerating same text.
    """
    if not text or len(text.strip()) < 5:
        return None
    
    try:
        # Create cache key from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        cache_path = str(VOICE_CACHE_DIR / f"jarvis_{text_hash}.mp3")
        
        # Check cache
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            # Cache hit - check if not too old (1 hour)
            if time.time() - os.path.getmtime(cache_path) < 3600:
                return cache_path
        
        # Generate new voice
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(_generate_voice_async(text, cache_path, language))
        finally:
            loop.close()
        
        if success:
            return cache_path
        return None
        
    except Exception as e:
        logger.error(f"[VOICE] Generation failed: {e}")
        return None


def generate_voice_for_message(text: str, chat_id: int = 0) -> Optional[str]:
    """
    Smart voice generation — generates voice for JARVIS responses.
    Strips markdown/emojis, detects language, generates beautiful audio.
    """
    return generate_voice(text)


# ═══════════════════════════════════════════════════════════
#  SPEECH-TO-TEXT — Transcribe User Voice Messages
# ═══════════════════════════════════════════════════════════

def transcribe_voice_message(audio_path: str) -> Optional[str]:
    """
    Transcribe a voice message audio file to text.
    Uses Groq Whisper API (fast, free) -> OpenAI Whisper API -> fallback.
    """
    if not os.path.exists(audio_path):
        logger.error(f"[STT] Audio file not found: {audio_path}")
        return None
    
    # Try Groq Whisper first (fastest, free)
    text = _transcribe_groq(audio_path)
    if text:
        return text
    
    # Try OpenAI Whisper
    text = _transcribe_openai(audio_path)
    if text:
        return text
    
    # Fallback: return None (will show "couldn't understand" message)
    logger.warning("[STT] All transcription methods failed")
    return None


def _transcribe_groq(audio_path: str) -> Optional[str]:
    """Transcribe using Groq Whisper API (free, fast)."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    
    try:
        import requests
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        with open(audio_path, "rb") as f:
            files = {"file": ("audio.ogg", f, "audio/ogg")}
            data = {
                "model": "whisper-large-v3",
                "language": "hi",  # Hindi primary
                "response_format": "text"
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            text = response.text.strip()
            if text:
                logger.info(f"[STT-Groq] Transcribed: {text[:100]}")
                return text
    except Exception as e:
        logger.error(f"[STT-Groq] Failed: {e}")
    
    return None


def _transcribe_openai(audio_path: str) -> Optional[str]:
    """Transcribe using OpenAI Whisper API."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    
    try:
        import requests
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        with open(audio_path, "rb") as f:
            files = {"file": ("audio.ogg", f, "audio/ogg")}
            data = {
                "model": "whisper-1",
                "language": "hi",
                "response_format": "text"
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            text = response.text.strip()
            if text:
                logger.info(f"[STT-OpenAI] Transcribed: {text[:100]}")
                return text
    except Exception as e:
        logger.error(f"[STT-OpenAI] Failed: {e}")
    
    return None


# ═══════════════════════════════════════════════════════════
#  TELEGRAM HELPERS — Download & Send Voice
# ═══════════════════════════════════════════════════════════

def download_telegram_voice(file_id: str, token: str) -> Optional[str]:
    """Download a Telegram voice message by file_id. Returns local path."""
    import requests
    
    try:
        # Get file path from Telegram
        url = f"https://api.telegram.org/bot{token}/getFile"
        resp = requests.get(url, params={"file_id": file_id}, timeout=15)
        data = resp.json()
        
        if not data.get("ok"):
            logger.error(f"[VOICE-DL] getFile failed: {data}")
            return None
        
        file_path = data["result"]["file_path"]
        
        # Download the file
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        resp = requests.get(download_url, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        # Save to temp file
        ext = file_path.split(".")[-1] if "." in file_path else "ogg"
        temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_voice_{file_id}.{ext}")
        with open(temp_path, "wb") as f:
            f.write(resp.content)
        
        logger.info(f"[VOICE-DL] Downloaded {len(resp.content)} bytes -> {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"[VOICE-DL] Download failed: {e}")
        return None


def send_voice_message(chat_id: int, audio_path: str, token: str, 
                       caption: str = None, reply_markup: dict = None) -> bool:
    """Send a voice message to Telegram chat."""
    import requests
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendVoice"
        
        with open(audio_path, "rb") as f:
            files = {"voice": ("jarvis_voice.mp3", f, "audio/mpeg")}
            data = {"chat_id": chat_id}
            
            if caption:
                data["caption"] = caption[:1024]  # Telegram caption limit
                data["parse_mode"] = "Markdown"
            
            if reply_markup:
                import json
                data["reply_markup"] = json.dumps(reply_markup)
            
            resp = requests.post(url, files=files, data=data, timeout=30)
        
        success = resp.status_code == 200
        if success:
            logger.info(f"[VOICE-SEND] Sent voice to {chat_id}")
        else:
            logger.error(f"[VOICE-SEND] Failed: {resp.text[:200]}")
        
        return success
        
    except Exception as e:
        logger.error(f"[VOICE-SEND] Error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  SMART VOICE RESPONSE — Decide when to speak
# ═══════════════════════════════════════════════════════════

# Always speak for these intents
VOICE_ALWAYS_INTENTS = {
    "greeting", "morning_brief", "market_summary", "help",
    "buy_sell_stock", "buy_sell_crypto", "global_analysis",
}

# Messages shorter than this get voice
VOICE_SHORT_THRESHOLD = 800

def should_send_voice(text: str, intent: str = "", is_voice_input: bool = False) -> bool:
    """
    Decide if JARVIS should send a voice response.
    Always send voice if user sent voice message.
    Also send voice for greetings, briefings, and shorter responses.
    """
    # Always respond with voice if user sent voice
    if is_voice_input:
        return True
    
    # Always speak for certain intents
    if intent in VOICE_ALWAYS_INTENTS:
        return True
    
    # Speak for shorter messages
    clean = clean_text_for_speech(text)
    if len(clean) <= VOICE_SHORT_THRESHOLD:
        return True
    
    return False


# ═══════════════════════════════════════════════════════════
#  VOICE CACHE CLEANUP
# ═══════════════════════════════════════════════════════════

def cleanup_voice_cache(max_age_hours: int = 2):
    """Remove old voice cache files."""
    try:
        now = time.time()
        for f in VOICE_CACHE_DIR.iterdir():
            if f.is_file() and now - f.stat().st_mtime > max_age_hours * 3600:
                f.unlink()
                logger.debug(f"[VOICE-CACHE] Removed {f.name}")
    except Exception as e:
        logger.error(f"[VOICE-CACHE] Cleanup error: {e}")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'generate_voice',
    'generate_voice_for_message', 
    'transcribe_voice_message',
    'download_telegram_voice',
    'send_voice_message',
    'clean_text_for_speech',
    'should_send_voice',
    'detect_language',
    'cleanup_voice_cache',
    'HINDI_VOICE',
    'ENGLISH_VOICE',
]
