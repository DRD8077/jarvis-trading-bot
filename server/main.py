"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║          ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                            ║
║          ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                            ║
║          ██║███████║██████╔╝██║   ██║██║███████╗                            ║
║     ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                           ║
║     ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║                           ║
║      ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                        ║
║                                                                              ║
║          SECURE SERVER — Z++++ Grade Security                                ║
║          Real AI • Real Market Data • Real Portfolio                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Security Layers:
  ✅ JWT Authentication (HS256, short-lived + refresh tokens)
  ✅ Bcrypt Password Hashing (12 rounds)
  ✅ Rate Limiting (per IP, auto-block)
  ✅ Brute Force Protection (account lockout)
  ✅ CORS Configuration
  ✅ Security Headers (HSTS, CSP, X-Frame-Options)
  ✅ Input Sanitization
  ✅ SQL Injection Protection (SQLAlchemy ORM)
  ✅ Audit Logging
  ✅ Request Size Limiting
  ✅ IP Blocking
"""

import os
import sys
import json
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI, Request, Response, HTTPException, Depends,
    status, Query, Body, Path as PathParam,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

# ═══════════════════════════════════════════════════════════════════
#  IMPORTS — Local Modules
# ═══════════════════════════════════════════════════════════════════
from config import (
    SERVER_HOST, SERVER_PORT, DEBUG, CORS_ORIGINS, ENVIRONMENT,
    RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW,
)
from database import (
    init_db, get_db, User, UserSession, Portfolio, Holding,
    Trade, Alert, ChatMessage, AuditLog, BlockedIP, gen_id,
)
from security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    rate_limiter, get_current_user, get_admin_user, get_optional_user,
    check_login_attempts, record_failed_login, record_successful_login,
    sanitize_input, validate_username, validate_password_strength,
    log_audit, SECURITY_HEADERS,
)
import ai_engine
import market_engine

# ═══════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/jarvis_server.log", mode="a"),
    ],
)
logger = logging.getLogger("jarvis.server")


# ═══════════════════════════════════════════════════════════════════
#  APP LIFECYCLE
# ═══════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    logger.info("═" * 60)
    logger.info("  JARVIS SERVER — Initializing...")
    logger.info("═" * 60)
    init_db()
    logger.info("✅ Database ready")
    logger.info("✅ AI Engine loaded")
    logger.info("✅ Market Engine loaded")
    logger.info(f"✅ Environment: {ENVIRONMENT}")
    logger.info(f"✅ Server: {SERVER_HOST}:{SERVER_PORT}")
    logger.info("═" * 60)
    logger.info("  JARVIS SERVER — ONLINE")
    logger.info("═" * 60)
    yield
    logger.info("JARVIS SERVER — Shutting down...")


# ═══════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(
    title="JARVIS Trading Server",
    description="Z++++ Secure AI Trading Platform",
    version="2.0.0",
    docs_url="/docs" if DEBUG else None,  # Disable docs in production
    redoc_url=None,
    lifespan=lifespan,
)

# ═══════════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Master security middleware — rate limiting, headers, logging."""
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else "unknown"
    request_id = secrets.token_hex(8)

    # 1. Rate Limiting
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limited: {client_ip} on {request.url.path}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Slow down."},
            headers={"Retry-After": "60"},
        )

    # 2. Request size check (10MB max)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request too large"},
        )

    # 3. Process request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # 4. Security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    # 5. Custom headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-RateLimit-Remaining"] = str(
        rate_limiter.get_remaining(client_ip)
    )
    response.headers["X-Powered-By"] = "JARVIS/2.0"

    # 6. Access logging
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"{client_ip} {request.method} {request.url.path} "
        f"→ {response.status_code} ({duration:.3f}s)"
    )

    return response


# ═══════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS (Request/Response)
# ═══════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = None

    @validator("username")
    def validate_username(cls, v):
        if not validate_username(v):
            raise ValueError("Username: 3-30 chars, alphanumeric + underscore only")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[str] = None


class TradeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    notes: Optional[str] = None


class AlertRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    condition: str = Field(..., pattern="^(above|below|change_pct)$")
    target_price: float = Field(..., gt=0)


class HoldingRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., gt=0)
    asset_type: str = Field(default="crypto")
    chain: Optional[str] = None
    contract_address: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ═══════════════════════════════════════════════════════════════════════
#   HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "JARVIS Trading Server",
        "version": "2.0.0",
        "security": "Z++++",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/status")
async def server_status():
    """Detailed server status."""
    return {
        "status": "operational",
        "services": {
            "ai_engine": "online" if ai_engine._model else "no_api_key",
            "market_data": "online",
            "database": "online",
            "security": "active",
        },
        "uptime": "running",
        "environment": ENVIRONMENT,
    }


