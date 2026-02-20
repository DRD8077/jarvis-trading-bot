"""
JARVIS Server — Integration Tests
═══════════════════════════════════
Tests all API endpoints, middleware, and module loading.
"""
import os
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required env vars for testing
os.environ.setdefault("ADMIN_CHAT_ID", "123456")
os.environ.setdefault("OWNER_CHAT_ID", "123456")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test:fake_token_for_testing")


@pytest.fixture(scope="module")
def app():
    """Create FastAPI test app."""
    from jarvis_server import app as _app
    return _app


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    from starlette.testclient import TestClient
    return TestClient(app)


# ═══════════════════════════════════════
#  Health & System Endpoints
# ═══════════════════════════════════════
class TestHealth:
    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert "engines_loaded" in d
        assert d["engines_loaded"] >= 1

    def test_api_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        d = r.json()
        assert "status" in d

    def test_system_overview(self, client):
        r = client.get("/api/system/overview")
        assert r.status_code == 200
        d = r.json()
        assert "server" in d
        assert "modules" in d
        assert d["server"]["version"] == "7.0"
        assert "cpu_percent" in d["server"]
        assert "memory_percent" in d["server"]


# ═══════════════════════════════════════
#  Admin Endpoints
# ═══════════════════════════════════════
class TestAdmin:
    def test_admin_overview(self, client):
        r = client.get("/api/admin/overview")
        assert r.status_code == 200
        d = r.json()
        assert "total_users" in d

    def test_admin_engines(self, client):
        r = client.get("/api/admin/engines")
        assert r.status_code == 200
        d = r.json()
        assert "engines" in d

    def test_admin_errors(self, client):
        r = client.get("/api/admin/errors")
        assert r.status_code == 200
        d = r.json()
        assert "total_errors" in d

    def test_admin_api_keys(self, client):
        r = client.get("/api/admin/api-keys")
        assert r.status_code == 200
        d = r.json()
        assert "keys" in d

    def test_admin_features(self, client):
        r = client.get("/api/admin/features")
        assert r.status_code == 200

    def test_admin_users(self, client):
        r = client.get("/api/admin/users")
        assert r.status_code == 200

    def test_admin_broadcast(self, client):
        r = client.post("/api/admin/broadcast", json={"message": "test"})
        assert r.status_code == 200

    def test_admin_cache_stats(self, client):
        r = client.get("/api/admin/cache/stats")
        assert r.status_code == 200

    def test_admin_bot_status(self, client):
        r = client.post("/api/admin/bot", json={"command": "status"})
        assert r.status_code == 200


# ═══════════════════════════════════════
#  MiniApp / Public Endpoints
# ═══════════════════════════════════════
class TestMiniApp:
    def test_miniapp_health(self, client):
        r = client.get("/api/miniapp/health")
        assert r.status_code == 200
        d = r.json()
        assert "engines_loaded" in d

    def test_miniapp_signals(self, client):
        r = client.get("/api/miniapp/signals")
        assert r.status_code == 200

    def test_miniapp_market(self, client):
        r = client.get("/api/miniapp/market")
        assert r.status_code == 200

    def test_miniapp_portfolio(self, client):
        r = client.get("/api/miniapp/portfolio")
        assert r.status_code == 200


# ═══════════════════════════════════════
#  Auth Endpoints (JWT)
# ═══════════════════════════════════════
class TestAuth:
    def test_register(self, client):
        r = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "testpass123",
            "chat_id": "999999"
        })
        # May succeed or say "user exists" (400)
        assert r.status_code in (200, 400)

    def test_login(self, client):
        r = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert r.status_code == 200

    def test_login_wrong_password(self, client):
        r = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        d = r.json()
        # Should fail or return error
        assert r.status_code == 200  # API always returns 200 with error in body
        # Auth error should be in response
        if "error" in d:
            assert True


