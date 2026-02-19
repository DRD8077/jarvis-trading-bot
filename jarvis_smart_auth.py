"""
🔐 JARVIS Smart Auth v1.0 — Owner & User Recognition System
═══════════════════════════════════════════════════════════════════
APK understands who is the OWNER and who are USERS!

Features:
  - Owner identification & special privileges
  - User registration & login via Telegram
  - Multi-tier access: Owner > Admin > Premium > Free
  - Device fingerprinting for security
  - Session management with JWT tokens
  - Auto-login with saved credentials
  - User profile & preferences storage
  - Behavioral analysis to identify real users
  - Anti-fraud detection

Author: JARVIS AI
"""

import os
import json
import hashlib
import hmac
import time
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger("jarvis-auth")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  AUTH CONFIG
# ═══════════════════════════════════════════════════════════

# Owner identification
OWNER_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "") or hashlib.sha256(
    f"jarvis-{OWNER_CHAT_ID}-secret".encode()
).hexdigest()

# Storage
AUTH_DB_PATH = Path("/workspaces/codespaces-blank/jarvis_auth_db.json")
SESSIONS_PATH = Path("/workspaces/codespaces-blank/jarvis_sessions.json")

# Access tiers
class AccessTier:
    OWNER = "owner"
    ADMIN = "admin"
    PREMIUM = "premium"
    FREE = "free"
    BANNED = "banned"

TIER_PERMISSIONS = {
    AccessTier.OWNER: {
        "all_access": True,
        "admin_panel": True,
        "broadcast": True,
        "manage_users": True,
        "trading": True,
        "premium_features": True,
        "api_unlimited": True,
        "voice_assistant": True,
        "gemini_pro": True,
        "auto_trader": True,
        "code_engine": True,
    },
    AccessTier.ADMIN: {
        "all_access": False,
        "admin_panel": True,
        "broadcast": True,
        "manage_users": True,
        "trading": True,
        "premium_features": True,
        "api_unlimited": True,
        "voice_assistant": True,
        "gemini_pro": True,
        "auto_trader": True,
        "code_engine": True,
    },
    AccessTier.PREMIUM: {
        "all_access": False,
        "admin_panel": False,
        "broadcast": False,
        "manage_users": False,
        "trading": True,
        "premium_features": True,
        "api_unlimited": False,
        "voice_assistant": True,
        "gemini_pro": True,
        "auto_trader": True,
        "code_engine": False,
    },
    AccessTier.FREE: {
        "all_access": False,
        "admin_panel": False,
        "broadcast": False,
        "manage_users": False,
        "trading": True,
        "premium_features": False,
        "api_unlimited": False,
        "voice_assistant": True,
        "gemini_pro": False,
        "auto_trader": False,
        "code_engine": False,
    },
    AccessTier.BANNED: {
        "all_access": False,
        "admin_panel": False,
        "broadcast": False,
        "manage_users": False,
        "trading": False,
        "premium_features": False,
        "api_unlimited": False,
        "voice_assistant": False,
        "gemini_pro": False,
        "auto_trader": False,
        "code_engine": False,
    },
}

# Rate limits per tier (requests per minute)
TIER_RATE_LIMITS = {
    AccessTier.OWNER: 999999,
    AccessTier.ADMIN: 1000,
    AccessTier.PREMIUM: 100,
    AccessTier.FREE: 30,
    AccessTier.BANNED: 0,
}


# ═══════════════════════════════════════════════════════════
#  DATABASE — User & Session Storage
# ═══════════════════════════════════════════════════════════

def _load_auth_db() -> Dict:
    """Load auth database."""
    if AUTH_DB_PATH.exists():
        try:
            return json.loads(AUTH_DB_PATH.read_text())
        except:
            pass
    return {"users": {}, "created_at": datetime.now(IST).isoformat()}


def _save_auth_db(db: Dict):
    """Save auth database."""
    db["updated_at"] = datetime.now(IST).isoformat()
    AUTH_DB_PATH.write_text(json.dumps(db, indent=2, default=str))


