"""
🧠💾 JARVIS SUPER MEMORY — Persistent Intelligence Like ChatGPT/Claude
═══════════════════════════════════════════════════════════════════
Remembers EVERYTHING — conversations, positions, predictions, what was right/wrong.

Memory Layers:
  1. Conversation Memory — Full chat history persisted to disk (like ChatGPT)
  2. Position Memory — "Maine 25950 call li" → tracked + analyzed all day
  3. Fact Memory — User preferences, trading style, risk appetite
  4. Prediction Memory — What JARVIS predicted vs what actually happened
  5. Learning Memory — What was right, what was wrong → self-improvement

Storage: JSON files on disk → survives restarts
Each user gets their own memory file: jarvis_memory_{chat_id}.json

Author: David Crew AI (Boss: Deepak Kumar)
"""

import os
import json
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from collections import defaultdict
import pytz

logger = logging.getLogger("jarvis_memory_pro")

IST = pytz.timezone('Asia/Kolkata')

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════

MEMORY_DIR = "memory_store"
os.makedirs(MEMORY_DIR, exist_ok=True)

MAX_CONVERSATIONS = 200      # Keep last 200 messages per user  
MAX_POSITIONS = 50           # Keep last 50 positions per user
MAX_FACTS = 100              # Max stored facts per user
MAX_PREDICTIONS = 100        # Track last 100 predictions
CONVERSATION_SUMMARY_AT = 100  # Summarize after 100 messages
POSITION_TRACK_INTERVAL = 300  # 5 min position re-analysis

# ═══════════════════════════════════════════════════════════
#  IN-MEMORY CACHE
# ═══════════════════════════════════════════════════════════

_memory_cache: Dict[str, dict] = {}  # chat_id -> full memory
_last_save: Dict[str, float] = {}    # chat_id -> last save timestamp
SAVE_INTERVAL = 30  # Save to disk max every 30 seconds


# ═══════════════════════════════════════════════════════════
#  CORE: Load / Save per-user Memory
# ═══════════════════════════════════════════════════════════

def _memory_file(chat_id: int) -> str:
    return os.path.join(MEMORY_DIR, f"user_{chat_id}.json")


def _default_memory() -> dict:
    return {
        "user_info": {
            "name": "",
            "chat_id": 0,
            "first_seen": datetime.now(IST).isoformat(),
            "language": "hinglish",
            "risk_appetite": "moderate",
            "trading_style": "",
            "budget": "",
        },
        "conversations": [],      # [{role, text, intent, timestamp}]
        "positions": [],           # [{symbol, strike, type, entry, time, status, pnl, notes}]
        "facts": {},               # key -> value (persistent preferences)
        "predictions": [],         # [{what, predicted, actual, correct, time}]
        "learnings": [],           # [{lesson, context, time}]
        "summary": "",             # AI-generated conversation summary
        "last_active": datetime.now(IST).isoformat(),
    }


def load_memory(chat_id: int) -> dict:
    """Load user memory from disk (with caching)."""
    cid = str(chat_id)
    
    if cid in _memory_cache:
        return _memory_cache[cid]
    
    fpath = _memory_file(chat_id)
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _memory_cache[cid] = data
            return data
        except Exception as e:
            logger.error(f"[MEMORY-PRO] Load error for {chat_id}: {e}")
    
    # New user
    data = _default_memory()
    data["user_info"]["chat_id"] = chat_id
    _memory_cache[cid] = data
    return data


def save_memory(chat_id: int, force: bool = False):
    """Save user memory to disk (throttled)."""
    cid = str(chat_id)
    now = time.time()
    
    if not force and cid in _last_save:
        if now - _last_save[cid] < SAVE_INTERVAL:
            return  # Throttle saves
    
    if cid not in _memory_cache:
        return
    
    try:
        fpath = _memory_file(chat_id)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(_memory_cache[cid], f, indent=2, ensure_ascii=False, default=str)
        _last_save[cid] = now
    except Exception as e:
        logger.error(f"[MEMORY-PRO] Save error for {chat_id}: {e}")


# ═══════════════════════════════════════════════════════════
#  CONVERSATION MEMORY — Like ChatGPT
# ═══════════════════════════════════════════════════════════

