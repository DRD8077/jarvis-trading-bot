"""
🪙 SunCrypto Live Engine — Real-time Indian Crypto Exchange Data
═══════════════════════════════════════════════════════════════════
Live prices, trading pairs, order book from SunCrypto + CoinDCX + WazirX.
"""

import os, json, logging, time, asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger("suncrypto-engine")
IST = timezone(timedelta(hours=5, minutes=30))

# Cache
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def _cached(key, ttl=30):
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    return None

def _set_cache(key, data):
    _cache[key] = data
    _cache_ts[key] = time.time()


# ═══════════════════════════════════════════════════════════
#  CoinDCX Public API (Indian crypto exchange)
# ═══════════════════════════════════════════════════════════

async def get_coindcx_tickers() -> List[Dict]:
    """Get all CoinDCX ticker data in INR."""
    c = _cached("cdx_tickers", 15)
    if c:
        return c
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.coindcx.com/exchange/ticker")
            if resp.status_code == 200:
                data = resp.json()
                # Filter INR pairs
                inr_pairs = []
                for t in data:
                    market = t.get("market", "")
                    if "INR" in market:
                        symbol = market.replace("INR", "").replace("I-", "")
                        inr_pairs.append({
                            "symbol": symbol,
                            "market": market,
                            "last_price": float(t.get("last_price", 0)),
                            "bid": float(t.get("bid", 0)),
                            "ask": float(t.get("ask", 0)),
                            "volume": float(t.get("volume", 0)),
                            "change_24h": float(t.get("change_24_hour", 0)),
                            "high_24h": float(t.get("high", 0)),
                            "low_24h": float(t.get("low", 0)),
                            "timestamp": t.get("timestamp", 0)
                        })
                
                inr_pairs.sort(key=lambda x: x.get("volume", 0), reverse=True)
                _set_cache("cdx_tickers", inr_pairs)
                return inr_pairs
    except Exception as e:
        logger.warning(f"CoinDCX tickers error: {e}")
    
    return []


async def get_coindcx_markets() -> List[Dict]:
    """Get all CoinDCX market details."""
    c = _cached("cdx_markets", 300)
    if c:
        return c
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.coindcx.com/exchange/v1/markets_details")
            if resp.status_code == 200:
                data = resp.json()
                markets = [{
                    "symbol": m.get("symbol", ""),
                    "base_currency": m.get("base_currency_short_name", ""),
                    "target_currency": m.get("target_currency_short_name", ""),
                    "min_quantity": m.get("min_quantity", 0),
                    "max_quantity": m.get("max_quantity", 0),
                    "min_price": m.get("min_price", 0),
                    "step_size": m.get("step", 0),
                    "pair": m.get("pair", ""),
                    "status": m.get("status", "")
                } for m in data if m.get("target_currency_short_name") == "INR"]
                _set_cache("cdx_markets", markets)
                return markets
    except Exception as e:
        logger.warning(f"CoinDCX markets error: {e}")
    return []


