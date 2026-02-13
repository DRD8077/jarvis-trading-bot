"""
🤖⚡ JARVIS AUTO-TRADER v3.0 — AI-Powered Crypto Auto-Investment Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FLOW:
  User Deposits INR → AI Scans -5% Dip Tokens → Auto-Invests → 
  Monitors 24/7 → Partial Book at 2x,5x,10x,50x,100x,1000x →
  Compound Profits → Auto-Withdraw on Target

FEATURES:
  • Multi-source scanning (DexScreener, Pump.fun, CoinDCX)
  • ML + Technical Analysis signal fusion
  • Adaptive risk management per market regime
  • Compound reinvestment engine
  • Auto-withdraw at user-defined target
  • Real-time P&L tracking with tax calculation
  • Strategy modes: Conservative, Balanced, Aggressive, YOLO

100% AI automation — user just deposits and watches money grow.
"""

import os
import json
import time
import logging
import threading
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("AUTO-TRADER")

# ═══════════════════════════════════════════════════════════
#  STRATEGY PROFILES
# ═══════════════════════════════════════════════════════════

STRATEGIES = {
    "conservative": {
        "name": "Conservative",
        "emoji": "🛡️",
        "description": "Lower risk, steady returns. Focus on established coins.",
        "min_gem_score": 50,
        "max_tokens": 15,
        "min_drop_pct": -5.0,
        "max_market_cap": 100_000_000,
        "min_liquidity": 10000,
        "stop_loss_pct": -20.0,
        "take_profit_pcts": [50, 100, 200, 400, 900],
        "compound_pct": 30,
        "rebalance_secs": 120,
        "risk_per_trade_pct": 5.0,
    },
    "balanced": {
        "name": "Balanced",
        "emoji": "⚖️",
        "description": "Mix of safety and growth. Best for most users.",
        "min_gem_score": 35,
        "max_tokens": 10,
        "min_drop_pct": -5.0,
        "max_market_cap": 50_000_000,
        "min_liquidity": 5000,
        "stop_loss_pct": -35.0,
        "take_profit_pcts": [100, 400, 900, 4900, 9900],
        "compound_pct": 50,
        "rebalance_secs": 180,
        "risk_per_trade_pct": 10.0,
    },
    "aggressive": {
        "name": "Aggressive",
        "emoji": "🔥",
        "description": "High risk, high reward. Early-stage micro-caps.",
        "min_gem_score": 20,
        "max_tokens": 8,
        "min_drop_pct": -10.0,
        "max_market_cap": 10_000_000,
        "min_liquidity": 2000,
        "stop_loss_pct": -50.0,
        "take_profit_pcts": [100, 400, 900, 4900, 9900, 99900],
        "compound_pct": 70,
        "rebalance_secs": 120,
        "risk_per_trade_pct": 15.0,
    },
    "yolo": {
        "name": "YOLO Moon",
        "emoji": "🚀",
        "description": "Maximum risk. Micro-caps, meme coins, new launches. 2K → 2Cr dream.",
        "min_gem_score": 10,
        "max_tokens": 5,
        "min_drop_pct": -15.0,
        "max_market_cap": 5_000_000,
        "min_liquidity": 1000,
        "stop_loss_pct": -60.0,
        "take_profit_pcts": [100, 400, 900, 4900, 9900, 99900, 999900],
        "compound_pct": 80,
        "rebalance_secs": 60,
        "risk_per_trade_pct": 25.0,
    },
}

# Auto-trader state file
TRADER_STATE_FILE = Path("auto_trader_state.json")

# ═══════════════════════════════════════════════════════════
#  STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════

_trader_lock = threading.Lock()
_active_traders: Dict[str, dict] = {}
_trader_thread: Optional[threading.Thread] = None
_running = False


def _load_state() -> dict:
    try:
        if TRADER_STATE_FILE.exists():
            return json.loads(TRADER_STATE_FILE.read_text())
    except:
        pass
    return {}


def _save_state(state: dict):
    try:
        TRADER_STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    except Exception as e:
        logger.error(f"Save state error: {e}")


def _safe_import(module_name):
    try:
        return __import__(module_name)
    except:
        return None


# ═══════════════════════════════════════════════════════════
#  CORE AUTO-TRADER ENGINE
# ═══════════════════════════════════════════════════════════

