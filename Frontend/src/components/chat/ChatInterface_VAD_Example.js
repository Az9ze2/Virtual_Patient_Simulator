// ChatInterface.js - Complete example with Voice Activity Detection

import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader, Mic, MicOff } from 'lucide-react';
import apiService from '../../services/apiService';
import { VoiceActivityDetector } from '../../utils/voiceActivityDetection';
import './ChatInterface.css';

const ChatInterface = () => {
  const { sessionData, addMessage, updateSession } = useApp();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [silenceDuration, setSilenceDuration] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);
  
  // Voice recording refs
  const vadRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

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

  // ============================================
  // VOICE RECORDING WITH AUTO-STOP
  // ============================================
  
  const startRecording = async () => {
    try {
      console.log('🎤 Starting voice recording...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000 // Optimal for Whisper
        } 
      });
      
      streamRef.current = stream;

      // Initialize Voice Activity Detector
      vadRef.current = new VoiceActivityDetector({
        silenceThreshold: 30,          // Volume threshold (0-100)
        silenceDuration: 1500,          // Auto-stop after 1.5s silence
        minRecordingTime: 500,          // Minimum 0.5s recording
        onVolumeChange: (volume) => {
          setVolumeLevel(volume);
        },
        onSilenceDetected: (duration) => {
          setSilenceDuration(duration);
        },
        onAutoStop: () => {
          console.log('🛑 Auto-stopped by Voice Activity Detection');
          stopRecording();
        }
      });

      await vadRef.current.start(stream);

      // Set up MediaRecorder for actual audio capture
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log('📼 Recording stopped, processing audio...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendToWhisper(audioBlob);
        
        // Cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      console.log('✅ Recording started with auto-stop enabled');
      
    } catch (error) {
      console.error('❌ Recording error:', error);
      alert('Could not access microphone. Please check permissions.');
      cleanupRecording();
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;
    
    console.log('🛑 Manually stopping recording...');
    
    // Stop VAD first
    if (vadRef.current) {
      vadRef.current.stop();
      vadRef.current = null;
    }
    
    // Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    setIsRecording(false);
    setVolumeLevel(0);
    setSilenceDuration(0);
  };

  const cleanupRecording = () => {
    if (vadRef.current) {
      vadRef.current.stop();
      vadRef.current = null;
    }
    
    if (mediaRecorderRef.current) {
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      mediaRecorderRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    setIsRecording(false);
    setVolumeLevel(0);
    setSilenceDuration(0);
    setIsProcessing(false);
  };

  const sendToWhisper = async (audioBlob) => {
    try {
      setIsProcessing(true);
      console.log('🔊 Sending audio to Whisper API...');
      console.log('📦 Audio blob size:', audioBlob.size, 'bytes');
      
      const formData = new FormData();
      
      // Determine file extension based on MIME type
      let filename = 'recording.webm';
      if (audioBlob.type.includes('mp4')) {
        filename = 'recording.mp4';
      } else if (audioBlob.type.includes('ogg')) {
        filename = 'recording.ogg';
      } else if (audioBlob.type.includes('wav')) {
        filename = 'recording.wav';
      }
      
      formData.append('audio', audioBlob, filename);
      
      // ✅ Use the backend API endpoint (not OpenAI directly)
      const response = await apiService.transcribeAudio(audioBlob);
      
      if (response.success && response.data.text) {
        const transcribedText = response.data.text.trim();
        console.log('✅ Transcription received:', transcribedText);
        
        if (transcribedText) {
          setInput(transcribedText);
          // Optionally auto-send the message after transcription
          // Uncomment the line below to enable auto-send:
          // await handleSendMessage({ preventDefault: () => {} });
        } else {
          console.warn('⚠️ Empty transcription received');
        }
      } else {
        throw new Error(response.error || 'Transcription failed');
      }
      
    } catch (error) {
      console.error('❌ Transcription error:', error);
      
      // Better error messages
      if (error.message.includes('timeout')) {
        alert('หมดเวลาในการประมวลผลเสียง กรุณาลองอีกครั้ง');
      } else if (error.message.includes('network')) {
        alert('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย');
      } else {
        alert('Speech recognition failed. Please try again or type your message.');
      }
    } finally {
      setIsProcessing(false);
      cleanupRecording();
    }
  };

  // ============================================
  // MESSAGE SENDING
  // ============================================

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
        content: `ข้อผิดพลาด: ${error.message}`,
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('th-TH', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupRecording();
    };
  }, []);

  return (
    <div className="chat-interface">
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
            <p>Begin by greeting the patient or use voice recording.</p>
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

      {/* Voice Activity Indicator */}
      {isRecording && (
        <div className="voice-indicator">
          <div className="volume-bar">
            <div 
              className="volume-fill" 
              style={{ 
                width: `${volumeLevel}%`,
                background: volumeLevel > 30 ? '#10b981' : '#94a3b8'
              }} 
            />
          </div>
          <span className="volume-text">{Math.round(volumeLevel)}%</span>
          
          {silenceDuration > 0 && (
            <div className="silence-indicator">
              Silence: {(silenceDuration / 1000).toFixed(1)}s
            </div>
          )}
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder={isRecording ? "Recording..." : "Type your message or use voice..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || isRecording || isProcessing}
        />
        
        {/* Voice Recording Button */}
        <button
          type="button"
          className={`btn chat-mic-btn ${isRecording ? 'recording' : ''} ${volumeLevel > 30 ? 'listening' : ''}`}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading || isProcessing}
          title={isRecording ? 'Stop recording (auto-stops after silence)' : 'Start voice recording'}
        >
          {isProcessing ? (
            <Loader size={20} className="spinning" />
          ) : isRecording ? (
            <MicOff size={20} />
          ) : (
            <Mic size={20} />
          )}
        </button>
        
        <button
          type="submit"
          className="btn btn-primary chat-send-btn"
          disabled={!input.trim() || isLoading || isRecording || isProcessing}
        >
          {isLoading ? <Loader size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
