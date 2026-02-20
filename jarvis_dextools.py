"""
🔧 JARVIS DexTools Engine — Token Analytics & Hot Pairs
═══════════════════════════════════════════════════════════
Uses DexTools API v2 for:
- Pair explorer with real price data
- Token audit scores & security checks
- Hot pairs & trending tokens
- Pool info & liquidity data
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List, Any

logger = logging.getLogger("jarvis-dextools")

DEXTOOLS_BASE = "https://public-api.dextools.io/trial/v2"
DEXTOOLS_API_KEY = os.getenv("DEXTOOLS_API_KEY", "")

# Supported chains
CHAIN_MAP = {
    "ethereum": "ether", "eth": "ether", "solana": "solana", "sol": "solana",
    "bsc": "bsc", "bnb": "bsc", "polygon": "polygon", "matic": "polygon",
    "arbitrum": "arbitrum", "arb": "arbitrum", "base": "base",
    "avalanche": "avalanche", "avax": "avalanche", "optimism": "optimism",
}


def _headers() -> dict:
    return {
        "X-BLOBR-KEY": DEXTOOLS_API_KEY,
        "Accept": "application/json",
    }


def is_available() -> bool:
    return bool(DEXTOOLS_API_KEY)


async def _fetch(url: str, params: dict = None) -> Optional[dict]:
    """Fetch from DexTools API."""
    if not DEXTOOLS_API_KEY:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=_headers(), params=params or {})
            if r.status_code == 200:
                data = r.json()
                return data.get("data", data)
            logger.warning(f"DexTools API {r.status_code}: {url}")
            return None
    except Exception as e:
        logger.warning(f"DexTools fetch error: {e}")
        return None


def _normalize_chain(chain: str) -> str:
    return CHAIN_MAP.get(chain.lower(), chain.lower())


# ═══════════════════════════════════════════════════════════
#  HOT PAIRS / TRENDING
# ═══════════════════════════════════════════════════════════
async def get_hot_pairs(chain: str = "solana") -> List[Dict]:
    """Get hot/trending pairs on a chain."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/ranking/{c}/hotpools")
    if not data:
        return []
    pools = data if isinstance(data, list) else data.get("results", [])
    results = []
    for p in pools[:30]:
        main_token = p.get("mainToken", {}) or {}
        results.append({
            "name": main_token.get("name", p.get("name", "Unknown")),
            "symbol": main_token.get("symbol", p.get("symbol", "")),
            "address": main_token.get("address", ""),
            "chain": chain,
            "price_usd": p.get("price", 0),
            "price_change_24h": p.get("variation24h", 0),
            "volume_24h": p.get("volume24h", 0),
            "liquidity_usd": p.get("liquidity", 0),
            "creation_time": p.get("creationTime", ""),
            "source": "dextools_hot",
        })
    return results


async def get_gainers(chain: str = "solana") -> List[Dict]:
    """Get top gainers on chain."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/ranking/{c}/gainers")
    if not data:
        return []
    tokens = data if isinstance(data, list) else data.get("results", [])
    results = []
    for t in tokens[:20]:
        results.append({
            "name": t.get("name", "Unknown"),
            "symbol": t.get("symbol", ""),
            "address": t.get("address", ""),
            "chain": chain,
            "price_usd": t.get("price", 0),
            "change_24h": t.get("variation24h", 0),
            "volume_24h": t.get("volume24h", 0),
            "source": "dextools_gainer",
        })
    return results


async def get_losers(chain: str = "solana") -> List[Dict]:
    """Get top losers on chain."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/ranking/{c}/losers")
    if not data:
        return []
    tokens = data if isinstance(data, list) else data.get("results", [])
    return [{
        "name": t.get("name", "Unknown"),
        "symbol": t.get("symbol", ""),
        "address": t.get("address", ""),
        "chain": chain,
        "price_usd": t.get("price", 0),
        "change_24h": t.get("variation24h", 0),
        "source": "dextools_loser",
    } for t in tokens[:20]]


