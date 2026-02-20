#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#   JARVIS Trading — Production APK Builder v5.0 (SDLC-Compliant)
#   ─────────────────────────────────────────────────────────────────
#   Usage:
#     ./build_apk_release.sh                  # Build debug APK
#     ./build_apk_release.sh --release        # Build signed release APK
#     ./build_apk_release.sh --release --aab  # Build AAB for Play Store
#     ./build_apk_release.sh --ci             # CI mode (no prompts)
#
#   SDLC Steps:
#     1. Pre-flight checks (Java, SDK, Node)
#     2. Frontend build (Vite + React)
#     3. Inject environment config
#     4. Capacitor sync
#     5. Gradle build (debug or release)
#     6. APK signing & verification
#     7. Output artifact with metadata
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── Configuration ───
PROJ_DIR="/workspaces/codespaces-blank/telegram-mini-app"
ANDROID_DIR="$PROJ_DIR/android"
OUTPUT_DIR="/workspaces/codespaces-blank/dist"
VERSION_FILE="/workspaces/codespaces-blank/version.json"
BUILD_MODE="debug"
BUILD_AAB=false
CI_MODE=false

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
ok()  { echo -e "${GREEN}  ✅ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
err() { echo -e "${RED}  ❌ $1${NC}"; exit 1; }

# ─── Parse args ───
for arg in "$@"; do
  case $arg in
    --release) BUILD_MODE="release" ;;
    --aab) BUILD_AAB=true ;;
    --ci) CI_MODE=true ;;
  esac
done

# ─── Banner ───
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🤖 JARVIS APK Builder v5.0 — SDLC Production Pipeline${NC}"
echo -e "${CYAN}  Mode: ${BUILD_MODE} | AAB: ${BUILD_AAB} | CI: ${CI_MODE}${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

START_TIME=$(date +%s)

# ═══════════════════════════════════════
#  Step 0: Pre-flight Checks
# ═══════════════════════════════════════
log "🔍 [0/7] Pre-flight checks..."

# Java
JAVA_PATHS=(
  "/usr/local/sdkman/candidates/java/21.0.9-ms"
  "/usr/local/sdkman/candidates/java/current"
  "/usr/lib/jvm/java-21-openjdk-amd64"
  "/usr/lib/jvm/java-17-openjdk-amd64"
)
for jpath in "${JAVA_PATHS[@]}"; do
  if [ -d "$jpath" ]; then
    export JAVA_HOME="$jpath"
    break
  fi
done
[ -z "${JAVA_HOME:-}" ] && err "Java not found. Install JDK 17+."
ok "Java: $JAVA_HOME"

# Android SDK
ANDROID_PATHS=("$HOME/android-sdk" "/usr/local/lib/android/sdk")
for apath in "${ANDROID_PATHS[@]}"; do
  if [ -d "$apath" ]; then
    export ANDROID_HOME="$apath"
    export ANDROID_SDK_ROOT="$apath"
    break
  fi
done
if [ -z "${ANDROID_HOME:-}" ]; then
  log "📦 Installing Android SDK..."
  mkdir -p ~/android-sdk
  export ANDROID_HOME=~/android-sdk
  export ANDROID_SDK_ROOT=~/android-sdk
  
  if [ ! -f ~/cmdline-tools.zip ]; then
    wget -q "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" -O ~/cmdline-tools.zip
  fi
  if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
    unzip -qo ~/cmdline-tools.zip -d ~/android-sdk/
    mkdir -p ~/android-sdk/cmdline-tools/latest
    mv ~/android-sdk/cmdline-tools/bin ~/android-sdk/cmdline-tools/latest/ 2>/dev/null || true
    mv ~/android-sdk/cmdline-tools/lib ~/android-sdk/cmdline-tools/latest/ 2>/dev/null || true
  fi
  export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
  yes | sdkmanager --licenses >/dev/null 2>&1 || true
  sdkmanager "platforms;android-36" "platforms;android-35" "build-tools;36.0.0" "build-tools;35.0.0" "platform-tools" 2>&1 | tail -5 || warn "SDK download partial"
fi
ok "Android SDK: $ANDROID_HOME"

# Node
command -v node >/dev/null 2>&1 || err "Node.js not found. Install Node 18+."
ok "Node: $(node --version)"

# ═══════════════════════════════════════
#  Step 1: Version management
# ═══════════════════════════════════════
log "📋 [1/7] Version management..."

# Read or create version
if [ -f "$VERSION_FILE" ]; then
  CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['version'])" 2>/dev/null || echo "7.0.0")
else
  CURRENT_VERSION="7.0.0"
fi

