"""
AI/ML Index Prediction Engine — Strong predictions for NIFTY/SENSEX options.

Uses ensemble ML (XGBoost + RandomForest + Gradient Boosting) with technical
features from multiple timeframes to predict short-term price direction.
Outputs specific CALL/PUT recommendations with confidence scores.
"""

import math
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

logger = logging.getLogger("ml_predictor")
IST = pytz.timezone("Asia/Kolkata")

# ═══════════════════════════════════════════════════════════
#  FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════

def _compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute technical features from OHLCV data for ML model."""
    import pandas_ta as pdt
    
    feat = pd.DataFrame(index=df.index)
    
    # Price features
    feat['close'] = df['Close']
    feat['returns_1'] = df['Close'].pct_change(1)
    feat['returns_3'] = df['Close'].pct_change(3)
    feat['returns_5'] = df['Close'].pct_change(5)
    feat['returns_10'] = df['Close'].pct_change(10)
    
    # Volatility
    feat['volatility_5'] = df['Close'].pct_change().rolling(5).std()
    feat['volatility_10'] = df['Close'].pct_change().rolling(10).std()
    feat['volatility_20'] = df['Close'].pct_change().rolling(20).std()
    
    # High-Low range
    feat['hl_range'] = (df['High'] - df['Low']) / df['Close']
    feat['hl_range_ma5'] = feat['hl_range'].rolling(5).mean()
    
    # Volume features
    if 'Volume' in df.columns:
        feat['volume_ratio'] = df['Volume'] / df['Volume'].rolling(10).mean()
        feat['volume_change'] = df['Volume'].pct_change()
    
    # RSI
    rsi = pdt.rsi(df['Close'], length=14)
    feat['rsi_14'] = rsi
    rsi7 = pdt.rsi(df['Close'], length=7)
    feat['rsi_7'] = rsi7
    
    # MACD
    macd = pdt.macd(df['Close'])
    if macd is not None and not macd.empty:
        feat['macd'] = macd.iloc[:, 0]
        feat['macd_signal'] = macd.iloc[:, 1] if macd.shape[1] > 1 else 0
        feat['macd_hist'] = macd.iloc[:, 2] if macd.shape[1] > 2 else 0
    
    # EMAs
    feat['ema_9'] = pdt.ema(df['Close'], length=9)
    feat['ema_21'] = pdt.ema(df['Close'], length=21)
    feat['ema_50'] = pdt.ema(df['Close'], length=50)
    feat['ema_cross'] = (feat['ema_9'] - feat['ema_21']) / df['Close']
    
    # Bollinger Bands
    bb = pdt.bbands(df['Close'], length=20)
    if bb is not None and not bb.empty:
        feat['bb_width'] = (bb.iloc[:, 2] - bb.iloc[:, 0]) / bb.iloc[:, 1]
        feat['bb_position'] = (df['Close'] - bb.iloc[:, 0]) / (bb.iloc[:, 2] - bb.iloc[:, 0] + 1e-10)
    
    # ATR
    atr = pdt.atr(df['High'], df['Low'], df['Close'], length=14)
    feat['atr'] = atr
    feat['atr_pct'] = atr / df['Close']
    
    # ADX
    adx = pdt.adx(df['High'], df['Low'], df['Close'], length=14)
    if adx is not None and not adx.empty:
        feat['adx'] = adx.iloc[:, 0]
    
    # Stochastic
    stoch = pdt.stoch(df['High'], df['Low'], df['Close'])
    if stoch is not None and not stoch.empty:
        feat['stoch_k'] = stoch.iloc[:, 0]
        feat['stoch_d'] = stoch.iloc[:, 1] if stoch.shape[1] > 1 else stoch.iloc[:, 0]
    
    # Day of week (cyclical)
    feat['day_sin'] = np.sin(2 * np.pi * df.index.dayofweek / 5)
    feat['day_cos'] = np.cos(2 * np.pi * df.index.dayofweek / 5)
    
    return feat


def _create_labels(df: pd.DataFrame, horizon: int = 1, threshold: float = 0.001) -> pd.Series:
    """Create target labels: 1 = UP (buy call), 0 = DOWN (buy put)."""
    future_returns = df['Close'].pct_change(horizon).shift(-horizon)
    labels = (future_returns > threshold).astype(int)
    return labels


# ═══════════════════════════════════════════════════════════
#  ENSEMBLE ML MODEL
# ═══════════════════════════════════════════════════════════

class IndexPredictor:
    """Ensemble predictor for NIFTY/SENSEX direction."""
    
    def __init__(self):
        self.models = {
            'rf': RandomForestClassifier(
                n_estimators=200, max_depth=8, min_samples_leaf=10,
                random_state=42, n_jobs=-1
            ),
            'gb': GradientBoostingClassifier(
                n_estimators=150, max_depth=5, learning_rate=0.05,
                min_samples_leaf=10, random_state=42
            ),
        }
        
        # Try to add XGBoost
        try:
            from xgboost import XGBClassifier
            self.models['xgb'] = XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.05,
                min_child_weight=10, random_state=42,
                use_label_encoder=False, eval_metric='logloss',
                verbosity=0
            )
        except ImportError:
            logger.warning("XGBoost not available, using RF+GB only")
        
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.train_score = 0.0
    
    def train(self, df: pd.DataFrame, horizon: int = 1) -> Dict[str, Any]:
        """Train ensemble on historical data."""
        features = _compute_features(df)
        labels = _create_labels(df, horizon=horizon)
        
        # Align and drop NaN
        combined = features.copy()
        combined['label'] = labels
        combined.dropna(inplace=True)
        
        if len(combined) < 50:
            return {"error": "Not enough data for training", "samples": len(combined)}
        
        X = combined.drop(columns=['label', 'close'], errors='ignore')
        y = combined['label']
        
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train each model
        scores = {}
        for name, model in self.models.items():
            try:
                cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')
                model.fit(X_scaled, y)
                scores[name] = {
                    'cv_mean': float(cv_scores.mean()),
                    'cv_std': float(cv_scores.std()),
                }
            except Exception as e:
                logger.error(f"Training {name} failed: {e}")
                scores[name] = {'error': str(e)}
        
        self.is_trained = True
        avg_score = np.mean([s['cv_mean'] for s in scores.values() if 'cv_mean' in s])
        self.train_score = avg_score
        
        return {
            "status": "trained",
            "samples": len(combined),
            "features": len(self.feature_names),
            "scores": scores,
            "avg_accuracy": float(avg_score),
        }
    
    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Predict next move direction using trained ensemble.
        
        Returns confidence, direction, and individual model votes.
        """
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        features = _compute_features(df)
        latest = features.iloc[-1:].drop(columns=['close'], errors='ignore')
        
        # Ensure all required features exist
        for col in self.feature_names:
            if col not in latest.columns:
                latest[col] = 0
        latest = latest[self.feature_names]
        latest = latest.fillna(0)
        
        X_scaled = self.scaler.transform(latest)
        
        votes = {}
        probs = []
        
        for name, model in self.models.items():
            try:
                pred = int(model.predict(X_scaled)[0])
                prob = model.predict_proba(X_scaled)[0]
                votes[name] = {
                    'prediction': pred,
                    'prob_up': float(prob[1]) if len(prob) > 1 else float(pred),
                    'prob_down': float(prob[0]) if len(prob) > 1 else float(1 - pred),
                }
                probs.append(float(prob[1]) if len(prob) > 1 else float(pred))
            except Exception as e:
                logger.error(f"Predict {name} failed: {e}")
        
        if not probs:
            return {"error": "All models failed prediction"}
        
        # Ensemble: weighted average
        avg_prob_up = np.mean(probs)
        direction = "UP" if avg_prob_up > 0.5 else "DOWN"
        confidence = abs(avg_prob_up - 0.5) * 2  # 0 to 1
        
        # Feature importance (from RF)
        top_features = []
        if 'rf' in self.models and hasattr(self.models['rf'], 'feature_importances_'):
            imp = self.models['rf'].feature_importances_
            sorted_idx = np.argsort(imp)[::-1][:5]
            for idx in sorted_idx:
                top_features.append({
                    'feature': self.feature_names[idx],
                    'importance': float(imp[idx]),
                })
        
        return {
            "direction": direction,
            "confidence": float(confidence),
            "prob_up": float(avg_prob_up),
            "prob_down": float(1 - avg_prob_up),
            "votes": votes,
            "top_features": top_features,
            "recommendation": "BUY_CE" if direction == "UP" else "BUY_PE",
            "train_accuracy": float(self.train_score),
        }


