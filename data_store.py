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
