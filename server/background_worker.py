"""
JARVIS BACKGROUND WORKER v4.0 — 24/7 Auto-Running
Price monitoring, alert checking, auto-trading signals
"""
import asyncio, httpx, logging, time, json
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger("jarvis.worker")

# ═══ ALERTS SYSTEM ═══
alerts_store: Dict[str, List] = {}  # user_id -> [alerts]
triggered_alerts: List = []

def get_alerts(user_id):
    if user_id not in alerts_store:
        alerts_store[user_id] = []
    return alerts_store[user_id]

def create_alert(user_id, symbol, condition, price, note=""):
    alert = {
        "id": f"alert_{int(time.time())}_{len(get_alerts(user_id))}",
        "symbol": symbol.upper(),
        "condition": condition,  # "above" or "below"
        "target_price": price,
        "note": note,
        "active": True,
        "created": datetime.utcnow().isoformat(),
        "triggered": False,
        "triggered_at": None
    }
    get_alerts(user_id).append(alert)
    return alert

def delete_alert(user_id, alert_id):
    alerts = get_alerts(user_id)
    alerts_store[user_id] = [a for a in alerts if a["id"] != alert_id]
    return {"success": True}


# ═══ MEMORY SYSTEM ═══
memory_store: Dict[str, Dict] = {}

def remember(user_id, key, value):
    if user_id not in memory_store:
        memory_store[user_id] = {}
    memory_store[user_id][key] = {"value": value, "stored_at": datetime.utcnow().isoformat()}
    return {"success": True, "key": key}

def recall(user_id, key):
    if user_id in memory_store and key in memory_store[user_id]:
        return memory_store[user_id][key]
    return {"error": "Not found", "key": key}


# ═══ BACKGROUND PRICE CHECKER ═══
class BackgroundWorker:
    def __init__(self):
        self.running = False
        self.last_prices = {}
        self.check_interval = 30  # seconds
        self.task = None
    
    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Background worker started — monitoring prices 24/7")
    
    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Background worker stopped")
    
    async def _run(self):
        while self.running:
            try:
                await self._check_alerts()
            except Exception as e:
                logger.error(f"Worker error: {e}")
            await asyncio.sleep(self.check_interval)
    
    async def _check_alerts(self):
        """Check all active alerts against current prices"""
        # Collect all unique symbols
        symbols = set()
        for user_id, alerts in alerts_store.items():
            for alert in alerts:
                if alert["active"]:
                    symbols.add(alert["symbol"].lower())
        
        if not symbols:
            return
        
        # Fetch current prices
        async with httpx.AsyncClient() as client:
            try:
                ids = ",".join(symbols)
                r = await client.get(f"https://api.coingecko.com/api/v3/simple/price", params={
                    "ids": ids, "vs_currencies": "usd"
                }, timeout=10)
                if r.status_code == 200:
                    prices = r.json()
                    self.last_prices.update(prices)
                    
                    # Check alerts
                    for user_id, alerts in alerts_store.items():
                        for alert in alerts:
                            if not alert["active"]:
                                continue
                            sym = alert["symbol"].lower()
                            if sym in prices:
                                current = prices[sym].get("usd", 0)
                                if alert["condition"] == "above" and current >= alert["target_price"]:
                                    alert["triggered"] = True
                                    alert["triggered_at"] = datetime.utcnow().isoformat()
                                    alert["active"] = False
                                    alert["trigger_price"] = current
                                    triggered_alerts.append({**alert, "user_id": user_id})
                                    logger.info(f"ALERT TRIGGERED: {alert['symbol']} above {alert['target_price']} (current: {current})")
                                elif alert["condition"] == "below" and current <= alert["target_price"]:
                                    alert["triggered"] = True
                                    alert["triggered_at"] = datetime.utcnow().isoformat()
                                    alert["active"] = False
                                    alert["trigger_price"] = current
                                    triggered_alerts.append({**alert, "user_id": user_id})
                                    logger.info(f"ALERT TRIGGERED: {alert['symbol']} below {alert['target_price']} (current: {current})")
            except Exception as e:
                logger.error(f"Price check error: {e}")


# Singleton
worker = BackgroundWorker()
