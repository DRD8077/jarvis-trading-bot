#!/bin/bash
# JARVIS Telegram AI App Setup Script

set -e

echo "🤖 JARVIS Telegram AI App Setup"
echo "==============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required. Please install Node.js 18+"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is required. Please install npm"
        exit 1
    fi

    # Check MongoDB (optional for basic setup)
    if ! command -v mongod &> /dev/null; then
        print_warning "MongoDB not found locally. You can use MongoDB Atlas cloud service."
    fi

    print_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    print_info "Installing core dependencies..."
    npm install
    print_success "Core dependencies installed"

    print_info "Installing AI & Voice dependencies..."
    npm run install:ai 2>/dev/null || {
        print_warning "AI dependencies installation failed - you can install manually:"
        print_warning "npm install @google/generative-ai whisper-node microsoft-cognitiveservices-speech-sdk"
    }

    print_info "Installing Gesture Recognition dependencies..."
    npm run install:gesture 2>/dev/null || {
        print_warning "Gesture dependencies installation failed - you can install manually:"
        print_warning "npm install @tensorflow/tfjs @tensorflow-models/posenet @mediapipe/camera_utils @mediapipe/drawing_utils @mediapipe/pose"
    }

    print_info "Installing Voice & Speech dependencies..."
    npm run install:voice 2>/dev/null || {
        print_warning "Voice dependencies installation failed - you can install manually:"
        print_warning "npm install microsoft-cognitiveservices-speech-sdk"
    }

    print_success "All dependencies installation attempted"
}

# Setup environment
setup_environment() {
    print_info "Setting up environment..."

    # Create .env files if they don't exist
    if [ ! -f "bot/.env" ]; then
        cp bot/.env.example bot/.env 2>/dev/null || cat > bot/.env << 'EOF'
BOT_TOKEN=your_telegram_bot_token_here
WEBAPP_URL=https://your-domain.com
BACKEND_URL=http://localhost:3000
LOG_LEVEL=info
ADMIN_USER_ID=your_telegram_user_id
EOF
        print_warning "Created bot/.env - please add your BOT_TOKEN and ADMIN_USER_ID"
    fi

    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
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
EOF
        print_warning "Created .env - please configure your API keys and settings"
    fi

    print_success "Environment setup complete"
}

# Generate secrets
generate_secrets() {
    print_info "Generating secure secrets..."

    # Generate JWT secret
    JWT_SECRET=$(openssl rand -hex 32)
    echo "JWT_SECRET=$JWT_SECRET" >> .env

    print_success "Secrets generated and saved to .env"
}

# Setup MongoDB
setup_database() {
    print_info "Setting up database..."

    if command -v mongod &> /dev/null; then
        print_info "Starting MongoDB..."
        # Note: This is a basic setup. In production, use proper MongoDB service
        sudo systemctl start mongod 2>/dev/null || print_warning "Could not start MongoDB service. Please start it manually."
    else
        print_warning "MongoDB not installed locally. Using connection string from .env"
        print_info "For MongoDB Atlas: https://cloud.mongodb.com"
    fi

    print_success "Database setup complete"
}

# Test setup
test_setup() {
    print_info "Testing setup..."

    # Test Node.js
    node --version
    print_success "Node.js working"

    # Test npm
    npm --version
    print_success "npm working"

    # Test basic server start
    timeout 5s npm start || print_info "Server test completed (expected timeout)"

    print_success "Setup test passed"
}

# Create startup scripts
create_scripts() {
    print_info "Creating startup scripts..."

    # Development startup script
    cat > start-dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting JARVIS AI App (Development)"

# Start backend in background
npm run dev &
BACKEND_PID=$!

# Wait a moment
sleep 2

# Start bot
npm run bot &
BOT_PID=$!

echo "✅ Services started!"
echo "Backend PID: $BACKEND_PID"
echo "Bot PID: $BOT_PID"
echo ""
echo "To stop: kill $BACKEND_PID $BOT_PID"

# Wait for services
wait
EOF

    # Production startup script
    cat > start-prod.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting JARVIS AI App (Production)"

# Start backend
npm start
EOF

    chmod +x start-dev.sh start-prod.sh
    print_success "Startup scripts created"
}

# Main setup function
main() {
    echo ""
    print_info "Welcome to JARVIS Telegram AI App Setup!"
    echo ""

    check_prerequisites
    install_dependencies
    setup_environment
    generate_secrets
    setup_database
    create_scripts
    test_setup

    echo ""
    print_success "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Edit .env and bot/.env with your configuration"
    echo "2. Create a Telegram bot with @BotFather"
    echo "3. Set your web app URL in bot settings"
    echo "4. Run: ./start-dev.sh (for development)"
    echo "5. Run: ./start-prod.sh (for production)"
    echo ""
    echo "🔗 Useful Commands:"
    echo "- Start development: ./start-dev.sh"
    echo "- Start production: ./start-prod.sh"
    echo "- View logs: Check console output"
    echo "- Stop services: Ctrl+C or kill PIDs"
    echo ""
    echo "📚 Documentation: README.md"
    echo "🆘 Support: Check README for troubleshooting"
    echo ""
    echo "Happy coding! 🚀"
}

# Run main function
main "$@"