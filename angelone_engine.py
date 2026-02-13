"""
📈 Angel One Trading Engine — Real-time Indian Stock Trading
═══════════════════════════════════════════════════════════════
Live market data, order placement, portfolio tracking via Angel One API.
"""

import os, json, logging, time, hashlib, hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger("angelone-engine")
IST = timezone(timedelta(hours=5, minutes=30))

# Angel One API config
ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
ANGEL_TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")

_session_token = None
_session_expiry = 0

# ═══════════════════════════════════════════════════════════
#  Angel One API Integration
# ═══════════════════════════════════════════════════════════

async def _get_session():
    """Get or refresh Angel One session."""
    global _session_token, _session_expiry
    if _session_token and time.time() < _session_expiry:
        return _session_token
    
    if not ANGEL_API_KEY:
        logger.warning("Angel One API key not configured")
        return None
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Generate TOTP if key available
            totp = ""
            if ANGEL_TOTP_KEY:
                try:
                    import pyotp
                    totp = pyotp.TOTP(ANGEL_TOTP_KEY).now()
                except ImportError:
                    pass
            
            resp = await client.post(
                "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-ClientLocalIP": "127.0.0.1",
                    "X-ClientPublicIP": "127.0.0.1",
                    "X-MACAddress": "00:00:00:00:00:00",
                    "X-PrivateKey": ANGEL_API_KEY
                },
                json={
                    "clientcode": ANGEL_CLIENT_ID,
                    "password": ANGEL_PASSWORD,
                    "totp": totp
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status"):
                    _session_token = data["data"]["jwtToken"]
                    _session_expiry = time.time() + 3600  # 1 hour
                    logger.info("Angel One session established")
                    return _session_token
    except Exception as e:
        logger.warning(f"Angel One login failed: {e}")
    
    return None


async def angel_get_portfolio() -> Dict:
    """Get Angel One portfolio holdings."""
    token = await _get_session()
    if not token:
        return {"holdings": [], "total_value": 0, "pnl": 0, "status": "not_connected"}
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/portfolio/v1/getHolding",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": ANGEL_API_KEY
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                holdings = data.get("data", []) or []
                total_value = sum(h.get("ltp", 0) * h.get("quantity", 0) for h in holdings)
                total_invested = sum(h.get("averageprice", 0) * h.get("quantity", 0) for h in holdings)
                pnl = total_value - total_invested
                
                return {
                    "holdings": [{
                        "symbol": h.get("tradingsymbol", ""),
                        "name": h.get("symbolname", ""),
                        "qty": h.get("quantity", 0),
                        "avg_price": h.get("averageprice", 0),
                        "ltp": h.get("ltp", 0),
                        "pnl": h.get("pnl", 0),
                        "pnl_pct": round(((h.get("ltp", 0) / h.get("averageprice", 1)) - 1) * 100, 2) if h.get("averageprice", 0) else 0
                    } for h in holdings],
                    "total_value": round(total_value, 2),
                    "total_invested": round(total_invested, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / total_invested * 100) if total_invested else 0, 2),
                    "status": "connected"
                }
    except Exception as e:
        logger.warning(f"Angel One portfolio error: {e}")
    
    return {"holdings": [], "total_value": 0, "status": "error"}


async def angel_get_positions() -> List[Dict]:
    """Get open positions."""
    token = await _get_session()
    if not token:
        return []
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/getPosition",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": ANGEL_API_KEY
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", []) or []
    except Exception as e:
        logger.warning(f"Angel One positions error: {e}")
    
    return []


async def angel_place_order(
    symbol: str,
    qty: int,
    side: str = "BUY",
    order_type: str = "MARKET",
    price: float = 0,
    exchange: str = "NSE",
    product_type: str = "DELIVERY"
) -> Dict:
    """Place order on Angel One."""
    token = await _get_session()
    if not token:
        return {"success": False, "error": "Not connected to Angel One"}
    
    try:
        import httpx
        
        # Get token symbol info
        symbol_token = await _get_symbol_token(symbol, exchange)
        if not symbol_token:
            return {"success": False, "error": f"Symbol {symbol} not found"}
        
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": symbol_token,
            "transactiontype": side.upper(),
            "exchange": exchange,
            "ordertype": order_type,
            "producttype": product_type,
            "duration": "DAY",
            "quantity": str(qty)
        }
        
        if order_type == "LIMIT" and price > 0:
            order_params["price"] = str(price)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/placeOrder",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": ANGEL_API_KEY
                },
                json=order_params
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status"):
                    return {
                        "success": True,
                        "order_id": data["data"]["orderid"],
                        "symbol": symbol,
                        "side": side,
                        "qty": qty,
                        "message": f"Order placed: {side} {qty} x {symbol}"
                    }
                return {"success": False, "error": data.get("message", "Order failed")}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "Order failed"}


