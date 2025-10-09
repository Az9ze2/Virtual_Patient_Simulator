# Virtual Patient Simulator - FastAPI Backend

This is the backend API for the Virtual Patient Simulator application, built with FastAPI. It provides RESTful endpoints for managing patient simulation sessions, case data, document processing, and configuration.

## Features

- **Session Management**: Create, manage, and track patient simulation sessions
- **Case Management**: List and load case files from cases_01 (child) and cases_02 (adult) folders  
- **Chatbot Integration**: Interface with the unified chatbot system for realistic patient interactions
- **Document Processing**: Upload and extract case data from PDF/DOCX documents
- **Configuration Management**: Adjust model parameters, temperature, and other settings
- **Token Tracking**: Monitor API usage and costs
- **Report Generation**: Download session reports and summaries

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the Backend directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start the Server

```bash
# Using the startup script (recommended)
python start_api.py

# Or directly with uvicorn
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **Main API**: http://127.0.0.1:8000
- **Interactive Documentation**: http://127.0.0.1:8000/docs
- **ReDoc Documentation**: http://127.0.0.1:8000/redoc

## API Endpoints

### Core Endpoints

- `GET /` - API status and version info
- `GET /health` - Health check endpoint

### Cases (`/api/cases`)

- `GET /list` - List all available cases
- `GET /categories` - Get case categories and counts
- `GET /get/{filename}` - Get full case data for a specific file

### Sessions (`/api/sessions`)

- `POST /start` - Start a new simulation session
- `GET /info/{session_id}` - Get session information
- `PUT /{session_id}/diagnosis` - Update diagnosis and treatment notes
- `POST /{session_id}/end` - End session and generate summary
- `GET /{session_id}/download` - Download session report
- `DELETE /{session_id}` - Delete session from memory
- `GET /active` - List active sessions

### Chatbot (`/api/chatbot`)

- `POST /{session_id}/chat` - Send message to chatbot
- `GET /{session_id}/patient-info` - Get patient information for examiner
- `GET /{session_id}/chat-history` - Get chat history
- `GET /{session_id}/token-usage` - Get current token usage
- `GET /{session_id}/chatbot-status` - Get chatbot configuration and status

### Documents (`/api/documents`)

- `POST /upload` - Upload and process document
- `POST /verify-and-save` - Verify extracted data and save as case
- `GET /schema` - Get extraction schema
- `GET /extraction-prompt` - Get extraction prompt
- `GET /download-template` - Download case template

### Configuration (`/api/config`)

- `GET /default` - Get default configuration
- `GET /models` - List available models
- `GET /memory-modes` - List memory management modes
- `GET /{session_id}` - Get session configuration
- `PUT /{session_id}` - Update session configuration
- `POST /validate` - Validate configuration
- `GET /presets/list` - Get configuration presets

## Usage Examples

### Starting a Session

```javascript
// 1. Get available cases
const casesResponse = await fetch('/api/cases/list');
const cases = await casesResponse.json();

// 2. Start session
const sessionData = {
    user_info: {
        name: "John Doe",
        student_id: "STU001"
    },
    case_filename: "01_01_breast_feeding_problems.json",
    config: {
        model_choice: "gpt-4.1-mini",
        temperature: 0.7,
        memory_mode: "summarize",
        exam_mode: false
    }
};

const sessionResponse = await fetch('/api/sessions/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sessionData)
});

const session = await sessionResponse.json();
const sessionId = session.data.session_id;
```

### Chatbot Interaction

```javascript
// Send message to chatbot
const messageData = { message: "วันนี้มีเรื่องอะไรให้ช่วยคะ" };

const chatResponse = await fetch(`/api/chatbot/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(messageData)
});

const response = await chatResponse.json();
console.log('Bot response:', response.data.response);
```

### Document Upload

```javascript
// Upload document for processing
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('/api/documents/upload', {
    method: 'POST',
    body: formData
});

const extractedData = await uploadResponse.json();
```

## Frontend Integration

The API is designed to work with your React frontend following this workflow:

### 1. Home Page Flow
- User enters name and student ID (stored temporarily)
- Fetch available cases: `GET /api/cases/list`
- Display case options grouped by type
- Start session: `POST /api/sessions/start`

### 2. Chat Interface Flow
- Get patient info: `GET /api/chatbot/{session_id}/patient-info`
- Send chat messages: `POST /api/chatbot/{session_id}/chat`
- Update diagnosis: `PUT /api/sessions/{session_id}/diagnosis`
- Monitor token usage: `GET /api/chatbot/{session_id}/token-usage`

### 3. Session End Flow
- End session: `POST /api/sessions/{session_id}/end`
- Download report: `GET /api/sessions/{session_id}/download`
- Return to home page

### 4. Document Upload Flow
- Upload document: `POST /api/documents/upload`
- Show extracted data for verification
- Save verified data: `POST /api/documents/verify-and-save`

### 5. Settings Flow
- Get available options: `GET /api/config/models`, `GET /api/config/memory-modes`
- Update session config: `PUT /api/config/{session_id}`

## Configuration Options

### Models
- **gpt-4.1-mini**: Tunable model with temperature control
- **gpt-5**: Deterministic model with limited parameters

### Memory Modes  
- **none**: Keep all conversation history
- **truncate**: Remove oldest messages when limit reached
- **summarize**: Compress old conversation into summaries (recommended)

### Other Settings
- **Temperature**: 0.0-2.0 (creativity level, GPT-4.1-mini only)
- **Exam Mode**: Fixed seed for reproducible results

## Error Handling

All endpoints return standardized responses:

**Success:**
```json
{
    "success": true,
    "message": "Operation completed successfully",
    "data": { ... }
}
```

**Error:**
```json
{
    "success": false,
    "error": "Error Type",
    "details": "Detailed error message"
}
```

## Project Structure

```
Backend/
├── api/
│   ├── app.py              # Main FastAPI application
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   ├── routers/
│   │   ├── cases.py        # Case management endpoints
│   │   ├── sessions.py     # Session management endpoints
│   │   ├── chatbot.py      # Chatbot interaction endpoints
│   │   ├── documents.py    # Document processing endpoints
│   │   └── config.py       # Configuration endpoints
│   └── utils/
│       ├── session_manager.py    # In-memory session storage
│       └── error_handling.py     # Error handling utilities
├── src/                    # Shared source code (unified_chatbot.py, etc.)
├── requirements.txt        # Python dependencies
├── start_api.py           # Startup script
└── API_README.md          # This file
```

## Development Notes

- **No Database**: All data stored in memory (sessions are temporary)
- **CORS Enabled**: Configured for React development on port 3000
- **Auto-Reload**: Development server reloads on code changes
- **Type Safety**: Full Pydantic validation for all inputs/outputs
- **Interactive Docs**: Built-in Swagger UI at `/docs`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes the src directory
2. **OpenAI API Key**: Verify `.env` file exists with valid key
3. **Port Conflicts**: API runs on port 8000 by default
4. **CORS Issues**: Frontend should run on port 3000 for default CORS config

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
python start_api.py
```

## Support

- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **Error Logs**: Check console output for detailed error messages
