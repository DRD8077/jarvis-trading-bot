"""
🚀 JARVIS Mini App API v4.0 — World's #1 AI Trading Platform
═══════════════════════════════════════════════════════════════
ALL 40+ modules. Real-time CoinDCX + DexScreener + Pump.fun + ML/AI.
Auto-trader, live signals, risk, sentiment, news, screener, airdrops,
rug detection, predictions, candle patterns, ultra AI, futures, options.
"""

import os, json, logging, asyncio, time, traceback, math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from functools import lru_cache

logger = logging.getLogger("miniapp-api")

# ═══════════════════════════════════════════════════════════
#  IN-MEMORY CACHE — makes repeated API hits instant
# ═══════════════════════════════════════════════════════════
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def _cached(key: str, ttl: int = 30):
    """Return cached data if available and not expired."""
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    return None

def _set_cache(key: str, data: Any):
    """Store data in cache."""
    _cache[key] = data
    _cache_ts[key] = time.time()

def _sanitize(obj):
    """Recursively replace NaN/Inf floats with 0 to prevent JSON errors."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj

class SafeJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(_sanitize(content), ensure_ascii=False).encode("utf-8")

# Override default response class for all routes
router = APIRouter(prefix="/api/miniapp", tags=["MiniApp"], default_response_class=SafeJSONResponse)
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  CACHE
# ═══════════════════════════════════════════════════════════
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def cached(key: str, ttl: int = 60):
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    return None

def set_cache(key: str, val: Any):
    _cache[key] = val
    _cache_ts[key] = time.time()

# ═══════════════════════════════════════════════════════════
#  SAFE IMPORTS — ALL 40+ MODULES
# ═══════════════════════════════════════════════════════════
def _imp(name):
    try:
        return __import__(name)
    except Exception as e:
        logger.warning(f"Module {name}: {e}")
        return None

_payment    = _imp("jarvis_payment")
_coindcx    = _imp("coindcx_engine")
_crypto     = _imp("crypto_engine")
_buy_sell   = _imp("buy_sell_engine")
_ml_pred    = _imp("ml_predictor")
_ml_pipe    = _imp("ml_pipeline")
_risk       = _imp("risk_manager")
_regime     = _imp("market_regime")
_auto_trader= _imp("auto_trader")
_ai_chat    = _imp("ai_chat")
_jarvis_ai  = _imp("jarvis_ai")
_sentiment  = _imp("sentiment_engine")
_ai_signals = _imp("ai_signals")
_news       = _imp("jarvis_news_brain")
_rug        = _imp("rug_detector")
_portfolio  = _imp("portfolio_tracker")
_predictions= _imp("prediction_tracker")
_airdrops   = _imp("airdrop_hunter")
_screener   = _imp("jarvis_screener_pro")
_futures    = _imp("jarvis_futures_brain")
_candle     = _imp("candle_analyzer")
_ultra      = _imp("jarvis_ultra_ai")
_market_brain = _imp("jarvis_market_brain")
_super_brain  = _imp("jarvis_super_brain")
_super_trader = _imp("jarvis_super_trader_brain")
_crypto_intel = _imp("crypto_intelligence")
_global_mkt   = _imp("global_market_analyzer")
_india_stock  = _imp("indian_stock_super_engine")
_nifty_brain  = _imp("nifty_super_brain")
_options      = _imp("options_engine")
_phantom      = _imp("phantom_wallet")
_solana       = _imp("solana_engine")
_whale        = _imp("whale_alert")
_backtester   = _imp("jarvis_backtester_pro")
_voice        = _imp("voice_engine")
_nifty_hunter = _imp("nifty_options_hunter")
_trade_tracker= _imp("trade_tracker")
_nse_live     = _imp("nse_live_engine")
_oi_trap      = _imp("oi_trap_brain")
_otm_atm      = _imp("otm_atm_engine")
_power_pred   = _imp("india_power_predictor")
_live_index   = _imp("live_index_engine")
_global_candle= _imp("global_candle_engine")
_intraday     = _imp("jarvis_intraday_scanner")
_options_pro  = _imp("jarvis_options_pro")
_cross_asset  = _imp("cross_asset_engine")

_loaded = {n: "ok" if m else "miss" for n, m in [
    ("payment", _payment), ("coindcx", _coindcx), ("crypto_engine", _crypto),
    ("buy_sell", _buy_sell), ("ml_predictor", _ml_pred), ("risk", _risk),
    ("regime", _regime), ("auto_trader", _auto_trader), ("ai_chat", _ai_chat),
    ("sentiment", _sentiment), ("ai_signals", _ai_signals), ("news", _news),
    ("rug_detector", _rug), ("portfolio", _portfolio), ("predictions", _predictions),
    ("airdrops", _airdrops), ("screener", _screener), ("futures", _futures),
    ("candle", _candle), ("ultra_ai", _ultra), ("market_brain", _market_brain),
    ("super_brain", _super_brain), ("super_trader", _super_trader),
    ("crypto_intel", _crypto_intel), ("global_market", _global_mkt),
    ("india_stock", _india_stock), ("options", _options),
    ("phantom", _phantom), ("solana", _solana), ("whale", _whale),
    ("backtester", _backtester), ("voice", _voice), ("nifty_hunter", _nifty_hunter),
]}
logger.info(f"JARVIS v4: {sum(1 for v in _loaded.values() if v=='ok')}/{len(_loaded)} modules loaded")


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
async def _safe(coro, default, timeout=20):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception as e:
        logger.warning(f"Async failed: {type(e).__name__}: {e}")
        return default

def _thread(fn, *a, **kw):
    return asyncio.to_thread(fn, *a, **kw)

# Alias — most endpoints use _run
_run = _thread


# ═══════════════════════════════════════════════════════════
#  1. HEALTH
# ═══════════════════════════════════════════════════════════
@router.get("/health")
async def health():
    return {"status": "ok", "version": "v4.0", "modules": _loaded,
            "loaded": sum(1 for v in _loaded.values() if v == "ok"),
            "total": len(_loaded), "ts": datetime.now(IST).isoformat()}


# ═══════════════════════════════════════════════════════════
#  2. DASHBOARD (parallel, cached)
# ═══════════════════════════════════════════════════════════
@router.get("/dashboard")
async def dashboard(user_id: Optional[str] = None):
    cache_key = f"dashboard_{user_id or 'anon'}"
    c = _cached(cache_key, 20)
    if c: return c
    res = await asyncio.gather(
        _safe(_thread(_get_portfolio, user_id), {}),
        _safe(_thread(_get_market_ticker), []),
        _safe(_thread(_get_quick_signals), [], timeout=30),
        _safe(_thread(_get_top_movers), {"gainers": [], "losers": []}),
        _safe(_thread(_get_market_regime), {}),
        _safe(_thread(_get_trader_status, user_id), {}),
        _safe(_thread(_get_sentiment), {}),
        _safe(_thread(_get_news_headlines, 8), []),
    )
    result = {
        "portfolio": res[0], "market_ticker": res[1], "signals": res[2],
        "top_movers": res[3], "regime": res[4], "auto_trader": res[5],
        "sentiment": res[6], "news": res[7],
        "ts": datetime.now(IST).isoformat(),
    }
    _set_cache(cache_key, result)
    return result


# ═══════════════════════════════════════════════════════════
#  3. MARKETS
# ═══════════════════════════════════════════════════════════
@router.get("/markets")
async def markets(category: Optional[str] = None):
    c = _cached("markets", 20)
    if c: return c
    r = await asyncio.gather(
        _safe(_thread(_get_coindcx_markets), [], timeout=15),
        _safe(_thread(_get_trending_gems), [], timeout=15),
        _safe(_thread(_get_indices), [], timeout=10),
    )
    result = {"crypto": r[0], "trending": r[1], "indices": r[2], "web3": []}
    if _coindcx:
        try:
            w3 = await _safe(_thread(_coindcx.get_all_web3_prices, 1, 30, "volume"), {}, timeout=10)
            result["web3"] = w3.get("tokens", [])[:30] if isinstance(w3, dict) else []
        except: pass
    _set_cache("markets", result)
    return result


# ═══════════════════════════════════════════════════════════
#  4. SIGNALS
# ═══════════════════════════════════════════════════════════
@router.get("/signals")
async def signals(market: str = "all"):
    hit = cached("signals_" + market, ttl=45)
    if hit is not None: return {"signals": hit, "count": len(hit)}
    tasks = []
    if market in ("all", "crypto") and _coindcx:
        tasks.append(_safe(_thread(_get_coindcx_signals, 8), [], timeout=45))
    if market in ("all", "crypto") and _buy_sell:
        tasks.append(_safe(_thread(_get_ta_signals), [], timeout=45))
    if market in ("all", "stock") and _buy_sell:
        tasks.append(_safe(_thread(_get_nifty_signals), [], timeout=45))
    gathered = await asyncio.gather(*tasks) if tasks else []
    result = []
    for batch in gathered:
        result.extend(batch)
    set_cache("signals_" + market, result)
    return {"signals": result, "count": len(result), "ts": datetime.now(IST).isoformat()}


# ═══════════════════════════════════════════════════════════
#  5. GEMS
# ═══════════════════════════════════════════════════════════
@router.get("/gems")
async def gems(source: str = "all", min_score: int = 5):
    hit = cached(f"gems_{source}_{min_score}", ttl=60)
    if hit is not None: return hit
    tasks = []
    if source in ("all", "dex", "dips") and _crypto:
        tasks.append(_safe(_thread(_crypto.scan_all_gems, min_score, 25), []))
    if source in ("all", "coindcx") and _coindcx:
        tasks.append(_safe(_thread(_get_coindcx_dips), []))
    gathered = await asyncio.gather(*tasks) if tasks else []
    all_gems = []
    for batch in gathered:
        all_gems.extend(batch if isinstance(batch, list) else [])
    result = {"gems": all_gems[:40], "count": len(all_gems), "source": source}
    set_cache(f"gems_{source}_{min_score}", result)
    return result


# ═══════════════════════════════════════════════════════════
#  6. WALLET & PORTFOLIO
# ═══════════════════════════════════════════════════════════
@router.get("/wallet")
async def wallet(user_id: str = "0"):
    uid = int(user_id)
    portfolio = _get_portfolio(user_id)
    txns = []
    if _payment and hasattr(_payment, 'get_transactions'):
        try: txns = _payment.get_transactions(uid)
        except: pass
    tax = {}
    if _payment and hasattr(_payment, 'calculate_crypto_tax'):
        try: tax = _payment.calculate_crypto_tax(uid)
        except: pass
    bal = portfolio.get("balance_inr", 0) if isinstance(portfolio, dict) else 0
    inv = portfolio.get("total_invested_inr", 0) if isinstance(portfolio, dict) else 0
    cur = portfolio.get("total_current_inr", 0) if isinstance(portfolio, dict) else 0
    return {
        "portfolio": portfolio, "balance_inr": bal,
        "total_deposited": inv, "total_withdrawn": 0,
        "total_profit": cur - inv, "transactions": txns[:20],
        "tax": tax, "ts": datetime.now(IST).isoformat(),
    }


# ═══════════════════════════════════════════════════════════
#  7. DEPOSIT / VERIFY / WITHDRAW
# ═══════════════════════════════════════════════════════════
@router.post("/deposit")
async def deposit(request: Request):
    body = await request.json()
    uid, amount = int(body.get("user_id", 0)), float(body.get("amount", 0))
    if amount < 100: return {"error": "Min deposit ₹100"}
    if not _payment: return {"error": "Payment unavailable"}
    try:
        return _payment.generate_deposit_qr(uid, amount)
    except Exception as e: return {"error": str(e)}

@router.post("/verify-deposit")
async def verify_deposit(request: Request):
    body = await request.json()
    uid, utr = int(body.get("user_id", 0)), body.get("utr", "")
    if not _payment: return {"error": "Payment unavailable"}
    try:
        return _payment.verify_deposit(uid, utr)
    except Exception as e: return {"error": str(e)}

@router.post("/withdraw")
async def withdraw(request: Request):
    body = await request.json()
    uid, amount = int(body.get("user_id", 0)), float(body.get("amount", 0))
    if amount < 100: return {"error": "Min withdrawal ₹100"}
    if not _payment: return {"error": "Payment unavailable"}
    try:
        if hasattr(_payment, 'request_withdrawal'):
            return _payment.request_withdrawal(uid, amount)
        return {"success": True, "message": f"₹{amount} withdrawal queued"}
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  8. AUTO-TRADER
# ═══════════════════════════════════════════════════════════
@router.get("/auto-trader/strategies")
async def at_strategies():
    if not _auto_trader: return {"strategies": []}
    try: return {"strategies": _auto_trader.get_all_strategies()}
    except: return {"strategies": []}

@router.post("/auto-trader/start")
async def at_start(request: Request):
    body = await request.json()
    uid = int(body.get("user_id", 0))
    amt = float(body.get("amount", 0))
    strat = body.get("strategy", "balanced")
    target = float(body.get("target_inr", 0))
    auto_wd = body.get("auto_withdraw", False)
    if not _auto_trader: return {"error": "Auto-trader unavailable"}
    if amt < 100: return {"error": "Min ₹100"}
    try:
        return await _thread(_auto_trader.start_auto_trader, uid, amt, strat, target, auto_wd)
    except Exception as e: return {"error": str(e)}

@router.post("/auto-trader/stop")
async def at_stop(request: Request):
    body = await request.json()
    uid, sell = int(body.get("user_id", 0)), body.get("sell_all", True)
    if not _auto_trader: return {"error": "Unavailable"}
    try:
        return await _thread(_auto_trader.stop_auto_trader, uid, sell)
    except Exception as e: return {"error": str(e)}

@router.get("/auto-trader/status")
async def at_status(user_id: str = "0"):
    if not _auto_trader: return {"traders": [], "active_count": 0}
    try: return _auto_trader.get_trader_status(int(user_id))
    except: return {"traders": [], "active_count": 0}

@router.get("/auto-trader/gems")
async def at_gems(strategy: str = "balanced"):
    if not _auto_trader: return {"gems_found": 0, "top_picks": []}
    try:
        return await _safe(_thread(_auto_trader.get_available_gems, strategy),
                          {"gems_found": 0, "top_picks": []}, timeout=15)
    except: return {"gems_found": 0, "top_picks": []}

@router.post("/auto-trader/compound")
async def at_compound(request: Request):
    body = await request.json()
    uid = int(body.get("user_id", 0))
    if not _auto_trader: return {"error": "Unavailable"}
    try: return await _thread(_auto_trader.compound_profits, uid)
    except Exception as e: return {"error": str(e)}

@router.get("/auto-trader/performance")
async def at_perf(user_id: str = Query(...)):
    if not _auto_trader: return {"error": "Unavailable"}
    try: return _auto_trader.get_performance_report(int(user_id))
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  9. SELL POSITIONS
# ═══════════════════════════════════════════════════════════
@router.post("/sell-position")
async def sell_pos(request: Request):
    body = await request.json()
    uid, pid = int(body.get("user_id", 0)), body.get("position_id", "")
    if not _payment: return {"error": "Unavailable"}
    try: return _payment.sell_position(uid, pid)
    except Exception as e: return {"error": str(e)}

@router.post("/sell-all")
async def sell_all(request: Request):
    body = await request.json()
    uid = int(body.get("user_id", 0))
    if not _payment: return {"error": "Unavailable"}
    try:
        if hasattr(_payment, 'sell_all_positions'):
            return _payment.sell_all_positions(uid)
        return {"error": "Not implemented"}
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  10. SENTIMENT
# ═══════════════════════════════════════════════════════════
@router.get("/sentiment")
async def sentiment_ep():
    hit = cached("sentiment_full", ttl=120)
    if hit is not None: return hit
    result = {"fear_greed": {}, "social": {}}
    if _sentiment:
        try: result["fear_greed"] = _sentiment.calculate_fear_greed_index()
        except: pass
        try:
            if hasattr(_sentiment, 'analyze_social_sentiment'):
                result["social"] = _sentiment.analyze_social_sentiment("crypto")
        except: pass
    set_cache("sentiment_full", result)
    return result


# ═══════════════════════════════════════════════════════════
#  11. NEWS
# ═══════════════════════════════════════════════════════════
@router.get("/news")
async def news_ep(limit: int = 15):
    hit = cached("news_full", ttl=180)
    if hit is not None: return {"news": hit[:limit], "count": min(len(hit), limit)}
    articles = _get_news_headlines(limit)
    set_cache("news_full", articles)
    return {"news": articles[:limit], "count": len(articles[:limit])}


# ═══════════════════════════════════════════════════════════
#  12. AI CHAT
# ═══════════════════════════════════════════════════════════
@router.post("/chat")
async def chat_ep(request: Request):
    body = await request.json()
    msg = body.get("message", "")
    uid = str(body.get("user_id", "0"))
    if not msg: return {"reply": "Please send a message."}
    reply = None
    if _ai_chat:
        for fn_name in ['chat_with_groq', 'chat_with_openai', 'chat_with_gemini']:
            if reply: break
            fn = getattr(_ai_chat, fn_name, None)
            if fn:
                try:
                    if fn_name == 'chat_with_groq':
                        reply = await _safe(_thread(fn, msg, None, int(uid)), None, timeout=15)
                    else:
                        reply = await _safe(_thread(fn, msg), None, timeout=15)
                except: pass
    return {"reply": reply or "AI services temporarily unavailable. Please try again."}


# ═══════════════════════════════════════════════════════════
#  13. ANALYZE — Deep analysis
# ═══════════════════════════════════════════════════════════
@router.get("/analyze")
async def analyze_ep(symbol: str = Query(...)):
    tasks = {}
    if _coindcx: tasks["coindcx"] = _safe(_thread(_analyze_coindcx, symbol), {}, timeout=30)
    if _rug: tasks["rug"] = _safe(_thread(_analyze_rug, symbol), {}, timeout=20)
    if _ultra: tasks["ultra"] = _safe(_thread(_analyze_ultra, symbol), {}, timeout=30)
    if _market_brain: tasks["deep"] = _safe(_thread(_analyze_deep, symbol), {}, timeout=30)
    result = {"symbol": symbol}
    if tasks:
        keys = list(tasks.keys())
        values = await asyncio.gather(*tasks.values())
        for k, v in zip(keys, values):
            result[k] = v
    return result


# ═══════════════════════════════════════════════════════════
#  14. PREDICTIONS
# ═══════════════════════════════════════════════════════════
@router.get("/predictions")
async def predictions_ep():
    if not _predictions: return {"total": 0, "accuracy": 0}
    try: return _predictions.get_accuracy_report()
    except: return {"total": 0, "accuracy": 0}


# ═══════════════════════════════════════════════════════════
#  15. AIRDROPS
# ═══════════════════════════════════════════════════════════
@router.get("/airdrops")
async def airdrops_ep():
    hit = cached("airdrops", ttl=300)
    if hit is not None: return hit
    result = {"protocols": []}
    if _airdrops:
        try:
            raw = _airdrops.airdrop_upcoming()
            if isinstance(raw, str):
                protocols = []
                current = {}
                for line in raw.split("\n"):
                    line = line.strip()
                    # Match lines like "*1. Phantom* 🟣" or "🔹 Name" or "🪙 Name"
                    is_header = False
                    if line.startswith("🔹") or line.startswith("🪙"):
                        is_header = True
                    elif line.startswith("*") and ". " in line[:8]:
                        is_header = True
                    if is_header:
                        if current: protocols.append(current)
                        name = line
                        # Remove emoji prefixes
                        for prefix in ["🔹", "🪙", "🟣", "🟢", "🟡"]:
                            name = name.replace(prefix, "")
                        # Extract name between asterisks
                        if "*" in name and name.count("*") >= 2:
                            parts = name.split("*")
                            for p in parts:
                                p = p.strip()
                                if p and not p[0].isdigit() and len(p) > 2:
                                    name = p
                                    break
                        name = name.strip().strip("*").strip()
                        current = {"name": name, "details": []}
                    elif line and current and len(line) > 5 and not line.startswith("━") and not line.startswith("🔮"):
                        # Clean detail line
                        detail = line.replace("_", "").strip()
                        if detail: current["details"].append(detail)
                if current: protocols.append(current)
                result["protocols"] = protocols[:15]
            elif isinstance(raw, list):
                result["protocols"] = raw[:15]
        except: pass
    set_cache("airdrops", result)
    return result


# ═══════════════════════════════════════════════════════════
#  16. RUG DETECTOR
# ═══════════════════════════════════════════════════════════
@router.get("/rug-check")
async def rug_check_ep(symbol: str = Query(...), chain: str = ""):
    if not _rug: return {"error": "Rug detector unavailable"}
    try:
        return await _safe(_thread(_rug.check_token_rug_risk, symbol, chain), {}, timeout=15)
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  17. SCREENER
# ═══════════════════════════════════════════════════════════
@router.get("/screener")
async def screener_ep(query: str = "momentum"):
    if not _screener: return {"results": "Unavailable"}
    try:
        return {"results": await _safe(_thread(_screener.run_screener, query), "No results", timeout=20)}
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  18. FUTURES & OPTIONS
# ═══════════════════════════════════════════════════════════
@router.get("/futures")
async def futures_ep():
    hit = cached("futures", ttl=120)
    if hit is not None: return hit
    result = {"vix": {}}
    if _futures:
        try: result["vix"] = _futures.get_india_vix()
        except: pass
        try:
            if hasattr(_futures, 'get_futures_dashboard'):
                dash = _futures.get_futures_dashboard()
                if isinstance(dash, dict): result.update(dash)
        except: pass
    set_cache("futures", result)
    return result


# ═══════════════════════════════════════════════════════════
#  19. CANDLE PATTERNS
# ═══════════════════════════════════════════════════════════
@router.get("/candle-patterns")
async def candle_ep(symbol: str = "^NSEI"):
    if not _candle: return {"patterns": []}
    try:
        return await _safe(_thread(_candle.analyze_index, symbol), {}, timeout=15)
    except: return {"patterns": []}


# ═══════════════════════════════════════════════════════════
#  20. ULTRA AI
# ═══════════════════════════════════════════════════════════
@router.get("/ultra-predict")
async def ultra_ep(tokens: str = "BTC,ETH,SOL"):
    if not _ultra: return {"predictions": []}
    try:
        tl = [t.strip() for t in tokens.split(",")]
        r = await _safe(_thread(_ultra.batch_ultra_predict, tl), [], timeout=20)
        return {"predictions": r if isinstance(r, list) else []}
    except: return {"predictions": []}


# ═══════════════════════════════════════════════════════════
#  21. TOP MOVERS
# ═══════════════════════════════════════════════════════════
@router.get("/top-movers")
async def movers_ep(limit: int = 10):
    return _get_top_movers()


# ═══════════════════════════════════════════════════════════
#  22. RISK
# ═══════════════════════════════════════════════════════════
@router.get("/risk")
async def risk_ep(symbol: str = "BTC", capital: float = 10000):
    if not _risk: return {"error": "Risk module unavailable"}
    try:
        r = {"symbol": symbol, "capital": capital}
        if hasattr(_risk, 'calculate_position_size'):
            r["position_size"] = _risk.calculate_position_size(capital, 0.02, 0.05)
        return r
    except Exception as e: return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  23. INTELLIGENCE (Super Brain)
# ═══════════════════════════════════════════════════════════
@router.get("/intelligence")
async def intel_ep():
    hit = cached("intelligence", ttl=180)
    if hit is not None: return hit
    result = {"briefing": "", "regime": {}, "vix": {}}
    if _super_brain and hasattr(_super_brain, 'get_market_intelligence'):
        try:
            result["briefing"] = await _safe(_thread(_super_brain.get_market_intelligence), {}, timeout=20)
        except: pass
    result["regime"] = _get_market_regime()
    if _futures:
        try: result["vix"] = _futures.get_india_vix()
        except: pass
    set_cache("intelligence", result)
    return result


# ═══════════════════════════════════════════════════════════
#  DATA FETCHERS
# ═══════════════════════════════════════════════════════════

def _get_portfolio(user_id):
    if _payment and user_id:
        try: return _payment.get_portfolio(int(user_id))
        except: pass
    return {"positions": [], "total_invested_inr": 0, "total_current_inr": 0,
            "pnl_inr": 0, "pnl_pct": 0, "balance_inr": 0}

def _get_market_ticker():
    hit = cached("market_ticker", ttl=60)
    if hit is not None: return hit
    tickers = []
    if _coindcx:
        try:
            inr = _coindcx.get_inr_tickers()
            top = sorted(inr or [], key=lambda x: float(x.get("volume", 0)), reverse=True)[:8]
            for t in top:
                sym = t.get("market", "").replace("I-", "").replace("_INR", "")
                tickers.append({"symbol": sym, "name": sym,
                    "price": float(t.get("last_price", 0)),
                    "change_pct": float(t.get("change_24_hour", 0)),
                    "volume": float(t.get("volume", 0)), "currency": "INR"})
        except: pass
    try:
        import yfinance as yf
        for sym, name, cur in [("^NSEI", "NIFTY 50", "INR"), ("^BSESN", "SENSEX", "INR"),
                                ("BTC-USD", "Bitcoin", "USD"), ("ETH-USD", "Ethereum", "USD")]:
            try:
                info = yf.Ticker(sym).fast_info
                price = round(info.last_price, 2) if hasattr(info, "last_price") else 0
                prev = info.previous_close if hasattr(info, "previous_close") else price
                chg = round(((price / prev) - 1) * 100, 2) if prev else 0
                tickers.append({"symbol": sym, "name": name, "price": price,
                                "change_pct": chg, "currency": cur})
            except: pass
    except: pass
    set_cache("market_ticker", tickers)
    return tickers

def _get_quick_signals():
    hit = cached("quick_signals", ttl=60)
    if hit is not None: return hit
    signals = []
    if _coindcx:
        try:
            for s in (_coindcx.scan_best_signals(8) or []):
                signals.append({"symbol": s.get("symbol", ""), 
                    "signal": s.get("master_signal", s.get("signal", "HOLD")),
                    "confidence": s.get("confidence", s.get("master_score", 0)),
                    "price": s.get("price_inr", s.get("price", 0)),
                    "change_24h": s.get("change_24h", 0),
                    "source": "CoinDCX ML+TA"})
        except: pass
    set_cache("quick_signals", signals[:10])
    return signals[:10]

def _get_top_movers():
    hit = cached("top_movers", ttl=60)
    if hit is not None: return hit
    r = {"gainers": [], "losers": []}
    if _coindcx:
        try:
            d = _coindcx.get_top_gainers_losers(10)
            r = d if isinstance(d, dict) else r
        except: pass
    set_cache("top_movers", r)
    return r

def _get_market_regime():
    hit = cached("market_regime", ttl=180)
    if hit is not None: return hit
    r = {"regime": "UNKNOWN", "confidence": 0}
    if _regime:
        try:
            d = _regime.get_regime_quick()
            r = d if isinstance(d, dict) else r
        except: pass
    set_cache("market_regime", r)
    return r

def _get_trader_status(user_id):
    if _auto_trader and user_id:
        try: return _auto_trader.get_trader_status(int(user_id))
        except: pass
    return {"traders": [], "active_count": 0}

def _get_sentiment():
    hit = cached("sentiment", ttl=120)
    if hit is not None: return hit
    r = {}
    if _sentiment:
        try:
            r = _sentiment.calculate_fear_greed_index()
            if not isinstance(r, dict): r = {}
        except: pass
    set_cache("sentiment", r)
    return r

def _get_news_headlines(limit=8):
    hit = cached("news_hl", ttl=300)
    if hit is not None: return hit[:limit]
    articles = []
    if _news:
        try:
            raw = _news.get_breaking_news()
            if isinstance(raw, list):
                for item in raw[:30]:
                    if isinstance(item, dict): articles.append(item)
                    elif isinstance(item, str) and len(item) > 15:
                        articles.append({"title": item, "source": "News"})
            elif isinstance(raw, str):
                for line in raw.split("\n"):
                    line = line.strip()
                    if line and len(line) > 20 and not line.startswith("━"):
                        title = line.split("*")[1].strip() if line.count("*") >= 2 else line
                        if title: articles.append({"title": title, "source": "Market"})
        except: pass
    if not articles and _news:
        try:
            raw2 = _news.get_latest_news()
            if isinstance(raw2, str):
                for line in raw2.split("\n"):
                    line = line.strip()
                    if line and len(line) > 20 and not line.startswith("━"):
                        title = line.split("*")[1].strip() if line.count("*") >= 2 else line
                        if title: articles.append({"title": title, "source": "Market"})
        except: pass
    set_cache("news_hl", articles)
    return articles[:limit]

def _get_coindcx_markets():
    hit = cached("cdx_mkt", ttl=45)
    if hit is not None: return hit
    crypto = []
    if _coindcx:
        try:
            tickers = _coindcx.get_inr_tickers()
            for t in sorted(tickers or [], key=lambda x: float(x.get("volume", 0)), reverse=True)[:50]:
                sym = t.get("market", "").replace("I-", "").replace("_INR", "")
                crypto.append({"symbol": sym, "price": float(t.get("last_price", 0)),
                    "change_24h": float(t.get("change_24_hour", 0)),
                    "volume": float(t.get("volume", 0)),
                    "high": float(t.get("high", 0)), "low": float(t.get("low", 0)),
                    "currency": "INR"})
        except: pass
    set_cache("cdx_mkt", crypto)
    return crypto

def _get_trending_gems():
    hit = cached("trend_gems", ttl=60)
    if hit is not None: return hit
    gems = []
    if _crypto:
        try:
            for g in (_crypto.scan_all_gems(5, 20) or []):
                gems.append({"symbol": g.get("symbol", ""), "name": g.get("name", ""),
                    "price_usd": g.get("price_usd", 0),
                    "change_1h": g.get("change_1h", 0), "change_24h": g.get("change_24h", 0),
                    "market_cap": g.get("market_cap", 0), "volume": g.get("volume_24h", 0),
                    "score": g.get("score", 0), "chain": g.get("chain", ""),
                    "source": g.get("source", ""), "address": g.get("address", "")})
        except: pass
    set_cache("trend_gems", gems)
    return gems

def _get_indices():
    hit = cached("indices", ttl=120)
    if hit is not None: return hit
    indices = []
    try:
        import yfinance as yf
        for sym, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX"), ("^NSEBANK", "BANK NIFTY")]:
            try:
                info = yf.Ticker(sym).fast_info
                price = round(info.last_price, 2) if hasattr(info, "last_price") else 0
                prev = info.previous_close if hasattr(info, "previous_close") else price
                indices.append({"symbol": sym, "name": name, "price": price,
                    "change_pct": round(((price/prev)-1)*100, 2) if prev else 0,
                    "change": round(price-prev, 2) if prev else 0})
            except: pass
    except: pass
    set_cache("indices", indices)
    return indices

def _get_coindcx_signals(limit=8):
    hit = cached("cdx_sig", ttl=45)
    if hit is not None: return hit[:limit]
    signals = []
    if _coindcx:
        try:
            for s in (_coindcx.scan_best_signals(limit) or []):
                signals.append({"symbol": s.get("symbol",""), 
                    "signal": s.get("master_signal", s.get("signal","HOLD")),
                    "confidence": s.get("confidence", s.get("master_score", 0)),
                    "price": s.get("price_inr", s.get("price", 0)),
                    "change_24h": s.get("change_24h", 0),
                    "risk": s.get("risk", ""),
                    "ml_prob": s.get("ml_buy_prob", 0),
                    "rsi": s.get("rsi", 0),
                    "source": "CoinDCX ML+TA", "market": "crypto"})
        except: pass
    set_cache("cdx_sig", signals)
    return signals[:limit]

def _get_ta_signals():
    hit = cached("ta_sig", ttl=60)
    if hit is not None: return hit
    signals = []
    if _buy_sell:
        try:
            for s in (_buy_sell.scan_crypto_signals(10) or []):
                signals.append({"symbol": s.symbol, "price": getattr(s, "price", 0),
                    "signal": s.signal_type.value if hasattr(s.signal_type, "value") else str(s.signal_type),
                    "confidence": s.confidence,
                    "source": "TA Engine", "market": "crypto"})
        except: pass
    set_cache("ta_sig", signals)
    return signals

def _get_nifty_signals():
    hit = cached("nifty_sig", ttl=120)
    if hit is not None: return hit
    signals = []
    if _buy_sell:
        try:
            for s in (_buy_sell.scan_nifty_signals(8) or []):
                signals.append({"symbol": s.symbol, "price": getattr(s, "price", 0),
                    "signal": s.signal_type.value if hasattr(s.signal_type, "value") else str(s.signal_type),
                    "confidence": s.confidence, "source": "NIFTY TA", "market": "stock"})
        except: pass
    set_cache("nifty_sig", signals)
    return signals

def _get_coindcx_dips():
    hit = cached("cdx_dips", ttl=60)
    if hit is not None: return hit
    dips = []
    if _coindcx:
        try:
            for t in (_coindcx.get_inr_tickers() or []):
                chg = float(t.get("change_24_hour", 0))
                if chg <= -5:
                    sym = t.get("market", "").replace("I-", "").replace("_INR", "")
                    dips.append({"symbol": sym, "price_usd": float(t.get("last_price",0)),
                        "change_24h": chg, "volume": float(t.get("volume",0)),
                        "source": "CoinDCX Dip", "chain": "INR",
                        "score": min(abs(chg)*2, 100)})
            dips.sort(key=lambda x: x["change_24h"])
        except: pass
    set_cache("cdx_dips", dips[:20])
    return dips[:20]

def _analyze_coindcx(symbol):
    try:
        if hasattr(_coindcx, 'get_detailed_analysis'):
            return _coindcx.get_detailed_analysis(symbol)
        sigs = _coindcx.scan_best_signals(30)
        for s in (sigs or []):
            if symbol.upper() in s.get("symbol","").upper():
                return s
    except: pass
    return {}

def _analyze_rug(symbol):
    try: return _rug.check_token_rug_risk(symbol, "")
    except: return {}

def _analyze_ultra(symbol):
    try:
        r = _ultra.batch_ultra_predict([symbol])
        return r[0] if r and isinstance(r, list) else {}
    except: return {}

def _analyze_deep(symbol):
    try: return _market_brain.analyze_crypto_token_deep(symbol)
    except: return {}


# ═══════════════════════════════════════════════════════════
#  🔮 PHANTOM WALLET & SOLANA — v4.1
# ═══════════════════════════════════════════════════════════

@router.get("/phantom/connect-link")
async def phantom_connect_link(user_id: str = Query(...)):
    """Generate Phantom wallet connect instructions."""
    try:
        if _phantom and hasattr(_phantom, "generate_phantom_connect_link"):
            link = _phantom.generate_phantom_connect_link(user_id)
            return {"status": "ok", "data": link}
        if _solana and hasattr(_solana, "generate_phantom_connect_deeplink"):
            link = _solana.generate_phantom_connect_deeplink(user_id)
            return {"status": "ok", "data": {"connect_link": link}}
        return {"status": "ok", "data": {"instructions": "Send your Phantom wallet address to connect."}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/phantom/connect")
async def phantom_connect(request: Request):
    """Connect a Phantom wallet to user account."""
    body = await request.json()
    user_id = str(body.get("user_id", ""))
    wallet_address = body.get("wallet_address", "")
    try:
        if _phantom and hasattr(_phantom, "connect_wallet"):
            result = _phantom.connect_wallet(user_id, wallet_address)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {"connected": True, "address": wallet_address}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/phantom/disconnect")
async def phantom_disconnect(request: Request):
    """Disconnect Phantom wallet."""
    body = await request.json()
    user_id = str(body.get("user_id", ""))
    try:
        if _phantom and hasattr(_phantom, "disconnect_wallet"):
            _phantom.disconnect_wallet(user_id)
        return {"status": "ok", "data": {"disconnected": True}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/phantom/scan")
async def phantom_scan(user_id: str = Query(...)):
    """Full wallet scan — tokens, prices, ML predictions, total value."""
    try:
        if _phantom and hasattr(_phantom, "scan_wallet"):
            result = await _run(_phantom.scan_wallet, user_id)
            return {"status": "ok", "data": result}
        if _solana and hasattr(_solana, "get_wallet_summary"):
            # Try direct solana scan
            wallet = _phantom.get_wallet(user_id) if _phantom else None
            addr = wallet.get("address", "") if wallet else ""
            if addr:
                result = await _run(_solana.get_wallet_summary, addr)
                return {"status": "ok", "data": result}
        return {"status": "ok", "data": {"tokens": [], "total_value": 0}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/phantom/dashboard")
async def phantom_dashboard(user_id: str = Query(...)):
    """Phantom wallet dashboard with all details."""
    try:
        if _phantom and hasattr(_phantom, "get_wallet_dashboard"):
            result = _phantom.get_wallet_dashboard(user_id)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/solana/balance")
async def solana_balance(wallet: str = Query(...)):
    """Get SOL + all SPL token balances."""
    try:
        if _solana:
            sol = await _run(_solana.get_sol_balance, wallet) if hasattr(_solana, "get_sol_balance") else 0
            tokens = await _run(_solana.get_all_token_balances, wallet) if hasattr(_solana, "get_all_token_balances") else []
            enriched = await _run(_solana.resolve_token_metadata, tokens) if hasattr(_solana, "resolve_token_metadata") and tokens else tokens
            return {"status": "ok", "data": {"sol_balance": sol, "tokens": enriched}}
        return {"status": "ok", "data": {"sol_balance": 0, "tokens": []}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/solana/transactions")
async def solana_transactions(wallet: str = Query(...), limit: int = Query(10)):
    """Recent Solana transactions."""
    try:
        if _solana and hasattr(_solana, "get_recent_transactions"):
            txns = await _run(_solana.get_recent_transactions, wallet, limit)
            return {"status": "ok", "data": txns}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/solana/transfer-link")
async def solana_transfer_link(request: Request):
    """Generate Phantom transfer deep link."""
    body = await request.json()
    try:
        if _solana and hasattr(_solana, "generate_phantom_transfer_link"):
            link = _solana.generate_phantom_transfer_link(
                body.get("to_address", ""),
                body.get("amount", 0),
                body.get("token_mint", "")
            )
            return {"status": "ok", "data": link}
        return {"status": "ok", "data": {"link": ""}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/solana/airdrops")
async def solana_airdrops(wallet: str = Query(...)):
    """Scan for claimable airdrops."""
    try:
        if _solana and hasattr(_solana, "scan_for_claimable_airdrops"):
            airdrops = await _run(_solana.scan_for_claimable_airdrops, wallet)
            return {"status": "ok", "data": airdrops}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  🐋 WHALE ALERTS
# ═══════════════════════════════════════════════════════════

@router.get("/whale-alert")
async def whale_alert(token: str = Query(...), chain: str = Query("solana")):
    """Whale activity for a specific token."""
    try:
        if _whale and hasattr(_whale, "detect_whale_activity_from_dex"):
            result = await _run(_whale.detect_whale_activity_from_dex, token, chain)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/whale-scan")
async def whale_scan(limit: int = Query(10)):
    """Scan trending tokens for whale activity."""
    try:
        if _whale and hasattr(_whale, "scan_whale_activity_trending"):
            result = await _run(_whale.scan_whale_activity_trending, limit)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/whale-onchain")
async def whale_onchain(mint: str = Query(...), symbol: str = Query("")):
    """On-chain whale transactions (Helius/Solscan)."""
    try:
        if _whale and hasattr(_whale, "check_helius_transactions"):
            result = await _run(_whale.check_helius_transactions, mint)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  📊 OPTIONS CHAIN & NIFTY
# ═══════════════════════════════════════════════════════════

@router.get("/options/chain")
async def option_chain(symbol: str = Query("NIFTY"), expiry: str = Query("")):
    """Full option chain with Greeks."""
    try:
        if _options and hasattr(_options, "generate_option_chain"):
            chain = await _run(_options.generate_option_chain, symbol, expiry)
            return {"status": "ok", "data": chain}
        return {"status": "ok", "data": {"calls": [], "puts": [], "spot": 0}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options/strategy")
async def option_strategy(symbol: str = Query("NIFTY"), outlook: str = Query("bullish"), budget: float = Query(5000)):
    """AI option strategy recommendation."""
    try:
        if _options and hasattr(_options, "recommend_strategy"):
            strategy = await _run(_options.recommend_strategy, symbol, outlook, budget)
            return {"status": "ok", "data": strategy}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options/budget-picks")
async def budget_picks(index: str = Query("NIFTY"), direction: str = Query("both"), budget: float = Query(5)):
    """Budget option picks (₹4-5 premium)."""
    try:
        if _nifty_hunter and hasattr(_nifty_hunter, "find_budget_options"):
            picks = await _run(_nifty_hunter.find_budget_options, index, direction, budget)
            return {"status": "ok", "data": picks}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options/morning-picks")
async def morning_picks():
    """Auto 9AM option picks."""
    try:
        if _nifty_hunter and hasattr(_nifty_hunter, "generate_morning_picks"):
            picks = await _run(_nifty_hunter.generate_morning_picks)
            return {"status": "ok", "data": picks}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options/positions")
async def options_positions(user_id: str = Query(...)):
    """Get user's option positions."""
    try:
        if _nifty_hunter and hasattr(_nifty_hunter, "get_my_positions_enhanced"):
            positions = _nifty_hunter.get_my_positions_enhanced(user_id)
            return {"status": "ok", "data": positions}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options/iv")