def start_auto_trader(
    chat_id: int,
    amount_inr: float,
    strategy: str = "balanced",
    target_inr: float = 0,
    auto_withdraw: bool = True,
) -> dict:
    """
    Start AI auto-trading for a user.
    
    Args:
        chat_id: Telegram user ID
        amount_inr: Amount to invest (min 100 INR)
        strategy: conservative/balanced/aggressive/yolo
        target_inr: Target amount to auto-withdraw (0 = no limit, ride forever)
        auto_withdraw: Auto-withdraw when target hit
    
    Returns:
        dict with success status, trader_id, investment details
    """
    if strategy not in STRATEGIES:
        strategy = "balanced"
    
    strat = STRATEGIES[strategy]
    
    # Import payment module
    payment = _safe_import("jarvis_payment")
    if not payment:
        return {"error": "Payment system unavailable"}
    
    # Check wallet balance
    wallet = payment.get_wallet(chat_id)
    if amount_inr > wallet["balance_inr"]:
        return {
            "error": f"Insufficient balance. Available: ₹{wallet['balance_inr']:,.2f}",
            "balance": wallet["balance_inr"],
        }
    
    if amount_inr < 100:
        return {"error": "Minimum investment: ₹100"}
    
    # Generate trader ID
    trader_id = f"AT{int(time.time())}{secrets.token_hex(3).upper()}"
    
    # Debit wallet
    new_bal = payment._debit_wallet(chat_id, amount_inr)
    if new_bal < 0:
        return {"error": "Failed to debit wallet"}
    
    # Scan for gems with strategy filters
    gems = _scan_with_strategy(strat)
    
    if not gems:
        payment._credit_wallet(chat_id, amount_inr, "refund_no_gems")
        return {
            "error": "No qualifying tokens found right now. Amount refunded. Market may be too hot — try again when dips appear.",
            "refunded": True,
        }
    
    # Calculate position sizing
    usd_rate = payment._get_usd_inr_rate()
    amount_usd = amount_inr / usd_rate
    num_tokens = min(len(gems), strat["max_tokens"])
    per_token_usd = amount_usd / num_tokens
    
    # Create positions
    positions = []
    for gem in gems[:num_tokens]:
        if gem.get("price_usd", 0) <= 0:
            continue
        
        qty = per_token_usd / gem["price_usd"]
        inv_inr = per_token_usd * usd_rate
        
        position = {
            "id": f"POS{int(time.time())}{secrets.token_hex(2).upper()}",
            "token_id": gem.get("token_id", gem.get("symbol", "UNKNOWN")),
            "symbol": gem.get("symbol", "???"),
            "name": gem.get("name", gem.get("symbol", "Unknown")),
            "chain": gem.get("chain", "solana"),
            "source": gem.get("source", "dexscreener"),
            "buy_price_usd": gem["price_usd"],
            "quantity": qty,
            "invested_usd": per_token_usd,
            "invested_inr": inv_inr,
            "current_price_usd": gem["price_usd"],
            "current_value_usd": per_token_usd,
            "pnl_pct": 0.0,
            "pnl_inr": 0.0,
            "gem_score": gem.get("score", 0),
            "signal_strength": gem.get("signal", "HOLD"),
            "change_at_buy": gem.get("change_24h", 0),
            "market_cap_at_buy": gem.get("market_cap", 0),
            "pair_url": gem.get("pair_url", ""),
            "status": "active",
            "bought_at": datetime.now().isoformat(),
            "take_profit_pcts": strat["take_profit_pcts"],
            "stop_loss_pct": strat["stop_loss_pct"],
            "profits_taken": [],
            "partial_sells": [],
        }
        positions.append(position)
    
    if not positions:
        payment._credit_wallet(chat_id, amount_inr, "refund_no_valid_tokens")
        return {"error": "No valid tokens to invest in. Amount refunded.", "refunded": True}
    
    actual_invested = sum(p["invested_inr"] for p in positions)
    
    # Store in payment system as well
    with payment._wallets_lock:
        wallets = payment._load_wallets()
        uid = str(chat_id)
        for pos in positions:
            wallets[uid]["investments"].append(pos)
        payment._save_wallets(wallets)
    
    # Create trader state
    trader = {
        "trader_id": trader_id,
        "chat_id": chat_id,
        "strategy": strategy,
        "strategy_config": strat,
        "amount_inr": actual_invested,
        "amount_usd": actual_invested / usd_rate,
        "target_inr": target_inr,
        "auto_withdraw": auto_withdraw,
        "positions": [p["id"] for p in positions],
        "status": "active",
        "started_at": datetime.now().isoformat(),
        "total_invested_inr": actual_invested,
        "total_profit_inr": 0.0,
        "total_withdrawn_inr": 0.0,
        "cycles_completed": 0,
        "compounds_done": 0,
        "highest_value_inr": actual_invested,
        "events": [{
            "type": "started",
            "time": datetime.now().isoformat(),
            "detail": f"Invested ₹{actual_invested:,.2f} into {len(positions)} tokens using {strat['name']} strategy",
        }],
    }
    
    # Save trader
    with _trader_lock:
        _active_traders[trader_id] = trader
        state = _load_state()
        state[trader_id] = trader
        _save_state(state)
    
    # Record transaction
    payment._record_tx(chat_id, {
        "type": "auto_trader_start",
        "trader_id": trader_id,
        "strategy": strategy,
        "amount_inr": actual_invested,
        "target_inr": target_inr,
        "tokens": [p["symbol"] for p in positions],
        "created": datetime.now().isoformat(),
    })
    
    # Ensure engine is running
    _ensure_engine_running()
    
    return {
        "success": True,
        "trader_id": trader_id,
        "strategy": strat["name"],
        "strategy_emoji": strat["emoji"],
        "invested_inr": actual_invested,
        "num_tokens": len(positions),
        "positions": positions,
        "target_inr": target_inr,
        "auto_withdraw": auto_withdraw,
        "remaining_balance": new_bal,
        "message": f"🤖 AI Auto-Trader ACTIVATED!\n"
                   f"Strategy: {strat['emoji']} {strat['name']}\n"
                   f"Invested: ₹{actual_invested:,.2f} → {len(positions)} tokens\n"
                   f"Target: {'₹' + f'{target_inr:,.0f}' if target_inr > 0 else '∞ (No limit)'}\n"
                   f"AI will auto-manage, book profits & compound 24/7",
    }