def remember_message(chat_id: int, role: str, text: str, intent: str = ""):
    """Store a conversation message — persisted to disk."""
    mem = load_memory(chat_id)
    
    msg = {
        "role": role,  # "user" or "assistant"
        "text": text[:1000],  # Cap at 1000 chars
        "intent": intent,
        "timestamp": datetime.now(IST).isoformat(),
    }
    
    mem["conversations"].append(msg)
    mem["last_active"] = datetime.now(IST).isoformat()
    
    # Trim if too long
    if len(mem["conversations"]) > MAX_CONVERSATIONS:
        # Keep first 5 (for context) + last 150
        mem["conversations"] = mem["conversations"][:5] + mem["conversations"][-150:]
    
    save_memory(chat_id)


def get_conversation_history(chat_id: int, last_n: int = 20) -> List[dict]:
    """Get recent conversation history."""
    mem = load_memory(chat_id)
    return mem["conversations"][-last_n:]


def get_conversation_for_ai(chat_id: int, last_n: int = 10) -> str:
    """Get conversation context formatted for AI prompts."""
    history = get_conversation_history(chat_id, last_n)
    if not history:
        return ""
    
    parts = ["\n[CONVERSATION MEMORY - Last messages:]"]
    for msg in history:
        role = "👤 User" if msg["role"] == "user" else "🤖 JARVIS"
        text = msg["text"][:200]
        ts = msg.get("timestamp", "")[:16]
        parts.append(f"{role} [{ts}]: {text}")
    
    return "\n".join(parts)


def get_full_context_for_ai(chat_id: int) -> str:
    """Get COMPLETE user context for AI — memory + facts + positions."""
    mem = load_memory(chat_id)
    parts = []
    
    # User info
    info = mem.get("user_info", {})
    if info.get("name"):
        parts.append(f"User: {info['name']}")
    if info.get("risk_appetite"):
        parts.append(f"Risk appetite: {info['risk_appetite']}")
    if info.get("trading_style"):
        parts.append(f"Trading style: {info['trading_style']}")
    if info.get("budget"):
        parts.append(f"Budget: {info['budget']}")
    
    # Active positions
    active = get_active_positions(chat_id)
    if active:
        parts.append("\n[ACTIVE POSITIONS:]")
        for p in active:
            sym = p.get("symbol", "")
            strike = p.get("strike", "")
            otype = p.get("option_type", "")
            entry = p.get("entry_price", 0)
            parts.append(f"  • {sym} {strike} {otype} @ ₹{entry}")
    
    # Key facts
    facts = mem.get("facts", {})
    if facts:
        parts.append("\n[STORED FACTS:]")
        for k, v in list(facts.items())[:20]:
            parts.append(f"  • {k}: {v}")
    
    # Recent conversation
    conv = get_conversation_for_ai(chat_id, 8)
    if conv:
        parts.append(conv)
    
    # Summary
    summary = mem.get("summary", "")
    if summary:
        parts.append(f"\n[CONVERSATION SUMMARY:]\n{summary[:500]}")
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  FACT MEMORY — Remember user preferences & info
# ═══════════════════════════════════════════════════════════

def remember_fact(chat_id: int, key: str, value: Any):
    """Store a permanent fact about the user."""
    mem = load_memory(chat_id)
    mem["facts"][key] = value
    
    # Also update user_info if applicable
    key_lower = key.lower()
    if "name" in key_lower:
        mem["user_info"]["name"] = str(value)
    elif "risk" in key_lower:
        mem["user_info"]["risk_appetite"] = str(value)
    elif "budget" in key_lower:
        mem["user_info"]["budget"] = str(value)
    elif "style" in key_lower:
        mem["user_info"]["trading_style"] = str(value)
    
    # Limit facts
    if len(mem["facts"]) > MAX_FACTS:
        keys = list(mem["facts"].keys())
        for k in keys[:len(keys) - MAX_FACTS]:
            del mem["facts"][k]
    
    save_memory(chat_id, force=True)


def recall_fact(chat_id: int, key: str, default: Any = None) -> Any:
    """Recall a stored fact."""
    mem = load_memory(chat_id)
    return mem["facts"].get(key, default)


def get_all_facts(chat_id: int) -> dict:
    """Get all stored facts."""
    mem = load_memory(chat_id)
    return mem.get("facts", {})


