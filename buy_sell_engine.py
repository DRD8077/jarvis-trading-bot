"""
🔥 SUPER POWERFUL BUY/SELL SIGNAL ENGINE 🔥
Advanced Buy/Sell Indicator for Indian Stocks (NIFTY/SENSEX) + Crypto
Combines: RSI, MACD, EMA Crossovers, Supertrend, Bollinger Bands,
          Volume Analysis, Candlestick Patterns, ADX, Stochastic, VWAP
Generates clear BUY/SELL/HOLD signals with entry, stop-loss, target in ₹
Auto-alerts when strong signals trigger

Author: JARVIS Trading Engine
"""

import os
import json
import time
import logging
import sqlite3
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SIGNAL TYPES & DATA CLASSES
# ═══════════════════════════════════════════════════════════════

class SignalType(Enum):
    STRONG_BUY = "🟢🟢 STRONG BUY"
    BUY = "🟢 BUY"
    WEAK_BUY = "🟡 WEAK BUY"
    HOLD = "⚪ HOLD"
    WEAK_SELL = "🟡 WEAK SELL"
    SELL = "🔴 SELL"
    STRONG_SELL = "🔴🔴 STRONG SELL"

class MarketType(Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    INDEX = "index"
    GLOBAL = "global"

@dataclass
class TechnicalIndicator:
    """Single technical indicator result"""
    name: str
    value: float
    signal: str  # "BUY", "SELL", "NEUTRAL"
    strength: float  # 0-100
    description: str
    description_hi: str  # Hindi description

@dataclass
class BuySellSignal:
    """Complete buy/sell signal with all analysis"""
    symbol: str
    market_type: MarketType
    signal_type: SignalType
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float
    risk_reward: float
    indicators: List[TechnicalIndicator]
    buy_score: int  # Number of buy indicators
    sell_score: int  # Number of sell indicators
    neutral_score: int
    trend: str  # "BULLISH", "BEARISH", "SIDEWAYS"
    volume_signal: str
    candle_pattern: str
    timestamp: str
    summary_en: str
    summary_hi: str  # Hindi summary
    alerts: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════
# TECHNICAL INDICATOR CALCULATIONS
# ═══════════════════════════════════════════════════════════════

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate RSI (Relative Strength Index)"""
    if len(closes) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    """Calculate MACD, Signal Line, and Histogram"""
    if len(closes) < slow + signal:
        return 0, 0, 0
    
    def ema(data, period):
        if len(data) < period:
            return data[-1] if data else 0
        multiplier = 2 / (period + 1)
        ema_val = sum(data[:period]) / period
        for price in data[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val
    
    # Calculate for last signal+5 periods for accuracy
    macd_line = []
    for i in range(slow, len(closes) + 1):
        fast_ema = ema(closes[:i], fast)
        slow_ema = ema(closes[:i], slow)
        macd_line.append(fast_ema - slow_ema)
    
    if len(macd_line) < signal:
        return macd_line[-1] if macd_line else 0, 0, 0
    
    signal_line = ema(macd_line, signal)
    histogram = macd_line[-1] - signal_line
    
    return round(macd_line[-1], 4), round(signal_line, 4), round(histogram, 4)

def calculate_ema(closes: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(closes) < period:
        return closes[-1] if closes else 0
    
    multiplier = 2 / (period + 1)
    ema_val = sum(closes[:period]) / period
    for price in closes[period:]:
        ema_val = (price - ema_val) * multiplier + ema_val
    return round(ema_val, 2)

def calculate_sma(closes: List[float], period: int) -> float:
    """Calculate Simple Moving Average"""
    if len(closes) < period:
        return sum(closes) / len(closes) if closes else 0
    return round(sum(closes[-period:]) / period, 2)

def calculate_bollinger_bands(closes: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """Calculate Bollinger Bands (upper, middle, lower)"""
    if len(closes) < period:
        return 0, 0, 0
    
    sma = sum(closes[-period:]) / period
    variance = sum((x - sma) ** 2 for x in closes[-period:]) / period
    std = variance ** 0.5
    
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    
    return round(upper, 2), round(sma, 2), round(lower, 2)

def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
    """Calculate Stochastic Oscillator (%K, %D)"""
    if len(closes) < k_period:
        return 50, 50
    
    k_values = []
    for i in range(k_period - 1, len(closes)):
        highest = max(highs[i-k_period+1:i+1])
        lowest = min(lows[i-k_period+1:i+1])
        if highest == lowest:
            k_values.append(50)
        else:
            k_values.append(((closes[i] - lowest) / (highest - lowest)) * 100)
    
    k = k_values[-1] if k_values else 50
    d = sum(k_values[-d_period:]) / min(d_period, len(k_values)) if k_values else 50
    
    return round(k, 2), round(d, 2)

def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Tuple[float, float, float]:
    """Calculate ADX, +DI, -DI"""
    if len(closes) < period + 1:
        return 25, 50, 50
    
    plus_dm = []
    minus_dm = []
    tr_list = []
    
    for i in range(1, len(closes)):
        high_diff = highs[i] - highs[i-1]
        low_diff = lows[i-1] - lows[i]
        
        plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
        minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
        
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return 25, 50, 50
    
    atr = sum(tr_list[-period:]) / period
    if atr == 0:
        return 25, 50, 50
    
    plus_di = (sum(plus_dm[-period:]) / period / atr) * 100
    minus_di = (sum(minus_dm[-period:]) / period / atr) * 100
    
    if plus_di + minus_di == 0:
        return 25, 50, 50
    
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    adx = dx  # Simplified
    
    return round(adx, 2), round(plus_di, 2), round(minus_di, 2)

def calculate_supertrend(highs: List[float], lows: List[float], closes: List[float], period: int = 10, multiplier: float = 3.0) -> Tuple[float, str]:
    """Calculate Supertrend indicator"""
    if len(closes) < period + 1:
        return closes[-1] if closes else 0, "NEUTRAL"
    
    # Calculate ATR
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return closes[-1], "NEUTRAL"
    
    atr = sum(tr_list[-period:]) / period
    
    # Calculate bands
    hl2 = (highs[-1] + lows[-1]) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Determine trend
    if closes[-1] > upper_band:
        return round(lower_band, 2), "BULLISH"
    elif closes[-1] < lower_band:
        return round(upper_band, 2), "BEARISH"
    else:
        return round((upper_band + lower_band) / 2, 2), "NEUTRAL"

def calculate_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
    """Calculate Volume Weighted Average Price"""
    if not volumes or not closes or len(closes) != len(volumes):
        return closes[-1] if closes else 0
    
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
    total_volume = sum(volumes)
    if total_volume == 0:
        return closes[-1]
    
    vwap = sum(tp * v for tp, v in zip(typical_prices, volumes)) / total_volume
    return round(vwap, 2)

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate Average True Range"""
    if len(closes) < 2:
        return 0
    
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return sum(tr_list) / len(tr_list) if tr_list else 0
    
    return round(sum(tr_list[-period:]) / period, 2)

def detect_volume_signal(volumes: List[float]) -> Tuple[str, float]:
    """Detect volume-based signals"""
    if len(volumes) < 20:
        return "NORMAL", 50
    
    avg_vol = sum(volumes[-20:]) / 20
    current_vol = volumes[-1]
    
    if avg_vol == 0:
        return "NORMAL", 50
    
    ratio = current_vol / avg_vol
    
    if ratio > 3.0:
        return "EXTREME_VOLUME", 95
    elif ratio > 2.0:
        return "HIGH_VOLUME", 80
    elif ratio > 1.5:
        return "ABOVE_AVG", 65
    elif ratio > 0.7:
        return "NORMAL", 50
    elif ratio > 0.3:
        return "LOW_VOLUME", 30
    else:
        return "DRIED_UP", 15

def detect_candle_pattern_signal(opens: List[float], highs: List[float], lows: List[float], closes: List[float]) -> Tuple[str, str, float]:
    """Detect candlestick pattern and its signal"""
    if len(closes) < 3:
        return "No Pattern", "NEUTRAL", 0
    
    o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
    po, ph, pl, pc = opens[-2], highs[-2], lows[-2], closes[-2]
    
    body = abs(c - o)
    total_range = h - l if h != l else 0.001
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    body_pct = body / total_range if total_range > 0 else 0
    
    # Bullish Engulfing
    if pc < po and c > o and c > po and o < pc:
        return "Bullish Engulfing 🐂", "BUY", 85
    
    # Bearish Engulfing
    if pc > po and c < o and c < po and o > pc:
        return "Bearish Engulfing 🐻", "SELL", 85
    
    # Hammer
    if lower_wick > body * 2 and upper_wick < body * 0.5 and body_pct < 0.4:
        return "Hammer 🔨", "BUY", 75
    
    # Shooting Star
    if upper_wick > body * 2 and lower_wick < body * 0.5 and body_pct < 0.4:
        return "Shooting Star ⭐", "SELL", 75
    
    # Morning Star (3-candle)
    if len(closes) >= 3:
        ppo, ppc = opens[-3], closes[-3]
        if ppc < ppo and abs(pc - po) < abs(ppc - ppo) * 0.3 and c > o and c > (ppo + ppc) / 2:
            return "Morning Star 🌅", "BUY", 80
    
    # Evening Star (3-candle)
    if len(closes) >= 3:
        ppo, ppc = opens[-3], closes[-3]
        if ppc > ppo and abs(pc - po) < abs(ppc - ppo) * 0.3 and c < o and c < (ppo + ppc) / 2:
            return "Evening Star 🌙", "SELL", 80
    
    # Doji
    if body_pct < 0.1:
        return "Doji ✚", "NEUTRAL", 50
    
    # Marubozu Bullish
    if c > o and upper_wick < body * 0.05 and lower_wick < body * 0.05:
        return "Bullish Marubozu 📈", "BUY", 70
    
    # Marubozu Bearish
    if c < o and upper_wick < body * 0.05 and lower_wick < body * 0.05:
        return "Bearish Marubozu 📉", "SELL", 70
    
    # Three White Soldiers
    if len(closes) >= 3:
        if closes[-1] > closes[-2] > closes[-3] and opens[-1] > opens[-2] > opens[-3]:
            if all(closes[i] > opens[i] for i in range(-3, 0)):
                return "Three White Soldiers 🎖️", "BUY", 85
    
    # Three Black Crows
    if len(closes) >= 3:
        if closes[-1] < closes[-2] < closes[-3] and opens[-1] < opens[-2] < opens[-3]:
            if all(closes[i] < opens[i] for i in range(-3, 0)):
                return "Three Black Crows 🦅", "SELL", 85
    
    # Piercing Pattern
    if pc < po and c > o and o < l and c > (po + pc) / 2:
        return "Piercing Pattern ⚡", "BUY", 70
    
    # Dark Cloud Cover
    if pc > po and c < o and o > ph and c < (po + pc) / 2:
        return "Dark Cloud ☁️", "SELL", 70
    
    # Bullish Harami
    if pc < po and c > o and c < po and o > pc:
        return "Bullish Harami 🔄", "BUY", 65
    
    # Bearish Harami
    if pc > po and c < o and c > po and o < pc:
        return "Bearish Harami 🔄", "SELL", 65
    
    # Default
    if c > o:
        return "Bullish Candle", "BUY", 40
    elif c < o:
        return "Bearish Candle", "SELL", 40
    else:
        return "Neutral", "NEUTRAL", 30

# ═══════════════════════════════════════════════════════════════
# MAIN SIGNAL GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_buy_sell_signal(
    symbol: str,
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    market_type: MarketType = MarketType.STOCK,
    currency: str = "INR"
) -> Optional[BuySellSignal]:
    """
    MASTER SIGNAL GENERATOR
    Analyzes 12+ technical indicators and generates a comprehensive buy/sell signal
    """
    try:
        if len(closes) < 26:
            return None
        
        current_price = closes[-1]
        indicators = []
        buy_count = 0
        sell_count = 0
        neutral_count = 0
        
        # ── 1. RSI Analysis ──
        rsi = calculate_rsi(closes)
        if rsi < 30:
            rsi_signal = "BUY"
            rsi_strength = 90 - rsi
            rsi_desc = f"RSI {rsi} - Oversold! Strong reversal expected"
            rsi_desc_hi = f"RSI {rsi} - बहुत ज़्यादा बिकवाली! मज़बूत उछाल संभव"
            buy_count += 1
        elif rsi < 40:
            rsi_signal = "BUY"
            rsi_strength = 65
            rsi_desc = f"RSI {rsi} - Approaching oversold zone"
            rsi_desc_hi = f"RSI {rsi} - ओवरसोल्ड ज़ोन के करीब"
            buy_count += 1
        elif rsi > 70:
            rsi_signal = "SELL"
            rsi_strength = rsi - 10
            rsi_desc = f"RSI {rsi} - Overbought! Correction expected"
            rsi_desc_hi = f"RSI {rsi} - बहुत ज़्यादा खरीदारी! गिरावट संभव"
            sell_count += 1
        elif rsi > 60:
            rsi_signal = "SELL"
            rsi_strength = 55
            rsi_desc = f"RSI {rsi} - Approaching overbought zone"
            rsi_desc_hi = f"RSI {rsi} - ओवरबॉट ज़ोन के करीब"
            sell_count += 1
        else:
            rsi_signal = "NEUTRAL"
            rsi_strength = 40
            rsi_desc = f"RSI {rsi} - Neutral zone"
            rsi_desc_hi = f"RSI {rsi} - न्यूट्रल ज़ोन"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("RSI", rsi, rsi_signal, rsi_strength, rsi_desc, rsi_desc_hi))
        
        # ── 2. MACD Analysis ──
        macd, signal_line, histogram = calculate_macd(closes)
        if histogram > 0 and macd > signal_line:
            macd_signal = "BUY"
            macd_strength = min(80, 50 + abs(histogram) * 100)
            macd_desc = f"MACD Bullish crossover (Hist: {histogram})"
            macd_desc_hi = f"MACD बुलिश क्रॉसओवर (हिस्ट: {histogram})"
            buy_count += 1
        elif histogram < 0 and macd < signal_line:
            macd_signal = "SELL"
            macd_strength = min(80, 50 + abs(histogram) * 100)
            macd_desc = f"MACD Bearish crossover (Hist: {histogram})"
            macd_desc_hi = f"MACD बेयरिश क्रॉसओवर (हिस्ट: {histogram})"
            sell_count += 1
        else:
            macd_signal = "NEUTRAL"
            macd_strength = 40
            macd_desc = f"MACD Neutral (Hist: {histogram})"
            macd_desc_hi = f"MACD न्यूट्रल (हिस्ट: {histogram})"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("MACD", histogram, macd_signal, macd_strength, macd_desc, macd_desc_hi))
        
        # ── 3. EMA Crossover (9/21) ──
        ema_9 = calculate_ema(closes, 9)
        ema_21 = calculate_ema(closes, 21)
        ema_50 = calculate_ema(closes, min(50, len(closes) - 1))
        ema_200 = calculate_ema(closes, min(200, len(closes) - 1))
        
        if ema_9 > ema_21 and current_price > ema_9:
            ema_signal = "BUY"
            ema_strength = 75
            ema_desc = f"EMA 9({ema_9}) > EMA 21({ema_21}) - Bullish trend"
            ema_desc_hi = f"EMA 9({ema_9}) > EMA 21({ema_21}) - तेज़ी का ट्रेंड"
            buy_count += 1
        elif ema_9 < ema_21 and current_price < ema_9:
            ema_signal = "SELL"
            ema_strength = 75
            ema_desc = f"EMA 9({ema_9}) < EMA 21({ema_21}) - Bearish trend"
            ema_desc_hi = f"EMA 9({ema_9}) < EMA 21({ema_21}) - मंदी का ट्रेंड"
            sell_count += 1
        else:
            ema_signal = "NEUTRAL"
            ema_strength = 40
            ema_desc = f"EMA crossover neutral"
            ema_desc_hi = f"EMA क्रॉसओवर न्यूट्रल"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("EMA Cross", ema_9 - ema_21, ema_signal, ema_strength, ema_desc, ema_desc_hi))
        
        # ── 4. Bollinger Bands ──
        bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(closes)
        if bb_lower > 0:
            if current_price <= bb_lower:
                bb_signal = "BUY"
                bb_strength = 80
                bb_desc = f"Price at Lower BB ({bb_lower}) - Bounce expected"
                bb_desc_hi = f"प्राइस लोअर BB ({bb_lower}) पर - उछाल संभव"
                buy_count += 1
            elif current_price >= bb_upper:
                bb_signal = "SELL"
                bb_strength = 80
                bb_desc = f"Price at Upper BB ({bb_upper}) - Resistance"
                bb_desc_hi = f"प्राइस अपर BB ({bb_upper}) पर - रेज़िस्टेंस"
                sell_count += 1
            else:
                bb_signal = "NEUTRAL"
                bb_strength = 40
                bb_desc = f"Price within BB range"
                bb_desc_hi = f"प्राइस BB रेंज में"
                neutral_count += 1
        else:
            bb_signal = "NEUTRAL"
            bb_strength = 30
            bb_desc = "Insufficient data for BB"
            bb_desc_hi = "BB के लिए कम डाटा"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("Bollinger", current_price, bb_signal, bb_strength, bb_desc, bb_desc_hi))
        
        # ── 5. Stochastic Oscillator ──
        stoch_k, stoch_d = calculate_stochastic(highs, lows, closes)
        if stoch_k < 20 and stoch_d < 20:
            stoch_signal = "BUY"
            stoch_strength = 80
            stoch_desc = f"Stochastic (%K:{stoch_k}, %D:{stoch_d}) - Oversold"
            stoch_desc_hi = f"स्टोकैस्टिक (%K:{stoch_k}, %D:{stoch_d}) - ओवरसोल्ड"
            buy_count += 1
        elif stoch_k > 80 and stoch_d > 80:
            stoch_signal = "SELL"
            stoch_strength = 80
            stoch_desc = f"Stochastic (%K:{stoch_k}, %D:{stoch_d}) - Overbought"
            stoch_desc_hi = f"स्टोकैस्टिक (%K:{stoch_k}, %D:{stoch_d}) - ओवरबॉट"
            sell_count += 1
        elif stoch_k > stoch_d:
            stoch_signal = "BUY"
            stoch_strength = 55
            stoch_desc = f"Stochastic bullish (%K > %D)"
            stoch_desc_hi = f"स्टोकैस्टिक बुलिश (%K > %D)"
            buy_count += 1
        else:
            stoch_signal = "NEUTRAL"
            stoch_strength = 40
            stoch_desc = f"Stochastic neutral"
            stoch_desc_hi = f"स्टोकैस्टिक न्यूट्रल"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("Stochastic", stoch_k, stoch_signal, stoch_strength, stoch_desc, stoch_desc_hi))
        
        # ── 6. ADX Trend Strength ──
        adx, plus_di, minus_di = calculate_adx(highs, lows, closes)
        if adx > 25 and plus_di > minus_di:
            adx_signal = "BUY"
            adx_strength = min(90, adx + 30)
            adx_desc = f"ADX {adx} - Strong bullish trend (+DI:{plus_di} > -DI:{minus_di})"
            adx_desc_hi = f"ADX {adx} - मज़बूत तेज़ी (+DI:{plus_di} > -DI:{minus_di})"
            buy_count += 1
        elif adx > 25 and minus_di > plus_di:
            adx_signal = "SELL"
            adx_strength = min(90, adx + 30)
            adx_desc = f"ADX {adx} - Strong bearish trend (-DI:{minus_di} > +DI:{plus_di})"
            adx_desc_hi = f"ADX {adx} - मज़बूत मंदी (-DI:{minus_di} > +DI:{plus_di})"
            sell_count += 1
        else:
            adx_signal = "NEUTRAL"
            adx_strength = 35
            adx_desc = f"ADX {adx} - Weak/No trend"
            adx_desc_hi = f"ADX {adx} - कमज़ोर ट्रेंड"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("ADX", adx, adx_signal, adx_strength, adx_desc, adx_desc_hi))
        
        # ── 7. Supertrend ──
        st_value, st_trend = calculate_supertrend(highs, lows, closes)
        if st_trend == "BULLISH":
            st_signal = "BUY"
            st_strength = 80
            st_desc = f"Supertrend BULLISH (Support: ₹{st_value})"
            st_desc_hi = f"सुपरट्रेंड तेज़ी (सपोर्ट: ₹{st_value})"
            buy_count += 1
        elif st_trend == "BEARISH":
            st_signal = "SELL"
            st_strength = 80
            st_desc = f"Supertrend BEARISH (Resistance: ₹{st_value})"
            st_desc_hi = f"सुपरट्रेंड मंदी (रेज़िस्टेंस: ₹{st_value})"
            sell_count += 1
        else:
            st_signal = "NEUTRAL"
            st_strength = 40
            st_desc = f"Supertrend Neutral"
            st_desc_hi = f"सुपरट्रेंड न्यूट्रल"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("Supertrend", st_value, st_signal, st_strength, st_desc, st_desc_hi))
        
        # ── 8. VWAP ──
        vwap = calculate_vwap(highs, lows, closes, volumes)
        if current_price > vwap * 1.01:
            vwap_signal = "BUY"
            vwap_strength = 65
            vwap_desc = f"Price above VWAP (₹{vwap}) - Bullish"
            vwap_desc_hi = f"प्राइस VWAP (₹{vwap}) से ऊपर - तेज़ी"
            buy_count += 1
        elif current_price < vwap * 0.99:
            vwap_signal = "SELL"
            vwap_strength = 65
            vwap_desc = f"Price below VWAP (₹{vwap}) - Bearish"
            vwap_desc_hi = f"प्राइस VWAP (₹{vwap}) से नीचे - मंदी"
            sell_count += 1
        else:
            vwap_signal = "NEUTRAL"
            vwap_strength = 40
            vwap_desc = f"Price near VWAP (₹{vwap})"
            vwap_desc_hi = f"प्राइस VWAP (₹{vwap}) के पास"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("VWAP", vwap, vwap_signal, vwap_strength, vwap_desc, vwap_desc_hi))
        
        # ── 9. Volume Analysis ──
        vol_signal_text, vol_strength = detect_volume_signal(volumes)
        if vol_signal_text in ["EXTREME_VOLUME", "HIGH_VOLUME"] and closes[-1] > closes[-2]:
            vol_signal = "BUY"
            vol_desc = f"Volume surge with price up - {vol_signal_text}"
            vol_desc_hi = f"वॉल्यूम बढ़ा + प्राइस ऊपर - {vol_signal_text}"
            buy_count += 1
        elif vol_signal_text in ["EXTREME_VOLUME", "HIGH_VOLUME"] and closes[-1] < closes[-2]:
            vol_signal = "SELL"
            vol_desc = f"Volume surge with price down - {vol_signal_text}"
            vol_desc_hi = f"वॉल्यूम बढ़ा + प्राइस नीचे - {vol_signal_text}"
            sell_count += 1
        else:
            vol_signal = "NEUTRAL"
            vol_desc = f"Volume: {vol_signal_text}"
            vol_desc_hi = f"वॉल्यूम: {vol_signal_text}"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("Volume", volumes[-1] if volumes else 0, vol_signal, vol_strength, vol_desc, vol_desc_hi))
        
        # ── 10. Candlestick Pattern ──
        candle_name, candle_sig, candle_strength = detect_candle_pattern_signal(opens, highs, lows, closes)
        if candle_sig == "BUY":
            buy_count += 1
        elif candle_sig == "SELL":
            sell_count += 1
        else:
            neutral_count += 1
        
        candle_desc_hi = f"कैंडल पैटर्न: {candle_name}"
        indicators.append(TechnicalIndicator("Candle Pattern", candle_strength, candle_sig, candle_strength, f"Pattern: {candle_name}", candle_desc_hi))
        
        # ── 11. Price vs 200 EMA (Golden/Death Cross Check) ──
        if current_price > ema_200 and ema_50 > ema_200:
            trend_200 = "BUY"
            trend_strength = 85
            trend_desc = f"Golden Cross - EMA50 > EMA200, Price above"
            trend_desc_hi = f"गोल्डन क्रॉस - EMA50 > EMA200, प्राइस ऊपर"
            buy_count += 1
        elif current_price < ema_200 and ema_50 < ema_200:
            trend_200 = "SELL"
            trend_strength = 85
            trend_desc = f"Death Cross - EMA50 < EMA200, Price below"
            trend_desc_hi = f"डेथ क्रॉस - EMA50 < EMA200, प्राइस नीचे"
            sell_count += 1
        else:
            trend_200 = "NEUTRAL"
            trend_strength = 45
            trend_desc = f"EMA trend mixed"
            trend_desc_hi = f"EMA ट्रेंड मिक्स्ड"
            neutral_count += 1
        
        indicators.append(TechnicalIndicator("EMA 200", ema_200, trend_200, trend_strength, trend_desc, trend_desc_hi))
        
        # ── 12. Price Momentum (Rate of Change) ──
        if len(closes) >= 10:
            roc = ((closes[-1] - closes[-10]) / closes[-10]) * 100
            if roc > 3:
                mom_signal = "BUY"
                mom_strength = min(80, 50 + roc * 5)
                mom_desc = f"Momentum +{roc:.1f}% (10-period) - Strong upward"
                mom_desc_hi = f"मोमेंटम +{roc:.1f}% (10-पीरियड) - तेज़ ऊपर"
                buy_count += 1
            elif roc < -3:
                mom_signal = "SELL"
                mom_strength = min(80, 50 + abs(roc) * 5)
                mom_desc = f"Momentum {roc:.1f}% (10-period) - Strong downward"
                mom_desc_hi = f"मोमेंटम {roc:.1f}% (10-पीरियड) - तेज़ नीचे"
                sell_count += 1
            else:
                mom_signal = "NEUTRAL"
                mom_strength = 40
                mom_desc = f"Momentum {roc:.1f}% - Flat"
                mom_desc_hi = f"मोमेंटम {roc:.1f}% - फ्लैट"
                neutral_count += 1
            
            indicators.append(TechnicalIndicator("Momentum", roc, mom_signal, mom_strength, mom_desc, mom_desc_hi))
        
        # ═══════════════════════════════════════════════════════
        # SIGNAL DECISION ENGINE
        # ═══════════════════════════════════════════════════════
        
        total = buy_count + sell_count + neutral_count
        buy_pct = (buy_count / total * 100) if total > 0 else 0
        sell_pct = (sell_count / total * 100) if total > 0 else 0
        
        # Determine signal type
        if buy_pct >= 75:
            signal_type = SignalType.STRONG_BUY
            confidence = min(95, buy_pct + 10)
        elif buy_pct >= 60:
            signal_type = SignalType.BUY
            confidence = min(85, buy_pct + 5)
        elif buy_pct >= 45 and buy_pct > sell_pct:
            signal_type = SignalType.WEAK_BUY
            confidence = buy_pct
        elif sell_pct >= 75:
            signal_type = SignalType.STRONG_SELL
            confidence = min(95, sell_pct + 10)
        elif sell_pct >= 60:
            signal_type = SignalType.SELL
            confidence = min(85, sell_pct + 5)
        elif sell_pct >= 45 and sell_pct > buy_pct:
            signal_type = SignalType.WEAK_SELL
            confidence = sell_pct
        else:
            signal_type = SignalType.HOLD
            confidence = 50
        
        # Determine overall trend
        if ema_9 > ema_21 > ema_50:
            trend = "BULLISH 📈"
        elif ema_9 < ema_21 < ema_50:
            trend = "BEARISH 📉"
        else:
            trend = "SIDEWAYS ➡️"
        
        # Calculate ATR for stop-loss and targets
        atr = calculate_atr(highs, lows, closes)
        
        # Entry, Stop-loss, Targets
        if "BUY" in signal_type.value:
            entry = current_price
            stop_loss = round(current_price - (atr * 1.5), 2)
            target_1 = round(current_price + (atr * 1.5), 2)
            target_2 = round(current_price + (atr * 2.5), 2)
            target_3 = round(current_price + (atr * 4.0), 2)
        elif "SELL" in signal_type.value:
            entry = current_price
            stop_loss = round(current_price + (atr * 1.5), 2)
            target_1 = round(current_price - (atr * 1.5), 2)
            target_2 = round(current_price - (atr * 2.5), 2)
            target_3 = round(current_price - (atr * 4.0), 2)
        else:
            entry = current_price
            stop_loss = round(current_price - (atr * 1.5), 2)
            target_1 = round(current_price + (atr * 1.0), 2)
            target_2 = round(current_price + (atr * 2.0), 2)
            target_3 = round(current_price + (atr * 3.0), 2)
        
        # Risk-Reward ratio
        risk = abs(entry - stop_loss)
        reward = abs(target_2 - entry)
        risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        # Generate summaries
        curr_sym = "₹" if currency == "INR" else "$"
        
        summary_en = (
            f"{signal_type.value} for {symbol}\n"
            f"Price: {curr_sym}{current_price:,.2f} | Confidence: {confidence:.0f}%\n"
            f"Indicators: {buy_count} BUY / {sell_count} SELL / {neutral_count} NEUTRAL\n"
            f"Trend: {trend} | Pattern: {candle_name}\n"
            f"Entry: {curr_sym}{entry:,.2f} | SL: {curr_sym}{stop_loss:,.2f}\n"
            f"Target 1: {curr_sym}{target_1:,.2f} | T2: {curr_sym}{target_2:,.2f} | T3: {curr_sym}{target_3:,.2f}\n"
            f"Risk:Reward = 1:{risk_reward}"
        )
        
        summary_hi = (
            f"{signal_type.value} - {symbol}\n"
            f"कीमत: {curr_sym}{current_price:,.2f} | भरोसा: {confidence:.0f}%\n"
            f"इंडिकेटर: {buy_count} खरीदो / {sell_count} बेचो / {neutral_count} रुको\n"
            f"ट्रेंड: {trend} | पैटर्न: {candle_name}\n"
            f"एंट्री: {curr_sym}{entry:,.2f} | स्टॉप लॉस: {curr_sym}{stop_loss:,.2f}\n"
            f"टार्गेट 1: {curr_sym}{target_1:,.2f} | T2: {curr_sym}{target_2:,.2f} | T3: {curr_sym}{target_3:,.2f}\n"
            f"रिस्क:रिवॉर्ड = 1:{risk_reward}"
        )
        
        # Alert conditions
        alerts = []
        if confidence >= 80:
            alerts.append(f"HIGH CONFIDENCE {signal_type.value} signal!")
        if rsi < 25 or rsi > 75:
            alerts.append(f"RSI extreme at {rsi}!")
        if vol_signal_text in ["EXTREME_VOLUME", "HIGH_VOLUME"]:
            alerts.append(f"Volume spike detected!")
        if candle_strength >= 80:
            alerts.append(f"Strong candle pattern: {candle_name}")
        if adx > 40:
            alerts.append(f"Very strong trend (ADX: {adx})")
        
        return BuySellSignal(
            symbol=symbol,
            market_type=market_type,
            signal_type=signal_type,
            confidence=confidence,
            entry_price=entry,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            risk_reward=risk_reward,
            indicators=indicators,
            buy_score=buy_count,
            sell_score=sell_count,
            neutral_score=neutral_count,
            trend=trend,
            volume_signal=vol_signal_text,
            candle_pattern=candle_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            summary_en=summary_en,
            summary_hi=summary_hi,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Signal generation error for {symbol}: {e}")
        traceback.print_exc()
        return None


# ═══════════════════════════════════════════════════════════════
# STOCK MARKET SIGNAL SCANNER (NIFTY/SENSEX)
# ═══════════════════════════════════════════════════════════════

def get_stock_signal(symbol: str) -> Optional[BuySellSignal]:
    """Get buy/sell signal for an Indian stock or index"""
    try:
        import yfinance as yf
        
        # Add .NS suffix for NSE stocks
        yf_symbol = symbol
        if not symbol.endswith(('.NS', '.BO', '^')):
            yf_symbol = f"{symbol}.NS"
        
        # Map common names
        symbol_map = {
            "NIFTY": "^NSEI",
            "NIFTY50": "^NSEI",
            "NIFTY 50": "^NSEI",
            "SENSEX": "^BSESN",
            "BSE": "^BSESN",
            "BANKNIFTY": "^NSEBANK",
            "BANK NIFTY": "^NSEBANK",
            "NIFTYBANK": "^NSEBANK",
            "NIFTYIT": "^CNXIT",
            "NIFTY IT": "^CNXIT",
        }
        
        upper_sym = symbol.upper().strip()
        if upper_sym in symbol_map:
            yf_symbol = symbol_map[upper_sym]
        
        # Fetch data
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period="6mo", interval="1d")
        
        if df.empty or len(df) < 26:
            return None
        
        opens = df['Open'].tolist()
        highs = df['High'].tolist()
        lows = df['Low'].tolist()
        closes = df['Close'].tolist()
        volumes = df['Volume'].tolist()
        
        # Determine market type
        if yf_symbol.startswith('^'):
            mtype = MarketType.INDEX
        else:
            mtype = MarketType.STOCK
        
        signal = generate_buy_sell_signal(
            symbol=upper_sym,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            market_type=mtype,
            currency="INR"
        )
        
        return signal
        
    except Exception as e:
        logger.error(f"Stock signal error for {symbol}: {e}")
        return None


