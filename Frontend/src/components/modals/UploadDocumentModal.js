import React, { useState, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { X, Upload, FileText, CheckCircle, AlertCircle, Eye, Edit } from 'lucide-react';
import './Modal.css';

const UploadDocumentModal = ({ onClose, onComplete }) => {
  const { startSession } = useApp();
  const [step, setStep] = useState(1); // 1: upload, 2: processing, 3: preview
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedData, setExtractedData] = useState(null);
  const [validationStatus, setValidationStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf'];
      if (!validTypes.includes(selectedFile.type)) {
        setError('Please upload a DOCX or PDF file');
        return;
      }

      // Validate file size (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }

      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const event = { target: { files: [droppedFile] } };
      handleFileSelect(event);
    }
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const simulateUpload = () => {
    setStep(2);
    setUploadProgress(0);
    
    // Simulate progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          // Simulate extraction complete
          setTimeout(() => {
            setExtractedData({
              case_id: 'CASE-UPLOAD-001',
              case_metadata: {
                case_title: 'Uploaded Case: Pediatric Assessment',
                medical_specialty: 'Pediatrics',
                exam_type: 'History Taking + Physical Examination',
                exam_duration_minutes: 15
              },
              examiner_view: {
                patient_background: {
                  name: 'ด.ช.สมชาย ใจดี',
                  age: { value: 6, unit: 'months' },
                  sex: 'Male',
                  chief_complaint: 'Fever for 2 days'
                }
              },
              validation: {
                complete: true,
                missingFields: []
              }
            });
            setValidationStatus({
              caseId: true,
              patientInfo: true,
              chiefComplaint: true,
              physicalExam: false
            });
            setStep(3);
          }, 500);
          return 100;
        }
        return prev + 5;
      });
    }, 100);
  };

  const handleStartSession = () => {
    const session = startSession({
      studentName: 'Current User',
      studentId: 'TEMP-ID',
      caseData: extractedData,
      caseId: extractedData.case_id,
      isUploadedCase: true
    });
    onComplete(session);
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal upload-modal">
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-title">Upload Document</h2>
            <p className="modal-subtitle">
              {step === 1 && 'Upload your patient case document'}
              {step === 2 && 'Extracting patient data...'}
              {step === 3 && 'Review extracted data'}
            </p>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          {step === 1 && (
            <div className="upload-section fade-in">
              <div
                className={`drop-zone ${file ? 'has-file' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
              >
                <input
                  type="file"
                  id="file-upload"
                  className="file-input"
                  accept=".docx,.pdf"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-upload" className="drop-zone-content">
                  {file ? (
                    <>
                      <FileText size={48} className="upload-icon success" />
                      <p className="upload-text-primary">{file.name}</p>
                      <p className="upload-text-secondary">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                      <p className="upload-text-hint">Click to change file</p>
                    </>
                  ) : (
                    <>
                      <Upload size={48} className="upload-icon" />
                      <p className="upload-text-primary">
                        Drop your document here or click to browse
                      </p>
                      <p className="upload-text-secondary">
                        Supports DOCX and PDF files up to 10MB
                      </p>
                    </>
                  )}
                </label>
              </div>

              {error && (
                <div className="error-message">
                  <AlertCircle size={18} />
                  {error}
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="processing-section fade-in">
              <div className="processing-content">
                <div className="spinner-large"></div>
                <h3>Processing Document</h3>
                <p>Extracting patient information from your document...</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="progress-text">{uploadProgress}%</p>
              </div>
            </div>
          )}

          {step === 3 && extractedData && (
            <div className="preview-section fade-in">
              <div className="validation-summary">
                <h3>Validation Status</h3>
                <div className="validation-items">
                  <div className="validation-item">
                    <CheckCircle size={18} className="icon-success" />
                    <span>Case ID: Found</span>
                  </div>
                  <div className="validation-item">
                    <CheckCircle size={18} className="icon-success" />
                    <span>Patient Information: Complete</span>
                  </div>
                  <div className="validation-item">
                    <CheckCircle size={18} className="icon-success" />
                    <span>Chief Complaint: Found</span>
                  </div>
                  <div className="validation-item">
                    <AlertCircle size={18} className="icon-warning" />
                    <span>Physical Examination: Incomplete</span>
                  </div>
                </div>
              </div>

              <div className="data-preview">
                <h3>Extracted Data Preview</h3>
                <div className="json-preview">
                  <pre>{JSON.stringify(extractedData, null, 2)}</pre>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {step === 1 && (
            <>
              <button className="btn btn-outline" onClick={onClose}>
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={simulateUpload}
                disabled={!file}
              >
                <Upload size={18} />
                Upload & Extract
              </button>
            </>
          )}

          {step === 3 && (
            <>
              <button className="btn btn-outline" onClick={onClose}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleStartSession}>
                Start Session with This Case
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadDocumentModal;
