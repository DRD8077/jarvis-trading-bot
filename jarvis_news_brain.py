"""
📰⚡ JARVIS NEWS BRAIN — Real-Time News + Sentiment Intelligence
═══════════════════════════════════════════════════════════════════
Auto-scrape financial news → AI Sentiment Analysis → Impact on Positions

"Koi important news hai?" → Latest market-moving news with sentiment
"RELIANCE ki koi news?" → Stock-specific news with impact analysis

Features:
  • Real-time RSS feed scraping (MoneyControl, ET, Reuters, LiveMint)
  • AI-powered sentiment analysis (Bullish/Bearish/Neutral)
  • Stock-specific news filtering
  • Market impact score (1-10)
  • Position impact alerts (news that affects your holdings)
  • Hindi + English support
  • Category tagging (Earnings, Policy, Global, Sector, Merger)
  • Breaking news priority system
  • News summary with AI

Author: JARVIS AI (Boss: Deepak Kumar)
"""

import os
import re
import time
import logging
import hashlib
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger("jarvis_news_brain")

# ═══════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

NEWS_BRAIN_AVAILABLE = FEEDPARSER_AVAILABLE or WEB_AVAILABLE

if NEWS_BRAIN_AVAILABLE:
    logger.info("[NEWS-BRAIN] 📰 News Brain loaded — Real-time Financial News ACTIVE")

# ═══════════════════════════════════════════════════════════
#  RSS FEEDS
# ═══════════════════════════════════════════════════════════
RSS_FEEDS = {
    "MoneyControl": {
        "market": "https://www.moneycontrol.com/rss/marketreports.xml",
        "news": "https://www.moneycontrol.com/rss/latestnews.xml",
        "stocks": "https://www.moneycontrol.com/rss/stocksnews.xml",
    },
    "Economic Times": {
        "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "mf": "https://economictimes.indiatimes.com/mf/rssfeeds/4521498.cms",
    },
    "LiveMint": {
        "market": "https://www.livemint.com/rss/markets",
    },
    "Business Standard": {
        "markets": "https://www.business-standard.com/rss/markets-106.rss",
    },
    "Reuters India": {
        "business": "https://feeds.reuters.com/reuters/INbusinessNews",
    },
}

# ═══════════════════════════════════════════════════════════
#  SENTIMENT KEYWORDS
# ═══════════════════════════════════════════════════════════
BULLISH_WORDS = [
    'surge', 'rally', 'gain', 'rise', 'jump', 'soar', 'climb', 'boom',
    'breakout', 'bullish', 'upgrade', 'outperform', 'buy', 'accumulate',
    'profit', 'dividend', 'growth', 'beat', 'record', 'high', 'positive',
    'recovery', 'strong', 'expansion', 'up', 'higher', 'optimistic',
    'tezzi', 'badhna', 'munafa', 'achha', 'upar',
]

BEARISH_WORDS = [
    'fall', 'drop', 'crash', 'plunge', 'decline', 'sink', 'tumble',
    'bearish', 'downgrade', 'underperform', 'sell', 'loss', 'miss',
    'weak', 'warning', 'cut', 'lower', 'negative', 'recession',
    'correction', 'panic', 'fear', 'crisis', 'default', 'fraud',
    'girna', 'nuksaan', 'bura', 'neeche', 'mandhi',
]

NEWS_CATEGORIES = {
    'earnings': ['earnings', 'result', 'profit', 'revenue', 'quarter', 'annual', 'eps'],
    'policy': ['rbi', 'rate', 'policy', 'inflation', 'gdp', 'budget', 'tax', 'sebi', 'regulation'],
    'global': ['us', 'fed', 'china', 'global', 'world', 'trade war', 'tariff', 'crude', 'dollar'],
    'sector': ['pharma', 'it', 'bank', 'auto', 'metal', 'energy', 'fmcg', 'real estate', 'infra'],
    'merger': ['merger', 'acquisition', 'buyout', 'takeover', 'stake', 'deal'],
    'ipo': ['ipo', 'listing', 'public offer', 'debut'],
    'crypto': ['bitcoin', 'crypto', 'blockchain', 'ethereum', 'defi', 'web3'],
}

# Cache
_news_cache: Dict[str, Tuple[float, List[Dict]]] = {}
NEWS_CACHE_TTL = 180  # 3 minutes


