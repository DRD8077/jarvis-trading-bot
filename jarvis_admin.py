"""
🔐 JARVIS ADMIN — Approval System + Per-User Personal AI Assistant
═══════════════════════════════════════════════════════════════════
- DEEPAK KUMAR is the ADMIN/BOSS of JARVIS
- Users who need special permissions → approval request sent to Deepak
- Each user gets their own personal AI assistant experience
- JARVIS acts as SPOC for EVERY user — personal financial advisor + coder + helper

Author: David Crew AI (Boss: Deepak Kumar)
"""

import os
import json
import time
import logging
import threading
from typing import Optional, Dict, List
from datetime import datetime

# Load .env file FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

# Web server imports
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio

logger = logging.getLogger("jarvis_admin")

# ═══════════════════════════════════════════════════════════
#  ADMIN CONFIG
# ═══════════════════════════════════════════════════════════

ADMIN_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", os.environ.get("ADMIN_CHAT_ID", "5647898018")))
ADMIN_NAME = "Deepak Kumar"

# Storage files
USERS_FILE = "jarvis_users.json"
APPROVALS_FILE = "jarvis_approvals.json"
USER_PREFS_FILE = "jarvis_user_prefs.json"

# User tiers
TIER_FREE = "free"       # Basic access (AI chat, news, weather, search)
TIER_PREMIUM = "premium"  # Full access (coding, trading signals, portfolio)
TIER_ADMIN = "admin"      # Full admin access (Deepak only)

# Features that require approval
APPROVAL_REQUIRED = {
    "coding": "💻 Programming/Code Generation",
    "trading_live": "📊 Live Trading Signals",
    "portfolio_write": "📈 Portfolio Management (Buy/Sell)",
    "github_push": "🔗 GitHub Push Access",
    "admin_panel": "🔐 Admin Panel Access",
    "broadcast": "📢 Broadcast Messages",
    "api_access": "🔑 Direct API Access",
}

# Features available to everyone
FREE_FEATURES = {
    "ai_chat", "news", "weather", "search", "crypto_prices",
    "nifty_analysis", "song_identify", "image_generate",
    "memory", "voice", "portfolio_view",
}


# ═══════════════════════════════════════════════════════════
#  USER DATABASE
# ═══════════════════════════════════════════════════════════

def _load_users() -> Dict:
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_users(users: Dict):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"[ADMIN] Save users error: {e}")


def register_user(chat_id: int, first_name: str = "", username: str = "") -> Dict:
    """Register a new user or update existing."""
    users = _load_users()
    cid = str(chat_id)
    
    is_new = cid not in users
    
    if cid not in users:
        users[cid] = {
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "tier": TIER_ADMIN if chat_id == ADMIN_CHAT_ID else TIER_FREE,
            "registered": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_count": 0,
            "approved_features": list(FREE_FEATURES),
            "language": "hindi",
            "alerts_on": True,
        }
        logger.info(f"[ADMIN] New user registered: {chat_id} ({first_name})")
    else:
        users[cid]["last_active"] = datetime.now().isoformat()
        users[cid]["message_count"] = users[cid].get("message_count", 0) + 1
        if first_name:
            users[cid]["first_name"] = first_name
        if username:
            users[cid]["username"] = username
    
    _save_users(users)
    
    # Notify web clients of new user
    if is_new:
        import asyncio
        asyncio.create_task(notify_new_user(users[cid]))
    
    return users[cid]


def get_user(chat_id: int) -> Optional[Dict]:
    """Get user info."""
    users = _load_users()
    return users.get(str(chat_id))


def get_user_tier(chat_id: int) -> str:
    """Get user tier."""
    if chat_id == ADMIN_CHAT_ID:
        return TIER_ADMIN
    user = get_user(chat_id)
    return user.get("tier", TIER_FREE) if user else TIER_FREE


def is_admin(chat_id: int) -> bool:
    """Check if user is admin."""
    return chat_id == ADMIN_CHAT_ID


def has_feature(chat_id: int, feature: str) -> bool:
    """Check if user has access to a feature."""
    if chat_id == ADMIN_CHAT_ID:
        return True  # Admin has ALL features
    
    if feature in FREE_FEATURES:
        return True  # Free features available to all
    
    user = get_user(chat_id)
    if not user:
        return False
    
    return feature in user.get("approved_features", [])


