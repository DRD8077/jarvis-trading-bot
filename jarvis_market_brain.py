"""
🧠⚡ JARVIS MARKET BRAIN — Intelligent Market Separator + Deep AI/ML Engine
════════════════════════════════════════════════════════════════════════════
Understands the difference between:
  📈 INDIAN STOCK MARKET — NIFTY, SENSEX, Bank Nifty, Indian stocks
  🪙 CRYPTO MARKET — Bitcoin, Ethereum, CoinDCX tokens, DexTools pairs

For Indian Stocks:
  - 250+ ML features via index_data.py
  - 6-model stacking ensemble (RF, ExtraTrees, GB, XGB, LGBM, LSTM)
  - 43 candlestick patterns
  - India-specific sentiment (7 RSS feeds, Fear & Greed, FII/DII)
  - Global cross-asset correlation (Gold, DXY, VIX, Crude, USD/INR)
  - Option chain analysis (PCR, Max Pain, IV Skew)
  - Multi-timeframe confluence

For Crypto:
  - 10+ real-time technical indicators
  - Rug Risk + Whale Detection + Liquidity Health
  - Smart Money Flow + Price Targets
  - ML prediction (RF + GB ensemble on OHLCV)
  - 25+ crypto candle patterns
  - Token-specific deep analysis (reply-based)
  - World's best indicators combined

Reply-Based Deep Token Analysis:
  - User replies to any crypto message → JARVIS analyzes that token deeply
  - 15+ indicators, ML prediction, candle patterns, price targets, risk analysis
  - Hindi verdict with full Entry/Target/SL

Author: JARVIS Intelligence Core
"""

import re
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("jarvis_brain")


# ═══════════════════════════════════════════════
#  MARKET TYPE DETECTOR — Indian Stocks vs Crypto
# ═══════════════════════════════════════════════

# Indian stock keywords
INDIAN_STOCK_KEYWORDS = {
    'nifty', 'sensex', 'bank nifty', 'banknifty', 'nse', 'bse',
    'nifty50', 'nifty 50', 'index', 'stock market', 'share market',
    'indian market', 'india market', 'nifty signals', 'sensex signals',
    'option chain', 'options', 'call option', 'put option', 'ce', 'pe', 'otm', 'itm',
    'expiry', 'weekly expiry', 'monthly expiry',
    'fii', 'dii', 'fii dii', 'foreign investor',
    'sebi', 'rbi', 'budget', 'union budget',
    'reliance', 'tcs', 'infosys', 'hdfc', 'icici', 'sbi', 'wipro', 'hul',
    'adani', 'tata', 'bharti', 'airtel', 'itc', 'kotak', 'axis',
    'bajaj', 'maruti', 'lt', 'larsen', 'nestle', 'asian paints',
    'titan', 'ultratech', 'hcl tech', 'tech mahindra', 'cipla', 'dr reddy',
    'power grid', 'ntpc', 'ongc', 'coal india', 'bhel',
    'stock', 'share', 'equity', 'mutual fund', 'sip',
    'demat', 'zerodha', 'groww', 'upstox', 'angel one',
    'intraday', 'delivery', 'swing trade',
    'support resistance', 'fibonacci',
    'market open', 'market close', 'pre-market',
    'quarter result', 'earnings', 'dividend',
    'ipo', 'listing',
}

# Crypto keywords
CRYPTO_KEYWORDS = {
    'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
    'crypto', 'cryptocurrency', 'blockchain', 'web3', 'defi', 'dex',
    'token', 'coin', 'altcoin', 'meme coin', 'memecoin',
    'binance', 'coinbase', 'coindcx', 'dextools',
    'swap', 'liquidity', 'pool', 'staking', 'yield', 'farming',
    'nft', 'metaverse', 'gamefi', 'play to earn',
    'wallet', 'phantom', 'metamask', 'trust wallet',
    'airdrop', 'rug pull', 'whale', 'pump', 'dump',
    'doge', 'dogecoin', 'shib', 'shiba', 'pepe', 'bonk', 'floki',
    'bnb', 'xrp', 'ripple', 'ada', 'cardano', 'dot', 'polkadot',
    'avax', 'avalanche', 'matic', 'polygon', 'link', 'chainlink',
    'uni', 'uniswap', 'aave', 'compound', 'maker', 'dai',
    'usdt', 'usdc', 'busd', 'tether',
    'sui', 'sei', 'apt', 'aptos', 'arb', 'arbitrum', 'op', 'optimism',
    'inj', 'injective', 'ton', 'toncoin', 'near', 'atom', 'cosmos',
    'fil', 'filecoin', 'render', 'rndr', 'fet', 'fetch',
    'hbar', 'hedera', 'algo', 'algorand', 'trx', 'tron',
    'ltc', 'litecoin', 'bch', 'bitcoin cash',
    'dexscreener', 'pump.fun', 'raydium', 'jupiter',
    'moonshot', 'rocket', '100x', '50x', '10x',
    'market cap', 'mcap', 'volume', 'circulating supply',
}

# CoinDCX known symbols (top 200)
COINDCX_SYMBOLS = {
    'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'BNB', 'SUI', 'AVAX', 'DOT',
    'LINK', 'MATIC', 'SHIB', 'PEPE', 'TON', 'NEAR', 'UNI', 'ATOM', 'FIL', 'ARB',
    'OP', 'INJ', 'BONK', 'FLOKI', 'HBAR', 'ALGO', 'FET', 'RENDER', 'TRX', 'LTC',
    'BCH', 'APT', 'SEI', 'IMX', 'SAND', 'MANA', 'AXS', 'GALA', 'ENJ', 'FLOW',
    'CHZ', 'GMT', 'APE', 'BLUR', 'CRV', 'SNX', 'COMP', 'MKR', 'AAVE', 'LDO',
    'RUNE', 'GRT', 'FTM', 'KAVA', 'ONE', 'ZIL', 'ICX', 'IOTA', 'XTZ', 'EOS',
    'NEO', 'QTUM', 'ZEC', 'DASH', 'XMR', 'YFI', 'SUSHI', 'BAL', 'DYDX', 'ENS',
    'WOO', 'SSV', 'RPL', 'PENDLE', 'RNDR', 'OCEAN', 'AGIX', 'TAO', 'WLD', 'AI16Z',
    'JASMY', 'CELO', 'SKL', 'AUDIO', 'ANKR', 'STORJ', 'AR', 'KDA', 'CFX', 'ACH',
    'VET', 'THETA', 'EGLD', 'STX', 'ICP', 'ROSE', 'MINA', 'KSM',
}


