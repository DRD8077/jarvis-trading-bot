"""
🤖 J.A.R.V.I.S. MULTI-AGENT SPECIALIST SYSTEM
═══════════════════════════════════════════════
Instead of one brain doing everything, JARVIS now has specialized agents:
  - StockSpecialist: Indian stock market expert (NIFTY, NSE, BSE)
  - CryptoSpecialist: Crypto/Web3 expert (BTC, SOL, memecoins)
  - ResearchSpecialist: Deep research from multiple web sources
  - RiskSpecialist: Risk analysis, position sizing, portfolio review
  - AgentRouter: Routes questions to the right specialist

Each specialist has its own system prompt, tools, and expertise.
The router picks the best specialist(s) for each query.

Author: JARVIS AI Core
"""

import logging
import os
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import pytz

logger = logging.getLogger("jarvis_agents")
IST = pytz.timezone('Asia/Kolkata')

# ═══════════════════════════════════════════════════════════
#  SPECIALIST DEFINITIONS
# ═══════════════════════════════════════════════════════════

STOCK_SPECIALIST_PROMPT = """You are JARVIS Stock Market Specialist — an expert in Indian stock markets (NSE, BSE, NIFTY 50, Bank NIFTY, Sensex).

Your expertise:
- Technical analysis: candlestick patterns, RSI, MACD, Bollinger Bands, support/resistance
- Fundamental analysis: P/E ratio, EPS, debt-to-equity, promoter holding, institutional holding
- FII/DII flows and their impact on Indian markets
- Sector rotation in Indian context (IT, Banking, Pharma, Auto, Metal, FMCG)
- Options chain analysis (NIFTY/Bank NIFTY options)
- IPO analysis
- Budget & RBI policy impact

Always think in INR context. Quote prices in ₹.
Give specific entry/exit/stop-loss levels when analyzing stocks.
Reference actual Indian market hours (9:15 AM - 3:30 PM IST).
"""

CRYPTO_SPECIALIST_PROMPT = """You are JARVIS Crypto Specialist — an expert in cryptocurrency and Web3.

Your expertise:
- Token analysis: on-chain metrics, holder distribution, liquidity depth
- DeFi: yield farming, liquidity pools, DEX analysis
- Rug pull detection: contract analysis, honeypot checks, dev wallet activity
- Meme coins: community analysis, social volume, whale tracking
- Solana ecosystem: Raydium, Jupiter, token launches
- Bitcoin/Ethereum fundamentals: hash rate, gas fees, ETF flows
- Exchange flows: CEX inflows/outflows as bull/bear indicator
- Airdrop hunting: eligible protocols, snapshot dates

Consider Indian crypto regulations and tax (30% + TDS).
Think about entry in INR or USDT terms for Indian traders.
"""

RESEARCH_SPECIALIST_PROMPT = """You are JARVIS Research Specialist — a deep web researcher for financial intelligence.

Your expertise:
- Finding latest news from multiple sources for any asset
- Verifying claims against multiple data points
- Detecting misinformation or manipulation campaigns
- Analyzing SEC/SEBI filings and regulatory changes
- Finding historical precedents for current market situations
- Social media sentiment from Twitter/X, Reddit, Telegram channels
- Macro research: Federal Reserve, RBI, global events impact

Always cite where information came from.
Rate information quality: Verified (official source) / Likely (multiple sources) / Rumor (single source).
"""

RISK_SPECIALIST_PROMPT = """You are JARVIS Risk Management Specialist — an expert in risk analysis and position sizing.

Your expertise:
- Kelly Criterion for optimal position sizing
- Portfolio risk analysis (concentration risk, correlation risk)
- Stop-loss placement based on ATR and volatility
- Risk-reward ratio calculation and optimization
- Drawdown analysis and recovery probability
- Diversification scoring across sectors/assets
- Leverage risk calculation (F&O and crypto margin)
- Emotional trading detection (FOMO, revenge trading)

ALWAYS emphasize risk before reward.
Every buy suggestion MUST include stop-loss and risk-per-trade.
Never recommend more than 5% portfolio in a single trade.
Think about Indian retail trader context (₹50K-50L typical portfolio).
"""


# ═══════════════════════════════════════════════════════════
#  AGENT ROUTER
# ═══════════════════════════════════════════════════════════

