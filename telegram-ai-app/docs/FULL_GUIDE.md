# JARVIS Telegram AI App - Complete Implementation Guide

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Documentation](#api-documentation)
7. [Frontend Implementation](#frontend-implementation)
8. [Backend Implementation](#backend-implementation)
9. [Bot Implementation](#bot-implementation)
10. [Database Schema](#database-schema)
11. [Security Implementation](#security-implementation)
12. [Payment Integration](#payment-integration)
13. [Deployment Guide](#deployment-guide)
14. [Testing Guide](#testing-guide)
15. [Troubleshooting](#troubleshooting)
16. [Performance Optimization](#performance-optimization)
17. [Future Enhancements](#future-enhancements)

---

## 🎯 Introduction

### What is JARVIS?
JARVIS is an AI-powered Telegram Mini App that provides intelligent assistance in Hindi and English, featuring voice input, secure authentication, and payment integration.

### Key Features
- 🤖 Advanced AI conversations in Hindi & English
- 🎙️ Voice input with speech recognition
- 🔐 Secure Telegram authentication
- 💰 Payment processing (UPI, Cards, Crypto)
- 📱 Mobile-first responsive design
- ⚙️ Customizable user settings
- ⭐ Premium subscription management
- 📊 Real-time chat with history
- 🎨 Dynamic theming (Light/Dark/Auto)

### Target Audience
- Indian users seeking AI assistance in Hindi
- Telegram users wanting integrated AI experiences
- Developers building Telegram Mini Apps
- Businesses needing AI-powered customer service

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram App  │────│  Telegram Bot   │────│   Mini App      │
│                 │    │                 │    │   (Frontend)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Express.js    │────│   MongoDB       │────│   AI Engine     │
│   Backend API   │    │   Database      │    │   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Razorpay      │────│   JWT Auth      │────│   WebSocket     │
│   Payments      │    │   Security      │    │   Real-time     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

#### Frontend (Mini App)
- **HTML5/CSS3**: Semantic markup and responsive design
- **Vanilla JavaScript**: No frameworks for optimal performance
- **Telegram Web App SDK**: Native Telegram integration
- **Web Speech API**: Voice input functionality
- **CSS Custom Properties**: Dynamic theming

#### Backend
- **Node.js**: Runtime environment
- **Express.js**: Web framework
- **MongoDB**: NoSQL database
- **Mongoose**: ODM for MongoDB
- **JWT**: Authentication tokens
- **bcrypt**: Password hashing (if needed)

#### AI & ML
- **OpenAI API**: Primary AI engine
- **Custom Prompts**: Hindi-optimized responses
- **Context Management**: Conversation history
- **Fallback System**: Rule-based responses

#### Security
- **Telegram Hash Verification**: Auth validation
- **HMAC-SHA256**: Request integrity
- **Rate Limiting**: DDoS protection
- **Input Sanitization**: XSS prevention

#### Payments
- **Razorpay**: Indian payment gateway
- **UPI Integration**: Indian payment systems
- **Webhook Verification**: Secure payment confirmation

---

## 📋 Prerequisites

### System Requirements
- **Node.js**: Version 18.0 or higher
- **MongoDB**: Version 4.4 or higher (or MongoDB Atlas)
- **npm**: Latest version
- **Git**: For version control

### Telegram Requirements
- **Telegram Account**: For bot creation and testing
- **Bot Token**: From @BotFather
- **Web App Domain**: HTTPS required for production

### API Keys (Optional but Recommended)
- **OpenAI API Key**: For AI functionality
- **Razorpay Keys**: For payment processing

### Development Tools
- **VS Code**: Recommended editor
- **Postman**: API testing
- **MongoDB Compass**: Database management
- **Browser DevTools**: Debugging

---

## 🚀 Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd telegram-ai-app
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Environment Setup
```bash
# Copy environment files
cp bot/.env.example bot/.env
cp .env.example .env

# Edit configuration
nano bot/.env
nano .env
```

### 4. Database Setup
```bash
# Local MongoDB
sudo systemctl start mongod

# Or use MongoDB Atlas
# Update MONGODB_URI in .env
```

### 5. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### 6. Start Application
```bash
# Development mode
./start-dev.sh

# Production mode
./start-prod.sh
```

---

## ⚙️ Configuration

### Environment Variables

#### Bot Configuration (`bot/.env`)
```env
# Telegram Bot Settings
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
WEBAPP_URL=https://your-domain.com
BACKEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=info
```

#### Backend Configuration (`.env`)
```env
# Server Settings
PORT=3000
NODE_ENV=development

# Database
MONGODB_URI=mongodb://localhost:27017/telegram_ai_app

# Security
JWT_SECRET=your-super-secure-jwt-secret-key-32-chars-min
ENCRYPTION_KEY=your-32-byte-encryption-key
HMAC_KEY=your-32-byte-hmac-key

# AI Settings
OPENAI_API_KEY=sk-your-openai-api-key
AI_MODEL=gpt-3.5-turbo
MAX_TOKENS=500
TEMPERATURE=0.7

# Payment Settings
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Rate Limiting
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX_REQUESTS=100

# CORS Settings
FRONTEND_URL=https://your-mini-app.com
ALLOWED_ORIGINS=https://web.telegram.org,https://telegram.me
```

### Telegram Bot Setup

1. **Create Bot with @BotFather**
   ```
   /newbot
   Bot Name: JARVIS AI Assistant
   Username: jarvis_ai_bot
   ```

2. **Configure Bot Settings**
   ```
   /setdescription
   Description: Your AI assistant powered by advanced AI 🤖

   /setabouttext
   About: JARVIS provides intelligent assistance in Hindi and English with voice support.

   /setcommands
   start - 🚀 Start JARVIS AI Assistant
   help - ❓ Get help and information
   settings - ⚙️ Access your settings
   premium - ⭐ Upgrade to premium
   ```

3. **Set Web App**
   ```
   /setmenubutton
   -> Web App
   URL: https://your-domain.com
   ```

### Domain Configuration

#### Development
- Use `http://localhost:3000` for backend
- Use `http://localhost:8080` for frontend (if separate)

#### Production
- HTTPS required for Telegram Mini Apps
- Domain must be accessible from Telegram
- SSL certificate from Let's Encrypt or similar

---

## 📡 API Documentation

### Base URL
```
Development: http://localhost:3000
Production: https://api.your-domain.com
```

### Authentication
All API requests require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "success": true,
  "message": "JARVIS AI App is running",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0"
}
```

#### Authentication
```http
POST /auth/verify
Content-Type: application/json

{
  "initData": "telegram_init_data_string"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 123456789,
    "name": "John Doe",
    "username": "johndoe",
    "language": "hi",
    "is_premium": false
  },
  "token": "jwt_token_here"
}
```

#### AI Chat
```http
POST /ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "नमस्ते, आप कैसे हैं?",
  "language": "hi"
}
```

**Response:**
```json
{
  "success": true,
  "reply": "नमस्ते! मैं ठीक हूं, धन्यवाद। आप कैसे हैं?",
  "response_time": 1250,
  "language": "hi"
}
```

#### Voice Input
```http
POST /ai/voice
Authorization: Bearer <token>
Content-Type: application/json

{
  "audioData": "base64_encoded_audio",
  "language": "hi"
}
```

#### User Profile
```http
GET /user/profile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 123456789,
    "name": "John Doe",
    "username": "johndoe",
    "language": "hi",
    "is_premium": false,
    "created_at": "2024-01-01T00:00:00.000Z",
    "settings": {
      "voice_enabled": true,
      "notifications": true,
      "theme": "auto"
    }
  }
}
```

#### Update Settings
```http
PUT /user/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "language": "en",
  "voice_enabled": false,
  "theme": "dark"
}
```

#### Chat History
```http
GET /user/chat-history?limit=20&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "chats": [
    {
      "message": "नमस्ते",
      "reply": "नमस्ते! मैं आपकी मदद कैसे कर सकता हूं?",
      "timestamp": "2024-01-01T00:00:00.000Z",
      "response_time": 800
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### Payment Order
```http
POST /payment/create-order
Authorization: Bearer <token>
Content-Type: application/json

{
  "plan_type": "monthly",
  "amount": 19900
}
```

**Response:**
```json
{
  "success": true,
  "order": {
    "id": "order_abc123",
    "amount": 19900,
    "currency": "INR",
    "plan_type": "monthly",
    "status": "created"
  }
}
```

---

## 🎨 Frontend Implementation

### File Structure
```
webapp/
├── index.html      # Main HTML structure
├── app.js          # Application logic
├── style.css       # Styles and themes
└── telegram.js     # Telegram SDK integration
```

### HTML Structure
```html
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS AI Assistant</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Loading Screen -->
    <div id="loading" class="screen">
        <div class="loading-spinner"></div>
        <h2>JARVIS लोड हो रहा है...</h2>
    </div>

    <!-- Auth Screen -->
    <div id="auth" class="screen hidden">
        <h1>🔐 प्रमाणीकरण</h1>
        <button id="authButton">Telegram से लॉगिन करें</button>
    </div>

    <!-- Main App -->
    <div id="app" class="app hidden">
        <header>
            <h1>JARVIS</h1>
            <div class="user-info">
                <span id="userName"></span>
                <span id="premiumBadge">⭐</span>
            </div>
        </header>

        <main>
            <!-- Chat Screen -->
            <div id="chatScreen" class="screen">
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="सवाल पूछें...">
                    <button id="voiceButton">🎙️</button>
                    <button id="sendButton">📤</button>
                </div>
            </div>

            <!-- Settings Screen -->
            <div id="settingsScreen" class="screen hidden">
                <h2>सेटिंग्स</h2>
                <div class="settings-group">
                    <label>भाषा:</label>
                    <select id="languageSelect">
                        <option value="hi">हिंदी</option>
                        <option value="en">English</option>
                    </select>
                </div>
                <!-- More settings... -->
            </div>
        </main>

        <nav class="bottom-nav">
            <button class="nav-item active" data-screen="chat">💬</button>
            <button class="nav-item" data-screen="settings">⚙️</button>
            <button class="nav-item" data-screen="premium">⭐</button>
        </nav>
    </div>

    <script src="telegram.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

### CSS Implementation
```css
:root {
    --primary-color: #0088cc;
    --bg-primary: #ffffff;
    --text-primary: #212121;
    --spacing-md: 16px;
    --radius-md: 8px;
}

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
}

.app {
    height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    background: linear-gradient(135deg, var(--primary-color), #006699);
    color: white;
    padding: var(--spacing-md);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-md);
}

.message {
    margin-bottom: var(--spacing-md);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
}

.message.user {
    background: var(--primary-color);
    color: white;
    margin-left: 20%;
}

.message.ai {
    background: #f0f0f0;
    margin-right: 20%;
}

.chat-input {
    display: flex;
    padding: var(--spacing-md);
    gap: var(--spacing-md);
    border-top: 1px solid #e0e0e0;
}

#messageInput {
    flex: 1;
    padding: var(--spacing-md);
    border: 2px solid #e0e0e0;
    border-radius: var(--radius-md);
    font-size: 16px;
}

.btn {
    padding: var(--spacing-md);
    border: none;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    cursor: pointer;
}

.bottom-nav {
    display: flex;
    background: white;
    border-top: 1px solid #e0e0e0;
}

.nav-item {
    flex: 1;
    padding: var(--spacing-md);
    border: none;
    background: none;
    font-size: 18px;
}

.nav-item.active {
    color: var(--primary-color);
}
```

### JavaScript Implementation
```javascript
class JarvisApp {
    constructor() {
        this.user = null;
        this.token = null;
        this.currentScreen = 'chat';
        this.init();
    }

    async init() {
        // Initialize Telegram Web App
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }

        this.setupEventListeners();
        await this.checkAuth();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchScreen(e.target.dataset.screen);
            });
        });

        // Chat input
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        document.getElementById('sendButton').addEventListener('click', () => {
            this.sendMessage();
        });

        // Voice input
        document.getElementById('voiceButton').addEventListener('click', () => {
            this.startVoiceInput();
        });

        // Auth
        document.getElementById('authButton').addEventListener('click', () => {
            this.authenticate();
        });
    }

    async checkAuth() {
        const tg = window.Telegram?.WebApp;
        if (!tg?.initData) {
            this.showAuthScreen();
            return;
        }

        try {
            const response = await this.apiCall('/auth/verify', {
                initData: tg.initData
            });

            if (response.success) {
                this.user = response.user;
                this.token = response.token;
                this.showApp();
            } else {
                this.showAuthScreen();
            }
        } catch (error) {
            this.showAuthScreen();
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        input.value = '';
        this.addMessage(message, 'user');

        try {
            const response = await this.apiCall('/ai/chat', { message });
            this.addMessage(response.reply, 'ai');
        } catch (error) {
            this.addMessage('क्षमा करें, कुछ गलती हुई।', 'ai');
        }
    }

    addMessage(text, type) {
        const messages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    switchScreen(screenName) {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById(screenName + 'Screen').classList.remove('hidden');

        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-screen="${screenName}"]`).classList.add('active');
    }

    async apiCall(endpoint, data) {
        const response = await fetch(`http://localhost:3000${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            body: JSON.stringify(data)
        });

        return await response.json();
    }

    showAuthScreen() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('auth').classList.remove('hidden');
    }

    showApp() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('auth').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

        if (this.user) {
            document.getElementById('userName').textContent = this.user.name;
        }
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisApp = new JarvisApp();
});
```

---

## 🔧 Backend Implementation

### Server Setup
```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: (process.env.RATE_LIMIT_WINDOW || 15) * 60 * 1000,
    max: process.env.RATE_LIMIT_MAX_REQUESTS || 100
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/auth', require('./routes/auth'));
app.use('/ai', require('./routes/ai'));
app.use('/user', require('./routes/user'));
app.use('/payment', require('./routes/payment'));

