import React from 'react';
import { ClipboardList } from 'lucide-react';
import './DiagnosisSection.css';

const DiagnosisSection = ({ diagnosis, setDiagnosis, treatmentPlan, setTreatmentPlan }) => {
  return (
    <div className="diagnosis-card">
      <div className="card-header">
        <h3 className="card-title">
          <ClipboardList size={20} />
          Diagnosis & Treatment
        </h3>
      </div>

      <div className="diagnosis-content">
        <div className="form-group">
          <label className="form-label">
            Primary Diagnosis
          </label>
          <textarea
            className="textarea"
            placeholder="Enter your diagnosis here..."
            value={diagnosis}
            onChange={(e) => setDiagnosis(e.target.value)}
            rows={4}
          />
          <p className="form-hint">
            Based on the patient history and examination findings
          </p>
        </div>

        <div className="form-group">
          <label className="form-label">
            Treatment Plan
          </label>
          <textarea
            className="textarea"
            placeholder="Enter your treatment plan..."
            value={treatmentPlan}
            onChange={(e) => setTreatmentPlan(e.target.value)}
            rows={4}
          />
          <p className="form-hint">
            Include management and patient education
          </p>
        </div>

        <div className="diagnosis-stats">
          <div className="stat-item">
            <span className="stat-label">Diagnosis</span>
            <span className="stat-value">{diagnosis ? '✓' : '—'}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Treatment</span>
            <span className="stat-value">{treatmentPlan ? '✓' : '—'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiagnosisSection;
