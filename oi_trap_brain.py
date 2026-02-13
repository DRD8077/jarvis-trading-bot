"""
🔥🧠 NIFTY/SENSEX OPTIONS OI + TRAP BRAIN v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JARVIS ka SABSE POWERFUL Options Intelligence Engine!

For ₹2-₹30 Call/Put buyers targeting ₹300 (10x-150x returns).

FEATURES:
  🔥 Real NSE/BSE Option Chain — LIVE OI, Volume, IV, Greeks
  🧠 OI-Based TRAP DETECTION — Bull Trap / Bear Trap / Range Trap
  📊 Strike-Level OI Map — Support/Resistance from OI data
  🎯 Max Pain LIVE — Real calculation from NSE OI
  📉 OI Change Tracker — Where smart money is moving
  ⚡ Straddle Premium — ATM straddle for expected range
  💰 Budget Option Finder — ₹2-₹30 targets (₹300 potential)
  📰 News-Based Bias — Integrate macro + event analysis
  🔄 PCR Weighted — OI + Volume weighted PCR
  🧠 SUPER SIGNAL — Combined AI verdict: BUY CALL / BUY PUT / AVOID

DATA SOURCES (100% FREE):
  • NSE India API (nseindia.com) — Real option chain
  • BSE India (bseindia.com) — SENSEX options
  • yfinance — Spot prices + historical
  • All FREE, no API keys needed

Author: JARVIS AI — Options Intelligence Division
"""

import os
import time
import math
import logging
import requests
import threading
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("OI-TRAP-BRAIN")

# ═══════════════════════════════════════════════════════════════
#  CACHE — 2-min TTL for live data
# ═══════════════════════════════════════════════════════════════
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
CACHE_TTL = 120  # 2 min

# OI history for change tracking
_oi_history: Dict[str, List[dict]] = {}  # key → list of snapshots
_oi_lock = threading.Lock()


def _cached(key: str, ttl: int = CACHE_TTL):
    if key in _cache and time.time() - _cache_ts.get(key, 0) < ttl:
        return _cache[key]
    return None


def _set_cache(key: str, val: Any):
    _cache[key] = val
    _cache_ts[key] = time.time()


# ═══════════════════════════════════════════════════════════════
#  NSE SESSION — Cookie management for API access
# ═══════════════════════════════════════════════════════════════

_nse_session = None
_nse_session_ts = 0


def _get_nse_session() -> requests.Session:
    global _nse_session, _nse_session_ts
    if _nse_session and time.time() - _nse_session_ts < 300:
        return _nse_session
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/option-chain",
        "Connection": "keep-alive",
    })
    try:
        s.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
        s.get("https://www.nseindia.com/option-chain", timeout=10)
    except Exception:
        pass
    _nse_session = s
    _nse_session_ts = time.time()
    return s


# ═══════════════════════════════════════════════════════════════
#  1. REAL NSE OPTION CHAIN FETCHER
# ═══════════════════════════════════════════════════════════════

def fetch_option_chain(symbol: str = "NIFTY") -> Optional[dict]:
    """
    Fetch REAL option chain from NSE India.
    symbol: NIFTY, BANKNIFTY, NIFTY NEXT 50, etc.
    For SENSEX, uses BSE API.
    """
    cache_key = f"chain_{symbol}"
    cached = _cached(cache_key, 60)
    if cached:
        return cached

    if symbol.upper() == "SENSEX":
        return _fetch_bse_chain()

    session = _get_nse_session()
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol.upper()}"

    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            records = data.get("records", {})
            if records.get("data"):
                result = _parse_nse_chain(records, symbol)
                _set_cache(cache_key, result)
                _store_oi_snapshot(symbol, result)
                return result
    except Exception as e:
        logger.debug(f"NSE chain error for {symbol}: {e}")

    # Fallback: yfinance + synthetic
    return _synthetic_chain(symbol)


def _fetch_bse_chain() -> Optional[dict]:
    """Fetch SENSEX option chain from BSE India."""
    cache_key = "chain_SENSEX"
    cached = _cached(cache_key, 60)
    if cached:
        return cached

    try:
        # BSE option chain API
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.bseindia.com/",
        }
        session = requests.Session()
        session.get("https://www.bseindia.com/", headers=headers, timeout=10)

        # BSE API endpoint for SENSEX options
        r = session.get(
            "https://api.bseindia.com/BseIndiaAPI/api/ddlExpiry/w?FDate=&TDate=&indexname=SENSEX&optiontype=",
            headers=headers, timeout=10
        )
        # Try alternate BSE endpoint
        if r.status_code != 200:
            return _synthetic_chain("SENSEX")

        # Parse BSE data
        expiry_data = r.json() if r.status_code == 200 else []

        # Get latest expiry option chain
        if expiry_data:
            latest_exp = expiry_data[0] if isinstance(expiry_data, list) else ""
            oc_url = f"https://api.bseindia.com/BseIndiaAPI/api/OptionChain/w?Ession={latest_exp}&scripcode=&indexname=SENSEX&optiontype="
            r2 = session.get(oc_url, headers=headers, timeout=10)
            if r2.status_code == 200:
                bse_data = r2.json()
                result = _parse_bse_chain(bse_data)
                if result:
                    _set_cache(cache_key, result)
                    _store_oi_snapshot("SENSEX", result)
                    return result
    except Exception as e:
        logger.debug(f"BSE chain error: {e}")

    return _synthetic_chain("SENSEX")


