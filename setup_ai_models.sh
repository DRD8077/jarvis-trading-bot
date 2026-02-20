#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   JARVIS AI Model Setup Script
#   Downloads models for offline AI usage
#   Run this AFTER building the APK and installing on phone
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📥 JARVIS AI Model Downloader"
echo "═══════════════════════════════════════════════════════════"
echo ""

MODELS_DIR="/workspaces/codespaces-blank/ai_models"
mkdir -p "$MODELS_DIR"

# ═══ Menu ═══
echo "Choose what to download:"
echo ""
echo "  LLM Models (for AI chat):"
echo "  1) TinyLlama 1.1B (670MB) — Fast, good quality"
echo "  2) Llama 3.2 1B (700MB) — Meta, latest gen"  
echo "  3) Phi-3 Mini 3.8B (2.3GB) — Microsoft, very smart"
echo "  4) Gemma 2B (1.5GB) — Google, multilingual"
echo ""
echo "  Voice Models (for STT):"
echo "  5) Vosk English US (40MB)"
echo "  6) Vosk Hindi (250MB)"
echo "  7) Vosk English India (36MB)"
echo ""
echo "  8) Download ALL recommended (2GB+ total)"
echo "  9) Push models to phone via ADB"
echo "  0) Exit"
echo ""
read -p "Enter choice (1-9): " choice

case $choice in
    1)
        echo "📥 Downloading TinyLlama 1.1B..."
        wget -c "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
            -O "$MODELS_DIR/tinyllama-1.1b-chat-Q4_K_M.gguf"
        echo "✅ Done!"
        ;;
    2)
        echo "📥 Downloading Llama 3.2 1B..."
        wget -c "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf" \
            -O "$MODELS_DIR/llama-3.2-1b-instruct-Q4_K_M.gguf"
        echo "✅ Done!"
        ;;
    3)
        echo "📥 Downloading Phi-3 Mini..."
        wget -c "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf" \
            -O "$MODELS_DIR/phi-3-mini-4k-instruct-q4.gguf"
        echo "✅ Done!"
        ;;
    4)
        echo "📥 Downloading Gemma 2B..."
        wget -c "https://huggingface.co/google/gemma-2b-it-GGUF/resolve/main/gemma-2b-it.Q4_K_M.gguf" \
            -O "$MODELS_DIR/gemma-2b-it-Q4_K_M.gguf"
        echo "✅ Done!"
        ;;
    5)
        echo "📥 Downloading Vosk English US..."
        wget -c "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" \
            -O "$MODELS_DIR/vosk-model-small-en-us.zip"
        cd "$MODELS_DIR" && unzip -o vosk-model-small-en-us.zip && rm vosk-model-small-en-us.zip
        echo "✅ Done!"
        ;;
    6)
        echo "📥 Downloading Vosk Hindi..."
        wget -c "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip" \
            -O "$MODELS_DIR/vosk-model-small-hi.zip"
        cd "$MODELS_DIR" && unzip -o vosk-model-small-hi.zip && rm vosk-model-small-hi.zip
        echo "✅ Done!"
        ;;
    7)
        echo "📥 Downloading Vosk English India..."
        wget -c "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip" \
            -O "$MODELS_DIR/vosk-model-small-en-in.zip"
        cd "$MODELS_DIR" && unzip -o vosk-model-small-en-in.zip && rm vosk-model-small-en-in.zip
        echo "✅ Done!"
        ;;
    8)
        echo "📥 Downloading ALL recommended models..."
        echo ""
        echo "--- TinyLlama 1.1B ---"
        wget -c "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
            -O "$MODELS_DIR/tinyllama-1.1b-chat-Q4_K_M.gguf"
        echo ""
        echo "--- Vosk English US ---"
        wget -c "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" \
            -O "$MODELS_DIR/vosk-en-us.zip"
        cd "$MODELS_DIR" && unzip -o vosk-en-us.zip && rm vosk-en-us.zip
        echo ""
        echo "--- Vosk Hindi ---"
        wget -c "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip" \
            -O "$MODELS_DIR/vosk-hi.zip"
        cd "$MODELS_DIR" && unzip -o vosk-hi.zip && rm vosk-hi.zip
        echo ""
        echo "✅ All models downloaded!"
        ;;
    9)
        echo "📲 Pushing models to phone via ADB..."
        echo ""
        
        # Check ADB
        if ! command -v adb &>/dev/null; then
            echo "❌ ADB not found. Install Android SDK platform-tools."
            exit 1
        fi
        
        # Check device
        DEVICE=$(adb devices | grep -v "List" | grep "device" | head -1)
        if [ -z "$DEVICE" ]; then
            echo "❌ No device connected. Connect phone via USB or WiFi ADB."
            echo "   USB: Enable USB debugging in Developer Options"
            echo "   WiFi: adb connect <phone-ip>:5555"
            exit 1
        fi
        
        APP_DIR="/data/data/com.jarvis.trading/files"
        
        # Push LLM models
        for model in "$MODELS_DIR"/*.gguf; do
            if [ -f "$model" ]; then
                echo "   📤 Pushing $(basename "$model")..."
                adb push "$model" "$APP_DIR/models/"
            fi
        done
        
        # Push Vosk models
        for vdir in "$MODELS_DIR"/vosk-model-*; do
            if [ -d "$vdir" ]; then
                echo "   📤 Pushing $(basename "$vdir")..."
                adb push "$vdir" "$APP_DIR/vosk-models/"
            fi
        done
        
        echo "✅ Models pushed to phone!"
        ;;
    0)
        echo "Bye! Jai Mahadev! 🙏"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📁 Models saved in: $MODELS_DIR"
echo ""
ls -lh "$MODELS_DIR/" 2>/dev/null
echo ""
echo "  📲 To push to phone: bash $0 (choose option 9)"
echo "  Or download in-app from the Models tab"
echo "═══════════════════════════════════════════════════════════"
