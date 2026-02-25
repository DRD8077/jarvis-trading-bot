#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  🚀 JARVIS AI — Standalone Professional APK Builder v1.0
#  ─────────────────────────────────────────────────────────────────
#  Zero Telegram dependency. Pure standalone Android APK.
#  Features: AI Chat, WebSocket Live, Firebase Push, Biometric,
#  Offline AI, Indian Stocks + Crypto, Voice AI
# ═══════════════════════════════════════════════════════════════════
set -e

# ═══ Configuration ═══
PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJ_DIR/telegram-mini-app"  # React app source
ANDROID_DIR="$FRONTEND_DIR/android"
DIST_DIR="$PROJ_DIR/dist"
VERSION_NAME="1.0.0"
VERSION_CODE="10000"
APP_NAME="JARVIS AI"
APP_ID="com.jarvis.trading"
BUILD_MODE="${1:-apk}"  # apk, release, aab, both
SERVER_URL="${JARVIS_SERVER_URL:-}"  # Production server URL for APK

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🚀 JARVIS AI — Standalone APK Builder v${VERSION_NAME}           ║"
echo "║   Mode: ${BUILD_MODE^^} | No Telegram Dependency              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ═══ Step 0: Prerequisites ═══
echo "🔍 [0/8] Checking prerequisites..."

# Java
if command -v java &>/dev/null; then
    echo "   ✅ Java: $(java -version 2>&1 | head -1 | awk -F'"' '{print $2}')"
else
    echo "   📦 Installing Java 17..."
    sudo apt-get update >/dev/null 2>&1 && sudo apt-get install -y openjdk-17-jdk >/dev/null 2>&1
fi

if [ -z "$JAVA_HOME" ]; then
    for jp in \
        /usr/local/sdkman/candidates/java/21.0.9-ms \
        /usr/local/sdkman/candidates/java/current \
        /usr/lib/jvm/java-17-openjdk-amd64 \
        /usr/lib/jvm/java-21-openjdk-amd64; do
        [ -d "$jp" ] && { export JAVA_HOME="$jp"; break; }
    done
fi
echo "   JAVA_HOME=$JAVA_HOME"

# Node.js
if ! command -v node &>/dev/null; then
    echo "   📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - >/dev/null 2>&1
    sudo apt-get install -y nodejs >/dev/null 2>&1
fi
echo "   ✅ Node: $(node --version)"

# Android SDK
if [ -z "$ANDROID_HOME" ]; then
    for sdk_path in "$HOME/android-sdk" "/usr/local/lib/android/sdk"; do
        [ -d "$sdk_path" ] && { export ANDROID_HOME="$sdk_path"; break; }
    done
fi

if [ -z "$ANDROID_HOME" ] || [ ! -d "$ANDROID_HOME" ]; then
    echo "   📦 Setting up Android SDK..."
    export ANDROID_HOME="$HOME/android-sdk"
    mkdir -p "$ANDROID_HOME"
    
    if [ ! -f ~/android-cmdline-tools.zip ]; then
        wget -q "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" \
            -O ~/android-cmdline-tools.zip
    fi
    
    if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
        unzip -qo ~/android-cmdline-tools.zip -d "$ANDROID_HOME/"
        mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
        mv "$ANDROID_HOME/cmdline-tools/bin" "$ANDROID_HOME/cmdline-tools/latest/" 2>/dev/null || true
        mv "$ANDROID_HOME/cmdline-tools/lib" "$ANDROID_HOME/cmdline-tools/latest/" 2>/dev/null || true
    fi
    
    export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
    yes | sdkmanager --licenses >/dev/null 2>&1 || true
    sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools" >/dev/null 2>&1 || true
fi

export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
echo "   ANDROID_HOME=$ANDROID_HOME"
echo "   ✅ All prerequisites ready"

# ═══ Step 1: Build React Frontend ═══
echo ""
echo "🔨 [1/8] Building standalone React frontend..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "   📦 Installing packages..."
    npm install --legacy-peer-deps 2>/dev/null || npm install
fi

# Build with server URL baked in for native APK
VITE_SERVER_URL="$SERVER_URL" npm run build 2>&1 | tail -3
echo "   ✅ Frontend built ($(du -sh dist | cut -f1))"

# ═══ Step 2: Capacitor Config ═══
echo ""
echo "📱 [2/8] Writing Capacitor config..."

