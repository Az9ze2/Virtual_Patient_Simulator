"""
Sessions Router - Handle session lifecycle and management
"""

import os
import json
import sys
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

# Add src directory to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    StartSessionRequest, StartSessionWithUploadedCaseRequest, APIResponse, SessionSummary,
    UpdateDiagnosisRequest, CaseInfo, CaseType, UserInfo
)
from api.utils.session_manager import session_manager

# Database integration
try:
    from api.db import repository as repo
    from api.db.time_utils import now_th
except Exception as _db_import_err:
    repo = None
    now_th = None

router = APIRouter()

# Base path to cases
CASES_BASE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'data'
)

@router.post("/prelogin")
async def prelogin(request: StartSessionRequest):
    """
    Validate/create user on "Select Case" (login/new user login), update last_login, and write audit log.
    No session is created here.
    """
    try:
        if not (repo and now_th):
            return APIResponse(success=True, message="DB not configured; skipping login persistence")
        provided_email = getattr(request.user_info, 'email', None)
        provided_name = request.user_info.name
        student_id = request.user_info.student_id
        # Check existing profile
        existing = repo.get_user_profile_by_student_id(student_id)
        created = False
        if existing:
            # Name must match ignoring case
            existing_name = existing.get('name') or ''
            if (provided_name or '').strip().lower() != (existing_name or '').strip().lower():
                raise HTTPException(status_code=400, detail="Provided name does not match registered account for this student ID")
            # Email must match if present, else set for first time
            existing_email = existing.get('email')
            if provided_email:
                if existing_email and provided_email != existing_email:
                    raise HTTPException(status_code=400, detail="Provided email does not match registered account for this student ID")
                if not existing_email:
                    repo.create_or_get_user(student_id=student_id, name=provided_name, email=provided_email, preferences=getattr(request.user_info, 'preferences', None))
            user_id = existing.get('user_id')
            login_type = 'login'
        else:
            # New user
            user_id = repo.create_or_get_user(
                student_id=student_id,
                name=provided_name,
                email=provided_email,
                preferences=getattr(request.user_info, 'preferences', None),
            )
            login_type = 'nu-login'
            created = True
        # Update last_login
        repo.update_user_last_login(user_id)
        # Audit log
        repo.add_audit_log(user_id=user_id, session_id=None, action_type=login_type, performed_at=now_th().replace(tzinfo=None))
        return APIResponse(success=True, message=f"{login_type} recorded", data={"user_id": user_id, "login_type": login_type})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prelogin: {str(e)}")