async def angel_get_order_book() -> List[Dict]:
    """Get order book."""
    token = await _get_session()
    if not token:
        return []
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/getOrderBook",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": ANGEL_API_KEY
                }
            )
            if resp.status_code == 200:
                return resp.json().get("data", []) or []
    except Exception as e:
        logger.warning(f"Angel One order book error: {e}")
    
    return []


async def angel_get_ltp(symbol: str, exchange: str = "NSE") -> Dict:
    """Get live price for a symbol."""
    token = await _get_session()
    if not token:
        # Fallback to yfinance
        return await _yfinance_price(symbol)
    
    try:
        import httpx
        symbol_token = await _get_symbol_token(symbol, exchange)
        if not symbol_token:
            return await _yfinance_price(symbol)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/getLtpData",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": ANGEL_API_KEY
                },
                json={
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "symboltoken": symbol_token
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                ltp = data.get("data", {}).get("ltp", 0)
                return {"symbol": symbol, "ltp": ltp, "exchange": exchange}
    except Exception as e:
        logger.warning(f"Angel LTP error: {e}")
    
    return await _yfinance_price(symbol)


async def _yfinance_price(symbol: str) -> Dict:
    """Fallback price from yfinance."""
    try:
        import yfinance as yf
        import asyncio
        
        nse_sym = f"{symbol}.NS"
        tk = await asyncio.to_thread(lambda: yf.Ticker(nse_sym).info)
        return {
            "symbol": symbol,
            "ltp": tk.get("currentPrice", tk.get("regularMarketPrice", 0)),
            "exchange": "NSE",
            "source": "yfinance"
        }
    except:
        return {"symbol": symbol, "ltp": 0, "error": "Not found"}


_symbol_cache: Dict[str, str] = {}

async def _get_symbol_token(symbol: str, exchange: str = "NSE") -> Optional[str]:
    """Get Angel One symbol token for a trading symbol."""
    cache_key = f"{exchange}:{symbol}"
    if cache_key in _symbol_cache:
        return _symbol_cache[cache_key]
    
    # Common symbol tokens
    common_tokens = {
        "NSE:RELIANCE": "2885", "NSE:TCS": "11536", "NSE:HDFCBANK": "1333",
        "NSE:INFY": "1594", "NSE:ICICIBANK": "4963", "NSE:SBIN": "3045",
        "NSE:BHARTIARTL": "10604", "NSE:ITC": "1660", "NSE:KOTAKBANK": "1922",
        "NSE:LT": "11483", "NSE:HINDUNILVR": "1394", "NSE:WIPRO": "3787",
        "NSE:TATAMOTORS": "3456", "NSE:AXISBANK": "5900", "NSE:SUNPHARMA": "3351",
        "NSE:ADANIENT": "25", "NSE:BAJFINANCE": "317", "NSE:MARUTI": "10999",
        "NSE:TITAN": "3506", "NSE:ASIANPAINT": "236",
        "NSE:NIFTY": "99926000", "NSE:BANKNIFTY": "99926009"
    }
    
    token = common_tokens.get(cache_key)
    if token:
        _symbol_cache[cache_key] = token
        return token
    
    return None


async def angel_get_market_status() -> Dict:
    """Check if market is open."""
    now = datetime.now(IST)
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    hour = now.hour
    minute = now.minute
    
    is_open = (weekday < 5 and 
               ((hour == 9 and minute >= 15) or (hour > 9 and hour < 15) or 
                (hour == 15 and minute <= 30)))
    
    pre_market = weekday < 5 and hour == 9 and minute < 15
    
    return {
        "is_open": is_open,
        "pre_market": pre_market,
        "session": "LIVE" if is_open else "PRE-OPEN" if pre_market else "CLOSED",
        "next_open": "09:15 IST" if not is_open else "Now",
        "time": now.strftime("%H:%M IST"),
        "day": now.strftime("%A")
    }


def is_angel_configured() -> bool:
    """Check if Angel One API is configured."""
    return bool(ANGEL_API_KEY and ANGEL_CLIENT_ID)


logger.info(f"📈 Angel One Engine loaded — {'Configured' if is_angel_configured() else 'Not configured'}")
