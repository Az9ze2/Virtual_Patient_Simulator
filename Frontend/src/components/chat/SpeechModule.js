import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import ttsService from '../../services/ttsService';

const SpeechModule = ({ 
  onTranscript, 
  autoSpeak = false, 
  messageToSpeak = null,
  speakerGender = 'female',
  speakerAge = 'child'
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const [recognitionError, setRecognitionError] = useState('');
  const [ttsError, setTtsError] = useState('');

  const recognitionRef = useRef(null);
  const messageCounterRef = useRef(0); // Counter to force re-speak
  const isRecognitionActiveRef = useRef(false); // Track recognition state

  // ============ Initialize gTTS Service ============
  useEffect(() => {
    // Test gTTS service on initialization
    console.log('🔊 Initializing Thai gTTS service');
    
    // Monitor TTS service status
    const checkTTSStatus = () => {
      setIsSpeaking(ttsService.isSpeaking());
    };
    
    const statusInterval = setInterval(checkTTSStatus, 500);
    
    return () => {
      clearInterval(statusInterval);
      // Stop any ongoing TTS when component unmounts
      ttsService.stop();
    };
  }, []);

  // ============ Initialize Speech Recognition ============
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      setRecognitionError('❌ เบราว์เซอร์นี้ไม่รองรับการรับเสียง กรุณาใช้ Chrome, Edge หรือ Safari');
      return;
    }

    const recognition = new SpeechRecognition();
    
    // FIXED: Optimal settings for Thai
    recognition.lang = 'th-TH';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('🎤 Recognition STARTED');
      isRecognitionActiveRef.current = true;
      setIsListening(true);
      setRecognitionError('');
    };

    recognition.onresult = (event) => {
      console.log('📝 Recognition result received');
      
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptText = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          finalTranscript += transcriptText;
          console.log('✅ Final transcript:', transcriptText);
        } else {
          console.log('⏳ Interim:', transcriptText);
          setTranscript(transcriptText);
        }
      }

      if (finalTranscript) {
        setTranscript(finalTranscript);
        
        if (onTranscript) {
          console.log('📤 Sending transcript to parent');
          onTranscript(finalTranscript);
        }
      }
    };

    recognition.onerror = (event) => {
      console.error('❌ Recognition error:', event.error);
      isRecognitionActiveRef.current = false;
      
      let errorMessage = 'เกิดข้อผิดพลาด';
      
      switch(event.error) {
        case 'no-speech':
          errorMessage = '⚠️ ไม่ได้ยินเสียง กรุณาพูดให้ชัดเจน';
          break;
        case 'audio-capture':
          errorMessage = '❌ ไม่พบไมโครโฟน กรุณาเชื่อมต่อไมโครโฟน';
          break;
        case 'not-allowed':
          errorMessage = '🔒 กรุณาอนุญาตการใช้ไมโครโฟนในเบราว์เซอร์';
          break;
        case 'network':
          errorMessage = '🌐 เกิดข้อผิดพลาดเครือข่าย';
          break;
        case 'aborted':
          errorMessage = '⏹️ การบันทึกเสียงถูกยกเลิก';
          break;
        default:
          errorMessage = `❌ ข้อผิดพลาด: ${event.error}`;
      }
      
      setRecognitionError(errorMessage);
      setIsListening(false);
      
      setTimeout(() => {
        setRecognitionError('');
      }, 5000);
    };

    recognition.onend = () => {
      console.log('🛑 Recognition ENDED');
      isRecognitionActiveRef.current = false;
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current && isRecognitionActiveRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          console.log('Cleanup: recognition already stopped');
        }
      }
    };
  }, [onTranscript]);

  // ============ gTTS Speech Function ============
  const speakWithGTTS = React.useCallback(async (text) => {
    if (!text || text.trim().length === 0) {
      console.warn('⚠️ No text to speak');
      return;
    }

    try {
      setTtsError('');
      setIsSpeaking(true);
      
      console.log('🔊 Speaking with gTTS:', text.substring(0, 50));
      
      // Configure TTS options based on speaker characteristics
      const options = {
        language: 'th', // Always use Thai
        slow: speakerAge === 'child', // Slower for children
        volume: 0.8
      };
      
      await ttsService.speak(text, options);
      
    } catch (error) {
      console.error('❌ gTTS error:', error);
      setTtsError('❌ ไม่สามารถอ่านข้อความได้');
      setIsSpeaking(false);
      
      // Clear error after 5 seconds
      setTimeout(() => setTtsError(''), 5000);
    }
  }, [speakerAge]);

  // ============ Auto-speak messages using gTTS ============
  useEffect(() => {
    if (autoSpeak && messageToSpeak) {
      messageCounterRef.current += 1;
      console.log('🔊 NEW MESSAGE #' + messageCounterRef.current + ':', messageToSpeak.substring(0, 50));
      
      // Use gTTS service to speak Thai text
      speakWithGTTS(messageToSpeak);
    }
  }, [messageToSpeak, autoSpeak, speakWithGTTS]);

  // ============ FIXED: Better microphone start ============
  const startListening = () => {
    if (!recognitionRef.current) {
      setRecognitionError('❌ ระบบรับเสียงไม่พร้อม');
      return;
    }

    // FIXED: Stop any ongoing recognition first
    if (isRecognitionActiveRef.current) {
      console.log('⚠️ Recognition already active, stopping first...');
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.log('Could not stop recognition:', e);
      }
    }

    // Stop any gTTS speech
    if (ttsService.isSpeaking()) {
      console.log('🔇 Stopping gTTS for microphone');
      ttsService.stop();
      setIsSpeaking(false);
    }

    // FIXED: Wait for clean state then start
    setTimeout(() => {
      try {
        console.log('▶️ Starting recognition...');
        recognitionRef.current.start();
        setTranscript('');
        setRecognitionError('');
      } catch (err) {
        console.error('❌ Failed to start recognition:', err);
        
        if (err.name === 'InvalidStateError') {
          // Already started, try to restart
          setTimeout(() => {
            try {
              recognitionRef.current.start();
            } catch (e) {
              setRecognitionError('❌ ไม่สามารถเริ่มการฟังได้ กรุณารีเฟรชหน้า');
            }
          }, 500);
        } else {
          setRecognitionError('❌ ไม่สามารถเริ่มการฟังได้');
        }
      }
    }, 200);
  };

  const stopListening = () => {
    if (recognitionRef.current && isRecognitionActiveRef.current) {
      console.log('⏹️ Stopping recognition manually');
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.log('Could not stop:', e);
      }
    }
  };


  const stopSpeaking = () => {
    console.log('🔇 Stopping gTTS manually');
    ttsService.stop();
    setIsSpeaking(false);
    setTtsError('');
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <div className="speech-module-error">
        <p>⚠️ เบราว์เซอร์นี้ไม่รองรับการใช้งานเสียง</p>
        <p style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
          แนะนำให้ใช้ Google Chrome, Microsoft Edge หรือ Safari
        </p>
      </div>
    );
  }

  return (
    <div className="speech-module">
      {/* Microphone Button */}
      <button
        className={`btn-speech ${isListening ? 'listening' : ''}`}
        onClick={toggleListening}
        disabled={isSpeaking}
        title={isListening ? 'หยุดฟัง (คลิกอีกครั้ง)' : 'กดแล้วพูด'}
        type="button"
      >
        {isListening ? <MicOff size={20} /> : <Mic size={20} />}
      </button>

      {/* Speaker Button */}
      <button
        className={`btn-speech ${isSpeaking ? 'speaking' : ''}`}
        onClick={stopSpeaking}
        disabled={!isSpeaking}
        title={isSpeaking ? 'หยุดพูด' : 'ไม่ได้พูด'}
        type="button"
      >
        {isSpeaking ? <VolumeX size={20} /> : <Volume2 size={20} />}
      </button>

      {/* Status Display */}
      {isListening && (
        <div className="speech-status listening-status">
          <span className="status-dot"></span>
          {transcript ? `"${transcript.substring(0, 30)}..."` : 'กำลังฟัง...'}
        </div>
      )}

      {isSpeaking && (
        <div className="speech-status speaking-status">
          <span className="status-dot"></span>
          กำลังพูด...
        </div>
      )}

      {/* Error Popups */}
      {recognitionError && (
        <div className="speech-error-popup recognition-error">
          {recognitionError}
        </div>
      )}
      
      {ttsError && (
        <div className="speech-error-popup tts-error">
          {ttsError}
        </div>
      )}
    </div>
  );
};

export default SpeechModule;