# ═══════════════════════════════════════════════════════════
#  POSITION MEMORY — Track what user bought/sold
# ═══════════════════════════════════════════════════════════

def add_position(chat_id: int, symbol: str, strike: int, option_type: str,
                 entry_price: float, quantity: int = 1, notes: str = "") -> dict:
    """
    Track a new position.
    Called when user says "maine nifty 25950 call li" or similar.
    """
    mem = load_memory(chat_id)
    
    position = {
        "id": len(mem["positions"]) + 1,
        "symbol": symbol.upper(),
        "strike": strike,
        "option_type": option_type.upper(),
        "entry_price": entry_price,
        "quantity": quantity,
        "entry_time": datetime.now(IST).isoformat(),
        "status": "OPEN",
        "current_price": entry_price,
        "pnl": 0.0,
        "pnl_pct": 0.0,
        "last_checked": datetime.now(IST).isoformat(),
        "notes": notes,
        "analysis_history": [],  # [{time, price, analysis}]
        "alerts_sent": [],
    }
    
    mem["positions"].append(position)
    
    # Trim old closed positions
    if len(mem["positions"]) > MAX_POSITIONS:
        # Keep all open + last N closed
        open_pos = [p for p in mem["positions"] if p["status"] == "OPEN"]
        closed_pos = [p for p in mem["positions"] if p["status"] != "OPEN"]
        mem["positions"] = open_pos + closed_pos[-(MAX_POSITIONS - len(open_pos)):]
    
    save_memory(chat_id, force=True)
    logger.info(f"[MEMORY-PRO] Position added: {symbol} {strike} {option_type} @ ₹{entry_price} for {chat_id}")
    
    return position


def close_position(chat_id: int, position_id: int = None, symbol: str = None,
                   strike: int = None, exit_price: float = 0) -> Optional[dict]:
    """Close/exit a tracked position."""
    mem = load_memory(chat_id)
    
    pos = None
    for p in mem["positions"]:
        if p["status"] != "OPEN":
            continue
        if position_id and p["id"] == position_id:
            pos = p
            break
        if symbol and strike:
            if p["symbol"] == symbol.upper() and p["strike"] == strike:
                pos = p
                break
    
    if not pos:
        return None
    
    pos["status"] = "CLOSED"
    pos["exit_price"] = exit_price
    pos["exit_time"] = datetime.now(IST).isoformat()
    if exit_price > 0 and pos.get("entry_price", 0) > 0:
        pos["pnl"] = round((exit_price - pos["entry_price"]) * pos.get("quantity", 1), 2)
        pos["pnl_pct"] = round(((exit_price - pos["entry_price"]) / pos["entry_price"]) * 100, 2)
    
    save_memory(chat_id, force=True)
    return pos


def get_active_positions(chat_id: int) -> List[dict]:
    """Get all open positions."""
    mem = load_memory(chat_id)
    return [p for p in mem.get("positions", []) if p.get("status") == "OPEN"]


def get_all_positions(chat_id: int) -> List[dict]:
    """Get all positions (open + closed)."""
    mem = load_memory(chat_id)
    return mem.get("positions", [])


def update_position_price(chat_id: int, position_id: int, current_price: float,
                          analysis: str = ""):
    """Update a position's current price and add analysis."""
    mem = load_memory(chat_id)
    
    for p in mem["positions"]:
        if p["id"] == position_id and p["status"] == "OPEN":
            p["current_price"] = current_price
            p["last_checked"] = datetime.now(IST).isoformat()
            if p.get("entry_price", 0) > 0:
                p["pnl"] = round((current_price - p["entry_price"]) * p.get("quantity", 1), 2)
                p["pnl_pct"] = round(((current_price - p["entry_price"]) / p["entry_price"]) * 100, 2)
            
            if analysis:
                p["analysis_history"].append({
                    "time": datetime.now(IST).isoformat(),
                    "price": current_price,
                    "analysis": analysis[:300],
                })
                # Keep last 20 analysis entries
                p["analysis_history"] = p["analysis_history"][-20:]
            break
    
    save_memory(chat_id)


# ═══════════════════════════════════════════════════════════
#  PREDICTION TRACKING — What was right, what was wrong
# ═══════════════════════════════════════════════════════════

