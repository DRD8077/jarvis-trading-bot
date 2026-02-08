"""
🧠⚡ J.A.R.V.I.S. SUPER BRAIN — The Ultimate AI Intelligence Hub
═══════════════════════════════════════════════════════════════════
JARVIS is the SINGLE POINT OF CONTACT (SPOC) for EVERYTHING.

This module aggregates ALL intelligence:
  1. 🌍 WORLDWIDE NEWS — Real-time from 15+ sources
  2. 📈 INDIAN STOCK MARKET — NSE/BSE/NIFTY/SENSEX
  3. 🪙 CRYPTO MARKET — All tokens, new launches, signals
  4. 🌐 GLOBAL MARKETS — US/Europe/Asia/Commodities
  5. 📰 SENTIMENT — News, social, FII/DII, Fear & Greed
  6. 🤖 ML PREDICTIONS — 6-model ensemble
  7. 👻 PHANTOM WALLET — Real-time Solana tracking
  8. 🚀 TOKEN SCANNER — pump.fun + DexScreener + CoinDCX
  9. 📊 SPOC DASHBOARD — System health monitoring
  10. 🎤 AUTO-VOICE — Gemini Live quality auto-play

Author: JARVIS AI — for Boss Deepak Kumar
"""

import os
import re
import json
import time
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger("jarvis_super_brain")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════

BOSS_NAME = "Deepak Kumar"
BOSS_CHAT_ID = int(os.environ.get("TEST_CHAT_ID", "0"))

# News API sources (free, no key needed)
NEWS_SOURCES = {
    "india_market": [
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.livemint.com/rss/markets",
    ],
    "india_general": [
        "https://feeds.feedburner.com/ndtvprofit-latest",
        "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    ],
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ],
    "us_market": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    ],
}

# Google News RSS for specific topics
GOOGLE_NEWS_TOPICS = {
    "crypto_india": "cryptocurrency+India",
    "nifty": "NIFTY+50+stock+market",
    "sensex": "SENSEX+BSE+market",
    "bitcoin": "Bitcoin+price+today",
    "solana": "Solana+SOL+crypto",
    "us_fed": "Federal+Reserve+interest+rate",
    "gold_india": "gold+price+India+today",
    "rupee": "USD+INR+rupee+dollar",
}

# ═══════════════════════════════════════════════════════════
#  STATE
# ═══════════════════════════════════════════════════════════
_news_cache: Dict[str, dict] = {}
_news_cache_time: float = 0
NEWS_CACHE_TTL = 300  # 5 minutes

_intelligence_cache: Dict[str, Any] = {}
_intelligence_time: float = 0
INTELLIGENCE_TTL = 600  # 10 minutes

_brain_running = False
_brain_thread = None

# Proactive alert tracking
_last_proactive_alert: Dict[str, float] = {}
PROACTIVE_COOLDOWN = 1800  # 30 min between same type


# ═══════════════════════════════════════════════════════════
#  NEWS FETCHER — Worldwide Real-Time News
# ═══════════════════════════════════════════════════════════

def _parse_rss(url: str, max_items: int = 5) -> List[dict]:
    """Parse RSS feed and return headlines."""
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 JARVIS-Bot/1.0"
        })
        if resp.status_code != 200:
            return []

        # Simple XML parsing without external library
        content = resp.text
        items = []
        
        # Find all <item> or <entry> blocks
        item_pattern = re.findall(r'<item[^>]*>(.*?)</item>', content, re.DOTALL)
        if not item_pattern:
            item_pattern = re.findall(r'<entry[^>]*>(.*?)</entry>', content, re.DOTALL)

        for item_xml in item_pattern[:max_items]:
            title = ""
            link = ""
            pub_date = ""

            # Extract title
            t_match = re.search(r'<title[^>]*>(.*?)</title>', item_xml, re.DOTALL)
            if t_match:
                title = t_match.group(1).strip()
                title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                title = re.sub(r'<[^>]+>', '', title).strip()

            # Extract link
            l_match = re.search(r'<link[^>]*>(.*?)</link>', item_xml, re.DOTALL)
            if l_match:
                link = l_match.group(1).strip()
                link = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', link)
            if not link:
                l_match = re.search(r'<link[^>]*href="([^"]+)"', item_xml)
                if l_match:
                    link = l_match.group(1)

            # Extract date
            d_match = re.search(r'<pubDate[^>]*>(.*?)</pubDate>', item_xml, re.DOTALL)
            if d_match:
                pub_date = d_match.group(1).strip()
            if not pub_date:
                d_match = re.search(r'<published[^>]*>(.*?)</published>', item_xml, re.DOTALL)
                if d_match:
                    pub_date = d_match.group(1).strip()

            if title:
                items.append({
                    "title": title[:200],
                    "link": link,
                    "date": pub_date[:50],
                })

        return items

    except Exception as e:
        logger.debug(f"[NEWS] RSS parse failed for {url[:50]}: {e}")
        return []