def detect_market_type(text: str) -> str:
    """
    Detect if user is asking about Indian Stock Market or Crypto Market.
    Returns: 'indian_stock', 'crypto', 'both', or 'unknown'
    """
    text_lower = text.lower().strip()
    
    stock_score = 0
    crypto_score = 0
    
    # Check keyword matches
    for kw in INDIAN_STOCK_KEYWORDS:
        if kw in text_lower:
            stock_score += 2 if len(kw) > 5 else 1
    
    for kw in CRYPTO_KEYWORDS:
        if kw in text_lower:
            crypto_score += 2 if len(kw) > 5 else 1
    
    # Check for CoinDCX symbols (uppercase words)
    words = text.upper().split()
    for w in words:
        clean = w.strip('$,.:!?')
        if clean in COINDCX_SYMBOLS:
            crypto_score += 3
    
    # Specific Indian market phrases
    if any(p in text_lower for p in ['nifty', 'sensex', 'bank nifty', 'nse', 'bse', 'option chain']):
        stock_score += 5
    
    # Specific crypto phrases
    if any(p in text_lower for p in ['bitcoin', 'crypto', 'token', 'blockchain', 'web3', 'defi']):
        crypto_score += 5
    
    # INR amounts with stock context
    if '₹' in text or 'inr' in text_lower:
        if any(w in text_lower for w in ['nifty', 'sensex', 'stock', 'share']):
            stock_score += 3
    
    if stock_score > 0 and crypto_score == 0:
        return 'indian_stock'
    elif crypto_score > 0 and stock_score == 0:
        return 'crypto'
    elif stock_score > 0 and crypto_score > 0:
        return 'both' if abs(stock_score - crypto_score) < 3 else ('indian_stock' if stock_score > crypto_score else 'crypto')
    else:
        return 'unknown'


def extract_token_from_message(text: str) -> Optional[str]:
    """Extract crypto token symbol from a message (for reply analysis)."""
    if not text:
        return None
    
    # Pattern 1: $SYMBOL
    match = re.search(r'\$([A-Z]{2,10})', text)
    if match:
        return match.group(1)
    
    # Pattern 2: Bold **SYMBOL** or *SYMBOL*
    match = re.search(r'\*\*?([A-Z]{2,10})\*\*?', text)
    if match and match.group(1) in COINDCX_SYMBOLS:
        return match.group(1)
    
    # Pattern 3: Known symbols appearing in text (search for pattern like "TOKEN — ₹" or "TOKEN (")
    for sym in COINDCX_SYMBOLS:
        patterns = [
            f'{sym} —', f'{sym} (', f'{sym}*', f'*{sym}*',
            f'{sym}\n', f'{sym} at', f'{sym} price',
            f'/cdx {sym}', f'/invest {sym}',
        ]
        for p in patterns:
            if p in text:
                return sym
    
    # Pattern 4: First word that looks like a crypto symbol
    words = text.upper().split()
    for w in words:
        clean = re.sub(r'[^A-Z]', '', w)
        if clean in COINDCX_SYMBOLS:
            return clean
    
    return None


def extract_token_from_reply(original_message: str, user_question: str) -> Optional[str]:
    """Extract token symbol when user replies to a previous bot message."""
    # Try extracting from the original message first
    token = extract_token_from_message(original_message)
    if token:
        return token
    
    # Try extracting from user's question
    token = extract_token_from_message(user_question)
    return token


# ═══════════════════════════════════════════════
#  INDIAN STOCK MARKET — Deep AI/ML Analysis
# ═══════════════════════════════════════════════

def analyze_indian_stock_deep(query: str) -> Dict:
    """
    Deep AI/ML analysis for Indian Stock Market questions.
    Combines: Technical Analysis + ML Prediction + Sentiment + News + Candles
    """
    result = {
        'type': 'indian_stock',
        'query': query,
        'timestamp': datetime.now().strftime("%H:%M IST"),
        'sections': [],
    }
    
    # Detect which index/stock
    query_lower = query.lower()
    is_nifty = any(w in query_lower for w in ['nifty', 'nifty50', 'nifty 50'])
    is_sensex = any(w in query_lower for w in ['sensex', 'bse'])
    is_banknifty = any(w in query_lower for w in ['banknifty', 'bank nifty'])
    
    if not (is_nifty or is_sensex or is_banknifty):
        # Default to both
        is_nifty = True
        is_sensex = True
    
    # 1. CANDLE PATTERN ANALYSIS
    try:
        from candle_analyzer import analyze_index
        
        if is_nifty:
            nifty_analysis = analyze_index("^NSEI", "NIFTY 50")
            if nifty_analysis and 'error' not in nifty_analysis:
                result['sections'].append({
                    'title': '🔱 NIFTY 50 — Candle Pattern + 12-Factor AI',
                    'data': nifty_analysis,
                    'type': 'candle_analysis'
                })
        
        if is_sensex:
            sensex_analysis = analyze_index("^BSESN", "SENSEX")
            if sensex_analysis and 'error' not in sensex_analysis:
                result['sections'].append({
                    'title': '🔱 SENSEX — Candle Pattern + 12-Factor AI',
                    'data': sensex_analysis,
                    'type': 'candle_analysis'
                })
        
        if is_banknifty:
            bn_analysis = analyze_index("^NSEBANK", "BANK NIFTY")
            if bn_analysis and 'error' not in bn_analysis:
                result['sections'].append({
                    'title': '🏦 BANK NIFTY — Candle Pattern + 12-Factor AI',
                    'data': bn_analysis,
                    'type': 'candle_analysis'
                })
    except Exception as e:
        logger.error(f"[BRAIN] Candle analysis error: {e}")
    
    # 2. ML PREDICTION (6-model ensemble)
    try:
        from ml_predictor import predict_index_direction, format_ml_prediction
        
        if is_nifty:
            ml_pred = predict_index_direction("^NSEI", "NIFTY 50")
            if ml_pred and 'error' not in ml_pred:
                result['sections'].append({
                    'title': '🤖 NIFTY ML Prediction (6-Model Ensemble)',
                    'data': ml_pred,
                    'type': 'ml_prediction',
                    'formatted': format_ml_prediction(ml_pred)
                })
        
        if is_sensex:
            ml_pred = predict_index_direction("^BSESN", "SENSEX")
            if ml_pred and 'error' not in ml_pred:
                result['sections'].append({
                    'title': '🤖 SENSEX ML Prediction (6-Model Ensemble)',
                    'data': ml_pred,
                    'type': 'ml_prediction',
                    'formatted': format_ml_prediction(ml_pred)
                })
    except Exception as e:
        logger.error(f"[BRAIN] ML prediction error: {e}")
    
    # 3. NEWS SENTIMENT + FEAR & GREED
    try:
        from sentiment_engine import analyze_news_sentiment, calculate_fear_greed_index
        
        sentiment = analyze_news_sentiment()
        if sentiment:
            result['sections'].append({
                'title': '📰 Market Sentiment — News + FII/DII',
                'data': sentiment,
                'type': 'sentiment'
            })
        
        fg = calculate_fear_greed_index()
        if fg:
            result['sections'].append({
                'title': '😱📊 Fear & Greed Index',
                'data': fg,
                'type': 'fear_greed'
            })
    except Exception as e:
        logger.error(f"[BRAIN] Sentiment error: {e}")
    
    # 4. OPTION CHAIN ANALYSIS
    try:
        from stock_data_fetcher import fetch_nse_option_chain, parse_option_chain_json, analyze_option_chain
        
        if is_nifty:
            oc_raw = fetch_nse_option_chain("NIFTY")
            if oc_raw:
                calls_df, puts_df, underlying = parse_option_chain_json(oc_raw)
                if calls_df is not None and not calls_df.empty:
                    oc_analysis = analyze_option_chain(calls_df, puts_df, underlying)
                    result['sections'].append({
                        'title': '📋 NIFTY Option Chain — PCR + Max Pain + IV',
                        'data': oc_analysis,
                        'type': 'option_chain'
                    })
    except Exception as e:
        logger.error(f"[BRAIN] Option chain error: {e}")
    
    return result


