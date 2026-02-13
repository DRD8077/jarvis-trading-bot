#!/bin/bash

echo "🚀 Setting up JARVIS Telegram Bot with Mini App"
echo "=============================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    npm install -g ngrok
fi

echo "🌐 Starting ngrok tunnel for WebApp..."
echo "   This will create a public URL for your mini app"
echo ""

# Start ngrok in background
ngrok http 3000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Please check ngrok installation."
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

echo "✅ Ngrok tunnel created: $NGROK_URL"
echo ""

# Update the .env file with ngrok URL
sed -i "s|WEBAPP_URL=.*|WEBAPP_URL=$NGROK_URL|" bot/.env

echo "🔧 Updated bot/.env with ngrok URL"
echo ""

echo "🤖 Starting JARVIS Telegram Bot..."
echo "   Bot Token: ✅ Configured"
echo "   WebApp URL: $NGROK_URL"
echo ""

# Start the bot
node bot/bot.js

# Cleanup
kill $NGROK_PID 2>/dev/null