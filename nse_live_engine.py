"""
🔥🔥🔥 NSE LIVE ENGINE — REAL-TIME OPTION CHAIN + PRICING (NUCLEAR)
═══════════════════════════════════════════════════════════════════════
100% REAL NSE India data — NO synthetic BS!

This engine provides:
  ✅ REAL NSE option chain with LIVE LTP, OI, Volume, IV, Greeks
  ✅ REAL ATM/OTM/ITM option prices from NSE
  ✅ Proper NSE cookie management with retry
  ✅ Smart fallback: NSE → BSE → yfinance + Black-Scholes
  ✅ Real-time spot prices for NIFTY, SENSEX, BANKNIFTY
  ✅ OI-based support/resistance levels
  ✅ Max Pain from REAL OI data
  ✅ PCR (Put-Call Ratio) from REAL OI
  ✅ In-memory caching with TTL (no disk I/O in hot path)
  ✅ Thread-safe with locks

Author: JARVIS Nuclear Trading Division
"""

import os
import math
import time
import logging
import threading
import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("nse_live_engine")

# ═══════════════════════════════════════════════════════════════
#  THREAD-SAFE IN-MEMORY CACHE
# ═══════════════════════════════════════════════════════════════

_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
_cache_lock = threading.Lock()

def _get_cached(key: str, ttl: int = 60) -> Optional[Any]:
    with _cache_lock:
        if key in _cache and time.time() - _cache_ts.get(key, 0) < ttl:
            return _cache[key]
    return None

def _set_cached(key: str, val: Any):
    with _cache_lock:
        _cache[key] = val
        _cache_ts[key] = time.time()


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

INDEX_CONFIG = {
    "NIFTY": {"ticker": "^NSEI", "nse_symbol": "NIFTY", "step": 50, "lot": 25,
              "expiry_day": 3},  # Thursday
    "SENSEX": {"ticker": "^BSESN", "nse_symbol": "SENSEX", "step": 100, "lot": 10,
               "expiry_day": 4},  # Friday
    "BANKNIFTY": {"ticker": "^NSEBANK", "nse_symbol": "BANKNIFTY", "step": 100, "lot": 15,
                  "expiry_day": 2},  # Wednesday
    "FINNIFTY": {"ticker": "NIFTY_FIN_SERVICE.NS", "nse_symbol": "FINNIFTY", "step": 50, "lot": 25,
                 "expiry_day": 1},  # Tuesday
}

RISK_FREE_RATE = 0.07  # India ~7%


# ═══════════════════════════════════════════════════════════════
#  NSE SESSION MANAGEMENT (with retry + cookie refresh)
# ═══════════════════════════════════════════════════════════════

_nse_session: Optional[requests.Session] = None
_nse_session_ts: float = 0
_nse_lock = threading.Lock()

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/option-chain",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


def _get_nse_session(force_new: bool = False) -> requests.Session:
    """Get or create NSE session with cookies. Thread-safe."""
    global _nse_session, _nse_session_ts
    with _nse_lock:
        if _nse_session and not force_new and time.time() - _nse_session_ts < 240:
            return _nse_session
        
        s = requests.Session()
        s.headers.update(NSE_HEADERS)
        
        try:
            # Step 1: Get main page cookies
            r = s.get("https://www.nseindia.com", timeout=10)
            time.sleep(0.3)
            
            # Step 2: Warm up option chain page
            s.get("https://www.nseindia.com/option-chain", timeout=10)
            time.sleep(0.2)
            
            _nse_session = s
            _nse_session_ts = time.time()
            logger.info("[NSE-LIVE] Session created successfully")
        except Exception as e:
            logger.warning(f"[NSE-LIVE] Session creation issue: {e}")
            _nse_session = s
            _nse_session_ts = time.time()
        
        return _nse_session


# ═══════════════════════════════════════════════════════════════
#  1. REAL NSE OPTION CHAIN — Direct NSE API
# ═══════════════════════════════════════════════════════════════

@dataclass
class LiveOptionStrike:
    """One strike from REAL NSE data."""
    strike: float
    ce_ltp: float = 0.0       # REAL Call price from NSE
    pe_ltp: float = 0.0       # REAL Put price from NSE
    ce_oi: int = 0
    pe_oi: int = 0
    ce_volume: int = 0
    pe_volume: int = 0
    ce_iv: float = 0.0
    pe_iv: float = 0.0
    ce_oi_change: int = 0
    pe_oi_change: int = 0
    ce_change: float = 0.0
    pe_change: float = 0.0
    ce_bid: float = 0.0
    ce_ask: float = 0.0
    pe_bid: float = 0.0
    pe_ask: float = 0.0
    ce_delta: float = 0.0
    pe_delta: float = 0.0
    moneyness: str = ""       # ITM / ATM / OTM


