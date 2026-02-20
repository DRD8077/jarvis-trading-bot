"""
🐘 JARVIS PostgreSQL Database Layer — Production-Grade Persistence
═════════════════════════════════════════════════════════════════════
Migrates from SQLite + JSON files to PostgreSQL:
- Async connection pool via asyncpg
- SQLAlchemy models for ORM
- Auto-migration on startup
- Concurrent access safe
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger("jarvis-db")

IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jarvis:jarvis123@localhost:5432/jarvis_db")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

PG_AVAILABLE = False
_pool = None

# ═══════════════════════════════════════════════════════════
#  CONNECTION POOL
# ═══════════════════════════════════════════════════════════
async def get_pool():
    """Get or create asyncpg connection pool."""
    global _pool, PG_AVAILABLE
    if _pool is not None:
        return _pool
    try:
        import asyncpg
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        PG_AVAILABLE = True
        logger.info("✅ PostgreSQL pool created")
        return _pool
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL not available: {e}")
        PG_AVAILABLE = False
        return None


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ═══════════════════════════════════════════════════════════
#  SCHEMA MIGRATION
# ═══════════════════════════════════════════════════════════
SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    password_hash TEXT DEFAULT '',
    role TEXT DEFAULT 'user',
    is_premium BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    language TEXT DEFAULT 'hi',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW(),
    login_count INTEGER DEFAULT 0,
    telegram_data JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}'
);

-- Feature toggles
CREATE TABLE IF NOT EXISTS feature_toggles (
    feature_id TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT DEFAULT ''
);

-- Trading signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    confidence REAL DEFAULT 0,
    price REAL DEFAULT 0,
    change_24h REAL DEFAULT 0,
    source TEXT DEFAULT '',
    market TEXT DEFAULT 'crypto',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);

-- Portfolio positions
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    side TEXT DEFAULT 'long',
    quantity REAL DEFAULT 0,
    entry_price REAL DEFAULT 0,
    current_price REAL DEFAULT 0,
    pnl REAL DEFAULT 0,
    pnl_pct REAL DEFAULT 0,
    status TEXT DEFAULT 'open',
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_positions_user ON positions(user_id);

-- Trade history
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL DEFAULT 0,
    price REAL DEFAULT 0,
    total REAL DEFAULT 0,
    pnl REAL DEFAULT 0,
    strategy TEXT DEFAULT '',
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);

-- Social signals (shared by users)
CREATE TABLE IF NOT EXISTS social_signals (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT DEFAULT '',
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    confidence REAL DEFAULT 0,
    note TEXT DEFAULT '',
    likes INTEGER DEFAULT 0,
    copies INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_social_created ON social_signals(created_at DESC);

-- Broadcast history
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    sent_by TEXT DEFAULT '',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    recipients INTEGER DEFAULT 0
);

-- Admin action log
CREATE TABLE IF NOT EXISTS admin_log (
    id SERIAL PRIMARY KEY,
    admin_id TEXT DEFAULT '',
    action TEXT NOT NULL,
    details TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API keys management
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_name TEXT UNIQUE NOT NULL,
    key_value TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    last_rotated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolio snapshots (for P&L charts)
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    total_value REAL DEFAULT 0,
    total_pnl REAL DEFAULT 0,
    positions_count INTEGER DEFAULT 0,
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_snapshots_user ON portfolio_snapshots(user_id, snapshot_at DESC);

-- Backtests
CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    start_date TEXT DEFAULT '',
    end_date TEXT DEFAULT '',
    initial_capital REAL DEFAULT 100000,
    final_capital REAL DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    max_drawdown REAL DEFAULT 0,
    sharpe_ratio REAL DEFAULT 0,
    results JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

async def init_database():
    """Initialize all database tables."""
    pool = await get_pool()
    if not pool:
        logger.warning("PostgreSQL not available — using SQLite/JSON fallback")
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        logger.info("✅ PostgreSQL schema initialized")
        return True
    except Exception as e:
        logger.error(f"Schema migration error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  CRUD OPERATIONS
# ═══════════════════════════════════════════════════════════

# --- Users ---
async def db_upsert_user(user_id: str, name: str = "", phone: str = "",
                          role: str = "user", telegram_data: dict = None) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, name, phone, role, telegram_data, last_login)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    name = COALESCE(NULLIF($2, ''), users.name),
                    last_login = NOW(),
                    login_count = users.login_count + 1
            """, user_id, name, phone, role, json.dumps(telegram_data or {}))
        return True
    except Exception as e:
        logger.error(f"Upsert user error: {e}")
        return False


async def db_get_user(user_id: str) -> Optional[Dict]:
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            if row:
                return dict(row)
    except Exception as e:
        logger.error(f"Get user error: {e}")
    return None


async def db_get_all_users() -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY last_login DESC")
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Get users error: {e}")
    return []