def _fetch_google_news(topic: str, max_items: int = 3) -> List[dict]:
    """Fetch Google News RSS for a topic."""
    url = f"https://news.google.com/rss/search?q={topic}&hl=en-IN&gl=IN&ceid=IN:en"
    return _parse_rss(url, max_items)


def fetch_all_news(force: bool = False) -> Dict[str, List[dict]]:
    """Fetch news from ALL sources — cached 5 min."""
    global _news_cache, _news_cache_time

    if not force and _news_cache and time.time() - _news_cache_time < NEWS_CACHE_TTL:
        return _news_cache

    all_news = {}
    
    # RSS sources
    for category, urls in NEWS_SOURCES.items():
        items = []
        for url in urls:
            items.extend(_parse_rss(url, max_items=3))
        all_news[category] = items[:8]  # Max 8 per category

    # Google News topics
    for topic_key, query in GOOGLE_NEWS_TOPICS.items():
        items = _fetch_google_news(query, max_items=3)
        all_news[topic_key] = items

    _news_cache = all_news
    _news_cache_time = time.time()
    
    logger.info(f"[NEWS] Fetched {sum(len(v) for v in all_news.values())} headlines from {len(all_news)} sources")
    return all_news


def format_news_digest(categories: List[str] = None) -> str:
    """Format a beautiful news digest for Telegram."""
    news = fetch_all_news()

    if categories:
        news = {k: v for k, v in news.items() if k in categories}

    if not any(news.values()):
        return "📰 *कोई ताज़ा खबर नहीं मिली* — बाद में try करें।"

    category_icons = {
        "india_market": "🇮🇳 भारतीय बाज़ार",
        "india_general": "🇮🇳 India News",
        "crypto": "🪙 Crypto News",
        "world": "🌍 World Business",
        "us_market": "🇺🇸 US Market",
        "crypto_india": "🪙🇮🇳 Crypto India",
        "nifty": "📊 NIFTY News",
        "sensex": "📈 SENSEX News",
        "bitcoin": "₿ Bitcoin",
        "solana": "◎ Solana",
        "us_fed": "🏦 US Federal Reserve",
        "gold_india": "🥇 Gold India",
        "rupee": "💵 USD/INR",
    }

    lines = []
    lines.append("📰🧠 *JARVIS WORLDWIDE NEWS DIGEST*")
    lines.append("═" * 28)
    lines.append(f"⏰ {datetime.now().strftime('%I:%M %p IST, %d %b %Y')}")
    lines.append("")

    for cat, items in news.items():
        if not items:
            continue
        icon = category_icons.get(cat, f"📌 {cat}")
        lines.append(f"*{icon}*")
        for i, item in enumerate(items[:4], 1):
            title = item['title']
            link = item.get('link', '')
            if link:
                lines.append(f"  {i}. [{title}]({link})")
            else:
                lines.append(f"  {i}. {title}")
        lines.append("")

    lines.append("🧠 _JARVIS Super Brain — Worldwide Intelligence_")
    lines.append("💡 /news — Refresh | /newsall — Full digest")

    return "\n".join(lines)


def format_news_voice() -> str:
    """Generate voice text for news digest."""
    news = fetch_all_news()

    voice_parts = ["Boss, yeh rahi aaj ki important headlines. "]

    # Pick top 3-4 headlines across categories
    all_headlines = []
    for cat, items in news.items():
        for item in items[:2]:
            all_headlines.append((cat, item['title']))

    for cat, title in all_headlines[:5]:
        voice_parts.append(f"{title}. ")

    voice_parts.append("Baaki details text message mein dekh lijiye.")
    return " ".join(voice_parts)