# ═══════════════════════════════════════════════════════════════════════
#   AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/auth/register", status_code=201)
async def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register new user."""
    # Check password strength
    valid, msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # Check if username exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    # Check email if provided
    if req.email:
        existing_email = db.query(User).filter(User.email == req.email).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    user = User(
        id=gen_id(),
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        api_key=secrets.token_hex(32),
    )
    db.add(user)

    # Create default portfolio
    portfolio = Portfolio(
        id=gen_id(),
        user_id=user.id,
        name="Main Portfolio",
    )
    db.add(portfolio)

    db.commit()

    # Generate tokens
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)

    # Store session
    session = UserSession(
        id=gen_id(),
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("User-Agent", "")[:255],
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(session)
    db.commit()

    # Audit log
    log_audit(db, "register", user.id, "auth",
              request.client.host if request.client else None)

    logger.info(f"New user registered: {user.username}")

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "api_key": user.api_key,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login with username and password."""
    user = db.query(User).filter(User.username == req.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check lockout
    if not check_login_attempts(user, db):
        raise HTTPException(
            status_code=423,
            detail=f"Account locked. Try again after {user.locked_until}",
        )

    # Verify password
    if not verify_password(req.password, user.password_hash):
        record_failed_login(user, db)
        remaining = 5 - user.failed_login_attempts
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials. {remaining} attempts remaining.",
        )

    # Success
    record_successful_login(user, db)

    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)

    # Store session
    session = UserSession(
        id=gen_id(),
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("User-Agent", "")[:255],
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(session)
    db.commit()

    log_audit(db, "login", user.id, "auth",
              request.client.host if request.client else None)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/api/auth/refresh")
async def refresh_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Get new access token using refresh token."""
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    # Verify session exists and is not revoked
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_revoked == False,
    ).first()

    if not session:
        raise HTTPException(status_code=401, detail="Session expired or revoked")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotate refresh token
    session.is_revoked = True
    new_refresh = create_refresh_token(user.id)
    new_session = UserSession(
        id=gen_id(),
        user_id=user.id,
        refresh_token=new_refresh,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("User-Agent", "")[:255],
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(new_session)
    db.commit()

    return {
        "access_token": create_access_token(user.id, user.username, user.role),
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@app.post("/api/auth/logout")
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout — revoke all sessions."""
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_revoked == False,
    ).update({"is_revoked": True})
    db.commit()

    log_audit(db, "logout", user.id, "auth",
              request.client.host if request.client else None)

    return {"message": "Logged out successfully"}


@app.post("/api/auth/change-password")
async def change_password(
    req: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password."""
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    valid, msg = validate_password_strength(req.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    user.password_hash = hash_password(req.new_password)

    # Revoke all sessions (force re-login)
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
    ).update({"is_revoked": True})

    db.commit()
    return {"message": "Password changed. Please login again."}


@app.get("/api/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


# ═══════════════════════════════════════════════════════════════════════
#   AI CHAT ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/ai/chat")
async def ai_chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with JARVIS AI — Real Gemini-powered responses."""
    message = sanitize_input(req.message, max_length=5000)

    # Get conversation history
    history_records = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history_records)
    ]

    # Get market context
    market_context = await market_engine.get_market_summary()

    # Generate AI response
    response = await ai_engine.chat(
        message=message,
        history=history,
        market_context=market_context,
        user_name=user.username,
    )

    # Store conversation
    user_msg = ChatMessage(
        id=gen_id(), user_id=user.id, role="user", content=message,
    )
    ai_msg = ChatMessage(
        id=gen_id(), user_id=user.id, role="assistant", content=response,
    )
    db.add(user_msg)
    db.add(ai_msg)
    db.commit()

    return {
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
        "market_context": market_context,
    }


