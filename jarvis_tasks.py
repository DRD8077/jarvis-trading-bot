"""
⚙️ JARVIS Background Tasks — ARQ Task Queue
═══════════════════════════════════════════════
Offload heavy tasks from the FastAPI event loop:
- Backtesting strategies
- AI analysis / deep scans
- Report generation
- Data aggregation
- Scheduled alerts
"""

import os
import json
import time
import logging
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("jarvis-tasks")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  TASK QUEUE — Using asyncio.Queue + background workers
#  (ARQ-compatible interface, works without Redis worker)
# ═══════════════════════════════════════════════════════════
_task_queue: asyncio.Queue = None
_task_results: Dict[str, Any] = {}
_task_status: Dict[str, str] = {}
_workers_running = False
NUM_WORKERS = 3


def _get_queue():
    global _task_queue
    if _task_queue is None:
        _task_queue = asyncio.Queue(maxsize=500)
    return _task_queue


# ═══════════════════════════════════════════════════════════
#  TASK REGISTRY
# ═══════════════════════════════════════════════════════════
_task_handlers: Dict[str, Any] = {}


def register_task(name: str):
    """Decorator to register an async task handler."""
    def decorator(fn):
        _task_handlers[name] = fn
        return fn
    return decorator


# ═══════════════════════════════════════════════════════════
#  BUILT-IN TASKS
# ═══════════════════════════════════════════════════════════
@register_task("backtest")
async def task_backtest(params: Dict) -> Dict:
    """Run backtesting strategy in background."""
    try:
        from jarvis_backtester_pro import (
            parse_strategy_from_text, run_backtest, BACKTESTER_AVAILABLE
        )
        if not BACKTESTER_AVAILABLE:
            return {"error": "Backtester not available (yfinance missing)"}

        symbol = params.get("symbol", "RELIANCE.NS")
        strategy_text = params.get("strategy", "RSI < 30 pe buy, RSI > 70 pe sell")
        capital = params.get("capital", 100000)
        period = params.get("period", "1y")

        strategy = parse_strategy_from_text(strategy_text)
        result = run_backtest(symbol, strategy, capital=capital, period=period)
        return result or {"error": "Backtest returned no results"}
    except Exception as e:
        return {"error": f"Backtest failed: {str(e)}"}


@register_task("deep_analysis")
async def task_deep_analysis(params: Dict) -> Dict:
    """Deep AI analysis of a token/stock."""
    try:
        symbol = params.get("symbol", "BTC")
        analysis_type = params.get("type", "crypto")

        results = {}

        # DexScreener data
        try:
            from dex_engine import dex_search
            dex_data = await dex_search(symbol, limit=5)
            results["dex_data"] = dex_data[:3]
        except Exception:
            pass

        # AI signals
        try:
            from ai_signals import full_technical_analysis
            ta = await asyncio.to_thread(full_technical_analysis, symbol)
            results["technical"] = ta
        except Exception:
            pass

        # Rug check (crypto)
        if analysis_type == "crypto":
            try:
                from rug_detector import analyze_rug_risk
                rug = await asyncio.to_thread(analyze_rug_risk, symbol)
                results["rug_check"] = rug
            except Exception:
                pass

        results["symbol"] = symbol
        results["type"] = analysis_type
        results["timestamp"] = datetime.now(IST).isoformat()
        return results
    except Exception as e:
        return {"error": str(e)}


@register_task("generate_report")
async def task_generate_report(params: Dict) -> Dict:
    """Generate a comprehensive portfolio/market report."""
    try:
        report_type = params.get("type", "market")
        results = {"type": report_type, "generated_at": datetime.now(IST).isoformat()}

        if report_type == "market":
            try:
                from dex_engine import get_full_market_snapshot
                snapshot = await get_full_market_snapshot()
                results["snapshot"] = snapshot
            except Exception:
                pass

        elif report_type == "portfolio":
            user_id = params.get("user_id", "0")
            try:
                from portfolio_tracker import get_portfolio, calculate_portfolio_pnl
                portfolio = get_portfolio(user_id)
                pnl = calculate_portfolio_pnl(user_id)
                results["portfolio"] = portfolio
                results["pnl"] = pnl
            except Exception:
                pass

        return results
    except Exception as e:
        return {"error": str(e)}


@register_task("scan_signals")
async def task_scan_signals(params: Dict) -> Dict:
    """Batch scan for trading signals."""
    try:
        from ai_signals import batch_signals
        market = params.get("market", "crypto")
        signals = await asyncio.to_thread(batch_signals, market)
        
        # Publish high-confidence signals via SSE
        try:
            from jarvis_sse import publish_signal
            for sig in (signals or []):
                if sig.get("confidence", 0) >= 80:
                    await publish_signal(sig)
        except Exception:
            pass

        return {"signals": signals, "count": len(signals or []), "market": market}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  QUEUE OPERATIONS
# ═══════════════════════════════════════════════════════════
async def enqueue_task(task_name: str, params: Dict = None, task_id: str = None) -> str:
    """Add a task to the queue. Returns task ID."""
    import secrets
    tid = task_id or f"{task_name}_{secrets.token_hex(6)}"
    _task_status[tid] = "queued"
    _task_results[tid] = None

    queue = _get_queue()
    await queue.put({"id": tid, "task": task_name, "params": params or {}, "queued_at": time.time()})

    logger.info(f"📋 Task queued: {tid} ({task_name})")
    return tid