def stop_auto_trader(chat_id: int, trader_id: str = None, sell_all: bool = True) -> dict:
    """Stop auto-trader and optionally sell all positions."""
    payment = _safe_import("jarvis_payment")
    if not payment:
        return {"error": "Payment system unavailable"}
    
    results = []
    with _trader_lock:
        state = _load_state()
        for tid, trader in list(state.items()):
            if trader.get("chat_id") != chat_id:
                continue
            if trader_id and tid != trader_id:
                continue
            if trader.get("status") != "active":
                continue
            
            trader["status"] = "stopped"
            trader["stopped_at"] = datetime.now().isoformat()
            
            if sell_all:
                # Sell all active positions
                sell_result = payment.sell_all(chat_id)
                trader["events"].append({
                    "type": "stopped_sold_all",
                    "time": datetime.now().isoformat(),
                    "detail": f"Stopped & sold all. Total: ₹{sell_result.get('total_sold_inr', 0):,.2f}",
                })
                results.append({
                    "trader_id": tid,
                    "total_sold_inr": sell_result.get("total_sold_inr", 0),
                    "total_profit_inr": sell_result.get("total_profit_inr", 0),
                    "new_balance": sell_result.get("new_balance", 0),
                })
            else:
                results.append({"trader_id": tid, "status": "stopped_positions_open"})
            
            state[tid] = trader
        
        _save_state(state)
    
    if not results:
        return {"error": "No active auto-trader found"}
    
    return {"success": True, "results": results}