@app.post("/api/ai/analyze/{symbol}")
async def ai_analyze(
    symbol: str = PathParam(..., min_length=1, max_length=20),
    user: User = Depends(get_current_user),
):
    """AI analysis for a specific asset."""
    # Get price data
    price_data = await market_engine.get_crypto_price(symbol.lower())
    if "error" in price_data:
        # Try Binance
        binance_data = await market_engine.get_binance_ticker(f"{symbol.upper()}USDT")
        if binance_data:
            price_data = binance_data

    analysis = await ai_engine.analyze_market(symbol.upper(), price_data)

    return {
        "symbol": symbol.upper(),
        "price_data": price_data,
        "analysis": analysis,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/ai/signal/{symbol}")
async def ai_signal(
    symbol: str = PathParam(..., min_length=1, max_length=20),
    user: User = Depends(get_current_user),
):
    """Get AI trading signal."""
    price_data = await market_engine.get_crypto_price(symbol.lower())
    if "error" in price_data:
        binance_data = await market_engine.get_binance_ticker(f"{symbol.upper()}USDT")
        if binance_data:
            price_data = binance_data

    signal = await ai_engine.generate_signal(symbol.upper(), price_data)

    return {
        "symbol": symbol.upper(),
        "signal": signal,
        "price_data": price_data,
        "disclaimer": "This is AI-generated analysis, not financial advice. Always DYOR.",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/ai/history")
async def chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chat history."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat() if m.created_at else None,
            }
            for m in reversed(messages)
        ]
    }


# ═══════════════════════════════════════════════════════════════════════
#   MARKET DATA ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/market/top")
async def market_top(
    limit: int = Query(default=100, ge=1, le=250),
    currency: str = Query(default="usd"),
):
    """Get top cryptocurrencies — No auth required."""
    data = await market_engine.get_top_cryptos(limit, currency)
    return {"coins": data, "count": len(data)}


@app.get("/api/market/price/{coin_id}")
async def market_price(coin_id: str):
    """Get detailed price for a coin."""
    data = await market_engine.get_crypto_price(coin_id)
    return data


@app.get("/api/market/search")
async def market_search(q: str = Query(..., min_length=1, max_length=50)):
    """Search cryptocurrencies."""
    results = await market_engine.search_crypto(q)
    return {"results": results}


@app.get("/api/market/trending")
async def market_trending():
    """Get trending cryptocurrencies."""
    coins = await market_engine.get_trending()
    return {"trending": coins}


@app.get("/api/market/global")
async def market_global():
    """Get global crypto market stats."""
    data = await market_engine.get_global_market()
    return data


@app.get("/api/market/fear-greed")
async def market_fear_greed():
    """Get Fear & Greed Index."""
    return await market_engine.get_fear_greed()


@app.get("/api/market/history/{coin_id}")
async def market_history(
    coin_id: str,
    days: int = Query(default=30, ge=1, le=365),
    currency: str = Query(default="usd"),
):
    """Get price history for charts."""
    data = await market_engine.get_price_history(coin_id, days, currency)
    return data


@app.get("/api/market/ticker/{symbol}")
async def binance_ticker(symbol: str):
    """Get Binance real-time ticker."""
    data = await market_engine.get_binance_ticker(symbol.upper())
    return data


