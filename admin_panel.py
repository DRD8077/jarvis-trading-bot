"""
🔐 JARVIS ADMIN PANEL 🔐
Complete admin control system for JARVIS Trading Bot
- Admin authentication via ADMIN_CHAT_ID
- Feature toggles (on/off for every module)
- Broadcast messages to all users
- User management & stats
- System health monitoring
- Language control

Author: JARVIS Admin System
"""

import os
import json
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ADMIN CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Admin chat IDs (comma-separated in env)
ADMIN_CHAT_IDS = set()
admin_ids_str = os.environ.get("ADMIN_CHAT_ID", "")
if admin_ids_str:
    for aid in admin_ids_str.split(","):
        aid = aid.strip()
        if aid:
            ADMIN_CHAT_IDS.add(aid)

DB_PATH = os.environ.get("DB_PATH", "jarvis_admin.db")

# ═══════════════════════════════════════════════════════════════
# FEATURE TOGGLES — DEFAULT STATES
# ═══════════════════════════════════════════════════════════════

DEFAULT_FEATURES = {
    # Stock Market Features
    "stock_analysis": {"name": "📊 Stock Analysis", "name_hi": "📊 स्टॉक एनालिसिस", "enabled": True, "category": "stock"},
    "stock_prediction": {"name": "🤖 ML Prediction", "name_hi": "🤖 ML प्रेडिक्शन", "enabled": True, "category": "stock"},
    "option_chain": {"name": "📈 Option Chain", "name_hi": "📈 ऑप्शन चेन", "enabled": True, "category": "stock"},
    "index_analysis": {"name": "📉 Index Analysis", "name_hi": "📉 इंडेक्स एनालिसिस", "enabled": True, "category": "stock"},
    "candle_patterns": {"name": "🕯️ Candle Patterns", "name_hi": "🕯️ कैंडल पैटर्न", "enabled": True, "category": "stock"},
    "stock_buy_sell": {"name": "🟢🔴 Stock Buy/Sell", "name_hi": "🟢🔴 स्टॉक खरीदो/बेचो", "enabled": True, "category": "stock"},
    
    # Crypto Features
    "crypto_gems": {"name": "💎 Crypto Gems", "name_hi": "💎 क्रिप्टो जेम्स", "enabled": True, "category": "crypto"},
    "pump_fun": {"name": "🚀 Pump.fun", "name_hi": "🚀 पंप.फन", "enabled": True, "category": "crypto"},
    "crypto_buy_sell": {"name": "🟢🔴 Crypto Buy/Sell", "name_hi": "🟢🔴 क्रिप्टो खरीदो/बेचो", "enabled": True, "category": "crypto"},
    "whale_alerts": {"name": "🐋 Whale Alerts", "name_hi": "🐋 व्हेल अलर्ट", "enabled": True, "category": "crypto"},
    "rug_detector": {"name": "🔍 Rug Detector", "name_hi": "🔍 रग डिटेक्टर", "enabled": True, "category": "crypto"},
    "gem_backtester": {"name": "📊 Gem Backtester", "name_hi": "📊 जेम बैकटेस्टर", "enabled": True, "category": "crypto"},
    
    # AI Features
    "ai_chat": {"name": "🤖 AI Chat", "name_hi": "🤖 AI चैट", "enabled": True, "category": "ai"},
    "jarvis_nlu": {"name": "🧠 JARVIS NLU", "name_hi": "🧠 जार्विस NLU", "enabled": True, "category": "ai"},
    "morning_brief": {"name": "🌅 Morning Brief", "name_hi": "🌅 मॉर्निंग ब्रीफ", "enabled": True, "category": "ai"},
    "sentiment": {"name": "📰 Sentiment Analysis", "name_hi": "📰 सेंटीमेंट एनालिसिस", "enabled": True, "category": "ai"},
    
    # Alerts & Notifications
    "auto_alerts": {"name": "🔔 Auto Alerts", "name_hi": "🔔 ऑटो अलर्ट", "enabled": True, "category": "alerts"},
    "buy_sell_alerts": {"name": "🚨 Buy/Sell Alerts", "name_hi": "🚨 खरीदो/बेचो अलर्ट", "enabled": True, "category": "alerts"},
    "price_alerts": {"name": "💰 Price Alerts", "name_hi": "💰 प्राइस अलर्ट", "enabled": True, "category": "alerts"},
    "sms_alerts": {"name": "📱 SMS Alerts", "name_hi": "📱 SMS अलर्ट", "enabled": True, "category": "alerts"},
    
    # Portfolio
    "portfolio": {"name": "💼 Portfolio", "name_hi": "💼 पोर्टफोलियो", "enabled": True, "category": "portfolio"},
    "watchlist": {"name": "👁️ Watchlist", "name_hi": "👁️ वॉचलिस्ट", "enabled": True, "category": "portfolio"},
    
    # Global
    "global_candles": {"name": "🌍 Global Candles", "name_hi": "🌍 ग्लोबल कैंडल्स", "enabled": True, "category": "global"},
    "hindi_mode": {"name": "🇮🇳 Hindi Mode", "name_hi": "🇮🇳 हिंदी मोड", "enabled": True, "category": "global"},
}

