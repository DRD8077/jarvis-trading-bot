"""Utilities to fetch and analyze NSE option chain data.

This module uses NSE's public JSON endpoints (via requests + session
cookie) instead of browser automation. It provides a simple heuristic
signal generator useful for integrating into the Telegram bot.
"""

from typing import Tuple, Dict, Any, Optional
import time
import requests
import pandas as pd


def _create_nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    })
    # Prime cookies by hitting the homepage
    base = "https://www.nseindia.com/"
    try:
        r = s.get(base, timeout=10)
        r.raise_for_status()
    except Exception:
        # still return session; later requests may work if API is accessible
        pass
    return s


def fetch_nse_option_chain(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch option chain JSON for a given equity symbol.

    Returns the parsed JSON (records/data) or None on failure.
    """
    session = _create_nse_session()
    api = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
    try:
        r = session.get(api, timeout=10)
        r.raise_for_status()
        js = r.json()
        # If NSE returned empty JSON (bot protection), fall back to latest saved snapshot
        records = js.get('records', {})
        if not records or not records.get('data'):
            try:
                from data_store import get_recent_snapshots
                snaps = get_recent_snapshots(symbol, limit=1)
                if snaps:
                    s = snaps[0]
                    underlying = s.get('underlying')
                    calls = s.get('calls', [])
                    puts = s.get('puts', [])
                    # build records/data list matching NSE structure
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
                    fallback_js = {'records': {'underlyingValue': underlying, 'data': data}}
                    print('Using fallback snapshot for', symbol)
                    return fallback_js
            except Exception as e:
                print('Fallback snapshot unavailable:', e)
        return js
    except Exception as e:
        print("Failed to fetch NSE option chain via API:", e)
        return None


def parse_option_chain_json(js: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """Parse NSE option chain JSON into calls/puts DataFrames and underlying price.

    Returns (calls_df, puts_df, underlying_price)
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

    # Normalize common columns and fill NaNs
    for df in (calls_df, puts_df):
        if not df.empty:
            df.fillna(0, inplace=True)

    return calls_df, puts_df, float(underlying)


def analyze_option_chain(calls_df: pd.DataFrame, puts_df: pd.DataFrame, underlying: float) -> Dict[str, Any]:
    """Produce heuristic AI-like signals from option chain data.

    This is a rule-based signal generator (fast to run). It returns a
    dictionary with `market_trend` and `recommendation` plus supporting
    metrics. You can replace this with an ML model later.
    """
    result = {
        "market_trend": "unknown",
        "recommendation": "hold",
        "net_oi_change": 0.0,
        "call_put_oi_ratio": None,
    }

    if calls_df.empty or puts_df.empty:
        return result

    # Focus on near-the-money strikes (within 5% of underlying)
    tol = underlying * 0.05
    near_calls = calls_df[abs(calls_df["strike"] - underlying) <= tol]
    near_puts = puts_df[abs(puts_df["strike"] - underlying) <= tol]

    # Aggregate metrics
    call_chng_oi = near_calls["changeinOpenInterest"].sum() if "changeinOpenInterest" in near_calls else 0
    put_chng_oi = near_puts["changeinOpenInterest"].sum() if "changeinOpenInterest" in near_puts else 0
    call_oi = near_calls["openInterest"].sum() if "openInterest" in near_calls else 0
    put_oi = near_puts["openInterest"].sum() if "openInterest" in near_puts else 0

    net_chng = float(call_chng_oi) - float(put_chng_oi)
    result["net_oi_change"] = net_chng

    ratio = (call_oi / (put_oi + 1)) if put_oi >= 0 else None
    result["call_put_oi_ratio"] = float(ratio) if ratio is not None else None

    # Heuristic rules
    if net_chng > 0 and ratio and ratio > 1.1:
        trend = "bullish"
        rec = "buy_calls"
    elif net_chng < 0 and ratio and ratio < 0.9:
        trend = "bearish"
        rec = "buy_puts"
    else:
        # look at IV and volume changes as tie-breakers
        call_iv = near_calls["impliedVolatility"].mean() if "impliedVolatility" in near_calls and not near_calls.empty else 0
        put_iv = near_puts["impliedVolatility"].mean() if "impliedVolatility" in near_puts and not near_puts.empty else 0
        if call_iv < put_iv:
            trend = "bullish"
            rec = "buy_calls"
        elif put_iv < call_iv:
            trend = "bearish"
            rec = "buy_puts"
        else:
            trend = "sideways"
            rec = "hold"

    result["market_trend"] = trend
    result["recommendation"] = rec
    result["underlying"] = underlying
    result["timestamp"] = int(time.time())
    return result


def format_signal_message(symbol: str, analysis: Dict[str, Any]) -> str:
    msg = [f"Signal for {symbol}: \n"]
    msg.append(f"Market trend: {analysis.get('market_trend')}")
    rec = analysis.get("recommendation")
    if rec == "buy_calls":
        human = "Recommendation: BUY Calls (aggressive)"
    elif rec == "buy_puts":
        human = "Recommendation: BUY Puts (aggressive)"
    else:
        human = "Recommendation: HOLD / Wait"
    msg.append(human)
    msg.append(f"Net OI change (near ATM): {analysis.get('net_oi_change')}")
    msg.append(f"Call/Put OI ratio (near ATM): {analysis.get('call_put_oi_ratio')}")
    msg.append(f"Underlying: {analysis.get('underlying')}")
    return "\n".join(msg)


if __name__ == "__main__":
    # quick local test
    data = fetch_nse_option_chain("RELIANCE")
    if data:
        calls, puts, u = parse_option_chain_json(data)
        a = analyze_option_chain(calls, puts, u)
        print(format_signal_message("RELIANCE", a))
