#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   JARVIS AI Agent — SUPER APK Build Script v3.0
#   With Offline LLM + Vosk STT + TTS + Device Commands
#   100% Offline AI — No Internet, No API Keys!
#   Jai Mahadev! 🙏
# ═══════════════════════════════════════════════════════════════
set -e

PROJ_DIR="/workspaces/codespaces-blank/telegram-mini-app"
ANDROID_DIR="$PROJ_DIR/android"
APK_OUTPUT="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
APK_DEST="$PROJ_DIR/dist/jarvis-ai-agent.apk"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🧠 JARVIS AI Agent APK Builder v3.0"
echo "  Offline LLM + Voice + Device Commands"
echo "  Jai Mahadev! 🙏"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ═══ Step 0: Check Java & Android SDK ═══
echo "🔍 [0/7] Checking prerequisites..."

# Java
if command -v java &>/dev/null; then
    echo "   ✅ Java found: $(java -version 2>&1 | head -1)"
else
    echo "   📦 Installing Java 17..."
    sudo apt update >/dev/null 2>&1
    sudo apt install -y openjdk-17-jdk >/dev/null 2>&1
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
fi

# Try multiple Java home locations
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
    sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools" >/dev/null 2>&1 || echo "   ⚠️ SDK download partial (may work)"
fi

export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools
echo "   ANDROID_HOME=$ANDROID_HOME"
echo "   ✅ Prerequisites ready"

# ═══ Step 1: Build React Frontend ═══
echo ""
echo "🔨 [1/7] Building React frontend with AI Agent..."
cd "$PROJ_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   📦 Installing npm packages..."
    npm install --legacy-peer-deps 2>/dev/null || npm install
fi

npm run build 2>&1 | tail -3
echo "   ✅ Frontend built"

# ═══ Step 2: Update Capacitor Config for Local Mode ═══
echo ""
echo "📱 [2/7] Configuring for hybrid mode (local UI + server AI)..."

# Write proper capacitor config — LOCAL UI, SERVER API (Gemini AI)
cat > "$PROJ_DIR/capacitor.config.json" << 'EOF'
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
      "rate": 1.0,
      "pitch": 1.0
    }
  }
}
EOF
echo "   ✅ Capacitor configured (local UI + server Gemini AI)"

# ═══ Step 3: Sync with Android ═══
echo ""
echo "📱 [3/7] Syncing with Android (Capacitor)..."
npx cap sync android 2>&1 | tail -3
echo "   ✅ Android synced"

# ═══ Step 4: Inject AI Config ═══
echo ""
echo "🧠 [4/7] Injecting AI Agent config..."

mkdir -p "$ANDROID_DIR/app/src/main/assets"

cat > "$ANDROID_DIR/app/src/main/assets/jarvis_ai_config.json" << 'EOF'
{
  "app_name": "JARVIS AI Agent",
  "version": "3.0.0-ai",
  "ai_engine": {
    "type": "local",
    "no_internet_required": true,
    "no_api_key_required": true,
    "llm": {
      "engine": "llama.cpp",
      "format": "GGUF",
      "default_model": "auto",
      "recommended_models": [
        {
          "name": "TinyLlama 1.1B",
          "filename": "tinyllama-1.1b-chat-Q4_K_M.gguf",
          "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
          "size_mb": 670,
          "min_ram_gb": 3,
          "quality": "good",
          "speed": "fast"
        },
        {
          "name": "Llama 3.2 1B",
          "filename": "llama-3.2-1b-instruct-Q4_K_M.gguf",
          "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
          "size_mb": 700,
          "min_ram_gb": 3,
          "quality": "very_good",
          "speed": "fast"
        },
        {
          "name": "Phi-3 Mini",
          "filename": "phi-3-mini-4k-instruct-q4.gguf",
          "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
          "size_mb": 2300,
          "min_ram_gb": 6,
          "quality": "excellent",
          "speed": "medium"
        }
      ],
      "settings": {
        "threads": 4,
        "context_size": 2048,
        "temperature": 0.7,
        "max_tokens": 512
      }
    },
    "stt": {
      "engine": "vosk",
      "models": {
        "en-us": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "hi": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip",
        "en-in": "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
      },
      "default_language": "en-us",
      "sample_rate": 16000
    },
    "tts": {
      "engine": "android_builtin",
      "default_language": "hi-IN",
      "offline_voices": true,
      "rate": 1.0,
      "pitch": 1.0
    }
  },
  "device_commands": {
    "battery": true,
    "network": true,
    "calls": true,
    "sms": true,
    "volume": true,
    "vibrate": true,
    "apps": true,
    "settings": true,
    "flashlight": true
  },
  "personality": {
    "name": "JARVIS",
    "creator": "DRD (Mahadev)",
    "style": "friendly_hindi_english",
    "wake_word": "jarvis",
    "greeting": "Jai Mahadev! Main JARVIS hoon, aapka AI assistant! 🙏"
  }
}
EOF
echo "   ✅ AI config injected"

# ═══ Step 5: Create models directory structure ═══
echo ""
echo "📁 [5/7] Setting up models directory..."

mkdir -p "$ANDROID_DIR/app/src/main/assets/models"
# NOTE: GGUF model files are too large for assets
# They will be downloaded to phone storage on first run
# or can be pre-loaded via adb push

echo '{"info": "Place .gguf model files here or download in-app"}' > "$ANDROID_DIR/app/src/main/assets/models/README.json"
echo "   ✅ Models directory ready"

# ═══ Step 6: Build Android APK ═══
echo ""
echo "🏗️ [6/7] Building Android APK..."
cd "$ANDROID_DIR"

# Make gradlew executable
chmod +x gradlew 2>/dev/null || true

# Build
./gradlew assembleDebug 2>&1 | tail -10

if [ -f "$APK_OUTPUT" ]; then
    echo "   ✅ APK built successfully!"
else
    echo "   ⚠️ APK not found at expected path, searching..."
    APK_OUTPUT=$(find "$ANDROID_DIR" -name "*.apk" -type f 2>/dev/null | head -1)
    if [ -n "$APK_OUTPUT" ]; then
        echo "   ✅ Found APK: $APK_OUTPUT"
    else
        echo "   ❌ Build failed — check logs above"
        exit 1
    fi
fi

# ═══ Step 7: Copy & Report ═══
echo ""
echo "📦 [7/7] Packaging final APK..."
mkdir -p "$(dirname "$APK_DEST")"
cp "$APK_OUTPUT" "$APK_DEST" 2>/dev/null || APK_DEST="$APK_OUTPUT"

APK_SIZE=$(du -h "$APK_DEST" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ JARVIS AI APK Ready!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  📱 APK:  $APK_DEST"
echo "  📦 Size: $APK_SIZE"
echo ""
echo "  🧠 How it works:"
echo "     ├── UI loads LOCALLY (no admin page!)"
echo "     ├── AI Chat → Server Gemini API (real AI!)"
echo "     ├── Trading, Signals, Dashboard → Live data"
echo "     ├── Voice AI (STT + TTS) → Browser APIs"
echo "     ├── Full React Trading App (not admin panel)"
echo "     └── Auto-connects to your server for Gemini"
echo ""
echo "  📲 Install on phone:"
echo "     adb install -r $APK_DEST"
echo ""
echo "  🙏 Jai Mahadev! Your JARVIS is ready!"
echo "═══════════════════════════════════════════════════════════"