@dataclass
class LiveOptionChain:
    """Complete REAL option chain."""
    symbol: str
    spot: float
    atm_strike: float
    step: int
    lot_size: int
    strikes: List[LiveOptionStrike] = field(default_factory=list)
    
    # OI aggregates
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    pcr_oi: float = 0.0
    pcr_volume: float = 0.0
    
    # Key levels from OI
    max_ce_oi_strike: float = 0.0    # Resistance
    max_pe_oi_strike: float = 0.0    # Support
    max_pain: float = 0.0
    straddle_premium: float = 0.0
    expected_range: Tuple[float, float] = (0, 0)
    
    # Expiry info
    expiry_dates: List[str] = field(default_factory=list)
    days_to_expiry: int = 0
    
    source: str = "NSE"
    timestamp: str = ""
    is_real_data: bool = True


def fetch_live_option_chain(symbol: str = "NIFTY", max_retries: int = 3) -> Optional[LiveOptionChain]:
    """
    Fetch REAL option chain from NSE India.
    Returns LiveOptionChain with REAL LTP, OI, IV, Volume.
    
    Falls back to: NSE API → BSE API → Synthetic (Black-Scholes)
    """
    cache_key = f"live_chain_{symbol.upper()}"
    cached = _get_cached(cache_key, ttl=45)
    if cached:
        return cached
    
    config = INDEX_CONFIG.get(symbol.upper(), INDEX_CONFIG["NIFTY"])
    
    # Method 1: NSE Direct API
    for attempt in range(max_retries):
        try:
            chain = _fetch_nse_option_chain(symbol.upper(), config)
            if chain and chain.strikes:
                _set_cached(cache_key, chain)
                return chain
        except Exception as e:
            logger.warning(f"[NSE-LIVE] Attempt {attempt+1} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                _get_nse_session(force_new=True)
                time.sleep(1)
    
    # Method 2: BSE API (for SENSEX)
    if symbol.upper() == "SENSEX":
        try:
            chain = _fetch_bse_option_chain(config)
            if chain and chain.strikes:
                _set_cached(cache_key, chain)
                return chain
        except Exception as e:
            logger.warning(f"[NSE-LIVE] BSE fallback failed: {e}")
    
    # Method 3: Synthetic chain with Black-Scholes
    try:
        chain = _generate_synthetic_chain(symbol.upper(), config)
        if chain:
            chain.is_real_data = False
            chain.source = "Synthetic (Black-Scholes)"
            _set_cached(cache_key, chain)
            return chain
    except Exception as e:
        logger.error(f"[NSE-LIVE] All methods failed for {symbol}: {e}")
    
    return None


def _fetch_nse_option_chain(symbol: str, config: dict) -> Optional[LiveOptionChain]:
    """Direct NSE API call for option chain."""
    session = _get_nse_session()
    nse_sym = config.get("nse_symbol", symbol)
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={nse_sym}"
    
    r = session.get(url, timeout=15)
    if r.status_code != 200:
        raise Exception(f"NSE returned {r.status_code}")
    
    data = r.json()
    records = data.get("records", {})
    raw_data = records.get("data", [])
    
    if not raw_data:
        raise Exception("Empty option chain data")
    
    spot = float(records.get("underlyingValue", 0))
    expiry_dates = records.get("expiryDates", [])
    step = config["step"]
    lot = config["lot"]
    atm = round(spot / step) * step
    
    # Days to expiry
    dte = _calc_days_to_expiry(expiry_dates[0] if expiry_dates else None, config.get("expiry_day", 3))
    
    strikes = []
    total_ce_oi = 0
    total_pe_oi = 0
    total_ce_vol = 0
    total_pe_vol = 0
    max_ce_oi = 0
    max_pe_oi = 0
    max_ce_oi_strike = 0
    max_pe_oi_strike = 0
    
    for rec in raw_data:
        strike_price = float(rec.get("strikePrice", 0))
        ce = rec.get("CE", {})
        pe = rec.get("PE", {})
        
        ce_oi = int(ce.get("openInterest", 0) or 0)
        pe_oi = int(pe.get("openInterest", 0) or 0)
        ce_vol = int(ce.get("totalTradedVolume", 0) or 0)
        pe_vol = int(pe.get("totalTradedVolume", 0) or 0)
        ce_ltp = float(ce.get("lastPrice", 0) or 0)
        pe_ltp = float(pe.get("lastPrice", 0) or 0)
        ce_iv_val = float(ce.get("impliedVolatility", 0) or 0)
        pe_iv_val = float(pe.get("impliedVolatility", 0) or 0)
        ce_oi_chg = int(ce.get("changeinOpenInterest", 0) or 0)
        pe_oi_chg = int(pe.get("changeinOpenInterest", 0) or 0)
        ce_chg = float(ce.get("change", 0) or 0)
        pe_chg = float(pe.get("change", 0) or 0)
        ce_bid = float(ce.get("bidprice", 0) or 0)
        ce_ask = float(ce.get("askprice", 0) or 0)
        pe_bid = float(pe.get("bidprice", 0) or 0)
        pe_ask = float(pe.get("askprice", 0) or 0)
        
        # Calculate delta from IV
        T = max(dte, 1) / 365
        ce_delta = _quick_delta(spot, strike_price, T, ce_iv_val / 100 if ce_iv_val > 0 else 0.15, "CE")
        pe_delta = _quick_delta(spot, strike_price, T, pe_iv_val / 100 if pe_iv_val > 0 else 0.15, "PE")
        
        # Moneyness
        if abs(strike_price - atm) < step * 0.5:
            moneyness = "ATM"
        elif (strike_price > spot):
            moneyness = "OTM" if True else "ITM"  # For CE: OTM when strike > spot
        else:
            moneyness = "ITM"
        
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        total_ce_vol += ce_vol
        total_pe_vol += pe_vol
        
        if ce_oi > max_ce_oi:
            max_ce_oi = ce_oi
            max_ce_oi_strike = strike_price
        if pe_oi > max_pe_oi:
            max_pe_oi = pe_oi
            max_pe_oi_strike = strike_price
        
        strikes.append(LiveOptionStrike(
            strike=strike_price,
            ce_ltp=ce_ltp,
            pe_ltp=pe_ltp,
            ce_oi=ce_oi,
            pe_oi=pe_oi,
            ce_volume=ce_vol,
            pe_volume=pe_vol,
            ce_iv=ce_iv_val,
            pe_iv=pe_iv_val,
            ce_oi_change=ce_oi_chg,
            pe_oi_change=pe_oi_chg,
            ce_change=ce_chg,
            pe_change=pe_chg,
            ce_bid=ce_bid,
            ce_ask=ce_ask,
            pe_bid=pe_bid,
            pe_ask=pe_ask,
            ce_delta=ce_delta,
            pe_delta=pe_delta,
            moneyness=moneyness,
        ))
    
    # Sort by strike
    strikes.sort(key=lambda s: s.strike)
    
    pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
    pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0
    
    # ATM straddle
    atm_strike_obj = next((s for s in strikes if abs(s.strike - atm) < step * 0.5), None)
    straddle = (atm_strike_obj.ce_ltp + atm_strike_obj.pe_ltp) if atm_strike_obj else 0
    
    # Max Pain
    max_pain = _calc_max_pain_from_strikes(strikes)
    
    chain = LiveOptionChain(
        symbol=symbol,
        spot=spot,
        atm_strike=atm,
        step=step,
        lot_size=lot,
        strikes=strikes,
        total_ce_oi=total_ce_oi,
        total_pe_oi=total_pe_oi,
        pcr_oi=round(pcr_oi, 3),
        pcr_volume=round(pcr_vol, 3),
        max_ce_oi_strike=max_ce_oi_strike,
        max_pe_oi_strike=max_pe_oi_strike,
        max_pain=max_pain,
        straddle_premium=straddle,
        expected_range=(spot - straddle, spot + straddle),
        expiry_dates=expiry_dates,
        days_to_expiry=dte,
        source="NSE",
        timestamp=datetime.now().strftime("%H:%M:%S IST"),
        is_real_data=True,
    )
    
    logger.info(f"[NSE-LIVE] {symbol}: spot=₹{spot:,.0f}, {len(strikes)} strikes, PCR={pcr_oi:.2f}, MaxPain=₹{max_pain:,.0f}")
    return chain


def _fetch_bse_option_chain(config: dict) -> Optional[LiveOptionChain]:
    """Fetch SENSEX option chain from BSE."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.bseindia.com/",
    }
    s = requests.Session()
    s.get("https://www.bseindia.com/", headers=headers, timeout=10)
    
    r = s.get(
        "https://api.bseindia.com/BseIndiaAPI/api/ddlExpiry/w?FDate=&TDate=&indexname=SENSEX&optiontype=",
        headers=headers, timeout=10
    )
    if r.status_code != 200:
        return None
    
    expiry_data = r.json() if isinstance(r.json(), list) else []
    if not expiry_data:
        return None
    
    latest_exp = expiry_data[0]
    r2 = s.get(
        f"https://api.bseindia.com/BseIndiaAPI/api/OptionChain/w?Ession={latest_exp}&scripcode=&indexname=SENSEX&optiontype=",
        headers=headers, timeout=10
    )
    if r2.status_code != 200:
        return None
    
    bse_data = r2.json()
    if not bse_data or not isinstance(bse_data, list):
        return None
    
    spot = 0
    strike_map = {}
    for item in bse_data:
        strike_price = float(item.get("StrikePrice", 0) or 0)
        opt_type = item.get("OptionType", "")
        oi = int(item.get("OI", 0) or 0)
        vol = int(item.get("TottrdQty", 0) or 0)
        ltp = float(item.get("LTP", 0) or 0)
        underlying = float(item.get("UndlyValue", 0) or 0)
        if underlying > 0:
            spot = underlying
        
        if strike_price not in strike_map:
            strike_map[strike_price] = LiveOptionStrike(strike=strike_price)
        
        s_obj = strike_map[strike_price]
        if opt_type == "CE":
            s_obj.ce_ltp = ltp
            s_obj.ce_oi = oi
            s_obj.ce_volume = vol
        elif opt_type == "PE":
            s_obj.pe_ltp = ltp
            s_obj.pe_oi = oi
            s_obj.pe_volume = vol
    
    if not spot or not strike_map:
        return None
    
    strikes = sorted(strike_map.values(), key=lambda s: s.strike)
    step = 100
    atm = round(spot / step) * step
    
    total_ce_oi = sum(s.ce_oi for s in strikes)
    total_pe_oi = sum(s.pe_oi for s in strikes)
    
    max_ce_s = max(strikes, key=lambda s: s.ce_oi, default=None)
    max_pe_s = max(strikes, key=lambda s: s.pe_oi, default=None)
    
    atm_obj = min(strikes, key=lambda s: abs(s.strike - atm), default=None)
    straddle = (atm_obj.ce_ltp + atm_obj.pe_ltp) if atm_obj else 0
    
    return LiveOptionChain(
        symbol="SENSEX",
        spot=spot,
        atm_strike=atm,
        step=step,
        lot_size=10,
        strikes=strikes,
        total_ce_oi=total_ce_oi,
        total_pe_oi=total_pe_oi,
        pcr_oi=round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else 0,
        max_ce_oi_strike=max_ce_s.strike if max_ce_s else 0,
        max_pe_oi_strike=max_pe_s.strike if max_pe_s else 0,
        max_pain=_calc_max_pain_from_strikes(strikes),
        straddle_premium=straddle,
        expected_range=(spot - straddle, spot + straddle),
        days_to_expiry=_calc_days_to_expiry(None, 4),
        source="BSE",
        timestamp=datetime.now().strftime("%H:%M:%S IST"),
        is_real_data=True,
    )


def _generate_synthetic_chain(symbol: str, config: dict) -> Optional[LiveOptionChain]:
    """Generate synthetic chain using yfinance + Black-Scholes when NSE/BSE APIs fail."""
    try:
        import yfinance as yf
        import numpy as np
        
        ticker = config.get("ticker", "^NSEI")
        df = yf.download(ticker, period="30d", interval="1d", progress=False)
        if df is None or len(df) < 5:
            return None
        
        if hasattr(df.columns, 'get_level_values'):
            try:
                df.columns = df.columns.get_level_values(0)
            except Exception:
                pass
        
        close_col = 'Close' if 'Close' in df.columns else 'close'
        spot = float(df[close_col].iloc[-1])
        
        # Historical volatility
        returns = df[close_col].pct_change().dropna()
        hv = float(returns.std() * np.sqrt(252))
        hv = max(0.10, min(0.50, hv))
        
        step = config["step"]
        lot = config["lot"]
        atm = round(spot / step) * step
        dte = _calc_days_to_expiry(None, config.get("expiry_day", 3))
        T = max(dte, 1) / 365
        
        strikes = []
        for i in range(-15, 16):
            K = atm + i * step
            if K <= 0:
                continue
            
            # IV smile
            distance = abs(K - spot) / spot
            iv = hv * (1 + distance * 1.2)
            
            ce_price = _bs_price(spot, K, T, RISK_FREE_RATE, iv, "CE")
            pe_price = _bs_price(spot, K, T, RISK_FREE_RATE, iv, "PE")
            ce_delta = _quick_delta(spot, K, T, iv, "CE")
            pe_delta = _quick_delta(spot, K, T, iv, "PE")
            
            if abs(K - atm) < step * 0.5:
                moneyness = "ATM"
            elif K > spot:
                moneyness = "OTM"
            else:
                moneyness = "ITM"
            
            strikes.append(LiveOptionStrike(
                strike=K,
                ce_ltp=round(ce_price, 2),
                pe_ltp=round(pe_price, 2),
                ce_iv=round(iv * 100, 1),
                pe_iv=round(iv * 100 * 1.03, 1),
                ce_delta=ce_delta,
                pe_delta=pe_delta,
                moneyness=moneyness,
            ))
        
        atm_obj = next((s for s in strikes if s.moneyness == "ATM"), None)
        straddle = (atm_obj.ce_ltp + atm_obj.pe_ltp) if atm_obj else 0
        
        return LiveOptionChain(
            symbol=symbol,
            spot=spot,
            atm_strike=atm,
            step=step,
            lot_size=lot,
            strikes=strikes,
            straddle_premium=straddle,
            expected_range=(spot - straddle, spot + straddle),
            days_to_expiry=dte,
            source="Synthetic (Black-Scholes)",
            timestamp=datetime.now().strftime("%H:%M:%S IST"),
            is_real_data=False,
        )
    except Exception as e:
        logger.error(f"[NSE-LIVE] Synthetic chain failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  2. REAL SPOT PRICE — with caching
# ═══════════════════════════════════════════════════════════════

def get_live_spot(symbol: str = "NIFTY") -> Dict[str, Any]:
    """Get real-time spot price. Returns dict with price, change, change_pct."""
    cache_key = f"spot_{symbol.upper()}"
    cached = _get_cached(cache_key, ttl=30)
    if cached:
        return cached
    
    result = {"symbol": symbol.upper(), "price": 0, "change": 0, "change_pct": 0, "source": ""}
    
    # Try NSE first
    try:
        session = _get_nse_session()
        if symbol.upper() in ("NIFTY", "BANKNIFTY", "FINNIFTY"):
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol.upper()}"
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                records = data.get("records", {})
                spot = float(records.get("underlyingValue", 0))
                if spot > 0:
                    result["price"] = spot
                    result["source"] = "NSE"
                    _set_cached(cache_key, result)
                    return result
    except Exception:
        pass
    
    # Fallback: yfinance
    try:
        import yfinance as yf
        config = INDEX_CONFIG.get(symbol.upper(), INDEX_CONFIG["NIFTY"])
        ticker = config["ticker"]
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        if df is not None and len(df) >= 2:
            if hasattr(df.columns, 'get_level_values'):
                try:
                    df.columns = df.columns.get_level_values(0)
                except Exception:
                    pass
            close_col = 'Close' if 'Close' in df.columns else 'close'
            result["price"] = float(df[close_col].iloc[-1])
            result["change"] = float(df[close_col].iloc[-1] - df[close_col].iloc[-2])
            result["change_pct"] = (result["change"] / df[close_col].iloc[-2]) * 100
            result["source"] = "yfinance"
    except Exception:
        pass
    
    if result["price"] > 0:
        _set_cached(cache_key, result)
    return result


# ═══════════════════════════════════════════════════════════════
#  3. SPECIFIC STRIKE PRICE LOOKUP — Real price for ANY strike
# ═══════════════════════════════════════════════════════════════

def get_strike_price(symbol: str, strike: float, option_type: str = "CE") -> Dict[str, Any]:
    """
    Get REAL price for a specific option strike.
    Returns: {strike, type, ltp, iv, oi, volume, delta, bid, ask, moneyness}
    """
    chain = fetch_live_option_chain(symbol)
    if not chain or not chain.strikes:
        return {"error": f"Option chain not available for {symbol}"}
    
    # Find closest strike
    closest = min(chain.strikes, key=lambda s: abs(s.strike - strike))
    
    if option_type.upper() == "CE":
        return {
            "symbol": symbol,
            "strike": closest.strike,
            "type": "CE",
            "ltp": closest.ce_ltp,
            "iv": closest.ce_iv,
            "oi": closest.ce_oi,
            "volume": closest.ce_volume,
            "delta": closest.ce_delta,
            "bid": closest.ce_bid,
            "ask": closest.ce_ask,
            "oi_change": closest.ce_oi_change,
            "change": closest.ce_change,
            "moneyness": closest.moneyness,
            "spot": chain.spot,
            "lot_size": chain.lot_size,
            "is_real": chain.is_real_data,
            "source": chain.source,
        }
    else:
        return {
            "symbol": symbol,
            "strike": closest.strike,
            "type": "PE",
            "ltp": closest.pe_ltp,
            "iv": closest.pe_iv,
            "oi": closest.pe_oi,
            "volume": closest.pe_volume,
            "delta": closest.pe_delta,
            "bid": closest.pe_bid,
            "ask": closest.pe_ask,
            "oi_change": closest.pe_oi_change,
            "change": closest.pe_change,
            "moneyness": closest.moneyness,
            "spot": chain.spot,
            "lot_size": chain.lot_size,
            "is_real": chain.is_real_data,
            "source": chain.source,
        }


# ═══════════════════════════════════════════════════════════════
#  4. ATM/OTM ANALYSIS — Real prices + Greeks + Scoring
# ═══════════════════════════════════════════════════════════════

def get_atm_otm_analysis(symbol: str = "NIFTY", budget: float = 2000,
                          direction: str = "auto", num_strikes: int = 8) -> Dict[str, Any]:
    """
    NUCLEAR ATM↔OTM analysis with REAL prices.
    Returns best options for given budget with real LTP, Greeks, scoring.
    """
    chain = fetch_live_option_chain(symbol)
    if not chain or not chain.strikes:
        return {"error": f"Option chain not available for {symbol}"}
    
    spot = chain.spot
    atm = chain.atm_strike
    step = chain.step
    lot = chain.lot_size
    dte = max(chain.days_to_expiry, 1)
    T = dte / 365
    
    # Auto-detect direction from PCR
    if direction == "auto":
        if chain.pcr_oi > 1.1:
            direction = "BULLISH"
        elif chain.pcr_oi < 0.7:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"
    
    calls = []
    puts = []
    
    for s in chain.strikes:
        # Skip far OTM
        if abs(s.strike - spot) > step * 15:
            continue
        
        # Call analysis (for bullish)
        if s.ce_ltp > 0:
            lots_fit = int(budget / (s.ce_ltp * lot)) if s.ce_ltp * lot > 0 else 0
            total_cost = s.ce_ltp * lot * max(lots_fit, 1)
            
            # Profit scenarios using REAL premium
            profits = {}
            for move_pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
                new_spot = spot * (1 + move_pct / 100)
                new_intrinsic = max(0, new_spot - s.strike)
                # Approximate new premium (intrinsic + time value decay)
                time_decay_factor = max(0.3, 1 - (1 / max(dte, 1)))
                new_premium = new_intrinsic + max(0, (s.ce_ltp - max(0, spot - s.strike))) * time_decay_factor
                profit_per_lot = (new_premium - s.ce_ltp) * lot
                roi_pct = ((new_premium - s.ce_ltp) / s.ce_ltp) * 100 if s.ce_ltp > 0 else 0
                profits[f"{move_pct}%"] = {"profit": round(profit_per_lot, 2), "roi": round(roi_pct, 1)}
            
            # Score
            score = _score_option_real(s.ce_ltp, s.ce_delta, s.ce_iv, s.ce_oi, 
                                        s.strike, spot, budget, lot, "CE", dte)
            
            calls.append({
                "strike": s.strike,
                "ltp": s.ce_ltp,
                "iv": s.ce_iv,
                "oi": s.ce_oi,
                "volume": s.ce_volume,
                "delta": s.ce_delta,
                "oi_change": s.ce_oi_change,
                "moneyness": _get_moneyness(s.strike, spot, "CE"),
                "cost_per_lot": round(s.ce_ltp * lot, 2),
                "lots_in_budget": lots_fit,
                "total_cost": round(total_cost, 2),
                "profits": profits,
                "score": score,
                "bid": s.ce_bid,
                "ask": s.ce_ask,
            })
        
        # Put analysis (for bearish)
        if s.pe_ltp > 0:
            lots_fit = int(budget / (s.pe_ltp * lot)) if s.pe_ltp * lot > 0 else 0
            total_cost = s.pe_ltp * lot * max(lots_fit, 1)
            
            profits = {}
            for move_pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
                new_spot = spot * (1 - move_pct / 100)
                new_intrinsic = max(0, s.strike - new_spot)
                time_decay_factor = max(0.3, 1 - (1 / max(dte, 1)))
                new_premium = new_intrinsic + max(0, (s.pe_ltp - max(0, s.strike - spot))) * time_decay_factor
                profit_per_lot = (new_premium - s.pe_ltp) * lot
                roi_pct = ((new_premium - s.pe_ltp) / s.pe_ltp) * 100 if s.pe_ltp > 0 else 0
                profits[f"{move_pct}%"] = {"profit": round(profit_per_lot, 2), "roi": round(roi_pct, 1)}
            
            score = _score_option_real(s.pe_ltp, abs(s.pe_delta), s.pe_iv, s.pe_oi,
                                        s.strike, spot, budget, lot, "PE", dte)
            
            puts.append({
                "strike": s.strike,
                "ltp": s.pe_ltp,
                "iv": s.pe_iv,
                "oi": s.pe_oi,
                "volume": s.pe_volume,
                "delta": s.pe_delta,
                "oi_change": s.pe_oi_change,
                "moneyness": _get_moneyness(s.strike, spot, "PE"),
                "cost_per_lot": round(s.pe_ltp * lot, 2),
                "lots_in_budget": lots_fit,
                "total_cost": round(total_cost, 2),
                "profits": profits,
                "score": score,
                "bid": s.pe_bid,
                "ask": s.pe_ask,
            })
    
    # Sort by score descending
    calls.sort(key=lambda x: x["score"], reverse=True)
    puts.sort(key=lambda x: x["score"], reverse=True)
    
    # Best picks
    best_calls = calls[:num_strikes]
    best_puts = puts[:num_strikes]
    
    return {
        "symbol": symbol,
        "spot": spot,
        "atm_strike": atm,
        "direction": direction,
        "pcr": chain.pcr_oi,
        "max_pain": chain.max_pain,
        "straddle_premium": chain.straddle_premium,
        "expected_range": chain.expected_range,
        "resistance": chain.max_ce_oi_strike,
        "support": chain.max_pe_oi_strike,
        "days_to_expiry": dte,
        "lot_size": lot,
        "budget": budget,
        "best_calls": best_calls,
        "best_puts": best_puts,
        "total_calls": len(calls),
        "total_puts": len(puts),
        "is_real_data": chain.is_real_data,
        "source": chain.source,
        "timestamp": chain.timestamp,
    }


def _score_option_real(ltp, delta, iv, oi, strike, spot, budget, lot, opt_type, dte):
    """Score an option based on real market data."""
    score = 0
    
    # 1. Budget fit (25 pts) — can we buy at least 1 lot?
    cost_per_lot = ltp * lot
    if cost_per_lot <= budget and cost_per_lot > 0:
        lots = int(budget / cost_per_lot)
        score += min(25, lots * 8)
    elif cost_per_lot > 0:
        score += max(0, 15 - (cost_per_lot - budget) / budget * 10)
    
    # 2. Delta sweet spot (25 pts) — 0.20-0.50 best for directional
    abs_delta = abs(delta) if delta else 0
    if 0.20 <= abs_delta <= 0.50:
        score += 25
    elif 0.15 <= abs_delta <= 0.60:
        score += 18
    elif 0.10 <= abs_delta <= 0.70:
        score += 10
    elif abs_delta > 0.70:
        score += 5  # ITM, less leverage
    
    # 3. OI presence (15 pts) — higher OI = more liquid
    if oi > 1000000:
        score += 15
    elif oi > 500000:
        score += 12
    elif oi > 100000:
        score += 8
    elif oi > 10000:
        score += 5
    
    # 4. IV consideration (15 pts) — moderate IV is ideal
    if 10 < iv < 20:
        score += 15
    elif 8 < iv < 30:
        score += 10
    elif iv > 40:
        score += 3  # High IV = expensive
    
    # 5. Moneyness ROI potential (20 pts)
    distance_pct = abs(strike - spot) / spot * 100
    if opt_type == "CE":
        if 0 <= distance_pct <= 1:
            score += 20  # ATM/near ATM
        elif 1 < distance_pct <= 2:
            score += 15  # Slightly OTM
        elif 2 < distance_pct <= 4:
            score += 10  # OTM with moonshot
        elif distance_pct > 4:
            score += 5   # Far OTM lottery
    else:
        if 0 <= distance_pct <= 1:
            score += 20
        elif 1 < distance_pct <= 2:
            score += 15
        elif 2 < distance_pct <= 4:
            score += 10
        elif distance_pct > 4:
            score += 5
    
    return round(score, 1)


# ═══════════════════════════════════════════════════════════════
#  5. FORMATTING — Beautiful Telegram output
# ═══════════════════════════════════════════════════════════════

def format_option_chain_telegram(chain: LiveOptionChain, num_strikes: int = 10) -> str:
    """Format option chain for Telegram message."""
    if not chain or not chain.strikes:
        return "❌ Option chain data not available"
    
    spot = chain.spot
    atm = chain.atm_strike
    step = chain.step
    
    # Get strikes around ATM
    nearby = [s for s in chain.strikes if abs(s.strike - atm) <= step * num_strikes // 2]
    nearby.sort(key=lambda s: s.strike)
    
    msg = (
        f"📊 *{chain.symbol} LIVE OPTION CHAIN*\n"
        f"{'━' * 38}\n"
        f"💹 *Spot:* ₹{spot:,.2f}\n"
        f"🎯 *ATM:* ₹{atm:,.0f}\n"
        f"📅 *Expiry:* {chain.days_to_expiry} days\n"
        f"📊 *PCR (OI):* {chain.pcr_oi:.2f}\n"
        f"🛡️ *Support (Max PE OI):* ₹{chain.max_pe_oi_strike:,.0f}\n"
        f"🚧 *Resistance (Max CE OI):* ₹{chain.max_ce_oi_strike:,.0f}\n"
        f"🎯 *Max Pain:* ₹{chain.max_pain:,.0f}\n"
        f"⚡ *Straddle:* ₹{chain.straddle_premium:,.2f}\n"
        f"📐 *Range:* ₹{chain.expected_range[0]:,.0f} - ₹{chain.expected_range[1]:,.0f}\n"
        f"📡 *Source:* {chain.source} {'✅' if chain.is_real_data else '⚠️ Synthetic'}\n"
        f"🕐 *Updated:* {chain.timestamp}\n"
        f"{'━' * 38}\n\n"
    )
    
    msg += f"{'CE Price':>10} {'CE OI':>8} │ {'Strike':^8} │ {'PE OI':>8} {'PE Price':>10}\n"
    msg += f"{'─' * 10} {'─' * 8} │ {'─' * 8} │ {'─' * 8} {'─' * 10}\n"
    
    for s in nearby:
        atm_marker = "◄" if abs(s.strike - atm) < step * 0.5 else " "
        ce_price_str = f"₹{s.ce_ltp:>7.2f}" if s.ce_ltp > 0 else f"{'--':>8}"
        pe_price_str = f"₹{s.pe_ltp:>7.2f}" if s.pe_ltp > 0 else f"{'--':>8}"
        ce_oi_str = f"{s.ce_oi // 1000}K" if s.ce_oi >= 1000 else str(s.ce_oi)
        pe_oi_str = f"{s.pe_oi // 1000}K" if s.pe_oi >= 1000 else str(s.pe_oi)
        
        msg += f"{ce_price_str} {ce_oi_str:>8} │ {s.strike:>7.0f}{atm_marker} │ {pe_oi_str:>8} {pe_price_str}\n"
    
    return msg


def format_atm_otm_analysis(analysis: Dict, opt_type: str = "CE") -> str:
    """Format ATM/OTM analysis for Telegram."""
    if "error" in analysis:
        return f"❌ {analysis['error']}"
    
    symbol = analysis["symbol"]
    spot = analysis["spot"]
    direction = analysis["direction"]
    budget = analysis["budget"]
    
    options = analysis["best_calls"] if opt_type == "CE" else analysis["best_puts"]
    type_name = "CALL" if opt_type == "CE" else "PUT"
    
    msg = (
        f"🔥 *{symbol} BEST {type_name} OPTIONS* 🔥\n"
        f"{'━' * 38}\n"
        f"💹 Spot: ₹{spot:,.2f} | Direction: {direction}\n"
        f"💰 Budget: ₹{budget:,.0f} | Lot: {analysis['lot_size']}\n"
        f"📅 Expiry: {analysis['days_to_expiry']} days\n"
        f"📊 PCR: {analysis['pcr']:.2f} | Max Pain: ₹{analysis['max_pain']:,.0f}\n"
        f"🛡️ Support: ₹{analysis['support']:,.0f} | 🚧 Resistance: ₹{analysis['resistance']:,.0f}\n"
        f"📡 Data: {analysis['source']} {'✅' if analysis['is_real_data'] else '⚠️'}\n"
        f"{'━' * 38}\n\n"
    )
    
    for i, opt in enumerate(options[:6], 1):
        moneyness = opt["moneyness"]
        emoji = "🟢" if moneyness == "ATM" else ("🔵" if moneyness == "ITM" else "🟡")
        
        msg += (
            f"{emoji} *#{i} — ₹{opt['strike']:,.0f} {type_name}* ({moneyness})\n"
            f"   💰 LTP: *₹{opt['ltp']:,.2f}* | Cost/Lot: ₹{opt['cost_per_lot']:,.0f}\n"
            f"   📊 IV: {opt['iv']:.1f}% | Delta: {opt['delta']:.2f}\n"
            f"   📈 OI: {opt['oi']:,} | Vol: {opt['volume']:,}\n"
            f"   🏆 Score: *{opt['score']:.0f}/100*\n"
        )
        
        if opt.get("profits"):
            msg += f"   📈 If +1% move: ROI *{opt['profits'].get('1.0%', {}).get('roi', 0):+.0f}%* (₹{opt['profits'].get('1.0%', {}).get('profit', 0):+,.0f})\n"
            msg += f"   🚀 If +2% move: ROI *{opt['profits'].get('2.0%', {}).get('roi', 0):+.0f}%* (₹{opt['profits'].get('2.0%', {}).get('profit', 0):+,.0f})\n"
        
        msg += "\n"
    
    return msg


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _bs_price(S, K, T, r, sigma, opt_type="CE"):
    """Black-Scholes option price."""
    if T <= 0 or sigma <= 0:
        return max(0, S - K) if opt_type == "CE" else max(0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    ncdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    if opt_type == "CE":
        return S * ncdf(d1) - K * math.exp(-r * T) * ncdf(d2)
    return K * math.exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)


def _quick_delta(S, K, T, sigma, opt_type="CE"):
    """Quick delta calculation."""
    if T <= 0 or sigma <= 0:
        if opt_type == "CE":
            return 1.0 if S > K else 0.0
        return -1.0 if K > S else 0.0
    d1 = (math.log(S / K) + (RISK_FREE_RATE + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    ncdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    if opt_type == "CE":
        return round(ncdf(d1), 4)
    return round(ncdf(d1) - 1, 4)


def _calc_max_pain_from_strikes(strikes: List[LiveOptionStrike]) -> float:
    """Calculate max pain from real OI data."""
    if not strikes:
        return 0
    
    min_pain = float('inf')
    max_pain_strike = strikes[len(strikes) // 2].strike
    
    for target in strikes:
        total_pain = 0
        for s in strikes:
            ce_pain = max(0, target.strike - s.strike) * s.ce_oi
            pe_pain = max(0, s.strike - target.strike) * s.pe_oi
            total_pain += ce_pain + pe_pain
        
        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = target.strike
    
    return max_pain_strike


def _calc_days_to_expiry(expiry_str: Optional[str], expiry_day: int = 3) -> int:
    """Calculate days to next expiry."""
    now = datetime.now()
    
    if expiry_str:
        try:
            # NSE format: "28-Nov-2025"
            expiry = datetime.strptime(expiry_str, "%d-%b-%Y")
            dte = (expiry - now).days
            if dte >= 0:
                return max(1, dte)
        except Exception:
            pass
    
    # Calculate next expiry day
    current_day = now.weekday()
    days_ahead = (expiry_day - current_day) % 7
    if days_ahead == 0 and now.hour >= 15:
        days_ahead = 7
    
    return max(1, days_ahead)


def _get_moneyness(strike: float, spot: float, opt_type: str) -> str:
    """Determine moneyness of an option."""
    diff_pct = abs(strike - spot) / spot * 100
    
    if diff_pct < 0.3:
        return "ATM"
    
    if opt_type == "CE":
        return "ITM" if strike < spot else "OTM"
    else:
        return "ITM" if strike > spot else "OTM"


# ═══════════════════════════════════════════════════════════════
#  MODULE STATUS
# ═══════════════════════════════════════════════════════════════

NSE_LIVE_AVAILABLE = True
logger.info("[NSE-LIVE] 🔥 NSE Live Engine loaded — REAL option chain + ATM/OTM pricing!")