def format_indian_stock_report(data: Dict) -> List[str]:
    """Format comprehensive Indian stock analysis into Telegram messages."""
    pages = []
    
    # Header
    lines = [
        f"{'═'*30}",
        f"📈🇮🇳 *JARVIS — INDIAN STOCK MARKET AI*",
        f"{'═'*30}",
        f"🕐 {data.get('timestamp', '')}",
        f"",
    ]
    
    for section in data.get('sections', []):
        title = section['title']
        stype = section['type']
        sdata = section['data']
        
        if stype == 'candle_analysis':
            lines.append(f"{'─'*28}")
            lines.append(f"*{title}*")
            lines.append(f"{'─'*28}")
            
            if isinstance(sdata, dict):
                # Core signal
                signal = sdata.get('signal', 'N/A')
                confidence = sdata.get('confidence', 0)
                direction = sdata.get('direction', 'NEUTRAL')
                
                lines.append(f"📊 *Signal:* {signal}")
                lines.append(f"🎯 *Direction:* {direction}")
                lines.append(f"💪 *Confidence:* {confidence:.0f}%")
                
                # Price
                price = sdata.get('current_price', sdata.get('price', 0))
                if price:
                    lines.append(f"💰 *Price:* ₹{price:,.2f}")
                
                # Key indicators
                ta = sdata.get('technical_analysis', sdata.get('indicators', {}))
                if isinstance(ta, dict):
                    if ta.get('rsi'):
                        lines.append(f"  📉 RSI(14): {ta['rsi']:.1f}")
                    if ta.get('macd_signal'):
                        lines.append(f"  📊 MACD: {ta.get('macd_signal', 'N/A')}")
                    if ta.get('ema_signal'):
                        lines.append(f"  📈 EMA: {ta.get('ema_signal', 'N/A')}")
                    if ta.get('adx'):
                        lines.append(f"  💪 ADX: {ta['adx']:.1f}")
                    if ta.get('supertrend_signal'):
                        lines.append(f"  🔮 Supertrend: {ta.get('supertrend_signal', 'N/A')}")
                
                # Candle patterns
                patterns = sdata.get('patterns', sdata.get('candlestick_patterns', []))
                if patterns:
                    lines.append(f"")
                    lines.append(f"🕯️ *Candle Patterns:*")
                    for p in patterns[:5]:
                        if isinstance(p, dict):
                            lines.append(f"  {'🟢' if p.get('type') == 'bullish' else '🔴' if p.get('type') == 'bearish' else '⚪'} {p.get('name', 'Unknown')}")
                        elif hasattr(p, 'name'):
                            lines.append(f"  {'🟢' if p.pattern_type == 'bullish' else '🔴' if p.pattern_type == 'bearish' else '⚪'} {p.name}")
                        else:
                            lines.append(f"  • {p}")
                
                # Levels
                support = sdata.get('support') or sdata.get('support_level')
                resistance = sdata.get('resistance') or sdata.get('resistance_level')
                if support: lines.append(f"  🟢 Support: ₹{support:,.2f}" if isinstance(support, (int, float)) else f"  🟢 Support: {support}")
                if resistance: lines.append(f"  🔴 Resistance: ₹{resistance:,.2f}" if isinstance(resistance, (int, float)) else f"  🔴 Resistance: {resistance}")
                
                # Verdict
                verdict = sdata.get('verdict', sdata.get('recommendation', ''))
                if verdict:
                    lines.append(f"")
                    lines.append(f"🎯 *Verdict:* {verdict}")
            
            elif isinstance(sdata, str):
                lines.append(sdata)
            
            lines.append(f"")
        
        elif stype == 'ml_prediction':
            formatted = section.get('formatted', '')
            if formatted:
                lines.append(f"{'─'*28}")
                lines.append(f"*{title}*")
                lines.append(f"{'─'*28}")
                # Add formatted ML text (may be multi-line)
                lines.append(formatted[:1500])  # Limit length
                lines.append(f"")
        
        elif stype == 'sentiment':
            lines.append(f"{'─'*28}")
            lines.append(f"*{title}*")
            lines.append(f"{'─'*28}")
            if isinstance(sdata, dict):
                overall = sdata.get('overall_sentiment', sdata.get('sentiment', 'N/A'))
                score = sdata.get('overall_score', sdata.get('score', 0))
                lines.append(f"📰 Overall: {overall} ({score:+.2f})" if isinstance(score, float) else f"📰 Overall: {overall}")
                
                headlines = sdata.get('headlines', sdata.get('top_headlines', []))
                if headlines:
                    lines.append(f"📰 *Top Headlines:*")
                    for h in headlines[:5]:
                        if isinstance(h, dict):
                            lines.append(f"  • {h.get('headline', h.get('title', ''))[:80]}")
                        else:
                            lines.append(f"  • {str(h)[:80]}")
            lines.append(f"")
        
        elif stype == 'fear_greed':
            lines.append(f"{'─'*28}")
            lines.append(f"*{title}*")
            lines.append(f"{'─'*28}")
            if isinstance(sdata, dict):
                index_val = sdata.get('index', sdata.get('value', 0))
                label = sdata.get('label', sdata.get('classification', 'N/A'))
                lines.append(f"😱 Fear & Greed: *{index_val:.0f}/100 — {label}*")
                
                components = sdata.get('components', {})
                if isinstance(components, dict):
                    for k, v in components.items():
                        if isinstance(v, dict):
                            lines.append(f"  {k}: {v.get('value', v.get('score', 'N/A'))}")
                        else:
                            lines.append(f"  {k}: {v}")
            lines.append(f"")
        
        elif stype == 'option_chain':
            lines.append(f"{'─'*28}")
            lines.append(f"*{title}*")
            lines.append(f"{'─'*28}")
            if isinstance(sdata, dict):
                pcr = sdata.get('pcr', sdata.get('put_call_ratio', 0))
                max_pain = sdata.get('max_pain', 0)
                signal = sdata.get('signal', sdata.get('oc_signal', 'N/A'))
                lines.append(f"📊 PCR: {pcr:.2f}" if isinstance(pcr, (int, float)) else f"📊 PCR: {pcr}")
                if max_pain: lines.append(f"💀 Max Pain: ₹{max_pain:,.0f}" if isinstance(max_pain, (int, float)) else f"💀 Max Pain: {max_pain}")
                lines.append(f"🎯 Signal: {signal}")
                
                support = sdata.get('support_level', sdata.get('support', 0))
                resistance = sdata.get('resistance_level', sdata.get('resistance', 0))
                if support: lines.append(f"🟢 OI Support: ₹{support:,.0f}" if isinstance(support, (int, float)) else f"🟢 OI Support: {support}")
                if resistance: lines.append(f"🔴 OI Resistance: ₹{resistance:,.0f}" if isinstance(resistance, (int, float)) else f"🔴 OI Resistance: {resistance}")
            lines.append(f"")
        
        # Page splitting (Telegram 4096 char limit)
        current = "\n".join(lines)
        if len(current) > 3500:
            pages.append(current)
            lines = [f"📈🇮🇳 *JARVIS — Indian Market (continued)*\n"]
    
    # Final disclaimer
    lines.extend([
        f"{'─'*28}",
        f"⚠️ *Disclaimer:* Ye JARVIS AI analysis hai, financial advice nahi.",
        f"Risk manage karo, stop loss zaroor lagao!",
        f"🤖 _JARVIS Indian Market Intelligence_",
    ])
    
    pages.append("\n".join(lines))
    return pages