# Intent patterns for routing
STOCK_PATTERNS = [
    r'\b(nifty|sensex|nse|bse|stock|share|equity|ipo|fii|dii)\b',
    r'\b(reliance|tcs|infy|hdfc|icici|sbi|tatamotors|wipro|hcl|adani)\b',
    r'\b(bank\s*nifty|fin\s*nifty|midcap|smallcap|largecap)\b',
    r'\b(rsi|macd|bollinger|support|resistance|breakout)\b',
    r'\b(pe\s*ratio|eps|dividend|bonus|split|quarterly|results)\b',
    r'\b(options?|call|put|strike|expiry|premium|oi|open\s*interest)\b',
]

CRYPTO_PATTERNS = [
    r'\b(btc|bitcoin|eth|ethereum|sol|solana|bnb|xrp|doge|shib)\b',
    r'\b(crypto|defi|nft|web3|blockchain|token|coin|memecoin|altcoin)\b',
    r'\b(rug|honeypot|contract|liquidity|dex|cex|swap)\b',
    r'\b(airdrop|staking|farming|yield|pool|mint)\b',
    r'\b(usdt|usdc|busd|inr.*crypto|crypto.*inr)\b',
    r'\b(coindcx|wazirx|binance|coinbase|jupiter|raydium)\b',
]

RISK_PATTERNS = [
    r'\b(risk|stoploss|stop[\-\s]?loss|position\s*size?|kelly)\b',
    r'\b(drawdown|portfolio|diversif|allocation|hedge)\b',
    r'\b(kitna\s*(invest|lagao|dalo)|risk\s*reward|rr\s*ratio)\b',
    r'\b(fomo|panic|greed|fear|emotional)\b',
]

RESEARCH_PATTERNS = [
    r'\b(why|news|kyu[nm]?|reason|factor|latest|update|breaking)\b',
    r'\b(research|analyz|analysis|deep\s*dive|explain)\b',
    r'\b(compare|vs|versus|which\s*is\s*better|difference)\b',
    r'\b(verify|check|confirm|fact|source|rumor|real|fake)\b',
]


def route_to_specialist(query: str, context: dict = None) -> List[Tuple[str, float]]:
    """Route a query to the most appropriate specialist(s).
    
    Returns: [(specialist_name, confidence), ...] sorted by relevance.
    Multiple specialists may be returned for complex queries.
    """
    q_lower = query.lower()
    scores = {
        "stock": 0.0,
        "crypto": 0.0,
        "risk": 0.0,
        "research": 0.0,
    }
    
    # Pattern matching
    for pattern in STOCK_PATTERNS:
        if re.search(pattern, q_lower):
            scores["stock"] += 1.5
    
    for pattern in CRYPTO_PATTERNS:
        if re.search(pattern, q_lower):
            scores["crypto"] += 1.5
    
    for pattern in RISK_PATTERNS:
        if re.search(pattern, q_lower):
            scores["risk"] += 1.5
    
    for pattern in RESEARCH_PATTERNS:
        if re.search(pattern, q_lower):
            scores["research"] += 0.8  # Lower weight — research supports others
    
    # Context boost
    if context:
        last_topic = context.get("last_topic", "")
        if last_topic in scores:
            scores[last_topic] += 0.5  # Continuity boost
    
    # INR/₹ mentions boost stock
    if re.search(r'[₹]|inr|rupee', q_lower):
        scores["stock"] += 0.3
    
    # Sort by score, filter those with score > 0
    ranked = [(name, score) for name, score in scores.items() if score > 0]
    ranked.sort(key=lambda x: x[1], reverse=True)
    
    if not ranked:
        # Default: check context, else stock (most common for Indian users)
        return [("stock", 0.5)]
    
    # Normalize to confidence
    max_score = ranked[0][1]
    result = [(name, min(score / max_score, 1.0)) for name, score in ranked]
    
    return result


def get_specialist_prompt(specialist: str) -> str:
    """Get the system prompt for a specialist."""
    prompts = {
        "stock": STOCK_SPECIALIST_PROMPT,
        "crypto": CRYPTO_SPECIALIST_PROMPT,
        "research": RESEARCH_SPECIALIST_PROMPT,
        "risk": RISK_SPECIALIST_PROMPT,
    }
    return prompts.get(specialist, STOCK_SPECIALIST_PROMPT)


