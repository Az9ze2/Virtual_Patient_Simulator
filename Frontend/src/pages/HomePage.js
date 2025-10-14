import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import StartSessionModal from '../components/modals/StartSessionModal';
import UploadDocumentModal from '../components/modals/UploadDocumentModal';
import SettingsModal from '../components/modals/SettingsModal';
import { Activity, Upload, Settings, Clock, Users, TrendingUp } from 'lucide-react';
import './HomePage.css';

// ============ NEW: COUNTUP ANIMATION COMPONENT ============
const CountUp = ({ end, duration = 2000, suffix = '' }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      const percentage = Math.min(progress / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - percentage, 4);
      setCount(Math.floor(easeOutQuart * end));

      if (percentage < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [end, duration]);

  return <>{count}{suffix}</>;
};

const HomePage = () => {
  const navigate = useNavigate();
  const { sessionData, theme } = useApp();
  const [showStartModal, setShowStartModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  
  // ============ TYPEWRITER EFFECT STATE ============
  // const [displayedTitle, setDisplayedTitle] = useState('');
  // const [titleComplete, setTitleComplete] = useState(false);
  // const fullTitle = 'Thai Language-Based Virtual Patient Simulator';

  // const [displayedTitle1, setDisplayedTitle1] = useState('');
  // const [titleComplete1, setTitleComplete1] = useState(false);
  // const fullthTitle = 'ระบบจำลองผู้ป่วยด้วยโมเดลภาษาไทย';

  // Mock statistics
  const stats = {
    recentSessions: 5,
    avgTime: 12,
    totalCases: 14
  };

  // ============ TYPEWRITER ANIMATION EFFECT ============
  // useEffect(() => {
  //   let currentIndex = 0;
  //   const typingSpeed = 50; // milliseconds per character

  //   const typingInterval = setInterval(() => {
  //     if (currentIndex <= fullTitle.length) {
  //       setDisplayedTitle(fullTitle.slice(0, currentIndex));
  //       currentIndex++;
  //     } else {
  //       setTitleComplete(true);
  //       clearInterval(typingInterval);
  //     }
  //   }, typingSpeed);

  //   return () => clearInterval(typingInterval);
  // }, []);

  // useEffect(() => {
  //   let currentIndex = 0;
  //   const typingSpeed = 80; // milliseconds per character

  //   const typingInterval = setInterval(() => {
  //     if (currentIndex <= fullthTitle.length) {
  //       setDisplayedTitle1(fullthTitle.slice(0, currentIndex));
  //       currentIndex++;
  //     } else {
  //       setTitleComplete1(true);
  //       clearInterval(typingInterval);
  //     }
  //   }, typingSpeed);

  //   return () => clearInterval(typingInterval);
  // }, []);

  
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
                {/* ============ TYPEWRITER TITLE ============ */}
                <h1 className="main-title">
                  Thai Language-Based Virtual Patient Simulator
                </h1>
                <h2 className="thai-title">
                  ระบบจำลองผู้ป่วยด้วยโมเดลภาษาไทย
                </h2>
                <p className="subtitle">
                  Practice clinical interviewing with AI-powered virtual patients
                </p>
              </div>
            </div>
          </header>

          {/* Main Action Cards */}
          <div className="action-cards">
            {/* ============ CARDS WITH STAGGER ANIMATION ============ */}
            <div 
              className="action-card primary-card fade-in"
              style={{ animationDelay: '0.2s' }}
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
              style={{ animationDelay: '0.4s' }}
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
              style={{ animationDelay: '0.6s' }}
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

          {/* ============ UPDATED: Statistics Section with CountUp ============ */}
          <div className="stats-section fade-in" style={{ animationDelay: '0.8s' }}>
            <div className="stat-card">
              <div className="stat-icon">
                <Users size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">
                  <CountUp end={stats.recentSessions} duration={2000} />
                </div>
                <div className="stat-label">Recent Sessions</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Clock size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">
                  <CountUp end={stats.avgTime} duration={2000} suffix=" min" />
                </div>
                <div className="stat-label">Average Duration</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <TrendingUp size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">
                  <CountUp end={stats.totalCases} duration={2000} />
                </div>
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