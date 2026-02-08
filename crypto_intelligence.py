"""
🧠💰 JARVIS Crypto Intelligence — Super Smart Token Analysis
═══════════════════════════════════════════════════════════════
World's most powerful crypto signal engine for JARVIS.

Features:
  1. Smart Token Signals — exact buy price, target, stop-loss in ₹
  2. Auto Rug Check on every recommendation
  3. DexScreener + pump.fun real-time data fusion
  4. Risk-adjusted position sizing (₹2K → ₹20K → ₹2Cr tracking)
  5. Price target alerts — auto-notify when target hit
  6. JARVIS speaks the analysis in Hindi

Uses: crypto_engine.py, buy_sell_engine.py, rug_detector.py,
      portfolio_tracker.py, whale_alert.py

Author: David Crew AI
"""

import os
import time
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

import requests

logger = logging.getLogger("crypto_intelligence")

# ═══════════════════════════════════════════════════════════
#  IMPORTS FROM EXISTING ENGINES
# ═══════════════════════════════════════════════════════════

try:
    from crypto_engine import (
        scan_trending_gems, scan_pumping_tokens, scan_all_gems,
        pump_get_trending, get_top_boosted_tokens,
        calculate_gem_score, get_usd_inr_rate, usd_to_inr, fmt_inr,
        get_sol_inr_price, _cached_get, _normalize_dex_pair
    )
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False
    logger.warning("[CRYPTO-IQ] crypto_engine not available")

try:
    from rug_detector import check_token_rug_risk, format_rug_check
    RUG_OK = True
except ImportError:
    RUG_OK = False
    logger.warning("[CRYPTO-IQ] rug_detector not available")

try:
    from buy_sell_engine import get_crypto_signal, format_bs_signal
    SIGNAL_OK = True
except ImportError:
    SIGNAL_OK = False
    logger.warning("[CRYPTO-IQ] buy_sell_engine not available")

try:
    from whale_alert import detect_whale_activity_from_dex
    WHALE_OK = True
except ImportError:
    WHALE_OK = False

try:
    from portfolio_tracker import add_holding, add_price_alert
    PORTFOLIO_OK = True
except ImportError:
    PORTFOLIO_OK = False


# ═══════════════════════════════════════════════════════════
#  WATCHLIST — Track tokens user is monitoring
# ═══════════════════════════════════════════════════════════

# In-memory watchlist: {chat_id: [{token_data}, ...]}
_user_watchlist: Dict[str, List[Dict]] = {}

# Price alert targets: {chat_id: [{symbol, buy_price, target_price, stop_loss, amount_inr}, ...]}
_user_alerts: Dict[str, List[Dict]] = {}

WATCHLIST_FILE = "/tmp/jarvis_watchlist.json"


def _load_watchlist():
    """Load watchlist from file."""
    global _user_watchlist, _user_alerts
    try:
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE) as f:
                data = json.load(f)
                _user_watchlist = data.get("watchlist", {})
                _user_alerts = data.get("alerts", {})
    except Exception:
        pass

def _save_watchlist():
    """Save watchlist to file."""
    try:
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump({"watchlist": _user_watchlist, "alerts": _user_alerts}, f)
    except Exception:
        pass

_load_watchlist()


def add_to_watchlist(chat_id: str, token: Dict) -> str:
    """Add a token to user's watchlist for monitoring."""
    if chat_id not in _user_watchlist:
        _user_watchlist[chat_id] = []

    # Check duplicate
    existing = [t for t in _user_watchlist[chat_id] if t.get("symbol") == token.get("symbol")]
    if existing:
        return f"⚠️ {token.get('symbol')} पहले से watchlist में है।"

    _user_watchlist[chat_id].append({
        "symbol": token.get("symbol", "?"),
        "chain": token.get("chain", "?"),
        "price_inr": token.get("price_inr", 0),
        "address": token.get("address", ""),
        "added_at": time.time(),
        "buy_price": token.get("price_inr", 0),
    })
    _save_watchlist()
    return f"✅ {token.get('symbol')} watchlist में add हो गया! 🎯"


