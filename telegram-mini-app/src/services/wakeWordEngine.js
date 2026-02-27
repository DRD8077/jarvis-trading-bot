/**
 * 🎙️ JARVIS Wake Word Engine — Always-On Voice Listener
 * ═══════════════════════════════════════════════════════
 * 
 * Listens for "Hey JARVIS" or "JARVIS" wake word continuously.
 * 3-layer architecture:
 *   1. Capacitor SpeechRecognition (Android native — best)
 *   2. Web Speech API (Chrome/Edge)
 *   3. Polling MediaRecorder → Server transcription (fallback)
 * 
 * Once wake word detected:
 *   - Plays activation sound
 *   - Opens AI Chat in listen mode
 *   - Vibrates phone (haptic feedback)
 */

class JarvisWakeWordEngine {
  constructor() {
    this.isListening = false;
    this.isSleeping = false;  // Sleep mode — JARVIS is quiet but still listening for wake-up
    this.recognition = null;
    this.listeners = [];
    this.sleepListeners = [];
    this.restartTimeout = null;
    this.consecutiveErrors = 0;
    this.maxErrors = 5;
    
    // Wake word patterns
    this.wakeWords = [
      'jarvis', 'hey jarvis', 'ok jarvis', 'hi jarvis',
      'hello jarvis', 'are you there jarvis', 'wake up jarvis',
      'jarvis wake up', 'jarvis uth jao', 'jarvis utho',
      'जार्विस', 'हे जार्विस', 'जार्विस उठो', 'जार्विस जागो',
    ];

    // Sleep command patterns
    this.sleepWords = [
      'jarvis go to sleep', 'go to sleep jarvis', 'jarvis sleep',
      'jarvis so jao', 'jarvis band karo', 'jarvis chup raho',
      'jarvis rest karo', 'good night jarvis', 'jarvis good night',
      'जार्विस सो जाओ', 'जार्विस बंद करो', 'जार्विस चुप रहो',
    ];

    // Wake-from-sleep patterns (subset — only explicit wake-up commands)
    this.wakeFromSleepWords = [
      'jarvis wake up', 'wake up jarvis', 'hey jarvis wake up',
      'jarvis uth jao', 'jarvis utho', 'jarvis jago',
      'जार्विस उठो', 'जार्विस जागो',
    ];
    
    console.log('[Wake Word Engine] Initialized');
  }

  /**
   * Register callback for when wake word is detected
   */
  onWakeWord(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  /**
   * Register callback for sleep/wake state changes
   */
  onSleepStateChange(callback) {
    this.sleepListeners.push(callback);
    return () => {
      this.sleepListeners = this.sleepListeners.filter(l => l !== callback);
    };
  }

  /**
   * Put JARVIS to sleep — she'll only listen for wake-up command
   */
  sleep() {
    this.isSleeping = true;
    console.log('[Wake Word Engine] 😴 JARVIS is sleeping — say "JARVIS wake up" to resume');
    this.sleepListeners.forEach(cb => {
      try { cb({ sleeping: true }); } catch {}
    });
  }

  /**
   * Wake JARVIS from sleep
   */
  wake() {
    this.isSleeping = false;
    console.log('[Wake Word Engine] ⚡ JARVIS is awake and ready!');
    this.sleepListeners.forEach(cb => {
      try { cb({ sleeping: false }); } catch {}
    });
  }

  /**
   * Start listening for wake word
   */
  async start() {
    if (this.isListening) return;
    
    console.log('[Wake Word Engine] Starting continuous listening...');
    this.isListening = true;
    this.consecutiveErrors = 0;
    
    // Try native Capacitor first
    const started = await this._tryCapacitorSTT() || await this._tryWebSpeechAPI();
    
    if (!started) {
      console.log('[Wake Word Engine] No speech recognition available — wake word disabled');
      this.isListening = false;
    }
    
    return started;
  }

  /**
   * Stop listening
   */
  stop() {
    this.isListening = false;
    this.consecutiveErrors = 0;
    
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
      this.restartTimeout = null;
    }
    
    try {
      if (this.recognition) {
        this.recognition.abort?.();
        this.recognition.stop?.();
        this.recognition = null;
      }
    } catch {}
    
    // Try Capacitor stop
    this._stopCapacitor();
    
    console.log('[Wake Word Engine] Stopped');
  }

  /**
   * Check if sleep command is in transcript
   */
  _checkSleepCommand(transcript) {
    const lower = transcript.toLowerCase().trim();
    for (const word of this.sleepWords) {
      if (lower.includes(word)) return true;
    }
    return false;
  }

  /**
   * Check if wake-from-sleep command is in transcript
   */
  _checkWakeFromSleep(transcript) {
    const lower = transcript.toLowerCase().trim();
    for (const word of this.wakeFromSleepWords) {
      if (lower.includes(word)) return true;
    }
    return false;
  }