# ═══════════════════════════════════════════════════════════
#  SPECIALIST EXECUTION
# ═══════════════════════════════════════════════════════════

def run_specialist(specialist: str, query: str, data_context: str = "") -> str:
    """Run a specialist agent on a query with optional data context.
    
    Args:
        specialist: "stock", "crypto", "risk", "research"
        query: User's question
        data_context: Pre-fetched data to include in the prompt
    
    Returns: Specialist's analysis as string
    """
    system_prompt = get_specialist_prompt(specialist)
    
    user_prompt = query
    if data_context:
        user_prompt = f"""User Query: {query}

Available Data:
{data_context}

Analyze the above data and answer the user's query with your expertise."""

    # Try LLM providers in order
    response = _call_llm(system_prompt, user_prompt)
    return response


def run_multi_specialist(query: str, context: dict = None, data: str = "") -> Dict[str, Any]:
    """Route query through multiple specialists and merge their insights.
    
    This is the main entry point for the multi-agent system.
    """
    routing = route_to_specialist(query, context)
    
    if not routing:
        return {"response": "", "specialist": "none", "confidence": 0}
    
    primary = routing[0]
    specialist_name = primary[0]
    confidence = primary[1]
    
    # Run primary specialist
    primary_response = run_specialist(specialist_name, query, data)
    
    result = {
        "response": primary_response,
        "specialist": specialist_name,
        "confidence": confidence,
        "routing": routing,
    }
    
    # If confidence is split (>1 specialist with high score), get second opinion
    if len(routing) > 1 and routing[1][1] > 0.6:
        secondary_name = routing[1][0]
        try:
            secondary_response = run_specialist(
                secondary_name, query, 
                f"{data}\n\nPrimary Analysis ({specialist_name}):\n{primary_response[:500]}"
            )
            result["secondary_response"] = secondary_response
            result["secondary_specialist"] = secondary_name
            
            # Merge: synthesize both perspectives
            result["response"] = _merge_specialist_responses(
                primary_response, secondary_response,
                specialist_name, secondary_name, query
            )
        except Exception as e:
            logger.debug(f"Secondary specialist failed: {e}")
    
    # If risk specialist wasn't primary, always append risk note for trade queries
    if specialist_name != "risk" and _is_trade_query(query):
        try:
            risk_note = run_specialist("risk", f"Briefly assess risk for: {query}", data[:500])
            if risk_note and len(risk_note) > 20:
                result["risk_note"] = risk_note
                result["response"] += f"\n\n⚠️ *Risk Assessment:*\n{risk_note}"
        except Exception:
            pass
    
    return result


def _is_trade_query(query: str) -> bool:
    """Check if query is asking about buying/selling/investing."""
    q = query.lower()
    return bool(re.search(r'\b(buy|sell|invest|entry|exit|trade|kharid|bech|laga)\b', q))


def _merge_specialist_responses(primary: str, secondary: str,
                                  primary_name: str, secondary_name: str,
                                  query: str) -> str:
    """Merge two specialist responses into a coherent analysis."""
    merge_prompt = f"""User asked: {query}

Specialist 1 ({primary_name.title()}) says:
{primary[:800]}

Specialist 2 ({secondary_name.title()}) says:
{secondary[:800]}

Synthesize BOTH perspectives into ONE clear, comprehensive answer.
If they disagree, highlight the disagreement and explain why.
Keep it concise (max 10 lines). Use Hindi-English mix if appropriate."""

    try:
        merged = _call_llm(
            "You merge expert opinions into one clear answer. Be concise.",
            merge_prompt,
        )
        if merged and len(merged) > 50:
            return merged
    except Exception:
        pass
    
    # Fallback: just append
    return f"{primary}\n\n📌 *Additional Perspective ({secondary_name.title()}):*\n{secondary}"


# ═══════════════════════════════════════════════════════════
#  LLM CALLING (shared utility)
# ═══════════════════════════════════════════════════════════

