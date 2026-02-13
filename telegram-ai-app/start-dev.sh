#!/bin/bash
echo "🚀 Starting JARVIS AI App (Development)"

# Start backend in background
npm run dev &
BACKEND_PID=$!

# Wait a moment
sleep 2

# Start bot
npm run bot &
BOT_PID=$!

echo "✅ Services started!"
echo "Backend PID: $BACKEND_PID"
echo "Bot PID: $BOT_PID"
echo ""
echo "To stop: kill $BACKEND_PID $BOT_PID"

# Wait for services
wait