@router.post("/start")
async def start_session(request: StartSessionRequest):
    """
    Start a new interview session
    """
    try:
        # Load case data
        case_data, case_info = _load_case_data(request.case_filename)

        # Create session in memory (returns session_id)
        session_id = session_manager.create_session(
            user_info=request.user_info,
            case_info=case_info,
            config=request.config,
            case_data=case_data
        )
        
        # Persist to DB (best-effort; do not fail request if DB unavailable)
        try:
            if repo and now_th:
                # Validate or create user profile
                provided_email = getattr(request.user_info, 'email', None)
                provided_name = request.user_info.name
                student_id = request.user_info.student_id

                existing = repo.get_user_profile_by_student_id(student_id)
                if existing:
                    # Name must match ignoring capitalization
                    existing_name = existing.get('name') or ''
                    if (provided_name or '').strip().lower() != (existing_name or '').strip().lower():
                        raise HTTPException(status_code=400, detail="Provided name does not match registered account for this student ID")
                    # Email must match exactly if stored
                    existing_email = existing.get('email')
                    if provided_email:
                        if existing_email and provided_email != existing_email:
                            raise HTTPException(status_code=400, detail="Provided email does not match registered account for this student ID")
                        if not existing_email:
                            # Set email for the first time
                            repo.create_or_get_user(student_id=student_id, name=provided_name, email=provided_email, preferences=getattr(request.user_info, 'preferences', None))
                    user_id = existing.get('user_id')
                else:
                    # New user: create with provided email/preferences
                    user_id = repo.create_or_get_user(
                        student_id=student_id,
                        name=provided_name,
                        email=provided_email,
                        preferences=getattr(request.user_info, 'preferences', None),
                    )
                # Last login is now handled at prelogin step
                # Derive case_id from request (should match DB-ingested id)
                cid = os.path.splitext(request.case_filename)[0]
                # Create session row (will fail if case FK missing)
                repo.create_session(
                    session_id=session_id,
                    user_id=user_id,
                    case_id=cid,
                    started_at=now_th().replace(tzinfo=None),
                )
                print(f"[DB] Created session: {session_id} for user {user_id} -> case {cid}")
                # Audit log
                repo.add_audit_log(
                    user_id=user_id,
                    session_id=session_id,
                    action_type="session_start",
                    performed_at=now_th().replace(tzinfo=None),
                )
                print(f"[DB] Audit log: session_start for {session_id}")
        except Exception as e:
            print(f"[DB][ERROR] Failed to persist session start to DB: {e}")
        
        return APIResponse(
            success=True,
            message="Session started successfully",
            data={
                "session_id": session_id,
                "case_info": case_info.dict(),
                "user_info": request.user_info.dict(),
                "examiner_view": case_data.get("examiner_view", {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )

@router.post("/start-uploaded-case")
async def start_session_with_uploaded_case(request: StartSessionWithUploadedCaseRequest):
    """
    Start a new interview session with uploaded case data
    """
    try:
        user_info = request.user_info
        case_data = request.case_data
        config = request.config
        
        # Create case info from uploaded data
        case_metadata = case_data.get('case_metadata', {})
        case_info = CaseInfo(
            filename="uploaded_case.json",
            case_id=case_data.get('case_id', 'UPLOADED-CASE'),
            case_title=case_metadata.get('case_title', 'Uploaded Case'),
            case_type=_determine_case_type_from_data(case_data),
            medical_specialty=case_metadata.get('medical_specialty', ''),
            exam_duration_minutes=case_metadata.get('exam_duration_minutes', 15)
        )
        
        # Create session in session manager
        session_id = session_manager.create_session(
            user_info=user_info,
            case_info=case_info,
            config=config,
            case_data=case_data
        )
        
        return APIResponse(
            success=True,
            message="Session started successfully with uploaded case",
            data={
                "session_id": session_id,
                "case_info": case_info.dict(),
                "user_info": user_info.dict(),
                "examiner_view": case_data.get("examiner_view", {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session with uploaded case: {str(e)}"
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

        # Persist completion to DB (best-effort)
        try:
            if repo and now_th:
                total_tokens = int((summary.token_usage or {}).get("total_tokens", 0))
                duration_seconds = int(summary.duration_minutes * 60)
                # Update session row
                repo.complete_session(
                    session_id=session_id,
                    total_tokens=total_tokens,
                    ended_at=now_th().replace(tzinfo=None),
                    duration_seconds=duration_seconds,
                )
                print(f"[DB] Marked session {session_id} as complete (tokens={total_tokens}, duration={duration_seconds}s)")
                # Save report (robust to schema) if not already present
                try:
                    if not repo.has_session_report(session_id):
                        rid = repo.insert_session_report(
                            session_id=session_id,
                            summary=summary.dict(),
                            generated_at=now_th().replace(tzinfo=None),
                        )
                        print(f"[DB] Inserted session_report id={rid} for session {session_id}")
                    else:
                        print(f"[DB] Session report already exists for {session_id}, skipping insert")
                except Exception as rep_err:
                    print(f"[DB][ERROR] Failed to insert session_report: {rep_err}")
                # Audit log with user_id resolved via student_id (always attempt)
                uid = None
                try:
                    uid = repo.get_user_id_by_student_id(summary.user_info.student_id)
                except Exception:
                    uid = None
                repo.add_audit_log(
                    user_id=uid,
                    session_id=session_id,
                    action_type="session_end",
                    performed_at=now_th().replace(tzinfo=None),
                )
                print(f"[DB] Audit log session_end for {session_id} (user_id={uid})")
        except Exception as e:
            print(f"[DB][ERROR] Failed to persist session end to DB: {e}")
        
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
    Download session report as PDF file
    """
    try:
        session = session_manager.get_session(session_id)
        report_data = None
        used_source = None

        # Prefer DB-saved summary first
        try:
            if repo:
                db_summary = repo.get_latest_session_report_summary(session_id)
                if db_summary:
                    report_data = db_summary
                    used_source = "db"
                    print(f"[DB] Loaded session report JSON from DB for session {session_id}")
        except Exception as e:
            print(f"[DB][ERROR] Failed to load report JSON from DB: {e}")

        if report_data is None:
            if not session:
                # Try to generate summary for ended session
                summary = session_manager.end_session(session_id)
                if not summary:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found"
                    )
                report_data = summary.dict()
                used_source = "generated"
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
                used_source = "memory"

        print(f"[PDF] Using report data source: {used_source}")
        # Generate PDF report using FPDF2
        try:
            import logging
            from fpdf import FPDF
            
            print(f"🔄 Starting PDF generation for session: {session_id}")
            
            # Extract data for PDF generation - handle both data formats
            ui = report_data.get('user_info') or report_data.get('userInfo') or {}
            ci = report_data.get('case_info') or report_data.get('caseInfo') or {}
            dt = report_data.get('diagnosis_treatment') or report_data.get('diagnosisTreatment') or {}
            ch = report_data.get('chat_history') or report_data.get('messages') or []
            
            print(f"📊 PDF data extracted: user_info={bool(ui)}, case_info={bool(ci)}, diagnosis={bool(dt)}, messages={len(ch) if ch else 0}")
            
            # Helper function to clean and format text for PDF
            def clean_text(text, is_timestamp=False):
                """Clean text for PDF display, with special timestamp formatting"""
                if text is None:
                    return 'N/A'
                text = str(text)
                
                # Format timestamps: "2025-01-15T10:30:45.123Z" -> "2025-01-15 10:30:45"
                if is_timestamp and text != 'N/A' and 'T' in text:
                    try:
                        date_part, time_part = text.split('T', 1)
                        # Remove microseconds and timezone info
                        time_part = time_part.split('.')[0].split('+')[0].split('-')[0].split('Z')[0]
                        text = f"{date_part} {time_part}"
                        print(f"🕰️ Formatted timestamp: {text}")
                    except Exception as ts_error:
                        print(f"⚠️ Timestamp format error: {ts_error}")
                
                # Normalize punctuation while preserving Unicode (Thai)
                text = text.replace('–', '-').replace('—', '-').replace('…', '...')
                return text.strip() or 'N/A'
            
            # Initialize PDF
            try:
                pdf = FPDF()
                pdf.add_page()
                print("✅ PDF document initialized")
            except Exception as pdf_init_error:
                print(f"❌ PDF initialization failed: {pdf_init_error}")
                raise
            
            # Load Thai font support - check local assets first, then system fonts
            pdf_font = 'helvetica'
            try:
                # Get directory of current file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                assets_fonts_dir = os.path.join(current_dir, '..', 'assets', 'fonts')
                
                # Priority order: local assets, then system fonts
                thai_fonts = [
                    # Local assets fonts (highest priority)
                    (os.path.join(assets_fonts_dir, 'THSarabunNew.ttf'), 'THSarabun'),
                    (os.path.join(assets_fonts_dir, 'NotoSansThai-Regular.ttf'), 'NotoSansThai'),
                    (os.path.join(assets_fonts_dir, 'Sarabun-Regular.ttf'), 'Sarabun'),
                    # Windows system fonts (fallback)
                    ('C:/Windows/Fonts/tahoma.ttf', 'Tahoma'),
                    ('C:/Windows/Fonts/arial.ttf', 'Arial'),
                    ('C:/Windows/Fonts/THSarabunNew.ttf', 'THSarabun')
                ]
                
                for font_path, font_name in thai_fonts:
                    if os.path.exists(font_path):
                        pdf.add_font(font_name, '', font_path, uni=True)
                        pdf_font = font_name
                        print(f"✅ Thai font loaded: {font_name} from {font_path}")
                        break
                else:
                    print("⚠️ No Thai fonts found - Thai text may not display properly")
                    print(f"🔍 Checked assets directory: {assets_fonts_dir}")
            except Exception as font_error:
                print(f"⚠️ Font loading error: {font_error}")
                pdf_font = 'helvetica'
            
            # Helper function for section headers (larger and more prominent)
            def add_section_header(title, font_size=16):
                """Add a prominent section header"""
                pdf.ln(3)
                pdf.set_font(pdf_font, '', font_size)
                pdf.cell(0, 8, f"=== {title.upper()} ===", ln=1)
                pdf.set_font(pdf_font, '', 12)
                pdf.ln(1)
            
            print("🎨 Starting PDF content generation...")
            
            # Main Title
            try:
                pdf.set_font(pdf_font, '', 22)
                pdf.cell(0, 14, '=== SESSION REPORT ===', ln=1, align='C')
                pdf.ln(8)
                print("✅ Title added")
            except Exception as title_error:
                print(f"⚠️ Title generation error: {title_error}")
            
            # Session Basic Info
            try:
                pdf.set_font(pdf_font, '', 12)
                pdf.cell(0, 7, f"Session ID: {clean_text(report_data.get('session_id'))}", ln=1)
                pdf.cell(0, 7, f"Created At: {clean_text(report_data.get('created_at'), is_timestamp=True)}", ln=1)
                print("✅ Basic info added")
            except Exception as basic_error:
                print(f"⚠️ Basic info error: {basic_error}")
            
            # Student Information Section
            try:
                add_section_header('Student Information')
                pdf.cell(0, 7, f"Name: {clean_text(ui.get('name'))}", ln=1)
                pdf.cell(0, 7, f"Student ID: {clean_text(ui.get('student_id'))}", ln=1)
                print("✅ Student info added")
            except Exception as student_error:
                print(f"⚠️ Student info error: {student_error}")
            
            # Case Information Section
            try:
                add_section_header('Case Information')
                pdf.cell(0, 7, f"Case Title: {clean_text(ci.get('case_title'))}", ln=1)
                pdf.cell(0, 7, f"Case ID: {clean_text(ci.get('case_id'))}", ln=1)
                pdf.cell(0, 7, f"Medical Specialty: {clean_text(ci.get('medical_specialty'))}", ln=1)
                pdf.cell(0, 7, f"Expected Duration: {clean_text(ci.get('exam_duration_minutes'))} minutes", ln=1)
                print("✅ Case info added")
            except Exception as case_error:
                print(f"⚠️ Case info error: {case_error}")
            
            # Session Performance Section
            try:
                add_section_header('Session Performance')
                duration_mins = report_data.get('duration_minutes', 0)
                safe_duration_mins = float(duration_mins) if duration_mins else 0
                
                # Format duration properly
                if safe_duration_mins >= 60:
                    hours = int(safe_duration_mins // 60)
                    minutes = int(safe_duration_mins % 60)
                    seconds = int((safe_duration_mins % 1) * 60)
                    if seconds > 0:
                        duration_text = f"{hours}h {minutes}m {seconds}s"
                    else:
                        duration_text = f"{hours}h {minutes}m"
                elif safe_duration_mins >= 1:
                    minutes = int(safe_duration_mins)
                    seconds = int((safe_duration_mins % 1) * 60)
                    if seconds > 0:
                        duration_text = f"{minutes}m {seconds}s"
                    else:
                        duration_text = f"{minutes}m"
                else:
                    seconds = int(safe_duration_mins * 60)
                    duration_text = f"{seconds}s"
                
                pdf.cell(0, 7, f"Actual Duration: {duration_text}", ln=1)
                pdf.cell(0, 7, f"Total Messages: {report_data.get('total_messages', 0)}", ln=1)
                print("✅ Performance metrics added")
            except Exception as perf_error:
                print(f"⚠️ Performance metrics error: {perf_error}")
            
            # Diagnosis & Treatment Section
            try:
                add_section_header('Clinical Assessment')
                
                # Check multiple possible field names for diagnosis and treatment
                diagnosis_candidates = [
                    dt.get('diagnosis'),
                    dt.get('diagnosis_text'), 
                    dt.get('diagnosisText'),
                    report_data.get('diagnosis'),
                    report_data.get('diagnosisText')
                ]
                
                treatment_candidates = [
                    dt.get('treatment_plan'),
                    dt.get('treatment'),
                    dt.get('treatmentPlan'),
                    dt.get('treatment_text'),
                    report_data.get('treatment_plan'),
                    report_data.get('treatmentPlan')
                ]
                
                # Find first non-empty diagnosis
                diagnosis_text = 'Not provided'
                for candidate in diagnosis_candidates:
                    if candidate and str(candidate).strip() and str(candidate).strip().lower() != 'n/a':
                        diagnosis_text = str(candidate)
                        break
                
                # Find first non-empty treatment plan
                treatment_text = 'Not provided'
                for candidate in treatment_candidates:
                    if candidate and str(candidate).strip() and str(candidate).strip().lower() != 'n/a':
                        treatment_text = str(candidate)
                        break
                
                diagnosis_text = clean_text(diagnosis_text)
                treatment_text = clean_text(treatment_text)
                
                # Diagnosis
                pdf.set_font(pdf_font, '', 13)  # Slightly larger for sub-headers
                pdf.cell(0, 7, 'Diagnosis:', ln=1)
                pdf.set_font(pdf_font, '', 12)
                
                # Handle long text by wrapping
                if len(diagnosis_text) > 80:
                    lines = [diagnosis_text[i:i+80] for i in range(0, len(diagnosis_text), 80)]
                    for line in lines:
                        pdf.cell(0, 6, f"  {line}", ln=1)
                else:
                    pdf.cell(0, 6, f"  {diagnosis_text}", ln=1)
                
                pdf.ln(2)
                
                # Treatment Plan (use already extracted treatment_text)
                pdf.set_font(pdf_font, '', 13)
                pdf.cell(0, 7, 'Treatment Plan:', ln=1)
                pdf.set_font(pdf_font, '', 12)
                
                if len(treatment_text) > 80:
                    lines = [treatment_text[i:i+80] for i in range(0, len(treatment_text), 80)]
                    for line in lines:
                        pdf.cell(0, 6, f"  {line}", ln=1)
                else:
                    pdf.cell(0, 6, f"  {treatment_text}", ln=1)
                    
                print("✅ Clinical assessment added")
            except Exception as diag_error:
                print(f"⚠️ Clinical assessment error: {diag_error}")
            
            # Conversation History Section
            try:
                add_section_header('Conversation History')
                pdf.set_font(pdf_font, '', 11)
                
                if ch and len(ch) > 0:
                    for i, msg in enumerate(ch[:10]):  # Limit to first 10 messages
                        # Check if near bottom of page
                        if pdf.get_y() > 250:
                            pdf.add_page()
                            pdf.set_font(pdf_font, '', 11)
                        
                        try:
                            # Extract message data
                            timestamp = clean_text(msg.get('timestamp', ''), is_timestamp=True)
                            user_msg = msg.get('user', '') or (msg.get('content', '') if msg.get('role') == 'user' else '')
                            bot_msg = msg.get('bot', '') or (msg.get('content', '') if msg.get('role') != 'user' else '')
                            
                            # Message header
                            pdf.cell(0, 6, f"[{i+1}] {timestamp}", ln=1)
                            
                            # Doctor message
                            if user_msg:
                                doctor_text = clean_text(user_msg)
                                if len(doctor_text) > 90:
                                    doctor_text = doctor_text[:90] + '...'
                                pdf.cell(0, 5, f"Doctor: {doctor_text}", ln=1)
                            
                            # Patient message  
                            if bot_msg:
                                patient_text = clean_text(bot_msg)
                                if len(patient_text) > 90:
                                    patient_text = patient_text[:90] + '...'
                                pdf.cell(0, 5, f"Patient: {patient_text}", ln=1)
                            
                            pdf.ln(1)
                            
                        except Exception as msg_error:
                            print(f"⚠️ Message {i+1} processing error: {msg_error}")
                            pdf.cell(0, 4, f"[{i+1}] Message processing error", ln=1)
                    
                    # Show total message count if truncated
                    if len(ch) > 10:
                        pdf.ln(1)
                        pdf.cell(0, 5, f"... and {len(ch) - 10} more messages (total: {len(ch)})", ln=1)
                    
                    print(f"✅ Conversation history added ({min(len(ch), 10)}/{len(ch)} messages)")
                else:
                    pdf.cell(0, 6, "No conversation history available", ln=1)
                    print("⚠️ No conversation history found")
                    
            except Exception as conv_error:
                print(f"⚠️ Conversation history error: {conv_error}")
            
            # Generate final PDF
            try:
                print("⚙️ Generating PDF binary data...")
                pdf_bytes = pdf.output()
                
                if not pdf_bytes or len(pdf_bytes) == 0:
                    raise Exception("PDF generation returned empty data")
                    
                print(f"✅ PDF generated successfully! Size: {len(pdf_bytes)} bytes")
                
                # Create file buffer
                buffer = io.BytesIO(pdf_bytes)
                buffer.seek(0)
                
                # Generate filename based on student info
                def generate_filename(ui, extension="pdf"):
                    """Generate filename in format: studentid_firstname.pdf or fallback to timestamp"""
                    student_id = clean_text(ui.get('student_id', '')).replace(' ', '_')
                    name = clean_text(ui.get('name', ''))
                    
                    # Extract first name (split by space and take first part)
                    if name and name != 'N/A':
                        first_name = name.split(' ')[0].replace(' ', '_')
                    else:
                        first_name = ''
                    
                    # Generate filename based on available data
                    if student_id and student_id != 'N/A' and first_name and first_name != 'N/A':
                        filename = f"{student_id}_{first_name}.{extension}"
                    elif student_id and student_id != 'N/A':
                        filename = f"{student_id}_session.{extension}"
                    else:
                        # Fallback to timestamp if no student info
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"session_report_{timestamp}.{extension}"
                    
                    # Clean filename of invalid characters
                    import re
                    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                    return filename
                
                filename = generate_filename(ui, "pdf")
                print(f"📦 Returning PDF file: {filename}")
                
                # Use simple, reliable Content-Disposition header
                # Most browsers handle ASCII filenames well, so let's make an ASCII-safe version
                import unicodedata
                import re
                
                # Create ASCII-safe filename by removing non-ASCII characters
                ascii_filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
                
                # If ASCII conversion removed too much, create a simple format
                if not ascii_filename or ascii_filename == '.pdf' or len(ascii_filename) < 5:
                    # Extract basic info and create simple filename
                    student_id = clean_text(ui.get('student_id', '')).replace(' ', '_')
                    if student_id and student_id != 'N/A':
                        ascii_filename = f"{student_id}_report.pdf"
                    else:
                        ascii_filename = f"student_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Clean any remaining problematic characters
                ascii_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', ascii_filename)
                
                content_disposition = f'attachment; filename="{ascii_filename}"'
                print(f"📝 Content-Disposition: {content_disposition}")
                
                # Audit log: download_report (best-effort)
                try:
                    if repo and now_th:
                        uid = None
                        try:
                            # Try resolve user id from session manager data
                            session_obj = session_manager.get_session(session_id)
                            if session_obj:
                                uid = repo.get_user_id_by_student_id(session_obj.user_info.student_id)
                        except Exception:
                            uid = None
                        repo.add_audit_log(
                            user_id=uid,
                            session_id=session_id,
                            action_type="download_report",
                            performed_at=now_th().replace(tzinfo=None),
                        )
                        print(f"[DB] Audit log download_report for {session_id} (user_id={uid})")
                except Exception as audit_err:
                    print(f"[DB][ERROR] Failed to write download_report audit: {audit_err}")

                return StreamingResponse(
                    buffer,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": content_disposition,
                        "Content-Type": "application/pdf"
                    }
                )
                
            except Exception as pdf_gen_error:
                print(f"❌ PDF generation failed: {pdf_gen_error}")
                raise
            
        except Exception as pdf_error:
            # PDF generation failed - fallback to HTML report
            import traceback
            print(f"❌ PDF generation completely failed - falling back to HTML report")
            print(f"🔍 Error details: {pdf_error}")
            print(f"🔎 Traceback: {traceback.format_exc()[:500]}...")  # Limit traceback length
            
            # Log the session data structure for debugging
            print(f"📊 Debug - Report data keys: {list(report_data.keys()) if report_data else 'None'}")
            
            # Build a simple HTML report (avoid emojis; use plain text)
            def esc(s):
                if s is None:
                    return ''
                return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

            ui = report_data.get('user_info', {}) or {}
            ci = report_data.get('case_info', {}) or {}
            dt = report_data.get('diagnosis_treatment', {}) or {}
            ch = report_data.get('chat_history', []) or []

            # Build conversation history
            conversation_history = ''.join([
                f"[{i+1}] Time: {esc(m.get('timestamp',''))}" + "\n   Doctor: " + f"{esc(m.get('user','') or (m.get('content','') if m.get('role')=='user' else ''))}" + "\n   Patient: " + f"{esc(m.get('bot','') or (m.get('content','') if m.get('role')!='user' else ''))}" + "\n\n"
                for i,m in enumerate(ch)
            ])
            
            html = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset='utf-8'>
                <title>Session Report</title>
                <style>
                  body {{ font-family: Arial, sans-serif; font-size: 12pt; color: #000; margin: 20px; }}
                  h1, h2 {{ margin: 0.4em 0 0.2em; }}
                  .section-title {{ font-weight: bold; font-size: 14pt; margin-top: 14px; }}
                  .kv {{ margin: 2px 0; }}
                  .mono {{ white-space: pre-wrap; font-family: monospace; }}
                  .divider {{ border-top: 1px solid #999; margin: 10px 0; }}
                </style>
              </head>
              <body>
                <h1>Session Report</h1>
                <div class='kv'>Session ID: {esc(report_data.get('session_id',''))}</div>
                <div class='kv'>Created At: {esc(report_data.get('created_at',''))}</div>
                <div class='divider'></div>

                <div class='section-title'>Student Information</div>
                <div class='kv'>Name: {esc(ui.get('name',''))}</div>
                <div class='kv'>Student ID: {esc(ui.get('student_id',''))}</div>

                <div class='section-title'>Case Information</div>
                <div class='kv'>Case Title: {esc(ci.get('case_title',''))}</div>
                <div class='kv'>Case ID: {esc(ci.get('case_id',''))}</div>
                <div class='kv'>Medical Specialty: {esc(ci.get('medical_specialty',''))}</div>
                <div class='kv'>Expected Duration: {esc(ci.get('exam_duration_minutes',''))} minutes</div>

                <div class='section-title'>Session Details</div>
                <div class='kv'>Actual Duration: {round(report_data.get('duration_minutes') or 0, 2)} minutes</div>
                <div class='kv'>Total Messages: {esc(report_data.get('total_messages',0))}</div>

                <div class='section-title'>Diagnosis and Treatment Plan</div>
                <div class='kv mono'>Diagnosis: {esc(dt.get('diagnosis') or 'Not provided')}</div>
                <div class='kv mono'>Treatment Plan: {esc(dt.get('treatment_plan') or 'Not provided')}</div>

                <div class='section-title'>Conversation History</div>
                <div class='mono'>
                  {conversation_history}
                </div>
              </body>
            </html>
            """

            buffer = io.BytesIO(html.encode('utf-8'))
            buffer.seek(0)
            
            # Generate filename using the same logic as PDF
            def generate_filename_html(ui, extension="html"):
                """Generate filename in format: studentid_firstname.html or fallback to timestamp"""
                def clean_text_simple(text):
                    if text is None:
                        return 'N/A'
                    return str(text).strip() or 'N/A'
                    
                student_id = clean_text_simple(ui.get('student_id', '')).replace(' ', '_')
                name = clean_text_simple(ui.get('name', ''))
                
                # Extract first name (split by space and take first part)
                if name and name != 'N/A':
                    first_name = name.split(' ')[0].replace(' ', '_')
                else:
                    first_name = ''
                
                # Generate filename based on available data
                if student_id and student_id != 'N/A' and first_name and first_name != 'N/A':
                    filename = f"{student_id}_{first_name}.{extension}"
                elif student_id and student_id != 'N/A':
                    filename = f"{student_id}_session.{extension}"
                else:
                    # Fallback to timestamp if no student info
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"session_report_{timestamp}.{extension}"
                
                # Clean filename of invalid characters
                import re
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                return filename
            
            filename = generate_filename_html(ui, "html")
            print(f"📦 Returning HTML file: {filename}")
            
            # Use simple, reliable Content-Disposition header for HTML
            import unicodedata
            import re
            
            # Create ASCII-safe filename
            ascii_filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
            
            # If ASCII conversion removed too much, create a simple format
            if not ascii_filename or ascii_filename == '.html' or len(ascii_filename) < 5:
                student_id = clean_text_simple(ui.get('student_id', '')).replace(' ', '_')
                if student_id and student_id != 'N/A':
                    ascii_filename = f"{student_id}_report.html"
                else:
                    ascii_filename = f"student_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Clean any remaining problematic characters
            ascii_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', ascii_filename)
            
            content_disposition = f'attachment; filename="{ascii_filename}"'
            print(f"📝 Content-Disposition: {content_disposition}")
            
            return StreamingResponse(
                buffer,
                media_type="text/html",
                headers={
                    "Content-Disposition": content_disposition,
                    "Content-Type": "text/html; charset=utf-8"
                }
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

def _determine_case_type_from_data(case_data: dict) -> CaseType:
    """
    Determine case type from case data based on patient age
    """
    try:
        age_info = case_data["examiner_view"]["patient_background"]["age"]
        
        # Handle both dict and plain int
        if isinstance(age_info, dict) and "value" in age_info:
            age = int(age_info["value"])
        elif isinstance(age_info, (int, float)):
            age = int(age_info)
        else:
            # Default to child if age format not recognized
            return CaseType.CHILD
        
        return CaseType.ADULT if age >= 18 else CaseType.CHILD
        
    except Exception:
        # Default to child case on error
        return CaseType.CHILD

def _load_case_data(filename: str):
    """
    Load case data and info by filename from disk; if not found, try DB by case_id.
    """
    try:
        # Normalize: strip any extension to get the base identifier
        filename_base = os.path.splitext(filename)[0]
        # First, try disk
        cases_path = None
        case_type = None
        if filename_base.startswith("01_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_01")
            case_type = CaseType.CHILD
        elif filename_base.startswith("02_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_02")
            case_type = CaseType.ADULT
        
        if cases_path:
            case_file_path = os.path.join(cases_path, filename_base + ".json")
            if os.path.exists(case_file_path):
                with open(case_file_path, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                case_metadata = case_data.get('case_metadata', {})
                case_info = CaseInfo(
                    filename=filename,
                    case_id=case_data.get('case_id', ''),
                    case_title=case_metadata.get('case_title', ''),
                    case_type=case_type or CaseType.CHILD,
                    medical_specialty=case_metadata.get('medical_specialty', ''),
                    exam_duration_minutes=case_metadata.get('exam_duration_minutes', 0)
                )
                return case_data, case_info
        
        # If not on disk, try to load from DB using the provided string as case_id
        if repo:
            data = repo.get_case_data(filename_base)
            if data:
                cid = data.get('case_id', filename)
                meta = data.get('case_metadata', {})
                prefix = cid.split('_')[0] if '_' in cid else '01'
                ctype = CaseType(prefix) if prefix in (CaseType.CHILD.value, CaseType.ADULT.value) else CaseType.CHILD
                case_info = CaseInfo(
                    filename=cid,
                    case_id=cid,
                    case_title=meta.get('case_title', cid),
                    case_type=ctype,
                    medical_specialty=meta.get('medical_specialty', ''),
                    exam_duration_minutes=meta.get('exam_duration_minutes', 0),
                )
                return data, case_info
        
        raise HTTPException(
            status_code=404,
            detail=f"Case not found on disk or database: {filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load case data: {str(e)}"
        )