def add_prediction(chat_id: int, what: str, predicted: str, context: str = ""):
    """Track a prediction JARVIS made."""
    mem = load_memory(chat_id)
    
    pred = {
        "what": what[:200],
        "predicted": predicted[:200],
        "context": context[:200],
        "actual": "",
        "correct": None,  # None=pending, True=correct, False=wrong
        "time": datetime.now(IST).isoformat(),
    }
    
    mem["predictions"].append(pred)
    if len(mem["predictions"]) > MAX_PREDICTIONS:
        mem["predictions"] = mem["predictions"][-MAX_PREDICTIONS:]
    
    save_memory(chat_id)


def update_prediction(chat_id: int, index: int, actual: str, correct: bool):
    """Update a prediction with actual result."""
    mem = load_memory(chat_id)
    preds = mem.get("predictions", [])
    if 0 <= index < len(preds):
        preds[index]["actual"] = actual
        preds[index]["correct"] = correct
        
        # Add learning
        lesson = f"Predicted '{preds[index]['predicted']}' for {preds[index]['what']}, actual was '{actual}' — {'CORRECT' if correct else 'WRONG'}"
        add_learning(chat_id, lesson, preds[index].get("context", ""))
    
    save_memory(chat_id)


def get_prediction_accuracy(chat_id: int) -> dict:
    """Get prediction accuracy stats."""
    mem = load_memory(chat_id)
    preds = mem.get("predictions", [])
    
    total = len(preds)
    resolved = [p for p in preds if p["correct"] is not None]
    correct = sum(1 for p in resolved if p["correct"])
    wrong = len(resolved) - correct
    pending = total - len(resolved)
    accuracy = (correct / len(resolved) * 100) if resolved else 0
    
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "pending": pending,
        "accuracy": round(accuracy, 1),
    }


# ═══════════════════════════════════════════════════════════
#  LEARNING MEMORY — Self-improvement
# ═══════════════════════════════════════════════════════════

def add_learning(chat_id: int, lesson: str, context: str = ""):
    """Store a learning from experience."""
    mem = load_memory(chat_id)
    
    mem["learnings"].append({
        "lesson": lesson[:500],
        "context": context[:200],
        "time": datetime.now(IST).isoformat(),
    })
    
    if len(mem["learnings"]) > 100:
        mem["learnings"] = mem["learnings"][-100:]
    
    save_memory(chat_id)


def get_learnings(chat_id: int, last_n: int = 10) -> List[dict]:
    """Get recent learnings."""
    mem = load_memory(chat_id)
    return mem.get("learnings", [])[-last_n:]


# ═══════════════════════════════════════════════════════════
#  NLU: Parse position from natural language
# ═══════════════════════════════════════════════════════════

