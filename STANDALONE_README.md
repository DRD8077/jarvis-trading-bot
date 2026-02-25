# 🚀 JARVIS AI Trading Platform — Standalone

**Professional AI-powered trading intelligence platform. Zero Telegram dependency.**

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 JARVIS AI Platform                   │
├──────────────┬──────────────────┬───────────────────┤
│  Android APK │   Web Browser    │   API Clients     │
│  (Capacitor) │   (React SPA)    │   (REST/WS)       │
├──────────────┴──────────────────┴───────────────────┤
│              WebSocket + REST API                    │
│         jarvis_standalone_server.py                  │
├─────────────────────────────────────────────────────┤
│  AI Engine  │ Trading Engine │ Market Data │ Auth   │
│  (Multi-LLM)│ (300+ endpoints)│ (Live)      │ (JWT) │
├──────────────┴──────────────────┴───────────────────┤
│     PostgreSQL      │      Redis Cache              │
└─────────────────────┴───────────────────────────────┘
```

## Quick Start

### Option 1: Local Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start standalone server
./start_standalone.sh

# Open: http://localhost:8000/app
# API Docs: http://localhost:8000/docs
```

### Option 2: Docker (Recommended)
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start everything (server + PostgreSQL + Redis)
docker compose -f docker-compose.standalone.yml up -d

# Open: http://localhost:8000/app
```

### Option 3: Build Android APK
```bash
# Build debug APK
./build_jarvis_apk.sh

# Build release APK (signed)
./build_jarvis_apk.sh release

# Build Play Store AAB
./build_jarvis_apk.sh aab

# Output: dist/JARVIS-AI-v1.0.0.apk
```

## What's Included

### Backend (Python/FastAPI)
| Component | Description |
|-----------|-------------|
| `jarvis_standalone_server.py` | Main standalone server — WebSocket + REST |
| `miniapp_api.py` | 300+ trading API endpoints |
| `jarvis_brain.py` | Multi-model AI brain (Groq/Gemini/OpenAI/Anthropic) |
| `ai_signals.py` | Technical analysis + trading signals |
| `jarvis_jwt_auth.py` | JWT authentication with refresh tokens |
| `jarvis_redis_cache.py` | Redis caching with memory fallback |
| `jarvis_database.py` | PostgreSQL async database |
| `jarvis_sse.py` | Server-Sent Events for real-time push |
| `ml_predictor.py` | ML predictions (XGBoost/LightGBM) |
| `indian_stock_super_engine.py` | Indian stock market analysis |
| `crypto_engine.py` | Crypto market scanning |
| `coindcx_engine.py` | CoinDCX exchange integration |
| `nifty_super_brain.py` | NIFTY/BANKNIFTY options intelligence |

### Frontend (React + Capacitor)
| Component | Description |
|-----------|-------------|
| Dashboard | Portfolio overview, signals, market movers |
| AI Chat | Multi-model streaming AI chat |
| Trading | Live trading interface |
| Options Chain | Real-time options data |
| Screener | Stock/crypto screener with filters |
| Backtester | Strategy backtesting |
| Voice AI | Hindi/English voice assistant |
| Offline AI | On-device LLM (llama.cpp) |
| Paper Trading | Virtual ₹10L practice mode |

### Real-Time Features
- **WebSocket** — Live price streaming at `/ws`
- **SSE** — Server-sent events at `/api/sse/subscribe`
- **Push Notifications** — Firebase Cloud Messaging (replaces Telegram)
- **Background Alerts** — Automated price alert monitoring

## API Endpoints

### Authentication
```
POST /api/auth/register    — Create account
POST /api/auth/login       — Login (returns JWT)
POST /api/auth/refresh     — Refresh access token
POST /api/auth/logout      — Logout
```

### AI Chat
```
POST /api/chat             — AI chat (multi-model)
GET  /api/chat/stream      — Streaming AI response (SSE)
```

### Market Data
```
GET  /api/miniapp/dashboard    — Full dashboard data
GET  /api/miniapp/ticker       — Ultra-fast price ticker
GET  /api/miniapp/price/{sym}  — Single symbol price
GET  /api/miniapp/markets      — All markets overview
```

### Trading Signals
```
GET  /api/miniapp/signals/quick/{sym}  — Quick signal
GET  /api/miniapp/signals/full/{sym}   — Full technical analysis
GET  /api/miniapp/screener/{type}      — Run screener
```

### Indian Stocks
```
GET  /api/miniapp/india/dashboard      — India market dashboard
GET  /api/miniapp/india/nifty-options  — NIFTY options chain
GET  /api/miniapp/futures/dashboard    — Futures dashboard
```

### WebSocket
```
ws://host/ws           — Main WebSocket (all broadcasts)
ws://host/ws/prices    — Live price updates
ws://host/ws/signals   — Trading signal alerts
ws://host/ws/user/{id} — User-specific alerts
```

### Push Notifications
```
POST /api/push/register    — Register FCM device token
POST /api/push/send        — Send notification to user
POST /api/push/broadcast   — Broadcast to all devices
```

## Configuration

### Required API Keys (at least one AI key)
| Key | Provider | Purpose |
|-----|----------|---------|
| `GROQ_API_KEY` | Groq | Fast AI chat (recommended) |
| `GEMINI_API_KEY` | Google | Gemini AI chat |
| `OPENAI_API_KEY` | OpenAI | GPT AI chat |
| `ANTHROPIC_API_KEY` | Anthropic | Claude AI chat |

### Optional Keys
| Key | Purpose |
|-----|---------|
| `COINDCX_API_KEY` | Crypto exchange trading |
| `ANGELONE_API_KEY` | Indian stock broker |
| `DEXTOOLS_API_KEY` | DEX pair explorer |
| `BIRDEYE_API_KEY` | Solana DEX data |
| `FCM_SERVER_KEY` | Firebase push notifications |

### Infrastructure
| Key | Default | Purpose |
|-----|---------|---------|
| `REDIS_URL` | `redis://localhost:6379/0` | Cache (optional, falls back to memory) |
| `DATABASE_URL` | `postgresql://jarvis:jarvis@localhost:5432/jarvis` | Database (optional) |
| `PORT` | `8000` | Server port |

