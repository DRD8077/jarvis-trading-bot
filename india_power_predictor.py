"""
🇮🇳 J.A.R.V.I.S. INDIAN MARKET POWER PREDICTOR
═══════════════════════════════════════════════════
Ultra-strong prediction system combining:
  - 6 ML models (RF, XGBoost, LightGBM, GradientBoosting, AdaBoost, Ridge)
  - 43 candlestick patterns
  - Multi-timeframe RSI/MACD/Bollinger consensus
  - FII/DII flow momentum
  - VIX regime detection
  - PCR sentiment
  - Pivot level proximity
  - GIFT NIFTY gap direction
  - Sector rotation signals
  - Past prediction accuracy calibration
  - Cross-asset correlation context
  - AI-powered news sentiment

Produces HIGH-CONFIDENCE BUY/SELL signals for NIFTY, SENSEX, BANKNIFTY.

Author: JARVIS AI Core
"""

import logging
import time
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pytz

logger = logging.getLogger("india_power_predictor")
IST = pytz.timezone('Asia/Kolkata')


# ═══════════════════════════════════════════════════════════
#  MULTI-FACTOR PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════

def power_predict(index: str = "NIFTY") -> Dict[str, Any]:
    """Generate ultra-strong prediction for Indian index.
    
    Combines 10+ signal sources into one high-confidence prediction.
    Returns: {direction, confidence, score, signals, entry, sl, targets, ...}
    """
    idx = index.upper()
    symbol_map = {
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
    }
    symbol = symbol_map.get(idx, "^NSEI")
    
    result = {
        "index": idx,
        "timestamp": datetime.now(IST).isoformat(),
        "signals": {},
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
    }
    
    # Get current price
    try:
        from otm_atm_engine import get_live_spot
        spot = get_live_spot(idx)
        result["spot"] = spot
    except Exception:
        try:
            import yfinance as yf
            spot = float(yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1])
            result["spot"] = spot
        except Exception:
            result["error"] = "Cannot fetch price"
            return result
    
    # ── Signal 1: ML Ensemble ──
    ml_signal = _get_ml_signal(symbol, idx)
    result["signals"]["ml_ensemble"] = ml_signal
    _tally(result, ml_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 2: Technical Analysis (RSI/MACD/BB) ──
    tech_signal = _get_technical_signal(symbol, idx)
    result["signals"]["technical"] = tech_signal
    _tally(result, tech_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 3: Candlestick Patterns ──
    candle_signal = _get_candle_signal(symbol, idx)
    result["signals"]["candlestick"] = candle_signal
    _tally(result, candle_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 4: FII/DII Flow ──
    fii_signal = _get_fii_signal()
    result["signals"]["fii_dii"] = fii_signal
    _tally(result, fii_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 5: VIX Regime ──
    vix_signal = _get_vix_signal()
    result["signals"]["vix"] = vix_signal
    _tally(result, vix_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 6: PCR Sentiment ──
    pcr_signal = _get_pcr_signal(idx)
    result["signals"]["pcr"] = pcr_signal
    _tally(result, pcr_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 7: Pivot Level Position ──
    pivot_signal = _get_pivot_signal(idx, spot)
    result["signals"]["pivot"] = pivot_signal
    _tally(result, pivot_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 8: GIFT NIFTY Gap ──
    gift_signal = _get_gift_signal()
    result["signals"]["gift_nifty"] = gift_signal
    _tally(result, gift_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 9: AI News Sentiment ──
    news_signal = _get_news_signal()
    result["signals"]["news_sentiment"] = news_signal
    _tally(result, news_signal.get("direction", "NEUTRAL"))
    
    # ── Signal 10: Cross-Asset Correlation ──
    corr_signal = _get_correlation_signal(idx)
    result["signals"]["correlation"] = corr_signal
    _tally(result, corr_signal.get("direction", "NEUTRAL"))
    
    # ── FINAL VERDICT ──
    total = result["bullish_count"] + result["bearish_count"] + result["neutral_count"]
    bull_pct = result["bullish_count"] / max(total, 1) * 100
    bear_pct = result["bearish_count"] / max(total, 1) * 100
    
    # Weighted confidence
    signal_weights = {
        "ml_ensemble": 2.0,
        "technical": 1.5,
        "candlestick": 1.0,
        "fii_dii": 1.5,
        "vix": 0.8,
        "pcr": 1.2,
        "pivot": 0.8,
        "gift_nifty": 0.6,
        "news_sentiment": 0.8,
        "correlation": 0.5,
    }
    
    weighted_bull = 0
    weighted_bear = 0
    total_weight = 0
    
    for sig_name, sig_data in result["signals"].items():
        w = signal_weights.get(sig_name, 1.0)
        total_weight += w
        direction = sig_data.get("direction", "NEUTRAL")
        conf = sig_data.get("confidence", 50) / 100
        if direction == "BULLISH":
            weighted_bull += w * conf
        elif direction == "BEARISH":
            weighted_bear += w * conf
    
    if total_weight > 0:
        bull_score = weighted_bull / total_weight * 100
        bear_score = weighted_bear / total_weight * 100
    else:
        bull_score = bear_score = 0
    
    # Final direction
    net_score = bull_score - bear_score
    
    if net_score > 30:
        direction = "STRONG BULLISH"
        action = "BUY CALL"
        emoji = "🟢🟢"
    elif net_score > 15:
        direction = "BULLISH"
        action = "BUY CALL"
        emoji = "🟢"
    elif net_score > 5:
        direction = "MILDLY BULLISH"
        action = "MILD BUY CE"
        emoji = "🟡📈"
    elif net_score < -30:
        direction = "STRONG BEARISH"
        action = "BUY PUT"
        emoji = "🔴🔴"
    elif net_score < -15:
        direction = "BEARISH"
        action = "BUY PUT"
        emoji = "🔴"
    elif net_score < -5:
        direction = "MILDLY BEARISH"
        action = "MILD BUY PE"
        emoji = "🟡📉"
    else:
        direction = "NEUTRAL"
        action = "WAIT / SELL STRADDLE"
        emoji = "⚪"
    
    confidence = min(abs(net_score) + 40, 95)
    
    # Calibrate with past accuracy
    try:
        from trade_tracker import get_calibrated_confidence
        real_conf = get_calibrated_confidence(confidence) * 100
        result["calibrated_confidence"] = round(real_conf, 1)
    except Exception:
        pass
    
    # Price levels
    step = {"NIFTY": 50, "SENSEX": 100, "BANKNIFTY": 100}.get(idx, 50)
    result.update({
        "direction": direction,
        "action": action,
        "emoji": emoji,
        "confidence": round(confidence, 1),
        "net_score": round(net_score, 1),
        "bull_score": round(bull_score, 1),
        "bear_score": round(bear_score, 1),
        "bull_pct": round(bull_pct, 1),
        "bear_pct": round(bear_pct, 1),
        "entry": round(spot, 1),
        "stop_loss": round(spot - step * 2 if "BULL" in direction else spot + step * 2, 1),
        "target_1": round(spot + step * 1 if "BULL" in direction else spot - step * 1, 1),
        "target_2": round(spot + step * 2 if "BULL" in direction else spot - step * 2, 1),
        "target_3": round(spot + step * 4 if "BULL" in direction else spot - step * 4, 1),
    })
    
    # Log prediction for tracking
    try:
        from trade_tracker import log_prediction
        indicators = {k: v.get("direction", "N/A") for k, v in result["signals"].items()}
        log_prediction(idx, action, confidence, spot, source="power_predict", indicators=indicators)
    except Exception:
        pass
    
    return result


def _tally(result: dict, direction: str):
    """Tally bullish/bearish/neutral counts."""
    if "BULL" in direction.upper():
        result["bullish_count"] += 1
    elif "BEAR" in direction.upper():
        result["bearish_count"] += 1
    else:
        result["neutral_count"] += 1


# ═══════════════════════════════════════════════════════════
#  INDIVIDUAL SIGNAL GENERATORS
# ═══════════════════════════════════════════════════════════

def _get_ml_signal(symbol: str, name: str) -> dict:
    try:
        from ml_predictor import predict_index_direction
        pred = predict_index_direction(symbol, name)
        if pred:
            return {
                "direction": pred.get("direction", "NEUTRAL"),
                "confidence": pred.get("confidence", 50),
                "detail": f"ML Ensemble: {pred.get('direction')} ({pred.get('confidence', 50):.0f}%)",
            }
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "ML unavailable"}


def _get_technical_signal(symbol: str, name: str) -> dict:
    try:
        from candle_analyzer import analyze_index
        tech = analyze_index(symbol, name)
        if tech:
            signal = tech.get("signal", "NEUTRAL")
            direction = "BULLISH" if "BUY" in signal.upper() else "BEARISH" if "SELL" in signal.upper() else "NEUTRAL"
            return {
                "direction": direction,
                "confidence": tech.get("confidence", 55),
                "detail": f"TA: RSI={tech.get('rsi', 'N/A')}, MACD={tech.get('macd_signal', 'N/A')}",
                "rsi": tech.get("rsi"),
                "macd": tech.get("macd_signal"),
            }
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "TA unavailable"}


def _get_candle_signal(symbol: str, name: str) -> dict:
    try:
        from candle_analyzer import analyze_index
        tech = analyze_index(symbol, name)
        if tech and tech.get("patterns"):
            bullish_patterns = sum(1 for p in tech["patterns"] if p.get("type") == "bullish")
            bearish_patterns = sum(1 for p in tech["patterns"] if p.get("type") == "bearish")
            if bullish_patterns > bearish_patterns:
                return {"direction": "BULLISH", "confidence": 60 + bullish_patterns * 5,
                        "detail": f"{bullish_patterns} bullish patterns found"}
            elif bearish_patterns > bullish_patterns:
                return {"direction": "BEARISH", "confidence": 60 + bearish_patterns * 5,
                        "detail": f"{bearish_patterns} bearish patterns found"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "No strong candle patterns"}


def _get_fii_signal() -> dict:
    try:
        from nifty_super_brain import get_fii_dii_data
        data = get_fii_dii_data()
        if data:
            fii_net = data.get("fii_net", 0)
            dii_net = data.get("dii_net", 0)
            total = fii_net + dii_net
            if total > 500:
                return {"direction": "BULLISH", "confidence": 65 + min(total / 100, 20),
                        "detail": f"FII+DII net inflow ₹{total:.0f}Cr"}
            elif total < -500:
                return {"direction": "BEARISH", "confidence": 65 + min(abs(total) / 100, 20),
                        "detail": f"FII+DII net outflow ₹{abs(total):.0f}Cr"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "FII/DII data unavailable"}


def _get_vix_signal() -> dict:
    try:
        from nifty_super_brain import get_india_vix
        data = get_india_vix()
        if data:
            vix = data.get("vix", 15)
            trend = data.get("trend", "")
            if vix > 22:
                return {"direction": "BEARISH", "confidence": 65,
                        "detail": f"VIX {vix:.1f} — FEAR! Bearish bias"}
            elif vix < 12 and "falling" in trend.lower():
                return {"direction": "BULLISH", "confidence": 60,
                        "detail": f"VIX {vix:.1f} — Low fear, complacency"}
            elif "rising" in trend.lower() and vix > 16:
                return {"direction": "BEARISH", "confidence": 55,
                        "detail": f"VIX {vix:.1f} rising — caution"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "VIX neutral"}


def _get_pcr_signal(index: str) -> dict:
    try:
        from nifty_super_brain import get_pcr_data
        data = get_pcr_data(index)
        if data:
            pcr = data.get("pcr_oi", 0)
            if pcr > 1.3:
                return {"direction": "BULLISH", "confidence": 65,
                        "detail": f"PCR {pcr:.2f} — Oversold, bull reversal likely"}
            elif pcr < 0.7:
                return {"direction": "BEARISH", "confidence": 65,
                        "detail": f"PCR {pcr:.2f} — Overbought, bear reversal likely"}
            elif pcr > 1.0:
                return {"direction": "BULLISH", "confidence": 55,
                        "detail": f"PCR {pcr:.2f} — Mild bullish"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "PCR neutral"}


def _get_pivot_signal(index: str, spot: float) -> dict:
    try:
        from nifty_super_brain import calculate_pivot_levels
        data = calculate_pivot_levels(index)
        if data:
            classic = data.get("classic", {})
            pp = classic.get("PP", 0)
            r1 = classic.get("R1", 0)
            s1 = classic.get("S1", 0)
            
            if spot > r1:
                return {"direction": "BULLISH", "confidence": 65,
                        "detail": f"Above R1 ({r1:.0f}) — Breakout bullish"}
            elif spot > pp:
                return {"direction": "BULLISH", "confidence": 55,
                        "detail": f"Above Pivot ({pp:.0f})"}
            elif spot < s1:
                return {"direction": "BEARISH", "confidence": 65,
                        "detail": f"Below S1 ({s1:.0f}) — Breakdown bearish"}
            elif spot < pp:
                return {"direction": "BEARISH", "confidence": 55,
                        "detail": f"Below Pivot ({pp:.0f})"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "At pivot"}


def _get_gift_signal() -> dict:
    try:
        from nifty_super_brain import get_gift_nifty
        data = get_gift_nifty()
        if data:
            gap = data.get("gap_pct", 0)
            if gap > 0.3:
                return {"direction": "BULLISH", "confidence": 60,
                        "detail": f"GIFT NIFTY gap up {gap:.1f}%"}
            elif gap < -0.3:
                return {"direction": "BEARISH", "confidence": 60,
                        "detail": f"GIFT NIFTY gap down {gap:.1f}%"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "No significant gap"}


def _get_news_signal() -> dict:
    try:
        from sentiment_engine import analyze_news_sentiment
        data = analyze_news_sentiment(use_ai=True)
        if data:
            sentiment = data.get("sentiment", "NEUTRAL")
            score = data.get("score", 0)
            if "BULL" in sentiment.upper():
                return {"direction": "BULLISH", "confidence": 55 + abs(score) * 30,
                        "detail": f"News: {sentiment} (score={score:.2f})"}
            elif "BEAR" in sentiment.upper():
                return {"direction": "BEARISH", "confidence": 55 + abs(score) * 30,
                        "detail": f"News: {sentiment} (score={score:.2f})"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "News neutral"}


def _get_correlation_signal(index: str) -> dict:
    try:
        from cross_asset_engine import scan_all_correlations
        data = scan_all_correlations()
        if data:
            regime = data.get("regime", "NORMAL")
            if regime == "RISK_ON":
                return {"direction": "BULLISH", "confidence": 60,
                        "detail": "Global Risk-ON regime"}
            elif regime == "RISK_OFF":
                return {"direction": "BEARISH", "confidence": 60,
                        "detail": "Global Risk-OFF regime"}
            
            # Check for divergences involving this index
            divs = data.get("divergences", [])
            for d in divs:
                if index in d.get("pair", ""):
                    return {"direction": "NEUTRAL", "confidence": 55,
                            "detail": f"Divergence: {d['pair']}"}
    except Exception:
        pass
    return {"direction": "NEUTRAL", "confidence": 50, "detail": "No correlation signal"}


# ═══════════════════════════════════════════════════════════
#  TELEGRAM FORMATTING
# ═══════════════════════════════════════════════════════════

def format_power_prediction(result: Dict) -> List[str]:
    """Format power prediction for Telegram (multi-page)."""
    pages = []
    idx = result.get("index", "NIFTY")
    
    # ── Page 1: Main Verdict ──
    p1 = (
        f"🔮 *{idx} POWER PREDICTION*\n"
        f"{'━' * 30}\n\n"
        f"💰 *Spot:* ₹{result.get('spot', 0):,.1f}\n\n"
        f"{result.get('emoji', '⚪')} *Direction:* {result.get('direction', 'NEUTRAL')}\n"
        f"🎯 *Action:* {result.get('action', 'WAIT')}\n"
        f"📊 *Confidence:* {result.get('confidence', 50):.0f}%\n"
    )
    
    cal_conf = result.get("calibrated_confidence")
    if cal_conf:
        p1 += f"📐 *Calibrated (real accuracy):* {cal_conf:.0f}%\n"
    
    p1 += (
        f"\n📈 *Bull Score:* {result.get('bull_score', 0):.0f}/100\n"
        f"📉 *Bear Score:* {result.get('bear_score', 0):.0f}/100\n"
        f"🔢 *Net:* {result.get('net_score', 0):+.0f}\n\n"
        f"📊 *Signals:* {result.get('bullish_count', 0)} Bullish | "
        f"{result.get('bearish_count', 0)} Bearish | "
        f"{result.get('neutral_count', 0)} Neutral\n\n"
    )
    
    if "BULL" in result.get("direction", ""):
        p1 += (
            f"🟢 *Entry:* ₹{result.get('entry', 0):,.1f}\n"
            f"🎯 *T1:* ₹{result.get('target_1', 0):,.1f}\n"
            f"🎯 *T2:* ₹{result.get('target_2', 0):,.1f}\n"
            f"🎯 *T3:* ₹{result.get('target_3', 0):,.1f}\n"
            f"🛑 *SL:* ₹{result.get('stop_loss', 0):,.1f}\n"
        )
    elif "BEAR" in result.get("direction", ""):
        p1 += (
            f"🔴 *Entry:* ₹{result.get('entry', 0):,.1f}\n"
            f"🎯 *T1:* ₹{result.get('target_1', 0):,.1f}\n"
            f"🎯 *T2:* ₹{result.get('target_2', 0):,.1f}\n"
            f"🎯 *T3:* ₹{result.get('target_3', 0):,.1f}\n"
            f"🛑 *SL:* ₹{result.get('stop_loss', 0):,.1f}\n"
        )
    
    pages.append(p1)
    
    # ── Page 2: Signal Breakdown ──
    p2 = f"📊 *{idx} SIGNAL BREAKDOWN*\n{'━' * 28}\n\n"
    
    signal_icons = {
        "ml_ensemble": "🧠", "technical": "📈", "candlestick": "🕯️",
        "fii_dii": "🏛️", "vix": "😱", "pcr": "📊",
        "pivot": "📐", "gift_nifty": "🌅", "news_sentiment": "📰",
        "correlation": "🔗",
    }
    
    for name, sig in result.get("signals", {}).items():
        icon = signal_icons.get(name, "📌")
        direction = sig.get("direction", "NEUTRAL")
        conf = sig.get("confidence", 50)
        detail = sig.get("detail", "")
        
        dir_emoji = "🟢" if "BULL" in direction else "🔴" if "BEAR" in direction else "⚪"
        p2 += f"{icon} *{name.replace('_', ' ').title()}*: {dir_emoji} {direction} ({conf:.0f}%)\n"
        if detail:
            p2 += f"   _→ {detail}_\n"
    
    pages.append(p2)
    
    return pages


def format_power_voice(result: Dict) -> str:
    """Hindi voice summary."""
    idx = result.get("index", "NIFTY")
    direction = result.get("direction", "NEUTRAL")
    confidence = result.get("confidence", 50)
    spot = result.get("spot", 0)
    bull = result.get("bullish_count", 0)
    bear = result.get("bearish_count", 0)
    
    msg = f"{idx} abhi {spot} pe hai. "
    
    if "BULL" in direction:
        msg += f"Power prediction BULLISH hai {confidence:.0f} percent confidence ke saath. "
        msg += f"10 mein se {bull} signals bullish hain. "
        msg += f"Target 1: {result.get('target_1', 0)}, Target 2: {result.get('target_2', 0)}. "
        msg += f"Stop loss {result.get('stop_loss', 0)} pe rakhna."
    elif "BEAR" in direction:
        msg += f"Power prediction BEARISH hai {confidence:.0f} percent confidence ke saath. "
        msg += f"10 mein se {bear} signals bearish hain. "
        msg += f"Put option ke liye target {result.get('target_1', 0)}. "
        msg += f"Stop loss {result.get('stop_loss', 0)} pe."
    else:
        msg += f"Market NEUTRAL hai. Koi clear signal nahi. Wait karo."
    
    return msg


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'power_predict',
    'format_power_prediction',
    'format_power_voice',
]
