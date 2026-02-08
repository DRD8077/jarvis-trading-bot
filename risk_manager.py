"""
========================================================================================
  ADVANCED RISK MANAGEMENT MODULE — Kelly Criterion | Position Sizing | Drawdown Control
========================================================================================

Professional-grade risk management for Indian market trading:
  - Kelly Criterion optimal bet sizing
  - Dynamic position sizing based on volatility (ATR)
  - Maximum drawdown limits and circuit breakers
  - Risk-reward ratio calculator
  - Portfolio heat tracking
  - Trailing stop-loss engine
  - Lot size calculations for NIFTY/SENSEX options
  - Investment amount to lot/strike calculator (₹2K, ₹5K, ₹20K, ₹50K)

All calculations in INR (₹).
"""

import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger("risk_manager")

# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS — Indian Market
# ═══════════════════════════════════════════════════════════════════════════

# Lot sizes
NIFTY_LOT_SIZE = 25
SENSEX_LOT_SIZE = 10  # Mini SENSEX
BANKNIFTY_LOT_SIZE = 15
FINNIFTY_LOT_SIZE = 25

# Strike intervals
NIFTY_STRIKE_STEP = 50
SENSEX_STRIKE_STEP = 100
BANKNIFTY_STRIKE_STEP = 100

# Risk limits
MAX_RISK_PER_TRADE_PCT = 2.0    # Max 2% of capital per trade
MAX_PORTFOLIO_HEAT_PCT = 10.0   # Max 10% total portfolio risk
MAX_DRAWDOWN_PCT = 15.0         # Stop trading at 15% drawdown
DAILY_LOSS_LIMIT_PCT = 3.0      # Max 3% daily loss

# Margin requirements (approximate)
NIFTY_MARGIN_PER_LOT = 125000   # ₹1.25L per lot
SENSEX_MARGIN_PER_LOT = 80000   # ₹80K per lot


# ═══════════════════════════════════════════════════════════════════════════
#  KELLY CRITERION
# ═══════════════════════════════════════════════════════════════════════════