## Deployment

### Railway
```bash
# Deploy to Railway
railway init
railway up
```

### Fly.io
```bash
fly launch --config fly.standalone.toml
fly deploy
```

### Docker (Self-hosted)
```bash
docker compose -f docker-compose.standalone.yml up -d
```

### APK Distribution
```bash
# Build APK with your server URL baked in
JARVIS_SERVER_URL=https://your-server.com ./build_jarvis_apk.sh release

# Install on Android device
adb install -r dist/JARVIS-AI-v1.0.0.apk
```

## File Structure

```
├── jarvis_standalone_server.py     # ← Main standalone server
├── start_standalone.sh             # ← Start script
├── build_jarvis_apk.sh             # ← APK builder
├── Dockerfile.standalone           # ← Docker image
├── docker-compose.standalone.yml   # ← Full stack (server+DB+Redis)
├── fly.standalone.toml             # ← Fly.io deployment
├── requirements.txt                # ← Python dependencies
├── .env.example                    # ← Environment template
├── miniapp_api.py                  # ← 300+ trading endpoints
├── jarvis_brain.py                 # ← AI brain engine
├── telegram-mini-app/              # ← React frontend source
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/             # ← 50+ UI components
│   │   └── services/               # ← 46 service modules
│   ├── capacitor.config.json
│   └── dist/                       # ← Built frontend
└── *.py                            # ← 137 Python engine modules
```

## No Telegram Dependency

This platform is **100% standalone**:
- ✅ Own JWT authentication (no Telegram login required)
- ✅ Firebase push notifications (not Telegram bot push)
- ✅ WebSocket real-time data (not Telegram WebApp)
- ✅ React SPA served directly (not Telegram Mini App)
- ✅ Android APK via Capacitor (not Telegram WebApp wrapper)
- ✅ REST API accessible from any client
