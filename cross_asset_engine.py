"""
🔗 J.A.R.V.I.S. CROSS-ASSET CORRELATION ENGINE
═══════════════════════════════════════════════════
Analyzes correlations between different assets to detect:
  - BTC/ETH divergence → reversal signal
  - NIFTY/DXY inverse correlation → INR impact
  - Gold/USD correlation → safe haven flows
  - Sector rotation patterns
  - Hidden correlations that keyword analysis misses

This helps JARVIS give context-aware advice like:
"BTC ₿ upar gaya but ETH nahi — divergence hai, careful!"

Author: JARVIS AI Core
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pytz

logger = logging.getLogger("cross_asset_engine")
IST = pytz.timezone('Asia/Kolkata')

# Correlation cache (refresh every 30 min)
_correlation_cache: Dict[str, Any] = {}
_cache_timestamp: float = 0
_CACHE_TTL = 1800  # 30 minutes

# ═══════════════════════════════════════════════════════════
#  PREDEFINED ASSET PAIRS TO MONITOR
# ═══════════════════════════════════════════════════════════

CRYPTO_PAIRS = [
    ("BTC", "ETH"),         # King vs Queen
    ("BTC", "SOL"),         # BTC vs Solana
    ("BTC", "BNB"),         # BTC vs Binance
    ("ETH", "SOL"),         # Ethereum vs Solana
]

STOCK_PAIRS = [
    ("^NSEI", "^BSESN"),   # NIFTY vs SENSEX (should be ~1.0)
    ("^NSEI", "DX-Y.NYB"), # NIFTY vs Dollar Index (inverse)
    ("^NSEI", "GC=F"),     # NIFTY vs Gold
    ("^NSEI", "^GSPC"),    # NIFTY vs S&P 500
]

CROSS_ASSET_PAIRS = [
    ("BTC-USD", "^NSEI"),   # Bitcoin vs Indian market
    ("GC=F", "DX-Y.NYB"),  # Gold vs Dollar (inverse)
    ("BTC-USD", "GC=F"),   # Bitcoin vs Gold
]


# ═══════════════════════════════════════════════════════════
#  PRICE FETCHING
# ═══════════════════════════════════════════════════════════

def _fetch_price_history(symbol: str, days: int = 30) -> Optional[List[float]]:
    """Fetch daily closing prices for a symbol."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d")
        if hist.empty:
            return None
        return hist['Close'].tolist()
    except Exception as e:
        logger.debug(f"Failed to fetch {symbol}: {e}")
        return None


def _fetch_crypto_history(symbol: str, days: int = 30) -> Optional[List[float]]:
    """Fetch crypto price history via yfinance (symbol-USD)."""
    # Try CoinDCX first for Indian prices
    try:
        from coindcx_engine import coindcx_quick_price
        price = coindcx_quick_price(symbol.upper())
        if price:
            # CoinDCX doesn't give history easily, use yfinance
            pass
    except Exception:
        pass
    
    return _fetch_price_history(f"{symbol}-USD", days)


# ═══════════════════════════════════════════════════════════
#  CORRELATION COMPUTATION
# ═══════════════════════════════════════════════════════════

