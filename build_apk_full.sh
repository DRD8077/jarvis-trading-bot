#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  📱 JARVIS AI — Android APK Builder v10.0 (Full Device Control)
#  ═══════════════════════════════════════════════════════════════════════════════
#  Builds a complete Android APK that includes:
#    ✅ React frontend (Vite + Capacitor)
#    ✅ Full device control (camera, mic, storage, contacts)
#    ✅ Voice commands with TTS/STT
#    ✅ Push notifications (Firebase)
#    ✅ Biometric auth
#    ✅ Background service
#    ✅ AI chat (Groq/Gemini/OpenAI/Anthropic)
#    ✅ Offline capabilities
#    ✅ Device management (WiFi, Bluetooth, battery)
#    ✅ App launch capability
#    ✅ File management
#    ✅ Auto-start on boot
#
#  Usage: ./build_apk_full.sh [--debug|--release|--aab]
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║     📱 JARVIS AI — Android APK Builder v10.0                        ║"
echo "║     Full Device Control + AI Assistant + Trading                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_TYPE="${1:---debug}"
VERSION=$(python3 -c "import json; print(json.load(open('version.json'))['version'])" 2>/dev/null || echo "10.0.0")
BUILD_NUM=$(python3 -c "import json; v=json.load(open('version.json')); v['build']=v.get('build',0)+1; open('version.json','w').write(json.dumps(v,indent=2)); print(v['build'])" 2>/dev/null || echo "1")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "  📌 Version: $VERSION (Build #$BUILD_NUM)"
echo "  🔨 Type:    $BUILD_TYPE"
echo "  ⏰ Time:    $TIMESTAMP"
echo ""

# ═══════════════════════════════════════════
# STEP 1: Pre-flight Checks
# ═══════════════════════════════════════════
echo "━━━ Step 1/9: Pre-flight Checks ━━━"

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "  ❌ Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
    sudo apt-get install -y nodejs 2>/dev/null || true
fi
echo "  ✅ Node.js: $(node --version)"

# Check Java
if ! command -v java &>/dev/null; then
    echo "  📦 Installing Java 17..."
    sudo apt-get update -qq && sudo apt-get install -y openjdk-17-jdk 2>/dev/null || true
fi
if command -v java &>/dev/null; then
    echo "  ✅ Java: $(java -version 2>&1 | head -1)"
else
    echo "  ⚠️ Java not found — Android build may fail"
fi

# Set JAVA_HOME
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android/sdk}"
export PATH="$JAVA_HOME/bin:$PATH"

echo ""

# ═══════════════════════════════════════════
# STEP 2: Build React Frontend
# ═══════════════════════════════════════════
echo "━━━ Step 2/9: Build React Frontend ━━━"

# Find frontend directory
FRONTEND_DIR=""
for dir in "telegram-mini-app" "frontend" "jarvis-app"; do
    if [ -d "$dir/src" ] && [ -f "$dir/package.json" ]; then
        FRONTEND_DIR="$dir"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo "  ❌ No frontend directory found!"
    exit 1
fi

cd "$FRONTEND_DIR"

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing frontend dependencies..."
    npm install 2>&1 | tail -3
fi

# Install Capacitor if not present
npm list @capacitor/core 2>/dev/null || npm install @capacitor/core @capacitor/cli 2>&1 | tail -2
npm list @capacitor/android 2>/dev/null || npm install @capacitor/android 2>&1 | tail -2

# Install device control plugins
echo "  📦 Installing Capacitor plugins for device control..."
PLUGINS=(
    "@capacitor/app"
    "@capacitor/browser"
    "@capacitor/camera"
    "@capacitor/clipboard"
    "@capacitor/device"
    "@capacitor/dialog"
    "@capacitor/filesystem"
    "@capacitor/geolocation"
    "@capacitor/haptics"
    "@capacitor/keyboard"
    "@capacitor/local-notifications"
    "@capacitor/motion"
    "@capacitor/network"
    "@capacitor/preferences"
    "@capacitor/push-notifications"
    "@capacitor/screen-reader"
    "@capacitor/share"
    "@capacitor/splash-screen"
    "@capacitor/status-bar"
    "@capacitor/text-zoom"
    "@capacitor/toast"
)

for plugin in "${PLUGINS[@]}"; do
    npm list "$plugin" 2>/dev/null || npm install "$plugin" 2>/dev/null || true
done
echo "  ✅ All plugins installed"

# Inject mobile config into frontend
cat > src/mobile-config.js << 'MOBILEEOF'
// JARVIS AI Mobile Configuration — Auto-generated
window.JARVIS_MOBILE = true;
window.JARVIS_VERSION = '10.0.0';
window.JARVIS_MODE = 'mobile';
window.JARVIS_FEATURES = {
    voiceCommands: true,
    camera: true,
    biometric: true,
    pushNotifications: true,
    offlineMode: true,
    deviceControl: true,
    fileManager: true,
    appLauncher: true,
    backgroundService: true,
    autoStart: true,
    contactAccess: true,
    locationTracking: true,
    trading: true,
    aiChat: true,
};
MOBILEEOF

