# 🧠 JARVIS v7.0 — LLM-Powered Improvement Roadmap

> **AI-Generated Analysis** of the entire 98K+ line codebase  
> Prioritized by impact, feasibility, and ROI

---

## 🔴 CRITICAL (Do Now — Production Blockers)

### 1. Security Hardening
| Issue | Impact | Fix |
|-------|--------|-----|
| Keystore password hardcoded in `build.gradle` | 🔒 Anyone can sign fake APKs | Move to `$KEYSTORE_PASSWORD` env var or GitHub Secrets |
| `.env` not confirmed in `.gitignore` | 🔥 API keys leaked | Verify `.gitignore` has `.env`, `*.keystore`, wallets |
| No HTTPS enforcement on API | 🔥 MITM attacks | Add `TrustedHostMiddleware` in FastAPI |
| JWT secret auto-generated (volatile) | ⚠️ Tokens invalidate on restart | Set `JWT_SECRET` in `.env` and persist |

### 2. Dead URLs in Config
| File | Issue | Fix |
|------|-------|-----|
| `capacitor.config.json` | ~~Railway URL~~ → ✅ Fixed to `davidcrewai.shop` | Done |
| `server.py` (old) | Still exists, can confuse deployment | Delete or rename |
| `Procfile` | May point to old Flask `server.py` | Update to `uvicorn jarvis_server:app` |

### 3. Database Migration Scripts
- **No Alembic or migration system** — schema changes require manual SQL
- **Fix**: Add `alembic` for PostgreSQL schema versioning
- **Priority**: HIGH (data loss risk on schema changes)

---

## 🟡 HIGH PRIORITY (Next Sprint)

### 4. Code Consolidation — Remove Duplicates
You have **multiple duplicate files** — each wasting memory and causing confusion:

| Keep | Remove/Merge | Savings |
|------|-------------|---------|
| `jarvis_server.py` | `server.py` (1168 lines), `miniapp_api.py` (2261 lines) | 3.4K lines |
| `ml_predictor.py` | `ml_predictor_old.py`, `ml_pipeline_old.py` | 1.8K lines |
| `crypto_engine.py` | `crypto_engine_old.py` | 1K lines |
| `telegram_bot.py` | `telegram_bot_backup.py` | 10K lines |
| `candle_analyzer.py` | `candle_analyzer_old.py` | 800 lines |
| `miniapp_api.py` | 4 backup files (`_v4_backup`, `_v5_backup`, etc.) | 8K lines |

**Total savings: ~25K lines (25% of codebase)**

### 5. Proper Python Package Structure
Current: all 90+ `.py` files in root directory (flat chaos)

Proposed:
```
jarvis/
  __init__.py
  server.py           # Main FastAPI app
  engines/
    __init__.py
    brain.py           # jarvis_brain.py
    signals.py         # ai_signals.py
    sniper.py          # auto_sniper.py
    ...
  services/
    __init__.py
    cache.py           # jarvis_redis_cache.py
    auth.py            # jarvis_jwt_auth.py
    database.py        # jarvis_database.py
    ...
  trading/
    __init__.py
    crypto.py
    stocks.py
    dex.py
    ...
```

### 6. Proper Error Handling in Frontend
- React components lack `ErrorBoundary` per-route
- API calls don't retry on network failure
- **Fix**: Add retry logic with exponential backoff in `api.js`

### 7. Android ProGuard / R8
- `minifyEnabled false` in release build — APK is 32MB
- Enable R8 shrinking → expect 40-60% size reduction (~15MB)
- Add ProGuard rules for Capacitor + llama.cpp

---

## 🟢 MEDIUM PRIORITY (Next Month)

### 8. Offline-First Architecture for APK
- Currently APK is a WebView → **useless offline**
- Add **Service Worker** with `workbox` for offline caching of:
  - Last portfolio data
  - Recent signals (24h)
  - Chat history
  - Hindi voice responses

### 9. React Performance
| Issue | Fix |
|-------|-----|
| 30+ components in flat folder | Organize into feature folders |
| No lazy loading | Add `React.lazy()` for heavy pages (Options, Charts) |
| Bundle is 1MB+ | Code-split with `manualChunks` in Vite (partially done) |
| No memo on lists | `React.memo()` on signal/trade list items |

