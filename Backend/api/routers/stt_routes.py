"""
Enhanced Speech-to-Text (STT) Routes with Better Error Handling
Uses OpenAI Whisper API + Word Correction AI for Thai medical conversations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import openai
import os
from typing import Dict, Any, Optional
import tempfile
import logging

# Import the word correction service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from services.correction import word_correction_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    logger.warning("⚠️  OPENAI_API_KEY not found! STT features will not work.")
else:
    logger.info("✓ OpenAI API key loaded successfully")


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    enable_correction: bool = Form(True),
    conversation_context: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Transcribe audio to text using OpenAI Whisper API with optional word correction
    """
    
    # Check if API key is available
    if not openai.api_key:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "api_not_configured",
                "message": "ระบบยังไม่พร้อมใช้งาน กรุณาติดต่อผู้ดูแลระบบ",
                "technical_detail": "OpenAI API key not configured"
            }
        )
    
    try:
        # ============ STEP 1: VALIDATE FILE ============
        allowed_types = [
            'audio/webm', 
            'audio/mp4', 
            'audio/mpeg', 
            'audio/wav', 
            'audio/ogg',
            'audio/webm;codecs=opus',
            'audio/x-m4a',
            'audio/mp4a-latm'
        ]
        
        if audio.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_format",
                    "message": f"รูปแบบไฟล์เสียงไม่รองรับ: {audio.content_type}",
                    "supported_formats": ["webm", "mp4", "mpeg", "wav", "ogg"]
                }
            )
        
        # Read and validate file size
        content = await audio.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        logger.info(f"📊 Received audio: {audio.filename}, size: {file_size_mb:.2f} MB, type: {audio.content_type}")
        
        if file_size_mb > 25:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "file_too_large",
                    "message": f"ไฟล์เสียงใหญ่เกินไป ({file_size_mb:.2f} MB) ขนาดสูงสุดคือ 25 MB",
                    "file_size_mb": round(file_size_mb, 2),
                    "max_size_mb": 25
                }
            )
        
        if file_size_mb < 0.001:  # Less than 1KB
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "file_too_small",
                    "message": "ไฟล์เสียงเล็กเกินไปหรือว่างเปล่า กรุณาบันทึกเสียงใหม่",
                    "file_size_mb": round(file_size_mb, 2)
                }
            )
        
        # ============ STEP 2: SAVE TO TEMP FILE ============
        extension_map = {
            'audio/webm': '.webm',
            'audio/webm;codecs=opus': '.webm',
            'audio/mp4': '.mp4',
            'audio/x-m4a': '.m4a',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/ogg': '.ogg'
        }
        extension = extension_map.get(audio.content_type, '.webm')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # ============ STEP 3: WHISPER TRANSCRIPTION ============
            logger.info(f"🎤 Transcribing audio with Whisper API...")
            
            with open(temp_file_path, 'rb') as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="th",
                    response_format="json",
                    temperature=0.0,
                    prompt="นี่คือการสนทนาทางการแพทย์เกี่ยวกับอาการของผู้ป่วย ใช้คำศัพท์ทางการแพทย์ภาษาไทย"
                )
            
            transcribed_text = transcript.text.strip()
            logger.info(f"✅ Whisper transcription: {transcribed_text[:100]}...")
            
            # ============ STEP 4: CHECK FOR TRULY SILENT/EMPTY AUDIO ONLY ============
            # Only reject if completely empty or whitespace
            silent_patterns = [
                "โปรดติดตามตอนต่อไป",
                ""  # Empty string
            ]
            if not transcribed_text or (len(transcribed_text.strip()) == 0 or transcribed_text in silent_patterns):
                logger.warning(f"⚠️ Empty transcription - no audio detected")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "silent_audio",
                        "message": "ไม่พบเสียงพูดในการบันทึก กรุณาตรวจสอบไมโครโฟนและพูดให้ชัดเจน",
                        "transcribed_text": transcribed_text,
                        "hint": "ตรวจสอบว่าไมโครโฟนทำงานปกติและพูดในระยะที่ใกล้พอ"
                    }
                )
            
            # ============ STEP 5: WORD CORRECTION (Optional) ============
            correction_result = None
            final_text = transcribed_text
            
            if enable_correction:
                logger.info(f"🔧 Applying word correction...")
                try:
                    correction_result = word_correction_service.correct_text(
                        transcribed_text=transcribed_text,
                        context=conversation_context or ""
                    )
                    final_text = correction_result["corrected_text"]
                    
                    if correction_result["corrections_made"]:
                        logger.info(f"📝 Corrections applied: {correction_result['changes']}")
                    else:
                        logger.info(f"✓ No corrections needed")
                except Exception as correction_error:
                    # If correction fails, use original transcription
                    logger.warning(f"⚠️ Correction failed, using original text: {str(correction_error)}")
                    final_text = transcribed_text
            
            # ============ STEP 6: PREPARE RESPONSE ============
            response_data = {
                "text": final_text,  # Final text to use
                "original_text": transcribed_text,  # Original Whisper output
                "language": "th",
                "model": "whisper-1",
                "file_size_mb": round(file_size_mb, 2),
                "correction_enabled": enable_correction
            }
            
            # Add correction details if enabled
            if enable_correction and correction_result:
                response_data["correction"] = {
                    "corrections_made": correction_result["corrections_made"],
                    "changes": correction_result.get("changes", []),
                    "model_used": correction_result.get("model_used", "gpt-4o-mini")
                }
            
            logger.info(f"✅ STT pipeline complete: '{transcribed_text}' → '{final_text}'")
            
            return {
                "success": True,
                "data": response_data,
                "message": "Transcription completed successfully" + (
                    " with word correction" if enable_correction else ""
                )
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"🗑️  Cleaned up temporary file: {temp_file_path}")
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is (they already have proper error messages)
        raise
    
    except openai.APIError as e:
        logger.error(f"🚨 OpenAI API Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "openai_api_error",
                "message": "เกิดข้อผิดพลาดจาก OpenAI กรุณาลองอีกครั้ง",
                "technical_detail": str(e)
            }
        )
    
    except openai.RateLimitError as e:
        logger.error(f"🚨 Rate Limit Error: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "มีการใช้งานมากเกินไป กรุณารอสักครู่แล้วลองใหม่",
                "technical_detail": "OpenAI API rate limit exceeded"
            }
        )
    
    except openai.APIConnectionError as e:
        logger.error(f"🚨 Connection Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "connection_failed",
                "message": "ไม่สามารถเชื่อมต่อกับระบบแปลงเสียงได้ กรุณาลองอีกครั้ง",
                "technical_detail": "Failed to connect to OpenAI API"
            }
        )
    
    except Exception as e:
        logger.error(f"🚨 Transcription Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "transcription_failed",
                "message": "เกิดข้อผิดพลาดในการแปลงเสียง กรุณาลองอีกครั้ง",
                "technical_detail": str(e)
            }
        )


@router.get("/status")
async def stt_status() -> Dict[str, Any]:
    """Check STT service status and configuration"""
    api_key_configured = bool(openai.api_key)
    
    return {
        "success": api_key_configured,
        "data": {
            "service": "OpenAI Whisper + Word Correction",
            "stt_model": "whisper-1",
            "correction_model": "gpt-4o-mini",
            "language": "th",
            "api_key_configured": api_key_configured,
            "max_file_size_mb": 25,
            "supported_formats": ["webm", "mp4", "mpeg", "wav", "ogg"],
            "features": {
                "whisper_transcription": True,
                "word_correction": True,
                "medical_terminology": True,
                "context_aware": True,
                "silent_audio_detection": True
            }
        },
        "message": "STT service with word correction is ready" if api_key_configured else "OpenAI API key not configured"
    }


@router.get("/health")
async def stt_health() -> Dict[str, Any]:
    """Health check endpoint for STT service"""
    api_key_configured = bool(openai.api_key)
    
    return {
        "status": "healthy" if api_key_configured else "degraded",
        "api_available": api_key_configured,
        "service": "STT + Word Correction",
        "components": {
            "whisper": api_key_configured,
            "word_correction": api_key_configured,
            "silent_detection": True
        }
    }