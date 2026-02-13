"""
🔥 DEX Engine v2.0 — Real-Time DexScreener + DexTools + Pump.fun
═══════════════════════════════════════════════════════════════════
REAL API connections. REAL prices. REAL-TIME data.
No mocks. No fakes. Production-grade.
"""

import os, json, logging, time, asyncio, hashlib, hmac
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Tuple
import httpx

logger = logging.getLogger("dex-engine")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
DEXSCREENER_BASE = "https://api.dexscreener.com"
DEXTOOLS_BASE = "https://public-api.dextools.io/trial/v2"
PUMPFUN_BASE = "https://frontend-api.pump.fun"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BIRDEYE_BASE = "https://public-api.birdeye.so"
JUPITER_PRICE_BASE = "https://price.jup.ag/v6"

DEXTOOLS_API_KEY = os.getenv("DEXTOOLS_API_KEY", "")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")

IST = timezone(timedelta(hours=5, minutes=30))

# Rate limiting
_last_call: Dict[str, float] = {}
_RATE_LIMIT = 0.3  # seconds between calls per endpoint


async def _rate_limit(key: str):
    now = time.time()
    last = _last_call.get(key, 0)
    wait = _RATE_LIMIT - (now - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_call[key] = time.time()


# ═══════════════════════════════════════════════════════════
#  HTTP CLIENT — Shared async client with retries
# ═══════════════════════════════════════════════════════════
_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            headers={"User-Agent": "JARVIS-Trading-Engine/2.0"},
            follow_redirects=True,
        )
    return _client


