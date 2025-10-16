import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, Play, Download, Clock, MessageSquare, Cpu, CheckCircle } from 'lucide-react';
import './SummaryPage.css';
import apiService from '../services/apiService';

const SummaryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionData, diagnosis, treatmentPlan } = location.state || {};

  const handleDownload = async () => {
    if (!sessionData?.sessionId) {
      alert('No session ID available for download.');
      return;
    }
    try {
      await apiService.downloadReport(sessionData.sessionId);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download report. Please try again.');
    }
  };

  if (!sessionData) {
    return (
      <div className="summary-page">
        <div className="container">
          <div className="error-state">
            <h2>No Session Data</h2>
            <p>Unable to load session summary.</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              <Home size={18} />
              Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract user info - handle both formats
  const userName = sessionData.userInfo?.name || sessionData.user_info?.name || 'N/A';
  const userStudentId = sessionData.userInfo?.student_id || sessionData.user_info?.student_id || 'N/A';
  const caseTitle = sessionData.caseInfo?.case_title || sessionData.case_info?.case_title || 'N/A';
  
  // Calculate duration
  const duration = sessionData.duration || (sessionData.endTime && sessionData.startTime ? sessionData.endTime - sessionData.startTime : 0);
  const safeDuration = isNaN(duration) ? 0 : duration;
  const durationHours = Math.floor(safeDuration / 3600000);
  const durationMinutes = Math.floor(safeDuration / 60000) % 60;
  const durationSeconds = Math.floor((safeDuration % 60000) / 1000);
  
  // Handle messages - check different possible structures
  const messages = sessionData.messages || sessionData.chat_history || [];
  const messageCount = Array.isArray(messages) ? messages.length : 0;
  const studentMessages = Array.isArray(messages) ? messages.filter(m => m.role === 'user' || m.type === 'user').length : 0;
  const patientMessages = Array.isArray(messages) ? messages.filter(m => m.role === 'assistant' || m.role === 'bot' || m.type === 'bot').length : 0;

  // Extract token usage - accumulated from all messages
  const tokenUsage = sessionData.tokenUsage || sessionData.token_usage || {};
  const safeTokenUsage = {
    inputTokens: Number(tokenUsage.inputTokens || tokenUsage.input_tokens || 0) || 0,
    outputTokens: Number(tokenUsage.outputTokens || tokenUsage.output_tokens || 0) || 0,
    totalTokens: Number(tokenUsage.totalTokens || tokenUsage.total_tokens || 0) || 0
  };


  return (
    <div className="summary-page">
      <div className="container">
        <div className="summary-content">
          {/* Header */}
          <div className="summary-header fade-in">
            <div className="success-icon">
              <CheckCircle size={48} />
            </div>
            <h1 className="summary-title">Session Complete!</h1>
            <p className="summary-subtitle">
              Great work, {userName}. Here's your session summary.
            </p>
          </div>

          {/* Session Info */}
          <div className="info-card fade-in" style={{ animationDelay: '0.1s' }}>
            <h3 className="card-section-title">Session Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Student Name</span>
                <span className="info-value">{userName}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Student ID</span>
                <span className="info-value">{userStudentId}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Case</span>
                <span className="info-value">{caseTitle}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Date</span>
                <span className="info-value">
                  {sessionData.startTime ? new Date(sessionData.startTime).toLocaleDateString('th-TH') : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="metrics-grid fade-in" style={{ animationDelay: '0.2s' }}>
            <div className="metric-card">
              <div className="metric-icon time">
                <Clock size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">Total Duration</div>
                <div className="metric-value">{durationHours}h {durationMinutes}m {durationSeconds}s</div>
                <div className="metric-detail">Active session time</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon messages">
                <MessageSquare size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">Total Messages</div>
                <div className="metric-value">{messageCount}</div>
                <div className="metric-detail">{studentMessages} from you, {patientMessages} from patient</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon tokens">
                <Cpu size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">Token Usage</div>
                <div className="metric-value">{safeTokenUsage.totalTokens}</div>
                <div className="metric-detail">
                  Input: {safeTokenUsage.inputTokens} | Output: {safeTokenUsage.outputTokens}
                </div>
              </div>
            </div>
          </div>

          {/* Diagnosis */}
          {(diagnosis || treatmentPlan) && (
            <div className="diagnosis-card fade-in" style={{ animationDelay: '0.3s' }}>
              <h3 className="card-section-title">Your Assessment</h3>
              
              {diagnosis && (
                <div className="assessment-section">
                  <h4 className="assessment-label">Diagnosis</h4>
                  <p className="assessment-text">{diagnosis}</p>
                </div>
              )}

              {treatmentPlan && (
                <div className="assessment-section">
                  <h4 className="assessment-label">Treatment Plan</h4>
                  <p className="assessment-text">{treatmentPlan}</p>
                </div>
              )}
            </div>
          )}

          {/* Conversation Preview */}
          <div className="conversation-card fade-in" style={{ animationDelay: '0.4s' }}>
            <h3 className="card-section-title">Conversation History</h3>
            <div className="conversation-preview">
              {Array.isArray(messages) && messages.length > 0 && messages.slice(0, 5).map((msg, idx) => {
                const isUser = msg.role === 'user' || msg.type === 'user';
                const content = msg.content || msg.user || msg.bot || 'No content';
                return (
                  <div key={idx} className={`preview-message ${isUser ? 'user' : 'assistant'}`}>
                    <span className="preview-role">
                      {isUser ? '🧑‍⚕️ Doctor' : '👩‍⚕️ Patient'}:
                    </span>
                    <span className="preview-text">{content}</span>
                  </div>
                );
              })}
              {messageCount > 5 && (
                <div className="preview-more">
                  +{messageCount - 5} more messages
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="action-buttons fade-in" style={{ animationDelay: '0.5s' }}>
            <button className="btn btn-primary btn-large" onClick={handleDownload}>
              <Download size={20} />
              Download PDF Report
            </button>
            <button className="btn btn-outline btn-large" onClick={() => navigate('/')}>
              <Home size={20} />
              Go Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryPage;