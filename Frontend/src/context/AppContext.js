import React, { createContext, useState, useContext, useEffect } from 'react';

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
      maxDuration: 15
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

  const startSession = (data) => {
    const session = {
      ...data,
      startTime: Date.now(),
      messages: [],
      tokenUsage: {
        input: 0,
        output: 0,
        total: 0
      }
    };
    setSessionData(session);
    return session;
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

  const endSession = () => {
    if (sessionData) {
      const completedSession = {
        ...sessionData,
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
