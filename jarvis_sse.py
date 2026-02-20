"""
📡 JARVIS SSE — Server-Sent Events for Real-Time Signals
═══════════════════════════════════════════════════════════
Push AI signals, price alerts, and notifications to clients
in real-time without polling.
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("jarvis-sse")
IST = timezone(timedelta(hours=5, minutes=30))

router = APIRouter(prefix="/api/sse", tags=["SSE"])
sse_router = router  # alias for server.py import

# Connected clients per channel
_clients: Dict[str, Set[asyncio.Queue]] = {
    "signals": set(),
    "alerts": set(),
    "prices": set(),
    "notifications": set(),
    "admin": set(),
}

# Last events per channel (for new subscribers)
_last_events: Dict[str, Any] = {}


# ═══════════════════════════════════════════════════════════
#  SSE ENDPOINTS
# ═══════════════════════════════════════════════════════════
@router.get("/signals")
async def sse_signals(request: Request):
    """Stream AI trading signals in real-time."""
    return await _create_sse_response(request, "signals")


@router.get("/alerts")
async def sse_alerts(request: Request):
    """Stream price alerts & notifications."""
    return await _create_sse_response(request, "alerts")


@router.get("/prices")
async def sse_prices(request: Request):
    """Stream live price updates."""
    return await _create_sse_response(request, "prices")


@router.get("/notifications")
async def sse_notifications(request: Request):
    """Stream user notifications."""
    return await _create_sse_response(request, "notifications")


@router.get("/admin")
async def sse_admin(request: Request):
    """Stream admin dashboard updates."""
    return await _create_sse_response(request, "admin")


@router.get("/all")
async def sse_all(request: Request):
    """Stream all event channels."""
    return await _create_sse_response(request, "all")


async def _create_sse_response(request: Request, channel: str):
    """Create SSE response for a channel."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    # Register client
    if channel == "all":
        for ch in _clients:
            _clients[ch].add(queue)
    else:
        if channel not in _clients:
            _clients[channel] = set()
        _clients[channel].add(queue)

    async def event_generator():
        try:
            # Send last known event immediately
            if channel in _last_events:
                yield {
                    "event": channel,
                    "data": json.dumps(_last_events[channel], default=str),
                }

            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "channel": channel,
                    "time": datetime.now(IST).isoformat(),
                    "message": f"Connected to {channel} stream",
                }),
            }

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for new events with timeout for keepalive
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield {
                        "event": data.get("event", channel),
                        "data": json.dumps(data.get("data", data), default=str),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield {"event": "ping", "data": json.dumps({"time": time.time()})}

        finally:
            # Unregister client
            if channel == "all":
                for ch in _clients:
                    _clients[ch].discard(queue)
            else:
                _clients.get(channel, set()).discard(queue)

    return EventSourceResponse(event_generator())


# ═══════════════════════════════════════════════════════════
#  EVENT PUBLISHING
# ═══════════════════════════════════════════════════════════
async def publish_event(channel: str, event_type: str, data: Any):
    """Publish event to all connected SSE clients on a channel."""
    if channel not in _clients:
        _clients[channel] = set()

    event = {"event": event_type, "data": data, "time": datetime.now(IST).isoformat()}
    _last_events[channel] = event

    # Also publish to Redis for multi-instance
    try:
        from jarvis_redis_cache import publish
        publish(f"sse:{channel}", event)
    except Exception:
        pass

    # Send to all connected clients
    dead_queues = set()
    for queue in _clients[channel]:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            dead_queues.add(queue)
        except Exception:
            dead_queues.add(queue)

    # Cleanup dead connections
    for q in dead_queues:
        _clients[channel].discard(q)


def publish_event_sync(channel: str, event_type: str, data: Any):
    """Sync wrapper for publishing events (for use in non-async contexts)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(publish_event(channel, event_type, data))
        else:
            loop.run_until_complete(publish_event(channel, event_type, data))
    except Exception:
        # If no loop available, just store last event
        _last_events[channel] = {"event": event_type, "data": data}


# ═══════════════════════════════════════════════════════════
#  SIGNAL PUBLISHER — Pushes signals when confidence > threshold
# ═══════════════════════════════════════════════════════════
async def publish_signal(signal: Dict):
    """Publish a trading signal if confidence is high enough."""
    confidence = signal.get("confidence", 0)
    if confidence >= 70:  # Only push high-confidence signals
        await publish_event("signals", "new_signal", {
            "symbol": signal.get("symbol", ""),
            "signal": signal.get("signal", ""),
            "confidence": confidence,
            "price": signal.get("price", 0),
            "target": signal.get("target", 0),
            "stop_loss": signal.get("stop_loss", 0),
            "source": signal.get("source", "ai"),
            "time": datetime.now(IST).isoformat(),
        })


async def publish_price_alert(user_id: str, symbol: str, price: float, condition: str):
    """Publish price alert notification."""
    await publish_event("alerts", "price_alert", {
        "user_id": user_id,
        "symbol": symbol,
        "price": price,
        "condition": condition,
        "time": datetime.now(IST).isoformat(),
    })


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
@router.get("/stats")
async def sse_stats():
    """Get SSE connection statistics."""
    return {
        "channels": {ch: len(clients) for ch, clients in _clients.items()},
        "total_connections": sum(len(c) for c in _clients.values()),
        "last_events": {ch: ev.get("time", "") for ch, ev in _last_events.items()},
    }


SSE_AVAILABLE = True
logger.info("📡 SSE engine loaded — real-time signal streaming ready")
