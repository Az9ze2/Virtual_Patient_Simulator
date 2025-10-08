import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader } from 'lucide-react';
import axios from 'axios';
import './ChatInterface.css';

const ChatInterface = () => {
  const { sessionData, addMessage, updateSession } = useApp();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessionData?.messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    });

    setIsLoading(true);

    try {
      // Real API call
      const response = await axios.post('/api/chat', {
        sessionId: sessionData.sessionId,
        message: userMessage,
        caseData: sessionData.caseData
      });

      // Use backend response
      const assistantReply = response.data.reply || 'ขอโทษค่ะ ไม่พบข้อมูลตอบกลับ';

      addMessage({
        role: 'assistant',
        content: assistantReply,
        timestamp: Date.now()
      });

      // Update token usage (optional, depends on backend)
      updateSession({
        tokenUsage: {
          input: (sessionData.tokenUsage?.input || 0) + Math.floor(userMessage.length / 4),
          output: (sessionData.tokenUsage?.output || 0) + Math.floor(assistantReply.length / 4),
          total: (sessionData.tokenUsage?.total || 0) + Math.floor((userMessage.length + assistantReply.length) / 4)
        }
      });

    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'system',
        content: 'ขอโทษค่ะ เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่อีกครั้ง',
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockResponse = (userInput) => {
    const lowerInput = userInput.toLowerCase();
    
    if (lowerInput.includes('สวัสดี') || lowerInput.includes('hello')) {
      return 'สวัสดีค่ะ ดิฉันมีความยินดีที่จะให้ข้อมูลเกี่ยวกับลูกค่ะ';
    }
    
    if (lowerInput.includes('ชื่อ') || lowerInput.includes('name')) {
      return 'ลูกชื่อ ด.ช.ยินดี ปรีดา ค่ะ อายุ 5 วัน';
    }
    
    if (lowerInput.includes('อาการ') || lowerInput.includes('symptom')) {
      return 'ดิฉันมาเพราะมีปัญหาเรื่องการให้นมลูกค่ะ หัวนมข้างขวาแตก และเจ็บตอนให้นม';
    }
    
    if (lowerInput.includes('นม') || lowerInput.includes('feed') || lowerInput.includes('breast')) {
      return 'ดิฉันให้นมแม่อย่างเดียวค่ะ ทุก 3 ชั่วโมง ครั้งละประมาณ 15-20 นาที แต่ตอนนี้เจ็บหัวนมข้างขวามากเลยค่ะ';
    }
    
    if (lowerInput.includes('เมื่อไหร่') || lowerInput.includes('when')) {
      return 'เริ่มมีอาการตั้งแต่คลอดลูกได้ 2 วัน ค่ะ';
    }
    
    if (lowerInput.includes('คำถาม') || lowerInput.includes('question') || lowerInput.includes('ถาม')) {
      return 'ดิฉันอยากทราบว่าน้ำหนักลูกเป็นปกติหรือไม่คะ และต้องดูแลหัวนมที่แตกอย่างไร';
    }

    if (lowerInput.includes('นอน') || lowerInput.includes('sleep')) {
      return 'ลูกนอนหลับได้ดีค่ะ นานครั้งละ 3-4 ชั่วโมง มักจะตื่นเองตอนหิว ไม่ต้องปลุกค่ะ';
    }

    if (lowerInput.includes('ถ่าย') || lowerInput.includes('stool') || lowerInput.includes('diaper')) {
      return 'ถ่ายอุจจาระสีเหลืองทอง เนื้อนิ่ม วันละ 4-6 ครั้ง ปัสสาวะสีเหลืองใส วันละ 6-8 ครั้งค่ะ';
    }
    
    return 'ดิฉันเข้าใจค่ะ มีอะไรอยากทราบเพิ่มเติมไหมคะ';
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
        <div className="message-count">
          {sessionData?.messages?.length || 0} messages
        </div>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {!sessionData?.messages?.length ? (
          <div className="empty-chat">
            <div className="empty-icon">💬</div>
            <h3>Start the Conversation</h3>
            <p>Begin by greeting the patient and asking about their concerns.</p>
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
          type="text"
          className="chat-input"
          placeholder="Type your message to the patient..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
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