def parse_position_from_text(text: str) -> Optional[dict]:
    """
    Parse position info from natural language.
    
    Handles:
      "maine nifty 25950 call li hai" → {symbol: NIFTY, strike: 25950, type: CE, action: BUY}
      "nifty 26000 pe sell ki" → {symbol: NIFTY, strike: 26000, type: PE, action: SELL}
      "25950 ki call 24 rs mein li" → {symbol: NIFTY, strike: 25950, type: CE, price: 24, action: BUY}
      "sensex 85000 put kharid li" → {symbol: SENSEX, strike: 85000, type: PE, action: BUY}
      "nifty 25950 call exit ki 35 pe" → {symbol: NIFTY, strike: 25950, type: CE, price: 35, action: SELL}
    """
    lower = text.lower().strip()
    
    # Check if it's a position statement
    buy_words = ['li hai', 'le li', 'li', 'kharidi', 'kharid li', 'buy ki', 'buy kiya',
                 'bought', 'entry', 'le liya', 'buy kari', 'le raha', 'liya hai',
                 'buy kar li', 'lia hai', 'buy kia', 'leli', 'khareedi', 'long',
                 'le lia', 'khareed li']
    sell_words = ['sell ki', 'bech di', 'bech diya', 'exit', 'sold', 'sell kiya',
                  'nikal di', 'nikal diya', 'book ki', 'profit book', 'loss book',
                  'sell kar di', 'bech dia', 'close ki', 'short', 'sell kia']
    
    action = None
    for w in buy_words:
        if w in lower:
            action = "BUY"
            break
    if not action:
        for w in sell_words:
            if w in lower:
                action = "SELL"
                break
    
    if not action:
        return None
    
    # Extract symbol
    symbol = "NIFTY"
    if "sensex" in lower or "bse" in lower:
        symbol = "SENSEX"
    elif "banknifty" in lower or "bank nifty" in lower:
        symbol = "BANKNIFTY"
    
    # Extract strike (4-6 digit number)
    strike_match = re.findall(r'\b(\d{4,6})\b', text)
    if not strike_match:
        return None
    strike = int(strike_match[0])
    
    # Validate range
    if symbol == "NIFTY" and not (15000 <= strike <= 35000):
        return None
    if symbol == "BANKNIFTY" and not (30000 <= strike <= 70000):
        return None
    if symbol == "SENSEX" and not (50000 <= strike <= 120000):
        return None
    
    # Extract option type
    opt_type = "CE"
    if any(w in lower for w in ['put', 'pe', 'पुट']):
        opt_type = "PE"
    elif any(w in lower for w in ['call', 'ce', 'कॉल']):
        opt_type = "CE"
    
    # Extract price (small number, typically < 1000)
    price = 0
    price_patterns = [
        r'(\d+\.?\d*)\s*(?:rs|rupee|rupees|₹|pe|par|mein|at|@)',
        r'(?:@|at|price|premium)\s*(\d+\.?\d*)',
        r'(\d{1,3}\.?\d*)\s*(?:ka|ki|ke)\s',
    ]
    for pp in price_patterns:
        pm = re.search(pp, lower)
        if pm:
            try:
                p = float(pm.group(1))
                if 0.5 <= p <= 5000:  # Valid option price range
                    price = p
                    break
            except:
                pass
    
    return {
        "symbol": symbol,
        "strike": strike,
        "option_type": opt_type,
        "action": action,
        "price": price,
        "raw_text": text,
    }


# ═══════════════════════════════════════════════════════════
#  FORMAT: Position Display
# ═══════════════════════════════════════════════════════════

def format_positions(chat_id: int) -> str:
    """Format all active positions for Telegram."""
    active = get_active_positions(chat_id)
    if not active:
        return "📊 *No Active Positions*\n_Koi tracked position nahi hai abhi._\n\n💡 _Likhiye: \"maine nifty 25950 call li\" aur JARVIS track karega!_"
    
    msg = "📊 *MY TRACKED POSITIONS* 📊\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    total_pnl = 0
    for p in active:
        sym = p.get("symbol", "?")
        strike = p.get("strike", 0)
        otype = p.get("option_type", "?")
        entry = p.get("entry_price", 0)
        current = p.get("current_price", entry)
        pnl = p.get("pnl", 0)
        pnl_pct = p.get("pnl_pct", 0)
        pid = p.get("id", 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        msg += (
            f"\n{emoji} *#{pid} {sym} {strike} {otype}*\n"
            f"   📥 Entry: ₹{entry:,.2f}\n"
            f"   📈 Current: ₹{current:,.2f}\n"
            f"   💰 P&L: ₹{pnl:+,.2f} ({pnl_pct:+.1f}%)\n"
        )
        
        # Show last analysis if available
        ah = p.get("analysis_history", [])
        if ah:
            last_a = ah[-1]
            msg += f"   🧠 _{last_a.get('analysis', '')[:100]}_\n"
        
        total_pnl += pnl
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    total_emoji = "🟢" if total_pnl >= 0 else "🔴"
    msg += f"{total_emoji} *Total P&L: ₹{total_pnl:+,.2f}*\n"
    msg += "\n💡 _Position close karne ke liye:_\n_\"nifty 25950 call sell ki 35 pe\"_"
    
    return msg


def format_position_voice(positions: List[dict]) -> str:
    """Format positions for voice output."""
    if not positions:
        return "Abhi koi tracked position nahi hai ji."
    
    voice = "Suniye ji! Aapki positions ka update... "
    for p in positions[:3]:  # Max 3 for voice
        sym = p.get("symbol", "")
        strike = p.get("strike", 0)
        otype = "call" if p.get("option_type") == "CE" else "put"
        pnl = p.get("pnl", 0)
        pnl_pct = p.get("pnl_pct", 0)
        
        if pnl >= 0:
            voice += f"{sym} {strike} {otype} mein {pnl_pct:.0f} percent profit hai... Badhiya! "
        else:
            voice += f"{sym} {strike} {otype} mein {abs(pnl_pct):.0f} percent loss hai... Thoda dhyan rakhiye. "
    
    voice += "Aur kuch puchna ho toh bataiye ji!"
    return voice


# ═══════════════════════════════════════════════════════════
#  MEMORY SEARCH — Find relevant past context
# ═══════════════════════════════════════════════════════════

def search_memory(chat_id: int, query: str, limit: int = 5) -> List[dict]:
    """Search through conversation memory for relevant messages."""
    mem = load_memory(chat_id)
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    results = []
    for msg in reversed(mem.get("conversations", [])):
        text_lower = msg.get("text", "").lower()
        # Simple keyword match scoring
        score = sum(1 for w in query_words if w in text_lower)
        if score > 0:
            results.append({**msg, "_score": score})
    
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:limit]


