# 🔥 JARVIS UNTAPPED POWER REPORT
## All Backend Functions NOT Yet Exposed to Mini App Frontend

**Generated:** 2026-02-11  
**Total files analyzed:** 28 backend files + miniapp_api.py (1792 lines)

---

## 📊 SUMMARY

| Category | Already Connected | **NOT Connected (Untapped)** |
|----------|:-:|:-:|
| Futures Brain | 2 (VIX, dashboard) | **6 (PCR, Max Pain, Basis, Straddle, OI Distribution, formatted)** |
| Options Pro | 0 | **6 (Strike price, Nearby options, Full chain summary, Recommendation, Parse query, Format)** |
| Intraday Scanner | 0 | **5 (Full scan, Breakouts, Volume spikes, Momentum, Detect breakout)** |
| Backtester Pro | 1 (handle_backtest_command) | **4 (RSI strategy, MACD strategy, Bollinger strategy, format_backtest)** |
| Screener Pro | 1 (run_screener) | **15 (All individual screen_* functions)** |
| News Brain | 2 (breaking, latest) | **5 (Stock news, Sector news, Sentiment score, Parse request, Handle command)** |
| Prediction Tracker | 1 (get_accuracy_report) | **3 (record_prediction, verify_predictions, format_accuracy_report)** |
| Risk Manager | 1 (calculate_position_size basic) | **7 (Kelly criterion, Investment plan, Trailing SL, Risk-reward, Drawdown tracker, Format report)** |
| Cross-Asset Engine | 0 | **4 (scan_all_correlations, get_correlation_insight, format_report, compute_correlation)** |
| Market Brain | 0 | **4 (analyze_indian_stock_deep, generate_conclusion, detect_market_type, format report)** |
| Super Brain | 1 (get_market_intelligence) | **4 (format_jarvis_briefing, fetch_all_news, format_news_digest, jarvis_route_command)** |
| Nifty Super Brain | 7 (FII/DII, VIX, PCR, Pivots, Gift, Sectors, OI) | **2 (get_ai_market_verdict, get_super_brain_analysis — AI LLM verdict)** |
| Options Engine | 2 (chain, recommend_strategy) | **6 (Straddle, Strangle, Bull Call Spread, Bear Put Spread, Iron Condor, IV Rank)** |
| Nifty Options Hunter | 3 (budget, morning, positions) | **3 (track_position, check_position_guardian, close_tracked_position)** |
| Indian Stock Engine | 3 (market status, super analysis, holidays) | **2 (recommend_best_options standalone, _suggest_strategy)** |

### **Total: ~71 powerful functions NOT yet exposed as API endpoints**

---

## 🎯 CATEGORY 1: FUTURES BRAIN (jarvis_futures_brain.py — 673 lines)
> **Currently connected:** `get_india_vix()`, `get_futures_dashboard()` (strings only)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `get_pcr()` | `(symbol="NIFTY") → Dict` | **Live PCR from NSE** — PCR OI, PCR Volume, PCR Change OI, interpretation |
| `get_max_pain()` | `(symbol="NIFTY") → Dict` | **Max Pain calculation** — max pain strike, current price, distance %, direction |
| `get_futures_basis()` | `(symbol="NIFTY") → Dict` | **Futures premium/discount** — spot vs synthetic futures, basis %, bull/bear sentiment |
| `get_straddle_premium()` | `(symbol="NIFTY") → Dict` | **ATM straddle premium** — CE+PE premium, premium %, expected range for today |
| `get_oi_distribution()` | `(symbol="NIFTY") → Dict` | **OI-based support/resistance** — max CE OI (resistance), max PE OI (support), top 5 levels |
| `handle_futures_command()` | `(text) → str` | NLP command router for futures queries |

**🔴 Impact: These are CORE F&O intelligence — PCR, Max Pain, Basis, Straddle Premium are what pro traders need!**

---

