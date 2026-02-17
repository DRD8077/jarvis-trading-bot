"""
🛡️ Security Middleware v2.0 — Bulletproof Protection
═══════════════════════════════════════════════════════
Rate limiting, HMAC validation, Telegram auth, anti-hack.
"""

import os, json, time, hashlib, hmac, logging, secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Set
from collections import defaultdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("security")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_IDS = set(filter(None, [
    os.getenv("ADMIN_CHAT_ID", ""),
    os.getenv("OWNER_CHAT_ID", ""),
    os.getenv("TEST_CHAT_ID", ""),
]))
API_SECRET = os.getenv("API_SECRET", secrets.token_hex(32))

# Rate limiting config
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120  # requests per window (generous for real-time)
RATE_LIMIT_BURST = 30  # burst requests in 5 seconds

# IP blocking
_blocked_ips: Set[str] = set()
_rate_counters: Dict[str, list] = defaultdict(list)
_failed_auths: Dict[str, int] = defaultdict(int)


# ═══════════════════════════════════════════════════════════
#  RATE LIMITER
# ═══════════════════════════════════════════════════════════
def _check_rate_limit(ip: str) -> bool:
    """Check if IP is within rate limits. Returns True if allowed."""
    if ip in _blocked_ips:
        return False
    
    now = time.time()
    
    # Clean old entries
    _rate_counters[ip] = [t for t in _rate_counters[ip] if now - t < RATE_LIMIT_WINDOW]
    
    # Check window limit
    if len(_rate_counters[ip]) >= RATE_LIMIT_MAX:
        logger.warning(f"Rate limit exceeded: {ip}")
        return False
    
    # Check burst limit (5 second window)
    recent = [t for t in _rate_counters[ip] if now - t < 5]
    if len(recent) >= RATE_LIMIT_BURST:
        logger.warning(f"Burst limit exceeded: {ip}")
        return False
    
    _rate_counters[ip].append(now)
    return True


def block_ip(ip: str):
    """Block an IP address."""
    _blocked_ips.add(ip)
    logger.warning(f"IP blocked: {ip}")


def unblock_ip(ip: str):
    """Unblock an IP address."""
    _blocked_ips.discard(ip)


# ═══════════════════════════════════════════════════════════
#  TELEGRAM AUTH VALIDATION
# ═══════════════════════════════════════════════════════════
def validate_telegram_init_data(init_data: str) -> Optional[Dict]:
    """
    Validate Telegram WebApp initData using HMAC-SHA256.
    Returns user data if valid, None if invalid.
    """
    if not init_data or not BOT_TOKEN:
        return None
    
    try:
        # Parse the init data
        params = {}
        for part in init_data.split("&"):
            if "=" in part:
                key, val = part.split("=", 1)
                params[key] = val
        
        # Extract hash
        received_hash = params.pop("hash", "")
        if not received_hash:
            return None
        
        # Build check string (sorted by key)
        check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        
        # Compute HMAC
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(computed_hash, received_hash):
            return None
        
        # Check auth_date (not too old — 24 hours max)
        auth_date = int(params.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            return None
        
        # Parse user data
        import urllib.parse
        user_str = urllib.parse.unquote(params.get("user", "{}"))
        user = json.loads(user_str)
        
        return {
            "id": user.get("id"),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "username": user.get("username", ""),
            "is_premium": user.get("is_premium", False),
            "language_code": user.get("language_code", "en"),
        }
    except Exception as e:
        logger.warning(f"Telegram auth validation error: {e}")
        return None


def is_admin(user_id) -> bool:
    """Check if user is admin."""
    return str(user_id) in ADMIN_IDS


# ═══════════════════════════════════════════════════════════
#  SECURITY MIDDLEWARE
# ═══════════════════════════════════════════════════════════
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        
        # Check blocked IPs
        if ip in _blocked_ips:
            return JSONResponse({"error": "Blocked"}, status_code=403)
        
        # Rate limiting
        if not _check_rate_limit(ip):
            return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' https: data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https: wss: http:; "
            "frame-src 'self' https:; "
            "frame-ancestors 'self' https: http:;"
        )
        
        return response


# ═══════════════════════════════════════════════════════════
#  API KEY VALIDATION
# ═══════════════════════════════════════════════════════════
def validate_api_key(key: str) -> bool:
    """Validate an API key."""
    if not key or not API_SECRET:
        return False
    return hmac.compare_digest(key, API_SECRET)


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_hex(32)


# ═══════════════════════════════════════════════════════════
#  INPUT SANITIZATION
# ═══════════════════════════════════════════════════════════
def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Limit length
    text = text[:max_length]
    # Remove potential script tags
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    return text.strip()
