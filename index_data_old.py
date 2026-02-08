"""Fetch index OHLCV data and compute technical features for ML."""
from typing import Tuple
import pandas as pd
import numpy as np
import yfinance as yf


def fetch_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical OHLCV for a ticker using yfinance.

    Examples: ticker='^NSEI' (Nifty 50), '^BSESN' (Sensex)
    """
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    df.index.name = "datetime"
    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add a small set of technical indicators used as features."""
    out = df.copy()
    out["return_1"] = out["close"].pct_change()
    out["return_5"] = out["close"].pct_change(5)

    # EMA
    out["ema_8"] = out["close"].ewm(span=8, adjust=False).mean()
    out["ema_21"] = out["close"].ewm(span=21, adjust=False).mean()
    out["ema_diff"] = out["ema_8"] - out["ema_21"]

    # RSI (simple)
    delta = out["close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    roll_up = up.ewm(span=14, adjust=False).mean()
    roll_down = down.ewm(span=14, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-9)
    out["rsi"] = 100.0 - (100.0 / (1.0 + rs))

    # MACD
    ema12 = out["close"].ewm(span=12, adjust=False).mean()
    ema26 = out["close"].ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()

    # ATR (14)
    high_low = out["high"] - out["low"]
    high_close = (out["high"] - out["close"].shift()).abs()
    low_close = (out["low"] - out["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    out["atr14"] = tr.rolling(window=14, min_periods=1).mean()

    # Bollinger Bands
    out["bb_mid"] = out["close"].rolling(window=20).mean()
    out["bb_std"] = out["close"].rolling(window=20).std()
    out["bb_upper"] = out["bb_mid"] + 2 * out["bb_std"]
    out["bb_lower"] = out["bb_mid"] - 2 * out["bb_std"]

    out = out.dropna()
    return out


def build_features_for_ml(df: pd.DataFrame, horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
    """Create features X and binary target y for next-step direction.

    y = 1 => next close > current close (bullish), 0 => bearish or flat
    """
    data = add_technical_indicators(df)
    features = [
        "return_1",
        "return_5",
        "ema_diff",
        "rsi",
        "macd",
        "macd_signal",
        "atr14",
        "bb_mid",
        "bb_upper",
        "bb_lower",
    ]
    data = data.copy()
    data["target_close"] = data["close"].shift(-horizon)
    data = data.dropna()
    X = data[features]
    y = (data["target_close"] > data["close"]).astype(int)
    return X, y