# In-memory feature cache
_features_cache = {}
_users_cache = {}


# ═══════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════

def init_admin_db():
    """Initialize admin database tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Feature toggles table
        c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
            feature_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            updated_at TEXT,
            updated_by TEXT
        )''')
        
        # User management table
        c.execute('''CREATE TABLE IF NOT EXISTS bot_users (
            chat_id TEXT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'hi',
            is_blocked INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            joined_at TEXT,
            last_active TEXT,
            total_commands INTEGER DEFAULT 0
        )''')
        
        # Broadcast history
        c.execute('''CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            sent_by TEXT,
            sent_at TEXT,
            recipients INTEGER DEFAULT 0
        )''')
        
        # Admin action log
        c.execute('''CREATE TABLE IF NOT EXISTS admin_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )''')
        
        # User language preferences
        c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
            chat_id TEXT PRIMARY KEY,
            language TEXT DEFAULT 'hi',
            auto_alerts INTEGER DEFAULT 1,
            buy_sell_alerts INTEGER DEFAULT 1,
            morning_brief INTEGER DEFAULT 0
        )''')
        
        # Insert default feature states
        for fid, fdata in DEFAULT_FEATURES.items():
            c.execute('''INSERT OR IGNORE INTO feature_toggles (feature_id, enabled, updated_at) 
                        VALUES (?, ?, ?)''', (fid, 1 if fdata["enabled"] else 0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Load into cache
        load_features_cache()
        
        logger.info("Admin DB initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Admin DB init error: {e}")
        return False


def load_features_cache():
    """Load feature toggles into memory cache"""
    global _features_cache
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT feature_id, enabled FROM feature_toggles")
        rows = c.fetchall()
        conn.close()
        
        _features_cache = {row[0]: bool(row[1]) for row in rows}
        
        # Fill in any missing features with defaults
        for fid, fdata in DEFAULT_FEATURES.items():
            if fid not in _features_cache:
                _features_cache[fid] = fdata["enabled"]
        
    except Exception:
        _features_cache = {fid: fdata["enabled"] for fid, fdata in DEFAULT_FEATURES.items()}


# ═══════════════════════════════════════════════════════════════
# ADMIN AUTHENTICATION
# ═══════════════════════════════════════════════════════════════

def is_admin(chat_id: str) -> bool:
    """Check if a chat_id is an admin"""
    return str(chat_id) in ADMIN_CHAT_IDS

def require_admin(chat_id: str) -> Tuple[bool, str]:
    """Check admin rights, return (is_admin, message)"""
    if is_admin(chat_id):
        return True, ""
    return False, (
        "🚫 एक्सेस डिनाइड!\n\n"
        "सर, ये Admin Panel सिर्फ Admin के लिए है।\n"
        "आपकी Chat ID: {}\n\n"
        "🔐 Admin access के लिए ADMIN_CHAT_ID सेट करें।"
    ).format(chat_id)


# ═══════════════════════════════════════════════════════════════
# FEATURE TOGGLE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def is_feature_enabled(feature_id: str) -> bool:
    """Check if a feature is enabled"""
    if not _features_cache:
        load_features_cache()
    return _features_cache.get(feature_id, True)

def toggle_feature(feature_id: str, enabled: bool, admin_id: str) -> Tuple[bool, str]:
    """Toggle a feature on/off"""
    if feature_id not in DEFAULT_FEATURES:
        return False, f"Feature '{feature_id}' not found!"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO feature_toggles (feature_id, enabled, updated_at, updated_by)
                     VALUES (?, ?, ?, ?)''',
                  (feature_id, 1 if enabled else 0, datetime.now().isoformat(), admin_id))
        
        # Log action
        action = "ENABLED" if enabled else "DISABLED"
        c.execute('''INSERT INTO admin_log (admin_id, action, details, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (admin_id, f"TOGGLE_{action}", f"{feature_id} -> {action}", datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update cache
        _features_cache[feature_id] = enabled
        
        feature_name = DEFAULT_FEATURES[feature_id]["name_hi"]
        status = "चालू ✅" if enabled else "बंद ❌"
        
        return True, f"{feature_name} अब {status} है!"
        
    except Exception as e:
        logger.error(f"Toggle feature error: {e}")
        return False, f"Error: {e}"

def toggle_all_features(enabled: bool, admin_id: str, category: str = None) -> str:
    """Toggle all features on/off, optionally by category"""
    count = 0
    for fid, fdata in DEFAULT_FEATURES.items():
        if category and fdata["category"] != category:
            continue
        toggle_feature(fid, enabled, admin_id)
        count += 1
    
    status = "चालू ✅" if enabled else "बंद ❌"
    cat_txt = f" ({category})" if category else ""
    return f"🔧 {count} features{cat_txt} अब {status} हैं!"

def get_features_status() -> str:
    """Get current status of all features"""
    if not _features_cache:
        load_features_cache()
    
    msg = (
        f"{'═' * 30}\n"
        f"🔐 जार्विस एडमिन - फीचर स्टेटस\n"
        f"{'═' * 30}\n\n"
    )
    
    categories = {
        "stock": "📊 स्टॉक मार्केट",
        "crypto": "💎 क्रिप्टो मार्केट",
        "ai": "🤖 AI फीचर्स",
        "alerts": "🔔 अलर्ट्स",
        "portfolio": "💼 पोर्टफोलियो",
        "global": "🌍 ग्लोबल",
    }
    
    for cat_id, cat_name in categories.items():
        msg += f"{cat_name}:\n"
        for fid, fdata in DEFAULT_FEATURES.items():
            if fdata["category"] == cat_id:
                enabled = _features_cache.get(fid, True)
                status = "✅ चालू" if enabled else "❌ बंद"
                msg += f"  {fdata['name_hi']} → {status}\n"
        msg += "\n"
    
    msg += f"{'═' * 30}\n"
    return msg


# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def register_user(chat_id: str, username: str = None, first_name: str = None, language: str = "hi"):
    """Register or update a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''INSERT INTO bot_users (chat_id, username, first_name, language, joined_at, last_active, total_commands)
                     VALUES (?, ?, ?, ?, ?, ?, 1)
                     ON CONFLICT(chat_id) DO UPDATE SET
                     username = COALESCE(?, username),
                     first_name = COALESCE(?, first_name),
                     last_active = ?,
                     total_commands = total_commands + 1''',
                  (chat_id, username, first_name, language, datetime.now().isoformat(), datetime.now().isoformat(),
                   username, first_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Register user error: {e}")

def get_user_language(chat_id: str) -> str:
    """Get user's preferred language"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT language FROM user_preferences WHERE chat_id = ?", (str(chat_id),))
        row = c.fetchone()
        conn.close()
        return row[0] if row else "hi"
    except Exception:
        return "hi"

def set_user_language(chat_id: str, language: str) -> str:
    """Set user's preferred language"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO user_preferences (chat_id, language)
                     VALUES (?, ?)
                     ON CONFLICT(chat_id) DO UPDATE SET language = ?''',
                  (str(chat_id), language, language))
        conn.commit()
        conn.close()
        
        if language == "hi":
            return "🇮🇳 भाषा हिंदी में बदल दी गई है! अब जार्विस हिंदी में बात करेगा।"
        else:
            return "🇬🇧 Language changed to English! JARVIS will now respond in English."
    except Exception as e:
        return f"Error: {e}"

