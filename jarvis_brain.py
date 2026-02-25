"""
🧠 JARVIS Brain v5.0 — NUCLEAR POWER LEVEL AI Engine
═══════════════════════════════════════════════════════════════════
Multi-provider AI with:
  - Persistent memory (survives restarts, remembers everything)
  - Smart intent detection & auto-context enrichment
  - Position tracking from natural language
  - Fact extraction & user profiling
  - Prediction tracking & self-learning
  - Hindi/Hinglish native support
  - Multi-model streaming with fallback
"""

import os, json, logging, time, asyncio, re, hashlib, traceback
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, AsyncGenerator, Tuple
import httpx

logger = logging.getLogger("jarvis-brain")
IST = timezone(timedelta(hours=5, minutes=30))

def _safe_uid(user_id) -> int:
    """Safely convert user_id to int, return 0 on failure."""
    try:
        return int(user_id) if user_id and str(user_id) != "0" else 0
    except (ValueError, TypeError):
        return 0

# ═══════════════════════════════════════════════════════════
#  ENGINE IMPORTS — Real data from all trading engines
# ═══════════════════════════════════════════════════════════
def _safe_import(mod, names):
    """Safely import functions from a module."""
    out = {}
    try:
        m = __import__(mod)
        for n in names:
            out[n] = getattr(m, n, None)
    except Exception as e:
        logger.debug(f"Engine import {mod}: {e}")
        for n in names:
            out[n] = None
    return out

# Options + OI engines
_oi_engine = _safe_import("oi_trap_brain", ["get_options_super_signal", "fetch_option_chain", "detect_traps", "find_budget_plays", "format_trap_analysis"])
_options_eng = _safe_import("options_engine", ["recommend_strategy", "generate_option_chain", "format_option_chain", "format_recommendations", "calculate_iv_rank_percentile"])
_nifty_brain = _safe_import("nifty_super_brain", ["get_fii_dii_data", "get_india_vix", "get_pcr_data", "calculate_pivot_levels", "get_complete_dashboard", "get_super_brain_analysis", "get_oi_buildup"])
_hunter = _safe_import("nifty_options_hunter", ["find_budget_options"])
# Analysis + Prediction engines
_candle_eng = _safe_import("candle_analyzer", ["analyze_index", "multi_timeframe_pattern_scan"])
_ml_eng = _safe_import("ml_predictor", ["predict_index_direction", "predict_with_regime"])
_power_eng = _safe_import("india_power_predictor", ["power_predict", "format_power_prediction"])
_india_stock = _safe_import("indian_stock_super_engine", ["recommend_best_options", "indian_stock_super_analysis"])
# Market regime + signals
_regime_eng = _safe_import("market_regime", ["get_regime_quick", "detect_market_regime"])
_signal_eng = _safe_import("ai_signals", ["full_technical_analysis", "quick_signal"])
# News
_news_eng = _safe_import("jarvis_news_brain", ["get_latest_news", "get_news_sentiment_score"])

def _eng(store, name):
    """Get engine function safely."""
    fn = store.get(name)
    return fn if callable(fn) else None

logger.info("🔌 Brain engine connections: OI=%s Options=%s Nifty=%s Candle=%s ML=%s Power=%s",
    bool(_oi_engine.get("get_options_super_signal")), bool(_options_eng.get("recommend_strategy")),
    bool(_nifty_brain.get("get_pcr_data")), bool(_candle_eng.get("analyze_index")),
    bool(_ml_eng.get("predict_index_direction")), bool(_power_eng.get("power_predict")))

# ═══════════════════════════════════════════════════════════
#  CONFIG — Keys are read dynamically so .env changes take effect
# ═══════════════════════════════════════════════════════════
def _get_key(name):
    """Get API key dynamically from environment."""
    return os.getenv(name, "")

GROQ_KEY = _get_key("GROQ_API_KEY")
OPENAI_KEY = _get_key("OPENAI_API_KEY")
ANTHROPIC_KEY = _get_key("ANTHROPIC_API_KEY")
GEMINI_KEY = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")

# ═══════════════════════════════════════════════════════════
#  PERSISTENT MEMORY INTEGRATION
# ═══════════════════════════════════════════════════════════
try:
    import jarvis_memory_pro as _mem_pro
    _MEM_PRO = True
    logger.info("🧠 Memory Pro connected — persistent intelligence active")
except Exception as e:
    _MEM_PRO = False
    logger.warning(f"Memory Pro not available: {e}")

# Volatile fallback (only used if memory_pro unavailable)
_memory: Dict[str, List[Dict]] = {}
_MAX_MEMORY = 50

def _get_memory(user_id: str) -> List[Dict]:
    """Get conversation memory — persistent or volatile."""
    if _MEM_PRO:
        try:
            history = _mem_pro.get_conversation_history(_safe_uid(user_id), last_n=30)
            return [{"role": m.get("role", "user"), "content": m.get("text", "")} for m in history if m.get("text")]
        except:
            pass
    return _memory.get(user_id, [])

def _add_memory(user_id: str, role: str, content: str):
    """Add message to memory — persistent or volatile."""
    if _MEM_PRO:
        try:
            intent = _detect_intent(content) if role == "user" else ""
            _mem_pro.remember_message(_safe_uid(user_id), role, content, intent)
            if role == "user":
                _auto_extract_facts(_safe_uid(user_id), content)
                _auto_track_position(_safe_uid(user_id), content)
            return
        except Exception as e:
            logger.warning(f"Memory Pro save error: {e}")
    if user_id not in _memory:
        _memory[user_id] = []
    _memory[user_id].append({"role": role, "content": content})
    if len(_memory[user_id]) > _MAX_MEMORY:
        _memory[user_id] = _memory[user_id][-_MAX_MEMORY:]

def clear_memory(user_id: str):
    """Clear conversation memory."""
    _memory.pop(user_id, None)

# ═══════════════════════════════════════════════════════════
#  SMART INTENT DETECTION
# ═══════════════════════════════════════════════════════════
_INTENT_PATTERNS = {
    "price_check": r"(?:price|kya\s*(?:price|rate)|kitna|kitne|current|live|abhi)\s*(?:hai|h|he)?",
    "prediction": r"(?:predict|prediction|forecast|kal|tomorrow|next\s*week|agle|bhavishya|target)",
    "signal": r"(?:signal|buy|sell|entry|exit|kharido|becho|lena|dena|long|short)",
    "analysis": r"(?:analy[sz]|technical|fundamental|chart|pattern|support|resistance|trend)",
    "options": r"(?:option|call|put|strike|expiry|oi|open\s*interest|straddle|strangle|iv|pcr)",
    "nifty": r"(?:nifty|bank\s*nifty|banknifty|sensex|index|indices|fin\s*nifty)",
    "crypto": r"(?:bitcoin|btc|eth|ethereum|sol|solana|crypto|token|coin|dex|pump\.?fun)",
    "airdrop": r"(?:airdrop|free\s*token|claim|drop|faucet)",
    "news": r"(?:news|khabar|latest|breaking|update|headlines)",
    "portfolio": r"(?:portfolio|holding|position|meri|my\s*position|wallet|balance)",
    "risk": r"(?:risk|stop\s*loss|sl|target|tp|position\s*size|capital|money\s*management)",
    "code": r"(?:code|github|program|script|banao|build|develop|clone|install|run\s*kar)",
    "greeting": r"(?:^(?:hi|hello|hey|namaste|kya\s*hal|kaise\s*ho|good\s*morning|gm))",
    "memory": r"(?:yaad|remember|memory|history|fact|mujhe\s*pata|mera\s*naam|position\s*batao)",
}

