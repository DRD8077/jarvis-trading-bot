"""
🔴 JARVIS Redis Cache Layer v2.0 — Enhanced Persistent Caching
═══════════════════════════════════════════════════════════════
Drop-in replacement for miniapp_api._cache with Redis backend.
- Automatic JSON serialization
- TTL management  
- Cache warming & invalidation
- Stats dashboard
- Pub/Sub for cache events
"""

import os
import json
import time
import logging
import asyncio
from typing import Any, Optional, Dict, Callable
from functools import wraps

logger = logging.getLogger("jarvis-redis-cache")

# ═══════════════════════════════════════════════════════════
#  CONNECTION
# ═══════════════════════════════════════════════════════════
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PREFIX = "jarvis:"
_redis_client = None
_redis_available = False

# Fallback in-memory
_mem: Dict[str, Any] = {}
_mem_exp: Dict[str, float] = {}

# Stats tracking
_stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}


def _get_redis():
    global _redis_client, _redis_available
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.Redis.from_url(
            REDIS_URL, decode_responses=True,
            socket_timeout=2, socket_connect_timeout=2,
            retry_on_timeout=True, health_check_interval=30,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info("✅ Redis cache connected: %s", REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning("⚠️ Redis unavailable, using memory fallback: %s", e)
        _redis_available = False
        _redis_client = None
        return None


# ═══════════════════════════════════════════════════════════
#  CORE OPERATIONS
# ═══════════════════════════════════════════════════════════
def cache_get(key: str) -> Optional[Any]:
    """Get from Redis or fallback."""
    fk = REDIS_PREFIX + key
    r = _get_redis()
    if r:
        try:
            val = r.get(fk)
            if val is not None:
                _stats["hits"] += 1
                return json.loads(val)
            _stats["misses"] += 1
            return None
        except Exception:
            _stats["errors"] += 1
    # Fallback
    if fk in _mem:
        if _mem_exp.get(fk, 0) > time.time():
            _stats["hits"] += 1
            return _mem[fk]
        del _mem[fk]
        _mem_exp.pop(fk, None)
    _stats["misses"] += 1
    return None


def cache_set(key: str, value: Any, ttl: int = 60) -> bool:
    """Set with TTL."""
    fk = REDIS_PREFIX + key
    _stats["sets"] += 1
    r = _get_redis()
    if r:
        try:
            r.setex(fk, ttl, json.dumps(value, default=str, ensure_ascii=False))
            return True
        except Exception:
            _stats["errors"] += 1
    _mem[fk] = value
    _mem_exp[fk] = time.time() + ttl
    return True


def cache_delete(key: str) -> bool:
    """Delete key."""
    fk = REDIS_PREFIX + key
    _stats["deletes"] += 1
    r = _get_redis()
    if r:
        try:
            r.delete(fk)
        except Exception:
            pass
    _mem.pop(fk, None)
    _mem_exp.pop(fk, None)
    return True


def cache_exists(key: str) -> bool:
    fk = REDIS_PREFIX + key
    r = _get_redis()
    if r:
        try:
            return bool(r.exists(fk))
        except Exception:
            pass
    return fk in _mem and _mem_exp.get(fk, 0) > time.time()


async def cache_get_or_compute(key: str, compute_fn, ttl: int = 60) -> Any:
    """Get from cache or compute async and store."""
    val = cache_get(key)
    if val is not None:
        return val
    val = await compute_fn()
    if val is not None:
        cache_set(key, val, ttl)
    return val


def cache_get_or_compute_sync(key: str, compute_fn, ttl: int = 60) -> Any:
    """Sync version."""
    val = cache_get(key)
    if val is not None:
        return val
    val = compute_fn()
    if val is not None:
        cache_set(key, val, ttl)
    return val


# ═══════════════════════════════════════════════════════════
#  BATCH OPERATIONS
# ═══════════════════════════════════════════════════════════
def cache_mget(keys: list) -> Dict[str, Any]:
    """Get multiple keys at once."""
    r = _get_redis()
    result = {}
    if r:
        try:
            fkeys = [REDIS_PREFIX + k for k in keys]
            vals = r.mget(fkeys)
            for k, v in zip(keys, vals):
                if v is not None:
                    result[k] = json.loads(v)
                    _stats["hits"] += 1
                else:
                    _stats["misses"] += 1
            return result
        except Exception:
            pass
    for k in keys:
        v = cache_get(k)
        if v is not None:
            result[k] = v
    return result


def cache_mset(items: Dict[str, Any], ttl: int = 60) -> bool:
    """Set multiple keys at once."""
    r = _get_redis()
    if r:
        try:
            pipe = r.pipeline()
            for k, v in items.items():
                fk = REDIS_PREFIX + k
                pipe.setex(fk, ttl, json.dumps(v, default=str, ensure_ascii=False))
            pipe.execute()
            _stats["sets"] += len(items)
            return True
        except Exception:
            pass
    for k, v in items.items():
        cache_set(k, v, ttl)
    return True


# ═══════════════════════════════════════════════════════════
#  CACHE DECORATOR
# ═══════════════════════════════════════════════════════════
def cached(key_prefix: str, ttl: int = 60):
    """Decorator for caching async function results."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Build cache key from prefix + args
            arg_key = ":".join(str(a) for a in args) + ":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{arg_key}" if arg_key.strip(":") else key_prefix
            val = cache_get(cache_key)
            if val is not None:
                return val
            val = await fn(*args, **kwargs)
            if val is not None:
                cache_set(cache_key, val, ttl)
            return val
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
#  STATS & MANAGEMENT
# ═══════════════════════════════════════════════════════════
def cache_stats() -> Dict[str, Any]:
    """Comprehensive cache stats."""
    r = _get_redis()
    total = _stats["hits"] + _stats["misses"]
    stats = {
        "backend": "redis" if _redis_available else "memory",
        "available": _redis_available,
        "hits": _stats["hits"],
        "misses": _stats["misses"],
        "hit_rate": f"{(_stats['hits']/total*100):.1f}%" if total > 0 else "0%",
        "sets": _stats["sets"],
        "deletes": _stats["deletes"],
        "errors": _stats["errors"],
    }
    if r:
        try:
            info = r.info("memory")
            stats["used_memory"] = info.get("used_memory_human", "?")
            stats["keys"] = r.dbsize()
            stats["connected_clients"] = r.info("clients").get("connected_clients", 0)
        except Exception:
            pass
    else:
        now = time.time()
        expired = [k for k, t in _mem_exp.items() if t < now]
        for k in expired:
            _mem.pop(k, None)
            _mem_exp.pop(k, None)
        stats["keys"] = len(_mem)
    return stats


def cache_flush(pattern: str = "*") -> int:
    """Flush matching keys."""
    r = _get_redis()
    count = 0
    if r:
        try:
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match=REDIS_PREFIX + pattern, count=200)
                if keys:
                    r.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        except Exception:
            pass
    else:
        to_del = [k for k in _mem if k.startswith(REDIS_PREFIX)]
        for k in to_del:
            _mem.pop(k, None)
            _mem_exp.pop(k, None)
            count += 1
    return count


# ═══════════════════════════════════════════════════════════
#  PUB/SUB
# ═══════════════════════════════════════════════════════════
def publish(channel: str, data: Any) -> bool:
    r = _get_redis()
    if r:
        try:
            r.publish(REDIS_PREFIX + channel, json.dumps(data, default=str))
            return True
        except Exception:
            return False
    return False


# Initialize
_get_redis()
logger.info(f"📦 Redis cache layer ready — backend={'redis' if _redis_available else 'memory'}")
