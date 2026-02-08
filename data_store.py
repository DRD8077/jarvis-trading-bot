import sqlite3
import json
from typing import Optional, List, Dict, Any


DB_PATH = "data.db"


def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            ts INTEGER NOT NULL,
            underlying REAL,
            calls_json TEXT,
            puts_json TEXT
        )
        """
    )
    conn.commit()
    # subscriptions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            chat_id INTEGER PRIMARY KEY,
            ts INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    # watchlist table (per-user symbols)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            ts INTEGER NOT NULL,
            UNIQUE(chat_id, symbol)
        )
        """
    )
    conn.commit()
    # alert preferences (per-user thresholds)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_prefs (
            chat_id INTEGER PRIMARY KEY,
            prob_threshold REAL DEFAULT 0.65,
            ts INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    # SMS subscribers (phone numbers for SMS alerts)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sms_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            user_name TEXT DEFAULT '',
            investment_amount REAL DEFAULT 2000,
            sms_active INTEGER DEFAULT 1,
            ts INTEGER NOT NULL,
            UNIQUE(chat_id, phone)
        )
        """
    )
    conn.commit()
    # User positions (track active trades for exit alerts)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            phone TEXT DEFAULT '',
            index_name TEXT NOT NULL,
            option_type TEXT NOT NULL,
            strike REAL NOT NULL,
            entry_price REAL NOT NULL,
            qty INTEGER NOT NULL,
            investment REAL NOT NULL,
            entry_time INTEGER NOT NULL,
            status TEXT DEFAULT 'OPEN',
            exit_price REAL DEFAULT 0,
            pnl REAL DEFAULT 0,
            exit_time INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def save_snapshot(symbol: str, ts: int, underlying: float, calls: List[Dict[str, Any]], puts: List[Dict[str, Any]], db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO snapshots (symbol, ts, underlying, calls_json, puts_json) VALUES (?, ?, ?, ?, ?)",
        (symbol, ts, underlying, json.dumps(calls), json.dumps(puts)),
    )
    conn.commit()
    conn.close()


def get_recent_snapshots(symbol: str, limit: int = 50, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT ts, underlying, calls_json, puts_json FROM snapshots WHERE symbol=? ORDER BY ts DESC LIMIT ?", (symbol, limit))
    rows = cur.fetchall()
    conn.close()
    results = []
    for ts, underlying, calls_json, puts_json in rows:
        results.append({
            "ts": ts,
            "underlying": underlying,
            "calls": json.loads(calls_json),
            "puts": json.loads(puts_json),
        })
    return results


def add_subscriber(chat_id: int, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO subscriptions (chat_id, ts) VALUES (?, strftime('%s','now'))", (chat_id,))
    conn.commit()
    conn.close()


def remove_subscriber(chat_id: int, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def list_subscribers(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM subscriptions")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_to_watchlist(chat_id: int, symbol: str, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO watchlist (chat_id, symbol, ts) VALUES (?, ?, strftime('%s','now'))", (chat_id, symbol.upper()))
        conn.commit()
    finally:
        conn.close()


def remove_from_watchlist(chat_id: int, symbol: str, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM watchlist WHERE chat_id = ? AND symbol = ?", (chat_id, symbol.upper()))
        conn.commit()
    finally:
        conn.close()


def get_watchlist(chat_id: int, db_path: str = DB_PATH) -> List[str]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM watchlist WHERE chat_id = ? ORDER BY ts DESC", (chat_id,))
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def set_alert_threshold(chat_id: int, prob_threshold: float, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO alert_prefs (chat_id, prob_threshold, ts) VALUES (?, ?, strftime('%s','now'))", (chat_id, prob_threshold))
        conn.commit()
    finally:
        conn.close()


def get_alert_threshold(chat_id: int, db_path: str = DB_PATH) -> float:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT prob_threshold FROM alert_prefs WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        return float(row[0]) if row else 0.65
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Initialized DB at", DB_PATH)


# ═══════════════════════════════════════════════════════════
#  SMS SUBSCRIBER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def add_sms_subscriber(chat_id: int, phone: str, user_name: str = "", investment_amount: float = 2000, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO sms_subscribers (chat_id, phone, user_name, investment_amount, sms_active, ts) "
            "VALUES (?, ?, ?, ?, 1, strftime('%s','now'))",
            (chat_id, phone.strip(), user_name, investment_amount)
        )
        conn.commit()
    finally:
        conn.close()


def remove_sms_subscriber(chat_id: int, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE sms_subscribers SET sms_active = 0 WHERE chat_id = ?", (chat_id,))
        conn.commit()
    finally:
        conn.close()


def get_sms_subscriber(chat_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT chat_id, phone, user_name, investment_amount, sms_active FROM sms_subscribers WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        if row:
            return {
                "chat_id": row[0], "phone": row[1], "user_name": row[2],
                "investment_amount": row[3], "sms_active": bool(row[4])
            }
        return None
    finally:
        conn.close()


def list_active_sms_subscribers(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT chat_id, phone, user_name, investment_amount FROM sms_subscribers WHERE sms_active = 1")
        rows = cur.fetchall()
        return [{"chat_id": r[0], "phone": r[1], "user_name": r[2], "investment_amount": r[3]} for r in rows]
    finally:
        conn.close()


def update_sms_investment(chat_id: int, investment_amount: float, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE sms_subscribers SET investment_amount = ? WHERE chat_id = ?", (investment_amount, chat_id))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  USER POSITION TRACKING
# ═══════════════════════════════════════════════════════════

def save_position(chat_id: int, phone: str, index_name: str, option_type: str,
                  strike: float, entry_price: float, qty: int, investment: float,
                  db_path: str = DB_PATH) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_positions (chat_id, phone, index_name, option_type, strike, "
            "entry_price, qty, investment, entry_time, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), 'OPEN')",
            (chat_id, phone, index_name, option_type, strike, entry_price, qty, investment)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_open_positions(chat_id: int = None, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if chat_id:
            cur.execute("SELECT id, chat_id, phone, index_name, option_type, strike, entry_price, qty, investment, entry_time FROM user_positions WHERE status = 'OPEN' AND chat_id = ?", (chat_id,))
        else:
            cur.execute("SELECT id, chat_id, phone, index_name, option_type, strike, entry_price, qty, investment, entry_time FROM user_positions WHERE status = 'OPEN'")
        rows = cur.fetchall()
        return [{
            "id": r[0], "chat_id": r[1], "phone": r[2], "index_name": r[3],
            "option_type": r[4], "strike": r[5], "entry_price": r[6],
            "qty": r[7], "investment": r[8], "entry_time": r[9]
        } for r in rows]
    finally:
        conn.close()


def close_position(position_id: int, exit_price: float, pnl: float, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE user_positions SET status = 'CLOSED', exit_price = ?, pnl = ?, exit_time = strftime('%s','now') WHERE id = ?",
            (exit_price, pnl, position_id)
        )
        conn.commit()
    finally:
        conn.close()