def get_trader_status(chat_id: int) -> dict:
    """Get comprehensive auto-trader status for a user."""
    payment = _safe_import("jarvis_payment")
    
    state = _load_state()
    traders = []
    
    for tid, trader in state.items():
        if trader.get("chat_id") != chat_id:
            continue
        
        # Get live portfolio data
        portfolio = {"positions": [], "pnl_pct": 0, "total_current_inr": 0}
        if payment:
            try:
                portfolio = payment.get_portfolio(chat_id)
            except:
                pass
        
        total_value = portfolio.get("total_current_inr", 0) + portfolio.get("balance_inr", 0)
        invested = trader.get("total_invested_inr", 0)
        profit = total_value - invested + trader.get("total_withdrawn_inr", 0)
        
        # Calculate multiplier
        multiplier = total_value / invested if invested > 0 else 1.0
        
        # Check target
        target_hit = False
        target_pct = 0
        if trader.get("target_inr", 0) > 0:
            target_pct = (total_value / trader["target_inr"]) * 100
            target_hit = total_value >= trader["target_inr"]
        
        traders.append({
            "trader_id": tid,
            "strategy": trader.get("strategy", "balanced"),
            "strategy_name": STRATEGIES.get(trader.get("strategy", "balanced"), {}).get("name", "Balanced"),
            "strategy_emoji": STRATEGIES.get(trader.get("strategy", "balanced"), {}).get("emoji", "⚖️"),
            "status": trader.get("status", "unknown"),
            "started_at": trader.get("started_at", ""),
            "invested_inr": invested,
            "current_value_inr": total_value,
            "profit_inr": profit,
            "profit_pct": ((total_value / invested) - 1) * 100 if invested > 0 else 0,
            "multiplier": f"{multiplier:.1f}x",
            "target_inr": trader.get("target_inr", 0),
            "target_pct": target_pct,
            "target_hit": target_hit,
            "total_withdrawn_inr": trader.get("total_withdrawn_inr", 0),
            "cycles_completed": trader.get("cycles_completed", 0),
            "compounds_done": trader.get("compounds_done", 0),
            "highest_value_inr": trader.get("highest_value_inr", invested),
            "positions": portfolio.get("positions", []),
            "events": trader.get("events", [])[-10:],
        })
    
    # Also get wallet info
    wallet_info = {}
    if payment:
        try:
            wallet_info = payment.get_wallet_balance(chat_id)
        except:
            wallet_info = payment.get_wallet(chat_id)
    
    return {
        "traders": traders,
        "active_count": sum(1 for t in traders if t["status"] == "active"),
        "total_invested": sum(t["invested_inr"] for t in traders),
        "total_value": sum(t["current_value_inr"] for t in traders),
        "total_profit": sum(t["profit_inr"] for t in traders),
        "wallet": wallet_info,
    }


def get_available_gems(strategy: str = "balanced") -> dict:
    """Preview what tokens AI would invest in right now."""
    if strategy not in STRATEGIES:
        strategy = "balanced"
    strat = STRATEGIES[strategy]
    
    gems = _scan_with_strategy(strat)
    
    return {
        "strategy": strat["name"],
        "strategy_emoji": strat["emoji"],
        "gems_found": len(gems),
        "top_picks": gems[:strat["max_tokens"]],
        "scan_time": datetime.now().isoformat(),
    }


def compound_profits(chat_id: int, trader_id: str = None) -> dict:
    """Manually trigger compound — reinvest profits into new gems."""
    payment = _safe_import("jarvis_payment")
    if not payment:
        return {"error": "Payment system unavailable"}
    
    wallet = payment.get_wallet(chat_id)
    available = wallet["balance_inr"]
    
    if available < 100:
        return {"error": f"Need minimum ₹100 to compound. Available: ₹{available:,.2f}"}
    
    # Re-invest available balance
    result = start_auto_trader(
        chat_id=chat_id,
        amount_inr=available,
        strategy="balanced",
        target_inr=0,
        auto_withdraw=False,
    )
    
    if result.get("success"):
        result["compound"] = True
        result["message"] = f"🔄 Compounded ₹{available:,.2f} into {result['num_tokens']} new tokens!"
    
    return result


# ═══════════════════════════════════════════════════════════
#  SCANNING ENGINE — Multi-Source Gem Discovery
# ═══════════════════════════════════════════════════════════

def _scan_with_strategy(strat: dict) -> list:
    """Scan for gems using strategy-specific filters."""
    all_gems = []
    
    # Source 1: jarvis_payment gem scanner (DexScreener + Pump.fun)
    try:
        payment = _safe_import("jarvis_payment")
        if payment:
            gems = payment.scan_gem_tokens()
            for g in gems:
                g["source_engine"] = "payment_scanner"
            all_gems.extend(gems)
    except Exception as e:
        logger.error(f"Payment scanner error: {e}")
    
    # Source 2: crypto_engine dip scanner
    try:
        crypto = _safe_import("crypto_engine")
        if crypto:
            dips = crypto.scan_dip_tokens(max_change_h1=strat.get("min_drop_pct", -5.0), limit=20)
            for d in dips:
                d["source_engine"] = "crypto_dip_scanner"
                if "score" not in d:
                    d["score"] = crypto.calculate_gem_score(d).get("score", 0) if hasattr(crypto, "calculate_gem_score") else 30
            all_gems.extend(dips)
            
            # Also get multichain gems
            multi = crypto.scan_multichain_gems(min_score=strat.get("min_gem_score", 20), limit=15)
            for m in multi:
                m["source_engine"] = "multichain_scanner"
            all_gems.extend(multi)
    except Exception as e:
        logger.error(f"Crypto engine error: {e}")
    
    # Source 3: CoinDCX signals (for INR-pair coins)
    try:
        coindcx = _safe_import("coindcx_engine")
        if coindcx:
            signals = coindcx.scan_best_signals(top_n=15)
            for sig in signals:
                if sig.get("signal") in ("STRONG_BUY", "BUY"):
                    gem = {
                        "token_id": sig.get("symbol", ""),
                        "symbol": sig.get("symbol", ""),
                        "name": sig.get("symbol", ""),
                        "price_usd": sig.get("price", 0) / 90,
                        "change_24h": sig.get("change_24h", 0),
                        "market_cap": sig.get("market_cap", 0),
                        "volume_24h": sig.get("volume", 0),
                        "score": sig.get("confidence", 50),
                        "signal": sig.get("signal", "BUY"),
                        "source": "coindcx",
                        "source_engine": "coindcx_ml",
                        "chain": "coindcx",
                    }
                    all_gems.append(gem)
    except Exception as e:
        logger.error(f"CoinDCX scanner error: {e}")
    
    # Deduplicate by token_id/symbol
    seen = set()
    unique_gems = []
    for g in all_gems:
        key = g.get("token_id", g.get("symbol", ""))
        if key and key not in seen:
            seen.add(key)
            unique_gems.append(g)
    
    # Apply strategy filters
    filtered = []
    for g in unique_gems:
        score = g.get("score", 0)
        mcap = g.get("market_cap", 0)
        liq = g.get("liquidity", g.get("volume_24h", 0))
        
        if score >= strat.get("min_gem_score", 10):
            if mcap <= strat.get("max_market_cap", 50_000_000) or mcap == 0:
                if liq >= strat.get("min_liquidity", 1000) or liq == 0:
                    filtered.append(g)
    
    # Sort by score descending
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return filtered


# ═══════════════════════════════════════════════════════════
#  BACKGROUND ENGINE — 24/7 AI Monitor
# ═══════════════════════════════════════════════════════════

def _ensure_engine_running():
    global _trader_thread, _running
    if _running:
        return
    _running = True
    _trader_thread = threading.Thread(target=_engine_loop, daemon=True)
    _trader_thread.start()
    logger.info("🤖 Auto-Trader Engine STARTED — 24/7 AI monitoring active")


def _engine_loop():
    """Master loop: monitor positions, compound, auto-withdraw."""
    global _running
    
    payment = _safe_import("jarvis_payment")
    if not payment:
        logger.error("Payment module not available, engine stopping")
        _running = False
        return
    
    # Also start payment rebalance if not running
    try:
        payment.start_auto_rebalance()
    except:
        pass
    
    cycle = 0
    while _running:
        try:
            cycle += 1
            state = _load_state()
            changed = False
            
            for tid, trader in state.items():
                if trader.get("status") != "active":
                    continue
                
                chat_id = trader.get("chat_id", 0)
                if not chat_id:
                    continue
                
                # Get live portfolio
                try:
                    portfolio = payment.get_portfolio(chat_id)
                except:
                    continue
                
                wallet = payment.get_wallet(chat_id)
                total_value = portfolio.get("total_current_inr", 0) + wallet.get("balance_inr", 0)
                invested = trader.get("total_invested_inr", 0)
                
                # Update highest value
                if total_value > trader.get("highest_value_inr", 0):
                    trader["highest_value_inr"] = total_value
                
                # CHECK AUTO-WITHDRAW TARGET
                target = trader.get("target_inr", 0)
                if target > 0 and total_value >= target and trader.get("auto_withdraw", True):
                    # SELL ALL & WITHDRAW
                    sell_result = payment.sell_all(chat_id)
                    trader["status"] = "target_achieved"
                    trader["total_withdrawn_inr"] += sell_result.get("total_sold_inr", 0)
                    trader["events"].append({
                        "type": "target_achieved",
                        "time": datetime.now().isoformat(),
                        "detail": f"🎯 TARGET HIT! ₹{total_value:,.0f} >= ₹{target:,.0f}. "
                                  f"All positions sold. Profit: ₹{sell_result.get('total_profit_inr', 0):,.0f}",
                    })
                    changed = True
                    logger.info(f"🎯 TARGET ACHIEVED for {chat_id}: ₹{total_value:,.0f}")
                    continue
                
                # COMPOUND PROFITS — reinvest profits periodically
                strat = STRATEGIES.get(trader.get("strategy", "balanced"), STRATEGIES["balanced"])
                compound_pct = strat.get("compound_pct", 50)
                available_balance = wallet.get("balance_inr", 0)
                
                if available_balance >= 500 and cycle % 20 == 0:
                    compound_amount = available_balance * (compound_pct / 100)
                    if compound_amount >= 100:
                        try:
                            invest_result = payment.auto_invest(chat_id, compound_amount)
                            if invest_result.get("success"):
                                trader["compounds_done"] = trader.get("compounds_done", 0) + 1
                                trader["events"].append({
                                    "type": "compound",
                                    "time": datetime.now().isoformat(),
                                    "detail": f"🔄 Compounded ₹{compound_amount:,.0f} into {invest_result.get('num_tokens', 0)} new tokens",
                                })
                                changed = True
                        except:
                            pass
                
                trader["cycles_completed"] = cycle
                
            if changed:
                _save_state(state)
                
        except Exception as e:
            logger.error(f"Engine loop error: {e}")
        
        time.sleep(60)  # Check every 60 seconds


