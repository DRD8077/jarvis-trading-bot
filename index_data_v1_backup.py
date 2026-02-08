"""
========================================================================================
  ADVANCED FEATURE ENGINEERING ENGINE — 120+ ML Features | INR Market Focused
========================================================================================

Computes exhaustive feature sets for ML models:
  - Price action features (returns, gaps, range expansion)
  - Multi-period technical indicators
  - Candlestick pattern encoding
  - Volume profile analysis
  - Volatility regime detection
  - Market microstructure features
  - Calendar / seasonality features (NSE expiry, FII flows proxy)
  - Lag features (autoregressive)
  - Cross-asset correlation features (Gold, USD/INR, DXY proxy)
  
All designed for Indian market (NSE/BSE) in INR.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional, List
import logging

logger = logging.getLogger("advanced_features")


# ═══════════════════════════════════════════════════════════════════════════
#  DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════

def fetch_history(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical OHLCV for a ticker using yfinance. INR prices."""
    import yfinance as yf
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Adj Close": "adj_close", "Volume": "volume",
    })
    # Also handle lower-case source
    cols_lower = {c.strip().lower(): c for c in df.columns}
    for std in ["open", "high", "low", "close", "volume"]:
        if std not in df.columns and std in cols_lower:
            df = df.rename(columns={cols_lower[std]: std})
    df.index.name = "datetime"
    return df


def fetch_cross_asset_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """Fetch correlated asset data for cross-asset features."""
    assets = {
        "gold": "GC=F",
        "crude": "CL=F",
        "dxy": "DX-Y.NYB",
        "usdinr": "USDINR=X",
        "vix": "^VIX",
        "us_sp500": "^GSPC",
        "nikkei": "^N225",
    }
    data = {}
    for name, ticker in assets.items():
        try:
            df = fetch_history(ticker, period=period)
            data[name] = df
        except Exception:
            pass
    return data