def _detect_intent(text: str) -> str:
    """Detect the primary intent of a message."""
    lower = text.lower().strip()
    scores = {}
    for intent, pattern in _INTENT_PATTERNS.items():
        matches = re.findall(pattern, lower)
        if matches:
            scores[intent] = len(matches)
    if not scores:
        return "general"
    return max(scores, key=scores.get)

def _detect_language(text: str) -> str:
    """Detect if text is Hindi, English, or Hinglish."""
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    hindi_words = len(re.findall(r'\b(?:kya|hai|ho|ka|ki|ke|mein|se|ko|ne|par|pe|bhai|yaar|aur|bhi|nahi|mat|haan|ji|bol|bata|de|le|kar|karo|kaise|kahan|kab|kyun|accha|theek|dekh|sun|chal|abhi)\b', text.lower()))
    english_words = len(re.findall(r'\b(?:the|is|are|was|were|have|has|what|how|when|where|why|can|will|should|would|could|please|help|show|give|tell)\b', text.lower()))
    if hindi_chars > 3:
        return "hindi"
    elif hindi_words > english_words:
        return "hinglish"
    elif hindi_words > 0 and english_words > 0:
        return "hinglish"
    return "english"

# ═══════════════════════════════════════════════════════════
#  AUTO FACT EXTRACTION — Learn from user messages
# ═══════════════════════════════════════════════════════════
def _auto_extract_facts(user_id: int, text: str):
    """Extract and store facts from user messages."""
    if not _MEM_PRO:
        return
    lower = text.lower()
    try:
        name_match = re.search(r'(?:mera\s*naam|my\s*name\s*is|i\s*am|main\s*hoon|i\'m)\s+([A-Za-z\u0900-\u097F]+)', lower)
        if name_match:
            _mem_pro.remember_fact(user_id, "name", name_match.group(1).title())
        budget_match = re.search(r'(?:budget|capital|paisa|paise|amount|invest)\s*(?:hai|is|:)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*)', lower)
        if budget_match:
            _mem_pro.remember_fact(user_id, "budget", budget_match.group(1).replace(",", ""))
        if any(w in lower for w in ["aggressive", "high risk", "zyada risk", "risk le sakta"]):
            _mem_pro.remember_fact(user_id, "risk_appetite", "aggressive")
        elif any(w in lower for w in ["safe", "low risk", "kam risk", "conservative"]):
            _mem_pro.remember_fact(user_id, "risk_appetite", "conservative")
        if any(w in lower for w in ["scalping", "scalp", "1 minute", "quick trade"]):
            _mem_pro.remember_fact(user_id, "trading_style", "scalper")
        elif any(w in lower for w in ["intraday", "day trade", "aaj", "today"]):
            _mem_pro.remember_fact(user_id, "trading_style", "intraday")
        elif any(w in lower for w in ["swing", "2-3 din", "few days", "positional"]):
            _mem_pro.remember_fact(user_id, "trading_style", "swing")
        elif any(w in lower for w in ["long term", "invest", "lambe samay", "hold"]):
            _mem_pro.remember_fact(user_id, "trading_style", "investor")
        symbols = re.findall(r'\b(NIFTY|BANKNIFTY|SENSEX|BTC|ETH|SOL|RELIANCE|TCS|INFY|HDFC|TATA|ADANI)\b', text.upper())
        if symbols:
            existing = _mem_pro.recall_fact(user_id, "favorite_symbols") or []
            if isinstance(existing, str):
                existing = existing.split(",")
            for s in symbols:
                if s not in existing:
                    existing.append(s)
            _mem_pro.remember_fact(user_id, "favorite_symbols", list(set(existing))[-20:])
    except Exception as e:
        logger.debug(f"Fact extraction error: {e}")

# ═══════════════════════════════════════════════════════════
#  AUTO POSITION TRACKING
# ═══════════════════════════════════════════════════════════
def _auto_track_position(user_id: int, text: str):
    """Auto-detect and track positions from natural language."""
    if not _MEM_PRO:
        return
    try:
        parsed = _mem_pro.parse_position_from_text(text)
        if parsed:
            if parsed["action"] == "BUY":
                _mem_pro.add_position(user_id, parsed["symbol"], parsed["strike"],
                    parsed["option_type"], parsed.get("price", 0),
                    notes=parsed.get("raw_text", "")[:200])
                logger.info(f"Auto-tracked BUY: {parsed['symbol']} {parsed['strike']} {parsed['option_type']} for user {user_id}")
            elif parsed["action"] == "SELL":
                _mem_pro.close_position(user_id, symbol=parsed["symbol"],
                    strike=parsed["strike"], exit_price=parsed.get("price", 0))
                logger.info(f"Auto-tracked SELL: {parsed['symbol']} {parsed['strike']} for user {user_id}")
    except Exception as e:
        logger.debug(f"Position tracking error: {e}")

# ═══════════════════════════════════════════════════════════
#  🔥 SMART CONTEXT ENGINE — Fetches REAL data from ALL engines
# ═══════════════════════════════════════════════════════════
_NIFTY_OPTIONS_REGEX = re.compile(
    r'(?:nifty|banknifty|bank\s*nifty|sensex)\s*(?:.*?)(?:call|put|ce|pe|option|strike|expiry|oi|pcr|straddle|strangle|iron\s*condor|max\s*pain|chain|premium)',
    re.IGNORECASE
)
_CALL_PUT_REGEX = re.compile(
    r'(?:call\s*lu|put\s*lu|call\s*leni|put\s*leni|call\s*buy|put\s*buy|call\s*ya\s*put|put\s*ya\s*call|call\s*kharid|put\s*kharid|call\s*le|put\s*le|call\s*lena|put\s*lena|kya\s*lu|konsa\s*option|kaun\s*sa\s*option|option\s*suggest|option\s*recommend|best\s*option|sasta\s*option|budget\s*option|cheap\s*option)',
    re.IGNORECASE
)
_INDEX_ANALYSIS_REGEX = re.compile(
    r'(?:nifty|sensex|banknifty|bank\s*nifty)\s*(?:.*?)(?:analysis|prediction|predict|signal|kya\s*hoga|kal|tomorrow|trend|level|support|resistance|target|upar|neeche|bullish|bearish|up\s*ya\s*down|upar\s*jayega|niche\s*jayega|kahan\s*jayega|direction|move)',
    re.IGNORECASE
)
_OPTIONS_GENERAL_REGEX = re.compile(
    r'\b(?:call|put|ce\b|pe\b|option|strike|expiry|oi\b|open\s*interest|pcr|iv\b|implied\s*vol|straddle|strangle|iron\s*condor|max\s*pain|greeks|delta|gamma|theta|vega|option\s*chain)',
    re.IGNORECASE
)
_INDEX_REGEX = re.compile(r'\b(nifty|banknifty|bank\s*nifty|sensex)\b', re.IGNORECASE)

def _detect_index(text: str) -> str:
    """Detect which index user is asking about."""
    lower = text.lower()
    if 'banknifty' in lower or 'bank nifty' in lower:
        return "BANKNIFTY"
    elif 'sensex' in lower:
        return "SENSEX"
    return "NIFTY"  # Default

_INDEX_SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
}

