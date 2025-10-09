"""
Error handling and validation utilities for the API
"""

import sys
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from api.models.schemas import ErrorResponse

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    """
    error_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(x) for x in error["loc"])
        error_details.append(f"{field_path}: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            error="Validation Error",
            details="; ".join(error_details)
        ).dict()
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=f"HTTP {exc.status_code}",
            details=str(exc.detail)
        ).dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions
    """
    # Log the full traceback for debugging
    print(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Internal Server Error", 
            details="An unexpected error occurred. Please try again or contact support."
        ).dict()
    )

def validate_session_exists(session_id: str, session_manager):
    """
    Validate that a session exists
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )
    return session

def validate_file_type(filename: str, allowed_extensions: list):
    """
    Validate file type by extension
    """
    if not filename.lower().endswith(tuple(allowed_extensions)):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )

def validate_case_filename(filename: str):
    """
    Validate case filename format
    """
    if not (filename.startswith("01_") or filename.startswith("02_")):
        raise HTTPException(
            status_code=400,
            detail="Invalid case filename format. Must start with '01_' or '02_'"
        )
    
    if not filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Case file must be a JSON file"
        )

def create_success_response(message: str, data: Optional[Dict[str, Any]] = None):
    """
    Create a standardized success response
    """
    return {
        "success": True,
        "message": message,
        "data": data
    }

def create_error_response(error: str, details: Optional[str] = None, status_code: int = 400):
    """
    Create a standardized error response
    """
    response_content = ErrorResponse(
        success=False,
        error=error,
        details=details
    ).dict()
    
    raise HTTPException(status_code=status_code, detail=response_content)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class SessionNotFoundError(Exception):
    """Custom session not found error"""
    pass

class ChatbotError(Exception):
    """Custom chatbot error"""
    pass

class DocumentProcessingError(Exception):
    """Custom document processing error"""
    pass

def safe_execute(func, *args, error_message: str = "Operation failed", **kwargs):
    """
    Safely execute a function with error handling
    """
    try:
        return func(*args, **kwargs)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {str(e)}"
        )
    except ChatbotError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot error: {str(e)}"
        )
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing error: {str(e)}"
        )
    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in {func.__name__}: {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"{error_message}: {str(e)}"
        )

def log_api_call(request: Request, response_data: Dict[str, Any]):
    """
    Log API calls for debugging/monitoring
    """
    method = request.method
    url = str(request.url)
    success = response_data.get("success", False)
    
    print(f"API Call: {method} {url} - {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        error = response_data.get("error", "Unknown error")
        print(f"  Error: {error}")

# Input sanitization helpers
def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    # Remove null bytes and control characters
    cleaned = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    if len(cleaned) > max_length:
        raise ValidationError(f"String too long (max {max_length} characters)")
    
    return cleaned.strip()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")
    
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    cleaned = filename
    
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '_')
    
    return cleaned.strip()

def validate_json_structure(data: Dict[str, Any], required_fields: list):
    """
    Validate JSON structure has required fields
    """
    missing_fields = []
    
    for field in required_fields:
        if '.' in field:
            # Handle nested fields like 'case_metadata.case_title'
            keys = field.split('.')
            current = data
            
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    missing_fields.append(field)
                    break
                current = current[key]
        else:
            if field not in data:
                missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True
