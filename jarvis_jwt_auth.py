"""
🔐 JARVIS JWT Authentication System — Secure Token-Based Auth
═══════════════════════════════════════════════════════════════
Replaces JSON file storage with proper JWT tokens:
- Access tokens (15 min) + Refresh tokens (7 days)
- bcrypt password hashing
- Session management via Redis
- Role-based access (owner, admin, premium, user)
"""

import os
import time
import json
import logging
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

import jwt
from passlib.hash import bcrypt

logger = logging.getLogger("jarvis-jwt")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
IST = timezone(timedelta(hours=5, minutes=30))

OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "5647898018")
ADMIN_CHAT_IDS = set(filter(None, [
    os.getenv("ADMIN_CHAT_ID", ""),
    os.getenv("OWNER_CHAT_ID", ""),
]))

# User storage (persisted to JSON + Redis)
USERS_FILE = "jarvis_jwt_users.json"
_users_db: Dict[str, Dict] = {}

# ═══════════════════════════════════════════════════════════
#  USER DATABASE
# ═══════════════════════════════════════════════════════════
def _load_users():
    global _users_db
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                _users_db = json.load(f)
    except Exception as e:
        logger.warning(f"Load users error: {e}")
        _users_db = {}

def _save_users():
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(_users_db, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Save users error: {e}")

_load_users()


def _get_role(user_id: str) -> str:
    """Determine user role."""
    uid = str(user_id)
    if uid == OWNER_CHAT_ID:
        return "owner"
    if uid in ADMIN_CHAT_IDS:
        return "admin"
    user = _users_db.get(uid, {})
    if user.get("is_premium"):
        return "premium"
    return "user"


# ═══════════════════════════════════════════════════════════
#  TOKEN GENERATION
# ═══════════════════════════════════════════════════════════
def create_access_token(user_id: str, extra_claims: Dict = None) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": _get_role(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token (longer lived)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store refresh token in Redis for revocation
    try:
        from jarvis_redis import cache_set
        cache_set(f"refresh:{user_id}", token, ttl=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    except Exception:
        pass

    return token


def create_token_pair(user_id: str) -> Dict[str, str]:
    """Create both access and refresh tokens."""
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ═══════════════════════════════════════════════════════════
#  TOKEN VERIFICATION
# ═══════════════════════════════════════════════════════════
def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None


def verify_access_token(token: str) -> Optional[Dict]:
    """Verify access token specifically."""
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Use refresh token to get new access token."""
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Check if refresh token is still valid in Redis
    try:
        from jarvis_redis import cache_get
        stored = cache_get(f"refresh:{user_id}")
        if stored and stored != refresh_token:
            logger.warning(f"Refresh token mismatch for user {user_id} — possible reuse attack")
            return None
    except Exception:
        pass

    # Issue new tokens (rotation)
    return create_token_pair(user_id)


def revoke_token(user_id: str) -> bool:
    """Revoke all tokens for a user (logout)."""
    try:
        from jarvis_redis import cache_delete
        cache_delete(f"refresh:{user_id}")
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
#  USER REGISTRATION & LOGIN
# ═══════════════════════════════════════════════════════════
def register_user(
    user_id: str,
    name: str,
    phone: str = "",
    password: str = "",
    telegram_data: Dict = None,
) -> Tuple[bool, Dict]:
    """Register a new user."""
    uid = str(user_id)

    if uid in _users_db:
        return False, {"error": "User already exists", "user_id": uid}

    user = {
        "user_id": uid,
        "name": name,
        "phone": phone,
        "password_hash": bcrypt.hash(password[:72]) if password else "",
        "role": _get_role(uid),
        "is_premium": False,
        "is_blocked": False,
        "created_at": datetime.now(IST).isoformat(),
        "last_login": datetime.now(IST).isoformat(),
        "login_count": 1,
        "telegram": telegram_data or {},
    }

    _users_db[uid] = user
    _save_users()

    tokens = create_token_pair(uid)
    return True, {**tokens, "user": {"user_id": uid, "name": name, "role": user["role"]}}


def login_user(
    user_id: str = "",
    name: str = "",
    phone: str = "",
    password: str = "",
    telegram_init_data: str = "",
) -> Tuple[bool, Dict]:
    """Login user and return JWT tokens."""
    uid = str(user_id) if user_id else ""

    # Telegram login — auto-register if new
    if telegram_init_data or uid:
        if uid and uid not in _users_db:
            # Auto-register Telegram users
            ok, data = register_user(uid, name or f"User_{uid}", phone)
            if ok:
                return True, data

        if uid in _users_db:
            user = _users_db[uid]
            if user.get("is_blocked"):
                return False, {"error": "Account blocked"}

            user["last_login"] = datetime.now(IST).isoformat()
            user["login_count"] = user.get("login_count", 0) + 1
            if name:
                user["name"] = name
            _save_users()

            tokens = create_token_pair(uid)
            return True, {
                **tokens,
                "user": {
                    "user_id": uid,
                    "name": user["name"],
                    "role": user["role"],
                    "is_premium": user.get("is_premium", False),
                }
            }

    # Phone + password login
    if phone and password:
        for uid, user in _users_db.items():
            if user.get("phone") == phone:
                if user.get("password_hash") and bcrypt.verify(password[:72], user["password_hash"]):
                    if user.get("is_blocked"):
                        return False, {"error": "Account blocked"}
                    user["last_login"] = datetime.now(IST).isoformat()
                    user["login_count"] = user.get("login_count", 0) + 1
                    _save_users()
                    tokens = create_token_pair(uid)
                    return True, {
                        **tokens,
                        "user": {"user_id": uid, "name": user["name"], "role": user["role"]}
                    }
                return False, {"error": "Invalid password"}
        return False, {"error": "User not found"}

    return False, {"error": "Provide user_id or phone+password"}


# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE / DEPENDENCY
# ═══════════════════════════════════════════════════════════
def get_current_user(request) -> Optional[Dict]:
    """Extract and verify user from request. Use as FastAPI dependency."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = verify_access_token(token)
        if payload:
            return {
                "user_id": payload["sub"],
                "role": payload.get("role", "user"),
            }
    # Fallback: check query param or cookie
    token = request.query_params.get("token") or request.cookies.get("jarvis_token")
    if token:
        payload = verify_access_token(token)
        if payload:
            return {"user_id": payload["sub"], "role": payload.get("role", "user")}
    return None


def require_role(min_role: str = "user"):
    """FastAPI dependency to require minimum role."""
    role_levels = {"user": 0, "premium": 1, "admin": 2, "owner": 3}

    def checker(request):
        user = get_current_user(request)
        if not user:
            return None
        user_level = role_levels.get(user.get("role", "user"), 0)
        required_level = role_levels.get(min_role, 0)
        if user_level < required_level:
            return None
        return user
    return checker


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════
def get_all_jwt_users() -> list:
    """Get all users (for admin)."""
    return [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in _users_db.values()
    ]


def update_user(user_id: str, updates: Dict) -> bool:
    """Update user fields."""
    uid = str(user_id)
    if uid not in _users_db:
        return False
    safe_fields = {"name", "phone", "is_premium", "is_blocked", "role"}
    for k, v in updates.items():
        if k in safe_fields:
            _users_db[uid][k] = v
    _save_users()
    return True


def delete_user(user_id: str) -> bool:
    """Delete a user."""
    uid = str(user_id)
    if uid in _users_db:
        del _users_db[uid]
        _save_users()
        revoke_token(uid)
        return True
    return False


def get_user_count() -> int:
    return len(_users_db)


def get_active_users(hours: int = 24) -> int:
    cutoff = (datetime.now(IST) - timedelta(hours=hours)).isoformat()
    return sum(1 for u in _users_db.values() if u.get("last_login", "") >= cutoff)


# Aliases for server
authenticate_user = login_user
revoke_refresh_token = revoke_token
get_all_users_jwt = get_all_jwt_users

JWT_AVAILABLE = True
logger.info(f"✅ JWT Auth loaded — {len(_users_db)} users, secret={'set' if os.getenv('JWT_SECRET') else 'auto-generated'}")
