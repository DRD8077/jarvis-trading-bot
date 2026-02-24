#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   JARVIS AI — Play Store Ready APK/AAB Build Script v5.0
#   All Features: Firebase Push, Biometric, Paper Trading,
#   Offline AI, AMOLED Theme, Swipe Gestures, Signal Cards
#   Play Store + Direct APK — Dual Output
#   Jai Mahadev! 🙏
# ═══════════════════════════════════════════════════════════════
set -e

PROJ_DIR="/workspaces/codespaces-blank/telegram-mini-app"
ANDROID_DIR="$PROJ_DIR/android"
APK_OUTPUT="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
AAB_OUTPUT="$ANDROID_DIR/app/build/outputs/bundle/release/app-release.aab"
APK_RELEASE_OUTPUT="$ANDROID_DIR/app/build/outputs/apk/release/app-release.apk"
DIST_DIR="$PROJ_DIR/dist"
VERSION_NAME="5.0.0"
VERSION_CODE="50000"

# Build mode: apk (default), aab (Play Store), or both
BUILD_MODE="${1:-apk}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🚀 JARVIS AI v${VERSION_NAME} — Pro APK Builder"
echo "  Firebase Push | Biometric | Paper Trading | Themes"
echo "  Build mode: ${BUILD_MODE^^}"
echo "  Jai Mahadev! 🙏"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══ Step 0: Check Prerequisites ═══
echo "🔍 [0/9] Checking prerequisites..."

# Java
if command -v java &>/dev/null; then
    echo "   ✅ Java found: $(java -version 2>&1 | head -1)"
else
    echo "   📦 Installing Java 17..."
    sudo apt update >/dev/null 2>&1
    sudo apt install -y openjdk-17-jdk >/dev/null 2>&1
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
fi

if [ -z "$JAVA_HOME" ]; then
    for jpath in \
        /usr/local/sdkman/candidates/java/21.0.9-ms \
        /usr/local/sdkman/candidates/java/current \
        /usr/lib/jvm/java-17-openjdk-amd64 \
        /usr/lib/jvm/java-21-openjdk-amd64; do
        if [ -d "$jpath" ]; then
            export JAVA_HOME="$jpath"
            break
        fi
    done
fi
echo "   JAVA_HOME=$JAVA_HOME"

# Android SDK
if [ -z "$ANDROID_HOME" ]; then
    if [ -d "$HOME/android-sdk" ]; then
        export ANDROID_HOME="$HOME/android-sdk"
    elif [ -d "/usr/local/lib/android/sdk" ]; then
        export ANDROID_HOME="/usr/local/lib/android/sdk"
    fi
fi

if [ -z "$ANDROID_HOME" ] || [ ! -d "$ANDROID_HOME" ]; then
    echo "   📦 Setting up Android SDK..."
    mkdir -p ~/android-sdk
    export ANDROID_HOME=~/android-sdk
    
    if [ ! -f ~/android-cmdline-tools.zip ]; then
        wget -q "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" -O ~/android-cmdline-tools.zip
    fi
    
    if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
        unzip -qo ~/android-cmdline-tools.zip -d ~/android-sdk/
        mkdir -p ~/android-sdk/cmdline-tools/latest
        mv ~/android-sdk/cmdline-tools/bin ~/android-sdk/cmdline-tools/latest/ 2>/dev/null || true
        mv ~/android-sdk/cmdline-tools/lib ~/android-sdk/cmdline-tools/latest/ 2>/dev/null || true
    fi
    
    export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
    yes | sdkmanager --licenses >/dev/null 2>&1 || true
    sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools" >/dev/null 2>&1 || echo "   ⚠️ SDK download partial"
fi

export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools
echo "   ANDROID_HOME=$ANDROID_HOME"
echo "   ✅ Prerequisites ready"

# ═══ Step 1: Build React Frontend ═══
echo ""
echo "🔨 [1/9] Building React frontend v${VERSION_NAME}..."
cd "$PROJ_DIR"