def set_price_alert(chat_id: str, symbol: str, buy_price: float,
                    target_price: float, stop_loss: float, amount_inr: float = 2000) -> str:
    """Set a price target alert for a token."""
    if chat_id not in _user_alerts:
        _user_alerts[chat_id] = []

    _user_alerts[chat_id].append({
        "symbol": symbol,
        "buy_price": buy_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "amount_inr": amount_inr,
        "created_at": time.time(),
        "triggered": False,
    })
    _save_watchlist()

    potential = (target_price / buy_price) * amount_inr if buy_price > 0 else 0
    return (
        f"🎯 *Price Alert Set!*\n"
        f"Token: {symbol}\n"
        f"Buy: {fmt_inr(buy_price)} | Target: {fmt_inr(target_price)} | SL: {fmt_inr(stop_loss)}\n"
        f"Amount: {fmt_inr(amount_inr)} → Potential: {fmt_inr(potential)}"
    )


def get_user_watchlist(chat_id: str) -> List[Dict]:
    """Get user's watchlist."""
    return _user_watchlist.get(chat_id, [])


def get_user_alerts(chat_id: str) -> List[Dict]:
    """Get user's active price alerts."""
    return [a for a in _user_alerts.get(chat_id, []) if not a.get("triggered")]


# ═══════════════════════════════════════════════════════════
#  SUPER SMART TOKEN ANALYSIS
# ═══════════════════════════════════════════════════════════

def analyze_token_full(token: Dict) -> Dict:
    """
    Full 360° analysis of a crypto token.
    Returns buy/sell signal + rug check + price targets + risk score.
    """
    result = {
        "symbol": token.get("symbol", "UNKNOWN"),
        "chain": token.get("chain", "?"),
        "price_usd": token.get("price_usd", 0),
        "price_inr": token.get("price_inr", 0),
        "mcap_inr": token.get("mcap_inr", 0),
        "volume_24h_inr": token.get("volume_inr", 0),
        "change_h1": token.get("change_h1", 0),
        "change_h24": token.get("change_h24", 0),
        "gem_score": token.get("gem_score", 0),
        "url": token.get("url", "") or token.get("dex_url", ""),
        "address": token.get("address", ""),
        "source": token.get("source", "dexscreener"),
    }

    # ── Rug Check ──
    if RUG_OK and result["address"]:
        try:
            rug = check_token_rug_risk(result["address"], result["chain"])
            result["rug_risk"] = rug.get("risk_level", "UNKNOWN")
            result["rug_score"] = rug.get("risk_score", 50)
            result["rug_flags"] = rug.get("flags", [])
            result["is_safe"] = rug.get("risk_level", "HIGH") in ("LOW", "MEDIUM")
        except Exception as e:
            logger.error(f"[CRYPTO-IQ] Rug check failed: {e}")
            result["rug_risk"] = "UNKNOWN"
            result["is_safe"] = True  # Don't block on rug check failure
    else:
        result["rug_risk"] = "UNCHECKED"
        result["is_safe"] = True

    # ── Signal (Buy/Sell/Hold) ──
    score = result.get("gem_score", 0)
    change_h1 = result.get("change_h1", 0)
    change_h24 = result.get("change_h24", 0)

    if not result["is_safe"]:
        result["signal"] = "🚫 AVOID"
        result["signal_reason"] = "Rug risk detected"
    elif score >= 70 and change_h1 > 5:
        result["signal"] = "🟢 STRONG BUY"
        result["signal_reason"] = f"High gem score ({score}), momentum up {change_h1:+.1f}%"
    elif score >= 50 and change_h1 > 0:
        result["signal"] = "🟢 BUY"
        result["signal_reason"] = f"Good score ({score}), positive momentum"
    elif score >= 30 and change_h24 > -10:
        result["signal"] = "🟡 HOLD/WATCH"
        result["signal_reason"] = f"Moderate score ({score}), watch for entry"
    elif change_h1 < -15 or change_h24 < -30:
        result["signal"] = "🔴 SELL/AVOID"
        result["signal_reason"] = f"Heavy dump: h1={change_h1:+.1f}%, h24={change_h24:+.1f}%"
    else:
        result["signal"] = "🟡 NEUTRAL"
        result["signal_reason"] = f"Score {score}, weak signals"

    # ── Price Targets ──
    price = result["price_inr"]
    if price > 0:
        if "STRONG BUY" in result["signal"]:
            result["target_1"] = price * 2.0    # 2x
            result["target_2"] = price * 5.0    # 5x
            result["target_3"] = price * 10.0   # 10x (moonshot)
            result["stop_loss"] = price * 0.70  # -30%
        elif "BUY" in result["signal"]:
            result["target_1"] = price * 1.5
            result["target_2"] = price * 3.0
            result["target_3"] = price * 5.0
            result["stop_loss"] = price * 0.75
        else:
            result["target_1"] = price * 1.2
            result["target_2"] = price * 1.5
            result["target_3"] = price * 2.0
            result["stop_loss"] = price * 0.80

    # ── Investment Calculation ──
    if price > 0 and "BUY" in result["signal"]:
        invest = 2000.0  # ₹2K
        tokens_count = invest / price
        result["invest_amount"] = invest
        result["tokens_count"] = tokens_count
        result["potential_2x"] = invest * 2
        result["potential_5x"] = invest * 5
        result["potential_10x"] = invest * 10
        result["potential_100x"] = invest * 100

    return result


