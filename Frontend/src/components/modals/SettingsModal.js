import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { X, Settings as SettingsIcon, Palette, Sun, Moon, Cpu, Sliders, Save } from 'lucide-react';
import './Modal.css';

const SettingsModal = ({ onClose }) => {
  const { theme, toggleTheme, settings, updateSettings } = useApp();
  const [activeTab, setActiveTab] = useState('ai');
  const [localSettings, setLocalSettings] = useState(settings);
  const [saved, setSaved] = useState(false);

  const handleSettingChange = (key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    updateSettings(localSettings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal settings-modal">
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-title">Settings</h2>
            <p className="modal-subtitle">Configure your preferences</p>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="settings-tabs">
          <button
            className={`settings-tab ${activeTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai')}
          >
            <Cpu size={18} />
            AI Configuration
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
                  Model Version
                </label>
                <select
                  className="select"
                  value={localSettings.model}
                  onChange={(e) => handleSettingChange('model', e.target.value)}
                >
                  <option value="gpt-4.1-mini">GPT-4.1 Mini (Tunable)</option>
                  <option value="gpt-5">GPT-5 (Deterministic)</option>
                </select>
                <p className="setting-hint">
                  GPT-4.1 Mini allows parameter tuning. GPT-5 provides consistent responses.
                </p>
              </div>

              {/* Memory Mode */}
              <div className="setting-group">
                <label className="setting-label">
                  Memory Mode
                </label>
                <select
                  className="select"
                  value={localSettings.memoryMode}
                  onChange={(e) => handleSettingChange('memoryMode', e.target.value)}
                >
                  <option value="none">Keep All History</option>
                  <option value="truncate">Truncate Old Messages</option>
                  <option value="summarize">Summarize Old Messages</option>
                </select>
                <p className="setting-hint">
                  Controls how conversation history is managed.
                </p>
              </div>

              {/* Exam Mode */}
              <div className="setting-group">
                <label className="setting-label">
                  Exam Mode
                </label>
                <div className="toggle-group">
                  <button
                    className={`toggle-option ${!localSettings.examMode ? 'active' : ''}`}
                    onClick={() => handleSettingChange('examMode', false)}
                  >
                    Practice Mode
                  </button>
                  <button
                    className={`toggle-option ${localSettings.examMode ? 'active' : ''}`}
                    onClick={() => handleSettingChange('examMode', true)}
                  >
                    Exam Mode
                  </button>
                </div>
                <p className="setting-hint">
                  Exam mode uses fixed seed for reproducible responses.
                </p>
              </div>

              {/* Temperature */}
              <div className="setting-group">
                <label className="setting-label">
                  <Sliders size={18} />
                  Temperature
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
                  Higher values make responses more creative. Lower values make them more focused.
                </p>
              </div>

              {/* Top P */}
              <div className="setting-group">
                <label className="setting-label">
                  <Sliders size={18} />
                  Top P
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
                  Controls diversity via nucleus sampling.
                </p>
              </div>

              {/* Frequency Penalty */}
              <div className="setting-group">
                <label className="setting-label">
                  <Sliders size={18} />
                  Frequency Penalty
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
                  Reduces repetition of words. Higher values decrease repetition.
                </p>
              </div>

              {/* Presence Penalty */}
              <div className="setting-group">
                <label className="setting-label">
                  <Sliders size={18} />
                  Presence Penalty
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
                  Encourages talking about new topics.
                </p>
              </div>

              {/* Max Duration */}
              <div className="setting-group">
                <label className="setting-label">
                  Max Session Duration (minutes)
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
                  Maximum time allowed for a session.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="settings-section fade-in">
              {/* Theme */}
              <div className="setting-group">
                <label className="setting-label">
                  <Palette size={18} />
                  Theme
                </label>
                <div className="theme-options">
                  <button
                    className={`theme-option ${theme === 'light' ? 'active' : ''}`}
                    onClick={theme === 'dark' ? toggleTheme : undefined}
                  >
                    <Sun size={24} />
                    <span>Light Mode</span>
                  </button>
                  <button
                    className={`theme-option ${theme === 'dark' ? 'active' : ''}`}
                    onClick={theme === 'light' ? toggleTheme : undefined}
                  >
                    <Moon size={24} />
                    <span>Dark Mode</span>
                  </button>
                </div>
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
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            <Save size={18} />
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
