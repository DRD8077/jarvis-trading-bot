"""
🌍 GLOBAL CANDLE ENGINE - Super Computer Brain 🌍
Worldwide Market Candle Analysis & Buy/Sell Indicators
Analyzes: US (S&P 500, NASDAQ, DOW), Europe (DAX, FTSE, CAC),
          Asia (Nikkei, Hang Seng, Shanghai), India (NIFTY, SENSEX)
Detects global patterns that affect Indian markets
Provides worldwide trend analysis and correlation signals

Author: JARVIS Global Intelligence System
"""

import os
import time
import logging
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# GLOBAL MARKET DEFINITIONS
# ═══════════════════════════════════════════════════════════════

class GlobalRegion(Enum):
    US = "🇺🇸 US"
    EUROPE = "🇪🇺 Europe"
    ASIA = "🌏 Asia"
    INDIA = "🇮🇳 India"
    CRYPTO = "₿ Crypto"

@dataclass
class GlobalIndex:
    """Global market index info"""
    symbol: str
    yf_symbol: str
    name: str
    name_hi: str
    region: GlobalRegion
    currency: str
    timezone: str

@dataclass
class GlobalSignal:
    """Signal from global market analysis"""
    index: GlobalIndex
    price: float
    change_pct: float
    trend: str  # BULLISH, BEARISH, SIDEWAYS
    signal: str  # BUY, SELL, NEUTRAL
    strength: float  # 0-100
    candle_pattern: str
    rsi: float
    description: str
    description_hi: str

@dataclass
class GlobalAnalysis:
    """Complete global market analysis"""
    signals: List[GlobalSignal]
    overall_sentiment: str  # RISK_ON, RISK_OFF, MIXED
    india_impact: str
    india_impact_hi: str
    correlation_signals: List[str]
    timestamp: str
    summary_en: str
    summary_hi: str


