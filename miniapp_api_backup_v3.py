"""
🚀 JARVIS Mini App API v3.0 — Ultimate AI Trading Platform
═══════════════════════════════════════════════════════════════════════
ALL 30+ modules integrated. CoinDCX + DexScreener + Pump.fun + ML/AI.
Auto-trader, live data, signals, risk management, portfolio tracking.
"""

import os
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from functools import lru_cache

logger = logging.getLogger("miniapp-api")

router = APIRouter(prefix="/api/miniapp", tags=["MiniApp"])

# ═══════════════════════════════════════════════════════════
#  TIMED CACHE (TTL-based caching for expensive calls)
# ═══════════════════════════════════════════════════════════
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def cached(key: str, ttl: int = 60):
    """Return cached value if fresh, else None"""
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    return None

def set_cache(key: str, value: Any):
    _cache[key] = value
    _cache_ts[key] = time.time()

# ═══════════════════════════════════════════════════════════
#  SAFE IMPORTS
# ═══════════════════════════════════════════════════════════

def safe_import(module_name, fallback=None):
    try:
        return __import__(module_name)
    except Exception as e:
        logger.warning(f"Module {module_name} not available: {e}")
        return fallback

# Pre-import all modules at startup
_payment = safe_import("jarvis_payment")
_coindcx = safe_import("coindcx_engine")
_crypto = safe_import("crypto_engine")
_buy_sell = safe_import("buy_sell_engine")
_ml_pred = safe_import("ml_predictor")
_ml_pipe = safe_import("ml_pipeline")
_risk = safe_import("risk_manager")
_regime = safe_import("market_regime")
_auto_trader = safe_import("auto_trader")
_ai_chat_mod = safe_import("ai_chat")
_jarvis_ai = safe_import("jarvis_ai")
_sentiment = safe_import("sentiment_engine")
_ai_signals = safe_import("ai_signals")

# ═══════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    modules = {}
    for name, mod in [("payment", _payment), ("coindcx", _coindcx), ("crypto", _crypto),
                       ("buy_sell", _buy_sell), ("ml_predictor", _ml_pred), ("risk", _risk),
                       ("regime", _regime), ("auto_trader", _auto_trader), ("ai_chat", _ai_chat_mod)]:
        modules[name] = "ok" if mod else "unavailable"
    return {"status": "ok", "service": "jarvis-miniapp-v3", "modules": modules,
            "timestamp": datetime.now().isoformat()}

