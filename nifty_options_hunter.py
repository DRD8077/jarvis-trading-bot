"""
🎯 NIFTY OPTIONS HUNTER — Budget ₹4-5 Option Finder + Auto Alerts + Position Guardian
═══════════════════════════════════════════════════════════════════════════════════════

Features:
1. 💰 Budget Option Finder — Find NIFTY/SENSEX options at ₹4-5 with ₹200-300 potential
2. 🔔 9 AM Auto-Pick Engine — Pre-market call/put recommendations
3. 🛡️ Position Guardian — Trail SL, auto-protect, loss prevention
4. 🧠 AI/ML Scoring — Multi-indicator option scoring
5. 🚨 STOP ALL Alerts — Instant kill switch for crypto/all notifications
"""

import os
import json
import time
import math
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
#  CONSTANTS & CONFIG
# ═══════════════════════════════════════════════════════════

try:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")
except ImportError:
    from datetime import timezone
    IST = timezone(timedelta(hours=5, minutes=30))

RISK_FREE_RATE = 0.065  # RBI repo rate ~6.5%
NIFTY_LOT_SIZE = 25
SENSEX_LOT_SIZE = 10  # BSE SENSEX options
BANKNIFTY_LOT_SIZE = 15

# Budget range for hunting
MIN_PREMIUM = 2.0   # ₹2 minimum (very cheap)
MAX_PREMIUM = 8.0   # ₹8 maximum budget
TARGET_PREMIUM = 5.0 # ₹4-5 sweet spot
TARGET_RETURN = 200  # Target ₹200-300 return

# Position Guardian
TRAIL_SL_LEVELS = [
    {"profit_pct": 100, "trail_to_pct": 70},   # 100%+ profit → trail SL to 70%
    {"profit_pct": 60,  "trail_to_pct": 40},    # 60%+ → trail to 40%
    {"profit_pct": 30,  "trail_to_pct": 15},    # 30%+ → trail to 15%
    {"profit_pct": 20,  "trail_to_pct": 5},     # 20%+ → trail to cost+5%
]

EXIT_RULES = {
    "LOSS_CRITICAL": {"threshold": -50, "action": "EXIT_NOW", "urgency": "🚨 CRITICAL"},
    "LOSS_HIGH":     {"threshold": -35, "action": "EXIT_NOW", "urgency": "⚠️ HIGH"},
    "LOSS_MEDIUM":   {"threshold": -20, "action": "EXIT_WARNING", "urgency": "⚡ MEDIUM"},
    "PROFIT_MEGA":   {"threshold": 200, "action": "BOOK_ALL", "urgency": "💰💰💰 MEGA"},
    "PROFIT_BIG":    {"threshold": 100, "action": "BOOK_PROFIT", "urgency": "💰💰 BIG"},
    "PROFIT_GOOD":   {"threshold": 50,  "action": "BOOK_PARTIAL", "urgency": "💰 GOOD"},
}

# Persistence file for user alert preferences
ALERT_PREFS_FILE = "jarvis_alert_prefs.json"
POSITION_GUARDIAN_FILE = "jarvis_positions_guardian.json"

# ═══════════════════════════════════════════════════════════
#  ALERT PREFERENCE MANAGER — Stop/Start All
# ═══════════════════════════════════════════════════════════

_alert_prefs_cache = {}
_prefs_lock = threading.Lock()


def _load_alert_prefs() -> dict:
    """Load alert preferences from disk."""
    global _alert_prefs_cache
    try:
        if os.path.exists(ALERT_PREFS_FILE):
            with open(ALERT_PREFS_FILE, "r") as f:
                _alert_prefs_cache = json.load(f)
    except Exception:
        _alert_prefs_cache = {}
    return _alert_prefs_cache


def _save_alert_prefs():
    """Save alert preferences to disk."""
    try:
        with open(ALERT_PREFS_FILE, "w") as f:
            json.dump(_alert_prefs_cache, f, indent=2)
    except Exception as e:
        logger.error(f"Save prefs error: {e}")


def get_user_prefs(chat_id: int) -> dict:
    """Get alert preferences for a user."""
    with _prefs_lock:
        if not _alert_prefs_cache:
            _load_alert_prefs()
        key = str(chat_id)
        if key not in _alert_prefs_cache:
            _alert_prefs_cache[key] = {
                "crypto_alerts": True,
                "stock_alerts": True,
                "option_alerts": True,
                "morning_picks": True,
                "position_guardian": True,
                "mode": "ALL",  # ALL, STOCKS_ONLY, CRYPTO_ONLY
                "budget_min": 3,
                "budget_max": 8,
            }
            _save_alert_prefs()
        return _alert_prefs_cache[key]


def set_user_pref(chat_id: int, key: str, value) -> dict:
    """Set a specific alert preference."""
    with _prefs_lock:
        prefs = get_user_prefs(chat_id)
        prefs[key] = value
        _alert_prefs_cache[str(chat_id)] = prefs
        _save_alert_prefs()
        return prefs