# ═══════════════════════════════════════════════════════════
#  MEMORY STATS
# ═══════════════════════════════════════════════════════════

def get_memory_stats(chat_id: int) -> dict:
    """Get memory statistics for a user."""
    mem = load_memory(chat_id)
    
    return {
        "conversations": len(mem.get("conversations", [])),
        "facts": len(mem.get("facts", {})),
        "positions_total": len(mem.get("positions", [])),
        "positions_open": len([p for p in mem.get("positions", []) if p.get("status") == "OPEN"]),
        "predictions": len(mem.get("predictions", [])),
        "learnings": len(mem.get("learnings", [])),
        "first_seen": mem.get("user_info", {}).get("first_seen", ""),
        "last_active": mem.get("last_active", ""),
        "accuracy": get_prediction_accuracy(chat_id),
    }


def format_memory_stats(chat_id: int) -> str:
    """Format memory stats for Telegram."""
    stats = get_memory_stats(chat_id)
    acc = stats["accuracy"]
    
    return (
        f"🧠💾 *JARVIS MEMORY STATUS* 💾🧠\n"
        f"╔══════════════════════════════╗\n"
        f"║ 💬 *Conversations:* {stats['conversations']}\n"
        f"║ 📝 *Stored Facts:* {stats['facts']}\n"
        f"║ 📊 *Positions:* {stats['positions_open']} open / {stats['positions_total']} total\n"
        f"║ 🔮 *Predictions:* {stats['predictions']}\n"
        f"║ 🧠 *Learnings:* {stats['learnings']}\n"
        f"║ 🎯 *Accuracy:* {acc['accuracy']}% ({acc['correct']}/{acc['correct']+acc['wrong']})\n"
        f"║ 📅 *First seen:* {stats['first_seen'][:10]}\n"
        f"║ ⏰ *Last active:* {stats['last_active'][:16]}\n"
        f"╚══════════════════════════════╝\n\n"
        f"💡 _JARVIS sab yaad rakhta hai — conversations, positions, predictions sab!_\n"
        f"_Main aapka full context samajhta hoon, jaise ChatGPT ya Claude!_ 🧠"
    )


# ═══════════════════════════════════════════════════════════
#  FLUSH ALL CACHES TO DISK
# ═══════════════════════════════════════════════════════════

def flush_all():
    """Save all cached memories to disk."""
    for cid in list(_memory_cache.keys()):
        save_memory(int(cid), force=True)
    logger.info(f"[MEMORY-PRO] Flushed {len(_memory_cache)} user memories to disk")


# ═══════════════════════════════════════════════════════════
#  UPDATE USER NAME
# ═══════════════════════════════════════════════════════════

def set_user_name(chat_id: int, name: str):
    """Store user's display name."""
    mem = load_memory(chat_id)
    mem["user_info"]["name"] = name
    remember_fact(chat_id, "name", name)


# ═══════════════════════════════════════════════════════════
#  MODULE STATUS
# ═══════════════════════════════════════════════════════════

MEMORY_PRO_AVAILABLE = True
logger.info(f"[MEMORY-PRO] 🧠💾 Super Memory loaded — persistent conversations + positions + facts")
