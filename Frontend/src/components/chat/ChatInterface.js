import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader, Mic, Volume2, VolumeX } from 'lucide-react';
import apiService from '../../services/apiService';
import './ChatInterface.css';

const ChatInterface = () => {
  const { sessionData, addMessage, updateSession } = useApp();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // ============ STT STATE ============
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [sttError, setSttError] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  // ============ SILENCE DETECTION STATE ============
  const [isListeningForSilence, setIsListeningForSilence] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  // ============ TTS STATE ============
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsVoice, setTtsVoice] = useState('nova');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimeoutRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);
  
  // ============ AUDIO ANALYSIS REFS ============
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastSoundTimeRef = useRef(0);
  const hasSpeechDetectedRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessionData?.messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!isLoading && !isRecording) {
      inputRef.current?.focus();
    }
  }, [isLoading, isRecording, sessionData?.messages]);

  useEffect(() => {
    if (sttError) {
      const timer = setTimeout(() => {
        setSttError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [sttError]);

  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    }
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const playAudio = (base64Audio) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      const audioUrl = `data:audio/mp3;base64,${base64Audio}`;
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onplay = () => {
        setIsPlayingAudio(true);
        console.log('🔊 TTS audio started playing');
      };
      
      audio.onended = () => {
        setIsPlayingAudio(false);
        console.log('✅ TTS audio finished playing');
      };
      
      audio.onerror = (error) => {
        setIsPlayingAudio(false);
        console.error('❌ TTS audio playback error:', error);
      };
      
      audio.play().catch(error => {
        console.error('❌ Failed to play audio:', error);
        setIsPlayingAudio(false);
      });
    } catch (error) {
      console.error('❌ Error playing audio:', error);
      setIsPlayingAudio(false);
    }
  };

  // ============ 🎯 NEW: BUILD CONVERSATION CONTEXT FOR AI CORRECTION ============
  const getConversationContext = () => {
    return apiService.buildConversationContext(
      sessionData?.messages || [], 
      sessionData?.caseData
    );
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !sessionData?.sessionId) return;

    const userMessage = input.trim();
    setInput('');

    addMessage({
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    });

    setIsLoading(true);

    try {
      const response = ttsEnabled 
        ? await apiService.sendMessageWithTTS(sessionData.sessionId, userMessage, true, ttsVoice, 1.0)
        : await apiService.sendMessage(sessionData.sessionId, userMessage);
      
      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.data.response,
          timestamp: Date.now()
        });

        if (ttsEnabled && response.data.audio && response.data.audio.audio_base64) {
          console.log('🎵 Playing TTS audio response...');
          playAudio(response.data.audio.audio_base64);
        }

        const tokens = response.data.token_usage;
        if (tokens) {
          const currentTokenUsage = sessionData?.tokenUsage || {
            inputTokens: 0,
            outputTokens: 0,
            totalTokens: 0
          };
          
          updateSession({
            tokenUsage: {
              inputTokens: currentTokenUsage.inputTokens + tokens.input_tokens,
              outputTokens: currentTokenUsage.outputTokens + tokens.output_tokens,
              totalTokens: currentTokenUsage.totalTokens + tokens.total_tokens
            }
          });
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'system',
        content: `ข้อผิดพลาด เกิดข้อผิดพลาด: ${error.message}`,
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ============ AUTO-SEND MESSAGE AFTER TRANSCRIPTION ============
  const autoSendTranscribedMessage = async (transcribedText) => {
    if (!transcribedText.trim() || !sessionData?.sessionId) return;

    addMessage({
      role: 'user',
      content: transcribedText,
      timestamp: Date.now()
    });

    setIsLoading(true);

    try {
      const response = ttsEnabled 
        ? await apiService.sendMessageWithTTS(sessionData.sessionId, transcribedText, true, ttsVoice, 1.0)
        : await apiService.sendMessage(sessionData.sessionId, transcribedText);
      
      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.data.response,
          timestamp: Date.now()
        });

        if (ttsEnabled && response.data.audio && response.data.audio.audio_base64) {
          console.log('🎵 Playing TTS audio response...');
          playAudio(response.data.audio.audio_base64);
        }

        const tokens = response.data.token_usage;
        if (tokens) {
          const currentTokenUsage = sessionData?.tokenUsage || {
            inputTokens: 0,
            outputTokens: 0,
            totalTokens: 0
          };
          
          updateSession({
            tokenUsage: {
              inputTokens: currentTokenUsage.inputTokens + tokens.input_tokens,
              outputTokens: currentTokenUsage.outputTokens + tokens.output_tokens,
              totalTokens: currentTokenUsage.totalTokens + tokens.total_tokens
            }
          });
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'system',
        content: `ข้อผิดพลาด เกิดข้อผิดพลาด: ${error.message}`,
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ============ AUDIO LEVEL DETECTION WITH NOISE CANCELLATION ============
  const detectAudioLevel = () => {
    if (!analyserRef.current) {
      console.log('⚠️ Analyser not available - cannot detect audio levels');
      return;
    }
    
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') {
      console.log('⚠️ MediaRecorder not recording - stopping detection');
      return;
    }

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    analyser.getByteFrequencyData(dataArray);
    
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;
    
    const NOISE_THRESHOLD = 8;
    const SPEECH_THRESHOLD = 16;
    
    setAudioLevel(average);
    
    const now = Date.now();
    if (!window.lastLogTime || now - window.lastLogTime > 500) {
      console.log('📊 Audio Level:', average.toFixed(2), 
                  '| Noise:', average > NOISE_THRESHOLD ? '✅' : '❌',
                  '| Speech:', average > SPEECH_THRESHOLD ? '✅' : '❌',
                  '| Has Speech:', hasSpeechDetectedRef.current);
      window.lastLogTime = now;
    }
    
    if (average > SPEECH_THRESHOLD) {
      lastSoundTimeRef.current = Date.now();
      
      if (!hasSpeechDetectedRef.current) {
        hasSpeechDetectedRef.current = true;
        setIsListeningForSilence(true);
        console.log('🎤 SPEECH DETECTED! Listening for silence...');
      }
    }
    
    const SILENCE_DURATION = 1250;
    const MIN_RECORDING_DURATION = 1000;
    
    const timeSinceLastSound = Date.now() - lastSoundTimeRef.current;
    const recordingDuration = Date.now() - (mediaRecorderRef.current?.startTime || Date.now());
    
    if (hasSpeechDetectedRef.current) {
      if (!window.lastTimingLog || now - window.lastTimingLog > 500) {
        console.log('⏱️ Time since last sound:', (timeSinceLastSound/1000).toFixed(1) + 's',
                    '| Recording duration:', (recordingDuration/1000).toFixed(1) + 's');
        window.lastTimingLog = now;
      }
    }
    
    if (hasSpeechDetectedRef.current && 
        timeSinceLastSound > SILENCE_DURATION && 
        recordingDuration > MIN_RECORDING_DURATION) {
      console.log('🔇 SILENCE DETECTED! Auto-stopping recording...');
      console.log('   - Time since last sound:', (timeSinceLastSound/1000).toFixed(1) + 's');
      console.log('   - Total recording time:', (recordingDuration/1000).toFixed(1) + 's');
      stopRecording();
      return;
    }
    
    animationFrameRef.current = requestAnimationFrame(detectAudioLevel);
  };

  // ============ START RECORDING WITH AUDIO ANALYSIS ============
  const startRecording = async () => {
    try {
      setSttError(null);
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setSttError('เบราว์เซอร์ของคุณไม่รองรับการบันทึกเสียง กรุณาใช้ Chrome, Firefox หรือ Edge');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          noiseSuppression: { ideal: true },
          echoCancellation: { ideal: true },
          autoGainControl: { ideal: true }
        } 
      });

      try {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContextRef.current.createMediaStreamSource(stream);
        analyserRef.current = audioContextRef.current.createAnalyser();
        
        analyserRef.current.fftSize = 2048;
        analyserRef.current.smoothingTimeConstant = 0.8;
        
        source.connect(analyserRef.current);
        
        console.log('✅ Audio analyser initialized successfully');
        console.log('   - FFT Size:', analyserRef.current.fftSize);
        console.log('   - Frequency Bin Count:', analyserRef.current.frequencyBinCount);
      } catch (error) {
        console.error('❌ Failed to initialize audio analyser:', error);
      }

      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4'
      ];
      
      let selectedMimeType = '';
      for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          selectedMimeType = type;
          break;
        }
      }

      if (!selectedMimeType) {
        throw new Error('ไม่พบรูปแบบการบันทึกเสียงที่รองรับ');
      }

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: selectedMimeType,
        audioBitsPerSecond: 128000
      });

      mediaRecorderRef.current.startTime = Date.now();

      audioChunksRef.current = [];
      hasSpeechDetectedRef.current = false;
      lastSoundTimeRef.current = Date.now();

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        
        setAudioLevel(0);
        setIsListeningForSilence(false);
        
        await processRecording(); 
      };

      mediaRecorderRef.current.start(100);
      setIsRecording(true);
      
      console.log('🎤 Recording started with noise cancellation enabled');
      console.log('📊 Thresholds: Noise=8, Speech=16, Silence=1.25s');
      console.log('🔍 Analyser available:', !!analyserRef.current);

      setTimeout(() => {
        console.log('🎯 Starting audio level detection...');
        console.log('   - isRecording:', isRecording);
        console.log('   - analyserRef.current:', !!analyserRef.current);
        detectAudioLevel();
      }, 100);

      silenceTimeoutRef.current = setTimeout(() => {
        console.log('⏰ Auto-stopping recording after 60 seconds');
        stopRecording();
      }, 60000);
      
    } catch (error) {
      console.error('🚨 Microphone access error:', error);
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setSttError('ไม่ได้รับอนุญาตให้ใช้ไมโครโฟน กรุณาอนุญาตการเข้าถึงไมโครโฟนในการตั้งค่าเบราว์เซอร์');
      } else if (error.name === 'NotFoundError') {
        setSttError('ไม่พบไมโครโฟน กรุณาเชื่อมต่อไมโครโฟนกับอุปกรณ์ของคุณ');
      } else if (error.name === 'NotReadableError') {
        setSttError('ไม่สามารถเข้าถึงไมโครโฟนได้ อาจมีแอปพลิเคชันอื่นกำลังใช้งานอยู่');
      } else {
        setSttError('เกิดข้อผิดพลาดในการเข้าถึงไมโครโฟน: ' + error.message);
      }
    }
  };
  
  const stopRecording = () => {
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('🛑 Recording stopped');
    }
  };

  // In ChatInterface.js - Update the processRecording function

  const processRecording = async () => {
    if (audioChunksRef.current.length === 0) {
      console.log('❌ No audio chunks recorded');
      setSttError('ไม่มีข้อมูลเสียงที่บันทึก กรุณาลองอีกครั้ง');
      return;
    }

    setIsProcessingAudio(true);
    setSttError(null);

    try {
      const audioBlob = new Blob(audioChunksRef.current, { 
        type: mediaRecorderRef.current.mimeType 
      });

      const fileSizeKB = (audioBlob.size / 1024).toFixed(2);
      console.log(`📊 Audio blob created: ${fileSizeKB} KB, type: ${audioBlob.type}`);

      if (audioBlob.size < 1000) {
        console.log('❌ Audio too small:', audioBlob.size, 'bytes');
        setSttError('เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง');
        setIsProcessingAudio(false);
        return;
      }

      console.log('📤 Sending audio to backend for transcription with AI correction...');
      
      const conversationContext = getConversationContext();
      console.log('🧠 Building conversation context for medical term correction');
      
      if (conversationContext) {
        console.log('   Context length:', conversationContext.length, 'characters');
        console.log('   Preview:', conversationContext.slice(0, 150) + '...');
      } else {
        console.log('   No context available (first message)');
      }
      
      const transcription = await apiService.transcribeAudio(audioBlob, conversationContext);

      console.log('📥 Transcription response:', transcription);

      if (transcription.success && transcription.data.text) {
        const transcribedText = transcription.data.text.trim();
        
        console.log('✅ Transcription successful:', transcribedText);
        
        if (transcription.data.original_text && 
            transcription.data.original_text !== transcribedText) {
          console.log('🔧 AI Correction applied:');
          console.log('   Original:', transcription.data.original_text);
          console.log('   Corrected:', transcribedText);
        }
        
        if (!transcribedText || transcribedText.length < 2) {
          console.log('❌ Transcribed text is empty or too short');
          setSttError('ไม่สามารถแปลงเสียงเป็นข้อความได้ กรุณาลองพูดชัดขึ้น');
          setIsProcessingAudio(false);
          return;
        }

        if (transcribedText) {
          console.log('🚀 Auto-sending transcribed message...');
          await autoSendTranscribedMessage(transcribedText);
          console.log('✅ Message auto-sent successfully!');
        } else {
          console.log('❌ Transcribed text is empty');
          setSttError('ไม่สามารถแปลงเสียงเป็นข้อความได้ กรุณาลองพูดชัดขึ้น');
        }
      } else {
        console.log('❌ Transcription failed:', transcription.error);
        throw new Error(transcription.error || 'Transcription failed');
      }

    } catch (error) {
      console.error('🚨 Transcription error:', error);
      
      // 🎯 NEW: Better error message handling
      let userFriendlyMessage = 'เกิดข้อผิดพลาดในการแปลงเสียง กรุณาลองอีกครั้ง';
      
      // Check for specific error types from backend
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        
        // Handle structured error responses
        if (errorData.detail) {
          if (typeof errorData.detail === 'object') {
            // Structured error with custom message
            if (errorData.detail.error === 'silent_audio') {
              userFriendlyMessage = 'ไม่พบเสียงพูดในการบันทึก กรุณาตรวจสอบไมโครโฟนและพูดให้ชัดเจน';
            } else if (errorData.detail.error === 'audio_too_short') {
              userFriendlyMessage = 'เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง';
            } else if (errorData.detail.message) {
              userFriendlyMessage = errorData.detail.message;
            }
          } else if (typeof errorData.detail === 'string') {
            // Simple string error
            userFriendlyMessage = errorData.detail;
          }
        }
      }
      
      // Check error message content
      if (error.message) {
        if (error.message.includes('timeout') || error.message.includes('หมดเวลา')) {
          userFriendlyMessage = 'หมดเวลาในการประมวลผลเสียง กรุณาลองอีกครั้ง';
        } else if (error.message.includes('network') || error.message.includes('Network error')) {
          userFriendlyMessage = 'เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย กรุณาตรวจสอบอินเทอร์เน็ต';
        } else if (error.message.includes('OpenAI API') || error.message.includes('API key')) {
          userFriendlyMessage = 'เกิดข้อผิดพลาดกับระบบ กรุณาติดต่อผู้ดูแล';
        } else if (error.message.includes('silent') || error.message.includes('ไม่พบเสียง')) {
          userFriendlyMessage = 'ไม่พบเสียงพูดในการบันทึก กรุณาพูดให้ชัดเจนและลองอีกครั้ง';
        } else if (error.message.includes('too short') || error.message.includes('สั้นเกินไป')) {
          userFriendlyMessage = 'เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง';
        } else if (error.message.includes('ไม่สามารถ') || error.message.includes('เกิดข้อผิดพลาด')) {
          // Already in Thai, use as-is
          userFriendlyMessage = error.message;
        }
      }
      
      setSttError(userFriendlyMessage);
    } finally {
      setIsProcessingAudio(false);
      audioChunksRef.current = [];
      console.log('🧹 Cleanup complete');
    }
  };

  // ============ TOGGLE RECORDING (SINGLE BUTTON) ============
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('th-TH', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="chat-interface">
      {sttError && (
        <div className="stt-error-banner">
          <div className="stt-error-content">
            <span className="stt-error-icon">⚠️</span>
            <span className="stt-error-text">{sttError}</span>
          </div>
          <button 
            className="stt-error-close"
            onClick={() => setSttError(null)}
            aria-label="ปิด"
          >
            ✕
          </button>
        </div>
      )}

      <div className="chat-header">
        <div className="chat-header-info">
          <div className="patient-avatar">👩‍⚕️</div>
          <div>
            <h3 className="chat-title">Virtual Patient</h3>
            <p className="chat-subtitle">
              {isPlayingAudio ? '🔊 Speaking...' : 
               isListeningForSilence ? '👂 Listening...' : 
               isRecording ? '🎤 Ready to listen' : 
               'Mother Simulator'}
            </p>
          </div>
        </div>
        <div className="header-stats">
          <div className="message-count">
            💬 {sessionData?.messages?.length || 0} messages
          </div>
        </div>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {!sessionData?.messages?.length ? (
          <div className="empty-chat">
            <div className="empty-icon">💬</div>
            <h3>Start the Conversation</h3>
            <p>Click the microphone to speak or type your message.</p>
            <p className="text-sm text-muted" style={{ marginTop: '0.5rem' }}>
              🧠 AI correction enabled for medical terminology
            </p>
          </div>
        ) : (
          sessionData.messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role === 'user' ? 'message-user' : 'message-assistant'} ${
                message.role === 'system' ? 'message-system' : ''
              }`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? '🧑‍⚕️' : message.role === 'system' ? '⚠️' : '👩‍⚕️'}
              </div>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.role === 'user' ? 'Doctor' : message.role === 'system' ? 'System' : 'Patient'}
                  </span>
                  <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
                <div className="message-text">{message.content}</div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-avatar">👩‍⚕️</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder={
            isRecording 
              ? isListeningForSilence 
                ? "🎤 กำลังฟัง... (พูดได้เลย)" 
                : "🎤 เริ่มพูดได้เลย..."
              : isProcessingAudio 
                ? "⚙️ กำลังประมวลผล..." 
                : "พิมพ์ข้อความหรือคลิกไมโครโฟนเพื่อพูด..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || isRecording || isProcessingAudio}
        />
        
        <button
          type="button"
          className={`btn chat-mic-btn ${ttsEnabled ? '' : 'btn-outline'}`}
          onClick={() => setTtsEnabled(!ttsEnabled)}
          disabled={isLoading || isRecording || isProcessingAudio}
          title={ttsEnabled ? 'ปิดเสียงตอบกลับ' : 'เปิดเสียงตอบกลับ'}
          style={{ 
            background: ttsEnabled ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' : undefined,
            height: '52px',
            minHeight: '52px'
          }}
        >
          {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </button>
        
        <button
          type="button"
          className={`btn chat-mic-btn ${isRecording ? 'recording' : ''} ${isListeningForSilence ? 'listening' : ''}`}
          onClick={toggleRecording}
          disabled={isLoading || isProcessingAudio}
          title={isRecording ? "หยุดบันทึก" : "เริ่มบันทึกเสียง"}
          style={{ 
            height: '52px',
            minHeight: '52px',
            boxShadow: isRecording && audioLevel > 30 
              ? `0 4px 25px rgba(239, 68, 68, ${0.3 + (audioLevel / 255) * 0.5})` 
              : undefined
          }}
        >
          {isProcessingAudio ? (
            <Loader size={20} className="spinning" />
          ) : isRecording ? (
            <>
              <Mic size={20} />
              <span style={{ marginLeft: '0.25rem', fontSize: '0.875rem' }}>
                {formatRecordingTime(recordingTime)}
              </span>
            </>
          ) : (
            <Mic size={20} />
          )}
        </button>

        <button
          type="submit"
          className="btn btn-primary chat-send-btn"
          disabled={!input.trim() || isLoading || isRecording || isProcessingAudio}
          style={{ 
            height: '52px',
            minHeight: '52px'
          }}
        >
          {isLoading ? <Loader size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;