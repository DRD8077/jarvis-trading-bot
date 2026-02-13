// JARVIS Telegram Mini App
// Main application logic

class JarvisApp {
    constructor() {
        // Check if running in Telegram WebApp
        this.isTelegramWebApp = window.Telegram && window.Telegram.WebApp;
        this.tg = this.isTelegramWebApp ? window.Telegram.WebApp : null;

        this.currentScreen = 'homeScreen'; // Changed from 'chat' to 'homeScreen'
        this.user = null;
        this.token = null;
        this.socket = null;
        this.settings = {
            language: 'hi',
            voiceEnabled: true,
            notifications: true,
            theme: 'auto'
        };
        this.chatHistory = [];
        this.recognition = null;
        this.isListening = false;
        this.liveVoiceActive = false;
        this.gestureActive = false;
        this.poseNet = null;
        this.camera = null;
        this.emotionDetectionActive = false;
        this.blazeFaceModel = null;
        this.emotionHistory = [];
        this.currentEmotions = null;

        // Trading data
        this.marketData = {
            nifty: { value: 22500.00, change: 125.50, changePercent: 0.56 },
            sensex: { value: 73500.00, change: 350.25, changePercent: 0.48 }
        };
        this.portfolio = [];
        this.watchlist = ['RELIANCE', 'TCS', 'INFY', 'HDFC'];

        this.init();
    }

