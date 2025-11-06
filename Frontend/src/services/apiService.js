import axios from 'axios';

class ApiService {
  constructor() {
    // Determine API base URL based on environment
    const getApiUrl = () => {
      // Check if we have an explicit API URL set
      if (process.env.REACT_APP_API_URL) {
        return process.env.REACT_APP_API_URL;
      }
      
      // Fallback based on NODE_ENV
      if (process.env.NODE_ENV === 'production') {
        // In production, this should be set via environment variables
        return 'https://your-railway-app.railway.app'; // Replace with your actual Railway URL
      } else {
        // Local development
        return 'http://localhost:8000';
      }
    };

    this.baseURL = getApiUrl();

    // Set up axios defaults
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 60000, // Increased to 1 minute for regular operations
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Log the API URL being used (helpful for debugging)
    console.log('🌐 API Base URL:', this.baseURL);

    // Add request interceptor for logging
    this.api.interceptors.request.use(
      (config) => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          data: config.data,
          params: config.params
        });
        return config;
      },
      (error) => {
        console.error('🚨 Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.api.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data
        });
        return response;
      },
      (error) => {
        console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
        if (error.response) {
          // Server responded with error status
          throw new Error(error.response.data?.details || error.response.data?.error || 'API request failed');
        } else if (error.request) {
          // Network error
          throw new Error('Network error. Please check if the backend server is running.');
        } else {
          // Other error
          throw new Error(error.message || 'Unknown error occurred');
        }
      }
    );
  }

  // ============================================
  // Health Check
  // ============================================
  
  async healthCheck() {
    const response = await this.api.get('/health');
    return response.data;
  }

  // ============================================
  // Test Endpoints
  // ============================================
  
  async testFilename() {
    try {
      console.log('🧪 Testing filename header transmission...');
      
      const response = await this.api.get('/test-filename', {
        responseType: 'blob'
      });
      
      console.log('🧪 Test response headers:', response.headers);
      console.log('🧪 Content-Disposition:', response.headers['content-disposition']);
      
      // Try to extract filename using same logic as downloadReport
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'test_fallback.txt';
      
      if (contentDisposition) {
        const patterns = [
          /filename="([^"]+)"/,
          /filename=([^;\s]+)/,
          /filename='([^']+)'/
        ];
        
        for (let i = 0; i < patterns.length; i++) {
          const match = contentDisposition.match(patterns[i]);
          if (match && match[1]) {
            filename = match[1].trim();
            console.log(`🧪 Test extracted filename: ${filename}`);
            break;
          }
        }
      }
      
      return { success: true, filename, headers: response.headers };
    } catch (error) {
      console.error('🧪 Test filename failed:', error);
      return { success: false, error: error.message };
    }
  }

  // ============================================
  // Cases API
  // ============================================
  
  async getCases() {
    const response = await this.api.get('/api/cases/list');
    return response.data;
  }

  async getCaseCategories() {
    const response = await this.api.get('/api/cases/categories');
    return response.data;
  }

  async getCaseData(filename) {
    const response = await this.api.get(`/api/cases/get/${filename}`);
    return response.data;
  }

  // ============================================
  // Sessions API
  async preLogin(userInfo) {
    const response = await this.api.post('/api/sessions/prelogin', {
      user_info: userInfo,
      case_filename: ''
    });
    return response.data;
  }

  async startSession(userInfo, caseFilename, config = {}) {
    const response = await this.api.post('/api/sessions/start', {
      user_info: userInfo,
      case_filename: caseFilename,
      config: config
    });
    return response.data;
  }

  async startSessionWithUploadedCase(userInfo, caseData, config = {}) {
    const response = await this.api.post('/api/sessions/start-uploaded-case', {
      user_info: userInfo,
      case_data: caseData,
      config: config
    });
    return response.data;
  }

  async getSessionInfo(sessionId) {
    const response = await this.api.get(`/api/sessions/info/${sessionId}`);
    return response.data;
  }

  async updateDiagnosis(sessionId, diagnosisData) {
    const response = await this.api.put(`/api/sessions/${sessionId}/diagnosis`, diagnosisData);
    return response.data;
  }

  async endSession(sessionId) {
    const response = await this.api.post(`/api/sessions/${sessionId}/end`);
    return response.data;
  }

  async downloadReport(sessionId) {
    try {
      console.log(`📥 Starting download for session: ${sessionId}`);
      
      const response = await this.api.get(`/api/sessions/${sessionId}/download`, {
        responseType: 'blob'
      });
      
      // Get content type from response headers
      const contentType = response.headers['content-type'] || 'application/pdf';
      console.log(`📄 Response content type: ${contentType}`);
      console.log(`📊 Response data size: ${response.data.size} bytes`);
      
      // Validate that we have data
      if (!response.data || response.data.size === 0) {
        throw new Error('Received empty file from server');
      }
      
      // Create download link with correct content type
      const url = window.URL.createObjectURL(new Blob([response.data], { type: contentType }));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'session_report.pdf';
      
      console.log(`📋 ALL RESPONSE HEADERS:`, response.headers);
      console.log(`📋 Content-Disposition (raw):`, contentDisposition);
      
      if (contentDisposition) {
        console.log(`🔎 Content-Disposition header: ${contentDisposition}`);
        
        // Simple pattern matching for filename="..." format
        const patterns = [
          /filename="([^"]+)"/,  // filename="name.pdf"
          /filename=([^;\s]+)/,   // filename=name.pdf
          /filename='([^']+)'/    // filename='name.pdf'
        ];
        
        let matched = false;
        for (let i = 0; i < patterns.length; i++) {
          const match = contentDisposition.match(patterns[i]);
          console.log(`🔍 Pattern ${i + 1} (${patterns[i]}) result:`, match);
          
          if (match && match[1]) {
            filename = match[1].trim();
            console.log(`✅ Successfully extracted filename: ${filename}`);
            matched = true;
            break;
          }
        }
        
        if (!matched) {
          console.log(`⚠️ No filename pattern matched in Content-Disposition header!`);
        }
      } else {
        // Fallback filename based on content type
        filename = contentType.includes('html') ? 'session_report.html' : 'session_report.pdf';
        console.log(`📄 No Content-Disposition header, using fallback: ${filename}`);
      }
      
      console.log(`💾 Downloading as: ${filename}`);
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      console.log(`✅ Download completed successfully: ${filename}`);
      return { success: true, filename };
      
    } catch (error) {
      console.error(`❌ Download failed for session ${sessionId}:`, error);
      throw error;
    }
  }

  async deleteSession(sessionId) {
    const response = await this.api.delete(`/api/sessions/${sessionId}`);
    return response.data;
  }

  async getActiveSessions() {
    const response = await this.api.get('/api/sessions/active');
    return response.data;
  }

  async getUserSessions(studentId) {
    const response = await this.api.post('/api/sessions/my-sessions', {
      student_id: studentId
    });
    return response.data;
  }

  // Chatbot API
  // ============================================
  
  async sendMessage(sessionId, message) {
    const response = await this.api.post(`/api/chatbot/${sessionId}/chat`, {
      message: message
    });
    return response.data;
  }

  async getPatientInfo(sessionId) {
    const response = await this.api.get(`/api/chatbot/${sessionId}/patient-info`);
    return response.data;
  }

  async getChatHistory(sessionId) {
    const response = await this.api.get(`/api/chatbot/${sessionId}/chat-history`);
    return response.data;
  }

  async getTokenUsage(sessionId) {
    const response = await this.api.get(`/api/chatbot/${sessionId}/token-usage`);
    return response.data;
  }

  async getChatbotStatus(sessionId) {
    const response = await this.api.get(`/api/chatbot/${sessionId}/chatbot-status`);
    return response.data;
  }

  // ============================================
  // Documents API
  // ============================================
  
  async uploadDocument(file, onUploadProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes timeout for ChatGPT processing
    };
    
    if (onUploadProgress) {
      config.onUploadProgress = onUploadProgress;
    }

    const response = await this.api.post('/api/documents/upload', formData, config);
    return response.data;
  }

  async verifyAndSaveData(extractedData, verified, corrections = null) {
    const formData = new FormData();
    formData.append('extracted_data', JSON.stringify(extractedData));
    formData.append('verified', verified.toString());
    
    if (corrections) {
      formData.append('corrections', JSON.stringify(corrections));
    }

    const response = await this.api.post('/api/documents/verify-and-save', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getExtractionSchema() {
    const response = await this.api.get('/api/documents/schema');
    return response.data;
  }

  async getExtractionPrompt() {
    const response = await this.api.get('/api/documents/extraction-prompt');
    return response.data;
  }

  async downloadCaseTemplate() {
    const response = await this.api.get('/api/documents/download-template', {
      responseType: 'blob'
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'case_template.json');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  }

  // ============================================
  // Configuration API
  // ============================================
  
  async getDefaultConfig() {
    const response = await this.api.get('/api/config/default');
    return response.data;
  }

  async getAvailableModels() {
    const response = await this.api.get('/api/config/models');
    return response.data;
  }

  async getMemoryModes() {
    const response = await this.api.get('/api/config/memory-modes');
    return response.data;
  }

  async getSessionConfig(sessionId) {
    const response = await this.api.get(`/api/config/${sessionId}`);
    return response.data;
  }

  async updateSessionConfig(sessionId, configUpdate) {
    const response = await this.api.put(`/api/config/${sessionId}`, configUpdate);
    return response.data;
  }

  async validateConfig(config) {
    const response = await this.api.post('/api/config/validate', config);
    return response.data;
  }

  async getConfigPresets() {
    const response = await this.api.get('/api/config/presets/list');
    return response.data;
  }
  
  // ============================================
  // 📊 Enhanced Text-to-Speech API (OPTIMIZED)
  // ============================================
  
  /**
   * Send message with TTS - Auto-selects voice based on patient info
   * OPTIMIZED: Natural Thai pronunciation + Child patient handling
   * @param {string} sessionId - Session ID
   * @param {string} message - User message
   * @param {boolean} enableTTS - Enable TTS audio (default: true)
   * @param {string|null} voice - Voice override (null = auto-select based on patient)
   * @param {number} speed - Speech speed 0.25-4.0 (default: 1)
   * @returns {Promise<Object>} Response with text and optional audio + speaker role info
   */
  async sendMessageWithTTS(sessionId, message, enableTTS = true, voice = null, speed = 1) {
    const response = await this.api.post(`/api/chatbot/${sessionId}/chat-with-tts`, {
      message: message,
      enable_tts: enableTTS,
      voice: voice, // null = auto-select (mother for children <12)
      tts_speed: speed
    });
    return response.data;
  }

  /**
   * Generate TTS with patient context (Enhanced & Optimized)
   * Automatically selects voice based on patient gender and age
   * Special handling: Children <12 years = Mother speaks
   * @param {string} text - Text to convert to speech
   * @param {Object} patientInfo - Patient information for voice selection
   * @param {Object} caseMetadata - Optional case metadata for context
   * @param {string|null} voice - Voice override (null = auto-select)
   * @param {number} speed - Speech speed (default: 1)
   * @param {boolean} usePersonality - Enable personality enhancement (default: true)
   * @returns {Promise<Object>} Response with audio data and voice info
   */
  async generateTTSWithContext(text, patientInfo, caseMetadata = null, voice = null, speed = 1, usePersonality = true) {
    const response = await this.api.post('/api/tts/generate-with-context', {
      text: text,
      patient_info: patientInfo,
      case_metadata: caseMetadata,
      voice: voice,
      model: 'gpt-4o-mini-tts',
      speed: speed,
      format: 'mp3',
      use_personality_prompt: usePersonality
    });
    return response.data;
  }

  /**
   * Generate basic TTS without patient context (Backward compatible)
   * @param {string} text - Text to convert
   * @param {string} voice - Voice name (alloy, echo, fable, onyx, nova, shimmer)
   * @param {string} model - TTS model (default: gpt-4o-mini-tts)
   * @param {number} speed - Speech speed (default: 1)
   * @param {string} format - Audio format (mp3, opus, aac, flac)
   */
  async generateTTS(text, voice = 'nova', model = 'gpt-4o-mini-tts', speed = 1, format = 'mp3') {
    const response = await this.api.post('/api/tts/generate', {
      text: text,
      voice: voice,
      model: model,
      speed: speed,
      format: format
    });
    return response.data;
  }

  /**
   * Get available TTS voices with descriptions
   * @returns {Promise<Object>} List of voices with descriptions
   */
  async getTTSVoices() {
    const response = await this.api.get('/api/tts/voices');
    return response.data;
  }

  /**
   * Get voice profile mappings for patient demographics
   * Shows which voices are selected for different patient types
   * Includes special rules for child patients
   * @returns {Promise<Object>} Voice profile mappings with special conditions
   */
  async getTTSVoiceProfiles() {
    const response = await this.api.get('/api/tts/voice-profiles');
    return response.data;
  }

  /**
   * Get TTS health status with enhanced features
   * @returns {Promise<Object>} Service health and available features
   */
  async getTTSHealth() {
    const response = await this.api.get('/api/tts/health');
    return response.data;
  }

  // ============================================
  // Admin API
  // ============================================
  async adminLogin(loginData) {
    const response = await this.api.post('/api/admin/login', loginData);
    return response.data;
  }

  async adminLogout(userId, isAdmin) {
    const response = await this.api.post('/api/admin/logout', {
      user_id: userId,
      is_admin: isAdmin
    });
    return response.data;
  }

  async getAdminStats() {
    const response = await this.api.get('/api/admin/stats');
    return response.data;
  }

  async getAuditLogs(limit = 50) {
    const response = await this.api.get('/api/admin/audit-logs', {
      params: { limit }
    });
    return response.data;
  }

  async getAdminSessions(limit = 50) {
    const response = await this.api.get('/api/admin/sessions', {
      params: { limit }
    });
    return response.data;
  }

  async getAdminUsers(limit = 50) {
    const response = await this.api.get('/api/admin/users', {
      params: { limit }
    });
    return response.data;
  }

  async getAdminMessages(limit = 50) {
    const response = await this.api.get('/api/admin/messages', {
      params: { limit }
    });
    return response.data;
  }

  async executeQuery(query, adminId, adminPassword = null) {
    const payload = {
      query,
      admin_id: adminId
    };
    if (adminPassword) {
      payload.admin_password = adminPassword;
    }
    const response = await this.api.post('/api/admin/execute-query', payload);
    return response.data;
  }

  async getAdminCases(limit = 100) {
    const response = await this.api.get('/api/admin/cases', {
      params: { limit }
    });
    return response.data;
  }

  async getHomeStats() {
    const response = await this.api.get('/api/admin/home-stats');
    return response.data;
  }

  // ============================================
  // Speech-to-Text API
  // ============================================
  /**
   * Transcribe audio with optional correction and conversation context
   * @param {Blob} audioBlob - Audio blob from MediaRecorder
   * @param {string|null} conversationContext - Recent conversation for context-aware correction
   * @param {boolean|null} enableCorrection - Override global correction setting
   * @returns {Promise<Object>} Transcription result with correction metadata
  */
  async transcribeAudioWithContext(audioBlob, conversationContext = null, enableCorrection = null) {
    try {
      console.log('🎤 Starting context-aware audio transcription...');
      console.log('📊 Audio blob size:', audioBlob.size, 'bytes');
      console.log('🧠 Context provided:', conversationContext ? 'YES' : 'NO');
      console.log('🔧 Correction:', enableCorrection === null ? 'DEFAULT' : enableCorrection ? 'ENABLED' : 'DISABLED');
      
      if (audioBlob.size < 5000) {
        console.warn('⚠️ Audio blob too small:', audioBlob.size, 'bytes');
        throw new Error('ไฟล์เสียงเล็กเกินไป กรุณาบันทึกเสียงให้ยาวขึ้น');
      }
      
      // Create FormData with audio and optional parameters
      const formData = new FormData();
      
      // Determine filename based on MIME type
      let filename = 'recording.webm';
      if (audioBlob.type.includes('mp4')) {
        filename = 'recording.mp4';
      } else if (audioBlob.type.includes('ogg')) {
        filename = 'recording.ogg';
      } else if (audioBlob.type.includes('wav')) {
        filename = 'recording.wav';
      }
      
      formData.append('audio', audioBlob, filename);
      
      // Add conversation context if provided
      if (conversationContext) {
        formData.append('conversation_context', conversationContext);
      }
      
      // Add correction override if specified
      if (enableCorrection !== null) {
        formData.append('enable_correction', enableCorrection.toString());
      }
      
      console.log('📤 Sending to:', `${this.baseURL}/api/stt/transcribe`);
      const startTime = performance.now();

      // Send request with extended timeout
      const response = await this.api.post('/api/stt/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes
      });

      const elapsedTime = performance.now() - startTime;
      console.log(`✅ Transcription complete in ${elapsedTime.toFixed(0)}ms`);
      console.log('📝 Response:', response.data);
      
      // Log correction results if available
      if (response.data.data?.correction) {
        const correction = response.data.data.correction;
        console.log('🧠 Correction applied:', correction.was_corrected ? 'YES' : 'NO');
        if (correction.was_corrected) {
          console.log('   Original:', correction.original_text);
          console.log('   Corrected:', correction.corrected_text);
        }
      }
      
      return response.data;
      
    } catch (error) {
      console.error('🚨 Transcription API Error:', error);
      
      // Enhanced error handling
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        
        if (typeof detail === 'object') {
          if (detail.error === 'silent_audio') {
            throw new Error(detail.message || 'ไม่พบเสียงพูดในการบันทึก');
          } else if (detail.error === 'audio_too_short') {
            throw new Error(detail.message || 'เสียงที่บันทึกสั้นเกินไป');
          } else if (detail.message) {
            throw new Error(detail.message);
          }
        } else if (typeof detail === 'string') {
          throw new Error(detail);
        }
      }
      
      if (error.response?.status === 400) {
        throw new Error('ข้อมูลเสียงไม่ถูกต้อง กรุณาลองบันทึกใหม่');
      } else if (error.response?.status === 429) {
        throw new Error('มีการใช้งานมากเกินไป กรุณารอสักครู่');
      } else if (error.response?.status === 500) {
        throw new Error('เกิดข้อผิดพลาดของระบบ กรุณาลองอีกครั้ง');
      }
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        throw new Error('หมดเวลาในการประมวลผลเสียง กรุณาลองอีกครั้ง');
      }
      
      if (error.message.includes('Network error') || error.code === 'ERR_NETWORK') {
        throw new Error('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย');
      }
      
      throw new Error(error.message || 'เกิดข้อผิดพลาดในการแปลงเสียง');
    }
  }

  /**
   * Get STT configuration and status
   * @returns {Promise<Object>} Current STT configuration
   */
  async getSTTConfig() {
    try {
      const response = await this.api.get('/api/stt/status');
      return response.data;
    } catch (error) {
      console.error('Error getting STT config:', error);
      throw error;
    }
  }

  /**
   * Update STT configuration at runtime
   * @param {Object} config - Configuration updates
   * @example
   * updateSTTConfig({
   *   enable_correction: true,
   *   correction_model: "gpt-4o-mini",
   *   correction_temperature: 0.1
   * })
   */
  async updateSTTConfig(config) {
    try {
      const response = await this.api.post('/api/stt/config', config);
      return response.data;
    } catch (error) {
      console.error('Error updating STT config:', error);
      throw error;
    }
  }

  // ============================================
  // 🧠 UTILITY: Build Conversation Context
  // ============================================
  
  /**
   * Build conversation context for better AI corrections
   * @param {Array} chatHistory - Recent chat messages
   * @param {Object} caseData - Current case information
   * @returns {string} Context string for correction AI
   */
  buildConversationContext(chatHistory, caseData) {
    try {
      // Take last 5 messages for context (not too much, not too little)
      const recentMessages = (chatHistory || []).slice(-5);
      
      let context = '';
      
      // Add case metadata for medical context
      if (caseData && caseData.case_metadata) {
        context += `Medical Case: ${caseData.case_metadata.case_title || 'Unknown'}\n`;
        context += `Specialty: ${caseData.case_metadata.medical_specialty || 'General'}\n`;
        
        // Add chief complaint for better medical term detection
        if (caseData.chief_complaint) {
          context += `Chief Complaint: ${caseData.chief_complaint}\n`;
        }
        
        context += '\n';
      }
      
      // Add recent conversation for context
      if (recentMessages.length > 0) {
        context += 'Recent conversation:\n';
        recentMessages.forEach(msg => {
          const role = msg.role === 'user' ? 'Doctor' : 'Patient';
          // Truncate long messages to keep context focused
          const content = msg.content.length > 150 
            ? msg.content.substring(0, 150) + '...'
            : msg.content;
          context += `${role}: ${content}\n`;
        });
      }
      
      console.log('🧠 Built conversation context:', context.length, 'characters');
      return context;
      
    } catch (error) {
      console.error('Error building conversation context:', error);
      return ''; // Return empty string on error, don't crash
    }
  }
}

// Create and export singleton instance
const apiService = new ApiService();
export default apiService;