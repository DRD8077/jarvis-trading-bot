"""
🚀💰 JARVIS REAL TRADER v1.0 — Actual On-Chain Solana Trading via Jupiter DEX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REAL TRADING — Not Paper Trading!
• Generates & manages encrypted Solana keypairs per user
• Executes real token swaps via Jupiter DEX Aggregator (v6)
• Auto-buy dip gems, auto-sell at take-profit/stop-loss ON-CHAIN
• Auto-compound: reinvest profits → 2K → 2L → 2Cr → 2LCr

100% FREE APIs:
  • Solana RPC (mainnet-beta) — free
  • Jupiter Swap API v6 — free, no API key
  • DexScreener — free
  • CoinGecko — free

WARNING: Real money at risk. DYOR. JARVIS is not liable for losses.
"""

import os
import json
import time
import base64
import hashlib
import hmac
import secrets
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Solana SDK
try:
    import base58
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.transaction import VersionedTransaction
    from solders.commitment_config import CommitmentLevel
    SOLANA_SDK_AVAILABLE = True
except ImportError:
    SOLANA_SDK_AVAILABLE = False

logger = logging.getLogger("JARVIS-REAL-TRADER")

# ═══════════════════════════════════════════════════════════════
#  CONFIG — All FREE endpoints
# ═══════════════════════════════════════════════════════════════

# Solana RPC (free tier)
FREE_RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://rpc.ankr.com/solana",
]
HELIUS_KEY = os.environ.get("HELIUS_API_KEY", "")
if HELIUS_KEY:
    FREE_RPC_ENDPOINTS.insert(0, f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}")

# Jupiter V6 API (free, unlimited)
JUPITER_QUOTE_URL = "https://api.jup.ag/swap/v1/quote"
JUPITER_SWAP_URL = "https://api.jup.ag/swap/v1/swap"
JUPITER_PRICE_URL = "https://api.jup.ag/price/v2"
JUPITER_TOKEN_LIST_URL = "https://token.jup.ag/strict"

# Token mints
SOL_MINT = "So11111111111111111111111111111111111111111"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# Owner config
OWNER_WALLET = os.environ.get("OWNER_SOLANA_WALLET", "8F1PJhuJa45RMWMJwgDASXL6bm6GYd1MtReJSTcWugaR")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))

# Encrypted wallet storage
TRADER_WALLET_FILE = Path("jarvis_trader_wallets_encrypted.json")
TRADE_LOG_FILE = Path("jarvis_trade_log.json")

# Trading config
MIN_SOL_RESERVE = 0.005       # Keep for fees (rent + tx fees)
MAX_SLIPPAGE_BPS = 500        # 5% slippage max
DEFAULT_PRIORITY_FEE = 50000  # 0.00005 SOL priority fee (lamports)
LAMPORTS_PER_SOL = 1_000_000_000

# Auto-compound stages (INR targets)
COMPOUND_STAGES = [
    {"name": "Stage 1: 2K → 2L", "target_inr": 200_000, "from_inr": 2_000},
    {"name": "Stage 2: 2L → 2Cr", "target_inr": 20_000_000, "from_inr": 200_000},
    {"name": "Stage 3: 2Cr → 2L Cr", "target_inr": 2_000_000_000, "from_inr": 20_000_000},
]

# Encryption key (derived from bot token)
_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "default-key")
_MASTER_KEY = hashlib.sha256(f"JARVIS-TRADER-{_BOT_TOKEN}".encode()).digest()
_HMAC_KEY = hashlib.sha256(f"JARVIS-TRADER-HMAC-{_BOT_TOKEN}".encode()).digest()

_wallets_lock = threading.Lock()
_auto_trader_running = False
_auto_trader_thread = None
_trade_callback = None  # callback(chat_id, message)

# USD/INR cache
_usd_inr_rate = 83.5
_usd_inr_ts = 0


# ═══════════════════════════════════════════════════════════════
#  🔐 ENCRYPTION — AES-256 Grade for Private Keys
# ═══════════════════════════════════════════════════════════════

def _encrypt(data: str) -> str:
    """Encrypt private key using PBKDF2-XOR + HMAC."""
    try:
        data_bytes = data.encode('utf-8')
        iv = secrets.token_bytes(16)
        key_stream = hashlib.pbkdf2_hmac('sha256', _MASTER_KEY, iv, 100000, dklen=len(data_bytes))
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_stream))
        mac = hmac.new(_HMAC_KEY, iv + encrypted, hashlib.sha256).digest()
        return base64.b64encode(iv + encrypted + mac).decode('ascii')
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return ""


def _decrypt(token: str) -> str:
    """Decrypt and verify HMAC."""
    try:
        combined = base64.b64decode(token.encode('ascii'))
        iv, mac = combined[:16], combined[-32:]
        encrypted = combined[16:-32]
        if not hmac.compare_digest(mac, hmac.new(_HMAC_KEY, iv + encrypted, hashlib.sha256).digest()):
            logger.error("HMAC verification FAILED — possible tampering!")
            return ""
        key_stream = hashlib.pbkdf2_hmac('sha256', _MASTER_KEY, iv, 100000, dklen=len(encrypted))
        return bytes(a ^ b for a, b in zip(encrypted, key_stream)).decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════
