"""
========================================================================================
  INDIAN MARKET SENTIMENT & NEWS ENGINE — Real-Time Sentiment Analysis
========================================================================================

Analyzes sentiment from multiple Indian market sources:
  - RSS feeds from MoneyControl, Economic Times, LiveMint, NDTV Profit
  - Google News RSS for NIFTY/SENSEX headlines
  - FII/DII flow sentiment proxy
  - Market breadth indicators (advance/decline ratio)
  - Social sentiment scoring with NLP
  - Fear & Greed Index (custom for Indian market)

All analysis in INR context for NSE/BSE.
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger("sentiment_engine")

# ═══════════════════════════════════════════════════════════════════════════
#  NEWS FETCHING (RSS FEEDS)
# ═══════════════════════════════════════════════════════════════════════════

INDIAN_MARKET_RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
    "et_markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "livemint": "https://www.livemint.com/rss/markets",
    "ndtv_profit": "https://feeds.feedburner.com/ndtvprofit-latest",
    "google_nifty": "https://news.google.com/rss/search?q=NIFTY+50+NSE+India&hl=en-IN&gl=IN&ceid=IN:en",
    "google_sensex": "https://news.google.com/rss/search?q=SENSEX+BSE+India&hl=en-IN&gl=IN&ceid=IN:en",
    "google_market": "https://news.google.com/rss/search?q=Indian+stock+market+today&hl=en-IN&gl=IN&ceid=IN:en",
}

# Sentiment word lists for Indian market context
BULLISH_WORDS = [
    'rally', 'surge', 'soar', 'gain', 'bull', 'bullish', 'up', 'rise', 'rising',
    'high', 'record', 'profit', 'positive', 'growth', 'boom', 'strong', 'recovery',
    'outperform', 'buy', 'breakout', 'support', 'green', 'advance', 'momentum',
    'upgrade', 'beat', 'exceeded', 'robust', 'optimistic', 'inflows', 'stimulus',
    'easing', 'rate cut', 'fii buying', 'dii buying', 'institutional buying',
    'nifty up', 'sensex up', 'market rally', 'stock surge', 'all-time high',
    'golden cross', 'bullish engulfing', 'morning star', 'hammer',
]

BEARISH_WORDS = [
    'fall', 'crash', 'plunge', 'drop', 'bear', 'bearish', 'down', 'decline',
    'low', 'loss', 'negative', 'recession', 'weak', 'sell', 'selloff', 'sell-off',
    'correction', 'resistance', 'red', 'retreat', 'downgrade', 'miss', 'feared',
    'pessimistic', 'outflows', 'tightening', 'rate hike', 'fii selling',
    'dii selling', 'institutional selling', 'nifty down', 'sensex down',
    'market crash', 'circuit breaker', 'death cross', 'bearish engulfing',
    'evening star', 'shooting star', 'panic', 'blood bath', 'capitulation',
    'inflation', 'war', 'crisis', 'default', 'bankruptcy',
]

NEUTRAL_WORDS = [
    'mixed', 'flat', 'range-bound', 'sideways', 'consolidation', 'unchanged',
    'stable', 'wait', 'hold', 'neutral', 'balanced',
]


def fetch_news_headlines(max_per_source: int = 10) -> List[Dict[str, str]]:
    """Fetch recent headlines from Indian market RSS feeds."""
    import requests

    all_headlines = []

    for source_name, feed_url in INDIAN_MARKET_RSS_FEEDS.items():
        try:
            resp = requests.get(feed_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MarketBot/1.0)',
            })
            if resp.status_code != 200:
                continue

            # Simple XML parsing (avoid lxml dependency)
            text = resp.text
            items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL)
            if not items:
                # Try <entry> for Atom feeds
                items = re.findall(r'<entry>(.*?)</entry>', text, re.DOTALL)

            for item in items[:max_per_source]:
                title = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL)
                if title:
                    title_text = title.group(1).strip()
                    # Clean CDATA
                    title_text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title_text)
                    title_text = re.sub(r'<[^>]+>', '', title_text).strip()

                    if title_text:
                        all_headlines.append({
                            "source": source_name,
                            "title": title_text,
                            "timestamp": datetime.now().isoformat(),
                        })

        except Exception as e:
            logger.debug(f"Failed to fetch {source_name}: {e}")

    return all_headlines


# ═══════════════════════════════════════════════════════════════════════════
#  SENTIMENT SCORING
# ═══════════════════════════════════════════════════════════════════════════

def _vader_score(text: str) -> Optional[float]:
    """VADER sentiment (if nltk available). Returns -1 to +1."""
    try:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        sid = SentimentIntensityAnalyzer()
        return sid.polarity_scores(text)["compound"]
    except Exception:
        return None


def _textblob_score(text: str) -> Optional[float]:
    """TextBlob sentiment (if available). Returns -1 to +1."""
    try:
        from textblob import TextBlob
        return TextBlob(text).sentiment.polarity
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  LLM-POWERED SENTIMENT (AI BRAIN)
# ═══════════════════════════════════════════════════════════════════════════

_llm_sentiment_cache: Dict[str, Tuple[float, float]] = {}  # headline -> (score, timestamp)
_LLM_CACHE_TTL = 3600  # 1 hour

def _llm_batch_sentiment(headlines: List[str]) -> Dict[str, float]:
    """Use LLM to score a batch of headlines at once. Much smarter than keywords.
    Returns dict of headline -> score (-1 to +1).
    """
    if not headlines:
        return {}
    
    # Check cache first
    now = time.time()
    uncached = []
    results = {}
    for h in headlines:
        if h in _llm_sentiment_cache:
            cached_score, cached_time = _llm_sentiment_cache[h]
            if now - cached_time < _LLM_CACHE_TTL:
                results[h] = cached_score
                continue
        uncached.append(h)
    
    if not uncached:
        return results
    
    # Batch up to 20 headlines per LLM call
    batch = uncached[:20]
    numbered = "\n".join(f"{i+1}. {h}" for i, h in enumerate(batch))
    
    prompt = f"""You are a financial market sentiment analyzer for the INDIAN stock market.
