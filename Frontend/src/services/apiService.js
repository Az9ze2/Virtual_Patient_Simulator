import axios from 'axios';

class ApiService {
  constructor() {
    // Set up axios defaults
    this.api = axios.create({
      baseURL: process.env.NODE_ENV === 'production' ? 'http://localhost:8000' : '',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

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

  // Health check
  async healthCheck() {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Cases API
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

  // Sessions API
  async startSession(userInfo, caseFilename, config = {}) {
    const response = await this.api.post('/api/sessions/start', {
      user_info: userInfo,
      case_filename: caseFilename,
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
    const response = await this.api.get(`/api/sessions/${sessionId}/download`, {
      responseType: 'blob'
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Extract filename from response headers or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'session_report.json';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+)"?/);
      if (match) filename = match[1];
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true, filename };
  }

  async deleteSession(sessionId) {
    const response = await this.api.delete(`/api/sessions/${sessionId}`);
    return response.data;
  }

  async getActiveSessions() {
    const response = await this.api.get('/api/sessions/active');
    return response.data;
  }

  // Chatbot API
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

  // Documents API
  async uploadDocument(file, onUploadProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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

  // Configuration API
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
}

// Create and export singleton instance
const apiService = new ApiService();
export default apiService;
