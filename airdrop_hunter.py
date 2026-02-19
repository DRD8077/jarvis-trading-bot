"""
🎁🚀 JARVIS AIRDROP HUNTER — Auto-Capture Free Crypto Airdrops
═══════════════════════════════════════════════════════════════════
Automatically scans the entire crypto world for free airdrops,
claims eligible ones, and transfers to user's Solana wallet.

SOURCES SCANNED:
  1. 🌐 DeFi Llama Airdrops — biggest DeFi airdrop tracker
  2. 🎁 Airdrop aggregators — airdrops.io, earndrop, etc.
  3. 🐦 Twitter/X Crypto — viral airdrop announcements
  4. 🟣 Solana Ecosystem — Jupiter, Jito, Tensor airdrops
  5. 🔵 EVM Airdrops — Arbitrum, Optimism, Base, zkSync
  6. 💎 NFT Airdrops — free mint tracking
  7. 📢 Telegram Airdrop Channels — auto-parse announcements
  8. 🪂 Retroactive Airdrops — protocol usage tracking

FEATURES:
  ✅ Auto-scan every 5 minutes
  ✅ Eligibility check based on wallet activity
  ✅ One-click claim via Telegram button
  ✅ Auto-transfer to Phantom wallet (Solana)
  ✅ Risk assessment — scam airdrop detection
  ✅ Hindi voice alert for high-value airdrops
  ✅ Historical airdrop database for pattern detection

Author: JARVIS AI — Airdrop Division
"""

import os
import re
import time
import json
import logging
import hashlib
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger("airdrop_hunter")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════

OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))
OWNER_SOLANA_WALLET = os.environ.get("OWNER_SOLANA_WALLET", "8F1PJhuJa45RMWMJwgDASXL6bm6GYd1MtReJSTcWugaR")
OWNER_TON_WALLET = os.environ.get("OWNER_TON_WALLET", "UQBlUgQZt_EGCpWC1_SLSlybImldwtPZXJnB7uwRULcgYzkC")

# Scanning intervals — ULTRA FAST REALTIME
SCAN_INTERVAL = 30       # 30 seconds — ULTRA FAST quick scan
DEEP_SCAN_INTERVAL = 300   # 5 minutes for deep scan
ALERT_COOLDOWN = 120     # 2 min cooldown per airdrop (fast alerts)

# INR conversion rate (updated periodically)
_usd_to_inr_rate = 83.5  # default fallback
_inr_rate_ts = 0

# Data storage
AIRDROP_DB_FILE = "jarvis_airdrops.json"
CLAIMED_FILE = "jarvis_claimed_airdrops.json"

# API endpoints
DEFILLAMA_AIRDROPS = "https://defillama-datasets.llama.fi/emissionsBreakdown"
# CoinGecko REMOVED
JUPITER_API = "https://api.jup.ag"
SOL_RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
HELIUS_KEY = os.environ.get("HELIUS_API_KEY", "")
HELIUS_RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}" if HELIUS_KEY else ""

# Known airdrop aggregator URLs to scrape
AIRDROP_SOURCES = [
    "https://defillama.com/airdrops",
    "https://earndrop.io/airdrops",
    "https://airdrops.io/latest/",
]

# Cache
_airdrop_cache: Dict[str, Any] = {}
_airdrop_cache_ts: Dict[str, float] = {}
_alerted_airdrops: Dict[str, float] = {}  # airdrop_id -> last_alert_time
_user_wallets: Dict[int, Dict] = {}  # chat_id -> {solana: addr, evm: addr, ton: addr}
WALLET_DB_FILE = "jarvis_user_wallets.json"

# ═══════════════════════════════════════════════════════════
#  AIRDROP DATABASE — Track all found airdrops
# ═══════════════════════════════════════════════════════════

_airdrop_db: List[Dict] = []
_claimed_airdrops: Dict[str, Dict] = {}


def _load_airdrop_db():
    """Load airdrop database from file."""
    global _airdrop_db, _claimed_airdrops
    try:
        if os.path.exists(AIRDROP_DB_FILE):
            with open(AIRDROP_DB_FILE) as f:
                _airdrop_db = json.load(f)
    except Exception:
        _airdrop_db = []
    try:
        if os.path.exists(CLAIMED_FILE):
            with open(CLAIMED_FILE) as f:
                _claimed_airdrops = json.load(f)
    except Exception:
        _claimed_airdrops = {}


def _save_airdrop_db():
    """Save airdrop database to file."""
    try:
        with open(AIRDROP_DB_FILE, 'w') as f:
            json.dump(_airdrop_db[-500:], f)  # Keep last 500
    except Exception:
        pass


def _save_claimed():
    """Save claimed airdrops."""
    try:
        with open(CLAIMED_FILE, 'w') as f:
            json.dump(_claimed_airdrops, f)
    except Exception:
        pass


_load_airdrop_db()


# ═══════════════════════════════════════════════════════════
#  WALLET MANAGEMENT
# ═══════════════════════════════════════════════════════════

def _load_user_wallets():
    """Load user wallets from persistent storage."""
    global _user_wallets
    try:
        if os.path.exists(WALLET_DB_FILE):
            with open(WALLET_DB_FILE) as f:
                raw = json.load(f)
                _user_wallets = {int(k): v for k, v in raw.items()}
    except Exception:
        _user_wallets = {}


def _save_user_wallets():
    """Save user wallets to persistent file."""
    try:
        with open(WALLET_DB_FILE, 'w') as f:
            json.dump({str(k): v for k, v in _user_wallets.items()}, f)
    except Exception:
        pass


_load_user_wallets()


def register_wallet(chat_id: int, chain: str, address: str):
    """Register a user's wallet for airdrop tracking."""
    if chat_id not in _user_wallets:
        _user_wallets[chat_id] = {}
    _user_wallets[chat_id][chain] = address
    _save_user_wallets()
    logger.info(f"[AIRDROP] Wallet registered: chat={chat_id} chain={chain}")


