"""
🧠 J.A.R.V.I.S. SELF-LEARNING TRADE TRACKER
═══════════════════════════════════════════════
Tracks every prediction JARVIS makes, verifies accuracy after 24 hours,
builds calibration curves, and feeds real accuracy stats into risk management.

Features:
- Logs every prediction (symbol, action, score, price)
- Auto-verifies 24h later against real price
- Computes rolling accuracy per score bucket (calibration)
- Feeds real win_rate into Kelly Criterion
- Tracks which indicators were most accurate
- Self-improving: adjusts verdict weights based on outcomes

Author: JARVIS AI Core
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

import pytz

logger = logging.getLogger("trade_tracker")
IST = pytz.timezone('Asia/Kolkata')

PREDICTION_LOG_FILE = "jarvis_predictions.json"
ACCURACY_STATS_FILE = "jarvis_accuracy_stats.json"

# ═══════════════════════════════════════════════════════════
#  PREDICTION LOGGING
# ═══════════════════════════════════════════════════════════

_predictions: List[dict] = []
_accuracy_stats: Dict[str, Any] = {}


def _load_predictions():
    global _predictions, _accuracy_stats
    try:
        if os.path.exists(PREDICTION_LOG_FILE):
            with open(PREDICTION_LOG_FILE, 'r') as f:
                _predictions = json.load(f)
    except Exception:
        _predictions = []
    try:
        if os.path.exists(ACCURACY_STATS_FILE):
            with open(ACCURACY_STATS_FILE, 'r') as f:
                _accuracy_stats = json.load(f)
    except Exception:
        _accuracy_stats = {}

_load_predictions()


def _save_predictions():
    try:
        with open(PREDICTION_LOG_FILE, 'w') as f:
            json.dump(_predictions[-5000:], f, indent=1, default=str)
    except Exception as e:
        logger.error(f"Save predictions failed: {e}")


def _save_accuracy_stats():
    try:
        with open(ACCURACY_STATS_FILE, 'w') as f:
            json.dump(_accuracy_stats, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Save accuracy failed: {e}")


def log_prediction(symbol: str, action: str, score: float, price: float,
                   source: str = "ultra_ai", indicators: dict = None,
                   timeframe: str = "24h"):
    """Log a prediction for future accuracy tracking.
    
    Args:
        symbol: Token/stock symbol
        action: STRONG BUY, BUY, HOLD, SELL, STRONG SELL
        score: Raw score (0-100)
        price: Price at time of prediction
        source: Which module made the prediction
        indicators: Dict of individual indicator signals
        timeframe: Expected verification timeframe
    """
    entry = {
        "id": f"{symbol}_{int(time.time())}",
        "symbol": symbol.upper(),
        "action": action,
        "score": round(score, 1),
        "price_at_call": price,
        "source": source,
        "indicators": indicators or {},
        "timeframe": timeframe,
        "timestamp": datetime.now(IST).isoformat(),
        "unix_ts": time.time(),
        "verified": False,
        "outcome": None,       # "correct" / "wrong" / "partial"
        "price_after": None,
        "pnl_pct": None,
    }
    
    _predictions.append(entry)
    
    # Auto-save every 10 predictions
    if len(_predictions) % 10 == 0:
        _save_predictions()
    
    logger.info(f"[TRACKER] Logged: {symbol} {action} @ {price} (score={score})")
    return entry["id"]


# ═══════════════════════════════════════════════════════════
#  PREDICTION VERIFICATION (call periodically)
# ═══════════════════════════════════════════════════════════

def verify_predictions(max_verify: int = 50) -> Dict[str, int]:
    """Check unverified predictions that are 24h+ old against actual prices.
    
    Returns: {"verified": N, "correct": N, "wrong": N, "partial": N}
    """
    stats = {"verified": 0, "correct": 0, "wrong": 0, "partial": 0, "errors": 0}
    now = time.time()
    verified_any = False
    
    for pred in _predictions:
        if pred.get("verified"):
            continue
        
        # Check if 24h has passed
        age_hours = (now - pred.get("unix_ts", now)) / 3600
        if age_hours < 6:  # Check after min 6 hours
            continue
        
        if stats["verified"] >= max_verify:
            break
        
        symbol = pred["symbol"]
        price_at_call = pred.get("price_at_call", 0)
        action = pred.get("action", "")
        
        if price_at_call <= 0:
            pred["verified"] = True
            pred["outcome"] = "invalid"
            continue
        
        # Get current price
        current_price = _get_current_price(symbol, pred.get("source", ""))
        
        if current_price is None or current_price <= 0:
            stats["errors"] += 1
            continue
        
        # Calculate P&L
        pnl_pct = ((current_price - price_at_call) / price_at_call) * 100
        
        # Determine outcome
        outcome = _judge_outcome(action, pnl_pct)
        
        pred["verified"] = True
        pred["outcome"] = outcome
        pred["price_after"] = current_price
        pred["pnl_pct"] = round(pnl_pct, 2)
        pred["verified_at"] = datetime.now(IST).isoformat()
        
        stats["verified"] += 1
        stats[outcome] = stats.get(outcome, 0) + 1
        verified_any = True
        
        logger.info(f"[TRACKER] Verified {symbol}: {action} → {outcome} ({pnl_pct:+.1f}%)")
    
    if verified_any:
        _save_predictions()
        _update_accuracy_stats()
    
    return stats


def _get_current_price(symbol: str, source: str) -> Optional[float]:
    """Get current price for a symbol."""
    # Try CoinDCX first (crypto)
    try:
        from coindcx_engine import coindcx_quick_price
        price = coindcx_quick_price(symbol)
        if price and price > 0:
            return price
    except Exception:
        pass
    
    # Try yfinance (stocks)
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception:
        pass
    
    return None


def _judge_outcome(action: str, pnl_pct: float) -> str:
    """Judge if prediction was correct based on action and actual P&L."""
    action_upper = action.upper()
    
    if "BUY" in action_upper or "STRONG BUY" in action_upper:
        if pnl_pct >= 3:
            return "correct"
        elif pnl_pct >= 0:
            return "partial"
        else:
            return "wrong"
    
    elif "SELL" in action_upper or "AVOID" in action_upper:
        if pnl_pct <= -2:
            return "correct"  # Correctly predicted it would drop
        elif pnl_pct <= 0:
            return "partial"
        else:
            return "wrong"
    
    else:  # HOLD
        if abs(pnl_pct) <= 3:
            return "correct"  # Sideways = correct HOLD
        else:
            return "partial"


# ═══════════════════════════════════════════════════════════
#  ACCURACY & CALIBRATION STATS
# ═══════════════════════════════════════════════════════════

def _update_accuracy_stats():
    """Rebuild accuracy stats from all verified predictions."""
    global _accuracy_stats
    
    verified = [p for p in _predictions if p.get("verified") and p.get("outcome") in ("correct", "wrong", "partial")]
    
    if not verified:
        return
    
    # Overall stats
    correct = sum(1 for p in verified if p["outcome"] == "correct")
    partial = sum(1 for p in verified if p["outcome"] == "partial")
    wrong = sum(1 for p in verified if p["outcome"] == "wrong")
    total = len(verified)
    
    # Score-bucket accuracy (calibration)
    buckets = {}
    for p in verified:
        bucket = int(p.get("score", 50) // 10) * 10  # 0, 10, 20, ... 90
        bucket_key = f"{bucket}-{bucket+9}"
        if bucket_key not in buckets:
            buckets[bucket_key] = {"total": 0, "correct": 0, "avg_pnl": []}
        buckets[bucket_key]["total"] += 1
        if p["outcome"] == "correct":
            buckets[bucket_key]["correct"] += 1
        if p.get("pnl_pct") is not None:
            buckets[bucket_key]["avg_pnl"].append(p["pnl_pct"])
    
    # Compute per-bucket accuracy
    for key, data in buckets.items():
        data["accuracy"] = round(data["correct"] / max(data["total"], 1) * 100, 1)
        data["avg_pnl"] = round(sum(data["avg_pnl"]) / max(len(data["avg_pnl"]), 1), 2)
    
    # Per-source accuracy
    source_stats = {}
    for p in verified:
        src = p.get("source", "unknown")
        if src not in source_stats:
            source_stats[src] = {"total": 0, "correct": 0}
        source_stats[src]["total"] += 1
        if p["outcome"] == "correct":
            source_stats[src]["correct"] += 1
    for src, data in source_stats.items():
        data["accuracy"] = round(data["correct"] / max(data["total"], 1) * 100, 1)
    
    # Per-action accuracy
    action_stats = {}
    for p in verified:
        act = p.get("action", "UNKNOWN")
        if act not in action_stats:
            action_stats[act] = {"total": 0, "correct": 0, "avg_pnl": []}
        action_stats[act]["total"] += 1
        if p["outcome"] == "correct":
            action_stats[act]["correct"] += 1
        if p.get("pnl_pct") is not None:
            action_stats[act]["avg_pnl"].append(p["pnl_pct"])
    for act, data in action_stats.items():
        data["accuracy"] = round(data["correct"] / max(data["total"], 1) * 100, 1)
        data["avg_pnl"] = round(sum(data["avg_pnl"]) / max(len(data["avg_pnl"]), 1), 2)
    
    # Indicator-level accuracy (which indicators are most reliable)
    indicator_accuracy = _compute_indicator_accuracy(verified)
    
    _accuracy_stats = {
        "total_predictions": total,
        "correct": correct,
        "partial": partial,
        "wrong": wrong,
        "overall_accuracy": round(correct / max(total, 1) * 100, 1),
        "overall_accuracy_with_partial": round((correct + partial * 0.5) / max(total, 1) * 100, 1),
        "calibration_buckets": buckets,
        "source_accuracy": source_stats,
        "action_accuracy": action_stats,
        "indicator_accuracy": indicator_accuracy,
        "avg_pnl_correct": round(sum(p["pnl_pct"] for p in verified if p["outcome"] == "correct" and p.get("pnl_pct")) / max(correct, 1), 2),
        "avg_pnl_wrong": round(sum(p["pnl_pct"] for p in verified if p["outcome"] == "wrong" and p.get("pnl_pct")) / max(wrong, 1), 2),
        "last_updated": datetime.now(IST).isoformat(),
    }
    
    _save_accuracy_stats()
    logger.info(f"[TRACKER] Stats updated: {total} predictions, {_accuracy_stats['overall_accuracy']}% accuracy")


def _compute_indicator_accuracy(verified: list) -> dict:
    """Figure out which individual indicators were most accurate."""
    indicator_stats = {}
    
    for pred in verified:
        indicators = pred.get("indicators", {})
        outcome = pred["outcome"]
        
        for ind_name, ind_signal in indicators.items():
            if ind_name not in indicator_stats:
                indicator_stats[ind_name] = {"bullish_correct": 0, "bullish_total": 0,
                                              "bearish_correct": 0, "bearish_total": 0}
            
            signal_str = str(ind_signal).upper()
            is_bullish = any(w in signal_str for w in ["BUY", "BULL", "UP", "LONG", "POSITIVE"])
            is_bearish = any(w in signal_str for w in ["SELL", "BEAR", "DOWN", "SHORT", "NEGATIVE"])
            
            if is_bullish:
                indicator_stats[ind_name]["bullish_total"] += 1
                if outcome == "correct":
                    indicator_stats[ind_name]["bullish_correct"] += 1
            elif is_bearish:
                indicator_stats[ind_name]["bearish_total"] += 1
                if outcome == "correct":
                    indicator_stats[ind_name]["bearish_correct"] += 1
    
    # Compute accuracy per indicator
    for name, data in indicator_stats.items():
        total = data["bullish_total"] + data["bearish_total"]
        correct = data["bullish_correct"] + data["bearish_correct"]
        data["accuracy"] = round(correct / max(total, 1) * 100, 1)
        data["total_signals"] = total
    
    return indicator_stats


# ═══════════════════════════════════════════════════════════
#  CALIBRATED CONFIDENCE
# ═══════════════════════════════════════════════════════════

def get_calibrated_confidence(raw_score: float) -> float:
    """Map raw verdict score (0-100) to actual historical accuracy.
    
    E.g., if score=75 historically was correct 68% of the time → returns 0.68
    This is the REAL confidence, not the optimistic raw score.
    """
    if not _accuracy_stats or "calibration_buckets" not in _accuracy_stats:
        # No history yet — return raw score as-is (slightly discounted)
        return min(raw_score * 0.8, 95) / 100
    
    bucket = int(raw_score // 10) * 10
    bucket_key = f"{bucket}-{bucket+9}"
    
    buckets = _accuracy_stats["calibration_buckets"]
    if bucket_key in buckets and buckets[bucket_key]["total"] >= 5:
        return buckets[bucket_key]["accuracy"] / 100
    
    # Not enough data for this bucket — use overall
    return _accuracy_stats.get("overall_accuracy", 50) / 100


def get_real_win_rate() -> Tuple[float, float, float]:
    """Get real win_rate, avg_win, avg_loss from prediction history.
    
    Returns: (win_rate, avg_win_pct, avg_loss_pct)
    Use this to feed into Kelly Criterion for REAL position sizing!
    """
    if not _accuracy_stats:
        return 0.55, 5.0, 3.0  # Conservative defaults
    
    total = _accuracy_stats.get("total_predictions", 0)
    if total < 10:
        return 0.55, 5.0, 3.0  # Not enough data yet
    
    correct = _accuracy_stats.get("correct", 0)
    win_rate = correct / max(total, 1)
    
    avg_win = abs(_accuracy_stats.get("avg_pnl_correct", 5.0))
    avg_loss = abs(_accuracy_stats.get("avg_pnl_wrong", 3.0))
    
    return win_rate, max(avg_win, 0.1), max(avg_loss, 0.1)


def get_best_indicators() -> List[Tuple[str, float]]:
    """Get indicators sorted by accuracy (most reliable first).
    
    Returns: [(indicator_name, accuracy_pct), ...]
    """
    if not _accuracy_stats or "indicator_accuracy" not in _accuracy_stats:
        return []
    
    ind_stats = _accuracy_stats["indicator_accuracy"]
    ranked = [
        (name, data["accuracy"]) 
        for name, data in ind_stats.items() 
        if data.get("total_signals", 0) >= 5
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def get_adaptive_weights() -> Dict[str, float]:
    """Get optimized weights for verdict scoring based on indicator accuracy.
    
    Instead of hardcoded weights, use accuracy-weighted scoring.
    """
    best = get_best_indicators()
    if not best:
        # Defaults
        return {
            "ai_signal": 0.40,
            "rug_risk": 0.20,
            "money_flow": 0.20,
            "whale": 0.10,
            "rr_ratio": 0.10,
        }
    
    # Normalize accuracies into weights
    total_acc = sum(acc for _, acc in best)
    if total_acc == 0:
        total_acc = 1
    
    weights = {}
    for name, acc in best:
        weights[name] = acc / total_acc
    
    return weights


# ═══════════════════════════════════════════════════════════
#  ACCURACY REPORT (for Telegram display)
# ═══════════════════════════════════════════════════════════

def format_accuracy_report() -> str:
    """Generate a beautiful accuracy report for Telegram."""
    stats = _accuracy_stats
    if not stats or stats.get("total_predictions", 0) == 0:
        return (
            "📊 *JARVIS Accuracy Report*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "अभी तक कोई verified prediction नहीं है जी।\n"
            "Predictions log हो रहे हैं, 24 घंटे बाद accuracy देखिएगा! 🌸"
        )
    
    report = (
        "📊 *JARVIS PREDICTION ACCURACY REPORT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    # Overall
    total = stats["total_predictions"]
    acc = stats["overall_accuracy"]
    acc_partial = stats["overall_accuracy_with_partial"]
    
    # Determine emoji based on accuracy
    if acc >= 70:
        grade = "🏆 EXCELLENT"
    elif acc >= 55:
        grade = "✅ GOOD"
    elif acc >= 40:
        grade = "🟡 AVERAGE"
    else:
        grade = "🔴 NEEDS IMPROVEMENT"
    
    report += (
        f"📈 *Overall:* {grade}\n"
        f"┣ Total Predictions: {total}\n"
        f"┣ Accuracy: *{acc}%*\n"
        f"┣ With Partial: {acc_partial}%\n"
        f"┣ Correct: {stats['correct']} | Wrong: {stats['wrong']} | Partial: {stats['partial']}\n"
        f"┣ Avg Win: +{stats.get('avg_pnl_correct', 0)}%\n"
        f"┗ Avg Loss: {stats.get('avg_pnl_wrong', 0)}%\n\n"
    )
    
    # Per-action breakdown
    action_stats = stats.get("action_accuracy", {})
    if action_stats:
        report += "🎯 *Per-Action Accuracy:*\n"
        for action, data in sorted(action_stats.items(), key=lambda x: x[1].get("accuracy", 0), reverse=True):
            emoji = "🟢" if data["accuracy"] >= 60 else "🟡" if data["accuracy"] >= 40 else "🔴"
            report += f"  {emoji} {action}: {data['accuracy']}% ({data['total']} trades, avg P&L: {data.get('avg_pnl', 0):+.1f}%)\n"
        report += "\n"
    
    # Best indicators
    best = get_best_indicators()
    if best:
        report += "🏅 *Most Reliable Indicators:*\n"
        for i, (name, acc) in enumerate(best[:5], 1):
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
            report += f"  {medal} {name}: {acc}% accuracy\n"
        report += "\n"
    
    # Calibration
    calibration = stats.get("calibration_buckets", {})
    if calibration:
        report += "📐 *Score Calibration:*\n"
        report += "_Score → Actual accuracy_\n"
        for bucket_key in sorted(calibration.keys()):
            data = calibration[bucket_key]
            if data["total"] >= 3:
                bar = "█" * int(data["accuracy"] / 10)
                report += f"  {bucket_key}: {bar} {data['accuracy']}% (n={data['total']})\n"
    
    report += f"\n_Last updated: {stats.get('last_updated', 'N/A')}_\n"
    report += "⚠️ _Past accuracy doesn't guarantee future results_"
    
    return report


def format_accuracy_voice() -> str:
    """Voice-friendly accuracy summary."""
    stats = _accuracy_stats
    if not stats or stats.get("total_predictions", 0) == 0:
        return "Abhi tak koi verified prediction nahi hai. 24 ghante baad accuracy report milega."
    
    acc = stats["overall_accuracy"]
    total = stats["total_predictions"]
    
    return (
        f"JARVIS ki overall accuracy {acc} percent hai, "
        f"{total} predictions mein se {stats['correct']} correct the. "
        f"Average winning trade plus {stats.get('avg_pnl_correct', 0)} percent tha."
    )


# ═══════════════════════════════════════════════════════════
#  EXPORT
# ═══════════════════════════════════════════════════════════

__all__ = [
    'log_prediction',
    'verify_predictions',
    'get_calibrated_confidence',
    'get_real_win_rate',
    'get_best_indicators',
    'get_adaptive_weights',
    'format_accuracy_report',
    'format_accuracy_voice',
]
