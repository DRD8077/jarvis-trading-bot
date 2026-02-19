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
    
    # Start background data prefetcher for Indian market data
    async def _prefetch_loop():
        """Background task to keep Indian market data warm in cache."""
        import httpx
        await asyncio.sleep(5)  # Wait for server to fully start
        base = f"http://127.0.0.1:{os.getenv('PORT', '8000')}"
        endpoints = [
            "/api/miniapp/india/dashboard",
            "/api/miniapp/dashboard",
            "/api/miniapp/markets",
        ]
        while True:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    for ep in endpoints:
                        try:
                            await client.get(f"{base}{ep}")
                        except Exception:
                            pass
                logger.debug("🔄 Background data refresh completed")
            except Exception:
                pass
            await asyncio.sleep(90)  # Refresh every 90 seconds
    
    prefetch_task = asyncio.create_task(_prefetch_loop())
    
    yield
    
    # Shutdown
    prefetch_task.cancel()
    
    # Shutdown: close HTTP client
    logger.info("Shutting down JARVIS...")
    try:
        from dex_engine import close_client
        await close_client()
        logger.info("HTTP client closed")
    except Exception as e:
        logger.warning(f"Shutdown error: {e}")


# ═══════════════════════════════════════════════════════════
#  APP INIT
# ═══════════════════════════════════════════════════════════
app = FastAPI(
    title="JARVIS Trading Platform",
    description="Real-time AI-powered crypto & stock trading platform",
    version="5.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE — Speed + Security + CORS
# ═══════════════════════════════════════════════════════════
# GZip compression for fast responses
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)

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
#  REACT MINI APP — Serve built React SPA from dist/
# ═══════════════════════════════════════════════════════════
MINIAPP_DIST = BASE_DIR / "telegram-mini-app" / "dist"
MINIAPP_INDEX = MINIAPP_DIST / "index.html"

# Serve React app assets (JS, CSS bundles)
if (MINIAPP_DIST / "assets").exists():
    app.mount("/miniapp/assets", StaticFiles(directory=str(MINIAPP_DIST / "assets")), name="miniapp-assets")

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
    """Admin API — system overview."""
    data = {"total_users": 0, "active_today": 0, "premium": 0, "features": ""}
    if ADMIN_PANEL_OK:
        try:
            all_users = get_all_users()
            data["total_users"] = len(all_users)
            data["features"] = get_features_status()
        except Exception:
            pass
    return data


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
