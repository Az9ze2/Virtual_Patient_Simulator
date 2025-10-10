import React, { useState } from 'react';
import { User, Stethoscope, Activity, FileText, ChevronDown, Calendar } from 'lucide-react';
import './PatientInfo.css';

const PatientInfo = ({ caseData, onExpand }) => {
  // ============ State for hover visibility ============
  const [isHovering, setIsHovering] = useState(false);

  const hasData = caseData && caseData.examiner_view;
  const { patient_background, physical_examination } = hasData ? caseData.examiner_view : {};

  const formatAge = (age) => {
    if (typeof age === 'object' && age.value && age.unit) {
      return `${age.value} ${age.unit}`;
    }
    return age;
  };

  // ============ Format vital signs helper ============
  const formatVitalSigns = (vitals) => {
    if (!vitals) return [];
    
    const vitalsList = [];
    if (vitals.body_temperature_in_celsius) {
      vitalsList.push({ label: 'Temperature', value: `${vitals.body_temperature_in_celsius}°C` });
    }
    if (vitals.heart_rate_in_beats_per_minute) {
      vitalsList.push({ label: 'Heart Rate', value: `${vitals.heart_rate_in_beats_per_minute} bpm` });
    }
    if (vitals.respiratory_rate_in_breaths_per_minute) {
      vitalsList.push({ label: 'Respiratory Rate', value: `${vitals.respiratory_rate_in_breaths_per_minute} /min` });
    }
    if (vitals.blood_pressure_in_mmHg) {
      vitalsList.push({ label: 'Blood Pressure', value: vitals.blood_pressure_in_mmHg });
    }
    if (vitals.oxygen_saturation) {
      vitalsList.push({ label: 'O2 Saturation', value: vitals.oxygen_saturation });
    }
    
    return vitalsList;
  };

  // ============ NEW: Handle hover events to expand/shrink boxes ============
  const handleMouseEnter = () => {
    if (hasData) {
      setIsHovering(true);
      if (onExpand) onExpand(true);
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    if (onExpand) onExpand(false);
  };

  const vitals = formatVitalSigns(physical_examination?.vital_signs);

  return (
    <div
      className="patient-info-card"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ cursor: hasData ? 'pointer' : 'default' }}
    >
      <div className="card-header">
        <h3 className="card-title">
          <FileText size={20} />
          Patient Information
        </h3>
      </div>
      {!hasData ? (
        <div className="empty-state">
          <p>No patient data available</p>
        </div>
      ) : !isHovering ? (
        // ============ Preview state when NOT hovering ============
        <div className="preview-state">
          <p className="data-available-text">Patient data available</p>
          <div className="hover-hint">
            <ChevronDown className="arrow-bounce" size={24} />
            <span className="hint-text">Hold here for more information</span>
          </div>
        </div>
      ) : (
        // ============ NEW: Expanded view when hovering - Shows full data inside the expanded box ============
        <div className="patient-info-expanded" style={{ overflowY: 'auto', height: '100%' }}>
          {/* Basic Information Section */}
          <div className="modal-section">
            <h4 className="modal-section-title">
              <User size={18} />
              Basic Information
            </h4>
            <div className="modal-info-grid">
              <div className="modal-info-item">
                <span className="modal-label">Name</span>
                <span className="modal-value">{patient_background?.name || 'N/A'}</span>
              </div>
              <div className="modal-info-item">
                <span className="modal-label">Age</span>
                <span className="modal-value">{formatAge(patient_background?.age) || 'N/A'}</span>
              </div>
              <div className="modal-info-item">
                <span className="modal-label">Sex</span>
                <span className="modal-value">{patient_background?.sex || 'N/A'}</span>
              </div>
              {patient_background?.occupation && patient_background.occupation !== 'not provided' && (
                <div className="modal-info-item">
                  <span className="modal-label">Occupation</span>
                  <span className="modal-value">{patient_background.occupation}</span>
                </div>
              )}
            </div>
          </div>

          {/* Chief Complaint Section */}
          <div className="modal-section">
            <h4 className="modal-section-title">
              <Activity size={18} />
              Chief Complaint
            </h4>
            <div className="modal-complaint">
              {patient_background?.chief_complaint || 'No chief complaint recorded'}
            </div>
          </div>

          {/* Vital Signs Section */}
          {vitals.length > 0 && (
            <div className="modal-section">
              <h4 className="modal-section-title">
                <Stethoscope size={18} />
                Vital Signs
              </h4>
              <div className="modal-vitals-grid">
                {vitals.map((vital, index) => (
                  <div key={index} className="modal-vital-card">
                    <span className="vital-card-label">{vital.label}</span>
                    <span className="vital-card-value">{vital.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Physical Examination Section */}
          {physical_examination && (
            <div className="modal-section">
              <h4 className="modal-section-title">
                <Stethoscope size={18} />
                Physical Examination
              </h4>
              
              {/* Measurements */}
              {(physical_examination.weight_kg || physical_examination.length_cm || physical_examination.ofc_cm) && (
                <div className="modal-measurements">
                  {physical_examination.weight_kg && (
                    <div className="measurement-badge">
                      <span className="measurement-label">Weight</span>
                      <span className="measurement-value">{physical_examination.weight_kg} kg</span>
                    </div>
                  )}
                  {physical_examination.length_cm && (
                    <div className="measurement-badge">
                      <span className="measurement-label">Length</span>
                      <span className="measurement-value">{physical_examination.length_cm} cm</span>
                    </div>
                  )}
                  {physical_examination.ofc_cm && (
                    <div className="measurement-badge">
                      <span className="measurement-label">OFC</span>
                      <span className="measurement-value">{physical_examination.ofc_cm} cm</span>
                    </div>
                  )}
                </div>
              )}

              {/* Examination Details */}
              {physical_examination.general_appearance && (
                <div className="modal-exam-detail">
                  <span className="exam-detail-label">General Appearance:</span>
                  <span className="exam-detail-text">{physical_examination.general_appearance}</span>
                </div>
              )}
              {physical_examination.heart && (
                <div className="modal-exam-detail">
                  <span className="exam-detail-label">Heart:</span>
                  <span className="exam-detail-text">{physical_examination.heart}</span>
                </div>
              )}
              {physical_examination.lungs && (
                <div className="modal-exam-detail">
                  <span className="exam-detail-label">Lungs:</span>
                  <span className="exam-detail-text">{physical_examination.lungs}</span>
                </div>
              )}
              {physical_examination.abdomen && (
                <div className="modal-exam-detail">
                  <span className="exam-detail-label">Abdomen:</span>
                  <span className="exam-detail-text">{physical_examination.abdomen}</span>
                </div>
              )}
            </div>
          )}

          {/* Medical History Section */}
          {patient_background?.patient_illness_history && (
            <div className="modal-section">
              <h4 className="modal-section-title">
                <Calendar size={18} />
                Medical History
              </h4>
              <div className="modal-history">
                {patient_background.patient_illness_history.past_medical_history && 
                 patient_background.patient_illness_history.past_medical_history !== 'not provided' && (
                  <div className="modal-history-item">
                    <span className="history-item-label">Past Medical History:</span>
                    <span className="history-item-text">{patient_background.patient_illness_history.past_medical_history}</span>
                  </div>
                )}
                {patient_background.patient_illness_history.current_medications && 
                 patient_background.patient_illness_history.current_medications !== 'not provided' && (
                  <div className="modal-history-item">
                    <span className="history-item-label">Current Medications:</span>
                    <span className="history-item-text">{patient_background.patient_illness_history.current_medications}</span>
                  </div>
                )}
                {patient_background.patient_illness_history.allergies && 
                 patient_background.patient_illness_history.allergies !== 'not provided' && (
                  <div className="modal-history-item">
                    <span className="history-item-label">Allergies:</span>
                    <span className="history-item-text">{patient_background.patient_illness_history.allergies}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PatientInfo;