  /**
   * Check if wake word is in transcript
   */
  _checkWakeWord(transcript) {
    const lower = transcript.toLowerCase().trim();

    // If sleeping, only respond to explicit wake-up commands
    if (this.isSleeping) {
      return this._checkWakeFromSleep(transcript);
    }

    // Check for sleep command first
    if (this._checkSleepCommand(transcript)) {
      this.sleep();
      // Fire a special "sleep" event to the listeners so UI can respond
      this.listeners.forEach(cb => {
        try { cb('__JARVIS_SLEEP__'); } catch {}
      });
      return false; // Don't trigger normal wake word flow
    }

    for (const word of this.wakeWords) {
      if (lower.includes(word)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Fire wake word detected event
   */
  _fireWakeWord(transcript) {
    // If waking from sleep, announce it
    if (this.isSleeping) {
      this.wake();
      console.log('[Wake Word Engine] ⚡ JARVIS woke up from sleep via:', transcript);
    }

    console.log('[Wake Word Engine] 🎯 WAKE WORD DETECTED:', transcript);
    
    // Haptic feedback
    try {
      if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
    } catch {}
    
    // Play activation sound
    this._playActivationSound();
    
    // Notify all listeners
    this.listeners.forEach(cb => {
      try { cb(transcript); } catch (e) {
        console.error('[Wake Word Engine] Listener error:', e);
      }
    });
  }

  /**
   * Play JARVIS activation sound — disabled to avoid annoying beeps
   */
  _playActivationSound() {
    // Disabled — no beep sounds on activation
    // Haptic vibration is enough feedback
  }

  /**
   * Try Capacitor SpeechRecognition (Android native)
   */
  async _tryCapacitorSTT() {
    try {
      const { SpeechRecognition } = await import('@capacitor-community/speech-recognition');
      
      // Check/request permission
      const permResult = await SpeechRecognition.requestPermissions();
      if (permResult?.speechRecognition !== 'granted') {
        console.log('[Wake Word Engine] Capacitor STT — permission denied');
        return false;
      }

      const startCapacitorSession = async () => {
        if (!this.isListening) return;
        
        try {
          const result = await SpeechRecognition.start({
            language: 'hi-IN',
            maxResults: 3,
            popup: false,
            partialResults: true,
          });

          const matches = result?.matches || [];
          for (const match of matches) {
            if (this._checkWakeWord(match)) {
              this._fireWakeWord(match);
              // Brief pause before restarting (let the main voice assistant take over)
              await new Promise(r => setTimeout(r, 3000));
              break;
            }
          }
        } catch (e) {
          this.consecutiveErrors++;
          if (this.consecutiveErrors > this.maxErrors) {
            console.log('[Wake Word Engine] Too many Capacitor errors, stopping');
            this.isListening = false;
            return;
          }
        }

        // Restart listening loop
        if (this.isListening) {
          this.restartTimeout = setTimeout(startCapacitorSession, 500);
        }
      };

      startCapacitorSession();
      console.log('[Wake Word Engine] ✅ Using Capacitor SpeechRecognition (native)');
      return true;
    } catch (e) {
      console.log('[Wake Word Engine] Capacitor STT not available:', e.message);
      return false;
    }
  }

  async _stopCapacitor() {
    try {
      const { SpeechRecognition } = await import('@capacitor-community/speech-recognition');
      await SpeechRecognition.stop();
    } catch {}
  }

  /**
   * Try Web Speech API (Chrome/Edge)
   */
  async _tryWebSpeechAPI() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return false;

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'hi-IN';
      this.recognition.maxAlternatives = 3;

      this.recognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (this._checkWakeWord(transcript)) {
            this._fireWakeWord(transcript);
            // Restart after a pause
            this.recognition.stop();
            if (this.isListening) {
              this.restartTimeout = setTimeout(() => {
                try { this.recognition.start(); } catch {}
              }, 3000);
            }
            return;
          }
        }
      };

      this.recognition.onerror = (event) => {
        if (event.error === 'not-allowed') {
          console.log('[Wake Word Engine] Microphone permission denied');
          this.isListening = false;
          return;
        }
        
        this.consecutiveErrors++;
        if (this.consecutiveErrors > this.maxErrors) {
          this.isListening = false;
          return;
        }

        // Auto-restart on non-fatal errors
        if (this.isListening) {
          this.restartTimeout = setTimeout(() => {
            try { this.recognition.start(); } catch {}
          }, 1000);
        }
      };

      this.recognition.onend = () => {
        this.consecutiveErrors = 0;
        if (this.isListening) {
          this.restartTimeout = setTimeout(() => {
            try { this.recognition.start(); } catch {}
          }, 500);
        }
      };

      this.recognition.start();
      console.log('[Wake Word Engine] ✅ Using Web Speech API (browser)');
      return true;
    } catch (e) {
      console.log('[Wake Word Engine] Web Speech API failed:', e.message);
      return false;
    }
  }
}

// Singleton
let instance = null;

export function getWakeWordEngine() {
  if (!instance) instance = new JarvisWakeWordEngine();
  return instance;
}

export default JarvisWakeWordEngine;
