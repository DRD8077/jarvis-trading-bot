"""
╔══════════════════════════════════════════════════════════════════════╗
║           JARVIS SERVER — MARKET DATA ENGINE                         ║
║           Real-time Crypto + Stock Data                               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import time
import logging
import asyncio
from typing import Optional, Dict, List
from datetime import datetime

import httpx
from config import COINGECKO_BASE, BINANCE_BASE, DEXSCREENER_BASE, MARKET_CACHE_TTL

logger = logging.getLogger("jarvis.market")

# ═══════════════════════════════════════════════════════════════════
#  IN-MEMORY CACHE
# ═══════════════════════════════════════════════════════════════════

_cache: Dict[str, tuple] = {}  # key -> (data, timestamp)


def _get_cached(key: str, ttl: int = MARKET_CACHE_TTL):
    """Get cached data if still valid."""
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < ttl:
            return data
    return None


def _set_cached(key: str, data):
    """Cache data."""
    _cache[key] = (data, time.time())


# ═══════════════════════════════════════════════════════════════════
#  HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "JARVIS-Trading-Bot/2.0"},
        )
    return _client


# ═══════════════════════════════════════════════════════════════════
#  COINGECKO — Top Crypto Data
# ═══════════════════════════════════════════════════════════════════

async def get_top_cryptos(limit: int = 100, currency: str = "usd") -> List[dict]:
    """Get top cryptocurrencies by market cap."""
    cache_key = f"top_cryptos_{limit}_{currency}"
    cached = _get_cached(cache_key, ttl=30)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": currency,
                "order": "market_cap_desc",
                "per_page": min(limit, 250),
                "page": 1,
                "sparkline": "true",
                "price_change_percentage": "1h,24h,7d",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        _set_cached(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"CoinGecko top cryptos error: {e}")
        return _get_cached(cache_key, ttl=600) or []  # Return stale cache if available


async def get_crypto_price(coin_id: str, currency: str = "usd") -> dict:
    """Get detailed price data for a specific coin."""
    cache_key = f"price_{coin_id}_{currency}"
    cached = _get_cached(cache_key, ttl=15)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{COINGECKO_BASE}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
            },
        )
        resp.raise_for_status()
        raw = resp.json()

        md = raw.get("market_data", {})
        data = {
            "id": raw["id"],
            "symbol": raw["symbol"].upper(),
            "name": raw["name"],
            "image": raw.get("image", {}).get("small", ""),
            "price": md.get("current_price", {}).get(currency, 0),
            "market_cap": md.get("market_cap", {}).get(currency, 0),
            "volume": md.get("total_volume", {}).get(currency, 0),
            "change_24h": md.get("price_change_percentage_24h", 0),
            "change_7d": md.get("price_change_percentage_7d", 0),
            "change_30d": md.get("price_change_percentage_30d", 0),
            "high_24h": md.get("high_24h", {}).get(currency, 0),
            "low_24h": md.get("low_24h", {}).get(currency, 0),
            "ath": md.get("ath", {}).get(currency, 0),
            "ath_change": md.get("ath_change_percentage", {}).get(currency, 0),
            "circulating_supply": md.get("circulating_supply", 0),
            "total_supply": md.get("total_supply", 0),
            "last_updated": raw.get("last_updated", ""),
        }
        _set_cached(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"CoinGecko price error for {coin_id}: {e}")
        return _get_cached(cache_key, ttl=600) or {"error": str(e)}


async def search_crypto(query: str) -> List[dict]:
    """Search for cryptocurrencies."""
    try:
        client = get_client()
        resp = await client.get(
            f"{COINGECKO_BASE}/search",
            params={"query": query},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("coins", [])[:20]
    except Exception as e:
        logger.error(f"CoinGecko search error: {e}")
        return []


async def get_trending() -> List[dict]:
    """Get trending coins."""
    cache_key = "trending"
    cached = _get_cached(cache_key, ttl=120)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(f"{COINGECKO_BASE}/search/trending")
        resp.raise_for_status()
        data = resp.json()
        coins = [item["item"] for item in data.get("coins", [])]
        _set_cached(cache_key, coins)
        return coins
    except Exception as e:
        logger.error(f"CoinGecko trending error: {e}")
        return []


async def get_global_market() -> dict:
    """Get global crypto market data."""
    cache_key = "global_market"
    cached = _get_cached(cache_key, ttl=60)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(f"{COINGECKO_BASE}/global")
        resp.raise_for_status()
        data = resp.json().get("data", {})
        _set_cached(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"CoinGecko global error: {e}")
        return {}


async def get_price_history(coin_id: str, days: int = 30, currency: str = "usd") -> list:
    """Get price history for charting."""
    cache_key = f"history_{coin_id}_{days}_{currency}"
    cached = _get_cached(cache_key, ttl=300)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            params={
                "vs_currency": currency,
                "days": days,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        _set_cached(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"Price history error: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════
#  BINANCE — Real-time Price Ticker
# ═══════════════════════════════════════════════════════════════════

async def get_binance_ticker(symbol: str = "BTCUSDT") -> dict:
    """Get real-time ticker from Binance."""
    cache_key = f"binance_{symbol}"
    cached = _get_cached(cache_key, ttl=5)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{BINANCE_BASE}/ticker/24hr",
            params={"symbol": symbol},
        )
        resp.raise_for_status()
        data = resp.json()
        result = {
            "symbol": data["symbol"],
            "price": float(data["lastPrice"]),
            "change_24h": float(data["priceChangePercent"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
            "volume": float(data["volume"]),
            "quote_volume": float(data["quoteVolume"]),
            "trades": int(data["count"]),
        }
        _set_cached(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Binance ticker error: {e}")
        return {}


async def get_binance_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100) -> list:
    """Get candlestick data from Binance."""
    cache_key = f"klines_{symbol}_{interval}_{limit}"
    cached = _get_cached(cache_key, ttl=30)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{BINANCE_BASE}/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
        )
        resp.raise_for_status()
        raw = resp.json()
        candles = []
        for k in raw:
            candles.append({
                "time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })
        _set_cached(cache_key, candles)
        return candles
    except Exception as e:
        logger.error(f"Binance klines error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
#  DEXSCREENER — DEX Token Data
# ═══════════════════════════════════════════════════════════════════

async def search_dex_tokens(query: str) -> List[dict]:
    """Search DEX tokens."""
    cache_key = f"dex_search_{query}"
    cached = _get_cached(cache_key, ttl=30)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"{DEXSCREENER_BASE}/dex/search",
            params={"q": query},
        )
        resp.raise_for_status()
        pairs = resp.json().get("pairs", [])[:20]
        _set_cached(cache_key, pairs)
        return pairs
    except Exception as e:
        logger.error(f"DexScreener search error: {e}")
        return []


async def get_dex_pair(chain: str, pair_address: str) -> dict:
    """Get specific DEX pair data."""
    try:
        client = get_client()
        resp = await client.get(
            f"{DEXSCREENER_BASE}/dex/pairs/{chain}/{pair_address}",
        )
        resp.raise_for_status()
        pairs = resp.json().get("pairs", [])
        return pairs[0] if pairs else {}
    except Exception as e:
        logger.error(f"DexScreener pair error: {e}")
        return {}


async def get_new_dex_pairs(chain: str = "solana") -> List[dict]:
    """Get newly created pairs on a chain."""
    cache_key = f"new_pairs_{chain}"
    cached = _get_cached(cache_key, ttl=60)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get(
            f"https://api.dexscreener.com/token-profiles/latest/v1",
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            filtered = [p for p in data if p.get("chainId") == chain][:20]
            _set_cached(cache_key, filtered)
            return filtered
        return []
    except Exception as e:
        logger.error(f"New pairs error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
#  MARKET SUMMARY (for AI context)
# ═══════════════════════════════════════════════════════════════════

async def get_market_summary() -> str:
    """Get concise market summary for AI context."""
    try:
        btc = await get_binance_ticker("BTCUSDT")
        eth = await get_binance_ticker("ETHUSDT")
        sol = await get_binance_ticker("SOLUSDT")
        global_data = await get_global_market()

        summary = f"""