def get_crypto_signal(symbol: str) -> Optional[BuySellSignal]:
    """Get buy/sell signal for a cryptocurrency"""
    try:
        import requests
        
        # Clean symbol
        clean_sym = symbol.upper().strip()
        if clean_sym.endswith("USDT"):
            clean_sym = clean_sym[:-4]
        if clean_sym.endswith("INR"):
            clean_sym = clean_sym[:-3]
        
        # Map common names
        crypto_map = {
            "BTC": "bitcoin", "BITCOIN": "bitcoin",
            "ETH": "ethereum", "ETHEREUM": "ethereum",
            "BNB": "binancecoin", "SOL": "solana",
            "SOLANA": "solana", "XRP": "ripple",
            "DOGE": "dogecoin", "DOGECOIN": "dogecoin",
            "ADA": "cardano", "DOT": "polkadot",
            "AVAX": "avalanche-2", "MATIC": "matic-network",
            "POLYGON": "matic-network", "SHIB": "shiba-inu",
            "LINK": "chainlink", "UNI": "uniswap",
            "ATOM": "cosmos", "LTC": "litecoin",
            "NEAR": "near", "APT": "aptos",
            "SUI": "sui", "ARB": "arbitrum",
            "OP": "optimism", "FTM": "fantom",
            "PEPE": "pepe", "WIF": "dogwifcoin",
            "BONK": "bonk", "FLOKI": "floki",
            "INJ": "injective-protocol", "TIA": "celestia",
            "SEI": "sei-network", "JUP": "jupiter-exchange-solana",
        }
        
        coin_id = crypto_map.get(clean_sym, clean_sym.lower())
        
        # Get OHLC data from DexScreener (CoinGecko removed)
        # Try DexScreener for token data
        url = f"https://api.dexscreener.com/latest/dex/search?q={clean_sym}"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        search_data = resp.json()
        pairs = search_data.get("pairs", [])
        if not pairs or len(pairs) < 1:
            return None
        
        # Use DexScreener pair data to approximate OHLC
        pair = pairs[0]
        price = float(pair.get("priceUsd", 0) or 0)
        if price <= 0:
            return None
        
        # Generate synthetic OHLC from price data
        inr_rate = 83.5
        try:
            from crypto_engine import get_usd_inr_rate
            inr_rate = get_usd_inr_rate()
        except:
            pass
        price_inr = price * inr_rate
        
        # Create approximate historical data from available changes
        change_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0) / 100
        opens = [price_inr * (1 - change_24h * (25-i)/25) for i in range(26)]
        highs = [p * 1.01 for p in opens]
        lows = [p * 0.99 for p in opens]
        closes = opens[:]
        volumes = [abs(h - l) * c for h, l, c in zip(highs, lows, closes)]
        
        signal = generate_buy_sell_signal(
            symbol=clean_sym,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            market_type=MarketType.CRYPTO,
            currency="INR"
        )
        
        return signal
        
    except Exception as e:
        logger.error(f"Crypto signal error for {symbol}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# NIFTY 50 TOP SIGNALS SCANNER
# ═══════════════════════════════════════════════════════════════

NIFTY_50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "BAJFINANCE", "WIPRO", "HCLTECH", "ULTRACEMCO",
    "TATAMOTORS", "NTPC", "POWERGRID", "ONGC", "M&M",
    "ADANIGREEN", "ADANIENT", "JSWSTEEL", "TATASTEEL", "TECHM",
    "BAJAJFINSV", "NESTLEIND", "INDUSINDBK", "GRASIM", "COALINDIA",
    "BPCL", "BRITANNIA", "CIPLA", "DRREDDY", "DIVISLAB",
    "EICHERMOT", "HEROMOTOCO", "APOLLOHOSP", "SBILIFE", "HDFCLIFE",
    "TATACONSUM", "HINDALCO", "UPL", "BAJAJ-AUTO", "LTIM"
]

