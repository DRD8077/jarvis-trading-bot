"""
========================================================================================
  PORTFOLIO TRACKER — Crypto + Stock Portfolio with Tax & Analytics (₹ INR)
========================================================================================

Features:
  1. Add/remove crypto holdings (symbol, qty, buy price)
  2. Add/remove STOCK holdings (NSE/BSE — e.g., RELIANCE, TATA MOTORS)
  3. Live P&L calculation with real-time price feeds
  4. Portfolio summary with total invested, current value, ROI
  5. Per-token/stock profit/loss breakdown
  6. Trade history with timestamps
  7. Indian Tax Calculator (30% crypto tax + 1% TDS + STCG/LTCG for stocks)
  8. Portfolio Analytics (Sharpe ratio, drawdown, sector allocation)
  9. All amounts in ₹ INR
  10. SQLite persistence per user (chat_id)
"""

import sqlite3
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("portfolio_tracker")

DB_PATH = "data.db"


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE SCHEMA — Crypto Portfolio Tables
# ═══════════════════════════════════════════════════════════════════════════

def init_portfolio_db(db_path: str = DB_PATH):
    """Create portfolio tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Active holdings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT DEFAULT '',
            chain TEXT DEFAULT 'solana',
            mint TEXT DEFAULT '',
            qty REAL NOT NULL,
            buy_price_inr REAL NOT NULL,
            buy_price_usd REAL DEFAULT 0,
            invested_inr REAL NOT NULL,
            source TEXT DEFAULT 'manual',
            added_ts INTEGER NOT NULL,
            status TEXT DEFAULT 'OPEN',
            sell_price_inr REAL DEFAULT 0,
            realized_pnl_inr REAL DEFAULT 0,
            closed_ts INTEGER DEFAULT 0
        )
    """)

    # Trade history log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            qty REAL NOT NULL,
            price_inr REAL NOT NULL,
            total_inr REAL NOT NULL,
            ts INTEGER NOT NULL,
            notes TEXT DEFAULT ''
        )
    """)

    # Price alerts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            chain TEXT DEFAULT 'solana',
            mint TEXT DEFAULT '',
            target_price_inr REAL NOT NULL,
            direction TEXT NOT NULL,
            created_ts INTEGER NOT NULL,
            triggered INTEGER DEFAULT 0,
            triggered_ts INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Portfolio DB tables initialized")


# ═══════════════════════════════════════════════════════════════════════════
#  ADD / REMOVE HOLDINGS
# ═══════════════════════════════════════════════════════════════════════════

def add_holding(chat_id: int, symbol: str, qty: float, buy_price_inr: float,
                name: str = "", chain: str = "solana", mint: str = "",
                buy_price_usd: float = 0, source: str = "manual",
                db_path: str = DB_PATH) -> int:
    """Add a crypto holding to the portfolio."""
    init_portfolio_db(db_path)
    invested = qty * buy_price_inr
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO crypto_portfolio 
            (chat_id, symbol, name, chain, mint, qty, buy_price_inr, buy_price_usd,
             invested_inr, source, added_ts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
        """, (chat_id, symbol.upper(), name, chain, mint, qty, buy_price_inr,
              buy_price_usd, invested, source, int(time.time())))
        conn.commit()

        # Log the trade
        cur.execute("""
            INSERT INTO crypto_trades (chat_id, symbol, action, qty, price_inr, total_inr, ts, notes)
            VALUES (?, ?, 'BUY', ?, ?, ?, ?, ?)
        """, (chat_id, symbol.upper(), qty, buy_price_inr, invested,
              int(time.time()), f"Added via {source}"))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def sell_holding(chat_id: int, symbol: str, sell_price_inr: float,
                 qty: Optional[float] = None, db_path: str = DB_PATH) -> Dict:
    """Sell a holding (full or partial). Returns P&L info."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, qty, buy_price_inr, invested_inr FROM crypto_portfolio
            WHERE chat_id = ? AND symbol = ? AND status = 'OPEN'
            ORDER BY added_ts ASC
        """, (chat_id, symbol.upper()))
        rows = cur.fetchall()

        if not rows:
            return {"success": False, "error": f"No open position for {symbol}"}

        total_sold = 0
        total_pnl = 0
        total_invested = 0

        for row_id, row_qty, row_buy_price, row_invested in rows:
            if qty is not None and total_sold >= qty:
                break

            sell_qty = row_qty if qty is None else min(row_qty - 0, qty - total_sold)
            if sell_qty <= 0:
                continue

            pnl = (sell_price_inr - row_buy_price) * sell_qty
            total_pnl += pnl
            total_sold += sell_qty
            total_invested += row_buy_price * sell_qty

            if sell_qty >= row_qty:
                # Close entire position
                cur.execute("""
                    UPDATE crypto_portfolio SET status = 'CLOSED', sell_price_inr = ?,
                    realized_pnl_inr = ?, closed_ts = ? WHERE id = ?
                """, (sell_price_inr, pnl, int(time.time()), row_id))
            else:
                # Partial sell — reduce qty
                new_qty = row_qty - sell_qty
                new_invested = new_qty * row_buy_price
                cur.execute("""
                    UPDATE crypto_portfolio SET qty = ?, invested_inr = ? WHERE id = ?
                """, (new_qty, new_invested, row_id))

        # Log the trade
        sale_total = total_sold * sell_price_inr
        cur.execute("""
            INSERT INTO crypto_trades (chat_id, symbol, action, qty, price_inr, total_inr, ts, notes)
            VALUES (?, ?, 'SELL', ?, ?, ?, ?, ?)
        """, (chat_id, symbol.upper(), total_sold, sell_price_inr, sale_total,
              int(time.time()), f"P&L: ₹{total_pnl:,.2f}"))
        conn.commit()

        roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        return {
            "success": True,
            "symbol": symbol.upper(),
            "qty_sold": total_sold,
            "sell_price_inr": sell_price_inr,
            "total_received_inr": sale_total,
            "total_invested_inr": total_invested,
            "pnl_inr": total_pnl,
            "roi_pct": roi,
        }
    finally:
        conn.close()


