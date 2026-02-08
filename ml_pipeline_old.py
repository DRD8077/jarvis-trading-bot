import os
import math
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from data_store import get_recent_snapshots

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)


def _safe_get(d: Dict[str, Any], keys: List[str], default=0):
    for k in keys:
        if k in d:
            return d.get(k, default)
    return default


def _extract_features(snapshot: Dict[str, Any]) -> Dict[str, float]:
    calls = snapshot.get("calls", [])
    puts = snapshot.get("puts", [])
    underlying = float(snapshot.get("underlying", 0.0) or 0.0)

    def agg(list_of, keys):
        vals = [float(_safe_get(x, keys, 0) or 0) for x in list_of]
        return float(np.mean(vals)) if vals else 0.0, float(np.sum(vals)) if vals else 0.0

    call_iv_mean, call_oi_sum = agg(calls, ["impliedVolatility", "IV"])
    put_iv_mean, put_oi_sum = agg(puts, ["impliedVolatility", "IV"])
    call_chngoi = float(sum(float(_safe_get(x, ["changeinOpenInterest", "changeInOpenInterest"], 0) or 0) for x in calls))
    put_chngoi = float(sum(float(_safe_get(x, ["changeinOpenInterest", "changeInOpenInterest"], 0) or 0) for x in puts))
    call_vol = float(sum(float(_safe_get(x, ["totalTradedVolume", "totalTradedVolume", "volume"], 0) or 0) for x in calls))
    put_vol = float(sum(float(_safe_get(x, ["totalTradedVolume", "totalTradedVolume", "volume"], 0) or 0) for x in puts))

    features = {
        "underlying": underlying,
        "call_iv_mean": call_iv_mean,
        "put_iv_mean": put_iv_mean,
        "call_oi": call_oi_sum,
        "put_oi": put_oi_sum,
        "call_chng_oi": call_chngoi,
        "put_chng_oi": put_chngoi,
        "call_vol": call_vol,
        "put_vol": put_vol,
        "oi_ratio": (call_oi_sum / (put_oi_sum + 1)) if put_oi_sum >= 0 else 0,
    }
    return features


def build_dataset(symbol: str, lookback: int = 200):
    snaps = get_recent_snapshots(symbol, limit=lookback + 5)
    if not snaps or len(snaps) < 5:
        return None
    # snapshots are returned newest-first; reverse to chronological
    snaps = list(reversed(snaps))
    rows = []
    for i in range(len(snaps) - 1):
        cur = snaps[i]
        nxt = snaps[i + 1]
        features = _extract_features(cur)
        # target: whether underlying increases in next snapshot by threshold
        u0 = float(cur.get("underlying", 0) or 0)
        u1 = float(nxt.get("underlying", 0) or 0)
        if u0 == 0:
            continue
        pct = (u1 - u0) / u0
        # label: 1 if up > 0.0005, 0 otherwise
        label = 1 if pct > 0.0005 else 0
        features["label"] = label
        rows.append(features)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    return df


def train_model(symbol: str, lookback: int = 500) -> Optional[str]:
    df = build_dataset(symbol, lookback=lookback)
    if df is None or df.empty:
        print("Not enough data to train model for", symbol)
        return None
    X = df.drop(columns=["label"]).fillna(0)
    y = df["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print(classification_report(y_test, preds))
    path = os.path.join(MODELS_DIR, f"{symbol}_rf.joblib")
    joblib.dump(clf, path)
    print("Saved model to", path)
    return path


def load_model(symbol: str):
    path = os.path.join(MODELS_DIR, f"{symbol}_rf.joblib")
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def predict_for_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    model = load_model(symbol)
    if model is None:
        return None
    snaps = get_recent_snapshots(symbol, limit=1)
    if not snaps:
        return None
    features = _extract_features(snaps[0])
    X = pd.DataFrame([features]).fillna(0)
    prob = model.predict_proba(X)[0]
    pred = int(model.predict(X)[0])
    return {"prediction": int(pred), "prob_up": float(prob[1]), "prob_down": float(prob[0])}


def explain_prediction(symbol: str, top_k: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Return top_k feature contributions for the latest snapshot using SHAP (TreeExplainer).

    Returns a list of dicts: [{"feature": name, "shap_value": value, "feature_value": v}, ...]
    """
    try:
        import shap
    except Exception:
        return None

    model = load_model(symbol)
    if model is None:
        return None
    snaps = get_recent_snapshots(symbol, limit=1)
    if not snaps:
        return None
    features = _extract_features(snaps[0])
    X = pd.DataFrame([features]).fillna(0)

    try:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X)
        # For binary classification shap_values is [neg, pos]
        if isinstance(shap_vals, list) and len(shap_vals) == 2:
            vals = shap_vals[1][0]
        else:
            vals = shap_vals[0]
        feature_names = X.columns.tolist()
        contributions = []
        import numpy as _np
        for name, v, fv in zip(feature_names, vals, X.iloc[0].tolist()):
            try:
                sv = float(_np.array(v).item())
            except Exception:
                sv = float(_np.array(v).astype(float).tolist()[0]) if hasattr(v, 'astype') else float(v)
            try:
                fv_s = float(_np.array(fv).item())
            except Exception:
                fv_s = float(fv)
            contributions.append({"feature": name, "shap_value": sv, "feature_value": fv_s})
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return contributions[:top_k]
    except Exception as e:
        # surface exception for debugging
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Train for RELIANCE quickly (requires snapshots in DB)
    p = train_model("RELIANCE", lookback=200)
    print("train result:", p)