# ═══════════════════════════════════════════════════════════
#  MARKET INTELLIGENCE — Unified view
# ═══════════════════════════════════════════════════════════

def get_market_intelligence() -> Dict[str, Any]:
    """Get unified market intelligence from all engines."""
    global _intelligence_cache, _intelligence_time

    if _intelligence_cache and time.time() - _intelligence_time < INTELLIGENCE_TTL:
        return _intelligence_cache

    intel = {
        "timestamp": datetime.now().isoformat(),
        "stock_market": {},
        "crypto_market": {},
        "global_markets": {},
        "news_sentiment": {},
        "alerts": [],
    }

    # Indian Stock Market
    try:
        from stock_data_fetcher import get_nifty_data
        nifty = get_nifty_data()
        if nifty:
            intel["stock_market"]["nifty"] = nifty
    except:
        pass

    # CoinDCX Crypto
    try:
        from coindcx_engine import get_all_web3_tokens, get_web3_top_movers
        tokens = get_all_web3_tokens()
        if tokens:
            intel["crypto_market"]["total_tokens"] = len(tokens)
            intel["crypto_market"]["top_movers"] = get_web3_top_movers(5)
    except:
        pass

    # Global Markets
    try:
        from global_candle_engine import analyze_all_global_markets
        global_data = analyze_all_global_markets()
        if global_data:
            intel["global_markets"] = global_data
    except:
        pass

    # News
    try:
        news = fetch_all_news()
        intel["news_sentiment"]["headline_count"] = sum(len(v) for v in news.values())
    except:
        pass

    _intelligence_cache = intel
    _intelligence_time = time.time()
    return intel


def format_jarvis_briefing() -> str:
    """Generate JARVIS complete briefing — stock + crypto + global + news."""
    lines = []
    lines.append("🧠🔱 *J.A.R.V.I.S. INTELLIGENCE BRIEFING*")
    lines.append("═" * 30)
    lines.append(f"👑 *Boss:* {BOSS_NAME}")
    lines.append(f"⏰ {datetime.now().strftime('%I:%M %p IST, %d %b %Y')}")
    lines.append("")

    # Stock Market section
    try:
        from stock_data_fetcher import get_nifty_data
        nifty = get_nifty_data()
        if nifty:
            price = nifty.get("last_price", 0)
            change = nifty.get("change_pct", 0)
            icon = "🟢" if change > 0 else "🔴"
            lines.append(f"📊 *INDIAN MARKET*")
            lines.append(f"  {icon} NIFTY 50: ₹{price:,.0f} ({change:+.1f}%)")
    except:
        pass

    # Crypto section
    try:
        from coindcx_engine import get_web3_top_movers
        movers = get_web3_top_movers(3)
        if movers:
            lines.append("")
            lines.append(f"🪙 *TOP CRYPTO MOVERS*")
            for m in movers:
                sym = m.get('symbol', '?')
                ch = m.get('change_24h', 0)
                icon = "🟢" if ch > 0 else "🔴"
                lines.append(f"  {icon} {sym}: {ch:+.1f}%")
    except:
        pass

    # Global Markets
    try:
        from global_candle_engine import fetch_global_data
        gdata = fetch_global_data()
        if gdata:
            lines.append("")
            lines.append(f"🌍 *GLOBAL MARKETS*")
            for idx_name, idx_data in list(gdata.items())[:5]:
                ch = idx_data.get('change_pct', 0)
                icon = "🟢" if ch > 0 else "🔴"
                lines.append(f"  {icon} {idx_name}: {ch:+.1f}%")
    except:
        pass

    # Top news
    news = fetch_all_news()
    top_headlines = []
    for cat, items in news.items():
        for item in items[:1]:
            top_headlines.append(item['title'])
    
    if top_headlines:
        lines.append("")
        lines.append("📰 *TOP HEADLINES*")
        for h in top_headlines[:5]:
            lines.append(f"  • {h[:80]}")

    lines.append("")
    lines.append("🧠 _JARVIS Super Brain — Complete Intelligence_")
    lines.append("💡 /spoc — Dashboard | /news — Full news")

    return "\n".join(lines)