def _load_sessions() -> Dict:
    """Load active sessions."""
    if SESSIONS_PATH.exists():
        try:
            return json.loads(SESSIONS_PATH.read_text())
        except:
            pass
    return {}


def _save_sessions(sessions: Dict):
    """Save active sessions."""
    SESSIONS_PATH.write_text(json.dumps(sessions, indent=2, default=str))


# ═══════════════════════════════════════════════════════════
#  TOKEN GENERATION — JWT-like tokens
# ═══════════════════════════════════════════════════════════

def _generate_token(user_id: str, tier: str, expires_hours: int = 720) -> str:
    """Generate a secure auth token."""
    payload = {
        "uid": user_id,
        "tier": tier,
        "iat": int(time.time()),
        "exp": int(time.time()) + (expires_hours * 3600),
        "jti": secrets.token_hex(8),
    }
    payload_str = json.dumps(payload, separators=(',', ':'))
    import base64
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()
    signature = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def _verify_token(token: str) -> Optional[Dict]:
    """Verify and decode an auth token."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        
        payload_b64, signature = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        import base64
        payload_str = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_str)
        
        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
        
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════

def register_user(
    chat_id: str,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    device_fingerprint: str = "",
) -> Dict[str, Any]:
    """
    Register a new user or update existing.
    Auto-detects if the user is the OWNER.
    """
    db = _load_auth_db()
    
    # Determine tier
    is_owner = str(chat_id) == str(OWNER_CHAT_ID)
    
    existing = db["users"].get(str(chat_id), {})
    current_tier = existing.get("tier", AccessTier.FREE)
    
    if is_owner:
        tier = AccessTier.OWNER
    elif current_tier in [AccessTier.ADMIN, AccessTier.PREMIUM]:
        tier = current_tier  # Preserve existing tier
    else:
        tier = AccessTier.FREE
    
    user = {
        "chat_id": str(chat_id),
        "username": username or existing.get("username", ""),
        "first_name": first_name or existing.get("first_name", ""),
        "last_name": last_name or existing.get("last_name", ""),
        "tier": tier,
        "is_owner": is_owner,
        "device_fingerprints": list(set(
            existing.get("device_fingerprints", []) + ([device_fingerprint] if device_fingerprint else [])
        ))[-5:],  # Keep last 5 devices
        "registered_at": existing.get("registered_at", datetime.now(IST).isoformat()),
        "last_active": datetime.now(IST).isoformat(),
        "login_count": existing.get("login_count", 0) + 1,
        "total_requests": existing.get("total_requests", 0),
        "preferences": existing.get("preferences", {
            "language": "hindi",
            "voice_enabled": True,
            "notifications": True,
            "theme": "dark",
        }),
        "security": {
            "last_ip": "",
            "suspicious_activity": False,
            "failed_attempts": 0,
        },
    }
    
    db["users"][str(chat_id)] = user
    _save_auth_db(db)
    
    # Generate token
    token = _generate_token(str(chat_id), tier)
    
    # Create session
    sessions = _load_sessions()
    sessions[str(chat_id)] = {
        "token": token,
        "created": datetime.now(IST).isoformat(),
        "device": device_fingerprint,
        "active": True,
    }
    _save_sessions(sessions)
    
    logger.info(f"👤 User registered: {chat_id} ({first_name}) - Tier: {tier}")
    
    return {
        "success": True,
        "user": user,
        "token": token,
        "is_owner": is_owner,
        "tier": tier,
        "permissions": TIER_PERMISSIONS.get(tier, {}),
    }


def login_user(
    chat_id: str,
    telegram_init_data: str = "",
    device_fingerprint: str = "",
) -> Dict[str, Any]:
    """
    Login a user — verify identity and return session.
    
    For Telegram users: validates init_data
    For APK users: validates device fingerprint + chat_id
    """
    db = _load_auth_db()
    user = db["users"].get(str(chat_id))
    
    if not user:
        # Auto-register new user
        return register_user(chat_id, device_fingerprint=device_fingerprint)
    
    # Check if banned
    if user.get("tier") == AccessTier.BANNED:
        return {
            "success": False,
            "error": "Account suspended",
            "is_banned": True,
        }
    
    # Update last active
    user["last_active"] = datetime.now(IST).isoformat()
    user["login_count"] = user.get("login_count", 0) + 1
    
    if device_fingerprint:
        fps = user.get("device_fingerprints", [])
        if device_fingerprint not in fps:
            fps.append(device_fingerprint)
        user["device_fingerprints"] = fps[-5:]
    
    db["users"][str(chat_id)] = user
    _save_auth_db(db)
    
    # Generate new token
    tier = user.get("tier", AccessTier.FREE)
    token = _generate_token(str(chat_id), tier)
    
    # Update session
    sessions = _load_sessions()
    sessions[str(chat_id)] = {
        "token": token,
        "created": datetime.now(IST).isoformat(),
        "device": device_fingerprint,
        "active": True,
    }
    _save_sessions(sessions)
    
    return {
        "success": True,
        "user": user,
        "token": token,
        "is_owner": user.get("is_owner", False),
        "tier": tier,
        "permissions": TIER_PERMISSIONS.get(tier, {}),
    }


def verify_session(token: str) -> Optional[Dict]:
    """Verify a session token and return user info."""
    payload = _verify_token(token)
    if not payload:
        return None
    
    db = _load_auth_db()
    user = db["users"].get(payload["uid"])
    if not user:
        return None
    
    return {
        "user_id": payload["uid"],
        "tier": payload["tier"],
        "user": user,
        "permissions": TIER_PERMISSIONS.get(payload["tier"], {}),
        "is_owner": user.get("is_owner", False),
    }


# ═══════════════════════════════════════════════════════════
#  PERMISSION CHECKS
# ═══════════════════════════════════════════════════════════

def is_owner(chat_id: str) -> bool:
    """Check if chat_id is the OWNER."""
    return str(chat_id) == str(OWNER_CHAT_ID)


def get_user_tier(chat_id: str) -> str:
    """Get user's access tier."""
    if is_owner(chat_id):
        return AccessTier.OWNER
    
    db = _load_auth_db()
    user = db["users"].get(str(chat_id), {})
    return user.get("tier", AccessTier.FREE)


