import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

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
  const [error, setError] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const [recognitionError, setRecognitionError] = useState('');

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const messageCounterRef = useRef(0); // FIXED: Counter to force re-speak
  const isRecognitionActiveRef = useRef(false); // FIXED: Track recognition state
  const availableVoicesRef = useRef([]);
  const voicesLoadedRef = useRef(false);

  // ============ Load voices ============
  useEffect(() => {
    const loadVoices = () => {
      const voices = synthRef.current.getVoices();
      if (voices.length > 0) {
        availableVoicesRef.current = voices;
        voicesLoadedRef.current = true;
        console.log('🎤 Loaded voices:', voices.length);
        console.log('🎤 Thai voices available:', voices.filter(v => v.lang.startsWith('th')).map(v => v.name));
      }
    };

    loadVoices();
    
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = loadVoices;
    }

    // Force load after delay
    setTimeout(loadVoices, 100);

    return () => {
      if (synthRef.current.onvoiceschanged !== undefined) {
        synthRef.current.onvoiceschanged = null;
      }
    };
  }, []);

  // ============ Initialize Speech Recognition ============
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('❌ เบราว์เซอร์นี้ไม่รองรับการรับเสียง กรุณาใช้ Chrome, Edge หรือ Safari');
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
      setError('');
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

  // ============ FIXED: Force speak EVERY message with counter ============
  useEffect(() => {
    if (autoSpeak && messageToSpeak) {
      messageCounterRef.current += 1;
      console.log('🔊 NEW MESSAGE #' + messageCounterRef.current + ':', messageToSpeak.substring(0, 50));
      
      // Force speak with unique trigger
      speakText(messageToSpeak, messageCounterRef.current);
    }
  }, [messageToSpeak, autoSpeak]);

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

    // FIXED: Stop any speech
    if (synthRef.current.speaking) {
      console.log('🔇 Stopping speech for microphone');
      synthRef.current.cancel();
      setIsSpeaking(false);
    }

    // FIXED: Wait for clean state then start
    setTimeout(() => {
      try {
        console.log('▶️ Starting recognition...');
        recognitionRef.current.start();
        setTranscript('');
        setError('');
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

  // ============ Smart voice selection ============
  const selectBestVoice = () => {
    if (!voicesLoadedRef.current || availableVoicesRef.current.length === 0) {
      console.warn('⚠️ No voices loaded yet');
      return null;
    }

    const voices = availableVoicesRef.current;
    
    // Try Thai voices first
    const thaiVoices = voices.filter(voice => voice.lang.startsWith('th'));
    
    if (thaiVoices.length > 0) {
      console.log('🎯 Using Thai voice');
      
      if (speakerAge === 'child') {
        const childVoice = thaiVoices.find(v => 
          v.name.toLowerCase().includes('child') || 
          v.name.toLowerCase().includes('kid')
        );
        if (childVoice) return childVoice;
      }
      
      if (speakerGender === 'female') {
        const femaleVoice = thaiVoices.find(v => 
          v.name.toLowerCase().includes('female') || 
          v.name.toLowerCase().includes('woman') ||
          v.name.toLowerCase().includes('samantha') ||
          (!v.name.toLowerCase().includes('male') && !v.name.toLowerCase().includes('man'))
        );
        if (femaleVoice) return femaleVoice;
      } else if (speakerGender === 'male') {
        const maleVoice = thaiVoices.find(v => 
          v.name.toLowerCase().includes('male') ||
          v.name.toLowerCase().includes('man')
        );
        if (maleVoice) return maleVoice;
      }
      
      return thaiVoices[0];
    }
    
    console.log('⚠️ No Thai voices, using default');
    return voices[0] || null;
  };

  // ============ FIXED: Force speak with counter ============
  const speakText = (text, counter) => {
    if (!text) return;

    console.log('🔊 Speaking message #' + counter);

    // FIXED: Force cancel completely
    synthRef.current.cancel();
    
    // FIXED: Longer delay to ensure cancel completes
    setTimeout(() => {
      // Double-check cancel
      if (synthRef.current.speaking) {
        console.log('⚠️ Still speaking, forcing cancel again');
        synthRef.current.cancel();
      }

      setTimeout(() => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'th-TH';
        
        // Adjust voice characteristics
        if (speakerAge === 'child') {
          utterance.rate = 0.7;
          utterance.pitch = 1.5;
        } else if (speakerGender === 'female') {
          utterance.rate = 0.7;
          utterance.pitch = 1.1;
        } else {
          utterance.rate = 0.7;
          utterance.pitch = 0.9;
        }
        
        utterance.volume = 1.0;

        utterance.onstart = () => {
          console.log('✅ TTS started');
          setIsSpeaking(true);
          setError('');
        };

        utterance.onend = () => {
          console.log('✅ TTS ended');
          setIsSpeaking(false);
        };

        utterance.onerror = (event) => {
          console.error('❌ TTS error:', event.error);
          setIsSpeaking(false);
        };

        // Select voice
        const selectedVoice = selectBestVoice();
        if (selectedVoice) {
          utterance.voice = selectedVoice;
          console.log('🎤 Voice:', selectedVoice.name);
        }

        // FIXED: Speak immediately
        console.log('▶️ Starting speech...');
        synthRef.current.speak(utterance);
      }, 100);
    }, 200);
  };

  const stopSpeaking = () => {
    console.log('🔇 Stopping speech manually');
    synthRef.current.cancel();
    setIsSpeaking(false);
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

      {/* Error Popup */}
      {recognitionError && (
        <div className="speech-error-popup">
          {recognitionError}
        </div>
      )}
    </div>
  );
};

export default SpeechModule;