"""
JARVIS Module — Unit Tests
═══════════════════════════
Tests individual backend modules in isolation.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ADMIN_CHAT_ID", "123456")
os.environ.setdefault("OWNER_CHAT_ID", "123456")


# ═══════════════════════════════════════
#  Error Handler
# ═══════════════════════════════════════
class TestErrorHandler:
    def test_import(self):
        import jarvis_error_handler as eh
        assert hasattr(eh, "log_error")
        assert hasattr(eh, "get_error_summary")
        assert hasattr(eh, "get_recent_errors")

    def test_log_and_retrieve(self):
        from jarvis_error_handler import log_error, get_error_summary, get_recent_errors
        log_error(category="test", message="Test error", module="test_module", severity="warning")
        summary = get_error_summary()
        assert "total_errors" in summary
        assert summary["total_errors"] >= 1

    def test_engine_health_tracking(self):
        from jarvis_error_handler import get_engine_health
        health = get_engine_health()
        assert isinstance(health, dict)


# ═══════════════════════════════════════
#  Redis Cache (Memory Fallback)
# ═══════════════════════════════════════
class TestRedisCache:
    def test_import(self):
        import jarvis_redis_cache as rc
        assert hasattr(rc, "cache_get")
        assert hasattr(rc, "cache_set")

    def test_set_and_get(self):
        from jarvis_redis_cache import cache_set, cache_get
        cache_set("test_key", "test_value", ttl=60)
        val = cache_get("test_key")
        assert val == "test_value"

    def test_get_missing_key(self):
        from jarvis_redis_cache import cache_get
        val = cache_get("nonexistent_key_xyz")
        assert val is None

    def test_cache_stats(self):
        from jarvis_redis_cache import cache_stats
        stats = cache_stats()
        assert "backend" in stats


# ═══════════════════════════════════════
#  JWT Auth
# ═══════════════════════════════════════
class TestJWTAuth:
    def test_import(self):
        try:
            import jarvis_jwt_auth as auth
            assert hasattr(auth, "register_user") or hasattr(auth, "login_user")
        except ImportError:
            pytest.skip("JWT dependencies not installed")

    def test_register_and_login(self):
        try:
            from jarvis_jwt_auth import register_user, login_user
            success, result = register_user("unit_test_user", "Unit Test", password="test1234")
            assert success or "already" in str(result)

            login_ok, login_data = login_user("unit_test_user", "test1234")
            if login_ok and "access_token" in login_data:
                assert len(login_data["access_token"]) > 10
        except (ImportError, ValueError):
            pytest.skip("JWT/bcrypt dependencies issue")


# ═══════════════════════════════════════
#  Rate Limiter
# ═══════════════════════════════════════
class TestRateLimiter:
    def test_import(self):
        import jarvis_rate_limiter as rl
        assert hasattr(rl, "UserRateLimitMiddleware") or hasattr(rl, "RateLimiterMiddleware")


# ═══════════════════════════════════════
#  SSE Engine
# ═══════════════════════════════════════
class TestSSE:
    def test_import(self):
        try:
            import jarvis_sse as sse
            assert hasattr(sse, "publish_event_sync") or hasattr(sse, "push_event")
        except ImportError:
            pytest.skip("SSE dependencies not installed")


# ═══════════════════════════════════════
#  Task Queue
# ═══════════════════════════════════════
class TestTaskQueue:
    def test_import(self):
        import jarvis_tasks as tq
        assert hasattr(tq, "submit_task") or hasattr(tq, "get_task_status")

    def test_submit_task(self):
        from jarvis_tasks import submit_task, get_task_status
        task_id = submit_task("backtest", {"symbol": "NIFTY", "strategy": "RSI"})
        assert task_id is not None
        status = get_task_status(task_id)
        assert "status" in status


# ═══════════════════════════════════════
#  Social Trading
# ═══════════════════════════════════════
class TestSocialTrading:
    def test_import(self):
        import jarvis_social as soc
        assert hasattr(soc, "share_signal") or hasattr(soc, "get_social_stats")

    def test_stats(self):
        from jarvis_social import get_social_stats
        stats = get_social_stats()
        assert "total_signals" in stats
        assert "total_traders" in stats


# ═══════════════════════════════════════
#  Notifications
# ═══════════════════════════════════════
class TestNotifications:
    def test_import(self):
        import jarvis_notifications as notif
        assert hasattr(notif, "subscribe") or hasattr(notif, "get_notification_stats")


# ═══════════════════════════════════════
#  Database
# ═══════════════════════════════════════
class TestDatabase:
    def test_import(self):
        import jarvis_database as db
        assert hasattr(db, "init_db") or hasattr(db, "get_user")


# ═══════════════════════════════════════
#  Prometheus
# ═══════════════════════════════════════
class TestPrometheus:
    def test_import(self):
        import jarvis_prometheus as prom
        assert hasattr(prom, "PrometheusMiddleware") or hasattr(prom, "metrics_router")


# ═══════════════════════════════════════
#  Birdeye & DexTools
# ═══════════════════════════════════════
class TestExternalEngines:
    def test_birdeye_import(self):
        import jarvis_birdeye as be
        assert hasattr(be, "get_token_info") or hasattr(be, "BIRDEYE_AVAILABLE")

    def test_dextools_import(self):
        import jarvis_dextools as dt
        assert hasattr(dt, "get_hot_pairs") or hasattr(dt, "get_trending")

    def test_backtester_import(self):
        import jarvis_backtester_pro as bt
        assert hasattr(bt, "run_backtest") or hasattr(bt, "BacktesterPro")
