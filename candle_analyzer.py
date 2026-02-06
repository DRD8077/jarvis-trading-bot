"""
Candlestick pattern recognition and technical analysis for NIFTY/SENSEX indices.
Uses ta-lib alternatives and pattern-based algorithms for AI-driven buy/sell signals.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import ta
import yfinance as yf


def fetch_index_candles(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLC (candle) data for NIFTY or SENSEX from Yahoo Finance.
    
    symbol: '^NSEI' for NIFTY, '^BSESN' for SENSEX
    period: time period ('60d', '1y', etc.)
    interval: '1d' (daily), '1h' (hourly), '5m' (5-min), etc.
    
    Returns DataFrame with OHLCV data or None on failure.
    """
    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        if data is None or data.empty:
            return None
        
        # yfinance returns multi-level columns (metric, ticker), flatten them
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Normalize column names
        data.columns = [col.strip().lower() for col in data.columns]
        
        # Rename to expected format
        rename_map = {
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'adj close': 'Adj Close'
        }
        data.rename(columns=rename_map, inplace=True)
        
        # Ensure required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(c in data.columns for c in required):
            print(f"Missing required columns. Have: {list(data.columns)}")
            return None
        
        return data.sort_index()
    except Exception as e:
        print(f"Failed to fetch candles for {symbol}: {e}")
        return None


def detect_candlestick_patterns(df: pd.DataFrame) -> Dict[str, any]:
    """Detect classic Japanese candlestick patterns in OHLCV data.
    
    Returns dict with pattern names and count/strength.
    """
    if df is None or len(df) < 3:
        return {}
    
    patterns = {}
    ohlc_vals = df[['Open', 'High', 'Low', 'Close']].tail(10).values  # Get numpy array
    
    # Extract scalar values for comparison
    for i in range(len(ohlc_vals)):
        try:
            o, h, l, c = float(ohlc_vals[i][0]), float(ohlc_vals[i][1]), float(ohlc_vals[i][2]), float(ohlc_vals[i][3])
        except (ValueError, IndexError):
            continue
        
        body = abs(c - o)
        total_range = h - l
        
        if total_range == 0:
            continue
        
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        
        # Hammer (bullish reversal)
        if body > 0 and lower_wick > 2 * body and upper_wick < 0.5 * body:
            patterns['hammer'] = patterns.get('hammer', 0) + 1
        
        # Hanging man (bearish)
        if body > 0 and lower_wick > 2 * body and upper_wick < 0.5 * body and c < o:
            patterns['hanging_man'] = patterns.get('hanging_man', 0) + 1
        
        # Engulfing (bullish if current closes higher than prev open)
        if i > 0:
            try:
                prev_o, prev_c = float(ohlc_vals[i-1][0]), float(ohlc_vals[i-1][3])
                if c > prev_o and o < prev_c:
                    patterns['bullish_engulfing'] = patterns.get('bullish_engulfing', 0) + 1
            except (ValueError, IndexError):
                pass
        
        # Doji (small body, long wicks)
        if body < 0.1 * total_range and upper_wick > 0.4 * total_range:
            patterns['doji'] = patterns.get('doji', 0) + 1
    
    return patterns