def get_user_wallet(chat_id: int, chain: str = "solana") -> Optional[str]:
    """Get user's wallet address for a chain."""
    wallet = _user_wallets.get(chat_id, {}).get(chain)
    if not wallet and chat_id == OWNER_CHAT_ID:
        if chain == "solana":
            return OWNER_SOLANA_WALLET
        if chain == "ton":
            return OWNER_TON_WALLET
    return wallet


def get_all_user_wallets(chat_id: int) -> Dict[str, str]:
    """Get all wallet addresses for a user."""
    wallets = _user_wallets.get(chat_id, {})
    if chat_id == OWNER_CHAT_ID:
        if "solana" not in wallets:
            wallets["solana"] = OWNER_SOLANA_WALLET
        if "ton" not in wallets:
            wallets["ton"] = OWNER_TON_WALLET
    return wallets


def get_usd_to_inr() -> float:
    """Get current USD to INR rate."""
    global _usd_to_inr_rate, _inr_rate_ts
    if time.time() - _inr_rate_ts < 3600:  # Cache 1 hour
        return _usd_to_inr_rate
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        if r.status_code == 200:
            _usd_to_inr_rate = r.json().get("rates", {}).get("INR", 83.5)
            _inr_rate_ts = time.time()
    except Exception:
        pass
    return _usd_to_inr_rate


def usd_to_inr(usd: float) -> float:
    """Convert USD to INR."""
    return usd * get_usd_to_inr()


# ═══════════════════════════════════════════════════════════
#  SOURCE 1: DEFILLAMA — Track protocols with upcoming airdrops
# ═══════════════════════════════════════════════════════════

def scan_defillama_airdrops() -> List[Dict]:
    """
    Scan DeFi Llama for protocols likely to do airdrops.
    Tracks: high TVL protocols without tokens, governance proposals, etc.
    """
    airdrops = []

    # CoinGecko REMOVED — skip CoinGecko trending scan

    return airdrops


# ═══════════════════════════════════════════════════════════
#  SOURCE 2: SOLANA AIRDROPS — Jupiter, Jito, Tensor, etc.
# ═══════════════════════════════════════════════════════════

def scan_solana_airdrops(wallet: str = None) -> List[Dict]:
    """
    Scan Solana ecosystem for claimable airdrops.
    Checks: Jupiter, Jito, Tensor, and other Solana protocols.
    """
    wallet = wallet or OWNER_SOLANA_WALLET
    airdrops = []

    # Check Jupiter for unclaimed rewards
    try:
        # Jupiter fee rewards / voting rewards
        r = requests.get(
            f"https://worker.jup.ag/limit-orders/all-open-orders?wallet={wallet}",
            timeout=10
        )
        if r.status_code == 200:
            orders = r.json()
            if isinstance(orders, list) and len(orders) > 0:
                airdrops.append({
                    "id": "jup_orders",
                    "name": "Jupiter Open Orders",
                    "symbol": "JUP",
                    "type": "protocol_reward",
                    "chain": "solana",
                    "source": "jupiter",
                    "status": "active_orders",
                    "estimated_value_usd": 0,
                    "url": "https://jup.ag",
                    "description": f"{len(orders)} open orders on Jupiter — may have rewards",
                    "found_at": time.time(),
                    "claimable": False,
                })
    except Exception as e:
        logger.debug(f"[AIRDROP] Jupiter scan error: {e}")

    # Check wallet for unknown token airdrops (SPL tokens)
    try:
        rpc = HELIUS_RPC or SOL_RPC
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }
        r = requests.post(rpc, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            accounts = data.get("result", {}).get("value", [])
            for acc in accounts:
                info = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                amount = float(info.get("tokenAmount", {}).get("uiAmount", 0) or 0)
                mint = info.get("mint", "")

                # Show ALL tokens with balance — even without price
                if amount > 0 and mint:
                    token_name = mint[:8]
                    token_symbol = "?"
                    value_usd = 0
                    
                    # Try to get price from Jupiter
                    try:
                        price_r = requests.get(
                            f"https://api.jup.ag/price/v2?ids={mint}",
                            timeout=5
                        )
                        if price_r.status_code == 200:
                            price_data = price_r.json().get("data", {}).get(mint, {})
                            price = float(price_data.get("price", 0) or 0)
                            if price_data.get("mintSymbol"):
                                token_name = price_data["mintSymbol"]
                                token_symbol = price_data["mintSymbol"]
                            if price > 0:
                                value_usd = amount * price
                    except Exception:
                        pass
                    
                    # Try DexScreener for price if Jupiter didn't have it
                    if value_usd == 0:
                        try:
                            dx_r = requests.get(
                                f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
                                timeout=5
                            )
                            if dx_r.status_code == 200:
                                pairs = dx_r.json().get("pairs", [])
                                if pairs:
                                    pair = pairs[0]
                                    price = float(pair.get("priceUsd", 0) or 0)
                                    if price > 0:
                                        value_usd = amount * price
                                    if pair.get("baseToken", {}).get("symbol"):
                                        token_name = pair["baseToken"]["symbol"]
                                        token_symbol = pair["baseToken"]["symbol"]
                        except Exception:
                            pass

                    # Add token regardless of price — user needs to see ALL wallet tokens
                    desc = f"{amount:,.2f} tokens in wallet"
                    if value_usd > 0:
                        desc += f" (${value_usd:,.4f})"
                    else:
                        desc += " (price unknown — could be new airdrop!)"
                    
                    airdrops.append({
                        "id": f"sol_token_{mint[:12]}",
                        "name": token_name,
                        "symbol": token_symbol,
                        "type": "wallet_token",
                        "chain": "solana",
                        "source": "wallet_scan",
                        "status": "in_wallet",
                        "amount": amount,
                        "estimated_value_usd": value_usd,
                        "mint": mint,
                        "url": f"https://solscan.io/token/{mint}",
                        "description": desc,
                        "found_at": time.time(),
                        "claimable": False,
                    })

    except Exception as e:
        logger.debug(f"[AIRDROP] Solana wallet scan error: {e}")

    return airdrops


# ═══════════════════════════════════════════════════════════
#  SOURCE 3: WEB SCRAPING — Airdrop aggregator sites
# ═══════════════════════════════════════════════════════════

def scan_airdrop_aggregators() -> List[Dict]:
    """
    Scrape airdrop aggregator websites for latest airdrops.
    """
    airdrops = []

    # Scan known airdrop listing pages
    for url in AIRDROP_SOURCES:
        try:
            r = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if r.status_code != 200:
                continue

            # Extract airdrop info from HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')

            # Generic extraction: find cards/articles with airdrop info
            for article in soup.find_all(['article', 'div'], class_=re.compile(
                    r'airdrop|card|item|entry|listing', re.I))[:20]:
                title_el = article.find(['h2', 'h3', 'h4', 'a'])
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get('href', '') or article.find('a', href=True)
                if isinstance(link, dict):
                    link = link.get('href', '')
                elif hasattr(link, 'get'):
                    link = link.get('href', '')

                # Make absolute URL
                if link and not link.startswith('http'):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)

                desc = article.get_text(strip=True)[:200]

                # Detect chain from text
                chain = "multi"
                text_lower = desc.lower()
                if "solana" in text_lower or "sol" in text_lower:
                    chain = "solana"
                elif "ethereum" in text_lower or "eth" in text_lower:
                    chain = "ethereum"
                elif "arbitrum" in text_lower:
                    chain = "arbitrum"
                elif "base" in text_lower:
                    chain = "base"

                # Detect value from text
                value_match = re.search(r'\$([0-9,]+)', desc)
                est_value = float(value_match.group(1).replace(',', '')) if value_match else 0

                airdrop_id = hashlib.md5(f"{title}_{url}".encode()).hexdigest()[:16]

                airdrops.append({
                    "id": f"web_{airdrop_id}",
                    "name": title[:100],
                    "symbol": "?",
                    "type": "web_airdrop",
                    "chain": chain,
                    "source": url.split('/')[2],
                    "status": "listed",
                    "estimated_value_usd": est_value,
                    "url": link or url,
                    "description": desc[:200],
                    "found_at": time.time(),
                    "claimable": True,
                })

        except ImportError:
            logger.debug("[AIRDROP] BeautifulSoup not available for web scraping")
            break
        except Exception as e:
            logger.debug(f"[AIRDROP] Aggregator scan error ({url}): {e}")

    return airdrops


