"""
🌐 JARVIS Social Trading — Share, Follow, Leaderboard
═══════════════════════════════════════════════════════
- Share trading signals to community
- Like and track signals
- Leaderboard by performance
- Top traders ranking
- Social feed
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger("jarvis-social")
IST = timezone(timedelta(hours=5, minutes=30))

# In-memory store (backed by PostgreSQL when available)
_signals: List[Dict] = []
_likes: Dict[str, set] = defaultdict(set)  # signal_id → set of user_ids
_followers: Dict[str, set] = defaultdict(set)  # user_id → set of follower_ids
_trader_stats: Dict[str, Dict] = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pnl": 0.0, "signals": 0})
MAX_FEED = 500


# ═══════════════════════════════════════════════════════════
#  SHARE SIGNAL
# ═══════════════════════════════════════════════════════════
def share_signal(user_id: str, username: str, signal: Dict) -> Dict:
    """Share a trading signal to the community."""
    entry = {
        "id": f"sig_{int(time.time())}_{len(_signals)}",
        "user_id": user_id,
        "username": username,
        "symbol": signal.get("symbol", "???"),
        "action": signal.get("action", "HOLD"),
        "confidence": signal.get("confidence", 0),
        "price": signal.get("price", 0),
        "target_price": signal.get("target_price"),
        "stop_loss": signal.get("stop_loss"),
        "timeframe": signal.get("timeframe", "1h"),
        "analysis": signal.get("analysis", ""),
        "likes": 0,
        "timestamp": datetime.now(IST).isoformat(),
        "status": "active",  # active, hit_target, stopped_out, expired
        "result_pnl": None,
    }
    _signals.append(entry)
    _trader_stats[user_id]["signals"] += 1

    if len(_signals) > MAX_FEED:
        _signals.pop(0)

    return entry


# ═══════════════════════════════════════════════════════════
#  SOCIAL FEED
# ═══════════════════════════════════════════════════════════
def get_feed(limit: int = 20, offset: int = 0, filter_action: str = None) -> List[Dict]:
    """Get social trading feed."""
    feed = list(reversed(_signals))
    if filter_action:
        feed = [s for s in feed if s.get("action") == filter_action.upper()]
    # Hydrate like counts
    for s in feed:
        s["likes"] = len(_likes.get(s["id"], set()))
    return feed[offset:offset + limit]


def get_user_signals(user_id: str, limit: int = 20) -> List[Dict]:
    """Get signals shared by a specific user."""
    return [s for s in reversed(_signals) if s.get("user_id") == user_id][:limit]


# ═══════════════════════════════════════════════════════════
#  LIKES
# ═══════════════════════════════════════════════════════════
def like_signal(signal_id: str, user_id: str) -> int:
    """Like a signal. Returns new like count."""
    _likes[signal_id].add(user_id)
    return len(_likes[signal_id])


def unlike_signal(signal_id: str, user_id: str) -> int:
    """Unlike a signal."""
    _likes[signal_id].discard(user_id)
    return len(_likes[signal_id])


def get_likes(signal_id: str) -> int:
    """Get like count for a signal."""
    return len(_likes.get(signal_id, set()))


# ═══════════════════════════════════════════════════════════
#  FOLLOW / UNFOLLOW
# ═══════════════════════════════════════════════════════════
def follow_trader(follower_id: str, trader_id: str) -> bool:
    """Follow a trader."""
    if follower_id == trader_id:
        return False
    _followers[trader_id].add(follower_id)
    return True


def unfollow_trader(follower_id: str, trader_id: str) -> bool:
    """Unfollow a trader."""
    _followers[trader_id].discard(follower_id)
    return True


def get_followers(trader_id: str) -> List[str]:
    """Get follower list for a trader."""
    return list(_followers.get(trader_id, set()))


def get_following(user_id: str) -> List[str]:
    """Get list of traders a user follows."""
    return [tid for tid, followers in _followers.items() if user_id in followers]


# ═══════════════════════════════════════════════════════════
#  LEADERBOARD
# ═══════════════════════════════════════════════════════════
def update_signal_result(signal_id: str, result_pnl: float):
    """Update signal with actual result (for leaderboard tracking)."""
    for s in _signals:
        if s["id"] == signal_id:
            s["result_pnl"] = result_pnl
            s["status"] = "hit_target" if result_pnl > 0 else "stopped_out"
            uid = s["user_id"]
            if result_pnl > 0:
                _trader_stats[uid]["wins"] += 1
            else:
                _trader_stats[uid]["losses"] += 1
            _trader_stats[uid]["total_pnl"] += result_pnl
            break


def get_leaderboard(limit: int = 20) -> List[Dict]:
    """Get top traders by performance."""
    leaders = []
    for user_id, stats in _trader_stats.items():
        total = stats["wins"] + stats["losses"]
        win_rate = (stats["wins"] / total * 100) if total > 0 else 0
        leaders.append({
            "user_id": user_id,
            "username": _get_username(user_id),
            "wins": stats["wins"],
            "losses": stats["losses"],
            "win_rate": round(win_rate, 1),
            "total_pnl": round(stats["total_pnl"], 2),
            "total_signals": stats["signals"],
            "followers": len(_followers.get(user_id, set())),
            "score": round(win_rate * 0.4 + stats["total_pnl"] * 0.4 + stats["signals"] * 0.2, 1),
        })
    leaders.sort(key=lambda x: x["score"], reverse=True)
    return leaders[:limit]


def _get_username(user_id: str) -> str:
    """Get username from signals."""
    for s in reversed(_signals):
        if s.get("user_id") == user_id:
            return s.get("username", user_id[:8])
    return user_id[:8]


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
def get_social_stats() -> Dict:
    """Get social trading stats."""
    total_likes = sum(len(v) for v in _likes.values())
    total_followers = sum(len(v) for v in _followers.values())
    active_signals = len([s for s in _signals if s.get("status") == "active"])
    return {
        "total_signals": len(_signals),
        "active_signals": active_signals,
        "total_traders": len(_trader_stats),
        "total_likes": total_likes,
        "total_follows": total_followers,
        "top_traders": get_leaderboard(5),
    }


# Alias for server compatibility
get_stats = get_social_stats

# ═══════════════════════════════════════════════════════════
#  FASTAPI ROUTER
# ═══════════════════════════════════════════════════════════
try:
    from fastapi import APIRouter
    social_router = APIRouter(prefix="/api/social", tags=["social"])

    @social_router.get("/feed")
    async def api_feed(limit: int = 20, offset: int = 0, action: str = None):
        return {"feed": get_feed(limit, offset, action)}

    @social_router.post("/like")
    async def api_like(data: dict):
        count = like_signal(data.get("signal_id", ""), data.get("user_id", ""))
        return {"likes": count}

    @social_router.post("/follow")
    async def api_follow(data: dict):
        ok = follow_trader(data.get("follower_id", ""), data.get("trader_id", ""))
        return {"success": ok}

    @social_router.get("/leaderboard")
    async def api_leaderboard(limit: int = 20):
        return {"leaderboard": get_leaderboard(limit)}

except ImportError:
    social_router = None

SOCIAL_AVAILABLE = True
logger.info("🌐 Social trading engine loaded")
