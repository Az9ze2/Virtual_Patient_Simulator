import React, { createContext, useState, useContext, useEffect } from 'react';
import apiService from '../services/apiService';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  // Theme management
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved || 'light';
  });

  // Settings
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('settings');
    return saved ? JSON.parse(saved) : {
      model: 'gpt-4.1-mini',
      temperature: 0.7,
      topP: 0.85,
      frequencyPenalty: 0.6,
      presencePenalty: 0.9,
      memoryMode: 'summarize',
      examMode: false,
      autoSave: true,
      showTimer: true,
      maxDuration: 15,
      uiScale: 0.8 // ✅ Add UI scale default
    };
  });

  // Session data
  const [sessionData, setSessionData] = useState(() => {
    const saved = localStorage.getItem('currentSession');
    return saved ? JSON.parse(saved) : null;
  });

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // ✅ Apply UI scale
  useEffect(() => {
    document.documentElement.style.setProperty('--ui-scale', settings.uiScale || 0.8);
  }, [settings.uiScale]);

  // Save settings
  useEffect(() => {
    localStorage.setItem('settings', JSON.stringify(settings));
  }, [settings]);

  // Save session data
  useEffect(() => {
    if (sessionData) {
      localStorage.setItem('currentSession', JSON.stringify(sessionData));
    } else {
      localStorage.removeItem('currentSession');
    }
  }, [sessionData]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const updateSettings = (newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const startSession = async (userInfo, caseFilename, config = {}) => {
    try {
      // Convert frontend settings to backend config format
      const backendConfig = {
        model_choice: config.model || settings.model,
        memory_mode: config.memoryMode || settings.memoryMode, 
        temperature: config.temperature || settings.temperature,
        exam_mode: config.examMode || settings.examMode
      };

      const response = await apiService.startSession(userInfo, caseFilename, backendConfig);
      
      if (response.success) {
        const session = {
          sessionId: response.data.session_id,
          userInfo: userInfo,
          caseInfo: response.data.case_info,
          caseData: {
            examiner_view: response.data.examiner_view
          },
          config: backendConfig,
          startTime: Date.now(),
          messages: [],
          tokenUsage: {
            inputTokens: 0,    // ✅ Fixed property names
            outputTokens: 0,   // ✅ Fixed property names
            totalTokens: 0     // ✅ Fixed property names
          },
          isUploadedCase: false
        };
        
        setSessionData(session);
        return session;
      } else {
        throw new Error(response.error || 'Failed to start session');
      }
    } catch (error) {
      console.error('Failed to start session:', error);
      throw error;
    }
  };

  const startSessionWithUploadedCase = async (userInfo, caseData, config = {}) => {
    try {
      // Convert frontend settings to backend config format
      const backendConfig = {
        model_choice: config.model || settings.model,
        memory_mode: config.memoryMode || settings.memoryMode, 
        temperature: config.temperature || settings.temperature,
        exam_mode: config.examMode || settings.examMode
      };

      const response = await apiService.startSessionWithUploadedCase(userInfo, caseData, backendConfig);
      
      if (response.success) {
        const session = {
          sessionId: response.data.session_id,
          userInfo: userInfo,
          caseInfo: response.data.case_info,
          caseData: {
            examiner_view: response.data.examiner_view
          },
          config: backendConfig,
          startTime: Date.now(),
          messages: [],
          tokenUsage: {
            inputTokens: 0,    // ✅ Fixed property names
            outputTokens: 0,   // ✅ Fixed property names
            totalTokens: 0     // ✅ Fixed property names
          },
          isUploadedCase: true,
          uploadedCaseData: caseData
        };
        
        setSessionData(session);
        return session;
      } else {
        throw new Error(response.error || 'Failed to start session with uploaded case');
      }
    } catch (error) {
      console.error('Failed to start session with uploaded case:', error);
      throw error;
    }
  };

  const updateSession = (updates) => {
    setSessionData(prev => prev ? { ...prev, ...updates } : null);
  };

  const addMessage = (message) => {
    setSessionData(prev => {
      if (!prev) return null;
      return {
        ...prev,
        messages: [...prev.messages, {
          ...message,
          timestamp: Date.now()
        }]
      };
    });
  };

  const endSession = async () => {
    if (sessionData && sessionData.sessionId) {
      try {
        const response = await apiService.endSession(sessionData.sessionId);
        
        if (response.success) {
          const completedSession = {
            ...sessionData,
            ...response.data.summary,
            endTime: Date.now(),
            duration: Date.now() - sessionData.startTime
          };
          
          // Save to session history
          const history = JSON.parse(localStorage.getItem('sessionHistory') || '[]');
          history.unshift(completedSession);
          localStorage.setItem('sessionHistory', JSON.stringify(history.slice(0, 10))); // Keep last 10
          
          setSessionData(null);
          return completedSession;
        }
      } catch (error) {
        console.error('Failed to end session:', error);
      }
    }
    
    // Fallback for local session end
    if (sessionData) {
      const completedSession = {
        ...sessionData,
        endTime: Date.now(),
        duration: Date.now() - sessionData.startTime
      };
      
      const history = JSON.parse(localStorage.getItem('sessionHistory') || '[]');
      history.unshift(completedSession);
      localStorage.setItem('sessionHistory', JSON.stringify(history.slice(0, 10)));
      
      setSessionData(null);
      return completedSession;
    }
    return null;
  };

  const clearSession = () => {
    setSessionData(null);
  };

  const value = {
    theme,
    toggleTheme,
    settings,
    updateSettings,
    sessionData,
    startSession,
    startSessionWithUploadedCase,
    updateSession,
    addMessage,
    endSession,
    clearSession
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};