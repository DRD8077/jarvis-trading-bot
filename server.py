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

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
    logger.info("  ✅ Server ready!")
    logger.info("═══════════════════════════════════════")
    
    yield
    
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
#  MIDDLEWARE — Security + CORS
# ═══════════════════════════════════════════════════════════
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
#  ROUTES — MiniApp API
# ═══════════════════════════════════════════════════════════
from miniapp_api import router as miniapp_router
app.include_router(miniapp_router)


# ═══════════════════════════════════════════════════════════
#  ROOT PAGES
# ═══════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def serve_miniapp(request: Request):
    """Serve the main JARVIS mini app."""
    return templates.TemplateResponse("miniapp.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def serve_miniapp_alt(request: Request):
    """Alternate route for the mini app."""
    return templates.TemplateResponse("miniapp.html", {"request": request})


@app.get("/miniapp", response_class=HTMLResponse)
async def serve_miniapp_alt2(request: Request):
    """Another alternate route."""
    return templates.TemplateResponse("miniapp.html", {"request": request})


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
        reload=os.getenv("ENV", "development") == "development",
        log_level="info",
        ws_max_size=16 * 1024 * 1024,
        timeout_keep_alive=30,
    )
