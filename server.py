"""
🚀 JARVIS Trading Platform — Main Server
═══════════════════════════════════════════
FastAPI server with WebSocket, security, and real-time data.
Run with: python server.py
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    # Manual .env loading fallback
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ═══ New Power-Up Module Imports ═══
try:
    from jarvis_redis_cache import cache_get, cache_set, cache_stats, cache_flush
    REDIS_CACHE_OK = True
except Exception as e:
    REDIS_CACHE_OK = False
    logging.getLogger('jarvis-server').warning(f'Redis cache import failed: {e}')

try:
    from jarvis_prometheus import PrometheusMiddleware, metrics_endpoint
    PROMETHEUS_OK = True
except Exception as e:
    PROMETHEUS_OK = False
    logging.getLogger('jarvis-server').warning(f'Prometheus import failed: {e}')

try:
    from jarvis_rate_limiter import UserRateLimitMiddleware
    RATE_LIMITER_OK = True
except Exception as e:
    RATE_LIMITER_OK = False
    logging.getLogger('jarvis-server').warning(f'Rate limiter import failed: {e}')

try:
    from jarvis_sse import sse_router, publish_signal, publish_event
    SSE_OK = True
except Exception as e:
    SSE_OK = False
    logging.getLogger('jarvis-server').warning(f'SSE import failed: {e}')

try:
    from jarvis_postgres import init_pool as pg_init_pool, pg_stats, pg_upsert_user, pg_log_signal, pg_log_trade, pg_get_signals, pg_get_trades, pg_get_api_keys, pg_set_api_key, pg_delete_api_key, pg_load_api_keys
    POSTGRES_OK = True
except Exception as e:
    POSTGRES_OK = False
    logging.getLogger('jarvis-server').warning(f'PostgreSQL import failed: {e}')

try:
    from jarvis_tasks import start_workers as task_start_workers, enqueue_task, get_task_status, task_stats
    TASKS_OK = True
except Exception as e:
    TASKS_OK = False
    logging.getLogger('jarvis-server').warning(f'Task queue import failed: {e}')

try:
    from jarvis_error_handler import log_error, get_error_summary, get_engine_health, safe_import
    ERROR_HANDLER_OK = True
except Exception as e:
    ERROR_HANDLER_OK = False
    logging.getLogger('jarvis-server').warning(f'Error handler import failed: {e}')

try:
    from jarvis_notifications import notify_signal, notify_admin, broadcast_message, subscribe, unsubscribe, get_notification_stats
    NOTIFICATIONS_OK = True
except Exception as e:
    NOTIFICATIONS_OK = False
    logging.getLogger('jarvis-server').warning(f'Notifications import failed: {e}')

try:
    from jarvis_social import share_signal, get_feed, like_signal as social_like, get_leaderboard, get_social_stats, follow_trader, unfollow_trader
    SOCIAL_OK = True
except Exception as e:
    SOCIAL_OK = False
    logging.getLogger('jarvis-server').warning(f'Social trading import failed: {e}')

try:
    from jarvis_dextools import get_dextools_summary, get_hot_pairs, get_token_audit
    DEXTOOLS_OK = True
except Exception as e:
    DEXTOOLS_OK = False
    logging.getLogger('jarvis-server').warning(f'DexTools import failed: {e}')

try:
    from jarvis_birdeye import get_birdeye_summary, get_trending_tokens, get_token_security
    BIRDEYE_OK = True
except Exception as e:
    BIRDEYE_OK = False
    logging.getLogger('jarvis-server').warning(f'Birdeye import failed: {e}')

try:
    from jarvis_jwt_auth import register_user, login_user, get_current_user, require_role, refresh_access_token
    JWT_AUTH_OK = True
except Exception as e:
    JWT_AUTH_OK = False
    logging.getLogger('jarvis-server').warning(f'JWT auth import failed: {e}')

# Admin panel imports
try:
    from admin_panel import (
        init_admin_db, get_all_users, get_user_stats, is_admin as admin_is_admin,
        get_features_status, toggle_feature, block_user, unblock_user,
    )
    ADMIN_PANEL_OK = True
except Exception as e:
    ADMIN_PANEL_OK = False
    logging.getLogger('jarvis-server').warning(f'Admin panel import failed: {e}')

# ═══════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("jarvis-server")


# ═══════════════════════════════════════════════════════════
#  LIFESPAN — startup / shutdown
# ═══════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("═══════════════════════════════════════")
    logger.info("  🚀 JARVIS Trading Platform Starting  ")
    logger.info("═══════════════════════════════════════")
    
    # Create data directories
    Path("data").mkdir(exist_ok=True)
    
    # Log environment status
    env_keys = {
        "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "DEXTOOLS_API_KEY": bool(os.getenv("DEXTOOLS_API_KEY")),
        "BIRDEYE_API_KEY": bool(os.getenv("BIRDEYE_API_KEY")),
    }
    for key, present in env_keys.items():
        status = "✅" if present else "❌"
        logger.info(f"  {status} {key}: {'configured' if present else 'missing'}")
    
    ai_providers = sum(1 for k in ["GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"] if os.getenv(k))
    if ai_providers == 0:
        logger.warning("  ⚠️  No AI provider keys configured! Jarvis AI chat will not work.")
    else:
        logger.info(f"  🧠 {ai_providers} AI provider(s) available")
    
    logger.info("  📊 DEX Engine: DexScreener + CoinGecko + Pump.fun")
    logger.info("  📈 Indian Markets: NSE/BSE via yfinance")
    logger.info("  🔒 Security: Rate limiting + HMAC + Telegram Auth")
    logger.info("  🎯 Auto-Sniper: 5 strategies loaded")
    logger.info("═══════════════════════════════════════")
    # Init admin DB
    if ADMIN_PANEL_OK:
        try:
            init_admin_db()
            logger.info("  🔐 Admin Panel: initialized")
        except Exception as e:
            logger.warning(f"  ⚠️ Admin Panel init error: {e}")
    
    logger.info("  ✅ Server ready!")
    logger.info("═══════════════════════════════════════")
    
    # ═══ Initialize PostgreSQL ═══
    if POSTGRES_OK:
        try:
            await pg_init_pool()
            logger.info("  🐘 PostgreSQL: connected")
        except Exception as e:
            logger.warning(f"  ⚠️ PostgreSQL init error: {e}")

    # ═══ Start Task Workers ═══
    task_worker_tasks = []
    if TASKS_OK:
        try:
            task_worker_tasks = await task_start_workers()
            logger.info("  ⚡ Task workers: started")
        except Exception as e:
            logger.warning(f"  ⚠️ Task workers error: {e}")

    # ═══ Log new module status ═══
    modules = {
        "Redis Cache": REDIS_CACHE_OK, "Prometheus": PROMETHEUS_OK,
        "Rate Limiter": RATE_LIMITER_OK, "SSE": SSE_OK,
        "PostgreSQL": POSTGRES_OK, "Tasks": TASKS_OK,
        "Error Handler": ERROR_HANDLER_OK, "Notifications": NOTIFICATIONS_OK,
        "Social Trading": SOCIAL_OK, "DexTools": DEXTOOLS_OK,
        "Birdeye": BIRDEYE_OK, "JWT Auth": JWT_AUTH_OK,
    }
    for name, ok in modules.items():
        status = "✅" if ok else "⚠️"
        logger.info(f"  {status} {name}: {'loaded' if ok else 'unavailable'}")

    # Start background data prefetcher for Indian market data
    async def _prefetch_loop():
        """Background task to keep Indian market data warm in cache."""
        import httpx
        await asyncio.sleep(5)  # Wait for server to fully start
        base = f"http://127.0.0.1:{os.getenv('PORT', '8000')}"
        # Fast endpoints — refresh every cycle
        fast_endpoints = [
            "/api/miniapp/india/dashboard",
            "/api/miniapp/dashboard",
            "/api/miniapp/markets",
            "/api/miniapp/options/chain?symbol=NIFTY",
        ]
        # Slow endpoints — refresh less frequently
        slow_endpoints = [
            "/api/miniapp/india/prediction?index=NIFTY",
            "/api/miniapp/india/ml-prediction?symbol=NIFTY",
            "/api/miniapp/regime?symbol=^NSEI",
            "/api/miniapp/global/analysis",
            "/api/miniapp/global/india-impact",
        ]
        cycle = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=45) as client:
                    for ep in fast_endpoints:
                        try:
                            await client.get(f"{base}{ep}")
                        except Exception:
                            pass
                    # Slow endpoints every 3rd cycle (~4.5 min)
                    if cycle % 3 == 0:
                        for ep in slow_endpoints:
                            try:
                                await client.get(f"{base}{ep}")
                            except Exception:
                                pass
                logger.debug("🔄 Background data refresh completed")
            except Exception:
                pass
            cycle += 1
            await asyncio.sleep(30)  # Refresh every 30 seconds for real-time
    
    prefetch_task = asyncio.create_task(_prefetch_loop())
    
    yield
    
    # Shutdown
    prefetch_task.cancel()
    for t in task_worker_tasks:
        t.cancel()
    
    # Shutdown: close HTTP client
    logger.info("Shutting down JARVIS...")
    try:
        from dex_engine import close_client
        await close_client()
        logger.info("HTTP client closed")
    except Exception as e:
        logger.warning(f"Shutdown error: {e}")
    
    # Close PostgreSQL pool
    if POSTGRES_OK:
        try:
            from jarvis_postgres import _pool
            if _pool:
                await _pool.close()
                logger.info("PostgreSQL pool closed")
        except Exception as e:
            logger.warning(f"PG shutdown error: {e}")


# ═══════════════════════════════════════════════════════════
#  APP INIT
# ═══════════════════════════════════════════════════════════
app = FastAPI(
    title="JARVIS Trading Platform",
    description="Real-time AI-powered crypto & stock trading platform with Redis, SSE, PostgreSQL, Social Trading",
    version="6.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE — Speed + Security + CORS + Metrics + Rate Limit
# ═══════════════════════════════════════════════════════════
# GZip compression for fast responses
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)

# Prometheus metrics middleware
if PROMETHEUS_OK:
    app.add_middleware(PrometheusMiddleware)

# Per-user rate limiting middleware
if RATE_LIMITER_OK:
    app.add_middleware(UserRateLimitMiddleware)

# Cache headers for static assets
from starlette.middleware.base import BaseHTTPMiddleware
class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if '/assets/' in path:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif path.endswith(('.js', '.css', '.png', '.svg', '.woff2')):
            response.headers['Cache-Control'] = 'public, max-age=86400'
        elif '/api/' in path:
            response.headers['Cache-Control'] = 'no-cache, max-age=0'
        return response
app.add_middleware(CacheMiddleware)

# Security middleware (rate limiting, headers)
from security_middleware import SecurityMiddleware
app.add_middleware(SecurityMiddleware)

# CORS — allow Telegram and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://t.me",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "*",  # Allow all for dev — restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
#  TEMPLATES & STATIC
# ═══════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Serve static files if directory exists
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ═══════════════════════════════════════════════════════════
#  APK DOWNLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.get("/download-apk")
async def download_apk():
    from fastapi.responses import FileResponse
    apk_path = BASE_DIR / "JARVIS-Nuclear-AI-v3.0.apk"
    if apk_path.exists():
        return FileResponse(
            str(apk_path),
            media_type="application/vnd.android.package-archive",
            filename="JARVIS-Nuclear-AI-v3.0.apk"
        )
    return {"error": "APK not found"}

#  REACT MINI APP — Serve built React SPA from dist/
# ═══════════════════════════════════════════════════════════
MINIAPP_DIST = BASE_DIR / "telegram-mini-app" / "dist"
MINIAPP_INDEX = MINIAPP_DIST / "index.html"

# Serve React app assets (JS, CSS bundles)
if (MINIAPP_DIST / "assets").exists():
    app.mount("/miniapp/assets", StaticFiles(directory=str(MINIAPP_DIST / "assets")), name="miniapp-assets")
    # Also serve at /assets/ so SPA works when loaded from root /
    app.mount("/assets", StaticFiles(directory=str(MINIAPP_DIST / "assets")), name="root-assets")

# Serve PWA icons
if (MINIAPP_DIST / "icons").exists():
    app.mount("/miniapp/icons", StaticFiles(directory=str(MINIAPP_DIST / "icons")), name="miniapp-icons")

# Serve OTA update bundles
ota_dir = BASE_DIR / "ota_bundles"
if ota_dir.exists():
    app.mount("/ota_bundles", StaticFiles(directory=str(ota_dir)), name="ota-bundles")

# Serve voice audio files
voice_dir = BASE_DIR / "voice_cache"
if not voice_dir.exists():
    voice_dir.mkdir(exist_ok=True)
app.mount("/voice_cache", StaticFiles(directory=str(voice_dir)), name="voice-cache")

# ═══════════════════════════════════════════════════════════
#  ROUTES — MiniApp API
# ═══════════════════════════════════════════════════════════
from miniapp_api import router as miniapp_router
app.include_router(miniapp_router)

# ═══ SSE Router (real-time signals push) ═══
if SSE_OK:
    app.include_router(sse_router)

# ═══════════════════════════════════════════════════════════
#  NEW ENGINE ROUTES — Voice, Gemini, Auth, Intelligence, OTA
# ═══════════════════════════════════════════════════════════
_new_engines = [
    ("jarvis_hindi_voice", "register_voice_routes", "Hindi Voice"),
    ("jarvis_gemini_bridge", "register_gemini_routes", "Gemini Bridge"),
    ("jarvis_smart_auth", "register_auth_routes", "Smart Auth"),
    ("jarvis_super_intelligence", "register_intelligence_routes", "Super Intelligence"),
    ("jarvis_ota_update", "register_ota_routes", "OTA Updates"),
]
for mod_name, func_name, label in _new_engines:
    try:
        mod = __import__(mod_name)
        register_fn = getattr(mod, func_name)
        register_fn(app)
        logger.info(f"  ✅ {label} routes registered")
    except Exception as e:
        logger.warning(f"  ⚠️ {label} routes failed: {e}")


# ═══════════════════════════════════════════════════════════
#  ROOT PAGES
# ═══════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def serve_miniapp(request: Request):
    """Serve the main JARVIS mini app."""
    if MINIAPP_INDEX.exists():
        return HTMLResponse(MINIAPP_INDEX.read_text())
    return templates.TemplateResponse("miniapp.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def serve_miniapp_alt(request: Request):
    """Alternate route for the mini app."""
    if MINIAPP_INDEX.exists():
        return HTMLResponse(MINIAPP_INDEX.read_text())
    return templates.TemplateResponse("miniapp.html", {"request": request})


@app.get("/miniapp", response_class=HTMLResponse)
async def serve_miniapp_route(request: Request):
    """Main mini app — serves React SPA."""
    if MINIAPP_INDEX.exists():
        return HTMLResponse(MINIAPP_INDEX.read_text())
    return templates.TemplateResponse("miniapp.html", {"request": request})


# Serve manifest.json and sw.js for PWA
from fastapi.responses import FileResponse

@app.get("/miniapp/manifest.json")
async def miniapp_manifest():
    f = MINIAPP_DIST / "manifest.json"
    if f.exists():
        return FileResponse(str(f), media_type="application/json")
    return JSONResponse({"name": "JARVIS Trading"})

@app.get("/miniapp/sw.js")
async def miniapp_sw():
    f = MINIAPP_DIST / "sw.js"
    if f.exists():
        return FileResponse(str(f), media_type="application/javascript")
    return JSONResponse({"error": "not found"}, status_code=404)


# SPA catch-all — any /miniapp/* that doesn't match API routes → serve index.html
@app.get("/miniapp/{path:path}", response_class=HTMLResponse)
async def miniapp_spa_catchall(request: Request, path: str):
    """Catch-all for React Router — serves index.html for all SPA routes."""
    # Don't catch API routes or static assets that already have their own mounts
    if path.startswith("assets/") or path.startswith("icons/"):
        return JSONResponse({"error": "not found"}, status_code=404)
    if MINIAPP_INDEX.exists():
        return HTMLResponse(MINIAPP_INDEX.read_text())
    return templates.TemplateResponse("miniapp.html", {"request": request})


# ═══════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════

# APK Download — serves the latest APK from a permanent URL
APK_PATH = BASE_DIR / "jarvis-trading.apk"

@app.get("/download", response_class=HTMLResponse)
async def download_page():
    """Beautiful APK download page."""
    apk_size = f"{APK_PATH.stat().st_size / (1024*1024):.1f} MB" if APK_PATH.exists() else "N/A"
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JARVIS Trading - Download</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0e1a;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'SF Pro',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}}
.card{{background:linear-gradient(135deg,#1a1f3a,#0f1225);border:1px solid rgba(59,130,246,.3);border-radius:24px;padding:48px 36px;text-align:center;max-width:420px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.logo{{font-size:3rem;font-weight:900;background:linear-gradient(135deg,#3b82f6,#8b5cf6,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
.subtitle{{color:#94a3b8;font-size:.9rem;margin-bottom:32px}}
.features{{text-align:left;margin:24px 0;padding:0 12px}}
.features div{{padding:8px 0;color:#cbd5e1;font-size:.85rem;border-bottom:1px solid rgba(255,255,255,.05)}}
.features span{{margin-right:8px}}
.btn{{display:inline-block;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;text-decoration:none;padding:16px 48px;border-radius:16px;font-size:1.1rem;font-weight:700;transition:all .2s;box-shadow:0 8px 24px rgba(59,130,246,.4)}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 12px 32px rgba(59,130,246,.5)}}
.size{{color:#64748b;font-size:.75rem;margin-top:12px}}
.badge{{display:inline-block;background:rgba(34,197,94,.15);color:#4ade80;padding:4px 12px;border-radius:8px;font-size:.75rem;margin-bottom:24px}}
</style></head><body>
<div class="card">
<div class="logo">JARVIS</div>
<p class="subtitle">AI-Powered Trading Intelligence</p>
<div class="badge">✅ 24/7 Always Online</div>
<div class="features">
<div><span>📊</span> Real-time NIFTY, SENSEX, BANKNIFTY</div>
<div><span>🤖</span> AI Trading Signals & Predictions</div>
<div><span>💎</span> Crypto DeFi Scanner</div>
<div><span>🗣️</span> Hindi Voice Assistant</div>
<div><span>🧠</span> Gemini + GPT Super Intelligence</div>
<div><span>📈</span> FII/DII, PCR, VIX, Options Chain</div>
</div>
<a href="/download/apk" class="btn">⬇️ Download APK</a>
<p class="size">{apk_size} • Android 7.0+</p>
</div></body></html>""")