def get_user_preferences(chat_id: str) -> Dict:
    """Get user preferences"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM user_preferences WHERE chat_id = ?", (str(chat_id),))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "chat_id": row[0],
                "language": row[1],
                "auto_alerts": bool(row[2]),
                "buy_sell_alerts": bool(row[3]),
                "morning_brief": bool(row[4])
            }
        return {"language": "hi", "auto_alerts": True, "buy_sell_alerts": True, "morning_brief": False}
    except Exception:
        return {"language": "hi", "auto_alerts": True, "buy_sell_alerts": True, "morning_brief": False}

def block_user(chat_id: str, admin_id: str) -> str:
    """Block a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE bot_users SET is_blocked = 1 WHERE chat_id = ?", (str(chat_id),))
        c.execute('''INSERT INTO admin_log (admin_id, action, details, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (admin_id, "BLOCK_USER", f"Blocked {chat_id}", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return f"🚫 User {chat_id} blocked!"
    except Exception as e:
        return f"Error: {e}"

def unblock_user(chat_id: str, admin_id: str) -> str:
    """Unblock a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE bot_users SET is_blocked = 0 WHERE chat_id = ?", (str(chat_id),))
        c.execute('''INSERT INTO admin_log (admin_id, action, details, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (admin_id, "UNBLOCK_USER", f"Unblocked {chat_id}", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return f"✅ User {chat_id} unblocked!"
    except Exception as e:
        return f"Error: {e}"

def is_user_blocked(chat_id: str) -> bool:
    """Check if user is blocked"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT is_blocked FROM bot_users WHERE chat_id = ?", (str(chat_id),))
        row = c.fetchone()
        conn.close()
        return bool(row[0]) if row else False
    except Exception:
        return False

def get_all_users() -> List[Dict]:
    """Get all registered users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM bot_users ORDER BY last_active DESC")
        rows = c.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "chat_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "language": row[3],
                "is_blocked": bool(row[4]),
                "is_premium": bool(row[5]),
                "joined_at": row[6],
                "last_active": row[7],
                "total_commands": row[8]
            })
        return users
    except Exception:
        return []

def get_user_stats() -> str:
    """Get user statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM bot_users")
        total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = 1")
        blocked = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM bot_users WHERE last_active > ?",
                  ((datetime.now() - timedelta(hours=24)).isoformat(),))
        active_24h = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM bot_users WHERE last_active > ?",
                  ((datetime.now() - timedelta(days=7)).isoformat(),))
        active_7d = c.fetchone()[0]
        
        c.execute("SELECT SUM(total_commands) FROM bot_users")
        total_cmds = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM bot_users WHERE language = 'hi'")
        hindi_users = c.fetchone()[0]
        
        conn.close()
        
        return (
            f"{'═' * 30}\n"
            f"👥 यूज़र स्टैटिस्टिक्स\n"
            f"{'═' * 30}\n\n"
            f"📊 कुल यूज़र: {total}\n"
            f"🟢 24 घंटे में एक्टिव: {active_24h}\n"
            f"📅 7 दिन में एक्टिव: {active_7d}\n"
            f"🚫 ब्लॉक्ड: {blocked}\n"
            f"🇮🇳 हिंदी यूज़र: {hindi_users}\n"
            f"🇬🇧 इंग्लिश यूज़र: {total - hindi_users}\n"
            f"📋 कुल कमांड्स: {total_cmds:,}\n"
            f"{'═' * 30}"
        )
    except Exception as e:
        return f"Stats error: {e}"


# ═══════════════════════════════════════════════════════════════
# BROADCAST SYSTEM
# ═══════════════════════════════════════════════════════════════

def get_broadcast_targets() -> List[str]:
    """Get all non-blocked user chat IDs for broadcast"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT chat_id FROM bot_users WHERE is_blocked = 0")
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception:
        return []