async def option_iv(symbol: str = Query("NIFTY")):
    """IV Rank & Percentile."""
    try:
        if _options and hasattr(_options, "calculate_iv_rank_percentile"):
            iv_data = await _run(_options.calculate_iv_rank_percentile, symbol)
            return {"status": "ok", "data": iv_data}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  🇮🇳 NIFTY SUPER BRAIN
# ═══════════════════════════════════════════════════════════

@router.get("/nifty/dashboard")
async def nifty_dashboard():
    """Complete NIFTY dashboard — VIX, PCR, FII/DII, Pivots, Sectors, OI."""
    c = _cached("nifty_dash", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_complete_dashboard"):
            dash = await _run(_nifty_brain.get_complete_dashboard)
            r = {"status": "ok", "data": dash}; _set_cache("nifty_dash", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/fii-dii")
async def nifty_fii_dii():
    """FII/DII daily flow data."""
    c = _cached("fii_dii", 60)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_fii_dii_data"):
            data = await _run(_nifty_brain.get_fii_dii_data)
            r = {"status": "ok", "data": data}; _set_cache("fii_dii", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/vix")
async def nifty_vix():
    """India VIX with trend + percentile."""
    c = _cached("vix", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_india_vix"):
            vix = await _run(_nifty_brain.get_india_vix)
            r = {"status": "ok", "data": vix}; _set_cache("vix", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/pcr")
async def nifty_pcr(index: str = Query("NIFTY")):
    """Put-Call Ratio dashboard."""
    c = _cached(f"pcr_{index}", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_pcr_data"):
            pcr = await _run(_nifty_brain.get_pcr_data, index)
            r = {"status": "ok", "data": pcr}; _set_cache(f"pcr_{index}", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/pivots")
async def nifty_pivots(index: str = Query("NIFTY")):
    """Pivot levels — Classic, Fibonacci, Camarilla, CPR."""
    c = _cached(f"pivots_{index}", 60)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "calculate_pivot_levels"):
            pivots = await _run(_nifty_brain.calculate_pivot_levels, index)
            r = {"status": "ok", "data": pivots}; _set_cache(f"pivots_{index}", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/gift")
async def nifty_gift():
    """GIFT Nifty pre-market gap prediction."""
    c = _cached("gift", 60)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_gift_nifty"):
            gift = await _run(_nifty_brain.get_gift_nifty)
            r = {"status": "ok", "data": gift}; _set_cache("gift", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/sectors")
async def nifty_sectors():
    """11-sector rotation heatmap."""
    c = _cached("sectors", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_sector_heatmap"):
            sectors = await _run(_nifty_brain.get_sector_heatmap)
            r = {"status": "ok", "data": sectors}; _set_cache("sectors", r); return r
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/oi")
async def nifty_oi(index: str = Query("NIFTY")):
    """OI Long/Short Buildup analysis."""
    c = _cached(f"oi_{index}", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_oi_buildup"):
            oi = await _run(_nifty_brain.get_oi_buildup, index)
            r = {"status": "ok", "data": oi}; _set_cache(f"oi_{index}", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  🇮🇳 INDIAN STOCK SUPER ENGINE
# ═══════════════════════════════════════════════════════════

@router.get("/india/market-status")
async def india_market_status():
    """Market status — Pre/Open/Closed/Holiday."""
    try:
        if _india_stock and hasattr(_india_stock, "get_market_status"):
            status = _india_stock.get_market_status()
            return {"status": "ok", "data": status}
        return {"status": "ok", "data": {"status": "unknown"}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/super-analysis")
async def india_super_analysis(query: str = Query("NIFTY"), budget: float = Query(2000)):
    """Full Indian stock ML analysis (250+ features)."""
    try:
        if _india_stock and hasattr(_india_stock, "indian_stock_super_analysis"):
            result = await _run(_india_stock.indian_stock_super_analysis, query, budget)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/holidays")
async def india_holidays():
    """NSE holiday calendar 2025-2026."""
    try:
        if _india_stock and hasattr(_india_stock, "get_upcoming_holidays"):
            h = _india_stock.get_upcoming_holidays()
            return {"status": "ok", "data": h}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/combined-dashboard")
async def india_combined_dashboard(index: str = Query("NIFTY")):
    """🚀 SUPER FAST — Returns ALL Indian stock data in ONE call."""
    c = _cached(f"india_combined_{index}", 25)
    if c: return c
    try:
        tasks = {
            "dashboard": _safe(_run(_nifty_brain.get_complete_dashboard), {}) if _nifty_brain and hasattr(_nifty_brain, "get_complete_dashboard") else asyncio.coroutine(lambda: {})(),
            "fii_dii": _safe(_run(_nifty_brain.get_fii_dii_data), {}) if _nifty_brain and hasattr(_nifty_brain, "get_fii_dii_data") else asyncio.coroutine(lambda: {})(),
            "vix": _safe(_run(_nifty_brain.get_india_vix), {}) if _nifty_brain and hasattr(_nifty_brain, "get_india_vix") else asyncio.coroutine(lambda: {})(),
            "pcr": _safe(_run(_nifty_brain.get_pcr_data, index), {}) if _nifty_brain and hasattr(_nifty_brain, "get_pcr_data") else asyncio.coroutine(lambda: {})(),
            "pivots": _safe(_run(_nifty_brain.calculate_pivot_levels, index), {}) if _nifty_brain and hasattr(_nifty_brain, "calculate_pivot_levels") else asyncio.coroutine(lambda: {})(),
            "gift": _safe(_run(_nifty_brain.get_gift_nifty), {}) if _nifty_brain and hasattr(_nifty_brain, "get_gift_nifty") else asyncio.coroutine(lambda: {})(),
            "sectors": _safe(_run(_nifty_brain.get_sector_heatmap), []) if _nifty_brain and hasattr(_nifty_brain, "get_sector_heatmap") else asyncio.coroutine(lambda: [])(),
            "oi": _safe(_run(_nifty_brain.get_oi_buildup, index), {}) if _nifty_brain and hasattr(_nifty_brain, "get_oi_buildup") else asyncio.coroutine(lambda: {})(),
        }
        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values())
        data = dict(zip(keys, results))
        # Also add market status (sync, no thread needed)
        if _india_stock and hasattr(_india_stock, "get_market_status"):
            data["market_status"] = _india_stock.get_market_status()
        # Add snapshot
        if _live_index and hasattr(_live_index, "get_full_market_snapshot"):
            snap = await _safe(_run(_live_index.get_full_market_snapshot), {})
            data["snapshot"] = snap
        elif _live_index and hasattr(_live_index, "get_market_snapshot"):
            snap = await _safe(_run(_live_index.get_market_snapshot), {})
            data["snapshot"] = snap
        r = {"status": "ok", "data": data}
        _set_cache(f"india_combined_{index}", r)
        return r
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  📈 PORTFOLIO ANALYTICS PRO
# ═══════════════════════════════════════════════════════════

@router.get("/portfolio/combined")
async def portfolio_combined(user_id: str = Query(...)):
    """Combined crypto + stock portfolio."""
    try:
        if _portfolio and hasattr(_portfolio, "format_combined_portfolio"):
            result = _portfolio.format_combined_portfolio(user_id)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/portfolio/pnl")
async def portfolio_pnl(user_id: str = Query(...)):
    """Live P&L breakdown."""
    try:
        if _portfolio:
            crypto_pnl = _portfolio.calculate_portfolio_pnl(user_id) if hasattr(_portfolio, "calculate_portfolio_pnl") else {}
            stock_pnl = _portfolio.calculate_stock_portfolio_pnl(user_id) if hasattr(_portfolio, "calculate_stock_portfolio_pnl") else {}
            return {"status": "ok", "data": {"crypto": crypto_pnl, "stocks": stock_pnl}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/portfolio/tax")
async def portfolio_tax(user_id: str = Query(...)):
    """Indian tax calculator (30% crypto + STCG/LTCG stocks)."""
    try:
        if _portfolio and hasattr(_portfolio, "calculate_tax"):
            tax = _portfolio.calculate_tax(user_id)
            return {"status": "ok", "data": tax}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/portfolio/add")
async def portfolio_add(request: Request):
    """Add holding to portfolio."""
    body = await request.json()
    try:
        user_id = str(body.get("user_id", ""))
        symbol = body.get("symbol", "")
        qty = body.get("quantity", 0)
        price = body.get("price", 0)
        ptype = body.get("type", "crypto")
        if _portfolio:
            if ptype == "stock" and hasattr(_portfolio, "add_stock_holding"):
                _portfolio.add_stock_holding(user_id, symbol, qty, price)
            elif hasattr(_portfolio, "add_holding"):
                _portfolio.add_holding(user_id, symbol, qty, price)
        return {"status": "ok", "data": {"added": True}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/portfolio/sell")
async def portfolio_sell(request: Request):
    """Sell holding from portfolio."""
    body = await request.json()
    try:
        user_id = str(body.get("user_id", ""))
        symbol = body.get("symbol", "")
        qty = body.get("quantity", 0)
        price = body.get("price", 0)
        ptype = body.get("type", "crypto")
        if _portfolio:
            if ptype == "stock" and hasattr(_portfolio, "sell_stock_holding"):
                _portfolio.sell_stock_holding(user_id, symbol, qty, price)
            elif hasattr(_portfolio, "sell_holding"):
                _portfolio.sell_holding(user_id, symbol, qty, price)
        return {"status": "ok", "data": {"sold": True}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/portfolio/alert")
async def portfolio_set_alert(request: Request):
    """Set price alert."""
    body = await request.json()
    try:
        user_id = str(body.get("user_id", ""))
        symbol = body.get("symbol", "")
        target = body.get("target_price", 0)
        direction = body.get("direction", "above")
        if _portfolio and hasattr(_portfolio, "add_price_alert"):
            _portfolio.add_price_alert(user_id, symbol, target, direction)
        return {"status": "ok", "data": {"alert_set": True}}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  🧪 BACKTEST BUILDER
# ═══════════════════════════════════════════════════════════

@router.post("/backtest")
async def run_backtest(request: Request):
    """Run backtest from natural language strategy description."""
    body = await request.json()
    strategy_text = body.get("strategy", "")
    try:
        if _backtester and hasattr(_backtester, "handle_backtest_command"):
            result = await _run(_backtester.handle_backtest_command, strategy_text)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {"error": "Backtester not available"}}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  🎙️ VOICE AI
# ═══════════════════════════════════════════════════════════

@router.post("/voice/generate")
async def voice_generate(request: Request):
    """Text-to-speech (OpenAI HD → Deepgram → Gemini → Edge TTS)."""
    body = await request.json()
    text = body.get("text", "")
    lang = body.get("language", "en")
    try:
        if _voice and hasattr(_voice, "generate_voice"):
            audio_path = await _run(_voice.generate_voice, text, lang)
            return {"status": "ok", "data": {"audio_path": audio_path}}
        return {"status": "ok", "data": {"error": "Voice engine not available"}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/voice/transcribe")
async def voice_transcribe(request: Request):
    """Speech-to-text (Groq Whisper → OpenAI Whisper)."""
    body = await request.json()
    audio_url = body.get("audio_url", "")
    try:
        if _voice and hasattr(_voice, "transcribe_voice_message"):
            text = await _run(_voice.transcribe_voice_message, audio_url)
            return {"status": "ok", "data": {"text": text}}
        return {"status": "ok", "data": {"text": ""}}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  📋 COPY TRADING & SOCIAL
# ═══════════════════════════════════════════════════════════

@router.get("/copy-trading/signals")
async def copy_trading_signals():
    """Get bot's live trades for copy trading."""
    try:
        if _super_trader and hasattr(_super_trader, "get_active_signals"):
            signals = _super_trader.get_active_signals()
            return {"status": "ok", "data": signals}
        if _auto_trader and hasattr(_auto_trader, "get_active_positions"):
            pos = _auto_trader.get_active_positions()
            return {"status": "ok", "data": pos}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/copy-trading/leaderboard")
async def copy_trading_leaderboard():
    """Top performing traders / strategies."""
    c = cached("leaderboard", 300)
    if c: return {"status": "ok", "data": c}
    try:
        if _auto_trader and hasattr(_auto_trader, "get_leaderboard"):
            lb = _auto_trader.get_leaderboard()
            set_cache("leaderboard", lb)
            return {"status": "ok", "data": lb}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/social/feed")
async def social_feed(limit: int = Query(20)):
    """Anonymized social trading feed."""
    try:
        if _trade_tracker and hasattr(_trade_tracker, "get_recent_trades"):
            trades = _trade_tracker.get_recent_trades(limit)
            # Anonymize
            for t in (trades or []):
                if "user" in t: t["user"] = t["user"][:3] + "***"
                if "user_id" in t: del t["user_id"]
            return {"status": "ok", "data": trades}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nifty/super-analysis")
async def nifty_super_analysis(index: str = Query("NIFTY")):
    """Full NIFTY super brain analysis."""
    c = _cached(f"super_analysis_{index}", 30)
    if c: return c
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_super_brain_analysis"):
            result = await _run(_nifty_brain.get_super_brain_analysis, index)
            r = {"status": "ok", "data": result}; _set_cache(f"super_analysis_{index}", r); return r
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  NSE LIVE OPTION CHAIN (Real NSE/BSE data)
# ═══════════════════════════════════════════════════════════
@router.get("/nse/live-chain")
async def nse_live_chain(symbol: str = Query("NIFTY")):
    """Real-time NSE option chain with live LTP, OI, Volume, IV, Greeks."""
    try:
        if _nse_live and hasattr(_nse_live, "fetch_live_option_chain"):
            chain = await _run(_nse_live.fetch_live_option_chain, symbol)
            if hasattr(chain, "__dict__"):
                chain = chain.__dict__
                for k in ["calls", "puts"]:
                    if k in chain and chain[k]:
                        chain[k] = [s.__dict__ if hasattr(s, "__dict__") else s for s in chain[k]]
            return {"status": "ok", "data": chain}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nse/live-spot")
async def nse_live_spot(symbol: str = Query("NIFTY")):
    """Real-time spot price from NSE."""
    try:
        if _nse_live and hasattr(_nse_live, "get_live_spot"):
            spot = await _run(_nse_live.get_live_spot, symbol)
            return {"status": "ok", "data": spot}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/nse/atm-otm")
async def nse_atm_otm(symbol: str = Query("NIFTY"), budget: float = Query(2000), direction: str = Query("auto")):
    """ATM vs OTM analysis with real prices + scoring."""
    try:
        if _nse_live and hasattr(_nse_live, "get_atm_otm_analysis"):
            result = await _run(_nse_live.get_atm_otm_analysis, symbol, budget, direction)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  OI TRAP BRAIN (Trap Detection + Budget Plays)
# ═══════════════════════════════════════════════════════════
@router.get("/oi/super-signal")
async def oi_super_signal(symbol: str = Query("NIFTY")):
    """Ultimate OI signal: trap detection + budget plays + direction."""
    try:
        if _oi_trap and hasattr(_oi_trap, "get_options_super_signal"):
            result = await _run(_oi_trap.get_options_super_signal, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/oi/traps")
async def oi_traps(symbol: str = Query("NIFTY")):
    """Bull/Bear/Range/MaxPain trap detection."""
    try:
        if _oi_trap and hasattr(_oi_trap, "fetch_option_chain"):
            chain = await _run(_oi_trap.fetch_option_chain, symbol)
            if chain and _oi_trap and hasattr(_oi_trap, "detect_traps"):
                traps = _oi_trap.detect_traps(chain)
                return {"status": "ok", "data": traps}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/oi/budget-plays")
async def oi_budget_plays(symbol: str = Query("NIFTY"), min_price: float = Query(2), max_price: float = Query(30)):
    """Budget option plays ₹2-₹30 with 10x-150x potential."""
    try:
        if _oi_trap and hasattr(_oi_trap, "fetch_option_chain"):
            chain = await _run(_oi_trap.fetch_option_chain, symbol)
            if chain and hasattr(_oi_trap, "find_budget_plays"):
                plays = _oi_trap.find_budget_plays(chain, min_price, max_price)
                return {"status": "ok", "data": plays}
        return {"status": "ok", "data": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/oi/change")
async def oi_change_analysis(symbol: str = Query("NIFTY")):
    """OI change analysis over time snapshots."""
    try:
        if _oi_trap and hasattr(_oi_trap, "get_oi_change"):
            result = await _run(_oi_trap.get_oi_change, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  OTM/ATM ENGINE (Transition Tracking + Momentum)
# ═══════════════════════════════════════════════════════════
@router.get("/otm/analysis")
async def otm_atm_analysis(index: str = Query("NIFTY"), num_strikes: int = Query(8)):
    """Complete OTM→ATM transition analysis with probabilities."""
    try:
        if _otm_atm and hasattr(_otm_atm, "full_otm_atm_analysis"):
            report = await _run(_otm_atm.full_otm_atm_analysis, index, num_strikes)
            if hasattr(report, "__dict__"):
                report = report.__dict__
                for k in ["calls", "puts"]:
                    if k in report and report[k]:
                        report[k] = [s.__dict__ if hasattr(s, "__dict__") else s for s in report[k]]
                for k in ["best_call", "best_put"]:
                    if k in report and report[k] and hasattr(report[k], "__dict__"):
                        report[k] = report[k].__dict__
            return {"status": "ok", "data": report}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/otm/momentum")
async def rapid_momentum(index: str = Query("NIFTY")):
    """Ultra-fast 2-min momentum signal for scalping."""
    try:
        if _otm_atm and hasattr(_otm_atm, "rapid_momentum_signal"):
            result = await _run(_otm_atm.rapid_momentum_signal, index)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  POWER PREDICTOR (10-Signal Ultra Prediction)
# ═══════════════════════════════════════════════════════════
@router.get("/india/power-predict")
async def power_predict(index: str = Query("NIFTY")):
    """10-signal weighted prediction: ML + TA + Candles + FII + VIX + PCR + Pivots + GIFT + News + Correlation."""
    try:
        if _power_pred and hasattr(_power_pred, "power_predict"):
            result = await _run(_power_pred.power_predict, index)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  LIVE INDEX ENGINE (2-Min Candles + Investment Calc)
# ═══════════════════════════════════════════════════════════
@router.get("/india/live-price")
async def india_live_price(symbol: str = Query("^NSEI")):
    """Real-time index price with OHLCV."""
    try:
        if _live_index and hasattr(_live_index, "get_live_price"):
            result = await _run(_live_index.get_live_price, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/2min-signal")
async def india_2min_signal(symbol: str = Query("^NSEI"), name: str = Query("NIFTY")):
    """2-minute candle scalping signal: RSI(7), EMA(9/21), momentum, volume surge."""
    try:
        if _live_index and hasattr(_live_index, "analyze_2min_candle"):
            result = await _run(_live_index.analyze_2min_candle, symbol, name)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/market-snapshot")
async def india_market_snapshot():
    """Combined NIFTY + SENSEX live snapshot."""
    try:
        if _live_index and hasattr(_live_index, "get_full_market_snapshot"):
            result = await _run(_live_index.get_full_market_snapshot)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/india/investment-calc")
async def india_investment_calc(symbol: str = Query("^NSEI"), name: str = Query("NIFTY"), investment: float = Query(2000)):
    """Calculate best option plays for given investment amount."""
    try:
        if _live_index and hasattr(_live_index, "generate_index_option_chain"):
            chain = await _run(_live_index.generate_index_option_chain, symbol, name)
            if chain and hasattr(_live_index, "calculate_investment_options"):
                result = _live_index.calculate_investment_options(chain, investment)
                return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  CANDLE ANALYZER (43 Patterns + 50+ Indicators)
# ═══════════════════════════════════════════════════════════
@router.get("/candles/patterns")
async def candle_patterns(symbol: str = Query("^NSEI"), name: str = Query("NIFTY")):
    """Multi-timeframe candlestick pattern scan (43 patterns × 4 timeframes)."""
    try:
        if _candle and hasattr(_candle, "multi_timeframe_pattern_scan"):
            result = await _run(_candle.multi_timeframe_pattern_scan, symbol)
            # Convert dataclass patterns
            if result and isinstance(result, dict):
                for tf, patterns in result.items():
                    if isinstance(patterns, list):
                        result[tf] = [p.__dict__ if hasattr(p, "__dict__") else p for p in patterns]
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/candles/analysis")
async def candle_analysis(symbol: str = Query("^NSEI"), name: str = Query("NIFTY")):
    """Complete AI analysis: candles + technicals + 12-factor scoring."""
    try:
        if _candle and hasattr(_candle, "analyze_index"):
            result = await _run(_candle.analyze_index, symbol, name)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/candles/indicators")
async def candle_indicators(symbol: str = Query("^NSEI"), period: str = Query("60d"), interval: str = Query("1d")):
    """50+ technical indicators: RSI, MACD, BB, Keltner, ADX, Aroon, Stoch, CCI, Williams, MFI, OBV, VWAP, Ichimoku, Fibonacci, Supertrend."""
    try:
        if _candle and hasattr(_candle, "fetch_index_candles") and hasattr(_candle, "calculate_technical_indicators"):
            df = await _run(_candle.fetch_index_candles, symbol, period, interval)
            if df is not None and len(df) > 0:
                indicators = _candle.calculate_technical_indicators(df)
                # Convert last row to serializable dict
                last = {}
                for col in indicators.columns:
                    val = indicators[col].iloc[-1] if len(indicators) > 0 else None
                    if val is not None:
                        try:
                            import math
                            if math.isnan(float(val)) or math.isinf(float(val)):
                                last[col] = None
                            else:
                                last[col] = round(float(val), 4)
                        except (ValueError, TypeError):
                            last[col] = str(val)
                # Also include recent history for charts
                history = []
                for _, row in indicators.tail(60).iterrows():
                    try:
                        d = {"date": str(row.name.date()) if hasattr(row.name, "date") else str(row.name)}
                        for c in ["Close", "RSI", "MACD", "BBU", "BBL", "BBM", "ADX", "SuperTrend", "OBV", "Volume"]:
                            if c in row.index:
                                v = row[c]
                                try:
                                    import math
                                    if not math.isnan(float(v)):
                                        d[c.lower()] = round(float(v), 4)
                                except:
                                    pass
                        history.append(d)
                    except:
                        pass
                return {"status": "ok", "data": {"current": last, "history": history}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  ML PREDICTOR (Deep Learning + Ensemble + SHAP)
# ═══════════════════════════════════════════════════════════
@router.get("/ml/predict")
async def ml_predict(symbol: str = Query("^NSEI"), name: str = Query("NIFTY")):
    """ML prediction: 6 models + LSTM + meta-learner with SHAP explainability."""
    try:
        if _ml_pred and hasattr(_ml_pred, "predict_with_regime"):
            result = await _run(_ml_pred.predict_with_regime, symbol, name)
            return {"status": "ok", "data": result}
        elif _ml_pred and hasattr(_ml_pred, "predict_index_direction"):
            result = await _run(_ml_pred.predict_index_direction, symbol, name)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  MARKET REGIME (8-Regime Adaptive Detection)
# ═══════════════════════════════════════════════════════════
@router.get("/india/regime")
async def market_regime(symbol: str = Query("^NSEI")):
    """8-regime adaptive detection: STRONG_BULL to STRONG_BEAR with trading parameters."""
    try:
        if _regime and hasattr(_regime, "detect_market_regime"):
            result = await _run(_regime.detect_market_regime, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
                if "regime" in result and hasattr(result["regime"], "value"):
                    result["regime"] = result["regime"].value
                if "trading_params" in result and hasattr(result["trading_params"], "__dict__"):
                    result["trading_params"] = result["trading_params"].__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  GLOBAL CANDLE ENGINE (World Impact on India)
# ═══════════════════════════════════════════════════════════
@router.get("/global/analysis")
async def global_analysis():
    """All 22 world markets + 5 commodities → India impact prediction."""
    try:
        if _global_candle and hasattr(_global_candle, "analyze_all_global_markets"):
            result = await _run(_global_candle.analyze_all_global_markets)
            if hasattr(result, "__dict__"):
                result = result.__dict__
                if "signals" in result and isinstance(result["signals"], list):
                    result["signals"] = [s.__dict__ if hasattr(s, "__dict__") else s for s in result["signals"]]
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/global/india-impact")
async def global_india_impact():
    """India market prediction scored from US, VIX, Asia, Crude, USD/INR, Gold."""
    try:
        if _global_candle and hasattr(_global_candle, "get_india_prediction_from_global"):
            result = await _run(_global_candle.get_india_prediction_from_global, "en")
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  JARVIS AI SUPER BRAIN VERDICT (THE ULTIMATE)
# ═══════════════════════════════════════════════════════════
@router.get("/ai/market-verdict")
async def ai_market_verdict():
    """JARVIS feeds ALL dashboard data to Groq AI → expert verdict with exact strikes."""
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_ai_market_verdict"):
            result = await _run(_nifty_brain.get_ai_market_verdict)
            return {"status": "ok", "data": {"verdict": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/ai/super-brain")
async def ai_super_brain():
    """Dashboard + AI Verdict combined — most comprehensive analysis."""
    try:
        idx = request.query_params.get("index", "NIFTY") if hasattr(request, 'query_params') else "NIFTY"
        if _nifty_brain and hasattr(_nifty_brain, "get_super_brain_analysis"):
            result = await _run(_nifty_brain.get_super_brain_analysis, idx)
            return {"status": "ok", "data": {"analysis": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/ai/complete-dashboard")
async def ai_complete_dashboard():
    """Full NIFTY dashboard text with all data (FII/DII, VIX, PCR, Pivots, OI, Gift, Sectors)."""
    try:
        if _nifty_brain and hasattr(_nifty_brain, "get_complete_dashboard"):
            result = await _run(_nifty_brain.get_complete_dashboard)
            return {"status": "ok", "data": {"dashboard": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  INTRADAY SCANNER (Breakout + Volume + Momentum)
# ═══════════════════════════════════════════════════════════
@router.get("/intraday/scan")
async def intraday_scan():
    """Full intraday scan across 50 NIFTY stocks — breakouts, volume, momentum."""
    try:
        if _intraday and hasattr(_intraday, "run_intraday_scan"):
            result = await _run(_intraday.run_intraday_scan)
            return {"status": "ok", "data": {"scan": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intraday/breakouts")
async def intraday_breakouts():
    """Intraday breakout stocks from NIFTY 50."""
    try:
        if _intraday and hasattr(_intraday, "scan_breakouts"):
            result = await _run(_intraday.scan_breakouts)
            return {"status": "ok", "data": {"breakouts": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intraday/volume-spikes")
async def intraday_volume_spikes():
    """Stocks with unusual volume surge today."""
    try:
        if _intraday and hasattr(_intraday, "scan_volume_spikes"):
            result = await _run(_intraday.scan_volume_spikes)
            return {"status": "ok", "data": {"volume_spikes": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intraday/momentum")
async def intraday_momentum():
    """Top momentum stocks from NIFTY 50."""
    try:
        if _intraday and hasattr(_intraday, "scan_momentum"):
            result = await _run(_intraday.scan_momentum)
            return {"status": "ok", "data": {"momentum": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  OPTIONS PRO (Strike-Level Intelligence)
# ═══════════════════════════════════════════════════════════
@router.get("/options-pro/strike")
async def options_pro_strike(symbol: str = "NIFTY", strike: int = 0, option_type: str = "CE"):
    """Get EXACT real-time price + IV + OI + recommendation for specific strike."""
    try:
        if _options_pro and hasattr(_options_pro, "get_strike_price"):
            result = await _run(_options_pro.get_strike_price, symbol, strike, option_type)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options-pro/nearby")
async def options_pro_nearby(symbol: str = "NIFTY", count: int = 10):
    """Get CE/PE prices for N strikes around ATM."""
    try:
        if _options_pro and hasattr(_options_pro, "get_nearby_options"):
            result = await _run(_options_pro.get_nearby_options, symbol, count)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/options-pro/chain-summary")
async def options_pro_chain_summary(symbol: str = "NIFTY"):
    """Full chain summary — ATM straddle, PCR, max pain, top CE/PE writers."""
    try:
        if _options_pro and hasattr(_options_pro, "get_full_chain_summary"):
            result = await _run(_options_pro.get_full_chain_summary, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  OPTIONS STRATEGY BUILDER (Straddle, Strangle, Spreads)
# ═══════════════════════════════════════════════════════════
@router.get("/strategy/recommend")
async def strategy_recommend(symbol: str = "NIFTY"):
    """AI recommends the best options strategy for current market conditions."""
    try:
        if _options and hasattr(_options, "recommend_strategy"):
            result = await _run(_options.recommend_strategy, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/straddle")
async def strategy_straddle(symbol: str = "NIFTY"):
    """Build ATM straddle with payoff analysis."""
    try:
        if _options and hasattr(_options, "build_straddle"):
            result = await _run(_options.build_straddle, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/strangle")
async def strategy_strangle(symbol: str = "NIFTY"):
    """Build OTM strangle with payoff analysis."""
    try:
        if _options and hasattr(_options, "build_strangle"):
            result = await _run(_options.build_strangle, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/bull-spread")
async def strategy_bull_spread(symbol: str = "NIFTY"):
    """Build bull call spread with limited risk."""
    try:
        if _options and hasattr(_options, "build_bull_call_spread"):
            result = await _run(_options.build_bull_call_spread, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/bear-spread")
async def strategy_bear_spread(symbol: str = "NIFTY"):
    """Build bear put spread with limited risk."""
    try:
        if _options and hasattr(_options, "build_bear_put_spread"):
            result = await _run(_options.build_bear_put_spread, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/iron-condor")
async def strategy_iron_condor(symbol: str = "NIFTY"):
    """Build iron condor for rangebound markets."""
    try:
        if _options and hasattr(_options, "build_iron_condor"):
            result = await _run(_options.build_iron_condor, symbol)
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/iv-analysis")
async def strategy_iv_analysis(symbol: str = "NIFTY"):
    """IV rank and percentile analysis for timing option trades."""
    try:
        if _options and hasattr(_options, "calculate_iv_rank_percentile"):
            result = await _run(_options.calculate_iv_rank_percentile, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/strategy/greeks")
async def strategy_greeks(spot: float = 25000, strike: float = 25000, days: float = 7, iv: float = 15, rate: float = 7, opt_type: str = "CE"):
    """Calculate Black-Scholes Greeks for any option."""
    try:
        if _options and hasattr(_options, "OptionGreeks") and hasattr(_options.OptionGreeks, "calculate_greeks"):
            T = days / 365.0
            result = _options.OptionGreeks.calculate_greeks(spot, strike, T, rate / 100.0, iv / 100.0, opt_type.upper())
            if hasattr(result, "__dict__"):
                result = result.__dict__
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  FUTURES BRAIN (F&O Core Intelligence)
# ═══════════════════════════════════════════════════════════
@router.get("/futures/dashboard")
async def futures_dashboard(symbol: str = "NIFTY"):
    """Complete F&O dashboard — PCR, max pain, VIX, straddle, OI distribution."""
    try:
        if _futures and hasattr(_futures, "get_futures_dashboard"):
            result = await _run(_futures.get_futures_dashboard, symbol)
            return {"status": "ok", "data": {"dashboard": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/futures/basis")
async def futures_basis(symbol: str = "NIFTY"):
    """Futures premium/discount to spot — measures sentiment."""
    try:
        if _futures and hasattr(_futures, "get_futures_basis"):
            result = await _run(_futures.get_futures_basis, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/futures/straddle")
async def futures_straddle(symbol: str = "NIFTY"):
    """ATM straddle premium — measures expected move."""
    try:
        if _futures and hasattr(_futures, "get_straddle_premium"):
            result = await _run(_futures.get_straddle_premium, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/futures/oi-distribution")
async def futures_oi_dist(symbol: str = "NIFTY"):
    """Full OI distribution across strikes."""
    try:
        if _futures and hasattr(_futures, "get_oi_distribution"):
            result = await _run(_futures.get_oi_distribution, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/futures/max-pain")
async def futures_max_pain(symbol: str = "NIFTY"):
    """Max pain level — where most options expire worthless."""
    try:
        if _futures and hasattr(_futures, "get_max_pain"):
            result = await _run(_futures.get_max_pain, symbol)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  CROSS-ASSET CORRELATION ENGINE
# ═══════════════════════════════════════════════════════════
@router.get("/correlations/scan")
async def correlations_scan():
    """Scan all cross-asset correlations: NIFTY/S&P500, BTC/Gold, etc."""
    try:
        if _cross_asset and hasattr(_cross_asset, "scan_all_correlations"):
            result = await _run(_cross_asset.scan_all_correlations)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/correlations/insight")
async def correlations_insight(symbol: str = "NIFTY"):
    """Correlation insight for a specific symbol."""
    try:
        if _cross_asset and hasattr(_cross_asset, "get_correlation_insight"):
            sym_map = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
            result = await _run(_cross_asset.get_correlation_insight, sym_map.get(symbol, symbol))
            return {"status": "ok", "data": {"insight": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  RISK MANAGER (Kelly, Position Sizing, Trailing SL)
# ═══════════════════════════════════════════════════════════
@router.get("/risk/kelly")
async def risk_kelly():
    """Kelly criterion from real trade history."""
    try:
        if _risk and hasattr(_risk, "kelly_from_real_trades"):
            result = await _run(_risk.kelly_from_real_trades)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/risk/position-size")
async def risk_position_size(capital: float = 100000, risk_pct: float = 2.0, entry: float = 100, sl: float = 95):
    """Calculate position size based on risk management."""
    try:
        if _risk and hasattr(_risk, "calculate_position_size"):
            result = await _run(_risk.calculate_position_size, capital=capital, risk_pct=risk_pct, entry_price=entry, stop_loss=sl)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/risk/investment-plan")
async def risk_investment_plan(capital: float = 50000):
    """Structured investment plan with allocation percentages."""
    try:
        if _risk and hasattr(_risk, "calculate_investment_plan"):
            result = await _run(_risk.calculate_investment_plan, total_capital=capital)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/risk/risk-reward")
async def risk_reward(entry: float = 100, sl: float = 95, target: float = 115):
    """Calculate risk-reward ratio."""
    try:
        if _risk and hasattr(_risk, "calculate_risk_reward"):
            result = await _run(_risk.calculate_risk_reward, entry_price=entry, stop_loss=sl, target_price=target)
            return {"status": "ok", "data": result}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  STOCK SCREENER PRO (15+ Screener Types)
# ═══════════════════════════════════════════════════════════
@router.get("/screener/run")
async def screener_run(query: str = ""):
    """Run a screener by natural language query."""
    try:
        if _screener and hasattr(_screener, "run_screener"):
            result = await _run(_screener.run_screener, query)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/oversold")
async def screener_oversold():
    """RSI oversold stocks — potential bounce candidates."""
    try:
        if _screener and hasattr(_screener, "screen_oversold"):
            result = await _run(_screener.screen_oversold)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/overbought")
async def screener_overbought():
    """RSI overbought stocks — potential reversal candidates."""
    try:
        if _screener and hasattr(_screener, "screen_overbought"):
            result = await _run(_screener.screen_overbought)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/volume-spike")
async def screener_volume_spike():
    """Stocks with unusual volume today."""
    try:
        if _screener and hasattr(_screener, "screen_volume_spike"):
            result = await _run(_screener.screen_volume_spike)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/gap-ups")
async def screener_gap_ups():
    """Gap-up stocks today."""
    try:
        if _screener and hasattr(_screener, "screen_gap_ups"):
            result = await _run(_screener.screen_gap_ups)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/momentum")
async def screener_top_momentum():
    """Top momentum stocks."""
    try:
        if _screener and hasattr(_screener, "screen_top_momentum"):
            result = await _run(_screener.screen_top_momentum)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/52week-high")
async def screener_52w_high():
    """Stocks near 52-week highs."""
    try:
        if _screener and hasattr(_screener, "screen_52week_high"):
            result = await _run(_screener.screen_52week_high)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/screener/bullish")
async def screener_strong_bull():
    """Strong bullish trend stocks."""
    try:
        if _screener and hasattr(_screener, "screen_strong_bullish"):
            result = await _run(_screener.screen_strong_bullish)
            return {"status": "ok", "data": {"result": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  NEWS BRAIN (Sentiment Analysis)
# ═══════════════════════════════════════════════════════════
@router.get("/news/market")
async def news_market():
    """Latest market news with AI sentiment analysis."""
    try:
        if _news and hasattr(_news, "get_market_news"):
            result = await _run(_news.get_market_news)
            return {"status": "ok", "data": {"news": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/news/stock")
async def news_stock(symbol: str = "RELIANCE"):
    """News for a specific stock with sentiment."""
    try:
        if _news and hasattr(_news, "get_stock_news"):
            result = await _run(_news.get_stock_news, symbol)
            return {"status": "ok", "data": {"news": result}}
        elif _news and hasattr(_news, "get_market_news"):
            result = await _run(_news.get_market_news, symbol)
            return {"status": "ok", "data": {"news": result}}
        return {"status": "ok", "data": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}