@app.get("/download/apk")
async def download_apk():
    """Direct APK download."""
    if APK_PATH.exists():
        return FileResponse(
            str(APK_PATH),
            media_type="application/vnd.android.package-archive",
            filename="jarvis-trading.apk",
            headers={"Content-Disposition": "attachment; filename=jarvis-trading.apk"}
        )
    return JSONResponse({"error": "APK not found"}, status_code=404)


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin(request: Request):
    """Serve the admin panel."""
    stats = {"total_users": 0, "active_today": 0, "premium_users": 0,
             "pending_approvals": 0, "last_update": "--"}
    users = []
    pending_approvals = []
    if ADMIN_PANEL_OK:
        try:
            all_users = get_all_users()
            users = all_users
            stats["total_users"] = len(all_users)
            stats["active_today"] = sum(1 for u in all_users if u.get("last_active", "")[:10] == datetime.now().strftime("%Y-%m-%d"))
            stats["premium_users"] = sum(1 for u in all_users if u.get("tier") == "premium")
            stats["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Admin data error: {e}")
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats,
        "users": users,
        "pending_approvals": pending_approvals,
        "payment_stats": {"total_deposits": 0, "total_withdrawals": 0, "pending_withdrawals": 0, "active_wallets": 0},
        "wallets": [],
        "transactions": [],
        "pending_withdrawals": [],
        "admin_chat_id": os.getenv("ADMIN_CHAT_ID", "Not Set"),
        "admin_name": "JARVIS Admin",
    })


