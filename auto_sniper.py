"""
🎯 Auto Sniper v2.0 — Automated Crypto Trading Engine
═══════════════════════════════════════════════════════════
Auto-buy at dips, auto-sell at targets.
Risk management. Compound profits. Zero emotions.
"""

import os, json, logging, time, asyncio, uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger("auto-sniper")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
POSITIONS_FILE = DATA_DIR / "positions.json"
TRADES_FILE = DATA_DIR / "trades.json"
SNIPER_CONFIG_FILE = DATA_DIR / "sniper_config.json"

# Default strategies
STRATEGIES = {
    "conservative": {
        "name": "Conservative",
        "description": "Low risk, steady gains. Buys at -10% dip, sells at +15%.",
        "risk_level": "LOW",
        "min_amount": 500,
        "buy_dip_pct": -10,
        "sell_target_pct": 15,
        "stop_loss_pct": -8,
        "max_positions": 3,
        "min_liquidity": 50000,
        "min_volume": 10000,
        "compound": False,
    },
    "balanced": {
        "name": "Balanced",
        "description": "Moderate risk. Buys at -5% dip, sells at +25%. Good risk/reward.",
        "risk_level": "MEDIUM",
        "min_amount": 200,
        "buy_dip_pct": -5,
        "sell_target_pct": 25,
        "stop_loss_pct": -12,
        "max_positions": 5,
        "min_liquidity": 20000,
        "min_volume": 5000,
        "compound": True,
    },
    "aggressive": {
        "name": "Aggressive",
        "description": "High risk, high reward. Targets 50-100%+ gains on meme coins.",
        "risk_level": "HIGH",
        "min_amount": 100,
        "buy_dip_pct": -3,
        "sell_target_pct": 50,
        "stop_loss_pct": -20,
        "max_positions": 8,
        "min_liquidity": 5000,
        "min_volume": 1000,
        "compound": True,
    },
    "scalper": {
        "name": "Scalper",
        "description": "Quick in-and-out. Small gains, many trades. 5-10% targets.",
        "risk_level": "MEDIUM",
        "min_amount": 100,
        "buy_dip_pct": -2,
        "sell_target_pct": 8,
        "stop_loss_pct": -5,
        "max_positions": 10,
        "min_liquidity": 10000,
        "min_volume": 5000,
        "compound": False,
    },
    "moonshot": {
        "name": "Moonshot Hunter",
        "description": "Extreme risk. Hunts for 100x-1000x on new Pump.fun coins.",
        "risk_level": "EXTREME",
        "min_amount": 50,
        "buy_dip_pct": -1,
        "sell_target_pct": 200,
        "stop_loss_pct": -50,
        "max_positions": 15,
        "min_liquidity": 1000,
        "min_volume": 500,
        "compound": True,
    },
}