BTC: ${btc.get('price', 0):,.2f} ({btc.get('change_24h', 0):+.2f}%)
ETH: ${eth.get('price', 0):,.2f} ({eth.get('change_24h', 0):+.2f}%)
SOL: ${sol.get('price', 0):,.2f} ({sol.get('change_24h', 0):+.2f}%)
Total Market Cap: ${global_data.get('total_market_cap', {}).get('usd', 0):,.0f}
BTC Dominance: {global_data.get('market_cap_percentage', {}).get('btc', 0):.1f}%
24h Volume: ${global_data.get('total_volume', {}).get('usd', 0):,.0f}
""".strip()
        return summary
    except Exception as e:
        logger.error(f"Market summary error: {e}")
        return "Market data temporarily unavailable"


# ═══════════════════════════════════════════════════════════════════
#  WHALE ALERTS (Large transactions)
# ═══════════════════════════════════════════════════════════════════

async def get_whale_transactions() -> List[dict]:
    """Get recent large crypto transactions from public APIs."""
    cache_key = "whale_txns"
    cached = _get_cached(cache_key, ttl=120)
    if cached:
        return cached

    try:
        client = get_client()
        # Use blockchain.info for large BTC transactions
        resp = await client.get(
            "https://blockchain.info/unconfirmed-transactions?format=json",
        )
        resp.raise_for_status()
        txns = resp.json().get("txs", [])

        whales = []
        for tx in txns:
            total = sum(out.get("value", 0) for out in tx.get("out", []))
            btc_amount = total / 1e8
            if btc_amount >= 10:  # 10+ BTC
                whales.append({
                    "hash": tx.get("hash", "")[:16] + "...",
                    "amount_btc": round(btc_amount, 4),
                    "time": tx.get("time", 0),
                    "type": "BTC Transfer",
                })

        whales = whales[:20]
        _set_cached(cache_key, whales)
        return whales
    except Exception as e:
        logger.error(f"Whale alerts error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
#  FEAR & GREED INDEX
# ═══════════════════════════════════════════════════════════════════

async def get_fear_greed() -> dict:
    """Get crypto Fear & Greed Index."""
    cache_key = "fear_greed"
    cached = _get_cached(cache_key, ttl=3600)
    if cached:
        return cached

    try:
        client = get_client()
        resp = await client.get("https://api.alternative.me/fng/?limit=1")
        resp.raise_for_status()
        data = resp.json().get("data", [{}])[0]
        result = {
            "value": int(data.get("value", 50)),
            "classification": data.get("value_classification", "Neutral"),
            "timestamp": data.get("timestamp", ""),
        }
        _set_cached(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Fear & Greed error: {e}")
        return {"value": 50, "classification": "Neutral"}
