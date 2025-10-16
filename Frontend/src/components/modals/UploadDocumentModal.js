import React, { useState, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { X, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import apiService from '../../services/apiService';
import './Modal.css';

const UploadDocumentModal = ({ onClose, onComplete }) => {
  const { startSessionWithUploadedCase } = useApp();
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

  const uploadDocument = async () => {
    if (!file) return;
    
    setStep(2);
    setUploadProgress(0);
    setError(null);
    
    try {
      // Start with file upload progress
      let uploadComplete = false;
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (!uploadComplete && prev < 20) {
            return prev + 2; // File upload: 0-20%
          } else if (uploadComplete && prev < 95) {
            return prev + 0.5; // AI processing: 20-95% (very slow for 3-4 min)
          }
          return prev;
        });
      }, 1000); // 1 second intervals for better UX during long processing
      
      // Upload document and process with ChatGPT
      const response = await apiService.uploadDocument(file, (progressEvent) => {
        if (progressEvent.loaded === progressEvent.total) {
          uploadComplete = true;
          setUploadProgress(20); // File uploaded, now processing
        }
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success && response.data.extracted_data) {
        // Set the real extracted data from ChatGPT
        setExtractedData(response.data.extracted_data);
        
        // Generate validation status based on the main schema topics
        const validationStatus = generateValidationStatus(response.data.extracted_data);
        setValidationStatus(validationStatus);
        
        setStep(3);
      } else {
        throw new Error(response.message || 'Failed to process document');
      }
    } catch (err) {
      console.error('Upload error:', err);
      let errorMessage = 'Failed to upload and process document';
      
      if (err.message.includes('timeout')) {
        errorMessage = 'Processing is taking longer than expected. The document might still be processing in the background. Please try again in a moment.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setStep(1);
      setUploadProgress(0);
    }
  };
  
  const generateValidationStatus = (data) => {
    return {
      case_id: !!(data.case_id),
      case_metadata: !!(data.case_metadata && data.case_metadata.case_title),
      examiner_view: !!(data.examiner_view && data.examiner_view.patient_background),
      simulation_view: !!(data.simulation_view && data.simulation_view.simulator_profile)
    };
  };

  const handleStartSession = async () => {
    try {
      const userInfo = {
        name: 'Current User',
        student_id: 'TEMP-ID',
        email: 'user@example.com'
      };
      
      const session = await startSessionWithUploadedCase(
        userInfo,
        extractedData,
        {}
      );
      
      onComplete(session);
    } catch (error) {
      console.error('Failed to start session:', error);
      setError('Failed to start session: ' + error.message);
    }
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
                <p>Extracting patient information using ChatGPT AI...</p>
                <p className="text-muted" style={{ fontSize: '0.9em', marginTop: '0.5rem' }}>
                  This may take 3-4 minutes depending on document complexity. Please be patient.
                </p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="progress-text">{uploadProgress}%</p>
                
                {error && (
                  <div className="error-message" style={{ marginTop: '1rem' }}>
                    <AlertCircle size={18} />
                    {error}
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 3 && extractedData && (
            <div className="preview-section fade-in">
              <div className="validation-summary">
                <h3>Validation Status</h3>
                <div className="validation-items">
                  <div className="validation-item">
                    {validationStatus?.case_id ? 
                      <CheckCircle size={18} className="icon-success" /> : 
                      <AlertCircle size={18} className="icon-warning" />
                    }
                    <span>Case ID: {validationStatus?.case_id ? 'Found' : 'Missing'}</span>
                  </div>
                  <div className="validation-item">
                    {validationStatus?.case_metadata ? 
                      <CheckCircle size={18} className="icon-success" /> : 
                      <AlertCircle size={18} className="icon-warning" />
                    }
                    <span>Case Metadata: {validationStatus?.case_metadata ? 'Complete' : 'Incomplete'}</span>
                  </div>
                  <div className="validation-item">
                    {validationStatus?.examiner_view ? 
                      <CheckCircle size={18} className="icon-success" /> : 
                      <AlertCircle size={18} className="icon-warning" />
                    }
                    <span>Examiner View: {validationStatus?.examiner_view ? 'Complete' : 'Incomplete'}</span>
                  </div>
                  <div className="validation-item">
                    {validationStatus?.simulation_view ? 
                      <CheckCircle size={18} className="icon-success" /> : 
                      <AlertCircle size={18} className="icon-warning" />
                    }
                    <span>Simulation View: {validationStatus?.simulation_view ? 'Complete' : 'Incomplete'}</span>
                  </div>
                </div>
              </div>

              <div className="data-preview">
                <h3>Extracted Data Preview</h3>
                <div className="json-preview">
                  <pre>{JSON.stringify(extractedData, null, 2)}</pre>
                </div>
                
                {error && (
                  <div className="error-message" style={{ marginTop: '1rem' }}>
                    <AlertCircle size={18} />
                    {error}
                  </div>
                )}
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
                onClick={uploadDocument}
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
