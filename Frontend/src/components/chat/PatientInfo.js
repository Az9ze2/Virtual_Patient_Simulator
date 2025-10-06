import React from 'react';
import { User, Calendar, Stethoscope, Activity, FileText } from 'lucide-react';
import './PatientInfo.css';

const PatientInfo = ({ caseData }) => {
  if (!caseData || !caseData.examiner_view) {
    return (
      <div className="patient-info-card">
        <div className="card-header">
          <h3 className="card-title">
            <FileText size={20} />
            Patient Information
          </h3>
        </div>
        <div className="empty-state">
          <p>No patient data available</p>
        </div>
      </div>
    );
  }

  const { patient_background, physical_examination } = caseData.examiner_view;

  const formatAge = (age) => {
    if (typeof age === 'object' && age.value && age.unit) {
      return `${age.value} ${age.unit}`;
    }
    return age;
  };

  return (
    <div className="patient-info-card">
      <div className="card-header">
        <h3 className="card-title">
          <FileText size={20} />
          Patient Information
        </h3>
      </div>

      <div className="info-section">
        <h4 className="section-title">
          <User size={18} />
          Demographics
        </h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Name</span>
            <span className="info-value">{patient_background?.name || 'N/A'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Age</span>
            <span className="info-value">{formatAge(patient_background?.age) || 'N/A'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Sex</span>
            <span className="info-value">{patient_background?.sex || 'N/A'}</span>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h4 className="section-title">
          <Stethoscope size={18} />
          Chief Complaint
        </h4>
        <p className="complaint-text">
          {patient_background?.chief_complaint || 'No chief complaint recorded'}
        </p>
      </div>

      {physical_examination && (
        <div className="info-section">
          <h4 className="section-title">
            <Activity size={18} />
            Physical Examination
          </h4>
          
          {physical_examination.vital_signs && (
            <div className="vital-signs">
              <div className="vital-item">
                <span className="vital-label">Temperature</span>
                <span className="vital-value">
                  {physical_examination.vital_signs.body_temperature_in_celsius}°C
                </span>
              </div>
              <div className="vital-item">
                <span className="vital-label">Heart Rate</span>
                <span className="vital-value">
                  {physical_examination.vital_signs.heart_rate_in_beats_per_minute} bpm
                </span>
              </div>
              <div className="vital-item">
                <span className="vital-label">RR</span>
                <span className="vital-value">
                  {physical_examination.vital_signs.respiratory_rate_in_breaths_per_minute} /min
                </span>
              </div>
              <div className="vital-item">
                <span className="vital-label">O2 Sat</span>
                <span className="vital-value">
                  {physical_examination.vital_signs.oxygen_saturation || 'N/A'}
                </span>
              </div>
            </div>
          )}

          {physical_examination.weight_kg && (
            <div className="measurement-grid">
              <div className="measurement-item">
                <span className="measurement-label">Weight</span>
                <span className="measurement-value">{physical_examination.weight_kg} kg</span>
              </div>
              {physical_examination.length_cm && (
                <div className="measurement-item">
                  <span className="measurement-label">Length</span>
                  <span className="measurement-value">{physical_examination.length_cm} cm</span>
                </div>
              )}
              {physical_examination.ofc_cm && (
                <div className="measurement-item">
                  <span className="measurement-label">OFC</span>
                  <span className="measurement-value">{physical_examination.ofc_cm} cm</span>
                </div>
              )}
            </div>
          )}

          {physical_examination.general_appearance && (
            <div className="exam-detail">
              <span className="detail-label">General:</span>
              <span className="detail-text">{physical_examination.general_appearance}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PatientInfo;
