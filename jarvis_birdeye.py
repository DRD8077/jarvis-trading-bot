"""
🦅 JARVIS Birdeye Engine — Solana DEX Intelligence
═══════════════════════════════════════════════════════
Birdeye API for superior Solana data:
- Token prices with multi-DEX aggregation
- Wallet tracking & top holders
- Token security scores
- OHLCV data for charting
- New token detection
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List, Any

logger = logging.getLogger("jarvis-birdeye")

BIRDEYE_BASE = "https://public-api.birdeye.so"
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")


def _headers() -> dict:
    return {
        "X-API-KEY": BIRDEYE_API_KEY,
        "Accept": "application/json",
        "x-chain": "solana",
    }


def is_available() -> bool:
    return bool(BIRDEYE_API_KEY)


async def _fetch(url: str, params: dict = None, chain: str = "solana") -> Optional[dict]:
    """Fetch from Birdeye API."""
    if not BIRDEYE_API_KEY:
        return None
    try:
        import httpx
        hdrs = _headers()
        hdrs["x-chain"] = chain
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=hdrs, params=params or {})
            if r.status_code == 200:
                data = r.json()
                return data.get("data", data)
            logger.warning(f"Birdeye API {r.status_code}: {url}")
            return None
    except Exception as e:
        logger.warning(f"Birdeye fetch error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  TOKEN PRICE & INFO
# ═══════════════════════════════════════════════════════════
async def get_token_price(address: str, chain: str = "solana") -> Optional[Dict]:
    """Get real-time token price from Birdeye."""
    data = await _fetch(f"{BIRDEYE_BASE}/defi/price", {"address": address}, chain)
    if not data:
        return None
    return {
        "address": address,
        "price_usd": data.get("value", 0),
        "update_time": data.get("updateUnixTime", 0),
        "source": "birdeye",
    }


async def get_multi_price(addresses: List[str], chain: str = "solana") -> Dict:
    """Get prices for multiple tokens at once."""
    addr_str = ",".join(addresses[:30])
    data = await _fetch(f"{BIRDEYE_BASE}/defi/multi_price", {"list_address": addr_str}, chain)
    if not data:
        return {}
    return {addr: {"price_usd": info.get("value", 0)} for addr, info in data.items()} if isinstance(data, dict) else {}


async def get_token_overview(address: str, chain: str = "solana") -> Optional[Dict]:
    """Get token overview with supply, holder, market data."""
    data = await _fetch(f"{BIRDEYE_BASE}/defi/token_overview", {"address": address}, chain)
    if not data:
        return None
    return {
        "address": address,
        "name": data.get("name", ""),
        "symbol": data.get("symbol", ""),
        "decimals": data.get("decimals", 0),
        "price_usd": data.get("price", 0),
        "market_cap": data.get("mc", 0),
        "holder_count": data.get("holder", 0),
        "supply": data.get("supply", 0),
        "volume_24h": data.get("v24hUSD", 0),
        "volume_change_24h": data.get("v24hChangePercent", 0),
        "price_change_24h": data.get("priceChange24hPercent", 0),
        "liquidity": data.get("liquidity", 0),
        "trade_count_24h": data.get("trade24h", 0),
        "buy_count_24h": data.get("buy24h", 0),
        "sell_count_24h": data.get("sell24h", 0),
        "unique_wallets_24h": data.get("uniqueWallet24h", 0),
        "source": "birdeye",
    }


# ═══════════════════════════════════════════════════════════
#  TOKEN SECURITY
# ═══════════════════════════════════════════════════════════
async def get_token_security(address: str, chain: str = "solana") -> Optional[Dict]:
    """Get token security analysis."""
    data = await _fetch(f"{BIRDEYE_BASE}/defi/token_security", {"address": address}, chain)
    if not data:
        return None
    return {
        "address": address,
        "is_token_2022": data.get("isToken2022", False),
        "is_honeypot": False,  # Birdeye doesn't directly flag this
        "top_10_holder_pct": data.get("top10HolderPercent", 0),
        "owner_address": data.get("ownerAddress", ""),
        "creation_tx": data.get("creationTx", ""),
        "creation_time": data.get("creationTime", 0),
        "mint_authority": data.get("mintAuthority", None),
        "freeze_authority": data.get("freezeAuthority", None),
        "is_mutable": data.get("isMutable", True),
        "risk_score": _calc_risk_score(data),
        "source": "birdeye",
    }


def _calc_risk_score(data: dict) -> int:
    """Calculate a 0-100 risk score (higher = riskier)."""
    score = 0
    if data.get("top10HolderPercent", 0) > 80:
        score += 30
    elif data.get("top10HolderPercent", 0) > 50:
        score += 15
    if data.get("mintAuthority"):
        score += 20
    if data.get("freezeAuthority"):
        score += 15
    if data.get("isMutable", True):
        score += 10
    if not data.get("creationTx"):
        score += 10
    return min(score, 100)


# ═══════════════════════════════════════════════════════════
#  TRENDING & NEW TOKENS  
# ═══════════════════════════════════════════════════════════
async def get_trending_tokens(chain: str = "solana", limit: int = 20) -> List[Dict]:
    """Get trending tokens by volume."""
    data = await _fetch(
        f"{BIRDEYE_BASE}/defi/tokenlist",
        {"sort_by": "v24hUSD", "sort_type": "desc", "offset": 0, "limit": limit},
        chain,
    )
    if not data:
        return []
    tokens = data.get("tokens", data) if isinstance(data, dict) else data
    if not isinstance(tokens, list):
        return []
    return [{
        "address": t.get("address", ""),
        "name": t.get("name", "Unknown"),
        "symbol": t.get("symbol", ""),
        "price_usd": t.get("price", 0) or t.get("v", 0),
        "volume_24h": t.get("v24hUSD", 0),
        "price_change_24h": t.get("priceChange24hPercent", 0) or t.get("v24hChangePercent", 0),
        "market_cap": t.get("mc", 0),
        "liquidity": t.get("liquidity", 0),
        "chain": chain,
        "source": "birdeye_trending",
    } for t in tokens[:limit]]


async def get_new_listings(chain: str = "solana", limit: int = 20) -> List[Dict]:
    """Get newly listed tokens."""
    data = await _fetch(
        f"{BIRDEYE_BASE}/defi/tokenlist",
        {"sort_by": "createdAt", "sort_type": "desc", "offset": 0, "limit": limit},
        chain,
    )
    if not data:
        return []
    tokens = data.get("tokens", data) if isinstance(data, dict) else data
    if not isinstance(tokens, list):
        return []
    return [{
        "address": t.get("address", ""),
        "name": t.get("name", "Unknown"),
        "symbol": t.get("symbol", ""),
        "price_usd": t.get("price", 0),
        "volume_24h": t.get("v24hUSD", 0),
        "market_cap": t.get("mc", 0),
        "liquidity": t.get("liquidity", 0),
        "chain": chain,
        "source": "birdeye_new",
    } for t in tokens[:limit]]


# ═══════════════════════════════════════════════════════════
#  WALLET TRACKING
# ═══════════════════════════════════════════════════════════
async def get_wallet_portfolio(wallet: str, chain: str = "solana") -> Optional[Dict]:
    """Get wallet token holdings."""
    data = await _fetch(f"{BIRDEYE_BASE}/v1/wallet/token_list", {"wallet": wallet}, chain)
    if not data:
        return None
    items = data.get("items", []) if isinstance(data, dict) else []
    holdings = []
    total_usd = 0
    for item in items[:50]:
        val = float(item.get("valueUsd", 0) or 0)
        total_usd += val
        holdings.append({
            "address": item.get("address", ""),
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "balance": item.get("uiAmount", 0),
            "value_usd": val,
            "price_usd": item.get("priceUsd", 0),
        })
    return {
        "wallet": wallet,
        "total_value_usd": total_usd,
        "token_count": len(holdings),
        "holdings": sorted(holdings, key=lambda x: x["value_usd"], reverse=True),
    }


# ═══════════════════════════════════════════════════════════
#  OHLCV DATA
# ═══════════════════════════════════════════════════════════
async def get_ohlcv(address: str, interval: str = "15m", chain: str = "solana") -> List[Dict]:
    """Get OHLCV candle data for charting."""
    import time as _time
    now = int(_time.time())
    time_from = now - 86400  # Last 24 hours
    data = await _fetch(
        f"{BIRDEYE_BASE}/defi/ohlcv",
        {"address": address, "type": interval, "time_from": time_from, "time_to": now},
        chain,
    )
    if not data:
        return []
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [{
        "time": c.get("unixTime", 0),
        "open": c.get("o", 0),
        "high": c.get("h", 0),
        "low": c.get("l", 0),
        "close": c.get("c", 0),
        "volume": c.get("v", 0),
    } for c in items]


# ═══════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════
async def get_birdeye_summary() -> Dict:
    """Dashboard summary."""
    if not BIRDEYE_API_KEY:
        return {"available": False, "error": "BIRDEYE_API_KEY not configured"}
    try:
        trending = await get_trending_tokens(limit=5)
        return {
            "available": True,
            "trending_count": len(trending),
            "top_3": trending[:3],
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


BIRDEYE_AVAILABLE = bool(BIRDEYE_API_KEY)
status = "active" if BIRDEYE_API_KEY else "inactive (no API key)"
logger.info(f"🦅 Birdeye engine loaded — {status}")