# ═══════════════════════════════════════════════════════════
#  DASHBOARD — Main screen data
# ═══════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_dashboard(user_id: Optional[str] = None):
    try:
        # Run ALL 6 data fetches in PARALLEL with 10s timeout each
        async def _safe(coro, default):
            try:
                return await asyncio.wait_for(coro, timeout=10)
            except Exception as e:
                logger.warning(f"Dashboard sub-call failed: {e}")
                return default

        portfolio_t = _safe(asyncio.to_thread(_get_portfolio, user_id),
                            {"positions": [], "total_invested_inr": 0, "total_current_inr": 0,
                             "pnl_inr": 0, "pnl_pct": 0, "balance_inr": 0})
        markets_t = _safe(asyncio.to_thread(_get_market_ticker), [])
        signals_t = _safe(asyncio.to_thread(_get_quick_signals), [])
        movers_t = _safe(asyncio.to_thread(_get_top_movers), {"gainers": [], "losers": []})
        regime_t = _safe(asyncio.to_thread(_get_market_regime), {"regime": "UNKNOWN", "confidence": 0})
        trader_t = _safe(asyncio.to_thread(_get_trader_status, user_id), {"traders": [], "active_count": 0})

        portfolio, markets, signals, movers, regime_data, trader_status = await asyncio.gather(
            portfolio_t, markets_t, signals_t, movers_t, regime_t, trader_t
        )

        return {
            "portfolio": portfolio,
            "market_ticker": markets,
            "signals": signals,
            "top_movers": movers,
            "regime": regime_data,
            "auto_trader": trader_status,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {"portfolio": {}, "market_ticker": [], "signals": [],
                "top_movers": {"gainers": [], "losers": []}, "regime": {},
                "auto_trader": {}, "timestamp": datetime.now().isoformat()}

# ═══════════════════════════════════════════════════════════
#  MARKETS — Live crypto & stock data
# ═══════════════════════════════════════════════════════════

@router.get("/markets")
async def get_markets(category: Optional[str] = None, page: int = 1, sort: str = "volume"):
    try:
        result = {"stocks": [], "crypto": [], "trending": [], "indices": [], "web3_tokens": []}

        # CoinDCX live tickers
        if _coindcx:
            try:
                tickers = await asyncio.to_thread(_coindcx.get_inr_tickers)
                if tickers:
                    crypto = []
                    for t in tickers[:50]:
                        crypto.append({
                            "symbol": t.get("market", "").replace("I-", "").replace("_INR", ""),
                            "price": t.get("last_price", 0),
                            "change_24h": float(t.get("change_24_hour", 0)),
                            "volume": float(t.get("volume", 0)),
                            "high": float(t.get("high", 0)),
                            "low": float(t.get("low", 0)),
                            "currency": "INR",
                        })
                    result["crypto"] = sorted(crypto, key=lambda x: abs(float(x.get("volume", 0))), reverse=True)
            except Exception as e:
                logger.error(f"CoinDCX markets: {e}")

        # Web3 tokens
        if _coindcx:
            try:
                if category:
                    tokens = await asyncio.to_thread(_coindcx.get_tokens_by_category, category)
                else:
                    web3 = await asyncio.to_thread(_coindcx.get_all_web3_prices, page, 30, sort)
                    tokens = web3.get("tokens", [])
                result["web3_tokens"] = tokens[:30]
            except:
                pass

        # Trending gems from crypto_engine
        if _crypto:
            try:
                gems = await asyncio.to_thread(_crypto.scan_all_gems, 10, 20)
                result["trending"] = [{
                    "symbol": g.get("symbol", ""),
                    "name": g.get("name", ""),
                    "price_usd": g.get("price_usd", 0),
                    "change_1h": g.get("change_1h", 0),
                    "change_24h": g.get("change_24h", 0),
                    "market_cap": g.get("market_cap", 0),
                    "volume": g.get("volume_24h", 0),
                    "score": g.get("score", 0),
                    "chain": g.get("chain", ""),
                    "source": g.get("source", ""),
                } for g in gems[:20]]
            except:
                pass

        # Stock indices via yfinance
        try:
            import yfinance as yf
            for sym, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX"), ("^NSEBANK", "BANK NIFTY")]:
                try:
                    t = yf.Ticker(sym)
                    info = t.fast_info
                    result["indices"].append({
                        "symbol": sym, "name": name,
                        "price": round(info.last_price, 2) if hasattr(info, 'last_price') else 0,
                        "change": round(info.last_price - info.previous_close, 2) if hasattr(info, 'previous_close') else 0,
                        "change_pct": round(((info.last_price / info.previous_close) - 1) * 100, 2) if hasattr(info, 'previous_close') and info.previous_close else 0,
                    })
                except:
                    pass
        except:
            pass

        return result
    except Exception as e:
        logger.error(f"Markets error: {e}")
        return {"stocks": [], "crypto": [], "trending": [], "indices": [], "web3_tokens": []}

# ═══════════════════════════════════════════════════════════
#  SIGNALS — AI Buy/Sell signals
# ═══════════════════════════════════════════════════════════

@router.get("/signals")
async def get_signals(market: str = "all"):
    try:
        signals = []

        # CoinDCX ML signals
        if _coindcx and market in ("all", "crypto"):
            try:
                best = await asyncio.to_thread(_coindcx.scan_best_signals, 15)
                for s in (best or []):
                    signals.append({
                        "symbol": s.get("symbol", ""),
                        "signal": s.get("signal", "HOLD"),
                        "confidence": s.get("confidence", 0),
                        "price": s.get("price", 0),
                        "change_24h": s.get("change_24h", 0),
                        "source": "CoinDCX ML+TA",
                        "market": "crypto",
                    })
            except:
                pass

        # Web3 scan signals
        if _coindcx and market in ("all", "web3"):
            try:
                web3_sigs = await asyncio.to_thread(_coindcx.scan_all_web3_signals, 10)
                for s in (web3_sigs or []):
                    signals.append({
                        "symbol": s.get("symbol", ""),
                        "signal": s.get("signal", "HOLD"),
                        "confidence": s.get("confidence", 0),
                        "price": s.get("price", 0),
                        "change_24h": s.get("change_24h", 0),
                        "source": "Web3 ML Scan",
                        "market": "web3",
                    })
            except:
                pass

        # Buy/sell engine stock signals
        if _buy_sell and market in ("all", "stock"):
            try:
                stock_sigs = await asyncio.to_thread(_buy_sell.scan_nifty_signals, 10)
                for s in (stock_sigs or []):
                    signals.append({
                        "symbol": s.symbol,
                        "signal": s.signal_type.value if hasattr(s.signal_type, 'value') else str(s.signal_type),
                        "confidence": s.confidence,
                        "price": s.entry_price,
                        "target_1": s.target_1,
                        "target_2": s.target_2,
                        "stop_loss": s.stop_loss,
                        "risk_reward": s.risk_reward,
                        "source": "JARVIS TA Engine",
                        "market": "stock",
                    })
            except:
                pass

        # Crypto signals from buy_sell engine
        if _buy_sell and market in ("all", "crypto"):
            try:
                crypto_sigs = await asyncio.to_thread(_buy_sell.scan_crypto_signals, 10)
                for s in (crypto_sigs or []):
                    signals.append({
                        "symbol": s.symbol,
                        "signal": s.signal_type.value if hasattr(s.signal_type, 'value') else str(s.signal_type),
                        "confidence": s.confidence,
                        "price": s.entry_price,
                        "target_1": s.target_1,
                        "stop_loss": s.stop_loss,
                        "source": "JARVIS Crypto TA",
                        "market": "crypto",
                    })
            except:
                pass

        # Sort by confidence
        signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return {"signals": signals[:30], "count": len(signals), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Signals error: {e}")
        return {"signals": [], "count": 0}

# ═══════════════════════════════════════════════════════════
#  ANALYZE — Deep analysis of a symbol
# ═══════════════════════════════════════════════════════════

@router.get("/analyze")
async def analyze_symbol(symbol: str = Query(...)):
    try:
        result = {"symbol": symbol, "analysis": {}, "signal": {}, "ml": {}, "investment": {}}

        # CoinDCX composite signal
        if _coindcx:
            try:
                comp = await asyncio.to_thread(_coindcx.get_composite_signal, symbol)
                result["analysis"] = comp or {}
            except:
                pass

        # Buy/sell signal
        if _buy_sell:
            try:
                sig = await asyncio.to_thread(_buy_sell.get_crypto_signal, symbol)
                if sig:
                    result["signal"] = {
                        "type": sig.signal_type.value if hasattr(sig.signal_type, 'value') else str(sig.signal_type),
                        "confidence": sig.confidence,
                        "entry": sig.entry_price,
                        "stop_loss": sig.stop_loss,
                        "target_1": sig.target_1,
                        "target_2": sig.target_2,
                        "target_3": sig.target_3,
                        "risk_reward": sig.risk_reward,
                        "trend": sig.trend,
                        "volume_signal": sig.volume_signal,
                        "indicators": [{"name": i.name, "value": i.value, "signal": i.signal} for i in (sig.indicators or [])],
                    }
            except:
                pass

        # Investment calculator
        if _coindcx:
            try:
                inv = await asyncio.to_thread(_coindcx.calculate_investment, symbol, 2000)
                result["investment"] = inv or {}
            except:
                pass

        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {"symbol": symbol, "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  ML PREDICTIONS — Index & crypto predictions
# ═══════════════════════════════════════════════════════════

@router.get("/predictions")
async def get_predictions(symbol: str = "^NSEI", name: str = "NIFTY"):
    try:
        result = {}
        if _ml_pred:
            try:
                pred = await asyncio.to_thread(_ml_pred.predict_index_direction, symbol, name)
                result = {
                    "direction": pred.get("direction_label", "NEUTRAL"),
                    "confidence": pred.get("confidence", 0),
                    "model_votes": pred.get("model_votes", {}),
                    "individual_models": pred.get("individual_models", {}),
                    "features_used": pred.get("features_used", 0),
                    "prediction_time": pred.get("prediction_time", ""),
                }
            except Exception as e:
                result = {"error": str(e)}

        if _ml_pipe:
            try:
                pipe_pred = await asyncio.to_thread(_ml_pipe.predict_for_symbol, symbol)
                if pipe_pred:
                    result["pipeline"] = pipe_pred
            except:
                pass

        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  WALLET & PORTFOLIO
# ═══════════════════════════════════════════════════════════

@router.get("/wallet")
async def get_wallet(user_id: Optional[str] = None):
    try:
        if not _payment or not user_id:
            return {"balance_inr": 0, "portfolio": [], "transactions": [], "tax": {}}

        chat_id = int(user_id) if user_id else 0
        wallet = await asyncio.to_thread(_payment.get_wallet, chat_id)
        portfolio = await asyncio.to_thread(_payment.get_portfolio, chat_id)
        transactions = await asyncio.to_thread(_payment.get_transaction_history, chat_id, 30)

        return {
            "balance_inr": wallet.get("balance_inr", 0),
            "total_deposited": wallet.get("total_deposited", 0),
            "total_withdrawn": wallet.get("total_withdrawn", 0),
            "total_profit": wallet.get("total_profit", 0),
            "portfolio": {
                "positions": portfolio.get("positions", []),
                "total_invested_inr": portfolio.get("total_invested_inr", 0),
                "total_current_inr": portfolio.get("total_current_inr", 0),
                "pnl_inr": portfolio.get("pnl_inr", 0),
                "pnl_pct": portfolio.get("pnl_pct", 0),
                "winners": portfolio.get("winners", 0),
                "losers": portfolio.get("losers", 0),
            },
            "transactions": transactions,
            "tax": portfolio.get("tax_info", {}),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Wallet error: {e}")
        return {"balance_inr": 0, "portfolio": {}, "transactions": [], "error": str(e)}

@router.post("/deposit")
async def deposit(request: Request):
    try:
        body = await request.json()
        user_id = body.get("user_id")
        amount = float(body.get("amount", 0))

        if not _payment or not user_id:
            return {"error": "Payment system unavailable"}
        if amount < 100:
            return {"error": "Minimum deposit: ₹1"}
        if amount > 500000:
            return {"error": "Maximum deposit: ₹5,00,000"}

        result = await asyncio.to_thread(_payment.generate_deposit_qr, int(user_id), amount)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/verify-deposit")
async def verify_deposit(request: Request):
    try:
        body = await request.json()
        user_id = body.get("user_id")
        utr = body.get("utr", "")
        if not _payment or not user_id:
            return {"error": "Payment system unavailable"}
        result = await asyncio.to_thread(_payment.verify_deposit, int(user_id), utr)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/withdraw")
async def withdraw(request: Request):
    try:
        body = await request.json()
        user_id = body.get("user_id")
        amount = float(body.get("amount", 0))
        if not _payment or not user_id:
            return {"error": "Payment system unavailable"}
        result = await asyncio.to_thread(_payment.request_withdrawal, int(user_id), amount)
        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  AUTO-TRADER — AI Auto-Investment
# ═══════════════════════════════════════════════════════════

@router.get("/auto-trader/strategies")
async def get_strategies():
    if _auto_trader:
        return _auto_trader.get_all_strategies()
    return {"strategies": []}

@router.post("/auto-trader/start")
async def start_trader(request: Request):
    try:
        body = await request.json()
        user_id = int(body.get("user_id", 0))
        amount = float(body.get("amount", 0))
        strategy = body.get("strategy", "balanced")
        target = float(body.get("target_inr", 0))
        auto_withdraw = body.get("auto_withdraw", True)

        if not _auto_trader:
            return {"error": "Auto-trader unavailable"}
        if not user_id:
            return {"error": "User ID required"}
        if amount < 100:
            return {"error": "Minimum: ₹100"}

        result = await asyncio.to_thread(
            _auto_trader.start_auto_trader,
            user_id, amount, strategy, target, auto_withdraw
        )
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/auto-trader/stop")
async def stop_trader(request: Request):
    try:
        body = await request.json()
        user_id = int(body.get("user_id", 0))
        trader_id = body.get("trader_id")
        sell_all = body.get("sell_all", True)

        if not _auto_trader:
            return {"error": "Auto-trader unavailable"}

        result = await asyncio.to_thread(_auto_trader.stop_auto_trader, user_id, trader_id, sell_all)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/auto-trader/status")
async def trader_status(user_id: str = Query(...)):
    try:
        if not _auto_trader:
            return {"traders": [], "active_count": 0}
        result = await asyncio.to_thread(_auto_trader.get_trader_status, int(user_id))
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/auto-trader/gems")
async def preview_gems(strategy: str = "balanced"):
    try:
        if not _auto_trader:
            return {"gems_found": 0, "top_picks": []}
        result = await asyncio.wait_for(
            asyncio.to_thread(_auto_trader.get_available_gems, strategy),
            timeout=15
        )
        return result
    except asyncio.TimeoutError:
        return {"gems_found": 0, "top_picks": [], "note": "Scan timed out, try again"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/auto-trader/compound")
async def compound(request: Request):
    try:
        body = await request.json()
        user_id = int(body.get("user_id", 0))
        if not _auto_trader:
            return {"error": "Auto-trader unavailable"}
        result = await asyncio.to_thread(_auto_trader.compound_profits, user_id)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/auto-trader/performance")
async def performance(user_id: str = Query(...)):
    try:
        if not _auto_trader:
            return {"error": "Auto-trader unavailable"}
        result = await asyncio.to_thread(_auto_trader.get_performance_report, int(user_id))
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/sell-position")
async def sell_position(request: Request):
    try:
        body = await request.json()
        user_id = int(body.get("user_id", 0))
        inv_id = body.get("position_id", "")
        if not _payment:
            return {"error": "Payment system unavailable"}
        result = await asyncio.to_thread(_payment.sell_position, user_id, inv_id)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/sell-all")
async def sell_all_positions(request: Request):
    try:
        body = await request.json()
        user_id = int(body.get("user_id", 0))
        if not _payment:
            return {"error": "Payment system unavailable"}
        result = await asyncio.to_thread(_payment.sell_all, user_id)
        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  GEMS & DIP SCANNER
# ═══════════════════════════════════════════════════════════

@router.get("/gems")
async def scan_gems(min_score: int = 10, source: str = "all"):
    try:
        gems = []

        if _crypto and source in ("all", "trending"):
            try:
                trending = await asyncio.to_thread(_crypto.scan_trending_gems, min_score, 20)
                gems.extend(trending or [])
            except:
                pass

        if _crypto and source in ("all", "dips"):
            try:
                dips = await asyncio.to_thread(_crypto.scan_dip_tokens, -5.0, 15)
                gems.extend(dips or [])
            except:
                pass

        if _crypto and source in ("all", "multichain"):
            try:
                multi = await asyncio.to_thread(_crypto.scan_multichain_gems, min_score, 15)
                gems.extend(multi or [])
            except:
                pass

        if _crypto and source in ("all", "new"):
            try:
                new = await asyncio.to_thread(_crypto.scan_pump_newest, min_score, 15)
                gems.extend(new or [])
            except:
                pass

        # Deduplicate
        seen = set()
        unique = []
        for g in gems:
            key = g.get("token_id", g.get("symbol", str(id(g))))
            if key not in seen:
                seen.add(key)
                unique.append(g)

        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {"gems": unique[:30], "count": len(unique), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"gems": [], "error": str(e)}

@router.get("/dip-alerts")
async def dip_alerts():
    try:
        alerts = []
        if _crypto:
            alerts = await asyncio.to_thread(_crypto.get_new_dip_alerts, -10.0)
        return {"alerts": alerts or [], "count": len(alerts or [])}
    except:
        return {"alerts": [], "count": 0}

@router.get("/top-movers")
async def top_movers():
    try:
        result = {"gainers": [], "losers": []}
        if _coindcx:
            try:
                data = await asyncio.to_thread(_coindcx.get_top_gainers_losers, 15)
                result["gainers"] = data.get("gainers", [])
                result["losers"] = data.get("losers", [])
            except:
                pass
        if _crypto and not result["gainers"]:
            try:
                data = await asyncio.to_thread(_crypto.get_web3_gainers_losers, 15) if hasattr(_crypto, "get_web3_gainers_losers") else {}
                result["gainers"] = data.get("gainers", [])
                result["losers"] = data.get("losers", [])
            except:
                pass
        return result
    except:
        return {"gainers": [], "losers": []}

# ═══════════════════════════════════════════════════════════
#  RISK MANAGEMENT
# ═══════════════════════════════════════════════════════════

@router.get("/risk")
async def get_risk(user_id: Optional[str] = None, capital: float = 100000):
    try:
        result = {"regime": {}, "position_size": {}, "kelly": {}, "risk_reward": {}}

        if _regime:
            try:
                regime = await asyncio.to_thread(_regime.get_regime_quick)
                result["regime"] = regime
            except:
                pass

        if _risk:
            try:
                pos = _risk.calculate_position_size(capital=capital, risk_per_trade_pct=2.0)
                result["position_size"] = pos
            except:
                pass
            try:
                kelly = _risk.kelly_criterion(win_rate=0.55, avg_win=5000, avg_loss=3000)
                result["kelly"] = kelly
            except:
                pass

        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  OPTIONS CHAIN
# ═══════════════════════════════════════════════════════════

@router.get("/options")
async def get_options(index: str = "NIFTY"):
    try:
        result = {"chain": [], "analysis": {}, "sentiment": ""}
        try:
            from stock_data_fetcher import fetch_nse_option_chain, analyze_option_chain
            chain = await asyncio.to_thread(fetch_nse_option_chain, index)
            if chain:
                analysis = analyze_option_chain(chain)
                result["chain"] = chain[:20] if isinstance(chain, list) else []
                result["analysis"] = analysis or {}
        except:
            pass

        try:
            from live_index_engine import generate_index_option_chain
            oi_data = await asyncio.to_thread(generate_index_option_chain, index)
            if oi_data:
                result["oi_analysis"] = oi_data
        except:
            pass

        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  SCREENER
# ═══════════════════════════════════════════════════════════

@router.get("/screener")
async def screener(preset: str = "top_signals", q: Optional[str] = None):
    try:
        results = []

        if preset == "top_signals" and _buy_sell:
            sigs = await asyncio.to_thread(_buy_sell.scan_nifty_signals, 20)
            results = [{
                "symbol": s.symbol,
                "signal": s.signal_type.value if hasattr(s.signal_type, 'value') else str(s.signal_type),
                "confidence": s.confidence,
                "price": s.entry_price,
                "target": s.target_1,
                "stop_loss": s.stop_loss,
            } for s in (sigs or [])]

        elif preset == "crypto_signals" and _buy_sell:
            sigs = await asyncio.to_thread(_buy_sell.scan_crypto_signals, 20)
            results = [{
                "symbol": s.symbol,
                "signal": s.signal_type.value if hasattr(s.signal_type, 'value') else str(s.signal_type),
                "confidence": s.confidence,
                "price": s.entry_price,
                "target": s.target_1,
                "stop_loss": s.stop_loss,
            } for s in (sigs or [])]

        elif preset == "gem_scanner" and _payment:
            gems = await asyncio.to_thread(_payment.scan_gem_tokens)
            results = gems or []

        elif preset == "web3" and _coindcx:
            sigs = await asyncio.to_thread(_coindcx.scan_all_web3_signals, 20)
            results = sigs or []

        elif q and _coindcx:
            results_raw = await asyncio.to_thread(_coindcx.search_web3_token, q)
            results = results_raw or []

        return {"results": results[:30], "preset": preset, "count": len(results)}
    except Exception as e:
        return {"results": [], "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  SENTIMENT
# ═══════════════════════════════════════════════════════════

@router.get("/sentiment")
async def get_sentiment():
    try:
        result = {"fear_greed": 50, "label": "Neutral", "social": {}, "news": []}

        if _sentiment:
            try:
                if hasattr(_sentiment, "get_fear_greed_index"):
                    fg = await asyncio.to_thread(_sentiment.get_fear_greed_index)
                    result["fear_greed"] = fg.get("value", 50) if fg else 50
                    result["label"] = fg.get("label", "Neutral") if fg else "Neutral"
            except:
                pass

        # News from various sources
        try:
            news_key = os.environ.get("NEWS_API_KEY", "")
            if news_key:
                import requests
                resp = requests.get(
                    f"https://newsapi.org/v2/everything?q=crypto+bitcoin&sortBy=publishedAt&pageSize=5&apiKey={news_key}",
                    timeout=5
                )
                if resp.ok:
                    articles = resp.json().get("articles", [])
                    result["news"] = [{
                        "title": a.get("title", ""),
                        "source": a.get("source", {}).get("name", ""),
                        "url": a.get("url", ""),
                        "time": a.get("publishedAt", ""),
                    } for a in articles[:5]]
        except:
            pass

        return result
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  AI CHAT
# ═══════════════════════════════════════════════════════════

@router.post("/chat")
async def ai_chat(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")
        user_id = body.get("user_id", "0")

        if not message:
            return {"reply": "Please enter a message."}

        reply = ""

        # Try JARVIS AI first
        if _jarvis_ai and hasattr(_jarvis_ai, "classify_intent"):
            try:
                intent = _jarvis_ai.classify_intent(message)
                if intent:
                    reply = f"[Intent: {intent}] "
            except:
                pass

        # Try ai_chat module
        if _ai_chat_mod and hasattr(_ai_chat_mod, "ai_chat"):
            try:
                chat_reply = await asyncio.to_thread(_ai_chat_mod.ai_chat, message, user_id)
                if chat_reply:
                    reply = chat_reply
            except:
                pass

        # Fallback: GROQ
        if not reply:
            try:
                groq_key = os.environ.get("GROQ_API_KEY", "")
                if groq_key:
                    import requests
                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": "You are JARVIS, an AI trading assistant. Help with crypto, stocks, market analysis. Be concise, data-driven."},
                                {"role": "user", "content": message},
                            ],
                            "max_tokens": 1000,
                        },
                        timeout=15,
                    )
                    if resp.ok:
                        reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            except:
                pass

        if not reply:
            reply = "I'm processing your request. Please try again in a moment."

        return {"reply": reply, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

# ═══════════════════════════════════════════════════════════
#  AIRDROPS
# ═══════════════════════════════════════════════════════════

@router.get("/airdrops")
async def get_airdrops():
    try:
        airdrops = []
        # Load from file
        try:
            with open("jarvis_airdrops.json") as f:
                airdrops = json.load(f)
        except:
            pass

        # New gem alerts
        if _crypto:
            try:
                alerts = await asyncio.to_thread(_crypto.get_new_gem_alerts, 40)
                for a in (alerts or []):
                    airdrops.append({
                        "name": a.get("name", "New Gem"),
                        "symbol": a.get("symbol", ""),
                        "type": "gem_alert",
                        "score": a.get("score", 0),
                        "chain": a.get("chain", ""),
                        "status": "active",
                    })
            except:
                pass

        return {"airdrops": airdrops[:20], "count": len(airdrops)}
    except:
        return {"airdrops": [], "count": 0}

# ═══════════════════════════════════════════════════════════
#  TAX CALCULATOR
# ═══════════════════════════════════════════════════════════

@router.get("/tax")
async def get_tax(user_id: str = Query(...)):
    try:
        if not _payment:
            return {"error": "Payment system unavailable"}
        report = await asyncio.to_thread(_payment.format_tax_report, int(user_id))
        portfolio = await asyncio.to_thread(_payment.get_portfolio, int(user_id))
        return {
            "report": report,
            "tax_info": portfolio.get("tax_info", {}),
            "total_profit": portfolio.get("pnl_inr", 0),
        }
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════

def _get_portfolio(user_id):
    if _payment and user_id:
        try:
            return _payment.get_portfolio(int(user_id))
        except:
            pass
    return {"positions": [], "total_invested_inr": 0, "total_current_inr": 0,
            "pnl_inr": 0, "pnl_pct": 0, "balance_inr": 0}

def _get_market_ticker():
    hit = cached("market_ticker", ttl=60)
    if hit is not None:
        return hit
    tickers = []
    try:
        import yfinance as yf
        for sym, name, currency in [("^NSEI", "NIFTY 50", "INR"), ("^BSESN", "SENSEX", "INR"),
                                     ("BTC-USD", "Bitcoin", "USD"), ("ETH-USD", "Ethereum", "USD"),
                                     ("SOL-USD", "Solana", "USD")]:
            try:
                t = yf.Ticker(sym)
                info = t.fast_info
                price = round(info.last_price, 2) if hasattr(info, "last_price") else 0
                prev = info.previous_close if hasattr(info, "previous_close") else price
                change_pct = round(((price / prev) - 1) * 100, 2) if prev else 0
                tickers.append({"symbol": sym, "name": name, "price": price,
                                "change_pct": change_pct, "currency": currency})
            except:
                pass
    except:
        pass

    # Add CoinDCX data
    if _coindcx:
        try:
            inr_tickers = _coindcx.get_inr_tickers()
            for t in (inr_tickers or [])[:5]:
                tickers.append({
                    "symbol": t.get("market", ""),
                    "name": t.get("market", "").replace("I-", "").replace("_INR", ""),
                    "price": float(t.get("last_price", 0)),
                    "change_pct": float(t.get("change_24_hour", 0)),
                    "currency": "INR",
                })
        except:
            pass

    set_cache("market_ticker", tickers)
    return tickers

def _get_quick_signals():
    hit = cached("quick_signals", ttl=60)
    if hit is not None:
        return hit
    signals = []
    if _coindcx:
        try:
            best = _coindcx.scan_best_signals(5)
            for s in (best or []):
                signals.append({
                    "symbol": s.get("symbol", ""),
                    "signal": s.get("signal", "HOLD"),
                    "confidence": s.get("confidence", 0),
                    "source": "ML+TA",
                })
        except:
            pass
    if _buy_sell:
        try:
            sigs = _buy_sell.scan_crypto_signals(5)
            for s in (sigs or []):
                signals.append({
                    "symbol": s.symbol,
                    "signal": s.signal_type.value if hasattr(s.signal_type, 'value') else str(s.signal_type),
                    "confidence": s.confidence,
                    "source": "TA Engine",
                })
        except:
            pass
    result = signals[:10]
    set_cache("quick_signals", result)
    return result

def _get_top_movers():
    hit = cached("top_movers", ttl=60)
    if hit is not None:
        return hit
    result = {"gainers": [], "losers": []}
    if _coindcx:
        try:
            data = _coindcx.get_top_gainers_losers(10)
            result = data or result
        except:
            pass
    set_cache("top_movers", result)
    return result

def _get_market_regime():
    hit = cached("market_regime", ttl=120)
    if hit is not None:
        return hit
    result = {"regime": "UNKNOWN", "confidence": 0}
    if _regime:
        try:
            result = _regime.get_regime_quick()
        except:
            pass
    set_cache("market_regime", result)
    return result

def _get_trader_status(user_id):
    if _auto_trader and user_id:
        try:
            return _auto_trader.get_trader_status(int(user_id))
        except:
            pass
    return {"traders": [], "active_count": 0}