# ═══════════════════════════════════════════════════════════
#  SENTIMENT ANALYZER
# ═══════════════════════════════════════════════════════════
def _analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze text sentiment.
    Returns: (BULLISH/BEARISH/NEUTRAL, confidence 0-1)
    """
    text_lower = text.lower()
    
    bull_score = sum(1 for w in BULLISH_WORDS if w in text_lower)
    bear_score = sum(1 for w in BEARISH_WORDS if w in text_lower)
    
    # TextBlob for additional analysis
    if TEXTBLOB_AVAILABLE:
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to +1
            if polarity > 0.1:
                bull_score += 2
            elif polarity < -0.1:
                bear_score += 2
        except Exception:
            pass
    
    total = bull_score + bear_score
    if total == 0:
        return "NEUTRAL", 0.5
    
    if bull_score > bear_score:
        confidence = bull_score / total
        return "BULLISH", min(confidence, 0.95)
    elif bear_score > bull_score:
        confidence = bear_score / total
        return "BEARISH", min(confidence, 0.95)
    else:
        return "NEUTRAL", 0.5


def _categorize_news(text: str) -> List[str]:
    """Categorize news article"""
    text_lower = text.lower()
    categories = []
    for cat, keywords in NEWS_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(cat)
    return categories if categories else ["general"]


def _calc_impact_score(sentiment: str, confidence: float, title: str) -> int:
    """Calculate market impact score 1-10"""
    score = 5  # base
    
    if confidence > 0.8:
        score += 2
    elif confidence > 0.6:
        score += 1
    
    # Breaking/urgent keywords
    urgency_words = ['breaking', 'urgent', 'crash', 'surge', 'record', 'crisis', 'shock', 'ban', 'scam']
    if any(w in title.lower() for w in urgency_words):
        score += 2
    
    # Big company names
    big_names = ['reliance', 'tata', 'hdfc', 'infosys', 'nifty', 'sensex', 'rbi', 'sebi']
    if any(n in title.lower() for n in big_names):
        score += 1
    
    return max(1, min(10, score))


# ═══════════════════════════════════════════════════════════
#  NEWS FETCHER
# ═══════════════════════════════════════════════════════════
def _fetch_rss_feed(url: str) -> List[Dict]:
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:20]:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()
            link = entry.get('link', '')
            published = entry.get('published', entry.get('updated', ''))
            
            # Parse date
            pub_date = None
            if published:
                try:
                    pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') and entry.published_parsed else None
                except Exception:
                    pass
            
            # Clean HTML from summary
            if summary:
                summary = re.sub(r'<[^>]+>', '', summary)[:300]
            
            if title:
                articles.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": pub_date,
                    "published_str": published,
                })
        return articles
    except Exception as e:
        logger.debug(f"[NEWS-BRAIN] RSS fetch error: {e}")
        return []


def _fetch_all_news() -> List[Dict]:
    """Fetch news from all RSS feeds"""
    cache_key = "all_news"
    now = time.time()
    
    if cache_key in _news_cache:
        ts, cached = _news_cache[cache_key]
        if now - ts < NEWS_CACHE_TTL:
            return cached
    
    all_articles = []
    seen_titles = set()
    
    for source_name, feeds in RSS_FEEDS.items():
        for feed_type, url in feeds.items():
            try:
                articles = _fetch_rss_feed(url)
                for a in articles:
                    # Deduplicate
                    title_hash = hashlib.md5(a['title'].lower().encode()).hexdigest()
                    if title_hash in seen_titles:
                        continue
                    seen_titles.add(title_hash)
                    
                    # Analyze
                    full_text = f"{a['title']} {a['summary']}"
                    sentiment, confidence = _analyze_sentiment(full_text)
                    categories = _categorize_news(full_text)
                    impact = _calc_impact_score(sentiment, confidence, a['title'])
                    
                    a.update({
                        "source": source_name,
                        "feed_type": feed_type,
                        "sentiment": sentiment,
                        "sentiment_confidence": confidence,
                        "categories": categories,
                        "impact_score": impact,
                    })
                    all_articles.append(a)
            except Exception as e:
                logger.debug(f"[NEWS-BRAIN] Error fetching {source_name}/{feed_type}: {e}")
    
    # Sort by impact score
    all_articles.sort(key=lambda x: (-x['impact_score'], x.get('published') or datetime.min), reverse=False)
    all_articles.sort(key=lambda x: -x['impact_score'])
    
    _news_cache[cache_key] = (now, all_articles)
    logger.info(f"[NEWS-BRAIN] Fetched {len(all_articles)} news articles")
    
    return all_articles


# ═══════════════════════════════════════════════════════════
#  STOCK-SPECIFIC NEWS
# ═══════════════════════════════════════════════════════════
def _search_stock_news(stock: str) -> List[Dict]:
    """Search for stock-specific news"""
    all_news = _fetch_all_news()
    stock_upper = stock.upper()
    stock_lower = stock.lower()
    
    # Also search company names
    company_names = {
        "RELIANCE": ["reliance", "mukesh ambani", "jio"],
        "TCS": ["tcs", "tata consultancy"],
        "INFY": ["infosys", "infy", "salil parekh"],
        "HDFCBANK": ["hdfc bank", "hdfc"],
        "ICICIBANK": ["icici bank", "icici"],
        "SBIN": ["sbi", "state bank"],
        "TATAMOTORS": ["tata motors", "tata motor"],
        "ITC": ["itc"],
        "WIPRO": ["wipro"],
        "BAJFINANCE": ["bajaj finance", "bajaj fin"],
        "ADANIENT": ["adani", "adani enterprises", "gautam adani"],
        "MARUTI": ["maruti", "maruti suzuki"],
        "LT": ["larsen", "l&t"],
        "SUNPHARMA": ["sun pharma", "sun pharmaceutical"],
        "TITAN": ["titan"],
        "BHARTIARTL": ["bharti airtel", "airtel"],
    }
    
    search_terms = [stock_lower]
    if stock_upper in company_names:
        search_terms.extend(company_names[stock_upper])
    
    results = []
    for article in all_news:
        text = f"{article['title']} {article.get('summary', '')}".lower()
        if any(term in text for term in search_terms):
            results.append(article)
    
    return results[:10]


# ═══════════════════════════════════════════════════════════
#  GOOGLE NEWS SCRAPER (Backup)
# ═══════════════════════════════════════════════════════════
def _fetch_google_news(query: str) -> List[Dict]:
    """Fallback: scrape Google News RSS"""
    if not FEEDPARSER_AVAILABLE:
        return []
    
    try:
        url = f"https://news.google.com/rss/search?q={query}+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
        articles = _fetch_rss_feed(url)
        
        for a in articles:
            full_text = f"{a['title']} {a.get('summary', '')}"
            sentiment, confidence = _analyze_sentiment(full_text)
            categories = _categorize_news(full_text)
            impact = _calc_impact_score(sentiment, confidence, a['title'])
            
            a.update({
                "source": "Google News",
                "feed_type": "search",
                "sentiment": sentiment,
                "sentiment_confidence": confidence,
                "categories": categories,
                "impact_score": impact,
            })
        
        return articles[:10]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════
#  FORMATTERS
# ═══════════════════════════════════════════════════════════
def _sentiment_emoji(sentiment: str) -> str:
    return {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "⚪"}.get(sentiment, "⚪")


def _impact_bar(score: int) -> str:
    filled = "🔥" * min(score, 10)
    empty = "░" * (10 - min(score, 10))
    return filled + empty


def format_news(articles: List[Dict], title: str = "Latest Market News", max_items: int = 10) -> str:
    """Format news articles for Telegram"""
    if not articles:
        return f"📰 *{title}*\n\n❌ Koi news available nahi hai abhi."
    
    output = (
        f"📰 *{title}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i, article in enumerate(articles[:max_items], 1):
        sentiment_e = _sentiment_emoji(article.get("sentiment", "NEUTRAL"))
        impact = article.get("impact_score", 5)
        cats = ", ".join(article.get("categories", ["general"]))
        source = article.get("source", "Unknown")
        
        output += (
            f"*{i}. {article['title'][:100]}*\n"
            f"   {sentiment_e} {article.get('sentiment', 'NEUTRAL')} | "
            f"Impact: {'🔥' * min(impact, 5)} ({impact}/10) | "
            f"📂 {cats}\n"
            f"   📡 _{source}_\n\n"
        )
    
    # Summary
    bull_count = sum(1 for a in articles[:max_items] if a.get('sentiment') == 'BULLISH')
    bear_count = sum(1 for a in articles[:max_items] if a.get('sentiment') == 'BEARISH')
    
    overall = "🟢 BULLISH BIAS" if bull_count > bear_count else "🔴 BEARISH BIAS" if bear_count > bull_count else "⚪ MIXED"
    
    output += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Overall Sentiment:* {overall}\n"
        f"   🟢 Bullish: {bull_count} | 🔴 Bearish: {bear_count} | ⚪ Neutral: {max_items - bull_count - bear_count}\n"
        f"⏰ _{datetime.now().strftime('%H:%M:%S IST')}_"
    )
    
    return output


def format_stock_news(stock: str) -> str:
    """Get and format stock-specific news"""
    # Try RSS first
    articles = _search_stock_news(stock)
    
    # Fallback to Google News
    if not articles:
        articles = _fetch_google_news(stock)
    
    return format_news(articles, f"{stock.upper()} News", 8)


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
def get_latest_news(max_items: int = 10) -> str:
    """Get latest market news with sentiment"""
    articles = _fetch_all_news()
    return format_news(articles, "Latest Market News", max_items)


def get_stock_news(stock: str) -> str:
    """Get stock-specific news"""
    return format_stock_news(stock)


def get_breaking_news() -> str:
    """Get only high-impact news (score >= 7)"""
    articles = _fetch_all_news()
    breaking = [a for a in articles if a.get("impact_score", 0) >= 7]
    return format_news(breaking, "🚨 BREAKING / HIGH IMPACT NEWS", 5)


def get_sector_news(sector: str) -> str:
    """Get sector-specific news"""
    articles = _fetch_all_news()
    sector_lower = sector.lower()
    filtered = [a for a in articles if sector_lower in " ".join(a.get("categories", []))]
    return format_news(filtered, f"{sector.upper()} Sector News", 8)


def get_news_sentiment_score() -> Dict[str, Any]:
    """Get overall market sentiment from news"""
    articles = _fetch_all_news()
    if not articles:
        return {"sentiment": "NEUTRAL", "score": 50, "confidence": 0.3}
    
    bull = sum(1 for a in articles if a.get("sentiment") == "BULLISH")
    bear = sum(1 for a in articles if a.get("sentiment") == "BEARISH")
    total = len(articles)
    
    score = int((bull / total) * 100) if total > 0 else 50
    
    if bull > bear * 1.5:
        return {"sentiment": "BULLISH", "score": score, "confidence": bull/total}
    elif bear > bull * 1.5:
        return {"sentiment": "BEARISH", "score": 100-score, "confidence": bear/total}
    else:
        return {"sentiment": "NEUTRAL", "score": 50, "confidence": 0.5}


def parse_news_request(text: str) -> Dict[str, Any]:
    """Parse natural language news request"""
    text_lower = text.lower()
    
    # Check for stock-specific
    import re
    # Look for stock names
    stocks = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
        "TATAMOTORS", "ITC", "WIPRO", "BAJFINANCE", "ADANIENT", "MARUTI",
        "LT", "SUNPHARMA", "TITAN", "BHARTIARTL", "NIFTY", "SENSEX",
        "BANKNIFTY", "ZOMATO", "PAYTM", "HAL", "IRCTC",
    ]
    
    for stock in stocks:
        if stock.lower() in text_lower:
            return {"type": "stock", "stock": stock}
    
    # Breaking news
    if any(w in text_lower for w in ['breaking', 'urgent', 'important', 'zaroori', 'badi']):
        return {"type": "breaking"}
    
    # Sector
    sectors = ['pharma', 'banking', 'it', 'auto', 'metal', 'energy', 'fmcg', 'infra']
    for s in sectors:
        if s in text_lower:
            return {"type": "sector", "sector": s}
    
    return {"type": "latest"}


def handle_news_command(text: str) -> str:
    """Main entry point for news commands"""
    if not NEWS_BRAIN_AVAILABLE:
        return "❌ News Brain unavailable — install feedparser"
    
    parsed = parse_news_request(text)
    
    if parsed["type"] == "stock":
        return get_stock_news(parsed["stock"])
    elif parsed["type"] == "breaking":
        return get_breaking_news()
    elif parsed["type"] == "sector":
        return get_sector_news(parsed["sector"])
    else:
        return get_latest_news()


if __name__ == "__main__":
    print(get_latest_news(5))