def compute_correlation(prices_a: List[float], prices_b: List[float]) -> Dict[str, float]:
    """Compute correlation metrics between two price series.
    
    Returns:
        correlation: -1 to +1 Pearson correlation
        rolling_corr: Recent 7-day correlation
        trend_a: % change in A
        trend_b: % change in B
        divergence: True if trends are diverging from historical correlation
    """
    # Align lengths
    min_len = min(len(prices_a), len(prices_b))
    if min_len < 5:
        return {"correlation": 0, "error": "Insufficient data"}
    
    a = np.array(prices_a[-min_len:])
    b = np.array(prices_b[-min_len:])
    
    # Returns (% changes)
    returns_a = np.diff(a) / a[:-1]
    returns_b = np.diff(b) / b[:-1]
    
    if len(returns_a) < 3:
        return {"correlation": 0, "error": "Insufficient data"}
    
    # Full period correlation
    full_corr = float(np.corrcoef(returns_a, returns_b)[0, 1])
    
    # Recent 7-day correlation
    recent_corr = full_corr
    if len(returns_a) >= 7:
        recent_corr = float(np.corrcoef(returns_a[-7:], returns_b[-7:])[0, 1])
    
    # Trends
    trend_a = float((a[-1] - a[0]) / a[0] * 100) if a[0] > 0 else 0
    trend_b = float((b[-1] - b[0]) / b[0] * 100) if b[0] > 0 else 0
    
    # Divergence detection
    # If historically correlated but recently diverging
    divergence = False
    if abs(full_corr) > 0.5 and abs(recent_corr - full_corr) > 0.3:
        divergence = True
    # If both should move together but one is flat/opposite
    if full_corr > 0.5 and trend_a * trend_b < 0:  # Going opposite directions
        divergence = True
    
    return {
        "correlation": round(full_corr, 3),
        "recent_correlation": round(recent_corr, 3),
        "trend_a_pct": round(trend_a, 2),
        "trend_b_pct": round(trend_b, 2),
        "divergence": divergence,
        "data_points": min_len,
    }


# ═══════════════════════════════════════════════════════════
#  FULL CORRELATION SCAN
# ═══════════════════════════════════════════════════════════

def scan_all_correlations(include_crypto: bool = True, include_stocks: bool = True) -> Dict[str, Any]:
    """Scan all predefined pairs and return correlation matrix + alerts."""
    global _correlation_cache, _cache_timestamp
    
    now = time.time()
    if _correlation_cache and (now - _cache_timestamp) < _CACHE_TTL:
        return _correlation_cache
    
    results = {
        "pairs": {},
        "divergences": [],
        "regime": "UNKNOWN",
        "scan_time": datetime.now(IST).isoformat(),
    }
    
    pairs_to_check = []
    if include_stocks:
        pairs_to_check.extend(STOCK_PAIRS)
    if include_crypto:
        pairs_to_check.extend([
            (f"{a}-USD", f"{b}-USD") for a, b in CRYPTO_PAIRS
        ])
    pairs_to_check.extend(CROSS_ASSET_PAIRS)
    
    for sym_a, sym_b in pairs_to_check:
        try:
            prices_a = _fetch_price_history(sym_a, 30)
            prices_b = _fetch_price_history(sym_b, 30)
            
            if prices_a and prices_b:
                corr = compute_correlation(prices_a, prices_b)
                pair_key = f"{sym_a} vs {sym_b}"
                results["pairs"][pair_key] = corr
                
                if corr.get("divergence"):
                    results["divergences"].append({
                        "pair": pair_key,
                        "correlation": corr["correlation"],
                        "recent": corr["recent_correlation"],
                        "trend_a": corr["trend_a_pct"],
                        "trend_b": corr["trend_b_pct"],
                    })
        except Exception as e:
            logger.debug(f"Correlation scan error for {sym_a}/{sym_b}: {e}")
    
    # Determine market regime from correlations
    results["regime"] = _detect_regime(results["pairs"])
    
    _correlation_cache = results
    _cache_timestamp = now
    
    return results


def _detect_regime(pairs: Dict[str, Dict]) -> str:
    """Detect market regime from correlation patterns.
    
    Returns: "RISK_ON", "RISK_OFF", "ROTATION", "NORMAL"
    """
    if not pairs:
        return "UNKNOWN"
    
    # Risk-on: stocks + crypto both up, gold down
    # Risk-off: stocks + crypto down, gold up
    # Rotation: some sectors up, others down
    
    nifty_trend = None
    btc_trend = None
    gold_trend = None
    
    for pair_key, data in pairs.items():
        if "NSEI" in pair_key and "GSPC" in pair_key:
            nifty_trend = data.get("trend_a_pct", 0)
        if "BTC" in pair_key and "NSEI" in pair_key:
            btc_trend = data.get("trend_a_pct", 0)
        if "GC=F" in pair_key and "DX" in pair_key:
            gold_trend = data.get("trend_a_pct", 0)
    
    if nifty_trend is not None and btc_trend is not None:
        if nifty_trend > 2 and btc_trend > 2:
            return "RISK_ON"
        elif nifty_trend < -2 and btc_trend < -2:
            return "RISK_OFF"
    
    if gold_trend is not None and nifty_trend is not None:
        if gold_trend > 3 and nifty_trend < -2:
            return "RISK_OFF"
    
    # Count divergences
    divergences = sum(1 for d in pairs.values() if d.get("divergence"))
    if divergences >= 2:
        return "ROTATION"
    
    return "NORMAL"


