# JARVIS Trading Server — Deployment Guide

## Z++++ Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                  JARVIS SERVER                       │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Rate     │  │ JWT Auth │  │ Security │          │
│  │ Limiter  │  │ Bcrypt   │  │ Headers  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│  ┌────▼──────────────▼──────────────▼─────┐         │
│  │         FastAPI Application             │         │
│  │                                         │         │
│  │  /api/auth/*      - Authentication      │         │
│  │  /api/ai/chat     - Gemini AI          │         │
│  │  /api/market/*    - Real Market Data    │         │
│  │  /api/portfolio/* - Portfolio Tracking   │         │
│  │  /api/alerts/*    - Price Alerts        │         │
│  │  /api/admin/*     - Admin Panel         │         │
│  └────┬───────────────┬───────────────┬───┘         │
│       │               │               │              │
│  ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐       │
│  │ SQLite   │   │ Gemini   │   │ CoinGecko│       │
│  │ Database │   │ AI API   │   │ Binance  │       │
│  └──────────┘   └──────────┘   └──────────┘       │
└─────────────────────────────────────────────────────┘
```

## Security Layers

1. **JWT Authentication** — HS256, 30-min access tokens, 7-day refresh tokens
2. **Bcrypt Password Hashing** — 12 rounds, industry standard
3. **Rate Limiting** — 100 req/min per IP, auto-block on abuse
4. **Brute Force Protection** — 5 failed attempts = 15-min lockout
5. **Security Headers** — HSTS, X-Frame-Options, CSP, etc.
6. **Input Sanitization** — All user input filtered
7. **SQL Injection Protection** — SQLAlchemy ORM (no raw queries)
8. **Audit Logging** — Every login/action logged
9. **Request Size Limiting** — 10MB max
10. **IP Blocking** — Manual + automatic

## Quick Start

### Local Development
```bash
cd server
pip install -r requirements.txt
cp ../.env .env  # or create with your keys
python main.py
```

### Docker
```bash
cd server
docker-compose up -d
```

### Environment Variables
```env
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional
GROQ_API_KEY=your-groq-key
JWT_SECRET_KEY=auto-generated-if-not-set
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
ENVIRONMENT=production
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=*
```

## API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Login (returns JWT tokens)
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/logout` — Revoke all sessions
- `POST /api/auth/change-password` — Change password
- `GET  /api/auth/me` — Get current user

### AI Chat (Gemini-powered)
- `POST /api/ai/chat` — Chat with JARVIS
- `POST /api/ai/analyze/{symbol}` — AI market analysis
- `POST /api/ai/signal/{symbol}` — AI trading signal
- `GET  /api/ai/history` — Chat history

### Market Data (Real-time)
- `GET /api/market/top` — Top cryptocurrencies
- `GET /api/market/price/{coin_id}` — Detailed coin price
- `GET /api/market/search` — Search coins
- `GET /api/market/trending` — Trending coins
- `GET /api/market/global` — Global market stats
- `GET /api/market/fear-greed` — Fear & Greed Index
- `GET /api/market/history/{coin_id}` — Price history
- `GET /api/market/ticker/{symbol}` — Binance ticker
- `GET /api/market/klines/{symbol}` — Candlestick data
- `GET /api/market/whales` — Whale transactions
- `GET /api/market/dex/search` — DEX token search
- `GET /api/market/dex/new` — New DEX pairs

### Portfolio
- `GET  /api/portfolio` — Get portfolios + holdings
- `POST /api/portfolio/holding` — Add/update holding
- `DELETE /api/portfolio/holding/{id}` — Remove holding
- `POST /api/portfolio/trade` — Record trade
- `GET  /api/portfolio/trades` — Trade history

### Alerts
- `GET    /api/alerts` — Get price alerts
- `POST   /api/alerts` — Create alert
- `DELETE /api/alerts/{id}` — Delete alert

### Admin (requires admin role)
- `GET  /api/admin/users` — List users
- `GET  /api/admin/audit` — Audit log
- `POST /api/admin/block-ip` — Block IP

## Deploy to VPS

```bash
# On your server (Ubuntu)
apt update && apt install docker.io docker-compose -y
git clone https://github.com/DRD8077/jarvis-trading-bot.git
cd jarvis-trading-bot/server

# Set your API keys
echo "GEMINI_API_KEY=your-key" > .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 64)" >> .env

# Deploy
docker-compose up -d

# Server will be at http://your-vps-ip:8000
```

## Connect Mobile App

In the APK build, set the server URL:
```bash
# In telegram-mini-app/.env
VITE_JARVIS_SERVER=http://your-server-ip:8000
```