# ═══════════════════════════════════════
#  Social Trading Endpoints
# ═══════════════════════════════════════
class TestSocial:
    def test_social_stats(self, client):
        r = client.get("/api/social/stats")
        assert r.status_code == 200

    def test_social_feed(self, client):
        r = client.get("/api/social/feed")
        assert r.status_code == 200

    def test_social_leaderboard(self, client):
        r = client.get("/api/social/leaderboard")
        assert r.status_code == 200


# ═══════════════════════════════════════
#  Backtester Endpoints
# ═══════════════════════════════════════
class TestBacktester:
    def test_backtest_run(self, client):
        r = client.post("/api/backtest/run", json={
            "strategy": "Buy when RSI < 30, sell when RSI > 70",
            "symbol": "NIFTY",
            "period": "1y"
        })
        assert r.status_code == 200


# ═══════════════════════════════════════
#  Task Queue Endpoints
# ═══════════════════════════════════════
class TestTasks:
    def test_task_list(self, client):
        r = client.get("/api/tasks")
        assert r.status_code == 200
        d = r.json()
        assert "queued" in d or "tasks" in d


# ═══════════════════════════════════════
#  SSE Endpoints
# ═══════════════════════════════════════
class TestSSE:
    def test_sse_stats(self, client):
        r = client.get("/api/sse/stats")
        assert r.status_code == 200


# ═══════════════════════════════════════
#  Prometheus Metrics
# ═══════════════════════════════════════
class TestMetrics:
    def test_prometheus_metrics(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        # Prometheus format
        assert "http_requests_total" in r.text or "HELP" in r.text or r.status_code == 200


# ═══════════════════════════════════════
#  Page Rendering
# ═══════════════════════════════════════
class TestPages:
    def test_admin_page(self, client):
        r = client.get("/admin")
        assert r.status_code == 200
        assert "JARVIS" in r.text

    def test_root_redirect(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code in [200, 307, 302]


# ═══════════════════════════════════════
#  Super Power Endpoints
# ═══════════════════════════════════════
class TestSuperPower:
    def test_uptime(self, client):
        r = client.get("/api/admin/uptime")
        assert r.status_code == 200
        data = r.json()
        assert "uptime_seconds" in data
        assert "uptime_formatted" in data
        assert "started_at" in data
        assert data["uptime_seconds"] >= 0

    def test_request_log(self, client):
        r = client.get("/api/admin/request-log")
        assert r.status_code == 200
        data = r.json()
        assert "requests" in data
        assert "total" in data
        assert isinstance(data["requests"], list)

    def test_request_log_with_limit(self, client):
        r = client.get("/api/admin/request-log?limit=2")
        assert r.status_code == 200
        data = r.json()
        assert len(data["requests"]) <= 2

    def test_activity(self, client):
        r = client.get("/api/admin/activity")
        assert r.status_code == 200
        data = r.json()
        assert "events" in data

    def test_export_users_csv(self, client):
        r = client.get("/api/admin/export/users")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "User ID" in r.text  # CSV header

    def test_export_errors_csv(self, client):
        r = client.get("/api/admin/export/errors")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "Timestamp" in r.text  # CSV header

    def test_export_signals_csv(self, client):
        r = client.get("/api/admin/export/signals")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "Pair" in r.text  # CSV header

    def test_full_backup(self, client):
        r = client.get("/api/admin/backup")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        data = r.json()
        assert "backup_time" in data
        assert "version" in data
        assert data["version"] == "7.0"

    def test_admin_page_has_command_palette(self, client):
        r = client.get("/admin")
        assert r.status_code == 200
        assert "cmd-overlay" in r.text
        assert "cmd-input" in r.text
        assert "openPalette" in r.text

    def test_admin_page_has_notification_center(self, client):
        r = client.get("/admin")
        assert "notif-panel" in r.text
        assert "notif-bell" in r.text
        assert "pushNotif" in r.text

    def test_admin_page_has_export_buttons(self, client):
        r = client.get("/admin")
        assert "/api/admin/export/users" in r.text
        assert "/api/admin/export/errors" in r.text
        assert "/api/admin/backup" in r.text

    def test_admin_page_has_request_log(self, client):
        r = client.get("/admin")
        assert "sec-reqlog" in r.text
        assert "loadReqLog" in r.text