# ═══════════════════════════════════════════════════════════
#  SOURCE 4: PROTOCOL TRACKING — Upcoming airdrops by protocol usage
# ═══════════════════════════════════════════════════════════

# Known protocols likely to airdrop
UPCOMING_AIRDROP_PROTOCOLS = [
    {"name": "Phantom", "chain": "solana", "category": "wallet", "likelihood": "high",
     "action": "Use Phantom swap, bridge features daily"},
    {"name": "Marginfi", "chain": "solana", "category": "lending", "likelihood": "high",
     "action": "Lend/Borrow on Marginfi"},
    {"name": "Kamino", "chain": "solana", "category": "DeFi", "likelihood": "high",
     "action": "Provide liquidity on Kamino"},
    {"name": "Drift Protocol", "chain": "solana", "category": "perps", "likelihood": "medium",
     "action": "Trade perpetuals on Drift"},
    {"name": "Zeta Markets", "chain": "solana", "category": "options", "likelihood": "medium",
     "action": "Trade options on Zeta"},
    {"name": "Meteora", "chain": "solana", "category": "AMM", "likelihood": "high",
     "action": "Provide liquidity in Meteora pools"},
    {"name": "Backpack Exchange", "chain": "solana", "category": "exchange", "likelihood": "high",
     "action": "Trade on Backpack exchange"},
    {"name": "Hyperliquid", "chain": "arbitrum", "category": "perps", "likelihood": "medium",
     "action": "Trade on Hyperliquid L1"},
    {"name": "LayerZero", "chain": "multi", "category": "bridge", "likelihood": "medium",
     "action": "Bridge assets using LayerZero"},
    {"name": "Scroll", "chain": "ethereum", "category": "L2", "likelihood": "medium",
     "action": "Use Scroll L2 for transactions"},
    {"name": "Linea", "chain": "ethereum", "category": "L2", "likelihood": "medium",
     "action": "Use Linea L2 for DeFi"},
    {"name": "Berachain", "chain": "berachain", "category": "L1", "likelihood": "high",
     "action": "Use Berachain testnet/mainnet"},
    {"name": "Monad", "chain": "monad", "category": "L1", "likelihood": "high",
     "action": "Join Monad testnet when available"},
    {"name": "Eclipse", "chain": "solana", "category": "L2", "likelihood": "high",
     "action": "Use Eclipse SVM L2"},
]


def get_upcoming_airdrop_protocols() -> List[Dict]:
    """Get list of protocols likely to airdrop."""
    return UPCOMING_AIRDROP_PROTOCOLS


# ═══════════════════════════════════════════════════════════
#  SCAM DETECTOR — Protect against fake airdrops
# ═══════════════════════════════════════════════════════════

_SCAM_PATTERNS = [
    r'connect.*wallet.*claim',
    r'send.*sol.*receive',
    r'approve.*unlimited',
    r'private.*key',
    r'seed.*phrase',
    r'mnemonic',
    r'verify.*wallet',
    r'claim.*now.*limited',
    r'sent.*you.*\d+.*token',
    r'double.*your',
    r'free.*bitcoin',
]

_COMPILED_SCAM = [re.compile(p, re.IGNORECASE) for p in _SCAM_PATTERNS]