# ═══════════════════════════════════════════════════════════
#  HIGH-LEVEL PREDICTION API
# ═══════════════════════════════════════════════════════════

# Cache trained models
_model_cache = {}


def predict_index_direction(index_symbol: str, index_name: str = "INDEX") -> Dict[str, Any]:
    """Train (if needed) and predict direction for NIFTY or SENSEX.
    
    Uses 1 year of daily data to train, then predicts next candle direction.
    Returns full prediction with confidence and recommendation.
    """
    import yfinance as yf
    
    cache_key = index_symbol
    
    # Fetch training data
    try:
        df = yf.download(index_symbol, period="1y", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 60:
            return {"error": f"Insufficient data for {index_name}"}
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Normalize columns
        rename_map = {c.lower(): c for c in df.columns}
        for std_name in ['Open', 'High', 'Low', 'Close', 'Volume']:
            low = std_name.lower()
            if low in rename_map and rename_map[low] != std_name:
                df.rename(columns={rename_map[low]: std_name}, inplace=True)
    except Exception as e:
        return {"error": f"Data fetch failed: {e}"}
    
    # Train or use cached model
    predictor = _model_cache.get(cache_key)
    retrain = False
    
    if predictor is None:
        retrain = True
    else:
        # Retrain every 30 min
        last_trained = _model_cache.get(f"{cache_key}_ts", 0)
        import time
        if time.time() - last_trained > 1800:
            retrain = True
    
    if retrain:
        predictor = IndexPredictor()
        train_result = predictor.train(df)
        if "error" in train_result:
            return train_result
        _model_cache[cache_key] = predictor
        import time
        _model_cache[f"{cache_key}_ts"] = time.time()
    
    # Predict
    prediction = predictor.predict(df)
    prediction["index"] = index_name
    prediction["price"] = float(df['Close'].iloc[-1])
    prediction["timestamp"] = datetime.now(IST).strftime("%H:%M:%S IST")
    
    return prediction


def format_ml_prediction(pred: Dict, investment: float = 2000) -> str:
    """Format ML prediction into Telegram message."""
    if "error" in pred:
        return f"❌ ML Prediction Error: {pred['error']}"
    
    index_name = pred.get("index", "INDEX")
    direction = pred.get("direction", "?")
    confidence = pred.get("confidence", 0)
    prob_up = pred.get("prob_up", 0.5)
    prob_down = pred.get("prob_down", 0.5)
    price = pred.get("price", 0)
    rec = pred.get("recommendation", "HOLD")
    votes = pred.get("votes", {})
    top_features = pred.get("top_features", [])
    accuracy = pred.get("train_accuracy", 0)
    
    if direction == "UP":
        emoji = "🟢🚀"
        action = "BUY CALL (CE)"
        bar_green = int(prob_up * 10)
        bar_red = 10 - bar_green
    else:
        emoji = "🔴📉"
        action = "BUY PUT (PE)"
        bar_red = int(prob_down * 10)
        bar_green = 10 - bar_red
    
    bull_bar = "🟩" * bar_green + "⬜" * (10 - bar_green)
    bear_bar = "🟥" * bar_red + "⬜" * (10 - bar_red)
    
    lines = [
        f"🤖🧠 *{index_name} — AI/ML PREDICTION* 🧠🤖",
        f"🔥━━━━━━━━━━━━━━━━━━━━━━━🔥",
        f"💹 *Price:* ₹{price:,.2f}",
        f"⏰ *Time:* {pred.get('timestamp', '')}",
        f"📊 *Model Accuracy:* {accuracy:.1%}",
        f"",
        f"  📈 Bullish: {bull_bar} {prob_up:.0%}",
        f"  📉 Bearish: {bear_bar} {prob_down:.0%}",
        f"",
        f"{emoji} *PREDICTION: {direction}* {emoji}",
        f"🎯 *Confidence:* {confidence:.0%}",
        f"💰 *Action:* {action}",
        f"",
    ]
    
    # Model votes
    if votes:
        lines.append("🗳️ *Model Votes:*")
        model_names = {"rf": "RandomForest", "gb": "GradientBoosting", "xgb": "XGBoost"}
        for name, vote in votes.items():
            display = model_names.get(name, name)
            v_dir = "UP ✅" if vote.get("prediction", 0) == 1 else "DOWN 🔻"
            v_conf = vote.get("prob_up", 0.5)
            lines.append(f"  ┣ {display}: {v_dir} ({v_conf:.0%})")
    
    # Top features
    if top_features:
        lines.append(f"\n📊 *Key Factors:*")
        for f in top_features[:3]:
            lines.append(f"  ┣ {f['feature']}: {f['importance']:.3f}")
    
    lines.extend([
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"⚠️ _AI prediction. Not financial advice. Use SL._",
    ])
    
    return "\n".join(lines)
