# JARVIS Telegram Mini App

A complete Android-app-like experience within Telegram, featuring AI-powered trading, secure payments, and real-time market data.

## 🚀 Features

### 🤖 AI-Powered Trading
- Real-time market signals and analysis
- AI-driven trading recommendations
- Risk management and portfolio tracking
- Multi-asset support (Stocks, Crypto, Options, Futures)

### 💰 Secure Payment System
- UPI deposits with instant processing
- Bank withdrawals with verification
- Encrypted wallet storage
- Transaction history and receipts

### 📱 Mobile-First Design
- Responsive design optimized for mobile
- Touch-friendly interface
- Offline-capable with service workers
- Push notifications support

### 🔒 Enterprise Security
- AES-256 encryption for sensitive data
- HMAC authentication for API calls
- Secure WebSocket connections
- GDPR-compliant data handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Mini App      │    │   Backend API   │
│   Client        │◄──►│   (React)       │◄──►│   (FastAPI)     │
│                 │    │                 │    │                 │
│ • Bot Commands  │    │ • Dashboard     │    │ • Trading Engine│
│ • Mini App Web  │    │ • Wallet        │    │ • Payment API   │
│ • Notifications │    │ • Trading       │    │ • WebSocket     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   External APIs │
                       │   (SQLite)      │    │                 │
                       │                 │    │ • NSE/BSE       │
                       │ • Users         │    │ • Crypto APIs   │
                       │ • Transactions  │    │ • Payment GW    │
                       │ • Signals       │    │ • SMS Service   │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
telegram-mini-app/
├── public/
│   ├── index.html          # Main HTML template
│   ├── manifest.json       # PWA manifest
│   └── icons/              # App icons
├── src/
│   ├── components/         # React components
│   │   ├── Dashboard.jsx   # Main dashboard
│   │   ├── Wallet.jsx      # Wallet management
│   │   ├── Trading.jsx     # Trading interface
│   │   ├── Settings.jsx    # User settings
│   │   └── Navigation.jsx  # Bottom navigation
│   ├── hooks/              # Custom React hooks
│   │   ├── useWebSocket.js # WebSocket connection
│   │   ├── useAuth.js      # Authentication
│   │   └── useApi.js       # API calls
│   ├── utils/              # Utility functions
│   │   ├── api.js          # API client
│   │   ├── encryption.js   # Encryption utilities
│   │   └── telegram.js     # Telegram SDK integration
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # App entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS config
└── README.md               # This file
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+
- Python 3.8+
- Telegram Bot Token
- Domain with SSL certificate

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd jarvis-telegram-mini-app
   ```

2. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt

   # Frontend
   cd telegram-mini-app
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Build and run:**
   ```bash
   # Build frontend
   npm run build

   # Start backend
   python jarvis_admin.py

   # Start Telegram bot
   python telegram_mini_app_bot.py
   ```

### Production Deployment

Use the automated deployment script:

```bash
chmod +x deploy_mini_app.sh
./deploy_mini_app.sh
```

This will:
- Install all dependencies
- Build the frontend
- Setup Nginx with SSL
- Configure systemd services
- Setup monitoring

## 🔧 Configuration

### Environment Variables

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@your_bot_username

# Mini App URLs
MINI_APP_URL=https://your-domain.com
BACKEND_URL=https://api.your-domain.com

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key_here
HMAC_KEY=your_32_byte_hmac_key_here

# Database
DATABASE_URL=sqlite:///./jarvis.db

# Payment
UPI_ID=merchant@paytm
BANK_ACCOUNT=account_details

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Set the Mini App URL in bot settings:
   ```
   /setmenubutton
   ```

## 📱 Usage

### For Users

1. **Start the bot:** Send `/start` to your bot
2. **Open Mini App:** Click "🚀 Open JARVIS Dashboard"
3. **Navigate:** Use bottom navigation or swipe gestures
4. **Trade:** View signals and execute trades
5. **Manage funds:** Deposit/withdraw from wallet

### For Developers

#### Adding New Features

1. Create component in `src/components/`
2. Add route in `App.jsx`
3. Update navigation in `Navigation.jsx`
4. Add API endpoints in backend

#### API Integration

```javascript
// Example API call
import { api } from '../utils/api';

const signals = await api.get('/api/signals');
```

#### WebSocket Usage

```javascript
// Real-time updates
import { useWebSocket } from '../hooks/useWebSocket';

const { data, sendMessage } = useWebSocket('/ws/updates');
```

## 🔒 Security

### Data Encryption
- All sensitive data encrypted with AES-256
- API keys and secrets stored securely
- End-to-end encryption for payments

### Authentication
- Telegram Web App authentication
- HMAC verification for API calls
- Session management with secure tokens

### Best Practices
- HTTPS only (required for Telegram Mini Apps)
- Content Security Policy headers
- Regular security audits
- Secure dependency updates

## 📊 API Documentation

### Authentication Endpoints

```
POST /api/auth/telegram    # Telegram auth verification
GET  /api/auth/me         # Get current user
```

### Trading Endpoints

```
GET  /api/signals         # Get trading signals
POST /api/trades          # Execute trade
GET  /api/portfolio       # Get portfolio
```

### Payment Endpoints

```
POST /api/wallet/deposit   # Request deposit
POST /api/wallet/withdraw  # Request withdrawal
GET  /api/transactions    # Get transaction history
```

### WebSocket Events

```
/ws/updates               # Real-time updates
/ws/signals               # Signal notifications
/ws/portfolio             # Portfolio changes
```

## 🧪 Testing

### Unit Tests
```bash
npm run test
```

### Integration Tests
```bash
npm run test:e2e
```

### Manual Testing Checklist
- [ ] Mini App opens in Telegram
- [ ] Authentication works
- [ ] Real-time updates function
- [ ] Payments process correctly
- [ ] Responsive design on mobile
- [ ] Offline functionality

## 🚀 Deployment

### Development
```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Production
```bash
# Automated deployment
./deploy_mini_app.sh

# Manual deployment
npm run build
# Copy dist/ to web server
# Configure reverse proxy
```

### Monitoring
```bash
# View system status
./monitor.sh

# Check logs
sudo journalctl -u jarvis-backend -f
sudo journalctl -u jarvis-telegram-bot -f
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

### Code Style
- Use ESLint and Prettier
- Follow React best practices
- Write comprehensive tests
- Document API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Docs](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

### Community
- [Telegram Channel](https://t.me/jarvis_trading)
- [Discord Server](https://discord.gg/jarvis)
- [GitHub Issues](https://github.com/jarvis/mini-app/issues)

### Contact
- Email: support@jarvis.ai
- Telegram: @jarvis_support

---

**Built with ❤️ by the JARVIS Team**

*Transforming Android app experiences into Telegram Mini Apps*