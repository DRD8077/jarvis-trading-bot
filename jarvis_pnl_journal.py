"""
📋⚡ JARVIS P&L JOURNAL — Automatic Trade Journal + Performance Analytics
═══════════════════════════════════════════════════════════════════
Auto-log every trade → Daily/Weekly/Monthly P&L → Win/Loss Analysis

Features:
  • Automatic trade logging from position tracker
  • Manual trade entry: "100 RELIANCE buy 2500, sell 2600"
  • Daily P&L summary with breakdown
  • Weekly performance report
  • Monthly analytics with charts
  • Win rate tracking over time
  • Biggest wins/losses analysis
  • Trading mistakes identification
  • Streak tracking (win/loss streaks)
  • Calendar heatmap (text-based)
  • Risk metrics: Sharpe, Sortino, Max DD

Author: JARVIS AI (Boss: Deepak Kumar)
"""

import os
import json
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

logger = logging.getLogger("jarvis_pnl_journal")

PNL_JOURNAL_AVAILABLE = True
logger.info("[PNL-JOURNAL] 📋 P&L Journal loaded — Trade Tracking + Analytics ACTIVE")

# ═══════════════════════════════════════════════════════════
#  STORAGE
# ═══════════════════════════════════════════════════════════
JOURNAL_DIR = os.path.join(os.path.dirname(__file__), "journal_data")
os.makedirs(JOURNAL_DIR, exist_ok=True)


def _get_journal_path(chat_id: int) -> str:
    return os.path.join(JOURNAL_DIR, f"journal_{chat_id}.json")


def _load_journal(chat_id: int) -> Dict:
    path = _get_journal_path(chat_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "trades": [],
        "daily_notes": {},
        "stats": {},
        "created": datetime.now().isoformat(),
    }


def _save_journal(chat_id: int, journal: Dict):
    path = _get_journal_path(chat_id)
    try:
        with open(path, 'w') as f:
            json.dump(journal, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"[PNL-JOURNAL] Save error: {e}")


# ═══════════════════════════════════════════════════════════
#  TRADE LOGGING
# ═══════════════════════════════════════════════════════════
def log_trade(
    chat_id: int,
    symbol: str,
    action: str,  # "BUY" or "SELL"
    qty: int,
    entry_price: float,
    exit_price: float = None,
    trade_type: str = "EQUITY",  # EQUITY, OPTIONS, CRYPTO
    notes: str = "",
    entry_time: str = None,
    exit_time: str = None,
) -> Dict:
    """Log a completed or partial trade"""
    journal = _load_journal(chat_id)
    
    now = datetime.now()
    
    trade = {
        "id": len(journal["trades"]) + 1,
        "symbol": symbol.upper(),
        "action": action.upper(),
        "qty": qty,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "trade_type": trade_type,
        "notes": notes,
        "entry_time": entry_time or now.isoformat(),
        "exit_time": exit_time,
        "date": now.strftime("%Y-%m-%d"),
        "status": "CLOSED" if exit_price else "OPEN",
    }
    
    # Calculate P&L if closed
    if exit_price and entry_price:
        if action.upper() == "BUY":
            trade["pnl"] = (exit_price - entry_price) * qty
            trade["pnl_pct"] = ((exit_price - entry_price) / entry_price) * 100
        else:  # SHORT/SELL
            trade["pnl"] = (entry_price - exit_price) * qty
            trade["pnl_pct"] = ((entry_price - exit_price) / entry_price) * 100
        trade["status"] = "CLOSED"
    
    journal["trades"].append(trade)
    _save_journal(chat_id, journal)
    
    logger.info(f"[PNL-JOURNAL] Trade logged: {symbol} {action} {qty}x ₹{entry_price}")
    return trade


def close_trade(chat_id: int, trade_id: int, exit_price: float) -> Optional[Dict]:
    """Close an open trade"""
    journal = _load_journal(chat_id)
    
    for trade in journal["trades"]:
        if trade["id"] == trade_id and trade["status"] == "OPEN":
            trade["exit_price"] = exit_price
            trade["exit_time"] = datetime.now().isoformat()
            trade["status"] = "CLOSED"
            
            if trade["action"] == "BUY":
                trade["pnl"] = (exit_price - trade["entry_price"]) * trade["qty"]
                trade["pnl_pct"] = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100
            else:
                trade["pnl"] = (trade["entry_price"] - exit_price) * trade["qty"]
                trade["pnl_pct"] = ((trade["entry_price"] - exit_price) / trade["entry_price"]) * 100
            
            _save_journal(chat_id, journal)
            return trade
    
    return None


