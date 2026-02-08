# 🔱 David Crew Trading Bot — 24/7 Deployment Guide

> **Goal:** Bot runs forever, even when your laptop is OFF or has no internet.

---

## 🏆 Option 1: Railway.app (EASIEST — FREE — Recommended)

Railway gives you a **free cloud server** that runs your bot 24/7.

### Step-by-Step:

1. **Push code to GitHub** (from Codespace terminal):
   ```bash
   git add -A
   git commit -m "Deploy: 24/7 trading bot"
   git push origin main
   ```

2. **Go to** [https://railway.app](https://railway.app) and click **"Start a New Project"**

3. **Click** "Deploy from GitHub Repo" → Select your repo (`codespaces-blank`)

4. **Railway will auto-detect the `Procfile`** and start building

5. **Add Environment Variables** (click your service → Variables tab):
   ```
   TELEGRAM_BOT_TOKEN = <your-bot-token>
   TEST_CHAT_ID = <your-chat-id>
   WATCHLIST = NIFTY,SENSEX
   ```

6. **Click Deploy** — Done! Bot runs 24/7 forever! 🎉

> ⚠️ Railway free tier gives $5/month credit (enough for this bot). Add a credit card for $5 more.

---

## 🥈 Option 2: Render.com (FREE Worker)

1. **Push code to GitHub** (same as above)

2. Go to [https://render.com](https://render.com) → "New" → "Background Worker"

3. Connect your GitHub repo

4. Render auto-detects `render.yaml` — just add env vars:
   ```
   TELEGRAM_BOT_TOKEN = <your-bot-token>
   TEST_CHAT_ID = <your-chat-id>
   ```

5. Click "Create Background Worker" — Bot runs 24/7!

> Render free tier spins down after 15 min of no traffic. Use "Worker" type (not Web Service) — workers don't spin down.

---

## 🥉 Option 3: Fly.io (FREE — Generous Limits)

1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login & Deploy:
   ```bash
   fly auth login
   fly launch    # Follow prompts, say YES to deploy
   fly secrets set TELEGRAM_BOT_TOKEN=<your-bot-token>
   fly secrets set TEST_CHAT_ID=<your-chat-id>
   fly deploy
   ```

3. Bot runs on Fly.io forever!

> Free tier: 3 shared VMs, 256MB RAM each — more than enough.

---

## 🖥️ Option 4: VPS (DigitalOcean / Oracle Cloud FREE)

### Oracle Cloud (ALWAYS FREE forever):

1. Go to [https://cloud.oracle.com](https://cloud.oracle.com) → Create free account
2. Create a **Compute Instance** (Always Free: ARM 4 CPU, 24GB RAM!)
3. SSH into the server:
   ```bash
   ssh ubuntu@YOUR_SERVER_IP
   ```
4. Install Docker:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose git
   sudo systemctl enable docker
   ```
5. Clone and Run:
   ```bash
   git clone https://github.com/YOUR_USERNAME/codespaces-blank.git
   cd codespaces-blank
   
   # Create .env file
   cat > .env << 'EOF'
   TELEGRAM_BOT_TOKEN=<your-bot-token>
   TEST_CHAT_ID=<your-chat-id>
   WATCHLIST=NIFTY,SENSEX
   EOF
   
   # Start bot (runs forever, auto-restarts on crash)
   docker compose up -d --build
   ```

6. Check logs:
   ```bash
   docker compose logs -f bot
   ```

> Oracle Cloud free tier is **truly free forever** — best for permanent hosting.

---

## ⚡ Quick Deploy from Codespace (Right Now)

If you want to deploy RIGHT NOW from this Codespace:

```bash
# 1. Make sure everything is committed
git add -A
git commit -m "🔱 Deploy: 24/7 David Crew Trading Bot"
git push origin main

# 2. Then go to Railway.app or Render.com and connect your GitHub repo
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot stops after Codespace sleeps | Deploy to Railway/Render/Fly (above) |
| "409 Conflict" error | Only ONE instance should run. Stop Codespace bot before deploying |
| Bot not responding | Check logs: `docker compose logs bot` or Railway dashboard |
| Token error | Re-check TELEGRAM_BOT_TOKEN env variable |

---

## 📊 Which Option to Choose?

| Platform | Cost | Difficulty | Best For |
|----------|------|------------|----------|
| **Railway** | Free $5/mo | ⭐ Easy | Quick deploy, beginners |
| **Render** | Free worker | ⭐ Easy | Zero maintenance |
| **Fly.io** | Free tier | ⭐⭐ Medium | More control |
| **Oracle Cloud** | FREE forever | ⭐⭐⭐ Advanced | Permanent server |

**🏆 Recommendation: Start with Railway.app — it takes 5 minutes!**