## 🎯 CATEGORY 2: OPTIONS PRO (jarvis_options_pro.py — 717 lines)
> **Currently connected:** NOTHING from this file

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `get_strike_price()` | `(symbol, strike, option_type="CE") → Dict` | **Exact real-time strike price** — LTP, IV, OI, Volume, Greeks, recommendation with Entry/SL/Target |
| `get_nearby_options()` | `(symbol, count=10) → Dict` | **Options near ATM** — N strikes around ATM with all data |
| `get_full_chain_summary()` | `(symbol) → Dict` | **Complete chain summary** — top CE/PE writers, OI buildup, ATM straddle, PCR, max pain in one call |
| `_generate_recommendation()` | `(...) → Dict` | **Pro Buy/Sell/Avoid** recommendation with confidence, reasons, risk-reward |
| `parse_option_query()` | `(text) → Dict` | NLP parser: "NIFTY 25000 CE" → structured query |
| `format_strike_result()` | `(data) → str` | Beautiful formatted output |

**🔴 Impact: This is the "Boss asks NIFTY 25950 CE kya hai?" engine. Critical for options traders!**

---

## 🎯 CATEGORY 3: INTRADAY SCANNER (jarvis_intraday_scanner.py — 410 lines)
> **Currently connected:** NOTHING from this file  
> **Universe:** 50 NIFTY stocks scanned in real-time

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `run_intraday_scan()` | `(stocks=None) → str` | **Full intraday scan** — breakouts, volume spikes, momentum across 50 stocks with multi-threading |
| `scan_breakouts()` | `() → str` | **Breakout-only scanner** — VWAP, SMA, high/low breakouts |
| `scan_volume_spikes()` | `() → str` | **Volume explosion** detector — 2x+ average volume alerts |
| `scan_momentum()` | `() → str` | **Biggest movers right now** — top momentum stocks |
| `_detect_breakout()` | `(stock, intra, daily) → Dict` | Core breakout detection (VWAP, SMA, ORB, RSI extreme, MACD crossover) |

**🔴 Impact: Real-time LIVE intraday scanning is THE killer feature for active traders!**

---

## 🎯 CATEGORY 4: BACKTESTER PRO (jarvis_backtester_pro.py — 575 lines)
> **Currently connected:** `handle_backtest_command()` (natural language only)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `backtest_rsi_strategy()` | `(symbol="NIFTY", period="1y") → str` | **Pre-built RSI backtest** — 1-click RSI strategy backtest |
| `backtest_macd_strategy()` | `(symbol="NIFTY", period="1y") → str` | **Pre-built MACD backtest** — 1-click MACD crossover backtest |
| `backtest_bollinger_strategy()` | `(symbol="NIFTY", period="1y") → str` | **Pre-built BB backtest** — 1-click Bollinger Bands backtest |
| `run_backtest()` | `(strategy: Dict) → Dict` | **Programmatic backtest** — returns structured results (trades, win rate, P&L, Sharpe, max drawdown) |
| `parse_strategy()` | `(text) → Dict` | Parse NL strategy to structured format |
| `format_backtest_result()` | `(result: Dict) → str` | Format backtest results |

**🔴 Impact: Pre-built strategy backtests would let users 1-click test popular strategies!**

---

## 🎯 CATEGORY 5: SCREENER PRO (jarvis_screener_pro.py — 540+ lines)
> **Currently connected:** `run_screener()` (generic)

### ❌ NOT CONNECTED (individual screeners):

| Function | Signature | What it does |
|----------|-----------|-------------|
| `screen_oversold()` | `() → str` | RSI < 30 oversold stocks |
| `screen_overbought()` | `() → str` | RSI > 70 overbought stocks |
| `screen_volume_spike()` | `() → str` | 2x+ volume breakout stocks |
| `screen_gap_ups()` | `() → str` | Gap-up stocks at open |
| `screen_top_momentum()` | `() → str` | Top 10 momentum stocks |
| `screen_52week_high()` | `() → str` | Stocks at 52-week high |
| `screen_strong_bullish()` | `() → str` | Strong bullish trend stocks |
| `screen_rsi_oversold()` | `(analyses, threshold) → List` | Filter RSI oversold |
| `screen_rsi_overbought()` | `(analyses, threshold) → List` | Filter RSI overbought |
| `screen_volume_breakout()` | `(analyses, min_ratio) → List` | Volume breakout filter |
| `screen_gap_up()` / `screen_gap_down()` | `(analyses) → List` | Gap detection |
| `screen_52w_high()` / `screen_52w_low()` | `(analyses) → List` | 52-week extremes |
| `screen_golden_cross()` | `(analyses) → List` | Golden cross (SMA 50 > 200) |
| `screen_death_cross()` | `(analyses) → List` | Death cross (SMA 50 < 200) |
| `screen_macd_bullish()` | `(analyses) → List` | MACD bullish crossover |

