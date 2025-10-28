import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import ChatInterface from '../components/chat/ChatInterface';
import PatientInfo from '../components/chat/PatientInfo';
import DiagnosisSection from '../components/chat/DiagnosisSection';
import SessionTimer from '../components/chat/SessionTimer';
import { ArrowLeft, StopCircle, AlertTriangle, Video } from 'lucide-react';
import apiService from '../services/apiService';
import './ChatbotPage.css';

const ChatbotPage = () => {
  const navigate = useNavigate();
  const { sessionData, endSession, settings, isRecording, stopRecording, recordingBlob } = useApp();
  const [showEndConfirm, setShowEndConfirm] = useState(false);
  const [diagnosis, setDiagnosis] = useState('');
  const [treatmentPlan, setTreatmentPlan] = useState('');
  
  // ============ NEW: State for box expansion ============
  const [isPatientInfoExpanded, setIsPatientInfoExpanded] = useState(false);
  
  // ============ MAGIC BENTO SPOTLIGHT EFFECT ============
  const chatCardRef = useRef(null);
  const infoCardRef = useRef(null);
  const diagnosisCardRef = useRef(null);

  useEffect(() => {
    // Redirect if no active session
    if (!sessionData) {
      navigate('/');
    }
  }, [sessionData, navigate]);

  // ============ MOUSE MOVE HANDLER FOR SPOTLIGHT ============
  const handleMouseMove = (e, ref) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    ref.current.style.setProperty('--mouse-x', `${x}px`);
    ref.current.style.setProperty('--mouse-y', `${y}px`);
  };

  const handleGoBack = () => {
    if (window.confirm('Are you sure you want to leave? Your progress will be saved.')) {
      navigate('/');
    }
  };

  const handleEndSession = () => {
    setShowEndConfirm(true);
  };

  const confirmEndSession = async () => {
    try {
      // First, save diagnosis and treatment to backend if they exist
      if (diagnosis || treatmentPlan) {
        console.log('📁 Saving diagnosis and treatment to backend before ending session...');
        try {
          await apiService.updateDiagnosis(sessionData.sessionId, {
            diagnosis: diagnosis || '',
            treatment_plan: treatmentPlan || '',
            notes: ''
          });
          console.log('✅ Diagnosis and treatment saved successfully');
        } catch (diagnosisError) {
          console.error('⚠️ Failed to save diagnosis/treatment:', diagnosisError);
          // Continue with session end even if diagnosis save fails
        }
      }
      
      // Stop recording if active
      if (isRecording) {
        console.log('📹 Stopping video recording...');
        stopRecording();
        
        // Wait a bit for the recording to finalize
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Then end the session
      const completedSession = await endSession();
      navigate('/summary', { state: { sessionData: completedSession, diagnosis, treatmentPlan } });
    } catch (error) {
      console.error('Failed to end session:', error);
      // Navigate anyway with current session data as fallback
      navigate('/summary', { state: { sessionData: sessionData, diagnosis, treatmentPlan } });
    }
  };

  if (!sessionData) {
    return null;
  }

  return (
    <div className="chatbot-page">
      {/* Header */}
      <header className="chatbot-header">
        <div className="header-left">
          <button className="btn btn-outline btn-icon" onClick={handleGoBack}>
            <ArrowLeft size={20} />
            Go Back
          </button>
          <div className="session-info">
            <h2 className="session-title">Virtual Patient Session</h2>
            <p className="session-meta">
              {sessionData.caseData?.title || 'Active Session'}
            </p>
          </div>
        </div>
        <div className="header-right">
          {isRecording && (
            <div className="recording-indicator">
              <div className="recording-dot"></div>
              <span>Recording</span>
            </div>
          )}
          {settings.showTimer && <SessionTimer startTime={sessionData.startTime} />}
          <button className="btn btn-danger btn-icon" onClick={handleEndSession}>
            <StopCircle size={20} />
            End Session
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="chatbot-content">
        <div className="content-grid">
          {/* ============ Left - Chat Interface with Magic Bento ============ */}
          <div className="chat-column">
            <div 
              ref={chatCardRef}
              className="magic-bento-card"
              onMouseMove={(e) => handleMouseMove(e, chatCardRef)}
            >
              <ChatInterface />
            </div>
          </div>

          {/* ============ Right - Patient Info & Diagnosis with Magic Bento ============ */}
          <div className="info-column">
            <div 
              ref={infoCardRef}
              className={`magic-bento-card ${isPatientInfoExpanded ? 'expanded' : ''}`}
              onMouseMove={(e) => handleMouseMove(e, infoCardRef)}
            >
              <PatientInfo 
                caseData={sessionData.caseData}
                onExpand={setIsPatientInfoExpanded}
              />
            </div>
            
            <div 
              ref={diagnosisCardRef}
              className={`magic-bento-card ${isPatientInfoExpanded ? 'shrunk' : ''}`}
              onMouseMove={(e) => handleMouseMove(e, diagnosisCardRef)}
            >
              <DiagnosisSection 
                diagnosis={diagnosis}
                setDiagnosis={setDiagnosis}
                treatmentPlan={treatmentPlan}
                setTreatmentPlan={setTreatmentPlan}
              />
            </div>
          </div>
        </div>
      </div>

      {/* End Session Confirmation Modal */}
      {showEndConfirm && (
        <div className="modal-overlay" onClick={() => setShowEndConfirm(false)}>
          <div className="modal confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <div className="warning-icon">
                  <AlertTriangle size={24} />
                </div>
                <h2 className="modal-title">End Session?</h2>
              </div>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to end this session?</p>
              <p className="text-muted">
                Your conversation and diagnosis will be saved, and you'll be taken to the summary page.
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setShowEndConfirm(false)}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={confirmEndSession}>
                Yes, End Session
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotPage;