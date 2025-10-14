#!/usr/bin/env python3
"""
Virtual Patient Simulator - FastAPI Backend
Handles frontend-backend communication for the virtual patient simulator
"""

import os
import sys
import time
import json
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import routers
from routers import sessions, chatbot, cases, documents, config

# Import session manager for cleanup
from utils.session_manager import session_manager

# Import error handlers
from utils.error_handling import (
    validation_exception_handler,
    http_exception_handler, 
    general_exception_handler
)

# Request Logging Middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get request info
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Read request body for POST/PUT requests
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = json.loads(body_bytes.decode())
                    # Recreate request with body
                    request = Request(request.scope, receive=lambda: {"type": "http.request", "body": body_bytes})
            except:
                body = "<non-JSON body>"
        
        print(f"\n🚀 [{timestamp}] {method} {url}")
        print(f"   🌍 Client: {client_ip}")
        if body:
            print(f"   📄 Body: {json.dumps(body, indent=2, ensure_ascii=False) if isinstance(body, dict) else body}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if 200 <= response.status_code < 300 else "🟡" if 300 <= response.status_code < 400 else "❌"
            print(f"   {status_emoji} Status: {response.status_code} | Time: {process_time:.3f}s")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            print(f"   ❌ Error: {str(e)} | Time: {process_time:.3f}s")
            raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("🚀 Virtual Patient Simulator API starting up...")
    yield
    # Shutdown
    print("🛑 Virtual Patient Simulator API shutting down...")
    # Clean up sessions
    session_manager.cleanup_all_sessions()

# Initialize FastAPI app
app = FastAPI(
    title="Virtual Patient Simulator API",
    description="Backend API for the Virtual Patient Simulator application",
    version="1.0.0",
    lifespan=lifespan
)

print("✅ FastAPI app initialized and ready to start...")



# -----------------------------
# 🌍 Dynamic CORS Configuration
# -----------------------------
frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    cors_origins = [frontend_url]
else:
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    print("⚠️ FRONTEND_URL not set — using localhost defaults for development")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

# Register error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Virtual Patient Simulator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.app:app", host="0.0.0.0", port=port, log_level="info")