**🔴 Impact: Individual screener buttons in the app would be extremely powerful for stock picking!**

---

## 🎯 CATEGORY 6: NEWS BRAIN (jarvis_news_brain.py — 520+ lines)
> **Currently connected:** `get_breaking_news()`, `get_latest_news()` (via dashboard helper)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `get_stock_news()` | `(stock) → str` | **Stock-specific news** — news for RELIANCE, TCS etc. with sentiment |
| `get_sector_news()` | `(sector) → str` | **Sector news** — pharma, banking, IT, auto, metal sector focus |
| `get_news_sentiment_score()` | `() → Dict` | **Overall market sentiment** from news — BULLISH/BEARISH/NEUTRAL with score |
| `format_stock_news()` | `(stock) → str` | Formatted stock news with sentiment emoji + impact bar |
| `handle_news_command()` | `(text) → str` | NLP news command handler |

**🔴 Impact: Stock-specific and sector news with sentiment scoring is critical for informed trading!**

---

## 🎯 CATEGORY 7: PREDICTION TRACKER (prediction_tracker.py — 350 lines)
> **Currently connected:** `get_accuracy_report()` (basic)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `record_prediction()` | `(symbol, direction, confidence, ...) → str` | **Record a prediction** for future accuracy tracking |
| `verify_predictions()` | `(max_age_hours=72) → Dict` | **Auto-verify** predictions against actual market data |
| `format_accuracy_report()` | `(report) → str` | **Formatted accuracy** with by-model and by-symbol breakdown |

**🔴 Impact: Showing verified prediction accuracy builds massive trust! "JARVIS was 73% accurate last week"**

---

## 🎯 CATEGORY 8: RISK MANAGER (risk_manager.py — 488 lines)
> **Currently connected:** `calculate_position_size()` (basic, 2 params only)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `kelly_criterion()` | `(win_rate, avg_win, avg_loss) → Dict` | **Kelly Criterion** — optimal position sizing (kelly%, half-kelly%, quarter-kelly%) |
| `kelly_from_real_trades()` | `() → Dict` | **Auto Kelly** from actual trade accuracy — self-learning position sizing |
| `calculate_position_size()` | `(capital, risk_pct, entry, sl, index) → Dict` | **FULL position sizing** — lots, qty, total cost, risk ₹, risk % (currently only basic used) |
| `calculate_investment_plan()` | `(amount, index_price, premium, ...) → Dict` | **Investment calculator** — ₹2K to ₹1L plans with scenario analysis (+0.25% to +3.0% moves) |
| `TrailingStopLoss` class | `.update(price) → Dict` | **Dynamic trailing SL** — auto-adjusts SL as price moves, ATR-based |
| `calculate_risk_reward()` | `(entry, sl, target1, t2, t3) → Dict` | **Risk-reward calculator** — RR ratio, required win rate, TAKE/SKIP recommendation |
| `DrawdownTracker` class | `.record_trade(pnl) → Dict` | **Drawdown tracking** — peak capital, max drawdown %, daily loss limit, auto-lock |
| `format_risk_report()` | `(...) → str` | Comprehensive risk report combining all above |

**🔴 Impact: Risk management is what separates pros from gamblers. Kelly, Trailing SL, and Drawdown tracking are MUST-HAVEs!**

---

## 🎯 CATEGORY 9: CROSS-ASSET ENGINE (cross_asset_engine.py — 354 lines)
> **Currently connected:** NOTHING from this file

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `scan_all_correlations()` | `(include_crypto=True, include_stocks=True) → Dict` | **Full correlation matrix** — BTC/ETH, NIFTY/S&P500, Gold/Dollar, cross-asset pairs with divergence alerts |
| `compute_correlation()` | `(prices_a, prices_b) → Dict` | Pearson + rolling correlation with divergence detection |
| `get_correlation_insight()` | `(symbol) → str` | **Per-symbol correlation** insight: "BTC diverging from ETH — unusual" |
| `format_correlation_report()` | `() → str` | Beautiful correlation report with regime (RISK_ON/RISK_OFF/ROTATION) |

**🔴 Impact: Cross-asset correlation is institutional-level intelligence. "NIFTY is inversely correlated with DXY" insights are gold!**