# ═══════════════════════════════════════════════════════════
#  DATA PERSISTENCE
# ═══════════════════════════════════════════════════════════
def _load_json(path: Path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except:
        pass
    return default if default is not None else {}


def _save_json(path: Path, data):
    try:
        path.write_text(json.dumps(data, indent=2, default=str))
    except Exception as e:
        logger.error(f"Save error {path}: {e}")


# ═══════════════════════════════════════════════════════════
#  POSITION MANAGEMENT
# ═══════════════════════════════════════════════════════════
class PositionManager:
    def __init__(self):
        self._positions: Dict[str, Dict] = _load_json(POSITIONS_FILE, {})
        self._trades: List[Dict] = _load_json(TRADES_FILE, [])
        self._snipers: Dict[str, Dict] = _load_json(SNIPER_CONFIG_FILE, {})
    
    def save(self):
        _save_json(POSITIONS_FILE, self._positions)
        _save_json(TRADES_FILE, self._trades)
        _save_json(SNIPER_CONFIG_FILE, self._snipers)
    
    # ─── Sniper Management ───
    def start_sniper(self, user_id: int, amount: float, strategy: str = "balanced",
                      target_inr: float = 0, auto_withdraw: bool = False) -> Dict:
        """Start auto-sniper for a user."""
        uid = str(user_id)
        strat = STRATEGIES.get(strategy, STRATEGIES["balanced"])
        
        if amount < strat["min_amount"]:
            return {"error": f"Minimum amount is ₹{strat['min_amount']} for {strat['name']} strategy"}
        
        sniper_id = str(uuid.uuid4())[:8]
        self._snipers[uid] = {
            "id": sniper_id,
            "user_id": user_id,
            "active": True,
            "strategy": strategy,
            "strategy_config": strat,
            "initial_amount": amount,
            "current_amount": amount,
            "target_inr": target_inr,
            "auto_withdraw": auto_withdraw,
            "total_profit": 0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "positions": [],
            "started_at": datetime.now(IST).isoformat(),
            "last_scan": None,
        }
        self.save()
        return {
            "success": True,
            "sniper_id": sniper_id,
            "message": f"🎯 Auto-Sniper started!\nStrategy: {strat['name']}\nAmount: ₹{amount}\nTarget: {'₹' + str(target_inr) if target_inr else 'Unlimited'}\nMax positions: {strat['max_positions']}",
        }
    
    def stop_sniper(self, user_id: int, sell_all: bool = True) -> Dict:
        """Stop auto-sniper for a user."""
        uid = str(user_id)
        if uid not in self._snipers:
            return {"error": "No active sniper found"}
        
        sniper = self._snipers[uid]
        sniper["active"] = False
        sniper["stopped_at"] = datetime.now(IST).isoformat()
        
        result = {
            "success": True,
            "message": "Auto-Sniper stopped",
            "total_profit": sniper.get("total_profit", 0),
            "total_trades": sniper.get("total_trades", 0),
            "win_rate": round(sniper["wins"] / max(sniper["total_trades"], 1) * 100, 1),
        }
        
        if sell_all:
            # Mark all positions for selling
            positions = self._get_user_positions(user_id)
            result["positions_to_sell"] = len(positions)
        
        self.save()
        return result
    
    def get_sniper_status(self, user_id: int) -> Dict:
        """Get sniper status for a user."""
        uid = str(user_id)
        sniper = self._snipers.get(uid)
        if not sniper:
            return {"traders": [], "active_count": 0}
        
        positions = self._get_user_positions(user_id)
        return {
            "traders": [{
                "id": sniper.get("id", ""),
                "strategy": sniper.get("strategy", "balanced"),
                "strategy_name": sniper.get("strategy_config", {}).get("name", "Balanced"),
                "active": sniper.get("active", False),
                "amount": sniper.get("current_amount", 0),
                "initial_amount": sniper.get("initial_amount", 0),
                "profit": sniper.get("total_profit", 0),
                "trades": sniper.get("total_trades", 0),
                "wins": sniper.get("wins", 0),
                "losses": sniper.get("losses", 0),
                "win_rate": round(sniper["wins"] / max(sniper["total_trades"], 1) * 100, 1),
                "positions": len(positions),
                "started_at": sniper.get("started_at", ""),
            }],
            "active_count": 1 if sniper.get("active") else 0,
        }
    
    def compound_profits(self, user_id: int) -> Dict:
        """Compound all profits back into trading."""
        uid = str(user_id)
        sniper = self._snipers.get(uid)
        if not sniper:
            return {"error": "No sniper found"}
        
        profit = sniper.get("total_profit", 0)
        if profit <= 0:
            return {"error": "No profits to compound"}
        
        sniper["current_amount"] += profit
        sniper["total_profit"] = 0
        self.save()
        
        return {
            "success": True,
            "message": f"₹{profit:.2f} compounded! New trading amount: ₹{sniper['current_amount']:.2f}",
            "new_amount": sniper["current_amount"],
        }
    
    def get_performance(self, user_id: int) -> Dict:
        """Get performance report for user."""
        uid = str(user_id)
        sniper = self._snipers.get(uid, {})
        user_trades = [t for t in self._trades if t.get("user_id") == user_id]
        
        total_profit = sum(t.get("profit", 0) for t in user_trades)
        wins = sum(1 for t in user_trades if t.get("profit", 0) > 0)
        losses = sum(1 for t in user_trades if t.get("profit", 0) <= 0)
        
        return {
            "total_profit": round(total_profit, 2),
            "total_trades": len(user_trades),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / max(len(user_trades), 1) * 100, 1),
            "active_positions": len(self._get_user_positions(user_id)),
            "best_trade": max([t.get("profit", 0) for t in user_trades], default=0),
            "worst_trade": min([t.get("profit", 0) for t in user_trades], default=0),
            "current_amount": sniper.get("current_amount", 0),
            "initial_amount": sniper.get("initial_amount", 0),
            "roi_pct": round(total_profit / max(sniper.get("initial_amount", 1), 1) * 100, 1),
        }
    
    # ─── Position helpers ───
    def _get_user_positions(self, user_id: int) -> List[Dict]:
        return [p for p in self._positions.values() if p.get("user_id") == user_id and p.get("status") == "open"]
    
    def add_position(self, user_id: int, token: Dict, amount: float) -> Dict:
        """Open a new position."""
        pos_id = str(uuid.uuid4())[:8]
        position = {
            "id": pos_id,
            "user_id": user_id,
            "symbol": token.get("symbol", ""),
            "name": token.get("name", ""),
            "address": token.get("base_address", token.get("address", "")),
            "chain": token.get("chain", "solana"),
            "entry_price": token.get("price_usd", 0),
            "amount_invested": amount,
            "tokens_bought": amount / max(token.get("price_usd", 0.000001), 0.000001),
            "current_price": token.get("price_usd", 0),
            "current_value": amount,
            "pnl": 0,
            "pnl_pct": 0,
            "status": "open",
            "opened_at": datetime.now(IST).isoformat(),
            "source": token.get("source", "dexscreener"),
        }
        self._positions[pos_id] = position
        self.save()
        return position
    
    def close_position(self, pos_id: str, current_price: float) -> Dict:
        """Close a position and record the trade."""
        pos = self._positions.get(pos_id)
        if not pos:
            return {"error": "Position not found"}
        
        entry = pos["entry_price"]
        tokens = pos["tokens_bought"]
        sell_value = tokens * current_price
        profit = sell_value - pos["amount_invested"]
        pnl_pct = (profit / pos["amount_invested"]) * 100 if pos["amount_invested"] else 0
        
        pos["status"] = "closed"
        pos["exit_price"] = current_price
        pos["final_value"] = sell_value
        pos["pnl"] = profit
        pos["pnl_pct"] = pnl_pct
        pos["closed_at"] = datetime.now(IST).isoformat()
        
        # Record trade
        trade = {
            "id": str(uuid.uuid4())[:8],
            "user_id": pos["user_id"],
            "position_id": pos_id,
            "symbol": pos["symbol"],
            "entry_price": entry,
            "exit_price": current_price,
            "amount": pos["amount_invested"],
            "profit": round(profit, 4),
            "pnl_pct": round(pnl_pct, 2),
            "duration": pos.get("opened_at", ""),
            "closed_at": datetime.now(IST).isoformat(),
        }
        self._trades.append(trade)
        
        # Update sniper stats
        uid = str(pos["user_id"])
        if uid in self._snipers:
            self._snipers[uid]["total_trades"] += 1
            self._snipers[uid]["total_profit"] += profit
            if profit > 0:
                self._snipers[uid]["wins"] += 1
                self._snipers[uid]["current_amount"] += profit
            else:
                self._snipers[uid]["losses"] += 1
        
        self.save()
        return {"success": True, "trade": trade}
    
    def get_all_positions(self, user_id: int) -> List[Dict]:
        """Get all positions (open and closed) for user."""
        return [p for p in self._positions.values() if p.get("user_id") == user_id]
    
    def get_open_positions(self, user_id: int) -> List[Dict]:
        """Get open positions for user."""
        return self._get_user_positions(user_id)
    
    def get_trades(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get trade history for user."""
        trades = [t for t in self._trades if t.get("user_id") == user_id]
        return sorted(trades, key=lambda t: t.get("closed_at", ""), reverse=True)[:limit]


# ═══════════════════════════════════════════════════════════
#  SNIPER SCANNER — Finds best tokens to buy
# ═══════════════════════════════════════════════════════════
async def scan_for_gems(strategy: str = "balanced") -> List[Dict]:
    """Scan markets for gems matching strategy criteria."""
    from dex_engine import find_dip_gems, dex_trending, pumpfun_trending
    
    strat = STRATEGIES.get(strategy, STRATEGIES["balanced"])
    
    # Get tokens from multiple sources
    results = await asyncio.gather(
        find_dip_gems(
            min_dip=strat["buy_dip_pct"],
            min_liquidity=strat["min_liquidity"],
            min_volume=strat["min_volume"],
        ),
        dex_trending(),
        return_exceptions=True,
    )
    
    dip_gems = results[0] if isinstance(results[0], list) else []
    trending = results[1] if isinstance(results[1], list) else []
    
    # Combine and rank
    all_tokens = dip_gems[:15]
    
    # Add trending tokens with high gem scores
    for t in trending[:10]:
        if t.get("gem_score", 0) > 60:
            all_tokens.append(t)
    
    return all_tokens


def get_all_strategies() -> List[Dict]:
    """Get all available strategies."""
    return [
        {
            "id": key,
            "name": val["name"],
            "description": val["description"],
            "risk_level": val["risk_level"],
            "min_amount": val["min_amount"],
            "buy_dip_pct": val["buy_dip_pct"],
            "sell_target_pct": val["sell_target_pct"],
            "stop_loss_pct": val["stop_loss_pct"],
            "max_positions": val["max_positions"],
        }
        for key, val in STRATEGIES.items()
    ]


# Global instance
_manager: Optional[PositionManager] = None


def get_manager() -> PositionManager:
    global _manager
    if _manager is None:
        _manager = PositionManager()
    return _manager
