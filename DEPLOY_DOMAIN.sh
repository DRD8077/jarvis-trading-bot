#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🚀 JARVIS — Deploy to davidcrewai.shop
#  Run: bash DEPLOY_DOMAIN.sh
# ═══════════════════════════════════════════════════════════
set -e

DOMAIN="davidcrewai.shop"
APP="david-crew-bot"
REGION="sin"

echo "═══════════════════════════════════════"
echo "  🚀 Deploying JARVIS to $DOMAIN"
echo "═══════════════════════════════════════"

# ═══ Step 1: Login to Fly.io ═══
echo ""
echo "📌 Step 1: Authenticate with Fly.io"
echo "────────────────────────────────────"
if ! flyctl auth whoami &>/dev/null; then
    echo "🔑 Opening Fly.io login..."
    flyctl auth login
fi
echo "✅ Authenticated as: $(flyctl auth whoami)"

# ═══ Step 2: Create app if needed ═══
echo ""
echo "📌 Step 2: Create app '$APP'"
echo "────────────────────────────────────"
if flyctl apps list | grep -q "$APP"; then
    echo "✅ App '$APP' already exists"
else
    flyctl apps create "$APP" --region "$REGION"
    echo "✅ App '$APP' created in $REGION"
fi

# ═══ Step 3: Set secrets ═══
echo ""
echo "📌 Step 3: Setting secrets..."
echo "────────────────────────────────────"
flyctl secrets set \
    TELEGRAM_BOT_TOKEN="7897330325:AAF0opOkFdu0AiZk-tGAF_oGPrY5KMzjazE" \
    ADMIN_CHAT_ID="5647898018" \
    OWNER_CHAT_ID="5647898018" \
    GROQ_API_KEY="$(grep GROQ_API_KEY .env | cut -d= -f2)" \
    OPENAI_API_KEY="$(grep OPENAI_API_KEY .env | cut -d= -f2)" \
    GEMINI_API_KEY="$(grep GEMINI_API_KEY .env | cut -d= -f2)" \
    COINDCX_API_KEY="$(grep COINDCX_API_KEY .env | cut -d= -f2)" \
    NEWS_API_KEY="$(grep NEWS_API_KEY .env | cut -d= -f2)" \
    STABILITY_API_KEY="$(grep STABILITY_API_KEY .env | cut -d= -f2)" \
    GOOGLE_API_KEY="$(grep GOOGLE_API_KEY .env | cut -d= -f2)" \
    WEBAPP_URL="https://${DOMAIN}/miniapp" \
    MINI_APP_URL="https://${DOMAIN}/miniapp" \
    --app "$APP" 2>/dev/null || true
echo "✅ Secrets configured"

# ═══ Step 4: Deploy ═══
echo ""
echo "📌 Step 4: Deploying to Fly.io..."
echo "────────────────────────────────────"
flyctl deploy --app "$APP" --region "$REGION" --remote-only
echo "✅ Deployed!"

# ═══ Step 5: Add custom domain ═══
echo ""
echo "📌 Step 5: Adding custom domain: $DOMAIN"
echo "────────────────────────────────────"
flyctl certs create "$DOMAIN" --app "$APP" 2>/dev/null || true
flyctl certs show "$DOMAIN" --app "$APP" 2>/dev/null
echo ""
echo "✅ SSL certificate requested for $DOMAIN"

# ═══ Step 6: DNS Instructions ═══
echo ""
echo "═══════════════════════════════════════════════"
echo "  📋 DNS SETUP (GoDaddy)"
echo "═══════════════════════════════════════════════"
echo ""
echo "  Go to: https://dcc.godaddy.com/manage/$DOMAIN/dns"
echo ""
echo "  1. DELETE all existing A records"
echo "  2. ADD a CNAME record:"
echo "     ┌──────────────────────────────────────┐"
echo "     │  Type:  CNAME                        │"
echo "     │  Name:  @                            │"
echo "     │  Value: ${APP}.fly.dev               │"
echo "     │  TTL:   600                          │"
echo "     └──────────────────────────────────────┘"
echo ""
echo "  3. If CNAME for @ isn't supported, use:"
echo "     ┌──────────────────────────────────────┐"
echo "     │  Type:  A                            │"
echo "     │  Name:  @                            │"
echo "     │  Value: (run: dig ${APP}.fly.dev +short) │"
echo "     └──────────────────────────────────────┘"
echo ""
FLY_IP=$(dig "${APP}.fly.dev" +short 2>/dev/null | head -1)
if [ -n "$FLY_IP" ]; then
    echo "  Fly.io IP: $FLY_IP"
fi
echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo "═══════════════════════════════════════════════"
echo "  App:    https://${APP}.fly.dev"
echo "  Domain: https://${DOMAIN}"
echo "  Mini:   https://${DOMAIN}/miniapp"
echo "  Health: https://${DOMAIN}/api/miniapp/health"
echo "  Bot:    @David_crew_bot"
echo "═══════════════════════════════════════════════"
