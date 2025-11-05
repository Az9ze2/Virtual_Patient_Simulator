import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, Download, Clock, MessageSquare, FileText, Calendar, Activity, CheckCircle, XCircle, Loader } from 'lucide-react';
import apiService from '../services/apiService';
import './MySessionsPage.css';

const MySessionsPage = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userData, setUserData] = useState(null);

  useEffect(() => {
    // Get user data from localStorage
    const storedUser = localStorage.getItem('adminUser');
    if (!storedUser) {
      navigate('/');
      return;
    }

    try {
      const user = JSON.parse(storedUser);
      setUserData(user);
      loadSessions(user.adminId);
    } catch (e) {
      console.error('Failed to parse user data:', e);
      navigate('/');
    }
  }, [navigate]);

  const loadSessions = async (studentId) => {
    try {
      setLoading(true);
      const response = await apiService.getUserSessions(studentId);
      if (response.success) {
        setSessions(response.data.sessions || []);
        setError(null);
      } else {
        console.error('Failed to load sessions:', response);
        setError('network');
      }
    } catch (err) {
      console.error('Error loading sessions:', err);
      // Check if it's a network error
      if (!err.response && (err.message.includes('fetch') || err.message.includes('network'))) {
        setError('network');
      } else {
        setError('network');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (sessionId) => {
    try {
      await apiService.downloadReport(sessionId);
    } catch (error) {
      alert('Download failed: ' + error.message);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <CheckCircle size={20} className="status-icon complete" />;
      case 'active':
        return <Activity size={20} className="status-icon active" />;
      default:
        return <XCircle size={20} className="status-icon ended" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'complete':
        return 'status-complete';
      case 'active':
        return 'status-active';
      default:
        return 'status-ended';
    }
  };

  return (
    <div className="my-sessions-page">
      <div className="sessions-header">
        <div className="header-content">
          <button className="back-btn" onClick={() => navigate('/')}>
            <Home size={20} />
            <span>Back to Home</span>
          </button>
          <div className="header-title">
            <h1>My Sessions</h1>
            <p>{userData?.name}'s Session History</p>
          </div>
        </div>
      </div>

      <div className="sessions-container">
        {loading ? (
          <div className="loading-state">
            <Loader className="spinning" size={48} />
            <p>Loading your sessions...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <XCircle size={48} />
            <h2>Unable to Load Sessions</h2>
            <p>Please check your internet connection and try again.</p>
            <button className="btn-primary" onClick={() => loadSessions(userData?.adminId)}>
              Retry
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="empty-state">
            <FileText size={64} />
            <h2>No Sessions Found</h2>
            <p>You haven't started any interview sessions yet.</p>
          </div>
        ) : (
          <>
            <div className="sessions-summary">
              <div className="summary-card">
                <span className="summary-emoji">📊</span>
                <div className="summary-content">
                  <span className="summary-value">{sessions.length}</span>
                  <span className="summary-label">Total Sessions</span>
                </div>
              </div>
              <div className="summary-card">
                <span className="summary-emoji">✅</span>
                <div className="summary-content">
                  <span className="summary-value">
                    {sessions.filter(s => s.status === 'complete').length}
                  </span>
                  <span className="summary-label">Completed Sessions</span>
                </div>
              </div>
              <div className="summary-card">
                <span className="summary-emoji">⏱️</span>
                <div className="summary-content">
                  <span className="summary-value">
                    {sessions.length > 0 && sessions.reduce((acc, s) => acc + (s.duration_seconds || 0), 0) > 0
                      ? Math.round(sessions.reduce((acc, s) => acc + (s.duration_seconds || 0), 0) / sessions.length / 60)
                      : 0}
                  </span>
                  <span className="summary-label">Average Duration (min)</span>
                </div>
              </div>
            </div>

            <div className="sessions-grid">
              {sessions.map((session) => (
                <div key={session.session_id} className="session-card">
                  <div className="session-header">
                    <div className="session-title">
                      <FileText size={20} />
                      <h3>{session.case_title || 'Untitled Case'}</h3>
                    </div>
                    <div className={`session-status ${getStatusColor(session.status)}`}>
                      {getStatusIcon(session.status)}
                      <span>{session.status}</span>
                    </div>
                  </div>

                  <div className="session-details">
                    <div className="detail-item">
                      <Calendar size={16} />
                      <span>{formatDate(session.started_at)}</span>
                    </div>
                    <div className="detail-item">
                      <Clock size={16} />
                      <span>{formatDuration(session.duration_seconds)}</span>
                    </div>
                    <div className="detail-item">
                      <MessageSquare size={16} />
                      <span>{session.message_count} messages</span>
                    </div>
                  </div>

                  {session.specialty && (
                    <div className="session-specialty">
                      <span className="specialty-badge">{session.specialty}</span>
                    </div>
                  )}

                  <div className="session-footer">
                    <span className="session-id">ID: {session.session_id.slice(0, 8)}...</span>
                    {session.has_report && (
                      <button
                        className="download-btn"
                        onClick={() => handleDownload(session.session_id)}
                      >
                        <Download size={16} />
                        <span>Download Report</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MySessionsPage;