def log_broadcast(message: str, admin_id: str, recipients: int):
    """Log a broadcast"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO broadcasts (message, sent_by, sent_at, recipients)
                     VALUES (?, ?, ?, ?)''',
                  (message, admin_id, datetime.now().isoformat(), recipients))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Broadcast log error: {e}")


# ═══════════════════════════════════════════════════════════════
# ADMIN PANEL UI
# ═══════════════════════════════════════════════════════════════

def generate_admin_panel(admin_id: str) -> str:
    """Generate the admin panel main screen"""
    is_adm, deny_msg = require_admin(admin_id)
    if not is_adm:
        return deny_msg
    
    status = get_features_status()
    
    panel = (
        f"{'═' * 30}\n"
        f"🔐 जार्विस एडमिन पैनल\n"
        f"{'═' * 30}\n\n"
        f"नमस्ते बॉस! 🙏\n"
        f"आपका एडमिन पैनल तैयार है।\n\n"
        f"{'─' * 25}\n"
        f"🔧 कमांड्स:\n\n"
        f"📊 फीचर कंट्रोल:\n"
        f"  /toggle <feature_id> - फीचर चालू/बंद\n"
        f"  /features - सभी फीचर्स देखें\n"
        f"  /enable_all - सब चालू करें\n"
        f"  /disable_all - सब बंद करें\n\n"
        f"👥 यूज़र मैनेजमेंट:\n"
        f"  /users - सभी यूज़र देखें\n"
        f"  /stats - यूज़र स्टैट्स\n"
        f"  /block <chat_id> - यूज़र ब्लॉक\n"
        f"  /unblock <chat_id> - यूज़र अनब्लॉक\n\n"
        f"📢 ब्रॉडकास्ट:\n"
        f"  /broadcast <message> - सबको मैसेज\n\n"
        f"🌐 सिस्टम:\n"
        f"  /system - सिस्टम हेल्थ\n"
        f"  /logs - एडमिन लॉग\n"
        f"  /lang hi|en - डिफॉल्ट भाषा\n\n"
        f"{'─' * 25}\n\n"
    )
    
    return panel

def build_admin_keyboard() -> List[List[Dict]]:
    """Build inline keyboard for admin panel"""
    keyboard = [
        [{"text": "📊 फीचर स्टेटस", "callback_data": "admin_features"},
         {"text": "👥 यूज़र स्टैट्स", "callback_data": "admin_stats"}],
        [{"text": "✅ सब चालू", "callback_data": "admin_enable_all"},
         {"text": "❌ सब बंद", "callback_data": "admin_disable_all"}],
        [{"text": "📊 स्टॉक ON/OFF", "callback_data": "admin_toggle_cat_stock"},
         {"text": "💎 क्रिप्टो ON/OFF", "callback_data": "admin_toggle_cat_crypto"}],
        [{"text": "🤖 AI ON/OFF", "callback_data": "admin_toggle_cat_ai"},
         {"text": "🔔 अलर्ट ON/OFF", "callback_data": "admin_toggle_cat_alerts"}],
        [{"text": "🌍 ग्लोबल ON/OFF", "callback_data": "admin_toggle_cat_global"},
         {"text": "💼 पोर्टफोलियो ON/OFF", "callback_data": "admin_toggle_cat_portfolio"}],
        [{"text": "📢 ब्रॉडकास्ट", "callback_data": "admin_broadcast"},
         {"text": "📋 लॉग देखें", "callback_data": "admin_logs"}],
        [{"text": "🔙 वापस जाएं", "callback_data": "admin_back"}],
    ]
    return keyboard

def build_feature_toggle_keyboard(category: str = None) -> List[List[Dict]]:
    """Build keyboard with individual feature toggles"""
    if not _features_cache:
        load_features_cache()
    
    keyboard = []
    for fid, fdata in DEFAULT_FEATURES.items():
        if category and fdata["category"] != category:
            continue
        enabled = _features_cache.get(fid, True)
        status = "✅" if enabled else "❌"
        keyboard.append([{
            "text": f"{status} {fdata['name_hi']}",
            "callback_data": f"admin_toggle_{fid}"
        }])
    
    keyboard.append([{"text": "🔙 एडमिन पैनल", "callback_data": "admin_panel"}])
    return keyboard


# ═══════════════════════════════════════════════════════════════
# SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════

def get_system_health() -> str:
    """Get system health status"""
    import importlib
    
    modules = {
        "telegram_bot": "🤖 टेलीग्राम बॉट",
        "ai_chat": "💬 AI चैट",
        "jarvis_ai": "🧠 जार्विस AI",
        "crypto_engine": "💎 क्रिप्टो इंजन",
        "candle_analyzer": "🕯️ कैंडल एनालाइज़र",
        "ml_predictor": "🤖 ML प्रेडिक्टर",
        "stock_data_fetcher": "📊 स्टॉक डाटा",
        "index_data": "📈 इंडेक्स डाटा",
        "sentiment_engine": "📰 सेंटीमेंट",
        "risk_manager": "⚠️ रिस्क मैनेजर",
        "portfolio_tracker": "💼 पोर्टफोलियो",
        "whale_alert": "🐋 व्हेल अलर्ट",
        "rug_detector": "🔍 रग डिटेक्टर",
        "gem_backtester": "📊 बैकटेस्टर",
        "buy_sell_engine": "🟢🔴 बाय/सेल इंजन",
        "global_candle_engine": "🌍 ग्लोबल कैंडल",
        "data_store": "💾 डाटाबेस",
        "sms_engine": "📱 SMS इंजन",
    }
    
    msg = (
        f"{'═' * 30}\n"
        f"🖥️ सिस्टम हेल्थ चेक\n"
        f"{'═' * 30}\n\n"
    )
    
    ok_count = 0
    fail_count = 0
    
    for mod_name, display in modules.items():
        try:
            importlib.import_module(mod_name)
            msg += f"  ✅ {display}\n"
            ok_count += 1
        except ImportError:
            msg += f"  ❌ {display} (not installed)\n"
            fail_count += 1
        except Exception as e:
            msg += f"  ⚠️ {display} ({str(e)[:30]})\n"
            fail_count += 1
    
    msg += f"\n{'─' * 25}\n"
    msg += f"✅ Working: {ok_count} | ❌ Failed: {fail_count}\n"
    msg += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n"
    msg += f"{'═' * 30}"
    
    return msg


def get_admin_logs(limit: int = 20) -> str:
    """Get recent admin action logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM admin_log ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return "📋 कोई लॉग नहीं है अभी।"
        
        msg = (
            f"{'═' * 30}\n"
            f"📋 एडमिन लॉग (Last {limit})\n"
            f"{'═' * 30}\n\n"
        )
        
        for row in rows:
            msg += f"  #{row[0]} | {row[2]} | {row[3]}\n  ⏱️ {row[4]}\n\n"
        
        msg += f"{'═' * 30}"
        return msg
    except Exception as e:
        return f"Log error: {e}"