TOP_CRYPTOS = [
    "BTC", "ETH", "SOL", "BNB", "XRP",
    "DOGE", "ADA", "AVAX", "DOT", "MATIC",
    "SHIB", "LINK", "UNI", "ATOM", "NEAR",
    "PEPE", "WIF", "BONK", "INJ", "SUI",
]

def scan_nifty_signals(top_n: int = 10) -> List[BuySellSignal]:
    """Scan NIFTY 50 stocks for strongest buy/sell signals"""
    signals = []
    
    for stock in NIFTY_50_STOCKS[:30]:  # Scan top 30 for speed
        try:
            signal = get_stock_signal(stock)
            if signal and signal.confidence >= 55:
                signals.append(signal)
        except Exception:
            continue
        time.sleep(0.5)  # Rate limit
    
    # Sort by confidence
    signals.sort(key=lambda s: s.confidence, reverse=True)
    return signals[:top_n]

def scan_crypto_signals(top_n: int = 10) -> List[BuySellSignal]:
    """Scan top cryptocurrencies for strongest buy/sell signals"""
    signals = []
    
    for coin in TOP_CRYPTOS:
        try:
            signal = get_crypto_signal(coin)
            if signal and signal.confidence >= 50:
                signals.append(signal)
        except Exception:
            continue
        time.sleep(1)  # Rate limit for CoinGecko
    
    signals.sort(key=lambda s: s.confidence, reverse=True)
    return signals[:top_n]