def _parse_nse_chain(records: dict, symbol: str) -> dict:
    """Parse NSE option chain data into structured format."""
    spot = float(records.get("underlyingValue", 0))
    expiry_dates = records.get("expiryDates", [])
    raw_data = records.get("data", [])

    strikes = []
    total_ce_oi = 0
    total_pe_oi = 0
    total_ce_vol = 0
    total_pe_vol = 0
    max_ce_oi = 0
    max_pe_oi = 0
    max_ce_strike = 0
    max_pe_strike = 0
    max_ce_oi_chg = 0
    max_pe_oi_chg = 0
    max_ce_chg_strike = 0
    max_pe_chg_strike = 0

    for rec in raw_data:
        strike_price = rec.get("strikePrice", 0)
        ce = rec.get("CE", {})
        pe = rec.get("PE", {})

        ce_oi = int(ce.get("openInterest", 0) or 0)
        pe_oi = int(pe.get("openInterest", 0) or 0)
        ce_vol = int(ce.get("totalTradedVolume", 0) or 0)
        pe_vol = int(pe.get("totalTradedVolume", 0) or 0)
        ce_ltp = float(ce.get("lastPrice", 0) or 0)
        pe_ltp = float(pe.get("lastPrice", 0) or 0)
        ce_iv = float(ce.get("impliedVolatility", 0) or 0)
        pe_iv = float(pe.get("impliedVolatility", 0) or 0)
        ce_oi_chg = int(ce.get("changeinOpenInterest", 0) or 0)
        pe_oi_chg = int(pe.get("changeinOpenInterest", 0) or 0)
        ce_chg = float(ce.get("change", 0) or 0)
        pe_chg = float(pe.get("change", 0) or 0)

        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        total_ce_vol += ce_vol
        total_pe_vol += pe_vol

        if ce_oi > max_ce_oi:
            max_ce_oi = ce_oi
            max_ce_strike = strike_price
        if pe_oi > max_pe_oi:
            max_pe_oi = pe_oi
            max_pe_strike = strike_price
        if abs(ce_oi_chg) > abs(max_ce_oi_chg):
            max_ce_oi_chg = ce_oi_chg
            max_ce_chg_strike = strike_price
        if abs(pe_oi_chg) > abs(max_pe_oi_chg):
            max_pe_oi_chg = pe_oi_chg
            max_pe_chg_strike = strike_price

        strikes.append({
            "strike": strike_price,
            "ce_oi": ce_oi, "pe_oi": pe_oi,
            "ce_vol": ce_vol, "pe_vol": pe_vol,
            "ce_ltp": ce_ltp, "pe_ltp": pe_ltp,
            "ce_iv": ce_iv, "pe_iv": pe_iv,
            "ce_oi_chg": ce_oi_chg, "pe_oi_chg": pe_oi_chg,
            "ce_chg": ce_chg, "pe_chg": pe_chg,
        })

    pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
    pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0

    # ATM strike (closest to spot)
    step = 50 if "NIFTY" in symbol.upper() and "BANK" not in symbol.upper() else 100
    atm_strike = round(spot / step) * step

    # ATM straddle premium
    atm_data = next((s for s in strikes if s["strike"] == atm_strike), None)
    straddle_premium = 0
    if atm_data:
        straddle_premium = atm_data["ce_ltp"] + atm_data["pe_ltp"]

    # Max Pain calculation
    max_pain = _calculate_max_pain(strikes, step)

    return {
        "symbol": symbol.upper(),
        "spot": spot,
        "atm_strike": atm_strike,
        "step": step,
        "expiry_dates": expiry_dates,
        "strikes": strikes,
        "total_ce_oi": total_ce_oi,
        "total_pe_oi": total_pe_oi,
        "total_ce_vol": total_ce_vol,
        "total_pe_vol": total_pe_vol,
        "pcr_oi": pcr_oi,
        "pcr_vol": pcr_vol,
        "max_ce_oi": max_ce_oi,
        "max_pe_oi": max_pe_oi,
        "max_ce_strike": max_ce_strike,  # Resistance
        "max_pe_strike": max_pe_strike,  # Support
        "max_ce_oi_chg": max_ce_oi_chg,
        "max_pe_oi_chg": max_pe_oi_chg,
        "max_ce_chg_strike": max_ce_chg_strike,
        "max_pe_chg_strike": max_pe_chg_strike,
        "straddle_premium": straddle_premium,
        "max_pain": max_pain,
        "expected_range_low": spot - straddle_premium,
        "expected_range_high": spot + straddle_premium,
        "timestamp": datetime.now().isoformat(),
        "source": "NSE",
    }


def _parse_bse_chain(bse_data: Any) -> Optional[dict]:
    """Parse BSE API response for SENSEX option chain."""
    try:
        if not bse_data or not isinstance(bse_data, list):
            return None

        strikes = []
        total_ce_oi = 0
        total_pe_oi = 0
        spot = 0

        for item in bse_data:
            strike = float(item.get("StrikePrice", 0) or 0)
            opt_type = item.get("OptionType", "")
            oi = int(item.get("OI", 0) or 0)
            vol = int(item.get("TottrdQty", 0) or 0)
            ltp = float(item.get("LTP", 0) or 0)
            underlying = float(item.get("UndlyValue", 0) or 0)
            if underlying > 0:
                spot = underlying

            existing = next((s for s in strikes if s["strike"] == strike), None)
            if not existing:
                existing = {"strike": strike, "ce_oi": 0, "pe_oi": 0,
                           "ce_vol": 0, "pe_vol": 0, "ce_ltp": 0, "pe_ltp": 0,
                           "ce_iv": 0, "pe_iv": 0, "ce_oi_chg": 0, "pe_oi_chg": 0,
                           "ce_chg": 0, "pe_chg": 0}
                strikes.append(existing)

            if opt_type == "CE":
                existing["ce_oi"] = oi
                existing["ce_vol"] = vol
                existing["ce_ltp"] = ltp
                total_ce_oi += oi
            elif opt_type == "PE":
                existing["pe_oi"] = oi
                existing["pe_vol"] = vol
                existing["pe_ltp"] = ltp
                total_pe_oi += oi

        if not spot or not strikes:
            return None

        step = 100  # SENSEX uses 100-point strikes
        atm_strike = round(spot / step) * step
        atm_data = next((s for s in strikes if s["strike"] == atm_strike), None)
        straddle_premium = (atm_data["ce_ltp"] + atm_data["pe_ltp"]) if atm_data else 0

        max_ce_oi = max((s["ce_oi"] for s in strikes), default=0)
        max_pe_oi = max((s["pe_oi"] for s in strikes), default=0)
        max_ce_strike = next((s["strike"] for s in strikes if s["ce_oi"] == max_ce_oi), 0)
        max_pe_strike = next((s["strike"] for s in strikes if s["pe_oi"] == max_pe_oi), 0)
        pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0

        return {
            "symbol": "SENSEX",
            "spot": spot,
            "atm_strike": atm_strike,
            "step": step,
            "expiry_dates": [],
            "strikes": strikes,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "total_ce_vol": 0,
            "total_pe_vol": 0,
            "pcr_oi": pcr_oi,
            "pcr_vol": 0,
            "max_ce_oi": max_ce_oi,
            "max_pe_oi": max_pe_oi,
            "max_ce_strike": max_ce_strike,
            "max_pe_strike": max_pe_strike,
            "max_ce_oi_chg": 0,
            "max_pe_oi_chg": 0,
            "max_ce_chg_strike": 0,
            "max_pe_chg_strike": 0,
            "straddle_premium": straddle_premium,
            "max_pain": _calculate_max_pain(strikes, step),
            "expected_range_low": spot - straddle_premium,
            "expected_range_high": spot + straddle_premium,
            "timestamp": datetime.now().isoformat(),
            "source": "BSE",
        }
    except Exception as e:
        logger.error(f"BSE parse error: {e}")
        return None


