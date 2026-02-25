/**
 * 🎮 JARVIS Gaming Screen Analyzer — Real-time Game Vision AI
 * ══════════════════════════════════════════════════════════════
 * Captures & analyzes game screen in real-time during BGMI/PUBG.
 * Uses MediaProjection API (Android) or Screen Capture API (Desktop).
 * Sends frames to JARVIS AI for tactical analysis.
 */

const ANALYSIS_INTERVAL = 600; // ms between frame analyses
const FRAME_QUALITY = 0.65; // JPEG quality (balance speed vs accuracy)
const MAX_FRAME_SIZE = 512; // Max dimension for sent frames

class JarvisGameVision {
  constructor() {
    this.isActive = false;
    this.stream = null;
    this.videoElement = null;
    this.canvas = null;
    this.ctx = null;
    this.analysisTimer = null;
    this.frameCount = 0;
    this.lastAnalysis = null;
    this.callbackOnAnalysis = null;
    this.callbackOnCallout = null;
    this.apiBase = window.API_BASE || 'http://127.0.0.1:8000';
    this.isDesktop = !!window.jarvisDesktop;
    this.gamingProfile = 'jonathan_gaming';
    this.performanceMode = false; // true = lower quality, faster analysis
    
    // Game state tracking
    this.gameState = {
      state: 'unknown',
      enemies: 0,
      health: 100,
      zone: 0,
      kills: 0,
      weapon: null,
      dangerLevel: 'safe',
    };
    
    // Callout history
    this.calloutHistory = [];
    this.lastCalloutTime = 0;
    this.calloutCooldown = 2000; // 2 seconds between voice callouts
  }

  // ═══════════════════════════════════
  // SCREEN CAPTURE — Start/Stop
  // ═══════════════════════════════════

  async startScreenCapture() {
    try {
      if (this.isDesktop && window.jarvisDesktop) {
        // Desktop: Use Electron screen capture
        return await this._startDesktopCapture();
      } else {
        // Mobile/Browser: Use MediaProjection / Screen Capture API
        return await this._startMobileCapture();
      }
    } catch (err) {
      console.error('[GameVision] Failed to start:', err);
      return { success: false, error: err.message };
    }
  }

  async _startDesktopCapture() {
    // Electron: periodic screenshot capture
    this.isActive = true;
    this._startAnalysisLoop('desktop');
    
    return {
      success: true,
      mode: 'desktop',
      message: '🖥️ Desktop screen capture started! JARVIS is watching your game.',
    };
  }