def scan_index_signals() -> List[BuySellSignal]:
    """Scan major indices for signals"""
    indices = ["NIFTY", "SENSEX", "BANKNIFTY"]
    signals = []
    
    for idx in indices:
        try:
            signal = get_stock_signal(idx)
            if signal:
                signals.append(signal)
        except Exception:
            continue
        time.sleep(0.5)
    
    return signals


# ═══════════════════════════════════════════════════════════════
# SIGNAL FORMATTING (English + Hindi)
# ═══════════════════════════════════════════════════════════════

def format_signal_message(signal: BuySellSignal, lang: str = "hi") -> str:
    """Format buy/sell signal as beautiful Telegram message"""
    if not signal:
        if lang == "hi":
            return "कोई सिग्नल नहीं मिला। बाद में कोशिश करें।"
        return "No signal found. Try again later."
    
    curr = "₹"
    
    # Signal emoji bar
    total = signal.buy_score + signal.sell_score + signal.neutral_score
    buy_bars = int((signal.buy_score / total) * 10) if total > 0 else 0
    sell_bars = int((signal.sell_score / total) * 10) if total > 0 else 0
    neutral_bars = 10 - buy_bars - sell_bars
    
    bar = "🟢" * buy_bars + "⚪" * neutral_bars + "🔴" * sell_bars
    
    # Confidence meter
    conf_filled = int(signal.confidence / 10)
    conf_empty = 10 - conf_filled
    conf_bar = "█" * conf_filled + "░" * conf_empty
    
    if lang == "hi":
        msg = (
            f"{'═' * 30}\n"
            f"🤖 जार्विस बाय/सेल सिग्नल\n"
            f"{'═' * 30}\n\n"
            f"📊 {signal.symbol} ({signal.market_type.value.upper()})\n"
            f"{'─' * 25}\n\n"
            f"🎯 सिग्नल: {signal.signal_type.value}\n"
            f"💰 कीमत: {curr}{signal.entry_price:,.2f}\n"
            f"📈 ट्रेंड: {signal.trend}\n"
            f"🕯️ कैंडल: {signal.candle_pattern}\n\n"
            f"{'─' * 25}\n"
            f"📊 इंडिकेटर स्कोरबोर्ड:\n"
            f"  🟢 खरीदो: {signal.buy_score}/{total}\n"
            f"  🔴 बेचो: {signal.sell_score}/{total}\n"
            f"  ⚪ रुको: {signal.neutral_score}/{total}\n"
            f"  {bar}\n\n"
            f"💪 भरोसा: {signal.confidence:.0f}%\n"
            f"  [{conf_bar}]\n\n"
            f"{'─' * 25}\n"
            f"🎯 ट्रेडिंग प्लान:\n"
            f"  ▶️ एंट्री: {curr}{signal.entry_price:,.2f}\n"
            f"  🛑 स्टॉप लॉस: {curr}{signal.stop_loss:,.2f}\n"
            f"  🎯 टार्गेट 1: {curr}{signal.target_1:,.2f}\n"
            f"  🎯 टार्गेट 2: {curr}{signal.target_2:,.2f}\n"
            f"  🎯 टार्गेट 3: {curr}{signal.target_3:,.2f}\n"
            f"  ⚖️ रिस्क:रिवॉर्ड = 1:{signal.risk_reward}\n\n"
            f"{'─' * 25}\n"
            f"📋 सभी इंडिकेटर:\n"
        )
        
        for ind in signal.indicators:
            emoji = "🟢" if ind.signal == "BUY" else ("🔴" if ind.signal == "SELL" else "⚪")
            msg += f"  {emoji} {ind.name}: {ind.description_hi}\n"
        
        if signal.alerts:
            msg += f"\n{'─' * 25}\n🚨 अलर्ट:\n"
            for alert in signal.alerts:
                msg += f"  ⚡ {alert}\n"
        
        msg += f"\n⏱️ {signal.timestamp}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 जार्विस: ये सिर्फ टेक्निकल एनालिसिस है।\nइन्वेस्ट करने से पहले अपनी रिसर्च ज़रूर करें!\n"
        
    else:
        msg = (
            f"{'═' * 30}\n"
            f"🤖 JARVIS BUY/SELL SIGNAL\n"
            f"{'═' * 30}\n\n"
            f"📊 {signal.symbol} ({signal.market_type.value.upper()})\n"
            f"{'─' * 25}\n\n"
            f"🎯 Signal: {signal.signal_type.value}\n"
            f"💰 Price: {curr}{signal.entry_price:,.2f}\n"
            f"📈 Trend: {signal.trend}\n"
            f"🕯️ Candle: {signal.candle_pattern}\n\n"
            f"{'─' * 25}\n"
            f"📊 Indicator Scoreboard:\n"
            f"  🟢 BUY: {signal.buy_score}/{total}\n"
            f"  🔴 SELL: {signal.sell_score}/{total}\n"
            f"  ⚪ NEUTRAL: {signal.neutral_score}/{total}\n"
            f"  {bar}\n\n"
            f"💪 Confidence: {signal.confidence:.0f}%\n"
            f"  [{conf_bar}]\n\n"
            f"{'─' * 25}\n"
            f"🎯 Trading Plan:\n"
            f"  ▶️ Entry: {curr}{signal.entry_price:,.2f}\n"
            f"  🛑 Stop Loss: {curr}{signal.stop_loss:,.2f}\n"
            f"  🎯 Target 1: {curr}{signal.target_1:,.2f}\n"
            f"  🎯 Target 2: {curr}{signal.target_2:,.2f}\n"
            f"  🎯 Target 3: {curr}{signal.target_3:,.2f}\n"
            f"  ⚖️ Risk:Reward = 1:{signal.risk_reward}\n\n"
            f"{'─' * 25}\n"
            f"📋 All Indicators:\n"
        )
        
        for ind in signal.indicators:
            emoji = "🟢" if ind.signal == "BUY" else ("🔴" if ind.signal == "SELL" else "⚪")
            msg += f"  {emoji} {ind.name}: {ind.description}\n"
        
        if signal.alerts:
            msg += f"\n{'─' * 25}\n🚨 Alerts:\n"
            for alert in signal.alerts:
                msg += f"  ⚡ {alert}\n"
        
        msg += f"\n⏱️ {signal.timestamp}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 JARVIS: This is technical analysis only.\nAlways do your own research before investing!\n"
    
    return msg


