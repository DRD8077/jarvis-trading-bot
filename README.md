# 🤖 JARVIS AI Trading Platform v7.0 — "Nuclear"

> **India's Most Powerful AI Trading Bot** — Telegram Bot + Android APK + Admin Panel  
> Built with proper **SDLC** (Software Development Life Cycle) practices

[![CI](https://github.com/DRD8077/jarvis-trading-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/DRD8077/jarvis-trading-bot/actions/workflows/ci.yml)
[![CD](https://github.com/DRD8077/jarvis-trading-bot/actions/workflows/cd.yml/badge.svg)](https://github.com/DRD8077/jarvis-trading-bot/actions/workflows/cd.yml)

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [SDLC Lifecycle](#-sdlc-lifecycle)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Android APK Build](#-android-apk-build)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    JARVIS Trading Platform v7.0                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │  📱 Android  │  │  🤖 Telegram │  │  🖥️  Admin Panel (Web)  │ │
│  │    APK       │  │     Bot      │  │    templates/admin.html  │ │
│  │  Capacitor   │  │  python-tgbot│  │    FastAPI + Jinja2      │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬──────────────┘ │
│         │                 │                       │                │
│         └─────────────────┼───────────────────────┘                │
│                           │                                        │
│  ┌────────────────────────▼────────────────────────────────────┐  │
│  │              FastAPI Server (jarvis_server.py)               │  │
│  │   63 routes │ JWT Auth │ Rate Limiter │ SSE │ Prometheus    │  │
│  └──────┬──────┬──────┬──────┬──────┬──────┬──────┬───────────┘  │
│         │      │      │      │      │      │      │               │
│  ┌──────▼┐ ┌──▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼──┐ ┌▼───┐ ┌▼────────┐    │
│  │Redis  │ │Pgsql│ │JWT │ │SSE │ │ARQ│ │Prom│ │Telegram  │    │
│  │Cache  │ │ DB  │ │Auth│ │Push│ │Que│ │Mtrc│ │Notifier  │    │
│  └───────┘ └─────┘ └────┘ └────┘ └───┘ └────┘ └──────────┘    │
│                                                                  │
│  ┌──────────────────── AI & Trading Engines ──────────────────┐  │
│  │ 🧠 Brain v5    │ 📊 AI Signals  │ 🕯️ Candle Analyzer      │  │
│  │ 🚀 Auto Sniper │ 💰 Buy/Sell    │ 💎 Conqueror Trader     │  │
│  │ 🤖 Mega Trader │ 📈 ML Pipeline │ 🇮🇳 Nifty Super Brain   │  │
│  │ 🌍 Global Mkts │ 🔥 DexTools    │ 🦅 Birdeye              │  │
│  │ 🌐 Social Trade│ 🧪 Backtester  │ 📰 News Brain           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 SDLC Lifecycle

This project follows a **full SDLC** (Software Development Life Cycle):

| Phase | Implementation | Status |
|-------|---------------|--------|
| **1. Planning** | `version.json`, GitHub Issues, this README | ✅ |
| **2. Requirements** | Feature flags in admin panel, `jarvis_config.json` | ✅ |
| **3. Design** | Architecture diagram above, modular engine pattern | ✅ |
| **4. Implementation** | 98K+ lines Python, React+Capacitor Android app | ✅ |
| **5. Testing** | `pytest` test suite, CI pipeline, smoke tests | ✅ |
| **6. Deployment** | GitHub Actions CI/CD, Docker, Fly.io | ✅ |
| **7. Maintenance** | OTA updates, error logging, Prometheus metrics | ✅ |

### CI/CD Pipeline

```
Push/PR → Lint (Ruff) → Tests (Pytest) → Build (Docker) → Security Scan
                                                    ↓
Tag v* → Build APK (Gradle) → Sign → GitHub Release → Deploy (Fly.io)
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Server | **FastAPI** + Uvicorn | Async HTTP, WebSocket, SSE |
| Auth | **PyJWT** + bcrypt | JWT tokens, refresh rotation |
| Cache | **Redis** (memory fallback) | Sub-ms caching, pub/sub |
| Database | **PostgreSQL** (asyncpg) | Persistent data, SQLite fallback |
| Queue | **ARQ** | Background task processing |
| Metrics | **Prometheus** | `/metrics` endpoint |
| Events | **SSE** (sse-starlette) | Real-time push to clients |
| AI | Groq, OpenAI, Gemini, Anthropic | Multi-AI brain |

### Frontend & Mobile
| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | **React 18** + Vite | SPA with hot reload |
| Styling | **TailwindCSS** | Utility-first CSS |
| Charts | **Chart.js** + Recharts | Portfolio P&L, sparklines |
| Android | **Capacitor 8** | Native APK wrapper |
| Offline AI | llama.cpp (GGUF) | On-device LLM |
| Voice | Vosk STT + Edge TTS | Hindi voice assistant |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Container | **Docker** + docker-compose | Redis, PostgreSQL, App |
| CI/CD | **GitHub Actions** | Lint, test, build, deploy |
| Hosting | **Fly.io** (Singapore) | Low-latency Asia |
| Linting | **Ruff** | Fast Python linter |
| Testing | **Pytest** | Unit + integration tests |

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/DRD8077/jarvis-trading-bot.git
cd jarvis-trading-bot
cp .env.example .env   # Add your API keys
```

### 2. Run with Docker (recommended)
```bash
docker compose up -d
# Starts: App + Redis + PostgreSQL
# Admin: http://localhost:8000/admin
# Health: http://localhost:8000/health
```

### 3. Run locally
```bash
pip install -r requirements.txt
uvicorn jarvis_server:app --host 0.0.0.0 --port 8000
```

---

## 📱 Android APK Build

### Quick Build (Debug)
```bash
./build_apk_release.sh
```

### Release Build (Signed)
```bash
./build_apk_release.sh --release
```

### Play Store Bundle (AAB)
```bash
./build_apk_release.sh --release --aab
```

### CI/CD Build
Push a git tag to auto-build:
```bash
git tag v7.0.1
git push origin v7.0.1
# → GitHub Actions builds APK + creates Release
```

### APK Features
- 🧠 **Offline LLM** — llama.cpp with GGUF models (no internet needed)
- 🎙️ **Hindi Voice** — Vosk STT + Edge TTS (sweet personality)
- 📊 **Live Trading** — Real-time signals via SSE push
- 🔄 **OTA Updates** — Auto-update web layer without Play Store
- 🔐 **Biometric Auth** — Fingerprint + device PIN
- 📈 **Chart.js Graphs** — Portfolio P&L with sparklines
- 🌐 **Social Trading** — Share & follow trader signals

---

## 📡 API Reference (63 routes)

### Core
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health + engine status |
| GET | `/admin` | Admin dashboard (web) |
| GET | `/miniapp` | Mini app (mobile) |
| GET | `/metrics` | Prometheus metrics |

### Auth (`/api/auth/`)
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Revoke tokens |

### Admin (`/api/admin/`)
| GET | `/api/admin/overview` | Dashboard stats |
| GET | `/api/admin/users` | All users |
| GET | `/api/admin/engines` | Engine status |
| GET | `/api/admin/errors` | Error log |
| GET | `/api/admin/api-keys` | Key management |
| POST | `/api/admin/broadcast` | Broadcast to all users |

### Trading
| GET | `/api/miniapp/signals` | AI trading signals |
| GET | `/api/miniapp/market` | Market overview |
| GET | `/api/miniapp/portfolio` | Portfolio + P&L |
| POST | `/api/backtest/run` | Strategy backtest |

### Social (`/api/social/`)
| GET | `/api/social/feed` | Signal feed |
| GET | `/api/social/leaderboard` | Top traders |
| POST | `/api/social/share` | Share signal |

### SSE (`/api/sse/`)
| GET | `/api/sse/signals` | Signal stream |
| GET | `/api/sse/all` | All events stream |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Lint check
pip install ruff && ruff check .
```

---

## 🚢 Deployment

### Fly.io (Production)
```bash
fly deploy
fly status
```

### Docker (Self-hosted)
```bash
docker compose up -d --build
```

---

## 📁 Project Structure

```
├── .github/workflows/       # CI/CD pipelines
│   ├── ci.yml               # Lint + Test + Docker build
│   └── cd.yml               # APK build + Deploy
├── tests/                   # Test suite (pytest)
├── telegram-mini-app/       # React + Capacitor (Android)
│   ├── src/                 # React components
│   ├── android/             # Gradle native Android
│   └── dist/                # Built frontend
├── templates/admin.html     # Admin dashboard v7
├── jarvis_server.py         # Main FastAPI server
├── jarvis_brain.py          # AI Brain v5
├── jarvis_jwt_auth.py       # JWT authentication
├── jarvis_redis_cache.py    # Redis cache layer
├── jarvis_database.py       # PostgreSQL + SQLite
├── jarvis_sse.py            # SSE real-time push
├── jarvis_prometheus.py     # Prometheus metrics
├── jarvis_tasks.py          # Background task queue
├── build_apk_release.sh     # Production APK builder
├── docker-compose.yml       # Docker (App+Redis+PG)
├── pyproject.toml           # Python project config
└── version.json             # Semantic versioning
```

---

## 🔐 Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_telegram_id
OWNER_CHAT_ID=your_telegram_id
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://jarvis:jarvis@localhost:5432/jarvis
```

---

**Built with ❤️ by DRD8077 | Jai Mahadev 🙏**
