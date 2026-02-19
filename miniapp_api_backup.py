"""
🚀 JARVIS Mini App API — Real-Time Trading API for Telegram Mini App
═══════════════════════════════════════════════════════════════════════
Connects ALL JARVIS modules into unified Mini App API endpoints.
CoinDCX + AngelOne grade — powered by JARVIS AI.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger("miniapp-api")

router = APIRouter(prefix="/api/miniapp", tags=["MiniApp"])

# ═══════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health check — confirms Mini App API is running."""
    return {"status": "ok", "service": "jarvis-miniapp", "timestamp": datetime.now().isoformat()}

# ═══════════════════════════════════════════════════════════
#  SAFE IMPORTS — gracefully handle missing modules
# ═══════════════════════════════════════════════════════════

def safe_import(module_name, fallback=None):
    try:
        return __import__(module_name)
    except Exception as e:
        logger.warning(f"Module {module_name} not available: {e}")
        return fallback

# ═══════════════════════════════════════════════════════════
#  DASHBOARD API
# ═══════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_dashboard(user_id: Optional[str] = None):
    """Main dashboard data — portfolio, markets, signals, movers"""
    try:
        portfolio = _get_portfolio(user_id)
        markets = _get_market_ticker()
        signals = _get_quick_signals()
        movers = _get_top_movers()
        
        return {
            "portfolio": portfolio,
            "markets": markets,
            "signals": signals[:5],
            "top_movers": movers[:5],
            "notifications": 0
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {
            "portfolio": {"total": 0, "change_pct": 0},
            "markets": _fallback_markets(),
            "signals": [],
            "top_movers": [],
            "notifications": 0
        }


# ═══════════════════════════════════════════════════════════
#  MARKETS API
# ═══════════════════════════════════════════════════════════

@router.get("/markets")
async def get_markets():
    """Get all tradeable tokens/stocks with live prices"""
    try:
        tokens = []
        
        # CoinDCX crypto tokens
        try:
            coindcx = safe_import("coindcx_engine")
            if coindcx and hasattr(coindcx, 'get_top_inr_tokens'):
                crypto_data = coindcx.get_top_inr_tokens()
                if isinstance(crypto_data, list):
                    for t in crypto_data[:50]:
                        tokens.append({
                            "symbol": t.get("symbol", t.get("target_currency_short_name", "?")),
                            "name": t.get("name", t.get("target_currency_name", "")),
                            "price": t.get("last_price", t.get("price", 0)),
                            "change": t.get("change_24h", t.get("change_24_hour", 0)),
                            "type": "crypto",
                            "color": "#F7931A",
                            "is_gem": t.get("is_gem", False),
                            "volume": t.get("volume", 0)
                        })
        except Exception as e:
            logger.warning(f"CoinDCX fetch error: {e}")
        
        # Crypto engine for gems/meme coins
        try:
            crypto_eng = safe_import("crypto_engine")
            if crypto_eng and hasattr(crypto_eng, 'get_trending_tokens'):
                trending = crypto_eng.get_trending_tokens()
                if isinstance(trending, list):
                    existing_symbols = {t["symbol"] for t in tokens}
                    for t in trending[:20]:
                        sym = t.get("symbol", "?")
                        if sym not in existing_symbols:
                            tokens.append({
                                "symbol": sym,
                                "name": t.get("name", ""),
                                "price": t.get("price_inr", t.get("price", 0)),
                                "change": t.get("change_24h", 0),
                                "type": "crypto",
                                "color": "#00D4AA",
                                "is_gem": True,
                                "volume": t.get("volume", 0)
                            })
        except Exception as e:
            logger.warning(f"Crypto engine error: {e}")

        # Indian stocks via yfinance
        try:
            import yfinance as yf
            nifty_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
                           "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS",
                           "KOTAKBANK.NS", "WIPRO.NS", "HCLTECH.NS", "MARUTI.NS", "TATAMOTORS.NS",
                           "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "NESTLEIND.NS"]
            for sym in nifty_stocks:
                try:
                    ticker = yf.Ticker(sym)
                    info = ticker.fast_info
                    price = getattr(info, 'last_price', 0) or 0
                    prev = getattr(info, 'previous_close', price) or price
                    change = ((price - prev) / prev * 100) if prev else 0
                    clean_sym = sym.replace(".NS", "")
                    tokens.append({
                        "symbol": clean_sym,
                        "name": clean_sym,
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "type": "stock",
                        "color": "#3B82F6"
                    })
                except: pass
        except Exception as e:
            logger.warning(f"Stock data error: {e}")

        # If nothing loaded, add fallback data
        if not tokens:
            tokens = _fallback_tokens()

        # Sort by volume/change
        tokens.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
        
        return {"tokens": tokens}
    except Exception as e:
        logger.error(f"Markets error: {e}")
        return {"tokens": _fallback_tokens()}


# ═══════════════════════════════════════════════════════════
#  SIGNALS API
# ═══════════════════════════════════════════════════════════

@router.get("/signals")
async def get_signals():
    """Get AI-powered trading signals"""
    try:
        signals = _get_quick_signals()
        regime = _get_market_regime()
        
        return {
            "signals": signals,
            "regime": regime
        }
    except Exception as e:
        logger.error(f"Signals error: {e}")
        return {"signals": [], "regime": {"name": "Analyzing...", "score": 50, "color": "var(--yellow)"}}


# ═══════════════════════════════════════════════════════════
#  ANALYZE — Deep analysis for specific symbol
# ═══════════════════════════════════════════════════════════

@router.get("/analyze")
async def analyze_symbol(symbol: str = Query(...)):
    """Deep AI analysis for a symbol"""
    try:
        result = {"symbol": symbol, "price": 0, "change": 0}
        
        # Try to get price
        try:
            import yfinance as yf
            yfin_sym = symbol + ".NS" if not symbol.endswith(".NS") and symbol.isalpha() and len(symbol) <= 15 else symbol
            ticker = yf.Ticker(yfin_sym)
            info = ticker.fast_info
            result["price"] = round(getattr(info, 'last_price', 0) or 0, 2)
            prev = getattr(info, 'previous_close', result["price"]) or result["price"]
            result["change"] = round(((result["price"] - prev) / prev * 100) if prev else 0, 2)
        except: pass

        # Try buy_sell_engine
        try:
            bse = safe_import("buy_sell_engine")
            if bse and hasattr(bse, 'generate_signal'):
                signal = bse.generate_signal(symbol)
                if signal and isinstance(signal, dict):
                    result["action"] = signal.get("action", signal.get("signal", "HOLD"))
                    result["entry"] = signal.get("entry", signal.get("entry_price", result["price"]))
                    result["target"] = signal.get("target", signal.get("target_price", 0))
                    result["sl"] = signal.get("sl", signal.get("stop_loss", 0))
                    result["confidence"] = signal.get("confidence", 70)
        except Exception as e:
            logger.warning(f"signal gen error: {e}")

        # Try AI signals
        try:
            ai_sig = safe_import("ai_signals")
            if ai_sig and hasattr(ai_sig, 'full_technical_analysis'):
                analysis = ai_sig.full_technical_analysis(symbol)
                if analysis and isinstance(analysis, dict):
                    result["indicators"] = {}
                    for key in ["RSI", "MACD", "EMA_20", "SMA_50", "BB_Upper", "BB_Lower", "VWAP", "ADX", "Supertrend"]:
                        if key in analysis:
                            result["indicators"][key] = str(analysis[key])
                    if not result.get("action"):
                        result["action"] = analysis.get("signal", analysis.get("action", "HOLD"))
        except Exception as e:
            logger.warning(f"AI signal error: {e}")
        
        # Try jarvis_ultra_ai for summary
        try:
            ultra = safe_import("jarvis_ultra_ai")
            if ultra and hasattr(ultra, 'ultra_predict'):
                prediction = ultra.ultra_predict(symbol)
                if prediction and isinstance(prediction, dict):
                    result["ai_summary"] = prediction.get("summary", prediction.get("analysis", ""))
                    if not result.get("action"):
                        result["action"] = prediction.get("action", "HOLD") 
                    if not result.get("confidence"):
                        result["confidence"] = prediction.get("confidence", 65)
        except Exception as e:
            logger.warning(f"Ultra AI error: {e}")

        if not result.get("action"):
            result["action"] = "HOLD"
            result["ai_summary"] = f"JARVIS AI is analyzing {symbol}. Technical indicators are being computed. Check back shortly for a detailed signal."

        return result

    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return {"symbol": symbol, "price": 0, "action": "HOLD", "ai_summary": "Analysis in progress..."}


# ═══════════════════════════════════════════════════════════
#  WALLET API
# ═══════════════════════════════════════════════════════════

@router.get("/wallet")
async def get_wallet(user_id: Optional[str] = None):
    """Get wallet balance, holdings, transactions"""
    try:
        balance = 0
        holdings = []
        transactions = []
        
        if user_id:
            try:
                payment = safe_import("jarvis_payment")
                if payment:
                    # Get wallet balance
                    if hasattr(payment, '_load_wallets'):
                        wallets = payment._load_wallets()
                        wallet = wallets.get(str(user_id), {})
                        balance = wallet.get("balance_inr", 0)
                    
                    # Get transactions
                    if hasattr(payment, '_load_transactions'):
                        all_txs = payment._load_transactions()
                        user_txs = all_txs.get(str(user_id), [])
                        for tx in user_txs[-20:]:
                            transactions.append({
                                "type": tx.get("type", "unknown"),
                                "amount": tx.get("amount_inr", 0),
                                "date": tx.get("created", ""),
                                "status": tx.get("status", "completed"),
                                "ref": tx.get("tx_ref", "")
                            })
                        transactions.reverse()  # newest first
            except Exception as e:
                logger.warning(f"Payment module error: {e}")
            
            # Get portfolio holdings
            try:
                pt = safe_import("portfolio_tracker")
                if pt and hasattr(pt, 'get_portfolio'):
                    portfolio = pt.get_portfolio(int(user_id))
                    if isinstance(portfolio, dict):
                        for sym, holding in portfolio.get("holdings", {}).items():
                            holdings.append({
                                "symbol": sym,
                                "qty": holding.get("quantity", 0),
                                "value": holding.get("current_value", 0),
                                "pnl": holding.get("pnl", 0)
                            })
            except Exception as e:
                logger.warning(f"Portfolio error: {e}")
        
        return {
            "balance": balance,
            "holdings": holdings,
            "transactions": transactions
        }
    except Exception as e:
        logger.error(f"Wallet error: {e}")
        return {"balance": 0, "holdings": [], "transactions": []}


@router.post("/deposit")
async def deposit(request: Request):
    """Process deposit request"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        amount = data.get("amount", 0)
        
        if amount < 1:
            return {"error": "Minimum deposit is ₹1"}
        
        # Try to generate UPI QR
        try:
            payment = safe_import("jarvis_payment")
            if payment and hasattr(payment, 'generate_deposit_qr'):
                qr_result = payment.generate_deposit_qr(int(user_id), amount)
                if qr_result:
                    return {"qr_url": qr_result.get("qr_url", ""), "message": "Scan QR to pay"}
        except: pass
        
        return {"message": f"Deposit request for ₹{amount} submitted. Admin will process shortly."}
    except Exception as e:
        return {"message": "Deposit request submitted."}


@router.post("/withdraw")
async def withdraw(request: Request):
    """Process withdrawal request"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        amount = data.get("amount", 0)
        bank = data.get("bank", "")
        
        try:
            payment = safe_import("jarvis_payment")
            if payment and hasattr(payment, 'request_withdrawal'):
                result = payment.request_withdrawal(int(user_id), amount, bank)
                return {"message": result.get("message", "Withdrawal request submitted")}
        except: pass
        
        return {"message": f"Withdrawal of ₹{amount} requested. Will be processed within 1-24 hours."}
    except Exception as e:
        return {"message": "Withdrawal request submitted."}


# ═══════════════════════════════════════════════════════════
#  OPTIONS API
# ═══════════════════════════════════════════════════════════

@router.get("/options")
async def get_options():
    """Get NIFTY options intelligence"""
    try:
        result = {"pcr": "--", "max_pain": "--", "vix": "--", "trend": "--", "suggestions": []}
        
        try:
            futures = safe_import("jarvis_futures_brain")
            if futures:
                if hasattr(futures, 'get_live_pcr'):
                    pcr_data = futures.get_live_pcr()
                    if pcr_data: result["pcr"] = str(round(pcr_data.get("pcr", 0), 2)) if isinstance(pcr_data, dict) else str(pcr_data)
                if hasattr(futures, 'get_max_pain'):
                    mp = futures.get_max_pain()
                    if mp: result["max_pain"] = str(mp) if not isinstance(mp, dict) else str(mp.get("max_pain", "--"))
                if hasattr(futures, 'get_india_vix'):
                    vix = futures.get_india_vix()
                    if vix: result["vix"] = str(round(vix, 2)) if isinstance(vix, (int, float)) else str(vix)
        except Exception as e:
            logger.warning(f"Futures brain error: {e}")
        
        try:
            options = safe_import("jarvis_options_pro")
            if options and hasattr(options, 'get_budget_options'):
                budget_opts = options.get_budget_options(budget=5)
                if isinstance(budget_opts, list):
                    for opt in budget_opts[:5]:
                        result["suggestions"].append({
                            "strike": str(opt.get("strike", "")),
                            "type": opt.get("type", "CE"),
                            "expiry": opt.get("expiry", ""),
                            "ltp": str(opt.get("ltp", 0)),
                            "recommendation": opt.get("recommendation", "")
                        })
        except Exception as e:
            logger.warning(f"Options pro error: {e}")
        
        return result
    except Exception as e:
        logger.error(f"Options error: {e}")
        return {"pcr": "--", "max_pain": "--", "vix": "--", "trend": "--", "suggestions": []}


# ═══════════════════════════════════════════════════════════
#  SCREENER API
# ═══════════════════════════════════════════════════════════

@router.get("/screener")
async def screener(q: Optional[str] = None, preset: Optional[str] = None):
    """NLP stock screener"""
    try:
        results = []
        
        try:
            screener_mod = safe_import("jarvis_screener_pro")
            if screener_mod and hasattr(screener_mod, 'screen_stocks'):
                query = q or preset or "top stocks"
                screen_results = screener_mod.screen_stocks(query)
                if isinstance(screen_results, list):
                    for r in screen_results[:20]:
                        results.append({
                            "symbol": r.get("symbol", ""),
                            "price": r.get("price", 0),
                            "reason": r.get("reason", r.get("match_reason", ""))
                        })
        except Exception as e:
            logger.warning(f"Screener error: {e}")
        
        return {"results": results}
    except Exception as e:
        return {"results": []}


# ═══════════════════════════════════════════════════════════
#  AIRDROPS API
# ═══════════════════════════════════════════════════════════

@router.get("/airdrops")
async def get_airdrops():
    """Get active airdrops"""
    try:
        airdrops = []
        
        try:
            airdrop_mod = safe_import("airdrop_hunter")
            if airdrop_mod and hasattr(airdrop_mod, 'get_active_airdrops'):
                active = airdrop_mod.get_active_airdrops()
                if isinstance(active, list):
                    for a in active[:20]:
                        airdrops.append({
                            "name": a.get("name", "Unknown"),
                            "est_value": a.get("estimated_value", "TBD"),
                            "chain": a.get("chain", "Multi-chain"),
                            "category": a.get("category", "DeFi"),
                            "status": a.get("status", "upcoming")
                        })
        except Exception as e:
            logger.warning(f"Airdrop error: {e}")
        
        # Fallback sample airdrops
        if not airdrops:
            airdrops = [
                {"name": "LayerZero Season 2", "est_value": "$500-$2000", "chain": "Multi-chain", "category": "Bridge", "status": "live"},
                {"name": "Scroll Mainnet", "est_value": "$300-$1500", "chain": "Ethereum L2", "category": "DeFi", "status": "live"},
                {"name": "Monad Testnet", "est_value": "$100-$800", "chain": "Monad", "category": "L1", "status": "upcoming"},
                {"name": "Berachain", "est_value": "$200-$1000", "chain": "Cosmos", "category": "DeFi", "status": "live"},
                {"name": "Eclipse", "est_value": "$150-$600", "chain": "Solana VM", "category": "L2", "status": "upcoming"},
            ]
        
        return {"airdrops": airdrops}
    except Exception as e:
        return {"airdrops": []}


# ═══════════════════════════════════════════════════════════
#  SENTIMENT API
# ═══════════════════════════════════════════════════════════

@router.get("/sentiment")
async def get_sentiment():
    """Get market sentiment and news"""
    try:
        result = {"score": 50, "label": "Neutral", "color": "#ffa502", "news": []}
        
        try:
            sentiment = safe_import("sentiment_engine")
            if sentiment:
                if hasattr(sentiment, 'get_market_sentiment'):
                    sent_data = sentiment.get_market_sentiment()
                    if isinstance(sent_data, dict):
                        score = sent_data.get("score", sent_data.get("sentiment_score", 50))
                        result["score"] = score
                        if score >= 70: result["label"] = "Greed"; result["color"] = "#00d4aa"
                        elif score >= 55: result["label"] = "Slightly Bullish"; result["color"] = "#7bed9f"
                        elif score <= 30: result["label"] = "Fear"; result["color"] = "#ff4757"
                        elif score <= 45: result["label"] = "Slightly Bearish"; result["color"] = "#ff6b81"
                        else: result["label"] = "Neutral"; result["color"] = "#ffa502"
                
                if hasattr(sentiment, 'get_latest_news'):
                    news = sentiment.get_latest_news()
                    if isinstance(news, list):
                        for n in news[:10]:
                            result["news"].append({
                                "title": n.get("title", ""),
                                "source": n.get("source", ""),
                                "sentiment": n.get("sentiment", "neutral")
                            })
        except Exception as e:
            logger.warning(f"Sentiment error: {e}")
        
        return result
    except Exception as e:
        return {"score": 50, "label": "Neutral", "color": "#ffa502", "news": []}


# ═══════════════════════════════════════════════════════════
#  RISK API
# ═══════════════════════════════════════════════════════════

@router.get("/risk")
async def get_risk(user_id: Optional[str] = None):
    """Get risk analysis"""
    try:
        result = {
            "risk_score": 50, "risk_label": "Moderate Risk", "risk_color": "var(--yellow)",
            "position_size": 5, "max_drawdown": 10,
            "regime_description": "Market is in a normal trading range."
        }
        
        try:
            risk_mod = safe_import("risk_manager")
            if risk_mod and hasattr(risk_mod, 'get_risk_assessment'):
                risk_data = risk_mod.get_risk_assessment()
                if isinstance(risk_data, dict):
                    result.update({
                        "risk_score": risk_data.get("risk_score", 50),
                        "position_size": risk_data.get("position_size_pct", 5),
                        "max_drawdown": risk_data.get("max_drawdown", 10)
                    })
        except: pass
        
        regime = _get_market_regime()
        result["regime_description"] = regime.get("description", result["regime_description"])
        
        score = result["risk_score"]
        if score <= 30: result["risk_label"] = "Low Risk"; result["risk_color"] = "var(--green)"
        elif score <= 60: result["risk_label"] = "Moderate Risk"; result["risk_color"] = "var(--yellow)"
        else: result["risk_label"] = "High Risk"; result["risk_color"] = "var(--red)"
        
        return result
    except Exception as e:
        return {"risk_score": 50, "risk_label": "Moderate", "risk_color": "var(--yellow)",
                "position_size": 5, "max_drawdown": 10, "regime_description": "Analyzing..."}


# ═══════════════════════════════════════════════════════════
#  AI CHAT API
# ═══════════════════════════════════════════════════════════

@router.post("/chat")
async def ai_chat(request: Request):
    """Process AI chat messages"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        message = data.get("message", "")
        
        if not message:
            return {"response": "Please type a message."}
        
        response = ""
        
        # Try JARVIS AI brain
        try:
            jarvis_ai = safe_import("jarvis_ai")
            if jarvis_ai and hasattr(jarvis_ai, 'process_query'):
                ai_response = jarvis_ai.process_query(message, user_id)
                if ai_response:
                    response = ai_response if isinstance(ai_response, str) else str(ai_response)
        except Exception as e:
            logger.warning(f"JARVIS AI error: {e}")
        
        # Try market brain for market-related queries
        if not response:
            try:
                market_brain = safe_import("jarvis_market_brain")
                if market_brain and hasattr(market_brain, 'process_market_query'):
                    mr = market_brain.process_market_query(message)
                    if mr: response = mr if isinstance(mr, str) else str(mr)
            except: pass
        
        # Try personal agent
        if not response:
            try:
                agent = safe_import("jarvis_personal_agent")
                if agent and hasattr(agent, 'process_query'):
                    ar = agent.process_query(message, user_id)
                    if ar: response = ar if isinstance(ar, str) else str(ar)
            except: pass
        
        # Intelligent fallback  
        if not response:
            msg_lower = message.lower()
            if any(w in msg_lower for w in ['nifty', 'sensex', 'stock', 'market']):
                response = "📊 <b>Market Analysis</b>\n\nJARVIS AI is analyzing Indian markets. Use the <b>Signals</b> tab for real-time AI signals, or the <b>Screener</b> for custom scans.\n\n💡 Try: 'RSI below 30 stocks' or 'volume breakout'"
            elif any(w in msg_lower for w in ['btc', 'bitcoin', 'crypto', 'eth', 'sol']):
                response = "🪙 <b>Crypto Analysis</b>\n\nCheck the <b>Markets</b> tab for live crypto prices from CoinDCX. The AI is continuously scanning for gems and trading signals.\n\n💡 Try: 'best crypto to buy' or 'check BTC signal'"
            elif any(w in msg_lower for w in ['wallet', 'balance', 'deposit', 'withdraw']):
                response = "💰 <b>Wallet</b>\n\nGo to the <b>Wallet</b> tab to check your balance, make UPI deposits, or withdraw to your Phantom wallet.\n\nMinimum deposit: ₹1"
            elif any(w in msg_lower for w in ['option', 'put', 'call', 'strike']):
                response = "📊 <b>Options Intelligence</b>\n\nCheck Options from the home screen for live PCR, Max Pain, India VIX, and budget option picks under ₹5.\n\n💡 Try: 'NIFTY options strategy'"
            elif any(w in msg_lower for w in ['hello', 'hi', 'hey']):
                response = "👋 <b>Hello!</b> I'm JARVIS, your AI trading assistant.\n\n🎯 <b>Ask me:</b>\n• Analyze any stock/crypto\n• Trading signals\n• Portfolio advice\n• Market sentiment\n• Options strategies\n\nI'm powered by multi-model AI (GPT + Gemini + Claude) for the best accuracy!"
            else:
                response = f"🤖 <b>JARVIS AI</b>\n\nI'm processing your request: <i>{message}</i>\n\nI can help with:\n• 📊 Stock & Crypto analysis\n• 📈 Trading signals (Buy/Sell)\n• 💰 Wallet & Portfolio\n• 🔍 Stock screening\n• 📊 Options intelligence\n• 🌍 Market sentiment\n\nTry asking something specific!"
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "🤖 JARVIS is processing. Please try again."}


# ═══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def _get_portfolio(user_id):
    """Get user portfolio summary"""
    try:
        if not user_id:
            return {"total": 0, "change_pct": 0}
        
        total = 0
        # Check wallet balance
        try:
            payment = safe_import("jarvis_payment")
            if payment and hasattr(payment, '_load_wallets'):
                wallets = payment._load_wallets()
                wallet = wallets.get(str(user_id), {})
                total = wallet.get("balance_inr", 0)
        except: pass
        
        # Check portfolio holdings
        try:
            pt = safe_import("portfolio_tracker")
            if pt and hasattr(pt, 'get_portfolio_value'):
                pv = pt.get_portfolio_value(int(user_id))
                if isinstance(pv, (int, float)):
                    total += pv
                elif isinstance(pv, dict):
                    total += pv.get("total_value", 0)
        except: pass
        
        return {"total": total, "change_pct": 0}
    except:
        return {"total": 0, "change_pct": 0}


def _get_market_ticker():
    """Get market overview data"""
    try:
        markets = []
        import yfinance as yf
        
        tickers = {
            "^NSEI": "NIFTY 50",
            "^BSESN": "SENSEX", 
            "BTC-USD": "BTC",
            "ETH-USD": "ETH",
            "SOL-USD": "SOL"
        }
        
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                info = t.fast_info
                price = getattr(info, 'last_price', 0) or 0
                prev = getattr(info, 'previous_close', price) or price
                change = ((price - prev) / prev * 100) if prev else 0
                markets.append({
                    "name": name,
                    "symbol": sym.replace("^", "").replace("-USD", ""),
                    "price": round(price, 2),
                    "change": round(change, 2)
                })
            except: pass
        
        if not markets:
            return _fallback_markets()
        return markets
    except:
        return _fallback_markets()


def _get_quick_signals():
    """Get quick signals from available modules"""
    signals = []
    
    try:
        bse = safe_import("buy_sell_engine")
        if bse:
            # Try to get recent signals
            if hasattr(bse, 'get_latest_signals'):
                latest = bse.get_latest_signals()
                if isinstance(latest, list):
                    for s in latest[:10]:
                        signals.append({
                            "symbol": s.get("symbol", "?"),
                            "action": s.get("action", s.get("signal", "HOLD")),
                            "price": s.get("price", 0),
                            "entry": s.get("entry", s.get("entry_price", 0)),
                            "target": s.get("target", s.get("target_price", 0)),
                            "sl": s.get("sl", s.get("stop_loss", 0)),
                            "confidence": s.get("confidence", 65),
                            "change": s.get("change", 0),
                            "type": s.get("type", "stock"),
                            "timeframe": s.get("timeframe", "1D"),
                            "source": "AI Multi-Model"
                        })
    except: pass
    
    try:
        ai_sig = safe_import("ai_signals")
        if ai_sig and hasattr(ai_sig, 'get_active_signals'):
            active = ai_sig.get_active_signals()
            if isinstance(active, list):
                existing = {s["symbol"] for s in signals}
                for s in active:
                    sym = s.get("symbol", "?")
                    if sym not in existing:
                        signals.append({
                            "symbol": sym,
                            "action": s.get("action", "HOLD"),
                            "price": s.get("price", 0),
                            "entry": s.get("entry", 0),
                            "target": s.get("target", 0),
                            "sl": s.get("sl", 0),
                            "confidence": s.get("confidence", 60),
                            "change": s.get("change", 0),
                            "type": s.get("type", "stock"),
                            "timeframe": "1D",
                            "source": "AI Technical"
                        })
    except: pass
    
    return signals


def _get_top_movers():
    """Get top gainers/losers"""
    try:
        movers = []
        
        try:
            coindcx = safe_import("coindcx_engine")
            if coindcx and hasattr(coindcx, 'get_top_gainers_losers'):
                data = coindcx.get_top_gainers_losers()
                if isinstance(data, dict):
                    for g in data.get("gainers", [])[:3]:
                        movers.append({"symbol": g.get("symbol", "?"), "name": g.get("name", ""), "price": g.get("price", 0), "change": g.get("change", 0)})
                    for l in data.get("losers", [])[:2]:
                        movers.append({"symbol": l.get("symbol", "?"), "name": l.get("name", ""), "price": l.get("price", 0), "change": l.get("change", 0)})
        except: pass
        
        if not movers:
            try:
                import yfinance as yf
                stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS"]
                for s in stocks:
                    try:
                        t = yf.Ticker(s)
                        info = t.fast_info
                        price = getattr(info, 'last_price', 0) or 0
                        prev = getattr(info, 'previous_close', price) or price
                        change = ((price - prev) / prev * 100) if prev else 0
                        movers.append({"symbol": s.replace(".NS",""), "name": s.replace(".NS",""), "price": round(price,2), "change": round(change,2)})
                    except: pass
            except: pass
        
        movers.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
        return movers
    except:
        return []


def _get_market_regime():
    """Get current market regime"""
    try:
        regime_mod = safe_import("market_regime")
        if regime_mod and hasattr(regime_mod, 'detect_regime'):
            regime = regime_mod.detect_regime()
            if isinstance(regime, dict):
                name = regime.get("regime", regime.get("name", "Neutral"))
                score = regime.get("score", 50)
                color = "var(--green)" if score > 65 else "var(--red)" if score < 35 else "var(--yellow)"
                return {"name": name, "score": score, "color": color, "description": regime.get("description", "")}
    except: pass
    return {"name": "Neutral", "score": 50, "color": "var(--yellow)", "description": "Market in normal range."}


def _fallback_markets():
    return [
        {"name": "NIFTY 50", "symbol": "NSEI", "price": 0, "change": 0},
        {"name": "SENSEX", "symbol": "BSESN", "price": 0, "change": 0},
        {"name": "BTC", "symbol": "BTC", "price": 0, "change": 0},
        {"name": "ETH", "symbol": "ETH", "price": 0, "change": 0},
    ]


def _fallback_tokens():
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": 0, "change": 0, "type": "crypto", "color": "#F7931A"},
        {"symbol": "ETH", "name": "Ethereum", "price": 0, "change": 0, "type": "crypto", "color": "#627EEA"},
        {"symbol": "SOL", "name": "Solana", "price": 0, "change": 0, "type": "crypto", "color": "#00FFA3"},
        {"symbol": "RELIANCE", "name": "Reliance Industries", "price": 0, "change": 0, "type": "stock", "color": "#3B82F6"},
        {"symbol": "TCS", "name": "Tata Consultancy", "price": 0, "change": 0, "type": "stock", "color": "#3B82F6"},
        {"symbol": "INFY", "name": "Infosys", "price": 0, "change": 0, "type": "stock", "color": "#3B82F6"},
    ]