# Auto-increment build number
BUILD_NUM=$(python3 -c "
import json, os
vf = '$VERSION_FILE'
d = json.load(open(vf)) if os.path.exists(vf) else {'version': '7.0.0', 'build': 0}
d['build'] = d.get('build', 0) + 1
d['built_at'] = '$(date -Iseconds)'
d['mode'] = '$BUILD_MODE'
d['git_sha'] = '$(git rev-parse --short HEAD 2>/dev/null || echo unknown)'
json.dump(d, open(vf, 'w'), indent=2)
print(d['build'])
")

ok "Version: $CURRENT_VERSION (build #$BUILD_NUM)"

# ═══════════════════════════════════════
#  Step 2: Build React Frontend
# ═══════════════════════════════════════
log "🔨 [2/7] Building React frontend (Vite)..."
cd "$PROJ_DIR"

if [ ! -d "node_modules" ]; then
  npm ci --prefer-offline 2>/dev/null || npm install
fi

# Inject build-time env
export VITE_APP_VERSION="$CURRENT_VERSION"
export VITE_BUILD_NUM="$BUILD_NUM"
export VITE_BUILD_MODE="$BUILD_MODE"
export VITE_API_URL="${API_URL:-https://davidcrewai.shop}"

npm run build 2>&1 | tail -5
ok "Frontend built ($(find dist -name '*.js' | wc -l) JS bundles)"

# ═══════════════════════════════════════
#  Step 3: Inject runtime config
# ═══════════════════════════════════════
log "⚙️  [3/7] Injecting runtime config..."

API_BASE="${API_URL:-}"

cat > "$ANDROID_DIR/app/src/main/assets/jarvis_config.json" << EOF
{
  "app_name": "JARVIS AI Trading",
  "version": "$CURRENT_VERSION",
  "build": $BUILD_NUM,
  "api_base": "$API_BASE",
  "build_mode": "$BUILD_MODE",
  "built_at": "$(date -Iseconds)",
  "local_first": true,
  "features": {
    "ota_updates": false,
    "sse_push": true,
    "voice_assistant": true,
    "offline_ai": true,
    "social_trading": true,
    "backtester": true,
    "portfolio_charts": true,
    "biometric_auth": true,
    "push_notifications": true
  },
  "sse": {
    "enabled": true,
    "url": "/api/sse/subscribe?channels=all"
  },
  "voice": {
    "enabled": true,
    "language": "hi-IN",
    "chat_url": "/api/voice/chat"
  }
}
EOF
ok "Config injected (API: $API_BASE)"

# ═══════════════════════════════════════
#  Step 4: Capacitor Sync
# ═══════════════════════════════════════
log "📱 [4/7] Capacitor sync..."
cd "$PROJ_DIR"
npx cap sync android 2>&1 | tail -3
ok "Android synced"

# ═══════════════════════════════════════
#  Step 5: Gradle Build
# ═══════════════════════════════════════
log "🏗️  [5/7] Gradle build ($BUILD_MODE)..."
cd "$ANDROID_DIR"
chmod +x gradlew

if [ "$BUILD_MODE" == "release" ]; then
  if [ "$BUILD_AAB" == "true" ]; then
    ./gradlew bundleRelease 2>&1 | tail -5
    ARTIFACT=$(find . -name "*.aab" -path "*/release/*" | head -1)
    ARTIFACT_TYPE="AAB"
  else
    ./gradlew assembleRelease 2>&1 | tail -5
    ARTIFACT=$(find . -name "*.apk" -path "*/release/*" | head -1)
    ARTIFACT_TYPE="APK"
  fi
else
  ./gradlew assembleDebug 2>&1 | tail -5
  ARTIFACT=$(find . -name "*.apk" -path "*/debug/*" | head -1)
  ARTIFACT_TYPE="APK"
fi

[ -z "$ARTIFACT" ] && err "Build failed — no artifact found"
ok "Build successful: $ARTIFACT_TYPE"

# ═══════════════════════════════════════
#  Step 6: Copy & Verify
# ═══════════════════════════════════════
log "📦 [6/7] Packaging artifact..."
mkdir -p "$OUTPUT_DIR"

FINAL_NAME="JARVIS-v${CURRENT_VERSION}-b${BUILD_NUM}-${BUILD_MODE}"
if [ "$ARTIFACT_TYPE" == "AAB" ]; then
  FINAL_PATH="$OUTPUT_DIR/${FINAL_NAME}.aab"
else
  FINAL_PATH="$OUTPUT_DIR/${FINAL_NAME}.apk"
fi

cp "$ARTIFACT" "$FINAL_PATH"

# Also copy to root for easy access
ROOT_NAME="JARVIS-v${CURRENT_VERSION}-${BUILD_MODE}.apk"
cp "$ARTIFACT" "/workspaces/codespaces-blank/$ROOT_NAME" 2>/dev/null || true

ARTIFACT_SIZE=$(ls -lh "$FINAL_PATH" | awk '{print $5}')
ARTIFACT_SHA=$(sha256sum "$FINAL_PATH" | awk '{print $1}')
ok "Packaged: $FINAL_PATH ($ARTIFACT_SIZE)"

# ═══════════════════════════════════════
#  Step 7: Build Report
# ═══════════════════════════════════════
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log "📊 [7/7] Build report..."

# Save build metadata
cat > "$OUTPUT_DIR/build-report.json" << EOF
{
  "version": "$CURRENT_VERSION",
  "build": $BUILD_NUM,
  "mode": "$BUILD_MODE",
  "type": "$ARTIFACT_TYPE",
  "file": "$(basename $FINAL_PATH)",
  "size": "$ARTIFACT_SIZE",
  "sha256": "$ARTIFACT_SHA",
  "built_at": "$(date -Iseconds)",
  "duration_sec": $DURATION,
  "git_branch": "$(git branch --show-current 2>/dev/null || echo unknown)",
  "git_sha": "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)",
  "java": "$JAVA_HOME",
  "node": "$(node --version)",
  "api_base": "$API_BASE"
}
EOF

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ BUILD COMPLETE — JARVIS v$CURRENT_VERSION (build #$BUILD_NUM)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  📱 Type:     $ARTIFACT_TYPE ($BUILD_MODE)"
echo -e "  📏 Size:     $ARTIFACT_SIZE"
echo -e "  📂 Path:     $FINAL_PATH"
echo -e "  🔒 SHA256:   ${ARTIFACT_SHA:0:16}..."
echo -e "  ⏱️  Duration: ${DURATION}s"
echo -e "  🌐 API:      $API_BASE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Serve APK info for download
echo -e "  📥 Download locally:"
echo -e "     cp $FINAL_PATH ~/Downloads/"
echo ""
