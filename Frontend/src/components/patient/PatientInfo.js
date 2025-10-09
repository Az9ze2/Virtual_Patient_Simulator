import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { User, Calendar, Stethoscope, Activity, Loader, RefreshCw } from 'lucide-react';
import apiService from '../../services/apiService';
import './PatientInfo.css';

const PatientInfo = () => {
  const { sessionData } = useApp();
  const [patientInfo, setPatientInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (sessionData?.sessionId) {
      loadPatientInfo();
    }
  }, [sessionData?.sessionId]);

  const loadPatientInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getPatientInfo(sessionData.sessionId);
      
      if (response.success) {
        setPatientInfo(response.data.patient_info);
      } else {
        throw new Error(response.error || 'Failed to load patient info');
      }
    } catch (err) {
      console.error('Failed to load patient info:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatAge = (ageData) => {
    if (!ageData) return 'N/A';
    if (typeof ageData === 'object' && ageData.value && ageData.unit) {
      return `${ageData.value} ${ageData.unit}`;
    }
    return ageData.toString();
  };

  const formatVitalSigns = (vitals) => {
    if (!vitals) return [];
    
    const vitalsList = [];
    if (vitals.body_temperature_in_celsius) {
      vitalsList.push(`Temp: ${vitals.body_temperature_in_celsius}°C`);
    }
    if (vitals.heart_rate_in_beats_per_minute) {
      vitalsList.push(`HR: ${vitals.heart_rate_in_beats_per_minute} bpm`);
    }
    if (vitals.respiratory_rate_in_breaths_per_minute) {
      vitalsList.push(`RR: ${vitals.respiratory_rate_in_breaths_per_minute} rpm`);
    }
    if (vitals.blood_pressure_in_mmHg) {
      vitalsList.push(`BP: ${vitals.blood_pressure_in_mmHg}`);
    }
    if (vitals.oxygen_saturation) {
      vitalsList.push(`O2 Sat: ${vitals.oxygen_saturation}`);
    }
    
    return vitalsList;
  };

  if (loading) {
    return (
      <div className="patient-info loading-state">
        <div className="patient-info-header">
          <h3>Patient Information</h3>
        </div>
        <div className="loading-content">
          <Loader className="spinning" size={24} />
          <p>Loading patient information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="patient-info error-state">
        <div className="patient-info-header">
          <h3>Patient Information</h3>
          <button 
            className="refresh-btn"
            onClick={loadPatientInfo}
            title="Retry loading patient info"
          >
            <RefreshCw size={16} />
          </button>
        </div>
        <div className="error-content">
          <p className="error-message">Failed to load patient information</p>
          <p className="error-details">{error}</p>
          <button className="btn btn-outline btn-sm" onClick={loadPatientInfo}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!patientInfo) {
    return (
      <div className="patient-info empty-state">
        <div className="patient-info-header">
          <h3>Patient Information</h3>
        </div>
        <div className="empty-content">
          <User size={48} className="empty-icon" />
          <p>Patient information not available</p>
        </div>
      </div>
    );
  }

  const vitals = formatVitalSigns(patientInfo.physical_examination?.vital_signs);

  return (
    <div className="patient-info">
      <div className="patient-info-header">
        <div className="header-content">
          <User size={20} />
          <h3>Patient Information</h3>
        </div>
        <button 
          className="refresh-btn"
          onClick={loadPatientInfo}
          title="Refresh patient info"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="patient-info-content">
        {/* Basic Information */}
        <div className="info-section">
          <h4 className="section-title">
            <User size={16} />
            Basic Information
          </h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Name:</span>
              <span className="info-value">{patientInfo.name || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Age:</span>
              <span className="info-value">{formatAge(patientInfo.age)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Sex:</span>
              <span className="info-value">{patientInfo.sex || 'N/A'}</span>
            </div>
            {patientInfo.occupation && patientInfo.occupation !== 'not provided' && (
              <div className="info-item">
                <span className="info-label">Occupation:</span>
                <span className="info-value">{patientInfo.occupation}</span>
              </div>
            )}
          </div>
        </div>

        {/* Chief Complaint */}
        <div className="info-section">
          <h4 className="section-title">
            <Activity size={16} />
            Chief Complaint
          </h4>
          <div className="complaint-content">
            {patientInfo.chief_complaint || 'No chief complaint recorded'}
          </div>
        </div>

        {/* Vital Signs */}
        {vitals.length > 0 && (
          <div className="info-section">
            <h4 className="section-title">
              <Stethoscope size={16} />
              Vital Signs
            </h4>
            <div className="vitals-grid">
              {vitals.map((vital, index) => (
                <div key={index} className="vital-item">
                  {vital}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Physical Examination */}
        {patientInfo.physical_examination && (
          <div className="info-section">
            <h4 className="section-title">
              <Stethoscope size={16} />
              Physical Examination
            </h4>
            <div className="exam-content">
              {patientInfo.physical_examination.general_appearance && (
                <div className="exam-item">
                  <span className="exam-label">General Appearance:</span>
                  <span className="exam-value">{patientInfo.physical_examination.general_appearance}</span>
                </div>
              )}
              {patientInfo.physical_examination.heart && (
                <div className="exam-item">
                  <span className="exam-label">Heart:</span>
                  <span className="exam-value">{patientInfo.physical_examination.heart}</span>
                </div>
              )}
              {patientInfo.physical_examination.lungs && (
                <div className="exam-item">
                  <span className="exam-label">Lungs:</span>
                  <span className="exam-value">{patientInfo.physical_examination.lungs}</span>
                </div>
              )}
              {patientInfo.physical_examination.abdomen && (
                <div className="exam-item">
                  <span className="exam-label">Abdomen:</span>
                  <span className="exam-value">{patientInfo.physical_examination.abdomen}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Medical History */}
        {patientInfo.patient_illness_history && (
          <div className="info-section">
            <h4 className="section-title">
              <Calendar size={16} />
              Medical History
            </h4>
            <div className="history-content">
              {patientInfo.patient_illness_history.past_medical_history && 
               patientInfo.patient_illness_history.past_medical_history !== 'not provided' && (
                <div className="history-item">
                  <span className="history-label">Past Medical History:</span>
                  <span className="history-value">{patientInfo.patient_illness_history.past_medical_history}</span>
                </div>
              )}
              {patientInfo.patient_illness_history.current_medications && 
               patientInfo.patient_illness_history.current_medications !== 'not provided' && (
                <div className="history-item">
                  <span className="history-label">Current Medications:</span>
                  <span className="history-value">{patientInfo.patient_illness_history.current_medications}</span>
                </div>
              )}
              {patientInfo.patient_illness_history.allergies && 
               patientInfo.patient_illness_history.allergies !== 'not provided' && (
                <div className="history-item">
                  <span className="history-label">Allergies:</span>
                  <span className="history-value">{patientInfo.patient_illness_history.allergies}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientInfo;