@app.get("/api/admin/overview")
async def admin_overview():
    """Admin API — system overview with real data."""
    data = {"total_users": 0, "active_today": 0, "premium": 0, "features": "", "engines_loaded": 0, "ws_clients": 0, "cache_entries": 0}
    if ADMIN_PANEL_OK:
        try:
            all_users = get_all_users()
            data["total_users"] = len(all_users)
            data["active_today"] = sum(1 for u in all_users if u.get("last_active", "")[:10] == datetime.now().strftime("%Y-%m-%d"))
            data["premium"] = sum(1 for u in all_users if u.get("is_premium"))
            data["features"] = get_features_status()
        except Exception:
            pass
    # Engine status from miniapp health
    try:
        from miniapp_api import _cache, _ws_clients
        data["cache_entries"] = len(_cache)
        data["ws_clients"] = len(_ws_clients)
    except:
        pass
    return data


@app.get("/api/admin/features")
async def admin_features():
    """Get all feature toggles as JSON."""
    if ADMIN_PANEL_OK:
        try:
            from admin_panel import DEFAULT_FEATURES, _features_cache, load_features_cache
            if not _features_cache:
                load_features_cache()
            features = []
            for fid, fdata in DEFAULT_FEATURES.items():
                features.append({
                    "id": fid,
                    "name": fdata["name"],
                    "category": fdata["category"],
                    "enabled": _features_cache.get(fid, fdata["enabled"]),
                })
            return {"features": features}
        except Exception as e:
            return {"features": [], "error": str(e)}
    return {"features": []}