def format_indian_stock_voice(data: Dict) -> str:
    """Hindi voice summary for Indian stock analysis."""
    sections = data.get('sections', [])
    parts = ["Boss, Indian stock market ka AI analysis ready hai!"]
    
    for s in sections:
        if s['type'] == 'candle_analysis':
            d = s['data']
            if isinstance(d, dict):
                signal = d.get('signal', '')
                name = s['title'].split('—')[0].strip() if '—' in s['title'] else 'Index'
                direction = d.get('direction', 'NEUTRAL')
                if 'BUY' in str(signal).upper() or direction == 'BULLISH':
                    parts.append(f"{name} mein bullish signal hai! Buy call ka mauqa!")
                elif 'SELL' in str(signal).upper() or direction == 'BEARISH':
                    parts.append(f"{name} mein bearish signal hai! Put ya sell ka signal!")
                else:
                    parts.append(f"{name} mein neutral hai, wait karo!")
    
    for s in sections:
        if s['type'] == 'fear_greed':
            d = s['data']
            if isinstance(d, dict):
                val = d.get('index', d.get('value', 50))
                if val < 30: parts.append("Market mein FEAR hai, cautious raho!")
                elif val > 70: parts.append("Market mein GREED hai, profit book karo!")
    
    for s in sections:
        if s['type'] == 'ml_prediction':
            d = s['data']
            if isinstance(d, dict):
                pred = d.get('prediction', d.get('direction', ''))
                conf = d.get('confidence', 0)
                name = s['title'].split('ML')[0].strip()
                if 'UP' in str(pred).upper():
                    parts.append(f"ML model kehta hai {name} UP jayega, confidence {conf:.0f} percent!")
                elif 'DOWN' in str(pred).upper():
                    parts.append(f"ML model kehta hai {name} DOWN jayega, confidence {conf:.0f} percent!")
    
    parts.append("Stop loss zaroor lagao Boss! Risk manage karo!")
    return " ".join(parts)


# ═══════════════════════════════════════════════
#  CRYPTO — Deep Token Analysis (Reply-Based)
# ═══════════════════════════════════════════════

