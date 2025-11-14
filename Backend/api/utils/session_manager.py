"""
Session Manager for Virtual Patient Simulator
Manages in-memory session data without persistent database
"""

import uuid
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from threading import Lock
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Load .env file from src directory
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ Loaded .env from: {env_path}")
else:
    # Fallback to default location
    load_dotenv()

from core.chatbot.unified_chatbot import UnifiedChatbotTester
from core.config.prompt_config import PromptConfig
from api.models.schemas import (
    SessionData, UserInfo, CaseInfo, SessionConfig,
    DiagnosisAndTreatment, PatientInfo, SessionSummary
)

class SessionManager:
    """Manages active sessions in memory"""
    
    # Session timeout in minutes (default 60 minutes = 1 hour)
    SESSION_TIMEOUT_MINUTES = 60
    
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
        self._chatbots: Dict[str, UnifiedChatbotTester] = {}
        self._lock = Lock()
    
    def create_session(
        self, 
        user_info: UserInfo, 
        case_info: CaseInfo, 
        config: SessionConfig,
        case_data: Dict[str, Any]
    ) -> str:
        """Create a new session with chatbot instance"""
        with self._lock:
            session_id = str(uuid.uuid4())
            
            # Create session data
            now = datetime.now()
            session = SessionData(
                session_id=session_id,
                user_info=user_info,
                case_info=case_info,
                config=config,
                created_at=now,
                last_activity=now,
                patient_info=self._extract_patient_info(case_data)
            )
            
            # Initialize chatbot
            chatbot = UnifiedChatbotTester(
                memory_mode=config.memory_mode.value,
                model_choice=config.model_choice.value,
                exam_mode=config.exam_mode
            )
            
            # Override temperature for GPT-4.1-mini if specified
            if config.model_choice.value == "gpt-4.1-mini" and config.temperature != 0.7:
                chatbot.generation_params["temperature"] = config.temperature
            
            # Determine and set case type from medical specialty before setup
            case_type = PromptConfig.get_case_type_from_medical_specialty(case_data)
            chatbot.case_type = case_type
            chatbot.display_name = PromptConfig.get_display_name(case_type)
            print(f"🏷️ Set case type from medical specialty: {case_type} ({'Mother/Guardian' if case_type == '01' else 'Patient'})")
            
            # Setup conversation with case data
            chatbot.setup_conversation(case_data)
            
            # Store session and chatbot
            self._sessions[session_id] = session
            self._chatbots[session_id] = chatbot
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID and update last activity"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_activity = datetime.now()
            return session
    
    def get_chatbot(self, session_id: str) -> Optional[UnifiedChatbotTester]:
        """Get chatbot instance by session ID and update last activity"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_activity = datetime.now()
            return self._chatbots.get(session_id)
    
    def update_chat_history(self, session_id: str, user_message: str, bot_response: str):
        """Add new chat message to session history and update last activity"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                now = datetime.now()
                session.chat_history.append({
                    "timestamp": now.isoformat(),
                    "user": user_message,
                    "bot": bot_response,
                    "type": "chat"
                })
                session.last_activity = now
    
    def update_diagnosis_treatment(
        self, 
        session_id: str, 
        diagnosis: Optional[str] = None,
        treatment_plan: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Update diagnosis and treatment data and update last activity"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                if diagnosis is not None:
                    session.diagnosis_treatment.diagnosis = diagnosis
                if treatment_plan is not None:
                    session.diagnosis_treatment.treatment_plan = treatment_plan
                if notes is not None:
                    session.diagnosis_treatment.notes = notes
                session.last_activity = datetime.now()
    
    def end_session(self, session_id: str) -> Optional[SessionSummary]:
        """End session and generate summary with token usage"""
        with self._lock:
            session = self._sessions.get(session_id)
            chatbot = self._chatbots.get(session_id)
            
            if not session or not chatbot:
                return None
            
            # Calculate duration
            duration = (datetime.now() - session.created_at).total_seconds() / 60.0
            
            # Get token usage from chatbot
            token_usage = {
                "input_tokens": chatbot.input_tokens,
                "output_tokens": chatbot.output_tokens,
                "total_tokens": chatbot.total_tokens
            }
            
            # Create summary
            summary = SessionSummary(
                session_id=session_id,
                user_info=session.user_info,
                case_info=session.case_info,
                duration_minutes=duration,
                total_messages=len(session.chat_history),
                token_usage=token_usage,
                diagnosis_treatment=session.diagnosis_treatment,
                chat_history=session.chat_history,
                created_at=session.created_at,
                ended_at=datetime.now(),
                exam_mode=session.config.exam_mode
            )
            
            return summary
    
    def delete_session(self, session_id: str):
        """Delete session from memory"""
        with self._lock:
            self._sessions.pop(session_id, None)
            self._chatbots.pop(session_id, None)
    
    def cleanup_all_sessions(self):
        """Clean up all sessions"""
        with self._lock:
            self._sessions.clear()
            self._chatbots.clear()
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        with self._lock:
            return list(self._sessions.keys())
    
    def get_active_sessions_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about all active sessions"""
        with self._lock:
            sessions_info = []
            now = datetime.now()
            for session_id, session in self._sessions.items():
                inactive_minutes = (now - session.last_activity).total_seconds() / 60.0
                sessions_info.append({
                    "session_id": session_id,
                    "user_name": session.user_info.name,
                    "student_id": session.user_info.student_id,
                    "case_title": session.case_info.case_title,
                    "case_id": session.case_info.case_id,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "inactive_minutes": round(inactive_minutes, 1),
                    "total_messages": len(session.chat_history),
                    "exam_mode": session.config.exam_mode
                })
            return sessions_info
    
    def cleanup_inactive_sessions(self, timeout_minutes: Optional[int] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Clean up sessions that have been inactive for longer than timeout_minutes.
        Properly ends sessions with summary generation and database updates.
        Returns list of (session_id, session_info) tuples for cleaned up sessions."""
        if timeout_minutes is None:
            timeout_minutes = self.SESSION_TIMEOUT_MINUTES
        
        with self._lock:
            now = datetime.now()
            timeout_delta = timedelta(minutes=timeout_minutes)
            sessions_to_cleanup = []
            
            # Find sessions to cleanup
            for session_id, session in list(self._sessions.items()):
                inactive_time = now - session.last_activity
                if inactive_time > timeout_delta:
                    inactive_minutes = inactive_time.total_seconds() / 60.0
                    session_info = {
                        "session_id": session_id,
                        "user_name": session.user_info.name,
                        "student_id": session.user_info.student_id,
                        "case_title": session.case_info.case_title,
                        "inactive_minutes": round(inactive_minutes, 1)
                    }
                    sessions_to_cleanup.append((session_id, session_info))
            
            # Properly end each session (generate summary, update DB)
            cleaned_sessions = []
            for session_id, session_info in sessions_to_cleanup:
                try:
                    # Generate summary before deleting
                    summary = self.end_session(session_id)
                    
                    # Persist to database if available
                    if summary:
                        try:
                            # Import here to avoid circular dependency
                            from api.db import repository as repo
                            from api.db.time_utils import now_th
                            
                            if repo and now_th:
                                total_tokens = int((summary.token_usage or {}).get("total_tokens", 0))
                                duration_seconds = int(summary.duration_minutes * 60)
                                
                                # Update session as complete
                                repo.complete_session(
                                    session_id=session_id,
                                    total_tokens=total_tokens,
                                    ended_at=now_th().replace(tzinfo=None),
                                    duration_seconds=duration_seconds,
                                )
                                
                                # Save report if not exists
                                if not repo.has_session_report(session_id):
                                    repo.insert_session_report(
                                        session_id=session_id,
                                        summary=summary.dict(),
                                        generated_at=now_th().replace(tzinfo=None),
                                    )
                                
                                # Add audit log
                                uid = None
                                try:
                                    uid = repo.get_user_id_by_student_id(summary.user_info.student_id)
                                except:
                                    pass
                                
                                token_usage = summary.token_usage or {}
                                mode = "exam" if summary.exam_mode else "practice"
                                details = f"mode={mode} | reason=auto_timeout | inactive_minutes={session_info['inactive_minutes']} | messages={summary.total_messages} | duration={duration_seconds}s | tokens={total_tokens}"
                                
                                repo.add_audit_log(
                                    user_id=uid,
                                    session_id=session_id,
                                    action_type="session_timeout",
                                    details=details,
                                    performed_at=now_th().replace(tzinfo=None),
                                    ip_address="system"
                                )
                        except Exception as db_err:
                            print(f"   [DB][ERROR] Failed to persist timeout for {session_id}: {db_err}")
                    
                    # Delete from memory
                    self.delete_session(session_id)
                    cleaned_sessions.append((session_id, session_info))
                    print(f"🕐 Auto-ended session due to timeout: {session_id} (user: {session_info['user_name']}, inactive: {session_info['inactive_minutes']} min)")
                    
                except Exception as e:
                    print(f"   ❌ Error ending session {session_id}: {e}")
                    # Force delete even if ending fails
                    self.delete_session(session_id)
            
            return cleaned_sessions
    
    def _extract_patient_info(self, case_data: Dict[str, Any]) -> PatientInfo:
        """Extract patient information from case data for examiner view"""
        examiner_view = case_data.get("examiner_view", {})
        patient_bg = examiner_view.get("patient_background", {})
        
        return PatientInfo(
            name=patient_bg.get("name", ""),
            age=patient_bg.get("age", {"value": 0, "unit": "years"}),
            sex=patient_bg.get("sex", ""),
            occupation=patient_bg.get("occupation"),
            chief_complaint=patient_bg.get("chief_complaint", ""),
            physical_examination=examiner_view.get("physical_examination", {}),
            patient_illness_history=examiner_view.get("patient_illness_history", {}),
            growth_and_birth_history=examiner_view.get("growth_and_birth_history")
        )

# Global session manager instance
session_manager = SessionManager()