---

## 🎯 CATEGORY 10: MARKET BRAIN (jarvis_market_brain.py — 1412 lines)
> **Currently connected:** Only `analyze_crypto_token_deep()` used in /analyze endpoint

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `analyze_indian_stock_deep()` | `(query) → Dict` | **DEEP Indian stock analysis** — candles + ML + sentiment + option chain + AI conclusion combined |
| `generate_indian_market_conclusion()` | `(data) → Dict` | **AI trading conclusion** — aggregates ALL data → BUY CE/PE/CASH verdict |
| `detect_market_type()` | `(text) → str` | Detect if query is about Indian stocks vs crypto |
| `format_indian_stock_report()` | `(data) → List[str]` | Multi-page formatted Indian stock report |
| `format_indian_stock_voice()` | `(data) → str` | Voice-friendly Indian market summary |

**🔴 Impact: This is the BRAIN that combines everything — calling `analyze_indian_stock_deep("NIFTY")` gives the most comprehensive analysis possible!**

---

## 🎯 CATEGORY 11: SUPER BRAIN (jarvis_super_brain.py — 690+ lines)
> **Currently connected:** `get_market_intelligence()` (basic)

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `fetch_all_news()` | `(force=False) → Dict[str, List]` | **All news by category** — markets, crypto, India, global, economy |
| `format_news_digest()` | `(categories=None) → str` | Formatted multi-category news digest |
| `format_jarvis_briefing()` | `() → str` | **Complete morning briefing** — market intelligence + news + signals combined |

---

## 🎯 CATEGORY 12: NIFTY SUPER BRAIN — AI VERDICT (nifty_super_brain.py — 1215 lines)
> **Currently connected:** FII/DII, VIX, PCR, Pivots, Gift, Sectors, OI, Dashboard, Super Analysis

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `get_ai_market_verdict()` | `(dashboard_text=None) → str` | **🧠 AI LLM VERDICT** — feeds ALL dashboard data to Groq/Gemini LLM → expert trading advice with exact strike/entry/SL/target |
| `get_super_brain_analysis()` | `(index="NIFTY") → str` | **ULTIMATE**: Dashboard + AI Verdict combined in one call |

**🔴 Impact: This is THE most powerful function — it uses Groq LLM (free) to analyze all data and give specific trades!**

---

## 🎯 CATEGORY 13: OPTIONS ENGINE — Strategy Builders (options_engine.py — 892 lines)
> **Currently connected:** `generate_option_chain()`, `recommend_strategy()`, `calculate_iv_rank_percentile()`

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `build_straddle()` | `(symbol="NIFTY") → OptionStrategy` | **Long Straddle** — ATM CE + PE, breakevens, max loss, margin |
| `build_strangle()` | `(symbol="NIFTY", otm_steps=2) → OptionStrategy` | **Long Strangle** — OTM CE + PE, cheaper than straddle |
| `build_bull_call_spread()` | `(symbol="NIFTY", spread_width=2) → OptionStrategy` | **Bull Call Spread** — limited risk bullish trade |
| `build_bear_put_spread()` | `(symbol="NIFTY", spread_width=2) → OptionStrategy` | **Bear Put Spread** — limited risk bearish trade |
| `build_iron_condor()` | `(symbol="NIFTY", wing_width=3) → OptionStrategy` | **Iron Condor** — range-bound income strategy |
| `calculate_greeks()` | `(S, K, T, r, sigma, opt_type) → OptionStrike` | **All Greeks** — Delta, Gamma, Theta, Vega for any option |

**🔴 Impact: Individual strategy builders let users construct ANY option strategy with exact legs, P&L, breakevens!**

---

## 🎯 CATEGORY 14: OPTIONS HUNTER — Position Tracking (nifty_options_hunter.py — 1100 lines)
> **Currently connected:** `find_budget_options()`, `generate_morning_picks()`, `get_my_positions_enhanced()`

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `track_position()` | `(chat_id, index, strike, opt_type, entry_price, ...) → Dict` | **Track a live option position** with auto SL/target monitoring |
| `check_position_guardian()` | `(position, current_spot) → Dict` | **Position guardian** — auto-checks if SL/target hit, generates alerts |
| `close_tracked_position()` | `(chat_id, pos_id, exit_price) → str` | **Close position** with P&L calculation |

