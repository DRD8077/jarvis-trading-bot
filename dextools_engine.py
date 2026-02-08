"""
╔══════════════════════════════════════════════════════════════════╗
║  🔥 JARVIS DEXTOOLS ENGINE v1.0 — Multi-Chain Token Intelligence  ║
║  DexTools Pairs, Meme Board, Live New Pairs, Airdrops             ║
║  All Blockchains: ETH, BSC, SOL, BASE, ARB, MATIC, AVAX          ║
║  Real-Time Token Alerts with AI/ML Buy/Sell Signals               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import time
import json
import logging
import threading
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════

DEXTOOLS_API_KEY = os.environ.get("DEXTOOLS_API_KEY", "")
DEXSCREENER_BASE = "https://api.dexscreener.com/latest/dex"
DEXTOOLS_BASE = "https://public-api.dextools.io/trial/v2"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BIRDEYE_BASE = "https://public-api.birdeye.so"
BIRDEYE_KEY = os.environ.get("BIRDEYE_API_KEY", "")

# Supported chains
CHAINS = {
    "ethereum": {"dextools": "ether", "dexscreener": "ethereum", "symbol": "ETH", "emoji": "🔷"},
    "bsc": {"dextools": "bsc", "dexscreener": "bsc", "symbol": "BNB", "emoji": "🟡"},
    "solana": {"dextools": "solana", "dexscreener": "solana", "symbol": "SOL", "emoji": "💜"},
    "base": {"dextools": "base", "dexscreener": "base", "symbol": "BASE", "emoji": "🔵"},
    "arbitrum": {"dextools": "arbitrum", "dexscreener": "arbitrum", "symbol": "ARB", "emoji": "🌀"},
    "polygon": {"dextools": "polygon", "dexscreener": "polygon", "symbol": "MATIC", "emoji": "🟣"},
    "avalanche": {"dextools": "avalanche", "dexscreener": "avalanche", "symbol": "AVAX", "emoji": "🔺"},
    "ton": {"dextools": "ton", "dexscreener": "ton", "symbol": "TON", "emoji": "💎"},
}

# DexTools deep links for mobile
DEXTOOLS_WEB = "https://www.dextools.io/app"
DEXSCREENER_WEB = "https://dexscreener.com"

REQUEST_TIMEOUT = 15
MAX_RETRIES = 2

# Token cache
_token_cache = {}
_cache_ttl = 120  # 2 min

# Alert state
_alerted_tokens = {}
_dextools_running = False
_alert_callback = None
_scan_interval = 180  # 3 min

# ═══════════════════════════════════════════════════════════
#  HELPER — HTTP with retry
# ═══════════════════════════════════════════════════════════

def _safe_float(val, default=0) -> float:
    """Safely convert any value to float, stripping $ and commas."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.replace("$", "").replace(",", "").strip()
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    if isinstance(val, dict):
        return default
    try:
        return float(val)
    except:
        return default