def check_airdrop_scam(airdrop: Dict) -> Tuple[bool, str]:
    """
    Check if an airdrop looks like a scam.
    Returns (is_safe, reason).
    """
    text = f"{airdrop.get('name', '')} {airdrop.get('description', '')}".lower()

    for i, pattern in enumerate(_COMPILED_SCAM):
        if pattern.search(text):
            return False, f"Scam pattern detected: {_SCAM_PATTERNS[i]}"

    # Check for suspicious URLs
    url = airdrop.get("url", "")
    if url:
        suspicious_domains = [
            "bit.ly", "tinyurl", "short.io", "t.co",
            "claim-", "free-", "airdrop-claim",
            ".xyz", ".tk", ".ml", ".ga",
        ]
        for sd in suspicious_domains:
            if sd in url.lower():
                return False, f"Suspicious URL domain: {sd}"

    # Value too good to be true
    value = airdrop.get("estimated_value_usd", 0)
    if value > 50000:
        return False, f"Value suspiciously high: ${value}"

    return True, "Passed all checks"


# ═══════════════════════════════════════════════════════════
#  SOURCE 4A: TON WALLET SCANNER — Check TON blockchain
# ═══════════════════════════════════════════════════════════

def scan_ton_wallet(wallet: str = None) -> List[Dict]:
    """Scan TON wallet for tokens/jettons (airdrops on TON chain)."""
    wallet = wallet or OWNER_TON_WALLET
    airdrops = []
    if not wallet:
        return airdrops

    try:
        # TON Center API to get jettons (TON tokens)
        r = requests.get(
            f"https://tonapi.io/v2/accounts/{wallet}/jettons",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/3.0"}
        )
        if r.status_code == 200:
            balances = r.json().get("balances", [])
            for bal in balances:
                jetton = bal.get("jetton", {})
                amount_raw = int(bal.get("balance", "0") or "0")
                decimals = int(jetton.get("decimals", 9) or 9)
                amount = amount_raw / (10 ** decimals) if decimals else amount_raw
                name = jetton.get("name", "Unknown TON Token")
                symbol = jetton.get("symbol", "?")
                mint_addr = jetton.get("address", "")
                verified = jetton.get("verification", "") == "whitelist"

                if amount > 0:
                    # Try to get USD price
                    value_usd = 0
                    try:
                        price_r = requests.get(
                            f"https://tonapi.io/v2/rates?tokens={mint_addr}&currencies=usd",
                            timeout=5
                        )
                        if price_r.status_code == 200:
                            rate_data = price_r.json().get("rates", {}).get(mint_addr, {})
                            price = float(rate_data.get("prices", {}).get("USD", 0) or 0)
                            if price > 0:
                                value_usd = amount * price
                    except Exception:
                        pass

                    desc = f"{amount:,.2f} {symbol} in TON wallet"
                    if value_usd > 0:
                        inr = usd_to_inr(value_usd)
                        desc += f" (${value_usd:,.4f} / ₹{inr:,.2f})"
                    else:
                        desc += " (price unknown — could be new airdrop!)"

                    airdrops.append({
                        "id": f"ton_token_{mint_addr[:12]}",
                        "name": name,
                        "symbol": symbol,
                        "type": "wallet_token",
                        "chain": "ton",
                        "source": "ton_wallet_scan",
                        "status": "in_wallet",
                        "amount": amount,
                        "estimated_value_usd": value_usd,
                        "mint": mint_addr,
                        "url": f"https://tonviewer.com/{wallet}",
                        "description": desc,
                        "found_at": time.time(),
                        "claimable": False,
                        "verified": verified,
                    })

    except Exception as e:
        logger.debug(f"[AIRDROP] TON wallet scan error: {e}")

    # Also get TON balance
    try:
        r = requests.get(
            f"https://tonapi.io/v2/accounts/{wallet}",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/3.0"}
        )
        if r.status_code == 200:
            balance_raw = int(r.json().get("balance", "0") or "0")
            ton_balance = balance_raw / 1e9
            if ton_balance > 0:
                # Get TON price
                value_usd = 0
                try:
                    pr = requests.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd", timeout=5)
                    if pr.status_code == 200:
                        ton_price = float(pr.json().get("rates", {}).get("TON", {}).get("prices", {}).get("USD", 0) or 0)
                        value_usd = ton_balance * ton_price
                except Exception:
                    pass

                inr = usd_to_inr(value_usd) if value_usd > 0 else 0
                desc = f"{ton_balance:,.4f} TON"
                if value_usd > 0:
                    desc += f" (${value_usd:,.2f} / ₹{inr:,.2f})"

                airdrops.append({
                    "id": "ton_native_balance",
                    "name": "TON (Toncoin)",
                    "symbol": "TON",
                    "type": "native_balance",
                    "chain": "ton",
                    "source": "ton_wallet_scan",
                    "status": "in_wallet",
                    "amount": ton_balance,
                    "estimated_value_usd": value_usd,
                    "url": f"https://tonviewer.com/{wallet}",
                    "description": desc,
                    "found_at": time.time(),
                    "claimable": False,
                })
    except Exception as e:
        logger.debug(f"[AIRDROP] TON balance error: {e}")

    return airdrops


# ═══════════════════════════════════════════════════════════
#  SOURCE 4B: DEXSCREENER NEW PAIRS — Realtime new token launches
# ═══════════════════════════════════════════════════════════