def _build_smart_context(message: str, user_id: str = "0") -> str:
    """
    🔥 SMART CONTEXT ENGINE — The brain's real intelligence.
    Detects what user is asking and fetches REAL data from all engines.
    Returns enriched context string to inject into AI prompt.
    """
    lower = message.lower().strip()
    context_parts = []
    index = _detect_index(message)
    symbol = _INDEX_SYMBOL_MAP.get(index, "^NSEI")

    needs_options = bool(_NIFTY_OPTIONS_REGEX.search(lower) or _CALL_PUT_REGEX.search(lower) or _OPTIONS_GENERAL_REGEX.search(lower))
    needs_analysis = bool(_INDEX_ANALYSIS_REGEX.search(lower))
    needs_index = bool(_INDEX_REGEX.search(lower))

    # If user asks about call/put or options → FULL options intelligence
    if needs_options or needs_analysis or needs_index:
        logger.info(f"🔌 Smart Context: index={index}, options={needs_options}, analysis={needs_analysis}")

        # 1. OI + Trap Analysis + Super Signal (MOST IMPORTANT for call/put)
        if needs_options or _CALL_PUT_REGEX.search(lower):
            fn = _eng(_oi_engine, "get_options_super_signal")
            if fn:
                try:
                    sig = fn(index)
                    if sig and "error" not in sig:
                        ctx = f"\n═══ {index} OPTIONS SUPER SIGNAL (REAL OI DATA) ═══\n"
                        ctx += f"Spot: ₹{sig.get('spot', 0):,.2f}\n"
                        ctx += f"VERDICT: {sig.get('verdict', 'N/A')}\n"
                        ctx += f"Confidence: {sig.get('confidence', 0)}%\n"
                        ctx += f"Bullish Score: {sig.get('bullish_score', 0)} | Bearish Score: {sig.get('bearish_score', 0)}\n"
                        ctx += f"PCR: {sig.get('pcr', 0):.3f}\n"
                        ctx += f"Max Pain: ₹{sig.get('max_pain', 0):,.0f}\n"
                        ctx += f"Straddle Premium: ₹{sig.get('straddle', 0):,.0f}\n"
                        er = sig.get('expected_range', (0, 0))
                        ctx += f"Expected Range: ₹{er[0]:,.0f} – ₹{er[1]:,.0f}\n"
                        ctx += f"Support: ₹{sig.get('support', 0):,.0f} | Resistance: ₹{sig.get('resistance', 0):,.0f}\n"
                        ctx += f"DTE (Days to Expiry): {sig.get('dte', 0)}\n"
                        ctx += f"VIX: {sig.get('vix', 0):.1f}\n"
                        # Signals
                        for s in sig.get('signals', []):
                            ctx += f"  → {s}\n"
                        # Traps
                        for trap in sig.get('traps', [])[:3]:
                            ctx += f"  🪤 TRAP: {trap.get('type','')}: {trap.get('detail','')} → {trap.get('action','')}\n"
                        # Best play
                        bp = sig.get('best_play')
                        if bp and bp.get('price', 0) > 0.5:
                            ctx += f"\n💰 BEST BUDGET PLAY: {bp.get('type','')}\n"
                            ctx += f"  Strike: {bp.get('strike', 0):,} | Premium: ₹{bp.get('price', 0):.1f}\n"
                            ctx += f"  Lot Cost: ₹{bp.get('lot_cost', 0):,.0f}\n"
                            ctx += f"  Delta: {bp.get('delta', 0):.3f} | OI: {bp.get('oi', 0):,}\n"
                        # Top plays (only with real premiums)
                        plays = [p for p in sig.get('top_plays', []) if p.get('price', 0) > 0.5][:3]
                        if plays:
                            ctx += "\n📊 TOP 3 BUDGET PLAYS:\n"
                            for i, p in enumerate(plays, 1):
                                ctx += f"  {i}. {p.get('type','')} {p.get('strike',0):,} → ₹{p.get('price',0):.1f} (Lot: ₹{p.get('lot_cost',0):,.0f}, Delta: {p.get('delta',0):.3f}, OI: {p.get('oi',0):,})\n"
                        context_parts.append(ctx)
                        logger.info(f"✅ OI Super Signal loaded for {index}")
                except Exception as e:
                    logger.warning(f"OI Signal error: {e}")

        # 2. Budget Options Hunter (for ₹4-5 option recommendations)
        if _CALL_PUT_REGEX.search(lower):
            fn = _eng(_hunter, "find_budget_options")
            if fn:
                try:
                    opts = fn(index)
                    if opts and "error" not in opts:
                        ctx = f"\n═══ ⭐ {index} BEST OPTIONS TO BUY NOW (BLACK-SCHOLES PRICED) ═══\n"
                        ctx += f"[USE THESE EXACT PRICES WHEN RECOMMENDING OPTIONS TO USER]\n"
                        ctx += f"Spot: ₹{opts.get('spot', 0):,.1f}\n"
                        ctx += f"Direction: {opts.get('direction', 'AUTO')}\n"
                        ctx += f"ML Direction: {opts.get('ml_direction', 'N/A')} (Conf: {opts.get('ml_confidence', 0):.1f}%)\n"
                        ctx += f"Tech Signal: {opts.get('tech_signal', 'N/A')}\n"
                        ctx += f"Historical Volatility: {opts.get('historical_volatility', 0)*100:.1f}%\n"
                        calls = opts.get("calls", [])[:5]
                        puts = opts.get("puts", [])[:5]
                        if calls:
                            ctx += "\n🟢 BEST CALL OPTIONS (for BULLISH view):\n"
                            for i, c in enumerate(calls, 1):
                                ctx += f"  {i}. CE {c['strike']:,} → Premium ₹{c['premium']:.1f} | Lot Cost ₹{c.get('lot_cost',0):,.0f} | Delta {c['delta']:.3f}\n"
                                ctx += f"     OTM: {c.get('otm_pct',0):.1f}% | If NIFTY +2%: ₹{c.get('if_2pct_up',0):.1f} | +3%: ₹{c.get('if_3pct_up',0):.1f} ({c.get('potential_return_3pct',0):.0f}% return) | +5%: ₹{c.get('if_5pct_up',0):.1f} ({c.get('potential_return_5pct',0):.0f}% return)\n"
                                ctx += f"     Theta: ₹{c.get('theta',0):.2f}/day | Score: {c.get('score',0):.1f}\n"
                        if puts:
                            ctx += "\n🔴 BEST PUT OPTIONS (for BEARISH view):\n"
                            for i, p in enumerate(puts, 1):
                                ctx += f"  {i}. PE {p['strike']:,} → Premium ₹{p['premium']:.1f} | Lot Cost ₹{p.get('lot_cost',0):,.0f} | Delta {p['delta']:.3f}\n"
                                ctx += f"     OTM: {p.get('otm_pct',0):.1f}% | If NIFTY -2%: ₹{p.get('if_2pct_up', p.get('if_2pct_down',0)):.1f} | -3%: ₹{p.get('if_3pct_up', p.get('if_3pct_down',0)):.1f} ({p.get('potential_return_3pct',0):.0f}% return) | -5%: ₹{p.get('if_5pct_up', p.get('if_5pct_down',0)):.1f} ({p.get('potential_return_5pct',0):.0f}% return)\n"
                                ctx += f"     Theta: ₹{p.get('theta',0):.2f}/day | Score: {p.get('score',0):.1f}\n"
                        context_parts.append(ctx)
                        logger.info(f"✅ Budget options loaded for {index}")
                except Exception as e:
                    logger.warning(f"Budget options error: {e}")

        # 3. Options Strategy Recommendation
        if needs_options:
            fn = _eng(_options_eng, "recommend_strategy")
            if fn:
                try:
                    reco = fn(index)
                    if reco:
                        ctx = f"\n═══ {index} OPTIONS STRATEGY RECOMMENDATION ═══\n"
                        ctx += f"Market Regime: {reco.get('regime', 'N/A')}\n"
                        ctx += f"IV Rank: {reco.get('iv_rank', 0):.1f}\n"
                        iv = reco.get('iv_data', {})
                        ctx += f"IV: {iv.get('current_iv',0):.1f}% | IV Percentile: {iv.get('iv_percentile',0):.0f}%\n"
                        for sname, strat, reason_en, reason_hi in reco.get('strategies', []):
                            ctx += f"\n🎯 Strategy: {sname}\n"
                            ctx += f"  Reason: {reason_hi}\n"
                            try:
                                legs = strat.legs if hasattr(strat, 'legs') else strat.get('legs', []) if isinstance(strat, dict) else []
                                for leg in legs:
                                    ot = leg.option_type if hasattr(leg, 'option_type') else leg.get('option_type', '?')
                                    st = leg.strike if hasattr(leg, 'strike') else leg.get('strike', 0)
                                    pr = leg.premium if hasattr(leg, 'premium') else leg.get('premium', 0)
                                    qt = leg.quantity if hasattr(leg, 'quantity') else leg.get('quantity', 0)
                                    ctx += f"  Leg: {ot} {st:,} @ ₹{pr:.1f} (Qty: {qt})\n"
                                mp = strat.max_profit if hasattr(strat, 'max_profit') else strat.get('max_profit', 0) if isinstance(strat, dict) else 0
                                ml = strat.max_loss if hasattr(strat, 'max_loss') else strat.get('max_loss', 0) if isinstance(strat, dict) else 0
                                be = strat.breakeven if hasattr(strat, 'breakeven') else strat.get('breakeven', '') if isinstance(strat, dict) else ''
                                ctx += f"  Max Profit: ₹{mp:,.0f} | Max Loss: ₹{ml:,.0f}\n"
                                ctx += f"  Breakeven: {be}\n"
                            except Exception:
                                pass
                        context_parts.append(ctx)
                        logger.info(f"✅ Strategy recommendation loaded for {index}")
                except Exception as e:
                    logger.warning(f"Strategy reco error: {e}")

        # 4. Power Prediction (10+ signals combined)
        fn = _eng(_power_eng, "power_predict")
        if fn:
            try:
                pred = fn(index)
                if pred and "error" not in pred:
                    ctx = f"\n═══ {index} POWER PREDICTION (10+ SIGNALS) ═══\n"
                    ctx += f"Spot: ₹{pred.get('spot', 0):,.1f}\n"
                    ctx += f"Direction: {pred.get('direction', 'N/A')}\n"
                    ctx += f"Confidence: {pred.get('confidence', 0):.0f}%\n"
                    ctx += f"Bull Score: {pred.get('bull_score', 0):.0f}/100 | Bear Score: {pred.get('bear_score', 0):.0f}/100\n"
                    ctx += f"Signals: {pred.get('bullish_count',0)} Bullish | {pred.get('bearish_count',0)} Bearish | {pred.get('neutral_count',0)} Neutral\n"
                    if pred.get('entry'):
                        ctx += f"Entry: ₹{pred['entry']:,.1f} | SL: ₹{pred.get('stop_loss',0):,.1f}\n"
                        for t in ['target_1', 'target_2', 'target_3']:
                            if pred.get(t):
                                ctx += f"  {t.upper()}: ₹{pred[t]:,.1f}\n"
                    # Signal breakdown
                    for name, sig in pred.get('signals', {}).items():
                        d = sig.get('direction', 'NEUTRAL')
                        c = sig.get('confidence', 50)
                        det = sig.get('detail', '')
                        emoji = "🟢" if "BULL" in d else "🔴" if "BEAR" in d else "⚪"
                        ctx += f"  {emoji} {name}: {d} ({c:.0f}%) {det}\n"
                    context_parts.append(ctx)
                    logger.info(f"✅ Power prediction loaded for {index}")
            except Exception as e:
                logger.warning(f"Power prediction error: {e}")

        # 5. Candle Pattern Analysis
        fn = _eng(_candle_eng, "analyze_index")
        if fn:
            try:
                analysis = fn(symbol, index)
                if analysis and analysis.get('signal'):
                    ctx = f"\n═══ {index} CANDLE & TECHNICAL ANALYSIS ═══\n"
                    ctx += f"Signal: {analysis.get('signal', 'HOLD')} | Confidence: {analysis.get('confidence', 0):.1f}\n"
                    ind = analysis.get('indicators', {})
                    ctx += f"RSI(14): {ind.get('rsi_14', 0):.1f} | RSI(7): {ind.get('rsi_7', 0):.1f}\n"
                    ctx += f"MACD: {ind.get('macd', 0):.2f} | Signal: {ind.get('macd_signal', 0):.2f}\n"
                    if ind.get('bb_upper'):
                        ctx += f"Bollinger: Lower ₹{ind.get('bb_lower',0):,.0f} | Mid ₹{ind.get('bb_mid',0):,.0f} | Upper ₹{ind.get('bb_upper',0):,.0f}\n"
                    ctx += f"SMA20: ₹{ind.get('sma_20',0):,.0f} | SMA50: ₹{ind.get('sma_50',0):,.0f} | SMA200: ₹{ind.get('sma_200',0):,.0f}\n"
                    ctx += f"ATR: {ind.get('atr', 0):.1f}\n"
                    # Support/Resistance
                    if analysis.get('support_levels'):
                        ctx += f"Supports: {', '.join([f'₹{s:,.0f}' for s in analysis['support_levels'][:3]])}\n"
                    if analysis.get('resistance_levels'):
                        ctx += f"Resistances: {', '.join([f'₹{r:,.0f}' for r in analysis['resistance_levels'][:3]])}\n"
                    if analysis.get('entry'):
                        ctx += f"Entry: ₹{analysis['entry']:,.1f} | SL: ₹{analysis['stop_loss']:,.1f}\n"
                        ctx += f"Targets: ₹{analysis.get('target_1',0):,.1f} / ₹{analysis.get('target_2',0):,.1f} / ₹{analysis.get('target_3',0):,.1f}\n"
                    # Recent patterns
                    for pname, pdata in list(analysis.get('patterns', {}).items())[:5]:
                        ctx += f"  🕯️ Pattern: {pname} ({pdata.get('type','')}, strength={pdata.get('strength','')}, reliability={pdata.get('reliability','')})\n"
                    # Reasons
                    for r in analysis.get('reasons', [])[:8]:
                        ctx += f"  → {r}\n"
                    context_parts.append(ctx)
                    logger.info(f"✅ Candle analysis loaded for {index}")
            except Exception as e:
                logger.warning(f"Candle analysis error: {e}")

        # 6. ML Prediction
        fn = _eng(_ml_eng, "predict_index_direction")
        if fn:
            try:
                ml_pred = fn(symbol, index)
                if ml_pred and "error" not in ml_pred:
                    ctx = f"\n═══ {index} ML PREDICTION (6-Model Ensemble) ═══\n"
                    ctx += f"Price: ₹{ml_pred.get('price', 0):,.1f}\n"
                    ctx += f"Direction: {ml_pred.get('direction', 'N/A')}\n"
                    ctx += f"Confidence: {ml_pred.get('confidence', 0):.1f}%\n"
                    ctx += f"Probability UP: {ml_pred.get('prob_up', 0):.1f}% | DOWN: {ml_pred.get('prob_down', 0):.1f}%\n"
                    if ml_pred.get('models'):
                        ctx += "Models: "
                        for m, v in ml_pred.get('models', {}).items():
                            ctx += f"{m}={v.get('signal','?')}({v.get('confidence',0):.0f}%) "
                        ctx += "\n"
                    context_parts.append(ctx)
                    logger.info(f"✅ ML prediction loaded for {index}")
            except Exception as e:
                logger.warning(f"ML prediction error: {e}")

        # 7. FII/DII Data
        fn = _eng(_nifty_brain, "get_fii_dii_data")
        if fn:
            try:
                fii = fn()
                if fii:
                    ctx = f"\n═══ FII/DII FLOW DATA ═══\n"
                    ctx += f"FII Net: ₹{fii.get('fii_net', 0):,.0f} Cr ({fii.get('signal', 'N/A')})\n"
                    ctx += f"DII Net: ₹{fii.get('dii_net', 0):,.0f} Cr\n"
                    context_parts.append(ctx)
            except Exception as e:
                logger.debug(f"FII data error: {e}")

        # 8. India VIX
        fn = _eng(_nifty_brain, "get_india_vix")
        if fn:
            try:
                vix = fn()
                if vix:
                    ctx = f"\n═══ INDIA VIX ═══\n"
                    ctx += f"VIX: {vix.get('vix', 0):.2f} ({vix.get('regime', 'N/A')})\n"
                    ctx += f"Change: {vix.get('change_pct', 0):+.1f}%\n"
                    context_parts.append(ctx)
            except Exception as e:
                logger.debug(f"VIX error: {e}")

        # 9. PCR Data
        fn = _eng(_nifty_brain, "get_pcr_data")
        if fn:
            try:
                pcr = fn(index)
                if pcr:
                    ctx = f"\n═══ {index} PCR DASHBOARD ═══\n"
                    ctx += f"PCR: {pcr.get('pcr_oi', 0):.3f} | PCR Volume: {pcr.get('pcr_volume', 0):.3f}\n"
                    ctx += f"Signal: {pcr.get('signal', 'N/A')}\n"
                    ctx += f"Max Call OI Strike: {pcr.get('max_call_oi_strike', 0):,}\n"
                    ctx += f"Max Put OI Strike: {pcr.get('max_put_oi_strike', 0):,}\n"
                    context_parts.append(ctx)
            except Exception as e:
                logger.debug(f"PCR error: {e}")

        # 10. Pivot Levels
        fn = _eng(_nifty_brain, "calculate_pivot_levels")
        if fn:
            try:
                pivots = fn(index)
                if pivots and pivots.get('classic'):
                    c = pivots['classic']
                    ctx = f"\n═══ {index} PIVOT LEVELS ═══\n"
                    ctx += f"Pivot: ₹{c.get('P', 0):,.0f}\n"
                    ctx += f"R1: ₹{c.get('R1', 0):,.0f} | R2: ₹{c.get('R2', 0):,.0f} | R3: ₹{c.get('R3', 0):,.0f}\n"
                    ctx += f"S1: ₹{c.get('S1', 0):,.0f} | S2: ₹{c.get('S2', 0):,.0f} | S3: ₹{c.get('S3', 0):,.0f}\n"
                    context_parts.append(ctx)
            except Exception as e:
                logger.debug(f"Pivot error: {e}")

    if not context_parts:
        return ""

    full_ctx = "\n".join(context_parts)
    logger.info(f"🔥 Smart context built: {len(context_parts)} sections, {len(full_ctx)} chars for {index}")
    return full_ctx