async def get_coindcx_orderbook(pair: str = "BTCINR") -> Dict:
    """Get CoinDCX order book for a pair."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://public.coindcx.com/market_data/orderbook?pair=I-{pair}")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "pair": pair,
                    "bids": data.get("bids", {})[:10] if isinstance(data.get("bids"), list) else [],
                    "asks": data.get("asks", {})[:10] if isinstance(data.get("asks"), list) else []
                }
    except Exception as e:
        logger.warning(f"CoinDCX orderbook error: {e}")
    return {"pair": pair, "bids": [], "asks": []}


# ═══════════════════════════════════════════════════════════
#  WazirX Public API (another Indian exchange)
# ═══════════════════════════════════════════════════════════

async def get_wazirx_tickers() -> List[Dict]:
    """Get WazirX tickers for INR pairs."""
    c = _cached("wzx_tickers", 15)
    if c:
        return c
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.wazirx.com/sapi/v1/tickers/24hr")
            if resp.status_code == 200:
                data = resp.json()
                inr_pairs = []
                for t in data:
                    if t.get("quoteAsset") == "inr":
                        inr_pairs.append({
                            "symbol": t.get("baseAsset", "").upper(),
                            "last_price": float(t.get("lastPrice", 0)),
                            "volume": float(t.get("quoteVolume", 0)),
                            "change_24h": float(t.get("priceChangePercent", 0)),
                            "high_24h": float(t.get("highPrice", 0)),
                            "low_24h": float(t.get("lowPrice", 0)),
                            "bid": float(t.get("bidPrice", 0)),
                            "ask": float(t.get("askPrice", 0)),
                            "exchange": "WazirX"
                        })
                
                inr_pairs.sort(key=lambda x: x.get("volume", 0), reverse=True)
                _set_cache("wzx_tickers", inr_pairs)
                return inr_pairs
    except Exception as e:
        logger.warning(f"WazirX tickers error: {e}")
    return []


# ═══════════════════════════════════════════════════════════
#  Aggregated Indian Crypto Data
# ═══════════════════════════════════════════════════════════

async def get_all_inr_prices() -> List[Dict]:
    """Get prices from all Indian exchanges combined."""
    c = _cached("all_inr", 15)
    if c:
        return c
    
    cdx_data, wzx_data = await asyncio.gather(
        get_coindcx_tickers(),
        get_wazirx_tickers(),
        return_exceptions=True
    )
    
    if isinstance(cdx_data, Exception):
        cdx_data = []
    if isinstance(wzx_data, Exception):
        wzx_data = []
    
    # Merge by symbol, prefer CoinDCX
    merged = {}
    for t in (cdx_data or []):
        sym = t["symbol"]
        merged[sym] = {
            "symbol": sym,
            "coindcx_price": t["last_price"],
            "coindcx_volume": t["volume"],
            "change_24h": t["change_24h"],
            "high_24h": t["high_24h"],
            "low_24h": t["low_24h"],
            "price_inr": t["last_price"],
            "exchange": "CoinDCX"
        }
    
    for t in (wzx_data or []):
        sym = t["symbol"]
        if sym in merged:
            merged[sym]["wazirx_price"] = t["last_price"]
            merged[sym]["wazirx_volume"] = t["volume"]
            # Arbitrage detection
            cdx_p = merged[sym]["coindcx_price"]
            wzx_p = t["last_price"]
            if cdx_p and wzx_p:
                arb = abs(cdx_p - wzx_p) / min(cdx_p, wzx_p) * 100
                merged[sym]["arbitrage_pct"] = round(arb, 2)
                merged[sym]["best_buy"] = "WazirX" if wzx_p < cdx_p else "CoinDCX"
                merged[sym]["best_sell"] = "CoinDCX" if wzx_p < cdx_p else "WazirX"
        else:
            merged[sym] = {
                "symbol": sym,
                "wazirx_price": t["last_price"],
                "wazirx_volume": t["volume"],
                "change_24h": t["change_24h"],
                "high_24h": t["high_24h"],
                "low_24h": t["low_24h"],
                "price_inr": t["last_price"],
                "exchange": "WazirX"
            }
    
    result = sorted(merged.values(), key=lambda x: x.get("coindcx_volume", 0) + x.get("wazirx_volume", 0), reverse=True)
    _set_cache("all_inr", result)
    return result


async def get_top_inr_gainers(limit: int = 10) -> List[Dict]:
    """Get top gainers in INR markets."""
    prices = await get_all_inr_prices()
    gainers = sorted([p for p in prices if p.get("change_24h", 0) > 0], 
                     key=lambda x: x["change_24h"], reverse=True)
    return gainers[:limit]


async def get_top_inr_losers(limit: int = 10) -> List[Dict]:
    """Get top losers in INR markets."""
    prices = await get_all_inr_prices()
    losers = sorted([p for p in prices if p.get("change_24h", 0) < 0],
                    key=lambda x: x["change_24h"])
    return losers[:limit]


async def get_inr_price(symbol: str) -> Dict:
    """Get INR price for a specific crypto token."""
    prices = await get_all_inr_prices()
    for p in prices:
        if p["symbol"].upper() == symbol.upper():
            return p
    
    # Try individual fetch from CoinDCX
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://api.coindcx.com/exchange/ticker")
            if resp.status_code == 200:
                for t in resp.json():
                    market = t.get("market", "")
                    if symbol.upper() in market and "INR" in market:
                        return {
                            "symbol": symbol.upper(),
                            "price_inr": float(t.get("last_price", 0)),
                            "change_24h": float(t.get("change_24_hour", 0)),
                            "volume": float(t.get("volume", 0)),
                            "exchange": "CoinDCX"
                        }
    except:
        pass
    
    return {"symbol": symbol.upper(), "price_inr": 0, "error": "Not found"}


async def search_inr_tokens(query: str) -> List[Dict]:
    """Search tokens available on Indian exchanges."""
    prices = await get_all_inr_prices()
    query = query.upper()
    results = [p for p in prices if query in p.get("symbol", "").upper()]
    return results[:20]


async def get_arbitrage_opportunities(min_pct: float = 0.5) -> List[Dict]:
    """Find arbitrage opportunities between Indian exchanges."""
    prices = await get_all_inr_prices()
    arbs = [p for p in prices if p.get("arbitrage_pct", 0) >= min_pct]
    arbs.sort(key=lambda x: x.get("arbitrage_pct", 0), reverse=True)
    return arbs[:20]


logger.info("🪙 SunCrypto/Indian Crypto Engine loaded — CoinDCX + WazirX")