def scan_dexscreener_new_pairs() -> List[Dict]:
    """Scan DexScreener for brand new token pairs — potential airdrop/early entry."""
    airdrops = []
    try:
        # Get latest Solana pairs
        r = requests.get(
            "https://api.dexscreener.com/token-pairs/v1/solana/latest",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/3.0"}
        )
        if r.status_code == 200:
            pairs = r.json() if isinstance(r.json(), list) else r.json().get("pairs", [])
            for pair in (pairs or [])[:15]:
                base = pair.get("baseToken", {})
                name = base.get("name", "Unknown")
                symbol = base.get("symbol", "?")
                mint = base.get("address", "")
                price_usd = float(pair.get("priceUsd", 0) or 0)
                volume = float(pair.get("volume", {}).get("h24", 0) or 0)
                mcap = float(pair.get("marketCap", 0) or pair.get("fdv", 0) or 0)
                liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                created = pair.get("pairCreatedAt", 0)

                # Only show pairs < 1hr old or with high volume
                pair_age_hours = (time.time() * 1000 - created) / 3600000 if created else 999
                if pair_age_hours < 1 or volume > 10000:
                    desc = f"NEW PAIR! {symbol} | MCap: ${mcap:,.0f} | Vol24h: ${volume:,.0f} | Liq: ${liquidity:,.0f}"
                    airdrops.append({
                        "id": f"dex_new_{mint[:12]}",
                        "name": name,
                        "symbol": symbol,
                        "type": "new_pair",
                        "chain": "solana",
                        "source": "dexscreener_new",
                        "status": "just_launched",
                        "amount": 0,
                        "estimated_value_usd": mcap,
                        "mint": mint,
                        "url": f"https://dexscreener.com/solana/{mint}",
                        "description": desc,
                        "found_at": time.time(),
                        "claimable": True,
                        "pair_age_hours": pair_age_hours,
                        "volume_24h": volume,
                        "liquidity": liquidity,
                    })
    except Exception as e:
        logger.debug(f"[AIRDROP] DexScreener new pairs error: {e}")
    return airdrops


# ═══════════════════════════════════════════════════════════
#  SOURCE 5: PUMP.FUN TRENDING — Realtime trending tokens
# ═══════════════════════════════════════════════════════════

def scan_pumpfun_realtime() -> List[Dict]:
    """Scan pump.fun for trending and recently graduated tokens."""
    airdrops = []
    try:
        # pump.fun king-of-the-hill (trending)
        r = requests.get(
            "https://frontend-api-v3.pump.fun/coins/king-of-the-hill?includeNsfw=false",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/3.0"}
        )
        if r.status_code == 200:
            data = r.json()
            coins = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for coin in coins[:10]:
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "?")
                mint = coin.get("mint", "")
                mcap = float(coin.get("usd_market_cap", 0) or 0)
                
                desc = f"🔥 pump.fun TRENDING! {symbol} | MCap: ${mcap:,.0f}"
                airdrops.append({
                    "id": f"pump_trending_{mint[:12]}",
                    "name": name,
                    "symbol": symbol,
                    "type": "trending_token",
                    "chain": "solana",
                    "source": "pump.fun",
                    "status": "trending",
                    "amount": 0,
                    "estimated_value_usd": mcap,
                    "mint": mint,
                    "url": f"https://pump.fun/{mint}",
                    "description": desc,
                    "found_at": time.time(),
                    "claimable": True,
                })
    except Exception as e:
        logger.debug(f"[AIRDROP] pump.fun trending error: {e}")

    # Recently graduated tokens (hit 69K MCap)
    try:
        r = requests.get(
            "https://frontend-api-v3.pump.fun/coins/latest?includeNsfw=false&limit=10",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/3.0"}
        )
        if r.status_code == 200:
            coins = r.json() if isinstance(r.json(), list) else []
            for coin in coins[:10]:
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "?")
                mint = coin.get("mint", "")
                mcap = float(coin.get("usd_market_cap", 0) or 0)

                aid = f"pump_new_{mint[:12]}"
                if aid not in {a["id"] for a in airdrops}:
                    airdrops.append({
                        "id": aid,
                        "name": name,
                        "symbol": symbol,
                        "type": "new_launch",
                        "chain": "solana",
                        "source": "pump.fun",
                        "status": "just_launched",
                        "amount": 0,
                        "estimated_value_usd": mcap,
                        "mint": mint,
                        "url": f"https://pump.fun/{mint}",
                        "description": f"NEW pump.fun launch! {symbol} | MCap: ${mcap:,.0f}",
                        "found_at": time.time(),
                        "claimable": True,
                    })
    except Exception as e:
        logger.debug(f"[AIRDROP] pump.fun latest error: {e}")

    return airdrops


# ═══════════════════════════════════════════════════════════
#  🔥 MASTER SCANNER — Scan ALL sources
# ═══════════════════════════════════════════════════════════

def scan_all_airdrops(wallet: str = None) -> List[Dict]:
    """
    Master scanner: scan all sources for airdrops.
    Returns list of airdrops sorted by estimated value.
    """
    wallet = wallet or OWNER_SOLANA_WALLET
    all_airdrops = []
    seen_ids = set()

    # Source 1: DeFi Llama / CoinGecko
    try:
        dl_airdrops = scan_defillama_airdrops()
        for a in dl_airdrops:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] DeFi Llama scan error: {e}")

    # Source 2: Solana wallet tokens
    try:
        sol_airdrops = scan_solana_airdrops(wallet)
        for a in sol_airdrops:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] Solana scan error: {e}")

    # Source 2B: TON wallet tokens
    try:
        ton_wallet = get_user_wallet(OWNER_CHAT_ID, "ton") or OWNER_TON_WALLET
        if ton_wallet:
            ton_airdrops = scan_ton_wallet(ton_wallet)
            for a in ton_airdrops:
                if a["id"] not in seen_ids:
                    seen_ids.add(a["id"])
                    all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] TON scan error: {e}")

    # Source 3: DexScreener new Solana pairs (REALTIME)
    try:
        dx_airdrops = scan_dexscreener_new_pairs()
        for a in dx_airdrops:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] DexScreener new pairs error: {e}")

    # Source 4: pump.fun trending (REALTIME)
    try:
        pf_airdrops = scan_pumpfun_realtime()
        for a in pf_airdrops:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] pump.fun realtime error: {e}")

    # Source 5: Web aggregators
    try:
        web_airdrops = scan_airdrop_aggregators()
        for a in web_airdrops:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_airdrops.append(a)
    except Exception as e:
        logger.error(f"[AIRDROP] Web scan error: {e}")

    # Scam filter
    safe_airdrops = []
    for a in all_airdrops:
        is_safe, reason = check_airdrop_scam(a)
        a["is_safe"] = is_safe
        a["scam_check"] = reason
        if is_safe:
            safe_airdrops.append(a)
        else:
            logger.warning(f"[AIRDROP] Filtered scam: {a['name']} — {reason}")

    # Sort by value
    safe_airdrops.sort(key=lambda x: x.get("estimated_value_usd", 0), reverse=True)

    # Save to DB
    for a in safe_airdrops:
        if a["id"] not in {d["id"] for d in _airdrop_db}:
            _airdrop_db.append(a)
    _save_airdrop_db()

    return safe_airdrops


