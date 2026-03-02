"""
JARVIS SECURITY v4.0 — JWT, Bcrypt, Rate Limiting, Audit
"""
import re, time, logging
from datetime import datetime, timedelta
from collections import defaultdict
import bcrypt, jwt
from fastapi import Request, HTTPException, Depends
from config import (JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS, BCRYPT_ROUNDS, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW,
    MAX_LOGIN_ATTEMPTS, LOGIN_LOCKOUT_MINUTES)

logger = logging.getLogger("jarvis.security")

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()

def verify_password(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), hashed.encode())
    except: return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "access"
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["iat"] = datetime.utcnow()
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "refresh"
    to_encode["exp"] = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["iat"] = datetime.utcnow()
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try: return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError: raise HTTPException(401, "Invalid token")

def validate_password_strength(password: str) -> dict:
    if len(password) < 8:
        return {"valid": False, "reason": "Password must be at least 8 characters"}
    return {"valid": True, "reason": "OK"}

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    # Remove potential script tags and SQL injection patterns
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'[;\-\-]|/\*|\*/', '', text)
    return text.strip()[:5000]

def log_audit(db, user_id: str, action: str, details: str = "", ip: str = ""):
    try:
        from database import AuditLog
        db.add(AuditLog(user_id=user_id, action=action, details=details, ip_address=ip))
        db.commit()
    except:
        pass

class RateLimiter:
    def __init__(self, max_requests=300, window=60):
        self._requests = defaultdict(list)
        self._blocked = {}
        self.max_requests = max_requests
        self.window = window
    
    def allow(self, ip: str) -> bool:
        now = time.time()
        if ip in self._blocked:
            if now < self._blocked[ip]: return False
            del self._blocked[ip]
        self._requests[ip] = [t for t in self._requests[ip] if now - t < self.window]
        if len(self._requests[ip]) >= self.max_requests: return False
        self._requests[ip].append(now)
        return True
    
    def is_allowed(self, ip: str) -> bool:
        return self.allow(ip)
    
    def block_ip(self, ip: str, dur: int = 3600):
        self._blocked[ip] = time.time() + dur

def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    payload = decode_token(auth[7:])
    return payload

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
