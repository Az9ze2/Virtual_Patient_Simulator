/**
 * Thai Text-to-Speech Service using Google TTS
 * Provides high-quality Thai language synthesis
 */

class TTSService {
  constructor() {
    this.audioQueue = [];
    this.isPlaying = false;
    this.currentAudio = null;
    this.baseURL = 'https://translate.google.com/translate_tts';
    
    // Default settings for Thai TTS
    this.settings = {
      language: 'th', // Thai language code
      slow: false,    // Normal speed
      host: 'translate.google.com',
      client: 'tw-ob'
    };
    
    console.log('🔊 Thai TTS Service initialized');
  }

  /**
   * Generate audio URL for Thai text using Google TTS
   * @param {string} text - Text to convert to speech
   * @param {Object} options - Optional parameters
   * @returns {string} - Audio URL
   */
  generateAudioURL(text, options = {}) {
    if (!text || text.trim().length === 0) {
      console.warn('⚠️ Empty text provided to TTS');
      return null;
    }

    // Merge options with defaults
    const config = { ...this.settings, ...options };
    
    // Clean text for TTS
    const cleanText = this.cleanTextForTTS(text);
    
    // Build URL parameters
    const params = new URLSearchParams({
      ie: 'UTF-8',
      q: cleanText,
      tl: config.language,
      client: config.client,
      tk: this.generateToken(cleanText), // Simple token generation
      ttsspeed: config.slow ? '0.24' : '0.5'
    });

    const audioURL = `${this.baseURL}?${params.toString()}`;
    
    console.log('🎵 Generated Thai TTS URL for:', cleanText.substring(0, 50));
    return audioURL;
  }

  /**
   * Clean text for optimal TTS synthesis
   * @param {string} text - Raw text
   * @returns {string} - Cleaned text
   */
  cleanTextForTTS(text) {
    return text
      .trim()
      .replace(/\s+/g, ' ')                    // Multiple spaces to single
      .replace(/[^\u0E00-\u0E7Fa-zA-Z0-9\s.,!?]/g, '') // Keep Thai, English, numbers, basic punctuation
      .substring(0, 200);                      // Limit length for TTS API
  }

  /**
   * Simple token generation for Google TTS
   * @param {string} text - Text to generate token for
   * @returns {string} - Generated token
   */
  generateToken(text) {
    // Simple hash-based token (for demo purposes)
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString();
  }

  /**
   * Speak Thai text using Google TTS
   * @param {string} text - Thai text to speak
   * @param {Object} options - Speech options
   * @returns {Promise} - Promise that resolves when speech starts
   */
  async speak(text, options = {}) {
    return new Promise((resolve, reject) => {
      try {
        if (!text || text.trim().length === 0) {
          console.warn('⚠️ No text to speak');
          resolve();
          return;
        }

        console.log('🔊 Speaking Thai text:', text.substring(0, 50));

        // Stop any current speech
        this.stop();

        const audioURL = this.generateAudioURL(text, options);
        if (!audioURL) {
          reject(new Error('Failed to generate audio URL'));
          return;
        }

        // Create audio element
        const audio = new Audio();
        this.currentAudio = audio;

        // Configure audio
        audio.preload = 'auto';
        audio.volume = options.volume || 1.0;

        // Event handlers
        audio.onloadstart = () => {
          console.log('📡 Loading Thai TTS audio...');
        };

        audio.oncanplay = () => {
          console.log('✅ Thai TTS audio ready');
          this.isPlaying = true;
          audio.play()
            .then(() => {
              console.log('▶️ Thai TTS playback started');
              resolve();
            })
            .catch((error) => {
              console.error('❌ Playback failed:', error);
              this.isPlaying = false;
              reject(error);
            });
        };

        audio.onended = () => {
          console.log('✅ Thai TTS playback completed');
          this.isPlaying = false;
          this.currentAudio = null;
          
          // Process queue if there are more items
          this.processQueue();
        };

        audio.onerror = (error) => {
          console.error('❌ Thai TTS audio error:', error);
          this.isPlaying = false;
          this.currentAudio = null;
          reject(new Error('TTS audio failed to load'));
        };

        audio.onpause = () => {
          console.log('⏸️ Thai TTS paused');
          this.isPlaying = false;
        };

        // Set audio source (this triggers loading)
        audio.src = audioURL;

      } catch (error) {
        console.error('❌ TTS speak error:', error);
        this.isPlaying = false;
        this.currentAudio = null;
        reject(error);
      }
    });
  }

  /**
   * Add text to speech queue
   * @param {string} text - Text to queue
   * @param {Object} options - Speech options
   */
  queue(text, options = {}) {
    if (text && text.trim().length > 0) {
      this.audioQueue.push({ text, options });
      console.log(`📝 Added to TTS queue: "${text.substring(0, 30)}..." (Queue: ${this.audioQueue.length})`);
      
      if (!this.isPlaying) {
        this.processQueue();
      }
    }
  }

  /**
   * Process the audio queue
   */
  async processQueue() {
    if (this.audioQueue.length === 0 || this.isPlaying) {
      return;
    }

    const { text, options } = this.audioQueue.shift();
    
    try {
      await this.speak(text, options);
    } catch (error) {
      console.error('❌ Queue processing error:', error);
      // Continue with next item in queue
      setTimeout(() => this.processQueue(), 1000);
    }
  }

  /**
   * Stop current speech and clear queue
   */
  stop() {
    console.log('🛑 Stopping Thai TTS');
    
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    
    this.isPlaying = false;
    this.audioQueue = []; // Clear queue
  }

  /**
   * Pause current speech
   */
  pause() {
    if (this.currentAudio && !this.currentAudio.paused) {
      console.log('⏸️ Pausing Thai TTS');
      this.currentAudio.pause();
      this.isPlaying = false;
    }
  }

  /**
   * Resume paused speech
   */
  resume() {
    if (this.currentAudio && this.currentAudio.paused) {
      console.log('▶️ Resuming Thai TTS');
      this.currentAudio.play()
        .then(() => {
          this.isPlaying = true;
        })
        .catch((error) => {
          console.error('❌ Resume failed:', error);
        });
    }
  }

  /**
   * Check if TTS is currently speaking
   * @returns {boolean} - True if speaking
   */
  isSpeaking() {
    return this.isPlaying && this.currentAudio && !this.currentAudio.paused;
  }

  /**
   * Get queue length
   * @returns {number} - Number of items in queue
   */
  getQueueLength() {
    return this.audioQueue.length;
  }

  /**
   * Clear the speech queue
   */
  clearQueue() {
    this.audioQueue = [];
    console.log('🗑️ TTS queue cleared');
  }

  /**
   * Set TTS configuration
   * @param {Object} config - Configuration options
   */
  configure(config) {
    this.settings = { ...this.settings, ...config };
    console.log('⚙️ TTS configured:', this.settings);
  }

  /**
   * Test TTS with sample Thai text
   */
  async test() {
    const testText = 'สวัสดีครับ ผมเป็นระบบอ่านข้อความภาษาไทย';
    console.log('🧪 Testing Thai TTS...');
    
    try {
      await this.speak(testText);
      console.log('✅ Thai TTS test successful');
    } catch (error) {
      console.error('❌ Thai TTS test failed:', error);
      throw error;
    }
  }
}

// Create singleton instance
const ttsService = new TTSService();

// Export the service
export default ttsService;

// Export class for advanced usage
export { TTSService };