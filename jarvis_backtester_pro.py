"""
🔬⚡ JARVIS BACKTESTER PRO — Natural Language Strategy Backtesting
═══════════════════════════════════════════════════════════════════
"RSI < 30 pe buy, RSI > 70 pe sell, RELIANCE pe backtest karo" → Full Report

Features:
  • Natural language strategy builder
  • Multiple entry/exit conditions (RSI, SMA, EMA, MACD, BB, VWAP)
  • Full P&L calculation with commissions
  • Win rate, max drawdown, Sharpe ratio
  • Trade-by-trade log
  • Equity curve (text-based)
  • Risk-adjusted returns
  • Multi-stock backtesting
  • Customizable timeperiod

Author: JARVIS AI (Boss: Deepak Kumar)
"""

import os
import re
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger("jarvis_backtester")

try:
    import yfinance as yf
    BACKTESTER_AVAILABLE = True
    logger.info("[BACKTESTER] 🔬 Backtester Pro loaded — Strategy Testing Engine ACTIVE")
except ImportError:
    BACKTESTER_AVAILABLE = False

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
DEFAULT_CAPITAL = 100000  # ₹1 Lakh
COMMISSION_PCT = 0.05  # 0.05% per trade (broker commission)
SLIPPAGE_PCT = 0.02  # 0.02% slippage


# ═══════════════════════════════════════════════════════════
#  INDICATORS
# ═══════════════════════════════════════════════════════════
def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _calc_sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(window=period).mean()

def _calc_ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()

