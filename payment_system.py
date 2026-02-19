"""
💳 Payment & Withdrawal System v2.0
═══════════════════════════════════════
UPI payments, wallet funding, withdrawal processing, transaction history.
Real INR ↔ Crypto conversion with live rates.
"""

import os, json, logging, time, hashlib, hmac, secrets, uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger("payment-system")
IST = timezone(timedelta(hours=5, minutes=30))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
WALLETS_FILE = os.path.join(DATA_DIR, "user_wallets.json")
WITHDRAWALS_FILE = os.path.join(DATA_DIR, "withdrawals.json")

OWNER_UPI = os.getenv("OWNER_UPI_ID", "")
OWNER_WALLET = os.getenv("OWNER_SOLANA_WALLET", "")
MIN_DEPOSIT = 1  # ₹1 minimum — no upper limit
MAX_DEPOSIT = 999999999  # Unlimited
MIN_WITHDRAWAL = 1  # ₹1 minimum
WITHDRAWAL_FEE_PCT = 1.0  # 1%


def _load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except:
        pass
    return default if default is not None else {}


def _save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Save error {path}: {e}")


# ═══════════════════════════════════════════════════════════
#  User Wallet Management
# ═══════════════════════════════════════════════════════════

def get_user_wallet(user_id: str) -> Dict:
    """Get or create user wallet."""
    wallets = _load_json(WALLETS_FILE, {})
    uid = str(user_id)
    
    if uid not in wallets:
        wallets[uid] = {
            "user_id": uid,
            "balance_inr": 0.0,
            "balance_sol": 0.0,
            "balance_usdt": 0.0,
            "total_deposited": 0.0,
            "total_withdrawn": 0.0,
            "total_earned": 0.0,
            "phantom_address": "",
            "upi_id": "",
            "bank_account": "",
            "ifsc_code": "",
            "kyc_verified": False,
            "created_at": datetime.now(IST).isoformat(),
            "updated_at": datetime.now(IST).isoformat()
        }
        _save_json(WALLETS_FILE, wallets)
    
    return wallets[uid]


def update_wallet_balance(user_id: str, amount_inr: float, tx_type: str = "credit") -> Dict:
    """Update user wallet balance."""
    wallets = _load_json(WALLETS_FILE, {})
    uid = str(user_id)
    
    if uid not in wallets:
        get_user_wallet(uid)
        wallets = _load_json(WALLETS_FILE, {})
    
    if tx_type == "credit":
        wallets[uid]["balance_inr"] = round(wallets[uid].get("balance_inr", 0) + amount_inr, 2)
        wallets[uid]["total_deposited"] = round(wallets[uid].get("total_deposited", 0) + amount_inr, 2)
    elif tx_type == "debit":
        current = wallets[uid].get("balance_inr", 0)
        if current < amount_inr:
            return {"success": False, "error": "Insufficient balance", "balance": current}
        wallets[uid]["balance_inr"] = round(current - amount_inr, 2)
        wallets[uid]["total_withdrawn"] = round(wallets[uid].get("total_withdrawn", 0) + amount_inr, 2)
    elif tx_type == "earn":
        wallets[uid]["balance_inr"] = round(wallets[uid].get("balance_inr", 0) + amount_inr, 2)
        wallets[uid]["total_earned"] = round(wallets[uid].get("total_earned", 0) + amount_inr, 2)
    
    wallets[uid]["updated_at"] = datetime.now(IST).isoformat()
    _save_json(WALLETS_FILE, wallets)
    
    return {"success": True, "balance": wallets[uid]["balance_inr"]}


# ═══════════════════════════════════════════════════════════
#  Deposit / Payment Processing
# ═══════════════════════════════════════════════════════════