def format_scanner_results(signals: List[BuySellSignal], title: str, lang: str = "hi") -> str:
    """Format multiple signals as a scanner/screener result"""
    if not signals:
        if lang == "hi":
            return f"🤖 {title}\n\nकोई मज़बूत सिग्नल नहीं मिला अभी।\nबाद में चेक करें सर!"
        return f"🤖 {title}\n\nNo strong signals found right now.\nCheck back later, Sir!"
    
    if lang == "hi":
        msg = (
            f"{'═' * 30}\n"
            f"🤖 {title}\n"
            f"{'═' * 30}\n\n"
        )
        
        buy_signals = [s for s in signals if "BUY" in s.signal_type.value]
        sell_signals = [s for s in signals if "SELL" in s.signal_type.value]
        
        if buy_signals:
            msg += "🟢 खरीदने वाले सिग्नल:\n"
            msg += "─" * 25 + "\n"
            for s in buy_signals[:5]:
                msg += (
                    f"  {s.signal_type.value} {s.symbol}\n"
                    f"  💰 ₹{s.entry_price:,.2f} | भरोसा: {s.confidence:.0f}%\n"
                    f"  🎯 SL: ₹{s.stop_loss:,.2f} → T: ₹{s.target_2:,.2f}\n"
                    f"  📊 {s.buy_score} Buy / {s.sell_score} Sell\n\n"
                )
        
        if sell_signals:
            msg += "🔴 बेचने वाले सिग्नल:\n"
            msg += "─" * 25 + "\n"
            for s in sell_signals[:5]:
                msg += (
                    f"  {s.signal_type.value} {s.symbol}\n"
                    f"  💰 ₹{s.entry_price:,.2f} | भरोसा: {s.confidence:.0f}%\n"
                    f"  🎯 SL: ₹{s.stop_loss:,.2f} → T: ₹{s.target_2:,.2f}\n"
                    f"  📊 {s.buy_score} Buy / {s.sell_score} Sell\n\n"
                )
        
        msg += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 जार्विस: सिर्फ टेक्निकल एनालिसिस!\n"
    else:
        msg = (
            f"{'═' * 30}\n"
            f"🤖 {title}\n"
            f"{'═' * 30}\n\n"
        )
        
        buy_signals = [s for s in signals if "BUY" in s.signal_type.value]
        sell_signals = [s for s in signals if "SELL" in s.signal_type.value]
        
        if buy_signals:
            msg += "🟢 BUY Signals:\n"
            msg += "─" * 25 + "\n"
            for s in buy_signals[:5]:
                msg += (
                    f"  {s.signal_type.value} {s.symbol}\n"
                    f"  💰 ₹{s.entry_price:,.2f} | Confidence: {s.confidence:.0f}%\n"
                    f"  🎯 SL: ₹{s.stop_loss:,.2f} → T: ₹{s.target_2:,.2f}\n"
                    f"  📊 {s.buy_score} Buy / {s.sell_score} Sell\n\n"
                )
        
        if sell_signals:
            msg += "🔴 SELL Signals:\n"
            msg += "─" * 25 + "\n"
            for s in sell_signals[:5]:
                msg += (
                    f"  {s.signal_type.value} {s.symbol}\n"
                    f"  💰 ₹{s.entry_price:,.2f} | Confidence: {s.confidence:.0f}%\n"
                    f"  🎯 SL: ₹{s.stop_loss:,.2f} → T: ₹{s.target_2:,.2f}\n"
                    f"  📊 {s.buy_score} Buy / {s.sell_score} Sell\n\n"
                )
        
        msg += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 JARVIS: Technical analysis only!\n"
    
    return msg


