import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { X, User, CreditCard, ChevronRight, FileText } from 'lucide-react';
import './Modal.css';

// Mock cases data
const MOCK_CASES = [
  {
    id: 'CASE-001',
    title: 'Breast Feeding Problems - Cracked Nipple',
    titleThai: 'ปัญหาการให้นมแม่ - หัวนมแตก',
    specialty: 'Pediatrics',
    duration: 10,
    description: '5-day-old infant with mother experiencing cracked nipple'
  },
  {
    id: 'CASE-002',
    title: 'Child Health Check - 9 months',
    titleThai: 'ตรวจสุขภาพเด็ก 9 เดือน',
    specialty: 'Pediatrics',
    duration: 10,
    description: '9-month-old infant routine health check'
  },
  {
    id: 'CASE-003',
    title: 'Phimosis in 2-month-old',
    titleThai: 'ปัญหาหนังหุ้มปลายลึงค์ในเด็ก 2 เดือน',
    specialty: 'Pediatrics',
    duration: 10,
    description: '2-month-old with phimosis concerns'
  },
  {
    id: 'CASE-004',
    title: 'Edema in Child',
    titleThai: 'อาการบวมในเด็ก',
    specialty: 'Pediatrics',
    duration: 10,
    description: 'Child presenting with edema symptoms'
  }
];

const StartSessionModal = ({ onClose, onStart }) => {
  const { startSession } = useApp();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    studentId: '',
    selectedCase: null
  });
  const [errors, setErrors] = useState({});

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

  const handleNext = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handleCaseSelect = (caseData) => {
    setFormData(prev => ({ ...prev, selectedCase: caseData }));
  };

  const handleStartSession = () => {
    if (!formData.selectedCase) {
      setErrors({ case: 'Please select a case' });
      return;
    }

    const session = startSession({
      studentName: formData.name,
      studentId: formData.studentId,
      caseData: formData.selectedCase,
      caseId: formData.selectedCase.id
    });

    onStart(session);
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
            <p className="modal-subtitle">Step {step} of 2</p>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

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
            </div>
          ) : (
            <div className="step-content fade-in">
              <div className="form-group">
                <label className="form-label">
                  <FileText size={18} />
                  Select Patient Case
                </label>
                <div className="case-list">
                  {MOCK_CASES.map((caseItem) => (
                    <div
                      key={caseItem.id}
                      className={`case-card ${formData.selectedCase?.id === caseItem.id ? 'selected' : ''}`}
                      onClick={() => handleCaseSelect(caseItem)}
                    >
                      <div className="case-header">
                        <h4 className="case-title">{caseItem.title}</h4>
                        <span className="case-duration">{caseItem.duration} min</span>
                      </div>
                      <p className="case-title-thai">{caseItem.titleThai}</p>
                      <p className="case-description">{caseItem.description}</p>
                      <div className="case-meta">
                        <span className="case-badge">{caseItem.specialty}</span>
                      </div>
                    </div>
                  ))}
                </div>
                {errors.case && (
                  <span className="error-text">{errors.case}</span>
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
              <button className="btn btn-primary" onClick={handleNext}>
                Next: Select Case
                <ChevronRight size={18} />
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-outline" onClick={() => setStep(1)}>
                Back
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleStartSession}
                disabled={!formData.selectedCase}
              >
                Start Session
                <ChevronRight size={18} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StartSessionModal;