def stop_all_crypto_alerts(chat_id: int) -> str:
    """Instantly stop ALL crypto notifications for user."""
    with _prefs_lock:
        prefs = get_user_prefs(chat_id)
        prefs["crypto_alerts"] = False
        prefs["mode"] = "STOCKS_ONLY"
        _alert_prefs_cache[str(chat_id)] = prefs
        _save_alert_prefs()

    return (
        "🛑🛑🛑 *ALL CRYPTO ALERTS — STOPPED* 🛑🛑🛑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Crypto gem alerts: *OFF*\n"
        "✅ Crypto pump alerts: *OFF*\n"
        "✅ Crypto dip alerts: *OFF*\n"
        "✅ Whale alerts: *OFF*\n"
        "✅ DexTools alerts: *OFF*\n"
        "✅ Airdrop alerts: *OFF*\n\n"
        "🇮🇳 *Mode: INDIAN STOCKS ONLY* 🇮🇳\n"
        "Ab sirf NIFTY/SENSEX/BankNIFTY alerts aayenge!\n\n"
        "💡 _Crypto wapas ON karne ke liye:_\n"
        '    "🔔 Crypto Alerts ON/OFF" button dabao\n\n'
        "🔥 *Active Alerts:*\n"
        "┣ 📊 NIFTY/SENSEX Call/Put picks\n"
        "┣ 🔔 9 AM Morning Auto-Picks\n"
        "┣ 🛡️ Position Guardian (SL alerts)\n"
        "┣ 📈 Market trend alerts\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def start_all_crypto_alerts(chat_id: int) -> str:
    """Re-enable all crypto alerts."""
    with _prefs_lock:
        prefs = get_user_prefs(chat_id)
        prefs["crypto_alerts"] = True
        prefs["mode"] = "ALL"
        _alert_prefs_cache[str(chat_id)] = prefs
        _save_alert_prefs()

    return (
        "🔔🟢 *ALL CRYPTO ALERTS — RE-ENABLED* 🟢🔔\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Crypto gem alerts: *ON*\n"
        "✅ Crypto pump alerts: *ON*\n"
        "✅ Whale alerts: *ON*\n\n"
        "🇮🇳🪙 *Mode: ALL MARKETS* 🪙🇮🇳\n"
        "Stocks + Crypto dono ke alerts aayenge!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def is_crypto_alerts_enabled(chat_id: int) -> bool:
    """Check if crypto alerts are enabled for user."""
    prefs = get_user_prefs(chat_id)
    return prefs.get("crypto_alerts", True)


# ═══════════════════════════════════════════════════════════
#  BLACK-SCHOLES ENGINE (for budget option pricing)
# ═══════════════════════════════════════════════════════════

def _norm_cdf(x):
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_pdf(x):
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def bs_price(S, K, T, r, sigma, option_type="CE"):
    """Black-Scholes option price."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return max(0, (S - K) if option_type == "CE" else (K - S))

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "CE":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def bs_delta(S, K, T, r, sigma, option_type="CE"):
    """Option delta."""
    if T <= 0 or sigma <= 0:
        return 0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    if option_type == "CE":
        return _norm_cdf(d1)
    else:
        return _norm_cdf(d1) - 1


def bs_gamma(S, K, T, r, sigma):
    """Option gamma."""
    if T <= 0 or sigma <= 0:
        return 0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    return _norm_pdf(d1) / (S * sigma * math.sqrt(T))


def bs_theta(S, K, T, r, sigma, option_type="CE"):
    """Option theta (per day)."""
    if T <= 0 or sigma <= 0:
        return 0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    term1 = -(S * _norm_pdf(d1) * sigma) / (2 * math.sqrt(T))
    if option_type == "CE":
        term2 = -r * K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        term2 = r * K * math.exp(-r * T) * _norm_cdf(-d2)
    return (term1 + term2) / 365


def implied_vol_from_price(S, K, T, r, market_price, option_type="CE"):
    """Newton-Raphson IV solver."""
    sigma = 0.3
    for _ in range(50):
        price = bs_price(S, K, T, r, sigma, option_type)
        vega = S * _norm_pdf(
            (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        ) * math.sqrt(T)
        if vega < 1e-8:
            break
        sigma = sigma - (price - market_price) / vega
        sigma = max(0.01, min(5.0, sigma))
    return sigma


# ═══════════════════════════════════════════════════════════
#  BUDGET OPTION HUNTER — Find ₹4-5 calls/puts
# ═══════════════════════════════════════════════════════════

def _get_live_price(symbol: str) -> float:
    """Get live index price."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception:
        pass
    return 0.0


def _get_historical_volatility(symbol: str, days: int = 30) -> float:
    """Calculate historical volatility."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        if len(hist) < 20:
            return 0.15
        returns = hist['Close'].pct_change().dropna()
        vol = float(returns.tail(days).std() * (252 ** 0.5))
        return max(0.08, min(0.50, vol))
    except Exception:
        return 0.15


def _get_ml_direction(symbol: str, name: str) -> dict:
    """Get ML prediction for direction."""
    try:
        from ml_predictor import predict_index_direction
        result = predict_index_direction(symbol, name)
        if "error" not in result:
            return result
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "probability": 0.5}


def _get_technical_signal(symbol: str) -> dict:
    """Get buy/sell signal from technical engine."""
    try:
        from buy_sell_engine import generate_buy_sell_signal
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d")
        if len(df) >= 15:
            signal = generate_buy_sell_signal(df, symbol)
            return signal
    except Exception:
        pass
    return {"signal": "HOLD", "score": 50, "strength": "NEUTRAL"}


def _get_candle_pattern(symbol: str) -> dict:
    """Get candle pattern analysis."""
    try:
        from candle_analyzer import analyze_candles_for_index
        result = analyze_candles_for_index(symbol.replace("^", ""))
        if result:
            return result
    except Exception:
        pass
    return {"pattern": "None", "signal": "NEUTRAL"}


def _days_to_expiry() -> float:
    """Calculate days to next weekly expiry (Thursday)."""
    now = datetime.now(IST)
    days_ahead = 3 - now.weekday()  # Thursday = 3
    if days_ahead <= 0:
        days_ahead += 7
    expiry = now + timedelta(days=days_ahead)
    expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
    diff = (expiry - now).total_seconds() / 86400
    return max(0.01, diff)


def find_budget_options(index: str = "NIFTY", direction: str = "AUTO",
                        budget_min: float = 3.0, budget_max: float = 8.0) -> dict:
    """
    🎯 Find budget options (₹3-8) that have potential to reach ₹200-300.

    Uses: Live price + Historical volatility + ML direction + Technical signals
          + Black-Scholes pricing to find optimal OTM strikes.
    """
    config = {
        "NIFTY":     {"symbol": "^NSEI", "name": "NIFTY 50", "lot": 25, "step": 50},
        "SENSEX":    {"symbol": "^BSESN", "name": "SENSEX", "lot": 10, "step": 100},
        "BANKNIFTY": {"symbol": "^NSEBANK", "name": "Bank NIFTY", "lot": 15, "step": 100},
    }

    cfg = config.get(index.upper(), config["NIFTY"])
    symbol = cfg["symbol"]
    lot = cfg["lot"]
    step = cfg["step"]

    # Get live data
    spot = _get_live_price(symbol)
    if spot <= 0:
        return {"error": f"{index} price not available"}

    # Get volatility
    hv = _get_historical_volatility(symbol)

    # Get ML direction
    ml = _get_ml_direction(symbol, cfg["name"])
    ml_dir = ml.get("direction", "NEUTRAL")
    ml_conf = ml.get("confidence", 50)
    ml_prob = ml.get("probability", 0.5)

    # Get technical signal
    tech = _get_technical_signal(symbol)
    tech_signal = tech.get("signal", "HOLD")
    tech_score = tech.get("score", 50)

    # Determine direction
    if direction == "AUTO":
        bullish_score = 0
        if ml_dir == "UP":
            bullish_score += 2
        elif ml_dir == "DOWN":
            bullish_score -= 2

        if "BUY" in tech_signal:
            bullish_score += 1
        elif "SELL" in tech_signal:
            bullish_score -= 1

        if ml_prob > 0.6:
            bullish_score += 1
        elif ml_prob < 0.4:
            bullish_score -= 1

        if bullish_score >= 1:
            direction = "BULLISH"
        elif bullish_score <= -1:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

    # Days to expiry
    dte = _days_to_expiry()
    T = dte / 365

    # Use slightly elevated IV for OTM pricing (skew)
    iv_base = max(hv, 0.12)
    iv_otm = iv_base * 1.15  # OTM skew premium

    # Generate strikes and find budget options
    atm_strike = round(spot / step) * step
    results = {"calls": [], "puts": []}

    # Scan OTM calls (above spot)
    for i in range(1, 30):
        strike = atm_strike + i * step
        try:
            price = bs_price(spot, strike, T, RISK_FREE_RATE, iv_otm, "CE")
            if price < 0.5:
                break  # Too far OTM
            if budget_min <= price <= budget_max:
                delta = bs_delta(spot, strike, T, RISK_FREE_RATE, iv_otm, "CE")
                gamma = bs_gamma(spot, strike, T, RISK_FREE_RATE, iv_otm)
                theta = bs_theta(spot, strike, T, RISK_FREE_RATE, iv_otm, "CE")

                # Calculate potential: what price becomes if spot moves 2-3%
                spot_up_2 = spot * 1.02
                spot_up_3 = spot * 1.03
                spot_up_5 = spot * 1.05
                price_2pct = bs_price(spot_up_2, strike, max(T - 1/365, 0.001), RISK_FREE_RATE, iv_otm, "CE")
                price_3pct = bs_price(spot_up_3, strike, max(T - 1/365, 0.001), RISK_FREE_RATE, iv_otm, "CE")
                price_5pct = bs_price(spot_up_5, strike, max(T - 2/365, 0.001), RISK_FREE_RATE, iv_otm, "CE")

                # Score this option
                score = 0
                # Prefer options closer to ₹4-5 (sweet spot)
                distance_from_target = abs(price - TARGET_PREMIUM)
                score += max(0, 10 - distance_from_target * 3)
                # High return potential
                if price_3pct > 0 and price > 0:
                    potential_return = (price_3pct / price - 1) * 100
                    score += min(30, potential_return / 5)
                # High gamma = more explosive
                score += min(10, gamma * 10000)
                # Delta sweet spot (0.05-0.20)
                if 0.05 <= abs(delta) <= 0.25:
                    score += 10
                # ML alignment
                if direction == "BULLISH":
                    score += 15

                results["calls"].append({
                    "strike": strike,
                    "premium": round(price, 2),
                    "delta": round(delta, 4),
                    "gamma": round(gamma, 6),
                    "theta": round(theta, 2),
                    "otm_pct": round((strike - spot) / spot * 100, 2),
                    "lot_cost": round(price * lot, 0),
                    "if_2pct_up": round(price_2pct, 2),
                    "if_3pct_up": round(price_3pct, 2),
                    "if_5pct_up": round(price_5pct, 2),
                    "potential_return_3pct": round((price_3pct / price - 1) * 100, 1) if price > 0 else 0,
                    "potential_return_5pct": round((price_5pct / price - 1) * 100, 1) if price > 0 else 0,
                    "score": round(score, 1),
                })
        except Exception:
            continue

    # Scan OTM puts (below spot)
    for i in range(1, 30):
        strike = atm_strike - i * step
        if strike <= 0:
            break
        try:
            price = bs_price(spot, strike, T, RISK_FREE_RATE, iv_otm, "PE")
            if price < 0.5:
                break
            if budget_min <= price <= budget_max:
                delta = bs_delta(spot, strike, T, RISK_FREE_RATE, iv_otm, "PE")
                gamma = bs_gamma(spot, strike, T, RISK_FREE_RATE, iv_otm)
                theta = bs_theta(spot, strike, T, RISK_FREE_RATE, iv_otm, "PE")

                spot_dn_2 = spot * 0.98
                spot_dn_3 = spot * 0.97
                spot_dn_5 = spot * 0.95
                price_2pct = bs_price(spot_dn_2, strike, max(T - 1/365, 0.001), RISK_FREE_RATE, iv_otm, "PE")
                price_3pct = bs_price(spot_dn_3, strike, max(T - 1/365, 0.001), RISK_FREE_RATE, iv_otm, "PE")
                price_5pct = bs_price(spot_dn_5, strike, max(T - 2/365, 0.001), RISK_FREE_RATE, iv_otm, "PE")

                score = 0
                distance_from_target = abs(price - TARGET_PREMIUM)
                score += max(0, 10 - distance_from_target * 3)
                if price_3pct > 0 and price > 0:
                    potential_return = (price_3pct / price - 1) * 100
                    score += min(30, potential_return / 5)
                score += min(10, gamma * 10000)
                if 0.05 <= abs(delta) <= 0.25:
                    score += 10
                if direction == "BEARISH":
                    score += 15

                results["puts"].append({
                    "strike": strike,
                    "premium": round(price, 2),
                    "delta": round(delta, 4),
                    "gamma": round(gamma, 6),
                    "theta": round(theta, 2),
                    "otm_pct": round((spot - strike) / spot * 100, 2),
                    "lot_cost": round(price * lot, 0),
                    "if_2pct_down": round(price_2pct, 2),
                    "if_3pct_down": round(price_3pct, 2),
                    "if_5pct_down": round(price_5pct, 2),
                    "potential_return_3pct": round((price_3pct / price - 1) * 100, 1) if price > 0 else 0,
                    "potential_return_5pct": round((price_5pct / price - 1) * 100, 1) if price > 0 else 0,
                    "score": round(score, 1),
                })
        except Exception:
            continue

    # Sort by score
    results["calls"].sort(key=lambda x: x["score"], reverse=True)
    results["puts"].sort(key=lambda x: x["score"], reverse=True)

    return {
        "index": index,
        "spot": spot,
        "hv": round(hv * 100, 1),
        "iv_used": round(iv_otm * 100, 1),
        "dte": round(dte, 1),
        "ml_direction": ml_dir,
        "ml_confidence": ml_conf,
        "ml_probability": round(ml_prob * 100, 1),
        "tech_signal": tech_signal,
        "tech_score": tech_score,
        "ai_direction": direction,
        "calls": results["calls"][:5],
        "puts": results["puts"][:5],
        "lot_size": lot,
        "timestamp": datetime.now(IST).strftime("%d-%b %I:%M %p"),
    }


def format_budget_options(data: dict) -> str:
    """Format budget options for Telegram."""
    if "error" in data:
        return f"❌ {data['error']}"

    idx = data["index"]
    spot = data["spot"]
    direction = data["ai_direction"]

    dir_emoji = "🟢 BULLISH" if direction == "BULLISH" else "🔴 BEARISH" if direction == "BEARISH" else "🟡 NEUTRAL"

    msg = (
        f"🎯💰 *{idx} BUDGET OPTIONS HUNTER* 💰🎯\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *{idx} Spot:* ₹{spot:,.1f}\n"
        f"📅 *Days to Expiry:* {data['dte']:.1f} days\n"
        f"📉 *Volatility:* HV {data['hv']}% | IV {data['iv_used']}%\n\n"
        f"🧠 *AI Direction:* {dir_emoji}\n"
        f"┣ ML: {data['ml_direction']} ({data['ml_confidence']}% conf)\n"
        f"┣ Technical: {data['tech_signal']} (Score: {data['tech_score']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # CALLS
    if data["calls"]:
        msg += "📗 *CALL OPTIONS (₹4-8 Budget):*\n"
        msg += "_Index ↑ gaya to ye calls profit denge_\n\n"
        for i, c in enumerate(data["calls"][:3], 1):
            star = "⭐" * min(5, max(1, int(c["score"] / 15)))
            msg += (
                f"*{i}. {idx} {c['strike']} CE* {star}\n"
                f"   💰 Premium: *₹{c['premium']}* (Lot: ₹{c['lot_cost']:,.0f})\n"
                f"   📊 Delta: {c['delta']} | OTM: {c['otm_pct']}%\n"
                f"   🎯 2% move: ₹{c['if_2pct_up']} | 3%: ₹{c['if_3pct_up']}\n"
                f"   🚀 5% move: *₹{c['if_5pct_up']}* (+{c['potential_return_5pct']}%)\n"
                f"   📈 Score: {c['score']}/100\n\n"
            )
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # PUTS
    if data["puts"]:
        msg += "📕 *PUT OPTIONS (₹4-8 Budget):*\n"
        msg += "_Index ↓ gaya to ye puts profit denge_\n\n"
        for i, p in enumerate(data["puts"][:3], 1):
            star = "⭐" * min(5, max(1, int(p["score"] / 15)))
            msg += (
                f"*{i}. {idx} {p['strike']} PE* {star}\n"
                f"   💰 Premium: *₹{p['premium']}* (Lot: ₹{p['lot_cost']:,.0f})\n"
                f"   📊 Delta: {p['delta']} | OTM: {p['otm_pct']}%\n"
                f"   🎯 2% down: ₹{p['if_2pct_down']} | 3%: ₹{p['if_3pct_down']}\n"
                f"   🚀 5% down: *₹{p['if_5pct_down']}* (+{p['potential_return_5pct']}%)\n"
                f"   📈 Score: {p['score']}/100\n\n"
            )

    # Recommendation
    if direction == "BULLISH" and data["calls"]:
        best = data["calls"][0]
        msg += (
            f"🏆 *JARVIS PICK:* {idx} {best['strike']} CE @ ₹{best['premium']}\n"
            f"🎯 Target: ₹{best['if_5pct_up']} | SL: ₹{max(1, best['premium'] - 2)}\n"
            f"💡 _₹{best['premium']} → ₹{best['if_5pct_up']} ka potential!_\n"
        )
    elif direction == "BEARISH" and data["puts"]:
        best = data["puts"][0]
        msg += (
            f"🏆 *JARVIS PICK:* {idx} {best['strike']} PE @ ₹{best['premium']}\n"
            f"🎯 Target: ₹{best['if_5pct_down']} | SL: ₹{max(1, best['premium'] - 2)}\n"
            f"💡 _₹{best['premium']} → ₹{best['if_5pct_down']} ka potential!_\n"
        )
    else:
        msg += (
            "⚠️ *Direction unclear — wait for confirmation*\n"
            "💡 _Jab clear signal aaye tab entry lo_\n"
        )

    msg += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Risk:* Budget options expire worthless if index doesn't move enough\n"
        f"🛡️ *SL Rule:* Premium ka 50% loss pe EXIT\n"
        f"📊 Lot size: {data['lot_size']} | Updated: {data['timestamp']}\n"
    )

    return msg


# ═══════════════════════════════════════════════════════════
#  9 AM AUTO-PICK ENGINE — Morning Market Open Picks
# ═══════════════════════════════════════════════════════════

def generate_morning_picks() -> str:
    """
    🔔 Generate 9 AM auto-pick alert with:
    - NIFTY + BankNIFTY budget options
    - ML direction + Technical confirmation
    - Specific entry, target, SL
    """
    now = datetime.now(IST)
    date_str = now.strftime("%d %b %Y")

    msg = (
        f"🔔🌅 *JARVIS 9 AM AUTO-PICKS* 🌅🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {date_str} | Pre-Market Analysis\n\n"
    )

    # Get picks for NIFTY and BANKNIFTY
    for index in ["NIFTY", "BANKNIFTY"]:
        try:
            data = find_budget_options(index=index, direction="AUTO", budget_min=3, budget_max=8)
            if "error" in data:
                msg += f"❌ {index}: {data['error']}\n\n"
                continue

            direction = data["ai_direction"]
            spot = data["spot"]
            dir_emoji = "🟢↑" if direction == "BULLISH" else "🔴↓" if direction == "BEARISH" else "🟡↔"

            msg += f"{'━' * 28}\n"
            msg += f"📊 *{index}* — {dir_emoji} {direction}\n"
            msg += f"Spot: ₹{spot:,.1f} | ML: {data['ml_direction']} ({data['ml_confidence']}%)\n\n"

            if direction == "BULLISH" and data["calls"]:
                best = data["calls"][0]
                msg += (
                    f"🟢 *BUY: {index} {best['strike']} CE*\n"
                    f"💰 Entry: *₹{best['premium']}* (Lot cost: ₹{best['lot_cost']:,.0f})\n"
                    f"🎯 Target 1: ₹{best['if_2pct_up']} | T2: ₹{best['if_3pct_up']}\n"
                    f"🚀 Max Target: ₹{best['if_5pct_up']}\n"
                    f"🛡️ SL: ₹{max(1, best['premium'] - 2)} (50% ka loss)\n"
                    f"⏰ _Market open hote hi entry lo!_\n\n"
                )
            elif direction == "BEARISH" and data["puts"]:
                best = data["puts"][0]
                msg += (
                    f"🔴 *BUY: {index} {best['strike']} PE*\n"
                    f"💰 Entry: *₹{best['premium']}* (Lot cost: ₹{best['lot_cost']:,.0f})\n"
                    f"🎯 Target 1: ₹{best['if_2pct_down']} | T2: ₹{best['if_3pct_down']}\n"
                    f"🚀 Max Target: ₹{best['if_5pct_down']}\n"
                    f"🛡️ SL: ₹{max(1, best['premium'] - 2)}\n"
                    f"⏰ _Market open hote hi entry lo!_\n\n"
                )
            else:
                # Neutral — show both sides
                if data["calls"]:
                    c = data["calls"][0]
                    msg += f"  📗 Call option: {index} {c['strike']} CE @ ₹{c['premium']}\n"
                if data["puts"]:
                    p = data["puts"][0]
                    msg += f"  📕 Put option: {index} {p['strike']} PE @ ₹{p['premium']}\n"
                msg += "  ⚠️ _Direction unclear — wait 15 min after open_\n\n"

        except Exception as e:
            msg += f"❌ {index} analysis failed: {str(e)[:80]}\n\n"

    msg += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Rules:*\n"
        f"┣ Entry: Market open ke 2-5 min baad\n"
        f"┣ SL hit hone pe turant EXIT\n"
        f"┣ Target hit pe 50% book, rest trail\n"
        f"┣ 2:30 PM tak position close karo\n\n"
        f"🛡️ Position track karne ke liye:\n"
        f"  /track NIFTY 23000CE 5\n"
        f"  (index strike+type entry_price)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    return msg


# ═══════════════════════════════════════════════════════════
#  POSITION GUARDIAN — Trail SL + Auto-Protect
# ═══════════════════════════════════════════════════════════

_guardian_data = {}  # {position_id: {"trailing_sl": X, "peak_price": Y, ...}}


def _load_guardian_data():
    """Load guardian state from disk."""
    global _guardian_data
    try:
        if os.path.exists(POSITION_GUARDIAN_FILE):
            with open(POSITION_GUARDIAN_FILE, "r") as f:
                _guardian_data = json.load(f)
    except Exception:
        _guardian_data = {}


def _save_guardian_data():
    """Persist guardian state."""
    try:
        with open(POSITION_GUARDIAN_FILE, "w") as f:
            json.dump(_guardian_data, f, indent=2)
    except Exception as e:
        logger.error(f"Save guardian: {e}")


def track_position(chat_id: int, index: str, strike: float, opt_type: str,
                   entry_price: float, qty: int = 0) -> dict:
    """
    Track a new position for the Position Guardian.
    User says: /track NIFTY 23000CE 5
    """
    index = index.upper()
    opt_type = opt_type.upper()
    if opt_type not in ("CE", "PE"):
        return {"error": "Option type must be CE or PE"}

    config = {
        "NIFTY": {"lot": 25, "symbol": "^NSEI"},
        "SENSEX": {"lot": 10, "symbol": "^BSESN"},
        "BANKNIFTY": {"lot": 15, "symbol": "^NSEBANK"},
    }
    cfg = config.get(index, config.get("NIFTY"))
    lot = cfg["lot"]
    if qty <= 0:
        qty = lot

    investment = entry_price * qty

    # Save to data_store
    try:
        from data_store import save_position
        pos_id = save_position(
            chat_id=chat_id,
            phone="",
            index_name=index,
            option_type=opt_type,
            strike=strike,
            entry_price=entry_price,
            qty=qty,
            investment=investment,
        )
    except Exception as e:
        return {"error": f"Save failed: {e}"}

    # Initialize guardian tracking
    _load_guardian_data()
    _guardian_data[str(pos_id)] = {
        "chat_id": chat_id,
        "index": index,
        "strike": strike,
        "opt_type": opt_type,
        "entry_price": entry_price,
        "qty": qty,
        "investment": investment,
        "trailing_sl": max(1, entry_price * 0.5),  # Initial SL at 50% loss
        "peak_price": entry_price,
        "alerts_sent": [],
        "status": "ACTIVE",
        "entry_time": datetime.now(IST).isoformat(),
    }
    _save_guardian_data()

    sl = max(1, entry_price * 0.5)
    return {
        "success": True,
        "position_id": pos_id,
        "index": index,
        "strike": strike,
        "opt_type": opt_type,
        "entry_price": entry_price,
        "qty": qty,
        "lot_cost": investment,
        "initial_sl": round(sl, 2),
        "msg": (
            f"✅🛡️ *POSITION TRACKED + GUARDIAN ACTIVE* 🛡️✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *{index} {int(strike)} {opt_type}*\n"
            f"💰 Entry: ₹{entry_price}\n"
            f"📦 Qty: {qty} | Investment: ₹{investment:,.0f}\n\n"
            f"🛡️ *Guardian Protection:*\n"
            f"┣ Initial SL: ₹{sl:.1f} (50% loss protection)\n"
            f"┣ Trail SL: Auto-adjust on profit\n"
            f"┣ Exit alerts: Every 2 min monitoring\n"
            f"┣ Peak tracking: Activated\n\n"
            f"📱 *Auto Alerts:*\n"
            f"┣ 🟢 +20% → Trail SL to cost\n"
            f"┣ 🟢 +30% → Trail SL to +15%\n"
            f"┣ 🟢 +60% → Trail SL to +40%\n"
            f"┣ 🟢 +100% → Trail SL to +70%\n"
            f"┣ 🔴 -20% → EXIT WARNING\n"
            f"┣ 🔴 -35% → EXIT NOW\n"
            f"┣ 🔴 -50% → EMERGENCY EXIT\n\n"
            f"ID: #{pos_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    }


def check_position_guardian(position: dict, current_spot: float) -> Optional[dict]:
    """
    Check a position and return guardian alert if needed.

    Calculates theoretical current premium using BS model,
    compares with entry + trailing SL, generates alerts.
    """
    pos_id = str(position.get("id", ""))
    _load_guardian_data()

    guardian = _guardian_data.get(pos_id)
    if not guardian or guardian.get("status") != "ACTIVE":
        return None

    index = position["index_name"]
    strike = position["strike"]
    opt_type = position["option_type"]
    entry_price = position["entry_price"]
    qty = position.get("qty", 25)

    # Calculate current theoretical price
    dte = _days_to_expiry()
    T = max(0.001, dte / 365)

    config = {
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
    }
    symbol = config.get(index, "^NSEI")
    hv = _get_historical_volatility(symbol)
    iv = max(hv * 1.15, 0.14)

    current_premium = bs_price(current_spot, strike, T, RISK_FREE_RATE, iv, opt_type)
    current_premium = max(0.5, current_premium)

    # Update peak
    if current_premium > guardian.get("peak_price", entry_price):
        guardian["peak_price"] = current_premium

    # P&L
    pnl_per_unit = current_premium - entry_price
    pnl_pct = (pnl_per_unit / entry_price) * 100 if entry_price > 0 else 0
    total_pnl = pnl_per_unit * qty

    # Check trailing SL
    trailing_sl = guardian.get("trailing_sl", entry_price * 0.5)

    alert = None

    # Update trailing SL on profit
    for level in TRAIL_SL_LEVELS:
        if pnl_pct >= level["profit_pct"]:
            new_sl = entry_price * (1 + level["trail_to_pct"] / 100)
            if new_sl > trailing_sl:
                trailing_sl = new_sl
                guardian["trailing_sl"] = trailing_sl

                alert_key = f"trail_{level['profit_pct']}"
                if alert_key not in guardian.get("alerts_sent", []):
                    guardian.setdefault("alerts_sent", []).append(alert_key)
                    alert = {
                        "type": "TRAIL_SL_UPDATE",
                        "urgency": "🟢 GOOD",
                        "msg": (
                            f"🟢🛡️ *TRAILING SL UPDATED* 🛡️🟢\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📊 *{index} {int(strike)} {opt_type}*\n"
                            f"💰 Entry: ₹{entry_price} → Now: *₹{current_premium:.1f}*\n"
                            f"📈 P&L: *₹{total_pnl:+,.0f}* ({pnl_pct:+.1f}%)\n\n"
                            f"🛡️ *New Trail SL:* ₹{trailing_sl:.1f}\n"
                            f"📊 Peak: ₹{guardian['peak_price']:.1f}\n\n"
                            f"💡 _P&L lock ho gaya! Ab loss nahi hoga!_\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        ),
                        "current_premium": current_premium,
                        "pnl": total_pnl,
                        "pnl_pct": pnl_pct,
                    }
            break

    # Check EXIT conditions
    if not alert:
        for rule_name, rule in EXIT_RULES.items():
            threshold = rule["threshold"]

            # Loss checks
            if "LOSS" in rule_name and pnl_pct <= threshold:
                alert_key = f"exit_{rule_name}"
                if alert_key not in guardian.get("alerts_sent", []):
                    guardian.setdefault("alerts_sent", []).append(alert_key)
                    if "CRITICAL" in rule_name:
                        action_text = "🚨🚨 *TURANT EXIT KARO!* 🚨🚨\nAur loss mat hone do!"
                    elif "HIGH" in rule_name:
                        action_text = "⚠️ *EXIT kar do! Market against ja raha hai!*"
                    else:
                        action_text = "⚡ *Warning: SL hit hone wala hai. Dekho aur decide karo.*"

                    alert = {
                        "type": rule["action"],
                        "urgency": rule["urgency"],
                        "msg": (
                            f"🔴🚨 *POSITION ALERT — {rule['action']}* 🚨🔴\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📊 *{index} {int(strike)} {opt_type}*\n"
                            f"💰 Entry: ₹{entry_price} → Now: *₹{current_premium:.1f}*\n"
                            f"📉 P&L: *₹{total_pnl:+,.0f}* ({pnl_pct:+.1f}%)\n"
                            f"🛡️ Trail SL: ₹{trailing_sl:.1f}\n\n"
                            f"{action_text}\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        ),
                        "current_premium": current_premium,
                        "pnl": total_pnl,
                        "pnl_pct": pnl_pct,
                    }
                    break

            # Profit checks
            if "PROFIT" in rule_name and pnl_pct >= threshold:
                alert_key = f"profit_{rule_name}"
                if alert_key not in guardian.get("alerts_sent", []):
                    guardian.setdefault("alerts_sent", []).append(alert_key)
                    if "MEGA" in rule_name:
                        action_text = "💰💰💰 *MEGA PROFIT! Full exit karo!*\n_Itna profit phir nahi milega!_"
                    elif "BIG" in rule_name:
                        action_text = "💰💰 *BIG PROFIT! 75% book karo!*\n_Remaining ka trail SL tight karo._"
                    else:
                        action_text = "💰 *GOOD PROFIT! 50% book karo!*\n_Baaki position trail pe rakho._"

                    alert = {
                        "type": rule["action"],
                        "urgency": rule["urgency"],
                        "msg": (
                            f"🟢💰 *PROFIT ALERT — {rule['action']}* 💰🟢\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📊 *{index} {int(strike)} {opt_type}*\n"
                            f"💰 Entry: ₹{entry_price} → Now: *₹{current_premium:.1f}*\n"
                            f"📈 P&L: *₹{total_pnl:+,.0f}* ({pnl_pct:+.1f}%)\n"
                            f"🛡️ Trail SL: ₹{trailing_sl:.1f}\n\n"
                            f"{action_text}\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        ),
                        "current_premium": current_premium,
                        "pnl": total_pnl,
                        "pnl_pct": pnl_pct,
                    }
                    break

    # Check trailing SL hit
    if not alert and current_premium <= trailing_sl and pnl_pct < 0:
        alert_key = "trail_sl_hit"
        if alert_key not in guardian.get("alerts_sent", []):
            guardian.setdefault("alerts_sent", []).append(alert_key)
            alert = {
                "type": "TRAIL_SL_HIT",
                "urgency": "🔴 SL HIT",
                "msg": (
                    f"🔴🛡️ *TRAILING SL HIT — EXIT NOW* 🛡️🔴\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📊 *{index} {int(strike)} {opt_type}*\n"
                    f"💰 Entry: ₹{entry_price} → SL: ₹{trailing_sl:.1f}\n"
                    f"📉 Current: *₹{current_premium:.1f}*\n"
                    f"📉 P&L: *₹{total_pnl:+,.0f}* ({pnl_pct:+.1f}%)\n\n"
                    f"🚨 *SL hit ho gaya! Position EXIT karo!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                ),
                "current_premium": current_premium,
                "pnl": total_pnl,
                "pnl_pct": pnl_pct,
            }

    # Save updated guardian state
    _guardian_data[pos_id] = guardian
    _save_guardian_data()

    return alert


def get_my_positions_enhanced(chat_id: int) -> str:
    """Get all positions with guardian status."""
    try:
        from data_store import get_open_positions
        positions = get_open_positions(chat_id)
    except Exception:
        positions = []

    if not positions:
        return (
            "📊 *MERI POSITIONS — Empty* 📊\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Koi open position nahi hai.\n\n"
            "💡 *Position track karne ke liye:*\n"
            "  /track NIFTY 23000CE 5\n"
            "  /track BANKNIFTY 50000PE 8\n\n"
            "Ya '💰 Budget Options' button se pick lo\n"
            "aur phir /track se add karo!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    _load_guardian_data()

    msg = (
        f"📊🛡️ *MERI POSITIONS + GUARDIAN* 🛡️📊\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    total_investment = 0
    total_pnl = 0

    for pos in positions:
        pos_id = str(pos["id"])
        guardian = _guardian_data.get(pos_id, {})
        trail_sl = guardian.get("trailing_sl", pos["entry_price"] * 0.5)
        peak = guardian.get("peak_price", pos["entry_price"])

        # Get current spot
        config = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
        symbol = config.get(pos["index_name"], "^NSEI")
        spot = _get_live_price(symbol)

        # Calculate current premium
        dte = _days_to_expiry()
        T = max(0.001, dte / 365)
        hv = _get_historical_volatility(symbol)
        iv = max(hv * 1.15, 0.14)
        current = bs_price(spot, pos["strike"], T, RISK_FREE_RATE, iv, pos["option_type"])
        current = max(0.5, current)

        pnl = (current - pos["entry_price"]) * pos.get("qty", 25)
        pnl_pct = ((current - pos["entry_price"]) / pos["entry_price"]) * 100 if pos["entry_price"] > 0 else 0

        total_investment += pos.get("investment", 0)
        total_pnl += pnl

        emoji = "🟢" if pnl >= 0 else "🔴"

        msg += (
            f"{emoji} *{pos['index_name']} {int(pos['strike'])} {pos['option_type']}*\n"
            f"  Entry: ₹{pos['entry_price']} → Now: ₹{current:.1f}\n"
            f"  P&L: *₹{pnl:+,.0f}* ({pnl_pct:+.1f}%)\n"
            f"  🛡️ Trail SL: ₹{trail_sl:.1f} | Peak: ₹{peak:.1f}\n"
            f"  📦 Qty: {pos.get('qty', 0)} | ID: #{pos['id']}\n\n"
        )

    total_emoji = "🟢📈" if total_pnl >= 0 else "🔴📉"
    msg += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{total_emoji} *TOTAL P&L:* ₹{total_pnl:+,.0f}\n"
        f"💰 *Investment:* ₹{total_investment:,.0f}\n\n"
        f"📱 _Position close karne ke liye:_\n"
        f"  /close [ID] [exit_price]\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    return msg


def close_tracked_position(chat_id: int, pos_id: int, exit_price: float) -> str:
    """Close a tracked position and calculate final P&L."""
    try:
        from data_store import get_open_positions, close_position

        positions = get_open_positions(chat_id)
        target = None
        for p in positions:
            if p["id"] == pos_id:
                target = p
                break

        if not target:
            return "❌ Position not found or already closed."

        pnl = (exit_price - target["entry_price"]) * target.get("qty", 25)
        close_position(pos_id, exit_price, pnl)

        # Remove from guardian
        _load_guardian_data()
        if str(pos_id) in _guardian_data:
            _guardian_data[str(pos_id)]["status"] = "CLOSED"
            _save_guardian_data()

        pnl_emoji = "🟢💰" if pnl >= 0 else "🔴📉"
        pnl_pct = ((exit_price - target["entry_price"]) / target["entry_price"]) * 100

        return (
            f"{pnl_emoji} *POSITION CLOSED* {pnl_emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *{target['index_name']} {int(target['strike'])} {target['option_type']}*\n"
            f"💰 Entry: ₹{target['entry_price']} → Exit: ₹{exit_price}\n"
            f"📈 P&L: *₹{pnl:+,.0f}* ({pnl_pct:+.1f}%)\n"
            f"📦 Qty: {target.get('qty', 0)}\n\n"
            f"{'🎉 Profit booked! Well done!' if pnl >= 0 else '😔 Loss hua, but capital protected!'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    except Exception as e:
        return f"❌ Close error: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    # Alert management
    'stop_all_crypto_alerts', 'start_all_crypto_alerts', 'is_crypto_alerts_enabled',
    'get_user_prefs', 'set_user_pref',
    # Budget options
    'find_budget_options', 'format_budget_options',
    # Morning picks
    'generate_morning_picks',
    # Position guardian
    'track_position', 'check_position_guardian', 'get_my_positions_enhanced',
    'close_tracked_position',
    # Black-Scholes
    'bs_price', 'bs_delta', 'bs_gamma', 'bs_theta',
]

# Load on import
_load_alert_prefs()
_load_guardian_data()
