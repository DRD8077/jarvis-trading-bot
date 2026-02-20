"""
🐘 JARVIS PostgreSQL Layer — Production Database
═══════════════════════════════════════════════════
Migration from SQLite + JSON files to PostgreSQL:
- Async connection pool via asyncpg
- User management
- Trade history
- Signal logs
- Portfolio tracking
- Falls back to SQLite if PG unavailable
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("jarvis-postgres")
IST = timezone(timedelta(hours=5, minutes=30))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jarvis")
PG_AVAILABLE = False
_pool = None


# ═══════════════════════════════════════════════════════════
#  CONNECTION POOL
# ═══════════════════════════════════════════════════════════
async def init_pool():
    """Initialize asyncpg connection pool."""
    global _pool, PG_AVAILABLE
    try:
        import asyncpg
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        PG_AVAILABLE = True
        logger.info("✅ PostgreSQL pool initialized: %s", DATABASE_URL.split("@")[-1])
        await _create_tables()
        return True
    except Exception as e:
        logger.warning("⚠️ PostgreSQL not available, using SQLite fallback: %s", e)
        PG_AVAILABLE = False
        return False


async def close_pool():
    """Close connection pool."""
    global _pool, PG_AVAILABLE
    if _pool:
        await _pool.close()
        _pool = None
        PG_AVAILABLE = False
        logger.info("PostgreSQL pool closed")


async def get_pool():
    global _pool
    if _pool is None:
        await init_pool()
    return _pool


# ═══════════════════════════════════════════════════════════
#  SCHEMA
# ═══════════════════════════════════════════════════════════
async def _create_tables():
    """Create all tables if they don't exist."""
    pool = await get_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                is_premium BOOLEAN DEFAULT FALSE,
                is_blocked BOOLEAN DEFAULT FALSE,
                language TEXT DEFAULT 'hi',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login TIMESTAMP WITH TIME ZONE,
                login_count INTEGER DEFAULT 0,
                telegram_data JSONB DEFAULT '{}'::jsonb
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity NUMERIC,
                price NUMERIC,
                total NUMERIC,
                pnl NUMERIC DEFAULT 0,
                status TEXT DEFAULT 'open',
                strategy TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                closed_at TIMESTAMP WITH TIME ZONE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signals_log (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_type TEXT,
                confidence NUMERIC,
                price NUMERIC,
                target NUMERIC,
                stop_loss NUMERIC,
                source TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                outcome TEXT,
                actual_price NUMERIC
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                symbol TEXT NOT NULL,
                quantity NUMERIC,
                avg_price NUMERIC,
                current_price NUMERIC DEFAULT 0,
                pnl NUMERIC DEFAULT 0,
                added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                symbol TEXT NOT NULL,
                target_price NUMERIC,
                condition TEXT DEFAULT 'above',
                triggered BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                triggered_at TIMESTAMP WITH TIME ZONE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS social_signals (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                user_name TEXT,
                symbol TEXT NOT NULL,
                signal_type TEXT,
                confidence INTEGER,
                note TEXT,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key_name TEXT UNIQUE NOT NULL,
                key_value TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        # Indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals_log(symbol)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_social_symbol ON social_signals(symbol)")

    logger.info("📋 PostgreSQL tables verified")


# ═══════════════════════════════════════════════════════════
#  USER OPERATIONS
# ═══════════════════════════════════════════════════════════
async def pg_upsert_user(user_id: str, name: str = "", phone: str = "",
                         role: str = "user", telegram_data: dict = None) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, name, phone, role, telegram_data, last_login, login_count)
                VALUES ($1, $2, $3, $4, $5::jsonb, NOW(), 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = COALESCE(NULLIF($2, ''), users.name),
                    last_login = NOW(),
                    login_count = users.login_count + 1
            """, user_id, name, phone, role, json.dumps(telegram_data or {}))
        return True
    except Exception as e:
        logger.error(f"PG upsert user error: {e}")
        return False


async def pg_get_users(limit: int = 100) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY last_login DESC NULLS LAST LIMIT $1", limit
            )
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PG get users error: {e}")
        return []


async def pg_get_user(user_id: str) -> Optional[Dict]:
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"PG get user error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  SIGNAL LOG
# ═══════════════════════════════════════════════════════════
async def pg_log_signal(symbol: str, signal_type: str, confidence: float,
                        price: float, target: float = 0, stop_loss: float = 0,
                        source: str = "ai") -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO signals_log (symbol, signal_type, confidence, price, target, stop_loss, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, symbol, signal_type, confidence, price, target, stop_loss, source)
        return True
    except Exception as e:
        logger.error(f"PG log signal error: {e}")
        return False


async def pg_get_signals(limit: int = 50, symbol: str = None) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            if symbol:
                rows = await conn.fetch(
                    "SELECT * FROM signals_log WHERE symbol = $1 ORDER BY created_at DESC LIMIT $2", symbol, limit
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM signals_log ORDER BY created_at DESC LIMIT $1", limit
                )
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PG get signals error: {e}")
        return []


# ═══════════════════════════════════════════════════════════
#  TRADE HISTORY
# ═══════════════════════════════════════════════════════════
async def pg_log_trade(user_id: str, symbol: str, side: str,
                       quantity: float, price: float, strategy: str = "") -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO trades (user_id, symbol, side, quantity, price, total, strategy)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, user_id, symbol, side, quantity, price, quantity * price, strategy)
        return True
    except Exception as e:
        logger.error(f"PG log trade error: {e}")
        return False


async def pg_get_trades(user_id: str, limit: int = 50) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM trades WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2", user_id, limit
            )
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PG get trades error: {e}")
        return []


# ═══════════════════════════════════════════════════════════
#  SOCIAL SIGNALS
# ═══════════════════════════════════════════════════════════
async def pg_add_social_signal(user_id: str, user_name: str, symbol: str,
                               signal_type: str, confidence: int, note: str = "") -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO social_signals (user_id, user_name, symbol, signal_type, confidence, note)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, user_name, symbol, signal_type, confidence, note)
        return True
    except Exception as e:
        logger.error(f"PG social signal error: {e}")
        return False


async def pg_get_social_signals(symbol: str = None, limit: int = 30) -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            if symbol:
                rows = await conn.fetch(
                    "SELECT * FROM social_signals WHERE symbol = $1 ORDER BY created_at DESC LIMIT $2", symbol, limit
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM social_signals ORDER BY created_at DESC LIMIT $1", limit
                )
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PG social signals error: {e}")
        return []


async def pg_like_signal(signal_id: int) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE social_signals SET likes = likes + 1 WHERE id = $1", signal_id)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
#  API KEYS MANAGEMENT
# ═══════════════════════════════════════════════════════════
async def pg_get_api_keys() -> List[Dict]:
    pool = await get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, key_name, is_active, created_at, updated_at FROM api_keys ORDER BY key_name")
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PG get api keys error: {e}")
        return []


async def pg_set_api_key(key_name: str, key_value: str) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO api_keys (key_name, key_value)
                VALUES ($1, $2)
                ON CONFLICT (key_name) DO UPDATE SET
                    key_value = $2, updated_at = NOW(), is_active = TRUE
            """, key_name, key_value)
        # Also set in environment
        os.environ[key_name] = key_value
        return True
    except Exception as e:
        logger.error(f"PG set api key error: {e}")
        return False


async def pg_delete_api_key(key_name: str) -> bool:
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE api_keys SET is_active = FALSE WHERE key_name = $1", key_name)
        os.environ.pop(key_name, None)
        return True
    except Exception as e:
        logger.error(f"PG delete api key error: {e}")
        return False


async def pg_load_api_keys():
    """Load all active API keys from DB into environment."""
    pool = await get_pool()
    if not pool:
        return 0
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT key_name, key_value FROM api_keys WHERE is_active = TRUE")
            count = 0
            for row in rows:
                os.environ[row["key_name"]] = row["key_value"]
                count += 1
            logger.info(f"📋 Loaded {count} API keys from PostgreSQL")
            return count
    except Exception as e:
        logger.error(f"PG load api keys error: {e}")
        return 0


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
async def pg_stats() -> Dict:
    pool = await get_pool()
    if not pool:
        return {"available": False}
    try:
        async with pool.acquire() as conn:
            users = await conn.fetchval("SELECT COUNT(*) FROM users")
            trades = await conn.fetchval("SELECT COUNT(*) FROM trades")
            signals = await conn.fetchval("SELECT COUNT(*) FROM signals_log")
            social = await conn.fetchval("SELECT COUNT(*) FROM social_signals")
            return {
                "available": True,
                "users": users,
                "trades": trades,
                "signals": signals,
                "social_signals": social,
                "pool_size": _pool.get_size() if _pool else 0,
            }
    except Exception as e:
        return {"available": False, "error": str(e)}


logger.info(f"🐘 PostgreSQL layer loaded — URL={'configured' if DATABASE_URL else 'not set'}")
