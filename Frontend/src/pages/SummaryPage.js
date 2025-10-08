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

  const duration = sessionData.duration || (sessionData.endTime - sessionData.startTime);
  const durationHours = Math.floor(duration / 3600000);
  const durationMinutes = Math.floor(duration / 60000) % 60000;
  const durationSeconds = Math.floor((duration % 60000) / 1000);
  const messageCount = sessionData.messages?.length || 0;
  const studentMessages = sessionData.messages?.filter(m => m.role === 'user').length || 0;
  const patientMessages = sessionData.messages?.filter(m => m.role === 'assistant').length || 0;

  const handleDownload = () => {
    const report = {
      sessionInfo: {
        studentName: sessionData.studentName,
        studentId: sessionData.studentId,
        caseTitle: sessionData.caseData?.title,
        date: new Date(sessionData.startTime).toLocaleString('th-TH'),
        duration: `${durationMinutes}m ${durationSeconds}s`
      },
      metrics: {
        totalMessages: messageCount,
        studentMessages,
        patientMessages,
        tokenUsage: sessionData.tokenUsage
      },
      conversation: sessionData.messages,
      diagnosis: {
        diagnosis,
        treatmentPlan
      }
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `session-${sessionData.studentId}-${Date.now()}.json`;
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
              Great work, {sessionData.studentName}. Here's your session summary.
            </p>
          </div>

          {/* Session Info */}
          <div className="info-card fade-in" style={{ animationDelay: '0.1s' }}>
            <h3 className="card-section-title">Session Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Student Name</span>
                <span className="info-value">{sessionData.studentName}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Student ID</span>
                <span className="info-value">{sessionData.studentId}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Case</span>
                <span className="info-value">{sessionData.caseData?.title || 'N/A'}</span>
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
                <div className="metric-value">{sessionData.tokenUsage?.total || 0}</div>
                <div className="metric-detail">
                  Input: {sessionData.tokenUsage?.input || 0} | Output: {sessionData.tokenUsage?.output || 0}
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
              {sessionData.messages && sessionData.messages.slice(0, 5).map((msg, idx) => (
                <div key={idx} className={`preview-message ${msg.role}`}>
                  <span className="preview-role">
                    {msg.role === 'user' ? '🧑‍⚕️ Doctor' : '👩‍⚕️ Patient'}:
                  </span>
                  <span className="preview-text">{msg.content}</span>
                </div>
              ))}
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
            {/* <button className="btn btn-outline btn-large" onClick={() => navigate('/')}>
              <Play size={20} />
              Start New Session
            </button> */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryPage;
