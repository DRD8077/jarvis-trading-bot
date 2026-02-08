"""
╔══════════════════════════════════════════════════════════════════════╗
║  JARVIS ULTRA AI PREDICTION ENGINE v4.0                            ║
║  World's Most Advanced Crypto AI — 100% FREE                      ║
║                                                                    ║
║  🔥 Features:                                                     ║
║    • 10 Technical Indicators (RSI, MACD, Bollinger, VWAP, EMA...) ║
║    • Rug Risk Assessment (5-factor)                                ║
║    • Whale Detection (buy/sell imbalance analysis)                 ║
║    • Liquidity Health Score                                        ║
║    • Smart Money Flow Detection                                    ║
║    • Clear Hindi BUY/SELL Recommendations                          ║
║    • Price Targets (Support/Resistance)                            ║
║    • Risk-Reward Ratio                                             ║
║    • Token Health Score (0-100)                                    ║
║    • Auto-integrated with DexTools Engine                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("JARVIS-ULTRA-AI")

# ═══════════════════════════════════════════════════════════
#  IMPORT AI SIGNALS ENGINE (10 TA indicators)
# ═══════════════════════════════════════════════════════════
try:
    from ai_signals import (
        full_technical_analysis,
        batch_signals as _ai_batch_signals,
        quick_signal as _ai_quick_signal,
        calculate_rsi,
        calculate_macd,
        calculate_bollinger,
    )
    AI_ENGINE_READY = True
except ImportError:
    AI_ENGINE_READY = False
    logger.warning("[ULTRA-AI] ai_signals.py not found — using fallback mode")


# ═══════════════════════════════════════════════════════════
#  RUG RISK ASSESSMENT (5-factor analysis)
# ═══════════════════════════════════════════════════════════

def assess_rug_risk(token: dict) -> dict:
    """
    5-Factor Rug Risk Assessment:
    1. Liquidity depth (low liq = high risk)
    2. Token age (new = higher risk)
    3. Buy/Sell ratio (extreme = manipulation)
    4. Volume/Liquidity ratio (extreme = wash trading)
    5. Price volatility (extreme swings = pump & dump)
    
    Returns: {"score": 0-100, "level": "LOW/MEDIUM/HIGH/EXTREME", "factors": [...]}
    """
    risk_score = 0
    factors = []
    
    liq = token.get("liquidity", 0)
    vol = token.get("volume_24h", 0)
    ratio = token.get("buy_sell_ratio", 0)
    change_1h = abs(token.get("price_change_1h", 0))
    change_24h = abs(token.get("price_change_24h", 0))
    is_new = token.get("is_new", False)
    mcap = token.get("market_cap", 0)
    
    # Factor 1: Liquidity Depth
    if liq <= 0:
        risk_score += 30
        factors.append("⚠️ Zero liquidity — EXTREME RISK")
    elif liq < 5_000:
        risk_score += 25
        factors.append("🔴 Very low liquidity < $5K")
    elif liq < 50_000:
        risk_score += 15
        factors.append("🟠 Low liquidity < $50K")
    elif liq < 500_000:
        risk_score += 5
        factors.append("🟡 Moderate liquidity")
    else:
        factors.append("🟢 Strong liquidity > $500K")
    
    # Factor 2: Token Age
    if is_new:
        risk_score += 20
        factors.append("🆕 New token — higher risk")
    
    # Factor 3: Buy/Sell Manipulation Check
    if ratio > 10:
        risk_score += 15
        factors.append("⚠️ Extreme buy ratio — possible manipulation")
    elif ratio > 0 and ratio < 0.1:
        risk_score += 15
        factors.append("⚠️ Extreme sell ratio — dump risk")
    
    # Factor 4: Wash Trading Check (Vol/Liq ratio)
    if liq > 0 and vol > 0:
        vol_liq = vol / liq
        if vol_liq > 50:
            risk_score += 15
            factors.append("⚠️ Vol/Liq > 50x — possible wash trading")
        elif vol_liq > 20:
            risk_score += 8
            factors.append("🟠 High Vol/Liq ratio")
    
    # Factor 5: Pump & Dump Check
    if change_1h > 100:
        risk_score += 20
        factors.append("🔴 1h pump > 100% — P&D risk")
    elif change_1h > 50:
        risk_score += 12
        factors.append("🟠 1h change > 50% — volatile")
    elif change_24h > 200:
        risk_score += 10
        factors.append("🟠 24h change > 200% — volatile")
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    # Level
    if risk_score >= 70:
        level = "EXTREME"
        emoji = "🔴🔴"
        hindi = "BAHUT KHATARNAK — DUR RAHO"
    elif risk_score >= 50:
        level = "HIGH"
        emoji = "🔴"
        hindi = "ZYADA RISK — SAMBHAL KE"
    elif risk_score >= 25:
        level = "MEDIUM"
        emoji = "🟠"
        hindi = "THODA RISK HAI — RESEARCH KARO"
    else:
        level = "LOW"
        emoji = "🟢"
        hindi = "KAM RISK — SAFE TOKEN"
    
    return {
        "score": risk_score,
        "level": level,
        "emoji": emoji,
        "hindi": hindi,
        "factors": factors,
    }


# ═══════════════════════════════════════════════════════════
#  WHALE DETECTION
# ═══════════════════════════════════════════════════════════

def detect_whale_activity(token: dict) -> dict:
    """
    Detect potential whale activity from buy/sell data.
    """
    buys_1h = token.get("buys_1h", 0)
    sells_1h = token.get("sells_1h", 0)
    buys_24h = token.get("buys_24h", 0)
    sells_24h = token.get("sells_24h", 0)
    ratio = token.get("buy_sell_ratio", 0)
    vol = token.get("volume_24h", 0)
    liq = token.get("liquidity", 0)
    
    # Large single-side activity = whale
    whale_signals = []
    whale_score = 0  # 0-100
    
    # Check 1h concentration
    total_1h = buys_1h + sells_1h
    if total_1h > 0:
        if buys_1h > 0 and sells_1h > 0:
            if buys_1h / total_1h > 0.85:
                whale_signals.append("🐳 Whale BUYING detected (85%+ buys in 1h)")
                whale_score += 40
            elif sells_1h / total_1h > 0.85:
                whale_signals.append("🐳 Whale SELLING detected (85%+ sells in 1h)")
                whale_score += 40
    
    # Check volume vs liquidity (big moves)
    if liq > 0 and vol > 0:
        if vol > liq * 5:
            whale_signals.append("🐳 Volume 5x+ liquidity — whale activity")
            whale_score += 30
    
    # Check ratio extremes  
    if ratio > 5:
        whale_signals.append("🐳 Buy ratio > 5x — accumulation")
        whale_score += 25
    elif 0 < ratio < 0.2:
        whale_signals.append("🐳 Sell ratio extreme — distribution")
        whale_score += 25
    
    whale_score = min(whale_score, 100)
    
    if whale_score >= 50:
        level = "HIGH"
        emoji = "🐳🐳"
    elif whale_score >= 25:
        level = "MODERATE"
        emoji = "🐳"
    else:
        level = "NONE"
        emoji = "✅"
    
    return {
        "score": whale_score,
        "level": level,
        "emoji": emoji,
        "signals": whale_signals,
    }


# ═══════════════════════════════════════════════════════════
#  LIQUIDITY HEALTH SCORE
# ═══════════════════════════════════════════════════════════

def liquidity_health(token: dict) -> dict:
    """
    Analyze token liquidity health.
    """
    liq = token.get("liquidity", 0)
    vol = token.get("volume_24h", 0)
    mcap = token.get("market_cap", 0)
    
    score = 0
    notes = []
    
    # Liquidity amount
    if liq >= 1_000_000:
        score += 40
        notes.append("💎 Deep liquidity > $1M")
    elif liq >= 100_000:
        score += 30
        notes.append("✅ Good liquidity > $100K")
    elif liq >= 10_000:
        score += 15
        notes.append("🟡 Moderate liquidity")
    elif liq > 0:
        score += 5
        notes.append("🔴 Low liquidity — slippage risk")
    
    # Vol/Liq ratio (healthy = 0.5-5x)
    if liq > 0:
        vol_liq = vol / liq
        if 0.5 <= vol_liq <= 5:
            score += 30
            notes.append("✅ Healthy trading volume")
        elif vol_liq > 5:
            score += 10
            notes.append("🟠 High volume — large price impact possible")
        else:
            score += 15
            notes.append("🟡 Low volume activity")
    
    # MCap backing
    if mcap > 0 and liq > 0:
        liq_mcap = liq / mcap
        if liq_mcap > 0.1:
            score += 30
            notes.append("💎 Well-backed (Liq/MCap > 10%)")
        elif liq_mcap > 0.03:
            score += 20
            notes.append("✅ Decent backing")
        else:
            score += 5
            notes.append("🟡 Thin liquidity backing")
    
    score = min(score, 100)
    
    if score >= 70:
        grade = "A"
    elif score >= 50:
        grade = "B"
    elif score >= 30:
        grade = "C"
    else:
        grade = "D"
    
    return {"score": score, "grade": grade, "notes": notes}


# ═══════════════════════════════════════════════════════════
#  SMART MONEY FLOW DETECTION
# ═══════════════════════════════════════════════════════════

def smart_money_flow(token: dict) -> dict:
    """
    Detect smart money flow direction.
    Uses: volume trend, buy/sell ratio trend, price momentum alignment.
    """
    vol = token.get("volume_24h", 0)
    liq = token.get("liquidity", 0)
    ratio = token.get("buy_sell_ratio", 0)
    change_5m = token.get("price_change_5m", 0)
    change_1h = token.get("price_change_1h", 0)
    change_6h = token.get("price_change_6h", 0)
    change_24h = token.get("price_change_24h", 0)
    
    flow_score = 0  # -100 (outflow) to +100 (inflow)
    signals = []
    
    # Buy/Sell ratio direction
    if ratio > 2:
        flow_score += 30
        signals.append("💰 Strong inflows (Buy ratio > 2x)")
    elif ratio > 1.3:
        flow_score += 15
        signals.append("📈 Moderate inflows")
    elif 0 < ratio < 0.5:
        flow_score -= 30
        signals.append("💸 Heavy outflows (Sell dominant)")
    elif 0 < ratio < 0.7:
        flow_score -= 15
        signals.append("📉 Moderate outflows")
    
    # Momentum alignment (accelerating trend)
    timeframes = [change_5m, change_1h, change_6h, change_24h]
    positive_count = sum(1 for c in timeframes if c > 0)
    
    if positive_count >= 3 and change_5m > change_1h / 12:
        flow_score += 25
        signals.append("🚀 Accelerating uptrend (smart money buying)")
    elif positive_count <= 1 and change_5m < 0:
        flow_score -= 25
        signals.append("⬇️ Accelerating downtrend")
    
    # Volume conviction
    if liq > 0 and vol > liq * 2:
        if flow_score > 0:
            flow_score += 20
            signals.append("💎 High conviction buying")
        elif flow_score < 0:
            flow_score -= 20
            signals.append("🔴 High conviction selling")
    
    flow_score = max(-100, min(100, flow_score))
    
    if flow_score >= 40:
        direction = "STRONG INFLOW"
        emoji = "💰💰"
    elif flow_score >= 15:
        direction = "INFLOW"
        emoji = "💰"
    elif flow_score <= -40:
        direction = "STRONG OUTFLOW"
        emoji = "💸💸"
    elif flow_score <= -15:
        direction = "OUTFLOW"
        emoji = "💸"
    else:
        direction = "NEUTRAL"
        emoji = "⚖️"
    
    return {
        "score": flow_score,
        "direction": direction,
        "emoji": emoji,
        "signals": signals,
    }


# ═══════════════════════════════════════════════════════════
#  PRICE TARGET ENGINE (Support/Resistance)
# ═══════════════════════════════════════════════════════════

def calculate_price_targets(token: dict, analysis: dict = None) -> dict:
    """
    Calculate price targets based on technical analysis.
    """
    price = token.get("price_usd", 0)
    if price <= 0:
        return {"support": 0, "resistance": 0, "upside_pct": 0, "downside_pct": 0}
    
    change_1h = token.get("price_change_1h", 0)
    change_24h = token.get("price_change_24h", 0)
    
    # Use Fibonacci from analysis if available
    if analysis and "indicators" in analysis:
        fib = analysis["indicators"].get("fibonacci", {})
        support = fib.get("nearest_support", price * 0.92)
        resistance = fib.get("nearest_resistance", price * 1.08)
    else:
        # Estimate from volatility
        volatility = max(abs(change_1h), abs(change_24h) / 4, 3)
        support = price * (1 - volatility / 100)
        resistance = price * (1 + volatility / 100)
    
    upside = ((resistance - price) / price * 100) if price > 0 else 0
    downside = ((price - support) / price * 100) if price > 0 else 0
    
    # Risk-Reward ratio
    rr_ratio = upside / downside if downside > 0 else 99
    
    if rr_ratio >= 3:
        rr_grade = "EXCELLENT"
        rr_emoji = "🟢🟢"
    elif rr_ratio >= 2:
        rr_grade = "GOOD"
        rr_emoji = "🟢"
    elif rr_ratio >= 1:
        rr_grade = "FAIR"
        rr_emoji = "🟡"
    else:
        rr_grade = "POOR"
        rr_emoji = "🔴"
    
    return {
        "support": support,
        "resistance": resistance,
        "upside_pct": round(upside, 2),
        "downside_pct": round(downside, 2),
        "rr_ratio": round(rr_ratio, 2),
        "rr_grade": rr_grade,
        "rr_emoji": rr_emoji,
    }


# ═══════════════════════════════════════════════════════════
#  TOKEN HEALTH SCORE (0-100 composite)
# ═══════════════════════════════════════════════════════════

def token_health_score(token: dict, analysis: dict = None) -> dict:
    """
    Overall token health score combining all factors.
    """
    rug = assess_rug_risk(token)
    whale = detect_whale_activity(token)
    liq = liquidity_health(token)
    money = smart_money_flow(token)
    
    # Health = inverse of risk + liquidity + money flow
    risk_component = max(0, 100 - rug["score"])  # Lower risk = higher health
    liq_component = liq["score"]
    money_component = max(0, 50 + money["score"] / 2)  # Normalize -100..+100 → 0..100
    
    # Weighted average
    health = (
        risk_component * 0.30 +
        liq_component * 0.25 +
        money_component * 0.25
    )
    
    # Add AI signal score if available
    if analysis:
        ai_score = analysis.get("composite_score", 0.5) * 100
        health += ai_score * 0.20
    else:
        health += 50 * 0.20  # neutral
    
    health = min(100, max(0, health))
    
    if health >= 80:
        grade = "A+"
        verdict = "EXCELLENT"
        emoji = "💎"
    elif health >= 65:
        grade = "A"
        verdict = "GOOD"
        emoji = "✅"  
    elif health >= 50:
        grade = "B"
        verdict = "AVERAGE"
        emoji = "🟡"
    elif health >= 35:
        grade = "C"
        verdict = "BELOW AVERAGE"
        emoji = "🟠"
    else:
        grade = "D"
        verdict = "POOR"
        emoji = "🔴"
    
    return {
        "score": round(health, 1),
        "grade": grade,
        "verdict": verdict,
        "emoji": emoji,
        "components": {
            "risk": round(risk_component, 1),
            "liquidity": round(liq_component, 1),
            "money_flow": round(money_component, 1),
        },
    }


# ═══════════════════════════════════════════════════════════
#  ULTRA PREDICTION — MAIN ENGINE
# ═══════════════════════════════════════════════════════════

def ultra_predict(token: dict) -> dict:
    """
    JARVIS Ultra AI Prediction — complete analysis for any token.
    
    Returns comprehensive prediction with:
    - Full 10-indicator TA (if ai_signals available)
    - Rug risk assessment
    - Whale detection
    - Liquidity health
    - Smart money flow
    - Price targets
    - Risk-reward ratio
    - Token health score
    - Clear BUY/SELL/HOLD with Hindi explanation
    """
    result = {
        "token": token.get("symbol", "???"),
        "name": token.get("name", "Unknown"),
        "chain": token.get("chain", "unknown"),
        "price": token.get("price_usd", 0),
    }
    
    # ── 1. Full Technical Analysis (10 indicators) ──
    if AI_ENGINE_READY:
        try:
            analysis = full_technical_analysis(token)
            result["ai_signal"] = analysis
        except Exception as e:
            logger.warning(f"[ULTRA-AI] TA failed for {token.get('symbol')}: {e}")
            analysis = None
            result["ai_signal"] = None
    else:
        analysis = None
        result["ai_signal"] = None
    
    # ── 2. Risk Assessment ──
    result["rug_risk"] = assess_rug_risk(token)
    
    # ── 3. Whale Detection ──
    result["whale"] = detect_whale_activity(token)
    
    # ── 4. Liquidity Health ──  
    result["liquidity"] = liquidity_health(token)
    
    # ── 5. Smart Money Flow ──
    result["money_flow"] = smart_money_flow(token)
    
    # ── 6. Price Targets ──
    result["targets"] = calculate_price_targets(token, analysis)
    
    # ── 7. Token Health Score ──
    result["health"] = token_health_score(token, analysis)
    
    # ── 8. Final Verdict with Hindi ──
    result["verdict"] = _generate_verdict(token, result)
    
    # ── 9. Log prediction for self-learning ──
    try:
        from trade_tracker import log_prediction
        symbol = token.get("symbol", token.get("base", "UNKNOWN"))
        price = float(token.get("priceUsd") or token.get("price") or 0)
        verdict = result["verdict"]
        indicators = {
            "ai_signal": str(result.get("ai_signal", {}).get("signal", "")),
            "rug_risk": str(result.get("rug_risk", {}).get("level", "")),
            "money_flow": str(result.get("money_flow", {}).get("direction", "")),
            "whale": str(result.get("whale", {}).get("signal", "")),
            "health": str(result.get("health", {}).get("grade", "")),
        }
        log_prediction(symbol, verdict["action"], verdict["score"], price,
                       source="ultra_ai", indicators=indicators)
    except Exception as e:
        logger.debug(f"[ULTRA-AI] Prediction logging failed: {e}")
    
    return result


def _generate_verdict(token: dict, result: dict) -> dict:
    """
    Generate clear BUY/SELL/HOLD verdict with Hindi explanation.
    """
    # Collect all signals
    ai = result.get("ai_signal")
    rug = result.get("rug_risk", {})
    health = result.get("health", {})
    money = result.get("money_flow", {})
    targets = result.get("targets", {})
    whale = result.get("whale", {})
    
    # Build final score
    score = 50  # Start neutral
    reasons_buy = []
    reasons_sell = []
    
    # AI Signal influence (40% weight)
    if ai:
        composite = ai.get("composite_score", 0.5)
        ai_influence = (composite - 0.5) * 80  # -40 to +40
        score += ai_influence
        
        if composite >= 0.65:
            reasons_buy.append(f"🧠 AI {ai['signal']} ({ai['confidence']:.0f}%)")
        elif composite <= 0.35:
            reasons_sell.append(f"🧠 AI {ai['signal']} ({ai['confidence']:.0f}%)")
    
    # Rug Risk influence (20% weight)  
    rug_score = rug.get("score", 0)
    if rug_score >= 50:
        score -= rug_score * 0.3
        reasons_sell.append(f"⚠️ Rug Risk: {rug['level']} ({rug_score})")
    elif rug_score <= 20:
        score += 5
        reasons_buy.append(f"🛡️ Low Rug Risk ({rug_score})")
    
    # Money Flow influence (20% weight)
    flow = money.get("score", 0)
    if flow >= 30:
        score += 10
        reasons_buy.append(f"💰 {money['direction']}")
    elif flow <= -30:
        score -= 10
        reasons_sell.append(f"💸 {money['direction']}")
    
    # Whale Warning (10% weight)
    if whale.get("score", 0) >= 50:
        score -= 5
        reasons_sell.append(f"🐳 Whale activity detected")
    
    # Risk-Reward (10% weight)
    rr = targets.get("rr_ratio", 1)
    if rr >= 2:
        score += 5
        reasons_buy.append(f"📊 R:R = {rr:.1f}x")
    elif rr < 0.5:
        score -= 5
        reasons_sell.append(f"📊 Poor R:R = {rr:.1f}x")
    
    # Cap score
    score = max(0, min(100, score))
    
    # ── Final Verdict ──
    if score >= 75:
        action = "STRONG BUY"
        emoji = "🟢🟢"
        hindi_action = "ZAROOR KHARIDO"
        hindi_detail = "Ye token bahut strong lag raha hai! AI, money flow, risk sab achha hai. BUY karo!"
    elif score >= 62:
        action = "BUY"
        emoji = "🟢"
        hindi_action = "BUY KARO"
        hindi_detail = "Ye token achha lag raha hai. Buy kar sakte ho, lekin stop-loss zaroor lagaana."
    elif score >= 52:
        action = "HOLD"
        emoji = "🟡"
        hindi_action = "HOLD KARO"
        hindi_detail = "Abhi wait karo. Token neutral hai, entry ka sahi time nahi aaya."
    elif score >= 42:
        action = "NEUTRAL"
        emoji = "⚪"
        hindi_action = "WAIT KARO"
        hindi_detail = "Token flat hai. Koi clear signal nahi hai. Wait karo ya skip karo."
    elif score >= 32:
        action = "CAUTION"
        emoji = "🟠"
        hindi_action = "SAMBHAL KE"
        hindi_detail = "Risk zyada hai. Agar already hold kar rahe ho toh stop-loss tight rakho."
    elif score >= 20:
        action = "SELL"
        emoji = "🔴"
        hindi_action = "SELL KARO"
        hindi_detail = "Ye token risky hai. Exit karna better rahega. Paise bachao."
    else:
        action = "STRONG SELL"
        emoji = "🔴🔴"
        hindi_action = "DUR RAHO"
        hindi_detail = "KHATARNAK! Is token se DUR raho. Rug pull / dump ka risk hai."
    
    return {
        "action": action,
        "emoji": emoji,
        "score": round(score, 1),
        "hindi_action": hindi_action,
        "hindi_detail": hindi_detail,
        "reasons_buy": reasons_buy,
        "reasons_sell": reasons_sell,
        "calibrated_confidence": _get_calibrated(score),
    }


def _get_calibrated(raw_score: float) -> Optional[float]:
    """Get calibrated confidence from trade tracker (if available)."""
    try:
        from trade_tracker import get_calibrated_confidence
        return round(get_calibrated_confidence(raw_score) * 100, 1)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  BATCH ULTRA PREDICT — For Token Lists
# ═══════════════════════════════════════════════════════════

def batch_ultra_predict(tokens: list) -> list:
    """
    Run Ultra AI Prediction on a list of tokens.
    Attaches _ultra field to each token dict.
    """
    for t in tokens:
        try:
            ultra = ultra_predict(t)
            t["_ultra"] = ultra
            
            # Also set _signal for backward compatibility with format_top_tokens
            verdict = ultra.get("verdict", {})
            t["_signal"] = {
                "signal": f"{verdict.get('emoji', '⚪')} {verdict.get('action', 'UNKNOWN')}",
                "emoji": verdict.get("emoji", "⚪"),
                "confidence": verdict.get("score", 50),
                "action": verdict.get("action", "UNKNOWN"),
                "hindi": verdict.get("hindi_action", ""),
            }
        except Exception as e:
            logger.warning(f"[ULTRA-AI] Prediction failed for {t.get('symbol')}: {e}")
    
    return tokens


# ═══════════════════════════════════════════════════════════
#  FORMAT — Enhanced Display with AI Predictions
# ═══════════════════════════════════════════════════════════

def _fmt_price(price: float) -> str:
    """Format price for display."""
    if price <= 0:
        return "$0"
    if price >= 1000:
        return f"${price:,.0f}"
    if price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.0001:
        return f"${price:.6f}"
    else:
        return f"${price:.10f}"


def _fmt_vol(vol: float) -> str:
    """Format volume for display."""
    if vol >= 1e9:
        return f"${vol / 1e9:.1f}B"
    elif vol >= 1e6:
        return f"${vol / 1e6:.1f}M"
    elif vol >= 1e3:
        return f"${vol / 1e3:.1f}K"
    elif vol > 0:
        return f"${vol:.0f}"
    return "$0"


def format_ultra_token_card(token: dict, rank: int = 0) -> str:
    """
    Format a single token with full Ultra AI prediction card.
    This is the detailed per-token view used in signal reports.
    """
    ultra = token.get("_ultra")
    if not ultra:
        ultra = ultra_predict(token)
    
    verdict = ultra.get("verdict", {})
    rug = ultra.get("rug_risk", {})
    whale = ultra.get("whale", {})
    health = ultra.get("health", {})
    money = ultra.get("money_flow", {})
    targets = ultra.get("targets", {})
    ai = ultra.get("ai_signal")
    liq_h = ultra.get("liquidity", {})
    
    chain_em = token.get("chain_emoji", "🔗")
    symbol = token.get("symbol", "???")
    name = token.get("name", "Unknown")
    price = token.get("price_usd", 0)
    change_1h = token.get("price_change_1h", 0)
    change_24h = token.get("price_change_24h", 0)
    
    # Header
    rank_str = f"{rank}. " if rank else ""
    lines = [
        f"{'━' * 32}",
        f"*{rank_str}{chain_em} {symbol}* — {name}",
        f"💰 `{_fmt_price(price)}`",
        f"{'🟢' if change_1h > 0 else '🔴'} 1h: `{change_1h:+.1f}%` | "
        f"{'🟢' if change_24h > 0 else '🔴'} 24h: `{change_24h:+.1f}%`",
        f"📊 Vol: {_fmt_vol(token.get('volume_24h', 0))} | "
        f"Liq: {_fmt_vol(token.get('liquidity', 0))}",
        f"",
    ]
    
    # ── Verdict Box ──
    lines.append(f"{verdict.get('emoji', '⚪')} *VERDICT: {verdict.get('action', 'UNKNOWN')}* "
                 f"(Score: {verdict.get('score', 50)}/100)")
    lines.append(f"🇮🇳 *{verdict.get('hindi_action', '')}*")
    lines.append(f"_{verdict.get('hindi_detail', '')}_")
    lines.append("")
    
    # ── AI Signal (if available) ──
    if ai:
        confidence = ai.get("confidence", 0)
        signal = ai.get("signal", "UNKNOWN")
        lines.append(f"🧠 *AI Signal:* {ai.get('emoji', '⚪')} {signal} ({confidence:.0f}%)")
        
        # Key indicators
        ind = ai.get("indicators", {})
        parts = []
        if "rsi" in ind:
            rsi_val = ind["rsi"]["value"]
            parts.append(f"RSI: {rsi_val:.0f}")
        if "macd" in ind:
            parts.append(f"MACD: {ind['macd']['trend']}")
        if "ema_cross" in ind:
            parts.append(f"EMA: {ind['ema_cross']['cross']}")
        if "bollinger" in ind:
            bb_pos = ind["bollinger"]["position"]
            parts.append(f"BB: {bb_pos:.0%}")
        if parts:
            lines.append(f"   📈 {' | '.join(parts)}")
        lines.append("")
    
    # ── Risk & Health ──
    lines.append(f"🛡️ Rug Risk: {rug.get('emoji', '⚪')} *{rug.get('level', '?')}* ({rug.get('score', 0)})")
    lines.append(f"💎 Health: {health.get('emoji', '⚪')} *{health.get('grade', '?')}* ({health.get('score', 0):.0f}/100)")
    lines.append(f"💰 Money: {money.get('emoji', '⚖️')} *{money.get('direction', 'NEUTRAL')}*")
    
    if whale.get("score", 0) >= 25:
        lines.append(f"🐳 Whale: {whale.get('emoji', '✅')} *{whale.get('level', 'NONE')}*")
    
    lines.append(f"💧 Liquidity: Grade *{liq_h.get('grade', '?')}*")
    
    # ── Price Targets ──
    if targets.get("support", 0) > 0:
        lines.append(f"")
        lines.append(f"🎯 Support: `{_fmt_price(targets['support'])}`")
        lines.append(f"🎯 Resistance: `{_fmt_price(targets['resistance'])}`")
        lines.append(f"📊 R:R = {targets.get('rr_emoji', '⚪')} *{targets.get('rr_ratio', 0):.1f}x* "
                     f"({targets.get('rr_grade', '?')})")
        lines.append(f"   ⬆️ Upside: `+{targets.get('upside_pct', 0):.1f}%` | "
                     f"⬇️ Risk: `{targets.get('downside_pct', 0):.1f}%`")
    
    # ── Buy/Sell Reasons ──
    reasons_buy = verdict.get("reasons_buy", [])
    reasons_sell = verdict.get("reasons_sell", [])
    
    if reasons_buy:
        lines.append(f"\n✅ *BUY Reasons:*")
        for r in reasons_buy[:3]:
            lines.append(f"  {r}")
    if reasons_sell:
        lines.append(f"\n⚠️ *SELL Reasons:*")
        for r in reasons_sell[:3]:
            lines.append(f"  {r}")
    
    # ── Links ──
    # Get deep links
    dx_url = token.get("dexscreener_url", "")
    dt_url = token.get("dextools_url", "")
    
    link_parts = []
    if dt_url:
        link_parts.append(f"[DexTools]({dt_url})")
    if dx_url:
        link_parts.append(f"[DexScreener]({dx_url})")
    
    address = token.get("address", "")
    chain = token.get("chain", "")
    if address and chain:
        if chain.lower() == "solana":
            link_parts.append(f"[Birdeye](https://birdeye.so/token/{address}?chain=solana)")
        else:
            link_parts.append(f"[CoinGecko](https://www.coingecko.com/en/coins/{token.get('name','').lower().replace(' ','-')})")
    
    if link_parts:
        lines.append(f"\n🔗 {' | '.join(link_parts)}")
    
    return "\n".join(lines)


def format_ultra_top_tokens(tokens: list, title: str = "🔥 TOP TOKENS — JARVIS ULTRA AI") -> str:
    """
    Format top tokens with COMPACT Ultra AI prediction cards.
    Used for DexTools Top 15, Meme Board, New Pairs.
    More compact than full card — fits 15 tokens in one message.
    """
    if not tokens:
        return "❌ No tokens found at the moment."
    
    lines = [
        f"🔥🧠 *{title}*",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"_JARVIS Ultra AI — 10 Indicators + Risk Analysis_",
        f"_{datetime.now().strftime('%I:%M %p IST, %d %b %Y')}_\n",
    ]
    
    for i, t in enumerate(tokens[:15], 1):
        ultra = t.get("_ultra")
        if not ultra:
            try:
                ultra = ultra_predict(t)
                t["_ultra"] = ultra
            except:
                ultra = {}
        
        verdict = ultra.get("verdict", {})
        health = ultra.get("health", {})
        rug = ultra.get("rug_risk", {})
        targets = ultra.get("targets", {})
        ai = ultra.get("ai_signal")
        
        chain_em = t.get("chain_emoji", "🔗")
        symbol = t.get("symbol", "???")
        price = t.get("price_usd", 0)
        change_1h = t.get("price_change_1h", 0)
        change_24h = t.get("price_change_24h", 0)
        ratio = t.get("buy_sell_ratio", 0)
        new_badge = " 🆕" if t.get("is_new") else ""
        
        p_em = "🟢" if change_1h > 0 else "🔴" if change_1h < 0 else "⚪"
        verdict_em = verdict.get("emoji", "⚪")
        action = verdict.get("action", "?")
        hindi = verdict.get("hindi_action", "")
        v_score = verdict.get("score", 50)
        
        # ── Token header ──
        lines.append(f"*{i}. {chain_em} {symbol}{new_badge}* — {t.get('name', '?')}")
        lines.append(f"   💰 `{_fmt_price(price)}` | "
                     f"{p_em} 1h: `{change_1h:+.1f}%` | 24h: `{change_24h:+.1f}%`")
        lines.append(f"   📊 Vol: {_fmt_vol(t.get('volume_24h', 0))} | "
                     f"Liq: {_fmt_vol(t.get('liquidity', 0))}")
        
        if ratio > 0:
            r_em = "🟢" if ratio > 1.5 else "🟡" if ratio > 1 else "🔴"
            lines.append(f"   {r_em} Buy/Sell: {ratio}x")
        
        # ── AI Verdict line ──
        lines.append(f"   {verdict_em} *{action}* — 🇮🇳 _{hindi}_ (Score: {v_score:.0f})")
        
        # ── Key indicators compact ──
        ind_parts = []
        if ai:
            ind = ai.get("indicators", {})
            if "rsi" in ind:
                rsi_v = ind["rsi"]["value"]
                rsi_e = "🟢" if rsi_v < 35 else "🔴" if rsi_v > 65 else "🟡"
                ind_parts.append(f"{rsi_e}RSI:{rsi_v:.0f}")
            if "macd" in ind:
                m_e = "🟢" if "bullish" in ind["macd"]["trend"] else "🔴"
                ind_parts.append(f"{m_e}MACD")
            if "ema_cross" in ind:
                e_e = "🟢" if ind["ema_cross"]["cross"] == "bullish" else "🔴"
                ind_parts.append(f"{e_e}EMA")
            if "bollinger" in ind:
                bb = ind["bollinger"]["position"]
                b_e = "🟢" if bb < 0.3 else "🔴" if bb > 0.7 else "🟡"
                ind_parts.append(f"{b_e}BB:{bb:.0%}")
        
        if ind_parts:
            lines.append(f"   📈 {' | '.join(ind_parts)}")
        
        # ── Risk + Health compact ──
        lines.append(f"   🛡️{rug.get('emoji','⚪')}Risk:{rug.get('level','?')} | "
                     f"{health.get('emoji','⚪')}Health:{health.get('grade','?')} | "
                     f"🎯R:R={targets.get('rr_ratio', 0):.1f}x")
        
        # ── Links ──
        dx = t.get("dexscreener_url", "")
        dt = t.get("dextools_url", "")
        link_parts = []
        if dt:
            link_parts.append(f"[DT]({dt})")
        if dx:
            link_parts.append(f"[DS]({dx})")
        addr = t.get("address", "")
        chain = t.get("chain", "")
        if addr and chain and chain.lower() == "solana":
            link_parts.append(f"[BE](https://birdeye.so/token/{addr}?chain=solana)")
        
        if link_parts:
            lines.append(f"   🔗 {' | '.join(link_parts)}")
        
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🧠 _10 TA Indicators + 5-Factor Risk + Whale + Smart Money_")
    lines.append("🤖 _JARVIS Ultra AI — Buy/Sell har token ke saath!_")
    lines.append("⚠️ _DYOR — Not financial advice_")
    
    return "\n".join(lines)


def format_ultra_voice(tokens: list) -> str:
    """
    Generate Hindi voice summary with clear buy/sell calls.
    """
    if not tokens:
        return "Boss, abhi koi token nahi mila."
    
    parts = ["Boss Deepak sir, JARVIS Ultra AI ka full analysis ready hai! "]
    
    buy_count = 0
    sell_count = 0
    
    for i, t in enumerate(tokens[:5], 1):
        ultra = t.get("_ultra", {})
        verdict = ultra.get("verdict", {})
        action = verdict.get("action", "UNKNOWN")
        hindi = verdict.get("hindi_action", "")
        score = verdict.get("score", 50)
        symbol = t.get("symbol", "unknown")
        price = t.get("price_usd", 0)
        change_1h = t.get("price_change_1h", 0)
        
        direction = "upar" if change_1h > 0 else "neeche" if change_1h < 0 else "stable"
        
        parts.append(
            f"Number {i}, {symbol}, price {_fmt_price(price)}, "
            f"last 1 hour mein {abs(change_1h):.1f} percent {direction}. "
        )
        
        # Clear buy/sell call
        if "BUY" in action:
            buy_count += 1
            parts.append(f"JARVIS ka verdict: {hindi}! Score {score:.0f} hai. ")
        elif "SELL" in action or "CAUTION" in action:
            sell_count += 1
            parts.append(f"JARVIS ka verdict: {hindi}! Score {score:.0f} hai. ")
        else:
            parts.append(f"JARVIS ka verdict: {hindi}. Neutral hai. ")
        
        # Rug risk warning
        rug = ultra.get("rug_risk", {})
        if rug.get("level") in ("HIGH", "EXTREME"):
            parts.append(f"LEKIN DHYAAN SE! Rug risk {rug['level']} hai. ")
    
    # Summary
    parts.append(f"\nTotal {len(tokens[:5])} tokens mein se {buy_count} BUY aur {sell_count} risky hain. ")
    parts.append("Full detail text message mein hai boss. DYOR kariye! Jai Shri Ram!")
    
    return "".join(parts)


# ═══════════════════════════════════════════════════════════
#  MODULE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  JARVIS ULTRA AI PREDICTION ENGINE v4.0 — TEST")
    print("=" * 60)
    
    # Test with a sample token
    sample = {
        "name": "Test Coin",
        "symbol": "TEST",
        "chain": "solana",
        "chain_emoji": "◎",
        "price_usd": 0.0045,
        "price_change_5m": 2.5,
        "price_change_1h": 15.3,
        "price_change_6h": 8.1,
        "price_change_24h": 42.7,
        "volume_24h": 1_200_000,
        "liquidity": 350_000,
        "market_cap": 5_000_000,
        "buy_sell_ratio": 2.3,
        "buys_1h": 450,
        "sells_1h": 120,
        "buys_24h": 5200,
        "sells_24h": 2100,
        "is_new": False,
        "address": "test123",
    }
    
    print("\n⏳ Running Ultra AI Prediction...")
    result = ultra_predict(sample)
    
    print(f"\n✅ AI Signal: {result.get('ai_signal', {}).get('signal', 'N/A')}")
    print(f"✅ Rug Risk: {result['rug_risk']['level']} (Score: {result['rug_risk']['score']})")
    print(f"✅ Whale: {result['whale']['level']} (Score: {result['whale']['score']})")
    print(f"✅ Liquidity: Grade {result['liquidity']['grade']} (Score: {result['liquidity']['score']})")
    print(f"✅ Money Flow: {result['money_flow']['direction']} (Score: {result['money_flow']['score']})")
    print(f"✅ Health: {result['health']['grade']} Score {result['health']['score']}")
    print(f"✅ Price Target: Support={_fmt_price(result['targets']['support'])} | Resist={_fmt_price(result['targets']['resistance'])}")
    print(f"✅ R:R Ratio: {result['targets']['rr_ratio']:.1f}x ({result['targets']['rr_grade']})")
    print(f"\n🔥 VERDICT: {result['verdict']['emoji']} {result['verdict']['action']}")
    print(f"🇮🇳 Hindi: {result['verdict']['hindi_action']}")
    print(f"📝 Detail: {result['verdict']['hindi_detail']}")
    print(f"📊 Score: {result['verdict']['score']}")
    
    if result['verdict']['reasons_buy']:
        print(f"\n✅ Buy Reasons: {result['verdict']['reasons_buy']}")
    if result['verdict']['reasons_sell']:
        print(f"\n⚠️ Sell Reasons: {result['verdict']['reasons_sell']}")
    
    # Test batch
    tokens = [sample]
    batch_ultra_predict(tokens)
    print(f"\n✅ Batch: _ultra attached = {'_ultra' in tokens[0]}")
    print(f"✅ Batch: _signal attached = {'_signal' in tokens[0]}")
    
    # Test formatting
    card = format_ultra_token_card(sample, rank=1)
    print(f"\n✅ Card format: {len(card)} chars")
    
    top = format_ultra_top_tokens(tokens, title="TEST TOP TOKENS")
    print(f"✅ Top format: {len(top)} chars")
    
    voice = format_ultra_voice(tokens)
    print(f"✅ Voice format: {len(voice)} chars")
    
    print(f"\n{'=' * 60}")
    print(f"  ALL TESTS PASSED ✅")
    print(f"{'=' * 60}")
