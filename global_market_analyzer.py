"""
Global Market Trend Analyzer
Tracks worldwide stock markets and Twitter sentiment to predict Indian market direction.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import os
from datetime import datetime, timedelta

# Global market indices and their correlation with Indian markets
GLOBAL_INDICES = {
    "US_NASDAQ": "^IXIC",      # Tech-heavy, high correlation with Nifty 50
    "US_SP500": "^GSPC",       # Broad US market
    "US_DOW": "^DJI",          # Dow Jones
    "EUR_DAX": "^GDAXI",       # Germany (Europe health)
    "UK_FTSE": "^FTSE",        # London Stock Exchange
    "ASIA_NIKKEI": "^N225",    # Japan (Asia sentiment)
    "ASIA_HSI": "^HSI",        # Hong Kong (China sentiment)
    "ASIA_SSE": "000001.SS",   # Shanghai (China economy)
    "NIFTY": "^NSEI",          # India reference
    "SENSEX": "^BSESN",        # India reference
    "OIL_WTI": "CL=F",         # Crude oil (global momentum)
    "GOLD": "GC=F",            # Gold (risk-off indicator)
    "VIX": "^VIX",             # US volatility (fear index)
}


def fetch_global_market_data(lookback_days: int = 30) -> Dict:
    """
    Fetch recent performance of global indices.
    Returns dict with direction (UP/DOWN), % change, and strength.
    Uses a longer lookback period (30 days) to ensure we get data.
    """
    results = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    for name, ticker in GLOBAL_INDICES.items():
        try:
            # Use period parameter instead of start/end for more reliable fetching
            data = yf.download(ticker, period="1mo", progress=False, repair=True)
            
            if data.empty or len(data) < 2:
                print(f"  {name}: No data")
                continue
            
            opening = float(data['Close'].iloc[0])
            closing = float(data['Close'].iloc[-1])
            
            if opening == 0 or closing == 0:
                print(f"  {name}: Invalid prices")
                continue
            
            pct_change = ((closing - opening) / opening) * 100
            
            direction = "📈 UP" if pct_change > 0 else "📉 DOWN"
            strength = abs(pct_change)
            
            results[name] = {
                "direction": direction,
                "pct_change": float(pct_change),
                "strength": float(strength),
                "price": float(closing),
                "opening": float(opening),
            }
            print(f"  ✓ {name}: {direction} {pct_change:.2f}%")
        except Exception as e:
            print(f"  {name}: Error - {str(e)[:50]}")
            results[name] = {"error": str(e)}
    
    return results


def analyze_global_sentiment(market_data: Dict) -> Tuple[str, float, str]:
    """
    Analyze global market sentiment based on available indices.
    Returns (sentiment: BULLISH/BEARISH/NEUTRAL, confidence: 0-1, reasoning: str)
    """
    if not market_data:
        return "⚪ NEUTRAL", 0.5, "Waiting for market data..."
    
    # Filter for valid data
    valid_data = {k: v for k, v in market_data.items() if "error" not in v}
    
    if not valid_data:
        return "⚪ NEUTRAL", 0.5, "Market data unavailable. Please try again."
    
    # Score each market
    bullish_count = 0
    bearish_count = 0
    total_strength = 0
    avg_change = 0
    
    for market, data in valid_data.items():
        pct_change = data.get('pct_change', 0)
        
        if pct_change > 0.5:
            bullish_count += 1
        elif pct_change < -0.5:
            bearish_count += 1
        
        total_strength += abs(pct_change)
        avg_change += pct_change
    
    num_markets = len(valid_data)
    avg_change = avg_change / num_markets if num_markets > 0 else 0
    
    # Decision logic simplified for fewer indices
    if bullish_count >= 2 and avg_change > 0.5:
        sentiment = "🟢 BULLISH"
        confidence = min(0.85, 0.5 + (bullish_count / (num_markets * 2)))
        reasoning = f"Global markets showing positive momentum. {bullish_count} of {num_markets} indices in uptrend."
    elif bearish_count >= 2 and avg_change < -0.5:
        sentiment = "🔴 BEARISH"
        confidence = min(0.85, 0.5 + (bearish_count / (num_markets * 2)))
        reasoning = f"Global markets showing weakness. {bearish_count} of {num_markets} indices in downtrend."
    elif bullish_count > bearish_count:
        sentiment = "🟡 MODERATELY BULLISH"
        confidence = 0.6
        reasoning = f"More indices up than down. {bullish_count} positive, {bearish_count} negative. Mixed signals."
    elif bearish_count > bullish_count:
        sentiment = "🟠 MODERATELY BEARISH"
        confidence = 0.6
        reasoning = f"More indices down than up. {bearish_count} negative, {bullish_count} positive. Caution advised."
    else:
        sentiment = "⚪ NEUTRAL"
        confidence = 0.5
        reasoning = "Global markets mixed. No clear direction observed."
    
    return sentiment, confidence, reasoning


def get_indian_market_direction_forecast() -> Dict:
    """
    Combined analysis for Indian market based on global trends.
    Fast version using simple price fetch.
    """
    market_data = {}
    
    # Critical indices for analysis
    critical_indices = {
        "US_NASDAQ": "^IXIC",
        "ASIA_NIKKEI": "^N225",
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
    }
    
    try:
        import requests
        # Try direct fetch of index values
        for name, ticker in critical_indices.items():
            try:
                # Simple approach: use yfinance Ticker object
                tick = yf.Ticker(ticker)
                
                # Get historical data
                hist = tick.history(period="30d")
                
                if len(hist) >= 2:
                    opening = float(hist['Close'].iloc[0])
                    closing = float(hist['Close'].iloc[-1])
                    
                    if opening > 0 and closing > 0:
                        pct_change = float(((closing - opening) / opening) * 100)
                        direction = "📈 UP" if pct_change > 0 else "📉 DOWN"
                        
                        market_data[name] = {
                            "direction": direction,
                            "pct_change": pct_change,
                            "strength": float(abs(pct_change)),
                            "price": closing,
                        }
                        print(f"✓ {name}: {direction} {pct_change:.2f}%")
            except Exception as e:
                print(f"✗ {name}: {str(e)[:50]}")
                pass
    except Exception as e:
        print(f"Error in data fetch: {str(e)}")
        pass
    
    global_sentiment, confidence, reasoning = analyze_global_sentiment(market_data)
    
    # Extract Nifty and Sensex current data
    nifty_data = market_data.get("NIFTY", {})
    sensex_data = market_data.get("SENSEX", {})
    
    # Build forecast
    forecast = {
        "timestamp": datetime.now().isoformat(),
        "global_sentiment": global_sentiment,
        "confidence": confidence,
        "reasoning": reasoning,
        "nifty_trend": nifty_data.get("direction", "❓"),
        "sensex_trend": sensex_data.get("direction", "❓"),
        "nifty_change": nifty_data.get("pct_change", 0),
        "sensex_change": sensex_data.get("pct_change", 0),
        "recommendation": _generate_recommendation(global_sentiment, confidence),
        "market_summary": _format_market_summary(market_data),
    }
    
    return forecast


def _generate_recommendation(sentiment: str, confidence: float) -> str:
    """Generate trading recommendation based on sentiment and confidence."""
    if "BULLISH" in sentiment:
        if confidence > 0.70:
            return "🚀 **BUY** - Strong upside expected. Consider going LONG on dips."
        else:
            return "✅ **BUY on weakness** - Cautiously bullish. Conservative buyers may wait for pullback."
    elif "BEARISH" in sentiment:
        if confidence > 0.70:
            return "🔴 **SELL/AVOID** - Strong downside risk. Consider hedging or staying in CASH."
        else:
            return "⚠️ **AVOID LONG** - Cautious outlook. Exit longs, prepare for downside."
    else:
        return "⏸️ **HOLD/WAIT** - No clear direction. Use range-trading strategies or wait for breakout."


def _format_market_summary(market_data: Dict) -> str:
    """Format market data into readable summary."""
    summary = []
    
    key_markets = ["US_NASDAQ", "US_SP500", "ASIA_NIKKEI", "ASIA_HSI", "VIX", "OIL_WTI"]
    
    found_any = False
    for market in key_markets:
        if market in market_data and "error" not in market_data[market]:
            data = market_data[market]
            direction = data['direction']
            change = data['pct_change']
            
            # Format change with color
            if change > 0:
                change_str = f"+{change:.2f}%"
            else:
                change_str = f"{change:.2f}%"
            
            summary.append(f"{market}: {direction} {change_str}")
            found_any = True
    
    if not found_any:
        return "(Market data loading... please retry)"
    
    return "\n".join(summary)


def get_market_trend_analysis() -> str:
    """
    Main function to generate comprehensive market trend analysis.
    Returns formatted string for Telegram bot.
    """
    try:
        import sys
        print("Fetching global market data...", file=sys.stderr)
        
        forecast = get_indian_market_direction_forecast()
        
        message = []
        message.append("🌍 *GLOBAL MARKET ANALYSIS FOR INDIAN MARKETS*\n")
        message.append("=" * 50)
        message.append(f"📊 Global Sentiment: {forecast['global_sentiment']}")
        message.append(f"📈 Confidence: {forecast['confidence']:.0%}\n")
        
        message.append("*Global Market Snapshot:*")
        
        # Add market summary with proper formatting
        snapshot = forecast['market_summary']
        if snapshot.strip():
            message.append(snapshot)
        else:
            message.append("(Fetching live data...)")
        message.append("")
        
        message.append("*Indian Market Status:*")
        message.append(f"NIFTY 50: {forecast['nifty_trend']} ({forecast['nifty_change']:+.2f}%)")
        message.append(f"SENSEX: {forecast['sensex_trend']} ({forecast['sensex_change']:+.2f}%)")
        message.append("")
        
        message.append("*Analysis:*")
        message.append(forecast['reasoning'])
        message.append("")
        
        message.append("*Recommendation:*")
        message.append(forecast['recommendation'])
        message.append("")
        
        message.append(f"⏰ Updated: {forecast['timestamp'][:10]} {forecast['timestamp'][11:16]}")
        
        result = "\n".join(message)
        print(f"Market analysis complete: {len(result)} chars", file=sys.stderr)
        return result
        
    except Exception as e:
        import traceback
        import sys
        traceback.print_exc(file=sys.stderr)
        return f"❌ Market trend analysis error: {str(e)}\n\nTrying again in a moment..."


if __name__ == "__main__":
    print(get_market_trend_analysis())