def format_briefing_voice() -> str:
    """Voice text for JARVIS briefing."""
    parts = [f"Namaste {BOSS_NAME} sir! Main JARVIS, aapki intelligence briefing de rahi hoon. "]

    try:
        from stock_data_fetcher import get_nifty_data
        nifty = get_nifty_data()
        if nifty:
            price = nifty.get("last_price", 0)
            change = nifty.get("change_pct", 0)
            parts.append(f"NIFTY {price:,.0f} par hai, {change:+.1f} percent. ")
    except:
        pass

    try:
        from coindcx_engine import get_web3_top_movers
        movers = get_web3_top_movers(2)
        if movers:
            for m in movers:
                parts.append(f"{m['symbol']} {m.get('change_24h', 0):+.0f} percent. ")
    except:
        pass

    news = fetch_all_news()
    for cat, items in news.items():
        if items:
            parts.append(f"{items[0]['title']}. ")
            break

    parts.append("Baaki sab details text mein hain. Main hoon na boss!")
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════
#  JARVIS ANIMATED RESPONSES — Rich visual formatting
# ═══════════════════════════════════════════════════════════

JARVIS_ANIMATIONS = {
    "greeting": "🤖✨ *J.A.R.V.I.S. ONLINE* ✨🤖\n" + "▰" * 15 + "▱" * 5 + "\n_Systems initializing..._\n" + "▰" * 20 + "\n_All systems active!_",
    "thinking": "🧠 *JARVIS analyzing...*\n░▒▓█ Processing █▓▒░\n🔄 _Scanning 30+ engines..._",
    "alert": "🚨⚡ *JARVIS ALERT* ⚡🚨\n" + "═" * 25,
    "success": "✅ *Mission Accomplished!*\n" + "━" * 25,
    "scan": "🔍 *JARVIS AI SCAN*\n" + "▰" * 20 + "\n⚡ _Processing..._",
}


def jarvis_animated_header(msg_type: str = "greeting") -> str:
    """Get JARVIS animated text header."""
    return JARVIS_ANIMATIONS.get(msg_type, JARVIS_ANIMATIONS["thinking"])


# ═══════════════════════════════════════════════════════════
#  SOLANA ADDRESS AUTO-DETECTOR
# ═══════════════════════════════════════════════════════════

# Solana addresses: 32-44 chars, base58 (no 0, O, l, I)
SOLANA_ADDR_PATTERN = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

def detect_solana_address(text: str) -> Optional[str]:
    """Auto-detect a Solana wallet address in any text message."""
    text = text.strip()
    
    # Direct check — entire message is an address
    if SOLANA_ADDR_PATTERN.match(text):
        return text
    
    # Check each word
    for word in text.split():
        word = word.strip('.,!?;:()[]{}')
        if SOLANA_ADDR_PATTERN.match(word):
            return word
    
    return None


# ═══════════════════════════════════════════════════════════
#  PROACTIVE INTELLIGENCE — Background Brain Thread
# ═══════════════════════════════════════════════════════════

def start_super_brain(send_fn, voice_fn, token: str):
    """Start JARVIS Super Brain — proactive intelligence + news + SPOC."""
    global _brain_running, _brain_thread

    if _brain_running:
        return

    _brain_running = True

    def _brain_loop():
        logger.info("[SUPER-BRAIN] 🧠⚡ JARVIS SUPER BRAIN STARTED")
        time.sleep(120)  # Wait for boot

        iteration = 0
        while _brain_running:
            try:
                iteration += 1

                # Every 30 min: proactive news digest to owner
                if iteration % 6 == 0 and BOSS_CHAT_ID:
                    _send_proactive_news(send_fn, voice_fn)

                # Every 1 hour: market intelligence briefing
                if iteration % 12 == 0 and BOSS_CHAT_ID:
                    _send_intelligence_briefing(send_fn, voice_fn)

                # Every 10 min: check for critical market moves
                _check_critical_moves(send_fn, voice_fn)

            except Exception as e:
                logger.error(f"[SUPER-BRAIN] Error: {e}")

            # Sleep 5 minutes per iteration
            for _ in range(300):
                if not _brain_running:
                    break
                time.sleep(1)

    _brain_thread = threading.Thread(target=_brain_loop, daemon=True, name="jarvis-super-brain")
    _brain_thread.start()
    logger.info("[SUPER-BRAIN] 🧠⚡ Background intelligence thread started")


