#!/usr/bin/env python3
"""
Virtual Patient Simulator - FastAPI Backend
Handles frontend-backend communication for the virtual patient simulator
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