def _calc_macd(close: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal, macd - signal

def _calc_bb(close: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    return sma + 2*std, sma, sma - 2*std

def _calc_vwap(data: pd.DataFrame) -> pd.Series:
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    cum_vol = data['Volume'].cumsum()
    return (tp * data['Volume']).cumsum() / cum_vol.replace(0, np.nan)


def _add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators to dataframe"""
    df = data.copy()
    close = df['Close']
    
    df['RSI'] = _calc_rsi(close)
    df['SMA9'] = _calc_sma(close, 9)
    df['SMA20'] = _calc_sma(close, 20)
    df['SMA50'] = _calc_sma(close, 50)
    df['SMA200'] = _calc_sma(close, 200)
    df['EMA9'] = _calc_ema(close, 9)
    df['EMA21'] = _calc_ema(close, 21)
    df['EMA50'] = _calc_ema(close, 50)
    df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = _calc_macd(close)
    df['BB_UPPER'], df['BB_MID'], df['BB_LOWER'] = _calc_bb(close)
    df['VWAP'] = _calc_vwap(data)
    
    # Price change
    df['CHANGE_PCT'] = close.pct_change() * 100
    
    return df


# ═══════════════════════════════════════════════════════════
#  STRATEGY PARSER (NLU)
# ═══════════════════════════════════════════════════════════
def parse_strategy(text: str) -> Dict[str, Any]:
    """
    Parse natural language strategy.
    
    Examples:
        "RSI < 30 pe buy, RSI > 70 pe sell" → conditions
        "EMA 9 cross above EMA 21 buy, below sell"
        "MACD bullish crossover buy, bearish sell"
        "price below bollinger lower buy, above upper sell"
    """
    text_lower = text.lower()
    
    strategy = {
        "buy_conditions": [],
        "sell_conditions": [],
        "symbol": "NIFTY",
        "period": "1y",
        "capital": DEFAULT_CAPITAL,
    }
    
    # Extract symbol
    symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
        "TATAMOTORS", "ITC", "WIPRO", "BAJFINANCE", "NIFTY", "BANKNIFTY",
        "SENSEX", "MARUTI", "LT", "TITAN", "ADANIENT", "SUNPHARMA",
        "HCLTECH", "TECHM", "TATASTEEL", "BHARTIARTL", "ONGC",
    ]
    for sym in symbols:
        if sym.lower() in text_lower:
            strategy["symbol"] = sym
            break
    
    # Extract period
    period_map = {
        r'(\d+)\s*year': lambda m: f"{m.group(1)}y",
        r'(\d+)\s*month': lambda m: f"{m.group(1)}mo",
        r'(\d+)\s*saal': lambda m: f"{m.group(1)}y",
        r'(\d+)\s*mahine': lambda m: f"{m.group(1)}mo",
        r'last\s*(\d+)y': lambda m: f"{m.group(1)}y",
    }
    for pattern, func in period_map.items():
        m = re.search(pattern, text_lower)
        if m:
            strategy["period"] = func(m)
            break
    
    # ── RSI conditions ──
    rsi_buy = re.search(r'rsi\s*[<<=]\s*(\d+).*(?:buy|khareed|entry|le)', text_lower)
    rsi_sell = re.search(r'rsi\s*[>>=]\s*(\d+).*(?:sell|bech|exit|nikl)', text_lower)
    
    if not rsi_buy:
        rsi_buy = re.search(r'(?:buy|khareed|entry|le).*rsi\s*[<<=]\s*(\d+)', text_lower)
    if not rsi_sell:
        rsi_sell = re.search(r'(?:sell|bech|exit|nikl).*rsi\s*[>>=]\s*(\d+)', text_lower)
    
    if rsi_buy:
        strategy["buy_conditions"].append(("RSI", "<", float(rsi_buy.group(1))))
    if rsi_sell:
        strategy["sell_conditions"].append(("RSI", ">", float(rsi_sell.group(1))))
    
    # ── SMA/EMA crossover conditions ──
    if re.search(r'(ema|sma)\s*(\d+)\s*(cross|above|upar).*?(ema|sma)\s*(\d+)', text_lower):
        m = re.search(r'(ema|sma)\s*(\d+)\s*(cross|above|upar).*?(ema|sma)\s*(\d+)', text_lower)
        fast_type = m.group(1).upper()
        fast_period = int(m.group(2))
        slow_type = m.group(4).upper()
        slow_period = int(m.group(5))
        strategy["buy_conditions"].append(("CROSS_ABOVE", f"{fast_type}{fast_period}", f"{slow_type}{slow_period}"))
        strategy["sell_conditions"].append(("CROSS_BELOW", f"{fast_type}{fast_period}", f"{slow_type}{slow_period}"))
    
    # ── MACD conditions ──
    if re.search(r'macd.*(bull|buy|positive|cross.*above)', text_lower):
        strategy["buy_conditions"].append(("MACD", ">", "SIGNAL"))
    if re.search(r'macd.*(bear|sell|negative|cross.*below)', text_lower):
        strategy["sell_conditions"].append(("MACD", "<", "SIGNAL"))
    
    # ── Bollinger conditions ──
    if re.search(r'(bollinger|bb).*(lower|neeche).*buy', text_lower) or re.search(r'buy.*(bollinger|bb).*(lower|neeche)', text_lower):
        strategy["buy_conditions"].append(("PRICE", "<", "BB_LOWER"))
    if re.search(r'(bollinger|bb).*(upper|upar).*sell', text_lower) or re.search(r'sell.*(bollinger|bb).*(upper|upar)', text_lower):
        strategy["sell_conditions"].append(("PRICE", ">", "BB_UPPER"))
    
    # ── Default: RSI strategy if nothing parsed ──
    if not strategy["buy_conditions"] and not strategy["sell_conditions"]:
        strategy["buy_conditions"] = [("RSI", "<", 30)]
        strategy["sell_conditions"] = [("RSI", ">", 70)]
    
    # Ensure we have both buy and sell
    if not strategy["sell_conditions"]:
        strategy["sell_conditions"] = [("RSI", ">", 70)]
    if not strategy["buy_conditions"]:
        strategy["buy_conditions"] = [("RSI", "<", 30)]
    
    return strategy


# ═══════════════════════════════════════════════════════════
#  CONDITION EVALUATOR
# ═══════════════════════════════════════════════════════════
def _eval_condition(row: pd.Series, prev_row: pd.Series, condition: Tuple) -> bool:
    """Evaluate a single condition"""
    try:
        cond_type = condition[0]
        
        if cond_type == "RSI":
            op, val = condition[1], condition[2]
            rsi = row.get("RSI", 50)
            if pd.isna(rsi):
                return False
            if op == "<":
                return rsi < val
            elif op == ">":
                return rsi > val
        
        elif cond_type == "MACD":
            op = condition[1]
            macd = row.get("MACD", 0)
            signal = row.get("MACD_SIGNAL", 0)
            if pd.isna(macd) or pd.isna(signal):
                return False
            if op == ">":
                return macd > signal
            elif op == "<":
                return macd < signal
        
        elif cond_type == "PRICE":
            op, target = condition[1], condition[2]
            price = row.get("Close", 0)
            target_val = row.get(target, price)
            if pd.isna(target_val):
                return False
            if op == "<":
                return price < target_val
            elif op == ">":
                return price > target_val
        
        elif cond_type == "CROSS_ABOVE":
            fast_key = condition[1]
            slow_key = condition[2]
            fast = row.get(fast_key, 0)
            slow = row.get(slow_key, 0)
            prev_fast = prev_row.get(fast_key, 0) if prev_row is not None else 0
            prev_slow = prev_row.get(slow_key, 0) if prev_row is not None else 0
            if any(pd.isna(v) for v in [fast, slow, prev_fast, prev_slow]):
                return False
            return fast > slow and prev_fast <= prev_slow
        
        elif cond_type == "CROSS_BELOW":
            fast_key = condition[1]
            slow_key = condition[2]
            fast = row.get(fast_key, 0)
            slow = row.get(slow_key, 0)
            prev_fast = prev_row.get(fast_key, 0) if prev_row is not None else 0
            prev_slow = prev_row.get(slow_key, 0) if prev_row is not None else 0
            if any(pd.isna(v) for v in [fast, slow, prev_fast, prev_slow]):
                return False
            return fast < slow and prev_fast >= prev_slow
    
    except Exception:
        return False
    
    return False


def _eval_conditions(row: pd.Series, prev_row: pd.Series, conditions: List[Tuple]) -> bool:
    """All conditions must be true (AND logic)"""
    return all(_eval_condition(row, prev_row, c) for c in conditions)


# ═══════════════════════════════════════════════════════════
#  BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════
def run_backtest(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run backtest and return full results.
    """
    symbol = strategy["symbol"]
    period = strategy["period"]
    capital = strategy.get("capital", DEFAULT_CAPITAL)
    
    # Map symbol to yfinance
    sym_map = {
        "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN",
    }
    yf_symbol = sym_map.get(symbol, f"{symbol}.NS")
    
    # Fetch data
    try:
        data = yf.download(yf_symbol, period=period, interval="1d", progress=False)
        if data is None or data.empty:
            return {"error": f"No data for {symbol}"}
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
    except Exception as e:
        return {"error": f"Data fetch failed: {e}"}
    
    # Add indicators
    df = _add_indicators(data)
    df = df.dropna(subset=['RSI']).copy()
    
    if len(df) < 30:
        return {"error": "Not enough data for backtesting"}
    
    # Run simulation
    trades = []
    position = None  # None or {"entry_price", "entry_date", "qty"}
    current_capital = capital
    peak_capital = capital
    max_drawdown = 0
    
    buy_conditions = strategy["buy_conditions"]
    sell_conditions = strategy["sell_conditions"]
    
    prev_row = None
    
    for idx, row in df.iterrows():
        if prev_row is None:
            prev_row = row
            continue
        
        close = float(row['Close'])
        
        if position is None:
            # Check buy conditions
            if _eval_conditions(row, prev_row, buy_conditions):
                qty = int(current_capital * 0.95 / close)  # Use 95% capital
                if qty > 0:
                    cost = qty * close * (1 + COMMISSION_PCT/100 + SLIPPAGE_PCT/100)
                    position = {
                        "entry_price": close,
                        "entry_date": idx,
                        "qty": qty,
                        "cost": cost,
                    }
                    current_capital -= cost
        else:
            # Check sell conditions
            if _eval_conditions(row, prev_row, sell_conditions):
                revenue = position["qty"] * close * (1 - COMMISSION_PCT/100 - SLIPPAGE_PCT/100)
                pnl = revenue - position["cost"]
                pnl_pct = (pnl / position["cost"]) * 100
                
                trades.append({
                    "entry_date": position["entry_date"],
                    "entry_price": position["entry_price"],
                    "exit_date": idx,
                    "exit_price": close,
                    "qty": position["qty"],
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "holding_days": (idx - position["entry_date"]).days,
                })
                
                current_capital += revenue
                position = None
                
                # Track drawdown
                if current_capital > peak_capital:
                    peak_capital = current_capital
                dd = (peak_capital - current_capital) / peak_capital * 100
                if dd > max_drawdown:
                    max_drawdown = dd
        
        prev_row = row
    
    # Close open position at last price
    if position:
        last_close = float(df['Close'].iloc[-1])
        revenue = position["qty"] * last_close * (1 - COMMISSION_PCT/100)
        pnl = revenue - position["cost"]
        trades.append({
            "entry_date": position["entry_date"],
            "entry_price": position["entry_price"],
            "exit_date": df.index[-1],
            "exit_price": last_close,
            "qty": position["qty"],
            "pnl": pnl,
            "pnl_pct": (pnl / position["cost"]) * 100,
            "holding_days": (df.index[-1] - position["entry_date"]).days,
            "open": True,
        })
        current_capital += revenue
    
    # Calculate stats
    total_pnl = current_capital - capital
    total_return = (total_pnl / capital) * 100
    
    winning = [t for t in trades if t["pnl"] > 0]
    losing = [t for t in trades if t["pnl"] <= 0]
    win_rate = len(winning) / len(trades) * 100 if trades else 0
    
    avg_win = np.mean([t["pnl"] for t in winning]) if winning else 0
    avg_loss = np.mean([t["pnl"] for t in losing]) if losing else 0
    
    profit_factor = abs(sum(t["pnl"] for t in winning) / sum(t["pnl"] for t in losing)) if losing and sum(t["pnl"] for t in losing) != 0 else float('inf')
    
    avg_holding = np.mean([t["holding_days"] for t in trades]) if trades else 0
    
    # Sharpe ratio (simplified)
    if trades:
        returns = [t["pnl_pct"] for t in trades]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 / max(avg_holding, 1)) if np.std(returns) > 0 else 0
    else:
        sharpe = 0
    
    # Data period
    start_date = df.index[0].strftime("%Y-%m-%d") if hasattr(df.index[0], 'strftime') else str(df.index[0])
    end_date = df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
    
    return {
        "symbol": symbol,
        "period": f"{start_date} → {end_date}",
        "total_days": len(df),
        "capital": capital,
        "final_capital": current_capital,
        "total_pnl": total_pnl,
        "total_return": total_return,
        "trades": trades,
        "total_trades": len(trades),
        "wins": len(winning),
        "losses": len(losing),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe,
        "avg_holding_days": avg_holding,
        "strategy": strategy,
    }


# ═══════════════════════════════════════════════════════════
#  FORMATTER
# ═══════════════════════════════════════════════════════════
def format_backtest_result(result: Dict[str, Any]) -> str:
    """Format backtest results for Telegram"""
    if "error" in result:
        return f"❌ Backtest Error: {result['error']}"
    
    pnl_emoji = "🟢" if result["total_pnl"] >= 0 else "🔴"
    grade = "A+" if result["win_rate"] > 70 else "A" if result["win_rate"] > 60 else "B" if result["win_rate"] > 50 else "C" if result["win_rate"] > 40 else "F"
    
    # Strategy description
    strategy = result["strategy"]
    buy_desc = []
    for c in strategy["buy_conditions"]:
        if c[0] == "RSI":
            buy_desc.append(f"RSI {c[1]} {c[2]}")
        elif c[0] == "MACD":
            buy_desc.append(f"MACD {c[1]} Signal")
        elif c[0] == "PRICE":
            buy_desc.append(f"Price {c[1]} {c[2]}")
        elif c[0] in ("CROSS_ABOVE", "CROSS_BELOW"):
            buy_desc.append(f"{c[1]} cross {c[0].split('_')[1].lower()} {c[2]}")
    
    sell_desc = []
    for c in strategy["sell_conditions"]:
        if c[0] == "RSI":
            sell_desc.append(f"RSI {c[1]} {c[2]}")
        elif c[0] == "MACD":
            sell_desc.append(f"MACD {c[1]} Signal")
        elif c[0] == "PRICE":
            sell_desc.append(f"Price {c[1]} {c[2]}")
        elif c[0] in ("CROSS_ABOVE", "CROSS_BELOW"):
            sell_desc.append(f"{c[1]} cross {c[0].split('_')[1].lower()} {c[2]}")
    
    output = (
        f"🔬 *JARVIS BACKTESTER PRO*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Stock:* {result['symbol']}\n"
        f"📅 *Period:* {result['period']}\n"
        f"💰 *Capital:* ₹{result['capital']:,.0f}\n\n"
        f"🎯 *STRATEGY:*\n"
        f"  🟢 BUY: {' & '.join(buy_desc)}\n"
        f"  🔴 SELL: {' & '.join(sell_desc)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 *RESULTS:*\n\n"
        f"💰 Final Capital: ₹{result['final_capital']:,.0f}\n"
        f"{pnl_emoji} *Total P&L: ₹{result['total_pnl']:,.0f} ({result['total_return']:+.2f}%)*\n\n"
        f"📊 *TRADE STATS:*\n"
        f"┣ Total Trades: {result['total_trades']}\n"
        f"┣ Winners: {result['wins']} ✅ | Losers: {result['losses']} ❌\n"
        f"┣ Win Rate: {result['win_rate']:.1f}% — Grade: *{grade}*\n"
        f"┣ Avg Win: ₹{result['avg_win']:,.0f}\n"
        f"┣ Avg Loss: ₹{result['avg_loss']:,.0f}\n"
        f"┣ Profit Factor: {result['profit_factor']:.2f}\n"
        f"┣ Max Drawdown: {result['max_drawdown']:.1f}%\n"
        f"┣ Sharpe Ratio: {result['sharpe_ratio']:.2f}\n"
        f"┗ Avg Holding: {result['avg_holding_days']:.0f} days\n\n"
    )
    
    # Last 5 trades
    trades = result.get("trades", [])
    if trades:
        output += "📋 *RECENT TRADES:*\n"
        for t in trades[-5:]:
            emoji = "✅" if t["pnl"] > 0 else "❌"
            entry_d = t["entry_date"].strftime("%d/%m") if hasattr(t["entry_date"], 'strftime') else str(t["entry_date"])[:5]
            exit_d = t["exit_date"].strftime("%d/%m") if hasattr(t["exit_date"], 'strftime') else str(t["exit_date"])[:5]
            open_tag = " ⏳" if t.get("open") else ""
            output += (
                f"  {emoji} {entry_d}→{exit_d} | ₹{t['entry_price']:.0f}→₹{t['exit_price']:.0f} | "
                f"₹{t['pnl']:+,.0f} ({t['pnl_pct']:+.1f}%){open_tag}\n"
            )
    
    # Verdict
    output += f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if result["total_return"] > 15 and result["win_rate"] > 55:
        output += "🟢 *VERDICT: EXCELLENT STRATEGY — Use with real money (with SL)* ✅"
    elif result["total_return"] > 5 and result["win_rate"] > 45:
        output += "🟡 *VERDICT: DECENT STRATEGY — Needs optimization* ⚠️"
    elif result["total_return"] > 0:
        output += "🟠 *VERDICT: MARGINAL — Beat FD but risky* ⚠️"
    else:
        output += "🔴 *VERDICT: LOSING STRATEGY — DO NOT USE* ❌"
    
    return output


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
def handle_backtest_command(text: str) -> str:
    """Main entry point"""
    if not BACKTESTER_AVAILABLE:
        return "❌ Backtester unavailable — yfinance not installed"
    
    strategy = parse_strategy(text)
    result = run_backtest(strategy)
    return format_backtest_result(result)


# Pre-built strategies
def backtest_rsi_strategy(symbol: str = "NIFTY", period: str = "1y") -> str:
    strategy = {
        "buy_conditions": [("RSI", "<", 30)],
        "sell_conditions": [("RSI", ">", 70)],
        "symbol": symbol,
        "period": period,
        "capital": DEFAULT_CAPITAL,
    }
    return format_backtest_result(run_backtest(strategy))


def backtest_macd_strategy(symbol: str = "NIFTY", period: str = "1y") -> str:
    strategy = {
        "buy_conditions": [("MACD", ">", "SIGNAL")],
        "sell_conditions": [("MACD", "<", "SIGNAL")],
        "symbol": symbol,
        "period": period,
        "capital": DEFAULT_CAPITAL,
    }
    return format_backtest_result(run_backtest(strategy))


def backtest_bollinger_strategy(symbol: str = "NIFTY", period: str = "1y") -> str:
    strategy = {
        "buy_conditions": [("PRICE", "<", "BB_LOWER")],
        "sell_conditions": [("PRICE", ">", "BB_UPPER")],
        "symbol": symbol,
        "period": period,
        "capital": DEFAULT_CAPITAL,
    }
    return format_backtest_result(run_backtest(strategy))


if __name__ == "__main__":
    print(handle_backtest_command("RSI 30 pe buy, RSI 70 pe sell karo RELIANCE pe last 1 year"))
