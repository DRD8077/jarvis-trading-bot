"""
🎤💕 J.A.R.V.I.S. Voice Engine v3 — ULTRA PREMIUM Multi-TTS
═══════════════════════════════════════════════════════════════════
World's best voice engine with 4-layer TTS fallback chain.

Primary:   OpenAI TTS-1-HD (nova voice — warm, beautiful, ultra-natural)
Secondary: Deepgram Aura TTS (asteria — fast, natural female)
Tertiary:  Google Gemini 2.5 Flash TTS (Kore voice)
Fallback:  Microsoft Edge TTS (hi-IN-SwaraNeural)
Output:    OGG Opus (auto-play waveform in Telegram — feels LIVE)

STT: Groq Whisper → OpenAI Whisper for voice-to-text

Author: David Crew AI
"""

import os
import re
import json
import logging
import asyncio
import subprocess
import tempfile
import hashlib
import time
import base64
from pathlib import Path
from typing import Optional, Tuple

import requests

logger = logging.getLogger("voice_engine")

# ═══════════════════════════════════════════════════════════
#  VOICE CONFIGURATION — 5-LAYER TTS CHAIN (ElevenLabs Primary)
# ═══════════════════════════════════════════════════════════

# ── ENV-CONFIGURABLE VOICE SETTINGS ──
_JARVIS_VOICE = os.environ.get("JARVIS_VOICE", "").strip()
_JARVIS_PERSONA = os.environ.get("JARVIS_PERSONA", "female").strip().lower()

# ── ElevenLabs TTS (NEW PRIMARY — ultra-realistic, best quality) ──
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "2bNrEsM0omyhLiEyOwqY")  # From voice library
ELEVENLABS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_STABILITY = 0.5
ELEVENLABS_SIMILARITY = 0.75
ELEVENLABS_STYLE = 0.5

# ── OpenAI TTS (SECONDARY — ultra-natural, best quality) ──
# nova = warm female | alloy = neutral | shimmer = expressive female
OPENAI_TTS_MODEL = "tts-1-hd"  # HD quality
OPENAI_TTS_VOICE = "nova" if _JARVIS_PERSONA == "female" else "onyx"
OPENAI_TTS_VOICE_BACKUP = "shimmer" if _JARVIS_PERSONA == "female" else "echo"
OPENAI_TTS_SPEED = 1.05  # slightly faster for natural feel

# ── Deepgram TTS (TERTIARY — fast, natural) ──
DEEPGRAM_TTS_MODEL = "aura-asteria-en"  # warm female
DEEPGRAM_TTS_MODEL_HI = "aura-asteria-en"  # Hindi content in English voice

# ── Gemini TTS (QUATERNARY — Gemini Live quality)
# Use JARVIS_VOICE env var if set, otherwise Aoede (best voice)
GEMINI_VOICE_PRIMARY = _JARVIS_VOICE if _JARVIS_VOICE else ("Kore" if _JARVIS_PERSONA == "female" else "Charon")
GEMINI_VOICE_BACKUP = "Aoede" if _JARVIS_PERSONA == "female" else "Orus"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# ── Edge TTS (FALLBACK — free but less natural) ──
EDGE_HINDI_VOICE = "hi-IN-SwaraNeural" if _JARVIS_PERSONA == "female" else "hi-IN-MadhurNeural"
EDGE_ENGLISH_VOICE = "en-IN-NeerjaExpressiveNeural" if _JARVIS_PERSONA == "female" else "en-IN-PrabhatNeural"
EDGE_VOICE_RATE = "-3%"
EDGE_VOICE_PITCH = "+12Hz"

# API Keys — support both GOOGLE_API_KEY and GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
OPENAI_API_KEY_TTS = os.environ.get("OPENAI_API_KEY", "")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

# Cache directory
VOICE_CACHE_DIR = Path("/tmp/jarvis_voice_cache")
VOICE_CACHE_DIR.mkdir(exist_ok=True)

# Voice limits
MAX_VOICE_TEXT_LENGTH = 3000
MAX_SUMMARY_LENGTH = 600
VOICE_SHORT_THRESHOLD = 1200

# Always send voice for these intents
VOICE_ALWAYS_INTENTS = {
    "greeting", "morning_brief", "market_summary", "help",
    "buy_sell_stock", "buy_sell_crypto", "global_analysis", "chat",
}