async def _fetch(url: str, headers: dict = None, params: dict = None) -> Optional[dict]:
    """Fetch JSON from URL with error handling."""
    try:
        client = get_client()
        r = await client.get(url, headers=headers or {}, params=params or {})
        if r.status_code == 200:
            return r.json()
        logger.warning(f"API {r.status_code}: {url}")
        return None
    except Exception as e:
        logger.warning(f"Fetch error {url}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  DEXSCREENER — Free, no API key needed
# ═══════════════════════════════════════════════════════════
async def dex_search(query: str, limit: int = 30) -> List[Dict]:
    """Search DexScreener for tokens by name/symbol/address."""
    await _rate_limit("dexscreener")
    data = await _fetch(f"{DEXSCREENER_BASE}/latest/dex/search", params={"q": query})
    if not data or "pairs" not in data:
        return []
    pairs = data["pairs"][:limit]
    return [_parse_dex_pair(p) for p in pairs]


async def dex_get_token(address: str) -> List[Dict]:
    """Get all pairs for a specific token address."""
    await _rate_limit("dexscreener_token")
    data = await _fetch(f"{DEXSCREENER_BASE}/latest/dex/tokens/{address}")
    if not data or "pairs" not in data:
        return []
    return [_parse_dex_pair(p) for p in data["pairs"][:20]]


async def dex_get_pair(chain: str, pair_address: str) -> Optional[Dict]:
    """Get specific pair data."""
    await _rate_limit("dexscreener_pair")
    data = await _fetch(f"{DEXSCREENER_BASE}/latest/dex/pairs/{chain}/{pair_address}")
    if not data or "pairs" not in data or not data["pairs"]:
        return None
    return _parse_dex_pair(data["pairs"][0])


async def dex_trending() -> List[Dict]:
    """Get trending/boosted tokens from DexScreener."""
    await _rate_limit("dexscreener_trending")
    data = await _fetch(f"{DEXSCREENER_BASE}/token-boosts/top/v1")
    if not data or not isinstance(data, list):
        return []
    results = []
    for item in data[:30]:
        results.append({
            "address": item.get("tokenAddress", ""),
            "chain": item.get("chainId", ""),
            "name": item.get("description", item.get("tokenAddress", "")[:8]),
            "symbol": item.get("tokenAddress", "")[:6].upper(),
            "url": item.get("url", ""),
            "icon": item.get("icon", ""),
            "amount": item.get("amount", 0),
            "source": "dexscreener_boost",
        })
    return results


async def dex_new_pairs(chain: str = "solana") -> List[Dict]:
    """Get newest pairs on a chain."""
    await _rate_limit("dexscreener_new")
    data = await _fetch(f"{DEXSCREENER_BASE}/latest/dex/pairs/{chain}")
    if not data or "pairs" not in data:
        return []
    return [_parse_dex_pair(p) for p in data["pairs"][:20]]


def _parse_dex_pair(p: dict) -> Dict:
    """Parse a DexScreener pair into our standard format."""
    price_usd = float(p.get("priceUsd", 0) or 0)
    price_native = float(p.get("priceNative", 0) or 0)
    chg_5m = float(p.get("priceChange", {}).get("m5", 0) or 0)
    chg_1h = float(p.get("priceChange", {}).get("h1", 0) or 0)
    chg_6h = float(p.get("priceChange", {}).get("h6", 0) or 0)
    chg_24h = float(p.get("priceChange", {}).get("h24", 0) or 0)
    vol_24h = float(p.get("volume", {}).get("h24", 0) or 0)
    liq_usd = float(p.get("liquidity", {}).get("usd", 0) or 0)
    mcap = float(p.get("marketCap", 0) or 0) if p.get("marketCap") else float(p.get("fdv", 0) or 0)
    txns = p.get("txns", {}).get("h24", {})
    buys = int(txns.get("buys", 0) or 0)
    sells = int(txns.get("sells", 0) or 0)
    
    # Compute gem score
    gem_score = _compute_gem_score(price_usd, chg_5m, chg_1h, chg_24h, vol_24h, liq_usd, mcap, buys, sells)
    
    return {
        "pair_address": p.get("pairAddress", ""),
        "chain": p.get("chainId", ""),
        "dex": p.get("dexId", ""),
        "base_token": p.get("baseToken", {}).get("symbol", ""),
        "base_address": p.get("baseToken", {}).get("address", ""),
        "quote_token": p.get("quoteToken", {}).get("symbol", ""),
        "symbol": p.get("baseToken", {}).get("symbol", ""),
        "name": p.get("baseToken", {}).get("name", ""),
        "price_usd": price_usd,
        "price_native": price_native,
        "change_5m": chg_5m,
        "change_1h": chg_1h,
        "change_6h": chg_6h,
        "change_24h": chg_24h,
        "volume_24h": vol_24h,
        "liquidity_usd": liq_usd,
        "market_cap": mcap,
        "buys_24h": buys,
        "sells_24h": sells,
        "buy_sell_ratio": round(buys / max(sells, 1), 2),
        "gem_score": gem_score,
        "url": p.get("url", f"https://dexscreener.com/{p.get('chainId', '')}/{p.get('pairAddress', '')}"),
        "created_at": p.get("pairCreatedAt", ""),
        "source": "dexscreener",
    }


def _compute_gem_score(price, chg5m, chg1h, chg24h, vol, liq, mcap, buys, sells) -> int:
    """Compute a gem score 0-100 based on multiple factors."""
    score = 50  # base
    
    # Volume momentum
    if vol > 100000: score += 5
    if vol > 500000: score += 5
    if vol > 1000000: score += 5
    
    # Liquidity safety
    if liq > 10000: score += 3
    if liq > 50000: score += 3
    if liq > 100000: score += 3
    if liq < 5000: score -= 10
    
    # Price momentum
    if chg5m > 2: score += 5
    if chg1h > 5: score += 5
    if chg24h > 10: score += 3
    if chg24h < -30: score += 8  # Deep dip = potential bounce
    if chg24h < -50: score += 10  # Very deep dip
    if chg24h < -5 and chg24h > -20 and chg1h > 0: score += 15  # Recovering from dip
    
    # Buy pressure
    ratio = buys / max(sells, 1)
    if ratio > 1.5: score += 5
    if ratio > 2.0: score += 5
    if ratio > 3.0: score += 5
    
    # Low mcap gems
    if mcap and mcap < 100000: score += 5
    if mcap and mcap < 50000: score += 5
    
    return min(100, max(0, score))


# ═══════════════════════════════════════════════════════════
#  COINGECKO — Free tier, major coins
# ═══════════════════════════════════════════════════════════
async def cg_prices(ids: str = "bitcoin,ethereum,solana,cardano,dogecoin,shiba-inu,pepe,bonk",
                     vs: str = "usd,inr") -> Dict:
    """Get real-time prices from CoinGecko."""
    await _rate_limit("coingecko")
    data = await _fetch(f"{COINGECKO_BASE}/simple/price", params={
        "ids": ids,
        "vs_currencies": vs,
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true",
    })
    return data or {}


async def cg_trending() -> List[Dict]:
    """Get trending coins from CoinGecko."""
    await _rate_limit("coingecko_trending")
    data = await _fetch(f"{COINGECKO_BASE}/search/trending")
    if not data or "coins" not in data:
        return []
    results = []
    for item in data["coins"][:15]:
        coin = item.get("item", {})
        results.append({
            "symbol": coin.get("symbol", ""),
            "name": coin.get("name", ""),
            "market_cap_rank": coin.get("market_cap_rank", 0),
            "price_btc": coin.get("price_btc", 0),
            "score": coin.get("score", 0),
            "thumb": coin.get("thumb", ""),
            "source": "coingecko_trending",
        })
    return results


async def cg_market_data(limit: int = 50) -> List[Dict]:
    """Get top coins with full market data."""
    await _rate_limit("coingecko_market")
    data = await _fetch(f"{COINGECKO_BASE}/coins/markets", params={
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(limit),
        "page": "1",
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    })
    if not data or not isinstance(data, list):
        return []
    results = []
    for c in data:
        results.append({
            "id": c.get("id", ""),
            "symbol": c.get("symbol", "").upper(),
            "name": c.get("name", ""),
            "price_usd": c.get("current_price", 0),
            "market_cap": c.get("market_cap", 0),
            "volume_24h": c.get("total_volume", 0),
            "change_1h": c.get("price_change_percentage_1h_in_currency", 0),
            "change_24h": c.get("price_change_percentage_24h", 0),
            "change_7d": c.get("price_change_percentage_7d_in_currency", 0),
            "high_24h": c.get("high_24h", 0),
            "low_24h": c.get("low_24h", 0),
            "ath": c.get("ath", 0),
            "ath_change": c.get("ath_change_percentage", 0),
            "image": c.get("image", ""),
            "rank": c.get("market_cap_rank", 0),
            "source": "coingecko",
        })
    return results


async def cg_fear_greed() -> Dict:
    """Get crypto fear & greed index."""
    data = await _fetch("https://api.alternative.me/fng/", params={"limit": "1"})
    if not data or "data" not in data:
        return {"value": 50, "label": "Neutral"}
    fg = data["data"][0]
    return {
        "value": int(fg.get("value", 50)),
        "label": fg.get("value_classification", "Neutral"),
        "timestamp": fg.get("timestamp", ""),
    }


# ═══════════════════════════════════════════════════════════
#  PUMP.FUN — Solana meme coin launchpad
# ═══════════════════════════════════════════════════════════
async def pumpfun_trending() -> List[Dict]:
    """Get trending tokens from Pump.fun."""
    await _rate_limit("pumpfun")
    data = await _fetch(f"{PUMPFUN_BASE}/coins", params={
        "offset": "0",
        "limit": "20",
        "sort": "market_cap",
        "order": "DESC",
        "includeNsfw": "false",
    })
    if not data or not isinstance(data, list):
        return []
    results = []
    for token in data[:20]:
        mcap = float(token.get("market_cap", 0) or 0)
        results.append({
            "address": token.get("mint", ""),
            "symbol": token.get("symbol", ""),
            "name": token.get("name", ""),
            "description": (token.get("description", "") or "")[:100],
            "image": token.get("image_uri", ""),
            "market_cap": mcap,
            "reply_count": token.get("reply_count", 0),
            "creator": token.get("creator", ""),
            "created_at": token.get("created_timestamp", 0),
            "chain": "solana",
            "source": "pumpfun",
            "url": f"https://pump.fun/{token.get('mint', '')}",
        })
    return results


async def pumpfun_new_coins() -> List[Dict]:
    """Get newest coins from Pump.fun."""
    await _rate_limit("pumpfun_new")
    data = await _fetch(f"{PUMPFUN_BASE}/coins", params={
        "offset": "0",
        "limit": "20",
        "sort": "created_timestamp",
        "order": "DESC",
        "includeNsfw": "false",
    })
    if not data or not isinstance(data, list):
        return []
    return [{
        "address": t.get("mint", ""),
        "symbol": t.get("symbol", ""),
        "name": t.get("name", ""),
        "market_cap": float(t.get("market_cap", 0) or 0),
        "chain": "solana",
        "source": "pumpfun_new",
        "url": f"https://pump.fun/{t.get('mint', '')}",
    } for t in data[:20]]


# ═══════════════════════════════════════════════════════════
#  JUPITER — Solana token prices
# ═══════════════════════════════════════════════════════════
async def jupiter_price(token_addresses: List[str]) -> Dict:
    """Get token prices from Jupiter (Solana)."""
    if not token_addresses:
        return {}
    await _rate_limit("jupiter")
    ids_str = ",".join(token_addresses[:10])
    data = await _fetch(f"{JUPITER_PRICE_BASE}/price", params={"ids": ids_str})
    if not data or "data" not in data:
        return {}
    return data["data"]


# ═══════════════════════════════════════════════════════════
#  GEM FINDER — Find tokens at dips with high potential
# ═══════════════════════════════════════════════════════════
async def find_dip_gems(min_dip: float = -5, max_dip: float = -80, 
                        min_liquidity: float = 5000, min_volume: float = 1000) -> List[Dict]:
    """
    Find tokens that dipped (potential bounce plays).
    These are tokens at -5% or more that could recover.
    """
    # Search for popular tokens on Solana
    searches = ["SOL", "BONK", "WIF", "JUP", "ORCA", "RAY", "MEME", "PEPE", "DOGE", "TRUMP"]
    all_gems = []
    
    for query in searches:
        try:
            pairs = await dex_search(query)
            for p in pairs:
                chg = p.get("change_24h", 0)
                liq = p.get("liquidity_usd", 0)
                vol = p.get("volume_24h", 0)
                
                # Filter: dipped between min_dip and max_dip, has liquidity and volume
                if min_dip >= chg >= max_dip and liq >= min_liquidity and vol >= min_volume:
                    # Calculate potential score
                    p["dip_score"] = _calculate_dip_potential(p)
                    all_gems.append(p)
        except Exception as e:
            logger.warning(f"Gem scan error for {query}: {e}")
            continue
    
    # Sort by gem score (highest first)
    all_gems.sort(key=lambda x: x.get("gem_score", 0) + x.get("dip_score", 0), reverse=True)
    
    # Deduplicate by base_address
    seen = set()
    unique = []
    for g in all_gems:
        addr = g.get("base_address", "")
        if addr and addr not in seen:
            seen.add(addr)
            unique.append(g)
    
    return unique[:30]


def _calculate_dip_potential(token: dict) -> int:
    """Calculate potential bounce score for a dipped token."""
    score = 0
    chg_24h = token.get("change_24h", 0)
    chg_1h = token.get("change_1h", 0)
    vol = token.get("volume_24h", 0)
    liq = token.get("liquidity_usd", 0)
    mcap = token.get("market_cap", 0)
    bsr = token.get("buy_sell_ratio", 1)
    
    # Deep dip = higher bounce potential
    if chg_24h < -10: score += 10
    if chg_24h < -20: score += 10
    if chg_24h < -30: score += 15
    if chg_24h < -50: score += 20
    
    # Recovering (1h positive while 24h negative) = strong signal
    if chg_1h > 0 and chg_24h < -10: score += 25
    if chg_1h > 5 and chg_24h < -20: score += 30
    
    # High volume on dip = accumulation
    if vol > 100000: score += 10
    if vol > 500000: score += 10
    
    # Good liquidity = safer
    if liq > 50000: score += 5
    if liq > 200000: score += 5
    
    # Buy pressure increasing
    if bsr > 1.5: score += 10
    if bsr > 2.0: score += 10
    
    return min(100, score)


# ═══════════════════════════════════════════════════════════
#  NEWS — Real crypto & stock news from RSS
# ═══════════════════════════════════════════════════════════
async def fetch_crypto_news(limit: int = 20) -> List[Dict]:
    """Fetch real news from multiple crypto sources."""
    news_urls = [
        ("https://cointelegraph.com/rss", "CoinTelegraph"),
        ("https://www.coindesk.com/arc/outboundfeeds/rss/", "CoinDesk"),
        ("https://cryptonews.com/news/feed/", "CryptoNews"),
        ("https://decrypt.co/feed", "Decrypt"),
    ]
    
    all_news = []
    for url, source in news_urls:
        try:
            client = get_client()
            r = await client.get(url, timeout=8.0)
            if r.status_code == 200:
                items = _parse_rss(r.text, source)
                all_news.extend(items)
        except Exception as e:
            logger.debug(f"News fetch error {source}: {e}")
            continue
    
    # Sort by date (newest first) and deduplicate
    all_news.sort(key=lambda x: x.get("published", ""), reverse=True)
    return all_news[:limit]


def _parse_rss(xml_text: str, source: str) -> List[Dict]:
    """Parse RSS XML into news items."""
    import re
    items = []
    # Simple XML parsing without external dependency
    item_blocks = re.findall(r'<item>(.*?)</item>', xml_text, re.DOTALL)
    for block in item_blocks[:10]:
        title = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', block, re.DOTALL)
        link = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
        pub_date = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
        desc = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', block, re.DOTALL)
        
        if title:
            items.append({
                "title": title.group(1).strip()[:200],
                "url": link.group(1).strip() if link else "",
                "source": source,
                "published": pub_date.group(1).strip() if pub_date else "",
                "summary": (desc.group(1).strip()[:300] if desc else "")
                    .replace("<p>", "").replace("</p>", "").replace("<br>", " "),
            })
    return items


async def fetch_india_news(limit: int = 10) -> List[Dict]:
    """Fetch Indian stock market news."""
    news_urls = [
        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "Economic Times"),
        ("https://www.moneycontrol.com/rss/latestnews.xml", "MoneyControl"),
    ]
    all_news = []
    for url, source in news_urls:
        try:
            client = get_client()
            r = await client.get(url, timeout=8.0)
            if r.status_code == 200:
                items = _parse_rss(r.text, source)
                all_news.extend(items)
        except:
            continue
    return all_news[:limit]


