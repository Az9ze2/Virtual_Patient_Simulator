import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader } from 'lucide-react';
import apiService from '../../services/apiService';
import SpeechModule from './SpeechModule';
import './ChatInterface.css';
import './SpeechModule.css';

const ChatInterface = () => {
  const { sessionData, addMessage, updateSession } = useApp();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lastAssistantMessage, setLastAssistantMessage] = useState(null);
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
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading, sessionData?.messages]);

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
        const assistantResponse = response.data.response;
        
        addMessage({
          role: 'assistant',
          content: assistantResponse,
          timestamp: Date.now()
        });

        // Set last assistant message for text-to-speech
        setLastAssistantMessage(assistantResponse);

        const tokens = response.data.token_usage;
        if (tokens) {
          // Accumulate tokens for the entire session
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

  // Handle transcript from speech recognition
  const handleTranscript = (transcript) => {
    console.log('📝 Received transcript:', transcript);
    setInput(transcript);
    
    // Auto-send the transcribed message after a short delay
    setTimeout(() => {
      if (transcript.trim() && !isLoading && sessionData?.sessionId) {
        const userMessage = transcript.trim();
        
        addMessage({
          role: 'user',
          content: userMessage,
          timestamp: Date.now()
        });

        setIsLoading(true);
        setInput('');

        apiService.sendMessage(sessionData.sessionId, userMessage)
          .then(response => {
            if (response.success) {
              const assistantResponse = response.data.response;
              
              addMessage({
                role: 'assistant',
                content: assistantResponse,
                timestamp: Date.now()
              });

              // Set last assistant message for text-to-speech
              setLastAssistantMessage(assistantResponse);

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
          })
          .catch(error => {
            console.error('Error sending message:', error);
            addMessage({
              role: 'system',
              content: `ข้อผิดพลาด เกิดข้อผิดพลาด: ${error.message}`,
              timestamp: Date.now()
            });
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
    }, 100);
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
            <p>Begin by greeting the patient and asking about their concerns.</p>
            <p className="text-muted" style={{ marginTop: '0.5rem' }}>
              🎤 Click the microphone to speak or type your message
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
          placeholder="พิมพ์ข้อความหรือกดไมค์เพื่อพูด..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
        />
        
        {/* Speech Module - Microphone next to Send button */}
        <SpeechModule
          onTranscript={handleTranscript}
          autoSpeak={true}
          messageToSpeak={lastAssistantMessage}
        />
        
        <button
          type="submit"
          className="btn btn-primary chat-send-btn"
          disabled={!input.trim() || isLoading}
        >
          {isLoading ? <Loader size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;