# ═══════════════════════════════════════════════════════════
#  TOKEN INFO & AUDIT
# ═══════════════════════════════════════════════════════════
async def get_token_info(chain: str, address: str) -> Optional[Dict]:
    """Get detailed token information."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/token/{c}/{address}")
    if not data:
        return None
    return {
        "name": data.get("name", ""),
        "symbol": data.get("symbol", ""),
        "address": address,
        "chain": chain,
        "decimals": data.get("decimals", 18),
        "total_supply": data.get("totalSupply", 0),
        "holders": data.get("holders", 0),
        "creation_time": data.get("creationTime", ""),
        "description": data.get("description", ""),
        "website": data.get("links", {}).get("website", ""),
        "twitter": data.get("links", {}).get("twitter", ""),
        "telegram": data.get("links", {}).get("telegram", ""),
        "logo": data.get("logo", ""),
    }


async def get_token_audit(chain: str, address: str) -> Optional[Dict]:
    """Get token audit/security score from DexTools."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/token/{c}/{address}/audit")
    if not data:
        return None
    return {
        "address": address,
        "chain": chain,
        "is_open_source": data.get("isOpenSource", False),
        "is_honeypot": data.get("isHoneypot", False),
        "is_mintable": data.get("isMintable", False),
        "is_proxy": data.get("isProxy", False),
        "is_blacklisted": data.get("isBlacklisted", False),
        "buy_tax": data.get("buyTax", {}).get("max", 0),
        "sell_tax": data.get("sellTax", {}).get("max", 0),
        "holder_count": data.get("holders", 0),
        "lp_holders": data.get("lpHolders", 0),
        "is_lp_locked": data.get("isLpLocked", False),
        "dextools_score": data.get("dextScore", {}).get("total", 0),
        "risk_level": "high" if data.get("isHoneypot") else ("medium" if data.get("isMintable") else "low"),
    }


async def get_token_price(chain: str, address: str) -> Optional[Dict]:
    """Get real-time token price."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/token/{c}/{address}/price")
    if not data:
        return None
    return {
        "price_usd": data.get("price", 0),
        "price_chain": data.get("priceChain", 0),
        "variation_5m": data.get("variation5m", 0),
        "variation_1h": data.get("variation1h", 0),
        "variation_6h": data.get("variation6h", 0),
        "variation_24h": data.get("variation24h", 0),
    }


# ═══════════════════════════════════════════════════════════
#  POOL / PAIR INFO
# ═══════════════════════════════════════════════════════════
async def get_token_pools(chain: str, address: str) -> List[Dict]:
    """Get all liquidity pools for a token."""
    c = _normalize_chain(chain)
    data = await _fetch(f"{DEXTOOLS_BASE}/token/{c}/{address}/pools", params={"sort": "volume24h", "order": "desc"})
    if not data:
        return []
    pools = data if isinstance(data, list) else data.get("results", [])
    return [{
        "pair_address": p.get("address", ""),
        "dex": p.get("exchange", {}).get("name", "Unknown") if isinstance(p.get("exchange"), dict) else str(p.get("exchange", "")),
        "liquidity": p.get("liquidity", 0),
        "volume_24h": p.get("volume24h", 0),
        "price": p.get("price", 0),
        "creation_time": p.get("creationTime", ""),
    } for p in pools[:10]]


# ═══════════════════════════════════════════════════════════
#  MULTI-CHAIN SCAN
# ═══════════════════════════════════════════════════════════
async def scan_all_chains() -> List[Dict]:
    """Scan hot pairs across multiple chains."""
    chains = ["solana", "ethereum", "bsc", "base", "arbitrum"]
    tasks = [get_hot_pairs(c) for c in chains]
    results_raw = await asyncio.gather(*tasks, return_exceptions=True)
    all_pairs = []
    for chain, result in zip(chains, results_raw):
        if isinstance(result, list):
            all_pairs.extend(result)
    # Sort by volume
    all_pairs.sort(key=lambda x: float(x.get("volume_24h", 0) or 0), reverse=True)
    return all_pairs[:50]


# ═══════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════
async def get_dextools_summary() -> Dict:
    """Get a summary of DexTools data for dashboard."""
    if not DEXTOOLS_API_KEY:
        return {"available": False, "error": "DEXTOOLS_API_KEY not configured"}
    try:
        hot = await get_hot_pairs("solana")
        return {
            "available": True,
            "hot_pairs": len(hot),
            "top_3": hot[:3],
            "chains_supported": list(CHAIN_MAP.values()),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


# Aliases for server
get_trending = get_hot_pairs  # server expects get_trending

DEXTOOLS_AVAILABLE = bool(DEXTOOLS_API_KEY)
status = "active" if DEXTOOLS_API_KEY else "inactive (no API key)"
logger.info(f"🔧 DexTools engine loaded — {status}")