Score each headline from -1.0 (very bearish for markets) to +1.0 (very bullish).
Consider: negation, sarcasm, context, actual market impact (not just words).

Headlines:
{numbered}

Reply with ONLY a JSON array of numbers, one per headline. Example: [-0.8, 0.5, 0.0, 0.7]
No text, no explanation, just the JSON array."""

    scores_list = None
    
    # Try Groq first (fastest + free tier)
    try:
        import os
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1,
            )
            raw = resp.choices[0].message.content.strip()
            import json
            scores_list = json.loads(raw)
    except Exception as e:
        logger.debug(f"Groq sentiment failed: {e}")
    
    # Try Gemini next
    if scores_list is None:
        try:
            import os
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-2.5-flash-lite")
                resp = model.generate_content(prompt)
                raw = resp.text.strip()
                import json
                # Extract JSON array from response
                match = re.search(r'\[[\d\s,.\-]+\]', raw)
                if match:
                    scores_list = json.loads(match.group(0))
        except Exception as e:
            logger.debug(f"Gemini sentiment failed: {e}")
    
    if scores_list and len(scores_list) == len(batch):
        for h, s in zip(batch, scores_list):
            score = max(-1.0, min(1.0, float(s)))
            results[h] = score
            _llm_sentiment_cache[h] = (score, now)
    
    return results


def _llm_summarize_sentiment(bullish_headlines: List[str], bearish_headlines: List[str]) -> str:
    """Get LLM to summarize the overall market mood from top headlines."""
    combined = ""
    if bullish_headlines:
        combined += "Bullish:\n" + "\n".join(f"- {h}" for h in bullish_headlines[:5]) + "\n"
    if bearish_headlines:
        combined += "Bearish:\n" + "\n".join(f"- {h}" for h in bearish_headlines[:5]) + "\n"
    
    if not combined:
        return ""
    
    prompt = f"""Based on these Indian market headlines, give a 2-3 line market mood summary in Hindi-English mix (like a smart friend talking).