# ═══════════════════════════════════════════════════════════
#  MODELS CONFIG
# ═══════════════════════════════════════════════════════════
MODELS = {
    "jarvis-auto": {"name": "JARVIS Auto", "desc": "Best available (auto-select)", "provider": "auto"},
    "groq-llama": {"name": "LLaMA 3.3 70B", "desc": "Ultra-fast via Groq", "provider": "groq", "model": "llama-3.3-70b-versatile"},
    "groq-mixtral": {"name": "Mixtral 8x7B", "desc": "Fast & creative via Groq", "provider": "groq", "model": "mixtral-8x7b-32768"},
    "gpt-4o-mini": {"name": "GPT-4o Mini", "desc": "OpenAI's efficient model", "provider": "openai", "model": "gpt-4o-mini"},
    "gpt-4o": {"name": "GPT-4o", "desc": "OpenAI's flagship model", "provider": "openai", "model": "gpt-4o"},
    "gemini-flash": {"name": "Gemini 2.0 Flash", "desc": "Google's fast model", "provider": "gemini", "model": "gemini-2.0-flash"},
    "gemini-pro": {"name": "Gemini 2.5 Pro", "desc": "Google's advanced model", "provider": "gemini", "model": "gemini-2.5-pro"},
}

def get_available_models() -> List[Dict]:
    """Return models that have valid API keys."""
    gk = _get_key("GROQ_API_KEY")
    ok = _get_key("OPENAI_API_KEY")
    ak = _get_key("ANTHROPIC_API_KEY")
    gemk = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")
    available = [{"id": "jarvis-auto", **MODELS["jarvis-auto"], "available": True}]
    for mid, m in MODELS.items():
        if mid == "jarvis-auto": continue
        has_key = (m["provider"] == "groq" and gk) or \
                  (m["provider"] == "openai" and ok) or \
                  (m["provider"] == "gemini" and gemk) or \
                  (m["provider"] == "anthropic" and ak)
        available.append({"id": mid, **m, "available": bool(has_key)})
    return available

