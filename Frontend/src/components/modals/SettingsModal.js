import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { X, Palette, Sun, Moon, Cpu, Sliders, Save, AlertTriangle, RotateCcw } from 'lucide-react';
import './Modal.css';

// Default settings configuration
const DEFAULT_SETTINGS = {
  model: 'gpt-4.1-mini',
  memoryMode: 'summarize',
  examMode: false,
  temperature: 0.7,
  topP: 0.85,
  frequencyPenalty: 0.6,
  presencePenalty: 0.9,
  maxDuration: 15,
  autoSave: true,
  showTimer: true
};

const DEFAULT_THEME = 'light';

const SettingsModal = ({ onClose }) => {
  const { theme, toggleTheme, settings, updateSettings } = useApp();
  const [activeTab, setActiveTab] = useState('ai');
  const [localSettings, setLocalSettings] = useState(settings);
  const [localTheme, setLocalTheme] = useState(theme); // Track theme locally
  const [saved, setSaved] = useState(false);
  const [showUnsavedWarning, setShowUnsavedWarning] = useState(false);
  const [showResetWarning, setShowResetWarning] = useState(false);

  // Check if there are unsaved changes
  const hasChanges = () => {
    return JSON.stringify(localSettings) !== JSON.stringify(settings) || localTheme !== theme;
  };

  const handleSettingChange = (key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleThemeToggle = (newTheme) => {
    setLocalTheme(newTheme); // Only update local state, not actual theme
    setSaved(false);
  };

  const handleSave = () => {
    // Save settings
    updateSettings(localSettings);
    
    // Apply theme ONLY when Save is clicked
    if (localTheme !== theme) {
      toggleTheme();
    }
    
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleResetToDefault = () => {
    setShowResetWarning(true);
  };

  const confirmReset = () => {
    setLocalSettings(DEFAULT_SETTINGS);
    setLocalTheme(DEFAULT_THEME);
    setSaved(false);
    setShowResetWarning(false);
  };

  const cancelReset = () => {
    setShowResetWarning(false);
  };

  const handleCancel = () => {
    if (hasChanges()) {
      setShowUnsavedWarning(true);
    } else {
      onClose();
    }
  };

  const confirmDiscard = () => {
    setShowUnsavedWarning(false);
    onClose();
  };

  const cancelDiscard = () => {
    setShowUnsavedWarning(false);
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleCancel();
    }
  };

  return (
    <>
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal settings-modal">
          <div className="modal-header">
            <div className="modal-title-section">
              <h2 className="modal-title">Settings</h2>
              <p className="modal-subtitle">Configure your preferences</p>
            </div>
            <button className="modal-close" onClick={handleCancel}>
              <X size={24} />
            </button>
          </div>

          <div className="settings-tabs">
            <button
              className={`settings-tab ${activeTab === 'ai' ? 'active' : ''}`}
              onClick={() => setActiveTab('ai')}
            >
              <Cpu size={18} />
              การตั้งค่า AI
            </button>
            <button
              className={`settings-tab ${activeTab === 'appearance' ? 'active' : ''}`}
              onClick={() => setActiveTab('appearance')}
            >
              <Palette size={18} />
              Appearance
            </button>
          </div>

          <div className="modal-body settings-body">
            {activeTab === 'ai' && (
              <div className="settings-section fade-in">
                {/* Model Selection */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Cpu size={18} />
                    เวอร์ชันโมเดล
                  </label>
                  <select
                    className="select"
                    value={localSettings.model}
                    onChange={(e) => handleSettingChange('model', e.target.value)}
                  >
                    <option value="gpt-4.1-mini">GPT-4.1 Mini (ปรับแต่งได้)</option>
                    <option value="gpt-5">GPT-5 (คำตอบคงที่)</option>
                  </select>
                  <p className="setting-hint">
                    GPT-4.1 Mini สามารถปรับแต่งพารามิเตอร์ได้ ส่วน GPT-5 ให้คำตอบที่สม่ำเสมอ
                  </p>
                </div>

                {/* Memory Mode */}
                <div className="setting-group">
                  <label className="setting-label">
                    โหมดความจำ
                  </label>
                  <select
                    className="select"
                    value={localSettings.memoryMode}
                    onChange={(e) => handleSettingChange('memoryMode', e.target.value)}
                  >
                    <option value="none">เก็บประวัติทั้งหมด</option>
                    <option value="truncate">ตัดข้อความเก่าทิ้ง</option>
                    <option value="summarize">สรุปข้อความเก่า</option>
                  </select>
                  <p className="setting-hint">
                    กำหนดวิธีจัดการประวัติการสนทนา
                  </p>
                </div>

                {/* Exam Mode */}
                <div className="setting-group">
                  <label className="setting-label">
                    โหมดการใช้งาน
                  </label>
                  <div className="toggle-group">
                    <button
                      className={`toggle-option ${!localSettings.examMode ? 'active' : ''}`}
                      onClick={() => handleSettingChange('examMode', false)}
                    >
                      โหมดฝึกซ้อม
                    </button>
                    <button
                      className={`toggle-option ${localSettings.examMode ? 'active' : ''}`}
                      onClick={() => handleSettingChange('examMode', true)}
                    >
                      โหมดสอบ
                    </button>
                  </div>
                  <p className="setting-hint">
                    โหมดสอบจะให้คำตอบที่เหมือนเดิมทุกครั้งเพื่อความยุติธรรม
                  </p>
                </div>

                {/* Temperature */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Sliders size={18} />
                    ความสร้างสรรค์
                    <span className="setting-value">{localSettings.temperature}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={localSettings.temperature}
                    onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                    className="slider"
                    disabled={localSettings.model === 'gpt-5'}
                  />
                  <p className="setting-hint">
                    ค่าสูง = คำตอบสร้างสรรค์มากขึ้น, ค่าต่ำ = คำตอบตรงประเด็นมากขึ้น
                  </p>
                </div>

                {/* Top P */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Sliders size={18} />
                    ความหลากหลาย
                    <span className="setting-value">{localSettings.topP}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={localSettings.topP}
                    onChange={(e) => handleSettingChange('topP', parseFloat(e.target.value))}
                    className="slider"
                    disabled={localSettings.model === 'gpt-5'}
                  />
                  <p className="setting-hint">
                    ควบคุมความหลากหลายของการเลือกคำ, ค่าสูง = คำตอบหลากหลายขึ้น
                  </p>
                </div>

                {/* Frequency Penalty */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Sliders size={18} />
                    ลดคำซ้ำ
                    <span className="setting-value">{localSettings.frequencyPenalty}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={localSettings.frequencyPenalty}
                    onChange={(e) => handleSettingChange('frequencyPenalty', parseFloat(e.target.value))}
                    className="slider"
                    disabled={localSettings.model === 'gpt-5'}
                  />
                  <p className="setting-hint">
                    ลดการใช้คำซ้ำๆ ค่าสูง = ซ้ำน้อยลง
                  </p>
                </div>

                {/* Presence Penalty */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Sliders size={18} />
                    หัวข้อใหม่
                    <span className="setting-value">{localSettings.presencePenalty}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={localSettings.presencePenalty}
                    onChange={(e) => handleSettingChange('presencePenalty', parseFloat(e.target.value))}
                    className="slider"
                    disabled={localSettings.model === 'gpt-5'}
                  />
                  <p className="setting-hint">
                    กระตุ้นให้พูดถึงหัวข้อใหม่ๆ มากขึ้น
                  </p>
                </div>

                {/* Max Duration */}
                <div className="setting-group">
                  <label className="setting-label">
                    ระยะเวลาสูงสุดต่อเซสชัน (นาที)
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={localSettings.maxDuration}
                    onChange={(e) => handleSettingChange('maxDuration', parseInt(e.target.value))}
                    min="5"
                    max="60"
                  />
                  <p className="setting-hint">
                    กำหนดเวลาสูงสุดที่อนุญาตสำหรับการใช้งานแต่ละครั้ง
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="settings-section fade-in">
                {/* Theme - MODIFIED: Use localTheme instead of theme */}
                <div className="setting-group">
                  <label className="setting-label">
                    <Palette size={18} />
                    Theme
                  </label>
                  <div className="theme-options">
                    <button
                      className={`theme-option ${localTheme === 'light' ? 'active' : ''}`}
                      onClick={() => handleThemeToggle('light')}
                    >
                      <Sun size={24} />
                      <span>Light Mode</span>
                    </button>
                    <button
                      className={`theme-option ${localTheme === 'dark' ? 'active' : ''}`}
                      onClick={() => handleThemeToggle('dark')}
                    >
                      <Moon size={24} />
                      <span>Dark Mode</span>
                    </button>
                  </div>
                  <p className="setting-hint">
                    Click "Save Settings" to apply theme change.
                  </p>
                </div>

                {/* Auto Save */}
                <div className="setting-group">
                  <label className="setting-label">
                    Auto-save Session
                  </label>
                  <div className="toggle-switch">
                    <input
                      type="checkbox"
                      id="auto-save"
                      checked={localSettings.autoSave}
                      onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
                    />
                    <label htmlFor="auto-save" className="switch-label">
                      <span className="switch-slider"></span>
                    </label>
                    <span className="toggle-label">
                      {localSettings.autoSave ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <p className="setting-hint">
                    Automatically save session progress every 30 seconds.
                  </p>
                </div>

                {/* Show Timer */}
                <div className="setting-group">
                  <label className="setting-label">
                    Show Timer
                  </label>
                  <div className="toggle-switch">
                    <input
                      type="checkbox"
                      id="show-timer"
                      checked={localSettings.showTimer}
                      onChange={(e) => handleSettingChange('showTimer', e.target.checked)}
                    />
                    <label htmlFor="show-timer" className="switch-label">
                      <span className="switch-slider"></span>
                    </label>
                    <span className="toggle-label">
                      {localSettings.showTimer ? 'Visible' : 'Hidden'}
                    </span>
                  </div>
                  <p className="setting-hint">
                    Display session timer in the chatbot interface.
                  </p>
                </div>
              </div>
            )}

            {/* Unsaved Changes Warning */}
            {hasChanges() && (
              <div style={{
                padding: '1rem',
                background: 'linear-gradient(135deg, #fef3c7, #fde047)',
                borderRadius: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                color: '#92400e',
                fontWeight: 600,
                marginTop: '1rem'
              }}>
                <AlertTriangle size={20} />
                <span>You have unsaved changes</span>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button className="btn btn-outline" onClick={handleResetToDefault} style={{ marginRight: 'auto' }}>
              <RotateCcw size={18} />
              Reset to Default
            </button>
            <button className="btn btn-outline" onClick={handleCancel}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={!hasChanges()}>
              <Save size={18} />
              {saved ? 'Saved!' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Unsaved Changes Warning Modal */}
      {showUnsavedWarning && (
        <div className="modal-overlay" style={{ zIndex: 1001 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
            <div className="modal-header">
              <div className="modal-title-section">
                <div className="warning-icon">
                  <AlertTriangle size={24} />
                </div>
                <h2 className="modal-title">Discard Changes?</h2>
              </div>
            </div>
            
            <div className="modal-body">
              <p>You have unsaved changes. Are you sure you want to close without saving them?</p>
            </div>

            <div className="modal-footer">
              <button className="btn btn-outline" onClick={cancelDiscard}>
                Go Back
              </button>
              <button className="btn btn-danger" onClick={confirmDiscard}>
                Yes, Discard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reset to Default Warning Modal */}
      {showResetWarning && (
        <div className="modal-overlay" style={{ zIndex: 1001 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
            <div className="modal-header">
              <div className="modal-title-section">
                <div className="warning-icon" style={{ background: 'linear-gradient(135deg, #fef3c7, #fde047)' }}>
                  <RotateCcw size={24} />
                </div>
                <h2 className="modal-title">Reset to Default?</h2>
              </div>
            </div>
            
            <div className="modal-body">
              <p>This will reset all settings to their default values. This action cannot be undone.</p>
            </div>

            <div className="modal-footer">
              <button className="btn btn-outline" onClick={cancelReset}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={confirmReset}>
                <RotateCcw size={18} />
                Yes, Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SettingsModal;