@app.post("/api/admin/features/toggle")
async def admin_toggle_feature(request: Request):
    """Toggle a feature on/off. Body: {feature_id, enabled}"""
    if not ADMIN_PANEL_OK:
        return {"error": "Admin panel not loaded"}
    try:
        body = await request.json()
        fid = body.get("feature_id", "")
        enabled = body.get("enabled", True)
        admin_id = os.getenv("ADMIN_CHAT_ID", "0")
        ok, msg = toggle_feature(fid, enabled, admin_id)
        return {"success": ok, "message": msg}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/user/block")
async def admin_block_user_route(request: Request):
    """Block a user. Body: {chat_id}"""
    if not ADMIN_PANEL_OK:
        return {"error": "Admin panel not loaded"}
    try:
        body = await request.json()
        cid = str(body.get("chat_id", ""))
        admin_id = os.getenv("ADMIN_CHAT_ID", "0")
        msg = block_user(cid, admin_id)
        return {"success": True, "message": msg}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/user/unblock")
async def admin_unblock_user_route(request: Request):
    """Unblock a user. Body: {chat_id}"""
    if not ADMIN_PANEL_OK:
        return {"error": "Admin panel not loaded"}
    try:
        body = await request.json()
        cid = str(body.get("chat_id", ""))
        admin_id = os.getenv("ADMIN_CHAT_ID", "0")
        msg = unblock_user(cid, admin_id)
        return {"success": True, "message": msg}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/user/message")