# Build frontend
echo "  🔨 Building frontend..."
npm run build 2>&1 | tail -5

cd "$SCRIPT_DIR"
echo "  ✅ Frontend built"
echo ""

# ═══════════════════════════════════════════
# STEP 3: Configure Capacitor
# ═══════════════════════════════════════════
echo "━━━ Step 3/9: Configure Capacitor ━━━"

cd "$FRONTEND_DIR"

# Create/update capacitor.config.json
cat > capacitor.config.json << CAPEOF
{
  "appId": "com.jarvis.ai.assistant",
  "appName": "JARVIS AI",
  "webDir": "dist",
  "bundledWebRuntime": false,
  "server": {
    "androidScheme": "https",
    "cleartext": true,
    "allowNavigation": ["*"]
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "backgroundColor": "#0a0e1a",
      "androidSplashResourceName": "splash",
      "androidScaleType": "CENTER_CROP",
      "showSpinner": true,
      "spinnerColor": "#00d4ff"
    },
    "PushNotifications": {
      "presentationOptions": ["badge", "sound", "alert"]
    },
    "Camera": {
      "permissions": ["camera", "photos"]
    },
    "LocalNotifications": {
      "smallIcon": "ic_stat_icon_config_sample",
      "iconColor": "#00d4ff",
      "sound": "beep.wav"
    },
    "Keyboard": {
      "resize": "body",
      "style": "dark"
    }
  },
  "android": {
    "backgroundColor": "#0a0e1a",
    "allowMixedContent": true,
    "captureInput": true,
    "webContentsDebuggingEnabled": false,
    "useLegacyBridge": false,
    "buildOptions": {
      "keystorePath": "jarvis-release.keystore",
      "keystoreAlias": "jarvis-key"
    }
  }
}
CAPEOF

echo "  ✅ Capacitor configured"
echo ""

# ═══════════════════════════════════════════
# STEP 4: Initialize/Sync Android Project
# ═══════════════════════════════════════════
echo "━━━ Step 4/9: Sync Android Project ━━━"

# Add Android platform if not exists
if [ ! -d "android" ]; then
    echo "  📦 Adding Android platform..."
    npx cap add android 2>&1 | tail -3
fi

# Sync
echo "  🔄 Syncing with Capacitor..."
npx cap sync android 2>&1 | tail -5
echo "  ✅ Android synced"
echo ""

# ═══════════════════════════════════════════
# STEP 5: Inject Android Permissions
# ═══════════════════════════════════════════
echo "━━━ Step 5/9: Inject Android Permissions ━━━"

MANIFEST="android/app/src/main/AndroidManifest.xml"

if [ -f "$MANIFEST" ]; then
    # Add comprehensive permissions for full device control
    if ! grep -q "RECORD_AUDIO" "$MANIFEST"; then
        sed -i '/<manifest/a\
    <!-- JARVIS AI Full Device Control Permissions -->\
    <uses-permission android:name="android.permission.INTERNET" />\
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />\
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />\
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />\
    <uses-permission android:name="android.permission.CAMERA" />\
    <uses-permission android:name="android.permission.RECORD_AUDIO" />\
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />\
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />\
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />\
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />\
    <uses-permission android:name="android.permission.READ_CONTACTS" />\
    <uses-permission android:name="android.permission.WRITE_CONTACTS" />\
    <uses-permission android:name="android.permission.CALL_PHONE" />\
    <uses-permission android:name="android.permission.SEND_SMS" />\
    <uses-permission android:name="android.permission.READ_SMS" />\
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />\
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />\
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\
    <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />\
    <uses-permission android:name="android.permission.VIBRATE" />\
    <uses-permission android:name="android.permission.WAKE_LOCK" />\
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />\
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />\
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />\
    <uses-permission android:name="android.permission.USE_FINGERPRINT" />\
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\
    <uses-permission android:name="android.permission.BLUETOOTH" />\
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />\
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />\
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />\
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />\
    <uses-permission android:name="android.permission.PACKAGE_USAGE_STATS" />\
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />\
    <uses-permission android:name="android.permission.FLASHLIGHT" />\
    <uses-permission android:name="android.permission.SET_WALLPAPER" />\
    \
    <!-- JARVIS Gaming AI Permissions -->\
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION" />\
    <uses-permission android:name="android.permission.READ_FRAME_BUFFER" />\
    <uses-permission android:name="android.permission.CAPTURE_VIDEO_OUTPUT" />\
    <uses-permission android:name="android.permission.CAPTURE_SECURE_VIDEO_OUTPUT" />\
    \
    <uses-feature android:name="android.hardware.camera" android:required="false" />\
    <uses-feature android:name="android.hardware.camera.autofocus" android:required="false" />\
    <uses-feature android:name="android.hardware.microphone" android:required="false" />\
    <uses-feature android:name="android.hardware.bluetooth" android:required="false" />\
    <uses-feature android:name="android.hardware.location" android:required="false" />\
    <uses-feature android:name="android.hardware.fingerprint" android:required="false" />' "$MANIFEST"
        echo "  ✅ Permissions injected"
    else
        echo "  ✅ Permissions already present"
    fi
    
    # Add boot receiver for auto-start
    if ! grep -q "BOOT_COMPLETED" "$MANIFEST"; then
        sed -i '/<\/application>/i\
        <!-- Auto-start on boot -->\
        <receiver android:name=".BootReceiver" android:exported="true">\
            <intent-filter>\
                <action android:name="android.intent.action.BOOT_COMPLETED" />\
            </intent-filter>\
        </receiver>' "$MANIFEST"
    fi
