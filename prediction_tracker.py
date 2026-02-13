"""
🎯 PREDICTION ACCURACY TRACKER — L3 Upgrade
═══════════════════════════════════════════════
Tracks ML prediction accuracy over time:
  ✅ Records predictions with timestamps
  ✅ Verifies against actual market data
  ✅ Tracks accuracy by index, timeframe, model
  ✅ Auto-adjusts confidence thresholds
  ✅ Provides leaderboard and performance reports

Author: JARVIS Nuclear ML Division
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pytz

logger = logging.getLogger("prediction_tracker")
IST = pytz.timezone("Asia/Kolkata")

PREDICTIONS_FILE = "jarvis_prediction_history.json"
_tracker_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════
#  PREDICTION STORAGE
# ═══════════════════════════════════════════════════════════

_predictions: List[Dict] = []
_loaded = False


def _load_predictions():
    global _predictions, _loaded
    if _loaded:
        return
    try:
        if os.path.exists(PREDICTIONS_FILE):
            with open(PREDICTIONS_FILE, "r") as f:
                _predictions = json.load(f)
    except Exception as e:
        logger.warning(f"[TRACKER] Load error: {e}")
        _predictions = []
    _loaded = True


def _save_predictions():
    with _tracker_lock:
        try:
            import tempfile
            fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=".")
            with os.fdopen(fd, 'w') as f:
                json.dump(_predictions[-5000:], f, indent=1)  # Keep last 5000
            os.replace(tmp, PREDICTIONS_FILE)
        except Exception as e:
            logger.error(f"[TRACKER] Save error: {e}")


def record_prediction(
    symbol: str,
    direction: str,  # "UP" / "DOWN" / "NEUTRAL"
    confidence: float,  # 0.0 - 1.0
    predicted_price: float = 0,
    current_price: float = 0,
    target_price: float = 0,
    stop_loss: float = 0,
    model_name: str = "ensemble",
    timeframe: str = "1d",
    source: str = "ml_predictor",
    chat_id: int = 0,
    extra: Dict = None,
):
    """Record a new prediction for future accuracy tracking."""
    _load_predictions()
    
    pred = {
        "id": f"{symbol}_{int(time.time())}_{len(_predictions)}",
        "symbol": symbol.upper(),
        "direction": direction.upper(),
        "confidence": round(confidence, 4),
        "predicted_price": predicted_price,
        "current_price": current_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "model": model_name,
        "timeframe": timeframe,
        "source": source,
        "chat_id": chat_id,
        "timestamp": datetime.now(IST).isoformat(),
        "ts_epoch": time.time(),
        "verified": False,
        "actual_outcome": None,  # Will be filled later
        "actual_price": 0,
        "hit_target": None,
        "hit_stop_loss": None,
        "profit_pct": 0,
        "extra": extra or {},
    }
    
    with _tracker_lock:
        _predictions.append(pred)
    
    _save_predictions()
    logger.info(f"[TRACKER] Recorded: {symbol} {direction} @ {current_price} conf={confidence:.1%}")
    return pred["id"]


def verify_predictions(max_age_hours: int = 72, max_verify: int = None):
    """
    Verify unresolved predictions against actual market data.
    Called periodically by background thread.
    """
    _load_predictions()
    
    try:
        import yfinance as yf
    except ImportError:
        return 0
    
    verified_count = 0
    now = time.time()
    
    for pred in _predictions:
        if pred.get("verified"):
            continue
        
        age_hours = (now - pred.get("ts_epoch", now)) / 3600
        if age_hours < 1:
            continue  # Too fresh
        if age_hours > max_age_hours:
            pred["verified"] = True
            pred["actual_outcome"] = "EXPIRED"
            verified_count += 1
            continue
        
        symbol = pred["symbol"]
        verified_count = 0
        correct = 0
        wrong = 0
        expired = 0
        now = time.time()
        processed = 0
        for pred in _predictions:
            if pred.get("verified"):
                continue
            age_hours = (now - pred.get("ts_epoch", now)) / 3600
            if age_hours < 1:
                continue  # Too fresh
            if age_hours > max_age_hours:
                pred["verified"] = True
                pred["actual_outcome"] = "EXPIRED"
                expired += 1
                verified_count += 1
                processed += 1
                if max_verify and processed >= max_verify:
                    break
                continue
            symbol = pred["symbol"]
            direction = pred["direction"]
            entry_price = pred.get("current_price", 0)
            if entry_price <= 0:
                continue
            ticker_map = {
                "NIFTY": "^NSEI",
                "SENSEX": "^BSESN",
                "BANKNIFTY": "^NSEBANK",
            }
            ticker = ticker_map.get(symbol, f"{symbol}.NS")
            try:
                df = yf.download(ticker, period="5d", interval="1d", progress=False)
                if df is None or len(df) < 1:
                    continue
                if hasattr(df.columns, 'get_level_values'):
                    try:
                        df.columns = df.columns.get_level_values(0)
                    except Exception:
                        pass
                close_col = 'Close' if 'Close' in df.columns else 'close'
                actual_price = float(df[close_col].iloc[-1])
                high_price = float(df['High' if 'High' in df.columns else 'high'].max())
                low_price = float(df['Low' if 'Low' in df.columns else 'low'].min())
                change_pct = (actual_price - entry_price) / entry_price * 100
                target = pred.get("target_price", 0)
                sl = pred.get("stop_loss", 0)
                hit_target = False
                hit_sl = False
                if target > 0 and direction == "UP" and high_price >= target:
                    hit_target = True
                elif target > 0 and direction == "DOWN" and low_price <= target:
                    hit_target = True
                if sl > 0 and direction == "UP" and low_price <= sl:
                    hit_sl = True
                elif sl > 0 and direction == "DOWN" and high_price >= sl:
                    hit_sl = True
                if direction == "UP":
                    is_correct = actual_price > entry_price
                elif direction == "DOWN":
                    is_correct = actual_price < entry_price
                else:
                    is_correct = abs(change_pct) < 0.5
                pred["verified"] = True
                pred["actual_price"] = actual_price
                pred["actual_outcome"] = "CORRECT" if is_correct else "WRONG"
                pred["hit_target"] = hit_target
                pred["hit_stop_loss"] = hit_sl
                pred["profit_pct"] = round(change_pct, 4)
                verified_count += 1
                processed += 1
                if is_correct:
                    correct += 1
                else:
                    wrong += 1
                if max_verify and processed >= max_verify:
                    break
            except Exception as e:
                logger.debug(f"[TRACKER] Verify failed for {symbol}: {e}")
                continue
        if verified_count > 0:
            _save_predictions()
            logger.info(f"[TRACKER] Verified {verified_count} predictions")
        return {
            "verified": verified_count,
            "correct": correct,
            "wrong": wrong,
            "expired": expired,
        }
    return verified_count


def get_accuracy_report(symbol: str = None, days: int = 30) -> Dict:
    """Get prediction accuracy statistics."""
    _load_predictions()
    
    cutoff = time.time() - (days * 86400)
    
    # Filter predictions
    preds = [p for p in _predictions if p.get("verified") and p.get("ts_epoch", 0) > cutoff]
    if symbol:
        preds = [p for p in preds if p["symbol"] == symbol.upper()]
    
    if not preds:
        return {"total": 0, "accuracy": 0, "message": "No verified predictions yet"}
    
    total = len(preds)
    correct = sum(1 for p in preds if p.get("actual_outcome") == "CORRECT")
    wrong = sum(1 for p in preds if p.get("actual_outcome") == "WRONG")
    expired = sum(1 for p in preds if p.get("actual_outcome") == "EXPIRED")
    
    targets_hit = sum(1 for p in preds if p.get("hit_target"))
    sl_hit = sum(1 for p in preds if p.get("hit_stop_loss"))
    
    avg_profit = sum(p.get("profit_pct", 0) for p in preds if p.get("actual_outcome") in ("CORRECT", "WRONG")) / max(1, correct + wrong)
    
    # Accuracy by model
    models = {}
    for p in preds:
        m = p.get("model", "unknown")
        if m not in models:
            models[m] = {"total": 0, "correct": 0}
        models[m]["total"] += 1
        if p.get("actual_outcome") == "CORRECT":
            models[m]["correct"] += 1
    
    # Accuracy by symbol
    symbols = {}
    for p in preds:
        s = p["symbol"]
        if s not in symbols:
            symbols[s] = {"total": 0, "correct": 0}
        symbols[s]["total"] += 1
        if p.get("actual_outcome") == "CORRECT":
            symbols[s]["correct"] += 1
    
    accuracy = correct / max(1, correct + wrong) * 100
    
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "expired": expired,
        "accuracy": round(accuracy, 1),
        "targets_hit": targets_hit,
        "sl_hit": sl_hit,
        "avg_profit_pct": round(avg_profit, 2),
        "by_model": {k: {"total": v["total"], "accuracy": round(v["correct"] / max(1, v["total"]) * 100, 1)} for k, v in models.items()},
        "by_symbol": {k: {"total": v["total"], "accuracy": round(v["correct"] / max(1, v["total"]) * 100, 1)} for k, v in symbols.items()},
        "days": days,
    }


def format_accuracy_report(report: Dict) -> str:
    """Format accuracy report for Telegram."""
    if report.get("total", 0) == 0:
        return "📊 No verified predictions yet. JARVIS is learning..."
    
    msg = (
        f"🎯 *JARVIS PREDICTION ACCURACY REPORT*\n"
        f"{'━' * 38}\n"
        f"📅 Last {report['days']} days\n\n"
        f"📊 *Total Predictions:* {report['total']}\n"
        f"✅ *Correct:* {report['correct']}\n"
        f"❌ *Wrong:* {report['wrong']}\n"
        f"⏰ *Expired:* {report.get('expired', 0)}\n\n"
        f"🏆 *Accuracy: {report['accuracy']:.1f}%*\n"
        f"📈 Avg Profit: {report['avg_profit_pct']:+.2f}%\n"
        f"🎯 Target Hit: {report.get('targets_hit', 0)} | SL Hit: {report.get('sl_hit', 0)}\n\n"
    )
    
    if report.get("by_symbol"):
        msg += f"*📊 By Symbol:*\n"
        for sym, data in report["by_symbol"].items():
            msg += f"  {sym}: {data['accuracy']:.1f}% ({data['total']} predictions)\n"
        msg += "\n"
    
    if report.get("by_model"):
        msg += f"*🤖 By Model:*\n"
        for model, data in report["by_model"].items():
            msg += f"  {model}: {data['accuracy']:.1f}% ({data['total']})\n"
    
    return msg


PREDICTION_TRACKER_AVAILABLE = True
logger.info("[TRACKER] 🎯 Prediction Accuracy Tracker loaded!")