def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> Dict[str, float]:
    """Calculate optimal position size using Kelly Criterion.
    
    win_rate: probability of winning (0 to 1)
    avg_win: average profit on winning trades (in ₹ or %)
    avg_loss: average loss on losing trades (positive number, in ₹ or %)
    
    Returns optimal fraction of capital to risk.
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return {"kelly_pct": 0, "half_kelly_pct": 0, "quarter_kelly_pct": 0}

    # Kelly formula: f* = (p * b - q) / b
    # where p = win rate, q = loss rate, b = win/loss ratio
    b = avg_win / avg_loss
    p = win_rate
    q = 1 - p

    kelly_f = (p * b - q) / b

    # Never risk more than Kelly suggests
    kelly_f = max(0, kelly_f)

    return {
        "kelly_pct": round(kelly_f * 100, 2),
        "half_kelly_pct": round(kelly_f * 50, 2),       # Conservative
        "quarter_kelly_pct": round(kelly_f * 25, 2),     # Very conservative
        "win_loss_ratio": round(b, 2),
        "expected_value": round(p * avg_win - q * avg_loss, 2),
    }


def kelly_from_real_trades() -> Dict[str, Any]:
    """Calculate Kelly Criterion using REAL trade accuracy from trade_tracker.
    
    This replaces guessed win_rate with actual verified accuracy.
    Returns Kelly position sizing based on self-learned stats.
    """
    try:
        from trade_tracker import get_real_win_rate
        win_rate, avg_win, avg_loss = get_real_win_rate()
        
        result = kelly_criterion(win_rate, avg_win, avg_loss)
        result["source"] = "real_trades"
        result["actual_win_rate"] = round(win_rate * 100, 1)
        
        return result
    except Exception:
        # Fallback to conservative defaults
        result = kelly_criterion(0.55, 5.0, 3.0)
        result["source"] = "default_estimate"
        result["actual_win_rate"] = None
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  POSITION SIZING
# ═══════════════════════════════════════════════════════════════════════════

def calculate_position_size(
    capital: float,
    risk_per_trade_pct: float = 1.0,
    entry_price: float = 0,
    stop_loss_price: float = 0,
    index_name: str = "NIFTY",
) -> Dict[str, Any]:
    """Calculate optimal position size based on risk management rules.
    
    capital: Total trading capital in ₹
    risk_per_trade_pct: Maximum % of capital to risk (default 1%)
    entry_price: Entry price of the option/stock
    stop_loss_price: Stop loss price
    index_name: NIFTY, SENSEX, BANKNIFTY
    """
    risk_per_trade_pct = min(risk_per_trade_pct, MAX_RISK_PER_TRADE_PCT)
    max_risk_amount = capital * (risk_per_trade_pct / 100)

    lot_size = {
        "NIFTY": NIFTY_LOT_SIZE,
        "SENSEX": SENSEX_LOT_SIZE,
        "BANKNIFTY": BANKNIFTY_LOT_SIZE,
        "FINNIFTY": FINNIFTY_LOT_SIZE,
    }.get(index_name.upper(), NIFTY_LOT_SIZE)

    risk_per_unit = abs(entry_price - stop_loss_price) if entry_price > 0 and stop_loss_price > 0 else entry_price * 0.02

    if risk_per_unit <= 0:
        risk_per_unit = 1

    # Max units based on risk
    max_units = int(max_risk_amount / risk_per_unit)
    max_lots = max(1, max_units // lot_size)

    # Also check capital constraint
    cost_per_lot = entry_price * lot_size if entry_price > 0 else 0
    affordable_lots = int(capital / cost_per_lot) if cost_per_lot > 0 else max_lots

    optimal_lots = min(max_lots, affordable_lots)
    optimal_qty = optimal_lots * lot_size

    total_cost = optimal_qty * entry_price if entry_price > 0 else 0
    total_risk = optimal_qty * risk_per_unit

    return {
        "optimal_lots": optimal_lots,
        "lot_size": lot_size,
        "optimal_qty": optimal_qty,
        "total_cost": round(total_cost, 2),
        "total_risk": round(total_risk, 2),
        "risk_pct": round((total_risk / capital) * 100, 2) if capital > 0 else 0,
        "max_risk_amount": round(max_risk_amount, 2),
        "risk_per_unit": round(risk_per_unit, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  INVESTMENT CALCULATOR (INR)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_investment_plan(
    investment_amount: float,
    index_price: float,
    option_premium: float,
    index_name: str = "NIFTY",
    option_type: str = "CE",
    confidence: float = 0.5,
) -> Dict[str, Any]:
    """Calculate detailed investment plan for a given amount in INR.
    
    Supports common amounts: ₹2K, ₹5K, ₹10K, ₹20K, ₹50K, ₹1L
    """
    lot_size = NIFTY_LOT_SIZE if "NIFTY" in index_name.upper() else SENSEX_LOT_SIZE

    cost_per_lot = option_premium * lot_size
    if cost_per_lot <= 0:
        cost_per_lot = 1

    affordable_lots = max(1, int(investment_amount / cost_per_lot))
    actual_cost = affordable_lots * cost_per_lot
    total_qty = affordable_lots * lot_size

    # Scenario analysis
    scenarios = {}
    for move_pct in [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]:
        # Simplified: option premium moves ~2x the index move for ATM
        option_delta = 0.5  # ATM delta
        premium_change = index_price * (move_pct / 100) * option_delta
        
        if option_type.upper() == "CE":
            profit = premium_change * total_qty
        else:  # PE
            profit = premium_change * total_qty

        profit_pct = (profit / actual_cost) * 100 if actual_cost > 0 else 0

        scenarios[f"+{move_pct}%"] = {
            "profit_inr": round(profit, 2),
            "profit_pct": round(profit_pct, 2),
            "new_premium": round(option_premium + premium_change / lot_size, 2),
        }

    # Risk-reward
    sl_pct = 30  # 30% of premium as stop loss
    stop_loss_premium = option_premium * (1 - sl_pct / 100)
    max_loss = (option_premium - stop_loss_premium) * total_qty
    target_premium = option_premium * 1.5  # 50% profit target
    expected_profit = (target_premium - option_premium) * total_qty

    return {
        "investment": investment_amount,
        "index_name": index_name,
        "option_type": option_type,
        "option_premium": option_premium,
        "lot_size": lot_size,
        "lots": affordable_lots,
        "total_qty": total_qty,
        "actual_cost": round(actual_cost, 2),
        "breakeven": round(index_price + option_premium if option_type == "CE" else index_price - option_premium, 2),
        "stop_loss_premium": round(stop_loss_premium, 2),
        "max_loss": round(max_loss, 2),
        "target_premium": round(target_premium, 2),
        "expected_profit": round(expected_profit, 2),
        "risk_reward_ratio": round(expected_profit / max_loss, 2) if max_loss > 0 else 0,
        "scenarios": scenarios,
        "confidence_adjusted_ev": round(expected_profit * confidence - max_loss * (1 - confidence), 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  TRAILING STOP LOSS ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class TrailingStopLoss:
    """Dynamic trailing stop-loss calculator."""

    def __init__(self, entry_price: float, initial_sl_pct: float = 2.0,
                 trail_pct: float = 1.0, atr: float = 0):
        self.entry_price = entry_price
        self.highest_price = entry_price
        self.initial_sl = entry_price * (1 - initial_sl_pct / 100)
        self.trail_pct = trail_pct
        self.atr = atr
        self.current_sl = self.initial_sl
        self.is_active = True

    def update(self, current_price: float) -> Dict[str, Any]:
        """Update trailing stop with new price."""
        if not self.is_active:
            return {"sl": self.current_sl, "triggered": True}

        if current_price > self.highest_price:
            self.highest_price = current_price
            # Trail stop up
            if self.atr > 0:
                new_sl = current_price - (2 * self.atr)
            else:
                new_sl = current_price * (1 - self.trail_pct / 100)
            self.current_sl = max(self.current_sl, new_sl)

        triggered = current_price <= self.current_sl

        if triggered:
            self.is_active = False

        profit_pct = ((current_price - self.entry_price) / self.entry_price) * 100

        return {
            "current_price": current_price,
            "stop_loss": round(self.current_sl, 2),
            "highest_price": round(self.highest_price, 2),
            "triggered": triggered,
            "profit_pct": round(profit_pct, 2),
            "distance_to_sl_pct": round(((current_price - self.current_sl) / current_price) * 100, 2),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  RISK-REWARD CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

def calculate_risk_reward(
    entry: float, stop_loss: float, target1: float,
    target2: float = 0, target3: float = 0,
) -> Dict[str, Any]:
    """Calculate risk-reward ratios and expected value."""
    risk = abs(entry - stop_loss)
    if risk == 0:
        return {"error": "Risk is zero"}

    targets = []
    for t, label in [(target1, "T1"), (target2, "T2"), (target3, "T3")]:
        if t > 0:
            reward = abs(t - entry)
            rr = reward / risk
            targets.append({
                "label": label,
                "price": round(t, 2),
                "reward": round(reward, 2),
                "rr_ratio": round(rr, 2),
                "required_winrate": round(1 / (1 + rr) * 100, 1),
            })

    return {
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "risk": round(risk, 2),
        "targets": targets,
        "recommended": "TAKE TRADE" if targets and targets[0]["rr_ratio"] >= 1.5 else "SKIP (RR < 1.5)",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DRAWDOWN TRACKER
# ═══════════════════════════════════════════════════════════════════════════

class DrawdownTracker:
    """Track portfolio drawdown and enforce limits."""

    def __init__(self, initial_capital: float, max_drawdown_pct: float = MAX_DRAWDOWN_PCT,
                 daily_limit_pct: float = DAILY_LOSS_LIMIT_PCT):
        self.initial_capital = initial_capital
        self.peak_capital = initial_capital
        self.current_capital = initial_capital
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_limit_pct = daily_limit_pct
        self.daily_start_capital = initial_capital
        self.trade_history: List[Dict] = []
        self.is_locked = False

    def record_trade(self, pnl: float) -> Dict[str, Any]:
        """Record a trade P&L and check limits."""
        self.current_capital += pnl
        self.peak_capital = max(self.peak_capital, self.current_capital)

        drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        daily_pnl = self.current_capital - self.daily_start_capital
        daily_pnl_pct = (daily_pnl / self.daily_start_capital) * 100

        self.trade_history.append({
            "pnl": round(pnl, 2),
            "capital": round(self.current_capital, 2),
            "drawdown_pct": round(drawdown, 2),
        })

        # Check limits
        if drawdown >= self.max_drawdown_pct:
            self.is_locked = True
            return {
                "status": "LOCKED",
                "reason": f"Max drawdown {self.max_drawdown_pct}% breached ({drawdown:.1f}%)",
                "drawdown_pct": round(drawdown, 2),
                "capital": round(self.current_capital, 2),
                "can_trade": False,
            }

        if daily_pnl_pct < -self.daily_limit_pct:
            return {
                "status": "DAILY_LIMIT",
                "reason": f"Daily loss limit {self.daily_limit_pct}% breached ({daily_pnl_pct:.1f}%)",
                "daily_pnl": round(daily_pnl, 2),
                "daily_pnl_pct": round(daily_pnl_pct, 2),
                "can_trade": False,
            }

        return {
            "status": "OK",
            "drawdown_pct": round(drawdown, 2),
            "daily_pnl": round(daily_pnl, 2),
            "capital": round(self.current_capital, 2),
            "total_pnl": round(self.current_capital - self.initial_capital, 2),
            "total_return_pct": round(((self.current_capital - self.initial_capital) / self.initial_capital) * 100, 2),
            "can_trade": True,
        }

    def reset_daily(self):
        """Reset daily counters (call at market open)."""
        self.daily_start_capital = self.current_capital

    def get_status(self) -> Dict[str, Any]:
        drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100 if self.peak_capital > 0 else 0
        return {
            "initial_capital": round(self.initial_capital, 2),
            "current_capital": round(self.current_capital, 2),
            "peak_capital": round(self.peak_capital, 2),
            "drawdown_pct": round(drawdown, 2),
            "total_pnl": round(self.current_capital - self.initial_capital, 2),
            "total_return_pct": round(((self.current_capital - self.initial_capital) / self.initial_capital) * 100, 2),
            "trades": len(self.trade_history),
            "is_locked": self.is_locked,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  FORMAT RISK REPORT
# ═══════════════════════════════════════════════════════════════════════════

def format_risk_report(
    capital: float,
    index_name: str,
    index_price: float,
    entry_price: float,
    stop_loss: float,
    target1: float,
    option_premium: float = 200,
    confidence: float = 0.5,
) -> str:
    """Generate a comprehensive risk report for Telegram."""
    pos = calculate_position_size(
        capital=capital, entry_price=entry_price,
        stop_loss_price=stop_loss, index_name=index_name,
    )
    rr = calculate_risk_reward(entry_price, stop_loss, target1)
    inv = calculate_investment_plan(
        investment_amount=capital, index_price=index_price,
        option_premium=option_premium, index_name=index_name,
        confidence=confidence,
    )
    kelly = kelly_criterion(win_rate=0.55, avg_win=target1 - entry_price, avg_loss=entry_price - stop_loss)

    lines = [
        f"⚖️ *RISK MANAGEMENT REPORT* ⚖️",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 Capital: ₹{capital:,.0f} | Index: {index_name}",
        f"📊 Index Price: ₹{index_price:,.2f}",
        f"",
        f"📐 *Position Sizing:*",
        f"  Optimal Lots: {pos['optimal_lots']} ({pos['optimal_qty']} units)",
        f"  Total Cost: ₹{pos['total_cost']:,.0f}",
        f"  Risk Amount: ₹{pos['total_risk']:,.0f} ({pos['risk_pct']}% of capital)",
        f"",
        f"🎯 *Risk-Reward:*",
    ]

    for t in rr.get("targets", []):
        lines.append(f"  {t['label']}: ₹{t['price']:,.0f} (RR: {t['rr_ratio']}:1, needs {t['required_winrate']}% WR)")

    lines.extend([
        f"  Verdict: *{rr.get('recommended', 'N/A')}*",
        f"",
        f"🧮 *Kelly Criterion:*",
        f"  Full Kelly: {kelly['kelly_pct']}% | Half Kelly: {kelly['half_kelly_pct']}%",
        f"  Expected Value: ₹{kelly['expected_value']:,.0f}",
        f"",
        f"💹 *Scenario Analysis:*",
    ])

    for scenario, data in inv.get("scenarios", {}).items():
        emoji = "🟢" if data["profit_inr"] > 0 else "🔴"
        lines.append(f"  {emoji} {scenario}: ₹{data['profit_inr']:+,.0f} ({data['profit_pct']:+.1f}%)")

    lines.extend([
        f"",
        f"⚠️ *Stop Loss: ₹{stop_loss:,.2f}*",
        f"💥 *Max Loss: ₹{inv.get('max_loss', 0):,.0f}*",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"⚠️ _Risk management is critical. Never risk more than 2% per trade._",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_risk_report(
        capital=50000,
        index_name="NIFTY",
        index_price=24500,
        entry_price=200,
        stop_loss=140,
        target1=300,
        option_premium=200,
        confidence=0.65,
    ))