if [ ! -d "node_modules" ]; then
    echo "   📦 Installing npm packages..."
    npm install --legacy-peer-deps 2>/dev/null || npm install
fi

npm run build 2>&1 | tail -3
echo "   ✅ Frontend built"

# ═══ Step 2: Write Capacitor Config ═══
echo ""
echo "📱 [2/9] Writing Capacitor config with all plugins..."

cat > "$PROJ_DIR/capacitor.config.json" << 'CAPEOF'
{
  "appId": "com.jarvis.trading",
  "appName": "JARVIS AI",
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
      "keystorePath": null,
      "releaseType": "APK"
    }
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "launchAutoHide": true,
      "backgroundColor": "#0a0e1a",
      "androidSplashResourceName": "splash",
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
      "rate": 1.0,
      "pitch": 1.0
    },
    "PushNotifications": {
      "presentationOptions": ["badge", "sound", "alert"]
    },
    "BiometricAuth": {
      "allowDeviceCredential": true
    },
    "Camera": {
      "permissions": ["camera"]
    },
    "LocalNotifications": {
      "smallIcon": "ic_stat_icon",
      "iconColor": "#3b82f6",
      "sound": "notification.wav"
    }
  }
}
CAPEOF
echo "   ✅ Capacitor config written"

# ═══ Step 3: Sync with Android ═══
echo ""
echo "📱 [3/9] Syncing with Android..."
npx cap sync android 2>&1 | tail -3
echo "   ✅ Android synced"

# ═══ Step 4: Inject AI + App Config ═══
echo ""
echo "🧠 [4/9] Injecting app config & assets..."

mkdir -p "$ANDROID_DIR/app/src/main/assets"
mkdir -p "$ANDROID_DIR/app/src/main/assets/models"

cat > "$ANDROID_DIR/app/src/main/assets/jarvis_ai_config.json" << 'EOF'
{
  "app_name": "JARVIS AI Trading Bot",
  "version": "5.0.0",
  "features": {
    "streaming_ai_chat": true,
    "firebase_push": true,
    "websocket_live_data": true,
    "onboarding_screens": true,
    "tradingview_charts": true,
    "offline_ai": true,
    "biometric_lock": true,
    "paper_trading": true,
    "pnl_journal": true,
    "hindi_voice": true,
    "signal_share_cards": true,
    "qr_scanner": true,
    "amoled_theme": true,
    "swipe_gestures": true,
    "copy_trading": true
  },
  "ai_engine": {
    "type": "hybrid",
    "online": "gemini",
    "offline": "llama.cpp",
    "recommended_models": [
      {"name": "TinyLlama 1.1B", "size_mb": 670, "min_ram_gb": 3},
      {"name": "Llama 3.2 1B", "size_mb": 700, "min_ram_gb": 3},
      {"name": "Phi-3 Mini", "size_mb": 2300, "min_ram_gb": 6}
    ]
  },
  "personality": {
    "name": "JARVIS",
    "creator": "DRD (Mahadev)",
    "style": "friendly_hindi_english",
    "greeting": "Jai Mahadev! Main JARVIS hoon, aapka AI assistant! 🙏"
  }
}
EOF

echo '{"info": "Place .gguf models here or download in-app"}' > "$ANDROID_DIR/app/src/main/assets/models/README.json"
echo "   ✅ App config injected"

# ═══ Step 5: Configure Android Manifest for permissions ═══
echo ""
echo "🔐 [5/9] Configuring Android permissions..."

MANIFEST="$ANDROID_DIR/app/src/main/AndroidManifest.xml"
if [ -f "$MANIFEST" ]; then
    # Add permissions if not present
    if ! grep -q "USE_BIOMETRIC" "$MANIFEST"; then
        sed -i '/<uses-permission android:name="android.permission.INTERNET"/a\
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />\
    <uses-permission android:name="android.permission.CAMERA" />\
    <uses-permission android:name="android.permission.VIBRATE" />\
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\
    <uses-permission android:name="android.permission.RECORD_AUDIO" />' "$MANIFEST"
        echo "   ✅ Permissions added (biometric, camera, push, audio)"
    else
        echo "   ✅ Permissions already present"
    fi
