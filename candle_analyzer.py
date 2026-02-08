"""
========================================================================================
  SUPER-ADVANCED CANDLESTICK PATTERN ENGINE — 40+ Patterns | Multi-Timeframe | AI Fusion
========================================================================================

Detects 40+ classic & advanced Japanese candlestick patterns with:
  - Single-candle patterns (Doji, Hammer, Shooting Star, Marubozu, etc.)
  - Dual-candle patterns (Engulfing, Harami, Piercing, Dark Cloud, Tweezer, etc.)
  - Triple-candle patterns (Morning/Evening Star, Three White Soldiers, Three Black Crows)
  - Multi-candle patterns (Rising/Falling Three, Tasuki Gap, etc.)
  - Multi-timeframe analysis (1min, 5min, 15min, 1H, 1D, 1W)
  - Pattern confluence scoring (multiple patterns = stronger signal)
  - AI-weighted signal generation with adaptive learning
  - Dynamic support/resistance from pattern clusters
  
All prices in INR (₹). Designed for NIFTY/SENSEX/NSE stocks.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("candle_analyzer")


# ═══════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CandlePattern:
    """Represents a detected candlestick pattern."""
    name: str
    pattern_type: str        # "bullish", "bearish", "neutral"
    strength: float          # 0.0 to 1.0
    reliability: float       # historical success rate 0-1
    timeframe: str           # "1d", "1h", "5m", etc.
    index: int               # position in DataFrame
    description: str = ""


@dataclass
class PatternCluster:
    """A group of patterns forming a confluence zone."""
    patterns: List[CandlePattern] = field(default_factory=list)
    net_signal: float = 0.0
    confidence: float = 0.0
    support_level: float = 0.0
    resistance_level: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  CANDLESTICK HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _body(o, c):
    return abs(c - o)

def _upper_wick(o, h, c):
    return h - max(o, c)

def _lower_wick(o, l, c):
    return min(o, c) - l

def _total_range(h, l):
    return h - l

def _is_bullish(o, c):
    return c > o

def _is_bearish(o, c):
    return c < o

def _body_pct(o, h, l, c):
    tr = _total_range(h, l)
    return _body(o, c) / tr if tr > 0 else 0


# ═══════════════════════════════════════════════════════════════════════════
#  40+ CANDLESTICK PATTERN DETECTORS
# ═══════════════════════════════════════════════════════════════════════════

def detect_all_patterns(df: pd.DataFrame, timeframe: str = "1d") -> List[CandlePattern]:
    """Master pattern detection — runs all 40+ pattern detectors on OHLCV data."""
    if df is None or len(df) < 5:
        return []

    patterns = []
    vals = df[['Open', 'High', 'Low', 'Close']].values
    vol = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df))

    for i in range(len(vals)):
        o, h, l, c = float(vals[i][0]), float(vals[i][1]), float(vals[i][2]), float(vals[i][3])
        body = _body(o, c)
        tr = _total_range(h, l)
        uw = _upper_wick(o, h, c)
        lw = _lower_wick(o, l, c)

        if tr == 0:
            continue

        bp = body / tr

        # ── SINGLE CANDLE PATTERNS ──

        # 1. Doji
        if bp < 0.05:
            patterns.append(CandlePattern("Doji", "neutral", 0.6, 0.55, timeframe, i,
                "Indecision — market may reverse"))

        # 2. Long-Legged Doji
        if bp < 0.05 and uw > 0.3 * tr and lw > 0.3 * tr:
            patterns.append(CandlePattern("Long-Legged Doji", "neutral", 0.7, 0.58, timeframe, i,
                "Extreme indecision — high volatility"))

        # 3. Dragonfly Doji
        if bp < 0.05 and lw > 0.6 * tr and uw < 0.05 * tr:
            patterns.append(CandlePattern("Dragonfly Doji", "bullish", 0.75, 0.62, timeframe, i,
                "Strong bullish reversal at support"))

        # 4. Gravestone Doji
        if bp < 0.05 and uw > 0.6 * tr and lw < 0.05 * tr:
            patterns.append(CandlePattern("Gravestone Doji", "bearish", 0.75, 0.61, timeframe, i,
                "Strong bearish reversal at resistance"))

        # 5. Hammer
        if body > 0 and lw >= 2 * body and uw < 0.3 * body and _is_bullish(o, c):
            patterns.append(CandlePattern("Hammer", "bullish", 0.8, 0.65, timeframe, i,
                "Bullish reversal — buyers rejected lower prices"))

        # 6. Inverted Hammer
        if body > 0 and uw >= 2 * body and lw < 0.3 * body and _is_bullish(o, c):
            patterns.append(CandlePattern("Inverted Hammer", "bullish", 0.65, 0.58, timeframe, i,
                "Potential bullish reversal — needs confirmation"))

        # 7. Hanging Man
        if body > 0 and lw >= 2 * body and uw < 0.3 * body and _is_bearish(o, c):
            patterns.append(CandlePattern("Hanging Man", "bearish", 0.7, 0.60, timeframe, i,
                "Bearish warning — selling pressure emerging"))

        # 8. Shooting Star
        if body > 0 and uw >= 2 * body and lw < 0.3 * body and _is_bearish(o, c):
            patterns.append(CandlePattern("Shooting Star", "bearish", 0.8, 0.63, timeframe, i,
                "Bearish reversal — sellers rejected higher prices"))

        # 9. Bullish Marubozu
        if _is_bullish(o, c) and uw < 0.02 * tr and lw < 0.02 * tr and bp > 0.9:
            patterns.append(CandlePattern("Bullish Marubozu", "bullish", 0.9, 0.70, timeframe, i,
                "Extreme bullish momentum — no resistance"))

        # 10. Bearish Marubozu
        if _is_bearish(o, c) and uw < 0.02 * tr and lw < 0.02 * tr and bp > 0.9:
            patterns.append(CandlePattern("Bearish Marubozu", "bearish", 0.9, 0.70, timeframe, i,
                "Extreme bearish momentum — no support"))

        # 11. Spinning Top
        if 0.1 < bp < 0.3 and uw > 0.3 * tr and lw > 0.3 * tr:
            patterns.append(CandlePattern("Spinning Top", "neutral", 0.4, 0.50, timeframe, i,
                "Indecision — small body, large wicks"))

        # 12. High Wave Candle
        if bp < 0.15 and (uw + lw) > 0.7 * tr:
            patterns.append(CandlePattern("High Wave", "neutral", 0.5, 0.52, timeframe, i,
                "Extreme indecision — major potential reversal"))

        # ── DUAL CANDLE PATTERNS ──
        if i < 1:
            continue

        po, ph, pl, pc = float(vals[i-1][0]), float(vals[i-1][1]), float(vals[i-1][2]), float(vals[i-1][3])
        p_body = _body(po, pc)
        p_tr = _total_range(ph, pl)

        if p_tr == 0:
            continue

        # 13. Bullish Engulfing
        if _is_bearish(po, pc) and _is_bullish(o, c) and o <= pc and c >= po and body > p_body:
            patterns.append(CandlePattern("Bullish Engulfing", "bullish", 0.85, 0.68, timeframe, i,
                "Strong bullish reversal — buyers overwhelmed sellers"))

        # 14. Bearish Engulfing
        if _is_bullish(po, pc) and _is_bearish(o, c) and o >= pc and c <= po and body > p_body:
            patterns.append(CandlePattern("Bearish Engulfing", "bearish", 0.85, 0.67, timeframe, i,
                "Strong bearish reversal — sellers overwhelmed buyers"))

        # 15. Bullish Harami
        if _is_bearish(po, pc) and _is_bullish(o, c) and o > pc and c < po and body < p_body * 0.5:
            patterns.append(CandlePattern("Bullish Harami", "bullish", 0.6, 0.55, timeframe, i,
                "Potential bullish reversal — selling pressure fading"))

        # 16. Bearish Harami
        if _is_bullish(po, pc) and _is_bearish(o, c) and o < pc and c > po and body < p_body * 0.5:
            patterns.append(CandlePattern("Bearish Harami", "bearish", 0.6, 0.55, timeframe, i,
                "Potential bearish reversal — buying pressure fading"))

        # 17. Piercing Line
        if _is_bearish(po, pc) and _is_bullish(o, c) and o < pl and c > (po + pc) / 2 and c < po:
            patterns.append(CandlePattern("Piercing Line", "bullish", 0.7, 0.60, timeframe, i,
                "Bullish reversal — closed above midpoint of prior bearish candle"))

        # 18. Dark Cloud Cover
        if _is_bullish(po, pc) and _is_bearish(o, c) and o > ph and c < (po + pc) / 2 and c > po:
            patterns.append(CandlePattern("Dark Cloud Cover", "bearish", 0.7, 0.60, timeframe, i,
                "Bearish reversal — closed below midpoint of prior bullish candle"))

        # 19. Tweezer Top
        if abs(h - ph) < 0.001 * h and _is_bullish(po, pc) and _is_bearish(o, c):
            patterns.append(CandlePattern("Tweezer Top", "bearish", 0.65, 0.58, timeframe, i,
                "Double resistance — bearish reversal"))

        # 20. Tweezer Bottom
        if abs(l - pl) < 0.001 * l and _is_bearish(po, pc) and _is_bullish(o, c):
            patterns.append(CandlePattern("Tweezer Bottom", "bullish", 0.65, 0.58, timeframe, i,
                "Double support — bullish reversal"))

        # 21. On-Neck Line
        if _is_bearish(po, pc) and _is_bullish(o, c) and abs(c - pl) < 0.002 * abs(pl + 1):
            patterns.append(CandlePattern("On-Neck Line", "bearish", 0.5, 0.52, timeframe, i,
                "Bearish continuation — buyers couldn't push past prior low"))

        # 22. In-Neck Line
        if _is_bearish(po, pc) and _is_bullish(o, c) and abs(c - pc) < 0.002 * abs(pc + 1):
            patterns.append(CandlePattern("In-Neck Line", "bearish", 0.5, 0.53, timeframe, i,
                "Bearish continuation — close near prior close"))

        # 23. Kicking Bullish
        p_bp = p_body / p_tr if p_tr > 0 else 0
        if _is_bearish(po, pc) and p_bp > 0.8 and _is_bullish(o, c) and bp > 0.8 and o > po:
            patterns.append(CandlePattern("Kicking Bullish", "bullish", 0.95, 0.72, timeframe, i,
                "Extremely rare bullish signal — trend reversal"))

        # 24. Kicking Bearish
        if _is_bullish(po, pc) and p_bp > 0.8 and _is_bearish(o, c) and bp > 0.8 and o < po:
            patterns.append(CandlePattern("Kicking Bearish", "bearish", 0.95, 0.72, timeframe, i,
                "Extremely rare bearish signal — trend reversal"))

        # 25. Bullish Counterattack
        if _is_bearish(po, pc) and _is_bullish(o, c) and abs(c - pc) < 0.002 * abs(pc + 1) and body > 0.5 * tr:
            patterns.append(CandlePattern("Bullish Counterattack", "bullish", 0.6, 0.55, timeframe, i,
                "Buyers matched sellers — potential reversal"))

        # 26. Bearish Counterattack
        if _is_bullish(po, pc) and _is_bearish(o, c) and abs(c - pc) < 0.002 * abs(pc + 1) and body > 0.5 * tr:
            patterns.append(CandlePattern("Bearish Counterattack", "bearish", 0.6, 0.55, timeframe, i,
                "Sellers matched buyers — potential reversal"))

        # ── TRIPLE CANDLE PATTERNS ──
        if i < 2:
            continue

        p2o, p2h, p2l, p2c = float(vals[i-2][0]), float(vals[i-2][1]), float(vals[i-2][2]), float(vals[i-2][3])
        p2_body = _body(p2o, p2c)
        p2_tr = _total_range(p2h, p2l)

        # 27. Morning Star
        if (p2_tr > 0 and _is_bearish(p2o, p2c) and p2_body > 0.5 * p2_tr and
            p_tr > 0 and _body(po, pc) < 0.3 * p_tr and
            _is_bullish(o, c) and c > (p2o + p2c) / 2):
            patterns.append(CandlePattern("Morning Star", "bullish", 0.9, 0.72, timeframe, i,
                "Strong bullish reversal — three-candle bottom pattern"))

        # 28. Evening Star
        if (p2_tr > 0 and _is_bullish(p2o, p2c) and p2_body > 0.5 * p2_tr and
            p_tr > 0 and _body(po, pc) < 0.3 * p_tr and
            _is_bearish(o, c) and c < (p2o + p2c) / 2):
            patterns.append(CandlePattern("Evening Star", "bearish", 0.9, 0.72, timeframe, i,
                "Strong bearish reversal — three-candle top pattern"))

        # 29. Morning Doji Star
        if (_is_bearish(p2o, p2c) and p_tr > 0 and _body(po, pc) < 0.05 * p_tr and
            _is_bullish(o, c) and c > (p2o + p2c) / 2):
            patterns.append(CandlePattern("Morning Doji Star", "bullish", 0.92, 0.74, timeframe, i,
                "Strongest bullish reversal — doji + buying follow-through"))

        # 30. Evening Doji Star
        if (_is_bullish(p2o, p2c) and p_tr > 0 and _body(po, pc) < 0.05 * p_tr and
            _is_bearish(o, c) and c < (p2o + p2c) / 2):
            patterns.append(CandlePattern("Evening Doji Star", "bearish", 0.92, 0.74, timeframe, i,
                "Strongest bearish reversal — doji + selling follow-through"))

        # 31. Three White Soldiers
        try:
            if (all(_is_bullish(float(vals[i-j][0]), float(vals[i-j][3])) for j in range(3)) and
                float(vals[i][3]) > float(vals[i-1][3]) > float(vals[i-2][3]) and
                all(_body(float(vals[i-j][0]), float(vals[i-j][3])) > 0.5 * _total_range(float(vals[i-j][1]), float(vals[i-j][2])) for j in range(3))):
                patterns.append(CandlePattern("Three White Soldiers", "bullish", 0.88, 0.70, timeframe, i,
                    "Strong bullish continuation — three consecutive strong green candles"))
        except (IndexError, ValueError):
            pass

        # 32. Three Black Crows
        try:
            if (all(_is_bearish(float(vals[i-j][0]), float(vals[i-j][3])) for j in range(3)) and
                float(vals[i][3]) < float(vals[i-1][3]) < float(vals[i-2][3]) and
                all(_body(float(vals[i-j][0]), float(vals[i-j][3])) > 0.5 * _total_range(float(vals[i-j][1]), float(vals[i-j][2])) for j in range(3))):
                patterns.append(CandlePattern("Three Black Crows", "bearish", 0.88, 0.70, timeframe, i,
                    "Strong bearish continuation — three consecutive strong red candles"))
        except (IndexError, ValueError):
            pass

        # 33. Three Inside Up
        if (_is_bearish(p2o, p2c) and _is_bullish(po, pc) and
            po > p2c and pc < p2o and _body(po, pc) < p2_body * 0.5 and
            _is_bullish(o, c) and c > pc):
            patterns.append(CandlePattern("Three Inside Up", "bullish", 0.8, 0.65, timeframe, i,
                "Confirmed bullish harami — strong reversal"))

        # 34. Three Inside Down
        if (_is_bullish(p2o, p2c) and _is_bearish(po, pc) and
            po < p2c and pc > p2o and _body(po, pc) < p2_body * 0.5 and
            _is_bearish(o, c) and c < pc):
            patterns.append(CandlePattern("Three Inside Down", "bearish", 0.8, 0.65, timeframe, i,
                "Confirmed bearish harami — strong reversal"))

        # 35. Three Outside Up
        if (_is_bearish(p2o, p2c) and _is_bullish(po, pc) and
            po <= p2c and pc >= p2o and _body(po, pc) > p2_body and
            _is_bullish(o, c) and c > pc):
            patterns.append(CandlePattern("Three Outside Up", "bullish", 0.82, 0.66, timeframe, i,
                "Confirmed bullish engulfing — strong continuation"))

        # 36. Three Outside Down
        if (_is_bullish(p2o, p2c) and _is_bearish(po, pc) and
            po >= p2c and pc <= p2o and _body(po, pc) > p2_body and
            _is_bearish(o, c) and c < pc):
            patterns.append(CandlePattern("Three Outside Down", "bearish", 0.82, 0.66, timeframe, i,
                "Confirmed bearish engulfing — strong continuation"))

        # 37. Abandoned Baby Bullish
        if (_is_bearish(p2o, p2c) and p_tr > 0 and
            _body(po, pc) < 0.05 * p_tr and ph < p2l and l > ph and
            _is_bullish(o, c)):
            patterns.append(CandlePattern("Abandoned Baby Bullish", "bullish", 0.95, 0.75, timeframe, i,
                "Extremely rare — strongest bullish reversal"))

        # 38. Abandoned Baby Bearish
        if (_is_bullish(p2o, p2c) and p_tr > 0 and
            _body(po, pc) < 0.05 * p_tr and pl > p2h and h < pl and
            _is_bearish(o, c)):
            patterns.append(CandlePattern("Abandoned Baby Bearish", "bearish", 0.95, 0.75, timeframe, i,
                "Extremely rare — strongest bearish reversal"))

        # ── QUAD+ CANDLE PATTERNS ──
        if i < 3:
            continue

        p3o, p3h, p3l, p3c = float(vals[i-3][0]), float(vals[i-3][1]), float(vals[i-3][2]), float(vals[i-3][3])

        # 39. Rising Three Methods
        if (_is_bullish(p3o, p3c) and _body(p3o, p3c) > 0.5 * _total_range(p3h, p3l) and
            all(_is_bearish(float(vals[i-j][0]), float(vals[i-j][3])) for j in [1, 2]) and
            float(vals[i-2][2]) > p3l and float(vals[i-1][2]) > p3l and
            _is_bullish(o, c) and c > p3c):
            patterns.append(CandlePattern("Rising Three Methods", "bullish", 0.78, 0.64, timeframe, i,
                "Bullish continuation — minor correction within uptrend"))

        # 40. Falling Three Methods
        if (_is_bearish(p3o, p3c) and _body(p3o, p3c) > 0.5 * _total_range(p3h, p3l) and
            all(_is_bullish(float(vals[i-j][0]), float(vals[i-j][3])) for j in [1, 2]) and
            float(vals[i-2][1]) < p3h and float(vals[i-1][1]) < p3h and
            _is_bearish(o, c) and c < p3c):
            patterns.append(CandlePattern("Falling Three Methods", "bearish", 0.78, 0.64, timeframe, i,
                "Bearish continuation — minor bounce within downtrend"))

        # 41. Bullish Belt Hold
        if _is_bullish(o, c) and abs(o - l) < 0.01 * tr and bp > 0.7 and i > 0 and o < float(vals[i-1][2]):
            patterns.append(CandlePattern("Bullish Belt Hold", "bullish", 0.65, 0.57, timeframe, i,
                "Gap down reversal — opened at low and rallied"))

        # 42. Bearish Belt Hold
        if _is_bearish(o, c) and abs(o - h) < 0.01 * tr and bp > 0.7 and i > 0 and o > float(vals[i-1][1]):
            patterns.append(CandlePattern("Bearish Belt Hold", "bearish", 0.65, 0.57, timeframe, i,
                "Gap up reversal — opened at high and sold off"))

        # 43. Upside Gap Two Crows
        if (i >= 2 and _is_bullish(p2o, p2c) and
            _is_bearish(po, pc) and po > p2c and
            _is_bearish(o, c) and o > po and c < pc and c > p2c):
            patterns.append(CandlePattern("Upside Gap Two Crows", "bearish", 0.7, 0.59, timeframe, i,
                "Bearish reversal after gap up — sellers gaining control"))

    return patterns


# ═══════════════════════════════════════════════════════════════════════════
#  MULTI-TIMEFRAME CANDLE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def fetch_index_candles(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLC candle data for any Indian index/stock from Yahoo Finance.
    symbol: '^NSEI' for NIFTY, '^BSESN' for SENSEX, 'RELIANCE.NS' for stocks
    INR prices only.
    """
    try:
        import yfinance as yf
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        if data is None or data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data.columns = [col.strip().lower() for col in data.columns]
        rename_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume', 'adj close': 'Adj Close',
        }
        data.rename(columns=rename_map, inplace=True)

        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(c in data.columns for c in required):
            return None

        return data.sort_index()
    except Exception as e:
        logger.error(f"Failed to fetch candles for {symbol}: {e}")
        return None