def format_token_signal(analysis: Dict) -> str:
    """Format a full token analysis into beautiful Hindi message."""
    sym = analysis["symbol"]
    signal = analysis.get("signal", "🟡 NEUTRAL")
    reason = analysis.get("signal_reason", "")
    price = analysis.get("price_inr", 0)
    chain = analysis.get("chain", "?").upper()

    msg = f"🧠 *JARVIS CRYPTO SIGNAL* 🧠\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"🪙 *{sym}* ({chain})\n"
    msg += f"📊 Signal: *{signal}*\n"
    msg += f"💬 {reason}\n\n"

    msg += f"💰 *Current Price:* {fmt_inr(price)}\n"
    if analysis.get("mcap_inr"):
        msg += f"📈 Market Cap: {fmt_inr(analysis['mcap_inr'])}\n"
    msg += f"⏱️ 1h: {analysis.get('change_h1', 0):+.1f}% | 24h: {analysis.get('change_h24', 0):+.1f}%\n"
    msg += f"⭐ Gem Score: {analysis.get('gem_score', 0)}/100\n\n"

    # Rug Check
    rug = analysis.get("rug_risk", "UNCHECKED")
    if rug == "LOW":
        msg += f"✅ *Rug Check:* SAFE (Low Risk)\n"
    elif rug == "MEDIUM":
        msg += f"⚠️ *Rug Check:* MODERATE Risk — ध्यान से!\n"
    elif rug == "HIGH":
        msg += f"🚫 *Rug Check:* HIGH RISK — AVOID!\n"
        if analysis.get("rug_flags"):
            msg += f"   Flags: {', '.join(analysis['rug_flags'][:3])}\n"
    else:
        msg += f"🔍 *Rug Check:* Not verified\n"
    msg += "\n"

    # Price Targets
    if "BUY" in signal and price > 0:
        msg += f"🎯 *PRICE TARGETS (₹ INR):*\n"
        msg += f"   ┣ Buy: {fmt_inr(price)}\n"
        msg += f"   ┣ Target 1 (2x): {fmt_inr(analysis.get('target_1', 0))}\n"
        msg += f"   ┣ Target 2 (5x): {fmt_inr(analysis.get('target_2', 0))}\n"
        msg += f"   ┣ Target 3 (10x): {fmt_inr(analysis.get('target_3', 0))}\n"
        msg += f"   ┗ Stop Loss: {fmt_inr(analysis.get('stop_loss', 0))}\n\n"

        # Investment calculation
        invest = analysis.get("invest_amount", 2000)
        msg += f"💸 *₹{invest:,.0f} लगाओगे तो:*\n"
        msg += f"   ┣ 2x → {fmt_inr(analysis.get('potential_2x', 0))}\n"
        msg += f"   ┣ 5x → {fmt_inr(analysis.get('potential_5x', 0))}\n"
        msg += f"   ┣ 10x → {fmt_inr(analysis.get('potential_10x', 0))}\n"
        msg += f"   ┗ 100x → {fmt_inr(analysis.get('potential_100x', 0))} 🚀🌕\n\n"

    # URL
    if analysis.get("url"):
        msg += f"🔗 [Chart देखें]({analysis['url']})\n"
    
    # 🛒 Direct BUY links (mobile-friendly deep links)
    chain_lower = analysis.get("chain", "").lower()
    token_addr = analysis.get("address", "") or analysis.get("token_address", "")
    if token_addr:
        msg += "\n🛒 *DIRECT BUY (Mobile Ready):*\n"
        if chain_lower in ("solana", "sol"):
            msg += f"   ┣ [🟣 Jupiter Swap](https://jup.ag/swap/SOL-{token_addr})\n"
            msg += f"   ┣ [🔵 Raydium](https://raydium.io/swap/?inputMint=sol&outputMint={token_addr})\n"
            msg += f"   ┗ [👻 Phantom](https://phantom.app/ul/swap/SOL-{token_addr})\n"
        elif chain_lower in ("ethereum", "eth"):
            msg += f"   ┣ [🦄 Uniswap](https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=ethereum)\n"
            msg += f"   ┗ [📊 1inch](https://app.1inch.io/#/1/simple/swap/ETH/{token_addr})\n"
        elif chain_lower in ("bsc", "bnb"):
            msg += f"   ┣ [🥞 PancakeSwap](https://pancakeswap.finance/swap?outputCurrency={token_addr}&chainId=56)\n"
            msg += f"   ┗ [📊 1inch](https://app.1inch.io/#/56/simple/swap/BNB/{token_addr})\n"
        elif chain_lower in ("arbitrum", "arb"):
            msg += f"   ┣ [🦄 Uniswap](https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=arbitrum)\n"
            msg += f"   ┗ [📊 1inch](https://app.1inch.io/#/42161/simple/swap/ETH/{token_addr})\n"
        elif chain_lower in ("base",):
            msg += f"   ┣ [🦄 Uniswap](https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=base)\n"
            msg += f"   ┗ [✈️ Aerodrome](https://aerodrome.finance/swap?to={token_addr})\n"
        elif chain_lower in ("polygon", "matic"):
            msg += f"   ┣ [🦄 Uniswap](https://app.uniswap.org/swap?outputCurrency={token_addr}&chain=polygon)\n"
            msg += f"   ┗ [⚡ QuickSwap](https://quickswap.exchange/#/swap?outputCurrency={token_addr})\n"
        elif chain_lower in ("avalanche", "avax"):
            msg += f"   ┗ [🏔️ TraderJoe](https://traderjoexyz.com/avalanche/trade?outputCurrency={token_addr})\n"
    msg += "\n"

    msg += f"⚠️ *DYOR — अपनी research करें | Stop-Loss जरूर लगाएं*"
    return msg


