# 📱 JARVIS Bot — Termux (Android) Setup Guide

## ⚡ QUICK START (3 Steps)

### Step 1: Termux Install karo
- **Google Play se MAT lo** (outdated hai)
- **F-Droid se lo:** https://f-droid.org/en/packages/com.termux/

### Step 2: Termux mein yeh paste karo
```bash
pkg update -y && pkg install -y git python
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ~/jarvis
cd ~/jarvis
bash termux_setup.sh
```

### Step 3: API Keys dalo jab script maange
- **Telegram Bot Token** (REQUIRED) — @BotFather se lo
- **Chat ID** (REQUIRED) — @userinfobot se lo
- Groq API Key (free) — https://console.groq.com
- Gemini API Key (free) — https://aistudio.google.com

---

## 🔧 Pehle Se Project GitHub Pe Push Karo (Laptop se)

Laptop pe terminal mein:
```bash
# Agar repo nahi banaya toh
git init
git add .
git commit -m "JARVIS bot"

# GitHub pe push karo
gh repo create jarvis-bot --private --push
# ya manually:
git remote add origin https://github.com/YOUR_USERNAME/jarvis-bot.git
git push -u origin main
```

Phir `termux_setup.sh` mein Line 19 edit karo:
```bash
GITHUB_REPO="YOUR_USERNAME/jarvis-bot"
```

---

## 📱 IMPORTANT: Android Settings (bot kill na ho)

### 1. Battery Optimization OFF karo
- Settings > Apps > Termux > Battery > Unrestricted

### 2. Termux Notification pin karo
- Jab Termux chalu ho, notification neeche aata hai
- Usse "pin" karo (notification bar mein)

### 3. Termux:Boot install karo (auto-start)
- F-Droid se Termux:Boot install karo
- `~/.termux/boot/` mein script rakho:
```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/jarvis.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/jarvis && bash termux_setup.sh
EOF
chmod +x ~/.termux/boot/jarvis.sh
```

---

## 🛑 Bot Control Commands

| Command | Description |
|---|---|
| `touch /tmp/jarvis_stop` | Bot band karo |
| `tail -f ~/jarvis/jarvis_bot.log` | Live logs dekho |
| `cat ~/jarvis/jarvis_bot.pid` | Bot PID dekho |
| `kill $(cat ~/jarvis/jarvis_bot.pid)` | Force kill |
| `cd ~/jarvis && bash termux_setup.sh` | Restart karo |

---

## 🔄 Code Update Karna (New features add karne ke baad)

Termux mein:
```bash
cd ~/jarvis
git pull origin main
# Phir restart:
touch /tmp/jarvis_stop
sleep 3
bash termux_setup.sh
```

---

## ⚠️ Troubleshooting

### "scikit-learn install nahi ho raha"
```bash
pkg install -y python-numpy python-scipy
pip install scikit-learn
```

### "Bot crash ho raha baar baar"
```bash
tail -50 ~/jarvis/jarvis_bot.log
```

### "Termux band ho jaata hai background mein"
- Battery optimization OFF karo (Step 1 upar)
- `termux-wake-lock` chala ke dekho

### "pip install fail"
```bash
pkg install -y build-essential
pip install --no-cache-dir PACKAGE_NAME
```

### Memory kam ho toh
Heavy ML packages skip karo — bot phir bhi chalega kyunki sab `try/except` mein hai.

---

## 🔐 Security Notes

- `.env` file mein API keys hain — **KABHI GitHub pe public repo mein mat dalo**
- Private repo use karo ya `.gitignore` mein `.env` add karo
- `jarvis_forever.sh` mein hardcoded keys hain — **HATAO unhe!**