def _get(url: str, headers: dict = None, params: dict = None, timeout: int = REQUEST_TIMEOUT) -> dict:
    """HTTP GET with retry and error handling."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                logger.warning(f"[DEXTOOLS] {url} returned {resp.status_code}")
                return {}
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"[DEXTOOLS] Request failed: {url} — {e}")
            time.sleep(1)
    return {}

def _dextools_headers():
    """DexTools API headers."""
    h = {"accept": "application/json"}
    if DEXTOOLS_API_KEY:
        h["X-BLOBR-KEY"] = DEXTOOLS_API_KEY
    return h


# ═══════════════════════════════════════════════════════════
#  SOURCE 1: DEXSCREENER — Hot Pairs (All Chains)
# ═══════════════════════════════════════════════════════════

def fetch_dexscreener_hot_pairs(chain: str = None, limit: int = 20) -> List[Dict]:
    """Fetch hottest trading pairs from DexScreener."""
    tokens = []
    try:
        if chain and chain in CHAINS:
            # Specific chain
            data = _get(f"{DEXSCREENER_BASE}/pairs/{CHAINS[chain]['dexscreener']}")
        else:
            # Use search for trending
            data = _get("https://api.dexscreener.com/token-boosts/top/v1")
        
        pairs = data if isinstance(data, list) else data.get("pairs", [])
        
        for p in pairs[:limit]:
            if isinstance(p, dict):
                base = p.get("baseToken", p) if "baseToken" in p else p
                token = _parse_dexscreener_pair(p)
                if token:
                    tokens.append(token)
    except Exception as e:
        logger.error(f"[DEXTOOLS] DexScreener hot pairs error: {e}")
    return tokens


def fetch_dexscreener_new_pairs(limit: int = 20) -> List[Dict]:
    """Fetch brand new live pairs from DexScreener — equivalent to dextools.io/live-new-pairs."""
    tokens = []
    try:
        data = _get("https://api.dexscreener.com/token-profiles/latest/v1")
        profiles = data if isinstance(data, list) else []
        
        for p in profiles[:limit * 2]:
            if not isinstance(p, dict):
                continue
            chain_id = p.get("chainId", "")
            token_addr = p.get("tokenAddress", "")
            if not token_addr:
                continue
            
            # Get full pair data
            pair_data = _get(f"{DEXSCREENER_BASE}/tokens/{token_addr}")
            pairs = pair_data.get("pairs", []) if pair_data else []
            
            if pairs:
                token = _parse_dexscreener_pair(pairs[0])
                if token:
                    token["is_new"] = True
                    token["source"] = "dexscreener_new"
                    tokens.append(token)
            
            if len(tokens) >= limit:
                break
            time.sleep(0.3)  # Rate limit
    except Exception as e:
        logger.error(f"[DEXTOOLS] DexScreener new pairs error: {e}")
    return tokens


def _parse_dexscreener_pair(pair: dict) -> Optional[Dict]:
    """Parse a single DexScreener pair into standard format."""
    try:
        base = pair.get("baseToken", {})
        if not base:
            return None
        
        price_usd = _safe_float(pair.get("priceUsd", 0))
        price_change_5m = _safe_float(pair.get("priceChange", {}).get("m5", 0))
        price_change_1h = _safe_float(pair.get("priceChange", {}).get("h1", 0))
        price_change_6h = _safe_float(pair.get("priceChange", {}).get("h6", 0))
        price_change_24h = _safe_float(pair.get("priceChange", {}).get("h24", 0))
        volume_24h = _safe_float(pair.get("volume", {}).get("h24", 0))
        liquidity = _safe_float(pair.get("liquidity", {}).get("usd", 0))
        mcap = _safe_float(pair.get("marketCap", 0)) or _safe_float(pair.get("fdv", 0))
        
        txns = pair.get("txns", {})
        buys_24h = int(txns.get("h24", {}).get("buys", 0) or 0)
        sells_24h = int(txns.get("h24", {}).get("sells", 0) or 0)
        buys_1h = int(txns.get("h1", {}).get("buys", 0) or 0)
        sells_1h = int(txns.get("h1", {}).get("sells", 0) or 0)
        
        chain_id = pair.get("chainId", "unknown")
        chain_info = None
        for k, v in CHAINS.items():
            if v.get("dexscreener") == chain_id:
                chain_info = v
                break
        
        pair_addr = pair.get("pairAddress", "")
        token_addr = base.get("address", "")
        
        return {
            "name": base.get("name", "Unknown"),
            "symbol": base.get("symbol", "???"),
            "address": token_addr,
            "pair_address": pair_addr,
            "chain": chain_id,
            "chain_emoji": chain_info["emoji"] if chain_info else "🔗",
            "chain_symbol": chain_info["symbol"] if chain_info else chain_id.upper(),
            "price_usd": price_usd,
            "price_change_5m": price_change_5m,
            "price_change_1h": price_change_1h,
            "price_change_6h": price_change_6h,
            "price_change_24h": price_change_24h,
            "volume_24h": volume_24h,
            "liquidity": liquidity,
            "market_cap": mcap,
            "buys_24h": buys_24h,
            "sells_24h": sells_24h,
            "buys_1h": buys_1h,
            "sells_1h": sells_1h,
            "buy_sell_ratio": round(buys_1h / max(sells_1h, 1), 2),
            "dex": pair.get("dexId", "unknown"),
            "pair_created": pair.get("pairCreatedAt", ""),
            "source": "dexscreener",
            "is_new": False,
            "dextools_url": f"{DEXTOOLS_WEB}/{chain_info['dextools'] if chain_info else chain_id}/pair-explorer/{pair_addr}" if pair_addr else "",
            "dexscreener_url": f"{DEXSCREENER_WEB}/{chain_id}/{pair_addr}" if pair_addr else "",
        }
    except Exception as e:
        logger.debug(f"[DEXTOOLS] Parse pair error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  SOURCE 2: COINGECKO TRENDING — Viral Tokens
# ═══════════════════════════════════════════════════════════

def fetch_coingecko_trending(limit: int = 15) -> List[Dict]:
    """Fetch top trending tokens from CoinGecko."""
    tokens = []
    try:
        data = _get(f"{COINGECKO_BASE}/search/trending")
        coins = data.get("coins", [])
        
        for item in coins[:limit]:
            coin = item.get("item", {})
            token = {
                "name": coin.get("name", "Unknown"),
                "symbol": coin.get("symbol", "???").upper(),
                "address": coin.get("id", ""),
                "pair_address": "",
                "chain": "multi",
                "chain_emoji": "🌐",
                "chain_symbol": "MULTI",
                "price_usd": _safe_float(coin.get("data", {}).get("price", 0)),
                "price_change_24h": _safe_float(coin.get("data", {}).get("price_change_percentage_24h", {}).get("usd", 0) if isinstance(coin.get("data", {}).get("price_change_percentage_24h"), dict) else coin.get("data", {}).get("price_change_percentage_24h", 0)),
                "price_change_5m": 0,
                "price_change_1h": 0,
                "price_change_6h": 0,
                "volume_24h": _safe_float(coin.get("data", {}).get("total_volume", 0)),
                "liquidity": 0,
                "market_cap": _safe_float(coin.get("data", {}).get("market_cap", 0)),
                "buys_24h": 0, "sells_24h": 0, "buys_1h": 0, "sells_1h": 0,
                "buy_sell_ratio": 0,
                "dex": "coingecko",
                "source": "coingecko_trending",
                "is_new": False,
                "market_cap_rank": coin.get("market_cap_rank", 999),
                "coingecko_score": coin.get("score", 0),
                "dextools_url": "",
                "dexscreener_url": "",
                "thumb": coin.get("thumb", ""),
            }
            tokens.append(token)
    except Exception as e:
        logger.error(f"[DEXTOOLS] CoinGecko trending error: {e}")
    return tokens


# ═══════════════════════════════════════════════════════════
#  SOURCE 3: MEME BOARD — Top Meme Coins
# ═══════════════════════════════════════════════════════════

def fetch_meme_board(limit: int = 15) -> List[Dict]:
    """Fetch top meme coins — equivalent to dextools.io/meme-board."""
    tokens = []
    try:
        # CoinGecko meme category
        data = _get(f"{COINGECKO_BASE}/coins/markets", params={
            "vs_currency": "usd",
            "category": "meme-token",
            "order": "volume_desc",
            "per_page": str(limit),
            "page": "1",
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d",
        })
        
        if isinstance(data, list):
            for coin in data:
                token = {
                    "name": coin.get("name", "Unknown"),
                    "symbol": coin.get("symbol", "???").upper(),
                    "address": coin.get("id", ""),
                    "pair_address": "",
                    "chain": "multi",
                    "chain_emoji": "🐸",
                    "chain_symbol": "MEME",
                    "price_usd": _safe_float(coin.get("current_price", 0)),
                    "price_change_1h": _safe_float(coin.get("price_change_percentage_1h_in_currency", 0)),
                    "price_change_24h": _safe_float(coin.get("price_change_percentage_24h", 0)),
                    "price_change_5m": 0,
                    "price_change_6h": 0,
                    "volume_24h": _safe_float(coin.get("total_volume", 0)),
                    "liquidity": 0,
                    "market_cap": _safe_float(coin.get("market_cap", 0)),
                    "buys_24h": 0, "sells_24h": 0, "buys_1h": 0, "sells_1h": 0,
                    "buy_sell_ratio": 0,
                    "dex": "coingecko",
                    "source": "meme_board",
                    "is_new": False,
                    "ath_change": _safe_float(coin.get("ath_change_percentage", 0)),
                    "dextools_url": "",
                    "dexscreener_url": "",
                }
                tokens.append(token)
    except Exception as e:
        logger.error(f"[DEXTOOLS] Meme board error: {e}")
    
    # Also try DexScreener search for "meme"
    try:
        data = _get(f"{DEXSCREENER_BASE}/search?q=meme")
        pairs = data.get("pairs", [])[:10]
        for p in pairs:
            token = _parse_dexscreener_pair(p)
            if token:
                token["source"] = "meme_board"
                token["chain_emoji"] = "🐸"
                tokens.append(token)
    except:
        pass
    
    return tokens[:limit]


# ═══════════════════════════════════════════════════════════
#  SOURCE 4: DEXTOOLS API — Direct (if API key available)
# ═══════════════════════════════════════════════════════════

def fetch_dextools_hot(chain: str = "ether", limit: int = 15) -> List[Dict]:
    """Fetch hot pairs from DexTools API directly."""
    tokens = []
    if not DEXTOOLS_API_KEY:
        return tokens
    
    try:
        data = _get(
            f"{DEXTOOLS_BASE}/ranking/{chain}/hotpools",
            headers=_dextools_headers(),
        )
        results = data.get("data", {}).get("results", []) if data else []
        
        for item in results[:limit]:
            main_token = item.get("mainToken", {})
            token = {
                "name": main_token.get("name", "Unknown"),
                "symbol": main_token.get("symbol", "???"),
                "address": main_token.get("address", ""),
                "pair_address": item.get("address", ""),
                "chain": chain,
                "chain_emoji": CHAINS.get(chain, {}).get("emoji", "🔗"),
                "chain_symbol": CHAINS.get(chain, {}).get("symbol", chain.upper()),
                "price_usd": float(item.get("price", 0) or 0),
                "price_change_24h": float(item.get("variation24h", 0) or 0),
                "price_change_5m": 0, "price_change_1h": 0, "price_change_6h": 0,
                "volume_24h": float(item.get("volume24h", 0) or 0),
                "liquidity": float(item.get("liquidity", 0) or 0),
                "market_cap": 0,
                "buys_24h": 0, "sells_24h": 0, "buys_1h": 0, "sells_1h": 0,
                "buy_sell_ratio": 0,
                "dex": item.get("exchange", ""),
                "source": "dextools_api",
                "is_new": False,
                "dextools_url": f"{DEXTOOLS_WEB}/{chain}/pair-explorer/{item.get('address', '')}",
                "dexscreener_url": "",
            }
            tokens.append(token)
    except Exception as e:
        logger.error(f"[DEXTOOLS] DexTools API error: {e}")
    return tokens


# ═══════════════════════════════════════════════════════════
#  SOURCE 5: DEXTOOLS AIRDROPS (via DeFi Llama + aggregators)
# ═══════════════════════════════════════════════════════════

def fetch_dextools_airdrops(limit: int = 10) -> List[Dict]:
    """Fetch airdrop opportunities — equivalent to dextools.io/airdrops."""
    airdrops = []
    
    # Source: DeFi Llama protocols with no token yet
    try:
        data = _get("https://api.llama.fi/protocols")
        if isinstance(data, list):
            no_token = [
                p for p in data 
                if not p.get("symbol") and float(p.get("tvl", 0) or 0) > 10_000_000
            ]
            no_token.sort(key=lambda x: float(x.get("tvl", 0) or 0), reverse=True)
            
            for p in no_token[:limit]:
                airdrops.append({
                    "name": p.get("name", "Unknown"),
                    "category": p.get("category", "DeFi"),
                    "tvl": float(p.get("tvl", 0) or 0),
                    "chains": p.get("chains", []),
                    "url": p.get("url", ""),
                    "description": f"TVL ${float(p.get('tvl', 0) or 0) / 1e6:.1f}M — No token yet, potential airdrop",
                    "source": "defillama",
                })
    except Exception as e:
        logger.error(f"[DEXTOOLS] Airdrop scan error: {e}")
    
    return airdrops


# ═══════════════════════════════════════════════════════════
#  MASTER SCAN — All sources combined
# ═══════════════════════════════════════════════════════════

def scan_all_tokens(limit: int = 15, include_memes: bool = True) -> List[Dict]:
    """
    Master scan: combines all DexScreener + CoinGecko + DexTools sources.
    Returns top tokens sorted by combined score.
    """
    all_tokens = []
    
    # Source 1: DexScreener hot boosted tokens
    try:
        hot = fetch_dexscreener_hot_pairs(limit=20)
        all_tokens.extend(hot)
        logger.info(f"[DEXTOOLS] Source 1 — DexScreener Hot: {len(hot)} tokens")
    except:
        pass
    
    # Source 2: DexScreener new pairs
    try:
        new = fetch_dexscreener_new_pairs(limit=10)
        all_tokens.extend(new)
        logger.info(f"[DEXTOOLS] Source 2 — New Pairs: {len(new)} tokens")
    except:
        pass
    
    # Source 3: CoinGecko trending
    try:
        trending = fetch_coingecko_trending(limit=15)
        all_tokens.extend(trending)
        logger.info(f"[DEXTOOLS] Source 3 — CoinGecko Trending: {len(trending)} tokens")
    except:
        pass
    
    # Source 4: Meme Board
    if include_memes:
        try:
            memes = fetch_meme_board(limit=10)
            all_tokens.extend(memes)
            logger.info(f"[DEXTOOLS] Source 4 — Meme Board: {len(memes)} tokens")
        except:
            pass
    
    # Source 5: DexTools API direct (if key available)
    if DEXTOOLS_API_KEY:
        for chain in ["ether", "solana", "bsc", "base"]:
            try:
                dex_hot = fetch_dextools_hot(chain=chain, limit=5)
                all_tokens.extend(dex_hot)
            except:
                pass
    
    # Deduplicate by symbol
    seen = set()
    unique_tokens = []
    for t in all_tokens:
        key = f"{t['symbol'].upper()}_{t.get('chain', '')}"
        if key not in seen:
            seen.add(key)
            unique_tokens.append(t)
    
    # Score and sort
    for t in unique_tokens:
        t["_score"] = _calculate_token_score(t)
    
    unique_tokens.sort(key=lambda x: x["_score"], reverse=True)
    return unique_tokens[:limit]


def _calculate_token_score(token: dict) -> float:
    """Calculate a composite score for ranking tokens."""
    score = 0
    
    # Volume score (higher is better)
    vol = token.get("volume_24h", 0)
    if vol > 10_000_000:
        score += 30
    elif vol > 1_000_000:
        score += 20
    elif vol > 100_000:
        score += 10
    elif vol > 10_000:
        score += 5
    
    # Price change momentum
    change_1h = abs(token.get("price_change_1h", 0))
    change_24h = abs(token.get("price_change_24h", 0))
    if change_1h > 20:
        score += 15
    elif change_1h > 10:
        score += 10
    elif change_1h > 5:
        score += 5
    
    if change_24h > 50:
        score += 20
    elif change_24h > 20:
        score += 10
    
    # Positive momentum bonus
    if token.get("price_change_1h", 0) > 0:
        score += 5
    if token.get("price_change_24h", 0) > 0:
        score += 5
    
    # Buy/sell ratio
    ratio = token.get("buy_sell_ratio", 0)
    if ratio > 2:
        score += 15
    elif ratio > 1.5:
        score += 10
    elif ratio > 1:
        score += 5
    
    # Liquidity 
    liq = token.get("liquidity", 0)
    if liq > 500_000:
        score += 10
    elif liq > 100_000:
        score += 7
    elif liq > 10_000:
        score += 3
    
    # New token bonus
    if token.get("is_new"):
        score += 10
    
    # Source bonus
    if token.get("source") == "dexscreener":
        score += 5
    if token.get("source") == "dextools_api":
        score += 8
    
    return score


# ═══════════════════════════════════════════════════════════
#  DEEP LINKS — Mobile App & Web
# ═══════════════════════════════════════════════════════════

def get_token_links(token: dict) -> Dict[str, str]:
    """Generate all possible links for a token including direct BUY/SWAP links."""
    chain = token.get("chain", "")
    pair_addr = token.get("pair_address", "")
    token_addr = token.get("address", "")
    
    links = {}
    
    # DexTools link
    chain_slug = None
    for k, v in CHAINS.items():
        if v.get("dexscreener") == chain or k == chain:
            chain_slug = v.get("dextools", chain)
            break
    
    if chain_slug and pair_addr:
        links["dextools"] = f"{DEXTOOLS_WEB}/{chain_slug}/pair-explorer/{pair_addr}"
    elif chain_slug and token_addr:
        links["dextools"] = f"{DEXTOOLS_WEB}/{chain_slug}/token/{token_addr}"
    
    # DexScreener link
    if chain and pair_addr:
        links["dexscreener"] = f"{DEXSCREENER_WEB}/{chain}/{pair_addr}"
    
    # CoinGecko link
    cg_id = token.get("address", "")
    if token.get("source") in ("coingecko_trending", "meme_board") and cg_id:
        links["coingecko"] = f"https://www.coingecko.com/en/coins/{cg_id}"
    
    # Birdeye (Solana)
    if chain == "solana" and token_addr:
        links["birdeye"] = f"https://birdeye.so/token/{token_addr}?chain=solana"
    
    # ═══════════════════════════════════════════
    #  🛒 DIRECT BUY / SWAP LINKS (Mobile Deep Links)
    # ═══════════════════════════════════════════
    if token_addr:
        # --- Solana chain ---
        if chain in ("solana", "sol"):
            # Jupiter Aggregator (best Solana DEX) — opens in Phantom browser too
            links["buy_jupiter"] = f"https://jup.ag/swap/SOL-{token_addr}"
            # Raydium
            links["buy_raydium"] = f"https://raydium.io/swap/?inputMint=sol&outputMint={token_addr}"
            # Phantom deep link (universal swap)
            links["buy_phantom"] = f"https://phantom.app/ul/swap/SOL-{token_addr}"
        
        # --- Ethereum chain ---
        elif chain in ("ethereum", "eth"):
            # Uniswap (universal link — works on mobile app)
            links["buy_uniswap"] = f"https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=ethereum"
            # 1inch (best price aggregator)
            links["buy_1inch"] = f"https://app.1inch.io/#/1/simple/swap/ETH/{token_addr}"
        
        # --- BSC chain ---
        elif chain in ("bsc", "bnb"):
            # PancakeSwap
            links["buy_pancakeswap"] = f"https://pancakeswap.finance/swap?outputCurrency={token_addr}&chainId=56"
            # 1inch BSC
            links["buy_1inch"] = f"https://app.1inch.io/#/56/simple/swap/BNB/{token_addr}"
        
        # --- Arbitrum ---
        elif chain in ("arbitrum", "arb"):
            links["buy_uniswap"] = f"https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=arbitrum"
            links["buy_1inch"] = f"https://app.1inch.io/#/42161/simple/swap/ETH/{token_addr}"
        
        # --- Base chain ---
        elif chain in ("base",):
            links["buy_uniswap"] = f"https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=base"
            links["buy_aerodrome"] = f"https://aerodrome.finance/swap?to={token_addr}"
        
        # --- Polygon ---
        elif chain in ("polygon", "matic"):
            links["buy_uniswap"] = f"https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=polygon"
            links["buy_quickswap"] = f"https://quickswap.exchange/#/swap?outputCurrency={token_addr}"
        
        # --- Avalanche ---
        elif chain in ("avalanche", "avax"):
            links["buy_traderjoe"] = f"https://traderjoexyz.com/avalanche/trade?outputCurrency={token_addr}"
    
    return links


# ═══════════════════════════════════════════════════════════
#  FORMAT — Telegram output
# ═══════════════════════════════════════════════════════════

def format_top_tokens(tokens: List[Dict], title: str = "🔥 TOP 15 TOKENS") -> str:
    """Format top tokens for Telegram with deep links."""
    if not tokens:
        return "❌ No tokens found at the moment."
    
    lines = [
        f"🔥🧠 *{title}*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"_Real-time multi-chain scan — {datetime.now().strftime('%I:%M %p IST')}_\n",
    ]
    
    for i, t in enumerate(tokens[:15], 1):
        emoji = "🟢" if t.get("price_change_1h", 0) > 0 else "🔴" if t.get("price_change_1h", 0) < 0 else "⚪"
        chain_em = t.get("chain_emoji", "🔗")
        
        # Signal
        signal_data = t.get("_signal", {})
        signal_emoji = signal_data.get("emoji", "")
        signal_text = signal_data.get("signal", "")
        
        price_str = _format_price(t.get("price_usd", 0))
        vol_str = _format_volume(t.get("volume_24h", 0))
        mcap_str = _format_volume(t.get("market_cap", 0))
        
        change_1h = t.get("price_change_1h", 0)
        change_24h = t.get("price_change_24h", 0)
        
        # Deep links
        links = get_token_links(t)
        link_parts = []
        if links.get("dextools"):
            link_parts.append(f"[DexTools]({links['dextools']})")
        if links.get("dexscreener"):
            link_parts.append(f"[DexScreener]({links['dexscreener']})")
        if links.get("birdeye"):
            link_parts.append(f"[Birdeye]({links['birdeye']})")
        if links.get("coingecko"):
            link_parts.append(f"[CoinGecko]({links['coingecko']})")
        link_str = " | ".join(link_parts) if link_parts else ""
        
        # New badge
        new_badge = " 🆕" if t.get("is_new") else ""
        
        lines.append(f"*{i}. {chain_em} {t['symbol']}{new_badge}* — {t['name']}")
        lines.append(f"   💰 `{price_str}` | MCap: {mcap_str}")
        lines.append(f"   {emoji} 1h: `{change_1h:+.1f}%` | 24h: `{change_24h:+.1f}%`")
        lines.append(f"   📊 Vol: {vol_str} | Liq: {_format_volume(t.get('liquidity', 0))}")
        
        if t.get("buy_sell_ratio", 0) > 0:
            ratio = t["buy_sell_ratio"]
            ratio_emoji = "🟢" if ratio > 1.5 else "🟡" if ratio > 1 else "🔴"
            lines.append(f"   {ratio_emoji} Buy/Sell: {ratio}x")
        
        if signal_text:
            lines.append(f"   {signal_emoji} *Signal: {signal_text}*")
        
        if link_str:
            lines.append(f"   🔗 {link_str}")
        
        # 🛒 Direct BUY links (mobile-friendly)
        buy_parts = []
        if links.get("buy_jupiter"):
            buy_parts.append(f"[Jupiter]({links['buy_jupiter']})")
        if links.get("buy_raydium"):
            buy_parts.append(f"[Raydium]({links['buy_raydium']})")
        if links.get("buy_phantom"):
            buy_parts.append(f"[Phantom]({links['buy_phantom']})")
        if links.get("buy_uniswap"):
            buy_parts.append(f"[Uniswap]({links['buy_uniswap']})")
        if links.get("buy_pancakeswap"):
            buy_parts.append(f"[PancakeSwap]({links['buy_pancakeswap']})")
        if links.get("buy_1inch"):
            buy_parts.append(f"[1inch]({links['buy_1inch']})")
        if links.get("buy_aerodrome"):
            buy_parts.append(f"[Aerodrome]({links['buy_aerodrome']})")
        if links.get("buy_quickswap"):
            buy_parts.append(f"[QuickSwap]({links['buy_quickswap']})")
        if links.get("buy_traderjoe"):
            buy_parts.append(f"[TraderJoe]({links['buy_traderjoe']})")
        
        if buy_parts:
            buy_str = " | ".join(buy_parts)
            lines.append(f"   🛒 *BUY:* {buy_str}")
        
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("_🤖 JARVIS AI — Multi-Chain Intelligence_")
    
    return "\n".join(lines)


def format_meme_board(tokens: List[Dict]) -> str:
    """Format meme board tokens."""
    return format_top_tokens(tokens, title="🐸 MEME BOARD — Top Meme Coins")


def format_new_pairs(tokens: List[Dict]) -> str:
    """Format new pairs."""
    return format_top_tokens(tokens, title="🆕 LIVE NEW PAIRS — Just Launched")


def format_airdrops(airdrops: List[Dict]) -> str:
    """Format DexTools-style airdrops."""
    if not airdrops:
        return "❌ No airdrop opportunities found."
    
    lines = [
        "🎁🔥 *DEXTOOLS AIRDROPS*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"_High-TVL protocols without tokens — potential airdrops_\n",
    ]
    
    for i, a in enumerate(airdrops, 1):
        tvl = a.get("tvl", 0)
        chains = ", ".join(a.get("chains", [])[:3])
        lines.append(f"*{i}. {a['name']}* — {a.get('category', 'DeFi')}")
        lines.append(f"   💰 TVL: ${tvl / 1e6:.1f}M | Chains: {chains}")
        if a.get("url"):
            lines.append(f"   🔗 [Visit]({a['url']})")
        lines.append(f"   💡 _{a.get('description', '')}_")
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚠️ _DYOR — Not financial advice_")
    
    return "\n".join(lines)


def format_voice_summary(tokens: List[Dict]) -> str:
    """Generate voice-friendly summary for top tokens."""
    if not tokens:
        return "Abhi koi hot token nahi mila boss."
    
    parts = ["Boss, top tokens ka update suniye. "]
    
    for i, t in enumerate(tokens[:5], 1):
        name = t.get("symbol", "unknown")
        price = t.get("price_usd", 0)
        change = t.get("price_change_1h", 0)
        
        direction = "upar" if change > 0 else "neeche" if change < 0 else "stable"
        
        signal_data = t.get("_signal", {})
        signal = signal_data.get("signal", "")
        
        parts.append(
            f"Number {i}, {name}, price {_format_price(price)}, "
            f"last 1 hour mein {abs(change):.1f} percent {direction}. "
        )
        if signal:
            parts.append(f"AI signal: {signal}. ")
    
    parts.append("Yeh the top trending tokens boss. Koi aur chahiye toh bataiye!")
    return "".join(parts)


def _format_price(price: float) -> str:
    """Format price for display."""
    if price == 0:
        return "$0"
    if price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.0001:
        return f"${price:.6f}"
    else:
        return f"${price:.10f}"


def _format_volume(vol: float) -> str:
    """Format volume/mcap for display."""
    if vol >= 1e9:
        return f"${vol / 1e9:.1f}B"
    elif vol >= 1e6:
        return f"${vol / 1e6:.1f}M"
    elif vol >= 1e3:
        return f"${vol / 1e3:.1f}K"
    elif vol > 0:
        return f"${vol:.0f}"
    return "$0"


# ═══════════════════════════════════════════════════════════
#  BACKGROUND SCANNER — Real-time alerts
# ═══════════════════════════════════════════════════════════

def set_alert_callback(callback):
    """Set the callback function for sending alerts."""
    global _alert_callback
    _alert_callback = callback
    logger.info("[DEXTOOLS] Alert callback set")


def _scan_loop():
    """Background scanner: check for big movers and new launches."""
    global _dextools_running
    logger.info("[DEXTOOLS] 🔥 Background scanner STARTED — scanning every 3 min")
    
    time.sleep(30)  # Wait for boot
    
    while _dextools_running:
        try:
            # Scan hot pairs
            tokens = scan_all_tokens(limit=15, include_memes=True)
            
            # Check for alert-worthy tokens
            for t in tokens:
                token_key = f"{t['symbol']}_{t.get('chain', '')}"
                
                # Skip already alerted (within 1 hour)
                if token_key in _alerted_tokens:
                    if time.time() - _alerted_tokens[token_key] < 3600:
                        continue
                
                # Alert on: big pump (>30% 1h), high buy/sell ratio (>3), or new + volume
                change_1h = abs(t.get("price_change_1h", 0))
                ratio = t.get("buy_sell_ratio", 0)
                is_new = t.get("is_new", False)
                vol = t.get("volume_24h", 0)
                
                should_alert = False
                alert_reason = ""
                
                if change_1h > 30:
                    should_alert = True
                    alert_reason = f"💥 {change_1h:.0f}% pump in 1 hour!"
                elif ratio > 3 and vol > 50_000:
                    should_alert = True
                    alert_reason = f"🐋 Extreme buy pressure: {ratio}x ratio"
                elif is_new and vol > 100_000:
                    should_alert = True
                    alert_reason = f"🆕 New launch with ${vol/1000:.0f}K volume!"
                
                if should_alert and _alert_callback:
                    _alerted_tokens[token_key] = time.time()
                    
                    links = get_token_links(t)
                    link_str = ""
                    if links.get("dextools"):
                        link_str = f"[📊 DexTools]({links['dextools']})"
                    elif links.get("dexscreener"):
                        link_str = f"[📊 DexScreener]({links['dexscreener']})"
                    
                    # Ultra AI Prediction for alerts
                    ultra_text = ""
                    try:
                        from jarvis_ultra_ai import ultra_predict
                        pred = ultra_predict(t)
                        verdict = pred.get("verdict", {})
                        rug = pred.get("rug_risk", {})
                        health = pred.get("health", {})
                        targets = pred.get("targets", {})
                        
                        ultra_text = (
                            f"\n🧠 *ULTRA AI VERDICT:*\n"
                            f"{verdict.get('emoji', '⚪')} *{verdict.get('action', '?')}* — "
                            f"🇮🇳 _{verdict.get('hindi_action', '')}_\n"
                            f"📊 Score: {verdict.get('score', 50):.0f}/100\n"
                            f"🛡️ Rug Risk: {rug.get('emoji', '⚪')} {rug.get('level', '?')}\n"
                            f"💎 Health: {health.get('emoji', '⚪')} {health.get('grade', '?')}\n"
                        )
                        
                        if targets.get("support", 0) > 0:
                            ultra_text += (
                                f"🎯 Target: `{targets.get('resistance', 0):.8f}` | "
                                f"R:R = {targets.get('rr_ratio', 0):.1f}x\n"
                            )
                    except Exception:
                        pass
                    
                    alert_msg = (
                        f"🚨🔥 *JARVIS TOKEN ALERT!*\n\n"
                        f"{t.get('chain_emoji', '🔗')} *{t['symbol']}* — {t['name']}\n"
                        f"💰 Price: `{_format_price(t.get('price_usd', 0))}`\n"
                        f"📈 1h: `{t.get('price_change_1h', 0):+.1f}%` | 24h: `{t.get('price_change_24h', 0):+.1f}%`\n"
                        f"📊 Vol: {_format_volume(t.get('volume_24h', 0))}\n\n"
                        f"⚡ {alert_reason}\n"
                        f"{ultra_text}\n"
                        f"{link_str}\n"
                        f"_⚠️ DYOR — Not financial advice_"
                    )
                    
                    try:
                        _alert_callback(None, alert_msg)  # None = send to owner
                    except Exception as e:
                        logger.error(f"[DEXTOOLS] Alert callback error: {e}")
            
            # Clean old alerts (>2 hours)
            cutoff = time.time() - 7200
            expired = [k for k, v in _alerted_tokens.items() if v < cutoff]
            for k in expired:
                del _alerted_tokens[k]
        
        except Exception as e:
            logger.error(f"[DEXTOOLS] Scan loop error: {e}")
        
        # Sleep in small increments
        for _ in range(_scan_interval):
            if not _dextools_running:
                break
            time.sleep(1)


def start_dextools_scanner():
    """Start the background DexTools scanner."""
    global _dextools_running
    if _dextools_running:
        return
    _dextools_running = True
    t = threading.Thread(target=_scan_loop, daemon=True, name="DexToolsScanner")
    t.start()
    logger.info("[DEXTOOLS] 🔥 DexTools Scanner LAUNCHED!")


def stop_dextools_scanner():
    """Stop the background scanner."""
    global _dextools_running
    _dextools_running = False


# ═══════════════════════════════════════════════════════════
#  ONE-CALL FUNCTIONS — For telegram_bot.py
# ═══════════════════════════════════════════════════════════

def dextools_top15() -> str:
    """One call: get formatted top 15 tokens."""
    tokens = scan_all_tokens(limit=15)
    # Add AI signals
    for t in tokens:
        t["_signal"] = generate_signal(t)
    return format_top_tokens(tokens)

def dextools_meme_board() -> str:
    """One call: get formatted meme board."""
    tokens = fetch_meme_board(limit=15)
    for t in tokens:
        t["_signal"] = generate_signal(t)
    return format_meme_board(tokens)

def dextools_new_pairs() -> str:
    """One call: get formatted new pairs."""
    tokens = fetch_dexscreener_new_pairs(limit=15)
    for t in tokens:
        t["_signal"] = generate_signal(t)
    return format_new_pairs(tokens)

def dextools_airdrops() -> str:
    """One call: get formatted airdrops."""
    airdrops = fetch_dextools_airdrops(limit=10)
    return format_airdrops(airdrops)

def dextools_voice() -> str:
    """One call: get voice summary of top tokens."""
    tokens = scan_all_tokens(limit=5)
    for t in tokens:
        t["_signal"] = generate_signal(t)
    return format_voice_summary(tokens)


# ═══════════════════════════════════════════════════════════
#  AI/ML BUY/SELL SIGNALS — Technical Analysis Engine
# ═══════════════════════════════════════════════════════════

def generate_signal(token: dict) -> Dict[str, str]:
    """
    Generate AI buy/sell signal for a token using multi-indicator analysis.
    Uses: RSI approximation, Volume profile, Momentum, Buy/Sell ratio, 
    Trend strength, Liquidity analysis.
    """
    signals = []
    weights = []
    
    # --- Indicator 1: Momentum (1h change) ---
    change_1h = token.get("price_change_1h", 0)
    if change_1h > 20:
        signals.append(("STRONG BUY", 0.9))
        weights.append(2)
    elif change_1h > 10:
        signals.append(("BUY", 0.7))
        weights.append(2)
    elif change_1h > 3:
        signals.append(("BUY", 0.6))
        weights.append(1.5)
    elif change_1h < -20:
        signals.append(("STRONG SELL", 0.9))
        weights.append(2)
    elif change_1h < -10:
        signals.append(("SELL", 0.7))
        weights.append(2)
    elif change_1h < -3:
        signals.append(("SELL", 0.6))
        weights.append(1.5)
    else:
        signals.append(("HOLD", 0.5))
        weights.append(1)
    
    # --- Indicator 2: RSI Approximation (from 5m + 1h + 24h changes) ---
    change_5m = token.get("price_change_5m", 0)
    change_24h = token.get("price_change_24h", 0)
    # Approximate RSI: if all timeframes positive = overbought, all negative = oversold
    positive_count = sum(1 for c in [change_5m, change_1h, change_24h] if c > 0)
    negative_count = sum(1 for c in [change_5m, change_1h, change_24h] if c < 0)
    
    if positive_count == 3 and change_1h > 15:
        signals.append(("OVERBOUGHT", 0.3))  # Caution
        weights.append(1.5)
    elif negative_count == 3 and change_1h < -15:
        signals.append(("OVERSOLD BUY", 0.8))  # Bounce opportunity
        weights.append(1.5)
    elif positive_count >= 2:
        signals.append(("BULLISH", 0.7))
        weights.append(1)
    elif negative_count >= 2:
        signals.append(("BEARISH", 0.3))
        weights.append(1)
    else:
        signals.append(("NEUTRAL", 0.5))
        weights.append(0.5)
    
    # --- Indicator 3: Buy/Sell Ratio ---
    ratio = token.get("buy_sell_ratio", 0)
    if ratio > 3:
        signals.append(("STRONG BUY", 0.95))
        weights.append(2.5)
    elif ratio > 2:
        signals.append(("BUY", 0.8))
        weights.append(2)
    elif ratio > 1.3:
        signals.append(("BUY", 0.65))
        weights.append(1.5)
    elif ratio > 0 and ratio < 0.5:
        signals.append(("STRONG SELL", 0.9))
        weights.append(2.5)
    elif ratio > 0 and ratio < 0.7:
        signals.append(("SELL", 0.7))
        weights.append(2)
    else:
        signals.append(("NEUTRAL", 0.5))
        weights.append(0.5)
    
    # --- Indicator 4: Volume Profile ---
    vol = token.get("volume_24h", 0)
    liq = token.get("liquidity", 0)
    mcap = token.get("market_cap", 0)
    
    # Volume/MCap ratio (higher = more interest)
    if mcap > 0:
        vol_mcap = vol / mcap
        if vol_mcap > 0.5:
            signals.append(("HIGH INTEREST", 0.75))
            weights.append(1.5)
        elif vol_mcap > 0.2:
            signals.append(("MODERATE", 0.6))
            weights.append(1)
    
    # Liquidity check
    if liq > 0 and vol > 0:
        vol_liq = vol / liq
        if vol_liq > 5:
            signals.append(("CAUTION HIGH VOL/LIQ", 0.4))
            weights.append(1)
    
    # --- Indicator 5: Trend Strength ---
    change_6h = token.get("price_change_6h", 0)
    if change_1h > 0 and change_6h > 0 and change_24h > 0:
        signals.append(("STRONG UPTREND", 0.85))
        weights.append(2)
    elif change_1h < 0 and change_6h < 0 and change_24h < 0:
        signals.append(("STRONG DOWNTREND", 0.15))
        weights.append(2)
    
    # --- Indicator 6: New Token Detection ---
    if token.get("is_new"):
        if vol > 100_000 and ratio > 1.5:
            signals.append(("NEW GEM BUY", 0.8))
            weights.append(1.5)
        else:
            signals.append(("NEW RISKY", 0.4))
            weights.append(1)
    
    # --- Composite Score ---
    if not signals:
        return {"signal": "NEUTRAL", "confidence": 0.5, "emoji": "⚪"}
    
    total_weight = sum(weights)
    weighted_score = sum(s[1] * w for (s, w) in zip(signals, weights)) / total_weight if total_weight > 0 else 0.5
    
    # Determine final signal
    if weighted_score >= 0.8:
        final = "🟢 STRONG BUY"
        emoji = "🟢"
    elif weighted_score >= 0.65:
        final = "🟢 BUY"
        emoji = "🟢"
    elif weighted_score >= 0.55:
        final = "🟡 HOLD"
        emoji = "🟡"
    elif weighted_score >= 0.4:
        final = "🟡 CAUTION"
        emoji = "🟡"
    elif weighted_score >= 0.25:
        final = "🔴 SELL"
        emoji = "🔴"
    else:
        final = "🔴 STRONG SELL"
        emoji = "🔴"
    
    confidence = min(weighted_score * 100, 99)
    
    return {
        "signal": final,
        "confidence": round(confidence, 1),
        "emoji": emoji,
        "score": round(weighted_score, 3),
        "indicators": len(signals),
    }


# ═══════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'scan_all_tokens', 'fetch_dexscreener_hot_pairs', 'fetch_dexscreener_new_pairs',
    'fetch_coingecko_trending', 'fetch_meme_board', 'fetch_dextools_hot',
    'fetch_dextools_airdrops', 'generate_signal', 'get_token_links',
    'format_top_tokens', 'format_meme_board', 'format_new_pairs',
    'format_airdrops', 'format_voice_summary',
    'dextools_top15', 'dextools_meme_board', 'dextools_new_pairs',
    'dextools_airdrops', 'dextools_voice',
    'start_dextools_scanner', 'stop_dextools_scanner', 'set_alert_callback',
]