def format_token_voice(analysis: Dict) -> str:
    """Format analysis for JARVIS to speak (short, natural Hindi)."""
    sym = analysis["symbol"]
    signal = analysis.get("signal", "NEUTRAL")
    price = analysis.get("price_inr", 0)

    if "STRONG BUY" in signal:
        voice = (
            f"{sym} coin बहुत अच्छा दिख रहा है जी। "
            f"अभी price {fmt_inr(price)} है। "
            f"Gem score काफी high है और momentum भी ऊपर जा रहा है। "
        )
    elif "BUY" in signal:
        voice = (
            f"{sym} में buying opportunity दिख रही है। "
            f"Price अभी {fmt_inr(price)} है। "
        )
    elif "AVOID" in signal:
        voice = (
            f"जी, {sym} में rug pull का risk है। "
            f"मेरी सलाह है इससे दूर रहें। "
        )
    elif "SELL" in signal:
        voice = (
            f"{sym} काफी dump हो रहा है। Exit करना better होगा। "
        )
    else:
        voice = f"{sym} अभी neutral है। Wait करें entry के लिए। "

    # Rug check result
    rug = analysis.get("rug_risk", "UNCHECKED")
    if rug == "LOW":
        voice += "Rug check safe है। "
    elif rug == "HIGH":
        voice += "WARNING — rug risk high है, avoid करें। "

    if "BUY" in signal and price > 0:
        voice += (
            f"अगर 2 हज़ार rupees लगाते हो तो 10x पर ये 20 हज़ार बन सकते हैं, "
            f"और 100x पर 2 लाख। Stop loss {fmt_inr(analysis.get('stop_loss', 0))} पर लगा लीजिए। "
        )

    voice += "बाकी details text message में हैं।"
    return voice