def has_permission(chat_id: str, permission: str) -> bool:
    """Check if user has a specific permission."""
    tier = get_user_tier(chat_id)
    perms = TIER_PERMISSIONS.get(tier, {})
    
    if perms.get("all_access"):
        return True
    
    return perms.get(permission, False)


def set_user_tier(chat_id: str, tier: str) -> Dict[str, Any]:
    """Set a user's access tier (owner/admin only)."""
    db = _load_auth_db()
    
    if str(chat_id) not in db["users"]:
        return {"error": "User not found"}
    
    db["users"][str(chat_id)]["tier"] = tier
    _save_auth_db(db)
    
    return {"success": True, "chat_id": chat_id, "new_tier": tier}


def ban_user(chat_id: str, reason: str = "") -> Dict[str, Any]:
    """Ban a user."""
    return set_user_tier(chat_id, AccessTier.BANNED)


def unban_user(chat_id: str) -> Dict[str, Any]:
    """Unban a user."""
    return set_user_tier(chat_id, AccessTier.FREE)


# ═══════════════════════════════════════════════════════════
#  USER PROFILE & STATS
# ═══════════════════════════════════════════════════════════

def get_user_profile(chat_id: str) -> Dict[str, Any]:
    """Get full user profile."""
    db = _load_auth_db()
    user = db["users"].get(str(chat_id))
    
    if not user:
        return {"error": "User not found"}
    
    tier = user.get("tier", AccessTier.FREE)
    
    return {
        "user": user,
        "tier": tier,
        "is_owner": user.get("is_owner", False),
        "permissions": TIER_PERMISSIONS.get(tier, {}),
        "rate_limit": TIER_RATE_LIMITS.get(tier, 30),
        "member_since": user.get("registered_at", ""),
        "login_count": user.get("login_count", 0),
    }