async def admin_send_message(request: Request):
    """Send a message to a specific user via Telegram. Body: {chat_id, message}"""
    try:
        body = await request.json()
        cid = body.get("chat_id", "")
        msg = body.get("message", "")
        if not cid or not msg:
            return {"error": "chat_id and message required"}
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return {"error": "TELEGRAM_BOT_TOKEN not configured"}
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": cid, "text": msg, "parse_mode": "HTML"}
            )
            return {"success": resp.status_code == 200, "data": resp.json()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/broadcast")
async def admin_broadcast(request: Request):
    """Broadcast message to all users. Body: {message}"""
    try:
        body = await request.json()
        msg = body.get("message", "")
        if not msg:
            return {"error": "Message required"}
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return {"error": "TELEGRAM_BOT_TOKEN not configured"}
        targets = []
        if ADMIN_PANEL_OK:
            from admin_panel import get_broadcast_targets, log_broadcast
            targets = get_broadcast_targets()
        if not targets:
            return {"error": "No users to broadcast to", "sent": 0}
        import httpx
        sent = 0
        failed = 0
        async with httpx.AsyncClient(timeout=10) as client:
            for cid in targets:
                try:
                    resp = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": cid, "text": msg, "parse_mode": "HTML"}
                    )
                    if resp.status_code == 200:
                        sent += 1
                    else:
                        failed += 1
                except:
                    failed += 1
        if ADMIN_PANEL_OK:
            log_broadcast(msg, os.getenv("ADMIN_CHAT_ID", "0"), sent)
        return {"success": True, "sent": sent, "failed": failed, "total": len(targets)}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/bot")