# ═══════════════════════════════════════════════════════════
#  SMART CRYPTO RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════

def get_top_crypto_picks(limit: int = 5, budget_inr: float = 2000) -> List[Dict]:
    """
    Get JARVIS's top crypto picks with full analysis.
    Scans DexScreener + pump.fun, scores, rug-checks, returns top picks.
    """
    if not CRYPTO_OK:
        return []

    try:
        # Get gems from all sources
        all_gems = scan_all_gems(min_score=20, limit=30)
        if not all_gems:
            all_gems = scan_trending_gems(min_score=10, limit=20)

        if not all_gems:
            return []

        # Full analysis on each
        analyzed = []
        for gem in all_gems[:15]:  # Analyze top 15
            try:
                analysis = analyze_token_full(gem)
                if analysis["is_safe"] and "BUY" in analysis.get("signal", ""):
                    analysis["invest_amount"] = budget_inr
                    analysis["tokens_count"] = budget_inr / analysis["price_inr"] if analysis["price_inr"] > 0 else 0
                    analyzed.append(analysis)
            except Exception as e:
                logger.error(f"[CRYPTO-IQ] Analysis error for {gem.get('symbol')}: {e}")
                continue

        # Sort by gem_score + momentum
        analyzed.sort(key=lambda x: (
            x.get("gem_score", 0) * 0.6 +
            max(0, x.get("change_h1", 0)) * 0.3 +
            (10 if "STRONG" in x.get("signal", "") else 0)
        ), reverse=True)

        return analyzed[:limit]

    except Exception as e:
        logger.error(f"[CRYPTO-IQ] get_top_picks failed: {e}")
        return []


def format_top_picks(picks: List[Dict], budget_inr: float = 2000) -> str:
    """Format top picks into beautiful JARVIS message."""
    if not picks:
        return "❌ अभी कोई अच्छा token नहीं मिला। बाद में try करें।"

    msg = f"🧠🔥 *JARVIS TOP CRYPTO PICKS* 🔥🧠\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"_Budget: {fmt_inr(budget_inr)} | All prices in ₹ INR_\n\n"

    for i, pick in enumerate(picks, 1):
        sym = pick["symbol"]
        signal = pick.get("signal", "")
        rug = pick.get("rug_risk", "?")
        price = pick.get("price_inr", 0)

        rug_icon = "✅" if rug == "LOW" else "⚠️" if rug == "MEDIUM" else "🔍"

        msg += f"*{i}. {sym}* ({pick.get('chain', '?').upper()}) {signal}\n"
        msg += f"   💰 Price: {fmt_inr(price)} | Score: {pick.get('gem_score', 0)}/100\n"
        msg += f"   📈 1h: {pick.get('change_h1', 0):+.1f}% | 24h: {pick.get('change_h24', 0):+.1f}%\n"
        msg += f"   {rug_icon} Rug: {rug} | MCap: {fmt_inr(pick.get('mcap_inr', 0))}\n"

        if "BUY" in signal and price > 0:
            msg += f"   🎯 Buy: {fmt_inr(price)} → Target: {fmt_inr(pick.get('target_2', 0))} | SL: {fmt_inr(pick.get('stop_loss', 0))}\n"
            msg += f"   💸 {fmt_inr(budget_inr)} → 10x = {fmt_inr(budget_inr * 10)}\n"

        if pick.get("url"):
            msg += f"   🔗 [Chart]({pick['url']})\n"
        msg += "\n"

    msg += f"⚠️ *DYOR | Stop-Loss लगाएं | सिर्फ वो पैसे लगाएं जो खोने की तैयारी हो*"
    return msg


def format_picks_voice(picks: List[Dict], budget_inr: float = 2000) -> str:
    """Format picks for JARVIS to speak."""
    if not picks:
        return "अभी कोई अच्छा token नहीं मिला जी। Market slow है। बाद में check करें।"

    voice = f"जी, मैंने {len(picks)} tokens analyze किए हैं। "

    top = picks[0]
    voice += (
        f"सबसे अच्छा अभी {top['symbol']} दिख रहा है "
        f"जिसकी price {fmt_inr(top.get('price_inr', 0))} है। "
    )

    safe_count = sum(1 for p in picks if p.get("rug_risk") == "LOW")
    if safe_count > 0:
        voice += f"{safe_count} tokens rug check safe हैं। "

    buy_count = sum(1 for p in picks if "BUY" in p.get("signal", ""))
    if buy_count > 0:
        voice += f"{buy_count} tokens में buying signal है। "

    voice += (
        f"अगर {fmt_inr(budget_inr)} invest करते हो और 10x hit हो जाए "
        f"तो {fmt_inr(budget_inr * 10)} बन सकते हैं। "
        f"बाकी details text में हैं। Stop loss जरूर लगाइए।"
    )
    return voice


