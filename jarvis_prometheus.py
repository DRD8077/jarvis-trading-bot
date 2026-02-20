"""
📊 JARVIS Prometheus Metrics — Observability & Monitoring
═══════════════════════════════════════════════════════════
Tracks:
- API request latency & count
- Cache hit rates
- Engine health
- WebSocket connections
- Background task stats
"""

import time
import logging
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("jarvis-metrics")

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info, generate_latest,
        CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY,
    )
    PROM_AVAILABLE = True
except ImportError:
    PROM_AVAILABLE = False
    logger.warning("prometheus_client not installed")


# ═══════════════════════════════════════════════════════════
#  METRICS DEFINITIONS
# ═══════════════════════════════════════════════════════════
if PROM_AVAILABLE:
    # Request metrics
    REQUEST_COUNT = Counter(
        "jarvis_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "jarvis_http_request_duration_seconds",
        "Request latency in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Cache metrics
    CACHE_HITS = Counter("jarvis_cache_hits_total", "Cache hits")
    CACHE_MISSES = Counter("jarvis_cache_misses_total", "Cache misses")
    CACHE_SIZE = Gauge("jarvis_cache_keys", "Number of cache keys")

    # WebSocket metrics
    WS_CONNECTIONS = Gauge("jarvis_ws_connections", "Active WebSocket connections")
    SSE_CONNECTIONS = Gauge("jarvis_sse_connections", "Active SSE connections", ["channel"])

    # Engine metrics
    ENGINES_LOADED = Gauge("jarvis_engines_loaded", "Number of loaded engines")
    ENGINE_STATUS = Info("jarvis_engine", "Engine status info")

    # Task queue metrics
    TASKS_QUEUED = Counter("jarvis_tasks_queued_total", "Total tasks queued", ["task_name"])
    TASKS_COMPLETED = Counter("jarvis_tasks_completed_total", "Completed tasks", ["task_name", "status"])
    TASKS_DURATION = Histogram(
        "jarvis_task_duration_seconds", "Task execution time",
        ["task_name"],
        buckets=[0.1, 0.5, 1.0, 5.0, 15.0, 30.0, 60.0, 120.0],
    )

    # Business metrics
    ACTIVE_USERS = Gauge("jarvis_active_users", "Active users in last hour")
    SIGNALS_GENERATED = Counter("jarvis_signals_total", "Trading signals generated", ["signal_type"])
    AI_REQUESTS = Counter("jarvis_ai_requests_total", "AI chat requests", ["provider"])


# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE — Auto-track request metrics
# ═══════════════════════════════════════════════════════════
class PrometheusMiddleware(BaseHTTPMiddleware):
    """Automatically track HTTP request metrics."""

    async def dispatch(self, request: Request, call_next):
        if not PROM_AVAILABLE:
            return await call_next(request)

        path = request.url.path
        # Normalize path to avoid high cardinality
        endpoint = _normalize_path(path)
        method = request.method

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

        return response


def _normalize_path(path: str) -> str:
    """Normalize URL path to prevent high-cardinality metrics."""
    # Group dynamic segments
    parts = path.strip("/").split("/")
    normalized = []
    for i, part in enumerate(parts):
        if part.isdigit() or len(part) > 30:
            normalized.append("{id}")
        else:
            normalized.append(part)
    result = "/" + "/".join(normalized[:4])  # Limit depth
    return result


# ═══════════════════════════════════════════════════════════
#  METRICS ENDPOINT
# ═══════════════════════════════════════════════════════════
async def metrics_endpoint(request: Request):
    """Prometheus /metrics endpoint."""
    if not PROM_AVAILABLE:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("# Prometheus client not available\n", status_code=503)

    # Update gauge metrics before serving
    _update_gauges()

    from fastapi.responses import Response as FastResponse
    return FastResponse(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


def _update_gauges():
    """Update gauge values from current state."""
    if not PROM_AVAILABLE:
        return
    try:
        from jarvis_redis_cache import cache_stats
        stats = cache_stats()
        CACHE_SIZE.set(stats.get("keys", 0))
    except Exception:
        pass

    try:
        from jarvis_sse import _clients
        for ch, clients in _clients.items():
            SSE_CONNECTIONS.labels(channel=ch).set(len(clients))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS — For use in other modules
# ═══════════════════════════════════════════════════════════
def track_cache_hit():
    if PROM_AVAILABLE:
        CACHE_HITS.inc()


def track_cache_miss():
    if PROM_AVAILABLE:
        CACHE_MISSES.inc()


def track_ws_connect():
    if PROM_AVAILABLE:
        WS_CONNECTIONS.inc()


def track_ws_disconnect():
    if PROM_AVAILABLE:
        WS_CONNECTIONS.dec()


def track_signal(signal_type: str):
    if PROM_AVAILABLE:
        SIGNALS_GENERATED.labels(signal_type=signal_type).inc()


def track_ai_request(provider: str):
    if PROM_AVAILABLE:
        AI_REQUESTS.labels(provider=provider).inc()


def track_task_queued(task_name: str):
    if PROM_AVAILABLE:
        TASKS_QUEUED.labels(task_name=task_name).inc()


def track_task_completed(task_name: str, status: str, duration: float):
    if PROM_AVAILABLE:
        TASKS_COMPLETED.labels(task_name=task_name, status=status).inc()
        TASKS_DURATION.labels(task_name=task_name).observe(duration)


def get_metrics_summary() -> Dict:
    """Get a JSON summary of key metrics (for admin dashboard)."""
    summary = {"prometheus_available": PROM_AVAILABLE}
    if PROM_AVAILABLE:
        try:
            summary["total_requests"] = sum(
                sample.value
                for metric in REQUEST_COUNT.collect()
                for sample in metric.samples
                if sample.name.endswith("_total")
            )
        except Exception:
            summary["total_requests"] = 0
        try:
            summary["cache_hits"] = CACHE_HITS._value.get()
            summary["cache_misses"] = CACHE_MISSES._value.get()
        except Exception:
            pass
    return summary


PROMETHEUS_AVAILABLE = PROM_AVAILABLE

# Router for /metrics endpoint
try:
    from fastapi import APIRouter
    from fastapi.responses import PlainTextResponse
    metrics_router = APIRouter(tags=["metrics"])

    @metrics_router.get("/metrics")
    async def prometheus_metrics():
        if PROM_AVAILABLE:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        return PlainTextResponse("# Prometheus not available", media_type="text/plain")
except ImportError:
    metrics_router = None

logger.info(f"📊 Prometheus metrics loaded — available={PROM_AVAILABLE}")