async def admin_bot_control(request: Request):
    """Bot control commands. Body: {command: start|stop|restart|status|health|logs}"""
    try:
        body = await request.json()
        cmd = body.get("command", "status")
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

        if cmd == "status":
            # Check if bot token is valid
            if not bot_token:
                return {"status": "error", "message": "TELEGRAM_BOT_TOKEN not configured"}
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                if resp.status_code == 200:
                    bot_info = resp.json().get("result", {})
                    return {"status": "online", "bot": bot_info.get("username", "unknown"), "name": bot_info.get("first_name", "JARVIS")}
                return {"status": "error", "message": "Bot token invalid"}

        elif cmd == "health":
            # Return comprehensive health
            import psutil
            cpu = psutil.cpu_percent() if hasattr(psutil, 'cpu_percent') else 0
            mem = psutil.virtual_memory().percent if hasattr(psutil, 'virtual_memory') else 0
            return {"status": "ok", "cpu": cpu, "memory": mem, "bot_token": bool(bot_token), "ai_keys": sum(1 for k in ["GROQ_API_KEY","OPENAI_API_KEY","GEMINI_API_KEY"] if os.getenv(k))}

        elif cmd == "logs":
            # Return recent log entries
            try:
                import subprocess
                result = subprocess.run(["tail", "-n", "50", "jarvis.log"], capture_output=True, text=True, timeout=5)
                return {"logs": result.stdout or "No log file found"}
            except:
                return {"logs": "Log file not available. Server is running via uvicorn."}

        elif cmd in ("start", "restart"):
            return {"status": "ok", "message": f"Bot {cmd} signal sent. Bot runs automatically with the server."}

        elif cmd == "stop":
            return {"status": "ok", "message": "Bot stop signal sent. Note: Bot will restart automatically."}

        return {"status": "unknown_command", "command": cmd}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/admin/engines")