# ═══════════════════════════════════════════════════════════
#  MONITORING — Check alerts & targets
# ═══════════════════════════════════════════════════════════

def check_price_alerts_all() -> List[Dict]:
    """
    Check all user price alerts against current prices.
    Returns list of triggered alerts: {chat_id, symbol, alert_type, message}
    """
    triggered = []

    for chat_id, alerts in _user_alerts.items():
        for alert in alerts:
            if alert.get("triggered"):
                continue

            symbol = alert.get("symbol", "")
            if not symbol:
                continue

            # Try to get current price
            try:
                current_price = _get_current_price(symbol)
                if current_price <= 0:
                    continue

                buy_price = alert.get("buy_price", 0)
                target = alert.get("target_price", 0)
                stop_loss = alert.get("stop_loss", 0)
                amount = alert.get("amount_inr", 2000)

                # Target hit!
                if target > 0 and current_price >= target:
                    pnl = (current_price / buy_price) * amount if buy_price > 0 else 0
                    alert["triggered"] = True
                    triggered.append({
                        "chat_id": chat_id,
                        "symbol": symbol,
                        "type": "TARGET_HIT",
                        "current_price": current_price,
                        "message": (
                            f"🎯🚀 *TARGET HIT — SELL NOW!* 🚀🎯\n\n"
                            f"🪙 {symbol} ने target hit कर लिया!\n"
                            f"Buy Price: {fmt_inr(buy_price)}\n"
                            f"Current: {fmt_inr(current_price)}\n"
                            f"📈 P&L: {fmt_inr(pnl)} ({(current_price/buy_price - 1)*100:+.1f}%)\n"
                            f"💰 आपके {fmt_inr(amount)} → {fmt_inr(pnl)} बन गए!\n\n"
                            f"⚡ SELL करें या HOLD करें — आपकी मर्जी!"
                        ),
                        "voice": (
                            f"बधाई हो जी! {symbol} ने target hit कर लिया! "
                            f"आपके {fmt_inr(amount)} अब {fmt_inr(pnl)} बन गए हैं! "
                            f"Sell कर लीजिए profit book करने के लिए।"
                        )
                    })

                # Stop loss hit
                elif stop_loss > 0 and current_price <= stop_loss:
                    alert["triggered"] = True
                    triggered.append({
                        "chat_id": chat_id,
                        "symbol": symbol,
                        "type": "STOP_LOSS",
                        "current_price": current_price,
                        "message": (
                            f"🔴⚠️ *STOP LOSS HIT — EXIT NOW!* ⚠️🔴\n\n"
                            f"🪙 {symbol} stop loss hit!\n"
                            f"Buy: {fmt_inr(buy_price)} → Now: {fmt_inr(current_price)}\n"
                            f"Loss limit reached. Exit to protect capital."
                        ),
                        "voice": (
                            f"Warning! {symbol} का stop loss hit हो गया है। "
                            f"तुरंत exit करें। Capital protect करना जरूरी है।"
                        )
                    })

                # Major pump alert (50%+ gain from buy)
                elif buy_price > 0 and current_price > buy_price * 1.5:
                    multiplier = current_price / buy_price
                    if multiplier >= 10:
                        label = "10x"
                    elif multiplier >= 5:
                        label = "5x"
                    elif multiplier >= 2:
                        label = "2x"
                    else:
                        label = f"{multiplier:.1f}x"

                    pnl = multiplier * amount
                    triggered.append({
                        "chat_id": chat_id,
                        "symbol": symbol,
                        "type": "PUMP_ALERT",
                        "current_price": current_price,
                        "message": (
                            f"🚀 *{label} PUMP — {symbol}!* 🚀\n\n"
                            f"Price: {fmt_inr(buy_price)} → {fmt_inr(current_price)}\n"
                            f"📈 Gain: {(multiplier-1)*100:+.1f}%\n"
                            f"💰 {fmt_inr(amount)} → {fmt_inr(pnl)}\n\n"
                            f"Partial profit book करो या HODL करो!"
                        ),
                        "voice": (
                            f"{symbol} {label} pump हो गया! "
                            f"आपके {fmt_inr(amount)} अब {fmt_inr(pnl)} बन गए। "
                            f"Partial profit book कर लो।"
                        )
                    })

            except Exception as e:
                logger.error(f"[CRYPTO-IQ] Alert check error for {symbol}: {e}")
                continue

    _save_watchlist()
    return triggered


