# 🤖 JARVIS Telegram AI App

A complete AI-powered Telegram Mini App with Hindi support, voice input, secure authentication, and payment integration.

## ✨ Features

### Core Features
- **🤖 AI Assistant**: Powered by advanced AI with Hindi & English support
- **🎙️ Voice Input**: Speech-to-text with Hindi language support
- **🔐 Secure Auth**: Telegram Web App authentication
- **💰 Payment Ready**: UPI, Cards, Crypto payment integration
- **📱 Mobile-First**: Android-like interface optimized for Telegram

### Advanced Features
- **💬 Real-time Chat**: Instant AI responses with typing indicators
- **⚙️ Custom Settings**: Language, voice, theme preferences
- **⭐ Premium Plans**: Subscription management with Razorpay
- **📊 Chat History**: Persistent conversation storage
- **🎨 Theme Support**: Light/Dark/Auto themes
- **📞 Haptic Feedback**: Native mobile-like interactions

### 🚀 NEW: Live Speaking AI
- **🎙️ Live Voice Chat**: Real-time voice conversations (0.5-1 sec delay)
- **🔊 AI Speech Synthesis**: AI speaks responses in Hindi/English
- **🎯 Continuous Recognition**: Always listening mode
- **⚡ Web Speech API**: Browser-native voice processing
- **🔄 Real-time Processing**: Instant voice-to-text-to-AI-to-speech

### 🤖 NEW: Gesture Recognition
- **📷 Camera Integration**: Real-time pose detection
- **👋 Gesture Detection**: Wave, thumbs up, pointing, nodding
- **🎯 TensorFlow.js**: Advanced ML pose estimation
- **📊 Confidence Scoring**: Accurate gesture recognition
- **🎨 Visual Feedback**: Pose skeleton overlay
- **📱 Mobile Optimized**: Phone camera integration

## �️ Technology Stack

### Backend
- **Node.js** - Runtime environment
- **Express.js** - Web framework
- **MongoDB** - NoSQL database
- **Mongoose** - ODM for MongoDB
- **JWT** - Authentication tokens
- **Socket.IO** - Real-time communication

### Frontend
- **HTML5/CSS3** - Semantic markup & responsive design
- **Vanilla JavaScript** - No frameworks for optimal performance
- **Telegram Web App SDK** - Native Telegram integration
- **Web Speech API** - Voice input & synthesis
- **Socket.IO Client** - Real-time features

### AI & ML
- **OpenAI API** - Primary AI engine
- **Google Gemini API** - Alternative AI provider
- **Azure Speech Services** - Professional voice processing
- **Whisper** - Open-source speech recognition
- **TensorFlow.js** - Machine learning in browser
- **MediaPipe** - Pose and gesture detection

### Security & Payments
- **Telegram Hash Verification** - Secure authentication
- **HMAC-SHA256** - Request integrity
- **Rate Limiting** - DDoS protection
- **Razorpay** - Indian payment gateway

### Real-time Features
- **WebSocket (Socket.IO)** - Live communication
- **Web Speech API** - Voice synthesis & recognition
- **MediaStream API** - Camera access for gestures
- **PoseNet** - Real-time pose estimation

## �🚀 Quick Start

### Prerequisites
- Node.js 18+
- MongoDB
- Telegram Bot Token
- Optional: OpenAI API Key

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd telegram-ai-app
npm install
```

2. **Environment setup:**
```bash
# Copy environment file
cp bot/.env bot/.env.local

# Edit with your configuration
nano bot/.env.local
```

3. **Database setup:**
```bash
# Install MongoDB locally or use cloud service
# Update MONGODB_URI in .env
```

4. **Start the application:**
```bash
# Start backend
npm run start

# In another terminal, start bot
npm run bot
```

## 📋 Configuration

### Environment Variables

#### Bot Configuration (`bot/.env`)
```env
BOT_TOKEN=your_telegram_bot_token_here
WEBAPP_URL=https://your-domain.com
BACKEND_URL=http://localhost:3000
```

#### Backend Configuration
```env
MONGODB_URI=mongodb://localhost:27017/telegram_ai_app
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_ai_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus
JWT_SECRET=your_jwt_secret_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key
HMAC_KEY=your_32_byte_hmac_key
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
PORT=3000
NODE_ENV=development
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX_REQUESTS=100
FRONTEND_URL=https://your-mini-app.com
ALLOWED_ORIGINS=https://web.telegram.org,https://telegram.me
```

## 🏗️ Project Structure

```
telegram-ai-app/
├── bot/                    # Telegram Bot
│   ├── bot.js             # Main bot logic
│   ├── commands.js        # Bot commands & responses
│   └── .env              # Bot configuration
├── webapp/                # Telegram Mini App Frontend
│   ├── index.html        # Main HTML
│   ├── app.js            # Main app logic
│   ├── style.css         # Styles & themes
│   └── telegram.js       # Telegram SDK integration
├── backend/               # Node.js Backend
│   ├── server.js         # Express server
│   ├── auth.js           # Authentication & JWT
│   ├── ai.js             # AI processing & responses
│   └── db.js             # MongoDB models & connection
├── docs/                  # Documentation
│   └── FULL_GUIDE.pdf    # Complete setup guide
├── package.json          # Dependencies & scripts
└── README.md             # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/verify` - Telegram auth verification
- `GET /user/profile` - Get user profile
- `PUT /user/settings` - Update user settings

