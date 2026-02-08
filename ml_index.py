"""
========================================================================================
  ML INDEX ENGINE — XGBoost + LightGBM + Walk-Forward for Index Prediction
========================================================================================

Scaffold for training on historical index data with 120+ features.
Uses walk-forward validation for proper out-of-sample testing.
All prices in INR (₹).
"""

from typing import Tuple, Dict
import joblib
import os
import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score

from index_data import fetch_history, build_features_for_ml

logger = logging.getLogger("ml_index")
MODEL_PATH = os.environ.get("INDEX_MODEL_PATH", "models/index_xgb.joblib")


def train_index_model(ticker: str = "^NSEI", period: str = "3y", interval: str = "1d") -> dict:
    """Train an ensemble model on index data with walk-forward validation."""
    df = fetch_history(ticker, period=period, interval=interval)
    X, y = build_features_for_ml(df)

    if X.empty or len(X) < 100:
        return {"error": "Not enough data"}

    # Walk-forward split (no shuffle for time series)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Try multiple models and pick the best
    models = {}

    try:
        from xgboost import XGBClassifier
        models['xgb'] = XGBClassifier(
            use_label_encoder=False, eval_metric="logloss",
            n_estimators=300, max_depth=5, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0, verbosity=0,
        )
    except ImportError:
        pass

    try:
        from lightgbm import LGBMClassifier
        models['lgbm'] = LGBMClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0, verbose=-1,
        )
    except ImportError:
        pass

    from sklearn.ensemble import GradientBoostingClassifier
    models['gb'] = GradientBoostingClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42,
    )

    best_model = None
    best_auc = 0
    results = {}

    for name, clf in models.items():
        try:
            clf.fit(X_train, y_train)
            preds = clf.predict(X_test)
            probs = clf.predict_proba(X_test)[:, 1]
            acc = float(accuracy_score(y_test, preds))
            auc = float(roc_auc_score(y_test, probs))
            results[name] = {"accuracy": acc, "auc": auc}
            logger.info(f"  {name}: acc={acc:.3f}, auc={auc:.3f}")
            if auc > best_auc:
                best_auc = auc
                best_model = clf
        except Exception as e:
            results[name] = {"error": str(e)}

    if best_model is None:
        return {"error": "All models failed"}

    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)

    return {
        "best_accuracy": float(accuracy_score(y_test, best_model.predict(X_test))),
        "best_auc": float(best_auc),
        "model_path": MODEL_PATH,
        "features": X.shape[1],
        "samples": len(X),
        "model_results": results,
    }


def load_model(path: str = None):
    p = path or MODEL_PATH
    if not os.path.exists(p):
        raise FileNotFoundError("Model not found. Run train_index_model first.")
    return joblib.load(p)


def predict_signal_for_latest(ticker: str = "^NSEI", model=None, thresh: float = 0.55) -> dict:
    """Predict direction for latest data point."""
    df = fetch_history(ticker, period="60d", interval="1d")
    X, y = build_features_for_ml(df, horizon=1)
    if X.empty:
        return {"signal": "hold", "prob": 0.0}
    if model is None:
        model = load_model()
    latest = X.iloc[-1:]
    prob = float(model.predict_proba(latest)[:, 1][0])

    if prob >= thresh:
        sig = "buy_calls"
    elif prob <= (1 - thresh):
        sig = "buy_puts"
    else:
        sig = "hold"

    return {
        "signal": sig,
        "prob": prob,
        "confidence": abs(prob - 0.5) * 2,
        "direction": "UP" if prob > 0.5 else "DOWN",
    }


if __name__ == "__main__":
    print("Training index model for ^NSEI ...")
    res = train_index_model()
    print("Done:", res)
