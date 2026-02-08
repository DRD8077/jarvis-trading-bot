"""
🛠️ JARVIS TOOLS — Weather, Web Search, Song Recognition, Image Generation
═══════════════════════════════════════════════════════════════════════════
Consolidated API integrations for new JARVIS features.
Uses: NEWS_API_KEY, OPENWEATHER_API_KEY, STABILITY_API_KEY,
      GOOGLE_SEARCH_API_KEY, SEARCH_ENGINE_ID, ACRCLOUD_*, MEM0_API_KEY

Author: David Crew AI
"""

import os
import json
import time
import hmac
import hashlib
import base64
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List
from io import BytesIO

logger = logging.getLogger("jarvis_tools")

# ═══════════════════════════════════════════════════════════
#  API KEYS (from .env)
# ═══════════════════════════════════════════════════════════

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY", "")
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID", "")
MEM0_API_KEY = os.environ.get("MEM0_API_KEY", "")
ACRCLOUD_ACCESS_KEY = os.environ.get("ACRCLOUD_ACCESS_KEY", "")
ACRCLOUD_SECRET_KEY = os.environ.get("ACRCLOUD_SECRET_KEY", "")


# ═══════════════════════════════════════════════════════════
#  🌤️ WEATHER ENGINE (OpenWeatherMap)
# ═══════════════════════════════════════════════════════════