def analyze_crypto_token_deep(symbol: str) -> Dict:
    """
    Deep AI/ML analysis for a specific crypto token.
    Uses ALL available indicators — world's best combined analysis.
    Called when user replies to a crypto message or asks about a specific token.
    """
    symbol = symbol.upper().strip()
    result = {
        'symbol': symbol,
        'type': 'crypto_deep',
        'timestamp': datetime.now().strftime("%H:%M IST"),
        'sections': {},
        'errors': [],
    }
    
    # 1. CoinDCX Composite Signal (TA + ML + Orderbook + Multi-TF)
    try:
        from coindcx_engine import get_composite_signal, get_all_web3_tokens
        
        composite = get_composite_signal(symbol)
        if composite and 'errors' not in composite or (isinstance(composite.get('errors'), list) and len(composite.get('errors', [])) < 3):
            result['sections']['composite'] = composite
            result['price_inr'] = composite.get('price_inr', 0)
            result['change_24h'] = composite.get('change_24h', 0)
    except Exception as e:
        result['errors'].append(f"Composite: {str(e)[:50]}")
    
    # 2. Ultra AI (Rug Risk + Whale + Liquidity + Smart Money + Health)
    try:
        from jarvis_ultra_ai import ultra_predict
        
        # Build token dict for ultra_predict
        token_data = {
            'symbol': symbol,
            'name': symbol,
            'price': result.get('price_inr', 0) / 85 if result.get('price_inr') else 0,  # Est USDT
            'priceChange': {'h24': result.get('change_24h', 0)},
            'volume': {'h24': 0},
            'liquidity': {'usd': 0},
            'fdv': 0,
            'pairCreatedAt': 0,
            'txns': {'h24': {'buys': 50, 'sells': 50}},
        }
        
        # Try to get better data from CoinDCX
        try:
            from coindcx_engine import get_all_web3_tokens
            tokens = get_all_web3_tokens()
            for t in tokens:
                if t['symbol'] == symbol:
                    token_data['name'] = t.get('name', symbol)
                    token_data['volume']['h24'] = t.get('volume', 0) / 85
                    token_data['liquidity']['usd'] = t.get('volume', 0) / 85 * 2  # Est
                    token_data['fdv'] = t.get('volume', 0) * 10  # Est
                    result['price_inr'] = t.get('price_inr', 0)
                    result['change_24h'] = t.get('change_24h', 0)
                    result['volume'] = t.get('volume', 0)
                    result['token_name'] = t.get('name', symbol)
                    result['categories'] = t.get('categories', [])
                    break
        except:
            pass
        
        ultra = ultra_predict(token_data)
        if ultra:
            result['sections']['ultra_ai'] = ultra
    except Exception as e:
        result['errors'].append(f"Ultra AI: {str(e)[:50]}")
    
    # 3. Mega Scanner (Full TA + ML + Candles) — single token
    try:
        from coindcx_engine import get_candles, compute_rsi, compute_ema, compute_macd, compute_bollinger, compute_stochastic, compute_atr, compute_obv, compute_adx
        
        pair_inr = f"I-{symbol}_INR"
        pair_usdt = f"B-{symbol}_USDT"
        
        df = get_candles(pair_inr, "1h", 200)
        if df is None or df.empty or len(df) < 30:
            df = get_candles(pair_usdt, "1h", 200)
        
        if df is not None and not df.empty and len(df) >= 30:
            close = df['close']
            ta_details = {}
            
            # RSI
            try:
                rsi = compute_rsi(close, 14).iloc[-1]
                if not __import__('numpy').isnan(rsi):
                    ta_details['rsi'] = round(rsi, 1)
                    if rsi < 30: ta_details['rsi_signal'] = "🟢 OVERSOLD — BUY zone!"
                    elif rsi < 40: ta_details['rsi_signal'] = "🟢 Low — accumulation"  
                    elif rsi > 70: ta_details['rsi_signal'] = "🔴 OVERBOUGHT — SELL zone!"
                    elif rsi > 60: ta_details['rsi_signal'] = "🟡 High — caution"
                    else: ta_details['rsi_signal'] = "⚪ Neutral"
            except: pass
            
            # EMA 9/21/50/200
            try:
                ema9 = compute_ema(close, 9).iloc[-1]
                ema21 = compute_ema(close, 21).iloc[-1]
                ema50 = compute_ema(close, min(50, len(close)-1)).iloc[-1] if len(close) > 50 else None
                ema200 = compute_ema(close, min(200, len(close)-1)).iloc[-1] if len(close) > 200 else None
                
                import numpy as np
                if not (np.isnan(ema9) or np.isnan(ema21)):
                    ta_details['ema9'] = round(float(ema9), 6)
                    ta_details['ema21'] = round(float(ema21), 6)
                    ta_details['ema_cross'] = "🟢 BULLISH (9>21)" if ema9 > ema21 else "🔴 BEARISH (9<21)"
                    
                    if ema50 and not np.isnan(ema50):
                        ta_details['ema50'] = round(float(ema50), 6)
                        if close.iloc[-1] > ema50:
                            ta_details['ema50_signal'] = "🟢 Above EMA50"
                        else:
                            ta_details['ema50_signal'] = "🔴 Below EMA50"
                    
                    if ema200 and not np.isnan(ema200):
                        ta_details['ema200'] = round(float(ema200), 6)
                        if ema50 and not np.isnan(ema50):
                            if ema50 > ema200:
                                ta_details['golden_cross'] = "🟢 GOLDEN CROSS (50>200) — Very Bullish!"
                            else:
                                ta_details['death_cross'] = "🔴 DEATH CROSS (50<200) — Very Bearish!"
            except: pass
            
            # MACD
            try:
                macd_l, sig_l, hist = compute_macd(close)
                import numpy as np
                macd_val = macd_l.iloc[-1]
                sig_val = sig_l.iloc[-1]
                if not (np.isnan(macd_val) or np.isnan(sig_val)):
                    ta_details['macd'] = round(float(macd_val), 6)
                    ta_details['macd_signal_line'] = round(float(sig_val), 6)
                    hist_val = float(hist.iloc[-1]) if hasattr(hist, 'iloc') else macd_val - sig_val
                    ta_details['macd_histogram'] = round(hist_val, 6)
                    ta_details['macd_cross'] = "🟢 BULLISH" if macd_val > sig_val else "🔴 BEARISH"
                    
                    # Histogram direction
                    if len(hist) > 2:
                        prev_hist = float(hist.iloc[-3]) if hasattr(hist, 'iloc') else 0
                        if hist_val > prev_hist:
                            ta_details['macd_momentum'] = "📈 Momentum INCREASING"
                        else:
                            ta_details['macd_momentum'] = "📉 Momentum DECREASING"
            except: pass
            
            # Bollinger Bands
            try:
                bb_u, bb_m, bb_l = compute_bollinger(close)
                import numpy as np
                if not any(np.isnan(v.iloc[-1]) for v in [bb_u, bb_m, bb_l]):
                    cur = close.iloc[-1]
                    bb_pos = (cur - bb_l.iloc[-1]) / (bb_u.iloc[-1] - bb_l.iloc[-1] + 1e-10)
                    ta_details['bb_upper'] = round(float(bb_u.iloc[-1]), 6)
                    ta_details['bb_middle'] = round(float(bb_m.iloc[-1]), 6)
                    ta_details['bb_lower'] = round(float(bb_l.iloc[-1]), 6)
                    ta_details['bb_position'] = round(bb_pos, 2)
                    bb_width = (bb_u.iloc[-1] - bb_l.iloc[-1]) / (bb_m.iloc[-1] + 1e-10) * 100
                    ta_details['bb_width'] = round(float(bb_width), 1)
                    if bb_pos < 0.1: ta_details['bb_signal'] = "🟢 OVERSOLD — Near Lower Band"
                    elif bb_pos > 0.9: ta_details['bb_signal'] = "🔴 OVERBOUGHT — Near Upper Band"
                    elif bb_width < 5: ta_details['bb_signal'] = "⚡ SQUEEZE — Big move coming!"
                    else: ta_details['bb_signal'] = "⚪ Middle Band"
            except: pass
            
            # Stochastic
            try:
                k, d = compute_stochastic(df)
                import numpy as np
                k_val = float(k.iloc[-1]) if hasattr(k, 'iloc') else float(k)
                d_val = float(d.iloc[-1]) if hasattr(d, 'iloc') else float(d)
                if not (np.isnan(k_val) or np.isnan(d_val)):
                    ta_details['stoch_k'] = round(k_val, 1)
                    ta_details['stoch_d'] = round(d_val, 1)
                    if k_val < 20: ta_details['stoch_signal'] = "🟢 OVERSOLD"
                    elif k_val > 80: ta_details['stoch_signal'] = "🔴 OVERBOUGHT"
                    elif k_val > d_val: ta_details['stoch_signal'] = "🟢 Bullish"
                    else: ta_details['stoch_signal'] = "🔴 Bearish"
            except: pass
            
            # ADX
            try:
                adx = compute_adx(df)
                import numpy as np
                adx_val = float(adx.iloc[-1]) if hasattr(adx, 'iloc') else float(adx)
                if not np.isnan(adx_val):
                    ta_details['adx'] = round(adx_val, 1)
                    if adx_val > 40: ta_details['adx_signal'] = "🔥 STRONG TREND"
                    elif adx_val > 25: ta_details['adx_signal'] = "📈 Trending"
                    else: ta_details['adx_signal'] = "➡️ Ranging/Weak"
            except: pass
            
            # ATR (volatility)
            try:
                atr = compute_atr(df)
                import numpy as np
                atr_val = float(atr.iloc[-1]) if hasattr(atr, 'iloc') else float(atr)
                if not np.isnan(atr_val):
                    price = close.iloc[-1]
                    atr_pct = (atr_val / price) * 100 if price > 0 else 0
                    ta_details['atr'] = round(atr_val, 6)
                    ta_details['atr_pct'] = round(atr_pct, 1)
                    if atr_pct > 8: ta_details['volatility'] = "🔴 VERY HIGH"
                    elif atr_pct > 4: ta_details['volatility'] = "🟡 HIGH"
                    elif atr_pct > 2: ta_details['volatility'] = "🟢 MODERATE"
                    else: ta_details['volatility'] = "🟢 LOW"
            except: pass
            
            # VWAP
            try:
                vwap = compute_vwap(df)
                import numpy as np
                vwap_val = float(vwap.iloc[-1]) if hasattr(vwap, 'iloc') else float(vwap)
                if not np.isnan(vwap_val):
                    ta_details['vwap'] = round(vwap_val, 6)
                    if close.iloc[-1] > vwap_val:
                        ta_details['vwap_signal'] = "🟢 Above VWAP (Bullish)"
                    else:
                        ta_details['vwap_signal'] = "🔴 Below VWAP (Bearish)"
            except: pass
            
            # OBV
            try:
                obv = compute_obv(df)
                obv_sma = obv.rolling(20).mean()
                if obv.iloc[-1] > obv_sma.iloc[-1]:
                    ta_details['obv_signal'] = "🟢 Accumulation (Smart Money Buying)"
                else:
                    ta_details['obv_signal'] = "🔴 Distribution (Smart Money Selling)"
            except: pass
            
            # Candle Patterns
            try:
                from coindcx_mega_scanner import detect_crypto_candle_patterns
                patterns = detect_crypto_candle_patterns(df)
                if patterns:
                    ta_details['candle_patterns'] = [
                        {'name': p.name, 'type': p.pattern_type, 'strength': p.strength, 'desc': p.description}
                        for p in patterns[:8]
                    ]
            except: pass
            
            # ML Prediction
            try:
                from coindcx_mega_scanner import _quick_ml_predict
                ml = _quick_ml_predict(df)
                if ml:
                    ta_details['ml_prediction'] = ml
            except: pass
            
            # Multi-Timeframe Check
            tf_signals = {}
            for tf_name, tf_int in [("15m", "15m"), ("4h", "4h"), ("1d", "1d")]:
                try:
                    df_tf = get_candles(pair_inr, tf_int, 100)
                    if df_tf is None or df_tf.empty:
                        df_tf = get_candles(pair_usdt, tf_int, 100)
                    if df_tf is not None and not df_tf.empty and len(df_tf) >= 20:
                        import numpy as np
                        c = df_tf['close']
                        tf_rsi = compute_rsi(c, 14).iloc[-1]
                        tf_ema9 = compute_ema(c, 9).iloc[-1]
                        tf_ema21 = compute_ema(c, 21).iloc[-1]
                        tf_macd, tf_sig, _ = compute_macd(c)
                        
                        tf_score = 0
                        if not np.isnan(tf_rsi):
                            if tf_rsi < 30: tf_score += 2
                            elif tf_rsi > 70: tf_score -= 2
                        if not (np.isnan(tf_ema9) or np.isnan(tf_ema21)):
                            if tf_ema9 > tf_ema21: tf_score += 1
                            else: tf_score -= 1
                        if not (np.isnan(tf_macd.iloc[-1]) or np.isnan(tf_sig.iloc[-1])):
                            if tf_macd.iloc[-1] > tf_sig.iloc[-1]: tf_score += 1
                            else: tf_score -= 1
                        
                        if tf_score >= 2: tf_signals[tf_name] = "🟢 BULLISH"
                        elif tf_score <= -2: tf_signals[tf_name] = "🔴 BEARISH"
                        else: tf_signals[tf_name] = "⚪ NEUTRAL"
                except:
                    pass
            
            if tf_signals:
                ta_details['multi_tf'] = tf_signals
            
            # Price Targets (Fibonacci-based)
            try:
                high_20 = df['high'].tail(20).max()
                low_20 = df['low'].tail(20).min()
                diff = high_20 - low_20
                cur = close.iloc[-1]
                
                ta_details['support_1'] = round(float(cur - diff * 0.382), 6)
                ta_details['support_2'] = round(float(cur - diff * 0.618), 6) 
                ta_details['resistance_1'] = round(float(cur + diff * 0.382), 6)
                ta_details['resistance_2'] = round(float(cur + diff * 0.618), 6)
                ta_details['resistance_3'] = round(float(cur + diff * 1.618), 6)
                
                # How high can it go?
                # Based on ATR, momentum, and historical range
                atr_p = ta_details.get('atr_pct', 3)
                momentum = result.get('change_24h', 0)
                
                # Conservative: 2x ATR
                conservative = cur * (1 + atr_p * 2 / 100)
                # Moderate: Fibonacci 1.618 extension
                moderate = float(cur + diff * 1.618)
                # Aggressive: Based on momentum continuation
                aggressive = cur * (1 + max(atr_p * 5, abs(momentum) * 2) / 100)
                # Moonshot: Historical max extension
                moonshot = cur * (1 + max(atr_p * 15, 100) / 100)
                
                ta_details['target_conservative'] = round(conservative, 6)
                ta_details['target_moderate'] = round(moderate, 6)
                ta_details['target_aggressive'] = round(aggressive, 6)
                ta_details['target_moonshot'] = round(moonshot, 6)
                
                # Stop loss
                ta_details['stop_loss'] = round(float(cur - diff * 0.618), 6)
                sl_pct = abs((ta_details['stop_loss'] - cur) / cur * 100)
                ta_details['sl_pct'] = round(sl_pct, 1)
                
                # Risk:Reward
                risk = cur - ta_details['stop_loss']
                reward = ta_details['target_moderate'] - cur
                ta_details['risk_reward'] = round(reward / risk, 1) if risk > 0 else 0
                
            except: pass
            
            result['sections']['deep_ta'] = ta_details
    except Exception as e:
        result['errors'].append(f"Deep TA: {str(e)[:50]}")
    
    # 4. Generate Final Verdict
    result['verdict'] = _generate_crypto_verdict(result)
    
    return result


