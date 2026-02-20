"""
🛡️ JARVIS Per-User Rate Limiter — SlowAPI + Custom Redis
═══════════════════════════════════════════════════════════
Per-user rate limiting using Redis-backed sliding window:
- Different limits per role (user/premium/admin)
- Per-endpoint rate limits
- Redis-backed for multi-instance
- Integrates with FastAPI via middleware
"""

import os
import time
import logging
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("jarvis-rate-limiter")

# ═══════════════════════════════════════════════════════════
#  CONFIG — requests per minute by role
# ═══════════════════════════════════════════════════════════
RATE_LIMITS = {
    "owner": 1000,
    "admin": 1000,
    "premium": 300,
    "user": 120,
    "anonymous": 120,
}

# Sensitive endpoints get stricter limits (per minute)
ENDPOINT_LIMITS = {
    "/api/miniapp/chat": 15,
    "/api/miniapp/auto-trader/start": 5,
    "/api/miniapp/auto-trader/stop": 5,
    "/api/admin/broadcast": 3,
    "/api/admin/bot": 10,
    "/api/auth/login": 10,
    "/api/auth/register": 5,
}

WINDOW_SECONDS = 60


def _get_redis():
    try:
        from jarvis_redis_cache import _get_redis as get_r
        return get_r()
    except Exception:
        return None


# In-memory fallback
_mem_counters = {}


def _get_user_id(request: Request) -> str:
    """Extract user ID from request (JWT, query param, or IP)."""
    # Try JWT
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from jarvis_jwt_auth import verify_access_token
            payload = verify_access_token(auth[7:])
            if payload:
                return f"user:{payload['sub']}"
        except Exception:
            pass
    # Try query param
    uid = request.query_params.get("user_id", "")
    if uid and uid != "0":
        return f"user:{uid}"
    # Fallback to IP
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    return f"ip:{ip}"


def _get_role(request: Request) -> str:
    """Get user role from request."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from jarvis_jwt_auth import verify_access_token
            payload = verify_access_token(auth[7:])
            if payload:
                return payload.get("role", "user")
        except Exception:
            pass
    return "anonymous"


def check_rate_limit(identifier: str, role: str, endpoint: str = "") -> tuple:
    """
    Check rate limit. Returns (allowed: bool, remaining: int, reset_at: int).
    """
    # Determine limit
    limit = RATE_LIMITS.get(role, RATE_LIMITS["anonymous"])
    # Check endpoint-specific limits
    ep_limit = None
    for ep_path, ep_max in ENDPOINT_LIMITS.items():
        if endpoint.startswith(ep_path):
            ep_limit = ep_max
            break

    now = int(time.time())
    window_key = f"ratelimit:{identifier}:{now // WINDOW_SECONDS}"

    r = _get_redis()
    if r:
        try:
            pipe = r.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, WINDOW_SECONDS + 5)
            count_result = pipe.execute()
            count = count_result[0]
        except Exception:
            count = 1
    else:
        # Memory fallback
        if window_key not in _mem_counters:
            _mem_counters[window_key] = 0
            # Cleanup old windows
            cutoff = f"ratelimit:{identifier}:{(now // WINDOW_SECONDS) - 2}"
            to_del = [k for k in _mem_counters if k < cutoff and k.startswith(f"ratelimit:{identifier}:")]
            for k in to_del:
                del _mem_counters[k]
        _mem_counters[window_key] += 1
        count = _mem_counters[window_key]

    # Check endpoint limit
    if ep_limit is not None:
        ep_key = f"ratelimit:{identifier}:ep:{endpoint}:{now // WINDOW_SECONDS}"
        if r:
            try:
                pipe = r.pipeline()
                pipe.incr(ep_key)
                pipe.expire(ep_key, WINDOW_SECONDS + 5)
                ep_result = pipe.execute()
                ep_count = ep_result[0]
            except Exception:
                ep_count = 1
        else:
            _mem_counters.setdefault(ep_key, 0)
            _mem_counters[ep_key] += 1
            ep_count = _mem_counters[ep_key]
        if ep_count > ep_limit:
            remaining = 0
            reset_at = (now // WINDOW_SECONDS + 1) * WINDOW_SECONDS
            return False, remaining, reset_at

    allowed = count <= limit
    remaining = max(0, limit - count)
    reset_at = (now // WINDOW_SECONDS + 1) * WINDOW_SECONDS
    return allowed, remaining, reset_at


# ═══════════════════════════════════════════════════════════
#  FASTAPI MIDDLEWARE
# ═══════════════════════════════════════════════════════════
class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user rate limiting middleware."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip rate limiting for static files, health, docs, metrics, admin pages
        SKIP_PREFIXES = [
            "/static", "/assets", "/health", "/ping", "/favicon",
            "/docs", "/redoc", "/openapi.json",
            "/metrics",
            "/admin",
            "/api/health",
            "/api/sse/",          # SSE streams are long-lived
        ]
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        # Localhost bypass for internal/dev requests
        client_ip = request.client.host if request.client else ""
        if client_ip in ("127.0.0.1", "::1", "localhost"):
            forwarded = request.headers.get("x-forwarded-for", "")
            if not forwarded:  # Only bypass if truly local (no proxy)
                return await call_next(request)

        identifier = _get_user_id(request)
        role = _get_role(request)
        allowed, remaining, reset_at = check_rate_limit(identifier, role, path)

        if not allowed:
            return JSONResponse(
                {"error": "Rate limit exceeded. Please slow down.", "retry_after": reset_at - int(time.time())},
                status_code=429,
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(reset_at - int(time.time())),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response


# Alias for server
RateLimiterMiddleware = UserRateLimitMiddleware

RATE_LIMITER_AVAILABLE = True
logger.info("🛡️ Per-user rate limiter loaded")
