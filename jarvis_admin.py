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