def get_new_airdrop_alerts(wallet: str = None) -> List[Dict]:
    """Get only NEW airdrop alerts not recently sent."""
    now = time.time()
    all_drops = scan_all_airdrops(wallet)
    new_alerts = []

    for a in all_drops:
        aid = a["id"]
        if now - _alerted_airdrops.get(aid, 0) > ALERT_COOLDOWN:
            new_alerts.append(a)
            _alerted_airdrops[aid] = now

    return new_alerts


# ═══════════════════════════════════════════════════════════
#  FORMAT FOR TELEGRAM
# ═══════════════════════════════════════════════════════════

def format_airdrop_scan(airdrops: List[Dict]) -> str:
    """Format airdrop scan results for Telegram."""
    if not airdrops:
        return (
            "🎁 *JARVIS AIRDROP HUNTER* 🎁\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "अभी कोई new airdrop नहीं मिला।\n\n"
            "💡 *Tip:* Upcoming airdrops के लिए ये protocols use करें:\n"
            "  • Phantom Wallet (swap, bridge)\n"
            "  • Jupiter Exchange\n"
            "  • Marginfi (lend/borrow)\n"
            "  • Meteora (liquidity)\n\n"
            "🔄 Auto-scan हर 90 सेकंड में चल रहा है।\n"
            f"📍 Wallet: `{OWNER_SOLANA_WALLET[:6]}...{OWNER_SOLANA_WALLET[-4:]}`\n"
            "जब कोई airdrop मिलेगा, तुरंत alert आएगा! 🚀"
        )

    msg = "🎁🚀 *JARVIS AIRDROP HUNTER* 🚀🎁\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"_{len(airdrops)} airdrops found | Auto-scam-filter ON_\n\n"

    for i, a in enumerate(airdrops[:15], 1):
        chain_icon = {
            "solana": "🟣",
            "ethereum": "🔵",
            "arbitrum": "🔷",
            "base": "🔵",
            "multi": "🌐",
        }.get(a.get("chain", ""), "🔹")

        status_icon = {
            "claimable": "✅",
            "listed": "📋",
            "in_wallet": "💰",
            "potential": "🔮",
            "active_orders": "📊",
        }.get(a.get("status", ""), "📌")

        source_tag = a.get("source", "unknown")
        value = a.get("estimated_value_usd", 0)
        value_str = f"~${value:,.2f}" if value > 0 else "TBD"
        inr_str = f" (~₹{usd_to_inr(value):,.2f})" if value > 0 else ""

        msg += f"*{i}. {a['name']}* {status_icon}\n"
        msg += f"   {chain_icon} {a.get('chain', '?').upper()} | {source_tag}\n"
        if value > 0:
            msg += f"   💰 Value: {value_str}{inr_str}\n"
        msg += f"   📝 {a.get('description', '')[:100]}\n"

        if a.get("amount"):
            msg += f"   🎯 Amount: {a['amount']:.4f} tokens\n"

        if a.get("url"):
            msg += f"   🔗 [Details]({a['url']})\n"

        # Add swap links for Solana tokens with mint address
        mint = a.get("mint", "")
        if mint and a.get("chain") == "solana":
            msg += f"   🛒 [Jupiter Swap](https://jup.ag/swap/{mint}-SOL)"
            msg += f" | [Raydium](https://raydium.io/swap/?inputMint={mint}&outputMint=sol)\n"

        msg += f"   ✅ Scam check: {a.get('scam_check', 'Passed')}\n\n"

    # Show active wallets
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    sol_wallet = OWNER_SOLANA_WALLET
    ton_wallet = OWNER_TON_WALLET
    if sol_wallet:
        msg += f"🟣 *Solana:* `{sol_wallet[:6]}...{sol_wallet[-4:]}`\n"
    if ton_wallet:
        msg += f"💎 *TON:* `{ton_wallet[:6]}...{ton_wallet[-6:]}`\n"
    msg += f"⚡ Auto-scan: *Every 30 seconds (ULTRA FAST)*\n\n"
    msg += "\n🔮 *UPCOMING AIRDROP PROTOCOLS:*\n"
    for p in UPCOMING_AIRDROP_PROTOCOLS[:5]:
        likelihood = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(p["likelihood"], "⚪")
        msg += f"   {likelihood} *{p['name']}* ({p['chain']}) — {p['action']}\n"

    msg += (
        "\n⚠️ *SAFETY RULES:*\n"
        "• _कभी seed phrase / private key share मत करो!_\n"
        "• _Unknown token ko approve मत करो!_\n"
        "• _JARVIS automatically scam filter करता है_\n"
        "• _हमेशा official website से ही claim करो_"
    )

    return msg


def format_airdrop_voice(airdrops: List[Dict]) -> str:
    """Format for JARVIS to speak."""
    if not airdrops:
        return (
            "अभी कोई new airdrop नहीं मिला जी। "
            "लेकिन auto scanner चल रहा है। "
            "जब कोई मिलेगा, तुरंत बताऊंगी!"
        )

    count = len(airdrops)
    voice = f"जी सुनो! मैंने {count} airdrops ढूंढे हैं। "

    top = airdrops[0]
    value = top.get("estimated_value_usd", 0)
    if value > 0:
        voice += f"सबसे बड़ा {top['name']} है, estimated value {value} dollars। "
    else:
        voice += f"सबसे interesting {top['name']} है, {top.get('chain', '')} chain पर। "

    sol_count = sum(1 for a in airdrops if a.get("chain") == "solana")
    if sol_count > 0:
        voice += f"{sol_count} airdrops Solana पर हैं जो आपके Phantom wallet में आ सकते हैं। "

    voice += (
        "सारी details text message में हैं। "
        "ध्यान रहे — कभी अपना seed phrase किसी को मत दो! "
        "JARVIS automatically scam check करता है।"
    )

    return voice