#  💼 WALLET MANAGEMENT — Real Solana Keypairs
# ═══════════════════════════════════════════════════════════════

def _load_trader_wallets() -> dict:
    try:
        if TRADER_WALLET_FILE.exists():
            return json.loads(TRADER_WALLET_FILE.read_text())
    except Exception as e:
        logger.error(f"Load wallets error: {e}")
    return {}


def _save_trader_wallets(data: dict):
    try:
        TRADER_WALLET_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.error(f"Save wallets error: {e}")


def create_trading_wallet(chat_id: int) -> dict:
    """
    Create a NEW Solana keypair for user. Private key encrypted.
    Returns { pubkey, created, success }
    """
    if not SOLANA_SDK_AVAILABLE:
        return {"error": "Solana SDK not installed. pip install solana solders base58"}

    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid in wallets and wallets[uid].get("pubkey"):
            # Already has wallet
            return {
                "success": True,
                "pubkey": wallets[uid]["pubkey"],
                "already_exists": True,
                "message": "Trading wallet already exists!"
            }

        # Generate new keypair
        kp = Keypair()
        pubkey = str(kp.pubkey())
        # Encrypt the full 64-byte secret key
        secret_b58 = base58.b58encode(bytes(kp)).decode('ascii')
        encrypted_key = _encrypt(secret_b58)

        wallets[uid] = {
            "chat_id": chat_id,
            "pubkey": pubkey,
            "encrypted_key": encrypted_key,
            "created": datetime.now().isoformat(),
            "trades": [],
            "active_positions": [],
            "total_invested_sol": 0.0,
            "total_profit_sol": 0.0,
            "total_profit_inr": 0.0,
            "compound_stage": 0,
            "auto_trade_enabled": False,
        }
        _save_trader_wallets(wallets)

    logger.info(f"[TRADER] Created wallet for {chat_id}: {pubkey}")
    return {
        "success": True,
        "pubkey": pubkey,
        "already_exists": False,
        "message": f"✅ Trading wallet created!\n\nAddress: `{pubkey}`\n\n⚠️ Send SOL to this address to start trading."
    }


def get_trading_wallet(chat_id: int) -> Optional[dict]:
    """Get user's trading wallet info (without private key)."""
    uid = str(chat_id)
    wallets = _load_trader_wallets()
    if uid not in wallets:
        return None
    w = wallets[uid].copy()
    w.pop("encrypted_key", None)  # Never expose private key
    return w