### 10. WebSocket for Real-Time Prices
- SSE is good for signals, but for **live price tickers** (100+ updates/sec), use WebSocket
- FastAPI already supports WS — add `/ws/prices` endpoint
- Frontend `useRealTime.js` hook already exists but uses polling

### 11. Push Notifications (FCM)
- Currently only Telegram push
- Add **Firebase Cloud Messaging** for APK push notifications
- When signal fires: SSE + Telegram + FCM (triple notification)

### 12. Crash Reporting (Sentry)
- No crash reporting in Python or React or Android
- Add **Sentry SDK** to:
  - `jarvis_server.py` (Python)
  - `main.jsx` (React)  
  - `build.gradle` (Android native)

---

## 🔵 NICE TO HAVE (Future Backlog)

### 13. Multi-Language Support
- Hindi voice works, but UI is English-only
- Add `i18n` with Hindi + English toggle
- Use Gemini for auto-translation

### 14. Dark/Light Theme
- Currently hardcoded dark theme
- Add theme toggle in Settings → store in localStorage

### 15. Automated Trading Paper Mode
- Before real trading: add **paper trading simulation**
- Track P&L without real money
- Build confidence before going live

### 16. Telegram Web App (TWA)
- Currently using Capacitor WebView
- Also release as **Telegram Web App** (no APK install needed)
- API already serves `/miniapp` — just register with BotFather

### 17. AI Model Fine-Tuning
- Current: generic prompts to Groq/OpenAI
- **Fine-tune** a small model on Indian market patterns
- Deploy as GGUF on device via llama.cpp (already have the infrastructure)

### 18. GraphQL API
- REST is fine for now, but for the complex frontend queries:
  - Portfolio + signals + market in one request
  - Subscription for SSE replacement
- Consider **Strawberry GraphQL** (async, works with FastAPI)

---

## 📊 Impact Matrix

```
                    HIGH IMPACT
                         │
     [Security]          │        [Consolidation]
     [DB Migration]      │        [Package Structure]
                         │        [ProGuard]
         ────────────────┼───────────────────
                         │        [Offline-First]
     [Error Handling]    │        [FCM Push]
     [Dead URLs]         │        [WebSocket]
                         │
                    LOW IMPACT
       EASY ─────────────┼──────────── HARD
```

---

## 🏃 Suggested Sprint Plan

### Sprint 1 (This Week)
- [x] Fix security issues (keystore, HTTPS, JWT secret)
- [x] Update dead URLs
- [x] CI/CD pipeline (GitHub Actions)
- [x] Test suite (pytest)
- [ ] Delete duplicate files (25K lines)

### Sprint 2 (Next Week)
- [ ] Enable ProGuard → shrink APK to ~15MB
- [ ] Add Alembic migrations for PostgreSQL
- [ ] React lazy loading + code splitting
- [ ] Service Worker for offline caching

### Sprint 3 (Week 3)
- [ ] Firebase Cloud Messaging (FCM)
- [ ] WebSocket for live prices
- [ ] Sentry crash reporting
- [ ] Package restructure (jarvis/ folder)

### Sprint 4 (Week 4)
- [ ] Hindi UI translation (i18n)
- [ ] Paper trading mode
- [ ] AI model fine-tuning pipeline
- [ ] Play Store preparation (AAB build, listing)

---

## 💡 LLM Analysis Summary

**What you have**: A massively feature-rich trading platform (98K lines) with 12+ AI engines, 63 API routes, Android APK with offline LLM, Hindi voice, social trading.

**What's missing**: SDLC discipline (now added ✅), automated testing (now added ✅), CI/CD (now added ✅), code organization, security hardening, and APK optimization.

**Biggest quick win**: Delete ~25K lines of duplicate/backup files. This alone makes the codebase 25% smaller and eliminates confusion about which file is "real".

**Biggest long-term win**: Move to package structure (`jarvis/`) and enable ProGuard. This transforms the project from "impressive hack" to "production software".

---

*Generated by LLM analysis of the full JARVIS codebase — February 2026*
