#!/usr/bin/env python3
"""
Virtual Patient Simulator - FastAPI Backend
Handles frontend-backend communication for the virtual patient simulator
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import routers
from routers import sessions, chatbot, cases, documents, config, stt_routes, tts, admin

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

# Background task for session cleanup
async def session_cleanup_task():
    """Background task that runs every 5 minutes to cleanup inactive sessions"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes (300 seconds)
            print("\n🧹 Running automatic session cleanup...")
            cleaned_sessions = session_manager.cleanup_inactive_sessions()
            if cleaned_sessions:
                print(f"   🕐 Cleaned up {len(cleaned_sessions)} inactive session(s)")
                for session_id, info in cleaned_sessions:
                    print(f"      - {info['user_name']} ({info['student_id']}): inactive for {info['inactive_minutes']} min")
            else:
                print("   ✓ No inactive sessions to cleanup")
        except Exception as e:
            print(f"   ❌ Error in session cleanup task: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("🚀 Virtual Patient Simulator API starting up...")
    print(f"🕐 Session timeout set to {session_manager.SESSION_TIMEOUT_MINUTES} minutes")
    print("🔄 Starting background session cleanup task (runs every 5 minutes)...")
    
    # Start background task for session cleanup
    cleanup_task = asyncio.create_task(session_cleanup_task())
    
    yield
    
    # Shutdown
    print("🛑 Virtual Patient Simulator API shutting down...")
    # Cancel background task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        print("   ✓ Background cleanup task stopped")
    # Clean up all remaining sessions
    session_manager.cleanup_all_sessions()
    print("   ✓ All sessions cleaned up")

# Initialize FastAPI app
app = FastAPI(
    title="Virtual Patient Simulator API",
    description="Backend API for the Virtual Patient Simulator application",
    version="1.0.0",
    lifespan=lifespan
)

print("✅ FastAPI app initialized and ready to start...")

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

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
    expose_headers=["Content-Disposition", "Content-Type"]
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(stt_routes.router, prefix="/api/stt", tags=["Speech-to-Text"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text-to-Speech"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

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

@app.get("/test-filename")
async def test_filename():
    """Test endpoint to verify Content-Disposition header transmission"""
    from fastapi import Response
    
    content = "Test file content for filename testing"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="65011441_Pavares_TEST.txt"'
        }
    )

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.app:app", host="0.0.0.0", port=port, log_level="info")