// Error handling
app.use((error, req, res, next) => {
    console.error(error);
    res.status(500).json({
        success: false,
        message: 'Internal server error'
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

### Authentication Route
```javascript
const express = require('express');
const { verifyTelegramAuth, generateJWT } = require('../auth');
const { User } = require('../db');

const router = express.Router();

router.post('/verify', async (req, res) => {
    try {
        const { initData } = req.body;

        if (!initData) {
            return res.status(400).json({
                success: false,
                message: 'initData is required'
            });
        }

        const userData = verifyTelegramAuth(initData, process.env.BOT_TOKEN);

        if (!userData) {
            return res.status(401).json({
                success: false,
                message: 'Invalid authentication'
            });
        }

        // Find or create user
        let user = await User.findOne({ telegram_id: userData.id });

        if (!user) {
            user = new User({
                telegram_id: userData.id,
                name: `${userData.first_name} ${userData.last_name || ''}`.trim(),
                username: userData.username,
                language: userData.language_code === 'hi' ? 'hi' : 'en'
            });
            await user.save();
        }

        const token = generateJWT(userData);

        res.json({
            success: true,
            user: {
                id: user.telegram_id,
                name: user.name,
                username: user.username,
                language: user.language,
                is_premium: user.is_premium
            },
            token
        });

    } catch (error) {
        console.error('Auth error:', error);
        res.status(500).json({
            success: false,
            message: 'Authentication failed'
        });
    }
});

module.exports = router;
```

### AI Route
```javascript
const express = require('express');
const { processAIQuery } = require('../ai');
const { Chat } = require('../db');
const authenticateToken = require('../middleware/auth');

const router = express.Router();

// Apply authentication to all routes
router.use(authenticateToken);

router.post('/chat', async (req, res) => {
    try {
        const { message, language = 'hi' } = req.body;
        const telegramId = req.user.telegram_id;

        if (!message?.trim()) {
            return res.status(400).json({
                success: false,
                message: 'Message is required'
            });
        }

        // Get recent chat history for context
        const recentChats = await Chat.find({ telegram_id: telegramId })
            .sort({ timestamp: -1 })
            .limit(5)
            .lean();

        const context = {
            previousMessages: recentChats.reverse().map(chat => [
                { role: 'user', content: chat.message },
                { role: 'assistant', content: chat.reply }
            ]).flat()
        };

        const startTime = Date.now();
        const reply = await processAIQuery(message, language, context);
        const responseTime = Date.now() - startTime;

        // Save to database
        await Chat.create({
            telegram_id: telegramId,
            message: message.trim(),
            reply,
            response_time: responseTime
        });

        res.json({
            success: true,
            reply,
            response_time: responseTime,
            language
        });

    } catch (error) {
        console.error('AI chat error:', error);
        res.status(500).json({
            success: false,
            message: 'AI processing failed',
            reply: 'क्षमा करें, कुछ तकनीकी दिक्कत है।'
        });
    }
});

router.post('/voice', async (req, res) => {
    // Voice processing implementation
    res.json({
        success: true,
        message: 'Voice processing not implemented yet'
    });
});

module.exports = router;
```

---

## 🤖 Bot Implementation

### Bot Setup
```javascript
const TelegramBot = require('node-telegram-bot-api');

const bot = new TelegramBot(process.env.BOT_TOKEN, { polling: true });

console.log('JARVIS Bot started');

// Command handlers
bot.onText(/\/start/, async (msg) => {
    const keyboard = {
        inline_keyboard: [
            [{
                text: '🚀 JARVIS खोलें',
                web_app: { url: process.env.WEBAPP_URL }
            }],
            [
                { text: '💬 चैट शुरू करें', callback_data: 'chat' },
                { text: '❓ मदद', callback_data: 'help' }
            ],
            [
                { text: '⚙️ सेटिंग्स', callback_data: 'settings' },
                { text: '⭐ प्रीमियम', callback_data: 'premium' }
            ]
        ]
    };

    await bot.sendMessage(msg.chat.id,
        `🤖 *नमस्ते ${msg.from.first_name}!*\n\nमैं जार्विस हूं, आपका AI असिस्टेंट।`,
        {
            parse_mode: 'Markdown',
            reply_markup: keyboard
        }
    );
});

bot.onText(/\/help/, async (msg) => {
    const helpText = `
🆘 *जार्विस हेल्प सेंटर*

📱 *मिनी ऐप इस्तेमाल करें:*
• Web App खोलकर पूर्ण फीचर्स का लाभ उठाएं
• हिंदी और अंग्रेजी दोनों में बात करें

🎙️ *वॉइस सपोर्ट:*
• मैसेज भेजें या वॉइस रिकॉर्ड करें
• AI समझकर जवाब देगा

💰 *प्रीमियम फीचर्स:*
• असीमित चैट
• प्राथमिकता सपोर्ट
• एडवांस्ड AI

📞 संपर्क: @jarvis_support
    `.trim();

    await bot.sendMessage(msg.chat.id, helpText, {
        parse_mode: 'Markdown'
    });
});

// Callback query handler
bot.on('callback_query', async (query) => {
    const data = query.data;
    const chatId = query.message.chat.id;

    switch (data) {
        case 'chat':
            await bot.sendMessage(chatId, '💬 Web App खोलकर चैट शुरू करें:', {
                reply_markup: {
                    inline_keyboard: [[{
                        text: '🚀 चैट शुरू करें',
                        web_app: { url: process.env.WEBAPP_URL }
                    }]]
                }
            });
            break;

        case 'help':
            // Handle help callback
            break;
    }

    await bot.answerCallbackQuery(query.id);
});

// Message handler for AI responses
bot.on('message', async (msg) => {
    // Skip commands
    if (msg.text?.startsWith('/')) return;

    // Basic response directing to Web App
    await bot.sendMessage(msg.chat.id,
        '🤖 *जार्विस:* अधिक सुविधाओं के लिए Web App खोलें!',
        {
            parse_mode: 'Markdown',
            reply_markup: {
                inline_keyboard: [[{
                    text: '🚀 ऐप खोलें',
                    web_app: { url: process.env.WEBAPP_URL }
                }]]
            }
        }
    );
});
```

---

## 🗄️ Database Schema

### User Collection
```javascript
{
  _id: ObjectId,
  telegram_id: Number,     // Unique Telegram user ID
  name: String,           // User's full name
  username: String,       // Telegram username (optional)
  language: String,       // 'hi' or 'en'
  is_premium: Boolean,    // Premium status
  subscription_end: Date, // Premium expiry
  created_at: Date,
  last_active: Date,
  settings: {
    voice_enabled: Boolean,
    notifications: Boolean,
    theme: String        // 'light', 'dark', 'auto'
  }
}
```

### Chat Collection
```javascript
{
  _id: ObjectId,
  telegram_id: Number,     // Reference to user
  message: String,        // User's message
  reply: String,          // AI response
  message_type: String,   // 'text', 'voice', 'image'
  ai_model: String,       // AI model used
  timestamp: Date,
  response_time: Number   // Response time in ms
}
```

### Payment Collection
```javascript
{
  _id: ObjectId,
  telegram_id: Number,
  transaction_id: String,  // Unique transaction ID
  amount: Number,         // Amount in paisa
  currency: String,       // 'INR'
  payment_method: String, // 'upi', 'card', 'wallet'
  status: String,         // 'pending', 'completed', 'failed'
  plan_type: String,      // 'monthly', 'yearly'
  razorpay_order_id: String,
  razorpay_payment_id: String,
  created_at: Date,
  completed_at: Date
}
```

### Session Collection (TTL)
```javascript
{
  _id: ObjectId,
  telegram_id: Number,
  session_token: String,  // JWT token
  expires_at: Date,       // Auto-delete after expiry
  ip_address: String,
  user_agent: String
}
```

### Indexes
```javascript
// User indexes
db.users.createIndex({ telegram_id: 1 }, { unique: true });
db.users.createIndex({ created_at: -1 });

// Chat indexes
db.chats.createIndex({ telegram_id: 1, timestamp: -1 });
db.chats.createIndex({ timestamp: -1 });

// Payment indexes
db.payments.createIndex({ telegram_id: 1, created_at: -1 });
db.payments.createIndex({ transaction_id: 1 }, { unique: true });

// Session indexes (TTL)
db.sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });
```

---

## 🔒 Security Implementation

### Authentication Flow
1. **Telegram Auth**: User opens Mini App
2. **Hash Verification**: Server verifies Telegram hash
3. **JWT Generation**: Create session token
4. **Token Validation**: All API calls require valid JWT

### Security Headers
```javascript
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "https://telegram.org"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.openai.com"]
    }
  }
}));
```

### Input Validation
```javascript
const validateMessage = (message) => {
  if (!message || typeof message !== 'string') return false;
  if (message.length > 1000) return false; // Max length
  if (/[<>\"'&]/.test(message)) return false; // Basic XSS check
  return true;
};
```

### Rate Limiting
```javascript
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests'
});
```

### Data Encryption
```javascript
const crypto = require('crypto');

const encrypt = (text) => {
  const cipher = crypto.createCipher('aes-256-cbc', process.env.ENCRYPTION_KEY);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return encrypted;
};

const decrypt = (encrypted) => {
  const decipher = crypto.createDecipher('aes-256-cbc', process.env.ENCRYPTION_KEY);
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
};
```

---

## 💳 Payment Integration

### Razorpay Setup
```javascript
const Razorpay = require('razorpay');

const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID,
  key_secret: process.env.RAZORPAY_KEY_SECRET
});
```

### Create Order
```javascript
app.post('/payment/create-order', authenticateToken, async (req, res) => {
  try {
    const { plan_type, amount } = req.body;

    const options = {
      amount: amount, // Amount in paisa
      currency: 'INR',
      receipt: `rcpt_${Date.now()}`,
      payment_capture: 1
    };

    const order = await razorpay.orders.create(options);

    // Save order to database
    await Payment.create({
      telegram_id: req.user.telegram_id,
      transaction_id: order.id,
      amount: amount,
      plan_type: plan_type,
      razorpay_order_id: order.id
    });

    res.json({
      success: true,
      order: {
        id: order.id,
        amount: order.amount,
        currency: order.currency
      }
    });

  } catch (error) {
    console.error('Order creation error:', error);
    res.status(500).json({
      success: false,
      message: 'Order creation failed'
    });
  }
});
```

### Webhook Handler
```javascript
app.post('/payment/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  try {
    const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
    const expectedSignature = crypto.createHmac('sha256', secret)
      .update(req.body)
      .digest('hex');

    const receivedSignature = req.headers['x-razorpay-signature'];

    if (expectedSignature !== receivedSignature) {
      return res.status(400).send('Invalid signature');
    }

    const event = JSON.parse(req.body);

    if (event.event === 'payment.captured') {
      const paymentId = event.payload.payment.entity.id;
      const orderId = event.payload.payment.entity.order_id;

      // Update payment status
      await Payment.findOneAndUpdate(
        { razorpay_order_id: orderId },
        {
          status: 'completed',
          razorpay_payment_id: paymentId,
          completed_at: new Date()
        }
      );

      // Update user premium status
      const payment = await Payment.findOne({ razorpay_order_id: orderId });
      if (payment) {
        const user = await User.findOne({ telegram_id: payment.telegram_id });
        if (user) {
          user.is_premium = true;
          user.subscription_end = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
          await user.save();
        }
      }
    }

    res.json({ success: true });

  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ success: false });
  }
});
```

---

## 🚀 Deployment Guide

### Production Requirements
- **Domain**: HTTPS-enabled domain
- **SSL Certificate**: Let's Encrypt or commercial
- **Reverse Proxy**: Nginx recommended
- **Process Manager**: PM2 for Node.js
- **Database**: MongoDB Atlas or dedicated server

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:3000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### PM2 Configuration
```json
{
  "name": "jarvis-ai-app",
  "script": "backend/server.js",
  "instances": "max",
  "exec_mode": "cluster",
  "env": {
    "NODE_ENV": "production",
    "PORT": 3000
  },
  "error_log": "/var/log/jarvis/app-error.log",
  "out_log": "/var/log/jarvis/app-out.log",
  "log_log": "/var/log/jarvis/app-combined.log",
  "time": true
}
```

### Environment Setup
```bash
# Production environment
NODE_ENV=production
PORT=3000
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/jarvis_prod
REDIS_URL=redis://localhost:6379
```

### SSL Setup with Let's Encrypt
```bash
sudo certbot --nginx -d your-domain.com -d api.your-domain.com
```

### Deployment Script
```bash
#!/bin/bash
# Production deployment script

echo "🚀 Deploying JARVIS AI App..."

# Pull latest changes
git pull origin main

# Install dependencies
npm ci --production=false

# Build assets (if any)
npm run build

# Run database migrations (if any)
npm run migrate

# Restart application
pm2 restart jarvis-ai-app

# Reload nginx
sudo nginx -t && sudo nginx -s reload

echo "✅ Deployment completed!"
```

---

## 🧪 Testing Guide

### Unit Tests
```javascript
const chai = require('chai');
const chaiHttp = require('chai-http');
const app = require('../backend/server');

chai.use(chaiHttp);
const { expect } = chai;

describe('Authentication', () => {
  it('should verify Telegram auth', (done) => {
    chai.request(app)
      .post('/auth/verify')
      .send({ initData: 'test_data' })
      .end((err, res) => {
        expect(res).to.have.status(200);
        expect(res.body).to.have.property('success');
        done();
      });
  });
});
```

### API Testing with Postman
```json
{
  "info": {
    "name": "JARVIS AI App API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:3000"
    }
  ]
}
```

### End-to-End Testing
```javascript
const puppeteer = require('puppeteer');

describe('Mini App E2E', () => {
  let browser;
  let page;

  before(async () => {
    browser = await puppeteer.launch();
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it('should load mini app', async () => {
    await page.goto('http://localhost:8080');
    await page.waitForSelector('#app');
    const title = await page.$eval('h1', el => el.textContent);
    expect(title).to.equal('JARVIS');
  });
});
```

---

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding
**Symptoms:** Bot doesn't reply to messages
**Solutions:**
1. Check BOT_TOKEN in environment
2. Verify bot is running: `ps aux | grep bot.js`
3. Check Telegram BotFather settings
4. Review bot logs for errors

#### Mini App Not Loading
**Symptoms:** Web App doesn't open in Telegram
**Solutions:**
1. Verify HTTPS in production
2. Check Web App URL in bot settings
3. Ensure domain is accessible
4. Check browser console for errors

#### AI Not Responding
**Symptoms:** Chat requests fail
**Solutions:**
1. Check OpenAI API key
2. Verify internet connection
3. Check API rate limits
4. Review AI service logs

#### Database Connection Failed
**Symptoms:** App crashes on startup
**Solutions:**
1. Verify MongoDB URI
2. Check MongoDB service status
3. Ensure network connectivity
4. Validate credentials

#### Payment Issues
**Symptoms:** Payments not processing
**Solutions:**
1. Check Razorpay credentials
2. Verify webhook URL
3. Check payment logs
4. Validate SSL certificates

### Debug Commands
```bash
# Check application status
pm2 status

# View application logs
pm2 logs jarvis-ai-app

# Check database connection
mongosh --eval "db.stats()"

# Test API endpoints
curl -X GET http://localhost:3000/health

# Check system resources
htop
df -h
free -h
```

### Log Analysis
```bash
# Search for errors in logs
grep "ERROR" /var/log/jarvis/*.log

# Monitor real-time logs
tail -f /var/log/jarvis/app-out.log

# Check Telegram bot logs
tail -f telegram_bot.log
```

---

## ⚡ Performance Optimization

### Database Optimization
```javascript
// Add indexes for frequently queried fields
db.users.createIndex({ telegram_id: 1 });
db.chats.createIndex({ telegram_id: 1, timestamp: -1 });

// Use aggregation pipelines for complex queries
const userStats = await Chat.aggregate([
  { $match: { telegram_id: userId } },
  { $group: { _id: null, count: { $sum: 1 }, avgResponseTime: { $avg: '$response_time' } } }
]);
```

### Caching Strategy
```javascript
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 300 }); // 5 minutes

// Cache user settings
const getUserSettings = async (userId) => {
  const cacheKey = `user_settings_${userId}`;
  let settings = cache.get(cacheKey);

  if (!settings) {
    settings = await User.findOne({ telegram_id: userId }, 'settings');
    cache.set(cacheKey, settings);
  }

  return settings;
};
```

### API Rate Limiting
```javascript
const rateLimit = require('express-rate-limit');

// Different limits for different endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: 'Too many authentication attempts'
});

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'API rate limit exceeded'
});

app.use('/auth/', authLimiter);
app.use('/api/', apiLimiter);
```

### Compression
```javascript
const compression = require('compression');

app.use(compression({
  level: 6, // Compression level
  threshold: 1024, // Only compress responses > 1KB
  filter: (req, res) => {
    if (req.headers['x-no-compression']) return false;
    return compression.filter(req, res);
  }
}));
```

### Connection Pooling
```javascript
// MongoDB connection with pooling
mongoose.connect(process.env.MONGODB_URI, {
  maxPoolSize: 10, // Maintain up to 10 socket connections
  serverSelectionTimeoutMS: 5000, // Keep trying to send operations for 5 seconds
  socketTimeoutMS: 45000, // Close sockets after 45 seconds of inactivity
  bufferCommands: false, // Disable mongoose buffering
  bufferMaxEntries: 0 // Disable mongoose buffering
});
```

---

## 🚀 Future Enhancements

### Phase 1: Core Improvements
- [ ] Voice input processing with speech-to-text
- [ ] Multi-language support (beyond Hindi/English)
- [ ] Advanced AI models integration
- [ ] Real-time notifications
- [ ] Chat export functionality

### Phase 2: Advanced Features
- [ ] File upload and processing
- [ ] Image recognition and analysis
- [ ] Voice response synthesis
- [ ] Group chat support
- [ ] Custom AI training

### Phase 3: Enterprise Features
- [ ] Team collaboration
- [ ] Analytics dashboard
- [ ] API access for third parties
- [ ] White-label solutions
- [ ] Advanced security features

### Technical Improvements
- [ ] GraphQL API implementation
- [ ] WebSocket for real-time features
- [ ] Redis caching layer
- [ ] Load balancing
- [ ] Microservices architecture

### Mobile App Development
- [ ] React Native Android app
- [ ] iOS app with SwiftUI
- [ ] Cross-platform features
- [ ] Offline functionality
- [ ] Push notifications

### Integration Opportunities
- [ ] WhatsApp Business API
- [ ] Slack integration
- [ ] Discord bot
- [ ] Web widget for websites
- [ ] REST API for developers

---

## 📞 Support & Community

### Getting Help
1. **Documentation**: Check this guide first
2. **GitHub Issues**: Report bugs and request features
3. **Telegram Group**: Join our community
4. **Email Support**: Contact our team

### Contributing
We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code of Conduct
- Be respectful and inclusive
- Follow coding best practices
- Test your changes thoroughly
- Document new features

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Telegram** for the amazing platform
- **OpenAI** for powerful AI capabilities
- **MongoDB** for reliable database solutions
- **Razorpay** for seamless payment processing
- **Node.js** community for excellent tools

---

*Built with ❤️ for the Indian AI community 🇮🇳*

**Last updated:** February 10, 2026
**Version:** 1.0.0