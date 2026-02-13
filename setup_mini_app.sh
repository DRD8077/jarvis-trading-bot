#!/bin/bash
# JARVIS Telegram Mini App Setup Script

set -e

echo "🤖 JARVIS Telegram Mini App Setup"
echo "=================================="

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

# Check if we're in the right directory
if [ ! -f "jarvis_admin.py" ]; then
    print_error "Please run this script from the JARVIS project root directory"
    exit 1
fi

# Check prerequisites
print_info "Checking prerequisites..."
command -v node >/dev/null 2>&1 || { print_error "Node.js is required but not installed. Please install Node.js 18+"; exit 1; }
command -v npm >/dev/null 2>&1 || { print_error "npm is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed."; exit 1; }
print_success "Prerequisites check passed"

# Setup environment
print_info "Setting up environment..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@your_bot_username

# Mini App Configuration
MINI_APP_URL=https://your-mini-app.com

# Backend Configuration
BACKEND_URL=https://api.your-mini-app.com
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///./jarvis.db

# Payment Configuration
UPI_ID=your_upi_id@paytm
BANK_ACCOUNT=your_bank_account_details

# Encryption Keys (Generate new ones for production)
ENCRYPTION_KEY=your_32_byte_encryption_key_here
HMAC_KEY=your_32_byte_hmac_key_here

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Logging
LOG_LEVEL=INFO
TELEGRAM_BOT_LOG=telegram_bot.log
EOF
    print_warning "Created .env file - please update with your actual configuration!"
else
    print_success "Environment file already exists"
fi

# Install backend dependencies
print_info "Installing backend dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_success "Backend dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Setup frontend
print_info "Setting up Telegram Mini App frontend..."
if [ ! -d "telegram-mini-app" ]; then
    print_error "telegram-mini-app directory not found. Please ensure the Mini App files are present."
    exit 1
fi

cd telegram-mini-app

# Install frontend dependencies
print_info "Installing frontend dependencies..."
npm install
print_success "Frontend dependencies installed"

# Build frontend
print_info "Building frontend..."
npm run build
print_success "Frontend built successfully"

cd ..

# Make scripts executable
print_info "Setting up scripts..."
chmod +x deploy_mini_app.sh
chmod +x telegram-mini-app/monitor.sh 2>/dev/null || true
print_success "Scripts configured"

# Generate encryption keys
print_info "Generating encryption keys..."
python3 -c "
import os
import base64

# Generate encryption key (32 bytes)
encryption_key = base64.b64encode(os.urandom(32)).decode('utf-8')
hmac_key = base64.b64encode(os.urandom(32)).decode('utf-8')

print(f'ENCRYPTION_KEY={encryption_key}')
print(f'HMAC_KEY={hmac_key}')
" > temp_keys.txt

if [ -f "temp_keys.txt" ]; then
    print_success "Encryption keys generated"
    print_warning "Update your .env file with these keys:"
    cat temp_keys.txt
    rm temp_keys.txt
fi

echo ""
print_success "🎉 JARVIS Telegram Mini App setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Update .env file with your Telegram bot token and other settings"
echo "2. Create a Telegram bot with @BotFather"
echo "3. Set your Mini App domain in the bot settings"
echo "4. Run: python3 jarvis_admin.py (for backend)"
echo "5. Run: python3 telegram_mini_app_bot.py (for bot)"
echo "6. For production: ./deploy_mini_app.sh"
echo ""
echo "🔗 Useful Commands:"
echo "- Start backend: python3 jarvis_admin.py"
echo "- Start bot: python3 telegram_mini_app_bot.py"
echo "- Build frontend: cd telegram-mini-app && npm run build"
echo "- Development: cd telegram-mini-app && npm run dev"
echo ""
echo "📚 Documentation: telegram-mini-app/README.md"
echo ""
echo "🆘 Support: Check the README for troubleshooting and API docs"