@app.get("/api/market/klines/{symbol}")
async def binance_klines(
    symbol: str,
    interval: str = Query(default="1h"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get Binance candlestick data."""
    data = await market_engine.get_binance_klines(symbol.upper(), interval, limit)
    return {"candles": data}


@app.get("/api/market/whales")
async def whale_alerts():
    """Get whale transactions."""
    data = await market_engine.get_whale_transactions()
    return {"whales": data}


@app.get("/api/market/dex/search")
async def dex_search(q: str = Query(..., min_length=1)):
    """Search DEX tokens."""
    results = await market_engine.search_dex_tokens(q)
    return {"pairs": results}


@app.get("/api/market/dex/new")
async def dex_new_pairs(chain: str = Query(default="solana")):
    """Get new DEX pairs."""
    pairs = await market_engine.get_new_dex_pairs(chain)
    return {"pairs": pairs}


# ═══════════════════════════════════════════════════════════════════════
#   PORTFOLIO ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/portfolio")
async def get_portfolios(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's portfolios."""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()

    result = []
    for p in portfolios:
        holdings = db.query(Holding).filter(Holding.portfolio_id == p.id).all()
        total_value = 0
        total_invested = 0
        holdings_data = []

        for h in holdings:
            # Get current price
            try:
                price_data = await market_engine.get_crypto_price(h.symbol.lower())
                current_price = price_data.get("price", h.current_price)
            except Exception:
                current_price = h.current_price

            value = h.quantity * current_price
            invested = h.quantity * h.avg_buy_price
            pnl = value - invested
            pnl_pct = ((current_price - h.avg_buy_price) / h.avg_buy_price * 100) if h.avg_buy_price > 0 else 0

            total_value += value
            total_invested += invested

            holdings_data.append({
                "id": h.id,
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_buy_price": h.avg_buy_price,
                "current_price": current_price,
                "value": round(value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "asset_type": h.asset_type,
            })

        result.append({
            "id": p.id,
            "name": p.name,
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_pnl": round(total_value - total_invested, 2),
            "total_pnl_pct": round(
                ((total_value - total_invested) / total_invested * 100)
                if total_invested > 0 else 0, 2
            ),
            "holdings": holdings_data,
        })

    return {"portfolios": result}


@app.post("/api/portfolio/holding")
async def add_holding(
    req: HoldingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add or update a holding."""
    # Get first portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(id=gen_id(), user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()

    # Check if holding exists
    existing = db.query(Holding).filter(
        Holding.portfolio_id == portfolio.id,
        Holding.symbol == req.symbol.upper(),
    ).first()

    if existing:
        # Average down/up
        total_qty = existing.quantity + req.quantity
        total_cost = (existing.quantity * existing.avg_buy_price) + (req.quantity * req.avg_buy_price)
        existing.quantity = total_qty
        existing.avg_buy_price = total_cost / total_qty if total_qty > 0 else 0
        existing.updated_at = datetime.utcnow()
    else:
        holding = Holding(
            id=gen_id(),
            portfolio_id=portfolio.id,
            symbol=req.symbol.upper(),
            quantity=req.quantity,
            avg_buy_price=req.avg_buy_price,
            asset_type=req.asset_type,
            chain=req.chain,
            contract_address=req.contract_address,
        )
        db.add(holding)

    db.commit()
    return {"message": f"Holding {req.symbol.upper()} updated"}


@app.delete("/api/portfolio/holding/{holding_id}")
async def remove_holding(
    holding_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a holding."""
    holding = db.query(Holding).join(Portfolio).filter(
        Holding.id == holding_id,
        Portfolio.user_id == user.id,
    ).first()

    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    db.delete(holding)
    db.commit()
    return {"message": "Holding removed"}


@app.post("/api/portfolio/trade")
async def record_trade(
    req: TradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a trade."""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(id=gen_id(), user_id=user.id)
        db.add(portfolio)

    trade = Trade(
        id=gen_id(),
        portfolio_id=portfolio.id,
        symbol=req.symbol.upper(),
        side=req.side,
        quantity=req.quantity,
        price=req.price,
        total_value=req.quantity * req.price,
        notes=sanitize_input(req.notes) if req.notes else None,
    )
    db.add(trade)
    db.commit()

    return {
        "trade": {
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "total_value": trade.total_value,
        }
    }


@app.get("/api/portfolio/trades")
async def get_trades(
    limit: int = Query(default=50, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get trade history."""
    trades = (
        db.query(Trade)
        .join(Portfolio)
        .filter(Portfolio.user_id == user.id)
        .order_by(Trade.executed_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "trades": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "quantity": t.quantity,
                "price": t.price,
                "total_value": t.total_value,
                "notes": t.notes,
                "executed_at": t.executed_at.isoformat() if t.executed_at else None,
            }
            for t in trades
        ]
    }


# ═══════════════════════════════════════════════════════════════════════
#   ALERTS ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/alerts")
async def get_alerts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's price alerts."""
    alerts = db.query(Alert).filter(Alert.user_id == user.id).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "symbol": a.symbol,
                "condition": a.condition,
                "target_price": a.target_price,
                "is_active": a.is_active,
                "is_triggered": a.is_triggered,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
    }


@app.post("/api/alerts")
async def create_alert(
    req: AlertRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create price alert."""
    alert = Alert(
        id=gen_id(),
        user_id=user.id,
        symbol=req.symbol.upper(),
        condition=req.condition,
        target_price=req.target_price,
    )
    db.add(alert)
    db.commit()
    return {"alert": {"id": alert.id, "symbol": alert.symbol, "condition": alert.condition}}


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id, Alert.user_id == user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}


# ═══════════════════════════════════════════════════════════════════════
#   ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/admin/users")
async def admin_list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ]
    }


@app.get("/api/admin/audit")
async def admin_audit_log(
    limit: int = Query(default=100, ge=1, le=1000),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get audit log (admin only)."""
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "logs": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "action": l.action,
                "resource": l.resource,
                "ip": l.ip_address,
                "timestamp": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    }


@app.post("/api/admin/block-ip")
async def admin_block_ip(
    ip: str = Body(..., embed=True),
    reason: str = Body(default="Manual block", embed=True),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Block an IP address (admin only)."""
    blocked = BlockedIP(ip=ip, reason=reason)
    db.merge(blocked)
    db.commit()
    rate_limiter.block_ip(ip, duration=86400)  # 24 hours
    return {"message": f"IP {ip} blocked"}


# ═══════════════════════════════════════════════════════════════════════
#   ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG,
        log_level="info",
        access_log=True,
        workers=1,
        timeout_keep_alive=30,
    )