def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate key technical indicators for NIFTY/SENSEX.
    
    Returns dict with RSI, MACD, SMA, Bollinger Bands, ATR, etc.
    """
    if df is None or len(df) < 20:
        return {}
    
    indicators = {}
    
    try:
        import pandas_ta as pdt
        
        # Current price and price change (get these first as they're most critical)
        indicators['price'] = float(df['Close'].iloc[-1])
        indicators['price_change'] = float(df['Close'].iloc[-1] - df['Close'].iloc[-2]) if len(df) > 1 else 0
        indicators['price_change_pct'] = (indicators['price_change'] / df['Close'].iloc[-2] * 100) if df['Close'].iloc[-2] != 0 else 0
        indicators['volume'] = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0
        
        # RSI (14-period)
        rsi = pdt.rsi(df['Close'], length=14)
        indicators['rsi'] = float(rsi.iloc[-1]) if rsi is not None and not rsi.empty else 50.0
        
        # SMA (50-day and 200-day)
        sma50 = pdt.sma(df['Close'], length=50)
        indicators['sma50'] = float(sma50.iloc[-1]) if sma50 is not None and not sma50.empty else indicators['price']
        
        sma200 = pdt.sma(df['Close'], length=200)
        indicators['sma200'] = float(sma200.iloc[-1]) if sma200 is not None and not sma200.empty else indicators['price']
        
        # Bollinger Bands
        bb = pdt.bbands(df['Close'], length=20)
        if bb is not None and not bb.empty:
            try:
                indicators['bb_upper'] = float(bb.iloc[-1, 2])
                indicators['bb_middle'] = float(bb.iloc[-1, 1])
                indicators['bb_lower'] = float(bb.iloc[-1, 0])
            except (IndexError, ValueError):
                indicators['bb_upper'] = indicators['price'] + 100
                indicators['bb_middle'] = indicators['price']
                indicators['bb_lower'] = indicators['price'] - 100
        
        # ATR (Average True Range)
        atr = pdt.atr(df['High'], df['Low'], df['Close'], length=14)
        indicators['atr'] = float(atr.iloc[-1]) if atr is not None and not atr.empty else 0.0
        
        # ADX (trend strength)
        adx = pdt.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx is not None and not adx.empty:
            try:
                indicators['adx'] = float(adx.iloc[-1, 0])
            except (IndexError, TypeError):
                indicators['adx'] = float(adx.iloc[-1])
        else:
            indicators['adx'] = 20.0
        
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        # Return sensible defaults if calculation fails
        if 'price' not in indicators:
            try:
                indicators['price'] = float(df['Close'].iloc[-1])
            except:
                indicators['price'] = 0.0
    
    return indicators


def analyze_index(symbol: str, symbol_name: str = "INDEX") -> Dict[str, any]:
    """Comprehensive AI analysis of NIFTY/SENSEX with candlestick patterns, 
    technical indicators, and algorithmic buy/sell signals.
    
    Returns dict with analysis, patterns, indicators, and signal.
    """
    result = {
        "symbol": symbol_name,
        "signal": "HOLD",
        "confidence": 0.0,
        "patterns": {},
        "indicators": {},
        "analysis": "",
        "reasons": []
    }
    
    # Fetch daily candles
    df = fetch_index_candles(symbol, period="180d", interval="1d")
    if df is None or df.empty:
        result["analysis"] = "Failed to fetch candle data"
        return result
    
    # Detect candlestick patterns
    patterns = detect_candlestick_patterns(df)
    result["patterns"] = patterns
    
    # Calculate technical indicators
    indicators = calculate_technical_indicators(df)
    result["indicators"] = indicators
    
    # AI-driven decision algorithm
    signal_score = 0.0  # -1 (strong sell) to +1 (strong buy)
    
    # RSI analysis
    rsi = indicators.get('rsi', 50)
    if rsi > 70:
        signal_score -= 0.2
        result["reasons"].append(f"RSI {rsi:.1f} - overbought")
    elif rsi < 30:
        signal_score += 0.2
        result["reasons"].append(f"RSI {rsi:.1f} - oversold (bullish)")
    elif rsi > 55:
        signal_score += 0.1
        result["reasons"].append(f"RSI {rsi:.1f} - uptrend momentum")
    elif rsi < 45:
        signal_score -= 0.1
        result["reasons"].append(f"RSI {rsi:.1f} - downtrend momentum")
    
    # SMA crossover analysis
    price = indicators.get('price', 0)
    sma50 = indicators.get('sma50', 0)
    sma200 = indicators.get('sma200', 0)
    
    if sma50 > sma200 and price > sma50:
        signal_score += 0.25
        result["reasons"].append("Golden cross + price above SMA50 (bullish)")
    elif sma50 < sma200 and price < sma50:
        signal_score -= 0.25
        result["reasons"].append("Death cross + price below SMA50 (bearish)")
    
    # Bollinger Bands analysis
    bb_upper = indicators.get('bb_upper', 0)
    bb_lower = indicators.get('bb_lower', 0)
    bb_middle = indicators.get('bb_middle', 0)
    
    if price > bb_upper:
        signal_score -= 0.15
        result["reasons"].append("Price above Bollinger upper band (overbought)")
    elif price < bb_lower:
        signal_score += 0.15
        result["reasons"].append("Price below Bollinger lower band (oversold)")
    
    # Candlestick pattern signals
    bullish_patterns = patterns.get('hammer', 0) + patterns.get('bullish_engulfing', 0)
    bearish_patterns = patterns.get('hanging_man', 0)
    
    if bullish_patterns > 0:
        signal_score += 0.15
        result["reasons"].append(f"Bullish patterns detected: {bullish_patterns}")
    if bearish_patterns > 0:
        signal_score -= 0.15
        result["reasons"].append(f"Bearish patterns detected: {bearish_patterns}")
    
    # ADX trend strength
    adx = indicators.get('adx', 20)
    if adx > 25:
        result["reasons"].append(f"Strong trend (ADX {adx:.1f})")
        if signal_score > 0:
            signal_score += 0.1
        else:
            signal_score -= 0.1
    else:
        result["reasons"].append(f"Weak trend (ADX {adx:.1f})")
    
    # Price momentum
    price_change_pct = indicators.get('price_change_pct', 0)
    if price_change_pct > 1:
        signal_score += 0.1
        result["reasons"].append(f"Positive momentum (+{price_change_pct:.2f}%)")
    elif price_change_pct < -1:
        signal_score -= 0.1
        result["reasons"].append(f"Negative momentum ({price_change_pct:.2f}%)")
    
    # Final signal determination
    signal_score = max(-1, min(1, signal_score))  # Clamp to [-1, 1]
    confidence = abs(signal_score)
    
    if signal_score >= 0.4:
        result["signal"] = "BUY"
        result["confidence"] = confidence
    elif signal_score <= -0.4:
        result["signal"] = "SELL"
        result["confidence"] = confidence
    else:
        result["signal"] = "HOLD"
        result["confidence"] = max(0.3, 1 - confidence)
    
    # Format analysis message
    analysis_lines = [
        f"📊 {symbol_name} Analysis",
        f"Price: ₹{price:.2f}",
        f"Signal: {result['signal']} (confidence: {confidence:.2%})",
        "",
        "Indicators:",
        f"  RSI(14): {rsi:.1f}",
        f"  SMA50/200: {sma50:.2f}/{sma200:.2f}",
        f"  ADX: {adx:.1f}",
        f"  ATR: {indicators.get('atr', 0):.2f}",
    ]
    
    if patterns:
        analysis_lines.append(f"Patterns: {', '.join(patterns.keys())}")
    
    analysis_lines.extend(result["reasons"])
    result["analysis"] = "\n".join(analysis_lines)
    
    return result


if __name__ == "__main__":
    # Test with NIFTY
    nifty = analyze_index("^NSEI", "NIFTY 50")
    print(nifty["analysis"])
    print("\n---\n")
    
    # Test with SENSEX
    sensex = analyze_index("^BSESN", "SENSEX")
    print(sensex["analysis"])
