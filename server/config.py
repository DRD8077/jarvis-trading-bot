"""
JARVIS SERVER v4.0 — CONFIGURATION
Z++++ Security | 24/7 Auto-Running
"""
import os, secrets
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# ═══ SERVER ═══
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
APP_VERSION = "4.0.0"

# ═══ SECURITY ═══
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(64))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
BCRYPT_ROUNDS = 12
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
RATE_LIMIT_REQUESTS = 300
RATE_LIMIT_WINDOW = 60
CORS_ORIGINS = ["*"]

# ═══ API KEYS ═══
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ═══ DATABASE ═══
DATABASE_DIR = Path(__file__).parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/jarvis.db"

# ═══ EXTERNAL APIS ═══
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BINANCE_BASE = "https://api.binance.com/api/v3"
DEXSCREENER_BASE = "https://api.dexscreener.com/latest"

# ═══ CACHE TTL (seconds) ═══
MARKET_CACHE_TTL = 30
AI_CACHE_TTL = 300

# ═══ LOGGING ═══
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