def get_all_users() -> List[Dict]:
    """Get all registered users."""
    users = _load_users()
    return list(users.values())


def get_user_count() -> int:
    """Get total user count."""
    return len(_load_users())


# ═══════════════════════════════════════════════════════════
#  APPROVAL SYSTEM
# ═══════════════════════════════════════════════════════════

def _load_approvals() -> Dict:
    try:
        if os.path.exists(APPROVALS_FILE):
            with open(APPROVALS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_approvals(approvals: Dict):
    try:
        with open(APPROVALS_FILE, "w") as f:
            json.dump(approvals, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"[ADMIN] Save approvals error: {e}")


def request_approval(chat_id: int, feature: str, reason: str = "") -> Dict:
    """User requests approval for a premium feature.
    Sends notification to Admin (Deepak Kumar).
    
    Returns: {"status": "pending"|"already_approved"|"auto_approved", "message": str}
    """
    # Admin gets auto-approval
    if chat_id == ADMIN_CHAT_ID:
        return {"status": "auto_approved", "message": "✅ Admin auto-approved!"}
    
    # Check if already approved
    if has_feature(chat_id, feature):
        return {"status": "already_approved", "message": "✅ Already approved!"}
    
    # Check if feature exists
    if feature not in APPROVAL_REQUIRED:
        return {"status": "error", "message": f"❌ Unknown feature: {feature}"}
    
    # Create approval request
    approvals = _load_approvals()
    req_id = f"{chat_id}_{feature}_{int(time.time())}"
    
    user = get_user(chat_id)
    user_name = user.get("first_name", "Unknown") if user else "Unknown"
    
    approvals[req_id] = {
        "id": req_id,
        "chat_id": chat_id,
        "user_name": user_name,
        "feature": feature,
        "feature_name": APPROVAL_REQUIRED.get(feature, feature),
        "reason": reason,
        "status": "pending",
        "requested": datetime.now().isoformat(),
    }
    _save_approvals(approvals)
    
    # Notify web clients of new approval request
    import asyncio
    asyncio.create_task(notify_new_approval(approvals[req_id]))
    
    return {
        "status": "pending",
        "req_id": req_id,
        "message": f"📋 Request submitted! {ADMIN_NAME} sir ko notify kiya gaya hai.",
        "admin_notification": format_approval_notification(approvals[req_id]),
    }


def approve_request(req_id: str) -> Dict:
    """Admin approves a request."""
    approvals = _load_approvals()
    req = approvals.get(req_id)
    if not req:
        return {"status": "error", "message": "❌ Request not found"}
    
    req["status"] = "approved"
    req["approved_at"] = datetime.now().isoformat()
    approvals[req_id] = req
    _save_approvals(approvals)
    
    # Grant feature to user
    users = _load_users()
    cid = str(req["chat_id"])
    if cid in users:
        features = users[cid].get("approved_features", list(FREE_FEATURES))
        if req["feature"] not in features:
            features.append(req["feature"])
        users[cid]["approved_features"] = features
        _save_users(users)
    
    # Notify web clients
    import asyncio
    asyncio.create_task(notify_stats_update())
    
    return {
        "status": "approved",
        "chat_id": req["chat_id"],
        "feature": req["feature"],
        "message": f"✅ Approved: {req['feature_name']} for {req['user_name']}"
    }


def reject_request(req_id: str, reason: str = "") -> Dict:
    """Admin rejects a request."""
    approvals = _load_approvals()
    req = approvals.get(req_id)
    if not req:
        return {"status": "error", "message": "❌ Request not found"}
    
    req["status"] = "rejected"
    req["rejected_at"] = datetime.now().isoformat()
    req["reject_reason"] = reason
    approvals[req_id] = req
    _save_approvals(approvals)
    
    # Notify web clients
    import asyncio
    asyncio.create_task(notify_stats_update())
    
    return {
        "status": "rejected",
        "chat_id": req["chat_id"],
        "message": f"❌ Rejected: {req['feature_name']} for {req['user_name']}"
    }


def get_pending_approvals() -> List[Dict]:
    """Get all pending approval requests."""
    approvals = _load_approvals()
    return [r for r in approvals.values() if r.get("status") == "pending"]


def format_approval_notification(req: Dict) -> str:
    """Format approval request for Admin notification."""
    return (
        f"🔔 *JARVIS Approval Request* 🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *User:* {req.get('user_name', 'Unknown')}\n"
        f"🆔 *Chat ID:* {req.get('chat_id')}\n"
        f"🔑 *Feature:* {req.get('feature_name', req.get('feature'))}\n"
        f"💬 *Reason:* {req.get('reason', 'No reason given')}\n"
        f"📅 *Time:* {req.get('requested', '')[:19]}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Approve: `/approve {req['id']}`\n"
        f"❌ Reject: `/reject {req['id']}`\n"
    )


# ═══════════════════════════════════════════════════════════
#  USER PREFERENCES (Per-User Personal Customization)
# ═══════════════════════════════════════════════════════════

def _load_prefs() -> Dict:
    try:
        if os.path.exists(USER_PREFS_FILE):
            with open(USER_PREFS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_prefs(prefs: Dict):
    try:
        with open(USER_PREFS_FILE, "w") as f:
            json.dump(prefs, f, indent=2, default=str)
    except Exception:
        pass


def get_user_prefs(chat_id: int) -> Dict:
    """Get user's personal preferences."""
    prefs = _load_prefs()
    return prefs.get(str(chat_id), {
        "language": "hindi",
        "voice_enabled": True,
        "alert_types": ["crypto", "nifty", "news"],
        "risk_appetite": "moderate",
        "investment_amount": 2000,
        "favorite_stocks": [],
        "favorite_crypto": [],
        "city": "Mumbai",
        "greeting_name": "",
    })


def set_user_pref(chat_id: int, key: str, value) -> bool:
    """Set a user preference."""
    prefs = _load_prefs()
    cid = str(chat_id)
    if cid not in prefs:
        prefs[cid] = get_user_prefs(chat_id)
    prefs[cid][key] = value
    _save_prefs(prefs)
    return True


def format_user_profile(chat_id: int) -> str:
    """Format user's personal profile for display."""
    user = get_user(chat_id)
    prefs = get_user_prefs(chat_id)
    tier = get_user_tier(chat_id)
    
    tier_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑"}.get(tier, "🆓")
    tier_name = {"free": "Free", "premium": "Premium", "admin": "Admin/Boss"}.get(tier, "Free")
    
    name = user.get("first_name", "Friend") if user else "Friend"
    msgs = user.get("message_count", 0) if user else 0
    registered = user.get("registered", "")[:10] if user else "Today"
    lang = prefs.get("language", "hindi").title()
    city = prefs.get("city", "Mumbai")
    risk = prefs.get("risk_appetite", "moderate").title()
    investment = prefs.get("investment_amount", 2000)
    
    features_count = len(user.get("approved_features", [])) if user else len(FREE_FEATURES)
    
    msg = (
        f"👤 *Your JARVIS Profile* 👤\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌸 *Name:* {name}\n"
        f"{tier_emoji} *Tier:* {tier_name}\n"
        f"💬 *Messages:* {msgs:,}\n"
        f"📅 *Since:* {registered}\n"
        f"🌍 *Language:* {lang}\n"
        f"📍 *City:* {city}\n"
        f"⚖️ *Risk:* {risk}\n"
        f"💰 *Investment:* ₹{investment:,}\n"
        f"🔑 *Features:* {features_count} active\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if tier == TIER_FREE:
        msg += (
            f"\n💡 *Upgrade to Premium:*\n"
            f"Ask JARVIS for: `/upgrade`\n"
            f"Boss {ADMIN_NAME} sir will approve! 🌸\n"
        )
    
    return msg


# ═══════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════

def format_admin_dashboard() -> str:
    """Format admin dashboard for Deepak Boss."""
    users = _load_users()
    pending = get_pending_approvals()
    
    total = len(users)
    active_24h = sum(1 for u in users.values() 
        if u.get("last_active", "") > (datetime.now().isoformat()[:10]))
    admins = sum(1 for u in users.values() if u.get("tier") == TIER_ADMIN)
    premiums = sum(1 for u in users.values() if u.get("tier") == TIER_PREMIUM)
    
    msg = (
        f"👑 *JARVIS Admin Dashboard — Boss {ADMIN_NAME}* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Users:* {total}\n"
        f"📱 *Active Today:* {active_24h}\n"
        f"👑 *Admins:* {admins}\n"
        f"⭐ *Premium:* {premiums}\n"
        f"🆓 *Free:* {total - admins - premiums}\n"
        f"📋 *Pending Approvals:* {len(pending)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if pending:
        msg += f"\n🔔 *Pending Approval Requests:*\n"
        for req in pending[:5]:
            msg += (
                f"• {req.get('user_name', '?')} → {req.get('feature_name', '?')}\n"
                f"  ✅ `/approve {req['id']}` | ❌ `/reject {req['id']}`\n"
            )
        if len(pending) > 5:
            msg += f"  ... +{len(pending)-5} more\n"
    
    msg += (
        f"\n*Commands:*\n"
        f"• `/users` — All users list\n"
        f"• `/approve <id>` — Approve request\n"
        f"• `/reject <id>` — Reject request\n"
        f"• `/grant <chat_id> <feature>` — Direct grant\n"
        f"• `/upgrade <chat_id>` — Upgrade to premium\n"
        f"• `/broadcast <msg>` — Message all users\n"
    )
    
    return msg


def grant_feature(chat_id: int, feature: str) -> str:
    """Admin directly grants a feature to a user."""
    users = _load_users()
    cid = str(chat_id)
    if cid not in users:
        return f"❌ User {chat_id} not found. They need to /start first."
    
    features = users[cid].get("approved_features", list(FREE_FEATURES))
    if feature not in features:
        features.append(feature)
    users[cid]["approved_features"] = features
    _save_users(users)
    
    return f"✅ Granted `{feature}` to {users[cid].get('first_name', chat_id)}"


def upgrade_user(chat_id: int) -> str:
    """Upgrade user to premium tier."""
    users = _load_users()
    cid = str(chat_id)
    if cid not in users:
        return f"❌ User {chat_id} not found."
    
    users[cid]["tier"] = TIER_PREMIUM
    # Grant all features
    all_features = list(FREE_FEATURES) + list(APPROVAL_REQUIRED.keys())
    users[cid]["approved_features"] = all_features
    _save_users(users)
    
    # Notify web clients
    import asyncio
    asyncio.create_task(notify_stats_update())
    
    return f"⭐ Upgraded {users[cid].get('first_name', chat_id)} to Premium!"


# ═══════════════════════════════════════════════════════════
#  ALERT ON/OFF MANAGEMENT (Per-User)
# ═══════════════════════════════════════════════════════════

def set_alerts(chat_id: int, enabled: bool) -> str:
    """
    PROPER ON/OFF toggle for alerts. 
    When OFF: actually stops all background threads from sending to this user.
    When ON: resumes alerts.
    """
    users = _load_users()
    cid = str(chat_id)
    
    if cid not in users:
        register_user(chat_id)
        users = _load_users()
    
    users[cid]["alerts_on"] = enabled
    _save_users(users)
    
    # Also update the stopped users file for nuclear stop
    try:
        stop_file = "jarvis_stopped_users.json"
        stopped = {}
        if os.path.exists(stop_file):
            with open(stop_file, "r") as f:
                stopped = json.load(f)
        
        if enabled:
            # Start: remove from stopped
            stopped.pop(cid, None)
        else:
            # Stop: add to stopped
            stopped[cid] = True
        
        with open(stop_file, "w") as f:
            json.dump(stopped, f)
    except Exception as e:
        logger.error(f"[ADMIN] Alert toggle error: {e}")
    
    status = "ON ✅" if enabled else "OFF 🔴"
    return (
        f"{'🟢' if enabled else '🛑'} *Alerts {status}*\n\n"
        f"{'✅ Crypto alerts: ON' if enabled else '❌ Crypto alerts: OFF'}\n"
        f"{'✅ Market signals: ON' if enabled else '❌ Market signals: OFF'}\n"
        f"{'✅ Auto notifications: ON' if enabled else '❌ Auto notifications: OFF'}\n"
        f"{'✅ Airdrop alerts: ON' if enabled else '❌ Airdrop alerts: OFF'}\n"
        f"{'✅ DexTools alerts: ON' if enabled else '❌ DexTools alerts: OFF'}\n"
        f"{'✅ Web3 signals: ON' if enabled else '❌ Web3 signals: OFF'}\n"
    )


def are_alerts_on(chat_id: int) -> bool:
    """Check if alerts are on for this user."""
    user = get_user(chat_id)
    if user:
        return user.get("alerts_on", True)
    return True  # Default: on for new users


def get_jarvis_user_context(chat_id: int) -> str:
    """Get user context string for JARVIS AI — makes JARVIS aware of users.
    Injected into the AI system prompt so JARVIS knows who's talking.
    """
    users = _load_users()
    total = len(users)
    user = users.get(str(chat_id))
    
    if not user:
        return f"JARVIS ECOSYSTEM: {total} registered users. Current user is new."
    
    name = user.get("first_name", "Friend")
    tier = user.get("tier", "free")
    msgs = user.get("message_count", 0)
    since = user.get("registered", "")[:10]
    
    # Build user list summary
    user_names = []
    for u in users.values():
        fn = u.get("first_name", "")
        if fn:
            tier_e = "👑" if u.get("tier") == "admin" else "⭐" if u.get("tier") == "premium" else ""
            user_names.append(f"{fn}{tier_e}")
    
    names_str = ", ".join(user_names[:20])
    
    return (
        f"JARVIS ECOSYSTEM STATUS:\n"
        f"- Total registered users: {total}\n"
        f"- User names: {names_str}\n"
        f"- Current user: {name} (tier: {tier}, messages: {msgs}, since: {since})\n"
        f"- Admin/Boss: {ADMIN_NAME}\n"
        f"When asked about users or who uses JARVIS, mention these details."
    )


# ═══════════════════════════════════════════════════════════
#  MODULE STATUS
# ═══════════════════════════════════════════════════════════

ADMIN_SYSTEM_AVAILABLE = True

logger.info(f"[ADMIN] 🔐 JARVIS Admin System loaded — Boss: {ADMIN_NAME} (ID: {ADMIN_CHAT_ID})")


# ═══════════════════════════════════════════════════════════
#  WEB ADMIN PANEL
# ═══════════════════════════════════════════════════════════

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

async def broadcast_message(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            active_connections.remove(connection)

def get_dashboard_stats():
    """Get current dashboard statistics."""
    users = _load_users()
    pending = get_pending_approvals()
    
    total = len(users)
    active_24h = sum(1 for u in users.values() 
        if u.get("last_active", "") > (datetime.now().isoformat()[:10]))
    premiums = sum(1 for u in users.values() if u.get("tier") == TIER_PREMIUM)
    
    return {
        "total_users": total,
        "active_today": active_24h,
        "premium_users": premiums,
        "pending_approvals": len(pending),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Background task for periodic stats updates
async def periodic_stats_update():
    """Periodically broadcast stats updates to all connected clients."""
    while True:
        await asyncio.sleep(30)  # Update every 30 seconds
        if active_connections:  # Only if there are active connections
            stats = get_dashboard_stats()
            await broadcast_message({"type": "stats_update", "stats": stats})

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(periodic_stats_update())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(title="JARVIS Admin Panel", description="Real-time admin dashboard for JARVIS", lifespan=lifespan)

# CORS middleware — required for Telegram Mini App WebView
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ═══ MINI APP API ROUTES (v6 — MEGA INTEGRATED) ═══
try:
    from miniapp_api import router as miniapp_router
    app.include_router(miniapp_router)
    logger.info("✅ Mini App API v6 MEGA loaded — ALL 25+ engines connected")
except Exception as e:
    logger.warning(f"⚠️ Mini App API not loaded: {e}")

# ═══ SERVE REACT MINI APP (built from telegram-mini-app/dist) ═══
import os as _os
_REACT_DIST = _os.path.join(_os.path.dirname(__file__) or '.', 'telegram-mini-app', 'dist')
_REACT_ASSETS = _os.path.join(_REACT_DIST, 'assets')

if _os.path.isdir(_REACT_ASSETS):
    app.mount("/miniapp/assets", StaticFiles(directory=_REACT_ASSETS), name="miniapp_assets")
    logger.info(f"✅ React assets mounted from {_REACT_ASSETS}")

# Serve vite.svg and other root static files
_REACT_VITE_SVG = _os.path.join(_REACT_DIST, 'vite.svg')
if _os.path.isfile(_REACT_VITE_SVG):
    from fastapi.responses import FileResponse as _FileResponse
    @app.get("/vite.svg")
    async def serve_vite_svg():
        return _FileResponse(_REACT_VITE_SVG)

@app.get("/miniapp", response_class=HTMLResponse)
async def serve_miniapp(request: Request):
    """Serve React SPA index.html."""
    react_index = _os.path.join(_REACT_DIST, 'index.html')
    if _os.path.isfile(react_index):
        with open(react_index, 'r') as f:
            return HTMLResponse(content=f.read())
    return templates.TemplateResponse("miniapp.html", {"request": request})

@app.get("/miniapp/{full_path:path}", response_class=HTMLResponse)
async def serve_miniapp_spa(request: Request, full_path: str = ""):
    """SPA fallback — all sub-routes serve React index.html."""
    # Check if it's a static file first
    static_file = _os.path.join(_REACT_DIST, full_path)
    if _os.path.isfile(static_file):
        from fastapi.responses import FileResponse as _FR
        return _FR(static_file)
    # Otherwise serve index.html for client-side routing
    react_index = _os.path.join(_REACT_DIST, 'index.html')
    if _os.path.isfile(react_index):
        with open(react_index, 'r') as f:
            return HTMLResponse(content=f.read())
    return templates.TemplateResponse("miniapp.html", {"request": request})

logger.info("✅ React Mini App serving at /miniapp (SPA with client-side routing)")

@app.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Serve the main admin panel."""
    stats = get_dashboard_stats()
    users = list(_load_users().values())
    pending_approvals = get_pending_approvals()
    
    # Payment data
    payment_stats = get_payment_stats()
    wallets_data = get_wallets_data()
    recent_transactions = get_recent_transactions()
    pending_withdrawals = get_pending_withdrawals()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats,
        "users": users,
        "pending_approvals": pending_approvals,
        "admin_name": ADMIN_NAME,
        "admin_chat_id": ADMIN_CHAT_ID,
        "payment_stats": payment_stats,
        "wallets_data": wallets_data,
        "recent_transactions": recent_transactions,
        "pending_withdrawals": pending_withdrawals
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial stats
        stats = get_dashboard_stats()
        await websocket.send_json({"type": "stats_update", "stats": stats})
        
        while True:
            # Keep connection alive - wait for any message or just ping
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# Background task for periodic stats updates
async def periodic_stats_update():
    """Periodically broadcast stats updates to all connected clients."""
    while True:
        await asyncio.sleep(30)  # Update every 30 seconds
        if active_connections:  # Only if there are active connections
            stats = get_dashboard_stats()
            await broadcast_message({"type": "stats_update", "stats": stats})

@app.post("/approve/{req_id}")
async def api_approve_request(req_id: str):
    """API endpoint to approve a request."""
    result = approve_request(req_id)
    # Broadcast update
    stats = get_dashboard_stats()
    await broadcast_message({"type": "stats_update", "stats": stats})
    await broadcast_message({"type": "log", "message": f"Approved request {req_id}"})
    return {"status": "success", "message": result.get("message", "Approved")}

@app.post("/reject/{req_id}")
async def api_reject_request(req_id: str, request: Request):
    """API endpoint to reject a request."""
    data = await request.json()
    reason = data.get("reason", "")
    result = reject_request(req_id, reason)
    # Broadcast update
    stats = get_dashboard_stats()
    await broadcast_message({"type": "stats_update", "stats": stats})
    await broadcast_message({"type": "log", "message": f"Rejected request {req_id}"})
    return {"status": "success", "message": result.get("message", "Rejected")}

@app.post("/upgrade/{chat_id}")
async def api_upgrade_user(chat_id: int):
    """API endpoint to upgrade a user."""
    result = upgrade_user(chat_id)
    # Broadcast update
    stats = get_dashboard_stats()
    await broadcast_message({"type": "stats_update", "stats": stats})
    await broadcast_message({"type": "log", "message": f"Upgraded user {chat_id}"})
    return {"status": "success", "message": result}

@app.post("/credit_wallet/{chat_id}")
async def api_credit_wallet(chat_id: int, request: Request):
    """API endpoint to credit wallet."""
    data = await request.json()
    amount = data.get("amount", 0)
    
    # Import payment functions
    from jarvis_payment import _credit_wallet, _record_tx
    from datetime import datetime
    
    new_balance = _credit_wallet(chat_id, amount, "admin_credit")
    
    _record_tx(chat_id, {
        "type": "admin_credit", 
        "amount_inr": amount, 
        "tx_ref": f"ADMIN{int(datetime.now().timestamp())}",
        "status": "completed", 
        "created": datetime.now().isoformat(),
    })
    
    # Broadcast update
    await broadcast_message({"type": "log", "message": f"Credited ₹{amount} to user {chat_id}"})
    return {"status": "success", "message": f"Credited ₹{amount}. New balance: ₹{new_balance:.2f}"}

@app.post("/debit_wallet/{chat_id}")
async def api_debit_wallet(chat_id: int, request: Request):
    """API endpoint to debit wallet."""
    data = await request.json()
    amount = data.get("amount", 0)
    
    # Import payment functions
    from jarvis_payment import _debit_wallet, _record_tx
    from datetime import datetime
    
    new_balance = _debit_wallet(chat_id, amount)
    
    if new_balance < 0:
        return {"status": "error", "message": "Insufficient balance"}
    
    _record_tx(chat_id, {
        "type": "admin_debit", 
        "amount_inr": amount, 
        "tx_ref": f"ADMIN{int(datetime.now().timestamp())}",
        "status": "completed", 
        "created": datetime.now().isoformat(),
    })
    
    # Broadcast update
    await broadcast_message({"type": "log", "message": f"Debited ₹{amount} from user {chat_id}"})
    return {"status": "success", "message": f"Debited ₹{amount}. New balance: ₹{new_balance:.2f}"}

@app.post("/approve_withdrawal/{tx_ref}")
async def api_approve_withdrawal(tx_ref: str):
    """API endpoint to approve withdrawal."""
    # Import payment functions
    from jarvis_payment import _load_transactions, _save_transactions
    from datetime import datetime
    
    transactions = _load_transactions()
    tx = None
    
    # Find transaction
    for user_txs in transactions.values():
        for t in user_txs:
            if t.get("tx_ref") == tx_ref and t.get("type") == "withdrawal":
                tx = t
                break
        if tx:
            break
    
    if not tx:
        return {"status": "error", "message": "Transaction not found"}
    
    tx["status"] = "completed"
    tx["approved_at"] = datetime.now().isoformat()
    _save_transactions(transactions)
    
    # Broadcast update
    await broadcast_message({"type": "log", "message": f"Approved withdrawal {tx_ref}"})
    return {"status": "success", "message": f"Approved withdrawal of ₹{tx['amount_inr']}"}

@app.post("/reject_withdrawal/{tx_ref}")
async def api_reject_withdrawal(tx_ref: str, request: Request):
    """API endpoint to reject withdrawal."""
    data = await request.json()
    reason = data.get("reason", "Rejected by admin")
    
    # Import payment functions
    from jarvis_payment import _load_transactions, _save_transactions, _credit_wallet
    from datetime import datetime
    
    transactions = _load_transactions()
    tx = None
    
    # Find transaction
    for user_txs in transactions.values():
        for t in user_txs:
            if t.get("tx_ref") == tx_ref and t.get("type") == "withdrawal":
                tx = t
                break
        if tx:
            break
    
    if not tx:
        return {"status": "error", "message": "Transaction not found"}
    
    # Refund amount to wallet
    _credit_wallet(tx["chat_id"], tx["amount_inr"], "refund")
    
    tx["status"] = "rejected"
    tx["rejected_at"] = datetime.now().isoformat()
    tx["reject_reason"] = reason
    _save_transactions(transactions)
    
    # Broadcast update
    await broadcast_message({"type": "log", "message": f"Rejected withdrawal {tx_ref}: {reason}"})
    return {"status": "success", "message": f"Rejected withdrawal and refunded ₹{tx['amount_inr']}"}

def get_payment_stats():
    """Get payment statistics."""
    try:
        from jarvis_payment import _load_wallets, _load_transactions
        
        wallets = _load_wallets()
        transactions = _load_transactions()
        
        total_deposits = sum(w.get("total_deposited", 0) for w in wallets.values())
        total_withdrawals = sum(w.get("total_withdrawn", 0) for w in wallets.values())
        active_wallets = sum(1 for w in wallets.values() if w.get("balance_inr", 0) > 0)
        
        pending_withdrawals = 0
        for user_txs in transactions.values():
            pending_withdrawals += sum(1 for t in user_txs if t.get("type") == "withdrawal" and t.get("status") == "processing")
        
        return {
            "total_deposits": f"{total_deposits:,.0f}",
            "total_withdrawals": f"{total_withdrawals:,.0f}",
            "active_wallets": active_wallets,
            "pending_withdrawals": pending_withdrawals
        }
    except Exception as e:
        logger.error(f"Payment stats error: {e}")
        return {
            "total_deposits": "0",
            "total_withdrawals": "0", 
            "active_wallets": 0,
            "pending_withdrawals": 0
        }

def get_wallets_data():
    """Get wallets data for admin panel."""
    try:
        from jarvis_payment import _load_wallets
        from jarvis_admin import get_user
        
        wallets = _load_wallets()
        result = []
        
        for chat_id_str, wallet in wallets.items():
            chat_id = int(chat_id_str)
            user = get_user(chat_id)
            result.append({
                "chat_id": chat_id,
                "user_name": user.get("first_name", "Unknown") if user else "Unknown",
                "wallet_id": wallet.get("wallet_id", "N/A"),
                "balance_inr": wallet.get("balance_inr", 0),
                "total_deposited": wallet.get("total_deposited", 0),
                "total_withdrawn": wallet.get("total_withdrawn", 0),
                "status": wallet.get("status", "inactive")
            })
        
        return result
    except Exception as e:
        logger.error(f"Wallets data error: {e}")
        return []

def get_recent_transactions():
    """Get recent transactions for admin panel."""
    try:
        from jarvis_payment import _load_transactions
        from jarvis_admin import get_user
        
        transactions = _load_transactions()
        result = []
        
        for chat_id_str, user_txs in transactions.items():
            chat_id = int(chat_id_str)
            user = get_user(chat_id)
            user_name = user.get("first_name", "Unknown") if user else "Unknown"
            
            for tx in user_txs[-10:]:  # Last 10 transactions per user
                result.append({
                    "user_name": user_name,
                    "type": tx.get("type", "unknown"),
                    "amount_inr": tx.get("amount_inr", 0),
                    "tx_ref": tx.get("tx_ref", "N/A"),
                    "status": tx.get("status", "unknown"),
                    "created": tx.get("created", "")
                })
        
        # Sort by created date, most recent first
        result.sort(key=lambda x: x.get("created", ""), reverse=True)
        return result[:50]  # Return top 50
    except Exception as e:
        logger.error(f"Recent transactions error: {e}")
        return []

def get_pending_withdrawals():
    """Get pending withdrawals for admin panel."""
    try:
        from jarvis_payment import _load_transactions
        from jarvis_admin import get_user
        
        transactions = _load_transactions()
        result = []
        
        for chat_id_str, user_txs in transactions.items():
            chat_id = int(chat_id_str)
            user = get_user(chat_id)
            user_name = user.get("first_name", "Unknown") if user else "Unknown"
            
            for tx in user_txs:
                if tx.get("type") == "withdrawal" and tx.get("status") == "processing":
                    result.append({
                        "user_name": user_name,
                        "chat_id": chat_id,
                        "amount_inr": tx.get("amount_inr", 0),
                        "tx_ref": tx.get("tx_ref", "N/A"),
                        "bank": tx.get("bank", "Unknown"),
                        "created": tx.get("created", "")
                    })
        
        return result
    except Exception as e:
        logger.error(f"Pending withdrawals error: {e}")
        return []

# Function to notify web clients of new events (call from other parts of the system)
async def notify_new_user(user_data: dict):
    """Notify web clients of new user registration."""
    await broadcast_message({
        "type": "new_user",
        "user": user_data
    })

async def notify_new_approval(approval_data: dict):
    """Notify web clients of new approval request."""
    await broadcast_message({
        "type": "new_approval", 
        "approval": approval_data
    })

async def notify_stats_update():
    """Notify web clients of stats update."""
    stats = get_dashboard_stats()
    await broadcast_message({
        "type": "stats_update",
        "stats": stats
    })

def start_web_server(port: int = 8000, host: str = "0.0.0.0"):
    """Start the JARVIS web server in a background thread with its own event loop."""
    def _run():
        import asyncio as _aio
        # Create a brand-new event loop for this thread to avoid conflicts
        loop = _aio.new_event_loop()
        _aio.set_event_loop(loop)
        config = uvicorn.Config(app, host=host, port=port, log_level="info", loop="asyncio")
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    t = threading.Thread(target=_run, daemon=True, name="JarvisWebServer")
    t.start()
    logger.info(f"🌐 JARVIS Web Server started on {host}:{port}")
    return t

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("jarvis_admin:app", host="0.0.0.0", port=port, reload=True)
