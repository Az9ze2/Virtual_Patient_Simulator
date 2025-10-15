import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, Play, Download, Clock, MessageSquare, Cpu, CheckCircle } from 'lucide-react';
import './SummaryPage.css';

const SummaryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionData, diagnosis, treatmentPlan } = location.state || {};

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
  const duration = sessionData.duration || (sessionData.endTime - sessionData.startTime);
  const durationHours = Math.floor(duration / 3600000);
  const durationMinutes = Math.floor(duration / 60000) % 60;
  const durationSeconds = Math.floor((duration % 60000) / 1000);
  
  // Handle messages - check different possible structures
  const messages = sessionData.messages || sessionData.chat_history || [];
  const messageCount = messages.length || 0;
  const studentMessages = messages.filter(m => m.role === 'user' || m.type === 'user').length || 0;
  const patientMessages = messages.filter(m => m.role === 'assistant' || m.role === 'bot' || m.type === 'bot').length || 0;

  // Extract token usage - accumulated from all messages
  const tokenUsage = sessionData.tokenUsage || {
    inputTokens: 0,
    outputTokens: 0,
    totalTokens: 0
  };

  const handleDownload = () => {
    const report = {
      sessionInfo: {
        studentName: userName,
        studentId: userStudentId,
        caseTitle: caseTitle,
        date: new Date(sessionData.startTime).toLocaleString('th-TH'),
        duration: `${durationMinutes}m ${durationSeconds}s`
      },
      metrics: {
        totalMessages: messageCount,
        studentMessages,
        patientMessages,
        tokenUsage: {
          inputTokens: tokenUsage.inputTokens,
          outputTokens: tokenUsage.outputTokens,
          totalTokens: tokenUsage.totalTokens
        }
      },
      conversation: messages,
      diagnosis: {
        diagnosis,
        treatmentPlan
      }
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `session-${userStudentId}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
                  {new Date(sessionData.startTime).toLocaleDateString('th-TH')}
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
                <div className="metric-value">{tokenUsage.totalTokens}</div>
                <div className="metric-detail">
                  Input: {tokenUsage.inputTokens} | Output: {tokenUsage.outputTokens}
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
              {messages && messages.slice(0, 5).map((msg, idx) => {
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
              Download Report
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