# --- Signals ---
async def db_save_signal(symbol: str, signal_type: str, confidence: float = 0,
                          price: float = 0, change_24h: float = 0,
                          source: str = "", market: str = "crypto",
                          metadata: dict = None) -> Optional[int]:
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO signals (symbol, signal_type, confidence, price, change_24h, source, market, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, symbol, signal_type, confidence, price, change_24h, source, market, json.dumps(metadata or {}))
            return row["id"]
    except Exception as e:
        logger.error(f"Save signal error: {e}")
    return None


async def db_get_recent_signals(limit: int = 50, market: str = None) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            if market:
                rows = await conn.fetch(
                    "SELECT * FROM signals WHERE market = $1 ORDER BY created_at DESC LIMIT $2",
                    market, limit)
            else:
                rows = await conn.fetch(
                    "SELECT * FROM signals ORDER BY created_at DESC LIMIT $1", limit)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Get signals error: {e}")
    return []


# --- Social Signals ---
async def db_share_signal(user_id: str, user_name: str, symbol: str,
                           signal_type: str, confidence: float = 0,
                           note: str = "") -> Optional[int]:
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO social_signals (user_id, user_name, symbol, signal_type, confidence, note)
                VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """, user_id, user_name, symbol, signal_type, confidence, note)
            return row["id"]
    except Exception as e:
        logger.error(f"Share signal error: {e}")
    return None


async def db_get_social_feed(limit: int = 30) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM social_signals ORDER BY created_at DESC LIMIT $1", limit)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Social feed error: {e}")
    return []


async def db_like_signal(signal_id: int) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_signals SET likes = likes + 1 WHERE id = $1", signal_id)
            return True
    except Exception:
        return False


async def db_copy_signal(signal_id: int) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_signals SET copies = copies + 1 WHERE id = $1", signal_id)
            return True
    except Exception:
        return False


# --- Portfolio Snapshots ---
async def db_save_portfolio_snapshot(user_id: str, total_value: float,
                                      total_pnl: float, positions_count: int) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO portfolio_snapshots (user_id, total_value, total_pnl, positions_count)
                VALUES ($1, $2, $3, $4)
            """, user_id, total_value, total_pnl, positions_count)
            return True
    except Exception:
        return False


async def db_get_portfolio_history(user_id: str, days: int = 30) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT total_value, total_pnl, positions_count, snapshot_at
                FROM portfolio_snapshots
                WHERE user_id = $1 AND snapshot_at > NOW() - INTERVAL '%s days'
                ORDER BY snapshot_at ASC
            """ % days, user_id)
            return [dict(r) for r in rows]
    except Exception:
        return []


# --- API Keys ---
async def db_get_api_keys() -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM api_keys ORDER BY key_name")
            return [dict(r) for r in rows]
    except Exception:
        return []


async def db_set_api_key(key_name: str, key_value: str) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO api_keys (key_name, key_value, last_rotated)
                VALUES ($1, $2, NOW())
                ON CONFLICT (key_name) DO UPDATE SET
                    key_value = $2, last_rotated = NOW()
            """, key_name, key_value)
            # Also set in environment
            os.environ[key_name] = key_value
            return True
    except Exception as e:
        logger.error(f"Set API key error: {e}")
    return False


async def db_delete_api_key(key_name: str) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM api_keys WHERE key_name = $1", key_name)
            os.environ.pop(key_name, None)
            return True
    except Exception:
        return False


# --- Backtests ---
async def db_save_backtest(user_id: str, symbol: str, strategy: str,
                            results: dict) -> Optional[int]:
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO backtests (user_id, symbol, strategy,
                    start_date, end_date, initial_capital, final_capital,
                    total_trades, win_rate, max_drawdown, sharpe_ratio, results)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, user_id, symbol, strategy,
                results.get("start_date", ""), results.get("end_date", ""),
                results.get("initial_capital", 100000), results.get("final_capital", 0),
                results.get("total_trades", 0), results.get("win_rate", 0),
                results.get("max_drawdown", 0), results.get("sharpe_ratio", 0),
                json.dumps(results))
            return row["id"]
    except Exception as e:
        logger.error(f"Save backtest error: {e}")
    return None


async def db_get_backtests(user_id: str, limit: int = 20) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM backtests WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit)
            return [dict(r) for r in rows]
    except Exception:
        return []


# --- Stats ---
async def db_stats() -> Dict[str, Any]:
    """Get database statistics."""
    pool = await get_pool()
    if not pool:
        return {"backend": "unavailable"}
    try:
        async with pool.acquire() as conn:
            users = await conn.fetchval("SELECT COUNT(*) FROM users")
            signals = await conn.fetchval("SELECT COUNT(*) FROM signals")
            trades = await conn.fetchval("SELECT COUNT(*) FROM trades")
            social = await conn.fetchval("SELECT COUNT(*) FROM social_signals")
            return {
                "backend": "postgresql",
                "users": users,
                "signals": signals,
                "trades": trades,
                "social_signals": social,
                "status": "connected",
            }
    except Exception as e:
        return {"backend": "postgresql", "status": "error", "error": str(e)}


# Aliases for server compatibility
init_db = init_database
DB_AVAILABLE = PG_AVAILABLE

logger.info("✅ PostgreSQL module loaded")