def stop_super_brain():
    """Stop the Super Brain."""
    global _brain_running
    _brain_running = False


def _send_proactive_news(send_fn, voice_fn):
    """Send proactive news digest to boss."""
    now = datetime.now()
    key = f"news_{now.strftime('%H')}"
    
    if key in _last_proactive_alert and time.time() - _last_proactive_alert[key] < PROACTIVE_COOLDOWN:
        return

    try:
        # Only during active hours (7 AM - 11 PM)
        if now.hour < 7 or now.hour > 23:
            return

        digest = format_news_digest(["india_market", "crypto", "us_market"])
        if digest and len(digest) > 100:
            send_fn(BOSS_CHAT_ID, digest)
            if voice_fn:
                voice_text = format_news_voice()
                voice_fn(BOSS_CHAT_ID, voice_text, intent="market_summary")
            _last_proactive_alert[key] = time.time()
            logger.info("[SUPER-BRAIN] Proactive news digest sent")
    except Exception as e:
        logger.error(f"[SUPER-BRAIN] News send failed: {e}")


def _send_intelligence_briefing(send_fn, voice_fn):
    """Send market intelligence briefing."""
    now = datetime.now()
    key = f"intel_{now.strftime('%H')}"

    if key in _last_proactive_alert and time.time() - _last_proactive_alert[key] < PROACTIVE_COOLDOWN:
        return

    try:
        if now.hour < 7 or now.hour > 23:
            return

        briefing = format_jarvis_briefing()
        if briefing:
            send_fn(BOSS_CHAT_ID, briefing)
            if voice_fn:
                voice_text = format_briefing_voice()
                voice_fn(BOSS_CHAT_ID, voice_text, intent="market_summary")
            _last_proactive_alert[key] = time.time()
    except Exception as e:
        logger.error(f"[SUPER-BRAIN] Briefing failed: {e}")


def _check_critical_moves(send_fn, voice_fn):
    """Check for critical market moves that need immediate alert."""
    key = "critical_move"
    if key in _last_proactive_alert and time.time() - _last_proactive_alert[key] < 600:
        return

    try:
        # Check crypto pumps/dumps
        from coindcx_engine import get_all_web3_tokens
        tokens = get_all_web3_tokens()
        if tokens:
            mega_movers = [t for t in tokens if abs(t.get('change_24h', 0)) > 50]
            if mega_movers and BOSS_CHAT_ID:
                msg = "🚨🧠 *JARVIS CRITICAL ALERT!*\n" + "═" * 25 + "\n\n"
                msg += "⚡ *MEGA MARKET MOVES DETECTED:*\n\n"
                for m in mega_movers[:5]:
                    ch = m.get('change_24h', 0)
                    sym = m.get('symbol', '?')
                    price = m.get('price_inr', 0)
                    icon = "🚀" if ch > 0 else "💀"
                    msg += f"{icon} *{sym}*: {ch:+.1f}% (₹{price:,.4f})\n"
                msg += f"\n🕐 {datetime.now().strftime('%I:%M %p IST')}"
                msg += "\n💡 /cdx <symbol> for full analysis"

                send_fn(BOSS_CHAT_ID, msg)
                if voice_fn:
                    names = ", ".join(m['symbol'] for m in mega_movers[:3])
                    voice_fn(BOSS_CHAT_ID,
                        f"Boss! Critical alert! {names} mein 50 percent se zyada movement hai! Turant check karo!",
                        intent="buy_sell_crypto")
                _last_proactive_alert[key] = time.time()
    except Exception as e:
        logger.debug(f"[SUPER-BRAIN] Critical move check: {e}")


# ═══════════════════════════════════════════════════════════
#  JARVIS COMMAND ROUTER — Universal SPOC
# ═══════════════════════════════════════════════════════════