def _generate_crypto_verdict(data: Dict) -> Dict:
    """Generate final BUY/SELL verdict from all analysis."""
    score = 0
    reasons = []
    
    # From composite signal
    composite = data.get('sections', {}).get('composite', {})
    if composite:
        master = composite.get('master_signal', {})
        if isinstance(master, dict):
            ms = master.get('score', 0)
            if ms > 0: score += min(ms, 5)
            else: score += max(ms, -5)
    
    # From ultra AI
    ultra = data.get('sections', {}).get('ultra_ai', {})
    if ultra:
        action = ultra.get('action', '')
        if 'BUY' in str(action).upper(): score += 3
        elif 'SELL' in str(action).upper(): score -= 3
        
        rug = ultra.get('rug_risk', {})
        if isinstance(rug, dict) and rug.get('score', 0) > 50:
            score -= 5
            reasons.append("⚠️ HIGH Rug Risk!")
    
    # From deep TA
    ta = data.get('sections', {}).get('deep_ta', {})
    if ta:
        if 'OVERSOLD' in str(ta.get('rsi_signal', '')): score += 2; reasons.append("RSI oversold")
        if 'OVERBOUGHT' in str(ta.get('rsi_signal', '')): score -= 2; reasons.append("RSI overbought")
        if 'BULLISH' in str(ta.get('ema_cross', '')): score += 1; reasons.append("EMA bullish cross")
        if 'BEARISH' in str(ta.get('ema_cross', '')): score -= 1
        if 'BULLISH' in str(ta.get('macd_cross', '')): score += 1
        if 'BEARISH' in str(ta.get('macd_cross', '')): score -= 1
        if 'GOLDEN' in str(ta.get('golden_cross', '')): score += 3; reasons.append("Golden Cross!")
        if 'DEATH' in str(ta.get('death_cross', '')): score -= 3; reasons.append("Death Cross!")
        if 'Accumulation' in str(ta.get('obv_signal', '')): score += 1; reasons.append("Smart money accumulating")
        
        ml = ta.get('ml_prediction', {})
        if ml:
            if ml.get('buy_prob', 0) > 60: score += 2; reasons.append(f"ML: {ml['buy_prob']:.0f}% buy")
            elif ml.get('sell_prob', 0) > 60: score -= 2; reasons.append(f"ML: {ml['sell_prob']:.0f}% sell")
    
    # Verdict
    if score >= 8: verdict = "STRONG BUY"; hindi = "ZAROOR KHARIDO Boss! Sab indicators BUY bol rahe hain!"; emoji = "🟢🟢🟢"
    elif score >= 5: verdict = "BUY"; hindi = "BUY KARO Boss! AI/ML dono agree kar rahe hain!"; emoji = "🟢🟢"
    elif score >= 3: verdict = "MILD BUY"; hindi = "BUY ka mauqa hai, entry le sakte ho!"; emoji = "🟢"
    elif score >= 1: verdict = "WATCH"; hindi = "WATCH karo, abhi confirm nahi hua"; emoji = "🟡"
    elif score <= -8: verdict = "STRONG SELL"; hindi = "ABHI SELL KARO! Sab red hai!"; emoji = "🔴🔴🔴"
    elif score <= -5: verdict = "SELL"; hindi = "SELL KARO Boss! Downtrend confirm!"; emoji = "🔴🔴"
    elif score <= -3: verdict = "MILD SELL"; hindi = "SELL sochho, girne wala hai"; emoji = "🔴"
    elif score <= -1: verdict = "BEARISH WATCH"; hindi = "Bearish dikh raha hai, wait karo"; emoji = "🟠"
    else: verdict = "HOLD"; hindi = "HOLD karo, koi clear signal nahi"; emoji = "⚪"
    
    return {
        'verdict': verdict,
        'hindi': hindi,
        'emoji': emoji,
        'score': score,
        'reasons': reasons[:5],
    }