# ═══════════════════════════════════════════════════════════════════════════
#  CORE TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════════════════

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add comprehensive technical indicators as columns."""
    out = df.copy()

    # Returns
    for p in [1, 2, 3, 5, 10, 20]:
        out[f"return_{p}"] = out["close"].pct_change(p)

    # Log returns
    out["log_return_1"] = np.log(out["close"] / out["close"].shift(1))

    # Gap (overnight)
    out["gap"] = (out["open"] - out["close"].shift(1)) / out["close"].shift(1)

    # Range features
    out["hl_range"] = (out["high"] - out["low"]) / out["close"]
    out["oc_range"] = (out["close"] - out["open"]) / out["close"]
    out["upper_wick_pct"] = (out["high"] - out[["open", "close"]].max(axis=1)) / (out["high"] - out["low"] + 1e-10)
    out["lower_wick_pct"] = (out[["open", "close"]].min(axis=1) - out["low"]) / (out["high"] - out["low"] + 1e-10)
    out["body_pct"] = abs(out["close"] - out["open"]) / (out["high"] - out["low"] + 1e-10)

    # EMAs
    for span in [5, 8, 13, 21, 34, 50, 100, 200]:
        out[f"ema_{span}"] = out["close"].ewm(span=span, adjust=False).mean()

    # EMA crossovers
    out["ema_8_21_cross"] = out["ema_8"] - out["ema_21"]
    out["ema_13_34_cross"] = out["ema_13"] - out["ema_34"]
    out["ema_50_200_cross"] = out["ema_50"] - out["ema_200"]

    # Price relative to EMAs
    for span in [8, 21, 50, 200]:
        out[f"price_vs_ema_{span}"] = (out["close"] - out[f"ema_{span}"]) / out[f"ema_{span}"]

    # RSI (multi-period)
    for period in [7, 14, 21]:
        delta = out["close"].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        roll_up = up.ewm(span=period, adjust=False).mean()
        roll_down = down.ewm(span=period, adjust=False).mean()
        rs = roll_up / (roll_down + 1e-9)
        out[f"rsi_{period}"] = 100.0 - (100.0 / (1.0 + rs))

    # Stochastic %K, %D
    for period in [14, 21]:
        low_min = out["low"].rolling(period).min()
        high_max = out["high"].rolling(period).max()
        out[f"stoch_k_{period}"] = 100 * (out["close"] - low_min) / (high_max - low_min + 1e-10)
        out[f"stoch_d_{period}"] = out[f"stoch_k_{period}"].rolling(3).mean()

    # MACD
    ema12 = out["close"].ewm(span=12, adjust=False).mean()
    ema26 = out["close"].ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    # ATR (multi-period)
    for period in [7, 14, 21]:
        high_low = out["high"] - out["low"]
        high_close = (out["high"] - out["close"].shift()).abs()
        low_close = (out["low"] - out["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        out[f"atr_{period}"] = tr.rolling(window=period, min_periods=1).mean()
        out[f"atr_pct_{period}"] = out[f"atr_{period}"] / out["close"]

    # Bollinger Bands
    for period in [20, 50]:
        mid = out["close"].rolling(period).mean()
        std = out["close"].rolling(period).std()
        out[f"bb_upper_{period}"] = mid + 2 * std
        out[f"bb_lower_{period}"] = mid - 2 * std
        out[f"bb_width_{period}"] = (out[f"bb_upper_{period}"] - out[f"bb_lower_{period}"]) / mid
        out[f"bb_pct_{period}"] = (out["close"] - out[f"bb_lower_{period}"]) / (out[f"bb_upper_{period}"] - out[f"bb_lower_{period}"] + 1e-10)

    # Volatility
    for period in [5, 10, 20, 60]:
        out[f"volatility_{period}"] = out["close"].pct_change().rolling(period).std() * np.sqrt(252)

    # Momentum
    for period in [5, 10, 20]:
        out[f"momentum_{period}"] = out["close"] / out["close"].shift(period) - 1

    # Williams %R
    for period in [14]:
        high_max = out["high"].rolling(period).max()
        low_min = out["low"].rolling(period).min()
        out[f"willr_{period}"] = -100 * (high_max - out["close"]) / (high_max - low_min + 1e-10)

    # CCI (Commodity Channel Index)
    tp = (out["high"] + out["low"] + out["close"]) / 3
    for period in [14, 20]:
        sma_tp = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        out[f"cci_{period}"] = (tp - sma_tp) / (0.015 * mad + 1e-10)

    # ADX (simplified)
    plus_dm = out["high"].diff()
    minus_dm = -out["low"].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr_14 = out["atr_14"] * 14  # approximate
    out["plus_di"] = 100 * (plus_dm.ewm(span=14).mean() / (tr_14 + 1e-10))
    out["minus_di"] = 100 * (minus_dm.ewm(span=14).mean() / (tr_14 + 1e-10))
    dx = 100 * abs(out["plus_di"] - out["minus_di"]) / (out["plus_di"] + out["minus_di"] + 1e-10)
    out["adx"] = dx.ewm(span=14).mean()

    # Volume features
    if "volume" in out.columns:
        for period in [5, 10, 20]:
            out[f"vol_sma_{period}"] = out["volume"].rolling(period).mean()
            out[f"vol_ratio_{period}"] = out["volume"] / (out[f"vol_sma_{period}"] + 1)
        out["vol_change"] = out["volume"].pct_change()

        # OBV (On Balance Volume)
        obv = [0]
        for i in range(1, len(out)):
            if out["close"].iloc[i] > out["close"].iloc[i - 1]:
                obv.append(obv[-1] + out["volume"].iloc[i])
            elif out["close"].iloc[i] < out["close"].iloc[i - 1]:
                obv.append(obv[-1] - out["volume"].iloc[i])
            else:
                obv.append(obv[-1])
        out["obv"] = obv
        out["obv_sma"] = pd.Series(obv, index=out.index).rolling(20).mean()

        # VWAP (cumulative)
        tp = (out["high"] + out["low"] + out["close"]) / 3
        out["vwap"] = (tp * out["volume"]).cumsum() / out["volume"].cumsum()
        out["price_vs_vwap"] = (out["close"] - out["vwap"]) / (out["vwap"] + 1e-10)

        # MFI
        pos_mf = tp * out["volume"] * (tp > tp.shift(1)).astype(float)
        neg_mf = tp * out["volume"] * (tp < tp.shift(1)).astype(float)
        mf_ratio = pos_mf.rolling(14).sum() / (neg_mf.rolling(14).sum() + 1e-10)
        out["mfi"] = 100 - (100 / (1 + mf_ratio))

    # Calendar / seasonality
    if hasattr(out.index, "dayofweek"):
        out["day_of_week"] = out.index.dayofweek
        out["day_sin"] = np.sin(2 * np.pi * out.index.dayofweek / 5)
        out["day_cos"] = np.cos(2 * np.pi * out.index.dayofweek / 5)
        out["month_sin"] = np.sin(2 * np.pi * out.index.month / 12)
        out["month_cos"] = np.cos(2 * np.pi * out.index.month / 12)
        out["week_of_year"] = out.index.isocalendar().week.values.astype(int)

        # NSE Monthly Expiry proximity (last Thursday of month)
        # Approximation: days until month end
        out["days_to_month_end"] = pd.Series(
            [(pd.Timestamp(d.year, d.month, 1) + pd.offsets.MonthEnd(1) - d).days for d in out.index],
            index=out.index,
        )
        out["near_expiry"] = (out["days_to_month_end"] <= 3).astype(int)

    # Lag features (autoregressive)
    for lag in [1, 2, 3, 5, 10]:
        out[f"close_lag_{lag}"] = out["close"].shift(lag)
        out[f"return_lag_{lag}"] = out["return_1"].shift(lag) if "return_1" in out.columns else 0
        out[f"volume_lag_{lag}"] = out["volume"].shift(lag) if "volume" in out.columns else 0

    # Rolling statistics
    for window in [5, 10, 20]:
        out[f"close_rolling_mean_{window}"] = out["close"].rolling(window).mean()
        out[f"close_rolling_std_{window}"] = out["close"].rolling(window).std()
        out[f"close_rolling_skew_{window}"] = out["close"].pct_change().rolling(window).skew()
        out[f"close_rolling_kurt_{window}"] = out["close"].pct_change().rolling(window).kurt()

    out = out.dropna()
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  CROSS-ASSET FEATURES
# ═══════════════════════════════════════════════════════════════════════════

def add_cross_asset_features(df: pd.DataFrame, cross_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Add cross-asset correlation features (Gold, USD/INR, Oil, VIX, etc.)."""
    out = df.copy()

    for name, cdf in cross_data.items():
        if cdf is None or cdf.empty:
            continue
        # Align on date index
        try:
            cross_close = cdf["close"].reindex(out.index, method="ffill")
            out[f"{name}_return_1"] = cross_close.pct_change(1)
            out[f"{name}_return_5"] = cross_close.pct_change(5)
            # Rolling correlation with NIFTY
            out[f"{name}_corr_20"] = out["return_1"].rolling(20).corr(out[f"{name}_return_1"])
        except Exception:
            pass

    return out


