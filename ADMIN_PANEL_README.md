# JARVIS Admin Panel - Mobile-Style Side Panel

## Overview
The JARVIS Admin Panel has been upgraded to a modern, mobile-first web interface with real-time updates, similar to Android mobile applications.

## Features

### 🎨 Mobile-First Design
- **Responsive Layout**: Adapts to all screen sizes from mobile to desktop
- **Side Panel Navigation**: Collapsible sidebar with smooth animations
- **Touch Gestures**: Swipe to open/close sidebar on mobile devices
- **PWA Ready**: Can be installed as a standalone app on mobile devices

### ⚡ Real-Time Updates
- **Live Statistics**: Dashboard updates automatically every 30 seconds
- **WebSocket Connection**: Real-time notifications for new users, approvals, and system events
- **Instant Actions**: Approve/reject requests with immediate UI updates
- **Activity Feed**: Live log of system activities

### 💰 Payment Management System
- **Wallet Overview**: View all user wallets with balances and transaction history
- **Deposit Tracking**: Monitor UPI deposits and verification status
- **Withdrawal Management**: Approve/reject bank withdrawals
- **Transaction History**: Complete audit trail of all financial transactions
- **Real-time Stats**: Live payment statistics and metrics

### 📱 Mobile App Experience
- **App-like Interface**: Modern UI with gradients and smooth transitions
- **Offline Manifest**: PWA manifest for app installation
- **Fast Loading**: Optimized for mobile networks
- **Gesture Support**: Swipe gestures for navigation

## How to Access

1. **Start the Server**:
   ```bash
   python jarvis_admin.py
   ```

2. **Open in Browser**:
   - Visit: `http://localhost:8000`
   - Or use the Simple Browser in VS Code

3. **Mobile Access**:
   - On mobile devices, visit the same URL
   - Add to home screen for app-like experience

## Navigation

### Sidebar Menu
- **Dashboard**: Overview with live statistics
- **Users**: Manage all registered users
- **Approvals**: Handle pending feature requests
- **Payments**: Complete payment and wallet management
- **Settings**: System configuration
- **Activity Logs**: Real-time system logs

### Mobile Features
- **Hamburger Menu**: Tap the menu icon to toggle sidebar
- **Swipe Gestures**: Swipe right to open, left to close sidebar
- **Responsive Tables**: Optimized for small screens

## Payment Management

### 💳 Wallet Management
- **View All Wallets**: See all user wallets with current balances
- **Credit/Debit**: Manually adjust wallet balances for admin purposes
- **Search Wallets**: Find specific users by name or wallet ID
- **Wallet Status**: Active/inactive status tracking

### 📥 Deposit System
- **UPI Integration**: Auto-verification system for UPI payments
- **QR Code Generation**: Users get branded QR codes for deposits
- **UTR Verification**: Enter transaction reference for instant crediting
- **Deposit History**: Complete log of all deposit transactions

### 📤 Withdrawal System
- **Bank Details**: Secure encrypted storage of bank information
- **Approval Workflow**: Admin approval required for withdrawals
- **Processing Status**: Track withdrawal status (pending/processing/completed)
- **Instant Refunds**: Reject withdrawals with automatic refunds

### 📊 Payment Statistics
- **Total Deposits**: Sum of all user deposits
- **Total Withdrawals**: Sum of all processed withdrawals
- **Active Wallets**: Number of wallets with positive balance
- **Pending Actions**: Count of pending withdrawals

## Real-Time Features

### Live Updates
- User count and activity stats refresh every 30 seconds
- New user registrations appear instantly
- Approval requests show up immediately
- System status indicators update in real-time

### WebSocket Connection
- Maintains persistent connection for instant updates
- Automatic reconnection if connection is lost
- Battery-efficient polling for mobile devices

## API Endpoints

The panel includes REST API endpoints for programmatic access:

### User Management
- `POST /approve/{req_id}` - Approve a request
- `POST /reject/{req_id}` - Reject a request
- `POST /upgrade/{chat_id}` - Upgrade user to premium

### Payment Management
- `POST /credit_wallet/{chat_id}` - Credit wallet balance
- `POST /debit_wallet/{chat_id}` - Debit wallet balance
- `POST /approve_withdrawal/{tx_ref}` - Approve withdrawal
- `POST /reject_withdrawal/{tx_ref}` - Reject withdrawal

- `WebSocket /ws` - Real-time updates

## Technical Details

### Technologies Used
- **FastAPI**: High-performance async web framework
- **WebSockets**: Real-time bidirectional communication
- **Jinja2**: Server-side templating
- **Bootstrap 5**: Responsive CSS framework
- **Font Awesome**: Icons and UI elements
- **AES-256 Encryption**: Secure wallet data storage

### Payment Security
- **Encrypted Wallets**: All wallet data encrypted with AES-256
- **HMAC Verification**: Transaction integrity checking
- **Secure Transactions**: Signed transaction references
- **Audit Trail**: Complete transaction history

### Real-Time Architecture
- Background tasks for periodic updates
- WebSocket broadcasting to all connected clients
- Event-driven notifications for system changes

## Installation as PWA

On mobile devices, users can:
1. Open the admin panel in their browser
2. Tap "Add to Home Screen"
3. Launch as a standalone app with app-like experience

## Security Notes

- Currently runs on localhost for development
- In production, add authentication and HTTPS
- Admin access is controlled by the existing permission system
- All payment data is encrypted at rest

## Payment Flow Examples

### User Deposit Process
1. User requests deposit via Telegram bot
2. Bot generates UPI QR code
3. User scans QR and makes payment
4. User enters UTR number for verification
5. Amount instantly credited to wallet
6. Admin can see transaction in real-time

### User Withdrawal Process
1. User sets bank details via bot
2. User requests withdrawal amount
3. Admin receives notification in panel
4. Admin approves/rejects withdrawal
5. If approved, amount transferred to bank
6. Status updates in real-time

## Future Enhancements

- Push notifications for critical events
- Offline data caching
- Advanced analytics and charts
- Multi-admin support
- Audit logs and compliance features
- Payment gateway integrations
- Automated KYC verification