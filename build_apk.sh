#!/bin/bash
# ═══════════════════════════════════════════════
#   JARVIS Trading - Build APK Script
# ═══════════════════════════════════════════════
set -e

PROJ_DIR="/workspaces/codespaces-blank/telegram-mini-app"
ANDROID_DIR="$PROJ_DIR/android"
APK_OUTPUT="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
APK_DEST="$PROJ_DIR/dist/jarvis-trading.apk"

export JAVA_HOME=/usr/local/sdkman/candidates/java/21.0.9-ms
export ANDROID_HOME=$HOME/android-sdk

echo "🔨 Building React frontend..."
cd "$PROJ_DIR"
npm run build

echo "📱 Syncing with Android..."
npx cap sync android

echo "🏗️ Building APK..."
cd "$ANDROID_DIR"
./gradlew assembleDebug

echo "📦 Copying APK to dist..."
cp "$APK_OUTPUT" "$APK_DEST"

APK_SIZE=$(ls -lh "$APK_DEST" | awk '{print $5}')
echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ APK Built Successfully!"
echo "  📏 Size: $APK_SIZE"
echo "  📂 File: $APK_DEST"
echo "  🌐 Download: /download/apk"
echo "═══════════════════════════════════════════════"
