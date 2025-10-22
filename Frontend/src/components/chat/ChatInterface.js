import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader, Mic, Square } from 'lucide-react';
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
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimeoutRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);

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

  // ============ AUTO-DISMISS ERROR AFTER 5 SECONDS ============
  useEffect(() => {
    if (sttError) {
      const timer = setTimeout(() => {
        setSttError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [sttError]);

  // ============ RECORDING TIMER ============
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
      const response = await apiService.sendMessage(sessionData.sessionId, userMessage);
      
      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.data.response,
          timestamp: Date.now()
        });

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

  // ============ START RECORDING FUNCTION ============
  const startRecording = async () => {
    try {
      // Clear previous error
      setSttError(null);
      
      // Check browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setSttError('เบราว์เซอร์ของคุณไม่รองรับการบันทึกเสียง กรุณาใช้ Chrome, Firefox หรือ Edge');
        return;
      }

      // Request microphone permission with optimized settings
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,           // Mono audio
          sampleRate: 16000,         // 16kHz (Whisper optimal)
          echoCancellation: true,    // Enable echo cancellation
          noiseSuppression: true,    // Enable noise suppression
          autoGainControl: true      // Enable auto gain
        } 
      });

      // Check supported MIME types in order of preference
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

      // Create MediaRecorder with selected MIME type
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: selectedMimeType,
        audioBitsPerSecond: 128000  // 128kbps
      });

      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Process the recorded audio
        await processRecording();
      };

      // Start recording (collect data every 100ms for smoother recording)
      mediaRecorderRef.current.start(100);
      setIsRecording(true);
      
      console.log('🎤 Recording started with MIME type:', selectedMimeType);

      // Auto-stop after 60 seconds to prevent excessively long recordings
      silenceTimeoutRef.current = setTimeout(() => {
        if (isRecording) {
          console.log('⏰ Auto-stopping recording after 60 seconds');
          stopRecording();
        }
      }, 60000);
      
    } catch (error) {
      console.error('🚨 Microphone access error:', error);
      
      // Provide user-friendly error messages in Thai
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
  
  // ============ STOP RECORDING FUNCTION ============
  const stopRecording = () => {
    // Clear timeout
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('🛑 Recording stopped');
    }
  };

  // ============ PROCESS RECORDED AUDIO ============
  const processRecording = async () => {
    if (audioChunksRef.current.length === 0) {
      setSttError('ไม่มีข้อมูลเสียงที่บันทึก กรุณาลองอีกครั้ง');
      return;
    }

    setIsProcessingAudio(true);
    setSttError(null);

    try {
      // Create audio blob from recorded chunks
      const audioBlob = new Blob(audioChunksRef.current, { 
        type: mediaRecorderRef.current.mimeType 
      });

      const fileSizeKB = (audioBlob.size / 1024).toFixed(2);
      console.log(`📊 Audio blob created: ${fileSizeKB} KB, type: ${audioBlob.type}`);

      // Validate minimum audio size (at least 1KB to ensure actual recording)
      if (audioBlob.size < 1000) {
        setSttError('เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง');
        setIsProcessingAudio(false);
        return;
      }

      // Send to backend for transcription via Whisper API
      console.log('🔄 Sending audio to backend for transcription...');
      const transcription = await apiService.transcribeAudio(audioBlob);

      if (transcription.success && transcription.data.text) {
        const transcribedText = transcription.data.text.trim();
        
        if (transcribedText) {
          // Set the transcribed text to input field
          setInput(transcribedText);
          console.log('✅ Transcription successful:', transcribedText);
          
          // Focus on input field so user can review before sending
          inputRef.current?.focus();
        } else {
          setSttError('ไม่สามารถแปลงเสียงเป็นข้อความได้ กรุณาลองพูดชัดขึ้น');
        }
      } else {
        throw new Error(transcription.error || 'Transcription failed');
      }

    } catch (error) {
      console.error('🚨 Transcription error:', error);
      
      // Thai error messages for different error types
      if (error.message.includes('timeout')) {
        setSttError('หมดเวลาในการประมวลผลเสียง กรุณาลองอีกครั้ง');
      } else if (error.message.includes('network')) {
        setSttError('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
      } else if (error.message.includes('OpenAI API')) {
        setSttError('เกิดข้อผิดพลาดกับ API กรุณาติดต่อผู้ดูแลระบบ');
      } else {
        setSttError('เกิดข้อผิดพลาดในการแปลงเสียง: ' + error.message);
      }
    } finally {
      setIsProcessingAudio(false);
      audioChunksRef.current = [];
    }
  };

  // ============ TOGGLE RECORDING ============
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
      {/* ============ STT ERROR NOTIFICATION ============ */}
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
            <p className="chat-subtitle">Mother Simulator</p>
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
            <p>Begin by greeting the patient or click the microphone to speak.</p>
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
              ? "🔴 กำลังบันทึกเสียง..." 
              : isProcessingAudio 
                ? "⚙️ กำลังประมวลผล..." 
                : "พิมพ์ข้อความหรือกดไมโครโฟนเพื่อพูด..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || isRecording || isProcessingAudio}
        />
        
        {/* ============ MIC BUTTON WITH RECORDING TIME ============ */}
        <button
          type="button"
          className={`btn chat-mic-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
          disabled={isLoading || isProcessingAudio}
          title={isRecording ? "หยุดบันทึก" : "เริ่มบันทึกเสียง"}
        >
          {isProcessingAudio ? (
            <Loader size={20} className="spinning" />
          ) : isRecording ? (
            <>
              <Square size={18} />
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
        >
          {isLoading ? <Loader size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;