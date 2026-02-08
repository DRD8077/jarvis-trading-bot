"""Simple ML training and inference for index direction (XGBoost).

This is a scaffold: train on historical index data, save a model, and
provide a predict function that returns probability and a simple signal
(buy_calls / buy_puts / hold) based on probability threshold.
"""
from typing import Tuple
import joblib
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier

from index_data import fetch_history, build_features_for_ml


MODEL_PATH = os.environ.get("INDEX_MODEL_PATH", "models/index_xgb.joblib")


def train_index_model(ticker: str = "^NSEI", period: str = "3y", interval: str = "1d") -> dict:
    df = fetch_history(ticker, period=period, interval=interval)
    X, y = build_features_for_ml(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    clf = XGBClassifier(use_label_encoder=False, eval_metric="logloss", n_estimators=200, max_depth=4)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, preds))
    auc = float(roc_auc_score(y_test, probs))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)

    return {"accuracy": acc, "auc": auc, "model_path": MODEL_PATH}


def load_model(path: str = None):
    p = path or MODEL_PATH
    if not os.path.exists(p):
        raise FileNotFoundError("Model not found. Run train_index_model first.")
    return joblib.load(p)


def predict_signal_for_latest(ticker: str = "^NSEI", model=None, thresh: float = 0.6) -> dict:
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
    return {"signal": sig, "prob": prob}


if __name__ == "__main__":
    print("Training index model for ^NSEI (this may take a few minutes)...")
    res = train_index_model()
    print("Done:", res)