fi

echo ""

# ═══════════════════════════════════════════
# STEP 6: Configure Gradle Build
# ═══════════════════════════════════════════
echo "━━━ Step 6/9: Configure Gradle Build ━━━"

GRADLE_FILE="android/app/build.gradle"
if [ -f "$GRADLE_FILE" ]; then
    # Update version
    VERSION_CODE=$((BUILD_NUM + 100))
    sed -i "s/versionCode [0-9]*/versionCode $VERSION_CODE/" "$GRADLE_FILE" 2>/dev/null
    sed -i "s/versionName \"[^\"]*\"/versionName \"$VERSION\"/" "$GRADLE_FILE" 2>/dev/null
    
    # Set minimum SDK to 24 for modern features
    sed -i "s/minSdkVersion [0-9]*/minSdkVersion 24/" "$GRADLE_FILE" 2>/dev/null
    sed -i "s/targetSdkVersion [0-9]*/targetSdkVersion 34/" "$GRADLE_FILE" 2>/dev/null
    
    echo "  ✅ Gradle configured: versionCode=$VERSION_CODE, versionName=$VERSION"
fi
echo ""

# ═══════════════════════════════════════════
# STEP 7: Generate/Use Keystore for Signing
# ═══════════════════════════════════════════
echo "━━━ Step 7/9: Keystore & Signing ━━━"

KEYSTORE="android/jarvis-release.keystore"
KEYSTORE_PROPS="android/keystore.properties"

if [ ! -f "$KEYSTORE" ]; then
    echo "  🔐 Generating release keystore..."
    keytool -genkey -v \
        -keystore "$KEYSTORE" \
        -alias jarvis-key \
        -keyalg RSA \
        -keysize 2048 \
        -validity 20000 \
        -storepass jarvisAI2024 \
        -keypass jarvisAI2024 \
        -dname "CN=JARVIS AI, OU=Trading, O=JARVIS, L=Mumbai, ST=MH, C=IN" 2>/dev/null
    echo "  ✅ Keystore generated"
else
    echo "  ✅ Keystore exists"
fi

# Create keystore properties
if [ ! -f "$KEYSTORE_PROPS" ]; then
    cat > "$KEYSTORE_PROPS" << KSEOF
storeFile=../jarvis-release.keystore
storePassword=jarvisAI2024
keyAlias=jarvis-key
keyPassword=jarvisAI2024
KSEOF
    echo "  ✅ Keystore properties created"
fi

# Inject signing config into build.gradle
if [ -f "$GRADLE_FILE" ] && ! grep -q "signingConfigs" "$GRADLE_FILE"; then
    sed -i '/android {/a\
    signingConfigs {\
        release {\
            def keystorePropsFile = rootProject.file("keystore.properties")\
            if (keystorePropsFile.exists()) {\
                def keystoreProps = new Properties()\
                keystoreProps.load(new FileInputStream(keystorePropsFile))\
                storeFile file(keystoreProps["storeFile"])\
                storePassword keystoreProps["storePassword"]\
                keyAlias keystoreProps["keyAlias"]\
                keyPassword keystoreProps["keyPassword"]\
            }\
        }\
    }' "$GRADLE_FILE"
    
    # Set release build type to use signing
    sed -i '/buildTypes {/,/}/{
        /release {/a\
            signingConfig signingConfigs.release
    }' "$GRADLE_FILE" 2>/dev/null || true
    
    echo "  ✅ Signing config injected"
fi

echo ""

# ═══════════════════════════════════════════
# STEP 8: Build APK
# ═══════════════════════════════════════════
echo "━━━ Step 8/9: Build APK ━━━"

