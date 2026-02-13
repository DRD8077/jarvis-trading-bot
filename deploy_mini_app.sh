#!/bin/bash
# JARVIS Telegram Mini App Deployment Script

set -e

echo "🚀 JARVIS Telegram Mini App Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINI_APP_DIR="$PROJECT_DIR/telegram-mini-app"
BACKEND_DIR="$PROJECT_DIR"
DOMAIN=${DOMAIN:-"your-mini-app.com"}
EMAIL=${EMAIL:-"admin@your-mini-app.com"}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi

    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi

    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3 first."
        exit 1
    fi

    print_success "Prerequisites check passed!"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."

    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@your_bot_username

# Mini App Configuration
MINI_APP_URL=https://$DOMAIN

# Backend Configuration
BACKEND_URL=https://api.$DOMAIN
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
        print_warning "Created .env file. Please update with your actual values!"
        print_warning "Especially: TELEGRAM_BOT_TOKEN, SECRET_KEY, ENCRYPTION_KEY, HMAC_KEY"
    else
        print_success "Environment file already exists"
    fi
}

# Install backend dependencies
install_backend_deps() {
    print_status "Installing backend dependencies..."

    cd "$BACKEND_DIR"

    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "Backend dependencies installed"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."

    if [ ! -d "$MINI_APP_DIR" ]; then
        print_error "Telegram Mini App directory not found!"
        exit 1
    fi

    cd "$MINI_APP_DIR"

    if [ -f "package.json" ]; then
        npm install
        print_success "Frontend dependencies installed"
    else
        print_error "package.json not found in telegram-mini-app directory!"
        exit 1
    fi
}

# Build frontend
build_frontend() {
    print_status "Building frontend..."

    cd "$MINI_APP_DIR"

    if [ -f "package.json" ]; then
        npm run build
        print_success "Frontend built successfully"
    else
        print_error "package.json not found!"
        exit 1
    fi
}

# Setup domain and SSL (using Let's Encrypt)
setup_ssl() {
    print_status "Setting up SSL certificate..."

    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        print_warning "Certbot not found. Installing..."
        sudo apt update
        sudo apt install -y certbot python3-certbot-nginx
    fi

    # Get SSL certificate
    sudo certbot certonly --standalone -d $DOMAIN -d api.$DOMAIN --email $EMAIL --agree-tos --non-interactive

    print_success "SSL certificates obtained"
}

# Setup Nginx
setup_nginx() {
    print_status "Setting up Nginx configuration..."

    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/jarvis-mini-app << EOF
server {
    listen 80;
    server_name $DOMAIN api.$DOMAIN;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Root directory for Mini App
    root $MINI_APP_DIR/dist;
    index index.html;

    # Handle client-side routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration (same as above)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # API server
    location / {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/jarvis-mini-app /etc/nginx/sites-enabled/

    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test configuration
    sudo nginx -t

    # Reload Nginx
    sudo systemctl reload nginx

    print_success "Nginx configured successfully"
}

# Setup systemd services
setup_services() {
    print_status "Setting up systemd services..."

    # Backend service
    sudo tee /etc/systemd/system/jarvis-backend.service << EOF
[Unit]
Description=JARVIS Backend API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
ExecStart=/usr/bin/python3 jarvis_admin.py
Restart=always
RestartSec=5
Environment=PATH=/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$BACKEND_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    # Telegram Bot service
    sudo tee /etc/systemd/system/jarvis-telegram-bot.service << EOF
[Unit]
Description=JARVIS Telegram Mini App Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
ExecStart=/usr/bin/python3 telegram_mini_app_bot.py
Restart=always
RestartSec=5
Environment=PATH=/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$BACKEND_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start services
    sudo systemctl daemon-reload
    sudo systemctl enable jarvis-backend
    sudo systemctl enable jarvis-telegram-bot
    sudo systemctl start jarvis-backend
    sudo systemctl start jarvis-telegram-bot

    print_success "Systemd services configured and started"
}

# Setup firewall
setup_firewall() {
    print_status "Setting up firewall..."

    # Allow SSH, HTTP, HTTPS
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable

    print_success "Firewall configured"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."

    # Install htop for monitoring
    sudo apt install -y htop

    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== JARVIS System Monitor ==="
echo "Date: $(date)"
echo ""

echo "=== Services Status ==="
sudo systemctl status jarvis-backend --no-pager -l | head -10
echo ""
sudo systemctl status jarvis-telegram-bot --no-pager -l | head -10
echo ""
sudo systemctl status nginx --no-pager -l | head -5
echo ""

echo "=== Resource Usage ==="
echo "Memory:"
free -h
echo ""
echo "Disk:"
df -h /
echo ""

echo "=== Network Connections ==="
netstat -tlnp | grep -E ':(80|443|8000)'
echo ""

echo "=== Recent Logs ==="
echo "Backend logs (last 5 lines):"
tail -5 /var/log/syslog | grep jarvis || echo "No recent backend logs"
echo ""
echo "Telegram bot logs (last 5 lines):"
tail -5 telegram_bot.log 2>/dev/null || echo "No telegram bot log file"
EOF

    chmod +x monitor.sh

    print_success "Monitoring setup complete"
}

# Main deployment function
main() {
    echo "Starting JARVIS Telegram Mini App deployment..."

    check_prerequisites
    setup_environment
    install_backend_deps
    install_frontend_deps
    build_frontend

    # Ask user if they want to setup domain/SSL
    read -p "Do you want to setup domain and SSL certificates? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_ssl
        setup_nginx
        setup_firewall
    else
        print_warning "Skipping domain/SSL setup. Make sure to configure web server manually."
    fi

    setup_services
    setup_monitoring

    print_success "🎉 JARVIS Telegram Mini App deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with actual values"
    echo "2. Configure your Telegram bot token"
    echo "3. Set up your domain DNS to point to this server"
    echo "4. Test the Mini App at https://$DOMAIN"
    echo ""
    echo "Useful commands:"
    echo "- View logs: ./monitor.sh"
    echo "- Restart backend: sudo systemctl restart jarvis-backend"
    echo "- Restart bot: sudo systemctl restart jarvis-telegram-bot"
    echo "- Check status: sudo systemctl status jarvis-backend jarvis-telegram-bot"
}

# Run main function
main "$@"