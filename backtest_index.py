"""Backtesting harness for index ML strategy (simple next-day entry/exits)."""
import pandas as pd
import numpy as np
from index_data import fetch_history, build_features_for_ml
from ml_index import load_model


def backtest(ticker: str = "^NSEI", model=None, threshold: float = 0.6):
    if model is None:
        model = load_model()
    df = fetch_history(ticker, period="3y", interval="1d")
    X, y = build_features_for_ml(df, horizon=1)
    if X.empty:
        raise RuntimeError("Not enough data for backtest")

    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= threshold).astype(int)

    # Align returns: next-day pct change from open to close
    returns = df.loc[X.index, "close"].pct_change().shift(-1).fillna(0)

    # Strategy: if pred==1 -> go long next day (buy at open, sell at close), else short (inverse)
    strat_ret = []
    for p, r in zip(preds, returns):
        if p == 1:
            strat_ret.append(r)
        else:
            strat_ret.append(-r)

    strat_ret = np.array(strat_ret)
    cum = (1 + strat_ret).cumprod() - 1

    results = {
        "total_return": float(cum[-1]) if len(cum) else 0.0,
        "mean_daily": float(np.nanmean(strat_ret)),
        "std_daily": float(np.nanstd(strat_ret)),
        "sharpe": float(np.nanmean(strat_ret) / (np.nanstd(strat_ret) + 1e-9) * np.sqrt(252)),
        "win_rate": float((strat_ret > 0).mean()),
    }
    return results


if __name__ == "__main__":
    m = load_model()
    print("Backtesting NIFTY...")
    r = backtest("^NSEI", model=m)
    print(r)
