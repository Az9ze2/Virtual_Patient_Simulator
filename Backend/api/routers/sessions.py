"""
Sessions Router - Handle session lifecycle and management
"""

import os
import json
import sys
import io
import zipfile
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

# Add src directory to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    StartSessionRequest, APIResponse, SessionSummary,
    UpdateDiagnosisRequest, CaseInfo, CaseType
)
from api.utils.session_manager import session_manager

router = APIRouter()

# Base path to cases
CASES_BASE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'data'
)

@router.post("/start")
async def start_session(request: StartSessionRequest):
    """
    Start a new interview session
    """
    try:
        # Load case data
        case_data, case_info = _load_case_data(request.case_filename)
        
        # Create session in session manager
        session_id = session_manager.create_session(
            user_info=request.user_info,
            case_info=case_info,
            config=request.config,
            case_data=case_data
        )
        
        return APIResponse(
            success=True,
            message="Session started successfully",
            data={
                "session_id": session_id,
                "case_info": case_info.dict(),
                "user_info": request.user_info.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )

@router.get("/info/{session_id}")
async def get_session_info(session_id: str):
    """
    Get session information including patient data
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return APIResponse(
            success=True,
            message="Session info retrieved successfully",
            data={
                "session_id": session_id,
                "user_info": session.user_info.dict(),
                "case_info": session.case_info.dict(),
                "patient_info": session.patient_info.dict() if session.patient_info else None,
                "diagnosis_treatment": session.diagnosis_treatment.dict(),
                "chat_history": session.chat_history,
                "created_at": session.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}"
        )

@router.put("/{session_id}/diagnosis")
async def update_diagnosis_treatment(session_id: str, request: UpdateDiagnosisRequest):
    """
    Update diagnosis and treatment plan for a session
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        # Update diagnosis and treatment
        session_manager.update_diagnosis_treatment(
            session_id=session_id,
            diagnosis=request.diagnosis,
            treatment_plan=request.treatment_plan,
            notes=request.notes
        )
        
        # Get updated session
        updated_session = session_manager.get_session(session_id)
        
        return APIResponse(
            success=True,
            message="Diagnosis and treatment updated successfully",
            data={
                "diagnosis_treatment": updated_session.diagnosis_treatment.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update diagnosis: {str(e)}"
        )

@router.post("/{session_id}/end")
async def end_session(session_id: str):
    """
    End session and generate summary with token usage
    """
    try:
        summary = session_manager.end_session(session_id)
        if not summary:
            raise HTTPException(
                status_code=404,
                detail="Session not found or already ended"
            )
        
        return APIResponse(
            success=True,
            message="Session ended successfully",
            data={"summary": summary.dict()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {str(e)}"
        )

@router.get("/{session_id}/download")
async def download_session_report(session_id: str):
    """
    Download session report as JSON file
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            # Try to generate summary for ended session
            summary = session_manager.end_session(session_id)
            if not summary:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found"
                )
            report_data = summary.dict()
        else:
            # Active session - create report from current state
            chatbot = session_manager.get_chatbot(session_id)
            duration = (datetime.now() - session.created_at).total_seconds() / 60.0
            
            token_usage = {}
            if chatbot:
                token_usage = {
                    "input_tokens": chatbot.input_tokens,
                    "output_tokens": chatbot.output_tokens,
                    "total_tokens": chatbot.total_tokens
                }
            
            report_data = {
                "session_id": session_id,
                "user_info": session.user_info.dict(),
                "case_info": session.case_info.dict(),
                "patient_info": session.patient_info.dict() if session.patient_info else None,
                "duration_minutes": duration,
                "total_messages": len(session.chat_history),
                "token_usage": token_usage,
                "diagnosis_treatment": session.diagnosis_treatment.dict(),
                "chat_history": session.chat_history,
                "created_at": session.created_at.isoformat(),
                "downloaded_at": datetime.now().isoformat(),
                "status": "active"
            }
        
        # Create JSON file in memory
        report_json = json.dumps(report_data, ensure_ascii=False, indent=2)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_report_{session_id[:8]}_{timestamp}.json"
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(report_json.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report: {str(e)}"
        )

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete session from memory
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        session_manager.delete_session(session_id)
        
        return APIResponse(
            success=True,
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.get("/active")
async def get_active_sessions():
    """
    Get list of active sessions
    """
    try:
        active_session_ids = session_manager.get_active_sessions()
        
        sessions_info = []
        for session_id in active_session_ids:
            session = session_manager.get_session(session_id)
            if session:
                sessions_info.append({
                    "session_id": session_id,
                    "user_name": session.user_info.name,
                    "case_title": session.case_info.case_title,
                    "created_at": session.created_at.isoformat(),
                    "message_count": len(session.chat_history)
                })
        
        return APIResponse(
            success=True,
            message=f"Found {len(sessions_info)} active sessions",
            data={"sessions": sessions_info}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active sessions: {str(e)}"
        )

def _load_case_data(filename: str):
    """
    Load case data and info from JSON file
    """
    try:
        # Determine which folder to look in based on filename prefix
        if filename.startswith("01_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_01")
            case_type = CaseType.CHILD
        elif filename.startswith("02_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_02")
            case_type = CaseType.ADULT
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid case filename format: {filename}"
            )
        
        case_file_path = os.path.join(cases_path, filename)
        
        if not os.path.exists(case_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Case file not found: {filename}"
            )
        
        with open(case_file_path, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        # Create case info
        case_metadata = case_data.get('case_metadata', {})
        case_info = CaseInfo(
            filename=filename,
            case_id=case_data.get('case_id', ''),
            case_title=case_metadata.get('case_title', ''),
            case_type=case_type,
            medical_specialty=case_metadata.get('medical_specialty', ''),
            exam_duration_minutes=case_metadata.get('exam_duration_minutes', 0)
        )
        
        return case_data, case_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load case data: {str(e)}"
        )