# ═══════════════════════════════════════════════════════════
#  CORRELATION INSIGHTS (for Telegram)
# ═══════════════════════════════════════════════════════════

def get_correlation_insight(symbol: str) -> str:
    """Get correlation-based insight for a specific symbol.
    
    E.g., for "BTC" → "BTC is diverging from ETH — unusual, could mean reversal"
    """
    sym_upper = symbol.upper()
    
    try:
        results = scan_all_correlations()
    except Exception:
        return ""
    
    insights = []
    
    for pair_key, data in results.get("pairs", {}).items():
        if sym_upper in pair_key.upper():
            corr = data.get("correlation", 0)
            recent = data.get("recent_correlation", 0)
            div = data.get("divergence", False)
            
            other = pair_key.replace(sym_upper, "").replace(" vs ", "").replace("-USD", "").strip()
            
            if div:
                insights.append(
                    f"⚠️ {sym_upper} diverging from {other} "
                    f"(normal corr: {corr:.2f}, recent: {recent:.2f})"
                )
            elif abs(corr) > 0.7:
                direction = "positive" if corr > 0 else "inverse"
                insights.append(
                    f"🔗 {sym_upper} has strong {direction} correlation with {other} ({corr:.2f})"
                )
    
    regime = results.get("regime", "UNKNOWN")
    if regime != "UNKNOWN" and regime != "NORMAL":
        insights.append(f"🌎 Market regime: {regime}")
    
    return "\n".join(insights) if insights else ""


def format_correlation_report() -> str:
    """Beautiful Telegram report of all correlations."""
    try:
        results = scan_all_correlations()
    except Exception:
        return "Correlation scan failed. yfinance data unavailable."
    
    report = (
        "🔗 *CROSS-ASSET CORRELATION REPORT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    regime = results.get("regime", "UNKNOWN")
    regime_emoji = {
        "RISK_ON": "🟢 RISK ON (bullish)",
        "RISK_OFF": "🔴 RISK OFF (defensive)",
        "ROTATION": "🔄 SECTOR ROTATION",
        "NORMAL": "⚪ NORMAL",
    }
    report += f"🌎 *Regime:* {regime_emoji.get(regime, regime)}\n\n"
    
    # Divergences (most important)
    divs = results.get("divergences", [])
    if divs:
        report += "⚠️ *DIVERGENCE ALERTS:*\n"
        for d in divs:
            report += (
                f"  🔀 {d['pair']}\n"
                f"     Historical: {d['correlation']:.2f} → Recent: {d['recent']:.2f}\n"
                f"     Trends: {d['trend_a']:+.1f}% vs {d['trend_b']:+.1f}%\n"
            )
        report += "\n"
    
    # All pairs
    report += "📊 *Correlations:*\n"
    for pair_key, data in results.get("pairs", {}).items():
        if "error" in data:
            continue
        corr = data.get("correlation", 0)
        emoji = "🟢" if corr > 0.5 else "🔴" if corr < -0.5 else "⚪"
        bar = "█" * int(abs(corr * 10))
        report += f"  {emoji} {pair_key}: {'−' if corr < 0 else '+'}{bar} {corr:.2f}\n"
    
    report += f"\n_Scan time: {results.get('scan_time', 'N/A')}_"
    
    return report


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'compute_correlation',
    'scan_all_correlations',
    'get_correlation_insight',
    'format_correlation_report',
]
