# 🧠 JARVIS AI Agent — Complete Offline AI for Android

## Jai Mahadev! 🙏 Yeh hai aapka **100% Offline AI Agent**

> **No Internet • No API Keys • No Cloud • Sab Phone ke Andar!**

---

## 🎯 What's Inside

| Component | Technology | Purpose |
|-----------|-----------|---------|
| 🧠 **LLM (Chat Brain)** | llama.cpp + GGUF models | On-device AI text generation |
| 🎤 **STT (Voice Input)** | Vosk | Offline speech-to-text (Hindi + English) |
| 🔊 **TTS (Voice Output)** | Android Built-in TTS | Offline text-to-speech |
| 📱 **Device Commands** | Native Android | Battery, Calls, Volume, Settings |
| 💬 **AI Chat UI** | React + Capacitor | Full chat with markdown, voice, commands |

---

## 📂 Project Structure

```
telegram-mini-app/
├── src/
│   ├── components/
│   │   └── AIAgent.jsx          ← 🧠 Main AI Agent UI (4 tabs)
│   └── services/
│       └── jarvisAIEngine.js    ← 🔌 JS Bridge to native plugins
│
├── android/app/src/main/java/com/jarvis/trading/
│   ├── MainActivity.java         ← Registers all plugins
│   └── plugins/
│       ├── LocalLLMPlugin.java   ← 🧠 llama.cpp server manager
│       ├── VoskSTTPlugin.java    ← 🎤 Vosk offline STT
│       ├── LocalTTSPlugin.java   ← 🔊 Android TTS wrapper
│       └── DeviceCommandsPlugin.java ← 📱 Phone control
│
├── android/app/build.gradle      ← Updated with Vosk, OkHttp deps
├── android/app/src/main/AndroidManifest.xml ← AI permissions added

Scripts:
├── build_apk_ai_agent.sh         ← 🏗️ One-click APK builder
└── setup_ai_models.sh            ← 📥 Model downloader
```

---

## 🚀 Quick Start (Codespace se Phone tak)

### Step 1: Build APK
```bash
bash build_apk_ai_agent.sh
```

### Step 2: Install on Phone
```bash
# USB se
adb install -r telegram-mini-app/dist/jarvis-ai-agent.apk

# Ya WiFi ADB se
adb connect <phone-ip>:5555
adb install -r telegram-mini-app/dist/jarvis-ai-agent.apk
```

### Step 3: Download AI Models (2 Options)

**Option A: In-App Download** (Recommended)
1. App khole → "AI Agent" tab pe jaao
2. "Models" tab pe click karo
3. "Download TinyLlama 1.1B" button dabao
4. STT model bhi download karo (English/Hindi)
5. Done! Start chatting! 🎉

**Option B: ADB se Push Karo** (Faster)
```bash
# Models download karo
bash setup_ai_models.sh   # Choose option 1 (TinyLlama) + 5 (Vosk English)

# Phone pe push karo
bash setup_ai_models.sh   # Choose option 9 (ADB push)

# Ya manually:
adb push ai_models/tinyllama-1.1b-chat-Q4_K_M.gguf \
    /data/data/com.jarvis.trading/files/models/
adb push ai_models/vosk-model-small-en-us-0.15/ \
    /data/data/com.jarvis.trading/files/vosk-models/
```

---

## 📱 App Features (All Buttons)

### 💬 Chat Tab
- Text input se AI se baat karo
- Voice button se bolke message bhejo
- AI ka response Markdown mein aata hai (bold, code, lists)
- Auto-speak: AI apna jawab bolega bhi (Hindi/English)
- Quick suggestions: Battery, Time, Market, Code, Hindi Chat

### ⚡ Commands Tab  
- **Battery**: Level, charging status, temperature
- **Time**: Current time, date, day
- **Network**: WiFi status, connection type
- **Device Info**: Brand, model, RAM, CPU cores
- **Volume Up/Down**: Media volume control
- **Vibrate**: Haptic feedback
- **Settings**: Open phone settings
- **Call/SMS**: Dial number directly
- **Open Browser**: Launch URL
- **WiFi/Bluetooth Settings**: Quick toggles

