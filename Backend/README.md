# Virtual Patient Simulator Backend

## Overview
Flask-based backend API for the Virtual Patient Simulator that provides endpoints for:
- Document extraction
- Patient simulation chat
- Medical knowledge queries

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd C:\Users\acer\Desktop\IRPC_Internship\Virtual_Patient_Simulator\backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python app.py
   ```

Or simply run the batch file:
```bash
start_backend.bat
```

The server will start at http://localhost:5000

## API Endpoints

### Health Check
- **GET** `/health`
- Returns server status

### Document Extraction
- **POST** `/api/extract`
- Upload a medical document for information extraction
- Request: Form data with file
- Response: Extracted patient data in JSON

### Patient Simulator

#### Initialize Session
- **POST** `/api/simulator/initialize`
- Initialize a new patient simulation session
- Request body:
  ```json
  {
    "patientData": { ... }
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "sessionId": "unique-session-id"
  }
  ```

#### Chat with Patient
- **POST** `/api/simulator/chat`
- Send a message to the virtual patient
- Request body:
  ```json
  {
    "sessionId": "session-id",
    "message": "Doctor's question",
    "patientData": { ... }
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "response": "Patient's response"
  }
  ```

### Active Sessions
- **GET** `/api/sessions`
- Get list of active simulation sessions (for debugging)

## File Structure

```
backend/
├── app.py                    # Main Flask application (standalone)
├── app_enhanced.py          # Enhanced version with service integrations
├── requirements.txt         # Python dependencies
├── start_backend.bat       # Windows startup script
├── README.md               # This file
└── uploads/                # Directory for uploaded files (created automatically)
```

## Features

### Standalone Mode (app.py)
- Works independently without external services
- Uses mock data for testing
- Perfect for development and testing

### Enhanced Mode (app_enhanced.py)
- Integrates with existing services if available:
  - ExtractionService
  - PatientSimulatorService
  - MedicalKnowledgeService
- Falls back to mock data if services are unavailable

## CORS Configuration
CORS is enabled for all routes to allow frontend communication from different ports.

## Session Management
Sessions are stored in memory. In production, consider using:
- Redis for session storage
- Database for persistence
- Session timeout management

## Error Handling
- All endpoints include error handling with appropriate HTTP status codes
- Errors are logged for debugging
- Graceful fallback to mock data when services fail

## Development

### Running with Debug Mode
The server runs with debug mode enabled by default for development.

### Testing the API

1. Health check:
   ```bash
   curl http://localhost:5000/health
   ```

2. Upload a document:
   ```bash
   curl -X POST -F "file=@document.pdf" http://localhost:5000/api/extract
   ```

3. Initialize simulator:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"patientData": {...}}' \
     http://localhost:5000/api/simulator/initialize
   ```

## Integration with Frontend

The backend is designed to work seamlessly with the React frontend:
- Frontend runs on port 3000
- Backend runs on port 5000
- Frontend proxies API requests to backend

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, you can change it:
```bash
set PORT=5001
python app.py
```

### Module Import Errors
If you see import errors for services:
- The app will run in standalone mode with mock data
- This is normal if the service modules are not available

### CORS Issues
CORS is enabled by default. If you still face issues:
- Check that the frontend is using the correct backend URL
- Ensure no firewall is blocking the connection

## Next Steps

1. Integrate with actual ML models for extraction
2. Connect to LLM for more sophisticated patient responses
3. Add database for persistent storage
4. Implement user authentication
5. Add WebSocket support for real-time chat