**🔴 Impact: Position tracking with auto-guardian alerts is what makes this a REAL trading platform!**

---

## 🎯 CATEGORY 15: GLOBAL CANDLE ENGINE — Regional Markets (global_candle_engine.py — 560 lines)
> **Currently connected:** `analyze_all_global_markets()`, `get_india_prediction_from_global()`

### ❌ NOT CONNECTED:

| Function | Signature | What it does |
|----------|-----------|-------------|
| `analyze_us_markets()` | `() → List[GlobalSignal]` | **US markets only** — S&P 500, NASDAQ, Dow Jones |
| `analyze_european_markets()` | `() → List[GlobalSignal]` | **European markets** — FTSE, DAX, CAC 40 |
| `analyze_asian_markets()` | `() → List[GlobalSignal]` | **Asian markets** — Nikkei, Hang Seng, Shanghai |
| `analyze_commodities()` | `() → List[GlobalSignal]` | **Commodities** — Gold, Crude Oil, Silver, Copper |

**🟡 Impact: Regional breakdowns are nice-to-have for detailed global view.**

---

## 🎯 TOP 20 HIGHEST-IMPACT FUNCTIONS TO CONNECT FIRST

| Priority | Function | File | Why |
|:--------:|----------|------|-----|
| 1 | `get_ai_market_verdict()` | nifty_super_brain.py | **THE AI LLM verdict with exact trades — users will LOVE this** |
| 2 | `run_intraday_scan()` | jarvis_intraday_scanner.py | **Real-time breakout/momentum scanner for 50 stocks** |
| 3 | `get_strike_price()` | jarvis_options_pro.py | **"NIFTY 25000 CE kya hai?" — exact LTP + recommendation** |
| 4 | `scan_all_correlations()` | cross_asset_engine.py | **Cross-asset intelligence — institutional-level** |
| 5 | `get_pcr()` | jarvis_futures_brain.py | **Live PCR — #1 most requested by options traders** |
| 6 | `get_max_pain()` | jarvis_futures_brain.py | **Max Pain — every expiry day traders need this** |
| 7 | `build_straddle/strangle/spread/condor()` | options_engine.py | **Strategy builders with P&L profile** |
| 8 | `get_straddle_premium()` | jarvis_futures_brain.py | **Today's expected range** |
| 9 | `calculate_risk_reward()` | risk_manager.py | **RR calculator — pro trading essential** |
| 10 | `kelly_criterion()` | risk_manager.py | **Optimal position sizing** |
| 11 | `get_full_chain_summary()` | jarvis_options_pro.py | **1-call complete chain data** |
| 12 | `analyze_indian_stock_deep()` | jarvis_market_brain.py | **Deep combined analysis engine** |
| 13 | `screen_oversold/overbought/momentum()` | jarvis_screener_pro.py | **Individual screener buttons** |
| 14 | `scan_volume_spikes()` | jarvis_intraday_scanner.py | **Volume explosion alerts** |
| 15 | `get_stock_news()` | jarvis_news_brain.py | **Stock-specific news with sentiment** |
| 16 | `get_news_sentiment_score()` | jarvis_news_brain.py | **Overall market news sentiment** |
| 17 | `calculate_investment_plan()` | risk_manager.py | **₹2K-₹1L scenario calculator** |
| 18 | `track_position()` | nifty_options_hunter.py | **Position tracking with guardian** |
| 19 | `backtest_rsi/macd/bollinger()` | jarvis_backtester_pro.py | **1-click pre-built backtests** |
| 20 | `verify_predictions()` | prediction_tracker.py | **Auto-verify prediction accuracy** |

---

## 📐 SUGGESTED NEW API ENDPOINTS

