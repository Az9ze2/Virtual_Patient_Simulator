import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
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

  // Video recording state
  const [recordingBlob, setRecordingBlob] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingBlobRef = useRef(null); // Ref for immediate access

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
    // Use ref for immediate access to blob
    const currentBlob = recordingBlobRef.current || recordingBlob;
    console.log('📁 Ending session, recording blob:', currentBlob ? `${currentBlob.size} bytes` : 'none');
    
    if (sessionData && sessionData.sessionId) {
      try {
        const response = await apiService.endSession(sessionData.sessionId);
        
        if (response.success) {
          const completedSession = {
            ...sessionData,
            ...response.data.summary,
            endTime: Date.now(),
            duration: Date.now() - sessionData.startTime,
            recordingBlob: currentBlob // Use ref blob
          };
          console.log('✅ Session completed with recording blob:', completedSession.recordingBlob ? `${completedSession.recordingBlob.size} bytes` : 'none');
          
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
      const currentBlob = recordingBlobRef.current || recordingBlob;
      const completedSession = {
        ...sessionData,
        endTime: Date.now(),
        duration: Date.now() - sessionData.startTime,
        recordingBlob: currentBlob // Use ref blob
      };
      console.log('✅ Session completed (fallback) with recording blob:', completedSession.recordingBlob ? `${completedSession.recordingBlob.size} bytes` : 'none');
      
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
    setRecordingBlob(null);
    recordingBlobRef.current = null;
  };

  const saveRecording = (blob) => {
    setRecordingBlob(blob);
  };

  // Recording control functions
  const startRecording = async () => {
    try {
      // Request camera permission
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: true
      });

      streamRef.current = stream;
      chunksRef.current = [];

      // Create MediaRecorder
      const options = { mimeType: 'video/webm;codecs=vp9' };
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'video/webm;codecs=vp8';
      }
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'video/webm';
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: options.mimeType });
        recordingBlobRef.current = blob; // Store in ref immediately
        setRecordingBlob(blob); // Also update state for UI
        setIsRecording(false);
        console.log('✅ Recording stopped and saved, blob size:', blob.size);
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setIsRecording(false);
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
      console.log('📹 Recording started successfully');
      return { success: true };
    } catch (err) {
      console.error('Start recording error:', err);
      let errorMessage = 'Failed to access camera';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera permission denied';
      }
      return { success: false, error: errorMessage };
    }
  };

  const stopRecording = () => {
    return new Promise((resolve) => {
      console.log('📹 Attempting to stop recording...');
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        // Set up one-time listener for when recording stops
        const handleStop = () => {
          console.log('📹 Stop event fired, blob will be available shortly');
          // Give a small delay for the onstop callback to complete
          setTimeout(() => {
            resolve({ success: true });
          }, 100);
        };
        
        mediaRecorderRef.current.addEventListener('stop', handleStop, { once: true });
        mediaRecorderRef.current.stop();
        
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      } else {
        console.warn('⚠️ No active recording to stop');
        resolve({ success: false });
      }
    });
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
    clearSession,
    recordingBlob,
    saveRecording,
    isRecording,
    startRecording,
    stopRecording
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};