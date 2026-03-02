"""
╔══════════════════════════════════════════════════════════════════════╗
║           JARVIS SERVER — CONFIGURATION & SECURITY                  ║
║           Z++++ Grade Security Configuration                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# ═══════════════════════════════════════════════════════════════════
#  SERVER SETTINGS
# ═══════════════════════════════════════════════════════════════════
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ═══════════════════════════════════════════════════════════════════
#  SECURITY — Z++++ Grade
# ═══════════════════════════════════════════════════════════════════
# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(64))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
BCRYPT_ROUNDS = 12

# Rate limiting (per IP)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Brute force protection
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# Request signing
API_SIGNING_KEY = os.getenv("API_SIGNING_KEY", secrets.token_hex(32))

# CORS origins (comma-separated)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ═══════════════════════════════════════════════════════════════════
#  API KEYS
# ═══════════════════════════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ═══════════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════════
DATABASE_DIR = Path(__file__).parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/jarvis.db")

# ═══════════════════════════════════════════════════════════════════
#  MARKET DATA
# ═══════════════════════════════════════════════════════════════════
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BINANCE_BASE = "https://api.binance.com/api/v3"
DEXSCREENER_BASE = "https://api.dexscreener.com/latest"

# Cache settings
MARKET_CACHE_TTL = 30  # seconds
AI_CACHE_TTL = 300  # seconds

# ═══════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
