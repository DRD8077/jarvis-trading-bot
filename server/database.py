"""
JARVIS DATABASE v4.0 — SQLAlchemy Models + Session Management
"""
import uuid, time
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def gen_id(): return str(uuid.uuid4())[:12]

# ═══ MODELS ═══

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    email = Column(String, default="")
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    refresh_token = Column(String, unique=True)
    ip_address = Column(String, default="")
    user_agent = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    name = Column(String, default="Main Portfolio")
    total_value = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Holding(Base):
    __tablename__ = "holdings"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    symbol = Column(String)
    name = Column(String, default="")
    quantity = Column(Float, default=0)
    avg_buy_price = Column(Float, default=0)
    current_price = Column(Float, default=0)
    pnl = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    symbol = Column(String)
    side = Column(String)  # buy/sell
    quantity = Column(Float)
    price = Column(Float)
    total = Column(Float)
    status = Column(String, default="completed")
    pnl = Column(Float, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    symbol = Column(String)
    condition = Column(String)  # above/below
    target_price = Column(Float)
    current_price = Column(Float, default=0)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    role = Column(String)  # user/assistant
    content = Column(Text)
    model = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    symbol = Column(String)
    name = Column(String, default="")
    added_at = Column(DateTime, default=datetime.utcnow)

class PnlEntry(Base):
    __tablename__ = "pnl_journal"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    symbol = Column(String)
    side = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float, default=0)
    quantity = Column(Float)
    pnl = Column(Float, default=0)
    status = Column(String, default="open")  # open/closed
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, default="system")
    action = Column(String)
    details = Column(Text, default="")
    ip_address = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryStore(Base):
    __tablename__ = "memory_store"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, index=True)
    key = Column(String)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class BlockedIP(Base):
    __tablename__ = "blocked_ips"
    id = Column(String, primary_key=True, default=gen_id)
    ip_address = Column(String, unique=True)
    reason = Column(String, default="")
    blocked_at = Column(DateTime, default=datetime.utcnow)

# ═══ INIT ═══
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
