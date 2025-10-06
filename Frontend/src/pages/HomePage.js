import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import StartSessionModal from '../components/modals/StartSessionModal';
import UploadDocumentModal from '../components/modals/UploadDocumentModal';
import SettingsModal from '../components/modals/SettingsModal';
import { Activity, Upload, Settings, Clock, Users, TrendingUp } from 'lucide-react';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();
  const { sessionData, theme } = useApp();
  const [showStartModal, setShowStartModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Mock statistics
  const stats = {
    recentSessions: 5,
    avgTime: 12,
    totalCases: 14
  };

  const handleStartSession = (sessionInfo) => {
    setShowStartModal(false);
    navigate('/chatbot');
  };

  const handleUploadComplete = (caseData) => {
    setShowUploadModal(false);
    navigate('/chatbot');
  };

  return (
    <div className="home-page">
      <div className="container">
        <div className="home-content">
          {/* Header */}
          <header className="home-header fade-in">
            <div className="logo-section">
              <div className="logo-icon">
                <Activity size={48} strokeWidth={2.5} />
              </div>
              <div className="title-section">
                <h1 className="main-title">
                  Thai Language-Based Virtual Patient Simulator
                </h1>
                <h2 className="thai-title">
                  ระบบจำลองผู้ป่วยด้วยโมเดลภาษา
                </h2>
                <p className="subtitle">
                  Practice clinical interviewing with AI-powered virtual patients
                </p>
              </div>
            </div>
          </header>

          {/* Main Action Cards */}
          <div className="action-cards">
            <div 
              className="action-card primary-card fade-in"
              style={{ animationDelay: '0.1s' }}
              onClick={() => setShowStartModal(true)}
            >
              <div className="card-icon">
                <Activity size={32} />
              </div>
              <h3 className="card-title">Start Interview Session</h3>
              <p className="card-description">
                Begin your practice with pre-loaded patient cases
              </p>
              <div className="card-footer">
                <span className="card-badge">{stats.totalCases} Cases Available</span>
              </div>
            </div>

            <div 
              className="action-card secondary-card fade-in"
              style={{ animationDelay: '0.2s' }}
              onClick={() => setShowUploadModal(true)}
            >
              <div className="card-icon">
                <Upload size={32} />
              </div>
              <h3 className="card-title">Upload Document</h3>
              <p className="card-description">
                Add custom patient case from your documents
              </p>
              <div className="card-footer">
                <span className="card-badge">DOCX, PDF Supported</span>
              </div>
            </div>

            <div 
              className="action-card tertiary-card fade-in"
              style={{ animationDelay: '0.3s' }}
              onClick={() => setShowSettingsModal(true)}
            >
              <div className="card-icon">
                <Settings size={32} />
              </div>
              <h3 className="card-title">Settings</h3>
              <p className="card-description">
                Configure AI model and interface preferences
              </p>
              <div className="card-footer">
                <span className="card-badge">Customize Experience</span>
              </div>
            </div>
          </div>

          {/* Statistics Section */}
          <div className="stats-section fade-in" style={{ animationDelay: '0.4s' }}>
            <div className="stat-card">
              <div className="stat-icon">
                <Users size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats.recentSessions}</div>
                <div className="stat-label">Recent Sessions</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Clock size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats.avgTime} min</div>
                <div className="stat-label">Average Duration</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <TrendingUp size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats.totalCases}</div>
                <div className="stat-label">Total Cases</div>
              </div>
            </div>
          </div>

          {/* Resume Session Banner */}
          {sessionData && (
            <div className="resume-banner fade-in">
              <div className="resume-content">
                <Activity size={20} />
                <span>You have an active session in progress</span>
              </div>
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/chatbot')}
              >
                Resume Session
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showStartModal && (
        <StartSessionModal
          onClose={() => setShowStartModal(false)}
          onStart={handleStartSession}
        />
      )}

      {showUploadModal && (
        <UploadDocumentModal
          onClose={() => setShowUploadModal(false)}
          onComplete={handleUploadComplete}
        />
      )}

      {showSettingsModal && (
        <SettingsModal
          onClose={() => setShowSettingsModal(false)}
        />
      )}
    </div>
  );
};

export default HomePage;