    async init() {
        try {
            // Initialize Telegram Web App if available
            if (this.isTelegramWebApp) {
                this.tg.ready();
                this.tg.expand();

                // Get user data from Telegram
                if (this.tg.initDataUnsafe && this.tg.initDataUnsafe.user) {
                    this.user = this.tg.initDataUnsafe.user;
                }
            } else {
                // Fallback for testing outside Telegram
                console.log('Running outside Telegram WebApp - using test mode');
                this.user = {
                    id: 123456789,
                    first_name: 'Test',
                    last_name: 'User',
                    username: 'testuser',
                    language_code: 'en'
                };
            }

            // Initialize Socket.IO
            this.initializeSocket();

            // Set theme
            this.applyTheme();

            // Setup voice recognition
            this.setupVoiceRecognition();

            // Setup gesture recognition
            this.setupGestureRecognition();

            // Setup emotion detection
            this.setupEmotionDetection();

            // Setup event listeners
            this.setupEventListeners();

            // Check authentication
            await this.checkAuth();

            // Load initial screen
            this.switchScreen('homeScreen');

        } catch (error) {
            console.error('App initialization error:', error);
            this.showError('App initialization failed');
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const screen = e.currentTarget.dataset.screen;
                this.switchScreen(screen);
            });
        });

        // Telegram WebApp events (only if available)
        if (this.isTelegramWebApp) {
            this.tg.onEvent('themeChanged', () => this.applyTheme());
        }

        // Trading actions
        document.getElementById('buyBtn').addEventListener('click', () => this.showBuyDialog());
        document.getElementById('sellBtn').addEventListener('click', () => this.showSellDialog());
        document.getElementById('watchlistBtn').addEventListener('click', () => this.switchScreen('marketsScreen'));
        document.getElementById('newsBtn').addEventListener('click', () => this.showNews());

        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => this.searchStocks());
        document.getElementById('stockSearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchStocks();
        });

        // Portfolio actions
        document.getElementById('addHoldingBtn').addEventListener('click', () => this.showAddHoldingDialog());
        document.getElementById('viewReportsBtn').addEventListener('click', () => this.showReports());

        // AI Chat
        const aiMessageInput = document.getElementById('aiMessageInput');
        const aiSendButton = document.getElementById('aiSendButton');

        aiMessageInput.addEventListener('input', () => {
            aiSendButton.disabled = !aiMessageInput.value.trim();
        });

        aiMessageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendAIMessage();
            }
        });

        aiSendButton.addEventListener('click', () => this.sendAIMessage());

        // Quick questions
        document.querySelectorAll('.quick-q-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.textContent;
                this.sendAIQuickQuestion(question);
            });
        });

        // Profile menu
        document.getElementById('settingsMenu').addEventListener('click', () => this.switchScreen('settingsScreen'));
        document.getElementById('subscriptionMenu').addEventListener('click', () => this.showSubscription());
        document.getElementById('helpMenu').addEventListener('click', () => this.showHelp());
        document.getElementById('logoutMenu').addEventListener('click', () => this.logout());

        // Chat input (legacy)
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        if (messageInput) {
            messageInput.addEventListener('input', () => {
                sendButton.disabled = !messageInput.value.trim();
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }

        // Voice button
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            voiceButton.addEventListener('click', () => this.toggleVoice());
        }

        // Live voice button
        document.getElementById('liveVoiceButton').addEventListener('click', () => {
            this.toggleLiveVoice();
        });

        // Gesture button
        document.getElementById('gestureButton').addEventListener('click', () => {
            this.toggleGestureRecognition();
        });

        // Emotion button
        document.getElementById('emotionButton').addEventListener('click', () => {
            this.toggleEmotionDetection();
        });

        // Stop live voice
        document.getElementById('stopLiveVoiceButton').addEventListener('click', () => {
            this.stopLiveVoice();
        });

        // Stop gesture
        document.getElementById('stopGestureButton').addEventListener('click', () => {
            this.stopGestureRecognition();
        });

        // Clear chat
        document.getElementById('clearChatButton').addEventListener('click', () => this.clearChat());

        // Settings
        document.getElementById('saveSettingsButton').addEventListener('click', () => this.saveSettings());
        document.getElementById('resetSettingsButton').addEventListener('click', () => this.resetSettings());

        // Premium
        document.querySelectorAll('.btn-premium').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const plan = e.currentTarget.dataset.plan;
                this.purchasePremium(plan);
            });
        });

        // Auth
        document.getElementById('authButton').addEventListener('click', () => this.authenticate());

        // Theme changes
        if (this.isTelegramWebApp) {
            this.tg.onEvent('themeChanged', () => this.applyTheme());
        }
    }

    async checkAuth() {
        try {
            // Show loading
            this.showLoading();

            // Get user data (from Telegram or test mode)
            const tgUser = this.isTelegramWebApp ? this.tg.initDataUnsafe?.user : this.user;

            if (!tgUser) {
                this.showAuthScreen();
                return;
            }

            // Authenticate with backend (skip for test mode)
            if (this.isTelegramWebApp) {
                const response = await this.apiCall('/auth/verify', {
                    initData: this.tg.initData
                });

                if (response.success) {
                    this.user = response.user;
                    this.token = response.token;

                    // Load user settings
                    await this.loadUserSettings();

                    // Show main app
                    this.showApp();

                    // Load chat history
                    await this.loadChatHistory();

                } else {
                    throw new Error(response.message || 'Authentication failed');
                }
            } else {
                // Test mode - skip authentication
                // Load user settings
                await this.loadUserSettings();

                // Show main app
                this.showApp();

                // Load chat history
                await this.loadChatHistory();
            }

        } catch (error) {
            console.error('Auth check error:', error);
            this.showAuthScreen();
        } finally {
            this.hideLoading();
        }
    }

    async authenticate() {
        try {
            const tgUser = this.tg.initDataUnsafe?.user;

            if (!tgUser) {
                this.showError('Telegram user data not available');
                return;
            }

            const response = await this.apiCall('/auth/verify', {
                initData: this.tg.initData
            });

            if (response.success) {
                this.user = response.user;
                this.token = response.token;
                this.showApp();
            } else {
                throw new Error(response.message || 'Authentication failed');
            }

        } catch (error) {
            console.error('Authentication error:', error);
            this.showError('Authentication failed. Please try again.');
        }
    }

    async loadUserSettings() {
        try {
            const response = await this.apiCall('/user/profile');

            if (response.success) {
                this.settings = { ...this.settings, ...response.user.settings };
                this.applySettings();
            }
        } catch (error) {
            console.error('Load settings error:', error);
        }
    }

    async loadChatHistory() {
        try {
            const response = await this.apiCall('/user/chat-history?limit=20');

            if (response.success && response.chats) {
                this.chatHistory = response.chats.reverse();
                this.renderChatHistory();
            }
        } catch (error) {
            console.error('Load chat history error:', error);
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        // Clear input
        messageInput.value = '';

        // Add user message to chat
        this.addMessage(message, 'user');

        // Disable send button
        document.getElementById('sendButton').disabled = true;

        try {
            // Show typing indicator
            this.showTyping();

            // Send to AI
            const response = await this.apiCall('/ai/chat', {
                message: message,
                language: this.settings.language
            });

            // Hide typing indicator
            this.hideTyping();

            if (response.success) {
                this.addMessage(response.reply, 'ai', response.response_time);
            } else {
                throw new Error(response.message || 'AI response failed');
            }

        } catch (error) {
            console.error('Send message error:', error);
            this.hideTyping();
            this.addMessage('क्षमा करें, कुछ तकनीकी दिक्कत है। बाद में फिर से कोशिश करें।', 'ai');
        }
    }

    setupVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Voice recognition not supported');
            document.getElementById('voiceButton').style.display = 'none';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        this.recognition.lang = this.settings.language === 'hi' ? 'hi-IN' : 'en-US';
        this.recognition.continuous = false;
        this.recognition.interimResults = false;

        this.recognition.onstart = () => {
            this.isListening = true;
            document.getElementById('voiceButton').textContent = '🎙️';
            document.getElementById('voiceButton').style.backgroundColor = '#f44336';
            if (this.isTelegramWebApp && this.tg.HapticFeedback) {
                this.tg.HapticFeedback.impactOccurred('medium');
            }
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('messageInput').value = transcript;
            document.getElementById('sendButton').disabled = false;
        };

        this.recognition.onend = () => {
            this.isListening = false;
            document.getElementById('voiceButton').textContent = '🎙️';
            document.getElementById('voiceButton').style.backgroundColor = '';
        };

        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.isListening = false;
            document.getElementById('voiceButton').textContent = '🎙️';
            document.getElementById('voiceButton').style.backgroundColor = '';
        };
    }

    toggleVoice() {
        if (!this.settings.voiceEnabled) {
            this.showError('Voice input is disabled in settings');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.lang = this.settings.language === 'hi' ? 'hi-IN' : 'en-US';
            this.recognition.start();
        }
    }

    addMessage(text, type, responseTime = null) {
        const messagesContainer = document.getElementById('chatMessages');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} fade-in`;

        const avatar = type === 'ai' ? '<div class="ai-avatar">🤖</div>' : '';

        const timeInfo = responseTime ? `<small class="text-secondary">${responseTime}ms</small>` : '';

        messageDiv.innerHTML = `
            ${avatar}
            <div class="message-content">
                <div class="message-bubble">${this.formatMessage(text)}</div>
                ${timeInfo}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Add to history
        this.chatHistory.push({
            message: type === 'user' ? text : null,
            reply: type === 'ai' ? text : null,
            timestamp: new Date(),
            type: type
        });
    }

    formatMessage(text) {
        // Basic formatting - convert line breaks, links, etc.
        return text
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    showTyping() {
        const messagesContainer = document.getElementById('chatMessages');

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai fade-in';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    renderChatHistory() {
        const messagesContainer = document.getElementById('chatMessages');

        // Clear existing messages except welcome
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            messagesContainer.appendChild(welcomeMessage);
        }

        // Render chat history
        this.chatHistory.forEach(chat => {
            if (chat.message) {
                this.addMessage(chat.message, 'user');
            }
            if (chat.reply) {
                this.addMessage(chat.reply, 'ai');
            }
        });
    }

    clearChat() {
        if (confirm('क्या आप सच में चैट को क्लियर करना चाहते हैं?')) {
            const messagesContainer = document.getElementById('chatMessages');
            const welcomeMessage = messagesContainer.querySelector('.welcome-message');

            messagesContainer.innerHTML = '';
            if (welcomeMessage) {
                messagesContainer.appendChild(welcomeMessage);
            }

            this.chatHistory = [];
        }
    }

    switchScreen(screenName) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.add('hidden');
        });

        // Show selected screen
        const targetScreen = document.getElementById(screenName + 'Screen');
        if (targetScreen) {
            targetScreen.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        const navItem = document.querySelector(`[data-screen="${screenName}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }

        this.currentScreen = screenName;
    }

    async saveSettings() {
        try {
            const newSettings = {
                language: document.getElementById('languageSelect').value,
                voice_enabled: document.getElementById('voiceEnabled').checked,
                notifications: document.getElementById('notificationsEnabled').checked,
                theme: document.getElementById('themeSelect').value
            };

            const response = await this.apiCall('/user/settings', newSettings);

            if (response.success) {
                this.settings = { ...this.settings, ...newSettings };
                this.applySettings();
                this.showSuccess('सेटिंग्स सेव हो गईं!');
            } else {
                throw new Error(response.message || 'Settings save failed');
            }

        } catch (error) {
            console.error('Save settings error:', error);
            this.showError('सेटिंग्स सेव करने में गलती');
        }
    }

    resetSettings() {
        if (confirm('क्या आप डिफॉल्ट सेटिंग्स पर रीसेट करना चाहते हैं?')) {
            document.getElementById('languageSelect').value = 'hi';
            document.getElementById('voiceEnabled').checked = true;
            document.getElementById('notificationsEnabled').checked = true;
            document.getElementById('themeSelect').value = 'auto';
        }
    }

    applySettings() {
        // Apply language
        // Apply voice settings
        document.getElementById('voiceButton').style.display =
            this.settings.voiceEnabled ? 'flex' : 'none';

        // Apply theme
        this.applyTheme();
    }

    applyTheme() {
        const theme = this.settings.theme;

        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else if (theme === 'light') {
            document.body.classList.remove('dark-theme');
        } else {
            // Auto theme based on Telegram theme or system preference
            if (this.isTelegramWebApp) {
                const tgTheme = this.tg.colorScheme;
                if (tgTheme === 'dark') {
                    document.body.classList.add('dark-theme');
                } else {
                    document.body.classList.remove('dark-theme');
                }
            } else {
                // Use system preference for test mode
                if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.body.classList.add('dark-theme');
                } else {
                    document.body.classList.remove('dark-theme');
                }
            }
        }
    }

    async purchasePremium(plan) {
        try {
            const response = await this.apiCall('/payment/create-order', {
                plan_type: plan,
                amount: plan === 'monthly' ? 19900 : 199900 // in paisa
            });

            if (response.success) {
                // Open payment URL or handle payment
                this.showSuccess('पेमेंट प्रोसेस शुरू हो गया!');
                // In real implementation, integrate with Razorpay or Telegram Payments
            } else {
                throw new Error(response.message || 'Payment creation failed');
            }

        } catch (error) {
            console.error('Purchase premium error:', error);
            this.showError('पेमेंट प्रोसेस में गलती');
        }
    }

    async apiCall(endpoint, data = null) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        const url = `${process.env.BACKEND_URL || 'http://localhost:3000'}${endpoint}`;

        try {
            let response;

            if (data) {
                response = await fetch(url, {
                    method: 'POST',
                    ...config,
                    body: JSON.stringify(data)
                });
            } else {
                response = await fetch(url, config);
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'API call failed');
            }

            return result;

        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }

    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    showAuthScreen() {
        document.getElementById('auth').classList.remove('hidden');
        document.getElementById('app').classList.add('hidden');
    }

    showApp() {
        document.getElementById('auth').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

        // Update user info
        if (this.user) {
            document.getElementById('userName').textContent = this.user.name;
            document.getElementById('premiumBadge').classList.toggle('hidden', !this.user.is_premium);
        }

        // Apply settings
        this.applySettings();
    }

    showError(message) {
        // Simple error display - in production, use a proper toast system
        alert(`❌ ${message}`);
    }

    showSuccess(message) {
        // Simple success display
        alert(`✅ ${message}`);
    }

    // ===== NEW FEATURES: Socket.IO, Live Voice, Gesture Recognition =====

    /**
     * Initialize Socket.IO connection for real-time features
     */
    initializeSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('🔗 Connected to server');
            if (this.token) {
                this.socket.emit('authenticate', { token: this.token });
            }
        });

        this.socket.on('authenticated', (data) => {
            if (data.success) {
                console.log('🔐 Socket authenticated');
            } else {
                console.error('Socket authentication failed');
            }
        });

        this.socket.on('ai-response', (data) => {
            this.handleAIResponse(data);
        });

        this.socket.on('gesture-response', (data) => {
            this.handleGestureResponse(data);
        });

        this.socket.on('emotion-result', (data) => {
            this.handleEmotionResult(data);
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showError('Connection error');
        });
    }

    /**
     * Handle AI response from live voice or chat
     */
    handleAIResponse(data) {
        const { text, audio, language } = data;

        // Add AI message to chat
        this.addMessage(text, 'ai');

        // Play audio response if available
        if (audio && audio.type === 'web-speech-api') {
            this.speakText(text, language);
        }

        // Hide live voice status
        if (this.liveVoiceActive) {
            this.updateLiveVoiceStatus(false);
        }
    }

    /**
     * Handle gesture recognition response
     */
    handleGestureResponse(data) {
        const { gesture, response, confidence } = data;

        // Add gesture acknowledgment
        this.addMessage(`👋 ${gesture} (${Math.round(confidence * 100)}%): ${response}`, 'system');

        // Provide haptic feedback
        if (this.tg.HapticFeedback) {
            this.tg.HapticFeedback.impactOccurred('medium');
        }
    }

    /**
     * Toggle live voice chat mode
     */
    toggleLiveVoice() {
        if (this.liveVoiceActive) {
            this.stopLiveVoice();
        } else {
            this.startLiveVoice();
        }
    }

    /**
     * Start live voice chat
     */
    startLiveVoice() {
        if (!this.socket || !this.socket.connected) {
            this.showError('Connection not available');
            return;
        }

        this.liveVoiceActive = true;
        this.updateLiveVoiceStatus(true);

        // Start continuous voice recognition
        this.startContinuousVoiceRecognition();

        this.showSuccess('लाइव वॉइस चैट शुरू हो गया');
    }

    /**
     * Stop live voice chat
     */
    stopLiveVoice() {
        this.liveVoiceActive = false;
        this.updateLiveVoiceStatus(false);
        this.stopVoiceRecognition();
    }

    /**
     * Update live voice status UI
     */
    updateLiveVoiceStatus(active) {
        const statusEl = document.getElementById('liveVoiceStatus');
        const textEl = document.getElementById('voiceStatusText');

        if (active) {
            statusEl.classList.remove('hidden');
            textEl.textContent = 'सुन रहा हूं...';
        } else {
            statusEl.classList.add('hidden');
        }
    }

    /**
     * Start continuous voice recognition for live chat
     */
    startContinuousVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Voice recognition not supported');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        this.recognition.continuous = true;
        this.recognition.interimResults = false;
        this.recognition.lang = this.settings.language === 'hi' ? 'hi-IN' : 'en-US';

        this.recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript;
            if (transcript.trim()) {
                // Send to server via Socket.IO
                this.socket.emit('voice-message', {
                    audioData: transcript, // In production, send actual audio data
                    language: this.settings.language
                });

                // Update status
                document.getElementById('voiceStatusText').textContent = 'प्रोसेस हो रहा है...';
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.showError('Voice recognition error');
        };

        this.recognition.onend = () => {
            if (this.liveVoiceActive) {
                // Restart recognition for continuous mode
                setTimeout(() => {
                    if (this.liveVoiceActive) {
                        this.recognition.start();
                    }
                }, 100);
            }
        };

        this.recognition.start();
    }

    /**
     * Speak text using Web Speech API
     */
    speakText(text, language = 'hi') {
        if (!('speechSynthesis' in window)) {
            console.log('Speech synthesis not supported');
            return;
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language === 'hi' ? 'hi-IN' : 'en-US';
        utterance.rate = 0.9;
        utterance.pitch = 1;

        // Find appropriate voice
        const voices = speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice =>
            voice.lang.startsWith(language === 'hi' ? 'hi' : 'en')
        );

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        speechSynthesis.speak(utterance);
    }

    /**
     * Toggle gesture recognition
     */
    toggleGestureRecognition() {
        if (this.gestureActive) {
            this.stopGestureRecognition();
        } else {
            this.startGestureRecognition();
        }
    }

    /**
     * Toggle emotion detection
     */
    toggleEmotionDetection() {
        if (this.emotionDetectionActive) {
            this.stopEmotionDetection();
        } else {
            this.startEmotionDetection();
        }
    }

    /**
     * Start gesture recognition using camera
     */
    async startGestureRecognition() {
        try {
            // Request camera permission
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user' }
            });

            this.gestureActive = true;
            document.getElementById('gestureCamera').classList.remove('hidden');

            const video = document.getElementById('gestureVideo');
            video.srcObject = stream;
            this.camera = stream;

            // Initialize PoseNet
            this.poseNet = await posenet.load();

            // Start pose detection
            this.detectPoses();

            document.getElementById('gestureStatus').textContent = 'जेस्चर रिकग्निशन सक्रिय';

        } catch (error) {
            console.error('Gesture recognition error:', error);
            this.showError('Camera access denied or not available');
        }
    }

    /**
     * Stop gesture recognition
     */
    stopGestureRecognition() {
        this.gestureActive = false;

        if (this.camera) {
            this.camera.getTracks().forEach(track => track.stop());
            this.camera = null;
        }

        document.getElementById('gestureCamera').classList.add('hidden');
        document.getElementById('gestureStatus').textContent = 'जेस्चर रिकग्निशन बंद';
    }

    /**
     * Detect poses and gestures from camera feed
     */
    async detectPoses() {
        if (!this.gestureActive || !this.poseNet) return;

        const video = document.getElementById('gestureVideo');
        const canvas = document.getElementById('gestureCanvas');
        const ctx = canvas.getContext('2d');

        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        try {
            const pose = await this.poseNet.estimateSinglePose(video, {
                flipHorizontal: true
            });

            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw pose keypoints
            this.drawPose(pose, ctx);

            // Analyze gesture
            const gesture = this.analyzeGesture(pose);
            if (gesture && gesture.confidence > 0.7) {
                // Send gesture data to server
                this.socket.emit('gesture-data', {
                    gesture: gesture.type,
                    confidence: gesture.confidence,
                    poseData: pose
                });

                // Debounce gesture detection
                await new Promise(resolve => setTimeout(resolve, 2000));
            }

        } catch (error) {
            console.error('Pose detection error:', error);
        }

        // Continue detection
        if (this.gestureActive) {
            requestAnimationFrame(() => this.detectPoses());
        }
    }

    /**
     * Draw pose keypoints on canvas
     */
    drawPose(pose, ctx) {
        const keypoints = pose.keypoints;

        // Draw keypoints
        keypoints.forEach(keypoint => {
            if (keypoint.score > 0.5) {
                ctx.beginPath();
                ctx.arc(keypoint.position.x, keypoint.position.y, 5, 0, 2 * Math.PI);
                ctx.fillStyle = '#0088cc';
                ctx.fill();
            }
        });

        // Draw skeleton
        const adjacentKeypoints = posenet.getAdjacentKeyPoints(keypoints, 0.5);
        adjacentKeypoints.forEach(keypoints => {
            ctx.beginPath();
            ctx.moveTo(keypoints[0].position.x, keypoints[0].position.y);
            ctx.lineTo(keypoints[1].position.x, keypoints[1].position.y);
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.stroke();
        });
    }

    /**
     * Analyze pose to detect gestures
     */
    analyzeGesture(pose) {
        const keypoints = pose.keypoints;
        const nose = keypoints.find(k => k.part === 'nose');
        const leftWrist = keypoints.find(k => k.part === 'leftWrist');
        const rightWrist = keypoints.find(k => k.part === 'rightWrist');
        const leftEye = keypoints.find(k => k.part === 'leftEye');
        const rightEye = keypoints.find(k => k.part === 'rightEye');

        if (!nose || !leftWrist || !rightWrist) return null;

        // Wave gesture (hands above head)
        if (leftWrist.position.y < nose.position.y && rightWrist.position.y < nose.position.y) {
            return { type: 'wave', confidence: 0.8 };
        }

        // Thumbs up (one hand raised)
        if ((leftWrist.position.y < nose.position.y - 50) ||
            (rightWrist.position.y < nose.position.y - 50)) {
            return { type: 'thumbs_up', confidence: 0.7 };
        }

        // Pointing gesture
        if (Math.abs(leftWrist.position.x - rightWrist.position.x) > 100) {
            return { type: 'pointing', confidence: 0.6 };
        }

        // Nod (head movement - basic detection)
        if (leftEye && rightEye) {
            const eyeLevel = (leftEye.position.y + rightEye.position.y) / 2;
            if (Math.abs(eyeLevel - nose.position.y) < 20) {
                return { type: 'nod', confidence: 0.5 };
            }
        }

        return null;
    }

    /**
     * Setup gesture recognition (PoseNet initialization)
     */
    async setupGestureRecognition() {
        // PoseNet will be loaded when needed
        console.log('🤖 Gesture recognition ready');
    }

    /**
     * Setup emotion detection (BlazeFace initialization)
     */
    async setupEmotionDetection() {
        try {
            // Load TensorFlow.js and BlazeFace model
            if (typeof tf !== 'undefined' && typeof blazeface !== 'undefined') {
                await tf.ready();
                this.blazeFaceModel = await blazeface.load();
                console.log('😊 Emotion detection ready');
            } else {
                console.log('⚠️ TensorFlow.js or BlazeFace not available');
            }
        } catch (error) {
            console.error('Emotion detection setup failed:', error);
        }
    }

    /**
     * Start emotion detection
     */
    async startEmotionDetection() {
        if (!this.blazeFaceModel) {
            this.showError('Emotion detection not available');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 320, height: 240, facingMode: 'user' }
            });

            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;
            video.playsInline = true;

            await new Promise(resolve => {
                video.onloadedmetadata = resolve;
            });

            this.emotionDetectionActive = true;
            this.detectEmotions(video);

            // Show emotion indicator
            this.showEmotionIndicator();

        } catch (error) {
            console.error('Failed to start emotion detection:', error);
            this.showError('Camera access denied for emotion detection');
        }
    }

    /**
     * Stop emotion detection
     */
    stopEmotionDetection() {
        this.emotionDetectionActive = false;
        this.hideEmotionIndicator();
    }

    /**
     * Detect emotions from video stream
     */
    async detectEmotions(video) {
        if (!this.emotionDetectionActive) return;

        try {
            const predictions = await this.blazeFaceModel.estimateFaces(video, false);

            if (predictions.length > 0) {
                // Simulate emotion detection (in production, use actual ML model)
                const emotions = this.simulateEmotionDetection();

                // Update current emotions
                this.currentEmotions = emotions;

                // Send to server for analysis
                this.socket.emit('emotion-data', {
                    faceData: { landmarks: predictions[0] },
                    text: this.getLastMessage(),
                    language: this.settings.language
                });

                // Update UI
                this.updateEmotionIndicator(emotions);
            }
        } catch (error) {
            console.error('Emotion detection error:', error);
        }

        // Continue detection
        if (this.emotionDetectionActive) {
            requestAnimationFrame(() => this.detectEmotions(video));
        }
    }

    /**
     * Simulate emotion detection (replace with actual ML model)
     */
    simulateEmotionDetection() {
        return {
            happy: Math.random() * 0.8,
            sad: Math.random() * 0.6,
            angry: Math.random() * 0.4,
            neutral: Math.random() * 0.9,
            excited: Math.random() * 0.5,
            confused: Math.random() * 0.3
        };
    }

    /**
     * Get last message from chat
     */
    getLastMessage() {
        const messages = document.querySelectorAll('.message.user');
        if (messages.length > 0) {
            return messages[messages.length - 1].textContent;
        }
        return null;
    }

    /**
     * Show emotion indicator in UI
     */
    showEmotionIndicator() {
        let indicator = document.getElementById('emotionIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'emotionIndicator';
            indicator.className = 'emotion-indicator';
            indicator.innerHTML = `
                <div class="emotion-face">😐</div>
                <div class="emotion-text">Analyzing...</div>
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    /**
     * Hide emotion indicator
     */
    hideEmotionIndicator() {
        const indicator = document.getElementById('emotionIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Update emotion indicator with current emotions
     */
    updateEmotionIndicator(emotions) {
        const indicator = document.getElementById('emotionIndicator');
        if (!indicator) return;

        // Find dominant emotion
        const dominant = Object.entries(emotions).reduce((a, b) =>
            emotions[a[0]] > emotions[b[0]] ? a : b
        );

        const emotionFaces = {
            happy: '😊',
            sad: '😢',
            angry: '😠',
            neutral: '😐',
            excited: '🤩',
            confused: '😕'
        };

        const face = emotionFaces[dominant[0]] || '😐';
        const confidence = Math.round(dominant[1] * 100);

        indicator.innerHTML = `
            <div class="emotion-face">${face}</div>
            <div class="emotion-text">${dominant[0]} (${confidence}%)</div>
        `;
    }

    /**
     * Handle emotion analysis result from server
     */
    handleEmotionResult(data) {
        console.log('Emotion analysis result:', data);

        // Update emotion history
        this.emotionHistory.push({
            timestamp: new Date(),
            emotions: data.emotions,
            dominant: data.dominantEmotion
        });

        // Keep only last 10 entries
        if (this.emotionHistory.length > 10) {
            this.emotionHistory.shift();
        }

        // If emotion-aware response is available, show it
        if (data.response) {
            this.addMessage(data.response, 'ai', 'emotion');
        }
    }

    // ===== TRADING & NAVIGATION METHODS =====

    /**
     * Switch between screens
     */
    switchScreen(screenId) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.add('hidden');
        });

        // Show selected screen
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        const navItem = document.querySelector(`[data-screen="${screenId}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }

        this.currentScreen = screenId;

        // Load screen data
        switch (screenId) {
            case 'homeScreen':
                this.loadHomeData();
                break;
            case 'marketsScreen':
                this.loadMarketsData();
                break;
            case 'portfolioScreen':
                this.loadPortfolioData();
                break;
            case 'aiScreen':
                this.loadAIChat();
                break;
            case 'profileScreen':
                this.loadProfileData();
                break;
        }
    }

    /**
     * Load home screen data
     */
    loadHomeData() {
        // Update market indices
        document.getElementById('niftyValue').textContent = this.marketData.nifty.value.toLocaleString('en-IN');
        document.getElementById('niftyChange').textContent = `${this.marketData.nifty.change > 0 ? '+' : ''}${this.marketData.nifty.change.toFixed(2)} (${this.marketData.nifty.changePercent > 0 ? '+' : ''}${this.marketData.nifty.changePercent.toFixed(2)}%)`;
        document.getElementById('niftyChange').className = `index-change ${this.marketData.nifty.change >= 0 ? 'positive' : 'negative'}`;

        document.getElementById('sensexValue').textContent = this.marketData.sensex.value.toLocaleString('en-IN');
        document.getElementById('sensexChange').textContent = `${this.marketData.sensex.change > 0 ? '+' : ''}${this.marketData.sensex.change.toFixed(2)} (${this.marketData.sensex.changePercent > 0 ? '+' : ''}${this.marketData.sensex.changePercent.toFixed(2)}%)`;
        document.getElementById('sensexChange').className = `index-change ${this.marketData.sensex.change >= 0 ? 'positive' : 'negative'}`;

        // Load top movers (mock data)
        this.loadTopMovers();
    }

    /**
     * Load top gainers and losers
     */
    loadTopMovers() {
        const topGainers = [
            { symbol: 'RELIANCE', price: 2450.50, change: 45.25, changePercent: 1.88 },
            { symbol: 'TCS', price: 3250.75, change: 52.30, changePercent: 1.64 },
            { symbol: 'INFY', price: 1420.20, change: 28.45, changePercent: 2.05 },
            { symbol: 'HDFC', price: 1680.90, change: 31.80, changePercent: 1.93 }
        ];

        const topLosers = [
            { symbol: 'ITC', price: 425.30, change: -12.45, changePercent: -2.84 },
            { symbol: 'WIPRO', price: 380.15, change: -8.90, changePercent: -2.29 },
            { symbol: 'TECHM', price: 1180.40, change: -25.60, changePercent: -2.12 },
            { symbol: 'LT', price: 2150.80, change: -41.20, changePercent: -1.88 }
        ];

        const gainersContainer = document.getElementById('topGainers');
        const losersContainer = document.getElementById('topLosers');

        if (gainersContainer) {
            gainersContainer.innerHTML = topGainers.map(stock => `
                <div class="mover-item">
                    <div class="mover-symbol">${stock.symbol}</div>
                    <div class="mover-price">₹${stock.price.toFixed(2)}</div>
                    <div class="mover-change positive">+${stock.change.toFixed(2)} (+${stock.changePercent.toFixed(2)}%)</div>
                </div>
            `).join('');
        }

        if (losersContainer) {
            losersContainer.innerHTML = topLosers.map(stock => `
                <div class="mover-item">
                    <div class="mover-symbol">${stock.symbol}</div>
                    <div class="mover-price">₹${stock.price.toFixed(2)}</div>
                    <div class="mover-change negative">${stock.change.toFixed(2)} (${stock.changePercent.toFixed(2)}%)</div>
                </div>
            `).join('');
        }
    }

    /**
     * Trading actions
     */
    showBuyDialog() {
        this.showAlert('📈 खरीदारी फीचर जल्द ही आ रहा है!', 'info');
    }

    showSellDialog() {
        this.showAlert('📉 बिक्री फीचर जल्द ही आ रहा है!', 'info');
    }

    showNews() {
        this.showAlert('📰 समाचार फीचर जल्द ही आ रहा है!', 'info');
    }

    /**
     * Utility method for alerts
     */
    showAlert(message, type = 'info') {
        // Use Telegram's showPopup if available, otherwise browser alert
        if (this.tg.showPopup) {
            this.tg.showPopup({
                title: type === 'error' ? '❌ एरर' : type === 'success' ? '✅ सफल' : 'ℹ️ जानकारी',
                message: message,
                buttons: [{ type: 'ok' }]
            });
        } else {
            alert(message);
        }
    }

    /**
     * Load markets screen data
     */
    loadMarketsData() {
        const marketsContainer = document.getElementById('marketsList');
        if (!marketsContainer) return;

        const stocks = [
            { symbol: 'RELIANCE', name: 'Reliance Industries', price: 2450.50, change: 45.25, changePercent: 1.88, volume: '2.5M' },
            { symbol: 'TCS', name: 'Tata Consultancy Services', price: 3250.75, change: 52.30, changePercent: 1.64, volume: '1.8M' },
            { symbol: 'INFY', name: 'Infosys Ltd', price: 1420.20, change: 28.45, changePercent: 2.05, volume: '3.2M' },
            { symbol: 'HDFC', name: 'Housing Development Finance', price: 1680.90, change: 31.80, changePercent: 1.93, volume: '1.4M' },
            { symbol: 'ITC', name: 'ITC Ltd', price: 425.30, change: -12.45, changePercent: -2.84, volume: '4.1M' },
            { symbol: 'WIPRO', name: 'Wipro Ltd', price: 380.15, change: -8.90, changePercent: -2.29, volume: '2.9M' },
            { symbol: 'TECHM', name: 'Tech Mahindra', price: 1180.40, change: -25.60, changePercent: -2.12, volume: '1.6M' },
            { symbol: 'LT', name: 'Larsen & Toubro', price: 2150.80, change: -41.20, changePercent: -1.88, volume: '1.2M' }
        ];

        marketsContainer.innerHTML = stocks.map(stock => `
            <div class="market-item" onclick="window.jarvisApp.showStockDetails('${stock.symbol}')">
                <div class="market-info">
                    <div class="market-symbol">${stock.symbol}</div>
                    <div class="market-name">${stock.name}</div>
                </div>
                <div class="market-price">
                    <div class="price">₹${stock.price.toFixed(2)}</div>
                    <div class="change ${stock.change >= 0 ? 'positive' : 'negative'}">
                        ${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)} (${stock.changePercent > 0 ? '+' : ''}${stock.changePercent.toFixed(2)}%)
                    </div>
                </div>
                <div class="market-volume">Vol: ${stock.volume}</div>
            </div>
        `).join('');
    }

    /**
     * Show stock details
     */
    showStockDetails(symbol) {
        this.showAlert(`📊 ${symbol} का डिटेल्ड चार्ट जल्द ही आ रहा है!`, 'info');
    }

    /**
     * Load portfolio screen data
     */
    loadPortfolioData() {
        const holdings = [
            { symbol: 'RELIANCE', shares: 50, avgPrice: 2400.00, currentPrice: 2450.50, value: 122525.00, pnl: 2525.00, pnlPercent: 2.08 },
            { symbol: 'TCS', shares: 30, avgPrice: 3200.00, currentPrice: 3250.75, value: 97522.50, pnl: 1537.50, pnlPercent: 1.60 },
            { symbol: 'INFY', shares: 75, avgPrice: 1400.00, currentPrice: 1420.20, value: 106515.00, pnl: 1515.00, pnlPercent: 1.44 }
        ];

        const totalValue = holdings.reduce((sum, holding) => sum + holding.value, 0);
        const totalPnl = holdings.reduce((sum, holding) => sum + holding.pnl, 0);
        const totalPnlPercent = (totalPnl / (totalValue - totalPnl)) * 100;

        // Update summary
        document.getElementById('portfolioValue').textContent = `₹${totalValue.toLocaleString('en-IN')}`;
        document.getElementById('portfolioPnl').textContent = `${totalPnl > 0 ? '+' : ''}₹${totalPnl.toLocaleString('en-IN')} (${totalPnlPercent > 0 ? '+' : ''}${totalPnlPercent.toFixed(2)}%)`;
        document.getElementById('portfolioPnl').className = `pnl-value ${totalPnl >= 0 ? 'positive' : 'negative'}`;

        // Load holdings
        const holdingsContainer = document.getElementById('holdingsList');
        if (holdingsContainer) {
            holdingsContainer.innerHTML = holdings.map(holding => `
                <div class="holding-item">
                    <div class="holding-info">
                        <div class="holding-symbol">${holding.symbol}</div>
                        <div class="holding-shares">${holding.shares} shares</div>
                    </div>
                    <div class="holding-value">
                        <div class="value">₹${holding.value.toLocaleString('en-IN')}</div>
                        <div class="pnl ${holding.pnl >= 0 ? 'positive' : 'negative'}">
                            ${holding.pnl > 0 ? '+' : ''}₹${holding.pnl.toLocaleString('en-IN')} (${holding.pnlPercent > 0 ? '+' : ''}${holding.pnlPercent.toFixed(2)}%)
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    /**
     * Load AI chat screen
     */
    loadAIChat() {
        // Clear chat if needed
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages && chatMessages.children.length === 0) {
            this.addMessage('नमस्ते! मैं JARVIS हूं, आपका AI ट्रेडिंग असिस्टेंट। मैं मार्केट एनालिसिस, ट्रेडिंग स्ट्रेटेजी और पोर्टफोलियो मैनेजमेंट में आपकी मदद कर सकता हूं।', 'ai', 'greeting');
        }
    }

    /**
     * Load profile screen data
     */
    loadProfileData() {
        // Mock user data
        const userData = {
            name: 'ट्रेडर कुमार',
            email: 'trader@example.com',
            joinDate: '15 जनवरी 2024',
            totalTrades: 127,
            winRate: 68.5,
            totalPnl: 45250.75
        };

        document.getElementById('userName').textContent = userData.name;
        document.getElementById('userEmail').textContent = userData.email;
        document.getElementById('joinDate').textContent = userData.joinDate;
        document.getElementById('totalTrades').textContent = userData.totalTrades;
        document.getElementById('winRate').textContent = `${userData.winRate}%`;
        document.getElementById('totalPnl').textContent = `₹${userData.totalPnl.toLocaleString('en-IN')}`;
    }

    /**
     * Send AI message
     */
    sendAIMessage() {
        const input = document.getElementById('aiInput');
        const message = input.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        input.value = '';

        // Simulate AI response
        setTimeout(() => {
            const responses = [
                'बाजार में रिलायंस इंडस्ट्रीज में मजबूत अपट्रेंड दिख रहा है। क्या आप खरीदारी पर विचार कर रहे हैं?',
                'आपके पोर्टफोलियो में TCS का प्रदर्शन अच्छा है। क्या आप इसे होल्ड करना चाहते हैं या कुछ प्रॉफिट बुक करना चाहते हैं?',
                'मार्केट में वोलेटिलिटी बढ़ रही है। रिस्क मैनेजमेंट जरूरी है।',
                'आईटी सेक्टर में अच्छी ग्रोथ दिख रही है। INFY और TCS में निवेश पर विचार करें।',
                'आपके ट्रेडिंग पैटर्न के आधार पर, आप एक कंजर्वेटिव इन्वेस्टर हैं। क्या आप एग्रेसिव ट्रेडिंग ट्राय करना चाहेंगे?'
            ];
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            this.addMessage(randomResponse, 'ai', 'analysis');
        }, 1000);
    }

    /**
     * Handle AI input enter key
     */
    handleAIInputKeyPress(event) {
        if (event.key === 'Enter') {
            this.sendAIMessage();
        }
    }

    /**
     * Send AI message from quick questions
     */
    sendAIMessageFromQuick(message) {
        document.getElementById('aiInput').value = message;
        this.sendAIMessage();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisApp = new JarvisApp();
    window.app = window.jarvisApp; // Also assign to window.app for compatibility
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JarvisApp;
}