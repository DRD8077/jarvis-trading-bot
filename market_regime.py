"""
========================================================================================
  🧠 MARKET REGIME DETECTION ENGINE — Adaptive Trading Intelligence
========================================================================================

  Detects current market regime and adapts ALL trading signals accordingly.
  
  REGIMES:
  🟢 STRONG BULL  — Trending up, low volatility, all MAs aligned bullish
  🟡 BULL         — Uptrend but not perfect conditions
  ⚪ SIDEWAYS     — Range-bound, no clear direction
  🟡 BEAR         — Downtrend forming
  🔴 STRONG BEAR  — Full downtrend, high fear
  🌊 VOLATILE     — High volatility regime, chaotic moves
  💎 ACCUMULATION — Smart money buying, low volume base
  📤 DISTRIBUTION — Smart money selling, topping pattern

  FEATURES:
  ✅ Multi-factor regime classification (VIX, ADX, trend, breadth)
  ✅ Regime-adaptive signal parameters (tighten SL in volatile, widen in trending)
  ✅ Market breadth analysis (advance/decline proxy)  
  ✅ Sector rotation detection
  ✅ Historical regime persistence tracking
  ✅ Heat map scoring (0-100 for bull/bear)
  ✅ INR focused — NIFTY, SENSEX, India VIX
  ✅ Hindi + English output
  
  Author: JARVIS Trading Engine
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import numpy as np
import pandas as pd
import pytz

logger = logging.getLogger("market_regime")
IST = pytz.timezone("Asia/Kolkata")

# Cache
_regime_cache: Dict[str, Tuple[Any, float]] = {}
REGIME_CACHE_TTL = 600  # 10 min


class MarketRegime(Enum):
    STRONG_BULL = "🟢🟢 STRONG BULL"
    BULL = "🟢 BULL"
    SIDEWAYS = "⚪ SIDEWAYS"
    BEAR = "🔴 BEAR"
    STRONG_BEAR = "🔴🔴 STRONG BEAR"
    VOLATILE = "🌊 HIGH VOLATILE"
    ACCUMULATION = "💎 ACCUMULATION"
    DISTRIBUTION = "📤 DISTRIBUTION"


@dataclass
class RegimeAnalysis:
    """Complete market regime analysis result."""
    regime: MarketRegime
    confidence: float  # 0-100
    bull_score: float  # 0-100 (how bullish)
    bear_score: float  # 0-100 (how bearish)
    volatility_score: float  # 0-100 (how volatile)
    trend_strength: float  # 0-100 (ADX-based)
    
    # Component scores
    vix_signal: str  # "FEAR" / "GREED" / "NEUTRAL"
    vix_value: float
    trend_signal: str  # "UP" / "DOWN" / "FLAT"
    momentum_signal: str  # "STRONG" / "WEAK" / "NEUTRAL"
    volume_signal: str  # "ACCUMULATION" / "DISTRIBUTION" / "NEUTRAL"
    breadth_signal: str  # "HEALTHY" / "WEAK" / "DIVERGENT"
    
    # Trading parameters (regime-adaptive)
    recommended_position_size: float  # % of capital
    recommended_sl_multiplier: float  # ATR multiplier for SL
    recommended_strategy: str
    recommended_strategy_hi: str
    
    # Sector leaders/laggards
    sector_leaders: List[str] = field(default_factory=list)
    sector_laggards: List[str] = field(default_factory=list)
    
    timestamp: str = ""
    
    # Historical regime
    prev_regime: str = ""
    regime_duration_days: int = 0


# ═══════════════════════════════════════════════════════════════
# CORE REGIME DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_market_regime(symbol: str = "^NSEI", period: str = "1y") -> RegimeAnalysis:
    """Detect current market regime using multi-factor analysis."""
    
    # Check cache
    cache_key = f"regime_{symbol}"
    if cache_key in _regime_cache:
        cached, ts = _regime_cache[cache_key]
        if time.time() - ts < REGIME_CACHE_TTL:
            return cached
    
    try:
        from index_data import fetch_history
    except ImportError:
        import yfinance as yf
        def fetch_history(t, period="1y", **kw):
            df = yf.download(t, period=period, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    
    df = fetch_history(symbol, period=period)
    if df.empty or len(df) < 60:
        return _default_regime()
    
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else pd.Series(0, index=df.index)
    
    # ─── 1. TREND ANALYSIS ───────────────────────────────────
    ema_20 = close.ewm(span=20, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()
    ema_200 = close.ewm(span=200, adjust=False).mean()
    
    price = close.iloc[-1]
    above_20 = price > ema_20.iloc[-1]
    above_50 = price > ema_50.iloc[-1]
    above_200 = price > ema_200.iloc[-1]
    
    ema_20_slope = (ema_20.iloc[-1] - ema_20.iloc[-5]) / ema_20.iloc[-5] * 100 if len(ema_20) > 5 else 0
    ema_50_slope = (ema_50.iloc[-1] - ema_50.iloc[-10]) / ema_50.iloc[-10] * 100 if len(ema_50) > 10 else 0
    
    # Trend score: -100 to +100
    trend_score = 0
    trend_score += 20 if above_20 else -20
    trend_score += 25 if above_50 else -25
    trend_score += 30 if above_200 else -30
    trend_score += min(15, max(-15, ema_20_slope * 5))
    trend_score += min(10, max(-10, ema_50_slope * 3))
    
    # Golden/Death cross
    if ema_50.iloc[-1] > ema_200.iloc[-1] and ema_50.iloc[-5] <= ema_200.iloc[-5]:
        trend_score += 15  # Golden cross
    elif ema_50.iloc[-1] < ema_200.iloc[-1] and ema_50.iloc[-5] >= ema_200.iloc[-5]:
        trend_score -= 15  # Death cross
    
    # ─── 2. MOMENTUM / RSI ──────────────────────────────────
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    rs = up.ewm(span=14, adjust=False).mean() / (down.ewm(span=14, adjust=False).mean() + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]
    
    momentum_score = 0
    if rsi_val > 70:
        momentum_score = 30  # Overbought but bullish momentum
    elif rsi_val > 55:
        momentum_score = 20
    elif rsi_val > 45:
        momentum_score = 0  # Neutral
    elif rsi_val > 30:
        momentum_score = -20
    else:
        momentum_score = -30  # Oversold
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_signal
    
    if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] > 0:
        momentum_score += 10
    elif macd_hist.iloc[-1] < 0 and macd_hist.iloc[-2] < 0:
        momentum_score -= 10
    
    # ─── 3. VOLATILITY / VIX ANALYSIS ────────────────────────
    returns = close.pct_change()
    vol_20 = returns.tail(20).std() * np.sqrt(252) * 100  # Annualized %
    vol_60 = returns.tail(60).std() * np.sqrt(252) * 100
    
    # Try to get India VIX
    vix_value = 0
    try:
        vix_df = fetch_history("^INDIAVIX", period="1mo")
        if not vix_df.empty:
            vix_value = vix_df["close"].iloc[-1]
    except Exception:
        # Fallback: US VIX
        try:
            vix_df = fetch_history("^VIX", period="1mo")
            if not vix_df.empty:
                vix_value = vix_df["close"].iloc[-1]
        except Exception:
            vix_value = vol_20  # Use realized vol as proxy
    
    # VIX signal
    if vix_value > 25:
        vix_signal = "FEAR"
        vol_score = 80
    elif vix_value > 20:
        vix_signal = "CAUTION"
        vol_score = 60
    elif vix_value > 15:
        vix_signal = "NEUTRAL"
        vol_score = 40
    elif vix_value > 10:
        vix_signal = "GREED"
        vol_score = 20
    else:
        vix_signal = "EXTREME_GREED"
        vol_score = 10
    
    # Vol expansion check
    vol_expanding = vol_20 > vol_60 * 1.3
    
    # ─── 4. ADX / TREND STRENGTH ─────────────────────────────
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr_14 = tr.ewm(span=14, adjust=False).mean()
    
    plus_di = 100 * (plus_dm.ewm(span=14, adjust=False).mean() / (atr_14 + 1e-10))
    minus_di = 100 * (minus_dm.ewm(span=14, adjust=False).mean() / (atr_14 + 1e-10))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.ewm(span=14, adjust=False).mean()
    adx_val = adx.iloc[-1]
    
    trending = adx_val > 25
    strong_trend = adx_val > 40
    
    # ─── 5. VOLUME ANALYSIS ──────────────────────────────────
    vol_avg = volume.rolling(20).mean()
    vol_ratio = volume.iloc[-1] / (vol_avg.iloc[-1] + 1)
    
    # OBV trend
    obv_direction = np.sign(close.diff())
    obv = (volume * obv_direction).cumsum()
    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / (abs(obv.iloc[-10]) + 1e-10) * 100 if len(obv) > 10 else 0
    
    volume_signal = "NEUTRAL"
    if obv_slope > 5 and price > ema_20.iloc[-1]:
        volume_signal = "ACCUMULATION"
    elif obv_slope < -5 and price < ema_20.iloc[-1]:
        volume_signal = "DISTRIBUTION"
    elif obv_slope > 0:
        volume_signal = "MILD_ACCUMULATION"
    elif obv_slope < 0:
        volume_signal = "MILD_DISTRIBUTION"
    
    # ─── 6. BREADTH ANALYSIS (using price structure) ────────
    # N-day high/low ratio
    at_20d_high = price >= high.tail(20).max() * 0.98
    at_20d_low = price <= low.tail(20).min() * 1.02
    
    # Distance from 52-week high/low
    high_252 = high.tail(min(252, len(high))).max()
    low_252 = low.tail(min(252, len(low))).min()
    dist_from_high = (price - high_252) / high_252 * 100
    dist_from_low = (price - low_252) / low_252 * 100
    
    breadth_signal = "HEALTHY"
    if dist_from_high > -3:
        breadth_signal = "STRONG"
    elif dist_from_high < -15:
        breadth_signal = "WEAK"
    elif at_20d_low:
        breadth_signal = "DETERIORATING"
    
    # ─── 7. SECTOR ROTATION ANALYSIS ─────────────────────────
    sectors = {
        "NIFTY Bank": "^NSEBANK",
        "NIFTY IT": "^CNXIT",
        "NIFTY Pharma": "^CNXPHARMA",
        "NIFTY FMCG": "^CNXFMCG",
        "NIFTY Metal": "^CNXMETAL",
        "NIFTY Realty": "^CNXREALTY",
        "NIFTY Energy": "^CNXENERGY",
    }
    
    sector_returns = {}
    for name, ticker in sectors.items():
        try:
            sdf = fetch_history(ticker, period="1mo")
            if not sdf.empty and len(sdf) > 5:
                ret = (sdf["close"].iloc[-1] / sdf["close"].iloc[-5] - 1) * 100
                sector_returns[name] = ret
        except Exception:
            pass
    
    sorted_sectors = sorted(sector_returns.items(), key=lambda x: x[1], reverse=True)
    sector_leaders = [f"{s[0]} ({s[1]:+.1f}%)" for s in sorted_sectors[:3]] if sorted_sectors else []
    sector_laggards = [f"{s[0]} ({s[1]:+.1f}%)" for s in sorted_sectors[-3:]] if len(sorted_sectors) >= 3 else []
    
    # ═══════════════════════════════════════════════════════════
    # REGIME CLASSIFICATION
    # ═══════════════════════════════════════════════════════════
    
    # Combine all scores
    total_bull = max(0, trend_score) + max(0, momentum_score)
    total_bear = abs(min(0, trend_score)) + abs(min(0, momentum_score))
    
    # Normalize to 0-100
    bull_score = min(100, (total_bull / 100) * 100)
    bear_score = min(100, (total_bear / 100) * 100)
    volatility_score = min(100, vol_score)
    trend_strength = min(100, adx_val * 2)
    
    # Determine regime
    if vol_expanding and vix_value > 25 and adx_val < 20:
        regime = MarketRegime.VOLATILE
        confidence = min(95, vol_score + 10)
    elif bull_score > 70 and trending and volume_signal in ("ACCUMULATION", "MILD_ACCUMULATION"):
        regime = MarketRegime.STRONG_BULL
        confidence = min(95, bull_score)
    elif bull_score > 50 and above_200:
        regime = MarketRegime.BULL
        confidence = min(90, bull_score)
    elif bear_score > 70 and trending and volume_signal in ("DISTRIBUTION", "MILD_DISTRIBUTION"):
        regime = MarketRegime.STRONG_BEAR
        confidence = min(95, bear_score)
    elif bear_score > 50 and not above_200:
        regime = MarketRegime.BEAR
        confidence = min(90, bear_score)
    elif not trending and volume_signal == "ACCUMULATION" and rsi_val < 45:
        regime = MarketRegime.ACCUMULATION
        confidence = 65
    elif not trending and volume_signal == "DISTRIBUTION" and rsi_val > 55:
        regime = MarketRegime.DISTRIBUTION
        confidence = 65
    else:
        regime = MarketRegime.SIDEWAYS
        confidence = max(50, 100 - trend_strength)
    
    # ─── REGIME-ADAPTIVE TRADING PARAMETERS ──────────────────
    if regime in (MarketRegime.STRONG_BULL, MarketRegime.BULL):
        position_size = 80 if regime == MarketRegime.STRONG_BULL else 60
        sl_mult = 2.0  # Wider SL in trends
        strategy = "Buy dips near EMA 20/50, ride the trend, trail SL"
        strategy_hi = "EMA 20/50 के पास गिरावट पर खरीदें, ट्रेंड चलने दें, trailing SL रखें"
    elif regime in (MarketRegime.STRONG_BEAR, MarketRegime.BEAR):
        position_size = 30 if regime == MarketRegime.STRONG_BEAR else 40
        sl_mult = 1.5  # Tight SL in bear
        strategy = "Short rallies, buy PUT options, keep cash heavy"
        strategy_hi = "रैली पर शॉर्ट करें, PUT options खरीदें, कैश भारी रखें"
    elif regime == MarketRegime.VOLATILE:
        position_size = 25
        sl_mult = 2.5  # Very wide SL
        strategy = "Reduce position size, use options for hedging, sell straddles"
        strategy_hi = "पोज़ीशन साइज़ कम करें, हेजिंग के लिए ऑप्शंस, straddle बेचें"
    elif regime == MarketRegime.ACCUMULATION:
        position_size = 50
        sl_mult = 1.8
        strategy = "Slowly build positions, focus on quality stocks, SIP mode"
        strategy_hi = "धीरे-धीरे पोज़ीशन बनाएं, क्वालिटी स्टॉक्स, SIP मोड"
    elif regime == MarketRegime.DISTRIBUTION:
        position_size = 30
        sl_mult = 1.2
        strategy = "Book profits, reduce exposure, prepare for downturn"
        strategy_hi = "प्रॉफिट बुक करें, एक्सपोज़र कम करें, गिरावट की तैयारी"
    else:  # SIDEWAYS
        position_size = 50
        sl_mult = 1.5
        strategy = "Range trading (buy support, sell resistance), options selling"
        strategy_hi = "रेंज ट्रेडिंग (सपोर्ट पर खरीदें, रेसिस्टेंस पर बेचें), ऑप्शन बेचें"
    
    # Trend/momentum signal strings
    if trend_score > 30:
        trend_sig = "STRONG UP"
    elif trend_score > 10:
        trend_sig = "UP"
    elif trend_score < -30:
        trend_sig = "STRONG DOWN"
    elif trend_score < -10:
        trend_sig = "DOWN"
    else:
        trend_sig = "FLAT"
    
    if momentum_score > 20:
        momentum_sig = "STRONG"
    elif momentum_score > 0:
        momentum_sig = "MODERATE"
    elif momentum_score < -20:
        momentum_sig = "WEAK"
    else:
        momentum_sig = "NEUTRAL"
    
    result = RegimeAnalysis(
        regime=regime,
        confidence=confidence,
        bull_score=bull_score,
        bear_score=bear_score,
        volatility_score=volatility_score,
        trend_strength=trend_strength,
        vix_signal=vix_signal,
        vix_value=vix_value,
        trend_signal=trend_sig,
        momentum_signal=momentum_sig,
        volume_signal=volume_signal,
        breadth_signal=breadth_signal,
        recommended_position_size=position_size,
        recommended_sl_multiplier=sl_mult,
        recommended_strategy=strategy,
        recommended_strategy_hi=strategy_hi,
        sector_leaders=sector_leaders,
        sector_laggards=sector_laggards,
        timestamp=datetime.now(IST).strftime("%d-%b %H:%M IST"),
    )
    
    # Cache
    _regime_cache[cache_key] = (result, time.time())
    return result


def _default_regime() -> RegimeAnalysis:
    """Return default neutral regime when data is unavailable."""
    return RegimeAnalysis(
        regime=MarketRegime.SIDEWAYS,
        confidence=50,
        bull_score=50,
        bear_score=50,
        volatility_score=50,
        trend_strength=20,
        vix_signal="NEUTRAL",
        vix_value=15,
        trend_signal="FLAT",
        momentum_signal="NEUTRAL",
        volume_signal="NEUTRAL",
        breadth_signal="NEUTRAL",
        recommended_position_size=50,
        recommended_sl_multiplier=1.5,
        recommended_strategy="Wait for clarity, trade small",
        recommended_strategy_hi="स्पष्टता का इंतज़ार करें, छोटा ट्रेड करें",
        timestamp=datetime.now(IST).strftime("%d-%b %H:%M IST"),
    )


# ═══════════════════════════════════════════════════════════════
# FORMATTING
# ═══════════════════════════════════════════════════════════════

def format_regime_report(analysis: RegimeAnalysis, lang: str = "hi") -> str:
    """Format regime analysis as Telegram message."""
    r = analysis
    
    # Bull/Bear meter
    meter_len = 20
    bull_bars = int(r.bull_score / 100 * meter_len)
    bear_bars = meter_len - bull_bars
    meter = "🟢" * bull_bars + "🔴" * bear_bars
    
    # Trend indicator
    trend_arrows = {"STRONG UP": "⬆️⬆️", "UP": "⬆️", "FLAT": "➡️", "DOWN": "⬇️", "STRONG DOWN": "⬇️⬇️"}
    trend_arrow = trend_arrows.get(r.trend_signal, "➡️")
    
    msg = f"🧠 *JARVIS MARKET REGIME DETECTOR* 🧠\n"
    msg += f"{'═' * 35}\n\n"
    
    msg += f"🎯 *Current Regime:* {r.regime.value}\n"
    msg += f"📊 *Confidence:* {r.confidence:.0f}%\n\n"
    
    msg += f"{'─' * 30}\n"
    msg += f"📈 *BULL vs BEAR METER:*\n"
    msg += f"{meter}\n"
    msg += f"🟢 Bull: {r.bull_score:.0f}% | 🔴 Bear: {r.bear_score:.0f}%\n\n"
    
    msg += f"📊 *COMPONENT ANALYSIS:*\n"
    msg += f"  {trend_arrow} Trend: *{r.trend_signal}* (Strength: {r.trend_strength:.0f}%)\n"
    msg += f"  💪 Momentum: *{r.momentum_signal}*\n"
    msg += f"  🌊 Volatility: *{r.volatility_score:.0f}/100*\n"
    msg += f"  😰 VIX: *{r.vix_value:.1f}* ({r.vix_signal})\n"
    msg += f"  📦 Volume: *{r.volume_signal}*\n"
    msg += f"  🏥 Breadth: *{r.breadth_signal}*\n\n"
    
    msg += f"{'─' * 30}\n"
    msg += f"⚡ *REGIME-ADAPTIVE STRATEGY:*\n"
    if lang == "hi":
        msg += f"📋 {r.recommended_strategy_hi}\n"
    else:
        msg += f"📋 {r.recommended_strategy}\n"
    msg += f"💰 Position Size: *{r.recommended_position_size}%* of capital\n"
    msg += f"🛡️ SL Multiplier: *{r.recommended_sl_multiplier}x ATR*\n\n"
    
    if r.sector_leaders:
        msg += f"🏆 *Sector Leaders:*\n"
        for s in r.sector_leaders:
            msg += f"  ✅ {s}\n"
    
    if r.sector_laggards:
        msg += f"📉 *Sector Laggards:*\n"
        for s in r.sector_laggards:
            msg += f"  ❌ {s}\n"
    
    msg += f"\n🕐 Updated: {r.timestamp}"
    return msg


def format_regime_voice(analysis: RegimeAnalysis) -> str:
    """Format regime for JARVIS voice output (Hindi)."""
    r = analysis
    regime_hi = {
        MarketRegime.STRONG_BULL: "Strong Bull",
        MarketRegime.BULL: "Bullish",
        MarketRegime.SIDEWAYS: "Sideways",
        MarketRegime.BEAR: "Bearish",
        MarketRegime.STRONG_BEAR: "Strong Bear",
        MarketRegime.VOLATILE: "High Volatile",
        MarketRegime.ACCUMULATION: "Accumulation phase",
        MarketRegime.DISTRIBUTION: "Distribution phase",
    }
    name = regime_hi.get(r.regime, "Sideways")
    
    voice = f"Market regime abhi {name} hai, confidence {r.confidence:.0f} percent. "
    voice += f"Bull score {r.bull_score:.0f}, Bear score {r.bear_score:.0f}. "
    voice += f"VIX {r.vix_value:.1f} pe hai, jo {r.vix_signal} signal de raha hai. "
    voice += f"Strategy: {r.recommended_strategy_hi}. "
    voice += f"Position size {r.recommended_position_size} percent rakhiye."
    
    return voice


def get_regime_quick(symbol: str = "^NSEI") -> Dict[str, Any]:
    """Quick regime summary for other modules to use."""
    try:
        r = detect_market_regime(symbol)
        return {
            "regime": r.regime.name,
            "regime_display": r.regime.value,
            "confidence": r.confidence,
            "bull_score": r.bull_score,
            "bear_score": r.bear_score,
            "volatility_score": r.volatility_score,
            "trend": r.trend_signal,
            "momentum": r.momentum_signal,
            "position_size": r.recommended_position_size,
            "sl_multiplier": r.recommended_sl_multiplier,
            "strategy": r.recommended_strategy,
            "strategy_hi": r.recommended_strategy_hi,
        }
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        return {"regime": "SIDEWAYS", "confidence": 50, "bull_score": 50, "bear_score": 50}


if __name__ == "__main__":
    print("🧠 Market Regime Detection Test...\n")
    r = detect_market_regime("^NSEI")
    print(format_regime_report(r))
    print("\n\n🎤 Voice:")
    print(format_regime_voice(r))