def stop_engine():
    """Stop the background engine."""
    global _running
    _running = False
    logger.info("🛑 Auto-Trader Engine STOPPED")


# ═══════════════════════════════════════════════════════════
#  ANALYTICS & REPORTING
# ═══════════════════════════════════════════════════════════

def get_performance_report(chat_id: int) -> dict:
    """Generate comprehensive performance analytics."""
    payment = _safe_import("jarvis_payment")
    if not payment:
        return {"error": "Payment system unavailable"}
    
    state = _load_state()
    portfolio = payment.get_portfolio(chat_id)
    wallet = payment.get_wallet(chat_id)
    
    total_invested = 0
    total_profit = 0
    total_withdrawn = 0
    best_trade = None
    worst_trade = None
    active_traders = 0
    
    for tid, trader in state.items():
        if trader.get("chat_id") != chat_id:
            continue
        total_invested += trader.get("total_invested_inr", 0)
        total_withdrawn += trader.get("total_withdrawn_inr", 0)
        if trader.get("status") == "active":
            active_traders += 1
    
    # Find best/worst from trade history
    trade_history = wallet.get("trade_history", [])
    for trade in trade_history:
        pnl = trade.get("pnl_pct", 0)
        if best_trade is None or pnl > best_trade.get("pnl_pct", 0):
            best_trade = trade
        if worst_trade is None or pnl < worst_trade.get("pnl_pct", 0):
            worst_trade = trade
    
    current_value = portfolio.get("total_value_inr", 0)
    total_pnl = current_value - total_invested + total_withdrawn
    
    winners = portfolio.get("winners", 0)
    losers = portfolio.get("losers", 0)
    win_rate = (winners / (winners + losers) * 100) if (winners + losers) > 0 else 0
    
    return {
        "total_invested_inr": total_invested,
        "current_value_inr": current_value,
        "total_profit_inr": total_pnl,
        "total_withdrawn_inr": total_withdrawn,
        "roi_pct": ((current_value + total_withdrawn) / total_invested - 1) * 100 if total_invested > 0 else 0,
        "multiplier": (current_value + total_withdrawn) / total_invested if total_invested > 0 else 1,
        "active_positions": len(portfolio.get("positions", [])),
        "active_traders": active_traders,
        "win_rate": win_rate,
        "winners": winners,
        "losers": losers,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "tax_info": portfolio.get("tax_info", {}),
        "balance_inr": wallet.get("balance_inr", 0),
    }


def get_all_strategies() -> dict:
    """Return all available strategies with descriptions."""
    return {
        "strategies": [
            {
                "id": sid,
                "name": s["name"],
                "emoji": s["emoji"],
                "description": s["description"],
                "risk_level": ["Low", "Medium", "High", "Extreme"][i],
                "max_tokens": s["max_tokens"],
                "stop_loss": f"{s['stop_loss_pct']}%",
                "targets": [f"{tp/100+1:.0f}x" for tp in s["take_profit_pcts"]],
                "compound_pct": s["compound_pct"],
            }
            for i, (sid, s) in enumerate(STRATEGIES.items())
        ]
    }


# Initialize on import — load saved state
try:
    _saved = _load_state()
    has_active = any(t.get("status") == "active" for t in _saved.values())
    if has_active:
        _ensure_engine_running()
except:
    pass