### AI Chat
- `POST /ai/chat` - Send message to AI
- `POST /ai/voice` - Voice input processing

### Payments
- `POST /payment/create-order` - Create payment order
- `POST /payment/webhook` - Payment webhook

### Chat History
- `GET /user/chat-history` - Get chat history

## 🎨 UI Components

### Screens
- **Chat Screen**: Main AI conversation interface
- **Settings Screen**: User preferences and configuration
- **Premium Screen**: Subscription plans and payments
- **Auth Screen**: Telegram authentication

### Features
- **Voice Input**: 🎙️ button with speech recognition
- **Message Bubbles**: User/AI message differentiation
- **Typing Indicators**: Real-time response feedback
- **Bottom Navigation**: Screen switching
- **Theme Support**: Dynamic light/dark themes

## 🤖 AI System

### Supported Languages
- **Hindi (hi)**: Primary language with cultural context
- **English (en)**: Fallback language

### AI Capabilities
- **Context Awareness**: Remembers conversation history
- **Voice Processing**: Speech-to-text integration
- **Smart Responses**: Human-like conversation
- **Error Handling**: Graceful failure management

### AI Prompts
The system uses specialized prompts for Hindi conversations, ensuring culturally appropriate and helpful responses.

## 💳 Payment Integration

### Supported Methods
- **UPI**: Indian payment system
- **Credit/Debit Cards**: International cards
- **Wallets**: Paytm, Google Pay, etc.
- **Net Banking**: Bank transfers

### Premium Plans
- **Monthly**: ₹199/month
- **Yearly**: ₹1,999/year (17% savings)

## 🔒 Security

### Authentication
- **Telegram Hash Verification**: Server-side auth validation
- **JWT Tokens**: Secure API access
- **Session Management**: Temporary session handling

### Data Protection
- **AES Encryption**: Sensitive data encryption
- **HMAC Validation**: Request integrity
- **Rate Limiting**: DDoS protection

## 📱 Telegram Integration

### Web App Features
- **Full Screen**: Expands to full viewport
- **Haptic Feedback**: Native mobile interactions
- **Theme Sync**: Matches Telegram theme
- **Safe Area**: Notch device support

### Bot Commands
- `/start` - Welcome and main menu
- `/help` - Help and information
- `/settings` - Settings access
- `/premium` - Premium subscription

## 🚀 Deployment

### Development
```bash
npm run dev    # Development with nodemon
npm run bot    # Start Telegram bot
```

### Production
```bash
npm run build  # Build for production
npm start      # Start production server
```

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## 🧪 Testing

### Manual Testing
1. **Bot Testing**: Send commands to your bot
2. **Web App Testing**: Open via Telegram
3. **API Testing**: Use tools like Postman
4. **Voice Testing**: Test speech recognition

### Automated Testing
```bash
npm test        # Run test suite
npm run test:watch  # Watch mode testing
```

## 📊 Monitoring

### Health Checks
- `GET /health` - Application health status
- Database connection monitoring
- API response time tracking

### Logging
- Request/response logging
- Error tracking
- User activity monitoring

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**
- Check BOT_TOKEN in environment
- Verify bot is running: `ps aux | grep bot.js`

**Web App not loading:**
- Check WEBAPP_URL configuration
- Verify HTTPS in production

**AI not responding:**
- Check OpenAI API key
- Verify internet connection

**Database connection failed:**
- Check MONGODB_URI
- Verify MongoDB is running

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 📞 Support

- **Documentation**: Check `docs/FULL_GUIDE.pdf`
- **Issues**: GitHub Issues
- **Telegram**: @jarvis_support

## 🙏 Acknowledgments

- Telegram Web App platform
- OpenAI for AI capabilities
- MongoDB for database
- Express.js community

---

**Built with ❤️ for the Indian AI community** 🇮🇳