# ═══════════════════════════════════════════════════════════
#  TEXT CLEANER — Make text speakable
# ═══════════════════════════════════════════════════════════

def clean_text_for_speech(text: str) -> str:
    """Clean text for TTS — remove emojis, markdown, formatting."""
    if not text:
        return ""

    cleaned = text

    # Remove Telegram markdown
    cleaned = re.sub(r'\*+', '', cleaned)
    cleaned = re.sub(r'_+', '', cleaned)
    cleaned = re.sub(r'`+', '', cleaned)

    # Remove links [text](url) → text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # Remove decorative lines
    cleaned = re.sub(r'[━═┣┗┃┏┓┛┫★✦╔╗╚╝║─│╠╣╬]+', '', cleaned)

    # Remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U0000FE00-\U0000FE0F"
        "\U0000200D"
        "\U00002B50-\U00002B55"
        "\U0000231A-\U0000231B"
        "\U000023E9-\U000023F3"
        "\U000023F8-\U000023FA"
        "\U000025AA-\U000025FE"
        "\U00002934-\U00002935"
        "\U00003030\U0000303D"
        "\U0001F004\U0001F0CF"
        "]+", flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub(' ', cleaned)

    # Remove special characters
    cleaned = re.sub(r'[#@\[\](){}<>|\\~/^]', ' ', cleaned)

    # Replace symbols with spoken words
    cleaned = cleaned.replace('₹', ' rupees ')
    cleaned = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', cleaned)

    # Clean whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())

    return cleaned.strip()


def detect_language(text: str) -> str:
    """Detect if text is primarily Hindi or English."""
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
    if total_alpha == 0:
        return "hi"
    return "hi" if hindi_chars / total_alpha > 0.3 else "en"


def _summarize_for_voice(text: str) -> str:
    """
    For long market reports, create a short conversational summary
    that sounds natural when spoken aloud. JARVIS speaks highlights only.
    Smart detection: crypto vs stock vs general.
    """
    clean = clean_text_for_speech(text)
    if len(clean) <= VOICE_SHORT_THRESHOLD:
        return clean

    lines = [l.strip() for l in clean.split('\n') if l.strip() and len(l.strip()) > 10]
    
    # Smart extraction: find key data lines
    key_lines = []
    for line in lines:
        # Priority lines: buy/sell signals, prices, targets, profits
        if any(w in line.lower() for w in [
            'buy', 'sell', 'signal', 'target', 'stop loss', 'entry',
            'profit', 'return', 'score', 'confidence', 'rocket',
            'strong', 'avoid', 'warning', 'alert',
            'rupees', 'percent', 'price', 'volume',
        ]):
            key_lines.append(line)
    
    # Take key lines first, then first few general lines
    if key_lines:
        summary_lines = key_lines[:5]
    else:
        summary_lines = lines[:4]
    
    summary = '. '.join(summary_lines)

    if len(summary) > MAX_SUMMARY_LENGTH:
        summary = summary[:MAX_SUMMARY_LENGTH]
        for sep in ['. ', '। ', ', ', ' ']:
            idx = summary.rfind(sep)
            if idx > MAX_SUMMARY_LENGTH // 2:
                summary = summary[:idx + 1]
                break

    summary += " बाकी details text message में देख लीजिए।"
    return summary


# ═══════════════════════════════════════════════════════════
#  GEMINI 2.5 FLASH TTS — GEMINI LIVE QUALITY VOICE
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
#  OPENAI TTS-1-HD — PRIMARY (Best quality, ultra-natural)
# ═══════════════════════════════════════════════════════════

