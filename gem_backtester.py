"""
========================================================================================
  GEM SCORE BACKTESTER — Track Prediction Accuracy Over Time
========================================================================================

Features:
  1. Log every gem score prediction with timestamp
  2. Track token price 1h, 6h, 24h later
  3. Calculate accuracy: did high-score gems actually pump?
  4. Win rate by score tier (60+, 70+, 80+, 90+)
  5. Best/worst predictions ranked
  6. Weekly accuracy reports
  7. All amounts in ₹ INR
"""

import sqlite3
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("gem_backtester")

DB_PATH = "data.db"


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def init_backtest_db(db_path: str = DB_PATH):
    """Create backtesting tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gem_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT DEFAULT '',
            chain TEXT DEFAULT 'solana',
            mint TEXT DEFAULT '',
            source TEXT DEFAULT 'dexscreener',
            gem_score INTEGER NOT NULL,
            price_usd_at_scan REAL NOT NULL,
            mcap_usd_at_scan REAL DEFAULT 0,
            scan_ts INTEGER NOT NULL,
            price_1h REAL DEFAULT 0,
            price_6h REAL DEFAULT 0,
            price_24h REAL DEFAULT 0,
            change_1h REAL DEFAULT 0,
            change_6h REAL DEFAULT 0,
            change_24h REAL DEFAULT 0,
            checked_1h INTEGER DEFAULT 0,
            checked_6h INTEGER DEFAULT 0,
            checked_24h INTEGER DEFAULT 0,
            outcome TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  LOG PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════

def log_prediction(token: Dict, db_path: str = DB_PATH) -> int:
    """Log a gem score prediction for future backtesting."""
    init_backtest_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gem_predictions
            (symbol, name, chain, mint, source, gem_score, price_usd_at_scan,
             mcap_usd_at_scan, scan_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token.get("symbol", "?"),
            token.get("name", ""),
            token.get("chain", "solana"),
            token.get("mint", ""),
            token.get("source", "dexscreener"),
            token.get("gem_score", 0),
            token.get("price_usd", 0),
            token.get("mcap_usd", 0),
            int(time.time()),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def log_batch_predictions(tokens: List[Dict], min_score: int = 30,
                          db_path: str = DB_PATH) -> int:
    """Log multiple predictions at once (for background loop)."""
    count = 0
    for t in tokens:
        if t.get("gem_score", 0) >= min_score:
            log_prediction(t, db_path)
            count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════════
#  UPDATE PRICES (check outcomes)
# ═══════════════════════════════════════════════════════════════════════════

def update_prediction_prices(db_path: str = DB_PATH) -> Dict:
    """Check predictions that need price updates (1h, 6h, 24h later)."""
    init_backtest_db(db_path)
    now = time.time()
    conn = sqlite3.connect(db_path)
    updated = {"1h": 0, "6h": 0, "24h": 0}

    try:
        cur = conn.cursor()

        # Get predictions needing 1h check (scanned 1+ hour ago, not yet checked)
        cur.execute("""
            SELECT id, symbol, chain, mint, price_usd_at_scan, scan_ts
            FROM gem_predictions
            WHERE checked_1h = 0 AND ? - scan_ts >= 3600
            LIMIT 20
        """, (now,))
        rows_1h = cur.fetchall()

        for row in rows_1h:
            pid, symbol, chain, mint, entry_price, scan_ts = row
            live_price = _get_price_usd(symbol, chain, mint)
            if live_price > 0 and entry_price > 0:
                change = ((live_price - entry_price) / entry_price) * 100
                cur.execute("""
                    UPDATE gem_predictions SET price_1h = ?, change_1h = ?, checked_1h = 1
                    WHERE id = ?
                """, (live_price, change, pid))
                updated["1h"] += 1

        # 6h check
        cur.execute("""
            SELECT id, symbol, chain, mint, price_usd_at_scan, scan_ts
            FROM gem_predictions
            WHERE checked_6h = 0 AND ? - scan_ts >= 21600
            LIMIT 20
        """, (now,))
        rows_6h = cur.fetchall()

        for row in rows_6h:
            pid, symbol, chain, mint, entry_price, scan_ts = row
            live_price = _get_price_usd(symbol, chain, mint)
            if live_price > 0 and entry_price > 0:
                change = ((live_price - entry_price) / entry_price) * 100
                cur.execute("""
                    UPDATE gem_predictions SET price_6h = ?, change_6h = ?, checked_6h = 1
                    WHERE id = ?
                """, (live_price, change, pid))
                updated["6h"] += 1

        # 24h check
        cur.execute("""
            SELECT id, symbol, chain, mint, price_usd_at_scan, scan_ts
            FROM gem_predictions
            WHERE checked_24h = 0 AND ? - scan_ts >= 86400
            LIMIT 20
        """, (now,))
        rows_24h = cur.fetchall()

        for row in rows_24h:
            pid, symbol, chain, mint, entry_price, scan_ts = row
            live_price = _get_price_usd(symbol, chain, mint)
            if live_price > 0 and entry_price > 0:
                change = ((live_price - entry_price) / entry_price) * 100
                outcome = "WIN" if change > 0 else "LOSS"
                cur.execute("""
                    UPDATE gem_predictions SET price_24h = ?, change_24h = ?, checked_24h = 1,
                    outcome = ? WHERE id = ?
                """, (live_price, change, outcome, pid))
                updated["24h"] += 1

        conn.commit()
    finally:
        conn.close()

    return updated


def _get_price_usd(symbol: str, chain: str = "solana", mint: str = "") -> float:
    """Get current USD price for backtesting."""
    try:
        from crypto_engine import get_token_pairs
        if mint:
            pairs = get_token_pairs(chain, mint)
            if pairs:
                best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
                return float(best.get("priceUsd", 0) or 0)
    except Exception:
        pass
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  ACCURACY REPORTS
# ═══════════════════════════════════════════════════════════════════════════

def get_accuracy_stats(db_path: str = DB_PATH) -> Dict:
    """Calculate accuracy statistics by score tier."""
    init_backtest_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        stats = {}
        for tier_name, min_s, max_s in [
            ("All (30+)", 30, 100),
            ("B-Tier (30-49)", 30, 49),
            ("A-Tier (50-69)", 50, 69),
            ("S-Tier (70+)", 70, 100),
        ]:
            # 1h accuracy
            cur.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN change_1h > 0 THEN 1 ELSE 0 END),
                       AVG(change_1h),
                       MAX(change_1h),
                       MIN(change_1h)
                FROM gem_predictions
                WHERE checked_1h = 1 AND gem_score BETWEEN ? AND ?
            """, (min_s, max_s))
            r1 = cur.fetchone()

            # 24h accuracy
            cur.execute("""
                SELECT COUNT(*),
                       SUM(CASE WHEN change_24h > 0 THEN 1 ELSE 0 END),
                       AVG(change_24h),
                       MAX(change_24h),
                       MIN(change_24h)
                FROM gem_predictions
                WHERE checked_24h = 1 AND gem_score BETWEEN ? AND ?
            """, (min_s, max_s))
            r24 = cur.fetchone()

            total_1h = r1[0] or 0
            wins_1h = r1[1] or 0
            total_24h = r24[0] or 0
            wins_24h = r24[1] or 0

            stats[tier_name] = {
                "total_1h": total_1h,
                "win_rate_1h": (wins_1h / total_1h * 100) if total_1h > 0 else 0,
                "avg_change_1h": r1[2] or 0,
                "best_1h": r1[3] or 0,
                "worst_1h": r1[4] or 0,
                "total_24h": total_24h,
                "win_rate_24h": (wins_24h / total_24h * 100) if total_24h > 0 else 0,
                "avg_change_24h": r24[2] or 0,
                "best_24h": r24[3] or 0,
                "worst_24h": r24[4] or 0,
            }

        # Best & worst predictions
        cur.execute("""
            SELECT symbol, gem_score, change_24h, scan_ts FROM gem_predictions
            WHERE checked_24h = 1 ORDER BY change_24h DESC LIMIT 5
        """)
        best = cur.fetchall()

        cur.execute("""
            SELECT symbol, gem_score, change_24h, scan_ts FROM gem_predictions
            WHERE checked_24h = 1 ORDER BY change_24h ASC LIMIT 5
        """)
        worst = cur.fetchall()

        # Total predictions logged
        cur.execute("SELECT COUNT(*) FROM gem_predictions")
        total_logged = cur.fetchone()[0] or 0

        return {
            "tiers": stats,
            "best_predictions": [{"symbol": r[0], "score": r[1], "change_24h": r[2], "ts": r[3]} for r in best],
            "worst_predictions": [{"symbol": r[0], "score": r[1], "change_24h": r[2], "ts": r[3]} for r in worst],
            "total_logged": total_logged,
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  TELEGRAM FORMATTER
# ═══════════════════════════════════════════════════════════════════════════

def format_accuracy_report(stats: Dict) -> str:
    """Format accuracy report for Telegram."""
    if stats["total_logged"] == 0:
        return (
            "📊 *GEM SCORE BACKTESTER*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "No predictions logged yet.\n"
            "The system will automatically track gem score accuracy.\n\n"
            "Check back after some gems have been scanned!"
        )

    msg = (
        f"📊🔬 *GEM SCORE ACCURACY REPORT* 🔬📊\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Total tracked: {stats['total_logged']} predictions_\n\n"
    )

    for tier_name, data in stats["tiers"].items():
        if data["total_1h"] == 0 and data["total_24h"] == 0:
            continue

        msg += f"*{tier_name}:*\n"
        if data["total_1h"] > 0:
            wr1 = data["win_rate_1h"]
            wr_icon = "🟢" if wr1 >= 55 else "🟡" if wr1 >= 45 else "🔴"
            msg += (
                f"   1h: {wr_icon} {wr1:.0f}% win ({data['total_1h']} trades)\n"
                f"   Avg: {data['avg_change_1h']:+.1f}% | "
                f"Best: {data['best_1h']:+.1f}% | Worst: {data['worst_1h']:+.1f}%\n"
            )
        if data["total_24h"] > 0:
            wr24 = data["win_rate_24h"]
            wr_icon = "🟢" if wr24 >= 55 else "🟡" if wr24 >= 45 else "🔴"
            msg += (
                f"   24h: {wr_icon} {wr24:.0f}% win ({data['total_24h']} trades)\n"
                f"   Avg: {data['avg_change_24h']:+.1f}% | "
                f"Best: {data['best_24h']:+.1f}% | Worst: {data['worst_24h']:+.1f}%\n"
            )
        msg += "\n"

    # Best predictions
    if stats.get("best_predictions"):
        msg += "🏆 *TOP PREDICTIONS (24h):*\n"
        for p in stats["best_predictions"][:3]:
            dt = datetime.fromtimestamp(p["ts"]).strftime("%d %b")
            msg += f"   🟢 {p['symbol']} (Score {p['score']}) → {p['change_24h']:+.1f}% [{dt}]\n"
        msg += "\n"

    # Worst predictions
    if stats.get("worst_predictions"):
        msg += "💀 *WORST PREDICTIONS (24h):*\n"
        for p in stats["worst_predictions"][:3]:
            dt = datetime.fromtimestamp(p["ts"]).strftime("%d %b")
            msg += f"   🔴 {p['symbol']} (Score {p['score']}) → {p['change_24h']:+.1f}% [{dt}]\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 _Accuracy improves with more data. Let it run!_"
    return msg