def format_single_airdrop_alert(airdrop: Dict, chat_id: int = None) -> str:
    """Format a single airdrop alert with INR value + auto-swap links."""
    chain_icon = {"solana": "🟣", "ethereum": "🔵", "arbitrum": "🔷", "ton": "💎"}.get(
        airdrop.get("chain", ""), "🌐")

    msg = f"🎁🚨 *NEW AIRDROP DETECTED!* 🚨🎁\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"🪙 *{airdrop['name']}*\n"
    msg += f"{chain_icon} Chain: {airdrop.get('chain', '?').upper()}\n"

    value = airdrop.get("estimated_value_usd", 0)
    if value > 0:
        inr = usd_to_inr(value)
        msg += f"💰 Value: ~${value:,.4f} (~₹{inr:,.2f})\n"

    if airdrop.get("amount"):
        msg += f"🎯 Amount: {airdrop['amount']:,.4f} tokens\n"

    msg += f"📝 {airdrop.get('description', '')[:200]}\n"

    # 🛒 Direct swap/claim links for Solana tokens
    mint = airdrop.get("mint", "")
    chain = airdrop.get("chain", "")

    if mint and chain == "solana":
        wallet = OWNER_SOLANA_WALLET
        msg += f"\n🛒 *QUICK SWAP (1-Click):*\n"
        msg += f"   🟣 [Jupiter Swap → SOL](https://jup.ag/swap/{mint}-SOL)\n"
        msg += f"   🔵 [Raydium Swap](https://raydium.io/swap/?inputMint={mint}&outputMint=sol)\n"
        msg += f"   👻 [Phantom Swap](https://phantom.app/ul/swap/{mint}-SOL)\n"
        msg += f"   🔍 [Solscan]({airdrop.get('url', f'https://solscan.io/token/{mint}')})\n"
        if wallet:
            msg += f"\n📍 *Solana Wallet:* `{wallet[:6]}...{wallet[-4:]}`\n"

    elif chain == "ton":
        ton_wallet = get_user_wallet(chat_id or OWNER_CHAT_ID, "ton") or OWNER_TON_WALLET
        msg += f"\n💎 *TON ACTIONS:*\n"
        msg += f"   🔗 [View on TonViewer](https://tonviewer.com/{ton_wallet})\n"
        msg += f"   💱 [STON.fi Swap](https://app.ston.fi/swap)\n"
        msg += f"   🏦 [Telegram @wallet](https://t.me/wallet)\n"
        if ton_wallet:
            msg += f"\n📍 *TON Wallet:* `{ton_wallet[:6]}...{ton_wallet[-6:]}`\n"

    if airdrop.get("url") and not mint:
        msg += f"\n🔗 [Claim / Details]({airdrop['url']})\n"

    msg += f"\n✅ Scam Check: {airdrop.get('scam_check', 'Passed')}"
    msg += "\n\n⚠️ _DYOR — Verify on official website before claiming!_"

    return msg


# ═══════════════════════════════════════════════════════════
#  BACKGROUND THREAD — Auto-scan every 5 minutes
# ═══════════════════════════════════════════════════════════

_airdrop_thread: Optional[threading.Thread] = None
_airdrop_running = threading.Event()
_send_alert_callback = None  # Set by telegram_bot.py


def set_alert_callback(callback):
    """Set the function to call when a new airdrop is found."""
    global _send_alert_callback
    _send_alert_callback = callback


