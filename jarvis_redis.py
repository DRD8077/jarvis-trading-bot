"""
🔴 JARVIS Redis Caching Layer — Persistent, Fast, Scalable
═══════════════════════════════════════════════════════════════
Replaces in-memory dict caching with Redis for:
- Persistence across server restarts
- Multi-instance scaling
- TTL-based automatic expiry
- Cache stats & monitoring
"""

import os
import json
import time
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger("jarvis-redis")

# ═══════════════════════════════════════════════════════════
#  REDIS CONNECTION
# ═══════════════════════════════════════════════════════════
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PREFIX = "jarvis:"
REDIS_AVAILABLE = False

_redis = None

def get_redis():
    """Get Redis connection (lazy singleton)."""
    global _redis, REDIS_AVAILABLE
    if _redis is not None:
        return _redis
    try:
        import redis
        _redis = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
            retry_on_timeout=True,
        )
        _redis.ping()
        REDIS_AVAILABLE = True
        logger.info("✅ Redis connected: %s", REDIS_URL)
        return _redis
    except Exception as e:
        logger.warning("⚠️ Redis not available, using fallback memory cache: %s", e)
        REDIS_AVAILABLE = False
        _redis = None
        return None


# ═══════════════════════════════════════════════════════════
#  FALLBACK IN-MEMORY CACHE (when Redis unavailable)
# ═══════════════════════════════════════════════════════════
_mem_cache: Dict[str, Any] = {}
_mem_ts: Dict[str, float] = {}


# ═══════════════════════════════════════════════════════════
#  CACHE OPERATIONS
# ═══════════════════════════════════════════════════════════
def cache_get(key: str) -> Optional[Any]:
    """Get value from cache (Redis or fallback)."""
    full_key = REDIS_PREFIX + key
    r = get_redis()
    if r:
        try:
            val = r.get(full_key)
            if val is not None:
                return json.loads(val)
            return None
        except Exception as e:
            logger.debug("Redis GET error: %s", e)
    # Fallback
    if full_key in _mem_cache:
        return _mem_cache[full_key]
    return None


def cache_set(key: str, value: Any, ttl: int = 60) -> bool:
    """Set value in cache with TTL in seconds."""
    full_key = REDIS_PREFIX + key
    r = get_redis()
    if r:
        try:
            serialized = json.dumps(value, default=str, ensure_ascii=False)
            r.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug("Redis SET error: %s", e)
    # Fallback
    _mem_cache[full_key] = value
    _mem_ts[full_key] = time.time() + ttl
    return True


def cache_delete(key: str) -> bool:
    """Delete a cache key."""
    full_key = REDIS_PREFIX + key
    r = get_redis()
    if r:
        try:
            r.delete(full_key)
            return True
        except Exception:
            pass
    _mem_cache.pop(full_key, None)
    _mem_ts.pop(full_key, None)
    return True


def cache_exists(key: str) -> bool:
    """Check if key exists."""
    full_key = REDIS_PREFIX + key
    r = get_redis()
    if r:
        try:
            return bool(r.exists(full_key))
        except Exception:
            pass
    return full_key in _mem_cache


def cache_get_or_set(key: str, factory_fn, ttl: int = 60) -> Any:
    """Get from cache or compute and set. Sync version."""
    val = cache_get(key)
    if val is not None:
        return val
    val = factory_fn()
    if val is not None:
        cache_set(key, val, ttl)
    return val


async def cache_get_or_set_async(key: str, factory_fn, ttl: int = 60) -> Any:
    """Get from cache or compute and set. Async version."""
    val = cache_get(key)
    if val is not None:
        return val
    val = await factory_fn()
    if val is not None:
        cache_set(key, val, ttl)
    return val


# ═══════════════════════════════════════════════════════════
#  CACHE STATS & MANAGEMENT
# ═══════════════════════════════════════════════════════════
def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    r = get_redis()
    stats = {
        "backend": "redis" if r else "memory",
        "available": REDIS_AVAILABLE,
    }
    if r:
        try:
            info = r.info("memory")
            stats["used_memory"] = info.get("used_memory_human", "?")
            stats["keys"] = r.dbsize()
            stats["hit_rate"] = info.get("keyspace_hits", 0)
            stats["miss_rate"] = info.get("keyspace_misses", 0)
            stats["connected_clients"] = r.info("clients").get("connected_clients", 0)
        except Exception:
            pass
    else:
        # Clean expired fallback entries
        now = time.time()
        expired = [k for k, ts in _mem_ts.items() if ts < now]
        for k in expired:
            _mem_cache.pop(k, None)
            _mem_ts.pop(k, None)
        stats["keys"] = len(_mem_cache)
        stats["used_memory"] = f"{sum(len(str(v)) for v in _mem_cache.values()) // 1024}KB"
    return stats


def cache_flush(pattern: str = "*") -> int:
    """Flush cache keys matching pattern."""
    r = get_redis()
    count = 0
    if r:
        try:
            full_pattern = REDIS_PREFIX + pattern
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match=full_pattern, count=100)
                if keys:
                    r.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning("Cache flush error: %s", e)
    else:
        to_del = [k for k in _mem_cache if k.startswith(REDIS_PREFIX)]
        for k in to_del:
            _mem_cache.pop(k, None)
            _mem_ts.pop(k, None)
            count += 1
    return count


def cache_ttl(key: str) -> int:
    """Get remaining TTL for a key in seconds."""
    full_key = REDIS_PREFIX + key
    r = get_redis()
    if r:
        try:
            return r.ttl(full_key)
        except Exception:
            pass
    if full_key in _mem_ts:
        remaining = int(_mem_ts[full_key] - time.time())
        return max(remaining, 0)
    return -2  # Key doesn't exist


# ═══════════════════════════════════════════════════════════
#  PUB/SUB FOR REAL-TIME EVENTS
# ═══════════════════════════════════════════════════════════
def publish_event(channel: str, data: Any) -> bool:
    """Publish event to Redis pub/sub channel."""
    r = get_redis()
    if r:
        try:
            r.publish(REDIS_PREFIX + channel, json.dumps(data, default=str))
            return True
        except Exception:
            pass
    return False


def subscribe_channel(channel: str):
    """Subscribe to Redis pub/sub channel. Returns pubsub object."""
    r = get_redis()
    if r:
        try:
            ps = r.pubsub()
            ps.subscribe(REDIS_PREFIX + channel)
            return ps
        except Exception:
            pass
    return None


# Initialize on import
get_redis()