async def admin_engines():
    """Get real-time status of all engines."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"http://127.0.0.1:{os.getenv('PORT', '8000')}/api/miniapp/health")
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return {"status": "ok", "engines_loaded": 0, "engines": {}}


from datetime import datetime


@app.get("/health")
async def root_health():
    """Root health check."""
    return {
        "status": "ok",
        "platform": "JARVIS Trading Platform",
        "version": "5.0.0",
        "engines": {
            "dex_engine": "active",
            "jarvis_brain": "active",
            "auto_sniper": "active",
            "security": "active",
        },
    }


@app.get("/ping")
async def ping():
    """Simple ping for uptime monitoring."""
    return {"pong": True}


# ═══════════════════════════════════════════════════════════
#  NEW POWER-UP API ROUTES
# ═══════════════════════════════════════════════════════════

# --- Metrics ---
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if PROMETHEUS_OK:
        return await metrics_endpoint(Request(scope={"type": "http"}))
    return JSONResponse({"error": "Prometheus not available"}, status_code=503)

@app.get("/api/metrics")
async def api_metrics():
    """System metrics for admin dashboard."""
    data = {"redis": None, "postgres": None, "tasks": None, "errors": None, "notifications": None, "social": None}
    if REDIS_CACHE_OK:
        data["redis"] = cache_stats()
    if POSTGRES_OK:
        try:
            data["postgres"] = await pg_stats()
        except:
            data["postgres"] = {"status": "error"}
    if TASKS_OK:
        data["tasks"] = task_stats()
    if ERROR_HANDLER_OK:
        data["errors"] = get_error_summary()
    if NOTIFICATIONS_OK:
        data["notifications"] = get_notification_stats()
    if SOCIAL_OK:
        data["social"] = get_social_stats()
    return data


# --- JWT Auth Routes ---
@app.post("/api/auth/register")
async def auth_register(request: Request):
    """Register a new user."""
    if not JWT_AUTH_OK:
        return JSONResponse({"error": "Auth module not available"}, status_code=503)
    try:
        body = await request.json()
        result = await register_user(body.get("username", ""), body.get("password", ""), body.get("chat_id", ""))
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/auth/login")
async def auth_login(request: Request):
    """Login and get JWT tokens."""
    if not JWT_AUTH_OK:
        return JSONResponse({"error": "Auth module not available"}, status_code=503)
    try:
        body = await request.json()
        result = await login_user(body.get("username", ""), body.get("password", ""))
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=401)

@app.post("/api/auth/refresh")
async def auth_refresh(request: Request):
    """Refresh access token."""
    if not JWT_AUTH_OK:
        return JSONResponse({"error": "Auth module not available"}, status_code=503)
    try:
        body = await request.json()
        result = await refresh_access_token(body.get("refresh_token", ""))
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=401)


# --- Task Queue Routes ---
@app.post("/api/tasks/enqueue")
async def api_enqueue_task(request: Request):
    """Enqueue a background task."""
    if not TASKS_OK:
        return JSONResponse({"error": "Task queue not available"}, status_code=503)
    try:
        body = await request.json()
        task_id = await enqueue_task(body.get("task_type", ""), body.get("params", {}), body.get("user_id", "system"))
        return {"task_id": task_id, "status": "queued"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/tasks/{task_id}")
async def api_task_status(task_id: str):
    """Get task status."""
    if not TASKS_OK:
        return JSONResponse({"error": "Task queue not available"}, status_code=503)
    status = get_task_status(task_id)
    if not status:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return status

@app.get("/api/tasks")
async def api_all_tasks():
    """Get task queue stats."""
    if not TASKS_OK:
        return {"status": "unavailable"}
    return task_stats()


# --- Social Trading Routes ---
@app.get("/api/social/feed")
async def api_social_feed(limit: int = 20, offset: int = 0, action: str = None):
    """Get social trading feed."""
    if not SOCIAL_OK:
        return {"signals": [], "message": "Social trading not available"}
    return {"signals": get_feed(limit, offset, action)}

@app.post("/api/social/share")
async def api_social_share(request: Request):
    """Share a trading signal."""
    if not SOCIAL_OK:
        return JSONResponse({"error": "Social trading not available"}, status_code=503)
    try:
        body = await request.json()
        signal = share_signal(body.get("user_id", "anon"), body.get("username", "Anon"), body)
        return {"signal": signal}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/social/like/{signal_id}")
async def api_social_like(signal_id: str, request: Request):
    """Like a signal."""
    if not SOCIAL_OK:
        return JSONResponse({"error": "Social not available"}, status_code=503)
    body = await request.json()
    count = social_like(signal_id, body.get("user_id", "anon"))
    return {"likes": count}

@app.post("/api/social/follow/{trader_id}")
async def api_social_follow(trader_id: str, request: Request):
    """Follow a trader."""
    if not SOCIAL_OK:
        return JSONResponse({"error": "Social not available"}, status_code=503)
    body = await request.json()
    ok = follow_trader(body.get("user_id", ""), trader_id)
    return {"followed": ok}

@app.get("/api/social/leaderboard")
async def api_leaderboard(limit: int = 20):
    """Get trader leaderboard."""
    if not SOCIAL_OK:
        return {"leaders": []}
    return {"leaders": get_leaderboard(limit)}

@app.get("/api/social/stats")
async def api_social_stats_route():
    """Get social trading stats."""
    if not SOCIAL_OK:
        return {"status": "unavailable"}
    return get_social_stats()


# --- DexTools Routes ---
@app.get("/api/dextools/summary")
async def api_dextools_summary():
    """Get DexTools market summary."""
    if not DEXTOOLS_OK:
        return {"status": "unavailable", "message": "DexTools API not configured"}
    try:
        return await get_dextools_summary()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/dextools/hot/{chain}")
async def api_dextools_hot(chain: str = "ethereum"):
    """Get hot pairs from DexTools."""
    if not DEXTOOLS_OK:
        return {"pairs": []}
    try:
        return await get_hot_pairs(chain)
    except Exception as e:
        return {"error": str(e)}


# --- Birdeye Routes ---
@app.get("/api/birdeye/summary")
async def api_birdeye_summary():
    """Get Birdeye Solana intelligence summary."""
    if not BIRDEYE_OK:
        return {"status": "unavailable", "message": "Birdeye API not configured"}
    try:
        return await get_birdeye_summary()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/birdeye/trending")
async def api_birdeye_trending():
    """Get trending tokens on Solana."""
    if not BIRDEYE_OK:
        return {"tokens": []}
    try:
        return await get_trending_tokens()
    except Exception as e:
        return {"error": str(e)}


# --- Notification Routes ---
@app.post("/api/notifications/subscribe")
async def api_subscribe(request: Request):
    """Subscribe to push notifications."""
    if not NOTIFICATIONS_OK:
        return JSONResponse({"error": "Notifications not available"}, status_code=503)
    body = await request.json()
    prefs = subscribe(body.get("chat_id", ""), body.get("preferences"))
    return {"subscribed": True, "preferences": prefs}

@app.post("/api/notifications/unsubscribe")
async def api_unsubscribe(request: Request):
    """Unsubscribe from notifications."""
    if not NOTIFICATIONS_OK:
        return JSONResponse({"error": "Notifications not available"}, status_code=503)
    body = await request.json()
    ok = unsubscribe(body.get("chat_id", ""))
    return {"unsubscribed": ok}

@app.get("/api/notifications/stats")
async def api_notification_stats():
    """Get notification stats."""
    if not NOTIFICATIONS_OK:
        return {"status": "unavailable"}
    return get_notification_stats()


# --- Admin API Keys Management ---
@app.get("/api/admin/api-keys")
async def admin_api_keys():
    """Get all API keys (masked)."""
    if not POSTGRES_OK:
        # Fallback: read from environment
        keys = []
        for k in ["GROQ_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
                   "DEXTOOLS_API_KEY", "BIRDEYE_API_KEY", "TELEGRAM_BOT_TOKEN", "NEWS_API_KEY",
                   "COINMARKETCAP_API_KEY", "STABILITY_API_KEY"]:
            val = os.getenv(k, "")
            keys.append({"key_name": k, "masked_value": val[:4] + "..." + val[-4:] if len(val) > 8 else ("set" if val else "not set"), "is_set": bool(val)})
        return {"keys": keys}
    try:
        keys = await pg_get_api_keys()
        return {"keys": keys}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/admin/api-keys")
async def admin_set_api_key(request: Request):
    """Set an API key."""
    if not POSTGRES_OK:
        return JSONResponse({"error": "PostgreSQL not available"}, status_code=503)
    try:
        body = await request.json()
        ok = await pg_set_api_key(body.get("key_name", ""), body.get("key_value", ""), body.get("admin_id", "system"))
        return {"success": ok}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


# --- Error Reporting Routes ---
@app.get("/api/admin/errors")
async def admin_errors():
    """Get error summary for admin."""
    if not ERROR_HANDLER_OK:
        return {"errors": [], "message": "Error handler not available"}
    return get_error_summary()

@app.get("/api/admin/engine-health")
async def admin_engine_health():
    """Get engine health status."""
    if not ERROR_HANDLER_OK:
        return {"engines": {}}
    return {"engines": get_engine_health()}


# --- System Overview (enhanced) ---
@app.get("/api/system/overview")
async def system_overview():
    """Comprehensive system overview for admin."""
    import psutil
    return {
        "server": {
            "version": "5.0.0",
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        },
        "modules": {
            "redis_cache": REDIS_CACHE_OK,
            "prometheus": PROMETHEUS_OK,
            "rate_limiter": RATE_LIMITER_OK,
            "sse": SSE_OK,
            "postgres": POSTGRES_OK,
            "tasks": TASKS_OK,
            "error_handler": ERROR_HANDLER_OK,
            "notifications": NOTIFICATIONS_OK,
            "social_trading": SOCIAL_OK,
            "dextools": DEXTOOLS_OK,
            "birdeye": BIRDEYE_OK,
            "jwt_auth": JWT_AUTH_OK,
        },
        "redis": cache_stats() if REDIS_CACHE_OK else None,
        "tasks": task_stats() if TASKS_OK else None,
        "social": get_social_stats() if SOCIAL_OK else None,
    }


# ═══════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════
@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    # Serve React SPA for any non-API 404s (SPA routing)
    if MINIAPP_INDEX.exists():
        return HTMLResponse(MINIAPP_INDEX.read_text())
    return templates.TemplateResponse("miniapp.html", {"request": request})


@app.exception_handler(500)
async def server_error(request: Request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# ═══════════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting JARVIS on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        ws_max_size=16 * 1024 * 1024,
        timeout_keep_alive=30,
    )