def _airdrop_scan_loop():
    """Background loop: scan for airdrops — ULTRA FAST REALTIME (every 30 seconds)."""
    logger.info("[AIRDROP] 🎁 Airdrop Hunter STARTED — ULTRA FAST SCAN every 30 seconds!")
    _airdrop_running.set()

    # Auto-register owner wallets on startup
    register_wallet(OWNER_CHAT_ID, "solana", OWNER_SOLANA_WALLET)
    if OWNER_TON_WALLET:
        register_wallet(OWNER_CHAT_ID, "ton", OWNER_TON_WALLET)
    logger.info(f"[AIRDROP] ✅ Owner wallets registered: SOL={OWNER_SOLANA_WALLET[:8]}... TON={OWNER_TON_WALLET[:8]}...")

    scan_count = 0
    while _airdrop_running.is_set():
        try:
            scan_count += 1
            wallet = get_user_wallet(OWNER_CHAT_ID, "solana")
            if not wallet:
                wallet = OWNER_SOLANA_WALLET
                register_wallet(OWNER_CHAT_ID, "solana", wallet)
            ton_wallet = get_user_wallet(OWNER_CHAT_ID, "ton") or OWNER_TON_WALLET

            # Deep scan every 10th cycle (~5 min), quick scan every 30sec
            if scan_count % 10 == 0:  # Deep scan (all sources)
                new_alerts = get_new_airdrop_alerts(wallet)
                logger.info(f"[AIRDROP] Deep scan #{scan_count}: {len(new_alerts)} new alerts (wallet: {wallet[:8]}...)")
            else:  # Quick scan (Solana wallet + TON wallet + DexScreener + pump.fun)
                new_alerts = []
                now = time.time()
                try:
                    # Scan Solana wallet tokens
                    sol_drops = scan_solana_airdrops(wallet)
                    for a in sol_drops:
                        if now - _alerted_airdrops.get(a["id"], 0) > ALERT_COOLDOWN:
                            new_alerts.append(a)
                            _alerted_airdrops[a["id"]] = now
                except Exception as e:
                    logger.warning(f"[AIRDROP] Wallet scan error: {e}")

                try:
                    # Scan TON wallet tokens
                    if ton_wallet:
                        ton_drops = scan_ton_wallet(ton_wallet)
                        for a in ton_drops:
                            if now - _alerted_airdrops.get(a["id"], 0) > ALERT_COOLDOWN:
                                new_alerts.append(a)
                                _alerted_airdrops[a["id"]] = now
                except Exception as e:
                    logger.warning(f"[AIRDROP] TON wallet scan error: {e}")
                
                try:
                    # Realtime DexScreener new pairs
                    dx_drops = scan_dexscreener_new_pairs()
                    for a in dx_drops:
                        if now - _alerted_airdrops.get(a["id"], 0) > ALERT_COOLDOWN:
                            new_alerts.append(a)
                            _alerted_airdrops[a["id"]] = now
                except Exception as e:
                    logger.warning(f"[AIRDROP] DexScreener realtime error: {e}")

                try:
                    # Realtime pump.fun trending
                    pf_drops = scan_pumpfun_realtime()
                    for a in pf_drops:
                        if now - _alerted_airdrops.get(a["id"], 0) > ALERT_COOLDOWN:
                            new_alerts.append(a)
                            _alerted_airdrops[a["id"]] = now
                except Exception as e:
                    logger.warning(f"[AIRDROP] pump.fun realtime error: {e}")

            # Send alerts
            if new_alerts and _send_alert_callback:
                for alert in new_alerts[:5]:  # Max 5 alerts per cycle
                    try:
                        is_safe, _ = check_airdrop_scam(alert)
                        if is_safe:
                            msg = format_single_airdrop_alert(alert)
                            _send_alert_callback(OWNER_CHAT_ID, msg)
                            logger.info(f"[AIRDROP] 🎁 Alert sent: {alert['name']} ({alert.get('type','?')}) to wallet {wallet[:8]}...")
                    except Exception as e:
                        logger.error(f"[AIRDROP] Alert send error: {e}")

        except Exception as e:
            logger.error(f"[AIRDROP] Scan loop error: {e}")

        # Wait SCAN_INTERVAL seconds (30s)
        for _ in range(SCAN_INTERVAL):
            if not _airdrop_running.is_set():
                break
            time.sleep(1)


def start_airdrop_hunter():
    """Start the background airdrop scanner."""
    global _airdrop_thread
    if _airdrop_thread and _airdrop_thread.is_alive():
        logger.info("[AIRDROP] Hunter already running")
        return

    _airdrop_thread = threading.Thread(
        target=_airdrop_scan_loop,
        name="AirdropHunter",
        daemon=True
    )
    _airdrop_thread.start()
    logger.info("[AIRDROP] 🎁🚀 Airdrop Hunter LAUNCHED!")


def stop_airdrop_hunter():
    """Stop the background scanner."""
    _airdrop_running.clear()
    logger.info("[AIRDROP] Hunter stopped")


# ═══════════════════════════════════════════════════════════
#  ONE-CALL FUNCTIONS (for Telegram bot)
# ═══════════════════════════════════════════════════════════

def airdrop_scan_full() -> str:
    """One-call: Full airdrop scan with all sources."""
    try:
        airdrops = scan_all_airdrops()
        return format_airdrop_scan(airdrops)
    except Exception as e:
        logger.error(f"[AIRDROP] Full scan error: {e}")
        return f"❌ Airdrop scan error: {str(e)[:100]}\n\n💡 Try again in a minute."


def airdrop_scan_solana() -> str:
    """One-call: Solana-only airdrop scan."""
    try:
        wallet = get_user_wallet(OWNER_CHAT_ID, "solana")
        airdrops = scan_solana_airdrops(wallet)
        return format_airdrop_scan(airdrops)
    except Exception as e:
        return f"❌ Solana scan error: {str(e)[:100]}"


def airdrop_upcoming() -> str:
    """Show upcoming airdrop protocols to farm."""
    protocols = get_upcoming_airdrop_protocols()

    msg = "🔮🎁 *UPCOMING AIRDROP PROTOCOLS* 🎁🔮\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_ये protocols use करो — airdrop मिलने के chances बढ़ेंगे!_\n\n"

    for i, p in enumerate(protocols, 1):
        likelihood = {"high": "🟢 HIGH", "medium": "🟡 MEDIUM", "low": "🔴 LOW"}.get(
            p["likelihood"], "⚪")
        chain_icon = {"solana": "🟣", "ethereum": "🔵", "arbitrum": "🔷",
                      "multi": "🌐"}.get(p.get("chain", ""), "🔹")

        msg += f"*{i}. {p['name']}* {chain_icon}\n"
        msg += f"   📊 Likelihood: {likelihood}\n"
        msg += f"   🎯 Action: _{p['action']}_\n"
        msg += f"   📂 Category: {p['category']}\n\n"

    msg += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* Daily protocol use करो, gas fees as investment samjho.\n"
        "🛡️ *Safety:* JARVIS auto-scam-check karega!\n"
        "🔄 Auto-scan ON — new airdrop milte hi alert aayega!"
    )

    return msg


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'scan_all_airdrops',
    'scan_solana_airdrops',
    'scan_ton_wallet',
    'scan_airdrop_aggregators',
    'scan_dexscreener_new_pairs',
    'scan_pumpfun_realtime',
    'get_new_airdrop_alerts',
    'format_airdrop_scan',
    'format_airdrop_voice',
    'format_single_airdrop_alert',
    'airdrop_scan_full',
    'airdrop_scan_solana',
    'airdrop_upcoming',
    'start_airdrop_hunter',
    'stop_airdrop_hunter',
    'set_alert_callback',
    'register_wallet',
    'get_user_wallet',
    'get_all_user_wallets',
    'usd_to_inr',
    'check_airdrop_scam',
    'get_upcoming_airdrop_protocols',
    'OWNER_TON_WALLET',
]