def _generate_openai_tts(text: str, output_ogg_path: str, voice: str = None) -> bool:
    """
    Generate voice using OpenAI TTS-1-HD — world's best TTS.
    Nova voice = warm, natural female — perfect JARVIS voice.
    Returns OGG Opus file.
    """
    api_key = OPENAI_API_KEY_TTS or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.debug("[VOICE-OPENAI] No OPENAI_API_KEY")
        return False

    voice = voice or OPENAI_TTS_VOICE
    clean = clean_text_for_speech(text)
    if not clean or len(clean) < 3:
        return False

    if len(clean) > VOICE_SHORT_THRESHOLD:
        clean = _summarize_for_voice(text)

    try:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENAI_TTS_MODEL,
            "input": clean,
            "voice": voice,
            "response_format": "opus",  # Direct OGG Opus!
            "speed": OPENAI_TTS_SPEED,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            logger.error(f"[VOICE-OPENAI] API error {resp.status_code}: {resp.text[:200]}")
            return False

        audio_bytes = resp.content
        if len(audio_bytes) < 1000:
            logger.warning("[VOICE-OPENAI] Audio too short")
            return False

        # OpenAI returns opus directly, just save it
        with open(output_ogg_path, 'wb') as f:
            f.write(audio_bytes)

        ogg_size = os.path.getsize(output_ogg_path)
        logger.info(f"[VOICE-OPENAI] Generated {ogg_size} bytes OGG, voice={voice}")
        return True

    except Exception as e:
        logger.error(f"[VOICE-OPENAI] TTS failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  DEEPGRAM AURA TTS — SECONDARY (Fast, natural)
# ═══════════════════════════════════════════════════════════

def _generate_deepgram_tts(text: str, output_ogg_path: str) -> bool:
    """
    Generate voice using Deepgram Aura TTS.
    Asteria = warm female voice, very natural.
    """
    api_key = DEEPGRAM_API_KEY or os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        logger.debug("[VOICE-DEEPGRAM] No DEEPGRAM_API_KEY")
        return False

    clean = clean_text_for_speech(text)
    if not clean or len(clean) < 3:
        return False

    if len(clean) > VOICE_SHORT_THRESHOLD:
        clean = _summarize_for_voice(text)

    try:
        model = DEEPGRAM_TTS_MODEL
        url = f"https://api.deepgram.com/v1/speak?model={model}&encoding=linear16&sample_rate=24000"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"text": clean}

        resp = requests.post(url, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            logger.error(f"[VOICE-DEEPGRAM] API error {resp.status_code}: {resp.text[:200]}")
            return False

        audio_bytes = resp.content
        if len(audio_bytes) < 1000:
            logger.warning("[VOICE-DEEPGRAM] Audio too short")
            return False

        # Deepgram returns PCM, convert to OGG Opus
        pcm_path = output_ogg_path.replace('.ogg', '_dg.pcm')
        with open(pcm_path, 'wb') as f:
            f.write(audio_bytes)

        success = _pcm_to_ogg_opus(pcm_path, output_ogg_path)

        try:
            os.unlink(pcm_path)
        except:
            pass

        if success:
            ogg_size = os.path.getsize(output_ogg_path)
            logger.info(f"[VOICE-DEEPGRAM] Generated {ogg_size} bytes OGG")
            return True
        return False

    except Exception as e:
        logger.error(f"[VOICE-DEEPGRAM] TTS failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  HELPER — PCM to OGG Opus
# ═══════════════════════════════════════════════════════════

def _pcm_to_ogg_opus(pcm_path: str, ogg_path: str) -> bool:
    """Convert raw PCM (16-bit, 24kHz, mono) to OGG Opus using ffmpeg."""
    try:
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 's16le',
            '-ar', '24000',
            '-ac', '1',
            '-i', pcm_path,
            '-c:a', 'libopus',
            '-b:a', '64k',
            '-vbr', 'on',
            '-application', 'voip',
            ogg_path
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0 and os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 500:
            return True
        logger.error(f"[VOICE] ffmpeg failed: {result.stderr[:200]}")
        return False
    except Exception as e:
        logger.error(f"[VOICE] PCM->OGG error: {e}")
        return False


def _generate_gemini_tts(text: str, output_ogg_path: str, voice: str = None) -> bool:
    """
    Generate voice using Gemini 2.5 Flash TTS — GEMINI LIVE quality.
    """
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("[VOICE] No GEMINI_API_KEY")
        return False

    voice = voice or GEMINI_VOICE_PRIMARY

    clean = clean_text_for_speech(text)
    if not clean or len(clean) < 3:
        return False

    if len(clean) > VOICE_SHORT_THRESHOLD:
        clean = _summarize_for_voice(text)

    # JARVIS personality prompt for ultra-natural speech
    # Dynamic prompt based on content type
    is_alert = any(w in clean.lower() for w in ['alert', 'warning', 'sell', 'stop loss', 'crash', 'rug'])
    is_happy = any(w in clean.lower() for w in ['profit', 'target', 'congratulation', 'बधाई', 'मुबारक', 'great', 'amazing', 'success', 'approved'])
    is_crypto = any(w in clean.lower() for w in ['token', 'crypto', 'coin', 'pump', 'rocket', 'moon', 'buy signal'])
    is_code = any(w in clean.lower() for w in ['code', 'program', 'script', 'github', 'execute', 'output', 'error'])
    is_greeting = any(w in clean.lower() for w in ['namaste', 'hello', 'good morning', 'welcome', 'नमस्ते', 'स्वागत'])
    
    if is_alert:
        mood = (
            "urgent but deeply caring — like a protective elder sister warning her family. "
            "Voice should be concerned but reassuring — 'main hoon na, tension mat lo!' feeling"
        )
    elif is_happy:
        mood = (
            "extremely excited, joyful and proud — like celebrating Diwali with your favorite person! "
            "Add genuine happiness, slight laugh in voice, 'waah! bahut accha!' energy. "
            "Voice should have a BIG SMILE — listener should FEEL the joy"
        )
    elif is_crypto:
        mood = (
            "confident, knowledgeable yet sweet — like a crypto genius best friend sharing amazing tips. "
            "Add excitement for good signals, gentle caution for risks. Sweet but smart"
        )
    elif is_code:
        mood = (
            "proud and sweet — like a brilliant engineer showing her creation with a cute smile. "
            "Confident about the code, warm in delivery — 'dekho ji, ye banaya maine!' feeling"
        )
    elif is_greeting:
        mood = (
            "extremely warm, sweet and welcoming — like meeting your favorite person after long time! "
            "Add genuine warmth, slight smile, gentle excitement. Pure love and warmth in voice. "
            "Make listener feel SPECIAL — like they are the most important person"
        )
    else:
        mood = (
            "warm, sweet, caring and gently smiling — like talking to someone very special. "
            "Natural Hindi conversational tone with genuine affection. Think loving elder sister "
            "who is also a genius — sweet but smart"
        )

    tts_prompt = (
        f"Speak this text in a {mood} natural Hindi female voice. "
        f"You are JARVIS — a beautiful, brilliant, caring Indian AI woman with Kore's warm, sweet voice. "
        f"CRITICAL VOICE RULES: "
        f"1. Speak like a REAL Indian woman — with natural Hindi rhythm, pauses, and melody. "
        f"2. Add gentle expressions naturally — 'hmm', 'suniye ji', 'dekhiye na', 'arey waah'. "
        f"3. Your voice should have a permanent SMILE — warm, sweet, genuine. "
        f"4. Hindi words should sound PERFECT — proper pronunciation of हिंदी, not robotic. "
        f"5. Mix Hindi-English (Hinglish) naturally like a real educated Indian woman. "
        f"6. Add slight emotional variations — excitement for good news, care for warnings. "
        f"7. NEVER sound robotic or monotone — be ALIVE, WARM, REAL. "
        f"8. Giggle slightly when sharing exciting news or achievements. "
        f"9. Sound like Gemini Live conversation — not reading from a script. "
        f"Here is what to say:\n\n{clean}"
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": tts_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice
                        }
                    }
                }
            }
        }

        resp = requests.post(url, json=payload, timeout=60)

        if resp.status_code != 200:
            logger.error(f"[VOICE-GEMINI] API error {resp.status_code}: {resp.text[:200]}")
            return False

        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])

        for part in parts:
            if "inlineData" in part:
                audio_b64 = part["inlineData"]["data"]
                audio_bytes = base64.b64decode(audio_b64)

                if len(audio_bytes) < 1000:
                    logger.warning("[VOICE-GEMINI] Audio too short")
                    return False

                pcm_path = output_ogg_path.replace('.ogg', '.pcm')
                with open(pcm_path, 'wb') as f:
                    f.write(audio_bytes)

                success = _pcm_to_ogg_opus(pcm_path, output_ogg_path)

                try:
                    os.unlink(pcm_path)
                except:
                    pass

                if success:
                    ogg_size = os.path.getsize(output_ogg_path)
                    logger.info(f"[VOICE-GEMINI] Generated {ogg_size} bytes OGG, voice={voice}")
                    return True
                return False

        logger.warning("[VOICE-GEMINI] No audio in response")
        return False

    except Exception as e:
        logger.error(f"[VOICE-GEMINI] TTS failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  SWEET VOICE PREPROCESSOR — Adds warmth and emotion
# ═══════════════════════════════════════════════════════════

def _add_voice_sweetness(text: str, language: str = "hi") -> str:
    """
    Add sweetness, warmth, and smile feel to voice text.
    Makes Edge TTS sound more human, warm, and caring.
    """
    import random

    sweet = text.strip()

    # Gentle pauses for natural speech rhythm
    sweet = sweet.replace("...", " ... ")
    sweet = sweet.replace(". ", "... ")  # Slightly longer pause between sentences

    if language == "hi":
        # ── Hindi sweetness ──
        # Replace abrupt endings with warm ones
        ending_sweetners = [
            " ji!", " na!", " haan ji!", " haan!",
        ]

        # Add warm fillers at natural breaks
        if not any(sweet.endswith(s) for s in ending_sweetners):
            if random.random() < 0.6:
                sweet += random.choice([" ji!", " haan!", " na ji!"])

        # Make common phrases warmer
        sweet = sweet.replace("aapka ", "aapka... ")
        sweet = sweet.replace("dekhiye", "dekhiye na")
        sweet = sweet.replace("bata", "bataa")
        sweet = sweet.replace("Abhi", "Abhii")
        sweet = sweet.replace("ready hai", "ready hai ji")

    else:
        # ── English sweetness ──
        if not sweet.endswith(("!", "?", "ji!", "right!")):
            if random.random() < 0.5:
                sweet += random.choice(["!", " right!", " okay!"])

    return sweet


# ═══════════════════════════════════════════════════════════
#  EDGE TTS — Sweet, warm, expressive voice
# ═══════════════════════════════════════════════════════════

async def _generate_edge_tts_async(text: str, output_path: str, language: str = "auto") -> bool:
    """Edge TTS with sweet, warm voice — higher pitch, expressive."""
    try:
        import edge_tts

        clean = clean_text_for_speech(text)
        if not clean or len(clean) < 3:
            return False

        if len(clean) > MAX_VOICE_TEXT_LENGTH:
            clean = _summarize_for_voice(text)

        if language == "auto":
            language = detect_language(clean)

        # Add sweetness to the text
        clean = _add_voice_sweetness(clean, language)

        voice = EDGE_HINDI_VOICE if language == "hi" else EDGE_ENGLISH_VOICE

        # Try expressive voice first, fallback to regular
        try:
            communicate = edge_tts.Communicate(
                clean, voice,
                rate=EDGE_VOICE_RATE,
                pitch=EDGE_VOICE_PITCH,
            )
        except Exception:
            # Fallback to regular voice if expressive not available
            fallback_voice = "en-IN-NeerjaNeural" if language != "hi" else EDGE_HINDI_VOICE
            communicate = edge_tts.Communicate(
                clean, fallback_voice,
                rate=EDGE_VOICE_RATE,
                pitch=EDGE_VOICE_PITCH,
            )

        mp3_path = output_path.replace('.ogg', '_edge.mp3')
        await communicate.save(mp3_path)

        if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 1000:
            return False

        result = subprocess.run([
            'ffmpeg', '-y', '-i', mp3_path,
            '-c:a', 'libopus', '-b:a', '64k', '-vbr', 'on',
            '-application', 'voip',
            output_path
        ], capture_output=True, text=True, timeout=15)

        try:
            os.unlink(mp3_path)
        except:
            pass

        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            logger.info(f"[VOICE-EDGE] Generated {os.path.getsize(output_path)} bytes, voice={voice}")
            return True
        return False

    except Exception as e:
        logger.error(f"[VOICE-EDGE] TTS failed: {e}")
        return False


def _generate_edge_tts(text: str, output_path: str, language: str = "auto") -> bool:
    """Sync wrapper for Edge TTS."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_generate_edge_tts_async(text, output_path, language))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"[VOICE-EDGE] Wrapper failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  ELEVENLABS TTS — NEW PRIMARY (Ultra-realistic, best voice)
# ═══════════════════════════════════════════════════════════

def _generate_elevenlabs_tts(text: str, output_ogg_path: str, voice_id: str = None) -> bool:
    """
    Generate voice using ElevenLabs — world's most realistic TTS.
    Voice ID: 2bNrEsM0omyhLiEyOwqY (from voice library)
    Returns OGG file path.
    """
    api_key = ELEVENLABS_API_KEY
    if not api_key:
        logger.debug("[VOICE-ELEVENLABS] No ELEVENLABS_API_KEY")
        return False

    voice_id = voice_id or ELEVENLABS_VOICE_ID
    clean = clean_text_for_speech(text)
    if not clean or len(clean) < 3:
        return False

    if len(clean) > VOICE_SHORT_THRESHOLD:
        clean = _summarize_for_voice(text)

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": clean,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": ELEVENLABS_STABILITY,
                "similarity_boost": ELEVENLABS_SIMILARITY,
                "style": ELEVENLABS_STYLE,
                "use_speaker_boost": True
            }
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            logger.error(f"[VOICE-ELEVENLABS] API error {resp.status_code}: {resp.text[:200]}")
            return False

        audio_bytes = resp.content
        if len(audio_bytes) < 1000:
            logger.warning("[VOICE-ELEVENLABS] Audio too short")
            return False

        # ElevenLabs returns MP3, convert to OGG Opus for Telegram
        mp3_path = output_ogg_path.replace('.ogg', '_el.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(audio_bytes)

        # Convert MP3 to OGG Opus
        try:
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', mp3_path,
                '-c:a', 'libopus',
                '-b:a', '64k',
                '-vbr', 'on',
                '-application', 'voip',
                output_ogg_path
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and os.path.exists(output_ogg_path) and os.path.getsize(output_ogg_path) > 500:
                logger.info(f"[VOICE-ELEVENLABS] Generated {os.path.getsize(output_ogg_path)} bytes OGG, voice={voice_id}")
                try:
                    os.unlink(mp3_path)
                except:
                    pass
                return True
        except Exception as e:
            logger.error(f"[VOICE-ELEVENLABS] ffmpeg convert failed: {e}")

        # Fallback: just return the MP3 renamed as ogg (some clients handle it)
        try:
            import shutil
            shutil.move(mp3_path, output_ogg_path)
            logger.info(f"[VOICE-ELEVENLABS] Using MP3 as fallback, size={os.path.getsize(output_ogg_path)}")
            return True
        except:
            pass

        return False

    except Exception as e:
        logger.error(f"[VOICE-ELEVENLABS] TTS failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  MAIN VOICE GENERATOR — ElevenLabs → Gemini → OpenAI → Edge
# ═══════════════════════════════════════════════════════════

# FREE_MODE: Use free APIs (Gemini + Edge)
# When ElevenLabs key is set, it becomes primary regardless of mode
FREE_MODE = not bool(ELEVENLABS_API_KEY) and not bool(OPENAI_API_KEY_TTS)


def generate_voice(text: str, language: str = "auto") -> Optional[str]:
    """
    Generate beautiful voice audio.
    PRIORITY: ElevenLabs (ultra-realistic) → OpenAI → Deepgram → Gemini → Edge TTS
    Returns: Path to OGG Opus file or None.
    """
    if not text or len(text.strip()) < 5:
        return None

    try:
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        cache_path = str(VOICE_CACHE_DIR / f"jarvis_{text_hash}.ogg")

        # Cache check (15 min TTL)
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 500:
            if time.time() - os.path.getmtime(cache_path) < 900:
                return cache_path

        # ═══ LAYER 0: ElevenLabs (ALWAYS FIRST if key available) ═══
        if ELEVENLABS_API_KEY:
            logger.info("[VOICE] Trying ElevenLabs (premium)")
            if _generate_elevenlabs_tts(text, cache_path):
                return cache_path

        if FREE_MODE:
            # ═══ FREE MODE — Gemini TTS first (best quality), then Edge ═══
            # 1. Gemini TTS (free tier — Gemini Live quality voice!)
            if GEMINI_API_KEY:
                if _generate_gemini_tts(text, cache_path):
                    return cache_path
                # Try backup voice
                if _generate_gemini_tts(text, cache_path, voice=GEMINI_VOICE_BACKUP):
                    return cache_path

            # 2. Edge TTS (FREE, fast, reliable, Hindi+English)
            if _generate_edge_tts(text, cache_path, language):
                return cache_path

            return None
        else:
            # ═══ PAID MODE — Premium voices first ═══
            # 1. OpenAI TTS-1-HD (nova voice)
            if _generate_openai_tts(text, cache_path):
                return cache_path
            if _generate_openai_tts(text, cache_path, voice=OPENAI_TTS_VOICE_BACKUP):
                return cache_path

            # 2. Deepgram Aura TTS
            logger.info("[VOICE] OpenAI failed, trying Deepgram")
            if _generate_deepgram_tts(text, cache_path):
                return cache_path

            # 3. Gemini TTS
            logger.info("[VOICE] Deepgram failed, trying Gemini")
            if _generate_gemini_tts(text, cache_path):
                return cache_path

            # 4. Edge TTS fallback
            logger.info("[VOICE] All paid failed, trying Edge TTS")
            if _generate_edge_tts(text, cache_path, language):
                return cache_path

            return None

    except Exception as e:
        logger.error(f"[VOICE] Generation failed: {e}")
        return None


def generate_voice_for_message(text: str, chat_id: int = 0) -> Optional[str]:
    """Smart voice generation for JARVIS responses."""
    return generate_voice(text)


def generate_voice_response(text: str, language: str = "auto") -> Optional[str]:
    """Alias for generate_voice — used by miniapp API."""
    return generate_voice(text, language)


def text_to_speech_ogg(text: str) -> Optional[str]:
    """Generate OGG from text — used by miniapp API."""
    return generate_voice(text)


# ═══════════════════════════════════════════════════════════
#  SPEECH-TO-TEXT — Transcribe User Voice Messages
# ═══════════════════════════════════════════════════════════

def transcribe_voice_message(audio_path: str) -> Optional[str]:
    """Transcribe voice to text. Groq Whisper → OpenAI Whisper."""
    if not os.path.exists(audio_path):
        logger.error(f"[STT] Audio file not found: {audio_path}")
        return None

    text = _transcribe_groq(audio_path)
    if text:
        return text

    text = _transcribe_openai(audio_path)
    if text:
        return text

    logger.warning("[STT] All transcription failed")
    return None


def _transcribe_groq(audio_path: str) -> Optional[str]:
    """Groq Whisper API (free, fast)."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        with open(audio_path, "rb") as f:
            files = {"file": ("audio.ogg", f, "audio/ogg")}
            data = {"model": "whisper-large-v3", "language": "hi", "response_format": "text"}
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
    """OpenAI Whisper API."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        with open(audio_path, "rb") as f:
            files = {"file": ("audio.ogg", f, "audio/ogg")}
            data = {"model": "whisper-1", "language": "hi", "response_format": "text"}
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
    """Download a Telegram voice message by file_id."""
    try:
        url = f"https://api.telegram.org/bot{token}/getFile"
        resp = requests.get(url, params={"file_id": file_id}, timeout=15)
        data = resp.json()

        if not data.get("ok"):
            logger.error(f"[VOICE-DL] getFile failed: {data}")
            return None

        file_path = data["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        resp = requests.get(download_url, timeout=30)

        if resp.status_code != 200:
            return None

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
    """Send voice message to Telegram — OGG Opus = waveform display = feels LIVE."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendVoice"

        mime = "audio/ogg" if audio_path.endswith('.ogg') else "audio/mpeg"
        fname = "jarvis_voice.ogg" if audio_path.endswith('.ogg') else "jarvis_voice.mp3"

        with open(audio_path, "rb") as f:
            files = {"voice": (fname, f, mime)}
            data = {"chat_id": chat_id}

            if caption:
                data["caption"] = caption[:1024]
                data["parse_mode"] = "Markdown"
            if reply_markup:
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
#  SMART VOICE DECISIONS — When to speak
# ═══════════════════════════════════════════════════════════

def should_send_voice(text: str, intent: str = "", is_voice_input: bool = False) -> bool:
    """
    JARVIS ALWAYS speaks — full automation, no tap-to-play!
    She is a REAL AI assistant — always talking like Gemini Live.
    """
    # ALWAYS send voice — full automation!
    if is_voice_input:
        return True
    if intent:
        return True
    clean = clean_text_for_speech(text)
    if len(clean) > 3:
        return True
    return True  # Even empty — JARVIS always responds


# ═══════════════════════════════════════════════════════════
#  VOICE CACHE CLEANUP
# ═══════════════════════════════════════════════════════════

def cleanup_voice_cache(max_age_hours: int = 1):
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
#  AUTO-PLAY VIDEO NOTE — Gemini Live Experience
# ═══════════════════════════════════════════════════════════

JARVIS_AVATAR_PATH = str(VOICE_CACHE_DIR / "jarvis_avatar.png")

def _ensure_jarvis_avatar() -> str:
    """Create animated JARVIS avatar image for video notes — Iron Man style!"""
    # Regenerate every 10 min for animation variety
    regen = False
    if os.path.exists(JARVIS_AVATAR_PATH):
        if time.time() - os.path.getmtime(JARVIS_AVATAR_PATH) > 600:
            regen = True
        else:
            return JARVIS_AVATAR_PATH
    else:
        regen = True

    if not regen:
        return JARVIS_AVATAR_PATH

    try:
        from PIL import Image, ImageDraw, ImageFont
        import math, random

        size = 480  # Higher res for crisp round bubble
        img = Image.new('RGB', (size, size), '#050520')
        draw = ImageDraw.Draw(img)

        cx, cy = size // 2, size // 2
        t = time.time()

        # Stars background
        random.seed(int(t) // 60)
        for _ in range(80):
            sx = random.randint(0, size)
            sy = random.randint(0, size)
            b = random.randint(80, 255)
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(b, b, b))

        # Outer glow rings
        for r in range(200, 170, -1):
            a = int(60 * (200 - r) / 30)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(20+a, 40+a, 150+min(a,100)))

        # Arc reactor core
        for r in range(120, 0, -1):
            p = r / 120
            red = int(15 + 80 * (1 - p))
            green = int(80 + 150 * (1 - p))
            blue = int(180 + 75 * (1 - p))
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(red, green, blue))

        # Animated waveform bars (changes every call)
        num_bars = 24
        for i in range(num_bars):
            x = cx + (i - num_bars // 2) * 12
            phase = math.sin(t * 1.5 + i * 0.7)
            h = int(20 + 35 * abs(phase))
            brightness = int(140 + 100 * abs(phase))
            draw.rectangle([x-3, cy-h, x+3, cy+h], fill=(brightness//2, brightness, 255))

        # JARVIS text
        try:
            font_lg = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
            font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        except:
            font_lg = ImageFont.load_default()
            font_sm = font_lg

        draw.text((cx, cy + 155), 'J.A.R.V.I.S.', fill=(180, 210, 255), font=font_lg, anchor='mm')
        draw.text((cx, cy + 180), 'Super Brain Online', fill=(100, 140, 200), font=font_sm, anchor='mm')

        # Status LEDs
        labels = ["AI", "MKT", "CRYPTO", "NEWS", "SCAN"]
        for i, lbl in enumerate(labels):
            dx = cx - 110 + i * 55
            dy = cy - 170
            draw.ellipse([dx-5, dy-5, dx+5, dy+5], fill=(0, 255, 80))
            draw.text((dx, dy + 16), lbl, fill=(140, 170, 220), font=font_sm, anchor='mm')

        img.save(JARVIS_AVATAR_PATH)
        logger.info("[VOICE] Created animated JARVIS avatar")
    except ImportError:
        # No PIL — create minimal avatar via ffmpeg later
        logger.warning("[VOICE] PIL not available, video note may use fallback")
        return ""
    except Exception as e:
        logger.error(f"[VOICE] Avatar creation failed: {e}")
        return ""
    return JARVIS_AVATAR_PATH


def create_video_note(audio_ogg_path: str) -> Optional[str]:
    """
    Convert OGG voice to auto-play video note (round bubble).
    Image + Audio -> Square MP4 video that auto-plays in Telegram!
    """
    avatar = _ensure_jarvis_avatar()
    if not avatar or not os.path.exists(audio_ogg_path):
        return None
    try:
        mp4_path = audio_ogg_path.replace('.ogg', '_vnote.mp4')
        result = subprocess.run([
            'ffmpeg', '-y',
            '-loop', '1', '-i', avatar,
            '-i', audio_ogg_path,
            '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k',
            '-s', '480x480',
            '-shortest',
            '-movflags', '+faststart',
            mp4_path
        ], capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 1000:
            logger.info(f"[VOICE] Video note: {os.path.getsize(mp4_path)} bytes")
            return mp4_path
        logger.error(f"[VOICE] Video note ffmpeg failed: {result.stderr[:200]}")
    except Exception as e:
        logger.error(f"[VOICE] Video note error: {e}")
    return None


def send_video_note(chat_id: int, video_path: str, token: str) -> bool:
    """Send auto-play video note (round bubble) to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendVideoNote"
        with open(video_path, 'rb') as f:
            resp = requests.post(url,
                files={'video_note': ('jarvis.mp4', f, 'video/mp4')},
                data={'chat_id': chat_id}, timeout=30)
        if resp.status_code == 200:
            logger.info(f"[VOICE-VNOTE] Auto-play sent to {chat_id}")
            return True
        logger.error(f"[VOICE-VNOTE] Failed: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"[VOICE-VNOTE] Error: {e}")
    return False


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
    'create_video_note',
    'send_video_note',
]