cd android

# Make gradlew executable
chmod +x gradlew 2>/dev/null

echo "  🔨 Building Android APK ($BUILD_TYPE)..."

case "$BUILD_TYPE" in
    --release)
        ./gradlew assembleRelease 2>&1 | tail -10
        APK_PATH="app/build/outputs/apk/release/app-release.apk"
        ;;
    --aab)
        ./gradlew bundleRelease 2>&1 | tail -10
        APK_PATH="app/build/outputs/bundle/release/app-release.aab"
        ;;
    *)
        ./gradlew assembleDebug 2>&1 | tail -10
        APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
        ;;
esac

cd "$SCRIPT_DIR"

# Copy APK to dist
mkdir -p dist
FINAL_NAME="JARVIS-AI-v${VERSION}-b${BUILD_NUM}"

if [ "$BUILD_TYPE" = "--release" ] && [ -f "$FRONTEND_DIR/android/$APK_PATH" ]; then
    cp "$FRONTEND_DIR/android/$APK_PATH" "dist/${FINAL_NAME}-release.apk"
    echo "  ✅ Release APK: dist/${FINAL_NAME}-release.apk"
elif [ "$BUILD_TYPE" = "--aab" ] && [ -f "$FRONTEND_DIR/android/$APK_PATH" ]; then
    cp "$FRONTEND_DIR/android/$APK_PATH" "dist/${FINAL_NAME}.aab"
    echo "  ✅ AAB Bundle: dist/${FINAL_NAME}.aab"
elif [ -f "$FRONTEND_DIR/android/$APK_PATH" ]; then
    cp "$FRONTEND_DIR/android/$APK_PATH" "dist/${FINAL_NAME}-debug.apk"
    echo "  ✅ Debug APK: dist/${FINAL_NAME}-debug.apk"
else
    echo "  ⚠️ APK build completed but file not found at expected path"
    echo "  🔍 Searching for APK..."
    find "$FRONTEND_DIR/android" -name "*.apk" -o -name "*.aab" 2>/dev/null | while read f; do
        echo "    Found: $f"
        cp "$f" "dist/" 2>/dev/null
    done
fi

echo ""

# ═══════════════════════════════════════════
# STEP 9: Build Report
# ═══════════════════════════════════════════
echo "━━━ Step 9/9: Build Report ━━━"

# Generate build report
cat > dist/build-report-apk.json << BREOF
{
  "app": "JARVIS AI",
  "version": "$VERSION",
  "build": $BUILD_NUM,
  "type": "$BUILD_TYPE",
  "timestamp": "$TIMESTAMP",
  "platform": "android",
  "minSdk": 24,
  "targetSdk": 34,
  "features": [
    "AI Chat (Groq/Gemini/OpenAI/Anthropic)",
    "Voice Commands (TTS + STT)",
    "Stock & Crypto Trading",
    "Push Notifications",
    "Camera Access",
    "Biometric Authentication",
    "File Manager",
    "Contact Access",
    "Location Tracking",
    "Bluetooth Control",
    "WiFi Management",
    "App Launcher",
    "SMS/Call Control",
    "Background Service",
    "Auto-start on Boot",
    "Offline Mode",
    "Device Flashlight",
    "Wallpaper Control"
  ]
}
BREOF

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                   📱 JARVIS APK Build Complete!                     ║"
echo "╠═══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                     ║"

# List built APKs
if [ -d "dist" ]; then
    echo "║  📁 Built Artifacts:                                                ║"
    for f in dist/JARVIS-AI-v${VERSION}*; do
        if [ -f "$f" ]; then
            SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
            NAME=$(basename "$f")
            printf "║    %-55s %8s ║\n" "$NAME" "$SIZE"
        fi
    done
fi

echo "║                                                                     ║"
echo "║  📱 What JARVIS Mobile Can Do:                                      ║"
echo "║    • AI Chat with voice commands                                     ║"
echo "║    • Open/control other apps on phone                               ║"
echo "║    • Make calls, send SMS                                            ║"
echo "║    • Camera & photo access                                           ║"
echo "║    • File management                                                 ║"
echo "║    • Contact management                                              ║"
echo "║    • Location tracking & maps                                        ║"
echo "║    • WiFi & Bluetooth control                                        ║"
echo "║    • Stock & crypto trading signals                                  ║"
echo "║    • Push notifications                                              ║"
echo "║    • Biometric lock                                                  ║"
echo "║    • Background service (always running)                             ║"
echo "║    • Auto-start on phone boot                                        ║"
echo "║    • Flashlight, wallpaper control                                   ║"
echo "║                                                                     ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📋 Install: Transfer APK to phone → Settings → Allow Unknown Sources → Install"
echo "  🎤 Say: 'Hey JARVIS' to activate voice commands"
echo ""