else
    echo "   ⚠️ AndroidManifest.xml not found (will be created by cap sync)"
fi

# ═══ Step 6: Set version in build.gradle ═══
echo ""
echo "📝 [6/9] Setting app version..."

BUILD_GRADLE="$ANDROID_DIR/app/build.gradle"
if [ -f "$BUILD_GRADLE" ]; then
    # Update versionName
    sed -i "s/versionName \".*\"/versionName \"${VERSION_NAME}\"/" "$BUILD_GRADLE"
    # Update versionCode
    sed -i "s/versionCode [0-9]*/versionCode ${VERSION_CODE}/" "$BUILD_GRADLE"
    echo "   ✅ Version set: ${VERSION_NAME} (${VERSION_CODE})"
else
    echo "   ⚠️ build.gradle not found"
fi

# ═══ Step 7: Generate keystore for release signing ═══
echo ""
echo "🔑 [7/9] Checking release signing..."

KEYSTORE_DIR="$ANDROID_DIR/app"
KEYSTORE_FILE="$KEYSTORE_DIR/jarvis-release.keystore"
KEYSTORE_PROPS="$ANDROID_DIR/keystore.properties"

if [ ! -f "$KEYSTORE_FILE" ]; then
    echo "   🔑 Generating release keystore..."
    keytool -genkeypair -v \
        -storetype PKCS12 \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass jarvis2024 \
        -keypass jarvis2024 \
        -alias jarvis-key \
        -keystore "$KEYSTORE_FILE" \
        -dname "CN=JARVIS AI, OU=Trading, O=Mahadev Tech, L=Mumbai, ST=MH, C=IN" \
        2>/dev/null || echo "   ⚠️ keytool not available, using debug key"
    
    if [ -f "$KEYSTORE_FILE" ]; then
        cat > "$KEYSTORE_PROPS" << KEOF
storeFile=app/jarvis-release.keystore
storePassword=jarvis2024
keyAlias=jarvis-key
keyPassword=jarvis2024
KEOF
        echo "   ✅ Release keystore created"
    fi
else
    echo "   ✅ Release keystore exists"
fi

# Inject signing config into build.gradle
if [ -f "$KEYSTORE_FILE" ] && [ -f "$BUILD_GRADLE" ]; then
    if ! grep -q "signingConfigs" "$BUILD_GRADLE"; then
        # Add signing config before the first buildTypes block
        sed -i '/buildTypes {/i\
    signingConfigs {\
        release {\
            storeFile file("jarvis-release.keystore")\
            storePassword "jarvis2024"\
            keyAlias "jarvis-key"\
            keyPassword "jarvis2024"\
        }\
    }' "$BUILD_GRADLE"
        
        # Set release build type to use the signing config
        sed -i 's/buildTypes {/buildTypes {\n        release {\n            signingConfig signingConfigs.release\n            minifyEnabled true\n            proguardFiles getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro"\n        }/' "$BUILD_GRADLE"
        echo "   ✅ Release signing config injected"
    fi
fi

# ═══ Step 8: Build APK / AAB ═══
echo ""
echo "🏗️ [8/9] Building Android ($BUILD_MODE)..."
cd "$ANDROID_DIR"

chmod +x gradlew 2>/dev/null || true

case "$BUILD_MODE" in
    aab)
        echo "   Building AAB for Play Store..."
        ./gradlew bundleRelease 2>&1 | tail -10
        BUILD_OUTPUT="$AAB_OUTPUT"
        ;;
    release)
        echo "   Building signed release APK..."
        ./gradlew assembleRelease 2>&1 | tail -10
        BUILD_OUTPUT="$APK_RELEASE_OUTPUT"
        ;;
    both)
        echo "   Building both APK and AAB..."
        ./gradlew assembleDebug 2>&1 | tail -5
        ./gradlew bundleRelease 2>&1 | tail -5
        BUILD_OUTPUT="$APK_OUTPUT"
        ;;
    *)
        echo "   Building debug APK..."
        ./gradlew assembleDebug 2>&1 | tail -10
        BUILD_OUTPUT="$APK_OUTPUT"
        ;;