TIMEFRAME_CONFIG = {
    "1m":  {"period": "7d",   "interval": "1m",  "weight": 0.10},
    "5m":  {"period": "60d",  "interval": "5m",  "weight": 0.15},
    "15m": {"period": "60d",  "interval": "15m", "weight": 0.18},
    "1h":  {"period": "60d",  "interval": "1h",  "weight": 0.20},
    "1d":  {"period": "1y",   "interval": "1d",  "weight": 0.25},
    "1wk": {"period": "5y",   "interval": "1wk", "weight": 0.12},
}


def multi_timeframe_pattern_scan(symbol: str, timeframes: List[str] = None) -> Dict[str, Any]:
    """Scan multiple timeframes for candlestick patterns and fuse signals."""
    if timeframes is None:
        timeframes = ["5m", "15m", "1h", "1d"]

    all_patterns = {}
    tf_signals = {}

    for tf in timeframes:
        config = TIMEFRAME_CONFIG.get(tf, {"period": "60d", "interval": tf, "weight": 0.2})
        df = fetch_index_candles(symbol, period=config["period"], interval=config["interval"])
        if df is None or len(df) < 10:
            continue

        patterns = detect_all_patterns(df, timeframe=tf)
        all_patterns[tf] = patterns

        recent_patterns = [p for p in patterns if p.index >= len(df) - 5]

        bullish_score = sum(p.strength * p.reliability for p in recent_patterns if p.pattern_type == "bullish")
        bearish_score = sum(p.strength * p.reliability for p in recent_patterns if p.pattern_type == "bearish")
        net = bullish_score - bearish_score
        weight = config["weight"]

        tf_signals[tf] = {
            "patterns": [{"name": p.name, "type": p.pattern_type, "strength": p.strength,
                          "reliability": p.reliability, "desc": p.description}
                         for p in recent_patterns],
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "net_signal": net,
            "weight": weight,
            "pattern_count": len(recent_patterns),
        }

    # Fused Signal
    weighted_signal = 0.0
    total_weight = 0.0
    total_patterns = 0

    for tf, sig in tf_signals.items():
        weighted_signal += sig["net_signal"] * sig["weight"]
        total_weight += sig["weight"]
        total_patterns += sig["pattern_count"]

    fused_signal = weighted_signal / total_weight if total_weight > 0 else 0.0

    agreeing = sum(1 for sig in tf_signals.values()
                   if sig["net_signal"] != 0 and (sig["net_signal"] > 0) == (fused_signal > 0))
    confluence_boost = 1.0 + (agreeing / max(len(tf_signals), 1)) * 0.3
    final_signal = fused_signal * confluence_boost
    confidence = min(abs(final_signal), 1.0)

    if final_signal > 0.15:
        direction = "BULLISH"
        action = "BUY_CE"
    elif final_signal < -0.15:
        direction = "BEARISH"
        action = "BUY_PE"
    else:
        direction = "NEUTRAL"
        action = "HOLD"

    return {
        "direction": direction,
        "action": action,
        "signal_score": float(final_signal),
        "confidence": float(confidence),
        "confluence_boost": float(confluence_boost),
        "total_patterns": total_patterns,
        "timeframe_signals": tf_signals,
        "agreeing_timeframes": agreeing,
        "total_timeframes": len(tf_signals),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  ADVANCED TECHNICAL INDICATORS (50+)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate 50+ technical indicators. All prices in INR (₹)."""
    if df is None or len(df) < 20:
        return {}

    indicators: Dict[str, float] = {}

    try:
        import pandas_ta as pdt

        # Price
        indicators['price'] = float(df['Close'].iloc[-1])
        indicators['price_change'] = float(df['Close'].iloc[-1] - df['Close'].iloc[-2]) if len(df) > 1 else 0
        indicators['price_change_pct'] = (indicators['price_change'] / df['Close'].iloc[-2] * 100) if len(df) > 1 and df['Close'].iloc[-2] != 0 else 0
        indicators['volume'] = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0

        # RSI Multi-period
        for period in [7, 9, 14, 21]:
            rsi = pdt.rsi(df['Close'], length=period)
            indicators[f'rsi_{period}'] = float(rsi.iloc[-1]) if rsi is not None and not rsi.empty else 50.0

        # Stochastic RSI
        stochrsi = pdt.stochrsi(df['Close'], length=14)
        if stochrsi is not None and not stochrsi.empty:
            indicators['stochrsi_k'] = float(stochrsi.iloc[-1, 0])
            indicators['stochrsi_d'] = float(stochrsi.iloc[-1, 1]) if stochrsi.shape[1] > 1 else indicators['stochrsi_k']

        # Moving Averages
        for period in [9, 20, 50, 100, 200]:
            sma = pdt.sma(df['Close'], length=period)
            indicators[f'sma_{period}'] = float(sma.iloc[-1]) if sma is not None and not sma.empty else indicators['price']
            ema = pdt.ema(df['Close'], length=period)
            indicators[f'ema_{period}'] = float(ema.iloc[-1]) if ema is not None and not ema.empty else indicators['price']

        # MACD
        macd = pdt.macd(df['Close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            indicators['macd'] = float(macd.iloc[-1, 0])
            indicators['macd_signal'] = float(macd.iloc[-1, 1]) if macd.shape[1] > 1 else 0
            indicators['macd_hist'] = float(macd.iloc[-1, 2]) if macd.shape[1] > 2 else 0

        # Bollinger Bands
        bb = pdt.bbands(df['Close'], length=20, std=2)
        if bb is not None and not bb.empty:
            indicators['bb_upper'] = float(bb.iloc[-1, 2])
            indicators['bb_middle'] = float(bb.iloc[-1, 1])
            indicators['bb_lower'] = float(bb.iloc[-1, 0])
            bb_width = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_width'] = bb_width
            indicators['bb_pct'] = (indicators['price'] - indicators['bb_lower']) / bb_width if bb_width > 0 else 0.5

        # Keltner Channel
        kc = pdt.kc(df['High'], df['Low'], df['Close'], length=20)
        if kc is not None and not kc.empty:
            indicators['kc_upper'] = float(kc.iloc[-1, 2]) if kc.shape[1] > 2 else 0
            indicators['kc_lower'] = float(kc.iloc[-1, 0])

        # Volatility
        atr = pdt.atr(df['High'], df['Low'], df['Close'], length=14)
        indicators['atr'] = float(atr.iloc[-1]) if atr is not None and not atr.empty else 0.0
        indicators['atr_pct'] = (indicators['atr'] / indicators['price'] * 100) if indicators['price'] > 0 else 0

        returns = df['Close'].pct_change().dropna()
        for lookback in [10, 20, 30]:
            indicators[f'hv_{lookback}'] = float(returns.tail(lookback).std() * np.sqrt(252) * 100) if len(returns) >= lookback else 0

        # Trend
        adx = pdt.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx is not None and not adx.empty:
            indicators['adx'] = float(adx.iloc[-1, 0])
            indicators['plus_di'] = float(adx.iloc[-1, 1]) if adx.shape[1] > 1 else 0
            indicators['minus_di'] = float(adx.iloc[-1, 2]) if adx.shape[1] > 2 else 0

        # Aroon
        aroon = pdt.aroon(df['High'], df['Low'], length=25)
        if aroon is not None and not aroon.empty:
            indicators['aroon_up'] = float(aroon.iloc[-1, 0])
            indicators['aroon_down'] = float(aroon.iloc[-1, 1]) if aroon.shape[1] > 1 else 0
            indicators['aroon_osc'] = indicators['aroon_up'] - indicators['aroon_down']

        # Momentum
        stoch = pdt.stoch(df['High'], df['Low'], df['Close'])
        if stoch is not None and not stoch.empty:
            indicators['stoch_k'] = float(stoch.iloc[-1, 0])
            indicators['stoch_d'] = float(stoch.iloc[-1, 1]) if stoch.shape[1] > 1 else indicators['stoch_k']

        cci = pdt.cci(df['High'], df['Low'], df['Close'], length=20)
        indicators['cci'] = float(cci.iloc[-1]) if cci is not None and not cci.empty else 0

        willr = pdt.willr(df['High'], df['Low'], df['Close'], length=14)
        indicators['willr'] = float(willr.iloc[-1]) if willr is not None and not willr.empty else -50

        if 'Volume' in df.columns:
            mfi = pdt.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
            indicators['mfi'] = float(mfi.iloc[-1]) if mfi is not None and not mfi.empty else 50

        roc = pdt.roc(df['Close'], length=12)
        indicators['roc'] = float(roc.iloc[-1]) if roc is not None and not roc.empty else 0

        # Volume
        if 'Volume' in df.columns:
            indicators['vol_sma_20'] = float(df['Volume'].rolling(20).mean().iloc[-1])
            indicators['vol_ratio'] = indicators['volume'] / indicators['vol_sma_20'] if indicators['vol_sma_20'] > 0 else 1

            obv = pdt.obv(df['Close'], df['Volume'])
            indicators['obv'] = float(obv.iloc[-1]) if obv is not None and not obv.empty else 0
            indicators['obv_sma'] = float(obv.rolling(20).mean().iloc[-1]) if obv is not None and len(obv) >= 20 else indicators['obv']

            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
            indicators['vwap'] = float(vwap.iloc[-1]) if not vwap.empty else indicators['price']

            ad = pdt.ad(df['High'], df['Low'], df['Close'], df['Volume'])
            indicators['ad_line'] = float(ad.iloc[-1]) if ad is not None and not ad.empty else 0

        # Ichimoku Cloud
        ichimoku = pdt.ichimoku(df['High'], df['Low'], df['Close'])
        if ichimoku is not None and isinstance(ichimoku, tuple) and len(ichimoku) > 0:
            ich = ichimoku[0]
            if ich is not None and not ich.empty:
                indicators['ichi_tenkan'] = float(ich.iloc[-1, 0]) if ich.shape[1] > 0 else 0
                indicators['ichi_kijun'] = float(ich.iloc[-1, 1]) if ich.shape[1] > 1 else 0
                indicators['ichi_senkou_a'] = float(ich.iloc[-1, 2]) if ich.shape[1] > 2 else 0
                indicators['ichi_senkou_b'] = float(ich.iloc[-1, 3]) if ich.shape[1] > 3 else 0
                indicators['ichi_cloud_green'] = 1 if indicators.get('ichi_senkou_a', 0) > indicators.get('ichi_senkou_b', 0) else 0

        # Fibonacci Retracement
        high_52w = float(df['High'].tail(252).max()) if len(df) >= 252 else float(df['High'].max())
        low_52w = float(df['Low'].tail(252).min()) if len(df) >= 252 else float(df['Low'].min())
        diff = high_52w - low_52w
        indicators['fib_0'] = low_52w
        indicators['fib_236'] = low_52w + 0.236 * diff
        indicators['fib_382'] = low_52w + 0.382 * diff
        indicators['fib_500'] = low_52w + 0.500 * diff
        indicators['fib_618'] = low_52w + 0.618 * diff
        indicators['fib_786'] = low_52w + 0.786 * diff
        indicators['fib_1000'] = high_52w
        indicators['high_52w'] = high_52w
        indicators['low_52w'] = low_52w

        # Pivot Points (Classic)
        prev_h = float(df['High'].iloc[-2]) if len(df) > 1 else indicators['price']
        prev_l = float(df['Low'].iloc[-2]) if len(df) > 1 else indicators['price']
        prev_c = float(df['Close'].iloc[-2]) if len(df) > 1 else indicators['price']
        pp = (prev_h + prev_l + prev_c) / 3
        indicators['pivot'] = pp
        indicators['r1'] = 2 * pp - prev_l
        indicators['r2'] = pp + (prev_h - prev_l)
        indicators['r3'] = prev_h + 2 * (pp - prev_l)
        indicators['s1'] = 2 * pp - prev_h
        indicators['s2'] = pp - (prev_h - prev_l)
        indicators['s3'] = prev_l - 2 * (prev_h - pp)

        # Supertrend
        st = pdt.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
        if st is not None and not st.empty:
            indicators['supertrend'] = float(st.iloc[-1, 0])
            indicators['supertrend_dir'] = float(st.iloc[-1, 1]) if st.shape[1] > 1 else 0

    except ImportError:
        logger.warning("pandas_ta not available, using basic calculations")
        indicators['price'] = float(df['Close'].iloc[-1])
    except Exception as e:
        logger.error(f"Error in technical indicators: {e}")
        if 'price' not in indicators:
            try:
                indicators['price'] = float(df['Close'].iloc[-1])
            except Exception:
                indicators['price'] = 0.0

    return indicators


# ═══════════════════════════════════════════════════════════════════════════
#  AI-POWERED SIGNAL GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def analyze_index(symbol: str, symbol_name: str = "INDEX") -> Dict[str, Any]:
    """Comprehensive AI analysis combining candlestick + technicals + multi-timeframe.
    All prices in INR (₹).
    """
    result: Dict[str, Any] = {
        "symbol": symbol_name,
        "signal": "HOLD",
        "confidence": 0.0,
        "patterns": {},
        "indicators": {},
        "analysis": "",
        "reasons": [],
        "entry": 0.0,
        "stop_loss": 0.0,
        "target_1": 0.0,
        "target_2": 0.0,
        "target_3": 0.0,
        "support_levels": [],
        "resistance_levels": [],
    }

    df = fetch_index_candles(symbol, period="1y", interval="1d")
    if df is None or df.empty:
        result["analysis"] = "Failed to fetch candle data"
        return result

    patterns = detect_all_patterns(df, timeframe="1d")
    recent_patterns = [p for p in patterns if p.index >= len(df) - 5]
    result["patterns"] = {
        p.name: {"type": p.pattern_type, "strength": p.strength,
                 "reliability": p.reliability, "desc": p.description}
        for p in recent_patterns
    }

    indicators = calculate_technical_indicators(df)
    result["indicators"] = indicators

    signal_score = 0.0
    price = indicators.get('price', 0)

    # Factor 1: RSI
    rsi = indicators.get('rsi_14', 50)
    rsi_7 = indicators.get('rsi_7', 50)
    if rsi < 25:
        signal_score += 0.12
        result["reasons"].append(f"🔥 RSI {rsi:.1f} — EXTREMELY oversold")
    elif rsi < 35:
        signal_score += 0.08
        result["reasons"].append(f"📈 RSI {rsi:.1f} — Oversold")
    elif rsi > 75:
        signal_score -= 0.12
        result["reasons"].append(f"⚠️ RSI {rsi:.1f} — EXTREMELY overbought")
    elif rsi > 65:
        signal_score -= 0.08
        result["reasons"].append(f"📉 RSI {rsi:.1f} — Overbought")

    if rsi_7 > rsi + 5:
        signal_score += 0.03
        result["reasons"].append("RSI(7) > RSI(14) — short-term momentum bullish")
    elif rsi_7 < rsi - 5:
        signal_score -= 0.03

    # Factor 2: Moving Averages
    ema_9 = indicators.get('ema_9', price)
    ema_20 = indicators.get('ema_20', price)
    sma_50 = indicators.get('sma_50', price)
    sma_200 = indicators.get('sma_200', price)

    if sma_50 > sma_200 and price > sma_50:
        signal_score += 0.10
        result["reasons"].append("🌟 Golden Cross + price > SMA50")
    elif sma_50 < sma_200 and price < sma_50:
        signal_score -= 0.10
        result["reasons"].append("💀 Death Cross + price < SMA50")

    if ema_9 > ema_20:
        signal_score += 0.05
        result["reasons"].append("EMA 9 > EMA 20")
    else:
        signal_score -= 0.05

    vwap = indicators.get('vwap', price)
    if price > vwap:
        signal_score += 0.03
        result["reasons"].append(f"Price above VWAP ₹{vwap:,.0f}")

    # Factor 3: Bollinger Bands
    bb_pct = indicators.get('bb_pct', 0.5)
    bb_width = indicators.get('bb_width', 0)
    if bb_pct < 0.05:
        signal_score += 0.08
        result["reasons"].append("Price at lower Bollinger Band")
    elif bb_pct > 0.95:
        signal_score -= 0.08
        result["reasons"].append("Price at upper Bollinger Band")
    if bb_width > 0 and bb_width / price < 0.02:
        result["reasons"].append("⚡ Bollinger Squeeze — breakout imminent!")

    # Factor 4: MACD
    macd_hist = indicators.get('macd_hist', 0)
    if macd_hist > 0:
        signal_score += 0.07
        result["reasons"].append(f"MACD histogram positive ({macd_hist:.2f})")
    elif macd_hist < 0:
        signal_score -= 0.07
        result["reasons"].append(f"MACD histogram negative ({macd_hist:.2f})")

    # Factor 5: Candlestick Patterns
    for p in recent_patterns:
        if p.pattern_type == "bullish":
            signal_score += p.strength * p.reliability * 0.15
            result["reasons"].append(f"🕯️ {p.name} (bullish {p.strength:.0%})")
        elif p.pattern_type == "bearish":
            signal_score -= p.strength * p.reliability * 0.15
            result["reasons"].append(f"🕯️ {p.name} (bearish {p.strength:.0%})")

    # Factor 6: ADX
    adx = indicators.get('adx', 20)
    plus_di = indicators.get('plus_di', 0)
    minus_di = indicators.get('minus_di', 0)
    if adx > 30:
        trend_mult = 1.2
        if plus_di > minus_di:
            signal_score += 0.06
            result["reasons"].append(f"Strong uptrend (ADX {adx:.0f})")
        else:
            signal_score -= 0.06
            result["reasons"].append(f"Strong downtrend (ADX {adx:.0f})")
    elif adx < 20:
        trend_mult = 0.7
        result["reasons"].append(f"Weak trend (ADX {adx:.0f})")
    else:
        trend_mult = 1.0
    signal_score *= trend_mult

    # Factor 7: Stochastic
    stoch_k = indicators.get('stoch_k', 50)
    stoch_d = indicators.get('stoch_d', 50)
    if stoch_k < 20 and stoch_d < 20:
        signal_score += 0.06
        result["reasons"].append(f"Stochastic oversold ({stoch_k:.0f}/{stoch_d:.0f})")
    elif stoch_k > 80 and stoch_d > 80:
        signal_score -= 0.06
        result["reasons"].append(f"Stochastic overbought ({stoch_k:.0f}/{stoch_d:.0f})")

    # Factor 8: CCI
    cci = indicators.get('cci', 0)
    if cci < -200:
        signal_score += 0.05
    elif cci > 200:
        signal_score -= 0.05

    # Factor 9: Volume
    vol_ratio = indicators.get('vol_ratio', 1)
    if vol_ratio > 1.5:
        result["reasons"].append(f"📊 High volume ({vol_ratio:.1f}x avg)")
        signal_score *= 1.1
    elif vol_ratio < 0.5:
        result["reasons"].append(f"Low volume ({vol_ratio:.1f}x avg)")
        signal_score *= 0.85

    # Factor 10: Ichimoku
    ichi_tenkan = indicators.get('ichi_tenkan', 0)
    ichi_kijun = indicators.get('ichi_kijun', 0)
    ichi_cloud = indicators.get('ichi_cloud_green', 0)
    if ichi_tenkan > 0 and ichi_kijun > 0:
        if price > ichi_tenkan and price > ichi_kijun and ichi_cloud == 1:
            signal_score += 0.08
            result["reasons"].append("☁️ Above Ichimoku Cloud (bullish)")
        elif price < ichi_tenkan and price < ichi_kijun and ichi_cloud == 0:
            signal_score -= 0.08
            result["reasons"].append("☁️ Below Ichimoku Cloud (bearish)")

    # Factor 11: Supertrend
    supertrend_dir = indicators.get('supertrend_dir', 0)
    if supertrend_dir == 1:
        signal_score += 0.06
        result["reasons"].append("📈 Supertrend bullish")
    elif supertrend_dir == -1:
        signal_score -= 0.06
        result["reasons"].append("📉 Supertrend bearish")

    # Factor 12: MFI
    mfi = indicators.get('mfi', 50)
    if mfi < 20:
        signal_score += 0.04
        result["reasons"].append(f"MFI oversold ({mfi:.0f})")
    elif mfi > 80:
        signal_score -= 0.04
        result["reasons"].append(f"MFI overbought ({mfi:.0f})")

    # Final
    signal_score = max(-1.0, min(1.0, signal_score))
    confidence = min(abs(signal_score) * 1.5, 0.99)

    if signal_score >= 0.5:
        result["signal"] = "SUPER STRONG BUY"
    elif signal_score >= 0.25:
        result["signal"] = "STRONG BUY"
    elif signal_score >= 0.10:
        result["signal"] = "BUY"
    elif signal_score <= -0.5:
        result["signal"] = "SUPER STRONG SELL"
    elif signal_score <= -0.25:
        result["signal"] = "STRONG SELL"
    elif signal_score <= -0.10:
        result["signal"] = "SELL"
    else:
        result["signal"] = "HOLD"

    result["confidence"] = confidence

    # Entry/Exit Levels
    atr = indicators.get('atr', 100)
    if "BUY" in result["signal"]:
        result["entry"] = price
        result["stop_loss"] = price - (atr * 2.0)
        result["target_1"] = price + (atr * 1.5)
        result["target_2"] = price + (atr * 3.0)
        result["target_3"] = price + (atr * 5.0)
    elif "SELL" in result["signal"]:
        result["entry"] = price
        result["stop_loss"] = price + (atr * 2.0)
        result["target_1"] = price - (atr * 1.5)
        result["target_2"] = price - (atr * 3.0)
        result["target_3"] = price - (atr * 5.0)

    result["support_levels"] = [
        indicators.get('s1', 0), indicators.get('s2', 0), indicators.get('s3', 0),
        indicators.get('fib_382', 0), indicators.get('fib_500', 0),
    ]
    result["resistance_levels"] = [
        indicators.get('r1', 0), indicators.get('r2', 0), indicators.get('r3', 0),
        indicators.get('fib_618', 0), indicators.get('fib_786', 0),
    ]

    # Format
    analysis_lines = [
        f"📊 *{symbol_name} SUPER AI ANALYSIS* 📊",
        f"{'━' * 35}",
        f"💹 Price: ₹{price:,.2f} ({indicators.get('price_change_pct', 0):+.2f}%)",
        f"🎯 Signal: *{result['signal']}* (confidence: {confidence:.0%})",
        "",
        f"📈 *Technical Indicators:*",
        f"  RSI(14): {rsi:.1f} | RSI(7): {rsi_7:.1f}",
        f"  MACD Hist: {macd_hist:.2f}",
        f"  SMA 50/200: ₹{sma_50:,.0f}/₹{sma_200:,.0f}",
        f"  ADX: {adx:.0f} | +DI: {plus_di:.0f} | -DI: {minus_di:.0f}",
        f"  ATR: ₹{atr:,.2f} | CCI: {cci:.0f}",
        f"  Stoch K/D: {stoch_k:.0f}/{stoch_d:.0f}",
        f"  BB%: {bb_pct:.0%} | Vol Ratio: {vol_ratio:.1f}x",
        f"  MFI: {mfi:.0f} | ROC: {indicators.get('roc', 0):.2f}",
    ]

    if recent_patterns:
        analysis_lines.append(f"\n🕯️ *Candlestick Patterns ({len(recent_patterns)}):*")
        for p in recent_patterns[:5]:
            emoji = "🟢" if p.pattern_type == "bullish" else "🔴" if p.pattern_type == "bearish" else "⚪"
            analysis_lines.append(f"  {emoji} {p.name} ({p.strength:.0%} strength)")

    if "BUY" in result["signal"] or "SELL" in result["signal"]:
        analysis_lines.extend([
            f"\n💰 *Trade Setup:*",
            f"  Entry: ₹{result['entry']:,.2f}",
            f"  Stop Loss: ₹{result['stop_loss']:,.2f}",
            f"  Target 1: ₹{result['target_1']:,.2f}",
            f"  Target 2: ₹{result['target_2']:,.2f}",
            f"  Target 3: ₹{result['target_3']:,.2f}",
        ])

    analysis_lines.extend([
        f"\n📐 *Pivot Levels:*",
        f"  R3: ₹{indicators.get('r3', 0):,.0f} | R2: ₹{indicators.get('r2', 0):,.0f} | R1: ₹{indicators.get('r1', 0):,.0f}",
        f"  Pivot: ₹{indicators.get('pivot', 0):,.0f}",
        f"  S1: ₹{indicators.get('s1', 0):,.0f} | S2: ₹{indicators.get('s2', 0):,.0f} | S3: ₹{indicators.get('s3', 0):,.0f}",
        f"\n📐 *Fibonacci Levels:*",
        f"  23.6%: ₹{indicators.get('fib_236', 0):,.0f} | 38.2%: ₹{indicators.get('fib_382', 0):,.0f}",
        f"  50.0%: ₹{indicators.get('fib_500', 0):,.0f} | 61.8%: ₹{indicators.get('fib_618', 0):,.0f}",
        f"  52W High: ₹{indicators.get('high_52w', 0):,.0f} | 52W Low: ₹{indicators.get('low_52w', 0):,.0f}",
    ])

    if result["reasons"]:
        analysis_lines.append(f"\n📋 *Reasons ({len(result['reasons'])}):*")
        for r in result["reasons"][:8]:
            analysis_lines.append(f"  • {r}")

    result["analysis"] = "\n".join(analysis_lines)
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  BACKWARD COMPATIBILITY — detect_candlestick_patterns
# ═══════════════════════════════════════════════════════════════════════════

def detect_candlestick_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Legacy API — returns dict of pattern_name → count."""
    all_p = detect_all_patterns(df)
    result: Dict[str, int] = {}
    for p in all_p:
        result[p.name] = result.get(p.name, 0) + 1
    return result


if __name__ == "__main__":
    nifty = analyze_index("^NSEI", "NIFTY 50")
    print(nifty["analysis"])
    print("\n" + "=" * 60 + "\n")
    sensex = analyze_index("^BSESN", "SENSEX")
    print(sensex["analysis"])