def get_weather(city: str = "Mumbai") -> str:
    """Get current weather + 3-day forecast for any city."""
    if not OPENWEATHER_API_KEY:
        return "⚠️ Weather API key not configured."
    
    try:
        # Current weather
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return f"⚠️ City '{city}' not found. Try: Mumbai, Delhi, Bangalore..."
        
        data = r.json()
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"].title()
        wind = data["wind"]["speed"]
        icon = _weather_emoji(data["weather"][0]["main"])
        city_name = data["name"]
        country = data["sys"]["country"]
        
        # Forecast (next 3 days)
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        fr = requests.get(forecast_url, params=params, timeout=10)
        forecast_text = ""
        if fr.status_code == 200:
            fdata = fr.json()
            days_seen = set()
            forecasts = []
            for item in fdata["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                day_key = dt.strftime("%A")
                if day_key not in days_seen and len(days_seen) < 3:
                    days_seen.add(day_key)
                    f_temp = item["main"]["temp"]
                    f_desc = item["weather"][0]["description"].title()
                    f_icon = _weather_emoji(item["weather"][0]["main"])
                    forecasts.append(f"  {f_icon} *{day_key}:* {f_temp:.0f}°C — {f_desc}")
            if forecasts:
                forecast_text = "\n📅 *3-Day Forecast:*\n" + "\n".join(forecasts)
        
        msg = (
            f"{icon} *Weather — {city_name}, {country}* {icon}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌡️ *Temperature:* {temp:.1f}°C (Feels like {feels:.1f}°C)\n"
            f"☁️ *Condition:* {desc}\n"
            f"💧 *Humidity:* {humidity}%\n"
            f"💨 *Wind:* {wind} m/s\n"
            f"{forecast_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Updated: {datetime.now().strftime('%I:%M %p')}"
        )
        return msg
        
    except Exception as e:
        logger.error(f"[WEATHER] Error: {e}")
        return f"⚠️ Weather fetch failed: {e}"


def _weather_emoji(condition: str) -> str:
    """Map weather condition to emoji."""
    mapping = {
        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️",
        "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Snow": "❄️",
        "Mist": "🌫️", "Fog": "🌫️", "Haze": "🌫️",
        "Smoke": "💨", "Dust": "🌪️", "Sand": "🌪️",
    }
    return mapping.get(condition, "🌤️")


# ═══════════════════════════════════════════════════════════
#  🔍 WEB SEARCH ENGINE (Google Custom Search)
# ═══════════════════════════════════════════════════════════

def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using Google Custom Search API."""
    if not GOOGLE_SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        return "⚠️ Google Search API not configured."
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": min(num_results, 10)
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return f"⚠️ Search failed (status {r.status_code})"
        
        data = r.json()
        items = data.get("items", [])
        if not items:
            return f"🔍 No results found for: {query}"
        
        total = data.get("searchInformation", {}).get("totalResults", "?")
        
        results = [
            f"🔍 *Google Search: {query}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 About {total} results\n"
        ]
        
        for i, item in enumerate(items[:num_results], 1):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "").replace("\n", " ")[:150]
            link = item.get("link", "")
            results.append(
                f"\n{i}. *{title}*\n"
                f"   {snippet}\n"
                f"   🔗 {link}"
            )
        
        results.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        return f"⚠️ Search failed: {e}"


# ═══════════════════════════════════════════════════════════
#  🎵 SONG RECOGNITION (ACRCloud)
# ═══════════════════════════════════════════════════════════

def identify_song(audio_bytes: bytes) -> str:
    """Identify a song from audio bytes using ACRCloud."""
    if not ACRCLOUD_ACCESS_KEY or not ACRCLOUD_SECRET_KEY:
        return "⚠️ Song recognition (ACRCloud) not configured."
    
    try:
        host = "identify-eu-west-1.acrcloud.com"
        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        timestamp = str(int(time.time()))
        
        string_to_sign = (
            f"{http_method}\n{http_uri}\n{ACRCLOUD_ACCESS_KEY}\n"
            f"{data_type}\n{signature_version}\n{timestamp}"
        )
        
        sign = base64.b64encode(
            hmac.new(
                ACRCLOUD_SECRET_KEY.encode('ascii'),
                string_to_sign.encode('ascii'),
                digestmod=hashlib.sha1
            ).digest()
        ).decode('ascii')
        
        files = {"sample": ("audio.ogg", audio_bytes, "audio/ogg")}
        data = {
            "access_key": ACRCLOUD_ACCESS_KEY,
            "sample_bytes": len(audio_bytes),
            "timestamp": timestamp,
            "signature": sign,
            "data_type": data_type,
            "signature_version": signature_version,
        }
        
        r = requests.post(
            f"https://{host}{http_uri}",
            files=files,
            data=data,
            timeout=15
        )
        
        result = r.json()
        status_code = result.get("status", {}).get("code", -1)
        
        if status_code == 0:
            # Song found!
            music = result.get("metadata", {}).get("music", [{}])[0]
            title = music.get("title", "Unknown")
            artists = ", ".join(a.get("name", "") for a in music.get("artists", [{"name": "Unknown"}]))
            album = music.get("album", {}).get("name", "")
            release = music.get("release_date", "")
            score = music.get("score", 0)
            
            # Try to get Spotify/YouTube links
            external = music.get("external_metadata", {})
            spotify_id = external.get("spotify", {}).get("track", {}).get("id", "")
            youtube_id = external.get("youtube", {}).get("vid", "")
            
            msg = (
                f"🎵 *Song Identified!* 🎵\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎶 *Title:* {title}\n"
                f"👤 *Artist:* {artists}\n"
            )
            if album:
                msg += f"💿 *Album:* {album}\n"
            if release:
                msg += f"📅 *Released:* {release}\n"
            msg += f"📊 *Match:* {score}%\n"
            
            if spotify_id:
                msg += f"\n🎧 *Spotify:* https://open.spotify.com/track/{spotify_id}"
            if youtube_id:
                msg += f"\n▶️ *YouTube:* https://youtube.com/watch?v={youtube_id}"
            
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return msg
        
        elif status_code == 1001:
            return "🎵 Couldn't identify the song. Try sending a clearer audio clip with the music."
        else:
            return f"🎵 Song recognition failed (code {status_code}). Try a longer/clearer clip."
            
    except Exception as e:
        logger.error(f"[SONG] ACRCloud error: {e}")
        return f"⚠️ Song recognition error: {e}"


# ═══════════════════════════════════════════════════════════
#  🎨 IMAGE GENERATION (Stability AI)
# ═══════════════════════════════════════════════════════════

def generate_image(prompt: str) -> Optional[bytes]:
    """Generate an image from text prompt using Stability AI."""
    if not STABILITY_API_KEY:
        return None
    
    try:
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }
        
        data = {
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "1:1",
            "model": "sd3.5-large-turbo",
        }
        
        r = requests.post(url, headers=headers, files={"none": ""}, data=data, timeout=60)
        
        if r.status_code == 200:
            return r.content
        
        # Fallback to SD3 medium
        data["model"] = "sd3-medium"
        r = requests.post(url, headers=headers, files={"none": ""}, data=data, timeout=60)
        
        if r.status_code == 200:
            return r.content
        
        # Fallback to SDXL
        url2 = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers2 = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        body = {
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        r2 = requests.post(url2, headers=headers2, json=body, timeout=60)
        if r2.status_code == 200:
            data2 = r2.json()
            if data2.get("artifacts"):
                img_b64 = data2["artifacts"][0]["base64"]
                return base64.b64decode(img_b64)
        
        logger.error(f"[IMAGE] Stability AI failed: {r.status_code} / {r2.status_code}")
        return None
        
    except Exception as e:
        logger.error(f"[IMAGE] Generation error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  📰 ENHANCED NEWS (NewsAPI.org)
# ═══════════════════════════════════════════════════════════

def get_news_headlines(category: str = "business", country: str = "in", count: int = 10) -> str:
    """Get top headlines from NewsAPI.org."""
    if not NEWS_API_KEY:
        return ""  # Return empty so RSS fallback can be used
    
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "country": country,
            "category": category,
            "pageSize": count
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return ""
        
        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return ""
        
        headlines = [
            f"📰 *Top {category.title()} Headlines ({country.upper()})* 📰\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        
        for i, article in enumerate(articles[:count], 1):
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "")
            desc = (article.get("description") or "")[:100]
            url_ = article.get("url", "")
            
            headlines.append(
                f"{i}. *{title}*\n"
                f"   📌 {source}"
            )
            if desc:
                headlines.append(f"   _{desc}_")
            if url_:
                headlines.append(f"   🔗 {url_}")
            headlines.append("")
        
        headlines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(headlines)
        
    except Exception as e:
        logger.error(f"[NEWS] NewsAPI error: {e}")
        return ""


def get_crypto_news(count: int = 8) -> str:
    """Get crypto-specific news."""
    if not NEWS_API_KEY:
        return ""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": NEWS_API_KEY,
            "q": "cryptocurrency OR bitcoin OR ethereum OR solana",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": count
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return ""
        
        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return ""
        
        headlines = [
            f"🪙 *Crypto News* 🪙\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        for i, a in enumerate(articles[:count], 1):
            title = a.get("title", "")
            source = a.get("source", {}).get("name", "")
            headlines.append(f"{i}. *{title}*\n   📌 {source}\n")
        
        headlines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(headlines)
        
    except Exception as e:
        logger.error(f"[NEWS] Crypto news error: {e}")
        return ""


# ═══════════════════════════════════════════════════════════
#  🧠 MEM0 MEMORY (Persistent Semantic Memory)
# ═══════════════════════════════════════════════════════════

def mem0_add(user_id: str, text: str, metadata: dict = None) -> bool:
    """Add a memory to Mem0."""
    if not MEM0_API_KEY:
        return False
    try:
        url = "https://api.mem0.ai/v1/memories/"
        headers = {
            "Authorization": f"Token {MEM0_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "messages": [{"role": "user", "content": text}],
            "user_id": str(user_id),
        }
        if metadata:
            body["metadata"] = metadata
        
        r = requests.post(url, headers=headers, json=body, timeout=10)
        return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"[MEM0] Add error: {e}")
        return False


def mem0_search(user_id: str, query: str, limit: int = 5) -> List[Dict]:
    """Search memories from Mem0."""
    if not MEM0_API_KEY:
        return []
    try:
        url = "https://api.mem0.ai/v1/memories/search/"
        headers = {
            "Authorization": f"Token {MEM0_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "query": query,
            "user_id": str(user_id),
            "limit": limit
        }
        r = requests.post(url, headers=headers, json=body, timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    except Exception as e:
        logger.error(f"[MEM0] Search error: {e}")
        return []


def mem0_get_all(user_id: str) -> List[Dict]:
    """Get all memories for a user from Mem0."""
    if not MEM0_API_KEY:
        return []
    try:
        url = f"https://api.mem0.ai/v1/memories/?user_id={user_id}"
        headers = {
            "Authorization": f"Token {MEM0_API_KEY}",
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    except Exception as e:
        logger.error(f"[MEM0] Get all error: {e}")
        return []


# ═══════════════════════════════════════════════════════════
#  AVAILABILITY FLAGS
# ═══════════════════════════════════════════════════════════

WEATHER_AVAILABLE = bool(OPENWEATHER_API_KEY)
SEARCH_AVAILABLE = bool(GOOGLE_SEARCH_API_KEY and SEARCH_ENGINE_ID)
SONG_AVAILABLE = bool(ACRCLOUD_ACCESS_KEY and ACRCLOUD_SECRET_KEY)
IMAGE_AVAILABLE = bool(STABILITY_API_KEY)
NEWS_ENHANCED = bool(NEWS_API_KEY)
MEM0_AVAILABLE = bool(MEM0_API_KEY)

logger.info(
    f"[TOOLS] Loaded: Weather={'✅' if WEATHER_AVAILABLE else '❌'} "
    f"Search={'✅' if SEARCH_AVAILABLE else '❌'} "
    f"Song={'✅' if SONG_AVAILABLE else '❌'} "
    f"Image={'✅' if IMAGE_AVAILABLE else '❌'} "
    f"News+={'✅' if NEWS_ENHANCED else '❌'} "
    f"Mem0={'✅' if MEM0_AVAILABLE else '❌'}"
)