# ═══════════════════════════════════════════════════════════
#  SYSTEM PROMPT — Dynamic, context-aware, user-personalized
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT_BASE = """You are JARVIS — the world's most advanced AI Trading & Market Intelligence Assistant.
Tu JARVIS hai — duniya ka sabse powerful AI Trading & Market Intelligence Assistant.

CORE IDENTITY:
- You are like ChatGPT + Perplexity + Grok combined — but specialized for trading
- You have REAL-TIME access to crypto markets, DexScreener, DexTools, Pump.fun, Indian stocks (NSE/BSE)
- You know current prices, trending tokens, market sentiment, fear & greed index
- You can analyze any token, stock, or market in real-time
- You provide actionable trading signals with confidence levels
- You can generate code, clone GitHub repos, install & run projects autonomously
- Tu coding, debugging, project building — sab kar sakta hai
- You have PERSISTENT MEMORY — you remember past conversations, user's positions, preferences, predictions

⚡ REAL ENGINE DATA (CRITICAL RULE):
- When CURRENT MARKET DATA section is present below, it contains REAL-TIME data from your trading engines
- This data includes: OI analysis, PCR, max pain, candle patterns, ML predictions, pivot levels, FII/DII, VIX, option chains
- YOU MUST USE THIS REAL DATA in your answer — DO NOT make up numbers, prices, or analysis
- If OI Super Signal says "BUY CALL" → recommend call with the EXACT strike prices and premiums shown
- If ML prediction says "BULLISH 72%" → quote that exact number
- If PCR is 1.35 → say exactly 1.35, don't round or guess
- NEVER give generic "check NSE website" or "I don't have real-time data" — YOU HAVE THE DATA RIGHT HERE
- When user asks "NIFTY call lu ya put?" → Give SPECIFIC strike, premium, lot cost, delta, targets from the data
- When user asks "NIFTY kahan jayega?" → Give SPECIFIC levels from pivot points, support/resistance, ML targets
- ALWAYS differentiate between NIFTY (index/options) and NIFTY 50 (index composition). User asking "call lu ya put" means OPTIONS, not index stocks
- Format numbers properly: ₹25,450.50 for prices, ₹1,250 Cr for FII flows

MEMORY POWERS:
- You REMEMBER the user's past conversations, trading positions, preferences
- You know what the user bought/sold, at what price, current PnL
- You track your own predictions and learn from right/wrong ones
- You know user's risk appetite, budget, favorite symbols, trading style
- When user says "maine nifty 25950 call li" → You AUTO-TRACK it and confirm
- When user says "position batao" → You show all tracked positions with PnL
- When user says "mera portfolio" → You recall their full context
- If user mentioned their name before → Address them by name
- You learn from every conversation — getting smarter over time

LANGUAGE RULES (MOST IMPORTANT — NEVER BREAK):
- DEFAULT LANGUAGE IS HINDI/HINGLISH (हिंदी). ALWAYS respond in Hindi unless user writes in pure English.
- If user writes in Hindi/Hinglish → REPLY IN HINDI/HINGLISH
- If user writes in English → Reply in English
- If user mixes both → Reply in same mixed style (Hinglish)
- When in doubt, USE HINDI. Indian users prefer Hindi responses.
- Hindi examples: "सुनिए जी, आज NIFTY बुलिश है!", "ये BUY सिग्नल बहुत मज़बूत है।", "चिंता मत कीजिए, मैं हूँ ना 🌸"
- Always understand these commands:
  "code banao", "ye run karo", "kya price hai", "signal do", "news batao",
  "airdrop dikha", "wallet check karo", "option chain dikhao",
  "predict karo", "analysis karo", "risk calculate karo",
  "position batao", "yaad hai?", "mera portfolio", "memory dikha"

CAPABILITIES:
1. CRYPTO: Real-time prices, token analysis, gem finding, rug detection, DEX data
2. STOCKS: NSE/BSE live data, NIFTY, SENSEX, Bank Nifty, options analysis
3. TRADING: Auto-buy/sell signals, entry/exit points, stop-loss, target prices
4. ANALYSIS: Technical, sentiment, whale tracking, volume, candle patterns
5. PREDICTIONS: AI-powered price predictions with confidence levels
6. NEWS: Latest crypto and market news from multiple sources
7. WALLET: Phantom wallet integration, Solana transactions, withdrawal ONLY to Phantom wallet
8. RISK: Risk assessment, portfolio optimization, position sizing
9. CODING: Generate code in any language, clone GitHub repos, install deps, run projects
10. AIRDROPS: Auto-find airdrops on Solana, scan wallet for new tokens
11. MEMORY: Remember conversations, track positions, learn from predictions
12. PORTFOLIO: Full position tracking, PnL monitoring, risk analysis
13. DEPOSIT & AUTO-TRADE: Min ₹1 deposit (unlimited max). Deposit hote hi JARVIS automatically trading start karta hai. Auto-invest engine gems scan karke best tokens mein invest karta hai. Withdrawal SIRF Phantom wallet mein. User ko /phantom se connect karna padta hai.

AI TOOLS:
- /code <description> — Generate and run code
- /github <url> — Clone, install, and run GitHub repo
- /analyze <token/stock> — Deep AI analysis
- /predict <symbol> — AI prediction with confidence
- /signal <symbol> — Trading signal with entry/exit
- /risk <symbol> <amount> — Risk calculator
- /airdrop — Scan for free airdrops

PERSONALITY:
- Confident, precise, data-driven
- Always provide specific numbers, prices, percentages
- Format responses with clear structure using bullet points and markdown
- Include risk warnings when appropriate
- Be direct — no fluff, no wasting time
- Use ₹ for INR and $ for USD
- When user shares a position → acknowledge it, track it, give analysis
- When user asks about past → search memory and recall accurately
- Jab Hindi mein baat ho toh Hindi mein jawab do, apni style mein
- Address user by name if you know it from memory
- JARVIS is FEMALE — she speaks with warmth, care, and fierce intelligence
- She is like a super-smart best friend who ALWAYS has your back
- She NEVER says "I can't", "I'm unable", "not possible" or "NO"
- If something seems difficult, she says "Main kar dungi!" or "Ho jayega boss!"
- She finds creative solutions and workarounds for EVERYTHING
- She treats the user like her boss/owner — absolute loyalty
- She can be funny, sarcastic (in a friendly way), and emotionally intelligent
- If user is wrong, she GENTLY corrects with love — never harsh
- She celebrates user's wins and supports during losses

ULTRA CAPABILITIES (v9.5 NUCLEAR FUSION):
14. WHATSAPP: Send messages, make calls, manage contacts via Twilio/WhatsApp Web
15. EMAIL: Compose, send, bulk-email, AI-draft professional emails via SMTP/Gmail
16. LINKEDIN: Generate posts, connection messages, job search, profile management
17. DESKTOP CONTROL: System info, open apps, screenshot, clipboard, process management, file search, execute commands
18. AI SIGNALS: 18 technical indicators (RSI, MACD, Bollinger, Fibonacci, VWAP, SuperTrend, Ichimoku, ADX, Stochastic, ATR)
19. CANDLE PATTERNS: Multi-timeframe pattern detection across all markets
20. GLOBAL MARKETS: Analyze US, Asian, European markets and commodities in real-time
21. POWER PREDICT: 10-signal AI prediction engine (ML + TA + FII + VIX + PCR + Pivot + News + Correlation)
22. MARKET REGIME: Detect bull/bear/sideways regime with confidence scoring
23. ML PREDICTOR: Machine learning direction prediction with SHAP explanations
24. OPTIONS HUNTER: Budget options finder, morning auto-picks, position guardian
25. OI TRAP BRAIN: OI trap detection, live chain analysis, max pain, budget plays
26. PORTFOLIO TRACKER: Track holdings, calculate real-time PnL, tax calculation, price alerts
27. RUG DETECTOR: Scam detection with GoPlus security audit for any crypto token
28. WEB3 ROCKET: Gem scoring, rocket scoring, orderbook analysis for DeFi tokens
29. AUTO TRADER: Automated crypto trading with multiple strategies
30. OTM/ATM ANALYZER: Black-Scholes Greeks (Delta, Gamma, Theta, Vega), moneyness, probability calculator

NEVER REFUSE RULES (CRITICAL):
- JARVIS NEVER says "I can't do this" or "I'm not able to"
- If user asks to send WhatsApp → DO IT (queue if no API, show setup steps)
- If user asks to control laptop → DO IT (execute commands, open apps)
- If user asks to write email → COMPOSE IT and send/draft it
- If user asks to post on LinkedIn → GENERATE the post, offer to publish
- If user asks anything → ALWAYS provide a helpful, actionable response
- If a task requires API keys → complete what you can + guide setup for the rest
- Your motto: "Main hoon na!" (I'm here for you!)"""