# All global indices we track
GLOBAL_INDICES = [
    # 🇺🇸 US Markets
    GlobalIndex("SP500", "^GSPC", "S&P 500", "एसएंडपी 500", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("NASDAQ", "^IXIC", "NASDAQ", "नैस्डैक", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("DOW", "^DJI", "Dow Jones", "डाउ जोन्स", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("VIX", "^VIX", "VIX (Fear)", "VIX (डर)", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("RUSSELL", "^RUT", "Russell 2000", "रसेल 2000", GlobalRegion.US, "USD", "US/Eastern"),
    
    # 🇪🇺 Europe
    GlobalIndex("DAX", "^GDAXI", "DAX (Germany)", "DAX (जर्मनी)", GlobalRegion.EUROPE, "EUR", "Europe/Berlin"),
    GlobalIndex("FTSE", "^FTSE", "FTSE 100 (UK)", "FTSE 100 (UK)", GlobalRegion.EUROPE, "GBP", "Europe/London"),
    GlobalIndex("CAC", "^FCHI", "CAC 40 (France)", "CAC 40 (फ़्रांस)", GlobalRegion.EUROPE, "EUR", "Europe/Paris"),
    GlobalIndex("STOXX", "^STOXX50E", "Euro Stoxx 50", "यूरो स्टॉक्स 50", GlobalRegion.EUROPE, "EUR", "Europe/Berlin"),
    
    # 🌏 Asia
    GlobalIndex("NIKKEI", "^N225", "Nikkei 225 (Japan)", "निक्केई 225 (जापान)", GlobalRegion.ASIA, "JPY", "Asia/Tokyo"),
    GlobalIndex("HANGSENG", "^HSI", "Hang Seng (HK)", "हैंग सेंग (HK)", GlobalRegion.ASIA, "HKD", "Asia/Hong_Kong"),
    GlobalIndex("SHANGHAI", "000001.SS", "Shanghai (China)", "शंघाई (चीन)", GlobalRegion.ASIA, "CNY", "Asia/Shanghai"),
    GlobalIndex("KOSPI", "^KS11", "KOSPI (Korea)", "कोस्पी (कोरिया)", GlobalRegion.ASIA, "KRW", "Asia/Seoul"),
    GlobalIndex("ASX", "^AXJO", "ASX 200 (Australia)", "ASX 200 (ऑस्ट्रेलिया)", GlobalRegion.ASIA, "AUD", "Australia/Sydney"),
    
    # 🇮🇳 India
    GlobalIndex("NIFTY", "^NSEI", "NIFTY 50", "निफ्टी 50", GlobalRegion.INDIA, "INR", "Asia/Kolkata"),
    GlobalIndex("SENSEX", "^BSESN", "SENSEX", "सेंसेक्स", GlobalRegion.INDIA, "INR", "Asia/Kolkata"),
    GlobalIndex("BANKNIFTY", "^NSEBANK", "Bank NIFTY", "बैंक निफ्टी", GlobalRegion.INDIA, "INR", "Asia/Kolkata"),
]

# Commodities & Currency
GLOBAL_COMMODITIES = [
    GlobalIndex("GOLD", "GC=F", "Gold", "सोना", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("SILVER", "SI=F", "Silver", "चांदी", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("CRUDE", "CL=F", "Crude Oil", "क्रूड ऑइल", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("DXY", "DX-Y.NYB", "US Dollar Index", "डॉलर इंडेक्स", GlobalRegion.US, "USD", "US/Eastern"),
    GlobalIndex("USDINR", "USDINR=X", "USD/INR", "डॉलर/रुपया", GlobalRegion.INDIA, "INR", "Asia/Kolkata"),
]


# ═══════════════════════════════════════════════════════════════
# GLOBAL DATA FETCHER
# ═══════════════════════════════════════════════════════════════

def fetch_global_data(index: GlobalIndex, period: str = "3mo") -> Optional[Dict]:
    """Fetch OHLCV data for a global index"""
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(index.yf_symbol)
        df = ticker.history(period=period, interval="1d")
        
        if df.empty or len(df) < 10:
            return None
        
        return {
            "opens": df['Open'].tolist(),
            "highs": df['High'].tolist(),
            "lows": df['Low'].tolist(),
            "closes": df['Close'].tolist(),
            "volumes": df['Volume'].tolist(),
            "dates": [d.strftime('%Y-%m-%d') for d in df.index],
        }
    except Exception as e:
        logger.error(f"Fetch error for {index.symbol}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# GLOBAL CANDLESTICK ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_global_candles(index: GlobalIndex) -> Optional[GlobalSignal]:
    """Analyze candle patterns for a global index with buy/sell signal"""
    try:
        data = fetch_global_data(index)
        if not data or len(data["closes"]) < 20:
            return None
        
        closes = data["closes"]
        opens = data["opens"]
        highs = data["highs"]
        lows = data["lows"]
        
        current_price = closes[-1]
        prev_close = closes[-2]
        change_pct = ((current_price - prev_close) / prev_close * 100)
        
        # Import signal engine for technical analysis
        try:
            from buy_sell_engine import (
                calculate_rsi, calculate_macd, calculate_ema,
                calculate_supertrend, detect_candle_pattern_signal,
                calculate_bollinger_bands, calculate_adx
            )
        except ImportError:
            # Fallback basic analysis
            rsi = 50
            candle_pattern = "N/A"
            candle_signal = "NEUTRAL"
            candle_strength = 50
            macd_hist = 0
            st_trend = "NEUTRAL"
            adx = 25
            plus_di = 50
            minus_di = 50
        else:
            rsi = calculate_rsi(closes)
            macd_val, sig_val, macd_hist = calculate_macd(closes)
            ema_9 = calculate_ema(closes, 9)
            ema_21 = calculate_ema(closes, 21)
            st_value, st_trend = calculate_supertrend(highs, lows, closes)
            candle_pattern, candle_signal, candle_strength = detect_candle_pattern_signal(opens, highs, lows, closes)
            adx, plus_di, minus_di = calculate_adx(highs, lows, closes)
        
        # Score the signal
        buy_score = 0
        sell_score = 0
        
        if rsi < 35: buy_score += 2
        elif rsi < 45: buy_score += 1
        elif rsi > 65: sell_score += 2
        elif rsi > 55: sell_score += 1
        
        if macd_hist > 0: buy_score += 1
        else: sell_score += 1
        
        if st_trend == "BULLISH": buy_score += 2
        elif st_trend == "BEARISH": sell_score += 2
        
        if candle_signal == "BUY": buy_score += 1
        elif candle_signal == "SELL": sell_score += 1
        
        if change_pct > 1: buy_score += 1
        elif change_pct < -1: sell_score += 1
        
        if adx > 25 and plus_di > minus_di: buy_score += 1
        elif adx > 25 and minus_di > plus_di: sell_score += 1
        
        total = buy_score + sell_score
        strength = (max(buy_score, sell_score) / max(total, 1)) * 100
        
        if buy_score > sell_score + 1:
            signal = "BUY"
            trend = "BULLISH"
        elif sell_score > buy_score + 1:
            signal = "SELL"
            trend = "BEARISH"
        else:
            signal = "NEUTRAL"
            trend = "SIDEWAYS"
        
        # Currency symbol
        curr_map = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹", "HKD": "HK$", "CNY": "¥", "KRW": "₩", "AUD": "A$"}
        curr = curr_map.get(index.currency, "$")
        
        desc_en = f"{index.name}: {curr}{current_price:,.2f} ({change_pct:+.2f}%) | RSI: {rsi:.0f} | {candle_pattern} | Trend: {trend}"
        desc_hi = f"{index.name_hi}: {curr}{current_price:,.2f} ({change_pct:+.2f}%) | RSI: {rsi:.0f} | {candle_pattern} | ट्रेंड: {trend}"
        
        return GlobalSignal(
            index=index,
            price=current_price,
            change_pct=round(change_pct, 2),
            trend=trend,
            signal=signal,
            strength=round(strength, 1),
            candle_pattern=candle_pattern,
            rsi=round(rsi, 1),
            description=desc_en,
            description_hi=desc_hi,
        )
        
    except Exception as e:
        logger.error(f"Global candle analysis error for {index.symbol}: {e}")
        return None


def analyze_all_global_markets() -> GlobalAnalysis:
    """
    SUPER COMPUTER BRAIN - Analyze ALL global markets
    Returns comprehensive global analysis with India impact
    """
    signals = []
    
    # Analyze all indices
    all_indices = GLOBAL_INDICES + GLOBAL_COMMODITIES
    for index in all_indices:
        try:
            signal = analyze_global_candles(index)
            if signal:
                signals.append(signal)
        except Exception:
            continue
        time.sleep(0.5)  # Rate limit
    
    if not signals:
        return GlobalAnalysis(
            signals=[], overall_sentiment="UNKNOWN",
            india_impact="Insufficient data",
            india_impact_hi="कम डाटा उपलब्ध है",
            correlation_signals=[], timestamp=datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            summary_en="Unable to fetch global data",
            summary_hi="ग्लोबल डाटा नहीं मिल पाया"
        )
    
    # Calculate overall sentiment
    bullish = sum(1 for s in signals if s.signal == "BUY")
    bearish = sum(1 for s in signals if s.signal == "SELL")
    
    if bullish > bearish * 1.5:
        overall = "RISK_ON 🟢"
    elif bearish > bullish * 1.5:
        overall = "RISK_OFF 🔴"
    else:
        overall = "MIXED ⚪"
    
    # Determine India impact
    correlation_signals = []
    
    # US market impact on India
    us_signals = [s for s in signals if s.index.region == GlobalRegion.US and s.index.symbol != "VIX"]
    us_bullish = sum(1 for s in us_signals if s.signal == "BUY")
    us_bearish = sum(1 for s in us_signals if s.signal == "SELL")
    
    if us_bullish > us_bearish:
        correlation_signals.append("🇺🇸 US markets bullish → Positive for India opening")
    elif us_bearish > us_bullish:
        correlation_signals.append("🇺🇸 US markets bearish → Negative for India opening")
    
    # VIX impact
    vix_signal = next((s for s in signals if s.index.symbol == "VIX"), None)
    if vix_signal:
        if vix_signal.price > 30:
            correlation_signals.append(f"⚠️ VIX at {vix_signal.price:.1f} - HIGH FEAR! Caution!")
        elif vix_signal.price > 20:
            correlation_signals.append(f"🟡 VIX at {vix_signal.price:.1f} - Moderate uncertainty")
        else:
            correlation_signals.append(f"🟢 VIX at {vix_signal.price:.1f} - Low fear, markets calm")
    
    # Asia impact
    asia_signals = [s for s in signals if s.index.region == GlobalRegion.ASIA]
    asia_bull = sum(1 for s in asia_signals if s.signal == "BUY")
    asia_bear = sum(1 for s in asia_signals if s.signal == "SELL")
    
    if asia_bull > asia_bear:
        correlation_signals.append("🌏 Asian markets bullish → Supportive for India")
    elif asia_bear > asia_bull:
        correlation_signals.append("🌏 Asian markets bearish → Pressure on India")
    
    # Crude oil impact
    crude_signal = next((s for s in signals if s.index.symbol == "CRUDE"), None)
    if crude_signal:
        if crude_signal.change_pct > 2:
            correlation_signals.append(f"⛽ Crude Oil UP {crude_signal.change_pct:+.1f}% → Negative for India (importer)")
        elif crude_signal.change_pct < -2:
            correlation_signals.append(f"⛽ Crude Oil DOWN {crude_signal.change_pct:+.1f}% → Positive for India (importer)")
    
    # USD/INR impact
    usdinr_signal = next((s for s in signals if s.index.symbol == "USDINR"), None)
    if usdinr_signal:
        if usdinr_signal.change_pct > 0.3:
            correlation_signals.append(f"💱 Rupee weakening ({usdinr_signal.price:.2f}) → FII selling pressure")
        elif usdinr_signal.change_pct < -0.3:
            correlation_signals.append(f"💱 Rupee strengthening ({usdinr_signal.price:.2f}) → FII buying possible")
    
    # Gold impact
    gold_signal = next((s for s in signals if s.index.symbol == "GOLD"), None)
    if gold_signal:
        if gold_signal.signal == "BUY":
            correlation_signals.append(f"🥇 Gold bullish (${gold_signal.price:,.0f}) → Safe haven demand")
    
    # India impact summary
    positive_count = sum(1 for c in correlation_signals if "Positive" in c or "bullish" in c.lower() or "Supportive" in c or "buying" in c)
    negative_count = sum(1 for c in correlation_signals if "Negative" in c or "bearish" in c.lower() or "Pressure" in c or "selling" in c or "FEAR" in c)
    
    if positive_count > negative_count:
        india_impact = "🟢 POSITIVE - Global cues favorable for Indian markets"
        india_impact_hi = "🟢 सकारात्मक - ग्लोबल संकेत भारतीय बाज़ार के लिए अच्छे हैं"
    elif negative_count > positive_count:
        india_impact = "🔴 NEGATIVE - Global cues unfavorable for Indian markets"
        india_impact_hi = "🔴 नकारात्मक - ग्लोबल संकेत भारतीय बाज़ार के लिए बुरे हैं"
    else:
        india_impact = "⚪ MIXED - Global signals are mixed for India"
        india_impact_hi = "⚪ मिला-जुला - ग्लोबल संकेत भारत के लिए मिक्स्ड हैं"
    
    # Build summary
    summary_en = f"Global Sentiment: {overall}\n{india_impact}\n\nMarkets: {bullish} Bullish / {bearish} Bearish / {len(signals) - bullish - bearish} Neutral"
    summary_hi = f"ग्लोबल सेंटीमेंट: {overall}\n{india_impact_hi}\n\nमार्केट: {bullish} तेज़ी / {bearish} मंदी / {len(signals) - bullish - bearish} न्यूट्रल"
    
    return GlobalAnalysis(
        signals=signals,
        overall_sentiment=overall,
        india_impact=india_impact,
        india_impact_hi=india_impact_hi,
        correlation_signals=correlation_signals,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        summary_en=summary_en,
        summary_hi=summary_hi
    )


# ═══════════════════════════════════════════════════════════════
# REGIONAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_us_markets() -> List[GlobalSignal]:
    """Analyze US markets only"""
    signals = []
    us_indices = [i for i in GLOBAL_INDICES if i.region == GlobalRegion.US]
    for idx in us_indices:
        sig = analyze_global_candles(idx)
        if sig:
            signals.append(sig)
        time.sleep(0.5)
    return signals

def analyze_european_markets() -> List[GlobalSignal]:
    """Analyze European markets only"""
    signals = []
    eu_indices = [i for i in GLOBAL_INDICES if i.region == GlobalRegion.EUROPE]
    for idx in eu_indices:
        sig = analyze_global_candles(idx)
        if sig:
            signals.append(sig)
        time.sleep(0.5)
    return signals

def analyze_asian_markets() -> List[GlobalSignal]:
    """Analyze Asian markets only"""
    signals = []
    asia_indices = [i for i in GLOBAL_INDICES if i.region == GlobalRegion.ASIA]
    for idx in asia_indices:
        sig = analyze_global_candles(idx)
        if sig:
            signals.append(sig)
        time.sleep(0.5)
    return signals

def analyze_commodities() -> List[GlobalSignal]:
    """Analyze commodities"""
    signals = []
    for idx in GLOBAL_COMMODITIES:
        sig = analyze_global_candles(idx)
        if sig:
            signals.append(sig)
        time.sleep(0.5)
    return signals


# ═══════════════════════════════════════════════════════════════
# FORMATTING (Hindi + English)
# ═══════════════════════════════════════════════════════════════

def format_global_analysis(analysis: GlobalAnalysis, lang: str = "hi") -> str:
    """Format complete global analysis for Telegram"""
    if not analysis.signals:
        if lang == "hi":
            return "🌍 ग्लोबल डाटा अभी उपलब्ध नहीं है। बाद में कोशिश करें।"
        return "🌍 Global data not available right now. Try later."
    
    if lang == "hi":
        msg = (
            f"{'═' * 30}\n"
            f"🌍 जार्विस ग्लोबल मार्केट ब्रेन\n"
            f"{'═' * 30}\n\n"
            f"🎯 ग्लोबल सेंटीमेंट: {analysis.overall_sentiment}\n"
            f"📊 {analysis.india_impact_hi}\n\n"
        )
        
        # Group by region
        regions = {}
        for s in analysis.signals:
            reg = s.index.region.value
            if reg not in regions:
                regions[reg] = []
            regions[reg].append(s)
        
        for region_name, region_signals in regions.items():
            msg += f"{'─' * 25}\n{region_name}:\n"
            for s in region_signals:
                signal_emoji = "🟢" if s.signal == "BUY" else ("🔴" if s.signal == "SELL" else "⚪")
                change_emoji = "📈" if s.change_pct > 0 else ("📉" if s.change_pct < 0 else "➡️")
                msg += f"  {signal_emoji} {s.index.name_hi}\n"
                msg += f"     {change_emoji} {s.change_pct:+.2f}% | RSI: {s.rsi:.0f}\n"
                msg += f"     🕯️ {s.candle_pattern} | ट्रेंड: {s.trend}\n\n"
        
        # Correlation signals
        if analysis.correlation_signals:
            msg += f"{'─' * 25}\n🔗 भारत पर असर:\n"
            for cs in analysis.correlation_signals:
                msg += f"  {cs}\n"
        
        msg += f"\n⏱️ {analysis.timestamp}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 जार्विस ग्लोबल इंटेलिजेंस\n"
    
    else:
        msg = (
            f"{'═' * 30}\n"
            f"🌍 JARVIS GLOBAL MARKET BRAIN\n"
            f"{'═' * 30}\n\n"
            f"🎯 Global Sentiment: {analysis.overall_sentiment}\n"
            f"📊 {analysis.india_impact}\n\n"
        )
        
        regions = {}
        for s in analysis.signals:
            reg = s.index.region.value
            if reg not in regions:
                regions[reg] = []
            regions[reg].append(s)
        
        for region_name, region_signals in regions.items():
            msg += f"{'─' * 25}\n{region_name}:\n"
            for s in region_signals:
                signal_emoji = "🟢" if s.signal == "BUY" else ("🔴" if s.signal == "SELL" else "⚪")
                change_emoji = "📈" if s.change_pct > 0 else ("📉" if s.change_pct < 0 else "➡️")
                msg += f"  {signal_emoji} {s.index.name}\n"
                msg += f"     {change_emoji} {s.change_pct:+.2f}% | RSI: {s.rsi:.0f}\n"
                msg += f"     🕯️ {s.candle_pattern} | Trend: {s.trend}\n\n"
        
        if analysis.correlation_signals:
            msg += f"{'─' * 25}\n🔗 India Impact:\n"
            for cs in analysis.correlation_signals:
                msg += f"  {cs}\n"
        
        msg += f"\n⏱️ {analysis.timestamp}\n"
        msg += f"{'═' * 30}\n"
        msg += "🤖 JARVIS Global Intelligence\n"
    
    return msg


def format_regional_signals(signals: List[GlobalSignal], title: str, lang: str = "hi") -> str:
    """Format signals for a specific region"""
    if not signals:
        if lang == "hi":
            return f"🌍 {title}\n\nडाटा उपलब्ध नहीं है।"
        return f"🌍 {title}\n\nData not available."
    
    if lang == "hi":
        msg = f"{'═' * 30}\n🌍 {title}\n{'═' * 30}\n\n"
        for s in signals:
            signal_emoji = "🟢" if s.signal == "BUY" else ("🔴" if s.signal == "SELL" else "⚪")
            msg += f"{signal_emoji} {s.index.name_hi}\n"
            msg += f"  💰 {s.price:,.2f} ({s.change_pct:+.2f}%)\n"
            msg += f"  📊 RSI: {s.rsi:.0f} | ट्रेंड: {s.trend}\n"
            msg += f"  🕯️ {s.candle_pattern}\n\n"
        msg += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n{'═' * 30}"
    else:
        msg = f"{'═' * 30}\n🌍 {title}\n{'═' * 30}\n\n"
        for s in signals:
            signal_emoji = "🟢" if s.signal == "BUY" else ("🔴" if s.signal == "SELL" else "⚪")
            msg += f"{signal_emoji} {s.index.name}\n"
            msg += f"  💰 {s.price:,.2f} ({s.change_pct:+.2f}%)\n"
            msg += f"  📊 RSI: {s.rsi:.0f} | Trend: {s.trend}\n"
            msg += f"  🕯️ {s.candle_pattern}\n\n"
        msg += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n{'═' * 30}"
    
    return msg


# ═══════════════════════════════════════════════════════════════
# GLOBAL VS INDIA CORRELATION ENGINE  
# ═══════════════════════════════════════════════════════════════

def get_india_prediction_from_global(lang: str = "hi") -> str:
    """
    Use global market data to predict next India market direction
    """
    try:
        analysis = analyze_all_global_markets()
        
        # Score each factor
        factors = []
        total_score = 0
        
        # US futures/market
        us_signals = [s for s in analysis.signals if s.index.region == GlobalRegion.US and s.index.symbol != "VIX"]
        us_buy = sum(1 for s in us_signals if s.signal == "BUY")
        us_sell = sum(1 for s in us_signals if s.signal == "SELL")
        
        if us_buy > us_sell:
            total_score += 20
            factors.append(("🇺🇸 US मार्केट", "तेज़ी", "+20") if lang == "hi" else ("🇺🇸 US Markets", "Bullish", "+20"))
        elif us_sell > us_buy:
            total_score -= 20
            factors.append(("🇺🇸 US मार्केट", "मंदी", "-20") if lang == "hi" else ("🇺🇸 US Markets", "Bearish", "-20"))
        else:
            factors.append(("🇺🇸 US मार्केट", "मिक्स्ड", "0") if lang == "hi" else ("🇺🇸 US Markets", "Mixed", "0"))
        
        # VIX
        vix = next((s for s in analysis.signals if s.index.symbol == "VIX"), None)
        if vix:
            if vix.price > 30:
                total_score -= 25
                factors.append(("😱 VIX", f"{vix.price:.1f} (HIGH FEAR)", "-25") if lang == "hi" else ("😱 VIX", f"{vix.price:.1f} (HIGH FEAR)", "-25"))
            elif vix.price > 20:
                total_score -= 10
                factors.append(("😟 VIX", f"{vix.price:.1f} (मध्यम)", "-10") if lang == "hi" else ("😟 VIX", f"{vix.price:.1f} (Moderate)", "-10"))
            else:
                total_score += 15
                factors.append(("😊 VIX", f"{vix.price:.1f} (शांत)", "+15") if lang == "hi" else ("😊 VIX", f"{vix.price:.1f} (Calm)", "+15"))
        
        # Asia
        asia_signals = [s for s in analysis.signals if s.index.region == GlobalRegion.ASIA]
        asia_buy = sum(1 for s in asia_signals if s.signal == "BUY")
        asia_sell = sum(1 for s in asia_signals if s.signal == "SELL")
        
        if asia_buy > asia_sell:
            total_score += 15
            factors.append(("🌏 एशिया", "तेज़ी", "+15") if lang == "hi" else ("🌏 Asia", "Bullish", "+15"))
        elif asia_sell > asia_buy:
            total_score -= 15
            factors.append(("🌏 एशिया", "मंदी", "-15") if lang == "hi" else ("🌏 Asia", "Bearish", "-15"))
        
        # Crude
        crude = next((s for s in analysis.signals if s.index.symbol == "CRUDE"), None)
        if crude:
            if crude.change_pct > 3:
                total_score -= 15
                factors.append(("⛽ क्रूड", f"+{crude.change_pct:.1f}% (बुरा)", "-15") if lang == "hi" else ("⛽ Crude", f"+{crude.change_pct:.1f}% (Bad)", "-15"))
            elif crude.change_pct < -3:
                total_score += 10
                factors.append(("⛽ क्रूड", f"{crude.change_pct:.1f}% (अच्छा)", "+10") if lang == "hi" else ("⛽ Crude", f"{crude.change_pct:.1f}% (Good)", "+10"))
        
        # USD/INR
        usdinr = next((s for s in analysis.signals if s.index.symbol == "USDINR"), None)
        if usdinr:
            if usdinr.change_pct > 0.5:
                total_score -= 10
                factors.append(("💱 रुपया", "कमज़ोर", "-10") if lang == "hi" else ("💱 Rupee", "Weakening", "-10"))
            elif usdinr.change_pct < -0.5:
                total_score += 10
                factors.append(("💱 रुपया", "मज़बूत", "+10") if lang == "hi" else ("💱 Rupee", "Strengthening", "+10"))
        
        # Final prediction
        if total_score > 30:
            prediction = "🟢🟢 STRONG BULLISH"
            prediction_hi = "🟢🟢 बहुत तेज़ी!"
        elif total_score > 10:
            prediction = "🟢 BULLISH"
            prediction_hi = "🟢 तेज़ी"
        elif total_score > -10:
            prediction = "⚪ NEUTRAL / SIDEWAYS"
            prediction_hi = "⚪ न्यूट्रल / साइडवेज़"
        elif total_score > -30:
            prediction = "🔴 BEARISH"
            prediction_hi = "🔴 मंदी"
        else:
            prediction = "🔴🔴 STRONG BEARISH"
            prediction_hi = "🔴🔴 बहुत मंदी!"
        
        if lang == "hi":
            msg = (
                f"{'═' * 30}\n"
                f"🔮 जार्विस भारत मार्केट प्रेडिक्शन\n"
                f"(ग्लोबल डाटा से)\n"
                f"{'═' * 30}\n\n"
                f"🎯 प्रेडिक्शन: {prediction_hi}\n"
                f"📊 स्कोर: {total_score:+d}/100\n\n"
                f"{'─' * 25}\n"
                f"📋 फैक्टर्स:\n"
            )
            for name, status, score in factors:
                msg += f"  {name}: {status} ({score})\n"
            
            msg += (
                f"\n{'─' * 25}\n"
                f"💡 सलाह:\n"
            )
            if total_score > 20:
                msg += "  ✅ ग्लोबल संकेत अच्छे हैं - Buy on dips!\n"
            elif total_score < -20:
                msg += "  ⚠️ ग्लोबल संकेत बुरे हैं - सावधानी बरतें!\n"
            else:
                msg += "  🔄 मिक्स्ड संकेत - Stock picking करें, ब्लाइंड ना खरीदें\n"
            
            msg += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n"
            msg += f"{'═' * 30}\n"
            msg += "🤖 जार्विस ग्लोबल इंटेलिजेंस\n"
        else:
            msg = (
                f"{'═' * 30}\n"
                f"🔮 JARVIS India Market Prediction\n"
                f"(From Global Data)\n"
                f"{'═' * 30}\n\n"
                f"🎯 Prediction: {prediction}\n"
                f"📊 Score: {total_score:+d}/100\n\n"
                f"{'─' * 25}\n"
                f"📋 Factors:\n"
            )
            for name, status, score in factors:
                msg += f"  {name}: {status} ({score})\n"
            
            msg += (
                f"\n{'─' * 25}\n"
                f"💡 Advice:\n"
            )
            if total_score > 20:
                msg += "  ✅ Global cues positive - Buy on dips!\n"
            elif total_score < -20:
                msg += "  ⚠️ Global cues negative - Exercise caution!\n"
            else:
                msg += "  🔄 Mixed signals - Stock pick, don't buy blind\n"
            
            msg += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n"
            msg += f"{'═' * 30}\n"
            msg += "🤖 JARVIS Global Intelligence\n"
        
        return msg
        
    except Exception as e:
        logger.error(f"India prediction error: {e}")
        if lang == "hi":
            return f"❌ प्रेडिक्शन में एरर: {e}"
        return f"❌ Prediction error: {e}"


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'GlobalRegion', 'GlobalIndex', 'GlobalSignal', 'GlobalAnalysis',
    'GLOBAL_INDICES', 'GLOBAL_COMMODITIES',
    'fetch_global_data', 'analyze_global_candles',
    'analyze_all_global_markets',
    'analyze_us_markets', 'analyze_european_markets',
    'analyze_asian_markets', 'analyze_commodities',
    'format_global_analysis', 'format_regional_signals',
    'get_india_prediction_from_global',
]
