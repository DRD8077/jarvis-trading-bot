"""
========================================================================================
  NSE OPTION CHAIN FETCHER — Enhanced for Indian Market (INR Only)
========================================================================================

Features:
  - NSE API option chain fetching with cookie management
  - Fallback to saved snapshots
  - Advanced OI analysis with PCR ratio
  - IV skew analysis
  - Max Pain calculation
  - Heuristic + ML signal generation
  - All prices in INR (₹)
"""

from typing import Tuple, Dict, Any, Optional
import time
import requests
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("stock_data_fetcher")


# ═══════════════════════════════════════════════════════════════════════════
#  NSE SESSION & API
# ═══════════════════════════════════════════════════════════════════════════

def _create_nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.nseindia.com/",
    })
    base = "https://www.nseindia.com/"
    try:
        r = s.get(base, timeout=10)
        r.raise_for_status()
    except Exception:
        pass
    return s


def fetch_nse_option_chain(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch option chain JSON for a given equity symbol from NSE.
    Returns parsed JSON or None on failure.
    """
    session = _create_nse_session()
    api = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
    try:
        r = session.get(api, timeout=10)
        r.raise_for_status()
        js = r.json()
        records = js.get('records', {})
        if not records or not records.get('data'):
            # Try fallback
            try:
                from data_store import get_recent_snapshots
                snaps = get_recent_snapshots(symbol, limit=1)
                if snaps:
                    s = snaps[0]
                    underlying = s.get('underlying')
                    calls = s.get('calls', [])
                    puts = s.get('puts', [])
                    strikes = {}
                    for c in calls:
                        st = int(c.get('strike', c.get('strikePrice', 0)))
                        strikes.setdefault(st, {})['CE'] = c
                    for p in puts:
                        st = int(p.get('strike', p.get('strikePrice', 0)))
                        strikes.setdefault(st, {})['PE'] = p
                    data = []
                    for st, sides in strikes.items():
                        item = {'strikePrice': st}
                        if 'CE' in sides:
                            item['CE'] = sides['CE']
                        if 'PE' in sides:
                            item['PE'] = sides['PE']
                        data.append(item)
                    return {'records': {'underlyingValue': underlying, 'data': data}}
            except Exception as e:
                logger.debug(f'Fallback unavailable: {e}')
        return js
    except Exception as e:
        logger.error(f"Failed to fetch NSE option chain: {e}")
        return None


def parse_option_chain_json(js: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """Parse NSE option chain JSON into calls/puts DataFrames and underlying price.
    Returns (calls_df, puts_df, underlying_price) — all in INR.
    """
    records = js.get("records", {})
    underlying = records.get("underlyingValue") or records.get("underlying") or 0.0
    rows = records.get("data", [])

    calls = []
    puts = []
    for r in rows:
        strike = r.get("strikePrice")
        if "CE" in r and r["CE"]:
            ce = r["CE"].copy()
            ce.update({"strike": strike})
            calls.append(ce)
        if "PE" in r and r["PE"]:
            pe = r["PE"].copy()
            pe.update({"strike": strike})
            puts.append(pe)

    calls_df = pd.DataFrame(calls)
    puts_df = pd.DataFrame(puts)

    for df in (calls_df, puts_df):
        if not df.empty:
            df.fillna(0, inplace=True)

    return calls_df, puts_df, float(underlying)


# ═══════════════════════════════════════════════════════════════════════════
#  MAX PAIN CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

def calculate_max_pain(calls_df: pd.DataFrame, puts_df: pd.DataFrame) -> float:
    """Calculate Max Pain — the strike price where option sellers have minimum loss."""
    if calls_df.empty or puts_df.empty or 'strike' not in calls_df.columns:
        return 0.0

    strikes = sorted(set(calls_df['strike'].tolist() + puts_df['strike'].tolist()))
    min_pain = float('inf')
    max_pain_strike = 0

    for s in strikes:
        total_pain = 0
        # Pain to call writers
        for _, row in calls_df.iterrows():
            if row['strike'] < s:
                oi = row.get('openInterest', row.get('OI', 0))
                total_pain += (s - row['strike']) * float(oi)
        # Pain to put writers
        for _, row in puts_df.iterrows():
            if row['strike'] > s:
                oi = row.get('openInterest', row.get('OI', 0))
                total_pain += (row['strike'] - s) * float(oi)

        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = s

    return float(max_pain_strike)


# ═══════════════════════════════════════════════════════════════════════════
#  ADVANCED OPTION CHAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_option_chain(calls_df: pd.DataFrame, puts_df: pd.DataFrame,
                         underlying: float) -> Dict[str, Any]:
    """Advanced AI-powered option chain analysis.
    All values in INR (₹).
    """
    result = {
        "market_trend": "unknown",
        "recommendation": "hold",
        "net_oi_change": 0.0,
        "call_put_oi_ratio": None,
        "max_pain": 0.0,
        "pcr": 0.0,
        "iv_skew": 0.0,
        "support": 0.0,
        "resistance": 0.0,
        "confidence": 0.0,
    }

    if calls_df.empty or puts_df.empty:
        return result

    # Near-the-money (within 5%)
    tol = underlying * 0.05
    near_calls = calls_df[abs(calls_df["strike"] - underlying) <= tol]
    near_puts = puts_df[abs(puts_df["strike"] - underlying) <= tol]

    # OI analysis
    oi_col = "openInterest" if "openInterest" in near_calls.columns else "OI"
    chng_col = "changeinOpenInterest" if "changeinOpenInterest" in near_calls.columns else "changeInOpenInterest"

    call_oi = float(near_calls[oi_col].sum()) if oi_col in near_calls.columns else 0
    put_oi = float(near_puts[oi_col].sum()) if oi_col in near_puts.columns else 0
    call_chng_oi = float(near_calls[chng_col].sum()) if chng_col in near_calls.columns else 0
    put_chng_oi = float(near_puts[chng_col].sum()) if chng_col in near_puts.columns else 0

    net_chng = call_chng_oi - put_chng_oi
    result["net_oi_change"] = net_chng

    # PCR (Put-Call Ratio)
    pcr = put_oi / (call_oi + 1)
    result["pcr"] = round(pcr, 3)

    # Call/Put OI Ratio
    ratio = call_oi / (put_oi + 1)
    result["call_put_oi_ratio"] = round(float(ratio), 3)

    # Max Pain
    result["max_pain"] = calculate_max_pain(calls_df, puts_df)

    # IV Skew (CE IV vs PE IV near ATM)
    iv_col = "impliedVolatility" if "impliedVolatility" in near_calls.columns else "IV"
    call_iv = float(near_calls[iv_col].mean()) if iv_col in near_calls.columns and not near_calls.empty else 0
    put_iv = float(near_puts[iv_col].mean()) if iv_col in near_puts.columns and not near_puts.empty else 0
    result["iv_skew"] = round(put_iv - call_iv, 3)

    # Support (highest put OI strike below underlying)
    puts_below = puts_df[puts_df["strike"] < underlying]
    if not puts_below.empty and oi_col in puts_below.columns:
        result["support"] = float(puts_below.loc[puts_below[oi_col].idxmax(), "strike"])

    # Resistance (highest call OI strike above underlying)
    calls_above = calls_df[calls_df["strike"] > underlying]
    if not calls_above.empty and oi_col in calls_above.columns:
        result["resistance"] = float(calls_above.loc[calls_above[oi_col].idxmax(), "strike"])

    # ═══ Signal Generation ═══
    signal_score = 0.0
    reasons = []

    # PCR analysis
    if pcr > 1.2:
        signal_score += 0.2
        reasons.append(f"PCR {pcr:.2f} > 1.2 (bullish — more puts = support)")
    elif pcr < 0.7:
        signal_score -= 0.2
        reasons.append(f"PCR {pcr:.2f} < 0.7 (bearish — more calls = resistance)")

    # OI change
    if net_chng > 0 and ratio > 1.1:
        signal_score += 0.15
        reasons.append("Net call OI increasing + high CE/PE ratio")
    elif net_chng < 0 and ratio < 0.9:
        signal_score -= 0.15
        reasons.append("Net put OI increasing + low CE/PE ratio")

    # IV skew
    if result["iv_skew"] > 5:
        signal_score += 0.1
        reasons.append(f"Put IV > Call IV (fear premium — bullish contrarian)")
    elif result["iv_skew"] < -5:
        signal_score -= 0.1
        reasons.append(f"Call IV > Put IV (greed — bearish contrarian)")

    # Max pain proximity
    max_pain = result["max_pain"]
    if max_pain > 0:
        mp_diff = (underlying - max_pain) / underlying * 100
        if mp_diff > 1:
            signal_score -= 0.1
            reasons.append(f"Price above Max Pain ₹{max_pain:,.0f} — may pull back")
        elif mp_diff < -1:
            signal_score += 0.1
            reasons.append(f"Price below Max Pain ₹{max_pain:,.0f} — may rally")

    signal_score = max(-1, min(1, signal_score))
    confidence = abs(signal_score)

    if signal_score > 0.15:
        trend = "bullish"
        rec = "buy_calls"
    elif signal_score < -0.15:
        trend = "bearish"
        rec = "buy_puts"
    else:
        trend = "sideways"
        rec = "hold"

    result["market_trend"] = trend
    result["recommendation"] = rec
    result["confidence"] = round(confidence, 3)
    result["underlying"] = underlying
    result["timestamp"] = int(time.time())
    result["reasons"] = reasons

    return result


# ═══════════════════════════════════════════════════════════════════════════
#  FORMAT SIGNAL MESSAGE
# ═══════════════════════════════════════════════════════════════════════════

def format_signal_message(symbol: str, analysis: Dict[str, Any]) -> str:
    """Format option chain analysis as rich Telegram message."""
    trend = analysis.get('market_trend', 'unknown')
    rec = analysis.get("recommendation", "hold")

    if rec == "buy_calls":
        emoji = "🟢🚀"
        human = "BUY Calls (CE) — Bullish"
    elif rec == "buy_puts":
        emoji = "🔴📉"
        human = "BUY Puts (PE) — Bearish"
    else:
        emoji = "🟡"
        human = "HOLD / Wait"

    lines = [
        f"📊 *{symbol} Option Chain Analysis* 📊",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💹 Underlying: ₹{analysis.get('underlying', 0):,.2f}",
        f"📈 Trend: *{trend.upper()}*",
        f"{emoji} Recommendation: *{human}*",
        f"🎯 Confidence: {analysis.get('confidence', 0):.0%}",
        f"",
        f"📊 *Key Metrics:*",
        f"  PCR: {analysis.get('pcr', 0):.3f}",
        f"  CE/PE OI Ratio: {analysis.get('call_put_oi_ratio', 0):.3f}",
        f"  Net OI Change: {analysis.get('net_oi_change', 0):+,.0f}",
        f"  IV Skew (PE-CE): {analysis.get('iv_skew', 0):+.2f}",
        f"  Max Pain: ₹{analysis.get('max_pain', 0):,.0f}",
        f"",
        f"📐 *Levels:*",
        f"  Support: ₹{analysis.get('support', 0):,.0f}",
        f"  Resistance: ₹{analysis.get('resistance', 0):,.0f}",
    ]

    reasons = analysis.get("reasons", [])
    if reasons:
        lines.append(f"\n📋 *Analysis Reasons:*")
        for r in reasons:
            lines.append(f"  • {r}")

    lines.extend([
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"⚠️ _Not financial advice. Use SL._",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    data = fetch_nse_option_chain("RELIANCE")
    if data:
        calls, puts, u = parse_option_chain_json(data)
        a = analyze_option_chain(calls, puts, u)
        print(format_signal_message("RELIANCE", a))
