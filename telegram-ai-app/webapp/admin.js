// Admin Panel JavaScript
class AdminPanel {
    constructor() {
        this.socket = null;
        this.currentTab = 'dashboard';
        this.emotionDetectionActive = false;
        this.emotionHistory = [];
        this.emotionCounts = {
            happy: 0,
            sad: 0,
            angry: 0,
            neutral: 0
        };

        this.init();
    }

    init() {
        this.setupTelegramWebApp();
        this.setupSocketIO();
        this.setupEventListeners();
        this.loadDashboardData();
        this.initializeCharts();
    }

    setupTelegramWebApp() {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();

            // Check if user is admin
            const user = window.Telegram.WebApp.initDataUnsafe?.user;
            if (user && this.isAdmin(user.id)) {
                this.showAdminPanel(user);
            } else {
                this.showAuthScreen();
            }
        } else {
            // For development/testing without Telegram
            this.showAdminPanel({ first_name: 'Admin', last_name: 'User' });
        }
    }

    isAdmin(userId) {
        // In production, check against admin user IDs from backend
        const adminIds = [123456789, 987654321]; // Replace with actual admin IDs
        return adminIds.includes(userId);
    }

    setupSocketIO() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to admin socket');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from admin socket');
        });

        // Listen for real-time updates
        this.socket.on('user-stats-update', (data) => {
            this.updateStats(data);
        });

        this.socket.on('emotion-data', (data) => {
            this.updateEmotionData(data);
        });

        this.socket.on('admin-notification', (notification) => {
            this.showNotification(notification);
        });
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Auth button
        document.getElementById('authButton')?.addEventListener('click', () => {
            this.verifyAdminAccess();
        });

        // Emotion detection controls
        document.getElementById('startEmotionDetection')?.addEventListener('click', () => {
            this.startEmotionDetection();
        });

        document.getElementById('stopEmotionDetection')?.addEventListener('click', () => {
            this.stopEmotionDetection();
        });

        // Settings
        document.getElementById('saveSettings')?.addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('resetSettings')?.addEventListener('click', () => {
            this.resetSettings();
        });

        // User search and filter
        document.getElementById('userSearch')?.addEventListener('input', (e) => {
            this.filterUsers(e.target.value);
        });

        document.getElementById('userFilter')?.addEventListener('change', (e) => {
            this.filterUsersByType(e.target.value);
        });

        // Time range for analytics
        document.getElementById('timeRange')?.addEventListener('change', (e) => {
            this.updateAnalytics(e.target.value);
        });
    }

    showAuthScreen() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('auth').classList.remove('hidden');
    }

    showAdminPanel(user) {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('auth').classList.add('hidden');
        document.getElementById('admin').classList.remove('hidden');

        // Set admin name
        const adminName = document.getElementById('adminName');
        if (adminName) {
            adminName.textContent = `${user.first_name} ${user.last_name || ''}`;
        }
    }

    verifyAdminAccess() {
        // In production, verify with backend
        if (window.Telegram && window.Telegram.WebApp) {
            const user = window.Telegram.WebApp.initDataUnsafe?.user;
            if (user && this.isAdmin(user.id)) {
                this.showAdminPanel(user);
            } else {
                this.showNotification('Access denied. You are not authorized as an admin.', 'error');
            }
        } else {
            // For development
            this.showAdminPanel({ first_name: 'Dev', last_name: 'Admin' });
        }
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.classList.add('hidden');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
        document.getElementById(`${tabName}Tab`).classList.remove('hidden');

        this.currentTab = tabName;

        // Load tab-specific data
        switch (tabName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'users':
                this.loadUsersData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
            case 'emotions':
                this.initializeEmotionDetection();
                break;
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/admin/stats');
            const data = await response.json();

            this.updateStats(data);
            this.updateCharts(data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    updateStats(data) {
        document.getElementById('totalUsers').textContent = data.totalUsers || 0;
        document.getElementById('totalChats').textContent = data.totalChats || 0;
        document.getElementById('premiumUsers').textContent = data.premiumUsers || 0;
        document.getElementById('totalRevenue').textContent = `₹${data.totalRevenue || 0}`;

        // Update change indicators
        this.updateChangeIndicator('usersChange', data.usersChange);
        this.updateChangeIndicator('chatsChange', data.chatsChange);
        this.updateChangeIndicator('premiumChange', data.premiumChange);
        this.updateChangeIndicator('revenueChange', data.revenueChange);
    }

    updateChangeIndicator(elementId, change) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const changeValue = change || 0;
        element.textContent = `${changeValue >= 0 ? '+' : ''}${changeValue}%`;

        element.classList.remove('positive', 'negative');
        if (changeValue > 0) {
            element.classList.add('positive');
        } else if (changeValue < 0) {
            element.classList.add('negative');
        }
    }

    initializeCharts() {
        // Activity Chart
        const activityCtx = document.getElementById('activityChart');
        if (activityCtx) {
            this.activityChart = new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Active Users',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Emotion Chart
        const emotionCtx = document.getElementById('emotionChart');
        if (emotionCtx) {
            this.emotionChart = new Chart(emotionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Happy', 'Sad', 'Angry', 'Neutral'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#ffd700', '#4a90e2', '#ff6b6b', '#a8a8a8']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Emotion History Chart
        const historyCtx = document.getElementById('emotionHistoryChart');
        if (historyCtx) {
            this.emotionHistoryChart = new Chart(historyCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Happy',
                        data: [],
                        borderColor: '#ffd700',
                        backgroundColor: 'rgba(255, 215, 0, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Sad',
                        data: [],
                        borderColor: '#4a90e2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Angry',
                        data: [],
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Neutral',
                        data: [],
                        borderColor: '#a8a8a8',
                        backgroundColor: 'rgba(168, 168, 168, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    }

    updateCharts(data) {
        if (this.activityChart && data.activityData) {
            this.activityChart.data.labels = data.activityData.labels;
            this.activityChart.data.datasets[0].data = data.activityData.values;
            this.activityChart.update();
        }

        if (this.emotionChart && data.emotionData) {
            this.emotionChart.data.datasets[0].data = data.emotionData;
            this.emotionChart.update();
        }
    }

    async loadUsersData() {
        try {
            const response = await fetch('/api/admin/users');
            const users = await response.json();

            this.displayUsers(users);
        } catch (error) {
            console.error('Failed to load users data:', error);
        }
    }

    displayUsers(users) {
        const usersList = document.getElementById('usersList');
        if (!usersList) return;

        usersList.innerHTML = '';

        users.forEach(user => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item';

            userItem.innerHTML = `
                <div class="user-info">
                    <h4>${user.name || 'Unknown User'}</h4>
                    <p>ID: ${user.telegramId} • Joined: ${new Date(user.createdAt).toLocaleDateString()}</p>
                </div>
                <div class="user-status">
                    <span class="status-badge ${user.isPremium ? 'premium' : 'free'}">
                        ${user.isPremium ? '⭐ Premium' : 'Free'}
                    </span>
                </div>
            `;

            usersList.appendChild(userItem);
        });
    }

    filterUsers(searchTerm) {
        const users = document.querySelectorAll('.user-item');
        users.forEach(user => {
            const name = user.querySelector('h4').textContent.toLowerCase();
            const visible = name.includes(searchTerm.toLowerCase());
            user.style.display = visible ? 'flex' : 'none';
        });
    }

    filterUsersByType(filterType) {
        const users = document.querySelectorAll('.user-item');
        users.forEach(user => {
            const isPremium = user.querySelector('.status-badge').classList.contains('premium');
            let visible = true;

            switch (filterType) {
                case 'premium':
                    visible = isPremium;
                    break;
                case 'free':
                    visible = !isPremium;
                    break;
                case 'all':
                default:
                    visible = true;
                    break;
            }

            user.style.display = visible ? 'flex' : 'none';
        });
    }

    async loadAnalyticsData() {
        // Load analytics data based on time range
        const timeRange = document.getElementById('timeRange').value;
        this.updateAnalytics(timeRange);
    }

    async updateAnalytics(timeRange) {
        try {
            const response = await fetch(`/api/admin/analytics?range=${timeRange}`);
            const data = await response.json();

            // Update usage and revenue charts
            this.updateUsageChart(data.usageData);
            this.updateRevenueChart(data.revenueData);
        } catch (error) {
            console.error('Failed to load analytics data:', error);
        }
    }

    updateUsageChart(data) {
        // Implementation for usage chart update
        console.log('Updating usage chart:', data);
    }

    updateRevenueChart(data) {
        // Implementation for revenue chart update
        console.log('Updating revenue chart:', data);
    }

    async initializeEmotionDetection() {
        try {
            // Load TensorFlow.js and BlazeFace model
            await tf.ready();
            this.blazeFaceModel = await blazeface.load();

            // Initialize emotion detection
            this.setupEmotionDetection();
        } catch (error) {
            console.error('Failed to initialize emotion detection:', error);
            this.showNotification('Failed to initialize emotion detection. Please check camera permissions.', 'error');
        }
    }

    setupEmotionDetection() {
        this.video = document.getElementById('emotionVideo');
        this.canvas = document.getElementById('emotionCanvas');
        this.status = document.getElementById('emotionStatus');

        if (!this.video || !this.canvas) return;

        this.canvas.width = 640;
        this.canvas.height = 480;
        this.ctx = this.canvas.getContext('2d');
    }

    async startEmotionDetection() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });

            this.video.srcObject = stream;
            this.emotionDetectionActive = true;

            this.status.textContent = '🎥 Detecting emotions...';
            document.getElementById('startEmotionDetection').disabled = true;
            document.getElementById('stopEmotionDetection').disabled = false;

            this.detectEmotions();
        } catch (error) {
            console.error('Failed to start emotion detection:', error);
            this.showNotification('Failed to access camera. Please check permissions.', 'error');
        }
    }

    stopEmotionDetection() {
        if (this.video.srcObject) {
            const stream = this.video.srcObject;
            stream.getTracks().forEach(track => track.stop());
            this.video.srcObject = null;
        }

        this.emotionDetectionActive = false;
        this.status.textContent = 'Camera stopped';
        document.getElementById('startEmotionDetection').disabled = false;
        document.getElementById('stopEmotionDetection').disabled = true;

        // Clear canvas
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    async detectEmotions() {
        if (!this.emotionDetectionActive) return;

        try {
            // Detect faces
            const predictions = await this.blazeFaceModel.estimateFaces(this.video, false);

            // Clear canvas
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            if (predictions.length > 0) {
                // Draw face bounding box
                const face = predictions[0];
                const [x, y, width, height] = face.topLeft.concat(face.bottomRight);

                this.ctx.strokeStyle = '#00ff00';
                this.ctx.lineWidth = 3;
                this.ctx.strokeRect(x, y, width - x, height - y);

                // Simulate emotion detection (in production, use actual ML model)
                const emotions = this.simulateEmotionDetection();

                // Update emotion bars
                this.updateEmotionBars(emotions);

                // Update emotion counts
                this.updateEmotionCounts(emotions);

                // Add to history
                this.addToEmotionHistory(emotions);

                // Send to backend
                this.socket.emit('emotion-update', {
                    emotions,
                    timestamp: Date.now(),
                    faceDetected: true
                });
            } else {
                this.status.textContent = 'No face detected';
            }
        } catch (error) {
            console.error('Emotion detection error:', error);
        }

        // Continue detection
        if (this.emotionDetectionActive) {
            requestAnimationFrame(() => this.detectEmotions());
        }
    }

    simulateEmotionDetection() {
        // Simulate emotion detection with realistic probabilities
        // In production, replace with actual ML model inference
        const emotions = {
            happy: Math.random() * 0.8,
            sad: Math.random() * 0.6,
            angry: Math.random() * 0.4,
            neutral: Math.random() * 0.9
        };

        // Normalize to ensure they sum to 1
        const total = emotions.happy + emotions.sad + emotions.angry + emotions.neutral;
        Object.keys(emotions).forEach(key => {
            emotions[key] = emotions[key] / total;
        });

        return emotions;
    }

    updateEmotionBars(emotions) {
        const emotionBars = document.getElementById('emotionBars');
        if (!emotionBars) return;

        emotionBars.innerHTML = '';

        Object.entries(emotions).forEach(([emotion, probability]) => {
            const percentage = Math.round(probability * 100);

            const barElement = document.createElement('div');
            barElement.className = 'emotion-bar';

            barElement.innerHTML = `
                <span class="emotion-label">${emotion.charAt(0).toUpperCase() + emotion.slice(1)}</span>
                <div class="emotion-progress">
                    <div class="emotion-fill ${emotion}" style="width: ${percentage}%"></div>
                </div>
                <span class="emotion-value">${percentage}%</span>
            `;

            emotionBars.appendChild(barElement);
        });
    }

    updateEmotionCounts(emotions) {
        // Find dominant emotion
        const dominantEmotion = Object.entries(emotions).reduce((a, b) =>
            emotions[a[0]] > emotions[b[0]] ? a : b
        )[0];

        this.emotionCounts[dominantEmotion]++;

        // Update display
        document.getElementById('happyCount').textContent = this.emotionCounts.happy;
        document.getElementById('sadCount').textContent = this.emotionCounts.sad;
        document.getElementById('angryCount').textContent = this.emotionCounts.angry;
        document.getElementById('neutralCount').textContent = this.emotionCounts.neutral;
    }

    addToEmotionHistory(emotions) {
        const timestamp = new Date().toLocaleTimeString();

        this.emotionHistory.push({
            time: timestamp,
            ...emotions
        });

        // Keep only last 20 entries
        if (this.emotionHistory.length > 20) {
            this.emotionHistory.shift();
        }

        // Update chart
        if (this.emotionHistoryChart) {
            this.emotionHistoryChart.data.labels = this.emotionHistory.map(h => h.time);
            this.emotionHistoryChart.data.datasets[0].data = this.emotionHistory.map(h => h.happy * 100);
            this.emotionHistoryChart.data.datasets[1].data = this.emotionHistory.map(h => h.sad * 100);
            this.emotionHistoryChart.data.datasets[2].data = this.emotionHistory.map(h => h.angry * 100);
            this.emotionHistoryChart.data.datasets[3].data = this.emotionHistory.map(h => h.neutral * 100);
            this.emotionHistoryChart.update();
        }
    }

    updateEmotionData(data) {
        // Update emotion chart on dashboard
        if (this.emotionChart && data.distribution) {
            this.emotionChart.data.datasets[0].data = data.distribution;
            this.emotionChart.update();
        }
    }

    async saveSettings() {
        const settings = {
            aiProvider: document.getElementById('aiProvider').value,
            emotionEnabled: document.getElementById('emotionEnabled').checked,
            rateLimit: parseInt(document.getElementById('rateLimit').value)
        };

        try {
            const response = await fetch('/api/admin/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showNotification('Settings saved successfully!', 'success');
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showNotification('Failed to save settings. Please try again.', 'error');
        }
    }

    async resetSettings() {
        if (confirm('Are you sure you want to reset all settings to default?')) {
            try {
                const response = await fetch('/api/admin/settings/reset', {
                    method: 'POST'
                });

                if (response.ok) {
                    this.showNotification('Settings reset to default!', 'success');
                    // Reload settings
                    setTimeout(() => location.reload(), 1000);
                } else {
                    throw new Error('Failed to reset settings');
                }
            } catch (error) {
                console.error('Failed to reset settings:', error);
                this.showNotification('Failed to reset settings. Please try again.', 'error');
            }
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification implementation
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#4caf50' : '#667eea'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Add notification animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});