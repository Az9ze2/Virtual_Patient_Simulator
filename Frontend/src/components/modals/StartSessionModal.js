import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { X, User, CreditCard, ChevronRight, FileText, Loader, Video } from 'lucide-react';
import apiService from '../../services/apiService';
import './Modal.css';


const StartSessionModal = ({ onClose, onStart, userData }) => {
  const { startSession, settings, startRecording } = useApp();
  // If userData is provided, skip to step 2 (case selection)
  const [step, setStep] = useState(userData ? 2 : 1);
  const [formData, setFormData] = useState({
    name: userData?.name || '',
    studentId: userData?.adminId || '',
    email: userData?.email || '',
    selectedCase: null
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [cases, setCases] = useState([]);
  const [loadingCases, setLoadingCases] = useState(false);
  const [showRecordingConsent, setShowRecordingConsent] = useState(false);
  const [recordingError, setRecordingError] = useState('');
  
  // Refs and state for gradient overlay
  const caseListRef = useRef(null);
  const cardRefs = useRef([]);
  const [showTopGradient, setShowTopGradient] = useState(false);
  const [showBottomGradient, setShowBottomGradient] = useState(true);
  const [visibleCards, setVisibleCards] = useState(new Set());

  // Load cases when modal opens
  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setLoadingCases(true);
      console.log('📋 Loading cases...');
      const response = await apiService.getCases();
      console.log('📋 Cases response:', response);
      if (response.success) {
        // Transform backend cases to frontend format
        const transformedCases = response.data.cases.map(caseItem => ({
          id: caseItem.case_id,
          filename: caseItem.filename,
          title: caseItem.case_title,
          titleThai: caseItem.case_title, // Use same title for now
          specialty: caseItem.medical_specialty,
          duration: caseItem.exam_duration_minutes,
          description: `${caseItem.case_type === '01' ? 'Child/Parent case' : 'Adult patient case'} - ${caseItem.medical_specialty}`,
          caseType: caseItem.case_type
        }));
        console.log('📋 Transformed cases:', transformedCases.length, 'cases');
        setCases(transformedCases);
      }
    } catch (error) {
      console.error('❌ Failed to load cases:', error);
      setErrors({ api: 'Failed to load cases. Please try again.' });
    } finally {
      setLoadingCases(false);
    }
  };

  // Intersection Observer for scroll-triggered animations
  useEffect(() => {
    if (step !== 2 || !caseListRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const cardId = entry.target.dataset.cardId;
          if (entry.isIntersecting) {
            // Add visible class when entering viewport
            setVisibleCards((prev) => new Set([...prev, cardId]));
          } else {
            // Remove visible class when leaving viewport (allows re-animation)
            setVisibleCards((prev) => {
              const newSet = new Set(prev);
              newSet.delete(cardId);
              return newSet;
            });
          }
        });
      },
      {
        root: caseListRef.current,
        rootMargin: '-1px 0px -20px 0px',
        threshold: 0.1
      }
    );

    cardRefs.current.forEach((card) => {
      if (card) observer.observe(card);
    });

    return () => observer.disconnect();
  }, [step]);

  // Handle scroll to show/hide gradients
  useEffect(() => {
    const caseList = caseListRef.current;
    if (!caseList) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = caseList;
      
      // Show top gradient if scrolled down
      setShowTopGradient(scrollTop > 10);
      
      // Show bottom gradient if not at bottom
      setShowBottomGradient(scrollTop < scrollHeight - clientHeight - 10);
    };

    caseList.addEventListener('scroll', handleScroll);
    // Initial check
    handleScroll();

    return () => caseList.removeEventListener('scroll', handleScroll);
  }, [step]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateStep1 = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.studentId.trim()) {
      newErrors.studentId = 'Student ID is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = async () => {
    if (!validateStep1()) return;
    try {
      setLoading(true);
      const userInfo = {
        name: formData.name,
        student_id: formData.studentId,
        email: formData.email,
        preferences: settings
      };
      await apiService.preLogin(userInfo);
      setStep(2);
    } catch (e) {
      console.error('Prelogin failed:', e);
      setErrors({ api: e.message || 'Login failed. Please check your info.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCaseSelect = (caseData) => {
    setFormData(prev => ({ ...prev, selectedCase: caseData }));
  };

  const handleStartSession = async () => {
    if (!formData.selectedCase) {
      setErrors({ case: 'Please select a case' });
      return;
    }

    // If exam mode is enabled, show recording consent
    if (settings.examMode) {
      setShowRecordingConsent(true);
      return;
    }

    // Start session without recording
    await startSessionWithoutRecording();
  };

  const startSessionWithoutRecording = async () => {
    try {
      setLoading(true);
      const userInfo = {
        name: formData.name,
        student_id: formData.studentId,
        email: formData.email,
        preferences: settings
      };
      
      const session = await startSession(userInfo, formData.selectedCase.filename, {});
      onStart(session);
      onClose();
    } catch (error) {
      console.error('Failed to start session:', error);
      setErrors({ api: error.message || 'Failed to start session. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRecording = async () => {
    try {
      setLoading(true);
      setShowRecordingConsent(false);
      
      // Start the session first
      const userInfo = {
        name: formData.name,
        student_id: formData.studentId,
        email: formData.email,
        preferences: settings
      };
      
      const session = await startSession(userInfo, formData.selectedCase.filename, {});
      
      // Start recording (this will request camera permission)
      console.log('📹 Starting recording...');
      const recordResult = await startRecording();
      
      if (!recordResult.success) {
        console.error('Failed to start recording:', recordResult.error);
        setRecordingError(recordResult.error || 'Failed to start recording');
        // Show error but continue with session
        setTimeout(() => {
          alert('Recording failed: ' + recordResult.error + '\nContinuing without recording.');
        }, 500);
      }
      
      onStart(session);
      onClose();
    } catch (error) {
      console.error('Failed to start session:', error);
      setErrors({ api: error.message || 'Failed to start session. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeclineRecording = async () => {
    setShowRecordingConsent(false);
    await startSessionWithoutRecording();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal start-session-modal">
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-title">Start New Session</h2>
            <p className="modal-subtitle">{userData ? 'Select Case' : `Step ${step} of 2`}</p>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {!userData && (
          <div className="modal-progress">
            <div 
              className={`progress-step ${step >= 1 ? 'active' : ''}`}
            >
              <div className="progress-dot"></div>
              <span className="progress-label">Student Info</span>
            </div>
            <div className="progress-line"></div>
            <div 
              className={`progress-step ${step >= 2 ? 'active' : ''}`}
            >
              <div className="progress-dot"></div>
              <span className="progress-label">Select Case</span>
            </div>
          </div>
        )}

        <div className="modal-body">
          {step === 1 ? (
            <div className="step-content fade-in">
              <div className="form-group">
                <label className="form-label">
                  <User size={18} />
                  Full Name
                </label>
                <input
                  type="text"
                  name="name"
                  className={`input ${errors.name ? 'input-error' : ''}`}
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={handleInputChange}
                  autoFocus
                />
                {errors.name && (
                  <span className="error-text">{errors.name}</span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">
                  <CreditCard size={18} />
                  Student ID
                </label>
                <input
                  type="text"
                  name="studentId"
                  className={`input ${errors.studentId ? 'input-error' : ''}`}
                  placeholder="Enter your student ID"
                  value={formData.studentId}
                  onChange={handleInputChange}
                />
                {errors.studentId && (
                  <span className="error-text">{errors.studentId}</span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">
                  Email (optional)
                </label>
                <input
                  type="email"
                  name="email"
                  className="input"
                  placeholder="your@email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>
            </div>
          ) : (
            <div className="step-content fade-in">
              <div className="form-group">
                <label className="form-label">
                  <FileText size={18} />
                  Select Patient Case
                </label>
                {/* Wrapper with gradient overlays */}
                {loadingCases ? (
                  <div className="loading-state">
                    <Loader className="spinning" size={24} />
                    <p>Loading cases...</p>
                  </div>
                ) : cases.length === 0 ? (
                  <div className="loading-state">
                    <p>No cases found. ({cases.length} cases loaded)</p>
                    {errors.api && <p className="error-text">{errors.api}</p>}
                  </div>
                ) : (
                  <div 
                    className={`case-list-wrapper ${showTopGradient ? 'show-top-gradient' : ''} ${showBottomGradient ? 'show-bottom-gradient' : ''}`}
                  >
                    <div className="case-list" ref={caseListRef}>
                      {cases.map((caseItem, index) => (
                        <div
                          key={caseItem.id}
                          ref={(el) => (cardRefs.current[index] = el)}
                          data-card-id={caseItem.id}
                          className={`case-card visible ${formData.selectedCase?.id === caseItem.id ? 'selected' : ''}`}
                          onClick={() => handleCaseSelect(caseItem)}
                        >
                          <div className="case-header">
                            <h4 className="case-title">{caseItem.title}</h4>
                            {/* <span className="case-duration">{caseItem.duration} min</span> */}
                          </div>
                          <p className="case-title-thai">{caseItem.titleThai}</p>
                          <p className="case-description">{caseItem.description}</p>
                          <div className="case-meta">
                            <span className="case-badge">{caseItem.specialty}</span>
                            <span className="case-badge case-type-badge">
                              {caseItem.caseType === '01' ? 'Child/Parent' : 'Adult Patient'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {errors.case && (
                  <span className="error-text">{errors.case}</span>
                )}
                {errors.api && (
                  <span className="error-text">{errors.api}</span>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {step === 1 ? (
            <>
              <button className="btn btn-outline" onClick={onClose}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleNext} disabled={loading}>
                Next: Select Case
                <ChevronRight size={18} />
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-outline" onClick={userData ? onClose : () => setStep(1)}>
                {userData ? 'Cancel' : 'Back'}
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleStartSession}
                disabled={!formData.selectedCase || loading}
              >
                {loading ? (
                  <>
                    <Loader className="spinning" size={18} />
                    Starting Session...
                  </>
                ) : (
                  <>
                    Start Session
                    <ChevronRight size={18} />
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Recording Consent Modal */}
      {showRecordingConsent && (
        <div className="modal-overlay" style={{ zIndex: 1001 }}>
          <div className="modal consent-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <div className="warning-icon">
                  <Video size={24} />
                </div>
                <h2 className="modal-title">Camera Recording Consent</h2>
              </div>
            </div>
            <div className="modal-body">
              <p>This session is in <strong>exam mode</strong> and requires video recording.</p>
              <p className="text-muted">
                We will request access to your camera to record the session. The recording will be saved and included in your session report.
              </p>
              {recordingError && (
                <div className="error-banner">
                  <span className="error-text">{recordingError}</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={handleDeclineRecording} disabled={loading}>
                Continue Without Recording
              </button>
              <button className="btn btn-primary" onClick={handleAcceptRecording} disabled={loading}>
                {loading ? (
                  <>
                    <Loader className="spinning" size={18} />
                    Starting...
                  </>
                ) : (
                  <>
                    <Video size={18} />
                    Accept & Start Recording
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StartSessionModal;