# ═══════════════════════════════════════════════════════════════
# AUTO ALERT SYSTEM
# ═══════════════════════════════════════════════════════════════

# Store last alert times to avoid spam
_last_alerts = {}  # symbol -> timestamp

def check_buy_sell_alerts(watchlist: List[str] = None, market: str = "stock") -> List[BuySellSignal]:
    """
    Check watchlist for strong buy/sell signals worth alerting
    Returns signals with confidence >= 70%
    """
    alert_signals = []
    
    if watchlist is None:
        watchlist = ["NIFTY", "SENSEX", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK"]
    
    for symbol in watchlist:
        # Rate limit: max 1 alert per symbol per 4 hours
        last_time = _last_alerts.get(symbol, 0)
        if time.time() - last_time < 14400:  # 4 hours
            continue
        
        try:
            if market == "crypto":
                signal = get_crypto_signal(symbol)
            else:
                signal = get_stock_signal(symbol)
            
            if signal and signal.confidence >= 70:
                alert_signals.append(signal)
                _last_alerts[symbol] = time.time()
        except Exception:
            continue
        
        time.sleep(1)  # Rate limiting
    
    return alert_signals


def format_alert_message(signal: BuySellSignal, lang: str = "hi") -> str:
    """Format an auto-alert message"""
    if lang == "hi":
        return (
            f"🚨🚨 जार्विस ऑटो अलर्ट 🚨🚨\n\n"
            f"📊 {signal.symbol} - {signal.signal_type.value}\n"
            f"💰 कीमत: ₹{signal.entry_price:,.2f}\n"
            f"💪 भरोसा: {signal.confidence:.0f}%\n"
            f"📈 ट्रेंड: {signal.trend}\n\n"
            f"🎯 ट्रेडिंग प्लान:\n"
            f"  ▶️ एंट्री: ₹{signal.entry_price:,.2f}\n"
            f"  🛑 SL: ₹{signal.stop_loss:,.2f}\n"
            f"  🎯 T1: ₹{signal.target_1:,.2f}\n"
            f"  🎯 T2: ₹{signal.target_2:,.2f}\n\n"
            f"📊 स्कोर: {signal.buy_score} Buy / {signal.sell_score} Sell\n"
            f"🕯️ पैटर्न: {signal.candle_pattern}\n\n"
            f"⏱️ {signal.timestamp}\n"
            f"🤖 जार्विस: अपनी रिसर्च भी ज़रूर करें!"
        )
    else:
        return (
            f"🚨🚨 JARVIS AUTO ALERT 🚨🚨\n\n"
            f"📊 {signal.symbol} - {signal.signal_type.value}\n"
            f"💰 Price: ₹{signal.entry_price:,.2f}\n"
            f"💪 Confidence: {signal.confidence:.0f}%\n"
            f"📈 Trend: {signal.trend}\n\n"
            f"🎯 Trading Plan:\n"
            f"  ▶️ Entry: ₹{signal.entry_price:,.2f}\n"
            f"  🛑 SL: ₹{signal.stop_loss:,.2f}\n"
            f"  🎯 T1: ₹{signal.target_1:,.2f}\n"
            f"  🎯 T2: ₹{signal.target_2:,.2f}\n\n"
            f"📊 Score: {signal.buy_score} Buy / {signal.sell_score} Sell\n"
            f"🕯️ Pattern: {signal.candle_pattern}\n\n"
            f"⏱️ {signal.timestamp}\n"
            f"🤖 JARVIS: Always do your own research!"
        )


# ═══════════════════════════════════════════════════════════════
# INTRADAY SCALPING ENGINE (NEW!)
# ═══════════════════════════════════════════════════════════════

def get_scalping_signal(symbol: str, index: str = "NIFTY") -> Optional[Dict[str, Any]]:
    """Generate intraday scalping signals using 5-min data.
    Uses RSI7 + EMA9/21 + Volume spike + ATR-based targets.
    Perfect for options trading (CE/PE).
    """
    import yfinance as yf
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        if df is None or df.empty or len(df) < 50:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume'] if 'Volume' in df.columns else pd.Series(0, index=df.index)

        price = float(close.iloc[-1])

        # EMA 9 & 21
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()

        # RSI 7
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        rs = up.ewm(span=7, adjust=False).mean() / (down.ewm(span=7, adjust=False).mean() + 1e-9)
        rsi7 = 100 - (100 / (1 + rs))

        # ATR 7
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr7 = tr.rolling(7).mean()
        atr_val = float(atr7.iloc[-1])

        # Volume spike
        vol_avg = vol.rolling(20).mean()
        vol_spike = float(vol.iloc[-1] / (vol_avg.iloc[-1] + 1)) if vol_avg.iloc[-1] > 0 else 1

        rsi_val = float(rsi7.iloc[-1])
        ema9_val = float(ema9.iloc[-1])
        ema21_val = float(ema21.iloc[-1])

        # Scalping signal logic
        buy_score = 0
        sell_score = 0
        reasons = []

        # EMA Cross
        if ema9_val > ema21_val:
            buy_score += 2
            reasons.append("EMA9 > EMA21 ✅")
        else:
            sell_score += 2
            reasons.append("EMA9 < EMA21 ❌")

        # RSI
        if rsi_val < 30:
            buy_score += 3
            reasons.append(f"RSI7={rsi_val:.0f} (Oversold) ✅")
        elif rsi_val < 45:
            buy_score += 1
            reasons.append(f"RSI7={rsi_val:.0f}")
        elif rsi_val > 70:
            sell_score += 3
            reasons.append(f"RSI7={rsi_val:.0f} (Overbought) ❌")
        elif rsi_val > 55:
            sell_score += 1
            reasons.append(f"RSI7={rsi_val:.0f}")

        # Volume
        if vol_spike > 2:
            buy_score += 1 if ema9_val > ema21_val else 0
            sell_score += 1 if ema9_val < ema21_val else 0
            reasons.append(f"Volume Spike {vol_spike:.1f}x 📊")

        # Price vs EMAs
        if price > ema9_val > ema21_val:
            buy_score += 1
        elif price < ema9_val < ema21_val:
            sell_score += 1

        # Overall signal
        if buy_score >= 4:
            signal = "🟢🟢 STRONG BUY CE"
            action = "BUY CALL"
        elif buy_score >= 3:
            signal = "🟢 BUY CE"
            action = "BUY CALL"
        elif sell_score >= 4:
            signal = "🔴🔴 STRONG BUY PE"
            action = "BUY PUT"
        elif sell_score >= 3:
            signal = "🔴 BUY PE"
            action = "BUY PUT"
        else:
            signal = "⚪ WAIT"
            action = "NO TRADE"

        # ATR-based targets
        sl = price - (1.5 * atr_val) if buy_score > sell_score else price + (1.5 * atr_val)
        t1 = price + (1 * atr_val) if buy_score > sell_score else price - (1 * atr_val)
        t2 = price + (2 * atr_val) if buy_score > sell_score else price - (2 * atr_val)

        confidence = max(buy_score, sell_score) / 7 * 100

        return {
            "symbol": index,
            "price": price,
            "signal": signal,
            "action": action,
            "confidence": min(95, confidence),
            "buy_score": buy_score,
            "sell_score": sell_score,
            "rsi7": rsi_val,
            "ema9": ema9_val,
            "ema21": ema21_val,
            "atr": atr_val,
            "vol_spike": vol_spike,
            "sl": round(sl, 2),
            "t1": round(t1, 2),
            "t2": round(t2, 2),
            "reasons": reasons,
            "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M IST"),
        }
    except Exception as e:
        logger.error(f"Scalping signal failed for {symbol}: {e}")
        return None


def format_scalping_signal(sig: Dict[str, Any], lang: str = "hi") -> str:
    """Format scalping signal as Telegram message."""
    if not sig:
        return "❌ Scalping signal not available"

    msg = f"⚡ *{sig['symbol']} — INTRADAY SCALPING* ⚡\n"
    msg += f"{'═' * 30}\n\n"
    msg += f"💰 Price: *₹{sig['price']:,.2f}*\n"
    msg += f"🎯 Signal: *{sig['signal']}*\n"
    msg += f"💪 Confidence: *{sig['confidence']:.0f}%*\n\n"

    msg += f"📊 *Indicators:*\n"
    for r in sig['reasons']:
        msg += f"  ┣ {r}\n"
    msg += f"  ┣ EMA9: ₹{sig['ema9']:,.2f} | EMA21: ₹{sig['ema21']:,.2f}\n"
    msg += f"  ┣ ATR: ₹{sig['atr']:,.2f}\n"
    msg += f"  ┣ Vol Spike: {sig['vol_spike']:.1f}x\n\n"

    if sig['action'] != "NO TRADE":
        bullish = "BUY" in sig['action'] and "CALL" in sig['action']
        msg += f"🎯 *Trading Plan:*\n"
        if bullish:
            msg += f"  ▶️ *Action: BUY CE (CALL)*\n"
        else:
            msg += f"  ▶️ *Action: BUY PE (PUT)*\n"
        msg += f"  🛑 SL: ₹{sig['sl']:,.2f}\n"
        msg += f"  🎯 T1: ₹{sig['t1']:,.2f}\n"
        msg += f"  🎯 T2: ₹{sig['t2']:,.2f}\n"

        # ₹2K investment calc
        move_pct = abs(sig['t1'] - sig['price']) / sig['price'] * 100
        msg += f"\n💸 *₹2,000 Investment:*\n"
        msg += f"  Move Expected: {move_pct:.1f}%\n"
        msg += f"  Option Premium × 2-3x = ₹{2000 * (1 + move_pct/100 * 3):,.0f}\n"
    else:
        msg += "⏳ *कोई clear signal नहीं है — WAIT करें*\n"

    msg += f"\n⏱️ {sig['timestamp']}"
    return msg


