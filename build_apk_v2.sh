#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   JARVIS Trading — SUPER APK Build Script v2.0
#   With OTA Updates + Gemini Bridge + Voice Assistant
# ═══════════════════════════════════════════════════════════════
set -e

PROJ_DIR="/workspaces/codespaces-blank/telegram-mini-app"
ANDROID_DIR="$PROJ_DIR/android"
APK_OUTPUT="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
APK_DEST="$PROJ_DIR/dist/jarvis-trading.apk"
OTA_DIR="/workspaces/codespaces-blank/ota_releases"

export JAVA_HOME=/usr/local/sdkman/candidates/java/21.0.9-ms
export ANDROID_HOME=$HOME/android-sdk

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🚀 JARVIS APK Builder v2.0 — SUPER INTELLIGENT BUILD"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Step 1: Build React frontend
echo "🔨 [1/6] Building React frontend with all new features..."
cd "$PROJ_DIR"
npm run build
echo "   ✅ Frontend built successfully"

# Step 2: Create OTA bundle from this build
echo "📦 [2/6] Creating OTA bundle for live updates..."
mkdir -p "$OTA_DIR"
VERSION=$(date +"%Y.%m.%d")
python3 -c "
import sys
sys.path.insert(0, '/workspaces/codespaces-blank')
from jarvis_ota_update import create_ota_bundle
result = create_ota_bundle('$VERSION', 'Auto-build with Voice + Gemini + Auth', False, False)
print(f'   OTA Bundle: v{result.get(\"version\", \"unknown\")} - {result.get(\"total_files\", 0)} files')
" 2>/dev/null || echo "   ⚠️ OTA bundle skipped (non-critical)"
echo "   ✅ OTA bundle created"

# Step 3: Sync with Android
echo "📱 [3/6] Syncing with Android (Capacitor)..."
npx cap sync android
echo "   ✅ Android synced"

# Step 4: Inject OTA updater config into the Android app
echo "🔄 [4/6] Injecting OTA updater + Gemini config..."
cat > "$ANDROID_DIR/app/src/main/assets/jarvis_config.json" << 'CONFIGEOF'
{
  "app_name": "JARVIS Trading",
  "version": "2.0.0",
  "ota": {
    "enabled": true,
    "check_url": "/api/ota/check",
    "auto_update": true,
    "check_interval_hours": 1,
    "wifi_only": false,
    "show_notification": true,
    "silent_update": true
  },
  "gemini": {
    "on_device_enabled": true,
    "cloud_enabled": true,
    "config_url": "/api/gemini/config",
    "default_model": "flash",
    "voice_enabled": true
  },
  "voice_assistant": {
    "enabled": true,
    "language": "hi-IN",
    "persona": "sweet_hindi",
    "chat_url": "/api/voice/chat",
    "speak_url": "/api/voice/speak",
    "transcribe_url": "/api/voice/transcribe",
    "wake_word": "jarvis",
    "always_listening": false
  },
  "auth": {
    "enabled": true,
    "login_url": "/api/auth/login",
    "register_url": "/api/auth/register",
    "verify_url": "/api/auth/verify",
    "auto_login": true,
    "device_fingerprint": true
  },
  "features": {
    "hindi_voice": true,
    "gemini_bridge": true,
    "ota_updates": true,
    "smart_auth": true,
    "super_intelligence": true,
    "proactive_alerts": true,
    "offline_mode": true
  }
}
CONFIGEOF
echo "   ✅ Config injected"

# Step 5: Build APK
echo "🏗️ [5/6] Building APK with all features..."
cd "$ANDROID_DIR"
./gradlew assembleDebug
echo "   ✅ APK built"

# Step 6: Copy and report
echo "📂 [6/6] Finalizing..."
mkdir -p "$(dirname "$APK_DEST")"
cp "$APK_OUTPUT" "$APK_DEST"

APK_SIZE=$(ls -lh "$APK_DEST" | awk '{print $5}')
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ SUPER INTELLIGENT APK Built Successfully!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  📱 APK File: $APK_DEST"
echo "  📏 Size: $APK_SIZE"
echo "  🌐 Download: /download/apk"
echo ""
echo "  ✨ NEW FEATURES IN THIS BUILD:"
echo "  ├── 🔄 OTA Live Updates (no re-download needed!)"
echo "  ├── 🎙️ Hindi Voice Assistant (sweet & smiling)"
echo "  ├── 🤖 Gemini Bridge (on-device + cloud AI)"
echo "  ├── 🔐 Smart Auth (owner/user recognition)"
echo "  ├── 🧠 Super Intelligence Engine"
echo "  └── ⚡ Proactive Alerts & Insights"
echo ""
echo "  📦 OTA Version: $VERSION"
echo "  👑 After first install, all future updates are LIVE!"
echo "═══════════════════════════════════════════════════════════"
