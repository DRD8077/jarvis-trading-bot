"""
📊 JARVIS Prometheus Metrics — Observability & Monitoring
═════════════════════════════════════════════════════════════
Track API latency, cache hits, engine health, WebSocket.
Exposes /metrics endpoint for Prometheus scraping.
"""

import time
import logging
from typing import Callable
from functools import wraps

from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("jarvis-metrics")

# ═══════════════════════════════════════════════════════════
#  METRICS DEFINITIONS
# ═══════════════════════════════════════════════════════════

# HTTP request metrics
REQUEST_COUNT = Counter(
    "jarvis_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "jarvis_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    "jarvis_websocket_connections",
    "Active WebSocket connections",
)

WS_MESSAGES = Counter(
    "jarvis_websocket_messages_total",
    "Total WebSocket messages sent",
    ["direction"],  # sent, received
)

# Cache metrics
CACHE_HITS = Counter(
    "jarvis_cache_hits_total",
    "Cache hit count",
    ["backend"],  # redis, memory
)

CACHE_MISSES = Counter(
    "jarvis_cache_misses_total",
    "Cache miss count",
    ["backend"],
)

CACHE_SIZE = Gauge(
    "jarvis_cache_entries",
    "Number of entries in cache",
)

# Engine metrics
ENGINE_STATUS = Gauge(
    "jarvis_engine_active",
    "Engine active status (1=active, 0=down)",
    ["engine_name"],
)

ENGINES_LOADED = Gauge(
    "jarvis_engines_loaded_total",
    "Total number of engines loaded",
)

# AI metrics
AI_REQUESTS = Counter(
    "jarvis_ai_requests_total",
    "Total AI provider requests",
    ["provider"],  # groq, openai, gemini
)

AI_LATENCY = Histogram(
    "jarvis_ai_request_duration_seconds",
    "AI request duration",
    ["provider"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Signal metrics
SIGNALS_GENERATED = Counter(
    "jarvis_signals_generated_total",
    "Trading signals generated",
    ["signal_type", "market"],
)

# Telegram metrics
TELEGRAM_MESSAGES = Counter(
    "jarvis_telegram_messages_total",
    "Telegram messages sent",
    ["type"],  # broadcast, individual, alert
)

# Auth metrics
AUTH_ATTEMPTS = Counter(
    "jarvis_auth_attempts_total",
    "Authentication attempts",
    ["result"],  # success, failure
)

# System info
SYSTEM_INFO = Info(
    "jarvis_system",
    "System information",
)

# Active users gauge
ACTIVE_USERS = Gauge(
    "jarvis_active_users",
    "Currently active users (last 24h)",
)

# Background task metrics
TASK_DURATION = Histogram(
    "jarvis_background_task_duration_seconds",
    "Background task execution time",
    ["task_name"],
)

TASK_ERRORS = Counter(
    "jarvis_background_task_errors_total",
    "Background task errors",
    ["task_name"],
)


# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═══════════════════════════════════════════════════════════
class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        # Normalize path to reduce cardinality
        path = self._normalize_path(request.url.path)

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        status = str(response.status_code)
        REQUEST_COUNT.labels(method=method, endpoint=path, status_code=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Reduce path cardinality for metrics."""
        parts = path.strip("/").split("/")
        normalized = []
        for i, part in enumerate(parts):
            # Replace UUIDs, IDs, and long numeric segments
            if len(part) > 20 or (part.isdigit() and len(part) > 3):
                normalized.append("{id}")
            else:
                normalized.append(part)
        result = "/" + "/".join(normalized[:4])  # Max 4 segments
        return result


# ═══════════════════════════════════════════════════════════
#  METRICS ENDPOINT
# ═══════════════════════════════════════════════════════════
async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


# ═══════════════════════════════════════════════════════════
#  DECORATORS
# ═══════════════════════════════════════════════════════════
def track_ai_request(provider: str):
    """Decorator to track AI request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            AI_REQUESTS.labels(provider=provider).inc()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                AI_LATENCY.labels(provider=provider).observe(time.time() - start)
                return result
            except Exception as e:
                AI_LATENCY.labels(provider=provider).observe(time.time() - start)
                raise
        return wrapper
    return decorator


def track_task(task_name: str):
    """Decorator to track background task metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                TASK_DURATION.labels(task_name=task_name).observe(time.time() - start)
                return result
            except Exception as e:
                TASK_ERRORS.labels(task_name=task_name).inc()
                TASK_DURATION.labels(task_name=task_name).observe(time.time() - start)
                raise
        return wrapper
    return decorator


# Initialize system info
SYSTEM_INFO.info({
    "version": "6.0",
    "platform": "JARVIS Trading",
    "python": "3.12",
})

logger.info("✅ Prometheus metrics loaded")
