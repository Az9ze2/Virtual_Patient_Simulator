"""
Pydantic models for API requests and responses
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class CaseType(str, Enum):
    CHILD = "01"  # cases_01 folder - child/parent cases
    ADULT = "02"  # cases_02 folder - adult patient cases

class ModelType(str, Enum):
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_5 = "gpt-5"

class MemoryMode(str, Enum):
    NONE = "none"
    TRUNCATE = "truncate" 
    SUMMARIZE = "summarize"

# User and Session Models
class UserInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    student_id: str = Field(..., min_length=1, max_length=50)

class SessionConfig(BaseModel):
    model_choice: ModelType = ModelType.GPT_4_1_MINI
    memory_mode: MemoryMode = MemoryMode.SUMMARIZE
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    exam_mode: bool = False

# Case Models
class CaseMetadata(BaseModel):
    case_id: str
    case_title: str
    medical_specialty: str
    exam_type: str
    exam_duration_minutes: int

class CaseInfo(BaseModel):
    filename: str
    case_id: str
    case_title: str
    case_type: CaseType
    medical_specialty: str
    exam_duration_minutes: int

class PatientInfo(BaseModel):
    """Patient information for the examiner view"""
    name: str
    age: Dict[str, Union[int, str]]
    sex: str
    occupation: Optional[str] = None
    chief_complaint: str
    physical_examination: Dict[str, Any]
    patient_illness_history: Dict[str, Any]
    growth_and_birth_history: Optional[Dict[str, Any]] = None

# Chat Models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    response: str
    response_time: float
    session_id: str

class DiagnosisAndTreatment(BaseModel):
    diagnosis: str = Field(default="", description="Current diagnosis notes")
    treatment_plan: str = Field(default="", description="Current treatment plan")
    notes: str = Field(default="", description="Additional clinical notes")

# Session Models
class SessionData(BaseModel):
    session_id: str
    user_info: UserInfo
    case_info: CaseInfo
    config: SessionConfig
    created_at: datetime
    chat_history: List[Dict[str, str]] = []
    diagnosis_treatment: DiagnosisAndTreatment = DiagnosisAndTreatment()
    patient_info: Optional[PatientInfo] = None

class SessionSummary(BaseModel):
    session_id: str
    user_info: UserInfo
    case_info: CaseInfo
    duration_minutes: float
    total_messages: int
    token_usage: Dict[str, int]
    diagnosis_treatment: DiagnosisAndTreatment
    chat_history: List[Dict[str, str]]
    ended_at: datetime

# Document Upload Models
class DocumentUploadResponse(BaseModel):
    filename: str
    file_size: int
    upload_time: datetime
    processing_status: str = "pending"

class ExtractedDataResponse(BaseModel):
    filename: str
    extracted_data: Dict[str, Any]
    case_type: CaseType
    processing_time: float
    suggested_filename: str

class DataVerification(BaseModel):
    verified: bool
    corrections: Optional[Dict[str, Any]] = None

# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Request Models
class StartSessionRequest(BaseModel):
    user_info: UserInfo
    case_filename: str
    config: Optional[SessionConfig] = SessionConfig()

class UpdateDiagnosisRequest(BaseModel):
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    model_choice: Optional[ModelType] = None
    memory_mode: Optional[MemoryMode] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    exam_mode: Optional[bool] = None
