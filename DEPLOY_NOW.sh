#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🚀 JARVIS Trading Platform — One-Click Deploy to Fly.io  
# ═══════════════════════════════════════════════════════════
# 
# STEP 1: Login to Fly.io (one time)
#   flyctl auth login
#
# STEP 2: Run this script
#   bash DEPLOY_NOW.sh
#
# STEP 3: Set your domain (davidcrewai.shop)
#   flyctl certs add davidcrewai.shop
#   # Then add CNAME record in GoDaddy:
#   #   Type: CNAME
#   #   Name: @  
#   #   Value: david-crew-bot.fly.dev
#
# ═══════════════════════════════════════════════════════════

set -e
export PATH="/home/codespace/.fly/bin:$PATH"

echo "═══════════════════════════════════════"
echo "  🚀 Deploying JARVIS to Fly.io"
echo "═══════════════════════════════════════"

# Check if logged in
flyctl auth whoami || { echo "❌ Not logged in. Run: flyctl auth login"; exit 1; }

# Set secrets from .env
echo "📦 Setting secrets..."
flyctl secrets set \
  GROQ_API_KEY="$(grep GROQ_API_KEY .env | cut -d= -f2)" \
  OPENAI_API_KEY="$(grep OPENAI_API_KEY .env | cut -d= -f2)" \
  GEMINI_API_KEY="$(grep GEMINI_API_KEY .env | cut -d= -f2)" \
  COINDCX_API_KEY="$(grep COINDCX_API_KEY .env | cut -d= -f2)" \
  COINDCX_SECRET="$(grep COINDCX_SECRET .env | cut -d= -f2)" \
  NEWS_API_KEY="$(grep NEWS_API_KEY .env | cut -d= -f2)" \
  OWNER_CHAT_ID="5647898018" \
  BOT_TOKEN="$(grep BOT_TOKEN telegram-ai-app/.env | cut -d= -f2)" \
  --stage 2>/dev/null || true

# Deploy
echo "🔨 Building & deploying..."
flyctl deploy --remote-only

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ DEPLOYED!"
echo "  🌐 https://david-crew-bot.fly.dev"
echo "  📱 Mini App: https://david-crew-bot.fly.dev/miniapp"
echo "═══════════════════════════════════════"
echo ""
echo "To connect davidcrewai.shop:"
echo "  1. flyctl certs add davidcrewai.shop"  
echo "  2. In GoDaddy DNS, add CNAME: @ → david-crew-bot.fly.dev"
echo "  3. Update bot WEBAPP_URL to https://davidcrewai.shop/miniapp"