def _get_keypair(chat_id: int) -> Optional['Keypair']:
    """Get decrypted Keypair for signing transactions. INTERNAL ONLY."""
    if not SOLANA_SDK_AVAILABLE:
        return None
    uid = str(chat_id)
    wallets = _load_trader_wallets()
    if uid not in wallets:
        return None
    encrypted = wallets[uid].get("encrypted_key", "")
    if not encrypted:
        return None
    secret_b58 = _decrypt(encrypted)
    if not secret_b58:
        return None
    try:
        secret_bytes = base58.b58decode(secret_b58)
        return Keypair.from_bytes(secret_bytes)
    except Exception as e:
        logger.error(f"Keypair restore error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  🔗 SOLANA RPC — Smart failover
# ═══════════════════════════════════════════════════════════════

def _rpc_call(method: str, params: list, timeout: int = 20) -> Optional[dict]:
    """Make Solana JSON-RPC call with failover."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    for endpoint in FREE_RPC_ENDPOINTS:
        try:
            r = requests.post(endpoint, json=payload, timeout=timeout,
                              headers={"Content-Type": "application/json"})
            if r.status_code == 200:
                data = r.json()
                if "error" not in data:
                    return data
        except Exception:
            continue
    return None


def get_sol_balance(pubkey: str) -> float:
    """Get SOL balance of a wallet."""
    try:
        result = _rpc_call("getBalance", [pubkey, {"commitment": "confirmed"}])
        if result and "result" in result:
            return result["result"]["value"] / LAMPORTS_PER_SOL
    except Exception as e:
        logger.error(f"Balance check error: {e}")
    return 0.0


def get_token_accounts(pubkey: str) -> List[dict]:
    """Get all SPL token accounts for a wallet."""
    try:
        result = _rpc_call("getTokenAccountsByOwner", [
            pubkey,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed", "commitment": "confirmed"}
        ])
        if result and "result" in result:
            accounts = []
            for acc in result["result"]["value"]:
                info = acc["account"]["data"]["parsed"]["info"]
                mint = info["mint"]
                amount = float(info["tokenAmount"]["uiAmountString"])
                decimals = info["tokenAmount"]["decimals"]
                if amount > 0:
                    accounts.append({
                        "mint": mint,
                        "amount": amount,
                        "decimals": decimals,
                        "account": acc["pubkey"],
                    })
            return accounts
    except Exception as e:
        logger.error(f"Token accounts error: {e}")
    return []


def get_token_price_usd(mint: str) -> float:
    """Get token price via Jupiter Price API."""
    try:
        r = requests.get(f"{JUPITER_PRICE_URL}?ids={mint}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            token_data = data.get("data", {}).get(mint, {})
            return float(token_data.get("price", 0))
    except Exception:
        pass
    return 0.0


def _get_usd_inr() -> float:
    """Get live USD/INR rate."""
    global _usd_inr_rate, _usd_inr_ts
    if time.time() - _usd_inr_ts < 3600:  # Cache 1 hour
        return _usd_inr_rate
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
        if r.status_code == 200:
            _usd_inr_rate = r.json().get("rates", {}).get("INR", 83.5)
            _usd_inr_ts = time.time()
    except Exception:
        pass
    return _usd_inr_rate


# ═══════════════════════════════════════════════════════════════
#  🔄 JUPITER DEX — Real Swap Execution
# ═══════════════════════════════════════════════════════════════

def get_swap_quote(input_mint: str, output_mint: str, amount_lamports: int,
                   slippage_bps: int = MAX_SLIPPAGE_BPS) -> Optional[dict]:
    """
    Get a swap quote from Jupiter V6.
    amount_lamports: input amount in smallest unit (lamports for SOL, raw for SPL)
    """
    try:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount_lamports),
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": False,
        }
        r = requests.get(JUPITER_QUOTE_URL, params=params, timeout=15)
        if r.status_code == 200:
            quote = r.json()
            if quote.get("outAmount"):
                return quote
            else:
                logger.warning(f"[JUPITER] No route found: {input_mint[:8]}→{output_mint[:8]}")
        else:
            logger.error(f"[JUPITER] Quote error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.error(f"[JUPITER] Quote exception: {e}")
    return None


def execute_swap(chat_id: int, input_mint: str, output_mint: str,
                 amount_lamports: int, slippage_bps: int = MAX_SLIPPAGE_BPS) -> dict:
    """
    Execute a REAL on-chain swap via Jupiter.
    Returns { success, signature, in_amount, out_amount, ... }
    """
    if not SOLANA_SDK_AVAILABLE:
        return {"error": "Solana SDK not available"}

    kp = _get_keypair(chat_id)
    if not kp:
        return {"error": "No trading wallet found. Create one first!"}

    pubkey = str(kp.pubkey())

    # 1. Get quote
    quote = get_swap_quote(input_mint, output_mint, amount_lamports, slippage_bps)
    if not quote:
        return {"error": "No swap route found. Token may have low liquidity."}

    # 2. Get swap transaction from Jupiter
    try:
        swap_body = {
            "quoteResponse": quote,
            "userPublicKey": pubkey,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": DEFAULT_PRIORITY_FEE,
            "dynamicComputeUnitLimit": True,
        }
        r = requests.post(JUPITER_SWAP_URL, json=swap_body, timeout=30)
        if r.status_code != 200:
            return {"error": f"Jupiter swap API error: {r.status_code} — {r.text[:200]}"}
        swap_data = r.json()
        swap_tx_b64 = swap_data.get("swapTransaction")
        if not swap_tx_b64:
            return {"error": "Jupiter returned no transaction. Try again."}
    except Exception as e:
        return {"error": f"Swap request failed: {str(e)[:100]}"}

    # 3. Deserialize, sign, and send
    try:
        raw_tx = base64.b64decode(swap_tx_b64)
        tx = VersionedTransaction.from_bytes(raw_tx)
        # Sign with our keypair
        signed_tx = VersionedTransaction(tx.message, [kp])
        signed_bytes = bytes(signed_tx)

        # Send to Solana RPC
        tx_b64 = base64.b64encode(signed_bytes).decode('ascii')
        result = _rpc_call("sendTransaction", [
            tx_b64,
            {
                "encoding": "base64",
                "skipPreflight": False,
                "preflightCommitment": "confirmed",
                "maxRetries": 3,
            }
        ])

        if result and "result" in result:
            signature = result["result"]
            logger.info(f"[TRADER] ✅ Swap TX sent: {signature}")

            # Wait for confirmation
            confirmed = _wait_for_confirmation(signature, timeout=60)

            return {
                "success": True,
                "signature": signature,
                "confirmed": confirmed,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "in_amount": int(quote.get("inAmount", amount_lamports)),
                "out_amount": int(quote.get("outAmount", 0)),
                "price_impact": quote.get("priceImpactPct", "0"),
                "route": quote.get("routePlan", []),
                "solscan_url": f"https://solscan.io/tx/{signature}",
            }
        else:
            error_msg = "Unknown RPC error"
            if result and "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))[:200]
            return {"error": f"Transaction failed: {error_msg}"}
    except Exception as e:
        return {"error": f"Sign/send error: {str(e)[:200]}"}


def _wait_for_confirmation(signature: str, timeout: int = 60) -> bool:
    """Wait for transaction confirmation."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = _rpc_call("getSignatureStatuses", [[signature]], timeout=10)
            if result and "result" in result:
                statuses = result["result"]["value"]
                if statuses and statuses[0]:
                    if statuses[0].get("confirmationStatus") in ("confirmed", "finalized"):
                        return True
                    if statuses[0].get("err"):
                        logger.error(f"[TRADER] TX failed on-chain: {statuses[0]['err']}")
                        return False
        except Exception:
            pass
        time.sleep(2)
    return False


# ═══════════════════════════════════════════════════════════════
#  🎯 BUY / SELL — High-Level Trading Functions
# ═══════════════════════════════════════════════════════════════

def buy_token(chat_id: int, token_mint: str, sol_amount: float,
              slippage_bps: int = MAX_SLIPPAGE_BPS) -> dict:
    """
    Buy a token using SOL.
    sol_amount: how much SOL to spend (e.g. 0.1 SOL)
    """
    kp = _get_keypair(chat_id)
    if not kp:
        return {"error": "No trading wallet. Use /create_wallet first."}

    pubkey = str(kp.pubkey())
    balance = get_sol_balance(pubkey)

    if balance < sol_amount + MIN_SOL_RESERVE:
        return {"error": f"Insufficient SOL. Balance: {balance:.4f} SOL, Need: {sol_amount + MIN_SOL_RESERVE:.4f} SOL (includes fee reserve)"}

    amount_lamports = int(sol_amount * LAMPORTS_PER_SOL)

    logger.info(f"[TRADER] BUY: {chat_id} buying {token_mint[:12]}... for {sol_amount} SOL")

    result = execute_swap(chat_id, SOL_MINT, token_mint, amount_lamports, slippage_bps)

    if result.get("success"):
        # Record the trade
        out_amount = int(result.get("out_amount", 0))
        entry_price = get_token_price_usd(token_mint)
        usd_inr = _get_usd_inr()

        trade = {
            "id": f"T{int(time.time())}{secrets.token_hex(2).upper()}",
            "type": "buy",
            "token_mint": token_mint,
            "sol_spent": sol_amount,
            "tokens_received": out_amount,
            "entry_price_usd": entry_price,
            "signature": result["signature"],
            "timestamp": datetime.now().isoformat(),
            "status": "confirmed" if result.get("confirmed") else "pending",
        }
        _record_trade(chat_id, trade)

        # Add to active positions
        _add_position(chat_id, {
            "token_mint": token_mint,
            "entry_price_usd": entry_price,
            "sol_invested": sol_amount,
            "tokens_held": out_amount,
            "buy_signature": result["signature"],
            "bought_at": datetime.now().isoformat(),
            "status": "active",
            "take_profit_levels": [200, 500, 1000, 5000, 10000, 100000, 1000000],  # % gain
            "stop_loss_pct": -35,
            "profits_taken": [],
        })

        result["trade_id"] = trade["id"]

    return result


def sell_token(chat_id: int, token_mint: str, sell_pct: float = 100.0,
               slippage_bps: int = MAX_SLIPPAGE_BPS) -> dict:
    """
    Sell a token for SOL.
    sell_pct: what % of holdings to sell (default 100%)
    """
    kp = _get_keypair(chat_id)
    if not kp:
        return {"error": "No trading wallet."}

    pubkey = str(kp.pubkey())

    # Find token account and balance
    accounts = get_token_accounts(pubkey)
    token_acc = None
    for acc in accounts:
        if acc["mint"] == token_mint:
            token_acc = acc
            break

    if not token_acc or token_acc["amount"] <= 0:
        return {"error": "No tokens found to sell."}

    sell_amount = token_acc["amount"] * (sell_pct / 100.0)
    # Convert to raw amount (smallest unit)
    raw_amount = int(sell_amount * (10 ** token_acc["decimals"]))

    if raw_amount <= 0:
        return {"error": "Sell amount too small."}

    logger.info(f"[TRADER] SELL: {chat_id} selling {sell_amount} of {token_mint[:12]}...")

    result = execute_swap(chat_id, token_mint, SOL_MINT, raw_amount, slippage_bps)

    if result.get("success"):
        sol_received = int(result.get("out_amount", 0)) / LAMPORTS_PER_SOL

        trade = {
            "id": f"T{int(time.time())}{secrets.token_hex(2).upper()}",
            "type": "sell",
            "token_mint": token_mint,
            "tokens_sold": sell_amount,
            "sol_received": sol_received,
            "exit_price_usd": get_token_price_usd(token_mint),
            "signature": result["signature"],
            "timestamp": datetime.now().isoformat(),
            "status": "confirmed" if result.get("confirmed") else "pending",
        }
        _record_trade(chat_id, trade)

        if sell_pct >= 100:
            _close_position(chat_id, token_mint, "manual_sell")

        result["sol_received"] = sol_received
        result["trade_id"] = trade["id"]

    return result


# ═══════════════════════════════════════════════════════════════
#  📊 POSITION & TRADE TRACKING
# ═══════════════════════════════════════════════════════════════

def _add_position(chat_id: int, position: dict):
    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid in wallets:
            wallets[uid].setdefault("active_positions", []).append(position)
            wallets[uid]["total_invested_sol"] = wallets[uid].get("total_invested_sol", 0) + position.get("sol_invested", 0)
            _save_trader_wallets(wallets)


def _close_position(chat_id: int, token_mint: str, reason: str = "sold"):
    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid in wallets:
            positions = wallets[uid].get("active_positions", [])
            for pos in positions:
                if pos.get("token_mint") == token_mint and pos.get("status") == "active":
                    pos["status"] = reason
                    pos["closed_at"] = datetime.now().isoformat()
            _save_trader_wallets(wallets)


def _record_trade(chat_id: int, trade: dict):
    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid in wallets:
            wallets[uid].setdefault("trades", []).append(trade)
            _save_trader_wallets(wallets)
    # Also log to trade log file
    try:
        logs = {}
        if TRADE_LOG_FILE.exists():
            logs = json.loads(TRADE_LOG_FILE.read_text())
        logs.setdefault(uid, []).append(trade)
        TRADE_LOG_FILE.write_text(json.dumps(logs, indent=2))
    except Exception:
        pass


def get_live_portfolio(chat_id: int) -> dict:
    """Get live portfolio with real on-chain balances and P&L."""
    wallet = get_trading_wallet(chat_id)
    if not wallet:
        return {"error": "No trading wallet."}

    pubkey = wallet["pubkey"]
    sol_balance = get_sol_balance(pubkey)
    token_accounts = get_token_accounts(pubkey)
    usd_inr = _get_usd_inr()
    sol_price = get_token_price_usd(SOL_MINT)

    positions = []
    total_value_usd = sol_balance * sol_price

    for acc in token_accounts:
        price = get_token_price_usd(acc["mint"])
        value_usd = acc["amount"] * price
        total_value_usd += value_usd

        # Find matching active position for P&L
        pos_info = _find_position(chat_id, acc["mint"])
        entry_price = pos_info.get("entry_price_usd", 0) if pos_info else 0
        pnl_pct = ((price / entry_price) - 1) * 100 if entry_price > 0 else 0

        positions.append({
            "mint": acc["mint"],
            "amount": acc["amount"],
            "price_usd": price,
            "value_usd": value_usd,
            "value_inr": value_usd * usd_inr,
            "entry_price_usd": entry_price,
            "pnl_pct": pnl_pct,
            "sol_invested": pos_info.get("sol_invested", 0) if pos_info else 0,
        })

    total_invested = wallet.get("total_invested_sol", 0) * sol_price
    total_pnl_usd = total_value_usd - total_invested if total_invested > 0 else 0

    return {
        "pubkey": pubkey,
        "sol_balance": sol_balance,
        "sol_price_usd": sol_price,
        "total_value_usd": total_value_usd,
        "total_value_inr": total_value_usd * usd_inr,
        "total_invested_usd": total_invested,
        "total_pnl_usd": total_pnl_usd,
        "total_pnl_inr": total_pnl_usd * usd_inr,
        "positions": positions,
        "num_tokens": len(positions),
        "compound_stage": wallet.get("compound_stage", 0),
    }


def _find_position(chat_id: int, token_mint: str) -> Optional[dict]:
    uid = str(chat_id)
    wallets = _load_trader_wallets()
    if uid in wallets:
        for pos in wallets[uid].get("active_positions", []):
            if pos.get("token_mint") == token_mint and pos.get("status") == "active":
                return pos
    return None


# ═══════════════════════════════════════════════════════════════
#  🤖 AUTO-TRADE ENGINE — Scan + Buy + Manage + Compound
# ═══════════════════════════════════════════════════════════════

def set_trade_callback(cb):
    """Set callback for trade notifications: cb(chat_id, message)"""
    global _trade_callback
    _trade_callback = cb


def enable_auto_trade(chat_id: int) -> dict:
    """Enable auto-trading for a user."""
    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid not in wallets:
            return {"error": "No trading wallet. Create one first!"}
        wallets[uid]["auto_trade_enabled"] = True
        _save_trader_wallets(wallets)
    return {"success": True, "message": "✅ Auto-trade ENABLED! JARVIS will auto-buy gems and manage positions."}


def disable_auto_trade(chat_id: int) -> dict:
    uid = str(chat_id)
    with _wallets_lock:
        wallets = _load_trader_wallets()
        if uid in wallets:
            wallets[uid]["auto_trade_enabled"] = False
            _save_trader_wallets(wallets)
    return {"success": True, "message": "⏸️ Auto-trade DISABLED."}


def start_auto_trader():
    """Start the background auto-trading engine."""
    global _auto_trader_running, _auto_trader_thread
    if _auto_trader_running:
        return
    _auto_trader_running = True
    _auto_trader_thread = threading.Thread(target=_auto_trade_loop, daemon=True)
    _auto_trader_thread.start()
    logger.info("[REAL-TRADER] 🚀 Auto-trade engine STARTED (3-min cycle)")


def stop_auto_trader():
    global _auto_trader_running
    _auto_trader_running = False


def _notify(chat_id: int, msg: str):
    """Send notification via callback."""
    if _trade_callback and chat_id:
        try:
            _trade_callback(chat_id, msg)
        except Exception:
            pass


def _auto_trade_loop():
    """
    Background loop: every 3 minutes
    1. Scan for gem tokens (DexScreener + Pump.fun)
    2. Auto-buy best gems with available SOL
    3. Monitor existing positions for take-profit / stop-loss
    4. Auto-compound profits
    """
    # Import scan_gem_tokens from jarvis_payment
    try:
        from jarvis_payment import scan_gem_tokens
    except ImportError:
        logger.error("[REAL-TRADER] Cannot import scan_gem_tokens!")
        scan_gem_tokens = lambda: []

    while _auto_trader_running:
        try:
            wallets = _load_trader_wallets()
            for uid, wallet in wallets.items():
                if not wallet.get("auto_trade_enabled"):
                    continue

                chat_id = wallet.get("chat_id", 0)
                pubkey = wallet.get("pubkey", "")
                if not pubkey or not chat_id:
                    continue

                sol_balance = get_sol_balance(pubkey)
                sol_price = get_token_price_usd(SOL_MINT)
                usd_inr = _get_usd_inr()

                # ── STEP 1: Monitor existing positions ──
                _manage_positions(chat_id, wallet, sol_price, usd_inr)

                # ── STEP 2: Auto-buy if we have enough SOL ──
                available_sol = sol_balance - MIN_SOL_RESERVE
                if available_sol >= 0.01:  # Min 0.01 SOL to trade
                    gems = scan_gem_tokens()
                    if gems:
                        # Pick top 3 gems by score
                        top_gems = sorted(gems, key=lambda g: g.get("score", 0), reverse=True)[:3]
                        per_gem_sol = available_sol / len(top_gems)

                        if per_gem_sol >= 0.005:  # Min 0.005 SOL per token
                            for gem in top_gems:
                                token_mint = gem.get("token_id", "")
                                if not token_mint or len(token_mint) < 30:
                                    continue

                                # Check if already holding this token
                                existing = _find_position(chat_id, token_mint)
                                if existing:
                                    continue

                                result = buy_token(chat_id, token_mint, per_gem_sol)
                                if result.get("success"):
                                    gem_name = gem.get("symbol", token_mint[:8])
                                    _notify(chat_id,
                                        f"🟢 *AUTO-BUY EXECUTED!*\n\n"
                                        f"Token: {gem_name}\n"
                                        f"SOL Spent: {per_gem_sol:.4f} SOL\n"
                                        f"Score: {gem.get('score', 0):.0f}/100\n"
                                        f"TX: [Solscan]({result.get('solscan_url', '')})\n\n"
                                        f"🎯 Targets: 2x→5x→10x→50x→100x→1000x→10000x\n"
                                        f"🛡️ Stop-loss: -35%")
                                else:
                                    logger.warning(f"[REAL-TRADER] Buy failed for {token_mint[:12]}: {result.get('error', '')[:100]}")
                                time.sleep(2)  # Rate limit between trades

                # ── STEP 3: Auto-compound check ──
                _check_compound_stage(chat_id, wallet, sol_balance, sol_price, usd_inr)

        except Exception as e:
            logger.error(f"[REAL-TRADER] Auto-trade loop error: {e}")

        time.sleep(180)  # 3-minute cycle


def _manage_positions(chat_id: int, wallet: dict, sol_price: float, usd_inr: float):
    """Monitor positions for take-profit / stop-loss and execute sells."""
    positions = wallet.get("active_positions", [])
    pubkey = wallet.get("pubkey", "")
    if not positions or not pubkey:
        return

    # Get actual token balances on-chain
    on_chain_accounts = get_token_accounts(pubkey)
    on_chain_map = {acc["mint"]: acc for acc in on_chain_accounts}

    for pos in positions:
        if pos.get("status") != "active":
            continue

        token_mint = pos.get("token_mint", "")
        entry_price = pos.get("entry_price_usd", 0)
        if not token_mint or entry_price <= 0:
            continue

        current_price = get_token_price_usd(token_mint)
        if current_price <= 0:
            continue

        pnl_pct = ((current_price / entry_price) - 1) * 100

        # ── STOP LOSS ──
        stop_loss = pos.get("stop_loss_pct", -35)
        if pnl_pct <= stop_loss:
            result = sell_token(chat_id, token_mint, 100.0)
            if result.get("success"):
                sol_got = result.get("sol_received", 0)
                inr_got = sol_got * sol_price * usd_inr
                _notify(chat_id,
                    f"🔴 *AUTO STOP-LOSS TRIGGERED!*\n\n"
                    f"Token: {token_mint[:12]}...\n"
                    f"Loss: {pnl_pct:+.1f}%\n"
                    f"SOL Recovered: {sol_got:.4f} SOL (₹{inr_got:,.0f})\n"
                    f"TX: [Solscan]({result.get('solscan_url', '')})\n\n"
                    f"🛡️ Capital protection by JARVIS")
            continue

        # ── TAKE PROFIT (partial sells) ──
        taken = pos.get("profits_taken", [])
        for tp_level in pos.get("take_profit_levels", []):
            if tp_level in taken:
                continue
            if pnl_pct >= tp_level:
                # Sell 25% at each level
                sell_pct = 25
                result = sell_token(chat_id, token_mint, sell_pct)
                if result.get("success"):
                    sol_got = result.get("sol_received", 0)
                    inr_got = sol_got * sol_price * usd_inr
                    multiplier = (tp_level / 100) + 1
                    taken.append(tp_level)
                    pos["profits_taken"] = taken

                    # Update wallet
                    uid = str(chat_id)
                    with _wallets_lock:
                        wallets = _load_trader_wallets()
                        if uid in wallets:
                            wallets[uid]["total_profit_sol"] = wallets[uid].get("total_profit_sol", 0) + sol_got
                            wallets[uid]["total_profit_inr"] = wallets[uid].get("total_profit_inr", 0) + inr_got
                            # Update position
                            for p in wallets[uid].get("active_positions", []):
                                if p.get("token_mint") == token_mint and p.get("status") == "active":
                                    p["profits_taken"] = taken
                            _save_trader_wallets(wallets)

                    _notify(chat_id,
                        f"💰 *PROFIT BOOKED — {multiplier:.0f}x!*\n\n"
                        f"Token: {token_mint[:12]}...\n"
                        f"Sold: {sell_pct}% | P&L: +{pnl_pct:.1f}%\n"
                        f"SOL Received: {sol_got:.4f} SOL (₹{inr_got:,.0f})\n"
                        f"TX: [Solscan]({result.get('solscan_url', '')})\n\n"
                        f"🚀 Remaining riding for {multiplier*2:.0f}x+ ...")
                break  # Only take one profit level at a time


def _check_compound_stage(chat_id: int, wallet: dict, sol_balance: float,
                          sol_price: float, usd_inr: float):
    """Check and update compound progress: 2K→2L→2Cr→2LCr."""
    total_value_inr = sol_balance * sol_price * usd_inr
    # Add token values
    pubkey = wallet.get("pubkey", "")
    if pubkey:
        for acc in get_token_accounts(pubkey):
            price = get_token_price_usd(acc["mint"])
            total_value_inr += acc["amount"] * price * usd_inr

    current_stage = wallet.get("compound_stage", 0)

    for i, stage in enumerate(COMPOUND_STAGES):
        if i <= current_stage and total_value_inr >= stage["target_inr"]:
            if i == current_stage:
                # Stage completed!
                uid = str(chat_id)
                with _wallets_lock:
                    wallets = _load_trader_wallets()
                    if uid in wallets:
                        wallets[uid]["compound_stage"] = i + 1
                        _save_trader_wallets(wallets)

                _notify(chat_id,
                    f"🏆🎉 *COMPOUND STAGE COMPLETE!*\n\n"
                    f"📊 {stage['name']}\n"
                    f"💰 Portfolio: ₹{total_value_inr:,.0f}\n"
                    f"🎯 Target: ₹{stage['target_inr']:,.0f} ✅")

                if i + 1 < len(COMPOUND_STAGES):
                    _notify(chat_id,
                        f"🚀 Now targeting Stage {i+2}: ₹{COMPOUND_STAGES[i+1]['target_inr']:,.0f}")
                else:
                    _notify(chat_id,
                        f"🎊 ALL STAGES COMPLETE! 2K → 2L → 2Cr → 2LCr ACHIEVED! 🏆")


# ═══════════════════════════════════════════════════════════════
#  📝 FORMATTED OUTPUT — For Telegram
# ═══════════════════════════════════════════════════════════════

def format_trading_wallet(chat_id: int) -> str:
    """Format trading wallet info for Telegram."""
    wallet = get_trading_wallet(chat_id)
    if not wallet:
        return ("❌ *No Trading Wallet Found!*\n\n"
                "Create one with /create\\_wallet\n"
                "Then send SOL to start real trading! 🚀")

    pubkey = wallet["pubkey"]
    sol_balance = get_sol_balance(pubkey)
    sol_price = get_token_price_usd(SOL_MINT)
    usd_inr = _get_usd_inr()
    sol_value_inr = sol_balance * sol_price * usd_inr

    stage = wallet.get("compound_stage", 0)
    stage_name = COMPOUND_STAGES[stage]["name"] if stage < len(COMPOUND_STAGES) else "ALL COMPLETE! 🏆"
    auto_status = "🟢 ON" if wallet.get("auto_trade_enabled") else "🔴 OFF"

    total_profit_sol = wallet.get("total_profit_sol", 0)
    total_profit_inr = wallet.get("total_profit_inr", 0)
    num_trades = len(wallet.get("trades", []))
    active_pos = len([p for p in wallet.get("active_positions", []) if p.get("status") == "active"])

    return (
        f"💼🚀 *JARVIS REAL TRADING WALLET*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 *Address:*\n`{pubkey}`\n\n"
        f"💰 *SOL Balance:* {sol_balance:.4f} SOL\n"
        f"💵 *Value:* ₹{sol_value_inr:,.2f}\n\n"
        f"📊 *Trading Stats:*\n"
        f"  • Trades: {num_trades}\n"
        f"  • Active Positions: {active_pos}\n"
        f"  • Total Profit: {total_profit_sol:+.4f} SOL (₹{total_profit_inr:+,.0f})\n\n"
        f"🤖 *Auto-Trade:* {auto_status}\n"
        f"🎯 *Compound Stage:* {stage_name}\n\n"
        f"⚡ Send SOL to above address to fund trading!\n"
        f"📱 Use Phantom/Solflare to send."
    )


def format_live_portfolio(chat_id: int) -> str:
    """Format live portfolio with P&L for Telegram."""
    portfolio = get_live_portfolio(chat_id)
    if "error" in portfolio:
        return f"❌ {portfolio['error']}"

    usd_inr = _get_usd_inr()
    msg = (
        f"📊🔥 *LIVE TRADING PORTFOLIO*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 SOL: {portfolio['sol_balance']:.4f} (₹{portfolio['sol_balance'] * portfolio['sol_price_usd'] * usd_inr:,.0f})\n"
        f"📈 Total Value: ₹{portfolio['total_value_inr']:,.0f}\n"
        f"📊 P&L: ₹{portfolio['total_pnl_inr']:+,.0f}\n\n"
    )

    if portfolio["positions"]:
        msg += "🪙 *Token Holdings:*\n"
        for i, pos in enumerate(portfolio["positions"][:10], 1):
            pnl_emoji = "🟢" if pos["pnl_pct"] >= 0 else "🔴"
            msg += (
                f"\n{i}. `{pos['mint'][:12]}...`\n"
                f"   Amount: {pos['amount']:.2f}\n"
                f"   Value: ₹{pos['value_inr']:,.0f}\n"
                f"   {pnl_emoji} P&L: {pos['pnl_pct']:+.1f}%\n"
            )
    else:
        msg += "📭 No token holdings yet.\n"

    stage = portfolio.get("compound_stage", 0)
    if stage < len(COMPOUND_STAGES):
        target = COMPOUND_STAGES[stage]["target_inr"]
        progress = min(100, (portfolio["total_value_inr"] / target) * 100)
        msg += f"\n🎯 *Compound:* {COMPOUND_STAGES[stage]['name']}\n"
        msg += f"📊 Progress: {progress:.1f}% → ₹{target:,.0f}\n"

    return msg


def format_trade_history(chat_id: int, limit: int = 10) -> str:
    """Format recent trade history."""
    wallet = get_trading_wallet(chat_id)
    if not wallet:
        return "❌ No trading wallet."

    trades = wallet.get("trades", [])[-limit:]
    if not trades:
        return "📭 No trades yet. Fund your wallet and enable auto-trade!"

    msg = f"📜 *TRADE HISTORY* (Last {len(trades)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    for t in reversed(trades):
        emoji = "🟢" if t["type"] == "buy" else "🔴"
        token = t.get("token_mint", "")[:12]
        sig = t.get("signature", "")
        if t["type"] == "buy":
            msg += f"{emoji} BUY `{token}...` — {t.get('sol_spent', 0):.4f} SOL\n"
        else:
            msg += f"{emoji} SELL `{token}...` — +{t.get('sol_received', 0):.4f} SOL\n"
        msg += f"   🔗 [TX](https://solscan.io/tx/{sig})\n"
        msg += f"   📅 {t.get('timestamp', '')[:16]}\n\n"

    return msg


# ═══════════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Wallet
    "create_trading_wallet", "get_trading_wallet", "get_sol_balance",
    # Trading
    "buy_token", "sell_token", "execute_swap", "get_swap_quote",
    # Portfolio
    "get_live_portfolio", "get_token_accounts", "get_token_price_usd",
    # Auto-trade
    "enable_auto_trade", "disable_auto_trade",
    "start_auto_trader", "stop_auto_trader", "set_trade_callback",
    # Formatting
    "format_trading_wallet", "format_live_portfolio", "format_trade_history",
    # Config
    "SOLANA_SDK_AVAILABLE", "COMPOUND_STAGES",
]