esac

# Find built output
if [ ! -f "$BUILD_OUTPUT" ]; then
    echo "   ⚠️ Expected output not found, searching..."
    BUILD_OUTPUT=$(find "$ANDROID_DIR" -name "*.apk" -o -name "*.aab" 2>/dev/null | head -1)
fi

if [ -z "$BUILD_OUTPUT" ] || [ ! -f "$BUILD_OUTPUT" ]; then
    echo "   ❌ Build failed — check logs above"
    exit 1
fi
echo "   ✅ Build successful!"

# ═══ Step 9: Package & Report ═══
echo ""
echo "📦 [9/9] Packaging final output..."
mkdir -p "$DIST_DIR"

# Copy APK
APK_DEST="$DIST_DIR/jarvis-ai-v${VERSION_NAME}.apk"
if [ -f "$APK_OUTPUT" ]; then
    cp "$APK_OUTPUT" "$APK_DEST"
fi
# Copy release APK if exists
if [ -f "$APK_RELEASE_OUTPUT" ]; then
    cp "$APK_RELEASE_OUTPUT" "$DIST_DIR/jarvis-ai-v${VERSION_NAME}-release.apk"
fi
# Copy AAB if exists
AAB_DEST="$DIST_DIR/jarvis-ai-v${VERSION_NAME}.aab"
if [ -f "$AAB_OUTPUT" ]; then
    cp "$AAB_OUTPUT" "$AAB_DEST"
fi

# Determine final output path
if [ -f "$APK_DEST" ]; then
    FINAL_OUTPUT="$APK_DEST"
elif [ -f "$AAB_DEST" ]; then
    FINAL_OUTPUT="$AAB_DEST"
else
    FINAL_OUTPUT="$BUILD_OUTPUT"
fi

OUTPUT_SIZE=$(du -h "$FINAL_OUTPUT" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ JARVIS AI v${VERSION_NAME} — Build Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  📱 Output:  $FINAL_OUTPUT"
echo "  📦 Size:    $OUTPUT_SIZE"
echo ""
echo "  ✨ v5.0 Features Included:"
echo "     ├── 💬 Streaming AI Chat (Gemini + Offline LLM)"
echo "     ├── 🔔 Firebase Push Notifications"
echo "     ├── 📡 WebSocket + SSE Live Data"
echo "     ├── 🎬 Onboarding Intro Screens"
echo "     ├── 📊 TradingView Candlestick Charts"
echo "     ├── 🧠 Offline AI (llama.cpp on-device)"
echo "     ├── 🔐 Biometric Lock (fingerprint/face)"
echo "     ├── 📝 Paper Trading (₹10L virtual money)"
echo "     ├── 📈 P&L Journal with CSV export"
echo "     ├── 🗣️ Hindi Voice Assistant"
echo "     ├── 🖼️ Signal Share Cards (WhatsApp/Insta)"
echo "     ├── 📷 QR Code Scanner"
echo "     ├── 🌙 AMOLED + Light + Dark Themes"
echo "     ├── 👆 Swipe Gestures Between Tabs"
echo "     └── 📋 Copy Trading (auto-follow top traders)"
echo ""
if [ -f "$AAB_DEST" ]; then
echo "  🏪 Play Store Upload:"
echo "     Upload $AAB_DEST to Google Play Console"
echo "     → https://play.google.com/console"
echo ""
fi
echo "  📲 Install APK on phone:"
echo "     adb install -r $FINAL_OUTPUT"
echo ""
echo "  🙏 Jai Mahadev! JARVIS v5.0 is ready! 🚀"
echo "═══════════════════════════════════════════════════════════════"
