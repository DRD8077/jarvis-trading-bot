"""
SMS Alert Engine — Send trading alerts via SMS to subscribers.

Uses multiple free methods:
1. Telegram (primary — free, unlimited)
2. Fast2SMS (free tier for Indian numbers — 100 SMS/day)
3. Email-to-SMS gateway (carrier-based, free)
4. Textbelt (1 free SMS/day per IP)

Also handles smart EXIT alerts when positions are losing money.
"""

import os
import re
import time
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz

logger = logging.getLogger("sms_engine")
IST = pytz.timezone("Asia/Kolkata")

# Free SMS API keys — configure in .env
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")

# Indian carrier email-to-SMS gateways (free)
CARRIER_GATEWAYS = {
    "jio": "{phone}@jio.com",
    "airtel": "{phone}@airtelmail.com",
    "vi": "{phone}@vimail.com",
}


def validate_indian_phone(phone: str) -> Optional[str]:
    """Validate and normalize Indian phone number.
    Accepts: +91XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX
    Returns: 10-digit number or None.
    """
    phone = re.sub(r'[^0-9]', '', phone)
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]
    elif phone.startswith('0') and len(phone) == 11:
        phone = phone[1:]
    
    if len(phone) == 10 and phone[0] in '6789':
        return phone
    return None


# ═══════════════════════════════════════════════════════════
#  SMS SENDING METHODS
# ═══════════════════════════════════════════════════════════