# ═══════════════════════════════════════════════════════════════════════════
#  CANDLESTICK PATTERN ENCODING
# ═══════════════════════════════════════════════════════════════════════════

def add_candle_pattern_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode candlestick patterns as binary features for ML models."""
    out = df.copy()

    o = out["open"] if "open" in out.columns else out["Open"]
    h = out["high"] if "high" in out.columns else out["High"]
    l = out["low"] if "low" in out.columns else out["Low"]
    c = out["close"] if "close" in out.columns else out["Close"]

    body = abs(c - o)
    tr = h - l + 1e-10
    bp = body / tr
    uw = h - pd.concat([o, c], axis=1).max(axis=1)
    lw = pd.concat([o, c], axis=1).min(axis=1) - l

    # Doji
    out["pat_doji"] = (bp < 0.05).astype(int)
    # Hammer
    out["pat_hammer"] = ((lw >= 2 * body) & (uw < 0.3 * body) & (c > o)).astype(int)
    # Shooting star
    out["pat_shooting_star"] = ((uw >= 2 * body) & (lw < 0.3 * body) & (c < o)).astype(int)
    # Marubozu
    out["pat_bull_marubozu"] = ((bp > 0.9) & (c > o)).astype(int)
    out["pat_bear_marubozu"] = ((bp > 0.9) & (c < o)).astype(int)
    # Engulfing
    prev_o = o.shift(1)
    prev_c = c.shift(1)
    prev_body = abs(prev_c - prev_o)
    out["pat_bull_engulfing"] = ((prev_c < prev_o) & (c > o) & (o <= prev_c) & (c >= prev_o) & (body > prev_body)).astype(int)
    out["pat_bear_engulfing"] = ((prev_c > prev_o) & (c < o) & (o >= prev_c) & (c <= prev_o) & (body > prev_body)).astype(int)
    # Large body
    out["pat_large_body"] = (bp > 0.7).astype(int)
    # High wick
    out["pat_high_wick"] = ((uw + lw) > 0.7 * tr).astype(int)

    return out


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD FEATURES FOR ML
# ═══════════════════════════════════════════════════════════════════════════

def build_features_for_ml(df: pd.DataFrame, horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
    """Create features X and binary target y for next-step direction prediction.
    y = 1 => next close > current close (bullish), 0 => bearish/flat
    """
    data = add_technical_indicators(df)
    data = add_candle_pattern_features(data)

    # Drop raw price columns (keep derived features only)
    exclude_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    # Also exclude lag raw cols
    feature_cols = [c for c in data.columns if c not in exclude_cols
                    and not c.startswith("close_lag_") and not c.startswith("volume_lag_")]

    data = data.copy()
    data["target_close"] = data["close"].shift(-horizon)
    data = data.dropna(subset=["target_close"])

    X = data[feature_cols].copy()
    y = (data["target_close"] > data["close"]).astype(int)

    # Drop any remaining NaN columns
    X = X.dropna(axis=1, how="all")
    # Fill remaining NaN with 0
    X = X.fillna(0)

    # Align y
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    return X, y


def build_regression_features(df: pd.DataFrame, horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
    """Build features for regression (predict exact return %)."""
    data = add_technical_indicators(df)
    data = add_candle_pattern_features(data)

    exclude_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    feature_cols = [c for c in data.columns if c not in exclude_cols
                    and not c.startswith("close_lag_") and not c.startswith("volume_lag_")]

    data = data.copy()
    data["future_return"] = data["close"].pct_change(horizon).shift(-horizon)
    data = data.dropna(subset=["future_return"])

    X = data[feature_cols].copy().fillna(0)
    y = data["future_return"]

    common_idx = X.index.intersection(y.index)
    return X.loc[common_idx], y.loc[common_idx]


if __name__ == "__main__":
    print("Fetching NIFTY 50 data...")
    df = fetch_history("^NSEI", period="2y")
    print(f"Raw data: {len(df)} rows")

    X, y = build_features_for_ml(df, horizon=1)
    print(f"Features: {X.shape[1]} columns, {len(X)} samples")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    print(f"\nTop feature columns:\n{list(X.columns[:20])}")