```
# FUTURES INTELLIGENCE
GET  /api/miniapp/futures/pcr?symbol=NIFTY          → get_pcr()
GET  /api/miniapp/futures/max-pain?symbol=NIFTY      → get_max_pain()
GET  /api/miniapp/futures/basis?symbol=NIFTY          → get_futures_basis()
GET  /api/miniapp/futures/straddle?symbol=NIFTY       → get_straddle_premium()
GET  /api/miniapp/futures/oi-levels?symbol=NIFTY      → get_oi_distribution()

# OPTIONS PRO
GET  /api/miniapp/options/strike?symbol=NIFTY&strike=25000&type=CE  → get_strike_price()
GET  /api/miniapp/options/nearby?symbol=NIFTY&count=10              → get_nearby_options()
GET  /api/miniapp/options/chain-summary?symbol=NIFTY                → get_full_chain_summary()

# STRATEGY BUILDERS
GET  /api/miniapp/options/straddle?symbol=NIFTY     → build_straddle()
GET  /api/miniapp/options/strangle?symbol=NIFTY     → build_strangle()
GET  /api/miniapp/options/bull-spread?symbol=NIFTY  → build_bull_call_spread()
GET  /api/miniapp/options/bear-spread?symbol=NIFTY  → build_bear_put_spread()
GET  /api/miniapp/options/iron-condor?symbol=NIFTY  → build_iron_condor()
GET  /api/miniapp/options/greeks?S=24000&K=25000&T=7&sigma=15&type=CE  → calculate_greeks()

# INTRADAY SCANNER
GET  /api/miniapp/intraday/scan          → run_intraday_scan()
GET  /api/miniapp/intraday/breakouts     → scan_breakouts()
GET  /api/miniapp/intraday/volume-spikes → scan_volume_spikes()
GET  /api/miniapp/intraday/momentum      → scan_momentum()

# SCREENER (individual)
GET  /api/miniapp/screener/oversold      → screen_oversold()
GET  /api/miniapp/screener/overbought    → screen_overbought()
GET  /api/miniapp/screener/volume-spike  → screen_volume_spike()
GET  /api/miniapp/screener/gap-ups       → screen_gap_ups()
GET  /api/miniapp/screener/momentum      → screen_top_momentum()
GET  /api/miniapp/screener/52w-high      → screen_52week_high()
GET  /api/miniapp/screener/bullish       → screen_strong_bullish()

# BACKTESTER PRO
GET  /api/miniapp/backtest/rsi?symbol=NIFTY&period=1y       → backtest_rsi_strategy()
GET  /api/miniapp/backtest/macd?symbol=NIFTY&period=1y      → backtest_macd_strategy()
GET  /api/miniapp/backtest/bollinger?symbol=NIFTY&period=1y → backtest_bollinger_strategy()

# NEWS WITH SENTIMENT
GET  /api/miniapp/news/stock?stock=RELIANCE   → get_stock_news()
GET  /api/miniapp/news/sector?sector=banking  → get_sector_news()
GET  /api/miniapp/news/sentiment              → get_news_sentiment_score()

# RISK MANAGEMENT
POST /api/miniapp/risk/kelly           → kelly_criterion()
GET  /api/miniapp/risk/kelly-auto      → kelly_from_real_trades()
POST /api/miniapp/risk/position-size   → calculate_position_size() [full params]
POST /api/miniapp/risk/investment-plan → calculate_investment_plan()
POST /api/miniapp/risk/risk-reward     → calculate_risk_reward()

# CROSS-ASSET CORRELATION
GET  /api/miniapp/correlation/scan     → scan_all_correlations()
GET  /api/miniapp/correlation/insight?symbol=BTC → get_correlation_insight()

# AI SUPER BRAIN
GET  /api/miniapp/ai/verdict           → get_ai_market_verdict()
GET  /api/miniapp/ai/deep-analysis?query=NIFTY  → analyze_indian_stock_deep()
GET  /api/miniapp/ai/briefing          → format_jarvis_briefing()

# PREDICTION TRACKING
POST /api/miniapp/predictions/record   → record_prediction()
POST /api/miniapp/predictions/verify   → verify_predictions()

# POSITION TRACKING
POST /api/miniapp/positions/track      → track_position()
POST /api/miniapp/positions/close      → close_tracked_position()

# GLOBAL REGIONAL
GET  /api/miniapp/global/us            → analyze_us_markets()
GET  /api/miniapp/global/europe        → analyze_european_markets()
GET  /api/miniapp/global/asia          → analyze_asian_markets()
GET  /api/miniapp/global/commodities   → analyze_commodities()
```

---

**Total new endpoints: ~45+**  
**Total untapped functions: ~71**  
**Files already imported in miniapp_api.py but underutilized: 15+**

The backend is MASSIVELY more powerful than what's currently exposed. The mini app is only scratching the surface!