def format_crypto_deep_report(data: Dict) -> List[str]:
    """Format detailed crypto token analysis for Telegram. Multi-page."""
    pages = []
    sym = data.get('symbol', '???')
    name = data.get('token_name', sym)
    price = data.get('price_inr', 0)
    change = data.get('change_24h', 0)
    verdict = data.get('verdict', {})
    
    from coindcx_mega_scanner import _fmt_inr
    
    lines = [
        f"{'═'*30}",
        f"🔥🧠 *{sym}* — JARVIS DEEP AI ANALYSIS",
        f"{'═'*30}",
        f"",
        f"💎 *{name}* ({sym})",
        f"💰 Price: {_fmt_inr(price)}" if price else f"💰 Price: Loading...",
        f"📈 24h Change: {change:+.1f}%" if change else "",
        f"🏷️ {', '.join(data.get('categories', [])[:3])}" if data.get('categories') else "",
        f"",
    ]
    
    # Verdict (TOP)
    if verdict:
        lines.extend([
            f"{'━'*28}",
            f"{verdict.get('emoji', '')} *VERDICT: {verdict.get('verdict', 'N/A')}*",
            f"🎯 *{verdict.get('hindi', '')}*",
            f"📊 AI Score: {verdict.get('score', 0):+d}",
        ])
        if verdict.get('reasons'):
            for r in verdict['reasons']:
                lines.append(f"  • {r}")
        lines.append(f"{'━'*28}")
        lines.append(f"")
    
    # Deep TA Section
    ta = data.get('sections', {}).get('deep_ta', {})
    if ta:
        lines.append(f"📊 *TECHNICAL ANALYSIS (World-Class Indicators):*")
        lines.append(f"{'─'*25}")
        
        # RSI
        if ta.get('rsi'):
            lines.append(f"📉 *RSI(14):* {ta['rsi']} → {ta.get('rsi_signal', '')}")
        
        # EMA
        if ta.get('ema_cross'):
            lines.append(f"📈 *EMA 9/21:* {ta['ema_cross']}")
        if ta.get('ema50_signal'):
            lines.append(f"📈 *EMA 50:* {ta['ema50_signal']}")
        if ta.get('golden_cross'):
            lines.append(f"⭐ *{ta['golden_cross']}*")
        if ta.get('death_cross'):
            lines.append(f"💀 *{ta['death_cross']}*")
        
        # MACD
        if ta.get('macd_cross'):
            lines.append(f"📊 *MACD:* {ta['macd_cross']}")
        if ta.get('macd_momentum'):
            lines.append(f"  {ta['macd_momentum']}")
        
        # Bollinger
        if ta.get('bb_signal'):
            lines.append(f"📏 *Bollinger:* {ta['bb_signal']} (Width: {ta.get('bb_width', 0)}%)")
        
        # Stochastic
        if ta.get('stoch_signal'):
            lines.append(f"🔄 *Stochastic:* {ta['stoch_signal']} (K:{ta.get('stoch_k', 0):.0f} D:{ta.get('stoch_d', 0):.0f})")
        
        # ADX
        if ta.get('adx_signal'):
            lines.append(f"💪 *ADX Trend:* {ta['adx_signal']} ({ta.get('adx', 0):.0f})")
        
        # ATR / Volatility
        if ta.get('volatility'):
            lines.append(f"📊 *Volatility:* {ta['volatility']} (ATR: {ta.get('atr_pct', 0)}%)")
        
        # VWAP
        if ta.get('vwap_signal'):
            lines.append(f"📊 *VWAP:* {ta['vwap_signal']}")
        
        # OBV
        if ta.get('obv_signal'):
            lines.append(f"💰 *OBV:* {ta['obv_signal']}")
        
        lines.append(f"")
        
        # Multi-Timeframe
        mtf = ta.get('multi_tf', {})
        if mtf:
            lines.append(f"⏰ *Multi-Timeframe Confluence:*")
            for tf, sig in mtf.items():
                lines.append(f"  {tf}: {sig}")
            
            # Confluence check
            bullish = sum(1 for s in mtf.values() if 'BULLISH' in s)
            bearish = sum(1 for s in mtf.values() if 'BEARISH' in s)
            if bullish >= 2:
                lines.append(f"  ✅ *{bullish} timeframes BULLISH — Strong confluence!*")
            elif bearish >= 2:
                lines.append(f"  ❌ *{bearish} timeframes BEARISH — Avoid!*")
            lines.append(f"")
        
        # Candle Patterns
        patterns = ta.get('candle_patterns', [])
        if patterns:
            lines.append(f"🕯️ *Candlestick Patterns:*")
            for p in patterns[:5]:
                if isinstance(p, dict):
                    emoji = "🟢" if p.get('type') == 'bullish' else "🔴" if p.get('type') == 'bearish' else "⚪"
                    lines.append(f"  {emoji} {p.get('name', '')} — {p.get('desc', '')}")
            lines.append(f"")
        
        # ML Prediction
        ml = ta.get('ml_prediction', {})
        if ml:
            lines.append(f"🤖 *ML Prediction (RF + Gradient Boosting):*")
            lines.append(f"  Signal: {ml.get('signal', 'N/A')}")
            lines.append(f"  Buy Probability: {ml.get('buy_prob', 50):.1f}%")
            lines.append(f"  Model Accuracy: {ml.get('confidence', 0):.1f}%")
            lines.append(f"")
        
        # Page split check
        current = "\n".join(lines)
        if len(current) > 3500:
            pages.append(current)
            lines = [f"🔥 *{sym}* — Deep Analysis (continued)\n"]
        
        # Price Targets
        if ta.get('target_conservative'):
            lines.append(f"🎯 *PRICE TARGETS — Kitna upar ja sakta hai?*")
            lines.append(f"{'─'*25}")
            lines.append(f"  🟢 Conservative: {_fmt_inr(ta['target_conservative'])}")
            lines.append(f"  🟡 Moderate: {_fmt_inr(ta['target_moderate'])}")
            lines.append(f"  🟠 Aggressive: {_fmt_inr(ta['target_aggressive'])}")
            lines.append(f"  🚀 Moonshot: {_fmt_inr(ta['target_moonshot'])}")
            lines.append(f"")
            lines.append(f"  📉 Support 1: {_fmt_inr(ta.get('support_1', 0))}")
            lines.append(f"  📉 Support 2: {_fmt_inr(ta.get('support_2', 0))}")
            lines.append(f"  📈 Resistance 1: {_fmt_inr(ta.get('resistance_1', 0))}")
            lines.append(f"  📈 Resistance 2: {_fmt_inr(ta.get('resistance_2', 0))}")
            lines.append(f"")
            lines.append(f"  🔴 *Stop Loss:* {_fmt_inr(ta.get('stop_loss', 0))} (-{ta.get('sl_pct', 0)}%)")
            lines.append(f"  📊 *Risk:Reward =* {ta.get('risk_reward', 0)}x")
            lines.append(f"")
    
    # Ultra AI Section
    ultra = data.get('sections', {}).get('ultra_ai', {})
    if ultra:
        lines.append(f"🛡️ *RISK ANALYSIS:*")
        lines.append(f"{'─'*25}")
        
        rug = ultra.get('rug_risk', {})
        if isinstance(rug, dict):
            lines.append(f"  🔍 Rug Risk: {rug.get('level', 'N/A')} ({rug.get('score', 0)}/100)")
        
        whale = ultra.get('whale', {})
        if isinstance(whale, dict):
            lines.append(f"  🐋 Whale Activity: {whale.get('level', 'N/A')}")
        
        liq = ultra.get('liquidity', {})
        if isinstance(liq, dict):
            lines.append(f"  💧 Liquidity: {liq.get('grade', 'N/A')} ({liq.get('score', 0)}/100)")
        
        flow = ultra.get('smart_money', {})
        if isinstance(flow, dict):
            lines.append(f"  💰 Smart Money: {flow.get('direction', 'N/A')}")
        
        health = ultra.get('health', {})
        if isinstance(health, dict):
            lines.append(f"  ❤️ Health Score: {health.get('grade', 'N/A')} ({health.get('score', 0)}/100)")
        lines.append(f"")
    
    # ₹2K Investment calculation
    if price and price > 0:
        qty = 2000 / price
        lines.append(f"💰 *₹2,000 invest karo to:*")
        lines.append(f"{'─'*25}")
        lines.append(f"  🪙 Quantity: {qty:.4f} {sym}")
        
        if ta.get('target_conservative'):
            t_con = ta['target_conservative']
            t_mod = ta['target_moderate']
            t_agg = ta['target_aggressive']
            t_moon = ta['target_moonshot']
            
            p_con = 2000 * (t_con / price - 1)
            p_mod = 2000 * (t_mod / price - 1)
            p_agg = 2000 * (t_agg / price - 1)
            p_moon = 2000 * (t_moon / price - 1)
            
            lines.append(f"  Conservative → ₹{2000 + p_con:,.0f} (Profit: ₹{p_con:,.0f})")
            lines.append(f"  Moderate → ₹{2000 + p_mod:,.0f} (Profit: ₹{p_mod:,.0f})")
            lines.append(f"  Aggressive → ₹{2000 + p_agg:,.0f} (Profit: ₹{p_agg:,.0f})")
            lines.append(f"  Moonshot → ₹{2000 + p_moon:,.0f} (Profit: ₹{p_moon:,.0f})")
        lines.append(f"")
    
    # Footer
    lines.extend([
        f"{'─'*28}",
        f"🛒 [CoinDCX Buy](https://coindcx.com/trade/{sym}INR) | /invest {sym}",
        f"⚠️ _JARVIS AI analysis hai, financial advice nahi._",
        f"🕐 {data.get('timestamp', '')} | _JARVIS Deep AI Engine_",
    ])
    
    pages.append("\n".join(lines))
    return pages