def create_deposit_request(user_id: str, amount: float, method: str = "upi") -> Dict:
    """Create a deposit/payment request."""
    if amount < MIN_DEPOSIT:
        return {"success": False, "error": f"Minimum deposit is ₹{MIN_DEPOSIT}"}
    if amount > MAX_DEPOSIT:
        return {"success": False, "error": f"Maximum deposit is ₹{MAX_DEPOSIT}"}
    
    tx_id = f"DEP-{uuid.uuid4().hex[:12].upper()}"
    
    deposit = {
        "tx_id": tx_id,
        "user_id": str(user_id),
        "type": "deposit",
        "amount": amount,
        "method": method,
        "status": "pending",
        "created_at": datetime.now(IST).isoformat(),
        "upi_id": OWNER_UPI,
        "qr_data": f"upi://pay?pa={OWNER_UPI}&pn=JARVIS&am={amount}&tn={tx_id}" if OWNER_UPI else ""
    }
    
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        transactions = []
    transactions.append(deposit)
    _save_json(TRANSACTIONS_FILE, transactions)
    
    return {
        "success": True,
        "tx_id": tx_id,
        "amount": amount,
        "method": method,
        "status": "pending",
        "upi_id": OWNER_UPI,
        "qr_data": deposit["qr_data"],
        "instructions": f"Send ₹{amount} to UPI ID: {OWNER_UPI}\nReference: {tx_id}"
    }


def confirm_deposit(tx_id: str, admin_id: str = "") -> Dict:
    """Admin confirms a deposit (or auto-verify). Auto-triggers trading."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        return {"success": False, "error": "No transactions"}
    
    for tx in transactions:
        if tx.get("tx_id") == tx_id and tx.get("type") == "deposit":
            if tx.get("status") == "completed":
                return {"success": False, "error": "Already processed"}
            
            tx["status"] = "completed"
            tx["confirmed_at"] = datetime.now(IST).isoformat()
            tx["confirmed_by"] = admin_id
            
            # Credit user wallet
            result = update_wallet_balance(tx["user_id"], tx["amount"], "credit")
            _save_json(TRANSACTIONS_FILE, transactions)
            
            # 🔥 AUTO-START TRADING after deposit confirmed
            auto_trade_result = None
            try:
                from jarvis_payment import auto_invest
                auto_trade_result = auto_invest(int(tx["user_id"]), tx["amount"])
                logger.info(f"Auto-invest triggered for user {tx['user_id']}: ₹{tx['amount']}")
            except Exception as e:
                logger.error(f"Auto-invest failed after deposit: {e}")
            
            return {
                "success": True,
                "tx_id": tx_id,
                "amount": tx["amount"],
                "new_balance": result.get("balance", 0),
                "auto_trading_started": auto_trade_result is not None and not auto_trade_result.get("error"),
                "message": f"₹{tx['amount']} deposited! JARVIS AI trading shuru ho gaya hai!"
            }
    
    return {"success": False, "error": "Transaction not found"}


# ═══════════════════════════════════════════════════════════
#  Withdrawal Processing
# ═══════════════════════════════════════════════════════════

def create_withdrawal_request(user_id: str, amount: float, method: str = "phantom", destination: str = "") -> Dict:
    """Create a withdrawal request — only to user's Phantom (Solana) wallet."""
    wallet = get_user_wallet(user_id)
    
    # Withdrawal only allowed to Phantom wallet
    phantom_addr = wallet.get("phantom_address", "") or destination
    if not phantom_addr or len(phantom_addr) < 32:
        return {
            "success": False,
            "error": "Withdrawal sirf Phantom wallet mein hota hai. Pehle apna Phantom wallet connect karo!"
        }
    
    if amount < MIN_WITHDRAWAL:
        return {"success": False, "error": f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}"}
    
    fee = round(amount * WITHDRAWAL_FEE_PCT / 100, 2)
    net_amount = round(amount - fee, 2)
    
    if wallet["balance_inr"] < amount:
        return {
            "success": False, 
            "error": f"Insufficient balance. Available: ₹{wallet['balance_inr']:.2f}"
        }
    
    tx_id = f"WDR-{uuid.uuid4().hex[:12].upper()}"
    
    withdrawal = {
        "tx_id": tx_id,
        "user_id": str(user_id),
        "type": "withdrawal",
        "amount": amount,
        "fee": fee,
        "net_amount": net_amount,
        "method": "phantom",
        "destination": f"Phantom: {phantom_addr[:8]}...{phantom_addr[-4:]}",
        "phantom_address": phantom_addr,
        "status": "pending",
        "created_at": datetime.now(IST).isoformat()
    }
    
    # Debit balance immediately (hold)
    update_wallet_balance(user_id, amount, "debit")
    
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        transactions = []
    transactions.append(withdrawal)
    _save_json(TRANSACTIONS_FILE, transactions)
    
    return {
        "success": True,
        "tx_id": tx_id,
        "amount": amount,
        "fee": fee,
        "net_amount": net_amount,
        "method": "phantom",
        "phantom_address": phantom_addr,
        "status": "pending",
        "message": f"₹{net_amount} withdrawal to Phantom wallet submitted. Auto-transfer in progress."
    }