### 📦 Models Tab
- See installed LLM models
- Download recommended models (TinyLlama, Phi-3, Gemma, Llama-3.2)
- Download STT voice models (English/Hindi)
- Load/switch between models
- Model size and status info

### ⚙️ Settings Tab
- Voice Output toggle
- Auto-Speak toggle
- Language selection (Hindi, English IN, English US)
- Temperature slider (Precise ↔ Creative)
- Max Tokens slider (Short ↔ Long responses)
- Phone TTS settings shortcut
- AI Engine info

---

## 🧠 Recommended Models

| Model | Size | RAM Needed | Quality | Speed | Best For |
|-------|------|-----------|---------|-------|----------|
| **TinyLlama 1.1B** | 670MB | 3GB+ | Good | ⚡ Fast | Quick chat, commands |
| **Llama 3.2 1B** | 700MB | 3GB+ | Very Good | ⚡ Fast | General purpose |
| **Gemma 2B** | 1.5GB | 4GB+ | Good | 🔄 Medium | Multilingual |
| **Phi-3 Mini 3.8B** | 2.3GB | 6GB+ | Excellent | 🐢 Slower | Complex reasoning |
| **DeepSeek R1 1.5B** | 1.1GB | 4GB+ | Very Good | 🔄 Medium | Reasoning + Hindi |

> **Recommendation**: 3-4GB RAM wale phone pe TinyLlama ya Llama-3.2-1B best hai!

---

## 🎤 Voice Models (Vosk STT)

| Language | Model | Size | Download |
|----------|-------|------|----------|
| English US | vosk-model-small-en-us-0.15 | 40MB | In-app |
| Hindi | vosk-model-small-hi-0.22 | 250MB | In-app |
| English India | vosk-model-small-en-in-0.4 | 36MB | In-app |

---

## 🔧 Tech Details

### How LLM Works (On-Device)
1. **llama-server** binary runs on localhost:8787
2. GGUF model loaded into RAM
3. App sends OpenAI-compatible requests to localhost
4. Response streamed back to UI
5. No internet needed!

### How STT Works (Offline)
1. Vosk model loaded from phone storage
2. Microphone audio captured at 16kHz
3. Real-time speech recognition
4. Partial + final results via events
5. Hindi + English supported

### How TTS Works (Offline)  
1. Android's built-in TextToSpeech engine
2. Offline voice packs (download from Settings)
3. Hindi (hi-IN), English (en-IN, en-US)
4. Speed & pitch customizable

---

## 🔒 Privacy & Security

- ✅ **100% Offline** — AI runs entirely on phone
- ✅ **No data sent anywhere** — no cloud, no servers
- ✅ **No API keys** — no OpenAI, no Google, nothing
- ✅ **No tracking** — your conversations are private
- ✅ **Open-source models** — transparent AI

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "No model found" | Download a model from Models tab |
| Voice not working | Grant microphone permission, download Vosk model |
| TTS silent | Go to Settings → "Phone TTS Settings" → download offline voices |
| App crash on model load | Model too big for RAM — try TinyLlama 1.1B |
| Slow responses | Use Q4_K_M quantized models, set threads=4 |
| Build fails | Run `bash build_apk_ai_agent.sh` — it auto-fixes most issues |

---

## 🙏 Credits

- **LLM**: [llama.cpp](https://github.com/ggerganov/llama.cpp) by Georgi Gerganov
- **STT**: [Vosk](https://github.com/alphacep/vosk-api) by Alpha Cephei
- **TTS**: Android Built-in TextToSpeech
- **Models**: TinyLlama, Meta Llama, Google Gemma, Microsoft Phi
- **App Framework**: React + Capacitor

**Made with ❤️ by DRD • Jai Mahadev! 🕉️**