def format_crypto_deep_voice(data: Dict) -> str:
    """Hindi voice for deep crypto analysis."""
    sym = data.get('symbol', '???')
    verdict = data.get('verdict', {})
    ta = data.get('sections', {}).get('deep_ta', {})
    
    parts = [f"Boss, {sym} ka deep AI analysis ready hai!"]
    
    if verdict:
        parts.append(f"Final verdict: {verdict.get('verdict', 'HOLD')}! {verdict.get('hindi', '')}")
    
    if ta:
        if ta.get('rsi'):
            parts.append(f"RSI {ta['rsi']:.0f} pe hai.")
        if ta.get('ema_cross'):
            parts.append(f"EMA cross {ta['ema_cross'].replace('🟢 ', '').replace('🔴 ', '')} hai.")
        if ta.get('ml_prediction'):
            ml = ta['ml_prediction']
            parts.append(f"ML model kehta hai {ml.get('signal', 'HOLD')}, {ml.get('buy_prob', 50):.0f} percent buy probability.")
        if ta.get('candle_patterns'):
            p = ta['candle_patterns'][0]
            if isinstance(p, dict):
                parts.append(f"Candle pattern: {p.get('name', '')}.")
    
    parts.append("Full details Telegram pe bhej diye hain Boss!")
    return " ".join(parts)


# ═══════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════

__all__ = [
    'detect_market_type',
    'extract_token_from_message',
    'extract_token_from_reply',
    'analyze_indian_stock_deep',
    'format_indian_stock_report',
    'format_indian_stock_voice',
    'analyze_crypto_token_deep',
    'format_crypto_deep_report',
    'format_crypto_deep_voice',
    '_generate_crypto_verdict',
    'INDIAN_STOCK_KEYWORDS',
    'CRYPTO_KEYWORDS',
    'COINDCX_SYMBOLS',
]
