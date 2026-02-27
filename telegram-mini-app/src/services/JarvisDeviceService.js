/**
 * 📱 JARVIS Mobile Device Control Service
 * ═══════════════════════════════════════════
 * Provides native device control for Android via Capacitor plugins.
 * Import this in your React app to give JARVIS full phone control.
 */

// Capacitor plugin imports — these work when running inside Capacitor
let Plugins = {};

try {
  if (typeof window !== 'undefined' && window.Capacitor?.Plugins) {
    Plugins = window.Capacitor.Plugins;
  }
} catch (e) {
  // Running in browser, plugins not available
}

class JarvisDeviceService {
  constructor() {
    try {
        this.isNative = typeof window !== 'undefined' && window.Capacitor?.isNativePlatform();
      this.platform = this.isNative ? window.Capacitor.getPlatform() : 'web';
  
    } catch(e) {
      console.warn('[JarvisDeviceService] Constructor init error:', e)
    }
}

  // ═══════════════════════════════════
  // DEVICE INFO
  // ═══════════════════════════════════

  async getDeviceInfo() {
    try {
      const { Device } = await import('@capacitor/device');
      const info = await Device.getInfo();
      const battery = await Device.getBatteryInfo();
      return { ...info, battery, platform: this.platform };
    } catch (e) {
      return { platform: this.platform, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // CAMERA
  // ═══════════════════════════════════

  async takePhoto() {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
      const image = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera,
      });
      return { success: true, image: image.dataUrl, format: image.format };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async pickPhoto() {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
      const image = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Photos,
      });
      return { success: true, image: image.dataUrl };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // FILESYSTEM
  // ═══════════════════════════════════

  async listFiles(directory = 'DOCUMENTS') {
    try {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      const result = await Filesystem.readdir({
        path: '',
        directory: Directory[directory] || Directory.Documents,
      });
      return { success: true, files: result.files };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async readFile(path, directory = 'DOCUMENTS') {
    try {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      const result = await Filesystem.readFile({
        path,
        directory: Directory[directory] || Directory.Documents,
      });
      return { success: true, data: result.data };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async writeFile(path, data, directory = 'DOCUMENTS') {
    try {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      await Filesystem.writeFile({
        path,
        data,
        directory: Directory[directory] || Directory.Documents,
      });
      return { success: true, path };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async deleteFile(path, directory = 'DOCUMENTS') {
    try {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      await Filesystem.deleteFile({
        path,
        directory: Directory[directory] || Directory.Documents,
      });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // CLIPBOARD
  // ═══════════════════════════════════

  async getClipboard() {
    try {
      const { Clipboard } = await import('@capacitor/clipboard');
      const result = await Clipboard.read();
      return { success: true, text: result.value, type: result.type };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async setClipboard(text) {
    try {
      const { Clipboard } = await import('@capacitor/clipboard');
      await Clipboard.write({ string: text });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // LOCATION
  // ═══════════════════════════════════

  async getLocation() {
    try {
      const { Geolocation } = await import('@capacitor/geolocation');
      const position = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
      return {
        success: true,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        speed: position.coords.speed,
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // NOTIFICATIONS
  // ═══════════════════════════════════

  async sendNotification(title, body, id = null) {
    try {
      const { LocalNotifications } = await import('@capacitor/local-notifications');
      await LocalNotifications.schedule({
        notifications: [{
          title,
          body,
          id: id || Math.floor(Math.random() * 100000),
          schedule: { at: new Date(Date.now() + 1000) },
          sound: null,
          smallIcon: 'ic_stat_icon_config_sample',
        }],
      });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // HAPTICS
  // ═══════════════════════════════════

  async vibrate(style = 'Medium') {
    try {
      const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
      await Haptics.impact({ style: ImpactStyle[style] || ImpactStyle.Medium });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // NETWORK
  // ═══════════════════════════════════

  async getNetworkStatus() {
    try {
      const { Network } = await import('@capacitor/network');
      const status = await Network.getStatus();
      return { success: true, ...status };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // SHARE
  // ═══════════════════════════════════

  async share(title, text, url) {
    try {
      const { Share } = await import('@capacitor/share');
      await Share.share({ title, text, url, dialogTitle: 'Share via JARVIS' });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // BROWSER
  // ═══════════════════════════════════

  async openUrl(url) {
    try {
      const { Browser } = await import('@capacitor/browser');
      await Browser.open({ url });
      return { success: true };
    } catch (e) {
      // Fallback
      window.open(url, '_blank');
      return { success: true, fallback: true };
    }
  }

  // ═══════════════════════════════════
  // APP CONTROL
  // ═══════════════════════════════════

  async openApp(packageName) {
    try {
      // Use Android Intent to open apps
      if (this.isNative && this.platform === 'android') {
        const { App } = await import('@capacitor/app');
        // Custom plugin or intent URL
        window.location.href = `intent://#Intent;package=${packageName};end`;
        return { success: true, app: packageName };
      }
      return { success: false, error: 'Not available on this platform' };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // Common app shortcuts
  async openWhatsApp(phone = '', message = '') {
    const url = phone
      ? `https://api.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(message)}`
      : 'https://api.whatsapp.com';
    return this.openUrl(url);
  }

  async openYouTube(query = '') {
    const url = query
      ? `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
      : 'https://www.youtube.com';
    return this.openUrl(url);
  }

  async openMaps(query) {
    return this.openUrl(`https://www.google.com/maps/search/${encodeURIComponent(query)}`);
  }

  async makeCall(phone) {
    return this.openUrl(`tel:${phone}`);
  }

  async sendSMS(phone, message = '') {
    return this.openUrl(`sms:${phone}${message ? `?body=${encodeURIComponent(message)}` : ''}`);
  }

  async sendEmail(to, subject = '', body = '') {
    return this.openUrl(`mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
  }

  // ═══════════════════════════════════
  // VOICE (TTS)
  // ═══════════════════════════════════

  async speak(text, lang = 'en-IN') {
    // v32: Respect mute/voice settings — NEVER bypass
    if (window.__JARVIS_MUTE || window.__JARVIS_VOICE_ENABLED === false) {
      return { success: false, error: 'Voice muted by user' };
    }
    // Route through central voice companion instead of direct speechSynthesis
    window.dispatchEvent(new CustomEvent('jarvis-speak', {
      detail: { text, priority: 'normal' }
    }));
    return { success: true };
  }

  async listen(lang = 'en-IN') {
    return new Promise((resolve) => {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        resolve({ success: false, error: 'STT not available' });
        return;
      }
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = lang;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        resolve({ success: true, text: event.results[0][0].transcript, confidence: event.results[0][0].confidence });
      };
      recognition.onerror = (event) => {
        resolve({ success: false, error: event.error });
      };
      recognition.start();
    });
  }

  // ═══════════════════════════════════
  // STATUS BAR (Android)
  // ═══════════════════════════════════

  async setStatusBarColor(color = '#0a0e1a') {
    try {
      const { StatusBar, Style } = await import('@capacitor/status-bar');
      await StatusBar.setBackgroundColor({ color });
      await StatusBar.setStyle({ style: Style.Dark });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async hideStatusBar() {
    try {
      const { StatusBar } = await import('@capacitor/status-bar');
      await StatusBar.hide();
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // PREFERENCES (Local Storage)
  // ═══════════════════════════════════

  async saveData(key, value) {
    try {
      const { Preferences } = await import('@capacitor/preferences');
      await Preferences.set({ key, value: JSON.stringify(value) });
      return { success: true };
    } catch (e) {
      localStorage.setItem(key, JSON.stringify(value));
      return { success: true, fallback: true };
    }
  }

  async loadData(key) {
    try {
      const { Preferences } = await import('@capacitor/preferences');
      const result = await Preferences.get({ key });
      return { success: true, data: result.value ? JSON.parse(result.value) : null };
    } catch (e) {
      const val = localStorage.getItem(key);
      return { success: true, data: val ? JSON.parse(val) : null, fallback: true };
    }
  }

  // ═══════════════════════════════════
  // TOAST
  // ═══════════════════════════════════

  async showToast(text, duration = 'short', position = 'bottom') {
    try {
      const { Toast } = await import('@capacitor/toast');
      await Toast.show({ text, duration, position });
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // ═══════════════════════════════════
  // DIALOG
  // ═══════════════════════════════════

  async showAlert(title, message) {
    try {
      const { Dialog } = await import('@capacitor/dialog');
      await Dialog.alert({ title, message });
      return { success: true };
    } catch (e) {
      alert(`${title}\n${message}`);
      return { success: true, fallback: true };
    }
  }

  async showConfirm(title, message) {
    try {
      const { Dialog } = await import('@capacitor/dialog');
      const result = await Dialog.confirm({ title, message });
      return { success: true, confirmed: result.value };
    } catch (e) {
      return { success: true, confirmed: confirm(`${title}\n${message}`), fallback: true };
    }
  }

  async showPrompt(title, message) {
    try {
      const { Dialog } = await import('@capacitor/dialog');
      const result = await Dialog.prompt({ title, message });
      return { success: true, value: result.value, cancelled: result.cancelled };
    } catch (e) {
      const val = prompt(`${title}\n${message}`);
      return { success: true, value: val, cancelled: val === null, fallback: true };
    }
  }

  // ═══════════════════════════════════
  // 🎮 GAMING CONTROL
  // ═══════════════════════════════════

  /**
   * Start gaming coaching session with screen capture
   */
  async startGamingSession(profile = 'jonathan_gaming') {
    try {
      const { default: jarvisGameVision } = await import('./jarvisGameVision');
      jarvisGameVision.gamingProfile = profile;
      const result = await jarvisGameVision.startScreenCapture();
      return { success: result.success, ...result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  /**
   * Stop gaming coaching session
   */
  async stopGamingSession() {
    try {
      const { default: jarvisGameVision } = await import('./jarvisGameVision');
      const result = jarvisGameVision.stopScreenCapture();
      return { success: true, ...result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  /**
   * Analyze a game screenshot manually
   * @param {File|string} imageOrDataUrl - File or base64 data URL
   */
  async analyzeGameScreenshot(imageOrDataUrl) {
    try {
      const { default: jarvisGameVision } = await import('./jarvisGameVision');
      const result = await jarvisGameVision.analyzeScreenshot(imageOrDataUrl);
      return { success: true, analysis: result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  /**
   * Switch pro player gaming profile
   * @param {string} profile - e.g., 'jonathan_gaming', 'mortal', 'scout'
   */
  async switchGamingProfile(profile) {
    try {
      const { default: jarvisGameVision } = await import('./jarvisGameVision');
      const result = await jarvisGameVision.setProfile(profile);
      return { success: true, ...result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  /**
   * Get current gaming state (enemies, health, zone, etc.)
   */
  getGamingState() {
    try {
      const jarvisGameVision = require('./jarvisGameVision').default;
      return {
        success: true,
        isActive: jarvisGameVision.isScreenSharing(),
        state: jarvisGameVision.getGameState(),
        frameCount: jarvisGameVision.getFrameCount(),
        calloutHistory: jarvisGameVision.getCalloutHistory().slice(-10),
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  /**
   * Launch BGMI / PUBG Mobile
   */
  async launchBGMI() {
    return await this.openApp('com.pubg.imobile');
  }

  /**
   * Launch PUBG Mobile (global)
   */
  async launchPUBG() {
    return await this.openApp('com.tencent.ig');
  }
}

// Export singleton
const jarvisDevice = new JarvisDeviceService();
export default jarvisDevice;
export { JarvisDeviceService };