cat > "$FRONTEND_DIR/capacitor.config.json" << EOF
{
  "appId": "${APP_ID}",
  "appName": "${APP_NAME}",
  "webDir": "dist",
  "server": {
    "cleartext": true,
    "allowNavigation": ["*"],
    "errorPath": "index.html",
    "androidScheme": "https"
  },
  "android": {
    "allowMixedContent": true,
    "backgroundColor": "#0a0e1a",
    "captureInput": true,
    "webContentsDebuggingEnabled": false,
    "initialFocus": true,
    "buildOptions": {
      "releaseType": "APK"
    }
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "launchAutoHide": true,
      "backgroundColor": "#0a0e1a",
      "showSpinner": true,
      "spinnerColor": "#3b82f6"
    },
    "StatusBar": {
      "style": "DARK",
      "backgroundColor": "#0a0e1a"
    },
    "LocalLLM": {
      "defaultModel": "auto",
      "threads": 4,
      "contextSize": 2048
    },
    "VoskSTT": {
      "defaultLanguage": "en-us",
      "sampleRate": 16000
    },
    "LocalTTS": {
      "defaultLanguage": "hi-IN",
      "rate": 1.0
    },
    "PushNotifications": {
      "presentationOptions": ["badge", "sound", "alert"]
    },
    "BiometricAuth": {
      "allowDeviceCredential": true
    },
    "LocalNotifications": {
      "smallIcon": "ic_stat_icon",
      "iconColor": "#3b82f6"
    }
  }
}
EOF
echo "   ✅ Capacitor configured for standalone"

# ═══ Step 3: Sync Android ═══
echo ""
echo "📱 [3/8] Syncing with Android..."
npx cap sync android 2>&1 | tail -3
echo "   ✅ Android synced"

# ═══ Step 4: Inject AI Config ═══
echo ""
echo "🧠 [4/8] Injecting standalone app config..."

mkdir -p "$ANDROID_DIR/app/src/main/assets/models"

cat > "$ANDROID_DIR/app/src/main/assets/jarvis_config.json" << EOF
{
  "app": {
    "name": "${APP_NAME}",
    "version": "${VERSION_NAME}",
    "mode": "standalone",
    "telegram_dependency": false
  },
  "features": {
    "ai_chat": true,
    "streaming_responses": true,
    "websocket_live_data": true,
    "firebase_push": true,
    "offline_ai": true,
    "biometric_lock": true,
    "paper_trading": true,
    "indian_stocks": true,
    "crypto_trading": true,
    "options_chain": true,
    "hindi_voice": true,
    "signal_alerts": true
  },
  "ai_engine": {
    "type": "hybrid",
    "online_providers": ["groq", "gemini", "openai", "anthropic"],
    "offline_engine": "llama.cpp",
    "offline_models": [
      {"name": "TinyLlama 1.1B", "size_mb": 670, "min_ram_gb": 3},
      {"name": "Phi-3 Mini", "size_mb": 2300, "min_ram_gb": 6}
    ]
  },
  "server": {
    "url": "${SERVER_URL}",
    "websocket": true,
    "push_notifications": "firebase"
  }
}
EOF
echo "   ✅ Standalone config injected"

# ═══ Step 5: Android Permissions ═══
echo ""
echo "🔐 [5/8] Configuring permissions..."

MANIFEST="$ANDROID_DIR/app/src/main/AndroidManifest.xml"
if [ -f "$MANIFEST" ]; then
    PERMS_TO_ADD=(
        "android.permission.USE_BIOMETRIC"
        "android.permission.CAMERA"
        "android.permission.VIBRATE"
        "android.permission.RECEIVE_BOOT_COMPLETED"
        "android.permission.POST_NOTIFICATIONS"
        "android.permission.FOREGROUND_SERVICE"
        "android.permission.RECORD_AUDIO"
    )
    for perm in "${PERMS_TO_ADD[@]}"; do
        if ! grep -q "$perm" "$MANIFEST"; then
            sed -i "/<uses-permission android:name=\"android.permission.INTERNET\"/a\\
    <uses-permission android:name=\"$perm\" />" "$MANIFEST"
        fi
    done
    echo "   ✅ All permissions configured"
fi

# ═══ Step 6: Set Version ═══
echo ""
echo "📝 [6/8] Setting version ${VERSION_NAME}..."

BUILD_GRADLE="$ANDROID_DIR/app/build.gradle"
if [ -f "$BUILD_GRADLE" ]; then
    sed -i "s/versionName \".*\"/versionName \"${VERSION_NAME}\"/" "$BUILD_GRADLE"
    sed -i "s/versionCode [0-9]*/versionCode ${VERSION_CODE}/" "$BUILD_GRADLE"
    echo "   ✅ Version: ${VERSION_NAME} (${VERSION_CODE})"
fi

# ═══ Step 7: Generate Keystore ═══
echo ""
echo "🔑 [7/8] Release signing..."