  async _startMobileCapture() {
    // Request screen capture permission
    if (!navigator.mediaDevices?.getDisplayMedia) {
      // Fallback: ask user to share screenshots manually
      this.isActive = true;
      this._startAnalysisLoop('manual');
      return {
        success: true,
        mode: 'manual',
        message: '📱 Manual mode: Take screenshots during gameplay, JARVIS will analyze them!',
      };
    }

    try {
      this.stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          cursor: 'never',
          displaySurface: 'monitor',
          frameRate: { ideal: 5, max: 10 }, // Low FPS for analysis
        },
        audio: false,
      });

      // Create hidden video element
      this.videoElement = document.createElement('video');
      this.videoElement.srcObject = this.stream;
      this.videoElement.autoplay = true;
      this.videoElement.muted = true;
      this.videoElement.style.display = 'none';
      document.body.appendChild(this.videoElement);

      // Create canvas for frame capture
      this.canvas = document.createElement('canvas');
      this.ctx = this.canvas.getContext('2d');

      // Wait for video to be ready
      await new Promise((resolve) => {
        this.videoElement.onloadedmetadata = () => {
          this.canvas.width = Math.min(this.videoElement.videoWidth, MAX_FRAME_SIZE);
          this.canvas.height = Math.min(
            this.videoElement.videoHeight,
            Math.round((this.videoElement.videoHeight / this.videoElement.videoWidth) * MAX_FRAME_SIZE)
          );
          resolve();
        };
      });

      this.isActive = true;
      this._startAnalysisLoop('stream');

      // Handle stream end
      this.stream.getTracks().forEach(track => {
        track.onended = () => this.stopScreenCapture();
      });

      return {
        success: true,
        mode: 'stream',
        resolution: `${this.canvas.width}x${this.canvas.height}`,
        message: '📺 Screen sharing started! JARVIS is analyzing your gameplay in real-time!',
      };
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        return {
          success: false,
          error: 'Screen sharing permission denied. Please allow screen sharing to enable gaming AI.',
        };
      }
      throw err;
    }
  }

  stopScreenCapture() {
    this.isActive = false;

    if (this.analysisTimer) {
      clearInterval(this.analysisTimer);
      this.analysisTimer = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.videoElement) {
      this.videoElement.remove();
      this.videoElement = null;
    }

    return {
      success: true,
      framesAnalyzed: this.frameCount,
      message: '📺 Screen sharing stopped. Good game!',
      gameState: this.gameState,
    };
  }

  // ═══════════════════════════════════
  // ANALYSIS LOOP
  // ═══════════════════════════════════

  _startAnalysisLoop(mode) {
    const interval = this.performanceMode ? ANALYSIS_INTERVAL * 2 : ANALYSIS_INTERVAL;

    this.analysisTimer = setInterval(async () => {
      if (!this.isActive) return;

      try {
        let frameData;

        if (mode === 'stream' && this.videoElement && this.ctx) {
          // Capture frame from video stream
          this.ctx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
          frameData = this.canvas.toDataURL('image/jpeg', FRAME_QUALITY);
        } else if (mode === 'desktop' && window.jarvisDesktop) {
          // Capture from Electron
          const result = await window.jarvisDesktop.captureScreen();
          if (result?.success) {
            frameData = result.image;
          }
        }

        if (frameData) {
          this.frameCount++;
          await this._analyzeFrame(frameData);
        }
      } catch (err) {
        console.error('[GameVision] Frame analysis error:', err);
      }
    }, interval);
  }

  async _analyzeFrame(frameData) {
    try {
      const response = await fetch(`${this.apiBase}/api/gaming/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frame: frameData,
          profile: this.gamingProfile,
          frame_number: this.frameCount,
          previous_state: this.gameState.state,
        }),
      });

      if (!response.ok) {
        // Fallback: local analysis
        return this._localAnalysis(frameData);
      }

      const analysis = await response.json();
      this._processAnalysis(analysis);
    } catch (err) {
      // Server unavailable — use local analysis
      this._localAnalysis(frameData);
    }
  }

  _processAnalysis(analysis) {
    this.lastAnalysis = analysis;

    // Update game state
    if (analysis.analysis) {
      const a = analysis.analysis;
      this.gameState = {
        state: a.state || this.gameState.state,
        enemies: a.enemies_visible || 0,
        health: a.health_percent || this.gameState.health,
        zone: a.zone_phase || this.gameState.zone,
        kills: a.kill_count || this.gameState.kills,
        weapon: a.current_weapon || this.gameState.weapon,
        dangerLevel: a.danger_level || 'safe',
        scope: a.current_scope || 'none',
        inVehicle: a.in_vehicle || false,
        isProne: a.is_prone || false,
        tacticalAdvice: a.tactical_advice || '',
        recommendedAction: a.recommended_action || '',
      };
    }

    // Process callouts
    if (analysis.callouts) {
      const now = Date.now();
      for (const callout of analysis.callouts) {
        this.calloutHistory.push({ text: callout, time: now });

        // Voice callout (with cooldown)
        if (now - this.lastCalloutTime > this.calloutCooldown) {
          this._voiceCallout(callout);
          this.lastCalloutTime = now;
        }
      }

      // Trim history
      if (this.calloutHistory.length > 100) {
        this.calloutHistory = this.calloutHistory.slice(-50);
      }
    }

    // Notify callbacks
    if (this.callbackOnAnalysis) {
      this.callbackOnAnalysis(analysis);
    }
  }

  _localAnalysis(frameData) {
    // Basic local analysis when server is unavailable
    const analysis = {
      analysis: { state: 'playing', note: 'Local mode — connect to server for full AI analysis' },
      callouts: ['🎮 Playing in local mode — AI analysis needs server connection'],
    };
    this._processAnalysis(analysis);
  }

  // ═══════════════════════════════════
  // VOICE CALLOUTS
  // ═══════════════════════════════════

  _voiceCallout(text) {
    // Strip emoji for speech
    const cleanText = text.replace(/[\u{1F300}-\u{1FAFF}]|[\u{2600}-\u{27BF}]/gu, '').trim();
    
    if ('speechSynthesis' in window && cleanText) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'en-IN';
      utterance.rate = 1.2; // Slightly fast for gaming callouts
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      
      // Try to find a good voice
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => 
        v.name.includes('Google') || v.name.includes('English')
      );
      if (preferredVoice) utterance.voice = preferredVoice;
      
      window.speechSynthesis.speak(utterance);
    }

    if (this.callbackOnCallout) {
      this.callbackOnCallout(text);
    }
  }

  // ═══════════════════════════════════
  // MANUAL FRAME ANALYSIS
  // ═══════════════════════════════════

  async analyzeScreenshot(imageDataOrFile) {
    let frameData;
    
    if (typeof imageDataOrFile === 'string') {
      frameData = imageDataOrFile;
    } else if (imageDataOrFile instanceof File) {
      frameData = await this._fileToDataUrl(imageDataOrFile);
    } else {
      return { error: 'Invalid input — provide base64 string or File object' };
    }

    this.frameCount++;
    await this._analyzeFrame(frameData);
    return this.lastAnalysis;
  }

  _fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  // ═══════════════════════════════════
  // PROFILE MANAGEMENT
  // ═══════════════════════════════════

  async setProfile(profileName) {
    this.gamingProfile = profileName.toLowerCase().replace(/\s+/g, '_');
    
    try {
      const response = await fetch(`${this.apiBase}/api/gaming/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileName }),
      });
      
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      // Offline mode
    }
    
    return {
      status: 'switched',
      profile: profileName,
      message: `🎮 Switched to ${profileName} profile!`,
    };
  }

  // ═══════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════

  getGameState() { return this.gameState; }
  getCalloutHistory() { return this.calloutHistory; }
  getFrameCount() { return this.frameCount; }
  isScreenSharing() { return this.isActive; }

  // ═══════════════════════════════════
  // EVENT HANDLERS
  // ═══════════════════════════════════

  onAnalysis(callback) { this.callbackOnAnalysis = callback; }
  onCallout(callback) { this.callbackOnCallout = callback; }
}

// Export singleton
const jarvisGameVision = new JarvisGameVision();
export default jarvisGameVision;
export { JarvisGameVision };