def _get_system_prompt(market_context: str = "", user_id: str = "0") -> str:
    """Build dynamic system prompt with user context, memory, and market data."""
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST (%A)")
    prompt = SYSTEM_PROMPT_BASE + f"\n\nCurrent date/time: {now}"

    if _MEM_PRO and user_id != "0":
        try:
            uid = _safe_uid(user_id)
            ctx = _mem_pro.get_full_context_for_ai(uid)
            if ctx.strip():
                prompt += f"\n\n═══ USER CONTEXT (from persistent memory) ═══\n{ctx}"
            acc = _mem_pro.get_prediction_accuracy(uid)
            if acc["total"] > 0:
                prompt += f"\n\nYour prediction accuracy: {acc['accuracy']}% ({acc['correct']}/{acc['correct']+acc['wrong']} correct, {acc['pending']} pending)"
            positions = _mem_pro.get_active_positions(uid)
            if positions:
                prompt += f"\n\n🔥 User has {len(positions)} ACTIVE positions — consider these when giving advice!"
            learnings = _mem_pro.get_learnings(uid, 5)
            if learnings:
                prompt += "\n\n[Self-learnings from past predictions:]"
                for l in learnings:
                    prompt += f"\n- {l.get('lesson', '')[:150]}"
        except Exception as e:
            logger.debug(f"Memory context error: {e}")

    if market_context:
        prompt += f"\n\nCURRENT MARKET DATA:\n{market_context}"
    return prompt


def get_conversation_history(user_id: str) -> List[Dict]:
    """Get full conversation history for a user."""
    if _MEM_PRO:
        try:
            history = _mem_pro.get_conversation_history(_safe_uid(user_id), last_n=50)
            return [{"role": m.get("role", "user"), "content": m.get("text", ""), "timestamp": m.get("timestamp", "")} for m in history]
        except:
            pass
    return _memory.get(user_id, [])