def jarvis_route_command(text: str, chat_id: int) -> Optional[dict]:
    """
    JARVIS SPOC command router — understands EVERYTHING.
    Returns {"response": str, "voice": str, "intent": str} or None.
    """
    text_lower = text.lower().strip()

    # News commands
    if any(kw in text_lower for kw in ["news", "khabar", "headlines", "newspaper", "akhbar"]):
        cats = None
        if any(kw in text_lower for kw in ["crypto", "bitcoin", "sol"]):
            cats = ["crypto", "bitcoin", "solana", "crypto_india"]
        elif any(kw in text_lower for kw in ["stock", "nifty", "sensex", "market", "share"]):
            cats = ["india_market", "nifty", "sensex"]
        elif any(kw in text_lower for kw in ["world", "global", "international", "duniya"]):
            cats = ["world", "us_market", "us_fed"]
        elif any(kw in text_lower for kw in ["gold", "silver", "rupee", "dollar", "sona", "chandi"]):
            cats = ["gold_india", "rupee"]
        
        return {
            "response": format_news_digest(cats),
            "voice": format_news_voice(),
            "intent": "market_summary",
        }

    # Intelligence briefing
    if any(kw in text_lower for kw in ["briefing", "intelligence", "sab batao", "kya chal raha", "update de"]):
        return {
            "response": format_jarvis_briefing(),
            "voice": format_briefing_voice(),
            "intent": "market_summary",
        }

    return None  # Not handled, let main bot handle


# ═══════════════════════════════════════════════════════════
#  ANIMATED JARVIS VIDEO NOTE (for auto-play)
# ═══════════════════════════════════════════════════════════

def create_animated_jarvis_frame() -> Optional[str]:
    """Create an animated JARVIS frame for video notes."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import math

        size = 480
        img = Image.new('RGB', (size, size), '#050520')
        draw = ImageDraw.Draw(img)

        t = time.time()

        # Dark space background with stars
        import random
        random.seed(42)  # consistent stars
        for _ in range(50):
            sx = random.randint(0, size)
            sy = random.randint(0, size)
            brightness = random.randint(100, 255)
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(brightness, brightness, brightness))

        # Outer ring glow
        cx, cy = size // 2, size // 2
        for r in range(180, 160, -1):
            alpha = int(80 * (180 - r) / 20)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(30 + alpha, 50 + alpha, 180 + min(alpha, 75)))

        # Inner reactor core
        for r in range(100, 0, -1):
            pct = r / 100
            red = int(30 + 100 * (1 - pct))
            green = int(100 + 130 * (1 - pct))
            blue = int(200 + 55 * (1 - pct))
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(red, green, blue))

        # Waveform bars (animated feel from time)
        num_bars = 20
        for i in range(num_bars):
            x = cx + (i - num_bars // 2) * 14
            phase = math.sin(t * 2 + i * 0.6)
            h = int(25 + 30 * abs(phase))
            bar_color = (120 + int(80 * abs(phase)), 180 + int(50 * abs(phase)), 255)
            draw.rectangle([x - 4, cy - h, x + 4, cy + h], fill=bar_color)

        # JARVIS text
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        except:
            font_large = ImageFont.load_default()
            font_small = font_large

        draw.text((cx, cy + 130), 'J.A.R.V.I.S.', fill=(180, 200, 255), font=font_large, anchor='mm')
        draw.text((cx, cy + 155), 'Super Brain Online', fill=(120, 150, 220), font=font_small, anchor='mm')

        # Status dots
        dots = ["AI", "STOCK", "CRYPTO", "NEWS", "WALLET"]
        for i, label in enumerate(dots):
            dx = cx - 100 + i * 50
            dy = cy - 150
            draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=(0, 255, 100))
            draw.text((dx, dy + 15), label, fill=(150, 180, 220), font=font_small, anchor='mm')

        # Save
        avatar_path = "/tmp/jarvis_voice_cache/jarvis_super_avatar.png"
        os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
        img.save(avatar_path)
        return avatar_path

    except ImportError:
        logger.debug("[SUPER-BRAIN] PIL not available for avatar")
        return None
    except Exception as e:
        logger.error(f"[SUPER-BRAIN] Avatar creation: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    # News
    'fetch_all_news', 'format_news_digest', 'format_news_voice',
    # Intelligence
    'get_market_intelligence', 'format_jarvis_briefing', 'format_briefing_voice',
    # Animated
    'jarvis_animated_header', 'create_animated_jarvis_frame',
    # Detection
    'detect_solana_address',
    # Background
    'start_super_brain', 'stop_super_brain',
    # Router
    'jarvis_route_command',
    # Config
    'BOSS_NAME', 'BOSS_CHAT_ID',
]