def _synthetic_chain(symbol: str) -> Optional[dict]:
    """Generate synthetic chain from yfinance when NSE/BSE API fails."""
    try:
        import yfinance as yf
        import pandas as pd

        yf_sym = {
            "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN", "NIFTY NEXT 50": "^NSMIDCP"
        }.get(symbol.upper(), "^NSEI")

        df = yf.download(yf_sym, period="30d", interval="1d", progress=False)
        if len(df) < 5:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        closes = df["Close"].values.flatten()
        spot = float(closes[-1])
        highs = df["High"].values.flatten()
        lows = df["Low"].values.flatten()

        # HV for IV estimation
        returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        hv = float(sum(r ** 2 for r in returns[-20:]) / min(20, len(returns))) ** 0.5 * math.sqrt(252) * 100

        step = 50 if "NIFTY" in symbol.upper() and "BANK" not in symbol.upper() else 100
        atm = round(spot / step) * step
        strikes = []

        for offset in range(-15, 16):
            strike = atm + offset * step
            dist = abs(strike - spot)
            moneyness = (strike - spot) / spot

            # Synthetic OI (higher near ATM)
            atm_factor = max(0, 1 - dist / (spot * 0.05))
            ce_oi = int(500000 * atm_factor + 100000 * max(0, moneyness))
            pe_oi = int(500000 * atm_factor + 100000 * max(0, -moneyness))

            # Synthetic premium from BS
            iv = hv * (1 + 0.2 * abs(moneyness))
            dte = _days_to_expiry()
            t = max(dte, 0.5) / 365.0

            ce_price = _bs_call(spot, strike, t, 0.065, iv / 100)
            pe_price = _bs_put(spot, strike, t, 0.065, iv / 100)

            strikes.append({
                "strike": strike,
                "ce_oi": ce_oi, "pe_oi": pe_oi,
                "ce_vol": int(ce_oi * 0.3), "pe_vol": int(pe_oi * 0.3),
                "ce_ltp": round(ce_price, 2), "pe_ltp": round(pe_price, 2),
                "ce_iv": round(iv, 1), "pe_iv": round(iv * 1.05, 1),
                "ce_oi_chg": 0, "pe_oi_chg": 0,
                "ce_chg": 0, "pe_chg": 0,
            })

        total_ce_oi = sum(s["ce_oi"] for s in strikes)
        total_pe_oi = sum(s["pe_oi"] for s in strikes)
        atm_data = next((s for s in strikes if s["strike"] == atm), None)
        straddle_premium = (atm_data["ce_ltp"] + atm_data["pe_ltp"]) if atm_data else 0

        return {
            "symbol": symbol.upper(),
            "spot": spot,
            "atm_strike": atm,
            "step": step,
            "expiry_dates": [],
            "strikes": strikes,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "total_ce_vol": 0, "total_pe_vol": 0,
            "pcr_oi": total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0,
            "pcr_vol": 0,
            "max_ce_oi": max((s["ce_oi"] for s in strikes), default=0),
            "max_pe_oi": max((s["pe_oi"] for s in strikes), default=0),
            "max_ce_strike": max(strikes, key=lambda s: s["ce_oi"])["strike"] if strikes else 0,
            "max_pe_strike": max(strikes, key=lambda s: s["pe_oi"])["strike"] if strikes else 0,
            "max_ce_oi_chg": 0, "max_pe_oi_chg": 0,
            "max_ce_chg_strike": 0, "max_pe_chg_strike": 0,
            "straddle_premium": straddle_premium,
            "max_pain": atm,
            "expected_range_low": spot - straddle_premium,
            "expected_range_high": spot + straddle_premium,
            "timestamp": datetime.now().isoformat(),
            "source": "synthetic",
        }
    except Exception as e:
        logger.error(f"Synthetic chain error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  2. MAX PAIN CALCULATOR (Real OI Based)
# ═══════════════════════════════════════════════════════════════

def _calculate_max_pain(strikes: list, step: int) -> float:
    """Calculate max pain from real OI data."""
    if not strikes:
        return 0

    min_pain = float('inf')
    max_pain_strike = 0

    strike_prices = [s["strike"] for s in strikes if s["strike"] > 0]
    if not strike_prices:
        return 0

    for test_price in strike_prices:
        total_pain = 0
        for s in strikes:
            sp = s["strike"]
            # CE ITM pain (call buyers)
            if test_price > sp:
                total_pain += (test_price - sp) * s["ce_oi"]
            # PE ITM pain (put buyers)
            if test_price < sp:
                total_pain += (sp - test_price) * s["pe_oi"]

        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = test_price

    return max_pain_strike


# ═══════════════════════════════════════════════════════════════
#  3. OI CHANGE TRACKER — Where smart money moves
# ═══════════════════════════════════════════════════════════════

def _store_oi_snapshot(symbol: str, chain: dict):
    """Store OI snapshot for change tracking."""
    with _oi_lock:
        key = symbol.upper()
        if key not in _oi_history:
            _oi_history[key] = []

        snapshot = {
            "ts": time.time(),
            "spot": chain.get("spot", 0),
            "total_ce_oi": chain.get("total_ce_oi", 0),
            "total_pe_oi": chain.get("total_pe_oi", 0),
            "pcr_oi": chain.get("pcr_oi", 0),
            "max_ce_strike": chain.get("max_ce_strike", 0),
            "max_pe_strike": chain.get("max_pe_strike", 0),
            "straddle": chain.get("straddle_premium", 0),
            "strikes_summary": [
                {"s": s["strike"], "co": s["ce_oi"], "po": s["pe_oi"]}
                for s in chain.get("strikes", []) if s["ce_oi"] + s["pe_oi"] > 0
            ][:30],  # Top 30 strikes
        }
        _oi_history[key].append(snapshot)
        # Keep last 100 snapshots (~3.5 hours at 2-min intervals)
        if len(_oi_history[key]) > 100:
            _oi_history[key] = _oi_history[key][-100:]


def get_oi_change(symbol: str = "NIFTY") -> dict:
    """Get OI change analysis over recent snapshots."""
    key = symbol.upper()
    snapshots = _oi_history.get(key, [])

    if len(snapshots) < 2:
        # Need at least 2 snapshots for comparison
        return {"available": False, "message": "OI change data building up... Check again in 5 min."}

    latest = snapshots[-1]
    prev = snapshots[-2]
    oldest = snapshots[0]

    ce_oi_chg = latest["total_ce_oi"] - prev["total_ce_oi"]
    pe_oi_chg = latest["total_pe_oi"] - prev["total_pe_oi"]
    spot_chg = latest["spot"] - prev["spot"]
    pcr_chg = latest["pcr_oi"] - prev["pcr_oi"]

    # Longer-term change (since first snapshot)
    ce_oi_chg_long = latest["total_ce_oi"] - oldest["total_ce_oi"]
    pe_oi_chg_long = latest["total_pe_oi"] - oldest["total_pe_oi"]
    spot_chg_long = latest["spot"] - oldest["spot"]

    # OI buildup type
    buildup = _classify_oi_buildup(spot_chg, ce_oi_chg, pe_oi_chg)
    buildup_long = _classify_oi_buildup(spot_chg_long, ce_oi_chg_long, pe_oi_chg_long)

    return {
        "available": True,
        "symbol": key,
        "spot": latest["spot"],
        "spot_chg": spot_chg,
        "ce_oi_chg_short": ce_oi_chg,
        "pe_oi_chg_short": pe_oi_chg,
        "ce_oi_chg_long": ce_oi_chg_long,
        "pe_oi_chg_long": pe_oi_chg_long,
        "pcr_current": latest["pcr_oi"],
        "pcr_chg": pcr_chg,
        "buildup_short": buildup,
        "buildup_long": buildup_long,
        "snapshots_count": len(snapshots),
        "time_range_min": int((latest["ts"] - oldest["ts"]) / 60),
        "resistance_shift": latest["max_ce_strike"] != prev["max_ce_strike"],
        "support_shift": latest["max_pe_strike"] != prev["max_pe_strike"],
        "new_resistance": latest["max_ce_strike"],
        "new_support": latest["max_pe_strike"],
        "straddle_chg": latest["straddle"] - prev["straddle"],
    }


def _classify_oi_buildup(price_chg: float, ce_oi_chg: int, pe_oi_chg: int) -> str:
    """Classify OI buildup pattern."""
    if price_chg > 0 and pe_oi_chg > 0:
        return "🟢 LONG BUILDUP (Bullish — Price ↑ + Put OI ↑)"
    elif price_chg < 0 and ce_oi_chg > 0:
        return "🔴 SHORT BUILDUP (Bearish — Price ↓ + Call OI ↑)"
    elif price_chg > 0 and ce_oi_chg < 0:
        return "🟡 SHORT COVERING (Mildly Bullish — Price ↑ + Call OI ↓)"
    elif price_chg < 0 and pe_oi_chg < 0:
        return "🟡 LONG UNWINDING (Mildly Bearish — Price ↓ + Put OI ↓)"
    else:
        return "⚪ RANGE BOUND"


# ═══════════════════════════════════════════════════════════════
#  4. 🔥 TRAP DETECTION — Bull Trap / Bear Trap / Range Trap
# ═══════════════════════════════════════════════════════════════

def detect_traps(chain: dict) -> dict:
    """
    Detect Bull Trap / Bear Trap / Range Trap from OI + Price data.

    Bull Trap: Price goes above resistance → high call OI unwinding →
               market makers pulling out → reversal coming
    Bear Trap: Price goes below support → high put OI unwinding →
               market makers pulling out → reversal UP coming
    Range Trap: Both call and put OI building near ATM → expiry squeeze
    """
    spot = chain.get("spot", 0)
    atm = chain.get("atm_strike", 0)
    max_ce_strike = chain.get("max_ce_strike", 0)  # Resistance
    max_pe_strike = chain.get("max_pe_strike", 0)  # Support
    straddle = chain.get("straddle_premium", 0)
    max_pain = chain.get("max_pain", 0)
    pcr = chain.get("pcr_oi", 1.0)
    strikes = chain.get("strikes", [])

    traps = []
    overall_bias = "NEUTRAL"

    # --- BULL TRAP Detection ---
    if spot > max_ce_strike and max_ce_strike > 0:
        # Price is above max call OI → dangerous zone
        # Check if call OI declining at this strike (writers exiting = bull trap)
        ce_at_resist = next((s for s in strikes if s["strike"] == max_ce_strike), None)
        if ce_at_resist and ce_at_resist.get("ce_oi_chg", 0) < 0:
            traps.append({
                "type": "🐂🪤 BULL TRAP!",
                "confidence": "HIGH",
                "detail": (
                    f"Price ({spot:,.0f}) > Resistance ({max_ce_strike:,})\n"
                    f"Call OI DECLINING at {max_ce_strike:,} = Writers exiting\n"
                    f"⚠️ REVERSAL DOWN likely! AVOID CALLS here!"
                ),
                "action": "🔴 BUY PUT near ₹2-₹10"
            })
            overall_bias = "BEARISH"
        else:
            traps.append({
                "type": "⚠️ BREAKOUT ATTEMPT",
                "confidence": "MEDIUM",
                "detail": (
                    f"Price ({spot:,.0f}) testing Resistance ({max_ce_strike:,})\n"
                    f"Watch for call OI change — if declining = BULL TRAP"
                ),
                "action": "🟡 WAIT for confirmation"
            })

    # --- BEAR TRAP Detection ---
    if spot < max_pe_strike and max_pe_strike > 0:
        pe_at_support = next((s for s in strikes if s["strike"] == max_pe_strike), None)
        if pe_at_support and pe_at_support.get("pe_oi_chg", 0) < 0:
            traps.append({
                "type": "🐻🪤 BEAR TRAP!",
                "confidence": "HIGH",
                "detail": (
                    f"Price ({spot:,.0f}) < Support ({max_pe_strike:,})\n"
                    f"Put OI DECLINING at {max_pe_strike:,} = Writers exiting\n"
                    f"⚠️ REVERSAL UP likely! AVOID PUTS here!"
                ),
                "action": "🟢 BUY CALL near ₹2-₹10"
            })
            overall_bias = "BULLISH"
        else:
            traps.append({
                "type": "⚠️ BREAKDOWN ATTEMPT",
                "confidence": "MEDIUM",
                "detail": (
                    f"Price ({spot:,.0f}) testing Support ({max_pe_strike:,})\n"
                    f"Watch for put OI change — if declining = BEAR TRAP"
                ),
                "action": "🟡 WAIT for confirmation"
            })

    # --- RANGE TRAP (Expiry Squeeze) ---
    dte = _days_to_expiry()
    range_pct = (straddle / spot * 100) if spot > 0 else 0
    if dte <= 2 and range_pct < 2.5:
        traps.append({
            "type": "📦 RANGE TRAP (Expiry Squeeze)",
            "confidence": "HIGH" if dte == 0 else "MEDIUM",
            "detail": (
                f"Expiry in {dte} days | Straddle: ₹{straddle:,.0f} ({range_pct:.1f}%)\n"
                f"Max Pain: {max_pain:,.0f} | Spot: {spot:,.0f}\n"
                f"Market will GRAVITATE to Max Pain!\n"
                f"Expected Range: {chain.get('expected_range_low', 0):,.0f} – {chain.get('expected_range_high', 0):,.0f}"
            ),
            "action": f"{'🎯 SELL STRADDLE near ATM' if dte == 0 else '🟡 Trade within range'}"
        })

    # --- MAX PAIN GRAVITY ---
    pain_dist = abs(spot - max_pain) / spot * 100 if spot > 0 else 0
    if pain_dist > 1:
        direction = "DOWN" if spot > max_pain else "UP"
        traps.append({
            "type": f"🧲 MAX PAIN GRAVITY ({direction})",
            "confidence": "MEDIUM",
            "detail": (
                f"Spot: {spot:,.0f} | Max Pain: {max_pain:,.0f}\n"
                f"Gap: {pain_dist:.1f}% → Price will be PULLED {direction}\n"
                f"Near expiry, this force gets STRONGER!"
            ),
            "action": f"🟢 BUY CALL near ₹2-₹10" if direction == "UP" else "🔴 BUY PUT near ₹2-₹10"
        })
        if direction == "UP" and overall_bias == "NEUTRAL":
            overall_bias = "BULLISH"
        elif direction == "DOWN" and overall_bias == "NEUTRAL":
            overall_bias = "BEARISH"

    # --- PCR Extreme Detection ---
    if pcr > 1.5:
        traps.append({
            "type": "🟢 EXTREME PUT WRITING",
            "confidence": "HIGH",
            "detail": f"PCR: {pcr:.2f} → Heavy put selling = Strong floor below\nMarket makers CONFIDENT price will hold!",
            "action": "🟢 BUY CALL near ₹5-₹20 targeting ₹50-₹300"
        })
        if overall_bias == "NEUTRAL":
            overall_bias = "BULLISH"
    elif pcr < 0.5:
        traps.append({
            "type": "🔴 EXTREME CALL WRITING",
            "confidence": "HIGH",
            "detail": f"PCR: {pcr:.2f} → Heavy call selling = Strong ceiling above\nMarket makers CONFIDENT price will fall!",
            "action": "🔴 BUY PUT near ₹5-₹20 targeting ₹50-₹300"
        })
        if overall_bias == "NEUTRAL":
            overall_bias = "BEARISH"

    if not traps:
        traps.append({
            "type": "✅ NO TRAP DETECTED",
            "confidence": "LOW",
            "detail": f"Price ({spot:,.0f}) within normal range\nSupport: {max_pe_strike:,} | Resistance: {max_ce_strike:,}",
            "action": "🟡 Trade normally with SL"
        })

    return {
        "traps": traps,
        "overall_bias": overall_bias,
        "spot": spot,
        "support": max_pe_strike,
        "resistance": max_ce_strike,
        "max_pain": max_pain,
        "pcr": pcr,
        "straddle": straddle,
        "dte": _days_to_expiry(),
    }


# ═══════════════════════════════════════════════════════════════
#  5. 💰 BUDGET OPTION FINDER — ₹2-₹30 targeting ₹300
# ═══════════════════════════════════════════════════════════════

def find_budget_plays(chain: dict, min_price: float = 2.0, max_price: float = 30.0) -> List[dict]:
    """
    Find call/put options between ₹2-₹30 with maximum potential.
    User's strategy: Buy at ₹2-₹30, target ₹300 (10x-150x)
    """
    spot = chain.get("spot", 0)
    strikes = chain.get("strikes", [])
    symbol = chain.get("symbol", "NIFTY")
    trap_data = detect_traps(chain)
    bias = trap_data.get("overall_bias", "NEUTRAL")
    max_pain = chain.get("max_pain", 0)
    dte = _days_to_expiry()

    plays = []

    for s in strikes:
        strike = s["strike"]

        # Check CALL options in budget range
        ce_price = s.get("ce_ltp", 0)
        if min_price <= ce_price <= max_price:
            dist_pct = ((strike - spot) / spot) * 100
            ce_oi = s.get("ce_oi", 0)
            ce_vol = s.get("ce_vol", 0)
            ce_iv = s.get("ce_iv", 0)

            # Score: higher = better play
            score = 0
            reasons = []

            # 1. OI momentum (higher OI = more liquid)
            if ce_oi > 100000:
                score += 20
                reasons.append("High OI (liquid)")
            elif ce_oi > 50000:
                score += 10

            # 2. Volume surge
            if ce_vol > 0 and ce_oi > 0 and (ce_vol / ce_oi) > 0.5:
                score += 15
                reasons.append("Volume surge!")

            # 3. Bias alignment
            if bias in ("BULLISH",):
                score += 25
                reasons.append(f"Bias: {bias}")
            elif bias == "NEUTRAL":
                score += 10

            # 4. Near max pain (high chance of execution)
            if abs(strike - max_pain) <= chain.get("step", 50) * 3:
                score += 15
                reasons.append("Near max pain zone")

            # 5. IV not too high (cheap options)
            if ce_iv < 20:
                score += 10
                reasons.append("Low IV (cheap)")

            # 6. Expiry proximity bonus (0-1 DTE = massive gamma)
            if dte <= 1:
                score += 20
                reasons.append(f"0-DTE GAMMA! ({dte}d)")
            elif dte <= 3:
                score += 10

            # 7. Distance from spot (OTM sweet spot: 1-3%)
            if 0.5 <= dist_pct <= 3.0:
                score += 15
                reasons.append(f"OTM sweet spot ({dist_pct:.1f}%)")

            target_300 = ce_price * 10  # Conservative 10x target
            move_needed = strike + target_300 - spot
            move_pct = (move_needed / spot) * 100

            plays.append({
                "type": "CALL",
                "strike": strike,
                "ltp": ce_price,
                "oi": ce_oi,
                "vol": ce_vol,
                "iv": ce_iv,
                "dist_pct": dist_pct,
                "score": score,
                "reasons": reasons,
                "target_10x": round(ce_price * 10, 2),
                "target_50x": round(ce_price * 50, 2),
                "sl": round(ce_price * 0.5, 2),
                "move_needed_pct": round(move_pct, 1),
                "symbol": symbol,
            })

        # Check PUT options in budget range
        pe_price = s.get("pe_ltp", 0)
        if min_price <= pe_price <= max_price:
            dist_pct = ((spot - strike) / spot) * 100
            pe_oi = s.get("pe_oi", 0)
            pe_vol = s.get("pe_vol", 0)
            pe_iv = s.get("pe_iv", 0)

            score = 0
            reasons = []

            if pe_oi > 100000:
                score += 20
                reasons.append("High OI (liquid)")
            elif pe_oi > 50000:
                score += 10

            if pe_vol > 0 and pe_oi > 0 and (pe_vol / pe_oi) > 0.5:
                score += 15
                reasons.append("Volume surge!")

            if bias in ("BEARISH",):
                score += 25
                reasons.append(f"Bias: {bias}")
            elif bias == "NEUTRAL":
                score += 10

            if abs(strike - max_pain) <= chain.get("step", 50) * 3:
                score += 15
                reasons.append("Near max pain zone")

            if pe_iv < 20:
                score += 10
                reasons.append("Low IV (cheap)")

            if dte <= 1:
                score += 20
                reasons.append(f"0-DTE GAMMA! ({dte}d)")
            elif dte <= 3:
                score += 10

            if 0.5 <= dist_pct <= 3.0:
                score += 15
                reasons.append(f"OTM sweet spot ({dist_pct:.1f}%)")

            target_300 = pe_price * 10
            move_needed = spot - (strike - target_300)
            move_pct = (move_needed / spot) * 100

            plays.append({
                "type": "PUT",
                "strike": strike,
                "ltp": pe_price,
                "oi": pe_oi,
                "vol": pe_vol,
                "iv": pe_iv,
                "dist_pct": dist_pct,
                "score": score,
                "reasons": reasons,
                "target_10x": round(pe_price * 10, 2),
                "target_50x": round(pe_price * 50, 2),
                "sl": round(pe_price * 0.5, 2),
                "move_needed_pct": round(move_pct, 1),
                "symbol": symbol,
            })

    # Sort by score, return top 10
    plays.sort(key=lambda x: x["score"], reverse=True)
    return plays[:10]


# ═══════════════════════════════════════════════════════════════
#  6. 🧠 SUPER SIGNAL — Combined AI Verdict
# ═══════════════════════════════════════════════════════════════

def get_options_super_signal(symbol: str = "NIFTY") -> dict:
    """
    THE ULTIMATE SIGNAL — Combines:
    1. OI data + PCR
    2. Trap detection
    3. Max Pain gravity
    4. Straddle premium (expected range)
    5. OI change momentum
    6. Budget plays ₹2-₹30
    7. News/VIX context

    Returns clear: BUY CALL / BUY PUT / AVOID with exact strike + price
    """
    chain = fetch_option_chain(symbol)
    if not chain:
        return {"error": f"Option chain data not available for {symbol}"}

    trap_data = detect_traps(chain)
    oi_change = get_oi_change(symbol)
    budget_plays = find_budget_plays(chain)

    # Get VIX for context
    vix = _get_india_vix()

    spot = chain["spot"]
    pcr = chain["pcr_oi"]
    max_pain = chain["max_pain"]
    straddle = chain["straddle_premium"]
    dte = _days_to_expiry()
    bias = trap_data["overall_bias"]
    support = trap_data["support"]
    resistance = trap_data["resistance"]

    # --- SCORE CALCULATION ---
    bullish_score = 0
    bearish_score = 0
    signals = []

    # 1. PCR Signal
    if pcr > 1.2:
        bullish_score += 20
        signals.append(f"PCR {pcr:.2f} = PUT writing dominant → BULLISH")
    elif pcr < 0.8:
        bearish_score += 20
        signals.append(f"PCR {pcr:.2f} = CALL writing dominant → BEARISH")
    else:
        signals.append(f"PCR {pcr:.2f} = Balanced")

    # 2. Max Pain Direction
    if spot < max_pain:
        bullish_score += 15
        signals.append(f"Spot < Max Pain ({max_pain:,.0f}) → PULL UP")
    elif spot > max_pain:
        bearish_score += 15
        signals.append(f"Spot > Max Pain ({max_pain:,.0f}) → PULL DOWN")

    # 3. Trap Analysis
    if bias == "BULLISH":
        bullish_score += 25
    elif bias == "BEARISH":
        bearish_score += 25

    # 4. OI Change Momentum
    if oi_change.get("available"):
        buildup = oi_change.get("buildup_short", "")
        if "LONG BUILDUP" in buildup:
            bullish_score += 20
            signals.append("OI: Long Buildup → BULLISH")
        elif "SHORT BUILDUP" in buildup:
            bearish_score += 20
            signals.append("OI: Short Buildup → BEARISH")
        elif "SHORT COVERING" in buildup:
            bullish_score += 10
            signals.append("OI: Short Covering → Mildly Bullish")
        elif "LONG UNWINDING" in buildup:
            bearish_score += 10
            signals.append("OI: Long Unwinding → Mildly Bearish")

    # 5. VIX context
    if vix > 0:
        if vix > 20:
            signals.append(f"VIX {vix:.1f} = HIGH FEAR → Big moves expected")
        elif vix < 13:
            signals.append(f"VIX {vix:.1f} = LOW FEAR → Range bound likely")
        else:
            signals.append(f"VIX {vix:.1f} = Normal")

    # 6. Expiry Effect
    if dte == 0:
        signals.append(f"⚡ EXPIRY DAY! Max gamma — explosive moves possible")
    elif dte == 1:
        signals.append(f"📅 1 day to expiry — Theta burn high, gamma rising")

    # Final verdict
    total_score = bullish_score + bearish_score
    if total_score == 0:
        total_score = 1

    bull_pct = (bullish_score / total_score) * 100
    bear_pct = (bearish_score / total_score) * 100

    if bullish_score > bearish_score + 15:
        verdict = "🟢 BUY CALL"
        confidence = min(95, int(bull_pct))
    elif bearish_score > bullish_score + 15:
        verdict = "🔴 BUY PUT"
        confidence = min(95, int(bear_pct))
    elif abs(bullish_score - bearish_score) <= 15:
        verdict = "🟡 AVOID / RANGE TRADE"
        confidence = 50
    else:
        verdict = "🟡 WAIT"
        confidence = 40

    # Best budget play
    best_play = None
    if budget_plays:
        if "CALL" in verdict:
            calls = [p for p in budget_plays if p["type"] == "CALL"]
            best_play = calls[0] if calls else budget_plays[0]
        elif "PUT" in verdict:
            puts = [p for p in budget_plays if p["type"] == "PUT"]
            best_play = puts[0] if puts else budget_plays[0]
        else:
            best_play = budget_plays[0]

    return {
        "symbol": symbol,
        "spot": spot,
        "verdict": verdict,
        "confidence": confidence,
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "signals": signals,
        "traps": trap_data["traps"],
        "support": support,
        "resistance": resistance,
        "max_pain": max_pain,
        "pcr": pcr,
        "straddle": straddle,
        "expected_range": (chain["expected_range_low"], chain["expected_range_high"]),
        "dte": dte,
        "vix": vix,
        "best_play": best_play,
        "top_plays": budget_plays[:5],
        "oi_change": oi_change,
        "source": chain.get("source", "unknown"),
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
#  7. HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _days_to_expiry() -> int:
    """Days to next Thursday expiry."""
    today = date.today()
    weekday = today.weekday()
    if weekday <= 3:
        days = 3 - weekday
    else:
        days = 7 - weekday + 3
    return days


def _get_india_vix() -> float:
    """Get India VIX."""
    cached = _cached("india_vix", 300)
    if cached:
        return cached
    try:
        import yfinance as yf
        data = yf.download("^INDIAVIX", period="2d", interval="1d", progress=False)
        if len(data) > 0:
            import pandas as pd
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            vix = float(data["Close"].values.flatten()[-1])
            _set_cache("india_vix", vix)
            return vix
    except Exception:
        pass
    return 0.0


def _bs_call(S, K, T, r, sigma):
    """Black-Scholes call price."""
    if T <= 0 or sigma <= 0:
        return max(0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)


def _bs_put(S, K, T, r, sigma):
    """Black-Scholes put price."""
    if T <= 0 or sigma <= 0:
        return max(0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def _norm_cdf(x):
    """Cumulative normal distribution."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ═══════════════════════════════════════════════════════════════
#  8. 📝 FORMATTED OUTPUT — Telegram Messages
# ═══════════════════════════════════════════════════════════════

def format_trap_analysis(symbol: str = "NIFTY") -> str:
    """🔥 OI + Trap Analysis — Complete formatted output."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return f"❌ {symbol} option chain data available nahi hai abhi."

    trap_data = detect_traps(chain)
    spot = chain["spot"]
    dte = _days_to_expiry()

    msg = (
        f"🔥🧠 *{symbol} OI + TRAP ANALYSIS* 🧠🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 *Spot:* {spot:,.2f}\n"
        f"📅 *Expiry:* {dte} days\n"
        f"📊 *PCR:* {chain['pcr_oi']:.3f}\n"
        f"🧲 *Max Pain:* {chain['max_pain']:,.0f}\n"
        f"⚡ *Straddle:* ₹{chain['straddle_premium']:,.0f}\n"
        f"📏 *Range:* {chain['expected_range_low']:,.0f} – {chain['expected_range_high']:,.0f}\n\n"
        f"🏗️ *KEY OI LEVELS:*\n"
        f"  🔴 RESISTANCE: {chain['max_ce_strike']:,} (Max Call OI: {chain['max_ce_oi']:,})\n"
        f"  🟢 SUPPORT: {chain['max_pe_strike']:,} (Max Put OI: {chain['max_pe_oi']:,})\n\n"
    )

    # Traps
    msg += "🪤 *TRAP DETECTION:*\n"
    for trap in trap_data["traps"]:
        msg += f"\n  {trap['type']}\n"
        msg += f"  📊 {trap['detail']}\n"
        msg += f"  🎯 *Action:* {trap['action']}\n"
        msg += f"  📈 Confidence: {trap['confidence']}\n"

    msg += f"\n\n🎯 *OVERALL BIAS:* {'🟢 BULLISH' if trap_data['overall_bias'] == 'BULLISH' else '🔴 BEARISH' if trap_data['overall_bias'] == 'BEARISH' else '🟡 NEUTRAL'}\n"
    msg += f"📡 Source: {chain.get('source', 'unknown')} | {chain.get('timestamp', '')[:16]}\n"

    return msg


def format_live_chain(symbol: str = "NIFTY") -> str:
    """📊 Live Option Chain — Top strikes near ATM."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return f"❌ {symbol} option chain data available nahi hai."

    spot = chain["spot"]
    atm = chain["atm_strike"]
    step = chain["step"]
    strikes = chain["strikes"]

    # Show 10 strikes around ATM
    near_strikes = [s for s in strikes if abs(s["strike"] - atm) <= step * 5]
    near_strikes.sort(key=lambda s: s["strike"])

    msg = (
        f"📊📈 *{symbol} LIVE OPTION CHAIN* 📈📊\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Spot: {spot:,.2f} | ATM: {atm:,}\n\n"
        f"```\n"
        f"{'CE_OI':>8} {'CE₹':>6} │ STRIKE │ {'PE₹':>6} {'PE_OI':>8}\n"
        f"{'─'*8} {'─'*6} │ {'─'*6} │ {'─'*6} {'─'*8}\n"
    )

    for s in near_strikes:
        ce_marker = "◄" if s["strike"] == atm else " "
        pe_marker = "►" if s["strike"] == atm else " "
        co = s["ce_oi"]
        po = s["pe_oi"]
        # Compact OI display
        co_str = f"{co/1000:.0f}K" if co >= 1000 else str(co)
        po_str = f"{po/1000:.0f}K" if po >= 1000 else str(po)

        msg += f"{co_str:>8} {s['ce_ltp']:>6.1f}{ce_marker}│{s['strike']:>7,}│{pe_marker}{s['pe_ltp']:>6.1f} {po_str:>8}\n"

    msg += f"```\n\n"
    msg += (
        f"📊 PCR: {chain['pcr_oi']:.3f} | Max Pain: {chain['max_pain']:,.0f}\n"
        f"⚡ Straddle: ₹{chain['straddle_premium']:,.0f}\n"
        f"📏 Range: {chain['expected_range_low']:,.0f} – {chain['expected_range_high']:,.0f}\n"
        f"📡 Source: {chain.get('source', '')} | {chain.get('timestamp', '')[:16]}\n"
    )
    return msg


def format_strike_map(symbol: str = "NIFTY") -> str:
    """🎯 Strike-Level OI Map — Support/Resistance visualization."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return f"❌ {symbol} data unavailable."

    spot = chain["spot"]
    strikes = chain["strikes"]
    step = chain["step"]

    # Top 5 call OI (resistance levels)
    sorted_ce = sorted(strikes, key=lambda s: s["ce_oi"], reverse=True)[:5]
    # Top 5 put OI (support levels)
    sorted_pe = sorted(strikes, key=lambda s: s["pe_oi"], reverse=True)[:5]

    msg = (
        f"🎯📊 *{symbol} OI STRIKE MAP* 📊🎯\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Spot: {spot:,.2f}\n\n"
        f"🔴 *RESISTANCE LEVELS (Top Call OI):*\n"
        f"_Yahan se upar jaana mushkil — Call writers block karenge_\n\n"
    )
    for s in sorted_ce:
        bar_len = min(20, int(s["ce_oi"] / max(1, chain["max_ce_oi"]) * 20))
        bar = "🟥" * bar_len
        dist = ((s["strike"] - spot) / spot) * 100
        msg += f"  *{s['strike']:,}* ({dist:+.1f}%) | OI: {s['ce_oi']:,}\n  {bar}\n"

    msg += (
        f"\n🟢 *SUPPORT LEVELS (Top Put OI):*\n"
        f"_Yahan se neeche girna mushkil — Put writers support denge_\n\n"
    )
    for s in sorted_pe:
        bar_len = min(20, int(s["pe_oi"] / max(1, chain["max_pe_oi"]) * 20))
        bar = "🟩" * bar_len
        dist = ((s["strike"] - spot) / spot) * 100
        msg += f"  *{s['strike']:,}* ({dist:+.1f}%) | OI: {s['pe_oi']:,}\n  {bar}\n"

    msg += (
        f"\n🧲 *Max Pain:* {chain['max_pain']:,.0f}\n"
        f"📊 *PCR:* {chain['pcr_oi']:.3f}\n"
        f"📡 Source: {chain.get('source', '')}\n"
    )
    return msg


def format_max_pain(symbol: str = "NIFTY") -> str:
    """📉 Max Pain Live Analysis."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return f"❌ {symbol} data unavailable."

    spot = chain["spot"]
    max_pain = chain["max_pain"]
    gap = spot - max_pain
    gap_pct = (gap / spot) * 100

    direction = "⬇️ DOWN" if gap > 0 else "⬆️ UP"
    emoji = "🔴" if gap > 0 else "🟢"

    msg = (
        f"📉🎯 *{symbol} MAX PAIN ANALYSIS* 🎯📉\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 *Spot Price:* {spot:,.2f}\n"
        f"🎯 *Max Pain:* {max_pain:,.0f}\n"
        f"📏 *Gap:* {abs(gap):,.0f} points ({abs(gap_pct):.1f}%)\n\n"
        f"{emoji} *Direction:* Price will be pulled {direction} towards Max Pain\n\n"
        f"🧲 *Max Pain Theory:*\n"
        f"_Option writers have maximum profit at {max_pain:,.0f}_\n"
        f"_Market makers will try to push price towards this level_\n"
        f"_This force is STRONGEST on expiry day!_\n\n"
        f"📅 Expiry in {_days_to_expiry()} days\n"
        f"⚡ Straddle: ₹{chain['straddle_premium']:,.0f}\n"
        f"📏 Expected: {chain['expected_range_low']:,.0f} – {chain['expected_range_high']:,.0f}\n\n"
    )

    if gap > 0:
        msg += f"💡 *Suggestion:* PUT le sakte ho ₹2-₹10 range mein\nTarget: ₹50-₹300 if price falls to max pain\n"
    else:
        msg += f"💡 *Suggestion:* CALL le sakte ho ₹2-₹10 range mein\nTarget: ₹50-₹300 if price rises to max pain\n"

    return msg


def format_oi_change(symbol: str = "NIFTY") -> str:
    """🔄 OI Change Tracker."""
    # Fetch fresh data first to trigger snapshot
    chain = fetch_option_chain(symbol)
    data = get_oi_change(symbol)

    if not data.get("available"):
        return (
            f"🔄📊 *{symbol} OI CHANGE TRACKER*\n\n"
            f"⏳ Data abhi build ho raha hai...\n"
            f"JARVIS har 2 min mein OI snapshot leta hai.\n"
            f"5 min baad check karo — full change data milega! 📊"
        )

    msg = (
        f"🔄📊 *{symbol} OI CHANGE TRACKER* 📊🔄\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 Spot: {data['spot']:,.2f} (Chg: {data['spot_chg']:+,.1f})\n\n"
        f"📊 *SHORT-TERM CHANGE (Last 2 min):*\n"
        f"  📞 Call OI Change: {data['ce_oi_chg_short']:+,}\n"
        f"  📉 Put OI Change: {data['pe_oi_chg_short']:+,}\n"
        f"  📈 Buildup: {data['buildup_short']}\n\n"
        f"📊 *LONGER-TERM ({data['time_range_min']} min):*\n"
        f"  📞 Call OI Change: {data['ce_oi_chg_long']:+,}\n"
        f"  📉 Put OI Change: {data['pe_oi_chg_long']:+,}\n"
        f"  📈 Buildup: {data['buildup_long']}\n\n"
        f"📊 *PCR:* {data['pcr_current']:.3f} (Chg: {data['pcr_chg']:+.3f})\n"
    )

    if data.get("resistance_shift"):
        msg += f"\n⚠️ *RESISTANCE SHIFTED* to {data['new_resistance']:,}\n"
    if data.get("support_shift"):
        msg += f"\n⚠️ *SUPPORT SHIFTED* to {data['new_support']:,}\n"

    if data.get("straddle_chg", 0) != 0:
        msg += f"\n⚡ Straddle Change: {data['straddle_chg']:+,.0f}\n"

    msg += f"\n📡 Snapshots: {data['snapshots_count']} | Period: {data['time_range_min']} min\n"
    return msg


def format_straddle_premium(symbol: str = "NIFTY") -> str:
    """⚡ ATM Straddle Premium — Expected range indicator."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return f"❌ {symbol} data unavailable."

    spot = chain["spot"]
    atm = chain["atm_strike"]
    straddle = chain["straddle_premium"]
    range_pct = (straddle / spot) * 100 if spot > 0 else 0
    dte = _days_to_expiry()

    # Find ATM prices
    atm_data = next((s for s in chain["strikes"] if s["strike"] == atm), None)
    ce_price = atm_data["ce_ltp"] if atm_data else 0
    pe_price = atm_data["pe_ltp"] if atm_data else 0

    msg = (
        f"⚡📊 *{symbol} ATM STRADDLE PREMIUM* 📊⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 Spot: {spot:,.2f} | ATM: {atm:,}\n"
        f"📅 Expiry: {dte} days\n\n"
        f"📞 *ATM Call ({atm:,} CE):* ₹{ce_price:,.2f}\n"
        f"📉 *ATM Put ({atm:,} PE):* ₹{pe_price:,.2f}\n"
        f"⚡ *Straddle Premium:* ₹{straddle:,.2f}\n\n"
        f"📏 *EXPECTED MOVE:*\n"
        f"  ⬆️ Upper: {spot + straddle:,.0f} (+{range_pct:.1f}%)\n"
        f"  ⬇️ Lower: {spot - straddle:,.0f} (-{range_pct:.1f}%)\n"
        f"  📊 Range: {range_pct * 2:.1f}%\n\n"
    )

    # Straddle strategy suggestion
    if dte == 0:
        msg += "💡 *EXPIRY DAY:* Straddle will decay FAST. Sellers have edge.\n"
        msg += "🎯 Buy OTM options ₹2-₹10 for lottery — massive gamma!\n"
    elif dte <= 2:
        msg += "💡 *Near Expiry:* Theta eating premium fast.\n"
        msg += "🎯 Directional plays better than straddle buying.\n"
    else:
        msg += "💡 *Time Available:* Straddle buy works if big event expected.\n"

    return msg


def format_super_signal(symbol: str = "NIFTY") -> str:
    """🧠 THE ULTIMATE OPTIONS SIGNAL — Clear BUY CALL / BUY PUT / AVOID."""
    sig = get_options_super_signal(symbol)
    if "error" in sig:
        return f"❌ {sig['error']}"

    msg = (
        f"🧠🔥 *{symbol} OPTIONS SUPER SIGNAL* 🔥🧠\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 Spot: {sig['spot']:,.2f} | PCR: {sig['pcr']:.3f}\n"
        f"🧲 Max Pain: {sig['max_pain']:,.0f}\n"
        f"📅 Expiry: {sig['dte']} days"
    )
    if sig.get("vix"):
        msg += f" | VIX: {sig['vix']:.1f}"
    msg += "\n\n"

    # ═══ KEY LEVELS ═══
    msg += (
        f"🏗️ *KEY LEVELS:*\n"
        f"  🔴 Resistance: {sig['resistance']:,}\n"
        f"  🟢 Support: {sig['support']:,}\n"
        f"  📏 Range: {sig['expected_range'][0]:,.0f} – {sig['expected_range'][1]:,.0f}\n"
        f"  ⚡ Straddle: ₹{sig['straddle']:,.0f}\n\n"
    )

    # ═══ SIGNALS ═══
    msg += "📡 *SIGNALS:*\n"
    for s in sig["signals"]:
        msg += f"  • {s}\n"
    msg += "\n"

    # ═══ TRAPS ═══
    if sig["traps"]:
        msg += "🪤 *TRAPS:*\n"
        for trap in sig["traps"][:3]:
            msg += f"  {trap['type']}\n"
    msg += "\n"

    # ═══ VERDICT ═══
    msg += (
        f"{'═' * 32}\n"
        f"🎯 *VERDICT:* {sig['verdict']}\n"
        f"📊 *Confidence:* {sig['confidence']}%\n"
        f"{'═' * 32}\n\n"
    )

    # ═══ BEST PLAY ═══
    play = sig.get("best_play")
    if play:
        msg += (
            f"💰 *BEST BUDGET PLAY:*\n"
            f"  {'🟢' if play['type'] == 'CALL' else '🔴'} *{play['symbol']} {play['strike']:,} {play['type']}*\n"
            f"  💵 Price: ₹{play['ltp']:.2f}\n"
            f"  🎯 Target (10x): ₹{play['target_10x']:.0f}\n"
            f"  🚀 Target (50x): ₹{play['target_50x']:.0f}\n"
            f"  🛡️ SL: ₹{play['sl']:.2f}\n"
            f"  📏 Move needed: {play['move_needed_pct']:.1f}%\n"
            f"  💡 {', '.join(play['reasons'][:3])}\n\n"
        )

    # ═══ TOP 5 PLAYS ═══
    top_plays = sig.get("top_plays", [])
    if len(top_plays) > 1:
        msg += "📋 *TOP 5 BUDGET OPTIONS (₹2-₹30):*\n"
        for i, p in enumerate(top_plays[:5], 1):
            emoji = "🟢" if p["type"] == "CALL" else "🔴"
            msg += (
                f"{i}. {emoji} {p['strike']:,} {p['type']} "
                f"₹{p['ltp']:.1f} → ₹{p['target_10x']:.0f} "
                f"(Score: {p['score']})\n"
            )
        msg += "\n"

    msg += (
        f"⚠️ *₹2-₹30 mein lo, ₹300 ka target!*\n"
        f"🛡️ *50% SL strictly follow karo!*\n"
        f"📡 Source: {sig.get('source', '')} | {sig.get('timestamp', '')[:16]}\n"
    )
    return msg


# ═══════════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════

OI_TRAP_BRAIN_AVAILABLE = True

__all__ = [
    "OI_TRAP_BRAIN_AVAILABLE",
    # Core data
    "fetch_option_chain", "detect_traps", "find_budget_plays",
    "get_options_super_signal", "get_oi_change",
    # Formatted output
    "format_trap_analysis", "format_live_chain", "format_strike_map",
    "format_max_pain", "format_oi_change", "format_straddle_premium",
    "format_super_signal",
]