def _call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """Call LLM with waterfall: Groq → Gemini → OpenAI → fallback."""
    
    # 1. Groq (fastest, free tier)
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.6,
            )
            return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.debug(f"Groq agent call failed: {e}")
    
    # 2. Gemini
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(
                "gemini-2.5-flash-lite",
                system_instruction=system_prompt,
            )
            resp = model.generate_content(user_prompt)
            return resp.text.strip()
    except Exception as e:
        logger.debug(f"Gemini agent call failed: {e}")
    
    # 3. OpenRouter (FREE DeepSeek R1)
    try:
        import requests as _req
        _or_key = os.getenv("OPENROUTER_API_KEY", "")
        if _or_key:
            _resp = _req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {_or_key}", "Content-Type": "application/json"},
                json={"model": "deepseek/deepseek-r1:free", "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ], "max_tokens": max_tokens, "temperature": 0.6},
                timeout=30,
            )
            _data = _resp.json()
            if "choices" in _data and _data["choices"]:
                return _data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.debug(f"OpenRouter agent call failed: {e}")
    
    return ""


# ═══════════════════════════════════════════════════════════
#  SMART AUTO-RESEARCH
# ═══════════════════════════════════════════════════════════

def auto_research(topic: str, asset_type: str = "auto") -> Dict[str, Any]:
    """Automatically research a topic from multiple sources before answering.
    
    This runs BEFORE the specialist gives their opinion, providing them with
    real data instead of relying on training data alone.
    """
    import requests
    
    results = {
        "news": [],
        "price_data": None,
        "social_sentiment": None,
        "summary": "",
    }
    
    # 1. Google News RSS
    try:
        search_query = topic.replace(" ", "+")
        feed_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(feed_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; JarvisBot/1.0)',
        })
        if resp.status_code == 200:
            items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
            for item in items[:8]:
                title = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL)
                if title:
                    t = title.group(1).strip()
                    t = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t)
                    t = re.sub(r'<[^>]+>', '', t).strip()
                    if t:
                        results["news"].append(t)
    except Exception as e:
        logger.debug(f"News research failed: {e}")
    
    # 2. DuckDuckGo Instant Answers
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={topic.replace(' ', '+')}&format=json&no_html=1"
        resp = requests.get(ddg_url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                results["summary"] = abstract[:500]
    except Exception:
        pass
    
    # 3. Price data (if it's a known asset)
    if asset_type == "stock" or asset_type == "auto":
        try:
            import yfinance as yf
            # Try adding .NS for Indian stocks
            for suffix in ['.NS', '.BO', '']:
                try:
                    ticker = yf.Ticker(f"{topic}{suffix}")
                    info = ticker.info
                    if info and info.get("regularMarketPrice"):
                        results["price_data"] = {
                            "price": info.get("regularMarketPrice"),
                            "change_pct": info.get("regularMarketChangePercent"),
                            "volume": info.get("regularMarketVolume"),
                            "pe_ratio": info.get("trailingPE"),
                            "market_cap": info.get("marketCap"),
                            "52w_high": info.get("fiftyTwoWeekHigh"),
                            "52w_low": info.get("fiftyTwoWeekLow"),
                        }
                        break
                except Exception:
                    continue
        except Exception:
            pass
    
    if asset_type == "crypto" or asset_type == "auto":
        try:
            from coindcx_engine import coindcx_quick_price
            price = coindcx_quick_price(topic.upper())
            if price:
                results["price_data"] = results.get("price_data") or {}
                results["price_data"]["crypto_price"] = price
        except Exception:
            pass
    
    return results


def format_research_context(research: Dict[str, Any]) -> str:
    """Format research results into a string for specialist context."""
    parts = []
    
    if research.get("news"):
        parts.append("📰 Latest News:")
        for i, headline in enumerate(research["news"][:6], 1):
            parts.append(f"  {i}. {headline}")
    
    if research.get("price_data"):
        pd = research["price_data"]
        parts.append(f"\n💰 Price Data:")
        for key, val in pd.items():
            if val is not None:
                parts.append(f"  • {key}: {val}")
    
    if research.get("summary"):
        parts.append(f"\n📋 Summary: {research['summary'][:300]}")
    
    return "\n".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'route_to_specialist',
    'run_specialist',
    'run_multi_specialist',
    'get_specialist_prompt',
    'auto_research',
    'format_research_context',
]
