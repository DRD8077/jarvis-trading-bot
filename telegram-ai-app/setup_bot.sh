#!/bin/bash

echo "🔑 Telegram Bot Token Setup"
echo "=========================="
echo ""
echo "Please provide your bot token from @BotFather:"
read -p "Bot Token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

# Update the .env file
sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=$BOT_TOKEN/" .env

echo ""
echo "✅ Bot token updated successfully!"
echo ""
echo "🚀 To start your bot with mini app:"
echo "   cd /workspaces/codespaces-blank/telegram-ai-app/bot"
echo "   node bot.js"
echo ""
echo "📱 Your mini app will be visible in the bot's side panel!"
echo ""
echo "🔗 WebApp URL: http://localhost:3000"
echo "👑 Admin Panel: http://localhost:3000/admin.html"