def get_multi_timeframe_signal(symbol: str, name: str = "") -> Optional[Dict[str, Any]]:
    """Multi-timeframe analysis combining 5m, 15m, 1h, 1d signals.
    Each timeframe gets a weight, final signal is weighted average.
    """
    import yfinance as yf

    timeframes = {
        "5m": {"period": "5d", "weight": 0.15},
        "15m": {"period": "5d", "weight": 0.20},
        "1h": {"period": "1mo", "weight": 0.30},
        "1d": {"period": "6mo", "weight": 0.35},
    }

    tf_signals = {}
    for tf, config in timeframes.items():
        try:
            df = yf.download(symbol, period=config["period"], interval=tf, progress=False)
            if df is None or df.empty or len(df) < 20:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df['Close']
            # Quick RSI
            delta = close.diff()
            up = delta.clip(lower=0)
            down = -delta.clip(upper=0)
            rs = up.ewm(span=14, adjust=False).mean() / (down.ewm(span=14, adjust=False).mean() + 1e-9)
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])

            # Quick EMA
            ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
            ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
            price = float(close.iloc[-1])

            # Signal: -2 to +2
            score = 0
            if rsi > 60:
                score += 1
            elif rsi < 40:
                score -= 1
            if price > ema20 > ema50:
                score += 1
            elif price < ema20 < ema50:
                score -= 1

            tf_signals[tf] = {
                "score": score,
                "weight": config["weight"],
                "rsi": rsi,
                "ema20": ema20,
                "ema50": ema50,
                "price": price,
                "trend": "BULL" if score > 0 else ("BEAR" if score < 0 else "NEUTRAL"),
            }
        except Exception:
            continue

    if not tf_signals:
        return None

    # Weighted average score
    total_weight = sum(s["weight"] for s in tf_signals.values())
    weighted_score = sum(s["score"] * s["weight"] for s in tf_signals.values()) / (total_weight + 1e-10)

    # Agreement
    trends = [s["trend"] for s in tf_signals.values()]
    bull_count = trends.count("BULL")
    bear_count = trends.count("BEAR")
    total = len(trends)

    if weighted_score > 0.5:
        signal = "🟢 MULTI-TF BULLISH"
        action = "BUY / CE"
    elif weighted_score < -0.5:
        signal = "🔴 MULTI-TF BEARISH"
        action = "SELL / PE"
    else:
        signal = "⚪ MULTI-TF NEUTRAL"
        action = "WAIT"

    return {
        "symbol": name or symbol,
        "signal": signal,
        "action": action,
        "weighted_score": round(weighted_score, 2),
        "agreement": f"{max(bull_count, bear_count)}/{total} timeframes agree",
        "timeframes": tf_signals,
        "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M IST"),
    }


def format_multi_tf(mtf: Dict[str, Any], lang: str = "hi") -> str:
    """Format multi-timeframe signal."""
    if not mtf:
        return "❌ Multi-TF data not available"

    msg = f"📊 *{mtf['symbol']} — MULTI-TIMEFRAME* 📊\n"
    msg += f"{'═' * 30}\n\n"
    msg += f"🎯 Signal: *{mtf['signal']}*\n"
    msg += f"🤝 Agreement: *{mtf['agreement']}*\n"
    msg += f"📈 Score: *{mtf['weighted_score']:+.2f}*\n\n"

    msg += f"📋 *Timeframe Breakdown:*\n"
    for tf, data in mtf.get("timeframes", {}).items():
        trend_emoji = "🟢" if data["trend"] == "BULL" else ("🔴" if data["trend"] == "BEAR" else "⚪")
        msg += f"  ┣ {tf}: {trend_emoji} {data['trend']} (RSI={data['rsi']:.0f})\n"

    msg += f"\n⏱️ {mtf['timestamp']}"
    return msg


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'SignalType', 'MarketType', 'TechnicalIndicator', 'BuySellSignal',
    'generate_buy_sell_signal', 'get_stock_signal', 'get_crypto_signal',
    'scan_nifty_signals', 'scan_crypto_signals', 'scan_index_signals',
    'format_signal_message', 'format_scanner_results',
    'check_buy_sell_alerts', 'format_alert_message',
    'NIFTY_50_STOCKS', 'TOP_CRYPTOS',
    'calculate_rsi', 'calculate_macd', 'calculate_ema', 'calculate_sma',
    'calculate_bollinger_bands', 'calculate_stochastic', 'calculate_adx',
    'calculate_supertrend', 'calculate_vwap', 'calculate_atr',
    'get_scalping_signal', 'format_scalping_signal',
    'get_multi_timeframe_signal', 'format_multi_tf',
]