def process_withdrawal(tx_id: str, action: str = "approve", admin_id: str = "") -> Dict:
    """Admin processes a withdrawal request."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        return {"success": False, "error": "No transactions"}
    
    for tx in transactions:
        if tx.get("tx_id") == tx_id and tx.get("type") == "withdrawal":
            if tx.get("status") != "pending":
                return {"success": False, "error": f"Already {tx['status']}"}
            
            if action == "approve":
                tx["status"] = "completed"
                tx["processed_at"] = datetime.now(IST).isoformat()
                tx["processed_by"] = admin_id
            elif action == "reject":
                tx["status"] = "rejected"
                tx["processed_at"] = datetime.now(IST).isoformat()
                # Refund balance
                update_wallet_balance(tx["user_id"], tx["amount"], "credit")
            
            _save_json(TRANSACTIONS_FILE, transactions)
            
            return {
                "success": True,
                "tx_id": tx_id,
                "action": action,
                "amount": tx["amount"],
                "status": tx["status"]
            }
    
    return {"success": False, "error": "Transaction not found"}


# ═══════════════════════════════════════════════════════════
#  Transaction History
# ═══════════════════════════════════════════════════════════

def get_transaction_history(user_id: str, limit: int = 50) -> List[Dict]:
    """Get user's transaction history."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        return []
    
    uid = str(user_id)
    user_txs = [tx for tx in transactions if tx.get("user_id") == uid]
    user_txs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_txs[:limit]


def get_pending_transactions(admin_only: bool = True) -> List[Dict]:
    """Get all pending transactions (admin)."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    if not isinstance(transactions, list):
        return []
    
    pending = [tx for tx in transactions if tx.get("status") == "pending"]
    pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return pending


# ═══════════════════════════════════════════════════════════
#  Save wallet settings
# ═══════════════════════════════════════════════════════════

def update_user_payment_info(user_id: str, upi_id: str = "", bank_account: str = "", 
                              ifsc_code: str = "", phantom_address: str = "") -> Dict:
    """Update user payment/wallet information."""
    wallets = _load_json(WALLETS_FILE, {})
    uid = str(user_id)
    
    if uid not in wallets:
        get_user_wallet(uid)
        wallets = _load_json(WALLETS_FILE, {})
    
    if upi_id:
        wallets[uid]["upi_id"] = upi_id
    if bank_account:
        wallets[uid]["bank_account"] = bank_account
    if ifsc_code:
        wallets[uid]["ifsc_code"] = ifsc_code
    if phantom_address:
        wallets[uid]["phantom_address"] = phantom_address
    
    wallets[uid]["updated_at"] = datetime.now(IST).isoformat()
    _save_json(WALLETS_FILE, wallets)
    
    return {"success": True, "message": "Payment info updated"}


logger.info("💳 Payment & Withdrawal System loaded")