# ═══════════════════════════════════════════════════════════════
# ADMIN COMMAND HANDLER
# ═══════════════════════════════════════════════════════════════

def handle_admin_command(chat_id: str, command: str, args: str = "") -> Tuple[str, Optional[List]]:
    """
    Handle admin commands
    Returns (response_text, optional_keyboard)
    """
    is_adm, deny_msg = require_admin(chat_id)
    if not is_adm:
        return deny_msg, None
    
    command = command.lower().strip()
    
    if command in ["admin", "admin_panel", "panel"]:
        return generate_admin_panel(chat_id), build_admin_keyboard()
    
    elif command == "features":
        return get_features_status(), build_feature_toggle_keyboard()
    
    elif command == "stats":
        return get_user_stats(), None
    
    elif command == "system":
        return get_system_health(), None
    
    elif command == "logs":
        return get_admin_logs(), None
    
    elif command == "users":
        users = get_all_users()
        if not users:
            return "कोई यूज़र नहीं है अभी।", None
        
        msg = f"👥 सभी यूज़र ({len(users)}):\n\n"
        for u in users[:50]:
            blocked = "🚫" if u["is_blocked"] else "✅"
            msg += f"  {blocked} {u['first_name'] or 'N/A'} (@{u['username'] or 'N/A'})\n"
            msg += f"     ID: {u['chat_id']} | Cmds: {u['total_commands']}\n\n"
        return msg, None
    
    elif command == "enable_all":
        result = toggle_all_features(True, chat_id)
        return result, build_admin_keyboard()
    
    elif command == "disable_all":
        result = toggle_all_features(False, chat_id)
        return result, build_admin_keyboard()
    
    elif command.startswith("toggle"):
        feature_id = args.strip() if args else command.replace("toggle_", "").replace("toggle ", "")
        if not feature_id or feature_id == "toggle":
            return "Usage: /toggle <feature_id>\n\nAvailable features:\n" + "\n".join(f"  • {fid}" for fid in DEFAULT_FEATURES.keys()), None
        
        current = _features_cache.get(feature_id, True)
        success, msg = toggle_feature(feature_id, not current, chat_id)
        return msg, build_feature_toggle_keyboard()
    
    elif command.startswith("block"):
        target_id = args.strip()
        if not target_id:
            return "Usage: /block <chat_id>", None
        result = block_user(target_id, chat_id)
        return result, None
    
    elif command.startswith("unblock"):
        target_id = args.strip()
        if not target_id:
            return "Usage: /unblock <chat_id>", None
        result = unblock_user(target_id, chat_id)
        return result, None
    
    elif command == "broadcast":
        if not args.strip():
            return "Usage: /broadcast <message>\n\nसभी यूज़र को मैसेज भेजें।", None
        # Return targets list - actual sending done by telegram_bot.py
        targets = get_broadcast_targets()
        return f"📢 BROADCAST_READY|{len(targets)}|{args}", None
    
    elif command.startswith("toggle_cat_"):
        category = command.replace("toggle_cat_", "")
        # Check current state of first feature in category
        first_feature = next((fid for fid, fd in DEFAULT_FEATURES.items() if fd["category"] == category), None)
        if first_feature:
            current = _features_cache.get(first_feature, True)
            result = toggle_all_features(not current, chat_id, category)
            return result, build_admin_keyboard()
        return f"Category {category} not found!", None
    
    else:
        return (
            "🤔 अज्ञात कमांड!\n\n"
            "एडमिन कमांड्स:\n"
            "/admin - एडमिन पैनल\n"
            "/features - फीचर कंट्रोल\n"
            "/stats - यूज़र स्टैट्स\n"
            "/system - सिस्टम हेल्थ\n"
            "/toggle <feature> - फीचर चालू/बंद\n"
            "/block <id> - यूज़र ब्लॉक\n"
            "/broadcast <msg> - ब्रॉडकास्ट"
        ), None