def remove_holding(chat_id: int, symbol: str, db_path: str = DB_PATH) -> bool:
    """Remove a holding entirely (cancel/delete, no P&L recorded)."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM crypto_portfolio WHERE chat_id = ? AND symbol = ? AND status = 'OPEN'
        """, (chat_id, symbol.upper()))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO QUERIES
# ═══════════════════════════════════════════════════════════════════════════

def get_portfolio(chat_id: int, db_path: str = DB_PATH) -> List[Dict]:
    """Get all open holdings for a user."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, symbol, name, chain, mint, qty, buy_price_inr, invested_inr,
                   source, added_ts
            FROM crypto_portfolio WHERE chat_id = ? AND status = 'OPEN'
            ORDER BY invested_inr DESC
        """, (chat_id,))
        rows = cur.fetchall()
        return [{
            "id": r[0], "symbol": r[1], "name": r[2], "chain": r[3], "mint": r[4],
            "qty": r[5], "buy_price_inr": r[6], "invested_inr": r[7],
            "source": r[8], "added_ts": r[9],
        } for r in rows]
    finally:
        conn.close()


def get_trade_history(chat_id: int, limit: int = 20, db_path: str = DB_PATH) -> List[Dict]:
    """Get recent trade history."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, action, qty, price_inr, total_inr, ts, notes
            FROM crypto_trades WHERE chat_id = ?
            ORDER BY ts DESC LIMIT ?
        """, (chat_id, limit))
        rows = cur.fetchall()
        return [{
            "symbol": r[0], "action": r[1], "qty": r[2], "price_inr": r[3],
            "total_inr": r[4], "ts": r[5], "notes": r[6],
        } for r in rows]
    finally:
        conn.close()


def get_closed_trades(chat_id: int, limit: int = 20, db_path: str = DB_PATH) -> List[Dict]:
    """Get closed positions with P&L."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, name, qty, buy_price_inr, sell_price_inr,
                   invested_inr, realized_pnl_inr, added_ts, closed_ts
            FROM crypto_portfolio WHERE chat_id = ? AND status = 'CLOSED'
            ORDER BY closed_ts DESC LIMIT ?
        """, (chat_id, limit))
        rows = cur.fetchall()
        return [{
            "symbol": r[0], "name": r[1], "qty": r[2], "buy_price_inr": r[3],
            "sell_price_inr": r[4], "invested_inr": r[5], "pnl_inr": r[6],
            "added_ts": r[7], "closed_ts": r[8],
        } for r in rows]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  LIVE P&L CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