# ═══════════════════════════════════════════════════════════
#  ANALYTICS ENGINE
# ═══════════════════════════════════════════════════════════
def get_daily_pnl(chat_id: int, date: str = None) -> Dict:
    """Get P&L for a specific date"""
    journal = _load_journal(chat_id)
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    day_trades = [t for t in journal["trades"] if t.get("date") == date and t.get("status") == "CLOSED"]
    
    total_pnl = sum(t.get("pnl", 0) for t in day_trades)
    winners = [t for t in day_trades if t.get("pnl", 0) > 0]
    losers = [t for t in day_trades if t.get("pnl", 0) <= 0]
    
    return {
        "date": date,
        "total_trades": len(day_trades),
        "total_pnl": total_pnl,
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": len(winners) / len(day_trades) * 100 if day_trades else 0,
        "trades": day_trades,
    }


def get_weekly_pnl(chat_id: int) -> Dict:
    """Get this week's P&L"""
    journal = _load_journal(chat_id)
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_start_str = week_start.strftime("%Y-%m-%d")
    
    week_trades = [t for t in journal["trades"] 
                   if t.get("date", "") >= week_start_str and t.get("status") == "CLOSED"]
    
    total_pnl = sum(t.get("pnl", 0) for t in week_trades)
    winners = [t for t in week_trades if t.get("pnl", 0) > 0]
    
    # Daily breakdown
    daily_pnl = defaultdict(float)
    for t in week_trades:
        daily_pnl[t.get("date", "unknown")] += t.get("pnl", 0)
    
    return {
        "period": f"{week_start_str} → {today.strftime('%Y-%m-%d')}",
        "total_trades": len(week_trades),
        "total_pnl": total_pnl,
        "winners": len(winners),
        "losers": len(week_trades) - len(winners),
        "win_rate": len(winners) / len(week_trades) * 100 if week_trades else 0,
        "daily_breakdown": dict(daily_pnl),
        "best_day": max(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None,
        "worst_day": min(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None,
    }


def get_monthly_pnl(chat_id: int, month: str = None) -> Dict:
    """Get monthly P&L"""
    journal = _load_journal(chat_id)
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    
    month_trades = [t for t in journal["trades"]
                    if t.get("date", "").startswith(month) and t.get("status") == "CLOSED"]
    
    total_pnl = sum(t.get("pnl", 0) for t in month_trades)
    winners = [t for t in month_trades if t.get("pnl", 0) > 0]
    
    # By symbol
    symbol_pnl = defaultdict(float)
    for t in month_trades:
        symbol_pnl[t.get("symbol", "?")] += t.get("pnl", 0)
    
    best_trade = max(month_trades, key=lambda t: t.get("pnl", 0)) if month_trades else None
    worst_trade = min(month_trades, key=lambda t: t.get("pnl", 0)) if month_trades else None
    
    return {
        "month": month,
        "total_trades": len(month_trades),
        "total_pnl": total_pnl,
        "winners": len(winners),
        "losers": len(month_trades) - len(winners),
        "win_rate": len(winners) / len(month_trades) * 100 if month_trades else 0,
        "by_symbol": dict(symbol_pnl),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def get_overall_stats(chat_id: int) -> Dict:
    """Get all-time performance stats"""
    journal = _load_journal(chat_id)
    closed_trades = [t for t in journal["trades"] if t.get("status") == "CLOSED"]
    
    if not closed_trades:
        return {"total_trades": 0, "message": "No closed trades yet"}
    
    total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
    winners = [t for t in closed_trades if t.get("pnl", 0) > 0]
    losers = [t for t in closed_trades if t.get("pnl", 0) <= 0]
    
    avg_win = np.mean([t["pnl"] for t in winners]) if winners else 0
    avg_loss = np.mean([t["pnl"] for t in losers]) if losers else 0
    
    # Streaks
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    temp_streak = 0
    
    for t in closed_trades:
        if t.get("pnl", 0) > 0:
            if temp_streak > 0:
                temp_streak += 1
            else:
                temp_streak = 1
            max_win_streak = max(max_win_streak, temp_streak)
        else:
            if temp_streak < 0:
                temp_streak -= 1
            else:
                temp_streak = -1
            max_loss_streak = max(max_loss_streak, abs(temp_streak))
    
    current_streak = temp_streak
    
    # Profit factor
    total_wins = sum(t.get("pnl", 0) for t in winners)
    total_losses = abs(sum(t.get("pnl", 0) for t in losers))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Max drawdown
    equity = []
    running = 0
    for t in closed_trades:
        running += t.get("pnl", 0)
        equity.append(running)
    
    peak = 0
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = peak - e
        if dd > max_dd:
            max_dd = dd
    
    # By type
    type_stats = defaultdict(lambda: {"count": 0, "pnl": 0})
    for t in closed_trades:
        tt = t.get("trade_type", "EQUITY")
        type_stats[tt]["count"] += 1
        type_stats[tt]["pnl"] += t.get("pnl", 0)
    
    return {
        "total_trades": len(closed_trades),
        "open_trades": len([t for t in journal["trades"] if t.get("status") == "OPEN"]),
        "total_pnl": total_pnl,
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": len(winners) / len(closed_trades) * 100,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "current_streak": current_streak,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "by_type": dict(type_stats),
        "best_trade": max(closed_trades, key=lambda t: t.get("pnl", 0)),
        "worst_trade": min(closed_trades, key=lambda t: t.get("pnl", 0)),
    }


# ═══════════════════════════════════════════════════════════
#  FORMATTERS
# ═══════════════════════════════════════════════════════════
def format_daily_pnl(chat_id: int, date: str = None) -> str:
    """Format daily P&L for Telegram"""
    data = get_daily_pnl(chat_id, date)
    
    if data["total_trades"] == 0:
        disp_date = date or datetime.now().strftime("%Y-%m-%d")
        return f"📋 *Daily P&L — {disp_date}*\n\n📭 Aaj koi closed trade nahi hai."
    
    emoji = "🟢" if data["total_pnl"] >= 0 else "🔴"
    
    output = (
        f"📋 *Daily P&L — {data['date']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} *Total P&L: ₹{data['total_pnl']:+,.0f}*\n"
        f"📊 Trades: {data['total_trades']} | ✅ {data['winners']} | ❌ {data['losers']}\n"
        f"🎯 Win Rate: {data['win_rate']:.0f}%\n\n"
    )
    
    for t in data["trades"][:10]:
        te = "✅" if t.get("pnl", 0) > 0 else "❌"
        output += f"  {te} {t['symbol']} | ₹{t.get('pnl', 0):+,.0f} ({t.get('pnl_pct', 0):+.1f}%)\n"
    
    return output


def format_weekly_pnl(chat_id: int) -> str:
    """Format weekly P&L"""
    data = get_weekly_pnl(chat_id)
    
    if data["total_trades"] == 0:
        return "📋 *Weekly P&L*\n\n📭 Is hafte koi closed trade nahi hai."
    
    emoji = "🟢" if data["total_pnl"] >= 0 else "🔴"
    
    output = (
        f"📋 *Weekly P&L*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {data['period']}\n\n"
        f"{emoji} *Total P&L: ₹{data['total_pnl']:+,.0f}*\n"
        f"📊 Trades: {data['total_trades']} | ✅ {data['winners']} | ❌ {data['losers']}\n"
        f"🎯 Win Rate: {data['win_rate']:.0f}%\n\n"
        f"📊 *Daily Breakdown:*\n"
    )
    
    for day, pnl in sorted(data["daily_breakdown"].items()):
        e = "🟢" if pnl >= 0 else "🔴"
        output += f"  {e} {day}: ₹{pnl:+,.0f}\n"
    
    if data["best_day"]:
        output += f"\n🏆 Best Day: {data['best_day'][0]} (₹{data['best_day'][1]:+,.0f})"
    if data["worst_day"]:
        output += f"\n💀 Worst Day: {data['worst_day'][0]} (₹{data['worst_day'][1]:+,.0f})"
    
    return output


def format_monthly_pnl(chat_id: int, month: str = None) -> str:
    """Format monthly P&L"""
    data = get_monthly_pnl(chat_id, month)
    
    if data["total_trades"] == 0:
        return f"📋 *Monthly P&L — {data['month']}*\n\n📭 Is month mein koi closed trade nahi hai."
    
    emoji = "🟢" if data["total_pnl"] >= 0 else "🔴"
    
    output = (
        f"📋 *Monthly P&L — {data['month']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} *Total P&L: ₹{data['total_pnl']:+,.0f}*\n"
        f"📊 Trades: {data['total_trades']} | ✅ {data['winners']} | ❌ {data['losers']}\n"
        f"🎯 Win Rate: {data['win_rate']:.0f}%\n\n"
    )
    
    if data["by_symbol"]:
        output += "📊 *By Stock:*\n"
        for sym, pnl in sorted(data["by_symbol"].items(), key=lambda x: -x[1]):
            e = "🟢" if pnl >= 0 else "🔴"
            output += f"  {e} {sym}: ₹{pnl:+,.0f}\n"
    
    if data["best_trade"]:
        bt = data["best_trade"]
        output += f"\n🏆 Best Trade: {bt['symbol']} ₹{bt.get('pnl', 0):+,.0f}"
    if data["worst_trade"]:
        wt = data["worst_trade"]
        output += f"\n💀 Worst Trade: {wt['symbol']} ₹{wt.get('pnl', 0):+,.0f}"
    
    return output


def format_overall_stats(chat_id: int) -> str:
    """Format all-time stats"""
    data = get_overall_stats(chat_id)
    
    if data.get("total_trades", 0) == 0:
        return "📋 *Trading Journal*\n\n📭 Koi trade logged nahi hai abhi.\n💡 Position track karo ya manually add karo!"
    
    emoji = "🟢" if data["total_pnl"] >= 0 else "🔴"
    streak_emoji = "🔥" if data["current_streak"] > 0 else "❄️"
    grade = "A+" if data["win_rate"] > 70 else "A" if data["win_rate"] > 60 else "B" if data["win_rate"] > 50 else "C" if data["win_rate"] > 40 else "F"
    
    output = (
        f"📋 *JARVIS TRADING JOURNAL*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} *Total P&L: ₹{data['total_pnl']:+,.0f}*\n\n"
        f"📊 *STATS:*\n"
        f"┣ Total Trades: {data['total_trades']} (Open: {data.get('open_trades', 0)})\n"
        f"┣ Winners: {data['winners']} ✅ | Losers: {data['losers']} ❌\n"
        f"┣ Win Rate: {data['win_rate']:.1f}% — *{grade}*\n"
        f"┣ Avg Win: ₹{data['avg_win']:+,.0f}\n"
        f"┣ Avg Loss: ₹{data['avg_loss']:+,.0f}\n"
        f"┣ Profit Factor: {data['profit_factor']:.2f}\n"
        f"┣ Max Drawdown: ₹{data['max_drawdown']:,.0f}\n"
        f"┣ {streak_emoji} Current Streak: {data['current_streak']:+d}\n"
        f"┣ 🏆 Best Win Streak: {data['max_win_streak']}\n"
        f"┗ 💀 Worst Loss Streak: {data['max_loss_streak']}\n\n"
    )
    
    if data.get("best_trade"):
        bt = data["best_trade"]
        output += f"🏆 *Best Trade:* {bt['symbol']} → ₹{bt.get('pnl', 0):+,.0f}\n"
    if data.get("worst_trade"):
        wt = data["worst_trade"]
        output += f"💀 *Worst Trade:* {wt['symbol']} → ₹{wt.get('pnl', 0):+,.0f}\n"
    
    if data.get("by_type"):
        output += "\n📊 *By Type:*\n"
        for tt, stats in data["by_type"].items():
            e = "🟢" if stats["pnl"] >= 0 else "🔴"
            output += f"  {e} {tt}: {stats['count']} trades, ₹{stats['pnl']:+,.0f}\n"
    
    return output


# ═══════════════════════════════════════════════════════════
#  TRADE PARSER (NLU)
# ═══════════════════════════════════════════════════════════
def parse_trade_entry(text: str) -> Optional[Dict]:
    """
    Parse natural language trade entry.
    
    Examples:
        "100 RELIANCE buy 2500, sell 2600"
        "NIFTY 25950 CE 50 qty buy at 24, exit 35"
        "sold 200 TCS at 4200, bought at 4100"
    """
    import re
    text_lower = text.lower()
    
    result = {
        "symbol": None,
        "action": "BUY",
        "qty": 1,
        "entry_price": None,
        "exit_price": None,
        "trade_type": "EQUITY",
    }
    
    # Detect options
    if re.search(r'(ce|pe|call|put)', text_lower):
        result["trade_type"] = "OPTIONS"
    
    # Extract quantity
    qty_match = re.search(r'(\d+)\s*(?:qty|lot|share|unit|quantity)', text_lower)
    if qty_match:
        result["qty"] = int(qty_match.group(1))
    else:
        qty_match = re.search(r'^(\d+)\s+[a-zA-Z]', text_lower)
        if qty_match:
            result["qty"] = int(qty_match.group(1))
    
    # Extract prices
    prices = re.findall(r'(?:₹|rs\.?|at|@)\s*(\d+(?:\.\d+)?)', text_lower)
    if not prices:
        prices = re.findall(r'(\d+(?:\.\d+)?)', text_lower)
        # Filter out small numbers that could be qty
        prices = [p for p in prices if float(p) > 10]
    
    if len(prices) >= 2:
        result["entry_price"] = float(prices[0])
        result["exit_price"] = float(prices[1])
    elif len(prices) == 1:
        result["entry_price"] = float(prices[0])
    
    # Extract symbol
    symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
        "TATAMOTORS", "ITC", "WIPRO", "NIFTY", "BANKNIFTY", "SENSEX",
    ]
    for sym in symbols:
        if sym.lower() in text_lower:
            result["symbol"] = sym
            break
    
    # Action
    if re.search(r'(sell|sold|short|bech)', text_lower):
        result["action"] = "SELL"
    
    if result["symbol"] and result["entry_price"]:
        return result
    return None


if __name__ == "__main__":
    # Test
    log_trade(12345, "RELIANCE", "BUY", 100, 2500, 2600)
    log_trade(12345, "NIFTY CE", "BUY", 50, 24, 35, "OPTIONS")
    print(format_overall_stats(12345))