def get_task_status(task_id: str) -> Dict:
    """Get status and result of a task."""
    status = _task_status.get(task_id, "not_found")
    result = _task_results.get(task_id)
    return {
        "task_id": task_id,
        "status": status,
        "result": result,
        "completed": status == "completed",
    }


def get_all_tasks() -> list:
    """Get all task statuses."""
    return [
        {"task_id": tid, "status": status, "has_result": tid in _task_results and _task_results[tid] is not None}
        for tid, status in _task_status.items()
    ]


def task_stats() -> Dict:
    """Return task queue statistics."""
    statuses = list(_task_status.values())
    return {
        "total": len(statuses),
        "pending": statuses.count("pending"),
        "running": statuses.count("running"),
        "completed": statuses.count("completed"),
        "failed": statuses.count("failed"),
        "workers": NUM_WORKERS if _workers_running else 0,
        "registered_tasks": list(_task_handlers.keys()),
    }


# ═══════════════════════════════════════════════════════════
#  WORKER
# ═══════════════════════════════════════════════════════════
async def _worker(worker_id: int):
    """Background worker that processes tasks from the queue."""
    queue = _get_queue()
    logger.info(f"  🔧 Worker {worker_id} started")
    while True:
        try:
            item = await queue.get()
            tid = item["id"]
            task_name = item["task"]
            params = item["params"]

            _task_status[tid] = "running"
            logger.info(f"  ⚙️ Worker {worker_id} processing: {tid}")

            handler = _task_handlers.get(task_name)
            if handler:
                try:
                    result = await asyncio.wait_for(handler(params), timeout=120)
                    _task_results[tid] = result
                    _task_status[tid] = "completed"
                    logger.info(f"  ✅ Task completed: {tid}")
                except asyncio.TimeoutError:
                    _task_results[tid] = {"error": "Task timed out (120s)"}
                    _task_status[tid] = "timeout"
                except Exception as e:
                    _task_results[tid] = {"error": str(e)}
                    _task_status[tid] = "failed"
                    logger.error(f"  ❌ Task failed: {tid} — {e}")
            else:
                _task_results[tid] = {"error": f"Unknown task: {task_name}"}
                _task_status[tid] = "failed"

            queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            await asyncio.sleep(1)


async def start_workers():
    """Start background workers. Call from server lifespan."""
    global _workers_running
    if _workers_running:
        return []
    _workers_running = True
    tasks = []
    for i in range(NUM_WORKERS):
        task = asyncio.create_task(_worker(i))
        tasks.append(task)
    logger.info(f"⚙️ {NUM_WORKERS} background workers started")
    return tasks


async def stop_workers(worker_tasks: list):
    """Stop all workers."""
    global _workers_running
    _workers_running = False
    for task in worker_tasks:
        task.cancel()
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    logger.info("⚙️ Workers stopped")


# ═══════════════════════════════════════════════════════════
#  SCHEDULED TASKS
# ═══════════════════════════════════════════════════════════
async def signal_scan_loop():
    """Periodic signal scanning — runs every 5 minutes."""
    while True:
        try:
            await asyncio.sleep(300)
            await enqueue_task("scan_signals", {"market": "crypto"})
            logger.debug("📡 Scheduled signal scan enqueued")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Signal scan loop error: {e}")
            await asyncio.sleep(60)


# ═══════════════════════════════════════════════════════════
#  SYNC WRAPPERS & COMPATIBILITY
# ═══════════════════════════════════════════════════════════
def submit_task(task_name: str, params: Dict = None) -> str:
    """Sync wrapper to submit a task (used by server endpoints)."""
    import secrets
    tid = f"{task_name}_{secrets.token_hex(6)}"
    _task_status[tid] = "queued"
    _task_results[tid] = None

    # Try to enqueue via event loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(enqueue_task(task_name, params, tid))
    except RuntimeError:
        # No running loop — store for later processing
        _task_status[tid] = "pending"

    return tid


def get_queue_stats() -> Dict:
    """Get queue stats for the API."""
    stats = task_stats()
    recent = []
    for tid, status in list(_task_status.items())[-20:]:
        task_type = tid.rsplit("_", 1)[0] if "_" in tid else tid
        recent.append({
            "task_id": tid,
            "task_type": task_type,
            "status": status,
            "created_at": datetime.now(IST).strftime("%H:%M:%S"),
        })
    return {
        "queued": stats.get("pending", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "workers": stats.get("workers", 0),
        "registered_tasks": stats.get("registered_tasks", []),
        "recent": recent,
    }


# ═══════════════════════════════════════════════════════════
#  FASTAPI ROUTER
# ═══════════════════════════════════════════════════════════
try:
    from fastapi import APIRouter
    task_router = APIRouter(prefix="/api/tasks", tags=["tasks"])

    @task_router.post("/submit")
    async def api_submit_task(request_data: dict):
        task_name = request_data.get("task", "")
        params = request_data.get("params", {})
        if task_name not in _task_handlers:
            return {"error": f"Unknown task: {task_name}", "available": list(_task_handlers.keys())}
        tid = await enqueue_task(task_name, params)
        return {"task_id": tid, "status": "queued"}

    @task_router.get("/status/{task_id}")
    async def api_task_status(task_id: str):
        return get_task_status(task_id)

    @task_router.get("/list")
    async def api_task_list():
        return {"tasks": get_all_tasks()}

    @task_router.get("/stats")
    async def api_task_stats():
        return get_queue_stats()

except ImportError:
    task_router = None

TASKS_AVAILABLE = True
logger.info("⚙️ Task queue engine loaded — %d registered tasks", len(_task_handlers))