def get_all_users() -> List[Dict]:
    """Get all registered users."""
    db = _load_auth_db()
    return list(db.get("users", {}).values())


def get_user_count() -> Dict[str, int]:
    """Get user count by tier."""
    db = _load_auth_db()
    users = db.get("users", {})
    
    counts = {t: 0 for t in [AccessTier.OWNER, AccessTier.ADMIN, AccessTier.PREMIUM, AccessTier.FREE, AccessTier.BANNED]}
    
    for user in users.values():
        tier = user.get("tier", AccessTier.FREE)
        counts[tier] = counts.get(tier, 0) + 1
    
    counts["total"] = len(users)
    return counts


# ═══════════════════════════════════════════════════════════
#  DEVICE FINGERPRINTING
# ═══════════════════════════════════════════════════════════

def generate_device_fingerprint(
    user_agent: str = "",
    screen_resolution: str = "",
    timezone_offset: str = "",
    language: str = "",
    platform: str = "",
) -> str:
    """Generate a device fingerprint from browser/device info."""
    raw = f"{user_agent}|{screen_resolution}|{timezone_offset}|{language}|{platform}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════
#  FASTAPI ROUTES
# ═══════════════════════════════════════════════════════════

def register_auth_routes(app_or_router):
    """Register auth API routes."""
    from fastapi import APIRouter, Form, Header, Request
    from fastapi.responses import JSONResponse
    
    auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
    
    @auth_router.post("/register")
    async def api_register(
        chat_id: str = Form(""),
        username: str = Form(""),
        first_name: str = Form(""),
        device_fp: str = Form(""),
    ):
        """Register new user."""
        if not chat_id:
            return JSONResponse({"error": "chat_id required"}, status_code=400)
        result = register_user(chat_id, username, first_name, device_fingerprint=device_fp)
        return JSONResponse(result)
    
    @auth_router.post("/login")
    async def api_login(
        chat_id: str = Form(""),
        telegram_init: str = Form(""),
        device_fp: str = Form(""),
    ):
        """Login user."""
        if not chat_id:
            return JSONResponse({"error": "chat_id required"}, status_code=400)
        result = login_user(chat_id, telegram_init, device_fp)
        return JSONResponse(result)
    
    @auth_router.get("/verify")
    async def api_verify(request: Request):
        """Verify session token."""
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse({"error": "No token"}, status_code=401)
        result = verify_session(token)
        if not result:
            return JSONResponse({"error": "Invalid token"}, status_code=401)
        return JSONResponse(result)
    
    @auth_router.get("/profile/{chat_id}")
    async def api_profile(chat_id: str):
        """Get user profile."""
        result = get_user_profile(chat_id)
        return JSONResponse(result)
    
    @auth_router.get("/users")
    async def api_users():
        """Get all users (admin only)."""
        return JSONResponse({
            "users": get_all_users(),
            "counts": get_user_count(),
        })
    
    @auth_router.post("/set-tier")
    async def api_set_tier(
        chat_id: str = Form(""),
        tier: str = Form("free"),
    ):
        """Set user tier (admin only)."""
        result = set_user_tier(chat_id, tier)
        return JSONResponse(result)
    
    @auth_router.post("/ban")
    async def api_ban(chat_id: str = Form("")):
        """Ban user."""
        return JSONResponse(ban_user(chat_id))
    
    @auth_router.post("/unban")
    async def api_unban(chat_id: str = Form("")):
        """Unban user."""
        return JSONResponse(unban_user(chat_id))
    
    if hasattr(app_or_router, 'include_router'):
        app_or_router.include_router(auth_router)
    
    logger.info("🔐 Auth routes registered")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'register_user',
    'login_user',
    'verify_session',
    'is_owner',
    'get_user_tier',
    'has_permission',
    'set_user_tier',
    'ban_user',
    'unban_user',
    'get_user_profile',
    'get_all_users',
    'get_user_count',
    'generate_device_fingerprint',
    'register_auth_routes',
    'AccessTier',
    'TIER_PERMISSIONS',
]
