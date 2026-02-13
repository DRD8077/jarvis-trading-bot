// Telegram Web App Integration
// Handles Telegram-specific features and SDK integration

class TelegramIntegration {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.initData = null;
        this.user = null;
        this.isExpanded = false;

        this.init();
    }

    init() {
        try {
            // Initialize Web App
            this.tg.ready();

            // Get init data
            this.initData = this.tg.initData;
            this.user = this.tg.initDataUnsafe?.user;

            // Set up event listeners
            this.setupEventListeners();

            // Configure Web App
            this.configureWebApp();

            console.log('Telegram Web App initialized');

        } catch (error) {
            console.error('Telegram Web App initialization error:', error);
        }
    }

    setupEventListeners() {
        // Theme changes
        this.tg.onEvent('themeChanged', () => {
            this.handleThemeChange();
        });

        // Viewport changes
        this.tg.onEvent('viewportChanged', () => {
            this.handleViewportChange();
        });

        // Safe area changes (for devices with notches)
        this.tg.onEvent('safeAreaChanged', () => {
            this.handleSafeAreaChange();
        });

        // Main button events (if used)
        this.tg.MainButton.onClick(() => {
            this.handleMainButtonClick();
        });

        // Back button events (if used)
        this.tg.BackButton.onClick(() => {
            this.handleBackButtonClick();
        });

        // Settings button events (if used)
        this.tg.SettingsButton.onClick(() => {
            this.handleSettingsButtonClick();
        });
    }

    configureWebApp() {
        // Expand to full height
        this.expand();

        // Set header color
        this.setHeaderColor('#0088cc');

        // Set background color
        this.setBackgroundColor('#ffffff');

        // Enable haptic feedback
        this.enableHapticFeedback();

        // Set viewport meta tag
        this.setViewport();

        // Handle orientation
        this.handleOrientation();
    }

    expand() {
        try {
            this.tg.expand();
            this.isExpanded = true;
        } catch (error) {
            console.error('Failed to expand Web App:', error);
        }
    }

    close() {
        try {
            this.tg.close();
        } catch (error) {
            console.error('Failed to close Web App:', error);
        }
    }

    setHeaderColor(color) {
        try {
            this.tg.setHeaderColor(color);
        } catch (error) {
            console.error('Failed to set header color:', error);
        }
    }

    setBackgroundColor(color) {
        try {
            this.tg.setBackgroundColor(color);
        } catch (error) {
            console.error('Failed to set background color:', error);
        }
    }

    enableHapticFeedback() {
        // Haptic feedback is enabled by default in modern Telegram clients
        // This method ensures it's available
        if (this.tg.HapticFeedback) {
            console.log('Haptic feedback enabled');
        }
    }

    setViewport() {
        // Ensure proper viewport settings
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content',
                'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover'
            );
        }
    }

    handleThemeChange() {
        const theme = this.tg.colorScheme;
        console.log('Theme changed to:', theme);

        // Update CSS custom properties based on theme
        this.updateThemeColors();

        // Notify app of theme change
        if (window.jarvisApp) {
            window.jarvisApp.applyTheme();
        }
    }

    handleViewportChange() {
        const viewportHeight = this.tg.viewportHeight;
        const viewportStableHeight = this.tg.viewportStableHeight;

        console.log('Viewport changed:', { viewportHeight, viewportStableHeight });

        // Adjust layout if needed
        this.adjustLayoutForViewport();
    }

    handleSafeAreaChange() {
        const safeAreaInset = this.tg.safeAreaInset;
        console.log('Safe area changed:', safeAreaInset);

        // Apply safe area insets for devices with notches
        this.applySafeAreaInsets(safeAreaInset);
    }

    handleMainButtonClick() {
        console.log('Main button clicked');
        // Handle main button action
    }

    handleBackButtonClick() {
        console.log('Back button clicked');
        // Handle back navigation
        if (window.jarvisApp) {
            window.jarvisApp.goBack();
        }
    }

    handleSettingsButtonClick() {
        console.log('Settings button clicked');
        // Open settings screen
        if (window.jarvisApp) {
            window.jarvisApp.switchScreen('settings');
        }
    }

    updateThemeColors() {
        const root = document.documentElement;

        if (this.tg.colorScheme === 'dark') {
            // Apply dark theme colors
            root.style.setProperty('--tg-theme-bg-color', this.tg.themeParams.bg_color || '#1c1c1d');
            root.style.setProperty('--tg-theme-text-color', this.tg.themeParams.text_color || '#ffffff');
            root.style.setProperty('--tg-theme-hint-color', this.tg.themeParams.hint_color || '#b1c3d5');
            root.style.setProperty('--tg-theme-link-color', this.tg.themeParams.link_color || '#5eabe1');
            root.style.setProperty('--tg-theme-button-color', this.tg.themeParams.button_color || '#2ea6ff');
            root.style.setProperty('--tg-theme-button-text-color', this.tg.themeParams.button_text_color || '#ffffff');
        } else {
            // Apply light theme colors
            root.style.setProperty('--tg-theme-bg-color', this.tg.themeParams.bg_color || '#ffffff');
            root.style.setProperty('--tg-theme-text-color', this.tg.themeParams.text_color || '#000000');
            root.style.setProperty('--tg-theme-hint-color', this.tg.themeParams.hint_color || '#999999');
            root.style.setProperty('--tg-theme-link-color', this.tg.themeParams.link_color || '#168acd');
            root.style.setProperty('--tg-theme-button-color', this.tg.themeParams.button_color || '#40a7e3');
            root.style.setProperty('--tg-theme-button-text-color', this.tg.themeParams.button_text_color || '#ffffff');
        }
    }

    adjustLayoutForViewport() {
        const vh = this.tg.viewportHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);

        // Adjust app height
        const app = document.querySelector('.app');
        if (app) {
            app.style.height = `${this.tg.viewportHeight}px`;
        }
    }

    applySafeAreaInsets(insets) {
        const root = document.documentElement;

        root.style.setProperty('--safe-area-inset-top', `${insets.top || 0}px`);
        root.style.setProperty('--safe-area-inset-bottom', `${insets.bottom || 0}px`);
        root.style.setProperty('--safe-area-inset-left', `${insets.left || 0}px`);
        root.style.setProperty('--safe-area-inset-right', `${insets.right || 0}px`);

        // Apply to body padding
        document.body.style.paddingTop = `var(--safe-area-inset-top)`;
        document.body.style.paddingBottom = `var(--safe-area-inset-bottom)`;
        document.body.style.paddingLeft = `var(--safe-area-inset-left)`;
        document.body.style.paddingRight = `var(--safe-area-inset-right)`;
    }

    handleOrientation() {
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.adjustLayoutForViewport();
            }, 100);
        });
    }

    // Utility methods for app integration
    showMainButton(text, isVisible = true) {
        try {
            this.tg.MainButton.text = text;
            if (isVisible) {
                this.tg.MainButton.show();
            } else {
                this.tg.MainButton.hide();
            }
        } catch (error) {
            console.error('Failed to control main button:', error);
        }
    }

    showBackButton(isVisible = true) {
        try {
            if (isVisible) {
                this.tg.BackButton.show();
            } else {
                this.tg.BackButton.hide();
            }
        } catch (error) {
            console.error('Failed to control back button:', error);
        }
    }

    showSettingsButton(isVisible = true) {
        try {
            if (isVisible) {
                this.tg.SettingsButton.show();
            } else {
                this.tg.SettingsButton.hide();
            }
        } catch (error) {
            console.error('Failed to control settings button:', error);
        }
    }

    sendData(data) {
        try {
            this.tg.sendData(JSON.stringify(data));
        } catch (error) {
            console.error('Failed to send data to bot:', error);
        }
    }

    showPopup(title, message, buttons = []) {
        try {
            this.tg.showPopup({
                title: title,
                message: message,
                buttons: buttons
            });
        } catch (error) {
            console.error('Failed to show popup:', error);
            // Fallback to alert
            alert(`${title}\n\n${message}`);
        }
    }

    showAlert(message) {
        this.showPopup('Alert', message, [{ text: 'OK' }]);
    }

    showConfirm(message, callback) {
        this.showPopup('Confirm', message, [
            { text: 'Cancel', type: 'cancel' },
            { text: 'OK', type: 'ok' }
        ]);

        // Handle callback when implemented
        if (callback) {
            // This would need to be handled via events
            console.log('Confirm callback:', callback);
        }
    }

    // Haptic feedback methods
    impactOccurred(style = 'medium') {
        try {
            this.tg.HapticFeedback.impactOccurred(style);
        } catch (error) {
            console.error('Haptic feedback not supported');
        }
    }

    notificationOccurred(type = 'success') {
        try {
            this.tg.HapticFeedback.notificationOccurred(type);
        } catch (error) {
            console.error('Haptic feedback not supported');
        }
    }

    // Getters for app information
    getUser() {
        return this.user;
    }

    getInitData() {
        return this.initData;
    }

    isVersionAtLeast(version) {
        return this.tg.isVersionAtLeast(version);
    }

    // Check platform
    getPlatform() {
        return this.tg.platform;
    }

    isAndroid() {
        return this.getPlatform() === 'android';
    }

    isIOS() {
        return this.getPlatform() === 'ios';
    }

    isDesktop() {
        return !this.isAndroid() && !this.isIOS();
    }
}

// Initialize Telegram integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.telegramIntegration = new TelegramIntegration();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TelegramIntegration;
}