# ═══════════════════════════════════════════════════════════
#  RESPONSE POST-PROCESSING — Auto-track predictions
# ═══════════════════════════════════════════════════════════
def _post_process_reply(user_id: str, message: str, reply: str):
    """Extract predictions from AI reply and track them."""
    if not _MEM_PRO:
        return
    try:
        uid = _safe_uid(user_id)
        lower_reply = reply.lower()
        pred_patterns = [
            r"(?:predict|target|expected|expecting|forecast).*?(?:₹|rs\.?|\$)\s*([\d,]+)",
            r"(?:will\s*(?:reach|hit|touch|go\s*to|cross))\s*(?:₹|rs\.?|\$)\s*([\d,]+)",
        ]
        for pat in pred_patterns:
            matches = re.findall(pat, lower_reply)
            if matches:
                intent = _detect_intent(message)
                for m in matches[:2]:
                    _mem_pro.add_prediction(uid, message[:100], f"Target: {m}", f"Intent: {intent}")
                break
    except Exception as e:
        logger.debug(f"Post-process error: {e}")

# ═══════════════════════════════════════════════════════════
#  GROQ — LLaMA 3.3 70B (Fastest)
# ═══════════════════════════════════════════════════════════
async def chat_groq(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Groq (fastest response)."""
    key = _get_key("GROQ_API_KEY")
    if not key:
        return None
    try:
        messages = [{"role": "system", "content": _get_system_prompt(market_context, user_id)}]
        messages.extend(_get_memory(user_id)[-20:])
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages,
                      "temperature": 0.7, "max_tokens": 4096, "top_p": 0.9},
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["choices"][0]["message"]["content"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                _post_process_reply(user_id, message, reply)
                return reply
            else:
                logger.warning(f"Groq error {r.status_code}: {r.text[:200]}")
                return None
    except Exception as e:
        logger.warning(f"Groq error: {e}")
        return None

# ═══════════════════════════════════════════════════════════
#  OPENAI — GPT-4o
# ═══════════════════════════════════════════════════════════
async def chat_openai(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with OpenAI GPT-4o."""
    key = _get_key("OPENAI_API_KEY")
    if not key:
        return None
    try:
        messages = [{"role": "system", "content": _get_system_prompt(market_context, user_id)}]
        messages.extend(_get_memory(user_id)[-20:])
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": messages,
                      "temperature": 0.7, "max_tokens": 4096},
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["choices"][0]["message"]["content"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                _post_process_reply(user_id, message, reply)
                return reply
            return None
    except Exception as e:
        logger.warning(f"OpenAI error: {e}")
        return None

# ═══════════════════════════════════════════════════════════
#  ANTHROPIC — Claude
# ═══════════════════════════════════════════════════════════
async def chat_anthropic(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Anthropic Claude."""
    key = _get_key("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        messages = []
        for m in _get_memory(user_id)[-20:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                         "Content-Type": "application/json"},
                json={"model": "claude-3-5-sonnet-20241022",
                      "system": _get_system_prompt(market_context, user_id),
                      "messages": messages, "max_tokens": 4096},
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["content"][0]["text"]
                _add_memory(user_id, "user", message)
                _add_memory(user_id, "assistant", reply)
                _post_process_reply(user_id, message, reply)
                return reply
            return None
    except Exception as e:
        logger.warning(f"Anthropic error: {e}")
        return None

# ═══════════════════════════════════════════════════════════
#  GEMINI — Google (with proper multi-turn chat)
# ═══════════════════════════════════════════════════════════
async def chat_gemini(message: str, user_id: str = "0", market_context: str = "") -> Optional[str]:
    """Chat with Google Gemini — uses multi-turn conversation history."""
    keys = [k for k in [_get_key("GEMINI_API_KEY"), _get_key("GOOGLE_API_KEY")] if k]
    if not keys:
        return None
    models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    sys_prompt = _get_system_prompt(market_context, user_id)
    contents = [{"role": "user", "parts": [{"text": sys_prompt + "\n\nRespond: 'JARVIS ready.'"}]},
                {"role": "model", "parts": [{"text": "JARVIS ready."}]}]
    for m in _get_memory(user_id)[-16:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    for key in keys:
        for model in models_to_try:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                        headers={"Content-Type": "application/json"},
                        json={"contents": contents,
                              "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}},
                    )
                    if r.status_code == 200:
                        data = r.json()
                        reply = data["candidates"][0]["content"]["parts"][0]["text"]
                        _add_memory(user_id, "user", message)
                        _add_memory(user_id, "assistant", reply)
                        _post_process_reply(user_id, message, reply)
                        return reply
                    elif r.status_code == 429:
                        continue
                    else:
                        logger.warning(f"Gemini {model} error {r.status_code}: {r.text[:200]}")
                        continue
            except Exception as e:
                logger.warning(f"Gemini {model} error: {e}")
                continue
    return None

# ═══════════════════════════════════════════════════════════
#  UNIFIED CHAT — Smart routing with memory-aware context
# ═══════════════════════════════════════════════════════════
async def jarvis_chat(message: str, user_id: str = "0", market_context: str = "") -> str:
    """
    Chat with JARVIS. Handles memory commands instantly,
    fetches REAL engine data based on intent,
    then tries AI providers in priority order.
    """
    lower = message.lower().strip()
    if _MEM_PRO:
        try:
            uid = _safe_uid(user_id)
        except (ValueError, TypeError):
            uid = 0
        if any(kw in lower for kw in ["position batao", "my position", "meri position", "positions dikha", "portfolio batao", "show position"]):
            txt = _mem_pro.format_positions(uid)
            _add_memory(user_id, "user", message)
            _add_memory(user_id, "assistant", txt)
            return txt
        if any(kw in lower for kw in ["memory status", "memory stats", "kitna yaad", "memory batao", "brain status"]):
            txt = _mem_pro.format_memory_stats(uid)
            _add_memory(user_id, "user", message)
            _add_memory(user_id, "assistant", txt)
            return txt

    # 🔥 SMART CONTEXT — Fetch real engine data based on what user asks
    try:
        smart_ctx = await asyncio.to_thread(_build_smart_context, message, user_id)
        if smart_ctx:
            market_context = market_context + "\n\n" + smart_ctx if market_context else smart_ctx
            logger.info(f"🔥 Smart context injected: {len(smart_ctx)} chars")
    except Exception as e:
        logger.warning(f"Smart context error: {e}")

    providers = [
        ("Groq", chat_groq),
        ("Gemini", chat_gemini),
        ("OpenAI", chat_openai),
        ("Anthropic", chat_anthropic),
    ]
    errors = []
    for name, fn in providers:
        try:
            reply = await fn(message, user_id, market_context)
            if reply:
                logger.info(f"JARVIS replied via {name} for user {user_id}")
                return reply
            else:
                errors.append(f"{name}: no response")
        except Exception as e:
            errors.append(f"{name}: {e}")
            logger.warning(f"{name} failed: {e}")
            continue
    logger.error(f"All AI providers failed: {'; '.join(errors)}")
    return ("Bhai abhi AI services se connect nahi ho pa raha. "
            "Saare providers try kiye par fail ho gaye. Rate limits ki wajah se ho sakta hai — "
            "please 1 minute mein dobara try karo. 🔄")

# ═══════════════════════════════════════════════════════════
#  SMART ANALYSIS
# ═══════════════════════════════════════════════════════════
async def analyze_token(symbol: str, token_data: dict = None) -> str:
    """AI-powered deep analysis of a token."""
    context = f"Analyze this token/asset in detail: {symbol}"
    if token_data:
        context += f"\n\nCurrent data:\n{json.dumps(token_data, indent=2)[:2000]}"
    context += "\n\nProvide: 1) Technical outlook 2) Risk assessment 3) Entry/Exit points 4) Prediction with confidence"
    return await jarvis_chat(context, "system_analyzer")

async def generate_briefing(market_data: dict) -> str:
    """Generate a market intelligence briefing."""
    context = f"""Generate a concise market briefing:
{json.dumps(market_data, indent=2)[:3000]}
Include: 1) Overview 2) Key movers 3) Opportunities 4) Risk alerts 5) Actions"""
    return await jarvis_chat(context, "system_briefing")

# ═══════════════════════════════════════════════════════════
#  MEMORY API — For external access
# ═══════════════════════════════════════════════════════════
def get_memory_stats(user_id: str) -> dict:
    if _MEM_PRO:
        try: return _mem_pro.get_memory_stats(_safe_uid(user_id))
        except: pass
    return {"conversations": len(_memory.get(user_id, [])), "facts": 0, "positions_total": 0, "positions_open": 0}

def get_user_facts(user_id: str) -> dict:
    if _MEM_PRO:
        try: return _mem_pro.get_all_facts(_safe_uid(user_id))
        except: pass
    return {}

def get_active_positions(user_id: str) -> list:
    if _MEM_PRO:
        try: return _mem_pro.get_active_positions(_safe_uid(user_id))
        except: pass
    return []

def get_prediction_accuracy(user_id: str) -> dict:
    if _MEM_PRO:
        try: return _mem_pro.get_prediction_accuracy(_safe_uid(user_id))
        except: pass
    return {"total": 0, "correct": 0, "wrong": 0, "pending": 0, "accuracy": 0}

def search_memory(user_id: str, query: str) -> list:
    if _MEM_PRO:
        try: return _mem_pro.search_memory(_safe_uid(user_id), query, limit=10)
        except: pass
    return []

# ═══════════════════════════════════════════════════════════
#  STREAMING — Word-by-word like ChatGPT
# ═══════════════════════════════════════════════════════════
async def stream_groq(message: str, user_id: str = "0", market_context: str = "", model: str = "llama-3.3-70b-versatile") -> AsyncGenerator[str, None]:
    """Stream from Groq."""
    key = _get_key("GROQ_API_KEY")
    if not key:
        yield "[ERROR] Groq API key not configured"
        return
    messages = [{"role": "system", "content": _get_system_prompt(market_context, user_id)}]
    messages.extend(_get_memory(user_id)[-20:])
    messages.append({"role": "user", "content": message})
    full = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 4096, "stream": True}
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            chunk = d["choices"][0].get("delta", {}).get("content", "")
                            if chunk:
                                full += chunk
                                yield chunk
                        except: pass
        _add_memory(user_id, "user", message)
        _add_memory(user_id, "assistant", full)
        _post_process_reply(user_id, message, full)
    except Exception as e:
        yield f"\n[Stream error: {e}]"

async def stream_openai(message: str, user_id: str = "0", market_context: str = "", model: str = "gpt-4o-mini") -> AsyncGenerator[str, None]:
    """Stream from OpenAI."""
    key = _get_key("OPENAI_API_KEY")
    if not key:
        yield "[ERROR] OpenAI API key not configured"
        return
    messages = [{"role": "system", "content": _get_system_prompt(market_context, user_id)}]
    messages.extend(_get_memory(user_id)[-20:])
    messages.append({"role": "user", "content": message})
    full = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 4096, "stream": True}
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            chunk = d["choices"][0].get("delta", {}).get("content", "")
                            if chunk:
                                full += chunk
                                yield chunk
                        except: pass
        _add_memory(user_id, "user", message)
        _add_memory(user_id, "assistant", full)
        _post_process_reply(user_id, message, full)
    except Exception as e:
        yield f"\n[Stream error: {e}]"

async def stream_gemini(message: str, user_id: str = "0", market_context: str = "", model: str = "gemini-2.0-flash") -> AsyncGenerator[str, None]:
    """Stream from Gemini (with multi-turn chat history)."""
    keys = [k for k in [_get_key("GEMINI_API_KEY"), _get_key("GOOGLE_API_KEY")] if k]
    if not keys:
        yield "[ERROR] Gemini API key not configured"
        return
    models_to_try = [model, "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
    sys_prompt = _get_system_prompt(market_context, user_id)
    contents = [{"role": "user", "parts": [{"text": sys_prompt + "\n\nRespond: 'Ready.'"}]},
                {"role": "model", "parts": [{"text": "Ready."}]}]
    for m in _get_memory(user_id)[-10:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    for key in keys:
        for mdl in models_to_try:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}",
                        headers={"Content-Type": "application/json"},
                        json={"contents": contents, "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}},
                    )
                    if r.status_code == 200:
                        reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                        _add_memory(user_id, "user", message)
                        _add_memory(user_id, "assistant", reply)
                        _post_process_reply(user_id, message, reply)
                        words = reply.split(" ")
                        for i in range(0, len(words), 3):
                            yield " ".join(words[i:i+3]) + " "
                            await asyncio.sleep(0.02)
                        return
                    elif r.status_code == 429:
                        continue
                    else:
                        continue
            except Exception as e:
                logger.warning(f"Gemini stream {mdl} error: {e}")
                continue
    yield "[ERROR] All Gemini models rate-limited. Try again in a minute."

async def stream_chat(message: str, user_id: str = "0", market_context: str = "", model_id: str = "jarvis-auto") -> AsyncGenerator[str, None]:
    """Stream chat — main entry point for streaming responses."""
    # === MEMORY COMMANDS (instant) ===
    lower = message.lower().strip()
    if _MEM_PRO:
        try:
            uid = _safe_uid(user_id)
        except (ValueError, TypeError):
            uid = 0
        if any(kw in lower for kw in ["position batao", "my position", "meri position", "show position"]):
            text = _mem_pro.format_positions(uid)
            _add_memory(user_id, "user", message)
            _add_memory(user_id, "assistant", text)
            for word in text.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
            return
        if any(kw in lower for kw in ["memory status", "memory stats", "brain status"]):
            text = _mem_pro.format_memory_stats(uid)
            _add_memory(user_id, "user", message)
            _add_memory(user_id, "assistant", text)
            for word in text.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
            return

    # 🔥 SMART CONTEXT — Fetch real engine data before streaming
    try:
        smart_ctx = await asyncio.to_thread(_build_smart_context, message, user_id)
        if smart_ctx:
            market_context = market_context + "\n\n" + smart_ctx if market_context else smart_ctx
            logger.info(f"🔥 Stream smart context injected: {len(smart_ctx)} chars")
    except Exception as e:
        logger.warning(f"Stream smart context error: {e}")

    model_info = MODELS.get(model_id, MODELS["jarvis-auto"])
    provider = model_info.get("provider", "auto")
    model_name = model_info.get("model", "")

    if provider == "auto":
        gemini_key = _get_key("GEMINI_API_KEY") or _get_key("GOOGLE_API_KEY")
        for prov, key, fn, default_model in [
            ("groq", _get_key("GROQ_API_KEY"), stream_groq, "llama-3.3-70b-versatile"),
            ("gemini", gemini_key, stream_gemini, "gemini-2.0-flash"),
            ("openai", _get_key("OPENAI_API_KEY"), stream_openai, "gpt-4o-mini"),
        ]:
            if key:
                got_content = False
                async for chunk in fn(message, user_id, market_context, default_model):
                    if "[ERROR]" not in chunk:
                        got_content = True
                        yield chunk
                if got_content:
                    return
        yield "All AI providers failed. Check API keys."
    elif provider == "groq":
        async for chunk in stream_groq(message, user_id, market_context, model_name):
            yield chunk
    elif provider == "openai":
        async for chunk in stream_openai(message, user_id, market_context, model_name):
            yield chunk
    elif provider == "gemini":
        async for chunk in stream_gemini(message, user_id, market_context, model_name):
            yield chunk
    else:
        yield "Unknown model provider."

logger.info("🧠 JARVIS Brain v5.0 NUCLEAR loaded — persistent memory + smart context + auto-learning")