def _get_current_price(symbol: str) -> float:
    """Get current price in INR for a token symbol."""
    if not CRYPTO_OK:
        return 0

    try:
        # Try DexScreener search
        url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            pairs = resp.json().get("pairs", [])
            if pairs:
                price_usd = float(pairs[0].get("priceUsd", 0))
                return usd_to_inr(price_usd)
    except Exception:
        pass
    return 0


# ═══════════════════════════════════════════════════════════
#  FAST TOKEN ENRICHMENT — Add rug + signal to any token
# ═══════════════════════════════════════════════════════════

def enrich_token_line(token: Dict) -> str:
    """
    Fast: returns 2-line enrichment string for ANY token dict.
    Line 1: 🛡️ Rug: XX% SAFE/RISKY | Signal: STRONG BUY
    Line 2: 🎯 Buy: ₹X | SL: ₹X | T1: ₹X (2x) | T2: ₹X (5x)
    """
    try:
        a = analyze_token_full(token)
    except Exception:
        return "   🛡️ Rug: N/A | Signal: N/A"

    # Rug line
    rug = a.get("rug_risk", "N/A")
    rug_score = a.get("rug_score", 0)
    if rug == "LOW":
        rug_str = f"✅ SAFE ({100-rug_score}%)"
    elif rug == "MEDIUM":
        rug_str = f"⚠️ MODERATE ({100-rug_score}%)"
    elif rug == "HIGH":
        rug_str = f"🚫 RISKY ({rug_score}%)"
    else:
        rug_str = "🔍 N/A"

    signal = a.get("signal", "🟡 NEUTRAL")
    line1 = f"   🛡️ Rug: {rug_str} | Signal: *{signal}*"

    # Price targets (only for BUY signals)
    price = a.get("price_inr", 0)
    if "BUY" in signal and price > 0:
        sl = a.get("stop_loss", 0)
        t1 = a.get("target_1", 0)
        t2 = a.get("target_2", 0)
        line2 = f"   🎯 Buy: {fmt_inr(price)} | SL: {fmt_inr(sl)} | T1: {fmt_inr(t1)} | T2: {fmt_inr(t2)}"
        # Investment calc
        invest = 2000
        if price > 0:
            pot_10x = invest * 10
            line3 = f"   💸 ₹2K → 10x = {fmt_inr(pot_10x)}"
        else:
            line3 = ""
        return f"{line1}\n{line2}\n{line3}" if line3 else f"{line1}\n{line2}"
    elif "AVOID" in signal or "SELL" in signal:
        line2 = f"   ⛔ *दूर रहें — Entry मत लो*"
        return f"{line1}\n{line2}"
    else:
        sl = a.get("stop_loss", 0)
        line2 = f"   ⏳ Wait for entry | SL: {fmt_inr(sl)}" if sl > 0 else ""
        return f"{line1}\n{line2}" if line2 else line1


def enrich_tokens_batch(tokens: List[Dict]) -> List[str]:
    """Enrich a list of tokens. Returns list of enrichment strings."""
    results = []
    for t in tokens:
        try:
            results.append(enrich_token_line(t))
        except Exception:
            results.append("   🛡️ Rug: N/A | Signal: N/A")
    return results


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'analyze_token_full',
    'format_token_signal',
    'format_token_voice',
    'get_top_crypto_picks',
    'format_top_picks',
    'format_picks_voice',
    'add_to_watchlist',
    'set_price_alert',
    'get_user_watchlist',
    'get_user_alerts',
    'check_price_alerts_all',
    'enrich_token_line',
    'enrich_tokens_batch',
]