Focus on: What's driving the market? Should traders be careful or aggressive?

{combined}

Reply short, direct, no fluff."""

    try:
        import os
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
    except Exception:
        pass
    
    return ""


def score_headline_sentiment(headline: str) -> float:
    """Score a single headline using multi-model ensemble.
    Returns -1.0 (very bearish) to +1.0 (very bullish).
    """
    text = headline.lower()

    # Model 1: Keyword matching
    bullish_count = sum(1 for w in BULLISH_WORDS if w in text)
    bearish_count = sum(1 for w in BEARISH_WORDS if w in text)
    neutral_count = sum(1 for w in NEUTRAL_WORDS if w in text)

    total = bullish_count + bearish_count + neutral_count
    if total == 0:
        keyword_score = 0.0
    else:
        keyword_score = (bullish_count - bearish_count) / (total + 1)
    keyword_score = max(-1.0, min(1.0, keyword_score))

    # Model 2: VADER (if available)
    vader = _vader_score(headline)
    # Model 3: TextBlob (if available)
    blob = _textblob_score(headline)

    # Ensemble: weighted average of available models
    scores = [(keyword_score, 0.4)]
    if vader is not None:
        scores.append((vader, 0.35))
    if blob is not None:
        scores.append((blob, 0.25))

    total_weight = sum(w for _, w in scores)
    ensemble = sum(s * w for s, w in scores) / total_weight if total_weight > 0 else 0.0

    return max(-1.0, min(1.0, ensemble))


def analyze_news_sentiment(use_ai: bool = True) -> Dict[str, Any]:
    """Fetch and analyze sentiment from all Indian market news sources.
    
    Now uses LLM-powered sentiment as primary scorer with keyword fallback.
    """
    headlines = fetch_news_headlines()

    if not headlines:
        return {
            "sentiment": "NEUTRAL",
            "score": 0.0,
            "confidence": 0.0,
            "headline_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "headlines": [],
            "ai_summary": "",
            "error": "Could not fetch news headlines",
        }

    # Try LLM batch scoring first (smarter: understands context, negation, sarcasm)
    llm_scores = {}
    if use_ai:
        try:
            all_titles = [h["title"] for h in headlines]
            llm_scores = _llm_batch_sentiment(all_titles)
            if llm_scores:
                logger.info(f"[SENTIMENT] AI scored {len(llm_scores)}/{len(headlines)} headlines")
        except Exception as e:
            logger.debug(f"LLM sentiment batch failed: {e}")

    scores = []
    bullish_headlines = []
    bearish_headlines = []
    neutral_headlines = []

    for h in headlines:
        title = h["title"]
        # Use LLM score if available, else fall back to keyword ensemble
        if title in llm_scores:
            score = llm_scores[title]
            h["score_source"] = "ai"
        else:
            score = score_headline_sentiment(title)
            h["score_source"] = "keyword"
        
        h["sentiment_score"] = score
        scores.append(score)

        if score > 0.1:
            bullish_headlines.append(h)
        elif score < -0.1:
            bearish_headlines.append(h)
        else:
            neutral_headlines.append(h)

    avg_score = np.mean(scores) if scores else 0.0
    std_score = np.std(scores) if scores else 0.0

    # Weighted recent headlines more
    if len(scores) > 5:
        recent_avg = np.mean(scores[:10])  # Most recent
        avg_score = 0.6 * recent_avg + 0.4 * avg_score

    # AI-scored headlines get higher confidence
    ai_count = sum(1 for h in headlines if h.get("score_source") == "ai")
    ai_boost = 1.15 if ai_count > len(headlines) * 0.5 else 1.0
    confidence = min(abs(avg_score) * 2 * ai_boost, 1.0) * (1 - std_score)

    if avg_score > 0.15:
        sentiment = "BULLISH"
    elif avg_score > 0.05:
        sentiment = "MILDLY BULLISH"
    elif avg_score < -0.15:
        sentiment = "BEARISH"
    elif avg_score < -0.05:
        sentiment = "MILDLY BEARISH"
    else:
        sentiment = "NEUTRAL"

    # Get AI summary of market mood
    ai_summary = ""
    if use_ai:
        try:
            ai_summary = _llm_summarize_sentiment(
                [h["title"] for h in bullish_headlines[:5]],
                [h["title"] for h in bearish_headlines[:5]],
            )
        except Exception:
            pass

    return {
        "sentiment": sentiment,
        "score": float(avg_score),
        "confidence": float(max(confidence, 0)),
        "headline_count": len(headlines),
        "bullish_count": len(bullish_headlines),
        "bearish_count": len(bearish_headlines),
        "neutral_count": len(neutral_headlines),
        "top_bullish": [h["title"] for h in bullish_headlines[:3]],
        "top_bearish": [h["title"] for h in bearish_headlines[:3]],
        "source_breakdown": _source_breakdown(headlines),
        "ai_summary": ai_summary,
        "ai_scored_pct": round(ai_count / max(len(headlines), 1) * 100, 1),
    }


def _source_breakdown(headlines: List[Dict]) -> Dict[str, float]:
    """Average sentiment per source."""
    source_scores: Dict[str, List[float]] = {}
    for h in headlines:
        src = h["source"]
        source_scores.setdefault(src, []).append(h.get("sentiment_score", 0.0))
    return {src: float(np.mean(scores)) for src, scores in source_scores.items()}


# ═══════════════════════════════════════════════════════════════════════════
#  INDIA FEAR & GREED INDEX (Custom)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_fear_greed_index() -> Dict[str, Any]:
    """Calculate an India-specific Fear & Greed Index (0-100).
    
    Components:
    1. VIX India (fear gauge)
    2. Market momentum (NIFTY vs 125-day SMA)
    3. News sentiment
    4. Market breadth (advance/decline)
    5. Put-Call Ratio
    6. Safe haven demand (Gold vs NIFTY relative performance)
    """
    components = {}
    scores = []

    try:
        import yfinance as yf

        # 1. India VIX (inverted: high VIX = fear)
        try:
            vix_data = yf.download("^INDIAVIX", period="5d", progress=False)
            if vix_data is not None and not vix_data.empty:
                if isinstance(vix_data.columns, pd.MultiIndex):
                    vix_data.columns = vix_data.columns.get_level_values(0)
                vix_close_col = 'Close' if 'Close' in vix_data.columns else 'close'
                india_vix = float(vix_data[vix_close_col].iloc[-1])
                # VIX 10-15 = extreme greed (90-100), VIX 25+ = extreme fear (0-10)
                vix_score = max(0, min(100, 100 - (india_vix - 10) * (100 / 20)))
                components["india_vix"] = {"value": india_vix, "score": vix_score}
                scores.append(vix_score)
        except Exception:
            pass

        # 2. Market Momentum (NIFTY vs 125-day SMA)
        try:
            nifty = yf.download("^NSEI", period="200d", progress=False)
            if nifty is not None and not nifty.empty:
                if isinstance(nifty.columns, pd.MultiIndex):
                    nifty.columns = nifty.columns.get_level_values(0)
                close_col = 'Close' if 'Close' in nifty.columns else 'close'
                current = float(nifty[close_col].iloc[-1])
                sma125 = float(nifty[close_col].tail(125).mean())
                momentum_pct = ((current - sma125) / sma125) * 100
                # +5% above SMA = extreme greed (90), -5% = extreme fear (10)
                momentum_score = max(0, min(100, 50 + momentum_pct * 8))
                components["market_momentum"] = {"value": momentum_pct, "score": momentum_score}
                scores.append(momentum_score)
        except Exception:
            pass

        # 3. News Sentiment
        try:
            news = analyze_news_sentiment()
            news_score_raw = news.get("score", 0)
            # Map -1 to +1 → 0 to 100
            news_score = max(0, min(100, 50 + news_score_raw * 50))
            components["news_sentiment"] = {"value": news_score_raw, "score": news_score}
            scores.append(news_score)
        except Exception:
            pass

        # 4. Safe Haven (Gold relative performance)
        try:
            gold = yf.download("GC=F", period="30d", progress=False)
            if gold is not None and not gold.empty and nifty is not None:
                if isinstance(gold.columns, pd.MultiIndex):
                    gold.columns = gold.columns.get_level_values(0)
                gold_close = 'Close' if 'Close' in gold.columns else 'close'
                gold_ret = float(gold[gold_close].pct_change(5).iloc[-1]) * 100
                nifty_ret = float(nifty[close_col].pct_change(5).iloc[-1]) * 100
                # If gold outperforms nifty = fear
                diff = nifty_ret - gold_ret
                haven_score = max(0, min(100, 50 + diff * 10))
                components["safe_haven"] = {"gold_5d": gold_ret, "nifty_5d": nifty_ret, "score": haven_score}
                scores.append(haven_score)
        except Exception:
            pass

    except ImportError:
        pass

    # Calculate composite
    if scores:
        composite = np.mean(scores)
    else:
        composite = 50  # neutral

    if composite >= 80:
        label = "EXTREME GREED 🤑"
    elif composite >= 60:
        label = "GREED 😊"
    elif composite >= 40:
        label = "NEUTRAL 😐"
    elif composite >= 20:
        label = "FEAR 😰"
    else:
        label = "EXTREME FEAR 😱"

    return {
        "index": float(composite),
        "label": label,
        "components": components,
        "component_count": len(scores),
    }


# Need pandas for VIX data
import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════
#  FII / DII FLOW ANALYSIS (Institutional Flows)
# ═══════════════════════════════════════════════════════════════════════════

def fetch_fii_dii_sentiment() -> Dict[str, Any]:
    """Estimate FII/DII sentiment from market data patterns.
    Uses NIFTY volume & price divergence as proxy for institutional flows.
    """
    try:
        import yfinance as yf
        nifty = yf.download("^NSEI", period="30d", progress=False)
        if nifty is None or nifty.empty:
            return {"fii_sentiment": "NEUTRAL", "dii_sentiment": "NEUTRAL", "score": 50}

        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        close = nifty['Close'] if 'Close' in nifty.columns else nifty['close']
        volume = nifty['Volume'] if 'Volume' in nifty.columns else nifty.get('volume', pd.Series([0]))

        # Price-Volume Divergence as institutional flow proxy
        price_change_5d = float(close.pct_change(5).iloc[-1]) * 100
        vol_change_5d = float(volume.pct_change(5).iloc[-1]) * 100 if volume.sum() > 0 else 0

        # Rising price + Rising volume = Strong institutional buying
        # Falling price + Rising volume = Institutional selling (distribution)
        # Rising price + Falling volume = Weak rally (no institutional support)
        if price_change_5d > 0.5 and vol_change_5d > 10:
            fii_sentiment = "STRONG BUYING"
            score = 80
        elif price_change_5d > 0.5 and vol_change_5d < -10:
            fii_sentiment = "WEAK BUYING"
            score = 60
        elif price_change_5d < -0.5 and vol_change_5d > 10:
            fii_sentiment = "DISTRIBUTION"
            score = 25
        elif price_change_5d < -0.5:
            fii_sentiment = "SELLING"
            score = 20
        else:
            fii_sentiment = "NEUTRAL"
            score = 50

        # Bank Nifty as DII proxy (banks = major DII holdings)
        try:
            banknifty = yf.download("^NSEBANK", period="10d", progress=False)
            if banknifty is not None and not banknifty.empty:
                if isinstance(banknifty.columns, pd.MultiIndex):
                    banknifty.columns = banknifty.columns.get_level_values(0)
                bn_close = banknifty['Close'] if 'Close' in banknifty.columns else banknifty['close']
                bn_change = float(bn_close.pct_change(5).iloc[-1]) * 100
                if bn_change > price_change_5d + 0.5:
                    dii_sentiment = "STRONG BUYING"
                elif bn_change > 0:
                    dii_sentiment = "BUYING"
                else:
                    dii_sentiment = "SELLING"
            else:
                dii_sentiment = "N/A"
        except Exception:
            dii_sentiment = "N/A"

        return {
            "fii_sentiment": fii_sentiment,
            "dii_sentiment": dii_sentiment,
            "price_change_5d": round(price_change_5d, 2),
            "vol_change_5d": round(vol_change_5d, 2),
            "score": score,
        }
    except Exception as e:
        logger.error(f"FII/DII analysis error: {e}")
        return {"fii_sentiment": "N/A", "dii_sentiment": "N/A", "score": 50}


# ═══════════════════════════════════════════════════════════════════════════
#  SOCIAL MEDIA SENTIMENT (Reddit/Twitter proxy via Google)
# ═══════════════════════════════════════════════════════════════════════════

SOCIAL_RSS_FEEDS = {
    "reddit_india": "https://news.google.com/rss/search?q=site:reddit.com+indian+stock+market&hl=en-IN&gl=IN",
    "twitter_india": "https://news.google.com/rss/search?q=NIFTY+stock+market+india+twitter&hl=en-IN&gl=IN",
    "youtube_market": "https://news.google.com/rss/search?q=NIFTY+analysis+today+youtube&hl=en-IN&gl=IN",
}

def analyze_social_sentiment() -> Dict[str, Any]:
    """Analyze social media sentiment from Google indexed posts."""
    import requests

    all_posts = []
    for source, url in SOCIAL_RSS_FEEDS.items():
        try:
            resp = requests.get(url, timeout=8, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MarketBot/1.0)'
            })
            if resp.status_code == 200:
                items = re.findall(r'<title[^>]*>(.*?)</title>', resp.text, re.DOTALL)
                for item in items[:8]:
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', item).strip()
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    if title and len(title) > 10:
                        score = score_headline_sentiment(title)
                        all_posts.append({"source": source, "title": title, "score": score})
        except Exception:
            pass

    if not all_posts:
        return {"sentiment": "NEUTRAL", "score": 0, "post_count": 0}

    avg_score = np.mean([p["score"] for p in all_posts])
    if avg_score > 0.15:
        sentiment = "BULLISH"
    elif avg_score > 0.05:
        sentiment = "MILDLY BULLISH"
    elif avg_score < -0.15:
        sentiment = "BEARISH"
    elif avg_score < -0.05:
        sentiment = "MILDLY BEARISH"
    else:
        sentiment = "NEUTRAL"

    return {
        "sentiment": sentiment,
        "score": float(avg_score),
        "post_count": len(all_posts),
        "top_posts": [p["title"] for p in sorted(all_posts, key=lambda x: abs(x["score"]), reverse=True)[:3]],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  FORMAT FOR TELEGRAM
# ═══════════════════════════════════════════════════════════════════════════

def format_sentiment_message() -> str:
    """Format comprehensive sentiment analysis as a Telegram message."""
    news = analyze_news_sentiment()
    fg = calculate_fear_greed_index()
    fii = fetch_fii_dii_sentiment()
    social = analyze_social_sentiment()

    lines = [
        "📰 *INDIAN MARKET SENTIMENT ANALYSIS* 📰",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Fear & Greed
    fg_val = fg["index"]
    fg_bar_filled = int(fg_val / 10)
    fg_bar = "█" * fg_bar_filled + "░" * (10 - fg_bar_filled)
    lines.extend([
        f"🎭 *India Fear & Greed Index:*",
        f"  [{fg_bar}] {fg_val:.0f}/100",
        f"  Status: *{fg['label']}*",
        "",
    ])

    if fg.get("components"):
        for name, comp in fg["components"].items():
            score = comp.get("score", 50)
            emoji = "🟢" if score > 60 else "🔴" if score < 40 else "🟡"
            lines.append(f"  {emoji} {name}: {score:.0f}/100")
        lines.append("")

    # News Sentiment
    sentiment_emoji = {"BULLISH": "🟢🚀", "MILDLY BULLISH": "🟢",
                       "BEARISH": "🔴📉", "MILDLY BEARISH": "🔴", "NEUTRAL": "🟡"}
    s_emoji = sentiment_emoji.get(news["sentiment"], "🟡")

    lines.extend([
        f"📊 *News Sentiment:* {s_emoji} *{news['sentiment']}*",
        f"  Score: {news['score']:+.2f} | Confidence: {news['confidence']:.0%}",
        f"  Headlines analyzed: {news['headline_count']}",
        f"  🟢 Bullish: {news['bullish_count']} | 🔴 Bearish: {news['bearish_count']} | ⚪ Neutral: {news['neutral_count']}",
        "",
    ])

    if news.get("top_bullish"):
        lines.append("📈 *Top Bullish Headlines:*")
        for h in news["top_bullish"][:2]:
            lines.append(f"  • {h[:80]}")
        lines.append("")

    if news.get("top_bearish"):
        lines.append("📉 *Top Bearish Headlines:*")
        for h in news["top_bearish"][:2]:
            lines.append(f"  • {h[:80]}")
        lines.append("")

    # Source breakdown
    if news.get("source_breakdown"):
        lines.append("📰 *Source Sentiments:*")
        for src, score in news["source_breakdown"].items():
            emoji = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "⚪"
            lines.append(f"  {emoji} {src}: {score:+.2f}")

    # FII/DII Institutional Flows
    lines.extend(["", "🏦 *INSTITUTIONAL FLOWS (FII/DII):*"])
    fii_emoji = {"STRONG BUYING": "🟢🟢", "WEAK BUYING": "🟢", "BUYING": "🟢",
                 "DISTRIBUTION": "🔴⚡", "SELLING": "🔴🔴", "NEUTRAL": "⚪"}
    lines.append(f"  FII: {fii_emoji.get(fii.get('fii_sentiment','N/A'), '⚪')} *{fii.get('fii_sentiment', 'N/A')}*")
    lines.append(f"  DII: {fii_emoji.get(fii.get('dii_sentiment','N/A'), '⚪')} *{fii.get('dii_sentiment', 'N/A')}*")
    if 'price_change_5d' in fii:
        lines.append(f"  📊 NIFTY 5D: {fii['price_change_5d']:+.1f}% | Vol 5D: {fii['vol_change_5d']:+.1f}%")

    # Social Media Sentiment
    if social.get("post_count", 0) > 0:
        s_em = {"BULLISH": "🟢🚀", "MILDLY BULLISH": "🟢", "BEARISH": "🔴📉",
                "MILDLY BEARISH": "🔴", "NEUTRAL": "🟡"}
        lines.extend(["", "🐦 *SOCIAL MEDIA SENTIMENT:*"])
        lines.append(f"  {s_em.get(social['sentiment'], '🟡')} *{social['sentiment']}* ({social['post_count']} posts)")
        if social.get("top_posts"):
            for p in social["top_posts"][:2]:
                lines.append(f"  • {p[:70]}")

    # Combined Verdict
    # Weighted composite of all signals
    all_scores = [fg_val, max(0, min(100, 50 + news.get("score", 0) * 50)),
                  fii.get("score", 50),
                  max(0, min(100, 50 + social.get("score", 0) * 50))]
    composite = np.mean(all_scores)

    if composite >= 70:
        verdict = "🟢🚀 *OVERALL: STRONG BULLISH*"
    elif composite >= 55:
        verdict = "🟢 *OVERALL: BULLISH*"
    elif composite >= 45:
        verdict = "🟡 *OVERALL: NEUTRAL*"
    elif composite >= 30:
        verdict = "🔴 *OVERALL: BEARISH*"
    else:
        verdict = "🔴📉 *OVERALL: STRONG BEARISH*"

    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", verdict])

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ _Sentiment analysis. Not financial advice._",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_sentiment_message())