# ═══════════════════════════════════════════════════════════════
# CALLBACK HANDLER FOR INLINE BUTTONS
# ═══════════════════════════════════════════════════════════════

def handle_admin_callback(chat_id: str, callback_data: str) -> Tuple[str, Optional[List]]:
    """Handle admin panel inline button callbacks"""
    is_adm, deny_msg = require_admin(chat_id)
    if not is_adm:
        return deny_msg, None
    
    if callback_data == "admin_features":
        return get_features_status(), build_feature_toggle_keyboard()
    
    elif callback_data == "admin_stats":
        return get_user_stats(), build_admin_keyboard()
    
    elif callback_data == "admin_enable_all":
        result = toggle_all_features(True, chat_id)
        return result + "\n\n" + get_features_status(), build_admin_keyboard()
    
    elif callback_data == "admin_disable_all":
        result = toggle_all_features(False, chat_id)
        return result + "\n\n" + get_features_status(), build_admin_keyboard()
    
    elif callback_data.startswith("admin_toggle_cat_"):
        category = callback_data.replace("admin_toggle_cat_", "")
        first_feature = next((fid for fid, fd in DEFAULT_FEATURES.items() if fd["category"] == category), None)
        if first_feature:
            current = _features_cache.get(first_feature, True)
            result = toggle_all_features(not current, chat_id, category)
            return result, build_admin_keyboard()
        return "Category not found!", build_admin_keyboard()
    
    elif callback_data.startswith("admin_toggle_"):
        feature_id = callback_data.replace("admin_toggle_", "")
        if feature_id in DEFAULT_FEATURES:
            current = _features_cache.get(feature_id, True)
            success, msg = toggle_feature(feature_id, not current, chat_id)
            return msg, build_feature_toggle_keyboard()
    
    elif callback_data == "admin_broadcast":
        return "📢 ब्रॉडकास्ट भेजने के लिए:\n/broadcast <आपका मैसेज>", None
    
    elif callback_data == "admin_logs":
        return get_admin_logs(), build_admin_keyboard()
    
    elif callback_data == "admin_panel":
        return generate_admin_panel(chat_id), build_admin_keyboard()
    
    elif callback_data == "admin_back":
        return "🏠 मेन मेन्यू पर वापस आ गए!", None
    
    return "Unknown admin action", build_admin_keyboard()


# ═══════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════

# Auto-initialize on import
try:
    init_admin_db()
except Exception as e:
    logger.error(f"Admin panel init error: {e}")


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'ADMIN_CHAT_IDS', 'DEFAULT_FEATURES',
    'init_admin_db', 'is_admin', 'require_admin',
    'is_feature_enabled', 'toggle_feature', 'toggle_all_features', 'get_features_status',
    'register_user', 'get_user_language', 'set_user_language', 'get_user_preferences',
    'block_user', 'unblock_user', 'is_user_blocked', 'get_all_users', 'get_user_stats',
    'get_broadcast_targets', 'log_broadcast',
    'generate_admin_panel', 'build_admin_keyboard', 'build_feature_toggle_keyboard',
    'get_system_health', 'get_admin_logs',
    'handle_admin_command', 'handle_admin_callback',
]