def _get_live_price_inr(symbol: str, chain: str = "solana", mint: str = "") -> float:
    """Get live price in INR for a token. Tries DexScreener first, then pump.fun."""
    try:
        from crypto_engine import get_usd_inr_rate, get_token_pairs, _normalize_dex_pair

        inr_rate = get_usd_inr_rate()

        # Try DexScreener with mint address
        if mint:
            pairs = get_token_pairs(chain, mint)
            if pairs:
                best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
                price_usd = float(best.get("priceUsd", 0) or 0)
                if price_usd > 0:
                    return price_usd * inr_rate

        # Try pump.fun for solana tokens
        if chain == "solana" and mint:
            from crypto_engine import pump_get_coin_detail, _normalize_pump_token
            detail = pump_get_coin_detail(mint)
            if detail:
                normalized = _normalize_pump_token(detail)
                return normalized.get("price_inr", 0)
    except Exception as e:
        logger.warning(f"Live price fetch failed for {symbol}: {e}")
    return 0


def calculate_portfolio_pnl(chat_id: int, db_path: str = DB_PATH) -> Dict:
    """Calculate live P&L for entire portfolio."""
    holdings = get_portfolio(chat_id, db_path)
    if not holdings:
        return {"holdings": [], "total_invested": 0, "current_value": 0,
                "total_pnl": 0, "roi_pct": 0}

    enriched = []
    total_invested = 0
    current_value = 0

    for h in holdings:
        live_price = _get_live_price_inr(h["symbol"], h["chain"], h["mint"])
        current_val = h["qty"] * live_price if live_price > 0 else 0
        pnl = current_val - h["invested_inr"] if live_price > 0 else 0
        roi = (pnl / h["invested_inr"] * 100) if h["invested_inr"] > 0 else 0

        enriched.append({
            **h,
            "live_price_inr": live_price,
            "current_value_inr": current_val,
            "unrealized_pnl_inr": pnl,
            "roi_pct": roi,
            "price_available": live_price > 0,
        })
        total_invested += h["invested_inr"]
        current_value += current_val

    total_pnl = current_value - total_invested
    roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    enriched.sort(key=lambda x: abs(x["unrealized_pnl_inr"]), reverse=True)

    return {
        "holdings": enriched,
        "total_invested": total_invested,
        "current_value": current_value,
        "total_pnl": total_pnl,
        "roi_pct": roi,
        "count": len(enriched),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  PRICE ALERTS
# ═══════════════════════════════════════════════════════════════════════════

def add_price_alert(chat_id: int, symbol: str, target_price_inr: float,
                    direction: str = "above", chain: str = "solana",
                    mint: str = "", db_path: str = DB_PATH) -> int:
    """Add a price alert. direction = 'above' or 'below'."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO crypto_price_alerts
            (chat_id, symbol, chain, mint, target_price_inr, direction, created_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, symbol.upper(), chain, mint, target_price_inr,
              direction.lower(), int(time.time())))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_active_price_alerts(chat_id: Optional[int] = None,
                            db_path: str = DB_PATH) -> List[Dict]:
    """Get active (non-triggered) price alerts."""
    init_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if chat_id:
            cur.execute("""
                SELECT id, chat_id, symbol, chain, mint, target_price_inr, direction, created_ts
                FROM crypto_price_alerts WHERE chat_id = ? AND triggered = 0
                ORDER BY created_ts DESC
            """, (chat_id,))
        else:
            cur.execute("""
                SELECT id, chat_id, symbol, chain, mint, target_price_inr, direction, created_ts
                FROM crypto_price_alerts WHERE triggered = 0
                ORDER BY created_ts DESC
            """)
        rows = cur.fetchall()
        return [{
            "id": r[0], "chat_id": r[1], "symbol": r[2], "chain": r[3],
            "mint": r[4], "target_price_inr": r[5], "direction": r[6],
            "created_ts": r[7],
        } for r in rows]
    finally:
        conn.close()


def trigger_price_alert(alert_id: int, db_path: str = DB_PATH):
    """Mark a price alert as triggered."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE crypto_price_alerts SET triggered = 1, triggered_ts = ?
            WHERE id = ?
        """, (int(time.time()), alert_id))
        conn.commit()
    finally:
        conn.close()


def delete_price_alert(alert_id: int, chat_id: int, db_path: str = DB_PATH) -> bool:
    """Delete a price alert (only if owned by user)."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM crypto_price_alerts WHERE id = ? AND chat_id = ?",
                    (alert_id, chat_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def check_price_alerts(db_path: str = DB_PATH) -> List[Dict]:
    """Check all active price alerts against live prices. Returns triggered ones."""
    alerts = get_active_price_alerts(db_path=db_path)
    triggered = []

    for alert in alerts:
        live_price = _get_live_price_inr(alert["symbol"], alert["chain"], alert["mint"])
        if live_price <= 0:
            continue

        hit = False
        if alert["direction"] == "above" and live_price >= alert["target_price_inr"]:
            hit = True
        elif alert["direction"] == "below" and live_price <= alert["target_price_inr"]:
            hit = True

        if hit:
            trigger_price_alert(alert["id"], db_path)
            alert["live_price_inr"] = live_price
            triggered.append(alert)

    return triggered


# ═══════════════════════════════════════════════════════════════════════════
#  TELEGRAM FORMATTERS (INR)
# ═══════════════════════════════════════════════════════════════════════════

def format_portfolio(pnl_data: Dict) -> str:
    """Format portfolio for Telegram message."""
    from crypto_engine import fmt_inr

    if not pnl_data.get("holdings"):
        return (
            "📂 *YOUR CRYPTO PORTFOLIO*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔹 No holdings yet!\n\n"
            "To add a token:\n"
            "`/buy SYMBOL QTY PRICE`\n"
            "Example: `/buy FARTCOIN 1000000 0.0065`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    total = pnl_data
    pnl_emoji = "🟢📈" if total["total_pnl"] >= 0 else "🔴📉"

    msg = (
        f"📂💰 *YOUR CRYPTO PORTFOLIO* 💰📂\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💼 *Summary:*\n"
        f"   📊 Holdings: {total['count']} tokens\n"
        f"   💰 Invested: {fmt_inr(total['total_invested'])}\n"
        f"   💎 Current: {fmt_inr(total['current_value'])}\n"
        f"   {pnl_emoji} P&L: {fmt_inr(abs(total['total_pnl']))} "
        f"({'+'if total['total_pnl']>=0 else '-'}{abs(total['roi_pct']):.1f}%)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    for i, h in enumerate(total["holdings"], 1):
        pnl = h["unrealized_pnl_inr"]
        roi = h["roi_pct"]
        icon = "🟢" if pnl >= 0 else "🔴"

        msg += (
            f"\n*{i}. {h['symbol']}*"
            f" ({h.get('name', '') or h.get('chain', 'SOL').upper()})\n"
            f"   🔢 Qty: {h['qty']:,.0f}\n"
            f"   💵 Buy: {fmt_inr(h['buy_price_inr'])}\n"
        )
        if h["price_available"]:
            msg += (
                f"   💰 Now: {fmt_inr(h['live_price_inr'])}\n"
                f"   {icon} P&L: {fmt_inr(abs(pnl))} ({'+' if pnl>=0 else '-'}{abs(roi):.1f}%)\n"
            )
        else:
            msg += f"   ⚠️ Price unavailable\n"

    msg += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_All prices in ₹ INR_\n"
        f"⚠️ *DYOR! Crypto is volatile.*"
    )
    return msg


def format_trade_history(trades: List[Dict]) -> str:
    """Format trade history for Telegram."""
    from crypto_engine import fmt_inr

    if not trades:
        return "📜 No trade history yet."

    msg = "📜 *TRADE HISTORY*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for t in trades[:15]:
        action_emoji = "🟢 BUY" if t["action"] == "BUY" else "🔴 SELL"
        dt = datetime.fromtimestamp(t["ts"]).strftime("%d %b %H:%M")
        msg += (
            f"{action_emoji} *{t['symbol']}*\n"
            f"   {t['qty']:,.0f} × {fmt_inr(t['price_inr'])} = {fmt_inr(t['total_inr'])}\n"
            f"   📅 {dt}\n\n"
        )

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━"
    return msg


def format_price_alert_msg(alert: Dict) -> str:
    """Format a triggered price alert."""
    from crypto_engine import fmt_inr
    direction = "⬆️ ABOVE" if alert["direction"] == "above" else "⬇️ BELOW"

    return (
        f"🔔🚨 *PRICE ALERT TRIGGERED!* 🚨🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 *{alert['symbol']}*\n"
        f"📊 Target: {direction} {fmt_inr(alert['target_price_inr'])}\n"
        f"💰 Current: {fmt_inr(alert.get('live_price_inr', 0))}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def format_alerts_list(alerts: List[Dict]) -> str:
    """Format active price alerts list."""
    from crypto_engine import fmt_inr

    if not alerts:
        return (
            "🔔 *YOUR PRICE ALERTS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "No active alerts.\n\n"
            "Set one: `/alert SYMBOL PRICE above`\n"
            "Example: `/alert FARTCOIN 0.01 above`"
        )

    msg = "🔔 *YOUR PRICE ALERTS*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for a in alerts:
        direction = "⬆️" if a["direction"] == "above" else "⬇️"
        msg += f"{direction} *{a['symbol']}* — {fmt_inr(a['target_price_inr'])} (ID: {a['id']})\n"
    msg += "\nDelete: `/delalert ID`"
    return msg


# ═══════════════════════════════════════════════════════════════════════════
#  STOCK PORTFOLIO (NSE/BSE)
# ═══════════════════════════════════════════════════════════════════════════

def init_stock_portfolio_db(db_path: str = DB_PATH):
    """Create stock portfolio tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            qty REAL NOT NULL,
            buy_price REAL NOT NULL,
            invested REAL NOT NULL,
            added_ts INTEGER NOT NULL,
            status TEXT DEFAULT 'OPEN',
            sell_price REAL DEFAULT 0,
            realized_pnl REAL DEFAULT 0,
            closed_ts INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            action TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            ts INTEGER NOT NULL,
            notes TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


def add_stock_holding(chat_id: int, symbol: str, qty: float, buy_price: float,
                      exchange: str = "NSE", db_path: str = DB_PATH) -> int:
    """Add a stock holding to portfolio."""
    init_stock_portfolio_db(db_path)
    invested = qty * buy_price
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO stock_portfolio 
            (chat_id, symbol, exchange, qty, buy_price, invested, added_ts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
        """, (chat_id, symbol.upper(), exchange.upper(), qty, buy_price,
              invested, int(time.time())))
        conn.commit()
        cur.execute("""
            INSERT INTO stock_trades (chat_id, symbol, exchange, action, qty, price, total, ts)
            VALUES (?, ?, ?, 'BUY', ?, ?, ?, ?)
        """, (chat_id, symbol.upper(), exchange.upper(), qty, buy_price,
              invested, int(time.time())))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def sell_stock_holding(chat_id: int, symbol: str, sell_price: float,
                       qty: Optional[float] = None, db_path: str = DB_PATH) -> Dict:
    """Sell stock holding (full or partial)."""
    init_stock_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, qty, buy_price, invested, added_ts FROM stock_portfolio
            WHERE chat_id = ? AND symbol = ? AND status = 'OPEN'
            ORDER BY added_ts ASC
        """, (chat_id, symbol.upper()))
        rows = cur.fetchall()

        if not rows:
            return {"success": False, "error": f"No open stock position for {symbol}"}

        total_sold = 0
        total_pnl = 0
        total_invested = 0
        holding_days = 0

        for row_id, row_qty, row_buy_price, row_invested, added_ts in rows:
            if qty is not None and total_sold >= qty:
                break
            sell_qty = row_qty if qty is None else min(row_qty, qty - total_sold)
            if sell_qty <= 0:
                continue

            pnl = (sell_price - row_buy_price) * sell_qty
            total_pnl += pnl
            total_sold += sell_qty
            total_invested += row_buy_price * sell_qty
            holding_days = max(holding_days, (int(time.time()) - added_ts) // 86400)

            if sell_qty >= row_qty:
                cur.execute("""
                    UPDATE stock_portfolio SET status = 'CLOSED', sell_price = ?,
                    realized_pnl = ?, closed_ts = ? WHERE id = ?
                """, (sell_price, pnl, int(time.time()), row_id))
            else:
                new_qty = row_qty - sell_qty
                cur.execute("""
                    UPDATE stock_portfolio SET qty = ?, invested = ? WHERE id = ?
                """, (new_qty, new_qty * row_buy_price, row_id))

        sale_total = total_sold * sell_price
        cur.execute("""
            INSERT INTO stock_trades (chat_id, symbol, action, qty, price, total, ts, notes)
            VALUES (?, ?, 'SELL', ?, ?, ?, ?, ?)
        """, (chat_id, symbol.upper(), total_sold, sell_price, sale_total,
              int(time.time()), f"P&L: ₹{total_pnl:,.2f}"))
        conn.commit()

        roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        return {
            "success": True, "symbol": symbol.upper(), "qty_sold": total_sold,
            "sell_price": sell_price, "total_received": sale_total,
            "total_invested": total_invested, "pnl": total_pnl,
            "roi_pct": roi, "holding_days": holding_days,
        }
    finally:
        conn.close()


def get_stock_portfolio(chat_id: int, db_path: str = DB_PATH) -> List[Dict]:
    """Get all open stock holdings."""
    init_stock_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, symbol, exchange, qty, buy_price, invested, added_ts
            FROM stock_portfolio WHERE chat_id = ? AND status = 'OPEN'
            ORDER BY invested DESC
        """, (chat_id,))
        rows = cur.fetchall()
        return [{"id": r[0], "symbol": r[1], "exchange": r[2], "qty": r[3],
                 "buy_price": r[4], "invested": r[5], "added_ts": r[6]} for r in rows]
    finally:
        conn.close()


def _get_stock_live_price(symbol: str) -> float:
    """Get live stock price from yfinance (NSE)."""
    try:
        import yfinance as yf
        suffixes = [".NS", ".BO", ""]
        for suffix in suffixes:
            try:
                ticker = yf.Ticker(f"{symbol}{suffix}")
                info = ticker.info or {}
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                if price and price > 0:
                    return float(price)
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"Stock price fetch failed for {symbol}: {e}")
    return 0


def calculate_stock_portfolio_pnl(chat_id: int, db_path: str = DB_PATH) -> Dict:
    """Calculate live P&L for stock portfolio."""
    holdings = get_stock_portfolio(chat_id, db_path)
    if not holdings:
        return {"holdings": [], "total_invested": 0, "current_value": 0,
                "total_pnl": 0, "roi_pct": 0, "count": 0}

    enriched = []
    total_invested = 0
    current_value = 0

    for h in holdings:
        live_price = _get_stock_live_price(h["symbol"])
        current_val = h["qty"] * live_price if live_price > 0 else 0
        pnl = current_val - h["invested"] if live_price > 0 else 0
        roi = (pnl / h["invested"] * 100) if h["invested"] > 0 else 0
        days = (int(time.time()) - h["added_ts"]) // 86400

        enriched.append({
            **h, "live_price": live_price, "current_value": current_val,
            "unrealized_pnl": pnl, "roi_pct": roi, "holding_days": days,
            "price_available": live_price > 0,
        })
        total_invested += h["invested"]
        current_value += current_val

    total_pnl = current_value - total_invested
    roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    enriched.sort(key=lambda x: abs(x["unrealized_pnl"]), reverse=True)

    return {
        "holdings": enriched, "total_invested": total_invested,
        "current_value": current_value, "total_pnl": total_pnl,
        "roi_pct": roi, "count": len(enriched),
    }


def format_stock_portfolio(pnl_data: Dict) -> str:
    """Format stock portfolio for Telegram."""
    if not pnl_data.get("holdings"):
        return (
            "📊 *YOUR STOCK PORTFOLIO* 📊\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔹 No stock holdings!\n\n"
            "Add: `/buystock RELIANCE 10 2500`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    total = pnl_data
    pnl_emoji = "🟢📈" if total["total_pnl"] >= 0 else "🔴📉"

    msg = (
        f"📊💰 *YOUR STOCK PORTFOLIO* 💰📊\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💼 *Summary:*\n"
        f"   📊 Stocks: {total['count']}\n"
        f"   💰 Invested: ₹{total['total_invested']:,.0f}\n"
        f"   💎 Current: ₹{total['current_value']:,.0f}\n"
        f"   {pnl_emoji} P&L: ₹{abs(total['total_pnl']):,.0f} "
        f"({'+'if total['total_pnl']>=0 else '-'}{abs(total['roi_pct']):.1f}%)\n\n"
    )

    for i, h in enumerate(total["holdings"][:15], 1):
        pnl = h["unrealized_pnl"]
        icon = "🟢" if pnl >= 0 else "🔴"
        msg += (
            f"*{i}. {h['symbol']}* ({h['exchange']})\n"
            f"   🔢 Qty: {h['qty']:,.0f} × ₹{h['buy_price']:,.2f}\n"
        )
        if h["price_available"]:
            msg += (
                f"   💰 CMP: ₹{h['live_price']:,.2f}\n"
                f"   {icon} P&L: ₹{abs(pnl):,.0f} ({h['roi_pct']:+.1f}%) | {h['holding_days']}d\n\n"
            )
        else:
            msg += f"   ⚠️ Price unavailable\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n_All prices in ₹ INR_"
    return msg


# ═══════════════════════════════════════════════════════════════════════════
#  INDIAN TAX CALCULATOR (Crypto + Stocks)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_tax(chat_id: int, db_path: str = DB_PATH) -> Dict:
    """Calculate Indian tax on crypto & stock gains.
    
    Crypto: 30% flat tax + 4% cess on ALL gains (no STCG/LTCG distinction)
           1% TDS on every transfer > ₹10,000
    Stocks: STCG (< 1 year) = 15% + cess
            LTCG (>= 1 year, exempt first ₹1,25,000) = 10% + cess
    """
    init_portfolio_db(db_path)
    init_stock_portfolio_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # Crypto closed trades
        cur.execute("""
            SELECT realized_pnl_inr, invested_inr, closed_ts, added_ts
            FROM crypto_portfolio WHERE chat_id = ? AND status = 'CLOSED'
        """, (chat_id,))
        crypto_rows = cur.fetchall()

        crypto_gain = sum(r[0] for r in crypto_rows if r[0] > 0)
        crypto_loss = sum(abs(r[0]) for r in crypto_rows if r[0] < 0)
        crypto_turnover = sum(r[1] for r in crypto_rows)

        # Crypto Tax: 30% + 4% cess = 31.2% (no loss offset allowed!)
        crypto_tax = crypto_gain * 0.30
        crypto_cess = crypto_tax * 0.04
        crypto_tds = crypto_turnover * 0.01 if crypto_turnover > 10000 else 0

        # Stock closed trades
        cur.execute("""
            SELECT realized_pnl, invested, closed_ts, added_ts
            FROM stock_portfolio WHERE chat_id = ? AND status = 'CLOSED'
        """, (chat_id,))
        stock_rows = cur.fetchall()

        stcg = 0  # Short-term (< 365 days)
        ltcg = 0  # Long-term (>= 365 days)
        for pnl, _, closed_ts, added_ts in stock_rows:
            if pnl <= 0:
                continue
            holding_days = (closed_ts - added_ts) // 86400 if closed_ts > added_ts else 0
            if holding_days < 365:
                stcg += pnl
            else:
                ltcg += pnl

        # Stock Tax
        stcg_tax = stcg * 0.15
        ltcg_exempt = min(ltcg, 125000)  # ₹1.25 lakh exempt
        ltcg_taxable = max(0, ltcg - ltcg_exempt)
        ltcg_tax = ltcg_taxable * 0.10
        stock_cess = (stcg_tax + ltcg_tax) * 0.04

        total_tax = crypto_tax + crypto_cess + stcg_tax + ltcg_tax + stock_cess

        return {
            "crypto_gain": crypto_gain, "crypto_loss": crypto_loss,
            "crypto_tax": crypto_tax, "crypto_cess": crypto_cess,
            "crypto_tds": crypto_tds,
            "stcg": stcg, "ltcg": ltcg, "ltcg_exempt": ltcg_exempt,
            "stcg_tax": stcg_tax, "ltcg_tax": ltcg_tax, "stock_cess": stock_cess,
            "total_tax": total_tax,
        }
    finally:
        conn.close()


def format_tax_report(tax: Dict) -> str:
    """Format tax calculation for Telegram."""
    msg = "🧾 *INDIAN TAX CALCULATOR* 🧾\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    msg += "🪙 *CRYPTO TAX (Section 115BBH):*\n"
    msg += f"   💰 Gains: ₹{tax['crypto_gain']:,.0f}\n"
    msg += f"   📉 Losses: ₹{tax['crypto_loss']:,.0f}\n"
    msg += f"   ⚠️ Loss offset: NOT ALLOWED\n"
    msg += f"   💸 Tax @30%: ₹{tax['crypto_tax']:,.0f}\n"
    msg += f"   📊 Cess @4%: ₹{tax['crypto_cess']:,.0f}\n"
    msg += f"   🏦 TDS @1%: ₹{tax['crypto_tds']:,.0f}\n\n"

    msg += "📊 *STOCK TAX:*\n"
    msg += f"   📈 STCG (<1yr): ₹{tax['stcg']:,.0f} → Tax @15%: ₹{tax['stcg_tax']:,.0f}\n"
    msg += f"   📊 LTCG (>1yr): ₹{tax['ltcg']:,.0f}\n"
    msg += f"   🎁 LTCG Exempt: ₹{tax['ltcg_exempt']:,.0f}\n"
    msg += f"   💸 LTCG Tax @10%: ₹{tax['ltcg_tax']:,.0f}\n"
    msg += f"   📊 Cess @4%: ₹{tax['stock_cess']:,.0f}\n\n"

    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💰 *TOTAL TAX LIABILITY: ₹{tax['total_tax']:,.0f}*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ _Estimate only. Consult a CA._"
    return msg


# ═══════════════════════════════════════════════════════════════════════════
#  COMBINED PORTFOLIO VIEW (Crypto + Stocks)
# ═══════════════════════════════════════════════════════════════════════════

def format_combined_portfolio(chat_id: int, db_path: str = DB_PATH) -> str:
    """Show combined crypto + stock portfolio summary."""
    crypto_pnl = calculate_portfolio_pnl(chat_id, db_path)
    stock_pnl = calculate_stock_portfolio_pnl(chat_id, db_path)

    total_invested = crypto_pnl["total_invested"] + stock_pnl["total_invested"]
    total_current = crypto_pnl["current_value"] + stock_pnl["current_value"]
    total_pnl = (total_current - total_invested)
    total_roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    crypto_pct = (crypto_pnl["current_value"] / total_current * 100) if total_current > 0 else 0
    stock_pct = 100 - crypto_pct

    p_emoji = "🟢📈" if total_pnl >= 0 else "🔴📉"

    msg = "🏦 *COMBINED PORTFOLIO* 🏦\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    msg += f"📊 *Asset Allocation:*\n"
    msg += f"   🪙 Crypto: {crypto_pct:.0f}% (₹{crypto_pnl['current_value']:,.0f})\n"
    msg += f"   📈 Stocks: {stock_pct:.0f}% (₹{stock_pnl['current_value']:,.0f})\n\n"

    msg += f"💼 *Totals:*\n"
    msg += f"   💰 Invested: ₹{total_invested:,.0f}\n"
    msg += f"   💎 Current: ₹{total_current:,.0f}\n"
    msg += f"   {p_emoji} P&L: ₹{abs(total_pnl):,.0f} ({total_roi:+.1f}%)\n\n"

    if crypto_pnl["count"] > 0:
        c_em = "🟢" if crypto_pnl['total_pnl'] >= 0 else "🔴"
        msg += f"🪙 *Crypto:* {crypto_pnl['count']} tokens | {c_em} ₹{crypto_pnl['total_pnl']:+,.0f}\n"
    if stock_pnl["count"] > 0:
        s_em = "🟢" if stock_pnl['total_pnl'] >= 0 else "🔴"
        msg += f"📊 *Stocks:* {stock_pnl['count']} stocks | {s_em} ₹{stock_pnl['total_pnl']:+,.0f}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_All prices in ₹ INR_"
    return msg
