/**
 * Voice Activity Detection (VAD) Utility
 * Detects silence and automatically stops recording
 */

export class VoiceActivityDetector {
  constructor(options = {}) {
    this.silenceThreshold = options.silenceThreshold || 30; // 0-100
    this.silenceDuration = options.silenceDuration || 1500; // ms
    this.minRecordingTime = options.minRecordingTime || 500; // ms
    this.onVolumeChange = options.onVolumeChange || (() => {});
    this.onSilenceDetected = options.onSilenceDetected || (() => {});
    this.onAutoStop = options.onAutoStop || (() => {});
    
    this.audioContext = null;
    this.analyser = null;
    this.silenceTimer = null;
    this.recordingStartTime = null;
    this.animationFrame = null;
    this.isAnalyzing = false;
  }

  async start(stream) {
    try {
      // Set up Web Audio API
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.analyser.smoothingTimeConstant = 0.8;
      source.connect(this.analyser);

      this.recordingStartTime = Date.now();
      this.isAnalyzing = true;
      this.analyze();
      
      return true;
    } catch (error) {
      console.error('VAD Error:', error);
      return false;
    }
  }

  analyze() {
    if (!this.isAnalyzing || !this.analyser) return;

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(dataArray);

    // Calculate average volume
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    const normalizedVolume = Math.min(100, (average / 255) * 100);
    
    this.onVolumeChange(normalizedVolume);

    // Voice Activity Detection
    if (normalizedVolume < this.silenceThreshold) {
      // Silence detected
      if (!this.silenceTimer) {
        this.silenceTimer = Date.now();
      }
      
      const silenceDur = Date.now() - this.silenceTimer;
      this.onSilenceDetected(silenceDur);
      
      // Check if we should auto-stop
      const recordingTime = Date.now() - this.recordingStartTime;
      if (silenceDur >= this.silenceDuration && recordingTime >= this.minRecordingTime) {
        console.log('🛑 VAD: Auto-stopping due to silence');
        this.stop();
        this.onAutoStop();
        return;
      }
    } else {
      // Voice detected - reset silence timer
      this.silenceTimer = null;
      this.onSilenceDetected(0);
    }

    // Continue analyzing
    this.animationFrame = requestAnimationFrame(() => this.analyze());
  }

  stop() {
    this.isAnalyzing = false;
    
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    
    this.analyser = null;
    this.silenceTimer = null;
  }

  isActive() {
    return this.isAnalyzing;
  }
}

export default VoiceActivityDetector;