KEYSTORE="$ANDROID_DIR/app/jarvis-release.keystore"
if [ ! -f "$KEYSTORE" ]; then
    keytool -genkeypair -v \
        -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass jarvis2024 -keypass jarvis2024 \
        -alias jarvis-key -keystore "$KEYSTORE" \
        -dname "CN=JARVIS AI, OU=Trading, O=DRD Tech, L=Mumbai, ST=MH, C=IN" \
        2>/dev/null && echo "   ✅ Keystore created" || echo "   ⚠️ Using debug signing"
fi

# Inject signing config
if [ -f "$KEYSTORE" ] && [ -f "$BUILD_GRADLE" ]; then
    if ! grep -q "signingConfigs" "$BUILD_GRADLE"; then
        sed -i '/buildTypes {/i\
    signingConfigs {\
        release {\
            storeFile file("jarvis-release.keystore")\
            storePassword "jarvis2024"\
            keyAlias "jarvis-key"\
            keyPassword "jarvis2024"\
        }\
    }' "$BUILD_GRADLE"
        sed -i 's/buildTypes {/buildTypes {\n        release {\n            signingConfig signingConfigs.release\n            minifyEnabled true\n            proguardFiles getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro"\n        }/' "$BUILD_GRADLE"
        echo "   ✅ Release signing injected"
    fi
fi

# ═══ Step 8: Build ═══
echo ""
echo "🏗️ [8/8] Building Android (${BUILD_MODE^^})..."
cd "$ANDROID_DIR"
chmod +x gradlew 2>/dev/null || true

APK_DEBUG="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
APK_RELEASE="$ANDROID_DIR/app/build/outputs/apk/release/app-release.apk"
AAB_RELEASE="$ANDROID_DIR/app/build/outputs/bundle/release/app-release.aab"

case "$BUILD_MODE" in
    release)
        ./gradlew assembleRelease 2>&1 | tail -10
        BUILD_OUTPUT="$APK_RELEASE"
        ;;
    aab)
        ./gradlew bundleRelease 2>&1 | tail -10
        BUILD_OUTPUT="$AAB_RELEASE"
        ;;
    both)
        ./gradlew assembleDebug assembleRelease bundleRelease 2>&1 | tail -10
        BUILD_OUTPUT="$APK_DEBUG"
        ;;
    *)
        ./gradlew assembleDebug 2>&1 | tail -10
        BUILD_OUTPUT="$APK_DEBUG"
        ;;
esac

# Find output
if [ ! -f "$BUILD_OUTPUT" ]; then
    BUILD_OUTPUT=$(find "$ANDROID_DIR" -name "*.apk" 2>/dev/null | head -1)
fi

if [ -z "$BUILD_OUTPUT" ] || [ ! -f "$BUILD_OUTPUT" ]; then
    echo "   ❌ Build failed"
    exit 1
fi

# ═══ Package Output ═══
mkdir -p "$DIST_DIR"
FINAL_APK="$DIST_DIR/JARVIS-AI-v${VERSION_NAME}.apk"
cp "$BUILD_OUTPUT" "$FINAL_APK"

[ -f "$APK_RELEASE" ] && cp "$APK_RELEASE" "$DIST_DIR/JARVIS-AI-v${VERSION_NAME}-release.apk"
[ -f "$AAB_RELEASE" ] && cp "$AAB_RELEASE" "$DIST_DIR/JARVIS-AI-v${VERSION_NAME}.aab"

OUTPUT_SIZE=$(du -h "$FINAL_APK" | cut -f1)

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ✅ JARVIS AI v${VERSION_NAME} — Build Complete!                 ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║                                                           ║"
echo "║   📱 APK:  $FINAL_APK"
echo "║   📦 Size: $OUTPUT_SIZE"
echo "║   🏗️  Mode: STANDALONE (No Telegram)                     ║"
echo "║                                                           ║"
echo "║   Features:                                               ║"
echo "║   ├── 🤖 AI Chat (Groq/Gemini/OpenAI/Anthropic)          ║"
echo "║   ├── 📡 WebSocket Real-Time Data                        ║"
echo "║   ├── 🔔 Firebase Push Notifications                     ║"
echo "║   ├── 🧠 Offline AI (llama.cpp on-device)                ║"
echo "║   ├── 🔐 Biometric Authentication                       ║"
echo "║   ├── 📊 Indian Stocks + Crypto Trading                  ║"
echo "║   ├── 📈 Options Chain & Screener                        ║"
echo "║   ├── 🗣️  Hindi Voice Assistant                           ║"
echo "║   └── 📱 100% Standalone — No Telegram                   ║"
echo "║                                                           ║"
echo "║   Install: adb install -r $FINAL_APK"
echo "╚═══════════════════════════════════════════════════════════╝"