def send_sms_fast2sms(phone: str, message: str) -> bool:
    """Send SMS via Fast2SMS (free tier: 100 SMS/day for Indian numbers)."""
    if not FAST2SMS_API_KEY:
        return False
    
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": message[:160],  # SMS limit
            "language": "english",
            "flash": 0,
            "numbers": phone,
        }
        headers = {
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        result = r.json()
        if result.get("return"):
            logger.info(f"[SMS] Fast2SMS sent to {phone}")
            return True
        else:
            logger.warning(f"[SMS] Fast2SMS failed: {result}")
            return False
    except Exception as e:
        logger.error(f"[SMS] Fast2SMS error: {e}")
        return False


def send_sms_textbelt(phone: str, message: str) -> bool:
    """Send SMS via Textbelt (1 free SMS/day)."""
    try:
        r = requests.post("https://textbelt.com/text", data={
            "phone": f"+91{phone}",
            "message": message[:160],
            "key": "textbelt",
        }, timeout=10)
        result = r.json()
        if result.get("success"):
            logger.info(f"[SMS] Textbelt sent to {phone}")
            return True
        else:
            logger.warning(f"[SMS] Textbelt failed: {result}")
            return False
    except Exception as e:
        logger.error(f"[SMS] Textbelt error: {e}")
        return False


def send_sms(phone: str, message: str) -> bool:
    """Send SMS using available methods. Tries Fast2SMS first, then Textbelt."""
    phone = validate_indian_phone(phone)
    if not phone:
        logger.error(f"[SMS] Invalid phone number")
        return False
    
    # Try Fast2SMS first
    if send_sms_fast2sms(phone, message):
        return True
    
    # Try Textbelt
    if send_sms_textbelt(phone, message):
        return True
    
    logger.warning(f"[SMS] All SMS methods failed for {phone}")
    return False


# ═══════════════════════════════════════════════════════════
#  ALERT MESSAGE BUILDERS (SMS-friendly, 160 char limit)
# ═══════════════════════════════════════════════════════════

def build_entry_sms(user_name: str, index_name: str, signal: str, strike: float,
                    premium: float, qty: int, investment: float, target: float) -> str:
    """Build SMS for entry alert."""
    action = "BUY CALL(CE)" if "CE" in signal.upper() or "BUY" in signal.upper() else "BUY PUT(PE)"
    msg = (
        f"{user_name} JI! {index_name} ALERT: "
        f"{action} Strike {strike:.0f} @ Rs{premium:.1f} "
        f"Qty:{qty} Cost:Rs{investment:.0f} "
        f"Target:Rs{target:.0f} "
        f"-DavidCrew Bot"
    )
    return msg[:160]


def build_exit_sms(user_name: str, index_name: str, reason: str,
                   entry_price: float, current_price: float, pnl: float,
                   pnl_pct: float, urgency: str = "HIGH") -> str:
    """Build SMS for exit alert."""
    if pnl >= 0:
        msg = (
            f"🟢 {user_name} JI! PROFIT BOOK {index_name}: "
            f"Entry Rs{entry_price:.0f} Now Rs{current_price:.0f} "
            f"P&L: +Rs{pnl:.0f} (+{pnl_pct:.0f}%) "
            f"BOOK PROFIT NOW! -DavidCrew"
        )
    else:
        msg = (
            f"🔴 {user_name} JI! EXIT {index_name} NOW! "
            f"Entry Rs{entry_price:.0f} Now Rs{current_price:.0f} "
            f"Loss: Rs{pnl:.0f} ({pnl_pct:.0f}%) "
            f"{reason} EXIT IN 5 MIN! -DavidCrew"
        )
    return msg[:160]


def build_market_open_sms(user_name: str, nifty_price: float, sensex_price: float,
                          nifty_signal: str, sensex_signal: str) -> str:
    """Build SMS for market open alert."""
    msg = (
        f"{user_name} JI! Market OPEN! "
        f"NIFTY:{nifty_price:.0f}({nifty_signal}) "
        f"SENSEX:{sensex_price:.0f}({sensex_signal}) "
        f"Check bot for trades! -DavidCrew"
    )
    return msg[:160]


def build_prediction_sms(user_name: str, index_name: str, direction: str,
                         confidence: float, strike: float, option_type: str,
                         investment: float, expected_profit: float) -> str:
    """Build SMS with personalized trade recommendation."""
    msg = (
        f"{user_name} JI! AI says {index_name} {direction}({confidence:.0%}) "
        f"BUY {strike:.0f}{option_type} "
        f"Invest Rs{investment:.0f} "
        f"Expected +Rs{expected_profit:.0f} "
        f"-DavidCrew"
    )
    return msg[:160]


# ═══════════════════════════════════════════════════════════
#  SMART EXIT MONITOR
# ═══════════════════════════════════════════════════════════

def check_position_health(position: Dict, current_spot: float) -> Dict[str, Any]:
    """Check if a position needs an exit alert.
    
    Returns dict with 'action' (HOLD/BOOK_PROFIT/EXIT_NOW/EXIT_URGENT)
    and 'reason'.
    """
    entry_price = position["entry_price"]
    strike = position["strike"]
    option_type = position["option_type"]
    investment = position["investment"]
    qty = position["qty"]
    entry_time = position["entry_time"]
    
    # Estimate current option premium based on spot movement
    if option_type == "CE":
        intrinsic = max(current_spot - strike, 0)
    else:
        intrinsic = max(strike - current_spot, 0)
    
    # Time decay estimation
    elapsed_mins = (time.time() - entry_time) / 60
    time_decay = max(0.5, 1 - (elapsed_mins / (6.25 * 60)))  # Full day = 6.25 hours
    
    # Estimate current premium
    if intrinsic > 0:
        estimated_premium = intrinsic + (entry_price * 0.2 * time_decay)
    else:
        # OTM — premium decays fast
        spot_move = abs(current_spot - strike) / strike
        estimated_premium = entry_price * max(0.05, 1 - spot_move * 10) * time_decay
    
    estimated_premium = max(estimated_premium, 0.05)
    
    current_value = estimated_premium * qty
    pnl = current_value - investment
    pnl_pct = (pnl / investment) * 100 if investment > 0 else 0
    
    result = {
        "estimated_premium": round(estimated_premium, 2),
        "current_value": round(current_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "action": "HOLD",
        "reason": "",
        "urgency": "LOW",
    }
    
    # Exit rules
    if pnl_pct <= -50:
        result["action"] = "EXIT_URGENT"
        result["reason"] = "LOSS >50%! Market crashed against you."
        result["urgency"] = "CRITICAL"
    elif pnl_pct <= -30:
        result["action"] = "EXIT_NOW"
        result["reason"] = "LOSS >30%. Cut losses now."
        result["urgency"] = "HIGH"
    elif pnl_pct <= -15:
        result["action"] = "EXIT_WARNING"
        result["reason"] = "Loss growing. Consider exit."
        result["urgency"] = "MEDIUM"
    elif pnl_pct >= 100:
        result["action"] = "BOOK_PROFIT"
        result["reason"] = "PROFIT 100%+! Take money off the table!"
        result["urgency"] = "HIGH"
    elif pnl_pct >= 50:
        result["action"] = "BOOK_PARTIAL"
        result["reason"] = "50%+ profit. Book partial. Trail SL."
        result["urgency"] = "MEDIUM"
    elif pnl_pct >= 20:
        result["action"] = "TRAIL_SL"
        result["reason"] = "Good profit. Set trailing stop-loss."
        result["urgency"] = "LOW"
    elif elapsed_mins > 300:  # > 5 hours
        if pnl_pct < 5:
            result["action"] = "EXIT_EOD"
            result["reason"] = "Near closing. Small P&L. Exit before decay."
            result["urgency"] = "MEDIUM"
    
    return result


# ═══════════════════════════════════════════════════════════
#  BULK SEND TO ALL SMS SUBSCRIBERS
# ═══════════════════════════════════════════════════════════

def send_bulk_sms_alert(message_builder_fn, **kwargs) -> int:
    """Send SMS to all active subscribers. Returns count of successful sends."""
    from data_store import list_active_sms_subscribers
    
    subscribers = list_active_sms_subscribers()
    sent = 0
    
    for sub in subscribers:
        phone = sub["phone"]
        user_name = sub.get("user_name", "Trader")
        investment = sub.get("investment_amount", 2000)
        
        try:
            msg = message_builder_fn(
                user_name=user_name,
                investment=investment,
                **kwargs
            )
            
            if send_sms(phone, msg):
                sent += 1
                time.sleep(0.5)  # Rate limit
        except Exception as e:
            logger.error(f"[SMS] Failed for {phone}: {e}")
    
    logger.info(f"[SMS] Bulk send complete: {sent}/{len(subscribers)} delivered")
    return sent


# ═══════════════════════════════════════════════════════════
#  VERIFICATION / WELCOME SMS
# ═══════════════════════════════════════════════════════════

def build_verification_sms(user_name: str, trade_info: str = "") -> str:
    """Build verification SMS sent immediately after phone registration."""
    msg = (
        f"{user_name} JI! Welcome to DavidCrew Trading Bot! "
        f"SMS alerts ACTIVE on this number. "
    )
    if trade_info:
        msg += trade_info + " "
    msg += "-DavidCrew Bot"
    return msg[:160]


# ═══════════════════════════════════════════════════════════
#  TELEGRAM-BASED "SMS" (always works, free)
# ═══════════════════════════════════════════════════════════

def send_telegram_sms_style(chat_id: int, message: str, bot_token: str = None) -> bool:
    """Send a Telegram message styled like an SMS alert (short, urgent)."""
    if not bot_token:
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"[TG-SMS] Failed for {chat_id}: {e}")
        return False