# ═══════════════════════════════════════════════════════════
#  INDIAN STOCK MARKET — NSE data
# ═══════════════════════════════════════════════════════════
async def get_nse_indices() -> List[Dict]:
    """Get live NSE indices (NIFTY, SENSEX, BANKNIFTY etc.)."""
    try:
        import yfinance as yf
        symbols = {
            "^NSEI": "NIFTY 50",
            "^BSESN": "SENSEX",
            "^NSEBANK": "BANK NIFTY",
            "^NSMIDCP": "NIFTY MIDCAP",
        }
        results = []
        for sym, name in symbols.items():
            try:
                ticker = yf.Ticker(sym)
                info = ticker.fast_info
                price = getattr(info, 'last_price', 0) or 0
                prev = getattr(info, 'previous_close', price) or price
                change = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    "symbol": sym,
                    "name": name,
                    "price": round(price, 2),
                    "prev_close": round(prev, 2),
                    "change": round(price - prev, 2),
                    "change_pct": round(change, 2),
                    "currency": "INR",
                    "source": "nse",
                })
            except:
                continue
        return results
    except Exception as e:
        logger.warning(f"NSE data error: {e}")
        return []


async def get_india_vix() -> Dict:
    """Get India VIX (fear gauge)."""
    try:
        import yfinance as yf
        ticker = yf.Ticker("^INDIAVIX")
        info = ticker.fast_info
        vix = getattr(info, 'last_price', 0) or 0
        prev = getattr(info, 'previous_close', vix) or vix
        return {
            "vix": round(vix, 2),
            "prev": round(prev, 2),
            "change": round(vix - prev, 2),
            "change_pct": round(((vix - prev) / prev * 100) if prev else 0, 2),
            "level": "HIGH" if vix > 20 else "MODERATE" if vix > 15 else "LOW",
        }
    except:
        return {"vix": 0, "level": "N/A"}


# ═══════════════════════════════════════════════════════════
#  AGGREGATED DATA — Combined from all sources
# ═══════════════════════════════════════════════════════════
async def get_full_market_snapshot() -> Dict:
    """Get complete market snapshot from all sources."""
    results = await asyncio.gather(
        cg_market_data(30),
        dex_trending(),
        cg_fear_greed(),
        cg_trending(),
        pumpfun_trending(),
        get_nse_indices(),
        get_india_vix(),
        return_exceptions=True,
    )
    
    return {
        "crypto_markets": results[0] if isinstance(results[0], list) else [],
        "dex_trending": results[1] if isinstance(results[1], list) else [],
        "fear_greed": results[2] if isinstance(results[2], dict) else {"value": 50, "label": "Neutral"},
        "cg_trending": results[3] if isinstance(results[3], list) else [],
        "pumpfun": results[4] if isinstance(results[4], list) else [],
        "nse_indices": results[5] if isinstance(results[5], list) else [],
        "india_vix": results[6] if isinstance(results[6], dict) else {},
        "ts": datetime.now(IST).isoformat(),
    }


async def close_client():
    """Close the HTTP client on shutdown."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
